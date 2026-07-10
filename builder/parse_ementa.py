"""Parser de ementa — passo 1.6.

Produz representação estruturada da ementa a partir do texto bruto, com ao
menos: (i) lista de tópicos e subtópicos, (ii) conceitos-chave por tópico,
(iii) pré-requisitos declarados, (iv) bibliografia citada.

Saída persistida em JSON e revisada manualmente; erros de extração devem ser
registrados no relatório.
"""

from __future__ import annotations

import re2
import os
import json
from pathlib import Path
from typing import Any
from openai import OpenAI


class LLMAuxiliar:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.environ.get("API_KEY"),
            base_url="https://integrate.api.nvidia.com/v1"
        )
        self.nome = "google/gemma-4-31b-it"

    def respondePrompt(self, prompt):
        try:
            resposta = self.client.chat.completions.create(
                model=self.nome,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0
            )
            return resposta.choices[0].message.content
        except Exception as erro:
            print(erro)
        return None

def parse_ementa(raw_text: str) -> dict[str, Any]:
    """Converte o texto bruto da ementa em estrutura auditável."""
    erros = []

    result = re2.search(r"Disciplina:\s*(.+)", raw_text)
    try:
        disciplina = str(result.group(1)).strip()
    except Exception as erro:
        disciplina = []
        erros.append(f"Disciplina: {erro}")

    result = re2.search(r"Área \(ENADE\):\s*(.+)", raw_text)
    try:
        area = str(result.group(1)).strip()
    except Exception as erro:
        area = []
        erros.append(f"Área: {erro}")

    options = re2.Options()
    options.dot_nl = True
    regex = re2.compile(r"Ementa:\s*(.+?)Pré-requisitos:", options)
    result = re2.search(regex, raw_text)
    try:
        top = str(result.group(1)).strip()
        with open("data/ementa_estruturada.example.json", 'r') as arq:
            exemplo = json.load(arq)
        print("Separando em tópicos...")
        llm = LLMAuxiliar()
        resposta = llm.respondePrompt(f'''
        Classifique os termos em tópicos e subtópicos. Para cada tópico, gere um JSON com "topic_id" (slug do nome), "name", "subtopics" (lista de strings) e "key_concepts" (lista de strings).
        Retorne APENAS uma lista JSON válida, utilizando aspas duplas, sem texto extra, sem quebras de linha entre itens, sem markdown.
        
        Exemplo:
        Entrada: "Ciclo hidrológico. Precipitação e sua medida. Evapotranspiração. Bacias hidrográficas: delimitação e características físicas. Escoamento superficial. Tempo de concentração."
        Saída: {exemplo["topics"]}

        Entrada: {top}
        Saída:''')
        if (resposta.startswith("```json")):
            resposta = resposta.replace("```json", '')
        if (resposta.endswith("```")):
            resposta = resposta.replace("```", '')
        resposta = resposta.strip()
        print(resposta)
        topicos = json.loads(resposta)
    except Exception as erro:
        topicos = []
        erros.append(f"Tópicos: {erro}")

    result = re2.search(r"Pré-requisitos:\s*([^.]+)", raw_text)
    try:
        preq = str(result.group(1)).strip()
        prerequisitos = [p.strip() for p in preq.split(';') if p.strip()]
    except Exception as erro:
        prerequisitos = []
        erros.append(f"Pré-requisitos: {erro}")

    result = re2.search(r"Bibliografia:\s*((?:-\s*.*(?:\n|$))+)", raw_text)
    try:
        bib = str(result.group(1)).strip()
        biblio = [b.lstrip("- ").strip() for b in bib.split("\n") if b.strip()]
    except Exception as erro:
        biblio = []
        erros.append(f"Bibliografia: {erro}")

    return {
        "discipline": disciplina,
        "area": area,
        "topics": topicos,
        "prerequisites": prerequisitos,
        "bibliography": biblio,
        "extraction_errors": erros,
    }


def main() -> None:
    raw = Path("data/ementa.txt").read_text(encoding="utf-8")
    structured = parse_ementa(raw)
    out = Path("data/ementa_estruturada.json")
    out.write_text(json.dumps(structured, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"ementa estruturada escrita em {out}")


if __name__ == "__main__":
    main()
