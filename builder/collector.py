"""Coletor (stub) — passo 1.8.

Executa buscas e fetch de páginas conforme o plano. Use **ao menos três** fontes
(web search aberto, Wikipedia, arXiv, Google Scholar, OpenStax, MIT OpenCourseWare,
SciELO, domínio público). A diversidade de fontes é avaliada (Camada 1).

O conteúdo bruto coletado **NÃO é versionado** (Seção 6.4) — fica em data/raw/
(ignorado). Apenas metadados/proveniência entram no repositório.

O log de execução (consultas, URLs visitadas, tempo) deve ser persistido.
"""

from __future__ import annotations
from dataclasses import dataclass
from ddgs import DDGS
from internetarchive import search_items, get_item
import wikipediaapi
import os

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
    os.makedirs("data/raw", exist_ok=True)
    # registrar log de execução (data/collection_log.json).
    docs = []
    for topico in plan["topics"]:
        fontes = plan["target_sources"]
        header = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:152.0) Gecko/20100101 Firefox/152.0"}
        for q in topico["queries"]:
            for fonte in fontes:
                match fonte:
                    case "wikipedia":
                        wiki = wikipediaapi.Wikipedia(user_agent=header["User-Agent"], language='pt')
                        pag = wiki.page(q)
                        if (pag.exists() == False):
                            pags = wiki.search(q).pages
                            pag = list(pags.values())[0]
                        with open(f"data/raw/{topico["topic_id"]}_wikipedia.txt", 'w') as arq:
                            arq.write(pag.title+'\n')
                            arq.write(pag.text)
                    case "web":
                        resultados = DDGS().text(query=q, max_results=5, backend="duckduckgo")
                        if (resultados):
                            for r in resultados:
                                url = r["href"]
                                if ("wikipedia" not in url):
                                    # a decidir como salvar pagina
                    case "publico":
                        query = f"{q} AND collection:opensource AND mediatype:texts"
                        result = search_items(query)
                        for i, r in enumerate(result):
                            if (i == 3): # geralmente os 3 primeiros são os mais confiáveis
                                break
                            item_id = r["identifier"]
                            item = get_item(item_id)
                            item.download(formats=["PDF"], destdir="data/raw")
    return docs

if __name__ == "__main__":
    raise SystemExit("Stub: implemente collect() e chame a partir de builder.run.")
