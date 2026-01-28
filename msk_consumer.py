"""
MSK Consumer - Process violation events from Kafka
Consumes from MSK 3.8.x cluster with IAM authentication
"""

import boto3
import json
from kafka import KafkaConsumer
from aws_msk_iam_sasl_signer import MSKAuthTokenProvider
from datetime import datetime

class MSKTokenProvider:
    """IAM token provider for MSK"""
    def token(self):
        token, _ = MSKAuthTokenProvider.generate_auth_token('us-east-1')
        return token

class ViolationConsumer:
    """Consume and process violation events from MSK"""
    
    def __init__(self, bootstrap_servers, topic='violations'):
        self.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        self.s3 = boto3.client('s3', region_name='us-east-1')
        self.sns = boto3.client('sns', region_name='us-east-1')
        
        self.table = self.dynamodb.Table('sports-violations')
        self.evidence_bucket = f"sports-security-evidence-{boto3.client('sts').get_caller_identity()['Account']}"
        
        # Create MSK consumer with IAM auth
        self.consumer = KafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers.split(','),
            security_protocol='SASL_SSL',
            sasl_mechanism='OAUTHBEARER',
            sasl_oauth_token_provider=MSKTokenProvider(),
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            group_id='sports-security-consumer'
        )
        
        print(f"🎧 Connected to MSK: {bootstrap_servers}")
        print(f"📊 Consuming from topic: {topic}")
    
    def process_violation(self, violation):
        """Process a single violation event"""
        violation_id = violation['violation_id']
        
        print(f"\n⚠️  Violation: {violation_id}")
        print(f"   Player: {violation['player_name']} (#{violation['player_number']})")
        print(f"   Type: {violation['type']}")
        print(f"   Confidence: {violation['confidence']}")
        
        # Store in DynamoDB
        self.table.put_item(Item={
            'violation_id': violation_id,
            'timestamp': violation['timestamp'],
            'player_name': violation['player_name'],
            'player_number': str(violation['player_number']),
            'team': violation['team'],
            'type': violation['type'],
            'zone': violation.get('zone', 'Unknown'),
            'severity': violation['severity'],
            'confidence': str(violation['confidence']),
            'explanation': violation['explanation']
        })
        print(f"   ✅ Stored in DynamoDB")
        
        # Store evidence frame in S3 (if provided)
        if 'frame_base64' in violation:
            import base64
            frame_data = base64.b64decode(violation['frame_base64'])
            s3_key = f"violations/{violation['timestamp'][:10]}/{violation_id}/frame.jpg"
            
            self.s3.put_object(
                Bucket=self.evidence_bucket,
                Key=s3_key,
                Body=frame_data,
                ContentType='image/jpeg'
            )
            print(f"   ✅ Evidence stored in S3: {s3_key}")
        
        # Send SNS alert for critical violations
        if violation['severity'] in ['violation', 'critical']:
            self.send_alert(violation)
    
    def send_alert(self, violation):
        """Send SNS alert"""
        try:
            topic_arn = f"arn:aws:sns:us-east-1:{boto3.client('sts').get_caller_identity()['Account']}:sports-security-alerts"
            
            message = f"""Sports Security Alert

Player: {violation['player_name']} (#{violation['player_number']})
Team: {violation['team']}
Type: {violation['type']}
Severity: {violation['severity']}
Confidence: {violation['confidence']}

Explanation: {violation['explanation']}

Timestamp: {violation['timestamp']}
"""
            
            self.sns.publish(
                TopicArn=topic_arn,
                Subject=f"⚠️ {violation['severity'].upper()}: {violation['type']}",
                Message=message
            )
            print(f"   ✅ Alert sent via SNS")
        except Exception as e:
            print(f"   ⚠️  SNS error: {e}")
    
    def start(self):
        """Start consuming messages"""
        print("\n🚀 Starting violation consumer...")
        print("   Press Ctrl+C to stop\n")
        
        try:
            for message in self.consumer:
                violation = message.value
                self.process_violation(violation)
        except KeyboardInterrupt:
            print("\n\n⏹️  Stopping consumer...")
        finally:
            self.consumer.close()
            print("✅ Consumer stopped")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python msk_consumer.py <bootstrap_servers>")
        print("\nExample:")
        print("  python msk_consumer.py b-1.sports.xxx.kafka.us-east-1.amazonaws.com:9098,b-2.sports.xxx.kafka.us-east-1.amazonaws.com:9098")
        sys.exit(1)
    
    consumer = ViolationConsumer(sys.argv[1])
    consumer.start()
