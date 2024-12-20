from datetime import datetime, timedelta

import mailchimp_marketing as MailchimpMarketing
from mailchimp_marketing.api_client import ApiClientError

from config import MAILCHIMP_API_KEY, MAILCHIMP_SERVER, MAILCHIMP_RECIPIENT_LIST_ID


def send_email_via_mailchimp(html_content):
    client = None
    try:
        client = MailchimpMarketing.Client()
        client.set_config({
            "api_key": MAILCHIMP_API_KEY,
            "server": MAILCHIMP_SERVER
        })
        response = client.ping.get()
        print(response)
    except ApiClientError as error:
        print(error)

    if client is None:
        print("Could not connect to Mailchimp")
        return

    # Get yesterday's date
    yesterday = datetime.now() - timedelta(days=1)

    # Format as MM/DD/YYYY
    yesterday_str = yesterday.strftime("%m/%d/%Y")

    try:
        # Create a campaign using the custom template
        campaign = client.campaigns.create({
            "type": "regular",
            "recipients": {
                "list_id": MAILCHIMP_RECIPIENT_LIST_ID
            },
            "settings": {
                "subject_line": "Herndon Police Chatter: " + yesterday_str + " Summary Report",
                "preview_text": "Catch up on the daily police activities in Herndon.",
                "title": "Herndon Police Chatter: " + yesterday_str,
                "from_name": "Herndon Police Chatter",
                "reply_to": "maourybusiness@gmail.com",
                "from_email": "maourybusiness@gmail.com"
            }
        })

        campaign_id = campaign['id']

        client.campaigns.set_content(campaign_id, {
            "html": html_content
        })

        # Send the campaign
        client.campaigns.send(campaign_id)

        print("Campaign sent successfully.")
    except ApiClientError as error:
        print("An error occurred: {}".format(error.text))