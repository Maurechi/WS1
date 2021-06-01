import { Box, Dialog, DialogTitle } from "@material-ui/core";
import Tab from "@material-ui/core/Tab";
import TabContext from "@material-ui/lab/TabContext";
import TabList from "@material-ui/lab/TabList";
import TabPanel from "@material-ui/lab/TabPanel";
import DagreGraph from "dagre-d3-react";
import { formatDistance, formatDistanceToNow, parseISO } from "date-fns";
import { utcToZonedTime } from "date-fns-tz";
import _ from "lodash";
import { observer } from "mobx-react-lite";
import React, { useMemo, useRef, useState } from "react";
import { Route, Switch, useHistory, useParams, useRouteMatch } from "react-router-dom";

import { DataGrid } from "diaas/DataGrid.js";
import { useStateV } from "diaas/form.js";
import { useAppState } from "diaas/state.js";
import {
  ActionButton,
  CircularProgressWithLabel,
  DefinitionTable as DefTable,
  Literal,
  Spinner,
  useResize,
  useTick,
} from "diaas/ui.js";

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
            // align: "DR",
            // ranker: "longest-path",
            // ranker: "tighest-tree",
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

const TaskDialog = ({ tid, open, onClose }) => {
  const { backend } = useAppState();

  const tasks = useDataTasks();

  let task = null;
  tasks.forEach((t) => {
    if (t.id === tid.v) {
      task = t;
    }
  });

  const taskState = useStateV(null);

  if (!open.v) {
    task = { info: {} };
  } else {
    if (task === null) {
      throw new Error(`Selected task is ${tid.v} but no task with that id.`);
    }

    if (task._state === undefined) {
      task._state = "INIT";
    }

    if (task._state === "INIT") {
      task._state = "LOADING";
      backend.taskInfo(task.id).then((t) => {
        task._state = "LOADED";
        task.info = t.info;
        taskState.v = task._state;
      });
    }
    taskState.v = task._state;
  }

  const spinner = useMemo(() => <Spinner color="gray40" />, []);

  let stdout;
  let stderr;
  if (task._state === "LOADED") {
    stdout = task.info.stdout ? <Literal>{task.info.stdout}</Literal> : null;
    stderr = task.info.stderr ? <Literal>{task.info.stderr}</Literal> : null;
  } else if (task._state === "LOADING" || task._state === "INIT") {
    stdout = task.info.stdout ? spinner : null;
    stderr = task.info.stderr ? spinner : null;
  } else {
    stdout = null;
    stderr = null;
  }

  if (stdout) {
    stdout = <DefTable.Term label="stdout"> {stdout} </DefTable.Term>;
  }
  if (stderr) {
    stderr = <DefTable.Term label="stderr"> {stderr} </DefTable.Term>;
  }

  return (
    <Dialog
      fullWidth={true}
      maxWidth="lg"
      onClose={() => {
        open.toggle();
        onClose();
      }}
      aria-labelledby="task-details-dialog-title"
      open={open.v}
    >
      <DialogTitle id="simple-dialog-title">Task {task.id}</DialogTitle>
      <Box p={2}>
        <DefTable>
          <DefTable.Term label="PID">{task.info.pid}</DefTable.Term>
          <DefTable.Term label="Started At">{task.info.started_at}</DefTable.Term>
          {stdout}
          {stderr}
          {task.info.otherInfo !== null && (
            <DefTable.Term label="Other">
              <Literal>{task.info.otherInfo}</Literal>
            </DefTable.Term>
          )}
        </DefTable>
      </Box>
    </Dialog>
  );
};

const Tasks = () => {
  let { tid: tidFromURL } = useParams();
  const history = useHistory();

  const columns = [
    { defaultFlex: 1, name: "nid", header: "Node ID", defaultWidth: 100 },
    { defaultFlex: 1, name: "state", header: "State" },
    {
      defaultFlex: 1,
      name: "startedAt",
      header: "Started At",
      defaultWidth: 200,
    },
    {
      defaultFlex: 1,
      name: "completedAt",
      header: "Completed After",
      defaultWidth: 200,
      render: ({ data: { state, startedAt, completedAt } }) => {
        if (completedAt) {
          return formatDistance(utcToZonedTime(parseISO(startedAt)), utcToZonedTime(parseISO(completedAt)));
        } else if (state === "RUNNING") {
          return <i>running for {formatDistanceToNow(utcToZonedTime(parseISO(startedAt)))}</i>;
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

  const tasks = useDataTasks();

  const rows = tasks
    .map((t) => {
      const { nid, pid, stdout, stderr, ...otherInfo } = t.info;
      return {
        nid: nid || `[${t.id}]`,
        id: t.id,
        state: t.state,
        otherInfo: otherInfo,
        startedAt: t.started_at,
        completedAt: t.completed_at,
        pid: pid,
        stdout: stdout,
        stderr: stderr,
      };
    })
    .sort((a, b) => b.startedAt.localeCompare(a.startedAt))
    .slice(0, 100);

  const open = useStateV(!!tidFromURL);
  const tid = useStateV(tidFromURL || null);

  const select = ({ data }) => {
    tid.v = data.id;
    open.v = true;
    history.push("/data-nodes/tasks/" + tid.v);
  };

  const onClose = () => {
    history.push("/data-nodes/tasks/");
  };

  return (
    <>
      <TaskDialog tid={tid} open={open} onClose={onClose} />
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

const Content = observer(({ tab: tabProp }) => {
  console.log("tabProp", tabProp);
  let defaultTab = tabProp || useParams().tab;
  if (!_.includes(["graph", "nodes", "tasks"], defaultTab)) {
    defaultTab = "graph";
  }

  const [tab, setTab] = useState(defaultTab);

  const history = useHistory();

  const onChange = (event, newValue) => {
    setTab(newValue);
    history.push("/data-nodes/" + newValue);
  };

  const { user, backend } = useAppState();

  const refreshInterval = 30;
  const tick = useTick({ bound: refreshInterval + 1 });
  const secondsRemaining = refreshInterval - tick;
  const percentRemaining = Math.min(100, Math.round(100 * (secondsRemaining / refreshInterval)));
  const [loading, setLoading] = useState(null);

  // console.log(tick, secondsRemaining, percentRemaining);

  if (tick === 0 && loading === null) {
    setLoading(
      backend.getDataNodes().then((data) => {
        user.dataStack.data = data;
        setLoading(null);
      })
    );
  }

  return (
    <TabContext value={tab}>
      <Box display="flex" alignItems="center">
        <Box style={{ flexGrow: 1 }}>
          <TabList onChange={onChange}>
            <Tab value="graph" label="Graph" />
            <Tab value="nodes" label="Nodes" />
            <Tab value="tasks" label="Tasks" />
          </TabList>
        </Box>
        <Box pr={4}>
          <CircularProgressWithLabel value={percentRemaining}>{secondsRemaining}s</CircularProgressWithLabel>
        </Box>
      </Box>
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
});

export const DataNodesContent = () => {
  let { path } = useRouteMatch();
  return (
    <Switch>
      <Route path={`${path}tasks/:tid`}>
        {" "}
        <Content tab="tasks" />{" "}
      </Route>
      <Route path={`${path}tasks`}>
        {" "}
        <Content tab="tasks" />{" "}
      </Route>
      <Route path={`${path}graph`}>
        {" "}
        <Content tab="graph" />{" "}
      </Route>
      <Route path={`${path}nodes`}>
        {" "}
        <Content tab="nodes" />{" "}
      </Route>
    </Switch>
  );
};
