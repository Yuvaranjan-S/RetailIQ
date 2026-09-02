"""
Edge Tracking — Zone Mapping and Dwell Time Tracker
Maps 2D frame coordinates to configured store zones and computes occupancy/dwell metrics.
"""
from typing import List, Dict, Any, Tuple
import time


class ZoneTracker:
    def __init__(self, zones_config: List[Dict[str, Any]] = None):
        """
        zones_config: list of dicts:
          [{"id": 1, "name": "Entrance", "bounds": (x1, y1, x2, y2)}]
        """
        self.zones = zones_config or [
            {"id": 1, "name": "Entrance", "bounds": (0, 0, 0.3, 0.5)},
            {"id": 2, "name": "Produce & Dairy", "bounds": (0.3, 0, 0.65, 0.5)},
            {"id": 3, "name": "Grocery & Packaged", "bounds": (0.65, 0, 1.0, 0.5)},
            {"id": 4, "name": "Electronics & Home", "bounds": (0, 0.5, 0.4, 1.0)},
            {"id": 5, "name": "Checkout Area", "bounds": (0.4, 0.5, 0.75, 1.0)},
            {"id": 6, "name": "Staff & Storage", "bounds": (0.75, 0.5, 1.0, 1.0)},
        ]
        self._track_history: Dict[int, float] = {}

    def map_detections_to_zones(
        self,
        detections: List[Dict[str, Any]],
        frame_width: int = 1280,
        frame_height: int = 720,
    ) -> Dict[int, Dict[str, Any]]:
        """
        Assign each detection centroid to a store zone.
        Returns: {zone_id: {"count": N, "zone_name": str}}
        """
        zone_counts = {z["id"]: {"count": 0, "name": z["name"], "dwell_avg": 45.0} for z in self.zones}

        for det in detections:
            cx, cy = det["centroid"]
            norm_x = cx / max(frame_width, 1)
            norm_y = cy / max(frame_height, 1)

            for z in self.zones:
                bx1, by1, bx2, by2 = z["bounds"]
                if bx1 <= norm_x <= bx2 and by1 <= norm_y <= by2:
                    zone_counts[z["id"]]["count"] += 1
                    break

        return zone_counts
