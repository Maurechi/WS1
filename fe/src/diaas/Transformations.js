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
import { useFormValue } from "diaas/form.js";
import { SampleDataTable } from "diaas/sources/SampleDataTable.js";
import { useAppState } from "diaas/state.js";
import { ButtonLink } from "diaas/ui.js";
import { NotFound } from "diaas/utils.js";
export const NewFile = () => <p>New</p>;

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
  const { trfid } = useParams();

  if (user.data_stacks.length === 0) {
    return <NotFound>Data stacks for user</NotFound>;
  }
  const trf = _.find(user.data_stacks[0].transformations, (t) => t.id === trfid);
  if (!trf) {
    return <NotFound>Transformation with id {trfid}</NotFound>;
  }

  const codeValue = useFormValue(trf.source);
  const [rows, setRows] = useState([]);
  const saveAndRun = () => {
    setSaveButtonLabel("Saving.");
    setSaveButtonDisabled(true);
    backend.postTransformation(trf.id, codeValue.v).then(() => {
      setSaveButtonLabel("Loading");
      backend.loadTransformation(trf.id).then((rows) => {
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
          <Box style={{ flexGrow: 1 }}>Editing {trf.id}:</Box>
          <Box>
            <Box display="flex">
              <Box mx={1}>
                <ButtonLink target="/workbench/new/" onClick={saveAndRun} disabled={saveButtonDisabled}>
                  {saveButtonLabel}
                </ButtonLink>
              </Box>
              <Box mx={1}>
                <ButtonLink target="/workbench/new/" disabled={true}>
                  Commit
                </ButtonLink>
              </Box>
            </Box>
          </Box>
        </Box>
        <CodeEditor mode={trf.type} code={codeValue} />
        <Divider />
        <SampleDataTable rows={rows} />
      </Box>
    </form>
  );
});

export const FileTable = observer(() => {
  const { user } = useAppState();
  let files;

  if (user.data_stacks.length > 0) {
    const dataStack = user.data_stacks[0];
    files = dataStack.transformations.map(({ id, type, last_modified }) => ({ id, type, lastModified: last_modified }));
  } else {
    files = [];
  }

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
        <Box style={{ flexGrow: 1 }}>Transformations:</Box>
        <Box>
          <Box display="flex">
            <Box mx={1}>
              <ButtonLink target="/tranformations/new/">New Transformation</ButtonLink>
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

export const Browser = () => {
  return <FileTable />;
};

export const TransformationsContent = () => {
  let { path } = useRouteMatch();
  return (
    <Switch>
      <Route path={`${path}new/`}>
        <NewFile />
      </Route>
      <Route path={`${path}:trfid`}>
        <Editor />
      </Route>
      <Route path={path}>
        <Browser />
      </Route>
    </Switch>
  );
};
