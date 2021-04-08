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
  constructor(state) {
    const self = this;
    self.axios = axios.create({
      baseURL: "/api/1/",
      validateStatus: (status) => _.includes([200, 201, 204, 404], status),
    });
    self.state = state;
    self.axios.interceptors.response.use(
      function (response) {
        // Do something with response data
        return response;
      },
      function (error) {
        if (error.response) {
          self.state.setFatalError({ title: "Backend api error", data: error.response.data });
        } else {
          self.state.setFatalError({ title: "Network error", message: JSON.stringify(error, null, 4) });
        }

        // setFatalError will pop up an unclosable error dialog,
        // there's no point in progressing, so just let our caller
        // hang forever.
        return new Promise(() => null);
      }
    );
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

  login(data) {
    return this.post("session", data).then(dataIfStatusEquals(200));
  }

  logout() {
    return this.delete("session").then(dataIfStatusEquals([200, 201]));
  }

  postSource(source_id, config) {
    return this.post(`/sources/${source_id}`, config).then(dataIfStatusEquals(200));
  }

  loadSource(source_id) {
    return this.post(`/sources/${source_id}/load`).then(dataIfStatusEquals(200));
  }

  postModel(model_id, payload) {
    return this.post(`/model/${model_id}`, payload).then(dataIfStatusEquals(200));
  }

  loadModel(model_id) {
    return this.post(`/model/${model_id}/load`).then(dataIfStatusEquals(200));
  }

  execute(payload) {
    return this.post(`/store/execute`, payload).then(dataIfStatusEquals(200));
  }
}

class User {
  constructor(data) {
    Object.assign(this, data);
  }

  get dataStack() {
    if (this.data_stacks && "0" in this.data_stacks) {
      return this.data_stacks["0"];
    } else {
      return null;
    }
  }

  set dataStack(ds) {
    if (this.data_stacks.length > 0) {
      this.data_stacks[0] = ds;
    } else {
      this.data_stacks = [ds];
    }
  }
}

class AppStateObject {
  user = null;
  initialized = false;
  fatalError = null;
  jobs = {
    list: [],
    byId: {},
    numActive: 0,
  };

  constructor() {
    makeAutoObservable(this);
    this.backend = new Backend(this);
  }

  setCurrentUser(user) {
    this.initialized = true;
    this.user = user ? new User(user) : null;
  }

  setSource(source) {
    const sources = [];
    let found = false;
    for (const s of this.user.data_stacks[0].sources) {
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
    this.user.data_stack.sources = sources;
  }

  setFatalError(err) {
    this.fatalError = err;
  }

  setJobs(jobs) {
    this.jobs = jobs;
  }

  initialize() {
    this.backend.getCurrentUser().then((user) => this.setCurrentUser(user));
  }

  login(data) {
    return this.backend.login(data).then((user) => this.setCurrentUser(user));
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

export const AppState = ({ children }) => {
  return <AppStateContext.Provider value={APP_STATE}>{children}</AppStateContext.Provider>;
};
