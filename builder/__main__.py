"""Runner do pipeline offline do construtor de corpus: `python -m builder`.

Orquestra parser -> planner -> coletor -> avaliador -> dedup -> indexador ->
congelador. **Não usa MCP.** Cada etapa persiste sua saída para auditoria.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

def _sem_embedding(chunks):
    dicio = {}
    for k, v in chunks:
        if k != "embedding":
            dicio[k] = v
    return dicio

def run() -> None:
    from builder.parse_ementa import parse_ementa
    from builder.planner import build_plan
    from builder.collector import collect
    from builder.evaluator import evaluate
    from builder.dedup import deduplicate
    from builder.indexer import build_index, save_embeddings
    from builder.freeze import freeze

    # 1) parse_ementa  -> data/ementa_estruturada.json
    print("=== 1/7 parse_ementa ===")
    ementa_path = Path("data/ementa_estruturada.json")
    if ementa_path.exists():
        print(f"ementa ja estruturada em {ementa_path}, pulando parse.")
        ementa = json.loads(ementa_path.read_text(encoding="utf-8"))
    else:
        raw = Path("data/ementa.txt").read_text(encoding="utf-8")
        ementa = parse_ementa(raw)
        ementa_path.write_text(json.dumps(ementa, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"ementa estruturada escrita em {ementa_path}")

    discipline: str = ementa.get("discipline", "")
    area: str = ementa.get("area", "")

    # 2) build_plan    -> data/plano_coleta.json
    print("=== 2/7 planner ===")
    plan = build_plan(ementa)
    plano_path = Path("data/plano_coleta.json")
    plano_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"plano de coleta escrito em {plano_path}")

    # 3) collect       -> data/raw/ (não versionado) + data/collection_log.json
    print("=== 3/7 coletor ===")
    docs = collect(plan)
    if not docs:
        print("AVISO: nenhum documento coletado. Verifique a conexao com a internet.")
        return

    # 4) evaluate      -> score + justificativa por documento
    print("=== 4/7 avaliador ===")
    evaluations_log = []
    for doc in docs:
        ev = evaluate(doc)
        doc.evaluator_score = ev.score
        evaluations_log.append(
            {"source_url": doc.source_url, "score": ev.score, "rationale": ev.rationale}
        )
    Path("data/evaluations_log.json").write_text(
        json.dumps(evaluations_log, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"avaliacao concluida — {len(docs)} documentos avaliados")

    # 5) deduplicate
    print("=== 5/7 dedup ===")
    docs_unicos = deduplicate([doc for doc in docs if doc.evaluator_score >= 0.75])
    if not docs_unicos:
        print("AVISO: todos os documentos foram removidos pelo dedup.")
        return

    # 6) build_index   -> vector store (não versionada) + metadados por chunk
    print("=== 6/7 indexador ===")
    chunks = build_index(docs_unicos, discipline=discipline)
    if not chunks:
        print("AVISO: nenhum chunk gerado. Verifique os documentos coletados.")
        return
    save_embeddings(chunks)

    # 7) freeze        -> data/corpus_meta.json (corpus_hash, memória da disciplina)
    print("=== 7/7 freeze ===")
    chunk_dicts = [asdict(c, dict_factory=_sem_embedding) for c in chunks]
    corpus_hash = freeze(chunk_dicts, discipline=discipline, area=area)

    # atualiza manifest.json com corpus_hash e tópicos reais
    manifest_path = Path("manifest.json")
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["name"] = "agente-conteudo-fisica-ii-e"
        manifest["run"]["command"] = "python3 -m mcp_content"
        manifest["content"]["discipline"] = discipline
        manifest["content"]["area"] = area
        manifest["content"]["enade_editions"] = ["2017", "2019", "2023"]
        manifest["content"]["topics"] = [t["topic_id"] for t in ementa.get("topics", [])]
        manifest["content"]["corpus_hash"] = corpus_hash
        # remove campo de comentário do env se existir
        manifest["run"].pop("env", None)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"manifest.json atualizado com corpus_hash={corpus_hash[:16]}...")

    print("=== pipeline concluido ===")
    print(f"disciplina : {discipline}")
    print(f"area       : {area}")
    print(f"chunks     : {len(chunks)}")
    print(f"corpus_hash: {corpus_hash}")


if __name__ == "__main__":
    run()
