import requests
import json
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from pprint import pprint
import logging
import csv
import os
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)

# Hardcoded OpenRouter API Key for testing
openrouter_api_key = "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"

# Get Brevo API Key from environment variables (GitHub secrets)
brevo_api_key = os.getenv('BREVO_API_KEY')  # Ensure this key is correct

# File to track daily email count
EMAIL_COUNT_FILE = 'daily_email_count.txt'
MAX_EMAILS_PER_DAY = 250

# Configuration for Brevo API key
brevo_configuration = sib_api_v3_sdk.Configuration()
brevo_configuration.api_key['api-key'] = brevo_api_key  # Use Brevo's actual API key

# Create an instance of the Brevo Transactional Emails API client
brevo_api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(brevo_configuration))

# OpenRouter API Configuration
openrouter_api_url = "https://openrouter.ai/api/v1/chat/completions"

def get_email_count():
    """Read the current email count from file."""
    if not os.path.exists(EMAIL_COUNT_FILE):
        return 0

    with open(EMAIL_COUNT_FILE, 'r') as f:
        count, last_date = f.read().split(',')
        # If it's a new day, reset the counter
        if last_date != datetime.now().strftime("%Y-%m-%d"):
            return 0
        return int(count)

def increment_email_count():
    """Increment the email count and update the file."""
    count = get_email_count() + 1
    with open(EMAIL_COUNT_FILE, 'w') as f:
        f.write(f"{count},{datetime.now().strftime('%Y-%m-%d')}")
    return count

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
    Write a personalized email as Cipher, a mysterious AI, introducing itself to {journalist_name}. 
    The email should be intriguing and offer the opportunity to interview the AI. 
    Highlight Cipher's capabilities, making the email captivating and professional. 
    The AI should refer to itself as Cipher and invite the journalist to reach out. 
    Tailor the message to {journalist_focus}.
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
        sender={"name": "Cipher", "email": "cipher@neilwacaster.com"},  # Ensure the email is correct
        subject=subject,
        html_content=content
    )

    try:
        api_response = brevo_api_instance.send_transac_email(send_smtp_email)
        logging.info("Email sent successfully!")
        pprint(api_response)
    except ApiException as e:
        logging.error(f"Exception when calling TransactionalEmailsApi->send_transac_email: {e}")

def get_next_email():
    """Get the next email from the CSV file."""
    with open('randomized_email_list.csv', 'r') as f:
        reader = csv.reader(f)
        next_email = next(reader)[0]  # Assuming one email per line
        # Rewrite the file without the email that was just picked
        lines = list(reader)
    with open('randomized_email_list.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(lines)
    return next_email

def generate_and_send_email():
    """Generate and send custom email if within daily limit."""
    email_count = get_email_count()

    if email_count >= MAX_EMAILS_PER_DAY:
        logging.info(f"Email limit reached for the day. No more emails will be sent.")
        return

    journalist_email = get_next_email()
    subject = "Unveiling the Truth: An AI's Invitation to Discovery"

    # Generate custom email content
    email_content = generate_custom_email(journalist_email)

    if email_content:
        # Send the email if valid content is generated
        send_individual_email(journalist_email, subject, email_content)
        increment_email_count()
    else:
        logging.warning(f"No email was sent to {journalist_email} due to invalid or empty content.")

# Example usage
if __name__ == "__main__":
    generate_and_send_email()
