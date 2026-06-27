# TP3 — Trilha B: Agente Acadêmico de Conteúdo (starter)

Starter code do **Agente Acadêmico de Conteúdo** (Trilha B). Componente de **duas
peças** em fases temporalmente separadas:

1. **Construtor de corpus (offline)** — `builder/`: parser de ementa, planner,
   coletor, avaliador de fontes, deduplicador, indexador e congelador. **Não usa MCP.**
2. **Servidor MCP de conteúdo (read-only)** — `mcp_content/`: serve o corpus
   congelado via as três tools do contrato (Seção 3.1). Não coleta nem escreve.

A disciplina-alvo é **uma única disciplina de graduação da UFAM, fora do
Instituto de Computação**, cuja área tenha prova ENADE com gabarito oficial e
cuja ementa esteja publicamente disponível.

> ⚠️ Trabalhe **dentro deste repositório gerado** pelo GitHub Classroom. Não crie
> repositório do zero, não aninhe em subpasta e não renomeie as pastas.

## Estrutura

```
builder/      pipeline offline (parser, planner, coletor, avaliador, dedup, indexador, congelador)
mcp_content/  servidor MCP read-only sobre o corpus congelado
data/         ementa estruturada, plano de coleta, metadados do corpus, hash congelado
evaluation/   resultados das suítes (construction, structural, content, contract, mock_integration, interop)
manifest.json manifesto do componente (Seção 3.1) — preencher
CHECKLIST.md  mapa requisito → onde foi cumprido (guia da correção)
```

> O **conteúdo bruto** coletado e o **índice da vector store** NÃO são versionados
> (Seção 6.4). Apenas metadados (URL, score, hash, chunks) e o `corpus_hash` entram
> no repositório. **Não versione enunciados completos do ENADE** — apenas a
> referência (edição, número da questão e link para a prova oficial).

## Pré-requisitos: clonar o Kit de Compatibilidade ao lado

O `check_contract` e o `tutor_mock` vivem no **Kit de Compatibilidade**
(repositório separado). Clone-o **ao lado** deste:

```bash
git clone <URL-do-kit-compatibilidade> ../kit-compatibilidade
```

Layout esperado:

```
trabalhos/
├── <seu-repo-trilha-b>/   ← você está aqui
└── kit-compatibilidade/   ← clonado ao lado
```

## Setup

```bash
python -m venv .venv && source .venv/bin/activate    # Python >= 3.10
pip install -r requirements.txt
```

## Fase 1 — construir, congelar e validar

```bash
# 1.5  anexar a ementa OFICIAL em data/ementa.txt (texto selecionável)
# 1.6–1.10  rodar o pipeline offline:
python -m builder            # parser -> planner -> coletor -> avaliador -> dedup -> indexador -> congelador

# 1.11  subir o servidor MCP read-only sobre o corpus congelado:
python -m mcp_content

# 1.15  conformidade ao contrato (rode a partir do kit; salve em evaluation/contract/):
#        --target-cwd aponta o servidor para ESTE repositório ($OLDPWD = onde você estava).
( cd ../kit-compatibilidade && \
  python -m check_contract --target "python -m mcp_content" --target-cwd "$OLDPWD" \
    --json "$OLDPWD/evaluation/contract/report.json" )

# 1.14  sessão de validação com o tutor_mock (registre em evaluation/mock_integration/):
( cd ../kit-compatibilidade && \
  python -m tutor_mock --target "python -m mcp_content" --target-cwd "$OLDPWD" )
```

> `--target` é o `run.command` do seu `manifest.json`; `--target-cwd` é a raiz
> deste repositório, onde `python -m mcp_content` resolve. É o ponto de acoplamento.

## O que entregar (resumo — ver CHECKLIST.md)

- `builder/` (pipeline completo) e `mcp_content/` (servidor read-only conforme o contrato).
- `data/` com ementa estruturada, plano de coleta, metadados do corpus e `corpus_hash`.
- `manifest.json` preenchido e validado por `check_contract`.
- `evaluation/construction/` (Camada 1), `evaluation/contract/`, `evaluation/mock_integration/` (Fase 1); `evaluation/interop/` (Fase 2).
- `RELATORIO.pdf` na raiz (máx. 8 páginas, formato SBC).

## Reprodutibilidade (Seção 7)

Fixe seeds (amostragem de busca, shuffling). O `corpus_hash` congelado deve ser
estável e registrado. Diversidade de fontes (≥3) é avaliada na Camada 1.
