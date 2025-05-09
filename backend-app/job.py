import utils
import requests
import os
import json
from enum import Enum
from redis_client import update_job_status, update_job_result, init_job
from video_utils import extract_frames_sample, outline_frames, crop_frames, save_frames, frame_to_base64
from ai_utils import describe_scene_with_gpt_vision
from flask_socketio import SocketIO, emit

class JobStatus(Enum):
    Pending = "pending"
    Processing = "processing"
    Complete = "completed"
    Error = "failed"

class JobStage(Enum):
    Upload = "upload_status"
    Download = "download_status"
    Analysis = "analysis_status"

class Job():
    def __init__(self, job_id, sid, socketio, upload_folder, logger, openai_key):
        self.job_id = job_id
        self.sid = sid
        self.upload_folder = upload_folder
        self.socketio = socketio
        self.openai_key = openai_key
        # self.upload_status = JobStatus.Pending
        # self.analysis_status = JobStatus.Pending
        self.filename = None
        self.error = None
        self.logger = logger 
        init_job(job_id)
        
    def _update_status(self, stage, status, error=None, filename=None):
        """
        Update to redis and emit
        """
        update_job_status(self.job_id, stage, status, error=error, filename=filename)
        self.socketio.emit('job_update', {
            "job_id": self.job_id,
            "stage": stage,
            "status": status,
            "error": error,
            "filename": filename
        }, room=self.sid)
        
    def _update_result(self, result):
        """
        Update to redis and emit the result
        """
        update_job_result(self.job_id, result)
        self.socketio.emit('job_done', {
            "job_id": self.job_id,
            "result": result
        }, room=self.sid)
    
    def download_video(self, video_url):
        """
        Handle video processing
        """
        try:
            self.filename = f"{self.job_id}-{video_url.split('/')[-1]}"
            video_path = os.path.join(self.upload_folder, self.filename)
            self._update_status(JobStage.Download.value, JobStatus.Processing.value, filename=self.filename)
            self.socketio.sleep(0.1)
            with requests.get(video_url, stream=True) as r:
                r.raise_for_status()
                with open(video_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            self.socketio.sleep(0.1)
            self._update_status(JobStage.Download.value, JobStatus.Complete.value, filename=self.filename)
        
            return video_path

        except Exception as e:
            self.error = str(e)
            self._update_status(JobStage.Upload.value, JobStatus.Error.value, error=self.error)
            self.logger.error(f"Download failed for job {self.job_id}: {self.error}")
            return None

    def upload_video(self, video_file):
        """
        Cannot run this async
        """
        
        try:
            self._update_status(JobStage.Upload.value, JobStatus.Processing.value)
            self.filename = f"{self.job_id}-{video_file.filename}"
            video_path = os.path.join(self.upload_folder, self.filename)
            video_file.save(video_path)
            self._update_status(JobStage.Upload.value, JobStatus.Complete.value, filename=self.filename)
            return video_path
        except Exception as e:
            self.error = str(e)
            self._update_status(JobStage.Upload.value, JobStatus.Error.value, error=self.error)
            self.logger.error(f"Upload failed for job {self.job_id}: {self.error}")
            return None
        
    def run_analysis(self, video_path):
        """
        Performs the analysis
        """
        try:
            self._update_status(JobStage.Analysis.value, JobStatus.Processing.value)
            self.socketio.sleep(0.1)
            # self.socketio.sleep(5)
            # Sampling the frames
            frames = extract_frames_sample(video_path)
            height, width, _ = frames[0][1].shape
            segment_width = width // 4

            # Anotate the frames
            frames = outline_frames(frames, 0, 0, segment_width, height, label="Top-down")
            frames = outline_frames(frames, segment_width, 0, segment_width, height, label="Side View")
            frames = crop_frames(frames, 0, 0, 2 * segment_width, height)
            # save_frames(frames)

            # Convert frames to (ts, base64)
            data = [(ts, frame_to_base64(f)) for ts, f in frames]
            
            # Feed into the gpt
            res = describe_scene_with_gpt_vision(data, self.openai_key)
            # Parse the response
            parsed = None
            try:
                parsed = json.loads(res)
            except json.JSONDecodeError:
                parsed = None
            
            self.socketio.sleep(0.1)
            self._update_status(JobStage.Analysis.value, JobStatus.Complete.value)
            self._update_result(parsed)

        except Exception as e:
            self.error = str(e)
            self._update_status(JobStage.Analysis.value, JobStatus.Error.value, error=self.error)
            self.logger.error(f"Analysis failed for job {self.job_id}: {self.error}")
    
