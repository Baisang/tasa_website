# Helper functions and stuff
import os
import random
import string
import time

import dateutil.parser
from flask import abort
from flask import session
from werkzeug.utils import secure_filename

from . import ROOT

ALLOWED_EXTENSIONS = set(['jpg', 'jpeg', 'gif', 'png'])

POSITIONS = [
    'President',
    'Internal Vice President',
    'External Vice President',
    'Treasurer',
    'Webmaster',
    'Outreach',
    'Public Relations',
    'Family Head',
    'Historian',
    'Senior Advisor',
    'Family Head Intern',
    'Historian Intern',
    'Public Relations Intern',
    'Outreach Intern',
    'Treasurer Intern',
    'Webmaster Intern',
]

img_formats = {
    'image/jpeg': 'JPEG',
    'image/png': 'PNG',
    'image/gif': 'GIF'
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_time(time_str):
    # turns the ISO-8601 format time given to us into epoch time and a formatted string
    date_time = dateutil.parser.parse(time_str)
    time_str = date_time.strftime("%A %B %d %I:%M%p")
    unix_time = int(time.mktime(date_time.timetuple()) + date_time.microsecond/1000000.0)
    return time_str, unix_time

def guess_image_extension(image):
    image_type = image.info().get('Content-Type')
    try:
        image_format = img_formats[image_type]
    except KeyError:
        raise ValueError('Not a supported image format')
    return image_format

def generate_random_filename(extension):
    file_name = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(8))
    file_name += '.' + extension
    return file_name

def create_image_paths(sub_root, file_name):
    image_url = os.path.join(sub_root, file_name)
    image_path = os.path.join(ROOT, image_url)
    return image_url, image_path

def file_from_request(request):
    if 'file' not in request.files:
        raise ValueError('No file attached')
    image = request.files['file']
    if image.filename == '':
        raise ValueError('Filename is empty')
    if not allowed_file(image.filename):
        raise ValueError('Not a supported image format')
    return image

def save_request_file(request, save_folder):
    image = file_from_request(request)
    filename = secure_filename(image.filename)
    image_url, image_path = create_image_paths(save_folder, filename)
    image.save(image_path)
    return image_url, image_path
