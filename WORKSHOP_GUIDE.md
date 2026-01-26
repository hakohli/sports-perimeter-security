# AWS Workshop: AI-Powered Sports Security with Real-Time Video Analysis

## Workshop Overview

**Title**: Building Real-Time Sports Perimeter Security with AWS AI Services

**Duration**: 3-4 hours

**Level**: Intermediate

**Services Used**:
- Amazon Bedrock (Claude 3.5 Sonnet)
- Amazon MSK (Managed Streaming for Kafka)
- Amazon DynamoDB
- Amazon S3
- Amazon SNS
- AWS Lambda (optional)
- Model Context Protocol (MCP)

## Learning Objectives

By the end of this workshop, participants will:
1. Build a real-time video analysis system using AWS AI services
2. Implement streaming data pipelines with MSK
3. Use Amazon Bedrock for intelligent violation detection
4. Apply MCP for AI agent context management
5. Create automated alerting systems
6. Organize and store evidence with proper data governance

## Prerequisites

### Required Knowledge
- Basic Python programming
- AWS account with appropriate permissions
- Understanding of AWS services (S3, DynamoDB, SNS)
- Familiarity with command line/terminal

### AWS Permissions Needed
```json
{
  "Services": [
    "s3:*",
    "dynamodb:*",
    "sns:*",
    "kafka:*",
    "bedrock:InvokeModel",
    "iam:CreateRole",
    "iam:AttachRolePolicy"
  ]
}
```

### Tools to Install
```bash
# Python 3.9+
python3 --version

# AWS CLI
aws --version

# Git
git --version

# pip packages
pip install boto3 opencv-python kafka-python
```

## Workshop Structure

### Module 1: Introduction (30 minutes)

**Topics**:
- Use case overview: Sports perimeter security
- Architecture walkthrough
- AI/ML concepts for video analysis
- Real-world applications

**Demo**:
- Show working solution with soccer video
- Display violation detection in real-time
- Review S3 evidence and DynamoDB records

**Hands-on**:
- Clone GitHub repository
- Review code structure
- Understand data flow

### Module 2: Setting Up AWS Infrastructure (45 minutes)

**Topics**:
- S3 bucket creation and organization
- DynamoDB table design
- SNS topic configuration
- IAM roles and permissions

**Hands-on**:
```bash
# Step 1: Clone repository
git clone https://github.com/hakohli/sports-perimeter-security.git
cd sports-perimeter-security

# Step 2: Deploy infrastructure
python3 deploy.py

# Step 3: Verify resources
aws s3 ls
aws dynamodb list-tables
aws sns list-topics
```

**Expected Output**:
- S3 bucket: `sports-security-evidence`
- DynamoDB table: `sports-violations`
- SNS topic: `sports-security-alerts`

**Troubleshooting**:
- Permission errors → Check IAM policies
- Bucket already exists → Use unique name
- Region mismatch → Ensure us-east-1

### Module 3: Understanding Amazon Bedrock (45 minutes)

**Topics**:
- Introduction to Amazon Bedrock
- Claude 3.5 Sonnet capabilities
- Prompt engineering for video analysis
- Confidence scoring and validation

**Hands-on**:
```python
# Test Bedrock API
import boto3
import json

bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

response = bedrock.invoke_model(
    modelId='us.anthropic.claude-3-5-sonnet-20241022-v2:0',
    body=json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 500,
        "messages": [{
            "role": "user",
            "content": "Explain how to detect a soccer player crossing a sideline."
        }]
    })
)

result = json.loads(response['body'].read())
print(result['content'][0]['text'])
```

**Discussion**:
- Why 100% confidence requirement?
- How to handle false positives?
- Player vs non-player classification

### Module 4: Video Processing Pipeline (60 minutes)

**Topics**:
- Video frame extraction with OpenCV
- Perimeter boundary detection
- Object detection basics
- Streaming to Kafka

**Hands-on**:
```bash
# Step 1: Upload test video to S3
aws s3 cp your-video.mp4 s3://sports-security-test-videos/

# Step 2: Download for processing
aws s3 cp s3://sports-security-test-videos/your-video.mp4 /tmp/

# Step 3: Run frame extraction
python3 test_solution.py
```

**Code Walkthrough**:
- Frame extraction logic
- Boundary detection algorithm
- Violation classification
- AI analysis integration

**Exercise**:
- Modify perimeter boundaries
- Adjust detection sensitivity
- Add new violation types

### Module 5: AI-Powered Violation Detection (45 minutes)

**Topics**:
- Prompt engineering for sports rules
- Structured output with JSON
- Confidence scoring
- Subject type classification

**Hands-on**:
```python
# Customize AI prompt for different sports
def analyze_violation(sport, violation_data):
    prompt = f"""
    Analyze this {sport} violation:
    Type: {violation_data['type']}
    Player: {violation_data['player_name']}
    Team: {violation_data['team']}
    
    Return JSON with confidence: 1.0 only if certain.
    """
    # Call Bedrock...
```

**Exercise**:
- Add basketball rules
- Implement offsides detection for football
- Create custom violation types

### Module 6: Data Storage and Organization (30 minutes)

**Topics**:
- S3 folder structure design
- DynamoDB schema optimization
- Evidence retention policies
- Compliance considerations

**Hands-on**:
```bash
# Explore S3 structure
aws s3 ls s3://sports-security-evidence/violations/2026-01-26/ --recursive

# Query DynamoDB
aws dynamodb scan --table-name sports-violations \
  --filter-expression "team = :team" \
  --expression-attribute-values '{":team":{"S":"Home Team"}}'

# Download evidence
aws s3 cp s3://sports-security-evidence/violations/2026-01-26/17-32-42/test_viol_xxx/description.txt -
```

**Discussion**:
- Why timestamp-based folders?
- Data retention requirements
- Privacy and compliance (GDPR, etc.)

### Module 7: Alerting and Notifications (30 minutes)

**Topics**:
- SNS topic configuration
- Email/SMS subscriptions
- Alert filtering by severity
- Integration with ticketing systems

**Hands-on**:
```bash
# Subscribe to alerts
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:ACCOUNT_ID:sports-security-alerts \
  --protocol email \
  --notification-endpoint your-email@example.com

# Test alert
python3 -c "
import boto3
sns = boto3.client('sns', region_name='us-east-1')
sns.publish(
    TopicArn='arn:aws:sns:us-east-1:ACCOUNT_ID:sports-security-alerts',
    Subject='Test Alert',
    Message='Workshop test notification'
)
"
```

**Exercise**:
- Add SMS notifications
- Filter alerts by severity
- Create custom alert templates

### Module 8: Model Context Protocol (MCP) (45 minutes)

**Topics**:
- Introduction to MCP
- Why MCP for AI agents?
- Creating MCP tools
- Streaming context to AI

**Hands-on**:
```python
# Review MCP server
cat mcp_server.py

# Understand MCP tools
# - stream_game_frames
# - get_violation_context
# - get_player_tracking
# - get_game_rules
```

**Discussion**:
- MCP vs direct API calls
- Benefits of abstraction
- Reusability across agents

### Module 9: Advanced Features (Optional - 30 minutes)

**Topics**:
- MSK integration for real-time streaming
- Apache Flink for stream processing
- Multi-camera support
- Dashboard creation

**Demo**:
- Show MSK cluster (if available)
- Explain Flink processing
- Display real-time dashboard

### Module 10: Production Deployment (30 minutes)

**Topics**:
- Cost optimization
- Scaling considerations
- Monitoring and logging
- Security best practices

**Hands-on**:
```bash
# Tag resources
aws s3api put-bucket-tagging \
  --bucket sports-security-evidence \
  --tagging 'TagSet=[{Key=Project,Value=Workshop},{Key=Environment,Value=Production}]'

# Enable CloudWatch logging
aws logs create-log-group --log-group-name /aws/sports-security

# Set up alarms
aws cloudwatch put-metric-alarm \
  --alarm-name high-violation-rate \
  --metric-name ViolationCount \
  --threshold 100
```

**Checklist**:
- [ ] All resources tagged
- [ ] Monitoring enabled
- [ ] Alerts configured
- [ ] Documentation complete
- [ ] Cost estimates reviewed

## Workshop Materials

### Provided Resources

1. **GitHub Repository**
   - Complete source code
   - Test video (soccer game)
   - Documentation
   - Deployment scripts

2. **Sample Data**
   - Soccer video (26 MB, 5 minutes)
   - Pre-generated violations
   - Example outputs

3. **Documentation**
   - Architecture diagrams
   - API references
   - Troubleshooting guide

### Participant Deliverables

By end of workshop, participants will have:
1. Working sports security system
2. Deployed AWS infrastructure
3. Test results with real video
4. Understanding of AI-powered video analysis
5. Reusable code for other use cases

## Cost Estimate

**Per Participant** (4-hour workshop):
- Bedrock API calls: ~$0.50
- S3 storage: ~$0.01
- DynamoDB: ~$0.01
- SNS: ~$0.001
- MSK (if used): ~$0.50
- **Total**: ~$1-2 per participant

**For 50 participants**: ~$50-100

## Cleanup Instructions

```bash
# Delete S3 bucket
aws s3 rb s3://sports-security-evidence --force

# Delete DynamoDB table
aws dynamodb delete-table --table-name sports-violations

# Delete SNS topic
aws sns delete-topic --topic-arn arn:aws:sns:us-east-1:ACCOUNT_ID:sports-security-alerts

# Delete test video bucket
aws s3 rb s3://sports-security-test-videos --force
```

## Extensions and Follow-ups

### Additional Use Cases
1. **Manufacturing Quality Control**
   - Defect detection on assembly lines
   - Real-time quality monitoring

2. **Retail Analytics**
   - Customer behavior analysis
   - Queue management

3. **Security Surveillance**
   - Perimeter breach detection
   - Unauthorized access alerts

4. **Healthcare Monitoring**
   - Patient fall detection
   - Equipment usage tracking

### Advanced Topics
- Multi-model ensemble detection
- Custom ML model training
- Real-time dashboards with QuickSight
- Integration with existing systems

## Instructor Notes

### Preparation (1 week before)
- [ ] Test all scripts in clean AWS account
- [ ] Verify Bedrock model access
- [ ] Prepare sample videos
- [ ] Create IAM roles for participants
- [ ] Set up workshop AWS account

### Day Before
- [ ] Test internet connectivity
- [ ] Verify AWS credentials
- [ ] Download all dependencies
- [ ] Print handouts
- [ ] Test projector/screen

### During Workshop
- [ ] Start with working demo
- [ ] Encourage questions
- [ ] Monitor participant progress
- [ ] Help with troubleshooting
- [ ] Collect feedback

### Common Issues

**Issue**: Bedrock access denied
**Solution**: Enable model access in Bedrock console

**Issue**: S3 bucket name conflict
**Solution**: Use unique prefix (participant name)

**Issue**: DynamoDB throttling
**Solution**: Use on-demand billing mode

**Issue**: Video too large
**Solution**: Provide pre-processed frames

## Feedback and Iteration

### Survey Questions
1. Was the workshop pace appropriate?
2. Which module was most valuable?
3. What would you change?
4. Will you use this in your work?
5. Additional topics to cover?

### Success Metrics
- 90%+ completion rate
- Working system deployed
- Positive feedback (4+/5)
- Follow-up questions/engagement

## Resources

### Links
- GitHub: https://github.com/hakohli/sports-perimeter-security
- AWS Bedrock Docs: https://docs.aws.amazon.com/bedrock/
- MCP Specification: https://modelcontextprotocol.io/
- OpenCV Tutorial: https://opencv.org/

### Contact
- Workshop Lead: [Your Name]
- Email: [Your Email]
- Slack: #sports-security-workshop

## Appendix

### A. Complete Architecture Diagram
```
[Video Source] → [Frame Extraction] → [MSK/Kafka]
                                          ↓
                                      [Flink Processing]
                                          ↓
                                      [AI Agent (Bedrock)]
                                          ↓
                                   [DynamoDB + S3 + SNS]
                                          ↓
                                      [MCP Server]
```

### B. Sample Workshop Schedule

**9:00 AM** - Welcome & Introductions
**9:30 AM** - Module 1: Overview
**10:00 AM** - Module 2: Infrastructure Setup
**10:45 AM** - Break
**11:00 AM** - Module 3: Bedrock
**11:45 AM** - Module 4: Video Processing
**12:45 PM** - Lunch
**1:45 PM** - Module 5: AI Detection
**2:30 PM** - Module 6: Data Storage
**3:00 PM** - Break
**3:15 PM** - Module 7: Alerting
**3:45 PM** - Module 8: MCP
**4:30 PM** - Module 9: Advanced (Optional)
**5:00 PM** - Q&A and Wrap-up

### C. Troubleshooting Guide

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed solutions.

### D. Additional Reading

- AWS Well-Architected Framework
- AI/ML Best Practices
- Video Processing at Scale
- Real-time Analytics Patterns
