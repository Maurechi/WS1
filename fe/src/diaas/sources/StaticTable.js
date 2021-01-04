import React from "react";

export const StaticTable = ({ source }) => {
  const { table } = source.definition.config;
  return (
    <>
      <p>
        <b>{source.name}</b>
      </p>
      <textarea rows={20} cols={60}>
        {table}
      </textarea>
    </>
  );
};
