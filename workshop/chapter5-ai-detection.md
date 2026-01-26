# Chapter 5: AI-Powered Violation Detection

**Duration**: 45 minutes

## Objectives
- Combine video frames with Bedrock AI
- Classify violations automatically
- Implement 100% confidence requirement
- Filter player-only violations

---

## The Detection Pipeline

```
Frame (image)
    ↓
Convert to base64
    ↓
Send to Bedrock with prompt
    ↓
Claude analyzes image
    ↓
Returns JSON analysis
    ↓
Validate confidence = 1.0
    ↓
Validate subject_type = "player"
    ↓
Store violation
```

---

## Bedrock Vision API

Claude can analyze images! Send image + text prompt:

```python
import boto3
import json
import base64

bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

def analyze_frame(frame_base64, context):
    """Analyze frame with Bedrock"""
    
    response = bedrock.invoke_model(
        modelId='us.anthropic.claude-3-5-sonnet-20241022-v2:0',
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "messages": [{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": frame_base64
                        }
                    },
                    {
                        "type": "text",
                        "text": f"Analyze this frame: {context}"
                    }
                ]
            }]
        })
    )
    
    result = json.loads(response['body'].read())
    return result['content'][0]['text']
```

---

## The Violation Detection Prompt

Here's our complete prompt:

```python
prompt = f"""Analyze this sports game frame for potential violations.

Context:
- Sport: Soccer
- Zone: Perimeter/Sideline
- Frame timestamp: {timestamp}

CRITICAL REQUIREMENTS:
1. ONLY report violations by PLAYERS (ignore audience, staff, coaches, referees)
2. ONLY return confidence: 1.0 if you are 100% certain
3. Return confidence: 0.0 for anything else
4. Identify player by name and jersey number if visible

Analyze for:
- Perimeter breach (player outside playing area)
- Unauthorized entry (non-player on field)
- Equipment violations
- Dangerous play

Return ONLY valid JSON:
{{
  "valid": true/false,
  "violation_type": "perimeter_breach|equipment|dangerous_play|none",
  "severity": "info|warning|violation|critical",
  "player_name": "Player Name or Unknown",
  "player_number": "Jersey number or null",
  "team": "Home Team|Away Team|Unknown",
  "zone": "sideline|endline|penalty_box|etc",
  "action": "Recommended action",
  "explanation": "Brief explanation",
  "confidence": 1.0 or 0.0,
  "subject_type": "player" or "non-player"
}}"""
```

---

## Hands-On: Analyze Your First Frame

Create `analyze_frame.py`:

```python
import boto3
import json
import base64
import cv2

def analyze_frame_for_violations(frame):
    """Analyze frame with Bedrock"""
    
    # Convert to base64
    success, buffer = cv2.imencode('.jpg', frame)
    frame_base64 = base64.b64encode(buffer).decode('utf-8')
    
    # Prepare prompt
    prompt = """Analyze this soccer frame for violations.

CRITICAL: Only report if:
1. Subject is a PLAYER
2. You are 100% certain (confidence: 1.0)

Return JSON with: valid, violation_type, player_name, 
player_number, team, confidence, subject_type, explanation"""
    
    # Call Bedrock
    bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
    
    response = bedrock.invoke_model(
        modelId='us.anthropic.claude-3-5-sonnet-20241022-v2:0',
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "image", "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": frame_base64
                    }},
                    {"type": "text", "text": prompt}
                ]
            }]
        })
    )
    
    result = json.loads(response['body'].read())
    analysis = json.loads(result['content'][0]['text'])
    
    return analysis

# Test it
frame = cv2.imread('test_frame.jpg')
result = analyze_frame_for_violations(frame)
print(json.dumps(result, indent=2))
```

Run it:
```bash
python3 analyze_frame.py
```

**Expected Output**:
```json
{
  "valid": true,
  "violation_type": "perimeter_breach",
  "player_name": "Cristiano Ronaldo",
  "player_number": "7",
  "team": "Home Team",
  "confidence": 1.0,
  "subject_type": "player",
  "explanation": "Player #7 crossed sideline boundary"
}
```

---

## Enforcing 100% Confidence

**Why 100% confidence?**
- Avoid false positives
- Only report when AI is certain
- Maintain system credibility

### Implementation

```python
def validate_analysis(analysis):
    """Enforce strict requirements"""
    
    # Requirement 1: Must be 100% confident
    if analysis.get('confidence', 0) < 1.0:
        analysis['valid'] = False
        analysis['confidence'] = 0.0
        print("❌ Rejected: Confidence < 100%")
        return analysis
    
    # Requirement 2: Must be a player
    if analysis.get('subject_type') != 'player':
        analysis['valid'] = False
        analysis['confidence'] = 0.0
        print("❌ Rejected: Not a player")
        return analysis
    
    # Requirement 3: Must have violation type
    if not analysis.get('violation_type') or analysis['violation_type'] == 'none':
        analysis['valid'] = False
        print("❌ Rejected: No violation detected")
        return analysis
    
    print("✅ Valid violation detected!")
    return analysis

# Use it
analysis = analyze_frame_for_violations(frame)
validated = validate_analysis(analysis)

if validated['valid']:
    print(f"Violation: {validated['violation_type']}")
    print(f"Player: {validated['player_name']}")
else:
    print("No valid violation")
```

---

## Player Identification

Claude can identify players from jerseys!

### What Claude Sees

```python
# Claude analyzes:
# - Jersey number
# - Team colors
# - Player position
# - Context clues

# Returns:
{
  "player_name": "Cristiano Ronaldo",  # If recognizable
  "player_number": "7",
  "team": "Home Team"  # Based on jersey color
}
```

### Handling Unknown Players

```python
def normalize_player_info(analysis):
    """Handle missing player info"""
    
    if not analysis.get('player_name'):
        analysis['player_name'] = f"Player #{analysis.get('player_number', 'Unknown')}"
    
    if not analysis.get('team'):
        analysis['team'] = 'Unknown Team'
    
    return analysis
```

---

## Hands-On: Process Multiple Frames

Create `batch_analyze.py`:

```python
import cv2
from frame_extractor import extract_frames
from analyze_frame import analyze_frame_for_violations, validate_analysis

def process_video(video_path, num_frames=10):
    """Process video and detect violations"""
    
    print(f"Extracting {num_frames} frames...")
    frames = extract_frames(video_path, num_frames)
    
    violations = []
    
    for i, frame in enumerate(frames):
        print(f"\nAnalyzing frame {i+1}/{len(frames)}...")
        
        # Analyze frame
        analysis = analyze_frame_for_violations(frame)
        
        # Validate
        validated = validate_analysis(analysis)
        
        # Store if valid
        if validated['valid']:
            violations.append({
                'frame_number': i,
                'analysis': validated
            })
            print(f"✅ Violation detected: {validated['violation_type']}")
        else:
            print(f"⚪ No violation")
    
    print(f"\n{'='*50}")
    print(f"Total violations: {len(violations)}")
    print(f"{'='*50}")
    
    return violations

# Test it
violations = process_video('soccer_sample.mp4', num_frames=10)

# Print summary
for v in violations:
    print(f"\nFrame {v['frame_number']}:")
    print(f"  Type: {v['analysis']['violation_type']}")
    print(f"  Player: {v['analysis']['player_name']}")
    print(f"  Team: {v['analysis']['team']}")
```

Run it:
```bash
python3 batch_analyze.py
```

---

## Violation Classification

### Types of Violations

**1. Perimeter Breach**
- Player leaves playing area
- Severity: Warning
- Action: Return to field

**2. Equipment Violation**
- Missing/incorrect equipment
- Severity: Info
- Action: Correct equipment

**3. Dangerous Play**
- Unsafe actions
- Severity: Critical
- Action: Stop play, issue card

**4. Unauthorized Entry**
- Non-player on field
- Severity: Violation
- Action: Remove from field

### Severity Levels

```python
SEVERITY_LEVELS = {
    'info': 1,      # FYI only
    'warning': 2,   # Minor issue
    'violation': 3, # Rule violation
    'critical': 4   # Safety issue
}

def should_alert(severity):
    """Determine if SNS alert needed"""
    return SEVERITY_LEVELS.get(severity, 0) >= 3
```

---

## Hands-On Exercise

### Exercise 1: Custom Violation Types

Add support for "offside" violations:

```python
prompt = f"""...
Analyze for:
- Perimeter breach
- Equipment violations
- Dangerous play
- Offside position  # NEW

Return JSON with:
  "violation_type": "perimeter_breach|equipment|dangerous_play|offside|none"
..."""
```

### Exercise 2: Confidence Threshold

Test with 95% confidence instead of 100%:

```python
def validate_analysis(analysis, threshold=0.95):
    if analysis.get('confidence', 0) < threshold:
        analysis['valid'] = False
    return analysis
```

**Question**: How many more violations are detected?

### Exercise 3: Multi-Sport Detection

Modify for basketball:

```python
prompt = f"""Analyze this BASKETBALL frame for violations.

Analyze for:
- Lane violations (3-second rule)
- Out of bounds
- Traveling
- Double dribble

Return JSON..."""
```

---

## Real-World Considerations

### False Positives

**Problem**: AI might misidentify violations

**Solutions**:
1. ✅ 100% confidence requirement
2. ✅ Player-only filtering
3. ✅ Human review for critical violations
4. ✅ Confidence scoring

### Performance

**Challenge**: Processing 1,800 frames takes time

**Optimizations**:
1. Sample frames (every 30th)
2. Parallel processing
3. Early exit (stop if violation found)
4. Batch API calls

### Cost Management

```python
# Cost per frame
INPUT_TOKENS = 200  # Prompt
IMAGE_TOKENS = 1000  # Image
OUTPUT_TOKENS = 100  # Response

cost_per_frame = (
    (INPUT_TOKENS + IMAGE_TOKENS) * 0.003 / 1000 +
    OUTPUT_TOKENS * 0.015 / 1000
)

print(f"Cost per frame: ${cost_per_frame:.4f}")
# ~$0.005 per frame
```

---

## Chapter 5 Checklist

- [ ] Analyzed frame with Bedrock
- [ ] Implemented 100% confidence check
- [ ] Filtered player-only violations
- [ ] Processed multiple frames
- [ ] Understand violation types
- [ ] Completed exercises

---

## Next: Chapter 6 - Data Storage

We'll store violations in DynamoDB and evidence in S3!

**Preview**: Organize violations by timestamp, store evidence images, and query violations. →
