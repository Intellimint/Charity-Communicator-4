from __future__ import print_function
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from pprint import pprint
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# Configuration of Brevo API key (Directly set here for testing purposes)
configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = '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'  # <-- Paste your API key here

# Create an instance of the Brevo API client
api_instance = sib_api_v3_sdk.EmailCampaignsApi(sib_api_v3_sdk.ApiClient(configuration))

def send_email_to_journalist(journalist_email, subject, content):
    # Log the attempt to send the email
    logging.info(f"Attempting to send an email to {journalist_email}")

    # Define the email campaign parameters (sending directly to the email)
    email_campaign = sib_api_v3_sdk.CreateEmailCampaign(
        name="AI-Journalist Outreach",
        subject=subject,
        sender={"name": "Neil Wacaster AI", "email": "contact@neilwacaster.com"},
        html_content=content,
        recipients={"exclusionListIds": [], "emails": [journalist_email]}  # Send directly to email
        # No scheduled_at field, so email is sent immediately
    )

    try:
        # Send the email campaign via Brevo API
        api_response = api_instance.create_email_campaign(email_campaign)
        logging.info("Email sent successfully!")
        pprint(api_response)
    except ApiException as e:
        logging.error(f"Exception when calling EmailCampaignsApi->create_email_campaign: {e}")
        print("Exception when calling EmailCampaignsApi->create_email_campaign: %s\n" % e)

# Example call to send a test email
if __name__ == "__main__":
    journalist_email = "foxlabscorp@gmail.com"  # Test email for yourself
    subject = "Collaboration Opportunity with AI for Social Good"
    content = """
    <p>Hello,</p>
    <p>This is an AI-driven initiative designed to support investigative journalism and social good projects.</p>
    <p>We are exploring how AI can assist journalists like you in finding hidden patterns in data, enhancing research efficiency, and amplifying efforts toward transparency and accountability.</p>
    <p>If you're interested in a collaboration or would like more details, feel free to reach out!</p>
    <p>Best regards,</p>
    <p>Neil Wacaster AI</p>
    """

    # Call the function to send the test email
    send_email_to_journalist(journalist_email, subject, content)

