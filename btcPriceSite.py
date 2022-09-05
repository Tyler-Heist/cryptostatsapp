import statistics
import requests
import datetime
from datetime import date
import sys
import time
import schedule
from schedule import run_pending
from collection_handler import Handler

handler = Handler()


def print_price():
    """ GET CURRENT PRICE OF BITCOIN """
    # calls API from coindesk.com
    current_btc_price = requests.get("https://api.coindesk.com/v1/bpi/currentprice.json")
    # gets and returns current price of BTC
    return current_btc_price.json()["bpi"]["USD"]["rate"]


def write_to_price_collection():
    """ WRITING PRICE DATA TO PRICE COLLECTION """
    # get current date
    current_date = str(date.today())
    # get current time
    current_time = str(datetime.datetime.now().time())

    # if first entry, price_id is 1
    # else, price_id is 1 more than current highest id
    if handler.count('Price') == 0:
        price_id = 1
    else:
        price_id = handler.count('Price') + 1

    # creates dictionary of relevant data for insertion into database
    data = {'ID': price_id, 'Date': current_date, 'Time': current_time, 'Price': print_price()}

    # inserts dictionary into database
    handler.create('Price', data)


def write_to_stats_collection():
    """ COMPUTES LOW/HIGH TIME/PRICE/MODE """
    # get the last 24 hours of price data
    i = handler.count('Price') - 23
    price_data = []
    time_data = []
    while i < handler.count('Price') + 1:
        # add price data and time data to respective lists
        price_data.append(float(handler.read('Price', {'ID': i})[0]['Price'].replace(',', "")))
        time_data.append(handler.read('Price', {'ID': i})[0]['Time'])
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

    # lists for times at which lowest and highest prices occurred each day
    all_lows = []
    all_highs = []
    i = 1
    while i < handler.count('Stats') + 1:
        # append times to respective list
        all_lows.append(handler.read('Stats', {'Days Running': i})[0]['Low Time'])
        all_highs.append(handler.read('Stats', {'Days Running': i})[0]['High Time'])
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
    low_accuracy = str(round((low_count / handler.count('Stats') * 100), 2)) + "%"
    high_accuracy = str(round((high_count / handler.count('Stats') * 100), 2)) + "%"

    # if first entry, stats_id ('Days Running') is 1
    # else, stats_id is 1 more than current highest id
    if handler.count('Stats') == 0:
        stats_id = 1
    else:
        stats_id = handler.count('Stats') + 1

    # used to show the date that an entry was added on
    current_date = str(date.today())

    # creates dictionary of relevant data for insertion into database
    insert_stats = {'Days Running': stats_id, 'Data From': current_date, 'Low Time': low_time,
                    'Low Price': minimum_price, 'Most Frequent Low': low_mode, 'Low Accuracy': low_accuracy,
                    'High Time': high_time, 'High Price': maximum_price, 'Most Frequent High': high_mode,
                    'High Accuracy': high_accuracy}

    # inserts dictionary into database
    handler.create('Stats', insert_stats)


# returns stats from the last time write_to_price_collection was executed
def most_recent_stats():
    last_entry = handler.count('Stats')
    stats = handler.read('Stats', {'Days Running': last_entry})[0]
    return stats


def main():
    """ SCHEDULER TO RUN TASKS EACH HOUR/DAY """
    try:
        # runs write_to_price_collection every hour on the first minute
        schedule.every().hour.at("01:00").do(write_to_price_collection)
        # runs write_to_stats_collection every day at 12:00 AM
        schedule.every().day.at("00:00:01").do(write_to_stats_collection)

        while True:
            run_pending()
            time.sleep(1)
    except KeyboardInterrupt:  # used to exit cleanly if stopped by the user
        sys.exit(0)


# will run main only when this file is explicitly run
# used to avoid execution when file is imported into another file
if __name__ == "__main__":
    main()


