import "@inovua/reactdatagrid-community/index.css";
import ReactDataGrid from "@inovua/reactdatagrid-community";
import { Box } from "@material-ui/core";
import React from "react";
import { Route, Switch, useRouteMatch } from "react-router-dom";

export const JobsTable = () => {
  const columns = [
    { defaultFlex: 2, name: "name", header: "Name" },
    { defaultFlex: 1, name: "status", header: "Status" },
    { defaultFlex: 2, name: "lastRun", header: "Last Run" },
    { defaultFlex: 2, name: "lastSuccess", header: "Last Success" },
  ];

  const rows = [
    { id: 1, name: "rocket_clean.py", status: "Failed", lastRun: "1 hour ago", lastSuccess: "11 hours ago" },
    { id: 1, name: "rockets_d.sql", status: "Upstream Failed", lastRun: "1 hour ago", lastSuccess: "11 hours ago" },
    { id: 1, name: "launches_d.sql", status: "Complete", lastRun: "6 hours ago", lastSuccess: "6 hours ago" },
    {
      id: 1,
      name: "conversion_f.sql",
      status: "In Progress",
      lastRun: "Running for 17 minutes.",
      lastSuccess: "6 hours ago",
    },
  ];

  return (
    <Box>
      <Box display="flex" mb={3}>
        <Box style={{ flexGrow: 1 }}>Jobs:</Box>
      </Box>
      <ReactDataGrid isProperty="id" columns={columns} dataSource={rows} style={{ minHeight: 550 }} />
    </Box>
  );
};

export const JobsContent = () => {
  let { path } = useRouteMatch();
  console.log("path is", path);
  return (
    <Switch>
      <Route path={path}>
        <JobsTable />
      </Route>
    </Switch>
  );
};
