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

from dataclasses import dataclass


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


def build_index(evaluated_docs: list) -> list[Chunk]:
    """Fragmenta em chunks, calcula embeddings e popula a vector store."""
    # TODO(aluno): chunking + embeddings + upsert na vector store + metadados.
    raise NotImplementedError
