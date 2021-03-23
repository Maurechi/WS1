import { Box, Divider } from "@material-ui/core";
import React, { useState } from "react";

import { TextField, useFormValue } from "diaas/form.js";
import { SampleDataTable } from "diaas/SampleDataTable.js";
import { useAppState } from "diaas/state.js";
import { ActionButton } from "diaas/ui.js";

export const GoogleSheet = ({ source }) => {
  const state = useAppState();
  const config = source.definition.config;
  const targetTable = useFormValue(config.target_table);

  const spreadsheet = useFormValue(config.spreadsheet);
  const range = useFormValue(config.range);
  const service_account_info = useFormValue(config.service_account_info);

  const [rows, setRows] = useState([]);
  const save = () => {
    saveAndLoadLabel.v = "Saving...";
    return state.backend
      .postSource(source.id, {
        type: source.type,
        spreadsheet: spreadsheet.v,
        range: range.v,
        service_account_info: service_account_info.v,
        target_table: targetTable.v,
      })
      .then(() => {
        saveAndLoadLabel.v = "Save and Load";
      });
  };
  const saveAndLoadLabel = useFormValue("Save and Load");
  const saveAndLoad = () => {
    return save().then(() => {
      saveAndLoadLabel.v = "Loading...";
      return state.backend.loadSource(source.id).then((data) => {
        saveAndLoadLabel.v = "Save and Load";
        console.log("Load returned", data);
        setRows(data.rows);
        // return [update, load];
      });
    });
  };
  return (
    <>
      <p>
        <b>{source.name}</b>
      </p>
      <table>
        <tr>
          <td>
            <b>Spreadsheet:</b>
          </td>
          <td>
            <TextField type="text" value={spreadsheet} />
          </td>
        </tr>
        <tr>
          <td>
            <b>Range:</b>
          </td>
          <td>
            <TextField type="text" value={range} />
          </td>
        </tr>
        <tr>
          <td>
            <b>Service Account:</b>
          </td>
          <td>
            <TextField value={service_account_info} />
          </td>
        </tr>
      </table>
      <Box display="flex">
        <Box pr={2}>
          <ActionButton onClick={saveAndLoad}>{saveAndLoadLabel.v}</ActionButton>
        </Box>
        <Box>
          <ActionButton onClick={save}>Save only</ActionButton>
        </Box>
      </Box>
      <Box py={4}>
        <Divider />
      </Box>
      <p>Data:</p>
      <SampleDataTable rows={rows} />
    </>
  );
};
