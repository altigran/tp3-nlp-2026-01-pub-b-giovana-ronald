"""Parser de ementa (stub) — passo 1.6.

Produz representação estruturada da ementa a partir do texto bruto, com ao
menos: (i) lista de tópicos e subtópicos, (ii) conceitos-chave por tópico,
(iii) pré-requisitos declarados, (iv) bibliografia citada.

Saída persistida em JSON e revisada manualmente; erros de extração devem ser
registrados no relatório.

TODO(aluno): implementar a extração real (regex/heurística/LLM auxiliar).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def parse_ementa(raw_text: str) -> dict[str, Any]:
    """Converte o texto bruto da ementa em estrutura auditável."""
    # TODO(aluno): preencher tópicos/subtópicos, conceitos, pré-requisitos, bibliografia.
    return {
        "discipline": "TODO",
        "area": "TODO",
        "topics": [
            # {"topic_id": "...", "name": "...", "subtopics": [...],
            #  "key_concepts": [...]}
        ],
        "prerequisites": [],
        "bibliography": [],
        "extraction_errors": [],
    }


def main() -> None:
    raw = Path("data/ementa.txt").read_text(encoding="utf-8")
    structured = parse_ementa(raw)
    out = Path("data/ementa_estruturada.json")
    out.write_text(json.dumps(structured, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"ementa estruturada escrita em {out}")


if __name__ == "__main__":
    main()
