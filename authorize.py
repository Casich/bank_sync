import logging

from enable_banking import EnableBanking
from secret_manager import Secrets

logger = logging.getLogger(__name__)

def main():
    try:
        logging.info("Creating new EnableBanking session")

        secrets = Secrets()

        bank = EnableBanking()

        session = bank.authorize()

        secrets.save_session(session)

        logger.info("Session saved successfully. Valid until %s", session['access']['valid_until'] )

    except Exception:
        logger.exception("Session renewal failed")
        raise

if __name__ == "__main__":
    main()