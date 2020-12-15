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
      branches: {
        master: {
          files: {
            pw3B: {
              id: "pw3B",
              name: "rockets_d.sql",
              details: "Locally Modified",
              lastModified: "Today",
              code:
                "select\n" +
                "  timestamp(json_extract(data, '$.launchDate')) as launch_date\n" +
                "  ,json_extract(data, '$.status')) as status\n" +
                "  ,upper(json_extract(data, '$.launchPad'))) as launch_pad\n" +
                "from rockets_r;",
            },
            orhj: {
              id: "orhj",
              name: "launches_d.sql",
              details: "Unmodified",
              lastModified: "1 Week Ago (Nov 3rd, 2020)",
            },
            mzsk: {
              id: "mzsk",
              name: "conversions_f.sql",
              details: "Unmodified",
              lastModified: "1 Week Ago (Nov 3rd, 2020)",
            },
            "9x27": {
              id: "9x27",
              name: "rockets_cleaned.py",
              details: "Unmodified",
              lastModified: "1 Week Ago (Nov 3rd, 2020)",
              code:
                "import pandas as pd\n" +
                "from diaas_modules.geo import Geo, AddressNotFound \n" +
                "\n" +
                "def transform_row(row):\n" +
                "    if row.lat is not None and row.lon is not None:\n" +
                "        row.geo = Geo.locate(row.lat, row.lon)\n" +
                "    elif row.address_text is not None:\n" +
                "        try:\n" +
                "            row.geo = Geo.geocode(row.address_text)\n" +
                "        except AddressNotFound:\n" +
                "            row.geo = None\n",
            },
          },
          tree: ["pw3B", "orhj", "mzsk", "9x27"],
        },
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
