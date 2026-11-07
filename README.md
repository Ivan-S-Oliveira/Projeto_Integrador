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
  projeto pelo notebook 01 (`get_parquet`) para
  `data/processed/dados-v2/srag.parquet`. Para repositório privado, defina
  `GITHUB_TOKEN` no `.env` (há um modelo em `.env.example`).
- Dados, modelos e saídas grandes não vão para o Git. Ficam versionados
  apenas os manifestos (`data/analytical/*.manifest.json` e
  `data/analytical/manifesto_*.json`) e o `.gitkeep` de cada pasta.
- Coorte definitiva publicada: 3.884.728 de 4.666.910 linhas da fonte
  (regras de exclusão em `docs/decisoes.md` §3).

## Fluxo

| Notebook | O que faz |
|---|---|
| `01_extracao` | Baixa o Parquet do GitHub e confere o arquivo. |
| `02_coorte_definitiva` | Aplica o contrato da coorte, publica a coorte e gera o artefato supervisionado + partição-mestre. |
| `03_eda_primeira_passagem` | Primeira análise exploratória e dicionário operacional. |
| `04_eda_temporal_agrupamento` | Análise temporal e agrupamento (K-Means, HCA). |
| `05_supervisionado_pilotos` | Pilotos com cinco famílias de modelos. |
| `06_pipeline_supervisionado` | Pré-processamento e pipeline. |
| `07_baseline_logistica` | Baseline e regressão logística. |
| `08_ablacoes_variaveis` | Ablações de variáveis. |
| `09_ajuste_fino` | Ajuste fino do Hist Gradient Boosting (gate G6). |
| `10_calibracao_limiar` | Calibração (G7) e limiar (G8) na validação. |
| `11_validacao_final` | Abre o teste uma única vez (G9): Teste A, Teste B e 2020–2022. |
| `12_pos_teste` | O/E, ECE, curva de decisão e equidade a partir das previsões salvas; **não** reabre o teste. |

## Estrutura

```text
configs/     supervised.yaml, final_cohort_v1.yaml, feature_contract_v1.json, dicionario_variaveis_v1.csv
data/        Parquet processado (dados-v2) e artefatos analíticos (coorte, dataset supervisionado, partição-mestre)
docs/        decisoes.md (resumo), dicionario_variaveis.md, limitacoes_e_rastreabilidade.md, historico/
notebooks/   fluxo de 01 a 12
resultados/  tabelas e figuras consolidadas (gerado no fechamento)
src/         config, dados, features, modelos, avaliacao, registro
outputs/     saídas das execuções (tabelas, previsões, runs); conteúdo grande fora do Git
```

## Como rodar

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Execute do 1 ao 12 individualmente
```

Rode os notebooks na ordem de 01 a 12. Os gates G1–G9 estão em
`configs/supervised.yaml`; cada notebook verifica o gate de que depende:

- `09_ajuste_fino` só faz a busca com **G6** aprovado.
- `10_calibracao_limiar` só calibra com **G7** e escolhe o limiar com **G8**
  aprovados.
- `11_validacao_final` só abre `test_ref` e `test_pandemic` com **G9**
  aprovado. Ao final, o gate vira `executado` e o manifesto registra
  `test_opened: true`.

O teste é aberto **uma única vez**. Para ensaiar o 11 sem abrir o teste, use
`SRAG_ENSAIO=1`; o ensaio não marca G9 e grava com prefixo `11_ensaio_`.

<!-- cadeia:inicio -->
Tempo e memoria (maquina oficial): a cadeia de notebooks 02 a 10 leva cerca de 14 min, com pico de 3.4 GB de memoria. Os notebooks 01 (download dos dados) e 11 (abertura unica do teste) ficam fora dessa execucao. Testado com Python 3.14.8; versoes exatas em `requirements-lock.txt`.
<!-- cadeia:fim -->

## Metodologia (resumo)

Partição determinística por grupo (`group_id`), seed 42, método
`hash_grupo_estratificado_mestre_v1`. Cada `group_id` aparece em um único
bloco; os testes ficam bloqueados no código até o gate G9.

| Bloco | Anos | Fração | Uso |
|---|---|---|---|
| `train_ref` | 2019, 2023–2025 | 70% | treino |
| `val_ref` | 2019, 2023–2025 | 15% | escolha de variáveis, hiperparâmetros, calibração e limiar |
| `test_ref` | 2019, 2023–2025 | 15% | Teste A (resultado principal) |
| `test_pandemic` | 2020–2022 | 100% | parte do Teste B |
| `exploracao` | 2026 | — | fora dos blocos principais (período parcial) |

Teste A = `test_ref`; Teste B = `test_ref` + `test_pandemic`. 2020–2022 é
sempre relatado em separado, ao lado do Teste B. A diferença A × B é lida
como **robustez temporal**, não como efeito causal da pandemia.

- Modelo final: Hist Gradient Boosting, 30 variáveis, sem peso de classe.
- Calibração `sigmoid` (gate G7) e limiar 0,1178 (gate G8) — maior precisão
  entre os cortes com recall ≥ 0,80. Ambos escolhidos só na validação
  (`val_cal`) e aplicados sem reajuste em `val_meas` e no teste.

Detalhes em `docs/decisoes.md`; o registro completo está em
`docs/historico/decisoes_completo.md`.

## Resultados

Validação (`val_ref`): PR-AUC 0,362, ROC-AUC 0,867, Brier 0,063.

Teste aberto **uma única vez** em 05/11/2026, com tudo congelado. Nada foi
reajustado depois; o limiar usado é o 0,1178 escolhido na validação.

| Janela | n | Óbitos | Prevalência | PR-AUC | PR-AUC ÷ prev. | ROC-AUC | Brier | Sens. | Prec. |
|---|---|---|---|---|---|---|---|---|---|
| **Teste A** (`test_ref`) | 119.245 | 10.065 | 8,4% | **0,369** | 4,37× | 0,869 | 0,0628 | 0,813 | 0,252 |
| 2020–2022 (`test_pandemic`) | 2.915.829 | 771.095 | 26,4% | 0,457 | 1,73× | 0,728 | 0,1835 | 0,792 | 0,379 |
| **Teste B** (`test_ref`+`test_pandemic`) | 3.035.074 | 781.160 | 25,7% | 0,454 | 1,77× | 0,735 | 0,1788 | 0,792 | 0,376 |

Teste A com intervalo de 95% por bootstrap de grupos (1000 réplicas):
PR-AUC 0,369 (0,359–0,379); ROC-AUC 0,869 (0,865–0,872); Brier 0,0628
(0,0618–0,0637).

As tabelas completas estão em `resultados/`.

## Limitações

- A ficha não registra a hora da saturação e do desconforto respiratório;
  ambos entraram no modelo (decisão de 03/11) por fazerem parte da
  definição de caso, mas a limitação temporal persiste.
- Variáveis, hiperparâmetros, calibração e limiar usam o mesmo bloco de
  validação (`val_ref`). A medida honesta é a do teste, aberto uma única
  vez.
- 2026 é parcial (dados até setembro, ~12% dos desfechos em aberto) e fica
  só como exploração. 2020–2022 têm prevalência muito maior (≈26% contra
  8,4%), o que explica o Brier pior e o O/E acima de 1 fora do domínio de
  desenvolvimento.
- Resultados descrevem desempenho preditivo, não causalidade; o modelo não
  é ferramenta de decisão clínica.

Ver `docs/limitacoes_e_rastreabilidade.md`.

## Autores

- **Ivan Schincariol Oliveira** — [LinkedIn](https://www.linkedin.com/in/ivan-s-oliveira-3608a92aa/)
- **Eduardo Hudson de Almeida Leite** — [LinkedIn](https://www.linkedin.com/in/eduardo-hudson-de-almeida-leite-71ab5a7b/)
- **Pedro Henrique Silva dos Santos** — [LinkedIn](https://www.linkedin.com/in/pedro-h-s-santos/)
- **Mateus da Silva Oliveira** — [LinkedIn](https://www.linkedin.com/in/mateusso)