import { Box } from "@material-ui/core";
import { DagreReact } from "dagre-reactjs";
import { observer } from "mobx-react-lite";
import React from "react";
import { Route, Switch, useRouteMatch } from "react-router-dom";

import { useAppState } from "diaas/state.js";

const DataNodes = observer(() => {
  const { user } = useAppState();

  const data_nodes = user.dataStack.data_nodes
    .slice()
    .sort((a, b) => b - a)
    .map((n) => Object.assign({}, n, { inputs: (n.inputs || []).sort() }));

  const nodes = {};
  const edgeList = [];

  const state_colors = {
    FRESH: "green",
    STALE: "#666666",
    REFRESHING: "orange",
    REFRESHING_STALE: "orange",
    ORPHAN: "red",
  };

  data_nodes.forEach((n, i) => {
    console.log("state = ", n.state);
    console.log("adding", n.id);
    nodes[n.id] = {
      id: i,
      label: n.id,
      styles: {
        shape: {
          styles: {
            strokeWidth: "1.5",
            stroke: "#868686",
          },
        },
        label: {
          styles: {
            fill: state_colors[n.state] || "red",
          },
        },
        node: {
          padding: {
            top: 10,
            bottom: 10,
            left: 10,
            right: 10,
          },
        },
      },
    };
  });

  const nodeList = Object.values(nodes).map((n) => n);

  data_nodes.forEach((n) => {
    if (n.inputs) {
      n.inputs.forEach((i) => {
        console.log("input", i, "=>", nodes[i]);
        edgeList.push({ from: nodes[i].id, to: nodes[n.id].id });
      });
    }
  });

  console.log("nodes", nodeList);
  console.log("edges", edgeList);

  return (
    <Box>
      <Box display="flex" mb={3}>
        <Box style={{ flexGrow: 1 }}>Data Nodes:</Box>
      </Box>
      <svg id="data-nodes" width={1800} height={4000}>
        <DagreReact
          nodes={nodeList}
          edges={edgeList}
          graphOptions={{
            rankdir: "LR",
            ranker: "tight-tree",
            marginx: 15,
            marginy: 15,
            ranksep: 55,
            nodesep: 15,
          }}
        />
      </svg>
    </Box>
  );
});

export const DataNodesContent = () => {
  let { path } = useRouteMatch();
  return (
    <Switch>
      <Route path={path}>
        <DataNodes />
      </Route>
    </Switch>
  );
};
