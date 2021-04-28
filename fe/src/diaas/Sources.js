import { Box, Grid, Paper, Typography } from "@material-ui/core";
import _ from "lodash";
import { observer } from "mobx-react-lite";
import React from "react";
import { Route, Switch, useHistory, useParams, useRouteMatch } from "react-router-dom";

import { DataGrid } from "diaas/DataGrid.js";
import { ErrorDialog } from "diaas/ErrorDialog.js";
import { TextField, useFormValue } from "diaas/form.js";
import { Code } from "diaas/sources/Code.js";
import { GoogleSheet } from "diaas/sources/GoogleSheet.js";
import { MySQL } from "diaas/sources/MySQL.js";
import { StaticTable } from "diaas/sources/StaticTable.js";
import { useAppState } from "diaas/state.js";
import { ActionButton, ButtonLink, DefinitionTable as DTable, VCenter } from "diaas/ui.js";

const UnknownSourceType = ({ source }) => {
  return <pre style={{ whiteSpace: "pre-wrap" }}>{JSON.stringify({ source }, null, 4)}</pre>;
};

const BrokenSource = observer(({ source }) => {
  const { backend } = useAppState();
  const text = useFormValue(source.text);
  const updateSource = () => {
    return backend.postFile("sources/" + source.filename, text.v);
  };
  const deleteSource = () => {
    return backend.deleteFile("sources/" + source.filename);
  };
  return (
    <DTable>
      <DTable.Term label="Error">
        <pre style={{ whiteSpace: "pre-nowrap" }}>{source.error}</pre>
      </DTable.Term>
      <DTable.Term label="Source Code">
        <TextField value={text} fullWidth={true} multiline={true} />
        <ActionButton onClick={updateSource}>Update Source</ActionButton>
        <ActionButton onClick={deleteSource}>Delete Source</ActionButton>
      </DTable.Term>
      <DTable.Term label="Full Dump">
        <pre style={{ whiteSpace: "pre-wrap" }}>{JSON.stringify(source, null, 4)}</pre>
      </DTable.Term>
    </DTable>
  );
});

// NOTE we could do something smarter here not have to edit this file
// every time we define a new componnet. however we'd still need to
// import the code and then we'd have unusedimports dangling around.
// this feels like a decent comporommise to me. 20210102:mb
const SOURCE_TYPE_REGISTRY = {
  "libds.source.google.GoogleSheet": { editor: GoogleSheet, iconURL: "google-sheets.svg", label: "Google Sheet" },
  "libds.source.static.StaticTable": { editor: StaticTable, iconURL: "csv.png", label: "Manual Data Entry" },
  "libds.source.mysql.MySQL": { editor: MySQL, iconURL: "mysql.png", label: "MySQL" },
};

const lookupSourceSpec = (source) => {
  if (source.type === ":broken") {
    return { editor: BrokenSource, iconURL: "broken.svg", label: "Broken" };
  } else if (source.code) {
    return { editor: Code, iconURL: "python.png", label: "Code" };
  } else {
    const mapped = SOURCE_TYPE_REGISTRY[source.type];
    if (mapped) {
      return mapped;
    } else {
      return { editor: UnknownSourceType, iconURL: "unknown.png", label: "Unknown" };
    }
  }
};

const SourceType = ({ source }) => {
  const { iconURL, label } = lookupSourceSpec(source);
  return (
    <>
      <img width="20px" src={`/i/logos/${iconURL}`} alt={label} /> {label}
    </>
  );
};

export const SourcesTable = observer(() => {
  const history = useHistory();
  const { path } = useRouteMatch();
  const { user } = useAppState();
  const sources = user.data_stacks[0].sources;

  const columns = [
    {
      defaultFlex: 1,
      name: "type",
      header: "Type",
      render: (column) => <SourceType source={column.data.source} />,
    },
    { defaultFlex: 6, name: "name", header: "Name" },
    { defaultFlex: 6, name: "filename", header: "File" },
  ];

  const makeRow = (source) => ({
    id: source.id,
    type: source.type,
    name: "name" in source ? source.name : source.id,
    source: source,
    filename: source.filename,
  });
  const rows = sources.map(makeRow);

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
        <Box style={{ flexGrow: 1 }}>Sources:</Box>
        <Box>
          <ButtonLink target={`${path}/:new`}>New Source</ButtonLink>
        </Box>
      </Box>
      <DataGrid
        isProperty="id"
        columns={columns}
        dataSource={rows}
        style={{ minHeight: 550 }}
        onRenderRow={onRenderRow}
      />
    </Box>
  );
});

export const NewConnectorCard = ({ logo, name, type, disabled }) => {
  return (
    <Paper>
      <ButtonLink
        target={`/sources/${type}/:new`}
        style={{ width: "100%" }}
        variant="outlined"
        color="#000000"
        disabled={disabled}
      >
        <Box display="flex" alignItems="center" justifyContent="flex-start" style={{ width: "100%" }}>
          <Box p={2}>
            {logo && (
              <VCenter style={{ minHeight: "50px" }}>
                <img
                  alt={`logo for ${name}`}
                  src={`/i/logos/${logo}`}
                  width="30px"
                  style={{ filter: disabled ? "grayscale(1)" : "none" }}
                />
              </VCenter>
            )}
            {!logo && <img alt="filler logo for layout purposes" src="/i/logos/postgresql.svg" width="30px" />}
          </Box>
          <Box flexGrow={2}>
            <Box
              mx={1}
              style={{
                textAlign: "left",
                textDecoration: disabled ? "line-through" : "none",
                color: disabled ? "#999999" : "inherit",
              }}
            >
              {name}
            </Box>
          </Box>
        </Box>
      </ButtonLink>
    </Paper>
  );
};

export const NewSourceChooser = () => {
  return (
    <Box>
      <Box mb={2}>
        <Box mb={2}>
          <Typography variant="h6">Marketing Sources</Typography>
        </Box>
        <Grid container spacing={4}>
          <Grid item xs={4}>
            <NewConnectorCard logo="google-adwords.png" name="Google Adwords" target="google-adwords" disabled />
          </Grid>
          <Grid item xs={4}>
            <NewConnectorCard logo="google-analytics.svg" name="Google Analytics" disabled />
          </Grid>
          <Grid item xs={4}>
            <NewConnectorCard logo="facebook.svg" name="Facebook ADs" target="facebook-ads" disabled />
          </Grid>
          <Grid item xs={4}>
            <NewConnectorCard logo="microsoft-bing.svg" name="Bing" disabled />
          </Grid>
        </Grid>
      </Box>

      <Box mb={2}>
        <Box mb={2}>
          <Typography variant="h6">SaaS Platforms</Typography>
        </Box>
        <Grid container spacing={4}>
          <Grid item xs={4}>
            <NewConnectorCard name="Salesforce" logo="salesforce.webp" disabled />
          </Grid>
          <Grid item xs={4}>
            <NewConnectorCard name="Pipedrive" logo="pipedrive.svg" disabled />
          </Grid>
        </Grid>
      </Box>

      <Box mb={2}>
        <Box mb={2}>
          <Typography variant="h6">Data Sources</Typography>
        </Box>
        <Grid container spacing={4}>
          <Grid item xs={4}>
            <NewConnectorCard logo="csv.png" name="Static Table" type="libds.source.static.StaticTable" />
          </Grid>
          <Grid item xs={4}>
            <NewConnectorCard logo="mysql.png" name="MySQL" type="libds.source.mysql.MySQL" />
          </Grid>
          <Grid item xs={4}>
            <NewConnectorCard logo="postgresql.svg" name="PostgreSQL" disabled />
          </Grid>
          <Grid item xs={4}>
            <NewConnectorCard logo="google-sheets.svg" name="Google Sheets" target="google-sheets" disabled />
          </Grid>
          <Grid item xs={4}>
            <NewConnectorCard name="BigQuery" logo="bigquery.png" disabled />
          </Grid>
          <Grid item xs={4}>
            <NewConnectorCard name="Redshift" logo="redshift.png" disabled />
          </Grid>
        </Grid>
      </Box>
    </Box>
  );
};

const SourceEditorContent = observer(() => {
  const { id } = useParams();
  const { user } = useAppState();
  let source = _.find(user.data_stacks[0].sources, (s) => s.id === id); //
  let spec;
  if (source) {
    spec = lookupSourceSpec(source);
  } else {
    return <ErrorDialog title="This was not supposed to happen." message={`No source found with id '${id}'`} />;
  }

  const Editor = spec.editor;
  return <Editor user={user} source={source} id={id} />;
});

export const SourcesContent = () => {
  let { path } = useRouteMatch();
  return (
    <Switch>
      <Route path={`${path}/\\:new`}>
        <NewSourceChooser />
      </Route>
      <Route path={`${path}:id`}>
        <SourceEditorContent />
      </Route>
      <Route path={path}>
        <SourcesTable />
      </Route>
    </Switch>
  );
};
