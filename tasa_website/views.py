import cStringIO
import dateutil.parser
import os
import random
import requests
import string
import sqlite3
import time
import urllib
import yaml

from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash
from contextlib import closing
from datetime import datetime, date
from PIL import Image
from werkzeug.utils import secure_filename

from helpers import allowed_file
from helpers import check_login


from . import app
from . import query_db
from . import IMAGE_FOLDER
from . import OFFICER_IMAGE_FOLDER
from . import ROOT
from . import secrets

img_formats = {
    'image/jpeg': 'JPEG',
    'image/png': 'PNG',
    'image/gif': 'GIF'
}


@app.route('/')
def show_latest_event():
    events = query_db('select title, time, location, link, image_url, unix_time from events order by unix_time desc')
    upcoming_events = filter(lambda e: e['unix_time'] > int(time.time()), events)
    if len(upcoming_events) == 0:
        upcoming_events.append(events[0])
    upcoming_events.sort(key=lambda e: e['unix_time'])
    return render_template('show_latest_event.html', event=upcoming_events[0])

@app.route('/add', methods=['POST'])
def add_event():
    check_login()
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
        payload = {"access_token": secrets['facebook']}
        res = requests.get(fb_api_base, params=payload).json()
        title = res['name']
        location = res['place']['name']
        time_str = res['start_time']
        # turns the ISO-8601 format time given to us into epoch time and a formatted string
        date_time = dateutil.parser.parse(time_str)
        time_str = date_time.strftime("%A %B %d %I:%M%p")
        unix_time = int(time.mktime(date_time.timetuple()) + date_time.microsecond/1000000.0)

        # another GET to get the cover photo..?
        payload = {"access_token": secrets['facebook'], "fields": "cover"}
        res = requests.get(fb_api_base, params=payload).json()
        image_url = res['cover']['source']
        image_data = urllib.urlopen(image_url)
        image_type = image_data.info().get('Content-Type')
        try:
            image_format = img_formats[image_type]
        except KeyError:
            raise ValueError('Not a supported image format')

        image_file = cStringIO.StringIO(image_data.read())
        image = Image.open(image_file)
        # should be random enough
        file_name = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(8))
        file_name += '.' + image_format
        image_url = os.path.join(IMAGE_FOLDER, file_name)
        image_path = os.path.join(ROOT, image_url)
        image.save(image_path, format=image_format)

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
    return redirect(url_for('show_latest_event'))

@app.route('/admin', methods=['GET'])
def admin_panel():
    check_login()
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
    check_login()

    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('admin_panel'))
    image = request.files['file']
    if image.filename == '':
        flash('No selected file')
        return redirect(url_for('admin_panel'))
    if not allowed_file(image.filename):
        flash('File extension not allowed. Must be jpg, png, or gif')
        return redirect(url_for('admin_panel'))

    filename = secure_filename(image.filename)
    image_url = os.path.join(OFFICER_IMAGE_FOLDER, filename)
    image_path = os.path.join(ROOT, image_url)
    image.save(image_path)

    name = request.form['name']
    year = request.form['year']
    major = request.form['major']
    position = request.form['position']
    quote = request.form['quote']
    description = request.form['description']
    href = '#' + request.form['name']

    query = 'insert into officers (name, year, major, quote, description, image_url, position, href)'\
            'values (?, ?, ?, ?, ?, ?, ?, ?)'
    g.db.execute(query, [name, year, major, quote, description, image_url, position, href])
    g.db.commit()
    return redirect(url_for('admin_panel'))

@app.route('/add_family', methods=['POST'])
def add_family():
    check_login()
    family_name = request.form['family_name']
    family_head1 = request.form['family_head1']
    family_head2 = request.form['family_head2']
    description = request.form['description']
    image_url = request.form['image_url']

    query = 'insert into families (family_name, family_head1, family_head2, description, image_url)'\
            'values (?, ?, ?, ?, ?)'
    g.db.execute(query, [family_name, family_head1, family_head2, description, image_url])
    g.db.commit()
    return redirect(url_for('admin_panel'))

@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html')

@app.route('/families', methods=['GET'])
def families():
    query = 'select family_name, family_head1, family_head2, description, image_url from families'
    families = query_db(query)
    return render_template('families.html', families=families)

@app.route('/files', methods=['GET'])
def files():
    return render_template('files.html')

@app.route('/donate', methods=['GET'])
def donate():
    return render_template('donate.html')
