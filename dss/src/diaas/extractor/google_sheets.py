from pprint import pprint

import google.oauth2.service_account
from googleapiclient.discovery import build

credentials = google.oauth2.service_account.Credentials.from_service_account_file(
    "/home/mb/Downloads/diaas-stg-0f315589edda.json"
)
service = build("sheets", "v4", credentials=credentials)
sheets = service.spreadsheets()
SAMPLE_SPREADSHEET_ID = "1WDn4zjMVjaCZsAjzQRgYNx7J2uBxqKnI1LWLHuq3b-I"  # https://docs.google.com/spreadsheets/d/1WDn4zjMVjaCZsAjzQRgYNx7J2uBxqKnI1LWLHuq3b-I/edit#gid=0
res = sheets.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range="A1:Z99").execute()

pprint(res)
