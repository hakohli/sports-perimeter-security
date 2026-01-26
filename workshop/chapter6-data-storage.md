# Chapter 6: Data Storage Strategy

**Duration**: 30 minutes

## Objectives
- Store violations in DynamoDB
- Organize evidence in S3 by timestamp
- Create description files
- Query and retrieve violations

---

## Storage Architecture

```
Violation Detected
    ↓
┌─────────────────────────────────┐
│ DynamoDB: Metadata              │
│ - violation_id                  │
│ - timestamp                     │
│ - player_name                   │
│ - type, severity                │
│ - s3_evidence_path              │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ S3: Evidence Files              │
│ violations/                     │
│   2026-01-26/                   │
│     13-45-30/                   │
│       violation_123/            │
│         frame.jpg               │
│         description.txt         │
└─────────────────────────────────┘
```

---

## DynamoDB Schema

### Table: `sports-violations`

**Primary Key**: `violation_id` (String)

**Attributes**:
```python
{
    'violation_id': 'viol_1738000000123',
    'timestamp': '2026-01-26T13:45:30.123Z',
    'player_name': 'Cristiano Ronaldo',
    'player_number': '7',
    'team': 'Home Team',
    'type': 'perimeter_breach',
    'zone': 'sideline',
    'severity': 'warning',
    'confidence': '1.0',
    'subject_type': 'player',
    's3_evidence_path': 's3://bucket/violations/2026-01-26/13-45-30/viol_123/',
    'explanation': 'Player crossed sideline boundary'
}
```

**GSI**: `timestamp-index` (for time-based queries)

---

## S3 Organization

### Timestamp-Based Folders

```
s3://sports-security-evidence/
└── violations/
    └── 2026-01-26/          # Date folder
        ├── 13-45-30/        # Time folder
        │   └── viol_123/    # Violation ID
        │       ├── frame.jpg
        │       └── description.txt
        └── 14-22-15/
            └── viol_124/
                ├── frame.jpg
                └── description.txt
```

**Benefits**:
- Easy to browse by date
- Natural partitioning
- Simple cleanup (delete old dates)

---

## Hands-On: Store Violation

Create `store_violation.py`:

```python
import boto3
import json
from datetime import datetime
import time

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
s3 = boto3.client('s3', region_name='us-east-1')

BUCKET = 'sports-security-evidence'
TABLE = 'sports-violations'

def store_violation(analysis, frame_bytes):
    """Store violation in DynamoDB and S3"""
    
    # Generate IDs
    violation_id = f"viol_{int(time.time() * 1000)}"
    timestamp = datetime.utcnow()
    
    # Create S3 path
    date_folder = timestamp.strftime('%Y-%m-%d')
    time_folder = timestamp.strftime('%H-%M-%S')
    s3_prefix = f"violations/{date_folder}/{time_folder}/{violation_id}"
    
    # Store frame in S3
    s3.put_object(
        Bucket=BUCKET,
        Key=f"{s3_prefix}/frame.jpg",
        Body=frame_bytes,
        ContentType='image/jpeg'
    )
    
    # Create description file
    description = f"""Violation Report
================

Violation ID: {violation_id}
Timestamp: {timestamp.isoformat()}

Player Information:
- Name: {analysis['player_name']}
- Number: {analysis['player_number']}
- Team: {analysis['team']}

Violation Details:
- Type: {analysis['violation_type']}
- Zone: {analysis['zone']}
- Severity: {analysis['severity']}
- Confidence: {analysis['confidence']}

Explanation:
{analysis['explanation']}

Recommended Action:
{analysis['action']}
"""
    
    s3.put_object(
        Bucket=BUCKET,
        Key=f"{s3_prefix}/description.txt",
        Body=description.encode('utf-8'),
        ContentType='text/plain'
    )
    
    # Store in DynamoDB
    table = dynamodb.Table(TABLE)
    table.put_item(Item={
        'violation_id': violation_id,
        'timestamp': timestamp.isoformat(),
        'player_name': analysis['player_name'],
        'player_number': str(analysis['player_number']),
        'team': analysis['team'],
        'type': analysis['violation_type'],
        'zone': analysis['zone'],
        'severity': analysis['severity'],
        'confidence': str(analysis['confidence']),
        'subject_type': analysis['subject_type'],
        's3_evidence_path': f"s3://{BUCKET}/{s3_prefix}/",
        'explanation': analysis['explanation']
    })
    
    print(f"✅ Stored violation: {violation_id}")
    print(f"   S3: {s3_prefix}/")
    
    return violation_id

# Test it
import cv2
frame = cv2.imread('test_frame.jpg')
_, frame_bytes = cv2.imencode('.jpg', frame)

analysis = {
    'player_name': 'Test Player',
    'player_number': '10',
    'team': 'Home Team',
    'violation_type': 'perimeter_breach',
    'zone': 'sideline',
    'severity': 'warning',
    'confidence': 1.0,
    'subject_type': 'player',
    'explanation': 'Player crossed boundary',
    'action': 'Return to field'
}

violation_id = store_violation(analysis, frame_bytes.tobytes())
```

Run it:
```bash
python3 store_violation.py
```

---

## Query Violations

### Get All Violations

```python
def get_all_violations():
    """Get all violations from DynamoDB"""
    table = dynamodb.Table('sports-violations')
    response = table.scan()
    return response['Items']

violations = get_all_violations()
print(f"Total violations: {len(violations)}")
```

### Get Violations by Date

```python
def get_violations_by_date(date):
    """Get violations for specific date"""
    table = dynamodb.Table('sports-violations')
    
    response = table.scan(
        FilterExpression='begins_with(#ts, :date)',
        ExpressionAttributeNames={'#ts': 'timestamp'},
        ExpressionAttributeValues={':date': date}
    )
    
    return response['Items']

# Get today's violations
today = datetime.utcnow().strftime('%Y-%m-%d')
violations = get_violations_by_date(today)
print(f"Violations today: {len(violations)}")
```

### Get Specific Violation

```python
def get_violation(violation_id):
    """Get single violation"""
    table = dynamodb.Table('sports-violations')
    response = table.get_item(Key={'violation_id': violation_id})
    return response.get('Item')

violation = get_violation('viol_1738000000123')
print(json.dumps(violation, indent=2))
```

---

## Retrieve Evidence from S3

```python
def get_evidence(violation_id):
    """Download evidence files"""
    
    # Get violation metadata
    violation = get_violation(violation_id)
    s3_path = violation['s3_evidence_path']
    
    # Parse S3 path
    # s3://bucket/violations/2026-01-26/13-45-30/viol_123/
    parts = s3_path.replace('s3://', '').split('/')
    bucket = parts[0]
    prefix = '/'.join(parts[1:])
    
    # Download frame
    frame_key = f"{prefix}frame.jpg"
    s3.download_file(bucket, frame_key, 'evidence_frame.jpg')
    
    # Download description
    desc_key = f"{prefix}description.txt"
    response = s3.get_object(Bucket=bucket, Key=desc_key)
    description = response['Body'].read().decode('utf-8')
    
    print(f"✅ Downloaded evidence for {violation_id}")
    print(f"\n{description}")
    
    return 'evidence_frame.jpg', description

# Test it
get_evidence('viol_1738000000123')
```

---

## Hands-On Exercise

### Exercise 1: Query by Player

```python
def get_violations_by_player(player_name):
    """Get all violations for specific player"""
    table = dynamodb.Table('sports-violations')
    
    response = table.scan(
        FilterExpression='player_name = :name',
        ExpressionAttributeValues={':name': player_name}
    )
    
    return response['Items']

# Test it
violations = get_violations_by_player('Cristiano Ronaldo')
print(f"Violations by Ronaldo: {len(violations)}")
```

### Exercise 2: Query by Severity

```python
def get_critical_violations():
    """Get all critical violations"""
    table = dynamodb.Table('sports-violations')
    
    response = table.scan(
        FilterExpression='severity = :sev',
        ExpressionAttributeValues={':sev': 'critical'}
    )
    
    return response['Items']
```

### Exercise 3: Cleanup Old Violations

```python
def cleanup_old_violations(days_old=30):
    """Delete violations older than N days"""
    from datetime import timedelta
    
    cutoff = datetime.utcnow() - timedelta(days=days_old)
    cutoff_str = cutoff.strftime('%Y-%m-%d')
    
    # Query old violations
    table = dynamodb.Table('sports-violations')
    response = table.scan(
        FilterExpression='#ts < :cutoff',
        ExpressionAttributeNames={'#ts': 'timestamp'},
        ExpressionAttributeValues={':cutoff': cutoff_str}
    )
    
    # Delete from DynamoDB and S3
    for item in response['Items']:
        # Delete S3 evidence
        s3_path = item['s3_evidence_path']
        # ... delete S3 objects
        
        # Delete DynamoDB record
        table.delete_item(Key={'violation_id': item['violation_id']})
    
    print(f"Deleted {len(response['Items'])} old violations")
```

---

## Best Practices

### 1. Consistent Naming
```python
# Use consistent ID format
violation_id = f"viol_{int(time.time() * 1000)}"

# Use ISO timestamps
timestamp = datetime.utcnow().isoformat()
```

### 2. Error Handling
```python
try:
    table.put_item(Item=item)
except ClientError as e:
    print(f"Error storing violation: {e}")
    # Retry or log
```

### 3. Batch Operations
```python
# Store multiple violations efficiently
with table.batch_writer() as batch:
    for violation in violations:
        batch.put_item(Item=violation)
```

### 4. Lifecycle Policies
```bash
# Auto-delete old S3 evidence after 90 days
aws s3api put-bucket-lifecycle-configuration \
  --bucket sports-security-evidence \
  --lifecycle-configuration file://lifecycle.json
```

---

## Chapter 6 Checklist

- [ ] Stored violation in DynamoDB
- [ ] Organized evidence in S3 by timestamp
- [ ] Created description files
- [ ] Queried violations
- [ ] Retrieved evidence from S3
- [ ] Completed exercises

---

## Next: Chapter 7 - SNS Alerting

We'll send real-time notifications when violations are detected! →
