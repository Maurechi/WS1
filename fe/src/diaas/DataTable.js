// NOTE ideally this would be in Source.js, but we put it here to
// avoid recursive dependencies 20210116:mb
import { makeStyles, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow } from "@material-ui/core";
import { parseCss, rgbToHsl } from "colorsys";
import _ from "lodash";
import React, { useMemo } from "react";

const tableStyles = makeStyles({
  table: {
    minWidth: 650,
  },
});

export const DataTable = ({ columns = null, rows = null }) => {
  if (columns === null) {
    if (rows !== null && rows.length > 0) {
      columns = rows[0].map(() => ({ style: {} }));
    } else {
      columns = [];
    }
  }
  const classes = tableStyles();

  rows = rows.map((row) => _.zip(row, columns).map((x) => ({ value: x[0], style: x[1].style })));

  const haveLabels = columns !== null && _.every(columns, (c) => c.label);

  return (
    <TableContainer component={Paper}>
      <Table className={classes.table} size="small">
        {haveLabels && (
          <TableHead>
            <TableRow>
              {columns.map((c, i) => (
                <TableCell key={i}>{c.label}</TableCell>
              ))}
            </TableRow>
          </TableHead>
        )}
        {rows !== null && (
          <TableBody>
            {rows.map((row, i) => (
              <TableRow key={i}>
                {row.map((r, j) => (
                  <TableCell key={j} style={r.style}>
                    {r.value}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        )}
      </Table>
    </TableContainer>
  );
};

export const SampleDataTable = ({ rows }) => {
  const pformat = (v) => {
    const StandOut = ({ children }) => <span style={{ color: "blue" }}>{children}</span>;
    if (v === null) {
      return <tt>NULL</tt>;
    } else if (_.isNumber(v)) {
      return (
        <tt>
          <StandOut>=</StandOut>
          {v}
        </tt>
      );
    } else if (_.isString(v)) {
      if (v.match(/^#[a-f0-9]{6}$/)) {
        const hsl = rgbToHsl(parseCss(v));
        const color = hsl.l < 50 ? "#ffffff" : "#000000";

        return <span style={{ backgroundColor: v, color: color }}>{v}</span>;
      } else {
        let parts = [];
        v.split(/((?<!\\)\n| )/).forEach((section) => {
          if (section === "\n") {
            parts.push(<StandOut key={parts.length}>\n</StandOut>);
          } else if (section === " ") {
            parts.push(<StandOut key={parts.length}>{"\u2423"}</StandOut>);
          } else {
            parts.push(<span key={parts.length}>{section}</span>);
          }
        });

        return (
          <tt>
            <StandOut>"</StandOut>
            {parts}
            <StandOut>"</StandOut>
          </tt>
        );
      }
    } else {
      return (
        <tt>
          <StandOut>(</StandOut>
          {v}
          <StandOut>)</StandOut>
        </tt>
      );
    }
  };

  const columns = useMemo(() => _.keys(rows[0]).map((c) => ({ label: c, property: c })), [rows]);
  const rowArrays = useMemo(() => _.map(rows, (r) => _.map(columns, (c) => pformat(r[c.property]))), [rows, columns]);

  if (rows.length === 0) {
    return <>No data.</>;
  } else {
    return <DataTable columns={columns} rows={rowArrays} />;
  }
};
