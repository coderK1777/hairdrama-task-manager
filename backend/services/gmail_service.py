import base64
import os
from email.message import EmailMessage

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

GMAIL_SCOPE = "https://www.googleapis.com/auth/gmail.send"


def _gmail_credentials() -> Credentials:
    required = {
        "client_id": os.getenv("GMAIL_OAUTH_CLIENT_ID"),
        "client_secret": os.getenv("GMAIL_OAUTH_CLIENT_SECRET"),
        "refresh_token": os.getenv("GMAIL_REFRESH_TOKEN"),
    }

    if not all(required.values()):
        raise RuntimeError("Gmail OAuth environment variables are not configured")

    return Credentials(
        token=None,
        refresh_token=required["refresh_token"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=required["client_id"],
        client_secret=required["client_secret"],
        scopes=[GMAIL_SCOPE],
    )


def send_email(to_email: str, subject: str, text_body: str) -> None:
    sender = os.getenv("GMAIL_SENDER_EMAIL")
    if not sender:
        raise RuntimeError("GMAIL_SENDER_EMAIL is not configured")

    message = EmailMessage()
    message["To"] = to_email
    message["From"] = sender
    message["Subject"] = subject
    message.set_content(text_body)

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

    service = build("gmail", "v1", credentials=_gmail_credentials(), cache_discovery=False)
    service.users().messages().send(
        userId="me",
        body={"raw": encoded_message},
    ).execute()
