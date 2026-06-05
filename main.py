import asyncio
from logger import logger
import sys
import os
import json
from time import time
from pathlib import Path
from processors.communication_summary_processor import summarize_messages_no_batch, summarize_messages
from app.config import AGENT_NAME, OLLAMA_MODEL, ENABLE_THINKING, MODEL_PROVIDER, GEMINI_MODEL
from datetime import datetime

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")

INPUT_PATHS = [
    Path("data/inbox/work_email_messages.json"),
    Path("data/inbox/personal_email_messages.json")
]

OUTPUT_PATH = Path(f"data/outputs/communication_summary_email_{timestamp}.md")
RAW_OUTPUT_PATH = Path(f"data/outputs/communication_summary_email_{timestamp}.json")

def load_messages():
    with open(INPUT_PATHS[0], "r") as f:
        return json.load(f)

@logger.catch
async def main():
    start_time = time()

    logger.info(f"{AGENT_NAME} is starting...")
    logger.info(f"Model provider: {MODEL_PROVIDER}")

    if (MODEL_PROVIDER == "gemini"):
        logger.info(f"Using Gemini model: {GEMINI_MODEL}\n")
    else:
        logger.info(f"Using local model: {OLLAMA_MODEL}")
        logger.info(f"Thinking enabled: {ENABLE_THINKING}\n")

    # logger.info("Refreshing message sources...\n")
    # refresh_gmail_messages()

    logger.info("Loading messages from inbox...")
    messages = load_messages()
    logger.info(f"Loaded {len(messages)} total messages.\n")

    logger.info("Creating communication summary...")
    summary_start_time = time()
    summary = await summarize_messages(messages)
    summary_end_time = time()

    logger.success(f"Summary created in {summary_end_time - summary_start_time:.2f} seconds.\n")

    summary_text = json.dumps(summary, indent=4)

    logger.info("Writing raw structured output...\n")
    with open(RAW_OUTPUT_PATH, "w") as f:
        f.write(summary_text)
    # write_markdown_output(summary_text, RAW_OUTPUT_PATH)

    # logger.info("Formatting summary as email...\n")
    # email_text = format_summary_as_email(summary)

    # logger.info("Writing email briefing output...\n")
    # write_markdown_output(email_text, OUTPUT_PATH)

    # logger.info("Preparing downstream action files...\n")
    # write_action_exports(summary)

    end_time = time()
    total_time = end_time - start_time
    logger.warning(f"Total execution time: {total_time:.2f} seconds.")


if __name__ == "__main__":
    asyncio.run(main())
