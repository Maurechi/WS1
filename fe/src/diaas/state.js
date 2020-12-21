import axios from "axios";
import _ from "lodash";
import { makeAutoObservable } from "mobx";
import { createContext, useContext } from "react";

class Backend {
  constructor() {
    this.axios = axios.create({
      baseURL: "//" + window.location.host + "/api/1/",
      validateStatus: (status) => _.includes([200, 201, 204, 404], status),
    });
  }

  getCurrentUser() {
    return this.axios.get("session").then((res) => {
      if (res.status === 404) {
        return null;
      } else {
        return res.data.data;
      }
    });
  }

  login(email) {
    return this.axios.post("session", { email: email }).then((res) => {
      if (res.status === 200) {
        return res.data.data;
      } else {
        return null;
      }
    });
  }

  logout() {
    return this.axios.delete("session").then((res) => {
      if (res.status === 201) {
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

  setCurrentUser(user) {
    this.initialized = true;
    this.user = user;
  }

  initialize() {
    this.backend.getCurrentUser().then((user) => this.setCurrentUser(user));
  }

  login(email) {
    return this.backend.login(email).then((user) => this.setCurrentUser(user));
  }

  logout() {
    return this.backend.logout().then(() => this.setCurrentUser(null));
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
