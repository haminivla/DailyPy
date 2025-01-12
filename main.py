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

async def getStockQuotes():   # Retrieve High, Low, Close and Change % of a stock and return as an array

    # Launch the headless browser
    browser = await launch(headless=True)
    page = await browser.newPage()

    # Go to the webpage
    await page.goto("https://www.shareinvestor.com/quote/SGX:O39")

    # Wait for the page to load (you can adjust this as needed)
    await page.waitForSelector('#sic_counterQuote_lastdone')  # Ensure the element is present

    # Get the page content after JavaScript has been rendered
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

        price = [round(float(high),2), round(float(low),2), round(float(close),2), round(float(change),2)]

        # Print the extracted values
        print(f"Prices: {price}")

    except AttributeError as e:
        print("Error extracting data: Could not find the required elements.")
    await browser.close()

#gc = authenticate()
#sheet = gc.open('Get Europe Cities Temperature').worksheet('Sheet3')

# Run the asyncio event loop
asyncio.get_event_loop().run_until_complete(getStockQuotes())
#getStockQuotes()

'''
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
        print(f"Temperature for city {index}: {temperature} °C")
    #logger.info(f'Weather in city: {temperature}')

sheet.update(temperature_list, 'B1:C2') # Update weather temperature data into Sheet3

'''
