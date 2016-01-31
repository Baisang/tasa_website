# all the imports
import dateutil.parser
import os
import requests
import sqlite3
import time

from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash
from contextlib import closing
from datetime import datetime, date

# configuration
DATABASE = 'tasa_website.db'
DEBUG = False

with open('TASA_SECRET', 'r') as f_sec:
    SECRET_KEY = f_sec.read().strip()
with open('TASA_FACEBOOK', 'r') as f_face:
    FACEBOOK_KEY = f_face.read().strip()
with open('TASA_USERNAME', 'r') as f_user:
    USERNAME = f_user.read().strip()
with open('TASA_PASSWORD', 'r') as f_pw:
    PASSWORD = f_pw.read().strip()

app = Flask(__name__)
app.config.from_object(__name__)

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.before_request
def before_request():
    g.db = connect_db()
    g.db.row_factory = sqlite3.Row

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    cur = g.db.execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


@app.route('/')
def show_latest_event():
    events = query_db('select title, time, location, link, image_url from events order by unix_time desc')
    upcoming_events = events.filter(lambda e: e['unix_time'] > int(time.time()))
    if len(upcoming_events) == 0:
        upcoming_events.append(events[0])
    return render_template('show_latest_event.html', event=upcoming_events[0])

@app.route('/add', methods=['POST'])
def add_event():
    if not session.get('logged_in'):
        abort(401)
    try:
        url = request.form['link']
        link = url
        # Facebook event url example:
        # https://www.facebook.com/events/1201801539835081/
        # we need to get the last part, the id. so let's find the index of the 2nd to last '/'
        # split the string and go from there.
        index = url.rfind('/', 0, url.rfind('/'))
        fb_event_id = url[index : len(url) - 1]

        # need to submit GET req to something like this:
        # https://graph.facebook.com/v2.5/1201801539835081?access_token=token
        fb_api_base = 'https://graph.facebook.com/v2.5/'
        fb_api_base += fb_event_id
        payload = {"access_token": FACEBOOK_KEY}
        res = requests.get(fb_api_base, params=payload).json()
        title = res['name']
        location = res['place']['name']
        time_str = res['start_time']
        # turns the ISO-8601 format time given to us into epoch time and a formatted string
        date_time = dateutil.parser.parse(time_str)
        time_str = date_time.strftime("%A %B %d %I:%M%p")
        unix_time = int(time.mktime(date_time.timetuple()) + date_time.microsecond/1000000.0)

        # another GET to get the cover photo..?
        payload = {"access_token": FACEBOOK_KEY, "fields": "cover"}
        res = requests.get(fb_api_base, params=payload).json()
        image_url = res['cover']['source']

        query = 'insert into events (title, time, location, link, image_url, unix_time)'\
                'values (?, ?, ?, ?, ?, ?)'
        g.db.execute(query, [title, time_str, location, link, image_url, unix_time])
        g.db.commit()
        flash('New event was successfully posted')
        return redirect(url_for('admin_panel'))
    except Exception as e:
        with open('log', 'a') as f:
            f.write(str(e)+'\n')
        return redirect(url_for('admin_panel'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != USERNAME:
            error = 'Invalid username'
        elif request.form['password'] != PASSWORD:
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
    return redirect(url_for('show_latest_event'))

@app.route('/admin', methods=['GET'])
def admin_panel():
    if not session.get('logged_in'):
        abort(401)
    events = query_db('select title from events order by unix_time desc')
    officers = query_db('select name from officers order by id')
    return render_template('admin.html', events=events, officers=officers)

@app.route('/events', methods=['GET'])
def event_list():
    query = 'select title, time, location, link, image_url, unix_time '\
            'from events order by unix_time desc limit 24'
    events = query_db(query)
    upcoming = []
    recent = []
    current_time = int(time.time())
    for event in events:
        if event['unix_time'] > current_time:
            # key thing here to remember was append vs extend,
            # since event is a sqlite row obj and iterable
            upcoming.append(event)
        else:
            recent.append(event)
    return render_template('events.html', recent=recent, upcoming=upcoming)

@app.route('/officers', methods=['GET'])
def officer_list():
    query = 'select * from officers order by id'
    officers = query_db(query)
    return render_template('officers.html', officers=officers)

@app.route('/add_officer', methods=['POST'])
def add_officer():
    # make sure to add officers by dec. position since they are ordered
    # by id
    if not session.get('logged_in'):
        abort(401)
    name = request.form['name']
    year = request.form['year']
    major = request.form['major']
    position = request.form['position']
    quote = request.form['quote']
    description = request.form['description']
    image_url = request.form['imageurl']
    href = '#' + request.form['name']

    query = 'insert into officers (name, year, major, quote, description, image_url, position, href)'\
            'values (?, ?, ?, ?, ?, ?, ?, ?)'
    g.db.execute(query, [name, year, major, quote, description, image_url, position, href])
    g.db.commit()
    return redirect(url_for('admin_panel'))

@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html')

@app.route('/families', methods=['GET'])
def families():
    return render_template('families.html')

@app.route('/files', methods=['GET'])
def files():
    return render_template('files.html')

@app.route('/donate', methods=['GET'])
def donate():
    return render_template('donate.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
