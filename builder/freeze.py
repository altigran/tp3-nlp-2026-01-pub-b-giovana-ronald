"""Congelador (stub) — passo 1.10/1.12.

Encerra o pipeline: calcula o `corpus_hash` (hash determinístico do índice e dos
metadados), preenche esse hash em todos os chunks e persiste o estado do corpus
e a **memória da disciplina** (estado por tópico: cobertura, número de documentos,
qualidade média das fontes).

O `corpus_hash` deve ser estável entre execuções (Seção 7) e referenciado em
todas as execuções da fase de tutoria.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from collections import defaultdict

CORPUS_META_PATH = Path("data/corpus_meta.json")
CORPUS_CHUNKS_PATH = Path("data/corpus_chunks.json")


def compute_corpus_hash(chunk_payloads: list[dict]) -> str:
    """Hash determinístico sobre os hashes de conteúdo bruto dos chunks."""
    raw_hashes = sorted(c["raw_content_hash"] for c in chunk_payloads)
    return hashlib.sha256(json.dumps(raw_hashes, ensure_ascii=False).encode("utf-8")).hexdigest()


def _compute_topics_state(chunk_payloads: list[dict], discipline: str) -> list[dict]:
    """Agrega estatísticas por tópico: cobertura, document_count, avg_credibility."""
    topico_docs: dict[str, set[str]] = defaultdict(set)  # topic_id -> set de source_url
    topico_scores: dict[str, list[float]] = defaultdict(list)

    for c in chunk_payloads:
        for tid in c.get("topics", []):
            topico_docs[tid].add(c["source_url"])
            topico_scores[tid].append(c["evaluator_score"])

    total_urls: set[str] = {c["source_url"] for c in chunk_payloads}

    states: list[dict] = []
    for tid, urls in topico_docs.items():
        scores = topico_scores[tid]
        avg_cred = round(sum(scores) / len(scores), 4) if scores else 0.0
        coverage = round(len(urls) / max(len(total_urls), 1), 4)
        states.append(
            {
                "topic_id": tid,
                "coverage": coverage,
                "document_count": len(urls),
                "avg_credibility": avg_cred,
                "discipline": discipline,
            }
        )

    return sorted(states, key=lambda x: x["topic_id"])


def freeze(chunk_payloads: list[dict], discipline: str = "", area: str = "") -> str:
    """Congela o corpus: grava corpus_hash, metadados e memória da disciplina."""
    corpus_hash = compute_corpus_hash(chunk_payloads)
    for c in chunk_payloads:
        c["corpus_hash"] = corpus_hash

    topics_state = _compute_topics_state(chunk_payloads, discipline)
    # cobertura, document_count, avg_credibility

    Path("data").mkdir(exist_ok=True)
    CORPUS_META_PATH.write_text(
        json.dumps(
            {
                "corpus_hash": corpus_hash,
                "chunk_count": len(chunk_payloads),
                "discipline": discipline,
                "area": area,
                "topics_state": topics_state,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    # Persistir também os metadados por chunk (sem o conteúdo bruto).
    CORPUS_CHUNKS_PATH.write_text(
        json.dumps(chunk_payloads, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"corpus congelado — corpus_hash={corpus_hash}")
    return corpus_hash
