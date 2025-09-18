from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()

class Camera(Base):
    __tablename__ = 'cameras'
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String)
    location = Column(String)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

class Event(Base):
    __tablename__ = 'events'
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    camera_id = Column(String, ForeignKey('cameras.id'))
    timestamp = Column(DateTime)
    event_type = Column(String)
    confidence = Column(Float)
    bounding_box = Column(JSON)
    thumbnail_path = Column(String)
    chunk_path = Column(String)
    camera = relationship("Camera")

class User(Base):
    __tablename__ = 'users'
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String) # e.g., 'admin', 'investigator', 'viewer'
