import json
import os
import re
from datetime import datetime
from urllib.parse import urlparse

import google.oauth2.service_account
from googleapiclient.discovery import build

from libds.source import Record, StaticSource
from libds.utils import yaml_load


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
        sheet_id,
        range,
        header_row,
        target_table,
        service_account_info,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.sheet_id = sheet_id
        self.range = range
        self.header_row = header_row
        self.target_table = target_table
        self.service_account_info = service_account_info

    @classmethod
    def load_from_yaml(cls, data_stack, file):
        data = yaml_load(file)

        sheet_id = lookup_spreadsheet_id(data["spreadsheet"])
        target_table = data["target_table"]
        range = data["range"]
        header_row = data["header_row"]
        service_account_json_var = data["service_account_json_var"]
        service_account_json = os.environ.get(service_account_json_var)
        service_account_info = json.loads(service_account_json)

        return cls(sheet_id, range, header_row, target_table, service_account_info)

    def info(self):
        return self._info(
            sheet_id=self.sheet_id,
            range=self.range,
            header_row=self.header_row,
        )

    def collect_new_records(self, since):
        credentials = (
            google.oauth2.service_account.Credentials.from_service_account_info(
                self.service_account_info
            )
        )

        service = build("sheets", "v4", credentials=credentials)
        sheets = service.spreadsheets()
        response = (
            sheets.values()
            .get(
                spreadsheetId=self.sheet_id,
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
            yield Record(
                data={key: value for key, value in zip(columns, row)},
                extracted_at=datetime.utcnow(),
            )
