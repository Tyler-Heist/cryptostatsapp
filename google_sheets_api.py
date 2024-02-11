from pathlib import Path

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

THIS_FOLDER = Path(__file__).parent.resolve()
credentials = Credentials.from_service_account_file(f'{THIS_FOLDER}/key.json')


def get_values(sheet_id, sheet_range):
    try:
        # Define client and request, then execute API call
        service = build("sheets", "v4", credentials=credentials)
        request = service.spreadsheets().values().get(spreadsheetId=sheet_id, range=sheet_range).execute()
        response = request.get("values", [])
        # Return values if response has values, else return 'No data found'
        if response:
            return response
        return 'No data found'
    except HttpError as e:
        return e


def append_values(sheet_id, sheet_name, values):
    try:
        # Define client and request, then execute API call
        service = build('sheets', 'v4', credentials=credentials)
        request = service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range=sheet_name,
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body={'values': [values]}
        )
        response = request.execute()
        return response
    except HttpError as e:
        return e
