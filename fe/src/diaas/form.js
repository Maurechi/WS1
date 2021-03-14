import { Checkbox as MUICheckbox, Select as MUISelect, TextField as MUITextField } from "@material-ui/core";
import React, { createContext, useCallback, useContext, useState } from "react";
import v from "voca";

import { wrapInBox } from "diaas/ui.js";
import { ignore } from "diaas/utils.js";

export const useFormValue = (initialValue, config) => {
  let [value, setValue] = useState(initialValue);
  let [isDirty, setIsDirty] = useState(false);
  let [isTouched, setIsTouched] = useState(false);

  const { transform = (x) => x, trim = true, onChange = (is, was) => ignore(is, was) } = config || {};
  return {
    getter() {
      return transform(value);
    },
    setter(newValue) {
      newValue = transform(newValue);
      if (trim) {
        newValue = v.trim(newValue);
      }
      if (newValue !== value) {
        setIsDirty(true);
        onChange(newValue, value);
        value = newValue;
        setValue(newValue);
      }
      return value;
    },
    toggle() {
      return this.setter(!this.v);
    },
    touch() {
      isTouched = true;
      setIsTouched(true);
    },
    get v() {
      return this.getter();
    },
    set v(newValue) {
      this.setter(newValue);
    },
    get isDirty() {
      return isDirty;
    },
    get isTouched() {
      return isTouched;
    },
  };
};

export const TextField = wrapInBox(({ value, onChange: callerOnChange, inputProps = {}, ...TextFieldProps }) => {
  inputProps["onBlur"] = useCallback(() => value.touch(), [value]);
  const form = useFormData();
  const onKeyDown = useCallback(
    (e) => {
      if (e.ctrlKey && e.key === "Enter") {
        form.submit();
      }
    },
    [form]
  );

  const onChange = useCallback(
    (e) => {
      if (e.target.value !== value.v) {
        const was = value.v;
        value.v = e.target.value;
        if (callerOnChange) {
          callerOnChange(value.v, was);
        }
      }
    },
    [value, callerOnChange]
  );

  inputProps["onKeyUp"] = onChange;
  if (form && form.submit) {
    inputProps["onKeyDown"] = onKeyDown;
  }
  return <MUITextField onChange={onChange} value={value.v || ""} inputProps={inputProps} {...TextFieldProps} />;
});

export const Checkbox = ({ value, ...CheckboxProps }) => (
  <MUICheckbox
    value={value.v}
    onChange={(e) => {
      value.setter(e.target.checked);
      value.touch();
    }}
    {...CheckboxProps}
  />
);

export const Select = ({ value, children, ...SelectProps }) => (
  <MUISelect
    value={value.v}
    onChange={(e) => value.setter(e.target.value)}
    onBlur={() => value.touch()}
    {...SelectProps}
  >
    {children}
  </MUISelect>
);

const FormContext = createContext();

const useFormData = () => useContext(FormContext);

export const Form = ({ children, onSubmit }) => {
  const formData = { submit: onSubmit };
  return (
    <FormContext.Provider value={formData}>
      <form onSubmit={onSubmit}>{children}</form>
    </FormContext.Provider>
  );
};
