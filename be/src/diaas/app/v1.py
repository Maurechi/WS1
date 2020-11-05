from flask import Blueprint, session
from diaas.app.utils import as_json
from diaas.model import Session
from diaas.db import db

api_v1 = Blueprint('api_v1', __name__)


@api_v1.route('/session', methods=['GET'])
@as_json
def session_get():
    if 'id' in session:
        return {'id': session['id']}
    else:
        return {}, 404


@api_v1.route('/session', methods=['POST'])
@as_json
def session_post():
    s = Session()
    db.session.add(s)
    db.session.commit()
    s.ensure_local_data()
    session['id'] = s.id
    return {'id': s.id}
