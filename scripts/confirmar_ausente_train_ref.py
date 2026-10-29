"""A6 — % de AUSENTE em train_ref para perd_olft, perd_pala e fadiga (card #50)."""
from __future__ import annotations

import pandas as pd

from src.utils import config as C


def _pct_ausente(serie: pd.Series) -> float:
    """Conta AUSENTE (categoria) ou NaN (numérica/branca) como ausente."""
    if isinstance(serie.dtype, pd.CategoricalDtype):
        # Categoria AUSENTE explícita + NaN residual
        ausente = (serie == "AUSENTE") | serie.isna()
    else:
        ausente = serie.isna()
    return float(ausente.mean() * 100)


def main() -> None:
    artefato = C.ANALYTICAL_DIR / "dataset_supervisionado.parquet"
    if not artefato.exists():
        raise FileNotFoundError(
            f"Artefato não encontrado: {artefato}\n"
            "Execute o B_07 (adaptado) para gerar o dataset supervisionado."
        )

    print(f"[A6] Lendo: {artefato}")
    df = pd.read_parquet(
        artefato,
        columns=["particao", "ano_internacao", "perd_olft", "perd_pala", "fadiga"],
    )

    # Filtra apenas o treino
    treino = df[df["particao"].astype(str) == "treino"].copy()
    if treino.empty:
        raise RuntimeError("Nenhuma linha com particao='treino' no artefato.")

    # Restringe aos anos de desenvolvimento
    anos_dev = [2019, 2023, 2024, 2025]
    treino = treino[treino["ano_internacao"].isin(anos_dev)]

    rows = []
    for col in ["perd_olft", "perd_pala", "fadiga"]:
        for ano, g in treino.groupby("ano_internacao"):
            rows.append({
                "variavel": col,
                "ano": int(ano),
                "n": len(g),
                "n_ausente": int(_pct_ausente(g[col]) * len(g) / 100),
                "pct_ausente": round(_pct_ausente(g[col]), 2),
            })

    out_df = pd.DataFrame(rows)
    out = C.ROOT_DIR / "outputs" / "final" / "ausente_train_ref_2019_2025.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out, index=False, encoding="utf-8-sig")

    print(f"[A6] Gravado: {out}")
    print()
    print(out_df.to_string(index=False))

    # Diagnóstico rápido
    print()
    print("[A6] Diagnóstico:")
    for col in ["perd_olft", "perd_pala", "fadiga"]:
        sub = out_df[out_df["variavel"] == col]
        pct_2019 = sub.loc[sub["ano"] == 2019, "pct_ausente"]
        pct_recente = sub.loc[sub["ano"].isin([2023, 2024, 2025]), "pct_ausente"]
        if not pct_2019.empty and not pct_recente.empty:
            print(
                f"  {col}: 2019={pct_2019.iloc[0]:.1f}% "
                f"vs 2023-2025={pct_recente.mean():.1f}% "
                f"→ "
                + ("marcador de ano ATIVO" if pct_2019.iloc[0] > 90 else "sem marcador forte")
            )


if __name__ == "__main__":
    main()