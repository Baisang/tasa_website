import cStringIO
import os
import random
import re
import requests
import string
import sqlite3
import time
import urllib
import yaml

from flask import Flask
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from PIL import Image
from werkzeug.utils import secure_filename

import auth
import fb_events
import helpers

from . import app
from . import FAMILY_IMAGE_FOLDER
from . import IMAGE_FOLDER
from . import OFFICER_IMAGE_FOLDER
from . import ROOT
from . import query_db

# This is kind of backwards, it's rendering a smaller template first that is
# part of the larger index version. Should fix soon.
@app.route('/')
def index():
    events = query_db('select title, time, location, link, image_url, unix_time from events order by unix_time desc')
    upcoming_events = filter(lambda e: e['unix_time'] > int(time.time()), events)
    if len(upcoming_events) == 0:
        upcoming_events.append(events[0])
    upcoming_events.sort(key=lambda e: e['unix_time'])
    return render_template('show_latest_event.html', event=upcoming_events[0])

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
            upcoming.append(event)
        else:
            recent.append(event)
    return render_template('events.html', recent=recent, upcoming=upcoming)

@app.route('/events', methods=['POST'])
def add_event():
    auth.check_login()
    try:
        url = request.form['link']
        # Facebook event url example:
        # https://www.facebook.com/events/1201801539835081/
        # Match the numbers between /s
        fb_event_id = re.match(r'.*/([0-9]+)/?$', url)
        if fb_event_id:
            fb_event_id = fb_event_id.group(1)
        else:
            raise Exception('Bad URL')

        res = fb_events.get_event(fb_event_id)

        title = res['name']
        location = res['place']['name']

        time_str, unix_time = helpers.convert_time(res['start_time'])

        # another GET to get the cover photo
        image_data = fb_events.get_cover_photo(fb_event_id)
        image_format = helpers.guess_image_extension(image_data)

        image_file = cStringIO.StringIO(image_data.read())
        image = Image.open(image_file)
        file_name = helpers.generate_random_filename(image_format)
        image_url, image_path = helpers.create_image_paths(IMAGE_FOLDER, file_name)
        image.save(image_path, format=image_format)

        query = 'insert into events (title, time, location, link, image_url, unix_time)'\
                'values (?, ?, ?, ?, ?, ?)'

        query_db(query, [title, time_str, location, url, image_url, unix_time])
        flash('New event was successfully posted')
        return redirect(url_for('admin_panel'))
    except Exception as e:
        flash('Exception: ' + str(e))
        return redirect(url_for('admin_panel'))

@app.route('/admin', methods=['GET'])
def admin_panel():
    auth.check_login()
    events = query_db('select title from events order by unix_time desc')
    officers = query_db('select name from officers order by id')
    return render_template('admin.html', events=events, officers=officers)

@app.route('/officers', methods=['GET'])
def officer_list():
    query = 'select * from officers order by id'
    officers = query_db(query)
    return render_template('officers.html', officers=officers)

@app.route('/add_officer', methods=['POST'])
def add_officer():
    auth.check_login()

    try:
        image = helpers.file_from_request(request)
    except ValueError as e:
        flash('Exception: ' + str(e))
        return redirect(url_for('admin_panel'))

    filename = secure_filename(image.filename)
    image_url, image_path = helpers.create_image_paths(OFFICER_IMAGE_FOLDER, filename)
    image.save(image_path)

    name = request.form['name']
    year = request.form['year']
    major = request.form['major']
    position = request.form['position']
    quote = request.form['quote']
    description = request.form['description']
    # TODO: this doesn't need to be part of the model
    href = '#' + request.form['name']

    query = 'insert into officers (name, year, major, quote, description, image_url, position, href)'\
            'values (?, ?, ?, ?, ?, ?, ?, ?)'
    g.db.execute(query, [name, year, major, quote, description, image_url, position, href])
    g.db.commit()
    flash('New officer successfully posted')
    return redirect(url_for('admin_panel'))

@app.route('/add_family', methods=['POST'])
def add_family():
    auth.check_login()

    try:
        image = helpers.file_from_request(request)
    except ValueError as e:
        flash('Exception: ' + str(e))
        return redirect(url_for('admin_panel'))

    filename = secure_filename(image.filename)
    image_url, image_path = helpers.create_image_paths(FAMILY_IMAGE_FOLDER, filename)
    image.save(image_path)

    family_name = request.form['family_name']
    family_head1 = request.form['family_head1']
    family_head2 = request.form['family_head2']
    description = request.form['description']

    query = 'insert into families (family_name, family_head1, family_head2, description, image_url)'\
            'values (?, ?, ?, ?, ?)'
    g.db.execute(query, [family_name, family_head1, family_head2, description, image_url])
    g.db.commit()
    flash('New family successfully posted')
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
