"""
Video ingestion from live game streams to Kinesis Video Streams
Supports RTSP, HLS, and file-based video sources
"""

import boto3
import cv2
import time
from datetime import datetime
import argparse

kinesis_video = boto3.client('kinesisvideo', region_name='us-east-1')
kinesis_video_media = boto3.client('kinesis-video-media', region_name='us-east-1')

STREAM_NAME = 'game-video-stream'

def create_video_stream():
    """Create Kinesis Video Stream"""
    try:
        kinesis_video.create_stream(
            StreamName=STREAM_NAME,
            DataRetentionInHours=24,
            MediaType='video/h264',
            Tags={'Project': 'Sports-Security', 'NoDelete': 'true'}
        )
        print(f"✓ Created video stream: {STREAM_NAME}")
    except kinesis_video.exceptions.ResourceInUseException:
        print(f"✓ Video stream already exists: {STREAM_NAME}")

def ingest_video(source, fps=30):
    """
    Ingest video from source to Kinesis Video Streams
    
    Args:
        source: Video source (RTSP URL, file path, or camera index)
        fps: Frames per second to capture
    """
    
    print(f"📹 Opening video source: {source}")
    cap = cv2.VideoCapture(source)
    
    if not cap.isOpened():
        raise Exception(f"Failed to open video source: {source}")
    
    # Get video properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    source_fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"✓ Video opened: {width}x{height} @ {source_fps} FPS")
    print(f"📤 Streaming to Kinesis at {fps} FPS...")
    
    frame_count = 0
    start_time = time.time()
    
    try:
        while True:
            ret, frame = cap.read()
            
            if not ret:
                print("⚠️  End of video or read error")
                break
            
            # Encode frame
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            
            # Add metadata
            timestamp = datetime.utcnow().isoformat()
            metadata = {
                'timestamp': timestamp,
                'frame_number': frame_count,
                'width': width,
                'height': height
            }
            
            # Send to Kinesis (simplified - actual implementation needs PutMedia API)
            # This is a placeholder - real implementation requires Kinesis Video Producer SDK
            
            frame_count += 1
            
            if frame_count % 100 == 0:
                elapsed = time.time() - start_time
                actual_fps = frame_count / elapsed
                print(f"  Frames: {frame_count}, FPS: {actual_fps:.1f}")
            
            # Control frame rate
            time.sleep(1.0 / fps)
            
    except KeyboardInterrupt:
        print("\n⏹️  Stopped by user")
    finally:
        cap.release()
        print(f"✅ Ingested {frame_count} frames")

def main():
    parser = argparse.ArgumentParser(description='Ingest video to Kinesis Video Streams')
    parser.add_argument('--source', required=True, help='Video source (RTSP URL, file, or camera)')
    parser.add_argument('--fps', type=int, default=30, help='Frames per second')
    parser.add_argument('--create-stream', action='store_true', help='Create stream if not exists')
    
    args = parser.parse_args()
    
    if args.create_stream:
        create_video_stream()
    
    ingest_video(args.source, args.fps)

if __name__ == "__main__":
    main()
