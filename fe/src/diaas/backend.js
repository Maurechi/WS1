import axios from "axios";
import _ from "lodash";

class Backend {
  constructor(args) {
    this.axios = axios.create({
      baseURL: "//" + window.location.host + "/api/1/",
      validateStatus: (status) => _.includes([200, 201, 204, 404], status),
    });
  }

  getSession() {
    return this.axios.get("session").then((res) => {
      if (res.status === 404) {
        return null;
      } else {
        return res.data;
      }
    });
  }
}

export const BACKEND = new Backend();
