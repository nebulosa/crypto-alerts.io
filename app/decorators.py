from functools import wraps
from threading import Thread

from flask import flash, redirect, url_for
from flask_login import current_user

def threaded(f):
    def wrapper(*args, **kwargs):
        thr = Thread(target=f, args=args, kwargs=kwargs)
        thr.start()
    return wrapper

def user_anonymous_or_confirmed_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated and not current_user.is_confirmed:
            return redirect(url_for('user_unconfirmed'))
        return func(*args, **kwargs)

    return decorated_function

def user_confirmed_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        #this will fail with an anonymous user
        if not current_user.confirmed:
            return redirect(url_for('user_unconfirmed'))
        return func(*args, **kwargs)

    return decorated_function

def user_mod_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not current_user.is_mod():
            return redirect(url_for('user_not_mod'))
        return func(*args, **kwargs)

    return decorated_function

def user_admin_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            return redirect(url_for('user_not_admin'))
        return func(*args, **kwargs)

    return decorated_function
