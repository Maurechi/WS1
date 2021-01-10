from flask import Blueprint, g, request, session

from diaas.app.utils import Request, as_json, login_required
from diaas.model import User

api_v1 = Blueprint("api_v1", __name__)


def _user_as_json(user):
    return {
        "uid": user.code,
        "displayName": user.display_name,
        "dataStacks": [ds.libds.info() for ds in user.data_stacks],
    }


MOCK_USER = dict(
    uid="q18y",
    workbenches=[
        dict(
            wbid="kauw",
            name="master",
            branch="master",
            warehouse=dict(
                whid="a7rt",
                name="Astrospace GmbH",
            ),
            branches=dict(
                master=dict(
                    files={
                        "pw3B": dict(
                            id="pw3B",
                            name="rockets_d.sql",
                            details="Locally Modified",
                            lastModified="Today",
                            code=(
                                "select\n"
                                "  timestamp(json_extract(data, '$.launchDate')) as launch_date\n"
                                "  ,json_extract(data, '$.status')) as status\n"
                                "  ,upper(json_extract(data, '$.launchPad'))) as launch_pad\n"
                                "from rockets_r;"
                            ),
                        ),
                        "orhj": dict(
                            id="orhj",
                            name="launches_d.sql",
                            details="Unmodified",
                            lastModified="1 Week Ago (Nov 3rd, 2020)",
                        ),
                        "mzsk": dict(
                            id="mzsk",
                            name="conversions_f.sql",
                            details="Unmodified",
                            lastModified="1 Week Ago (Nov 3rd, 2020)",
                        ),
                        "9x27": dict(
                            id="9x27",
                            name="rockets_cleaned.py",
                            details="Unmodified",
                            lastModified="1 Week Ago (Nov 3rd, 2020)",
                            code=(
                                "import pandas as pd\n"
                                "from diaas_modules.geo import Geo, AddressNotFound \n"
                                "\n"
                                "def transform_row(row):\n"
                                "    if row.lat is not None and row.lon is not None:\n"
                                "        row.geo = Geo.locate(row.lat, row.lon)\n"
                                "    elif row.address_text is not None:\n"
                                "        try:\n"
                                "            row.geo = Geo.geocode(row.address_text)\n"
                                "        except AddressNotFound:\n"
                                "            row.geo = None\n"
                            ),
                        ),
                    },
                    tree=["pw3B", "orhj", "mzsk", "9x27"],
                ),
            ),
        ),
    ],
)


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
    email = Request(request).get_value("email")
    u = User.ensure_user(email)
    session["uid"] = u.uid
    return _user_as_json(u)


@api_v1.route("/session", methods=["DELETE"])
@as_json
def session_delete():
    session.clear()
    return None, 200


@api_v1.route("/sources/<path:id>", methods=["POST"])
@login_required
@as_json
def source_update(id):
    ds = g.user.data_stacks[0]
    return ds.libds.update_source_config(id, request.get_json())


@api_v1.route("/sources/<path:id>/load", methods=["POST"])
@login_required
@as_json
def source_load(id):
    ds = g.user.data_stacks[0]
    return ds.libds.load_source(id)
