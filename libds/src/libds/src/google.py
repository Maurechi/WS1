import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import google.oauth2.service_account
from googleapiclient.discovery import build

from libds.src import Row, StaticSource


def lookup_spreadsheet_id(spreadsheet):
    try:
        # https://docs.google.com/spreadsheets/d/1WDn4zjMVjaCZsAjzQRgYNx7J2uBxqKnI1LWLHuq3b-I/edit#gid=0
        url = urlparse(spreadsheet)
        if url.path is not None:
            m = re.match("/spreadsheets/d/([^/]+)", url.path)
            if m:
                return m[1]
        return spreadsheet
    except ValueError:
        return spreadsheet


class GoogleSheet(StaticSource):
    def __init__(
        self,
        service_account_file=None,
        service_account_info=None,
        spreadsheet=None,
        range=None,
        header_row=True,
        **kwargs,
    ):
        super().__init__(**kwargs)
        if service_account_info and service_account_file:
            raise ValueError(
                "Attempting to set both service_account_file and service_account_json, exaclty one must be specified."
            )
        if service_account_info is None and service_account_file is None:
            raise ValueError(
                "One of either service_account_file or service_account_json must be set."
            )
        if service_account_file is not None:
            self.service_account_file = Path(service_account_file)
        else:
            self.service_account_file = None

        if service_account_info is not None:
            if isinstance(service_account_info, str):
                self.service_account_info = json.loads(service_account_info)
            elif isinstance(service_account_info, dict):
                self.service_account_info = service_account_info
            else:
                raise ValueError(
                    "service_account_info must be a str, of properly formatted json, or a dict."
                )
        else:
            self.service_account_info = None

        self.spreadsheet = spreadsheet
        self.range = range
        self.header_row = header_row

    def info(self):
        return self._info(
            spreadsheet=self.spreadsheet,
            range=self.range,
        )

    def collect_new_records(self, since):
        if self.service_account_file is not None:
            service_account_info = json.load(self.service_account_file.open("r"))
        else:
            service_account_info = self.service_account_info
        credentials = (
            google.oauth2.service_account.Credentials.from_service_account_info(
                service_account_info
            )
        )

        service = build("sheets", "v4", credentials=credentials)
        sheets = service.spreadsheets()
        response = (
            sheets.values()
            .get(
                spreadsheetId=lookup_spreadsheet_id(self.spreadsheet),
                range=self.range,
                majorDimension="ROWS",
                valueRenderOption="UNFORMATTED_VALUE",
            )
            .execute()
        )
        values = response["values"]
        if len(values) == 0:
            rows = []
            columns = []
        else:
            first_row = values[0]
            if self.header_row:
                columns = first_row
                rows = values[1:]
            else:
                columns = [str(i) for i in range(len(values[0]))]
                rows = values

        for row in rows:
            yield Row(
                primary_key=None,
                data={key: value for key, value in zip(columns, row)},
                valid_at=datetime.utcnow(),
            )
