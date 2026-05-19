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
_DEFAULT_MODEL = "llama3.1:8b"
_DEFAULT_TEMPERATURE = 0.0
_DEFAULT_TIMEOUT_S = 120
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
    pass
