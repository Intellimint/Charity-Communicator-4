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

# Load API keys from environment variables
brevo_api_key = os.getenv("BREVO_API_KEY")
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

# Ensure API keys are loaded
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
<p>Hi there,</p>

<p>Have you noticed how many people got new phones over the holidays? 📱</p>

<p>There's a huge opportunity right now to turn those old devices into funding for your charity, and we handle everything.</p>

<p>Here's the deal:</p>
<ul>
    <li>Your supporters mail in their old phones</li>
    <li>We handle all logistics and processing</li>
    <li>You get 50% of the proceeds (average $17K per campaign)</li>
    <li>Zero work required from your team</li>
</ul>

<p>We're only launching this with 10 select charities this quarter, as each campaign gets our full attention.</p>

<p>Want to grab a quick call to learn more? Just hit reply with "YES" and I'll send over a booking link.</p>

<p>Best,<br>Neil Fox<br>Founder, Donate by Mail<br><a href="https://www.donatebymail.org">donatebymail.org</a></p>
"""

def get_email_count():
    """Get the current count of emails sent today."""
    sent_emails = load_sent_emails()
    today = datetime.now().strftime("%Y-%m-%d")
    return sum(1 for email in sent_emails if email["date"] == today)

def load_sent_emails():
    """Load the list of sent emails from the file."""
    if os.path.exists(SENT_EMAILS_FILE):
        with open(SENT_EMAILS_FILE, 'r') as file:
            return json.load(file)
    return []

def save_sent_email(email):
    """Save a sent email to the log file."""
    sent_emails = load_sent_emails()
    sent_emails.append({"email": email, "date": datetime.now().strftime("%Y-%m-%d")})
    with open(SENT_EMAILS_FILE, 'w') as file:
        json.dump(sent_emails, file)

def email_already_sent(recipient_email):
    """Check if the email has already been sent to the given address."""
    sent_emails = load_sent_emails()
    return any(entry['email'] == recipient_email for entry in sent_emails)

def send_individual_email(recipient_email, subject, content):
    """Send an email using Brevo's Transactional Email API."""
    logging.info(f"Attempting to send an email to {recipient_email}")

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=[{"email": recipient_email}],
        sender={"name": "Neil Fox", "email": "contact@donatebymail.org"},  # Update sender email if needed
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
    with open('randomized_email_list.csv', 'r') as f:
        reader = list(csv.reader(f))
    random.shuffle(reader)  # Shuffle to pick a random email
    next_email = reader[0][0]
    # Rewrite the file without the email that was just picked
    with open('randomized_email_list.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(reader[1:])
    return next_email

def generate_and_send_email():
    """Generate and send an email if within the daily limit."""
    email_count = get_email_count()

    if email_count >= MAX_EMAILS_PER_DAY:
        logging.info(f"Email limit reached for the day. No more emails will be sent.")
        return

    recipient_email = get_next_email()

    # Check if the email has already been sent
    if email_already_sent(recipient_email):
        logging.info(f"Email has already been sent to {recipient_email}. Skipping.")
        return

    # Updated subject line
    subject = "Turn Unused Phones into $17K for Your Charity (Zero Work Required)"
    email_content = EMAIL_TEMPLATE.strip()  # Ensure the email template is clean and formatted

    # Send the email
    send_individual_email(recipient_email, subject, email_content)

# Example usage
if __name__ == "__main__":
    generate_and_send_email()
