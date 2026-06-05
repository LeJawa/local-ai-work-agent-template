import json
from loguru import logger
import re
import requests
import copy
import math

from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL, ENABLE_THINKING

def round_up(n, multiple=256):
    return math.ceil(n / multiple) * multiple

def get_prompt_token_count(payload) -> int:
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

    data = r.json()
    return data["prompt_eval_count"]

def choose_num_ctx(payload, num_predict: int, margin=128) -> int:
    prompt_tokens = get_prompt_token_count(payload)

    needed = prompt_tokens + num_predict + margin
    return round_up(needed, 256)

def ask_local_model(prompt:str, system_prompt: str, num_predict=80, num_ctx=1024, json_mode=False, **kwargs: list[str|int]) -> str:
    payload = {
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

    num_ctx = choose_num_ctx(
        payload,
        num_predict=num_predict,
    )

    payload["options"]["num_ctx"] = num_ctx

    logger.debug(f"=========== New request ===========")
    logger.debug(f"Payload:\n{json.dumps(payload, indent=2)}")

    req_response = requests.post(
        f"{OLLAMA_BASE_URL}/api/chat",
        json=payload,
        timeout=600,
    )

    req_response.raise_for_status()
    data = req_response.json()

    logger.debug(f"Response:\n{json.dumps(data, indent=2)}")

    response = data["message"]["content"]

    return clean_response(response)

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
