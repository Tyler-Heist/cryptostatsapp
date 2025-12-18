from flask import Flask, render_template
from flask_caching import Cache
from pathlib import Path
import google_sheets_api

SHEET_ID = '1OKWn63iR-B9nxYuqebhIDhiasZWOT-61gUeoJkq8dsQ'
THIS_FOLDER = Path(__file__).parent.resolve()

# Flask constructor takes the name of current module (__name__) as argument.
app = Flask(__name__, template_folder=str(THIS_FOLDER / 'templates'))
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 3600})


@app.route('/')
@cache.cached()
def index():
    response = google_sheets_api.get_data(spreadsheet_id=SHEET_ID, spreadsheet_range='Stats!A1:F', df_bool=False)
    recent_stats = response[-1]
    return render_template(
        template_name_or_list='index.html',
        days_running=recent_stats[0],
        data_from=recent_stats[1],
        low_mode=recent_stats[2],
        low_accuracy=recent_stats[3],
        high_mode=recent_stats[4],
        high_accuracy=recent_stats[5]
    )


# main driver function
if __name__ == '__main__':
    # run() method of Flask class runs the application
    app.run(debug=False)
