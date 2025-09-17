"""
Database models for AI surveillance system
Blueprint reference: python_database integration
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Boolean, JSON, Text, 
    ForeignKey, Index, create_engine, MetaData
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

Base = declarative_base()

class Camera(Base):
    """Camera model for managing camera devices and locations"""
    __tablename__ = "cameras"
    
    camera_id = Column(String(64), primary_key=True)
    name = Column(String(255), nullable=False)
    location = Column(String(500))
    latitude = Column(Float)  # For map positioning
    longitude = Column(Float)  # For map positioning
    region_id = Column(String(64))
    status = Column(String(20), default="active")  # active, inactive, maintenance
    camera_type = Column(String(50), default="security")  # security, traffic, etc.
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    video_chunks = relationship("VideoChunk", back_populates="camera")
    events = relationship("Event", back_populates="camera")
    
    def __repr__(self):
        return f"<Camera(camera_id='{self.camera_id}', name='{self.name}')>"

class VideoChunk(Base):
    """Video chunk model for storing video segments"""
    __tablename__ = "video_chunks"
    
    chunk_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    camera_id = Column(String(64), ForeignKey("cameras.camera_id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    duration_seconds = Column(Integer)
    minio_key = Column(String(500), nullable=False)  # S3 object key
    hls_playlist_key = Column(String(500))  # HLS playlist key
    file_size_bytes = Column(Integer)
    checksum = Column(String(64))
    resolution = Column(String(20))  # 1920x1080, etc.
    fps = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    camera = relationship("Camera", back_populates="video_chunks")
    events = relationship("Event", back_populates="video_chunk")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_chunks_camera_time', 'camera_id', 'start_time'),
        Index('idx_chunks_time_range', 'start_time', 'end_time'),
    )
    
    def __repr__(self):
        return f"<VideoChunk(chunk_id='{self.chunk_id}', camera_id='{self.camera_id}')>"

class Event(Base):
    """Event model for AI detection results"""
    __tablename__ = "events"
    
    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    camera_id = Column(String(64), ForeignKey("cameras.camera_id"), nullable=False)
    chunk_id = Column(UUID(as_uuid=True), ForeignKey("video_chunks.chunk_id"))
    event_type = Column(String(50), nullable=False)  # person, vehicle, anomaly, etc.
    confidence = Column(Float, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    bounding_box = Column(JSONB)  # {x, y, width, height}
    thumbnail_key = Column(String(500))  # MinIO key for thumbnail
    embedding_id = Column(String(64))  # Reference to Milvus embedding
    event_metadata = Column(JSONB)  # Additional event metadata
    severity = Column(String(20), default="low")  # low, medium, high, critical
    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String(255))
    acknowledged_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    camera = relationship("Camera", back_populates="events")
    video_chunk = relationship("VideoChunk", back_populates="events")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_events_camera_time', 'camera_id', 'start_time'),
        Index('idx_events_type', 'event_type'),
        Index('idx_events_severity', 'severity'),
        Index('idx_events_acknowledged', 'acknowledged'),
    )
    
    def __repr__(self):
        return f"<Event(event_id='{self.event_id}', type='{self.event_type}')>"

class EmbeddingMetadata(Base):
    """Metadata for embeddings stored in Milvus"""
    __tablename__ = "embedding_metadata"
    
    embedding_id = Column(String(64), primary_key=True)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.event_id"))
    camera_id = Column(String(64), ForeignKey("cameras.camera_id"))
    embedding_type = Column(String(50), nullable=False)  # xclip, clip, etc.
    vector_dimension = Column(Integer, default=512)
    model_version = Column(String(50))
    extraction_timestamp = Column(DateTime, default=datetime.utcnow)
    milvus_collection = Column(String(100), default="surveillance_embeddings")
    
    # Relationships
    event = relationship("Event")
    camera = relationship("Camera")
    
    def __repr__(self):
        return f"<EmbeddingMetadata(embedding_id='{self.embedding_id}')>"

class User(Base):
    """User model for authentication and RBAC"""
    __tablename__ = "users"
    
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="viewer")  # admin, investigator, operator, viewer
    is_active = Column(Boolean, default=True)
    permissions = Column(JSONB)  # Role-based permissions
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<User(username='{self.username}', role='{self.role}')>"

class SearchQuery(Base):
    """Log search queries for analytics and improvement"""
    __tablename__ = "search_queries"
    
    query_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    query_text = Column(Text, nullable=False)
    query_type = Column(String(50))  # semantic, text, filter
    gemini_interpretation = Column(JSONB)  # Gemini's query analysis
    sql_filters = Column(JSONB)  # Generated SQL filters
    milvus_filters = Column(JSONB)  # Milvus search parameters
    results_count = Column(Integer)
    execution_time_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<SearchQuery(query_id='{self.query_id}', query_text='{self.query_text[:50]}')>"