"""
Camera class for managing video sources and processing
OOP-oriented design for edge agent
"""
import os
import cv2
import time
from pathlib import Path
from typing import Iterator, Tuple, Optional
from dataclasses import dataclass
import logging

@dataclass
class CameraConfig:
    """Configuration for camera instances"""
    camera_id: str
    video_path: str
    fps: float = 30.0
    chunk_duration: int = 10  # seconds
    frame_skip: int = 15  # process every Nth frame for detection
    
class Camera:
    """OOP Camera class for video file processing as simulated camera feeds"""
    
    def __init__(self, config: CameraConfig):
        self.config = config
        self.camera_id = config.camera_id
        self.video_path = config.video_path
        self.fps = config.fps
        self.chunk_duration = config.chunk_duration
        self.frame_skip = config.frame_skip
        
        # Video capture objects
        self.cap = None
        self.frame_count = 0
        self.current_chunk_start_time = None
        self.is_active = False
        
        # Logging
        self.logger = logging.getLogger(f"Camera-{self.camera_id}")
        
        self._initialize_video()
    
    def _initialize_video(self) -> bool:
        """Initialize video capture from file"""
        try:
            if not os.path.exists(self.video_path):
                self.logger.error(f"Video file not found: {self.video_path}")
                return False
                
            self.cap = cv2.VideoCapture(self.video_path)
            if not self.cap.isOpened():
                self.logger.error(f"Cannot open video file: {self.video_path}")
                return False
            
            # Get video properties
            total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            video_fps = self.cap.get(cv2.CAP_PROP_FPS)
            duration = total_frames / video_fps if video_fps > 0 else 0
            
            self.logger.info(f"Initialized camera {self.camera_id}: {total_frames} frames, {video_fps:.2f} FPS, {duration:.2f}s duration")
            self.is_active = True
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing video: {e}")
            return False
    
    def get_frame(self) -> Optional[Tuple[bool, any]]:
        """Get next frame from video"""
        if not self.cap or not self.is_active:
            return None
            
        try:
            ret, frame = self.cap.read()
            if not ret:
                # Loop the video for continuous simulation
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()
                self.logger.info(f"Looped video for camera {self.camera_id}")
            
            if ret:
                self.frame_count += 1
                return ret, frame
            return None
            
        except Exception as e:
            self.logger.error(f"Error reading frame: {e}")
            return None
    
    def should_process_frame(self) -> bool:
        """Check if current frame should be processed for detection"""
        return self.frame_count % self.frame_skip == 0
    
    def get_frames_for_detection(self) -> Iterator[Tuple[any, float]]:
        """Generator that yields frames for AI detection processing"""
        while self.is_active:
            frame_data = self.get_frame()
            if frame_data is None:
                break
                
            ret, frame = frame_data
            if ret and self.should_process_frame():
                timestamp = time.time()
                yield frame, timestamp
            
            # Control frame rate
            time.sleep(1.0 / self.fps)
    
    def get_chunk_frames(self) -> Iterator[Tuple[any, float, bool]]:
        """Generator that yields frames for video chunk creation"""
        chunk_frame_count = 0
        chunk_frames_needed = int(self.fps * self.chunk_duration)
        
        while self.is_active:
            frame_data = self.get_frame()
            if frame_data is None:
                break
                
            ret, frame = frame_data
            if ret:
                timestamp = time.time()
                chunk_frame_count += 1
                
                # Check if chunk is complete
                is_chunk_end = chunk_frame_count >= chunk_frames_needed
                
                yield frame, timestamp, is_chunk_end
                
                if is_chunk_end:
                    chunk_frame_count = 0
            
            # Control frame rate
            time.sleep(1.0 / self.fps)
    
    def get_camera_metadata(self) -> dict:
        """Get camera metadata for database storage"""
        return {
            "camera_id": self.camera_id,
            "video_path": self.video_path,
            "fps": self.fps,
            "is_active": self.is_active,
            "frame_count": self.frame_count
        }
    
    def stop(self):
        """Stop camera and release resources"""
        self.is_active = False
        if self.cap:
            self.cap.release()
            self.logger.info(f"Camera {self.camera_id} stopped")
    
    def __del__(self):
        """Cleanup on destruction"""
        self.stop()

class CameraManager:
    """Manager class for multiple camera instances"""
    
    def __init__(self, video_directory: str):
        self.video_directory = Path(video_directory)
        self.cameras = {}
        self.logger = logging.getLogger("CameraManager")
        
        self._discover_cameras()
    
    def _discover_cameras(self):
        """Auto-discover cameras from video files in directory"""
        if not self.video_directory.exists():
            self.logger.warning(f"Video directory not found: {self.video_directory}")
            return
        
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv'}
        video_files = [f for f in self.video_directory.iterdir() 
                      if f.suffix.lower() in video_extensions]
        
        for video_file in video_files:
            # Create camera_id from filename
            camera_id = video_file.stem.replace(' ', '_').replace('-', '_')
            
            config = CameraConfig(
                camera_id=camera_id,
                video_path=str(video_file),
                fps=2.0,  # Reduced FPS for simulation
                chunk_duration=10,
                frame_skip=30  # Process every 30th frame for detection
            )
            
            camera = Camera(config)
            if camera.is_active:
                self.cameras[camera_id] = camera
                self.logger.info(f"Added camera: {camera_id}")
    
    def get_camera(self, camera_id: str) -> Optional[Camera]:
        """Get camera by ID"""
        return self.cameras.get(camera_id)
    
    def get_all_cameras(self) -> dict:
        """Get all active cameras"""
        return self.cameras
    
    def stop_all_cameras(self):
        """Stop all cameras"""
        for camera in self.cameras.values():
            camera.stop()
        self.logger.info("All cameras stopped")