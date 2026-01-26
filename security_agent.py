"""
AI Security Agent for analyzing violations using Bedrock Claude
Provides intelligent violation classification and context-aware decisions
"""

import json
import boto3
import base64
from kafka import KafkaConsumer
from datetime import datetime

bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
s3 = boto3.client('s3', region_name='us-east-1')
sns = boto3.client('sns', region_name='us-east-1')

VIOLATIONS_TABLE = 'sports-violations'
EVIDENCE_BUCKET = 'sports-security-evidence'
ALERT_TOPIC_ARN = 'arn:aws:sns:us-east-1:ACCOUNT_ID:sports-security-alerts'

class SecurityAgent:
    """AI-powered security agent for violation analysis"""
    
    def __init__(self, sport='baseball'):
        self.sport = sport
        self.rules = self.load_sport_rules(sport)
    
    def load_sport_rules(self, sport):
        """Load sport-specific rules"""
        rules = {
            'baseball': {
                'perimeter_zones': ['dugout', 'bullpen', 'field_boundary'],
                'violations': ['perimeter_breach', 'balk', 'illegal_pitch'],
                'severity_levels': ['info', 'warning', 'violation', 'critical']
            },
            'football': {
                'perimeter_zones': ['sideline', 'endzone', 'bench_area'],
                'violations': ['offsides', 'false_start', 'illegal_formation'],
                'severity_levels': ['info', 'warning', 'penalty', 'ejection']
            }
        }
        return rules.get(sport, rules['baseball'])
    
    def analyze_violation_with_ai(self, violation_data, frame_data):
        """Use Bedrock Claude to analyze violation"""
        
        # Prepare context
        context = f"""
Sport: {self.sport}
Violation Type: {violation_data.get('type')}
Zone: {violation_data.get('zone')}
Subject: {violation_data.get('subject')}
Position: {violation_data.get('position')}
Timestamp: {violation_data.get('timestamp')}

Analyze this potential violation and provide:
1. Is this a valid violation? (true/false)
2. Severity level: {', '.join(self.rules['severity_levels'])}
3. Recommended action
4. Explanation
5. Confidence score (0-1)

Return as JSON with keys: valid, severity, action, explanation, confidence
"""
        
        # Call Bedrock
        response = bedrock_runtime.invoke_model(
            modelId='us.anthropic.claude-3-5-sonnet-20241022-v2:0',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [{
                    "role": "user",
                    "content": context
                }]
            })
        )
        
        result = json.loads(response['body'].read())
        analysis_text = result['content'][0]['text']
        
        try:
            analysis = json.loads(analysis_text)
        except:
            # Fallback if AI doesn't return valid JSON
            analysis = {
                'valid': True,
                'severity': 'warning',
                'action': 'Review manually',
                'explanation': analysis_text,
                'confidence': 0.7
            }
        
        return analysis
    
    def store_violation(self, violation_id, violation_data, ai_analysis, frame_data):
        """Store violation in DynamoDB and evidence in S3"""
        
        # Store frame evidence in S3
        evidence_key = f"violations/{violation_id}/frame.jpg"
        
        try:
            # Decode and upload frame
            frame_bytes = base64.b64decode(frame_data)
            s3.put_object(
                Bucket=EVIDENCE_BUCKET,
                Key=evidence_key,
                Body=frame_bytes,
                ContentType='image/jpeg'
            )
            evidence_url = f"s3://{EVIDENCE_BUCKET}/{evidence_key}"
        except Exception as e:
            print(f"⚠️  Failed to store evidence: {e}")
            evidence_url = None
        
        # Store in DynamoDB
        table = dynamodb.Table(VIOLATIONS_TABLE)
        
        item = {
            'violation_id': violation_id,
            'timestamp': violation_data['timestamp'],
            'sport': self.sport,
            'type': violation_data['type'],
            'zone': violation_data.get('zone'),
            'subject': violation_data.get('subject'),
            'position': violation_data.get('position'),
            'severity': ai_analysis['severity'],
            'valid': ai_analysis['valid'],
            'confidence': str(ai_analysis['confidence']),
            'action': ai_analysis['action'],
            'explanation': ai_analysis['explanation'],
            'evidence_url': evidence_url,
            'status': 'detected'
        }
        
        table.put_item(Item=item)
        
        return item
    
    def send_alert(self, violation):
        """Send alert via SNS for critical violations"""
        
        if violation['severity'] in ['critical', 'violation', 'penalty']:
            message = f"""
🚨 SPORTS SECURITY ALERT

Sport: {violation['sport']}
Type: {violation['type']}
Zone: {violation.get('zone', 'N/A')}
Subject: {violation.get('subject', 'Unknown')}
Severity: {violation['severity']}

AI Analysis:
{violation['explanation']}

Recommended Action:
{violation['action']}

Confidence: {float(violation['confidence']):.0%}

Evidence: {violation.get('evidence_url', 'N/A')}
Timestamp: {violation['timestamp']}
"""
            
            try:
                sns.publish(
                    TopicArn=ALERT_TOPIC_ARN,
                    Subject=f"Security Alert: {violation['type']}",
                    Message=message
                )
                print(f"📧 Alert sent for {violation['violation_id']}")
            except Exception as e:
                print(f"⚠️  Failed to send alert: {e}")
    
    def process_violations(self, bootstrap_servers, topic='game-frames'):
        """Consume frames from Kafka and analyze violations"""
        
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers.split(','),
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            group_id='security-agent'
        )
        
        print(f"🤖 Security Agent monitoring {self.sport} games")
        print(f"📡 Listening on topic: {topic}\n")
        
        for message in consumer:
            frame_event = message.value
            
            # Check for violations in frame
            if frame_event.get('violations'):
                for violation in frame_event['violations']:
                    
                    violation_id = f"viol_{int(datetime.utcnow().timestamp() * 1000)}"
                    
                    print(f"\n⚠️  Violation detected: {violation_id}")
                    print(f"   Type: {violation['type']}")
                    print(f"   Zone: {violation.get('zone')}")
                    
                    # Analyze with AI
                    ai_analysis = self.analyze_violation_with_ai(
                        violation,
                        frame_event.get('frame_data', '')
                    )
                    
                    print(f"   AI Analysis: {ai_analysis['severity']} (confidence: {ai_analysis['confidence']})")
                    
                    if ai_analysis['valid']:
                        # Store violation
                        stored = self.store_violation(
                            violation_id,
                            {**violation, 'timestamp': frame_event['timestamp']},
                            ai_analysis,
                            frame_event.get('frame_data', '')
                        )
                        
                        # Send alert if critical
                        self.send_alert(stored)
                        
                        print(f"   ✅ Violation recorded")
                    else:
                        print(f"   ℹ️  False positive - ignored")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: security_agent.py <bootstrap_servers> <sport>")
        sys.exit(1)
    
    agent = SecurityAgent(sport=sys.argv[2])
    agent.process_violations(sys.argv[1])
