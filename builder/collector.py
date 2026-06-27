"""Coletor (stub) — passo 1.8.

Executa buscas e fetch de páginas conforme o plano. Use **ao menos três** fontes
(web search aberto, Wikipedia, arXiv, Google Scholar, OpenStax, MIT OpenCourseWare,
SciELO, domínio público). A diversidade de fontes é avaliada (Camada 1).

O conteúdo bruto coletado **NÃO é versionado** (Seção 6.4) — fica em data/raw/
(ignorado). Apenas metadados/proveniência entram no repositório.

O log de execução (consultas, URLs visitadas, tempo) deve ser persistido.

TODO(aluno): respeitar robots.txt, rate limits e termos de uso (Seção 8).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CollectedDoc:
    source_url: str
    topic_ids: list[str]
    raw_path: str          # caminho local em data/raw/ (não versionado)
    fetched_at: str        # ISO 8601
    source_kind: str       # ex.: wikipedia | arxiv | openstax | scielo | web


def collect(plan: dict) -> list[CollectedDoc]:
    """Executa a coleta conforme o plano e devolve os documentos brutos."""
    # TODO(aluno): implementar busca + fetch; salvar bruto em data/raw/;
    # registrar log de execução (data/collection_log.json).
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit("Stub: implemente collect() e chame a partir de builder.run.")
