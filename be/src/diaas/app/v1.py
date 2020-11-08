from flask import Blueprint, request, session

from diaas.app.utils import Request, as_json
from diaas.model import User

api_v1 = Blueprint("api_v1", __name__)


@api_v1.route("/user", methods=["GET"])
@as_json
def session_get():
    if "uid" in session:
        return {"uid": session["uid"]}
    else:
        return {}, 404


@api_v1.route("/user", methods=["POST"])
@as_json
def session_post():
    email = Request(request).get_value("email")
    u = User.query.filter(User.email == email).one_or_none()
    if u is None:
        return {}, 404
    else:
        return {"uid": u.code, "email": u.email}
