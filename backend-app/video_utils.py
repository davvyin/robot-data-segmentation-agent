import cv2
import os
from moviepy.editor import VideoFileClip
import numpy as np
import base64


def split_video_intervals(video_path, clip_duration=5, overlap=2):
    # split the clip into multiple segments, return the times
    clip = VideoFileClip(video_path)
    duration = int(clip.duration)
    segments = []
    start = 0
    while start < duration:
        end = min(start + clip_duration, duration)
        segments.append((start, end))
        start += clip_duration - overlap
    return segments


def save_frames(frames, output_dir="sampled_frames"):
    os.makedirs(output_dir, exist_ok=True)
    for timestamp, frame in frames:
        mmss = f"{int(timestamp // 60):02d}{int(timestamp % 60):02d}"
        filename = os.path.join(output_dir, f"frame_{mmss}.jpg")
        cv2.imwrite(filename, frame)


def extract_keyframes_by_diff(video_path, threshold=2):
    # try to find the key scene changes
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_id = 0
    last_frame = None
    keyframes = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if last_frame is not None:
            diff = cv2.absdiff(last_frame, gray)
            score = np.mean(diff)
            if score > threshold:
                timestamp = frame_id / fps
                keyframes.append((timestamp, frame.copy()))
        last_frame = gray
        frame_id += 1
    cap.release()
    print("total frame", frame_id)
    return keyframes


def extract_frames_sample(video_path, n_frames=None, persistant_diff=False):
    # sample frames with fix intervals
    # n_frames: how many sampled frames

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps
    
    # default n seconds frames
    if not n_frames:
        n_frames = int(duration)
    interval = total_frames // n_frames
    frames = []
    last_frame = None
    timestamp = 0
    frame_id = 0
    
    last_frame_gray = None
    persistent_overlay = None
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        timestamp = frame_id / fps
        
        last_frame = frame.copy()
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        overlay = frame.copy()
        
        if persistant_diff:
            if last_frame_gray is not None:
                diff = cv2.absdiff(last_frame_gray, gray_frame)
                _, diff = cv2.threshold(diff, 50, 255, cv2.THRESH_BINARY)

                if persistent_overlay is None:
                    persistent_overlay = np.zeros_like(diff)
                
                persistent_overlay = cv2.bitwise_or(persistent_overlay, diff)

                overlay = frame.copy()
                overlay[persistent_overlay > 0] = (0, 0, 255)
            else:
                overlay = frame.copy()
                persistent_overlay = np.zeros_like(gray_frame)
        
        # sampled frame
        if not frame_id % interval:
            last_frame_gray = gray_frame.copy()
            frames.append((timestamp, overlay))
            # reset the grey frame for the window
            persistent_overlay = np.zeros_like(gray_frame)
        
        frame_id += 1

    if (frames and frames[-1] != last_frame) or not frames:
        frames.append((timestamp, last_frame))
    cap.release()
    return frames

def crop_frame(frame, x, y, width, height):
    # crop the image
    return frame[y : y + height, x : x + width]

def outline_frame(frame, x, y, width, height, label=None, color=(0, 0, 255), thickness=2):
    cv2.rectangle(frame, (x, y), (x + width, y + height), color, thickness)
    if label:
        cv2.putText(frame, label, (x + 5, y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    return frame

def crop_frames(frames, x, y, width, height):
    new_frames = []
    for timestamp, frame in frames:
        new_frames.append((timestamp, crop_frame(frame, x, y, width, height)))
    return new_frames

def outline_frames(frames, x, y, width, height, label=None, color=(0, 0, 255), thickness=2):
    new_frames = []
    for timestamp, frame in frames:
        new_frames.append((timestamp, outline_frame(frame, x, y, width, height, label, color, thickness)))
    return new_frames
    
def frame_to_base64(frame):
    _, buffer = cv2.imencode(".jpg", frame)
    b64 = base64.b64encode(buffer).decode("utf-8")
    return b64
