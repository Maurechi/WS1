import { Grid } from "@material-ui/core";
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
  const saveAndLoad = () => {
    return state.backend.post(`/sources/${source.id}`, { data: data.v, target_table: targetTable.v }).then((res) => {
      return res;
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
      <ActionButton onClick={saveAndLoad}>Save and Load</ActionButton>
    </form>
  );
});
