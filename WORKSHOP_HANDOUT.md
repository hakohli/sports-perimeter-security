# Workshop Participant Handout

## Sports Perimeter Security Workshop - Quick Reference

### Your AWS Account Setup

**Account ID**: _________________
**Region**: us-east-1
**IAM User**: _________________

### Workshop Goals

✅ Deploy AI-powered video analysis system
✅ Detect sports violations in real-time
✅ Use Amazon Bedrock for intelligent analysis
✅ Store and organize evidence
✅ Set up automated alerts

### Quick Start Commands

```bash
# 1. Clone repository
git clone https://github.com/hakohli/sports-perimeter-security.git
cd sports-perimeter-security

# 2. Install dependencies
pip install boto3 opencv-python kafka-python

# 3. Configure AWS
aws configure
# Enter your credentials when prompted

# 4. Deploy infrastructure
python3 deploy.py

# 5. Run test
python3 test_solution.py
```

### Key Resources Created

| Resource | Name | Purpose |
|----------|------|---------|
| S3 Bucket | `sports-security-evidence` | Store violation evidence |
| DynamoDB | `sports-violations` | Track violations |
| SNS Topic | `sports-security-alerts` | Send alerts |

### Subscribe to Alerts

```bash
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:sports-security-alerts \
  --protocol email \
  --notification-endpoint YOUR_EMAIL@example.com
```

### View Results

**DynamoDB**:
```bash
aws dynamodb scan --table-name sports-violations --max-items 5
```

**S3 Evidence**:
```bash
aws s3 ls s3://sports-security-evidence/violations/ --recursive
```

**Download Description**:
```bash
aws s3 cp s3://sports-security-evidence/violations/2026-01-26/HH-MM-SS/violation_id/description.txt -
```

### Architecture

```
Video → Frame Extraction → AI Analysis (Bedrock) → Storage (S3 + DynamoDB) → Alerts (SNS)
```

### Key Concepts

**100% Confidence Rule**: Only report violations AI is 100% certain about

**Player-Only**: Ignore audience, staff, coaches - track players only

**Timestamp Folders**: Organize evidence by date/time for easy browsing

**MCP**: Model Context Protocol for AI agent communication

### Troubleshooting

**Issue**: Bedrock access denied
**Fix**: Enable model in Bedrock console → Model access

**Issue**: S3 bucket exists
**Fix**: Use unique name or delete existing

**Issue**: No violations detected
**Fix**: Check video has players near boundaries

### Cost Tracking

Monitor your costs:
```bash
aws ce get-cost-and-usage \
  --time-period Start=2026-01-26,End=2026-01-27 \
  --granularity DAILY \
  --metrics BlendedCost
```

### Cleanup (End of Workshop)

```bash
# Delete S3 buckets
aws s3 rb s3://sports-security-evidence --force
aws s3 rb s3://sports-security-test-videos --force

# Delete DynamoDB table
aws dynamodb delete-table --table-name sports-violations

# Delete SNS topic
aws sns delete-topic --topic-arn arn:aws:sns:us-east-1:ACCOUNT_ID:sports-security-alerts
```

### Exercises

**Exercise 1**: Modify detection for basketball
**Exercise 2**: Add SMS alerts
**Exercise 3**: Create custom violation types
**Exercise 4**: Analyze your own video

### Notes

_Use this space for your notes during the workshop_

---

---

---

---

---

### Resources

- GitHub: https://github.com/hakohli/sports-perimeter-security
- AWS Bedrock: https://aws.amazon.com/bedrock/
- Workshop Slack: #sports-security-workshop

### Feedback

Please complete the survey: [Survey Link]

**Questions?** Ask the instructor or post in Slack!
