from functools import wraps
from flask import session, redirect, url_for, request, abort
import db

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            abort(403, description="You must be logged in to access this page.")
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session or session['role'] not in roles:
                abort(403, description="You do not have permission to access this page.")
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def group_member_required(param='group_id'):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session.get('user_id')
            group_id = kwargs.get(param) or request.view_args.get(param)
            if not user_id or not group_id or not db.check_user_joined_group(user_id, group_id):
                abort(403, description="You must be a member of this group to access this page.")
            return f(*args, **kwargs)
        return decorated_function
    return decorator

