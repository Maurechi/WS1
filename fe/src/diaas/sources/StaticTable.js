import { Box, Grid } from "@material-ui/core";
import _ from "lodash";
import { observer } from "mobx-react-lite";
import React from "react";

import { Form, TextField, useFormValue } from "diaas/form.js";
import { SampleDataTable } from "diaas/SampleDataTable.js";
export const StaticTable = observer(({ source }) => {
  const table = useFormValue(source.data.table);
  const data = useFormValue(source.data.data);
  const rows = source.info.rows.map((row) => Object.fromEntries(_.zip(source.info.columns, row)));
  const submit = () => null;
  return (
    <Form onSubmit={submit}>
      <Grid container>
        <Grid item xs={12}>
          <TextField pb={4} label="Table" value={table} fullWidth={true} style={{ maxWidth: "600px" }} />
        </Grid>
        <Grid item xs={6}>
          <Box p={4}>
            <TextField
              label="Values"
              value={data}
              fullWidth={true}
              multiline={true}
              InputProps={{ style: { fontFamily: "monospace" } }}
            >
              {data.v}
            </TextField>
          </Box>
        </Grid>
        <Grid item xs={6}>
          <Box p={4}>
            <SampleDataTable rows={rows} />
          </Box>
        </Grid>
      </Grid>
    </Form>
  );
});
