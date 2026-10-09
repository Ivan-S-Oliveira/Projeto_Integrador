"""
Limpeza básica do dataset bruto de SRAG.

Etapa inicial do pipeline de dados: aplica normalizações determinísticas
que **não dependem do alvo nem de decisões de modelagem**. É o primeiro
contato com o arquivo bruto vindo do OpenDataSUS, antes de qualquer
feature engineering ou split.

Regras aplicadas
----------------
1. Strings `"nan"` e `""` viram `pd.NA` — a ausência passa a ser
   representada de forma única e explícita.
2. Se `nu_notific` existir, remove duplicatas por essa coluna mantendo a
   primeira ocorrência. Caso contrário, o passo é ignorado.
3. Códigos numéricos com sufixo `.0` em colunas de **texto** são
   normalizados (`"2.0"` → `"2"`). Colunas numéricas não são tocadas
   (o pandas já as representa como o mesmo valor).
4. Colunas cujo nome começa com `dt_` são convertidas para
   `datetime64[ns]` com `errors="coerce"` — datas inválidas viram `NaT`.

O que esta função NÃO faz
-------------------------
Converte ausência em "não"? **Não.** Essa é uma operação proibida sem
regra metodológica documentada: campos categóricos binários (`febre`,
`tosse`, `dispneia`, ...) com valor ausente representam *informação não
coletada*, não "sintoma ausente". Atribuir `"Não"` a esses campos
inventaria dado clínico que não está na notificação.

Qualquer transformação desse tipo precisaria de:
    - decisão explícita em `configs/supervised.yaml`;
    - gate metodológico aprovado;
    - teste dedicado verificando que a regra é aplicada só onde foi
      definida.

Enquanto isso, esta função mantém `pd.NA` — quem consome o dado decide
o que fazer (descartar, imputar com estratégia, criar coluna indicadora).

Limitações conhecidas
---------------------
- A normalização regex atua em todas as colunas de texto, inclusive
  free-text. O padrão exige que a string inteira seja `"<dígitos>.0"`,
  o que só deve casar em colunas de código — mas fica registrado.
- A conversão de datas atinge `dt_evoluca`, `dt_encerra` e `dt_digita`.
  Essas colunas são **proibidas como feature** (`features.proibidas` no
  `supervised.yaml`), mas permanecem úteis como metadado (auditoria,
  ordenação, filtros).
"""

from __future__ import annotations

import pandas as pd


def limpeza_basica(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica limpeza determinística ao dataset bruto.

    Ver a docstring do módulo para o contrato completo: normalização de
    ausência, deduplicação, normalização de códigos em texto e conversão
    de colunas `dt_*` para `datetime64[ns]`.

    Parâmetros
    ----------
    df : pd.DataFrame
        Dataset bruto recém-carregado (tipicamente de Parquet ou CSV).

    Retorno
    -------
    pd.DataFrame
        Cópia do dataset com as transformações aplicadas. O objeto de
        entrada não é mutado — `df.replace` devolve novo DataFrame.

    Notas
    -----
    - Não altera ausência em campos categóricos para um valor afirmativo
      (ex.: `"Não"`). Ver "O que esta função NÃO faz" no módulo.
    - O comportamento depende das colunas presentes: `nu_notific` é
      opcional; qualquer coluna `dt_*` é convertida.
    """
    # 1. Valores vazios → NA explícito.
    #    `replace` com dict casa a string inteira, não substring — seguro.
    df = df.replace({"nan": pd.NA, "": pd.NA})

    # 2. Deduplicação por número de notificação (chave do episódio).
    if "nu_notific" in df.columns:
        df = df.drop_duplicates(subset="nu_notific")

    # 3. Normalização de códigos em colunas de texto ("2.0" → "2").
    #    O padrão é ancorado (^...$) — só casa strings inteiramente numéricas.
    df = df.replace(r"^(\d+)\.0+$", r"\1", regex=True)

    # 4. Colunas temporais → datetime64[ns].
    colunas_data = [c for c in df.columns if c.startswith("dt_")]
    for coluna in colunas_data:
        df[coluna] = pd.to_datetime(df[coluna], errors="coerce")

    return df