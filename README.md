# Projeto Integrador — SRAG e Machine Learning

Projeto acadêmico do **Projeto Integrador I da Pós-Graduação em Inteligência
Artificial**. Estima o risco de óbito por SRAG no momento da internação
hospitalar, com dados públicos do SIVEP-Gripe (2019–2026).

O projeto é acadêmico e exploratório. Não é um sistema clínico validado e não
permite conclusões causais.

## Pergunta

Com as informações disponíveis na admissão, qual é a probabilidade de óbito
por SRAG? O alvo é `evolucao = 2` (óbito por SRAG) contra `evolucao = 1`
(cura).

## Dados

- Fonte: Ministério da Saúde, base SRAG 2019–2026
  (<https://apidadosabertos.saude.gov.br/vigilancia-e-meio-ambiente/srag-2019-2026>).
- O Parquet `dados-v2/srag.parquet` é baixado da release do GitHub do
  projeto pelo notebook 01 (`get_parquet`). Para repositório privado,
  defina `GITHUB_TOKEN` no `.env`.
- Dados, modelos e saídas grandes não vão para o Git.

## Fluxo

| Notebook | O que faz |
|---|---|
| `01_extracao` | Baixa o Parquet do GitHub e confere o arquivo. |
| `02_coorte_definitiva` | Aplica o contrato da coorte, publica a coorte e gera a partição. |
| `03_eda_primeira_passagem` | Primeira análise exploratória. |
| `04_eda_temporal_agrupamento` | Análise temporal e agrupamento (K-Means, HCA). |
| `05_supervisionado_pilotos` | Pilotos com cinco famílias de modelos. |
| `06_pipeline_supervisionado` | Pré-processamento e pipeline. |
| `07_baseline_logistica` | Baseline e regressão logística. |
| `08_ablacoes_variaveis` | Ablações de variáveis. |
| `09_ajuste_fino` | Ajuste fino do Hist Gradient Boosting. |
| `10_calibracao_limiar` | Calibração e limiar na validação. |
| `11_validacao_final` | Abre o teste uma única vez (Teste A, Teste B e 2020–2022). |

## Estrutura

```text
configs/     supervised.yaml, contrato da coorte e contrato de variáveis
docs/        decisoes.md (resumo) e historico/
notebooks/   fluxo de 01 a 11
src/         config, dados, features, modelos, avaliacao, registro
tests/       testes do protocolo (pytest)
```

## Como rodar

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -e .
python -m pytest
```

Rode os notebooks na ordem. O 11 só abre o teste depois da aprovação do gate
G9 em `configs/supervised.yaml`. Para ensaiar o 11 sem abrir o teste, use
`SRAG_ENSAIO=1`.

<!-- cadeia:inicio -->
Tempo e memoria (maquina oficial): a cadeia de notebooks 02 a 10 leva cerca de 14 min, com pico de 3.4 GB de memoria. Os notebooks 01 (download dos dados) e 11 (abertura unica do teste) ficam fora dessa execucao. Testado com Python 3.14.8; versoes exatas em `requirements-lock.txt`.
<!-- cadeia:fim -->

## Metodologia (resumo)

- Partição por grupo (`group_id`), seed 42: `train_ref` 70%, `val_ref` 15% e
  `test_ref` 15% em 2019 e 2023–2025; 2020–2022 em `test_pandemic`; 2026 fica
  só para exploração.
- Modelo final: Hist Gradient Boosting, 30 variáveis, sem peso de classe.
- Calibração `sigmoid` e limiar 0,1178 (maior precisão com recall ≥ 0,80),
  escolhidos só na validação.
- Teste A = `test_ref`; Teste B = `test_ref` + `test_pandemic`.

Detalhes em `docs/decisoes.md`.

## Resultados

Validação (`val_ref`): PR-AUC 0,362, ROC-AUC 0,867, Brier 0,063. Os
resultados do teste ficam no relatório final, depois da abertura única.

## Limitações

- A ficha não registra a hora da saturação e do desconforto respiratório.
- Variáveis, hiperparâmetros, calibração e limiar usam o mesmo bloco de
  validação.
- 2026 é parcial; 2020–2022 têm prevalência muito maior (≈26% contra 8,4%).
- Resultados descrevem desempenho preditivo, não causalidade.

## Autores

- **Ivan Schincariol Oliveira** — [LinkedIn](https://www.linkedin.com/in/ivan-s-oliveira-3608a92aa/)
- **Eduardo Hudson de Almeida Leite** — [LinkedIn](https://www.linkedin.com/in/eduardo-hudson-de-almeida-leite-71ab5a7b/)
- **Pedro Henrique Silva dos Santos** — [LinkedIn](https://www.linkedin.com/in/pedro-h-s-santos/)
- **Mateus da Silva Oliveira** — [LinkedIn](https://www.linkedin.com/in/mateusso)
