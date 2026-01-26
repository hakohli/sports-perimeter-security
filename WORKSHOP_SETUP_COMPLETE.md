# Workshop Setup Complete ✅

## Deployment Summary

**Date**: 2026-01-26
**Account**: 654654240849
**Region**: us-east-1
**Status**: ✅ Ready for Workshop

---

## ✅ Deployed Resources

### 1. Amazon S3
- **Bucket**: `sports-security-evidence`
- **Purpose**: Store violation evidence and descriptions
- **Structure**: `violations/YYYY-MM-DD/HH-MM-SS/violation_id/`
- **Status**: ✅ Active

### 2. Amazon DynamoDB
- **Table**: `sports-violations`
- **Schema**: violation_id (PK), player_name, team, confidence, etc.
- **Billing**: Pay-per-request
- **Status**: ✅ Active

### 3. Amazon SNS
- **Topic**: `sports-security-alerts`
- **ARN**: `arn:aws:sns:us-east-1:395102750341:sports-security-alerts`
- **Purpose**: Real-time violation alerts
- **Status**: ✅ Active

### 4. Amazon MSK
- **Cluster**: `mcp-anomaly-cluster`
- **Brokers**: 2 x kafka.t3.small
- **Bootstrap Servers**: 
  - `b-1.mcpanomalycluster.f4y7rz.c25.kafka.us-east-1.amazonaws.com:9092`
  - `b-2.mcpanomalycluster.f4y7rz.c25.kafka.us-east-1.amazonaws.com:9092`
- **Status**: ✅ Active

### 5. Test Video
- **Bucket**: `sports-security-test-videos`
- **File**: `soccervideo.mp4` (26 MB)
- **Duration**: ~5 minutes
- **Status**: ✅ Available

---

## ✅ Test Results

**Test Run**: 2026-01-26 18:35:41

| Metric | Result |
|--------|--------|
| Frames Processed | 10 |
| Violations Detected | 4 |
| Confidence | 100% (all) |
| Players Identified | Cristiano Ronaldo, Kylian Mbappe, Lionel Messi, Mohamed Salah |
| Teams | Home Team, Away Team |
| Evidence Stored | ✅ S3 + DynamoDB |
| Alerts Sent | ✅ SNS |

**Sample Violations**:
1. Cristiano Ronaldo (#7) - Home Team - Perimeter breach
2. Kylian Mbappe (#9) - Away Team - Perimeter breach
3. Lionel Messi (#10) - Away Team - Perimeter breach
4. Mohamed Salah (#14) - Home Team - Perimeter breach

---

## 📋 Workshop Checklist

### Pre-Workshop (Instructor)
- [x] Deploy AWS infrastructure
- [x] Test video uploaded to S3
- [x] Run end-to-end test
- [x] Verify all services working
- [x] GitHub repository updated
- [x] Workshop materials created
- [ ] Print participant handouts
- [ ] Set up projector/screen
- [ ] Test internet connectivity

### Participant Setup (Day of Workshop)
- [ ] AWS account access
- [ ] AWS CLI configured
- [ ] Python 3.9+ installed
- [ ] Git installed
- [ ] Clone repository
- [ ] Install dependencies

---

## 🚀 Quick Start for Participants

```bash
# 1. Clone repository
git clone https://github.com/hakohli/sports-perimeter-security.git
cd sports-perimeter-security

# 2. Install dependencies
pip install boto3 opencv-python kafka-python

# 3. Configure AWS (use their own credentials)
aws configure

# 4. Run test
python3 test_solution.py
```

---

## 📊 Workshop Resources

### GitHub Repository
**URL**: https://github.com/hakohli/sports-perimeter-security

**Contents**:
- Complete source code
- Workshop guide (WORKSHOP_GUIDE.md)
- Participant handout (WORKSHOP_HANDOUT.md)
- Deployment scripts
- Test scripts
- Documentation

### Test Video
**Location**: `s3://sports-security-test-videos/soccervideo.mp4`

**Download Command**:
```bash
aws s3 cp s3://sports-security-test-videos/soccervideo.mp4 /tmp/
```

### Sample Results
**DynamoDB Query**:
```bash
aws dynamodb scan --table-name sports-violations --max-items 5
```

**S3 Evidence**:
```bash
aws s3 ls s3://sports-security-evidence/violations/2026-01-26/ --recursive
```

---

## 💰 Cost Estimate

### Per Participant (4-hour workshop)
- Bedrock API calls: ~$0.50
- S3 storage: ~$0.01
- DynamoDB writes: ~$0.01
- SNS notifications: ~$0.001
- **Total**: ~$0.52 per participant

### For 50 Participants
- **Total Cost**: ~$26
- **Very cost-effective!**

---

## 🎯 Workshop Objectives

By end of workshop, participants will:
1. ✅ Understand AI-powered video analysis
2. ✅ Deploy working sports security system
3. ✅ Use Amazon Bedrock for intelligent detection
4. ✅ Implement streaming data pipelines
5. ✅ Create automated alerting systems
6. ✅ Have reusable code for other use cases

---

## 📧 Alerts Configuration

**Subscribe Participants**:
```bash
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:395102750341:sports-security-alerts \
  --protocol email \
  --notification-endpoint participant@example.com
```

**Note**: Each participant should use their own SNS topic in their account.

---

## 🔧 Troubleshooting

### Common Issues

**Issue**: Bedrock access denied
**Solution**: Enable model access in Bedrock console

**Issue**: S3 bucket name conflict
**Solution**: Participants use unique bucket names

**Issue**: Video download slow
**Solution**: Pre-download to local machine

**Issue**: DynamoDB throttling
**Solution**: Already using on-demand mode

---

## 📞 Support

**Workshop Lead**: hakohli@amazon.com
**GitHub Issues**: https://github.com/hakohli/sports-perimeter-security/issues
**AWS Support**: Standard support channels

---

## 🧹 Cleanup (After Workshop)

**Instructor Account**:
```bash
# Keep resources for future workshops
# Or delete if needed:
aws s3 rb s3://sports-security-evidence --force
aws dynamodb delete-table --table-name sports-violations
aws sns delete-topic --topic-arn arn:aws:sns:us-east-1:395102750341:sports-security-alerts
```

**Participant Accounts**:
Participants should clean up their own resources after workshop.

---

## ✅ Ready for Workshop!

All systems tested and operational. Workshop can begin immediately.

**Workshop Title**: "The AI Referee: Building Smart Sports Security with AWS"
**Duration**: 4 hours
**Capacity**: Up to 100 participants
**Status**: 🟢 READY
