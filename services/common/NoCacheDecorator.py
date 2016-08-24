# See https://gist.github.com/roshammar

from flask import make_response
from functools import update_wrapper


def nocache(f):
    """
    Add cache control headers to prevent web caches from caching results.
    """
    def new_func(*args, **kwargs):
        resp = make_response(f(*args, **kwargs))
        resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0'
        return resp
    return update_wrapper(new_func, f)
