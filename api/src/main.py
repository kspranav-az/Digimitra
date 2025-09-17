"""
FastAPI main application for AI surveillance system
Blueprint reference: python_database integration
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import get_db, create_tables, get_db_session
from models import Camera, Event, VideoChunk, User
from services import get_surveillance_services, SurveillanceServices

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager for service initialization and cleanup"""
    # Startup
    logger.info("Starting AI Surveillance System API...")
    
    # Initialize database tables
    try:
        create_tables()
        logger.info("Database tables created/verified successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise
    
    # Initialize surveillance services
    from services import surveillance_services
    global surveillance_services
    try:
        surveillance_services = SurveillanceServices()
        logger.info("Surveillance services instance created")
        
        # Initialize all services
        if surveillance_services.initialize_services():
            logger.info("Surveillance services initialized successfully")
            
            # Start consumers if streaming is available
            if surveillance_services.start_consumers():
                logger.info("Kafka consumers started successfully")
            else:
                logger.warning("Kafka consumers could not be started (streaming service unavailable)")
        else:
            logger.warning("Some surveillance services failed to initialize")
            
        # Check readiness
        if surveillance_services.is_ready():
            logger.info("API is ready to handle requests")
        else:
            logger.warning("API is not fully ready - some services may be unavailable")
            
    except Exception as e:
        logger.error(f"Failed to initialize surveillance services: {e}")
        # Don't raise - allow app to start in degraded mode
        surveillance_services = SurveillanceServices()  # Create basic instance
    
    logger.info("API startup complete")
    
    yield  # App runs here
    
    # Shutdown
    logger.info("Shutting down AI Surveillance System API...")
    try:
        if surveillance_services:
            surveillance_services.shutdown()
            logger.info("Surveillance services shutdown complete")
    except Exception as e:
        logger.error(f"Error during service shutdown: {e}")
    
    logger.info("API shutdown complete")

# Create FastAPI app with lifespan
app = FastAPI(
    title="AI Surveillance System API",
    description="OOP-architected AI surveillance system with real-time processing",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "AI Surveillance System API",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    try:
        # Test database connection
        db_status = "connected"
        try:
            with get_db_session() as db:
                db.execute("SELECT 1")
        except:
            db_status = "disconnected"
        
        # Check if services are ready
        services_ready = False
        try:
            services = get_surveillance_services()
            services_ready = services.is_ready()
        except:
            pass
        
        return {
            "status": "healthy" if db_status == "connected" else "degraded",
            "database": db_status,
            "services": {
                "api": "running",
                "database": db_status,
                "surveillance_services": "ready" if services_ready else "not_ready"
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.get("/api/v1/cameras")
async def get_cameras(db: Session = Depends(get_db)):
    """Get all cameras"""
    try:
        cameras = db.query(Camera).all()
        return {
            "cameras": [
                {
                    "camera_id": camera.camera_id,
                    "name": camera.name,
                    "location": camera.location,
                    "latitude": camera.latitude,
                    "longitude": camera.longitude,
                    "status": camera.status,
                    "is_active": camera.is_active
                }
                for camera in cameras
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/v1/events")
async def get_events(
    camera_id: str = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get events with optional camera filtering"""
    try:
        query = db.query(Event)
        if camera_id:
            query = query.filter(Event.camera_id == camera_id)
        
        events = query.limit(limit).all()
        return {
            "events": [
                {
                    "event_id": str(event.event_id),
                    "camera_id": event.camera_id,
                    "event_type": event.event_type,
                    "confidence": event.confidence,
                    "start_time": event.start_time.isoformat() if event.start_time else None,
                    "severity": event.severity,
                    "acknowledged": event.acknowledged
                }
                for event in events
            ],
            "total": len(events)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/api/v1/cameras")
async def create_camera(
    camera_data: dict,
    db: Session = Depends(get_db)
):
    """Create a new camera"""
    try:
        camera = Camera(
            camera_id=camera_data.get("camera_id"),
            name=camera_data.get("name"),
            location=camera_data.get("location"),
            latitude=camera_data.get("latitude"),
            longitude=camera_data.get("longitude"),
            region_id=camera_data.get("region_id"),
            camera_type=camera_data.get("camera_type", "security")
        )
        db.add(camera)
        db.commit()
        db.refresh(camera)
        
        return {
            "message": "Camera created successfully",
            "camera_id": camera.camera_id
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/api/v1/search/similarity")
async def search_similarity(request_data: dict):
    """Search events by vector similarity"""
    try:
        query_embedding = request_data.get("embedding")
        top_k = request_data.get("top_k", 10)
        camera_filter = request_data.get("camera_id")
        
        if not query_embedding:
            raise HTTPException(status_code=400, detail="embedding is required")
        
        services = get_surveillance_services()
        results = services.search_events_by_similarity(
            query_embedding=query_embedding,
            top_k=top_k,
            camera_filter=camera_filter
        )
        
        return {
            "results": results,
            "total": len(results)
        }
        
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail="Services not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@app.get("/api/v1/events/{event_id}/playback")
async def get_event_playback(event_id: str):
    """Get playback URLs for event"""
    try:
        services = get_surveillance_services()
        urls = services.get_event_playback_urls(event_id)
        
        if not urls:
            raise HTTPException(status_code=404, detail="Event not found")
        
        return urls
        
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail="Services not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Playback error: {str(e)}")

@app.get("/api/v1/cameras/{camera_id}/live")
async def get_camera_live_feed(camera_id: str):
    """Get live feed URL for camera"""
    try:
        services = get_surveillance_services()
        feed_url = services.get_camera_live_feed_url(camera_id)
        
        if not feed_url:
            raise HTTPException(status_code=404, detail="Camera not found or inactive")
        
        return {"live_feed_url": feed_url}
        
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail="Services not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Live feed error: {str(e)}")

@app.get("/api/v1/health/services")
async def health_check_services():
    """Check health of all integrated services"""
    try:
        services = get_surveillance_services()
        health_status = services.health_check()
        
        # Use overall_status from enhanced health check
        status = health_status.get("overall_status", "unknown")
        
        return {
            "status": status,
            **health_status
        }
        
    except RuntimeError as e:
        # Services not initialized - return degraded status
        return {
            "status": "degraded",
            "error": "Services not initialized",
            "initialized": False,
            "consumers_started": False,
            "services": {
                "storage": {"available": False, "error": "Not initialized"},
                "streaming": {"available": False, "error": "Not initialized"},
                "vector_db": {"available": False, "error": "Not initialized"}
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)