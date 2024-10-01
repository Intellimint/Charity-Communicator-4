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

# Hardcoded Brevo API key for testing purposes
brevo_api_key = "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"  # Replace this with your actual Brevo API key
openrouter_api_key = "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"  # Replace this with your actual OpenRouter API key

# File to track sent emails
SENT_EMAILS_FILE = 'sent_emails.json'
MAX_EMAILS_PER_DAY = 250

# Configuration for Brevo API key
brevo_configuration = sib_api_v3_sdk.Configuration()
brevo_configuration.api_key['api-key'] = brevo_api_key  # Ensure the key is set properly

# Create an instance of the Brevo Transactional Emails API client
brevo_api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(brevo_configuration))

# OpenRouter API Configuration
openrouter_api_url = "https://openrouter.ai/api/v1/chat/completions"

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
    else:
        # If file doesn't exist, return an empty list
        return []

def save_sent_email(email):
    """Save a sent email to the log file."""
    sent_emails = load_sent_emails()
    sent_emails.append({"email": email, "date": datetime.now().strftime("%Y-%m-%d")})
    with open(SENT_EMAILS_FILE, 'w') as file:
        json.dump(sent_emails, file)

def email_already_sent(journalist_email):
    """Check if the email has already been sent to the given address."""
    sent_emails = load_sent_emails()
    return any(entry['email'] == journalist_email for entry in sent_emails)

def extract_journalist_info(email):
    """Extract journalist's name and publication from email address."""
    username = email.split('@')[0]
    domain = email.split('@')[1].split('.')[0]

    # Assume first initial and last name format for the email username
    name_parts = username.split('.')
    if len(name_parts) == 2:
        journalist_name = f"{name_parts[0].capitalize()} {name_parts[1].capitalize()}"
    else:
        journalist_name = username.capitalize()

    # Use the domain as the focus, assuming it's the publication
    return journalist_name, domain.capitalize()

def generate_custom_email(journalist_email):
    """Generate a custom email using OpenRouter."""
    journalist_name, journalist_focus = extract_journalist_info(journalist_email)
    
    logging.info(f"Generating a custom email for {journalist_name} at {journalist_focus}")

    prompt = f"""
Write a personalized email as a representative from Donate by Mail named Neil Wacaster, introducing the nonprofit to {journalist_name}. The email should highlight Donate by Mail's mission to collect unused tech items to empower veterans or recycle them responsibly. Make the email captivating by emphasizing the impact on veterans' education and employment opportunities, and the simplicity of the donation process.
Suggest a unique angle for {journalist_name} to explore, such as the tech donation process, the environmental impact of recycling devices, or the personal stories of veterans helped by the program. Invite the journalist to reach out for an interview or feature, and include a clear call to action for collaboration.
Tailor the message to {journalist_focus}. Make sure to include the web address for the 501(c)(3), which is https://www.donatebymail.org
    """

    headers = {
        "Authorization": f"Bearer {openrouter_api_key}",
        "Content-Type": "application/json",
    }

    data = {
        "model": "nousresearch/hermes-3-llama-3.1-405b:free",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    try:
        response = requests.post(openrouter_api_url, headers=headers, data=json.dumps(data))
        response.raise_for_status()

        # Log the raw response for debugging
        logging.info(f"OpenRouter response: {response.json()}")

        email_text = response.json().get('choices', [{}])[0].get('message', {}).get('content', '')

        if email_text.strip():
            logging.info(f"Custom email generated: {email_text}")
            formatted_email = email_text.replace("\n", "</p><p>")  # Format email for HTML
            return f"<p>{formatted_email}</p>"
        else:
            logging.warning("OpenRouter returned an empty response.")
            return None
    except requests.RequestException as e:
        logging.error(f"Error generating custom email: {e}")
        return None

def send_individual_email(journalist_email, subject, content):
    """Send an email using Brevo's Transactional Email API."""
    logging.info(f"Attempting to send an email to {journalist_email}")

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=[{"email": journalist_email}],
        sender={"name": "Cipher", "email": "contact@neilwacaster.com"},  # Use the correct email address
        subject=subject,
        html_content=content
    )

    try:
        api_response = brevo_api_instance.send_transac_email(send_smtp_email)
        logging.info("Email sent successfully!")
        pprint(api_response)
        # Log the sent email to the JSON file
        save_sent_email(journalist_email)
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
    """Generate and send custom email if within daily limit."""
    email_count = get_email_count()

    if email_count >= MAX_EMAILS_PER_DAY:
        logging.info(f"Email limit reached for the day. No more emails will be sent.")
        return

    journalist_email = get_next_email()

    # Check if email has already been sent
    if email_already_sent(journalist_email):
        logging.info(f"Email has already been sent to {journalist_email}. Skipping.")
        return

    subject = "Story Pitch: How Old Tech is Changing Veterans’ Lives"

    # Generate custom email content
    email_content = generate_custom_email(journalist_email)

    if email_content:
        # Send the email if valid content is generated
        send_individual_email(journalist_email, subject, email_content)
    else:
        logging.warning(f"No email was sent to {journalist_email} due to invalid or empty content.")

# Example usage
if __name__ == "__main__":
    generate_and_send_email()
