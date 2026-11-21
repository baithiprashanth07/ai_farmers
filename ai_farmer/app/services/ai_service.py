"""Provider-neutral language model access for farm-specific recommendations."""
from typing import Any, Dict, Optional, Tuple
from urllib.parse import quote

import httpx

from app.config import get_settings
from app.utils import logger


_DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",
    "groq": "llama-3.3-70b-versatile",
    "gemini": "gemini-2.0-flash",
    "anthropic": "claude-3-5-sonnet-latest",
    "openrouter": "meta-llama/llama-3.3-70b-instruct:free",
    "ollama": "llama3.1",
    "custom": "local-model",
}


class AIService:
    """Call hosted and local chat models without exposing credentials to clients."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def _provider_config(self) -> Tuple[str, Optional[str], str, Optional[str]]:
        requested = self.settings.ai_provider.strip().lower()
        configured = {
            "openai": self.settings.openai_api_key,
            "groq": self.settings.groq_api_key,
            "gemini": self.settings.gemini_api_key,
            "anthropic": self.settings.anthropic_api_key,
            "openrouter": self.settings.openrouter_api_key,
        }

        provider = requested
        if provider == "auto":
            provider = next(
                (name for name, key in configured.items() if key and not key.startswith("your-")),
                "",
            )
            if not provider and self.settings.ai_base_url:
                provider = "custom"
            if not provider:
                return "none", None, "", None

        if provider not in {*configured, "ollama", "custom"}:
            logger.warning("Unsupported AI_PROVIDER value; AI recommendations are disabled.")
            return "none", None, "", None

        key = self.settings.ai_api_key or configured.get(provider)
        if key and key.startswith("your-"):
            key = None
        base_url = self.settings.ai_base_url
        if provider == "openai":
            base_url = base_url or "https://api.openai.com/v1"
        elif provider == "groq":
            base_url = base_url or "https://api.groq.com/openai/v1"
        elif provider == "gemini":
            base_url = base_url or "https://generativelanguage.googleapis.com/v1beta/openai"
        elif provider == "openrouter":
            base_url = base_url or "https://openrouter.ai/api/v1"
        elif provider == "ollama":
            base_url = base_url or self.settings.ollama_base_url
        elif provider == "custom" and not base_url:
            logger.warning("AI_PROVIDER=custom requires AI_BASE_URL; AI advice is disabled.")
            return "none", None, "", None

        model = self.settings.ai_model
        if provider == "groq":
            model = model or self.settings.groq_model
        return provider, key, model or _DEFAULT_MODELS[provider], base_url

    def status(self) -> Dict[str, Any]:
        """Return safe provider readiness information; never return API keys."""
        provider, _, model, base_url = self._provider_config()
        return {
            "configured": provider != "none" and (provider == "ollama" or provider == "custom" or bool(self._provider_config()[1])),
            "provider": provider,
            "model": model or None,
            "endpoint": base_url if provider in {"ollama", "custom"} else None,
            "supported_providers": ["openai", "groq", "gemini", "anthropic", "openrouter", "ollama", "custom"],
        }

    def complete(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Return a model response, or None when no provider is configured or fails."""
        provider, api_key, model, base_url = self._provider_config()
        if provider == "none":
            return None
        if provider not in {"ollama", "custom"} and not api_key:
            logger.warning("AI provider {} is selected but has no API key configured.", provider)
            return None

        try:
            with httpx.Client(timeout=httpx.Timeout(30.0, connect=5.0)) as client:
                if provider == "anthropic":
                    response = client.post(
                        "https://api.anthropic.com/v1/messages",
                        headers={
                            "x-api-key": api_key or "",
                            "anthropic-version": "2023-06-01",
                            "content-type": "application/json",
                        },
                        json={
                            "model": model,
                            "max_tokens": 1200,
                            "system": system_prompt,
                            "messages": [{"role": "user", "content": user_prompt}],
                        },
                    )
                    response.raise_for_status()
                    blocks = response.json().get("content", [])
                    answer = "\n".join(
                        block["text"] for block in blocks
                        if block.get("type") == "text" and isinstance(block.get("text"), str)
                    )
                elif provider == "gemini":
                    response = client.post(
                        f"https://generativelanguage.googleapis.com/v1beta/models/{quote(model, safe='')}:generateContent",
                        params={"key": api_key},
                        json={
                            "systemInstruction": {"parts": [{"text": system_prompt}]},
                            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
                            "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1200},
                        },
                    )
                    response.raise_for_status()
                    candidates = response.json().get("candidates", [])
                    parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
                    answer = "\n".join(part["text"] for part in parts if isinstance(part.get("text"), str))
                else:
                    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
                    response = client.post(
                        f"{base_url.rstrip('/')}/chat/completions",
                        headers=headers,
                        json={
                            "model": model,
                            "temperature": 0.3,
                            "max_tokens": 1200,
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt},
                            ],
                        },
                    )
                    response.raise_for_status()
                    answer = response.json()["choices"][0]["message"]["content"]

            if isinstance(answer, str) and answer.strip():
                return answer.strip()
            logger.warning("AI provider {} returned an empty response.", provider)
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as error:
            status_code = getattr(getattr(error, "response", None), "status_code", None)
            logger.warning(
                "AI provider {} request failed{} ({}).",
                provider,
                f" with HTTP {status_code}" if status_code else "",
                type(error).__name__,
            )
        return None


ai_service = AIService()
