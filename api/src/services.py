"""
Integrated services for AI surveillance system
Combining all service components
"""
import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from storage_service import MinIOStorageService
from streaming_service import RedpandaStreamingService
from vector_service import MilvusVectorService
from database import get_db_session
from models import Camera, Event, VideoChunk, EmbeddingMetadata

class SurveillanceServices:
    """Main service orchestrator for AI surveillance system"""
    
    def __init__(self):
        self.logger = logging.getLogger("SurveillanceServices")
        
        # Service instances (initialized lazily)
        self.storage = None
        self.streaming = None
        self.vector_db = None
        
        # Service status tracking
        self._initialized = False
        self._consumers_started = False
    
    def initialize_services(self) -> bool:
        """Initialize all services - called during FastAPI startup"""
        
        if self._initialized:
            return True
        
        try:
            self.logger.info("Initializing surveillance services...")
            
            # Initialize services with error handling
            self.storage = MinIOStorageService()
            self.streaming = RedpandaStreamingService()
            self.vector_db = MilvusVectorService()
            
            # Verify services are working
            services_status = {
                "storage": self.storage.health_check() if self.storage else False,
                "streaming": self.streaming.health_check() if self.streaming else False,
                "vector_db": self.vector_db.health_check() if self.vector_db else False
            }
            
            # Log service status
            for service, status in services_status.items():
                if status:
                    self.logger.info(f"{service} service: OK")
                else:
                    self.logger.warning(f"{service} service: UNAVAILABLE")
            
            self._initialized = True
            self.logger.info("Surveillance services initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize services: {e}")
            return False
    
    def start_consumers(self) -> bool:
        """Start Kafka consumers - called after service initialization"""
        
        if self._consumers_started or not self._initialized:
            return False
        
        if not self.streaming or not self.streaming.health_check():
            self.logger.warning("Streaming service not available, skipping consumer startup")
            return False
        
        try:
            return self._start_consumers()
        except Exception as e:
            self.logger.error(f"Failed to start consumers: {e}")
            return False
    
    def _start_consumers(self):
        """Start Kafka consumers for processing events"""
        
        # Start event consumer
        self.streaming.start_event_consumer(
            group_id="api-event-processor",
            message_handler=self._handle_event_message
        )
        
        # Start chunk consumer
        self.streaming.start_chunk_consumer(
            group_id="api-chunk-processor", 
            message_handler=self._handle_chunk_message
        )
        
        # Start embedding consumer
        embedding_consumer = self.streaming.create_consumer(
            topics=[self.streaming.embeddings_topic],
            group_id="api-embedding-processor"
        )
        if embedding_consumer:
            import threading
            thread = threading.Thread(
                target=self.streaming._consume_messages,
                args=(embedding_consumer, self._handle_embedding_message, "api-embedding-processor"),
                daemon=True
            )
            thread.start()
        
        self._consumers_started = True
        self.logger.info("Started Kafka consumers")
        return True
    
    def _handle_event_message(self, key: str, message: Dict[str, Any]):
        """Handle incoming event messages from edge agent"""
        
        try:
            with get_db_session() as db:
                # Look for existing chunk to link to
                chunk_id = message.get("chunk_id")
                chunk = None
                if chunk_id:
                    chunk = db.query(VideoChunk).filter(VideoChunk.chunk_id == chunk_id).first()
                
                # Create event record
                event = Event(
                    camera_id=message.get("camera_id"),
                    chunk_id=chunk.chunk_id if chunk else None,
                    event_type=message.get("event_type"),
                    confidence=message.get("confidence"),
                    start_time=datetime.fromisoformat(message.get("timestamp")),
                    bounding_box=message.get("bounding_box"),
                    thumbnail_key=message.get("thumbnail_key"),
                    embedding_id=message.get("embedding_id"),
                    event_metadata=message.get("metadata", {}),
                    severity=message.get("severity", "low")
                )
                
                db.add(event)
                db.flush()
                
                # Store embedding metadata
                if message.get("embedding_id"):
                    embedding_meta = EmbeddingMetadata(
                        embedding_id=message.get("embedding_id"),
                        event_id=event.event_id,
                        camera_id=message.get("camera_id"),
                        embedding_type="xclip",
                        extraction_timestamp=datetime.now()
                    )
                    db.add(embedding_meta)
                
                self.logger.info(f"Processed event: {event.event_id}, linked to chunk: {chunk_id}")
                
        except Exception as e:
            self.logger.error(f"Error handling event message: {e}")
    
    def _handle_chunk_message(self, key: str, message: Dict[str, Any]):
        """Handle incoming chunk messages from edge agent"""
        
        try:
            with get_db_session() as db:
                # Create chunk record
                chunk = VideoChunk(
                    camera_id=message.get("camera_id"),
                    start_time=datetime.fromisoformat(message.get("start_time")),
                    end_time=datetime.fromisoformat(message.get("end_time")),
                    duration_seconds=message.get("duration_seconds"),
                    minio_key=message.get("minio_key"),
                    hls_playlist_key=message.get("hls_playlist_key"),
                    file_size_bytes=message.get("file_size_bytes"),
                    checksum=message.get("checksum")
                )
                
                db.add(chunk)
                
                self.logger.info(f"Processed chunk: {chunk.chunk_id}")
                
        except Exception as e:
            self.logger.error(f"Error handling chunk message: {e}")
    
    def _handle_embedding_message(self, key: str, message: Dict[str, Any]):
        """Handle incoming embedding messages from edge agent"""
        
        try:
            import numpy as np
            
            # Extract embedding data
            embedding_id = message.get("embedding_id")
            event_id = message.get("event_id")
            camera_id = message.get("camera_id")
            timestamp = datetime.fromisoformat(message.get("timestamp"))
            event_type = message.get("event_type")
            confidence = message.get("confidence")
            embedding_data = message.get("embedding")
            
            if embedding_data and embedding_id:
                # Convert embedding to numpy array
                embedding = np.array(embedding_data, dtype=np.float32)
                
                # Insert into Milvus
                success = self.vector_db.insert_embedding(
                    embedding_id=embedding_id,
                    event_id=event_id,
                    camera_id=camera_id,
                    timestamp=timestamp,
                    event_type=event_type,
                    confidence=confidence,
                    embedding=embedding
                )
                
                if success:
                    self.logger.info(f"Processed embedding: {embedding_id}")
                else:
                    self.logger.error(f"Failed to insert embedding: {embedding_id}")
            
        except Exception as e:
            self.logger.error(f"Error handling embedding message: {e}")
    
    def search_events_by_similarity(self,
                                  query_embedding: List[float],
                                  top_k: int = 10,
                                  camera_filter: str = None,
                                  time_range: tuple = None) -> List[Dict[str, Any]]:
        """Search events by vector similarity"""
        
        if not self._initialized or not self.vector_db:
            self.logger.warning("Vector database not available")
            return []
        
        import numpy as np
        query_vector = np.array(query_embedding, dtype=np.float32)
        
        # Search in Milvus
        similar_embeddings = self.vector_db.search_similar(
            query_embedding=query_vector,
            top_k=top_k,
            camera_filter=camera_filter,
            time_range=time_range
        )
        
        # Enrich with database data and presigned URLs
        enriched_results = []
        
        with get_db_session() as db:
            for result in similar_embeddings:
                event = db.query(Event).filter(
                    Event.event_id == result["event_id"]
                ).first()
                
                if event:
                    # Get presigned URLs for thumbnail and video
                    thumbnail_url = None
                    if event.thumbnail_key and self.storage:
                        thumbnail_url = self.storage.get_presigned_url(event.thumbnail_key)
                    
                    video_url = None
                    if event.video_chunk and self.storage:
                        video_url = self.storage.get_presigned_url(event.video_chunk.minio_key)
                    
                    enriched_result = {
                        "event_id": str(event.event_id),
                        "camera_id": event.camera_id,
                        "event_type": event.event_type,
                        "confidence": event.confidence,
                        "timestamp": event.start_time.isoformat(),
                        "similarity": result["similarity"],
                        "thumbnail_url": thumbnail_url,
                        "video_url": video_url,
                        "bounding_box": event.bounding_box,
                        "severity": event.severity
                    }
                    
                    enriched_results.append(enriched_result)
        
        return enriched_results
    
    def get_camera_live_feed_url(self, camera_id: str) -> Optional[str]:
        """Get live feed URL for camera"""
        
        if not camera_id:
            return None
        
        # Check if camera exists in database
        try:
            with get_db_session() as db:
                camera = db.query(Camera).filter(Camera.camera_id == camera_id).first()
                if not camera or not camera.is_active:
                    return None
        except Exception as e:
            self.logger.error(f"Error checking camera status: {e}")
            return None
        
        # Return HLS stream URL - could be enhanced to check actual stream availability
        return f"/api/v1/hls/{camera_id}/live.m3u8"
    
    def get_event_playback_urls(self, event_id: str) -> Dict[str, Optional[str]]:
        """Get playback URLs for event with presigned URLs"""
        
        if not event_id:
            return {}
        
        try:
            with get_db_session() as db:
                event = db.query(Event).filter(Event.event_id == event_id).first()
                
                if not event:
                    return {}
                
                result = {
                    "event_id": str(event.event_id),
                    "camera_id": event.camera_id,
                    "event_type": event.event_type,
                    "timestamp": event.start_time.isoformat() if event.start_time else None
                }
                
                # Thumbnail URL with presigned access
                if event.thumbnail_key and self.storage and self.storage.health_check():
                    try:
                        result["thumbnail_url"] = self.storage.get_presigned_url(
                            event.thumbnail_key, 
                            expiry_hours=24
                        )
                    except Exception as e:
                        self.logger.error(f"Error generating thumbnail presigned URL: {e}")
                        result["thumbnail_url"] = None
                else:
                    result["thumbnail_url"] = None
                
                # Video URL with presigned access
                if event.video_chunk and event.video_chunk.minio_key and self.storage and self.storage.health_check():
                    try:
                        result["video_url"] = self.storage.get_presigned_url(
                            event.video_chunk.minio_key,
                            expiry_hours=24
                        )
                        # Also provide HLS playlist if available
                        if event.video_chunk.hls_playlist_key:
                            result["hls_url"] = self.storage.get_presigned_url(
                                event.video_chunk.hls_playlist_key,
                                expiry_hours=24
                            )
                    except Exception as e:
                        self.logger.error(f"Error generating video presigned URL: {e}")
                        result["video_url"] = None
                else:
                    result["video_url"] = None
                
                # Add direct download URLs if storage is available
                if self.storage and self.storage.health_check():
                    result["storage_available"] = True
                else:
                    result["storage_available"] = False
                    self.logger.warning("Storage service unavailable for event playback")
                
                return result
                
        except Exception as e:
            self.logger.error(f"Error getting event playback URLs: {e}")
            return {}
    
    def health_check(self) -> Dict[str, Any]:
        """Complete health check of all services with detailed status"""
        
        health_status = {
            "initialized": self._initialized,
            "consumers_started": self._consumers_started,
            "services": {}
        }
        
        # Check individual services
        try:
            if self.storage:
                health_status["services"]["storage"] = {
                    "available": self.storage.health_check(),
                    "endpoint": getattr(self.storage, 'endpoint', 'unknown')
                }
            else:
                health_status["services"]["storage"] = {
                    "available": False,
                    "error": "Service not initialized"
                }
        except Exception as e:
            health_status["services"]["storage"] = {
                "available": False,
                "error": str(e)
            }
        
        try:
            if self.streaming:
                health_status["services"]["streaming"] = {
                    "available": self.streaming.health_check(),
                    "bootstrap_servers": getattr(self.streaming, 'bootstrap_servers', 'unknown'),
                    "topics": {
                        "events": getattr(self.streaming, 'events_topic', 'unknown'),
                        "chunks": getattr(self.streaming, 'chunks_topic', 'unknown'),
                        "embeddings": getattr(self.streaming, 'embeddings_topic', 'unknown')
                    }
                }
            else:
                health_status["services"]["streaming"] = {
                    "available": False,
                    "error": "Service not initialized"
                }
        except Exception as e:
            health_status["services"]["streaming"] = {
                "available": False,
                "error": str(e)
            }
        
        try:
            if self.vector_db:
                health_status["services"]["vector_db"] = {
                    "available": self.vector_db.health_check(),
                    "host": f"{getattr(self.vector_db, 'host', 'unknown')}:{getattr(self.vector_db, 'port', 'unknown')}",
                    "collection": getattr(self.vector_db, 'collection_name', 'unknown')
                }
                # Add collection stats if available
                if self.vector_db.health_check():
                    try:
                        stats = self.vector_db.get_collection_stats()
                        health_status["services"]["vector_db"]["stats"] = stats
                    except:
                        pass
            else:
                health_status["services"]["vector_db"] = {
                    "available": False,
                    "error": "Service not initialized"
                }
        except Exception as e:
            health_status["services"]["vector_db"] = {
                "available": False,
                "error": str(e)
            }
        
        # Overall health determination
        services_available = [
            health_status["services"][service].get("available", False) 
            for service in health_status["services"]
        ]
        
        health_status["overall_status"] = "healthy" if all(services_available) else "degraded"
        health_status["available_services"] = sum(services_available)
        health_status["total_services"] = len(services_available)
        
        return health_status
    
    def shutdown(self):
        """Graceful shutdown of all services"""
        
        self.logger.info("Shutting down surveillance services...")
        
        # Stop consumers first
        if self.streaming and self._consumers_started:
            try:
                self.streaming.stop_all_consumers()
                self._consumers_started = False
                self.logger.info("Stopped Kafka consumers")
            except Exception as e:
                self.logger.error(f"Error stopping consumers: {e}")
        
        # Close service connections
        try:
            if self.streaming:
                if hasattr(self.streaming, 'producer') and self.streaming.producer:
                    self.streaming.producer.close()
        except Exception as e:
            self.logger.error(f"Error closing streaming service: {e}")
        
        try:
            if self.vector_db and hasattr(self.vector_db, '__del__'):
                self.vector_db.__del__()
        except Exception as e:
            self.logger.error(f"Error closing vector database: {e}")
        
        self._initialized = False
        self.logger.info("Surveillance services shutdown complete")
    
    def is_ready(self) -> bool:
        """Check if services are ready to handle requests"""
        
        if not self._initialized:
            return False
        
        # At minimum, we need storage and database to be functional
        # Streaming and vector_db can be degraded
        essential_services = []
        if self.storage:
            essential_services.append(self.storage.health_check())
        
        # Check database connectivity
        try:
            with get_db_session() as db:
                db.execute("SELECT 1")
                essential_services.append(True)
        except Exception:
            essential_services.append(False)
        
        return all(essential_services)

# Global services instance - initialized during FastAPI startup
surveillance_services: Optional[SurveillanceServices] = None

def get_surveillance_services() -> SurveillanceServices:
    """Get the global surveillance services instance"""
    global surveillance_services
    if surveillance_services is None:
        raise RuntimeError("Surveillance services not initialized. Call during FastAPI startup.")
    return surveillance_services