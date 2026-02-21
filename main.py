import datetime
import logging
import os
import sys
import time
from logging.handlers import RotatingFileHandler

import requests
import schedule
from tenacity import retry, wait_fixed, RetryError
from dotenv import load_dotenv
from pushbullet import Pushbullet
from tenacity import stop_after_attempt
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

GSHEET_API_KEY = os.getenv('API_KEY')
PUSHBULLET_TOKEN = os.getenv('PUSHBULLET_TOKEN')
pb = Pushbullet(PUSHBULLET_TOKEN)


def pb_checkin() -> None:
    pb.push_note(title='Weekly Checkin', body='Everything is still going well!')


@retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
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
        raise
    except ValueError as e:
        logging.exception(f'JSON error: {e}')
        raise


@retry(stop=stop_after_attempt(3), wait=wait_fixed(10))
def write_price_data(data: list) -> None:
    logging.info(f'Appending data to: {SPREADSHEET_ID}')
    google_sheets_api.append_rows(data=data, spreadsheet_id=SPREADSHEET_ID, spreadsheet_range=PRICE_DATA_SHEET)


def main() -> None:
    try:
        logging.info(f"{'-' * 35} STARTING  EXECUTION {'-' * 35}")

        current_price = None

        try:
            current_price = get_price_data()
        except RetryError as e:
            msg = f'Error getting price data: {e}'
            logging.error(msg)
            pb.push_note(title='CryptoStatsApp Error', body=msg)

        if current_price is not None:
            # Get date info
            now = datetime.datetime.now()
            current_date = now.strftime('%Y-%m-%d')
            current_time = now.strftime('%H:%M:%S')
            time_zone = get_localzone().tzname(now)

            # Append most recent price to Price_Data Google Sheet
            data = [current_date, current_time, time_zone, current_price]

            try:
                write_price_data(data=data)
            except RetryError as e:
                msg = f'Error appending to sheet - Range: {PRICE_DATA_SHEET} - Data: {data} - Error: {e}'
                logging.error(msg)
                pb.push_note(title='CryptoStatsApp Error', body=msg)

    except Exception as e:
        logging.exception(f'Unhandled exception: {e}')
    finally:
        logging.info(f"{'-' * 35} EXECUTION COMPLETED {'-' * 35}\n\n")


# will run main only when this file is explicitly run
# used to avoid execution when file is imported into another file
if __name__ == "__main__":
    try:
        # main()
        pb.push_note(title='CryptoStatsApp', body='Script Started')
        schedule.every().hour.at('01:00').do(main)
        schedule.every().week.at('01:00').do(pb_checkin)
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        sys.exit(0)
