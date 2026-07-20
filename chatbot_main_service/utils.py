from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
import numpy as np
from schemas import Memory, DocumentDecision
from chat_models import chat_model, embeddings
from global_context import memory_storage, document_storage, chat_history, web_links

import os
import re

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)

from tqdm.auto import tqdm
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    WebBaseLoader
)

from prompts.chat_prompt import CHAT_PROMPT
from prompts.memory_prompt import MEMORY_PROMPT
from prompts.document_needs_prompt import DOCUMENT_NEEDS_PROMPT
from prompts.document_prompt import DOCUMENT_PROMPT

parser = JsonOutputParser(pydantic_object=Memory)

document_needs_parser = JsonOutputParser(pydantic_object=DocumentDecision)

format_instructions = parser.get_format_instructions()

documents_need_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            DOCUMENT_NEEDS_PROMPT
        ),
        ("human", "{message}")
    ]
)

memory_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            MEMORY_PROMPT
        ),
        ("human", "{message}")
    ]
)

# =========================
# Chat generation
# =========================

chat_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            CHAT_PROMPT
        ),
        ("human", "{message}")
    ]
)

def remove_thinking(text: str) -> str:
    """
    Removes Qwen3 reasoning blocks.

    If there is no <think>...</think>, the text is returned unchanged.
    """

    return re.sub(
        r"<think>.*?</think>",
        "",
        text,
        flags=re.DOTALL
    ).strip()

# =========================
# Storage
# =========================

def cosine_similarity(a, b):
    return np.dot(a, b) / (
        np.linalg.norm(a) * np.linalg.norm(b)
    )

# =========================
# 1. Extract facts
# =========================

def extract_memory(message: str):
    formatted_prompt = memory_prompt.invoke({
        "message": message,
        "format_instructions": format_instructions
    })

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

            similarity = cosine_similarity(
                embedding,
                item["embedding"]
            )

            if similarity >= threshold:
                duplicate = True
                break


        if not duplicate:
            memory_storage.append(
                {
                    "text": fact,
                    "embedding": embedding
                }
            )

# =========================
# 3. Retrieve memory
# =========================

def retrieve_memory(message, top_k=5):

    query_embedding = embeddings.embed_query(message)

    results = []

    for item in memory_storage:

        similarity = cosine_similarity(
            query_embedding,
            item["embedding"]
        )

        results.append(
            {
                "text": item["text"],
                "score": similarity
            }
        )


    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )


    return [
        item["text"]
        for item in results[:top_k]
    ]


# =========================
# 4. Generate answer
# =========================

def generate_answer(message):

    memories = retrieve_memory(message)

    memory_text = "\n".join(
        f"- {m}" for m in memories
    )

    formatted_prompt = chat_prompt.invoke(
        {
            "message": message,
            "memory": memory_text
        }
    )

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

    formatted_prompt = documents_need_prompt.invoke(
        {
            "message": message
        }
    )

    response = chat_model.invoke(formatted_prompt)

    response_clear = remove_thinking(response.content)

    print("Document decision raw:", response_clear)

    decision = document_needs_parser.parse(response_clear)

    if isinstance(decision, dict):
        return decision.get("use_documents", False)

    return False

def load_documents(folder):

    documents = []

    for filename in os.listdir(folder):

        path = os.path.join(folder, filename)

        if filename.endswith(".txt"):

            loader = TextLoader(path)

            documents.extend(loader.load())

        elif filename.endswith(".pdf"):

            loader = PyPDFLoader(path)

            documents.extend(loader.load())

    return documents

def load_web_documents(urls):

    documents = []

    for url in urls:

        loader = WebBaseLoader(url)

        documents.extend(loader.load())

    return documents

def split_documents(documents):

    splitter = RecursiveCharacterTextSplitter(

        chunk_size=800,
        chunk_overlap=150

    )

    return splitter.split_documents(documents)

def build_document_index(folder):

    global document_storage

    document_storage.clear()

    print(f"Scanning folder: {folder}\n")

    supported_formats = {
        ".txt",
        ".pdf"
    }

    all_chunks = []

    # ---------- Loading web pages ----------

    if web_links:
    
        print("\nLoading web pages...\n")
    
        web_documents = load_web_documents(web_links)
    
        print(f"Web pages loaded: {len(web_documents)}")
    
        web_chunks = split_documents(web_documents)
    
        print(f"Web chunks created: {len(web_chunks)}")
    
        all_chunks.extend(web_chunks)

    document_count = 0

    for filename in os.listdir(folder):

        path = os.path.join(folder, filename)

        if not os.path.isfile(path):
            continue


        extension = os.path.splitext(filename)[1].lower()


        if extension not in supported_formats:
            continue


        document_count += 1

        print(f"[FOUND] {filename}")


        # ---------- Loading ----------

        if extension == ".txt":

            loader = TextLoader(
                path,
                encoding="utf-8"
            )

        elif extension == ".pdf":

            loader = PyPDFLoader(path)


        documents = loader.load()


        print(
            f"        Pages/parts loaded: {len(documents)}"
        )


        # ---------- Splitting ----------

        chunks = split_documents(documents)


        print(
            f"        Chunks created: {len(chunks)}"
        )


        all_chunks.extend(chunks)



    print("\n----------------------")
    print(f"Documents found: {document_count}")
    print(f"Total chunks: {len(all_chunks)}")
    print("----------------------\n")


    if not all_chunks:
        print("No supported documents found.")
        return


    # ---------- Embeddings ----------

    print("Generating embeddings...\n")


    for chunk in tqdm(
        all_chunks,
        desc="Embedding chunks"
    ):

        text = chunk.page_content


        embedding = embeddings.embed_query(text)


        document_storage.append(
            {
                "text": text,

                "embedding": embedding,

                "source": chunk.metadata.get(
                    "source",
                    "unknown"
                ),

                "page": chunk.metadata.get(
                    "page",
                    None
                )
            }
        )


    print("\nIndexing complete.")
    print("----------------------")
    print(
        f"Stored embeddings: {len(document_storage)}"
    )

def retrieve_documents(question, top_k=5):

    query_embedding = embeddings.embed_query(question)

    results = []

    for item in document_storage:

        similarity = cosine_similarity(
            query_embedding,
            item["embedding"]
        )

        results.append(
            {
                "text": item["text"],
                "source": item["source"],
                "page": item["page"],
                "score": similarity
            }
        )

    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return results[:top_k]

document_prompt = ChatPromptTemplate.from_messages(
[
(
"system",
DOCUMENT_PROMPT
),
("human","{message}")
]
)

def generate_document_answer(message):

    chunks = retrieve_documents(message)

    context = "\n\n".join(

        chunk["text"]

        for chunk in chunks

    )

    formatted_prompt = document_prompt.invoke(

        {
            "context": context,
            "message": message
        }

    )

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
        memory_context = "\n".join(
            f"- {fact}" for fact in memories
        )
    else:
        memory_context = "No relevant information."

    # -----------------------------
    # Генерация ответа
    # -----------------------------

    if use_documents_anyway:
        use_documents = True

    if use_documents:

        print("Using document search")

        answer = remove_thinking(
            generate_document_answer(message)
        )

    else:

        history_context = get_chat_context(history_size)

        formatted_prompt = chat_prompt.invoke(
            {
                "message": message,
                "memory": memory_context,
                "history": history_context
            }
        )

        response = chat_model.invoke(formatted_prompt)

        answer = remove_thinking(response.content)

    # -----------------------------
    # Сохраняем историю
    # -----------------------------

    chat_history.append(
        {
            "role": "user",
            "content": message
        }
    )

    chat_history.append(
        {
            "role": "assistant",
            "content": answer
        }
    )

    return answer