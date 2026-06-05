from http.client import responses
import asyncio
import httpx
import json
from loguru import logger
import re
import requests
import copy
import math

from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL, ENABLE_THINKING, CONCURRENT_OLLAMA_CALLS

def round_up(n, multiple=256):
    return math.ceil(n / multiple) * multiple

def get_prompt_token_count(payload, tries = 0) -> int:
    if tries > 3:
        raise Exception("Failed to get prompt token count after 3 tries")

    probe = copy.deepcopy(payload)
    probe["stream"] = False

    # Generate as little as possible; use Ollama's real tokenizer/template.
    probe["options"] = {
        **probe.get("options", {}),
        "num_predict": 1,
    }

    r = requests.post(
        f"{OLLAMA_BASE_URL}/api/chat",
        json=probe,
        timeout=180,
    )
    r.raise_for_status()

    prompt_count = r.json()["prompt_eval_count"]

    if prompt_count < 10:
        logger.warning(f"Prompt token count is {prompt_count}; retrying...")
        return get_prompt_token_count(payload, tries + 1)

    return prompt_count

def choose_num_ctx(payload, num_predict: int, margin=128) -> int:
    prompt_tokens = get_prompt_token_count(payload)

    needed = prompt_tokens + num_predict + margin
    return max(round_up(needed, 256), 1024)

def build_payload(prompt: str, system_prompt: str, num_predict=80, num_ctx=1024, json_mode=False, **kwargs: list[str|int]) -> dict:
    return {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "think": ENABLE_THINKING,
        "stream": False,
        "format": "json" if json_mode else None,
        "options": {
            "num_predict": num_predict,
            "temperature": 0,
            "top_p": 0.1,
            "num_ctx": num_ctx,
            **kwargs
        },
    }

async def ask_local_model(prompt:str, system_prompt: str, num_predict=80, num_ctx=1024, json_mode=False, **kwargs: list[str|int]) -> str:
    payload = build_payload(prompt, system_prompt, num_predict=num_predict, num_ctx=num_ctx, json_mode=json_mode, **kwargs)

    num_ctx = choose_num_ctx(
        payload,
        num_predict=num_predict,
    )
    payload["options"]["num_ctx"] = num_ctx

    response = await ollama_chat(payload)

    return clean_response(response)

sem = asyncio.Semaphore(CONCURRENT_OLLAMA_CALLS)

async def ollama_chat(payload) -> str:
    async with sem:

        logger.trace(f"=========== New request ===========")
        logger.trace(f"Payload:\n{json.dumps(payload, indent=2)}")

        async with httpx.AsyncClient() as client:
            req_response = await client.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json=payload,
            timeout=600,
        )

        req_response.raise_for_status()
        data = req_response.json()

        logger.trace(f"Response:\n{json.dumps(data, indent=2)}")

        response = data["message"]["content"]
        return response

def clean_response(text) -> str:
    """
    Clean common Qwen thinking/reasoning output.
    """

    prefix = ""
    if "<think>" in text or "</think>" in text:
       print("Model included thinking in their response.")

    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)

    if "</think>" in text:
        text = text.split("</think>")[-1]


    reasoning_starters = [
        "Hmm,",
        "The user wants",
        "Okay,",
        "Let me think",
        "I need to",
        "First,",
    ]

    cleaned = text.strip()

    for starter in reasoning_starters:
        if cleaned.startswith(starter):
            print("The model responded, but did not follow the exact output format.")

    return cleaned
