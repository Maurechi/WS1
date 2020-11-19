import axios from "axios";
import _ from "lodash";
import { action, makeAutoObservable } from "mobx";
import { createContext, useContext } from "react";

import { ignore } from "diaas/utils.js";

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
    return this.axios.post("user", { email: email }).then((res) => {
      if (res.status === 200) {
        return res.data.data;
      } else {
        return null;
      }
    });
  }
}

const MOCK_USER = {
  uid: "q18y",
  workbenches: [
    {
      wbid: "kauw",
      name: "master",
      branch: "master",
      warehouse: {
        whid: "a7rt",
        name: "Astrospace GmbH",
      },
    },
  ],
};

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
        this.user = MOCK_USER;
      })
    );
  }

  login(email) {
    this.backend.login(email).then(
      action("login", (user) => {
        ignore(user);
        this.user = MOCK_USER;
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
