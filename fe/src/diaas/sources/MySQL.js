import React from "react";

export const MySQL = ({ source }) => {
  const Row = ({ label, children }) => (
    <tr>
      <td>{label}</td>
      <td>{children}</td>
    </tr>
  );
  return (
    <table>
      <Row label="Host">
        <input value={source.data.connect_args.host} />
      </Row>
      <Row label="Username">
        <input value={source.data.connect_args.username} />
      </Row>
      <Row label="Password">
        <input value={source.data.connect_args.password} />
      </Row>
      <Row label="Database">
        <input value={source.data.connect_args.database} />
      </Row>
    </table>
  );
};
