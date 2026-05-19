[README.md](https://github.com/user-attachments/files/28014418/README.md)
# From Raw Detections to Real Intelligence

Pipeline de inteligência de retalho que transforma 250 015 deteções anónimas de visão computacional num relatório semanal estruturado e auditável, com IA local.

**Unidade Curricular:** Interação com Modelos de Larga Escala

---

## Visão Geral

Sensores de visão computacional em loja física produzem milhares de eventos demográficos anónimos por dia — `(zona, género, faixa etária, timestamp)` — sem qualquer `person_id` global. Este pipeline desanonimiza esse fluxo, reconstrói trajetórias individuais e produz um relatório operacional pronto para gestão.

**Regra de ouro:** o modelo de linguagem **nunca** acede aos dados brutos. Consome exclusivamente `metrics.json` (resumos analíticos consolidados). Esta barreira de abstração é a defesa primária contra alucinações numéricas.

Resultado típico em hardware comum: **\~5,5 segundos** para processar 7 dias de operação (≈ 45 000 eventos/s).

---

## Arquitetura

events.csv  ─►  src/stitcher.py    ─►  data/processed/journeys.csv

                  (O(N) via bucketing demográfico)

journeys.csv ─►  src/analytics.py  ─►  outputs/metrics.json

                  (Pandas vetorizado)

metrics.json ─►  src/insights.py   ─►  outputs/insights.json

                  (Ollama local · llama3.2:1b · JSON mode)

metrics.json \+ insights.json

             ─►  src/report.py     ─►  outputs/weekly\_report.md

                  (Jinja2)

journeys.csv \+ outputs/\*

             ─►  src/evaluate.py   ─►  outputs/quality\_report.json

                  (schema validation · grounding · reprodutibilidade)

Cada fase comunica estritamente via sistema de ficheiros — qualquer módulo pode ser executado, testado e inspecionado de forma isolada.

---

## Stack Tecnológico

- **Python** ≥ 3.11  
- **Ollama** (runtime local de LLMs), modelo `llama3.2:1b`  
- Bibliotecas principais (ver `requirements.txt`):

| Pacote | Versão | Função |
| :---- | :---- | :---- |
| `pandas` | 2.2.3 | Analítica vetorizada |
| `pyyaml` | 6.0.2 | Carregamento do `config.yaml` |
| `jinja2` | 3.1.4 | Renderização do relatório |
| `requests` | 2.32.3 | Cliente HTTP para Ollama |
| `pytest` | 8.3.3 | Testes automatizados |

---

## Instalação e Execução

### 1\. Clonar e preparar o ambiente

git clone \<url-do-repositorio\>

cd from-raw-detections-to-real-intelligence

python \-m venv .venv

source .venv/bin/activate          \# Linux/macOS

\# .venv\\Scripts\\activate           \# Windows

pip install \-r requirements.txt

### 2\. Arrancar o Ollama e descarregar o modelo

ollama serve &

ollama pull llama3.2:1b

### 3\. Correr o pipeline completo

python run\_pipeline.py

Os artefactos finais ficam em `outputs/`: `metrics.json`, `insights.json`, `weekly_report.md` e `quality_report.json`.

### 4\. Correr os testes

pytest tests/

### 5\. Estudo comparativo de prompts

Executa o módulo de insights com as três versões de prompt e compara os outputs:

for v in v1\_naive v2\_structured v3\_grounded; do

    python \-m src.insights \--prompt "$v"

done

---

## Configuração

Todos os limiares e parâmetros operacionais estão centralizados em `config.yaml`. Os valores críticos:

| Chave | Valor | Significado |
| :---- | :---- | :---- |
| `stitcher.max_gap_s` | `1800` | Tolerância máxima (30 min) entre eventos da mesma jornada. |
| `stitcher.max_journey_s` | `7200` | Fecho forçado de qualquer jornada ao fim de 120 min. |
| `llm.temperature` | `0.0` | Determinismo total — anula a criatividade do modelo. |

Estes valores são justificados em detalhe no Relatório Técnico (secções 3 e 4).

---

## Estrutura de Diretórios

.

├── config.yaml                \# Parâmetros centrais do pipeline

├── run\_pipeline.py            \# Orquestrador end-to-end

├── requirements.txt

│

├── data/

│   ├── raw/                   \# events.csv (input imutável)

│   └── processed/             \# journeys.csv (output do stitcher)

│

├── src/

│   ├── stitcher.py            \# Reconstrução de trajetórias (bucketing O(N))

│   ├── analytics.py           \# KPIs, segmentações, Z-score de anomalias

│   ├── insights.py            \# Cliente Ollama \+ JSON mode \+ fallback

│   ├── llm\_client.py          \# Wrapper HTTP para o Ollama

│   ├── report.py              \# Renderização Jinja2

│   ├── evaluate.py            \# Validação de schema, grounding e reprodutibilidade

│   └── utils.py               \# Carregamento de config, logging

│

├── prompts/

│   ├── v1\_naive.txt           \# Zero-shot básico

│   ├── v2\_structured.txt      \# Zero-shot com schema

│   └── v3\_grounded.txt        \# Few-shot ancorado (versão final)

│

├── templates/

│   └── weekly\_report.j2       \# Template Jinja2 do relatório

│

├── outputs/                   \# Artefactos gerados (gitignored)

│

├── tests/                     \# Suite pytest

│

└── notebooks/                 \# Exploração inicial (EDA, prototipagem)

---

## Garantias de Qualidade

- **Schema validation** — todas as chaves obrigatórias nos artefactos JSON são verificadas.  
- **Grounding** — qualquer métrica citada pelo LLM tem de existir literalmente em `metrics.json`.  
- **Reprodutibilidade** — re-execução do stitcher em diretório temporário compara hashes MD5; delta de linhas tem de ser 0\.  
- **Análise de sensibilidade** — `max_gap_s` é testado a ±20 % para medir o impacto na volumetria de jornadas.

---

## Limitações Conhecidas

1. **Rigidez paramétrica** — `max_gap_s` é único para toda a loja; secções grandes beneficiariam de janelas dinâmicas.  
2. **Atribuição gulosa** — o stitcher decide localmente, sem reconciliação retroativa. Em oclusões prolongadas pode fragmentar jornadas. Uma evolução natural seria Viterbi ou min-cost flow.

---

## Autor

**Pedro Pereira Rêgo** — nº 55221  
