import axios from "axios";
import _ from "lodash";
import { makeAutoObservable } from "mobx";
import { createContext, useContext } from "react";

const dataIf = (condition) => {
  return (response) => {
    if (condition(response)) {
      return response.data.data;
    } else {
      return null;
    }
  };
};

const dataIfStatusEquals = (status) => {
  let condition;
  if (_.isArray(status)) {
    condition = (res) => _.includes(status, res.status);
  } else {
    condition = (res) => status === res.status;
  }
  return dataIf(condition);
};

class Backend {
  constructor() {
    this.axios = axios.create({
      baseURL: "//" + window.location.host + "/api/1/",
      validateStatus: (status) => _.includes([200, 201, 204, 404], status),
    });
  }

  get(url, config) {
    return this.axios.get(url, config);
  }

  post(url, data, config) {
    return this.axios.post(url, data, config);
  }

  delete(url, config) {
    return this.axios.delete(url, config);
  }

  getCurrentUser() {
    return this.get("session").then(dataIfStatusEquals(200));
  }

  login(email) {
    return this.post("session", { email: email }).then(dataIfStatusEquals(200));
  }

  logout() {
    return this.delete("session").then(dataIfStatusEquals([200, 201]));
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

  setSource(source) {
    const sources = [];
    let found = false;
    for (const s of this.user.data_stacks[0].info.sources) {
      if (s.id === source.id) {
        sources.push(source);
        found = true;
      } else {
        sources.push(s);
      }
    }
    if (!found) {
      sources.push(source);
    }
    this.user.data_stacks[0].info.sources = sources;
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
