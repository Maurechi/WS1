import { Grid, Typography } from "@material-ui/core";
import _ from "lodash";
import { observer } from "mobx-react-lite";
import React from "react";
import { useHistory } from "react-router-dom";

import { SampleDataTable } from "diaas/DataTable.js";
import { Form, TextField, useFormValue } from "diaas/form.js";
import { useAppState } from "diaas/state.js";
import { ActionButton } from "diaas/ui.js";

export const iconURL = "csv.png";
export const label = "Manual Data Entry";

const useSourceFileUpdater = () => {
  const { user, backend } = useAppState();
  const history = useHistory();
  return ({ src_id, dst_id, data }) => {
    const src = `sources/${src_id}.yaml`;
    const dst = `sources/${dst_id}.yaml`;

    return backend
      .postFile(src, data)
      .then(() => {
        if (src !== dst) {
          return backend.moveFile(src, dst);
        } else {
          return Promise.resolve(null);
        }
      })
      .then(() => {
        return backend.sourceInfo(dst_id);
      })
      .then((source) => {
        let sources = user.data_stacks[0].sources;
        sources = _.filter(sources, (s) => s.id !== src_id);
        sources.push(source);
        user.data_stacks[0].sources = sources;
        return history.replace(`/sources/${dst_id}`);
      });
  };
};

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

  const sourceFileUpdater = useSourceFileUpdater();

  const save = () => {
    const src_id = source.filename === null ? table.v : source.data.table;
    const dst_id = table.v;
    return sourceFileUpdater({
      src_id,
      dst_id,
      data: {
        data: data.v,
        table: table.v,
        type: source.data.type,
      },
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
