import "@inovua/reactdatagrid-community/index.css";
import ReactDataGrid from "@inovua/reactdatagrid-community";
import {
  Box,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Paper,
  TextField as MUITextField,
  Typography,
} from "@material-ui/core";
import Autocomplete from "@material-ui/lab/Autocomplete";
import _ from "lodash";
import { observer } from "mobx-react-lite";
import React, { useState } from "react";
import { Route, Switch, useHistory, useParams, useRouteMatch } from "react-router-dom";

import { ErrorDialog } from "diaas/ErrorDialog.js";
import { Checkbox, Select, TextField, useFormValue } from "diaas/form.js";
import { Code } from "diaas/sources/Code.js";
import { GoogleSheet } from "diaas/sources/GoogleSheet.js";
import { StaticTable } from "diaas/sources/StaticTable.js";
import { useAppState } from "diaas/state.js";
import { ButtonLink } from "diaas/ui.js";

// NOTE we could do something smarter here not have to edit this file
// every time we define a new componnet. however we'd still need to
// import the code and then we'd have unusedimports dangling around.
// this feels like a decent comporommise to me. 20210102:mb
const SOURCE_TYPE_REGISTRY = {
  "libds.source.google.GoogleSheet": { editor: GoogleSheet, iconURL: "google-sheets.svg", label: "Google Sheet" },
  "libds.source.facebook.Ads": { editor: GoogleSheet, iconURL: "facebook.svg", label: "Facebook Ads" },
  "libds.source.google.Adwords": { editor: Code, iconURL: "google-adwords.png", label: "Google Ads" },
  "libds.source.static.StaticTable": { editor: StaticTable, iconURL: "csv.png", label: "Manual Data Entry" },
};

const lookupSourceType = (source) => SOURCE_TYPE_REGISTRY[source.type];

const SourceEditor = ({ user, source }) => {
  const Component = source.definition["in"] === "code" ? Code : lookupSourceType(source).editor;
  return <Component user={user} source={source} />;
};

const SourceType = ({ source }) => {
  const { iconURL, label } = lookupSourceType(source);
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
    { defaultFlex: 9, name: "name", header: "Name" },
  ];

  const makeRow = (source) => ({
    id: source.id,
    type: source.type,
    name: "name" in source ? source.name : source.id,
    source: source,
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
          <ButtonLink target="/sources/new/">New Source</ButtonLink>
        </Box>
      </Box>
      <ReactDataGrid
        isProperty="id"
        columns={columns}
        dataSource={rows}
        style={{ minHeight: 550 }}
        onRenderRow={onRenderRow}
      />
    </Box>
  );
});

export const ConnectorCard = ({ logo, name, target }) => {
  return (
    <Paper>
      <ButtonLink target={`${target}`} style={{ width: "100%" }} variant="outlined" color="#000000">
        <Box display="flex" alignItems="center" justifyContent="flex-start" style={{ width: "100%" }}>
          <Box p={2}>
            {logo && <img alt={`logo for ${name}`} src={`/i/logos/${logo}`} width="30px" />}
            {!logo && <img alt="filler logo for layout purposes" src="/i/logos/postgresql.svg" width="30px" />}
          </Box>
          <Box flexGrow={2}>
            <Box mx={1} style={{ textAlign: "left" }}>
              {name}
            </Box>
          </Box>
        </Box>
      </ButtonLink>
    </Paper>
  );
};

export const SourceNewGoogleAdwords = () => {
  const [value, setValue] = useState("");
  return (
    <>
      <Grid container spacing={1}>
        <Grid item xs={12}>
          <p>New Google Adwords Data Source</p>
        </Grid>
        <Grid item xs={12}>
          <TextField label="Customer Id" value={value} onChange={(e) => setValue(e.target.value)} type="string" />
        </Grid>
        <Grid item xs={12}>
          <TextField label="Service Account" value={value} onChange={(e) => setValue(e.target.value)} type="string" />
        </Grid>
      </Grid>
    </>
  );
};

export const SourceNewFacebookAds = () => {
  const accountId = useFormValue("000000000001 'DE - B2C'");
  const useAllAccounts = useFormValue(true);
  const breakdown = useFormValue("region");
  return (
    <>
      <Grid container spacing={1}>
        <Grid item xs={12}>
          <p>New Facebook Ads Data Source</p>
        </Grid>
        <Grid item xs={3}>
          <TextField disabled={useAllAccounts.v} label="Account ID" value={accountId} type="string" />
          <Box>- or -</Box>
          Sync All Accounts
          <Checkbox label="All Accounts" value={useAllAccounts} />
        </Grid>
        <Grid item xs={9}>
          <FormControl>
            <InputLabel id="fb-breakdown-select-label">Breakdown</InputLabel>
            <Select
              labelId="fb-breakdown-select-label"
              id="fb-breakdown-select-value"
              style={{ width: 120 }}
              value={breakdown}
            >
              <MenuItem value={""}>All</MenuItem>
              <MenuItem value={"country"}>Country</MenuItem>
              <MenuItem value={"region"}>Region</MenuItem>
            </Select>
          </FormControl>
          <Autocomplete
            id="fb-fields-select"
            options={["cpc", "ad_id", "ad_name", "campaign_id", "campaign_name"]}
            getOptionLabel={(option) => option}
            style={{ width: 300 }}
            multiple
            renderInput={(params) => <MUITextField {...params} label="Fields" variant="outlined" dense />}
          />
        </Grid>
      </Grid>
    </>
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
            <ConnectorCard logo="google-sheets.svg" name="Google Sheets" target="google-sheets" />
          </Grid>
          <Grid item xs={4}>
            <ConnectorCard logo="google-adwords.png" name="Google Adwords" target="google-adwords" />
          </Grid>
          <Grid item xs={4}>
            <ConnectorCard logo="google-analytics.svg" name="Google Analytics" />
          </Grid>
          <Grid item xs={4}>
            <ConnectorCard logo="facebook.svg" name="Facebook ADs" target="facebook-ads" />
          </Grid>
          <Grid item xs={4}>
            <ConnectorCard logo="microsoft-bing.svg" name="Bing" />
          </Grid>
        </Grid>
      </Box>

      <Box mb={2}>
        <Box mb={2}>
          <Typography variant="h6">SaaS Platforms</Typography>
        </Box>
        <Grid container spacing={4}>
          <Grid item xs={4}>
            <ConnectorCard name="Salesforce" logo="salesforce.webp" />
          </Grid>
          <Grid item xs={4}>
            <ConnectorCard name="Pipedrive" logo="pipedrive.svg" />
          </Grid>
        </Grid>
      </Box>

      <Box mb={2}>
        <Box mb={2}>
          <Typography variant="h6">Data Sources</Typography>
        </Box>
        <Grid container spacing={4}>
          <Grid item xs={4}>
            <ConnectorCard logo="postgresql.svg" name="PostgreSQL" />
          </Grid>
          <Grid item xs={4}>
            <ConnectorCard name="CSV" logo="csv.png" />
          </Grid>
          <Grid item xs={4}>
            <ConnectorCard name="BigQuery" logo="bigquery.png" />
          </Grid>
          <Grid item xs={4}>
            <ConnectorCard name="Redshift" logo="redshift.png" />
          </Grid>
        </Grid>
      </Box>
    </Box>
  );
};

const SourceEditorContent = observer(() => {
  const { id } = useParams();
  const { user } = useAppState();
  const source = _.find(user.data_stacks[0].sources, (s) => s.id === id); //
  if (!source) {
    console.log("error");
    return <ErrorDialog title="This was not supposed to happen." message={`No source found with id '${id}'`} />;
  } else {
    return <SourceEditor user={user} source={source} />;
  }
});

export const SourcesContent = () => {
  let { path } = useRouteMatch();
  return (
    <Switch>
      <Route path={`${path}new/google-adwords`}>
        <SourceNewGoogleAdwords />
      </Route>
      <Route path={`${path}new/facebook-ads`}>
        <SourceNewFacebookAds />
      </Route>
      <Route path={`${path}new/`}>
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
