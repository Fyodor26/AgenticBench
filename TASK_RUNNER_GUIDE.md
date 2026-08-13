# Task Runner Service - Documentation

## Overview

The Task Runner Service orchestrates comprehensive benchmark runs where tasks are executed against multiple agents. It handles sequential and parallel execution, aggregates results, and generates detailed reports.

## Architecture

### Core Components

1. **TaskRunnerService** - Main orchestration logic
2. **ExecutionMode** - Enum for execution strategies
3. **BenchmarkConfig** - Configuration for benchmark runs
4. **BenchmarkResult** - Result container with all metrics
5. **BenchmarkScheduler** - Handles periodic runs (future)

## Execution Modes

### PARALLEL (Default)
- Execute all agents concurrently
- Respects `max_concurrent` limit (default: 5)
- Faster overall execution
- Useful for high-throughput benchmarking

```python
config = BenchmarkConfig(
    task_id=1,
    mode=ExecutionMode.PARALLEL,
    max_concurrent=10  # Run up to 10 agents simultaneously
)
```

### SEQUENTIAL
- Execute agents one at a time
- Useful for debugging or low-resource environments
- Better resource isolation

```python
config = BenchmarkConfig(
    task_id=1,
    mode=ExecutionMode.SEQUENTIAL
)
```

### ALL_AGENTS
- Run all active agents

```python
config = BenchmarkConfig(
    task_id=1,
    agent_ids=None  # None means all active agents
)
```

### SPECIFIC_AGENTS
- Run only specified agents

```python
config = BenchmarkConfig(
    task_id=1,
    agent_ids=[1, 3, 5]  # Only agents 1, 3, 5
)
```

## API Endpoints

### Run Task Benchmark
```
POST /task-runner/run?task_id=1&mode=parallel&max_concurrent=5&timeout=60
```

Response:
```json
{
  "message": "Benchmark started for task 'Write API'",
  "task_id": 1,
  "mode": "parallel",
  "max_concurrent": 5,
  "timeout_per_agent": 60
}
```

### Get Task Results
```
GET /task-runner/results/{task_id}
```

Response:
```json
{
  "task_id": 1,
  "task_title": "Write REST API",
  "evaluations_count": 5,
  "agent_performance": {
    "1": {
      "agent_name": "GPT-4o",
      "provider": "gpt-4o",
      "evaluations": 1,
      "total_cost": 0.015,
      "average_score": 85.5,
      "max_score": 85.5,
      "min_score": 85.5
    }
  },
  "summary": {
    "total_evaluations": 5,
    "total_cost": 0.075,
    "total_tokens": 15000
  }
}
```

### Get Task Comparison
```
GET /task-runner/comparison/{task_id}
```

Detailed agent-by-agent comparison with all metrics:

```json
{
  "task_id": 1,
  "task_title": "Write REST API",
  "agents_count": 5,
  "agents": [
    {
      "rank": 1,
      "agent_id": 1,
      "agent_name": "GPT-4o",
      "provider": "openai",
      "model": "gpt-4o",
      "overall_score": 87.3,
      "correctness": 90.5,
      "hallucination": 85.0,
      "tool_usage": 88.0,
      "planning_quality": 82.5,
      "execution_time": 2.5,
      "tokens_used": 3500,
      "cost": 0.015,
      "success": true
    },
    {
      "rank": 2,
      "agent_id": 2,
      "agent_name": "Claude-3-Sonnet",
      "provider": "anthropic",
      "model": "claude-3-sonnet",
      "overall_score": 85.2,
      "correctness": 88.0,
      "hallucination": 83.0,
      "tool_usage": 85.5,
      "planning_quality": 85.0,
      "execution_time": 3.1,
      "tokens_used": 2800,
      "cost": 0.010,
      "success": true
    }
  ]
}
```

### Get Task Statistics
```
GET /task-runner/tasks/{task_id}/stats
```

### Run All Tasks
```
POST /task-runner/run-all
```

Run benchmarks for all active tasks in parallel.

### Run Task Against Agent
```
POST /task-runner/tasks/{task_id}/run-against-agent?agent_id=1&timeout=60
```

### Performance Matrix
```
GET /task-runner/performance-matrix?limit=10
```

Shows agent performance across multiple tasks:

```json
{
  "tasks": [
    {"id": 1, "title": "Write REST API"},
    {"id": 2, "title": "Write Database Schema"}
  ],
  "agents": [
    {
      "agent_id": 1,
      "agent_name": "GPT-4o",
      "provider": "openai",
      "tasks": {
        "Write REST API": 87.3,
        "Write Database Schema": 82.1
      }
    }
  ]
}
```

## Result Structure

### BenchmarkResult
```python
@dataclass
class BenchmarkResult:
    benchmark_id: str              # Unique ID for this run
    task_id: int                   # Task that was run
    total_agents: int              # Total agents executed
    completed: int                 # Successfully completed
    failed: int                    # Failed executions
    start_time: datetime           # Start timestamp
    end_time: datetime             # End timestamp
    duration_seconds: float        # Total duration
    evaluations: List[dict]        # Per-evaluation results
    summary_stats: Dict[str, Any]  # Aggregated statistics
```

### Summary Statistics
```python
{
    "total_evaluations": 5,
    "successful_evaluations": 5,
    "failed_evaluations": 0,
    "success_rate": 100.0,
    "scores": {
        "mean": 85.6,
        "max": 90.2,
        "min": 78.5,
        "median": 85.5
    },
    "costs": {
        "total": 0.075,
        "mean": 0.015,
        "max": 0.020
    },
    "execution_time": {
        "mean": 2.8,
        "max": 3.5,
        "min": 1.9
    }
}
```

## Usage Examples

### Example 1: Run All Agents Against a Task
```bash
curl -X POST http://localhost:8000/task-runner/run \
  -H "Content-Type: application/json" \
  -d '{"task_id": 1}'
```

### Example 2: Run Specific Agents with Custom Timeout
```bash
curl -X POST "http://localhost:8000/task-runner/run?task_id=1&agent_ids=1,2,3&timeout=120&mode=parallel"
```

### Example 3: Sequential Execution
```bash
curl -X POST "http://localhost:8000/task-runner/run?task_id=1&mode=sequential"
```

### Example 4: Get Detailed Results
```bash
curl http://localhost:8000/task-runner/comparison/1
```

### Example 5: View Performance Across Tasks
```bash
curl http://localhost:8000/task-runner/performance-matrix?limit=20
```

## Configuration Options

### Execution Timeout
- **Default**: 60 seconds
- **Min**: 10 seconds
- **Max**: 600 seconds
- Controls per-agent execution timeout

### Max Concurrent
- **Default**: 5 concurrent executions
- **Min**: 1 (sequential equivalent)
- **Max**: 50 (safety limit)
- Only applies to PARALLEL mode

### Auto Calculate Metrics
- **Default**: True
- Automatically calculate metrics after execution
- Set to False for faster completion if metrics not needed

### Create Report
- **Default**: True
- Generate summary report after completion

## Performance Considerations

### Parallel Execution
- Best for high throughput
- Respects concurrency limits to avoid overwhelming APIs
- 5 concurrent = good balance for API rate limits

### Sequential Execution
- Best for debugging
- Better for resource-constrained environments
- ~5x slower than parallel with 5 agents

### Timeout Management
- Each agent execution has its own timeout
- Total execution time = max(agent_timeout) + overhead
- Retry logic adds additional time

## Monitoring & Logging

Key log messages:
```
Starting task runner for task 1: Write REST API
Running against 5 agents in parallel mode
Started evaluation run for task 1
Task 1 complete. Completed: 5/5, Duration: 12.5s
```

## Advanced Features

### Performance Matrix
Visualize how agents perform across different task types:
- Useful for identifying agent strengths/weaknesses
- Helps in task categorization
- Shows cost efficiency patterns

### Batch Operations
Run all active tasks at once:
```bash
curl -X POST http://localhost:8000/task-runner/run-all
```

This executes:
1. Query all active tasks
2. Create benchmark config for each
3. Run in background
4. Track all results independently

## Future Enhancements

1. **Scheduled Benchmarks**: Run benchmarks on a schedule
2. **Historical Tracking**: Track performance over time
3. **Regression Detection**: Alert on performance degradation
4. **Cost Optimization**: Suggest cheaper models for similar scores
5. **Parallel Benchmarking**: Run multiple tasks in parallel
6. **Custom Metrics**: Allow user-defined metric calculations

## Troubleshooting

### Slow Execution
- Check if sequential mode is being used
- Increase max_concurrent (up to 50)
- Check for network issues

### High Failure Rate
- Check agent API key/credentials
- Verify task prompt is valid
- Check timeout isn't too short
- Review agent logs

### High Costs
- Use cheaper models (GPT-3.5, Claude Haiku)
- Reduce number of agents
- Optimize task prompts for brevity
- Run fewer times or cache results

## Best Practices

1. **Test First**: Run 1-2 agents before benchmarking all
2. **Use Appropriate Timeouts**: Don't set too low
3. **Monitor Costs**: Start with GPT-3.5, move to GPT-4 for important tasks
4. **Batch Operations**: Run all agents at once, not individually
5. **Review Results**: Check comparison view for anomalies
6. **Archive Results**: Save important benchmark runs
