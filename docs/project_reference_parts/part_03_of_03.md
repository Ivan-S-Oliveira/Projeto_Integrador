<!-- PROJECT_COMPLETE_REFERENCE part 3/3 -->
## `notebooks/C/C_13_boosting.ipynb`

- Git: `tracked` · status `clean`
- Size: `33.3 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `5e8cd0be1182ecacaa42dfafb10518cf2a76f0372ee8cc4967d6dce01c8da23f`

- Cells: `15` (`9` code, `6` markdown)
- Code cells executed: `9` of `9`
- Kernel: `.venv (3.14.7)`; Python `3.14.7`
- Outputs: `text outputs included`

### Cell 1 [markdown]

```markdown
# C4 — Boosting

Avalia `HistGradientBoostingClassifier` na mesma partição do C3.
Se o gate `G6_finalistas_tuning` estiver aprovado, executa busca
limitada para ambos os finalistas. **Não abre o teste**, não calibra
e não escolhe limiar — isso pertence ao C5.

**Pré-requisito:** `pip install -e .`
```

### Cell 2 [code] · In [1]

```python
from pathlib import Path
import itertools
import json
import os
import sys
import time

import numpy as np
import pandas as pd
from IPython.display import display


def encontrar_raiz_projeto(start: Path | None = None) -> Path:
    atual = (start or Path.cwd()).resolve()
    for candidato in (atual, *atual.parents):
        if (candidato / "src").is_dir() and (candidato / "pyproject.toml").is_file():
            return candidato
    raise RuntimeError(f"Raiz do projeto não encontrada a partir de: {atual}")


ROOT_DIR = encontrar_raiz_projeto()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.utils import config as C
from src.utils import env
from src.utils.reproducibility import Run
from src.data.supervised_artifact import load_supervised_artifact, split_partitions
from src.evaluation.leakage import check_leakage
from src.evaluation.metrics import metricas_completas
from src.models.logistic import build_logistic_pipeline
from src.models.boosting import build_boosting_pipeline

env.carregar_dotenv()
env.garantir_diretorios()

TABLES_DIR      = C.TABLES_DIR
PREDICTIONS_DIR = C.PREDICTIONS_DIR
TABLES_DIR.mkdir(parents=True, exist_ok=True)
PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)

SEED = int(C.SEED)
print(C.resumo())
```

**Output 1 (stream:stdout)**

```text
ROOT_DIR          = <REPO>
DATA_DIR          = <REPO>\data
RAW_DIR           = <REPO>\data\raw
PROCESSED_DIR     = <REPO>\data\processed
ANALYTICAL_DIR    = <REPO>\data\analytical
TREINO_DIR        = <REPO>\data\treino
OUTPUTS_DIR       = <REPO>\outputs
RUNS_DIR          = <REPO>\outputs\runs
LOGS_DIR          = <REPO>\logs
CONFIGS_DIR       = <REPO>\configs
SUPERVISED_YAML   = <REPO>\configs\supervised.yaml (ok)
PARQUET_NAME      = srag.parquet
DATA_VERSION      = dados-v2
GITHUB_REPO       = Ivan-S-Oliveira/Projeto_Integrador
HTTP_TIMEOUT      = 180
HTTP_TENTATIVAS   = 3
SEED              = 42
GITHUB_TOKEN?     = False
SRAG_PARQUET_URL  = https://github.com/Ivan-S-Oliveira/Projeto_Integrador/releases/download/dados-v2/srag.parquet
SUPERVISED_SHA256 = 6a86868c0d348086a4334960c2461a9ba66b8200020aeeabaec4bfadddbaa7c6
```

### Cell 3 [markdown]

```markdown
## Carregar artefacto e materializar partições

Mesma fonte que C2/C3. `split_partitions` devolve apenas
`(treino, validacao)` — o teste fica inacessível.
```

### Cell 4 [code] · In [2]

```python
COHORT_KIND = os.getenv("SRAG_COHORT_KIND", "provisional").lower()

df, manifest = load_supervised_artifact(ROOT_DIR, expected_kind=COHORT_KIND)
treino, validacao = split_partitions(df, manifest)

PARTICAO = manifest["partition_column"]
ALVO     = manifest["target_column"]
FEATURES = list(manifest["feature_columns"])

X_train = treino[FEATURES].copy()
y_train = pd.to_numeric(treino[ALVO], errors="coerce").astype("int8")
X_val   = validacao[FEATURES].copy()
y_val   = pd.to_numeric(validacao[ALVO], errors="coerce").astype("int8")

check_leakage(X_train)
check_leakage(X_val)

n_teste = int((df[PARTICAO].astype(str) == "teste").sum())

display(pd.DataFrame({
    "particao":   ["treino", "validacao"],
    "n":          [len(treino), len(validacao)],
    "positivos":  [int(y_train.sum()), int(y_val.sum())],
    "prevalencia":[float(y_train.mean()), float(y_val.mean())],
}))

print(f"cohort_kind : {manifest['cohort_kind']}")
print(f"features    : {len(FEATURES)}")
print(f"teste       : {n_teste:,} (fechado)")
```

**Output 1 (display_data)**

```text
    particao        n  positivos  prevalencia
0     treino  2740584     599323     0.218684
1  validacao   587272     128429     0.218687
[non-text output omitted: text/html]
```

**Output 2 (stream:stdout)**

```text
cohort_kind : provisional
features    : 31
teste       : 587,276 (fechado)
```

### Cell 5 [markdown]

```markdown
## Modelos de referência

Logística e boosting com configurações do YAML (sem tuning). Servem
de base para a comparação caso o gate G6 esteja pendente.
```

### Cell 6 [code] · In [3]

```python
log_cfg   = C.cfg("models", "logistic") or {}
boost_cfg = C.cfg("models", "boosting") or {}

DEFAULTS_BOOST = {
    "max_leaf_nodes":     int(boost_cfg.get("max_leaf_nodes") or 31),
    "min_samples_leaf":   int(boost_cfg.get("min_samples_leaf") or 20),
    "l2_regularization":  float(boost_cfg.get("l2_regularization") or 0.0),
    "early_stopping":     bool(boost_cfg.get("early_stopping") or False),
    "class_weight":       boost_cfg.get("class_weight") or "balanced",
}

DEFAULTS_LOG = {
    "solver":       log_cfg.get("solver", "lbfgs"),
    "max_iter":     int(log_cfg.get("max_iter", 1000)),
    "class_weight": log_cfg.get("class_weight", "balanced"),
}

pipe_log_ref = build_logistic_pipeline(C=1.0, **DEFAULTS_LOG)
pipe_log_ref.fit(X_train, y_train)
prob_log_ref = pipe_log_ref.predict_proba(X_val)[:, 1]

pipe_boost_ref = build_boosting_pipeline(
    learning_rate=0.05, max_iter=500, max_depth=None, **DEFAULTS_BOOST,
)
pipe_boost_ref.fit(X_train, y_train)
prob_boost_ref = pipe_boost_ref.predict_proba(X_val)[:, 1]

display(pd.DataFrame([
    {"modelo": "logistica_C1",  **metricas_completas(y_val, prob_log_ref,   limiar=0.5)},
    {"modelo": "boosting_base", **metricas_completas(y_val, prob_boost_ref, limiar=0.5)},
]))
```

**Output 1 (display_data)**

```text
          modelo       auc        ap    pr_auc     brier  log_loss        f1  \
0   logistica_C1  0.775236  0.440616  0.440616  0.198063  0.567540  0.505889   
1  boosting_base  0.787433  0.467521  0.467521  0.195973  0.552883  0.511183   

   precision    recall  sensibilidade  especificidade  accuracy  limiar  \
0   0.375804  0.773712       0.773712        0.640302  0.669477     0.5   
1   0.371800  0.817744       0.817744        0.613273  0.657988     0.5   

          n  
0  587272.0  
1  587272.0  
[non-text output omitted: text/html]
```

### Cell 7 [markdown]

```markdown
## Busca limitada (somente se G6 aprovado)

Respeita `tuning.metrica_principal` e `tuning.max_configuracoes_por_modelo`.
Amostra apenas se `MAX_TREINO_BUSCA` for definido — caso contrário usa
o treino completo.
```

### Cell 8 [code] · In [4]

```python
MAX_TREINO_BUSCA = None

METRICAS = ("ap", "pr_auc", "auc", "brier", "f1", "precision", "recall")


def _subamostrar(X, y, max_n, seed):
    if max_n is None or max_n <= 0 or len(X) <= max_n:
        return X, y
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(X), size=max_n, replace=False)
    return X.iloc[idx].copy(), y.iloc[idx].copy()


def _busca_limitada(candidatos, construir, X_tr, y_tr, X_va, y_va, *,
                    seed, max_configs, metrica_principal):
    """Shuffle, avalia os `max_configs` primeiros, devolve (tabela, melhor)."""
    rng = np.random.default_rng(seed)
    ordem = rng.permutation(len(candidatos))
    selecionados = [candidatos[i] for i in ordem][:max_configs]

    linhas, melhor = [], None
    for params in selecionados:
        t0 = time.perf_counter()
        pipe = construir(**params)
        pipe.fit(X_tr, y_tr)
        fit_s = time.perf_counter() - t0
        prob = pipe.predict_proba(X_va)[:, 1]
        m = metricas_completas(y_va, prob, limiar=0.5)

        linha = {**{k: float(m[k]) for k in METRICAS},
                 **params,
                 "duracao_fit_s": float(fit_s)}
        linhas.append(linha)

        score = linha[metrica_principal]
        if melhor is None or score > melhor["score"]:
            melhor = {"score": score, "params": params,
                      "pipeline": pipe, "prob_val": prob}

    return pd.DataFrame(linhas), melhor


def _candidatos_boosting():
    return [
        {"learning_rate": float(lr), "max_iter": int(mi),
         "max_depth": (None if md is None else int(md))}
        for lr in (C.cfg("models", "boosting", "busca_learning_rate") or [0.05])
        for mi in (C.cfg("models", "boosting", "busca_max_iter")      or [500])
        for md in (C.cfg("models", "boosting", "busca_max_depth")     or [None])
    ]


def _candidatos_logistica():
    return [{"C": float(c)} for c in (C.cfg("models", "logistic", "busca_C") or [1.0])]
```

### Cell 9 [code] · In [5]

```python
G6_STATUS  = (C.cfg("gates", "G6_finalistas_tuning") or {}).get("status")
G6_APROVADO = G6_STATUS == "aprovado"

tuning_cfg        = C.cfg("tuning") or {}
METRICA_PRINCIPAL = str(tuning_cfg.get("metrica_principal") or "pr_auc")
MAX_CONFIGS       = max(1, int(tuning_cfg.get("max_configuracoes_por_modelo") or 30))

print(f"G6_finalistas_tuning: {G6_STATUS} (aprovado={G6_APROVADO})")
print(f"metrica_principal   : {METRICA_PRINCIPAL}")
print(f"max_configs         : {MAX_CONFIGS}")

resultados_busca_log = resultados_busca_boost = None
melhor_config_log    = melhor_config_boost    = None

pipe_log_final,   prob_log_final   = pipe_log_ref,   prob_log_ref
pipe_boost_final, prob_boost_final = pipe_boost_ref, prob_boost_ref
metricas_log_final   = {**metricas_completas(y_val, prob_log_final,   limiar=0.5), "modelo": "logistica_C1"}
metricas_boost_final = {**metricas_completas(y_val, prob_boost_final, limiar=0.5), "modelo": "boosting_base"}

if G6_APROVADO:
    X_busca, y_busca = _subamostrar(X_train, y_train, MAX_TREINO_BUSCA, SEED)
    print(f"\nBusca em {len(X_busca):,} linhas (treino original: {len(X_train):,}).")

    resultados_busca_log, melhor_config_log = _busca_limitada(
        _candidatos_logistica(),
        lambda **p: build_logistic_pipeline(**p, **DEFAULTS_LOG),
        X_busca, y_busca, X_val, y_val,
        seed=SEED, max_configs=MAX_CONFIGS, metrica_principal=METRICA_PRINCIPAL,
    )
    resultados_busca_log = resultados_busca_log.sort_values(
        [METRICA_PRINCIPAL, "brier"], ascending=[False, True]
    ).reset_index(drop=True)
    display(resultados_busca_log)

    resultados_busca_boost, melhor_config_boost = _busca_limitada(
        _candidatos_boosting(),
        lambda **p: build_boosting_pipeline(**p, **DEFAULTS_BOOST),
        X_busca, y_busca, X_val, y_val,
        seed=SEED, max_configs=MAX_CONFIGS, metrica_principal=METRICA_PRINCIPAL,
    )
    resultados_busca_boost = resultados_busca_boost.sort_values(
        [METRICA_PRINCIPAL, "brier"], ascending=[False, True]
    ).reset_index(drop=True)
    display(resultados_busca_boost)

    if melhor_config_log is not None:
        pipe_log_final = build_logistic_pipeline(**melhor_config_log["params"], **DEFAULTS_LOG)
        pipe_log_final.fit(X_train, y_train)
        prob_log_final = pipe_log_final.predict_proba(X_val)[:, 1]
        metricas_log_final = {**metricas_completas(y_val, prob_log_final, limiar=0.5),
                              "modelo": "logistica_tuned"}

    if melhor_config_boost is not None:
        pipe_boost_final = build_boosting_pipeline(**melhor_config_boost["params"], **DEFAULTS_BOOST)
        pipe_boost_final.fit(X_train, y_train)
        prob_boost_final = pipe_boost_final.predict_proba(X_val)[:, 1]
        metricas_boost_final = {**metricas_completas(y_val, prob_boost_final, limiar=0.5),
                                "modelo": "boosting_tuned"}
else:
    print("\nG6 pendente — busca limitada não executada. Comparação usará referências.")
```

**Output 1 (stream:stdout)**

```text
G6_finalistas_tuning: pendente (aprovado=False)
metrica_principal   : pr_auc
max_configs         : 30

G6 pendente — busca limitada não executada. Comparação usará referências.
```

### Cell 10 [markdown]

```markdown
## Comparação, predições e persistência
```

### Cell 11 [code] · In [6]

```python
comparacao = pd.DataFrame([
    {"modelo": metricas_log_final["modelo"],
     **{k: metricas_log_final[k] for k in ("ap", "pr_auc", "auc", "brier", "f1", "precision", "recall", "accuracy")}},
    {"modelo": metricas_boost_final["modelo"],
     **{k: metricas_boost_final[k] for k in ("ap", "pr_auc", "auc", "brier", "f1", "precision", "recall", "accuracy")}},
]).sort_values("ap", ascending=False).reset_index(drop=True)

delta_ap = (
    comparacao.loc[comparacao["modelo"].str.startswith("boosting"),  "ap"].iloc[0]
    - comparacao.loc[comparacao["modelo"].str.startswith("logistica"), "ap"].iloc[0]
)
display(comparacao)
print(f"Δ AP (boosting − logística): {delta_ap:+.4f}")

pred_val = pd.concat([
    pd.DataFrame({"y_true": y_val.to_numpy(), "y_prob": prob_log_final,
                  "modelo": metricas_log_final["modelo"],
                  "cohort_kind": manifest["cohort_kind"]}),
    pd.DataFrame({"y_true": y_val.to_numpy(), "y_prob": prob_boost_final,
                  "modelo": metricas_boost_final["modelo"],
                  "cohort_kind": manifest["cohort_kind"]}),
], ignore_index=True)
pred_val["y_pred"] = (pred_val["y_prob"] >= 0.5).astype(int)
```

**Output 1 (display_data)**

```text
          modelo        ap    pr_auc       auc     brier        f1  precision  \
0  boosting_base  0.467521  0.467521  0.787433  0.195973  0.511183   0.371800   
1   logistica_C1  0.440616  0.440616  0.775236  0.198063  0.505889   0.375804   

     recall  accuracy  
0  0.817744  0.657988  
1  0.773712  0.669477  
[non-text output omitted: text/html]
```

**Output 2 (stream:stdout)**

```text
Δ AP (boosting − logística): +0.0269
```

### Cell 12 [code] · In [7]

```python
timestamp = pd.Timestamp.now(tz="UTC").strftime("%Y%m%dT%H%M%SZ")
prefixo   = f"C4_boosting_{manifest['cohort_kind']}_{timestamp}"

caminho_comparacao = TABLES_DIR      / f"{prefixo}_comparacao.csv"
caminho_predicoes  = PREDICTIONS_DIR / f"{prefixo}_predicoes_validacao.parquet"
caminho_manifesto  = TABLES_DIR      / f"{prefixo}_manifesto.json"
caminho_busca_log  = TABLES_DIR      / f"{prefixo}_busca_logistica.csv"
caminho_busca_bst  = TABLES_DIR      / f"{prefixo}_busca_boosting.csv"

comparacao.to_csv(caminho_comparacao, index=False, encoding="utf-8-sig")
pred_val.to_parquet(caminho_predicoes, index=False)
if resultados_busca_log   is not None: resultados_busca_log.to_csv(caminho_busca_log, index=False, encoding="utf-8-sig")
if resultados_busca_boost is not None: resultados_busca_boost.to_csv(caminho_busca_bst, index=False, encoding="utf-8-sig")

manifesto_c4 = {
    "cohort_kind":        manifest["cohort_kind"],
    "dataset_path":       manifest["dataset_path"],
    "dataset_sha256":     manifest["dataset_sha256"],
    "feature_columns":    FEATURES,
    "target_column":      ALVO,
    "partition_column":   PARTICAO,
    "n_treino":           int(len(treino)),
    "n_validacao":        int(len(validacao)),
    "n_teste_fechado":    n_teste,
    "g6_status":          G6_STATUS,
    "buscas_executadas":  bool(G6_APROVADO),
    "metrica_principal":  METRICA_PRINCIPAL,
    "max_configs":        MAX_CONFIGS,
    "melhor_config_logistica": (
        None if melhor_config_log is None
        else {"C": melhor_config_log["params"]["C"],
              "score": float(melhor_config_log["score"])}
    ),
    "melhor_config_boosting": (
        None if melhor_config_boost is None
        else {**melhor_config_boost["params"],
              "score": float(melhor_config_boost["score"])}
    ),
    "limiar_usado":       0.5,
    "limiar_e_diagnostico": True,
    "calibracao_aplicada": False,
    "teste_aberto":       False,
    "features_final_congelada_no_yaml": bool(C.cfg("features", "final")),
    "artefatos": {
        "comparacao":          str(caminho_comparacao),
        "predicoes_validacao": str(caminho_predicoes),
        "busca_logistica":     str(caminho_busca_log) if resultados_busca_log   is not None else None,
        "busca_boosting":      str(caminho_busca_bst) if resultados_busca_boost is not None else None,
    },
}
caminho_manifesto.write_text(
    json.dumps(manifesto_c4, ensure_ascii=False, indent=2, default=str),
    encoding="utf-8",
)

assert len(pd.read_csv(caminho_comparacao, encoding="utf-8-sig")) == len(comparacao)
assert len(pd.read_parquet(caminho_predicoes)) == len(pred_val)

print(f"Comparação : {caminho_comparacao}")
print(f"Predições  : {caminho_predicoes}")
print(f"Manifesto  : {caminho_manifesto}")
```

**Output 1 (stream:stdout)**

```text
Comparação : <REPO>\outputs\tables\C4_boosting_provisional_20261017T010744Z_comparacao.csv
Predições  : <REPO>\outputs\predictions\C4_boosting_provisional_20261017T010744Z_predicoes_validacao.parquet
Manifesto  : <REPO>\outputs\tables\C4_boosting_provisional_20261017T010744Z_manifesto.json
```

### Cell 13 [markdown]

```markdown
## Proposta de atualização do YAML

Consolida os hiperparâmetros vencedores num bloco pronto para colar em
`supervised.yaml`. **Não é aplicada automaticamente** — o C5 lê o YAML
que existir em disco.
```

### Cell 14 [code] · In [8]

```python
def _fmt(v):
    if v is None: return "null"
    if isinstance(v, bool): return "true" if v else "false"
    return repr(v) if isinstance(v, str) else str(v)


def _montar_proposta_yaml():
    linhas = [
        "# Proposta de atualização do YAML — gerada pelo C4.",
        "# NÃO aplicada automaticamente; revise e cole em configs/supervised.yaml.",
        f"# cohort_kind: {manifest['cohort_kind']}",
        f"# g6_status: {G6_STATUS}",
        f"# metrica_principal: {METRICA_PRINCIPAL}",
        "models:",
    ]
    if melhor_config_log is not None:
        linhas += ["  logistic:", f"    C: {_fmt(melhor_config_log['params']['C'])}"]
    if melhor_config_boost is not None:
        p = melhor_config_boost["params"]
        linhas += [
            "  boosting:",
            f"    learning_rate: {_fmt(p['learning_rate'])}",
            f"    max_iter: {_fmt(p['max_iter'])}",
            f"    max_depth: {_fmt(p['max_depth'])}",
        ]
    return "\n".join(linhas) + "\n"


if G6_APROVADO and (melhor_config_log or melhor_config_boost):
    proposta = _montar_proposta_yaml()
    caminho_proposta = TABLES_DIR / f"{prefixo}_proposta_yaml.yaml"
    caminho_proposta.write_text(proposta, encoding="utf-8")
    print(proposta)
    print(f"Salvo: {caminho_proposta}")
else:
    caminho_proposta = None
    print("Sem proposta de atualização do YAML (G6 pendente ou busca vazia).")
```

**Output 1 (stream:stdout)**

```text
Sem proposta de atualização do YAML (G6 pendente ou busca vazia).
```

### Cell 15 [code] · In [9]

```python
with Run(
    modelo="C4_boosting",
    parametros={
        "cohort_kind":       manifest["cohort_kind"],
        "g6_status":         G6_STATUS,
        "buscas_executadas": bool(G6_APROVADO),
        "metrica_principal": METRICA_PRINCIPAL,
        "max_configs":       MAX_CONFIGS,
        "limiar_diagnostico": 0.5,
        "calibracao_aplicada": False,
        "teste_aberto":      False,
    },
    dataset={
        "n_treino":        int(len(treino)),
        "n_validacao":     int(len(validacao)),
        "n_teste_fechado": n_teste,
    },
    features={"n_features": len(FEATURES), "usadas": FEATURES},
    notas="C4 — boosting na partição do C3. Buscas condicionadas ao G6. Teste não consultado.",
    dataset_path=Path(manifest["dataset_path"]),
    dataset_sha256=manifest["dataset_sha256"],
) as r:
    r.metrica(
        logistica_ap=metricas_log_final["ap"],
        logistica_auc=metricas_log_final["auc"],
        boosting_ap=metricas_boost_final["ap"],
        boosting_auc=metricas_boost_final["auc"],
        boosting_brier=metricas_boost_final["brier"],
        delta_ap=delta_ap,
    )

print("Run registrado em:", r.pasta)
```

**Output 1 (stream:stdout)**

```text
[reproducibility] run registrado em: <REPO>\outputs\runs\2026-10-16_220744_784223_C4_boosting
Run registrado em: <REPO>\outputs\runs\2026-10-16_220744_784223_C4_boosting
```

## `notebooks/C/C_15_calibracao_limiar.ipynb`

- Git: `tracked` · status `clean`
- Size: `29.3 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `4e02d65b69000c9e9347fcd32bc8cd12dcff67e2e5360c628d1f8eec9d608272`

- Cells: `10` (`6` code, `4` markdown)
- Code cells executed: `6` of `6`
- Kernel: `.venv (3.14.7)`; Python `3.14.7`
- Outputs: `text outputs included`

### Cell 1 [markdown]

```markdown
# C5 — Calibração e Escolha de Limiar

Calibra os finalistas e escolhe o limiar operacional usando **somente
treino e validação**. Se `HONEST_CALIB_SPLIT = True`, a validação é
dividida em `val_cal` (ajusta calibrador) e `val_meas` (mede Brier,
escolhe limiar). Não abre o teste e não escreve no YAML.

**Pré-requisito:** `pip install -e .` com scikit-learn ≥ 1.6.
```

### Cell 2 [code] · In [1]

```python
from pathlib import Path
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd
from IPython.display import display
from sklearn.model_selection import train_test_split


def encontrar_raiz_projeto(start: Path | None = None) -> Path:
    atual = (start or Path.cwd()).resolve()
    for candidato in (atual, *atual.parents):
        if (candidato / "src").is_dir() and (candidato / "pyproject.toml").is_file():
            return candidato
    raise RuntimeError(f"Raiz do projeto não encontrada a partir de: {atual}")


ROOT_DIR = encontrar_raiz_projeto()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    import sklearn.frozen  # noqa: F401
except ImportError as exc:
    raise RuntimeError(
        "Este notebook requer scikit-learn >= 1.6 (FrozenEstimator)."
    ) from exc

from src.utils import config as C
from src.utils import env
from src.utils.reproducibility import Run
from src.data.supervised_artifact import load_supervised_artifact, split_partitions
from src.evaluation.leakage import check_leakage
from src.evaluation.metrics import metricas_completas, brier
from src.evaluation.calibration import curva_confiabilidade, ece, mce, brier_decomposicao
from src.models.factory import build_finalista
from src.models.calibration import calibrar, escolher_limiar

env.carregar_dotenv()
env.garantir_diretorios()

TABLES_DIR      = C.TABLES_DIR
PREDICTIONS_DIR = C.PREDICTIONS_DIR
TABLES_DIR.mkdir(parents=True, exist_ok=True)
PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)

SEED      = int(C.SEED)
G7_STATUS = str(C.cfg("gates", "G7_calibracao", "status") or "pendente")
G8_STATUS = str(C.cfg("gates", "G8_limiar", "status") or "pendente")

print(C.resumo())
```

**Output 1 (stream:stdout)**

```text
ROOT_DIR          = <REPO>
DATA_DIR          = <REPO>\data
RAW_DIR           = <REPO>\data\raw
PROCESSED_DIR     = <REPO>\data\processed
ANALYTICAL_DIR    = <REPO>\data\analytical
TREINO_DIR        = <REPO>\data\treino
OUTPUTS_DIR       = <REPO>\outputs
RUNS_DIR          = <REPO>\outputs\runs
LOGS_DIR          = <REPO>\logs
CONFIGS_DIR       = <REPO>\configs
SUPERVISED_YAML   = <REPO>\configs\supervised.yaml (ok)
PARQUET_NAME      = srag.parquet
DATA_VERSION      = dados-v2
GITHUB_REPO       = Ivan-S-Oliveira/Projeto_Integrador
HTTP_TIMEOUT      = 180
HTTP_TENTATIVAS   = 3
SEED              = 42
GITHUB_TOKEN?     = False
SRAG_PARQUET_URL  = https://github.com/Ivan-S-Oliveira/Projeto_Integrador/releases/download/dados-v2/srag.parquet
SUPERVISED_SHA256 = 6a86868c0d348086a4334960c2461a9ba66b8200020aeeabaec4bfadddbaa7c6
```

### Cell 3 [markdown]

```markdown
## Carregar artefacto e preparar validação

Se `HONEST_CALIB_SPLIT = True`, `val_cal` ajusta o calibrador e
`val_meas` mede — evita o viés otimista de calibrar e medir no mesmo
conjunto. Caso contrário, ambos são a validação inteira.
```

### Cell 4 [code] · In [2]

```python
COHORT_KIND = os.getenv("SRAG_COHORT_KIND", "provisional").lower()

df, manifest = load_supervised_artifact(ROOT_DIR, expected_kind=COHORT_KIND)
treino, validacao = split_partitions(df, manifest)

PARTICAO = manifest["partition_column"]
ALVO     = manifest["target_column"]
FEATURES = list(manifest["feature_columns"])

X_train = treino[FEATURES].copy()
y_train = pd.to_numeric(treino[ALVO], errors="coerce").astype("int8")
X_val   = validacao[FEATURES].copy()
y_val   = pd.to_numeric(validacao[ALVO], errors="coerce").astype("int8")

check_leakage(X_train)
check_leakage(X_val)

HONEST_CALIB_SPLIT = True
CALIB_SPLIT_FRAC   = 0.5
CALIB_SPLIT_SEED   = SEED

if HONEST_CALIB_SPLIT:
    idx_cal, idx_meas = train_test_split(
        np.arange(len(y_val)),
        test_size=1.0 - CALIB_SPLIT_FRAC,
        random_state=CALIB_SPLIT_SEED,
        stratify=y_val.to_numpy(),
    )
    X_val_cal  = X_val.iloc[idx_cal].reset_index(drop=True)
    y_val_cal  = y_val.iloc[idx_cal].reset_index(drop=True)
    X_val_meas = X_val.iloc[idx_meas].reset_index(drop=True)
    y_val_meas = y_val.iloc[idx_meas].reset_index(drop=True)
    CALIB_SPLIT_HASH = hashlib.sha256(
        np.asarray(idx_cal, dtype=np.int64).tobytes()
    ).hexdigest()[:16]
else:
    X_val_cal, y_val_cal = X_val, y_val
    X_val_meas, y_val_meas = X_val, y_val
    CALIB_SPLIT_HASH = None

n_teste = int((df[PARTICAO].astype(str) == "teste").sum())

display(pd.DataFrame({
    "bloco":      ["treino", "val_cal", "val_meas"],
    "n":          [len(X_train), len(X_val_cal), len(X_val_meas)],
    "positivos":  [int(y_train.sum()), int(y_val_cal.sum()), int(y_val_meas.sum())],
}))

print(f"cohort_kind : {manifest['cohort_kind']}")
print(f"features    : {len(FEATURES)}")
print(f"teste       : {n_teste:,} (fechado)")
if CALIB_SPLIT_HASH:
    print(f"split_hash  : {CALIB_SPLIT_HASH}")
```

**Output 1 (display_data)**

```text
      bloco        n  positivos
0    treino  2740584     599323
1   val_cal   293636      64215
2  val_meas   293636      64214
[non-text output omitted: text/html]
```

**Output 2 (stream:stdout)**

```text
cohort_kind : provisional
features    : 31
teste       : 587,276 (fechado)
split_hash  : c1a8f0dfddbf2b40
```

### Cell 5 [markdown]

```markdown
## Calibrar finalistas e escolher limiar

Para cada finalista da `selecao_modelos.finalistas`, treina no
treino, calibra cada método candidato em `val_cal`, mede Brier em
`val_meas` e escolhe o melhor. Depois escolhe o limiar no mesmo
`val_meas`.

O YAML usa `hist_gradient_boosting`; a fábrica usa `boosting` —
mapeamento abaixo, sem duplicar lógica de construção.
```

### Cell 6 [code] · In [3]

```python
ALIASES_FINALISTA = {
    "logistic":               "logistic",
    "boosting":               "boosting",
    "hist_gradient_boosting": "boosting",
}

selecao_cfg = C.cfg("selecao_modelos") or {}
FINALISTAS  = list(selecao_cfg.get("finalistas") or [])
if not FINALISTAS:
    raise RuntimeError("selecao_modelos.finalistas está vazio no YAML.")

desconhecidos = [n for n in FINALISTAS if n not in ALIASES_FINALISTA]
if desconhecidos:
    raise ValueError(f"Finalistas desconhecidos: {desconhecidos}")

calibracao_cfg      = C.cfg("calibracao") or {}
CALIBRACAO_ATIVA    = bool(calibracao_cfg.get("ativa", True))
METODOS_CANDIDATOS  = list(calibracao_cfg.get("metodos_candidatos") or ["sigmoid", "isotonic"])

limiar_cfg            = C.cfg("limiar") or {}
LIMIAR_METRICA        = limiar_cfg.get("metrica") or "f1"
LIMIAR_MIN_PRECISION  = limiar_cfg.get("min_precision")

print(f"finalistas          : {FINALISTAS}")
print(f"calibracao ativa    : {CALIBRACAO_ATIVA} ({METODOS_CANDIDATOS})")
print(f"limiar metrica      : {LIMIAR_METRICA} (min_precision={LIMIAR_MIN_PRECISION})")

resultados = {}

for nome_yaml in FINALISTAS:
    pipe = build_finalista(ALIASES_FINALISTA[nome_yaml])
    pipe.fit(X_train, y_train)
    prob_base = pipe.predict_proba(X_val_meas)[:, 1]
    brier_base = float(brier(y_val_meas, prob_base))

    calibracoes = {}
    if CALIBRACAO_ATIVA:
        for metodo in METODOS_CANDIDATOS:
            try:
                cal = calibrar(pipe, X_val_cal, y_val_cal, method=metodo)
                prob = cal.predict_proba(X_val_meas)[:, 1]
                calibracoes[metodo] = {
                    "pipeline":  cal,
                    "prob_meas": prob,
                    "brier":     float(brier(y_val_meas, prob)),
                }
            except Exception as exc:
                print(f"  {nome_yaml}/{metodo}: falhou ({exc!r})")

    if calibracoes:
        metodo = min(calibracoes, key=lambda m: calibracoes[m]["brier"])
        escolha = {"metodo": metodo, **calibracoes[metodo]}
    else:
        escolha = {"metodo": None, "pipeline": pipe,
                   "prob_meas": prob_base, "brier": brier_base}

    resultados[nome_yaml] = {
        "brier_base":    brier_base,
        "prob_base_meas": prob_base,
        "calibracoes":   calibracoes,
        "escolha":       escolha,
    }

    res = escolher_limiar(
        y_val_meas,
        escolha["prob_meas"],
        metrica=LIMIAR_METRICA,
        min_precision=LIMIAR_MIN_PRECISION,
    )
    resultados[nome_yaml]["limiar"] = res

tabela = pd.DataFrame([
    {"finalista": n,
     "metodo_calibracao": r["escolha"]["metodo"],
     "brier_base": r["brier_base"],
     "brier_calibrado": r["escolha"]["brier"],
     "ganho_brier": r["brier_base"] - r["escolha"]["brier"],
     "limiar": r["limiar"]["limiar"],
     "metrica": r["limiar"]["metrica"],
     "valor_metrica": r["limiar"]["valor"]}
    for n, r in resultados.items()
])
display(tabela)
```

**Output 1 (stream:stdout)**

```text
finalistas          : ['hist_gradient_boosting', 'logistic']
calibracao ativa    : True (['sigmoid', 'isotonic'])
limiar metrica      : f1 (min_precision=None)
```

**Output 2 (display_data)**

```text
                finalista metodo_calibracao  brier_base  brier_calibrado  \
0  hist_gradient_boosting           sigmoid    0.195889         0.140943   
1                logistic          isotonic    0.198105         0.143855   

   ganho_brier  limiar metrica  valor_metrica  
0     0.054945   0.255      f1       0.515904  
1     0.054250   0.255      f1       0.505913  
[non-text output omitted: text/html]
```

### Cell 7 [markdown]

```markdown
## Diagnósticos e persistência

Curva de confiabilidade, decomposição de Brier, ECE e MCE em
`val_meas` com o método escolhido. Persistimos tudo em `outputs/`.
```

### Cell 8 [code] · In [4]

```python
diagnosticos = {}
linhas_diag  = []

for nome, r in resultados.items():
    prob = r["escolha"]["prob_meas"]
    d = {
        "curva":  curva_confiabilidade(y_val_meas, prob, n_bins=10),
        "decomp": brier_decomposicao(y_val_meas, prob, n_bins=10),
        "ece":    float(ece(y_val_meas, prob, n_bins=10)),
        "mce":    float(mce(y_val_meas, prob, n_bins=10)),
    }
    diagnosticos[nome] = d
    linhas_diag.append({
        "finalista":   nome,
        "metodo":      r["escolha"]["metodo"] or "sem_calibracao",
        "ece":         d["ece"],
        "mce":         d["mce"],
        "brier":       d["decomp"]["brier"],
        "reliability": d["decomp"]["reliability"],
        "resolution":  d["decomp"]["resolution"],
    })

display(pd.DataFrame(linhas_diag))
```

**Output 1 (display_data)**

```text
                finalista    metodo       ece       mce     brier  \
0  hist_gradient_boosting   sigmoid  0.001753  0.182603  0.140943   
1                logistic  isotonic  0.001096  0.179992  0.143855   

   reliability  resolution  
0     0.000014    0.029117  
1     0.000004    0.026160  
[non-text output omitted: text/html]
```

### Cell 9 [code] · In [5]

```python
timestamp = pd.Timestamp.now(tz="UTC").strftime("%Y%m%dT%H%M%SZ")
prefixo   = f"C5_calibracao_limiar_{manifest['cohort_kind']}_{timestamp}"

caminho_tabela       = TABLES_DIR      / f"{prefixo}_escolhas.csv"
caminho_predicoes    = PREDICTIONS_DIR / f"{prefixo}_predicoes_val_meas.parquet"
caminho_manifesto    = TABLES_DIR      / f"{prefixo}_manifesto.json"

tabela.to_csv(caminho_tabela, index=False, encoding="utf-8-sig")

artefatos_diag = {}
for nome, d in diagnosticos.items():
    c_curva = TABLES_DIR / f"{prefixo}_{nome}_curva.csv"
    d["curva"].to_csv(c_curva, index=False, encoding="utf-8-sig")
    resultados[nome]["limiar"]["tabela"].to_csv(
        TABLES_DIR / f"{prefixo}_{nome}_limiar.csv", index=False, encoding="utf-8-sig",
    )
    artefatos_diag[nome] = {
        "curva":         str(c_curva),
        "ece":           d["ece"],
        "mce":           d["mce"],
        "brier_decomp":  {k: float(v) for k, v in d["decomp"].items()},
    }

predicoes = []
for nome, r in resultados.items():
    predicoes.append(pd.DataFrame({
        "y_true": y_val_meas.to_numpy(), "y_prob": r["prob_base_meas"],
        "modelo": f"{nome}_base", "cohort_kind": manifest["cohort_kind"],
    }))
    if r["escolha"]["metodo"]:
        predicoes.append(pd.DataFrame({
            "y_true": y_val_meas.to_numpy(), "y_prob": r["escolha"]["prob_meas"],
            "modelo": f"{nome}_{r['escolha']['metodo']}", "cohort_kind": manifest["cohort_kind"],
        }))

pred_val = pd.concat(predicoes, ignore_index=True)
pred_val["y_pred"] = (pred_val["y_prob"] >= 0.5).astype(int)
pred_val.to_parquet(caminho_predicoes, index=False)

manifesto_c5 = {
    "cohort_kind":        manifest["cohort_kind"],
    "dataset_sha256":     manifest["dataset_sha256"],
    "feature_columns":    FEATURES,
    "target_column":      ALVO,
    "partition_column":   PARTICAO,
    "n_treino":           int(len(treino)),
    "n_validacao":        int(len(validacao)),
    "n_val_cal":          int(len(X_val_cal)),
    "n_val_meas":         int(len(X_val_meas)),
    "n_teste_fechado":    n_teste,
    "honest_calib_split": bool(HONEST_CALIB_SPLIT),
    "calib_split_frac":   float(CALIB_SPLIT_FRAC),
    "calib_split_seed":   int(CALIB_SPLIT_SEED),
    "calib_split_hash":   CALIB_SPLIT_HASH,
    "finalistas":         FINALISTAS,
    "calibracao_ativa":   CALIBRACAO_ATIVA,
    "metodos_candidatos": METODOS_CANDIDATOS,
    "escolhas": {
        n: {"metodo": r["escolha"]["metodo"],
            "brier_base":      r["brier_base"],
            "brier_calibrado": r["escolha"]["brier"],
            "limiar":          r["limiar"]["limiar"],
            "limiar_metrica":  r["limiar"]["metrica"]}
        for n, r in resultados.items()
    },
    "diagnosticos":       artefatos_diag,
    "g7_status":          G7_STATUS,
    "g8_status":          G8_STATUS,
    "teste_aberto":       False,
    "yaml_atualizado":    False,
    "artefatos": {
        "tabela":              str(caminho_tabela),
        "predicoes_val_meas":  str(caminho_predicoes),
    },
}
caminho_manifesto.write_text(
    json.dumps(manifesto_c5, ensure_ascii=False, indent=2, default=str),
    encoding="utf-8",
)

print(f"Tabela     : {caminho_tabela}")
print(f"Predições  : {caminho_predicoes}")
print(f"Manifesto  : {caminho_manifesto}")
```

**Output 1 (stream:stdout)**

```text
Tabela     : <REPO>\outputs\tables\C5_calibracao_limiar_provisional_20261017T021055Z_escolhas.csv
Predições  : <REPO>\outputs\predictions\C5_calibracao_limiar_provisional_20261017T021055Z_predicoes_val_meas.parquet
Manifesto  : <REPO>\outputs\tables\C5_calibracao_limiar_provisional_20261017T021055Z_manifesto.json
```

### Cell 10 [code] · In [6]

```python
melhor_nome      = max(resultados, key=lambda n: resultados[n]["limiar"]["auc"])
metodo_escolhido = resultados[melhor_nome]["escolha"]["metodo"]
limiar_escolhido = resultados[melhor_nome]["limiar"]

proposta_yaml = "\n".join([
    "# Proposta de atualização do YAML — C5 (não aplicada automaticamente).",
    f"# cohort_kind: {manifest['cohort_kind']}",
    f"# G7/G8 no momento: {G7_STATUS}/{G8_STATUS}",
    f"# finalista sugerido (maior AUC em val_meas): {melhor_nome}",
    "calibracao:",
    f"  metodo: {metodo_escolhido}",
    "limiar:",
    f"  otimo: {limiar_escolhido['limiar']}",
    f"  metrica: {limiar_escolhido['metrica']}",
])
print(proposta_yaml)

with Run(
    modelo="C5_calibracao_limiar",
    parametros={
        "cohort_kind":        manifest["cohort_kind"],
        "finalistas":         FINALISTAS,
        "calibracao_ativa":   CALIBRACAO_ATIVA,
        "metodos_candidatos": METODOS_CANDIDATOS,
        "honest_calib_split": HONEST_CALIB_SPLIT,
        "limiar_metrica":     LIMIAR_METRICA,
        "min_precision":      LIMIAR_MIN_PRECISION,
        "teste_aberto":       False,
        "yaml_atualizado":    False,
    },
    dataset={
        "n_treino":        int(len(treino)),
        "n_val_cal":       int(len(X_val_cal)),
        "n_val_meas":      int(len(X_val_meas)),
        "n_teste_fechado": n_teste,
    },
    features={"n_features": len(FEATURES), "usadas": FEATURES},
    notas="C5 — calibração e limiar escolhidos na validação. Teste não consultado.",
    dataset_path=Path(manifest["dataset_path"]),
    dataset_sha256=manifest["dataset_sha256"],
) as r:
    r.metrica(**{
        f"{n}_{sufixo}": float(valor)
        for n, res in resultados.items()
        for sufixo, valor in [
            ("brier_base", res["brier_base"]),
            ("brier_calibrado", res["escolha"]["brier"]),
            ("limiar", res["limiar"]["limiar"]),
            ("auc", res["limiar"]["auc"]),
        ]
    })

print("Run registrado em:", r.pasta)
```

**Output 1 (stream:stdout)**

```text
# Proposta de atualização do YAML — C5 (não aplicada automaticamente).
# cohort_kind: provisional
# G7/G8 no momento: pendente/pendente
# finalista sugerido (maior AUC em val_meas): hist_gradient_boosting
calibracao:
  metodo: sigmoid
limiar:
  otimo: 0.255
  metrica: f1
[reproducibility] run registrado em: <REPO>\outputs\runs\2026-10-16_231055_901408_C5_calibracao_limiar
Run registrado em: <REPO>\outputs\runs\2026-10-16_231055_901408_C5_calibracao_limiar
```

## `notebooks/C/C_16_validacao_final.ipynb`

- Git: `tracked` · status `clean`
- Size: `31.5 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `e5820958e558f7dcb97b3d9600423b63af78d94e04959526412e616ec1f2dc4f`

- Cells: `15` (`9` code, `6` markdown)
- Code cells executed: `0` of `9`
- Kernel: `.venv (3.14.8)`; Python `3.14.8`
- Outputs: `text outputs included`

### Cell 1 [markdown]

```markdown
# C6 — Validação Final

Abre a partição de teste **uma única vez**, após `G7`, `G8` e `G9`
estarem aprovados, e produz a avaliação final do modelo congelado.

Reconstrói o pipeline deterministicamente do YAML, calibra em `val_cal`
(mesmo split do C5) e avalia no teste: métricas agregadas, IC por
bootstrap, erros (FN primeiro), por ano, por grupo e calibração por ano.
No final, marca `G9_holdout` como `executado` no YAML.

**Pré-requisito:** `pip install -e .` com scikit-learn ≥ 1.6.
```

### Cell 2 [code] · In [ ]

```python
from pathlib import Path
import hashlib
import json
import os
import re
import sys

import numpy as np
import pandas as pd
from IPython.display import display
from sklearn.model_selection import train_test_split


def encontrar_raiz_projeto(start: Path | None = None) -> Path:
    atual = (start or Path.cwd()).resolve()
    for candidato in (atual, *atual.parents):
        if (candidato / "src").is_dir() and (candidato / "pyproject.toml").is_file():
            return candidato
    raise RuntimeError(f"Raiz do projeto não encontrada a partir de: {atual}")


ROOT_DIR = encontrar_raiz_projeto()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    import sklearn.frozen  # noqa: F401
except ImportError as exc:
    raise RuntimeError(
        "Este notebook requer scikit-learn >= 1.6 (FrozenEstimator)."
    ) from exc

from src.utils import config as C
from src.utils import env
from src.utils.reproducibility import Run
from src.data.supervised_artifact import load_supervised_artifact
from src.evaluation.metrics import (
    metricas_completas, ic_bootstrap,
    auc, average_precision, brier as brier_metric,
)
from src.evaluation.errors import matriz_confusao, metricas_por_grupo
from src.evaluation.calibration import curva_confiabilidade, ece, mce, brier_decomposicao
from src.features.engineering import faixa_etaria as _faixa_etaria
from src.models.factory import build_finalista
from src.models.calibration import calibrar

env.carregar_dotenv()
env.garantir_diretorios()

TABLES_DIR      = C.TABLES_DIR
PREDICTIONS_DIR = C.PREDICTIONS_DIR
TABLES_DIR.mkdir(parents=True, exist_ok=True)
PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)

print(C.resumo())
```

### Cell 3 [markdown]

```markdown
## Verificar gates e carregar configuração congelada

`G9_holdout` precisa estar `aprovado` — o notebook marcará `executado`
no fim. A configuração do modelo (finalista, calibração, limiar,
features) tem de estar congelada no YAML.
```

### Cell 4 [code] · In [ ]

```python
GATES_EXIGIDOS = ["G7_calibracao", "G8_limiar", "G9_holdout"]
status_gates   = {g: (C.cfg("gates", g) or {}).get("status") for g in GATES_EXIGIDOS}

display(pd.DataFrame({"gate": list(status_gates), "status": list(status_gates.values())}))

faltando = [g for g, s in status_gates.items() if s != "aprovado"]
if faltando:
    raise RuntimeError(f"Gates não aprovados: {faltando}. Edite supervised.yaml.")

n_acessos_antes = int((C.cfg("gates", "G9_holdout") or {}).get("n_acessos") or 0)

COHORT_KIND = os.getenv("SRAG_COHORT_KIND", "provisional").lower()
df, manifest = load_supervised_artifact(ROOT_DIR, expected_kind=COHORT_KIND)

PARTICAO = manifest["partition_column"]
ALVO     = manifest["target_column"]

selecao_cfg          = C.cfg("selecao_modelos") or {}
finalista_escolhido  = selecao_cfg.get("finalista_escolhido")
if finalista_escolhido is None:
    candidatos = list(selecao_cfg.get("finalistas") or [])
    if len(candidatos) == 1:
        finalista_escolhido = candidatos[0]
    else:
        raise RuntimeError("selecao_modelos.finalista_escolhido não definido.")

calib_cfg    = C.cfg("calibracao") or {}
calib_metodo = calib_cfg.get("metodo")
calib_ativa  = bool(calib_cfg.get("ativa", True))
calib_fonte  = str(calib_cfg.get("fonte") or "validacao")

limiar_cfg    = C.cfg("limiar") or {}
limiar_final  = limiar_cfg.get("otimo")
limiar_metrica = limiar_cfg.get("metrica")

FEATURES = list(C.cfg("features", "final") or [])

if not FEATURES:
    raise RuntimeError("features.final vazio — congele as features antes do C6.")
if calib_ativa and calib_metodo is None:
    raise RuntimeError("calibracao.ativa=true mas metodo vazio no YAML.")
if limiar_final is None:
    raise RuntimeError("limiar.otimo vazio no YAML.")
if calib_fonte != "validacao":
    raise RuntimeError(f"calibracao.fonte deve ser 'validacao', não {calib_fonte!r}.")

proibidas = set(C.cfg("features", "proibidas") or [])
if set(FEATURES) & proibidas:
    raise RuntimeError(f"features.final contém colunas proibidas: {sorted(set(FEATURES) & proibidas)}")

limiar_final_val = float(limiar_final)

display(pd.DataFrame([
    {"chave": "finalista",        "valor": finalista_escolhido},
    {"chave": "calibracao.metodo","valor": calib_metodo if calib_ativa else "desativada"},
    {"chave": "limiar.otimo",    "valor": limiar_final_val},
    {"chave": "limiar.metrica",  "valor": limiar_metrica},
    {"chave": "features.final",  "valor": len(FEATURES)},
    {"chave": "n_acessos_G9",    "valor": n_acessos_antes},
]))
```

### Cell 5 [code] · In [ ]

```python
# Guarda contra reabertura do teste no mesmo dataset_sha256.
ALLOW_REOPEN = os.getenv("SRAG_ALLOW_TEST_REOPEN", "0") == "1"

reaberturas = []
for caminho in TABLES_DIR.glob("C6_validacao_final_*_manifesto.json"):
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        continue
    if dados.get("dataset_sha256") == manifest["dataset_sha256"]:
        reaberturas.append({"arquivo": caminho.name, "em_utc": dados.get("teste_aberto_em_utc")})

if reaberturas and not ALLOW_REOPEN:
    display(pd.DataFrame(reaberturas))
    raise RuntimeError(
        "Teste já aberto para este dataset_sha256. Defina "
        "SRAG_ALLOW_TEST_REOPEN=1 para reabrir e registe o motivo em docs/decisoes.md."
    )
print("Guarda OK." if not reaberturas else f"Reabertura autorizada ({len(reaberturas)} anterior(es)).")
```

### Cell 6 [markdown]

```markdown
## Reproduzir split do C5 e calibrar

O limiar congelado foi escolhido em `val_meas` com calibrador ajustado em
`val_cal`. Se o C6 recalibrasse em `val` inteira, a escala mudaria e o
limiar deixaria de ser o ótimo. Localizamos o manifesto do C5 compatível
e reproduzimos o split (hash de índice confirma que é o mesmo).
```

### Cell 7 [code] · In [ ]

```python
CALIB_SPLIT_FRAC_PADRAO = 0.5
HASH_LEN = 16


def _reproduzir_split_val_cal(y_val, frac_cal, seed):
    idx_cal, idx_meas = train_test_split(
        np.arange(len(y_val)),
        test_size=1.0 - frac_cal,
        random_state=seed,
        stratify=y_val.to_numpy(),
    )
    return (np.asarray(idx_cal,  dtype=np.int64),
            np.asarray(idx_meas, dtype=np.int64))


def _localizar_manifesto_c5(dataset_sha256, finalista, metodo, calib_ativa):
    for caminho in sorted(
        TABLES_DIR.glob("C5_calibracao_limiar_*_manifesto.json"),
        key=lambda p: p.stat().st_mtime, reverse=True,
    ):
        try:
            dados = json.loads(caminho.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if dados.get("dataset_sha256") != dataset_sha256:
            continue
        if calib_ativa:
            escolha = (dados.get("escolhas") or {}).get(finalista) or {}
            if escolha.get("metodo") != metodo:
                continue
        return dados, caminho
    return None, None


treino    = df.loc[df[PARTICAO] == "treino"].reset_index(drop=True)
validacao = df.loc[df[PARTICAO] == "validacao"].reset_index(drop=True)
teste     = df.loc[df[PARTICAO] == "teste"].reset_index(drop=True)

X_train = treino[FEATURES]
y_train = pd.to_numeric(treino[ALVO], errors="coerce").astype("int8")
X_val   = validacao[FEATURES]
y_val   = pd.to_numeric(validacao[ALVO], errors="coerce").astype("int8")
X_test  = teste[FEATURES]
y_test  = pd.to_numeric(teste[ALVO], errors="coerce").astype("int8")

manifesto_c5, manifesto_c5_path = _localizar_manifesto_c5(
    manifest["dataset_sha256"], finalista_escolhido,
    calib_metodo if calib_ativa else None, calib_ativa,
)

if calib_ativa and manifesto_c5 is None:
    raise RuntimeError(
        "Nenhum manifesto C5 compatível (dataset_sha256 + metodo). "
        "Rode o C5 com a configuração atual do YAML antes do C6."
    )

HONEST_CALIB_SPLIT = bool(manifesto_c5.get("honest_calib_split", False)) if manifesto_c5 else False
CALIB_SPLIT_FRAC   = float(manifesto_c5.get("calib_split_frac", CALIB_SPLIT_FRAC_PADRAO)) if manifesto_c5 else CALIB_SPLIT_FRAC_PADRAO
CALIB_SPLIT_SEED   = int(manifesto_c5.get("calib_split_seed", C.SEED)) if manifesto_c5 else int(C.SEED)

if HONEST_CALIB_SPLIT:
    idx_cal, _ = _reproduzir_split_val_cal(y_val, CALIB_SPLIT_FRAC, CALIB_SPLIT_SEED)
    hash_local = hashlib.sha256(idx_cal.tobytes()).hexdigest()[:HASH_LEN]
    assert manifesto_c5 is not None
    hash_c5 = manifesto_c5.get("calib_split_hash")
    if hash_c5 and hash_local != hash_c5:
        raise RuntimeError(f"Split divergente do C5 (local={hash_local}, C5={hash_c5}).")
    X_val_cal = X_val.iloc[idx_cal].reset_index(drop=True)
    y_val_cal = y_val.iloc[idx_cal].reset_index(drop=True)
else:
    X_val_cal, y_val_cal = X_val, y_val

ALIASES_FINALISTA = {
    "logistic":               "logistic",
    "boosting":               "boosting",
    "hist_gradient_boosting": "boosting",
}
if finalista_escolhido not in ALIASES_FINALISTA:
    raise ValueError(f"Finalista desconhecido: {finalista_escolhido!r}")

pipe_base = build_finalista(ALIASES_FINALISTA[finalista_escolhido])
pipe_base.fit(X_train, y_train)

if calib_ativa:
    if calib_metodo is None:
        raise ValueError("calib_metodo deve ser definido quando a calibração está ativa.")
    calibrador = calibrar(pipe_base, X_val_cal, y_val_cal, method=calib_metodo)
else:
    calibrador = None

preditor = calibrador if calibrador is not None else pipe_base

display(pd.DataFrame({
    "bloco":     ["treino", "val_cal", "teste"],
    "n":         [len(treino), len(X_val_cal), len(teste)],
    "positivos": [int(y_train.sum()), int(y_val_cal.sum()), int(y_test.sum())],
    "prevalencia": [float(y_train.mean()), float(y_val_cal.mean()), float(y_test.mean())],
}))
print(f"finalista   : {finalista_escolhido} (fábrica: {ALIASES_FINALISTA[finalista_escolhido]})")
print(f"calibração  : {calib_metodo if calib_ativa else 'desativada'}")
print(f"split C5    : {'honesto' if HONEST_CALIB_SPLIT else 'validação inteira'}")
```

### Cell 8 [markdown]

```markdown
## Abrir o teste — predição única

Esta é a **única** execução do C6 que toca no teste. Nada aqui é usado
para reajustar modelo, calibração ou limiar.
```

### Cell 9 [code] · In [ ]

```python
abertura_teste_utc = pd.Timestamp.now(tz="UTC").isoformat()

prob_test    = preditor.predict_proba(X_test)[:, 1]
y_test_arr   = y_test.to_numpy()
y_pred_test  = (prob_test >= limiar_final_val).astype(int)

if not np.isfinite(prob_test).all() or not ((prob_test >= 0) & (prob_test <= 1)).all():
    raise RuntimeError("Probabilidades inválidas no teste.")

metricas_test = metricas_completas(y_test_arr, prob_test, limiar=limiar_final_val)
matriz_test   = matriz_confusao(y_test_arr, y_pred_test)

display(pd.DataFrame([{
    "finalista": finalista_escolhido,
    "calibracao": calib_metodo if calib_ativa else "nenhuma",
    "limiar": limiar_final_val,
    **{k: float(v) for k, v in metricas_test.items()},
}]))
display(matriz_test)

print(f"Teste aberto em UTC: {abertura_teste_utc}")
print(f"n teste: {len(prob_test):,}  óbitos reais: {int(y_test_arr.sum()):,}")
```

### Cell 10 [markdown]

```markdown
## IC bootstrap, erros e avaliação estratificada

- IC percentil para AP, AUC e Brier, conforme `avaliacao.bootstrap`.
- Falsos negativos primeiro (`analise_erros.priorizar_falsos_negativos`).
- Métricas por ano e por grupo (`avaliacao.grupos`).
- Calibração por ano.
```

### Cell 11 [code] · In [ ]

```python
boot_cfg   = C.cfg("avaliacao", "bootstrap") or {}
BOOT_ATIVO = bool(boot_cfg.get("ativo", True))
BOOT_REPS  = int(boot_cfg.get("repeticoes") or 1000)
BOOT_NIVEL = float(boot_cfg.get("nivel") or 0.95)
BOOT_SEED  = int(boot_cfg.get("seed") or C.SEED)

ic_resultados = {}
if BOOT_ATIVO:
    for nome, fn in [("ap", average_precision), ("auc", auc), ("brier", brier_metric)]:
        est, inf, sup = ic_bootstrap(
            y_test_arr, prob_test, metrica=fn,
            n_boot=BOOT_REPS, alpha=1.0 - BOOT_NIVEL, seed=BOOT_SEED,
        )
        ic_resultados[nome] = {"estimativa": est, "ic_inferior": inf, "ic_superior": sup, "nivel": BOOT_NIVEL}

ic_df = pd.DataFrame([{"metrica": k, **v} for k, v in ic_resultados.items()])
display(ic_df)
```

### Cell 12 [code] · In [ ]

```python
erros_cfg    = C.cfg("avaliacao", "analise_erros") or {}
ERROS_ATIVA  = bool(erros_cfg.get("ativa", True))

df_err = teste.copy()
df_err["y_true"] = y_test_arr
df_err["y_pred"] = y_pred_test
df_err["y_prob"] = prob_test

fn = df_err[(df_err.y_true == 1) & (df_err.y_pred == 0)]
tp = df_err[(df_err.y_true == 1) & (df_err.y_pred == 1)]
fp = df_err[(df_err.y_true == 0) & (df_err.y_pred == 1)]
tn = df_err[(df_err.y_true == 0) & (df_err.y_pred == 0)]

display(pd.DataFrame([
    {"classe": "FN (óbito→cura)",     "n": len(fn), "frac": len(fn) / len(df_err)},
    {"classe": "TP (óbito→óbito)",    "n": len(tp), "frac": len(tp) / len(df_err)},
    {"classe": "FP (cura→óbito)",     "n": len(fp), "frac": len(fp) / len(df_err)},
    {"classe": "TN (cura→cura)",      "n": len(tn), "frac": len(tn) / len(df_err)},
]))

comparacao_fn_tp = pd.DataFrame()
amostra_fn       = pd.DataFrame()

if ERROS_ATIVA and len(fn) > 0 and len(tp) > 0:
    feats_num = [c for c in FEATURES if pd.api.types.is_numeric_dtype(df_err[c])]
    comparacao_fn_tp = pd.DataFrame([
        {"feature": c,
         "fn_media": float(fn[c].mean()), "tp_media": float(tp[c].mean()),
         "delta_media": float(fn[c].mean() - tp[c].mean())}
        for c in feats_num
    ])
    comparacao_fn_tp["abs_delta"] = comparacao_fn_tp.delta_media.abs()
    comparacao_fn_tp = comparacao_fn_tp.sort_values("abs_delta", ascending=False).reset_index(drop=True)
    print("Features numéricas com maior diferença FN vs TP:")
    display(comparacao_fn_tp)

if len(fn) > 0:
    amostra_fn = fn.sort_values("y_prob", ascending=False).head(20)[FEATURES + ["y_prob"]]
    print("Top 20 falsos negativos por probabilidade predita:")
    display(amostra_fn)
```

### Cell 13 [code] · In [ ]

```python
COLUNA_ANO = str(C.cfg("periodo", "coluna_ano") or "ano_internacao")

metricas_por_ano_df = pd.DataFrame()
curvas_por_ano      = {}
calib_por_ano_df    = pd.DataFrame()

if COLUNA_ANO in teste.columns:
    anos = sorted(teste[COLUNA_ANO].dropna().astype(int).unique().tolist())
    linhas_ano, linhas_calib = [], []

    for ano in anos:
        m = (teste[COLUNA_ANO].astype("Int64") == ano).to_numpy()
        y_a, p_a = y_test_arr[m], prob_test[m]
        if len(y_a) == 0:
            continue
        tem_2_classes = len(np.unique(y_a)) >= 2
        linhas_ano.append({
            "ano": int(ano), "n": int(len(y_a)), "positivos": int(y_a.sum()),
            "prevalencia": float(y_a.mean()),
            "ap":  float(average_precision(y_a, p_a)) if tem_2_classes else float("nan"),
            "auc": float(auc(y_a, p_a)) if tem_2_classes else float("nan"),
            "brier": float(brier_metric(y_a, p_a)),
            "ece": float(ece(y_a, p_a, n_bins=10)) if len(y_a) >= 20 else float("nan"),
        })
        if len(y_a) >= 20 and tem_2_classes:
            curvas_por_ano[int(ano)] = curva_confiabilidade(y_a, p_a, n_bins=10)
            d = brier_decomposicao(y_a, p_a, n_bins=10)
            linhas_calib.append({
                "ano": int(ano), "n": int(len(y_a)),
                "ece": float(ece(y_a, p_a, n_bins=10)),
                "mce": float(mce(y_a, p_a, n_bins=10)),
                **{k: float(v) for k, v in d.items()},
            })

    metricas_por_ano_df = pd.DataFrame(linhas_ano)
    calib_por_ano_df    = pd.DataFrame(linhas_calib)

display(metricas_por_ano_df)

grupos_cfg    = list(C.cfg("avaliacao", "grupos") or [])
min_n_grupo   = int(C.cfg("avaliacao", "min_n_grupo") or 100)

df_grupos = teste.copy()
if "faixa_etaria" in grupos_cfg and "faixa_etaria" not in df_grupos.columns and "idade_anos" in df_grupos.columns:
    df_grupos["faixa_etaria"] = _faixa_etaria(df_grupos["idade_anos"])

metricas_por_grupo_dict = {}
grupos_pulados = []
for grupo in grupos_cfg:
    if grupo not in df_grupos.columns:
        grupos_pulados.append(grupo)
        continue
    metricas_por_grupo_dict[grupo] = metricas_por_grupo(
        df_grupos, y_test_arr, prob_test, grupo,
        limiar=limiar_final_val, min_n=min_n_grupo,
    )
    print(f"\n=== {grupo} ===")
    display(metricas_por_grupo_dict[grupo])

if grupos_pulados:
    print(f"\nGrupos pulados (ausentes no teste): {grupos_pulados}")

display(calib_por_ano_df)
```

### Cell 14 [markdown]

```markdown
## Persistir, registar e marcar G9 como executado

Edição cirúrgica do YAML: só o bloco `G9_holdout` é tocado (preserva
comentários). Na próxima execução, a verificação de gates falha — é
a disciplina de abertura única imposta pelo código.
```

### Cell 15 [code] · In [ ]

```python
timestamp = pd.Timestamp.now(tz="UTC").strftime("%Y%m%dT%H%M%SZ")
prefixo   = f"C6_validacao_final_{manifest['cohort_kind']}_{timestamp}"

caminho_metricas   = TABLES_DIR      / f"{prefixo}_metricas.csv"
caminho_matriz     = TABLES_DIR      / f"{prefixo}_matriz_confusao.csv"
caminho_por_ano    = TABLES_DIR      / f"{prefixo}_metricas_por_ano.csv"
caminho_calib_ano  = TABLES_DIR      / f"{prefixo}_calibracao_por_ano.csv"
caminho_ic         = TABLES_DIR      / f"{prefixo}_ic_bootstrap.csv"
caminho_erros      = TABLES_DIR      / f"{prefixo}_analise_erros.csv"
caminho_fn         = TABLES_DIR      / f"{prefixo}_fn_amostra.csv"
caminho_predicoes  = PREDICTIONS_DIR / f"{prefixo}_predicoes_teste.parquet"
caminho_manifesto  = TABLES_DIR      / f"{prefixo}_manifesto.json"

pd.DataFrame([{"finalista": finalista_escolhido, "limiar": limiar_final_val,
               **{k: float(v) for k, v in metricas_test.items()}}]).to_csv(
    caminho_metricas, index=False, encoding="utf-8-sig")
matriz_test.to_csv(caminho_matriz, encoding="utf-8-sig")
metricas_por_ano_df.to_csv(caminho_por_ano, index=False, encoding="utf-8-sig")
calib_por_ano_df.to_csv(caminho_calib_ano, index=False, encoding="utf-8-sig")
if not ic_df.empty:           ic_df.to_csv(caminho_ic, index=False, encoding="utf-8-sig")
if not comparacao_fn_tp.empty: comparacao_fn_tp.to_csv(caminho_erros, index=False, encoding="utf-8-sig")
if not amostra_fn.empty:       amostra_fn.to_csv(caminho_fn, index=False, encoding="utf-8-sig")

for grupo, tab in metricas_por_grupo_dict.items():
    tab.to_csv(TABLES_DIR / f"{prefixo}_por_grupo_{grupo}.csv", index=False, encoding="utf-8-sig")
for ano, curva in curvas_por_ano.items():
    curva.to_csv(TABLES_DIR / f"{prefixo}_curva_{ano}.csv", index=False, encoding="utf-8-sig")

pred_test = pd.DataFrame({
    "y_true": y_test_arr, "y_prob": prob_test, "y_pred": y_pred_test,
    "limiar": limiar_final_val, "modelo": finalista_escolhido,
    "cohort_kind": manifest["cohort_kind"],
})
if COLUNA_ANO in teste.columns:
    pred_test[COLUNA_ANO] = teste[COLUNA_ANO].to_numpy()
pred_test.to_parquet(caminho_predicoes, index=False)

manifesto_c6 = {
    "cohort_kind":         manifest["cohort_kind"],
    "dataset_path":        manifest["dataset_path"],
    "dataset_sha256":      manifest["dataset_sha256"],
    "feature_columns":     FEATURES,
    "target_column":       ALVO,
    "partition_column":    PARTICAO,
    "n_treino":            int(len(treino)),
    "n_validacao":         int(len(validacao)),
    "n_teste":             int(len(teste)),
    "finalista_escolhido": finalista_escolhido,
    "calibracao_ativa":    calib_ativa,
    "calibracao_metodo":   calib_metodo,
    "calibracao_fonte":    calib_fonte,
    "honest_calib_split":  HONEST_CALIB_SPLIT,
    "manifesto_c5_usado":  str(manifesto_c5_path) if manifesto_c5_path else None,
    "limiar_final":        limiar_final_val,
    "limiar_metrica":      limiar_metrica,
    "teste_aberto_em_utc": abertura_teste_utc,
    "metricas_agregadas":  {k: float(v) for k, v in metricas_test.items()},
    "ic_bootstrap":        ic_resultados,
    "erros":               {"fn": len(fn), "tp": len(tp), "fp": len(fp), "tn": len(tn)},
    "grupos_avaliados":    list(metricas_por_grupo_dict),
    "grupos_pulados":      grupos_pulados,
    "artefatos": {
        "metricas":         str(caminho_metricas),
        "matriz_confusao":  str(caminho_matriz),
        "metricas_por_ano": str(caminho_por_ano),
        "calibracao_por_ano": str(caminho_calib_ano),
        "ic_bootstrap":     str(caminho_ic),
        "analise_erros":    str(caminho_erros) if not comparacao_fn_tp.empty else None,
        "fn_amostra":       str(caminho_fn)    if not amostra_fn.empty else None,
        "predicoes_teste":  str(caminho_predicoes),
    },
}
caminho_manifesto.write_text(
    json.dumps(manifesto_c6, ensure_ascii=False, indent=2, default=str),
    encoding="utf-8",
)

with Run(
    modelo="C6_validacao_final",
    parametros={"cohort_kind": manifest["cohort_kind"], "finalista": finalista_escolhido,
                "calibracao_metodo": calib_metodo, "limiar_final": limiar_final_val,
                "limiar_metrica": limiar_metrica, "teste_aberto_em_utc": abertura_teste_utc,
                "n_acessos_antes": n_acessos_antes},
    dataset={"n_treino": len(treino), "n_validacao": len(validacao), "n_teste": len(teste)},
    features={"n_features": len(FEATURES), "usadas": FEATURES},
    notas="C6 — abertura única do teste. Pipeline reconstruído via build_finalista.",
    dataset_path=Path(manifest["dataset_path"]),
    dataset_sha256=manifest["dataset_sha256"],
) as r:
    r.metrica(**{k: float(v) for k, v in metricas_test.items()})

print(f"Run registrado em: {r.pasta}")


# Marcar G9 como executado (edição cirúrgica do YAML, preserva comentários)
def _marcar_g9_executado(root_dir: Path, timestamp_utc: str, n_antes: int) -> Path:
    yaml_path = root_dir / "configs" / "supervised.yaml"
    linhas = yaml_path.read_text(encoding="utf-8").splitlines(keepends=True)

    i_ini = i_fim = indent_bloco = None
    for i, linha in enumerate(linhas):
        if linha.rstrip() == "  G9_holdout:":
            i_ini = i
            indent_bloco = len(linha) - len(linha.lstrip(" "))
            continue
        if i_ini is None or not linha.strip():
            continue
        if len(linha) - len(linha.lstrip(" ")) < indent_bloco:
            i_fim = i
            break
    if i_ini is None:
        raise RuntimeError("Bloco `G9_holdout:` não encontrado.")
    i_fim = i_fim or len(linhas)

    indent_chave = indent_bloco + 2

    def _substituir(bloco, chave, valor):
        padrao = re.compile(rf"^(\s{{{indent_chave}}}){re.escape(chave)}:\s*.*$")
        for j, l in enumerate(bloco):
            m = padrao.match(l)
            if m:
                bloco[j] = f"{m.group(1)}{chave}: {valor}\n"
                return True
        return False

    bloco = linhas[i_ini:i_fim]
    ok = [
        _substituir(bloco, "status",       "executado"),
        _substituir(bloco, "executado_em", f'"{timestamp_utc}"'),
        _substituir(bloco, "n_acessos",    str(n_antes + 1)),
    ]
    if not all(ok):
        raise RuntimeError(
            "Campos status/executado_em/n_acessos ausentes no bloco G9_holdout. "
            "O teste JÁ FOI ABERTO — corrija o YAML e defina SRAG_ALLOW_TEST_REOPEN=1 "
            "para reexecutar."
        )
    linhas[i_ini:i_fim] = bloco
    yaml_path.write_text("".join(linhas), encoding="utf-8")
    return yaml_path


caminho_yaml = _marcar_g9_executado(ROOT_DIR, abertura_teste_utc, n_acessos_antes)

print()
print("=" * 60)
print(f"C6 concluído. AP={metricas_test['ap']:.4f}  AUC={metricas_test['auc']:.4f}  Brier={metricas_test['brier']:.4f}")
print(f"Falsos negativos: {len(fn)} de {int(y_test_arr.sum())} óbitos")
print(f"G9 marcado em {caminho_yaml}")
print("=" * 60)
```

## `pyproject.toml`

- Git: `tracked` · status `clean`
- Size: `1.9 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `abadb0fb73a06e3a342f03ce049a7f74fede307ad1bf38aa39b4ce3d517d433c`

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "projeto-integrador"
version = "0.0.1"
description = "Análise retrospectiva de risco de óbito por SRAG (SIVEP-Gripe)."
readme = "README.md"
requires-python = ">=3.11"
license = { text = "Proprietary" }
authors = [
    { name = "Time do Projeto Integrador SRAG" },
]
keywords = ["srag", "sivep-gripe", "supervisionado", "saude-publica"]
classifiers = [
    "Private :: Do Not Upload",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Scientific/Engineering :: Medical Science Apps.",
]

dependencies = [
    "numpy>=1.26",
    "pandas>=2.1",
    "pyarrow>=15.0",
    "scikit-learn>=1.4",
    "PyYAML>=6.0",
    "requests>=2.31",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=5.0",
    "ruff>=0.6",
    "mypy>=1.11",
]
docs = [
    "mkdocs>=1.6",
    "mkdocs-material>=9.5",
]

[project.urls]
Repository = "https://github.com/SEU_USUARIO/SEU_REPO"

# ---------------------------------------------------------------------------
# Empacotamento — src/ é o pacote de topo, para que `import src.*` funcione
# ---------------------------------------------------------------------------
[tool.setuptools.packages.find]
where      = ["."]
include    = ["src*"]
namespaces = false

# ---------------------------------------------------------------------------
# Pytest
# ---------------------------------------------------------------------------
[tool.pytest.ini_options]
minversion   = "7.0"
testpaths    = ["tests"]
python_files = ["test_*.py"]
pythonpath   = ["."]
addopts      = "-ra -q"
markers = [
    "slow: testes que fazem I/O pesado (Parquet, downloads)",
    "net:  testes que exigem acesso à internet",
]
```

## `README.md`

- Git: `tracked` · status `clean`
- Size: `19.9 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `c227016dabad9f197ff4507945ee8b5e69a42eedbcbf9ad884dc7cea334a3ada`

````markdown
# Projeto Integrador --- SRAG e Machine Learning

Projeto acadêmico desenvolvido no âmbito do **Projeto Integrador I da
Pós-Graduação em Inteligência Artificial**. Investiga o uso de técnicas
de aprendizado de máquina sobre dados públicos de Síndrome Respiratória
Aguda Grave (SRAG), com foco em preparação de dados, avaliação de
modelos e reprodutibilidade.

> **Status:** em desenvolvimento. A seleção final do modelo, a
> calibração, a definição do limiar e a avaliação final ainda dependem
> da conclusão dos gates metodológicos configurados no projeto.

## Objetivo

Construir um fluxo reproduzível para estudar a previsão retrospectiva de
óbito por SRAG a partir de informações disponíveis **no momento da
internação hospitalar**. O trabalho envolve:

-   acesso, organização e preparação dos dados;
-   definição e rastreabilidade da coorte analítica;
-   análise exploratória e experimentos não supervisionados;
-   engenharia e validação de atributos;
-   comparação de modelos supervisionados;
-   calibração das probabilidades e escolha de limiar;
-   avaliação de erros e análise de desempenho por grupos;
-   documentação dos experimentos e das limitações.

O projeto tem finalidade **acadêmica e exploratória**. Não é um sistema
clinicamente validado, não deve ser usado para diagnóstico ou decisão
clínica e não permite inferir causalidade a partir de associações
preditivas.

## Fonte dos dados

Os dados são provenientes da base pública **SRAG 2019--2026**,
disponibilizada pelo Ministério da Saúde por meio da API de Dados
Abertos.

-   **Fonte:** Ministério da Saúde --- Dados Abertos
-   **Endpoint:**
    <https://apidadosabertos.saude.gov.br/vigilancia-e-meio-ambiente/srag-2019-2026>

O projeto utiliza arquivos Parquet e rotinas de acesso/armazenamento. Os
dados originais, arquivos Parquet, modelos treinados e resultados
volumosos não devem ser versionados diretamente no Git.

## Arquitetura e organização

A lógica reutilizável deve ficar em `src/`; notebooks devem orquestrar
experimentos, explicar decisões e apresentar tabelas e gráficos.
Parâmetros e decisões metodológicas devem permanecer centralizados em
`configs/` e `docs/`.

``` text
Projeto_Integrador/
├── configs/
│   ├── dicionario_variaveis_v1.csv
│   └── supervised.yaml
├── docs/
│   └── decisoes.md
├── notebooks/
│   ├── 00_acesso_dados_parquet.ipynb
│   ├── 01_extracao.ipynb
│   ├── 02_eda/
│   │   ├── 01_eda_primeira_passagem.ipynb
│   │   ├── 02_eda_temporal_clustering.ipynb
│   │   ├── 03_supervisionado_pilotos.ipynb
│   │   ├── 04_consolidacao_shortlist_transicao_coorte.ipynb
│   │   └── _provisorio_construcao_coorte_b.ipynb
│   └── C/
│       ├── C1_smoke_test.ipynb
│       ├── C2_pipeline_supervisionado.ipynb
│       ├── C3_baseline_logistica.ipynb
│       ├── C4_boosting.ipynb
│       ├── C5_calibracao_limiar.ipynb
│       └── C6_validacao_final.ipynb
├── src/
│   ├── data/
│   │   ├── cohort_source.py
│   │   ├── split.py
│   │   └── supervised_artifact.py
│   ├── evaluation/
│   │   ├── calibration.py
│   │   ├── errors.py
│   │   ├── leakage.py
│   │   ├── metrics.py
│   │   └── temporal.py
│   ├── features/
│   │   ├── engineering.py
│   │   └── normalization.py
│   ├── models/
│   │   ├── baseline.py
│   │   ├── boosting.py
│   │   ├── calibration.py
│   │   ├── factory.py
│   │   ├── logistic.py
│   │   └── pipeline.py
│   └── utils/
│       ├── config.py
│       ├── env.py
│       ├── reproducibility.py
│       └── storage.py
├── tests/
├── tools/
│   └── update_project_reference.py
├── .env.example
├── .gitignore
├── pyproject.toml
├── requirements.txt
└── README.md
```

A árvore acima destaca os principais componentes identificados na
referência do projeto; `tests/` contém testes automatizados para
configuração, coorte, atributos, partições, pipeline, métricas,
calibração, leakage e reprodutibilidade. Consulte os arquivos do
repositório para a lista completa.

### Responsabilidades principais

  ---------------------------------------------------------------------------
  Componente                              Responsabilidade
  --------------------------------------- -----------------------------------
  `configs/supervised.yaml`               Configura alvo, período, atributos,
                                          partições, modelos, métricas e
                                          gates metodológicos.

  `configs/dicionario_variaveis_v1.csv`   Dicionário de variáveis.

  `docs/decisoes.md`                      Registro das decisões
                                          metodológicas.

  `src/data/`                             Resolução/carregamento da coorte,
                                          partições e artefatos
                                          supervisionados.

  `src/features/`                         Engenharia e normalização de
                                          atributos.

  `src/models/`                           Construção de pipelines, modelos e
                                          calibração.

  `src/evaluation/`                       Métricas, avaliação temporal,
                                          calibração, erros e verificações de
                                          leakage.

  `src/utils/`                            Configuração, ambiente,
                                          armazenamento e reprodutibilidade.

  `tests/`                                Verificações automatizadas dos
                                          contratos do projeto.

  `notebooks/`                            Exploração, experimentos,
                                          orquestração e comunicação dos
                                          resultados.
  ---------------------------------------------------------------------------

## Notebooks

  -----------------------------------------------------------------------------------------------
  Notebook                                                    Finalidade
  ----------------------------------------------------------- -----------------------------------
  `00_acesso_dados_parquet.ipynb`                             Verificar o acesso aos dados
                                                              Parquet.

  `01_extracao.ipynb`                                         Documentar a etapa de extração.

  `02_eda/01_eda_primeira_passagem.ipynb`                     Primeira exploração e diagnóstico
                                                              dos dados.

  `02_eda/02_eda_temporal_clustering.ipynb`                   Análises temporais e experimentos
                                                              de agrupamento.

  `02_eda/03_supervisionado_pilotos.ipynb`                    Experimentos supervisionados
                                                              preliminares.

  `02_eda/04_consolidacao_shortlist_transicao_coorte.ipynb`   Consolidar a shortlist e a
                                                              transição da coorte.

  `02_eda/_provisorio_construcao_coorte_b.ipynb`              Notebook provisório de construção
                                                              de coorte; confirmar sua
                                                              necessidade antes de tratá-lo como
                                                              fluxo oficial.

  `C/C1_smoke_test.ipynb`                                     Verificar componentes essenciais do
                                                              ambiente e do projeto.

  `C/C2_pipeline_supervisionado.ipynb`                        Orquestrar e validar o pipeline
                                                              supervisionado.

  `C/C3_baseline_logistica.ipynb`                             Executar referências e experimentos
                                                              com regressão logística.

  `C/C4_boosting.ipynb`                                       Executar a busca limitada e avaliar
                                                              boosting.

  `C/C5_calibracao_limiar.ipynb`                              Escolher calibração e limiar usando
                                                              dados permitidos.

  `C/C6_validacao_final.ipynb`                                Executar o protocolo de validação
                                                              final, condicionado à liberação do
                                                              gate correspondente.
  -----------------------------------------------------------------------------------------------

Os notebooks devem evitar implementações duplicadas de funções
reutilizáveis. Uma função deve migrar para `src/` quando representar uma
responsabilidade compartilhada ou uma regra que precise de testes;
código exclusivo de apresentação e orquestração pode permanecer no
notebook.

## Metodologia supervisionada

### Alvo e momento da previsão

A configuração ativa define:

-   coluna de origem do alvo: `evolucao`;
-   coluna de modelagem: `alvo_obito_srag`;
-   classe positiva: valor `2.0`;
-   classe negativa: valor `1.0`;
-   descarte de outros valores para o alvo principal: habilitado;
-   análise de sensibilidade para qualquer óbito: configurada
    separadamente.

O momento de previsão definido metodologicamente é a **internação
hospitalar**. Informações registradas depois desse momento não devem ser
usadas como atributos de entrada.

### Período e partições

A configuração abrange 2019--2026, incluindo 2026 como ano parcial. A
partição primária atualmente configurada é **aleatória estratificada por
alvo e ano de internação**, com seed `42` e proporções:

-   treino: 70%;
-   validação: 15%;
-   teste/holdout: 15%.

**Importante:** apesar do interesse em comportamento temporal, essa
configuração não corresponde a uma separação estritamente cronológica
entre passado e futuro. Análises temporais adicionais podem ser usadas
como análises de robustez, mas não devem substituir silenciosamente a
partição primária definida na configuração. A documentação e os
resultados devem explicitar essa escolha.

### Atributos e prevenção de leakage

A configuração inclui atributos numéricos e categóricos, além de regras
para engenharia de atributos. A lista final de atributos ainda depende
da confirmação do gate `G1_definicao_alvo_features`.

Variáveis relacionadas ao desfecho ou a informações posteriores à
internação estão listadas entre as proibidas em
`configs/supervised.yaml`. Antes de treinar, verificar:

1.  se cada atributo estava disponível no momento da internação;
2.  se o alvo não aparece entre as entradas;
3.  se transformações e imputações são ajustadas somente nos dados de
    treino;
4.  se treino, validação e teste respeitam os contratos de partição;
5.  se a coorte e a lista de atributos estão documentadas e versionadas
    por metadados.

Não use o holdout final para escolher modelo, hiperparâmetros,
calibração ou limiar.

### Modelos e seleção

A configuração prevê baseline, regressão logística, árvore de decisão,
random forest e boosting. A shortlist provisória registrada aponta
`hist_gradient_boosting` e `logistic` como finalistas candidatos; isso
não equivale a uma escolha final de modelo. A métrica principal
configurada para comparação é `PR-AUC`.

### Calibração, limiar e avaliação

A configuração prevê comparar métodos de calibração (`sigmoid` e
`isotonic`) e avaliar o Brier Score antes e depois da calibração. O
limiar deve ser escolhido apenas com dados de validação, de acordo com
os critérios registrados na configuração.

As métricas configuradas incluem:

-   PR-AUC e ROC-AUC;
-   Brier Score e log loss;
-   precisão, recall/sensibilidade, F1 e especificidade;
-   matriz de confusão;
-   avaliação por grupos e por ano;
-   análise de erros, com prioridade para falsos negativos;
-   bootstrap para estimativa de incerteza, conforme os parâmetros
    ativos.

As métricas finais devem ser publicadas somente após a execução válida
do protocolo de avaliação e acompanhadas do contexto, tamanho da amostra
e limitações.

## Gates metodológicos e status

Os gates em `configs/supervised.yaml` registram decisões que precisam
ser concluídas antes de avançar. No snapshot documentado:

  -----------------------------------------------------------------------
  Gate                    Situação registrada     Significado
  ----------------------- ----------------------- -----------------------
  G1 --- alvo e atributos Pendente                Confirmar coorte
                                                  definitiva, alvo e
                                                  lista final de
                                                  atributos.

  G2 --- janela e         Aprovado                Período e estratégia de
  partições                                       partição registrados.

  G4 --- baseline         Aprovado                Execução do modelo de
                                                  referência registrada.

  G5 --- pilotos          Aprovado                Pilotos supervisionados
                                                  registrados.

  G6 --- finalistas e     Pendente                Selecionar finalista e
  tuning                                          concluir busca
                                                  limitada.

  G7 --- calibração       Pendente                Escolher método com
                                                  dados permitidos.

  G8 --- limiar           Pendente                Definir limiar usando
                                                  validação.

  G9 --- holdout final    Pendente                Liberar e executar o
                                                  teste final uma única
                                                  vez, após congelar as
                                                  decisões.
  -----------------------------------------------------------------------

Esses estados são os registrados no snapshot de referência e podem
mudar. Consulte sempre `configs/supervised.yaml` e os testes antes de
executar ou descrever uma etapa como concluída.

## Configuração do ambiente

Recomenda-se executar o projeto em ambiente virtual, na raiz do
repositório.

### Windows PowerShell

``` powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Se a política do PowerShell impedir a ativação, use o terminal Command
Prompt:

``` bat
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Configure o interpretador do ambiente `.venv` no VS Code. Não é
necessário remover a instalação global do Python para usar esse
ambiente.

### Segredos e dados privados

O projeto inclui `.env.example` como referência de configuração. Nunca
comite tokens, arquivos `.env` com valores reais, senhas ou credenciais.
Se o acesso aos dados exigir `GITHUB_TOKEN`, configure-o como variável
de ambiente ou pelo mecanismo de segredos suportado pelo ambiente de
execução.

## Testes

Execute os testes a partir da raiz do repositório, com o ambiente
virtual ativado:

``` powershell
python -m pytest
```

Se o comando não estiver disponível, confira se as dependências de
desenvolvimento estão instaladas no ambiente selecionado. Após mudanças,
execute os testes pertinentes, revise o diff e verifique se a
documentação continua coerente com código e configuração.

## Reprodutibilidade e artefatos

Para permitir a rastreabilidade dos experimentos:

-   mantenha parâmetros e decisões em `configs/` e `docs/`;
-   registre seeds, versões, origem e identificação da coorte;
-   mantenha transformações reutilizáveis em `src/`;
-   registre resultados e metadados sem expor dados sensíveis;
-   preserve a separação entre desenvolvimento e holdout;
-   use `.gitignore` para impedir o versionamento de dados grandes,
    modelos, saídas geradas, segredos e caminhos locais.

Os artefatos e resultados devem seguir as convenções já utilizadas no
projeto. Não crie diretórios alternativos para a mesma finalidade sem
antes verificar a organização existente.

## Pontos de atenção conhecidos

A referência estática do repositório identificou itens que precisam ser
conferidos; eles não significam automaticamente que toda a
funcionalidade esteja quebrada:

1.  **Importação de `csv_to_parquet`:** `tests/test_pipeline.py`
    referencia `src.data.extracao.csv_to_parquet`, mas o módulo
    correspondente não aparece entre os arquivos rastreados no snapshot.
    Verifique histórico de renomeação e atualize o teste ou a
    implementação canônica, sem recriar o módulo às cegas.
2.  **Engenharia de atributos:** nomes derivados configurados --- como
    `sin_semana`, `cos_semana`, `ano_internacao` e
    `dias_sintomas_ate_internacao` --- não foram todos encontrados como
    nomes estáticos nos módulos de `src/data/` e `src/features/`.
    Confirme sua geração real e cubra o contrato com testes.
3.  **Documentação de decisões:** `docs/decisoes.md` cita
    `configs/dicionario_variaveis_v1_revisao.csv`, que não aparece na
    lista de arquivos rastreados do snapshot. Atualize a referência ou
    restaure o arquivo se ele for realmente necessário.
4.  **Lógica nos notebooks:** há funções auxiliares locais nos notebooks
    de EDA e modelagem. Avalie caso a caso se são exclusivas de um
    experimento ou se devem ser promovidas a módulos testados em `src/`.
5.  **Caminhos e estrutura:** mantenha este README sincronizado com os
    arquivos reais; a referência do projeto é um snapshot estático, não
    uma verificação de execução ponta a ponta.

## Limitações

Os dados públicos podem conter ausências, inconsistências, duplicidades,
diferenças de preenchimento e mudanças ao longo do tempo. A definição da
coorte, do alvo e das variáveis disponíveis influencia os resultados. O
ano de 2026 está configurado como parcial e exige interpretação
cuidadosa.

Os resultados descrevem desempenho preditivo na população e nas
condições avaliadas. Não demonstram causalidade, não garantem
generalização para outros períodos ou populações e não constituem
validação clínica.

## Autores

-   **Ivan Schincariol Oliveira** ---
    [LinkedIn](https://www.linkedin.com/in/ivan-s-oliveira-3608a92aa/)
-   **Eduardo Hudson de Almeida Leite** ---
    [LinkedIn](https://www.linkedin.com/in/eduardo-hudson-de-almeida-leite-71ab5a7b/)
-   **Pedro Henrique Silva dos Santos** ---
    [LinkedIn](https://www.linkedin.com/in/pedro-h-s-santos/)
-   **Mateus da Silva Oliveira** ---
    [LinkedIn](https://www.linkedin.com/in/mateusso)

## Contexto acadêmico

**Projeto Integrador I --- Pós-Graduação em Inteligência Artificial.**

O projeto reúne práticas de engenharia de dados, análise exploratória,
aprendizado supervisionado e não supervisionado, engenharia de
atributos, avaliação de modelos, prevenção de vazamento de informação e
reprodutibilidade.
````

## `requirements.txt`

- Git: `tracked` · status `clean`
- Size: `129 B` · modified `2026-10-17 19:30 UTC`
- SHA-256: `73ee76a39fe6c52069d4b78b0e09ef10b77d0fa8d9d6c26bcce043cef18f6ac8`

```text
python-dotenv
PyYAML
pandas
requests
ipykernel
numpy
matplotlib
seaborn
scikit-learn
pyarrow
jupyterlab
pytest
joblib
```

## `src/__init__.py`

- Git: `tracked` · status `clean`
- Size: `0 B` · modified `2026-10-14 22:03 UTC`
- SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

```python

```

## `src/data/__init__.py`

- Git: `tracked` · status `clean`
- Size: `0 B` · modified `2026-10-06 02:28 UTC`
- SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

```python

```

## `src/data/cohort_source.py`

- Git: `tracked` · status `clean`
- Size: `3.8 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `3cf13f00abc576d8b736b8aef0c3d7ef48b5cb863fee1b781e81116a8824487d`

```python
"""Resolve a fonte de coorte sem acoplar notebooks ao nome do arquivo.

A troca entre coorte provisória e definitiva acontece por parâmetro ou
pela variável de ambiente ``SRAG_COHORT_KIND``. Não transforma a coorte,
não cria partições e não altera o alvo.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal, get_args

import pandas as pd

from src.utils.hashing import sha256_file

CohortKind = Literal["provisional", "final", "auto"]

_ENV_VAR        = "SRAG_COHORT_KIND"
_DEFAULT_KIND   = "provisional"
_VALID_KINDS    = frozenset(get_args(CohortKind))
_ANALYTICAL_DIR = Path("data") / "analytical"

_FINAL_FILENAMES = ("coorte_final.parquet",)
_PROVISIONAL_FILENAMES = (
    "coorte_provisoria.parquet",
    "coorte_provisoria_b.parquet",
    "coorte.parquet",
)


@dataclass(frozen=True)
class CohortSource:
    """Metadados imutáveis da coorte selecionada."""

    kind: str
    path: str
    sha256: str
    size_bytes: int
    rows: int
    columns: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def cohort_candidates(root: Path) -> dict[str, tuple[Path, ...]]:
    """Candidatos de coorte por tipo, na ordem de preferência."""
    analytical = root / _ANALYTICAL_DIR
    return {
        "final":       tuple(analytical / n for n in _FINAL_FILENAMES),
        "provisional": tuple(analytical / n for n in _PROVISIONAL_FILENAMES),
    }


def _resolve_kind(kind: CohortKind | None) -> str:
    selected = (kind or os.getenv(_ENV_VAR, _DEFAULT_KIND)).lower()
    if selected not in _VALID_KINDS:
        raise ValueError(
            f"{_ENV_VAR} deve ser {sorted(_VALID_KINDS)}. Recebido: {selected!r}."
        )
    return selected


def _kind_from_path(path: Path) -> str:
    return "final" if "final" in path.name.lower() else "provisional"


def resolve_cohort_path(
    root: Path,
    *,
    kind: CohortKind | None = None,
    explicit_path: Path | None = None,
) -> tuple[str, Path]:
    """Resolve a coorte sem alternar silenciosamente de provisória para final.

    ``kind=None`` consulta ``SRAG_COHORT_KIND`` (default ``provisional``).
    ``auto`` prefere a definitiva quando existir. Execuções oficiais devem
    usar ``provisional`` ou ``final`` explícitos.
    """
    if explicit_path is not None:
        path = Path(explicit_path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Coorte explícita não encontrada: {path}")
        return _kind_from_path(path), path

    selected   = _resolve_kind(kind)
    candidates = cohort_candidates(root)
    order      = ("final", "provisional") if selected == "auto" else (selected,)

    for effective_kind in order:
        for path in candidates[effective_kind]:
            if path.is_file():
                return effective_kind, path.resolve()

    candidatos = "\n".join(
        f"- {p}" for k in order for p in candidates[k]
    )
    raise FileNotFoundError(
        f"Nenhuma coorte do tipo {selected!r} encontrada. Candidatos:\n{candidatos}"
    )


def load_cohort(
    root: Path,
    *,
    kind: CohortKind | None = None,
    explicit_path: Path | None = None,
    columns: list[str] | None = None,
) -> tuple[pd.DataFrame, CohortSource]:
    """Carrega a coorte selecionada e devolve dados + metadados da fonte."""
    effective_kind, path = resolve_cohort_path(
        root, kind=kind, explicit_path=explicit_path,
    )
    frame  = pd.read_parquet(path, columns=columns)
    source = CohortSource(
        kind=effective_kind,
        path=str(path),
        sha256=sha256_file(path),
        size_bytes=path.stat().st_size,
        rows=int(len(frame)),
        columns=int(frame.shape[1]),
    )
    return frame, source
```

## `src/data/split.py`

- Git: `tracked` · status `clean`
- Size: `10.0 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `cb423ad56c5931511e575cb3bf1b6f9a3c4c03e661a1f42d62cc8930875b2e3e`

```python
"""Partições agrupadas e estratificadas (treino / validação / teste).

Garante simultaneamente:

- **Estratificação**: cada partição preserva a proporção do alvo (0/1),
  importante porque a prevalência de óbito é baixa.
- **Agrupamento**: todas as linhas de um mesmo grupo caem numa única
  partição, evitando vazamento entre treino e avaliação.

Estratos pequenos demais para as três partições são tratados por
``politica_estratos_pequenos``. Uso::

    from src.data.split import criar_particoes_agrupadas

    df_part = criar_particoes_agrupadas(
        df, target_column="alvo", group_column="nu_notific",
    )
"""

from __future__ import annotations

import warnings
from typing import Any, Literal, get_args

import numpy as np
import pandas as pd

__all__ = [
    "PARTICOES_CANONICAS",
    "SplitWarning",
    "criar_particoes_agrupadas",
]

PARTICOES_CANONICAS: tuple[str, ...] = ("treino", "validacao", "teste")

PoliticaEstratosPequenos = Literal["raise", "warn_teste", "warn_treino", "drop"]
PoliticaGrupoHeterogeneo = Literal["raise", "warn"]

_POLITICAS_ESTRATOS_PEQUENOS = frozenset(get_args(PoliticaEstratosPequenos))
_POLITICAS_GRUPO_HETEROGENEO = frozenset(get_args(PoliticaGrupoHeterogeneo))


class SplitWarning(UserWarning):
    """Decisão não-trivial do split (estrato pequeno, grupo com alvo misto).

    Filtre com ``warnings.filterwarnings("ignore", category=SplitWarning)``
    se a decisão já foi tomada pelo grupo.
    """


def _validar_parametros(
    df: pd.DataFrame,
    *,
    target_column: str,
    group_column: str,
    partition_column: str,
    frac_treino: float,
    frac_validacao: float,
    min_grupos_por_estrato: int,
    politica_estratos_pequenos: str,
    on_grupo_alvo_heterogeneo: str,
) -> None:
    if df.empty:
        raise ValueError("DataFrame vazio — não há como criar partições.")
    if target_column not in df.columns:
        raise KeyError(f"Coluna de alvo ausente: {target_column!r}")
    if group_column not in df.columns:
        raise KeyError(f"Coluna de grupo ausente: {group_column!r}")
    if partition_column in df.columns:
        raise ValueError(
            f"DataFrame já contém a coluna {partition_column!r}. "
            "Remova-a ou escolha outro nome — o split não sobrescreve partições."
        )

    if not 0.0 < frac_treino < 1.0:
        raise ValueError(f"frac_treino deve estar em (0, 1); recebido {frac_treino!r}.")
    if not 0.0 < frac_validacao < 1.0:
        raise ValueError(f"frac_validacao deve estar em (0, 1); recebido {frac_validacao!r}.")
    if frac_treino + frac_validacao >= 1.0:
        raise ValueError("frac_treino + frac_validacao deve ser < 1 (resto vira `teste`).")

    if min_grupos_por_estrato < len(PARTICOES_CANONICAS):
        raise ValueError(
            f"min_grupos_por_estrato deve ser >= {len(PARTICOES_CANONICAS)}; "
            f"recebido {min_grupos_por_estrato!r}."
        )
    if politica_estratos_pequenos not in _POLITICAS_ESTRATOS_PEQUENOS:
        raise ValueError(
            f"politica_estratos_pequenos inválida: {politica_estratos_pequenos!r}. "
            f"Use uma de {sorted(_POLITICAS_ESTRATOS_PEQUENOS)}."
        )
    if on_grupo_alvo_heterogeneo not in _POLITICAS_GRUPO_HETEROGENEO:
        raise ValueError(
            f"on_grupo_alvo_heterogeneo inválido: {on_grupo_alvo_heterogeneo!r}. "
            f"Use uma de {sorted(_POLITICAS_GRUPO_HETEROGENEO)}."
        )


def _estrato_por_grupo(
    df: pd.DataFrame,
    *,
    target_column: str,
    group_column: str,
    on_grupo_alvo_heterogeneo: PoliticaGrupoHeterogeneo,
) -> pd.Series:
    """Estrato (valor do alvo) por grupo.

    Grupos com mais de um valor distinto de alvo são tratados por
    ``on_grupo_alvo_heterogeneo``: ``"raise"`` levanta ``ValueError``;
    ``"warn"`` emite ``SplitWarning`` e usa a moda. Grupos com alvo todo
    nulo são descartados com ``SplitWarning``.
    """
    agrupado = df.groupby(group_column, observed=True)[target_column]

    heterogeneos = agrupado.nunique(dropna=True)
    heterogeneos = heterogeneos[heterogeneos > 1]
    if not heterogeneos.empty:
        amostra = heterogeneos.index.tolist()[:5]
        msg = (
            f"{len(heterogeneos)} grupo(s) com mais de um valor distinto "
            f"de alvo em {target_column!r}. Exemplos: {amostra}"
        )
        if on_grupo_alvo_heterogeneo == "raise":
            raise ValueError(
                msg + ". Resolva as inconsistências ou use "
                "on_grupo_alvo_heterogeneo='warn'."
            )
        warnings.warn(msg + ". Usando a moda por grupo.", SplitWarning, stacklevel=3)

    estrato = agrupado.agg(
        lambda s: s.dropna().mode().iloc[0] if s.notna().any() else None
    )

    if estrato.isna().any():
        n = int(estrato.isna().sum())
        warnings.warn(
            f"{n} grupo(s) com alvo todo nulo em {target_column!r}. "
            "Serão descartados do split.",
            SplitWarning,
            stacklevel=3,
        )
        estrato = estrato.dropna()

    if estrato.empty:
        raise ValueError("Nenhum grupo com alvo não nulo — impossível estratificar.")

    return estrato


def _distribuir_tamanhos(
    n: int,
    frac_treino: float,
    frac_validacao: float,
) -> tuple[int, int, int]:
    """Distribui ``n >= 3`` grupos em (treino, validação, teste), ≥1 por partição."""
    if n < 3:
        raise ValueError(f"_distribuir_tamanhos requer n >= 3; recebido {n}.")

    n_valid  = max(1, int(n * frac_validacao))
    n_teste  = max(1, n - max(1, int(n * frac_treino)) - n_valid)
    n_treino = n - n_valid - n_teste
    return n_treino, n_valid, n_teste


def _aplicar_politica_estrato_pequeno(
    grupos: list[Any],
    *,
    estrato: Any,
    min_grupos_por_estrato: int,
    politica: PoliticaEstratosPequenos,
    atribuicao: dict[Any, str],
    descartar: set[Any],
) -> None:
    n = len(grupos)
    msg = (
        f"Estrato {estrato!r} tem apenas {n} grupo(s) "
        f"(< min_grupos_por_estrato={min_grupos_por_estrato}). "
        f"Política: {politica!r}."
    )

    if politica == "raise":
        raise ValueError(
            msg + " Ajuste min_grupos_por_estrato ou use "
            "politica_estratos_pequenos='warn_teste'|'warn_treino'|'drop'."
        )

    if politica == "drop":
        warnings.warn(f"{msg} Descartando do resultado.", SplitWarning, stacklevel=2)
        descartar.update(grupos)
        return

    destino = "teste" if politica == "warn_teste" else "treino"
    warnings.warn(f"{msg} Destinando ao {destino}.", SplitWarning, stacklevel=2)
    atribuicao.update({g: destino for g in grupos})


def criar_particoes_agrupadas(
    df: pd.DataFrame,
    *,
    target_column: str,
    group_column: str,
    partition_column: str = "particao",
    frac_treino: float = 0.7,
    frac_validacao: float = 0.15,
    seed: int = 42,
    min_grupos_por_estrato: int = 3,
    politica_estratos_pequenos: PoliticaEstratosPequenos = "raise",
    on_grupo_alvo_heterogeneo: PoliticaGrupoHeterogeneo = "raise",
) -> pd.DataFrame:
    """Partições treino/validação/teste agrupadas e estratificadas.

    Não muta ``df``: devolve cópia com ``partition_column`` adicionada.
    Grupos com alvo nulo e estratos descartados por ``"drop"`` não aparecem.

    Levanta ``KeyError`` se ``target_column`` ou ``group_column`` não
    existirem em ``df``, e ``ValueError`` para parâmetros inválidos,
    DataFrame vazio, coluna de partição já presente, ou estrato pequeno
    com política ``"raise"``.
    """
    _validar_parametros(
        df,
        target_column=target_column,
        group_column=group_column,
        partition_column=partition_column,
        frac_treino=frac_treino,
        frac_validacao=frac_validacao,
        min_grupos_por_estrato=min_grupos_por_estrato,
        politica_estratos_pequenos=politica_estratos_pequenos,
        on_grupo_alvo_heterogeneo=on_grupo_alvo_heterogeneo,
    )

    estrato_por_grupo = _estrato_por_grupo(
        df,
        target_column=target_column,
        group_column=group_column,
        on_grupo_alvo_heterogeneo=on_grupo_alvo_heterogeneo,
    )

    rng       = np.random.default_rng(seed)
    atribuicao: dict[Any, str] = {}
    descartar: set[Any] = set()

    for estrato, sub in estrato_por_grupo.groupby(estrato_por_grupo):
        grupos = sub.index.tolist()
        rng.shuffle(grupos)

        if len(grupos) < min_grupos_por_estrato:
            _aplicar_politica_estrato_pequeno(
                grupos,
                estrato=estrato,
                min_grupos_por_estrato=min_grupos_por_estrato,
                politica=politica_estratos_pequenos,
                atribuicao=atribuicao,
                descartar=descartar,
            )
            continue

        n_treino, n_valid, n_teste = _distribuir_tamanhos(
            len(grupos), frac_treino, frac_validacao,
        )
        fatias = {
            "treino":    grupos[:n_treino],
            "validacao": grupos[n_treino:n_treino + n_valid],
            "teste":     grupos[n_treino + n_valid:],
        }
        for particao, membros in fatias.items():
            atribuicao.update({g: particao for g in membros})

    out = df.copy()
    out[partition_column] = out[group_column].map(atribuicao)

    invalidos = out[partition_column].isna() | out[group_column].isin(descartar)
    if invalidos.any():
        out = out.loc[~invalidos].reset_index(drop=True)

    out[partition_column] = out[partition_column].astype("object")

    faltando = set(PARTICOES_CANONICAS) - set(out[partition_column].unique())
    if faltando:
        warnings.warn(
            f"Partição(ões) sem nenhuma linha após o split: {sorted(faltando)}. "
            "Verifique a distribuição dos estratos antes de prosseguir.",
            SplitWarning,
            stacklevel=2,
        )

    return out
```

## `src/data/supervised_artifact.py`

- Git: `tracked` · status `clean`
- Size: `11.3 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `8c1030a654b10ad4b2be788e6db4dcb2768919ddf45cdb18421987b04e9988e4`

```python
"""Persistencia e leitura do dataset supervisionado canonico.

Separa notebooks da origem fisica da coorte: o Notebook 03 materializa uma
unica particao e os notebooks seguintes apenas a reutilizam.

O manifesto registra, alem do hash e das particoes:

- ``feature_columns`` — colunas usadas como features;
- ``numeric_columns`` / ``categorical_columns`` — divisao por tipo,
  consumida por ``build_preprocessor``;
- ``audit_columns`` — colunas no parquet que NAO entram em X, mas devem
  ser preservadas para auditoria (ex.: ``sg_uf``, ``faixa_etaria``).

Convencoes:

- As particoes canonicas sao ``treino``, ``validacao`` e ``teste``.
- ``split_partitions`` devolve ``(treino, validacao)`` — par consumido na
  fase de selecao. O bloco ``teste`` NAO e exposto; use
  ``holdout_partition`` respeitando o gate ``G9_holdout``.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd

from src.utils.hashing import sha256_file

DATASET_NAME = "dataset_supervisionado.parquet"
MANIFEST_NAME = "manifesto_supervisionado.json"
SCHEMA_VERSION = 2

_PARTITION_TREINO    = "treino"
_PARTITION_VALIDACAO = "validacao"
_PARTITION_TESTE     = "teste"

ALLOWED_PARTITIONS = {_PARTITION_TREINO, _PARTITION_VALIDACAO, _PARTITION_TESTE}


def _paths(root: Path) -> tuple[Path, Path]:
    """Caminhos canonicos (dataset, manifesto) para uma raiz de projeto."""
    output_dir = Path(root).resolve() / "data" / "analytical"
    return output_dir / DATASET_NAME, output_dir / MANIFEST_NAME


def _validar_grupos(
    num_set: set[str],
    cat_set: set[str],
    feats_set: set[str],
) -> None:
    if overlap := num_set & cat_set:
        raise ValueError(
            "Colunas presentes em numeric_columns E categorical_columns: "
            f"{sorted(overlap)}"
        )
    if fora := (num_set | cat_set) - feats_set:
        raise ValueError(
            "numeric_columns/categorical_columns contem colunas fora de "
            f"feature_columns: {sorted(fora)}"
        )
    if faltando := feats_set - (num_set | cat_set):
        raise ValueError(
            "Cada feature precisa estar em numeric_columns ou "
            f"categorical_columns. Faltando: {sorted(faltando)}"
        )


def _resolver_grupos(
    feature_columns: Sequence[str],
    numeric_columns: Sequence[str] | None,
    categorical_columns: Sequence[str] | None,
) -> tuple[list[str] | None, list[str] | None]:
    """Resolve o par ``(numericas, categoricas)``.

    - Ambas ``None`` → ``(None, None)`` (compatibilidade com chamadas antigas).
    - Apenas uma passada → o complemento e inferido dentro de ``feature_columns``.
    - Ambas passadas → valida disjuncao e cobertura exata de ``feature_columns``.
    """
    if numeric_columns is None and categorical_columns is None:
        return None, None

    num = list(numeric_columns) if numeric_columns is not None else None
    cat = list(categorical_columns) if categorical_columns is not None else None

    if num is None:
        assert cat is not None
        cat_set = set(cat)
        num = [c for c in feature_columns if c not in cat_set]
    if cat is None:
        num_set = set(num)
        cat = [c for c in feature_columns if c not in num_set]

    _validar_grupos(set(num), set(cat), set(feature_columns))
    return num, cat


def validate_supervised_frame(
    frame: pd.DataFrame,
    *,
    feature_columns: Sequence[str],
    target_column: str,
    partition_column: str,
    audit_columns: Sequence[str] | None = None,
) -> None:
    """Valida schema minimo, alvo e particoes do artefato supervisionado."""
    required = set(feature_columns) | {target_column, partition_column}
    if audit_columns:
        required |= set(audit_columns)

    if missing := sorted(required - set(frame.columns)):
        raise KeyError(f"Colunas ausentes no dataset supervisionado: {missing}")

    if frame.empty:
        raise ValueError("O dataset supervisionado nao pode ser vazio.")

    target_values = set(
        pd.to_numeric(frame[target_column], errors="coerce")
        .dropna().astype(int).unique()
    )
    if not target_values or not target_values.issubset({0, 1}):
        raise ValueError(f"Alvo deve ser binario 0/1. Observado: {sorted(target_values)}")

    observed = set(frame[partition_column].dropna().astype(str).unique())
    if observed != ALLOWED_PARTITIONS:
        raise ValueError(
            "Particoes esperadas treino, validacao e teste. "
            f"Observado: {sorted(observed)}"
        )


def _build_manifest(
    *,
    frame: pd.DataFrame,
    dataset_path: Path,
    source: Mapping[str, Any],
    feature_columns: Sequence[str],
    numeric_columns: list[str] | None,
    categorical_columns: list[str] | None,
    audit_columns: Sequence[str] | None,
    target_column: str,
    partition_column: str,
    cohort_kind: str,
    seed: int,
) -> dict[str, Any]:
    partition_counts = {
        str(key): int(value)
        for key, value in frame[partition_column].value_counts(dropna=False).items()
    }
    return {
        "schema_version":      SCHEMA_VERSION,
        "generated_utc":       datetime.now(timezone.utc).isoformat(),
        "cohort_kind":         str(cohort_kind),
        "source":              dict(source),
        "dataset_path":        str(dataset_path),
        "dataset_sha256":      sha256_file(dataset_path),
        "rows":                int(len(frame)),
        "columns":             int(frame.shape[1]),
        "feature_columns":     list(feature_columns),
        "numeric_columns":     numeric_columns,
        "categorical_columns": categorical_columns,
        "audit_columns":       list(audit_columns) if audit_columns else [],
        "target_column":       target_column,
        "partition_column":    partition_column,
        "partition_counts":    partition_counts,
        "seed":                int(seed),
        "test_opened":         False,
    }


def persist_supervised_artifact(
    frame: pd.DataFrame,
    *,
    root: Path,
    source: Mapping[str, Any],
    feature_columns: Sequence[str],
    target_column: str,
    partition_column: str,
    cohort_kind: str,
    seed: int,
    numeric_columns: Sequence[str] | None = None,
    categorical_columns: Sequence[str] | None = None,
    audit_columns: Sequence[str] | None = None,
    overwrite: bool = False,
) -> tuple[Path, Path]:
    """Grava dataset e manifesto, preservando a particao criada no Notebook 03.

    ``numeric_columns``/``categorical_columns`` dividem ``feature_columns``
    por tipo (ambas, uma, ou nenhuma — ver ``_resolver_grupos``).
    ``audit_columns`` sao validadas como presentes mas nao entram em X.
    """
    num, cat = _resolver_grupos(feature_columns, numeric_columns, categorical_columns)

    validate_supervised_frame(
        frame,
        feature_columns=feature_columns,
        target_column=target_column,
        partition_column=partition_column,
        audit_columns=audit_columns,
    )

    dataset_path, manifest_path = _paths(root)
    dataset_path.parent.mkdir(parents=True, exist_ok=True)

    if not overwrite and (dataset_path.exists() or manifest_path.exists()):
        raise FileExistsError(
            "Artefato supervisionado ja existe. Use overwrite=True somente em uma "
            "reconstrucao deliberada da mesma etapa."
        )

    frame.to_parquet(dataset_path, index=False)

    manifest = _build_manifest(
        frame=frame,
        dataset_path=dataset_path,
        source=source,
        feature_columns=feature_columns,
        numeric_columns=num,
        categorical_columns=cat,
        audit_columns=audit_columns,
        target_column=target_column,
        partition_column=partition_column,
        cohort_kind=cohort_kind,
        seed=seed,
    )
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    return dataset_path, manifest_path


def load_supervised_artifact(
    root: Path,
    *,
    expected_kind: str | None = None,
    columns: Sequence[str] | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Carrega o artefato canonico e valida hash, tipo de coorte e schema."""
    dataset_path, manifest_path = _paths(root)

    if not dataset_path.is_file() or not manifest_path.is_file():
        raise FileNotFoundError(
            "Execute o Notebook 03 adaptado para gerar "
            f"{DATASET_NAME} e {MANIFEST_NAME}."
        )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    if expected_kind and manifest.get("cohort_kind") != expected_kind:
        raise RuntimeError(
            f"Artefato de coorte {manifest.get('cohort_kind')!r}, mas "
            f"SRAG_COHORT_KIND={expected_kind!r}. Reconstrua no Notebook 03."
        )

    if sha256_file(dataset_path) != manifest.get("dataset_sha256"):
        raise RuntimeError("Hash do dataset supervisionado difere do manifesto.")

    frame = pd.read_parquet(dataset_path, columns=list(columns) if columns else None)

    if columns is None:
        validate_supervised_frame(
            frame,
            feature_columns=manifest["feature_columns"],
            target_column=manifest["target_column"],
            partition_column=manifest["partition_column"],
            audit_columns=manifest.get("audit_columns") or None,
        )

    manifest["dataset_path"] = str(dataset_path)
    return frame, manifest


def _select_partition(
    frame: pd.DataFrame,
    manifest: Mapping[str, Any],
    partition: str,
) -> pd.DataFrame:
    col = manifest["partition_column"]
    if col not in frame.columns:
        raise KeyError(f"Coluna de particao ausente no DataFrame: {col!r}")
    return frame.loc[frame[col].astype(str) == partition].reset_index(drop=True)


def split_partitions(
    frame: pd.DataFrame,
    manifest: Mapping[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Devolve ``(treino, validacao)`` a partir da coluna de particao canonica.

    Este e o par consumido durante a fase de selecao de modelo (C2..C6).
    O bloco ``teste`` NAO e exposto aqui de proposito — a avaliacao final
    exige o gate ``G9_holdout`` aprovado e passa por ``holdout_partition``.
    """
    treino    = _select_partition(frame, manifest, _PARTITION_TREINO)
    validacao = _select_partition(frame, manifest, _PARTITION_VALIDACAO)

    if treino.empty:
        raise ValueError("Particao 'treino' vazia no dataset supervisionado.")
    if validacao.empty:
        raise ValueError("Particao 'validacao' vazia no dataset supervisionado.")

    return treino, validacao


def holdout_partition(
    frame: pd.DataFrame,
    manifest: Mapping[str, Any],
) -> pd.DataFrame:
    """Devolve o bloco ``teste`` (holdout).

    Uso disciplinado: so deve ser chamada depois que o gate ``G9_holdout``
    estiver aprovado. A checagem do gate e responsabilidade do fluxo de
    modelagem (ver ``TemporalSplit.concluir_selecao``); esta funcao apenas
    isola o acesso fisico a particao.
    """
    teste = _select_partition(frame, manifest, _PARTITION_TESTE)
    if teste.empty:
        raise ValueError("Particao 'teste' vazia no dataset supervisionado.")
    return teste
```

## `src/evaluation/__init__.py`

- Git: `tracked` · status `clean`
- Size: `1.5 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `641a3e6e599d6b8e24f989bf5323b6168d045aa268aa170c18144dafc9bee5e2`

```python
"""Avaliação: splits temporais, métricas, calibração e análise de erros."""

from src.evaluation.calibration import (
    brier_decomposicao,
    curva_confiabilidade,
    ece,
    mce,
)
from src.evaluation.errors import (
    CriterioTop,
    extrair_falsos_negativos,
    extrair_falsos_positivos,
    matriz_confusao,
    metricas_por_grupo,
    top_erros,
)
from src.evaluation.leakage import (
    LeakageError,
    check_leakage,
)
from src.evaluation.metrics import (
    ArrayLike,
    accuracy,
    auc,
    average_precision,
    brier,
    especificidade,
    f1,
    ic_bootstrap,
    log_loss,
    metricas_completas,
    metricas_por_limiar,
    precision,
    recall,
    sensibilidade,
)
from src.evaluation.temporal import (
    TemporalSplit,
    split_temporal_3way,
)

__all__ = [
    # metrics
    "ArrayLike",
    "accuracy",
    "auc",
    "average_precision",
    "brier",
    "especificidade",
    "f1",
    "ic_bootstrap",
    "log_loss",
    "metricas_completas",
    "metricas_por_limiar",
    "precision",
    "recall",
    "sensibilidade",
    # calibration
    "brier_decomposicao",
    "curva_confiabilidade",
    "ece",
    "mce",
    # errors
    "CriterioTop",
    "extrair_falsos_negativos",
    "extrair_falsos_positivos",
    "matriz_confusao",
    "metricas_por_grupo",
    "top_erros",
    # leakage
    "LeakageError",
    "check_leakage",
    # temporal
    "TemporalSplit",
    "split_temporal_3way",
]
```

## `src/evaluation/calibration.py`

- Git: `tracked` · status `clean`
- Size: `4.6 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `b76e7a28efe53ad9566eb664b60c4f931d78107b539d3c8f6fa903f162b6da94`

```python
"""
Avaliação de calibração de probabilidades.

Complementa ``src/models/calibration.py``:

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

import numpy as np
import pandas as pd

from src.evaluation.metrics import _to_int_labels, _to_np

ArrayLike = np.ndarray | pd.Series | list


def _bins_digitize(p: np.ndarray, n_bins: int) -> np.ndarray:
    """Índice do bin (0..n_bins-1) de cada probabilidade em ``[0, 1]``."""
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    return np.clip(np.digitize(p, edges[1:-1], right=True), 0, n_bins - 1)


def _linha_vazia(b: int, edges: np.ndarray) -> dict[str, float]:
    return {
        "bin_centro":    float((edges[b] + edges[b + 1]) / 2),
        "freq_positiva": float("nan"),
        "n":             0.0,
        "gap":           float("nan"),
    }


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
    y      = _to_int_labels(y_true)
    p      = _to_np(y_prob)
    edges  = np.linspace(0.0, 1.0, n_bins + 1)
    idx    = _bins_digitize(p, n_bins)

    linhas: list[dict[str, float]] = []
    for b in range(n_bins):
        m = idx == b
        n = int(m.sum())

        if n == 0:
            linhas.append(_linha_vazia(b, edges))
            continue

        centro = float(p[m].mean())
        freq   = float(y[m].mean())
        linhas.append({
            "bin_centro":    centro,
            "freq_positiva": freq,
            "n":             float(n),
            "gap":           abs(freq - centro),
        })

    return pd.DataFrame(linhas)


def ece(
    y_true: ArrayLike,
    y_prob: ArrayLike,
    n_bins: int = 10,
) -> float:
    """Expected Calibration Error — média ponderada dos gaps por bin."""
    tabela = curva_confiabilidade(y_true, y_prob, n_bins=n_bins)
    total  = float(tabela["n"].sum())

    if total == 0:
        return float("nan")

    pesos = tabela["n"] / total
    gaps  = tabela["gap"].fillna(0.0)
    return float((pesos * gaps).sum())


def mce(
    y_true: ArrayLike,
    y_prob: ArrayLike,
    n_bins: int = 10,
) -> float:
    """Maximum Calibration Error — o pior gap entre os bins."""
    tabela = curva_confiabilidade(y_true, y_prob, n_bins=n_bins)
    gaps   = tabela["gap"].dropna()

    if gaps.empty:
        return float("nan")

    return float(gaps.max())


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
        raise ValueError("y_true vazio — não há como decompor o Brier.")

    base_rate   = float(y.mean())
    uncertainty = base_rate * (1.0 - base_rate)
    brier_obs   = float(np.mean((p - y) ** 2))
    idx         = _bins_digitize(p, n_bins)

    reliability = 0.0
    resolution  = 0.0

    for b in range(n_bins):
        m   = idx == b
        n_b = int(m.sum())

        if n_b == 0:
            continue

        freq_obs  = float(y[m].mean())
        freq_pred = float(p[m].mean())
        peso      = n_b / n

        reliability += peso * (freq_obs - freq_pred) ** 2
        resolution  += peso * (freq_obs - base_rate) ** 2

    return {
        "brier":       brier_obs,
        "reliability": float(reliability),
        "resolution":  float(resolution),
        "uncertainty": float(uncertainty),
        "n":           float(n),
    }
```

## `src/evaluation/errors.py`

- Git: `tracked` · status `clean`
- Size: `5.5 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `7a6e18f4d634a243771a6d0408cef798c3acc96c9b14fbbc559cd50477334dad`

```python
"""
Análise de erros: quem o modelo erra, por quanto, e em quais grupos.

A checagem de leakage vive em ``src/evaluation/leakage`` — importe de lá::

    from src.evaluation.leakage import LeakageError, check_leakage
"""

from __future__ import annotations

from typing import Literal

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

__all__ = [
    "ArrayLike",
    "CriterioTop",
    "matriz_confusao",
    "extrair_falsos_positivos",
    "extrair_falsos_negativos",
    "metricas_por_grupo",
    "top_erros",
]

ArrayLike   = np.ndarray | pd.Series | list
CriterioTop = Literal["fp", "fn", "erro_absoluto"]


def _validar_tamanhos(df: pd.DataFrame, y: np.ndarray) -> None:
    """Garante que ``df`` e os rótulos têm o mesmo número de linhas."""
    if len(df) != len(y):
        raise ValueError(f"df tem {len(df)} linhas e y_true tem {len(y)}.")


def matriz_confusao(
    y_true: ArrayLike,
    y_pred: ArrayLike,
) -> pd.DataFrame:
    """
    Matriz de confusão 2×2 como DataFrame.

    Colunas: ``["pred_0", "pred_1"]``, índice: ``["real_0", "real_1"]``.
    Adiciona linha/coluna ``"total"``.
    """
    y = _to_int_labels(y_true)
    p = _to_int_labels(y_pred)

    contagens = {
        (yv, pv): int(((y == yv) & (p == pv)).sum())
        for yv in (0, 1)
        for pv in (0, 1)
    }

    df = pd.DataFrame(
        [[contagens[(0, 0)], contagens[(0, 1)]],
         [contagens[(1, 0)], contagens[(1, 1)]]],
        index=["real_0", "real_1"],
        columns=["pred_0", "pred_1"],
    )
    df["total"] = df.sum(axis=1)
    df.loc["total"] = df.sum(axis=0)
    return df


def _extrair_por_mascara(
    df: pd.DataFrame,
    y_true: ArrayLike,
    y_pred: ArrayLike,
    *,
    yv: int,
    pv: int,
) -> pd.DataFrame:
    """Linhas de ``df`` onde ``y_true == yv`` e ``y_pred == pv``."""
    y = _to_int_labels(y_true)
    p = _to_int_labels(y_pred)
    return df.loc[(y == yv) & (p == pv)].reset_index(drop=True)


def extrair_falsos_positivos(
    df: pd.DataFrame,
    y_true: ArrayLike,
    y_pred: ArrayLike,
) -> pd.DataFrame:
    """Linhas de ``df`` onde o modelo previu 1 mas o real é 0."""
    return _extrair_por_mascara(df, y_true, y_pred, yv=0, pv=1)


def extrair_falsos_negativos(
    df: pd.DataFrame,
    y_true: ArrayLike,
    y_pred: ArrayLike,
) -> pd.DataFrame:
    """Linhas de ``df`` onde o modelo previu 0 mas o real é 1."""
    return _extrair_por_mascara(df, y_true, y_pred, yv=1, pv=0)


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
    Métricas por categoria de ``coluna_grupo`` (ex.: ``"sg_uf"``).

    Ignora grupos com menos de ``min_n`` amostras (evita métricas instáveis).
    Colunas: ``grupo, n, taxa_positivos, auc, f1, precision, recall``.
    """
    if coluna_grupo not in df.columns:
        raise KeyError(f"Coluna de grupo ausente: {coluna_grupo!r}")

    y = _to_int_labels(y_true)
    p = _to_np(y_prob)
    _validar_tamanhos(df, y)

    base   = df.reset_index(drop=True)
    grupos = base[coluna_grupo].astype("string")

    linhas: list[dict[str, float | str]] = []

    for g in grupos.dropna().unique():
        m = (grupos == g).to_numpy()
        n = int(m.sum())

        if n < min_n:
            continue

        y_g    = y[m]
        p_g    = p[m]
        y_pred = (p_g >= limiar).astype(int)

        linhas.append({
            "grupo":          str(g),
            "n":              float(n),
            "taxa_positivos": float(y_g.mean()),
            "auc":            auc(y_g, p_g) if len(np.unique(y_g)) >= 2 else np.nan,
            "f1":             f1(y_g, y_pred),
            "precision":      precision(y_g, y_pred),
            "recall":         recall(y_g, y_pred),
        })

    return (
        pd.DataFrame(linhas)
        .sort_values("n", ascending=False)
        .reset_index(drop=True)
    )


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
    Retorna as ``n`` linhas de ``df`` com os piores erros.

    ``criterio``:
        - ``"fp"``            → prob decrescente entre FP
        - ``"fn"``            → prob crescente entre FN
        - ``"erro_absoluto"`` → ``|prob − y|`` decrescente (todos os erros)

    Adiciona colunas ``y_true``, ``y_prob``, ``y_pred``, ``erro_abs``.
    """
    y      = _to_int_labels(y_true)
    p      = _to_np(y_prob)
    y_pred = (p >= limiar).astype(int)
    _validar_tamanhos(df, y)

    out = df.reset_index(drop=True).copy()
    out["y_true"]   = y
    out["y_prob"]   = p
    out["y_pred"]   = y_pred
    out["erro_abs"] = np.abs(p - y)

    if criterio == "fp":
        sel = out[(out.y_true == 0) & (out.y_pred == 1)].sort_values("y_prob", ascending=False)
    elif criterio == "fn":
        sel = out[(out.y_true == 1) & (out.y_pred == 0)].sort_values("y_prob", ascending=True)
    elif criterio == "erro_absoluto":
        sel = out[out.y_true != out.y_pred].sort_values("erro_abs", ascending=False)
    else:
        raise ValueError(f"criterio inválido: {criterio!r}. Use 'fp', 'fn' ou 'erro_absoluto'.")

    return sel.head(n).reset_index(drop=True)
```

## `src/evaluation/leakage.py`

- Git: `tracked` · status `clean`
- Size: `2.1 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `e504ad9142e598ef1d3e6ee4ecc2c63804f5569c5370eaa0ce132cafd9b1bde4`

```python
"""Verificação anti-vazamento de dados.

``check_leakage`` valida que nenhuma coluna proibida aparece em ``X``.
A lista efetiva é a união de:

- ``forbidden_columns`` (explícito) OU ``features.proibidas`` do YAML;
- ``DEFAULT_LEAKAGE_COLUMNS`` (desfecho, tratamentos, clusters);
- ``target_column`` (explícito) OU ``target.coluna`` do YAML.
"""

from __future__ import annotations

from typing import Iterable

import pandas as pd

from src.utils import config as C

__all__ = ["LeakageError", "check_leakage"]


class LeakageError(RuntimeError):
    """Erro lançado quando variáveis com vazamento são encontradas."""


DEFAULT_LEAKAGE_COLUMNS = frozenset({
    "evolucao", "dt_evoluca", "dt_encerra",
    "uti", "utilizouvni", "suport_ven",
    "antiviral", "antivirais",
    "classificacao_final",
    "cluster", "cluster_rotulo",
})


def _resolve_forbidden_columns(
    forbidden_columns: Iterable[str] | None,
    target_column: str | None,
) -> set[str]:
    """Conjunto efetivo de colunas proibidas.

    Prioridade: ``forbidden_columns`` explícito > ``features.proibidas``
    do YAML. Sempre soma ``DEFAULT_LEAKAGE_COLUMNS`` e o alvo.
    """
    base = (
        set(forbidden_columns)
        if forbidden_columns is not None
        else set(C.cfg("features", "proibidas") or [])
    )
    base |= DEFAULT_LEAKAGE_COLUMNS

    target = target_column if target_column is not None else C.cfg("target", "coluna")
    if target:
        base.add(target)
    return base


def check_leakage(
    X: pd.DataFrame,
    *,
    forbidden_columns: Iterable[str] | None = None,
    target_column: str | None = None,
) -> None:
    """Levanta ``LeakageError`` se ``X`` contiver colunas proibidas.

    ``forbidden_columns=None`` usa ``features.proibidas`` do YAML;
    ``target_column=None`` usa ``target.coluna`` do YAML.
    """
    forbidden = _resolve_forbidden_columns(forbidden_columns, target_column)
    if detected := sorted(set(X.columns) & forbidden):
        raise LeakageError(f"Variáveis de leakage detectadas: {', '.join(detected)}")
```

## `src/evaluation/metrics.py`

- Git: `tracked` · status `clean`
- Size: `7.5 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `a2536cd3cc53d9a5e7ebe6320a4e0011043d1dccf51803d84abe85eaf5184c14`

```python
"""
Métricas de classificação binária — todas retornam ``float``.

Encapsula o scikit-learn para garantir ``float``: em várias funções ele
retorna ``Float | ndarray``, o que polui o type-checker.

Oferece ainda:
    - ``metricas_por_limiar`` → tabela varrendo limiares
    - ``ic_bootstrap``        → intervalo de confiança por bootstrap

``ap`` (average precision) e ``pr_auc`` são a **mesma métrica** — a
chave ``pr_auc`` é um alias mantido para compatibilidade com consumidores
que usam essa nomenclatura (ex.: C4). Ambas apontam para o mesmo valor.
"""

from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    f1_score,
    log_loss as sk_log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)

__all__ = [
    "ArrayLike",
    "auc",
    "average_precision",
    "brier",
    "log_loss",
    "f1",
    "precision",
    "recall",
    "accuracy",
    "especificidade",
    "sensibilidade",
    "metricas_completas",
    "metricas_por_limiar",
    "ic_bootstrap",
]

ArrayLike = np.ndarray | pd.Series | list


def _to_np(x: ArrayLike) -> np.ndarray:
    return np.asarray(x).ravel()


def _to_int_labels(y: ArrayLike) -> np.ndarray:
    return np.asarray(y).ravel().astype(int)


def _contagens_confusao(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> tuple[int, int, int, int]:
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    return tp, fp, tn, fn


def _especificidade_de_contagens(tn: int, fp: int) -> float:
    """``TN / (TN + FP)``; 0.0 quando não há negativo real."""
    denom = tn + fp
    return tn / denom if denom > 0 else 0.0


def auc(y_true: ArrayLike, y_prob: ArrayLike) -> float:
    return float(roc_auc_score(_to_int_labels(y_true), _to_np(y_prob)))


def average_precision(y_true: ArrayLike, y_prob: ArrayLike) -> float:
    return float(average_precision_score(_to_int_labels(y_true), _to_np(y_prob)))


def brier(y_true: ArrayLike, y_prob: ArrayLike) -> float:
    return float(brier_score_loss(_to_int_labels(y_true), _to_np(y_prob)))


def log_loss(y_true: ArrayLike, y_prob: ArrayLike) -> float:
    """Log loss (entropia cruzada binária) sobre probabilidades."""
    return float(sk_log_loss(_to_int_labels(y_true), _to_np(y_prob), labels=[0, 1]))


def f1(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    return float(f1_score(
        _to_int_labels(y_true), _to_int_labels(y_pred), zero_division=0,
    ))


def precision(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    return float(precision_score(
        _to_int_labels(y_true), _to_int_labels(y_pred), zero_division=0,
    ))


def recall(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    return float(recall_score(
        _to_int_labels(y_true), _to_int_labels(y_pred), zero_division=0,
    ))


def accuracy(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    return float(accuracy_score(
        _to_int_labels(y_true), _to_int_labels(y_pred),
    ))


def especificidade(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    """Especificidade = ``TN / (TN + FP)`` — recall da classe negativa."""
    _, fp, tn, _ = _contagens_confusao(
        _to_int_labels(y_true), _to_int_labels(y_pred),
    )
    return _especificidade_de_contagens(tn, fp)


def sensibilidade(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    """Alias semântico de ``recall`` — alinha com a chave do YAML."""
    return recall(y_true, y_pred)


def metricas_completas(
    y_true: ArrayLike,
    y_prob: ArrayLike,
    limiar: float = 0.5,
) -> dict[str, float]:
    """
    Dict com todas as métricas agregadas — pronto para ``Run.metrica(**d)``.

    ``pr_auc`` é **alias** de ``ap`` (ambos = ``average_precision_score``),
    mantido por compatibilidade com consumidores que usam esse nome (ex.: C4).
    """
    y      = _to_int_labels(y_true)
    p      = _to_np(y_prob)
    y_pred = (p >= limiar).astype(int)
    ap     = average_precision(y, p)

    return {
        "auc":            auc(y, p),
        "ap":             ap,
        "pr_auc":         ap,
        "brier":          brier(y, p),
        "log_loss":       log_loss(y, p),
        "f1":             f1(y, y_pred),
        "precision":      precision(y, y_pred),
        "recall":         recall(y, y_pred),
        "sensibilidade":  sensibilidade(y, y_pred),
        "especificidade": especificidade(y, y_pred),
        "accuracy":       accuracy(y, y_pred),
        "limiar":         float(limiar),
        "n":              float(len(y)),
    }


def metricas_por_limiar(
    y_true: ArrayLike,
    y_prob: ArrayLike,
    n_limiares: int = 101,
) -> pd.DataFrame:
    """
    Tabela com métricas para cada limiar em ``[0.01, 0.99]``.

    Colunas: ``limiar, tp, fp, tn, fn, f1, precision, recall,
    sensibilidade, especificidade, accuracy, youden_j``.

    ``youden_j`` = sensibilidade + especificidade − 1, útil para escolher
    o limiar que maximiza a separação entre as classes. As contagens de
    confusão ficam expostas para permitir derivar qualquer outra métrica
    a posteriori — não há tabela paralela de lambdas.
    """
    y = _to_int_labels(y_true)
    p = _to_np(y_prob)

    linhas: list[dict[str, float]] = []

    for th in np.linspace(0.01, 0.99, n_limiares):
        lim    = float(th)
        y_pred = (p >= lim).astype(int)

        tp, fp, tn, fn = _contagens_confusao(y, y_pred)
        rec = recall(y, y_pred)
        esp = _especificidade_de_contagens(tn, fp)

        linhas.append({
            "limiar":         lim,
            "tp":             tp,
            "fp":             fp,
            "tn":             tn,
            "fn":             fn,
            "f1":             f1(y, y_pred),
            "precision":      precision(y, y_pred),
            "recall":         rec,
            "sensibilidade":  rec,
            "especificidade": esp,
            "accuracy":       accuracy(y, y_pred),
            "youden_j":       rec + esp - 1.0,
        })

    return pd.DataFrame(linhas)


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

    Retorna ``(estimativa, limite_inferior, limite_superior)``. Amostras
    degeneradas (uma única classe) são descartadas internamente. Métrica
    default é ``auc``; ``alpha=0.05`` corresponde a IC 95%.
    """
    y = _to_int_labels(y_true)
    p = _to_np(y_prob)
    n = len(y)

    rng     = np.random.default_rng(seed)
    valores = np.empty(n_boot, dtype="float64")

    for i in range(n_boot):
        idx = rng.integers(0, n, size=n)
        valores[i] = (
            metrica(y[idx], p[idx]) if len(np.unique(y[idx])) >= 2 else np.nan
        )

    est     = float(metrica(y, p))
    validos = valores[~np.isnan(valores)]

    if validos.size == 0:
        return est, float("nan"), float("nan")

    return (
        est,
        float(np.quantile(validos, alpha / 2)),
        float(np.quantile(validos, 1 - alpha / 2)),
    )
```

## `src/evaluation/temporal.py`

- Git: `tracked` · status `clean`
- Size: `7.4 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `eb8b768efe8484f354dd034bc536c2db975744457cc1c9e659d64c2b80458546`

```python
"""
Split temporal em três blocos + trava do holdout.

⚠️  Ferramenta de **sensibilidade temporal** — NÃO é o split oficial.
O split oficial do projeto é o **aleatório estratificado**, gerado no
Notebook 03 e persistido em `dataset_supervisionado.parquet` (usado por
C2, C3, C5, C6). Este módulo serve para perguntas do tipo "o desempenho
se mantém se eu treinar no passado e testar no futuro?".

Regra de ouro (quando usado):
    treino + validacao → escolha de modelo
    holdout            → UMA ÚNICA vez, após ``concluir_selecao()``

A classe ``TemporalSplit`` bloqueia o acesso ao holdout enquanto o gate
``G9_holdout`` não estiver aprovado.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, get_args

import pandas as pd

from src.utils import config as C

OnNat = Literal["raise", "drop"]
_ON_NAT_VALORES = frozenset(get_args(OnNat))


def _validar_fracao(nome: str, valor: float) -> None:
    if not 0 < valor < 1:
        raise ValueError(f"{nome} deve estar em (0, 1); recebido {valor!r}.")


def _validar_coluna_tempo(df: pd.DataFrame, coluna_tempo: str) -> None:
    if coluna_tempo not in df.columns:
        raise KeyError(f"Coluna temporal ausente: {coluna_tempo!r}")
    if not pd.api.types.is_datetime64_any_dtype(df[coluna_tempo]):
        raise TypeError(
            f"Coluna temporal {coluna_tempo!r} não é datetime "
            f"(dtype atual: {df[coluna_tempo].dtype}). "
            "Converta com pd.to_datetime antes do split."
        )


def _tratar_nat(
    df: pd.DataFrame,
    coluna_tempo: str,
    on_nat: OnNat,
) -> pd.DataFrame:
    """Remove ``NaT`` em ``coluna_tempo`` conforme ``on_nat``."""
    nat_mask = df[coluna_tempo].isna()
    n_nat    = int(nat_mask.sum())

    if not n_nat:
        return df
    if on_nat == "raise":
        raise ValueError(
            f"{n_nat} linha(s) com data inválida (NaT) em "
            f"{coluna_tempo!r}. Remova-as antes ou use on_nat='drop'."
        )
    return df.loc[~nat_mask].reset_index(drop=True)


def split_temporal_3way(
    df: pd.DataFrame,
    coluna_tempo: str,
    frac_treino: float = 0.7,
    frac_validacao: float = 0.15,
    *,
    on_nat: OnNat = "raise",
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Divide em treino / validação / holdout, **sem embaralhar**.

    Garante, na ordem temporal::

        max(treino[coluna_tempo]) <= min(validacao[coluna_tempo])
        max(validacao[coluna_tempo]) <= min(holdout[coluna_tempo])

    ``on_nat='raise'`` (default) falha se houver ``NaT``; ``'drop'``
    remove essas linhas antes de ordenar.
    """
    if on_nat not in _ON_NAT_VALORES:
        raise ValueError(
            f"on_nat inválido: {on_nat!r}. Use {sorted(_ON_NAT_VALORES)}."
        )

    _validar_fracao("frac_treino",    frac_treino)
    _validar_fracao("frac_validacao", frac_validacao)
    if frac_treino + frac_validacao >= 1:
        raise ValueError(
            "frac_treino + frac_validacao deve ser < 1 (resto vira holdout)."
        )

    _validar_coluna_tempo(df, coluna_tempo)
    df = _tratar_nat(df, coluna_tempo, on_nat)

    ordenado = df.sort_values(coluna_tempo, kind="mergesort").reset_index(drop=True)
    n = len(ordenado)
    if n < 3:
        raise ValueError(f"Dataset pequeno demais para split 3-way: n={n}")

    corte_treino = int(n * frac_treino)
    corte_valid  = int(n * (frac_treino + frac_validacao))

    return (
        ordenado.iloc[:corte_treino].reset_index(drop=True),
        ordenado.iloc[corte_treino:corte_valid].reset_index(drop=True),
        ordenado.iloc[corte_valid:].reset_index(drop=True),
    )


@dataclass
class TemporalSplit:
    """Guarda os três blocos e controla o acesso ao holdout.

    ⚠️  Ferramenta de **sensibilidade temporal**, não o split oficial.
    Uso típico::

        split = TemporalSplit(df, coluna_tempo="dt_notific")
        tr, va = split.treino_validacao()  # seleção
        split.concluir_selecao()           # exige G9_holdout aprovado
        ho = split.holdout()               # avaliação, uma vez
    """

    df: pd.DataFrame
    coluna_tempo: str
    frac_treino: float = 0.7
    frac_validacao: float = 0.15
    on_nat: OnNat = "raise"

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
            on_nat=self.on_nat,
        )
        self._treino    = tr
        self._validacao = va
        self._holdout   = ho

    def treino_validacao(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """``(treino, validacao)`` — único par para a fase de seleção."""
        return self._treino, self._validacao

    @property
    def treino(self) -> pd.DataFrame:
        return self._treino

    @property
    def validacao(self) -> pd.DataFrame:
        return self._validacao

    def concluir_selecao(self) -> None:
        """Libera o holdout após o gate ``G9_holdout`` estar aprovado.

        O gate é a autorização explícita — G7 e G8 tratam de decisões da
        fase de seleção e devem ter sido fechados *antes* deste ponto.
        Chamar **uma única vez**, após congelar modelo, calibração e limiar.
        """
        gate   = C.cfg("gates", "G9_holdout") or {}
        status = gate.get("status")
        if status != "aprovado":
            raise RuntimeError(
                "Holdout bloqueado: gate `G9_holdout` ainda não aprovado "
                f"(status atual: {status!r}). Feche o gate em "
                "`configs/supervised.yaml` antes de chamar `concluir_selecao()`."
            )
        self._holdout_liberado = True

    @property
    def holdout_liberado(self) -> bool:
        return self._holdout_liberado

    def holdout(self) -> pd.DataFrame:
        """Bloco de holdout. Levanta ``RuntimeError`` se ainda bloqueado."""
        if not self._holdout_liberado:
            raise RuntimeError(
                "Holdout bloqueado. Chame `split.concluir_selecao()` antes."
            )
        return self._holdout

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
        """Resumo legível — bom para log no ``Run``."""

        def _periodo(d: pd.DataFrame) -> str:
            if d.empty:
                return "vazio"
            return f"{d[self.coluna_tempo].min()} .. {d[self.coluna_tempo].max()}"

        estado = "liberado" if self._holdout_liberado else "bloqueado"
        return (
            f"TemporalSplit(coluna={self.coluna_tempo!r}, "
            f"papel='sensibilidade_temporal')\n"
            f"  treino    : {self.n_treino:>10,}  {_periodo(self._treino)}\n"
            f"  validacao : {self.n_validacao:>10,}  {_periodo(self._validacao)}\n"
            f"  holdout   : {self.n_holdout:>10,}  {_periodo(self._holdout)}  ({estado})"
        )
```

## `src/features/__init__.py`

- Git: `tracked` · status `clean`
- Size: `508 B` · modified `2026-10-17 19:30 UTC`
- SHA-256: `bd18b2388ca98116b750d5ffea5c9471d3b169ae4be762c417a6195ed525cc34`

```python
"""Engenharia de atributos do pipeline supervisionado."""

from src.features.engineering import (
    COLUNAS_DERIVADAS,
    ano_mes_internacao,
    faixa_etaria,
    idade_em_anos,
    intervalo_sintomas_internacao,
    montar_features,
    sazonalidade,
    sexo_categoria,
)

__all__ = [
    "COLUNAS_DERIVADAS",
    "ano_mes_internacao",
    "faixa_etaria",
    "idade_em_anos",
    "intervalo_sintomas_internacao",
    "montar_features",
    "sazonalidade",
    "sexo_categoria",
]
```

## `src/features/engineering.py`

- Git: `tracked` · status `clean`
- Size: `8.0 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `6dc551fb32ada10a58850fe4481627da9855ebcbe58fb7b84e821030e8e61846`

```python
"""Engenharia de atributos do pipeline supervisionado.

Centraliza as derivadas aplicadas pela Pessoa A / Notebook 03. Cada função
transforma colunas disponíveis na admissão hospitalar em atributos prontos
para o modelo — nenhuma usa informação posterior ao desfecho.

As regras (faixas etárias, política de intervalos, sazonalidade) vêm de
``features.engenharia`` no ``configs/supervised.yaml``, com defaults locais
quando o YAML não define nada.
"""

from __future__ import annotations

from typing import Literal, get_args

import numpy as np
import pandas as pd

from src.utils import config as C

__all__ = [
    "COLUNAS_DERIVADAS",
    "idade_em_anos",
    "intervalo_sintomas_internacao",
    "sazonalidade",
    "faixa_etaria",
    "sexo_categoria",
    "ano_mes_internacao",
    "montar_features",
]

PoliticaIntervalo = Literal["sinalizar", "descartar"]

_INTERVALO_MAX_DIAS_PADRAO = 60.0
_SEMANAS_POR_ANO           = 52.18
_POLITICAS_VALIDAS         = frozenset(get_args(PoliticaIntervalo))

_FAIXAS_PADRAO: tuple[tuple[str, float, float | None], ...] = (
    ("<1",    0.0,   1.0),
    ("1-4",   1.0,   5.0),
    ("5-11",  5.0,  12.0),
    ("12-17", 12.0, 18.0),
    ("18-39", 18.0, 40.0),
    ("40-59", 40.0, 60.0),
    ("60-79", 60.0, 80.0),
    ("80+",   80.0, None),
)

COLUNAS_DERIVADAS: tuple[str, ...] = (
    "idade_anos",
    "dias_sintomas_ate_internacao",
    "sin_semana",
    "cos_semana",
    "ano_internacao",
    "mes_internacao",
    "flag_intervalo_invalido",
    "flag_internacao_antes_sintomas",
    "faixa_etaria",
    "sexo_categoria",
)


def _intervalo_max_dias() -> float:
    valor = C.cfg("features", "engenharia", "intervalo_max_dias")
    return _INTERVALO_MAX_DIAS_PADRAO if valor is None else float(valor)


def _intervalo_politica() -> PoliticaIntervalo:
    valor = C.cfg("features", "engenharia", "intervalo_politica")
    if valor is None:
        return "sinalizar"

    politica = str(valor).strip().lower()
    if politica not in _POLITICAS_VALIDAS:
        raise ValueError(
            f"features.engenharia.intervalo_politica inválida: {valor!r}. "
            f"Use uma de {sorted(_POLITICAS_VALIDAS)}."
        )
    return politica  # type: ignore[return-value]


def _faixas_etarias() -> list[tuple[str, float, float | None]]:
    bruto = C.cfg("features", "engenharia", "faixas_etarias")
    if not bruto:
        return list(_FAIXAS_PADRAO)

    return [
        (
            str(item["nome"]),
            float(item["min"]),
            None if item.get("max") is None else float(item["max"]),
        )
        for item in bruto
    ]


def idade_em_anos(df: pd.DataFrame) -> pd.Series:
    """
    Converte nu_idade_n + tp_idade (SIVEP) em idade em anos.

    tp_idade: 1=dias, 2=meses, 3=anos. Retorna float64 com NaN quando
    a codificação é desconhecida, a idade é negativa ou excede 120.
    """
    idade = pd.to_numeric(df["nu_idade_n"], errors="coerce")
    tipo  = pd.to_numeric(df["tp_idade"],   errors="coerce")

    anos = pd.Series(
        np.select(
            [tipo.eq(1), tipo.eq(2), tipo.eq(3)],
            [idade / 365.25, idade / 12.0, idade],
            default=np.nan,
        ),
        index=df.index,
        dtype="float64",
    )

    invalido = idade.isna() | idade.lt(0) | ~tipo.isin([1, 2, 3]) | anos.gt(120)
    return anos.where(~invalido)


def intervalo_sintomas_internacao(df: pd.DataFrame) -> pd.DataFrame:
    """
    Deriva dias entre dt_sin_pri e dt_interna, com flags de invalidade.

    Colunas: ``dias_sintomas_ate_internacao`` (float64), ``flag_intervalo_invalido``
    (int8), ``flag_internacao_antes_sintomas`` (int8). A política de valores
    fora de ``[0, intervalo_max_dias]`` vem de
    ``features.engenharia.intervalo_politica``.
    """
    max_dias = _intervalo_max_dias()
    politica = _intervalo_politica()

    dt_sin = pd.to_datetime(df["dt_sin_pri"], errors="coerce")
    dt_int = pd.to_datetime(df["dt_interna"], errors="coerce")

    delta = (dt_int - dt_sin).dt.days.astype("float64")

    invalido = delta.isna() | delta.lt(0) | delta.gt(max_dias)
    negativo = delta.lt(0)

    delta_final = delta.where(~invalido) if politica == "descartar" else delta

    return pd.DataFrame({
        "dias_sintomas_ate_internacao":   delta_final,
        "flag_intervalo_invalido":        invalido.astype("int8"),
        "flag_internacao_antes_sintomas": negativo.astype("int8"),
    })


def sazonalidade(
    df: pd.DataFrame,
    coluna_data: str | None = None,
) -> pd.DataFrame:
    """
    Codifica a semana ISO como par (seno, cosseno) em ``2π × (semana − 1)/52,18``.

    Coluna default: ``dt_sin_pri`` (ou ``features.engenharia.coluna_sazonalidade``).
    Datas nulas resultam em NaN.
    """
    if coluna_data is None:
        coluna_data = C.cfg("features", "engenharia", "coluna_sazonalidade") or "dt_sin_pri"
    if coluna_data not in df.columns:
        raise KeyError(f"Coluna temporal ausente: {coluna_data!r}")

    datas = pd.to_datetime(df[coluna_data], errors="coerce")

    semana = pd.Series(np.nan, index=df.index, dtype="float64")
    mask = datas.notna()
    if mask.any():
        semana.loc[mask] = (
            datas[mask].dt.isocalendar()["week"].astype("float64").to_numpy()
        )

    angulo = 2.0 * np.pi * (semana - 1.0) / _SEMANAS_POR_ANO

    return pd.DataFrame({
        "sin_semana": np.sin(angulo),
        "cos_semana": np.cos(angulo),
    })


def faixa_etaria(idade_anos: pd.Series) -> pd.Series:
    """
    Categoriza idade em faixas semiabertas ``[min, max)`` do YAML.

    Idade nula vira a categoria explícita ``"desconhecida"``.
    """
    faixas = _faixas_etarias()
    idade  = pd.to_numeric(idade_anos, errors="coerce")

    out = pd.Series("desconhecida", index=idade.index, dtype="object")
    for nome, lo, hi in faixas:
        mask = idade.ge(lo)
        if hi is not None:
            mask &= idade.lt(hi)
        out[mask] = nome

    return out.astype("category")


def sexo_categoria(df: pd.DataFrame) -> pd.Series:
    """
    Normaliza ``cs_sexo`` em categórica explícita.

    ``M`` → masculino; ``F`` → feminino; ``I`` → ignorado; demais/nulo → ausente.
    """
    sexo = df["cs_sexo"].astype("string").str.strip().str.upper()

    out = pd.Series("ausente", index=df.index, dtype="object")
    out[sexo.eq("M")] = "masculino"
    out[sexo.eq("F")] = "feminino"
    out[sexo.eq("I")] = "ignorado"

    return out.astype("category")


def ano_mes_internacao(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extrai ``ano_internacao`` e ``mes_internacao`` de ``dt_interna`` como float64.

    Datas nulas resultam em NaN, mantendo compatibilidade com
    ``SimpleImputer`` e ``StandardScaler``.
    """
    dt = pd.to_datetime(df["dt_interna"], errors="coerce")

    return pd.DataFrame({
        "ano_internacao": dt.dt.year.astype("float64"),
        "mes_internacao": dt.dt.month.astype("float64"),
    })


def montar_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica todas as derivações e devolve cópia de ``df`` com as colunas de
    ``COLUNAS_DERIVADAS`` adicionadas. Não muta a entrada.
    """
    out = df.copy()

    out["idade_anos"] = idade_em_anos(df)

    intervalo = intervalo_sintomas_internacao(df)
    out["dias_sintomas_ate_internacao"]   = intervalo["dias_sintomas_ate_internacao"]
    out["flag_intervalo_invalido"]        = intervalo["flag_intervalo_invalido"]
    out["flag_internacao_antes_sintomas"] = intervalo["flag_internacao_antes_sintomas"]

    saz = sazonalidade(df)
    out["sin_semana"] = saz["sin_semana"]
    out["cos_semana"] = saz["cos_semana"]

    out["faixa_etaria"]   = faixa_etaria(out["idade_anos"])
    out["sexo_categoria"] = sexo_categoria(df)

    ano_mes = ano_mes_internacao(df)
    out["ano_internacao"] = ano_mes["ano_internacao"]
    out["mes_internacao"] = ano_mes["mes_internacao"]

    return out
```

## `src/features/normalization.py`

- Git: `tracked` · status `clean`
- Size: `0 B` · modified `2026-10-17 19:30 UTC`
- SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

```python

```

## `src/models/__init__.py`

- Git: `tracked` · status `clean`
- Size: `1.5 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `193d5ccf3d79ae3e4699f21e442947e652dd4430898e78753ff60f9d2a3a8a76`

```python
"""Modelos supervisionados do Projeto Integrador."""

from src.models.baseline import (
    DummyStrategy,
    build_baseline_pipeline,
    evaluate_baseline,
)
from src.models.boosting import build_boosting_pipeline
from src.models.calibration import (
    MetodoCalibracao,
    Metrica,
    calibrar,
    escolher_limiar,
)
from src.models.factory import (
    Finalista,
    build_finalista,
    finalistas_disponiveis,
)
from src.models.logistic import (
    Penalty,
    Solver,
    build_logistic_pipeline,
)
from src.models.pipeline import (
    ALVO,
    AUSENTE,
    COLUNA_TEMPO,
    FEATURES,
    FEATURES_CATEGORICAS,
    FEATURES_NUMERICAS,
    build_pipeline,
    build_preprocessor,
    criar_alvo_binario,
    filtrar_rotulos_validos,
    random_state,
)

__all__ = [
    # pipeline (constantes + pré-processamento + alvo)
    "ALVO",
    "AUSENTE",
    "COLUNA_TEMPO",
    "FEATURES",
    "FEATURES_CATEGORICAS",
    "FEATURES_NUMERICAS",
    "build_pipeline",
    "build_preprocessor",
    "criar_alvo_binario",
    "filtrar_rotulos_validos",
    "random_state",
    # baseline
    "DummyStrategy",
    "build_baseline_pipeline",
    "evaluate_baseline",
    # logistic
    "Penalty",
    "Solver",
    "build_logistic_pipeline",
    # boosting
    "build_boosting_pipeline",
    # calibração
    "MetodoCalibracao",
    "Metrica",
    "calibrar",
    "escolher_limiar",
    # fábrica
    "Finalista",
    "build_finalista",
    "finalistas_disponiveis",
]
```

## `src/models/baseline.py`

- Git: `tracked` · status `clean`
- Size: `2.2 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `c5d4d8e3a65bda1fe15756cb5169b953cf52aff95ac3e6795e6f3ae60094c43e`

```python
"""
Baseline: ``DummyClassifier`` — piso mínimo de desempenho.

Serve para responder: "o modelo aprendeu algo além da classe majoritária?"
O piso efetivo depende de ``strategy`` — ver ``build_baseline_pipeline``.
"""
from __future__ import annotations

from typing import Literal

import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.pipeline import Pipeline

from src.evaluation.metrics import metricas_completas
from src.models.pipeline import build_preprocessor, random_state

DummyStrategy = Literal[
    "most_frequent",
    "prior",
    "stratified",
    "uniform",
    "constant",
]


def build_baseline_pipeline(
    *,
    strategy: DummyStrategy = "prior",
    preprocessor=None,
) -> Pipeline:
    """``Pipeline`` com pré-processamento + ``DummyClassifier``.

    Estratégias mais úteis como piso:

    - ``"prior"``         → probabilidade constante = prevalência do treino
      (AUC ≈ 0.5 por construção; Brier ainda informativo);
    - ``"most_frequent"`` → sempre a classe majoritária
      (F1/recall = 0 se a positiva for minoria);
    - ``"stratified"``    → amostra respeitando o prior.

    ``preprocessor=None`` usa ``build_preprocessor()``.
    """
    pre = preprocessor if preprocessor is not None else build_preprocessor()

    return Pipeline([
        ("pre", pre),
        ("clf", DummyClassifier(
            strategy=strategy,
            random_state=random_state(),
        )),
    ])


def evaluate_baseline(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_eval: pd.DataFrame,
    y_eval: pd.Series,
    *,
    strategy: DummyStrategy = "prior",
) -> dict[str, str | float]:
    """Treina e avalia um ``DummyClassifier`` — devolve o dict de métricas.

    O dict inclui ``strategy`` (a escolhida) mais todas as chaves de
    ``metricas_completas`` — ver esse módulo para a lista completa.
    """
    pipe = build_baseline_pipeline(strategy=strategy)
    pipe.fit(X_train, y_train)
    y_prob = pipe.predict_proba(X_eval)[:, 1]

    return {
        "strategy": strategy,
        **metricas_completas(y_eval, y_prob, limiar=0.5),
    }
```

## `src/models/boosting.py`

- Git: `tracked` · status `clean`
- Size: `2.0 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `12d703ed5c3cc9f7cb12fd4aa4d961c54f2a24b9c1b1971110fc50c355118f39`

```python
"""
Gradient boosting — ``HistGradientBoostingClassifier`` (nativo do sklearn).

Requer scikit-learn >= 1.2 (``class_weight`` como str ou dict).
"""
from __future__ import annotations

from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.pipeline import Pipeline

from src.models.pipeline import build_preprocessor, random_state


def build_boosting_pipeline(
    *,
    learning_rate: float = 0.05,
    max_iter: int = 500,
    max_depth: int | None = None,
    max_leaf_nodes: int = 31,
    min_samples_leaf: int = 20,
    l2_regularization: float = 0.0,
    early_stopping: bool = False,
    validation_fraction: float = 0.1,
    n_iter_no_change: int = 20,
    class_weight: str | dict | None = "balanced",
    preprocessor=None,
) -> Pipeline:
    """``Pipeline`` de pré-processamento + ``HistGradientBoostingClassifier``.

    Parâmetros cujo default difere do sklearn por decisão do projeto:

    - ``early_stopping=False`` (em vez de ``'auto'``): sem early stopping
      interno, ``max_iter`` é escolhido na validação (gate G6);
    - ``class_weight="balanced"``: ajusta pelo inverso da frequência.

    Os restantes parâmetros seguem a semântica do sklearn
    (``learning_rate``, ``max_depth``, ``max_leaf_nodes``,
    ``min_samples_leaf``, ``l2_regularization``, ``validation_fraction``,
    ``n_iter_no_change``).

    ``preprocessor=None`` usa ``build_preprocessor()``.
    """
    pre = preprocessor if preprocessor is not None else build_preprocessor()

    clf = HistGradientBoostingClassifier(
        learning_rate=learning_rate,
        max_iter=max_iter,
        max_depth=max_depth,
        max_leaf_nodes=max_leaf_nodes,
        min_samples_leaf=min_samples_leaf,
        l2_regularization=l2_regularization,
        early_stopping=early_stopping,
        validation_fraction=validation_fraction,
        n_iter_no_change=n_iter_no_change,
        class_weight=class_weight,
        random_state=random_state(),
    )

    return Pipeline([("pre", pre), ("clf", clf)])
```

## `src/models/calibration.py`

- Git: `tracked` · status `clean`
- Size: `4.3 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `ad67dccc727378dccad80ba90f070646617d99c49e7e1154e1198ad7f17f1c7a`

```python
"""
Calibração de probabilidades e escolha de limiar de decisão.

``calibrar`` envolve um ``Pipeline`` já ajustado em
``CalibratedClassifierCV`` com ``FrozenEstimator`` — o pipeline base
não é re-treinado. ``escolher_limiar`` varre uma grade de limiares e
devolve o ótimo segundo uma métrica, com restrições opcionais de
precision/recall.

A agregação de métricas vive em ``src.evaluation.metrics``.
"""

from __future__ import annotations

from typing import Any, Literal, get_args

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import brier_score_loss, roc_auc_score

from src.evaluation.metrics import metricas_por_limiar

__all__ = [
    "MetodoCalibracao",
    "Metrica",
    "calibrar",
    "escolher_limiar",
]

Metrica          = Literal["f1", "precision", "recall", "accuracy", "youden_j"]
MetodoCalibracao = Literal["isotonic", "sigmoid"]

_METRICAS_VALIDAS = frozenset(get_args(Metrica))
_METODOS_VALIDOS  = frozenset(get_args(MetodoCalibracao))


def calibrar(
    pipeline,
    X_cal: pd.DataFrame,
    y_cal: pd.Series,
    *,
    method: MetodoCalibracao = "isotonic",
):
    """Ajusta um ``CalibratedClassifierCV`` sobre um pipeline congelado.

    Use uma base de calibração distinta do treino do ``pipeline``. O
    pipeline não é re-treinado — o calibrador aprende só o mapeamento
    probabilidade → probabilidade.

    ``"isotonic"`` é não-paramétrico (requer mais dados); ``"sigmoid"``
    (Platt) é paramétrico e mais estável em amostras pequenas.
    """
    if method not in _METODOS_VALIDOS:
        raise ValueError(
            f"method inválido: {method!r}. Use {sorted(_METODOS_VALIDOS)}."
        )

    # Lazy: sklearn.frozen só existe a partir do 1.6 — mantém o módulo
    # importável em ambientes mais antigos (o erro surge só em calibrar()).
    from sklearn.frozen import FrozenEstimator

    modelo = CalibratedClassifierCV(
        estimator=FrozenEstimator(pipeline),
        method=method,
    )
    modelo.fit(X_cal, y_cal)
    return modelo


def escolher_limiar(
    y_true: pd.Series | np.ndarray,
    y_prob: pd.Series | np.ndarray,
    *,
    metrica: Metrica = "f1",
    n_limiares: int = 101,
    min_precision: float | None = None,
    min_recall: float | None = None,
) -> dict[str, Any]:
    """Devolve o limiar ótimo segundo ``metrica`` e um resumo associado.

    Restrições opcionais de ``min_precision`` / ``min_recall`` filtram
    candidatos antes de maximizar ``metrica``; se nada sobrar, levanta
    ``ValueError``.

    Retorna dict com ``limiar``, ``valor`` (da métrica escolhida),
    ``metrica``, ``auc``, ``brier`` e ``tabela`` (grade completa de
    ``metricas_por_limiar``).
    """
    if metrica not in _METRICAS_VALIDAS:
        raise ValueError(
            f"metrica inválida: {metrica!r}. Use {sorted(_METRICAS_VALIDAS)}."
        )

    y_true_arr = np.asarray(y_true).ravel().astype(int)
    y_prob_arr = np.asarray(y_prob).ravel()

    tabela = metricas_por_limiar(y_true_arr, y_prob_arr, n_limiares=n_limiares)

    candidatos = tabela
    filtros: list[str] = []
    if min_precision is not None:
        filtros.append(f"precision ≥ {min_precision}")
        candidatos = candidatos[candidatos["precision"] >= min_precision]
    if min_recall is not None:
        filtros.append(f"recall ≥ {min_recall}")
        candidatos = candidatos[candidatos["recall"] >= min_recall]
    if candidatos.empty:
        restricao = " e ".join(filtros) if filtros else "sem restrição"
        raise ValueError(f"Nenhum limiar atende à(s) restrição(ões): {restricao}.")

    if metrica not in candidatos.columns:
        raise ValueError(
            f"A métrica {metrica!r} não foi produzida por metricas_por_limiar. "
            f"Colunas disponíveis: {sorted(candidatos.columns)}"
        )

    idx_melhor   = candidatos[metrica].idxmax()
    linha_melhor = tabela.loc[[idx_melhor]].iloc[0]

    return {
        "limiar":  float(linha_melhor["limiar"]),
        "valor":   float(linha_melhor[metrica]),
        "metrica": metrica,
        "auc":     float(roc_auc_score(y_true_arr, y_prob_arr)),
        "brier":   float(brier_score_loss(y_true_arr, y_prob_arr)),
        "tabela":  tabela,
    }
```

## `src/models/factory.py`

- Git: `tracked` · status `clean`
- Size: `2.2 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `bd098f04f4a328f10903bbd8ca8ee25642fcc8054a1c946e406e89ad8449251a`

```python
"""
Fábrica de finalistas — ponto único de construção dos modelos de C5/C6.

Hiperparâmetros vêm de ``models.<nome>`` no ``supervised.yaml``; overrides
em ``**overrides`` têm precedência. ``preprocessor=None`` faz cada
construtor usar o default (``build_preprocessor()``).
"""

from __future__ import annotations

from typing import Any, Literal, get_args

from sklearn.pipeline import Pipeline

from src.models.boosting import build_boosting_pipeline
from src.models.logistic import build_logistic_pipeline
from src.utils import config as C

__all__ = ["Finalista", "build_finalista", "finalistas_disponiveis"]

Finalista = Literal["boosting", "logistic"]
_FINALISTAS_VALIDOS = frozenset(get_args(Finalista))


def finalistas_disponiveis() -> tuple[str, ...]:
    """Nomes canônicos dos finalistas registrados, em ordem estável."""
    return tuple(sorted(_FINALISTAS_VALIDOS))


def _kwargs_do_yaml(nome: str) -> dict[str, Any]:
    """Lê ``models.<nome>`` do YAML e devolve kwargs aceitos pelo construtor.

    Descartados: chaves ``busca_*`` (grid de tuning) e valores ``None``
    (deixa o default do construtor agir). Devolve ``{}`` se a secção não
    existir ou não for mapping.
    """
    secao = C.cfg("models", nome)
    if not isinstance(secao, dict):
        return {}
    return {
        k: v
        for k, v in secao.items()
        if v is not None and not k.startswith("busca_")
    }


def build_finalista(
    nome: str,
    *,
    preprocessor=None,
    **overrides: Any,
) -> Pipeline:
    """Constrói o ``Pipeline`` de um finalista pelo nome.

    Levanta ``ValueError`` se ``nome`` não estiver em
    ``finalistas_disponiveis()``. O ``Pipeline`` devolvido **não está
    ajustado** — o caller faz ``fit``.
    """
    if nome not in _FINALISTAS_VALIDOS:
        raise ValueError(
            f"finalista desconhecido: {nome!r}. "
            f"Use um destes: {sorted(_FINALISTAS_VALIDOS)}."
        )

    params = _kwargs_do_yaml(nome) | overrides
    if preprocessor is not None:
        params["preprocessor"] = preprocessor

    if nome == "boosting":
        return build_boosting_pipeline(**params)
    return build_logistic_pipeline(**params)
```

## `src/models/logistic.py`

- Git: `tracked` · status `clean`
- Size: `4.3 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `54130cc65471c262e5e13c152954e741ce077e7ea1ec52361e75a1102732c6c1`

```python
"""
Regressão logística — modelo linear interpretável.

A partir do scikit-learn 1.8, ``penalty`` foi depreciado (remoção prevista
para 1.10) em favor de ``l1_ratio``. A chave ``models.logistic.penalty``
do ``supervised.yaml`` (``"l1"``, ``"l2"`` ou ``"elasticnet"``) é
traduzida para o ``l1_ratio`` equivalente, mantendo a config como fonte
única da verdade sem depender da API depreciada.
"""

from __future__ import annotations

from typing import Literal, cast

from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from src.models.pipeline import build_preprocessor, random_state
from src.utils import config as C

__all__ = ["Penalty", "Solver", "build_logistic_pipeline"]

Solver  = Literal["lbfgs", "liblinear", "newton-cg", "newton-cholesky", "sag", "saga"]
Penalty = Literal["l1", "l2", "elasticnet"]

# Solver × tipo de penalidade efetivo (derivado do l1_ratio final).
_L1_RATIO_SOLVERS: dict[str, frozenset[str]] = {
    "l2":         frozenset({"lbfgs", "liblinear", "newton-cg", "newton-cholesky", "sag", "saga"}),
    "l1":         frozenset({"liblinear", "saga"}),
    "elasticnet": frozenset({"saga"}),
}

_PENALTIES_VALIDAS = ("l1", "l2", "elasticnet")


def _penalty_do_yaml() -> Penalty | None:
    """Lê ``models.logistic.penalty`` do YAML.

    Devolve ``None`` quando a chave está ausente, vazia ou nula — o
    ``l1_ratio`` passado explicitamente é usado sem alteração. Levanta
    ``ValueError`` se a chave existir mas tiver valor desconhecido.
    """
    valor = C.cfg("models", "logistic", "penalty")
    if not valor:
        return None
    if valor not in _PENALTIES_VALIDAS:
        raise ValueError(
            f"models.logistic.penalty inválido: {valor!r}. "
            f"Use uma de {_PENALTIES_VALIDAS}."
        )
    return cast(Penalty, valor)


def _tipo_penalidade(l1_ratio: float) -> str:
    """Classifica o ``l1_ratio`` em ``"l2"``, ``"l1"`` ou ``"elasticnet"``."""
    if l1_ratio == 0.0:
        return "l2"
    if l1_ratio == 1.0:
        return "l1"
    return "elasticnet"


def build_logistic_pipeline(
    *,
    C: float = 1.0,
    l1_ratio: float = 0.0,
    penalty: Penalty | None = None,
    solver: Solver = "lbfgs",
    max_iter: int = 1000,
    class_weight: str | dict | None = "balanced",
    preprocessor=None,
) -> Pipeline:
    """``Pipeline`` de pré-processamento + ``LogisticRegression``.

    ``penalty=None`` (default) lê ``models.logistic.penalty`` do YAML.
    Quando definido, sobrepõe ``l1_ratio``:

    - ``"l2"``          → força ``l1_ratio=0.0``;
    - ``"l1"``          → força ``l1_ratio=1.0``;
    - ``"elasticnet"``  → exige ``0 < l1_ratio < 1``.

    ``l1_ratio`` (0..1) só tem efeito quando ``penalty`` é ``None`` ou
    ``"elasticnet"``. O ``solver`` precisa ser compatível com o tipo
    resultante (ver ``_L1_RATIO_SOLVERS``).

    Levanta ``ValueError`` para ``l1_ratio`` fora de ``[0, 1]``,
    combinação ``solver`` × tipo inválida, ou ``penalty="elasticnet"``
    com ``l1_ratio`` nos extremos.
    """
    if penalty is None:
        penalty = _penalty_do_yaml()

    if penalty == "l2":
        l1_ratio = 0.0
    elif penalty == "l1":
        l1_ratio = 1.0
    elif penalty == "elasticnet" and not 0.0 < l1_ratio < 1.0:
        raise ValueError(
            f"penalty='elasticnet' requer 0 < l1_ratio < 1; "
            f"recebido l1_ratio={l1_ratio!r}."
        )

    if not 0.0 <= l1_ratio <= 1.0:
        raise ValueError(f"l1_ratio deve estar em [0, 1]; recebido {l1_ratio!r}.")

    tipo             = _tipo_penalidade(l1_ratio)
    solvers_validos  = _L1_RATIO_SOLVERS[tipo]
    if solver not in solvers_validos:
        raise ValueError(
            f"combinação inválida: l1_ratio={l1_ratio!r} ({tipo}) "
            f"com solver={solver!r}. Use um destes: {sorted(solvers_validos)}."
        )

    pre = preprocessor if preprocessor is not None else build_preprocessor()

    return Pipeline([
        ("pre", pre),
        ("clf", LogisticRegression(
            C=C,
            l1_ratio=l1_ratio,
            solver=solver,
            max_iter=max_iter,
            class_weight=class_weight,
            random_state=random_state(),
        )),
    ])
```

## `src/models/pipeline.py`

- Git: `tracked` · status `clean`
- Size: `7.0 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `c05a7280b283384e08f2d11a0a0abc77c00c7a961432d6d77f6c160c8a1ac9a1`

```python
"""
Fundação dos modelos supervisionados.

Fonte única de verdade para o pré-processamento e para a derivação do
alvo binário a partir de ``evolucao``, além da leitura da config canônica
(``configs/supervised.yaml``) e da conveniência ``build_pipeline``.

Notebooks e demais modelos devem importar este módulo em vez de
reimplementar o pré-processamento.
"""

from __future__ import annotations

import logging
from typing import Iterable

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.utils import config as C

__all__ = [
    "ALVO",
    "AUSENTE",
    "COLUNA_TEMPO",
    "FEATURES",
    "FEATURES_CATEGORICAS",
    "FEATURES_NUMERICAS",
    "build_pipeline",
    "build_preprocessor",
    "criar_alvo_binario",
    "filtrar_rotulos_validos",
    "random_state",
]

logger = logging.getLogger(__name__)

# Sem defaults próprios: se a config falhar, o import falha — decisão
# deliberada para que um YAML inválido impeça a modelagem cedo.
ALVO: str = C.cfg("target", "coluna")
COLUNA_TEMPO: str = C.cfg("coluna_tempo")

FEATURES_NUMERICAS: list[str] = list(C.cfg("features", "numericas") or [])
FEATURES_CATEGORICAS: list[str] = list(C.cfg("features", "categoricas") or [])

AUSENTE: str = C.cfg("missingness", "categoricas", "valor_ausente")

if _final := C.cfg("features", "final"):
    _fs = set(_final)
    FEATURES_NUMERICAS = [c for c in FEATURES_NUMERICAS if c in _fs]
    FEATURES_CATEGORICAS = [c for c in FEATURES_CATEGORICAS if c in _fs]

FEATURES: list[str] = FEATURES_NUMERICAS + FEATURES_CATEGORICAS


def _alvo_cfg_positivos() -> list[float]:
    """Códigos de ``target.positivos`` do YAML, como floats."""
    return [float(v) for v in (C.cfg("target", "positivos") or [])]


def _alvo_cfg_negativos() -> list[float]:
    """Códigos de ``target.negativos`` do YAML, como floats."""
    return [float(v) for v in (C.cfg("target", "negativos") or [])]


def build_preprocessor(
    numericas: Iterable[str] | None = None,
    categoricas: Iterable[str] | None = None,
) -> ColumnTransformer:
    """``ColumnTransformer`` de pré-processamento.

    - Numéricas: ``SimpleImputer(strategy="median")`` + ``StandardScaler``.
    - Categóricas: ``SimpleImputer(strategy="constant", fill_value=AUSENTE)``
      + ``OneHotEncoder(handle_unknown="ignore")``.

    ``AUSENTE`` vem de ``missingness.categoricas.valor_ausente`` no YAML,
    mantendo o mesmo comportamento do Notebook 03. ``None`` em cada
    parâmetro usa a lista correspondente do YAML.
    """
    num = list(numericas) if numericas is not None else FEATURES_NUMERICAS
    cat = list(categoricas) if categoricas is not None else FEATURES_CATEGORICAS

    pipe_num = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler",  StandardScaler()),
    ])
    pipe_cat = Pipeline([
        ("imputer", SimpleImputer(strategy="constant", fill_value=AUSENTE)),
        ("onehot",  OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])

    return ColumnTransformer(
        transformers=[
            ("num", pipe_num, num),
            ("cat", pipe_cat, cat),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )


def criar_alvo_binario(
    df: pd.DataFrame,
    alvo: str | None = None,
    positivos: Iterable[float] | None = None,
    negativos: Iterable[float] | None = None,
) -> pd.Series:
    """Converte ``evolucao`` em alvo binário (``float64``, NaN onde indefinido).

    ``1`` = óbito SRAG (``target.positivos`` do YAML), ``0`` = cura
    (``target.negativos``). Qualquer outro valor (``3.0``, ``9.0``, nulos)
    vira ``NaN`` — descartado adiante por ``filtrar_rotulos_validos``.

    Argumentos explícitos sobrepõem o YAML. Levanta ``ValueError`` se os
    conjuntos se sobrepuserem ou se algum estiver vazio.
    """
    alvo = alvo if alvo is not None else ALVO

    positivos_set = {
        float(v) for v in (positivos if positivos is not None else _alvo_cfg_positivos())
    }
    negativos_set = {
        float(v) for v in (negativos if negativos is not None else _alvo_cfg_negativos())
    }

    if overlap := positivos_set & negativos_set:
        raise ValueError(
            f"`positivos` e `negativos` não podem se sobrepor: {sorted(overlap)}"
        )
    if not positivos_set:
        raise ValueError("`target.positivos` está vazio na config.")
    if not negativos_set:
        raise ValueError("`target.negativos` está vazio na config.")

    valores = df[alvo].astype("float64")
    y = pd.Series(float("nan"), index=df.index, dtype="float64")
    y[valores.isin(negativos_set)] = 0
    y[valores.isin(positivos_set)] = 1
    return y


def filtrar_rotulos_validos(
    X: pd.DataFrame,
    y: pd.Series,
) -> tuple[pd.DataFrame, pd.Series]:
    """Remove linhas em que ``y`` é NaN. Devolve ``(X, y)`` alinhados (int8)."""
    if not y.index.equals(X.index):
        raise ValueError("X e y precisam ter o mesmo índice.")

    mascara = y.notna()
    return (
        X.loc[mascara].reset_index(drop=True),
        y.loc[mascara].astype("int8").reset_index(drop=True),
    )


def random_state() -> int:
    """Seed canônica do projeto (``config.SEED``)."""
    return int(C.SEED)


def build_pipeline(
    X: pd.DataFrame | None = None,
    y: pd.Series | None = None,
    *,
    classifier: object | None = None,
    features: Iterable[str] | None = None,
    strict: bool = True,
) -> Pipeline:
    """Constrói o ``Pipeline`` sklearn.

    - ``classifier=None`` → devolve só o pré-processamento (útil no C2).
    - ``classifier`` passado (C3+) → anexa como etapa final.
    - ``features=None`` → usa ``FEATURES`` do módulo.
    - ``strict=True`` → levanta ``KeyError`` se alguma feature configurada
      estiver ausente em ``X``; ``False`` → emite warning e segue só com
      as presentes.
    """
    num = list(FEATURES_NUMERICAS)
    cat = list(FEATURES_CATEGORICAS)

    if features is not None:
        fs = set(features)
        num = [c for c in num if c in fs]
        cat = [c for c in cat if c in fs]

    if X is not None:
        if ausentes := sorted((set(num) | set(cat)) - set(X.columns)):
            msg = (
                f"Features configuradas ausentes em X: {ausentes}. "
                "Verifique `features` no supervised.yaml ou o DataFrame "
                "de entrada."
            )
            if strict:
                raise KeyError(msg)
            logger.warning(msg)
            num = [c for c in num if c in X.columns]
            cat = [c for c in cat if c in X.columns]

    pre = build_preprocessor(numericas=num, categoricas=cat)

    etapas: list[tuple[str, object]] = [("pre", pre)]
    if classifier is not None:
        etapas.append(("clf", classifier))

    return Pipeline(etapas)
```

## `src/protocolo/__init__.py`

- Git: `tracked` · status `clean`
- Size: `89 B` · modified `2026-10-17 19:30 UTC`
- SHA-256: `dc84b0499cded1d8b8fe8cffd8906ca4d73a01297f048160dd439decf23dcb02`

```python
"""Verificações e registros da Pessoa A (protocolo, coorte, qualidade, decisões)."""
```

## `src/protocolo/verificacoes.py`

- Git: `tracked` · status `clean`
- Size: `89.8 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `2bf4f22f18037a036d9db390362ee569764e67732feb4adf65d5e3fc51f957fd`

```python
"""
Verificações da Pessoa A (A1–A4) — Projeto Integrador SRAG
==========================================================

Lógica reutilizável usada pelos notebooks `notebooks/A/A1..A4`. Os notebooks só
executam, exibem e documentam; as regras ficam aqui e em `configs/decisoes.yaml`.

  A1  códigos, protocolo e coorte      a1_columns, a1_code_tables, a1_waterfall, a1_target
  A2  qualidade, datas, elegibilidade  a2_missing, a2_dates, a2_duplicates, a2_maturity, a2_eligibility
  A3  desenho experimental e pilotos   a3_config_audit, a3_forbidden, a3_temporal_split,
                                       a3_leak_scan, a3_suspicious_metrics, a3_audit_logs
  A4  candidatos e decisão             a4_decision_table
  Registro                             log_decision (tabela de decisões), write_ata (atas de gate)

As listas de variáveis e ações sugeridas são PROPOSTA INICIAL: confirmar no dicionário
oficial do SIVEP-Gripe e registrar a decisão com `log_decision`.
"""
from __future__ import annotations

MODULE_VERSION = "0.8"  # incrementar quando a assinatura das funções mudar (os notebooks conferem)

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

# =============================================================================
# CONFIGURAÇÃO PADRÃO (a fonte de verdade é configs/decisoes.yaml; ver load_config)
# =============================================================================
DEFAULT_CONFIG: dict = {
    "cols": {
        "hospital": "HOSPITAL",
        "dt_interna": "DT_INTERNA",
        "evolucao": "EVOLUCAO",
        "tp_idade": "TP_IDADE",
        "nu_idade": "NU_IDADE_N",
        "dt_nasc": "DT_NASC",
        "dt_sin_pri": "DT_SIN_PRI",
        "dt_notific": "DT_NOTIFIC",
        "dt_evoluca": "DT_EVOLUCA",
        "dt_encerra": "DT_ENCERRA",
        "nu_notific": "NU_NOTIFIC",
    },
    # Períodos (ano de DT_INTERNA)
    "dev_years": [2022, 2023, 2024],
    "holdout_years": [2025],
    "min_date": "2009-01-01",  # início do SIVEP-Gripe
    # Códigos esperados por campo (strings). Estenda conforme o dicionário.
    "expected_codes": {
        "HOSPITAL": ["1", "2", "9"],
        "EVOLUCAO": ["1", "2", "3", "9"],
        "TP_IDADE": ["1", "2", "3"],
        "UTI": ["1", "2", "9"],
        "FEBRE": ["1", "2", "9"],
        "TOSSE": ["1", "2", "9"],
        "DISPNEIA": ["1", "2", "9"],
        "SATURACAO": ["1", "2", "9"],
    },
    # Alvo: 1 = óbito (EVOLUCAO=2); 0 = cura (EVOLUCAO=1).
    # EVOLUCAO=3 (óbito por outras causas) fica como categoria separada;
    # 9/ausente NUNCA vira cura -> NA e sai da coorte.
    "target_positive": "2",
    "target_negative": "1",
    "target_separate": ["3"],
    "closed_codes": ["1", "2", "3"],
    # Se True, o waterfall exclui registros com inconsistência de datas "excluir"
    "drop_date_inconsistencies": False,
    # Maturidade de EVOLUCAO: mínimo de % encerrados por mês de internação
    "maturity_min_closed_pct": 90.0,
    # Datas: regra, descrição, ação sugerida
    # (excluir | transformar em ausente | manter com flag | apenas documentar)
    "date_rules": [
        ["dt_nasc", "dt_sin_pri", "Nascimento posterior ao início dos sintomas", "excluir"],
        ["dt_sin_pri", "dt_notific", "Início dos sintomas posterior à notificação", "manter com flag"],
        ["dt_sin_pri", "dt_interna", "Início dos sintomas posterior à internação", "manter com flag"],
        ["dt_interna", "dt_evoluca", "Evolução anterior à internação", "excluir"],
        ["dt_evoluca", "dt_encerra", "Encerramento anterior à evolução", "manter com flag"],
    ],
    "max_symptom_to_admission_days": 30,
    "max_age_years": 120,
    # Classificação de variáveis (proposta inicial -> confirmar no dicionário)
    "forbidden_vars": [
        "EVOLUCAO", "DT_EVOLUCA", "DT_ENCERRA", "CLASSI_FIN", "CLASSI_OUT", "CRITERIO",
        "UTI", "DT_ENTUTI", "DT_SAIDUTI", "SUPORT_VEN", "ANTIVIRAL", "DT_ANTIVIR",
        "DT_COLETA", "TP_AMOSTRA", "PCR_RESUL", "DT_PCR", "RES_AN", "DT_RES_AN",
        "RES_IGG", "RES_IGM", "RES_IGA", "DT_RES", "POS_PCRFLU", "POS_PCROUT",
        "HOSPITAL",  # critério de inclusão (constante na coorte), não feature
        "EVOLUCAO_COVID19", "SOROLOGIA", "PCR",
        "UTILIZOUVNI",  # suporte ventilatório: tratamento durante a internação (confirmar)
    ],
    "conditional_vars": [
        "SATURACAO", "VACINA", "VACINA_COV", "DOSE_1_COV", "DOSE_2_COV", "DOSE_REF",
        "SG_UF", "SG_UF_NOT", "CO_MUN_RES", "ID_MN_RESI", "CS_ZONA", "SURTO_SG",
    ],
    "allowed_vars": [
        "CS_SEXO", "NU_IDADE_N", "TP_IDADE", "CS_RACA", "CS_GESTANT", "FEBRE", "TOSSE",
        "GARGANTA", "DISPNEIA", "DESC_RESP", "DIARREIA", "VOMITO", "DOR_ABD", "FADIGA",
        "PERD_OLFT", "PERD_PALA", "CARDIOPATI", "HEMATOLOGI", "SIND_DOWN", "HEPATICA",
        "ASMA", "DIABETES", "NEUROLOGIC", "PNEUMOPATI", "IMUNODEPRE", "RENAL", "OBESIDADE",
        "DT_SIN_PRI", "DT_INTERNA", "DT_NOTIFIC", "SEM_PRI",
    ],
    # Varredura de vazamento univariado
    "leak_auc_threshold": 0.90,
    "leak_max_categories": 50,
    "leak_sample": 200_000,
    "suspicious_metric_threshold": 0.95,
    # Logs: chaves mínimas esperadas (regex, case-insensitive)
    "log_required_keys": {
        "timestamp": r"timestamp|data_hora|datetime",
        "versão": r"vers[aã]o|version",
        "seed": r"seed|semente",
        "config": r"config",
        "variáveis": r"features|vari[aá]veis|columns",
        "folds": r"fold",
        "parâmetros": r"params|par[aâ]metros|hiperpar",
        "artefatos": r"artefato|artifact|output",
    },
    # A4
    "decision_min_pr_auc_gain": 0.01,
    "decision_max_cv_ratio": 0.10,
    "exclusion_sample_rows": 50,
    # População analítica entregue ao C (C2 espera exatamente este arquivo)
    "dataset_analitico": {"path": "data/analytical/dataset_supervisionado.parquet"},
    # Experimentos de split (A3b): aleatório 70-15-15 em cenários de período (anos de DT_INTERNA)
    "experimentos_split": {
        "seed": 42,
        "fracoes": {"treino": 0.70, "validacao": 0.15, "holdout": 0.15},
        "estratificar_por_alvo": True,
        "bench_max_linhas": 200000,
        "cenarios": {
            "todos_2019_2025": {"anos": [2019, 2020, 2021, 2022, 2023, 2024, 2025],
                                "descricao": "Base completa 2019-2025"},
            "sem_2020_2021": {"anos": [2019, 2022, 2023, 2024, 2025],
                              "descricao": "Remove 2020 e 2021 (anos de pandemia)"},
        },
    },
    # Features derivadas criadas na exportação (só com informação disponível na admissão)
    "derivadas": {
        "intervalo_max_dias": 30,          # sintomas -> internação acima disso (ou < 0, ou ausente) = inválido
        "periodo_semanas": 52.1775,        # sazonalidade: sin/cos(2*pi*semana_ISO_da_internação/período)
        "faixas_etarias": {
            "bins": [0, 1, 5, 12, 18, 30, 40, 50, 60, 70, 80, 200],
            "labels": ["<1", "1-4", "5-11", "12-17", "18-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"],
        },
    },
}

OK, WARN, FAIL = "OK", "ATENÇÃO", "FALHA"

# Nomes físicos observados na EDA 01 (Parquet dados-v1, 194 colunas) usados para classificar variáveis.
_EDA_TRATAMENTO = ["ANTIVIRAL", "TP_ANTIVIR", "DT_ANTIVIR", "TRAT_COV", "TIPO_TRAT", "DT_TRT_COV", "OUT_ANTIV", "OUT_TRAT"]
_EDA_DESFECHO = ["EVOLUCAO", "DT_EVOLUCA", "DT_ENCERRA", "DT_DIGITA"]
_EDA_GEOGRAFIA = ["SG_UF_NOT", "CO_REGIONA", "CO_MUN_NOT", "CO_PAIS", "SG_UF", "CO_RG_RESI", "CO_MUN_RES",
                  "SG_UF_INTE", "CO_RG_INTE", "CO_MU_INTE"]
_EDA_VACINACAO = ["VACINA", "DT_UT_DOSE", "MAE_VAC", "DT_VAC_MAE", "M_AMAMENTA", "DT_DOSEUNI", "DT_1_DOSE",
                  "DT_2_DOSE", "VACINA_COV", "DOSE_1_COV", "DOSE_2_COV", "DOSE_REF", "DOSE_2REF", "DOSE_ADIC", "DOS_RE_BI"]
_EDA_SOCIAL_TEXTO = ["PAC_COCBO", "PAC_DSCBO", "POV_CT", "TP_POV_CT", "ESTRANG",
                     "OUTRO_SIN", "OUTRO_DES", "OBES_IMC", "OUT_MORBI", "MORB_DESC"]
_EDA_CANDIDATAS_EXTRA = ["CS_ETINIA", "CS_ESCOL_N", "AVE_SUINO", "OUT_ANIM", "PUERPERA", "TABAG"]

# Nomes alternativos (base da API / supervised.yaml) -> nome canônico SIVEP usado aqui.
# CONFIRMAR no dicionário da base: p.ex. 'internado' é assumido equivalente a HOSPITAL.
ALIASES = {
    "HOSPITAL": ["INTERNADO"],
    "DT_INTERNA": ["DT_INTERNACAO"],
    "DT_EVOLUCA": ["DT_EVOLUCAO"],
    "DT_ENCERRA": ["DT_ENCERRAMENTO"],
    "CLASSI_FIN": ["CLASSIFICACAO_FINAL"],
    "CRITERIO": ["CRITERIO_CONFIRMACAO"],
}
_ALT2CANON = {alt: can for can, alts in ALIASES.items() for alt in alts}


def _merge_lists() -> None:
    """Acrescenta a DEFAULT_CONFIG os grupos da EDA (sem duplicar nem conflitar entre classes)."""
    f, c, a = (DEFAULT_CONFIG[k] for k in ("forbidden_vars", "conditional_vars", "allowed_vars"))
    f += [x for x in _EDA_TRATAMENTO + _EDA_DESFECHO if x not in f]
    c += [x for x in _EDA_GEOGRAFIA + _EDA_VACINACAO + _EDA_SOCIAL_TEXTO if x not in c and x not in f]
    a += [x for x in _EDA_CANDIDATAS_EXTRA if x not in a and x not in f and x not in c]


_merge_lists()


def canon(name) -> str:
    n = str(name).strip().upper()
    return _ALT2CANON.get(n, n)


# =============================================================================
# Utilitários
# =============================================================================
class Report:
    """Acumula achados e grava tabelas/relatório."""

    def __init__(self, out: str | Path, nome: str = "relatorio_pessoa_a"):
        self.nome = nome
        self.out = Path(out)
        self.out.mkdir(parents=True, exist_ok=True)
        self.findings: list[tuple[str, str, str, str]] = []

    def add(self, stage: str, check: str, status: str, detail: str) -> None:
        self.findings.append((stage, check, status, detail))
        icon = {OK: "[ok]", WARN: "[!!]", FAIL: "[XX]"}[status]
        print(f"{icon} {stage} | {check}: {detail}")

    def save(self, name: str, df: pd.DataFrame) -> None:
        df.to_csv(self.out / f"{name}.csv", index=False, encoding="utf-8-sig")

    def write_md(self) -> Path:
        path = self.out / f"{self.nome}.md"
        lines = [f"# Relatório de verificações — {self.nome}", ""]
        lines += ["| Etapa | Verificação | Status | Detalhe |", "| --- | --- | --- | --- |"]
        for stage, check, status, detail in self.findings:
            lines.append(f"| {stage} | {check} | {status} | {detail.replace('|', '/')} |")
        n = {s: sum(1 for f in self.findings if f[2] == s) for s in (OK, WARN, FAIL)}
        lines += ["", f"**Resumo:** {n[OK]} OK · {n[WARN]} atenção · {n[FAIL]} falha(s)."]
        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    @property
    def has_failure(self) -> bool:
        return any(f[2] == FAIL for f in self.findings)


PLAUSIBLE_YEARS = (1900, 2100)  # datas fora disso (0001, 9999, 20224...) viram NaT


def parse_date(s: pd.Series) -> pd.Series:
    """Converte para datetime64[ns] aceitando ISO (aaaa-mm-dd) e dd/mm/aaaa.

    Datas fora de 1900–2100 viram NaT ANTES de qualquer conta (evita OverflowError em
    subtrações/comparações com anos absurdos) e a resolução é padronizada (Parquet pode
    trazer s/ms/us). Quem precisa contar datas inválidas usa `raw.notna() & parsed.isna()`.
    """
    if isinstance(s.dtype, pd.CategoricalDtype):  # converte só as categorias únicas (poucos milhares de datas)
        cats = parse_date(pd.Series(s.cat.categories.astype("string")))
        codes = s.cat.codes.to_numpy()
        arr = cats.to_numpy(dtype="datetime64[ns]") if len(cats) else np.array([], dtype="datetime64[ns]")
        vals = np.full(len(s), np.datetime64("NaT"), dtype="datetime64[ns]")
        ok = codes >= 0
        if ok.any():
            vals[ok] = arr[codes[ok]]
        return pd.Series(vals, index=s.index)
    if pd.api.types.is_datetime64_any_dtype(s):
        out = s
        if getattr(out.dt, "tz", None) is not None:
            out = out.dt.tz_localize(None)
    else:
        t = s.astype("string").str.strip()
        out = pd.to_datetime(t, errors="coerce", format="ISO8601")
        miss = out.isna() & t.notna() & (t != "")
        if miss.any():
            out[miss] = pd.to_datetime(t[miss], errors="coerce", format="%d/%m/%Y")
        miss = out.isna() & t.notna() & (t != "")
        if miss.any():  # formatos mistos (ex.: '05/03/2022 00:00', '2022/03/05')
            try:
                out[miss] = pd.to_datetime(t[miss], errors="coerce", format="mixed", dayfirst=True)
            except (TypeError, ValueError):
                pass
    yr = out.dt.year
    out = out.mask((yr < PLAUSIBLE_YEARS[0]) | (yr > PLAUSIBLE_YEARS[1]))
    return out.astype("datetime64[ns]")


def code_str(s: pd.Series) -> pd.Series:
    """Normaliza códigos (1, 1.0, '1', ' 1 ') para string; vazio -> <NA>."""
    n = pd.to_numeric(s, errors="coerce")
    txt = s.astype("string").str.strip()
    res = txt.where(n.isna(), n.round().astype("Int64").astype("string"))
    return res.mask(res == "")


def make_target(evolucao: pd.Series, cfg: dict = DEFAULT_CONFIG) -> pd.Series:
    """1 = óbito, 0 = cura; qualquer outro valor (inclusive 9/ausente) -> NA."""
    e = code_str(evolucao)
    out = pd.Series(pd.NA, index=e.index, dtype="Int64")
    out[(e == cfg["target_positive"]).fillna(False).to_numpy(bool)] = 1
    out[(e == cfg["target_negative"]).fillna(False).to_numpy(bool)] = 0
    return out


def age_years(df: pd.DataFrame, cfg: dict) -> pd.Series:
    c = cfg["cols"]
    n = pd.to_numeric(df[c["nu_idade"]], errors="coerce").to_numpy(float)
    t = code_str(df[c["tp_idade"]])
    is_ = lambda v: (t == v).fillna(False).to_numpy(bool)  # noqa: E731
    vals = np.select([is_("3"), is_("2"), is_("1")], [n, n / 12, n / 365], default=np.nan)
    return pd.Series(vals, index=df.index)


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    """Padroniza nomes (maiúsculas + aliases -> nome canônico SIVEP). Renomeia IN-PLACE (sem copiar)."""
    up = [str(c).strip().upper() for c in df.columns]
    present = set(up)
    new, renamed = [], []
    for u in up:
        c = canon(u)
        if c != u and c not in present:
            renamed.append(f"{u}->{c}")
            new.append(c)
        else:
            new.append(u)
    df.attrs["orig_names"] = {n: str(o).strip() for o, n in zip(df.columns, new)}  # canônico -> nome original
    df.columns = new
    if renamed:
        print(f"[aliases] colunas renomeadas: {', '.join(renamed)}")
    return df


def year_labels(df: pd.DataFrame, cfg: dict) -> pd.Series:
    dt = parse_date(df[cfg["cols"]["dt_interna"]])
    return dt.dt.year.astype("Int64").astype("string").fillna("sem_data")


def has_cols(df: pd.DataFrame, cols: list[str]) -> list[str]:
    return [c for c in cols if c not in df.columns]


# =============================================================================
# A1 — Códigos, protocolo e coorte
# =============================================================================
def a1_columns(df, cfg, rep: Report) -> None:
    need = list(cfg["cols"].values())
    missing = has_cols(df, need)
    if missing:
        rep.add("A1", "Colunas essenciais", FAIL, f"ausentes: {', '.join(missing)}")
        print("   colunas disponíveis:", ", ".join(map(str, df.columns[:80])))
        print("   -> ajuste 'cols' em configs/decisoes.yaml ou ALIASES em verificacoes.py para os nomes reais da base")
    else:
        rep.add("A1", "Colunas essenciais", OK, f"{len(need)} colunas presentes")


def a1_code_tables(df, cfg, rep: Report) -> None:
    ano = year_labels(df, cfg)
    rows, unexpected = [], []
    for col, expected in cfg["expected_codes"].items():
        if col not in df.columns:
            continue
        codes = code_str(df[col]).fillna("<vazio>")
        tab = pd.crosstab(codes, ano)
        tab.insert(0, "campo", col)
        tab.insert(1, "esperado", [c in expected for c in tab.index])
        rows.append(tab.reset_index(names="codigo"))
        bad = [c for c in tab.index if c not in expected and c != "<vazio>"]
        if bad:
            unexpected.append(f"{col}: {bad}")
    if rows:
        rep.save("a1_tabela_codigos", pd.concat(rows, ignore_index=True))
    if unexpected:
        rep.add("A1", "Códigos inesperados", WARN, "; ".join(unexpected))
    else:
        rep.add("A1", "Códigos inesperados", OK, "todos os códigos dentro do esperado")


def a1_waterfall(df, cfg, rep: Report, sufixo: str = "") -> pd.DataFrame:
    """Aplica os filtros em sequência, registra N antes/depois e amostras das exclusões."""
    c = cfg["cols"]
    today = pd.Timestamp.today().normalize()
    dt = parse_date(df[c["dt_interna"]])
    ok_date = (dt.notna() & (dt <= today) & (dt >= pd.Timestamp(cfg["min_date"]))).to_numpy(bool)
    hosp = (code_str(df[c["hospital"]]) == "1").fillna(False).to_numpy(bool)
    anos = dt.dt.year
    analytic = anos.isin(cfg["dev_years"] + cfg["holdout_years"]).to_numpy(bool)
    evo = code_str(df[c["evolucao"]])
    closed = evo.isin(cfg["closed_codes"]).to_numpy(bool)
    binary = evo.isin([cfg["target_positive"], cfg["target_negative"]]).to_numpy(bool)

    steps = [
        ("Hospitalização confirmada", "HOSPITAL = 1", hosp),
        ("Data de internação válida", f"DT_INTERNA parseável, ≥ {cfg['min_date']} e ≤ hoje", ok_date),
        ("Período analítico", f"ano(DT_INTERNA) em {cfg['dev_years'] + cfg['holdout_years']}", analytic),
        ("Evolução encerrada", f"EVOLUCAO em {cfg['closed_codes']} (9/ausente fora)", closed),
        ("Alvo binário definido", "EVOLUCAO em {cura, óbito}; óbito por outras causas separado", binary),
    ]
    if cfg["drop_date_inconsistencies"]:
        steps.insert(3, ("Coerência de datas", "regras de datas com ação 'excluir'", _date_ok_mask(df, cfg)))

    remaining = np.ones(len(df), dtype=bool)
    rows = [dict(ordem=0, filtro="Base completa", regra="—", n_excluido=0,
                 n_restante=len(df), pct_restante=100.0)]
    sample_cols = [x for x in dict.fromkeys(list(c.values()) + ["NU_NOTIFIC"]) if x in df.columns]
    for i, (name, rule, mask) in enumerate(steps, start=1):
        excl = remaining & ~mask
        kept = remaining & mask
        rows.append(dict(ordem=i, filtro=name, regra=rule, n_excluido=int(excl.sum()),
                         n_restante=int(kept.sum()), pct_restante=round(100 * kept.sum() / len(df), 2)))
        if excl.any():
            smp = df.loc[excl, sample_cols].head(cfg["exclusion_sample_rows"])
            rep.save(f"a1_amostra_exclusoes{sufixo}_{i:02d}", smp)
        remaining = kept
    wf = pd.DataFrame(rows)
    rep.save(f"a1_waterfall{sufixo}", wf)
    final = int(remaining.sum())
    status = OK if final > 0 else FAIL
    rep.add("A1", "Waterfall da coorte" + (f" [{sufixo.strip(chr(95))}]" if sufixo else ""), status,
            f"{len(df):,} -> {final:,} registros ({100 * final / max(len(df), 1):.1f}%)")
    return wf


def _date_ok_mask(df, cfg) -> np.ndarray:
    ok = np.ones(len(df), dtype=bool)
    for a, b, _, action in cfg["date_rules"]:
        if action != "excluir":
            continue
        da, db = parse_date(df[cfg["cols"][a]]), parse_date(df[cfg["cols"][b]])
        ok &= ~((da > db).fillna(False).to_numpy(bool))
    return ok


def a1_cohort(df, cfg) -> pd.DataFrame:
    """Retorna a coorte final (mesmas regras do waterfall) com _ano e _alvo."""
    c = cfg["cols"]
    dt = parse_date(df[c["dt_interna"]])
    today = pd.Timestamp.today().normalize()
    evo = code_str(df[c["evolucao"]])
    m = ((code_str(df[c["hospital"]]) == "1").fillna(False).to_numpy(bool)
         & (dt.notna() & (dt <= today) & (dt >= pd.Timestamp(cfg["min_date"]))).to_numpy(bool)
         & dt.dt.year.isin(cfg["dev_years"] + cfg["holdout_years"]).to_numpy(bool)
         & evo.isin([cfg["target_positive"], cfg["target_negative"]]).to_numpy(bool))
    if cfg["drop_date_inconsistencies"]:
        m &= _date_ok_mask(df, cfg)
    out = df.loc[m].copy()
    out["_ano"] = dt[m].dt.year.astype(int)
    out["_alvo"] = make_target(out[c["evolucao"]], cfg).astype(int)
    return out


def a1_target(df, cfg, rep: Report) -> None:
    c = cfg["cols"]
    ano = year_labels(df, cfg)
    evo = code_str(df[c["evolucao"]]).fillna("<vazio>")
    hosp = (code_str(df[c["hospital"]]) == "1").fillna(False).to_numpy(bool)
    tab = pd.crosstab(ano[hosp], evo[hosp])
    tab["total"] = tab.sum(axis=1)
    rep.save("a1_alvo_por_ano", tab.reset_index(names="ano"))
    # Teste de sanidade: desconhecido nunca pode virar cura
    probe = make_target(pd.Series(["1", "2", "3", "9", None, "", "x"]), cfg)
    expected = [0, 1, None, None, None, None, None]
    ok = all((pd.isna(a) and e is None) or a == e for a, e in zip(probe, expected))
    rep.add("A1", "Alvo: desconhecido ≠ cura", OK if ok else FAIL,
            "9/ausente/3 viram NA; só 1->0 e 2->1" if ok else f"mapeamento incorreto: {list(probe)}")


DERIVADAS = ("idade_anos", "intervalo_sint_interna_dias", "flag_intervalo_invalido",
             "sin_semana", "cos_semana", "faixa_etaria")
_DERIVADAS_CANON = {d.upper() for d in DERIVADAS}


def add_derived(df: pd.DataFrame, cfg: dict, wanted=None) -> list[str]:
    """Cria IN-PLACE (nomes canônicos em maiúsculas) as features derivadas pedidas.

    Usa só o que existe na admissão (idade, DT_SIN_PRI, DT_INTERNA); nunca desfecho nem datas posteriores.
    - idade_anos: NU_IDADE_N convertida por TP_IDADE (dias/365, meses/12, anos); fora de [0, max_age_years] -> NaN
    - faixa_etaria: faixas de cfg['derivadas']['faixas_etarias'] (texto; NaN se idade inválida)
    - intervalo_sint_interna_dias: DT_INTERNA - DT_SIN_PRI em dias; NaN quando inválido
    - flag_intervalo_invalido: 1 se o intervalo é ausente, negativo ou > intervalo_max_dias; senão 0
    - sin_semana / cos_semana: semana ISO de DT_INTERNA em círculo de periodo_semanas
    """
    c, d = cfg["cols"], cfg["derivadas"]
    wanted = {canon(w) for w in (wanted if wanted is not None else DERIVADAS)} & _DERIVADAS_CANON
    criadas: list[str] = []
    if wanted & {"IDADE_ANOS", "FAIXA_ETARIA"}:
        age = age_years(df, cfg)
        age = age.where((age >= 0) & (age <= cfg["max_age_years"]))
        if "IDADE_ANOS" in wanted:
            df["IDADE_ANOS"] = age
            criadas.append("IDADE_ANOS")
        if "FAIXA_ETARIA" in wanted:
            fx = pd.cut(age, bins=d["faixas_etarias"]["bins"], labels=d["faixas_etarias"]["labels"], right=False)
            df["FAIXA_ETARIA"] = fx.astype(object).where(fx.notna(), np.nan)
            criadas.append("FAIXA_ETARIA")
    if wanted & {"INTERVALO_SINT_INTERNA_DIAS", "FLAG_INTERVALO_INVALIDO"}:
        gap = (parse_date(df[c["dt_interna"]]) - parse_date(df[c["dt_sin_pri"]])).dt.days.astype("float64")
        invalido = gap.isna() | (gap < 0) | (gap > d["intervalo_max_dias"])
        if "FLAG_INTERVALO_INVALIDO" in wanted:
            df["FLAG_INTERVALO_INVALIDO"] = invalido.astype("int8")
            criadas.append("FLAG_INTERVALO_INVALIDO")
        if "INTERVALO_SINT_INTERNA_DIAS" in wanted:
            df["INTERVALO_SINT_INTERNA_DIAS"] = gap.where(~invalido)
            criadas.append("INTERVALO_SINT_INTERNA_DIAS")
    if wanted & {"SIN_SEMANA", "COS_SEMANA"}:
        sem = parse_date(df[c["dt_interna"]]).dt.isocalendar().week.astype("float64")
        ang = 2 * np.pi * sem / d["periodo_semanas"]
        if "SIN_SEMANA" in wanted:
            df["SIN_SEMANA"] = np.sin(ang)
            criadas.append("SIN_SEMANA")
        if "COS_SEMANA" in wanted:
            df["COS_SEMANA"] = np.cos(ang)
            criadas.append("COS_SEMANA")
    return criadas


def _analytical_path(cfg: dict) -> Path:
    """Usa C.ANALYTICAL_DIR do projeto (como o C1/C2); senão, o caminho de configs/decisoes.yaml."""
    nome = Path(cfg["dataset_analitico"]["path"]).name
    try:
        from src.utils import config as C  # noqa: N812

        return Path(C.ANALYTICAL_DIR) / nome
    except Exception:  # noqa: BLE001
        return Path(cfg["dataset_analitico"]["path"])


def a1_export_dataset(df, cfg, rep: Report, supervised_config=None, path=None, versao="0.1",
                      excluir_proibidas=False, extra_cols=(), split=None, rotulo="") -> dict:
    """Grava a população analítica (coorte + alvo + tempo + features) para o C2.

    Colunas: id (NU_NOTIFIC), colunas de tempo (coluna_tempo do supervised.yaml e DT_INTERNA),
    alvo (EVOLUCAO bruta: apenas 1/2 após a coorte), features do supervised.yaml e ANO_INTERNACAO.
    Usa os NOMES ORIGINAIS das colunas da base (os do supervised.yaml), ordenado pelo tempo.
    Nenhuma coluna proibida além das features pedidas é enviada ao C.
    """
    path = Path(path) if path else _analytical_path(cfg)
    _t = f" [{rotulo}]" if rotulo else ""
    c = cfg["cols"]
    orig = df.attrs.get("orig_names", {})
    cohort = a1_cohort(df, cfg)
    y = load_supervised_yaml(supervised_config) if supervised_config and Path(supervised_config).exists() else {}
    if y:
        feats = supervised_features(y)
        target_col = canon((y.get("target") or {}).get("coluna", c["evolucao"]))
        time_col = canon(y.get("coluna_tempo", c["dt_interna"]))
    else:
        feats = [canon(x) for x in cfg["allowed_vars"] if canon(x) in df.columns]
        target_col, time_col = c["evolucao"], c["dt_interna"]
    grupos = [canon(g) for g in (((y.get("avaliacao") or {}).get("grupos")) or [])]
    pedir_derivadas = [f for f in dict.fromkeys(feats + grupos) if f in _DERIVADAS_CANON and f not in cohort.columns]
    derivadas_criadas = add_derived(cohort, cfg, pedir_derivadas) if pedir_derivadas else []
    forb = {canon(x) for x in cfg["forbidden_vars"]}
    hits = [f for f in feats if f in forb]
    if excluir_proibidas:
        feats = [f for f in feats if f not in forb]
    missing = [f for f in feats if f not in cohort.columns]
    grupos_cols = [g for g in grupos if g in cohort.columns]
    feats = [f for f in feats if f in cohort.columns]
    keep = [k for k in [c["nu_notific"], time_col, c["dt_interna"], target_col, *feats, *grupos_cols,
                        *map(canon, extra_cols)] if k in cohort.columns]
    keep = list(dict.fromkeys(keep))
    out = cohort[keep].copy()
    for t in {time_col, c["dt_interna"]}:
        if t in out.columns:
            out[t] = parse_date(out[t])
    out["ANO_INTERNACAO"] = cohort["_ano"].to_numpy()
    n_data_invalida = 0
    if time_col in out.columns:
        n_data_invalida = int(out[time_col].isna().sum())
        out = out.dropna(subset=[time_col]).sort_values(time_col, kind="stable")
    if split:  # coluna `split` (treino/validacao/holdout) sorteada, estratificada pelo alvo, reprodutível pela seed
        estr = out[target_col].astype(str).to_numpy() if split.get("estratificar_por_alvo", True) else None
        out["SPLIT"] = split_aleatorio(len(out), estr, split.get("seed", 42), split.get("fracoes"))
    pedidos = {}
    if y:
        f_ = y.get("features", {}) or {}
        for n in ((f_.get("final") or []) or (f_.get("numericas") or []) + (f_.get("categoricas") or [])):
            pedidos[canon(n)] = str(n)
        for g_ in ((y.get("avaliacao") or {}).get("grupos") or []):
            pedidos.setdefault(canon(g_), str(g_))
        pedidos[target_col] = str((y.get("target") or {}).get("coluna", target_col))
        pedidos[time_col] = str(y.get("coluna_tempo", time_col))
    nome_final = lambda col: pedidos.get(col, orig.get(col, col.lower()))  # noqa: E731
    aliases_aplicados = {nome_final(c_): orig.get(c_, c_.lower()) for c_ in out.columns
                         if c_ in pedidos and nome_final(c_).lower() != orig.get(c_, c_.lower()).lower()}
    out.columns = [nome_final(col) for col in out.columns]
    tgt_name = nome_final(target_col)
    assert set(pd.Series(out[tgt_name]).dropna().astype(float).unique()) <= {1.0, 2.0}, "alvo fora de {1,2}"

    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".csv":
        out.to_csv(path, index=False)
    else:
        out.to_parquet(path, index=False)
    meta = dict(versao=versao, criado_em=pd.Timestamp.now().isoformat(timespec="seconds"), arquivo=str(path),
                n_linhas=int(len(out)), colunas=list(out.columns), alvo=tgt_name,
                coluna_tempo=nome_final(time_col),
                anos={str(k): int(v_) for k, v_ in out["ano_internacao"].value_counts().sort_index().items()},
                desenvolvimento=cfg["dev_years"], holdout=cfg["holdout_years"],
                features_proibidas_no_dataset=[orig.get(h, h.lower()) for h in hits if not excluir_proibidas],
                features_ausentes_na_base=missing, base_origem_linhas=int(len(df)),
                aliases_aplicados_yaml_para_fisico=aliases_aplicados,
                descartadas_data_tempo_invalida=n_data_invalida,
                derivadas_criadas=[nome_final(x) for x in derivadas_criadas],
                grupos_avaliacao_incluidos=[nome_final(g) for g in grupos_cols])
    meta["sha256"] = _sha256(path)
    if split:
        meta["split"] = {"tipo": split.get("tipo", "aleatorio"), "seed": split.get("seed", 42),
                         "fracoes": split.get("fracoes"), "contagem": out["split"].value_counts().to_dict()}
    path.with_suffix(".meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    if derivadas_criadas:
        rep.add("A1", "Features derivadas" + _t, OK,
                f"criadas no dataset: {', '.join(nome_final(x) for x in derivadas_criadas)}")
    if n_data_invalida:
        rep.add("A1", "Data da coluna de tempo" + _t, WARN,
                f"{n_data_invalida:,} linhas com {nome_final(time_col)} inválida/ausente descartadas (o C2 faria o mesmo)")
    if aliases_aplicados:
        rep.add("A1", "Nomes do YAML x base" + _t, WARN,
                "colunas gravadas com o nome pedido no YAML, mas vindas de outro nome físico: "
                + ", ".join(f"{k}<-{v_}" for k, v_ in aliases_aplicados.items()) + " (confirmar equivalência)")
    hard = [h for h in hits if h != "HOSPITAL" and not excluir_proibidas]
    if hard:
        rep.add("A1", "Dataset analítico" + _t, FAIL, f"{len(out):,} linhas gravadas, MAS com features proibidas: {', '.join(hard)}")
    elif missing:
        rep.add("A1", "Dataset analítico" + _t, WARN, f"{len(out):,} linhas v{versao}; features ausentes na base: {', '.join(missing)}")
    else:
        rep.add("A1", "Dataset analítico" + _t, OK, f"{len(out):,} linhas, {out.shape[1]} colunas -> {path} (v{versao})")
    return meta


def validar_contrato_c2(path, supervised_config, rep: Report) -> bool:
    """Confere o ARQUIVO gravado contra o que o C2 consome (células 6–16 do C2_pipeline_supervisionado).

    O C2 faz: read_parquet -> TARGET e DATE_COLUMN presentes -> to_datetime(DATE_COLUMN) e dropna ->
    treino[FEATURES] -> criar_alvo_binario/filtrar_rotulos_validos -> check_leakage(X).
    """
    st, p = "A1-C2", Path(path)
    if not p.exists():
        rep.add(st, "Arquivo do dataset", FAIL, f"não encontrado: {p}")
        return False
    y = load_supervised_yaml(supervised_config)
    f = y.get("features", {}) or {}
    target = (y.get("target") or {}).get("coluna")
    data_col = y.get("coluna_tempo")
    feats = list(f.get("final") or ((f.get("numericas") or []) + (f.get("categoricas") or [])))
    positivos = [float(x) for x in ((y.get("target") or {}).get("positivos") or [])]
    if p.suffix == ".csv":
        names = list(pd.read_csv(p, nrows=0).columns)
    else:
        import pyarrow.parquet as pq

        names = pq.ParquetFile(p).schema_arrow.names
    wanted = [c for c in dict.fromkeys([target, data_col, *feats]) if c in names]
    d = pd.read_csv(p, usecols=wanted) if p.suffix == ".csv" else pd.read_parquet(p, columns=wanted)
    ok = True
    faltam = [c for c in (target, data_col, *feats) if c not in names]
    if faltam:
        ok = False
        rep.add(st, "Colunas exigidas pelo C2", FAIL, f"ausentes no dataset: {', '.join(map(str, faltam))}")
    else:
        rep.add(st, "Colunas exigidas pelo C2", OK, f"alvo '{target}', tempo '{data_col}' e {len(feats)} features presentes")
    if data_col in d.columns:
        dt = pd.to_datetime(d[data_col], errors="coerce")
        n_bad = int(dt.isna().sum())
        if n_bad:
            rep.add(st, "Coluna de tempo", WARN, f"{n_bad:,} datas inválidas (o C2 descarta essas linhas)")
        elif not dt.is_monotonic_increasing:
            rep.add(st, "Coluna de tempo", WARN, "dataset não está ordenado por tempo (o TemporalSplit pode reordenar)")
        else:
            rep.add(st, "Coluna de tempo", OK, f"datetime válido, ordenado: {dt.min().date()} -> {dt.max().date()}")
    if target in d.columns:
        vals = set(pd.Series(d[target]).dropna().astype(float).unique())
        if positivos and not (set(positivos) & vals):
            ok = False
            rep.add(st, "Alvo", FAIL, f"nenhum valor positivo {positivos} no dataset (valores: {sorted(vals)})")
        elif vals - {1.0, 2.0}:
            rep.add(st, "Alvo", WARN, f"valores fora de {{1,2}}: {sorted(vals - {1.0, 2.0})} (o C2 os descarta)")
        else:
            rep.add(st, "Alvo", OK, f"apenas cura/óbito; positivos {positivos} presentes")
    prib = {str(x).lower() for x in (f.get("proibidas") or [])}
    vazam = [c for c in feats if str(c).lower() in prib]
    if vazam:
        ok = False
        rep.add(st, "check_leakage (C2)", FAIL, f"features em `proibidas`: {', '.join(vazam)}")
    else:
        rep.add(st, "check_leakage (C2)", OK, "nenhuma feature está em `proibidas`")
    rep.add(st, "Tamanho", OK if len(d) else FAIL, f"{len(d):,} linhas")
    return ok and len(d) > 0


# =============================================================================
# Experimentos de split: aleatório 70-15-15 e cenários de período (A3b)
# =============================================================================
def _sha256(path) -> str:
    import hashlib

    h = hashlib.sha256()
    with open(path, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def verificar_dataset_congelado(path, rep: Report) -> bool:
    """Compara o SHA-256 do arquivo com o gravado no .meta.json (população analítica congelada)."""
    p = Path(path)
    meta_p = p.with_suffix(".meta.json")
    if not p.exists() or not meta_p.exists():
        rep.add("A4", "Dataset congelado", FAIL, f"arquivo ou metadados ausentes: {p.name}")
        return False
    meta = json.loads(meta_p.read_text(encoding="utf-8"))
    ok = meta.get("sha256") == _sha256(p)
    rep.add("A4", "Dataset congelado", OK if ok else FAIL,
            f"{p.name} v{meta.get('versao')} " + ("inalterado desde a exportação" if ok else "FOI ALTERADO após a exportação"))
    return ok


def cfg_para_anos(cfg: dict, anos) -> dict:
    """Cópia de cfg com o período analítico = `anos` (sem holdout temporal): usada nos cenários."""
    c2 = json.loads(json.dumps(cfg))
    c2["dev_years"] = [int(a) for a in anos]
    c2["holdout_years"] = []
    return c2


def split_aleatorio(n: int, estratos=None, seed: int = 42, fracoes: dict | None = None) -> np.ndarray:
    """Rótulos 'treino'/'validacao'/'holdout' sorteados (opcionalmente estratificados), reprodutíveis pela seed."""
    fr = fracoes or {"treino": 0.70, "validacao": 0.15, "holdout": 0.15}
    if abs(sum(fr.values()) - 1) > 1e-9:
        raise ValueError(f"frações devem somar 1: {fr}")
    rng = np.random.default_rng(seed)
    rot = np.empty(n, dtype=object)
    if estratos is None:
        grupos = [np.arange(n)]
    else:
        est = np.asarray(estratos).astype(str)
        grupos = [np.flatnonzero(est == k) for k in sorted(set(est))]
    for idx in grupos:
        idx = rng.permutation(idx)
        m = len(idx)
        n_tr, n_va = int(round(m * fr["treino"])), int(round(m * fr["validacao"]))
        rot[idx[:n_tr]] = "treino"
        rot[idx[n_tr:n_tr + n_va]] = "validacao"
        rot[idx[n_tr + n_va:]] = "holdout"
    return rot


def split_por_ordem(valores_tempo, fracoes: dict | None = None) -> np.ndarray:
    """Divisão temporal por posição (como o TemporalSplit por fração do C2): passado -> treino, futuro -> holdout."""
    fr = fracoes or {"treino": 0.70, "validacao": 0.15, "holdout": 0.15}
    v_ = np.asarray(valores_tempo)
    ordem = np.argsort(v_, kind="stable")
    n = len(v_)
    n_tr, n_va = int(round(n * fr["treino"])), int(round(n * fr["validacao"]))
    rot = np.empty(n, dtype=object)
    rot[ordem[:n_tr]] = "treino"
    rot[ordem[n_tr:n_tr + n_va]] = "validacao"
    rot[ordem[n_tr + n_va:]] = "holdout"
    return rot


def _ler(path, cols):
    p = Path(path)
    if p.suffix == ".csv":
        return pd.read_csv(p, usecols=[c for c in cols if c in pd.read_csv(p, nrows=0).columns])
    import pyarrow.parquet as pq

    nomes = pq.ParquetFile(p).schema_arrow.names
    return pd.read_parquet(p, columns=[c for c in cols if c in nomes])


def _relatorio_split(path, meta: dict, cfg: dict, rep: Report, nome: str) -> pd.DataFrame:
    st, tag = "A3b", f" [{nome}]"
    fr = cfg["experimentos_split"]["fracoes"]
    d = _ler(path, ["split", meta["alvo"], "ano_internacao", "nu_notific"])
    d["_y"] = (pd.to_numeric(d[meta["alvo"]], errors="coerce") == float(cfg["target_positive"])).astype(int)
    t = d.groupby("split").agg(n=("_y", "size"), n_obitos=("_y", "sum"))
    t["pct_linhas"] = (100 * t["n"] / t["n"].sum()).round(2)
    t["prevalencia_obito_pct"] = (100 * t["n_obitos"] / t["n"]).round(2)
    t = t.reindex(["treino", "validacao", "holdout"]).reset_index()
    rep.save(f"a3_split_aleatorio_{nome}", t)
    por_ano = pd.crosstab(d["ano_internacao"], d["split"]).reindex(columns=["treino", "validacao", "holdout"], fill_value=0)
    rep.save(f"a3_split_aleatorio_{nome}_por_ano", por_ano.reset_index())

    dev = max(abs(float(t.loc[t["split"] == k, "pct_linhas"].iloc[0]) - 100 * fr[k]) for k in fr)
    rep.add(st, "Proporções 70/15/15" + tag, OK if dev <= 0.5 else WARN,
            f"desvio máximo {dev:.2f} p.p. | " + ", ".join(f"{r.split}={r.n:,}" for r in t.itertuples()))
    amp = float(t["prevalencia_obito_pct"].max() - t["prevalencia_obito_pct"].min())
    rep.add(st, "Estratificação do alvo" + tag, OK if amp <= 0.5 else WARN,
            f"prevalência de óbito por split: " + ", ".join(f"{r.split}={r.prevalencia_obito_pct}%" for r in t.itertuples())
            + f" (amplitude {amp:.2f} p.p.)")
    faltam = [(int(a), s) for a in por_ano.index for s in por_ano.columns if por_ano.loc[a, s] == 0]
    rep.add(st, "Anos em cada split" + tag, OK if not faltam else WARN,
            "todos os anos aparecem nos 3 splits (split aleatório mistura os períodos)" if not faltam
            else f"anos ausentes em algum split: {faltam[:6]}")
    if "nu_notific" in d.columns:
        g = d.dropna(subset=["nu_notific"]).groupby("nu_notific")["split"].nunique()
        n_dup = int((g > 1).sum())
        rep.add(st, "NU_NOTIFIC entre splits" + tag, OK if n_dup == 0 else WARN,
                "nenhum NU_NOTIFIC repetido em splits diferentes" if n_dup == 0
                else f"{n_dup:,} NU_NOTIFIC aparecem em mais de um split (pode ser vazamento entre treino e validação)")
    return t


def a3_split_aleatorio_cenario(df, cfg, rep: Report, nome: str, anos, supervised_config=None,
                               versao: str = "0.1", excluir_proibidas: bool = False) -> dict:
    """Coorte do cenário (anos informados) + dataset com coluna `split` aleatória 70/15/15 + relatório."""
    cfg_s = cfg_para_anos(cfg, anos)
    a1_waterfall(df, cfg_s, rep, sufixo=f"_{nome}")
    base = _analytical_path(cfg)
    caminho = base.with_name(f"dataset_supervisionado_{nome}{base.suffix}")
    e = cfg["experimentos_split"]
    meta = a1_export_dataset(df, cfg_s, rep, supervised_config, path=caminho, versao=versao,
                             excluir_proibidas=excluir_proibidas, rotulo=nome,
                             split={"tipo": "aleatorio", "seed": e["seed"], "fracoes": e["fracoes"],
                                    "estratificar_por_alvo": e["estratificar_por_alvo"]})
    meta["anos_cenario"] = [int(a) for a in anos]
    _relatorio_split(caminho, meta, cfg, rep, nome)
    return meta


def a3_benchmark_split(path, supervised_config, cfg: dict, rep: Report, nome: str,
                       max_rows: int = 200_000, seed: int = 42) -> pd.DataFrame:
    """Regressão logística treino -> VALIDAÇÃO em split aleatório e em split temporal por ordem (o holdout NÃO é aberto).

    Mostra o quanto o split aleatório é otimista frente ao temporal (autocorrelação no tempo).
    """
    from sklearn.compose import ColumnTransformer
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler

    y = load_supervised_yaml(supervised_config)
    f = y.get("features", {}) or {}
    numericas = list(f.get("numericas") or [])
    categoricas = list(f.get("categoricas") or [])
    if f.get("final"):
        numericas = [x for x in f["final"] if x in numericas]
        categoricas = [x for x in f["final"] if x not in numericas]
    alvo, tempo = y["target"]["coluna"], y["coluna_tempo"]
    pos = float(y["target"]["positivos"][0])
    d = _ler(path, [alvo, tempo, "split", *numericas, *categoricas])
    numericas = [c for c in numericas if c in d.columns]
    categoricas = [c for c in categoricas if c in d.columns]
    d[tempo] = pd.to_datetime(d[tempo], errors="coerce")
    d = d.dropna(subset=[tempo]).reset_index(drop=True)
    d["part_aleatoria"] = d["split"].to_numpy()
    d["part_temporal"] = split_por_ordem(d[tempo].to_numpy(), cfg["experimentos_split"]["fracoes"])
    if len(d) > max_rows:
        d = d.sample(max_rows, random_state=seed).reset_index(drop=True)
    yb = (pd.to_numeric(d[alvo], errors="coerce") == pos).astype(int).to_numpy()
    X = d[numericas + categoricas].copy()
    for c in numericas:
        X[c] = pd.to_numeric(X[c], errors="coerce")
    for c in categoricas:
        X[c] = X[c].astype("string").fillna("__NA__").astype(object)

    linhas = []
    for particao, col in (("aleatoria", "part_aleatoria"), ("temporal_por_ordem", "part_temporal")):
        tr = (d[col] == "treino").to_numpy()
        va = (d[col] == "validacao").to_numpy()
        if len(np.unique(yb[tr])) < 2 or len(np.unique(yb[va])) < 2:
            continue
        prep = ColumnTransformer([
            ("num", Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler())]), numericas),
            ("cat", OneHotEncoder(handle_unknown="ignore", min_frequency=30), categoricas),
        ])
        pipe = Pipeline([("prep", prep), ("clf", LogisticRegression(max_iter=300, class_weight="balanced"))])
        pipe.fit(X[tr], yb[tr])
        p = pipe.predict_proba(X[va])[:, 1]
        prior = float(yb[tr].mean())
        base = dict(cenario=nome, particao=particao, n_treino=int(tr.sum()), n_validacao=int(va.sum()),
                    prevalencia_validacao=round(float(yb[va].mean()), 4))
        linhas.append(dict(base, modelo="baseline_prior", roc_auc=0.5, pr_auc=round(float(yb[va].mean()), 4),
                           brier=round(float(np.mean((prior - yb[va]) ** 2)), 4)))
        linhas.append(dict(base, modelo="logistica", roc_auc=round(roc_auc_score(yb[va], p), 4),
                           pr_auc=round(average_precision_score(yb[va], p), 4),
                           brier=round(brier_score_loss(yb[va], p), 4)))
    res = pd.DataFrame(linhas)
    rep.save(f"a3_benchmark_split_{nome}", res)
    tag = f" [{nome}]"
    lg = res[res["modelo"] == "logistica"].set_index("particao") if len(res) else res
    if len(res) and {"aleatoria", "temporal_por_ordem"} <= set(lg.index):
        delta = float(lg.loc["aleatoria", "pr_auc"] - lg.loc["temporal_por_ordem", "pr_auc"])
        rep.add("A3b", "Split aleatório x temporal" + tag, WARN if delta > 0.02 else OK,
                f"PR-AUC (validação): aleatório {lg.loc['aleatoria', 'pr_auc']:.3f} vs temporal {lg.loc['temporal_por_ordem', 'pr_auc']:.3f} "
                f"(Δ {delta:+.3f})" + (" — o aleatório está otimista; decidir pelo temporal" if delta > 0.02 else ""))
    else:
        rep.add("A3b", "Split aleatório x temporal" + tag, WARN, "benchmark não executado (alvo com uma só classe em algum split)")
    return res


_COR_SPLIT = {"treino": "#2F6DB5", "validacao": "#E8912D", "holdout": "#6BA368"}
_ORDEM_SPLIT = ["treino", "validacao", "holdout"]


def _rotulos_barras(ax, barras, textos, dy=0.0):
    for b, t in zip(barras, textos):
        ax.annotate(t, (b.get_x() + b.get_width() / 2, b.get_height() + dy), ha="center", va="bottom", fontsize=9)


def grafico_split_cenario(rep: Report, cfg: dict, nome: str, anos=None, fig_dir="outputs/figures/pessoa_a",
                          mostrar: bool = False):
    """3 painéis do split aleatório de um cenário (a partir das tabelas já gravadas em rep.out):
    (a) % de linhas por split x meta 70/15/15; (b) prevalência de óbito por split; (c) composição dos splits dentro de cada ano.
    """
    import matplotlib.pyplot as plt

    t = pd.read_csv(Path(rep.out) / f"a3_split_aleatorio_{nome}.csv").set_index("split").reindex(_ORDEM_SPLIT)
    pa = pd.read_csv(Path(rep.out) / f"a3_split_aleatorio_{nome}_por_ano.csv").set_index("ano_internacao")[_ORDEM_SPLIT]
    fr = cfg["experimentos_split"]["fracoes"]
    cores = [_COR_SPLIT[s] for s in _ORDEM_SPLIT]
    fig, axs = plt.subplots(1, 3, figsize=(17, 4.8), gridspec_kw={"width_ratios": [1, 1, 1.5]})

    ax = axs[0]  # (a) proporção de linhas
    barras = ax.bar(_ORDEM_SPLIT, t["pct_linhas"], color=cores)
    for i, s in enumerate(_ORDEM_SPLIT):
        ax.hlines(100 * fr[s], i - 0.42, i + 0.42, colors="black", linestyles="--", linewidth=1.4,
                  label="meta 70/15/15" if i == 0 else None)
    _rotulos_barras(ax, barras, [f"{p:.1f}%\nn={int(n):,}" for p, n in zip(t["pct_linhas"], t["n"])], dy=1)
    ax.set_ylim(0, 100 * max(fr.values()) * 1.25)
    ax.set_ylabel("% das linhas da coorte")
    ax.set_title("(a) Proporção de linhas por split")
    ax.legend(loc="upper right", fontsize=9)

    ax = axs[1]  # (b) prevalência do alvo
    prev = t["prevalencia_obito_pct"]
    geral = 100 * t["n_obitos"].sum() / t["n"].sum()
    barras = ax.bar(_ORDEM_SPLIT, prev, color=cores)
    ax.axhline(geral, color="black", linestyle="--", linewidth=1.4, label=f"geral {geral:.2f}%")
    _rotulos_barras(ax, barras, [f"{p:.2f}%" for p in prev], dy=0.3)
    ax.set_ylim(0, max(prev.max(), geral) * 1.3)
    ax.set_ylabel("% de óbitos (alvo = 1)")
    ax.set_title(f"(b) Prevalência de óbito por split (amplitude {prev.max() - prev.min():.2f} p.p.)")
    ax.legend(loc="upper right", fontsize=9)

    ax = axs[2]  # (c) composição por ano
    comp = pa.div(pa.sum(axis=1), axis=0) * 100
    base = np.zeros(len(comp))
    for s in _ORDEM_SPLIT:
        ax.bar(comp.index.astype(str), comp[s], bottom=base, color=_COR_SPLIT[s], label=s)
        for x, (v_, b_) in enumerate(zip(comp[s], base)):
            if v_ >= 6:
                ax.text(x, b_ + v_ / 2, f"{v_:.0f}%", ha="center", va="center", fontsize=8, color="white")
        base = base + comp[s].to_numpy()
    ax.axhline(70, color="black", linestyle=":", linewidth=1)
    ax.axhline(85, color="black", linestyle=":", linewidth=1)
    ax.set_ylim(0, 100)
    ax.set_xticks(range(len(comp)), [f"{a}\nn={int(n):,}" for a, n in zip(comp.index, pa.sum(axis=1))], fontsize=8)
    ax.set_ylabel("% do ano em cada split")
    ax.set_title("(c) Composição dos splits dentro de cada ano")
    ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.17), fontsize=9)

    anos_txt = f" — anos {', '.join(map(str, anos))}" if anos else ""
    fig.suptitle(f"Split aleatório estratificado 70/15/15 — {nome}{anos_txt}", fontsize=13, y=1.02)
    fig.tight_layout()
    destino = Path(fig_dir)
    destino.mkdir(parents=True, exist_ok=True)
    caminho = destino / f"split_{nome}.png"
    fig.savefig(caminho, dpi=140, bbox_inches="tight")
    if mostrar:
        plt.show()
    else:
        plt.close(fig)
    return caminho


def grafico_comparacao_cenarios(rep: Report, cfg: dict, nomes, fig_dir="outputs/figures/pessoa_a", mostrar: bool = False):
    """Compara os cenários: N por ano empilhado por split (um painel por cenário, mesmo eixo) + prevalência por split."""
    import matplotlib.pyplot as plt

    nomes = list(nomes)
    por_ano = {n: pd.read_csv(Path(rep.out) / f"a3_split_aleatorio_{n}_por_ano.csv").set_index("ano_internacao")[_ORDEM_SPLIT]
               for n in nomes}
    resumo = {n: pd.read_csv(Path(rep.out) / f"a3_split_aleatorio_{n}.csv").set_index("split").reindex(_ORDEM_SPLIT) for n in nomes}
    anos = sorted(set().union(*[set(p.index) for p in por_ano.values()]))
    topo = max(p.sum(axis=1).max() for p in por_ano.values()) * 1.12
    fig, axs = plt.subplots(1, len(nomes) + 1, figsize=(6 * len(nomes) + 5.5, 4.8),
                            gridspec_kw={"width_ratios": [1.3] * len(nomes) + [1]})
    for ax, n in zip(axs, nomes):
        p = por_ano[n].reindex(anos, fill_value=0)
        base = np.zeros(len(p))
        for s in _ORDEM_SPLIT:
            ax.bar(p.index.astype(str), p[s], bottom=base, color=_COR_SPLIT[s], label=s)
            base = base + p[s].to_numpy()
        for x, tot in enumerate(base):
            if tot == 0:
                ax.axvspan(x - 0.5, x + 0.5, color="#DDDDDD", alpha=0.6)
                ax.text(x, topo * 0.5, "fora do\ncenário", ha="center", va="center", fontsize=9, color="#555555")
            else:
                ax.text(x, tot + topo * 0.01, f"{int(tot):,}", ha="center", va="bottom", fontsize=8)
        ax.set_ylim(0, topo)
        ax.set_ylabel("registros na coorte")
        ax.set_title(f"{n}  (N={int(base.sum()):,})")
    axs[0].legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.1), fontsize=9)

    ax = axs[-1]
    larg = 0.8 / len(nomes)
    cores_cen = ["#444444", "#B5B5B5", "#8A6FBF", "#C96F6F"]
    for i, n in enumerate(nomes):
        x = np.arange(3) + (i - (len(nomes) - 1) / 2) * larg
        barras = ax.bar(x, resumo[n]["prevalencia_obito_pct"], larg, label=n, color=cores_cen[i % len(cores_cen)])
        _rotulos_barras(ax, barras, [f"{p:.1f}%" for p in resumo[n]["prevalencia_obito_pct"]], dy=0.2)
    ax.set_xticks(range(3), _ORDEM_SPLIT)
    ymax = max(r["prevalencia_obito_pct"].max() for r in resumo.values())
    ax.set_ylim(0, ymax * 1.3)
    ax.set_ylabel("% de óbitos")
    ax.set_title("Prevalência de óbito por split")
    ax.legend(fontsize=8, loc="upper right")
    fig.suptitle("Comparação dos cenários — split aleatório 70/15/15", fontsize=13, y=1.02)
    fig.tight_layout()
    destino = Path(fig_dir)
    destino.mkdir(parents=True, exist_ok=True)
    caminho = destino / "split_comparacao_cenarios.png"
    fig.savefig(caminho, dpi=140, bbox_inches="tight")
    if mostrar:
        plt.show()
    else:
        plt.close(fig)
    return caminho


def comparar_cenarios(metas: dict, benchs: dict, rep: Report) -> pd.DataFrame:
    """Tabela única: N, prevalência e desempenho (validação) por cenário."""
    linhas = []
    for nome, m in metas.items():
        d = _ler(m["arquivo"], [m["alvo"]])
        y = (pd.to_numeric(d[m["alvo"]], errors="coerce") == 2).astype(int)
        r = dict(cenario=nome, anos=",".join(map(str, m.get("anos_cenario", []))), n_linhas=len(d),
                 n_obitos=int(y.sum()), prevalencia_obito_pct=round(100 * float(y.mean()), 2))
        b = benchs.get(nome)
        if b is not None and len(b):
            for part in ("aleatoria", "temporal_por_ordem"):
                x = b[(b["modelo"] == "logistica") & (b["particao"] == part)]
                if len(x):
                    r[f"pr_auc_{part}"], r[f"roc_auc_{part}"] = float(x["pr_auc"].iloc[0]), float(x["roc_auc"].iloc[0])
        linhas.append(r)
    t = pd.DataFrame(linhas)
    rep.save("comparacao_cenarios", t)
    return t


# =============================================================================
# A2 — Qualidade, datas e elegibilidade
# =============================================================================
def a2_missing(df, cfg, rep: Report) -> None:
    ano = year_labels(df, cfg)
    coded = set(cfg["expected_codes"])
    rows = []
    for col in df.columns:
        s = df[col]
        isna = s.isna()
        if s.dtype == object or pd.api.types.is_string_dtype(s):
            isna = isna | (s.astype("string").str.strip() == "").fillna(False)
        g = isna.groupby(ano).agg(["mean", "size"])
        ign = None
        if col in coded:
            ign = (code_str(s) == "9").fillna(False).groupby(ano).mean()
        for y, r in g.iterrows():
            rows.append(dict(coluna=col, ano=y, n=int(r["size"]), pct_vazio=round(100 * r["mean"], 2),
                             pct_ignorado=None if ign is None else round(100 * ign.loc[y], 2)))
    long = pd.DataFrame(rows)
    rep.save("a2_vazios_ignorados_por_ano", long)
    piv = long[long["ano"] != "sem_data"].pivot(index="coluna", columns="ano", values="pct_vazio")
    inexistente = piv[(piv >= 99.9).any(axis=1) & (piv < 99.9).any(axis=1)]
    rep.save("a2_campos_inexistentes_por_ano", inexistente.reset_index())
    if len(inexistente):
        rep.add("A2", "Campo inexistente por ano", WARN,
                f"{len(inexistente)} campos 100% vazios em algum ano (ex.: {', '.join(inexistente.index[:5])})")
    else:
        rep.add("A2", "Campo inexistente por ano", OK, "nenhuma ruptura total de preenchimento")


def a2_dates(df, cfg, rep: Report) -> None:
    c = cfg["cols"]
    today = pd.Timestamp.today().normalize()
    rows = []
    for a, b, desc, action in cfg["date_rules"]:
        if c[a] not in df.columns or c[b] not in df.columns:
            continue
        da, db = parse_date(df[c[a]]), parse_date(df[c[b]])
        both = da.notna() & db.notna()
        bad = (da > db).fillna(False)
        rows.append(dict(regra=f"{c[a]} <= {c[b]}", descricao=desc, n_comparaveis=int(both.sum()),
                         n_violacoes=int(bad.sum()),
                         pct=round(100 * bad.sum() / max(both.sum(), 1), 3), acao_sugerida=action))
    for key in ("dt_nasc", "dt_sin_pri", "dt_notific", "dt_interna", "dt_evoluca", "dt_encerra"):
        if c[key] in df.columns:
            d = parse_date(df[c[key]])
            raw_filled = df[c[key]].notna()
            unparsable = int((raw_filled & d.isna()).sum())
            future = int((d > today).sum())
            rows.append(dict(regra=f"{c[key]} válida", descricao="Data futura, não interpretável ou fora de 1900–2100",
                             n_comparaveis=int(raw_filled.sum()), n_violacoes=unparsable + future,
                             pct=round(100 * (unparsable + future) / max(raw_filled.sum(), 1), 3),
                             acao_sugerida="transformar em ausente"))
    if {c["dt_sin_pri"], c["dt_interna"]} <= set(df.columns):
        gap = (parse_date(df[c["dt_interna"]]) - parse_date(df[c["dt_sin_pri"]])).dt.days
        big = int((gap > cfg["max_symptom_to_admission_days"]).sum())
        rows.append(dict(regra="sintomas->internação", descricao=f"> {cfg['max_symptom_to_admission_days']} dias",
                         n_comparaveis=int(gap.notna().sum()), n_violacoes=big,
                         pct=round(100 * big / max(gap.notna().sum(), 1), 3), acao_sugerida="manter com flag"))
    if {c["nu_idade"], c["tp_idade"]} <= set(df.columns):
        age = age_years(df, cfg)
        bad = int(((age < 0) | (age > cfg["max_age_years"])).sum())
        rows.append(dict(regra="idade em anos", descricao=f"< 0 ou > {cfg['max_age_years']}",
                         n_comparaveis=int(age.notna().sum()), n_violacoes=bad,
                         pct=round(100 * bad / max(age.notna().sum(), 1), 3), acao_sugerida="transformar em ausente"))
    res = pd.DataFrame(rows)
    rep.save("a2_coerencia_datas", res)
    crit = res[(res["n_violacoes"] > 0) & ((res["pct"] > 1.0) | (res["acao_sugerida"] == "excluir"))]
    if len(crit):
        rep.add("A2", "Coerência de datas", WARN,
                f"{len(crit)} regra(s) com violações relevantes: "
                + "; ".join(f"{r.regra} ({r.n_violacoes})" for r in crit.itertuples()))
    else:
        rep.add("A2", "Coerência de datas", OK, "violações ≤ 1% e nenhuma regra de exclusão violada")


def a2_duplicates(df, cfg, rep: Report) -> None:
    c = cfg["cols"]
    exact = int(pd.util.hash_pandas_object(df, index=False).duplicated().sum())  # hash: evita cópia da base
    rows = [dict(tipo="linhas exatamente duplicadas", n_linhas=exact, n_grupos=exact)]
    nn = c["nu_notific"]
    if nn in df.columns:
        d = df[df[nn].notna()].duplicated(subset=[nn], keep=False)
        grp = df.loc[d.index[d], nn].nunique()
        rows.append(dict(tipo=f"{nn} repetido (não implica mesma pessoa)", n_linhas=int(d.sum()), n_grupos=int(grp)))
        key = [x for x in (nn, c["dt_notific"], c["dt_nasc"]) if x in df.columns]
        if len(key) > 1:
            d2 = df.duplicated(subset=key, keep=False)
            rows.append(dict(tipo=f"mesma chave {key}", n_linhas=int(d2.sum()), n_grupos=int(df[d2][key].drop_duplicates().shape[0])))
    res = pd.DataFrame(rows)
    rep.save("a2_duplicidades", res)
    rep.add("A2", "Duplicidades", WARN if exact else OK,
            f"{exact:,} linhas exatas duplicadas; demais tipos em a2_duplicidades.csv")


def a2_maturity(df, cfg, rep: Report) -> None:
    c = cfg["cols"]
    dt = parse_date(df[c["dt_interna"]])
    hosp = (code_str(df[c["hospital"]]) == "1").fillna(False).to_numpy(bool)
    m = hosp & dt.notna().to_numpy(bool)
    sub = df.loc[m]
    mes = dt[m].dt.to_period("M").astype(str)
    closed = code_str(sub[c["evolucao"]]).isin(cfg["closed_codes"])
    enc = parse_date(sub[c["dt_encerra"]]) if c["dt_encerra"] in sub.columns else pd.Series(pd.NaT, index=sub.index)
    days = (enc - dt[m]).dt.days
    res = pd.DataFrame({"mes": mes, "fechado": closed, "tem_encerra": enc.notna(), "dias": days})
    out = res.groupby("mes").agg(n=("fechado", "size"), pct_evolucao_fechada=("fechado", lambda x: round(100 * x.mean(), 2)),
                                 pct_com_dt_encerra=("tem_encerra", lambda x: round(100 * x.mean(), 2)),
                                 mediana_dias_ate_encerra=("dias", "median")).reset_index()
    rep.save("a2_maturidade_evolucao_por_mes", out)
    out["ano"] = out["mes"].str[:4].astype(int)
    imaturo = out[out["ano"].isin(cfg["holdout_years"]) & (out["pct_evolucao_fechada"] < cfg["maturity_min_closed_pct"])]
    if len(imaturo):
        rep.add("A2", "Maturidade de EVOLUCAO (holdout)", WARN,
                f"{len(imaturo)} mês(es) abaixo de {cfg['maturity_min_closed_pct']}% fechados: "
                f"{', '.join(imaturo['mes'].head(6))}")
    else:
        rep.add("A2", "Maturidade de EVOLUCAO (holdout)", OK, "todos os meses do holdout com evolução madura")


def classify_variable(col: str, pct_vazio: float, cfg: dict) -> tuple[str, str, str]:
    if col in cfg["forbidden_vars"]:
        return "excluir", "Pós-admissão, desfecho ou critério de inclusão (risco de vazamento)", "Não"
    if col in cfg["conditional_vars"]:
        return "incluir com condição", "Depende de quando foi registrada/completa na admissão", "Verificar"
    if col in cfg["allowed_vars"]:
        if pct_vazio > 95:
            return "auditoria", "Permitida, mas quase toda vazia", "Verificar"
        return "incluir", "Disponível na admissão (proposta inicial)", "Sim"
    return "auditoria", "Não classificada: consultar dicionário", "Verificar"


def a2_eligibility(df, cfg, rep: Report) -> None:
    sample = df.sample(min(len(df), 100_000), random_state=0) if len(df) > 100_000 else df
    rows = []
    for col in df.columns:
        s = df[col]
        pv = float(100 * (s.isna() | (s.astype("string").str.strip() == "").fillna(False)).mean()) \
            if s.dtype == object or pd.api.types.is_string_dtype(s) else float(100 * s.isna().mean())
        classe, why, na_adm = classify_variable(col, pv, cfg)
        rows.append(dict(coluna=col, classe=classe, justificativa=why, existe_na_admissao_sugerido=na_adm,
                         pct_vazio=round(pv, 2), n_distintos_amostra=int(sample[col].nunique(dropna=True)),
                         quando_observada="", quando_chegou_na_base="", decisao_final="", responsavel="", data=""))
    carregadas = set(df.columns)
    for c_ in df.attrs.get("schema_cols", []):
        if canon(c_) not in carregadas:
            rows.append(dict(coluna=str(c_).upper(), classe="auditoria",
                             justificativa="Existe no Parquet, mas não foi carregada (fora das listas classificadas)",
                             existe_na_admissao_sugerido="Verificar", pct_vazio=None, n_distintos_amostra=None,
                             quando_observada="", quando_chegou_na_base="", decisao_final="", responsavel="", data=""))
    mat = pd.DataFrame(rows).sort_values(["classe", "coluna"])
    rep.save("a2_matriz_elegibilidade", mat)
    cont = mat["classe"].value_counts().to_dict()
    rep.add("A2", "Matriz de elegibilidade", WARN if cont.get("auditoria") else OK,
            f"{cont} — preencher colunas em branco e fechar 'auditoria'")


# =============================================================================
# A3 — Desenho experimental e pilotos
# =============================================================================
def load_feature_list(path: str | Path) -> list[str]:
    """Lê lista de features de .txt (1 por linha), .json ou .yaml/.yml."""
    p = Path(path)
    txt = p.read_text(encoding="utf-8")
    if p.suffix in (".yaml", ".yml"):
        import yaml

        data = yaml.safe_load(txt)
    elif p.suffix == ".json":
        data = json.loads(txt)
    else:
        return [canon(ln.split("#")[0]) for ln in txt.splitlines() if ln.split("#")[0].strip()]

    def find(obj):
        if isinstance(obj, list) and all(isinstance(x, str) for x in obj):
            return obj
        if isinstance(obj, dict) and ("numericas" in obj or "categoricas" in obj):
            return supervised_features({"features": obj})
        if isinstance(obj, dict):
            for k in ("features", "feature_cols", "variaveis", "variáveis", "colunas", "columns"):
                if k in obj:
                    r = find(obj[k])
                    if r:
                        return r
            for v in obj.values():
                r = find(v)
                if r:
                    return r
        return None

    res = find(data)
    if not res:
        raise ValueError(f"Nenhuma lista de features encontrada em {p}")
    return [canon(x) for x in res]


def load_supervised_yaml(path: str | Path) -> dict:
    import yaml

    return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}


def supervised_features(y: dict) -> list[str]:
    """Features efetivas do configs/supervised.yaml: `final` se preenchida, senão numéricas + categóricas."""
    f = y.get("features", {}) or {}
    lst = f.get("final") or ((f.get("numericas") or []) + (f.get("categoricas") or []))
    return [canon(x) for x in lst]


def a3_config_audit(y: dict, cfg: dict, rep: Report, schema_cols=None) -> None:
    """Confere o supervised.yaml contra as decisões do plano (A1–A3)."""
    st = "A3-cfg"
    tg = y.get("target", {}) or {}
    pos = [float(x) for x in (tg.get("positivos") or [])]
    if pos != [float(cfg["target_positive"])]:
        rep.add(st, "Alvo: positivos", WARN, f"positivos={pos}; plano prevê óbito SRAG = [{cfg['target_positive']}]")
    else:
        rep.add(st, "Alvo: positivos", OK, "óbito SRAG (evolucao=2) como positivo")
    if not any(k for k in tg if "outras" in k or "ausente" in k or "nulo" in k):
        rep.add(st, "Alvo: evolucao=3 e ausente", WARN,
                "o YAML só tem `descartar_ignorado` (evolucao==9). O C2 descarta 3/9/nulos em "
                "`filtrar_rotulos_validos`; confirmar em src/models/pipeline.py que `criar_alvo_binario` "
                "trata 3 e ausente como inválidos (nunca como cura)")
    ct = canon(y.get("coluna_tempo", ""))
    if ct != "DT_INTERNA":
        rep.add(st, "Coluna temporal", WARN,
                f"split usa '{y.get('coluna_tempo')}', mas o ponto de previsão do plano é DT_INTERNA")
    else:
        rep.add(st, "Coluna temporal", OK, "split por DT_INTERNA")
    tp = y.get("temporal", {}) or {}
    rep.add(st, "C2 x split por datas", WARN,
            "o C2 enviado cria `TemporalSplit(df, coluna_tempo, frac_treino, frac_validacao)` e não lê "
            "`temporal.modo`/`temporal.datas`: para holdout = 2025 o C precisa adaptar o split")
    if tp.get("modo") != "datas":
        rep.add(st, "Split temporal", WARN,
                f"modo='{tp.get('modo')}' (fração). Plano: desenvolvimento {cfg['dev_years']} / holdout "
                f"{cfg['holdout_years']} -> usar modo 'datas' (G2)")
    else:
        d = tp.get("datas", {}) or {}
        try:
            h0 = pd.Timestamp(d["holdout"]["start"])
            v1 = pd.Timestamp(d["validacao"]["end"])
            t0 = pd.Timestamp(d["treino"]["start"])
            ok = v1 < h0 and h0.year == min(cfg["holdout_years"]) and t0.year == min(cfg["dev_years"])
            rep.add(st, "Split temporal (datas)", OK if ok else FAIL,
                    f"treino>={t0.date()}, validação<={v1.date()}, holdout>={h0.date()}"
                    + ("" if ok else " — inconsistente com o plano"))
        except Exception:
            rep.add(st, "Split temporal (datas)", FAIL, "datas incompletas ou inválidas")
    if schema_cols:
        fisico = {str(c).lower() for c in schema_cols}
        por_canon = {canon(c): str(c).lower() for c in schema_cols}
        f = y.get("features", {}) or {}
        pedidas = [str(x).lower() for x in ((f.get("final") or []) + (f.get("numericas") or []) + (f.get("categoricas") or []))]
        if f.get("final"):
            pedidas = [str(x).lower() for x in f["final"]]
        deriv_pedidas = [n for n in pedidas if n in DERIVADAS]
        if deriv_pedidas:
            rep.add(st, "Features derivadas do YAML", OK,
                    f"{', '.join(deriv_pedidas)} não existem no Parquet: a Pessoa A as cria no dataset analítico")
        for rotulo, nomes, status in (("Features do YAML x Parquet", pedidas, FAIL),
                                      ("`proibidas` do YAML x Parquet", [str(x).lower() for x in (f.get("proibidas") or [])], WARN)):
            ausentes = [n for n in nomes if n not in fisico and n not in DERIVADAS]
            if ausentes:
                dicas = [f"{n}->{por_canon[canon(n)]}" for n in ausentes if canon(n) in por_canon]
                rep.add(st, rotulo, status,
                        f"não existem no Parquet: {', '.join(ausentes)}"
                        + (f" (nome físico provável: {', '.join(dicas)})" if dicas else "")
                        + (" — o C2 não conseguirá carregá-las" if status == FAIL else " — test_leakage não protege as colunas reais"))
            else:
                rep.add(st, rotulo, OK, "todos os nomes existem no Parquet")
    feats = supervised_features(y)
    forb = {canon(v) for v in cfg["forbidden_vars"]}
    yml_forb = {canon(v) for v in (y.get("features", {}) or {}).get("proibidas", []) or []}
    hit = sorted(set(feats) & (forb | yml_forb))
    soft = [h for h in hit if h == "HOSPITAL"]
    hard = [h for h in hit if h not in soft]
    if hard:
        rep.add(st, "Features x proibidas", FAIL, f"em X: {', '.join(hard)}")
    if soft:
        rep.add(st, "Feature constante", WARN, "internado/HOSPITAL é critério de inclusão (constante na coorte)")
    if not hit:
        rep.add(st, "Features x proibidas", OK, f"{len(feats)} features sem conflito")
    faltam = sorted(forb - yml_forb - {"HOSPITAL"})
    if faltam:
        rep.add(st, "Lista `proibidas` do YAML", WARN,
                f"{len(faltam)} do plano não protegidas pelo test_leakage: {', '.join(faltam[:12])}")
    if "NU_IDADE_N" in feats and not any(f in feats for f in ("TP_IDADE", "IDADE_ANOS")):
        rep.add(st, "Idade", WARN, "nu_idade_n sem tp_idade: unidade mistura dias/meses/anos; converter para anos")
    cond = sorted(set(feats) & {canon(v) for v in cfg["conditional_vars"]})
    if cond:
        rep.add(st, "Features condicionais", WARN, f"confirmar condição de uso: {', '.join(cond)}")
    pend = [k for k, v in (y.get("gates") or {}).items() if (v or {}).get("status") != "aprovado"]
    if pend:
        rep.add(st, "Gates", WARN, f"{len(pend)} pendentes: {', '.join(pend[:4])}... (A aprova G1/G2 com as regras A1–A3)")


def a3_forbidden(features: list[str], label: str, cfg, rep: Report, must_exclude_target=True) -> None:
    forb = {v.upper() for v in cfg["forbidden_vars"]}
    hit = sorted(set(features) & forb)
    hard = [h for h in hit if h != "HOSPITAL"]
    if "HOSPITAL" in hit:
        rep.add("A3", f"Feature constante ({label})", WARN, "HOSPITAL/internado é critério de inclusão (constante na coorte)")
    if hard:
        rep.add("A3", f"Variáveis proibidas ({label})", FAIL, f"presentes: {', '.join(hard)}")
    elif not hit:
        rep.add("A3", f"Variáveis proibidas ({label})", OK, f"{len(features)} variáveis, nenhuma proibida")
    cond = sorted(set(features) & {v.upper() for v in cfg["conditional_vars"]})
    if cond:
        rep.add("A3", f"Variáveis condicionais ({label})", WARN, f"confirmar condição de uso: {', '.join(cond)}")
    if label == "clustering" and must_exclude_target and cfg["cols"]["evolucao"] in features:
        rep.add("A3", "Desfecho no clustering", FAIL, "EVOLUCAO não pode formar clusters")


def a3_temporal_split(cohort: pd.DataFrame, cfg, rep: Report) -> None:
    dev, hold = set(cfg["dev_years"]), set(cfg["holdout_years"])
    problems = []
    if dev & hold:
        problems.append(f"anos sobrepostos: {sorted(dev & hold)}")
    if hold and dev and min(hold) <= max(dev):
        problems.append("holdout não é posterior ao desenvolvimento")
    present = set(cohort["_ano"].unique())
    if hold - present:
        problems.append(f"holdout sem registros: {sorted(hold - present)}")
    if dev - present:
        problems.append(f"desenvolvimento sem registros: {sorted(dev - present)}")
    split = np.where(cohort["_ano"].isin(dev), "desenvolvimento", np.where(cohort["_ano"].isin(hold), "holdout", "fora"))
    tab = (cohort.assign(split=split).groupby(["split", "_ano"])["_alvo"]
           .agg(n="size", n_obitos="sum", prevalencia_obito=lambda x: round(100 * x.mean(), 2)).reset_index())
    rep.save("a3_split_temporal", tab)
    if problems:
        rep.add("A3", "Split temporal", FAIL, "; ".join(problems))
        return
    prev = tab.groupby("split")["n_obitos"].sum() / tab.groupby("split")["n"].sum() * 100
    diff = abs(prev.get("holdout", np.nan) - prev.get("desenvolvimento", np.nan))
    if diff > 10:
        rep.add("A3", "Split temporal", WARN, f"prevalência difere {diff:.1f} p.p. entre dev e holdout (drift)")
    else:
        rep.add("A3", "Split temporal", OK, f"dev {sorted(dev)} < holdout {sorted(hold)}; Δ prevalência {diff:.1f} p.p.")


def a3_leak_scan(cohort: pd.DataFrame, cfg, rep: Report) -> None:
    """AUC univariada contra o alvo: valores ~1 sugerem vazamento (indicativo, não prova)."""
    from sklearn.metrics import roc_auc_score

    skip = set(cfg["cols"].values()) | {"_ano", "_alvo"}
    data = cohort.sample(min(len(cohort), cfg["leak_sample"]), random_state=0)
    y = data["_alvo"].to_numpy()
    if len(np.unique(y)) < 2:
        rep.add("A3", "Varredura de vazamento", WARN, "alvo com uma única classe; varredura não executada")
        return
    rows = []
    for col in data.columns:
        if col in skip:
            continue
        s = data[col]
        try:
            if pd.api.types.is_numeric_dtype(s):
                x = s.fillna(s.median()).to_numpy(float)
            else:
                if s.nunique() > cfg["leak_max_categories"]:
                    continue
                x = data.groupby(s.astype("string").fillna("<NA>"))["_alvo"].transform("mean").to_numpy(float)
            auc = roc_auc_score(y, x)
        except Exception:
            continue
        rows.append(dict(coluna=col, auc_univariada=round(auc, 4), forca=round(abs(auc - 0.5) * 2, 4)))
    res = pd.DataFrame(rows).sort_values("forca", ascending=False)
    rep.save("a3_varredura_vazamento", res)
    thr = cfg["leak_auc_threshold"]
    sus = res[(res["auc_univariada"] >= thr) | (res["auc_univariada"] <= 1 - thr)]
    if len(sus):
        rep.add("A3", "Varredura de vazamento", WARN,
                f"AUC univariada ≥ {thr}: {', '.join(sus['coluna'].head(8))} — investigar")
    else:
        rep.add("A3", "Varredura de vazamento", OK, f"nenhuma variável com AUC univariada ≥ {thr}")


def a3_suspicious_metrics(results: pd.DataFrame, cfg, rep: Report) -> None:
    res = results.copy()
    res.columns = [c.lower() for c in res.columns]
    thr = cfg["suspicious_metric_threshold"]
    cols = [c for c in ("roc_auc", "pr_auc") if c in res.columns]
    if not cols:
        rep.add("A3", "Métricas suspeitas", WARN, "colunas roc_auc/pr_auc não encontradas")
        return
    flag = res[(res[cols] >= thr).any(axis=1)]
    if len(flag):
        rep.add("A3", "Métricas suspeitas", WARN, f"{len(flag)} linha(s) com métrica ≥ {thr}: possível vazamento")
    else:
        rep.add("A3", "Métricas suspeitas", OK, f"nenhuma métrica ≥ {thr}")


def a3_audit_logs(logs_dir: str | Path, cfg, rep: Report) -> None:
    d = Path(logs_dir)
    files = [p for p in d.rglob("*") if p.is_file() and p.suffix in (".json", ".jsonl", ".log", ".txt")] if d.exists() else []
    if not files:
        rep.add("A3", "Auditoria de logs", WARN, f"nenhum log encontrado em {d}")
        return
    rows = []
    for p in files:
        txt = p.read_text(encoding="utf-8", errors="ignore")
        row = {"arquivo": str(p)}
        for k, rx in cfg["log_required_keys"].items():
            row[k] = bool(re.search(rx, txt, flags=re.I))
        rows.append(row)
    res = pd.DataFrame(rows)
    rep.save("a3_auditoria_logs", res)
    keys = list(cfg["log_required_keys"])
    incompletos = res[~res[keys].all(axis=1)]
    if len(incompletos):
        faltas = {k for k in keys if not res[k].all()}
        rep.add("A3", "Auditoria de logs", WARN, f"{len(incompletos)}/{len(res)} logs incompletos (faltam: {', '.join(sorted(faltas))})")
    else:
        rep.add("A3", "Auditoria de logs", OK, f"{len(res)} logs com todos os campos mínimos")


# =============================================================================
# A4 — Candidatos e decisão
# =============================================================================
def a4_decision_table(results: pd.DataFrame, cfg, rep: Report) -> None:
    """Espera colunas: modelo, [fold], roc_auc, pr_auc, brier (nomes case-insensitive)."""
    res = results.copy()
    res.columns = [c.lower() for c in res.columns]
    alias = {"model": "modelo", "candidate": "modelo", "candidato": "modelo"}
    res = res.rename(columns=alias)
    if "modelo" not in res.columns:
        rep.add("A4", "Tabela de decisão", FAIL, "coluna 'modelo' não encontrada")
        return
    metrics = [m for m in ("pr_auc", "roc_auc", "brier") if m in res.columns]
    agg = res.groupby("modelo")[metrics].agg(["mean", "std"])
    agg.columns = [f"{m}_{s}" for m, s in agg.columns]
    agg = agg.reset_index()
    lower = agg["modelo"].str.lower()
    base = agg[lower.str.contains("baseline|dummy|prevalen")]
    logi = agg[lower.str.contains("log")]
    notes = []
    for _, r in agg.iterrows():
        n = []
        if "pr_auc_mean" in agg.columns and len(logi) and "log" not in r["modelo"].lower() \
                and not re.search("baseline|dummy|prevalen", r["modelo"].lower()):
            gain = r["pr_auc_mean"] - logi["pr_auc_mean"].iloc[0]
            if gain < cfg["decision_min_pr_auc_gain"]:
                n.append(f"ganho de PR-AUC sobre a logística ({gain:+.3f}) não justifica complexidade")
            if "brier_mean" in agg.columns and r["brier_mean"] > logi["brier_mean"].iloc[0]:
                n.append("Brier pior que a logística")
        if "pr_auc_mean" in agg.columns and len(base) and r["pr_auc_mean"] <= base["pr_auc_mean"].iloc[0] \
                and not re.search("baseline|dummy|prevalen", r["modelo"].lower()):
            n.append("não supera o baseline em PR-AUC")
        if "pr_auc_std" in agg.columns and r["pr_auc_mean"] > 0 and r["pr_auc_std"] / r["pr_auc_mean"] > cfg["decision_max_cv_ratio"]:
            n.append("alta variação entre folds")
        notes.append("; ".join(n) if n else "sem alerta automático")
    agg["alertas_automaticos"] = notes
    agg["decisao"] = ""
    agg["justificativa_descarte_ou_manutencao"] = ""
    agg["pendencia_para_18_10"] = ""
    rep.save("a4_tabela_decisao", agg.round(4))
    n_alert = sum(n != "sem alerta automático" for n in notes)
    rep.add("A4", "Tabela de decisão", WARN if n_alert else OK,
            f"{len(agg)} candidatos; {n_alert} com alerta — preencher decisão/justificativa")


# =============================================================================
# Config, carga da base e registros (decisões / atas)
# =============================================================================
def load_config(path: str | Path | None = "configs/decisoes.yaml") -> dict:
    """DEFAULT_CONFIG sobreposto pelo YAML de decisões (se existir)."""
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    if path and Path(path).exists():
        import yaml

        for k, v in (yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}).items():
            cfg[k] = {**cfg[k], **v} if isinstance(cfg.get(k), dict) and isinstance(v, dict) else v
    return cfg


def find_base(root: str | Path = ".") -> Path | None:
    """Procura a base ORIGINAL (Parquet/CSV). Ignora data/analytical (saída da Pessoa A) e metadados."""
    r = Path(root)
    for pat in ("data/raw/**/*.parquet", "data/**/*.parquet", "data/raw/**/*.csv", "data/**/*.csv"):
        hits = [h for h in sorted(r.glob(pat))
                if "analytical" not in h.parts and "dataset_supervisionado" not in h.name]
        if hits:
            return hits[0]
    return None


def colunas_necessarias(schema_cols, cfg: dict, supervised_config=None, modo: str = "classificadas") -> list[str]:
    """Colunas físicas do Parquet que as verificações realmente usam (a base tem ~194; carregar todas estoura a memória).

    modo "minimas": essenciais (coorte/alvo/datas) + códigos esperados + o que o supervised.yaml pede
    (features, alvo, tempo, grupos). modo "classificadas": soma as listas proibidas/condicionais/permitidas (A2).
    """
    need = {canon(x) for x in cfg["cols"].values()} | {canon(x) for x in cfg["expected_codes"]}
    if modo != "minimas":
        for k in ("forbidden_vars", "conditional_vars", "allowed_vars"):
            need |= {canon(x) for x in cfg[k]}
    if supervised_config and Path(supervised_config).exists():
        y = load_supervised_yaml(supervised_config)
        f = y.get("features", {}) or {}
        need |= {canon(x) for x in supervised_features(y)}
        need |= {canon(x) for x in (f.get("proibidas") or [])}
        need |= {canon(x) for x in ((y.get("avaliacao") or {}).get("grupos") or [])}
        need |= {canon((y.get("target") or {}).get("coluna", cfg["cols"]["evolucao"])), canon(y.get("coluna_tempo", ""))}
    return [c for c in schema_cols if canon(c) in need]


def carregar_base(path=None, demo: bool = False, sample: int = 0, colunas="classificadas",
                  cfg: dict | None = None, supervised_config=None, compactar: bool = True) -> pd.DataFrame:
    """Lê a base. path=None -> usa `src.utils.storage.get_parquet()` do projeto (ou procura em data/).

    colunas: "minimas" (só o essencial + o que o supervised.yaml pede; A1/A3/A3b), "classificadas" (soma as listas de
    variáveis; A2), "todas" (pesado) ou lista de nomes. O schema completo fica em df.attrs["schema_cols"].
    compactar=True lê o Parquet via pyarrow com texto em `category` (e libera a tabela Arrow durante a conversão):
    reduz muito o pico de memória (a base tem milhões de linhas).
    """
    if demo:
        print("[demo] usando dados sintéticos")
        df = make_demo()[0]
        df.attrs["schema_cols"] = list(df.columns)
        return df
    p = Path(path) if path else None
    if p is None:
        try:
            from src.utils import storage  # pipeline do projeto

            p = Path(storage.get_parquet(force=False))
        except Exception as e:  # noqa: BLE001
            print(f"[storage] indisponível ({type(e).__name__}); procurando em data/ ...")
            p = find_base()
    if p is None or not p.exists():
        raise FileNotFoundError(
            f"Base não encontrada (procurei em '{Path.cwd() / 'data'}' por *.parquet e *.csv). "
            "Informe DATA_PATH com o caminho do arquivo ou coloque-o em data/raw/.")
    cfg = cfg or load_config()
    modo_leitura = "padrão"
    if p.suffix == ".parquet":
        import pyarrow.parquet as pq

        schema_cols = pq.ParquetFile(p).schema_arrow.names
        if colunas == "todas":
            cols = None
        elif isinstance(colunas, (list, tuple)):
            cols = [c for c in schema_cols if c.lower() in {str(x).lower() for x in colunas}]
        else:
            cols = colunas_necessarias(schema_cols, cfg, supervised_config, modo=str(colunas))
        df = None
        if compactar:
            try:
                tabela = pq.read_table(p, columns=cols)
                df = tabela.to_pandas(self_destruct=True, strings_to_categorical=True, split_blocks=True)
                del tabela
                modo_leitura = "compacto (texto em category)"
            except Exception as e:  # noqa: BLE001
                print(f"[leitura compacta falhou: {type(e).__name__}: {str(e)[:80]}] usando leitura padrão")
                df = None
        if df is None:
            df = pd.read_parquet(p, columns=cols)
    else:
        df = pd.read_csv(p, low_memory=False)
        schema_cols = list(df.columns)
    df.attrs["schema_cols"] = list(schema_cols)
    print(f"[base] {p} -> {len(df):,} linhas x {df.shape[1]} colunas carregadas (de {len(schema_cols)} no arquivo) | leitura {modo_leitura}")
    if sample and len(df) > sample:
        df = df.sample(sample, random_state=0)
        print(f"[amostra] {sample:,} linhas")
    return df


def uso_memoria_gb(df: pd.DataFrame) -> float:
    return float(df.memory_usage(index=False, deep=True).sum() / 1e9)


DECISION_COLS = ["id", "etapa", "tema", "decisao", "responsavel", "data", "status", "impacto", "evidencia"]


def log_decision(out, id: str, tema: str, decisao: str, etapa: str = "", responsavel: str = "Pessoa A",
                 status: str = "proposta", impacto: str = "", evidencia: str = "") -> pd.DataFrame:
    """Insere/atualiza (por id) uma linha na tabela de decisões. status: proposta | aprovada | revisar."""
    path = Path(out) / "tabela_decisoes.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    row = dict(id=id, etapa=etapa, tema=tema, decisao=decisao, responsavel=responsavel,
               data=pd.Timestamp.today().date().isoformat(), status=status, impacto=impacto, evidencia=evidencia)
    t = pd.read_csv(path, dtype=str).fillna("") if path.exists() else pd.DataFrame(columns=DECISION_COLS)
    t = pd.concat([t[t["id"] != id], pd.DataFrame([row])], ignore_index=True)[DECISION_COLS]
    t.to_csv(path, index=False, encoding="utf-8-sig")
    return t


def write_ata(out, nome: str, data: str, decisoes=(), pendencias=(), riscos=(), shortlist=(),
              descartes=(), rep: Report | None = None) -> Path:
    """Gera a ata (Gates 2/3, 17/10...) em Markdown a partir de listas e dos alertas do relatório."""
    def sec(titulo, itens):
        return [f"## {titulo}", ""] + ([f"- {i}" for i in itens] if itens else ["- (nenhum registrado)"]) + [""]

    lines = [f"# {nome}", "", f"**Data:** {data}", ""]
    lines += sec("Decisões", decisoes) + sec("Candidatos na shortlist", shortlist) + sec("Descartes e justificativas", descartes)
    lines += sec("Riscos", riscos) + sec("Pendências", pendencias)
    if rep is not None:
        alerts = [f for f in rep.findings if f[2] != OK]
        lines += ["## Alertas das verificações automáticas", ""]
        lines += [f"- [{f[2]}] {f[0]} / {f[1]}: {f[3]}" for f in alerts] or ["- nenhum"]
    slug = re.sub(r"[^a-z0-9]+", "_", nome.lower()).strip("_")
    path = Path(out) / (slug if slug.startswith("ata_") else f"ata_{slug}") 
    path = path.with_suffix(".md")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


# =============================================================================
# Execução
# =============================================================================
def run(df: pd.DataFrame, args, cfg: dict) -> Report:
    rep = Report(args.out)
    df = prepare(df)
    if args.sample and len(df) > args.sample:
        df = df.sample(args.sample, random_state=0)
        print(f"[amostra] usando {args.sample:,} linhas")
    stage = args.stage
    do = lambda s: stage in (s, "all")  # noqa: E731

    a1_columns(df, cfg, rep)
    if rep.has_failure:
        rep.write_md()
        return rep

    cohort = None
    if do("a1") or do("a3"):
        if do("a1"):
            a1_code_tables(df, cfg, rep)
            a1_waterfall(df, cfg, rep)
            a1_target(df, cfg, rep)
        cohort = a1_cohort(df, cfg)
    if do("a2"):
        a2_missing(df, cfg, rep)
        a2_dates(df, cfg, rep)
        a2_duplicates(df, cfg, rep)
        a2_maturity(df, cfg, rep)
        a2_eligibility(df, cfg, rep)
    if do("a3"):
        if args.supervised_config:
            y = load_supervised_yaml(args.supervised_config)
            a3_config_audit(y, cfg, rep, df.attrs.get("schema_cols"))
            if not args.features_supervised:
                a3_forbidden(supervised_features(y), "supervisionado", cfg, rep)
        if args.features_supervised:
            a3_forbidden(load_feature_list(args.features_supervised), "supervisionado", cfg, rep)
        if args.features_clustering:
            a3_forbidden(load_feature_list(args.features_clustering), "clustering", cfg, rep)
        if cohort is not None and len(cohort):
            a3_temporal_split(cohort, cfg, rep)
            a3_leak_scan(cohort, cfg, rep)
        if args.logs_dir:
            a3_audit_logs(args.logs_dir, cfg, rep)
        if args.results:
            a3_suspicious_metrics(pd.read_csv(args.results), cfg, rep)
    if do("a4") and args.results:
        a4_decision_table(pd.read_csv(args.results), cfg, rep)
    elif stage == "a4":
        rep.add("A4", "Tabela de decisão", FAIL, "informe --results com a tabela de experimentos")
    path = rep.write_md()
    print(f"\nRelatório: {path}")
    return rep


def make_demo(n: int = 30_000, seed: int = 0, inicio: str = "2022-01-01", anos: int = 4) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Dados sintéticos com defeitos plantados, para testar o script."""
    rng = np.random.default_rng(seed)
    interna = pd.Timestamp(inicio) + pd.to_timedelta(rng.integers(0, 365 * anos - 30, n), unit="D")
    sint = interna - pd.to_timedelta(rng.integers(0, 10, n), unit="D")
    df = pd.DataFrame({
        "NU_NOTIFIC": rng.integers(10**8, 10**9, n).astype(str),
        "DT_NOTIFIC": sint + pd.to_timedelta(rng.integers(0, 5, n), unit="D"),
        "DT_SIN_PRI": sint,
        "DT_INTERNA": interna,
        "DT_NASC": sint - pd.to_timedelta(rng.integers(365, 365 * 90, n), unit="D"),
        "NU_IDADE_N": rng.integers(1, 90, n),
        "TP_IDADE": 3,
        "HOSPITAL": rng.choice([1, 2, 9], n, p=[0.9, 0.08, 0.02]),
        "CS_SEXO": rng.choice(["M", "F", "I"], n, p=[0.49, 0.5, 0.01]),
        "FEBRE": rng.choice([1, 2, 9], n),
        "DISPNEIA": rng.choice([1, 2, 9], n),
        "SATURACAO": rng.choice([1, 2, 9, np.nan], n),
    })
    risk = (df["NU_IDADE_N"] / 90 + (df["DISPNEIA"] == 1) * 0.3 + rng.normal(0, 0.4, n))
    obito = risk > 0.9
    evo = np.where(obito, 2, 1)
    evo = np.where(rng.random(n) < 0.03, 3, evo)
    evo = np.where(rng.random(n) < 0.04, 9, evo)
    df["EVOLUCAO"] = evo
    df["DT_EVOLUCA"] = interna + pd.to_timedelta(rng.integers(2, 30, n), unit="D")
    df["DT_ENCERRA"] = df["DT_EVOLUCA"] + pd.to_timedelta(rng.integers(0, 40, n), unit="D")
    df["UTI"] = np.where(obito, rng.choice([1, 2], n, p=[0.8, 0.2]), rng.choice([1, 2], n, p=[0.3, 0.7]))
    df["VAZ_DEMO"] = (obito).astype(int)  # vazamento plantado
    # defeitos plantados
    df.loc[:30, "DT_INTERNA"] = pd.NaT
    df.loc[31:60, "DT_EVOLUCA"] = df.loc[31:60, "DT_INTERNA"] - pd.Timedelta(days=5)
    df.loc[61:90, "EVOLUCAO"] = 7
    df = pd.concat([df, df.iloc[200:230]], ignore_index=True)  # duplicatas exatas
    # 2025 imaturo: evolução ainda aberta nos meses finais
    late = df["DT_INTERNA"] >= pd.Timestamp("2025-09-01")
    df.loc[late & (rng.random(len(df)) < 0.5), "EVOLUCAO"] = np.nan
    res = pd.DataFrame({
        "modelo": ["baseline"] * 3 + ["logistica"] * 3 + ["boosting"] * 3 + ["boosting_leak"] * 3,
        "fold": [1, 2, 3] * 4,
        "pr_auc": [0.15, 0.16, 0.15, 0.40, 0.42, 0.38, 0.405, 0.41, 0.39, 0.99, 0.99, 0.98],
        "roc_auc": [0.5, 0.5, 0.5, 0.80, 0.81, 0.79, 0.805, 0.81, 0.80, 0.99, 0.99, 0.99],
        "brier": [0.15, 0.15, 0.15, 0.10, 0.10, 0.11, 0.11, 0.10, 0.11, 0.01, 0.01, 0.01],
    })
    return df, res
```

## `src/utils/__init__.py`

- Git: `tracked` · status `clean`
- Size: `0 B` · modified `2026-10-06 02:28 UTC`
- SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

```python

```

## `src/utils/config.py`

- Git: `tracked` · status `clean`
- Size: `8.0 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `83593c64261804f7b18aab33d121ef6e4d90c7a65aa612fb5649bf4889fed358`

```python
"""
Configurações centralizadas do Projeto Integrador.

Fonte única da verdade para diretórios, identificação da versão dos dados,
seed de reprodutibilidade e acesso tipado ao ``configs/supervised.yaml``.

Segredos e URLs sensíveis (``GITHUB_TOKEN``, ``SRAG_PARQUET_URL``) são lidos
em tempo de execução via ``os.getenv``, nunca no import. O YAML aceita
interpolação ``${VAR}``, resolvida no momento da leitura.

Uso típico::

    from src.utils import config as C

    C.SEED
    C.OUTPUTS_DIR
    C.cfg("target", "coluna")
    C.exigir_gate("G7_calibracao")
"""

from __future__ import annotations

import hashlib
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


ROOT_DIR: Path = Path(__file__).resolve().parents[2]

SEED         = 42
RANDOM_STATE = SEED

DATA_DIR       = ROOT_DIR / "data"
RAW_DIR        = DATA_DIR / "raw"
PROCESSED_DIR  = DATA_DIR / "processed"
ANALYTICAL_DIR = DATA_DIR / "analytical"
TREINO_DIR     = DATA_DIR / "treino"

CONFIGS_DIR  = ROOT_DIR / "configs"
MODELS_DIR   = ROOT_DIR / "models"
OUTPUTS_DIR  = ROOT_DIR / "outputs"
RUNS_DIR     = OUTPUTS_DIR / "runs"
LOGS_DIR     = ROOT_DIR / "logs"
REPORTS_DIR  = ROOT_DIR / "reports"
FIGURES_DIR  = REPORTS_DIR / "figures"

TABLES_DIR      = OUTPUTS_DIR / "tables"
PREDICTIONS_DIR = OUTPUTS_DIR / "predictions"

SUPERVISED_YAML = CONFIGS_DIR / "supervised.yaml"

GITHUB_REPO  = "Ivan-S-Oliveira/Projeto_Integrador"
DATA_VERSION = "dados-v2"
PARQUET_NAME = "srag.parquet"

GITHUB_RELEASE_URL = (
    f"https://github.com/{GITHUB_REPO}/releases/download/{DATA_VERSION}/"
)

HTTP_TIMEOUT    = 180
HTTP_TENTATIVAS = 3
HTTP_BACKOFF    = 5

CSV_SEP      = ","
CSV_ENCODING = "utf-8-sig"
COLS         = None

PARQUET_COMPRESSION = "zstd"
CSV_CHUNKSIZE       = 500_000


class GatePendenteError(RuntimeError):
    """Levantado quando se tenta usar um valor que depende de gate não aprovado."""


def github_token() -> str | None:
    """Token do GitHub (opcional) para releases/downloads autenticados."""
    return os.getenv("GITHUB_TOKEN")


def srag_parquet_url() -> str:
    """URL do Parquet oficial processado.

    Construída a partir de ``GITHUB_REPO`` / ``DATA_VERSION`` /
    ``PARQUET_NAME``. Pode ser sobrescrita via ``SRAG_PARQUET_URL``.
    """
    url_padrao = (
        f"https://github.com/{GITHUB_REPO}/releases/download/"
        f"{DATA_VERSION}/{PARQUET_NAME}"
    )
    return os.getenv("SRAG_PARQUET_URL", url_padrao).strip() or url_padrao


_ENV_PATTERN = re.compile(r"\$\{(\w+)\}")


def _interpolar_env(texto: str) -> str:
    """Substitui ``${VAR}`` pelo valor de ``os.getenv``; ausente vira ``""``."""
    return _ENV_PATTERN.sub(lambda m: os.getenv(m.group(1), ""), texto)


def _get_nested(mapping: Any, *chaves: str, default: Any = None) -> Any:
    """Acesso a caminho de chaves num dict; devolve ``default`` se faltar."""
    atual = mapping
    for k in chaves:
        if not isinstance(atual, dict) or k not in atual:
            return default
        atual = atual[k]
    return atual


@lru_cache(maxsize=1)
def carregar_supervised() -> dict[str, Any]:
    """Lê ``configs/supervised.yaml`` e devolve o dict parseado (cacheado).

    Resolve ``${VAR}`` antes do parse. Levanta ``FileNotFoundError`` se o
    YAML não existir e ``ValueError`` se a raiz não for mapping.
    """
    if not SUPERVISED_YAML.exists():
        raise FileNotFoundError(
            f"Configuração não encontrada: {SUPERVISED_YAML}\n"
            f"Crie o arquivo em {CONFIGS_DIR}/supervised.yaml "
            f"ou ajuste CONFIGS_DIR / SUPERVISED_YAML em config.py."
        )

    texto = _interpolar_env(SUPERVISED_YAML.read_text(encoding="utf-8"))
    dados = yaml.safe_load(texto) or {}

    if not isinstance(dados, dict):
        raise ValueError(
            f"{SUPERVISED_YAML} deve conter um mapeamento (dict) na raiz, "
            f"mas veio {type(dados).__name__}."
        )
    return dados


def supervised_yaml_sha256() -> str | None:
    """SHA-256 do ``supervised.yaml``, ou ``None`` se o arquivo não existir."""
    if not SUPERVISED_YAML.exists():
        return None
    h = hashlib.sha256()
    with open(SUPERVISED_YAML, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def cfg(*chaves: str, default: Any = None) -> Any:
    """Acessa ``configs/supervised.yaml`` por caminho de chaves.

    Exemplo::

        cfg("target", "coluna")       # → "evolucao"
        cfg("temporal", "fracao")     # → {"treino": 0.7, "validacao": 0.15}

    Devolve ``default`` se qualquer chave do caminho não existir.
    """
    return _get_nested(carregar_supervised(), *chaves, default=default)


def exigir_valor(valor: Any, *, caminho: str, gate: str) -> Any:
    """Devolve ``valor`` se preenchido; levanta ``GatePendenteError`` se ``None`` ou ``"TBD"``.

    Usado para valores do YAML que só podem ser preenchidos após gate aprovado.
    """
    if valor is None or valor == "TBD":
        raise GatePendenteError(
            f"Valor não definido em '{caminho}'. "
            f"Aprove o gate '{gate}' em configs/supervised.yaml antes de usar."
        )
    return valor


def gate_aprovado(nome_gate: str) -> bool:
    """True se ``gates.<nome_gate>.status == 'aprovado'``."""
    return _get_nested(carregar_supervised(), "gates", nome_gate, default={}).get("status") == "aprovado"


def exigir_gate(nome_gate: str) -> None:
    """Levanta ``GatePendenteError`` se o gate ainda não estiver aprovado.

    Use no início de etapas que dependem de decisão metodológica congelada
    (ex.: holdout antes de G9).
    """
    if not gate_aprovado(nome_gate):
        raise GatePendenteError(
            f"Gate '{nome_gate}' está pendente. "
            f"Aprove-o em configs/supervised.yaml (status: aprovado) "
            f"antes de rodar esta etapa."
        )


def features_finais() -> list[str]:
    """Lista final de features.

    Usa ``features.final`` se preenchida; caso contrário, concatena
    ``features.numericas`` + ``features.categoricas``.
    """
    f = cfg("features") or {}
    return list(f["final"]) if f.get("final") else (
        list(f.get("numericas", [])) + list(f.get("categoricas", []))
    )


def limiar_ativo() -> float:
    """Limiar de decisão vigente.

    Usa ``limiar.otimo`` se o gate ``G8_limiar`` estiver aprovado e o valor
    preenchido; caso contrário, cai em ``limiar.default`` (0.5).
    """
    lim = cfg("limiar") or {}
    if gate_aprovado("G8_limiar") and lim.get("otimo") is not None:
        return float(lim["otimo"])
    return float(lim.get("default", 0.5))


def resumo() -> str:
    """Resumo legível das configurações ativas — usado em bootstrap de notebooks."""
    yaml_ok = "ok" if SUPERVISED_YAML.exists() else "AUSENTE"
    linhas = [
        ("ROOT_DIR",          ROOT_DIR),
        ("DATA_DIR",          DATA_DIR),
        ("RAW_DIR",           RAW_DIR),
        ("PROCESSED_DIR",     PROCESSED_DIR),
        ("ANALYTICAL_DIR",    ANALYTICAL_DIR),
        ("TREINO_DIR",        TREINO_DIR),
        ("OUTPUTS_DIR",       OUTPUTS_DIR),
        ("RUNS_DIR",          RUNS_DIR),
        ("LOGS_DIR",          LOGS_DIR),
        ("CONFIGS_DIR",       CONFIGS_DIR),
        ("SUPERVISED_YAML",   f"{SUPERVISED_YAML} ({yaml_ok})"),
        ("PARQUET_NAME",      PARQUET_NAME),
        ("DATA_VERSION",      DATA_VERSION),
        ("GITHUB_REPO",       GITHUB_REPO),
        ("HTTP_TIMEOUT",      HTTP_TIMEOUT),
        ("HTTP_TENTATIVAS",   HTTP_TENTATIVAS),
        ("SEED",              SEED),
        ("GITHUB_TOKEN?",     bool(github_token())),
        ("SRAG_PARQUET_URL",  srag_parquet_url()),
        ("SUPERVISED_SHA256", supervised_yaml_sha256()),
    ]
    return "\n".join(f"{nome:18s}= {valor}" for nome, valor in linhas)


if __name__ == "__main__":
    print(resumo())
```

## `src/utils/env.py`

- Git: `tracked` · status `clean`
- Size: `3.7 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `7dce7d27c80c42f4efe7f89128fafb3763fe78c8070593ad5c3d508284ce866b`

```python
"""
Variáveis de ambiente e segredos do projeto.

Fluxo: ``.env`` → ``os.environ`` → ``config.py`` → restante do projeto.

O arquivo ``.env`` nunca é versionado (ver ``.gitignore``); use
``.env.example`` como template. Diretórios são aliases de
``src.utils.config``, fonte única da verdade.
"""

from __future__ import annotations

import os
from pathlib import Path

from src.utils import config as C


# Aliases públicos — conveniência para notebooks e testes.
ROOT      = C.ROOT_DIR
DATA      = C.DATA_DIR
RAW       = C.RAW_DIR
PROCESSED = C.PROCESSED_DIR
TREINO    = C.TREINO_DIR
FIGURES   = C.FIGURES_DIR

# Diretórios criados por ``garantir_diretorios``. A ordem não importa —
# ``mkdir(parents=True)`` cria a árvore conforme necessário.
_DIRS_PADRAO = (
    C.DATA_DIR, C.RAW_DIR, C.PROCESSED_DIR, C.ANALYTICAL_DIR,
    C.TREINO_DIR, C.CONFIGS_DIR, C.MODELS_DIR, C.OUTPUTS_DIR,
    C.RUNS_DIR, C.LOGS_DIR, C.REPORTS_DIR, C.FIGURES_DIR,
    C.TABLES_DIR, C.PREDICTIONS_DIR,
)


def garantir_diretorios() -> None:
    """Cria todos os diretórios padrão do projeto, se ainda não existirem.

    Percorre as constantes de ``config.py`` — nenhum caminho é redefinido aqui.
    """
    for p in _DIRS_PADRAO:
        p.mkdir(parents=True, exist_ok=True)


def carregar_dotenv(caminho: Path | None = None) -> bool:
    """Carrega ``.env`` da raiz do projeto (ou de ``caminho``).

    Retorna ``True`` se o arquivo foi encontrado e carregado, ``False`` caso
    contrário (arquivo ausente ou ``python-dotenv`` indisponível). Não
    sobrescreve variáveis já definidas no ambiente.
    """
    # Lazy: python-dotenv não é dependência obrigatória — permite importar
    # este módulo em ambientes que não o têm instalado.
    try:
        from dotenv import load_dotenv
    except ImportError:
        return False

    caminho = Path(caminho) if caminho else ROOT / ".env"
    if not caminho.exists():
        return False

    load_dotenv(dotenv_path=caminho, override=False)
    return True


def detectar_ambiente() -> str:
    """``"ci"`` se estiver em pipeline, senão ``"local"``."""
    return "ci" if os.getenv("CI") or os.getenv("GITHUB_ACTIONS") else "local"


ENV = detectar_ambiente()


def get_env(nome: str, default: str | None = None) -> str | None:
    """Lê uma variável de ambiente, com default opcional."""
    return os.getenv(nome, default)


def get_secret(nome: str, obrigatorio: bool = True) -> str | None:
    """Lê um segredo/variável sensível do ambiente.

    Se ``obrigatorio=True`` (default) e a variável não existir, levanta
    ``RuntimeError`` com instruções de configuração. Se ``False``, devolve
    ``None``.
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


def resumo() -> str:
    """Resumo legível do estado do ambiente."""
    linhas = [
        ("ROOT_DIR",         ROOT),
        ("ENV",              ENV),
        (".env encontrado?", (ROOT / ".env").exists()),
        ("GITHUB_TOKEN?",    bool(os.getenv("GITHUB_TOKEN"))),
    ]
    return "\n".join(f"{nome:18s}= {valor}" for nome, valor in linhas)


if __name__ == "__main__":
    carregar_dotenv()
    garantir_diretorios()
    print(resumo())
```

## `src/utils/hashing.py`

- Git: `tracked` · status `clean`
- Size: `891 B` · modified `2026-10-17 19:30 UTC`
- SHA-256: `aa96962d96190d264f1a459148e77cafb11afeb5598f0bc557f8422f797e044f`

```python
"""Hashing de arquivos para verificação de integridade.

Centraliza ``sha256_file``, usado tanto pela resolução de coorte
(``src/data/cohort_source.py``) quanto pela persistência do artefato
supervisionado (``src/data/supervised_artifact.py``).
"""

from __future__ import annotations

import hashlib
from pathlib import Path

__all__ = ["sha256_file"]

_DEFAULT_CHUNK_SIZE = 1024 * 1024


def sha256_file(path: Path, chunk_size: int = _DEFAULT_CHUNK_SIZE) -> str:
    """Calcula SHA-256 de um arquivo sem carregá-lo integralmente em memória.

    Lê em blocos de ``chunk_size`` bytes (default 1 MiB), permitindo
    hashear arquivos grandes com memória constante.
    """
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()
```

## `src/utils/reproducibility.py`

- Git: `tracked` · status `clean`
- Size: `13.1 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `15c5a5196d30fb740693656dc5700fc2ef5b7ff4c1cb9c9e55dd3bf876094064`

```python
"""
Registro de execuções para reprodutibilidade (critério C1).

Cada execução grava em ``outputs/runs/<RUN_ID>/``:

- ``metadata.json`` — tudo estruturado
- ``summary.txt``   — versão legível

Uso::

    from src.utils.reproducibility import Run

    with Run(modelo="logistic", parametros={"C": 1.0}) as r:
        ... treino ...
        r.metrica(auc=0.82, accuracy=0.78)
        r.anotar("split aleatorio estratificado")
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Any, Literal

from src.utils import config as C
from src.utils.storage import read_sha256

RUNS_DIR: Path = C.RUNS_DIR

Status = Literal["success", "error"]
_VERSOES_PACOTES = ("numpy", "pandas", "pyarrow", "scikit-learn", "scipy", "matplotlib", "seaborn")
_DATASET_TAMANHOS = ("n_rows", "train_rows", "valid_rows", "test_rows")


# ---------------------------------------------------------------------------
# Helpers de metadados
# ---------------------------------------------------------------------------

def _agora() -> dict[str, str]:
    utc = datetime.now(timezone.utc)
    return {
        "utc":   utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "local": utc.astimezone().strftime("%Y-%m-%dT%H:%M:%S%z"),
    }


def _coletar_gates() -> dict[str, str]:
    """Estado atual de cada gate em ``supervised.yaml`` como ``{nome: status}``."""
    gates = C.cfg("gates") or {}
    return {nome: (info or {}).get("status", "desconhecido") for nome, info in gates.items()}


def _versoes() -> dict[str, str | None]:
    """Versões das bibliotecas fundamentais e do Python."""
    resultado: dict[str, str | None] = {"python": platform.python_version()}
    for pacote in _VERSOES_PACOTES:
        try:
            resultado[pacote] = metadata.version(pacote)
        except metadata.PackageNotFoundError:
            resultado[pacote] = None
    return resultado


def _run_git(args: list[str]) -> str | None:
    """Corre ``git args`` em ``C.ROOT_DIR``; devolve stdout ou ``None``."""
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=C.ROOT_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError:
        return None
    return proc.stdout.strip() if proc.returncode == 0 else None


def _git_info() -> dict[str, str | bool | None]:
    """Commit, branch e estado da árvore de trabalho."""
    status = _run_git(["status", "--porcelain"])
    return {
        "commit": _run_git(["rev-parse", "HEAD"]),
        "branch": _run_git(["branch", "--show-current"]),
        "dirty":  bool(status) if status is not None else None,
    }


def _env_info() -> dict[str, str | bool]:
    """Informações não sensíveis do ambiente."""
    return {
        "python_executable": sys.executable,
        "python_version":    platform.python_version(),
        "platform":          platform.platform(),
        "cwd":               str(Path.cwd()),
        "ci":                bool(os.getenv("CI") or os.getenv("GITHUB_ACTIONS")),
    }


def _resolver_dataset_sha256(
    dataset_sha256: str | None,
    dataset_path: Path | None,
) -> str | None:
    """SHA-256 do dataset por prioridade: explícito > sidecar > ``None``.

    O sidecar é ``<dataset_path>.sha256`` (ver ``src.utils.storage``).
    """
    if dataset_sha256:
        return dataset_sha256
    if dataset_path is None:
        return None
    try:
        return read_sha256(Path(dataset_path))
    except OSError:
        return None


# ---------------------------------------------------------------------------
# summary.txt
# ---------------------------------------------------------------------------

def _bloco(titulo: str, itens: dict[str, Any], largura: int = 20) -> list[str]:
    """``titulo`` seguido de ``k: v`` alinhados — devolve linhas já vazias acima."""
    linhas = ["", f"{titulo}:"]
    for k, v in itens.items():
        if isinstance(v, float):
            linhas.append(f"  {k:{largura}s} {v:.4f}")
        else:
            linhas.append(f"  {k:{largura}s} {v}")
    return linhas


def _resumo(meta: dict[str, Any]) -> str:
    """``summary.txt`` curto e legível a partir do metadata."""
    linhas = [
        f"RUN_ID:   {meta['run_id']}",
        f"MODELO:   {meta['modelo']}",
        f"SEED:     {meta['seed']}",
        f"STATUS:   {meta.get('status', 'desconhecido')}",
    ]

    if meta.get("data_version"):
        linhas.append(f"DADOS:    {meta['data_version']}")
    if meta.get("dataset_sha256"):
        linhas.append(f"SHA-256:  {meta['dataset_sha256']}")

    ds = meta.get("dataset") or {}
    for k in _DATASET_TAMANHOS:
        if k in ds:
            linhas.append(f"{k.upper():10s} {ds[k]:,}")

    if meta.get("duracao_s") is not None:
        linhas.append(f"DURACAO:  {meta['duracao_s']:.1f}s")

    if meta.get("erro"):
        err = meta["erro"]
        linhas += ["", "ERRO:",
                   f"  tipo:     {err.get('tipo')}",
                   f"  mensagem: {err.get('mensagem')}"]

    if meta.get("metricas"):
        linhas += _bloco("MÉTRICAS", meta["metricas"])

    if meta.get("parametros"):
        linhas += _bloco("PARÂMETROS", meta["parametros"])

    if meta.get("gates"):
        linhas += _bloco("GATES", meta["gates"], largura=34)

    if meta.get("notas"):
        linhas += ["", f"NOTAS: {meta['notas']}"]

    linhas += ["", f"TIMESTAMP_UTC: {meta['timestamp']['utc']}"]
    return "\n".join(linhas) + "\n"


# ---------------------------------------------------------------------------
# API pública: gerar, registar, listar, carregar
# ---------------------------------------------------------------------------

def gerar_run_id(
    modelo: str | None = None,
    base_dir: Path | None = None,
) -> str:
    """Identificador único ``YYYY-MM-DD_HHMMSS_micros[_modelo]``.

    Com ``base_dir``, acrescenta sufixo ``_NN`` em caso de colisão no
    sistema de arquivos.
    """
    candidato = datetime.now().strftime("%Y-%m-%d_%H%M%S_%f")
    if modelo:
        candidato = f"{candidato}_{modelo}"
    if base_dir is None:
        return candidato

    base = Path(base_dir)
    run_id, contador = candidato, 1
    while (base / run_id).exists():
        run_id = f"{candidato}_{contador:02d}"
        contador += 1
    return run_id


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
    status: Status = "success",
    erro: dict[str, Any] | None = None,
    dataset_sha256: str | None = None,
) -> Path:
    """Grava ``metadata.json`` + ``summary.txt`` em ``outputs/runs/<RUN_ID>/``.

    ``status='error'`` deve vir acompanhado de ``erro`` (dict com ``tipo``,
    ``mensagem`` e opcionalmente ``traceback``). ``dataset_sha256=None``
    deixa a chave ausente do metadata.
    """
    base = Path(output_dir) if output_dir is not None else RUNS_DIR
    if run_id is None:
        run_id = gerar_run_id(modelo=modelo, base_dir=base)

    pasta = base / run_id
    pasta.mkdir(parents=True, exist_ok=False)

    meta: dict[str, Any] = {
        "run_id":         pasta.name,
        "timestamp":      _agora(),
        "modelo":         modelo,
        "seed":           seed if seed is not None else C.SEED,
        "status":         status,
        "erro":           erro,
        "duracao_s":      duracao_s,
        "parametros":     parametros or {},
        "dataset":        dataset or {},
        "dataset_sha256": dataset_sha256,
        "data_version":   C.DATA_VERSION,
        "features":       features or {},
        "metricas":       metricas or {},
        "gates":          _coletar_gates(),
        "notas":          notas,
        "versoes":        _versoes(),
        "git":            _git_info(),
        "env":            _env_info(),
        "supervised_yaml_sha256": C.supervised_yaml_sha256(),
    }

    (pasta / "metadata.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    (pasta / "summary.txt").write_text(_resumo(meta), encoding="utf-8")

    print(f"[reproducibility] run registrado em: {pasta}")
    return pasta


def listar_runs(output_dir: Path | None = None) -> list[dict[str, Any]]:
    """Metadados das execuções registadas, ordenados por ``run_id`` decrescente.

    Cada item inclui ``"pasta"`` com o caminho absoluto.
    """
    raiz = Path(output_dir) if output_dir is not None else RUNS_DIR
    if not raiz.exists():
        return []

    runs: list[dict[str, Any]] = []
    for pasta in raiz.iterdir():
        if not pasta.is_dir():
            continue
        meta_path = pasta / "metadata.json"
        if not meta_path.exists():
            continue
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        meta["pasta"] = str(pasta)
        runs.append(meta)

    return sorted(runs, key=lambda m: str(m.get("run_id", "")), reverse=True)


def carregar_run(
    run: str | Path,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Carrega o ``metadata.json`` de uma execução."""
    caminho = Path(run)
    if not caminho.is_absolute():
        caminho = (Path(output_dir) if output_dir else RUNS_DIR) / caminho

    meta_path = caminho / "metadata.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"metadata.json não encontrado em {caminho}")
    return json.loads(meta_path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------

class Run:
    """Context manager de registo de execução.

    O metadata é gravado sempre ao sair do bloco, inclusive em caso de
    excepção (com ``status="error"`` e ``erro`` estruturado). A excepção
    não é suprimida — ``__exit__`` devolve ``False``.
    """

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
        dataset_path: Path | None = None,
        dataset_sha256: str | None = None,
    ) -> None:
        self.modelo         = modelo
        self.seed           = seed
        self.parametros     = dict(parametros or {})
        self.dataset        = dict(dataset or {})
        self.features       = dict(features or {})
        self.notas          = notas
        self.output_dir     = output_dir
        self.dataset_path   = dataset_path
        self.dataset_sha256 = dataset_sha256
        self._metricas: dict[str, Any] = {}
        self._inicio: float | None = None
        self.pasta: Path | None = None

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

        if exc_type is None:
            status: Status = "success"
            erro: dict[str, Any] | None = None
        else:
            status = "error"
            erro = {
                "tipo":      exc_type.__name__,
                "modulo":    getattr(exc_type, "__module__", None),
                "mensagem":  str(exc) if exc is not None else None,
                "traceback": (
                    "".join(traceback.format_exception(exc_type, exc, tb))
                    if tb is not None else None
                ),
            }

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
            status=status,
            erro=erro,
            dataset_sha256=_resolver_dataset_sha256(self.dataset_sha256, self.dataset_path),
        )
        return False
```

## `src/utils/storage.py`

- Git: `tracked` · status `clean`
- Size: `8.8 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `05b2bbcc41102e5028f55a7cc665d49df4b25eca58f050f77a004b74e20dc724`

```python
"""
Contrato oficial de acesso ao Parquet de SRAG.

Fluxo: ``GitHub Release → data/processed/<DATA_VERSION>/srag.parquet``.

Tenta o download público via release; se falhar e houver ``GITHUB_TOKEN``,
usa o asset privado via API do GitHub. Grava um sidecar ``<arquivo>.sha256``
para reprodutibilidade. ``force=True`` rebaixa e descarta o sidecar antigo.
"""

from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Iterable

import pandas as pd
import requests

from src.utils import config as C
from src.utils.env import PROCESSED, get_secret


PARQUET_MAGIC: bytes = b"PAR1"
_CHUNK: int = 8 * 1024 * 1024


def _token() -> str | None:
    """``GITHUB_TOKEN`` se definido; caso contrário, ``None``."""
    return get_secret("GITHUB_TOKEN", obrigatorio=False)


def sha256_path(parquet_path: Path) -> Path:
    """Caminho do sidecar ``.sha256`` associado a um Parquet."""
    return parquet_path.with_suffix(parquet_path.suffix + ".sha256")


def read_sha256(parquet_path: Path) -> str | None:
    """Lê o SHA-256 do sidecar, ou ``None`` se ele não existir."""
    sidecar = sha256_path(parquet_path)
    if not sidecar.exists():
        return None
    linha = sidecar.read_text(encoding="utf-8").strip()
    return linha.split()[0] if linha else None


def _abrir_stream(
    url: str,
    *,
    headers: dict[str, str] | None,
    tentativas: int,
    backoff: float,
    timeout: float,
) -> requests.Response:
    """Abre um stream HTTP com retry linear.

    4xx permanente (exceto 429) falha sem retentar. 5xx, 429 e erros de
    conexão são retentados até ``tentativas`` vezes, com espera
    ``backoff * tentativa`` entre elas.
    """
    last_exc: Exception | None = None

    for tentativa in range(1, tentativas + 1):
        try:
            r = requests.get(
                url,
                headers=headers or {},
                stream=True,
                timeout=timeout,
                allow_redirects=True,
            )
        except requests.RequestException as exc:
            last_exc = exc
            if tentativa < tentativas:
                time.sleep(backoff * tentativa)
            continue

        if r.ok:
            return r

        # 4xx permanente (excepto 429): falha sem retentar.
        if 400 <= r.status_code < 500 and r.status_code != 429:
            r.close()
            r.raise_for_status()

        status = r.status_code
        r.close()
        last_exc = requests.HTTPError(f"HTTP {status} em {url}")
        if tentativa < tentativas:
            time.sleep(backoff * tentativa)

    if last_exc is None:
        raise RuntimeError(f"Nenhuma tentativa executada para {url}")
    raise last_exc


def _baixar_para_part(
    r: requests.Response,
    tmp: Path,
) -> tuple[str, bytes]:
    """Streama ``r`` para ``tmp``; devolve ``(sha256_hex, primeiros_16_bytes)``.

    Imprime progresso quando o servidor declara ``content-length``.
    """
    h = hashlib.sha256()
    first = b""
    total = int(r.headers.get("content-length", 0))
    done = 0

    with open(tmp, "wb") as f:
        for chunk in r.iter_content(_CHUNK):
            if not chunk:
                continue
            if not first:
                first = chunk[:16]
            f.write(chunk)
            h.update(chunk)
            done += len(chunk)
            if total:
                print(
                    f"\rBaixando: {done / 1e6:.0f}/{total / 1e6:.0f} MB",
                    end="",
                    flush=True,
                )

    if total:
        print()
    return h.hexdigest(), first


def download_file(
    url: str,
    dest: Path,
    *,
    headers: dict[str, str] | None = None,
    expected_magic: bytes | None = None,
    expected_sha256: str | None = None,
) -> str:
    """Baixa ``url`` para ``dest`` com verificação de magic bytes e SHA-256.

    Retorna o SHA-256 hex e grava o sidecar ``<dest>.sha256``. O download
    passa por ``<dest>.part``, removido em qualquer falha. Levanta
    ``RuntimeError`` se o content-type indicar HTML/JSON, se o magic não
    bater ou se o SHA-256 divergir.
    """
    tmp = dest.with_suffix(dest.suffix + ".part")
    tmp.unlink(missing_ok=True)

    r = _abrir_stream(
        url,
        headers=headers,
        tentativas=C.HTTP_TENTATIVAS,
        backoff=C.HTTP_BACKOFF,
        timeout=C.HTTP_TIMEOUT,
    )
    try:
        ctype = r.headers.get("content-type", "").lower()
        if "text/html" in ctype or "application/json" in ctype:
            preview = next(r.iter_content(256), b"")
            raise RuntimeError(
                f"Download retornou {ctype!r} em vez de binário. "
                f"URL: {url}\nPrimeiros bytes: {preview[:80]!r}"
            )
        digest, first_bytes = _baixar_para_part(r, tmp)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
    finally:
        r.close()

    if expected_magic and not first_bytes.startswith(expected_magic):
        tmp.unlink(missing_ok=True)
        raise RuntimeError(
            f"Arquivo baixado não é válido. Esperado começar com "
            f"{expected_magic!r}, recebido {first_bytes!r}. URL: {url}"
        )

    if expected_sha256 and digest.lower() != expected_sha256.lower():
        tmp.unlink(missing_ok=True)
        raise RuntimeError(
            f"SHA-256 divergente para {url}.\n"
            f"  esperado: {expected_sha256}\n"
            f"  obtido:   {digest}"
        )

    tmp.replace(dest)
    sha256_path(dest).write_text(f"{digest}  {dest.name}\n", encoding="utf-8")
    return digest


def _private_asset_url(token: str) -> str:
    """URL do asset Parquet via API do GitHub (repositório privado)."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    url = (
        f"https://api.github.com/repos/{C.GITHUB_REPO}/releases/tags/"
        f"{C.DATA_VERSION}"
    )
    r = requests.get(url, headers=headers, timeout=C.HTTP_TIMEOUT)
    r.raise_for_status()

    assets = r.json().get("assets", [])
    asset = next((a for a in assets if a["name"] == C.PARQUET_NAME), None)
    if asset is None:
        nomes = [a["name"] for a in assets]
        raise RuntimeError(
            f"Asset {C.PARQUET_NAME!r} não encontrado na release "
            f"{C.DATA_VERSION!r}. Disponíveis: {nomes}"
        )
    return asset["url"]


def get_parquet(
    force: bool = False,
    *,
    expected_sha256: str | None = None,
) -> Path:
    """Devolve o caminho local do Parquet de SRAG, baixando se necessário.

    Ordem: release pública; se falhar e ``GITHUB_TOKEN`` estiver definido,
    asset privado via API. ``force=True`` rebaixa mesmo que o arquivo
    exista e descarta o sidecar antigo. ``expected_sha256`` valida o hash
    do arquivo baixado.

    Efeito colateral: Parquet gravado em
    ``data/processed/<DATA_VERSION>/<PARQUET_NAME>``, sidecar ``.sha256``
    ao lado, e SHA-256 impresso no stdout.
    """
    folder = PROCESSED / C.DATA_VERSION
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / C.PARQUET_NAME

    if path.exists() and not force:
        return path

    if force and path.exists():
        path.unlink()
        sha256_path(path).unlink(missing_ok=True)

    public_url = (
        f"https://github.com/{C.GITHUB_REPO}/releases/download/"
        f"{C.DATA_VERSION}/{C.PARQUET_NAME}"
    )

    try:
        digest = download_file(
            public_url,
            path,
            expected_magic=PARQUET_MAGIC,
            expected_sha256=expected_sha256,
        )
    except (requests.HTTPError, RuntimeError):
        token = _token()
        if not token:
            raise RuntimeError(
                "Download falhou. Repositório privado ou asset inválido? "
                "Cadastre o segredo GITHUB_TOKEN."
            )
        digest = download_file(
            _private_asset_url(token),
            path,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/octet-stream",
            },
            expected_magic=PARQUET_MAGIC,
            expected_sha256=expected_sha256,
        )

    print(f"[storage] SHA-256: {digest}")
    return path


def read_srag(
    columns: Iterable[str] | None = None,
    filters: list[tuple] | None = None,
) -> pd.DataFrame:
    """Lê o Parquet de SRAG como DataFrame.

    ``columns`` restringe o subconjunto carregado (pushdown do Parquet);
    ``filters`` segue o formato de ``pd.read_parquet(filters=...)``.
    """
    return pd.read_parquet(
        get_parquet(),
        columns=list(columns) if columns is not None else None,
        filters=filters,
    )
```

## `tests/conftest.py`

- Git: `tracked` · status `clean`
- Size: `639 B` · modified `2026-10-17 19:30 UTC`
- SHA-256: `d09e0a36c305a02829b974b59774ccf94a97163357a9f419d17ec98e22a5d549`

```python
"""Fixtures partilhadas entre testes."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.utils import config as C


@pytest.fixture(scope="session")
def parquet_disponivel() -> Path | None:
    """Parquet processado, ou ``None`` se ainda não foi gerado.

    Fixture de sessão — o path é calculado uma vez por execução. Testes
    que dependem dela devem fazer ``pytest.skip()`` quando o retorno é
    ``None`` (o Parquet não vem versionado no Git).
    """
    caminho = C.PROCESSED_DIR / C.DATA_VERSION / C.PARQUET_NAME
    return caminho if caminho.is_file() else None
```

## `tests/test_calibration.py`

- Git: `tracked` · status `clean`
- Size: `3.5 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `993b7617cdacd34f6659bdf2b40134f6a21a79b3af9fc7c9d12c44a642bfeca5`

```python
"""Testes de calibração e escolha de limiar."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

from src.models.calibration import calibrar, escolher_limiar


@pytest.fixture
def dados_limiar() -> tuple[np.ndarray, np.ndarray]:
    """10 amostras balanceadas — y_true binário, y_prob em [0, 1]."""
    y = np.array([0, 0, 1, 1, 1, 0, 1, 0, 1, 1])
    p = np.array([0.1, 0.2, 0.8, 0.9, 0.6, 0.3, 0.7, 0.4, 0.85, 0.75])
    return y, p


@pytest.fixture
def modelo_ajustado() -> tuple[LogisticRegression, pd.DataFrame, pd.Series]:
    """``LogisticRegression`` ajustado em ``X`` 1D sintético com sinal.

    Fixture separada (não por teste) para que múltiplos testes de calibração
    reutilizem o mesmo modelo — o objecto é imutável após ``fit``.
    """
    pytest.importorskip("sklearn.frozen")
    rng = np.random.RandomState(0)
    X = pd.DataFrame({"a": rng.randn(200)})
    y = pd.Series((X["a"] + rng.randn(200) * 0.1 > 0).astype(int))
    return LogisticRegression().fit(X, y), X, y


# ---------------------------------------------------------------------------
# escolher_limiar
# ---------------------------------------------------------------------------

def test_escolher_limiar_retorna_dict(dados_limiar):
    y, p = dados_limiar
    r = escolher_limiar(y, p, metrica="f1")
    assert {"limiar", "valor", "metrica", "auc", "brier", "tabela"} <= set(r)
    assert r["metrica"] == "f1"
    assert 0 < r["limiar"] < 1


def test_escolher_limiar_metrica_invalida(dados_limiar):
    y, p = dados_limiar
    # Metrica não existe no Literal — passagem intencional de valor inválido.
    with pytest.raises(ValueError, match="metrica inválida"):
        escolher_limiar(y, p, metrica="nao_existe")  # type: ignore[arg-type]


def test_escolher_limiar_min_precision_respeitado():
    y = np.array([0, 0, 1, 1])
    p = np.array([0.1, 0.2, 0.8, 0.9])
    r = escolher_limiar(y, p, metrica="recall", min_precision=0.9)
    linha = r["tabela"][r["tabela"]["limiar"] == r["limiar"]]
    assert linha["precision"].iloc[0] >= 0.9


def test_escolher_limiar_min_precision_impossivel():
    y = np.array([1, 0, 0, 0])
    p = np.array([0.1, 0.9, 0.8, 0.85])
    with pytest.raises(ValueError, match="precision"):
        escolher_limiar(y, p, min_precision=0.5)


# ---------------------------------------------------------------------------
# calibrar
# ---------------------------------------------------------------------------

def test_calibrar_metodo_invalido(modelo_ajustado):
    modelo, X, y = modelo_ajustado
    with pytest.raises(ValueError, match="method inválido"):
        calibrar(modelo, X, y, method="nao_existe")  # type: ignore[arg-type]


def test_calibrar_sigmoid_preserva_shape(modelo_ajustado):
    modelo, X, y = modelo_ajustado
    cal = calibrar(modelo, X, y, method="sigmoid")
    proba = cal.predict_proba(X)
    assert proba.shape == (len(X), 2)
    assert np.allclose(proba.sum(axis=1), 1.0)
    assert np.all((proba >= 0) & (proba <= 1))


def test_calibrar_isotonic_preserva_shape():
    pytest.importorskip("sklearn.frozen")
    rng = np.random.RandomState(1)
    X = pd.DataFrame({"a": rng.randn(500)})
    y = pd.Series((X["a"] > 0).astype(int))
    modelo = LogisticRegression().fit(X, y)

    cal = calibrar(modelo, X, y, method="isotonic")
    assert cal.predict_proba(X).shape == (len(X), 2)
```

## `tests/test_cohort_source.py`

- Git: `tracked` · status `clean`
- Size: `2.1 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `81aae255c95584ea1c6178160a6e4b8a19fd4d8833ff17fa29bc4ec9b22c67e4`

```python
"""Testes do resolvedor de coorte (provisória, final, auto)."""

from pathlib import Path

import pandas as pd
import pytest

from src.data.cohort_source import cohort_candidates, load_cohort, resolve_cohort_path


@pytest.fixture(autouse=True)
def _sem_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    """Limpa ``SRAG_COHORT_KIND`` do ambiente antes de cada teste.

    Sem isto, um ``SRAG_COHORT_KIND`` definido no shell do runner
    tornaria os testes dependentes do estado local.
    """
    monkeypatch.delenv("SRAG_COHORT_KIND", raising=False)


def _write(path: Path, value: int) -> None:
    """Grava um Parquet 1×1 com uma única coluna ``value``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"value": [value]}).to_parquet(path, index=False)


def test_padrao_permanece_provisorio(tmp_path: Path) -> None:
    paths = cohort_candidates(tmp_path)
    _write(paths["provisional"][1], 1)   # coorte_provisoria_b.parquet
    _write(paths["final"][0], 2)         # coorte_final.parquet (existe, mas não é o default)

    kind, path = resolve_cohort_path(tmp_path)

    assert kind == "provisional"
    assert path.name == "coorte_provisoria_b.parquet"


def test_final_exige_escolha_explicita(tmp_path: Path) -> None:
    path = cohort_candidates(tmp_path)["final"][0]
    _write(path, 2)

    frame, source = load_cohort(tmp_path, kind="final")

    assert frame["value"].tolist() == [2]
    assert source.kind == "final"
    assert source.rows == 1
    assert len(source.sha256) == 64


def test_auto_prefere_final(tmp_path: Path) -> None:
    paths = cohort_candidates(tmp_path)
    _write(paths["provisional"][0], 1)
    _write(paths["final"][0], 2)

    kind, path = resolve_cohort_path(tmp_path, kind="auto")

    assert kind == "final"
    assert path.name == "coorte_final.parquet"


def test_tipo_invalido_falha(tmp_path: Path) -> None:
    # Valor viola intencionalmente o Literal CohortKind.
    with pytest.raises(ValueError, match="provisional, final ou auto"):
        resolve_cohort_path(tmp_path, kind="desconhecida")  # type: ignore[arg-type]
```

## `tests/test_config.py`

- Git: `tracked` · status `clean`
- Size: `7.4 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `e9d6278318474900c708013ab29c1eaa30ed96c935b7a320868c01924ef7c5ca`

```python
"""Integridade do ambiente e da configuração do projeto."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.utils import config as C
from src.utils import env


def _url_parquet_esperada() -> str:
    """URL canônica do Parquet na release pública."""
    return (
        f"https://github.com/{C.GITHUB_REPO}/releases/download/"
        f"{C.DATA_VERSION}/{C.PARQUET_NAME}"
    )


# ---------------------------------------------------------------------------
# Raiz e diretórios
# ---------------------------------------------------------------------------

def test_root_dir_existe() -> None:
    assert C.ROOT_DIR.exists()
    assert C.ROOT_DIR.is_dir()


def test_root_dir_calculado_a_partir_do_arquivo() -> None:
    """``ROOT_DIR`` deriva de ``config.py`` (dois níveis acima: ``src/utils/``)."""
    assert C.ROOT_DIR == Path(C.__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "chave",
    ["DATA_DIR", "RAW_DIR", "PROCESSED_DIR", "REPORTS_DIR", "MODELS_DIR"],
)
def test_diretorios_derivam_da_raiz(chave: str) -> None:
    """Diretórios públicos derivam de ``ROOT_DIR``.

    O clone pode estar em ``C:/Users`` ou ``OneDrive`` — o que não pode
    é o caminho estar literalmente gravado em ``config.py``.
    """
    valor = getattr(C, chave)
    assert isinstance(valor, Path)
    assert valor.is_absolute()
    assert C.ROOT_DIR in valor.parents, f"{chave}={valor} não deriva de {C.ROOT_DIR}"


# ---------------------------------------------------------------------------
# Sem caminhos pessoais hardcoded
# ---------------------------------------------------------------------------

def _encontrar_caminhos_hardcoded(fonte: str, nomes_de_caminho: set[str]) -> list[dict]:
    """Inspeciona atribuições de ``nomes_de_caminho`` à procura de caminhos pessoais.

    Só atribuições são olhadas — comentários, docstrings e mensagens podem
    mencionar ``C:/Users`` ou ``/home`` sem serem configuração real.
    """
    proibidos = ("c:/users/", "/home/", "/users/")
    problemas: list[dict] = []

    for no in ast.walk(ast.parse(fonte)):
        if isinstance(no, ast.Assign) and len(no.targets) == 1:
            alvo, valor = no.targets[0], no.value
        elif isinstance(no, ast.AnnAssign):
            alvo, valor = no.target, no.value
        else:
            continue

        if valor is None or not isinstance(alvo, ast.Name) or alvo.id not in nomes_de_caminho:
            continue

        for item in ast.walk(valor):
            if not isinstance(item, ast.Constant) or not isinstance(item.value, str):
                continue
            texto = item.value.replace("\\", "/").lower()
            if termos := [t for t in proibidos if t in texto]:
                problemas.append({"constante": alvo.id, "valor": item.value, "termos": termos})

    return problemas


def test_config_nao_contem_caminho_pessoal_hardcoded() -> None:
    """Nenhuma constante de caminho em ``config.py`` tem caminho pessoal literal."""
    nomes_de_caminho = {
        "ROOT_DIR", "DATA_DIR", "RAW_DIR", "PROCESSED_DIR",
        "TREINO_DIR", "CONFIGS_DIR", "MODELS_DIR", "OUTPUTS_DIR",
        "RUNS_DIR", "LOGS_DIR", "REPORTS_DIR", "FIGURES_DIR",
        "TABLES_DIR", "PREDICTIONS_DIR", "SUPERVISED_YAML",
    }
    fonte = Path(C.__file__).read_text(encoding="utf-8")

    problemas = _encontrar_caminhos_hardcoded(fonte, nomes_de_caminho)
    assert not problemas, f"Caminhos pessoais hardcoded em constantes: {problemas}"


# ---------------------------------------------------------------------------
# Seed, versão e HTTP
# ---------------------------------------------------------------------------

def test_seed_definido() -> None:
    assert isinstance(C.SEED, int)
    assert C.SEED == 42


def test_random_state_igual_ao_seed() -> None:
    assert C.RANDOM_STATE == C.SEED


def test_repo_definido() -> None:
    assert C.GITHUB_REPO and "/" in C.GITHUB_REPO


def test_data_version_e_parquet_definidos() -> None:
    assert C.DATA_VERSION
    assert C.PARQUET_NAME.endswith(".parquet")


def test_parametros_http_razoaveis() -> None:
    assert C.HTTP_TIMEOUT > 0
    assert C.HTTP_TENTATIVAS >= 1
    assert C.HTTP_BACKOFF >= 0


# ---------------------------------------------------------------------------
# URL do Parquet — prioridade da variável de ambiente
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "valor_env, esperado_override",
    [
        (None, False),
        ("https://example.org/dados/srag_teste.parquet", True),
        ("   ", False),
    ],
    ids=["sem_env", "env_customizada", "env_vazia"],
)
def test_srag_parquet_url(valor_env, esperado_override, monkeypatch: pytest.MonkeyPatch) -> None:
    """``SRAG_PARQUET_URL`` sobrepõe a URL padrão; vazia cai no padrão."""
    if valor_env is None:
        monkeypatch.delenv("SRAG_PARQUET_URL", raising=False)
    else:
        monkeypatch.setenv("SRAG_PARQUET_URL", valor_env)

    url = C.srag_parquet_url()
    if esperado_override:
        assert valor_env is not None
        assert url == valor_env.strip()
    else:
        assert url == _url_parquet_esperada()


# ---------------------------------------------------------------------------
# env.py
# ---------------------------------------------------------------------------

def test_env_aponta_para_mesma_raiz() -> None:
    assert env.ROOT == C.ROOT_DIR


def test_env_diretorios_padrao_existem() -> None:
    env.garantir_diretorios()
    for caminho in (env.RAW, env.PROCESSED, env.TREINO, env.FIGURES):
        assert caminho.is_dir(), f"{caminho} não é diretório após garantir_diretorios()"


def test_env_resumo_nao_quebra() -> None:
    texto = env.resumo()
    assert "ROOT_DIR" in texto
    assert "ENV" in texto


def test_get_secret_obrigatorio_levanta_erro(monkeypatch: pytest.MonkeyPatch) -> None:
    nome = "VAR_QUE_NAO_EXISTE_XYZ"
    monkeypatch.delenv(nome, raising=False)
    with pytest.raises(RuntimeError, match=nome):
        env.get_secret(nome)


def test_get_secret_opcional_retorna_none(monkeypatch: pytest.MonkeyPatch) -> None:
    nome = "VAR_OPCIONAL_XYZ"
    monkeypatch.delenv(nome, raising=False)
    assert env.get_secret(nome, obrigatorio=False) is None


# ---------------------------------------------------------------------------
# Schema do Parquet (slow)
# ---------------------------------------------------------------------------

@pytest.mark.slow
def test_features_finais_existem_no_schema(parquet_disponivel) -> None:
    """Colunas do ``supervised.yaml`` existem no Parquet (ou são derivadas).

    Features derivadas (produzidas por ``montar_features``) não existem no
    Parquet bruto — excluídas da checagem. As colunas de entrada exigidas
    pela derivação são verificadas explicitamente.
    """
    if parquet_disponivel is None:
        pytest.skip("Parquet não disponível.")

    import pyarrow.parquet as pq
    from src.models import pipeline

    colunas = set(pq.read_schema(parquet_disponivel).names)
    derivadas = set(C.cfg("features", "engenharia", "derivadas") or [])
    entradas = set(C.cfg("features", "engenharia", "entradas") or [])
    base = set(pipeline.FEATURES) - derivadas

    faltando = (base | entradas) - colunas
    assert not faltando, f"Colunas ausentes no Parquet: {sorted(faltando)}"
```

## `tests/test_errors.py`

- Git: `tracked` · status `clean`
- Size: `5.5 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `7c4362c964cc4035939c32264b33a4e27cff1abf1cb40979616c1e8b55479164`

```python
"""Testes de análise de erros em ``src.evaluation.errors``."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.evaluation.errors import (
    extrair_falsos_negativos,
    extrair_falsos_positivos,
    matriz_confusao,
    metricas_por_grupo,
    top_erros,
)


@pytest.fixture
def y_true_y_pred() -> tuple[np.ndarray, np.ndarray]:
    """8 amostras com falsos positivos e negativos plantados.

    Labels (não probabilidades) — para ``top_erros``, cada teste constrói
    os seus próprios dados.
    """
    y_true = np.array([0, 0, 1, 1, 0, 1, 0, 1])
    y_pred = np.array([0, 1, 1, 0, 0, 1, 1, 1])
    return y_true, y_pred


def _df_com_indice(n: int) -> pd.DataFrame:
    """DataFrame ``{"x": range(n)}`` — índice rastreável nos testes de extração."""
    return pd.DataFrame({"x": range(n)})


# ---------------------------------------------------------------------------
# matriz_confusao
# ---------------------------------------------------------------------------

def test_matriz_confusao_shape_e_valores(y_true_y_pred) -> None:
    y_true, y_pred = y_true_y_pred
    m = matriz_confusao(y_true, y_pred)
    assert {"pred_0", "pred_1"}.issubset(m.columns)
    assert {"real_0", "real_1"}.issubset(m.index)
    assert m.loc["real_0", "pred_1"] == 2
    assert m.loc["real_1", "pred_0"] == 1


def test_matriz_confusao_tem_totais(y_true_y_pred) -> None:
    y_true, y_pred = y_true_y_pred
    m = matriz_confusao(y_true, y_pred)
    assert "total" in m.columns
    assert "total" in m.index
    assert m.loc["total", "total"] == len(y_true)


# ---------------------------------------------------------------------------
# extrair_falsos_*
# ---------------------------------------------------------------------------

def test_extrair_fp(y_true_y_pred) -> None:
    y_true, y_pred = y_true_y_pred
    fp = extrair_falsos_positivos(_df_com_indice(len(y_true)), y_true, y_pred)
    assert len(fp) == 2
    assert set(fp["x"]) == {1, 6}


def test_extrair_fn(y_true_y_pred) -> None:
    y_true, y_pred = y_true_y_pred
    fn = extrair_falsos_negativos(_df_com_indice(len(y_true)), y_true, y_pred)
    assert len(fn) == 1
    assert fn["x"].iloc[0] == 3


# ---------------------------------------------------------------------------
# metricas_por_grupo
# ---------------------------------------------------------------------------

def test_metricas_por_grupo_coluna_renomeada() -> None:
    """A coluna de prevalência chama-se ``taxa_positivos``, não ``positivos``."""
    n = 300
    df = pd.DataFrame({"grupo": ["A"] * n + ["B"] * n})
    y = pd.Series(np.tile([0, 1], n))
    p = pd.Series(np.tile([0.1, 0.9], n))

    r = metricas_por_grupo(df, y, p, "grupo", min_n=10)
    assert "taxa_positivos" in r.columns
    assert "positivos" not in r.columns


def test_metricas_por_grupo_ignora_abaixo_de_min_n() -> None:
    """Grupo com menos de ``min_n`` é excluído do resultado."""
    df = pd.DataFrame({"grupo": ["A"] * 5 + ["B"] * 300})
    y = pd.Series([0, 1] * 152 + [0])
    p = pd.Series([0.1, 0.9] * 152 + [0.5])

    r = metricas_por_grupo(df, y, p, "grupo", min_n=30)
    assert set(r["grupo"]) == {"B"}
    assert r.loc[r["grupo"] == "B", "n"].iloc[0] == 300


def test_metricas_por_grupo_coluna_ausente() -> None:
    df = pd.DataFrame({"outra": [1, 2]})
    with pytest.raises(KeyError):
        metricas_por_grupo(df, np.array([0, 1]), np.array([0.1, 0.9]), "grupo")


def test_metricas_por_grupo_tamanho_incompativel() -> None:
    """``df`` (5 linhas) com ``y`` (6 linhas) deve falhar antes de agregar."""
    df = pd.DataFrame({"grupo": ["A"] * 5})
    y = np.array([0, 1, 0, 1, 0, 1])
    p = np.array([0.1, 0.9, 0.2, 0.8, 0.3, 0.7])
    with pytest.raises(ValueError):
        metricas_por_grupo(df, y, p, "grupo")


# ---------------------------------------------------------------------------
# top_erros
# ---------------------------------------------------------------------------

def test_top_erros_erro_absoluto() -> None:
    """Adiciona ``y_true``, ``y_prob``, ``y_pred``, ``erro_abs`` ao DataFrame."""
    df = pd.DataFrame({"x": range(6)})
    y_true = np.array([0, 0, 1, 1, 0, 1])
    y_prob = np.array([0.1, 0.9, 0.1, 0.9, 0.5, 0.5])

    t = top_erros(df, y_true, y_prob, n=3, criterio="erro_absoluto")
    assert len(t) == 3
    for c in ("y_true", "y_prob", "y_pred", "erro_abs"):
        assert c in t.columns


def test_top_erros_fp_ordena_por_prob_decrescente() -> None:
    df = pd.DataFrame({"x": range(5)})
    y_true = np.array([0, 0, 1, 1, 0])
    y_prob = np.array([0.1, 0.9, 0.1, 0.9, 0.6])

    t = top_erros(df, y_true, y_prob, n=5, criterio="fp")
    assert (t["y_true"] == 0).all()
    assert (t["y_pred"] == 1).all()
    assert t["y_prob"].is_monotonic_decreasing


def test_top_erros_fn_ordena_por_prob_crescente() -> None:
    df = pd.DataFrame({"x": range(5)})
    y_true = np.array([0, 0, 1, 1, 1])
    y_prob = np.array([0.1, 0.9, 0.1, 0.4, 0.9])

    t = top_erros(df, y_true, y_prob, n=5, criterio="fn")
    assert (t["y_true"] == 1).all()
    assert (t["y_pred"] == 0).all()
    assert t["y_prob"].is_monotonic_increasing


def test_top_erros_criterio_invalido() -> None:
    df = pd.DataFrame({"x": [1, 2]})
    # Valor viola intencionalmente o Literal CriterioTop.
    with pytest.raises(ValueError, match="criterio inválido"):
        top_erros(df, np.array([0, 1]), np.array([0.1, 0.9]), criterio="xxx")  # type: ignore[arg-type]
```

## `tests/test_features.py`

- Git: `tracked` · status `clean`
- Size: `11.3 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `db4f5e070d3e0bc1ea7298a41d48a9628bc341d91ea8da80359c8444981dcfe0`

```python
"""
Testes de engenharia de atributos (``src/features/engineering.py``).

Cobre funções puras e o orquestrador ``montar_features``: contrato de
cada derivada, casos inválidos, não-mutação da entrada e invariantes de
ponto-no-tempo. Não testa parsing do YAML.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.features.engineering import (
    ano_mes_internacao,
    faixa_etaria,
    idade_em_anos,
    intervalo_sintomas_internacao,
    montar_features,
    sazonalidade,
    sexo_categoria,
)


# Conjunto mínimo de entradas exigido por ``montar_features``, alinhado
# com ``features.engenharia.entradas`` do supervised.yaml.
ENTRADAS_OBRIGATORIAS: tuple[str, ...] = (
    "nu_idade_n",
    "tp_idade",
    "cs_sexo",
    "dt_sin_pri",
    "dt_interna",
)

# Derivadas que ``montar_features`` deve produzir. Deliberadamente
# hardcoded (não importado de engineering) para travar mudanças
# silenciosas no contrato.
COLUNAS_DERIVADAS_ESPERADAS: frozenset[str] = frozenset({
    "idade_anos",
    "dias_sintomas_ate_internacao",
    "flag_intervalo_invalido",
    "flag_internacao_antes_sintomas",
    "sin_semana",
    "cos_semana",
    "faixa_etaria",
    "sexo_categoria",
    "ano_internacao",
    "mes_internacao",
})


@pytest.fixture
def df_base() -> pd.DataFrame:
    """DataFrame mínimo com as colunas exigidas por ``montar_features``.

    Linhas:

    - 0: adulto (30a), 4 dias até internação, M
    - 1: bebé (6 meses), 5 dias, F
    - 2: adulto (40a), 5 dias, sexo ignorado
    - 3: recém-nascido (1 dia), 5 dias, M
    """
    return pd.DataFrame({
        "nu_idade_n": [30, 6, 40, 1],
        "tp_idade":   [3, 2, 3, 1],
        "cs_sexo":    ["M", "F", "I", "M"],
        "dt_sin_pri": ["2024-01-01", "2024-03-15", "2024-06-20", "2024-09-05"],
        "dt_interna": ["2024-01-05", "2024-03-20", "2024-06-25", "2024-09-10"],
    })


class TestIdadeEmAnos:
    def test_anos_direto(self, df_base: pd.DataFrame) -> None:
        assert idade_em_anos(df_base).iloc[0] == pytest.approx(30.0)

    def test_meses_convertidos(self, df_base: pd.DataFrame) -> None:
        assert idade_em_anos(df_base).iloc[1] == pytest.approx(0.5)

    def test_dias_convertidos(self, df_base: pd.DataFrame) -> None:
        assert idade_em_anos(df_base).iloc[3] == pytest.approx(1 / 365.25)

    def test_retorna_float64(self, df_base: pd.DataFrame) -> None:
        assert idade_em_anos(df_base).dtype == np.float64

    def test_tipo_invalido_vira_nan(self) -> None:
        df = pd.DataFrame({"nu_idade_n": [10], "tp_idade": [9]})
        assert pd.isna(idade_em_anos(df)).all()

    def test_idade_negativa_vira_nan(self) -> None:
        df = pd.DataFrame({"nu_idade_n": [-1], "tp_idade": [3]})
        assert pd.isna(idade_em_anos(df)).all()

    def test_idade_acima_de_120_vira_nan(self) -> None:
        df = pd.DataFrame({"nu_idade_n": [200], "tp_idade": [3]})
        assert pd.isna(idade_em_anos(df)).all()

    def test_nao_muta_entrada(self, df_base: pd.DataFrame) -> None:
        antes = df_base.copy(deep=True)
        idade_em_anos(df_base)
        pd.testing.assert_frame_equal(df_base, antes)


class TestIntervaloSintomasInternacao:
    def test_intervalo_positivo(self, df_base: pd.DataFrame) -> None:
        out = intervalo_sintomas_internacao(df_base)
        assert out["dias_sintomas_ate_internacao"].iloc[0] == pytest.approx(4.0)

    def test_tipos_das_colunas(self, df_base: pd.DataFrame) -> None:
        out = intervalo_sintomas_internacao(df_base)
        assert out["dias_sintomas_ate_internacao"].dtype == np.float64
        assert out["flag_intervalo_invalido"].dtype == np.int8
        assert out["flag_internacao_antes_sintomas"].dtype == np.int8

    def test_negativo_seta_ambas_flags(self) -> None:
        df = pd.DataFrame({"dt_sin_pri": ["2024-01-10"], "dt_interna": ["2024-01-05"]})
        out = intervalo_sintomas_internacao(df)
        assert out["flag_internacao_antes_sintomas"].iloc[0] == 1
        assert out["flag_intervalo_invalido"].iloc[0] == 1

    def test_acima_do_limite_seta_flag_umbrella_sem_marcar_sinal(self) -> None:
        df = pd.DataFrame({"dt_sin_pri": ["2024-01-01"], "dt_interna": ["2024-06-01"]})
        out = intervalo_sintomas_internacao(df)
        assert out["flag_intervalo_invalido"].iloc[0] == 1
        assert out["flag_internacao_antes_sintomas"].iloc[0] == 0

    def test_data_ausente_seta_flag_umbrella(self) -> None:
        df = pd.DataFrame({"dt_sin_pri": [None], "dt_interna": ["2024-01-05"]})
        out = intervalo_sintomas_internacao(df)
        assert pd.isna(out["dias_sintomas_ate_internacao"].iloc[0])
        assert out["flag_intervalo_invalido"].iloc[0] == 1

    def test_politica_sinalizar_mantem_valor_bruto(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Default: valor inválido fica visível, comunicado por flags."""
        df = pd.DataFrame({"dt_sin_pri": ["2024-01-10"], "dt_interna": ["2024-01-05"]})
        monkeypatch.setattr(
            "src.features.engineering._intervalo_politica",
            lambda: "sinalizar",
        )
        out = intervalo_sintomas_internacao(df)
        assert out["dias_sintomas_ate_internacao"].iloc[0] == pytest.approx(-5.0)

    def test_politica_descartar_substitui_por_nan(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        df = pd.DataFrame({"dt_sin_pri": ["2024-01-10"], "dt_interna": ["2024-01-05"]})
        monkeypatch.setattr(
            "src.features.engineering._intervalo_politica",
            lambda: "descartar",
        )
        out = intervalo_sintomas_internacao(df)
        assert pd.isna(out["dias_sintomas_ate_internacao"].iloc[0])
        assert out["flag_intervalo_invalido"].iloc[0] == 1


class TestSazonalidade:
    def test_gera_sin_e_cos_no_intervalo(self, df_base: pd.DataFrame) -> None:
        out = sazonalidade(df_base)
        assert set(out.columns) == {"sin_semana", "cos_semana"}
        for col in out.columns:
            assert out[col].between(-1.0, 1.0, inclusive="both").all()

    def test_mesma_semana_em_anos_diferentes_proxima(self) -> None:
        df = pd.DataFrame({"dt_sin_pri": ["2023-03-15", "2024-03-13"]})  # mesma semana ISO
        out = sazonalidade(df)
        assert abs(out["sin_semana"].iloc[0] - out["sin_semana"].iloc[1]) < 0.1
        assert abs(out["cos_semana"].iloc[0] - out["cos_semana"].iloc[1]) < 0.1

    def test_data_nula_vira_nan(self) -> None:
        out = sazonalidade(pd.DataFrame({"dt_sin_pri": [None]}))
        assert pd.isna(out["sin_semana"].iloc[0])
        assert pd.isna(out["cos_semana"].iloc[0])

    def test_coluna_ausente_levanta_keyerror(self) -> None:
        df = pd.DataFrame({"outra_data": ["2024-01-01"]})
        with pytest.raises(KeyError, match="Coluna temporal ausente"):
            sazonalidade(df, coluna_data="dt_sin_pri")


class TestFaixaEtaria:
    def test_fronteiras_semiabertas(self) -> None:
        out = faixa_etaria(pd.Series([0.0, 0.99, 1.0, 4.99, 5.0, 80.0, 120.0]))
        assert list(out) == ["<1", "<1", "1-4", "1-4", "5-11", "80+", "80+"]

    def test_idade_nula_vira_desconhecida(self) -> None:
        out = faixa_etaria(pd.Series([np.nan, 30.0]))
        assert out.iloc[0] == "desconhecida"
        assert out.iloc[1] == "18-39"

    def test_retorna_categoria(self) -> None:
        assert isinstance(faixa_etaria(pd.Series([30.0])).dtype, pd.CategoricalDtype)


class TestSexoCategoria:
    @pytest.mark.parametrize(
        "entrada, esperado",
        [
            ("M",     "masculino"),
            ("f",     "feminino"),
            (" I ",   "ignorado"),
            ("X",     "ausente"),
            (None,    "ausente"),
        ],
    )
    def test_mapeamento(self, entrada: str | None, esperado: str) -> None:
        df = pd.DataFrame({"cs_sexo": [entrada]})
        assert sexo_categoria(df).iloc[0] == esperado

    def test_retorna_categoria(self) -> None:
        df = pd.DataFrame({"cs_sexo": ["M"]})
        assert isinstance(sexo_categoria(df).dtype, pd.CategoricalDtype)


class TestAnoMesInternacao:
    def test_extrai_ano_e_mes(self, df_base: pd.DataFrame) -> None:
        out = ano_mes_internacao(df_base)
        assert out["ano_internacao"].tolist() == [2024.0] * 4
        assert out["mes_internacao"].tolist() == [1.0, 3.0, 6.0, 9.0]

    def test_data_nula_vira_nan(self) -> None:
        out = ano_mes_internacao(pd.DataFrame({"dt_interna": [None]}))
        assert pd.isna(out["ano_internacao"].iloc[0])
        assert pd.isna(out["mes_internacao"].iloc[0])


class TestMontarFeatures:
    def test_gera_todas_as_derivadas_do_yaml(self, df_base: pd.DataFrame) -> None:
        """Trava o contrato entre ``features.engenharia.derivadas`` e a função."""
        faltando = COLUNAS_DERIVADAS_ESPERADAS - set(montar_features(df_base).columns)
        assert not faltando, f"Derivadas ausentes: {sorted(faltando)}"

    def test_nao_muta_entrada(self, df_base: pd.DataFrame) -> None:
        antes = df_base.copy(deep=True)
        montar_features(df_base)
        pd.testing.assert_frame_equal(df_base, antes)

    def test_preserva_colunas_originais(self, df_base: pd.DataFrame) -> None:
        out = montar_features(df_base)
        assert set(df_base.columns).issubset(out.columns)

    def test_nao_gera_colunas_proibidas(self, df_base: pd.DataFrame) -> None:
        proibidas = {"evolucao", "alvo_obito_srag", "dt_evoluca", "uti", "cluster"}
        assert proibidas.isdisjoint(montar_features(df_base).columns)


class TestPontoNoTempo:
    """Invariantes contra vazamento temporal — o ponto de previsão é a admissão."""

    def test_so_precisa_das_entradas_declaradas(self, df_base: pd.DataFrame) -> None:
        """Um df com só as entradas declaradas deve bastar para as derivadas."""
        out = montar_features(df_base[list(ENTRADAS_OBRIGATORIAS)].copy())
        assert COLUNAS_DERIVADAS_ESPERADAS.issubset(out.columns)

    def test_colunas_pos_admissao_nao_influenciam(self, df_base: pd.DataFrame) -> None:
        """Injetar colunas pós-alta não pode alterar a saída."""
        baseline = montar_features(df_base)

        df_contaminado = df_base.copy()
        df_contaminado["evolucao"]  = [1.0, 2.0, 1.0, 2.0]
        df_contaminado["dt_evoluca"] = pd.to_datetime(
            ["2024-02-01", "2024-04-01", "2024-07-01", "2024-10-01"]
        )
        df_contaminado["uti"]        = [0, 1, 0, 1]
        df_contaminado["suport_ven"] = [0, 1, 0, 0]

        contaminado = montar_features(df_contaminado)

        pd.testing.assert_frame_equal(
            baseline[list(COLUNAS_DERIVADAS_ESPERADAS)].reset_index(drop=True),
            contaminado[list(COLUNAS_DERIVADAS_ESPERADAS)].reset_index(drop=True),
        )

    def test_ordem_das_linhas_nao_altera_derivadas(self, df_base: pd.DataFrame) -> None:
        """Derivadas são pointwise — sem dependência de ordem."""
        normal    = montar_features(df_base)
        invertido = montar_features(df_base.iloc[::-1].reset_index(drop=True))

        pd.testing.assert_frame_equal(
            normal[list(COLUNAS_DERIVADAS_ESPERADAS)].reset_index(drop=True),
            invertido[list(COLUNAS_DERIVADAS_ESPERADAS)].iloc[::-1].reset_index(drop=True),
        )
```

## `tests/test_leakage.py`

- Git: `tracked` · status `clean`
- Size: `3.9 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `122506d41aa18213123b6ed3ddddcd38f68b16d69a8448e540708ef0d89a55f8`

```python
"""
Testes anti-vazamento de dados.

Cobrem:

- consistência entre ``features.proibidas`` e ``pipeline.FEATURES``;
- proibição do alvo nas features;
- contrato de ``check_leakage`` (coluna proibida, alvo, lista vazia);
- duplicidade de identificadores no Parquet (slow).
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.evaluation.leakage import LeakageError, check_leakage
from src.utils import config as C


# ---------------------------------------------------------------------------
# Contrato de configuração (features.proibidas ↔ FEATURES)
# ---------------------------------------------------------------------------

@pytest.fixture
def proibidas() -> set[str]:
    """Conjunto ``features.proibidas`` do ``supervised.yaml``."""
    return set(C.cfg("features", "proibidas") or [])


@pytest.fixture
def features_finais() -> set[str]:
    """``pipeline.FEATURES`` — features efetivamente usadas pelo modelo."""
    from src.models import pipeline
    return set(pipeline.FEATURES)


def test_proibidas_nao_vazia(proibidas: set[str]) -> None:
    assert proibidas


def test_alvo_esta_entre_proibidas(proibidas: set[str]) -> None:
    assert C.cfg("target", "coluna") in proibidas


def test_features_finais_sem_proibidas(
    features_finais: set[str],
    proibidas: set[str],
) -> None:
    vazamento = features_finais & proibidas
    assert not vazamento, f"FEATURES contém colunas proibidas: {sorted(vazamento)}"


def test_features_finais_nao_inclui_alvo(features_finais: set[str]) -> None:
    assert C.cfg("target", "coluna") not in features_finais


# ---------------------------------------------------------------------------
# Contrato de check_leakage
# ---------------------------------------------------------------------------

def test_check_leakage_passa_com_X_limpo() -> None:
    X = pd.DataFrame({"feat_a": [1, 2, 3], "feat_b": [4, 5, 6]})
    check_leakage(X)


def test_check_leakage_levanta_para_proibida(proibidas: set[str]) -> None:
    coluna = sorted(proibidas)[0]
    X = pd.DataFrame({coluna: [1, 2, 3], "feat_ok": [4, 5, 6]})

    with pytest.raises(LeakageError) as exc:
        check_leakage(X)

    assert coluna in str(exc.value)


def test_check_leakage_levanta_para_alvo() -> None:
    alvo = C.cfg("target", "coluna")
    X = pd.DataFrame({alvo: [0, 1, 0], "feat_ok": [1, 2, 3]})

    with pytest.raises(LeakageError):
        check_leakage(X)


def test_check_leakage_lista_vazia_ainda_verifica_alvo() -> None:
    """``forbidden_columns=[]`` ainda soma ``DEFAULT_LEAKAGE_COLUMNS`` + alvo."""
    alvo = C.cfg("target", "coluna")
    X = pd.DataFrame({alvo: [0, 1, 0], "feat_ok": [1, 2, 3]})

    with pytest.raises(LeakageError):
        check_leakage(X, forbidden_columns=[])


# ---------------------------------------------------------------------------
# Identificadores no Parquet (slow)
# ---------------------------------------------------------------------------

@pytest.mark.slow
def test_dataset_sem_identificadores_duplicados(parquet_disponivel) -> None:
    """Taxa de ``nu_notific`` (ou equivalente) duplicado deve ser < 5%."""
    if parquet_disponivel is None:
        pytest.skip("Parquet não disponível.")

    import pyarrow.parquet as pq

    colunas = set(pq.read_schema(parquet_disponivel).names)
    candidatas = ("nu_notific", "numero_notificacao", "id_notificacao", "id")
    coluna_id = next((c for c in candidatas if c in colunas), None)

    if coluna_id is None:
        pytest.skip("Sem coluna identificadora adequada.")

    df = pd.read_parquet(parquet_disponivel, columns=[coluna_id])
    ids = df[coluna_id].dropna().astype("string").str.strip()
    ids = ids[ids.ne("")]

    if ids.empty:
        pytest.skip(f"Coluna {coluna_id} sem identificadores válidos.")

    taxa = int(ids.duplicated().sum()) / len(ids)
    assert taxa < 0.05, f"Taxa alta de duplicados em {coluna_id}: {taxa:.1%}"
```

## `tests/test_metrics.py`

- Git: `tracked` · status `clean`
- Size: `5.5 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `1251e53dbcb79353e211e590d332539869bb13d1671fa69eaf4ca35e892eb370`

```python
"""Testes das métricas em ``src.evaluation.metrics``."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.evaluation.metrics import (
    accuracy,
    auc,
    average_precision,
    brier,
    f1,
    ic_bootstrap,
    metricas_completas,
    metricas_por_limiar,
    precision,
    recall,
)


@pytest.fixture
def y_true() -> np.ndarray:
    """10 rótulos binários — 6 positivos (1), 4 negativos (0)."""
    return np.array([0, 0, 1, 1, 1, 0, 1, 0, 1, 1])


@pytest.fixture
def y_prob() -> np.ndarray:
    """10 probabilidades em ``[0, 1]`` correlacionadas com ``y_true``."""
    return np.array([0.1, 0.2, 0.8, 0.9, 0.6, 0.3, 0.7, 0.4, 0.85, 0.75])


# Chaves contratuais de ``metricas_completas`` — a lista serve como
# armadilha contra remoções silenciosas no módulo fonte.
_CHAVES_METRICAS_COMPLETAS = (
    "auc", "ap", "brier", "f1", "precision", "recall",
    "accuracy", "limiar", "n",
)


# ---------------------------------------------------------------------------
# AUC
# ---------------------------------------------------------------------------

def test_auc_perfeito() -> None:
    """Classificador com separação perfeita → AUC = 1.0."""
    y = np.array([0, 0, 1, 1])
    p = np.array([0.1, 0.2, 0.8, 0.9])
    assert auc(y, p) == pytest.approx(1.0)


def test_auc_constante_e_meio() -> None:
    """Probabilidades constantes → AUC = 0.5 por construção."""
    y = np.array([0, 0, 1, 1])
    p = np.array([0.5, 0.5, 0.5, 0.5])
    assert auc(y, p) == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# Métricas de probabilidade (aceitam y_prob)
# ---------------------------------------------------------------------------

def test_metricas_individuais_retornam_float(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> None:
    for fn in (auc, average_precision, brier):
        assert isinstance(fn(y_true, y_prob), float)


def test_average_precision_em_intervalo(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> None:
    assert 0.0 <= average_precision(y_true, y_prob) <= 1.0


def test_brier_em_intervalo(y_true: np.ndarray, y_prob: np.ndarray) -> None:
    assert 0.0 <= brier(y_true, y_prob) <= 1.0


# ---------------------------------------------------------------------------
# Métricas de classificação (aceitam y_pred duro)
# ---------------------------------------------------------------------------

def test_f1_precision_recall(y_true: np.ndarray) -> None:
    y_pred = np.array([0, 0, 1, 1, 1, 0, 0, 0, 1, 1])
    for fn in (f1, precision, recall):
        v = fn(y_true, y_pred)
        assert isinstance(v, float)
        assert 0.0 <= v <= 1.0


def test_accuracy_perfeita() -> None:
    y = np.array([0, 1, 0, 1])
    assert accuracy(y, y) == pytest.approx(1.0)


def test_zero_division_nao_quebra() -> None:
    """``y_true`` e ``y_pred`` sem positivos → métricas devolvem 0.0, não ``ZeroDivisionError``."""
    y_true = np.zeros(3, dtype=int)
    y_pred = np.zeros(3, dtype=int)
    assert f1(y_true, y_pred) == 0.0
    assert precision(y_true, y_pred) == 0.0
    assert recall(y_true, y_pred) == 0.0


# ---------------------------------------------------------------------------
# metricas_completas
# ---------------------------------------------------------------------------

def test_metricas_completas_chaves(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> None:
    d = metricas_completas(y_true, y_prob, limiar=0.5)
    for k in _CHAVES_METRICAS_COMPLETAS:
        assert k in d
    assert d["limiar"] == 0.5
    assert d["n"] == float(len(y_true))


def test_metricas_completas_aceita_series(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> None:
    """``metricas_completas`` deve aceitar ``pd.Series`` como entrada."""
    d = metricas_completas(pd.Series(y_true), pd.Series(y_prob))
    assert "auc" in d


# ---------------------------------------------------------------------------
# metricas_por_limiar
# ---------------------------------------------------------------------------

def test_metricas_por_limiar(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> None:
    t = metricas_por_limiar(y_true, y_prob, n_limiares=11)
    assert {"limiar", "f1", "precision", "recall", "accuracy"}.issubset(t.columns)
    assert len(t) == 11
    assert (t["limiar"] > 0).all()
    assert (t["limiar"] < 1).all()


# ---------------------------------------------------------------------------
# ic_bootstrap
# ---------------------------------------------------------------------------

def test_ic_bootstrap_retorna_tres_floats(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> None:
    est, inf, sup = ic_bootstrap(y_true, y_prob, n_boot=50, seed=42)
    assert isinstance(est, float)
    assert isinstance(inf, float)
    assert isinstance(sup, float)
    assert inf <= sup


def test_ic_bootstrap_deterministico(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> None:
    """Mesma seed → mesmo resultado."""
    a = ic_bootstrap(y_true, y_prob, n_boot=50, seed=42)
    b = ic_bootstrap(y_true, y_prob, n_boot=50, seed=42)
    assert a == b


def test_ic_bootstrap_metrica_customizada(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> None:
    est, inf, sup = ic_bootstrap(
        y_true,
        y_prob,
        metrica=average_precision,
        n_boot=30,
        seed=1,
    )
    assert inf <= est <= sup
```

## `tests/test_model_pipelines.py`

- Git: `tracked` · status `clean`
- Size: `6.2 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `5dd0bbc04fc6c0033ae84664fc9de929d70e6c05a8ca0c4f89ccdd5b8c581af6`

```python
"""
Testes rápidos dos construtores de pipeline de modelos supervisionados.

Cobrem baseline, logística e boosting. Não dependem do Parquet nem fazem
I/O pesado. As features vêm de ``src.models.pipeline`` (que lê o
``supervised.yaml``) — sem hard-code.
"""

from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd
import pytest
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from src.models import pipeline as P
from src.models.baseline import build_baseline_pipeline
from src.models.boosting import build_boosting_pipeline
from src.models.logistic import build_logistic_pipeline
from src.utils import config as C


def _df_features(
    n: int = 200,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.Series]:
    """DataFrame sintético com exactamente as features exigidas pelo YAML.

    Numéricas com distribuição normal; categóricas com 3 níveis como
    strings. O alvo é balanceado 50/50 e depois embaralhado — garante as
    duas classes para ``DummyClassifier(strategy="prior")`` e para
    ``LogisticRegression(class_weight="balanced")``.
    """
    rng = np.random.default_rng(seed)
    dados: dict[str, np.ndarray] = {}

    for coluna in P.FEATURES_NUMERICAS:
        dados[coluna] = rng.normal(loc=50.0, scale=15.0, size=n)
    for coluna in P.FEATURES_CATEGORICAS:
        dados[coluna] = rng.choice(["0", "1", "2"], size=n)

    X = pd.DataFrame(dados)
    y = pd.Series(
        np.concatenate([np.zeros(n // 2, dtype=int), np.ones(n - n // 2, dtype=int)]),
        name="alvo",
    ).sample(frac=1, random_state=seed).reset_index(drop=True)

    return X, y


def _colunas_do_pre(pipe: Pipeline) -> set[str]:
    """Colunas declaradas no ``ColumnTransformer`` do pipeline.

    ``ColumnTransformer.transformers`` é uma lista de
    ``(nome, transformer, colunas)`` — extraímos a terceira posição.
    """
    colunas: set[str] = set()
    for _, _, cols in pipe.named_steps["pre"].transformers:
        if isinstance(cols, list):
            colunas.update(cols)
    return colunas


# `max_iter` reduzido para manter os testes rápidos — smoke de fit, não tuning.
_CONSTRUTORES: list[tuple[str, Callable[[], Pipeline], type]] = [
    ("baseline", lambda: build_baseline_pipeline(), DummyClassifier),
    ("logistic", lambda: build_logistic_pipeline(max_iter=500), LogisticRegression),
    ("boosting", lambda: build_boosting_pipeline(max_iter=30), HistGradientBoostingClassifier),
]

_IDS = [nome for nome, _, _ in _CONSTRUTORES]


# ---------------------------------------------------------------------------
# Contrato do pipeline (estrutura)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(("nome", "ctor", "clf_esperado"), _CONSTRUTORES, ids=_IDS)
def test_pipeline_retorna_pipeline(
    nome: str,
    ctor: Callable[[], Pipeline],
    clf_esperado: type,
) -> None:
    """Cada construtor devolve ``Pipeline(pre, clf)`` com o classificador correto."""
    pipe = ctor()
    assert isinstance(pipe, Pipeline), nome
    assert list(pipe.named_steps.keys()) == ["pre", "clf"], nome
    assert isinstance(pipe.named_steps["clf"], clf_esperado), nome


@pytest.mark.parametrize(("nome", "ctor", "clf_esperado"), _CONSTRUTORES, ids=_IDS)
def test_pipeline_nao_inclui_proibidas(
    nome: str,
    ctor: Callable[[], Pipeline],
    clf_esperado: type,
) -> None:
    proibidas = set(C.cfg("features", "proibidas") or [])
    assert proibidas, (
        "`features.proibidas` está vazio no supervised.yaml — "
        "ao menos o alvo e as colunas posteriores ao desfecho precisam "
        "estar listadas."
    )

    colisoes = _colunas_do_pre(ctor()) & proibidas
    assert not colisoes, (
        f"{nome}: colunas proibidas no pré-processador: {sorted(colisoes)}"
    )


# ---------------------------------------------------------------------------
# Comportamento (fit + predict_proba)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(("nome", "ctor", "clf_esperado"), _CONSTRUTORES, ids=_IDS)
def test_pipeline_fit_predict_proba(
    nome: str,
    ctor: Callable[[], Pipeline],
    clf_esperado: type,
) -> None:
    X, y = _df_features(n=200)
    pipe = ctor().fit(X, y)
    proba = pipe.predict_proba(X)

    assert proba.shape == (len(X), 2), f"{nome}: shape {proba.shape}"
    assert np.isfinite(proba).all(), f"{nome}: probabilidades com NaN/Inf"
    assert ((proba >= 0) & (proba <= 1)).all(), f"{nome}: fora de [0, 1]"
    assert np.allclose(proba.sum(axis=1), 1.0), f"{nome}: linhas não somam 1"


# ---------------------------------------------------------------------------
# Contrato de features
# ---------------------------------------------------------------------------

def test_pipelines_usam_features_do_yaml() -> None:
    """Pré-processador expõe ``FEATURES_NUMERICAS + FEATURES_CATEGORICAS`` do YAML.

    Canário contra features fora do YAML ou filtros silenciosos.
    """
    esperadas = set(P.FEATURES_NUMERICAS) | set(P.FEATURES_CATEGORICAS)
    assert esperadas, "Nenhuma feature declarada em supervised.yaml."

    for nome, ctor, _ in _CONSTRUTORES:
        colunas = _colunas_do_pre(ctor())
        faltando = esperadas - colunas
        extras = colunas - esperadas
        assert colunas == esperadas, (
            f"{nome}: pré-processador divergente do YAML. "
            f"Faltando: {sorted(faltando)}; Extras: {sorted(extras)}"
        )


# ---------------------------------------------------------------------------
# Validação de parâmetros
# ---------------------------------------------------------------------------

def test_logistic_pipeline_solver_invalido() -> None:
    """``l1_ratio=1.0`` (L1 puro) exige ``liblinear`` ou ``saga``.

    Com ``lbfgs`` o construtor deve levantar ``ValueError``.
    """
    with pytest.raises(ValueError, match="combinação inválida"):
        build_logistic_pipeline(l1_ratio=1.0, solver="lbfgs")
```

## `tests/test_pipeline.py`

- Git: `tracked` · status `clean`
- Size: `2.7 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `0b547fc2d43446a0239bbb73659cfcb3cbbb362a90b86f8bf7e73dd7b35cbc00`

```python
"""
Testes do pipeline de ingestão: ``read_srag``, ``get_parquet`` e
``build_pipeline``.

Testes que tocam no Parquet são marcados com ``@pytest.mark.slow``.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.models.pipeline import build_pipeline
from src.utils import env
from src.utils.storage import get_parquet, read_srag


# ---------------------------------------------------------------------------
# Ingestão do Parquet (slow)
# ---------------------------------------------------------------------------

@pytest.mark.slow
def test_read_srag_retorna_dataframe(parquet_disponivel: Path | None) -> None:
    if parquet_disponivel is None:
        pytest.skip("Parquet não disponível.")

    df = read_srag(columns=["sg_uf", "dt_notific"])

    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert {"sg_uf", "dt_notific"}.issubset(set(df.columns))


@pytest.mark.slow
def test_get_parquet_reaproveita_arquivo(parquet_disponivel: Path | None) -> None:
    """``force=False`` reutiliza o arquivo existente (mesmo mtime e tamanho)."""
    if parquet_disponivel is None:
        pytest.skip("Parquet não disponível.")

    caminho_1 = get_parquet(force=False)
    estado_1 = caminho_1.stat()
    caminho_2 = get_parquet(force=False)
    estado_2 = caminho_2.stat()

    assert caminho_1.resolve() == caminho_2.resolve()
    assert estado_1.st_mtime_ns == estado_2.st_mtime_ns
    assert estado_1.st_size == estado_2.st_size


# ---------------------------------------------------------------------------
# build_pipeline
# ---------------------------------------------------------------------------

def test_build_pipeline_falha_feature_ausente() -> None:
    X = pd.DataFrame({"nu_idade_n": [30.0, 40.0, 50.0]})
    with pytest.raises(KeyError, match="ausentes"):
        build_pipeline(X=X)


def test_build_pipeline_strict_false_avisa_mas_continua(
    caplog: pytest.LogCaptureFixture,
) -> None:
    X = pd.DataFrame({"nu_idade_n": [30.0, 40.0, 50.0]})
    with caplog.at_level("WARNING"):
        pipe = build_pipeline(X=X, strict=False)

    assert pipe is not None
    assert "ausentes" in caplog.text.lower()


# ---------------------------------------------------------------------------
# Diretórios padrão
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("nome_dir", ["RAW", "PROCESSED"])
def test_diretorio_padrao_foi_criado(nome_dir: str) -> None:
    """``env.garantir_diretorios`` cria os diretórios esperados."""
    env.garantir_diretorios()
    caminho = getattr(env, nome_dir)
    assert caminho.is_dir(), f"{caminho} não é diretório"
```

## `tests/test_regras_pessoa_a.py`

- Git: `tracked` · status `clean`
- Size: `22.9 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `9b4f7be9ae95ffc9d1af19fd25f5182f4f3c57e8da0ad73e1cdf5aae7d3f74d7`

```python
"""
Testes das regras da Pessoa A (``src.protocolo.verificacoes``).

Cobre A1–A4, casos limite de datas, leitura compacta (colunas
``category``) e o contrato de exportação consumido pelo C2.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.protocolo import verificacoes as v


# ---------------------------------------------------------------------------
# Fixtures e helpers
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def cfg() -> dict:
    return v.load_config(None)


@pytest.fixture(scope="module")
def demo() -> pd.DataFrame:
    return v.prepare(v.make_demo(n=3000)[0])


def _escrever_yaml(
    tmp_path: Path,
    numericas: list[str],
    categoricas: list[str],
    *,
    proibidas: list[str] | None = None,
    grupos: list[str] | None = None,
) -> Path:
    """Escreve ``supervised.yaml`` mínimo para testes de exportação.

    Devolve o ``Path``. Cobre os campos consumidos por ``a1_export_dataset``
    e ``validar_contrato_c2``: alvo, coluna de tempo, features e (opcional)
    grupos de avaliação.
    """
    def lst(items: list[str]) -> str:
        return "[" + ", ".join(items) + "]"

    features = (
        f"{{numericas: {lst(numericas)}, categoricas: {lst(categoricas)}"
        + (f", proibidas: {lst(proibidas)}" if proibidas else "")
        + "}"
    )
    linhas = [
        "target: {coluna: evolucao, positivos: [2.0]}",
        "coluna_tempo: dt_notific",
        f"features: {features}",
    ]
    if grupos:
        linhas.append(f"avaliacao: {{grupos: {lst(grupos)}}}")

    caminho = tmp_path / "supervised.yaml"
    caminho.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return caminho


def _base_texto(n: int = 15_000) -> pd.DataFrame:
    """``make_demo`` com datas como texto ISO e códigos como strings."""
    base = v.make_demo(n=n, inicio="2019-01-01", anos=7)[0]
    base.columns = [c.lower() for c in base.columns]
    for c in ("dt_nasc", "dt_evoluca", "dt_encerra", "dt_sin_pri", "dt_interna", "dt_notific"):
        base[c] = base[c].dt.strftime("%Y-%m-%d")
    for c in ("evolucao", "hospital", "tp_idade"):
        base[c] = base[c].astype("Int64").astype(str).replace("<NA>", None)
    return base


def _como_categoria(df: pd.DataFrame) -> pd.DataFrame:
    """Converte todas as colunas string (excepto ``nu_notific``) em ``category``."""
    d = df.copy()
    for c in d.columns:
        if (d[c].dtype == object or pd.api.types.is_string_dtype(d[c])) and c != "nu_notific":
            d[c] = d[c].astype("category")
    return d


# ---------------------------------------------------------------------------
# A1 — alvo, aliases, datas, waterfall, coorte
# ---------------------------------------------------------------------------

def test_alvo_desconhecido_nao_vira_cura(cfg):
    t = v.make_target(pd.Series(["1", "2", "3", "9", None, "", "x", 1.0, 2.0]), cfg)
    assert list(t.astype("object")) == [0, 1, pd.NA, pd.NA, pd.NA, pd.NA, pd.NA, 0, 1]


def test_aliases_para_nomes_canonicos():
    df = v.prepare(pd.DataFrame({"internado": [1], "dt_encerramento": ["2024-01-01"], "evolucao": [2]}))
    assert {"HOSPITAL", "DT_ENCERRA", "EVOLUCAO"} <= set(df.columns)


def test_parse_date_iso_e_br():
    s = v.parse_date(pd.Series(["2024-03-05", "05/03/2024", "lixo", None]))
    assert s.iloc[0] == s.iloc[1] == pd.Timestamp("2024-03-05")
    assert s.iloc[2:].isna().all()


def test_waterfall_monotonico(cfg, demo, tmp_path):
    rep = v.Report(tmp_path)
    wf = v.a1_waterfall(demo, cfg, rep)
    assert wf["n_restante"].iloc[0] == len(demo)
    assert wf["n_restante"].is_monotonic_decreasing
    assert (wf["n_excluido"].iloc[1:].sum() + wf["n_restante"].iloc[-1]) == len(demo)


def test_coorte_so_tem_cura_ou_obito(cfg, demo):
    c = v.a1_cohort(demo, cfg)
    assert set(c["_alvo"].unique()) <= {0, 1}
    assert set(c["_ano"].unique()) <= set(cfg["dev_years"] + cfg["holdout_years"])


# ---------------------------------------------------------------------------
# A2 — datas absurdas, maturidade, formatos mistos
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("unidade", ["s", "ms", "us", "texto"])
def test_datas_absurdas_nao_estouram(cfg, tmp_path, unidade):
    datas = ["2024-03-05", "0001-01-01", "9999-12-31", "1850-05-05", "2024-01-01"]
    col = (pd.Series(datas) if unidade == "texto"
           else pd.Series(np.array(datas, dtype=f"datetime64[{unidade}]")))
    outra = pd.Series(["2024-03-01"] * 5) if unidade == "texto" else pd.Series(
        np.array(["2024-03-01"] * 5, dtype=f"datetime64[{unidade}]"))
    d = v.parse_date(col)
    assert d.isna().tolist() == [False, True, True, True, False]
    df = pd.DataFrame({"DT_NASC": col, "DT_SIN_PRI": outra, "DT_NOTIFIC": outra, "DT_INTERNA": col,
                       "DT_EVOLUCA": col, "DT_ENCERRA": outra, "HOSPITAL": 1, "EVOLUCAO": 1,
                       "TP_IDADE": 3, "NU_IDADE_N": 40, "NU_NOTIFIC": "1"})
    rep = v.Report(tmp_path)
    v.a2_dates(df, cfg, rep)      # não pode levantar OverflowError
    v.a2_maturity(df, cfg, rep)


def test_parse_date_formatos_mistos_e_ano_absurdo():
    s = v.parse_date(pd.Series(["2022-03-05", "05/03/2022", "05/03/2022 00:00:00", "2022/03/05", "2224-01-01", "lixo"]))
    assert s.iloc[:4].eq(pd.Timestamp("2022-03-05")).all()
    assert s.iloc[4:].isna().all()


def test_parse_date_categorica_igual_a_texto():
    s = pd.Series(["2022-03-05", "05/03/2022", None, "9999-12-31", "lixo", "2022-03-05"] * 50)
    a = v.parse_date(s)
    b = v.parse_date(s.astype("category"))
    assert a.isna().tolist() == b.isna().tolist()
    assert a.dropna().tolist() == b.dropna().tolist()


# ---------------------------------------------------------------------------
# A3 — auditoria de config e deteção de vazamento
# ---------------------------------------------------------------------------

def test_variavel_proibida_gera_falha(cfg, tmp_path):
    rep = v.Report(tmp_path)
    v.a3_forbidden(["NU_IDADE_N", "DT_EVOLUCA"], "supervisionado", cfg, rep)
    assert rep.has_failure


def test_evolucao_no_clustering_gera_falha(cfg, tmp_path):
    rep = v.Report(tmp_path)
    v.a3_forbidden(["EVOLUCAO", "FEBRE"], "clustering", cfg, rep)
    assert rep.has_failure


def test_auditoria_supervised_aponta_fracao_e_dt_notific(cfg, tmp_path):
    y = {"target": {"positivos": [2.0], "descartar_ignorado": True}, "coluna_tempo": "dt_notific",
         "temporal": {"modo": "fracao"}, "features": {"numericas": ["nu_idade_n"], "categoricas": ["febre"]}}
    rep = v.Report(tmp_path)
    v.a3_config_audit(y, cfg, rep)
    checks = {f[1]: f[2] for f in rep.findings}
    assert checks["Coluna temporal"] == v.WARN
    assert checks["Split temporal"] == v.WARN
    assert checks["Alvo: evolucao=3 e ausente"] == v.WARN
    assert checks["Idade"] == v.WARN


def test_auditoria_yaml_contra_schema_fisico(cfg, tmp_path):
    schema = ["nu_notific", "hospital", "evolucao", "dt_evoluca", "dt_encerra", "cs_gestant", "nu_idade_n", "febre"]
    y = {"target": {"positivos": [2.0]}, "coluna_tempo": "dt_notific", "temporal": {"modo": "fracao"},
         "features": {"numericas": ["nu_idade_n"], "categoricas": ["tp_gestante", "internado", "febre"],
                      "proibidas": ["evolucao", "dt_evolucao", "dt_encerramento"]}}
    rep = v.Report(tmp_path)
    v.a3_config_audit(y, cfg, rep, schema)
    achados = {f[1]: f for f in rep.findings}
    f1 = achados["Features do YAML x Parquet"]
    assert f1[2] == v.FAIL and "tp_gestante" in f1[3] and "internado->hospital" in f1[3]
    f2 = achados["`proibidas` do YAML x Parquet"]
    assert f2[2] == v.WARN and "dt_evolucao->dt_evoluca" in f2[3] and "dt_encerramento->dt_encerra" in f2[3]


def test_auditoria_nao_acusa_derivadas_como_ausentes(cfg, tmp_path):
    y = {"target": {"positivos": [2.0]}, "coluna_tempo": "dt_notific", "temporal": {"modo": "fracao"},
         "features": {"numericas": ["nu_idade_n", "idade_anos", "sin_semana"], "categoricas": ["faixa_etaria", "febre"],
                      "proibidas": ["evolucao"]}}
    rep = v.Report(tmp_path)
    v.a3_config_audit(y, cfg, rep, ["nu_idade_n", "febre", "evolucao", "dt_notific"])
    achados = {f[1]: f[2] for f in rep.findings}
    assert achados["Features do YAML x Parquet"] == v.OK
    assert achados["Features derivadas do YAML"] == v.OK


# ---------------------------------------------------------------------------
# A1 — exportação do dataset analítico
# ---------------------------------------------------------------------------

def test_exporta_dataset_para_o_c2(cfg, tmp_path):
    base = v.make_demo(n=3000)[0]
    base.columns = [c.lower() for c in base.columns]
    base = base.rename(columns={"hospital": "internado"})
    df = v.prepare(base)

    y = _escrever_yaml(tmp_path, ["nu_idade_n"], ["febre", "internado"])
    out = tmp_path / "dataset_supervisionado.csv"
    meta = v.a1_export_dataset(df, cfg, v.Report(tmp_path), y, path=out)

    d = pd.read_csv(out)
    assert {"evolucao", "dt_notific", "nu_idade_n", "febre", "internado"} <= set(d.columns)
    assert set(d["evolucao"].unique()) <= {1, 2}
    assert d["dt_notific"].is_monotonic_increasing
    assert "dt_evoluca" not in d.columns and meta["n_linhas"] == len(d)


def test_export_cria_derivadas_pedidas_pelo_yaml(cfg, tmp_path):
    base = v.make_demo(n=3000)[0]
    base.columns = [c.lower() for c in base.columns]

    y = _escrever_yaml(
        tmp_path,
        ["nu_idade_n", "idade_anos", "intervalo_sint_interna_dias",
         "flag_intervalo_invalido", "sin_semana", "cos_semana"],
        ["febre", "faixa_etaria"],
        proibidas=["evolucao", "dt_evoluca"],
        grupos=["cs_sexo", "faixa_etaria"],
    )
    out = tmp_path / "d.csv"
    meta = v.a1_export_dataset(v.prepare(base), cfg, v.Report(tmp_path), y, path=out)

    d = pd.read_csv(out)
    for col in ("idade_anos", "intervalo_sint_interna_dias", "flag_intervalo_invalido",
                "sin_semana", "cos_semana", "faixa_etaria", "cs_sexo"):
        assert col in d.columns, col
    assert meta["features_ausentes_na_base"] == []

    rep = v.Report(tmp_path, "c")
    assert v.validar_contrato_c2(out, y, rep) is True


def test_find_base_ignora_dataset_analitico(tmp_path):
    (tmp_path / "data" / "analytical").mkdir(parents=True)
    (tmp_path / "data" / "raw").mkdir(parents=True)
    (tmp_path / "data" / "analytical" / "dataset_supervisionado.parquet").write_bytes(b"x")
    (tmp_path / "data" / "raw" / "srag.csv").write_text("a\n1\n")
    base_encontrada = v.find_base(tmp_path)
    assert base_encontrada is not None
    assert base_encontrada.name == "srag.csv"


def test_contrato_c2_dataset_valido(cfg, tmp_path):
    base = v.make_demo(n=3000)[0]
    base.columns = [c.lower() for c in base.columns]

    y = _escrever_yaml(tmp_path, ["nu_idade_n"], ["febre", "dispneia"],
                       proibidas=["evolucao", "dt_evoluca"])
    out = tmp_path / "dataset_supervisionado.csv"
    meta = v.a1_export_dataset(v.prepare(base), cfg, v.Report(tmp_path), y, path=out)

    rep = v.Report(tmp_path, "contrato")
    assert v.validar_contrato_c2(out, y, rep) is True
    assert meta["descartadas_data_tempo_invalida"] >= 0
    assert not rep.has_failure


def test_contrato_c2_feature_inexistente_e_proibida_falham(cfg, tmp_path):
    base = v.make_demo(n=2000)[0]
    base.columns = [c.lower() for c in base.columns]

    # Feature inexistente na base (tp_gestante)
    y = _escrever_yaml(tmp_path, ["nu_idade_n"], ["febre", "tp_gestante"],
                       proibidas=["evolucao", "dt_evoluca"])
    out = tmp_path / "d.csv"
    v.a1_export_dataset(v.prepare(base), cfg, v.Report(tmp_path), y, path=out)

    rep = v.Report(tmp_path, "c1")
    assert v.validar_contrato_c2(out, y, rep) is False
    assert any(f[1] == "Colunas exigidas pelo C2" and f[2] == v.FAIL for f in rep.findings)

    # Feature proibida no X (evolucao)
    y2 = _escrever_yaml(tmp_path, ["nu_idade_n"], ["febre", "evolucao"],
                        proibidas=["evolucao", "dt_evoluca"])
    rep2 = v.Report(tmp_path, "c2")
    v.validar_contrato_c2(out, y2, rep2)
    assert any(f[1].startswith("check_leakage") and f[2] == v.FAIL for f in rep2.findings)


# ---------------------------------------------------------------------------
# Features derivadas
# ---------------------------------------------------------------------------

def test_features_derivadas_valores(cfg):
    df = pd.DataFrame({
        "NU_IDADE_N": [40, 24, 365, 150, 30, 5],
        "TP_IDADE": [3, 2, 1, 3, 3, 3],                       # anos, meses, dias, anos(absurdo), anos, anos
        "DT_SIN_PRI": ["2024-01-01", "2024-01-10", "2024-01-10", "2024-01-01", None, "2024-01-01"],
        "DT_INTERNA": ["2024-01-03", "2024-01-05", "2024-01-20", "2024-03-01", "2024-01-03", "2024-01-08"],
    })
    criadas = v.add_derived(df, cfg)
    assert set(criadas) == {d.upper() for d in v.DERIVADAS}
    assert df["IDADE_ANOS"].iloc[:3].tolist() == [40.0, 2.0, 1.0] and pd.isna(df["IDADE_ANOS"].iloc[3])
    assert df["FAIXA_ETARIA"].iloc[:3].tolist() == ["40-49", "1-4", "1-4"] and pd.isna(df["FAIXA_ETARIA"].iloc[3])
    # intervalo: 2 dias ok | -5 (negativo) | 10 ok | 60 (>30) | ausente | 7 ok
    assert df["FLAG_INTERVALO_INVALIDO"].tolist() == [0, 1, 0, 1, 1, 0]
    assert df["INTERVALO_SINT_INTERNA_DIAS"].iloc[np.array([0, 2, 5])].tolist() == [2.0, 10.0, 7.0]
    assert df["INTERVALO_SINT_INTERNA_DIAS"].iloc[np.array([1, 3, 4])].isna().all()
    assert df["SIN_SEMANA"].between(-1, 1).all() and df["COS_SEMANA"].between(-1, 1).all()


def test_derivadas_nao_dependem_do_desfecho(cfg):
    import inspect
    fonte = inspect.getsource(v.add_derived)
    for proibido in ("EVOLUCAO", "dt_evoluca", "dt_encerra", "CLASSI_FIN"):
        assert proibido not in fonte


# ---------------------------------------------------------------------------
# A3b — split aleatório e cenários
# ---------------------------------------------------------------------------

def test_split_aleatorio_proporcoes_estratos_e_reprodutibilidade():
    n = 10_000
    y = np.array(["1"] * 8_700 + ["2"] * 1_300)
    a = v.split_aleatorio(n, y, seed=42)
    b = v.split_aleatorio(n, y, seed=42)
    c = v.split_aleatorio(n, y, seed=7)
    assert (a == b).all() and not (a == c).all()

    s = pd.Series(a)
    assert s.value_counts().to_dict() == {"treino": 7000, "validacao": 1500, "holdout": 1500}
    for classe, total in (("1", 8700), ("2", 1300)):
        sub = pd.Series(a[y == classe]).value_counts()
        assert abs(sub["treino"] - 0.70 * total) <= 1 and abs(sub["validacao"] - 0.15 * total) <= 1


def test_split_por_ordem_e_cronologico():
    t = pd.to_datetime(pd.Series(pd.date_range("2022-01-01", periods=1000))).sample(frac=1, random_state=1).to_numpy()
    rot = v.split_por_ordem(t)
    d = pd.DataFrame({"t": t, "r": rot})
    assert d[d.r == "treino"].t.max() <= d[d.r == "validacao"].t.min()
    assert d[d.r == "validacao"].t.max() <= d[d.r == "holdout"].t.min()


def test_cenario_sem_2020_2021_exclui_os_anos(cfg, tmp_path):
    base = v.make_demo(n=20_000, inicio="2019-01-01", anos=7)[0]
    base.columns = [c.lower() for c in base.columns]
    df = v.prepare(base)

    y = _escrever_yaml(tmp_path, ["nu_idade_n", "idade_anos"], ["febre", "dispneia", "faixa_etaria"])
    c2 = json.loads(json.dumps(cfg)); c2["dataset_analitico"]["path"] = str(tmp_path / "dataset.csv")
    rep = v.Report(tmp_path)
    cenarios = c2["experimentos_split"]["cenarios"]

    m_todos = v.a3_split_aleatorio_cenario(df, c2, rep, "todos_2019_2025", cenarios["todos_2019_2025"]["anos"], y)
    m_sem = v.a3_split_aleatorio_cenario(df, c2, rep, "sem_2020_2021", cenarios["sem_2020_2021"]["anos"], y)
    d_todos = pd.read_csv(m_todos["arquivo"]); d_sem = pd.read_csv(m_sem["arquivo"])

    assert {2019, 2020, 2021, 2022, 2023, 2024, 2025} <= set(d_todos["ano_internacao"].unique())
    assert set(d_sem["ano_internacao"].unique()) == {2019, 2022, 2023, 2024, 2025}
    assert len(d_sem) < len(d_todos)
    assert set(d_todos["split"].unique()) == {"treino", "validacao", "holdout"}
    assert abs(d_todos["split"].value_counts(normalize=True)["treino"] - 0.70) < 0.005

    prev = d_todos.groupby("split")["evolucao"].apply(lambda s: (s == 2).mean())
    assert prev.max() - prev.min() < 0.005

    assert m_todos["arquivo"] != m_sem["arquivo"]
    assert not [f for f in rep.findings if f[0] == "A3b" and f[2] == v.FAIL]

    assert v.verificar_dataset_congelado(m_todos["arquivo"], rep) is True
    with open(m_todos["arquivo"], "a", encoding="utf-8") as fh:
        fh.write("\n")
    assert v.verificar_dataset_congelado(m_todos["arquivo"], rep) is False


def test_benchmark_aleatorio_x_temporal_e_comparacao(cfg, tmp_path):
    base = v.make_demo(n=15_000, inicio="2019-01-01", anos=7)[0]
    base.columns = [c.lower() for c in base.columns]
    df = v.prepare(base)

    y = _escrever_yaml(tmp_path, ["nu_idade_n", "idade_anos", "sin_semana", "cos_semana"],
                       ["febre", "dispneia", "faixa_etaria"])
    c2 = json.loads(json.dumps(cfg)); c2["dataset_analitico"]["path"] = str(tmp_path / "dataset.csv")
    rep = v.Report(tmp_path)
    metas, benchs = {}, {}

    for nome, spec in c2["experimentos_split"]["cenarios"].items():
        metas[nome] = v.a3_split_aleatorio_cenario(df, c2, rep, nome, spec["anos"], y)
        benchs[nome] = v.a3_benchmark_split(metas[nome]["arquivo"], y, c2, rep, nome, max_rows=8_000)
        assert {"aleatoria", "temporal_por_ordem"} == set(benchs[nome]["particao"])
        lg = benchs[nome][benchs[nome]["modelo"] == "logistica"]
        assert (lg["roc_auc"] > 0.6).all()      # sinal sintético (idade/dispneia) é aprendido

    t = v.comparar_cenarios(metas, benchs, rep)
    assert list(t["cenario"]) == ["todos_2019_2025", "sem_2020_2021"]
    assert t.loc[0, "n_linhas"] > t.loc[1, "n_linhas"]
    assert "pr_auc_aleatoria" in t.columns and "pr_auc_temporal_por_ordem" in t.columns


def test_graficos_do_split_sao_gerados(cfg, tmp_path):
    base = v.make_demo(n=12_000, inicio="2019-01-01", anos=7)[0]
    base.columns = [c.lower() for c in base.columns]
    df = v.prepare(base)

    y = _escrever_yaml(tmp_path, ["nu_idade_n"], ["febre", "dispneia"])
    c2 = json.loads(json.dumps(cfg)); c2["dataset_analitico"]["path"] = str(tmp_path / "dataset.csv")
    rep = v.Report(tmp_path)
    nomes = list(c2["experimentos_split"]["cenarios"])

    for nome in nomes:
        v.a3_split_aleatorio_cenario(df, c2, rep, nome, c2["experimentos_split"]["cenarios"][nome]["anos"], y)

    figs = tmp_path / "figs"
    pngs = [v.grafico_split_cenario(rep, c2, n, c2["experimentos_split"]["cenarios"][n]["anos"], figs) for n in nomes]
    pngs.append(v.grafico_comparacao_cenarios(rep, c2, nomes, figs))

    for p in pngs:
        assert p.exists() and p.stat().st_size > 10_000 and p.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert {p.name for p in pngs} == {"split_todos_2019_2025.png", "split_sem_2020_2021.png", "split_comparacao_cenarios.png"}


# ---------------------------------------------------------------------------
# A4 — tabela de decisão e registo
# ---------------------------------------------------------------------------

def test_decision_table_alerta_complexidade_sem_ganho(cfg, tmp_path):
    res = pd.DataFrame({"modelo": ["baseline"] * 2 + ["logistica"] * 2 + ["boosting"] * 2,
                        "pr_auc": [.15, .15, .40, .40, .401, .401], "roc_auc": [.5] * 2 + [.8] * 2 + [.8] * 2,
                        "brier": [.15] * 2 + [.10] * 2 + [.11] * 2})
    rep = v.Report(tmp_path)
    v.a4_decision_table(res, cfg, rep)
    t = pd.read_csv(tmp_path / "a4_tabela_decisao.csv")
    assert "não justifica" in t.loc[t["modelo"] == "boosting", "alertas_automaticos"].iloc[0]


def test_log_decision_upsert(tmp_path):
    v.log_decision(tmp_path, "D-01", "tema", "a")
    t = v.log_decision(tmp_path, "D-01", "tema", "b")
    assert len(t) == 1 and t.loc[0, "decisao"] == "b"


# ---------------------------------------------------------------------------
# Leitura compacta — colunas ``category``
# ---------------------------------------------------------------------------

def test_resultados_iguais_com_colunas_category(cfg, tmp_path):
    """O resultado do A1/A2 não muda quando o texto é lido como ``category``."""
    base = _base_texto()
    d_txt, d_cat = v.prepare(base.copy()), v.prepare(_como_categoria(base))
    r1, r2 = v.Report(tmp_path / "txt"), v.Report(tmp_path / "cat")

    wf1, wf2 = v.a1_waterfall(d_txt, cfg, r1), v.a1_waterfall(d_cat, cfg, r2)
    assert wf1[["n_excluido", "n_restante"]].equals(wf2[["n_excluido", "n_restante"]])

    c1, c2 = v.a1_cohort(d_txt, cfg), v.a1_cohort(d_cat, cfg)
    assert len(c1) == len(c2) and c1["_alvo"].sum() == c2["_alvo"].sum()

    for fn in (v.a2_missing, v.a2_dates, v.a2_duplicates, v.a2_maturity, v.a2_eligibility):
        fn(d_txt, cfg, r1)
        fn(d_cat, cfg, r2)

    d1 = pd.read_csv(tmp_path / "txt" / "a2_coerencia_datas.csv")
    d2 = pd.read_csv(tmp_path / "cat" / "a2_coerencia_datas.csv")
    assert d1[["regra", "n_violacoes"]].equals(d2[["regra", "n_violacoes"]])
    assert [f[2] for f in r1.findings] == [f[2] for f in r2.findings]


def test_export_e_vazamento_com_category(cfg, tmp_path):
    y = _escrever_yaml(tmp_path, ["nu_idade_n", "idade_anos"], ["febre", "faixa_etaria", "cs_sexo"])
    df = v.prepare(_como_categoria(_base_texto()))
    c2 = json.loads(json.dumps(cfg)); c2["dataset_analitico"]["path"] = str(tmp_path / "d.csv")
    rep = v.Report(tmp_path)

    meta = v.a3_split_aleatorio_cenario(df, c2, rep, "todos_2019_2025", [2019, 2020, 2021, 2022, 2023, 2024, 2025], y)
    assert meta["n_linhas"] > 0 and v.validar_contrato_c2(meta["arquivo"], y, rep) is True

    v.a3_leak_scan(v.a1_cohort(df, c2), c2, rep)
    assert not [f for f in rep.findings if f[2] == v.FAIL]


# ---------------------------------------------------------------------------
# Colunas necessárias do Parquet
# ---------------------------------------------------------------------------

def test_colunas_minimas_sao_menos_que_as_classificadas(cfg):
    schema = ["nu_notific", "hospital", "evolucao", "dt_interna", "dt_notific", "dt_sin_pri", "nu_idade_n", "tp_idade",
              "uti", "antiviral", "vacina_cov", "cs_raca", "coluna_x", "febre"]
    minimas = v.colunas_necessarias(schema, cfg, None, modo="minimas")
    classif = v.colunas_necessarias(schema, cfg, None, modo="classificadas")
    assert set(minimas) < set(classif)
    assert {"hospital", "evolucao", "dt_interna", "nu_idade_n", "tp_idade", "dt_sin_pri"} <= set(minimas)
    assert not ({"antiviral", "vacina_cov", "coluna_x"} & set(minimas))
    assert {"antiviral", "vacina_cov"} <= set(classif)
```

## `tests/test_reproducibility.py`

- Git: `tracked` · status `clean`
- Size: `5.1 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `27ce4e8b0f95c728593a299998f26b53c8c39feb88b531a56c125f251acc6194`

```python
"""Testes do registro de execuções (``src.utils.reproducibility``)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from src.utils import config as C
from src.utils import reproducibility as R


# Campos que ``registrar_execucao`` deve sempre gravar no metadata.
# Serve como armadilha contra remoções silenciosas na estrutura do dict.
_CAMPOS_METADATA: tuple[str, ...] = (
    "run_id", "timestamp", "modelo", "seed", "status",
    "parametros", "dataset", "metricas", "features",
    "duracao_s", "erro", "data_version", "gates", "versoes",
    "git", "env", "notas", "dataset_sha256", "supervised_yaml_sha256",
)


def _ler_meta(pasta: Path) -> dict[str, Any]:
    """Lê ``metadata.json`` de uma execução."""
    return json.loads((pasta / "metadata.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# registrar_execucao — estrutura e conteúdo
# ---------------------------------------------------------------------------

def test_registrar_execucao_cria_pasta(tmp_path: Path) -> None:
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


def test_metadata_tem_campos_obrigatorios(tmp_path: Path) -> None:
    pasta = R.registrar_execucao(
        modelo="teste",
        seed=7,
        parametros={"x": 1},
        metricas={"auc": 0.9},
        output_dir=tmp_path,
    )
    meta = _ler_meta(pasta)

    for chave in _CAMPOS_METADATA:
        assert chave in meta

    assert meta["seed"] == 7
    assert meta["modelo"] == "teste"
    assert meta["metricas"]["auc"] == 0.9


def test_metadata_grava_data_version(tmp_path: Path) -> None:
    pasta = R.registrar_execucao(modelo="dv", output_dir=tmp_path)
    assert _ler_meta(pasta)["data_version"] == C.DATA_VERSION


def test_metadata_grava_gates(tmp_path: Path) -> None:
    meta = _ler_meta(R.registrar_execucao(modelo="gates", output_dir=tmp_path))
    assert isinstance(meta["gates"], dict)
    assert "G9_holdout" in meta["gates"]


def test_seed_padrao_vem_do_config(tmp_path: Path) -> None:
    """Sem ``seed`` explícito, usa ``config.SEED``."""
    pasta = R.registrar_execucao(modelo="seed_default", output_dir=tmp_path)
    assert _ler_meta(pasta)["seed"] == C.SEED


# ---------------------------------------------------------------------------
# Run como context manager
# ---------------------------------------------------------------------------

def test_run_context_manager_sucesso(tmp_path: Path) -> None:
    r: R.Run | None = None
    with R.Run(modelo="ctx", seed=1, output_dir=tmp_path) as r:
        r.metrica(auc=0.77)
        r.anotar("nota de teste")

    assert r is not None
    assert r.pasta is not None
    meta = _ler_meta(r.pasta)
    assert meta["metricas"]["auc"] == 0.77
    assert "nota de teste" in meta["notas"]
    assert meta["duracao_s"] is not None
    assert meta["status"] == "success"
    assert meta["erro"] is None


def test_run_registra_excecao(tmp_path: Path) -> None:
    """Mesmo em exceção, o metadata é gravado — com status e erro."""
    r: R.Run | None = None
    with pytest.raises(RuntimeError, match="boom"):
        with R.Run(modelo="erro", output_dir=tmp_path) as r:
            raise RuntimeError("boom")

    assert r is not None
    assert r.pasta is not None
    meta = _ler_meta(r.pasta)
    assert meta["status"] == "error"
    assert meta["erro"]["tipo"] == "RuntimeError"
    assert "boom" in meta["erro"]["mensagem"]
    assert "Traceback" in meta["erro"]["traceback"]


def test_run_nao_suprime_excecao(tmp_path: Path) -> None:
    """O ``__exit__`` devolve ``False`` — a exceção propaga."""
    with pytest.raises(ValueError):
        with R.Run(modelo="propaga", output_dir=tmp_path):
            raise ValueError("propaga")


# ---------------------------------------------------------------------------
# gerar_run_id
# ---------------------------------------------------------------------------

def test_run_id_unico(tmp_path: Path) -> None:
    """Sufixo ``_NN`` evita colisão quando o ID base já existe."""
    a = R.gerar_run_id(modelo="dup", base_dir=tmp_path)
    (tmp_path / a).mkdir()
    b = R.gerar_run_id(modelo="dup", base_dir=tmp_path)
    assert a != b


# ---------------------------------------------------------------------------
# listar_runs / carregar_run
# ---------------------------------------------------------------------------

def test_listar_e_carregar(tmp_path: Path) -> None:
    R.registrar_execucao(modelo="a", output_dir=tmp_path)
    R.registrar_execucao(modelo="b", output_dir=tmp_path)

    runs = R.listar_runs(output_dir=tmp_path)
    assert len(runs) == 2

    meta = R.carregar_run(runs[0]["run_id"], output_dir=tmp_path)
    assert meta["modelo"] in {"a", "b"}
```

## `tests/test_smoke.py`

- Git: `tracked` · status `clean`
- Size: `3.2 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `f3161fc26862baaf40b068430fdf0f334f7c016964efec5340d393f3fbe782bc`

```python
"""
Smoke tests do Parquet de SRAG.

Verificam que o dataset existe, abre, tem o schema esperado e produz uma
saída mínima. Todos os testes são marcados ``slow`` via ``pytestmark``.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
import pytest

from src.utils import storage


pytestmark = pytest.mark.slow


# Colunas mínimas esperadas no SRAG; ajustar conforme o dicionário de dados.
COLUNAS_ESPERADAS: frozenset[str] = frozenset({"sg_uf", "dt_notific"})


@pytest.fixture
def parquet(parquet_disponivel: Path | None) -> Path:
    """``parquet_disponivel`` obrigatório — faz skip se ausente."""
    if parquet_disponivel is None:
        pytest.skip(
            "Nenhum Parquet encontrado. Rode 00_acesso_dados_parquet.ipynb "
            "ou 01_extracao.ipynb primeiro."
        )
    return parquet_disponivel


@pytest.fixture(scope="module")
def schema_colunas(parquet: Path) -> set[str]:
    """Nome das colunas do Parquet — lido uma vez por módulo."""
    return set(pq.read_schema(parquet).names)


# ---------------------------------------------------------------------------
# Estrutura do arquivo
# ---------------------------------------------------------------------------

def test_parquet_existe_e_nao_vazio(parquet: Path) -> None:
    assert parquet.is_file()
    assert parquet.stat().st_size > 0


def test_parquet_tem_magic_bytes(parquet: Path) -> None:
    with open(parquet, "rb") as f:
        magic = f.read(4)
    assert magic == b"PAR1", f"Arquivo não é Parquet válido (magic={magic!r})"


def test_parquet_abre(schema_colunas: set[str]) -> None:
    assert schema_colunas


def test_parquet_tem_colunas_esperadas(schema_colunas: set[str]) -> None:
    faltando = COLUNAS_ESPERADAS - schema_colunas
    assert not faltando, f"Colunas ausentes: {sorted(faltando)}"


# ---------------------------------------------------------------------------
# Leitura via pandas
# ---------------------------------------------------------------------------

def test_parquet_tem_registros(parquet: Path) -> None:
    df = pd.read_parquet(parquet, columns=["sg_uf"])
    assert len(df) > 0


def test_produz_saida_pequena(parquet: Path) -> None:
    """O smoke final — produzir uma saída minúscula funciona ponta-a-ponta."""
    df = pd.read_parquet(parquet, columns=["sg_uf"]).head(10)
    assert len(df) == 10


# ---------------------------------------------------------------------------
# Leitura via storage.read_srag
# ---------------------------------------------------------------------------

def test_storage_read_srag(parquet: Path) -> None:
    """``storage.read_srag`` devolve DataFrame não vazio com as colunas pedidas."""
    df = storage.read_srag(columns=["sg_uf"])
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert "sg_uf" in df.columns


def test_storage_read_srag_com_filtro(parquet: Path) -> None:
    """O filtro ``sg_uf == "SP"`` é aplicado no lado do Parquet."""
    df = storage.read_srag(
        columns=["sg_uf"],
        filters=[("sg_uf", "==", "SP")],
    )
    if df.empty:
        pytest.skip("Nenhum registro de SP no dataset.")
    assert (df["sg_uf"] == "SP").all()
```

## `tests/test_split.py`

- Git: `tracked` · status `clean`
- Size: `9.4 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `64427eee86a2c645dc367875cc93b984d65d716716fba3d1f498931894ab98e3`

```python
"""
Testes para ``src.data.split.criar_particoes_agrupadas``.

Invariantes:

1. nenhum grupo em mais de uma partição;
2. proporções de linhas próximas de 70/15/15 (com tolerância);
3. mesma seed → mesma partição.

Cobrem também políticas de estratos pequenos, grupos com alvo
heterogéneo (raise/warn) e validações de parâmetros/colunas.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import pytest

from src.data.split import (
    PARTICOES_CANONICAS,
    SplitWarning,
    criar_particoes_agrupadas,
)


# ---------------------------------------------------------------------------
# Fixtures sintéticas
# ---------------------------------------------------------------------------

def _df_estratificado(
    n_grupos_classe0: int = 30,
    n_grupos_classe1: int = 20,
    linhas_por_grupo: int = 3,
    seed: int = 0,
) -> pd.DataFrame:
    """DataFrame com grupos homogéneos (alvo constante por grupo)."""
    rng = np.random.default_rng(seed)
    linhas = []
    gid = 0
    for classe, n_grupos in [(0, n_grupos_classe0), (1, n_grupos_classe1)]:
        for _ in range(n_grupos):
            grupo = f"g{gid:04d}"
            gid += 1
            n = int(rng.integers(1, linhas_por_grupo + 1))
            for i in range(n):
                linhas.append({
                    "nu_notific": grupo,
                    "alvo": classe,
                    "valor": float(rng.normal()),
                    "idx_linha": i,
                })
    return pd.DataFrame(linhas)


def _df_grande(
    n_grupos_classe0: int = 700,
    n_grupos_classe1: int = 300,
) -> pd.DataFrame:
    """Base grande o suficiente para checar proporções com folga."""
    return _df_estratificado(
        n_grupos_classe0=n_grupos_classe0,
        n_grupos_classe1=n_grupos_classe1,
        linhas_por_grupo=2,
        seed=1,
    )


def _df_com_estrato_pequeno() -> pd.DataFrame:
    """1 grupo na classe 1 (estrato pequeno) + 20 grupos na classe 0."""
    return _df_estratificado(n_grupos_classe0=20, n_grupos_classe1=1)


def _df_com_grupo_heterogeneo() -> pd.DataFrame:
    """``g0000`` (classe 0) recebe uma linha com alvo=1."""
    df = _df_estratificado(n_grupos_classe0=20, n_grupos_classe1=10)
    idx = df.index[df["nu_notific"] == "g0000"][0]
    df.loc[idx, "alvo"] = 1
    return df


def _split(df: pd.DataFrame, **kwargs: Any) -> pd.DataFrame:
    """``criar_particoes_agrupadas`` com os defaults dos testes."""
    params: dict[str, Any] = {
        "target_column": "alvo",
        "group_column": "nu_notific",
        "partition_column": "particao",
    }
    params.update(kwargs)
    return criar_particoes_agrupadas(df, **params)


def _assert_proporcoes(contagem: pd.Series, tol: float = 0.05) -> None:
    """Asserts de 70/15/15 sobre ``value_counts(normalize=True)``."""
    assert abs(contagem["treino"] - 0.70) < tol, contagem
    assert abs(contagem["validacao"] - 0.15) < tol, contagem
    assert abs(contagem["teste"] - 0.15) < tol, contagem


# ---------------------------------------------------------------------------
# Invariantes de partição
# ---------------------------------------------------------------------------

def test_grupos_nao_cruzam_particoes() -> None:
    """Nenhum ``nu_notific`` aparece em mais de uma partição."""
    out = _split(_df_estratificado(), seed=42)
    grupos_por_particao = out.groupby("nu_notific", observed=True)["particao"].nunique()
    assert (grupos_por_particao == 1).all(), (
        f"Grupos em mais de uma partição:\n{grupos_por_particao[grupos_por_particao > 1]}"
    )


def test_nenhuma_linha_perdida() -> None:
    df = _df_estratificado()
    out = _split(df, seed=42)
    assert len(out) == len(df)
    assert set(out["particao"].unique()) == set(PARTICOES_CANONICAS)


# ---------------------------------------------------------------------------
# Proporções 70/15/15
# ---------------------------------------------------------------------------

def test_proporcoes_linhas_proximas_de_70_15_15() -> None:
    """Grupos são atómicos; a proporção real de linhas oscila em torno do alvo."""
    out = _split(_df_grande(), seed=42)
    _assert_proporcoes(out["particao"].value_counts(normalize=True))


def test_proporcoes_grupos_proximas_de_70_15_15() -> None:
    out = _split(_df_grande(), seed=42)
    por_grupo = out.groupby("nu_notific", observed=True)["particao"].first()
    _assert_proporcoes(por_grupo.value_counts(normalize=True))


def test_estratificacao_preserva_proporcao_aproximada() -> None:
    df = _df_estratificado(n_grupos_classe0=70, n_grupos_classe1=30)
    out = _split(df, seed=42)

    prevalencia_global = df["alvo"].mean()
    for particao in PARTICOES_CANONICAS:
        sub = out[out["particao"] == particao]
        assert abs(sub["alvo"].mean() - prevalencia_global) < 0.10


# ---------------------------------------------------------------------------
# Reprodutibilidade por seed
# ---------------------------------------------------------------------------

def test_reprodutibilidade_mesma_seed() -> None:
    """Mesma seed → mesmas partições."""
    df = _df_estratificado()
    a = _split(df, seed=7)
    b = _split(df, seed=7)
    pd.testing.assert_series_equal(a["particao"], b["particao"])


def test_seeds_diferentes_produzem_splits_diferentes() -> None:
    df = _df_estratificado()
    a = _split(df, seed=1)
    b = _split(df, seed=2)
    assert not a["particao"].equals(b["particao"])


# ---------------------------------------------------------------------------
# Estratos pequenos — 4 políticas
# ---------------------------------------------------------------------------

def test_estrato_pequeno_raise_e_default() -> None:
    with pytest.raises(ValueError, match="Estrato"):
        _split(_df_com_estrato_pequeno())


def test_estrato_pequeno_warn_teste_manda_para_teste() -> None:
    df = _df_com_estrato_pequeno()
    with pytest.warns(SplitWarning, match="Destinando ao teste"):
        out = _split(df, politica_estratos_pequenos="warn_teste")

    linhas_classe1 = out[out["alvo"] == 1]
    assert (linhas_classe1["particao"] == "teste").all()
    assert len(out) == len(df)


def test_estrato_pequeno_warn_treino_manda_para_treino() -> None:
    with pytest.warns(SplitWarning, match="Destinando ao treino"):
        out = _split(_df_com_estrato_pequeno(), politica_estratos_pequenos="warn_treino")

    linhas_classe1 = out[out["alvo"] == 1]
    assert (linhas_classe1["particao"] == "treino").all()


def test_estrato_pequeno_drop_remove_linhas() -> None:
    df = _df_com_estrato_pequeno()
    with pytest.warns(SplitWarning, match="Descartando"):
        out = _split(df, politica_estratos_pequenos="drop")

    assert (out["alvo"] == 1).sum() == 0
    assert len(out) < len(df)
    assert set(out["particao"].unique()).issubset(set(PARTICOES_CANONICAS))


# ---------------------------------------------------------------------------
# Grupos com alvo heterogéneo
# ---------------------------------------------------------------------------

def test_grupo_heterogeneo_raise() -> None:
    with pytest.raises(ValueError, match="mais de um valor distinto"):
        _split(_df_com_grupo_heterogeneo())


def test_grupo_heterogeneo_warn() -> None:
    with pytest.warns(SplitWarning, match="mais de um valor distinto"):
        _split(_df_com_grupo_heterogeneo(), on_grupo_alvo_heterogeneo="warn")


# ---------------------------------------------------------------------------
# Validação de parâmetros e colunas
# ---------------------------------------------------------------------------

def test_coluna_alvo_ausente() -> None:
    with pytest.raises(KeyError, match="alvo"):
        criar_particoes_agrupadas(
            _df_estratificado(),
            target_column="nao_existe",
            group_column="nu_notific",
        )


def test_coluna_grupo_ausente() -> None:
    with pytest.raises(KeyError, match="grupo"):
        criar_particoes_agrupadas(
            _df_estratificado(),
            target_column="alvo",
            group_column="nao_existe",
        )


def test_partition_column_ja_existente() -> None:
    df = _df_estratificado()
    df["particao"] = "treino"
    with pytest.raises(ValueError, match="já contém"):
        _split(df)


@pytest.mark.parametrize(
    "kwargs, match",
    [
        ({"frac_treino": 0.0}, "frac_treino"),
        ({"frac_validacao": 1.5}, "frac_validacao"),
        ({"frac_treino": 0.7, "frac_validacao": 0.4}, "< 1"),
    ],
    ids=["frac_treino_zero", "frac_validacao_acima", "soma_maior_que_1"],
)
def test_frac_invalida(kwargs: dict, match: str) -> None:
    with pytest.raises(ValueError, match=match):
        _split(_df_estratificado(), **kwargs)


def test_min_grupos_abaixo_de_3() -> None:
    with pytest.raises(ValueError, match="min_grupos_por_estrato"):
        _split(_df_estratificado(), min_grupos_por_estrato=2)


def test_politica_invalida() -> None:
    # Valor viola intencionalmente o Literal PoliticaEstratosPequenos.
    with pytest.raises(ValueError, match="politica_estratos_pequenos"):
        _split(_df_estratificado(), politica_estratos_pequenos="qualquer_coisa")  # type: ignore[arg-type]


def test_df_vazio() -> None:
    with pytest.raises(ValueError, match="vazio"):
        _split(pd.DataFrame({"alvo": [], "nu_notific": []}))
```

## `tests/test_supervised_artifact.py`

- Git: `tracked` · status `clean`
- Size: `3.0 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `a96b43cbaabb4dfc300bb4984a27705cea7d68b5c33607eedd157aeb1b2b7d44`

```python
"""Testes do artefacto supervisionado (``src.data.supervised_artifact``).

Cobrem o contrato de persistência/leitura: preservação da partição,
validação do tipo de coorte e exigência das três partições.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from src.data.supervised_artifact import (
    load_supervised_artifact,
    persist_supervised_artifact,
)


def _frame() -> pd.DataFrame:
    """6 registos — 2 por partição, alvo alternado (0/1).

    Colunas mínimas para os testes: uma feature numérica, o alvo binário
    e a coluna de partição.
    """
    return pd.DataFrame({
        "idade_anos":      [10.0, 20.0, 30.0, 40.0, 50.0, 60.0],
        "alvo_obito_srag": [0, 1, 0, 1, 0, 1],
        "particao":        ["treino", "treino", "validacao", "validacao", "teste", "teste"],
    })


def _persistir(tmp_path: Path, frame: pd.DataFrame, **kwargs: Any) -> None:
    """Grava ``frame`` como artefacto supervisionado em ``tmp_path``.

    Preenche os kwargs obrigatórios com valores mínimos e deixa
    ``**kwargs`` sobrepor (ex.: ``source`` com conteúdo).
    """
    params: dict[str, Any] = {
        "source":           {},
        "feature_columns":  ["idade_anos"],
        "target_column":    "alvo_obito_srag",
        "partition_column": "particao",
        "cohort_kind":      "provisional",
        "seed":             42,
    }
    params.update(kwargs)
    persist_supervised_artifact(frame, root=tmp_path, **params)


# ---------------------------------------------------------------------------
# Contrato de round-trip
# ---------------------------------------------------------------------------

def test_roundtrip_preserva_particao(tmp_path: Path) -> None:
    """Gravar e ler preserva a partição, e o manifesto regista o estado inicial."""
    frame = _frame()
    _persistir(tmp_path, frame, source={"kind": "provisional", "sha256": "abc"})

    loaded, manifest = load_supervised_artifact(tmp_path, expected_kind="provisional")

    assert loaded["particao"].tolist() == frame["particao"].tolist()
    assert manifest["test_opened"] is False
    assert manifest["seed"] == 42


# ---------------------------------------------------------------------------
# Validações
# ---------------------------------------------------------------------------

def test_tipo_de_coorte_incorreto_falha(tmp_path: Path) -> None:
    """Ler com ``expected_kind`` diferente do gravado deve falhar."""
    _persistir(tmp_path, _frame())

    with pytest.raises(RuntimeError, match="SRAG_COHORT_KIND"):
        load_supervised_artifact(tmp_path, expected_kind="final")


def test_particoes_incompletas_falham(tmp_path: Path) -> None:
    """Dataset sem o bloco ``teste`` viola o contrato de partições."""
    frame = _frame().query("particao != 'teste'")

    with pytest.raises(ValueError, match="Particoes esperadas"):
        _persistir(tmp_path, frame)
```

## `tests/test_target.py`

- Git: `tracked` · status `clean`
- Size: `3.7 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `d85c2169acc6f5354bd755e57e581a19a479be160515fcbac3260b4fcfb21aa7`

```python
"""Contrato do alvo binário: ``evolucao`` → {0, 1, NaN}."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.models.pipeline import criar_alvo_binario, filtrar_rotulos_validos
from src.utils import config as C


def _df(valores: list[float | None]) -> pd.DataFrame:
    """DataFrame ``{"evolucao": valores, "feat": range(n)}``.

    A coluna ``feat`` serve como índice rastreável nas asserts.
    """
    return pd.DataFrame({"evolucao": valores, "feat": range(len(valores))})


# ---------------------------------------------------------------------------
# Mapeamento evolucao → {0, 1, NaN}
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ([2.0],       [1.0]),
        ([1.0],       [0.0]),
        ([3.0],       [float("nan")]),
        ([9.0],       [float("nan")]),
        ([np.nan],    [float("nan")]),
    ],
    ids=["positivo", "negativo", "codigo_3", "codigo_9", "nan_entrada"],
)
def test_mapeamento_puro(entrada, esperado) -> None:
    """``2.0``→1, ``1.0``→0, qualquer outro→NaN."""
    y = criar_alvo_binario(_df(entrada))
    for obtido, esperado_valor in zip(y, esperado):
        if pd.isna(esperado_valor):
            assert pd.isna(obtido)
        else:
            assert obtido == esperado_valor


def test_mistura_completa() -> None:
    y = criar_alvo_binario(_df([1.0, 2.0, 3.0, 9.0, np.nan]))
    assert y.iloc[0] == 0.0
    assert y.iloc[1] == 1.0
    assert y.iloc[2:].isna().all()


# ---------------------------------------------------------------------------
# filtrar_rotulos_validos
# ---------------------------------------------------------------------------

def test_filtrar_remove_nan() -> None:
    df = _df([1.0, 2.0, 3.0, 9.0, np.nan])
    X_ok, y_ok = filtrar_rotulos_validos(df[["feat"]], criar_alvo_binario(df))

    assert len(y_ok) == 2
    assert y_ok.dtype == np.int8
    assert y_ok.tolist() == [0, 1]
    assert list(X_ok["feat"]) == [0, 1]


def test_filtrar_exige_indice_alinhado() -> None:
    X = pd.DataFrame({"feat": [1, 2]}, index=[0, 1])
    y = pd.Series([0, 1], index=[1, 2])
    with pytest.raises(ValueError, match="mesmo índice"):
        filtrar_rotulos_validos(X, y)


# ---------------------------------------------------------------------------
# Validação de argumentos
# ---------------------------------------------------------------------------

def test_positivos_e_negativos_nao_se_sobrepoem() -> None:
    with pytest.raises(ValueError, match="sobrepor"):
        criar_alvo_binario(_df([1.0, 2.0]), positivos=[1.0, 2.0], negativos=[1.0])


def test_positivos_vazio_levanta() -> None:
    with pytest.raises(ValueError, match="positivos"):
        criar_alvo_binario(_df([1.0, 2.0]), positivos=[], negativos=[1.0])


def test_negativos_vazio_levanta() -> None:
    with pytest.raises(ValueError, match="negativos"):
        criar_alvo_binario(_df([1.0, 2.0]), positivos=[2.0], negativos=[])


# ---------------------------------------------------------------------------
# Default vem do YAML
# ---------------------------------------------------------------------------

def test_default_vem_do_yaml() -> None:
    """Sem argumentos, usa ``target.positivos`` e ``target.negativos`` do YAML."""
    pos = C.cfg("target", "positivos")
    neg = C.cfg("target", "negativos")
    assert pos, "target.positivos precisa estar definido no YAML"
    assert neg, "target.negativos precisa estar definido no YAML"

    y = criar_alvo_binario(_df([float(pos[0]), float(neg[0])]))
    assert y.tolist() == [1.0, 0.0]
```

## `tests/test_temporal.py`

- Git: `tracked` · status `clean`
- Size: `5.9 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `8f3be3964a5456ddc4a6588aafc2c382e7525bc613eb9bb1d2ca25cd41a93fd0`

```python
"""
Testes do split temporal em três blocos e da trava do holdout.

Cobrem garantia de não sobreposição temporal, validação de frações e
coluna temporal, tratamento de ``NaT`` e liberação do holdout apenas com
``G9_holdout`` aprovado.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.evaluation.temporal import TemporalSplit, split_temporal_3way
from src.utils import config as C


@pytest.fixture
def df_temporal() -> pd.DataFrame:
    """100 dias consecutivos a partir de 2020-01-01, coluna ``x`` = range(100)."""
    return pd.DataFrame({
        "data": pd.date_range("2020-01-01", periods=100, freq="D"),
        "x":    range(100),
    })


@pytest.fixture
def df_temporal_com_nat(df_temporal: pd.DataFrame) -> pd.DataFrame:
    """``df_temporal`` com ``NaT`` na linha 5 da coluna ``data``."""
    df = df_temporal.copy()
    df.loc[5, "data"] = pd.NaT
    return df


# ---------------------------------------------------------------------------
# split_temporal_3way — ordem e proporções
# ---------------------------------------------------------------------------

def test_split_temporal_ordem_correta(df_temporal: pd.DataFrame) -> None:
    """Sem sobreposição temporal entre blocos; proporções 70/15/15."""
    treino, validacao, holdout = split_temporal_3way(df_temporal, "data")

    assert treino["data"].max() <= validacao["data"].min()
    assert validacao["data"].max() <= holdout["data"].min()
    assert len(treino) == 70
    assert len(validacao) == 15
    assert len(holdout) == 15


def test_split_temporal_preserva_ordem(df_temporal: pd.DataFrame) -> None:
    treino, validacao, holdout = split_temporal_3way(df_temporal, "data")

    assert treino["data"].is_monotonic_increasing
    assert validacao["data"].is_monotonic_increasing
    assert holdout["data"].is_monotonic_increasing


# ---------------------------------------------------------------------------
# split_temporal_3way — validações de parâmetros
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "kwargs",
    [
        {"frac_treino": 0},
        {"frac_treino": 1},
        {"frac_validacao": 0},
        {"frac_validacao": 1},
        {"frac_treino": 0.8, "frac_validacao": 0.3},
    ],
    ids=[
        "frac_treino_zero",
        "frac_treino_um",
        "frac_validacao_zero",
        "frac_validacao_um",
        "soma_maior_que_1",
    ],
)
def test_fracoes_invalidas(df_temporal: pd.DataFrame, kwargs: dict) -> None:
    with pytest.raises(ValueError):
        split_temporal_3way(df_temporal, "data", **kwargs)


def test_coluna_tempo_ausente(df_temporal: pd.DataFrame) -> None:
    with pytest.raises(KeyError):
        split_temporal_3way(df_temporal, "coluna_inexistente")


def test_coluna_tempo_nao_datetime(df_temporal: pd.DataFrame) -> None:
    df = df_temporal.copy()
    df["data"] = df["data"].astype(str)
    with pytest.raises(TypeError):
        split_temporal_3way(df, "data")


# ---------------------------------------------------------------------------
# split_temporal_3way — tratamento de NaT
# ---------------------------------------------------------------------------

def test_on_nat_raise(df_temporal_com_nat: pd.DataFrame) -> None:
    with pytest.raises(ValueError):
        split_temporal_3way(df_temporal_com_nat, "data", on_nat="raise")


def test_on_nat_drop(df_temporal_com_nat: pd.DataFrame) -> None:
    treino, validacao, holdout = split_temporal_3way(
        df_temporal_com_nat, "data", on_nat="drop",
    )
    assert len(treino) + len(validacao) + len(holdout) == 99


def test_on_nat_invalido(df_temporal: pd.DataFrame) -> None:
    # Valor viola intencionalmente o Literal OnNat.
    with pytest.raises(ValueError):
        split_temporal_3way(df_temporal, "data", on_nat="ignorar")  # type: ignore[arg-type]


def test_dataset_pequeno() -> None:
    df = pd.DataFrame({"data": pd.date_range("2020-01-01", periods=2)})
    with pytest.raises(ValueError):
        split_temporal_3way(df, "data")


# ---------------------------------------------------------------------------
# TemporalSplit — trava do holdout
# ---------------------------------------------------------------------------

def test_holdout_bloqueado_por_padrao(df_temporal: pd.DataFrame) -> None:
    split = TemporalSplit(df_temporal, "data")
    assert not split.holdout_liberado
    with pytest.raises(RuntimeError):
        split.holdout()


def test_holdout_liberado_apos_gate(
    df_temporal: pd.DataFrame,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Com ``G9_holdout`` aprovado, ``concluir_selecao()`` libera o holdout."""
    monkeypatch.setattr(C, "cfg", lambda *a, **kw: {"status": "aprovado"})

    split = TemporalSplit(df_temporal, "data")
    split.concluir_selecao()

    assert split.holdout_liberado
    assert len(split.holdout()) == 15


def test_holdout_bloqueado_sem_gate(
    df_temporal: pd.DataFrame,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Com ``G9_holdout`` pendente, ``concluir_selecao()`` levanta ``RuntimeError``."""
    monkeypatch.setattr(C, "cfg", lambda *a, **kw: {"status": "pendente"})

    split = TemporalSplit(df_temporal, "data")
    with pytest.raises(RuntimeError):
        split.concluir_selecao()


def test_treino_validacao_nao_expoe_holdout(df_temporal: pd.DataFrame) -> None:
    split = TemporalSplit(df_temporal, "data")
    treino, validacao = split.treino_validacao()

    assert treino is split.treino
    assert validacao is split.validacao


def test_resumo_marca_holdout_bloqueado(df_temporal: pd.DataFrame) -> None:
    resumo = TemporalSplit(df_temporal, "data").resumo()

    assert "treino" in resumo
    assert "validacao" in resumo
    assert "holdout" in resumo
    assert "bloqueado" in resumo
```

## `tools/clean_project.py`

- Git: `tracked` · status `clean`
- Size: `3.7 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `06775202d5495fc9c9bbe917b343da103153ec1a1c491c20b34c8e3cdd7260d6`

```python
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DIRECTORIES_TO_CLEAN = [
    "outputs",
    "reports",
    "models",
    "logs",
    ".pytest_cache",
    ".ipynb_checkpoints",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".nox",
]

FILE_PATTERNS = [
    "*.png", "*.jpg", "*.jpeg", "*.gif", "*.svg",
    "*.log", "*.tmp",
    "*.joblib", "*.pkl", "*.pickle",
    "*.h5", "*.hdf5",
    "*.pt", "*.pth", "*.onnx",
    "*.npy", "*.npz",
]

PROTECTED_FOLDERS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "notebooks",
    "src",
    "tests",
    "tools",
    "configs",
    "docs",
    "data/raw",
    "data/analytical",
    "data/external",
}


def remove_file(path: Path, dry_run: bool) -> None:
    if dry_run:
        print(f"[DRY RUN] FILE  {path}")
        return
    path.unlink(missing_ok=True)
    print(f"[REMOVED] FILE  {path}")


def remove_directory(path: Path, dry_run: bool) -> None:
    if dry_run:
        print(f"[DRY RUN] DIR   {path}")
        return
    shutil.rmtree(path, ignore_errors=True)
    print(f"[REMOVED] DIR   {path}")


def clean_directory_contents(path: Path, dry_run: bool) -> None:
    """Remove conteúdo mas preserva o diretório e os .gitkeep."""
    if not path.exists():
        return
    for child in path.iterdir():
        if child.name == ".gitkeep":
            continue
        if child.is_dir():
            remove_directory(child, dry_run)
        else:
            remove_file(child, dry_run)


def clean_directories(dry_run: bool) -> None:
    for directory in DIRECTORIES_TO_CLEAN:
        path = PROJECT_ROOT / directory
        if path.exists():
            clean_directory_contents(path, dry_run)


def clean_pycache(dry_run: bool) -> None:
    for cache_dir in PROJECT_ROOT.rglob("__pycache__"):
        remove_directory(cache_dir, dry_run)


def clean_generated_files(dry_run: bool) -> None:
    for pattern in FILE_PATTERNS:
        for file_path in PROJECT_ROOT.rglob(pattern):
            if any(protected in str(file_path) for protected in PROTECTED_FOLDERS):
                continue
            remove_file(file_path, dry_run)


def clean_processed_data(dry_run: bool) -> None:
    processed_folder = PROJECT_ROOT / "data" / "processed"
    if processed_folder.exists():
        clean_directory_contents(processed_folder, dry_run)


def clean_reference(dry_run: bool) -> None:
    for name in ("PROJECT_COMPLETE_REFERENCE.md", "PROJECT_COMPLETE_REFERENCE.json"):
        path = PROJECT_ROOT / "docs" / name
        if path.exists():
            remove_file(path, dry_run)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Limpa artefactos gerados sem tocar em código, configs ou dados originais."
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Mostra o que seria removido sem apagar.")
    parser.add_argument("--clean-processed", action="store_true",
                        help="Remove data/processed (obriga a re-download do Parquet).")
    parser.add_argument("--clean-reference", action="store_true",
                        help="Remove docs/PROJECT_COMPLETE_REFERENCE.{md,json}.")
    args = parser.parse_args()

    clean_directories(args.dry_run)
    clean_pycache(args.dry_run)
    clean_generated_files(args.dry_run)

    if args.clean_processed:
        clean_processed_data(args.dry_run)

    if args.clean_reference:
        clean_reference(args.dry_run)

    print("\nLimpeza concluída.")


if __name__ == "__main__":
    main()
```

## `tools/update_project_reference.py`

- Git: `tracked` · status `clean`
- Size: `106.0 KB` · modified `2026-10-17 19:30 UTC`
- SHA-256: `2ffc9adf7a56f5afb4573d28b1f51925303f56a438ad52b4bcd32d637ee88617`

```python
#!/usr/bin/env python3
r"""Generate a complete, AI-oriented diagnostic snapshot of the SRAG repository.

Run from anywhere inside the repository, preferably with the project venv
(so installed package versions are the real ones):

    .\.venv\Scripts\python.exe tools\update_project_reference.py
    .\.venv\Scripts\python.exe tools\update_project_reference.py --split-mb 4
    .\.venv\Scripts\python.exe tools\update_project_reference.py --run-tests --pytest-args "-m 'not slow'"

Creates (default):

    docs/PROJECT_COMPLETE_REFERENCE.md     full human/AI-readable snapshot
    docs/PROJECT_COMPLETE_REFERENCE.json   machine-readable summary
    docs/project_reference_parts/          the same Markdown split into parts
                                           (default 1 MB each; --no-split to disable)

What the snapshot contains
--------------------------
1.  Git state: branch, commit, remote, status, recent log, diff stat and the
    full diff of uncommitted changes (capped).
2.  Full path inventory of the working folder, including ignored and local
    folders (data/, outputs/, models/, reports/), with size, modification time
    and Git state. File contents of data are never copied.
3.  Full source of every relevant text file: .py, .ipynb, .md, .yaml, .yml,
    .toml, .json, .csv (capped), .txt, .ini, .cfg, .ps1, .sh, .sql, etc.
4.  Notebooks: every cell source, execution counts and, by default, the TEXT
    outputs (streams, text/plain results, errors and tracebacks). Images and
    HTML are replaced by placeholders. Execution order problems are reported.
5.  Small text artifacts produced by the project (manifests, waterfalls,
    summary tables under outputs/, reports/, data/ manifests), capped by size
    and number of CSV rows. Prediction folders are never included.
6.  Text extracted from .docx and .pptx documents (plans, reports).
7.  Python environment: interpreter, platform and every installed package
    version (scikit-learn, pandas, numpy, ...).
8.  Parsed configuration: full YAML summary, gates table, duplicate YAML keys,
    pyproject.toml validity and dependency lists.
9.  Static API catalog: every module, function, class, method, signature,
    docstring, consumers and tests.
10. Static diagnostics ("attention report"), including:
    - internal imports of modules or names that do not exist;
    - calls to project functions with keyword arguments they do not accept
      or with too many positional arguments;
    - gate names used in code/docs that are absent from the YAML;
    - YAML keys never referenced by code (possible dead configuration);
    - feature contract problems (forbidden features, derived features);
    - third-party imports missing from requirements.txt/pyproject.toml and
      unpinned dependencies;
    - duplicated symbols and notebook-local functions duplicating src/;
    - notebooks executed out of order, never executed, or with saved errors;
    - documents pointing to paths that do not exist;
    - mojibake/encoding problems; TODO/FIXME markers;
    - untracked relevant files.
11. Optional: pytest results (--run-tests). This is the only option that
    imports and executes project code.

Safety
------
Secrets and credentials are redacted. Absolute local paths are replaced by
<REPO> and <HOME>. .env files and binary data (Parquet, models, images) are
never copied. Notebook outputs can be disabled with --no-notebook-outputs.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.metadata as importlib_metadata
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None

try:
    import tomllib  # Python 3.11+
except Exception:  # pragma: no cover
    tomllib = None

SCHEMA_VERSION = 4

OUTPUT_DIR = Path("docs")
OUTPUT_MD_NAME = "PROJECT_COMPLETE_REFERENCE.md"
OUTPUT_JSON_NAME = "PROJECT_COMPLETE_REFERENCE.json"
PARTS_DIR_NAME = "project_reference_parts"

DEFAULT_MAX_INLINE_BYTES = 4_000_000
DEFAULT_MAX_OUTPUT_CHARS = 6_000
DEFAULT_MAX_ARTIFACT_BYTES = 300_000
DEFAULT_MAX_CSV_ROWS = 60
DEFAULT_MAX_DIFF_CHARS = 400_000
DEFAULT_GIT_LOG = 40
DEFAULT_SPLIT_MB = 1.0
MAX_INVENTORY_ENTRIES = 30_000
MAX_DOCSTRING_CHARS = 4_000
MAX_SOURCE_LINES_PER_LARGE_NOTEBOOK_CELL = 200

# Never walked (tooling, caches, virtual environments).
EXCLUDED_DIRS_ANYWHERE = {
    ".git", ".venv", "venv", "env", ".env", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", ".tox", ".nox", ".ipynb_checkpoints",
    "node_modules", ".idea", ".vscode", "site-packages", ".eggs",
    "build", "dist",
}
# Walked for the path inventory and small text artifacts, never as source.
ARTIFACT_DIRS_AT_ROOT = {
    "data", "outputs", "models", "logs", "artifacts", "mlruns", "reports",
}
# Never copied, even when small and textual.
ARTIFACT_EXCLUDED_DIR_NAMES = {"predictions", "predicoes", "raw", "cache", "tmp"}
EXCLUDED_FILES = {
    ".env", "pip_inspect-venv.json", OUTPUT_MD_NAME, OUTPUT_JSON_NAME,
}
# Files whose existence and keys are reported, but whose values are redacted.
KEYS_ONLY_FILES = {"paths.local.json"}

TEXT_SUFFIXES = {
    ".py", ".pyi", ".md", ".rst", ".txt", ".yaml", ".yml", ".toml", ".ini",
    ".cfg", ".json", ".json5", ".sql", ".ps1", ".psm1", ".sh", ".bat",
    ".cmd", ".csv", ".tsv", ".html", ".css", ".js", ".r", ".R",
}
ARTIFACT_TEXT_SUFFIXES = {".json", ".yaml", ".yml", ".md", ".txt", ".csv", ".tsv", ".log"}
OFFICE_SUFFIXES = {".docx", ".pptx"}
SPECIAL_NAMES = {
    "README", "LICENSE", "Makefile", "Dockerfile", "requirements.txt",
    "pyproject.toml", "pytest.ini", "setup.cfg", "tox.ini", ".env.example",
    ".gitignore", ".gitattributes", ".pre-commit-config.yaml", "environment.yml",
}
LANG = {
    ".py": "python", ".pyi": "python", ".md": "markdown", ".rst": "rst",
    ".yaml": "yaml", ".yml": "yaml", ".toml": "toml", ".json": "json",
    ".json5": "json5", ".ini": "ini", ".cfg": "ini", ".sql": "sql",
    ".ps1": "powershell", ".psm1": "powershell", ".sh": "bash", ".bat": "bat",
    ".cmd": "bat", ".csv": "csv", ".tsv": "tsv", ".html": "html", ".css": "css",
    ".js": "javascript", ".log": "text", ".r": "r",
}
LIKELY_BINARY_SUFFIXES = {
    ".parquet", ".feather", ".arrow", ".pkl", ".pickle", ".joblib", ".onnx",
    ".pt", ".pth", ".h5", ".hdf5", ".npy", ".npz", ".pdf", ".doc", ".ppt",
    ".xls", ".xlsx", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".zip",
    ".7z", ".gz", ".tar", ".bz2", ".xz", ".dbf", ".db", ".sqlite", ".exe", ".dll",
}
IMPORTANT_UNTRACKED_PREFIXES = (
    "src/", "tests/", "configs/", "docs/", "notebooks/", "tools/", "scripts/",
)

# Import name -> distribution name, for the dependency check.
IMPORT_TO_DIST = {
    "sklearn": "scikit-learn", "yaml": "pyyaml", "dotenv": "python-dotenv",
    "PIL": "pillow", "cv2": "opencv-python", "bs4": "beautifulsoup4",
    "docx": "python-docx", "pptx": "python-pptx", "dateutil": "python-dateutil",
    "IPython": "ipython", "jwt": "pyjwt", "skimage": "scikit-image",
    "google": "google-api-python-client", "snowflake": "snowflake-connector-python",
}
KEY_PACKAGES = (
    "scikit-learn", "pandas", "numpy", "scipy", "pyarrow", "pyyaml", "joblib",
    "matplotlib", "seaborn", "python-dotenv", "requests", "pytest",
    "ipykernel", "jupyter", "nbformat", "statsmodels", "shap",
)

ENV_RE = re.compile(
    r"(?:os\.getenv|os\.environ\.get|os\.environ\[|get_env|get_secret|getenv)"
    r"\(?\s*['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]"
)
SECRET_RE = re.compile(
    r"(?im)^(\s*[A-Za-z_][A-Za-z0-9_.-]*?"
    r"(?:token|secret|password|passwd|pwd|api[_-]?key|private[_-]?key|credential)"
    r"[A-Za-z0-9_.-]*\s*[:=]\s*)([^\n#]+)"
)
PRIVATE_KEY_RE = re.compile(
    r"-----BEGIN [^-]+ PRIVATE KEY-----.*?-----END [^-]+ PRIVATE KEY-----",
    re.DOTALL,
)
URL_CREDENTIAL_RE = re.compile(r"(?i)(https?://[^\s/:]+:)([^@\s]+)(@)")
GITHUB_TOKEN_RE = re.compile(r"\b(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b")
WINDOWS_USER_RE = re.compile(r"(?i)\b[A-Z]:[\\/]+Users[\\/]+[^\\/\s\"'<>|]+")
POSIX_HOME_RE = re.compile(r"(?<![A-Za-z0-9_])/(?:home|Users)/[^/\s\"'<>|]+")
ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
BACKTICK_RUN_RE = re.compile(r"`+")
HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
FILE_LITERAL_RE = re.compile(
    r"['\"]([^'\"\n]+\.(?:parquet|csv|json|yaml|yml|joblib|pkl|png|jpg|md|html|txt))['\"]",
    re.IGNORECASE,
)
GATE_RE = re.compile(r"\bG\d+_[A-Za-z0-9_]+\b")
TODO_RE = re.compile(r"(?i)\b(TODO|FIXME|XXX|HACK|PENDENTE)\b[:\s-]*(.{0,140})")
MOJIBAKE_RE = re.compile(r"(?:├|┤|Ã[\u0080-\u00BF¡-¿]|Â[\u00A0-\u00BF ]|â€|\uFFFD)")

CONTEXT = """# Project Complete Reference

> **Generated file. Do not edit manually.**
> Generated by `tools/update_project_reference.py` (schema v{schema}).
> Static snapshot of the repository and of the local working folder.

## 1. Purpose

This reference lets a person or an AI diagnose the SRAG project without prior
conversation context and without access to the machine. It contains the full
source of code, notebooks (with text outputs), configuration and documentation,
plus the Git state, the local path inventory, installed package versions,
parsed configuration and static consistency checks.

## 2. Methodological guardrails

- Academic retrospective prediction project, not a clinically validated tool.
- Prediction time is hospital admission; later information cannot be a feature.
- Do not make causal claims from predictive associations.
- Never use the final test partition for model, hyperparameter, calibration or
  threshold selection.
- Partition, target, features, seed, calibration, threshold and gates come from
  `configs/supervised.yaml` and executable tests.
- Original data, Parquets, trained models, secrets and local paths are never
  copied into this reference (only their paths, sizes and dates).

## 3. How to use this reference (any AI)

1. Read Sections 6 (executive map) and 7 (attention report).
2. Check Section 8 (configuration and gates) and Section 9 (environment).
3. Search Section 12 (API catalog) before proposing any new function.
4. Check Sections 13 to 15 for imports, tests and notebook orchestration.
5. Read the exact implementation in Section 17 (full source).
6. Use Section 18 (artifacts) and notebook outputs as evidence of what was
   actually executed; use Section 10 (inventory) to know what exists locally.
7. If code, configuration, tests, notebooks and plans disagree, report the
   conflict explicitly; never choose silently.

## 4. Evidence precedence

1. Current executable code and tests.
2. Active configuration and explicit decision records.
3. Notebook sources and saved outputs (outputs may be stale: check execution
   counts and artifact dates).
4. Generated artifacts (manifests, tables).
5. Older plans and roadmaps (historical intent only).

## 5. Status vocabulary

- **Implemented:** executable code exists in the current snapshot.
- **Configured:** an active value, rule or gate exists in configuration.
- **Tested / Consumed:** a static reference was found in tests / other code.
- **Working tree:** relevant but not tracked in the current commit.
- **Local only:** exists in the folder but is ignored by Git.
- **Attention:** mismatch, duplication risk, stale reference or broken contract.
"""


@dataclass
class GitEntry:
    path: str
    tracked: bool
    status: str = ""
    exists: bool = True


@dataclass
class CallSite:
    name: str
    location: str
    keywords: list[str]
    n_positional: int
    has_star_args: bool
    has_star_kwargs: bool


@dataclass
class Symbol:
    module: str
    path: str
    qualname: str
    name: str
    kind: str
    signature: str
    lineno: int
    end_lineno: int | None
    docstring: str
    decorators: list[str] = field(default_factory=list)
    calls: list[str] = field(default_factory=list)
    env_vars: list[str] = field(default_factory=list)
    file_literals: list[str] = field(default_factory=list)
    is_private: bool = False
    params: list[str] = field(default_factory=list)
    n_positional_params: int = 0
    has_varargs: bool = False
    has_varkw: bool = False
    defaults: dict[str, str] = field(default_factory=dict)


@dataclass
class PythonFileAnalysis:
    path: str
    module: str
    docstring: str
    parse_error: str | None
    imports: list[str]
    internal_imports: list[str]
    external_imports: list[str]
    import_from: list[dict[str, Any]]
    calls: list[str]
    call_sites: list[CallSite]
    symbols: list[Symbol]
    top_level_names: list[str]
    constants: dict[str, str]
    env_vars: list[str]
    file_literals: list[str]
    has_star_import: bool = False
    lines: int = 0


@dataclass
class NotebookAnalysis:
    path: str
    cells: int
    code_cells: int
    markdown_cells: int
    kernel: dict[str, Any]
    language_version: str
    headings: list[str]
    imports: list[str]
    internal_imports: list[str]
    import_from: list[dict[str, Any]]
    functions: list[Symbol]
    classes: list[Symbol]
    assignments: list[str]
    file_literals: list[str]
    env_vars: list[str]
    parse_errors: list[str]
    call_sites: list[CallSite]
    code_lines: int
    executed_cells: int
    execution_counts: list[int | None]
    out_of_order: bool
    error_outputs: list[str]
    outputs_included: bool


@dataclass
class Attention:
    severity: str
    category: str
    message: str
    evidence: list[str] = field(default_factory=list)
    recommendation: str = ""


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

def run_command(
    args: list[str],
    *,
    cwd: Path,
    check: bool = True,
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    if check and result.returncode:
        raise RuntimeError(
            result.stderr.strip() or result.stdout.strip()
            or f"Command failed: {' '.join(args)}"
        )
    return result


def git(root: Path, *args: str, check: bool = True) -> str:
    return run_command(["git", "-c", "core.quotepath=false", *args], cwd=root, check=check).stdout


def root_dir() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if result.returncode:
        raise RuntimeError("Run inside the Git repository.")
    return Path(result.stdout.strip()).resolve()


def module_name(path: Path) -> str:
    parts = list(path.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def human_bytes(value: int) -> str:
    size = float(value)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{value} B"


class Redactor:
    """Removes secrets and replaces absolute local paths."""

    def __init__(self, root: Path) -> None:
        variants = {str(root), root.as_posix(), str(root).replace("\\", "\\\\")}
        self.root_variants = sorted((v for v in variants if v), key=len, reverse=True)
        home = Path.home()
        self.home_variants = sorted(
            {str(home), home.as_posix(), str(home).replace("\\", "\\\\")}, key=len, reverse=True
        )

    def __call__(self, text: str) -> tuple[str, list[str]]:
        warnings: list[str] = []
        if PRIVATE_KEY_RE.search(text):
            text = PRIVATE_KEY_RE.sub("[REDACTED_PRIVATE_KEY]", text)
            warnings.append("private key redacted")
        if GITHUB_TOKEN_RE.search(text):
            text = GITHUB_TOKEN_RE.sub("[REDACTED_TOKEN]", text)
            warnings.append("token redacted")
        if SECRET_RE.search(text):
            text = SECRET_RE.sub(r"\1[REDACTED]", text)
            warnings.append("possible secret assignment redacted")
        if URL_CREDENTIAL_RE.search(text):
            text = URL_CREDENTIAL_RE.sub(r"\1[REDACTED]\3", text)
            warnings.append("credentials in URL redacted")
        for value in self.root_variants:
            text = text.replace(value, "<REPO>")
        for value in self.home_variants:
            text = text.replace(value, "<HOME>")
        text = WINDOWS_USER_RE.sub("<HOME>", text)
        text = POSIX_HOME_RE.sub("<HOME>", text)
        return text, warnings


def fence_for(text: str) -> str:
    longest = max((len(m.group(0)) for m in BACKTICK_RUN_RE.finditer(text)), default=0)
    return "`" * max(3, longest + 1)


def code_block(text: str, lexer: str = "text") -> str:
    fence = fence_for(text)
    return f"{fence}{lexer}\n{text}\n{fence}"


def truncate(text: str, limit: int, label: str = "characters") -> str:
    if limit <= 0 or len(text) <= limit:
        return text
    head = text[: int(limit * 0.7)]
    tail = text[-int(limit * 0.3):]
    return f"{head}\n... [{len(text) - len(head) - len(tail)} {label} omitted] ...\n{tail}"


def safe_unparse(node: ast.AST | None, default: str = "") -> str:
    if node is None:
        return default
    try:
        return ast.unparse(node)
    except Exception:
        return default or "..."


def literal_preview(node: ast.AST, max_chars: int = 300) -> str:
    try:
        text = repr(ast.literal_eval(node))
    except Exception:
        text = safe_unparse(node, "<dynamic>")
    return text if len(text) <= max_chars else text[: max_chars - 3] + "..."


def dotted_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = dotted_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    if isinstance(node, ast.Call):
        return dotted_name(node.func)
    return None


def env_names(text: str) -> list[str]:
    return sorted(set(ENV_RE.findall(text)))


def file_literals(text: str) -> list[str]:
    return sorted({m.group(1) for m in FILE_LITERAL_RE.finditer(text)})


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = text.encode("utf-8")
    if path.exists() and path.read_bytes() == data:
        return
    with tempfile.NamedTemporaryFile("wb", delete=False, dir=path.parent) as handle:
        handle.write(data)
        temporary = Path(handle.name)
    temporary.replace(path)


# ---------------------------------------------------------------------------
# Git and filesystem inventory
# ---------------------------------------------------------------------------

def parse_porcelain_status(root: Path) -> dict[str, str]:
    raw = git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    items = raw.split("\0")
    status: dict[str, str] = {}
    i = 0
    while i < len(items):
        item = items[i]
        if not item:
            i += 1
            continue
        code, path_text = item[:2], item[3:]
        if code[0] in {"R", "C"} and i + 1 < len(items):
            status[path_text] = code
            i += 2
        else:
            status[path_text] = code
            i += 1
    return status


def collect_git_entries(root: Path) -> tuple[list[GitEntry], set[str], set[str]]:
    status_map = parse_porcelain_status(root)
    tracked = {line.strip() for line in git(root, "ls-files").splitlines() if line.strip()}
    untracked = {
        line.strip()
        for line in git(root, "ls-files", "--others", "--exclude-standard").splitlines()
        if line.strip()
    }
    entries = [
        GitEntry(
            path=Path(value).as_posix(),
            tracked=value in tracked,
            status=status_map.get(value, ""),
            exists=(root / value).is_file(),
        )
        for value in sorted(tracked | untracked, key=str.lower)
    ]
    return entries, tracked, untracked


def walk_inventory(
    root: Path,
    tracked: set[str],
    untracked: set[str],
) -> tuple[list[dict[str, Any]], bool]:
    """All files in the working folder, except tooling/caches/venvs."""
    rows: list[dict[str, Any]] = []
    truncated = False
    for current, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDED_DIRS_ANYWHERE)
        for name in sorted(files):
            absolute = Path(current) / name
            rel = absolute.relative_to(root).as_posix()
            try:
                stat = absolute.stat()
            except OSError:
                continue
            if rel in tracked:
                state = "tracked"
            elif rel in untracked:
                state = "untracked"
            else:
                state = "ignored"
            rows.append(
                {
                    "path": rel,
                    "git": state,
                    "bytes": stat.st_size,
                    "modified_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc)
                    .strftime("%Y-%m-%d %H:%M"),
                }
            )
            if len(rows) >= MAX_INVENTORY_ENTRIES:
                return rows, True
    return rows, truncated


def is_artifact_path(path: Path) -> bool:
    return bool(path.parts) and path.parts[0] in ARTIFACT_DIRS_AT_ROOT


def include_source(path: Path, *, tracked: bool) -> bool:
    parts = path.parts
    if any(part in EXCLUDED_DIRS_ANYWHERE for part in parts):
        return False
    if is_artifact_path(path):
        return False
    if path.name in EXCLUDED_FILES or path.parent.name == PARTS_DIR_NAME:
        return False
    if path.name.startswith(".env") and path.name != ".env.example":
        return False
    if not tracked and not path.as_posix().startswith(IMPORTANT_UNTRACKED_PREFIXES):
        if len(parts) != 1:  # untracked root files (pyproject, README) are allowed
            return False
    suffix = path.suffix.lower()
    return (
        suffix in TEXT_SUFFIXES
        or suffix == ".ipynb"
        or suffix in OFFICE_SUFFIXES
        or path.name in SPECIAL_NAMES
        or path.name in KEYS_ONLY_FILES
    )


def include_artifact(path: Path, size: int, max_bytes: int) -> bool:
    if not is_artifact_path(path):
        return False
    if any(part.lower() in ARTIFACT_EXCLUDED_DIR_NAMES for part in path.parts):
        return False
    if path.name.startswith(".env"):
        return False
    if path.suffix.lower() not in ARTIFACT_TEXT_SUFFIXES:
        return False
    # Raw/large CSVs are only previewed (head), so allow them up to 50x.
    limit = max_bytes * 50 if path.suffix.lower() in {".csv", ".tsv"} else max_bytes
    return size <= limit


# ---------------------------------------------------------------------------
# Python AST analysis
# ---------------------------------------------------------------------------

def imported_names(tree: ast.AST) -> tuple[list[str], list[dict[str, Any]], bool]:
    imports: set[str] = set()
    froms: list[dict[str, Any]] = []
    star = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            prefix = "." * node.level + (node.module or "")
            names = [alias.name for alias in node.names]
            if "*" in names:
                star = True
            froms.append(
                {"module": prefix, "names": names, "lineno": getattr(node, "lineno", 0)}
            )
            for name in names:
                imports.add(f"{prefix}.{name}".strip("."))
    return sorted(imports), froms, star


def call_names(tree: ast.AST) -> list[str]:
    return sorted(
        {
            name
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            for name in [dotted_name(node.func)]
            if name
        }
    )


def call_sites(tree: ast.AST, label: str) -> list[CallSite]:
    sites: list[CallSite] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = dotted_name(node.func)
        if not name:
            continue
        sites.append(
            CallSite(
                name=name,
                location=f"{label}:{getattr(node, 'lineno', 0)}",
                keywords=[kw.arg for kw in node.keywords if kw.arg],
                n_positional=sum(not isinstance(a, ast.Starred) for a in node.args),
                has_star_args=any(isinstance(a, ast.Starred) for a in node.args),
                has_star_kwargs=any(kw.arg is None for kw in node.keywords),
            )
        )
    return sites


def top_level_names(tree: ast.Module) -> list[str]:
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                for sub in ast.walk(target):
                    if isinstance(sub, ast.Name):
                        names.add(sub.id)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                names.add((alias.asname or alias.name).split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.add(alias.asname or alias.name)
        elif isinstance(node, (ast.If, ast.Try)):
            # Conditional definitions (try/except ImportError, if TYPE_CHECKING)
            for sub in ast.walk(node):
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    names.add(sub.name)
                elif isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Store):
                    names.add(sub.id)
                elif isinstance(sub, ast.alias):
                    names.add((sub.asname or sub.name).split(".")[0])
    return sorted(names)


def assigned_constants(tree: ast.Module) -> dict[str, str]:
    constants: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id.isupper():
                constants[target.id] = literal_preview(node.value)
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id.isupper() and node.value:
                constants[node.target.id] = literal_preview(node.value)
    return constants


def function_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
    returns = f" -> {safe_unparse(node.returns)}" if node.returns else ""
    return f"{prefix} {node.name}({safe_unparse(node.args, '...')}){returns}"


def extract_symbol(
    node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef,
    *,
    path: Path,
    module: str,
    text: str,
    parent: str = "",
) -> Symbol:
    qualname = f"{parent}.{node.name}" if parent else node.name
    params: list[str] = []
    n_pos = 0
    has_varargs = has_varkw = False
    defaults: dict[str, str] = {}
    if isinstance(node, ast.ClassDef):
        signature, kind = f"class {node.name}({', '.join(safe_unparse(b) for b in node.bases)})", "class"
        # A class call uses __init__ (or dataclass fields): handled loosely.
        init = next(
            (
                child for child in node.body
                if isinstance(child, ast.FunctionDef) and child.name == "__init__"
            ),
            None,
        )
        if init is not None:
            args = init.args
            positional = [a.arg for a in args.posonlyargs + args.args][1:]
            params = positional + [a.arg for a in args.kwonlyargs]
            n_pos = len(positional)
            has_varargs = args.vararg is not None
            has_varkw = args.kwarg is not None
        else:
            has_varargs = has_varkw = True  # unknown (dataclass, inheritance)
    else:
        signature = function_signature(node)
        kind = "method" if parent else "function"
        args = node.args
        positional = [a.arg for a in args.posonlyargs + args.args]
        if parent and positional and positional[0] in {"self", "cls"}:
            positional = positional[1:]
        params = positional + [a.arg for a in args.kwonlyargs]
        n_pos = len(positional)
        has_varargs = args.vararg is not None
        has_varkw = args.kwarg is not None
        pos_defaults = args.defaults
        for arg, default in zip((args.posonlyargs + args.args)[-len(pos_defaults):] if pos_defaults else [], pos_defaults):
            defaults[arg.arg] = literal_preview(default, 120)
        for arg, default in zip(args.kwonlyargs, args.kw_defaults):
            if default is not None:
                defaults[arg.arg] = literal_preview(default, 120)
    doc = (ast.get_docstring(node) or "").strip()
    if len(doc) > MAX_DOCSTRING_CHARS:
        doc = doc[: MAX_DOCSTRING_CHARS - 3] + "..."
    segment = ast.get_source_segment(text, node) or ""
    return Symbol(
        module=module,
        path=path.as_posix(),
        qualname=qualname,
        name=node.name,
        kind=kind,
        signature=signature,
        lineno=node.lineno,
        end_lineno=getattr(node, "end_lineno", None),
        docstring=doc,
        decorators=[safe_unparse(d) for d in node.decorator_list],
        calls=call_names(node),
        env_vars=env_names(segment),
        file_literals=file_literals(segment),
        is_private=node.name.startswith("_"),
        params=params,
        n_positional_params=n_pos,
        has_varargs=has_varargs,
        has_varkw=has_varkw,
        defaults=defaults,
    )


def analyze_python(path: Path, text: str, internal_roots: set[str]) -> PythonFileAnalysis:
    module = module_name(path)
    lines = len(text.splitlines())
    try:
        tree = ast.parse(text, filename=path.as_posix())
    except SyntaxError as exc:
        return PythonFileAnalysis(
            path=path.as_posix(), module=module, docstring="", parse_error=str(exc),
            imports=[], internal_imports=[], external_imports=[], import_from=[],
            calls=[], call_sites=[], symbols=[], top_level_names=[], constants={},
            env_vars=env_names(text), file_literals=file_literals(text), lines=lines,
        )
    imports, froms, star = imported_names(tree)
    internal = sorted(v for v in imports if v.split(".")[0] in internal_roots or v.startswith("."))
    external = sorted(set(imports) - set(internal))
    symbols: list[Symbol] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            symbols.append(extract_symbol(node, path=path, module=module, text=text))
            if isinstance(node, ast.ClassDef):
                for child in node.body:
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        symbols.append(
                            extract_symbol(child, path=path, module=module, text=text, parent=node.name)
                        )
    return PythonFileAnalysis(
        path=path.as_posix(),
        module=module,
        docstring=(ast.get_docstring(tree) or "").strip(),
        parse_error=None,
        imports=imports,
        internal_imports=internal,
        external_imports=external,
        import_from=froms,
        calls=call_names(tree),
        call_sites=call_sites(tree, path.as_posix()),
        symbols=symbols,
        top_level_names=top_level_names(tree),
        constants=assigned_constants(tree),
        env_vars=env_names(text),
        file_literals=file_literals(text),
        has_star_import=star,
        lines=lines,
    )


# ---------------------------------------------------------------------------
# Notebooks
# ---------------------------------------------------------------------------

def strip_magics(source: str) -> str:
    """Comment out IPython magics/shell lines so the cell can be parsed."""
    lines = []
    for line in source.splitlines():
        stripped = line.lstrip()
        if stripped.startswith(("%", "!", "?")) or stripped.endswith("?"):
            lines.append("# " + line)
        else:
            lines.append(line)
    return "\n".join(lines)


def render_output(output: dict[str, Any], max_chars: int, redactor: Redactor) -> tuple[str, str]:
    """Return (kind, text) for one notebook output."""
    kind = output.get("output_type", "unknown")
    if kind == "stream":
        text = "".join(output.get("text", []))
        label = f"stream:{output.get('name', 'stdout')}"
    elif kind in {"execute_result", "display_data"}:
        data = output.get("data", {})
        omitted = [mime for mime in data if mime != "text/plain"]
        text = "".join(data.get("text/plain", []))
        if omitted:
            text += ("\n" if text else "") + f"[non-text output omitted: {', '.join(sorted(omitted))}]"
        label = kind
    elif kind == "error":
        trace = "\n".join(output.get("traceback", []))
        text = f"{output.get('ename', '')}: {output.get('evalue', '')}\n{trace}"
        label = "error"
    else:
        text, label = json.dumps(output)[:500], kind
    text = ANSI_RE.sub("", text)
    text, _ = redactor(text)
    return label, truncate(text.rstrip(), max_chars)


def analyze_notebook(
    path: Path,
    data: bytes,
    internal_roots: set[str],
) -> tuple[NotebookAnalysis, dict[str, Any]]:
    nb = json.loads(data.decode("utf-8-sig"))
    headings: list[str] = []
    imports: set[str] = set()
    internal_imports: set[str] = set()
    froms: list[dict[str, Any]] = []
    functions: list[Symbol] = []
    classes: list[Symbol] = []
    assignments: set[str] = set()
    literals: set[str] = set()
    envs: set[str] = set()
    parse_errors: list[str] = []
    sites: list[CallSite] = []
    errors: list[str] = []
    counts: list[int | None] = []
    code_lines = code_cells = markdown_cells = executed = 0
    for number, cell in enumerate(nb.get("cells", []), 1):
        kind = cell.get("cell_type", "unknown")
        source = "".join(cell.get("source", []))
        if kind == "markdown":
            markdown_cells += 1
            headings.extend(title.strip() for _, title in HEADING_RE.findall(source))
            continue
        if kind != "code":
            continue
        code_cells += 1
        code_lines += len(source.splitlines())
        count = cell.get("execution_count")
        counts.append(count)
        if count is not None:
            executed += 1
        for output in cell.get("outputs", []):
            if output.get("output_type") == "error":
                errors.append(f"cell {number}: {output.get('ename', '')}: {str(output.get('evalue', ''))[:200]}")
        label = f"{path.as_posix()}#cell-{number}"
        try:
            tree = ast.parse(strip_magics(source), filename=label)
        except SyntaxError as exc:
            parse_errors.append(f"Cell {number}: {exc}")
            continue
        cell_imports, cell_froms, _ = imported_names(tree)
        imports.update(cell_imports)
        internal_imports.update(v for v in cell_imports if v.split(".")[0] in internal_roots)
        for item in cell_froms:
            froms.append({**item, "cell": number})
        sites.extend(call_sites(tree, label))
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(extract_symbol(node, path=Path(label), module=f"notebook:{path.as_posix()}", text=source))
            elif isinstance(node, ast.ClassDef):
                classes.append(extract_symbol(node, path=Path(label), module=f"notebook:{path.as_posix()}", text=source))
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    if isinstance(target, ast.Name) and (
                        target.id.isupper() or target.id.lower().endswith(("_dir", "_path", "_file"))
                    ):
                        assignments.add(target.id)
        literals.update(file_literals(source))
        envs.update(env_names(source))
    numeric = [c for c in counts if c is not None]
    out_of_order = any(b < a for a, b in zip(numeric, numeric[1:]))
    meta = nb.get("metadata", {})
    analysis = NotebookAnalysis(
        path=path.as_posix(),
        cells=len(nb.get("cells", [])),
        code_cells=code_cells,
        markdown_cells=markdown_cells,
        kernel=meta.get("kernelspec", {}),
        language_version=str(meta.get("language_info", {}).get("version", "")),
        headings=headings,
        imports=sorted(imports),
        internal_imports=sorted(internal_imports),
        import_from=froms,
        functions=functions,
        classes=classes,
        assignments=sorted(assignments),
        file_literals=sorted(literals),
        env_vars=sorted(envs),
        parse_errors=parse_errors,
        call_sites=sites,
        code_lines=code_lines,
        executed_cells=executed,
        execution_counts=counts,
        out_of_order=out_of_order,
        error_outputs=errors,
        outputs_included=False,
    )
    return analysis, nb


def notebook_source_markdown(
    nb: dict[str, Any],
    analysis: NotebookAnalysis,
    *,
    include_outputs: bool,
    max_output_chars: int,
    reduced: bool,
    redactor: Redactor,
) -> str:
    parts: list[str] = [
        f"- Cells: `{analysis.cells}` (`{analysis.code_cells}` code, `{analysis.markdown_cells}` markdown)",
        f"- Code cells executed: `{analysis.executed_cells}` of `{analysis.code_cells}`"
        + (" — **executed out of order**" if analysis.out_of_order else ""),
        f"- Kernel: `{analysis.kernel.get('display_name', '')}`; Python `{analysis.language_version}`",
        f"- Outputs: `{'text outputs included' if include_outputs else 'omitted'}`"
        + ("; **reduced view** (notebook above size limit)" if reduced else ""),
        "",
    ]
    for number, cell in enumerate(nb.get("cells", []), 1):
        kind = cell.get("cell_type", "unknown")
        source, _ = redactor("".join(cell.get("source", [])).rstrip())
        if kind == "code":
            count = cell.get("execution_count")
            if reduced:
                lines = source.splitlines()
                if len(lines) > MAX_SOURCE_LINES_PER_LARGE_NOTEBOOK_CELL:
                    source = "\n".join(lines[:MAX_SOURCE_LINES_PER_LARGE_NOTEBOOK_CELL]) + (
                        f"\n# ... {len(lines) - MAX_SOURCE_LINES_PER_LARGE_NOTEBOOK_CELL} lines omitted ..."
                    )
            parts.append(f"### Cell {number} [code] · In [{count if count is not None else ' '}]")
            parts.append("")
            parts.append(code_block(source, "python"))
            if include_outputs:
                for out_index, output in enumerate(cell.get("outputs", []), 1):
                    label, text = render_output(output, max_output_chars, redactor)
                    if not text:
                        continue
                    parts.append("")
                    parts.append(f"**Output {out_index} ({label})**")
                    parts.append("")
                    parts.append(code_block(text, "text"))
        else:
            parts.append(f"### Cell {number} [{kind}]")
            parts.append("")
            parts.append(code_block(source, "markdown"))
        parts.append("")
    return "\n".join(parts).rstrip()


# ---------------------------------------------------------------------------
# Office documents and artifacts
# ---------------------------------------------------------------------------

def office_text(data: bytes, suffix: str) -> str:
    """Plain text of .docx/.pptx using only the standard library."""
    import io
    from xml.etree import ElementTree as ET

    texts: list[str] = []
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        if suffix == ".docx":
            names = ["word/document.xml"]
        else:
            names = sorted(
                (n for n in archive.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)),
                key=lambda n: int(re.findall(r"\d+", n)[-1]),
            )
        for index, name in enumerate(names, 1):
            if name not in archive.namelist():
                continue
            root = ET.fromstring(archive.read(name))
            if suffix == ".pptx":
                texts.append(f"--- slide {index} ---")
            for paragraph in root.iter():
                tag = paragraph.tag.rsplit("}", 1)[-1]
                if tag == "p":
                    line = "".join(
                        (node.text or "")
                        for node in paragraph.iter()
                        if node.tag.rsplit("}", 1)[-1] in {"t", "tab"}
                    ).strip()
                    if line:
                        texts.append(line)
                elif tag == "tr" and suffix == ".docx":
                    pass
    return "\n".join(texts)


def csv_preview(text: str, max_rows: int) -> tuple[str, int]:
    lines = text.splitlines()
    total = max(0, len(lines) - 1)
    if len(lines) <= max_rows + 1:
        return text, total
    return "\n".join(lines[: max_rows + 1]) + f"\n... [{total - max_rows} more rows omitted]", total


def keys_only_json(text: str) -> str:
    try:
        data = json.loads(text)
    except Exception:
        return "[could not parse; values hidden]"

    def mask(value: Any) -> Any:
        if isinstance(value, dict):
            return {k: mask(v) for k, v in value.items()}
        if isinstance(value, list):
            return [mask(v) for v in value[:5]]
        return f"<{type(value).__name__}>"

    return json.dumps(mask(data), ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Configuration, environment and dependency files
# ---------------------------------------------------------------------------

def flatten_mapping(value: Any, prefix: str = "") -> dict[str, Any]:
    result: dict[str, Any] = {}
    if isinstance(value, dict) and value:
        for key, child in value.items():
            new_prefix = f"{prefix}.{key}" if prefix else str(key)
            result.update(flatten_mapping(child, new_prefix))
    else:
        result[prefix] = value
    return result


def nested_get(mapping: Any, *keys: str, default: Any = None) -> Any:
    current = mapping
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def load_yaml_strict(text: str) -> tuple[Any | None, str | None, list[str]]:
    """Parse YAML; also report duplicated keys (safe_load silently keeps the last)."""
    if yaml is None:
        return None, "PyYAML not available", []
    duplicates: list[str] = []

    class DupLoader(yaml.SafeLoader):  # type: ignore[misc]
        pass

    def construct_mapping(loader: Any, node: Any, deep: bool = False) -> Any:
        seen: set[Any] = set()
        for key_node, _ in node.value:
            key = loader.construct_object(key_node, deep=deep)
            if key in seen:
                duplicates.append(f"{key!r} (line {key_node.start_mark.line + 1})")
            seen.add(key)
        return yaml.SafeLoader.construct_mapping(loader, node, deep=deep)

    DupLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping)
    try:
        return yaml.load(text, Loader=DupLoader), None, duplicates  # noqa: S506
    except Exception as exc:
        return None, repr(exc), duplicates


def parse_requirements(text: str) -> dict[str, str]:
    deps: dict[str, str] = {}
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or line.startswith(("-", "git+", "http")):
            continue
        match = re.match(r"([A-Za-z0-9_.\-\[\]]+)\s*(.*)", line)
        if match:
            name = re.sub(r"\[.*\]", "", match.group(1)).lower().replace("_", "-")
            deps[name] = match.group(2).strip()
    return deps


def parse_pyproject(text: str) -> tuple[dict[str, Any] | None, str | None]:
    if tomllib is None:
        return None, "tomllib unavailable (Python < 3.11)"
    try:
        return tomllib.loads(text), None
    except Exception as exc:
        return None, repr(exc)


def pyproject_dependencies(data: dict[str, Any]) -> dict[str, str]:
    deps: dict[str, str] = {}
    values = list(nested_get(data, "project", "dependencies", default=[]) or [])
    for group in (nested_get(data, "project", "optional-dependencies", default={}) or {}).values():
        values.extend(group or [])
    for item in values:
        match = re.match(r"([A-Za-z0-9_.\-\[\]]+)\s*(.*)", str(item))
        if match:
            name = re.sub(r"\[.*\]", "", match.group(1)).lower().replace("_", "-")
            deps[name] = match.group(2).strip()
    return deps


def installed_packages() -> dict[str, str]:
    packages: dict[str, str] = {}
    for dist in importlib_metadata.distributions():
        try:
            name = (dist.metadata["Name"] or "").lower().replace("_", "-")
        except Exception:
            continue
        if name:
            packages[name] = dist.version
    return dict(sorted(packages.items()))


def top_level_import_map() -> dict[str, str]:
    """Import name -> distribution, from installed metadata when available."""
    mapping = {k: v for k, v in IMPORT_TO_DIST.items()}
    try:
        for top, dists in importlib_metadata.packages_distributions().items():
            if dists:
                mapping.setdefault(top, dists[0].lower().replace("_", "-"))
    except Exception:
        pass
    return mapping


def run_tests(root: Path, extra: str, timeout: int) -> dict[str, Any]:
    args = [sys.executable, "-m", "pytest", "-q", "-rfEs", "--no-header", "-p", "no:cacheprovider"]
    if extra:
        import shlex
        args += shlex.split(extra, posix=(os.name != "nt"))
    try:
        result = run_command(args, cwd=root, check=False, timeout=timeout)
        output = (result.stdout + "\n" + result.stderr).strip()
        return {"command": " ".join(args[1:]), "returncode": result.returncode, "output": output}
    except subprocess.TimeoutExpired:
        return {"command": " ".join(args[1:]), "returncode": None, "output": f"Timeout after {timeout}s"}
    except Exception as exc:
        return {"command": " ".join(args[1:]), "returncode": None, "output": repr(exc)}


# ---------------------------------------------------------------------------
# Static diagnostics
# ---------------------------------------------------------------------------

def index_consumers(
    symbols: list[Symbol],
    python_files: list[PythonFileAnalysis],
    notebooks: list[NotebookAnalysis],
) -> dict[str, list[str]]:
    consumers: dict[str, set[str]] = defaultdict(set)
    by_name: defaultdict[str, list[Symbol]] = defaultdict(list)
    for symbol in symbols:
        by_name[symbol.name].append(symbol)
    sources: list[tuple[str, set[str]]] = [
        (a.path, set(a.calls) | set(a.imports)) for a in python_files
    ] + [
        (n.path, set(n.imports) | {s.name for s in n.call_sites}) for n in notebooks
    ]
    for path, haystack in sources:
        tails = {item.rsplit(".", 1)[-1] for item in haystack}
        for name in tails & set(by_name):
            for match in by_name[name]:
                if path != match.path:
                    consumers[f"{match.module}.{match.qualname}"].add(path)
    return {key: sorted(values) for key, values in sorted(consumers.items())}


def index_tests(symbols: list[Symbol], python_files: list[PythonFileAnalysis]) -> dict[str, list[str]]:
    tests: dict[str, set[str]] = defaultdict(set)
    test_files = [
        f for f in python_files
        if f.path.startswith("tests/") or Path(f.path).name.startswith("test_")
    ]
    for test in test_files:
        tails = {v.rsplit(".", 1)[-1] for v in set(test.calls) | set(test.imports)}
        for symbol in symbols:
            if symbol.name in tails and symbol.path != test.path:
                tests[f"{symbol.module}.{symbol.qualname}"].add(test.path)
    return {key: sorted(values) for key, values in sorted(tests.items())}


def resolve_relative(module: str, current: str, is_package: bool) -> str:
    if not module.startswith("."):
        return module
    level = len(module) - len(module.lstrip("."))
    base = current.split(".")
    if not is_package:
        base = base[:-1]
    base = base[: len(base) - (level - 1)] if level > 1 else base
    rest = module.lstrip(".")
    return ".".join([*base, rest] if rest else base)


def import_integrity_attention(
    python_files: list[PythonFileAnalysis],
    notebooks: list[NotebookAnalysis],
    internal_roots: set[str],
) -> list[Attention]:
    modules = {f.module: f for f in python_files}
    packages = {m.rsplit(".", 1)[0] for m in modules if "." in m}
    missing_modules: defaultdict[str, set[str]] = defaultdict(set)
    missing_names: defaultdict[str, set[str]] = defaultdict(set)

    def check(module: str, names: list[str], where: str) -> None:
        if module.split(".")[0] not in internal_roots:
            return
        if module not in modules and module not in packages:
            missing_modules[module].add(where)
            return
        target = modules.get(module)
        if target is None or target.has_star_import or target.parse_error:
            return
        defined = set(target.top_level_names)
        for name in names:
            if name == "*" or name in defined:
                continue
            if f"{module}.{name}" in modules or f"{module}.{name}" in packages:
                continue
            missing_names[f"{module}.{name}"].add(where)

    for f in python_files:
        is_pkg = f.path.endswith("__init__.py")
        for item in f.import_from:
            module = resolve_relative(item["module"], f.module, is_pkg)
            check(module, item["names"], f"{f.path}:{item['lineno']}")
        for value in f.imports:
            if "." not in value and value in internal_roots:
                continue
    for nb in notebooks:
        for item in nb.import_from:
            check(item["module"], item["names"], f"{nb.path}#cell-{item.get('cell')}")
    attention = [
        Attention(
            "high", "internal-import-missing-module",
            f"Import of internal module `{name}`, which does not exist in the snapshot.",
            sorted(paths),
            "Check branch completeness, renamed modules or stale imports before recreating code.",
        )
        for name, paths in sorted(missing_modules.items())
    ]
    attention += [
        Attention(
            "high", "internal-import-missing-name",
            f"`{name.rsplit('.', 1)[1]}` is imported from `{name.rsplit('.', 1)[0]}`, "
            "but that module does not define or re-export it.",
            sorted(paths),
            "Export the name in the module (or its __init__) or fix the import.",
        )
        for name, paths in sorted(missing_names.items())
    ]
    return attention


def call_signature_attention(
    symbols: list[Symbol],
    python_files: list[PythonFileAnalysis],
    notebooks: list[NotebookAnalysis],
) -> list[Attention]:
    """Calls to project functions with keywords they do not accept."""
    candidates: defaultdict[str, list[Symbol]] = defaultdict(list)
    for symbol in symbols:
        if symbol.kind in {"function", "class"} and symbol.path.startswith("src/"):
            candidates[symbol.name].append(symbol)
    unique = {name: items[0] for name, items in candidates.items() if len(items) == 1}
    local_defs: dict[str, set[str]] = defaultdict(set)
    for f in python_files:
        local_defs[f.path].update(s.name for s in f.symbols if s.kind in {"function", "class"})
    for nb in notebooks:
        local_defs[nb.path].update(s.name for s in nb.functions + nb.classes)

    problems: list[Attention] = []
    sources = [(f.path, f.call_sites) for f in python_files] + [(n.path, n.call_sites) for n in notebooks]
    for path, sites in sources:
        for site in sites:
            tail = site.name.rsplit(".", 1)[-1]
            target = unique.get(tail)
            if target is None or path == target.path or tail in local_defs[path]:
                continue
            if "." in site.name and site.name.split(".")[0] in {"self", "cls"}:
                continue
            issues: list[str] = []
            if not target.has_varkw:
                bad = [k for k in site.keywords if k not in target.params]
                if bad:
                    issues.append(f"unknown keyword(s) {bad}")
            if not target.has_varargs and not site.has_star_args and site.n_positional > target.n_positional_params:
                issues.append(
                    f"{site.n_positional} positional args, accepts {target.n_positional_params}"
                )
            if issues:
                problems.append(
                    Attention(
                        "high", "call-signature-mismatch",
                        f"Call to `{target.module}.{target.name}` does not match its signature: "
                        + "; ".join(issues) + ".",
                        [site.location, f"definition: {target.path}:{target.lineno} `{target.signature}`"],
                        "Fix the call or the function signature; this raises TypeError when executed.",
                    )
                )
    return problems


def gate_attention(
    gate_names: set[str],
    files_text: dict[str, str],
    notebook_sources: dict[str, str],
) -> list[Attention]:
    if not gate_names:
        return []
    found: defaultdict[str, set[str]] = defaultdict(set)
    for path, text in {**files_text, **notebook_sources}.items():
        if path.endswith(("supervised.yaml", OUTPUT_MD_NAME)):
            continue
        for match in GATE_RE.findall(text):
            found[match].add(path)
    stale = {name: paths for name, paths in found.items() if name not in gate_names}
    return [
        Attention(
            "medium", "gate-name-not-in-yaml",
            f"`{name}` is referenced but does not exist in `gates` of the active YAML.",
            sorted(paths),
            "Update the reference (code, docstring, notebook or document) to an existing gate.",
        )
        for name, paths in sorted(stale.items())
    ]


def config_contract_attention(config: Any, python_files: list[PythonFileAnalysis]) -> list[Attention]:
    if not isinstance(config, dict):
        return []
    attention: list[Attention] = []

    def as_list(*keys: str) -> list[str]:
        value = nested_get(config, *keys, default=[])
        return [str(v) for v in value] if isinstance(value, list) else []

    final = as_list("features", "final")
    active = set(final) or set(as_list("features", "numericas")) | set(as_list("features", "categoricas"))
    prohibited = set(as_list("features", "proibidas"))
    if active & prohibited:
        attention.append(Attention(
            "high", "feature-leakage-contract",
            "Configured model features overlap `features.proibidas`.",
            sorted(active & prohibited), "Remove the overlap or revise configuration and tests."))
    target = nested_get(config, "target", "coluna")
    if target and target not in prohibited:
        attention.append(Attention(
            "high", "feature-leakage-contract", "`target.coluna` is not in `features.proibidas`.",
            [str(target)], "Add the raw target to the forbidden list."))
    derived = set(as_list("features", "engenharia", "derivadas"))
    model_features = set(as_list("features", "numericas")) | set(as_list("features", "categoricas"))
    unused_derived = sorted(derived - model_features - set(final))
    if unused_derived:
        attention.append(Attention(
            "low", "derived-not-used-as-feature",
            "Derived columns produced by feature engineering but absent from the model feature lists.",
            unused_derived, "Confirm whether they are intentionally descriptive-only or missing from the model."))
    source_text = "\n".join(
        " ".join(f.calls + list(f.constants) + list(f.constants.values()) + f.file_literals + f.top_level_names)
        for f in python_files if f.path.startswith(("src/features/", "src/data/"))
    )
    absent = sorted(v for v in derived if v not in source_text)
    if absent:
        attention.append(Attention(
            "medium", "derived-feature-contract",
            "Configured derived features not found as static names in src/features or src/data.",
            absent, "Confirm whether names are dynamic, stale or missing from the implementation."))
    fractions = nested_get(config, "temporal", "fracao", default={})
    if isinstance(fractions, dict):
        numeric = [v for v in fractions.values() if isinstance(v, (int, float))]
        if numeric and abs(sum(numeric) - 1.0) > 1e-9:
            attention.append(Attention(
                "high", "split-contract", "Split fractions do not sum to 1.", [repr(fractions)],
                "Correct the split contract."))
    models = nested_get(config, "models", default={}) or {}
    closed = set(as_list("selecao_modelos", "familias_encerradas"))
    for name in sorted(closed):
        if nested_get(models, name, "ativa") is True:
            attention.append(Attention(
                "low", "config-consistency",
                f"`models.{name}.ativa` is true, but the family is in `selecao_modelos.familias_encerradas`.",
                [f"models.{name}.ativa"], "Set `ativa: false` or remove the family from the closed list."))
    finalists = as_list("selecao_modelos", "finalistas")
    for name in finalists:
        if name not in models:
            attention.append(Attention(
                "medium", "config-consistency",
                f"Finalist `{name}` has no section in `models` (factory names must match).",
                [f"selecao_modelos.finalistas: {finalists}", f"models: {sorted(models)}"],
                "Use the same names or declare an explicit alias in code."))
    gates = nested_get(config, "gates", default={}) or {}
    numbers = sorted(int(m.group(1)) for k in gates for m in [re.match(r"G(\d+)_", str(k))] if m)
    if numbers:
        gaps = [f"G{n}" for n in range(numbers[0], numbers[-1] + 1) if n not in numbers]
        if gaps:
            attention.append(Attention(
                "low", "gate-numbering", "Gate numbering has gaps.", gaps,
                "Document why the gate does not exist or renumber."))
    return attention


def unused_config_keys_attention(config: Any, code_text: str) -> list[Attention]:
    if not isinstance(config, dict):
        return []
    unused: list[str] = []
    for key in flatten_mapping(config):
        parts = key.split(".")
        if parts[0] in {"gates", "selecao_modelos"}:
            continue
        leaf = next((p for p in reversed(parts) if not p.isdigit()), parts[-1])
        if not re.search(rf"['\"]{re.escape(leaf)}['\"]", code_text):
            unused.append(key)
    if not unused:
        return []
    return [Attention(
        "low", "config-key-not-referenced",
        f"{len(unused)} YAML keys whose name never appears as a string literal in code or notebooks "
        "(possible dead configuration, or keys read dynamically).",
        unused[:80], "Remove dead keys or make the code read them; keep documentation keys commented.")]


def dependency_attention(
    python_files: list[PythonFileAnalysis],
    notebooks: list[NotebookAnalysis],
    requirements: dict[str, str] | None,
    pyproject_deps: dict[str, str] | None,
    import_map: dict[str, str],
    internal_roots: set[str],
) -> list[Attention]:
    stdlib = set(getattr(sys, "stdlib_module_names", ()))
    used: defaultdict[str, set[str]] = defaultdict(set)
    for f in python_files:
        for value in f.external_imports:
            used[value.split(".")[0]].add(f.path)
    for nb in notebooks:
        for value in nb.imports:
            used[value.split(".")[0]].add(nb.path)
    third_party = {
        top: paths for top, paths in used.items()
        if top and top not in stdlib and top not in internal_roots and not top.startswith("_")
        and top not in {"__future__"}
    }
    attention: list[Attention] = []
    for label, deps in (("requirements.txt", requirements), ("pyproject.toml", pyproject_deps)):
        if deps is None:
            continue
        missing = []
        for top, paths in sorted(third_party.items()):
            dist = import_map.get(top, top).lower().replace("_", "-")
            if dist not in deps and top.lower() not in deps:
                missing.append(f"{top} (distribution `{dist}`) used in {sorted(paths)[0]}")
        if missing:
            attention.append(Attention(
                "medium", "dependency-not-declared",
                f"Third-party imports not declared in `{label}`.", missing,
                "Declare them (with a minimum version) in a single source of dependencies."))
        unpinned = sorted(name for name, spec in deps.items() if not spec)
        if unpinned:
            attention.append(Attention(
                "low", "dependency-unpinned", f"Dependencies without version constraint in `{label}`.",
                unpinned, "Add minimum versions for reproducibility (at least scikit-learn, pandas, numpy)."))
    return attention


def duplicate_symbol_attention(symbols: list[Symbol]) -> list[Attention]:
    grouped: defaultdict[str, set[str]] = defaultdict(set)
    for symbol in symbols:
        if symbol.kind in {"function", "class"} and not symbol.path.startswith("tests/") and symbol.name != "main":
            grouped[symbol.name].add(symbol.path)
    return [
        Attention(
            "medium", "duplicate-symbol-name", f"`{name}` is defined in multiple files.",
            sorted(paths), "Confirm distinct responsibilities or consolidate competing implementations.")
        for name, paths in sorted(grouped.items()) if len(paths) > 1
    ]


def notebook_attention(notebooks: list[NotebookAnalysis], python_files: list[PythonFileAnalysis]) -> list[Attention]:
    canonical: defaultdict[str, list[str]] = defaultdict(list)
    for f in python_files:
        if f.path.startswith("src/"):
            for s in f.symbols:
                if s.kind in {"function", "class"}:
                    canonical[s.name].append(s.path)
    attention: list[Attention] = []
    for nb in notebooks:
        for s in nb.functions + nb.classes:
            if s.name in canonical:
                attention.append(Attention(
                    "medium", "notebook-duplicates-src",
                    f"Notebook defines `{s.name}`, already present in src.",
                    [s.path, *sorted(set(canonical[s.name]))],
                    "Use the src implementation, or extend it if behaviour differs."))
        local = [s.name for s in nb.functions + nb.classes if s.name not in canonical]
        if local:
            attention.append(Attention(
                "low", "notebook-local-functions",
                f"`{nb.path}` defines {len(local)} local functions/classes.",
                local, "Keep single-use orchestration in the notebook; move reusable logic to src with tests."))
        if nb.out_of_order:
            attention.append(Attention(
                "medium", "notebook-execution-order",
                f"`{nb.path}` was saved with cells executed out of order.",
                [str(nb.execution_counts)], "Restart the kernel and run all cells before trusting saved outputs."))
        if nb.code_cells and nb.executed_cells < nb.code_cells:
            attention.append(Attention(
                "low", "notebook-not-fully-executed",
                f"`{nb.path}`: {nb.code_cells - nb.executed_cells} of {nb.code_cells} code cells have no saved execution.",
                [], "Outputs may be partial; re-run before using results."))
        if nb.error_outputs:
            attention.append(Attention(
                "high", "notebook-saved-errors", f"`{nb.path}` was saved with error outputs.",
                nb.error_outputs[:20], "Fix the error and re-run, or clear the stale output."))
        if nb.parse_errors:
            attention.append(Attention(
                "medium", "notebook-parse-error", f"`{nb.path}` has code cells that could not be parsed.",
                nb.parse_errors[:20], "Check syntax (magics are already tolerated)."))
    return attention


def stale_document_attention(files_text: dict[str, str], existing_paths: set[str]) -> list[Attention]:
    path_re = re.compile(
        r"(?<![A-Za-z0-9_./-])((?:src|tests|notebooks|configs|tools|docs|data|outputs)/"
        r"[A-Za-z0-9_./-]+\.(?:py|ipynb|yaml|yml|md|csv|json|parquet|toml))"
    )
    existing_dirs = {str(Path(p).parent.as_posix()) for p in existing_paths}
    attention: list[Attention] = []
    for path, text in files_text.items():
        if not path.lower().endswith((".md", ".rst", ".txt", ".py", ".yaml", ".yml")):
            continue
        refs = sorted({m.group(1) for m in path_re.finditer(text)})
        missing = [
            r for r in refs
            if r not in existing_paths and "{" not in r and "*" not in r and r not in existing_dirs
        ]
        if missing:
            attention.append(Attention(
                "low" if path.endswith(".py") else "medium", "reference-to-missing-path",
                f"`{path}` references paths absent from the working folder.", missing[:40],
                "Confirm whether the reference is historical, generated at runtime, or stale."))
    return attention


def text_quality_attention(files_text: dict[str, str], notebook_sources: dict[str, str]) -> tuple[list[Attention], list[str]]:
    mojibake: list[str] = []
    todos: list[str] = []
    for path, text in {**files_text, **notebook_sources}.items():
        if path.endswith(OUTPUT_MD_NAME):
            continue
        for number, line in enumerate(text.splitlines(), 1):
            if MOJIBAKE_RE.search(line):
                mojibake.append(f"{path}:{number}: {line.strip()[:100]}")
            match = TODO_RE.search(line)
            if match and not path.endswith(".csv"):
                todos.append(f"{path}:{number}: {match.group(1)} {match.group(2).strip()}")
    attention = []
    if mojibake:
        attention.append(Attention(
            "low", "encoding-mojibake", "Text with likely encoding corruption (file saved with the wrong encoding).",
            mojibake[:40], "Fix the characters and save the file as UTF-8."))
    return attention, todos


def working_tree_attention(entries: list[GitEntry]) -> list[Attention]:
    relevant = [e.path for e in entries if not e.tracked and e.exists and e.path.startswith(IMPORTANT_UNTRACKED_PREFIXES)]
    modified = [f"{e.path} ({e.status.strip()})" for e in entries if e.tracked and e.status.strip()]
    attention = []
    if relevant:
        attention.append(Attention(
            "high", "untracked-relevant-files", "Relevant files exist only in the working tree (not committed).",
            relevant, "Commit intentional files or remove them before treating the snapshot as the project state."))
    if modified:
        attention.append(Attention(
            "medium", "uncommitted-changes", "Tracked files with uncommitted changes.", modified[:60],
            "Review Section 16 (diff) and commit or discard."))
    return attention


def symbol_quality_attention(
    symbols: list[Symbol],
    consumers: dict[str, list[str]],
    tests: dict[str, list[str]],
) -> list[Attention]:
    public = [
        s for s in symbols
        if s.path.startswith("src/") and not s.is_private and s.kind in {"function", "class"}
    ]
    orphan = [f"{s.module}.{s.name}" for s in public if not consumers.get(f"{s.module}.{s.qualname}") and not tests.get(f"{s.module}.{s.qualname}")]
    untested = [f"{s.module}.{s.name}" for s in public if not tests.get(f"{s.module}.{s.qualname}")]
    nodoc = [f"{s.module}.{s.name}" for s in public if not s.docstring]
    out = []
    if orphan:
        out.append(Attention("low", "public-symbol-unused",
                             "Public src symbols with no detected consumer and no test (possibly dead code).",
                             orphan, "Remove, test, or document why they exist."))
    if untested:
        out.append(Attention("low", "public-symbol-untested",
                             f"{len(untested)} public src symbols without a detected test.", untested,
                             "Prioritise tests for functions used by notebooks C2–C6."))
    if nodoc:
        out.append(Attention("low", "missing-docstring", "Public src symbols without docstring.", nodoc,
                             "Add a short docstring with purpose, parameters and returned value."))
    return out


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def render_attention(attention: list[Attention]) -> str:
    if not attention:
        return "- No static inconsistencies detected."
    counts = Counter(a.severity for a in attention)
    lines = [
        f"Totals: **{counts.get('high', 0)} high**, {counts.get('medium', 0)} medium, {counts.get('low', 0)} low.",
        "",
        "| # | Severity | Category | Message |",
        "|---|---|---|---|",
    ]
    ordered = sorted(attention, key=lambda a: (SEVERITY_ORDER.get(a.severity, 9), a.category, a.message))
    for i, a in enumerate(ordered, 1):
        lines.append(f"| A{i} | {a.severity.upper()} | {a.category} | {a.message.replace('|', '/')} |")
    lines.append("")
    for i, a in enumerate(ordered, 1):
        lines += [f"### A{i}. {a.severity.upper()} — {a.category}", "", a.message, ""]
        if a.evidence:
            lines += ["**Evidence**", "", *(f"- `{v}`" for v in a.evidence), ""]
        if a.recommendation:
            lines += [f"**Recommended action:** {a.recommendation}", ""]
    return "\n".join(lines).rstrip()


def render_symbol(symbol: Symbol, consumers: dict[str, list[str]], tests: dict[str, list[str]]) -> str:
    key = f"{symbol.module}.{symbol.qualname}"
    lines = [
        f"#### `{symbol.qualname}`",
        "",
        code_block(symbol.signature, "python"),
        "",
        f"- Location: `{symbol.path}:{symbol.lineno}-{symbol.end_lineno}`",
        f"- Visibility: `{'private' if symbol.is_private else 'public'}`",
        "- Tested by: " + (", ".join(f"`{p}`" for p in tests.get(key, [])) or "not found statically"),
        "- Consumed by: " + (", ".join(f"`{p}`" for p in consumers.get(key, [])) or "not found statically"),
    ]
    if symbol.defaults:
        lines.append("- Defaults: " + ", ".join(f"`{k}={v}`" for k, v in symbol.defaults.items()))
    if symbol.decorators:
        lines.append("- Decorators: " + ", ".join(f"`{d}`" for d in symbol.decorators))
    if symbol.calls:
        lines.append("- Calls: " + ", ".join(f"`{c}`" for c in symbol.calls[:40]))
    if symbol.env_vars:
        lines.append("- Environment variables: " + ", ".join(f"`{e}`" for e in symbol.env_vars))
    if symbol.file_literals:
        lines.append("- File literals: " + ", ".join(f"`{e}`" for e in symbol.file_literals))
    lines += ["", symbol.docstring or "_Missing docstring._", ""]
    return "\n".join(lines)


def render_python_api(python_files: list[PythonFileAnalysis], consumers: dict, tests: dict) -> str:
    parts: list[str] = []
    for f in sorted(python_files, key=lambda x: x.path.lower()):
        parts += [f"### `{f.path}`", ""]
        if f.parse_error:
            parts += [f"- **Parse error:** `{f.parse_error}`", ""]
            continue
        parts += [
            f"- Module: `{f.module}` · {f.lines} lines",
            "- Internal imports: " + (", ".join(f"`{v}`" for v in f.internal_imports) or "none"),
            "- External imports: " + (", ".join(f"`{v}`" for v in f.external_imports) or "none"),
        ]
        if f.constants:
            parts.append("- Module constants: " + ", ".join(f"`{k} = {v}`" for k, v in f.constants.items()))
        if f.env_vars:
            parts.append("- Environment variables: " + ", ".join(f"`{e}`" for e in f.env_vars))
        parts.append("")
        if f.docstring:
            parts += [f.docstring, ""]
        for symbol in f.symbols:
            parts.append(render_symbol(symbol, consumers, tests))
    return "\n".join(parts).rstrip()


def render_table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return "- None."
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    out += ["| " + " | ".join(str(c).replace("|", "/").replace("\n", " ") for c in row) + " |" for row in rows]
    return "\n".join(out)


def render_tree(inventory: list[dict[str, Any]]) -> str:
    """Directory tree with file counts and sizes."""
    dirs: defaultdict[str, list[int]] = defaultdict(lambda: [0, 0])
    for row in inventory:
        parent = str(Path(row["path"]).parent.as_posix())
        while True:
            dirs[parent][0] += 1
            dirs[parent][1] += row["bytes"]
            if parent in {".", ""}:
                break
            parent = str(Path(parent).parent.as_posix())
    lines = []
    for d in sorted(dirs):
        depth = 0 if d == "." else d.count("/") + 1
        name = "./" if d == "." else Path(d).name + "/"
        lines.append(f"{'  ' * depth}{name}  ({dirs[d][0]} files, {human_bytes(dirs[d][1])})")
    return code_block("\n".join(lines), "text")


def split_document(document: str, max_bytes: int) -> list[str]:
    """Split on level-2 headings, keeping parts under max_bytes when possible."""
    chunks: list[str] = []
    current: list[str] = []
    in_fence = None
    for line in document.splitlines(keepends=True):
        fence = re.match(r"^(`{3,})", line)
        if fence:
            if in_fence is None:
                in_fence = fence.group(1)
            elif line.strip() == in_fence:
                in_fence = None
        if in_fence is None and line.startswith("## ") and current:
            chunks.append("".join(current))
            current = []
        current.append(line)
    if current:
        chunks.append("".join(current))
    parts: list[str] = []
    buffer = ""
    for chunk in chunks:
        if buffer and len((buffer + chunk).encode("utf-8")) > max_bytes:
            parts.append(buffer)
            buffer = ""
        if len(chunk.encode("utf-8")) > max_bytes:
            lines = chunk.splitlines(keepends=True)
            piece = ""
            for line in lines:
                if piece and len((piece + line).encode("utf-8")) > max_bytes:
                    parts.append(piece + "\n\n_(section continues in the next part)_\n")
                    piece = ""
                piece += line
            buffer = piece
        else:
            buffer += chunk
    if buffer:
        parts.append(buffer)
    return parts


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def build_reference(root: Path, args: argparse.Namespace) -> tuple[str, dict[str, Any]]:
    redactor = Redactor(root)
    entries, tracked, untracked = collect_git_entries(root)
    inventory, inventory_truncated = walk_inventory(root, tracked, untracked)
    inv_by_path = {row["path"]: row for row in inventory}
    existing_paths = set(inv_by_path)

    internal_roots = {
        Path(e.path).parts[0] for e in entries
        if e.exists and Path(e.path).suffix.lower() in {".py", ".pyi"} and len(Path(e.path).parts) > 1
    } | {"src", "tests", "tools"}

    selected: list[tuple[Path, bool, str]] = []
    seen: set[str] = set()
    for e in entries:
        if e.exists and include_source(Path(e.path), tracked=e.tracked):
            selected.append((Path(e.path), e.tracked, e.status))
            seen.add(e.path)
    ignored_sources: list[str] = []
    for row in inventory:
        rel_path = Path(row["path"])
        if (
            row["git"] == "ignored"
            and row["path"] not in seen
            and row["path"].startswith(IMPORTANT_UNTRACKED_PREFIXES)
            and include_source(rel_path, tracked=True)
        ):
            selected.append((rel_path, False, "!! ignored by .gitignore"))
            ignored_sources.append(row["path"])

    python_files: list[PythonFileAnalysis] = []
    notebooks: list[NotebookAnalysis] = []
    files_text: dict[str, str] = {}
    notebook_text: dict[str, str] = {}
    file_records: list[dict[str, Any]] = []
    source_sections: list[str] = []
    skipped: list[str] = []
    yaml_docs: dict[str, dict[str, Any]] = {}
    config: Any = None
    config_error: str | None = None
    yaml_duplicates: dict[str, list[str]] = {}
    pyproject_data: dict[str, Any] | None = None
    pyproject_error: str | None = None
    requirements: dict[str, str] | None = None

    for rel, is_tracked, status in selected:
        absolute = root / rel
        data = absolute.read_bytes()
        digest = sha256_bytes(data)
        suffix = rel.suffix.lower()
        header = [
            f"## `{rel.as_posix()}`",
            "",
            f"- Git: `{'tracked' if is_tracked else 'untracked (working tree)'}` · status `{status.strip() or 'clean'}`",
            f"- Size: `{human_bytes(len(data))}` · modified `{inv_by_path.get(rel.as_posix(), {}).get('modified_utc', '?')} UTC`",
            f"- SHA-256: `{digest}`",
        ]
        record = {
            "path": rel.as_posix(), "tracked": is_tracked, "status": status, "sha256": digest,
            "bytes": len(data), "type": suffix.lstrip(".") or rel.name,
        }
        if suffix in LIKELY_BINARY_SUFFIXES:
            skipped.append(f"{rel.as_posix()} (binary)")
            continue
        if suffix == ".ipynb":
            try:
                analysis, nb = analyze_notebook(rel, data, internal_roots)
            except Exception as exc:
                skipped.append(f"{rel.as_posix()} (notebook parse error: {exc!r})")
                continue
            reduced = len(data) > args.max_inline_bytes
            analysis.outputs_included = args.notebook_outputs
            notebooks.append(analysis)
            notebook_text[rel.as_posix()] = "\n".join(
                "".join(c.get("source", [])) for c in nb.get("cells", [])
            )
            body = notebook_source_markdown(
                nb, analysis, include_outputs=args.notebook_outputs,
                max_output_chars=args.max_output_chars, reduced=reduced, redactor=redactor,
            )
            source_sections.append("\n".join(header) + "\n\n" + body + "\n")
            file_records.append(record)
            continue
        if suffix in OFFICE_SUFFIXES:
            try:
                text = office_text(data, suffix)
            except Exception as exc:
                skipped.append(f"{rel.as_posix()} (office parse error: {exc!r})")
                continue
            text, warnings = redactor(text)
            files_text[rel.as_posix()] = text
            header.append("- Content: plain text extracted (formatting, tables layout and images not preserved)")
            source_sections.append("\n".join(header) + "\n\n" + code_block(truncate(text, args.max_inline_bytes), "text") + "\n")
            file_records.append(record)
            continue
        if b"\x00" in data[:8192]:
            skipped.append(f"{rel.as_posix()} (binary content)")
            continue
        decoded = data.decode("utf-8-sig", errors="replace")
        text, warnings = redactor(decoded)
        if rel.as_posix() == "tools/update_project_reference.py":
            text, warnings = decoded, []  # the generator's own regexes look like secrets
            for value in redactor.root_variants:
                text = text.replace(value, "<REPO>")
        files_text[rel.as_posix()] = text
        if warnings:
            header.append("- Security: " + "; ".join(warnings))
        if suffix in {".py", ".pyi"}:
            python_files.append(analyze_python(rel, text, internal_roots))
        elif suffix in {".yaml", ".yml"}:
            parsed, error, dups = load_yaml_strict(decoded)
            yaml_docs[rel.as_posix()] = {"error": error, "duplicates": dups}
            if dups:
                yaml_duplicates[rel.as_posix()] = dups
            if rel.as_posix() == args.config:
                config, config_error = parsed, error
        elif rel.name == "pyproject.toml":
            pyproject_data, pyproject_error = parse_pyproject(decoded)
        elif rel.name == "requirements.txt" and len(rel.parts) == 1:
            requirements = parse_requirements(decoded)
        if suffix in {".csv", ".tsv"} and len(data) > args.max_artifact_bytes:
            preview, total = csv_preview(text, args.max_csv_rows)
            header.append(f"- Content: first {args.max_csv_rows} of {total} rows")
            body = code_block(preview, "csv")
        elif len(data) > args.max_inline_bytes:
            body = code_block(truncate(text, args.max_inline_bytes), LANG.get(suffix, "text"))
        else:
            body = code_block(text.rstrip(), LANG.get(suffix, "text"))
        source_sections.append("\n".join(header) + "\n\n" + body + "\n")
        file_records.append(record)

    # Small text artifacts (outputs/, data/ manifests, reports/)
    artifact_sections: list[str] = []
    artifact_records: list[dict[str, Any]] = []
    if args.artifacts:
        for row in inventory:
            rel = Path(row["path"])
            if not include_artifact(rel, row["bytes"], args.max_artifact_bytes):
                continue
            try:
                raw = (root / rel).read_bytes()
            except OSError:
                continue
            if b"\x00" in raw[:8192]:
                continue
            text, _ = redactor(raw.decode("utf-8-sig", errors="replace"))
            suffix = rel.suffix.lower()
            note = ""
            if suffix in {".csv", ".tsv"}:
                text, total = csv_preview(text, args.max_csv_rows)
                note = f" · {total} rows" + (f" (first {args.max_csv_rows} shown)" if total > args.max_csv_rows else "")
            else:
                text = truncate(text, args.max_artifact_bytes)
            artifact_sections.append(
                f"### `{rel.as_posix()}`\n\n- Git: `{row['git']}` · `{human_bytes(row['bytes'])}` · "
                f"modified `{row['modified_utc']} UTC`{note}\n\n"
                + code_block(text.rstrip(), LANG.get(suffix, "text")) + "\n"
            )
            artifact_records.append(row)
            if suffix in {".yaml", ".yml"}:
                files_text[rel.as_posix()] = text

    # Indexes and diagnostics
    symbols = [s for f in python_files for s in f.symbols]
    consumers = index_consumers(symbols, python_files, notebooks)
    tests = index_tests(symbols, python_files)
    import_map = top_level_import_map()
    packages = installed_packages()
    pyproject_deps = pyproject_dependencies(pyproject_data) if pyproject_data else None
    gates = nested_get(config, "gates", default={}) if isinstance(config, dict) else {}
    gate_names = set(gates) if isinstance(gates, dict) else set()
    code_text = "\n".join(
        [t for p, t in files_text.items() if p.endswith(".py")] + list(notebook_text.values())
    )

    attention: list[Attention] = []
    attention += working_tree_attention(entries)
    if ignored_sources:
        attention.append(Attention(
            "high", "source-ignored-by-git",
            "Source/config/test/notebook files are ignored by .gitignore and therefore missing from GitHub.",
            ignored_sources,
            "Fix .gitignore (anchor root folders, e.g. `/data/` instead of `data/`) and commit the files."))
    attention += import_integrity_attention(python_files, notebooks, internal_roots)
    attention += call_signature_attention(symbols, python_files, notebooks)
    attention += config_contract_attention(config, python_files)
    attention += gate_attention(gate_names, files_text, notebook_text)
    attention += unused_config_keys_attention(config, code_text)
    attention += dependency_attention(python_files, notebooks, requirements, pyproject_deps, import_map, internal_roots)
    attention += duplicate_symbol_attention(symbols)
    attention += notebook_attention(notebooks, python_files)
    attention += stale_document_attention(files_text, existing_paths)
    quality, todos = text_quality_attention(files_text, notebook_text)
    attention += quality
    attention += symbol_quality_attention(symbols, consumers, tests)
    for f in python_files:
        if f.parse_error:
            attention.append(Attention("high", "python-parse-error", f"`{f.path}` could not be parsed.",
                                       [f.parse_error], "Fix syntax or check interpreter compatibility."))
    if config_error:
        attention.append(Attention("high", "yaml-error", f"`{args.config}` could not be analysed.",
                                   [config_error], "Fix the YAML (or install PyYAML) and regenerate."))
    for path, dups in yaml_duplicates.items():
        attention.append(Attention("high", "yaml-duplicate-keys",
                                   f"`{path}` has duplicated keys; yaml.safe_load silently keeps the last value.",
                                   dups, "Remove the duplicates."))
    if pyproject_error:
        attention.append(Attention("high", "pyproject-invalid", "`pyproject.toml` is not valid TOML.",
                                   [pyproject_error], "Fix it; `pip install -e .` fails with an invalid pyproject."))
    if inventory_truncated:
        attention.append(Attention("low", "inventory-truncated",
                                   f"Path inventory stopped at {MAX_INVENTORY_ENTRIES} files.", [],
                                   "Exclude large generated folders or raise MAX_INVENTORY_ENTRIES."))

    tests_result = run_tests(root, args.pytest_args, args.test_timeout) if args.run_tests else None
    if tests_result and tests_result["returncode"] not in (0, None):
        attention.append(Attention("high", "tests-failing", "pytest returned a non-zero exit code.",
                                   [tests_result["output"].splitlines()[-1] if tests_result["output"] else ""],
                                   "See Section 11."))

    # Git details
    branch = git(root, "branch", "--show-current").strip() or "detached"
    commit = git(root, "rev-parse", "HEAD", check=False).strip() or "no commits"
    remote, _ = redactor(git(root, "remote", "get-url", "origin", check=False).strip())
    status_text = git(root, "status", "--short", "--branch").rstrip() or "clean"
    log_text = git(root, "log", f"-{args.git_log}", "--date=iso", "--pretty=format:%h %ad %an%n    %s", check=False).rstrip()
    branches = git(root, "branch", "-a", "-vv", check=False).rstrip()
    ahead_behind = git(root, "rev-list", "--left-right", "--count", "HEAD...@{upstream}", check=False).strip()
    diff_stat = git(root, "diff", "HEAD", "--stat", check=False).rstrip()
    diff_text = ""
    if args.include_diff:
        raw_diff = git(root, "diff", "HEAD", "--", ".", ":(exclude)docs/" + OUTPUT_MD_NAME,
                       ":(exclude)docs/" + OUTPUT_JSON_NAME, check=False)
        diff_text = truncate(redactor(raw_diff)[0], args.max_diff_chars)
    gitignore_check = git(root, "check-ignore", "-v", "--no-index", *[
        p for p in ("data/", "outputs/", "models/", ".env", "configs/paths.local.json") if (root / p).exists()
    ], check=False).strip() if any((root / p).exists() for p in ("data", "outputs", "models", ".env")) else ""

    generated = datetime.now(timezone.utc).isoformat(timespec="seconds")
    counts = Counter(a.severity for a in attention)
    public = [s for s in symbols if s.path.startswith("src/") and not s.is_private and s.kind in {"function", "class"}]

    # ---- Section 6
    sec6 = [
        "## 6. Executive continuation map", "",
        f"- Generated (UTC): `{generated}` · branch `{branch}` · commit `{commit[:12]}`",
        f"- Git status: `{'clean' if status_text.count(chr(10)) == 0 else 'has changes'}`; upstream ahead/behind: `{ahead_behind or 'n/a'}`",
        f"- Files in working folder (inventory): `{len(inventory)}` "
        f"(tracked `{sum(r['git'] == 'tracked' for r in inventory)}`, untracked `{sum(r['git'] == 'untracked' for r in inventory)}`, "
        f"ignored/local `{sum(r['git'] == 'ignored' for r in inventory)}`)",
        f"- Source files with full content: `{len(file_records)}`; artifacts included: `{len(artifact_records)}`",
        f"- Python modules: `{len(python_files)}` · notebooks: `{len(notebooks)}` · public src symbols: `{len(public)}`",
        f"- Public src symbols with tests: `{sum(bool(tests.get(f'{s.module}.{s.qualname}')) for s in public)}` · with consumers: "
        f"`{sum(bool(consumers.get(f'{s.module}.{s.qualname}')) for s in public)}`",
        f"- Attention items: **{counts.get('high', 0)} high**, {counts.get('medium', 0)} medium, {counts.get('low', 0)} low",
        f"- Tests executed: `{'yes, exit ' + str(tests_result['returncode']) if tests_result else 'no (use --run-tests)'}`",
        "",
        "### Canonical responsibility map", "",
        render_table(["Responsibility", "Inspect first"], [
            ["Data access and Parquet", "`src/utils/storage.py`, `src/utils/config.py`"],
            ["Cohort and supervised artifact", "`src/data/`, cohort notebooks, `tests/test_cohort_source.py`"],
            ["Feature engineering", "`src/features/`, `tests/test_features.py`, YAML `features`"],
            ["Split and leakage", "`src/data/split.py`, `src/evaluation/leakage.py`, split tests"],
            ["Models and pipelines", "`src/models/`, `tests/test_model_pipelines.py`"],
            ["Metrics, calibration, errors", "`src/evaluation/`, `src/models/calibration.py`"],
            ["Experiment logging", "`src/utils/reproducibility.py`"],
            ["Decisions and gates", f"`{args.config}`, `docs/decisoes.md`"],
        ]),
    ]

    # ---- Section 8: configuration
    sec8 = ["## 8. Configuration", ""]
    if isinstance(config, dict):
        if gate_names:
            sec8 += ["### Gates", "", render_table(
                ["Gate", "Status", "Approved by", "Date", "Description"],
                [[f"`{k}`", str(nested_get(gates, k, "status")), str(nested_get(gates, k, "aprovado_por")),
                  str(nested_get(gates, k, "data")), str(nested_get(gates, k, "descricao") or "").strip()[:160]]
                 for k in gates]), ""]
        sec8 += ["### Flattened active configuration", "", f"Source: `{args.config}`", ""]
        sec8 += [f"- `{k}`: `{repr(v)[:400]}`" for k, v in flatten_mapping(config).items()]
    else:
        sec8.append(f"- Configuration unavailable: `{config_error}`")
    sec8 += ["", "### YAML files", "", render_table(
        ["File", "Parse", "Duplicated keys"],
        [[f"`{p}`", "ok" if not d["error"] else d["error"][:80], ", ".join(d["duplicates"]) or "none"]
         for p, d in sorted(yaml_docs.items())])]
    sec8 += ["", "### pyproject.toml", ""]
    if pyproject_data is not None:
        sec8 += [
            f"- Valid TOML: yes · name `{nested_get(pyproject_data, 'project', 'name')}` · "
            f"requires-python `{nested_get(pyproject_data, 'project', 'requires-python')}`",
            "- Dependencies: " + (", ".join(f"`{k}{v}`" for k, v in (pyproject_deps or {}).items()) or "none"),
        ]
    else:
        sec8.append(f"- {pyproject_error or 'not found'}")
    sec8 += ["", "### requirements.txt", "",
             "- " + (", ".join(f"`{k}{v}`" for k, v in requirements.items()) if requirements else "not found")]

    # ---- Section 9: environment
    key_rows = []
    declared = {**(requirements or {}), **(pyproject_deps or {})}
    for name in KEY_PACKAGES:
        if name in packages or name in declared:
            key_rows.append([f"`{name}`", packages.get(name, "**not installed**"),
                             (requirements or {}).get(name, "—") if requirements is not None else "n/a",
                             (pyproject_deps or {}).get(name, "—") if pyproject_deps is not None else "n/a"])
    sec9 = [
        "## 9. Python environment", "",
        f"- Interpreter: `{sys.version.split()[0]}` · implementation `{platform.python_implementation()}`",
        f"- Executable inside repo venv: `{'yes' if str(root).lower() in sys.executable.lower() else 'no (results reflect another interpreter)'}`",
        f"- Platform: `{platform.platform()}`",
        f"- PyYAML available: `{yaml is not None}` · tomllib available: `{tomllib is not None}`",
        "", "### Key packages: installed vs declared", "",
        render_table(["Package", "Installed", "requirements.txt", "pyproject.toml"], key_rows),
        "", "### All installed distributions", "",
        code_block("\n".join(f"{k}=={v}" for k, v in packages.items()), "text"),
    ]

    # ---- Section 10: inventory
    sec10 = [
        "## 10. Path inventory of the working folder", "",
        "Contents of data/models are never copied. `ignored` = exists locally but is ignored by Git.", "",
        "### Directory tree", "", render_tree(inventory), "",
        "### All files", "",
        render_table(["Path", "Git", "Size", "Modified (UTC)"],
                     [[f"`{r['path']}`", r["git"], human_bytes(r["bytes"]), r["modified_utc"]] for r in inventory]),
        "", "### Skipped files", "", *(f"- `{s}`" for s in skipped), *([] if skipped else ["- None."]),
        "", "### .gitignore check for local folders", "", code_block(gitignore_check or "n/a", "text"),
    ]

    # ---- Section 11: tests
    test_rows = []
    for f in python_files:
        if f.path.startswith("tests/") or Path(f.path).name.startswith("test_"):
            names = [s.qualname for s in f.symbols if s.name.startswith("test_")]
            test_rows.append([f"`{f.path}`", str(len(names)), ", ".join(f"`{v}`" for v in f.internal_imports) or "none"])
    sec11 = ["## 11. Tests", "", render_table(["Test file", "Tests", "Internal imports"], test_rows), ""]
    if tests_result:
        sec11 += [f"### pytest result (exit `{tests_result['returncode']}`)", "",
                  f"Command: `{tests_result['command']}`", "",
                  code_block(truncate(redactor(tests_result["output"])[0], 60_000), "text")]
    else:
        sec11.append("pytest was not executed. Use `--run-tests` (optionally `--pytest-args \"-m 'not slow'\"`).")

    # ---- Section 13/14/15
    dep_rows = [[f"`{f.module}`", ", ".join(f"`{v}`" for v in f.internal_imports) or "none"]
                for f in sorted(python_files, key=lambda x: x.module)]
    sec13 = ["## 13. Internal dependency map", "", render_table(["Module", "Internal imports"], dep_rows)]
    nb_rows = [[f"`{n.path}`", f"{n.code_cells}/{n.markdown_cells}", f"{n.executed_cells}/{n.code_cells}",
                "yes" if n.out_of_order else "no", str(len(n.error_outputs)),
                ", ".join(f"`{v}`" for v in n.internal_imports) or "none",
                ", ".join(f"`{s.name}`" for s in n.functions + n.classes) or "none"]
               for n in sorted(notebooks, key=lambda x: x.path)]
    sec14 = ["## 14. Notebook orchestration inventory", "",
             render_table(["Notebook", "Code/MD cells", "Executed", "Out of order", "Errors",
                           "Internal imports", "Local functions"], nb_rows), ""]
    for n in sorted(notebooks, key=lambda x: x.path):
        sec14 += [f"### `{n.path}` headings", "", *(f"- {h}" for h in n.headings), ""]
        if n.file_literals:
            sec14 += ["Referenced files: " + ", ".join(f"`{v}`" for v in n.file_literals), ""]
    env_index: defaultdict[str, set[str]] = defaultdict(set)
    for f in python_files:
        for e in f.env_vars:
            env_index[e].add(f.path)
    for n in notebooks:
        for e in n.env_vars:
            env_index[e].add(n.path)
    lit_index: defaultdict[str, set[str]] = defaultdict(set)
    for f in python_files:
        for lit in f.file_literals:
            lit_index[lit].add(f.path)
    for n in notebooks:
        for lit in n.file_literals:
            lit_index[lit].add(n.path)
    sec15 = ["## 15. Environment variables, file literals and TODOs", "",
             "### Environment variables (names only)", "",
             *([f"- `{k}`: " + ", ".join(f"`{p}`" for p in sorted(v)) for k, v in sorted(env_index.items())] or ["- None."]),
             "", "### File names referenced in code", "",
             *([f"- `{k}` ← " + ", ".join(f"`{p}`" for p in sorted(v)) for k, v in sorted(lit_index.items())] or ["- None."]),
             "", "### TODO / FIXME / PENDENTE markers", "", *([f"- `{t}`" for t in todos] or ["- None."])]

    sec16 = ["## 16. Git history and uncommitted changes", "",
             "### Status", "", code_block(status_text, "text"), "",
             "### Branches", "", code_block(redactor(branches)[0] or "n/a", "text"), "",
             f"### Last {args.git_log} commits", "", code_block(redactor(log_text)[0] or "no commits", "text"), "",
             "### Diff stat (working tree vs HEAD)", "", code_block(diff_stat or "no changes", "text")]
    if args.include_diff:
        sec16 += ["", "### Full diff (working tree vs HEAD)", "", code_block(diff_text or "no changes", "diff")]

    document_parts = [
        CONTEXT.format(schema=SCHEMA_VERSION).rstrip(), "",
        *sec6, "",
        "## 7. Static attention report", "", render_attention(attention), "",
        *sec8, "", *sec9, "", *sec10, "", *sec11, "",
        "## 12. Python API and reuse catalog", "",
        "Generated with Python AST; project modules are not imported.", "",
        render_python_api(python_files, consumers, tests), "",
        *sec13, "", *sec14, "", *sec15, "", *sec16, "",
        "## 17. Full source by file", "",
        "Every relevant file of the repository, including untracked files in source folders. "
        "Notebooks include cell sources and, unless disabled, text outputs.", "",
        "\n".join(source_sections).rstrip(), "",
        "## 18. Local artifacts (small text files from data/, outputs/, reports/, models/)", "",
        ("\n".join(artifact_sections).rstrip() if artifact_sections else "- None included (use defaults or check --no-artifacts)."),
        "",
        "## 19. Snapshot provenance", "",
        f"- Generated UTC: `{generated}`",
        f"- Branch / commit: `{branch}` / `{commit}`",
        f"- Origin: `{remote or 'not configured'}`",
        f"- Generator options: `{ {k: (str(v) if isinstance(v, Path) else v) for k, v in vars(args).items()} }`",
    ]
    document = "\n".join(document_parts).rstrip() + "\n"

    machine = {
        "schema_version": SCHEMA_VERSION,
        "generated_utc": generated,
        "repository": {"branch": branch, "commit": commit, "origin": remote or None,
                       "status": status_text, "ahead_behind": ahead_behind},
        "environment": {"python": sys.version.split()[0], "platform": platform.platform(), "packages": packages},
        "inventory": inventory,
        "files": file_records,
        "artifacts": artifact_records,
        "python_files": [asdict(f) for f in python_files],
        "notebooks": [asdict(n) for n in notebooks],
        "consumers": consumers,
        "tests_by_symbol": tests,
        "attention": [asdict(a) for a in attention],
        "environment_variables": {k: sorted(v) for k, v in sorted(env_index.items())},
        "config": config if isinstance(config, (dict, list)) else None,
        "config_error": config_error,
        "yaml_files": yaml_docs,
        "pyproject": {"valid": pyproject_data is not None, "error": pyproject_error, "dependencies": pyproject_deps},
        "requirements": requirements,
        "tests_result": tests_result,
        "todos": todos,
        "skipped": skipped,
    }
    return document, machine


def parse_args() -> argparse.Namespace:
    # argparse rejects values that start with "-" (e.g. --pytest-args "-m 'not slow'").
    argv = sys.argv[1:]
    for index, value in enumerate(argv[:-1]):
        if value == "--pytest-args" and argv[index + 1].startswith("-"):
            argv[index : index + 2] = [f"--pytest-args={argv[index + 1]}"]
            break
    parser = argparse.ArgumentParser(
        description="Generate a complete diagnostic snapshot of the repository for review by a person or an AI.")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR, help="Destination folder (default: docs).")
    parser.add_argument("--config", default="configs/supervised.yaml", help="Main YAML configuration (relative path).")
    parser.add_argument("--split-mb", type=float, default=DEFAULT_SPLIT_MB,
                        help=f"Size of each part in docs/{PARTS_DIR_NAME}/ (default: {DEFAULT_SPLIT_MB} MB).")
    parser.add_argument("--no-split", dest="split", action="store_false",
                        help=f"Do not write docs/{PARTS_DIR_NAME}/.")
    parser.add_argument("--no-notebook-outputs", dest="notebook_outputs", action="store_false",
                        help="Omit notebook outputs (sources only).")
    parser.add_argument("--max-output-chars", type=int, default=DEFAULT_MAX_OUTPUT_CHARS,
                        help="Maximum characters per notebook output.")
    parser.add_argument("--no-artifacts", dest="artifacts", action="store_false",
                        help="Do not include small text artifacts from data/, outputs/, reports/, models/.")
    parser.add_argument("--max-artifact-bytes", type=int, default=DEFAULT_MAX_ARTIFACT_BYTES)
    parser.add_argument("--max-csv-rows", type=int, default=DEFAULT_MAX_CSV_ROWS)
    parser.add_argument("--max-inline-bytes", type=int, default=DEFAULT_MAX_INLINE_BYTES,
                        help="Files above this size are truncated (notebooks use a reduced view).")
    parser.add_argument("--git-log", type=int, default=DEFAULT_GIT_LOG, help="Number of recent commits to list.")
    parser.add_argument("--no-diff", dest="include_diff", action="store_false", help="Omit the full uncommitted diff.")
    parser.add_argument("--max-diff-chars", type=int, default=DEFAULT_MAX_DIFF_CHARS)
    parser.add_argument("--run-tests", action="store_true", help="Run pytest and include the result (executes project code).")
    parser.add_argument("--pytest-args", default="", help="Extra pytest arguments, e.g. \"-m 'not slow'\".")
    parser.add_argument("--test-timeout", type=int, default=1800)
    parser.add_argument("--fail-on-high", action="store_true", help="Exit with code 2 if HIGH attention items exist.")
    return parser.parse_args(argv)


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # Windows consoles
        except Exception:
            pass
    args = parse_args()
    root = root_dir()
    document, machine = build_reference(root, args)
    out_dir = root / args.output_dir
    output_md = out_dir / OUTPUT_MD_NAME
    output_json = out_dir / OUTPUT_JSON_NAME
    atomic_write(output_md, document)
    atomic_write(output_json, json.dumps(machine, ensure_ascii=False, indent=2, default=str) + "\n")

    parts_dir = out_dir / PARTS_DIR_NAME
    if parts_dir.exists():
        for old in parts_dir.glob("part_*.md"):
            old.unlink()
    written_parts: list[Path] = []
    if args.split and args.split_mb > 0:
        parts = split_document(document, int(args.split_mb * 1024 * 1024))
        for index, part in enumerate(parts, 1):
            target = parts_dir / f"part_{index:02d}_of_{len(parts):02d}.md"
            header = f"<!-- PROJECT_COMPLETE_REFERENCE part {index}/{len(parts)} -->\n"
            atomic_write(target, header + part)
            written_parts.append(target)

    high = sum(a.get("severity") == "high" for a in machine["attention"])
    print(f"update_project_reference.py schema v{SCHEMA_VERSION}")
    print(f"Updated: {output_md} ({human_bytes(output_md.stat().st_size)})")
    print(f"Updated: {output_json} ({human_bytes(output_json.stat().st_size)})")
    if written_parts:
        print(f"Parts:   {len(written_parts)} file(s) in {parts_dir}")
        for part in written_parts:
            print(f"         {part.name} ({human_bytes(part.stat().st_size)})")
    else:
        print("Parts:   not written (--no-split)")
    print(f"Inventory: {len(machine['inventory'])} files, full source: {len(machine['files'])}, "
          f"artifacts: {len(machine['artifacts'])}")
    print(f"Python modules: {len(machine['python_files'])}, notebooks: {len(machine['notebooks'])}")
    print(f"Attention items: {len(machine['attention'])} ({high} high)")
    if machine.get("tests_result"):
        print(f"pytest exit code: {machine['tests_result']['returncode']}")
    if args.fail_on_high and high:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

## `configs/paths.local.json`

- Git: `untracked (working tree)` · status `!! ignored by .gitignore`
- Size: `45 B` · modified `2026-10-08 01:30 UTC`
- SHA-256: `6a840ee1f558f2fa14ca762c3df41bf82300c680614792cd298d857ea68da198`

```json
{
"parquet_srag": "data/raw/srag.parquet"
}
```

## 18. Local artifacts (small text files from data/, outputs/, reports/, models/)

### `data/manifest_dados-v2.yaml`

- Git: `tracked` · `1.9 KB` · modified `2026-10-17 19:30 UTC`

```yaml
manifest_version: "1.0"

dataset:
  id: "srag-dados-v2"
  versao: "dados-v2"
  arquivo: "srag.parquet"
  formato: "parquet"
  caminho_relativo: "data/processed/dados-v2/srag.parquet"

integridade:
  sha256: "96ED6B9D5CEEBAAEA00659F77511112174B04BB980CB243B560C00DD2A8F316C
  tamanho_bytes: 303573013
  quantidade_linhas: 4666910
  quantidade_colunas: 198

cobertura_temporal:
  periodo_nominal_fontes: "2019-2026"
  periodo_observado_dt_notific:
    inicio: "2018-12-30"
    fim: "2026-09-28"
  observacao:
    - "Foram observados três registros com dt_notific em 2018."
    - "A elegibilidade temporal da coorte será definida por dt_interna, não por dt_notific."
    - "O recorte analítico principal considera internações entre 2019 e 2026."
    - "O ano de 2026 está incompleto na versão atual dos dados e deverá ser identificado como tal nas análises temporais."
    - "Os anos associados à pandemia serão mantidos inicialmente; qualquer exclusão posterior será tratada como análise de sensibilidade."

geracao:
  data_geracao: "2026-10-09"
  motivo_nova_versao: >
    Correção da geração de dt_notific. Na versão dados-v1,
    a coluna não preservava as datas individuais de notificação
    e apresentava valores concentrados em âncoras anuais do
    calendário epidemiológico. A versão dados-v2 preserva os
    valores individuais provenientes das fontes oficiais.

fontes:
  - nome: "Dados Abertos do SUS - SRAG 2019 a 2026"
    url: "https://dadosabertos.saude.gov.br/dataset/srag-2019-a-2026"

uso_no_projeto:
  interface_leitura: "src.utils.storage.read_srag"
  versao_configurada: "dados-v2"
  observacao: >
    Os notebooks devem acessar o dataset pela interface de storage
    do repositório, evitando caminhos locais absolutos.

validacao:
  schema_verificado: true
  dimensoes_verificadas: true
  notebook_validacao: "01_eda_primeira_passagem.ipynb"
  hash_confirmado_manualmente: true
```

### `data/analytical/dataset_supervisionado.meta.json`

- Git: `ignored` · `1.7 KB` · modified `2026-10-17 19:14 UTC`

```json
{
  "versao": "0.1",
  "criado_em": "2026-10-17T16:14:53",
  "arquivo": "<REPO>\\data\\analytical\\dataset_supervisionado.parquet",
  "n_linhas": 3739615,
  "colunas": [
    "nu_notific",
    "dt_interna",
    "evolucao",
    "idade_anos",
    "cs_gestant",
    "cs_raca",
    "cs_zona",
    "ave_suino",
    "febre",
    "tosse",
    "garganta",
    "dispneia",
    "diarreia",
    "vomito",
    "dor_abd",
    "fadiga",
    "perd_olft",
    "perd_pala",
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
    "out_morbi",
    "sg_uf",
    "faixa_etaria",
    "ano_internacao"
  ],
  "alvo": "evolucao",
  "coluna_tempo": "dt_interna",
  "anos": {
    "2019": 43513,
    "2020": 979812,
    "2021": 1480215,
    "2022": 475980,
    "2023": 240704,
    "2024": 229478,
    "2025": 289913
  },
  "desenvolvimento": [
    2019,
    2020,
    2021,
    2022,
    2023,
    2024
  ],
  "holdout": [
    2025
  ],
  "features_proibidas_no_dataset": [],
  "features_ausentes_na_base": [
    "DIAS_SINTOMAS_ATE_INTERNACAO",
    "SEXO_CATEGORIA"
  ],
  "base_origem_linhas": 4666910,
  "aliases_aplicados_yaml_para_fisico": {},
  "descartadas_data_tempo_invalida": 0,
  "derivadas_criadas": [
    "idade_anos",
    "faixa_etaria"
  ],
  "grupos_avaliacao_incluidos": [
    "sg_uf",
    "faixa_etaria"
  ],
  "sha256": "b43e34cc04bc0581dcc10f127eedf73fda3aff8a371409ff3ee807cbc384543c"
}
```

### `data/analytical/dataset_supervisionado_sem_2020_2021.meta.json`

- Git: `ignored` · `1.9 KB` · modified `2026-10-17 00:51 UTC`

```json
{
  "versao": "0.1",
  "criado_em": "2026-10-16T21:51:46",
  "arquivo": "<REPO>\\data\\analytical\\dataset_supervisionado_sem_2020_2021.parquet",
  "n_linhas": 1279588,
  "colunas": [
    "nu_notific",
    "dt_interna",
    "evolucao",
    "idade_anos",
    "cs_gestant",
    "cs_raca",
    "cs_zona",
    "ave_suino",
    "febre",
    "tosse",
    "garganta",
    "dispneia",
    "diarreia",
    "vomito",
    "dor_abd",
    "fadiga",
    "perd_olft",
    "perd_pala",
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
    "out_morbi",
    "sg_uf",
    "faixa_etaria",
    "ano_internacao",
    "split"
  ],
  "alvo": "evolucao",
  "coluna_tempo": "dt_interna",
  "anos": {
    "2019": 43513,
    "2022": 475980,
    "2023": 240704,
    "2024": 229478,
    "2025": 289913
  },
  "desenvolvimento": [
    2019,
    2022,
    2023,
    2024,
    2025
  ],
  "holdout": [],
  "features_proibidas_no_dataset": [],
  "features_ausentes_na_base": [
    "DIAS_SINTOMAS_ATE_INTERNACAO",
    "SEXO_CATEGORIA"
  ],
  "base_origem_linhas": 4666910,
  "aliases_aplicados_yaml_para_fisico": {},
  "descartadas_data_tempo_invalida": 0,
  "derivadas_criadas": [
    "idade_anos",
    "faixa_etaria"
  ],
  "grupos_avaliacao_incluidos": [
    "sg_uf",
    "faixa_etaria"
  ],
  "sha256": "e7c5c4a56d29bc72aab0b0c9a7b6dd67dae4830e758c97998a4bac1aca5444b9",
  "split": {
    "tipo": "aleatorio",
    "seed": 42,
    "fracoes": {
      "treino": 0.7,
      "validacao": 0.15,
      "holdout": 0.15
    },
    "contagem": {
      "treino": 895712,
      "holdout": 191938,
      "validacao": 191938
    }
  }
}
```

### `data/analytical/dataset_supervisionado_todos_2019_2025.meta.json`

- Git: `ignored` · `1.9 KB` · modified `2026-10-17 00:50 UTC`

```json
{
  "versao": "0.1",
  "criado_em": "2026-10-16T21:50:56",
  "arquivo": "<REPO>\\data\\analytical\\dataset_supervisionado_todos_2019_2025.parquet",
  "n_linhas": 3739615,
  "colunas": [
    "nu_notific",
    "dt_interna",
    "evolucao",
    "idade_anos",
    "cs_gestant",
    "cs_raca",
    "cs_zona",
    "ave_suino",
    "febre",
    "tosse",
    "garganta",
    "dispneia",
    "diarreia",
    "vomito",
    "dor_abd",
    "fadiga",
    "perd_olft",
    "perd_pala",
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
    "out_morbi",
    "sg_uf",
    "faixa_etaria",
    "ano_internacao",
    "split"
  ],
  "alvo": "evolucao",
  "coluna_tempo": "dt_interna",
  "anos": {
    "2019": 43513,
    "2020": 979812,
    "2021": 1480215,
    "2022": 475980,
    "2023": 240704,
    "2024": 229478,
    "2025": 289913
  },
  "desenvolvimento": [
    2019,
    2020,
    2021,
    2022,
    2023,
    2024,
    2025
  ],
  "holdout": [],
  "features_proibidas_no_dataset": [],
  "features_ausentes_na_base": [
    "DIAS_SINTOMAS_ATE_INTERNACAO",
    "SEXO_CATEGORIA"
  ],
  "base_origem_linhas": 4666910,
  "aliases_aplicados_yaml_para_fisico": {},
  "descartadas_data_tempo_invalida": 0,
  "derivadas_criadas": [
    "idade_anos",
    "faixa_etaria"
  ],
  "grupos_avaliacao_incluidos": [
    "sg_uf",
    "faixa_etaria"
  ],
  "sha256": "7348b0e2f7403116d544fc27117dfe5f838fbd707f112c6b35df50ea3d2b94e4",
  "split": {
    "tipo": "aleatorio",
    "seed": 42,
    "fracoes": {
      "treino": 0.7,
      "validacao": 0.15,
      "holdout": 0.15
    },
    "contagem": {
      "treino": 2617730,
      "holdout": 560943,
      "validacao": 560942
    }
  }
}
```

### `data/analytical/manifesto_supervisionado.json`

- Git: `ignored` · `2.3 KB` · modified `2026-10-17 00:43 UTC`

```json
{
  "schema_version": 2,
  "generated_utc": "2026-10-17T00:43:25.222942+00:00",
  "cohort_kind": "provisional",
  "source": {
    "kind": "provisional",
    "path": "<REPO>\\data\\analytical\\coorte_provisoria_b.parquet",
    "sha256": "da94652dbabd832f512f8346f19ef3fb12adc3e418c27c9229d693b4fe43c7f9",
    "size_bytes": 209678288,
    "rows": 3915136,
    "columns": 125
  },
  "dataset_path": "<REPO>\\data\\analytical\\dataset_supervisionado.parquet",
  "dataset_sha256": "408e5d40ef3dc82a57af5b5c9706a224641c7f0808819d333f48d4638d4e022b",
  "rows": 3915132,
  "columns": 43,
  "feature_columns": [
    "idade_anos",
    "dias_sintomas_ate_internacao",
    "sexo_categoria",
    "cs_gestant",
    "cs_raca",
    "cs_zona",
    "ave_suino",
    "febre",
    "tosse",
    "garganta",
    "dispneia",
    "diarreia",
    "vomito",
    "dor_abd",
    "fadiga",
    "perd_olft",
    "perd_pala",
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
    "out_morbi"
  ],
  "numeric_columns": [
    "idade_anos",
    "dias_sintomas_ate_internacao"
  ],
  "categorical_columns": [
    "sexo_categoria",
    "cs_gestant",
    "cs_raca",
    "cs_zona",
    "ave_suino",
    "febre",
    "tosse",
    "garganta",
    "dispneia",
    "diarreia",
    "vomito",
    "dor_abd",
    "fadiga",
    "perd_olft",
    "perd_pala",
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
    "out_morbi"
  ],
  "audit_columns": [
    "nu_notific",
    "grupo_split",
    "ano_internacao",
    "sg_uf",
    "faixa_etaria",
    "cs_escol_n",
    "vacina",
    "vacina_cov",
    "saturacao",
    "desc_resp"
  ],
  "target_column": "alvo_obito_srag",
  "partition_column": "particao",
  "partition_counts": {
    "treino": 2740584,
    "teste": 587276,
    "validacao": 587272
  },
  "seed": 42,
  "test_opened": false
}
```

### `outputs/tables/pessoa_a/a1_alvo_por_ano.csv`

- Git: `ignored` · `830 B` · modified `2026-10-17 19:14 UTC` · 32 rows

```csv
ano,1,2,3,9,<vazio>,total
1917,1,0,0,0,3,4
1918,0,0,0,0,1,1
1941,1,0,0,1,2,4
2009,1,0,0,0,0,1
2011,1,0,0,0,0,1
2012,2,0,0,0,0,2
2016,0,1,0,0,0,1
2017,2,0,0,0,0,2
2018,10,0,0,0,1,11
2019,38292,5221,8,1340,2682,47543
2020,705699,274113,15414,20385,60753,1076364
2021,1062924,417291,21305,38603,117266,1657389
2022,389547,86433,13727,12552,33874,536133
2023,217667,23037,7724,5528,11713,265669
2024,210358,19120,7220,4212,12457,253367
2025,268686,21227,8252,5561,11889,315615
2026,165784,9743,5014,4454,25442,210437
2027,6,0,0,1,0,7
2028,4,0,0,0,0,4
2029,3,0,0,3,3,9
2031,2,0,0,0,0,2
2032,1,0,0,0,0,1
2033,0,0,0,0,3,3
2034,0,0,0,1,0,1
2050,0,0,0,0,1,1
2052,1,0,0,0,0,1
2055,0,0,0,0,1,1
2056,0,0,0,0,1,1
2092,1,0,0,0,0,1
2098,1,0,0,1,0,2
2099,1,0,0,0,0,1
sem_data,38927,16729,1383,2610,12429,72078
```

### `outputs/tables/pessoa_a/a1_amostra_exclusoes_01.csv`

- Git: `ignored` · `3.5 KB` · modified `2026-10-17 19:14 UTC` · 50 rows

```csv
HOSPITAL,DT_INTERNA,EVOLUCAO,TP_IDADE,NU_IDADE_N,DT_NASC,DT_SIN_PRI,DT_NOTIFIC,DT_EVOLUCA,DT_ENCERRA,NU_NOTIFIC
,,,3,75,1950-11-02,2026-03-22,2026-03-23,,,31775652598724
2,,1,3,4,2022-03-03,2026-03-23,2026-03-29,2026-03-31,2026-06-11,31781205405890
,,1,2,8,2025-08-09,2026-04-18,2026-04-28,2026-04-19,2026-06-02,31780414044334
2,,1,3,50,1975-04-08,2026-03-07,2026-03-07,,2026-03-20,31776951547485
,,1,3,83,1942-12-21,2026-08-10,2026-08-13,,2026-08-13,31786648314248
,,9,3,8,2017-09-29,2026-03-25,2026-03-26,,2026-03-30,31776114768213
2,,,3,7,2019-02-21,2026-04-18,2026-04-22,,2026-04-26,31777485114556
,,1,2,4,2026-03-22,2026-07-12,2026-07-13,2026-07-21,2026-07-21,31784037049124
,,1,3,4,2021-09-27,2026-06-01,2026-06-15,,2026-07-23,31781782758352
,,,3,75,1950-09-14,2026-06-07,2026-06-08,,,31780925222220
,,,3,65,1960-07-08,2026-04-01,2026-04-14,,,31784125722808
,,,3,9,2016-07-22,2026-01-13,2026-01-18,,,31768751302378
2,,,2,7,2025-06-18,2026-01-04,2026-01-07,,,31767972796009
,,,3,5,2020-10-10,2026-08-18,2026-08-20,,,31787317509231
,,1,3,1,2025-01-15,2026-05-06,2026-05-06,,2026-05-08,31780258970676
9,,1,3,4,2021-09-06,2026-05-03,2026-05-03,2026-05-05,2026-07-03,31783105365899
2,,2,3,1,2025-03-11,2026-05-28,2026-06-09,2026-06-09,2026-06-16,31782311120470
,,1,2,6,2025-11-02,2026-05-20,2026-05-21,2026-06-08,2026-06-23,31782218952764
,,,2,7,2026-01-06,2026-08-02,2026-08-07,,,31786119085137
,,,3,73,1952-08-22,2026-04-04,2026-04-13,,,31776078195609
,,1,3,57,1968-08-22,2026-04-29,2026-04-30,,2026-05-12,31778069604877
,,1,3,1,2025-04-14,2026-04-24,2026-04-27,,2026-05-05,31777322020581
9,,1,3,40,1985-05-02,2026-01-30,2026-02-03,,2026-08-03,31772451218119
2,,1,2,2,2026-04-13,2026-06-19,2026-06-22,2026-06-26,2026-06-26,31782249136338
2,,1,3,6,2020-03-01,2026-05-03,2026-05-07,,2026-05-13,31778676513948
,,,3,9,2017-02-18,2026-06-23,2026-06-24,,,31782997221458
,,,2,2,2026-05-23,2026-07-06,2026-07-06,,,31783376982074
,,,3,80,1945-10-02,2026-02-28,2026-03-06,,2026-03-18,31772828882255
,,1,2,8,2025-11-28,2026-07-21,2026-07-24,,2026-07-24,31785406932822
,,1,2,6,2026-02-17,2026-08-07,2026-08-11,2026-08-12,2026-08-31,31787766202549
2,,2,3,12,2014-02-11,2026-03-19,2026-03-27,2026-03-27,2026-03-27,31774964608477
,,1,3,1,2024-10-01,2026-02-09,2026-02-09,,2026-02-13,31779580487653
2,,2,3,88,1937-10-25,2026-01-27,2026-01-31,2026-01-31,2026-02-12,31774289284081
2,,,3,2,2023-10-15,2026-04-22,2026-04-24,,2026-04-28,31777486180757
,,,3,66,1960-04-14,2026-08-08,2026-08-12,,,31786571794321
,,,3,1,2024-10-13,2026-06-11,2026-06-17,,,31781707959452
,,1,3,57,1969-05-11,2026-08-14,2026-08-17,2026-08-19,2026-08-19,31786973020085
9,,,3,46,1979-11-27,2026-09-01,2026-09-02,,,31788371070901
,,1,3,1,2024-12-23,2026-04-11,2026-04-16,,2026-06-08,31776357800729
,,,3,1,2025-01-04,2026-04-05,2026-04-16,,,31776343591581
2,,1,3,41,1984-05-03,2026-02-22,2026-03-02,2026-02-24,2026-03-02,31772423427061
,,1,2,11,2025-08-30,2026-07-23,2026-07-24,,2026-08-03,31784914226565
,,1,2,4,2025-09-06,2026-01-12,2026-01-12,2026-01-26,2026-02-06,31769008935928
,,,3,35,1991-08-07,2026-08-15,2026-08-18,,,31787060140830
,,,3,2,2024-05-29,2026-08-21,2026-08-28,,,31789074988249
2,,1,3,90,1935-08-24,2026-01-07,2026-01-09,2026-01-09,2026-01-14,31768403627553
,,1,3,67,1959-01-29,2026-06-15,2026-06-16,2026-06-19,2026-06-25,31781696854761
2,,1,3,42,1983-12-15,2026-01-14,2026-02-08,,2026-02-08,31770572532065
2,,2,3,64,1961-07-01,2026-02-21,2026-02-21,2026-02-21,2026-02-21,31773350909558
,,,3,58,1968-06-08,2026-07-16,2026-07-21,,2026-08-10,31784646474693
```

### `outputs/tables/pessoa_a/a1_amostra_exclusoes_02.csv`

- Git: `ignored` · `3.6 KB` · modified `2026-10-17 19:14 UTC` · 50 rows

```csv
HOSPITAL,DT_INTERNA,EVOLUCAO,TP_IDADE,NU_IDADE_N,DT_NASC,DT_SIN_PRI,DT_NOTIFIC,DT_EVOLUCA,DT_ENCERRA,NU_NOTIFIC
1,,1,2,8,2025-08-10,2026-04-01,2026-04-15,,2026-04-21,31777549715837
1,,1,3,77,1949-05-26,2026-07-12,2026-07-12,2026-07-15,2026-07-17,31788874096772
1,,1,3,7,2018-08-31,2026-01-10,2026-01-12,2026-01-28,2026-02-09,31770647469632
1,,,3,3,2023-04-20,2026-09-04,2026-09-09,,,31788975169679
1,,1,2,3,2025-11-10,2026-02-06,2026-02-07,2026-02-20,2026-06-10,31773940312126
1,,1,3,1,2024-09-24,2026-07-04,2026-08-26,2026-08-11,2026-08-26,31787751835649
1,,1,3,43,1982-11-27,2026-02-21,2026-02-27,2026-03-02,2026-03-05,31772219564355
1,,1,2,1,2025-12-04,2026-01-08,2026-01-12,2026-01-21,2026-01-26,31769453667829
1,,1,2,11,2025-03-16,2026-02-20,2026-02-23,2026-02-24,2026-04-13,31771838270995
1,,1,3,31,1994-11-08,2026-09-06,2026-09-09,2026-09-16,2026-09-17,31789563351861
1,,1,3,62,1963-11-04,2026-02-11,2026-02-13,2026-02-20,2026-03-04,31771008239682
1,,,1,7,2026-05-12,2026-05-19,2026-05-21,,,31779467820819
1,,,3,3,2022-12-09,2026-09-03,2026-09-05,,,31788620734654
1,,,3,4,2021-11-21,2026-07-30,2026-07-31,,,31786458971825
1,,,3,2,2024-03-30,2026-08-01,2026-08-04,,,31785867861406
1,,1,3,2,2023-09-24,2026-07-10,2026-07-20,2026-07-14,2026-07-22,31784748275602
1,,1,3,2,2024-05-11,2026-09-03,2026-09-10,2026-09-15,2026-09-18,31789065947469
1,,,3,2,2024-06-17,2026-09-01,2026-09-02,,,31788382629475
1,,,3,2,2024-06-05,2026-08-14,2026-08-19,,,31787172228431
1,,,3,2,2024-06-25,2026-06-26,2026-07-10,,,31783704794838
1,,,3,1,2024-08-25,2026-06-20,2026-06-22,,,31782152025297
1,,,3,1,2024-12-14,2026-05-03,2026-05-07,,,31778183597383
1,,1,3,1,2025-06-09,2026-08-21,2026-08-24,2026-09-03,2026-09-22,31787583741919
1,,,3,1,2025-07-27,2026-07-28,2026-07-29,,,31785360853298
1,,,2,10,2025-08-16,2026-06-01,2026-06-04,,,31780575267248
1,,1,2,8,2025-08-22,2026-04-25,2026-04-29,2026-05-01,2026-05-25,31777465516478
1,,1,2,7,2025-08-18,2026-03-23,2026-03-28,,2026-04-01,31774888210371
1,,1,3,73,1952-05-15,2026-04-25,2026-04-27,2026-04-30,2026-05-04,31778092086325
1,,1,3,2,2023-11-03,2026-07-07,2026-07-09,2026-07-13,2026-07-14,31783942348556
1,,,3,2,2023-10-10,2026-04-13,2026-04-13,,,31776091074476
1,,1,3,2,2023-11-06,2026-08-25,2026-08-25,,2026-09-11,31787918509080
1,,1,3,75,1950-11-05,2026-06-04,2026-06-11,,2026-06-16,31781178224317
1,,1,3,1,2024-12-27,2026-03-12,2026-03-15,2026-03-16,2026-03-16,31773662225812
1,,2,3,46,1980-03-30,2026-05-04,2026-05-07,2026-05-14,2026-05-15,31778770573608
1,,1,3,2,2024-03-22,2026-04-22,2026-04-29,2026-05-02,2026-05-07,31781007905994
1,,1,3,37,1989-08-03,2026-08-24,2026-08-25,2026-09-04,2026-09-25,31789485848987
1,,,3,50,1975-05-26,2026-01-17,2026-01-18,,2026-01-22,31769099934860
1,,1,3,74,1952-02-15,2026-07-20,2026-08-03,2026-08-03,2026-08-18,31786461727931
1,,1,3,81,1944-05-31,2026-03-27,2026-04-09,2026-04-15,2026-04-20,31775740797449
1,,1,3,2,2024-01-08,2026-09-01,2026-09-03,2026-09-05,2026-09-08,31789128973635
1,,1,3,1,2024-10-17,2026-08-18,2026-08-24,,2026-09-10,31789062515336
1,,1,3,2,2024-01-29,2026-03-17,2026-03-18,2026-03-26,2026-04-03,31775250713894
1,,1,3,27,1998-11-17,2026-05-01,2026-05-09,,2026-05-18,31778336961281
1,,1,3,57,1968-08-22,2026-01-19,2026-02-04,,2026-02-04,31770645711921
1,,,3,2,2024-05-21,2026-08-04,2026-08-06,,2026-08-07,31786039467922
1,,1,3,78,1947-11-07,2026-06-19,2026-06-26,,2026-07-08,31782494985225
1,,1,3,1,2024-02-22,2026-01-06,2026-01-08,2026-01-13,2026-01-14,31768314692248
1,,1,2,8,2025-12-25,2026-08-30,2026-09-02,2026-09-09,2026-09-11,31788527556568
1,,1,3,1,2024-07-23,2026-01-30,2026-02-05,2026-02-13,2026-02-24,31770378778543
1,,,2,7,2026-01-11,2026-09-07,2026-09-11,,,31789140997184
```

### `outputs/tables/pessoa_a/a1_amostra_exclusoes_03.csv`

- Git: `ignored` · `4.1 KB` · modified `2026-10-17 19:14 UTC` · 50 rows

```csv
HOSPITAL,DT_INTERNA,EVOLUCAO,TP_IDADE,NU_IDADE_N,DT_NASC,DT_SIN_PRI,DT_NOTIFIC,DT_EVOLUCA,DT_ENCERRA,NU_NOTIFIC
1,2026-06-11,1,2,1,2026-05-02,2026-06-02,2026-06-11,2026-06-19,2026-06-19,31781201987679
1,2026-06-15,,3,37,1989-04-04,2026-06-15,2026-06-17,,,31782407823707
1,2026-03-10,1,3,4,2021-10-06,2026-03-09,2026-03-14,,,31773493207022
1,2026-03-18,1,1,11,2026-03-07,2026-03-18,2026-03-23,2026-04-14,2026-04-15,31774542694487
1,2026-08-18,,3,75,1950-09-09,2026-08-08,2026-08-18,,,31787085791388
1,2026-03-10,1,3,78,1947-11-10,2026-03-10,2026-03-10,2026-03-16,2026-03-16,31773441569320
1,2026-05-27,,3,1,2025-03-11,2026-05-19,2026-05-26,,,31780065930274
1,2026-05-08,,2,0,2025-05-13,2026-05-05,2026-05-08,,,31779901434401
1,2026-06-15,,3,66,1960-06-13,2026-06-14,2026-06-16,,,31781629359036
1,2026-05-23,,3,15,2011-04-14,2026-05-23,2026-05-24,,,31780947295202
1,2026-07-07,1,3,4,2021-07-14,2026-07-03,2026-07-09,2026-07-11,2026-07-17,31783622594901
1,2026-04-04,,3,32,1993-09-15,2026-04-04,2026-04-04,,,31779149516127
1,2026-05-13,1,2,6,2025-11-17,2026-05-12,2026-05-13,2026-05-15,2026-05-21,31779376399165
1,2026-05-15,,3,74,1952-04-18,2026-05-15,2026-05-16,,,31779137099882
1,2026-03-19,1,3,11,2014-09-18,2026-03-19,2026-03-20,2026-03-28,2026-04-06,31775493343412
1,2026-05-19,,3,75,1950-12-19,2026-05-16,2026-05-22,,,31779804314537
1,2026-09-08,,2,5,2026-03-21,2026-09-08,2026-09-09,,,31788967146868
1,2026-06-02,1,2,1,2026-04-22,2026-05-27,2026-06-03,2026-06-16,2026-06-19,31780508092246
1,2026-04-14,1,2,5,2025-11-23,2026-04-14,2026-05-04,2026-04-14,2026-05-04,31777902324367
1,2026-04-22,1,3,31,1995-01-25,2026-04-19,2026-04-23,2026-05-04,2026-05-11,31777581635868
1,2026-03-28,,3,1,2024-10-25,2026-03-08,2026-03-28,,,31774869565386
1,2026-04-11,1,3,5,2020-06-26,2026-04-05,2026-04-11,2026-04-13,2026-04-17,31776433120192
1,2026-05-26,1,3,12,2013-08-27,2026-05-26,2026-05-28,2026-05-29,2026-06-03,31780063755400
1,2026-03-26,,3,78,1947-12-30,2026-03-26,2026-03-31,,,31775052422525
1,2026-06-02,1,2,4,2026-02-04,2026-06-02,2026-06-03,2026-06-09,2026-07-29,31785339117793
1,2026-08-25,2,3,65,1961-06-06,2026-08-25,2026-08-25,2026-08-27,2026-09-01,31790273405307
1,2026-05-18,1,3,58,1967-11-07,2026-05-16,2026-05-18,2026-05-25,2026-05-25,31779716421577
1,2026-06-20,1,3,25,2001-02-10,2026-06-18,2026-06-20,2026-07-01,2026-07-07,31783419856968
1,2026-05-26,1,3,2,2023-10-10,2026-05-21,2026-05-26,2026-05-30,2026-05-30,31781122407541
1,2026-05-09,1,3,64,1962-02-11,2026-05-08,2026-05-12,2026-05-20,2026-05-20,31778874675119
1,2026-04-13,1,3,80,1946-03-11,2026-04-01,2026-04-16,2026-05-07,2026-05-08,31776340279767
1,2026-03-24,1,3,25,2000-04-11,2026-03-24,2026-03-25,2026-04-03,2026-04-13,31774465391980
1,2026-05-05,1,3,1,2024-12-13,2026-05-05,2026-05-05,2026-05-10,2026-05-11,31778065923802
1,2026-07-27,1,2,3,2026-04-14,2026-07-15,2026-07-27,2026-08-07,2026-08-10,31785175448633
1,2026-01-18,1,3,81,1945-01-17,2026-01-18,2026-01-19,2026-01-24,2026-03-25,31768838162860
1,2026-05-17,1,3,11,2014-07-17,2026-05-10,2026-05-18,2026-05-25,2026-05-29,31779116223319
1,2026-08-09,,3,3,2023-06-18,2026-08-07,2026-08-10,,,31786456692694
1,2026-04-11,,3,15,2010-07-19,2026-04-11,2026-04-11,,,31777560339040
1,2026-06-24,1,3,90,1935-11-19,2026-06-24,2026-06-24,2026-07-10,2026-07-11,31782483816212
1,2026-03-29,1,3,12,2013-06-20,2026-03-26,2026-03-30,2026-04-02,2026-04-02,31776451468405
1,2026-08-13,1,3,3,2023-01-23,2026-08-05,2026-08-13,2026-08-17,2026-09-02,31787326594739
1,2026-06-03,1,3,35,1991-04-24,2026-06-01,2026-06-03,,2026-06-16,31781011168335
1,2026-06-09,1,2,1,2026-05-26,2026-06-09,2026-06-10,2026-06-23,2026-07-24,31781096428357
1,2026-09-19,,3,67,1959-04-27,2026-09-19,2026-09-23,,,31790263201573
1,2026-05-06,,3,1,2024-09-30,2026-05-05,2026-05-06,,,31778163531908
1,2026-03-09,,3,85,1940-10-17,2026-03-08,2026-03-10,,,31773322485191
1,2026-03-12,1,3,1,2024-11-10,2026-03-07,2026-03-12,2026-03-20,2026-03-23,31773400244831
1,2026-07-12,1,3,8,2018-03-13,2026-07-10,2026-07-12,,2026-08-05,31783901810343
1,2026-05-23,1,2,3,2026-02-03,2026-05-22,2026-05-25,2026-05-31,2026-06-19,31779735858953
1,2026-05-06,1,3,2,2023-08-06,2026-05-04,2026-05-06,2026-05-09,2026-05-25,31779714355076
```

### `outputs/tables/pessoa_a/a1_amostra_exclusoes_04.csv`

- Git: `ignored` · `3.8 KB` · modified `2026-10-17 19:14 UTC` · 50 rows

```csv
HOSPITAL,DT_INTERNA,EVOLUCAO,TP_IDADE,NU_IDADE_N,DT_NASC,DT_SIN_PRI,DT_NOTIFIC,DT_EVOLUCA,DT_ENCERRA,NU_NOTIFIC
1,2020-06-21,,2,7,2026-01-27,2026-08-08,2026-08-09,,,31787231962439
1,2025-12-24,9,2,4,2025-12-26,2026-04-09,2026-04-16,,2026-05-25,31776358797785
1,2025-10-03,9,3,4,2021-09-04,2026-03-01,2026-03-04,,2026-06-03,31780500876680
1,2025-12-16,9,2,6,2025-10-07,2026-04-08,2026-04-13,,2026-06-03,31780511592426
1,2025-12-17,,3,48,1977-06-27,2026-01-10,2026-01-12,,2026-04-02,31768219829649
1,2025-10-31,,3,67,1959-02-05,2026-03-16,2026-03-18,,,31773833215234
1,2025-11-01,,3,1,2025-03-26,2026-06-10,2026-06-11,,,31781197871583
1,2025-03-22,,3,75,1951-03-07,2026-03-24,2026-03-25,,,31774544007083
1,2025-01-14,,1,8,2026-01-14,2026-01-22,2026-02-26,,,31772103567239
1,2025-07-29,,2,6,2025-07-29,2026-01-19,2026-01-21,,,31769002628458
1,2025-09-11,,2,9,2025-09-11,2026-06-29,2026-06-29,,,31782995283941
1,2024-11-27,9,3,1,2024-11-11,2026-04-11,2026-04-19,,2026-05-26,31776623873074
1,2025-06-25,,3,1,2025-04-04,2026-05-30,2026-06-30,,2026-07-02,31782913329965
1,2025-12-27,,2,7,2025-12-26,2026-08-24,2026-08-31,,,31788210956301
1,2025-12-27,9,2,3,2025-12-26,2026-03-29,2026-03-30,,2026-05-25,31779819988812
1,2024-11-27,9,3,1,2024-11-11,2026-03-26,2026-03-31,,2026-05-26,31782076559440
1,2025-09-06,9,3,1,2024-11-07,2026-02-12,2026-02-18,,2026-05-25,31771513748972
1,2025-09-18,,3,12,2014-01-27,2026-06-29,2026-07-07,,2026-07-22,31783709799403
1,2024-03-08,,3,3,2022-11-17,2026-03-01,2026-03-12,,,31773333151517
1,2025-07-29,,2,9,2025-07-29,2026-04-18,2026-04-19,,,31776624396581
1,2025-08-08,,2,2,2025-06-13,2025-08-08,2025-08-11,,,31754941893170
1,2025-11-22,,3,63,1962-10-23,2025-11-20,2025-11-22,,,31774014430620
1,2025-08-19,,2,11,2024-09-29,2025-08-19,2025-08-22,,,31756133743688
1,2025-05-29,,2,3,2025-02-02,2025-05-27,2025-05-29,,2025-12-23,31748523312830
1,2025-07-06,,1,20,2025-06-10,2025-06-30,2025-07-06,,,31751895447999
1,2025-05-23,9,3,46,1978-12-12,2025-05-20,2025-05-24,,2025-05-25,31748089238562
1,2025-11-17,,2,8,2025-03-13,2025-11-10,2025-11-19,,,31764859064552
1,2025-05-31,9,3,1,2023-11-18,2025-05-28,2025-05-31,,2025-06-06,31749241564718
1,2025-01-24,9,3,54,1970-08-22,2025-01-16,2025-02-06,,2025-02-06,31738852792527
1,2025-03-29,,3,1,2023-06-23,2025-03-26,2025-03-31,,,31743606324329
1,2025-09-20,,3,75,1950-03-01,2025-09-20,2025-09-27,,2025-10-01,31759177531632
1,2025-08-26,,2,3,2025-05-07,2025-08-26,2025-08-27,,2025-09-01,31756299279917
1,2025-06-25,9,2,7,2024-11-04,2025-06-21,2025-06-25,,2025-07-14,31751467374225
1,2025-07-29,,3,2,2022-08-25,2025-07-28,2025-07-29,,,31754404310472
1,2025-06-19,,3,1,2023-11-14,2025-06-19,2025-06-21,,2025-06-21,31750504750935
1,2025-06-22,,3,3,2021-07-30,2025-06-22,2025-06-23,,,31750795034604
1,2025-07-03,9,1,1,2025-06-28,2025-06-29,2025-07-03,,2025-07-07,31751634307198
1,2025-07-23,,3,13,2011-12-11,2025-07-20,2025-08-08,,,31755001458106
1,2025-05-09,9,2,8,2024-09-07,2025-05-09,2025-06-16,,2025-06-16,31747153986065
1,2025-02-02,,3,1,2023-07-21,2025-01-31,2025-02-04,,,31738672439669
1,2025-04-01,,3,8,2016-12-01,2025-03-31,2025-04-01,,,31743515421873
1,2025-09-15,,2,1,2025-08-19,2025-09-12,2025-09-15,,,31760622681774
1,2025-06-05,9,3,6,2018-09-30,2025-06-01,2025-06-05,,2025-06-18,31749648905665
1,2025-10-23,,3,91,1934-06-23,2025-10-20,2025-10-29,,,31761741761758
1,2025-05-21,9,1,9,2025-05-02,2025-05-11,2025-05-21,,2025-07-10,31747839435766
1,2025-08-21,9,3,5,2019-08-29,2025-08-20,2025-08-26,,2025-09-08,31756211835539
1,2025-06-01,9,3,4,2020-10-29,2025-05-31,2025-06-02,,2025-06-04,31748863954462
1,2025-05-20,,3,75,1949-06-24,2025-05-19,2025-05-20,,,31747801163619
1,2025-07-23,9,3,71,1953-12-10,2025-07-23,2025-07-26,,2025-07-26,31753555880402
1,2025-10-22,9,3,1,2024-01-15,2025-10-22,2025-10-27,,,31761594784556
```

### `outputs/tables/pessoa_a/a1_amostra_exclusoes_05.csv`

- Git: `ignored` · `4.5 KB` · modified `2026-10-17 19:14 UTC` · 50 rows

```csv
HOSPITAL,DT_INTERNA,EVOLUCAO,TP_IDADE,NU_IDADE_N,DT_NASC,DT_SIN_PRI,DT_NOTIFIC,DT_EVOLUCA,DT_ENCERRA,NU_NOTIFIC
1,2025-09-24,3,2,8,2025-08-12,2026-04-11,2026-05-04,2026-04-16,2026-05-04,31777916441450
1,2025-12-03,3,2,1,2025-12-03,2026-01-09,2026-01-30,2026-03-11,2026-03-12,31769792468795
1,2025-12-18,3,3,77,1948-02-08,2026-01-05,2026-01-06,2026-01-06,2026-01-06,31768488161625
1,2025-10-31,3,2,4,2025-10-31,2026-02-04,2026-05-01,2026-04-07,2026-05-01,31777634956473
1,2025-12-30,3,3,50,1975-11-28,2026-01-09,2026-01-13,2026-01-21,2026-02-10,31770727069269
1,2025-12-11,3,3,62,1963-10-16,2026-01-30,2026-02-03,2026-02-13,2026-02-19,31770125136508
1,2025-02-10,3,3,52,1973-02-02,2025-02-09,2025-02-11,2025-02-18,2025-03-11,31739820410851
1,2025-06-27,3,3,81,1944-05-26,2025-06-27,2025-06-30,2025-07-03,2025-07-04,31751305140132
1,2025-08-16,3,2,4,2025-04-18,2025-08-09,2025-08-16,2025-10-11,2025-10-08,31755535974964
1,2025-05-15,3,3,57,1967-10-16,2025-05-08,2025-05-15,2025-05-29,2025-06-13,31747425704642
1,2025-04-10,3,3,68,1956-12-10,2025-04-10,2025-04-24,2025-04-10,2025-05-16,31747403476732
1,2025-03-05,3,3,71,1953-04-23,2025-02-15,2025-03-28,2025-03-05,2025-04-03,31743690196040
1,2025-03-08,3,3,9,2015-06-09,2025-03-07,2025-03-08,2025-03-08,2025-03-14,31741617511408
1,2025-04-17,3,3,54,1971-02-10,2025-04-17,2025-04-17,2025-04-17,2025-04-23,31745430231436
1,2025-07-24,3,3,98,1927-03-01,2025-07-22,2025-07-24,2025-07-31,2025-08-04,31753706945283
1,2025-01-13,3,3,94,1930-09-16,2025-01-03,2025-01-09,2025-02-07,2025-02-23,31737987292722
1,2025-08-06,3,3,37,1987-11-13,2025-08-06,2025-08-08,2025-08-11,2025-08-08,31754680600341
1,2025-04-06,3,3,15,2009-08-26,2025-04-01,2025-04-10,2025-04-10,2025-04-10,31745600659334
1,2025-12-23,3,2,1,2025-11-24,2025-12-20,2025-12-23,2025-12-26,2026-01-20,31766517607662
1,2025-09-02,3,3,36,1988-10-29,2025-09-02,2025-09-12,2025-09-08,2025-09-12,31757676072748
1,2025-07-01,3,3,66,1958-07-01,2025-06-30,2025-07-01,2025-09-04,2025-09-16,31751474441385
1,2025-01-09,3,3,92,1932-09-05,2025-01-09,2025-02-03,2025-01-22,2025-02-03,31738613590398
1,2025-01-20,3,2,5,2024-08-17,2025-01-17,2025-01-20,2025-01-27,2025-02-19,31737476808694
1,2025-07-05,3,3,54,1971-01-20,2025-07-05,2025-07-05,2025-07-07,2025-07-08,31751959045074
1,2025-06-05,3,3,86,1938-09-22,2025-06-04,2025-06-05,2025-06-12,2025-07-09,31752086047118
1,2025-06-20,3,3,57,1967-11-05,2025-06-15,2025-06-27,2025-07-02,2025-07-02,31751046185463
1,2025-05-20,3,3,73,1952-02-02,2025-05-20,2025-05-21,2025-05-22,2025-05-30,31747854379616
1,2025-06-25,3,3,77,1948-05-01,2025-06-25,2025-06-25,2025-07-27,2025-08-22,31750947402157
1,2025-07-18,3,3,78,1946-09-15,2025-07-16,2025-07-18,2025-08-13,2025-08-18,31752816212607
1,2025-01-30,3,3,63,1961-09-30,2025-01-10,2025-01-30,2025-03-08,2025-03-08,31738669486415
1,2025-05-07,3,3,56,1968-10-28,2025-05-07,2025-06-02,2025-06-09,2025-06-12,31748863298033
1,2025-05-30,3,3,73,1951-12-15,2025-05-28,2025-06-02,2025-07-15,2025-07-18,31749474500518
1,2025-04-22,3,2,8,2024-08-28,2025-04-10,2025-04-23,2025-04-23,2025-04-23,31745420160005
1,2025-11-16,3,3,1,2024-01-05,2025-11-13,2025-11-17,2025-11-25,2025-12-11,31764096943902
1,2025-04-11,3,3,65,1960-03-09,2025-04-09,2025-04-14,2025-05-05,2025-05-06,31744640890627
1,2025-06-24,3,3,76,1948-11-18,2025-06-18,2025-06-26,2025-06-28,2025-07-02,31751387763386
1,2025-10-20,3,3,60,1964-12-06,2025-10-17,2025-10-20,2025-10-23,2025-10-31,31761157628603
1,2025-03-14,3,3,43,1981-12-04,2025-03-10,2025-03-17,2025-04-05,2025-06-09,31742315828370
1,2025-04-08,3,3,38,1986-06-19,2025-04-05,2025-04-08,2025-04-08,2025-04-14,31745865241129
1,2025-06-11,3,3,68,1957-05-30,2025-06-10,2025-06-11,2025-06-24,2025-07-01,31749629091064
1,2025-12-03,3,3,54,1971-07-24,2025-11-28,2025-12-03,2025-12-07,2025-12-29,31765400192345
1,2025-09-19,3,3,85,1939-12-14,2025-09-19,2025-09-19,2025-10-08,2025-10-18,31761743862779
1,2025-05-07,3,3,1,2023-10-17,2025-05-05,2025-05-07,2025-05-28,2025-05-30,31747073511832
1,2025-12-23,3,3,57,1968-05-20,2025-12-10,2025-12-24,2026-01-27,2026-01-27,31766574194275
1,2025-08-21,3,3,73,1952-05-02,2025-08-18,2025-08-21,2025-09-17,2025-10-03,31755809317953
1,2025-05-13,3,3,93,1932-02-23,2025-05-09,2025-05-15,2025-06-21,2025-06-24,31747331606130
1,2025-01-22,3,3,87,1937-11-10,2025-01-22,2025-01-22,2025-02-01,2025-02-01,31739541405562
1,2025-08-15,3,3,51,1974-03-22,2025-08-15,2025-08-16,2025-08-19,2025-08-19,31755863690526
1,2025-07-04,3,3,32,1992-12-08,2025-06-27,2025-07-07,2025-07-07,2025-08-20,31755726935268
1,2025-11-22,3,3,65,1960-01-04,2025-11-22,2025-11-25,2026-01-07,2026-01-08,31764096261188
```

### `outputs/tables/pessoa_a/a1_tabela_codigos.csv`

- Git: `ignored` · `3.8 KB` · modified `2026-10-17 19:14 UTC` · 32 rows

```csv
codigo,campo,esperado,1917,1918,1941,2009,2011,2012,2016,2017,2018,2019,2020,2021,2022,2023,2024,2025,2026,2027,2028,2029,2031,2032,2033,2034,2050,2052,2055,2056,2092,2098,2099,sem_data
1,HOSPITAL,True,4,1,4,1,1,2,1,2,11,47543,1076364,1657389,536133,265669,253367,315615,210437,7,4,9,2,1,3,1,1,1,1,1,1,2,1,72078
2,HOSPITAL,True,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,102956
9,HOSPITAL,True,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,10066
<vazio>,HOSPITAL,False,0,0,0,0,0,0,0,0,0,2,11,4,2,2,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,119207
1,EVOLUCAO,True,1,0,1,1,1,2,0,2,10,38294,705704,1062927,389548,217669,210358,268686,165785,6,4,3,2,1,0,0,0,1,0,0,1,1,1,141523
2,EVOLUCAO,True,0,0,0,0,0,0,1,0,0,5221,274119,417293,86433,23037,19120,21227,9743,0,0,0,0,0,0,0,0,0,0,0,0,0,0,79814
3,EVOLUCAO,True,0,0,0,0,0,0,0,0,0,8,15414,21305,13727,7724,7220,8253,5014,0,0,0,0,0,0,0,0,0,0,0,0,0,0,7784
9,EVOLUCAO,True,0,0,1,0,0,0,0,0,0,1340,20385,38603,12552,5528,4212,5561,4454,1,0,3,0,0,0,1,0,0,0,0,0,1,0,10928
<vazio>,EVOLUCAO,False,3,1,2,0,0,0,0,0,1,2682,60753,117266,33875,11713,12457,11889,25442,0,0,3,0,0,3,0,1,0,1,1,0,0,0,64258
1,TP_IDADE,True,0,0,0,0,0,0,0,0,0,1754,3866,5920,4181,3258,3638,4771,2724,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1695
2,TP_IDADE,True,1,0,1,0,1,0,0,0,2,12580,18283,43407,54697,60504,60545,81218,57591,1,0,1,0,0,0,0,0,0,1,0,0,0,0,16103
3,TP_IDADE,True,3,1,3,1,0,2,1,2,9,33211,1054226,1608067,477257,201909,189184,229627,150123,6,4,8,2,1,3,1,1,1,0,1,1,2,1,286509
1,UTI,True,0,0,0,0,1,1,0,1,8,17130,332253,508784,147058,73955,73262,85580,53968,0,0,0,0,0,0,0,0,0,0,0,0,0,0,26453
2,UTI,True,4,1,4,1,0,1,1,0,2,29183,629864,960616,325691,167145,160537,208066,141221,4,4,9,2,1,2,0,1,0,1,1,1,2,1,42265
9,UTI,True,0,0,0,0,0,0,0,1,0,327,25070,34232,8046,2778,3241,3033,1930,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2650
<vazio>,UTI,False,0,0,0,0,0,0,0,0,1,905,89188,153762,55340,21793,16327,18937,13319,3,0,0,0,0,1,1,0,1,0,0,0,0,0,232939
1,FEBRE,True,1,0,4,0,0,1,1,1,7,41899,617699,877980,266070,152246,157260,195656,137085,5,3,7,1,1,0,0,0,0,0,1,1,2,1,145310
2,FEBRE,True,3,0,0,1,1,1,0,1,4,5269,313591,483203,166184,76126,69569,94455,57941,2,1,2,1,0,2,0,1,1,1,0,0,0,0,66099
9,FEBRE,True,0,0,0,0,0,0,0,0,0,213,15552,19160,5317,1574,987,981,670,0,0,0,0,0,0,0,0,0,0,0,0,0,0,5986
<vazio>,FEBRE,False,0,1,0,0,0,0,0,0,0,164,129533,277051,98564,35725,25551,24524,14742,0,0,0,0,0,1,1,0,0,0,0,0,0,0,86912
1,TOSSE,True,2,1,3,0,0,2,0,1,7,44036,725450,1127588,366618,201006,198279,255199,172114,7,4,8,2,1,1,0,1,0,1,1,1,2,1,179090
2,TOSSE,True,2,0,1,1,1,0,1,1,4,3131,229341,308468,97958,41498,38961,46422,29378,0,0,1,0,0,1,0,0,1,0,0,0,0,0,45857
9,TOSSE,True,0,0,0,0,0,0,0,0,0,183,13179,15175,3874,1118,798,653,515,0,0,0,0,0,0,0,0,0,0,0,0,0,0,5360
<vazio>,TOSSE,False,0,0,0,0,0,0,0,0,0,195,108405,206163,67685,22049,15329,13342,8431,0,0,0,0,0,1,1,0,0,0,0,0,0,0,74000
1,DISPNEIA,True,3,1,4,0,0,1,1,2,8,39368,745718,1170804,326207,174529,168783,215847,143136,5,3,6,1,0,1,0,1,1,1,1,1,0,1,145095
2,DISPNEIA,True,0,0,0,1,1,1,0,0,3,7548,213596,280704,120980,56624,56905,75066,51206,2,1,2,1,1,1,0,0,0,0,0,0,1,0,64414
9,DISPNEIA,True,0,0,0,0,0,0,0,0,0,260,11518,13196,4164,1506,1070,1141,721,0,0,0,0,0,0,0,0,0,0,0,0,0,0,5483
<vazio>,DISPNEIA,False,1,0,0,0,0,0,0,0,0,369,105543,192690,84784,33012,26609,23562,15375,0,0,1,0,0,1,1,0,0,0,0,0,1,0,89315
1,SATURACAO,True,1,0,1,0,0,0,1,2,8,32213,605830,1068602,283505,143613,138419,173998,114940,5,3,6,1,0,1,1,1,1,1,1,0,0,0,101837
2,SATURACAO,True,2,0,3,1,1,2,0,0,3,13811,298619,321592,140591,74378,76794,104460,71428,2,1,3,1,1,1,0,0,0,0,0,1,1,1,80891
9,SATURACAO,True,0,0,0,0,0,0,0,0,0,713,18502,17516,4769,1715,1411,1626,1235,0,0,0,0,0,0,0,0,0,0,0,0,0,0,9393
<vazio>,SATURACAO,False,1,1,0,0,0,0,0,0,0,808,153424,249684,107270,45965,36743,35532,22835,0,0,0,0,0,1,0,0,0,0,0,0,1,0,112186
```

### `outputs/tables/pessoa_a/a1_waterfall.csv`

- Git: `ignored` · `573 B` · modified `2026-10-17 19:14 UTC` · 6 rows

```csv
ordem,filtro,regra,n_excluido,n_restante,pct_restante
0,Base completa,—,0,4666910,100.0
1,Hospitalização confirmada,HOSPITAL = 1,232253,4434657,95.02
2,Data de internação válida,"DT_INTERNA parseável, ≥ 2009-01-01 e ≤ hoje",72133,4362524,93.48
3,Período analítico,"ano(DT_INTERNA) em [2019, 2020, 2021, 2022, 2023, 2024, 2025]",210444,4152080,88.97
4,Evolução encerrada,"EVOLUCAO em ['1', '2', '3'] (9/ausente fora)",338815,3813265,81.71
5,Alvo binário definido,"EVOLUCAO em {cura, óbito}; óbito por outras causas separado",73650,3739615,80.13
```

### `outputs/tables/pessoa_a/relatorio_A1.md`

- Git: `ignored` · `1.1 KB` · modified `2026-10-17 19:14 UTC`

```markdown
# Relatório de verificações — relatorio_A1

| Etapa | Verificação | Status | Detalhe |
| --- | --- | --- | --- |
| A1 | Colunas essenciais | OK | 11 colunas presentes |
| A1 | Códigos inesperados | OK | todos os códigos dentro do esperado |
| A1 | Waterfall da coorte | OK | 4,666,910 -> 3,739,615 registros (80.1%) |
| A1 | Alvo: desconhecido ≠ cura | OK | 9/ausente/3 viram NA; só 1->0 e 2->1 |
| A1 | Features derivadas | OK | criadas no dataset: idade_anos, faixa_etaria |
| A1 | Dataset analítico | ATENÇÃO | 3,739,615 linhas v0.1; features ausentes na base: DIAS_SINTOMAS_ATE_INTERNACAO, SEXO_CATEGORIA |
| A1-C2 | Colunas exigidas pelo C2 | FALHA | ausentes no dataset: dias_sintomas_ate_internacao, sexo_categoria |
| A1-C2 | Coluna de tempo | OK | datetime válido, ordenado: 2019-01-01 -> 2025-12-31 |
| A1-C2 | Alvo | OK | apenas cura/óbito; positivos [2.0] presentes |
| A1-C2 | check_leakage (C2) | OK | nenhuma feature está em `proibidas` |
| A1-C2 | Tamanho | OK | 3,739,615 linhas |

**Resumo:** 9 OK · 1 atenção · 1 falha(s).
```

### `outputs/tables/pessoa_a/tabela_decisoes.csv`

- Git: `ignored` · `1.2 KB` · modified `2026-10-17 19:14 UTC` · 6 rows

```csv
id,etapa,tema,decisao,responsavel,data,status,impacto,evidencia
D-01,A1,Ponto de previsão,DT_INTERNA (admissão); campos posteriores bloqueados,Pessoa A,2026-10-17,proposta,Define quais variáveis podem entrar,Dicionário SIVEP-Gripe (completar)
D-02,A1,Coorte estrita,"HOSPITAL=1, DT_INTERNA válida, período analítico, evolução encerrada",Pessoa A,2026-10-17,proposta,Ver waterfall (a1_waterfall.csv),
D-03,A1,Alvo principal,Óbito SRAG (EVOLUCAO=2) vs cura (EVOLUCAO=1),Pessoa A,2026-10-17,proposta,Alinhar target.positivos do supervised.yaml (G1),
D-04,A1,Evolução desconhecida e óbito outras causas,EVOLUCAO=9/ausente e 3 saem do alvo binário; nunca viram cura,Pessoa A,2026-10-17,proposta,"Exigir filtro EVOLUCAO in {1,2} no loader do C",
D-12,A1,Features derivadas (criadas no dataset analítico),"idade_anos (TP_IDADE), faixa_etaria, intervalo sintomas->internação (inválido se ausente/negativo/>30 dias) + flag, sin/cos da semana ISO da internação",Pessoa A,2026-10-17,proposta,Só informação da admissão; o C2 as encontra no dataset (supervised.yaml),
D-05,A1,Período analítico,"Desenvolvimento [2019, 2020, 2021, 2022, 2023, 2024]; holdout [2025]",Pessoa A,2026-10-17,proposta,Exclui anos fora do período; alinhar G2,
```

## 19. Snapshot provenance

- Generated UTC: `2026-10-17T21:06:48+00:00`
- Branch / commit: `mateus/eda-inicial` / `8692d8e46776834cc039b398447d129e0cd909cd`
- Origin: `https://github.com/Ivan-S-Oliveira/Projeto_Integrador.git`
- Generator options: `{'output_dir': 'docs', 'config': 'configs/supervised.yaml', 'split_mb': 1.0, 'split': True, 'notebook_outputs': True, 'max_output_chars': 6000, 'artifacts': True, 'max_artifact_bytes': 300000, 'max_csv_rows': 60, 'max_inline_bytes': 4000000, 'git_log': 40, 'include_diff': True, 'max_diff_chars': 400000, 'run_tests': False, 'pytest_args': '', 'test_timeout': 1800, 'fail_on_high': False}`
