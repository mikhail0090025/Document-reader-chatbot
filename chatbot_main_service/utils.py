from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from schemas import Memory, DocumentDecision
from chat_models import chat_model, embeddings
from global_context import memory_storage, chat_history
import re
from prompts.chat_prompt import CHAT_PROMPT
from prompts.memory_prompt import MEMORY_PROMPT
from prompts.document_needs_prompt import DOCUMENT_NEEDS_PROMPT
from prompts.document_prompt import DOCUMENT_PROMPT
from documents import (
    retrieve_documents,
    cosine_similarity,
)

parser = JsonOutputParser(pydantic_object=Memory)

document_needs_parser = JsonOutputParser(pydantic_object=DocumentDecision)

format_instructions = parser.get_format_instructions()

documents_need_prompt = ChatPromptTemplate.from_messages(
    [("system", DOCUMENT_NEEDS_PROMPT), ("human", "{message}")]
)

memory_prompt = ChatPromptTemplate.from_messages(
    [("system", MEMORY_PROMPT), ("human", "{message}")]
)

# =========================
# Chat generation
# =========================

chat_prompt = ChatPromptTemplate.from_messages(
    [("system", CHAT_PROMPT), ("human", "{message}")]
)


def remove_thinking(text: str) -> str:
    """
    Removes Qwen3 reasoning blocks.

    If there is no <think>...</think>, the text is returned unchanged.
    """

    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


# =========================
# 1. Extract facts
# =========================


def extract_memory(message: str):
    formatted_prompt = memory_prompt.invoke(
        {"message": message, "format_instructions": format_instructions}
    )

    response = chat_model.invoke(formatted_prompt)
    cleaned_response = remove_thinking(response.content)

    print("New facts:", cleaned_response)

    try:
        memory = parser.parse(cleaned_response)

        if isinstance(memory, list):
            return memory

        return memory.get("facts", [])

    except Exception as e:
        print(f"Memory parsing failed: {e}")
        return []


# =========================
# 2. Save facts
# =========================


def save_memory(facts, threshold=0.90):

    for fact in facts:
        embedding = embeddings.embed_query(fact)

        duplicate = False

        for item in memory_storage:
            similarity = cosine_similarity(embedding, item["embedding"])

            if similarity >= threshold:
                duplicate = True
                break

        if not duplicate:
            memory_storage.append({"text": fact, "embedding": embedding})


# =========================
# 3. Retrieve memory
# =========================


def retrieve_memory(message, top_k=5):

    query_embedding = embeddings.embed_query(message)

    results = []

    for item in memory_storage:
        similarity = cosine_similarity(query_embedding, item["embedding"])

        results.append({"text": item["text"], "score": similarity})

    results.sort(key=lambda x: x["score"], reverse=True)

    return [item["text"] for item in results[:top_k]]


# =========================
# 4. Generate answer
# =========================


def generate_answer(message):

    memories = retrieve_memory(message)

    memory_text = "\n".join(f"- {m}" for m in memories)

    formatted_prompt = chat_prompt.invoke({"message": message, "memory": memory_text})

    response = chat_model.invoke(formatted_prompt)

    return response.content


def show_all_memory():
    if not memory_storage:
        print("Memory is empty.")
        return

    print("Stored memories:\n")

    for i, item in enumerate(memory_storage, start=1):
        print(f"{i}. {item['text']}")


def show_all_messages():
    if not chat_history:
        print("Chat is empty.")
        return

    print("Stored messages:\n")

    for i, item in enumerate(chat_history, start=1):
        print(f"{i}. {item['content']}")


def need_documents(message: str):

    formatted_prompt = documents_need_prompt.invoke({"message": message})

    response = chat_model.invoke(formatted_prompt)

    response_clear = remove_thinking(response.content)

    print("Document decision raw:", response_clear)

    decision = document_needs_parser.parse(response_clear)

    if isinstance(decision, dict):
        return decision.get("use_documents", False)

    return False


document_prompt = ChatPromptTemplate.from_messages(
    [("system", DOCUMENT_PROMPT), ("human", "{message}")]
)


def generate_document_answer(message):

    chunks = retrieve_documents(message)

    context = "\n\n".join(chunk["text"] for chunk in chunks)

    formatted_prompt = document_prompt.invoke({"context": context, "message": message})

    response = chat_model.invoke(formatted_prompt)

    return response.content


def get_chat_context(history_size=4):

    if not chat_history:
        return "No previous messages."

    messages = chat_history[-history_size:]

    context = ""

    for msg in messages:
        role = msg["role"]
        content = msg["content"]

        context += f"{role}: {content}\n"

    return context


def chat(message: str, use_documents_anyway=False, history_size=4):

    # 1. Проверяем, нужны ли документы
    use_documents = need_documents(message)

    print("Use documents:", use_documents)

    # 2. Извлекаем новые факты
    new_facts = extract_memory(message)

    # 3. Сохраняем память
    if new_facts:
        save_memory(new_facts)

    # 4. Получаем релевантную память
    memories = retrieve_memory(message)

    print("Memories:", memories)

    # 5. Формируем контекст памяти
    if memories:
        memory_context = "\n".join(f"- {fact}" for fact in memories)
    else:
        memory_context = "No relevant information."

    # -----------------------------
    # Генерация ответа
    # -----------------------------

    if use_documents_anyway:
        use_documents = True

    if use_documents:
        print("Using document search")

        answer = remove_thinking(generate_document_answer(message))

    else:
        history_context = get_chat_context(history_size)

        formatted_prompt = chat_prompt.invoke(
            {"message": message, "memory": memory_context, "history": history_context}
        )

        response = chat_model.invoke(formatted_prompt)

        answer = remove_thinking(response.content)

    # -----------------------------
    # Сохраняем историю
    # -----------------------------

    chat_history.append({"role": "user", "content": message})

    chat_history.append({"role": "assistant", "content": answer})

    return answer
