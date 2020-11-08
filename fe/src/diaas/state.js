import axios from "axios";
import _ from "lodash";
import { action, makeAutoObservable } from "mobx";
import { createContext, useContext } from "react";

class Backend {
  constructor() {
    this.axios = axios.create({
      baseURL: "//" + window.location.host + "/api/1/",
      validateStatus: (status) => _.includes([200, 201, 204, 404], status),
    });
  }

  getCurrentUser() {
    return this.axios.get("user").then((res) => {
      if (res.status === 404) {
        return null;
      } else {
        return res.data.data;
      }
    });
  }

  login(email) {
    return Promise.resolve({ code: "abcd", email: email });
    return this.axios.post("user", { email: email }).then((res) => {
      if (res.status === 200) {
        return res.data.data;
      } else {
        return null;
      }
    });
  }
}

class AppStateObject {
  user = null;
  initialized = false;

  constructor() {
    makeAutoObservable(this);
    this.backend = new Backend();
  }

  initialize() {
    this.backend.getCurrentUser().then(
      action("setCurrentUser", (user) => {
        this.initialized = true;
        this.user = user;
      })
    );
  }

  login(email) {
    this.backend.login(email).then(
      action("login", (user) => {
        this.user = user;
      })
    );
  }
}

export const AppStateContext = createContext();

export const useAppState = () => {
  return useContext(AppStateContext);
};

export const APP_STATE = new AppStateObject();

export const AppState = ({ children }) => (
  <AppStateContext.Provider value={APP_STATE}>{children}</AppStateContext.Provider>
);
