# Helper functions and stuff

ALLOWED_EXTENSIONS = set(['jpg', 'jpeg', 'gif', 'png'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
