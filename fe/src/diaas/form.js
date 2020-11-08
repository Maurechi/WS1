import { TextField } from "@material-ui/core";
import React, { useState } from "react";
import v from "voca";

export const useFormValue = (initialValue) => {
  let [value, setValue] = useState(initialValue);
  return {
    getter() {
      return value;
    },
    setter(newValue) {
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

export const TextInput = ({ label, value, trim = true }) => (
  <TextField
    label={label}
    defaultValue={value.v}
    onChange={(e) => value.setter(trim ? v.trim(e.target.value) : e.target.value)}
  />
);
