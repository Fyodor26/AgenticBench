# Agent Execution Engine - Implementation Guide

## Overview

The Agent Execution Engine is the core system that handles executing AI agents against evaluation tasks. It supports multiple LLM providers and includes sophisticated metrics calculation.

## Architecture

### Components

1. **AgentExecutor** (`agents/executor.py`)
   - Main routing class for agent execution
   - Supports multiple providers: OpenAI, Anthropic, Generic HTTP, Mock

2. **Provider-Specific Executors**
   - `OpenAIExecutor`: Execute against OpenAI APIs (GPT-4, GPT-4o, etc.)
   - `AnthropicExecutor`: Execute against Anthropic APIs (Claude)
   - `GenericHTTPExecutor`: Execute against any HTTP API
   - `MockExecutor`: Mock responses for testing

3. **ExecutorService** (`services/executor_service.py`)
   - Orchestrates agent execution
   - Manages retry logic with exponential backoff
   - Integrates with evaluation service for metrics calculation
   - Supports batch execution

4. **EvaluationService** (`services/evaluation_service.py`)
   - Calculates comprehensive metrics
   - Manages evaluation lifecycle
   - Generates leaderboards

## Database Schema Updates

### Agent Model Changes
```python
provider: str          # "openai", "anthropic", "generic", "mock"
model: str            # Model name (e.g., "gpt-4o", "claude-3-sonnet")
temperature: float    # Sampling temperature (0.0-2.0)
max_tokens: int       # Max output tokens
timeout: int          # Execution timeout in seconds
is_active: bool       # Enable/disable agent
```

### Evaluation Model Enhancements
```python
retry_count: int      # Number of retry attempts
metadata: dict        # Execution metadata (stop_reason, etc.)
```

### EvaluationMetrics Model Additions
```python
cost: float           # Execution cost
execution_time: float # Time taken
tokens_used: int      # Total tokens used
```

## API Endpoints

### Create Evaluation
```
POST /evaluations/
{
  "task_id": 1,
  "agent_id": 1
}
```

### Get Evaluation
```
GET /evaluations/{eval_id}
```

### List Evaluations
```
GET /evaluations/?task_id=1&agent_id=1&status=completed
```

### Calculate Metrics
```
POST /evaluations/{eval_id}/calculate-metrics
```

### Agent Leaderboard
```
GET /evaluations/leaderboard/agents?limit=50&offset=0
```

### Run All Agents
```
POST /evaluations/{task_id}/run-all-agents?agent_ids=1,2,3
```

### Evaluation Stats
```
GET /evaluations/stats/overview
```

## Metrics Calculation

### Correctness (40%)
- Jaccard similarity on word level
- Key phrase matching (3-gram overlap)
- Length similarity penalty

**Score Calculation:**
```
jaccard * 0.5 + phrase_match * 0.3 + length_ratio * 0.2
```

### Hallucination Score (20%)
- Detects uncertainty markers ("I'm not sure", "possibly", etc.)
- Rewards confidence markers ("definitely", "verified", etc.)
- Range: 0-100 (higher = fewer hallucinations)

### Tool Usage (20%)
- Detects API calls, database queries, function calls
- Base score: 40 + tool indicators
- Penalties for errors

### Planning Quality (20%)
- Detects structured reasoning: "plan", "step", "approach", "then", "therefore"
- Bonus for formatted output (numbered lists, bullet points)

### Overall Score
```
overall = (correctness * 0.4) + (hallucination * 0.2) + (tool_usage * 0.2) + (planning_quality * 0.2)
```

## Execution Flow

### Single Agent Execution
```
1. Create Evaluation record (status: pending)
2. Fetch Agent and Task details
3. Call AgentExecutor with appropriate provider
4. Update Evaluation with response, execution_time, tokens_used, cost
5. Calculate metrics using EvaluationService
6. Update Evaluation status to "completed" or "failed"
7. Retry logic: up to 3 attempts with exponential backoff
```

### Batch Execution
```
1. For each agent, create Evaluation record
2. Execute concurrently (up to max_concurrent limit, default 5)
3. Track success/failure per agent
4. Return summary results
```

## Provider Configuration

### OpenAI
```python
provider: "openai"
model: "gpt-4o"  # or "gpt-4", "gpt-3.5-turbo"
api_key: "sk-..."
temperature: 0.7
max_tokens: 2048
```

**Pricing:**
- GPT-4: $0.03/M input, $0.06/M output
- GPT-4o: $0.005/M input, $0.015/M output
- GPT-3.5: $0.0005/M input, $0.0015/M output

### Anthropic
```python
provider: "anthropic"
model: "claude-3-sonnet"  # or "claude-3-opus", "claude-3-haiku"
api_key: "sk-ant-..."
temperature: 0.7
max_tokens: 2048
```

**Pricing:**
- Claude-3-Opus: $0.015/M input, $0.075/M output
- Claude-3-Sonnet: $0.003/M input, $0.015/M output
- Claude-3-Haiku: $0.00025/M input, $0.00125/M output

### Generic HTTP
```python
provider: "generic"
api_endpoint: "http://localhost:8080/api/execute"
api_key: "optional-bearer-token"
```

Expected Response Format:
```json
{
  "response": "agent output",
  "tokens_used": 100,
  "prompt_tokens": 50,
  "completion_tokens": 50,
  "cost": 0.001,
  "metadata": {}
}
```

### Mock
```python
provider: "mock"
```

Mock responses for testing without API calls.

## Retry Logic

- **Max Retries:** 3
- **Initial Delay:** 2 seconds
- **Backoff Multiplier:** 2x
  - Retry 1: 2 seconds
  - Retry 2: 4 seconds
  - Retry 3: 8 seconds

Failures that trigger retry:
- Timeout
- Network errors
- API rate limits
- Temporary service issues

Final failure after all retries:
- Evaluation marked as "failed"
- Error message recorded
- Metrics not calculated

## Usage Examples

### Register Agent
```bash
curl -X POST http://localhost:8000/agents/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "GPT-4o",
    "description": "OpenAI GPT-4o",
    "provider": "openai",
    "model": "gpt-4o",
    "api_key": "sk-...",
    "temperature": 0.7,
    "is_active": true
  }'
```

### Create Task
```bash
curl -X POST http://localhost:8000/tasks/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Write a REST API",
    "description": "Write a simple REST API",
    "prompt": "Write a simple REST API using Python and FastAPI",
    "expected_output": "from fastapi import FastAPI...",
    "category": "Code Generation",
    "difficulty": "medium"
  }'
```

### Run Evaluation
```bash
curl -X POST http://localhost:8000/evaluations/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": 1,
    "agent_id": 1
  }'
```

### Get Leaderboard
```bash
curl http://localhost:8000/evaluations/leaderboard/agents?limit=10
```

## Performance Considerations

### Concurrent Execution
- Batch executor limits concurrent tasks to avoid overwhelming APIs
- Default: 5 concurrent executions
- Configurable via `max_concurrent` parameter

### Caching
- Agent credentials are not cached (always fetched fresh)
- Task prompts are not cached
- Metrics are computed on-demand or cached after evaluation

### Database Indexes
- `ix_agents_provider`: Fast provider lookups
- `ix_agents_is_active`: Filter active agents
- `ix_eval_agent_created`: Leaderboard queries
- `ix_eval_task_status`: Status filtering
- `ix_metrics_score`: Ranking queries

## Error Handling

### Execution Errors
- **Timeout**: Configured timeout exceeded
- **Network Error**: Connection failed
- **API Error**: Non-200 response status
- **Invalid Response**: Response not in expected format

All errors are logged with full context and stored in evaluation record.

## Monitoring & Debugging

Enable logging:
```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

Key log points:
- Evaluation start/completion
- Metrics calculation results
- Retry attempts
- Errors with full stack traces

## Future Enhancements

1. **Streaming Support**: Stream agent responses for real-time feedback
2. **Cost Capping**: Limit total cost per evaluation/agent
3. **Smart Retries**: Retry based on error type (not all errors warrant retry)
4. **Caching**: Cache expensive operations like metrics calculation
5. **Webhooks**: Notify external systems of completion
6. **Metrics Refinement**: Use LLM-based correctness evaluation
7. **Multi-language Support**: Execute agents in different programming languages
