# Project Complete Reference

> **Generated file. Do not edit manually.**  
> Update with `tools/update_project_reference.py`.

## 1. Project context

This is an academic retrospective machine-learning project using SRAG/SIVEP-Gripe data. The operational objective is to estimate risk of death from SRAG using only information plausibly available by hospital admission. The unit of analysis is an eligible notification used as a proxy for a hospital episode, not automatically a unique person.

The repository already contains reusable foundations for configuration, environment handling, Parquet access, basic preprocessing, target construction, preprocessing pipelines, baseline, logistic regression, gradient boosting, probability calibration, threshold selection, classification metrics, calibration diagnostics, error analysis, temporal validation, protected holdout access, experiment registration and automated tests.

## 2. Non-negotiable methodological rules

- Academic retrospective analysis, not a clinically validated decision tool.
- Do not make causal claims from predictive associations.
- Prediction time is hospital admission. Later information cannot be a feature.
- Current target contract: `evolucao == 2.0` is positive; `evolucao == 1.0` is negative; other values stay outside the primary binary target unless formally changed.
- Never use the final holdout to choose model, hyperparameters, calibration or threshold.
- Preserve temporal ordering. Do not silently replace temporal validation with random splitting.
- Data, trained models, outputs, local paths, `.env` and secrets do not belong in Git.
- Changes to cohort, target, features, split, seed, calibration, threshold or gates must update configuration, tests and documentation together.

## 3. Ways of working

1. Read this document before proposing code.
2. Search the API catalog and complete source sections before creating a function.
3. Notebooks orchestrate, explain and visualize. Reusable logic belongs in `src/`.
4. Experimental decisions belong in `configs/`.
5. Use `src/utils/storage.py` for the official Parquet contract.
6. Use `src/evaluation/temporal.py::TemporalSplit` for the final three-way workflow.
7. Reuse metrics and error analysis from `src/evaluation/`.
8. Use `src/utils/reproducibility.py::Run` instead of creating another logger.
9. A new public function requires an uncovered gap, typing, docstring and tests.
10. Review `git diff` and run relevant tests before integration.

## 4. Source precedence

1. Executable code and tests describe actual behavior.
2. `configs/supervised.yaml` describes approved or pending decisions and gates.
3. This generated reference combines the current codebase.
4. Older plans describe intent, not necessarily implementation.

## 5. Status labels

- **Implemented:** executable code exists.
- **Configured:** a value or rule exists in configuration.
- **Planned:** described but not confirmed in executable code.
- **Placeholder:** intentionally empty file reserved for later work.
- **Attention:** overlap, pending decision or technical risk.


## 6. Current snapshot

- Generated UTC: `2026-10-08T20:10:19.980994+00:00`
- Branch: `mateus/eda-inicial`
- Commit: `2742f09479303d7d55c5958aca1433c762bcd786`
- Included tracked files: `35`

### Git status

```text
clean working tree
```

## 7. Included file list

- `configs/supervised.yaml`
- `notebooks/00_acesso_dados_parquet.ipynb`
- `notebooks/01_extracao.ipynb`
- `notebooks/02_analise_exploratoria.ipynb`
- `notebooks/02_eda/01_eda_primeira_passagem.ipynb`
- `notebooks/03_preprocessamento.ipynb`
- `notebooks/04_feature_engineering.ipynb`
- `notebooks/05_treinamento.ipynb`
- `notebooks/06_avaliacao.ipynb`
- `notebooks/C/C1_smoke_test.ipynb`
- `pyproject.toml`
- `pytest.ini`
- `README.md`
- `requirements.txt`
- `src/__init__.py`
- `src/evaluation/__init__.py`
- `src/evaluation/calibration.py`
- `src/evaluation/errors.py`
- `src/evaluation/metrics.py`
- `src/evaluation/temporal.py`
- `src/features/__init__.py`
- `src/features/engenharia_features.py`
- `src/utils/__init__.py`
- `src/utils/config.py`
- `src/utils/env.py`
- `src/utils/reproducibility.py`
- `src/utils/storage.py`
- `tests/conftest.py`
- `tests/test_config.py`
- `tests/test_leakage.py`
- `tests/test_pipeline.py`
- `tests/test_reproducibility.py`
- `tests/test_smoke.py`
- `tools/collect_repo_context.py`
- `tools/update_project_reference.py`

## 8. Environment variables referenced

- `CI`: `src/utils/env.py`, `src/utils/reproducibility.py`
- `GITHUB_ACTIONS`: `src/utils/env.py`, `src/utils/reproducibility.py`
- `GITHUB_TOKEN`: `src/utils/config.py`, `src/utils/env.py`, `src/utils/storage.py`
- `SRAG_PARQUET_URL`: `src/utils/config.py`

Only names are documented. Secret values must never appear here.

## 9. Python API catalog

Generated statically with Python AST. Project modules are not imported or executed. Missing docstrings are marked explicitly.

### `src/__init__.py`

- No top-level functions or classes detected.

### `src/evaluation/__init__.py`

Avaliação: splits temporais, métricas, calibração e análise de erros.

- No top-level functions or classes detected.

### `src/evaluation/calibration.py`

Avaliação de calibração de probabilidades.

Complementa `src/models/calibration.py`:

    src/models/calibration.py      → AJUSTA a calibração
    src/evaluation/calibration.py  → MEDE a qualidade da calibração

Métricas implementadas
----------------------
- Curva de confiabilidade (reliability diagram)
- ECE  (Expected Calibration Error)
- MCE  (Maximum Calibration Error)
- Decomposição de Brier em Reliability + Resolution − Uncertainty
  (Murphy, 1973)

#### `def curva_confiabilidade(y_true: ArrayLike, y_prob: ArrayLike, n_bins: int=10) -> pd.DataFrame`
- Source line: `34`
Dados para o reliability diagram.

Colunas:
    bin_centro    — probabilidade média prevista no bin
    freq_positiva — fração real de positivos no bin
    n             — número de amostras no bin
    gap           — |freq_positiva - bin_centro|

#### `def ece(y_true: ArrayLike, y_prob: ArrayLike, n_bins: int=10) -> float`
- Source line: `82`
Expected Calibration Error — média ponderada dos gaps por bin.

#### `def mce(y_true: ArrayLike, y_prob: ArrayLike, n_bins: int=10) -> float`
- Source line: `97`
Maximum Calibration Error — o pior gap entre os bins.

#### `def brier_decomposicao(y_true: ArrayLike, y_prob: ArrayLike, n_bins: int=10) -> dict[str, float]`
- Source line: `114`
Decompõe o Brier score (Murphy, 1973):

    Brier = Reliability − Resolution + Uncertainty

Retorna
-------
dict com:
    brier         — Brier score observado
    reliability   — quanto menor, melhor (penaliza desvios locais)
    resolution    — quanto maior, melhor (capacidade de separar)
    uncertainty   — entropia binária da base (fixa para o dataset)
    n             — número de amostras

### `src/evaluation/errors.py`

Análise de erros: quem o modelo erra, por quanto, e em quais grupos.

Ferramentas
-----------
- `matriz_confusao`           → TP/FP/FN/TN em DataFrame
- `extrair_falsos_positivos`  → subconjunto do df com FP
- `extrair_falsos_negativos`  → subconjunto do df com FN
- `metricas_por_grupo`        → métricas por categoria de uma coluna
- `top_erros`                 → os N piores erros por confiança

#### `def matriz_confusao(y_true: ArrayLike, y_pred: ArrayLike) -> pd.DataFrame`
- Source line: `38`
Matriz de confusão 2×2 como DataFrame.

Colunas: ["pred_0", "pred_1"], índice: ["real_0", "real_1"].
Adiciona linha/coluna "total" para conveniência.

#### `def extrair_falsos_positivos(df: pd.DataFrame, y_true: ArrayLike, y_pred: ArrayLike) -> pd.DataFrame`
- Source line: `70`
Retorna as linhas de `df` onde o modelo previu 1 mas o real é 0.

#### `def extrair_falsos_negativos(df: pd.DataFrame, y_true: ArrayLike, y_pred: ArrayLike) -> pd.DataFrame`
- Source line: `82`
Retorna as linhas de `df` onde o modelo previu 0 mas o real é 1.

#### `def metricas_por_grupo(df: pd.DataFrame, y_true: ArrayLike, y_prob: ArrayLike, coluna_grupo: str, *, limiar: float=0.5, min_n: int=30) -> pd.DataFrame`
- Source line: `98`
Métricas por categoria de `coluna_grupo` (ex.: "sg_uf", "cs_sexo").

Ignora grupos com menos de `min_n` amostras (evita métricas instáveis).

Colunas: grupo, n, positivos, auc, f1, precision, recall.

#### `def top_erros(df: pd.DataFrame, y_true: ArrayLike, y_prob: ArrayLike, *, n: int=20, criterio: CriterioTop='erro_absoluto', limiar: float=0.5) -> pd.DataFrame`
- Source line: `163`
Retorna as N linhas de `df` com os piores erros.

Parâmetros
----------
criterio : {"fp", "fn", "erro_absoluto"}
    - "fp"            → ordena por prob decrescente entre FP
    - "fn"            → ordena por prob crescente entre FN
    - "erro_absoluto" → ordena por |prob − y| decrescente (todos os erros)

Adiciona colunas: `y_true`, `y_prob`, `y_pred`, `erro_abs`.

### `src/evaluation/metrics.py`

Métricas de classificação binária — todas retornam `float`.

Motivo: o scikit-learn retorna `Float | ndarray` para várias métricas,
o que faz o Pylance reclamar. Aqui a gente encapsula e garante `float`.

Também oferece:
    - `metricas_por_limiar` → tabela varrendo limiares
    - `ic_bootstrap`        → intervalo de confiança por bootstrap

#### `def _to_np(x: ArrayLike) -> np.ndarray`
- Source line: `36`
- **Missing docstring**

#### `def _to_int_labels(y: ArrayLike) -> np.ndarray`
- Source line: `40`
- **Missing docstring**

#### `def auc(y_true: ArrayLike, y_prob: ArrayLike) -> float`
- Source line: `48`
- **Missing docstring**

#### `def average_precision(y_true: ArrayLike, y_prob: ArrayLike) -> float`
- Source line: `52`
- **Missing docstring**

#### `def brier(y_true: ArrayLike, y_prob: ArrayLike) -> float`
- Source line: `56`
- **Missing docstring**

#### `def f1(y_true: ArrayLike, y_pred: ArrayLike) -> float`
- Source line: `60`
- **Missing docstring**

#### `def precision(y_true: ArrayLike, y_pred: ArrayLike) -> float`
- Source line: `64`
- **Missing docstring**

#### `def recall(y_true: ArrayLike, y_pred: ArrayLike) -> float`
- Source line: `68`
- **Missing docstring**

#### `def accuracy(y_true: ArrayLike, y_pred: ArrayLike) -> float`
- Source line: `72`
- **Missing docstring**

#### `def metricas_completas(y_true: ArrayLike, y_prob: ArrayLike, limiar: float=0.5) -> dict[str, float]`
- Source line: `80`
Retorna um dict com AUC, AP, Brier, F1, precision, recall e accuracy.
Pronto para `Run.metrica(**d)`.

#### `def metricas_por_limiar(y_true: ArrayLike, y_prob: ArrayLike, n_limiares: int=101) -> pd.DataFrame`
- Source line: `118`
Tabela com métricas para cada limiar em [0.01, 0.99].

Colunas: limiar, f1, precision, recall, accuracy.

#### `def ic_bootstrap(y_true: ArrayLike, y_prob: ArrayLike, *, metrica: Callable[[ArrayLike, ArrayLike], float]=auc, n_boot: int=200, alpha: float=0.05, seed: int=42) -> tuple[float, float, float]`
- Source line: `149`
Intervalo de confiança via bootstrap percentil.

Retorna (estimativa, limite_inferior, limite_superior).

Parâmetros
----------
metrica : callable(y_true, y_prob) -> float
    Função de métrica. Default: `auc`.
n_boot : int
    Número de reamostragens.
alpha : float
    Nível de significância (0.05 → IC 95%).
seed : int
    Semente para reprodutibilidade.

### `src/evaluation/temporal.py`

Split temporal em três blocos + trava do holdout.

Regra de ouro:
    ┌──────────────┬──────────────┬──────────────────┐
    │   treino     │  validação   │     holdout      │
    └──────────────┴──────────────┴──────────────────┘
     mais antigo ───────────────────────► mais recente

    - `treino` + `validação` → escolha de modelo, hiperparâmetros, limiar
    - `holdout`               → UMA ÚNICA vez, no fim, após `concluir_selecao()`

A classe `TemporalSplit` bloqueia o acesso ao holdout enquanto a seleção
não for explicitamente marcada como concluída. Isso impede o erro clássico
de "espionar" o holdout durante a fase de modelagem.

#### `def split_temporal_3way(df: pd.DataFrame, coluna_tempo: str, frac_treino: float=0.7, frac_validacao: float=0.15) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]`
- Source line: `29`
Split temporal em treino / validação / holdout, **sem embaralhar**.

Parâmetros
----------
df : pd.DataFrame
    Base completa.
coluna_tempo : str
    Coluna usada para ordenar (ex.: "dt_notific").
frac_treino, frac_validacao : float
    Frações do total. `frac_holdout = 1 - frac_treino - frac_validacao`.

Retorno
-------
(treino, validacao, holdout) : tuple de DataFrames

Garantias
---------
    max(treino[coluna_tempo]) <= min(validacao[coluna_tempo])
    max(validacao[coluna_tempo]) <= min(holdout[coluna_tempo])

#### `class TemporalSplit`
- Source line: `93`
Guarda os três blocos e controla o acesso ao holdout.

Uso típico
----------
    split = TemporalSplit(df, coluna_tempo="dt_notific")

    # Fase 1 — escolha de modelo (SOMENTE treino + validação)
    tr, va = split.treino_validacao()
    modelo = ...
    modelo.fit(tr[FEATURES], y_tr)

    # Ao terminar a seleção:
    split.concluir_selecao()

    # Fase 2 — avaliação final, UMA única vez
    ho = split.holdout()
    y_prob = modelo.predict_proba(ho[FEATURES])[:, 1]

Atributos
---------
n_treino, n_validacao, n_holdout : int
    Tamanhos de cada bloco (útil para logging).

##### `def __post_init__(self) -> None`
- **Missing method docstring**

##### `def treino_validacao(self) -> tuple[pd.DataFrame, pd.DataFrame]`
Retorna (treino, validação).

Este é o único caminho para treinar e comparar modelos durante a
fase de seleção. O holdout NÃO é exposto aqui.

##### `def treino(self) -> pd.DataFrame`
- **Missing method docstring**

##### `def validacao(self) -> pd.DataFrame`
- **Missing method docstring**

##### `def concluir_selecao(self) -> None`
Marca a fase de seleção como encerrada e libera o holdout.

Deve ser chamada **uma única vez**, depois que o modelo final foi
escolhido, o limiar foi definido e a calibração foi ajustada.

##### `def holdout_liberado(self) -> bool`
- **Missing method docstring**

##### `def holdout(self) -> pd.DataFrame`
Retorna o bloco de holdout.

Levanta `RuntimeError` se `concluir_selecao()` ainda não foi
chamada. Isso impede que o holdout seja consultado durante a
escolha de modelo.

##### `def n_treino(self) -> int`
- **Missing method docstring**

##### `def n_validacao(self) -> int`
- **Missing method docstring**

##### `def n_holdout(self) -> int`
- **Missing method docstring**

##### `def resumo(self) -> str`
Resumo legível do split — bom para log no `Run`.

### `src/features/__init__.py`

- No top-level functions or classes detected.

### `src/features/engenharia_features.py`

- No top-level functions or classes detected.

### `src/utils/__init__.py`

- No top-level functions or classes detected.

### `src/utils/config.py`

Configurações centralizadas do Projeto Integrador.

Regras deste módulo:
- NÃO usar caminhos pessoais (C:/Users/... , /home/fulano/...).
- NÃO usar caminhos absolutos externos ao projeto.
- Todos os caminhos derivam de ROOT_DIR, calculado a partir deste arquivo.
- Segredos e URLs sensíveis são lidos LAZILY (função), nunca no import —
  porque o `.env` é carregado por `env.carregar_dotenv()` depois.
- O YAML de configuração (`configs/supervised.yaml`) também é lido LAZILY
  e cacheado, pelo mesmo motivo.

#### `def github_token() -> str | None`
- Source line: `83`
Token do GitHub — lido a cada chamada (permite .env tardio).

#### `def srag_parquet_url() -> str`
- Source line: `88`
URL do Parquet do SRAG 2019–2026.

Override via variável de ambiente `SRAG_PARQUET_URL`.
O link do Parquet muda semanalmente — atualize em:
  https://dadosabertos.saude.gov.br/dataset/srag-2019-a-2026

#### `def _interpolar_env(texto: str) -> str`
- Source line: `112`
Substitui `${VAR}` pelo valor de os.environ (vazio se ausente).

#### `def carregar_supervised() -> dict[str, Any]`
- Source line: `118`
Lê `configs/supervised.yaml` de forma lazy e cacheada.

Regras:
- Import de `yaml` é local (dependência opcional em tempo de import).
- Se o arquivo não existir, levanta FileNotFoundError com instrução.
- Suporta `${VAR}` interpolado a partir do ambiente.
- O resultado é cacheado — para recarregar após editar o YAML, chame
  `carregar_supervised.cache_clear()`.

#### `def supervised_yaml_sha256() -> str | None`
- Source line: `154`
SHA-256 do YAML atual (ou None se não existir).
Útil para gravar em `metadata.json` e garantir reprodutibilidade.

#### `class GatePendenteError`
- Source line: `203`
Levantado quando se tenta usar um valor que depende de gate não aprovado.

#### `def cfg(*chaves: str, default: Any=None) -> Any`
- Source line: `207`
Acessa uma chave aninhada do supervised.yaml.

    cfg("target", "coluna")          -> "evolucao"
    cfg("models", "logistic", "C")   -> None (TBD)

#### `def exigir_valor(valor: Any, *, caminho: str, gate: str) -> Any`
- Source line: `222`
Garante que `valor` não é None nem 'TBD'. Se for, levanta erro
apontando o gate que precisa ser aprovado antes.

#### `def gate_aprovado(nome_gate: str) -> bool`
- Source line: `235`
Retorna True se o gate existe e está com status 'aprovado'.

#### `def exigir_gate(nome_gate: str) -> None`
- Source line: `241`
Levanta GatePendenteError se o gate ainda não foi aprovado.

#### `def features_finais() -> list[str]`
- Source line: `251`
Retorna a lista final de features.
Se `features.final` for null, usa numericas + categoricas.

#### `def limiar_ativo() -> float`
- Source line: `263`
Retorna o limiar operacional.
Só usa `otimo` se o gate G7 estiver aprovado; caso contrário, `default`.

#### `def _status(valor: object) -> str`
- Source line: `277`
- **Missing docstring**

#### `def resumo() -> str`
- Source line: `281`
Retorna um resumo legível das configurações ativas.

### `src/utils/env.py`

Carregamento de variáveis de ambiente e segredos do projeto.

Fluxo:
    .env  →  os.environ  →  config.py  →  restante do projeto

Regras:
- O arquivo .env NUNCA vai para o Git (ver .gitignore).
- Use .env.example como template versionado.
- Não há dependência de Colab, Kaggle ou qualquer ambiente específico.
- Em CI/CD ou produção, defina as variáveis diretamente no ambiente;
  o .env é opcional e serve apenas para desenvolvimento local.

#### `def garantir_diretorios() -> None`
- Source line: `35`
Cria os diretórios padrão do projeto, se ainda não existirem.

#### `def carregar_dotenv(caminho: Path | None=None) -> bool`
- Source line: `47`
Carrega o arquivo .env da raiz do projeto (ou o caminho informado).

Retorna True se o arquivo foi encontrado e carregado, False caso contrário.
Não sobrescreve variáveis já definidas no ambiente (override=False).

#### `def detectar_ambiente() -> str`
- Source line: `71`
Retorna 'ci' se estiver em pipeline, senão 'local'.

Não é mais usado para escolher fonte de segredos — apenas para logs.

#### `def get_env(nome: str, default: str | None=None) -> str | None`
- Source line: `88`
Lê uma variável de ambiente, com default opcional.

#### `def get_secret(nome: str, obrigatorio: bool=True) -> str | None`
- Source line: `93`
Lê um segredo/variável sensível do ambiente.

Parâmetros
----------
nome : str
    Nome da variável (ex.: 'GITHUB_TOKEN').
obrigatorio : bool
    Se True (padrão) e a variável não existir, levanta RuntimeError
    com mensagem explicativa. Se False, retorna None.

Uso
---
>>> token = get_secret("GITHUB_TOKEN", obrigatorio=False)
>>> if token: ...

#### `def resumo() -> str`
- Source line: `132`
Resumo legível do estado do ambiente.

### `src/utils/reproducibility.py`

Registro de execuções para reprodutibilidade (critério C1).

Cada execução gera `outputs/runs/<RUN_ID>/` com:
    metadata.json   ← tudo estruturado
    summary.txt     ← versão legível

Uso:
    from src.utils.reproducibility import Run

    with Run(modelo="logistic", parametros={"C": 1.0}) as r:
        ... treino ...
        r.metrica(auc=0.82, accuracy=0.78)
        r.anotar("split temporal por dt_notific")

#### `def gerar_run_id(modelo: str | None=None, base_dir: Path | None=None) -> str`
- Source line: `41`
Gera um identificador unico para uma execucao.

O uso de microssegundos reduz o risco de duas execucoes
receberem o mesmo identificador.

#### `def _agora() -> dict[str, str]`
- Source line: `83`
- **Missing docstring**

#### `def _resumo(meta: dict[str, Any]) -> str`
- Source line: `91`
summary.txt curto e legível.

#### `def _versoes() -> dict[str, str | None]`
- Source line: `126`
Retorna as versoes fundamentais da execucao.

#### `def _git_info() -> dict[str, str | bool | None]`
- Source line: `155`
Retorna commit, branch e estado da arvore de trabalho.

#### `def _env_info() -> dict[str, str | bool]`
- Source line: `200`
Retorna informacoes nao sensiveis do ambiente.

#### `def registrar_execucao(modelo: str, *, seed: int | None=None, parametros: dict[str, Any] | None=None, dataset: dict[str, Any] | None=None, features: dict[str, Any] | None=None, metricas: dict[str, Any] | None=None, duracao_s: float | None=None, notas: str | None=None, run_id: str | None=None, output_dir: Path | None=None) -> Path`
- Source line: `221`
Grava metadata.json + summary.txt em outputs/runs/<RUN_ID>/.

#### `def listar_runs(output_dir: Path | None=None) -> list[dict[str, Any]]`
- Source line: `286`
Lista os metadados das execucoes registradas.

Cada item retornado corresponde ao conteudo de um
metadata.json e inclui tambem o caminho da pasta.

#### `def carregar_run(run: str | Path, output_dir: Path | None=None) -> dict[str, Any]`
- Source line: `342`
Carrega o metadata.json de uma execucao.

#### `class Run`
- Source line: `379`
with Run(modelo="logistic", parametros={"C": 1.0}) as r: ...

##### `def __init__(self, modelo: str, *, seed: int | None=None, parametros: dict[str, Any] | None=None, dataset: dict[str, Any] | None=None, features: dict[str, Any] | None=None, notas: str | None=None, output_dir: Path | None=None) -> None`
- **Missing method docstring**

##### `def metrica(self, **kwargs: Any) -> 'Run'`
- **Missing method docstring**

##### `def anotar(self, texto: str) -> 'Run'`
- **Missing method docstring**

##### `def add_dataset(self, **kwargs: Any) -> 'Run'`
- **Missing method docstring**

##### `def __enter__(self) -> 'Run'`
- **Missing method docstring**

##### `def __exit__(self, exc_type, exc, tb) -> bool`
- **Missing method docstring**

### `src/utils/storage.py`

#### `def _token()`
- Source line: `13`
- **Missing docstring**

#### `def _download(url, dest, headers=None, expected_magic=None)`
- Source line: `20`
- **Missing docstring**

#### `def _private_asset_url(token)`
- Source line: `74`
- **Missing docstring**

#### `def get_parquet(force=False)`
- Source line: `100`
- **Missing docstring**

#### `def read_srag(columns=None, filters=None)`
- Source line: `145`
- **Missing docstring**

### `tests/conftest.py`

Fixtures compartilhadas e marcação de testes.

Marcadores:
    slow  → testes que fazem I/O pesado (download/leitura do Parquet completo)
    net   → testes que exigem acesso à internet

Uso:
    pytest                       # só testes rápidos
    pytest -m slow               # só testes lentos
    pytest -m "not slow"         # idem ao primeiro
    pytest -m "slow and net"     # testes lentos que precisam de rede

#### `def pytest_configure(config)`
- Source line: `27`
- **Missing docstring**

#### `def root_dir() -> Path`
- Source line: `37`
- **Missing docstring**

#### `def processed_dir() -> Path`
- Source line: `42`
- **Missing docstring**

#### `def parquet_disponivel() -> Path | None`
- Source line: `47`
Retorna o primeiro Parquet de SRAG encontrado, ou None.

Ordem de preferência:
    1) data/processed/dados-v1/srag.parquet   (release oficial)
    2) data/processed/srag_amostra.parquet    (extração local)
    3) data/raw/*.parquet                     (baixado por extracao.py)

### `tests/test_config.py`

Verifica que o ambiente e a configuracao estao integros.

Estes testes sao rapidos e nao fazem I/O pesado.
Devem rodar em toda validacao local e em CI.

#### `def test_root_dir_existe()`
- Source line: `17`
- **Missing docstring**

#### `def test_root_dir_calculado_a_partir_do_arquivo()`
- Source line: `22`
- **Missing docstring**

#### `def test_diretorios_derivam_da_raiz(chave)`
- Source line: `38`
Os diretorios do projeto devem derivar de ROOT_DIR.

O caminho absoluto pode conter C:/Users ou OneDrive porque
esse pode ser o local real do clone. O que nao pode existir
e um caminho pessoal gravado diretamente em config.py.

#### `def test_config_nao_contem_caminho_pessoal_hardcoded()`
- Source line: `60`
Examina somente atribuicoes de constantes relacionadas
a caminhos.

Comentarios, docstrings e mensagens explicativas podem
mencionar exemplos como C:/Users ou /home sem representar
uma configuracao real do projeto.

#### `def test_seed_definido()`
- Source line: `170`
- **Missing docstring**

#### `def test_random_state_igual_ao_seed()`
- Source line: `175`
- **Missing docstring**

#### `def test_repo_e_data_version_definidos()`
- Source line: `179`
- **Missing docstring**

#### `def test_srag_parquet_url_nao_vazia()`
- Source line: `186`
- **Missing docstring**

#### `def test_parametros_http_razoaveis()`
- Source line: `194`
- **Missing docstring**

#### `def test_env_aponta_para_mesma_raiz()`
- Source line: `200`
- **Missing docstring**

#### `def test_env_diretorios_padrao_existem()`
- Source line: `204`
- **Missing docstring**

#### `def test_env_resumo_nao_quebra()`
- Source line: `225`
- **Missing docstring**

#### `def test_get_secret_obrigatorio_levanta_erro(monkeypatch)`
- Source line: `232`
- **Missing docstring**

#### `def test_get_secret_opcional_retorna_none(monkeypatch)`
- Source line: `249`
- **Missing docstring**

### `tests/test_leakage.py`

Testes anti-vazamento de dados.

Os testes protegem contra:
- inclusao do alvo no conjunto de features;
- inclusao de colunas posteriores ao desfecho;
- quebra da ordem temporal entre treino, validacao e holdout;
- duplicacao de identificadores quando houver uma chave adequada.

#### `def test_config_features_proibidas_definidas()`
- Source line: `29`
- **Missing docstring**

#### `def test_pipeline_expoe_features_sem_alvo()`
- Source line: `47`
- **Missing docstring**

#### `def test_pipeline_nao_inclui_coluna_alvo()`
- Source line: `65`
- **Missing docstring**

#### `def test_split_temporal_3way_respeita_ordem()`
- Source line: `73`
- **Missing docstring**

#### `def test_temporal_split_bloqueia_holdout()`
- Source line: `113`
- **Missing docstring**

#### `def test_dataset_sem_identificadores_duplicados(parquet_disponivel)`
- Source line: `145`
Testa duplicidade somente se houver uma coluna que possa
funcionar como identificador da notificacao.

UF e data nao formam uma chave unica e nao devem ser usadas
isoladamente para declarar duplicacao de registros.

### `tests/test_pipeline.py`

Testes do pipeline de ingestão: extracao.py, read_srag, csv_to_parquet.

Marcados como `slow` porque tocam arquivos grandes.

#### `def test_read_srag_retorna_dataframe(parquet_disponivel)`
- Source line: `26`
Valida o caminho oficial de leitura local do projeto.

#### `def test_get_parquet_reaproveita_arquivo(parquet_disponivel)`
- Source line: `61`
get_parquet com force igual a False deve reutilizar
o arquivo existente.

#### `def test_csv_to_parquet_round_trip(tmp_path)`
- Source line: `107`
CSV pequeno → Parquet → lê de volta e confere.

#### `def test_csv_to_parquet_erro_quando_csv_inexistente(tmp_path)`
- Source line: `131`
- **Missing docstring**

#### `def test_raw_dir_foi_criado()`
- Source line: `145`
- **Missing docstring**

#### `def test_processed_dir_foi_criado()`
- Source line: `152`
- **Missing docstring**

### `tests/test_reproducibility.py`

Testes do registro de execuções.

#### `def test_registrar_execucao_cria_pasta(tmp_path)`
- Source line: `11`
- **Missing docstring**

#### `def test_metadata_tem_campos_obrigatorios(tmp_path)`
- Source line: `26`
- **Missing docstring**

#### `def test_run_context_manager(tmp_path)`
- Source line: `46`
- **Missing docstring**

#### `def test_run_id_unico(tmp_path)`
- Source line: `58`
- **Missing docstring**

#### `def test_listar_e_carregar(tmp_path)`
- Source line: `65`
- **Missing docstring**

#### `def test_seed_padrao_vem_do_config(tmp_path)`
- Source line: `76`
- **Missing docstring**

### `tests/test_smoke.py`

Smoke tests: o dataset existe, abre, tem colunas e registros?

Todos os testes de I/O estão marcados como `slow`.
Rode com:  pytest -m slow

#### `def test_parquet_existe(parquet_disponivel)`
- Source line: `21`
- **Missing docstring**

#### `def test_parquet_tem_magic_bytes(parquet_disponivel)`
- Source line: `31`
- **Missing docstring**

#### `def test_parquet_abre(parquet_disponivel)`
- Source line: `43`
- **Missing docstring**

#### `def test_parquet_tem_colunas_esperadas(parquet_disponivel)`
- Source line: `52`
- **Missing docstring**

#### `def test_parquet_tem_registros(parquet_disponivel)`
- Source line: `72`
- **Missing docstring**

#### `def test_leitura_de_uma_coluna(parquet_disponivel)`
- Source line: `79`
- **Missing docstring**

#### `def test_produz_saida_pequena(parquet_disponivel)`
- Source line: `87`
Confirma que conseguimos produzir uma saída minúscula — o 'smoke' final.

#### `def test_storage_read_srag(parquet_disponivel)`
- Source line: `102`
- **Missing docstring**

#### `def test_storage_read_srag_com_filtro(parquet_disponivel)`
- Source line: `113`
- **Missing docstring**

### `tools/collect_repo_context.py`

Gera um pacote seguro de contexto técnico do repositório para pessoas e IAs.

As pastas data/, models/, outputs/ e logs/ são excluídas
somente quando estão na raiz. Módulos como src/data e
src/models permanecem incluídos no inventário.

Uso, na raiz do Git:
    python tools/collect_repo_context.py

Saídas:
    docs/ai_context/repo_inventory.json
    docs/ai_context/repo_inventory.md
    docs/ai_context/pip_inspect.json
    docs/ai_context/pip_freeze.txt
    docs/ai_context/git_tracked_files.txt

O script não lê valores de .env, não inclui o conteúdo de dados/artefatos, e exclui
.venv, .git, caches, outputs e arquivos grandes.

#### `def run(cmd: list[str]) -> dict[str, Any]`
- Source line: `69`
- **Missing docstring**

#### `def sha256(path: Path) -> str`
- Source line: `78`
- **Missing docstring**

#### `def rel(path: Path) -> str`
- Source line: `86`
- **Missing docstring**

#### `def excluded(path: Path) -> bool`
- Source line: `90`
Exclui caches em qualquer nível, mas exclui data, models,
outputs e logs somente quando forem pastas da raiz.

Assim:
    data/processed/...       → excluído
    models/modelo.pkl        → excluído
    src/data/extracao.py     → incluído
    src/models/pipeline.py   → incluído

#### `def tracked_files() -> list[Path]`
- Source line: `119`
- **Missing docstring**

#### `def safe_text(path: Path) -> str | None`
- Source line: `126`
- **Missing docstring**

#### `def docstring(node: ast.AST) -> str | None`
- Source line: `140`
- **Missing docstring**

#### `def signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str`
- Source line: `145`
- **Missing docstring**

#### `def analyze_python(path: Path) -> dict[str, Any]`
- Source line: `175`
- **Missing docstring**

#### `def analyze_notebook(path: Path) -> dict[str, Any]`
- Source line: `210`
- **Missing docstring**

#### `def env_names_from_text(text: str) -> list[str]`
- Source line: `235`
- **Missing docstring**

#### `def redact_config_preview(path: Path, text: str) -> str`
- Source line: `247`
- **Missing docstring**

### `tools/update_project_reference.py`

One-command project reference generator.

Run from repository root:
    .\.venv\Scripts\python.exe tools\update_project_reference.py

Creates:
    docs/PROJECT_COMPLETE_REFERENCE.md

#### `def git(root: Path, *args: str) -> str`
- Source line: `77`
- **Missing docstring**

#### `def root_dir() -> Path`
- Source line: `83`
- **Missing docstring**

#### `def tracked(root: Path) -> list[Path]`
- Source line: `89`
- **Missing docstring**

#### `def include(path: Path) -> bool`
- Source line: `92`
- **Missing docstring**

#### `def redact(text: str) -> tuple[str, list[str]]`
- Source line: `95`
- **Missing docstring**

#### `def function_signature(node) -> str`
- Source line: `103`
- **Missing docstring**

#### `def api_section(path: Path, text: str) -> tuple[str, list[str]]`
- Source line: `111`
- **Missing docstring**

#### `def notebook(data: bytes) -> tuple[str, dict]`
- Source line: `129`
- **Missing docstring**

#### `def atomic_write(path: Path, text: str) -> None`
- Source line: `137`
- **Missing docstring**

#### `def main() -> int`
- Source line: `143`
- **Missing docstring**


## 10. Skipped files

- None.

## 11. Complete tracked source by file

Each section preserves the original file boundary. Notebook outputs are omitted.

## `configs/supervised.yaml`

- SHA-256: `5ba1cb2b4189b5f045e2e7558b21a5ec88daf040f6074e42be5db19c014127b6`
- Bytes: `8894`

```yaml
# =============================================================================
# Configuração do pipeline supervisionado — Projeto Integrador
# =============================================================================
#
# Este arquivo é a fonte única de verdade para C2–C6.
# Nenhum notebook deve hard-coded hiperparâmetro, fração de split ou limiar.
#
# REGRA:
#   Valores marcados com `null` ou `"TBD"` só podem ser preenchidos
#   DEPOIS que o gate correspondente for aprovado.
#   Enquanto estiverem nulos, o loader levanta erro explícito ao tentar usá-los.
# =============================================================================

version: 1
run_name_prefix: "supervisionado"

# -----------------------------------------------------------------------------
# Reprodutibilidade
# -----------------------------------------------------------------------------
seed: 42

# -----------------------------------------------------------------------------
# Alvo
# -----------------------------------------------------------------------------
target:
  coluna: evolucao

  # Valor(es) de `evolucao` que contam como positivo (óbito SRAG).
  # 1 = cura | 2 = óbito SRAG | 3 = óbito outras causas | 9 = ignorado
  positivos: [2.0]

  # Se True, descarta linhas com `evolucao == 9` (ignorado).
  descartar_ignorado: true

# -----------------------------------------------------------------------------
# Coluna temporal (usada no split)
# -----------------------------------------------------------------------------
coluna_tempo: dt_notific

# -----------------------------------------------------------------------------
# Features
# -----------------------------------------------------------------------------
# Estrutura definida agora; lista final consolidada após o gate G1.
features:
  numericas:
    - nu_idade_n

  categoricas:
    - sg_uf
    - cs_sexo
    - tp_gestante
    - febre
    - tosse
    - dispneia
    - saturacao
    - internado
    - utilizouvni
    - vacina_cov

  # Lista final só é fechada depois do gate G1 (definição do alvo e features).
  # Enquanto `null`, o loader usa `numericas + categoricas`.
  final: null

  # Colunas que NUNCA podem entrar em X (vazamento de alvo).
  # Servem de invariante para o `test_leakage.py`.
  proibidas:
    - evolucao
    - evolucao_covid19
    - dt_evolucao
    - dt_encerramento
    - classificacao_final
    - criterio_confirmacao
    - sorologia
    - pcr

# -----------------------------------------------------------------------------
# Split temporal
# -----------------------------------------------------------------------------
# As datas (`start` / `end`) são preenchidas APÓS o gate G2 (análise descritiva
# do período coberto pelo dataset). Enquanto nulas, o split é feito por fração.
temporal:
  modo: fracao        # "fracao" | "datas"
  fracao:
    treino:    0.70
    validacao: 0.15
    # holdout é o restante: 1 - 0.70 - 0.15 = 0.15

  # Só usadas se `modo == "datas"`. Deixadas nulas de propósito.
  datas:
    treino:
      start: null
      end:   null
    validacao:
      start: null
      end:   null
    holdout:
      start: null
      end:   null

  # Trava de segurança: o holdout só é liberado após `concluir_selecao()`.
  exigir_conclusao_selecao: true

# -----------------------------------------------------------------------------
# Modelos
# -----------------------------------------------------------------------------
# Valores marcados como null serão definidos nos gates:
#   G3 → baseline (referência fixa, valores já definidos abaixo)
#   G4 → regressão logística (busca de C e class_weight)
#   G5 → boosting (busca de learning_rate, max_iter, etc.)
models:

  baseline:
    # Não depende de tuning — é a referência mínima.
    strategy: prior

  logistic:
    # Valores iniciais razoáveis. Gate G4 decide se ficam.
    C: null                   # TBD: busca em [1e-3, 1e-2, 1e-1, 1, 10]
    penalty: l2
    solver: lbfgs
    max_iter: 1000
    class_weight: balanced

  boosting:
    # Valores iniciais razoáveis. Gate G5 decide se ficam.
    learning_rate: null       # TBD: busca em [0.01, 0.03, 0.05, 0.1]
    max_iter: null            # TBD: busca em [300, 500, 1000]
    max_depth: null           # TBD: [None, 4, 6, 8]
    max_leaf_nodes: 31
    min_samples_leaf: 20
    l2_regularization: 0.0
    early_stopping: true
    validation_fraction: 0.1
    n_iter_no_change: 20
    class_weight: balanced

# -----------------------------------------------------------------------------
# Calibração
# -----------------------------------------------------------------------------
# Gate G6 decide o método e onde calibrar (validação vs pedaço do treino).
calibracao:
  ativa: true
  metodo: null                # TBD: "isotonic" | "sigmoid"
  fonte: null                 # TBD: "validacao" | "treino_tail"
  frac_treino_tail: 0.10      # usado se `fonte == "treino_tail"`
  cv: prefit

# -----------------------------------------------------------------------------
# Limiar de decisão
# -----------------------------------------------------------------------------
# Gate G7 decide o limiar operacional (trade-off recall × precision).
limiar:
  default: 0.50               # usado enquanto o gate não fecha
  otimo: null                 # TBD: preenchido pelo gate G7
  metrica: f1                 # "f1" | "recall" | "precision" | "accuracy"
  min_precision: null         # TBD: se contexto clínico exigir, ex.: 0.5

# -----------------------------------------------------------------------------
# Métricas e avaliação
# -----------------------------------------------------------------------------
avaliacao:
  metricas_principais:
    - auc
    - ap
    - brier
    - f1
    - precision
    - recall
    - accuracy

  bootstrap:
    n_boot: 200
    alpha: 0.05
    seed: 42

  calibracao:
    n_bins: 10
    reportar:
      - ece
      - mce
      - brier_decomposicao

  grupos:
    # Colunas para `metricas_por_grupo` na análise de erros (C6)
    - sg_uf
    - cs_sexo
    - faixa_etaria

  min_n_grupo: 100            # grupos menores são ignorados

# -----------------------------------------------------------------------------
# Registro de execução
# -----------------------------------------------------------------------------
registro:
  output_dir: outputs/runs
  salvar_metadata: true
  salvar_summary: true

# =============================================================================
# GATES
# =============================================================================
# Cada gate marca uma decisão que precisa ser tomada ANTES de rodar a próxima
# etapa. O campo `status` evolui de "pendente" para "aprovado".
# Enquanto houver gate pendente, notebooks C3+ recusam rodar.
# =============================================================================
gates:

  G1_definicao_alvo_features:
    descricao: >
      Definir alvo binário definitivo (quais valores de `evolucao`
      contam como positivo) e a lista final de features.
    status: pendente
    aprovado_por: null
    data: null

  G2_janela_temporal:
    descricao: >
      Definir janelas de treino / validação / holdout. Pode ser por fração
      (modo atual) ou por datas explícitas.
    status: pendente
    aprovado_por: null
    data: null

  G3_baseline:
    descricao: >
      Rodar `DummyClassifier` e registrar AUC/accuracy de referência.
      Nenhum modelo precisa superar — serve para calibrar expectativas.
    status: pendente
    aprovado_por: null
    data: null

  G4_logistica:
    descricao: >
      Buscar C e class_weight da regressão logística na validação.
      Preencher `models.logistic.C`.
    status: pendente
    aprovado_por: null
    data: null

  G5_boosting:
    descricao: >
      Buscar learning_rate / max_iter / max_depth na validação.
      Preencher os campos `null` em `models.boosting`.
    status: pendente
    aprovado_por: null
    data: null

  G6_calibracao:
    descricao: >
      Escolher método de calibração (isotonic vs sigmoid) e fonte
      (validação vs treino_tail). Medir ECE antes/depois.
    status: pendente
    aprovado_por: null
    data: null

  G7_limiar:
    descricao: >
      Escolher limiar operacional. Se contexto clínico exigir precisão
      mínima, preencher `min_precision`.
    status: pendente
    aprovado_por: null
    data: null

  G8_holdout:
    descricao: >
      Liberar holdout UMA única vez. Rodar após G7.
      Registrar métricas finais em `outputs/runs/<RUN_ID>/metadata.json`.
    status: pendente
    aprovado_por: null
    data: null
```

## `notebooks/00_acesso_dados_parquet.ipynb`

- SHA-256: `bcdbce9d12a5367443589f2da21997ac762ba05a09d025c3b637bab90ddef8b4`
- Bytes: `3861`
- Notebook: `{"cells": 12, "kernel": {"display_name": "Python 3", "language": "python", "name": "python3"}, "outputs_omitted": true}`

### Cell 1 [markdown]

```markdown
# 00 — Acesso aos dados (Parquet)

Valida o acesso ao dataset distribuído via GitHub Release.

Pré-requisitos:
- Estar na raiz do projeto (ou em `notebooks/`).
- `requirements.txt` já instalado.
- Para repositório privado: variável/segregado `GITHUB_TOKEN` configurado.
```

### Cell 2 [markdown]

```markdown
## 0. Configuração inicial (imports e `sys.path`)

Deixe **todos os imports** aqui nesta primeira célula. Isso evita avisos do Pylance nas células seguintes (o analisador estático não acompanha a ordem de execução do kernel).
```

### Cell 3 [code]

```python
from pathlib import Path
import sys

ROOT_DIR = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.utils import storage

print("ROOT_DIR:", ROOT_DIR)
```

### Cell 4 [markdown]

```markdown
# 1. Diagnóstico rápido (rode isto antes de qualquer coisa)
```

### Cell 5 [code]

```python
path = storage.get_parquet(force=True)

print("Arquivo:", path)
print("Existe:", path.exists())
print("Tamanho:", path.stat().st_size, "bytes")

with open(path, "rb") as f:
    print("Primeiros 20 bytes:", f.read(20))
```

### Cell 6 [code]

```python
import pyarrow.parquet as pq
pq.read_schema(path)
```

### Cell 7 [markdown]

```markdown
## 2. Leitura mínima (só uma coluna)

Verifica se o Parquet é baixado/aberto corretamente.
```

### Cell 8 [code]

```python
df = storage.read_srag(columns=["sg_uf"])
print("shape:", df.shape)
df.head()
```

### Cell 9 [markdown]

```markdown
## 3. Coluna categórica — municípios únicos
```

### Cell 10 [code]

```python
storage.read_srag(columns=["id_municip"]).drop_duplicates().head(20)
```

### Cell 11 [markdown]

```markdown
## 4. Leitura com filtro (pushdown do Parquet)

Só as colunas necessárias e apenas linhas de SP.
```

### Cell 12 [code]

```python
df_sp = storage.read_srag(
    columns=["dt_notific", "sg_uf", "evolucao"],
    filters=[("sg_uf", "==", "SP")],
)

print("shape:", df_sp.shape)
df_sp.head()
```

## `notebooks/01_extracao.ipynb`

- SHA-256: `57d2c092ae78c727b7b3e77af64278849aac6eeb617b96157ea739d44f4083eb`
- Bytes: `6973`
- Notebook: `{"cells": 15, "kernel": {"display_name": "Python 3", "language": "python", "name": "python3"}, "outputs_omitted": true}`

### Cell 1 [markdown]

```markdown
# Extração de Dados SRAG

Este notebook documenta a **ingestão** dos dados brutos do SRAG 2019–2026.

Fluxo:

```
Dados Abertos do SUS (Parquet)
        ↓
coletar_amostra()  → DataFrame
        ↓
CSV (intermediário legível)
        ↓
Parquet (formato final para análise)
```

> **Escopo:** aqui só se faz **extração e conversão**.
> Modelagem, validação e métricas ficam em notebooks posteriores.
```

### Cell 2 [markdown]

```markdown
## 1. Importações e configuração inicial

Funciona tanto se o notebook for executado da **raiz do projeto** quanto de dentro de `notebooks/`.

Aproveita `src.utils.env` para:
- carregar o `.env` (se existir);
- garantir que `data/raw`, `data/processed`, `data/treino` e `reports/figures` existam.
```

### Cell 3 [code]

```python
from pathlib import Path
import sys

import pandas as pd


# Raiz do projeto (funciona tanto da raiz quanto de notebooks/)
ROOT_DIR = (
    Path.cwd().parent
    if Path.cwd().name == "notebooks"
    else Path.cwd()
)

# Permite importar src
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


# Módulos internos
from src.utils import env
from src.data.extracao import coletar_amostra, csv_to_parquet


# Carrega .env (se existir) e garante diretórios padrão do projeto
env.carregar_dotenv()
env.garantir_diretorios()

print("ROOT_DIR:", ROOT_DIR)
print(env.resumo())
```

### Cell 4 [markdown]

```markdown
## 2. Diretório de dados brutos
```

### Cell 5 [code]

```python
RAW_DIR = env.RAW
print(f"RAW_DIR: {RAW_DIR}")
```

### Cell 6 [markdown]

```markdown
## 3. Coleta dos dados brutos

⚠️ **Importante:** o SRAG 2019–2026 **não possui API paginada** nos Dados Abertos do SUS. O conjunto é disponibilizado apenas como **arquivo** (CSV, JSON, Parquet, XML).

Por isso, `coletar_amostra()` em `src/data/extracao.py` agora **baixa diretamente o arquivo Parquet** do portal e devolve um `DataFrame`:

```
https://dadosabertos.saude.gov.br/dataset/srag-2019-a-2026
        ↓
download do Parquet
        ↓
pd.read_parquet()
        ↓
DataFrame
```

Se o arquivo já existir localmente (`data/raw/<nome>.parquet`), ele é **reutilizado** — não baixa de novo.
```

### Cell 7 [code]

```python
df = coletar_amostra()

print(f"\nTotal coletado: {len(df):,} registros")
print(f"Total de colunas: {len(df.columns)}")

if df.empty:
    raise ValueError("Nenhum registro foi coletado.")

df.head()
```

### Cell 8 [markdown]

```markdown
## 4. Persistência do CSV (intermediário legível)
```

### Cell 9 [code]

```python
arquivo_csv = RAW_DIR / "srag_amostra.csv"

df.to_csv(
    arquivo_csv,
    index=False,
    encoding="utf-8-sig",
)
```

### Cell 10 [markdown]

```markdown
## 5. Verificação do total de registros salvos
```

### Cell 11 [code]

```python
df_salvo = pd.read_csv(arquivo_csv, low_memory=False)

print(f"Arquivo salvo em: {arquivo_csv}")
print(f"Registros no DataFrame: {len(df):,}")
print(f"Registros no arquivo:   {len(df_salvo):,}")

if len(df) == len(df_salvo):
    print("✓ Verificação concluída: todos os registros foram salvos.")
else:
    print("⚠ Atenção: o número de registros não coincide.")
```

### Cell 12 [markdown]

```markdown
## 6. Conversão do CSV para Parquet

O Parquet é o formato final usado pelos notebooks de análise.
O nome `srag_amostra.parquet` evita confusão com o Parquet completo distribuído em `data/processed/dados-v1/srag.parquet`.
```

### Cell 13 [code]

```python
PROCESSED_DIR = env.PROCESSED
arquivo_parquet = PROCESSED_DIR / "srag_amostra.parquet"

csv_to_parquet(
    csv_path=arquivo_csv,
    out_path=arquivo_parquet,
)
```

### Cell 14 [markdown]

```markdown
## 7. Verificação dos arquivos gerados
```

### Cell 15 [code]

```python
print(f"CSV:     {arquivo_csv}")
print(f"Parquet: {arquivo_parquet}")

print(f"\nTamanho do CSV:     {arquivo_csv.stat().st_size / 1024**2:.2f} MB")
print(f"Tamanho do Parquet: {arquivo_parquet.stat().st_size / 1024**2:.2f} MB")
```

## `notebooks/02_analise_exploratoria.ipynb`

- SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Bytes: `0`
- Notebook: `{"cells": 0, "placeholder": true}`

_Empty placeholder._

## `notebooks/02_eda/01_eda_primeira_passagem.ipynb`

- SHA-256: `61364f14adcb3d0b0849895bc7a9438408e32fb4b11b89e690e64fbf45f1ba7a`
- Bytes: `10811`
- Notebook: `{"cells": 18, "kernel": {"display_name": ".venv (3.14.7)", "language": "python", "name": "python3"}, "outputs_omitted": true}`

### Cell 1 [code]

```python
from pathlib import Path
import sys


def encontrar_raiz_projeto() -> Path:
    pasta_atual = Path.cwd().resolve()

    for pasta in [pasta_atual, *pasta_atual.parents]:
        if (pasta / "src").exists() and (pasta / "configs").exists():
            return pasta

    raise FileNotFoundError(
        "Não foi possível localizar a raiz do projeto."
    )


ROOT_DIR = encontrar_raiz_projeto()

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


from src.utils import env
from src.utils import storage


env.carregar_dotenv()

print(f"Raiz do projeto: {ROOT_DIR}")
```

### Cell 2 [code]

```python
COLUNAS_EDA = [
    "nu_notific",
    "dt_notific",
    "dt_sin_pri",
    "sem_pri",
    "cs_sexo",
    "nu_idade_n",
    "tp_idade",
    "cs_gestant",
    "ave_suino",
    "febre",
    "tosse",
    "garganta",
    "dispneia",
    "diarreia",
    "vomito",
    "outro_sin",
    "puerpera",
    "cardiopati",
    "hematologi",
    "sind_down",
    "hepatica",
    "asma",
    "diabetes",
    "neurologic",
    "pneumopati",
    "imunodepre",
    "renal",
    "obesidade",
    "obes_imc",
    "out_morbi",
    "tabag",
    "vacina",
    "dt_ut_dose",
    "mae_vac",
    "dt_vac_mae",
    "dt_doseuni",
    "dt_1_dose",
    "dt_2_dose",
    "hospital",
    "dt_interna",
    "evolucao",
    "dt_evoluca",
    "dt_encerra",
    "dt_digita",
    "out_anim",
    "dor_abd",
    "fadiga",
    "perd_olft",
    "perd_pala",
    "vacina_cov",
    "dose_1_cov",
    "dose_2_cov",
    "dose_ref",
    "dose_2ref",
    "dose_adic",
    "dos_re_bi"
]
```

### Cell 3 [code]

```python
caminho_parquet = storage.get_parquet()

print(f"Arquivo: {caminho_parquet}")
print(f"Existe: {caminho_parquet.exists()}")
print(
    f"Tamanho: "
    f"{caminho_parquet.stat().st_size / 1024**2:,.2f} MB"
)
```

### Cell 4 [code]

```python
import pyarrow.parquet as pq


arquivo_parquet = pq.ParquetFile(caminho_parquet)

colunas_disponiveis = arquivo_parquet.schema_arrow.names

print(
    f"Linhas registradas no Parquet: "
    f"{arquivo_parquet.metadata.num_rows:,}"
)

print(
    f"Colunas registradas no Parquet: "
    f"{arquivo_parquet.metadata.num_columns:,}"
)

print(
    f"Row groups: "
    f"{arquivo_parquet.metadata.num_row_groups:,}"
)
```

### Cell 5 [code]

```python
for coluna in COLUNAS_EDA:
    print(coluna)
```

### Cell 6 [code]

```python
colunas_disponiveis = set(metadados["colunas"])

colunas_ausentes = [
    coluna
    for coluna in COLUNAS_EDA
    if coluna not in colunas_disponiveis
]

if colunas_ausentes:
    print("Colunas que não foram encontradas:")

    for coluna in colunas_ausentes:
        print(f"- {coluna}")
else:
    print(
        "Todas as colunas solicitadas existem no Parquet."
    )
```

### Cell 7 [code]

```python
df = storage.read_srag(
    columns=COLUNAS_EDA,
)

print(f"Linhas carregadas: {df.shape[0\]:,}")
print(f"Colunas carregadas: {df.shape[1\]:,}")

display(df.head())
```

### Cell 8 [code]

```python
print(f"Linhas: {df.shape,}")
print(f"Colunas: {df.shape,}")
```

### Cell 9 [code]

```python
tipos = (
    df.dtypes
    .astype(str)
    .rename("tipo")
    .reset_index()
    .rename(columns={"index": "coluna"})
)

display(tipos)
```

### Cell 10 [code]

```python
df.info()
```

### Cell 11 [code]

```python
memoria_mb = (
    df.memory_usage(deep=True).sum()
    / 1024**2
)

print(f"Memória total utilizada: {memoria_mb:,.2f} MB")
```

### Cell 12 [code]

```python
memoria_colunas = (
    df.memory_usage(deep=True)
    .div(1024**2)
    .rename("memoria_mb")
    .sort_values(ascending=False)
    .reset_index()
    .rename(columns={"index": "coluna"})
)

display(memoria_colunas)
```

### Cell 13 [code]

```python
ausencias = (
    df.isna()
    .sum()
    .rename("quantidade_ausente")
    .to_frame()
)

ausencias["percentual_ausente"] = (
    ausencias["quantidade_ausente"]
    / len(df)
    * 100
)

ausencias = ausencias.sort_values(
    "percentual_ausente",
    ascending=False,
)

display(ausencias)
```

### Cell 14 [code]

```python
cardinalidade = (
    df.nunique(dropna=False)
    .rename("quantidade_valores_distintos")
    .sort_values(ascending=False)
    .reset_index()
    .rename(columns={"index": "coluna"})
)

display(cardinalidade)
```

### Cell 15 [code]

```python
# df["DT_NOTIFIC"] = pd.to_datetime(
#     df["DT_NOTIFIC"],
#     errors="coerce",
# )

# df["ANO_NOTIFICACAO"] = (
#     df["DT_NOTIFIC"].dt.year
# )

# display(
#     df["ANO_NOTIFICACAO"]
#     .value_counts(dropna=False)
#     .sort_index()
# )

df["ANO"].value_counts(
    dropna=False
).sort_index()
```

### Cell 16 [code]

```python
caminho_saida = (
RAIZ_PROJETO
/ "outputs"
/ "tables"
/ "validacao_colunas_eda.csv"
)
 
tipos.to_csv(
caminho_saida,
index=False,
encoding="utf-8-sig",
)
 
print(f"Arquivo salvo em: {caminho_saida}")
```

### Cell 17 [code]

```python
caminho_ausencias = (
    RAIZ_PROJETO
    / "outputs"
    / "tables"
    / "ausencias_primeira_passagem.csv"
)

ausencias.to_csv(
    caminho_ausencias,
    encoding="utf-8-sig",
)

print(f"Arquivo salvo em: {caminho_ausencias}")
```

### Cell 18 [code]

```python

```

## `notebooks/03_preprocessamento.ipynb`

- SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Bytes: `0`
- Notebook: `{"cells": 0, "placeholder": true}`

_Empty placeholder._

## `notebooks/04_feature_engineering.ipynb`

- SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Bytes: `0`
- Notebook: `{"cells": 0, "placeholder": true}`

_Empty placeholder._

## `notebooks/05_treinamento.ipynb`

- SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Bytes: `0`
- Notebook: `{"cells": 0, "placeholder": true}`

_Empty placeholder._

## `notebooks/06_avaliacao.ipynb`

- SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Bytes: `0`
- Notebook: `{"cells": 0, "placeholder": true}`

_Empty placeholder._

## `notebooks/C/C1_smoke_test.ipynb`

- SHA-256: `10aca6bd07bbaa96d90077cc33cd11239503410aea5051405790a2481ff7e23b`
- Bytes: `3673`
- Notebook: `{"cells": 7, "kernel": {"display_name": "Python 3", "language": "python", "name": "python3"}, "outputs_omitted": true}`

### Cell 1 [markdown]

```markdown
# C1 — Smoke Test e Reprodutibilidade

## Objetivo

Verificar se o ambiente do projeto está configurado corretamente
e se os principais módulos podem ser executados de forma reproduzível.

Este notebook **não realiza treinamento definitivo de modelos**.

### Verificações

- Ambiente Python
- Dependências
- Configurações
- Estrutura de diretórios
- Acesso aos dados
- Imports dos módulos
- Reprodutibilidade
```

### Cell 2 [code]

```python
from pathlib import Path
import sys

ROOT_DIR = Path.cwd().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

print("Projeto:", ROOT_DIR)
```

### Cell 3 [code]

```python
import platform
import sys

print("Python:", sys.version)
print("Sistema:", platform.system())
print("Arquitetura:", platform.machine())
```

### Cell 4 [code]

```python
from src.utils import config
from src.utils import storage
from src.utils import env

print("Imports principais: OK")

# Se você criou reproducibility.py:
from src.utils import reproducibility

print("Reprodutibilidade: OK")
```

### Cell 5 [code]

```python
required_dirs = [
    ROOT_DIR / "data",
    ROOT_DIR / "data" / "raw",
    ROOT_DIR / "data" / "processed",
    ROOT_DIR / "data" / "analytical",
    ROOT_DIR / "models",
    ROOT_DIR / "outputs",
    ROOT_DIR / "logs",
    ROOT_DIR / "configs",
]

for directory in required_dirs:
    print(
        "OK" if directory.exists() else "FALTA",
        directory
    )
```

### Cell 6 [code]

```python
import pyarrow.parquet as pq

parquet_path = (
    ROOT_DIR
    / "data"
    / "processed"
    / "dados-v1"
    / "srag.parquet"
)

schema = pq.read_schema(parquet_path)

print(schema)
```

### Cell 7 [code]

```python
assert parquet_path.exists(), "Parquet não encontrado"

print("SMOKE TEST: OK")
```

## `pyproject.toml`

- SHA-256: `c90d11c836f2fbc0679c6c6ba5d3cfeb61546cfc9a6a0e063d0ba23b5657ee0d`
- Bytes: `249`

```toml
[tool.pytest.ini_options]
minversion = "7.0"
testpaths  = ["tests"]
python_files = ["test_*.py"]
addopts = "-ra -q"
markers = [
    "slow: testes que fazem I/O pesado (Parquet, downloads)",
    "net:  testes que exigem acesso à internet",
]
```

## `pytest.ini`

- SHA-256: `32fdbb1c71bb5fd5755841b1521e26c7920334c2a314e67f26f68401ee3fc46c`
- Bytes: `164`

```ini
[pytest]
testpaths = tests
addopts = -ra -q
markers =
    slow: testes que fazem I/O pesado (Parquet, downloads)
    net:  testes que exigem acesso à internet
```

## `README.md`

- SHA-256: `444a994236e7dd27cd596d1eb96d2296b22cef33da8d3b1cd47b89063921096c`
- Bytes: `8242`

```markdown
# Projeto Integrador — SRAG Machine Learning

Projeto desenvolvido como parte do **Projeto Integrador I** da Pós-Graduação em Inteligência Artificial.

O projeto tem como objetivo aplicar técnicas de **Machine Learning** sobre dados reais da base de **Síndrome Respiratória Aguda Grave (SRAG)**, disponibilizada pelo Ministério da Saúde.

> 🚧 **Status:** Projeto em desenvolvimento.

---

## 🎯 Objetivo

O projeto busca investigar a aplicação de técnicas de Machine Learning sobre dados de SRAG, realizando um fluxo completo de desenvolvimento de um modelo:

**extração → limpeza → análise exploratória → engenharia de atributos → treinamento → avaliação**

O problema específico de Machine Learning e a variável-alvo (`target`) serão definidos e documentados durante o desenvolvimento do projeto.

---

## 📊 Dados

Os dados utilizados são provenientes da base pública **SRAG 2019–2026**, disponibilizada pelo Ministério da Saúde por meio da API de Dados Abertos.

**Fonte:** [Portal de Dados Abertos do Ministério da Saúde](https://apidadosabertos.saude.gov.br/)

Os dados são coletados por meio de uma rotina desenvolvida em Python e passam por diferentes etapas de preparação antes de serem utilizados nos modelos.

### Fluxo dos dados

```text
API do Ministério da Saúde
          │
          ▼
     Extração
          │
          ▼
      data/raw/
          │
          ▼
       Limpeza
          │
          ▼
   data/processed/
          │
          ▼
Feature Engineering
          │
          ▼
     data/treino/
          │
          ▼
     Treinamento
          │
          ▼
      Avaliação
          │
          ▼
   Modelo final
```

---

## 🧠 Tecnologias

O projeto utiliza principalmente:

* Python
* JupyterLab
* Pandas
* NumPy
* Requests
* Matplotlib
* Seaborn
* Scikit-learn
* python-dotenv

---

## 📁 Estrutura do projeto

```text
srag-machine-learning/
│
├── data/
│   ├── raw/
│   │   └── srag_amostra.csv
│   │
│   ├── processed/
│   │   └── srag_limpo.csv
│   │
│   └── treino/
│       ├── X_train.csv
│       ├── X_test.csv
│       ├── y_train.csv
│       └── y_test.csv
│
├── notebooks/
│   ├── 01_extracao.ipynb
│   ├── 02_analise_exploratoria.ipynb
│   ├── 03_preprocessamento.ipynb
│   ├── 04_feature_engineering.ipynb
│   ├── 05_treinamento.ipynb
│   └── 06_avaliacao.ipynb
│
├── src/
│   ├── data/
│   │   ├── extracao.py
│   │   └── preprocessamento.py
│   │
│   ├── features/
│   │   └── engenharia_features.py
│   │
│   ├── models/
│   │   ├── treinamento.py
│   │   └── avaliacao.py
│   │
│   └── utils/
│       └── config.py
│
├── models/
│   └── modelo_final.pkl
│
├── reports/
│   └── figuras/
│
├── requirements.txt
├── README.md
└── .gitignore
```

### 📂 Descrição das pastas

| Pasta             | Finalidade                                |
| ----------------- | ----------------------------------------- |
| `data/raw/`       | Dados obtidos diretamente da fonte        |
| `data/processed/` | Dados após limpeza e tratamento           |
| `data/treino/`    | Dados separados para treinamento e teste  |
| `notebooks/`      | Exploração, experimentação e documentação |
| `src/data/`       | Extração e preparação dos dados           |
| `src/features/`   | Engenharia e transformação de atributos   |
| `src/models/`     | Treinamento e avaliação dos modelos       |
| `src/utils/`      | Configurações e funções auxiliares        |
| `models/`         | Modelos treinados                         |
| `reports/`        | Gráficos e resultados das análises        |

---

## 🔬 Etapas do projeto

### 1. Extração dos dados

Os dados são obtidos por meio da API de Dados Abertos do Ministério da Saúde.

O código responsável pela extração está em:

```text
src/data/extracao.py
```

O processo é explorado e documentado em:

```text
notebooks/01_extracao.ipynb
```

---

### 2. Análise Exploratória

Nesta etapa são investigados:

* estrutura dos dados;
* tipos das variáveis;
* valores ausentes;
* duplicidades;
* distribuição das variáveis;
* relações entre atributos;
* distribuição temporal dos registros;
* possíveis padrões e anomalias.

Notebook:

```text
notebooks/02_analise_exploratoria.ipynb
```

---

### 3. Pré-processamento

Nesta etapa são realizados os tratamentos necessários para preparar os dados para Machine Learning.

Exemplos:

* tratamento de valores ausentes;
* conversão de tipos;
* remoção de duplicidades;
* tratamento de variáveis categóricas;
* tratamento de datas;
* preparação das variáveis.

Código principal:

```text
src/data/preprocessamento.py
```

Notebook:

```text
notebooks/03_preprocessamento.ipynb
```

---

### 4. Engenharia de atributos

Nesta etapa são criadas e selecionadas variáveis que podem contribuir para o desempenho dos modelos.

Código:

```text
src/features/engenharia_features.py
```

Notebook:

```text
notebooks/04_feature_engineering.ipynb
```

---

### 5. Treinamento

Os dados são separados em conjuntos de treinamento e teste:

```text
X_train
X_test
y_train
y_test
```

Diferentes algoritmos de Machine Learning poderão ser avaliados e comparados.

Código:

```text
src/models/treinamento.py
```

Notebook:

```text
notebooks/05_treinamento.ipynb
```

---

### 6. Avaliação

Os modelos são avaliados utilizando métricas adequadas ao problema.

Entre as métricas que poderão ser utilizadas:

* Accuracy
* Precision
* Recall
* F1-Score
* Matriz de Confusão
* ROC-AUC

A escolha definitiva das métricas será feita de acordo com a variável-alvo e as características do problema.

Código:

```text
src/models/avaliacao.py
```

Notebook:

```text
notebooks/06_avaliacao.ipynb
```

---

## 📈 Resultados

Os resultados dos experimentos, métricas, gráficos e comparações entre modelos serão documentados nesta seção conforme o desenvolvimento do projeto.

Os gráficos gerados durante as análises poderão ser armazenados em:

```text
reports/figuras/
```

---

## ⚙️ Instalação

Clone o repositório:

```bash
git clone https://github.com/SEU-USUARIO/srag-machine-learning.git
```

Entre na pasta:

```bash
cd srag-machine-learning
```

Crie um ambiente virtual:

```bash
python -m venv .venv
```

Ative o ambiente virtual no Windows:

```bash
.venv\Scripts\activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

---

## ▶️ Execução

Os notebooks podem ser executados seguindo a ordem:

```text
01_extracao
      ↓
02_analise_exploratoria
      ↓
03_preprocessamento
      ↓
04_feature_engineering
      ↓
05_treinamento
      ↓
06_avaliacao
```

O código reutilizável e definitivo das etapas encontra-se na pasta `src/`.

---

## ⚠️ Considerações

Os dados utilizados são provenientes de uma fonte pública e podem apresentar valores ausentes, inconsistências, alterações e outras características comuns a bases de dados reais.

Os resultados dos modelos devem ser interpretados considerando as limitações dos dados, das variáveis utilizadas e da metodologia empregada.

Este projeto possui finalidade **acadêmica e educacional**.

---

## 👥 Autores

* [Ivan Schincariol Oliveira](https://www.linkedin.com/in/ivan-s-oliveira-3608a92aa/)
* [Eduardo Hudson de Almeida Leite](https://www.linkedin.com/in/eduardo-hudson-de-almeida-leite-71ab5a7b/)
* [Pedro Henrique Silva dos Santos](https://www.linkedin.com/in/pedro-h-s-santos/)
* [Mateus da Silva Oliveira](https://www.linkedin.com/in/mateusso)
```

## `requirements.txt`

- SHA-256: `3f8f10901200a2490e4a2503ed2d5982c58aa865872c1f7fdb24f6922859f349`
- Bytes: `110`

```text
python-dotenv
PyYAML
jupyterlab
pandas
requests
numpy
matplotlib
seaborn
scikit-learn
pyarrow
pytest
```

## `src/__init__.py`

- SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Bytes: `0`

```python

```

## `src/evaluation/__init__.py`

- SHA-256: `8a8af79b590f02f5dcefaf3de03a6090002e90af1e94214d6f54bef53abc27dd`
- Bytes: `1015`

```python
"""Avaliação: splits temporais, métricas, calibração e análise de erros."""

from src.evaluation.temporal import (
    TemporalSplit,
    split_temporal_3way,
)
from src.evaluation.metrics import (
    auc,
    brier,
    f1,
    precision,
    recall,
    accuracy,
    metricas_completas,
    metricas_por_limiar,
    ic_bootstrap,
)
from src.evaluation.calibration import (
    curva_confiabilidade,
    ece,
    mce,
    brier_decomposicao,
)
from src.evaluation.errors import (
    matriz_confusao,
    extrair_falsos_positivos,
    extrair_falsos_negativos,
    metricas_por_grupo,
    top_erros,
)

__all__ = [
    "TemporalSplit", "split_temporal_3way",
    "auc", "brier", "f1", "precision", "recall", "accuracy",
    "metricas_completas", "metricas_por_limiar", "ic_bootstrap",
    "curva_confiabilidade", "ece", "mce", "brier_decomposicao",
    "matriz_confusao", "extrair_falsos_positivos", "extrair_falsos_negativos",
    "metricas_por_grupo", "top_erros",
]
```

## `src/evaluation/calibration.py`

- SHA-256: `50a7bf1b27bc9f0593e2fbc3b30f07b2d4365dadb0c28ee4a451bbf32144a895`
- Bytes: `5020`

```python
"""
Avaliação de calibração de probabilidades.

Complementa `src/models/calibration.py`:

    src/models/calibration.py      → AJUSTA a calibração
    src/evaluation/calibration.py  → MEDE a qualidade da calibração

Métricas implementadas
----------------------
- Curva de confiabilidade (reliability diagram)
- ECE  (Expected Calibration Error)
- MCE  (Maximum Calibration Error)
- Decomposição de Brier em Reliability + Resolution − Uncertainty
  (Murphy, 1973)
"""

from __future__ import annotations

from typing import Union

import numpy as np
import pandas as pd

from src.evaluation.metrics import _to_int_labels, _to_np

ArrayLike = Union[np.ndarray, pd.Series, list]


# ---------------------------------------------------------------------------
# Reliability diagram
# ---------------------------------------------------------------------------

def curva_confiabilidade(
    y_true: ArrayLike,
    y_prob: ArrayLike,
    n_bins: int = 10,
) -> pd.DataFrame:
    """
    Dados para o reliability diagram.

    Colunas:
        bin_centro    — probabilidade média prevista no bin
        freq_positiva — fração real de positivos no bin
        n             — número de amostras no bin
        gap           — |freq_positiva - bin_centro|
    """
    y = _to_int_labels(y_true)
    p = _to_np(y_prob)

    bins = np.linspace(0.0, 1.0, n_bins + 1)
    idx = np.clip(np.digitize(p, bins[1:-1], right=True), 0, n_bins - 1)

    linhas: list[dict[str, float]] = []
    for b in range(n_bins):
        m = idx == b
        n = int(m.sum())
        if n == 0:
            linhas.append({
                "bin_centro":    float((bins[b] + bins[b + 1]) / 2),
                "freq_positiva": float("nan"),
                "n":             0.0,
                "gap":           float("nan"),
            })
        else:
            centro = float(p[m].mean())
            freq = float(y[m].mean())
            linhas.append({
                "bin_centro":    centro,
                "freq_positiva": freq,
                "n":             float(n),
                "gap":           float(abs(freq - centro)),
            })

    return pd.DataFrame(linhas)


# ---------------------------------------------------------------------------
# ECE / MCE
# ---------------------------------------------------------------------------

def ece(
    y_true: ArrayLike,
    y_prob: ArrayLike,
    n_bins: int = 10,
) -> float:
    """Expected Calibration Error — média ponderada dos gaps por bin."""
    tabela = curva_confiabilidade(y_true, y_prob, n_bins=n_bins)
    total = float(tabela["n"].sum())
    if total == 0:
        return float("nan")
    pesos = tabela["n"] / total
    gaps = tabela["gap"].fillna(0.0)
    return float((pesos * gaps).sum())


def mce(
    y_true: ArrayLike,
    y_prob: ArrayLike,
    n_bins: int = 10,
) -> float:
    """Maximum Calibration Error — o pior gap entre os bins."""
    tabela = curva_confiabilidade(y_true, y_prob, n_bins=n_bins)
    gaps = tabela["gap"].dropna()
    if gaps.empty:
        return float("nan")
    return float(gaps.max())


# ---------------------------------------------------------------------------
# Decomposição de Brier (Murphy)
# ---------------------------------------------------------------------------

def brier_decomposicao(
    y_true: ArrayLike,
    y_prob: ArrayLike,
    n_bins: int = 10,
) -> dict[str, float]:
    """
    Decompõe o Brier score (Murphy, 1973):

        Brier = Reliability − Resolution + Uncertainty

    Retorna
    -------
    dict com:
        brier         — Brier score observado
        reliability   — quanto menor, melhor (penaliza desvios locais)
        resolution    — quanto maior, melhor (capacidade de separar)
        uncertainty   — entropia binária da base (fixa para o dataset)
        n             — número de amostras
    """
    y = _to_int_labels(y_true)
    p = _to_np(y_prob)
    n = len(y)

    if n == 0:
        raise ValueError("y_true vazio.")

    base_rate = float(y.mean())
    uncertainty = base_rate * (1.0 - base_rate)
    brier_obs = float(np.mean((p - y) ** 2))

    bins = np.linspace(0.0, 1.0, n_bins + 1)
    idx = np.clip(np.digitize(p, bins[1:-1], right=True), 0, n_bins - 1)

    reliability = 0.0
    resolution = 0.0
    for b in range(n_bins):
        m = idx == b
        n_b = int(m.sum())
        if n_b == 0:
            continue
        freq_obs = float(y[m].mean())
        freq_pred = float(p[m].mean())
        peso = n_b / n
        reliability += peso * (freq_obs - freq_pred) ** 2
        resolution += peso * (freq_obs - base_rate) ** 2

    return {
        "brier":       brier_obs,
        "reliability": float(reliability),
        "resolution":  float(resolution),
        "uncertainty": float(uncertainty),
        "n":           float(n),
    }
```

## `src/evaluation/errors.py`

- SHA-256: `9fe389c3b32f70747bb79c94d3757fd904677f219081ae9f71413499f3f9acd4`
- Bytes: `6402`

```python
"""
Análise de erros: quem o modelo erra, por quanto, e em quais grupos.

Ferramentas
-----------
- `matriz_confusao`           → TP/FP/FN/TN em DataFrame
- `extrair_falsos_positivos`  → subconjunto do df com FP
- `extrair_falsos_negativos`  → subconjunto do df com FN
- `metricas_por_grupo`        → métricas por categoria de uma coluna
- `top_erros`                 → os N piores erros por confiança
"""

from __future__ import annotations

from typing import Literal, Union

import numpy as np
import pandas as pd

from src.evaluation.metrics import (
    _to_int_labels,
    _to_np,
    auc,
    f1,
    precision,
    recall,
)

ArrayLike = Union[np.ndarray, pd.Series, list]

CriterioTop = Literal["fp", "fn", "erro_absoluto"]


# ---------------------------------------------------------------------------
# Matriz de confusão
# ---------------------------------------------------------------------------

def matriz_confusao(
    y_true: ArrayLike,
    y_pred: ArrayLike,
) -> pd.DataFrame:
    """
    Matriz de confusão 2×2 como DataFrame.

    Colunas: ["pred_0", "pred_1"], índice: ["real_0", "real_1"].
    Adiciona linha/coluna "total" para conveniência.
    """
    y = _to_int_labels(y_true)
    p = _to_int_labels(y_pred)

    tn = int(((y == 0) & (p == 0)).sum())
    fp = int(((y == 0) & (p == 1)).sum())
    fn = int(((y == 1) & (p == 0)).sum())
    tp = int(((y == 1) & (p == 1)).sum())

    df = pd.DataFrame(
        [[tn, fp], [fn, tp]],
        index=["real_0", "real_1"],
        columns=["pred_0", "pred_1"],
    )
    df["total"] = df.sum(axis=1)
    df.loc["total"] = df.sum(axis=0)
    return df


# ---------------------------------------------------------------------------
# Falsos positivos / negativos
# ---------------------------------------------------------------------------

def extrair_falsos_positivos(
    df: pd.DataFrame,
    y_true: ArrayLike,
    y_pred: ArrayLike,
) -> pd.DataFrame:
    """Retorna as linhas de `df` onde o modelo previu 1 mas o real é 0."""
    y = _to_int_labels(y_true)
    p = _to_int_labels(y_pred)
    mascara = (y == 0) & (p == 1)
    return df.loc[mascara].reset_index(drop=True)


def extrair_falsos_negativos(
    df: pd.DataFrame,
    y_true: ArrayLike,
    y_pred: ArrayLike,
) -> pd.DataFrame:
    """Retorna as linhas de `df` onde o modelo previu 0 mas o real é 1."""
    y = _to_int_labels(y_true)
    p = _to_int_labels(y_pred)
    mascara = (y == 1) & (p == 0)
    return df.loc[mascara].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Métricas por grupo
# ---------------------------------------------------------------------------

def metricas_por_grupo(
    df: pd.DataFrame,
    y_true: ArrayLike,
    y_prob: ArrayLike,
    coluna_grupo: str,
    *,
    limiar: float = 0.5,
    min_n: int = 30,
) -> pd.DataFrame:
    """
    Métricas por categoria de `coluna_grupo` (ex.: "sg_uf", "cs_sexo").

    Ignora grupos com menos de `min_n` amostras (evita métricas instáveis).

    Colunas: grupo, n, positivos, auc, f1, precision, recall.
    """
    if coluna_grupo not in df.columns:
        raise KeyError(f"Coluna de grupo ausente: {coluna_grupo!r}")

    y = _to_int_labels(y_true)
    p = _to_np(y_prob)

    if len(df) != len(y):
        raise ValueError(
            f"df tem {len(df)} linhas e y_true tem {len(y)}."
        )

    # zera o índice para casar com arrays
    base = df.reset_index(drop=True)
    grupos = base[coluna_grupo].astype("string")

    linhas: list[dict[str, float | str]] = []
    for g in grupos.dropna().unique():
        m = (grupos == g).to_numpy()
        n = int(m.sum())
        if n < min_n:
            continue

        y_g = y[m]
        p_g = p[m]
        y_pred = (p_g >= limiar).astype(int)

        # AUC só faz sentido se houver as duas classes
        if len(np.unique(y_g)) < 2:
            auc_g = float("nan")
        else:
            auc_g = auc(y_g, p_g)

        linhas.append({
            "grupo":     str(g),
            "n":         float(n),
            "positivos": float(y_g.mean()),
            "auc":       auc_g,
            "f1":        f1(y_g, y_pred),
            "precision": precision(y_g, y_pred),
            "recall":    recall(y_g, y_pred),
        })

    return pd.DataFrame(linhas).sort_values("n", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Top-N piores erros
# ---------------------------------------------------------------------------

def top_erros(
    df: pd.DataFrame,
    y_true: ArrayLike,
    y_prob: ArrayLike,
    *,
    n: int = 20,
    criterio: CriterioTop = "erro_absoluto",
    limiar: float = 0.5,
) -> pd.DataFrame:
    """
    Retorna as N linhas de `df` com os piores erros.

    Parâmetros
    ----------
    criterio : {"fp", "fn", "erro_absoluto"}
        - "fp"            → ordena por prob decrescente entre FP
        - "fn"            → ordena por prob crescente entre FN
        - "erro_absoluto" → ordena por |prob − y| decrescente (todos os erros)

    Adiciona colunas: `y_true`, `y_prob`, `y_pred`, `erro_abs`.
    """
    y = _to_int_labels(y_true)
    p = _to_np(y_prob)
    y_pred = (p >= limiar).astype(int)

    if len(df) != len(y):
        raise ValueError(
            f"df tem {len(df)} linhas e y_true tem {len(y)}."
        )

    out = df.reset_index(drop=True).copy()
    out["y_true"] = y
    out["y_prob"] = p
    out["y_pred"] = y_pred
    out["erro_abs"] = np.abs(p - y)

    if criterio == "fp":
        sel = out[(out["y_true"] == 0) & (out["y_pred"] == 1)]
        sel = sel.sort_values("y_prob", ascending=False)
    elif criterio == "fn":
        sel = out[(out["y_true"] == 1) & (out["y_pred"] == 0)]
        sel = sel.sort_values("y_prob", ascending=True)
    elif criterio == "erro_absoluto":
        sel = out[out["y_true"] != out["y_pred"]]
        sel = sel.sort_values("erro_abs", ascending=False)
    else:
        raise ValueError(
            f"criterio inválido: {criterio!r}. "
            f"Use 'fp', 'fn' ou 'erro_absoluto'."
        )

    return sel.head(n).reset_index(drop=True)
```

## `src/evaluation/metrics.py`

- SHA-256: `bad2eba62e460e7b3a4ff2003988faeddf36432a0b02e8b8ad2afe4f066df138`
- Bytes: `5912`

```python
"""
Métricas de classificação binária — todas retornam `float`.

Motivo: o scikit-learn retorna `Float | ndarray` para várias métricas,
o que faz o Pylance reclamar. Aqui a gente encapsula e garante `float`.

Também oferece:
    - `metricas_por_limiar` → tabela varrendo limiares
    - `ic_bootstrap`        → intervalo de confiança por bootstrap
"""

from __future__ import annotations

from typing import Callable, Union

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


# ---------------------------------------------------------------------------
# Tipos auxiliares
# ---------------------------------------------------------------------------

ArrayLike = Union[np.ndarray, pd.Series, list]


def _to_np(x: ArrayLike) -> np.ndarray:
    return np.asarray(x).ravel()


def _to_int_labels(y: ArrayLike) -> np.ndarray:
    return np.asarray(y).ravel().astype(int)


# ---------------------------------------------------------------------------
# Métricas individuais (retornam float)
# ---------------------------------------------------------------------------

def auc(y_true: ArrayLike, y_prob: ArrayLike) -> float:
    return float(roc_auc_score(_to_int_labels(y_true), _to_np(y_prob)))


def average_precision(y_true: ArrayLike, y_prob: ArrayLike) -> float:
    return float(average_precision_score(_to_int_labels(y_true), _to_np(y_prob)))


def brier(y_true: ArrayLike, y_prob: ArrayLike) -> float:
    return float(brier_score_loss(_to_int_labels(y_true), _to_np(y_prob)))


def f1(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    return float(f1_score(_to_int_labels(y_true), _to_int_labels(y_pred), zero_division=0))


def precision(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    return float(precision_score(_to_int_labels(y_true), _to_int_labels(y_pred), zero_division=0))


def recall(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    return float(recall_score(_to_int_labels(y_true), _to_int_labels(y_pred), zero_division=0))


def accuracy(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    return float(accuracy_score(_to_int_labels(y_true), _to_int_labels(y_pred)))


# ---------------------------------------------------------------------------
# Resumo completo
# ---------------------------------------------------------------------------

def metricas_completas(
    y_true: ArrayLike,
    y_prob: ArrayLike,
    limiar: float = 0.5,
) -> dict[str, float]:
    """
    Retorna um dict com AUC, AP, Brier, F1, precision, recall e accuracy.
    Pronto para `Run.metrica(**d)`.
    """
    y = _to_int_labels(y_true)
    p = _to_np(y_prob)
    y_pred = (p >= limiar).astype(int)

    return {
        "auc":       auc(y, p),
        "ap":        average_precision(y, p),
        "brier":     brier(y, p),
        "f1":        f1(y, y_pred),
        "precision": precision(y, y_pred),
        "recall":    recall(y, y_pred),
        "accuracy":  accuracy(y, y_pred),
        "limiar":    float(limiar),
        "n":         float(len(y)),
    }


# ---------------------------------------------------------------------------
# Varredura de limiar
# ---------------------------------------------------------------------------

_METRICAS: dict[str, Callable[[np.ndarray, np.ndarray], float]] = {
    "f1":        lambda y, p: float(f1_score(y, p, zero_division=0)),
    "precision": lambda y, p: float(precision_score(y, p, zero_division=0)),
    "recall":    lambda y, p: float(recall_score(y, p, zero_division=0)),
    "accuracy":  lambda y, p: float(accuracy_score(y, p)),
}


def metricas_por_limiar(
    y_true: ArrayLike,
    y_prob: ArrayLike,
    n_limiares: int = 101,
) -> pd.DataFrame:
    """
    Tabela com métricas para cada limiar em [0.01, 0.99].

    Colunas: limiar, f1, precision, recall, accuracy.
    """
    y = _to_int_labels(y_true)
    p = _to_np(y_prob)

    linhas: list[dict[str, float]] = []
    for th in np.linspace(0.01, 0.99, n_limiares):
        y_pred = (p >= float(th)).astype(int)
        linhas.append({
            "limiar":    float(th),
            "f1":        _METRICAS["f1"](y, y_pred),
            "precision": _METRICAS["precision"](y, y_pred),
            "recall":    _METRICAS["recall"](y, y_pred),
            "accuracy":  _METRICAS["accuracy"](y, y_pred),
        })

    return pd.DataFrame(linhas)


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

def ic_bootstrap(
    y_true: ArrayLike,
    y_prob: ArrayLike,
    *,
    metrica: Callable[[ArrayLike, ArrayLike], float] = auc,
    n_boot: int = 200,
    alpha: float = 0.05,
    seed: int = 42,
) -> tuple[float, float, float]:
    """
    Intervalo de confiança via bootstrap percentil.

    Retorna (estimativa, limite_inferior, limite_superior).

    Parâmetros
    ----------
    metrica : callable(y_true, y_prob) -> float
        Função de métrica. Default: `auc`.
    n_boot : int
        Número de reamostragens.
    alpha : float
        Nível de significância (0.05 → IC 95%).
    seed : int
        Semente para reprodutibilidade.
    """
    y = _to_int_labels(y_true)
    p = _to_np(y_prob)

    rng = np.random.default_rng(seed)
    n = len(y)
    valores = np.empty(n_boot, dtype="float64")

    for i in range(n_boot):
        idx = rng.integers(0, n, size=n)
        valores[i] = metrica(y[idx], p[idx])

    est = float(metrica(y, p))
    inf = float(np.quantile(valores, alpha / 2))
    sup = float(np.quantile(valores, 1 - alpha / 2))
    return est, inf, sup
```

## `src/evaluation/temporal.py`

- SHA-256: `302bd38701cb96958ee1b7d9259f9646494a7fdc60135aff884cceaba8cbc064`
- Bytes: `7835`

```python
"""
Split temporal em três blocos + trava do holdout.

Regra de ouro:
    ┌──────────────┬──────────────┬──────────────────┐
    │   treino     │  validação   │     holdout      │
    └──────────────┴──────────────┴──────────────────┘
     mais antigo ───────────────────────► mais recente

    - `treino` + `validação` → escolha de modelo, hiperparâmetros, limiar
    - `holdout`               → UMA ÚNICA vez, no fim, após `concluir_selecao()`

A classe `TemporalSplit` bloqueia o acesso ao holdout enquanto a seleção
não for explicitamente marcada como concluída. Isso impede o erro clássico
de "espionar" o holdout durante a fase de modelagem.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


# ---------------------------------------------------------------------------
# Split em 3 blocos (função pura, sem trava)
# ---------------------------------------------------------------------------

def split_temporal_3way(
    df: pd.DataFrame,
    coluna_tempo: str,
    frac_treino: float = 0.7,
    frac_validacao: float = 0.15,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split temporal em treino / validação / holdout, **sem embaralhar**.

    Parâmetros
    ----------
    df : pd.DataFrame
        Base completa.
    coluna_tempo : str
        Coluna usada para ordenar (ex.: "dt_notific").
    frac_treino, frac_validacao : float
        Frações do total. `frac_holdout = 1 - frac_treino - frac_validacao`.

    Retorno
    -------
    (treino, validacao, holdout) : tuple de DataFrames

    Garantias
    ---------
        max(treino[coluna_tempo]) <= min(validacao[coluna_tempo])
        max(validacao[coluna_tempo]) <= min(holdout[coluna_tempo])
    """
    if coluna_tempo not in df.columns:
        raise KeyError(f"Coluna temporal ausente: {coluna_tempo!r}")

    if not (0 < frac_treino < 1):
        raise ValueError("frac_treino deve estar em (0, 1).")
    if not (0 < frac_validacao < 1):
        raise ValueError("frac_validacao deve estar em (0, 1).")
    if frac_treino + frac_validacao >= 1:
        raise ValueError(
            "frac_treino + frac_validacao deve ser < 1 "
            "(o restante vira holdout)."
        )

    ordenado = (
        df.sort_values(coluna_tempo, kind="mergesort")
          .reset_index(drop=True)
    )

    n = len(ordenado)
    if n < 3:
        raise ValueError(f"Dataset pequeno demais para split 3-way: n={n}")

    corte_treino = int(n * frac_treino)
    corte_valid = int(n * (frac_treino + frac_validacao))

    treino = ordenado.iloc[:corte_treino].reset_index(drop=True)
    validacao = ordenado.iloc[corte_treino:corte_valid].reset_index(drop=True)
    holdout = ordenado.iloc[corte_valid:].reset_index(drop=True)

    return treino, validacao, holdout


# ---------------------------------------------------------------------------
# Split com trava do holdout
# ---------------------------------------------------------------------------

@dataclass
class TemporalSplit:
    """
    Guarda os três blocos e controla o acesso ao holdout.

    Uso típico
    ----------
        split = TemporalSplit(df, coluna_tempo="dt_notific")

        # Fase 1 — escolha de modelo (SOMENTE treino + validação)
        tr, va = split.treino_validacao()
        modelo = ...
        modelo.fit(tr[FEATURES], y_tr)

        # Ao terminar a seleção:
        split.concluir_selecao()

        # Fase 2 — avaliação final, UMA única vez
        ho = split.holdout()
        y_prob = modelo.predict_proba(ho[FEATURES])[:, 1]

    Atributos
    ---------
    n_treino, n_validacao, n_holdout : int
        Tamanhos de cada bloco (útil para logging).
    """

    df: pd.DataFrame
    coluna_tempo: str
    frac_treino: float = 0.7
    frac_validacao: float = 0.15

    _treino: pd.DataFrame = field(init=False, repr=False)
    _validacao: pd.DataFrame = field(init=False, repr=False)
    _holdout: pd.DataFrame = field(init=False, repr=False)
    _holdout_liberado: bool = field(init=False, default=False, repr=False)

    def __post_init__(self) -> None:
        tr, va, ho = split_temporal_3way(
            self.df,
            coluna_tempo=self.coluna_tempo,
            frac_treino=self.frac_treino,
            frac_validacao=self.frac_validacao,
        )
        self._treino = tr
        self._validacao = va
        self._holdout = ho

    # ------------------------------------------------------------------
    # Acesso aos blocos de modelagem
    # ------------------------------------------------------------------

    def treino_validacao(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Retorna (treino, validação).

        Este é o único caminho para treinar e comparar modelos durante a
        fase de seleção. O holdout NÃO é exposto aqui.
        """
        return self._treino, self._validacao

    @property
    def treino(self) -> pd.DataFrame:
        return self._treino

    @property
    def validacao(self) -> pd.DataFrame:
        return self._validacao

    # ------------------------------------------------------------------
    # Ciclo de vida do holdout
    # ------------------------------------------------------------------

    def concluir_selecao(self) -> None:
        """
        Marca a fase de seleção como encerrada e libera o holdout.

        Deve ser chamada **uma única vez**, depois que o modelo final foi
        escolhido, o limiar foi definido e a calibração foi ajustada.
        """
        self._holdout_liberado = True

    @property
    def holdout_liberado(self) -> bool:
        return self._holdout_liberado

    def holdout(self) -> pd.DataFrame:
        """
        Retorna o bloco de holdout.

        Levanta `RuntimeError` se `concluir_selecao()` ainda não foi
        chamada. Isso impede que o holdout seja consultado durante a
        escolha de modelo.
        """
        if not self._holdout_liberado:
            raise RuntimeError(
                "Holdout bloqueado.\n"
                "Finalize a seleção de modelo e chame `split.concluir_selecao()` "
                "antes de acessar o holdout."
            )
        return self._holdout

    # ------------------------------------------------------------------
    # Diagnóstico
    # ------------------------------------------------------------------

    @property
    def n_treino(self) -> int:
        return len(self._treino)

    @property
    def n_validacao(self) -> int:
        return len(self._validacao)

    @property
    def n_holdout(self) -> int:
        return len(self._holdout)

    def resumo(self) -> str:
        """Resumo legível do split — bom para log no `Run`."""
        def _periodo(d: pd.DataFrame) -> str:
            if d.empty:
                return "vazio"
            ini = d[self.coluna_tempo].min()
            fim = d[self.coluna_tempo].max()
            return f"{ini} .. {fim}"

        return (
            f"TemporalSplit(coluna={self.coluna_tempo!r})\n"
            f"  treino    : {self.n_treino:>10,}  {_periodo(self._treino)}\n"
            f"  validacao : {self.n_validacao:>10,}  {_periodo(self._validacao)}\n"
            f"  holdout   : {self.n_holdout:>10,}  {_periodo(self._holdout)}  "
            f"({'liberado' if self._holdout_liberado else 'bloqueado'})"
        )
```

## `src/features/__init__.py`

- SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Bytes: `0`

```python

```

## `src/features/engenharia_features.py`

- SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Bytes: `0`

```python

```

## `src/utils/__init__.py`

- SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Bytes: `0`

```python

```

## `src/utils/config.py`

- SHA-256: `bedf5a8b094a4bda545ac0b7a2eeda1feea4731703d22d9139c8c5785b83596e`
- Bytes: `11207`

```python
"""
Configurações centralizadas do Projeto Integrador.

Regras deste módulo:
- NÃO usar caminhos pessoais (C:/Users/... , /home/fulano/...).
- NÃO usar caminhos absolutos externos ao projeto.
- Todos os caminhos derivam de ROOT_DIR, calculado a partir deste arquivo.
- Segredos e URLs sensíveis são lidos LAZILY (função), nunca no import —
  porque o `.env` é carregado por `env.carregar_dotenv()` depois.
- O YAML de configuração (`configs/supervised.yaml`) também é lido LAZILY
  e cacheado, pelo mesmo motivo.
"""

from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Raiz do projeto
# ---------------------------------------------------------------------------
# <ROOT>/src/utils/config.py → parents[2] = <ROOT>
# ---------------------------------------------------------------------------
ROOT_DIR: Path = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Reprodutibilidade
# ---------------------------------------------------------------------------
SEED = 42
RANDOM_STATE = SEED


# ---------------------------------------------------------------------------
# Diretórios do projeto (fonte única da verdade)
# ---------------------------------------------------------------------------
DATA_DIR      = ROOT_DIR / "data"
RAW_DIR       = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
TREINO_DIR    = DATA_DIR / "treino"

CONFIGS_DIR   = ROOT_DIR / "configs"
MODELS_DIR    = ROOT_DIR / "models"
OUTPUTS_DIR   = ROOT_DIR / "outputs"
RUNS_DIR      = OUTPUTS_DIR / "runs"
LOGS_DIR      = ROOT_DIR / "logs"
REPORTS_DIR   = ROOT_DIR / "reports"
FIGURES_DIR   = REPORTS_DIR / "figures"

TABLES_DIR        = OUTPUTS_DIR / "tables"
PREDICTIONS_DIR   = OUTPUTS_DIR / "predictions"


# ---------------------------------------------------------------------------
# Arquivos de configuração do projeto
# ---------------------------------------------------------------------------
SUPERVISED_YAML = CONFIGS_DIR / "supervised.yaml"


# ---------------------------------------------------------------------------
# Dataset processado (versão distribuída via GitHub Release)
# ---------------------------------------------------------------------------
GITHUB_REPO  = "Ivan-S-Oliveira/Projeto_Integrador"
DATA_VERSION = "dados-v1"
PARQUET_NAME = "srag.parquet"

GITHUB_RELEASE_URL = (
    f"https://github.com/{GITHUB_REPO}/releases/download/{DATA_VERSION}/"
)


# ---------------------------------------------------------------------------
# Segredos e URLs sensíveis — LEITURA LAZY
# ---------------------------------------------------------------------------
# Não use estas constantes em tempo de import. Chame as funções abaixo,
# sempre depois de `env.carregar_dotenv()`. Assim o `.env` funciona.
# ---------------------------------------------------------------------------

def github_token() -> str | None:
    """Token do GitHub — lido a cada chamada (permite .env tardio)."""
    return os.getenv("GITHUB_TOKEN")


def srag_parquet_url() -> str:
    """
    URL do Parquet do SRAG 2019–2026.

    Override via variável de ambiente `SRAG_PARQUET_URL`.
    O link do Parquet muda semanalmente — atualize em:
      https://dadosabertos.saude.gov.br/dataset/srag-2019-a-2026
    """
    return os.getenv(
        "SRAG_PARQUET_URL",
        "https://s3.sa-east-1.amazonaws.com/"
        "ckan.saude.gov.br/SRAG/2023/INFLUD23-16-10-2023.parquet",
    )


# ---------------------------------------------------------------------------
# Configuração supervisionada — LEITURA LAZY + CACHEADa
# ---------------------------------------------------------------------------
# Interpolação simples de ${VAR} com variáveis de ambiente. Útil quando o
# YAML quiser referenciar algo do .env (ex.: caminhos de artefato).
# ---------------------------------------------------------------------------
_ENV_PATTERN = re.compile(r"\$\{(\w+)\}")


def _interpolar_env(texto: str) -> str:
    """Substitui `${VAR}` pelo valor de os.environ (vazio se ausente)."""
    return _ENV_PATTERN.sub(lambda m: os.getenv(m.group(1), ""), texto)


@lru_cache(maxsize=1)
def carregar_supervised() -> dict[str, Any]:
    """
    Lê `configs/supervised.yaml` de forma lazy e cacheada.

    Regras:
    - Import de `yaml` é local (dependência opcional em tempo de import).
    - Se o arquivo não existir, levanta FileNotFoundError com instrução.
    - Suporta `${VAR}` interpolado a partir do ambiente.
    - O resultado é cacheado — para recarregar após editar o YAML, chame
      `carregar_supervised.cache_clear()`.
    """
    if not SUPERVISED_YAML.exists():
        raise FileNotFoundError(
            f"Configuração não encontrada: {SUPERVISED_YAML}\n"
            f"Crie o arquivo em {CONFIGS_DIR}/supervised.yaml "
            f"ou ajuste CONFIGS_DIR / SUPERVISED_YAML em config.py."
        )

    try:
        import yaml  # import local: não quebra quem não usa o YAML
    except ImportError as e:
        raise ImportError(
            "PyYAML não está instalado. Rode: pip install pyyaml"
        ) from e

    texto = _interpolar_env(SUPERVISED_YAML.read_text(encoding="utf-8"))
    dados = yaml.safe_load(texto) or {}

    if not isinstance(dados, dict):
        raise ValueError(
            f"{SUPERVISED_YAML} deve conter um mapeamento (dict) na raiz, "
            f"mas veio {type(dados).__name__}."
        )
    return dados


def supervised_yaml_sha256() -> str | None:
    """
    SHA-256 do YAML atual (ou None se não existir).
    Útil para gravar em `metadata.json` e garantir reprodutibilidade.
    """
    import hashlib
    if not SUPERVISED_YAML.exists():
        return None
    h = hashlib.sha256()
    with open(SUPERVISED_YAML, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------
HTTP_TIMEOUT    = 180
HTTP_TENTATIVAS = 3
HTTP_BACKOFF    = 5


# ---------------------------------------------------------------------------
# Leitura de CSV
# ---------------------------------------------------------------------------
CSV_SEP      = ","
CSV_ENCODING = "utf-8-sig"
COLS         = None   # None = todas as colunas


# ---------------------------------------------------------------------------
# Conversão CSV → Parquet
# ---------------------------------------------------------------------------
PARQUET_COMPRESSION = "zstd"
CSV_CHUNKSIZE       = 500_000


# ---------------------------------------------------------------------------
# Compatibilidade retroativa
# ---------------------------------------------------------------------------
# O SRAG não possui API paginada — mantidos como None para deixar explícito.
API_URL   = None
PAGE_SIZE = None
N_PAGINAS = None

# ---------------------------------------------------------------------------
# Acesso tipado ao YAML supervisionado
# ---------------------------------------------------------------------------
class GatePendenteError(RuntimeError):
    """Levantado quando se tenta usar um valor que depende de gate não aprovado."""


def cfg(*chaves: str, default: Any = None) -> Any:
    """
    Acessa uma chave aninhada do supervised.yaml.

        cfg("target", "coluna")          -> "evolucao"
        cfg("models", "logistic", "C")   -> None (TBD)
    """
    atual: Any = carregar_supervised()
    for k in chaves:
        if not isinstance(atual, dict) or k not in atual:
            return default
        atual = atual[k]
    return atual


def exigir_valor(valor: Any, *, caminho: str, gate: str) -> Any:
    """
    Garante que `valor` não é None nem 'TBD'. Se for, levanta erro
    apontando o gate que precisa ser aprovado antes.
    """
    if valor is None or valor == "TBD":
        raise GatePendenteError(
            f"Valor não definido em '{caminho}'. "
            f"Aprove o gate '{gate}' em configs/supervised.yaml antes de usar."
        )
    return valor


def gate_aprovado(nome_gate: str) -> bool:
    """Retorna True se o gate existe e está com status 'aprovado'."""
    g = cfg("gates", nome_gate) or {}
    return g.get("status") == "aprovado"


def exigir_gate(nome_gate: str) -> None:
    """Levanta GatePendenteError se o gate ainda não foi aprovado."""
    if not gate_aprovado(nome_gate):
        raise GatePendenteError(
            f"Gate '{nome_gate}' está pendente. "
            f"Aprove-o em configs/supervised.yaml (status: aprovado) "
            f"antes de rodar esta etapa."
        )


def features_finais() -> list[str]:
    """
    Retorna a lista final de features.
    Se `features.final` for null, usa numericas + categoricas.
    """
    f = cfg("features") or {}
    final = f.get("final")
    if final:
        return list(final)
    return list(f.get("numericas", [])) + list(f.get("categoricas", []))


def limiar_ativo() -> float:
    """
    Retorna o limiar operacional.
    Só usa `otimo` se o gate G7 estiver aprovado; caso contrário, `default`.
    """
    lim = cfg("limiar") or {}
    if gate_aprovado("G7_limiar") and lim.get("otimo") is not None:
        return float(lim["otimo"])
    return float(lim.get("default", 0.5))


# ---------------------------------------------------------------------------
# Utilitário de diagnóstico
# ---------------------------------------------------------------------------
def _status(valor: object) -> str:
    return "definido" if valor else "vazio"


def resumo() -> str:
    """Retorna um resumo legível das configurações ativas."""
    yaml_ok = "ok" if SUPERVISED_YAML.exists() else "AUSENTE"
    return (
        f"ROOT_DIR          = {ROOT_DIR}\n"
        f"DATA_DIR          = {DATA_DIR}\n"
        f"RAW_DIR           = {RAW_DIR}\n"
        f"PROCESSED_DIR     = {PROCESSED_DIR}\n"
        f"TREINO_DIR        = {TREINO_DIR}\n"
        f"OUTPUTS_DIR       = {OUTPUTS_DIR}\n"
        f"RUNS_DIR          = {RUNS_DIR}\n"
        f"LOGS_DIR          = {LOGS_DIR}\n"
        f"CONFIGS_DIR       = {CONFIGS_DIR}\n"
        f"SUPERVISED_YAML   = {SUPERVISED_YAML} ({yaml_ok})\n"
        f"PARQUET_NAME      = {PARQUET_NAME}\n"
        f"DATA_VERSION      = {DATA_VERSION}\n"
        f"GITHUB_REPO       = {GITHUB_REPO}\n"
        f"HTTP_TIMEOUT      = {HTTP_TIMEOUT}\n"
        f"HTTP_TENTATIVAS   = {HTTP_TENTATIVAS}\n"
        f"SEED              = {SEED}\n"
        f"GITHUB_TOKEN?     = {bool(github_token())}\n"
        f"SRAG_PARQUET_URL  = {srag_parquet_url()}\n"
        f"SUPERVISED_SHA256 = {supervised_yaml_sha256()}\n"
    )


if __name__ == "__main__":
    print(resumo())
```

## `src/utils/env.py`

- SHA-256: `da7ccb78607f8577a3ecc76047aa1a418584779a2afb352a98bda3f900633b94`
- Bytes: `5054`

```python
"""
Carregamento de variáveis de ambiente e segredos do projeto.

Fluxo:
    .env  →  os.environ  →  config.py  →  restante do projeto

Regras:
- O arquivo .env NUNCA vai para o Git (ver .gitignore).
- Use .env.example como template versionado.
- Não há dependência de Colab, Kaggle ou qualquer ambiente específico.
- Em CI/CD ou produção, defina as variáveis diretamente no ambiente;
  o .env é opcional e serve apenas para desenvolvimento local.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Raiz do projeto: <ROOT>/src/utils/env.py → parents[2] = <ROOT>
# ---------------------------------------------------------------------------
ROOT: Path = Path(__file__).resolve().parents[2]

# Diretórios padrão do projeto
DATA      = ROOT / "data"
RAW       = DATA / "raw"
PROCESSED = DATA / "processed"
TREINO    = DATA / "treino"
FIGURES   = ROOT / "reports" / "figures"


def garantir_diretorios() -> None:
    """Cria os diretórios padrão do projeto, se ainda não existirem."""
    for p in (RAW, PROCESSED, TREINO, FIGURES):
        p.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Carregamento do .env (opcional)
# ---------------------------------------------------------------------------
# python-dotenv é opcional: se não estiver instalado, seguimos apenas com
# variáveis de ambiente já definidas no sistema.
# ---------------------------------------------------------------------------
def carregar_dotenv(caminho: Path | None = None) -> bool:
    """
    Carrega o arquivo .env da raiz do projeto (ou o caminho informado).

    Retorna True se o arquivo foi encontrado e carregado, False caso contrário.
    Não sobrescreve variáveis já definidas no ambiente (override=False).
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        return False

    caminho = Path(caminho) if caminho else ROOT / ".env"

    if not caminho.exists():
        return False

    load_dotenv(dotenv_path=caminho, override=False)
    return True


# ---------------------------------------------------------------------------
# Detecção do ambiente (apenas informativa)
# ---------------------------------------------------------------------------
def detectar_ambiente() -> str:
    """
    Retorna 'ci' se estiver em pipeline, senão 'local'.

    Não é mais usado para escolher fonte de segredos — apenas para logs.
    """
    if os.getenv("CI") or os.getenv("GITHUB_ACTIONS"):
        return "ci"
    return "local"


ENV = detectar_ambiente()


# ---------------------------------------------------------------------------
# Acesso a variáveis e segredos
# ---------------------------------------------------------------------------
def get_env(nome: str, default: str | None = None) -> str | None:
    """Lê uma variável de ambiente, com default opcional."""
    return os.getenv(nome, default)


def get_secret(nome: str, obrigatorio: bool = True) -> str | None:
    """
    Lê um segredo/variável sensível do ambiente.

    Parâmetros
    ----------
    nome : str
        Nome da variável (ex.: 'GITHUB_TOKEN').
    obrigatorio : bool
        Se True (padrão) e a variável não existir, levanta RuntimeError
        com mensagem explicativa. Se False, retorna None.

    Uso
    ---
    >>> token = get_secret("GITHUB_TOKEN", obrigatorio=False)
    >>> if token: ...
    """
    valor = os.getenv(nome)

    if valor:
        return valor

    if not obrigatorio:
        return None

    raise RuntimeError(
        f"Variável de ambiente '{nome}' não definida.\n"
        f"Defina-a de uma destas formas:\n"
        f"  1) Crie/edite o arquivo {ROOT / '.env'} (não versionado):\n"
        f"         {nome}=seu_valor_aqui\n"
        f"  2) Exporte no shell antes de rodar o projeto:\n"
        f"         Linux/macOS:  export {nome}=seu_valor_aqui\n"
        f"         PowerShell:   $env:{nome} = \"seu_valor_aqui\"\n"
    )


# ---------------------------------------------------------------------------
# Diagnóstico
# ---------------------------------------------------------------------------
def resumo() -> str:
    """Resumo legível do estado do ambiente."""
    tem_env_file = (ROOT / ".env").exists()
    return (
        f"ROOT_DIR         = {ROOT}\n"
        f"ENV              = {ENV}\n"
        f".env encontrado? = {tem_env_file}\n"
        f"GITHUB_TOKEN?    = {bool(os.getenv('GITHUB_TOKEN'))}\n"
    )


# ---------------------------------------------------------------------------
# Execução direta: prepara diretórios e mostra o resumo
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    carregar_dotenv()
    garantir_diretorios()
    print(resumo())
```

## `src/utils/reproducibility.py`

- SHA-256: `e4022c6716ffecc2d2a32228468bb164ab70b82180b6e721aaeb5a3ae9ac6bf7`
- Bytes: `11106`

```python
"""
Registro de execuções para reprodutibilidade (critério C1).

Cada execução gera `outputs/runs/<RUN_ID>/` com:
    metadata.json   ← tudo estruturado
    summary.txt     ← versão legível

Uso:
    from src.utils.reproducibility import Run

    with Run(modelo="logistic", parametros={"C": 1.0}) as r:
        ... treino ...
        r.metrica(auc=0.82, accuracy=0.78)
        r.anotar("split temporal por dt_notific")
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import time

from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Any

from src.utils import config as C


RUNS_DIR: Path = getattr(C, "RUNS_DIR", C.ROOT_DIR / "outputs" / "runs")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def gerar_run_id(
    modelo: str | None = None,
    base_dir: Path | None = None,
) -> str:
    """
    Gera um identificador unico para uma execucao.

    O uso de microssegundos reduz o risco de duas execucoes
    receberem o mesmo identificador.
    """
    agora = datetime.now().strftime(
        "%Y-%m-%d_%H%M%S_%f"
    )

    sufixo = (
        f"_{modelo}"
        if modelo
        else ""
    )

    candidato = (
        f"{agora}{sufixo}"
    )

    if base_dir is None:
        return candidato

    base = Path(base_dir)
    run_id = candidato
    contador = 1

    while (
        base / run_id
    ).exists():
        run_id = (
            f"{candidato}_{contador:02d}"
        )
        contador += 1

    return run_id


def _agora() -> dict[str, str]:
    utc = datetime.now(timezone.utc)
    return {
        "utc":   utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "local": utc.astimezone().strftime("%Y-%m-%dT%H:%M:%S%z"),
    }


def _resumo(meta: dict[str, Any]) -> str:
    """summary.txt curto e legível."""
    linhas = [
        f"RUN_ID:   {meta['run_id']}",
        f"MODELO:   {meta['modelo']}",
        f"SEED:     {meta['seed']}",
    ]
    ds = meta.get("dataset") or {}
    for k in ("n_rows", "train_rows", "valid_rows", "test_rows"):
        if k in ds:
            linhas.append(f"{k.upper():9s} {ds[k]:,}")
    if meta.get("duracao_s") is not None:
        linhas.append(f"DURACAO:  {meta['duracao_s']:.1f}s")

    if meta.get("metricas"):
        linhas.append("")
        linhas.append("MÉTRICAS:")
        for k, v in meta["metricas"].items():
            linhas.append(f"  {k:20s} {v:.4f}" if isinstance(v, float)
                          else f"  {k:20s} {v}")

    if meta.get("parametros"):
        linhas.append("")
        linhas.append("PARÂMETROS:")
        for k, v in meta["parametros"].items():
            linhas.append(f"  {k:20s} {v}")

    if meta.get("notas"):
        linhas.append("")
        linhas.append(f"NOTAS: {meta['notas']}")

    linhas.append("")
    linhas.append(f"TIMESTAMP_UTC: {meta['timestamp']['utc']}")
    return "\n".join(linhas) + "\n"

def _versoes() -> dict[str, str | None]:
    """
    Retorna as versoes fundamentais da execucao.
    """
    pacotes = [
        "numpy",
        "pandas",
        "pyarrow",
        "scikit-learn",
        "scipy",
        "matplotlib",
        "seaborn",
    ]

    resultado = {
        "python": platform.python_version(),
    }

    for pacote in pacotes:
        try:
            resultado[pacote] = (
                metadata.version(pacote)
            )
        except metadata.PackageNotFoundError:
            resultado[pacote] = None

    return resultado


def _git_info() -> dict[str, str | bool | None]:
    """
    Retorna commit, branch e estado da arvore de trabalho.
    """

    def executar_git(
        argumentos: list[str],
    ) -> str | None:
        try:
            processo = subprocess.run(
                ["git"] + argumentos,
                cwd=C.ROOT_DIR,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
        except OSError:
            return None

        if processo.returncode != 0:
            return None

        return processo.stdout.strip()

    status = executar_git(
        ["status", "--porcelain"]
    )

    return {
        "commit": executar_git(
            ["rev-parse", "HEAD"]
        ),
        "branch": executar_git(
            ["branch", "--show-current"]
        ),
        "dirty": (
            bool(status)
            if status is not None
            else None
        ),
    }


def _env_info() -> dict[str, str | bool]:
    """
    Retorna informacoes nao sensiveis do ambiente.
    """
    return {
        "python_executable": sys.executable,
        "python_version": (
            platform.python_version()
        ),
        "platform": platform.platform(),
        "cwd": str(Path.cwd()),
        "ci": bool(
            os.getenv("CI")
            or os.getenv("GITHUB_ACTIONS")
        ),
    }

# ---------------------------------------------------------------------------
# Núcleo
# ---------------------------------------------------------------------------

def registrar_execucao(
    modelo: str,
    *,
    seed: int | None = None,
    parametros: dict[str, Any] | None = None,
    dataset: dict[str, Any] | None = None,
    features: dict[str, Any] | None = None,
    metricas: dict[str, Any] | None = None,
    duracao_s: float | None = None,
    notas: str | None = None,
    run_id: str | None = None,
    output_dir: Path | None = None,
) -> Path:
    """Grava metadata.json + summary.txt em outputs/runs/<RUN_ID>/."""
    base = Path(
    output_dir
    if output_dir is not None
    else RUNS_DIR
    )

    if run_id is None:
        run_id = gerar_run_id(
            modelo=modelo,
            base_dir=base,
        )

    pasta = base / run_id

    pasta.mkdir(
        parents=True,
        exist_ok=False,
    )

    meta: dict[str, Any] = {
        "run_id": pasta.name,
        "timestamp": _agora(),
        "modelo": modelo,
        "seed": (
            seed
            if seed is not None
            else C.SEED
        ),
        "duracao_s": duracao_s,
        "parametros": parametros or {},
        "dataset": dataset or {},
        "features": features or {},
        "metricas": metricas or {},
        "notas": notas,
        "versoes": _versoes(),
        "git": _git_info(),
        "env": _env_info(),
        "supervised_yaml_sha256": (
            C.supervised_yaml_sha256()
        ),
    }

    (pasta / "metadata.json").write_text(
            json.dumps(meta, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
    )
    (pasta / "summary.txt").write_text(_resumo(meta), encoding="utf-8")

    print(f"[reproducibility] run registrado em: {pasta}")
    return pasta

def listar_runs(
    output_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """
    Lista os metadados das execucoes registradas.

    Cada item retornado corresponde ao conteudo de um
    metadata.json e inclui tambem o caminho da pasta.
    """
    raiz = Path(
        output_dir
        if output_dir is not None
        else RUNS_DIR
    )

    if not raiz.exists():
        return []

    runs: list[dict[str, Any]] = []

    for pasta in raiz.iterdir():
        if not pasta.is_dir():
            continue

        metadata_path = (
            pasta / "metadata.json"
        )

        if not metadata_path.exists():
            continue

        try:
            meta = json.loads(
                metadata_path.read_text(
                    encoding="utf-8"
                )
            )
        except (
            json.JSONDecodeError,
            OSError,
        ):
            continue

        meta["pasta"] = str(pasta)

        runs.append(meta)

    return sorted(
        runs,
        key=lambda item: str(
            item.get("run_id", "")
        ),
        reverse=True,
    )


def carregar_run(
    run: str | Path,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """
    Carrega o metadata.json de uma execucao.
    """
    caminho = Path(run)

    if not caminho.is_absolute():
        raiz = Path(
            output_dir or RUNS_DIR
        )

        caminho = (
            raiz / caminho
        )

    metadata_path = (
        caminho / "metadata.json"
    )

    if not metadata_path.exists():
        raise FileNotFoundError(
            "metadata.json nao encontrado em "
            f"{caminho}"
        )

    texto = metadata_path.read_text(
        encoding="utf-8"
    )

    return json.loads(texto)
# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------

class Run:
    """with Run(modelo="logistic", parametros={"C": 1.0}) as r: ..."""

    def __init__(
        self,
        modelo: str,
        *,
        seed: int | None = None,
        parametros: dict[str, Any] | None = None,
        dataset: dict[str, Any] | None = None,
        features: dict[str, Any] | None = None,
        notas: str | None = None,
        output_dir: Path | None = None,
    ) -> None:
        self.modelo      = modelo
        self.seed        = seed
        self.parametros  = dict(parametros or {})
        self.dataset     = dict(dataset or {})
        self.features    = dict(features or {})
        self.notas       = notas
        self.output_dir  = output_dir
        self._metricas:  dict[str, Any] = {}
        self._inicio:    float | None = None
        self.pasta:      Path | None = None

    def metrica(self, **kwargs: Any) -> "Run":
        self._metricas.update(kwargs)
        return self

    def anotar(self, texto: str) -> "Run":
        self.notas = f"{self.notas}\n{texto}" if self.notas else texto
        return self

    def add_dataset(self, **kwargs: Any) -> "Run":
        self.dataset.update(kwargs)
        return self

    def __enter__(self) -> "Run":
        self._inicio = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        duracao = time.perf_counter() - self._inicio if self._inicio else None
        self.pasta = registrar_execucao(
            modelo=self.modelo,
            seed=self.seed,
            parametros=self.parametros,
            dataset=self.dataset,
            features=self.features,
            metricas=self._metricas,
            duracao_s=duracao,
            notas=self.notas,
            output_dir=self.output_dir,
        )
        return False  # não suprime exceção
```

## `src/utils/storage.py`

- SHA-256: `426643c1972a121473a8806dc417c6c92f489facdbc004482cfc7403366467d7`
- Bytes: `4155`

```python
import os

import pandas as pd
import requests

from src.utils.env import PROCESSED, get_secret
from src.utils import config as C


PARQUET_MAGIC = b"PAR1"


def _token():
    try:
        return get_secret("GITHUB_TOKEN")
    except Exception:
        return os.environ.get("GITHUB_TOKEN")


def _download(url, dest, headers=None, expected_magic=None):
    tmp = dest.with_suffix(".part")

    with requests.get(
        url,
        headers=headers or {},
        stream=True,
        timeout=60,
        allow_redirects=True,
    ) as r:
        r.raise_for_status()

        ctype = r.headers.get("content-type", "").lower()
        if "text/html" in ctype or "application/json" in ctype:
            # Lê só o comecinho pra mostrar no erro
            preview = next(r.iter_content(256), b"")
            tmp.unlink(missing_ok=True)
            raise RuntimeError(
                f"Download retornou {ctype!r} em vez de binário. "
                f"URL: {url}\n"
                f"Primeiros bytes: {preview[:80]!r}"
            )

        total = int(r.headers.get("content-length", 0))
        done = 0
        first_bytes = b""

        with open(tmp, "wb") as f:
            for chunk in r.iter_content(8 * 1024 * 1024):
                if not first_bytes:
                    first_bytes = chunk[:16]
                f.write(chunk)
                done += len(chunk)
                if total:
                    print(
                        f"\rBaixando: {done / 1e6:.0f}/"
                        f"{total / 1e6:.0f} MB",
                        end="",
                        flush=True,
                    )
    print()

    if expected_magic and not first_bytes.startswith(expected_magic):
        tmp.unlink(missing_ok=True)
        raise RuntimeError(
            f"Arquivo baixado não é válido. "
            f"Esperado começar com {expected_magic!r}, "
            f"recebido {first_bytes[:16]!r}. "
            f"URL: {url}"
        )

    tmp.replace(dest)


def _private_asset_url(token):
    h = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    url = (
        f"https://api.github.com/repos/{C.GITHUB_REPO}/releases/tags/"
        f"{C.DATA_VERSION}"
    )
    r = requests.get(url, headers=h, timeout=30)
    r.raise_for_status()

    assets = r.json().get("assets", [])
    asset = next(
        (a for a in assets if a["name"] == C.PARQUET_NAME),
        None,
    )
    if asset is None:
        nomes = [a["name"] for a in assets]
        raise RuntimeError(
            f"Asset {C.PARQUET_NAME!r} não encontrado na release "
            f"{C.DATA_VERSION!r}. Disponíveis: {nomes}"
        )
    return asset["url"]


def get_parquet(force=False):
    folder = PROCESSED / C.DATA_VERSION
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / C.PARQUET_NAME

    if path.exists() and not force:
        return path

    # Se forçar, remove o arquivo antigo (pode estar corrompido)
    if force and path.exists():
        path.unlink()

    public_url = (
        f"https://github.com/{C.GITHUB_REPO}/releases/download/"
        f"{C.DATA_VERSION}/{C.PARQUET_NAME}"
    )

    try:
        _download(
            public_url,
            path,
            expected_magic=PARQUET_MAGIC,
        )
    except (requests.HTTPError, RuntimeError):
        token = _token()
        if not token:
            raise RuntimeError(
                "Download falhou. Repositório privado ou asset inválido? "
                "Cadastre o segredo GITHUB_TOKEN."
            )

        h = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/octet-stream",
        }
        _download(
            _private_asset_url(token),
            path,
            h,
            expected_magic=PARQUET_MAGIC,
        )

    return path


def read_srag(columns=None, filters=None):
    return pd.read_parquet(
        get_parquet(),
        columns=columns,
        filters=filters,
    )
```

## `tests/conftest.py`

- SHA-256: `219617a1f94edfe0857f023b753b9f956257f30ddc2326f196167170e1a24954`
- Bytes: `1899`

```python
"""
Fixtures compartilhadas e marcação de testes.

Marcadores:
    slow  → testes que fazem I/O pesado (download/leitura do Parquet completo)
    net   → testes que exigem acesso à internet

Uso:
    pytest                       # só testes rápidos
    pytest -m slow               # só testes lentos
    pytest -m "not slow"         # idem ao primeiro
    pytest -m "slow and net"     # testes lentos que precisam de rede
"""

from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.utils import env, config as C  # noqa: E402


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: teste lento (I/O pesado)")
    config.addinivalue_line("markers", "net:  teste que exige internet")


# ---------------------------------------------------------------------------
# Fixtures de caminhos
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def root_dir() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def processed_dir() -> Path:
    return env.PROCESSED


@pytest.fixture(scope="session")
def parquet_disponivel() -> Path | None:
    """
    Retorna o primeiro Parquet de SRAG encontrado, ou None.

    Ordem de preferência:
        1) data/processed/dados-v1/srag.parquet   (release oficial)
        2) data/processed/srag_amostra.parquet    (extração local)
        3) data/raw/*.parquet                     (baixado por extracao.py)
    """
    candidatos = [
        env.PROCESSED / C.DATA_VERSION / C.PARQUET_NAME,
        env.PROCESSED / "srag_amostra.parquet",
    ]
    candidatos += sorted((env.RAW).glob("*.parquet"))

    for p in candidatos:
        if p.exists():
            return p
    return None
```

## `tests/test_config.py`

- SHA-256: `b04ffa5dc6626a51ba5d483e9da8fbcc8e214be6a6366ec5dfe5aa6dd51241a3`
- Bytes: `5890`

```python
"""
Verifica que o ambiente e a configuracao estao integros.

Estes testes sao rapidos e nao fazem I/O pesado.
Devem rodar em toda validacao local e em CI.
"""

import ast

from pathlib import Path
import pytest

from src.utils import config as C
from src.utils import env


def test_root_dir_existe():
    assert C.ROOT_DIR.exists()
    assert C.ROOT_DIR.is_dir()


def test_root_dir_calculado_a_partir_do_arquivo():
    esperado = Path(C.__file__).resolve().parents[2]

    assert C.ROOT_DIR == esperado


@pytest.mark.parametrize(
    "chave",
    [
        "DATA_DIR",
        "RAW_DIR",
        "PROCESSED_DIR",
        "REPORTS_DIR",
        "MODELS_DIR",
    ],
)
def test_diretorios_derivam_da_raiz(chave):
    """
    Os diretorios do projeto devem derivar de ROOT_DIR.

    O caminho absoluto pode conter C:/Users ou OneDrive porque
    esse pode ser o local real do clone. O que nao pode existir
    e um caminho pessoal gravado diretamente em config.py.
    """
    valor = getattr(C, chave)

    assert isinstance(valor, Path)

    assert valor.is_absolute(), (
        f"{chave} deveria ser um caminho absoluto."
    )

    assert C.ROOT_DIR in valor.parents, (
        f"{chave}={valor} nao deriva de "
        f"ROOT_DIR={C.ROOT_DIR}"
    )


def test_config_nao_contem_caminho_pessoal_hardcoded():
    """
    Examina somente atribuicoes de constantes relacionadas
    a caminhos.

    Comentarios, docstrings e mensagens explicativas podem
    mencionar exemplos como C:/Users ou /home sem representar
    uma configuracao real do projeto.
    """
    caminho_config = Path(C.__file__)

    fonte = caminho_config.read_text(
        encoding="utf-8"
    )

    arvore = ast.parse(
        fonte,
        filename=str(caminho_config),
    )

    nomes_de_caminho = {
        "ROOT_DIR",
        "DATA_DIR",
        "RAW_DIR",
        "PROCESSED_DIR",
        "TREINO_DIR",
        "CONFIGS_DIR",
        "MODELS_DIR",
        "OUTPUTS_DIR",
        "RUNS_DIR",
        "LOGS_DIR",
        "REPORTS_DIR",
        "FIGURES_DIR",
        "TABLES_DIR",
        "PREDICTIONS_DIR",
        "SUPERVISED_YAML",
    }

    proibidos = [
        "c:/users/",
        "/home/",
        "/users/",
        "onedrive - pfizer",
    ]

    problemas = []

    for no in ast.walk(arvore):
        nome_alvo = None
        valor = None

        if isinstance(no, ast.Assign):
            if len(no.targets) != 1:
                continue

            alvo = no.targets[0]

            if isinstance(alvo, ast.Name):
                nome_alvo = alvo.id
                valor = no.value

        elif isinstance(no, ast.AnnAssign):
            alvo = no.target

            if isinstance(alvo, ast.Name):
                nome_alvo = alvo.id
                valor = no.value

        if nome_alvo not in nomes_de_caminho:
            continue

        if valor is None:
            continue

        valores_textuais = [
            item.value
            for item in ast.walk(valor)
            if isinstance(item, ast.Constant)
            and isinstance(item.value, str)
        ]

        for texto in valores_textuais:
            texto_normalizado = (
                texto
                .replace("\\", "/")
                .lower()
            )

            encontrados = [
                termo
                for termo in proibidos
                if termo in texto_normalizado
            ]

            if encontrados:
                problemas.append(
                    {
                        "constante": nome_alvo,
                        "valor": texto,
                        "termos": encontrados,
                    }
                )

    assert not problemas, (
        "Foram encontrados caminhos pessoais hard-coded "
        "em constantes de configuracao: "
        f"{problemas}"
    )


def test_seed_definido():
    assert isinstance(C.SEED, int)
    assert C.SEED == 42


def test_random_state_igual_ao_seed():
    assert C.RANDOM_STATE == C.SEED


def test_repo_e_data_version_definidos():
    assert C.GITHUB_REPO
    assert "/" in C.GITHUB_REPO
    assert C.DATA_VERSION
    assert C.PARQUET_NAME.endswith(".parquet")


def test_srag_parquet_url_nao_vazia():
    url = C.srag_parquet_url()

    assert isinstance(url, str)
    assert url.strip()
    assert url.startswith(("http://", "https://"))


def test_parametros_http_razoaveis():
    assert C.HTTP_TIMEOUT > 0
    assert C.HTTP_TENTATIVAS >= 1
    assert C.HTTP_BACKOFF >= 0


def test_env_aponta_para_mesma_raiz():
    assert env.ROOT == C.ROOT_DIR


def test_env_diretorios_padrao_existem():
    env.garantir_diretorios()

    caminhos = [
        env.RAW,
        env.PROCESSED,
        env.TREINO,
        env.FIGURES,
    ]

    for caminho in caminhos:
        assert caminho.exists(), (
            f"{caminho} nao foi criado por "
            "env.garantir_diretorios()"
        )

        assert caminho.is_dir(), (
            f"{caminho} existe, mas nao e um diretorio."
        )


def test_env_resumo_nao_quebra():
    texto = env.resumo()

    assert "ROOT_DIR" in texto
    assert "ENV" in texto


def test_get_secret_obrigatorio_levanta_erro(
    monkeypatch,
):
    nome = "VAR_QUE_NAO_EXISTE_XYZ"

    monkeypatch.delenv(
        nome,
        raising=False,
    )

    with pytest.raises(
        RuntimeError,
        match=nome,
    ):
        env.get_secret(nome)


def test_get_secret_opcional_retorna_none(
    monkeypatch,
):
    nome = "VAR_OPCIONAL_XYZ"

    monkeypatch.delenv(
        nome,
        raising=False,
    )

    assert env.get_secret(
        nome,
        obrigatorio=False,
    ) is None
```

## `tests/test_leakage.py`

- SHA-256: `d3825fac4787ead105b821382f2a928dcfcbb1c70fd3e6bd8b09ea809855cb4d`
- Bytes: `4817`

```python
"""
Testes anti-vazamento de dados.

Os testes protegem contra:
- inclusao do alvo no conjunto de features;
- inclusao de colunas posteriores ao desfecho;
- quebra da ordem temporal entre treino, validacao e holdout;
- duplicacao de identificadores quando houver uma chave adequada.
"""

import pandas as pd
import pytest

from src.utils import config as C


COLUNAS_PROIBIDAS = {
    "evolucao",
    "evolucao_covid19",
    "dt_evolucao",
    "dt_encerramento",
    "classificacao_final",
    "criterio_confirmacao",
    "sorologia",
    "pcr",
}


def test_config_features_proibidas_definidas():
    configuracao = C.carregar_supervised()

    proibidas_config = set(
        configuracao["features"]["proibidas"]
    )

    faltantes = (
        COLUNAS_PROIBIDAS
        - proibidas_config
    )

    assert not faltantes, (
        "As seguintes colunas proibidas nao estao "
        f"declaradas no YAML: {faltantes}"
    )


def test_pipeline_expoe_features_sem_alvo():
    from src.models import pipeline

    assert hasattr(pipeline, "FEATURES")

    features = set(pipeline.FEATURES)

    vazamento = (
        features
        & COLUNAS_PROIBIDAS
    )

    assert not vazamento, (
        "FEATURES contem colunas proibidas: "
        f"{vazamento}"
    )


def test_pipeline_nao_inclui_coluna_alvo():
    from src.models import pipeline

    features = set(pipeline.FEATURES)

    assert pipeline.ALVO not in features


def test_split_temporal_3way_respeita_ordem():
    from src.evaluation.temporal import (
        split_temporal_3way,
    )

    df = pd.DataFrame(
        {
            "dt_notific": pd.date_range(
                "2020-01-01",
                periods=100,
                freq="D",
            ),
            "valor": range(100),
        }
    )

    treino, validacao, holdout = (
        split_temporal_3way(
            df,
            coluna_tempo="dt_notific",
            frac_treino=0.70,
            frac_validacao=0.15,
        )
    )

    assert not treino.empty
    assert not validacao.empty
    assert not holdout.empty

    assert (
        treino["dt_notific"].max()
        <= validacao["dt_notific"].min()
    )

    assert (
        validacao["dt_notific"].max()
        <= holdout["dt_notific"].min()
    )


def test_temporal_split_bloqueia_holdout():
    from src.evaluation.temporal import (
        TemporalSplit,
    )

    df = pd.DataFrame(
        {
            "dt_notific": pd.date_range(
                "2020-01-01",
                periods=100,
                freq="D",
            ),
            "valor": range(100),
        }
    )

    split = TemporalSplit(
        df=df,
        coluna_tempo="dt_notific",
    )

    assert not split.holdout_liberado

    with pytest.raises(RuntimeError):
        split.holdout()

    split.concluir_selecao()

    assert split.holdout_liberado
    assert not split.holdout().empty


def test_dataset_sem_identificadores_duplicados(
    parquet_disponivel,
):
    """
    Testa duplicidade somente se houver uma coluna que possa
    funcionar como identificador da notificacao.

    UF e data nao formam uma chave unica e nao devem ser usadas
    isoladamente para declarar duplicacao de registros.
    """
    if parquet_disponivel is None:
        pytest.skip("Parquet nao disponivel.")

    import pyarrow.parquet as pq

    schema = pq.read_schema(
        parquet_disponivel
    )

    colunas = set(schema.names)

    candidatas = [
        "nu_notific",
        "numero_notificacao",
        "id_notificacao",
        "id",
    ]

    coluna_id = next(
        (
            coluna
            for coluna in candidatas
            if coluna in colunas
        ),
        None,
    )

    if coluna_id is None:
        pytest.skip(
            "O Parquet nao possui uma coluna identificadora "
            "adequada para o teste de duplicidade."
        )

    df = pd.read_parquet(
        parquet_disponivel,
        columns=[coluna_id],
    )

    ids = (
        df[coluna_id]
        .dropna()
        .astype("string")
        .str.strip()
    )

    ids = ids[
        ids.ne("")
    ]

    if ids.empty:
        pytest.skip(
            f"A coluna {coluna_id} nao possui "
            "identificadores validos."
        )

    quantidade_duplicada = int(
        ids.duplicated().sum()
    )

    taxa_duplicada = (
        quantidade_duplicada
        / len(ids)
    )

    assert taxa_duplicada < 0.05, (
        "Alta taxa de identificadores duplicados em "
        f"{coluna_id}: "
        f"{quantidade_duplicada}/{len(ids)} "
        f"({taxa_duplicada:.1%})"
    )
```

## `tests/test_pipeline.py`

- SHA-256: `3def0c1cddfbe4963db897f5384622ecd9f80279588f4a9784f49f179a5abf80`
- Bytes: `3808`

```python
"""
Testes do pipeline de ingestão: extracao.py, read_srag, csv_to_parquet.

Marcados como `slow` porque tocam arquivos grandes.
"""

from pathlib import Path

import pandas as pd
import pytest

from src.utils import config as C, env


pytestmark = pytest.mark.slow


# ---------------------------------------------------------------------------
# coletar_amostra — download do Parquet
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Leitura do Parquet local
# ---------------------------------------------------------------------------

def test_read_srag_retorna_dataframe(
    parquet_disponivel,
):
    """
    Valida o caminho oficial de leitura local do projeto.
    """
    if parquet_disponivel is None:
        pytest.skip(
            "Parquet nao disponivel."
        )

    from src.utils.storage import read_srag

    df = read_srag(
        columns=[
            "sg_uf",
            "dt_notific",
        ]
    )

    assert isinstance(
        df,
        pd.DataFrame,
    )

    assert not df.empty

    assert {
        "sg_uf",
        "dt_notific",
    }.issubset(
        set(df.columns)
    )


def test_get_parquet_reaproveita_arquivo(
    parquet_disponivel,
):
    """
    get_parquet com force igual a False deve reutilizar
    o arquivo existente.
    """
    if parquet_disponivel is None:
        pytest.skip(
            "Parquet nao disponivel."
        )

    from src.utils.storage import get_parquet

    caminho_1 = Path(
        get_parquet(force=False)
    )

    estado_1 = caminho_1.stat()

    caminho_2 = Path(
        get_parquet(force=False)
    )

    estado_2 = caminho_2.stat()

    assert (
        caminho_1.resolve()
        == caminho_2.resolve()
    )

    assert (
        estado_1.st_mtime_ns
        == estado_2.st_mtime_ns
    )

    assert (
        estado_1.st_size
        == estado_2.st_size
    )


# ---------------------------------------------------------------------------
# csv_to_parquet
# ---------------------------------------------------------------------------

def test_csv_to_parquet_round_trip(tmp_path):
    """CSV pequeno → Parquet → lê de volta e confere."""
    from src.data.extracao import csv_to_parquet

    csv_path = tmp_path / "amostra.csv"
    parquet_path = tmp_path / "amostra.parquet"

    df_orig = pd.DataFrame(
        {
            "sg_uf": ["SP", "RJ", "MG"],
            "dt_notific": ["2024-01-01", "2024-01-02", "2024-01-03"],
        }
    )
    df_orig.to_csv(csv_path, index=False, encoding="utf-8-sig")

    # csv_to_parquet usa C.COLS e C.CSV_SEP; como C.COLS = None, lê tudo
    csv_to_parquet(csv_path=csv_path, out_path=parquet_path)

    assert parquet_path.exists()
    df_lido = pd.read_parquet(parquet_path)
    assert len(df_lido) == len(df_orig)
    assert set(df_lido.columns) >= set(df_orig.columns)


def test_csv_to_parquet_erro_quando_csv_inexistente(tmp_path):
    from src.data.extracao import csv_to_parquet

    with pytest.raises(FileNotFoundError):
        csv_to_parquet(
            csv_path=tmp_path / "nao_existe.csv",
            out_path=tmp_path / "saida.parquet",
        )


# ---------------------------------------------------------------------------
# Diretórios
# ---------------------------------------------------------------------------

def test_raw_dir_foi_criado():
    env.garantir_diretorios()

    assert env.RAW.exists()
    assert env.RAW.is_dir()


def test_processed_dir_foi_criado():
    env.garantir_diretorios()

    assert env.PROCESSED.exists()
    assert env.PROCESSED.is_dir()
```

## `tests/test_reproducibility.py`

- SHA-256: `70624f0cfaf97c9b8a2fb1e0763d4debc34a3ab0946b648b2d2ae5ca8485a807`
- Bytes: `2451`

```python
"""Testes do registro de execuções."""

import json
from pathlib import Path

import pytest

from src.utils import reproducibility as R


def test_registrar_execucao_cria_pasta(tmp_path):
    pasta = R.registrar_execucao(
        modelo="teste",
        seed=42,
        parametros={"C": 1.0},
        dataset={"nome": "srag", "n_rows": 100},
        metricas={"auc": 0.5},
        duracao_s=1.23,
        output_dir=tmp_path,
    )
    assert pasta.exists()
    assert (pasta / "metadata.json").exists()
    assert (pasta / "summary.txt").exists()


def test_metadata_tem_campos_obrigatorios(tmp_path):
    pasta = R.registrar_execucao(
        modelo="teste",
        seed=7,
        parametros={"x": 1},
        metricas={"auc": 0.9},
        output_dir=tmp_path,
    )
    meta = json.loads((pasta / "metadata.json").read_text(encoding="utf-8"))

    for chave in ("run_id", "timestamp", "modelo", "seed",
                  "parametros", "dataset", "metricas",
                  "versoes", "git", "env", "duracao_s"):
        assert chave in meta

    assert meta["seed"] == 7
    assert meta["modelo"] == "teste"
    assert meta["metricas"]["auc"] == 0.9


def test_run_context_manager(tmp_path):
    with R.Run(modelo="ctx", seed=1, output_dir=tmp_path) as r:
        r.metrica(auc=0.77)
        r.anotar("nota de teste")

    assert r.pasta is not None
    meta = json.loads((r.pasta / "metadata.json").read_text(encoding="utf-8"))
    assert meta["metricas"]["auc"] == 0.77
    assert "nota de teste" in meta["notas"]
    assert meta["duracao_s"] is not None


def test_run_id_unico(tmp_path):
    a = R.gerar_run_id(modelo="dup", base_dir=tmp_path)
    (tmp_path / a).mkdir()
    b = R.gerar_run_id(modelo="dup", base_dir=tmp_path)
    assert a != b


def test_listar_e_carregar(tmp_path):
    R.registrar_execucao(modelo="a", output_dir=tmp_path)
    R.registrar_execucao(modelo="b", output_dir=tmp_path)

    runs = R.listar_runs(output_dir=tmp_path)
    assert len(runs) == 2

    meta = R.carregar_run(runs[0]["run_id"], output_dir=tmp_path)
    assert meta["modelo"] in {"a", "b"}


def test_seed_padrao_vem_do_config(tmp_path):
    from src.utils import config as C

    pasta = R.registrar_execucao(modelo="seed_default", output_dir=tmp_path)
    meta = json.loads((pasta / "metadata.json").read_text(encoding="utf-8"))
    assert meta["seed"] == C.SEED
```

## `tests/test_smoke.py`

- SHA-256: `fefab2c8801a13fcec3f00a6570fb54932b027011fd70f9cd77a3cdf64169bee`
- Bytes: `4133`

```python
"""
Smoke tests: o dataset existe, abre, tem colunas e registros?

Todos os testes de I/O estão marcados como `slow`.
Rode com:  pytest -m slow
"""

import pandas as pd
import pytest

from src.utils import config as C


pytestmark = pytest.mark.slow


# ---------------------------------------------------------------------------
# Existência e integridade do arquivo
# ---------------------------------------------------------------------------

def test_parquet_existe(parquet_disponivel):
    if parquet_disponivel is None:
        pytest.skip(
            "Nenhum Parquet encontrado. Rode 00_acesso_dados_parquet.ipynb "
            "ou 01_extracao.ipynb primeiro."
        )
    assert parquet_disponivel.exists()
    assert parquet_disponivel.stat().st_size > 0


def test_parquet_tem_magic_bytes(parquet_disponivel):
    if parquet_disponivel is None:
        pytest.skip("Parquet não disponível.")
    with open(parquet_disponivel, "rb") as f:
        magic = f.read(4)
    assert magic == b"PAR1", f"Arquivo não é Parquet válido (magic={magic!r})"


# ---------------------------------------------------------------------------
# Abertura e esquema
# ---------------------------------------------------------------------------

def test_parquet_abre(parquet_disponivel):
    if parquet_disponivel is None:
        pytest.skip("Parquet não disponível.")
    import pyarrow.parquet as pq

    schema = pq.read_schema(parquet_disponivel)
    assert len(schema.names) > 0


def test_parquet_tem_colunas_esperadas(parquet_disponivel):
    if parquet_disponivel is None:
        pytest.skip("Parquet não disponível.")
    import pyarrow.parquet as pq

    schema = pq.read_schema(parquet_disponivel)
    colunas = set(schema.names)

    # Colunas mínimas que o projeto espera encontrar no SRAG.
    # Ajuste aqui conforme o dicionário de dados for consolidado.
    esperadas = {"sg_uf", "dt_notific"}
    faltando = esperadas - colunas

    assert not faltando, f"Colunas ausentes: {faltando}"


# ---------------------------------------------------------------------------
# Leitura e registros
# ---------------------------------------------------------------------------

def test_parquet_tem_registros(parquet_disponivel):
    if parquet_disponivel is None:
        pytest.skip("Parquet não disponível.")
    df = pd.read_parquet(parquet_disponivel, columns=["sg_uf"])
    assert len(df) > 0


def test_leitura_de_uma_coluna(parquet_disponivel):
    if parquet_disponivel is None:
        pytest.skip("Parquet não disponível.")
    df = pd.read_parquet(parquet_disponivel, columns=["sg_uf"])
    assert df.shape[1] == 1
    assert "sg_uf" in df.columns


def test_produz_saida_pequena(parquet_disponivel):
    """Confirma que conseguimos produzir uma saída minúscula — o 'smoke' final."""
    if parquet_disponivel is None:
        pytest.skip("Parquet não disponível.")
    df = pd.read_parquet(parquet_disponivel, columns=["sg_uf"]).head(10)
    assert len(df) == 10
    # Uma contagem simples, só pra exercitar o DataFrame
    contagem = df["sg_uf"].value_counts()
    assert contagem.sum() == 10


# ---------------------------------------------------------------------------
# storage.py
# ---------------------------------------------------------------------------

def test_storage_read_srag(parquet_disponivel):
    if parquet_disponivel is None:
        pytest.skip("Parquet não disponível.")
    from src.utils import storage

    df = storage.read_srag(columns=["sg_uf"])
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert "sg_uf" in df.columns


def test_storage_read_srag_com_filtro(parquet_disponivel):
    if parquet_disponivel is None:
        pytest.skip("Parquet não disponível.")
    from src.utils import storage

    df = storage.read_srag(
        columns=["sg_uf"],
        filters=[("sg_uf", "==", "SP")],
    )
    if len(df) == 0:
        pytest.skip("Nenhum registro de SP no dataset.")
    assert (df["sg_uf"] == "SP").all()
```

## `tools/collect_repo_context.py`

- SHA-256: `daee8ca759323c54ca5dbcfd305f4f095a92f7c0926927975adb8beb6981c8c0`
- Bytes: `13119`

```python
#!/usr/bin/env python
"""Gera um pacote seguro de contexto técnico do repositório para pessoas e IAs.

As pastas data/, models/, outputs/ e logs/ são excluídas
somente quando estão na raiz. Módulos como src/data e
src/models permanecem incluídos no inventário.

Uso, na raiz do Git:
    python tools/collect_repo_context.py

Saídas:
    docs/ai_context/repo_inventory.json
    docs/ai_context/repo_inventory.md
    docs/ai_context/pip_inspect.json
    docs/ai_context/pip_freeze.txt
    docs/ai_context/git_tracked_files.txt

O script não lê valores de .env, não inclui o conteúdo de dados/artefatos, e exclui
.venv, .git, caches, outputs e arquivos grandes.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.cwd().resolve()
OUT = ROOT / "docs" / "ai_context"
OUT.mkdir(parents=True, exist_ok=True)

EXCLUDED_DIR_NAMES_ANYWHERE = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".ipynb_checkpoints",
    "node_modules",
    "dist",
    "build",
}

EXCLUDED_ROOT_DIRS = {
    "data",
    "outputs",
    "models",
    "logs",
}
TEXT_SUFFIXES = {
    ".py", ".md", ".txt", ".yaml", ".yml", ".toml", ".ini", ".cfg",
    ".json", ".ipynb", ".ps1", ".bat", ".sh", ".sql",
}
CODE_SUFFIXES = {".py", ".ipynb"}
MAX_TEXT_BYTES = 1_000_000
SECRET_NAME = re.compile(r"(token|secret|password|passwd|api[_-]?key|credential)", re.I)


def run(cmd: list[str]) -> dict[str, Any]:
    try:
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, errors="replace")
        return {"command": cmd, "returncode": p.returncode,
                "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}
    except Exception as exc:
        return {"command": cmd, "returncode": None, "stdout": "", "stderr": repr(exc)}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def excluded(path: Path) -> bool:
    """
    Exclui caches em qualquer nível, mas exclui data, models,
    outputs e logs somente quando forem pastas da raiz.

    Assim:
        data/processed/...       → excluído
        models/modelo.pkl        → excluído
        src/data/extracao.py     → incluído
        src/models/pipeline.py   → incluído
    """
    relative = path.relative_to(ROOT)
    parts = relative.parts

    if not parts:
        return False

    if any(
        part in EXCLUDED_DIR_NAMES_ANYWHERE
        for part in parts
    ):
        return True

    if parts[0] in EXCLUDED_ROOT_DIRS:
        return True

    return False


def tracked_files() -> list[Path]:
    result = run(["git", "ls-files", "-z"])
    if result["returncode"] == 0:
        return [ROOT / p for p in result["stdout"].split("\x00") if p]
    return [p for p in ROOT.rglob("*") if p.is_file() and not excluded(p)]


def safe_text(path: Path) -> str | None:
    if path.stat().st_size > MAX_TEXT_BYTES or path.suffix.lower() not in TEXT_SUFFIXES:
        return None
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding="latin-1")
        except Exception:
            return None
    except Exception:
        return None


def docstring(node: ast.AST) -> str | None:
    value = ast.get_docstring(node, clean=True)
    return value[:1200] if value else None


def signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    args = []
    positional = list(node.args.posonlyargs) + list(node.args.args)
    defaults_offset = len(positional) - len(node.args.defaults)
    for i, arg in enumerate(positional):
        prefix = "/" if node.args.posonlyargs and i == len(node.args.posonlyargs) else ""
        annotation = ast.unparse(arg.annotation) if arg.annotation else None
        item = arg.arg + (f": {annotation}" if annotation else "")
        if i >= defaults_offset:
            item += "=" + ast.unparse(node.args.defaults[i - defaults_offset])
        args.append(item)
        if prefix:
            args.append(prefix)
    if node.args.vararg:
        args.append("*" + node.args.vararg.arg)
    elif node.args.kwonlyargs:
        args.append("*")
    for arg, default in zip(node.args.kwonlyargs, node.args.kw_defaults):
        item = arg.arg
        if arg.annotation:
            item += ": " + ast.unparse(arg.annotation)
        if default is not None:
            item += "=" + ast.unparse(default)
        args.append(item)
    if node.args.kwarg:
        args.append("**" + node.args.kwarg.arg)
    ret = f" -> {ast.unparse(node.returns)}" if node.returns else ""
    return f"{node.name}({', '.join(args)}){ret}"


def analyze_python(path: Path) -> dict[str, Any]:
    text = safe_text(path)
    if text is None:
        return {"parse_error": "arquivo não textual ou muito grande"}
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        return {"parse_error": f"{exc.msg} linha {exc.lineno}"}

    imports, functions, classes, constants = [], [], [], []
    for node in tree.body:
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(("." * node.level) + (node.module or ""))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append({"name": node.name, "signature": signature(node),
                              "line": node.lineno, "docstring": docstring(node)})
        elif isinstance(node, ast.ClassDef):
            methods = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append({"name": item.name, "signature": signature(item),
                                    "line": item.lineno, "docstring": docstring(item)})
            classes.append({"name": node.name, "line": node.lineno,
                            "docstring": docstring(node), "methods": methods})
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    constants.append(target.id)
    return {"module_docstring": docstring(tree), "imports": sorted(set(imports)),
            "functions": functions, "classes": classes, "constants": constants}


def analyze_notebook(path: Path) -> dict[str, Any]:
    if path.stat().st_size == 0:
        return {
            "status": "placeholder",
            "empty": True,
            "cell_count": 0,
            "code_cells": 0,
            "markdown_cells": 0,
        }
    try:
        nb = json.loads(path.read_text(encoding="utf-8"))
        cells = nb.get("cells", [])
        return {
            "nbformat": nb.get("nbformat"),
            "kernel": nb.get("metadata", {}).get("kernelspec", {}),
            "language": nb.get("metadata", {}).get("language_info", {}),
            "cell_count": len(cells),
            "code_cells": sum(c.get("cell_type") == "code" for c in cells),
            "markdown_cells": sum(c.get("cell_type") == "markdown" for c in cells),
            "execution_counts": [c.get("execution_count") for c in cells if c.get("cell_type") == "code"],
        }
    except Exception as exc:
        return {"parse_error": repr(exc)}


def env_names_from_text(text: str) -> list[str]:
    patterns = [
        r"os\.getenv\([\"']([A-Za-z_][A-Za-z0-9_]*)",
        r"os\.environ(?:\.get)?\([\"']([A-Za-z_][A-Za-z0-9_]*)",
        r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}",
    ]
    found = set()
    for pattern in patterns:
        found.update(re.findall(pattern, text))
    return sorted(found)


def redact_config_preview(path: Path, text: str) -> str:
    if path.name == ".env" or SECRET_NAME.search(path.name):
        return "[conteúdo omitido por segurança]"
    lines = []
    for line in text.splitlines()[:250]:
        if "=" in line:
            key = line.split("=", 1)[0].strip()
            if SECRET_NAME.search(key):
                line = f"{key}=<REDACTED>"
        lines.append(line)
    return "\n".join(lines)


files = []
python_analysis = {}
notebooks = {}
env_vars = set()

for path in tracked_files():
    if not path.exists() or excluded(path):
        continue
    record = {
        "path": rel(path), "suffix": path.suffix.lower(),
        "size_bytes": path.stat().st_size, "sha256": sha256(path),
    }
    text = safe_text(path)
    if text is not None:
        record["line_count"] = len(text.splitlines())
        env_vars.update(env_names_from_text(text))
        if path.suffix.lower() in {".yaml", ".yml", ".toml", ".ini", ".cfg"}:
            record["preview_redacted"] = redact_config_preview(path, text)
    files.append(record)
    if path.suffix.lower() == ".py":
        python_analysis[rel(path)] = analyze_python(path)
    elif path.suffix.lower() == ".ipynb":
        notebooks[rel(path)] = analyze_notebook(path)

commands = {
    "git_status": run(["git", "status", "--short", "--branch"]),
    "git_remote": run(["git", "remote", "-v"]),
    "git_branches": run(["git", "branch", "--all", "--verbose", "--no-abbrev"]),
    "git_log": run(["git", "log", "--date=iso-strict", "--pretty=format:%H%x09%ad%x09%an%x09%s", "-n", "100"]),
    "git_tags": run(["git", "tag", "--list", "--sort=-creatordate"]),
    "git_submodules": run(["git", "submodule", "status"]),
    "python_version": run([sys.executable, "--version"]),
    "pip_check": run([sys.executable, "-m", "pip", "check"]),
}

pip_inspect = run([sys.executable, "-m", "pip", "inspect", "--local"])
if pip_inspect["returncode"] == 0:
    (OUT / "pip_inspect.json").write_text(pip_inspect["stdout"] + "\n", encoding="utf-8")
pip_freeze = run([sys.executable, "-m", "pip", "freeze"])
(OUT / "pip_freeze.txt").write_text(pip_freeze["stdout"] + "\n", encoding="utf-8")
(OUT / "git_tracked_files.txt").write_text("\n".join(sorted(f["path"] for f in files)) + "\n", encoding="utf-8")

inventory = {
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "root_name": ROOT.name,
    "python_executable": sys.executable,
    "python_version": sys.version,
    "platform": platform.platform(),
    "file_count": len(files),
    "files": sorted(files, key=lambda x: x["path"]),
    "python_analysis": python_analysis,
    "notebooks": notebooks,
    "environment_variable_names_only": sorted(env_vars),
    "commands": commands,
    "notes": [
        "Valores de variáveis de ambiente não são coletados.",
        "data/, outputs/, models/, logs/, .git/ e .venv/ são excluídos.",
        "Conteúdo integral dos arquivos não é copiado; são coletados estrutura, hashes e símbolos.",
    ],
}
(OUT / "repo_inventory.json").write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8")

md = []
md.append("# Inventário técnico do repositório\n")
md.append(f"Gerado em: `{inventory['generated_at_utc']}`  ")
md.append(f"Python: `{sys.version.split()[0]}`  ")
md.append(f"Executável: `{sys.executable}`  ")
md.append(f"Arquivos rastreados analisados: **{len(files)}**\n")
md.append("## Estado do Git\n```text\n" + commands["git_status"]["stdout"] + "\n```\n")
md.append("## Variáveis de ambiente referenciadas\n")
md.extend(f"- `{name}`" for name in sorted(env_vars))
md.append("\n## Arquivos Python e símbolos\n")
for path, info in sorted(python_analysis.items()):
    md.append(f"### `{path}`")
    if info.get("parse_error"):
        md.append(f"- Erro de parse: `{info['parse_error']}`")
        continue
    if info.get("module_docstring"):
        md.append(f"- Módulo: {info['module_docstring'].splitlines()[0]}")
    for item in info.get("functions", []):
        md.append(f"- Função L{item['line']}: `{item['signature']}`")
    for cls in info.get("classes", []):
        md.append(f"- Classe L{cls['line']}: `{cls['name']}`")
        for method in cls["methods"]:
            md.append(f"  - Método L{method['line']}: `{method['signature']}`")
md.append("\n## Notebooks\n")
for path, info in sorted(notebooks.items()):
    md.append(f"- `{path}`: {info}")
md.append("\n## Validação do ambiente\n")
md.append(f"- `pip check` return code: `{commands['pip_check']['returncode']}`")
if commands["pip_check"]["stdout"]:
    md.append("```text\n" + commands["pip_check"]["stdout"] + "\n```")
if commands["pip_check"]["stderr"]:
    md.append("```text\n" + commands["pip_check"]["stderr"] + "\n```")
(OUT / "repo_inventory.md").write_text("\n".join(md) + "\n", encoding="utf-8")

print(f"Inventário criado em: {OUT}")
for p in sorted(OUT.iterdir()):
    print(" -", p.relative_to(ROOT))
```

## `tools/update_project_reference.py`

- SHA-256: `776fb6d9689e52db9c67a02bd8b46d0315ac743394e4281a7de882dc1144355a`
- Bytes: `11493`

```python
#!/usr/bin/env python3
r"""One-command project reference generator.

Run from repository root:
    .\.venv\Scripts\python.exe tools\update_project_reference.py

Creates:
    docs/PROJECT_COMPLETE_REFERENCE.md
"""
from __future__ import annotations
import ast, hashlib, json, re, subprocess, tempfile
from datetime import datetime, timezone
from pathlib import Path

OUTPUT = Path("docs/PROJECT_COMPLETE_REFERENCE.md")
MAX_BYTES = 4_000_000
EXCLUDED_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".ipynb_checkpoints", "data", "outputs", "models", "logs", "node_modules"}
EXCLUDED_FILES = {".env", "paths.local.json", "pip_inspect-venv.json", OUTPUT.name}
TEXT_SUFFIXES = {".py", ".pyi", ".md", ".rst", ".txt", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".json", ".json5", ".sql", ".ps1", ".sh", ".bat", ".gitignore", ".gitattributes"}
SPECIAL_NAMES = {"README", "README.md", "LICENSE", "Makefile", "Dockerfile", "requirements.txt", "pyproject.toml", "pytest.ini"}
LANG = {".py":"python", ".pyi":"python", ".md":"markdown", ".rst":"rst", ".yaml":"yaml", ".yml":"yaml", ".toml":"toml", ".json":"json", ".json5":"json5", ".ini":"ini", ".cfg":"ini", ".sql":"sql", ".ps1":"powershell", ".sh":"bash", ".bat":"bat"}
ENV_RE = re.compile(r"(?:os\.getenv|os\.environ\.get|get_env|get_secret)\(\s*['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]")
SECRET_RE = re.compile(r"(?im)^(\s*[A-Za-z_][A-Za-z0-9_.-]*?(?:token|secret|password|passwd|pwd|api[_-]?key|private[_-]?key|credential)[A-Za-z0-9_.-]*\s*[:=]\s*)([^\n#]+)")
PRIVATE_KEY_RE = re.compile(r"-----BEGIN [^-]+ PRIVATE KEY-----.*?-----END [^-]+ PRIVATE KEY-----", re.DOTALL)

CONTEXT = '''# Project Complete Reference

> **Generated file. Do not edit manually.**  
> Update with `tools/update_project_reference.py`.

## 1. Project context

This is an academic retrospective machine-learning project using SRAG/SIVEP-Gripe data. The operational objective is to estimate risk of death from SRAG using only information plausibly available by hospital admission. The unit of analysis is an eligible notification used as a proxy for a hospital episode, not automatically a unique person.

The repository already contains reusable foundations for configuration, environment handling, Parquet access, basic preprocessing, target construction, preprocessing pipelines, baseline, logistic regression, gradient boosting, probability calibration, threshold selection, classification metrics, calibration diagnostics, error analysis, temporal validation, protected holdout access, experiment registration and automated tests.

## 2. Non-negotiable methodological rules

- Academic retrospective analysis, not a clinically validated decision tool.
- Do not make causal claims from predictive associations.
- Prediction time is hospital admission. Later information cannot be a feature.
- Current target contract: `evolucao == 2.0` is positive; `evolucao == 1.0` is negative; other values stay outside the primary binary target unless formally changed.
- Never use the final holdout to choose model, hyperparameters, calibration or threshold.
- Preserve temporal ordering. Do not silently replace temporal validation with random splitting.
- Data, trained models, outputs, local paths, `.env` and secrets do not belong in Git.
- Changes to cohort, target, features, split, seed, calibration, threshold or gates must update configuration, tests and documentation together.

## 3. Ways of working

1. Read this document before proposing code.
2. Search the API catalog and complete source sections before creating a function.
3. Notebooks orchestrate, explain and visualize. Reusable logic belongs in `src/`.
4. Experimental decisions belong in `configs/`.
5. Use `src/utils/storage.py` for the official Parquet contract.
6. Use `src/evaluation/temporal.py::TemporalSplit` for the final three-way workflow.
7. Reuse metrics and error analysis from `src/evaluation/`.
8. Use `src/utils/reproducibility.py::Run` instead of creating another logger.
9. A new public function requires an uncovered gap, typing, docstring and tests.
10. Review `git diff` and run relevant tests before integration.

## 4. Source precedence

1. Executable code and tests describe actual behavior.
2. `configs/supervised.yaml` describes approved or pending decisions and gates.
3. This generated reference combines the current codebase.
4. Older plans describe intent, not necessarily implementation.

## 5. Status labels

- **Implemented:** executable code exists.
- **Configured:** a value or rule exists in configuration.
- **Planned:** described but not confirmed in executable code.
- **Placeholder:** intentionally empty file reserved for later work.
- **Attention:** overlap, pending decision or technical risk.
'''

def git(root: Path, *args: str) -> str:
    p = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode:
        raise RuntimeError(p.stderr.strip() or "Git command failed")
    return p.stdout

def root_dir() -> Path:
    p = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode:
        raise RuntimeError("Run inside the Git repository.")
    return Path(p.stdout.strip()).resolve()

def tracked(root: Path) -> list[Path]:
    return sorted((Path(x) for x in git(root, "ls-files").splitlines() if x.strip()), key=lambda p: p.as_posix().lower())

def include(path: Path) -> bool:
    return not any(part in EXCLUDED_DIRS for part in path.parts) and path.name not in EXCLUDED_FILES and not path.name.startswith(".env") and (path.suffix.lower() in TEXT_SUFFIXES or path.suffix.lower() == ".ipynb" or path.name in SPECIAL_NAMES)

def redact(text: str) -> tuple[str, list[str]]:
    warnings = []
    if PRIVATE_KEY_RE.search(text):
        text = PRIVATE_KEY_RE.sub("[REDACTED_PRIVATE_KEY]", text); warnings.append("private key redacted")
    if SECRET_RE.search(text):
        text = SECRET_RE.sub(r"\1[REDACTED]", text); warnings.append("possible secret assignment redacted")
    return text, warnings

def function_signature(node) -> str:
    prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
    try: args = ast.unparse(node.args)
    except Exception: args = "..."
    try: returns = " -> " + ast.unparse(node.returns) if node.returns else ""
    except Exception: returns = ""
    return f"{prefix} {node.name}({args}){returns}"

def api_section(path: Path, text: str) -> tuple[str, list[str]]:
    try: tree = ast.parse(text)
    except SyntaxError as exc: return f"### `{path.as_posix()}`\n\n- Parse error: `{exc}`\n", []
    out = [f"### `{path.as_posix()}`", ""]
    module_doc = ast.get_docstring(tree)
    if module_doc: out += [module_doc.strip(), ""]
    found = False
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            found = True; out += [f"#### `{function_signature(node)}`", f"- Source line: `{node.lineno}`", ast.get_docstring(node) or "- **Missing docstring**", ""]
        elif isinstance(node, ast.ClassDef):
            found = True; out += [f"#### `class {node.name}`", f"- Source line: `{node.lineno}`", ast.get_docstring(node) or "- **Missing class docstring**", ""]
            for method in node.body:
                if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    out += [f"##### `{function_signature(method)}`", ast.get_docstring(method) or "- **Missing method docstring**", ""]
    if not found: out += ["- No top-level functions or classes detected.", ""]
    return "\n".join(out), sorted(set(ENV_RE.findall(text)))

def notebook(data: bytes) -> tuple[str, dict]:
    if not data: return "_Empty placeholder._\n", {"cells": 0, "placeholder": True}
    nb = json.loads(data.decode("utf-8-sig")); blocks = []
    for i, cell in enumerate(nb.get("cells", []), 1):
        kind = cell.get("cell_type", "unknown"); source = "".join(cell.get("source", [])).rstrip(); lexer = "python" if kind == "code" else "markdown"
        blocks.append(f"### Cell {i} [{kind}]\n\n```{lexer}\n{source}\n```")
    return "\n\n".join(blocks) + "\n", {"cells": len(nb.get("cells", [])), "kernel": nb.get("metadata", {}).get("kernelspec", {}), "outputs_omitted": True}

def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True); data = text.encode("utf-8")
    if path.exists() and path.read_bytes() == data: return
    with tempfile.NamedTemporaryFile("wb", delete=False, dir=path.parent) as f: f.write(data); temp = f.name
    Path(temp).replace(path)

def main() -> int:
    root = root_dir(); output = root / OUTPUT; paths = [p for p in tracked(root) if include(p)]
    branch = git(root, "branch", "--show-current").strip() or "detached"; commit = git(root, "rev-parse", "HEAD").strip(); status = git(root, "status", "--short").rstrip() or "clean working tree"
    api, sources, variables, skipped = [], [], {}, []
    for rel in paths:
        data = (root / rel).read_bytes()
        if len(data) > MAX_BYTES: skipped.append(f"{rel.as_posix()} ({len(data)} bytes)"); continue
        digest = hashlib.sha256(data).hexdigest()
        if rel.suffix.lower() == ".ipynb":
            try: text, meta = notebook(data)
            except Exception as exc: text, meta = f"_Notebook parse error: {exc!r}_\n", {"parse_error": repr(exc)}
            sources.append(f"## `{rel.as_posix()}`\n\n- SHA-256: `{digest}`\n- Bytes: `{len(data)}`\n- Notebook: `{json.dumps(meta, ensure_ascii=False)}`\n\n{text}")
            continue
        if b"\x00" in data[:8192]: skipped.append(f"{rel.as_posix()} (binary)"); continue
        text, warnings = redact(data.decode("utf-8-sig", errors="replace"))
        if rel.suffix.lower() == ".py":
            section, names = api_section(rel, text); api.append(section)
            for name in names: variables.setdefault(name, set()).add(rel.as_posix())
        security = "\n> Security: " + "; ".join(warnings) + "\n" if warnings else ""
        lexer = LANG.get(rel.suffix.lower(), "text")
        sources.append(f"## `{rel.as_posix()}`\n\n- SHA-256: `{digest}`\n- Bytes: `{len(data)}`\n{security}\n```{lexer}\n{text.rstrip()}\n```\n")
    env = "\n".join(f"- `{name}`: " + ", ".join(f"`{p}`" for p in sorted(files)) for name, files in sorted(variables.items())) or "- None detected."
    skipped_text = "\n".join(f"- `{x}`" for x in skipped) or "- None."
    document = f'''{CONTEXT}

## 6. Current snapshot

- Generated UTC: `{datetime.now(timezone.utc).isoformat()}`
- Branch: `{branch}`
- Commit: `{commit}`
- Included tracked files: `{len(paths) - len(skipped)}`

### Git status

```text
{status}
```

## 7. Included file list

''' + "\n".join(f"- `{p.as_posix()}`" for p in paths) + f'''

## 8. Environment variables referenced

{env}

Only names are documented. Secret values must never appear here.

## 9. Python API catalog

Generated statically with Python AST. Project modules are not imported or executed. Missing docstrings are marked explicitly.

''' + "\n".join(api) + f'''

## 10. Skipped files

{skipped_text}

## 11. Complete tracked source by file

Each section preserves the original file boundary. Notebook outputs are omitted.

''' + "\n".join(sources)
    atomic_write(output, document)
    print(f"Updated: {output}"); print(f"Included: {len(paths) - len(skipped)}"); print(f"Skipped: {len(skipped)}")
    return 0

if __name__ == "__main__": raise SystemExit(main())
```
