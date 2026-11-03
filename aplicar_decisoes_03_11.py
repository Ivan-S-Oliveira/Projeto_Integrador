r"""Aplica as decisões de 03/11 no repositório (rodar da raiz, com o .venv).

--variaveis : saturacao e desc_resp entram no modelo principal; perd_olft, perd_pala e fadiga saem.
              Edita configs/supervised.yaml, configs/feature_contract_v1.json,
              src/data/supervised_artifact.py, o C_14 e o docs/decisoes.md (entrada 29.34).
--anova     : acrescenta a ANOVA (eta²) ao perfil dos grupos do B_04, com Kruskal-Wallis como conferência,
              e corrige a §29.7 do docs/decisoes.md.
--simular   : mostra o que mudaria, sem gravar nada.
--relatorio : roda --variaveis e --anova numa CÓPIA dos 6 arquivos (pasta temporária) e grava um relatório
              completo (resultado, conferências e diferenças) em %TEMP%\\relatorio_aplicar_decisoes.txt.
              Não altera nada no repositório e não cria arquivo nele.

Cada troca confere que o texto esperado aparece exatamente onde deveria. Se algo não bater, o script para
sem gravar nenhum arquivo daquela parte. Preserva as quebras de linha (CRLF/LF) e a codificação UTF-8.
Salve este arquivo FORA do repositório (por exemplo, em Documentos) e rode na raiz do projeto:

    .\.venv\Scripts\python.exe C:\caminho\aplicar_decisoes_03_11.py --relatorio
    .\.venv\Scripts\python.exe C:\caminho\aplicar_decisoes_03_11.py --variaveis --simular
"""
from __future__ import annotations

import argparse
import ast
import difflib
import json
import platform
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

RAIZ = Path.cwd()
SAIDOS = ["fadiga", "perd_olft", "perd_pala"]
ENTRAM = ["saturacao", "desc_resp"]


class Falha(Exception):
    pass


def ler(p: Path) -> tuple[str, str]:
    bruto = p.read_bytes().decode("utf-8")
    nl = "\r\n" if "\r\n" in bruto else "\n"
    return bruto.replace("\r\n", "\n"), nl


def gravar(p: Path, texto: str, nl: str) -> None:
    p.write_bytes(texto.replace("\n", nl).encode("utf-8"))


def trocar(texto: str, velho: str, novo: str, vezes: int, onde: str) -> str:
    n = texto.count(velho)
    if n != vezes:
        raise Falha(f"{onde}: esperava {vezes} ocorrência(s) de {velho[:70]!r}, achei {n}.")
    return texto.replace(velho, novo)


# ----------------------------------------------------------------------------- variáveis
def yaml_variaveis(t: str) -> str:
    onde = "configs/supervised.yaml"
    if "sensibilidade_marcador_periodo" in t:
        raise Falha(f"{onde}: a decisão de variáveis já foi aplicada.")
    for v in SAIDOS:
        t = trocar(t, f"  - {v}\n", "", 2, onde)
    t = trocar(t, "  - dispneia\n", "  - dispneia\n  - saturacao\n  - desc_resp\n", 2, onde)
    t = trocar(
        t,
        "  sensibilidade_gravidade_admissao:\n  - saturacao\n  - desc_resp\n",
        "  sensibilidade_gravidade_admissao: []  # 03/11: saturacao e desc_resp entraram no modelo principal (decisoes.md §29.34)\n"
        "  sensibilidade_marcador_periodo:  # 03/11: fora do modelo; guardadas no artefato só para a linha \"P + 3 sintomas\" do C_14\n"
        "  - perd_olft\n  - perd_pala\n  - fadiga\n",
        1, onde,
    )
    t = trocar(
        t,
        "  sem_saturacao_desc_resp:\n    ativa: true\n",
        "  sem_saturacao_desc_resp:\n    ativa: false  # 03/11: as duas variáveis entraram no modelo principal (decisoes.md §29.34)\n",
        1, onde,
    )
    t = trocar(
        t,
        "      As variaveis saturacao e desc_resp permanecem na analise de sensibilidade\n"
        "      de gravidade na admissao; vacina e vacina_cov permanecem como contexto\n",
        "      Em 03/11, saturacao e desc_resp entraram no conjunto principal e perd_olft,\n"
        "      perd_pala e fadiga sairam (decisoes.md 29.34); vacina e vacina_cov permanecem como contexto\n",
        1, onde,
    )
    return t


def json_variaveis(t: str) -> str:
    d = json.loads(t)
    final = d["features"]["final"]
    if not all(v in final for v in SAIDOS) or any(v in final for v in ENTRAM):
        raise Falha("configs/feature_contract_v1.json: a lista final não está no estado esperado (já aplicado?).")
    final = [v for v in final if v not in SAIDOS]
    i = final.index("dispneia") + 1
    d["features"]["final"] = final[:i] + ENTRAM + final[i:]
    d["features"]["sensibilidade_gravidade_admissao"] = []
    d["features"]["sensibilidade_marcador_periodo"] = list(SAIDOS)
    return json.dumps(d, ensure_ascii=False, indent=2) + ("\n" if t.endswith("\n") else "")


def artefato_variaveis(t: str) -> str:
    onde = "src/data/supervised_artifact.py"
    t = trocar(
        t,
        "        *(features_cfg.get(\"sensibilidade_gravidade_admissao\") or []),\n    ]\n",
        "        *(features_cfg.get(\"sensibilidade_gravidade_admissao\") or []),\n"
        "        *(features_cfg.get(\"sensibilidade_marcador_periodo\") or []),\n    ]\n",
        1, onde,
    )
    t = trocar(
        t,
        "    ``features.sensibilidade_gravidade_admissao``. Nenhuma delas entra em\n",
        "    ``features.sensibilidade_gravidade_admissao`` e\n"
        "    ``features.sensibilidade_marcador_periodo``. Nenhuma delas entra em\n",
        1, onde,
    )
    return t


C14_TROCAS = [
    ('"P_menos_3_sintomas": (df, sem3(num), sem3(cat), ["logistic", "boosting"]),',
     '"P_mais_3_sintomas": (df, num, cat + TRES_SINTOMAS, ["logistic", "boosting"]),', 1),
    ('"P_mais_gravidade": (df, num, cat + ["saturacao", "desc_resp"], ["logistic"]),',
     '"P_menos_gravidade": (df, num, [c for c in cat if c not in ("saturacao", "desc_resp")], ["logistic"]),', 1),
    ('    sem3 = lambda cols: [c for c in cols if c not in TRES_SINTOMAS]  # noqa: E731\n', '', 1),
    ('probabilidades[("P_menos_3_sintomas", familia)]', 'probabilidades[("P_mais_3_sintomas", familia)]', 1),
    ('roc_auc_menos3_', 'roc_auc_mais3_', 1),
    ('dif_menos3_menos_P_', 'dif_mais3_menos_P_', 1),
]


def notebook(t: str, editar, onde: str) -> str:
    nb = json.loads(t)
    mudou = editar(nb["cells"])
    if not mudou:
        raise Falha(f"{onde}: nada foi alterado.")
    for c in nb["cells"]:
        if c["cell_type"] == "code":
            fonte = "".join(c["source"]) if isinstance(c["source"], list) else c["source"]
            try:
                ast.parse("\n".join("#" + l if l.lstrip().startswith(("%", "!")) else l for l in fonte.split("\n")))
            except SyntaxError as e:
                raise Falha(f"{onde}: célula {c.get('id')} ficou com erro de sintaxe: {e}") from e
    import re as _re
    m_ind = _re.match(r"\{\r?\n( +)\"", t)
    indent = len(m_ind.group(1)) if m_ind else 1
    return json.dumps(nb, ensure_ascii=False, indent=indent) + ("\n" if t.endswith("\n") else "")


def _fonte(c) -> str:
    return "".join(c["source"]) if isinstance(c["source"], list) else c["source"]


def _gravar_fonte(c, texto: str) -> None:
    c["source"] = texto.splitlines(keepends=True) if isinstance(c["source"], list) else texto
    if c["cell_type"] == "code":
        c["outputs"], c["execution_count"] = [], None


def c14_editar(cells) -> bool:
    codigo = "\n\x00\n".join(_fonte(c) for c in cells if c["cell_type"] == "code")
    for velho, _novo, vezes in C14_TROCAS:
        if codigo.count(velho) != vezes:
            raise Falha(f"C_14: esperava {vezes} ocorrência(s) de {velho[:60]!r}, achei {codigo.count(velho)}.")
    mudou = False
    for c in cells:
        if c["cell_type"] != "code":
            continue
        f = _fonte(c)
        novo = f
        for velho, n, _ in C14_TROCAS:
            novo = novo.replace(velho, n)
        novo = novo.replace('"ablacoes_val_tune.csv"', '"ablacoes_val_ref.csv"')
        if novo != f:
            _gravar_fonte(c, novo)
            mudou = True
    return mudou


ENTRADA_2934 = """
#### 29.34 03/11 · Ponto de decisão: lista de variáveis congelada

- **Decisão:** o modelo principal passa a ter 30 variáveis. Entram `saturacao` e
  `desc_resp`; saem `perd_olft`, `perd_pala` e `fadiga`. Contexto (escolaridade,
  vacina) e região continuam fora do modelo.
- **Saturação e desconforto respiratório:** fazem parte da definição de caso de
  SRAG hospitalizado (síndrome gripal com dispneia ou desconforto respiratório,
  ou saturação de O2 abaixo de 95% em ar ambiente) e são registradas no campo 34
  da ficha do SIVEP-Gripe, "Sinais e Sintomas", junto com febre e tosse: são
  sinais que classificam o caso na chegada ao hospital. Na ablação de 02/11
  (logística, validação de 39.748 fichas), acrescentá-las elevou a PR-AUC em
  0,0195 e a ROC-AUC em 0,0088, o maior ganho entre as ablações. Limitação
  mantida: a ficha não registra a hora da medição.
- **Três sintomas (perda de olfato, perda de paladar e fadiga):** os campos
  passam a ser preenchidos com a pandemia; em 2019 ficam em branco em 99,5% a
  99,7% das fichas (19% a 32% em 2023 a 2025) e funcionam como marcador de
  período. Retirá-los custou −0,0002 (logística) e −0,0004 (boosting) de PR-AUC
  na ablação de 02/11; a ROC-AUC de 2019 sem eles variou +0,0001 e +0,0005, com
  intervalos que cruzam zero. A retirada é uma decisão de validade, e não de
  desempenho: o critério de desempenho da §29.19 não foi atingido, e a mudança
  de critério fica registrada aqui. As três colunas ficam no artefato
  (`features.sensibilidade_marcador_periodo`) só para a linha "P + 3 sintomas"
  do C_14.
- **Recodificação das comorbidades por `fator_risc`:** PREENCHER com o resultado
  da conferência (contagem de brancos com `fator_risc` = 2) e a decisão.
- **Sensibilidade "sem saturação e desconforto":** desativada
  (`sensibilidades.sem_saturacao_desc_resp.ativa: false`); a linha
  "P − gravidade" do C_14 mostra o efeito de retirá-las.
- **Impacto:** o artefato supervisionado é regerado (mesmas fichas e blocos;
  `feature_columns` e hash novos) e os notebooks de modelagem e de agrupamento
  são reexecutados. Substitui, nestes pontos, as §13, §29.2, §29.14 e §29.19.
"""


def decisoes_variaveis(t: str) -> str:
    onde = "docs/decisoes.md"
    if "Ponto de decisão: lista de variáveis congelada" in t:
        raise Falha(f"{onde}: a entrada 29.34 já existe.")
    t = trocar(
        t, "## 13. Saturação e desconforto respiratório\n\n",
        "## 13. Saturação e desconforto respiratório\n\n"
        "> Atualizado em 03/11 (§29.34): `saturacao` e `desc_resp` passaram ao modelo principal. "
        "O texto abaixo é o registro anterior.\n\n", 1, onde)
    cab = next((l for l in t.split("\n") if l.startswith("### 29.19 ")), None)
    if cab is None:
        raise Falha(f"{onde}: título da §29.19 não encontrado.")
    t = trocar(t, cab + "\n", cab + "\n\n> Atualizado em 03/11 (§29.34): os três sintomas saíram do modelo por "
               "decisão de validade (marcador de período), e não pelo critério de desempenho abaixo.\n", 1, onde)
    return t.rstrip("\n") + "\n" + ENTRADA_2934


# ----------------------------------------------------------------------------- ANOVA
ANOVA_FUNCAO = '''def ns_perfil_grupos(base, rotulos, numericas, categoricas):
    """Uma linha por variável: teste de associação com o grupo, tamanho do efeito e amplitude entre grupos.

    Categóricas: qui-quadrado de independência (efeito = V de Cramér).
    Numéricas: ANOVA de um fator (efeito = eta²), com Kruskal-Wallis como conferência sem suposição de normalidade.
    Com dezenas de milhares de fichas quase todo p-valor fica abaixo de 0,05: a leitura é pelo tamanho do efeito.
    """
    grupos = np.asarray(rotulos)
    linhas = []
    for coluna in categoricas:
        texto = base[coluna].astype("string").str.strip()
        ausente = (texto.isna() | texto.eq("")).to_numpy(dtype=bool)
        sim = texto.isin(["1", "1.0"]).to_numpy(dtype=bool)
        valores = np.where(ausente, "AUSENTE", texto.fillna("").to_numpy(dtype=object))
        tabela = pd.crosstab(valores, grupos)
        qui2, p_qui2 = chi2_contingency(tabela, correction=False)[:2]
        menor = min(tabela.shape) - 1
        efeito = float(np.sqrt(qui2 / (tabela.to_numpy().sum() * menor))) if menor > 0 else float("nan")
        pct_ausente = pd.Series(ausente).groupby(grupos).mean() * 100
        pct_sim = pd.Series(sim).groupby(grupos).mean() * 100
        linhas.append({
            "variavel": coluna, "tipo": "categorica", "medida": "V_de_Cramer", "efeito": efeito,
            "teste": "qui_quadrado", "estatistica": float(qui2), "p_valor": float(p_qui2),
            "eta2_por_postos": np.nan, "p_kruskal": np.nan,
            "pct_ausente_amostra": float(ausente.mean() * 100),
            "amplitude_pct_ausente": float(pct_ausente.max() - pct_ausente.min()),
            "amplitude_pct_sim": float(pct_sim.max() - pct_sim.min()),
            "media_minima": np.nan, "media_maxima": np.nan,
        })
    for coluna in numericas:
        serie = pd.to_numeric(base[coluna], errors="coerce").reset_index(drop=True)
        por_grupo = [dados.dropna().to_numpy(dtype=float) for _, dados in serie.groupby(grupos)]
        por_grupo = [dados for dados in por_grupo if dados.size]
        n, k = sum(dados.size for dados in por_grupo), len(por_grupo)
        estatistica_f = p_anova = eta2 = estatistica_h = p_kruskal = float("nan")
        if k >= 2 and n > k:
            todos = np.concatenate(por_grupo)
            media_geral = todos.mean()
            soma_total = float(((todos - media_geral) ** 2).sum())
            soma_entre = float(sum(d.size * (d.mean() - media_geral) ** 2 for d in por_grupo))
            if soma_total > 0:
                estatistica_f, p_anova = (float(v) for v in f_oneway(*por_grupo))
                eta2 = soma_entre / soma_total
                estatistica_h, p_kruskal = (float(v) for v in kruskal(*por_grupo))
        eta2_postos = max(0.0, (estatistica_h - k + 1) / (n - k)) if not np.isnan(estatistica_h) else float("nan")
        medias = serie.groupby(grupos).mean()
        linhas.append({
            "variavel": coluna, "tipo": "numerica", "medida": "eta2_ANOVA", "efeito": eta2,
            "teste": "ANOVA_um_fator", "estatistica": estatistica_f, "p_valor": p_anova,
            "eta2_por_postos": eta2_postos, "p_kruskal": p_kruskal,
            "pct_ausente_amostra": float(serie.isna().mean() * 100),
            "amplitude_pct_ausente": np.nan, "amplitude_pct_sim": np.nan,
            "media_minima": float(medias.min()), "media_maxima": float(medias.max()),
        })
    return pd.DataFrame(linhas).sort_values("efeito", ascending=False, ignore_index=True)
'''


def b04_editar(cells) -> bool:
    alvo = [c for c in cells if c["cell_type"] == "code" and "def ns_perfil_grupos(" in _fonte(c)]
    if len(alvo) != 1:
        raise Falha(f"B_04: esperava 1 célula com ns_perfil_grupos, achei {len(alvo)}.")
    c = alvo[0]
    f = _fonte(c)
    if "f_oneway" in f:
        raise Falha("B_04: a ANOVA já foi aplicada.")
    f = trocar(f, "from scipy.stats import chi2_contingency, kruskal\n",
               "from scipy.stats import chi2_contingency, f_oneway, kruskal\n", 1, "B_04")
    i = f.index("def ns_perfil_grupos(")
    resto = f[i:]
    fim = resto.find("\ndef ", 1)
    if fim != -1:
        raise Falha("B_04: ns_perfil_grupos não é a última função da célula; edite à mão.")
    _gravar_fonte(c, f[:i] + ANOVA_FUNCAO.rstrip("\n") + ("\n" if f.endswith("\n") else ""))
    return True


def decisoes_anova(t: str) -> str:
    return trocar(t, "qui-quadrado/ANOVA",
                  "qui-quadrado (V de Cramér) e ANOVA (η²), com Kruskal-Wallis como conferência, no B_04", 1,
                  "docs/decisoes.md §29.7")



# ----------------------------------------------------------------------------- relatório
ARQUIVOS = [
    "configs/supervised.yaml",
    "configs/feature_contract_v1.json",
    "src/data/supervised_artifact.py",
    "notebooks/C/C_14_ablacoes_variaveis.ipynb",
    "notebooks/B/B_04_eda_temporal_clustering.ipynb",
    "docs/decisoes.md",
]
LIMITE_DIFF = 300


def _contar(antes: str, depois: str) -> tuple[int, int]:
    mais = menos = 0
    for l in difflib.unified_diff(antes.split("\n"), depois.split("\n"), lineterm="", n=0):
        if l.startswith(("+++", "---", "@@")):
            continue
        mais += l.startswith("+")
        menos += l.startswith("-")
    return mais, menos


def _diff(antes: str, depois: str, rotulo: str) -> list[str]:
    linhas = list(difflib.unified_diff(antes.split("\n"), depois.split("\n"), f"antes/{rotulo}", f"depois/{rotulo}",
                                       lineterm="", n=1))
    if len(linhas) > LIMITE_DIFF:
        linhas = linhas[:LIMITE_DIFF] + [f"... (+{len(linhas) - LIMITE_DIFF} linhas de diferença omitidas)"]
    return linhas


def _celulas(texto: str) -> dict[str, str]:
    return {str(c.get("id", i)): "".join(c["source"]) if isinstance(c["source"], list) else c["source"]
            for i, c in enumerate(json.loads(texto)["cells"])}


def _forma(bruto: bytes) -> str:
    texto = bruto.decode("utf-8")
    nl = "CRLF" if "\r\n" in texto else "LF"
    fim = "com" if texto.endswith("\n") else "sem"
    return f"{nl}, {fim} quebra de linha final, {len(texto.splitlines())} linhas"


def relatorio() -> int:
    global RAIZ
    origem = RAIZ
    saida = Path(tempfile.gettempdir()) / "relatorio_aplicar_decisoes.txt"
    tmp = Path(tempfile.mkdtemp(prefix="sim_decisoes_"))
    L: list[str] = [
        "RELATÓRIO DO aplicar_decisoes_03_11.py (simulação em cópia; o repositório não foi alterado)",
        f"Gerado em {datetime.now():%Y-%m-%d %H:%M:%S} · Python {platform.python_version()} · pasta {origem}", "",
    ]
    faltando = [r for r in ARQUIVOS if not (origem / r).is_file()]
    if faltando:
        L += ["PARADO: arquivos não encontrados na pasta atual: " + ", ".join(faltando),
              "Rode da raiz do projeto (onde fica a pasta configs)."]
        saida.write_text("\n".join(L) + "\n", encoding="utf-8")
        print("\n".join(L))
        return 1
    for r in ARQUIVOS:
        (tmp / r).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origem / r, tmp / r)
    brutos = {r: (origem / r).read_bytes() for r in ARQUIVOS}
    RAIZ = tmp
    resultado, textos = "OK: as trocas aplicaram sem erro na cópia.", {}
    try:
        for rel, func in plano(True, True):
            if rel in textos:
                original, nl, atual = textos[rel]
            else:
                original, nl = ler(tmp / rel)
                atual = original
            textos[rel] = (original, nl, func(atual))
        for rel, (_o, nl, novo) in textos.items():
            gravar(tmp / rel, novo, nl)
    except Falha as e:
        resultado = f"PARADO (nada seria gravado no repositório): {e}"
    RAIZ = origem
    L += ["=== 1. RESULTADO ===", resultado, ""]

    L += ["=== 2. CONFERÊNCIAS ==="]
    if resultado.startswith("OK"):
        try:
            import yaml
            f = yaml.safe_load((tmp / "configs/supervised.yaml").read_text(encoding="utf-8"))["features"]
            L.append(f"- variáveis no modelo: {len(f['final'])} (esperado 30) · saturacao dentro: {'saturacao' in f['final']} · "
                     f"desc_resp dentro: {'desc_resp' in f['final']} · fadiga fora: {'fadiga' not in f['final']} · "
                     f"perd_olft fora: {'perd_olft' not in f['final']} · perd_pala fora: {'perd_pala' not in f['final']}")
            L.append(f"- listas numericas + categoricas = {len(f['numericas']) + len(f['categoricas'])} (deve ser igual a final) · "
                     f"sensibilidade_gravidade_admissao: {f['sensibilidade_gravidade_admissao']} · "
                     f"sensibilidade_marcador_periodo: {f['sensibilidade_marcador_periodo']}")
        except Exception as e:  # noqa: BLE001
            L.append(f"- YAML: não consegui conferir ({e!r})")
        try:
            c = json.loads((tmp / "configs/feature_contract_v1.json").read_text(encoding="utf-8"))["features"]
            L.append(f"- contrato JSON: {len(c['final'])} variáveis finais · marcador_periodo: {c['sensibilidade_marcador_periodo']}")
        except Exception as e:  # noqa: BLE001
            L.append(f"- contrato JSON: {e!r}")
        try:
            ast.parse((tmp / "src/data/supervised_artifact.py").read_text(encoding="utf-8"))
            L.append("- supervised_artifact.py: sintaxe ok")
        except SyntaxError as e:
            L.append(f"- supervised_artifact.py: ERRO DE SINTAXE {e}")
        try:
            src = ""
            for i, t in _celulas((tmp / "notebooks/B/B_04_eda_temporal_clustering.ipynb").read_text(encoding="utf-8")).items():
                if "def ns_perfil_grupos(" in t:
                    src = t
            import numpy as np
            import pandas as pd
            from scipy.stats import chi2_contingency, f_oneway, kruskal
            ns = {"np": np, "pd": pd, "chi2_contingency": chi2_contingency, "f_oneway": f_oneway, "kruskal": kruskal}
            exec(src[src.index("def ns_perfil_grupos("):], ns)  # noqa: S102
            rng = np.random.default_rng(0)
            g = rng.integers(0, 3, 600)
            base = pd.DataFrame({"idade": g * 20 + rng.normal(0, 5, 600), "febre": np.where(g == 0, "1", "2")})
            r = ns["ns_perfil_grupos"](base, g, ["idade"], ["febre"])
            colunas = {"variavel", "tipo", "medida", "efeito", "estatistica", "p_valor", "pct_ausente_amostra",
                       "amplitude_pct_ausente", "amplitude_pct_sim", "media_minima", "media_maxima"}
            L.append(f"- função da ANOVA roda em dados de teste: {len(r)} linhas · colunas antigas preservadas: "
                     f"{colunas <= set(r.columns)} · eta2 da idade = {float(r.loc[r['variavel'] == 'idade', 'efeito'].iloc[0]):.3f}")
        except Exception as e:  # noqa: BLE001
            L.append(f"- função da ANOVA: não consegui executar nesta máquina ({e!r})")
    else:
        L.append("- puladas (as trocas não foram aplicadas)")
    L.append("")

    L += ["=== 3. RESUMO POR ARQUIVO (linhas acrescentadas / removidas) ===",
          "Para os dois notebooks a primeira coluna é do arquivo JSON inteiro: se ela for muito maior que a das células, o script reformatou o arquivo.", ""]
    L.append(f"{'arquivo':<56}{'+':>6}{'-':>6}   forma do arquivo (antes -> depois)")
    detalhes: list[str] = []
    for r in ARQUIVOS:
        a = brutos[r].decode("utf-8").replace("\r\n", "\n")
        b_bruto = (tmp / r).read_bytes()
        b = b_bruto.decode("utf-8").replace("\r\n", "\n")
        mais, menos = _contar(a, b)
        L.append(f"{r:<56}{mais:>6}{menos:>6}   {_forma(brutos[r])} -> {_forma(b_bruto)}")
        if a == b:
            continue
        if r.endswith(".ipynb"):
            ca, cb = _celulas(a), _celulas(b)
            mud = [i for i in cb if ca.get(i) != cb[i]]
            sa = "\n".join(ca[i] for i in mud)
            sb = "\n".join(cb[i] for i in mud)
            m2, d2 = _contar(sa, sb)
            aviso = ""
            if mais + menos > 3 * (m2 + d2) + 80:
                aviso = "  <<< ATENÇÃO: o arquivo mudou muito mais que as células: formato reescrito"
            L.append(f"{'   células alteradas: ' + str(len(mud)) + ' de ' + str(len(cb)):<56}{m2:>6}{d2:>6}{aviso}")
            for i in mud:
                detalhes += ["", f"--- {r} · célula {i} ---"] + _diff(ca.get(i, ""), cb[i], f"{r}#{i}")
        else:
            detalhes += ["", f"--- {r} ---"] + _diff(a, b, r)
    L += ["", "=== 4. DIFERENÇAS ==="] + detalhes
    saida.write_text("\n".join(L) + "\n", encoding="utf-8")
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"Relatório gerado: {saida}")
    print(resultado)
    return 0 if resultado.startswith("OK") else 2

# ----------------------------------------------------------------------------- execução
def plano(variaveis: bool, anova: bool):
    p = []
    if variaveis:
        p += [
            ("configs/supervised.yaml", yaml_variaveis),
            ("configs/feature_contract_v1.json", json_variaveis),
            ("src/data/supervised_artifact.py", artefato_variaveis),
            ("notebooks/C/C_14_ablacoes_variaveis.ipynb", lambda t: notebook(t, c14_editar, "C_14")),
            ("docs/decisoes.md", decisoes_variaveis),
        ]
    if anova:
        p += [
            ("notebooks/B/B_04_eda_temporal_clustering.ipynb", lambda t: notebook(t, b04_editar, "B_04")),
            ("docs/decisoes.md", decisoes_anova),
        ]
    return p


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--variaveis", action="store_true")
    ap.add_argument("--anova", action="store_true")
    ap.add_argument("--simular", action="store_true")
    ap.add_argument("--relatorio", action="store_true")
    a = ap.parse_args()
    if not (RAIZ / "configs" / "supervised.yaml").is_file():
        print("Rode na raiz do repositório (onde fica a pasta configs).")
        return 1
    if a.relatorio:
        return relatorio()
    if not (a.variaveis or a.anova):
        ap.error("informe --variaveis, --anova, --relatorio ou combinações")
    textos: dict[str, tuple[str, str, str]] = {}
    try:
        for rel, func in plano(a.variaveis, a.anova):
            p = RAIZ / rel
            if not p.is_file():
                raise Falha(f"arquivo não encontrado: {rel}")
            if rel in textos:
                original, nl, atual = textos[rel]
            else:
                original, nl = ler(p)
                atual = original
            textos[rel] = (original, nl, func(atual))
    except Falha as e:
        print(f"PARADO, nada foi gravado: {e}")
        return 2
    for rel, (original, nl, novo) in textos.items():
        import difflib
        mud = sum(1 for l in difflib.unified_diff(original.split("\n"), novo.split("\n"), lineterm="", n=0)
                  if l[:1] in "+-" and not l.startswith(("+++", "---")))
        print(f"{'simulado' if a.simular else 'gravado '}  {rel}  (≈{mud} linhas)")
        if not a.simular:
            gravar(RAIZ / rel, novo, nl)
    print("Simulação: nada foi gravado." if a.simular else "Concluído. Rode o pytest rápido antes do commit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
