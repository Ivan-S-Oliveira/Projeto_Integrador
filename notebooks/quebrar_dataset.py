"""
Divide o dataset de SRAG em arquivos anuais por data de coleta (dt_coleta).

Entrada : data/treino/srag_amostra.csv
Saída   : data/treino/srag_YYYY.csv  (um arquivo por ano presente em dt_coleta)
"""

from pathlib import Path
import pandas as pd


# ---------------------------------------------------------------------------
# Configurações
# ---------------------------------------------------------------------------
ROOT_DIR = Path.cwd()                       # ajuste se rodar de outro diretório
ARQUIVO_ENTRADA = ROOT_DIR / "data" / "treino" / "srag_amostra.csv"
PASTA_SAIDA     = ROOT_DIR / "data" / "treino"

COLUNA_DATA = "dt_coleta"                   # coluna usada para separar por ano


# ---------------------------------------------------------------------------
# Função principal
# ---------------------------------------------------------------------------
def dividir_srag_por_ano(
    entrada: Path = ARQUIVO_ENTRADA,
    pasta_saida: Path = PASTA_SAIDA,
    coluna_data: str = COLUNA_DATA,
) -> None:
    pasta_saida.mkdir(parents=True, exist_ok=True)

    if not entrada.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {entrada}")

    print(f"Lendo: {entrada}")
    df = pd.read_csv(entrada, low_memory=False)

    if coluna_data not in df.columns:
        raise KeyError(f"A coluna '{coluna_data}' não existe no dataset.")

    # Converte a coluna de data (aceita formatos ISO e brasileiro)
    df[coluna_data] = pd.to_datetime(df[coluna_data], errors="coerce", dayfirst=False)

    n_invalidos = df[coluna_data].isna().sum()
    if n_invalidos:
        print(f"⚠  {n_invalidos} registros sem {coluna_data} válida serão ignorados.")

    df = df.dropna(subset=[coluna_data])

    # Ano da coleta
    df["ano_coleta"] = df[coluna_data].dt.year

    print("\nDistribuição por ano de coleta:")
    print(df["ano_coleta"].value_counts().sort_index().to_string())

    # Um arquivo por ano
    for ano in sorted(df["ano_coleta"].unique()):
        ano_int = int(ano)
        df_ano = df[df["ano_coleta"] == ano_int].drop(columns=["ano_coleta"])

        destino = pasta_saida / f"srag_{ano_int}.csv"
        df_ano.to_csv(destino, index=False, encoding="utf-8-sig")
        print(f"  → {destino.name:<18} {len(df_ano):>7,} registros")

    print(f"\nPronto. Arquivos salvos em: {pasta_saida}")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    dividir_srag_por_ano()