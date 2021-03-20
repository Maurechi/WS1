import shlex
from datetime import datetime

from libds.source import Record, StaticSource


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
    def from_config(cls, config):
        init_args = dict(
            table_name=config.get("table_name", None), name=config.get("name", None)
        )

        if "data" in config:
            return StaticTable.from_data(
                config["data"], header=config.get("header", True), **init_args
            )
        else:
            if "rows" not in config:
                raise ValueError(
                    "Config has neither `data` nor `rows`, there is nothing here."
                )
            rows = config["rows"]
            if "columns" not in config:
                columns = ["c{i + 1}" for i in range(len(rows[0]))]
            else:
                columns = config["columns"]
            return StaticTable(columns=columns, rows=rows, **init_args)

    def info(self):
        return self._info(num_rows=len(self.rows))

    def collect_new_records(self, since):
        for row in self.rows:
            yield Record(
                primary_key=None,
                data={key: value for key, value in zip(self.columns, row)},
                valid_at=datetime.utcnow(),
            )

    @classmethod
    def from_data(cls, data, header=True, **init_args):
        columns = None
        rows = []

        for line in data.split("\n"):
            if line.strip() == "":
                continue
            row = shlex.split(line)
            if columns is None:
                if header:
                    columns = row
                    continue
                else:
                    columns = ["c{i + 1}" for i in range(len(row))]

            if len(row) < len(columns):
                row = row + [""] * (len(columns) - len(row))
            rows.append(row)

        return StaticTable(columns=columns, rows=rows, **init_args)


class StaticJSONs(StaticSource):
    def __init__(
        self,
        values=None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        if values is None:
            values = []
        self.values = values

    def info(self):
        return self._info(first_value=self.values[0], num_values=len(self.values))

    def collect_new_records(self, since):
        yield from self.values
