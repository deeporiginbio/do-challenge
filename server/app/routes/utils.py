import hashlib
import json
from functools import wraps

from flask import request
from werkzeug.exceptions import Unauthorized

from app.config.core import settings


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        api_key = request.headers.get("X-API-KEY")
        if not api_key or api_key != settings.ADMIN_API_KEY:
            raise Unauthorized("Unauthorized")
        return fn(*args, **kwargs)

    return wrapper


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        secret_key = request.headers.get("X-TOKEN")
        if not secret_key:
            raise Unauthorized("Unauthorized")
        return fn(secret_key, *args, **kwargs)
    return wrapper


def generate_hash(int_list: list[int]) -> str:
    list_str = json.dumps(int_list, sort_keys=True)
    return hashlib.sha256(list_str.encode()).hexdigest()