"""Avaliador de fontes (stub) — passo 1.9.

Heurística explícita que produz um `score` numérico e uma justificativa textual
por documento, ambos persistidos. Critérios sugeridos: domínio da fonte,
presença de autor, idioma, indícios de revisão por pares, data de publicação.

O `score` resultante é o `evaluator_score` exigido nos metadados de cada chunk.

TODO(aluno): definir e documentar as heurísticas e seus pesos.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit


# Heurísticas e pesos definidos:
#   - Domínio da fonte (+0.30): wikipedia, archive.org, gov.br, edu.br, scielo
#   - Fonte estruturada (+0.20): wikipedia (artigo enciclopédico)
#   - Tamanho do conteúdo (+0.20): texto > 1000 chars indica conteúdo substantivo
#   - Ausência de termos spam (+0.10): penaliza "clique aqui", "assine agora", etc.

DOMINIOS_CONFIAVEIS = {
    "pt.wikipedia.org": 0.30,
    "en.wikipedia.org": 0.30,
    "archive.org": 0.25,
    "scielo.br": 0.30,
    "scielo.org": 0.30,
    "gov.br": 0.25,
    "edu.br": 0.25,
    "ufam.edu.br": 0.30,
    "brasilescola.uol.com.br": 0.20,
    "khanacademy.org": 0.25,
    "fisica.net": 0.20,
    "infoescola.com": 0.15,
}

TERMOS_SPAM = [
    "clique aqui",
    "assine agora",
    "publicidade",
    "advertisement",
    "cookie policy",
    "aceitar cookies",
    "politica de privacidade",
    "newsletter",
    "cadastre-se gratis",
]


@dataclass
class SourceEvaluation:
    score: float           # 0.0 a 1.0 (evaluator_score)
    rationale: str         # justificativa textual persistida


def evaluate(doc) -> SourceEvaluation:
    """Avalia a credibilidade de um documento coletado."""
    # Aplica heurísticas explícitas e produz score + justificativa.
    reasons: list[str] = []
    score = 0.0

    # extrai campos de forma compatível com dataclass e dict
    if hasattr(doc, "source_url"):
        source_url: str = doc.source_url
        source_kind: str = doc.source_kind
        raw_path: str = doc.raw_path
    else:
        source_url = doc.get("source_url", "")
        source_kind = doc.get("source_kind", "")
        raw_path = doc.get("raw_path", "")

    # 1. domínio confiável
    netloc = urlsplit(source_url).netloc.lstrip("www.")
    dominio_score = 0.0
    for dominio, s in DOMINIOS_CONFIAVEIS.items():
        if dominio in netloc:
            dominio_score = s
            reasons.append(f"dominio confiavel ({dominio}): +{s:.2f}")
            break
    if dominio_score == 0.0:
        reasons.append("dominio nao reconhecido: +0.00")
    score += dominio_score

    # 2. fonte estruturada (wikipedia tem artigo enciclopédico)
    if source_kind == "wikipedia":
        score += 0.20
        reasons.append("fonte wikipedia (estruturada): +0.20")
    elif source_kind == "publico":
        score += 0.10
        reasons.append("fonte dominio publico (archive.org): +0.10")

    # 3. tamanho do conteúdo
    try:
        from pathlib import Path
        text = Path(raw_path).read_text(encoding="utf-8", errors="ignore")
        if len(text) >= 1000:
            score += 0.20
            reasons.append(f"conteudo substantivo ({len(text)} chars): +0.20")
        elif len(text) >= 300:
            score += 0.10
            reasons.append(f"conteudo moderado ({len(text)} chars): +0.10")
        else:
            reasons.append(f"conteudo curto ({len(text)} chars): +0.00")

        # 4. ausência de termos spam
        text_lower = text.lower()
        spam_encontrado = [t for t in TERMOS_SPAM if t in text_lower]
        if spam_encontrado:
            penalidade = min(0.20, len(spam_encontrado) * 0.05)
            score -= penalidade
            reasons.append(f"termos de spam encontrados {spam_encontrado[:3]}: -{penalidade:.2f}")
        else:
            score += 0.10
            reasons.append("sem termos de spam: +0.10")
    except Exception as exc:
        reasons.append(f"erro ao ler arquivo ({exc}): conteudo nao avaliado")

    # clampeia entre 0 e 1
    score = max(0.0, min(1.0, score))
    rationale = "; ".join(reasons)
    return SourceEvaluation(score=round(score, 4), rationale=rationale)
