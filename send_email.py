import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from pprint import pprint
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# Configuration of Brevo API key
configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = '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'  # <-- Insert your API key here

# Create an instance of the Brevo Transactional Emails API client
api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

def send_individual_email(journalist_email, subject, content):
    # Log the attempt to send the email
    logging.info(f"Attempting to send an individual email to {journalist_email}")

    # Define the email parameters
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=[{"email": journalist_email}],  # Directly send to individual email
        sender={"name": "Neil Wacaster AI", "email": "contact@neilwacaster.com"},
        subject=subject,
        html_content=content
    )

    try:
        # Send the email via Brevo API
        api_response = api_instance.send_transac_email(send_smtp_email)
        logging.info("Email sent successfully!")
        pprint(api_response)
    except ApiException as e:
        logging.error(f"Exception when calling TransactionalEmailsApi->send_transac_email: {e}")
        print(f"Exception when calling TransactionalEmailsApi->send_transac_email: {e}")

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
    send_individual_email(journalist_email, subject, content)
