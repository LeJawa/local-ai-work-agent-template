import json
from enum import STRICT
from time import time
from processors.communication_summary_processor import empty_summary, build_summary_prompt
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


def load_system_prompt():
    with open("app/prompts/system_prompt.md", "r", encoding="utf-8") as file:
        return file.read()


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


def ask_ollama(user_prompt) -> str:
    system_prompt = load_system_prompt()

    if not ENABLE_THINKING:
        user_prompt = f"/no_think {user_prompt}"

    response = ask_local_model(user_prompt, system_prompt, num_predict=80, num_ctx=1024)
    return response

def process_messages_no_batch(messages: list[dict[str,str]]) -> dict[str, list[dict[str,str]]]:
    if not messages:
        return empty_summary()

    start_time = time()

    print(f"Processing all {len(messages)} messages in one request")

    prompt = build_summary_prompt(messages)

    response = ask_local_model(prompt, system_prompt=STRICT_JSON_SYSTEM_PROMPT, num_predict=1500, num_ctx=4096, json_mode=True)

    end_time = time()
    print(f"No-batch request completed in  {end_time - start_time:.2f} seconds.")

    try:
        return json.loads(response)
    except json.JSONDecodeError:
        raise ValueError(f"No-batch request returned invalid JSON: \n{response}")



def ask_local_model(prompt:str, system_prompt: str, num_predict=80, num_ctx=1024, json_mode=False, **kwargs: list[str|int]) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "think": ENABLE_THINKING,
        "stream": False,
        "options": {
            "num_predict": num_predict,
            "temperature": 0,
            "top_p": 0.1,
            "num_ctx": num_ctx,
            "json_mode": json_mode,
            **kwargs
        },
    }

    req_response = requests.post(
        f"{OLLAMA_BASE_URL}/api/chat",
        json=payload,
        timeout=600,
    )

    req_response.raise_for_status()

    response = req_response.json()["message"]["content"]

    return clean_response(response)
