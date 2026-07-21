from langchain_community.document_loaders import TextLoader, PyPDFLoader, WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from chat_models import embeddings
import os
from tqdm.auto import tqdm
import numpy as np
from global_context import document_storage, CHUNK_SIZE, CHUNK_OVERLAP, web_links

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


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

    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)

    return splitter.split_documents(documents)


def add_document(path):

    filename = os.path.basename(path)

    extension = os.path.splitext(filename)[1].lower()

    if extension == ".txt":
        loader = TextLoader(path, encoding="utf-8")

    elif extension == ".pdf":
        loader = PyPDFLoader(path)

    else:
        return

    documents = loader.load()

    chunks = split_documents(documents)

    print(f"[ADD] {filename}: {len(chunks)} chunks")

    for chunk in tqdm(chunks, desc=f"Embedding {filename}"):
        embedding = embeddings.embed_query(chunk.page_content)

        document_storage.append(
            {
                "document_id": filename,
                "text": chunk.page_content,
                "embedding": embedding,
                "source": chunk.metadata.get("source", filename),
                "page": chunk.metadata.get("page"),
            }
        )

    return len(chunks)


def remove_document(document_id):

    global document_storage

    before = len(document_storage)

    document_storage[:] = [
        chunk for chunk in document_storage if chunk["document_id"] != document_id
    ]

    removed = before - len(document_storage)

    print(f"Removed {removed} chunks from '{document_id}'")

    return removed


def build_document_index(folder):

    global document_storage

    document_storage.clear()

    print(f"Scanning folder: {folder}")

    supported_formats = {".txt", ".pdf"}

    for filename in os.listdir(folder):
        path = os.path.join(folder, filename)

        if not os.path.isfile(path):
            continue

        extension = os.path.splitext(filename)[1].lower()

        if extension not in supported_formats:
            continue

        add_document(path)

    print(f"\nStored embeddings: {len(document_storage)}")


def retrieve_documents(question, top_k=5):

    query_embedding = embeddings.embed_query(question)

    results = []

    for item in document_storage:
        similarity = cosine_similarity(query_embedding, item["embedding"])

        results.append(
            {
                "text": item["text"],
                "source": item["source"],
                "page": item["page"],
                "score": similarity,
            }
        )

    results.sort(key=lambda x: x["score"], reverse=True)

    return results[:top_k]

def add_web_document(url):

    web_links.append(url)

    loader = WebBaseLoader(url)

    documents = loader.load()

    chunks = split_documents(documents)

    print(f"[WEB ADD] {url}: {len(chunks)} chunks")

    for chunk in tqdm(chunks, desc=f"Embedding {url}"):

        embedding = embeddings.embed_query(
            chunk.page_content
        )

        document_storage.append(
            {
                "document_id": url,
                "text": chunk.page_content,
                "embedding": embedding,
                "source": url,
                "page": None,
                "type": "web",
            }
        )

    return len(chunks)



def remove_web_document(url):

    web_links.remove(url)

    global document_storage

    before = len(document_storage)

    document_storage[:] = [
        chunk
        for chunk in document_storage
        if chunk["document_id"] != url
    ]

    removed = before - len(document_storage)

    print(
        f"[WEB REMOVE] {url}: {removed} chunks"
    )

    return removed