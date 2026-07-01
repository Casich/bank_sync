import os
from datetime import timedelta

from enable_banking import EnableBanking
from google_sheets import GoogleSheets


bank = EnableBanking()
sheets = GoogleSheets()


latest = sheets.get_latest_booking_date()

transactions = bank.get_transactions(
    from_date=(
        latest - timedelta(days=2)
        if latest else None
    )
)

added = sheets.append_transactions(transactions)

print(f"Added {added} new transactions.")