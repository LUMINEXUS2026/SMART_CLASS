from functools import wraps

from flask import abort
from flask_login import current_user, login_required


def roles_required(*roles):
    def decorator(fn):
        @wraps(fn)
        @login_required
        def wrapper(*args, **kwargs):
            if not current_user.has_role(*roles):
                abort(403)
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def strict_roles_required(*roles):
    return roles_required(*roles)
