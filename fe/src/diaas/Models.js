import "@inovua/reactdatagrid-community/index.css";
import ReactDataGrid from "@inovua/reactdatagrid-community";
import { Box, Divider } from "@material-ui/core";
import _ from "lodash";
import { observer } from "mobx-react-lite";
import React, { useState } from "react";
import { Route, Switch, useHistory, useParams, useRouteMatch } from "react-router-dom";

// NOTE this is a disaster. i know. eslint wants to reoder import
// alphabetically (which is somthing we generally want in this code
// base). however AceEditor needs to be loaded before its dependencies
// (and this is really AceEditor's fault). So we have to split the
// laods into 2 files, name them so that eslint wan't swap the load
// order, and then finally re import everything. would be great to
// have a way to tell eslint "don't reorder these 3 lines", but i
// wasn't able to find it.
// 20201215:mb
import "diaas/AceEditor_A_Editor";
import "diaas/AceEditor_B_Dependencies";
import AceEditor from "diaas/AceEditor";
import { TextField, useFormValue } from "diaas/form.js";
import { SampleDataTable } from "diaas/sources/SampleDataTable.js";
import { useAppState } from "diaas/state.js";
import { ButtonLink, NotFound } from "diaas/ui.js";

const CodeEditor = ({ code, mode, disabled = false }) => {
  return (
    <AceEditor
      width="100%"
      mode={mode}
      theme="solarized_light"
      name="UNIQUE_ID_OF_DIV"
      value={code.v}
      onChange={code.setter}
      fontSize={18}
      readOnly={disabled}
    />
  );
};

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

  return (
    <form onSubmit={saveAndRun}>
      <Box>
        <Box display="flex" mb={3}>
          <Box style={{ flexGrow: 1 }}>ID: {creating ? <TextField value={idValue} /> : <pre>{model.id}</pre>}</Box>
          <Box>
            <Box display="flex">
              <Box mx={1}>
                <ButtonLink onClick={saveAndRun} disabled={saveButtonDisabled}>
                  {saveButtonLabel}
                </ButtonLink>
              </Box>
              <Box mx={1}>
                <ButtonLink disabled={true}>Commit</ButtonLink>
              </Box>
            </Box>
          </Box>
        </Box>
        <CodeEditor mode={model.type} code={codeValue} />
        <Divider />
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
      <ReactDataGrid
        isProperty="id"
        columns={columns}
        dataSource={files}
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
