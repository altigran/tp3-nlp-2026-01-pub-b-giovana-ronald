"""Runner do pipeline offline do construtor de corpus: `python -m builder`.

Orquestra parser -> planner -> coletor -> avaliador -> dedup -> indexador ->
congelador. **Não usa MCP.** Cada etapa persiste sua saída para auditoria.

TODO(aluno): conectar as etapas reais. O esqueleto abaixo mostra a ordem.
"""

from __future__ import annotations


def run() -> None:
    # from builder.parse_ementa import parse_ementa
    # from builder.planner import build_plan
    # from builder.collector import collect
    # from builder.evaluator import evaluate
    # from builder.dedup import deduplicate
    # from builder.indexer import build_index
    # from builder.freeze import freeze
    #
    # 1) parse_ementa  -> data/ementa_estruturada.json
    # 2) build_plan    -> data/plano_coleta.json
    # 3) collect       -> data/raw/ (não versionado) + data/collection_log.json
    # 4) evaluate      -> score + justificativa por documento
    # 5) deduplicate
    # 6) build_index   -> vector store (não versionada) + metadados por chunk
    # 7) freeze        -> data/corpus_meta.json (corpus_hash, memória da disciplina)
    raise NotImplementedError("Stub: implemente o pipeline conectando os módulos de builder/.")


if __name__ == "__main__":
    run()
