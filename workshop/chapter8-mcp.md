# Chapter 8: Model Context Protocol (MCP)

**Duration**: 30 minutes

## Objectives
- Understand what MCP is and why it matters
- Set up MCP server for streaming context
- Connect AI agent to MCP server
- See real-time violation streaming

---

## What is MCP?

**Model Context Protocol** is an open standard for providing context to AI models.

### Traditional Approach
```
AI Agent → Query Database → Get Results → Analyze
```

**Problems**:
- Static snapshots
- No real-time updates
- Manual refresh needed

### MCP Approach
```
AI Agent ← MCP Server ← Live Data Stream
```

**Benefits**:
- ✅ Real-time context
- ✅ Streaming updates
- ✅ Always current data
- ✅ Standardized protocol

---

## Why MCP for Sports Security?

### Use Case: Live Game Monitoring

**Without MCP**:
```python
# Agent must poll for updates
while game_active:
    violations = query_database()
    analyze(violations)
    time.sleep(5)  # Wait 5 seconds
```

**With MCP**:
```python
# Agent receives live stream
mcp_client.subscribe('violations')
# Violations arrive in real-time
```

### Real-World Example

```
Game starts at 2:00 PM
    ↓
2:15 PM: Violation detected
    ↓
MCP Server streams violation
    ↓
AI Agent receives immediately
    ↓
Agent analyzes and responds
    ↓
Alert sent within seconds
```

---

## MCP Architecture

```
┌─────────────────────────────────┐
│ Video Processing                │
│ - Extract frames                │
│ - Detect violations             │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ MCP Server                      │
│ - Streams violations            │
│ - Provides context              │
│ - Handles subscriptions         │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ AI Agent (Bedrock)              │
│ - Receives real-time context    │
│ - Analyzes patterns             │
│ - Makes decisions               │
└─────────────────────────────────┘
```

---

## MCP Server Setup

Review `mcp_server.py`:

```python
import json
from datetime import datetime

class MCPServer:
    """MCP server for sports security context"""
    
    def __init__(self):
        self.subscribers = []
        self.violation_stream = []
    
    def subscribe(self, client_id):
        """Subscribe to violation stream"""
        self.subscribers.append(client_id)
        print(f"✅ Client {client_id} subscribed")
    
    def publish_violation(self, violation):
        """Publish violation to all subscribers"""
        
        # Add to stream
        self.violation_stream.append({
            'timestamp': datetime.utcnow().isoformat(),
            'violation': violation
        })
        
        # Notify subscribers
        for subscriber in self.subscribers:
            self.send_to_subscriber(subscriber, violation)
    
    def get_context(self, query):
        """Get current context for AI agent"""
        
        if query == 'recent_violations':
            # Return last 10 violations
            return self.violation_stream[-10:]
        
        elif query == 'player_history':
            # Return violations by player
            player_violations = {}
            for item in self.violation_stream:
                player = item['violation']['player_name']
                if player not in player_violations:
                    player_violations[player] = []
                player_violations[player].append(item)
            return player_violations
        
        elif query == 'game_summary':
            # Return game statistics
            return {
                'total_violations': len(self.violation_stream),
                'by_type': self._count_by_type(),
                'by_severity': self._count_by_severity()
            }
    
    def _count_by_type(self):
        """Count violations by type"""
        counts = {}
        for item in self.violation_stream:
            vtype = item['violation']['type']
            counts[vtype] = counts.get(vtype, 0) + 1
        return counts
    
    def _count_by_severity(self):
        """Count violations by severity"""
        counts = {}
        for item in self.violation_stream:
            severity = item['violation']['severity']
            counts[severity] = counts.get(severity, 0) + 1
        return counts

# Create server
mcp_server = MCPServer()
```

---

## AI Agent with MCP

Review `security_agent.py`:

```python
import boto3
import json

class SecurityAgent:
    """AI agent with MCP context"""
    
    def __init__(self, mcp_server):
        self.mcp_server = mcp_server
        self.bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        
        # Subscribe to MCP server
        self.mcp_server.subscribe('security_agent')
    
    def analyze_with_context(self, violation):
        """Analyze violation with MCP context"""
        
        # Get context from MCP
        recent = self.mcp_server.get_context('recent_violations')
        player_history = self.mcp_server.get_context('player_history')
        game_summary = self.mcp_server.get_context('game_summary')
        
        # Build prompt with context
        prompt = f"""Analyze this violation with game context:

Current Violation:
- Player: {violation['player_name']}
- Type: {violation['type']}
- Severity: {violation['severity']}

Game Context:
- Total violations: {game_summary['total_violations']}
- Recent violations: {len(recent)}
- Player history: {len(player_history.get(violation['player_name'], []))} previous violations

Question: Is this a pattern or isolated incident?
Should we escalate this violation?

Return JSON with: pattern_detected, escalate, reasoning"""
        
        # Call Bedrock with context
        response = self.bedrock.invoke_model(
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
        analysis = json.loads(result['content'][0]['text'])
        
        return analysis

# Create agent
agent = SecurityAgent(mcp_server)
```

---

## Hands-On: Test MCP Flow

Create `test_mcp.py`:

```python
from mcp_server import MCPServer
from security_agent import SecurityAgent

# Setup
mcp_server = MCPServer()
agent = SecurityAgent(mcp_server)

# Simulate violations
violations = [
    {
        'player_name': 'Cristiano Ronaldo',
        'type': 'perimeter_breach',
        'severity': 'warning'
    },
    {
        'player_name': 'Cristiano Ronaldo',
        'type': 'perimeter_breach',
        'severity': 'warning'
    },
    {
        'player_name': 'Lionel Messi',
        'type': 'equipment',
        'severity': 'info'
    }
]

# Process violations
for violation in violations:
    print(f"\n{'='*50}")
    print(f"Processing: {violation['player_name']} - {violation['type']}")
    
    # Publish to MCP
    mcp_server.publish_violation(violation)
    
    # Agent analyzes with context
    analysis = agent.analyze_with_context(violation)
    
    print(f"\nAnalysis:")
    print(f"  Pattern detected: {analysis['pattern_detected']}")
    print(f"  Escalate: {analysis['escalate']}")
    print(f"  Reasoning: {analysis['reasoning']}")

# Get game summary
summary = mcp_server.get_context('game_summary')
print(f"\n{'='*50}")
print("Game Summary:")
print(json.dumps(summary, indent=2))
```

Run it:
```bash
python3 test_mcp.py
```

**Expected Output**:
```
==================================================
Processing: Cristiano Ronaldo - perimeter_breach

Analysis:
  Pattern detected: False
  Escalate: False
  Reasoning: First violation, isolated incident

==================================================
Processing: Cristiano Ronaldo - perimeter_breach

Analysis:
  Pattern detected: True
  Escalate: True
  Reasoning: Second violation by same player, pattern emerging

==================================================
Game Summary:
{
  "total_violations": 3,
  "by_type": {
    "perimeter_breach": 2,
    "equipment": 1
  },
  "by_severity": {
    "warning": 2,
    "info": 1
  }
}
```

---

## MCP Benefits Demonstrated

### 1. Pattern Detection

**Without MCP**:
```python
# Agent sees only current violation
# No history, no context
```

**With MCP**:
```python
# Agent sees:
# - Current violation
# - Player history
# - Game patterns
# - Recent trends
```

### 2. Smart Escalation

```python
# First violation: Warning
# Second violation: Escalate (pattern detected)
# Third violation: Critical (repeated offender)
```

### 3. Real-Time Insights

```python
# MCP provides live game statistics
# Agent makes informed decisions
# No manual queries needed
```

---

## Hands-On Exercise

### Exercise 1: Add Custom Context

Extend MCP server with zone tracking:

```python
def get_context(self, query):
    if query == 'hot_zones':
        # Track which zones have most violations
        zone_counts = {}
        for item in self.violation_stream:
            zone = item['violation']['zone']
            zone_counts[zone] = zone_counts.get(zone, 0) + 1
        return zone_counts
```

### Exercise 2: Time-Based Context

Add time window filtering:

```python
def get_recent_violations(self, minutes=5):
    """Get violations from last N minutes"""
    from datetime import datetime, timedelta
    
    cutoff = datetime.utcnow() - timedelta(minutes=minutes)
    
    recent = []
    for item in self.violation_stream:
        timestamp = datetime.fromisoformat(item['timestamp'])
        if timestamp > cutoff:
            recent.append(item)
    
    return recent
```

### Exercise 3: Team Comparison

Compare violations between teams:

```python
def get_team_comparison(self):
    """Compare violations by team"""
    home_violations = []
    away_violations = []
    
    for item in self.violation_stream:
        team = item['violation']['team']
        if 'Home' in team:
            home_violations.append(item)
        else:
            away_violations.append(item)
    
    return {
        'home': len(home_violations),
        'away': len(away_violations)
    }
```

---

## MCP vs Traditional Polling

### Performance Comparison

**Traditional Polling**:
```python
# Query every 5 seconds
while True:
    violations = db.query()  # Database hit
    time.sleep(5)
    
# Cost: Continuous database queries
# Latency: Up to 5 seconds
```

**MCP Streaming**:
```python
# Subscribe once
mcp_client.subscribe('violations')

# Receive updates immediately
# Cost: Single connection
# Latency: < 1 second
```

### Cost Savings

| Approach | Database Queries/Hour | Cost |
|----------|----------------------|------|
| Polling (5s) | 720 | $0.72 |
| MCP Streaming | 0 | $0.00 |

---

## Production Considerations

### 1. Connection Management

```python
class MCPServer:
    def handle_disconnect(self, client_id):
        """Handle client disconnection"""
        if client_id in self.subscribers:
            self.subscribers.remove(client_id)
            print(f"Client {client_id} disconnected")
```

### 2. Message Buffering

```python
def publish_violation(self, violation):
    """Buffer messages for offline clients"""
    
    # Add to buffer
    self.message_buffer.append(violation)
    
    # Send to online subscribers
    for subscriber in self.subscribers:
        if self.is_connected(subscriber):
            self.send_to_subscriber(subscriber, violation)
```

### 3. Rate Limiting

```python
def publish_violation(self, violation):
    """Rate limit publications"""
    
    if self.should_throttle():
        self.buffer_violation(violation)
        return
    
    self.send_to_subscribers(violation)
```

---

## Chapter 8 Checklist

- [ ] Understand MCP concept
- [ ] Set up MCP server
- [ ] Connected AI agent to MCP
- [ ] Tested real-time streaming
- [ ] Saw pattern detection in action
- [ ] Completed exercises

---

## Next: Chapter 9 - Testing & Validation

We'll test the complete system end-to-end! →
