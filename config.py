from pathlib import Path

# ----------------------------
# Google Cloud Project
# ----------------------------
GOOGLE_CLOUD_PROJECT_ID = "bank-sync-496017"

# ----------------------------
# Enable Banking
# ----------------------------

API_ORIGIN = "https://api.enablebanking.com"
APPLICATION_ID = "89380a13-d055-48ff-942c-017dc24d0335"
KEY_PATH = Path("credentials/enablebanking.pem")
ASPSP_NAME = "Jyske Bank"
ASPSP_COUNTRY = "DK"
REDIRECT_URL = "http://localhost:8080/auth_redirect"


# ----------------------------
# Google Sheets
# ----------------------------

GOOGLE_CREDENTIALS = Path("credentials/google-service-account.json")
SHEET_NAME = "Bank_sync"


# ----------------------------
# Session
# ----------------------------

SESSION_FILE = Path("session.json")