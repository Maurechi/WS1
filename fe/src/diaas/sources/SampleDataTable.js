// NOTE ideally this would be in Source.js, but we put it here to
// avoid recursive dependencies 20210116:mb
import "@inovua/reactdatagrid-community/index.css";
import ReactDataGrid from "@inovua/reactdatagrid-community";
import React from "react";

export const SampleDataTable = ({ rows }) => {
  if (rows.length === 0) {
    return <>No data.</>;
  }
  const columnNames = Object.keys(rows[0]);
  const columns = columnNames.map((c) => ({ name: c, header: c }));
  return <ReactDataGrid columns={columns} dataSource={rows} />;
};
