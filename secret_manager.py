import json
import os
from pathlib import Path

from google.cloud import secretmanager
from google.auth import default
from google.oauth2.service_account import Credentials

from config import (
    GOOGLE_CLOUD_PROJECT_ID,
    GOOGLE_CREDENTIALS,
    SESSION_FILE,
    KEY_PATH,
)

IS_CLOUD = os.getenv("K_SERVICE") is not None


class Secrets:

    def __init__(self):
        if IS_CLOUD:
            self.client = secretmanager.SecretManagerServiceClient()

    # ----------------------------------------------------
    # Private helpers
    # ----------------------------------------------------

    def _get_secret(self, secret_name):

        name = (
            f"projects/{GOOGLE_CLOUD_PROJECT_ID}"
            f"/secrets/{secret_name}"
            "/versions/latest"
        )

        response = self.client.access_secret_version(
            request={"name": name}
        )

        return response.payload.data.decode()

    # ----------------------------------------------------
    # Enable Banking private key
    # ----------------------------------------------------

    def load_private_key(self):

        if IS_CLOUD:
            return self._get_secret(
                "enablebanking-private-key"
            )

        with open(KEY_PATH, "r") as f:
            return f.read()

    # ----------------------------------------------------
    # Google Sheets service account credentials
    # ----------------------------------------------------

    def load_google_credentials(self):    

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]

        if IS_CLOUD:
            creds, _ = default(scopes=scopes)
            return creds

        return Credentials.from_service_account_file(
            GOOGLE_CREDENTIALS,
            scopes=scopes,
        )


    # ----------------------------------------------------
    # Session
    # ----------------------------------------------------

    def load_session(self):

        if IS_CLOUD:
            return json.loads(
                self._get_secret(
                    "enablebanking-session"
                )
            )

        if not Path(SESSION_FILE).exists():
            return None

        with open(SESSION_FILE, "r") as f:
            return json.load(f)

    def save_session(self, session):

        if IS_CLOUD:
            parent = (
                f"projects/{GOOGLE_CLOUD_PROJECT_ID}"
                "/secrets/enablebanking-session"
            )

            self.client.add_secret_version(
                request={
                    "parent": parent,
                    "payload": {
                        "data": json.dumps(session).encode()
                    },
                }
            )
            return

        with open(SESSION_FILE, "w") as f:
            json.dump(session, f, indent=4)