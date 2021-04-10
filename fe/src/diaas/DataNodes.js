import { Box } from "@material-ui/core";
import Tab from "@material-ui/core/Tab";
import TabContext from "@material-ui/lab/TabContext";
import TabList from "@material-ui/lab/TabList";
import TabPanel from "@material-ui/lab/TabPanel";
import DagreGraph from "dagre-d3-react";
import _ from "lodash";
import { observer } from "mobx-react-lite";
import React, { useRef, useState } from "react";
import { Route, Switch, useParams, useRouteMatch } from "react-router-dom";

import { DataGrid } from "diaas/DataGrid.js";
import { useAppState } from "diaas/state.js";
import { ActionButton, useResize } from "diaas/ui.js";

const useDataNodes = () => {
  const { user } = useAppState();

  return user.dataStack.data_nodes.slice().map((n) => Object.assign({}, n, { upstream: (n.upstream || []).sort() }));
};

const Graph = observer(() => {
  const dataNodes = useDataNodes();

  const nodes = {};
  const linksList = [];

  const state_colors = {
    FRESH: "green",
    STALE: "#666666",
    REFRESHING: "orange",
    REFRESHING_STALE: "orange",
    ORPHAN: "red",
  };

  dataNodes.forEach((n, i) => {
    nodes[n.id] = {
      id: i,
      label: n.id,
      config: { style: "fill: " + state_colors[n.state] || "blue" },
    };
  });

  const nodeList = Object.values(nodes).map((n) => n);

  dataNodes.forEach((n) => {
    if (n.upstream) {
      n.upstream.forEach((i) => {
        linksList.push({ source: nodes[i].id, target: nodes[n.id].id });
      });
    }
  });

  const wrapper = useRef(null);
  const { width } = useResize(wrapper);

  return (
    <Box>
      <Box display="flex" mb={3} ref={wrapper}>
        <Box style={{ flexGrow: 1 }}>Data Dependencies:</Box>
      </Box>
      <Box className="dataNodeGraph" style={{ border: "1px black solid" }}>
        <DagreGraph
          nodes={nodeList}
          links={linksList}
          config={{
            rankdir: "LR",
            // align: 'UL',
            ranker: "tight-tree",
          }}
          width={width || 500}
          height={800}
          zoomable
          fitBoundaries
        />
      </Box>
    </Box>
  );
});

const Tasks = () => {
  return <p>Tasks</p>;
};

const Nodes = () => {
  const columns = [
    {
      name: "Action",
      header: "",
      render: ({ data }) => {
        if (data.state === "FRESH") {
          return <ActionButton>Refresh</ActionButton>;
        } else {
          return <pre>{data.state}</pre>;
        }
      },
    },
    { name: "id", header: "ID", defaultWidth: 400 },
    { name: "state", header: "State" },
  ];
  const dataNodes = useDataNodes();
  const rows = dataNodes.sort((a, b) => a.id.localeCompare(b.id));
  return <DataGrid columns={columns} dataSource={rows} style={{ minHeight: 500 }} />;
};

const DataNodes = () => {
  let { tab } = useParams();
  if (!_.includes(["graph", "nodes", "tasks"], tab)) {
    tab = "graph";
  }

  const [value, setValue] = useState(tab);

  const onChange = (event, newValue) => {
    setValue(newValue);
  };

  return (
    <TabContext value={value}>
      <TabList onChange={onChange}>
        <Tab value="graph" label="Graph" />
        <Tab value="nodes" label="Nodes" />
        <Tab value="tasks" label="Tasks" />
      </TabList>
      <TabPanel value="graph">
        <Graph />
      </TabPanel>
      <TabPanel value="nodes">
        <Nodes />
      </TabPanel>
      <TabPanel value="tasks">
        <Tasks />
      </TabPanel>
    </TabContext>
  );
};

export const DataNodesContent = () => {
  let { path } = useRouteMatch();
  return (
    <Switch>
      <Route path={`${path}:tab`}>
        <DataNodes />
      </Route>
      <Route path={path}>
        <DataNodes />
      </Route>
    </Switch>
  );
};
