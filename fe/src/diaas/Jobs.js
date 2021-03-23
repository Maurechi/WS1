import { Box } from "@material-ui/core";
import React from "react";
import { Route, Switch, useRouteMatch } from "react-router-dom";

import { DataGrid } from "diaas/DataGrid.js";

export const JobsTable = () => {
  const columns = [
    { defaultFlex: 2, name: "name", header: "Name" },
    { defaultFlex: 1, name: "status", header: "Status" },
    { defaultFlex: 2, name: "lastRun", header: "Last Run" },
    { defaultFlex: 2, name: "lastSuccess", header: "Last Success" },
  ];

  const rows = [
    { id: 1, name: "Load Source: static_kpis", status: "Failed", lastRun: "1 hour ago", lastSuccess: "6 hours ago" },
    {
      id: 2,
      name: "Transform: static_kpis_d",
      status: "Upstream Failed",
      lastRun: "1 hour ago",
      lastSuccess: "6 hours ago",
    },
    {
      id: 3,
      name: "Load Source: a_google_sheet",
      status: "Complete",
      lastRun: "3 hours ago",
      lastSuccess: "11 hours ago",
    },
    {
      id: 4,
      name: "Transform: enrich_data.py",
      status: "Complete",
      lastRun: "6 hours ago",
      lastSuccess: "6 hours ago",
    },
  ];

  return (
    <Box>
      <Box display="flex" mb={3}>
        <Box style={{ flexGrow: 1 }}>Jobs:</Box>
      </Box>
      <DataGrid isProperty="id" columns={columns} dataSource={rows} style={{ minHeight: 550 }} />
    </Box>
  );
};

export const JobsContent = () => {
  let { path } = useRouteMatch();
  return (
    <Switch>
      <Route path={path}>
        <JobsTable />
      </Route>
    </Switch>
  );
};
