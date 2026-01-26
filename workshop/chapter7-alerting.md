# Chapter 7: Real-Time Alerting with SNS

**Duration**: 30 minutes

## Objectives
- Configure SNS topic for alerts
- Send notifications on violations
- Format alert messages
- Test email and SMS alerts

---

## Why SNS?

**Amazon SNS** (Simple Notification Service) sends real-time alerts to:
- 📧 Email
- 📱 SMS
- 🔔 Mobile push
- 🌐 HTTP endpoints
- 📊 Other AWS services

**Use Case**: Notify security staff immediately when violations occur

---

## SNS Architecture

```
Violation Detected
    ↓
Check Severity
    ↓
severity >= "violation"?
    ↓ YES
Publish to SNS Topic
    ↓
┌─────────────────────────────────┐
│ SNS Topic                       │
│ sports-security-alerts          │
└─────────────────────────────────┘
    ↓
┌──────────┬──────────┬──────────┐
│  Email   │   SMS    │  Lambda  │
│ Security │ On-call  │ Webhook  │
└──────────┴──────────┴──────────┘
```

---

## Configure SNS Topic

### Already Created!

From Chapter 2, we have:
```
arn:aws:sns:us-east-1:ACCOUNT_ID:sports-security-alerts
```

### Add Email Subscription

```bash
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:ACCOUNT_ID:sports-security-alerts \
  --protocol email \
  --notification-endpoint your-email@example.com
```

**Check your email** and confirm subscription!

### Add SMS Subscription (Optional)

```bash
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:ACCOUNT_ID:sports-security-alerts \
  --protocol sms \
  --notification-endpoint +1234567890
```

---

## Send Alert

Create `send_alert.py`:

```python
import boto3
import json

sns = boto3.client('sns', region_name='us-east-1')
TOPIC_ARN = 'arn:aws:sns:us-east-1:ACCOUNT_ID:sports-security-alerts'

def send_violation_alert(violation):
    """Send SNS alert for violation"""
    
    # Format message
    subject = f"⚠️ {violation['severity'].upper()}: {violation['type']}"
    
    message = f"""Sports Security Alert
{'='*50}

VIOLATION DETECTED

Player: {violation['player_name']} (#{violation['player_number']})
Team: {violation['team']}
Type: {violation['type']}
Zone: {violation['zone']}
Severity: {violation['severity']}
Confidence: {violation['confidence']}

Details:
{violation['explanation']}

Recommended Action:
{violation['action']}

Evidence:
{violation['s3_evidence_path']}

Timestamp: {violation['timestamp']}
Violation ID: {violation['violation_id']}
"""
    
    # Send alert
    response = sns.publish(
        TopicArn=TOPIC_ARN,
        Subject=subject,
        Message=message
    )
    
    print(f"✅ Alert sent: {response['MessageId']}")
    return response['MessageId']

# Test it
violation = {
    'violation_id': 'viol_123',
    'timestamp': '2026-01-26T13:45:30Z',
    'player_name': 'Cristiano Ronaldo',
    'player_number': '7',
    'team': 'Home Team',
    'type': 'perimeter_breach',
    'zone': 'sideline',
    'severity': 'warning',
    'confidence': '1.0',
    'explanation': 'Player crossed sideline boundary',
    'action': 'Return player to field',
    's3_evidence_path': 's3://bucket/violations/2026-01-26/13-45-30/viol_123/'
}

send_violation_alert(violation)
```

Run it:
```bash
python3 send_alert.py
```

**Check your email!** You should receive the alert.

---

## Alert Filtering

### Only Alert on Critical Violations

```python
SEVERITY_LEVELS = {
    'info': 1,
    'warning': 2,
    'violation': 3,
    'critical': 4
}

def should_send_alert(severity):
    """Determine if alert needed"""
    return SEVERITY_LEVELS.get(severity, 0) >= 3

def process_violation(violation):
    """Process violation and alert if needed"""
    
    # Always store in DynamoDB
    store_violation(violation)
    
    # Only alert on serious violations
    if should_send_alert(violation['severity']):
        send_violation_alert(violation)
        print("📧 Alert sent")
    else:
        print("ℹ️  No alert (severity too low)")
```

---

## Formatted Alerts

### HTML Email (Rich Formatting)

```python
def send_html_alert(violation):
    """Send formatted HTML email"""
    
    html_message = f"""
    <html>
    <body style="font-family: Arial, sans-serif;">
        <h2 style="color: #d32f2f;">⚠️ Violation Detected</h2>
        
        <table style="border-collapse: collapse; width: 100%;">
            <tr style="background-color: #f5f5f5;">
                <td style="padding: 10px; border: 1px solid #ddd;"><strong>Player</strong></td>
                <td style="padding: 10px; border: 1px solid #ddd;">{violation['player_name']} (#{violation['player_number']})</td>
            </tr>
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;"><strong>Team</strong></td>
                <td style="padding: 10px; border: 1px solid #ddd;">{violation['team']}</td>
            </tr>
            <tr style="background-color: #f5f5f5;">
                <td style="padding: 10px; border: 1px solid #ddd;"><strong>Type</strong></td>
                <td style="padding: 10px; border: 1px solid #ddd;">{violation['type']}</td>
            </tr>
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;"><strong>Severity</strong></td>
                <td style="padding: 10px; border: 1px solid #ddd; color: #d32f2f;"><strong>{violation['severity'].upper()}</strong></td>
            </tr>
        </table>
        
        <p><strong>Explanation:</strong><br>{violation['explanation']}</p>
        <p><strong>Action:</strong><br>{violation['action']}</p>
        
        <p><a href="{violation['s3_evidence_path']}" style="background-color: #1976d2; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Evidence</a></p>
    </body>
    </html>
    """
    
    sns.publish(
        TopicArn=TOPIC_ARN,
        Subject=f"⚠️ Violation: {violation['type']}",
        Message=violation['explanation'],  # Plain text fallback
        MessageAttributes={
            'html': {
                'DataType': 'String',
                'StringValue': html_message
            }
        }
    )
```

---

## Alert Throttling

### Prevent Alert Spam

```python
from datetime import datetime, timedelta

alert_history = {}

def should_throttle_alert(player_name, violation_type, minutes=5):
    """Prevent duplicate alerts within time window"""
    
    key = f"{player_name}:{violation_type}"
    now = datetime.utcnow()
    
    if key in alert_history:
        last_alert = alert_history[key]
        if now - last_alert < timedelta(minutes=minutes):
            print(f"⏸️  Throttled: Alert sent {(now - last_alert).seconds}s ago")
            return True
    
    alert_history[key] = now
    return False

def smart_alert(violation):
    """Send alert with throttling"""
    
    if should_throttle_alert(violation['player_name'], violation['type']):
        print("Skipping duplicate alert")
        return
    
    send_violation_alert(violation)
```

---

## Hands-On Exercise

### Exercise 1: Test Different Severities

```python
# Test each severity level
severities = ['info', 'warning', 'violation', 'critical']

for severity in severities:
    violation = {
        'violation_id': f'test_{severity}',
        'severity': severity,
        'player_name': 'Test Player',
        'type': 'test',
        # ... other fields
    }
    
    if should_send_alert(severity):
        print(f"✅ Would alert: {severity}")
    else:
        print(f"⚪ No alert: {severity}")
```

### Exercise 2: Custom Alert Format

Create a Slack-style alert:

```python
def send_slack_style_alert(violation):
    """Format alert like Slack message"""
    
    emoji = {
        'info': 'ℹ️',
        'warning': '⚠️',
        'violation': '🚨',
        'critical': '🔴'
    }
    
    message = f"""{emoji[violation['severity']]} *{violation['type'].upper()}*

*Player:* {violation['player_name']} (#{violation['player_number']})
*Team:* {violation['team']}
*Zone:* {violation['zone']}

_{violation['explanation']}_

*Action Required:* {violation['action']}
"""
    
    sns.publish(
        TopicArn=TOPIC_ARN,
        Subject=f"{emoji[violation['severity']]} Violation Alert",
        Message=message
    )
```

### Exercise 3: Multi-Channel Alerts

Send to different channels based on severity:

```python
TOPIC_ARNS = {
    'info': 'arn:aws:sns:us-east-1:ACCOUNT:info-alerts',
    'warning': 'arn:aws:sns:us-east-1:ACCOUNT:warning-alerts',
    'critical': 'arn:aws:sns:us-east-1:ACCOUNT:critical-alerts'
}

def send_to_appropriate_channel(violation):
    """Route alert to correct SNS topic"""
    
    severity = violation['severity']
    topic_arn = TOPIC_ARNS.get(severity, TOPIC_ARNS['warning'])
    
    sns.publish(
        TopicArn=topic_arn,
        Subject=f"Violation: {violation['type']}",
        Message=format_message(violation)
    )
```

---

## Integration with Storage

### Complete Flow

```python
def handle_violation(analysis, frame_bytes):
    """Complete violation handling"""
    
    # 1. Store in DynamoDB and S3
    violation_id = store_violation(analysis, frame_bytes)
    
    # 2. Get full violation record
    violation = get_violation(violation_id)
    
    # 3. Send alert if needed
    if should_send_alert(violation['severity']):
        if not should_throttle_alert(violation['player_name'], violation['type']):
            send_violation_alert(violation)
            print("✅ Complete: Stored and alerted")
        else:
            print("✅ Complete: Stored (alert throttled)")
    else:
        print("✅ Complete: Stored (no alert needed)")
    
    return violation_id
```

---

## SNS Pricing

### Cost Structure
- **Email**: $0 (free)
- **SMS**: $0.00645 per message (US)
- **HTTP/S**: $0.60 per million requests
- **Mobile push**: $0.50 per million requests

### Workshop Cost
- 10 violations detected
- 5 alerts sent (email)
- **Total**: $0.00 (email is free!)

---

## Monitoring Alerts

### Check Alert Status

```bash
# List subscriptions
aws sns list-subscriptions-by-topic \
  --topic-arn arn:aws:sns:us-east-1:ACCOUNT:sports-security-alerts

# Check delivery status
aws sns get-subscription-attributes \
  --subscription-arn arn:aws:sns:us-east-1:ACCOUNT:sports-security-alerts:SUBSCRIPTION_ID
```

### CloudWatch Metrics

```bash
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

## Chapter 7 Checklist

- [ ] SNS topic configured
- [ ] Email subscription confirmed
- [ ] Sent test alert
- [ ] Implemented alert filtering
- [ ] Added alert throttling
- [ ] Completed exercises

---

## Next: Chapter 8 - Model Context Protocol (MCP)

Learn how MCP provides real-time streaming context to AI agents! →
