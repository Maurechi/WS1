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

  return user.dataStack.data.nodes.slice().map((n) => Object.assign({}, n, { upstream: (n.upstream || []).sort() }));
};

const useDataTasks = () => {
  const { user } = useAppState();

  return user.dataStack.data.tasks;
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

const Nodes = observer(() => {
  const { backend } = useAppState();
  const columns = [
    { name: "id", header: "ID", defaultWidth: 400 },
    { name: "state", header: "State" },
    {
      name: "Action",
      header: "",
      render: ({ data }) => {
        if (_.includes(["FRESH", "REFRESHING"], data.state)) {
          return <ActionButton onClick={() => backend.updateDataNodeState(data.id, "STALE")}>Refresh</ActionButton>;
        } else if (_.includes(["ORPHAN"], data.state)) {
          return <ActionButton onClick={() => backend.deleteDataNode(data.id)}>Delete</ActionButton>;
        } else {
          return "";
        }
      },
    },
  ];
  const tasks = useDataNodes();
  const rows = tasks.sort((a, b) => a.id.localeCompare(b.id));
  return <DataGrid columns={columns} dataSource={rows} style={{ minHeight: 1000 }} />;
});

const Tasks = () => {
  const columns = [
    { defaultFlex: 1, name: "id", header: "ID", defaultWidth: 100 },
    { defaultFlex: 1, name: "state", header: "State" },
    { defaultFlex: 4, name: "startedAt", header: "Started At", defaultWidth: 200 },
    { defaultFlex: 8, name: "info", header: "Other Info", render: ({ value }) => <pre>{value}</pre> },
  ];
  const dataNodes = useDataTasks();
  const rows = dataNodes
    .map((t) => {
      const { started_at, ...otherInfo } = t.info;
      return {
        id: t.id,
        state: t.state,
        startedAt: started_at,
        info: JSON.stringify(otherInfo),
      };
    })
    .sort((a, b) => b.startedAt.localeCompare(a.startedAt));
  return <DataGrid columns={columns} dataSource={rows} style={{ minHeight: 1000 }} editable={true} />;
};

const Content = () => {
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
        <Content />
      </Route>
      <Route path={path}>
        <Content />
      </Route>
    </Switch>
  );
};
