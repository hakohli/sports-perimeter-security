"""
Test script for sports security - simulates frame extraction and violation detection
Tests with soccer video from S3 without requiring Kafka
"""

import cv2
import json
import boto3
from datetime import datetime
import base64

s3 = boto3.client('s3', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
sns = boto3.client('sns', region_name='us-east-1')

def test_frame_extraction(video_path, max_frames=10):
    """Extract frames and simulate violation detection"""
    
    print(f"📹 Opening video: {video_path}")
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print("❌ Failed to open video")
        return
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps
    
    print(f"✓ Video info: {total_frames} frames, {fps:.1f} FPS, {duration:.1f}s duration")
    print(f"📊 Extracting {max_frames} sample frames...\n")
    
    frame_count = 0
    sample_interval = total_frames // max_frames
    
    violations_detected = []
    
    while frame_count < max_frames:
        # Jump to next sample frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count * sample_interval)
        ret, frame = cap.read()
        
        if not ret:
            break
        
        # Simulate detection (in real system, this would be computer vision)
        # For demo, randomly detect "violations" in some frames
        if frame_count % 3 == 0:  # Simulate violation every 3rd frame
            # Simulate player detection with names and teams
            players = [
                {'name': 'Cristiano Ronaldo', 'team': 'Home Team', 'number': 7},
                {'name': 'Lionel Messi', 'team': 'Away Team', 'number': 10},
                {'name': 'Neymar Jr', 'team': 'Home Team', 'number': 11},
                {'name': 'Kylian Mbappe', 'team': 'Away Team', 'number': 9},
                {'name': 'Mohamed Salah', 'team': 'Home Team', 'number': 14}
            ]
            
            player = players[frame_count % len(players)]
            
            violation = {
                'frame_id': f"frame_{frame_count}",
                'timestamp': datetime.utcnow().isoformat(),
                'type': 'perimeter_breach',
                'zone': 'sideline',
                'player_name': player['name'],
                'player_number': player['number'],
                'team': player['team'],
                'position': [250 + frame_count * 10, 300],
                'severity': 'warning'
            }
            
            print(f"⚠️  Frame {frame_count}: Potential violation detected")
            print(f"   Type: {violation['type']}")
            print(f"   Zone: {violation['zone']}")
            print(f"   Player: {violation['player_name']} (#{violation['player_number']})")
            print(f"   Team: {violation['team']}")
            
            # Analyze with AI
            ai_analysis = analyze_with_bedrock(violation, frame)
            
            if ai_analysis['valid']:
                violation['ai_analysis'] = ai_analysis
                violations_detected.append(violation)
                
                # Store in DynamoDB
                store_violation(violation, frame)
                
                print(f"   ✅ Confirmed by AI (confidence: 100%)")
                print(f"   Subject type: {ai_analysis.get('subject_type', 'player')}")
                print(f"   Severity: {ai_analysis['severity']}")
            else:
                reason = "Not a player" if ai_analysis.get('subject_type') != 'player' else "Confidence < 100%"
                print(f"   ℹ️  Rejected - {reason}")
        
        frame_count += 1
        print(f"✓ Processed frame {frame_count}/{max_frames}")
    
    cap.release()
    
    print(f"\n{'='*60}")
    print(f"✅ Test Complete!")
    print(f"{'='*60}")
    print(f"Frames processed: {frame_count}")
    print(f"Violations detected: {len(violations_detected)}")
    
    if violations_detected:
        print(f"\n📧 Sending test alert...")
        send_test_alert(violations_detected)
    
    return violations_detected

def analyze_with_bedrock(violation, frame):
    """Analyze violation with Bedrock Claude"""
    
    # Encode frame
    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
    frame_b64 = base64.b64encode(buffer).decode('utf-8')
    
    prompt = f"""Analyze this potential soccer game violation:

Type: {violation['type']}
Zone: {violation['zone']}
Player: {violation['player_name']} (#{violation['player_number']})
Team: {violation['team']}

CRITICAL REQUIREMENTS:
1. ONLY report violations by PLAYERS (ignore audience, ground staff, coaches, referees)
2. ONLY return confidence: 1.0 if you are 100% certain this is a valid player violation
3. Return confidence: 0.0 for anything else (non-players, uncertain situations)

Return JSON with:
- valid: true ONLY if subject is a player AND violation is certain
- severity: info/warning/violation/critical
- action: recommended action
- explanation: brief explanation including player name and team
- confidence: 1.0 (100% certain) or 0.0 (not certain or not a player)
- subject_type: "player" or "non-player" (audience/staff/coach/referee)

Return ONLY valid JSON."""

    try:
        response = bedrock_runtime.invoke_model(
            modelId='us.anthropic.claude-3-5-sonnet-20241022-v2:0',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 500,
                "messages": [{
                    "role": "user",
                    "content": prompt
                }]
            })
        )
        
        result = json.loads(response['body'].read())
        analysis_text = result['content'][0]['text']
        
        # Try to parse JSON
        try:
            analysis = json.loads(analysis_text)
            
            # Enforce 100% confidence requirement
            if analysis.get('confidence', 0) < 1.0:
                analysis['valid'] = False
                analysis['confidence'] = 0.0
            
            # Enforce player-only requirement
            if analysis.get('subject_type') != 'player':
                analysis['valid'] = False
                analysis['confidence'] = 0.0
                
        except:
            # Fallback - reject by default
            analysis = {
                'valid': False,
                'severity': 'info',
                'action': 'Ignore - insufficient confidence',
                'explanation': 'Unable to determine with 100% certainty',
                'confidence': 0.0,
                'subject_type': 'unknown'
            }
        
        return analysis
        
    except Exception as e:
        print(f"   ⚠️  AI analysis failed: {e}")
        return {
            'valid': False,
            'severity': 'info',
            'action': 'System error',
            'explanation': str(e),
            'confidence': 0.0,
            'subject_type': 'unknown'
        }

def store_violation(violation, frame):
    """Store violation in DynamoDB and frame in S3"""
    
    violation_id = f"test_viol_{int(datetime.utcnow().timestamp() * 1000)}"
    
    # Create timestamp-based folder structure
    timestamp = datetime.utcnow()
    date_folder = timestamp.strftime('%Y-%m-%d')
    time_folder = timestamp.strftime('%H-%M-%S')
    
    # S3 path: violations/2026-01-26/15-45-30/violation_id/
    s3_prefix = f"violations/{date_folder}/{time_folder}/{violation_id}"
    
    # Store frame in S3
    try:
        _, buffer = cv2.imencode('.jpg', frame)
        s3.put_object(
            Bucket='sports-security-evidence',
            Key=f"{s3_prefix}/frame.jpg",
            Body=buffer.tobytes(),
            ContentType='image/jpeg'
        )
        
        # Create description text file
        description = f"""Violation Report
================

Violation ID: {violation_id}
Timestamp: {violation['timestamp']}
Type: {violation['type']}
Zone: {violation['zone']}

Player Information
------------------
Name: {violation['player_name']}
Number: #{violation['player_number']}
Team: {violation['team']}
Position: {violation['position']}

AI Analysis
-----------
Severity: {violation['ai_analysis']['severity']}
Confidence: {violation['ai_analysis']['confidence'] * 100:.0f}%
Subject Type: {violation['ai_analysis'].get('subject_type', 'player')}

Explanation:
{violation['ai_analysis']['explanation']}

Recommended Action:
{violation['ai_analysis']['action']}

Evidence:
Frame: s3://sports-security-evidence/{s3_prefix}/frame.jpg
"""
        
        s3.put_object(
            Bucket='sports-security-evidence',
            Key=f"{s3_prefix}/description.txt",
            Body=description.encode('utf-8'),
            ContentType='text/plain'
        )
        
        evidence_url = f"s3://sports-security-evidence/{s3_prefix}/"
        print(f"   📁 Stored: {date_folder}/{time_folder}/{violation_id}/")
        
    except Exception as e:
        print(f"   ⚠️  Failed to store evidence: {e}")
        evidence_url = None
    
    # Store in DynamoDB
    try:
        table = dynamodb.Table('sports-violations')
        
        item = {
            'violation_id': violation_id,
            'timestamp': violation['timestamp'],
            'sport': 'soccer',
            'type': violation['type'],
            'zone': violation['zone'],
            'player_name': violation['player_name'],
            'player_number': str(violation['player_number']),
            'team': violation['team'],
            'position': violation['position'],
            'severity': violation['ai_analysis']['severity'],
            'valid': violation['ai_analysis']['valid'],
            'confidence': str(violation['ai_analysis']['confidence']),
            'subject_type': violation['ai_analysis'].get('subject_type', 'player'),
            'action': violation['ai_analysis']['action'],
            'explanation': violation['ai_analysis']['explanation'],
            'evidence_url': evidence_url,
            'status': 'test'
        }
        
        table.put_item(Item=item)
        
    except Exception as e:
        print(f"   ⚠️  Failed to store in DynamoDB: {e}")

def send_test_alert(violations):
    """Send test alert via SNS"""
    
    message = f"""
🚨 SPORTS SECURITY TEST ALERT

Test completed successfully!

Violations detected: {len(violations)}

Sample violation:
- Type: {violations[0]['type']}
- Zone: {violations[0]['zone']}
- Severity: {violations[0]['ai_analysis']['severity']}
- Confidence: {violations[0]['ai_analysis']['confidence']:.0%}

AI Analysis:
{violations[0]['ai_analysis']['explanation']}

This is a test of the sports perimeter security system.
Check DynamoDB table 'sports-violations' for full results.
"""
    
    try:
        sns.publish(
            TopicArn='arn:aws:sns:us-east-1:395102750341:sports-security-alerts',
            Subject='Sports Security Test - Success',
            Message=message
        )
        print("✅ Test alert sent to hakohli@amazon.com")
    except Exception as e:
        print(f"⚠️  Failed to send alert: {e}")

if __name__ == "__main__":
    print("="*60)
    print("Sports Perimeter Security - Test Run")
    print("="*60)
    print("\nVideo source: s3://sports-security-test-videos/soccervideo.mp4")
    print("Testing with local copy: /tmp/soccervideo.mp4\n")
    
    violations = test_frame_extraction('/tmp/soccervideo.mp4', max_frames=10)
    
    print(f"\n📊 View results:")
    print(f"   DynamoDB: aws dynamodb scan --table-name sports-violations --region us-east-1")
    print(f"   S3: aws s3 ls s3://sports-security-evidence/violations/")
    print(f"   Email: Check hakohli@amazon.com for alert (confirm subscription first)")
