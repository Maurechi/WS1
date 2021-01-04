import { Grid } from "@material-ui/core";
import React from "react";

import { ActionButton } from "diaas/ActionButton.js";
import { TextField, useFormValue } from "diaas/form.js";

export const StaticTable = ({ source }) => {
  const { table } = source.definition.config;
  const sourceValue = useFormValue(table);
  const idValue = useFormValue(source.id);
  const targetTableValue = useFormValue("SCHEMA.TABLE");

  const submit = () => {
    console.log("Will update to", sourceValue.v);
  };
  const saveAndLoad = () => {
    return new Promise(() => null);
  };
  return (
    <form onSubmit={submit}>
      <Grid container>
        <Grid item xs={12}>
          <TextField pb={4} label="ID" value={idValue} fullWidth={true} style={{ maxWidth: "600px" }} disabled={true} />
        </Grid>
        <Grid item xs={12}>
          <TextField
            pb={4}
            label="Target Table"
            value={targetTableValue}
            fullWidth={true}
            style={{ maxWidth: "600px" }}
          />
        </Grid>
      </Grid>
      <TextField
        label="Values"
        value={sourceValue}
        fullWidth={true}
        multiline={true}
        InputProps={{ style: { fontFamily: "monospace" } }}
      >
        {table}
      </TextField>
      <ActionButton onClick={saveAndLoad}>Save and Load</ActionButton>
    </form>
  );
};
