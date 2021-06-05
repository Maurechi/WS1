import { Box, Grid } from "@material-ui/core";
import { observer } from "mobx-react-lite";
import React, { createRef, useState } from "react";

import { SampleDataTable } from "diaas/DataTable.js";
import { CodeEditor, useLocalStorage } from "diaas/form.js";
import { useAppState } from "diaas/state.js";
import { ActionButton, StandardButton as Button, useResize } from "diaas/ui.js";

export const CellData = React.memo((props) => <SampleDataTable {...props} />);

export const Cell = observer(({ value }) => {
  const { backend } = useAppState();
  const [rows, setRows] = useState([]);
  const ref = createRef();
  const { width } = useResize(ref);
  const run = () => {
    return backend.execute({ statement: value.v }).then((data) => {
      setRows(data.rows);
    });
  };

  return (
    <>
      <Grid container ref={ref}>
        <Grid item xs={12}>
          <CodeEditor mode="sql" value={value} />
        </Grid>
        <Grid item xs={6}>
          <ActionButton onClick={run}>Run</ActionButton>
        </Grid>
        <Grid item xs={6}>
          <Button>Delete Cell</Button>
        </Grid>
        <Grid item xs={12}>
          {rows && (
            <>
              <hr />
              <Box style={{ overflow: "scroll", maxWidth: width }}>
                <CellData rows={rows} />
              </Box>
            </>
          )}
        </Grid>
      </Grid>
      <hr />
    </>
  );
});

export const Notebook = ({ id, baseTable }) => {
  const values = useLocalStorage(`diaas:Notebook/${id}/cells`, [`select *\nfrom ${baseTable}\nlimit 23`]);

  const newCellClick = () => {
    values.v = values.v.concat([`select *\nfrom ${baseTable}\nlimit 23`]);
  };

  const cellValues = values.v.map((_, i) => {
    return {
      get v() {
        return values.v[i];
      },
      setter(newValue) {
        let newValues = values.v.slice();
        newValues[i] = newValue;
        values.v = newValues;
      },
    };
  });

  return (
    <Grid container spacing={2}>
      {cellValues.map((v, i) => (
        <Grid item xs={12} key={i}>
          <Cell value={v} />
        </Grid>
      ))}
      <Grid item key="+1" xs={12}>
        <Button onClick={newCellClick}>New Cell</Button>
      </Grid>
    </Grid>
  );
};
