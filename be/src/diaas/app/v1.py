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


@api_v1.route("/user", methods=["GET"])
@as_json
def session_get():
    if "uid" in session:
        u = User.query.filter(User.uid == session["uid"]).one_or_none()
        if u is None:
            return {}, 404
        else:
            return MOCK_USER  # _user_as_json(u)
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
