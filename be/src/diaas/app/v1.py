from flask import Blueprint, g, request, session

from diaas.app.login import login
from diaas.app.utils import Request, as_json, login_required
from diaas.model import User

api_v1 = Blueprint("api_v1", __name__)


def _data_stack_as_json(ds):
    info = ds.libds.info()
    tasks = info.get("data", {}).get("tasks", None)
    if tasks is not None:
        for task in tasks:
            if "info" in task:
                for key, value in task["info"].items():
                    if isinstance(value, str) and len(value) > 200:
                        value = value[:99] + "\n...\n" + value[-99:]
                        task["info"][key] = value
    return info


def _session_json(user):
    return {
        "uid": user.code,
        "display_name": user.display_name,
        "email": user.email,
        "data_stacks": {
            ds.id: _data_stack_as_json(ds) for ds in user.data_stacks.values()
        },
    }


@api_v1.route("/session", methods=["GET"])
@as_json
def session_get():
    if "uid" in session:
        u = User.query.filter(User.uid == session["uid"]).one_or_none()
        if u is None:
            return None, 404
        else:
            return _session_json(u), 200
    else:
        return None, 404


@api_v1.route("/session", methods=["POST"])
@as_json
def session_post():
    u = login()
    if u:
        session["uid"] = u.uid
        return _session_json(u)
    else:
        return {}, 401


@api_v1.route("/session", methods=["DELETE"])
@as_json
def session_delete():
    session.clear()
    return None, 200


@api_v1.route("/sources/<path:id>/inspect", methods=["GET"])
@login_required
@as_json
def inspect_source(id):
    libds = g.user.current_data_stack.libds
    return libds.inspect("source", id)


@api_v1.route("/files/<path:file>", methods=["POST"])
@login_required
@as_json
def update_file(file):
    libds = g.user.current_data_stack.libds
    payload = request.get_json()
    if "text" in payload:
        libds.update_file(file, payload["text"])
    if "dst" in payload:
        libds.move_file(file, payload["dst"])
    return {}


@api_v1.route("/files/<path:file>", methods=["DELETE"])
@login_required
@as_json
def delete_file(file):
    libds = g.user.current_data_stack.libds
    return libds.delete_file(file)


@api_v1.route("/models/<path:mid>", methods=["GET"])
@login_required
@as_json
def model_info(mid):
    info = g.user.current_data_stack.libds.info()
    for m in info.get("models", []):
        if m.get("id") == mid:
            return m
    else:
        return None


@api_v1.route("/model/<path:id>", methods=["POST"])
@login_required
@as_json
def model_update(id):
    req = Request()
    libds = g.user.current_data_stack.libds
    return libds.model_update(
        id=req.require("id"),
        type=req.require("type"),
        source=req.require("source"),
        current_id=id,
    )


@api_v1.route("/model/", methods=["POST"])
@login_required
@as_json
def model_create():
    req = Request()
    libds = g.user.current_data_stack.libds
    return libds.model_update(
        id=req.require("id"),
        type=req.param("type", default="select"),
        source=req.require("source"),
    )


@api_v1.route("/store/execute", methods=["POST"])
@login_required
@as_json
def execute():
    req = Request()
    libds = g.user.current_data_stack.libds
    return libds.execute(
        statement=req.require("statement"),
    )


@api_v1.route("/data-nodes/<path:nid>/update", methods=["POST"])
@login_required
@as_json
def data_node_update(nid):
    req = Request()
    libds = g.user.current_data_stack.libds
    return libds.data_node_update(nid=nid, state=req.require("state"))


@api_v1.route("/data-nodes/<path:nid>", methods=["DELETE"])
@login_required
@as_json
def data_node_delete(nid):
    libds = g.user.current_data_stack.libds
    return libds.data_node_delete(nid=nid)


@api_v1.route("/tasks/<path:tid>", methods=["GET"])
@login_required
@as_json
def task_info(tid):
    info = g.user.current_data_stack.libds.info()
    for task in info.get("data", {}).get("tasks", []):
        if task.get("id") == tid:
            return task
    else:
        return None
