"""
Event detection classes using YOLOv8 and X-CLIP for AI surveillance
OOP-oriented design for edge agent
"""
import cv2
import numpy as np
import torch
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None
    print("Warning: ultralytics not installed, YOLOv8 detection disabled")

try:
    from transformers import CLIPProcessor, CLIPModel
except ImportError:
    CLIPProcessor = None
    CLIPModel = None
    print("Warning: transformers not installed, CLIP embeddings disabled")

@dataclass
class Detection:
    """Structure for object detection results"""
    class_id: int
    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x, y, width, height
    timestamp: datetime
    frame_shape: Tuple[int, int]  # height, width

@dataclass
class EventDetection:
    """Structure for event detection with embeddings"""
    detection: Detection
    thumbnail: np.ndarray
    embedding: Optional[np.ndarray] = None
    event_type: str = "object_detection"
    severity: str = "low"

class YOLODetector:
    """YOLO-based object detection class"""
    
    def __init__(self, model_path: str = "yolov8n.pt", device: str = "auto"):
        self.logger = logging.getLogger("YOLODetector")
        self.device = self._get_device(device)
        self.model = None
        self.class_names = {}
        
        self._initialize_model(model_path)
    
    def _get_device(self, device: str) -> str:
        """Determine the best device for inference"""
        if device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            else:
                return "cpu"
        return device
    
    def _initialize_model(self, model_path: str):
        """Initialize YOLO model"""
        try:
            if YOLO is None:
                self.logger.warning("YOLO not available, using mock detector")
                return
            
            self.model = YOLO(model_path)
            self.model.to(self.device)
            
            # Get class names
            self.class_names = self.model.names
            
            self.logger.info(f"YOLO model loaded on {self.device}")
            self.logger.info(f"Available classes: {list(self.class_names.values())}")
            
        except Exception as e:
            self.logger.error(f"Error loading YOLO model: {e}")
            self.model = None
    
    def detect(self, frame: np.ndarray, 
               confidence_threshold: float = 0.5,
               target_classes: List[str] = None) -> List[Detection]:
        """Detect objects in frame"""
        
        if self.model is None:
            # Return mock detection for testing
            return self._mock_detection(frame)
        
        try:
            # Run inference
            results = self.model(frame, verbose=False)
            detections = []
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        confidence = float(box.conf[0])
                        class_id = int(box.cls[0])
                        class_name = self.class_names.get(class_id, "unknown")
                        
                        # Filter by confidence and target classes
                        if confidence < confidence_threshold:
                            continue
                        
                        if target_classes and class_name not in target_classes:
                            continue
                        
                        # Get bounding box coordinates
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        bbox = (int(x1), int(y1), int(x2 - x1), int(y2 - y1))
                        
                        detection = Detection(
                            class_id=class_id,
                            class_name=class_name,
                            confidence=confidence,
                            bbox=bbox,
                            timestamp=datetime.now(),
                            frame_shape=frame.shape[:2]
                        )
                        
                        detections.append(detection)
            
            return detections
            
        except Exception as e:
            self.logger.error(f"Error during detection: {e}")
            return []
    
    def _mock_detection(self, frame: np.ndarray) -> List[Detection]:
        """Mock detection for testing when YOLO is not available"""
        height, width = frame.shape[:2]
        
        # Generate random mock detection occasionally
        import random
        if random.random() < 0.1:  # 10% chance of detection
            class_name = random.choice(["person", "car", "bicycle"])
            return [Detection(
                class_id=0,
                class_name=class_name,
                confidence=0.8,
                bbox=(width//4, height//4, width//2, height//2),
                timestamp=datetime.now(),
                frame_shape=(height, width)
            )]
        
        return []

class CLIPEmbeddingExtractor:
    """X-CLIP embedding extraction for semantic search"""
    
    def __init__(self, model_name: str = "openai/clip-vit-base-patch32", device: str = "auto"):
        self.logger = logging.getLogger("CLIPEmbeddingExtractor")
        self.device = self._get_device(device)
        self.model = None
        self.processor = None
        
        self._initialize_model(model_name)
    
    def _get_device(self, device: str) -> str:
        """Determine the best device for inference"""
        if device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            else:
                return "cpu"
        return device
    
    def _initialize_model(self, model_name: str):
        """Initialize CLIP model"""
        try:
            if CLIPProcessor is None or CLIPModel is None:
                self.logger.warning("CLIP not available, using mock embeddings")
                return
            
            self.processor = CLIPProcessor.from_pretrained(model_name)
            self.model = CLIPModel.from_pretrained(model_name)
            self.model.to(self.device)
            self.model.eval()
            
            self.logger.info(f"CLIP model loaded on {self.device}")
            
        except Exception as e:
            self.logger.error(f"Error loading CLIP model: {e}")
            self.model = None
    
    def extract_image_embedding(self, image: np.ndarray) -> Optional[np.ndarray]:
        """Extract embedding from image"""
        
        if self.model is None:
            # Return mock embedding
            return np.random.rand(512).astype(np.float32)
        
        try:
            # Convert BGR to RGB
            if len(image.shape) == 3:
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                image_rgb = image
            
            # Process image
            inputs = self.processor(images=image_rgb, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Extract features
            with torch.no_grad():
                image_features = self.model.get_image_features(**inputs)
                
            # Normalize embedding
            embedding = image_features.cpu().numpy().flatten()
            embedding = embedding / np.linalg.norm(embedding)
            
            return embedding.astype(np.float32)
            
        except Exception as e:
            self.logger.error(f"Error extracting embedding: {e}")
            return None
    
    def extract_text_embedding(self, text: str) -> Optional[np.ndarray]:
        """Extract embedding from text description"""
        
        if self.model is None:
            # Return mock embedding
            return np.random.rand(512).astype(np.float32)
        
        try:
            # Process text
            inputs = self.processor(text=[text], return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Extract features
            with torch.no_grad():
                text_features = self.model.get_text_features(**inputs)
            
            # Normalize embedding
            embedding = text_features.cpu().numpy().flatten()
            embedding = embedding / np.linalg.norm(embedding)
            
            return embedding.astype(np.float32)
            
        except Exception as e:
            self.logger.error(f"Error extracting text embedding: {e}")
            return None

class EventDetector:
    """Main event detection class combining YOLO and CLIP"""
    
    def __init__(self, camera_id: str, config: Dict[str, Any] = None):
        self.camera_id = camera_id
        self.config = config or {}
        self.logger = logging.getLogger(f"EventDetector-{camera_id}")
        
        # Initialize detectors
        self.yolo_detector = YOLODetector(
            model_path=self.config.get("yolo_model", "yolov8n.pt"),
            device=self.config.get("device", "auto")
        )
        
        self.clip_extractor = CLIPEmbeddingExtractor(
            model_name=self.config.get("clip_model", "openai/clip-vit-base-patch32"),
            device=self.config.get("device", "auto")
        )
        
        # Detection configuration
        self.confidence_threshold = self.config.get("confidence_threshold", 0.5)
        self.target_classes = self.config.get("target_classes", ["person", "car", "bicycle", "motorcycle"])
        
    def process_frame(self, frame: np.ndarray) -> List[EventDetection]:
        """Process frame and return event detections"""
        
        # Run object detection
        detections = self.yolo_detector.detect(
            frame, 
            confidence_threshold=self.confidence_threshold,
            target_classes=self.target_classes
        )
        
        event_detections = []
        
        for detection in detections:
            try:
                # Extract thumbnail
                thumbnail = self._extract_thumbnail(frame, detection.bbox)
                
                # Extract embedding
                embedding = self.clip_extractor.extract_image_embedding(thumbnail)
                
                # Determine event severity
                severity = self._determine_severity(detection)
                
                event_detection = EventDetection(
                    detection=detection,
                    thumbnail=thumbnail,
                    embedding=embedding,
                    event_type=f"{detection.class_name}_detection",
                    severity=severity
                )
                
                event_detections.append(event_detection)
                
            except Exception as e:
                self.logger.error(f"Error processing detection: {e}")
                continue
        
        return event_detections
    
    def _extract_thumbnail(self, frame: np.ndarray, bbox: Tuple[int, int, int, int]) -> np.ndarray:
        """Extract thumbnail from frame using bounding box"""
        x, y, w, h = bbox
        
        # Ensure bounding box is within frame bounds
        height, width = frame.shape[:2]
        x = max(0, min(x, width - 1))
        y = max(0, min(y, height - 1))
        w = max(1, min(w, width - x))
        h = max(1, min(h, height - y))
        
        # Extract region of interest
        thumbnail = frame[y:y+h, x:x+w]
        
        # Resize to standard thumbnail size
        thumbnail_size = (224, 224)
        thumbnail = cv2.resize(thumbnail, thumbnail_size)
        
        return thumbnail
    
    def _determine_severity(self, detection: Detection) -> str:
        """Determine event severity based on detection"""
        
        # High-priority classes
        high_priority_classes = ["person"]
        medium_priority_classes = ["car", "motorcycle"]
        
        if detection.class_name in high_priority_classes:
            if detection.confidence > 0.8:
                return "high"
            elif detection.confidence > 0.6:
                return "medium"
        elif detection.class_name in medium_priority_classes:
            if detection.confidence > 0.8:
                return "medium"
        
        return "low"
    
    def get_detection_summary(self, event_detections: List[EventDetection]) -> Dict[str, Any]:
        """Get summary of detections for logging/monitoring"""
        
        summary = {
            "total_detections": len(event_detections),
            "by_class": {},
            "by_severity": {"low": 0, "medium": 0, "high": 0, "critical": 0},
            "avg_confidence": 0.0
        }
        
        if not event_detections:
            return summary
        
        total_confidence = 0
        for event_detection in event_detections:
            detection = event_detection.detection
            
            # Count by class
            class_name = detection.class_name
            summary["by_class"][class_name] = summary["by_class"].get(class_name, 0) + 1
            
            # Count by severity
            severity = event_detection.severity
            summary["by_severity"][severity] += 1
            
            # Sum confidence
            total_confidence += detection.confidence
        
        summary["avg_confidence"] = total_confidence / len(event_detections)
        
        return summary