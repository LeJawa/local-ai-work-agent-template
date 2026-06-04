import json
from app.agent import ask_ollama, ask_local_model, process_messages_no_batch

def test_process_messages_no_batch():
    with open("data/inbox/work_email_messages.json", "r", encoding="utf-8") as file:
        messages = json.load(file)

    response = process_messages_no_batch(messages[:3])

    assert isinstance(response, dict)

    print(json.dumps(response, indent=4))
