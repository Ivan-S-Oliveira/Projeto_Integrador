#!/usr/bin/env python3
"""Gera docs/dicionario_variaveis.md a partir de configs/dicionario_variaveis_v1.csv.

Filtra as 30 features de `features.final` (mais alvo e colunas de auditoria)
e escreve uma linha por variável com: nome, descrição SIVEP-Gripe, tipo,
códigos, tratamento e motivo.

Uso (na raiz do repositório):
    ./.venv/Scripts/python.exe tools/dicionario_variaveis.py
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]

CAMINHO_YAML      = ROOT / "configs" / "supervised.yaml"
CAMINHO_MANIFESTO = ROOT / "data" / "analytical" / "manifesto_supervisionado.json"
CAMINHO_CSV       = ROOT / "configs" / "dicionario_variaveis_v1.csv"
CAMINHO_SAIDA     = ROOT / "docs" / "dicionario_variaveis.md"

# Features derivadas por src/features/engineering.py (não estão no CSV de
# 199 colunas do Parquet, porque não existem como coluna bruta).
FEATURES_DERIVADAS: dict[str, dict[str, str]] = {
    "idade_anos": {
        "descricao": "Idade em anos (padronizada)",
        "codigos": "—",
        "recodificacao": "derivada de nu_idade_n + tp_idade "
                         "(1=dias, 2=meses, 3=anos; /365.25, /12, direto)",
        "motivo": "feature do contrato principal (numérica)",
    },
    "sexo_categoria": {
        "descricao": "Sexo em categoria explícita",
        "codigos": "M=masculino; F=feminino; I=ignorado; ausente=ausente",
        "recodificacao": "derivada de cs_sexo (normaliza M/F/I; resto vira ausente)",
        "motivo": "feature do contrato principal (categórica)",
    },
    "faixa_etaria": {
        "descricao": "Faixa etária (intervalo semiaberto)",
        "codigos": "<1, 1-4, 5-11, 12-17, 18-39, 40-59, 60-79, 80+, desconhecida",
        "recodificacao": "derivada de idade_anos com bins do YAML",
        "motivo": "feature do contrato principal (categórica; usada em avaliação por faixa)",
    },
    "dias_sintomas_ate_internacao": {
        "descricao": "Intervalo entre início dos sintomas e internação (dias)",
        "codigos": "float; pode ser negativo (nosocomial) ou >60 (outlier)",
        "recodificacao": "dt_interna − dt_sin_pri em dias; flag_intervalo_invalido marca "
                         "negativos e >max_dias",
        "motivo": "feature do contrato principal (numérica); política D_COORTE_006/007 "
                  "exclui negativos e >60 dias da coorte final",
    },
    "ano_internacao": {
        "descricao": "Ano da internação (derivado de dt_interna)",
        "codigos": "2019 a 2026",
        "recodificacao": "dt_interna.dt.year como Int16",
        "motivo": "âncora temporal; usado em avaliação por ano e partição-mestre",
    },
    "regiao_residencia": {
        "descricao": "Região do Brasil da UF de residência",
        "codigos": "NORTE, NORDESTE, CENTRO-OESTE, SUDESTE, SUL, AUSENTE",
        "recodificacao": "derivada de sg_uf (mapa UF→região; UF desconhecida vira AUSENTE)",
        "motivo": "feature de contexto; usada na estratificação da partição",
    },
    "group_id": {
        "descricao": "Identificador de grupo (para partição-mestre)",
        "codigos": "nu_notific normalizado, ou 'sem_notific:<id_registro>'",
        "recodificacao": "gerado por criar_group_id; NÃO é preditor",
        "motivo": "estrutura de coorte; usado na partição-mestre (hash por grupo)",
    },
    "id_registro": {
        "descricao": "Identificador técnico do registro",
        "codigos": "string única",
        "recodificacao": "gerado no construtor da coorte; NÃO é preditor",
        "motivo": "auditoria; fora das matrizes de features",
    },
    "fator_risc": {
        "descricao": "Possui fatores de risco/comorbidades? (pergunta-mãe)",
        "codigos": "1=sim; 2=não; 9=ignorado; branco=ausente",
        "recodificacao": "coluna de auditoria do artefato supervisionado; "
                         "NÃO é feature do modelo",
        "motivo": "auditoria e análise de sensibilidade (não entra no modelo)",
    },
}

CABECALHO_TABELA = (
    "| Variável | Nome SIVEP-Gripe | Descrição | Tipo | Códigos | "
    "Branco | Ignorado | Recodificação | Motivo |"
)
SEPARADOR_TABELA = (
    "|----------|------------------|-----------|------|---------|"
    "--------|----------|----------------|--------|"
)


def carregar_contrato() -> tuple[list[str], str, list[str]]:
    """Lê YAML + manifesto e devolve (features_final, alvo, colunas_auditoria)."""
    config = yaml.safe_load(CAMINHO_YAML.read_text(encoding="utf-8"))
    manifesto = json.loads(CAMINHO_MANIFESTO.read_text(encoding="utf-8"))

    features_final = list(config["features"]["final"])
    alvo = str(config["target"]["coluna"])
    audit = list(manifesto.get("audit_columns") or [])

    if not features_final:
        raise RuntimeError("features.final vazio em configs/supervised.yaml")
    if not alvo:
        raise RuntimeError("target.coluna vazio em configs/supervised.yaml")

    return features_final, alvo, audit


def carregar_dicionario() -> pd.DataFrame:
    """Lê o dicionário completo de 199 colunas (configs/dicionario_variaveis_v1.csv)."""
    if not CAMINHO_CSV.is_file():
        raise FileNotFoundError(
            f"Dicionário completo ausente: {CAMINHO_CSV}\n"
            "Recupere de um commit anterior (git log --all --full-history -- "
            f'"{CAMINHO_CSV.relative_to(ROOT)}") ou rode a célula do '
            "dicionário em 03_eda_primeira_passagem.ipynb."
        )
    dic = pd.read_csv(CAMINHO_CSV, encoding="utf-8-sig", dtype="string")
    if "coluna" not in dic.columns:
        raise KeyError(
            f"CSV sem coluna 'coluna'; colunas encontradas: {list(dic.columns)}"
        )
    return dic


def filtrar_variaveis(
    dic: pd.DataFrame,
    features_final: list[str],
    alvo: str,
    audit: list[str],
) -> tuple[pd.DataFrame, list[dict[str, str]]]:
    """Filtra o CSV nas variáveis do modelo + alvo + auditoria.

    Retorna (tabela do CSV, linhas derivadas/estruturais que não estão no CSV).
    """
    alvo_lista = list(dict.fromkeys([*features_final, alvo, *audit]))

    no_csv = set(dic["coluna"])
    faltando = sorted(set(alvo_lista) - no_csv)

    sem_doc = [c for c in faltando if c not in FEATURES_DERIVADAS]
    if sem_doc:
        raise SystemExit(
            f"ERRO: variáveis ausentes no CSV sem documentação em "
            f"FEATURES_DERIVADAS: {sem_doc}"
        )

    presentes = [c for c in alvo_lista if c in no_csv]
    filtrado = dic.set_index("coluna").loc[presentes].reset_index()

    derivadas: list[dict[str, str]] = []
    for coluna in alvo_lista:
        if coluna in FEATURES_DERIVADAS:
            info = FEATURES_DERIVADAS[coluna]
            tipo = (
                "estrutura/auditoria"
                if coluna in {"group_id", "id_registro", "fator_risc"}
                else "derivada"
            )
            derivadas.append({
                "coluna": coluna,
                "nome": coluna,
                "descricao": info["descricao"],
                "tipo": tipo,
                "codigos": info["codigos"],
                "branco": "categoria AUSENTE (não é 'não')",
                "ignorado": "categoria IGNORADO (código 9)",
                "recodificacao": info["recodificacao"],
                "motivo": info["motivo"],
            })
    return filtrado, derivadas


def gerar_linha(registro: pd.Series) -> dict[str, str]:
    """Monta uma linha da tabela a partir de uma linha do CSV filtrado."""
    coluna = str(registro["coluna"])

    nome = str(registro.get("nome_amigavel") or coluna)
    grupo = str(registro.get("grupo") or "").strip()
    descricao = f"{nome} ({grupo})" if grupo else nome

    tipo = str(registro.get("tipo_analitico_inferido") or "não classificado")

    codigos = str(registro.get("codigos") or registro.get("expected_codes") or "—")
    if codigos.strip() in ("", "—", "nan", "None"):
        codigos = "—"

    branco = "categoria AUSENTE (não é 'não')"
    ignorado = "categoria IGNORADO (código 9)"
    recod = str(registro.get("transformacao_sugerida") or "nenhuma").strip() or "nenhuma"

    motivo = str(
        registro.get("justificativa_decisao_final")
        or registro.get("decisao_final_usuario")
        or "feature do contrato principal"
    ).strip() or "feature do contrato principal"

    return {
        "coluna": coluna,
        "nome": nome,
        "descricao": descricao,
        "tipo": tipo,
        "codigos": codigos,
        "branco": branco,
        "ignorado": ignorado,
        "recodificacao": recod,
        "motivo": motivo,
    }


def _linha_markdown(celulas: list[str]) -> str:
    """Monta uma linha de tabela, escapando '|' dentro das células."""
    return "| " + " | ".join(c.replace("|", "/") for c in celulas) + " |"


def montar_markdown(
    filtrado: pd.DataFrame,
    derivadas: list[dict[str, str]],
) -> str:
    """Constrói o Markdown completo (cabeçalho + tabela do CSV + derivadas)."""
    total = len(filtrado) + len(derivadas)
    linhas = [
        "# Dicionário das variáveis do modelo",
        "",
        "Documento gerado automaticamente por `tools/dicionario_variaveis.py` "
        "a partir de `configs/dicionario_variaveis_v1.csv`, "
        "`configs/supervised.yaml` e `data/analytical/manifesto_supervisionado.json`.",
        "",
        f"- Total de variáveis documentadas: `{total}` "
        f"({len(filtrado)} do dicionário de 199 colunas do Parquet + "
        f"{len(derivadas)} derivadas ou estruturais).",
        "- **Branco** = valor nulo no CSV original; vira categoria explícita `AUSENTE` "
        "no pré-processador (não é tratado como 'não').",
        "- **Ignorado** = código 9 do SIVEP-Gripe; vira categoria `IGNORADO` "
        "(não é tratado como 'não').",
        "- **Recodificação** = transformação aplicada antes do modelo "
        "(ex.: derivar `idade_anos` a partir de `nu_idade_n` + `tp_idade`).",
        "",
        "## 1. Variáveis do dicionário de 199 colunas do Parquet",
        "",
        CABECALHO_TABELA,
        SEPARADOR_TABELA,
    ]
    for _, registro in filtrado.iterrows():
        linha = gerar_linha(registro)
        linhas.append(_linha_markdown([
            f"`{linha['coluna']}`", linha["nome"], linha["descricao"],
            linha["tipo"], linha["codigos"], linha["branco"],
            linha["ignorado"], linha["recodificacao"], linha["motivo"],
        ]))

    if derivadas:
        linhas += [
            "",
            "## 2. Variáveis derivadas e estruturais",
            "",
            "Features criadas por `src/features/engineering.py` (ou identificadores "
            "gerados em código). Não estão no dicionário de 199 colunas do Parquet "
            "porque não são colunas brutas.",
            "",
            CABECALHO_TABELA,
            SEPARADOR_TABELA,
        ]
        for item in derivadas:
            linhas.append(_linha_markdown([
                f"`{item['coluna']}`", item["nome"], item["descricao"],
                item["tipo"], item["codigos"], item["branco"],
                item["ignorado"], item["recodificacao"], item["motivo"],
            ]))

    return "\n".join(linhas) + "\n"


def main() -> int:
    print(f"[dicionario] lendo YAML:      {CAMINHO_YAML.relative_to(ROOT)}")
    features_final, alvo, audit = carregar_contrato()
    print(f"[dicionario] features.final:  {len(features_final)}")
    print(f"[dicionario] alvo:            {alvo}")
    print(f"[dicionario] colunas auditoria: {len(audit)}")

    print(f"[dicionario] lendo CSV:       {CAMINHO_CSV.relative_to(ROOT)}")
    dic = carregar_dicionario()
    print(f"[dicionario] linhas no CSV:   {len(dic)}")

    filtrado, derivadas = filtrar_variaveis(dic, features_final, alvo, audit)
    total = len(filtrado) + len(derivadas)
    print(f"[dicionario] variáveis totais: {total} "
          f"({len(filtrado)} do CSV + {len(derivadas)} derivadas/estruturais)")

    markdown = montar_markdown(filtrado, derivadas)

    CAMINHO_SAIDA.parent.mkdir(parents=True, exist_ok=True)
    CAMINHO_SAIDA.write_text(markdown, encoding="utf-8")
    print(f"[dicionario] escrito:         {CAMINHO_SAIDA.relative_to(ROOT)}")

    conteudo = CAMINHO_SAIDA.read_text(encoding="utf-8")
    faltando = [
        c for c in [*features_final, alvo, *audit]
        if f"`{c}`" not in conteudo
    ]
    if faltando:
        raise SystemExit(f"ERRO: variáveis não aparecem no .md: {faltando}")

    print(f"[dicionario] OK: {total} linhas na tabela final")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())