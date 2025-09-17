"""
Video processing classes for AI detection and chunk management
OOP-oriented design for edge agent
"""
import cv2
import numpy as np
import torch
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import tempfile
import os

@dataclass
class DetectionResult:
    """Structure for detection results"""
    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x, y, width, height
    timestamp: datetime
    frame_data: Optional[np.ndarray] = None

@dataclass
class VideoChunk:
    """Structure for video chunks"""
    camera_id: str
    start_time: datetime
    end_time: datetime
    frames: List[np.ndarray]
    frame_timestamps: List[datetime]
    file_path: Optional[str] = None

class VideoProcessor:
    """OOP Video processor for creating chunks and managing video data"""
    
    def __init__(self, camera_id: str, chunk_duration: int = 10):
        self.camera_id = camera_id
        self.chunk_duration = chunk_duration
        self.current_chunk_frames = []
        self.current_chunk_timestamps = []
        self.chunk_start_time = None
        self.logger = logging.getLogger(f"VideoProcessor-{camera_id}")
        
        # Video encoding settings
        self.fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.fps = 30.0
    
    def add_frame(self, frame: np.ndarray, timestamp: datetime) -> Optional[VideoChunk]:
        """Add frame to current chunk, return chunk if complete"""
        
        # Initialize chunk if needed
        if self.chunk_start_time is None:
            self.chunk_start_time = timestamp
            self.current_chunk_frames = []
            self.current_chunk_timestamps = []
        
        self.current_chunk_frames.append(frame.copy())
        self.current_chunk_timestamps.append(timestamp)
        
        # Check if chunk is complete
        elapsed = timestamp - self.chunk_start_time
        if elapsed.total_seconds() >= self.chunk_duration:
            return self._finalize_chunk()
        
        return None
    
    def _finalize_chunk(self) -> VideoChunk:
        """Finalize current chunk and prepare for next"""
        if not self.current_chunk_frames:
            return None
            
        chunk = VideoChunk(
            camera_id=self.camera_id,
            start_time=self.chunk_start_time,
            end_time=self.current_chunk_timestamps[-1],
            frames=self.current_chunk_frames.copy(),
            frame_timestamps=self.current_chunk_timestamps.copy()
        )
        
        self.logger.info(f"Finalized chunk: {len(self.current_chunk_frames)} frames, "
                        f"{(chunk.end_time - chunk.start_time).total_seconds():.2f}s")
        
        # Reset for next chunk
        self.chunk_start_time = None
        self.current_chunk_frames = []
        self.current_chunk_timestamps = []
        
        return chunk
    
    def save_chunk_to_file(self, chunk: VideoChunk, output_dir: str) -> str:
        """Save video chunk to MP4 file"""
        if not chunk.frames:
            raise ValueError("Cannot save empty chunk")
        
        # Generate filename
        timestamp_str = chunk.start_time.strftime("%Y%m%d_%H%M%S")
        filename = f"{self.camera_id}_{timestamp_str}.mp4"
        output_path = os.path.join(output_dir, filename)
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Get frame dimensions
        height, width = chunk.frames[0].shape[:2]
        
        # Create video writer
        writer = cv2.VideoWriter(output_path, self.fourcc, self.fps, (width, height))
        
        try:
            for frame in chunk.frames:
                writer.write(frame)
            
            self.logger.info(f"Saved chunk to: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error saving chunk: {e}")
            raise
        finally:
            writer.release()
    
    def create_thumbnail(self, frame: np.ndarray, bbox: Tuple[int, int, int, int]) -> np.ndarray:
        """Create thumbnail from frame and bounding box"""
        x, y, w, h = bbox
        
        # Ensure bounding box is within frame bounds
        height, width = frame.shape[:2]
        x = max(0, min(x, width - 1))
        y = max(0, min(y, height - 1))
        w = max(1, min(w, width - x))
        h = max(1, min(h, height - y))
        
        # Extract region of interest
        roi = frame[y:y+h, x:x+w]
        
        # Resize to standard thumbnail size
        thumbnail_size = (224, 224)
        thumbnail = cv2.resize(roi, thumbnail_size)
        
        return thumbnail
    
    def force_chunk_completion(self) -> Optional[VideoChunk]:
        """Force completion of current chunk (for shutdown)"""
        if self.current_chunk_frames:
            return self._finalize_chunk()
        return None

class HLSProcessor:
    """Processor for creating HLS (HTTP Live Streaming) segments"""
    
    def __init__(self, camera_id: str, output_dir: str):
        self.camera_id = camera_id
        self.output_dir = output_dir
        self.segment_duration = 6  # seconds per HLS segment
        self.logger = logging.getLogger(f"HLSProcessor-{camera_id}")
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
    
    def process_chunk_to_hls(self, chunk: VideoChunk) -> Dict[str, str]:
        """Convert video chunk to HLS segments and playlist"""
        try:
            # Save chunk as temporary MP4
            temp_mp4 = os.path.join(self.output_dir, f"temp_{self.camera_id}.mp4")
            
            # Create VideoWriter for temporary file
            if not chunk.frames:
                return {}
            
            height, width = chunk.frames[0].shape[:2]
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(temp_mp4, fourcc, 30.0, (width, height))
            
            for frame in chunk.frames:
                writer.write(frame)
            writer.release()
            
            # Generate HLS playlist and segments using FFmpeg
            playlist_name = f"{self.camera_id}.m3u8"
            playlist_path = os.path.join(self.output_dir, playlist_name)
            
            # FFmpeg command for HLS generation
            import subprocess
            cmd = [
                'ffmpeg', '-y',  # overwrite output
                '-i', temp_mp4,
                '-f', 'hls',
                '-hls_time', str(self.segment_duration),
                '-hls_list_size', '10',
                '-hls_flags', 'delete_segments',
                playlist_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info(f"Created HLS playlist: {playlist_path}")
                
                # Clean up temporary file
                if os.path.exists(temp_mp4):
                    os.remove(temp_mp4)
                
                return {
                    "playlist_path": playlist_path,
                    "playlist_name": playlist_name
                }
            else:
                self.logger.error(f"FFmpeg error: {result.stderr}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error creating HLS: {e}")
            return {}

class FrameExtractor:
    """Utility class for extracting specific frames from video chunks"""
    
    @staticmethod
    def extract_frames_at_timestamps(chunk: VideoChunk, 
                                   target_timestamps: List[datetime]) -> List[np.ndarray]:
        """Extract frames at specific timestamps from chunk"""
        extracted_frames = []
        
        for target_time in target_timestamps:
            # Find closest frame to target timestamp
            closest_idx = 0
            min_diff = abs((chunk.frame_timestamps[0] - target_time).total_seconds())
            
            for i, frame_time in enumerate(chunk.frame_timestamps):
                diff = abs((frame_time - target_time).total_seconds())
                if diff < min_diff:
                    min_diff = diff
                    closest_idx = i
            
            if closest_idx < len(chunk.frames):
                extracted_frames.append(chunk.frames[closest_idx])
        
        return extracted_frames
    
    @staticmethod
    def extract_middle_frame(chunk: VideoChunk) -> Optional[np.ndarray]:
        """Extract middle frame from chunk"""
        if not chunk.frames:
            return None
        
        middle_idx = len(chunk.frames) // 2
        return chunk.frames[middle_idx]