"""Base agent configuration and utilities"""
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from crewai import Agent, Task, LLM
import os


class LLMProvider:
    """Factory for creating LLM instances (CrewAI 1.x / LiteLLM format)"""

    @staticmethod
    def get_llm(provider: str = "anthropic", model: str = None, temperature: float = 0.1):
        """
        Get LLM instance based on provider

        Args:
            provider: 'openai', 'anthropic', or 'google'
            model: Model name (optional, uses defaults)
            temperature: Temperature for generation (0.0-1.0)

        Returns:
            crewai.LLM instance
        """
        if provider == "openai":
            model = model or "gpt-4-turbo-preview"
            return LLM(
                model=f"openai/{model}",
                temperature=temperature,
                api_key=os.getenv("OPENAI_API_KEY")
            )

        elif provider == "anthropic":
            model = model or "claude-sonnet-4-6"
            return LLM(
                model=f"anthropic/{model}",
                temperature=temperature,
                api_key=os.getenv("ANTHROPIC_API_KEY")
            )

        elif provider == "google":
            model = model or "gemini/gemini-pro"
            return LLM(
                model=f"gemini/{model}",
                temperature=temperature,
                api_key=os.getenv("GOOGLE_API_KEY")
            )

        else:
            raise ValueError(f"Unknown provider: {provider}")


class BaseVulnerabilityAgent(ABC):
    """Base class for all vulnerability analysis agents"""

    def __init__(
        self,
        llm_provider: str = "anthropic",
        llm_model: Optional[str] = None,
        temperature: float = 0.1
    ):
        self.llm = LLMProvider.get_llm(llm_provider, llm_model, temperature)
        self.agent = self._create_agent()

    @abstractmethod
    def _create_agent(self) -> Agent:
        """Create the CrewAI agent with role and goal"""
        pass

    @abstractmethod
    def create_task(self, context: Dict[str, Any]) -> Task:
        """Create a task for this agent"""
        pass

    @abstractmethod
    def process_result(self, task_output: Any) -> Dict[str, Any]:
        """Process the task output into structured data"""
        pass
