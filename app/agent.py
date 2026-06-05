from loguru import logger
import json
from enum import STRICT
from time import time
from processors.communication_summary_processor import empty_summary, build_summary_prompt
from utils.llm import ask_local_model

import re
import requests

from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL, ENABLE_THINKING

STRICT_JSON_SYSTEM_PROMPT = """
You are a strict JSON classification engine for an executive assistant.
Return only valid JSON.
Do not explain.
Do not reason out loud.
do not include Markdown.
Do not include text before or after the JSON.
"""


def load_strict_json_system_prompt() -> str:
    with open("app/prompts/strict_json_system_prompt.md", "r", encoding="utf-8") as file:
        return file.read()


OUTPUT_TOKENS_PER_MESSAGE = 100

def summarize_messages_no_batch(messages: list[dict[str,str]]) -> dict[str, list[dict[str,str]]]:
    if not messages:
        return empty_summary()

    start_time = time()

    logger.info(f"Processing all {len(messages)} messages in one request")

    prompt = build_summary_prompt(messages)
    system_prompt = load_strict_json_system_prompt()

    predicted_output_tokens = OUTPUT_TOKENS_PER_MESSAGE * len(messages)
    context_tokens = 4096

    response = ask_local_model(prompt, system_prompt=system_prompt, num_predict=predicted_output_tokens, num_ctx=context_tokens, json_mode=True)

    end_time = time()
    logger.info(f"No-batch request completed in  {end_time - start_time:.2f} seconds.")

    try:
        return json.loads(response)
    except json.JSONDecodeError:
        raise ValueError(f"No-batch request returned invalid JSON: \n{response}")
