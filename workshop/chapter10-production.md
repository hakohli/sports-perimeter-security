# Chapter 10: Production Deployment & Next Steps

**Duration**: 30 minutes

## Objectives
- Prepare system for production
- Implement monitoring and logging
- Set up CI/CD pipeline
- Plan future enhancements

---

## Production Readiness Checklist

### Security
- [ ] IAM roles with least privilege
- [ ] Secrets in AWS Secrets Manager
- [ ] S3 bucket encryption enabled
- [ ] DynamoDB encryption at rest
- [ ] VPC endpoints for private access

### Reliability
- [ ] Error handling and retries
- [ ] Dead letter queues
- [ ] Backup and recovery
- [ ] Multi-region failover

### Performance
- [ ] Auto-scaling configured
- [ ] Caching strategy
- [ ] Batch processing
- [ ] Connection pooling

### Monitoring
- [ ] CloudWatch dashboards
- [ ] Alarms for errors
- [ ] Cost monitoring
- [ ] Performance metrics

---

## Security Hardening

### 1. IAM Roles

Create least-privilege role:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:Query"
      ],
      "Resource": "arn:aws:dynamodb:us-east-1:ACCOUNT:table/sports-violations"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::sports-security-evidence/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sns:Publish"
      ],
      "Resource": "arn:aws:sns:us-east-1:ACCOUNT:sports-security-alerts"
    }
  ]
}
```

### 2. Secrets Management

```python
import boto3
import json

def get_secret(secret_name):
    """Retrieve secret from Secrets Manager"""
    
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_name)
    
    return json.loads(response['SecretString'])

# Use in code
config = get_secret('sports-security/config')
api_key = config['api_key']
```

### 3. S3 Encryption

```bash
# Enable default encryption
aws s3api put-bucket-encryption \
  --bucket sports-security-evidence \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'
```

---

## Monitoring & Logging

### CloudWatch Dashboard

Create `dashboard.json`:

```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/DynamoDB", "ConsumedWriteCapacityUnits", {"stat": "Sum"}]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "us-east-1",
        "title": "DynamoDB Writes"
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/SNS", "NumberOfMessagesPublished", {"stat": "Sum"}]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "us-east-1",
        "title": "SNS Alerts Sent"
      }
    }
  ]
}
```

Deploy:
```bash
aws cloudwatch put-dashboard \
  --dashboard-name sports-security \
  --dashboard-body file://dashboard.json
```

### CloudWatch Alarms

```bash
# Alert on high error rate
aws cloudwatch put-metric-alarm \
  --alarm-name sports-security-errors \
  --alarm-description "Alert on processing errors" \
  --metric-name Errors \
  --namespace SportsSecurityApp \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:us-east-1:ACCOUNT:sports-security-alerts
```

### Application Logging

```python
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('sports-security')

def process_violation(violation):
    """Process violation with logging"""
    
    logger.info(f"Processing violation", extra={
        'violation_id': violation['violation_id'],
        'player': violation['player_name'],
        'type': violation['type']
    })
    
    try:
        store_violation(violation)
        logger.info("Violation stored successfully")
    except Exception as e:
        logger.error(f"Failed to store violation: {e}", extra={
            'violation_id': violation['violation_id'],
            'error': str(e)
        })
        raise
```

---

## Error Handling

### Retry Logic

```python
from botocore.exceptions import ClientError
import time

def invoke_bedrock_with_retry(prompt, max_retries=3):
    """Invoke Bedrock with exponential backoff"""
    
    for attempt in range(max_retries):
        try:
            response = bedrock.invoke_model(
                modelId='us.anthropic.claude-3-5-sonnet-20241022-v2:0',
                body=json.dumps(prompt)
            )
            return response
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            if error_code == 'ThrottlingException':
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Throttled, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error("Max retries reached")
                    raise
            else:
                logger.error(f"Bedrock error: {error_code}")
                raise
```

### Dead Letter Queue

```python
import boto3

sqs = boto3.client('sqs', region_name='us-east-1')

def send_to_dlq(violation, error):
    """Send failed violation to DLQ"""
    
    sqs.send_message(
        QueueUrl='https://sqs.us-east-1.amazonaws.com/ACCOUNT/sports-security-dlq',
        MessageBody=json.dumps({
            'violation': violation,
            'error': str(error),
            'timestamp': datetime.utcnow().isoformat()
        })
    )
    
    logger.info(f"Sent to DLQ: {violation['violation_id']}")
```

---

## Performance Optimization

### 1. Batch Processing

```python
def process_violations_batch(violations):
    """Process multiple violations efficiently"""
    
    # Batch DynamoDB writes
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('sports-violations')
    
    with table.batch_writer() as batch:
        for violation in violations:
            batch.put_item(Item=violation)
    
    logger.info(f"Batch processed {len(violations)} violations")
```

### 2. Connection Pooling

```python
from botocore.config import Config

# Configure connection pool
config = Config(
    max_pool_connections=50,
    retries={'max_attempts': 3}
)

bedrock = boto3.client('bedrock-runtime', 
                       region_name='us-east-1',
                       config=config)
```

### 3. Caching

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_player_history(player_name):
    """Cache player history queries"""
    
    table = dynamodb.Table('sports-violations')
    response = table.query(
        IndexName='player-index',
        KeyConditionExpression='player_name = :name',
        ExpressionAttributeValues={':name': player_name}
    )
    
    return response['Items']
```

---

## CI/CD Pipeline

### GitHub Actions Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy Sports Security

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run tests
        run: python -m pytest tests/
  
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Deploy infrastructure
        run: python deploy.py
```

---

## Cost Optimization

### 1. S3 Lifecycle Policies

```json
{
  "Rules": [
    {
      "Id": "Archive old evidence",
      "Status": "Enabled",
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "STANDARD_IA"
        },
        {
          "Days": 90,
          "StorageClass": "GLACIER"
        }
      ],
      "Expiration": {
        "Days": 365
      }
    }
  ]
}
```

### 2. DynamoDB On-Demand

Already using pay-per-request mode:
```python
BillingMode='PAY_PER_REQUEST'
```

### 3. Bedrock Cost Tracking

```python
def track_bedrock_cost(input_tokens, output_tokens):
    """Track Bedrock API costs"""
    
    input_cost = (input_tokens / 1000) * 0.003
    output_cost = (output_tokens / 1000) * 0.015
    total_cost = input_cost + output_cost
    
    # Log to CloudWatch
    cloudwatch = boto3.client('cloudwatch')
    cloudwatch.put_metric_data(
        Namespace='SportsSecurityApp',
        MetricData=[{
            'MetricName': 'BedrockCost',
            'Value': total_cost,
            'Unit': 'None'
        }]
    )
```

---

## Scaling Strategy

### Horizontal Scaling

```python
# Process videos in parallel with Lambda
import boto3

lambda_client = boto3.client('lambda')

def process_video_lambda(video_s3_uri):
    """Invoke Lambda to process video"""
    
    lambda_client.invoke(
        FunctionName='sports-security-processor',
        InvocationType='Event',  # Async
        Payload=json.dumps({
            'video_uri': video_s3_uri
        })
    )
```

### Auto-scaling DynamoDB

```bash
# Enable auto-scaling (if using provisioned mode)
aws application-autoscaling register-scalable-target \
  --service-namespace dynamodb \
  --resource-id table/sports-violations \
  --scalable-dimension dynamodb:table:WriteCapacityUnits \
  --min-capacity 5 \
  --max-capacity 100
```

---

## Future Enhancements

### 1. Multi-Sport Support

```python
SPORT_CONFIGS = {
    'soccer': {
        'violations': ['perimeter_breach', 'offside', 'handball'],
        'zones': ['sideline', 'endline', 'penalty_box']
    },
    'basketball': {
        'violations': ['lane_violation', 'out_of_bounds', 'traveling'],
        'zones': ['paint', 'three_point_line', 'sideline']
    },
    'baseball': {
        'violations': ['balk', 'interference', 'out_of_baseline'],
        'zones': ['foul_line', 'baseline', 'pitchers_mound']
    }
}

def analyze_for_sport(frame, sport):
    """Analyze frame for sport-specific violations"""
    config = SPORT_CONFIGS[sport]
    # Use sport-specific prompt
```

### 2. Real-Time Video Streaming

```python
# Process live video stream
import cv2

def process_live_stream(stream_url):
    """Process live video stream"""
    
    cap = cv2.VideoCapture(stream_url)
    frame_count = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Process every 30th frame
        if frame_count % 30 == 0:
            analyze_frame_for_violations(frame)
        
        frame_count += 1
    
    cap.release()
```

### 3. Dashboard UI

```python
# Flask web dashboard
from flask import Flask, render_template
import boto3

app = Flask(__name__)

@app.route('/')
def dashboard():
    """Show live violations dashboard"""
    
    # Get recent violations
    table = dynamodb.Table('sports-violations')
    response = table.scan(Limit=10)
    
    return render_template('dashboard.html', 
                         violations=response['Items'])

@app.route('/api/violations')
def api_violations():
    """API endpoint for violations"""
    # Return JSON for frontend
```

### 4. Mobile App

```python
# AWS Amplify + React Native
# Push notifications via SNS
# Real-time updates via AppSync
```

### 5. Advanced Analytics

```python
# Violation trends
def analyze_trends():
    """Analyze violation patterns over time"""
    
    # Query last 30 days
    violations = get_violations_last_n_days(30)
    
    # Group by day
    by_day = {}
    for v in violations:
        day = v['timestamp'][:10]
        by_day[day] = by_day.get(day, 0) + 1
    
    # Detect trends
    # Predict future violations
```

---

## Cleanup (After Workshop)

### Delete Resources

```bash
# Delete S3 bucket
aws s3 rm s3://sports-security-evidence --recursive
aws s3api delete-bucket --bucket sports-security-evidence

# Delete DynamoDB table
aws dynamodb delete-table --table-name sports-violations

# Delete SNS topic
aws sns delete-topic --topic-arn arn:aws:sns:us-east-1:ACCOUNT:sports-security-alerts
```

Or use the cleanup script:

```python
# cleanup.py
import boto3

def cleanup_all():
    """Delete all workshop resources"""
    
    s3 = boto3.client('s3')
    dynamodb = boto3.client('dynamodb')
    sns = boto3.client('sns')
    
    # Delete S3
    bucket = 'sports-security-evidence'
    objects = s3.list_objects_v2(Bucket=bucket)
    if 'Contents' in objects:
        for obj in objects['Contents']:
            s3.delete_object(Bucket=bucket, Key=obj['Key'])
    s3.delete_bucket(Bucket=bucket)
    
    # Delete DynamoDB
    dynamodb.delete_table(TableName='sports-violations')
    
    # Delete SNS
    sns.delete_topic(TopicArn='arn:aws:sns:us-east-1:ACCOUNT:sports-security-alerts')
    
    print("✅ All resources deleted")

cleanup_all()
```

---

## Workshop Complete! 🎉

### What You Built

✅ **AI-powered sports security system**
- Real-time violation detection
- 100% confidence requirement
- Player-only filtering
- Timestamp-organized evidence
- Automated alerting

✅ **AWS Services Used**
- Amazon Bedrock (Claude 3.5 Sonnet)
- Amazon S3 (evidence storage)
- Amazon DynamoDB (violation records)
- Amazon SNS (real-time alerts)
- Model Context Protocol (streaming context)

✅ **Skills Learned**
- Video processing with OpenCV
- AI prompt engineering
- AWS infrastructure deployment
- Real-time data streaming
- Production best practices

---

## Next Steps

### 1. Extend the System
- Add more sports
- Implement live streaming
- Build web dashboard
- Create mobile app

### 2. Share Your Work
- Blog about your experience
- Share on GitHub
- Present at meetups
- Contribute improvements

### 3. Learn More
- AWS Machine Learning courses
- Computer vision tutorials
- Bedrock documentation
- MCP specification

---

## Resources

### Documentation
- [Amazon Bedrock](https://docs.aws.amazon.com/bedrock/)
- [Claude API](https://docs.anthropic.com/claude/reference)
- [OpenCV](https://docs.opencv.org/)
- [Model Context Protocol](https://modelcontextprotocol.io/)

### Code Repository
- GitHub: https://github.com/hakohli/sports-perimeter-security

### Support
- AWS Support
- GitHub Issues
- Workshop Slack channel

---

## Feedback

Please share your feedback:
- What worked well?
- What was challenging?
- What would you improve?
- What would you build next?

**Thank you for participating!** 🙏

---

## Chapter 10 Checklist

- [ ] Reviewed security best practices
- [ ] Set up monitoring and logging
- [ ] Implemented error handling
- [ ] Optimized performance
- [ ] Planned future enhancements
- [ ] Cleaned up resources (optional)

---

## 🎓 Workshop Complete!

You've successfully built **The AI Referee** - an intelligent sports security system powered by AWS!

**Total Workshop Time**: ~4 hours
**Total Cost**: ~$0.50-$1.00
**Skills Gained**: Priceless! 🚀
