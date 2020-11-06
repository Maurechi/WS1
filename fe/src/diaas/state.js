import { makeAutoObservable } from "mobx";

import { BACKEND } from "diaas/backend";

class State {
  session = null;
  user = null;
  initialized = false;

  constructor() {
    makeAutoObservable(this);
  }

  isAuthenticated() {
    return this.user !== null;
  }

  isInitialized() {
    return this.initialized;
  }

  initialize() {
    return BACKEND.getSession().then((session) => {
      if (session) {
        this.session = session;
        this.user = session.user;
      } else {
        this.session = null;
        this.user = null;
      }
      this.initialized = true;
      return this;
    });
  }
}

export const STATE = new State();
