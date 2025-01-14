import requests
import json
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from pprint import pprint
import logging
import csv
import os
import random
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)

# Load API key from environment variables
brevo_api_key = os.getenv("BREVO_API_KEY")

# Ensure API key is loaded
if not brevo_api_key:
    raise ValueError("Brevo API key is not set. Please check the environment variable BREVO_API_KEY.")

# File to track sent emails
SENT_EMAILS_FILE = 'sent_emails.json'
MAX_EMAILS_PER_DAY = 250

# Configuration for Brevo API key
brevo_configuration = sib_api_v3_sdk.Configuration()
brevo_configuration.api_key['api-key'] = brevo_api_key

# Create an instance of the Brevo Transactional Emails API client
brevo_api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(brevo_configuration))

# Campaign email template with HTML formatting
EMAIL_TEMPLATE = """
<p>For Immediate Consideration:</p>

<p>In the wake of record-breaking smartphone upgrades (over 200 million phones replaced in 2023), an innovative nonprofit is turning electronic waste into vital funding for local charities.</p>

<p>Donate by Mail has launched a nationwide initiative that:</p>
<ul>
    <li>Converts unused phones into funding for charitable organizations</li>
    <li>Reduces e-waste through responsible recycling</li>
    <li>Helps connect veterans and underserved communities with refurbished technology</li>
</ul>

<p>On average, each campaign generates $34,000 in value from donated devices, with 50% going directly to partner charities. We're currently working with organizations focused on disaster relief, veterans' services, and community support programs.</p>

<p>Would you be interested in learning more about this intersection of environmental sustainability and charitable giving? I'm happy to provide additional details, statistics, or connect you with charities already participating in the program.</p>

<p>Best regards,<br>
Neil Fox<br>
Founder, Donate by Mail<br>
contact@donatebymail.org<br>
<a href="https://www.donatebymail.org">donatebymail.org</a></p>
"""

def get_email_count():
    """Get the current count of emails sent today."""
    try:
        sent_emails = load_sent_emails()
        today = datetime.now().strftime("%Y-%m-%d")
        return sum(1 for email in sent_emails if email["date"] == today)
    except Exception as e:
        logging.error(f"Error getting email count: {e}")
        return MAX_EMAILS_PER_DAY  # Return max to prevent sending in case of error

def load_sent_emails():
    """Load the list of sent emails from the file."""
    try:
        if os.path.exists(SENT_EMAILS_FILE):
            with open(SENT_EMAILS_FILE, 'r') as file:
                return json.load(file)
        return []
    except Exception as e:
        logging.error(f"Error loading sent emails: {e}")
        return []

def save_sent_email(email):
    """Save a sent email to the log file."""
    try:
        sent_emails = load_sent_emails()
        sent_emails.append({"email": email, "date": datetime.now().strftime("%Y-%m-%d")})
        with open(SENT_EMAILS_FILE, 'w') as file:
            json.dump(sent_emails, file)
    except Exception as e:
        logging.error(f"Error saving sent email: {e}")

def email_already_sent(recipient_email):
    """Check if the email has already been sent to the given address."""
    try:
        sent_emails = load_sent_emails()
        return any(entry['email'] == recipient_email for entry in sent_emails)
    except Exception as e:
        logging.error(f"Error checking if email was sent: {e}")
        return True  # Return True to prevent sending in case of error

def send_individual_email(recipient_email, subject, content):
    """Send an email using Brevo's Transactional Email API."""
    logging.info(f"Attempting to send an email to {recipient_email}")

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=[{"email": recipient_email}],
        sender={"name": "Neil Fox", "email": "contact@donatebymail.org"},
        subject=subject,
        html_content=content
    )

    try:
        api_response = brevo_api_instance.send_transac_email(send_smtp_email)
        logging.info("Email sent successfully!")
        pprint(api_response)
        # Log the sent email to the JSON file
        save_sent_email(recipient_email)
    except ApiException as e:
        logging.error(f"Exception when calling TransactionalEmailsApi->send_transac_email: {e}")

def get_next_email():
    """Get the next random email from the CSV file."""
    try:
        with open('randomized_email_list.csv', 'r') as f:
            reader = list(csv.reader(f))
            if not reader:
                logging.error("Email list is empty")
                return None
            random.shuffle(reader)
            next_email = reader[0][0]
        
        with open('randomized_email_list.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(reader[1:])
        return next_email
    except FileNotFoundError:
        logging.error("randomized_email_list.csv not found")
        return None
    except Exception as e:
        logging.error(f"Error getting next email: {e}")
        return None

def generate_and_send_email():
    """Generate and send an email if within the daily limit."""
    email_count = get_email_count()

    if email_count >= MAX_EMAILS_PER_DAY:
        logging.info(f"Email limit reached for the day. No more emails will be sent.")
        return

    recipient_email = get_next_email()
    if not recipient_email:
        logging.error("No valid email address obtained")
        return

    if email_already_sent(recipient_email):
        logging.info(f"Email has already been sent to {recipient_email}. Skipping.")
        return

    # Updated subject line
    subject = "Story Tip: Local Charities Turn Old Phones into $34K Revenue Streams"
    email_content = EMAIL_TEMPLATE.strip()  # Ensure the email template is clean and formatted

    # Send the email
    send_individual_email(recipient_email, subject, email_content)

# Example usage
if __name__ == "__main__":
    generate_and_send_email()
