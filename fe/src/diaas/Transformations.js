import "@inovua/reactdatagrid-community/index.css";
import ReactDataGrid from "@inovua/reactdatagrid-community";
import { Box } from "@material-ui/core";
import { observer } from "mobx-react-lite";
import React from "react";
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
import { useAppState } from "diaas/state.js";
import { ButtonLink } from "diaas/ui.js";

export const NewFile = () => <p>New</p>;

export const CodeEditor = ({ code, mode }) => {
  return (
    <AceEditor width="100%" mode={mode} theme="solarized_light" name="UNIQUE_ID_OF_DIV" value={code} fontSize={18} />
  );
};

export const Editor = observer(() => {
  const { user } = useAppState();
  const { fid } = useParams();
  const wb = user.workbenches[0];
  const file = wb.branches[wb.branch].files[fid];

  return (
    <Box>
      <Box display="flex" mb={3}>
        <Box style={{ flexGrow: 1 }}>Editing {file.name}:</Box>
        <Box>
          <Box display="flex">
            <Box mx={1}>
              <ButtonLink variant="contained" color="primary" target="/workbench/new/">
                Save & Test
              </ButtonLink>
            </Box>
            <Box mx={1}>
              <ButtonLink variant="contained" color="primary" target="/workbench/new/">
                Save
              </ButtonLink>
            </Box>
            <Box mx={1}>
              <ButtonLink variant="contained" color="primary" target="/workbench/new/">
                Commit
              </ButtonLink>
            </Box>
          </Box>
        </Box>
      </Box>
      <CodeEditor mode={file.name.match(/[.]py$/) ? "python" : "sql"} code={file.code} />
    </Box>
  );
});

export const FileTable = observer(() => {
  const { user } = useAppState();
  //const wb = user.workbenches[0];
  //const branch = wb.branches[wb.branch];
  //const files = branch.tree.map((fid) => branch.files[fid]);
  const files = [];

  const columns = [
    { defaultFlex: 1, name: "name", header: "Name" },
    { defaultFlex: 2, name: "details", header: "Details" },
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
              <ButtonLink variant="contained" color="primary" target="/tranformations/new/">
                New Transformation
              </ButtonLink>
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
      <Route path={`${path}:fid`}>
        <Editor />
      </Route>
      <Route path={path}>
        <Browser />
      </Route>
    </Switch>
  );
};
