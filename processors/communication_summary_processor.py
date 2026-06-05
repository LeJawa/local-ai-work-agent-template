import asyncio
from collections.abc import Iterator
from loguru import logger
import json
from enum import STRICT
from time import time
from utils.llm import ask_local_model

import re
import requests

from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL, ENABLE_THINKING, BATCH_SIZE

_strict_json_system_prompt = None
_summary_prompt = None
_json_format = None

def load_strict_json_system_prompt() -> str:
    global _strict_json_system_prompt
    if _strict_json_system_prompt is None:
        with open("processors/prompts/strict_json_system_prompt.md", "r", encoding="utf-8") as file:
            _strict_json_system_prompt = file.read()
    return _strict_json_system_prompt

def load_summary_prompt() -> str:
    global _summary_prompt
    if _summary_prompt is None:
        with open("processors/prompts/communication_triage_prompt.md", "r", encoding="utf-8") as file:
            _summary_prompt = file.read()
    return _summary_prompt

def load_json_format() -> dict[str, list[dict[str,str]]]:
    global _json_format
    if _json_format is None:
        with open("processors/prompts/communication_triage_format.json", "r", encoding="utf-8") as file:
            raw_json_format = file.read()
            _json_format = json.loads(raw_json_format)
    return _json_format


def empty_summary() -> dict[str, list[dict[str,str]]]:
    summary = {}

    for key in load_json_format().keys():
        summary[key] = []
    return summary


OUTPUT_TOKENS_PER_MESSAGE = 100

async def summarize_messages_no_batch(messages: list[dict[str,str]]) -> dict[str, list[dict[str,str]]]:
    if not messages:
        return empty_summary()

    start_time = time()

    logger.info(f"Processing all {len(messages)} messages in one request")

    prompt = build_summary_prompt(messages)
    system_prompt = load_strict_json_system_prompt()

    predicted_output_tokens = OUTPUT_TOKENS_PER_MESSAGE * len(messages)
    context_tokens = 4096

    response = await ask_local_model(prompt, system_prompt=system_prompt, num_predict=predicted_output_tokens, num_ctx=context_tokens, json_mode=True)

    end_time = time()
    logger.info(f"No-batch request completed in  {end_time - start_time:.2f} seconds.")

    try:
        return json.loads(response)
    except json.JSONDecodeError:
        raise ValueError(f"No-batch request returned invalid JSON: \n{response}")


def batch_iterator(messages: list[dict[str,str]], batch_size: int = BATCH_SIZE) -> Iterator[list[dict[str,str]]]:
    batch = []

    for message in messages:
        batch.append(message)

        if len(batch) == batch_size:
            yield batch
            batch = []

    if batch:
        yield batch

async def summarize_messages(messages: list[dict[str,str]]) -> dict[str, list[dict[str,str]]]:
    if not messages:
        return empty_summary()

    tasks = []

    async with asyncio.TaskGroup() as tg:
        for batch_number, batch in enumerate(batch_iterator(messages), start=1):
            tasks.append(tg.create_task(classify_message_batch(batch, batch_number)))

    batch_results = [task.result() for task in tasks]

    return merge_summaries(batch_results)

def merge_summaries(batch_results: list[dict[str, list[dict[str,str]]]]) -> dict[str, list[dict[str,str]]]:
    merged = {}
    for result in batch_results:
        for key, value in result.items():
            merged.setdefault(key, []).extend(value)
    return merged


async def classify_message_batch(batch: list[dict[str,str]], batch_number: int) -> dict[str, list[dict[str,str]]]:
    start_time = time()

    logger.info(f"Processing batch {batch_number} of with {len(batch)} message{"s" if len(batch) > 1 else ""}...")

    prompt = build_summary_prompt(batch)
    system_prompt = load_strict_json_system_prompt()

    predicted_output_tokens = OUTPUT_TOKENS_PER_MESSAGE * len(batch)
    context_tokens = 4096

    response = await ask_local_model(prompt, system_prompt=system_prompt, num_predict=predicted_output_tokens, num_ctx=context_tokens, json_mode=True)

    end_time = time()
    logger.success(f"Batch {batch_number} completed in  {end_time - start_time:.2f} seconds.")

    try:
        return json.loads(response)
    except json.JSONDecodeError:
        raise ValueError(f"Batch {batch_number} returned invalid JSON:\n{response}")


def format_messages_for_prompt(messages: list[dict[str, str]]) -> str:
    prompt_messages:list[str] = []
    for index, message in enumerate(messages):
        prompt_messages.append(f"""
Message {index}
Source: {message.get("source", "Unknown")}
From: {message.get("from", "Unknown")}
Date: {message.get("date", "Unknown")}
Subject: {message.get("subject", "No subject")}
Snippet: {message.get("snippet", "")}
Body: {message.get("body", "")}
""")

    return "\n".join(prompt_messages)

def build_summary_prompt(messages: list[dict[str, str]]) -> str:

    formatted_messages = format_messages_for_prompt(messages)
    summary_prompt = load_summary_prompt()
    json_format = json.dumps(load_json_format(), indent=2)

    summary_prompt = summary_prompt.replace("{{MESSAGES}}", formatted_messages)
    summary_prompt = summary_prompt.replace("{{JSON_FORMAT}}", json_format)

    return summary_prompt
