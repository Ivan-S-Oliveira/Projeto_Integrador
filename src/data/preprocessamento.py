import pandas as pd

def limpeza_basica(
    df: pd.DataFrame
) -> pd.DataFrame:

    # Valores vazios
    df = df.replace(
        {
            "nan": pd.NA,
            "": pd.NA
        }
    )

    # Remover duplicidades
    if "nu_notific" in df.columns:

        df = df.drop_duplicates(
            subset="nu_notific"
        )

    # Corrigir códigos como 1.0 → 1
    df = df.replace(
        r"^(\d+)\.0+$",
        r"\1",
        regex=True
    )

    # Converter datas
    colunas_data = [
        coluna
        for coluna in df.columns
        if coluna.startswith("dt_")
    ]

    for coluna in colunas_data:

        df[coluna] = pd.to_datetime(
            df[coluna],
            errors="coerce"
        )

    return df