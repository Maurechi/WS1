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
const SOURCE_EDITOR_REGISTRY = {
  "libds.source.google.GoogleSheet": GoogleSheet,
  "libds.source.static.StaticTable": StaticTable,
  __code__: Code,
};

export const SourcesTable = observer(() => {
  const columns = [
    { defaultFlex: 2, name: "name", header: "Name" },
    { defaultFlex: 1, name: "type", header: "Type" },
    { defaultFlex: 2, name: "details", header: "Details" },
  ];

  const history = useHistory();
  const { path } = useRouteMatch();
  const { user } = useAppState();
  const makeRow = (source) => ({ name: source.name, type: source.type, key: source.key });
  const rows = user.dataStacks[0].info.sources.map(makeRow);

  const onRenderRow = (rowProps) => {
    const { onClick } = rowProps;
    rowProps.onClick = (e) => {
      onClick(e);
      history.push(`${path}${rowProps.data.key}`);
    };
  };

  return (
    <Box>
      <Box display="flex" mb={3}>
        <Box style={{ flexGrow: 1 }}>Sources:</Box>
        <Box>
          <ButtonLink variant="contained" color="primary" target="/sources/new/">
            New Source
          </ButtonLink>
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
      <ButtonLink target={`${target}`} style={{ width: "100%" }}>
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

const SourceEditor = observer(() => {
  const { key } = useParams();
  const { user } = useAppState();
  const source = _.find(user.dataStacks[0].info.sources, (s) => s.key == key);

  const Component = SOURCE_EDITOR_REGISTRY[source.definition["in"] === "code" ? "__code__" : source.type];

  return <Component user={user} source={source} />;
});

export const SourcesContent = () => {
  let { path } = useRouteMatch();
  console.log("path is", path);
  return (
    <Switch>
      <Route path={`${path}new`}>
        <NewSourceChooser />
      </Route>
      <Route path={`${path}:key`}>
        <SourceEditor />
      </Route>
      <Route path={path}>
        <SourcesTable />
      </Route>
    </Switch>
  );
};
