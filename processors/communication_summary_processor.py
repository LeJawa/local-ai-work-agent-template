import json
from app.config import BATCH_SIZE

def empty_summary():
    pass

def batch_messages(messages: list[dict[str, str]], batch_size=BATCH_SIZE):
    pass

def merge_summaries(summary_results):
    pass

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
    with open("app/prompts/communication_triage_prompt.md", "r", encoding="utf-8") as file:
        summary_prompt = file.read()
    with open("app/prompts/communication_triage_format.json", "r", encoding="utf-8") as file:
        raw_json_format = file.read()

    formatted_messages = format_messages_for_prompt(messages)
    json_format = json.dumps(json.loads(raw_json_format), indent=2)

    summary_prompt = summary_prompt.replace("{{MESSAGES}}", formatted_messages)
    summary_prompt = summary_prompt.replace("{{JSON_FORMAT}}", json_format)

    return summary_prompt

def classify_message_batch(batch, batch_number: int):
    pass

def summarize_messages(messages):
    pass
