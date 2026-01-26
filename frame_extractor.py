"""
Extract frames from video and publish to MSK for analysis
Includes perimeter boundary detection and player tracking
"""

import json
import cv2
import numpy as np
from kafka import KafkaProducer
import base64
from datetime import datetime

class FrameExtractor:
    """Extract and analyze video frames"""
    
    def __init__(self, bootstrap_servers, topic='game-frames'):
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers.split(','),
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        self.topic = topic
        self.frame_count = 0
        
        # Define perimeter boundaries (example for baseball field)
        self.boundaries = {
            'field_boundary': [(100, 100), (500, 100), (500, 400), (100, 400)],
            'dugout_zone': [(50, 50), (150, 50), (150, 150), (50, 150)],
            'restricted_zone': [(600, 300), (700, 300), (700, 400), (600, 400)]
        }
    
    def detect_objects(self, frame):
        """Detect players and objects in frame"""
        # Simplified detection - real implementation would use YOLO/SSD
        # This is a placeholder for demonstration
        
        detections = []
        
        # Example: Use background subtraction for motion detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (21, 21), 0)
        
        # Placeholder detection
        detections.append({
            'type': 'player',
            'id': 'player_42',
            'position': [250, 300],
            'confidence': 0.95,
            'bbox': [240, 280, 260, 320]
        })
        
        return detections
    
    def check_perimeter_breach(self, detections):
        """Check if any detected object breaches perimeter"""
        violations = []
        
        for detection in detections:
            pos = detection['position']
            
            for zone_name, boundary in self.boundaries.items():
                if self.point_in_polygon(pos, boundary):
                    # Check if this is a restricted zone
                    if 'restricted' in zone_name or 'dugout' in zone_name:
                        violations.append({
                            'type': 'perimeter_breach',
                            'zone': zone_name,
                            'subject': detection['id'],
                            'position': pos,
                            'severity': 'warning'
                        })
        
        return violations
    
    def point_in_polygon(self, point, polygon):
        """Check if point is inside polygon"""
        x, y = point
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    def process_frame(self, frame):
        """Process frame and publish to Kafka"""
        
        # Detect objects
        detections = self.detect_objects(frame)
        
        # Check for violations
        violations = self.check_perimeter_breach(detections)
        
        # Encode frame as base64 (for small frames, use S3 for full resolution)
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        frame_b64 = base64.b64encode(buffer).decode('utf-8')
        
        # Create event
        event = {
            'frame_id': f"frame_{self.frame_count}",
            'timestamp': datetime.utcnow().isoformat(),
            'frame_data': frame_b64[:1000],  # Truncated for demo
            'detections': detections,
            'violations': violations,
            'metadata': {
                'width': frame.shape[1],
                'height': frame.shape[0],
                'boundaries': list(self.boundaries.keys())
            }
        }
        
        # Publish to Kafka
        self.producer.send(self.topic, value=event)
        
        self.frame_count += 1
        
        return event
    
    def extract_from_video(self, video_source, sample_rate=1):
        """
        Extract frames from video source
        
        Args:
            video_source: Video file or stream URL
            sample_rate: Extract 1 frame every N frames
        """
        
        cap = cv2.VideoCapture(video_source)
        
        if not cap.isOpened():
            raise Exception(f"Failed to open video: {video_source}")
        
        print(f"📹 Extracting frames from: {video_source}")
        print(f"   Sample rate: 1 frame every {sample_rate} frames")
        
        frame_num = 0
        
        try:
            while True:
                ret, frame = cap.read()
                
                if not ret:
                    break
                
                if frame_num % sample_rate == 0:
                    event = self.process_frame(frame)
                    
                    if event['violations']:
                        print(f"⚠️  Frame {self.frame_count}: {len(event['violations'])} violations")
                    
                    if self.frame_count % 10 == 0:
                        print(f"✓ Processed {self.frame_count} frames")
                
                frame_num += 1
                
        except KeyboardInterrupt:
            print("\n⏹️  Stopped")
        finally:
            cap.release()
            self.producer.flush()
            print(f"✅ Extracted {self.frame_count} frames")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: frame_extractor.py <bootstrap_servers> <video_source> <sample_rate>")
        sys.exit(1)
    
    extractor = FrameExtractor(sys.argv[1])
    extractor.extract_from_video(sys.argv[2], int(sys.argv[3]))
