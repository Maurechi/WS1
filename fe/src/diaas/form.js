import { Checkbox as MUICheckbox, Select as MUISelect, TextField as MUITextField } from "@material-ui/core";
import _ from "lodash";
import React, { createContext, useCallback, useContext, useState } from "react";
import * as uuid from "uuid";

import AceEditor from "diaas/AceEditor";
import { wrapInBox } from "diaas/ui.js";

export const makeValueObject = (store, load, onChange) => {
  if (!onChange) {
    onChange = () => null;
  }
  return {
    getter() {
      return load();
    },
    setter(newValue) {
      const value = load();
      if (newValue !== value) {
        onChange(newValue, value);
        store(newValue);
      }
      return newValue;
    },
    toggle() {
      return this.setter(!this.v);
    },
    get v() {
      return this.getter();
    },
    set v(newValue) {
      this.setter(newValue);
    },
  };
};

export const useLocalStorage = (key, initialValue) => {
  if (!window.localStorage.getItem(key)) {
    window.localStorage.setItem(key, JSON.stringify(initialValue));
  }

  let [value, setValue] = useState(JSON.parse(window.localStorage.getItem(key)));

  let [timer, setTimer] = useState(null);

  const store = (newValue) => {
    if (timer) {
      clearTimeout(timer);
    }
    timer = setTimeout(() => window.localStorage.setItem(key, JSON.stringify(value)), 500);
    setTimer(timer);

    value = newValue;
    setValue(newValue);
  };
  const load = () => {
    return value;
  };

  return makeValueObject(store, load);
};

export const useStateV = (initialValue) => {
  let [value, setValue] = useState(initialValue);
  return makeValueObject(
    (newValue) => {
      setValue(newValue);
      value = newValue;
    },
    () => value
  );
};

export const useFormValue = (initialValue, config) => {
  let { trim = true, parse = (x) => x, serialize = (x) => x } = config || {};

  if (trim) {
    const outer = serialize;
    serialize = (x) => {
      if (_.isString(x)) {
        x = _.trim(x);
      }
      return outer(x);
    };
  }

  let [isDirty, setIsDirty] = useState(false);
  let [isTouched, setIsTouched] = useState(false);

  let [value, setValue] = useState(initialValue);

  const store = (newValue) => {
    setIsDirty(true);
    setValue(serialize(newValue));
  };

  const load = () => parse(value);

  const o = makeValueObject(store, load);

  o.touch = () => {
    isTouched = true;
    setIsTouched(true);
  };

  Object.defineProperty(o, "isDirty", {
    get: () => isDirty,
  });

  Object.defineProperty(o, "isTouched", {
    get: () => isTouched,
  });

  return o;
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
    checked={value.v}
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

export const CodeEditor = ({ mode, value, disabled = false }) => {
  const [divId] = useState(uuid.v4());
  return (
    <AceEditor
      width="100%"
      mode={mode}
      theme="solarized_light"
      name={divId}
      value={value.v}
      onChange={value.setter}
      fontSize={14}
      readOnly={disabled}
      minLines={4}
      maxLines={Infinity}
    />
  );
};
