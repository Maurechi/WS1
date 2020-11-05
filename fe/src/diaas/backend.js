import v from "voca";

class Backend {
  constructor(args) {
    let { baseurl = null } = args || {};
    if (!baseurl) {
      baseurl = "//api/v1/";
    }
    this.baseurl = v(baseurl).trimRight("/") + "/";
  }

  getSession() {
    return new Promise((res) => {
      setTimeout(() => res({ user: { name: "Marco" } }), 3000);
    });
  }
}

export const BACKEND = new Backend();
