import _ from "lodash";
import { observer } from "mobx-react-lite";
import React from "react";

import { DataTable } from "diaas/DataTable.js";
import { Checkbox, TextField, useFormValue } from "diaas/form.js";
import { useSourceFileUpdater } from "diaas/sources/common.js";
import { ActionButton, ContentTitle } from "diaas/ui.js";

export const iconURL = "google-sheets.svg";
export const label = "Google Sheet";

const SettingsTable = ({ src_id, spreadsheet, target_table, range, headerRow, service_account_json_var }) => {
  const rows = [
    ["Spreadsheet (ID or URL)", <TextField value={spreadsheet} fullWidth={true} />],
    ["Table", <TextField value={target_table} fullWidth={true} />],
    ["Range", <TextField value={range} fullWidth={true} />],
    ["Header Row", <Checkbox value={headerRow} />],
    ["Service Account JSON from var", <TextField value={service_account_json_var} fullWidth={true} />],
  ];

  const saveEnabled = _.trim(spreadsheet.v) && _.trim(target_table.v);
  const sourceFileUpdater = useSourceFileUpdater();

  const save = () => {
    return sourceFileUpdater({
      src_id: src_id,
      dst_id: target_table.v,
      data: {
        type: "libds.source.google.GoogleSheet",
        spreadsheet: spreadsheet.v,
        target_table: target_table.v,
        range: range.v,
        header_row: !!headerRow.v,
        service_account_json_var: service_account_json_var.v,
      },
    });
  };

  return (
    <>
      <DataTable rows={rows} columns={[{ style: { width: "20%" } }, { style: {} }]} />
      <ActionButton enabled={saveEnabled} onClick={save}>
        Save
      </ActionButton>
    </>
  );
};

export const Creator = observer(() => {
  const spreadsheet = useFormValue("");
  const target_table = useFormValue("");
  const range = useFormValue("A1:ZZ999");
  const headerRow = useFormValue(true);
  const service_account_json_var = useFormValue("CARAVEL_SERVICE_ACCOUNT_JSON");

  return (
    <>
      <ContentTitle iconURL={iconURL}>Creating new Google Sheet Source</ContentTitle>
      <SettingsTable
        src_id={target_table.v}
        spreadsheet={spreadsheet}
        target_table={target_table}
        range={range}
        headerRow={headerRow}
        service_account_json_var={service_account_json_var}
      />
    </>
  );
});

export const Editor = ({ source }) => {
  const spreadsheet = useFormValue(source.data.spreadsheet);
  const target_table = useFormValue(source.data.target_table);
  const range = useFormValue(source.data.range);
  const headerRow = useFormValue(source.data.header_row);
  const service_account_json_var = useFormValue(source.data.service_account_json_var);

  return (
    <>
      <ContentTitle iconURL={iconURL}>Editing Google Sheet for {target_table.v}</ContentTitle>
      <SettingsTable
        src_id={source.id}
        spreadsheet={spreadsheet}
        target_table={target_table}
        range={range}
        headerRow={headerRow}
        service_account_json_var={service_account_json_var}
      />
    </>
  );
};
