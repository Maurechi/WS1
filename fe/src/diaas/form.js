import { TextField } from "@material-ui/core";
import React, { useState } from "react";
import v from "voca";

export const useFormValue = (initialValue, config) => {
  let [value, setValue] = useState(initialValue);
  const { transform = (x) => x } = config || {};
  return {
    getter() {
      return transform(value);
    },
    setter(newValue) {
      newValue = transform(newValue);
      setValue(newValue);
      value = newValue;
      return newValue;
    },
    get v() {
      return this.getter();
    },
    set v(newValue) {
      this.setter(newValue);
    },
  };
};

export const TextInput = ({ value, ...TextFieldProps }) => (
  <TextField defaultValue={v.trim(value.v)} onChange={(e) => value.setter(e.target.value)} {...TextFieldProps} />
);
