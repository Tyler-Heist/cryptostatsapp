import datetime
import sys
import time

import pandas as pd
import requests
import schedule
from tzlocal import get_localzone

import google_sheets_api


def get_price():
    # calls coindesk.com API to get BTC price
    current_btc_price = requests.get('https://api.coindesk.com/v1/bpi/currentprice.json')
    return current_btc_price.json()['bpi']['USD']['rate']


def update_stats_sheet(price):
    # Get date info
    date = str(datetime.date.today())
    now = datetime.datetime.now()
    current_time = now.strftime('%H:%M:%S')
    time_zone = get_localzone().tzname(now)

    # Validate google sheet credentials
    creds = google_sheets_api.get_creds()
    SHEET_ID = '1OKWn63iR-B9nxYuqebhIDhiasZWOT-61gUeoJkq8dsQ'
    PRICE_SHEET = 'Price_Data'
    STATS_SHEET = 'Stats'
    values = [date, current_time, time_zone, price]
    # Update Price_Data Google Sheet
    google_sheets_api.append_values(credentials=creds, sheet_id=SHEET_ID, sheet_name=PRICE_SHEET, values=values)

    # Get all values from Price_Data Google Sheet
    vals = google_sheets_api.get_values(credentials=creds, sheet_id=SHEET_ID, sheet_range=f'{PRICE_SHEET}!A1:D')
    # If a full days prices have been retrieved, calculate the days highs and lows
    if (len(vals) - 1) % 24 == 0:
        print(f'24 hours of data available. Data count: {len(vals) - 1}')
        # Put data into dataframe
        df = pd.DataFrame(vals[-24:], columns=['Date', 'Time', 'Time Zone', 'Price'])
        # Find rows with lowest and highest prices and get their respective prices and times
        min_row = df[df.Price == df.Price.min()]
        max_row = df[df.Price == df.Price.max()]
        date = min_row['Date'].values[0]
        low_time = f'{min_row["Time"].values[0][:2]}:00'
        low_price = min_row['Price'].values[0]
        high_time = f'{max_row["Time"].values[0][:2]}:00'
        high_price = max_row['Price'].values[0]
        # Put all data in list to add to dataframe we will be created
        new_row = [[date, low_time, low_price, '', '', high_time, high_price, '', '']]
        # Get all values from Stats Google Sheet
        vals = google_sheets_api.get_values(credentials=creds, sheet_id=SHEET_ID, sheet_range=f'{STATS_SHEET}!A1:I')
        # Put values into dataframe, adding new_row to the end of the dataframe
        stats = pd.concat([pd.DataFrame(vals[1:]), pd.DataFrame(new_row)])
        stats = stats.reset_index(drop=True)
        # Add column names
        stats.columns = vals[0]
        # Find mode when price was at its lowest, calculate percentage of mode
        low_mode = stats['Low Time'].mode().values[0]
        low_counts = stats['Low Time'].value_counts()
        low_accuracy = f'{low_counts[low_mode] / sum(low_counts) * 100:.2f}%'
        # Find mode when price was at its highest, calculate percentage of mode
        high_mode = stats['High Time'].mode().values[0]
        high_counts = stats['High Time'].value_counts()
        high_accuracy = f'{high_counts[high_mode] / sum(high_counts) * 100:.2f}%'
        # Now that we have all values needed, fill in missing values from new_row list and add row to Stats Google Sheet
        new_stats = [date, low_time, low_price, low_mode, low_accuracy, high_time, high_price, high_mode, high_accuracy]
        return google_sheets_api.append_values(credentials=creds, sheet_id=SHEET_ID, sheet_name=STATS_SHEET, values=new_stats)
    else:
        # If a full days prices have not been retrieved, return count of values
        return f'24 hours of data not available. Data count: {len(vals) - 1}'


def main():
    try:
        # Runs update_stats_sheet on the first minute of every hour
        schedule.every().hour.at("00:01").do(update_stats_sheet(price=get_price()))
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:  # used to exit cleanly if stopped by the user
        sys.exit(0)


# will run main only when this file is explicitly run
# used to avoid execution when file is imported into another file
if __name__ == "__main__":
    main()
