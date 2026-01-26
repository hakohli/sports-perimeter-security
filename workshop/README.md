# The AI Referee Workshop
## Building Smart Sports Security with AWS

### Workshop Information
- **Duration**: 4 hours
- **Level**: Intermediate
- **Prerequisites**: Basic Python, AWS account

---

## Table of Contents

1. [Chapter 1: Introduction & Demo](chapter1-introduction.md)
2. [Chapter 2: AWS Infrastructure Setup](chapter2-infrastructure.md)
3. [Chapter 3: Amazon Bedrock Deep Dive](chapter3-bedrock.md)
4. [Chapter 4: Video Processing Pipeline](chapter4-video-processing.md)
5. [Chapter 5: AI-Powered Detection](chapter5-ai-detection.md)
6. [Chapter 6: Data Storage & Organization](chapter6-data-storage.md)
7. [Chapter 7: Alerting & Notifications](chapter7-alerting.md)
8. [Chapter 8: Model Context Protocol](chapter8-mcp.md)
9. [Chapter 9: Testing & Validation](chapter9-testing.md)
10. [Chapter 10: Production & Next Steps](chapter10-production.md)

---

## Workshop Schedule

### Morning Session (9:00 AM - 1:00 PM)

**9:00 - 9:30** | Chapter 1: Introduction & Demo
- Welcome and introductions
- Use case overview
- Live demo of working solution
- Architecture walkthrough

**9:30 - 10:15** | Chapter 2: Infrastructure Setup
- AWS account setup
- Deploy S3, DynamoDB, SNS
- Verify resources
- Hands-on: Run deployment script

**10:15 - 10:30** | ☕ Break

**10:30 - 11:15** | Chapter 3: Amazon Bedrock
- Introduction to Bedrock
- Claude 3.5 Sonnet capabilities
- Prompt engineering
- Hands-on: Test Bedrock API

**11:15 - 12:00** | Chapter 4: Video Processing
- Frame extraction with OpenCV
- Perimeter detection
- Streaming to Kafka
- Hands-on: Process test video

**12:00 - 12:30** | Chapter 5: AI Detection
- Violation classification
- Confidence scoring
- Player vs non-player filtering
- Hands-on: Customize detection rules

**12:30 - 12:50** | Chapters 6-8: Storage, Alerts, MCP
- S3 organization
- SNS configuration
- MCP overview
- Hands-on: Subscribe to alerts

**12:50 - 1:00** | Chapters 9-10: Testing & Wrap-up
- Run complete test
- Review results
- Production considerations
- Q&A and next steps

---

## Learning Objectives

By the end of this workshop, you will:

✅ Understand AI-powered video analysis architecture
✅ Deploy a working sports security system on AWS
✅ Use Amazon Bedrock for intelligent violation detection
✅ Implement real-time data pipelines
✅ Create automated alerting systems
✅ Have reusable code for other use cases

---

## Required Tools

```bash
# Check prerequisites
python3 --version  # 3.9+
aws --version      # AWS CLI
git --version      # Git

# Install Python packages
pip install boto3 opencv-python kafka-python
```

---

## Quick Start

```bash
# Clone repository
git clone https://github.com/hakohli/sports-perimeter-security.git
cd sports-perimeter-security

# Deploy infrastructure
python3 deploy.py

# Run test
python3 test_solution.py
```

---

## Workshop Resources

- **GitHub**: https://github.com/hakohli/sports-perimeter-security
- **Test Video**: `s3://sports-security-test-videos/soccervideo.mp4`
- **Instructor**: hakohli@amazon.com

---

## Cost Estimate

- **Per Participant**: ~$0.50 for 4 hours
- **50 Participants**: ~$25 total

---

## Support

- Ask questions anytime during workshop
- Use Slack channel: #ai-referee-workshop
- GitHub issues for bugs/feedback

---

Let's build an AI referee! 🏆
