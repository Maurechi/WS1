from flask import Blueprint, request, session

from diaas.app.utils import Request, as_json
from diaas.model import User, Warehouse, Workbench

api_v1 = Blueprint("api_v1", __name__)


@api_v1.route("/session", methods=["GET"])
@as_json
def session_get():
    if "id" in session:
        return {"id": session["id"]}
    else:
        return {}, 404


@api_v1.route("/session", methods=["POST"])
@as_json
def session_post():
    email = Request(request).get_value("email")
    session["email"] = email
    return {"email": email}
