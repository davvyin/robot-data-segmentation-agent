from flask import Flask, request, jsonify
from config import config
import os
from video_utils import extract_frames_sample, frame_to_base64, save_frames, crop_frames, outline_frames
from ai_utils import describe_scene_with_gpt_vision
import openai
import json


app = Flask(__name__)


@app.route("/")
def home():
    return "Hello, world!"


@app.route("/upload", methods=["POST"])
def upload():
    print("uploading")
    if "video" not in request.files:
        return jsonify({"error": "No video file uploaded"}), 400

    video = request.files["video"]
    video_path = os.path.join(app.config["UPLOAD_FOLDER"], video.filename)
    video.save(video_path)

    frames = extract_frames_sample(video_path, 10)  # making the snapshot [(ts, frame)]
    height, width, _ = frames[0][1].shape
    segment_width = width // 4


    frames = outline_frames(frames, 0, 0, segment_width, height, label="Top-down")
    frames = outline_frames(frames, segment_width, 0, segment_width, height, label="Side View")
    frames = outline_frames(frames, segment_width * 2, 0, segment_width, height, label="Arm 1")
    frames = outline_frames(frames, segment_width * 3, 0, segment_width, height, label="Arm 2")
    
    save_frames(frames)

    data = [(ts, frame_to_base64(f)) for ts, f in frames]

    res = describe_scene_with_gpt_vision(data)
    print(res)
    parsed = None
    try:
        parsed = json.loads(res)
    except json.JSONDecodeError:
        parsed = None
    print(parsed, "response")

    return jsonify({"segments": parsed})


def create_app(app_environment=None):
    if app_environment is None:
        # default is dev
        app.config.from_object(config["dev"])
    else:
        app.config.from_object(config[app_environment])
    UPLOAD_FOLDER = app.config["UPLOAD_FOLDER"]
    openai.api_key = app.config["OPENAI_KEY"]
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)


if __name__ == "__main__":
    create_app()
    app.run(debug=True)
