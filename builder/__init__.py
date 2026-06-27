"""Construtor de corpus (offline) — Trilha B.

Pipeline de módulos que, a partir da ementa, executa parser, planner, busca,
fetch, avaliação de fontes, deduplicação e indexação, encerrando com o
congelamento do corpus (hash do índice e dos metadados). **Não usa MCP.**
"""
