#!/usr/bin/env python3
"""Análise descritiva de maturidade de desfecho por ano (somente leitura).

Não altera coorte, partição, período nem gates. Lê apenas
dt_interna, hospital e evolucao da base inteira (não da coorte).
Saída: outputs/final/maturidade_desfecho_por_ano.csv
"""
from __future__ import annotations
import pandas as pd
from pathlib import Path
from src.utils import storage

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "final" / "maturidade_desfecho_por_ano.csv"
ANOS = range(2019, 2027)  # inclui 2026 para comparação com §29.15


def main() -> int:
    d = storage.read_srag(columns=["dt_interna", "hospital", "evolucao"])
    d = d[pd.to_numeric(d["hospital"], errors="coerce").eq(1)].copy()
    d["ano"] = pd.to_datetime(d["dt_interna"], errors="coerce").dt.year
    e = pd.to_numeric(d["evolucao"], errors="coerce")
    d["desfecho"] = e.map({
        1: "cura", 2: "obito", 3: "obito_outra_causa", 9: "ignorado",
    }).fillna("vazio")

    t = pd.crosstab(d["ano"], d["desfecho"])
    t["n"] = t.sum(axis=1)
    fora = [c for c in ("obito_outra_causa", "ignorado", "vazio") if c in t.columns]
    t["pct_sem_desfecho_util"] = (t[fora].sum(axis=1) / t["n"] * 100).round(1)
    t["mortalidade_observada_pct"] = (t.get("obito", 0) / t["n"] * 100).round(1)

    # Marca anos com dt_interna inválida (não devem existir na coorte)
    invalidos = d["ano"].isna().sum()
    if invalidos:
        print(f"[aviso] {invalidos} registros com dt_interna inválida (ano = NaN)")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    t.to_csv(OUT)
    print(t.to_string())
    print(f"\nTabela: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())