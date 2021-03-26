import { Box, Divider, Grid, Typography } from "@material-ui/core";
import _ from "lodash";
import { observer } from "mobx-react-lite";
import React, { useState } from "react";
import { Route, Switch, useHistory, useParams, useRouteMatch } from "react-router-dom";

import { DataGrid } from "diaas/DataGrid.js";
import { CodeEditor, TextField, useFormValue } from "diaas/form.js";
import { Notebook } from "diaas/Notebook.js";
import { SampleDataTable } from "diaas/SampleDataTable.js";
import { useAppState } from "diaas/state.js";
import { ButtonLink, NotFound, StandardButton, VCenter } from "diaas/ui.js";

export const Editor = observer(() => {
  const [saveButtonLabel, setSaveButtonLabel] = useState("Save & Run");
  const [saveButtonDisabled, setSaveButtonDisabled] = useState(false);
  const { user, backend } = useAppState();

  if (user.dataStack === null) {
    return <NotFound>No Data stacks for user</NotFound>;
  }

  const { modelId } = useParams();
  const creating = modelId === "new";

  let model;
  if (creating) {
    model = { id: "", type: "sql", source: "select * from" };
  } else {
    model = _.find(user.dataStack.models, (m) => m.id === modelId);
    if (!model) {
      return <NotFound>No Model with id {modelId}</NotFound>;
    }
  }

  const codeValue = useFormValue(model.source);
  const idValue = useFormValue(model.id);

  const [rows, setRows] = useState([]);
  const saveAndRun = () => {
    setSaveButtonLabel("Saving.");
    setSaveButtonDisabled(true);
    backend.postModel(creating ? "" : modelId, { type: "select", id: idValue.v, source: codeValue.v }).then((data) => {
      setSaveButtonLabel("Loading");
      backend.loadModel(data.id).then((rows) => {
        setSaveButtonDisabled(false);
        setSaveButtonLabel("Save & Run");
        setRows(rows);
      });
    });
  };

  const SaveAndRunButton = () => (
    <StandardButton onClick={saveAndRun} disabled={saveButtonDisabled}>
      {" "}
      {saveButtonLabel}{" "}
    </StandardButton>
  );

  return (
    <form onSubmit={saveAndRun}>
      <Box>
        <Box display="flex" mb={3}>
          <Box style={{ flexGrow: 1 }}>
            <Typography variant="h4">Settings</Typography>
            <VCenter>
              <Box pr={2}>ID2:</Box>
              <Box>
                {" "}
                <TextField value={idValue} />{" "}
              </Box>
            </VCenter>
          </Box>
          <Box>
            <Box display="flex">
              <Box mx={1}>
                <SaveAndRunButton />
              </Box>
              <Box mx={1}>
                <StandardButton disabled={true}>Commit</StandardButton>
              </Box>
            </Box>
          </Box>
        </Box>
        <Divider />
        <Grid container>
          <Grid item xs={6}>
            <Typography variant="h4">Model</Typography>
            <CodeEditor mode={model.type} value={codeValue} />
          </Grid>
          <Grid item xs={6}>
            <Typography variant="h4">Notebook</Typography>
            <Notebook />
          </Grid>
        </Grid>
        <Divider />
        <Typography variant="h4">Data Sample</Typography>
        <SaveAndRunButton />
        <SampleDataTable rows={rows} />
      </Box>
    </form>
  );
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
        <Box style={{ flexGrow: 1 }}>Models:</Box>
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
        style={{ minHeight: 550 }}
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
