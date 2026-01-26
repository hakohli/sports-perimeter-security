# Chapter 3: Amazon Bedrock Deep Dive

**Duration**: 45 minutes

## Objectives
- Understand Amazon Bedrock capabilities
- Learn Claude 3.5 Sonnet features
- Master prompt engineering for video analysis
- Test Bedrock API hands-on

---

## What is Amazon Bedrock?

**Amazon Bedrock** is a fully managed service that provides access to foundation models (FMs) from leading AI companies through a single API.

### Key Features
- ✅ **No infrastructure management** - Serverless
- ✅ **Multiple models** - Claude, Llama, Titan, etc.
- ✅ **Pay-per-use** - No upfront costs
- ✅ **Secure** - Data stays in your AWS account
- ✅ **Scalable** - Handles any workload

### Why Bedrock for Sports Security?

**Traditional Approach**:
- Train custom ML model (weeks/months)
- Collect training data (thousands of images)
- Manage infrastructure (GPUs, servers)
- Update models regularly

**Bedrock Approach**:
- Use pre-trained Claude model (ready now)
- No training data needed
- No infrastructure to manage
- Always latest model

---

## Claude 3.5 Sonnet

**Model ID**: `us.anthropic.claude-3-5-sonnet-20241022-v2:0`

### Capabilities
- 📝 Text analysis
- 🖼️ Image understanding
- 📄 Document processing
- 🎯 Structured output (JSON)
- 🧠 Context awareness

### Perfect for Sports Security
- Understands sports rules
- Analyzes video frames
- Classifies violations
- Provides explanations
- Gives confidence scores

---

## Hands-On: Your First Bedrock Call

### Step 1: Enable Model Access

1. Go to AWS Console → Bedrock
2. Click "Model access"
3. Enable "Claude 3.5 Sonnet"
4. Wait for approval (~2 minutes)

### Step 2: Test Basic API Call

Create `test_bedrock.py`:

```python
import boto3
import json

bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

response = bedrock.invoke_model(
    modelId='us.anthropic.claude-3-5-sonnet-20241022-v2:0',
    body=json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 500,
        "messages": [{
            "role": "user",
            "content": "Explain what a perimeter breach is in soccer."
        }]
    })
)

result = json.loads(response['body'].read())
print(result['content'][0]['text'])
```

Run it:
```bash
python3 test_bedrock.py
```

**Expected Output**: Claude explains perimeter breach in soccer

---

## Prompt Engineering for Violation Detection

### Basic Prompt (Not Good)
```
Is this a violation?
```

**Problems**:
- Too vague
- No context
- Unclear output format

### Better Prompt
```
Analyze this soccer violation:
Type: perimeter_breach
Player: Cristiano Ronaldo
Zone: sideline

Is this valid? Return yes or no.
```

**Better, but**:
- Still lacks structure
- No confidence score
- Missing details

### Optimal Prompt (What We Use)
```
Analyze this potential soccer game violation:

Type: perimeter_breach
Zone: sideline
Player: Cristiano Ronaldo (#7)
Team: Home Team

CRITICAL REQUIREMENTS:
1. ONLY report violations by PLAYERS (ignore audience, staff, coaches)
2. ONLY return confidence: 1.0 if 100% certain
3. Return confidence: 0.0 for anything else

Return JSON with:
- valid: true/false
- severity: info/warning/violation/critical
- action: recommended action
- explanation: brief explanation
- confidence: 1.0 or 0.0
- subject_type: "player" or "non-player"

Return ONLY valid JSON.
```

**Why This Works**:
- ✅ Clear requirements
- ✅ Structured output
- ✅ Confidence scoring
- ✅ Subject classification
- ✅ Actionable results

---

## Hands-On: Test Violation Analysis

Create `test_violation_analysis.py`:

```python
import boto3
import json

bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

def analyze_violation(player_name, team, violation_type):
    """Test violation analysis with Bedrock"""
    
    prompt = f"""Analyze this potential soccer game violation:

Type: {violation_type}
Zone: sideline
Player: {player_name}
Team: {team}

CRITICAL REQUIREMENTS:
1. ONLY report violations by PLAYERS
2. ONLY return confidence: 1.0 if 100% certain
3. Return confidence: 0.0 for anything else

Return JSON with:
- valid: true/false
- severity: info/warning/violation/critical
- action: recommended action
- explanation: brief explanation
- confidence: 1.0 or 0.0
- subject_type: "player" or "non-player"

Return ONLY valid JSON."""

    response = bedrock.invoke_model(
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

# Test with different scenarios
print("Test 1: Player violation")
result1 = analyze_violation("Cristiano Ronaldo", "Home Team", "perimeter_breach")
print(json.dumps(result1, indent=2))

print("\nTest 2: Coach on field (should reject)")
result2 = analyze_violation("Coach Smith", "Home Team", "perimeter_breach")
print(json.dumps(result2, indent=2))
```

Run it:
```bash
python3 test_violation_analysis.py
```

**Expected**:
- Test 1: `valid: true, confidence: 1.0`
- Test 2: `valid: false, confidence: 0.0` (not a player)

---

## Understanding Bedrock Pricing

### Cost Structure
- **Input tokens**: $0.003 per 1,000 tokens
- **Output tokens**: $0.015 per 1,000 tokens

### Our Usage
- **Prompt**: ~200 tokens
- **Response**: ~100 tokens
- **Cost per violation**: ~$0.006

### Workshop Cost
- 50 violations analyzed
- Total: ~$0.30 for Bedrock

**Very affordable!**

---

## Bedrock Best Practices

### 1. Structured Output
Always request JSON for programmatic use:
```
Return ONLY valid JSON.
```

### 2. Clear Requirements
Be explicit about what you want:
```
CRITICAL REQUIREMENTS:
1. Only report X
2. Only return Y
```

### 3. Confidence Scoring
Always ask for confidence:
```
confidence: 1.0 (100% certain) or 0.0 (not certain)
```

### 4. Error Handling
```python
try:
    analysis = json.loads(result['content'][0]['text'])
except:
    # Fallback logic
    analysis = {'valid': False, 'confidence': 0.0}
```

---

## Hands-On Exercise

### Exercise 1: Modify the Prompt

Edit the prompt to detect **offsides** in soccer:

```python
prompt = f"""Analyze this potential offsides violation:

Player: {player_name}
Position: {position}
Offside line: {offside_line}

Is the player in an offside position?
Return JSON with valid, confidence, explanation.
"""
```

### Exercise 2: Test Different Sports

Modify for basketball:
- Violation type: "lane_violation"
- Zone: "paint"
- Rule: "3-second rule"

### Exercise 3: Adjust Confidence

What happens if you change confidence threshold to 0.95?
- More violations detected?
- More false positives?

---

## Key Takeaways

✅ **Bedrock is serverless** - No infrastructure to manage
✅ **Claude understands context** - Sports rules, player roles
✅ **Structured output** - JSON for easy integration
✅ **Confidence scoring** - Know when AI is certain
✅ **Cost-effective** - Pay only for what you use

---

## Chapter 3 Checklist

- [ ] Bedrock model access enabled
- [ ] First API call successful
- [ ] Understand prompt engineering
- [ ] Tested violation analysis
- [ ] Completed exercises
- [ ] Understand pricing

---

## Next: Chapter 4 - Video Processing

We'll learn how to extract frames from videos and detect violations!

**Break Time**: 15 minutes ☕

After break, we'll process real video! →
