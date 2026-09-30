"""
===================================================================
WEEK 10 - GEMINI CLIENT HELPER WITH EXPONENTIAL BACKOFF
===================================================================
Provides robust model generation with exponential backoff on rate
limits (429 / RESOURCE_EXHAUSTED) to ensure uninterrupted test runs.
===================================================================
"""

import os
import sys
import time
import logging
from google import genai
from google.genai import types

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="[GEMINI-CLIENT] %(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("gemini_client")

PRIMARY_MODEL = "gemini-3.5-flash-lite"
FALLBACK_MODEL = "gemini-flash-latest"


def get_gemini_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("Missing GEMINI_API_KEY / GOOGLE_API_KEY")
    return genai.Client(api_key=api_key)


def safe_generate_content(
    client: genai.Client,
    contents,
    config: types.GenerateContentConfig,
    max_retries: int = 5
):
    """Executes Gemini content generation with exponential backoff on rate limits."""
    models_to_try = [PRIMARY_MODEL, FALLBACK_MODEL]

    for model in models_to_try:
        for attempt in range(max_retries):
            try:
                return client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config
                )
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    wait_s = 6 * (attempt + 1)
                    logger.warning(f"Rate limited (429) on {model}. Retrying in {wait_s}s (attempt {attempt + 1}/{max_retries})...")
                    time.sleep(wait_s)
                elif "503" in err_str or "Service Unavailable" in err_str:
                    wait_s = 4 * (attempt + 1)
                    logger.warning(f"Server error (503) on {model}. Retrying in {wait_s}s...")
                    time.sleep(wait_s)
                elif "404" in err_str:
                    logger.warning(f"Model {model} returned 404 Not Found. Skipping model.")
                    break
                else:
                    logger.error(f"Unrecoverable error on {model}: {e}")
                    raise e

    raise RuntimeError("All Gemini model generation attempts exhausted.")
