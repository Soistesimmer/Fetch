import os
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel
from sklearn.cluster import AgglomerativeClustering

model_fpath = "path/to/merge/data"
tokenizer = AutoTokenizer.from_pretrained(model_fpath)
model = AutoModel.from_pretrained(model_fpath).cuda()
max_seq_length = 256

def compute_emb(texts):
    inputs = tokenizer(texts, padding=True, truncation=True, return_tensors="pt", max_length=max_seq_length)
    inputs = {k: v.to(model.device) for k, v in inputs.items()}
    # Get the embeddings
    with torch.no_grad():
        embeddings = model(**inputs, output_hidden_states=True, return_dict=True).pooler_output
        embeddings = F.normalize(embeddings, p=2, dim=-1)
    return embeddings.cpu().numpy()

def cluster(texts, d=0.1):
    if len(texts) < 2:
        return [0]
    embs = compute_emb(texts)
    clustering = AgglomerativeClustering(n_clusters=None, metric="cosine", linkage="average", distance_threshold=d).fit(embs)
    return clustering.labels_.tolist()

app = FastAPI()

class InputText(BaseModel):
    texts: List[str]
    d: float

class OutputPrediction(BaseModel):
    labels: List

@app.post("/predict", response_model=OutputPrediction)
async def predict(input_text: InputText):
    labels = cluster(input_text.texts, input_text.d)
    return {"labels": labels}