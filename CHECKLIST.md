# CHECKLIST de Aderência — Trilha B (Agente de Conteúdo)

Para cada requisito, indique **onde** foi cumprido (arquivo, função ou seção do
relatório). O preenchimento é usado como guia na correção (Seção 6.7).

## Disciplina e escopo
- [x] Disciplina não-computacional da UFAM, área com ENADE, ementa pública — _onde:_ seção do relatório "Introdução"
- [x] Justificativa da escolha (material em PT, viabilidade, edição(ões) ENADE) no relatório — _onde:_ seção do relatório "Introdução"
- [x] Ementa oficial anexada em `data/ementa.txt` (texto selecionável, não escaneado) — _onde:_ arquivo data/ementa.txt

## Construtor de corpus (offline) — Camada 1
- [x] Parser de ementa (tópicos, conceitos, pré-requisitos, bibliografia) → `data/ementa_estruturada.json` — _onde:_ arquivo builder/parse_ementa.py
- [x] Planner com plano de coleta auditável → `data/plano_coleta.json` — _onde:_ arquivo builder/planner.py
- [x] Coletor com **≥3 fontes** distintas; log de execução persistido — _onde:_ arquivo builder/collector.py
- [x] Avaliador de fontes com heurística explícita (score + justificativa) — _onde:_ arquvio builder/evaluator.py
- [x] Deduplicador — _onde:_ arquivo builder/dedup.py
- [x] Indexador em vector store com metadados obrigatórios por chunk — _onde:_ arquivo indexer.py
- [x] Congelador: `corpus_hash` do índice e dos metadados → `data/corpus_meta.json` — _onde:_ arquivo freezer.py
- [ ] Memória da disciplina (cobertura, nº docs, qualidade média por tópico) — _onde:_

## Servidor MCP de conteúdo (read-only)
- [ ] `list_topics`, `corpus_query`, `get_chunk` conforme o contrato (Seção 3.1) — _onde:_
- [ ] Todos os metadados obrigatórios em cada chunk — _onde:_
- [ ] Erros estruturados (índice inválido, chunk inexistente, query malformada) sem propagar exceção — _onde:_
- [ ] Read-only: sem coleta/indexação/escrita; sem `web_search`/`fetch_page`/etc. — _onde:_
- [ ] `manifest.json` preenchido e validado por `check_contract` → `evaluation/contract/` — _onde:_

## Validação da Fase 1
- [ ] **Camada 1 — Qualidade da Construção** → `evaluation/construction/` (cobertura, diversidade, credibilidade, volume) — _onde:_
- [ ] Conexão do `tutor_mock` e sessão registrada → `evaluation/mock_integration/` — _onde:_

## Fase 2 — interoperabilidade
- [ ] Servidor disponibilizado aos **2 tutores** sorteados; suas suítes aplicadas — _onde:_
- [ ] Logs de chamadas, latência por tool, distribuição de queries por tópico, falhas — _onde:_
- [ ] Relatório de interoperabilidade → `evaluation/interop/` — _onde:_
- [ ] Análise de erros (3–5 casos) no relatório — _onde:_

## Reprodutibilidade (Seção 7)
- [ ] Seeds fixas (amostragem de busca, shuffling) — _onde:_
- [ ] `corpus_hash` estável e registrado — _onde:_

## Higiene do repositório (Seção 6.4)
- [ ] Conteúdo bruto e índice da vector store NÃO versionados — _onde:_
- [ ] Enunciados completos do ENADE NÃO versionados (apenas referência + link) — _onde:_

## Entregáveis gerais
- [ ] `README.md` com setup, execução e reprodução — _onde:_
- [ ] `requirements.txt` com versões fixadas — _onde:_
- [ ] `RELATORIO.pdf` na raiz (máx. 8 páginas, formato SBC, texto selecionável) — _onde:_

## Bônus de divulgação (Seção 5) — opcional
- [ ] **opt-in**: autorizo a inclusão do meu repositório no post coletivo da disciplina no Medium — **( ) sim   ( ) não**
  - Requisitos se "sim": repositório público só após as notas; licença permissiva (MIT/Apache-2.0); atribuição explícita; sem republicar enunciados completos do ENADE.
