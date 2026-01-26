# Chapter 2: AWS Infrastructure Setup

**Duration**: 45 minutes

## Objectives
- Deploy S3 bucket for evidence storage
- Create DynamoDB table for violations
- Set up SNS topic for alerts
- Verify all resources are working

---

## Prerequisites Check

Before we start, verify you have:

```bash
# AWS CLI configured
aws sts get-caller-identity

# Should show your account ID and user
```

If this fails, run:
```bash
aws configure
# Enter your AWS credentials
```

---

## Step 1: Clone the Repository (5 minutes)

```bash
# Clone workshop code
git clone https://github.com/hakohli/sports-perimeter-security.git
cd sports-perimeter-security

# Verify files
ls -la
```

**Expected files**:
- `deploy.py` - Deployment script
- `test_solution.py` - Test script
- `security_agent.py` - AI agent
- `README.md` - Documentation

---

## Step 2: Review Deployment Script (5 minutes)

Open `deploy.py` and review what it does:

```python
# Creates:
# 1. S3 bucket: sports-security-evidence
# 2. DynamoDB table: sports-violations
# 3. SNS topic: sports-security-alerts
# 4. IAM roles (if needed)
```

**Key Configuration**:
- Region: `us-east-1`
- Billing: Pay-per-request (no upfront cost)
- Tags: `Project=Sports-Security, NoDelete=true`

---

## Step 3: Deploy Infrastructure (10 minutes)

### Run Deployment

```bash
python3 deploy.py
```

**Expected Output**:
```
============================================================
Sports Perimeter Security - Deployment
============================================================

📦 Creating S3 bucket...
✓ Created S3 bucket: sports-security-evidence

💾 Creating DynamoDB table...
✓ Created DynamoDB table: sports-violations

📧 Creating SNS topic...
✓ Created SNS topic: arn:aws:sns:us-east-1:ACCOUNT_ID:sports-security-alerts

============================================================
✓ Deployment Complete!
============================================================
```

### Troubleshooting

**Issue**: Bucket already exists
```bash
# Use unique name
export BUCKET_SUFFIX=$(date +%s)
# Edit deploy.py to add suffix
```

**Issue**: Permission denied
```bash
# Check IAM permissions
aws iam get-user
# Ensure you have S3, DynamoDB, SNS permissions
```

**Issue**: Region mismatch
```bash
# Set region
export AWS_DEFAULT_REGION=us-east-1
```

---

## Step 4: Verify S3 Bucket (5 minutes)

### List Buckets
```bash
aws s3 ls | grep sports-security
```

**Expected**:
```
sports-security-evidence
sports-security-test-videos
```

### Check Bucket Structure
```bash
aws s3 ls s3://sports-security-evidence/
```

**Should be empty** (we haven't stored violations yet)

### Test Upload
```bash
echo "Test file" > test.txt
aws s3 cp test.txt s3://sports-security-evidence/test/
aws s3 ls s3://sports-security-evidence/test/
```

**Expected**: `test.txt` appears

---

## Step 5: Verify DynamoDB Table (5 minutes)

### Describe Table
```bash
aws dynamodb describe-table --table-name sports-violations
```

**Key Information**:
```json
{
  "TableName": "sports-violations",
  "KeySchema": [
    {"AttributeName": "violation_id", "KeyType": "HASH"}
  ],
  "BillingMode": "PAY_PER_REQUEST",
  "TableStatus": "ACTIVE"
}
```

### Check Table is Empty
```bash
aws dynamodb scan --table-name sports-violations --max-items 5
```

**Expected**: `"Count": 0` (no violations yet)

---

## Step 6: Verify SNS Topic (5 minutes)

### List Topics
```bash
aws sns list-topics | grep sports-security
```

**Expected**:
```
arn:aws:sns:us-east-1:ACCOUNT_ID:sports-security-alerts
```

### Subscribe to Alerts
```bash
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:ACCOUNT_ID:sports-security-alerts \
  --protocol email \
  --notification-endpoint YOUR_EMAIL@example.com
```

**Important**: Check your email and **confirm subscription**!

### Test Alert
```bash
aws sns publish \
  --topic-arn arn:aws:sns:us-east-1:ACCOUNT_ID:sports-security-alerts \
  --subject "Workshop Test" \
  --message "Hello from AI Referee workshop!"
```

**Check your email** - you should receive the test message!

---

## Step 7: Tag Resources (5 minutes)

### Tag S3 Bucket
```bash
aws s3api put-bucket-tagging \
  --bucket sports-security-evidence \
  --tagging 'TagSet=[{Key=Project,Value=AI-Referee-Workshop},{Key=Owner,Value=YOUR_NAME}]'
```

### Tag DynamoDB Table
```bash
aws dynamodb tag-resource \
  --resource-arn arn:aws:dynamodb:us-east-1:ACCOUNT_ID:table/sports-violations \
  --tags Key=Project,Value=AI-Referee-Workshop Key=Owner,Value=YOUR_NAME
```

### Why Tag?
- Track costs by project
- Identify resources easily
- Automate cleanup
- Compliance requirements

---

## Step 8: Review Cost Estimates (5 minutes)

### Current Costs (Empty Resources)

| Service | Cost |
|---------|------|
| S3 (empty) | $0.00 |
| DynamoDB (no requests) | $0.00 |
| SNS (no messages) | $0.00 |
| **Total** | **$0.00** |

### Workshop Costs (4 hours)

| Service | Usage | Cost |
|---------|-------|------|
| S3 | ~100 MB storage | $0.002 |
| DynamoDB | ~100 writes | $0.0001 |
| SNS | ~10 notifications | $0.00001 |
| Bedrock | ~50 API calls | $0.50 |
| **Total** | | **~$0.50** |

### Monitor Costs
```bash
aws ce get-cost-and-usage \
  --time-period Start=2026-01-26,End=2026-01-27 \
  --granularity DAILY \
  --metrics BlendedCost
```

---

## Hands-On Exercise

### Exercise 1: Explore S3 Structure

Create the folder structure we'll use:
```bash
aws s3api put-object \
  --bucket sports-security-evidence \
  --key violations/2026-01-26/README.txt \
  --body - <<< "Violations will be stored here"

aws s3 ls s3://sports-security-evidence/violations/ --recursive
```

### Exercise 2: Test DynamoDB Write

```python
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('sports-violations')

# Write test record
table.put_item(Item={
    'violation_id': 'test_001',
    'timestamp': datetime.utcnow().isoformat(),
    'player_name': 'Test Player',
    'team': 'Test Team',
    'type': 'test',
    'confidence': '1.0'
})

print("✓ Test record written!")
```

Run it:
```bash
python3 -c "$(cat test_dynamodb.py)"
```

Verify:
```bash
aws dynamodb get-item \
  --table-name sports-violations \
  --key '{"violation_id":{"S":"test_001"}}'
```

---

## Architecture Review

What we just deployed:

```
┌─────────────────────────────────────┐
│         Your AWS Account            │
│                                     │
│  ┌──────────┐  ┌──────────┐       │
│  │    S3    │  │ DynamoDB │       │
│  │ Evidence │  │Violations│       │
│  └──────────┘  └──────────┘       │
│                                     │
│  ┌──────────┐                      │
│  │   SNS    │                      │
│  │  Alerts  │                      │
│  └──────────┘                      │
└─────────────────────────────────────┘
```

**Next**: We'll add Amazon Bedrock for AI analysis!

---

## Verification Checklist

Before moving to Chapter 3, verify:

- [ ] S3 bucket created and accessible
- [ ] DynamoDB table active
- [ ] SNS topic created
- [ ] Email subscription confirmed
- [ ] Test alert received
- [ ] Resources tagged
- [ ] Cost estimate understood

---

## Common Issues & Solutions

**Issue**: "Access Denied" errors
**Solution**: Check IAM permissions, ensure you have admin or power user access

**Issue**: "Bucket name already taken"
**Solution**: S3 bucket names are globally unique, add a suffix

**Issue**: "Table already exists"
**Solution**: Either use existing table or delete and recreate

**Issue**: "Email not received"
**Solution**: Check spam folder, verify email address, confirm subscription

---

## Chapter 2 Complete! ✅

You now have:
- ✅ S3 bucket for evidence
- ✅ DynamoDB table for violations
- ✅ SNS topic for alerts
- ✅ All resources verified and working

**Next**: Chapter 3 - Amazon Bedrock Deep Dive

We'll learn how to use AI for intelligent violation detection! →
