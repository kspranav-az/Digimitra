"""
Edge Agent Orchestrator - Connects all components for end-to-end pipeline
"""
import os
import sys
import time
import logging
import threading
from datetime import datetime
from typing import Dict, Any
import uuid

# Add API source to path for service imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../../api/src'))

from camera import CameraManager
from video_processor import VideoProcessor, HLSProcessor
from event_detector import EventDetector
from storage_service import MinIOStorageService
from streaming_service import RedpandaStreamingService
from vector_service import MilvusVectorService

class EdgeOrchestrator:
    """Main orchestrator for edge agent processing pipeline"""
    
    def __init__(self, video_directory: str = "/data/videos"):
        self.video_directory = video_directory
        self.logger = logging.getLogger("EdgeOrchestrator")
        self.shutdown_flag = threading.Event()
        
        # Initialize services
        self.storage_service = MinIOStorageService()
        self.streaming_service = RedpandaStreamingService()
        
        # Initialize camera manager
        self.camera_manager = CameraManager(video_directory)
        
        # Initialize processing components per camera
        self.video_processors = {}
        self.event_detectors = {}
        self.hls_processors = {}
        
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize processing components for each camera"""
        
        for camera_id, camera in self.camera_manager.get_all_cameras().items():
            # Video processor for chunks
            self.video_processors[camera_id] = VideoProcessor(
                camera_id=camera_id,
                chunk_duration=10
            )
            
            # Event detector for AI processing
            self.event_detectors[camera_id] = EventDetector(
                camera_id=camera_id,
                config={
                    "confidence_threshold": 0.5,
                    "target_classes": ["person", "car", "bicycle", "motorcycle"]
                }
            )
            
            # HLS processor for streaming
            hls_output_dir = os.environ.get("HLS_OUT_DIR", "/hls")
            self.hls_processors[camera_id] = HLSProcessor(
                camera_id=camera_id,
                output_dir=hls_output_dir
            )
            
            self.logger.info(f"Initialized components for camera: {camera_id}")
    
    def start_processing(self):
        """Start processing all cameras"""
        
        self.logger.info("Starting edge processing...")
        
        for camera_id, camera in self.camera_manager.get_all_cameras().items():
            # Start processing thread for each camera
            thread = threading.Thread(
                target=self._process_camera,
                args=(camera_id, camera),
                daemon=True
            )
            thread.start()
            self.logger.info(f"Started processing thread for camera: {camera_id}")
        
        # Wait for shutdown signal
        try:
            self.shutdown_flag.wait()
        except KeyboardInterrupt:
            self.logger.info("Received shutdown signal")
        
        self.stop_processing()
    
    def _process_camera(self, camera_id: str, camera):
        """Process video from single camera"""
        
        video_processor = self.video_processors[camera_id]
        event_detector = self.event_detectors[camera_id]
        hls_processor = self.hls_processors[camera_id]
        
        self.logger.info(f"Processing camera: {camera_id}")
        
        try:
            for frame, timestamp in camera.get_frames_for_detection():
                if self.shutdown_flag.is_set():
                    break
                
                # Convert timestamp to datetime
                frame_time = datetime.fromtimestamp(timestamp)
                
                # Add frame to video processor
                completed_chunk = video_processor.add_frame(frame, frame_time)
                
                # Process completed chunks
                if completed_chunk:
                    self._process_completed_chunk(camera_id, completed_chunk, hls_processor)
                
                # Run AI detection on frame
                event_detections = event_detector.process_frame(frame)
                
                # Process detections
                for event_detection in event_detections:
                    self._process_event_detection(
                        camera_id=camera_id,
                        event_detection=event_detection,
                        chunk_id=getattr(completed_chunk, 'chunk_id', None) if completed_chunk else None
                    )
                
                # Small delay to control processing rate
                time.sleep(0.1)
                
        except Exception as e:
            self.logger.error(f"Error processing camera {camera_id}: {e}")
        
        self.logger.info(f"Stopped processing camera: {camera_id}")
    
    def _process_completed_chunk(self, camera_id: str, chunk, hls_processor):
        """Process completed video chunk"""
        
        try:
            # Save chunk to temporary file
            import tempfile
            import cv2
            
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
                # Create video writer
                if chunk.frames:
                    height, width = chunk.frames[0].shape[:2]
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    writer = cv2.VideoWriter(temp_file.name, fourcc, 30.0, (width, height))
                    
                    for frame in chunk.frames:
                        writer.write(frame)
                    
                    writer.release()
                    
                    # Read video data
                    with open(temp_file.name, 'rb') as f:
                        video_data = f.read()
                    
                    # Upload to MinIO
                    minio_key = self.storage_service.upload_video_chunk(
                        camera_id=camera_id,
                        chunk_data=video_data,
                        timestamp=chunk.start_time,
                        metadata={
                            "duration_seconds": (chunk.end_time - chunk.start_time).total_seconds(),
                            "frame_count": len(chunk.frames),
                            "resolution": f"{width}x{height}"
                        }
                    )
                    
                    if minio_key:
                        # Create HLS segments
                        hls_info = hls_processor.process_chunk_to_hls(chunk)
                        
                        # Publish chunk metadata to Kafka
                        chunk_metadata = {
                            "chunk_id": str(uuid.uuid4()),
                            "camera_id": camera_id,
                            "start_time": chunk.start_time.isoformat(),
                            "end_time": chunk.end_time.isoformat(),
                            "duration_seconds": (chunk.end_time - chunk.start_time).total_seconds(),
                            "minio_key": minio_key,
                            "hls_playlist_key": hls_info.get("playlist_name"),
                            "file_size_bytes": len(video_data),
                            "frame_count": len(chunk.frames)
                        }
                        
                        self.streaming_service.publish_chunk_metadata(
                            camera_id=camera_id,
                            chunk_metadata=chunk_metadata
                        )
                        
                        self.logger.info(f"Processed chunk: {minio_key}")
                    
                    # Cleanup temp file
                    os.unlink(temp_file.name)
                
        except Exception as e:
            self.logger.error(f"Error processing chunk: {e}")
    
    def _process_event_detection(self, camera_id: str, event_detection, chunk_id: str = None):
        """Process AI event detection"""
        
        try:
            detection = event_detection.detection
            
            # Generate unique IDs
            event_id = str(uuid.uuid4())
            embedding_id = str(uuid.uuid4())
            
            # Upload thumbnail to MinIO
            import cv2
            thumbnail_key = None
            if event_detection.thumbnail is not None:
                # Encode thumbnail as JPEG
                _, thumbnail_data = cv2.imencode('.jpg', event_detection.thumbnail)
                thumbnail_bytes = thumbnail_data.tobytes()
                
                thumbnail_key = self.storage_service.upload_thumbnail(
                    camera_id=camera_id,
                    thumbnail_data=thumbnail_bytes,
                    event_id=event_id,
                    timestamp=detection.timestamp
                )
            
            # Publish event to Kafka
            event_data = {
                "event_id": event_id,
                "camera_id": camera_id,
                "chunk_id": chunk_id,
                "event_type": detection.class_name,
                "confidence": detection.confidence,
                "timestamp": detection.timestamp.isoformat(),
                "bounding_box": {
                    "x": detection.bbox[0],
                    "y": detection.bbox[1], 
                    "width": detection.bbox[2],
                    "height": detection.bbox[3]
                },
                "thumbnail_key": thumbnail_key,
                "embedding_id": embedding_id,
                "severity": event_detection.severity,
                "metadata": {
                    "frame_shape": detection.frame_shape
                }
            }
            
            self.streaming_service.publish_event(
                camera_id=camera_id,
                event_data=event_data
            )
            
            # Publish embedding to Kafka
            if event_detection.embedding is not None:
                embedding_data = {
                    "embedding_id": embedding_id,
                    "event_id": event_id,
                    "camera_id": camera_id,
                    "timestamp": detection.timestamp.isoformat(),
                    "event_type": detection.class_name,
                    "confidence": detection.confidence,
                    "embedding": event_detection.embedding.tolist()
                }
                
                self.streaming_service.publish_embedding(
                    camera_id=camera_id,
                    embedding_data=embedding_data
                )
            
            self.logger.info(f"Processed event: {event_id}, type: {detection.class_name}")
            
        except Exception as e:
            self.logger.error(f"Error processing event detection: {e}")
    
    def stop_processing(self):
        """Stop all processing"""
        
        self.logger.info("Stopping edge processing...")
        self.shutdown_flag.set()
        
        # Stop all cameras
        self.camera_manager.stop_all_cameras()
        
        # Stop streaming service
        self.streaming_service.stop_all_consumers()
        
        self.logger.info("Edge processing stopped")

def main():
    """Main entry point for edge agent"""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get video directory from environment
    video_dir = os.environ.get("VIDEO_DIR", "/data/videos")
    
    # Create and start orchestrator
    orchestrator = EdgeOrchestrator(video_directory=video_dir)
    orchestrator.start_processing()

if __name__ == "__main__":
    main()