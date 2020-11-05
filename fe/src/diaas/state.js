import { makeAutoObservable } from "mobx";

import { BACKEND } from "diaas/backend";

class State {
  session = null;
  user = null;

  constructor() {
    makeAutoObservable(this);
  }

  hasUser() {
    return this.user !== null;
  }

  isInitialized() {
    return this.session !== null;
  }

  initialize() {
    return BACKEND.getSession().then((session) => {
      this.session = session;
      this.user = session.user;
      return this;
    });
  }
}

export const STATE = new State();
