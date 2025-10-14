"""
OpenAI LLM Provider Implementation.
"""

from typing import AsyncGenerator, Optional
try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None
import structlog

from ..types import LLMConfig
from .base import LLMProvider, LLMResponse

logger = structlog.get_logger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider implementation."""
    
    def __init__(self, config: LLMConfig):
        """Initialize OpenAI provider."""
        super().__init__(config)
        if not AsyncOpenAI:
            raise ImportError("openai package not installed. Install with: pip install openai")
        self.client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url if config.base_url else None
        )
        logger.info("openai_provider_initialized", model=config.model)
    
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate a response from OpenAI."""
        system_prompt = kwargs.pop('system_prompt', None)
        temperature = kwargs.pop('temperature', self.config.temperature)
        max_tokens = kwargs.pop('max_tokens', self.config.max_tokens)
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            content = response.choices[0].message.content or ""
            usage = {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0
            }
            
            return LLMResponse(content=content, usage=usage)
            
        except Exception as e:
            logger.error("openai_generation_error", error=str(e))
            raise
    
    async def stream(self, prompt: str, **kwargs) -> AsyncGenerator[LLMResponse, None]:
        """Stream a response from OpenAI."""
        system_prompt = kwargs.pop('system_prompt', None)
        temperature = kwargs.pop('temperature', self.config.temperature)
        max_tokens = kwargs.pop('max_tokens', self.config.max_tokens)
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            stream = await self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield LLMResponse(content=chunk.choices[0].delta.content)
                    
        except Exception as e:
            logger.error("openai_streaming_error", error=str(e))
            raise
    
    async def health_check(self) -> dict:
        """Check if the provider is healthy."""
        try:
            await self.client.models.list()
            return {
                "status": "healthy",
                "provider": "openai",
                "model": self.config.model
            }
        except Exception as e:
            logger.error("openai_health_check_error", error=str(e))
            return {
                "status": "unhealthy",
                "provider": "openai",
                "error": str(e)
            }
