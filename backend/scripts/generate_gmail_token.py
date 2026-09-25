"""One-time helper to generate the Gmail sender refresh token.

Use a Google OAuth Desktop client from the same Google Cloud project where
Gmail API is enabled. The refresh token is saved only in the ignored backend/.env.
"""

import os
from pathlib import Path

from dotenv import load_dotenv, set_key
from google_auth_oauthlib.flow import InstalledAppFlow

def main():
    env_path = Path(__file__).resolve().parents[1] / ".env"
    load_dotenv(env_path)

    client_id = os.getenv("GMAIL_OAUTH_CLIENT_ID")
    client_secret = os.getenv("GMAIL_OAUTH_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise RuntimeError("Set GMAIL_OAUTH_CLIENT_ID and GMAIL_OAUTH_CLIENT_SECRET in backend/.env first")

    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }

    flow = InstalledAppFlow.from_client_config(
        client_config,
        scopes=["https://www.googleapis.com/auth/gmail.send"],
    )
    credentials = flow.run_local_server(
        port=0, access_type="offline", prompt="consent", timeout_seconds=300,
        success_message="Gmail sender authorized. You can close this tab.",
    )
    if not credentials.refresh_token:
        raise RuntimeError("Google did not return a refresh token. Repeat consent for the sender account.")
    set_key(str(env_path), "GMAIL_REFRESH_TOKEN", credentials.refresh_token)
    print("Gmail refresh token saved privately in backend/.env. Its value is not printed.")


if __name__ == "__main__":
    main()
