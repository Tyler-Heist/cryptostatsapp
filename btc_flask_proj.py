import btcPriceSite

# Importing flask module in the project is mandatory
# An object of Flask class is our WSGI application.
from flask import Flask, render_template

# Flask constructor takes the name of
# current module (__name__) as argument.
app = Flask(__name__)


# The route() function of the Flask class is a decorator,
# which tells the application which URL should call
# the associated function.
@app.route('/')
# ‘/’ URL is bound with index() function.
def index():
    recent_stats = btcPriceSite.most_recent_stats()
    days_running = list(recent_stats.values())[0]
    data_from = list(recent_stats.values())[1]
    low_time = list(recent_stats.values())[2]
    low_price = list(recent_stats.values())[3]
    low_mode = list(recent_stats.values())[4]
    low_accuracy = list(recent_stats.values())[5]
    high_time = list(recent_stats.values())[6]
    high_price = list(recent_stats.values())[7]
    high_mode = list(recent_stats.values())[8]
    high_accuracy = list(recent_stats.values())[9]
    return render_template('index.html', days_running=days_running, data_from=data_from,
                           low_time=low_time, low_price=low_price, low_mode=low_mode,
                           low_accuracy=low_accuracy, high_time=high_time, high_price=high_price,
                           high_mode=high_mode, high_accuracy=high_accuracy)


# main driver function
if __name__ == '__main__':
    # run() method of Flask class runs the application
    # on the local development server.
    app.run(debug=True)
