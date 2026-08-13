"""
Agent Execution Engine - Handles execution of agents from different providers
with support for OpenAI, Anthropic, and generic HTTP-based agents.
"""

import asyncio
import time
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import httpx
import logging
import traceback
import ollama
from app.agents.ollama_agent import OllamaAgent
from app.agents.gemini_agent import GeminiAgent
from app.evaluation.result import ExecutionResult

logger = logging.getLogger(__name__)


class AgentProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GENERIC = "generic"
    MOCK = "mock"
    OLLAMA = "ollama"
    GEMINI ="gemini"



class BaseExecutor:
    """Base class for agent executors"""
    
    async def execute(
        self,
        prompt: str,
        model: str,
        api_key: str,
        **kwargs
    ) -> ExecutionResult:
        raise NotImplementedError


class AgentExecutor:
    """Routes execution to the correct AI provider."""

    EXECUTORS = {
        AgentProvider.OLLAMA: OllamaAgent(),
        AgentProvider.GEMINI: GeminiAgent(),
    }

    @staticmethod
    async def execute(
        prompt: str,
        provider: str,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        api_endpoint: Optional[str] = None,
        timeout: int = 60,
        **kwargs,
    ) -> ExecutionResult:

        try:
            provider_enum = AgentProvider(provider.lower())

            print(f"Executing with provider: {provider_enum}")

        except ValueError:
            return ExecutionResult(
                success=False,
                error=f"Unknown provider: {provider}",
            )

        executor = AgentExecutor.EXECUTORS.get(provider_enum)

        print(
            f"Executor found: {executor} "
            f"for provider: {provider_enum}"
        )

        if not executor:
            return ExecutionResult(
                success=False,
                error=f"No executor configured for provider: {provider}",
            )

        if provider_enum == AgentProvider.OLLAMA:
            return await executor.execute(
                prompt=prompt,
                model=model or "llama3",
                timeout=timeout,
                **kwargs,
            )

        elif provider_enum == AgentProvider.GEMINI:
            return await executor.execute(
                prompt=prompt,
                model=model or "gemini-3.5-flash",
                api_key=api_key,
                timeout=timeout,
                **kwargs,
            )

        return ExecutionResult(
            success=False,
            error=f"Unsupported provider: {provider}",
        )