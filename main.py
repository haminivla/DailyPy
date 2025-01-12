import gspread
import os
from google.auth import default
from google.auth.transport.requests import Request
from google.oauth2 import service_account

import logging
import logging.handlers
import os

import re
import asyncio                  # run asynchronous functions
import requests                 # retrieve data via https requests
from pyppeteer import launch    # run headless Chrome browser to return the web pages 
from bs4 import BeautifulSoup   # scrap information from web pages
from datetime import datetime

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

def authenticate():     # Perform authentication and return the authenticated gspread client

    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",     # Full access to Google Sheets
        "https://www.googleapis.com/auth/drive"             # Full access to Google Drive
    ]

    if 'GITHUB_ACTIONS' in os.environ:
        # Running in GitHub Actions - authenticate via Workload Identity Federation
        creds, project = default(scopes=SCOPES)
        gc = gspread.authorize(creds)
    else:
        # Running locally - authenticate via service account file
        gc = gspread.service_account(filename='haoshoken-12da629190c2.json')
    return gc

def readGSheet():           # Read and return the list of stock quotes from the GSheet

    quotes = []
    for i in range (3):
        quotes.append(sheet.cell(1, 1 + (i * 4)).value)
    return quotes

def updateGSheet(data):     # Iterates through a list of stock data and update the GSheet

    for index, value in enumerate(data):
        cell_range = f'{gspread.utils.rowcol_to_a1(2, 1 + (index * 4))}:{gspread.utils.rowcol_to_a1(2, 4 + (index * 4))}'
        sheet.update([value], cell_range)

async def getStockQuotes(): # Retrieve High, Low, Close and Change % of a stock and return as an array

    browser = await launch(                                 # Launch the headless browser
        headless=True,                                      # Ensure headless mode
        args=['--no-sandbox', '--disable-setuid-sandbox']   # Add flags for headless environments (e.g. CI/CD)
    )
    page = await browser.newPage()

    results = []
    for item in quotes:
        
        await page.goto(f"https://www.shareinvestor.com/quote/{item}")
        await page.waitForSelector('#sic_counterQuote_lastdone')    # Ensure the target element is present
        content = await page.content()

        # Parse the rendered html page with BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        try:
            high = soup.find('div', {'id': 'sic_counterQuote_high'}).text.strip()
            low = soup.find('div', {'id': 'sic_counterQuote_low'}).text.strip()
            close = soup.find('span', {'id': 'sic_counterQuote_lastdone'}).text.strip()
            # Use regex to extract the % value in between the brackets
            change = re.search(r'\((.*?)\)', soup.find('span', {'id': 'sic_counterQuote_chg_perc_change'}).text.strip())
            change = change.group(1).replace('%', '').strip()

            price = [float(high), float(low), float(close), float(change)]
            results.append(price)

        except AttributeError as e:
            print("Error extracting data: Could not find the required elements.")

    return results
    await browser.close()

gc = authenticate()
sheet = gc.open('Get Europe Cities Temperature').worksheet('Sheet3')

quotes = readGSheet()       # store list of stock quotes to be retrieved

# Run the getStockQuotes function in an asyncio event loop to get the updated stock data
data = asyncio.get_event_loop().run_until_complete(getStockQuotes())

sheet.insert_row([], 2)
sheet.update([[datetime.now().strftime("%Y-%m-%d %H:%M:%S")]], 'M1')
updateGSheet(data)          # update GSheet with the retrieved stock data

'''
### Function to test read/write GSheet with free Open_Meteo API ###
def testWeatherAPI():
    data = sheet.get('A1:A3')               # Retrieve data from range A1:A3 on Sheet3
    logger.info(f"From GSheet: {data}")

    # Retrieve weather temperature from API
    r = requests.get('https://api.open-meteo.com/v1/forecast?latitude=48.8566,1.3521&longitude=2.3522,103.8198&current_weather=true')
    if r.status_code == 200:
        weather_data = r.json()
        temperature_list = []

        for index, city_data in enumerate(weather_data):
            temperature = city_data["current_weather"]["temperature"]
            temperature_list.append([index, temperature])

    logger.info(f"Temperature for city {index}: {temperature} °C")     # Logs the results into status.log file
    sheet.update(temperature_list, 'B1:C2')                 # Update weather temperature data into Sheet3
'''
