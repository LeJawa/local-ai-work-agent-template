import json
from time import time
from pathlib import Path
from app.agent import ask_ollama, process_messages_no_batch
from app.config import AGENT_NAME, OLLAMA_MODEL, ENABLE_THINKING, MODEL_PROVIDER, GEMINI_MODEL

INPUT_PATHS = [
    Path("data/inbox/work_email_messages.json"),
    Path("data/inbox/personal_email_messages.json")
]

OUTPUT_PATH = Path("data/outputs/communication_summary_email.md")
RAW_OUTPUT_PATH = Path("data/outputs/communication_summary_email.json")

def load_messages():
    with open(INPUT_PATHS[0], "r") as f:
        return json.load(f)

def main():
    start_time = time()

    print(f"{AGENT_NAME} is starting...")
    print(f"Model provider: {MODEL_PROVIDER}")

    if (MODEL_PROVIDER == "gemini"):
        print(f"Using Gemini model: {GEMINI_MODEL}")
    else:
        print(f"Using local model: {OLLAMA_MODEL}")
        print(f"Thinking enabled: {ENABLE_THINKING}")

    # print("\nRefreshing message sources...")
    # refresh_gmail_messages()

    print("\nLoading messages from inbox...")
    messages = load_messages()[:3]
    print(f"Loaded {len(messages)} total messages.")

    print("\nCreating communication summary...")
    summary_start_time = time()
    summary = process_messages_no_batch(messages)
    summary_end_time = time()

    print(f"Summary created in {summary_end_time - summary_start_time:.2f} seconds.")

    summary_text = json.dumps(summary, indent=4)

    print("\nWriting raw structured output...")
    with open(RAW_OUTPUT_PATH, "w") as f:
        f.write(summary_text)
    # write_markdown_output(summary_text, RAW_OUTPUT_PATH)

    # print("\nFormatting summary as email...")
    # email_text = format_summary_as_email(summary)

    # print("\n Writing email briefing output...")
    # write_markdown_output(email_text, OUTPUT_PATH)

    # print("\nPreparing downstream action files...")
    # write_action_exports(summary)

    end_time = time()
    total_time = end_time - start_time
    print(f"\nTotal execution time: {total_time:.2f} seconds.")



if __name__ == "__main__":
    main()
