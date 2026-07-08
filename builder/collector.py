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

import hashlib
import json
import os
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from urllib.parse import urlsplit

import requests
import wikipediaapi
from bs4 import BeautifulSoup
from ddgs import DDGS

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:152.0) Gecko/20100101 Firefox/152.0"
HEADERS = {"User-Agent": USER_AGENT}
REQUEST_TIMEOUT = 15  # segundos
MAX_WEB_RESULTS = 5
MAX_ARCHIVE_ITEMS = 3  # geralmente os 3 primeiros são os mais confiáveis
DATA_RAW = Path("data/raw")


@dataclass
class CollectedDoc:
    source_url: str
    topic_ids: list[str]
    raw_path: str          # caminho local em data/raw/ (não versionado)
    fetched_at: str        # ISO 8601
    source_kind: str       # ex.: wikipedia | arxiv | openstax | scielo | web
    raw_content_hash: str  # sha256 do conteúdo bruto
    evaluator_score: float = 0.0  # preenchido pelo evaluator


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _iso_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _safe_filename(topic_id: str, kind: str, suffix: str) -> Path:
    return DATA_RAW / f"{topic_id}_{kind}_{suffix}"


def _collect_wikipedia(topic_id: str, query: str, docs: list[CollectedDoc], log_entries: list[dict]) -> None:
    wiki = wikipediaapi.Wikipedia(user_agent=USER_AGENT, language="pt")
    pag = wiki.page(query)
    if not pag.exists():
        # tenta busca pelo slug sem espaços
        slug = query.replace(" ", "_")
        pag = wiki.page(slug)
    if not pag.exists():
        log_entries.append({"source": "wikipedia", "query": query, "status": "not_found"})
        return

    text = pag.title + "\n" + pag.text
    nome_arq = _safe_filename(topic_id, "wikipedia", f"{_sha256(pag.fullurl)[:8]}.txt")
    nome_arq.write_text(text, encoding="utf-8")
    raw_hash = _sha256(text)

    docs.append(
        CollectedDoc(
            source_url=pag.fullurl,
            topic_ids=[topic_id],
            raw_path=str(nome_arq),
            fetched_at=_iso_now(),
            source_kind="wikipedia",
            raw_content_hash=raw_hash,
        )
    )
    log_entries.append({"source": "wikipedia", "query": query, "url": pag.fullurl, "status": "ok"})


def _collect_web(topic_id: str, query: str, docs: list[CollectedDoc], log_entries: list[dict]) -> None:
    try:
        resultados = DDGS().text(query=query, max_results=MAX_WEB_RESULTS, backend="duckduckgo")
    except Exception as exc:
        log_entries.append({"source": "web", "query": query, "status": "ddg_error", "detail": str(exc)})
        return

    if not resultados:
        log_entries.append({"source": "web", "query": query, "status": "no_results"})
        return

    for r in resultados:
        url: str = r.get("href", "")
        if not url:
            continue
        # ignora wikipedia (já coletada) e PDFs
        if "wikipedia" in url or url.lower().endswith(".pdf"):
            continue
        try:
            resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            if resp.status_code != 200:
                log_entries.append({"source": "web", "url": url, "status": f"http_{resp.status_code}"})
                continue
        except Exception as exc:
            log_entries.append({"source": "web", "url": url, "status": "fetch_error", "detail": str(exc)})
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        # tira itens irrelevantes da página
        for tag in soup(["header", "nav", "style", "script", "footer", "noscript"]):
            tag.decompose()
        for img in soup.find_all("img"):
            src = img.get("src", "")
            markdown = f" ![Fórmula]({src}) "
            img.replace_with(markdown)
        # caso as fórmulas forem em mathjax (acontece no brasilescola, por exemplo)
        for mjx_container in soup.find_all("mjx-container"):
            assistive_mml = mjx_container.find("mjx-assistive-mml")
            if assistive_mml:
                math = assistive_mml.find("math")
                mjx_container.replace_with(f" {str(math)} ")

        text = soup.get_text(separator="\n", strip=True)
        if len(text) < 200:
            # página sem conteúdo útil
            continue

        netloc = urlsplit(url).netloc
        nome_arq = _safe_filename(topic_id, "web", f"{netloc}_{_sha256(url)[:8]}.txt")
        nome_arq.write_text(text, encoding="utf-8")
        raw_hash = _sha256(text)

        docs.append(
            CollectedDoc(
                source_url=url,
                topic_ids=[topic_id],
                raw_path=str(nome_arq),
                fetched_at=_iso_now(),
                source_kind="web",
                raw_content_hash=raw_hash,
            )
        )
        log_entries.append({"source": "web", "query": query, "url": url, "status": "ok"})


def _collect_publico(topic_id: str, query: str, docs: list[CollectedDoc], log_entries: list[dict]) -> None:
    try:
        from internetarchive import search_items, get_item
    except ImportError:
        log_entries.append({"source": "publico", "query": query, "status": "import_error"})
        return

    ia_query = f"{query} AND collection:opensource AND mediatype:texts AND language:portuguese"
    try:
        results = list(search_items(ia_query, fields=["identifier", "title", "subject"]))
    except Exception as exc:
        log_entries.append({"source": "publico", "query": query, "status": "search_error", "detail": str(exc)})
        return

    for i, r in enumerate(results):
        if i >= MAX_ARCHIVE_ITEMS:  # geralmente os 3 primeiros são os mais confiáveis
            break
        item_id = r.get("identifier", "")
        if not item_id:
            continue
        try:
            item = get_item(item_id)
            # pega metadados do item ao invés de baixar PDF (economia de disco)
            meta = item.metadata or {}
            titulo = str(meta.get("title", item_id))
            descricao = str(meta.get("description", ""))
            assunto = str(meta.get("subject", ""))
            text = f"Titulo: {titulo}\nAssunto: {assunto}\nDescricao: {descricao}"
            if len(text) < 50:
                continue
            nome_arq = _safe_filename(topic_id, "publico", f"{item_id[:40]}.txt")
            nome_arq.write_text(text, encoding="utf-8")
            raw_hash = _sha256(text)
            url = f"https://archive.org/details/{item_id}"
            docs.append(
                CollectedDoc(
                    source_url=url,
                    topic_ids=[topic_id],
                    raw_path=str(nome_arq),
                    fetched_at=_iso_now(),
                    source_kind="publico",
                    raw_content_hash=raw_hash,
                )
            )
            log_entries.append({"source": "publico", "query": query, "item_id": item_id, "status": "ok"})
        except Exception as exc:
            log_entries.append({"source": "publico", "query": query, "item_id": item_id, "status": "error", "detail": str(exc)})


def collect(plan: dict) -> list[CollectedDoc]:
    """Executa a coleta conforme o plano e devolve os documentos brutos."""
    # implementar busca + fetch; salvar bruto em data/raw/;
    # registrar log de execução (data/collection_log.json).
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    docs: list[CollectedDoc] = []
    log_entries: list[dict] = []

    for topico in plan["topics"]:
        topic_id: str = topico["topic_id"]
        fontes: list[str] = topico.get("target_sources", ["wikipedia", "web", "publico"])
        queries: list[str] = topico.get("queries", [])

        for query in queries:
            for fonte in fontes:
                match fonte:
                    case "wikipedia":
                        _collect_wikipedia(topic_id, query, docs, log_entries)
                    case "web":
                        _collect_web(topic_id, query, docs, log_entries)
                    case "publico":
                        _collect_publico(topic_id, query, docs, log_entries)
                    case _:
                        log_entries.append({"fonte": fonte, "status": "unknown_source"})

    Path("data/collection_log.json").write_text(
        json.dumps({"collected_at": _iso_now(), "entries": log_entries}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"coleta concluida — {len(docs)} documentos, {len(log_entries)} entradas de log")
    return docs


if __name__ == "__main__":
    raise SystemExit("Stub: implemente collect() e chame a partir de builder.run.")
