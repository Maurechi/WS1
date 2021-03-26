import { useEffect, useState } from "react";
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

export const useLocalStorage = (key, initialValue) => {
  if (initialValue === undefined) {
    initialValue = null;
  }
  useEffect(() => {
    if (!window.localStorage.getItem(key)) {
      window.localStorage.setItem(key, JSON.stringify(initialValue));
    }
  });

  return useCell({
    store: (newValue) => {
      console.log("Storing", newValue, "under", key);
      window.localStorage.setItem(key, JSON.stringify(newValue));
      return newValue;
    },
    load: () => {
      console.log("Getting", key);
      return JSON.parse(window.localStorage.getItem(key));
    },
  });
};
