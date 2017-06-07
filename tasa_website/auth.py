from flask import request, session, redirect, url_for, \
     abort, render_template, flash

from . import app
from . import secrets

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != secrets['username']:
            error = 'Invalid username'
        elif request.form['password'] != secrets['password']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('admin_panel'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('index'))

def check_login():
    if not session.get('logged_in'):
        abort(401)
