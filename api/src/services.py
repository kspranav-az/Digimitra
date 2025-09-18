import os
import uuid
import logging
from typing import List, Optional
from urllib.parse import urljoin

from sqlalchemy.orm import Session
from minio import Minio
from pymilvus import MilvusClient

from shared.models import Event, Camera

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SurveillanceServices:
    def __init__(self, db: Session):
        self.db = db
        # Initialize MinIO client
        self.minio_client = Minio(
            endpoint=os.environ.get("MINIO_ENDPOINT"),
            access_key=os.environ.get("MINIO_ACCESS_KEY"),
            secret_key=os.environ.get("MINIO_SECRET_KEY"),
            secure=False
        )
        # Initialize Milvus client
        self.milvus_client = MilvusClient(
            host=os.environ.get("MILVUS_HOST"),
            port=int(os.environ.get("MILVUS_PORT"))
        )
        # HLS base URL for playback
        self.hls_base_url = f"http://{os.environ.get('MINIO_ENDPOINT')}/hls/"

    def initialize_services(self):
        """
        Initializes MinIO buckets and Milvus collections if they don't exist.
        """
        self._initialize_minio()
        self._initialize_milvus()

    def _initialize_minio(self):
        """
        Creates MinIO buckets if they don't already exist.
        """
        try:
            if not self.minio_client.bucket_exists("thumbnails"):
                self.minio_client.make_bucket("thumbnails")
                logger.info("Created bucket: thumbnails")
            if not self.minio_client.bucket_exists("chunks"):
                self.minio_client.make_bucket("chunks")
                logger.info("Created bucket: chunks")
        except Exception as e:
            logger.error(f"Error initializing MinIO: {e}")
            raise

    def _initialize_milvus(self):
        """
        Creates Milvus collections if they don't already exist.
        """
        try:
            if not self.milvus_client.has_collection("events"):
                self.milvus_client.create_collection(
                    collection_name="events",
                    schema={
                        "fields": [
                            {"name": "embedding", "type": "FLOAT_VECTOR", "params": {"dim": 512}},
                            {"name": "event_id", "type": "VARCHAR", "params": {"max_length": 36}},
                            {"name": "timestamp", "type": "INT64"},
                            {"name": "camera_id", "type": "VARCHAR", "params": {"max_length": 255}},
                        ]
                    },
                    index_params=[
                        {"field": "embedding", "index_type": "IVF_FLAT", "metric_type": "L2"}
                    ]
                )
                logger.info("Created Milvus collection: events")
        except Exception as e:
            logger.error(f"Error initializing Milvus: {e}")
            raise
    
    def get_event_playback_urls(self, event_id: str) -> dict:
        """
        Generates signed URLs for event playback (HLS playlist and thumbnails).
        """
        event = self.db.query(Event).filter(Event.event_id == event_id).first()
        if not event:
            return {}

        # Get the associated video chunk
        chunk_path = event.chunk_path
        if not chunk_path:
            return {}
        
        # Construct HLS playlist URL
        playlist_url = urljoin(self.hls_base_url, f"{chunk_path}/playlist.m3u8")

        # Construct other stream file URLs
        stream_urls = {
            f"stream{i}.ts": urljoin(self.hls_base_url, f"{chunk_path}/stream{i}.ts")
            for i in range(3)  # Assuming 3 quality levels
        }

        return {
            "event_id": event_id,
            "playlist_url": playlist_url,
            "stream_urls": stream_urls,
            "thumbnail_urls": [urljoin(self.hls_base_url, thumbnail.path) for thumbnail in event.thumbnails]
        }

    def search_events_by_similarity(
        self, 
        query_embedding: List[float], 
        top_k: int = 10, 
        camera_filter: Optional[str] = None,
        time_range: Optional[tuple] = None
    ) -> List[dict]:
        """
        Searches for events in Milvus based on embedding similarity.
        """
        try:
            search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
            results = self.milvus_client.search(
                collection_name="events",
                data=[query_embedding],
                limit=top_k,
                search_params=search_params
            )
            
            # Process and return results with playback URLs
            return [
                {
                    "event_id": hit.entity.get("event_id"),
                    "distance": hit.distance,
                    "playback": self.get_event_playback_urls(hit.entity.get("event_id"))
                }
                for hit in results[0]
            ]
        except Exception as e:
            logger.error(f"Error searching Milvus: {e}")
            return []

    def get_camera_live_feed_url(self, camera_id: str) -> Optional[str]:
        """
        Returns the live feed URL for a given camera.
        """
        camera = self.db.query(Camera).filter(Camera.id == camera_id).first()
        if camera:
            return urljoin(self.hls_base_url, f"{camera.id}/live.m3u8")
        return None

def get_surveillance_services():
    db = Session()
    return SurveillanceServices(db)
