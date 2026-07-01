from datetime import datetime

import gspread

from secret_manager import Secrets
from config import SHEET_NAME


class GoogleSheets:

    def __init__(self):
        self.secrets = Secrets()
        credentials = self.secrets.load_google_credentials()
        self.client = gspread.authorize(credentials)
        self.sheet = self.client.open(SHEET_NAME).sheet1
   

    def get_existing_entry_references(self):
        """
        Returns a set containing all entry references already stored
        in the sheet.
        """

        values = self.sheet.col_values(7)

        if len(values) <= 1:
            return set()

        return set(values[1:])

    def append_transactions(self, transactions):
        """
        Appends only transactions that are not already present.
        """

        existing = self.get_existing_entry_references()

        rows = []

        transactions.sort(
            key=lambda t: (
                t["booking_date"],
                t["entry_reference"],
            )
        )

        for transaction in transactions:

            if transaction["entry_reference"] in existing:
                continue

            rows.append([
                self._format_date(transaction["booking_date"]),
                self._format_date(transaction["value_date"]),
                transaction["amount"],
                transaction["currency"],
                transaction["description"],
                transaction["balance"],
                transaction["entry_reference"],
                ""
            ])

        if rows:

            self.sheet.append_rows(
                rows,
                value_input_option="USER_ENTERED",
            )

            # Auto-sort efter raw date
            self._sort_sheet()

        return len(rows)
    

    def get_latest_booking_date(self):
        """
        Returns the newest booking date found in the sheet.

        Returns:
            datetime.date | None
        """

        dates = self.sheet.col_values(1)

        # Kun header
        if len(dates) <= 1:
            return None

        latest = max(
            datetime.strptime(date, "%d/%m/%Y").date()
            for date in dates[1:]
            if date
        )

        return latest
    

    def _format_date(self, iso_date: str) -> str:
        """
        Convert YYYY-MM-DD → DD/MM/YYYY
        """
        return datetime.strptime(iso_date, "%Y-%m-%d").strftime("%d/%m/%Y")
    

    def _sort_sheet(self):
        """
        Sort sheet by raw booking date (column 2), descending.
        """

        self.sheet.sort(
            (2, "des")  # column B = raw date
        )