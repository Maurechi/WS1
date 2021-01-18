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

const MOCK_USER = {
  data_stacks: [
    {
      config: { created_at: "2021-01-01T17:41:23+01:00" },
      repo: { branch: "prd" },
      sources: [
        {
          definition: {
            filename: "sources/adwords.yaml",
            in: "code",
          },
          id: "adwords-222-333-4444",
          name: "property.de (account 222-333-4444)",
          num_rows: 2,
          type: "libds.source.google.Adwords",
        },
        {
          definition: {
            config: { account: "1234567890" },
            in: "config",
          },
          id: "fbads",
          name: "Spend per Geo",
          num_rows: 2,
          type: "libds.source.facebook.Ads",
        },
        {
          definition: {
            config: {
              data:
                "date value\n2020-01-01 0\n2020-02-01 2\n2020-03-01 4\n2020-04-01 8\n2020-05-01 16\n2020-06-01 32\n2020-07-01 64\n2020-08-01 100\n2020-09-01 256\n2020-10-01 501\n2020-11-01 1024\n2020-12-01 2048\n2021-01-01 4096",
              target_table: "source.kpi_targets",
            },
            filename: "sources/kpi_targets.yaml",
            in: "config",
          },
          id: "static_kpis",
          name: "KPI Targets",
          num_rows: 13,
          type: "libds.source.static.StaticTable",
        },
        {
          definition: {
            config: {
              range: "A1:C99",
              service_account_file: "./extract/generic-diaas-extractor.json",
              spreadsheet_id: "1WDn4zjMVjaCZsAjzQRgYNx7J2uBxqKnI1LWLHuq3b-I",
            },
            filename: "sources/offline_spend.yaml",
            in: "config",
          },
          name: "Offline Spend Sheet",
          id: "offline_spend",
          range: "A1:C99",
          spreadsheet_id: "1WDn4zjMVjaCZsAjzQRgYNx7J2uBxqKnI1LWLHuq3b-I",
          type: "libds.source.google.GoogleSheet",
        },
      ],
      stores: [
        {
          id: "store",
          parameters: {
            host: "host.docker.internal",
            password: "scrypt$defa03d78fdb45fefded8d0005dc1e2d$768eaa26a5c2f7b2766a4a7c9a89dbf4b3c86dee",
            port: 6543,
            user: "postgres",
          },
          type: "libds.store.postgresql.PostgreSQL",
        },
      ],
      transformations: [
        {
          code:
            "with data as (\n  select\n    try_cast((data->>'date')::varchar, null::date) as date,\n    try_cast((data->>'value')::varchar, null::int) as value\n  from source.static_kpis\n)\nselect\n  date,\n  value,\n  case when value > 1 then log(2, value) else 0 end as integer_length\n  from data;",
          filename: "transformations/static_kpis_d.sql",
          id: "static_kpis_d",
          last_modified: "2021-01-11T22:48:28.249518",
          type: "sql",
        },
        {
          code:
            "-- https://dba.stackexchange.com/questions/203934/postgresql-alternative-to-sql-server-s-try-cast-function#203986\ncreate or replace function try_cast(_in text, inout _out anyelement) as\n$$\nbegin\n  execute format('select %L::%s', _in, pg_typeof(_out)) into _out;\nexception when others then\n  _out := null;\nend\n$$  LANGUAGE plpgsql;",
          filename: "transformations/common.sql",
          id: "common",
          last_modified: "2021-01-11T22:48:37.865690",
          type: "sql",
        },
        {
          code: "def transform():\n    return []\n",
          filename: "transformations/enrich_data.py",
          id: "enrich_data",
          last_modified: "2021-01-11T22:25:02.470636",
          type: "python",
        },
      ],
    },
  ],
  display_name: "mb",
  uid: "dx03",
};

const USE_MOCK_USER = false;

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
    return this.get("session").then(USE_MOCK_USER ? () => MOCK_USER : dataIfStatusEquals(200));
  }

  login(email) {
    return this.post("session", { email: email }).then(dataIfStatusEquals(200));
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

  postTransformation(transformation_id, source) {
    return this.post(`/transformation/${transformation_id}`, { source }).then(dataIfStatusEquals(200));
  }

  loadTransformation(transformation_id) {
    return this.post(`/transformation/${transformation_id}/load`).then(dataIfStatusEquals(200));
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
    this.user.data_stacks[0].sources = sources;
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
