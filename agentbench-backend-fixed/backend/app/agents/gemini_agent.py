import asyncio
import logging
import time
from typing import Optional

from app.evaluation.result import ExecutionResult

logger = logging.getLogger(__name__)

try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    genai = None
    GENAI_AVAILABLE = False
    logger.warning(
        "google-genai is not installed; the Gemini provider will return an "
        "error when used. Install it with `pip install google-genai`."
    )


class GeminiAgent:
    """
    Executor for Google Gemini models.
    """

    async def execute(
        self,
        prompt: str,
        model: str = "gemini-3.5-flash",
        api_key: Optional[str] = None,
        timeout: int = 60,
        **kwargs,
    ) -> ExecutionResult:

        if not GENAI_AVAILABLE:
            return ExecutionResult(
                success=False,
                error="Gemini provider is unavailable: google-genai package is not installed.",
            )

        if not api_key:
            return ExecutionResult(
                success=False,
                error="Gemini API key is missing",
            )

        start_time = time.perf_counter()

        try:
            client = genai.Client(api_key=api_key)
            print(api_key)

            response = await asyncio.wait_for(
                asyncio.to_thread(
                    client.models.generate_content,
                    model=model,
                    contents=prompt,
                ),
                timeout=timeout,
            )

            execution_time = time.perf_counter() - start_time

            return ExecutionResult(
                success=True,
                output=response.text,
                execution_time=execution_time,
                tokens_used=None,
                prompt_tokens=None,
                completion_tokens=None,
                cost=0.0,
                metadata={
                    "provider": "gemini",
                    "model": model,
                },
            )

        except asyncio.TimeoutError:
            execution_time = time.perf_counter() - start_time

            return ExecutionResult(
                success=False,
                error=f"Gemini execution timed out after {timeout} seconds",
                execution_time=execution_time,
                metadata={
                    "provider": "gemini",
                    "model": model,
                },
            )

        except Exception as e:
            execution_time = time.perf_counter() - start_time
            logger.error("Gemini execution failed: %s", e)

            return ExecutionResult(
                success=False,
                error=str(e),
                execution_time=execution_time,
                metadata={
                    "provider": "gemini",
                    "model": model,
                    "exception_type": type(e).__name__,
                },
            )
