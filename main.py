import logging
import os
from datetime import timedelta
from flask import Flask

from enable_banking import EnableBanking
from google_sheets import GoogleSheets


IS_CLOUD = os.getenv("K_SERVICE") is not None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

logger = logging.getLogger(__name__)


app = Flask(__name__)

@app.route("/", methods=["GET"])
def run_sync():

    main()

    return "OK", 200


def main():
    try:
        logger.info("Starting synchronization...")

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

        logger.info("Added %s new transactions", added)

        logger.info("Synchronization completed succesfully")
    
    except Exception:
        logger.exception("Synchronization failed")
        raise

if __name__ == "__main__":
    if IS_CLOUD:
        app.run(host="0.0.0.0", port=8080)
    else:
        main()