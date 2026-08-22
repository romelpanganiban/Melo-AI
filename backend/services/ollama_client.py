"""Ollama LLM Integration for Melo-AI"""

import httpx
import json
from typing import Iterator, Optional
from core.logging import logger
from core.errors import ChatServiceError


class OllamaClient:
    """Client for interacting with Ollama API"""
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen3:8b",
        timeout: int = 300,
        num_predict: int = 512,
        keep_alive: str = "10m",
        num_ctx: int = 8192
    ):
        """Initialize Ollama client
        
        Args:
            base_url: Ollama API base URL (default: http://localhost:11434)
            model: Model name to use (default: qwen3:8b)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.num_predict = num_predict
        self.keep_alive = keep_alive
        self.num_ctx = num_ctx
        self.last_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        self.client = httpx.Client(timeout=timeout)

    def list_models(self) -> list[dict]:
        """Return the models installed in the Ollama instance."""
        response = self.client.get(f"{self.base_url}/api/tags")
        if response.status_code != 200:
            raise ChatServiceError(
                f"Ollama API error: {response.status_code} - {response.text}"
            )

        return response.json().get("models", [])
    
    def is_available(self) -> bool:
        """Check if Ollama server is available
        
        Returns:
            True if server is running, False otherwise
        """
        try:
            response = self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception as e:
            logger.warning(
                f"Ollama server not available: {str(e)}",
                extra={"base_url": self.base_url}
            )
            return False
    
    def is_model_available(self) -> bool:
        """Check if the specified model is available
        
        Returns:
            True if model is installed, False otherwise
        """
        try:
            response = self.client.get(f"{self.base_url}/api/tags")
            if response.status_code != 200:
                return False
            
            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            
            # Check if model name matches (with or without tag)
            for model_name in model_names:
                if model_name.startswith(self.model.split(":")[0]):
                    return True
            
            return False
        except Exception as e:
            logger.warning(
                f"Error checking model availability: {str(e)}",
                extra={"model": self.model}
            )
            return False
    
    def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 40
    ) -> str:
        """Generate a response using Ollama
        
        Args:
            prompt: User prompt/message
            system_prompt: System prompt for context
            temperature: Sampling temperature (0-2)
            top_p: Nucleus sampling parameter
            top_k: Top-K sampling parameter
        
        Returns:
            Generated response text
            
        Raises:
            ChatServiceError: If API call fails
        """
        try:
            # Build the full prompt with system message if provided
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            logger.info(
                "Generating response with Ollama",
                extra={
                    "model": self.model,
                    "prompt_length": len(prompt),
                    "temperature": temperature
                }
            )
            
            # Call Ollama API
            response = self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "temperature": temperature,
                    "top_p": top_p,
                    "top_k": top_k,
                    "num_predict": self.num_predict,
                    "keep_alive": self.keep_alive,
                    "num_ctx": self.num_ctx,
                }
            )
            
            if response.status_code != 200:
                raise ChatServiceError(
                    f"Ollama API error: {response.status_code} - {response.text}"
                )
            
            result = response.json()
            self.last_usage = {
                "prompt_tokens": result.get("prompt_eval_count", 0),
                "completion_tokens": result.get("eval_count", 0),
                "total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0),
            }
            generated_text = result.get("response", "").strip()
            
            if not generated_text:
                raise ChatServiceError("Ollama returned empty response")
            
            logger.info(
                "Response generated successfully",
                extra={
                    "model": self.model,
                    "response_length": len(generated_text)
                }
            )
            
            return generated_text
            
        except httpx.ConnectError as e:
            logger.error(
                f"Cannot connect to Ollama server at {self.base_url}",
                extra={"error": str(e)}
            )
            raise ChatServiceError(
                f"Cannot connect to Ollama. Make sure Ollama is running at {self.base_url}"
            )
        except httpx.TimeoutException as e:
            logger.error(
                f"Ollama request timeout",
                extra={"timeout": self.timeout}
            )
            raise ChatServiceError(
                f"Ollama request timed out after {self.timeout}s. The model might be processing a long request."
            )
        except Exception as e:
            logger.error(
                f"Error generating response: {str(e)}",
                extra={"model": self.model}
            )
            raise ChatServiceError(f"Failed to generate response: {str(e)}")

    def generate_response_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 40
    ) -> Iterator[str]:
        """Generate a streaming response using Ollama.

        Yields incremental text chunks as they arrive from Ollama.
        """
        try:
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"

            logger.info(
                "Generating streaming response with Ollama",
                extra={
                    "model": self.model,
                    "prompt_length": len(prompt),
                    "temperature": temperature
                }
            )

            with self.client.stream(
                "POST",
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": True,
                    "temperature": temperature,
                    "top_p": top_p,
                    "top_k": top_k,
                    "num_predict": self.num_predict,
                    "keep_alive": self.keep_alive,
                    "num_ctx": self.num_ctx,
                }
            ) as response:
                if response.status_code != 200:
                    raise ChatServiceError(
                        f"Ollama API error: {response.status_code}"
                    )

                for line in response.iter_lines():
                    if not line:
                        continue

                    try:
                        payload = json.loads(line)
                    except json.JSONDecodeError:
                        logger.warning("Skipping malformed Ollama stream chunk")
                        continue

                    text = payload.get("response", "")
                    if text:
                        yield text

                    if payload.get("done") is True:
                        self.last_usage = {
                            "prompt_tokens": payload.get("prompt_eval_count", 0),
                            "completion_tokens": payload.get("eval_count", 0),
                            "total_tokens": payload.get("prompt_eval_count", 0) + payload.get("eval_count", 0),
                        }
                        break

        except httpx.ConnectError as e:
            logger.error(
                f"Cannot connect to Ollama server at {self.base_url}",
                extra={"error": str(e)}
            )
            raise ChatServiceError(
                f"Cannot connect to Ollama. Make sure Ollama is running at {self.base_url}"
            )
        except httpx.TimeoutException:
            logger.error(
                "Ollama stream timeout",
                extra={"timeout": self.timeout}
            )
            raise ChatServiceError(
                f"Ollama request timed out after {self.timeout}s."
            )
        except Exception as e:
            logger.error(
                f"Error generating streaming response: {str(e)}",
                extra={"model": self.model}
            )
            raise ChatServiceError(f"Failed to generate streaming response: {str(e)}")
    
    def close(self) -> None:
        """Close the HTTP client"""
        self.client.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
