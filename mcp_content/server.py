"""Servidor MCP de conteúdo read-only (stub) — passo 1.11.

Implementa as três tools do contrato da Seção 3.1 sobre o **corpus congelado**.
Transporte stdio. Tratamento explícito de erros (índice inválido, chunk
inexistente, query malformada) com mensagens estruturadas — **sem propagar
exceções** ao cliente.

O contrato completo está no `CONTRATO.md` do Kit de Compatibilidade. Valide este
servidor com o `check_contract` do kit:

    ( cd ../kit-compatibilidade && \
      python -m check_contract --target "python -m mcp_content" \
        --json "$OLDPWD/evaluation/contract/report.json" )

TODO(aluno): carregar o corpus congelado (vector store + metadados) e implementar
o ranking real. Os stubs abaixo já retornam o envelope correto.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

# --- Envelope do contrato (mantenha igual ao CONTRATO.md do kit) -----------
# Códigos canônicos: MALFORMED_QUERY, INVALID_K, INVALID_FILTERS, CHUNK_NOT_FOUND.
# Metadados obrigatórios por chunk: chunk_id, text, source_url, evaluator_score,
# collected_at, topics, raw_content_hash, discipline, corpus_hash.


def ok(data: dict) -> dict:
    return {"ok": True, "data": data}


def err(code: str, message: str, **extra) -> dict:
    return {"ok": False, "error": {"code": code, "message": message, **extra}}


mcp = FastMCP("agente-conteudo")

# TODO(aluno): carregar o corpus congelado aqui (data/corpus_meta.json + índice).
CORPUS_HASH = "TODO"


@mcp.tool()
def list_topics() -> dict:
    """Tópicos cobertos e estado por tópico (cobertura, nº docs, credibilidade)."""
    # TODO(aluno): devolver discipline/area/enade_editions/corpus_hash/topics reais.
    return err("NOT_IMPLEMENTED", "list_topics ainda não implementada")


@mcp.tool()
def corpus_query(query: str, k: int = 5, filters: dict | None = None) -> dict:
    """k chunks mais relevantes, com proveniência completa nos metadados."""
    if not isinstance(query, str) or not query.strip():
        return err("MALFORMED_QUERY", "parâmetro 'query' ausente ou vazio")
    if isinstance(k, bool) or not isinstance(k, int) or k <= 0:
        return err("INVALID_K", "parâmetro 'k' deve ser inteiro positivo")
    if filters is not None and not isinstance(filters, dict):
        return err("INVALID_FILTERS", "parâmetro 'filters' deve ser objeto/dicionário")
    # TODO(aluno): recuperar da vector store e devolver chunks com TODOS os metadados.
    return err("NOT_IMPLEMENTED", "corpus_query ainda não implementada")


@mcp.tool()
def get_chunk(chunk_id: str) -> dict:
    """Recupera um chunk específico por identificador."""
    if not isinstance(chunk_id, str) or not chunk_id.strip():
        return err("MALFORMED_QUERY", "parâmetro 'chunk_id' ausente ou vazio")
    # TODO(aluno): buscar o chunk; se inexistente, retornar CHUNK_NOT_FOUND.
    return err("NOT_IMPLEMENTED", "get_chunk ainda não implementada")


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
