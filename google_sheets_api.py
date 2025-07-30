from google.oauth2.service_account import Credentials
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from pathlib import Path
import pandas as pd

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
THIS_FOLDER = Path(__file__).parent.resolve()
CREDS_FILE = THIS_FOLDER / 'creds.json'


def validate_creds() -> Credentials:
    # Load and return service account credentials from the JSON key file.
    return Credentials.from_service_account_file(str(CREDS_FILE), scopes=SCOPES)


def get_data(spreadsheet_id: str, spreadsheet_range: str, df_bool: bool = True) -> pd.DataFrame | list:
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
