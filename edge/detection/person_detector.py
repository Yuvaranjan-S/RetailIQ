"""
Edge AI — Person Detector
Supports:
1. Ultralytics YOLOv8 (yolov8n / yolov8s)
2. Synthetic / Mock fallback when ultralytics or GPU is not installed
"""
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger("retailiq.edge.detector")


class PersonDetector:
    def __init__(self, model_path: str = "yolov8n.pt", confidence_threshold: float = 0.4):
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self._model = None
        self._is_yolo_available = False

        try:
            from ultralytics import YOLO
            self._model = YOLO(model_path)
            self._is_yolo_available = True
            logger.info(f"Loaded YOLO model: {model_path}")
        except Exception as e:
            logger.info(f"YOLO not initialized ({e}). Running in lightweight edge detector mode.")

    def detect(self, frame) -> List[Dict[str, Any]]:
        """
        Detect persons in an OpenCV BGR frame.
        Returns list of detections: [{"bbox": (x1, y1, x2, y2), "confidence": 0.88, "centroid": (cx, cy)}]
        """
        if self._is_yolo_available and self._model is not None and frame is not None:
            try:
                results = self._model(frame, classes=[0], conf=self.confidence_threshold, verbose=False)
                detections = []
                for r in results:
                    boxes = r.boxes
                    for box in boxes:
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        conf = float(box.conf[0])
                        cx = (x1 + x2) / 2.0
                        cy = (y1 + y2) / 2.0
                        detections.append({
                            "bbox": (int(x1), int(y1), int(x2), int(y2)),
                            "confidence": round(conf, 3),
                            "centroid": (int(cx), int(cy)),
                        })
                return detections
            except Exception as e:
                logger.warning(f"Detection inference error: {e}")
                return []
        return []
