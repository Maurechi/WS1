import CheckCircleIcon from "@material-ui/icons/CheckCircle";
import ErrorIcon from "@material-ui/icons/Error";
import WarningIcon from "@material-ui/icons/Warning";
import { formatDistance } from "date-fns";
import _ from "lodash";
import { observer } from "mobx-react-lite";
import React from "react";
import { Link } from "react-router-dom";

import { DataTable } from "diaas/DataTable.js";
import { useAppState } from "diaas/state.js";

export const summarizeSourceDataNodes = (source) => {
  const nodes = _.values(source.data_nodes);
  const fresh_nodes = _.filter(nodes, (n) => n.state === "FRESH");
  const not_fresh_nodes = _.filter(nodes, (n) => n.state !== "FRESH");
  const done_nodes = _.filter(nodes, (n) => n.last_task && n.last_task.state === "DONE");
  const errored_nodes = _.filter(nodes, (n) => n.last_task && n.last_task.state === "ERRORED");

  const summary = {
    nodes,
    num_nodes: nodes.length,
    has_data_nodes: nodes.length > 0,
    fresh_nodes,
    num_fresh: fresh_nodes.length,
    not_fresh_nodes,
    num_not_fresh: not_fresh_nodes.length,
    done_nodes,
    num_done: done_nodes.length,
    errored_nodes,
    num_errored: errored_nodes.length,
  };

  summary.has_errors = errored_nodes.length > 0;
  summary.has_refreshing = not_fresh_nodes.length > 0;
  summary.is_fresh = !summary.has_errors && !summary.has_refreshing;

  if (summary.num_done > 0) {
    const max_completed_at = _.max(_.map(summary.done_nodes, (n) => n.last_task.completed_at));
    summary.age = formatDistance(new Date(max_completed_at), new Date());
  }

  return summary;
};

export const CheckMark = ({ error, warning, state }) => {
  if (error || state === "error") {
    return <ErrorIcon style={{ color: "red" }} />;
  } else if (warning || state === "warning") {
    return <WarningIcon style={{ color: "orange" }} />;
  } else {
    return <CheckCircleIcon style={{ color: "green" }} />;
  }
};

export const SourcesDashboard = observer(() => {
  const { user } = useAppState();
  const sources = _.sortBy(user.data_stacks[0].sources, "id");

  const columns = [
    { label: "", style: { width: "10%" } },
    { label: "ID", style: { width: "10%" } },
    { label: "Details", style: { width: "80%" } },
  ];

  const rows = sources.map((s) => {
    const summ = summarizeSourceDataNodes(s);

    const link = <Link to={`/sources/${s.id}`}>{s.id}</Link>;

    if (summ.has_errors) {
      return [
        <CheckMark error />,
        link,
        `${summ.num_fresh} task${summ.num_fresh === 1 ? "" : "s"} ready out of ${summ.num_nodes}`,
      ];
    } else if (summ.has_refreshing) {
      return [<CheckMark warning />, link, `${summ.num_fresh} completed out of ${summ.num_nodes}`];
    } else {
      return [<CheckMark healthy />, link, `Done. Last completed ${summ.age} ago`];
    }
  });

  return <DataTable columns={columns} rows={rows} />;
});
