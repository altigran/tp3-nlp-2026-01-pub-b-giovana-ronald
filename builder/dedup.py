"""Deduplicador (stub).

Remove documentos/trechos redundantes antes da indexação (ex.: near-duplicates
por hash de shingles / similaridade de embeddings). Reduz inflação artificial
de cobertura e diversidade.

TODO(aluno): escolher e documentar a estratégia de deduplicação.
"""

from __future__ import annotations

from pathlib import Path


# Estratégia escolhida: dois passes:
#   1. Hash exato: remove documentos com raw_content_hash idêntico.
#   2. Near-duplicate por shingles: Jaccard sobre 3-shingles de palavras
#      para remover documentos com similaridade > threshold.

SHINGLE_SIZE = 3
JACCARD_THRESHOLD = 0.75  # docs acima disso são considerados duplicatas


def _shingles(text: str, k: int = SHINGLE_SIZE) -> set[tuple[str, ...]]:
    words = text.lower().split()
    if len(words) < k:
        return {tuple(words)}
    return {tuple(words[i : i + k]) for i in range(len(words) - k + 1)}


def _jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def deduplicate(docs: list) -> list:
    """Devolve a lista de documentos sem duplicatas."""
    # Implementação: MinHash/SimHash ou similaridade de embeddings.
    # Escolha: Jaccard sobre shingles (leve, sem deps extras).
    if not docs:
        return []

    def get_field(doc, field: str):
        if hasattr(doc, field):
            return getattr(doc, field)
        return doc.get(field, "")

    # passo 1: dedup por hash exato
    seen_hashes: set[str] = set()
    apos_hash: list = []
    for doc in docs:
        h = get_field(doc, "raw_content_hash")
        if h in seen_hashes:
            continue
        seen_hashes.add(h)
        apos_hash.append(doc)

    # passo 2: near-dup por shingles Jaccard
    shingles_list: list[set] = []
    for doc in apos_hash:
        raw_path = get_field(doc, "raw_path")
        try:
            text = Path(raw_path).read_text(encoding="utf-8", errors="ignore")
        except Exception:
            text = raw_path  # fallback: usa o próprio path como texto
        shingles_list.append(_shingles(text))

    unicos: list = []
    unicos_shingles: list[set] = []
    for i, doc in enumerate(apos_hash):
        sh = shingles_list[i]
        is_dup = any(_jaccard(sh, us) >= JACCARD_THRESHOLD for us in unicos_shingles)
        if not is_dup:
            unicos.append(doc)
            unicos_shingles.append(sh)

    removidos = len(docs) - len(unicos)
    print(f"dedup: {len(docs)} -> {len(unicos)} documentos ({removidos} removidos)")
    return unicos
