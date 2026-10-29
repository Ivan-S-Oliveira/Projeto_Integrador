"""A4 — Volume mensal de internações por SRAG em 2019 (card #50)."""
from __future__ import annotations

import pandas as pd

from src.utils import config as C
from src.utils import storage


def main() -> None:
    # 1. Lê só o necessário do Parquet oficial
    print("[A4] Lendo dt_interna e hospital do Parquet oficial...")
    df = storage.read_srag(
        columns=["dt_interna", "hospital"],
        compactar=True,  # texto vira category, reduz memória
    )

    # 2. Filtra internações confirmadas de 2019
    dt = pd.to_datetime(df["dt_interna"], errors="coerce")
    hosp = df["hospital"].astype("string").str.strip() == "1"
    mask = hosp & (dt.dt.year == 2019)

    # 3. Conta por mês
    volume = (
        dt.loc[mask]
        .dt.to_period("M")
        .value_counts()
        .sort_index()
        .rename_axis("mes")
        .reset_index(name="n_internacoes")
    )
    volume["mes"] = volume["mes"].astype(str)

    # 4. Grava
    out = C.ROOT_DIR / "outputs" / "final" / "volume_mensal_2019.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    volume.to_csv(out, index=False, encoding="utf-8-sig")

    print(f"[A4] Gravado: {out}")
    print(f"[A4] Total 2019: {int(volume['n_internacoes'].sum()):,} internações")
    print()
    print(volume.to_string(index=False))

    # 5. Alerta se algum mês estiver muito abaixo (ou zerado)
    if len(volume) == 12:
        mediana = volume["n_internacoes"].median()
        suspeitos = volume[volume["n_internacoes"] < 0.3 * mediana]
        if not suspeitos.empty:
            print()
            print("[A4] ATENÇÃO: meses com volume < 30% da mediana:")
            print(suspeitos.to_string(index=False))
    else:
        print()
        print(f"[A4] ATENÇÃO: 2019 tem apenas {len(volume)} meses com registros "
              f"(esperado: 12). Meses ausentes indicam lacuna na base.")


if __name__ == "__main__":
    main()