from datetime import timedelta
import logging

from enable_banking import EnableBanking
from google_sheets import GoogleSheets


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

logger = logging.getLogger(__name__)


bank = EnableBanking()
sheets = GoogleSheets()


latest = sheets.get_latest_booking_date()
logger.debug("Latest transaction is from %s", latest.strftime("%d-%m-%Y"))
fetch_date = latest - timedelta(days=2)
logger.info("Fetching transactions from %s...", fetch_date.strftime("%d-%m-%Y"))
transactions = bank.get_transactions(
    from_date=(
        fetch_date
        if latest else None
    )
)
logger.debug("Fetched {transactions} transactions")

added = sheets.append_transactions(transactions)

logger.info("Added {added} new transactions")