import pandas as pd

def limpeza_basica(
    df: pd.DataFrame
) -> pd.DataFrame:

    df = df.replace(
        {
            "nan": pd.NA,
            "": pd.NA
        }
    )

    if "nu_notific" in df.columns:
        df = df.drop_duplicates(
            subset="nu_notific"
        )

    df = df.replace(
        r"^(\d+)\.0+$",
        r"\1",
        regex=True
    )

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