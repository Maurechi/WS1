import shlex
from datetime import datetime

from libds.source import Record, StaticSource
from libds.utils import yaml_load


def parse_text_rows(text):
    rows = []
    max_length = 0
    for line in text.split("\n"):
        if line.strip() == "":
            continue
        row = shlex.split(line)
        rows.append(row)
        max_length = max(max_length, len(row))

    regular_rows = []
    for row in rows:
        if len(row) < max_length:
            row = row + [""] * (max_length - len(row))
        regular_rows.append(row)

    return regular_rows


class StaticTable(StaticSource):
    def __init__(
        self,
        columns=None,
        rows=None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        if columns is None:
            columns = ["value"]
        self.columns = columns

        if rows is None:
            rows = []
        self.rows = rows

    @classmethod
    def load_from_yaml(cls, data_stack, path):
        data = yaml_load(path)
        table = data.get("table")
        headers = data.get("headers", True)

        rows = parse_text_rows(data["data"])
        if len(rows) == 0:
            columns = []
        if headers:
            columns = rows[0]
            rows = rows[1:]
        else:
            columns = ["c{i + 1}" for i in range(len(rows[0]))]

        return cls(data_stack=data_stack, table=table, rows=rows, columns=columns)

    def info(self):
        return self._info(
            num_rows=len(self.rows),
            columns=self.columns,
            rows=self.rows,
            table_name=self.table_name,
            schema_name=self.schema_name,
        )

    def collect_new_records(self, since):
        for row in self.rows:
            yield Record(
                data={key: value for key, value in zip(self.columns, row)},
                extracted_at=datetime.utcnow(),
            )
