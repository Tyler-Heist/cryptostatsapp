from logging.handlers import RotatingFileHandler
from tzlocal import get_localzone
from dotenv import load_dotenv
import google_sheets_api
import pandas as pd
import datetime
import requests
import schedule
import logging
import sys
import time
import os


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


def main() -> None:
    try:
        logging.info(f"{'-' * 35} STARTING  EXECUTION {'-' * 35}")
        # Parameters for API call
        params = {
            'market': 'coinbase',
            'instruments': 'BTC-USD',
            'apply_mapping': 'true',
            'api_key': os.getenv('API_KEY')
        }

        # Get current BTC price coindesk.com via API (gets data from Coinbase)
        logging.info('Calling coindesk API')
        current_price = 0
        try:
            response = requests.get('https://data-api.coindesk.com/spot/v1/latest/tick', params=params, timeout=3)
            response.raise_for_status()
            response_data = response.json()
            current_price = response_data.get('Data', {}).get('BTC-USD', {}).get('PRICE', '')
            if not current_price:
                logging.warning(f'Price data not found: {response_data} - Status Code: {response.status_code}')
        except requests.exceptions.RequestException as e:
            logging.error(f'An error occurred: {e}')
        except ValueError as e:
            logging.error(f'JSON error: {e}')

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
            logging.error(
                f'Error appending to: {SPREADSHEET_ID} - Range: {PRICE_DATA_SHEET} - Data: {data} - Error: {e}'
            )
            return

        start_time = datetime.time(0, 0, 0)
        end_time = datetime.time(0, 59, 59)

        # Only execute the code below if the time is between midnight and 1AM
        if start_time <= now.time() <= end_time:
            logging.info('Getting all values from Previous_Day_Stats Google Sheet')
            try:
                previous_day_stats = google_sheets_api.get_data(
                    spreadsheet_id=SPREADSHEET_ID,
                    spreadsheet_range=PREVIOUS_DAY_STATS_SHEET
                )
            except Exception as e:
                logging.error(f'Error getting data from: {SPREADSHEET_ID} - Error: {e}')
                return

            # New row to add to df before calculating most up-to-date mode
            new_row = {
                'Date': previous_day_stats['Date'][0],
                'Low Time': previous_day_stats['Low Time'][0][:5],
                'Low Price': previous_day_stats['Low Price'][0],
                'Most Frequent Low': '',
                'Low Accuracy': '=COUNTIF(INDIRECT("D2:D" & ROW()), INDIRECT("D" & ROW()))/ROW()',
                'High Time': previous_day_stats['High Time'][0][:5],
                'High Price': previous_day_stats['High Price'][0],
                'Most Frequent High': '',
                'High Accuracy': '=COUNTIF(INDIRECT("H2:H" & ROW()), INDIRECT("H" & ROW()))/ROW()'
            }

            logging.info(f'Get all daily stats from {SPREADSHEET_ID}')
            try:
                stats = google_sheets_api.get_data(spreadsheet_id=SPREADSHEET_ID, spreadsheet_range=STATS_SHEET)
            except Exception as e:
                logging.error(f'Error getting data from: {SPREADSHEET_ID} - Error: {e}')
                return

            logging.info('Adding new row to stats df')
            stats.loc[len(stats)] = new_row

            logging.info('Calculating mode of Most Frequent Low and Most Frequent High columns')
            modes = stats.mode()
            low_mode = modes['Most Frequent Low'].tolist()
            high_mode = modes['Most Frequent High'].tolist()

            logging.info('Adding modes into new_row')
            new_row_index = len(stats) - 1
            stats.at[new_row_index, 'Most Frequent Low'] = f"'{low_mode[0]}" if low_mode else 'N/A'
            stats.at[new_row_index, 'Most Frequent High'] = f"'{high_mode[0]}" if high_mode else 'N/A'

            logging.info('Converting last row in df (new_row) back into a list')
            row_to_add = stats.iloc[new_row_index].tolist()

            logging.info(f'Appending {new_row} to: {SPREADSHEET_ID}')
            try:
                google_sheets_api.append_rows(
                    data=row_to_add,
                    spreadsheet_id=SPREADSHEET_ID,
                    spreadsheet_range=STATS_SHEET
                )
            except Exception as e:
                logging.error(
                    f'Error appending to: {SPREADSHEET_ID} - Range: {STATS_SHEET} - Data: {data} - Error: {e}'
                )
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
