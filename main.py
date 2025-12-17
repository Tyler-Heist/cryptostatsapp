import datetime
import logging
import os
import sys
import time
from logging.handlers import RotatingFileHandler

import pandas as pd
import requests
import schedule
from dotenv import load_dotenv
from pushbullet import Pushbullet
from tzlocal import get_localzone

import google_sheets_api

handler = RotatingFileHandler('cryptostatsapp.log', maxBytes=5*1024*1024, backupCount=5)
logging.basicConfig(
    handlers=[handler],
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

load_dotenv()

SPREADSHEET_ID = '1OKWn63iR-B9nxYuqebhIDhiasZWOT-61gUeoJkq8dsQ'
PRICE_DATA_SHEET = 'Price_Data!A1:D'
PREVIOUS_DAY_STATS_SHEET = 'Previous_Day_Stats!A:E'
STATS_SHEET = 'Stats!A1:I'

GSHEET_API_KEY = os.getenv('API_KEY')
PUSHBULLET_TOKEN = os.getenv('PUSHBULLET_TOKEN')
pb = Pushbullet(PUSHBULLET_TOKEN)


def get_price_data() -> float | None:
    # Parameters for API call
    params = {
        'market': 'coinbase',
        'instruments': 'BTC-USD',
        'apply_mapping': 'true',
        'api_key': GSHEET_API_KEY
    }

    # Get current BTC price coindesk.com via API (gets data from Coinbase)
    logging.info('Calling coindesk API')
    try:
        response = requests.get(url='https://data-api.coindesk.com/spot/v1/latest/tick', params=params, timeout=3)
        response.raise_for_status()
        response_data = response.json()
        current_price = response_data.get('Data', {}).get('BTC-USD', {}).get('PRICE', '')
        if not current_price:
            logging.warning(f'Price data not found: {response_data} - Status Code: {response.status_code}')
            return None
        return current_price
    except requests.exceptions.RequestException as e:
        logging.exception(f'An error occurred: {e}')
        raise e
    except ValueError as e:
        logging.exception(f'JSON error: {e}')
        raise e


def main() -> None:
    try:
        logging.info(f"{'-' * 35} STARTING  EXECUTION {'-' * 35}")

        pb.push_note(title='CryptoStatsApp', body='Script Started')

        current_price = get_price_data()

        # Get date info
        now = datetime.datetime.now()
        current_date = now.strftime('%Y-%m-%d')
        current_time = now.strftime('%H:%M:%S')
        time_zone = get_localzone().tzname(now)

        # Append most recent price to Price_Data Google Sheet
        data = [current_date, current_time, time_zone, current_price]
        try:
            logging.info(f'Appending data to: {SPREADSHEET_ID}')
            google_sheets_api.append_rows(data=data, spreadsheet_id=SPREADSHEET_ID, spreadsheet_range=PRICE_DATA_SHEET)
        except Exception as e:
            msg = f'Error appending to sheet - Range: {PRICE_DATA_SHEET} - Data: {data} - Error: {e}'
            logging.error(msg)
            pb.push_note(title='CryptoStatsApp Error', body=msg)
            return
    except Exception as e:
        logging.exception(f'Unhandled exception: {e}')
    finally:
        logging.info(f"{'-' * 35} EXECUTION COMPLETED {'-' * 35}\n\n")


# will run main only when this file is explicitly run
# used to avoid execution when file is imported into another file
if __name__ == "__main__":
    try:
        # main()
        schedule.every().hour.at('01:00').do(main)
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        sys.exit(0)
