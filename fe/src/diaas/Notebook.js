import React, { useState } from "react";

import { CodeEditor, useFormValue } from "diaas/form.js";
import { SampleDataTable } from "diaas/SampleDataTable.js";
import { useAppState } from "diaas/state.js";
import { StandardButton as Button } from "diaas/ui.js";

export const Cell = () => {
  const value = useFormValue("select 1", { trim: false });
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
};

export const Notebook = () => {
  const [cells, setCells] = useState([<Cell />]);

  const newCellClick = () => {
    setCells(cells.concat([<Cell />]));
  };

  return (
    <ul style={{ listStyle: "none" }}>
      {cells.map((e, i) => (
        <li key={i}>
          <Cell />
        </li>
      ))}
      <li key="add-cell">
        <Button onClick={newCellClick}>New Cell</Button>
      </li>
    </ul>
  );
};
