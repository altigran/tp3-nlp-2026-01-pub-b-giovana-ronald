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
from bs4 import BeautifulSoup
from urllib.parse import urlsplit
import os
import requests
import wikipediaapi

@dataclass
class CollectedDoc:
    source_url: str
    topic_ids: list[str]
    raw_path: str          # caminho local em data/raw/ (não versionado)
    fetched_at: str        # ISO 8601
    source_kind: str       # ex.: wikipedia | arxiv | openstax | scielo | web


def collect(plan: dict) -> list[CollectedDoc]:
    """Executa a coleta conforme o plano e devolve os documentos brutos."""
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
                        nome_arq = f"data/raw/{topico["topic_id"]}_wikipedia.txt"
                        with open(nome_arq, 'w') as arq:
                            arq.write(pag.title+'\n')
                            arq.write(pag.text)
                    case "web":
                        resultados = DDGS().text(query=q, max_results=5, backend="duckduckgo")
                        if (resultados):
                            for r in resultados:
                                url = r["href"]
                                if ("wikipedia" not in url) and (url.endswith(".pdf") == False):
                                    req = requests.get(url)
                                    if (req.status_code == 200):
                                        soup = BeautifulSoup(req.text, "html.parser")
                                        # tira items irrelevantes da página
                                        for item in soup(["header", "nav", "style", "script", "footer", "noscript"]):
                                            item.decompose()
                                        for img in soup.find_all("img"):
                                            src = img.get("src", "")
                                            markdown = f" ![Fórmula]({src}) "
                                            img.replace_with(markdown)
                                        # caso as formulares forem em mathjax (acontece no brasilescola, por exemplo)
                                        for mjx_container in soup.find_all("mjx-container"):
                                            assistive_mml = mjx_container.find("mjx-assistive-mml")
                                            if (assistive_mml):
                                                math = assistive_mml.find("math")
                                                mjx_container.replace_with(f" {str(math)} ")
                                        nome_arq = f"data/raw/{topico["topic_id"]}_{urlsplit(url).netloc}.md"
                                        with open(nome_arq, 'w') as arq:
                                            arq.write(soup.get_text(separator='\n', strip=True))
                                if (url.endswith(".pdf")):
                                    nome_arq = f"data/raw/{topico["topic_id"]}_{urlsplit(url).netloc}.pdf"
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
