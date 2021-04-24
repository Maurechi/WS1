import React from "react";

import { CodeEditor, useFormValue } from "diaas/form.js";

export const Code = ({ source }) => {
  const value = useFormValue(source.code, { trim: false });
  return (
    <>
      <p>
        <tt>{source.id}</tt> defined in <tt>{source.filename}</tt>
      </p>
      <CodeEditor mode="python" value={value} disabled={true} />
    </>
  );
};
