# Helper functions and stuff

from flask import abort
from flask import session

ALLOWED_EXTENSIONS = set(['jpg', 'jpeg', 'gif', 'png'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def check_login():
    if not session.get('logged_in'):
        abort(401)
