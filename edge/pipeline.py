"""
Edge Vision Pipeline — Camera feed ingestion, detection, tracking, and event emission.
Emits structured JSON events to /api/events with edge buffering.
"""
import time
import json
import logging
import httpx
from datetime import datetime, timezone
from edge.detection.person_detector import PersonDetector
from edge.tracking.zone_tracker import ZoneTracker

logging.basicConfig(level=logging.INFO, format="%(asctime)s [EDGE] %(levelname)s — %(message)s")
logger = logging.getLogger("retailiq.edge.pipeline")


class EdgePipeline:
    def __init__(
        self,
        backend_url: str = "http://localhost:8000",
        store_id: int = 1,
        camera_source: str = "0",
        frame_skip: int = 3,
    ):
        self.backend_url = backend_url
        self.store_id = store_id
        self.camera_source = camera_source
        self.frame_skip = frame_skip
        self.detector = PersonDetector()
        self.tracker = ZoneTracker()
        self.buffer = []

    def process_and_emit(self, detections, frame_width=1280, frame_height=720):
        """Map detections to zones and format event payload"""
        zone_summary = self.tracker.map_detections_to_zones(detections, frame_width, frame_height)
        events = []
        total_people = len(detections)

        for zone_id, data in zone_summary.items():
            events.append({
                "store_id": self.store_id,
                "event_type": "zone_update",
                "zone_id": zone_id,
                "payload": {
                    "zone_id": zone_id,
                    "people_count": data["count"],
                    "dwell_time_avg": data["dwell_avg"],
                },
                "confidence": 0.92,
                "source": "edge_yolo",
            })

        events.append({
            "store_id": self.store_id,
            "event_type": "footfall_update",
            "payload": {
                "current": total_people,
                "delta": 0,
            },
            "source": "edge_yolo",
        })

        return events

    async def send_events(self, events):
        """Send events to backend with offline buffering"""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.post(
                    f"{self.backend_url}/api/events/batch",
                    json={"events": events},
                )
                if res.status_code == 200:
                    logger.info(f"Dispatched {len(events)} edge events to backend")
                    return True
        except Exception as e:
            logger.warning(f"Backend offline ({e}). Buffering {len(events)} events locally.")
            self.buffer.extend(events)
            return False


if __name__ == "__main__":
    import asyncio
    pipeline = EdgePipeline()
    logger.info("Edge AI Vision Pipeline initialized and ready for video/camera stream input.")
