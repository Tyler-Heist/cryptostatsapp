import gspread
# Importing flask module in the project is mandatory
# An object of Flask class is our WSGI application.
from flask import Flask, render_template

sa = gspread.service_account(filename="service_account.json")
sh = sa.open("BtcPriceSite")
stats_sheet = sh.worksheet("Stats")
# Flask constructor takes the name of
# current module (__name__) as argument.
application = Flask(__name__)


# The route() function of the Flask class is a decorator,
# which tells the application which URL should call
# the associated function.
@application.route('/')
# ‘/’ URL is bound with index() function.
def index():
    recent_stats = stats_sheet.get_all_records()
    recent_stats = recent_stats[-1]
    days_running = len(recent_stats)
    data_from = list(recent_stats.values())[0]
    low_time = list(recent_stats.values())[1]
    low_price = list(recent_stats.values())[2]
    low_mode = list(recent_stats.values())[3]
    low_accuracy = list(recent_stats.values())[4]
    high_time = list(recent_stats.values())[5]
    high_price = list(recent_stats.values())[6]
    high_mode = list(recent_stats.values())[7]
    high_accuracy = list(recent_stats.values())[8]
    return render_template('index.html', days_running=days_running, data_from=data_from,
                           low_time=low_time, low_price=low_price, low_mode=low_mode,
                           low_accuracy=low_accuracy, high_time=high_time, high_price=high_price,
                           high_mode=high_mode, high_accuracy=high_accuracy)


# main driver function
if __name__ == '__main__':
    # run() method of Flask class runs the application
    # on the local development server.
    application.run(debug=True)
