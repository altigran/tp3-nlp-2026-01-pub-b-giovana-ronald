"""Indexador (stub) — passo 1.10.

Indexa o material aprovado em uma **vector store**, anexando a CADA chunk os
metadados obrigatórios do contrato (Seção 3.1):

    chunk_id, text, source_url, evaluator_score, collected_at, topics,
    raw_content_hash, discipline, corpus_hash

O índice da vector store **não é versionado** (Seção 6.4: regenerável); apenas
os metadados por chunk e o hash entram no repositório.

TODO(aluno): escolher a vector store (ex.: FAISS, Chroma) e o modelo de embedding;
documentar tamanho de chunk e k de recuperação no relatório.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

import numpy as np
from openai import OpenAI

# Vector store escolhida: JSON + numpy (cosine similarity em memória).
# Modelo de embedding: nvidia/nv-embed-qa-4 via API NVIDIA (openai-compat).
# Tamanho de chunk: 200 palavras com sobreposição de 40 palavras.
# k de recuperação padrão: 5.

CHUNK_SIZE = 200       # palavras por chunk
CHUNK_OVERLAP = 40     # palavras de sobreposição entre chunks
EMBED_MODEL = "nvidia/nv-embed-qa-4"
EMBED_DIM = 1024
CORPUS_CHUNKS_PATH = Path("data/corpus_chunks.json")


@dataclass
class Chunk:
    chunk_id: str
    text: str
    source_url: str
    evaluator_score: float
    collected_at: str
    topics: list[str]
    raw_content_hash: str
    discipline: str
    corpus_hash: str = ""   # preenchido no congelamento (freeze)
    embedding: list[float] | None = None  # vetor de embedding


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Divide texto em chunks de 'size' palavras com sobreposição."""
    words = text.split()
    if not words:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = min(start + size, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start += size - overlap
    return chunks


def _get_embeddings(texts: list[str], client: OpenAI) -> list[list[float]]:
    """Calcula embeddings em lotes de até 32 textos."""
    BATCH = 32
    all_vecs: list[list[float]] = []
    for i in range(0, len(texts), BATCH):
        batch = texts[i : i + BATCH]
        try:
            resp = client.embeddings.create(
                model=EMBED_MODEL,
                input=batch,
                encoding_format="float",
            )
            all_vecs.extend([item.embedding for item in resp.data])
        except Exception as exc:
            print(f"aviso: erro ao calcular embedding para batch {i//BATCH}: {exc}")
            # preenche com zeros para não quebrar o pipeline
            all_vecs.extend([[0.0] * EMBED_DIM for _ in batch])
        time.sleep(0.2)  # respeita rate limit da API
    return all_vecs


def build_index(evaluated_docs: list, discipline: str = "") -> list[Chunk]:
    """Fragmenta em chunks, calcula embeddings e popula a vector store."""
    # chunking + embeddings + upsert na vector store + metadados.
    api_key = os.environ.get("API_KEY")
    if not api_key:
        raise EnvironmentError("Variavel de ambiente API_KEY nao definida.")

    client = OpenAI(
        api_key=api_key,
        base_url="https://integrate.api.nvidia.com/v1",
    )

    chunks: list[Chunk] = []
    textos_para_embed: list[str] = []

    for doc in evaluated_docs:
        # compatível com dataclass e dict
        if hasattr(doc, "raw_path"):
            raw_path = doc.raw_path
            source_url = doc.source_url
            topic_ids = doc.topic_ids
            collected_at = doc.fetched_at
            evaluator_score = doc.evaluator_score
            raw_content_hash = doc.raw_content_hash
        else:
            raw_path = doc.get("raw_path", "")
            source_url = doc.get("source_url", "")
            topic_ids = doc.get("topic_ids", [])
            collected_at = doc.get("fetched_at", "")
            evaluator_score = doc.get("evaluator_score", 0.0)
            raw_content_hash = doc.get("raw_content_hash", "")

        try:
            text_full = Path(raw_path).read_text(encoding="utf-8", errors="ignore")
        except Exception as exc:
            print(f"aviso: nao foi possivel ler {raw_path}: {exc}")
            continue

        partes = _chunk_text(text_full)
        for idx, parte in enumerate(partes):
            chunk_id = f"{topic_ids[0] if topic_ids else 'unknown'}_{_sha256(raw_content_hash)[:8]}_{idx}"
            c = Chunk(
                chunk_id=chunk_id,
                text=parte,
                source_url=source_url,
                evaluator_score=evaluator_score,
                collected_at=collected_at,
                topics=list(topic_ids),
                raw_content_hash=raw_content_hash,
                discipline=discipline,
                corpus_hash="",
            )
            chunks.append(c)
            textos_para_embed.append(parte)

    print(f"indexador: {len(chunks)} chunks gerados, calculando embeddings...")
    embeddings = _get_embeddings(textos_para_embed, client)
    for chunk, emb in zip(chunks, embeddings):
        chunk.embedding = emb

    return chunks


def save_chunks(chunks: list[Chunk]) -> None:
    """Persiste os chunks (com embeddings) em data/corpus_chunks.json."""
    payload = [asdict(c) for c in chunks]
    CORPUS_CHUNKS_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"indexador: {len(chunks)} chunks salvos em {CORPUS_CHUNKS_PATH}")
