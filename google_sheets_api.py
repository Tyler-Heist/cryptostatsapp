from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from pathlib import Path
import pandas as pd
import os

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


def validate_creds() -> Credentials:
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds


def get_data(spreadsheet_id: str, spreadsheet_range: str, df_bool: bool=True) -> pd.DataFrame | list:
    creds = validate_creds()

    try:
        service = build('sheets', 'v4', credentials=creds, cache_discovery=False)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(
            spreadsheetId=spreadsheet_id,
            range=spreadsheet_range,
            valueRenderOption='FORMATTED_VALUE'
        ).execute()

        values = result.get('values', [])

        if not values:
            raise ValueError('No "Values" found in result')

        if df_bool:
            df = pd.DataFrame(values[1:], columns=values[0])
            return df
        else:
            return values

    except HttpError as e:
        raise RuntimeError(f'An HTTP error occurred: {e}')

    except Exception as e:
        raise RuntimeError(f'An error occurred: {e}')


def append_rows(data: pd.DataFrame | list, spreadsheet_id: str, spreadsheet_range: str) -> None:
    creds = validate_creds()

    try:
        if isinstance(data, pd.DataFrame):
            data = data.values.tolist()
        elif isinstance(data, list):
            data = [data]
        else:
            raise TypeError('"data" must be of type pd.Dataframe or list')

        service = build('sheets', 'v4', credentials=creds, cache_discovery=False)
        # Call the Sheets API
        sheet = service.spreadsheets()
        request = sheet.values().append(
            spreadsheetId=spreadsheet_id,
            range=spreadsheet_range,
            valueInputOption='USER_ENTERED',
            body={'values': data}
        )
        request.execute()
    except HttpError as e:
        raise RuntimeError(f'Failed to append rows in {spreadsheet_range}: {e}')
