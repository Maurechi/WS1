import { Box, Divider, Grid, Typography } from "@material-ui/core";
import _ from "lodash";
import { observer } from "mobx-react-lite";
import React from "react";
import { generatePath, Route, Switch, useHistory, useParams, useRouteMatch } from "react-router-dom";

import { DataGrid } from "diaas/DataGrid.js";
import { CodeEditor, TextField, useFormValue } from "diaas/form.js";
import { Notebook } from "diaas/Notebook.js";
import { useAppState } from "diaas/state.js";
import { ActionButton, ButtonLink, NotFound, VCenter } from "diaas/ui.js";

export const Editor = observer(() => {
  const { user, backend } = useAppState();
  const history = useHistory();
  const routeMatch = useRouteMatch();

  if (user.dataStack === null) {
    return <NotFound>No Data stacks for user</NotFound>;
  }

  const { modelId } = useParams();
  const creating = modelId === "new";

  let model;
  let found;
  if (creating) {
    model = { id: "", type: "sql", source: "select * from" };
    found = true;
  } else {
    model = _.find(user.dataStack.models, (m) => m.id === modelId);
    if (!model) {
      found = false;
      model = {};
    } else {
      found = true;
    }
  }

  const textValue = useFormValue(model.source, { trim: false });
  const idValue = useFormValue(model.id);

  const redirectToModel = (mid) => {
    return backend.modelInfo(mid).then((m) => {
      user.dataStack.models = _.concat(user.dataStack.models, [m]);
      if (history.location.pathname === routeMatch.url) {
        history.replace(generatePath(routeMatch.path, { modelId: mid }));
      }
    });
  };

  const save = () => {
    let updateFile;
    if (creating) {
      updateFile = backend.postFile(`models/${idValue.v}.sql`, textValue.v).then(() => {
        return redirectToModel(idValue.v);
      });
    } else {
      updateFile = backend.postFile(model.filename, textValue.v);
      if (model.id !== idValue.v) {
        updateFile = updateFile.then(() => {
          const m = model.filename.match(/^models(.*)\/.*(\.[^.]+)$/);
          if (m === null) {
            throw new Error(`filename does not match regexp: ${model.filename}`);
          }
          const dirs = m[1];
          const ext = m[2];
          return backend.moveFile(model.filename, "models" + dirs + "/" + idValue.v + ext).then(() => {
            user.dataStack.models = _.filter(user.dataStack.models, (m) => m.id !== model.id);
            return redirectToModel(idValue.v);
          });
        });
      }
    }
    return updateFile.then(() => {
      return backend.updateDataNodeState("public." + idValue.v, "STALE");
    });
  };

  if (!found) {
    return <NotFound>No Model with id {modelId}</NotFound>;
  } else {
    return (
      <form onSubmit={save}>
        <Box>
          <Box display="flex" mb={3}>
            <Box style={{ flexGrow: 1 }}>
              <Typography variant="h4">Settings</Typography>
              <VCenter>
                <Box pr={2}>ID:</Box>
                <Box>
                  <TextField value={idValue} />
                </Box>
              </VCenter>
            </Box>
            <Box>
              <Box display="flex">
                <Box mx={1}>
                  <ActionButton onClick={save}>Save</ActionButton>
                </Box>
              </Box>
            </Box>
          </Box>
          <Divider />
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Typography variant="h4">Model</Typography>
              <CodeEditor mode={model.type} value={textValue} />
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="h4">Notebook</Typography>
              <Notebook id={modelId} baseTable={modelId} />
            </Grid>
          </Grid>
        </Box>
      </form>
    );
  }
});

export const FileTable = observer(() => {
  const { user } = useAppState();
  const models = user.dataStack ? user.dataStack.models : [];
  const files = models.map(({ id, type, last_modified }) => ({
    id,
    type,
    lastModified: last_modified,
  }));

  const columns = [
    { defaultFlex: 1, name: "id", header: "id" },
    { defaultFlex: 2, name: "type", header: "type" },
    { defaultFlex: 1, name: "lastModified", header: "Last Modified" },
  ];

  const history = useHistory();
  const { path } = useRouteMatch();

  const onRenderRow = (rowProps) => {
    const { onClick } = rowProps;
    rowProps.onClick = (e) => {
      onClick(e);
      history.push(`${path}${rowProps.data.id}`);
    };
  };

  return (
    <Box>
      <Box display="flex" mb={3}>
        <Box style={{ flexGrow: 1 }}>
          <Typography variant="h4">Models</Typography>
        </Box>
        <Box>
          <Box display="flex">
            <Box mx={1}>
              <ButtonLink target="/models/new">New Model</ButtonLink>
            </Box>
          </Box>
        </Box>
      </Box>
      <DataGrid
        isProperty="id"
        columns={columns}
        dataSource={files}
        defaultSortInfo={{ name: "id", dir: 1 }}
        style={{ minHeight: 1000 }}
        onRenderRow={onRenderRow}
      />
    </Box>
  );
});

export const ModelsContent = () => {
  let { path } = useRouteMatch();
  return (
    <Switch>
      <Route path={`${path}:modelId`}>
        <Editor />
      </Route>
      <Route path={path}>
        <FileTable />
      </Route>
    </Switch>
  );
};
