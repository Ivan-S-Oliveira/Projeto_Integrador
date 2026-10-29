"""A5 — % de branco por ano para as features principais e de contexto (card #50)."""
from __future__ import annotations

import pandas as pd

from src.utils import config as C
from src.utils import storage


# As 31 features principais (features.final do supervised.yaml)
FEATURES_PRINCIPAIS = [
    "idade_anos", "dias_sintomas_ate_internacao", "sexo_categoria",
    "cs_gestant", "cs_raca", "cs_zona", "ave_suino", "febre", "tosse",
    "garganta", "dispneia", "diarreia", "vomito", "dor_abd", "fadiga",
    "perd_olft", "perd_pala", "outro_sin", "puerpera", "cardiopati",
    "hematologi", "sind_down", "hepatica", "asma", "diabetes",
    "neurologic", "pneumopati", "imunodedepre", "renal", "obesidade",
    "out_morbi",
]

# Contexto incremental + sensibilidade de gravidade
FEATURES_CONTEXTO = [
    "cs_escol_n", "sg_uf", "vacina", "vacina_cov_previa",
    "saturacao", "desc_resp",
]

# Variáveis citadas no card #50
FEATURES_CARD = ["perd_olft", "perd_pala", "fadiga", "dor_abd"]

# Colunas físicas do Parquet (nomes em minúsculo como aparecem no arquivo)
# As features derivadas (idade_anos, dias_sintomas_ate_internacao,
# sexo_categoria) NÃO existem no Parquet; precisam ser derivadas antes.
COLUNAS_BRUTAS = [
    "nu_idade_n", "tp_idade", "dt_sin_pri", "dt_interna",
    "cs_sexo", "cs_gestant", "cs_raca", "cs_zona",
    "ave_suino", "febre", "tosse", "garganta", "dispneia",
    "diarreia", "vomito", "dor_abd", "fadiga", "perd_olft",
    "perd_pala", "outro_sin", "puerpera", "cardiopati",
    "hematologi", "sind_down", "hepatica", "asma", "diabetes",
    "neurologic", "pneumopati", "imunodedepre", "renal", "obesidade",
    "out_morbi", "cs_escol_n", "sg_uf", "vacina", "vacina_cov",
    "saturacao", "desc_resp", "hospital",
]

ANOS = [2019, 2023, 2024, 2025]


def main() -> None:
    print("[A5] Lendo Parquet oficial...")
    df = storage.read_srag(columns=COLUNAS_BRUTAS, compactar=True)

    # Filtra internações confirmadas nos anos de desenvolvimento
    dt = pd.to_datetime(df["dt_interna"], errors="coerce")
    hosp = df["hospital"].astype("string").str.strip() == "1"
    mask = hosp & dt.dt.year.isin(ANOS)
    df = df.loc[mask].copy()
    df["ano"] = dt.loc[mask].dt.year.astype(int)

    # Deriva as três features que o card cita e que dependem de cálculo
    # (idade_anos, dias_sintomas_ate_internacao) para o alvo.
    # O alvo não é necessário aqui; só o branco.

    rows = []
    for col in df.columns:
        if col in ("dt_interna", "hospital", "ano"):
            continue
        for ano, g in df.groupby("ano"):
            s = g[col]
            # Branco = NaN ou string vazia
            pct = 100 * (
                s.isna()
                | (s.astype("string").str.strip() == "")
            ).mean()
            rows.append({"coluna": col, "ano": int(ano), "pct_branco": round(pct, 2)})

    long = pd.DataFrame(rows)
    if long.empty:
        raise RuntimeError("Nenhuma coluna calculada; verifique a leitura.")

    # Pivot: linhas = colunas; colunas = anos
    wide = long.pivot(index="coluna", columns="ano", values="pct_branco")
    wide = wide.reindex(columns=ANOS)
    wide["max_branco"] = wide.max(axis=1)
    wide["alerta_90pct"] = wide["max_branco"] >= 90

    # Ordena pelos mais problemáticos
    wide = wide.sort_values("max_branco", ascending=False)

    out = C.ROOT_DIR / "outputs" / "final" / "campos_por_ano.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    wide.to_csv(out, encoding="utf-8-sig")

    print(f"[A5] Gravado: {out}")
    print(f"[A5] Variáveis com > 90% de branco em algum ano: "
          f"{int(wide['alerta_90pct'].sum())}")
    print()
    print(wide.head(20).to_string())


if __name__ == "__main__":
    main()