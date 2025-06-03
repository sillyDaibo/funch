import os
from typing import Optional, Dict, Any
import litellm

class LLMClient:
    """A unified client for interacting with various LLM providers."""
    
    def __init__(
        self,
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None
    ) -> None:
        """Initialize the LLM client.
        
        Args:
            model: The model name (e.g. "gpt-3.5-turbo", "claude-2", "deepseek-chat")
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            api_key: Provider API key (defaults to env vars)
            api_base: Custom API base URL
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.api_key = api_key
        self.api_base = api_base

    def invoke(
        self, 
        prompt: str,
        system_message: Optional[str] = None,
        **kwargs: Dict[str, Any]
    ) -> str:
        """Invoke the LLM with a prompt.
        
        Args:
            prompt: User prompt/message
            system_message: Optional system message
            **kwargs: Additional parameters for the LLM call
            
        Returns:
            Generated text response
        """
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        response = litellm.completion(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            api_key=self.api_key,
            api_base=self.api_base,
            **kwargs
        )

        return response.choices[0].message.content

    async def invoke_async(
        self, 
        prompt: str,
        system_message: Optional[str] = None,
        **kwargs: Dict[str, Any]
    ) -> str:
        """Asynchronously invoke the LLM with a prompt.
        
        Args:
            prompt: User prompt/message
            system_message: Optional system message
            **kwargs: Additional parameters for the LLM call
            
        Returns:
            Generated text response
        """
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        response = await litellm.acompletion(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            api_key=self.api_key,
            api_base=self.api_base,
            **kwargs
        )

        return response.choices[0].message.content
