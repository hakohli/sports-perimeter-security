# Sports Perimeter Security - Deployment Summary

## ✅ Successfully Deployed

### AWS Resources Created

| Resource | Name | Status | Purpose |
|----------|------|--------|---------|
| **S3 Bucket** | `sports-security-evidence` | ✅ Active | Store video evidence clips |
| **DynamoDB Table** | `sports-violations` | ✅ Active | Track violations and AI analysis |
| **SNS Topic** | `sports-security-alerts` | ✅ Active | Real-time alerts to officials |
| **MSK Cluster** | `mcp-anomaly-cluster` | 🟡 Creating | Shared with anomaly detection |

### S3 Bucket Configuration
- **Versioning**: Enabled
- **Lifecycle**: Auto-delete after 30 days
- **Tags**: Project=Sports-Security, NoDelete=true

### DynamoDB Schema
```
Primary Key: violation_id (String)
GSI: timestamp-index
Billing: Pay-per-request

Attributes:
- violation_id
- timestamp
- sport
- type (perimeter_breach, offsides, etc.)
- zone
- subject (player_id)
- position
- severity (info, warning, violation, critical)
- valid (AI validation)
- confidence
- action (recommended action)
- explanation (AI analysis)
- evidence_url (S3 link)
- status
```

### SNS Topic
- **ARN**: `arn:aws:sns:us-east-1:395102750341:sports-security-alerts`
- **Purpose**: Alert security staff and officials
- **Protocols**: Email, SMS, Lambda

## 🎯 Use Cases

### 1. Perimeter Breach Detection
**Scenario**: Player enters restricted coaching zone during game

**Flow**:
1. Video frame extracted → Kafka
2. Frame analyzer detects player in restricted zone
3. AI agent validates violation
4. Alert sent to security staff
5. Evidence clip saved to S3

### 2. Rule Violation Detection
**Scenario**: Offsides in football

**Flow**:
1. Frame shows player position
2. Flink compares to line of scrimmage
3. Detects offsides violation
4. AI confirms with context
5. Alert sent to officials

### 3. Safety Monitoring
**Scenario**: Unauthorized person on field

**Flow**:
1. Person detected without player/staff ID
2. Classified as security threat
3. High-severity alert triggered
4. Security team notified immediately

## 📊 Architecture Reuse

This solution **reuses** the MCP Live anomaly detection architecture:

| Component | Anomaly Detection | Sports Security |
|-----------|------------------|-----------------|
| **MSK** | Metrics streaming | Video frame streaming |
| **Flink** | Statistical analysis | Computer vision + tracking |
| **AI Agent** | Anomaly classification | Violation classification |
| **MCP** | Stream metrics | Stream frames + context |
| **DynamoDB** | Anomaly context | Violation records |
| **SNS** | Anomaly alerts | Security alerts |

**Key Difference**: Video analysis instead of metric analysis

## 🚀 Quick Start

### 1. Subscribe to Alerts
```bash
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:395102750341:sports-security-alerts \
  --protocol email \
  --notification-endpoint your-email@example.com \
  --region us-east-1
```

### 2. Wait for MSK (if not active)
```bash
aws kafka describe-cluster \
  --cluster-arn arn:aws:kafka:us-east-1:395102750341:cluster/mcp-anomaly-cluster/3783fbf6-b6c7-41c0-abf0-c8be3280cfb1-25 \
  --region us-east-1 \
  --query 'ClusterInfo.State'
```

### 3. Create Kafka Topics
```bash
# Get bootstrap servers when MSK is ACTIVE
export BOOTSTRAP_SERVERS="<from-msk-cluster>"

# Create topics
kafka-topics --create \
  --bootstrap-server $BOOTSTRAP_SERVERS \
  --topic game-frames \
  --partitions 2 \
  --replication-factor 2

kafka-topics --create \
  --bootstrap-server $BOOTSTRAP_SERVERS \
  --topic violations \
  --partitions 2 \
  --replication-factor 2
```

### 4. Start Security Agent
```bash
cd /Users/hakohli/sports-perimeter-security
pip install -r requirements.txt

python3 security_agent.py $BOOTSTRAP_SERVERS baseball
```

### 5. Process Video
```bash
# Extract frames from video file
python3 frame_extractor.py $BOOTSTRAP_SERVERS game-video.mp4 30

# Or ingest live stream
python3 video_ingester.py --source rtsp://camera-url --fps 30
```

## 📹 Supported Video Sources

- **RTSP Streams**: Live camera feeds
- **HLS Streams**: Broadcast streams
- **Video Files**: MP4, AVI, MOV
- **Webcam**: Local camera (index 0, 1, etc.)

## 🏷️ Supported Sports

### Baseball
- Perimeter: Dugout, bullpen, field boundary
- Violations: Balk, illegal pitch, perimeter breach

### Football
- Perimeter: Sideline, endzone, bench area
- Violations: Offsides, false start, illegal formation

### Basketball
- Perimeter: Court boundary, bench area
- Violations: Lane violation, out of bounds

### Soccer
- Perimeter: Touchline, goal area
- Violations: Offsides, handball

## 🔍 Monitoring

### View Violations
```bash
aws dynamodb scan \
  --table-name sports-violations \
  --region us-east-1
```

### Check S3 Evidence
```bash
aws s3 ls s3://sports-security-evidence/violations/
```

### SNS Subscriptions
```bash
aws sns list-subscriptions-by-topic \
  --topic-arn arn:aws:sns:us-east-1:395102750341:sports-security-alerts \
  --region us-east-1
```

## 💰 Cost Estimate

- **S3**: ~$0.023/GB (evidence storage)
- **DynamoDB**: ~$1-5/month (pay-per-request)
- **SNS**: ~$0.50/million notifications
- **MSK**: ~$150/month (shared with anomaly detection)
- **Bedrock**: ~$0.003 per 1K tokens

**Total**: ~$10-20/month (excluding MSK which is shared)

## 🔐 Security

- Video encryption in transit and at rest
- IAM role-based access control
- 30-day evidence retention
- Audit logging via CloudTrail
- Optional face blurring for privacy

## 📚 Documentation

- **README**: `/Users/hakohli/sports-perimeter-security/README.md`
- **GitHub**: https://github.com/hakohli/sports-perimeter-security
- **Related**: MCP Live Anomaly Detection (shared infrastructure)

## 🎯 Next Steps

1. ✅ Infrastructure deployed
2. ⏳ Wait for MSK cluster (~10 min remaining)
3. 📧 Subscribe to SNS alerts
4. 🎥 Configure video sources
5. 🏃 Start processing games
6. 📊 Monitor violations dashboard

## 🔗 Links

- **GitHub**: https://github.com/hakohli/sports-perimeter-security
- **S3 Console**: https://s3.console.aws.amazon.com/s3/buckets/sports-security-evidence
- **DynamoDB Console**: https://console.aws.amazon.com/dynamodbv2/home?region=us-east-1#table?name=sports-violations
- **SNS Console**: https://console.aws.amazon.com/sns/v3/home?region=us-east-1#/topic/arn:aws:sns:us-east-1:395102750341:sports-security-alerts
