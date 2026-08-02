"""
sensor-backend/signal_processor.py
──────────────────────────────────
Turns raw CSI data into (a) movement/presence detection and (b) rough zone estimates.
This operates purely in-memory on the live stream.
"""

import time
import math
from collections import deque
import logging

log = logging.getLogger(__name__)

# Constants for tuning the signal processing
WINDOW_SIZE = 10           # How many recent samples to keep per node
MOVEMENT_THRESHOLD = 5.0   # Variance threshold above which we declare "movement"

class CSISignalProcessor:
    def __init__(self):
        # Stores a history of recent RSSI values for each node
        # Format: { "node_id": deque([rssi1, rssi2, ...], maxlen=WINDOW_SIZE) }
        self.node_history = {}
        
        # Current state outputs
        self.is_movement_detected = False
        self.active_zone = "Unknown"
        self.last_update_time = time.time()
        
    def add_data_point(self, node_id: str, rssi: float):
        """Called every time a new CSI packet arrives from an ESP32 node."""
        if node_id not in self.node_history:
            self.node_history[node_id] = deque(maxlen=WINDOW_SIZE)
            log.info(f"Signal Processor: Tracking new zone/node -> {node_id}")
            
        self.node_history[node_id].append(rssi)
        
    def _calculate_variance(self, values: list) -> float:
        """Calculates the statistical variance of a list of numbers."""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        return sum((x - mean) ** 2 for x in values) / len(values)
        
    def process(self):
        """
        Analyzes the recent history to detect movement and determine the active zone.
        Should be called in the main loop right before broadcasting to WebSocket.
        """
        current_time = time.time()
        self.current_highest_variance = 0.0
        most_disturbed_node = "Unknown"
        
        # 1. Calculate variance for all nodes to find signal disturbances
        for node_id, history in self.node_history.items():
            if len(history) >= 2:  # Need at least 2 points for variance
                variance = self._calculate_variance(list(history))
                
                # Keep track of which node has the MOST disturbance
                if variance > self.current_highest_variance:
                    self.current_highest_variance = variance
                    most_disturbed_node = node_id
                    
        # 2. Movement Detection (Step 4)
        if self.current_highest_variance > MOVEMENT_THRESHOLD:
            self.is_movement_detected = True
            # 3. Zone Estimation (Step 5)
            self.active_zone = most_disturbed_node
        else:
            self.is_movement_detected = False
            
        self.last_update_time = current_time

    def get_state(self) -> dict:
        """Returns the processed data for the WebSocket broadcaster."""
        variances = {}
        for node_id, history in self.node_history.items():
            variances[node_id] = round(self._calculate_variance(list(history)), 2)
            
        return {
            "movement_detected": self.is_movement_detected,
            "active_zone": self.active_zone,
            "highest_variance_score": round(getattr(self, 'current_highest_variance', 0.0), 2),
            "node_variances": variances,
            "tracked_zones": list(self.node_history.keys())
        }
