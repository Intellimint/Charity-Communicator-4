import os
import requests
from msal import ConfidentialClientApplication
import pandas as pd

def main():
    # Load secrets / credentials from environment variables
    CLIENT_ID = os.getenv("GRAPH_CLIENT_ID")
    TENANT_ID = os.getenv("GRAPH_TENANT_ID")
    CLIENT_SECRET = os.getenv("GRAPH_CLIENT_SECRET")

    if not CLIENT_ID or not TENANT_ID or not CLIENT_SECRET:
        raise ValueError("Missing one or more required environment variables: "
                         "GRAPH_CLIENT_ID, GRAPH_TENANT_ID, GRAPH_CLIENT_SECRET")

    # OAuth2 authority and endpoint
    AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
    SCOPES = ["https://graph.microsoft.com/.default"]

    # Acquire OAuth2 token using MSAL
    app = ConfidentialClientApplication(
        client_id=CLIENT_ID,
        client_credential=CLIENT_SECRET,
        authority=AUTHORITY
    )
    result = app.acquire_token_for_client(scopes=SCOPES)

    if "access_token" not in result:
        print(f"Failed to acquire token: {result.get('error_description')}")
        return

    # Load CSV file path from an environment variable or use a default
    csv_file_path = os.getenv("CSV_FILE_PATH", "unique_emails.csv")

    # Load the email list without a header
    email_list = pd.read_csv(csv_file_path, header=None)  # Read CSV without header
    email_list.columns = ['Email']  # Assign a default column name

    # Email template
    subject = "Turn Unused Phones into $17K for Your Charity (Zero Work Required)"
    body = """
    <p>Hi there,</p>

    <p>Have you noticed how many people got new phones over the holidays? 📱</p>
    <p>There's a huge opportunity right now to turn those old devices into funding for your charity, and we handle everything.</p>

    <p><strong>Here's the deal:</strong></p>
    <ul>
        <li>Your supporters mail in their old phones</li>
        <li>We handle all logistics and processing</li>
        <li>You get 50% of the proceeds (average $17K per campaign)</li>
        <li>Zero work required from your team</li>
    </ul>

    <p>We're only launching this with 10 select charities this quarter, as each campaign gets our full attention.</p>

    <p>Want to grab a quick call to learn more? Just hit reply with "YES" and I'll send over a booking link.</p>

    <p>Best,<br>
    Neil Fox<br>
    Founder, Donate by Mail<br>
    <a href="https://donatebymail.org">donatebymail.org</a></p>

    <p><strong>P.S.</strong> This is perfect timing with all those holiday phone upgrades sitting in drawers right now!</p>
    """

    # Microsoft Graph API endpoint for sending emails
    from_email_address = os.getenv("FROM_EMAIL_ADDRESS", "contact@donatebymail.org")
    endpoint = f"https://graph.microsoft.com/v1.0/users/{from_email_address}/sendMail"

    # Prepare HTTP request headers
    headers = {
        "Authorization": f"Bearer {result['access_token']}",
        "Content-Type": "application/json"
    }

    # Loop through the email list and send the email
    for _, row in email_list.iterrows():
        recipient_email = row['Email']

        # Prepare the email content
        email_data = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "HTML",
                    "content": body
                },
                "toRecipients": [
                    {"emailAddress": {"address": recipient_email}}
                ]
            }
        }

        # Send email
        response = requests.post(endpoint, headers=headers, json=email_data)

        # Check response status
        if response.status_code == 202:
            print(f"Email sent successfully to {recipient_email}")
        else:
            print(f"Failed to send email to {recipient_email}: {response.status_code} - {response.json()}")

if __name__ == "__main__":
    main()
