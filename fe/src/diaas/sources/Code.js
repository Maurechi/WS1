import React from "react";

export const Code = ({ source }) => {
  const { filename, code } = source.definition;
  return (
    <>
      <p>
        <tt>{source.id}</tt> defined in <tt>{filename}</tt>
      </p>
      <pre>{code}</pre>
    </>
  );
};
