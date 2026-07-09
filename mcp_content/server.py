"""Servidor MCP de conteúdo read-only — passo 1.11.

Implementa as três tools do contrato da Seção 3.1 sobre o **corpus congelado**.
Transporte stdio. Tratamento explícito de erros (índice inválido, chunk
inexistente, query malformada) com mensagens estruturadas — **sem propagar
exceções** ao cliente.

O contrato completo está no `CONTRATO.md` do Kit de Compatibilidade. Valide este
servidor com o `check_contract` do kit:

    ( cd ../kit-compatibilidade && \\
      python -m check_contract --target "python -m mcp_content" \\
        --json "$OLDPWD/evaluation/contract/report.json" )
"""

from __future__ import annotations

from pathlib import Path
from mcp.server.fastmcp import FastMCP
from sentence_transformers import SentenceTransformer
import json
import numpy as np

# --- Envelope do contrato (mantenha igual ao CONTRATO.md do kit) -----------
# Códigos canônicos: MALFORMED_QUERY, INVALID_K, INVALID_FILTERS, CHUNK_NOT_FOUND.
# Metadados obrigatórios por chunk: chunk_id, text, source_url, evaluator_score,
# collected_at, topics, raw_content_hash, discipline, corpus_hash.

# --- Caminhos do corpus congelado ------------------------------------------
CORPUS_CHUNKS_PATH = Path("data/corpus_chunks.json")
CORPUS_META_PATH = Path("data/corpus_meta.json")
CORPUS_EMBEDDINGS_PATH = Path("data/index/embeddings.npy")

EMBED_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMBED_DIM = 384


def ok(data: dict) -> dict:
    return {"ok": True, "data": data}


def err(code: str, message: str, **extra) -> dict:
    return {"ok": False, "error": {"code": code, "message": message, **extra}}


# --- Carregamento do corpus congelado (data/corpus_meta.json + índice) ------

def _load_corpus() -> tuple[list[dict], dict, np.ndarray | None]:
    """Carrega chunks, meta e matrix de embeddings do corpus congelado."""
    if not CORPUS_CHUNKS_PATH.exists():
        return [], {}, None
    chunks = json.loads(CORPUS_CHUNKS_PATH.read_text(encoding="utf-8"))
    meta = {}
    if CORPUS_META_PATH.exists():
        meta = json.loads(CORPUS_META_PATH.read_text(encoding="utf-8"))

    # carrega matriz de embeddings do ficheiro numpy (separado do JSON)
    embed_matrix: np.ndarray | None = None
    if CORPUS_EMBEDDINGS_PATH.exists():
        embed_matrix = np.load(str(CORPUS_EMBEDDINGS_PATH)).astype(np.float32)
        # normaliza linhas para cosseno eficiente via dot product
        if (embed_matrix):
            norms = np.sqrt(np.sum(embed_matrix ** 2, axis=1, keepdims=True))
            norms[norms == 0] = 1.0
            embed_matrix = embed_matrix / norms

    return chunks, meta, embed_matrix


# carregamento na inicialização do módulo
_CHUNKS, _META, _EMBED_MATRIX = _load_corpus()

# índice para get_chunk por chunk_id
_CHUNK_INDEX: dict[str, dict] = {c["chunk_id"]: c for c in _CHUNKS}

CORPUS_HASH: str = _META.get("corpus_hash", "")

mcp = FastMCP("agente-conteudo")


# --- Modelo de embedding (lazy init) ---------------------------------------

_model: SentenceTransformer | None = None


def _embed_query(query: str) -> np.ndarray | None:
    """Calcula embedding da query com sentence-transformers."""
    global _model
    if _model is None:
        print(f"servidor: carregando modelo {EMBED_MODEL_NAME}...")
        _model = SentenceTransformer(EMBED_MODEL_NAME)
    try:
        vec = np.asarray(_model.encode([query], normalize_embeddings=True), dtype=np.float32).flatten()
        return vec
    except Exception as exc:
        print(f"aviso: erro ao calcular embedding da query: {exc}")
        return None


def _keyword_rank(query: str, k: int, filters: dict | None) -> list[dict]:
    """Fallback: ranking por contagem de tokens da query nos chunks."""
    tokens = set(query.lower().split())
    scored: list[tuple[float, dict]] = []
    for c in _CHUNKS:
        if filters:
            topic_filter = filters.get("topic")
            if topic_filter and topic_filter not in c.get("topics", []):
                continue
        text_tokens = set(c.get("text", "").lower().split())
        score = len(tokens & text_tokens) / max(len(tokens), 1)
        scored.append((score, c))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:k]]


def _chunk_payload(c: dict) -> dict:
    """Retorna apenas os campos exigidos pelo contrato (sem embedding)."""
    return {
        "chunk_id": c.get("chunk_id", ""),
        "text": c.get("text", ""),
        "source_url": c.get("source_url", ""),
        "evaluator_score": c.get("evaluator_score", 0.0),
        "collected_at": c.get("collected_at", ""),
        "topics": c.get("topics", []),
        "raw_content_hash": c.get("raw_content_hash", ""),
        "discipline": c.get("discipline", ""),
        "corpus_hash": c.get("corpus_hash", CORPUS_HASH),
    }


# --- Tools do contrato ------------------------------------------------------

@mcp.tool()
def list_topics() -> dict:
    """Tópicos cobertos e estado por tópico (cobertura, nº docs, credibilidade)."""
    # Devolver discipline/area/enade_editions/corpus_hash/topics reais.
    if not _META:
        return err("NOT_READY", "corpus nao encontrado — execute 'python3 -m builder' primeiro")

    meta = _META
    topics_state = meta.get("topics_state", [])

    return ok(
        {
            "discipline": meta.get("discipline", ""),
            "area": meta.get("area", ""),
            "enade_editions": ["2019", "2021", "2023"],
            "corpus_hash": CORPUS_HASH,
            "topics": [
                {
                    "topic_id": t.get("topic_id", ""),
                    "coverage": t.get("coverage", 0.0),
                    "document_count": t.get("document_count", 0),
                    "avg_credibility": t.get("avg_credibility", 0.0),
                    "discipline": t.get("discipline", meta.get("discipline", "")),
                }
                for t in topics_state
            ],
        }
    )


@mcp.tool()
def corpus_query(query: str, k: int = 5, filters: dict | None = None) -> dict:
    """k chunks mais relevantes, com proveniência completa nos metadados."""
    if not isinstance(query, str) or not query.strip():
        return err("MALFORMED_QUERY", "parâmetro 'query' ausente ou vazio")
    if isinstance(k, bool) or not isinstance(k, int) or k <= 0:
        return err("INVALID_K", "parâmetro 'k' deve ser inteiro positivo")
    if filters is not None and not isinstance(filters, dict):
        return err("INVALID_FILTERS", "parâmetro 'filters' deve ser objeto/dicionário")

    if not _CHUNKS:
        return err("NOT_READY", "corpus nao encontrado — execute 'python3 -m builder' primeiro")

    # Recuperar da vector store e devolver chunks com TODOS os metadados.
    resultados: list[dict] = []
    if _EMBED_MATRIX is not None:
        q_vec = _embed_query(query.strip())
        if q_vec is not None:
            scores: np.ndarray = _EMBED_MATRIX @ q_vec  # cosseno (matriz normalizada)
            if filters and filters.get("topic"):
                topic_filter = filters["topic"]
                for i, c in enumerate(_CHUNKS):
                    if topic_filter not in c.get("topics", []):
                        scores[i] = -1.0
            top_k_idx = np.argsort(scores)[::-1][:k]
            resultados = [_CHUNKS[int(i)] for i in top_k_idx]
        else:
            resultados = _keyword_rank(query, k, filters)
    else:
        resultados = _keyword_rank(query, k, filters)

    return ok(
        {
            "query": query,
            "k": k,
            "corpus_hash": CORPUS_HASH,
            "chunks": [_chunk_payload(c) for c in resultados],
        }
    )


@mcp.tool()
def get_chunk(chunk_id: str) -> dict:
    """Recupera um chunk específico por identificador."""
    if not isinstance(chunk_id, str) or not chunk_id.strip():
        return err("MALFORMED_QUERY", "parâmetro 'chunk_id' ausente ou vazio")
    # Buscar o chunk; se inexistente, retornar CHUNK_NOT_FOUND.
    c = _CHUNK_INDEX.get(chunk_id.strip())
    if c is None:
        return err("CHUNK_NOT_FOUND", f"chunk '{chunk_id}' nao encontrado no corpus")

    return ok(_chunk_payload(c))


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
