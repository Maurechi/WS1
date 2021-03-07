from flask import Blueprint, g, request, session

from diaas.app.login import login
from diaas.app.utils import Request, as_json, login_required
from diaas.model import User

api_v1 = Blueprint("api_v1", __name__)


def _user_as_json(user):
    return {
        "uid": user.code,
        "display_name": user.display_name,
        "data_stacks": {ds.id: ds.libds.info() for ds in user.data_stacks.values()},
    }


@api_v1.route("/session", methods=["GET"])
@as_json
def session_get():
    if "uid" in session:
        u = User.query.filter(User.uid == session["uid"]).one_or_none()
        if u is None:
            return None, 404
        else:
            return _user_as_json(u), 200
    else:
        return None, 404


@api_v1.route("/session", methods=["POST"])
@as_json
def session_post():
    u = login()
    if u:
        session["uid"] = u.uid
        return _user_as_json(u)
    else:
        return {}, 401


@api_v1.route("/session", methods=["DELETE"])
@as_json
def session_delete():
    session.clear()
    return None, 200


@api_v1.route("/sources/<path:id>", methods=["POST"])
@login_required
@as_json
def source_update(id):
    libds = g.user.current_data_stack.libds
    return libds.source_update(id, request.get_json())


@api_v1.route("/sources/<path:id>/load", methods=["POST"])
@login_required
@as_json
def source_load(id):
    libds = g.user.current_data_stack.libds
    return libds.source_load(id)


@api_v1.route("/transformation/<path:id>", methods=["POST"])
@login_required
@as_json
def transformation_update(id):
    req = Request()
    libds = g.user.current_data_stack.libds
    return libds.transformation_update(
        id=req.require("id"),
        type=req.require("type"),
        source=req.require("source"),
        current_id=id,
    )


@api_v1.route("/transformation/", methods=["POST"])
@login_required
@as_json
def transformation_create():
    req = Request()
    libds = g.user.current_data_stack.libds
    return libds.transformation_update(
        id=req.require("id"),
        type=req.param("type", default="select"),
        source=req.require("source"),
    )


@api_v1.route("/transformation/<path:id>/load", methods=["POST"])
@login_required
@as_json
def transformation_load(id):
    libds = g.user.current_data_stack.libds
    return libds.transformation_load(id)
