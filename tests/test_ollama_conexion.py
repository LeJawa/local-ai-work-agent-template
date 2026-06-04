from app.agent import ask_ollama, ask_local_model

def test_ollama_conexion():
    EXPECTED_TEST_RESPONSE = "Test is successful!"
    user_prompt = f"/nothink Return only this exact text: {EXPECTED_TEST_RESPONSE}"
    system_prompt = """You are a local AI work assistant.

This is a connection test.

You must return only the exact text requested by the user.

Do not explain.
Do not reason.
Do not include thinking.
Do not include markdown.
Do not include extra words."""
    response = ask_local_model(user_prompt, system_prompt, num_predict=80, num_ctx=1024)

    assert response == EXPECTED_TEST_RESPONSE
