"""Planner de coleta (stub) — passo 1.7.

Deriva um plano de coleta por tópico a partir da ementa estruturada. O plano é
persistido e auditável (entra em data/plano_coleta.json).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_plan(structured_ementa: dict[str, Any]) -> dict[str, Any]:
    """Gera o plano de coleta por tópico."""
    topicos = []
    fontes = ["wikipedia", "web", "publico"]
    for top in structured_ementa["topics"]:
        queries = structured_ementa["subtopicos"] + structured_ementa["key_concepts"]
        topicos.append({"topic_id": top["topic_id"], "queries": queries, "target_sources": fontes, "max_docs": len(queries)})

    return {
        "version": 1,
        "seed": 42,
        "topics": topicos
    }


def main() -> None:
    ementa = json.loads(Path("data/ementa_estruturada.json").read_text(encoding="utf-8"))
    plan = build_plan(ementa)
    out = Path("data/plano_coleta.json")
    out.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"plano de coleta escrito em {out}")


if __name__ == "__main__":
    main()
