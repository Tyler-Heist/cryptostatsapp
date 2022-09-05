import statistics
import sys
import time
import gspread
import requests
from datetime import date
import datetime
import schedule

sa = gspread.service_account(filename="service_account.json")
sh = sa.open("BtcPriceSite")

price_sheet = sh.worksheet("Price_Data")
stats_sheet = sh.worksheet("Stats")


def print_price():
    """ GET CURRENT PRICE OF BITCOIN """
    # calls API from coindesk.com
    current_btc_price = requests.get("https://api.coindesk.com/v1/bpi/currentprice.json")
    # gets and returns current price of BTC
    return current_btc_price.json()["bpi"]["USD"]["rate"]


def write_to_price_data_sheet():
    """ WRITING PRICE DATA TO PRICE COLLECTION"""
    # get current date and time
    current_date = str(date.today())
    current_time = str(datetime.datetime.now().time())

    # get number of rows in sheet (add one for next empty row)
    next_empty_row = str(len(price_sheet.get_all_values()) + 1)

    # add row to sheet
    price_sheet.add_rows(1)

    # set parameters for where to put next row of data
    update_date = 'A' + next_empty_row
    update_time = 'B' + next_empty_row
    update_price = 'C' + next_empty_row

    # write next row of data
    price_sheet.update(update_date, current_date)
    price_sheet.update(update_time, current_time)
    price_sheet.update(update_price, print_price())


def write_to_stats_sheet():
    """ COMPUTES LOW/HIGH TIME/PRICE/MODE """
    # get all records from price sheet
    all_price_records = price_sheet.get_all_records()

    # check if there are 24 records, return if not
    if len(all_price_records) < 24:
        return

    # take only last 24 data points
    all_price_records = all_price_records[-24:]

    # create list to store price and time data
    price_data = []
    time_data = []
    # add each price and time entry to price_time and time_data respectively
    i = 0
    while i < len(all_price_records):
        price_data.append(all_price_records[i]['Price'])
        time_data.append(all_price_records[i]['Time'])
        i += 1

    # find the lowest price in price_data list
    minimum_price = min(price_data)
    min_price_index = price_data.index(minimum_price)
    # find hour at which the lowest price occurred
    min_price_time = time_data[min_price_index]
    # rounds minimum price to 2 decimal places
    minimum_price = round(minimum_price, 2)

    # find the highest price in price_data list
    maximum_price = max(price_data)
    max_price_index = price_data.index(maximum_price)
    # find hour at which the highest price occurred
    max_price_time = time_data[max_price_index]
    # rounds maximum price to 2 decimal places
    maximum_price = round(maximum_price, 2)

    # used to convert time data to more easily readable time
    time_conversion = {"00": "12AM", "01": "1AM", "02": "2AM", "03": "3AM",
                       "04": "4AM", "05": "5AM", "06": "6AM", "07": "7AM",
                       "08": "8AM", "09": "9AM", "10": "10AM", "11": "11AM",
                       "12": "12PM", "13": "1PM", "14": "2PM", "15": "3PM",
                       "16": "4PM", "17": "5PM", "18": "6PM", "19": "7PM",
                       "20": "8PM", "21": "9PM", "22": "10PM", "23": "11PM"}

    # converts time to more easily readable syntax
    high_time = time_conversion[max_price_time[0:2]]
    low_time = time_conversion[min_price_time[0:2]]

    # get all records from stats sheet
    all_stats = stats_sheet.get_all_records()

    # create list to store all data from 'Low Time' and 'High Time'
    all_lows = []
    all_highs = []
    # add each price and time entry to price_time and time_data respectively
    i = 0
    while i < len(all_stats):
        all_lows.append(all_stats[i]['Low Time'])
        all_highs.append(all_stats[i]['High Time'])
        i += 1
    
    # finds the time when the lowest and highest prices occur most frequently (mode)
    low_mode = statistics.mode(all_lows)
    high_mode = statistics.mode(all_highs)

    # finds how many times mode occurs for the lows
    low_count = 0
    for elem in all_lows:
        if elem == low_mode:
            low_count += 1

    # finds how many times mode occurs for the highest
    high_count = 0
    for elem in all_highs:
        if elem == high_mode:
            high_count += 1

    # compute percentage (accuracy) for how often mode occurs
    low_accuracy = str(round((low_count / len(all_stats) * 100), 2)) + "%"
    high_accuracy = str(round((high_count / len(all_stats) * 100), 2)) + "%"

    # get current date
    current_date = str(date.today())

    # get number of rows in sheet (add one for next empty row)
    next_empty_row = str(len(all_stats) + 2)

    # add row to sheet
    stats_sheet.add_rows(1)

    # set parameters for where to put next row of data
    update_date = 'A' + next_empty_row
    update_low_time = 'B' + next_empty_row
    update_low_price = 'C' + next_empty_row
    update_low_mode = 'D' + next_empty_row
    update_low_accuracy = 'E' + next_empty_row
    update_high_time = 'F' + next_empty_row
    update_high_price = 'G' + next_empty_row
    update_high_mode = 'H' + next_empty_row
    update_high_accuracy = 'I' + next_empty_row

    # write next row of data
    stats_sheet.update(update_date, current_date)
    stats_sheet.update(update_low_time, low_time)
    stats_sheet.update(update_low_price, minimum_price)
    stats_sheet.update(update_low_mode, low_mode)
    stats_sheet.update(update_low_accuracy, low_accuracy)
    stats_sheet.update(update_high_time, high_time)
    stats_sheet.update(update_high_price, maximum_price)
    stats_sheet.update(update_high_mode, high_mode)
    stats_sheet.update(update_high_accuracy, high_accuracy)


def main():
    try:
        # runs write_to_price_collection every hour on the first minute
        schedule.every().hour.at("00:01").do(write_to_price_data_sheet)
        # runs write_to_stats_collection every day at 12:00 AM
        schedule.every().day.at("00:00:30").do(write_to_stats_sheet)

        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:  # used to exit cleanly if stopped by the user
        sys.exit(0)


# will run main only when this file is explicitly run
# used to avoid execution when file is imported into another file
if __name__ == "__main__":
    main()
