import React from "react";

import { CodeEditor, useFormValue } from "diaas/form.js";

export const Code = ({ source }) => {
  const { filename, code } = source.definition;
  const value = useFormValue(code);
  return (
    <>
      <p>
        <tt>{source.id}</tt> defined in <tt>{filename}</tt>
      </p>
      <CodeEditor mode="python" value={value} disabled={true} />
    </>
  );
};
