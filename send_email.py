import requests
import json
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from pprint import pprint
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# Configuration of Brevo API key
brevo_configuration = sib_api_v3_sdk.Configuration()
brevo_configuration.api_key['api-key'] = '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'  # Insert Brevo API key

# Create an instance of the Brevo Transactional Emails API client
brevo_api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(brevo_configuration))

# Configuration for OpenRouter Hermes 3 405B API
openrouter_api_url = "https://openrouter.ai/api/v1/chat/completions"
openrouter_api_key = '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'  # Insert OpenRouter API key

def extract_journalist_info(email):
    """Extract journalist's name and publication from email address"""
    username = email.split('@')[0]
    domain = email.split('@')[1].split('.')[0]

    # Assume first initial and last name format for the email username
    name_parts = username.split('.')
    if len(name_parts) == 2:
        journalist_name = f"{name_parts[0].capitalize()} {name_parts[1].capitalize()}"
    else:
        journalist_name = username.capitalize()

    # Use the domain as the focus, assuming it's the publication or company
    journalist_focus = domain.capitalize()

    return journalist_name, journalist_focus

def generate_custom_email(journalist_email):
    """Generate a custom email using Hermes 3 405B model via OpenRouter"""
    journalist_name, journalist_focus = extract_journalist_info(journalist_email)
    
    logging.info(f"Generating a custom email for {journalist_name}")

    # Define the prompt for the Hermes 3 405B model
    prompt = f"""
    You are Cipher, a mysterious and powerful AI built to assist journalists in uncovering hidden truths.
    Write a personalized, intriguing email to {journalist_name}, a journalist who covers topics at {journalist_focus}.
    The email should emphasize Cipher's advanced capabilities in uncovering hidden stories, analyzing complex patterns, and revealing what was once concealed. 
    Make the tone mysterious but professional, and invite the journalist to reply to this email to learn more or interview Cipher. Also, generate a custom subject line that will spark curiosity.
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
        # Send the request to OpenRouter
        response = requests.post(openrouter_api_url, headers=headers, data=json.dumps(data))
        response.raise_for_status()

        # Parse the response
        email_text = response.json()['choices'][0]['message']['content']

        if email_text.strip():
            logging.info(f"Custom email generated: {email_text}")
            return email_text
        else:
            logging.warning("OpenRouter returned an empty response.")
            return None
    except requests.RequestException as e:
        logging.error(f"Error generating custom email: {e}")
        return None

def send_individual_email(journalist_email, subject, content):
    """Send an email using Brevo's Transactional Email API"""
    logging.info(f"Attempting to send an email to {journalist_email}")

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=[{"email": journalist_email}],
        sender={"name": "Cipher", "email": "contact@neilwacaster.com"},
        subject=subject,
        html_content=content
    )

    try:
        # Send the email via Brevo API
        api_response = brevo_api_instance.send_transac_email(send_smtp_email)
        logging.info("Email sent successfully!")
        pprint(api_response)
    except ApiException as e:
        logging.error(f"Exception when calling TransactionalEmailsApi->send_transac_email: {e}")

def generate_and_send_email(journalist_email):
    """Generate and send custom email if valid response is received"""
    
    # Generate custom email content
    email_content = generate_custom_email(journalist_email)

    if email_content:
        # Parse email content to extract subject and body
        subject_line = email_content.split("\n")[0].replace("Subject: ", "").strip()
        email_body = email_content.replace(subject_line, "").strip()

        # Only send the email if valid content is generated
        send_individual_email(journalist_email, subject_line, email_body)
    else:
        logging.warning(f"No email was sent to {journalist_email} due to invalid or empty content.")

# Example usage
if __name__ == "__main__":
    journalist_email = "foxlabscorp@gmail.com"  # Test email for yourself

    # Generate and send email to the journalist
    generate_and_send_email(journalist_email)
