import React from "react";

export const GoogleSheet = ({ source, user }) => {
  const { spreadsheet_id, range } = source.definition.config;
  return (
    <>
      <p>
        <b>{source.name}</b>
      </p>
      <table>
        <tr>
          <td>
            <b>Spreadsheet ID:</b>
          </td>
          <td>
            <input type="text" value={spreadsheet_id} />
          </td>
        </tr>
        <tr>
          <td>
            <b>Range:</b>
          </td>
          <td>
            <input type="text" value={range} />
          </td>
        </tr>
      </table>
    </>
  );
};
