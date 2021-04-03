import { useState } from "react";
// eslint-disable-next-line
export const ignore = (v) => null;

export const useCell = (config) => {
  let [isDirty, setIsDirty] = useState(false);
  let [isTouched, setIsTouched] = useState(false);

  const { store, load, onChange = (is, was) => ignore(is, was) } = config || {};

  return {
    getter() {
      return load();
    },
    setter(newValue) {
      const value = load();
      if (newValue !== value) {
        setIsDirty(true);
        onChange(newValue, value);
        store(newValue);
      }
      return newValue;
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

export const useLocalStorage = (key, initialValue) => {
  if (!window.localStorage.getItem(key)) {
    window.localStorage.setItem(key, JSON.stringify(initialValue));
  }

  let [value, setValue] = useState(JSON.parse(window.localStorage.getItem(key)));

  let [timer, setTimer] = useState(null);

  return useCell({
    store: (newValue) => {
      if (timer) {
        clearTimeout(timer);
      }
      timer = setTimeout(() => window.localStorage.setItem(key, JSON.stringify(value)), 500);
      setTimer(timer);

      value = newValue;
      setValue(newValue);
    },
    load: () => {
      return value;
    },
  });
};
