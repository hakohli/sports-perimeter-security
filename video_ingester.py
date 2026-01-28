"""
Stream video to Kinesis Video Streams
Replaces OpenCV frame extraction with KVS streaming
"""

import boto3
import cv2
import time
from datetime import datetime

class VideoStreamer:
    """Stream video to Kinesis Video Streams"""
    
    def __init__(self, stream_name='sports-security-video-stream'):
        self.kvs = boto3.client('kinesisvideo', region_name='us-east-1')
        self.stream_name = stream_name
        self.stream_arn = None
        
    def get_stream_endpoint(self):
        """Get KVS data endpoint"""
        response = self.kvs.get_data_endpoint(
            StreamName=self.stream_name,
            APIName='PUT_MEDIA'
        )
        return response['DataEndpoint']
    
    def stream_video(self, video_source):
        """
        Stream video to KVS
        
        Args:
            video_source: Video file path or camera index (0 for webcam)
        """
        print(f"📹 Streaming video to KVS: {self.stream_name}")
        
        # For production, use GStreamer or AWS KVS Producer SDK
        # This is a simplified example
        
        print("""
        To stream video to KVS, use one of these methods:
        
        1. GStreamer (Recommended):
           gst-launch-1.0 -v filesrc location=video.mp4 ! \\
             decodebin ! videoconvert ! x264enc ! h264parse ! \\
             kvssink stream-name=sports-security-video-stream
        
        2. AWS KVS Producer SDK:
           https://github.com/awslabs/amazon-kinesis-video-streams-producer-sdk-cpp
        
        3. RTSP Camera:
           gst-launch-1.0 rtspsrc location=rtsp://camera-ip ! \\
             rtph264depay ! h264parse ! \\
             kvssink stream-name=sports-security-video-stream
        """)
        
    def stream_from_file(self, video_file):
        """Stream from video file using OpenCV (for testing)"""
        cap = cv2.VideoCapture(video_file)
        
        if not cap.isOpened():
            print(f"❌ Cannot open video: {video_file}")
            return
        
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        frame_count = 0
        
        print(f"📹 Streaming {video_file} at {fps} FPS")
        print("⚠️  Note: For production, use GStreamer or KVS Producer SDK")
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # In production, frames would be sent to KVS
            # Here we just simulate the streaming
            if frame_count % fps == 0:  # Log every second
                print(f"  Frame {frame_count} ({frame_count//fps}s)")
            
            time.sleep(1/fps)  # Maintain FPS
        
        cap.release()
        print(f"✅ Streaming complete: {frame_count} frames")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python video_ingester.py <video_file>")
        print("\nFor production streaming, use GStreamer:")
        print("  gst-launch-1.0 filesrc location=video.mp4 ! \\")
        print("    decodebin ! videoconvert ! x264enc ! h264parse ! \\")
        print("    kvssink stream-name=sports-security-video-stream")
        sys.exit(1)
    
    streamer = VideoStreamer()
    streamer.stream_from_file(sys.argv[1])
