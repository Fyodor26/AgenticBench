import asyncio
import time
import traceback

import ollama

from app.agents.base import BaseAgent
from app.evaluation.result import ExecutionResult


class OllamaAgent(BaseAgent):

    async def execute(
        self,
        prompt: str,
        model: str = "qwen3:4b",
        timeout: int = 300,
        **kwargs,
    ) -> ExecutionResult:

        print("========== OLLAMA AGENT ==========")
        print(f"Model: {model}")
        print(f"Prompt: {prompt}")
        print(f"Timeout: {timeout}")

        start_time = time.time()

        try:
            client = ollama.AsyncClient()

            response = await asyncio.wait_for(
                client.chat(
                    model=model,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                ),
                timeout=timeout,
            )

            execution_time = time.time() - start_time

            output = response["message"]["content"]

            prompt_tokens = response.get(
                "prompt_eval_count",
                0,
            )

            completion_tokens = response.get(
                "eval_count",
                0,
            )

            print("Ollama execution completed")
            print(output)
            print(f"Execution time: {execution_time:.2f}s")

            return ExecutionResult(
    success=True,
    output=output,
    execution_time=execution_time,
    tokens_used=prompt_tokens + completion_tokens,
    prompt_tokens=prompt_tokens,
    completion_tokens=completion_tokens,
    cost=0.0,
    model=model,
    score=0.0,   # will be calculated later
    metadata={
        "provider": "ollama",
    },
)

        except asyncio.TimeoutError:

            execution_time = time.time() - start_time

            print(
                f"Ollama execution timed out after "
                f"{timeout} seconds"
            )

            return ExecutionResult(
                success=False,
                error=f"Ollama execution timeout after {timeout} seconds",
                execution_time=execution_time,
                model=model,
metadata={
    "provider": "ollama",
    "exception": "TimeoutError",
}
            )

        except Exception as e:

            execution_time = time.time() - start_time

            print("Ollama execution failed:")
            traceback.print_exc()

            return ExecutionResult(
                success=False,
                error=str(e),
                execution_time=execution_time,
                metadata={
                    "provider": "ollama",
                    "model": model,
                    "exception": type(e).__name__,
                },
            )