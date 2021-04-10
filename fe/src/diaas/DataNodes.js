import { Box } from "@material-ui/core";
import DagreGraph from "dagre-d3-react";
import { observer } from "mobx-react-lite";
import React, { useRef } from "react";
import { Route, Switch, useRouteMatch } from "react-router-dom";

import { useAppState } from "diaas/state.js";
import { useResize } from "diaas/ui.js";

const DataNodes = observer(() => {
  const { user } = useAppState();

  const data_nodes = user.dataStack.data_nodes
    .slice()
    .sort((a, b) => b - a)
    .map((n) => Object.assign({}, n, { upstream: (n.upstream || []).sort() }));

  const nodes = {};
  const linksList = [];

  const state_colors = {
    FRESH: "green",
    STALE: "#666666",
    REFRESHING: "orange",
    REFRESHING_STALE: "orange",
    ORPHAN: "red",
  };

  data_nodes.forEach((n, i) => {
    nodes[n.id] = {
      id: i,
      label: n.id,
      config: { style: "fill: " + state_colors[n.state] || "blue" },
    };
  });

  const nodeList = Object.values(nodes).map((n) => n);

  data_nodes.forEach((n) => {
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
        <Box style={{ flexGrow: 1 }}>Data Nodes:</Box>
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
