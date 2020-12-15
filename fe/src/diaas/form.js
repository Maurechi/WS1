import { Checkbox as MUICheckbox, Select as MUISelect, TextField as MUITextField } from "@material-ui/core";
import React, { useState } from "react";
import v from "voca";

export const useFormValue = (initialValue, config) => {
  let [value, setValue] = useState(initialValue);
  let [isDirty, setIsDirty] = useState(false);
  let [isTouched, setIsTouched] = useState(false);

  const { transform = (x) => x } = config || {};
  return {
    getter() {
      return transform(value);
    },
    setter(newValue) {
      newValue = transform(newValue);
      if (newValue !== value) {
        setIsDirty(true);
        setValue(newValue);
        value = newValue;
      }
      return value;
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

export const TextField = ({ value, ...TextFieldProps }) => (
  <MUITextField
    onChange={(e) => value.setter(e.target.value)}
    value={v.trim(value.v)}
    inputProps={{ onBlur: () => value.touch() }}
    {...TextFieldProps}
  />
);

export const Checkbox = ({ value, ...CheckboxProps }) => (
  <MUICheckbox
    value={value.v}
    onChange={(e) => {
      value.setter(e.target.checked);
      value.touched();
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