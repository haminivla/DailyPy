import gspread
import os
from google.auth import default
from google.auth.transport.requests import Request
from google.oauth2 import service_account

import logging
import logging.handlers
import os

import requests     # to retrieve data via https requests

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

def authenticate():

    # Define the required scopes for both Google Sheets and Google Drive
    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",     # Full access to Google Sheets
        "https://www.googleapis.com/auth/drive"             # Full access to Google Drive
    ]

    if 'GITHUB_ACTIONS' in os.environ:
        # Running in GitHub Actions - authenticate via Workload Identity Federation
        # This assumes the environment has the right credentials for GitHub Actions
        creds, project = default(scopes=SCOPES)  # This gets the credentials provided by GitHub Actions
    else:
        # Running locally - authenticate via service account file
        creds = service_account.Credentials.from_service_account_file(
            'haoshoken-12da629190c2.json', 
            scopes=SCOPES
        )
    return creds

# Authenticate
creds = authenticate()

# Create a client using gspread
gc = gspread.authorize(creds)

# Open the Google Sheet by its name
sheet = gc.open('Get Europe Cities Temperature').worksheet('Sheet3')

# Retrieve data from range A1:A3 on Sheet3
data = sheet.get('A1:A3')
print(data)
logger.info(f"From GSheet: {data}")

# Retrieve weather temperature from API
r = requests.get('https://api.open-meteo.com/v1/forecast?latitude=48.8566&longitude=2.3522&current_weather=true')
if r.status_code == 200:
    data = r.json()
    temperature = data["current_weather"]["temperature"]
    logger.info(f'Weather in Paris: {temperature}')

# Update weather temperature data into Sheet3
sheet.update('B1', [[temperature]])

'''# Path to your service account JSON credentials
# https://cloud.google.com/blog/products/identity-security/enabling-keyless-authentication-from-github-actions
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

# Test Github environment variables
try:
    SOME_SECRET = os.environ["SOME_SECRET"]
except KeyError:
    SOME_SECRET = "Token not available!"
    #logger.info("Token not available!")
    #raise

if __name__ == "__main__":
    logger.info(f"Token value: {SOME_SECRET}")
'''
