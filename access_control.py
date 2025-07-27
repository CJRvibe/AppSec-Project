from functools import wraps
from flask import session, redirect, url_for, request, abort

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

