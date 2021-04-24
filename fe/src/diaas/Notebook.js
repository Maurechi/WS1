import { observer } from "mobx-react-lite";
import React, { useState } from "react";

import { SampleDataTable } from "diaas/DataTable.js";
import { CodeEditor, useLocalStorage } from "diaas/form.js";
import { useAppState } from "diaas/state.js";
import { StandardButton as Button } from "diaas/ui.js";

export const Cell = observer(({ value }) => {
  const {
    user: { dataStack: ds },
    backend,
  } = useAppState();
  const [rows, setRows] = useState([]);
  const run = () => {
    backend.execute({ statement: value.v }).then((data) => {
      setRows(data);
    });
  };

  return (
    <>
      <CodeEditor mode="sql" value={value} />
      <Button onClick={run}>Run against {ds.config.name}</Button>
      <Button>Delete Cell</Button>
      {rows && (
        <>
          <hr />
          <SampleDataTable rows={rows} />
        </>
      )}
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
    <ul style={{ listStyle: "none" }}>
      {cellValues.map((v, i) => (
        <li key={i}>
          <Cell value={v} />
        </li>
      ))}
      <li key="add-cell">
        <Button onClick={newCellClick}>New Cell</Button>
      </li>
    </ul>
  );
};
