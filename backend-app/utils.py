
import random
import string
allowed_extensions = {'mp4', 'avi', 'mov', 'mkv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

# 8 digit is enough
def generate_job_id():
    return "job-" + ''.join(random.choice(string.digits) for _ in range(8))

def generate_file_id():
    return "f-" + ''.join(random.choice(string.digits) for _ in range(8)) #file id

