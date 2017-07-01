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

def create_file_paths(sub_root, file_name):
    file_url = os.path.join(sub_root, file_name)
    file_path = os.path.join(ROOT, file_url)
    return file_url, file_path

def file_from_request(request):
    if 'file' not in request.files:
        raise ValueError('No file attached')
    request_file = request.files['file']
    if request_file.filename == '':
        raise ValueError('Filename is empty')
    if not allowed_file(request_file.filename):
        raise ValueError('Not a supported image format')
    return request_file

def save_request_file(request, save_folder):
    f = file_from_request(request)
    filename = secure_filename(f.filename)
    f_url, f_path = create_image_paths(save_folder, filename)
    f.save(f_path)
    return f_url

def check_file_in_request(request):
    return 'file' in request.files and request.files['file'].filename != ''
