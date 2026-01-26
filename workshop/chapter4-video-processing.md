# Chapter 4: Video Processing with OpenCV

**Duration**: 45 minutes

## Objectives
- Extract frames from video files
- Detect perimeter zones
- Identify player positions
- Prepare frames for AI analysis

---

## Why Video Processing?

**Challenge**: AI models can't analyze video directly
**Solution**: Extract individual frames (images) and analyze each one

### Video → Frames
```
Video (30 fps, 60 seconds)
    ↓
1,800 frames (images)
    ↓
Sample every 30 frames
    ↓
60 frames to analyze
```

---

## OpenCV Basics

**OpenCV** = Open Computer Vision library

### Installation
```bash
pip install opencv-python
```

### Basic Operations
```python
import cv2

# Read video
video = cv2.VideoCapture('video.mp4')

# Get properties
fps = video.get(cv2.CAP_PROP_FPS)
frame_count = video.get(cv2.CAP_PROP_FRAME_COUNT)

# Read frame
success, frame = video.read()

# Release video
video.release()
```

---

## Hands-On: Extract Frames

Create `extract_frames.py`:

```python
import cv2
import os

def extract_frames(video_path, output_dir, sample_rate=30):
    """Extract frames from video"""
    
    os.makedirs(output_dir, exist_ok=True)
    
    video = cv2.VideoCapture(video_path)
    fps = video.get(cv2.CAP_PROP_FPS)
    frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"Video: {fps} fps, {frame_count} frames")
    
    frame_num = 0
    saved_count = 0
    
    while True:
        success, frame = video.read()
        if not success:
            break
            
        # Sample every Nth frame
        if frame_num % sample_rate == 0:
            output_path = f"{output_dir}/frame_{frame_num:06d}.jpg"
            cv2.imwrite(output_path, frame)
            saved_count += 1
            print(f"Saved frame {frame_num}")
        
        frame_num += 1
    
    video.release()
    print(f"Extracted {saved_count} frames")

# Test it
extract_frames('test_video.mp4', 'frames', sample_rate=30)
```

Run it:
```bash
python3 extract_frames.py
```

**Expected**: Creates `frames/` directory with extracted images

---

## Perimeter Detection

### What is a Perimeter?

In sports, the **perimeter** is the boundary of the playing field:
- Soccer: Sidelines and goal lines
- Basketball: Court boundaries
- Baseball: Foul lines

### Detection Strategy

1. **Define zones** (coordinates)
2. **Detect players** (position)
3. **Check if player crosses** boundary

### Simple Zone Detection

```python
def is_in_zone(x, y, zone):
    """Check if point (x,y) is in zone"""
    return (zone['x_min'] <= x <= zone['x_max'] and
            zone['y_min'] <= y <= zone['y_max'])

# Define sideline zone
sideline_zone = {
    'x_min': 0,
    'x_max': 100,
    'y_min': 0,
    'y_max': 50
}

# Check player position
player_x, player_y = 75, 25
if is_in_zone(player_x, player_y, sideline_zone):
    print("Player in sideline zone!")
```

---

## Hands-On: Frame Extractor

Review `frame_extractor.py` from the repository:

```bash
cat frame_extractor.py
```

**Key Functions**:

### 1. Extract Frames
```python
def extract_frames(video_path, num_frames=10):
    """Extract evenly spaced frames"""
    video = cv2.VideoCapture(video_path)
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Calculate frame indices
    indices = [int(i * total_frames / num_frames) 
               for i in range(num_frames)]
    
    frames = []
    for idx in indices:
        video.set(cv2.CAP_PROP_POS_FRAMES, idx)
        success, frame = video.read()
        if success:
            frames.append(frame)
    
    video.release()
    return frames
```

### 2. Detect Perimeter Breach
```python
def detect_perimeter_breach(frame):
    """Detect if player is near perimeter"""
    height, width = frame.shape[:2]
    
    # Define perimeter zones (10% from edges)
    margin = int(width * 0.1)
    
    zones = {
        'sideline': (0, margin, 0, height),
        'endline': (0, width, 0, margin)
    }
    
    # Simple detection: check edge pixels
    # (In production, use object detection)
    
    return {
        'breach_detected': True,
        'zone': 'sideline',
        'confidence': 0.85
    }
```

---

## Test Frame Extraction

### Step 1: Download Test Video

```bash
# Use sample soccer video
aws s3 cp s3://sports-security-test-videos/soccer_sample.mp4 .
```

### Step 2: Extract Frames

```python
from frame_extractor import extract_frames

frames = extract_frames('soccer_sample.mp4', num_frames=10)
print(f"Extracted {len(frames)} frames")

# Save first frame
import cv2
cv2.imwrite('test_frame.jpg', frames[0])
```

### Step 3: View Frame

```bash
open test_frame.jpg  # macOS
# or
xdg-open test_frame.jpg  # Linux
```

---

## Preparing Frames for Bedrock

Bedrock requires images in **base64** format:

```python
import base64
import cv2

def frame_to_base64(frame):
    """Convert OpenCV frame to base64"""
    # Encode as JPEG
    success, buffer = cv2.imencode('.jpg', frame)
    
    # Convert to base64
    jpg_as_text = base64.b64encode(buffer).decode('utf-8')
    
    return jpg_as_text

# Test it
frame = frames[0]
base64_image = frame_to_base64(frame)
print(f"Base64 length: {len(base64_image)}")
```

---

## Hands-On Exercise

### Exercise 1: Extract More Frames

Modify to extract 30 frames instead of 10:

```python
frames = extract_frames('soccer_sample.mp4', num_frames=30)
```

How does this affect:
- Processing time?
- Storage space?
- Detection accuracy?

### Exercise 2: Frame Quality

Test different JPEG quality levels:

```python
def frame_to_base64(frame, quality=85):
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    success, buffer = cv2.imencode('.jpg', frame, encode_param)
    return base64.b64encode(buffer).decode('utf-8')

# Test different qualities
for quality in [50, 75, 95]:
    b64 = frame_to_base64(frame, quality)
    print(f"Quality {quality}: {len(b64)} bytes")
```

**Question**: What's the optimal quality for cost vs accuracy?

### Exercise 3: Zone Detection

Implement custom zone detection:

```python
def detect_custom_zone(frame, zone_name):
    """Detect if activity in custom zone"""
    height, width = frame.shape[:2]
    
    zones = {
        'penalty_box': (width//4, 3*width//4, 0, height//3),
        'midfield': (width//3, 2*width//3, height//3, 2*height//3),
        'goal_area': (width//2-50, width//2+50, 0, 100)
    }
    
    if zone_name not in zones:
        return None
    
    x1, x2, y1, y2 = zones[zone_name]
    zone_frame = frame[y1:y2, x1:x2]
    
    # Simple activity detection
    # (In production, use object detection)
    
    return {
        'zone': zone_name,
        'activity_detected': True
    }
```

---

## Video Processing Pipeline

Here's the complete flow:

```
1. Download video from S3
   ↓
2. Extract frames (every 30th frame)
   ↓
3. Detect perimeter zones
   ↓
4. Convert frames to base64
   ↓
5. Send to Bedrock for analysis
   ↓
6. Store violations in DynamoDB
   ↓
7. Save evidence to S3
```

---

## Performance Optimization

### Frame Sampling Strategy

**Option 1: Fixed Rate**
```python
# Every 30 frames (1 per second at 30fps)
sample_rate = 30
```

**Option 2: Adaptive**
```python
# More frames when action detected
if action_detected:
    sample_rate = 10  # 3 per second
else:
    sample_rate = 60  # 0.5 per second
```

**Option 3: Key Frames Only**
```python
# Only extract key frames (scene changes)
# Requires more complex logic
```

### Memory Management

```python
# Process in batches
batch_size = 10

for i in range(0, len(frames), batch_size):
    batch = frames[i:i+batch_size]
    process_batch(batch)
    # Batch processed, memory freed
```

---

## Common Issues

**Issue**: Video won't open
```python
video = cv2.VideoCapture(video_path)
if not video.isOpened():
    print(f"Error: Cannot open {video_path}")
    # Check file exists and format is supported
```

**Issue**: Out of memory
```python
# Don't load all frames at once
# Process one at a time
while True:
    success, frame = video.read()
    if not success:
        break
    process_frame(frame)
    # Frame processed, memory freed
```

**Issue**: Slow processing
```python
# Resize frames before processing
frame = cv2.resize(frame, (640, 480))
# Smaller = faster processing
```

---

## Chapter 4 Checklist

- [ ] OpenCV installed
- [ ] Extracted frames from video
- [ ] Understand frame sampling
- [ ] Converted frames to base64
- [ ] Tested zone detection
- [ ] Completed exercises

---

## Next: Chapter 5 - AI Violation Detection

Now we'll combine video processing with Bedrock AI to detect violations!

**Preview**: We'll analyze frames with Claude and classify violations automatically. →
