# Sports Perimeter Security & Rule Violation Detection

Real-time monitoring system for detecting perimeter breaches and rule violations during live sports games using AI-powered video analysis.

## Use Cases

- **Perimeter Breach Detection**: Players/staff entering restricted zones
- **Rule Violations**: Offsides, fouls, illegal plays
- **Safety Monitoring**: Unauthorized personnel on field
- **Crowd Control**: Fans breaching barriers
- **Equipment Violations**: Illegal gear, tampering

## Architecture

```
Video Streams → Kinesis Video → Frame Extraction → MSK (Kafka)
                                                      ↓
                                                   Flink
                                                   (Detection)
                                                      ↓
                                                  AI Agent
                                                  (Bedrock)
                                                      ↓
                                              DynamoDB + SNS
                                              (Alerts)
```

## Components

### 1. **Video Ingestion**
- Kinesis Video Streams for live game feeds
- Frame extraction (1 FPS for analysis)
- Metadata: timestamp, camera angle, game context

### 2. **MSK (Kafka)**
- Topics:
  - `game-frames` - Extracted video frames
  - `violations` - Detected violations
  - `perimeter-events` - Boundary crossings

### 3. **Flink Processing**
- Computer vision preprocessing
- Perimeter boundary detection
- Player/object tracking
- Rule violation detection

### 4. **AI Agent (Bedrock)**
- Claude 3.5 Sonnet for visual analysis
- Violation classification
- Context-aware decision making
- False positive reduction

### 5. **MCP Server**
- `stream_game_frames` - Get live video frames
- `get_violation_context` - Historical violations
- `get_player_tracking` - Player position data
- `get_game_rules` - Current game rules

### 6. **Storage & Alerts**
- DynamoDB: Violation records
- S3: Video evidence clips
- SNS: Real-time alerts to security/officials
- EventBridge: Trigger automated responses

## Features

### Perimeter Detection
- Define virtual boundaries (field edges, restricted zones)
- Track player/personnel positions
- Alert on unauthorized entry
- Severity classification (warning, violation, critical)

### Rule Violation Detection
- Sport-specific rules (offsides, fouls, etc.)
- Equipment violations
- Time violations (shot clock, play clock)
- Substitution violations

### AI-Powered Analysis
- Visual scene understanding
- Context-aware decisions
- Pattern recognition
- Historical violation patterns

### Real-Time Alerts
- Instant notifications to officials
- Video clip generation
- Violation severity scoring
- Recommended actions

## Supported Sports

- **Baseball**: Perimeter breaches, balk detection, illegal pitches
- **Football**: Offsides, false starts, illegal formations
- **Basketball**: Lane violations, shot clock, out of bounds
- **Soccer**: Offsides, handball, dangerous play
- **Hockey**: Offsides, icing, too many men

## Quick Start

```bash
# Deploy infrastructure
python deploy.py

# Start video ingestion
python video_ingester.py --source rtsp://camera-url

# Start AI agent
python security_agent.py

# Monitor violations
python violation_dashboard.py
```

## Data Flow

```
1. Live Video → Kinesis Video Streams
2. Frame Extraction → MSK (game-frames topic)
3. Flink processes frames:
   - Detect perimeter boundaries
   - Track player positions
   - Identify potential violations
4. Violations → MSK (violations topic)
5. AI Agent analyzes:
   - Classify violation type
   - Assess severity
   - Generate evidence
6. Store in DynamoDB + Alert via SNS
7. MCP provides context to AI agents
```

## Example Violations

### Perimeter Breach
```json
{
  "violation_id": "viol_123",
  "type": "perimeter_breach",
  "timestamp": "2026-01-26T15:30:45Z",
  "location": "left_field_boundary",
  "subject": "player_42",
  "severity": "warning",
  "description": "Player entered restricted coaching zone",
  "video_clip": "s3://violations/viol_123.mp4"
}
```

### Rule Violation
```json
{
  "violation_id": "viol_124",
  "type": "offsides",
  "timestamp": "2026-01-26T15:31:12Z",
  "sport": "football",
  "subject": "player_87",
  "severity": "critical",
  "description": "Offensive player crossed line before snap",
  "ai_confidence": 0.95
}
```

## Cost Estimate

- Kinesis Video: ~$0.0085/GB ingested
- MSK: ~$150/month (2 brokers)
- Flink: ~$0.11/hour per KPU
- Bedrock: ~$0.003 per 1K tokens
- Storage: ~$0.023/GB (S3)

**Total**: ~$200-300/month per game stream

## Security & Compliance

- Video encryption (in-transit and at-rest)
- Access control (IAM roles)
- Audit logging (CloudTrail)
- Data retention policies
- Privacy compliance (face blurring optional)

## Integration

- **Scoreboard Systems**: Sync with game clock
- **Referee Systems**: Alert handheld devices
- **Broadcast**: Overlay violation markers
- **Analytics**: Post-game violation reports

## Files

- `video_ingester.py` - Ingest video streams to Kinesis
- `frame_extractor.py` - Extract frames and publish to Kafka
- `flink_violation_detector.py` - Flink app for violation detection
- `security_agent.py` - AI agent for violation analysis
- `mcp_server.py` - MCP server for streaming context
- `deploy.py` - Infrastructure deployment
- `violation_dashboard.py` - Real-time monitoring dashboard

## Next Steps

1. Deploy infrastructure
2. Configure video sources
3. Define perimeter boundaries
4. Set up rule definitions
5. Start monitoring
6. Review and tune detection thresholds
