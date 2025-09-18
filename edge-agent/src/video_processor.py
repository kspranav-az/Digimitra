
import os
import cv2
import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoProcessor:
    """
    Reads video files and provides frames for processing.
    """
    def __init__(self, video_path: str):
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            raise IOError(f"Cannot open video file: {video_path}")
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        logger.info(f"Opened video '{video_path}' with {self.fps:.2f} FPS.")

    def get_frames(self, sample_rate: int = 1):
        """
        Generator that yields frames from the video at a specified sample rate (in FPS).
        """
        frame_interval = int(self.fps / sample_rate)
        frame_count = 0
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                # Loop the video for continuous demo
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            
            if frame_count % frame_interval == 0:
                yield frame
            
            frame_count += 1

    def release(self):
        self.cap.release()

class HLSProcessor:
    """
    Uses ffmpeg to convert a video file into a looping HLS stream.
    """
    def __init__(self, video_path: str, hls_out_dir: str, camera_id: str):
        self.video_path = video_path
        self.hls_out_dir = os.path.join(hls_out_dir, camera_id)
        self.camera_id = camera_id
        os.makedirs(self.hls_out_dir, exist_ok=True)

    def start_streaming(self):
        """
        Starts an ffmpeg process to generate a live HLS stream from the video file.
        This will run indefinitely, looping the source video.
        """
        playlist_path = os.path.join(self.hls_out_dir, "live.m3u8")
        command = [
            'ffmpeg', '-re', '-stream_loop', '-1', '-i', self.video_path,
            '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23',
            '-c:a', 'aac', '-b:a', '128k',
            '-f', 'hls',
            '-hls_time', '4', # 4-second segments
            '-hls_list_size', '5', # Keep 5 segments in the playlist
            '-hls_flags', 'delete_segments', # Delete old segments
            playlist_path
        ]
        
        logger.info(f"Starting HLS streaming for camera '{self.camera_id}'...")
        # Run ffmpeg in the background
        subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logger.info(f"HLS stream for {self.camera_id} should be available at {playlist_path}")
