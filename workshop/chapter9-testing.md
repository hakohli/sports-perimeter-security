# Chapter 9: Testing & Validation

**Duration**: 45 minutes

## Objectives
- Test complete end-to-end flow
- Validate violation detection accuracy
- Verify data storage and alerts
- Troubleshoot common issues

---

## Testing Strategy

```
1. Unit Tests (Individual components)
   ↓
2. Integration Tests (Components together)
   ↓
3. End-to-End Tests (Complete flow)
   ↓
4. Validation (Accuracy check)
```

---

## Test Video Setup

### Download Test Video

```bash
# Download sample soccer video
aws s3 cp s3://sports-security-test-videos/soccer_sample.mp4 .

# Verify download
ls -lh soccer_sample.mp4
```

**Expected**: ~26MB video file

---

## Unit Tests

### Test 1: Frame Extraction

```python
from frame_extractor import extract_frames

def test_frame_extraction():
    """Test frame extraction"""
    
    frames = extract_frames('soccer_sample.mp4', num_frames=5)
    
    assert len(frames) == 5, f"Expected 5 frames, got {len(frames)}"
    assert frames[0].shape[2] == 3, "Frame should be RGB"
    
    print("✅ Frame extraction test passed")

test_frame_extraction()
```

### Test 2: Bedrock API

```python
import boto3
import json

def test_bedrock_api():
    """Test Bedrock connection"""
    
    bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
    
    response = bedrock.invoke_model(
        modelId='us.anthropic.claude-3-5-sonnet-20241022-v2:0',
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 100,
            "messages": [{
                "role": "user",
                "content": "Say 'test successful'"
            }]
        })
    )
    
    result = json.loads(response['body'].read())
    text = result['content'][0]['text']
    
    assert 'test successful' in text.lower()
    print("✅ Bedrock API test passed")

test_bedrock_api()
```

### Test 3: DynamoDB Storage

```python
import boto3
from datetime import datetime

def test_dynamodb_storage():
    """Test DynamoDB write/read"""
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('sports-violations')
    
    # Write test record
    test_id = f"test_{int(datetime.utcnow().timestamp())}"
    table.put_item(Item={
        'violation_id': test_id,
        'timestamp': datetime.utcnow().isoformat(),
        'player_name': 'Test Player',
        'type': 'test'
    })
    
    # Read back
    response = table.get_item(Key={'violation_id': test_id})
    assert 'Item' in response
    
    # Cleanup
    table.delete_item(Key={'violation_id': test_id})
    
    print("✅ DynamoDB storage test passed")

test_dynamodb_storage()
```

### Test 4: S3 Storage

```python
import boto3

def test_s3_storage():
    """Test S3 write/read"""
    
    s3 = boto3.client('s3', region_name='us-east-1')
    bucket = 'sports-security-evidence'
    
    # Write test file
    test_key = 'test/test_file.txt'
    s3.put_object(
        Bucket=bucket,
        Key=test_key,
        Body=b'Test content'
    )
    
    # Read back
    response = s3.get_object(Bucket=bucket, Key=test_key)
    content = response['Body'].read()
    assert content == b'Test content'
    
    # Cleanup
    s3.delete_object(Bucket=bucket, Key=test_key)
    
    print("✅ S3 storage test passed")

test_s3_storage()
```

---

## Integration Tests

### Test 5: Frame Analysis Pipeline

```python
from frame_extractor import extract_frames
from analyze_frame import analyze_frame_for_violations, validate_analysis

def test_analysis_pipeline():
    """Test frame extraction + analysis"""
    
    # Extract frame
    frames = extract_frames('soccer_sample.mp4', num_frames=1)
    frame = frames[0]
    
    # Analyze
    analysis = analyze_frame_for_violations(frame)
    
    # Validate structure
    assert 'valid' in analysis
    assert 'confidence' in analysis
    assert 'subject_type' in analysis
    
    # Validate
    validated = validate_analysis(analysis)
    
    print(f"✅ Analysis pipeline test passed")
    print(f"   Valid: {validated['valid']}")
    print(f"   Confidence: {validated['confidence']}")

test_analysis_pipeline()
```

### Test 6: Storage Pipeline

```python
from store_violation import store_violation
import cv2

def test_storage_pipeline():
    """Test violation storage (DynamoDB + S3)"""
    
    # Create test violation
    analysis = {
        'player_name': 'Test Player',
        'player_number': '99',
        'team': 'Test Team',
        'violation_type': 'test',
        'zone': 'test_zone',
        'severity': 'info',
        'confidence': 1.0,
        'subject_type': 'player',
        'explanation': 'Test violation',
        'action': 'Test action'
    }
    
    # Create test frame
    frame = cv2.imread('test_frame.jpg')
    _, frame_bytes = cv2.imencode('.jpg', frame)
    
    # Store
    violation_id = store_violation(analysis, frame_bytes.tobytes())
    
    # Verify in DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('sports-violations')
    response = table.get_item(Key={'violation_id': violation_id})
    
    assert 'Item' in response
    print(f"✅ Storage pipeline test passed")
    print(f"   Violation ID: {violation_id}")

test_storage_pipeline()
```

---

## End-to-End Test

### Complete System Test

Run the provided test script:

```bash
python3 test_solution.py
```

**What it does**:
1. ✅ Extracts 10 frames from video
2. ✅ Analyzes each frame with Bedrock
3. ✅ Validates 100% confidence requirement
4. ✅ Filters player-only violations
5. ✅ Stores violations in DynamoDB
6. ✅ Saves evidence to S3
7. ✅ Sends SNS alerts (if severity >= violation)

**Expected Output**:
```
============================================================
Sports Perimeter Security - Test Solution
============================================================

📹 Extracting frames from video...
✓ Extracted 10 frames

🔍 Analyzing frames with Bedrock...

Frame 1/10:
  ⚪ No violation detected

Frame 2/10:
  ✅ Violation detected: perimeter_breach
  Player: Cristiano Ronaldo (#7)
  Team: Home Team
  Confidence: 1.0

Frame 3/10:
  ❌ Rejected: Confidence < 100%

...

============================================================
Test Results
============================================================
Frames analyzed: 10
Violations detected: 4
Violations stored: 4
Alerts sent: 2

✓ Test completed successfully!
============================================================
```

---

## Validation Tests

### Test 7: Accuracy Validation

```python
def validate_accuracy():
    """Validate detection accuracy"""
    
    # Known violations in test video
    ground_truth = [
        {'frame': 2, 'type': 'perimeter_breach', 'player': 'Ronaldo'},
        {'frame': 5, 'type': 'perimeter_breach', 'player': 'Messi'},
        {'frame': 7, 'type': 'equipment', 'player': 'Mbappe'},
        {'frame': 9, 'type': 'perimeter_breach', 'player': 'Salah'}
    ]
    
    # Run detection
    violations = process_video('soccer_sample.mp4', num_frames=10)
    
    # Calculate metrics
    detected = len(violations)
    expected = len(ground_truth)
    
    accuracy = detected / expected if expected > 0 else 0
    
    print(f"✅ Accuracy validation:")
    print(f"   Expected: {expected}")
    print(f"   Detected: {detected}")
    print(f"   Accuracy: {accuracy:.1%}")
    
    assert accuracy >= 0.8, "Accuracy below 80%"

validate_accuracy()
```

### Test 8: False Positive Check

```python
def test_false_positives():
    """Ensure no false positives"""
    
    # Test with clean video (no violations)
    violations = process_video('clean_game.mp4', num_frames=10)
    
    assert len(violations) == 0, f"False positives detected: {len(violations)}"
    print("✅ No false positives")

# Note: Requires clean test video
```

### Test 9: Player Filtering

```python
def test_player_filtering():
    """Verify only players are detected"""
    
    violations = process_video('soccer_sample.mp4', num_frames=10)
    
    for v in violations:
        assert v['analysis']['subject_type'] == 'player', \
            f"Non-player detected: {v['analysis']['subject_type']}"
    
    print("✅ Player filtering working correctly")

test_player_filtering()
```

---

## Verification Checklist

### Check DynamoDB

```bash
# Count violations
aws dynamodb scan \
  --table-name sports-violations \
  --select COUNT

# View recent violations
aws dynamodb scan \
  --table-name sports-violations \
  --max-items 5
```

### Check S3

```bash
# List evidence folders
aws s3 ls s3://sports-security-evidence/violations/ --recursive

# Count evidence files
aws s3 ls s3://sports-security-evidence/violations/ --recursive | wc -l
```

### Check SNS

```bash
# Check email for alerts
# Should have received 2-4 alerts

# View SNS metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/SNS \
  --metric-name NumberOfMessagesPublished \
  --dimensions Name=TopicName,Value=sports-security-alerts \
  --start-time 2026-01-26T00:00:00Z \
  --end-time 2026-01-26T23:59:59Z \
  --period 3600 \
  --statistics Sum
```

---

## Troubleshooting Guide

### Issue 1: No Violations Detected

**Symptoms**: All frames return `valid: false`

**Causes**:
- Video quality too low
- Confidence threshold too high
- Wrong sport/context

**Solutions**:
```python
# Lower confidence threshold (testing only)
def validate_analysis(analysis, threshold=0.95):
    if analysis.get('confidence', 0) < threshold:
        analysis['valid'] = False

# Add debug logging
print(f"Analysis: {json.dumps(analysis, indent=2)}")
```

### Issue 2: Too Many False Positives

**Symptoms**: Non-violations being detected

**Causes**:
- Confidence threshold too low
- Player filtering not working
- Prompt not specific enough

**Solutions**:
```python
# Enforce strict requirements
if analysis.get('confidence', 0) < 1.0:
    analysis['valid'] = False

if analysis.get('subject_type') != 'player':
    analysis['valid'] = False
```

### Issue 3: Bedrock Throttling

**Symptoms**: `ThrottlingException` errors

**Causes**:
- Too many API calls
- Rate limit exceeded

**Solutions**:
```python
import time

# Add delay between calls
for frame in frames:
    analysis = analyze_frame(frame)
    time.sleep(1)  # 1 second delay

# Or use exponential backoff
from botocore.exceptions import ClientError

def analyze_with_retry(frame, max_retries=3):
    for i in range(max_retries):
        try:
            return analyze_frame(frame)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ThrottlingException':
                wait = 2 ** i
                print(f"Throttled, waiting {wait}s...")
                time.sleep(wait)
            else:
                raise
```

### Issue 4: S3 Upload Fails

**Symptoms**: `AccessDenied` or `NoSuchBucket`

**Causes**:
- Bucket doesn't exist
- Wrong region
- No permissions

**Solutions**:
```bash
# Verify bucket exists
aws s3 ls s3://sports-security-evidence/

# Check region
aws s3api get-bucket-location --bucket sports-security-evidence

# Check permissions
aws s3api get-bucket-policy --bucket sports-security-evidence
```

---

## Performance Benchmarks

### Expected Performance

| Metric | Value |
|--------|-------|
| Frame extraction | ~1 second/10 frames |
| Bedrock analysis | ~2 seconds/frame |
| DynamoDB write | ~100ms |
| S3 upload | ~200ms |
| **Total** | **~25 seconds/10 frames** |

### Optimization Tips

```python
# Process frames in parallel
from concurrent.futures import ThreadPoolExecutor

def process_frames_parallel(frames):
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(analyze_frame_for_violations, frames)
    return list(results)

# Reduces time to ~5 seconds for 10 frames
```

---

## Hands-On Exercise

### Exercise 1: Add Test Coverage

Create comprehensive test suite:

```python
def run_all_tests():
    """Run complete test suite"""
    
    tests = [
        test_frame_extraction,
        test_bedrock_api,
        test_dynamodb_storage,
        test_s3_storage,
        test_analysis_pipeline,
        test_storage_pipeline,
        validate_accuracy,
        test_player_filtering
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Tests passed: {passed}/{len(tests)}")
    print(f"Tests failed: {failed}/{len(tests)}")

run_all_tests()
```

### Exercise 2: Load Testing

Test with larger video:

```python
# Process 100 frames instead of 10
violations = process_video('soccer_sample.mp4', num_frames=100)

# Measure performance
import time
start = time.time()
violations = process_video('soccer_sample.mp4', num_frames=100)
duration = time.time() - start

print(f"Processed 100 frames in {duration:.1f} seconds")
print(f"Average: {duration/100:.2f} seconds/frame")
```

---

## Chapter 9 Checklist

- [ ] Ran all unit tests
- [ ] Ran integration tests
- [ ] Completed end-to-end test
- [ ] Validated accuracy
- [ ] Verified data in DynamoDB
- [ ] Verified evidence in S3
- [ ] Received SNS alerts
- [ ] Troubleshot any issues

---

## Next: Chapter 10 - Production Deployment

Final chapter! We'll prepare the system for production use. →
