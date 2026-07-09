"""Indexador — passo 1.10.

Indexa o material aprovado em uma **vector store**, anexando a CADA chunk os
metadados obrigatórios do contrato (Seção 3.1):

    chunk_id, text, source_url, evaluator_score, collected_at, topics,
    raw_content_hash, discipline, corpus_hash

O índice da vector store **não é versionado** (Seção 6.4: regenerável); apenas
os metadados por chunk e o hash entram no repositório.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer

# Vector store: JSON + cosine similarity sobre embeddings.
# Modelo de embedding: sentence-transformers multi-língua (384 dims).
# Tamanho de chunk: 200 palavras com sobreposição de 40 palavras.
# k de recuperação padrão: 5.

CHUNK_SIZE = 200       # palavras por chunk
CHUNK_OVERLAP = 40     # palavras de sobreposição entre chunks
EMBED_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMBED_DIM = 384
INDICES_PATH = Path("data/index/embeddings.npy")


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
    embedding: list[float] | None = None  # vetor de embedding (384 dims)


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


def build_index(evaluated_docs: list, discipline: str = "") -> list[Chunk]:
    """Fragmenta em chunks, calcula embeddings e popula a vector store."""
    print(f"indexador: carregando modelo {EMBED_MODEL_NAME}...")
    model = SentenceTransformer(EMBED_MODEL_NAME)

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
    embeddings = model.encode(textos_para_embed, show_progress_bar=True).tolist()
    for chunk, emb in zip(chunks, embeddings):
        chunk.embedding = emb

    return chunks


def save_embeddings(chunks: list[Chunk]) -> None:
    """Persiste os embeddings em data/index/ (não versionado)."""
    embs = [c.embedding for c in chunks if c.embedding is not None]
    if (embs == []):
        return
    INDICES_PATH.parent.mkdir(parents=True, exist_ok=True)
    np.save(str(INDICES_PATH), np.array(embs, dtype=np.float32))
    print(f"indexador: {len(embs)} embeddings salvos em {INDICES_PATH}")
