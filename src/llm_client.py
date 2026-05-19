"""
Thin wrapper around the Ollama HTTP API.

Handles temperature, timeout, retries (max 2), and JSON-mode prompting.
Isolating this means Ollama can be swapped for a mock during tests and
for prompt-comparison runs.

Public API:
    generate(prompt, schema=None) -> str
"""

from __future__ import annotations

import json
import logging
import time

import requests

logger = logging.getLogger(__name__)

_DEFAULT_BASE_URL = "http://localhost:11434"
_DEFAULT_MODEL = "llama3.2:1b"
_DEFAULT_TEMPERATURE = 0.0
_DEFAULT_TIMEOUT_S = 3600
_MAX_RETRIES = 2


def generate(
    prompt: str,
    schema: dict | None = None,
    *,
    model: str = _DEFAULT_MODEL,
    temperature: float = _DEFAULT_TEMPERATURE,
    base_url: str = _DEFAULT_BASE_URL,
    timeout_s: int = _DEFAULT_TIMEOUT_S,
    max_retries: int = _MAX_RETRIES,
) -> str:
    url = f"{base_url.rstrip('/')}/api/generate"

    if schema is not None:
        keys = ", ".join(f'"{k}"' for k in schema)
        prompt = (
            f"{prompt}\n\nRespond with valid JSON only. "
            f"The response must be a JSON object with keys: {keys}."
        )

    payload: dict = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature},
    }
    if schema is not None:
        payload["format"] = "json"

    last_exc: Exception | None = None
    for attempt in range(1, max_retries + 2):
        try:
            logger.debug("LLM request attempt %d/%d", attempt, max_retries + 1)
            resp = requests.post(url, json=payload, timeout=timeout_s)
            resp.raise_for_status()
            return resp.json()["response"]
        except (requests.RequestException, KeyError, ValueError) as exc:
            last_exc = exc
            if attempt <= max_retries:
                wait = 2 ** (attempt - 1)
                logger.warning("Attempt %d failed (%s); retrying in %ds", attempt, exc, wait)
                time.sleep(wait)
            else:
                logger.error("All %d attempts failed: %s", max_retries + 1, exc)

    raise RuntimeError(f"LLM generate failed after {max_retries + 1} attempts") from last_exc
