import google_sheets_api
# Importing flask module in the project is mandatory
# An object of Flask class is our WSGI application.
from flask import Flask, render_template

SHEET_ID = '1OKWn63iR-B9nxYuqebhIDhiasZWOT-61gUeoJkq8dsQ'
STATS_SHEET = 'Stats'
creds = google_sheets_api.get_creds()
# Flask constructor takes the name of
# current module (__name__) as argument.
application = Flask(__name__)


# The route() function of the Flask class is a decorator,
# which tells the application which URL should call the associated function.
@application.route('/')
# ‘/’ URL is bound with index() function.
def index():
    response = google_sheets_api.get_values(credentials=creds, sheet_id=SHEET_ID, sheet_range=f'{STATS_SHEET}!A1:I')
    recent_stats = response[-1]
    return render_template('index.html', days_running=len(response)-1, data_from=recent_stats[0],
                           low_time=recent_stats[1], low_price=recent_stats[2], low_mode=recent_stats[3],
                           low_accuracy=recent_stats[4], high_time=recent_stats[5], high_price=recent_stats[6],
                           high_mode=recent_stats[7], high_accuracy=recent_stats[8])


# main driver function
if __name__ == '__main__':
    # run() method of Flask class runs the application
    # on the local development server.
    application.run(debug=True)

