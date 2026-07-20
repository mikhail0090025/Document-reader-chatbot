from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
from langchain_huggingface import (
    HuggingFacePipeline,
    HuggingFaceEmbeddings,
    ChatHuggingFace,
)
import gc

model_name = "Qwen/Qwen2.5-3B-Instruct"

CACHE_DIR = "./models"

tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=CACHE_DIR)

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    cache_dir=CACHE_DIR,
    low_cpu_mem_usage=True,
)

# model_name="BAAI/bge-base-en-v1.5"
model_name = "BAAI/bge-m3"

embeddings = HuggingFaceEmbeddings(
    model_name=model_name,
    cache_folder=CACHE_DIR,
)

gc.collect()

pipe = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    max_new_tokens=400,
    do_sample=False,
    temperature=0.4,
    top_p=0.95,
    top_k=50,
    return_full_text=False,
)

llm = HuggingFacePipeline(pipeline=pipe)

chat_model = ChatHuggingFace(llm=llm)
