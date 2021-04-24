// NOTE ideally this would be in Source.js, but we put it here to
// avoid recursive dependencies 20210116:mb
import { makeStyles, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow } from "@material-ui/core";
import _ from "lodash";
import React from "react";

const tableStyles = makeStyles({
  table: {
    minWidth: 650,
  },
});

export const SampleDataTable = ({ rows }) => {
  if (rows.length === 0) {
    return <>No data.</>;
  }
  const columns = _(rows[0])
    .keys()
    .map((c) => ({ field: c, header: c }))
    .value();

  const classes = tableStyles();

  console.log(columns, rows);

  return (
    <TableContainer component={Paper}>
      <Table className={classes.table} size="small" aria-label="a dense table">
        <TableHead>
          <TableRow>
            {columns.map((c) => (
              <TableCell key={c.field}>{c.header}</TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {rows.map((row, i) => (
            <TableRow key={"r" + i}>
              {columns.map((c) => (
                <TableCell key={"r" + i + "c" + c.field}>{row[c.field]}</TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};
