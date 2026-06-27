"""Deduplicador (stub).

Remove documentos/trechos redundantes antes da indexação (ex.: near-duplicates
por hash de shingles / similaridade de embeddings). Reduz inflação artificial
de cobertura e diversidade.

TODO(aluno): escolher e documentar a estratégia de deduplicação.
"""

from __future__ import annotations


def deduplicate(docs: list) -> list:
    """Devolve a lista de documentos sem duplicatas."""
    # TODO(aluno): implementar (ex.: MinHash/SimHash ou similaridade de embeddings).
    raise NotImplementedError
