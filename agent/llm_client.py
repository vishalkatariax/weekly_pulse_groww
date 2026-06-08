import os
import time
from typing import Optional

import requests
from dotenv import load_dotenv

class RateLimitError(Exception):
    pass

class RateLimiter:
    def __init__(self,
                 requests_per_minute: int = 30,
                 tokens_per_minute: int = 12000,
                 requests_per_day: int = 1000,
                 tokens_per_day: int = 100000):
        self.requests_per_minute = requests_per_minute
        self.tokens_per_minute = tokens_per_minute
        self.requests_per_day = requests_per_day
        self.tokens_per_day = tokens_per_day

        self.minute_window_start = time.time()
        self.day_window_start = time.time()
        self.requests_this_minute = 0
        self.tokens_this_minute = 0
        self.requests_today = 0
        self.tokens_today = 0

    def _reset_if_needed(self):
        now = time.time()
        if now - self.minute_window_start >= 60:
            self.minute_window_start = now
            self.requests_this_minute = 0
            self.tokens_this_minute = 0
        if now - self.day_window_start >= 86400:
            self.day_window_start = now
            self.requests_today = 0
            self.tokens_today = 0

    def reserve(self, request_count: int = 1, token_count: int = 0):
        self._reset_if_needed()
        if self.requests_this_minute + request_count > self.requests_per_minute:
            raise RateLimitError("Request rate limit reached for the current minute")
        if self.tokens_this_minute + token_count > self.tokens_per_minute:
            raise RateLimitError("Token rate limit reached for the current minute")
        if self.requests_today + request_count > self.requests_per_day:
            raise RateLimitError("Daily request limit exceeded")
        if self.tokens_today + token_count > self.tokens_per_day:
            raise RateLimitError("Daily token limit exceeded")

        self.requests_this_minute += request_count
        self.tokens_this_minute += token_count
        self.requests_today += request_count
        self.tokens_today += token_count

    def available(self):
        self._reset_if_needed()
        return {
            "requests_remaining_minute": max(0, self.requests_per_minute - self.requests_this_minute),
            "tokens_remaining_minute": max(0, self.tokens_per_minute - self.tokens_this_minute),
            "requests_remaining_day": max(0, self.requests_per_day - self.requests_today),
            "tokens_remaining_day": max(0, self.tokens_per_day - self.tokens_today),
        }

class LLMClient:
    def __init__(self,
                 api_key: Optional[str] = None,
                 dry_run: bool = True,
                 requests_per_minute: int = 30,
                 tokens_per_minute: int = 12000,
                 requests_per_day: int = 1000,
                 tokens_per_day: int = 100000):
        env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
        env_path = os.path.normpath(env_path)
        load_dotenv(dotenv_path=env_path)
        self.api_key = api_key or os.environ.get("LLM_API_KEY") or os.environ.get("GROQ_API_KEY")
        self.dry_run = dry_run
        self.rate_limiter = RateLimiter(
            requests_per_minute=requests_per_minute,
            tokens_per_minute=tokens_per_minute,
            requests_per_day=requests_per_day,
            tokens_per_day=tokens_per_day,
        )

    def send_prompt(self, prompt: str, max_tokens: int = 512, estimated_tokens: int = 0) -> str:
        self.rate_limiter.reserve(request_count=1, token_count=estimated_tokens)
        if self.dry_run:
            return self.mock_response(prompt)

        if not self.api_key:
            raise ValueError(
                "No API key available for live LLM calls. Set LLM_API_KEY or GROQ_API_KEY in the environment."
            )

        return self._call_groq(prompt, max_tokens=max_tokens)

    def _call_groq(self, prompt: str, max_tokens: int = 512) -> str:
        url = "https://api.groq.com/openai/v1/responses"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "llama-3.3-70b-versatile",
            "input": prompt,
            "max_output_tokens": max_tokens,
            "temperature": 0.2,
        }
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            raise RuntimeError(f"Groq API request failed: {exc}") from exc

        return self._parse_groq_response(data)

    def _parse_groq_response(self, data):
        if not isinstance(data, dict):
            raise RuntimeError("Unexpected Groq API response format")
        if "error" in data and data["error"] is not None:
            error_message = data['error']
            if isinstance(error_message, dict) and 'message' in error_message:
                error_message = error_message['message']
            raise RuntimeError(f"Groq API error: {error_message}")
        if "output" in data and isinstance(data["output"], list) and data["output"]:
            text_chunks = []
            for item in data["output"]:
                if not isinstance(item, dict):
                    continue
                if "content" in item and isinstance(item["content"], list):
                    for content_piece in item["content"]:
                        if isinstance(content_piece, dict) and content_piece.get("type") == "output_text":
                            text_chunks.append(str(content_piece.get("text", "")).strip())
                if item.get("type") == "message" and isinstance(item.get("content"), list):
                    for content_piece in item["content"]:
                        if isinstance(content_piece, dict) and content_piece.get("type") == "output_text":
                            text_chunks.append(str(content_piece.get("text", "")).strip())
            if text_chunks:
                return " ".join(text_chunks).strip()
        if "choices" in data and isinstance(data["choices"], list) and data["choices"]:
            choice = data["choices"][0]
            return str(choice.get("text") or choice.get("message", "")).strip()
        if "completion" in data:
            return str(data["completion"]).strip()
        raise RuntimeError("Unexpected Groq API response format")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "input": prompt,
            "max_output_tokens": max_tokens,
            "temperature": 0.2,
        }
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            raise RuntimeError(f"Groq API request failed: {exc}") from exc

        if "error" in data:
            raise RuntimeError(f"Groq API error: {data['error']}")

        # Support multiple Groq response payload shapes.
        if isinstance(data, dict):
            if "output" in data and isinstance(data["output"], list) and data["output"]:
                content = data["output"][0].get("content")
                if isinstance(content, list):
                    return " ".join(str(item) for item in content).strip()
                return str(content or "").strip()
            if "choices" in data and isinstance(data["choices"], list) and data["choices"]:
                choice = data["choices"][0]
                return str(choice.get("text") or choice.get("message", "")).strip()

        raise RuntimeError("Unexpected Groq API response format")

    def mock_response(self, prompt: str) -> str:
        if "Generate 3 action items" in prompt:
            return (
                "1. Improve user onboarding validation flows to reduce OTP and KYC drop-off. "
                "2. Fix common payment and withdrawal error paths and surface clearer status updates. "
                "3. Strengthen customer support triage for high-frequency charge and fund issues."
            )
        if "Write a concise summary" in prompt:
            return (
                "Users are primarily struggling with Payments and Withdrawals, and a smaller but significant portion of feedback focuses on KYC and onboarding issues. "
                "Most complaints center on charges, customer support, and transaction reliability, while positive sentiment notes the app's ease of use and trading experience."
            )
        return "Mock LLM response placeholder."
