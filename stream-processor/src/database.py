import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from shared.models import Base

def get_db():
    db_url = os.environ.get("DATABASE_URL")
    engine = create_engine(db_url)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)()

def create_tables():
    db_url = os.environ.get("DATABASE_URL")
    engine = create_engine(db_url)
    Base.metadata.create_all(bind=engine)
