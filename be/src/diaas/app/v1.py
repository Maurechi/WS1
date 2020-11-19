from flask import Blueprint, request, session

from diaas.app.utils import Request, as_json
from diaas.model import User, initial_user_setup

api_v1 = Blueprint("api_v1", __name__)


def _warehouse_as_json(wh):
    return {"whid": wh.code}


def _workbench_as_json(wb):
    return {
        "wbid": wb.code,
        "branch": "null",
        "warehouse": _warehouse_as_json(wb.warehouse),
    }


def _user_as_json(user):
    return {
        "uid": user.code,
        "workbenches": [_workbench_as_json(wb) for wb in user.workbenches],
    }


@api_v1.route("/user", methods=["GET"])
@as_json
def session_get():
    if "uid" in session:
        u = User.query.filter(User.uid == session["uid"]).one_or_none()
        if u is None:
            return {}, 404
        else:
            return _user_as_json(u)
    else:
        return {}, 404


@api_v1.route("/user", methods=["POST"])
@as_json
def session_post():
    email = Request(request).get_value("email")
    u = User.query.filter(User.email == email).one_or_none()
    if u is None:
        u = initial_user_setup(email)

    session["uid"] = u.uid
    return _user_as_json(u)
