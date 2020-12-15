import "@inovua/reactdatagrid-community/index.css";
import ReactDataGrid from "@inovua/reactdatagrid-community";
import { Box } from "@material-ui/core";
import { observer } from "mobx-react-lite";
import React from "react";
import { Route, Switch, useHistory, useParams, useRouteMatch } from "react-router-dom";

import "diaas/AceEditor_A_Editor";
import "diaas/AceEditor_B_Dependencies";
import AceEditor from "diaas/AceEditor";
import { useAppState } from "diaas/state.js";
import { ButtonLink } from "diaas/ui.js";

export const NewFile = () => <p>New</p>;

export const CodeEditor = ({ code, mode }) => {
  const options = {
    selectOnLineNumbers: true,
  };

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
  const wb = user.workbenches[0];
  const branch = wb.branches[wb.branch];
  const files = branch.tree.map((fid) => branch.files[fid]);

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
        <Box style={{ flexGrow: 1 }}>Workbench:</Box>
        <Box>
          <Box display="flex">
            <Box mx={1}>
              <ButtonLink variant="contained" color="primary" target="/tranformations/new/">
                New
              </ButtonLink>
            </Box>
            <Box mx={1}>
              <ButtonLink variant="contained" color="primary" target="/tranformations/new/">
                Commit
              </ButtonLink>
            </Box>
            <Box mx={1}>
              <ButtonLink variant="contained" color="primary" target="/tranformations/new/">
                Test
              </ButtonLink>
            </Box>
            <Box mx={1}>
              <ButtonLink variant="contained" color="primary" target="/tranformations/new/">
                Deploy
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

export const WorkbenchContent = () => {
  let { path } = useRouteMatch();
  console.log("path is", path);
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
