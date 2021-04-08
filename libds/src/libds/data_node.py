from dataclasses import dataclass
from datetime import timedelta
from typing import Optional, Sequence

from libds.utils import _timedelta_as_info


@dataclass
class DataNode:
    id: str
    container: Optional[str] = None
    inputs: Optional[Sequence[str]] = None
    details: Optional[dict] = None
    expires_after: Optional[timedelta] = None

    def info(self):
        i = {"id": self.id}
        if self.container is not None:
            i["container"] = self.container
        if self.inputs:
            i["inputs"] = self.inputs
        if self.details:
            i["details"] = self.details
        if self.expires_after is not None:
            i["expires_after"] = _timedelta_as_info(self.expires_after)

        return i


class DataNodeDB:
    CONCURRENCY = 4

    def __init__(self, data_stack):
        self.data_stack = data_stack
        self.nodes = None

    def connect(self):
        self._ensure_schema()
        return None

    def load(self):
        with self.connect() as conn:
            nodes = self.data_stack.data_nodes()

            for n in nodes:
                n.state = None
            states = conn.execute(
                "SELECT node_id, state FROM data_nodes WHERE node_id = ?"
            )
            for state in states:
                nodes[state["id"]].state = state["state"]

            for n in nodes:
                if n.state is None:
                    n.state = "STALE"
                    conn.execute(
                        "INSERT INTO data_nodes (node_id, state) values (?, 'STALE')",
                        n.id,
                    )

            self.nodes = nodes

        return self

    def tick(self):
        with self.connect() as conn:
            res = conn.execute(
                "SELECT count(*) as count FROM data_nodes WHERE state = 'REFRESHING'"
            )
            num_active = res["count"]
            if num_active >= self.CONCURRENCY:
                return

            stale_with_fresh_inputs = []

            for node in self.nodes:
                if node.state == "STALE":
                    if node.inputs == []:
                        stale_with_fresh_inputs.append(node)
                    if all(self.nodes[i].state == "FRESH" for i in node.inputs):
                        stale_with_fresh_inputs.append(node)
