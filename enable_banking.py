import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse
from secret_manager import Secrets

import jwt
import requests

from config import (
    API_ORIGIN,
    APPLICATION_ID,
    ASPSP_COUNTRY,
    ASPSP_NAME,
    KEY_PATH,
)


class EnableBanking:

    def __init__(self):
        self.secrets = Secrets()
        self.jwt = self._create_jwt()
        self.headers = {
            "Authorization": f"Bearer {self.jwt}"
        }


    # ----------------------------------------------------
    # JWT
    # ----------------------------------------------------

    def _create_jwt(self):

        iat = int(datetime.now().timestamp())

        body = {
            "iss": "enablebanking.com",
            "aud": "api.enablebanking.com",
            "iat": iat,
            "exp": iat + 3600,
        }

        private_key = self.secrets.load_private_key()

        return jwt.encode(
            body,
            private_key,
            algorithm="RS256",
            headers={"kid": APPLICATION_ID},
        )

    def _load_private_key(self):

        if self.secret_manager:
            return self.secret_manager.get_secret(
                "enablebanking-private-key"
            )

        with open(KEY_PATH) as f:
            return f.read()

    # ----------------------------------------------------
    # Authentication
    # ----------------------------------------------------

    def ensure_authenticated(self):

        self.session = self.secrets.load_session()

        if self._has_valid_session():
            print("Using existing Enable Banking session.")
            return

        raise RuntimeError(
            "Enable Banking session has expired. "
            "Run authorize.py"
        )


    def authorize(self):
        application = self._get_application()

        auth_url = self._start_authorization(
            application["redirect_urls"][0]
        )

        print()
        print("Authenticate here:")
        print(auth_url)
        print()

        redirected_url = input(
            "Paste redirect URL after MitID login:\n"
        )

        auth_code = parse_qs(
            urlparse(redirected_url).query
        )["code"][0]

        session = self._create_session(auth_code)

        session_data = {
            "session_id": session["session_id"],
            "account_uid": session["accounts"][0]["uid"],
            "valid_until": session["access"]["valid_until"],
            "authorized_at": session["authorized"],
            "bank": ASPSP_NAME
        }
        
        self.secrets.save_session(session_data)

        print("Session saved.")
        
        return session_data

    # ----------------------------------------------------
    # Session validation
    # ----------------------------------------------------

    def _has_valid_session(self):

        if self.session is None:
            return False

        expires = datetime.fromisoformat(
            self.session["valid_until"].replace("Z", "+00:00")
        )

        return expires > datetime.now(timezone.utc)

    # ----------------------------------------------------
    # API calls
    # ----------------------------------------------------

    def _get_application(self):

        r = requests.get(
            f"{API_ORIGIN}/application",
            headers=self.headers,
        )

        r.raise_for_status()

        return r.json()

    def _start_authorization(self, redirect_url):

        body = {
            "access": {
                "valid_until": (
                    datetime.now(timezone.utc)
                    + timedelta(days=90)
                ).isoformat()
            },
            "aspsp": {
                "name": ASPSP_NAME,
                "country": ASPSP_COUNTRY,
            },
            "state": str(uuid.uuid4()),
            "redirect_url": redirect_url,
            "psu_type": "personal",
        }

        r = requests.post(
            f"{API_ORIGIN}/auth",
            json=body,
            headers=self.headers,
        )

        r.raise_for_status()

        return r.json()["url"]

    def _create_session(self, auth_code):

        r = requests.post(
            f"{API_ORIGIN}/sessions",
            json={
                "code": auth_code
            },
            headers=self.headers,
        )

        r.raise_for_status()

        return r.json()

    # ----------------------------------------------------
    # Transactions
    # ----------------------------------------------------

    from datetime import datetime, timedelta, timezone


    def get_transactions(self, from_date=None):
        """
        Fetch and normalize transactions from Enable Banking.

        Args:
            from_date (datetime.date | None):
                Only fetch transactions from this date and forward.
                If None, defaults to last 90 days.
        """

        self.ensure_authenticated()

        account_uid = self.session["account_uid"]

        # ----------------------------------------------------
        # Determine start date
        # ----------------------------------------------------
        if from_date is None:
            from_date = (
                datetime.now(timezone.utc)
                - timedelta(days=90)
            ).date()

        query = {
            "date_from": from_date.isoformat(),
        }

        continuation_key = None
        transactions = []

        while True:

            if continuation_key:
                query["continuation_key"] = continuation_key

            r = requests.get(
                f"{API_ORIGIN}/accounts/{account_uid}/transactions",
                params=query,
                headers=self.headers,
            )

            r.raise_for_status()

            response = r.json()

            for transaction in response["transactions"]:

                normalized = self._normalize_transaction(transaction)

                if normalized is None:
                    continue

                transactions.append(normalized)


            continuation_key = response.get("continuation_key")

            if continuation_key is None:
                break

        return transactions
    
    
    def _normalize_transaction(self, transaction):
        """
        Convert a raw Enable Banking transaction into the simplified format
        used by the rest of the application.
        """

        # Ignore pending transactions
        status = transaction.get("status")
        if status != "BOOK":
            return None

        # Ignore transactions with entry reference
        entry_reference = transaction.get("entry_reference")
        if not entry_reference:
            return None

        amount = float(transaction["transaction_amount"]["amount"])

        if transaction["credit_debit_indicator"] == "DBIT":
            amount = -amount

        description = ""

        if transaction.get("remittance_information"):
            description = " ".join(transaction["remittance_information"])

        return {
            "entry_reference": transaction["entry_reference"],
            "booking_date": transaction["booking_date"],
            "value_date": transaction["value_date"],
            "amount": amount,
            "currency": transaction["transaction_amount"]["currency"],
            "description": description,
            "balance": float(
                transaction["balance_after_transaction"]["amount"]
            ),
        }