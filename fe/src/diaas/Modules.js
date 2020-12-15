import "@inovua/reactdatagrid-community/index.css";
import ReactDataGrid from "@inovua/reactdatagrid-community";
import { Box } from "@material-ui/core";
import MoreHoriz from "@material-ui/icons/MoreHoriz";
import React from "react";
import { Route, Switch, useRouteMatch } from "react-router-dom";

export const ModulesTable = () => {
  const renderName = ({ data }) => (
    <Box display="flex" alignItems="center">
      <Box flexGrow={1}>{data.name}</Box>
      <Box px={2}>
        <MoreHoriz />
      </Box>
    </Box>
  );
  const renderEnabled = ({ data }) => <Box>{data.enabled ? "yes" : "no"}</Box>;
  const columns = [
    { defaultFlex: 6, name: "name", header: "Name", render: renderName },
    { defaultFlex: 1, name: "enabled", header: "Enabled", render: renderEnabled },
  ];

  const rows = [
    { id: 1, enabled: false, name: "Logistics - Orders per Geo Clusters" },
    { id: 1, enabled: true, name: "Marketing - Churn" },
    { id: 1, enabled: false, name: "Marketing - Multitouch Attribution" },
    { id: 1, enabled: true, name: "Operations - Tickets and Agents" },
    { id: 1, enabled: true, name: "Operations - Employee Churn" },
  ];

  return (
    <Box>
      <Box display="flex" mb={3}>
        <Box style={{ flexGrow: 1 }}>Modules:</Box>
      </Box>
      <ReactDataGrid isProperty="id" columns={columns} dataSource={rows} style={{ minHeight: 550 }} />
    </Box>
  );
};

export const ModulesContent = () => {
  let { path } = useRouteMatch();
  console.log("path is", path);
  return (
    <Switch>
      <Route path={path}>
        <ModulesTable />
      </Route>
    </Switch>
  );
};
