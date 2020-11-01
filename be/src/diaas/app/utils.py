from pathlib import Path
import decimal
from collections.abc import Mapping, Sequence
from functools import wraps
from pprint import pformat

import arrow
from flask_json import FlaskJSON, json_response, request
from diaas.db import db


class ApiError(Exception):
    STATUS = None
    CODE = None

    def __init__(self, status=None, code=None, source=None, title=None, detail=None):
        self.status = status or self.STATUS
        self.code = code or self.CODE
        self._source = source
        self.title = title
        self.detail = detail

    def source(self):
        return self._source

    def as_json(self):
        error = {
            "status": self.status,
            "code": self.code,
        }
        if self.title is not None:
            error["title"] = self.title
        if self.detail is not None:
            error["detail"] = self.detail
        source = self.source()
        if source is not None:
            error["source"] = source
        return error


def register_error_handler(app):
    def errorhandler(e):
        return json_response(status_=e.status, data_=dict(errors=[e.as_json()]))

    app.errorhandler(ApiError)(errorhandler)
    return app


class NotFoundError(ApiError):
    STATUS = 404
    CODE = "not-found"

    def __init__(self, entity_type=None, entity_id=None):
        super().__init__()
        self.entity_id = entity_id
        self.entity_type = entity_type

    def source(self):
        s = {}
        if self.entity_id is not None:
            s["id"] = self.entity_id
        if self.entity_type is not None:
            s["type"] = self.entity_type
        return s


class AlreadyExistsError(ApiError):
    STATUS = 409
    CODE = "entity-already-exists"

    def __init__(self, entity_type, key, existing_id):
        title = f"Entity of type {entity_type}, found by {key}, already exists with key {key}."
        source = dict(type=entity_type, key=key, existing_id=existing_id)
        super().__init__(
            source=source, title=title,
        )


class ValidationError(ApiError):
    STATUS = 422
    CODE = "validation-failure"

    def __init__(self, title, source=None):
        if source is None:
            source = {"request": request.get_json()}
        super().__init__(source=source, title=title)


flask_json = FlaskJSON()

EIGHT_PLACES = decimal.Decimal(10) ** -8


@flask_json.encoder
def encode(thing):
    if isinstance(thing, decimal.Decimal):
        try:
            return float(thing.quantize(EIGHT_PLACES))
        except decimal.InvalidOperation:
            return float(thing)
    elif isinstance(thing, arrow.Arrow):
        return thing.isoformat()
    elif isinstance(thing, Path):
        return str(thing)
    else:
        return None


def _parse_view_result(result):
    data = status = headers = None
    if isinstance(result, tuple):
        if len(result) > 0:
            data = result[0]
        if len(result) > 1:
            status = result[1]
        if len(result) > 2:
            headers = result[2]
    else:
        data = result
        status = 200

    return data, status, headers


def as_json(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        data, status, headers = _parse_view_result(view(*args, **kwargs))

        if not isinstance(data, (Mapping, Sequence, int, str, float)):
            raise Exception(
                f"as_json decorated functions must return a dict or a seq; "
                f"not a `{pformat(data)}` of type `{type(data)}`"
            )

        return json_response(status_=status, data_=dict(data=data), headers_=headers)

    return wrapped


def no_autoflush(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        with db.session.no_autoflush:
            return view(*args, **kwargs)

    return wrapped
