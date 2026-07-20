import gc
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from langchain_huggingface import HuggingFaceEmbeddings

model_name = "Qwen/Qwen2.5-3B-Instruct"

CACHE_DIR = "./models"

tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=CACHE_DIR)

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    cache_dir=CACHE_DIR,
    device_map="auto",
    low_cpu_mem_usage=True,
    offload_state_dict=True,
    offload_folder="./offload",
)

# model_name="BAAI/bge-base-en-v1.5"
model_name = "BAAI/bge-m3"

embeddings = HuggingFaceEmbeddings(
    model_name=model_name,
    cache_folder=CACHE_DIR,
)

gc.collect()
