r"""Corrige o notebook de análise temporal (EDA 02) para a coorte definitiva.

Uso (na raiz do projeto): .\.venv\Scripts\python.exe corrigir_notebook_eda_temporal.py

O que faz, de uma vez só e sem depender do estado atual do arquivo:
  1. troca as células 1, 2, 4 e 71 pelas versões corrigidas (coorte definitiva, partição-mestra
     por id_registro e análise de desfecho só no bloco train_ref);
  2. remove o sufixo "_B06" dos nomes COLUNAS_*;
  3. confere o resultado (sintaxe das células alteradas e ausência de "B06" e "B_06") antes de gravar.
Guarda uma cópia do arquivo original em .srag-status-local/backups/. Rodar duas vezes dá o mesmo resultado.
"""
import ast
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

NOMES = [
    "COLUNAS_ESTRUTURA", "COLUNAS_DEMOGRAFIA", "COLUNAS_CONTEXTO", "COLUNAS_INTERVALOS",
    "COLUNAS_CONTADORES_EXISTENTES", "COLUNAS_CLUSTERING", "COLUNAS_SOLICITADAS",
    "COLUNAS_EXISTENTES", "COLUNAS_AUSENTES",
]
CELULA_1 = r'''# EDA 02 — Análise temporal e clustering

## Objetivo

Descrever temporalmente a coorte analítica do projeto SRAG e explorar
perfis de apresentação na admissão por meio de técnicas de clustering.

### Fonte da coorte

A fonte da coorte é resolvida pelo mecanismo central do projeto, sem
manter uma lista própria de arquivos neste notebook. Esta execução usa a
coorte definitiva (`coorte_final.parquet`), e o caminho efetivamente
utilizado é validado antes da leitura.

A descrição temporal usa todas as fichas. As análises de associação com o
desfecho (sintomas, comorbidades, faixa etária e número de comorbidades)
usam apenas o bloco `train_ref` da partição-mestra
(`data/analytical/partitions_master.parquet`), para que nenhuma tabela
use fichas reservadas à validação e ao teste.

O tipo, o caminho e a dimensão da coorte utilizada são registrados no
início da execução e na tabela `eda_02_resumo_fonte.csv`, permitindo
rastrear exatamente a origem dos resultados.

## Limites

- o desfecho não participará da formação dos clusters;
- identificadores não serão usados como variáveis de clustering;
- informações posteriores à admissão não entrarão na matriz;
- 2026 será tratado conforme a cobertura da coorte carregada;
- o desfecho será relacionado aos clusters somente depois da definição
  da solução não supervisionada.
'''
CELULA_2 = r'''from pathlib import Path
import gc
import json
import sys
import time

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

import os
import psutil

PROCESSO_ATUAL = psutil.Process(os.getpid())

def memoria_processo_gb():
    """Retorna a memória residente do kernel atual em GB."""

    return (
        PROCESSO_ATUAL.memory_info().rss
        / (1024 ** 3)
    )

print(
    "Memória inicial do kernel:",
    f"{memoria_processo_gb():.2f} GB",
)

def encontrar_raiz_projeto() -> Path:
    pasta_atual = Path.cwd().resolve()

    for pasta in [pasta_atual, *pasta_atual.parents]:
        possui_src = (pasta / "src").is_dir()
        possui_configs = (pasta / "configs").is_dir()

        if possui_src and possui_configs:
            return pasta

    raise FileNotFoundError(
        "Não foi possível localizar a raiz do projeto."
    )


ROOT_DIR = encontrar_raiz_projeto()

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.data.cohort_source import resolve_cohort_path
from src.utils import config as C

TIPO_COORTE, CAMINHO_COORTE = resolve_cohort_path(
    root=ROOT_DIR,
    kind="final",
    explicit_path=None,
)

CAMINHO_COORTE = Path(CAMINHO_COORTE)
NOME_COORTE = str(TIPO_COORTE)

if not CAMINHO_COORTE.is_file():
    raise FileNotFoundError(
        "A fonte de coorte resolvida não existe: "
        f"{CAMINHO_COORTE}"
    )

print(
    "Tipo de coorte:",
    NOME_COORTE,
)
print(
    "Arquivo da coorte:",
    CAMINHO_COORTE,
)


COLUNAS_ESTRUTURA = [
    "id_registro",
    "nu_notific",
    "dt_interna_convertida",
    "ano_internacao",
    "evolucao_normalizada",
    "alvo_obito_srag",
]

COLUNAS_DEMOGRAFIA = [
    "cs_sexo",
    "sexo_categoria",
    "nu_idade_n",
    "tp_idade",
    "idade_anos",
    "faixa_etaria",
    "cs_gestant",
    "cs_raca",
    "cs_zona",
]

COLUNAS_SINTOMAS_PLANEJADAS = [
    "febre",
    "tosse",
    "garganta",
    "dispneia",
    "desc_resp",
    "saturacao",
    "diarreia",
    "vomito",
    "dor_abd",
    "fadiga",
    "perd_olft",
    "perd_pala",
    "outro_sin",
]

COLUNAS_COMORBIDADES_PLANEJADAS = [
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
]

COLUNAS_CONTEXTO = [
    "cs_escol_n",
    "sg_uf",
    "vacina",
    "vacina_cov",
    "ave_suino",
]

COLUNAS_INTERVALOS = [
    "dt_sin_pri",
    "dt_interna",
    "dt_sin_pri_convertida",
    "dias_sintomas_ate_internacao",
    "flag_intervalo_invalido",
]

COLUNAS_CONTADORES_EXISTENTES = [
    "n_sintomas_confirmados",
    "n_sintomas_avaliados",
    "n_comorbidades_confirmadas",
    "n_comorbidades_avaliadas",
    "flag_multimorbidade",
]

COLUNAS_CLUSTERING = [
    "sin_semana",
    "cos_semana",
]


COLUNAS_SOLICITADAS = list(
    dict.fromkeys(
        COLUNAS_ESTRUTURA
        + COLUNAS_DEMOGRAFIA
        + COLUNAS_SINTOMAS_PLANEJADAS
        + COLUNAS_COMORBIDADES_PLANEJADAS
        + COLUNAS_CONTEXTO
        + COLUNAS_INTERVALOS
        + COLUNAS_CONTADORES_EXISTENTES
        + COLUNAS_CLUSTERING
    )
)


# ------------------------------------------------------------
# Conferência do schema antes da leitura
# ------------------------------------------------------------

arquivo_parquet = pq.ParquetFile(
    CAMINHO_COORTE
)

COLUNAS_DISPONIVEIS_COORTE = set(
    arquivo_parquet.schema_arrow.names
)

COLUNAS_EXISTENTES = [
    coluna
    for coluna in COLUNAS_SOLICITADAS
    if coluna in COLUNAS_DISPONIVEIS_COORTE
]

COLUNAS_AUSENTES = [
    coluna
    for coluna in COLUNAS_SOLICITADAS
    if coluna not in COLUNAS_DISPONIVEIS_COORTE
]


# Colunas exigidas diretamente do Parquet. As derivadas (data convertida,
# ano e evolução normalizada) são criadas na célula seguinte quando a
# coorte definitiva não as traz prontas.
COLUNAS_OBRIGATORIAS_COORTE = [
    "id_registro",
    "nu_notific",
    "dt_interna",
    "alvo_obito_srag",
]

colunas_obrigatorias_ausentes = [
    coluna
    for coluna in COLUNAS_OBRIGATORIAS_COORTE
    if coluna not in COLUNAS_DISPONIVEIS_COORTE
]

if colunas_obrigatorias_ausentes:
    raise KeyError(
        "A coorte não contém as colunas obrigatórias: "
        f"{colunas_obrigatorias_ausentes}"
    )


print(
    "Colunas disponíveis no Parquet:",
    len(COLUNAS_DISPONIVEIS_COORTE),
)

print(
    "Colunas solicitadas pelo notebook:",
    len(COLUNAS_SOLICITADAS),
)

print(
    "Colunas que serão carregadas:",
    len(COLUNAS_EXISTENTES),
)

if COLUNAS_AUSENTES:
    print(
        "Colunas opcionais ausentes, que poderão ser derivadas:",
        COLUNAS_AUSENTES,
    )


# ------------------------------------------------------------
# Leitura projetada
# ------------------------------------------------------------

t0_carregamento = time.perf_counter()

try:
    coorte = pd.read_parquet(
        CAMINHO_COORTE,
        columns=COLUNAS_EXISTENTES,
        dtype_backend="pyarrow",
    )

    BACKEND_COORTE = "pyarrow"

except TypeError:
    coorte = pd.read_parquet(
        CAMINHO_COORTE,
        columns=COLUNAS_EXISTENTES,
    )

    BACKEND_COORTE = "numpy/object"


if coorte.empty:
    raise ValueError(
        "A coorte carregada está vazia."
    )


# ------------------------------------------------------------
# Partição-mestra: identifica o bloco de cada ficha
# ------------------------------------------------------------

CAMINHO_PARTICAO_MESTRA = ROOT_DIR / "data" / "analytical" / "partitions_master.parquet"
CAMINHO_MANIFESTO_PARTICAO = ROOT_DIR / "data" / "analytical" / "manifesto_particao.json"

for caminho_necessario in (CAMINHO_PARTICAO_MESTRA, CAMINHO_MANIFESTO_PARTICAO):
    if not caminho_necessario.is_file():
        raise FileNotFoundError(
            "Arquivo da partição-mestra não encontrado: "
            f"{caminho_necessario}"
        )

particao_mestra = pd.read_parquet(
    CAMINHO_PARTICAO_MESTRA,
    columns=["id_registro", "particao"],
)

if not particao_mestra["id_registro"].is_unique:
    raise ValueError(
        "A partição-mestra tem id_registro repetido."
    )

particao_mestra["particao"] = particao_mestra["particao"].astype("category")

bloco_por_registro = particao_mestra.set_index("id_registro")["particao"]

# Alinha pelo id_registro (e não pela posição das linhas): fichas que
# ficaram fora da partição-mestra recebem valor ausente.
coorte["particao"] = bloco_por_registro.reindex(
    coorte["id_registro"].to_numpy()
).array

del particao_mestra
del bloco_por_registro


# Conferência contra o manifesto da partição: as contagens precisam bater.
with open(CAMINHO_MANIFESTO_PARTICAO, encoding="utf-8") as arquivo_manifesto:
    blocos_esperados = {
        nome_bloco: int(info_bloco["n_linhas"])
        for nome_bloco, info_bloco in json.load(arquivo_manifesto)["blocos"].items()
    }

blocos_observados = (
    coorte["particao"]
    .value_counts(dropna=True)
    .astype("int64")
    .to_dict()
)

if blocos_observados != blocos_esperados:
    raise ValueError(
        "As contagens por bloco divergem do manifesto da partição. "
        f"Observado: {blocos_observados}. Esperado: {blocos_esperados}."
    )

print(
    "Fichas sem bloco na partição-mestra:",
    int(coorte["particao"].isna().sum()),
)
print(
    "Fichas em train_ref:",
    blocos_observados["train_ref"],
)


memoria_apos_leitura_mb = (
    coorte.memory_usage(
        index=True,
        deep=True,
    )
    .sum()
    / 1_048_576
)


# ------------------------------------------------------------
# Compactação controlada
# ------------------------------------------------------------

COLUNAS_CATEGORICAS_BAIXA_CARDINALIDADE = [
    coluna
    for coluna in (
        COLUNAS_DEMOGRAFIA
        + COLUNAS_SINTOMAS_PLANEJADAS
        + COLUNAS_COMORBIDADES_PLANEJADAS
        + COLUNAS_CONTEXTO
        + [
            "evolucao_normalizada",
            "faixa_etaria",
        ]
    )
    if coluna in coorte.columns
]


relatorio_compactacao = []


for coluna in COLUNAS_CATEGORICAS_BAIXA_CARDINALIDADE:
    memoria_antes = int(
        coorte[coluna]
        .memory_usage(
            index=False,
            deep=True,
        )
    )

    quantidade_categorias = int(
        coorte[coluna]
        .nunique(
            dropna=False
        )
    )

    if quantidade_categorias <= 500:
        coorte[coluna] = (
            coorte[coluna]
            .astype("category")
        )

    memoria_depois = int(
        coorte[coluna]
        .memory_usage(
            index=False,
            deep=True,
        )
    )

    relatorio_compactacao.append(
        {
            "coluna": coluna,
            "categorias": quantidade_categorias,
            "dtype_final": str(
                coorte[coluna].dtype
            ),
            "memoria_antes_mb": (
                memoria_antes
                / 1_048_576
            ),
            "memoria_depois_mb": (
                memoria_depois
                / 1_048_576
            ),
        }
    )


if "ano_internacao" in coorte.columns:
    coorte["ano_internacao"] = (
        pd.to_numeric(
            coorte["ano_internacao"],
            errors="coerce",
        )
        .astype("Int16")
    )


if "alvo_obito_srag" in coorte.columns:
    coorte["alvo_obito_srag"] = (
        pd.to_numeric(
            coorte["alvo_obito_srag"],
            errors="coerce",
        )
        .astype("Int8")
    )


if "idade_anos" in coorte.columns:
    coorte["idade_anos"] = (
        pd.to_numeric(
            coorte["idade_anos"],
            errors="coerce",
        )
        .astype("Float32")
    )


if "dias_sintomas_ate_internacao" in coorte.columns:
    coorte["dias_sintomas_ate_internacao"] = (
        pd.to_numeric(
            coorte["dias_sintomas_ate_internacao"],
            errors="coerce",
        )
        .astype("Float32")
    )


for coluna in [
    "n_sintomas_confirmados",
    "n_sintomas_avaliados",
    "n_comorbidades_confirmadas",
    "n_comorbidades_avaliadas",
]:
    if coluna in coorte.columns:
        coorte[coluna] = (
            pd.to_numeric(
                coorte[coluna],
                errors="coerce",
            )
            .astype("Int16")
        )


for coluna in [
    "flag_intervalo_invalido",
    "flag_multimorbidade",
]:
    if coluna in coorte.columns:
        coorte[coluna] = (
            pd.to_numeric(
                coorte[coluna],
                errors="coerce",
            )
            .fillna(0)
            .astype("int8")
        )


memoria_final_mb = (
    coorte.memory_usage(
        index=True,
        deep=True,
    )
    .sum()
    / 1_048_576
)

tempo_carregamento_s = (
    time.perf_counter()
    - t0_carregamento
)

gc.collect()


print(
    "Coorte utilizada:",
    NOME_COORTE,
)

print(
    "Caminho:",
    CAMINHO_COORTE,
)

print(
    "Backend:",
    BACKEND_COORTE,
)

print(
    "Dimensão carregada:",
    coorte.shape,
)

print(
    "Memória após leitura:",
    f"{memoria_apos_leitura_mb:,.2f} MB",
)

print(
    "Memória após compactação:",
    f"{memoria_final_mb:,.2f} MB",
)

if memoria_apos_leitura_mb > 0:
    reducao_memoria_pct = (
        1
        - memoria_final_mb
        / memoria_apos_leitura_mb
    ) * 100
else:
    reducao_memoria_pct = 0.0

print(
    "Redução após compactação:",
    f"{reducao_memoria_pct:,.2f}%",
)

print(
    "Tempo de leitura e compactação:",
    f"{tempo_carregamento_s:,.2f} s",
)


relatorio_compactacao_df = (
    pd.DataFrame(
        relatorio_compactacao
    )
    .sort_values(
        [
            "memoria_antes_mb",
            "coluna",
        ],
        ascending=[
            False,
            True,
        ],
    )
    .reset_index(drop=True)
)


display(
    relatorio_compactacao_df.head(20)
)
'''
CELULA_71 = r'''# ============================================================
# Base enxuta para as análises de desfecho
# ============================================================

import gc
import time

t0_base_desfecho = time.perf_counter()

COLUNAS_FIXAS_DESFECHO = [
    "ano_internacao",
    "alvo_obito_srag",
    "faixa_etaria",
    "sexo_categoria",
    "n_sintomas_confirmados",
    "n_sintomas_avaliados",
    "n_comorbidades_confirmadas",
    "n_comorbidades_avaliadas",
    "flag_multimorbidade",
]

COLUNAS_ANALISE_DESFECHO = list(
    dict.fromkeys(
        COLUNAS_FIXAS_DESFECHO
        + list(COLUNAS_SINTOMAS)
        + list(COLUNAS_COMORBIDADES)
    )
)

colunas_desfecho_ausentes = [
    coluna
    for coluna in COLUNAS_ANALISE_DESFECHO
    if coluna not in coorte.columns
]

if colunas_desfecho_ausentes:
    raise KeyError(
        "A coorte não contém todas as colunas necessárias "
        "para a análise de desfecho. "
        f"Colunas ausentes: {colunas_desfecho_ausentes}"
    )

memoria_coorte_mb = (
    coorte.memory_usage(
        index=True,
        deep=True,
    )
    .sum()
    / 1_048_576
)

if "particao" not in coorte.columns:
    raise KeyError(
        "A coluna 'particao' não existe na coorte carregada. "
        "Confira a leitura da partição-mestra na célula 2."
    )

mascara_base_desfecho = (
    coorte["particao"]
    .eq("train_ref")
    .to_numpy(dtype=bool)
)

if not mascara_base_desfecho.any():
    raise ValueError(
        "Não há registros do bloco train_ref na coorte."
    )

base_analise_desfecho = (
    coorte.loc[
        mascara_base_desfecho,
        COLUNAS_ANALISE_DESFECHO,
    ]
    .reset_index(drop=True)
)

origem_analise_desfecho = "particao_treino"

del mascara_base_desfecho

if base_analise_desfecho.empty:
    raise ValueError(
        "A base selecionada para a análise "
        "do desfecho está vazia."
    )

alvo_valido = (
    base_analise_desfecho["alvo_obito_srag"]
    .isin([0, 1])
    .all()
)

if not alvo_valido:
    valores_invalidos_alvo = sorted(
        base_analise_desfecho.loc[
            ~base_analise_desfecho["alvo_obito_srag"].isin([0, 1]),
            "alvo_obito_srag",
        ]
        .drop_duplicates()
        .astype("string")
        .tolist()
    )

    raise ValueError(
        "A base da análise contém valores inválidos "
        "em 'alvo_obito_srag': "
        f"{valores_invalidos_alvo}"
    )

# Compactar apenas as colunas categóricas da base enxuta.
# A coorte original não é alterada.
colunas_textuais_desfecho = (
    base_analise_desfecho
    .select_dtypes(
        include=[
            "object",
            "string",
        ]
    )
    .columns
    .tolist()
)

for coluna in colunas_textuais_desfecho:
    quantidade_categorias = (
        base_analise_desfecho[coluna]
        .nunique(dropna=False)
    )

    # Sintomas, comorbidades, faixa etária e sexo têm
    # cardinalidade pequena e se beneficiam de category.
    if quantidade_categorias <= 500:
        base_analise_desfecho[coluna] = (
            base_analise_desfecho[coluna]
            .astype("category")
        )

memoria_base_desfecho_mb = (
    base_analise_desfecho
    .memory_usage(
        index=True,
        deep=True,
    )
    .sum()
    / 1_048_576
)

gc.collect()

print(
    "Origem da análise do desfecho:",
    origem_analise_desfecho,
)

print(
    "Registros utilizados:",
    len(base_analise_desfecho),
)

print(
    "Colunas utilizadas:",
    len(COLUNAS_ANALISE_DESFECHO),
)

print(
    "Óbitos por SRAG:",
    int(
        base_analise_desfecho["alvo_obito_srag"]
        .sum()
    ),
)

print(
    "Memória da coorte completa:",
    f"{memoria_coorte_mb:,.2f} MB",
)

print(
    "Memória da base enxuta de desfecho:",
    f"{memoria_base_desfecho_mb:,.2f} MB",
)

print(
    "Redução de memória:",
    f"{(
        1
        - memoria_base_desfecho_mb
        / memoria_coorte_mb
    ) * 100:,.2f}%",
)

print(
    "Tempo de preparação:",
    f"{time.perf_counter() - t0_base_desfecho:,.2f} s",
)
'''


def fonte(celula):
    texto = celula["source"]
    return "".join(texto) if isinstance(texto, list) else texto


def definir_fonte(celula, texto):
    celula["source"] = texto.splitlines(keepends=True)
    if celula["cell_type"] == "code":
        celula["outputs"] = []
        celula["execution_count"] = None


def unica(nb, tipo, trecho, descricao):
    achadas = [c for c in nb["cells"] if c["cell_type"] == tipo and trecho in fonte(c)]
    if len(achadas) != 1:
        sys.exit(f"ERRO: esperava 1 célula para '{descricao}' e encontrei {len(achadas)}. Nada foi alterado.")
    return achadas[0]


def main():
    raiz = Path.cwd()
    candidatos = [p for p in (raiz / "notebooks").rglob("*eda_temporal*.ipynb") if ".ipynb_checkpoints" not in p.parts]
    if len(candidatos) != 1:
        sys.exit(f"ERRO: esperava 1 notebook *eda_temporal*.ipynb em notebooks/ e encontrei {len(candidatos)}. Rode na raiz do projeto.")
    caminho = candidatos[0]
    bruto = caminho.read_bytes()
    crlf = b"\r\n" in bruto
    nb = json.loads(bruto.decode("utf-8"))

    c1 = unica(nb, "markdown", "### Fonte da coorte", "texto da fonte da coorte")
    c2 = unica(nb, "code", "def encontrar_raiz_projeto", "leitura da coorte")
    c4 = unica(nb, "code", "COLUNAS_ENTRADA_FEATURES", "entradas das variáveis derivadas")
    c71 = unica(nb, "code", "# Base enxuta para as análises de desfecho", "base de desfecho")

    definir_fonte(c1, CELULA_1)
    definir_fonte(c2, CELULA_2)
    definir_fonte(c71, CELULA_71)

    for celula in nb["cells"]:
        texto = fonte(celula)
        novo = texto
        for nome in NOMES:
            novo = re.sub(r"\b" + nome + r"_B06\b", nome, novo)
        if novo != texto:
            celula["source"] = novo.splitlines(keepends=True)

    for celula in nb["cells"]:
        if re.search(r"B_?06", fonte(celula)):
            sys.exit("ERRO: ainda há 'B06' ou 'B_06' numa célula. Nada foi gravado.")
    for celula in (c2, c4, c71):
        try:
            ast.parse(fonte(celula))
        except SyntaxError as erro:
            sys.exit(f"ERRO de sintaxe numa célula alterada: {erro}. Nada foi gravado.")

    backups = raiz / ".srag-status-local" / "backups"
    backups.mkdir(parents=True, exist_ok=True)
    copia = backups / f"{caminho.stem}.antes_{datetime.now():%Y%m%d_%H%M%S}.ipynb"
    shutil.copy2(caminho, copia)

    saida = json.dumps(nb, indent=1, ensure_ascii=False, sort_keys=True) + "\n"
    if crlf:
        saida = saida.replace("\n", "\r\n")
    caminho.write_bytes(saida.encode("utf-8"))
    print(f"OK: {caminho.relative_to(raiz)} corrigido. Cópia do original em {copia.relative_to(raiz)}.")
    print("Confira com: git diff --stat (deve mostrar só este notebook, com poucas linhas alteradas).")


if __name__ == "__main__":
    main()
