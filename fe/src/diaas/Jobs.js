import { Box } from "@material-ui/core";
import React, { useEffect, useState } from "react";
import { Route, Switch, useRouteMatch } from "react-router-dom";

import { DataGrid } from "diaas/DataGrid.js";
import { useAppState } from "diaas/state.js";

export const JobsTable = () => {
  const state = useAppState();
  const [jobs, setJobs] = useState([]);
  useEffect(() => {
    state.backend.jobsList().then(setJobs);
  }, [state]);
  const columns = [
    { defaultFlex: 2, name: "id", header: "ID" },
    { defaultFlex: 1, name: "state", header: "State" },
  ];

  return (
    <Box>
      <Box display="flex" mb={3}>
        <Box style={{ flexGrow: 1 }}>Jobs:</Box>
      </Box>
      <DataGrid
        isProperty="id"
        columns={columns}
        dataSource={jobs}
        style={{ minHeight: 550 }}
        defaultSortInfo={{ name: "id", dir: -1 }}
      />
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
