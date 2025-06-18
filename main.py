from tzlocal import get_localzone
from dotenv import load_dotenv
import google_sheets_api
import pandas as pd
import datetime
import requests
import schedule
import sys
import time
import os

# FIXME: Change to execute based on CST time

load_dotenv()

SPREADSHEET_ID = '1OKWn63iR-B9nxYuqebhIDhiasZWOT-61gUeoJkq8dsQ'
PRICE_DATA_SHEET = 'Price_Data!A1:D'
PREVIOUS_DAY_STATS_SHEET = 'Previous_Day_Stats!A:E'
STATS_SHEET = 'Stats!A1:I'


def main() -> None:
    # Parameters for API call
    params = {
        'market': 'coinbase',
        'instruments': 'BTC-USD',
        'apply_mapping': 'true',
        'api_key': os.getenv('API_KEY')
    }

    # Get current BTC price coindesk.com via API (gets data from Coinbase)
    response = requests.get('https://data-api.coindesk.com/spot/v1/latest/tick', params=params)
    current_price = response.json().get('Data', '').get('BTC-USD', '').get('PRICE', '')

    # Get date info
    now = datetime.datetime.now()
    current_date = now.strftime('%Y-%m-%d')
    current_time = now.strftime('%H:%M:%S')
    time_zone = get_localzone().tzname(now)

    # Append most recent price to Price_Data Google Sheet
    data = [current_date, current_time, time_zone, current_price]
    google_sheets_api.append_rows(data=data, spreadsheet_id=SPREADSHEET_ID, spreadsheet_range=PRICE_DATA_SHEET)

    start_time = datetime.time(0, 0, 0)
    end_time = datetime.time(0, 59, 59)

    # Only execute the code below if the time is between midnight and 1AM
    if start_time <= now.time() <= end_time:
        # Get all values from Previous_Day_Stats Google Sheet
        previous_day_stats = google_sheets_api.get_data(
            spreadsheet_id=SPREADSHEET_ID,
            spreadsheet_range=PREVIOUS_DAY_STATS_SHEET
        )

        test = previous_day_stats['Low Time'][0][:5]

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

        # Get all daily stats
        stats = google_sheets_api.get_data(spreadsheet_id=SPREADSHEET_ID, spreadsheet_range=STATS_SHEET)

        # Add new row to stats df
        stats.loc[len(stats)] = new_row

        # Calculate mode of Most Frequent Low and Most Frequent High columns
        modes = stats.mode()
        low_mode = modes['Most Frequent Low'].tolist()
        high_mode = modes['Most Frequent High'].tolist()

        # Add modes into new_row
        new_row_index = len(stats) - 1
        stats.at[new_row_index, 'Most Frequent Low'] = f"'{low_mode[0]}" if low_mode else 'N/A'
        stats.at[new_row_index, 'Most Frequent High'] = f"'{high_mode[0]}" if high_mode else 'N/A'

        # Convert last row in df (new_row) back into a list
        row_to_add = stats.iloc[new_row_index].tolist()

        # Add "new_row" into Google Sheet
        google_sheets_api.append_rows(data=row_to_add, spreadsheet_id=SPREADSHEET_ID, spreadsheet_range=STATS_SHEET)


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
