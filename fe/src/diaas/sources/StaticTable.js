import { Grid, Typography } from "@material-ui/core";
import _ from "lodash";
import { observer } from "mobx-react-lite";
import React from "react";

import { SampleDataTable } from "diaas/DataTable.js";
import { Form, TextField, useFormValue } from "diaas/form.js";
import { useAppState } from "diaas/state.js";
import { ActionButton } from "diaas/ui.js";

export const iconURL = "csv.png";
export const label = "Manual Data Entry";

export const Editor = observer(({ source }) => {
  if (!source) {
    source = {
      data: {
        table: null,
        data: "",
        type: "libds.source.static.StaticTable",
      },
      info: {
        rows: [],
        columns: [],
      },
      filename: null,
    };
  }
  const table = useFormValue(source.data.table);
  const data = useFormValue(source.data.data, { trim: false });
  const rows = source.info.rows.map((row) => Object.fromEntries(_.zip(source.info.columns, row)));
  const { backend } = useAppState();
  const save = () => {
    let src, dst;
    if (source.filename === null) {
      src = `sources/${table.v}.yaml`;
      dst = src;
    } else {
      src = `sources/${source.filename}`;
      dst = `sources/${table.v}.yaml`;
    }
    return backend
      .postFile(src, {
        data: data.v,
        table: table.v,
        type: source.data.type,
      })
      .then(() => {
        return src !== dst ? backend.moveFile(src, dst) : null;
      });
  };
  return (
    <Form onSubmit={save}>
      <Grid container spacing={2}>
        <Grid item xs={12}>
          <TextField pb={4} label="Table" value={table} fullWidth={true} style={{ maxWidth: "600px" }} />
        </Grid>
        <Grid item xs={6}>
          <Typography variant="h6">Value Input</Typography>
          <TextField value={data} fullWidth={true} multiline={true} InputProps={{ style: { fontFamily: "monospace" } }}>
            {data.v}
          </TextField>
          <ActionButton onClick={save}>Save</ActionButton>
        </Grid>
        <Grid item xs={6}>
          <Typography variant="h6">Value Table</Typography>
          <SampleDataTable rows={rows} />
        </Grid>
      </Grid>
    </Form>
  );
});

export const Creator = Editor;
