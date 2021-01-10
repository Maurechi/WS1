import { Box, Grid } from "@material-ui/core";
import { observer } from "mobx-react-lite";
import React from "react";

import { ActionButton } from "diaas/ActionButton.js";
import { TextField, useFormValue } from "diaas/form.js";
import { useAppState } from "diaas/state.js";

export const StaticTable = observer(({ source }) => {
  const state = useAppState();
  const config = source.definition.config;
  const data = useFormValue(config.data);
  const id = useFormValue(source.id);
  const targetTable = useFormValue(config.target_table);

  const submit = () => {
    return saveAndLoad();
  };
  const saveAndLoadLabel = useFormValue("Save and load");
  const saveAndLoad = () => {
    saveAndLoadLabel.v = "Saving...";
    return state.backend.post(`/sources/${source.id}`, { data: data.v, target_table: targetTable.v }).then((update) => {
      saveAndLoadLabel.v = "Loading...";
      return state.backend.post(`/sources/${source.id}/load`).then((load) => {
        saveAndLoadLabel.v = "Save and load";
        return [update, load];
      });
    });
  };
  return (
    <form onSubmit={submit}>
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
        <Box pr={2}>
          <ActionButton disabled={true}>Save and truncate and load</ActionButton>
        </Box>
        <Box>
          <ActionButton disabled={true}>Save only</ActionButton>
        </Box>
      </Box>
    </form>
  );
});
