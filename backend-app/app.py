from flask import Flask, request, jsonify
import requests
from werkzeug.utils import secure_filename
from config import config, DevConfig
import os
from video_utils import extract_frames_sample, frame_to_base64, save_frames, crop_frames, outline_frames
from ai_utils import describe_scene_with_gpt_vision
from utils import allowed_file, generate_job_id
from job import Job
from redis_client import get_job_status
import logging
import openai
from threading import Thread
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room



logging.basicConfig(level=logging.INFO) 
UPLOAD_FOLDER = config['dev'].UPLOAD_FOLDER
OPENAI_KEY = config['dev'].OPENAI_KEY

app = Flask(__name__)

CORS(app, supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins="*")
def create_app(app_environment=None):
    global UPLOAD_FOLDER
    global OPENAI_KEY
    if app_environment is None:
        # default is dev
        UPLOAD_FOLDER = config['dev'].UPLOAD_FOLDER
        OPENAI_KEY = config['dev'].OPENAI_KEY
    else:
        UPLOAD_FOLDER = config[app_environment].UPLOAD_FOLDER
        OPENAI_KEY = config[app_environment].OPENAI_KEY
    
    openai.api_key = UPLOAD_FOLDER
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)


if __name__ == "__main__":
    create_app()
    socketio.run(app, debug=True, host='0.0.0.0', port=8080)


def process_job(job, video_url=None, video_path=None):
    """
    Start async process job, use video path first
    """
    if video_path:
        job.run_analysis(video_path)
    elif video_url:
        video_path = job.download_video(video_url)
        job.run_analysis(video_path)
    
    return True

@app.route("/")
def home():
    return "Hello, world!"

# web socket
@socketio.on('connect')
def handle_connect():
    sid = request.sid
    join_room(sid)
    print(f"Client connected: {sid}")
    emit('connected', {"sid": sid, "message": "You are now connected."}, room=sid)
    
@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    leave_room(sid)
    print(f"Client disconnected: {sid}")

@socketio.on('subscribe')
def handle_subscribe(data):
    sid = data.get('sid')
    if sid:
        join_room(sid)
        emit('subscribed', {"message": f"Subscribed to job room {sid}"}, room=sid)
        print(f"Client subscribed to room: {sid}")


@app.route("/run_job", methods=['POST'])
def run_job():
    video_file = request.files.get("video")
    video_url = request.form.get("videoUrl")
    sid = request.form.get("sid") # sending msg to socket sid


    if not video_file and not video_url:
        return jsonify({"error": "No video file or URL provided"}), 400
    
    if not sid:
        return jsonify({"error": "No socket found"}), 400
    
    job_id = generate_job_id()
    upload_folder = UPLOAD_FOLDER
    openai_key = OPENAI_KEY

    # init the job
    job = Job(job_id, sid, socketio, upload_folder, logging, openai_key)

    # store the video if file present （not async here）
    video_path = None 
    if video_file:
        video_path = job.upload_video(video_file)
    
    # thread = Thread(target=process_job, args=(job, video_url, video_path))
    # thread.start()
    # process_job(job, video_url, video_path)
    socketio.start_background_task(target=process_job, job=job, video_url=video_url, video_path=video_path)

    # return this immediately start the streaming
    return jsonify({"job_id": job_id, "action": "run job", "sid": sid}), 202 

