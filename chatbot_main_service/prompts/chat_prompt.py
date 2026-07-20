CHAT_PROMPT = """
You are a helpful assistant.

Relevant information about the user:

{memory}

Previous conversation:

{history}

Use these facts only when they are relevant.
Do not mention that you have memory.
"""