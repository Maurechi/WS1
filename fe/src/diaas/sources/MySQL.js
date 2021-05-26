import _ from "lodash";
import { observer } from "mobx-react-lite";
import React from "react";
import { useHistory } from "react-router-dom";

import { DataTable } from "diaas/DataTable.js";
import { Checkbox, makeValueObject, TextField, useFormValue } from "diaas/form.js";
import { IntervalSelector } from "diaas/sources/common.js";
import { useAppState } from "diaas/state.js";
import { ActionButton, ContentTitle } from "diaas/ui.js";

export const iconURL = "mysql.png";
export const label = "MySQL";

export const Editor = observer(({ source }) => {
  const { user, backend } = useAppState();
  const history = useHistory();

  if (!source) {
    source = {
      data: {
        connect_args: {},
      },
      filename: null,
      id: null,
    };
  }

  const id = useFormValue(source.id);
  const host = useFormValue(source.data.connect_args.host);
  const port = useFormValue(source.data.connect_args.port);
  const username = useFormValue(source.data.connect_args.username);
  const password_var = useFormValue(source.data.connect_args.password_var);
  const database = useFormValue(source.data.connect_args.database);
  const stale_after = useFormValue(source.data.stale_after);
  const target_table_name_prefix = useFormValue(source.data.target_table_name_prefix);
  const target_schema = useFormValue(source.data.target_schema);
  const rows = [
    ["Id", <TextField value={id} fullWidth={true} disabled={source.id !== null} />],
    ["Host", <TextField value={host} fullWidth={true} />],
    ["Port", <TextField value={port} fullWidth={true} />],
    ["Username", <TextField value={username} fullWidth={true} />],
    ["Password (var name)", <TextField value={password_var} fullWidth={true} />],
    ["Database", <TextField value={database} fullWidth={true} />],
    ["Refresh Interval", <IntervalSelector value={stale_after} />],
    ["Target Schema", <TextField value={target_schema} fullWidth={true} />],
    ["Target Table Name Prefix", <TextField value={target_table_name_prefix} fullWidth={true} />],
  ];
  const tables = useFormValue(source.data.tables || {});
  const save = () => {
    const data = _.cloneDeep(source.data);
    data.type = "libds.source.mysql.MySQL";
    data.connect_args["host"] = host.v;
    data.connect_args["port"] = port.v;
    data.connect_args["username"] = username.v;
    data.connect_args["password_var"] = password_var.v;
    data.connect_args["database"] = database.v;
    data.stale_after = stale_after.v;
    data.target_table_name_prefix = target_table_name_prefix.v;
    data.target_schema = target_schema.v;
    data.tables = {};
    for (const table_name in tables.v) {
      const { load, unpack } = tables.v[table_name];
      if (load || unpack) {
        data.tables[table_name] = { load, unpack };
      }
    }

    const post = backend.postFile(source.id === null ? `sources/${id.v}.yaml` : `sources/${source.filename}`, data);
    if (source.id === null) {
      return post
        .then(() => {
          return backend.sourceInfo(id.v);
        })
        .then((source) => {
          user.data_stacks[0].sources.push(source);
          return history.replace(`/sources/${id.v}`);
        });
    } else {
      return post;
    }
  };

  const inspectError = useFormValue(null);
  const inspect = () => {
    return save().then(() => {
      return backend.inspectSource(source.id).then((res) => {
        if (res.error) {
          inspectError.v = res.error;
        } else {
          const allTables = _.cloneDeep(tables.v);
          _.keys(res.data.tables).forEach((name) => {
            if (!(name in allTables)) {
              allTables[name] = { load: false, unpack: false };
            }
          });
          tables.v = allTables;
        }
      });
    });
  };

  const listingColumns = [
    { label: "Load", style: { width: 40 } },
    { label: "Unpack", style: { width: 40 } },
    { label: "Table Name" },
  ];
  const table_names = _.keys(tables.v).sort();

  const listingRows = table_names.map((name) => {
    let load, unpack;
    // return [name, name, name];
    load = makeValueObject(
      (v) => {
        tables.v[name]["load"] = v;
        if (!v) {
          unpack.v = false;
        }
        tables.v = _.cloneDeep(tables.v);
      },
      () => !!tables.v[name]["load"]
    );
    load.touch = () => null;
    unpack = makeValueObject(
      (v) => {
        tables.v[name]["unpack"] = v;
        if (v) {
          load.v = true;
        }
        tables.v = _.cloneDeep(tables.v);
      },
      () => !!tables.v[name]["unpack"]
    );
    unpack.touch = () => null;

    return [<Checkbox value={load} />, <Checkbox value={unpack} />, name];
  });

  return (
    <>
      <ContentTitle iconURL="mysql.png">MySQL</ContentTitle>
      <DataTable rows={rows} columns={[{ style: { width: "20%" } }, { style: {} }]} />
      <ActionButton onClick={save}>Save</ActionButton>
      <ActionButton onClick={inspect}>Load Tables</ActionButton>
      {inspectError.v && (
        <>
          <p>Error loading database details:</p> <pre>{JSON.stringify(inspectError.v, null, 4)}</pre>
        </>
      )}
      <DataTable rows={listingRows} columns={listingColumns} />
    </>
  );
});

export const Creator = () => <Editor source={null} />;
