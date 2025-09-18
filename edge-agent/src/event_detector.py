import torch
from ultralytics import YOLO
from transformers import XCLIPProcessor, XCLIPModel
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EventDetector:
    """
    Loads AI models and performs event detection and embedding generation.
    """
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")

        # 1. Load YOLOv8 for object detection
        self.yolo_model = YOLO('yolov8n.pt')
        self.yolo_model.to(self.device)
        logger.info("YOLOv8 model loaded.")

        # 2. Load X-CLIP for embeddings
        self.xclip_model_name = "microsoft/xclip-base-patch32"
        self.xclip_processor = XCLIPProcessor.from_pretrained(self.xclip_model_name)
        self.xclip_model = XCLIPModel.from_pretrained(self.xclip_model_name)
        self.xclip_model.to(self.device)
        logger.info("X-CLIP model loaded.")

    def detect_events(self, frame, classes_to_detect=None):
        """
        Runs object detection on a single frame.
        Filters for specific classes if provided (e.g., [0] for 'person').
        """
        if classes_to_detect is None:
            classes_to_detect = [0] # Default to detecting persons

        results = self.yolo_model(frame, classes=classes_to_detect, verbose=False)
        detections = []
        for result in results:
            for box in result.boxes:
                detections.append({
                    "class_id": int(box.cls),
                    "class_name": self.yolo_model.names[int(box.cls)],
                    "confidence": float(box.conf),
                    "bounding_box": [int(coord) for coord in box.xyxy[0]] # [x1, y1, x2, y2]
                })
        return detections

    def generate_embedding(self, video_clip_frames):
        """
        Generates a 512-dimension embedding for a list of video frames (clip).
        """
        if not video_clip_frames:
            return None

        inputs = self.xclip_processor(
            videos=list(video_clip_frames),
            return_tensors="pt",
            padding=True
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            embedding = self.xclip_model.get_video_features(**inputs).cpu().numpy()[0]
            
        return embedding.tolist()
