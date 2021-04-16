import { Box, Dialog, DialogTitle } from "@material-ui/core";
import Tab from "@material-ui/core/Tab";
import TabContext from "@material-ui/lab/TabContext";
import TabList from "@material-ui/lab/TabList";
import TabPanel from "@material-ui/lab/TabPanel";
import DagreGraph from "dagre-d3-react";
import { formatDistance, formatDistanceToNow, parseISO } from "date-fns";
import _ from "lodash";
import { observer } from "mobx-react-lite";
import React, { useRef, useState } from "react";
import { Route, Switch, useHistory, useParams, useRouteMatch } from "react-router-dom";

import { DataGrid } from "diaas/DataGrid.js";
import { useStateV } from "diaas/form.js";
import { useAppState } from "diaas/state.js";
import { ActionButton, DefinitionTable, Literal, useResize } from "diaas/ui.js";

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

    MISSING: "black",
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
        if (!(i in nodes)) {
          nodes[i] = {
            id: i,
            label: i,
            config: { style: "fill: " + state_colors["MISSING"] },
          };
          nodeList.push(nodes[i]);
        }
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
    { defaultFlex: 1, name: "nid", header: "Node ID", defaultWidth: 100 },
    { defaultFlex: 1, name: "state", header: "State" },
    { defaultFlex: 1, name: "startedAt", header: "Started At", defaultWidth: 200 },
    {
      defaultFlex: 1,
      name: "completedAt",
      header: "Completed After",
      defaultWidth: 200,
      render: ({ data: { state, startedAt, completedAt } }) => {
        if (completedAt) {
          return formatDistance(parseISO(startedAt), parseISO(completedAt));
        } else if (state === "RUNNING") {
          return <i>running for {formatDistanceToNow(parseISO(startedAt))}</i>;
        } else {
          return "";
        }
      },
    },
    {
      defaultFlex: 3,
      name: "otherInfo",
      header: "Other Info",
      render: ({ value }) => <pre>{JSON.stringify(value).substring(0, 100)}</pre>,
    },
  ];

  const dataNodes = useDataTasks();

  const rows = dataNodes
    .map((t) => {
      const { nid, started_at, completed_at, pid, stdout, stderr, ...otherInfo } = t.info;
      return {
        nid: nid || `[${t.id}]`,
        id: t.id,
        state: t.state,
        otherInfo: otherInfo,
        startedAt: started_at,
        completedAt: completed_at,
        pid: pid,
        stdout: stdout,
        stderr: stderr,
      };
    })
    .sort((a, b) => b.startedAt.localeCompare(a.startedAt))
    .slice(0, 100);

  const open = useStateV(false);

  const tid = useStateV(null);
  const state = useStateV(null);
  const startedAt = useStateV(null);
  const pid = useStateV(null);
  const stdout = useStateV(null);
  const stderr = useStateV(null);
  const otherInfo = useStateV(null);

  const select = ({ data }) => {
    tid.v = data.id;
    startedAt.v = data.startedAt;
    state.v = data.state;

    pid.v = data.pid;
    stdout.v = data.stdout;
    stderr.v = data.stderr;
    otherInfo.v = _.isEmpty(data.otherInfo) ? null : JSON.stringify(data.otherInfo, null, 4).trim();
    open.v = true;
  };

  console.log("open", open.v);

  const Table = DefinitionTable;

  return (
    <>
      <Dialog
        fullWidth={true}
        maxWidth="lg"
        onClose={() => open.toggle()}
        aria-labelledby="task-details-dialog-title"
        open={open.v}
      >
        <DialogTitle id="simple-dialog-title">Task {tid.v}</DialogTitle>
        <Box p={2}>
          <Table>
            <Table.Term label="PID">{pid.v}</Table.Term>
            <Table.Term label="Started At">{startedAt.v}</Table.Term>
            {stdout.v && (
              <Table.Term label="stdout">
                {" "}
                <Literal>{stdout.v}</Literal>{" "}
              </Table.Term>
            )}
            {stderr.v && (
              <Table.Term label="stderr">
                {" "}
                <Literal>{stderr.v}</Literal>{" "}
              </Table.Term>
            )}
            {otherInfo.v !== null && (
              <Table.Term label="Other">
                <Literal>{otherInfo.v}</Literal>
              </Table.Term>
            )}
          </Table>
        </Box>
      </Dialog>
      <DataGrid
        idProperty="id"
        columns={columns}
        dataSource={rows}
        style={{ minHeight: 1000 }}
        enableSelection
        onSelectionChange={(selected) => select(selected)}
      />
    </>
  );
};

const Content = () => {
  let { tab: tabParam } = useParams();
  if (!_.includes(["graph", "nodes", "tasks"], tabParam)) {
    tabParam = "graph";
  }

  const [tab, setTab] = useState(tabParam);

  const history = useHistory();

  const onChange = (event, newValue) => {
    setTab(newValue);
    history.push("./" + newValue);
  };

  return (
    <TabContext value={tab}>
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
