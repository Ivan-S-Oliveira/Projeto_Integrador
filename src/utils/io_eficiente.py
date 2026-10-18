"""I/O compacto para Parquet no projeto SRAG."""
from __future__ import annotations
from pathlib import Path
import numpy as np, pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

def metadados_parquet(caminho):
    arq=pq.ParquetFile(caminho); meta=arq.metadata
    return {"caminho":str(caminho),"linhas":int(meta.num_rows),"colunas":int(meta.num_columns),
            "row_groups":int(meta.num_row_groups),"nomes_colunas":list(arq.schema_arrow.names),
            "tamanho_mb":Path(caminho).stat().st_size/1_048_576}

def amostra_parquet(caminho,n=5,columns=None):
    arq=pq.ParquetFile(caminho)
    lote=next(arq.iter_batches(batch_size=n,columns=list(columns) if columns else None),None)
    return pd.DataFrame(columns=columns or arq.schema_arrow.names) if lote is None else lote.to_pandas()

def compactar_dataframe(df, limite_categoria=1000, colunas_texto_livre=()):
    livres=set(colunas_texto_livre)
    for col in list(df.columns):
        s=df[col]
        if col in livres:
            df[col]=s.astype("string[pyarrow]"); continue
        if isinstance(s.dtype,pd.CategoricalDtype): continue
        if pd.api.types.is_datetime64_any_dtype(s.dtype):
            df[col]=pd.to_datetime(s,errors="coerce").astype("datetime64[ns]"); continue
        if pd.api.types.is_object_dtype(s.dtype) or pd.api.types.is_string_dtype(s.dtype):
            df[col]=s.astype("category") if s.nunique(dropna=True)<=limite_categoria else s.astype("string[pyarrow]")
        elif pd.api.types.is_float_dtype(s.dtype): df[col]=s.astype("float32")
        elif pd.api.types.is_integer_dtype(s.dtype) and not pd.api.types.is_extension_array_dtype(s.dtype):
            df[col]=pd.to_numeric(s,downcast="integer")
    return df

def ler_parquet_enxuto(caminho,columns=None,filters=None,colunas_texto_livre=()):
    tabela=pq.read_table(caminho,columns=list(columns) if columns else None,filters=filters)
    df=tabela.to_pandas(strings_to_categorical=True,self_destruct=True,split_blocks=True)
    del tabela
    return compactar_dataframe(df,colunas_texto_livre=colunas_texto_livre)

def matriz_para_plot(df):
    return pd.DataFrame(df.to_numpy(dtype=np.float64,na_value=np.nan),index=df.index.copy(),columns=df.columns.copy())
