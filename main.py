import google.auth
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from googleapiclient.discovery import build

import logging
import logging.handlers
import os

import requests

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger_file_handler = logging.handlers.RotatingFileHandler(
    "status.log",
    maxBytes=1024 * 1024,
    backupCount=1,
    encoding="utf8",
)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger_file_handler.setFormatter(formatter)
logger.addHandler(logger_file_handler)

# Path to your service account JSON credentials
SERVICE_ACCOUNT_FILE = os.getenv('GOOGLE_APPLICATION_KEY')

if not SERVICE_ACCOUNT_FILE:
    # raise ValueError("Google service account credentials file not set in environment variable 'GOOGLE_APPLICATION_KEY'")
    SERVICE_ACCOUNT_FILE = 'haoshoken-12da629190c2.json'

# Scopes needed for Sheets API access
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Authenticate with the service account and generate the credentials object
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# Use the credentials to build the service object
service = build('sheets', 'v4', credentials=credentials)

# Specify the ID of the Google Sheet and the range of data you want to retrieve
SPREADSHEET_ID = '1k0J_FvbWzEabCrs4omCcmC0rvWtdd__4t18mp_ZOvTA'
RANGE_NAME = 'Sheet3!A1:A3'

# Call the Sheets API to retrieve data
def get_sheet_data():
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')
    else:
        print('Data retrieved from sheet:')
        for row in values:
            print(row)
            logger.info(f"From GSheet: {row}")

# Retrieve weather temperature from API
r = requests.get('https://api.open-meteo.com/v1/forecast?latitude=48.8566&longitude=2.3522&current_weather=true')
if r.status_code == 200:
    data = r.json()
    temperature = data["current_weather"]["temperature"]
    logger.info(f'Weather in Paris: {temperature}')

# Test Github environment variables
try:
    SOME_SECRET = os.environ["SOME_SECRET"]
except KeyError:
    SOME_SECRET = "Token not available!"
    #logger.info("Token not available!")
    #raise

if __name__ == "__main__":
    get_sheet_data()
    logger.info(f"Token value: {SOME_SECRET}")

