import { Box, Divider, Grid } from "@material-ui/core";
import { observer } from "mobx-react-lite";
import React, { useState } from "react";

import { ActionButton } from "diaas/ActionButton.js";
import { Form, TextField, useFormValue } from "diaas/form.js";
import { SampleDataTable } from "diaas/sources/SampleDataTable.js";
import { useAppState } from "diaas/state.js";

export const StaticTable = observer(({ source }) => {
  const state = useAppState();
  const config = source.definition.config;
  const data = useFormValue(config.data);
  const id = useFormValue(source.id);
  const targetTable = useFormValue(config.target_table);

  const [rows, setRows] = useState([]);

  const submit = () => {
    return saveAndLoad();
  };
  const saveAndLoadLabel = useFormValue("Save and load");
  const saveAndLoad = () => {
    saveAndLoadLabel.v = "Saving...";
    return state.backend.postSource(source.id, { data: data.v, target_table: targetTable.v }).then(() => {
      saveAndLoadLabel.v = "Loading...";
      return state.backend.loadSource(source.id).then((data) => {
        saveAndLoadLabel.v = "Save and load";
        console.log("Load returned", data);
        setRows(data.rows);
        // return [update, load];
      });
    });
  };
  return (
    <Form onSubmit={submit}>
      <Grid container>
        <Grid item xs={12}>
          <TextField pb={4} label="ID" value={id} fullWidth={true} style={{ maxWidth: "600px" }} disabled={true} />
        </Grid>
        <Grid item xs={12}>
          <TextField pb={4} label="Target Table" value={targetTable} fullWidth={true} style={{ maxWidth: "600px" }} />
        </Grid>
      </Grid>
      <TextField
        label="Values"
        value={data}
        fullWidth={true}
        multiline={true}
        InputProps={{ style: { fontFamily: "monospace" } }}
      >
        {data.v}
      </TextField>
      <Box display="flex">
        <Box pr={2}>
          <ActionButton onClick={saveAndLoad}>{saveAndLoadLabel.v}</ActionButton>
        </Box>
        <Box>
          <ActionButton disabled={true}>Save only</ActionButton>
        </Box>
      </Box>
      <Box py={4}>
        <Divider />
      </Box>
      <p>Data:</p>
      <SampleDataTable rows={rows} />
    </Form>
  );
});
