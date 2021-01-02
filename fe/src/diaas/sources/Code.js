import React from "react";

export const Code = ({ source, user }) => {
  const { filename } = source.definition;
  return (
    <>
      <p>
        <b>{source.name}</b>
      </p>
      <pre>{filename}</pre>
    </>
  );
};
