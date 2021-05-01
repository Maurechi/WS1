import { Grid, Typography } from "@material-ui/core";
import _ from "lodash";
import { observer } from "mobx-react-lite";
import React from "react";

import { SampleDataTable } from "diaas/DataTable.js";
import { Form, TextField, useFormValue } from "diaas/form.js";
import { useAppState } from "diaas/state.js";
import { ActionButton } from "diaas/ui.js";
export const StaticTable = observer(({ source }) => {
  const table = useFormValue(source.data.table);
  const data = useFormValue(source.data.data);
  const rows = source.info.rows.map((row) => Object.fromEntries(_.zip(source.info.columns, row)));
  const { backend } = useAppState();
  const save = () => {
    return backend
      .postFile("sources/" + source.filename, {
        data: data.v,
        table: table.v,
        type: source.data.type,
      })
      .then(() => {
        if (table.v !== source.data.table) {
          return backend.moveFile("sources/" + source.filename, "sources/" + table.v + ".yaml");
        } else {
          return null;
        }
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
