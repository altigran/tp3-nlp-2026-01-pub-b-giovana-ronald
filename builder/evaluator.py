"""Avaliador de fontes — passo 1.9.

Heurística explícita que produz um `score` numérico e uma justificativa textual
por documento, ambos persistidos. Critérios sugeridos: domínio da fonte,
presença de autor, idioma, indícios de revisão por pares, data de publicação.

O `score` resultante é o `evaluator_score` exigido nos metadados de cada chunk.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit
from pathlib import Path

# Heurísticas e pesos definidos:
#   - Domínio da fonte (peso 2): wikipedia, top 5 universidades com bons cursos de física segundo o RUF da UOL, sites educativos
#   - Idioma (peso 1): penaliza texto em idiomas estrangeiros.
#   - Tamanho do conteúdo (peso 2): texto > 5000 chars indica conteúdo substantivo
#   - Ausência de termos spam (peso 1): penaliza "clique aqui", "assine", etc.

DOMINIOS_ACADEMICOS = [
    ".usp.br",
    ".unicamp.br",
    ".ufmg.br",
    ".ufrj.br",
    ".ufsc.br",
]

DOMINIOS_CONFIAVEIS = [
    "pt.wikipedia.org",
    "archive.org",
]

DOMINIOS_EDUCATIVOS = [
    "brasilescola.uol.com.br",
    "mundoeducacao.uol.com.br",
    "khanacademy.org",
    "todamateria.com.br"
]

TERMOS_SPAM = [
    "clique aqui",
    "assine",
    "publicidade",
    "advertisement",
    "política de privacidade",
    "newsletter",
    "cadastre-se",
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

    idioma_score = 0.0
    # 1. domínio confiável
    netloc = urlsplit(source_url).netloc.lstrip("www.")
    dominio_score = 0.0
    achou = [dominio for dominio in DOMINIOS_CONFIAVEIS if dominio == netloc]
    if (achou == []):
        achou = [dominio for dominio in DOMINIOS_EDUCATIVOS if dominio == netloc]
        if (achou == []):
            achou = [dominio for dominio in DOMINIOS_ACADEMICOS if netloc.endswith(dominio)]
            if (achou == []):
                reasons.append("domínio não reconhecido: 0.0")
            else:
                dominio_score = 1.0
                reasons.append(f"domínio acadêmico ({achou[0]}): 1.0")
        else:
            dominio_score = 0.5
            reasons.append(f"domínio educativo ({achou[0]}): 0.5")
            idioma_score = 1.0 # todos só tem artigos em pt-br, então já mata aqui
    else:
        dominio_score = 0.5
        reasons.append(f"domínio confiável ({achou[0]}): 0.5")

    tam_score = 0.0
    no_spam_score = 0.0
    try:
        text = Path(raw_path).read_text(encoding="utf-8", errors="ignore")
        text_lower = text.lower()
        # 2. idioma
        if (source_kind == "wikipedia"):
            idioma_score = 1.0 # já que é sempre da wikipedia pt-br
        elif (idioma_score == 0.0):
            if any(prep in text_lower for prep in [" da ", " do ", " em ", " com ", " uma ", " por "]):
                idioma_score = 1.0

        # 3. tamanho do conteúdo
        if len(text) >= 5000:
            tam_score = 1.0
            reasons.append(f"conteúdo substantivo ({len(text)} chars): 1.0")
        elif len(text) >= 1500:
            tam_score = 0.5
            reasons.append(f"conteúdo moderado ({len(text)} chars): 0.5")
        else:
            tam_score = 0.0
            reasons.append(f"conteúdo curto ({len(text)} chars): 0.0")

        # 4. ausência de termos spam
        spam_encontrado = [t for t in TERMOS_SPAM if t in text_lower]
        no_spam_score = 1.0
        if spam_encontrado:
            penalidade = min(0.20, len(spam_encontrado) * 0.05)
            no_spam_score -= penalidade
            reasons.append(f"termos de spam encontrados {spam_encontrado[:3]}: -{penalidade:.2f}")
        else:
            reasons.append("sem termos de spam: 1.0")
    except Exception as exc:
        reasons.append(f"erro ao ler arquivo ({exc}): conteúdo não avaliado")

    # média ponderada
    score = (2*dominio_score + 1*idioma_score + 2*tam_score + no_spam_score)/(2+1+2+1)
    rationale = "; ".join(reasons)
    return SourceEvaluation(score=round(score, 4), rationale=rationale)
