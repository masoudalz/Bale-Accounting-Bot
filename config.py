# config.py
import os

# Database Connection (Replaced with placeholders / environment variables)
DB_CONN = os.getenv("DB_CONN", "DRIVER={SQL Server};SERVER=YOUR_SERVER_IP;DATABASE=YOUR_DB;UID=YOUR_USER;PWD=YOUR_PASSWORD")

# Bot API Credentials
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
BASE_URL = f"https://tapi.bale.ai/bot{BOT_TOKEN}"

# Passwords & Access Control
PASSWORD_NORMAL = os.getenv("PASSWORD_NORMAL", "1234")
PASSWORD_FULL = os.getenv("PASSWORD_FULL", "5678")
PASSWORD_WAREHOUSE = os.getenv("PASSWORD_WAREHOUSE", "9012")

# Paths
PDF_FOLDER = os.getenv("PDF_FOLDER", "./pdf_exports")

FONT_PATH = "C:/Windows/Fonts/Nazanin+ Regular.ttf"
FONT_PATH_FALLBACK = "C:/Windows/Fonts/Tahoma.ttf"

HISTORY_START_YEAR = 1405

# Webzi API Settings
WEBZI_BASE_URL = os.getenv("WEBZI_BASE_URL", "https://example.com/api/shop/product")

WEBZI_API_HEADERS = {
    "Authorization": f"Bearer {os.getenv('WEBZI_API_TOKEN', 'YOUR_TOKEN_HERE')}",
    "Content-Type": "application/json",
    "Accept": "application/json, text/plain, */*",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "X-Requested-With": "XMLHttpRequest"
}

if not os.path.exists(PDF_FOLDER):
    os.makedirs(PDF_FOLDER)
