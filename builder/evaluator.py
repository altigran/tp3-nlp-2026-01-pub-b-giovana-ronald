"""Avaliador de fontes (stub) — passo 1.9.

Heurística explícita que produz um `score` numérico e uma justificativa textual
por documento, ambos persistidos. Critérios sugeridos: domínio da fonte,
presença de autor, idioma, indícios de revisão por pares, data de publicação.

O `score` resultante é o `evaluator_score` exigido nos metadados de cada chunk.

TODO(aluno): definir e documentar as heurísticas e seus pesos.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SourceEvaluation:
    score: float           # 0.0 a 1.0 (evaluator_score)
    rationale: str         # justificativa textual persistida


def evaluate(doc) -> SourceEvaluation:
    """Avalia a credibilidade de um documento coletado."""
    # TODO(aluno): aplicar heurísticas explícitas e produzir score + justificativa.
    raise NotImplementedError
