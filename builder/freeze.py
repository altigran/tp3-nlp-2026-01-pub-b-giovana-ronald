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


def compute_corpus_hash(chunk_payloads: list[dict]) -> str:
    """Hash determinístico sobre os hashes de conteúdo bruto dos chunks."""
    raw_hashes = sorted(c["raw_content_hash"] for c in chunk_payloads)
    return hashlib.sha256(json.dumps(raw_hashes, ensure_ascii=False).encode("utf-8")).hexdigest()


def freeze(chunk_payloads: list[dict], topics_state: list[dict]) -> str:
    """Congela o corpus: grava corpus_hash, metadados e memória da disciplina."""
    corpus_hash = compute_corpus_hash(chunk_payloads)
    for c in chunk_payloads:
        c["corpus_hash"] = corpus_hash

    Path("data").mkdir(exist_ok=True)
    Path("data/corpus_meta.json").write_text(
        json.dumps(
            {
                "corpus_hash": corpus_hash,
                "chunk_count": len(chunk_payloads),
                "topics_state": topics_state,  # cobertura, document_count, avg_credibility
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    # TODO(aluno): persistir também os metadados por chunk (sem o conteúdo bruto).
    print(f"corpus congelado — corpus_hash={corpus_hash}")
    return corpus_hash
