import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def get_creds():
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = None
    # token.json is created automatically when authorizing the first time; stores the user's access and refresh token
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", scopes)
    # If there are no valid credentials available, prompt user to log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", scopes)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds


def get_values(credentials, sheet_id, sheet_range):
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


def append_values(credentials, sheet_id, sheet_name, values):
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
