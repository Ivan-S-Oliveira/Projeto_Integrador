"""
Verificações da Pessoa A (A1–A4) — Projeto Integrador SRAG
==========================================================

Lógica reutilizável usada pelos notebooks `notebooks/A/A1..A4`. Os notebooks só
executam, exibem e documentam; as regras ficam aqui e em `configs/decisoes.yaml`.

  A1  códigos, protocolo e coorte      a1_columns, a1_code_tables, a1_waterfall, a1_target
  A2  qualidade, datas, elegibilidade  a2_missing, a2_dates, a2_duplicates, a2_maturity, a2_eligibility
  A3  desenho experimental e pilotos   a3_config_audit, a3_forbidden, a3_temporal_split,
                                       a3_leak_scan, a3_suspicious_metrics, a3_audit_logs
  A4  candidatos e decisão             a4_decision_table
  Registro                             log_decision (tabela de decisões), write_ata (atas de gate)

As listas de variáveis e ações sugeridas são PROPOSTA INICIAL: confirmar no dicionário
oficial do SIVEP-Gripe e registrar a decisão com `log_decision`.
"""
from __future__ import annotations

MODULE_VERSION = "0.8"  # incrementar quando a assinatura das funções mudar (os notebooks conferem)

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

# =============================================================================
# CONFIGURAÇÃO PADRÃO (a fonte de verdade é configs/decisoes.yaml; ver load_config)
# =============================================================================
DEFAULT_CONFIG: dict = {
    "cols": {
        "hospital": "HOSPITAL",
        "dt_interna": "DT_INTERNA",
        "evolucao": "EVOLUCAO",
        "tp_idade": "TP_IDADE",
        "nu_idade": "NU_IDADE_N",
        "dt_nasc": "DT_NASC",
        "dt_sin_pri": "DT_SIN_PRI",
        "dt_notific": "DT_NOTIFIC",
        "dt_evoluca": "DT_EVOLUCA",
        "dt_encerra": "DT_ENCERRA",
        "nu_notific": "NU_NOTIFIC",
    },
    # Períodos (ano de DT_INTERNA)
    "dev_years": [2022, 2023, 2024],
    "holdout_years": [2025],
    "min_date": "2009-01-01",  # início do SIVEP-Gripe
    # Códigos esperados por campo (strings). Estenda conforme o dicionário.
    "expected_codes": {
        "HOSPITAL": ["1", "2", "9"],
        "EVOLUCAO": ["1", "2", "3", "9"],
        "TP_IDADE": ["1", "2", "3"],
        "UTI": ["1", "2", "9"],
        "FEBRE": ["1", "2", "9"],
        "TOSSE": ["1", "2", "9"],
        "DISPNEIA": ["1", "2", "9"],
        "SATURACAO": ["1", "2", "9"],
    },
    # Alvo: 1 = óbito (EVOLUCAO=2); 0 = cura (EVOLUCAO=1).
    # EVOLUCAO=3 (óbito por outras causas) fica como categoria separada;
    # 9/ausente NUNCA vira cura -> NA e sai da coorte.
    "target_positive": "2",
    "target_negative": "1",
    "target_separate": ["3"],
    "closed_codes": ["1", "2", "3"],
    # Se True, o waterfall exclui registros com inconsistência de datas "excluir"
    "drop_date_inconsistencies": False,
    # Maturidade de EVOLUCAO: mínimo de % encerrados por mês de internação
    "maturity_min_closed_pct": 90.0,
    # Datas: regra, descrição, ação sugerida
    # (excluir | transformar em ausente | manter com flag | apenas documentar)
    "date_rules": [
        ["dt_nasc", "dt_sin_pri", "Nascimento posterior ao início dos sintomas", "excluir"],
        ["dt_sin_pri", "dt_notific", "Início dos sintomas posterior à notificação", "manter com flag"],
        ["dt_sin_pri", "dt_interna", "Início dos sintomas posterior à internação", "manter com flag"],
        ["dt_interna", "dt_evoluca", "Evolução anterior à internação", "excluir"],
        ["dt_evoluca", "dt_encerra", "Encerramento anterior à evolução", "manter com flag"],
    ],
    "max_symptom_to_admission_days": 30,
    "max_age_years": 120,
    # Classificação de variáveis (proposta inicial -> confirmar no dicionário)
    "forbidden_vars": [
        "EVOLUCAO", "DT_EVOLUCA", "DT_ENCERRA", "CLASSI_FIN", "CLASSI_OUT", "CRITERIO",
        "UTI", "DT_ENTUTI", "DT_SAIDUTI", "SUPORT_VEN", "ANTIVIRAL", "DT_ANTIVIR",
        "DT_COLETA", "TP_AMOSTRA", "PCR_RESUL", "DT_PCR", "RES_AN", "DT_RES_AN",
        "RES_IGG", "RES_IGM", "RES_IGA", "DT_RES", "POS_PCRFLU", "POS_PCROUT",
        "HOSPITAL",  # critério de inclusão (constante na coorte), não feature
        "EVOLUCAO_COVID19", "SOROLOGIA", "PCR",
        "UTILIZOUVNI",  # suporte ventilatório: tratamento durante a internação (confirmar)
    ],
    "conditional_vars": [
        "SATURACAO", "VACINA", "VACINA_COV", "DOSE_1_COV", "DOSE_2_COV", "DOSE_REF",
        "SG_UF", "SG_UF_NOT", "CO_MUN_RES", "ID_MN_RESI", "CS_ZONA", "SURTO_SG",
    ],
    "allowed_vars": [
        "CS_SEXO", "NU_IDADE_N", "TP_IDADE", "CS_RACA", "CS_GESTANT", "FEBRE", "TOSSE",
        "GARGANTA", "DISPNEIA", "DESC_RESP", "DIARREIA", "VOMITO", "DOR_ABD", "FADIGA",
        "PERD_OLFT", "PERD_PALA", "CARDIOPATI", "HEMATOLOGI", "SIND_DOWN", "HEPATICA",
        "ASMA", "DIABETES", "NEUROLOGIC", "PNEUMOPATI", "IMUNODEPRE", "RENAL", "OBESIDADE",
        "DT_SIN_PRI", "DT_INTERNA", "DT_NOTIFIC", "SEM_PRI",
    ],
    # Varredura de vazamento univariado
    "leak_auc_threshold": 0.90,
    "leak_max_categories": 50,
    "leak_sample": 200_000,
    "suspicious_metric_threshold": 0.95,
    # Logs: chaves mínimas esperadas (regex, case-insensitive)
    "log_required_keys": {
        "timestamp": r"timestamp|data_hora|datetime",
        "versão": r"vers[aã]o|version",
        "seed": r"seed|semente",
        "config": r"config",
        "variáveis": r"features|vari[aá]veis|columns",
        "folds": r"fold",
        "parâmetros": r"params|par[aâ]metros|hiperpar",
        "artefatos": r"artefato|artifact|output",
    },
    # A4
    "decision_min_pr_auc_gain": 0.01,
    "decision_max_cv_ratio": 0.10,
    "exclusion_sample_rows": 50,
    # População analítica entregue ao C (C2 espera exatamente este arquivo)
    "dataset_analitico": {"path": "data/analytical/dataset_supervisionado.parquet"},
    # Experimentos de split (A3b): aleatório 70-15-15 em cenários de período (anos de DT_INTERNA)
    "experimentos_split": {
        "seed": 42,
        "fracoes": {"treino": 0.70, "validacao": 0.15, "holdout": 0.15},
        "estratificar_por_alvo": True,
        "bench_max_linhas": 200000,
        "cenarios": {
            "todos_2019_2025": {"anos": [2019, 2020, 2021, 2022, 2023, 2024, 2025],
                                "descricao": "Base completa 2019-2025"},
            "sem_2019_2022": {"anos": [2019, 2022, 2023, 2024, 2025],
                              "descricao": "Remove 2019, 2020, 2021 e 2022 (anos de pandemia)"},
        },
    },
    # Features derivadas criadas na exportação (só com informação disponível na admissão)
    "derivadas": {
        "intervalo_max_dias": 30,          # sintomas -> internação acima disso (ou < 0, ou ausente) = inválido
        "periodo_semanas": 52.1775,        # sazonalidade: sin/cos(2*pi*semana_ISO_da_internação/período)
        "faixas_etarias": {
            "bins": [0, 1, 5, 12, 18, 30, 40, 50, 60, 70, 80, 200],
            "labels": ["<1", "1-4", "5-11", "12-17", "18-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"],
        },
    },
}

OK, WARN, FAIL = "OK", "ATENÇÃO", "FALHA"

# Nomes físicos observados na EDA 01 (Parquet dados-v1, 194 colunas) usados para classificar variáveis.
_EDA_TRATAMENTO = ["ANTIVIRAL", "TP_ANTIVIR", "DT_ANTIVIR", "TRAT_COV", "TIPO_TRAT", "DT_TRT_COV", "OUT_ANTIV", "OUT_TRAT"]
_EDA_DESFECHO = ["EVOLUCAO", "DT_EVOLUCA", "DT_ENCERRA", "DT_DIGITA"]
_EDA_GEOGRAFIA = ["SG_UF_NOT", "CO_REGIONA", "CO_MUN_NOT", "CO_PAIS", "SG_UF", "CO_RG_RESI", "CO_MUN_RES",
                  "SG_UF_INTE", "CO_RG_INTE", "CO_MU_INTE"]
_EDA_VACINACAO = ["VACINA", "DT_UT_DOSE", "MAE_VAC", "DT_VAC_MAE", "M_AMAMENTA", "DT_DOSEUNI", "DT_1_DOSE",
                  "DT_2_DOSE", "VACINA_COV", "DOSE_1_COV", "DOSE_2_COV", "DOSE_REF", "DOSE_2REF", "DOSE_ADIC", "DOS_RE_BI"]
_EDA_SOCIAL_TEXTO = ["PAC_COCBO", "PAC_DSCBO", "POV_CT", "TP_POV_CT", "ESTRANG",
                     "OUTRO_SIN", "OUTRO_DES", "OBES_IMC", "OUT_MORBI", "MORB_DESC"]
_EDA_CANDIDATAS_EXTRA = ["CS_ETINIA", "CS_ESCOL_N", "AVE_SUINO", "OUT_ANIM", "PUERPERA", "TABAG"]

# Nomes alternativos (base da API / supervised.yaml) -> nome canônico SIVEP usado aqui.
# CONFIRMAR no dicionário da base: p.ex. 'internado' é assumido equivalente a HOSPITAL.
ALIASES = {
    "HOSPITAL": ["INTERNADO"],
    "DT_INTERNA": ["DT_INTERNACAO"],
    "DT_EVOLUCA": ["DT_EVOLUCAO"],
    "DT_ENCERRA": ["DT_ENCERRAMENTO"],
    "CLASSI_FIN": ["CLASSIFICACAO_FINAL"],
    "CRITERIO": ["CRITERIO_CONFIRMACAO"],
}
_ALT2CANON = {alt: can for can, alts in ALIASES.items() for alt in alts}


def _merge_lists() -> None:
    """Acrescenta a DEFAULT_CONFIG os grupos da EDA (sem duplicar nem conflitar entre classes)."""
    f, c, a = (DEFAULT_CONFIG[k] for k in ("forbidden_vars", "conditional_vars", "allowed_vars"))
    f += [x for x in _EDA_TRATAMENTO + _EDA_DESFECHO if x not in f]
    c += [x for x in _EDA_GEOGRAFIA + _EDA_VACINACAO + _EDA_SOCIAL_TEXTO if x not in c and x not in f]
    a += [x for x in _EDA_CANDIDATAS_EXTRA if x not in a and x not in f and x not in c]


_merge_lists()


def canon(name) -> str:
    n = str(name).strip().upper()
    return _ALT2CANON.get(n, n)


# =============================================================================
# Utilitários
# =============================================================================
class Report:
    """Acumula achados e grava tabelas/relatório."""

    def __init__(self, out: str | Path, nome: str = "relatorio_pessoa_a"):
        self.nome = nome
        self.out = Path(out)
        self.out.mkdir(parents=True, exist_ok=True)
        self.findings: list[tuple[str, str, str, str]] = []

    def add(self, stage: str, check: str, status: str, detail: str) -> None:
        self.findings.append((stage, check, status, detail))
        icon = {OK: "[ok]", WARN: "[!!]", FAIL: "[XX]"}[status]
        print(f"{icon} {stage} | {check}: {detail}")

    def save(self, name: str, df: pd.DataFrame) -> None:
        df.to_csv(self.out / f"{name}.csv", index=False, encoding="utf-8-sig")

    def write_md(self) -> Path:
        path = self.out / f"{self.nome}.md"
        lines = [f"# Relatório de verificações — {self.nome}", ""]
        lines += ["| Etapa | Verificação | Status | Detalhe |", "| --- | --- | --- | --- |"]
        for stage, check, status, detail in self.findings:
            lines.append(f"| {stage} | {check} | {status} | {detail.replace('|', '/')} |")
        n = {s: sum(1 for f in self.findings if f[2] == s) for s in (OK, WARN, FAIL)}
        lines += ["", f"**Resumo:** {n[OK]} OK · {n[WARN]} atenção · {n[FAIL]} falha(s)."]
        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    @property
    def has_failure(self) -> bool:
        return any(f[2] == FAIL for f in self.findings)


PLAUSIBLE_YEARS = (1900, 2100)  # datas fora disso (0001, 9999, 20224...) viram NaT


def parse_date(s: pd.Series) -> pd.Series:
    """Converte para datetime64[ns] aceitando ISO (aaaa-mm-dd) e dd/mm/aaaa.

    Datas fora de 1900–2100 viram NaT ANTES de qualquer conta (evita OverflowError em
    subtrações/comparações com anos absurdos) e a resolução é padronizada (Parquet pode
    trazer s/ms/us). Quem precisa contar datas inválidas usa `raw.notna() & parsed.isna()`.
    """
    if isinstance(s.dtype, pd.CategoricalDtype):  # converte só as categorias únicas (poucos milhares de datas)
        cats = parse_date(pd.Series(s.cat.categories.astype("string")))
        codes = s.cat.codes.to_numpy()
        arr = cats.to_numpy(dtype="datetime64[ns]") if len(cats) else np.array([], dtype="datetime64[ns]")
        vals = np.full(len(s), np.datetime64("NaT"), dtype="datetime64[ns]")
        ok = codes >= 0
        if ok.any():
            vals[ok] = arr[codes[ok]]
        return pd.Series(vals, index=s.index)
    if pd.api.types.is_datetime64_any_dtype(s):
        out = s
        if getattr(out.dt, "tz", None) is not None:
            out = out.dt.tz_localize(None)
    else:
        t = s.astype("string").str.strip()
        out = pd.to_datetime(t, errors="coerce", format="ISO8601")
        miss = out.isna() & t.notna() & (t != "")
        if miss.any():
            out[miss] = pd.to_datetime(t[miss], errors="coerce", format="%d/%m/%Y")
        miss = out.isna() & t.notna() & (t != "")
        if miss.any():  # formatos mistos (ex.: '05/03/2022 00:00', '2022/03/05')
            try:
                out[miss] = pd.to_datetime(t[miss], errors="coerce", format="mixed", dayfirst=True)
            except (TypeError, ValueError):
                pass
    yr = out.dt.year
    out = out.mask((yr < PLAUSIBLE_YEARS[0]) | (yr > PLAUSIBLE_YEARS[1]))
    return out.astype("datetime64[ns]")


def code_str(s: pd.Series) -> pd.Series:
    """Normaliza códigos (1, 1.0, '1', ' 1 ') para string; vazio -> <NA>."""
    n = pd.to_numeric(s, errors="coerce")
    txt = s.astype("string").str.strip()
    res = txt.where(n.isna(), n.round().astype("Int64").astype("string"))
    return res.mask(res == "")


def make_target(evolucao: pd.Series, cfg: dict = DEFAULT_CONFIG) -> pd.Series:
    """1 = óbito, 0 = cura; qualquer outro valor (inclusive 9/ausente) -> NA."""
    e = code_str(evolucao)
    out = pd.Series(pd.NA, index=e.index, dtype="Int64")
    out[(e == cfg["target_positive"]).fillna(False).to_numpy(bool)] = 1
    out[(e == cfg["target_negative"]).fillna(False).to_numpy(bool)] = 0
    return out


def age_years(df: pd.DataFrame, cfg: dict) -> pd.Series:
    c = cfg["cols"]
    n = pd.to_numeric(df[c["nu_idade"]], errors="coerce").to_numpy(float)
    t = code_str(df[c["tp_idade"]])
    is_ = lambda v: (t == v).fillna(False).to_numpy(bool)  # noqa: E731
    vals = np.select([is_("3"), is_("2"), is_("1")], [n, n / 12, n / 365], default=np.nan)
    return pd.Series(vals, index=df.index)


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    """Padroniza nomes (maiúsculas + aliases -> nome canônico SIVEP). Renomeia IN-PLACE (sem copiar)."""
    up = [str(c).strip().upper() for c in df.columns]
    present = set(up)
    new, renamed = [], []
    for u in up:
        c = canon(u)
        if c != u and c not in present:
            renamed.append(f"{u}->{c}")
            new.append(c)
        else:
            new.append(u)
    df.attrs["orig_names"] = {n: str(o).strip() for o, n in zip(df.columns, new)}  # canônico -> nome original
    df.columns = new
    if renamed:
        print(f"[aliases] colunas renomeadas: {', '.join(renamed)}")
    return df


def year_labels(df: pd.DataFrame, cfg: dict) -> pd.Series:
    dt = parse_date(df[cfg["cols"]["dt_interna"]])
    return dt.dt.year.astype("Int64").astype("string").fillna("sem_data")


def has_cols(df: pd.DataFrame, cols: list[str]) -> list[str]:
    return [c for c in cols if c not in df.columns]


# =============================================================================
# A1 — Códigos, protocolo e coorte
# =============================================================================
def a1_columns(df, cfg, rep: Report) -> None:
    need = list(cfg["cols"].values())
    missing = has_cols(df, need)
    if missing:
        rep.add("A1", "Colunas essenciais", FAIL, f"ausentes: {', '.join(missing)}")
        print("   colunas disponíveis:", ", ".join(map(str, df.columns[:80])))
        print("   -> ajuste 'cols' em configs/decisoes.yaml ou ALIASES em verificacoes.py para os nomes reais da base")
    else:
        rep.add("A1", "Colunas essenciais", OK, f"{len(need)} colunas presentes")


def a1_code_tables(df, cfg, rep: Report) -> None:
    ano = year_labels(df, cfg)
    rows, unexpected = [], []
    for col, expected in cfg["expected_codes"].items():
        if col not in df.columns:
            continue
        codes = code_str(df[col]).fillna("<vazio>")
        tab = pd.crosstab(codes, ano)
        tab.insert(0, "campo", col)
        tab.insert(1, "esperado", [c in expected for c in tab.index])
        rows.append(tab.reset_index(names="codigo"))
        bad = [c for c in tab.index if c not in expected and c != "<vazio>"]
        if bad:
            unexpected.append(f"{col}: {bad}")
    if rows:
        rep.save("a1_tabela_codigos", pd.concat(rows, ignore_index=True))
    if unexpected:
        rep.add("A1", "Códigos inesperados", WARN, "; ".join(unexpected))
    else:
        rep.add("A1", "Códigos inesperados", OK, "todos os códigos dentro do esperado")


def a1_waterfall(df, cfg, rep: Report, sufixo: str = "") -> pd.DataFrame:
    """Aplica os filtros em sequência, registra N antes/depois e amostras das exclusões."""
    c = cfg["cols"]
    today = pd.Timestamp.today().normalize()
    dt = parse_date(df[c["dt_interna"]])
    ok_date = (dt.notna() & (dt <= today) & (dt >= pd.Timestamp(cfg["min_date"]))).to_numpy(bool)
    hosp = (code_str(df[c["hospital"]]) == "1").fillna(False).to_numpy(bool)
    anos = dt.dt.year
    analytic = anos.isin(cfg["dev_years"] + cfg["holdout_years"]).to_numpy(bool)
    evo = code_str(df[c["evolucao"]])
    closed = evo.isin(cfg["closed_codes"]).to_numpy(bool)
    binary = evo.isin([cfg["target_positive"], cfg["target_negative"]]).to_numpy(bool)

    steps = [
        ("Hospitalização confirmada", "HOSPITAL = 1", hosp),
        ("Data de internação válida", f"DT_INTERNA parseável, ≥ {cfg['min_date']} e ≤ hoje", ok_date),
        ("Período analítico", f"ano(DT_INTERNA) em {cfg['dev_years'] + cfg['holdout_years']}", analytic),
        ("Evolução encerrada", f"EVOLUCAO em {cfg['closed_codes']} (9/ausente fora)", closed),
        ("Alvo binário definido", "EVOLUCAO em {cura, óbito}; óbito por outras causas separado", binary),
    ]
    if cfg["drop_date_inconsistencies"]:
        steps.insert(3, ("Coerência de datas", "regras de datas com ação 'excluir'", _date_ok_mask(df, cfg)))

    remaining = np.ones(len(df), dtype=bool)
    rows = [dict(ordem=0, filtro="Base completa", regra="—", n_excluido=0,
                 n_restante=len(df), pct_restante=100.0)]
    sample_cols = [x for x in dict.fromkeys(list(c.values()) + ["NU_NOTIFIC"]) if x in df.columns]
    for i, (name, rule, mask) in enumerate(steps, start=1):
        excl = remaining & ~mask
        kept = remaining & mask
        rows.append(dict(ordem=i, filtro=name, regra=rule, n_excluido=int(excl.sum()),
                         n_restante=int(kept.sum()), pct_restante=round(100 * kept.sum() / len(df), 2)))
        if excl.any():
            smp = df.loc[excl, sample_cols].head(cfg["exclusion_sample_rows"])
            rep.save(f"a1_amostra_exclusoes{sufixo}_{i:02d}", smp)
        remaining = kept
    wf = pd.DataFrame(rows)
    rep.save(f"a1_waterfall{sufixo}", wf)
    final = int(remaining.sum())
    status = OK if final > 0 else FAIL
    rep.add("A1", "Waterfall da coorte" + (f" [{sufixo.strip(chr(95))}]" if sufixo else ""), status,
            f"{len(df):,} -> {final:,} registros ({100 * final / max(len(df), 1):.1f}%)")
    return wf


def _date_ok_mask(df, cfg) -> np.ndarray:
    ok = np.ones(len(df), dtype=bool)
    for a, b, _, action in cfg["date_rules"]:
        if action != "excluir":
            continue
        da, db = parse_date(df[cfg["cols"][a]]), parse_date(df[cfg["cols"][b]])
        ok &= ~((da > db).fillna(False).to_numpy(bool))
    return ok


def a1_cohort(df, cfg) -> pd.DataFrame:
    """Retorna a coorte final (mesmas regras do waterfall) com _ano e _alvo."""
    c = cfg["cols"]
    dt = parse_date(df[c["dt_interna"]])
    today = pd.Timestamp.today().normalize()
    evo = code_str(df[c["evolucao"]])
    m = ((code_str(df[c["hospital"]]) == "1").fillna(False).to_numpy(bool)
         & (dt.notna() & (dt <= today) & (dt >= pd.Timestamp(cfg["min_date"]))).to_numpy(bool)
         & dt.dt.year.isin(cfg["dev_years"] + cfg["holdout_years"]).to_numpy(bool)
         & evo.isin([cfg["target_positive"], cfg["target_negative"]]).to_numpy(bool))
    if cfg["drop_date_inconsistencies"]:
        m &= _date_ok_mask(df, cfg)
    out = df.loc[m].copy()
    out["_ano"] = dt[m].dt.year.astype(int)
    out["_alvo"] = make_target(out[c["evolucao"]], cfg).astype(int)
    return out


def a1_target(df, cfg, rep: Report) -> None:
    c = cfg["cols"]
    ano = year_labels(df, cfg)
    evo = code_str(df[c["evolucao"]]).fillna("<vazio>")
    hosp = (code_str(df[c["hospital"]]) == "1").fillna(False).to_numpy(bool)
    tab = pd.crosstab(ano[hosp], evo[hosp])
    tab["total"] = tab.sum(axis=1)
    rep.save("a1_alvo_por_ano", tab.reset_index(names="ano"))
    # Teste de sanidade: desconhecido nunca pode virar cura
    probe = make_target(pd.Series(["1", "2", "3", "9", None, "", "x"]), cfg)
    expected = [0, 1, None, None, None, None, None]
    ok = all((pd.isna(a) and e is None) or a == e for a, e in zip(probe, expected))
    rep.add("A1", "Alvo: desconhecido ≠ cura", OK if ok else FAIL,
            "9/ausente/3 viram NA; só 1->0 e 2->1" if ok else f"mapeamento incorreto: {list(probe)}")


DERIVADAS = ("idade_anos", "intervalo_sint_interna_dias", "flag_intervalo_invalido",
             "sin_semana", "cos_semana", "faixa_etaria")
_DERIVADAS_CANON = {d.upper() for d in DERIVADAS}


def add_derived(df: pd.DataFrame, cfg: dict, wanted=None) -> list[str]:
    """Cria IN-PLACE (nomes canônicos em maiúsculas) as features derivadas pedidas.

    Usa só o que existe na admissão (idade, DT_SIN_PRI, DT_INTERNA); nunca desfecho nem datas posteriores.
    - idade_anos: NU_IDADE_N convertida por TP_IDADE (dias/365, meses/12, anos); fora de [0, max_age_years] -> NaN
    - faixa_etaria: faixas de cfg['derivadas']['faixas_etarias'] (texto; NaN se idade inválida)
    - intervalo_sint_interna_dias: DT_INTERNA - DT_SIN_PRI em dias; NaN quando inválido
    - flag_intervalo_invalido: 1 se o intervalo é ausente, negativo ou > intervalo_max_dias; senão 0
    - sin_semana / cos_semana: semana ISO de DT_INTERNA em círculo de periodo_semanas
    """
    c, d = cfg["cols"], cfg["derivadas"]
    wanted = {canon(w) for w in (wanted if wanted is not None else DERIVADAS)} & _DERIVADAS_CANON
    criadas: list[str] = []
    if wanted & {"IDADE_ANOS", "FAIXA_ETARIA"}:
        age = age_years(df, cfg)
        age = age.where((age >= 0) & (age <= cfg["max_age_years"]))
        if "IDADE_ANOS" in wanted:
            df["IDADE_ANOS"] = age
            criadas.append("IDADE_ANOS")
        if "FAIXA_ETARIA" in wanted:
            fx = pd.cut(age, bins=d["faixas_etarias"]["bins"], labels=d["faixas_etarias"]["labels"], right=False)
            df["FAIXA_ETARIA"] = fx.astype(object).where(fx.notna(), np.nan)
            criadas.append("FAIXA_ETARIA")
    if wanted & {"INTERVALO_SINT_INTERNA_DIAS", "FLAG_INTERVALO_INVALIDO"}:
        gap = (parse_date(df[c["dt_interna"]]) - parse_date(df[c["dt_sin_pri"]])).dt.days.astype("float64")
        invalido = gap.isna() | (gap < 0) | (gap > d["intervalo_max_dias"])
        if "FLAG_INTERVALO_INVALIDO" in wanted:
            df["FLAG_INTERVALO_INVALIDO"] = invalido.astype("int8")
            criadas.append("FLAG_INTERVALO_INVALIDO")
        if "INTERVALO_SINT_INTERNA_DIAS" in wanted:
            df["INTERVALO_SINT_INTERNA_DIAS"] = gap.where(~invalido)
            criadas.append("INTERVALO_SINT_INTERNA_DIAS")
    if wanted & {"SIN_SEMANA", "COS_SEMANA"}:
        sem = parse_date(df[c["dt_interna"]]).dt.isocalendar().week.astype("float64")
        ang = 2 * np.pi * sem / d["periodo_semanas"]
        if "SIN_SEMANA" in wanted:
            df["SIN_SEMANA"] = np.sin(ang)
            criadas.append("SIN_SEMANA")
        if "COS_SEMANA" in wanted:
            df["COS_SEMANA"] = np.cos(ang)
            criadas.append("COS_SEMANA")
    return criadas


def _analytical_path(cfg: dict) -> Path:
    """Usa C.ANALYTICAL_DIR do projeto (como o C1/C2); senão, o caminho de configs/decisoes.yaml."""
    nome = Path(cfg["dataset_analitico"]["path"]).name
    try:
        from src.utils import config as C  # noqa: N812

        return Path(C.ANALYTICAL_DIR) / nome
    except Exception:  # noqa: BLE001
        return Path(cfg["dataset_analitico"]["path"])


def a1_export_dataset(df, cfg, rep: Report, supervised_config=None, path=None, versao="0.1",
                      excluir_proibidas=False, extra_cols=(), split=None, rotulo="") -> dict:
    """Grava a população analítica (coorte + alvo + tempo + features) para o C2.

    Colunas: id (NU_NOTIFIC), colunas de tempo (coluna_tempo do supervised.yaml e DT_INTERNA),
    alvo (EVOLUCAO bruta: apenas 1/2 após a coorte), features do supervised.yaml e ANO_INTERNACAO.
    Usa os NOMES ORIGINAIS das colunas da base (os do supervised.yaml), ordenado pelo tempo.
    Nenhuma coluna proibida além das features pedidas é enviada ao C.
    """
    path = Path(path) if path else _analytical_path(cfg)
    _t = f" [{rotulo}]" if rotulo else ""
    c = cfg["cols"]
    orig = df.attrs.get("orig_names", {})
    cohort = a1_cohort(df, cfg)
    y = load_supervised_yaml(supervised_config) if supervised_config and Path(supervised_config).exists() else {}
    if y:
        feats = supervised_features(y)
        target_col = canon((y.get("target") or {}).get("coluna", c["evolucao"]))
        time_col = canon(y.get("coluna_tempo", c["dt_interna"]))
    else:
        feats = [canon(x) for x in cfg["allowed_vars"] if canon(x) in df.columns]
        target_col, time_col = c["evolucao"], c["dt_interna"]
    grupos = [canon(g) for g in (((y.get("avaliacao") or {}).get("grupos")) or [])]
    pedir_derivadas = [f for f in dict.fromkeys(feats + grupos) if f in _DERIVADAS_CANON and f not in cohort.columns]
    derivadas_criadas = add_derived(cohort, cfg, pedir_derivadas) if pedir_derivadas else []
    forb = {canon(x) for x in cfg["forbidden_vars"]}
    hits = [f for f in feats if f in forb]
    if excluir_proibidas:
        feats = [f for f in feats if f not in forb]
    missing = [f for f in feats if f not in cohort.columns]
    grupos_cols = [g for g in grupos if g in cohort.columns]
    feats = [f for f in feats if f in cohort.columns]
    keep = [k for k in [c["nu_notific"], time_col, c["dt_interna"], target_col, *feats, *grupos_cols,
                        *map(canon, extra_cols)] if k in cohort.columns]
    keep = list(dict.fromkeys(keep))
    out = cohort[keep].copy()
    for t in {time_col, c["dt_interna"]}:
        if t in out.columns:
            out[t] = parse_date(out[t])
    out["ANO_INTERNACAO"] = cohort["_ano"].to_numpy()
    n_data_invalida = 0
    if time_col in out.columns:
        n_data_invalida = int(out[time_col].isna().sum())
        out = out.dropna(subset=[time_col]).sort_values(time_col, kind="stable")
    if split:  # coluna `split` (treino/validacao/holdout) sorteada, estratificada pelo alvo, reprodutível pela seed
        estr = out[target_col].astype(str).to_numpy() if split.get("estratificar_por_alvo", True) else None
        out["SPLIT"] = split_aleatorio(len(out), estr, split.get("seed", 42), split.get("fracoes"))
    pedidos = {}
    if y:
        f_ = y.get("features", {}) or {}
        for n in ((f_.get("final") or []) or (f_.get("numericas") or []) + (f_.get("categoricas") or [])):
            pedidos[canon(n)] = str(n)
        for g_ in ((y.get("avaliacao") or {}).get("grupos") or []):
            pedidos.setdefault(canon(g_), str(g_))
        pedidos[target_col] = str((y.get("target") or {}).get("coluna", target_col))
        pedidos[time_col] = str(y.get("coluna_tempo", time_col))
    nome_final = lambda col: pedidos.get(col, orig.get(col, col.lower()))  # noqa: E731
    aliases_aplicados = {nome_final(c_): orig.get(c_, c_.lower()) for c_ in out.columns
                         if c_ in pedidos and nome_final(c_).lower() != orig.get(c_, c_.lower()).lower()}
    out.columns = [nome_final(col) for col in out.columns]
    tgt_name = nome_final(target_col)
    assert set(pd.Series(out[tgt_name]).dropna().astype(float).unique()) <= {1.0, 2.0}, "alvo fora de {1,2}"

    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".csv":
        out.to_csv(path, index=False)
    else:
        out.to_parquet(path, index=False)
    meta = dict(versao=versao, criado_em=pd.Timestamp.now().isoformat(timespec="seconds"), arquivo=str(path),
                n_linhas=int(len(out)), colunas=list(out.columns), alvo=tgt_name,
                coluna_tempo=nome_final(time_col),
                anos={str(k): int(v_) for k, v_ in out["ano_internacao"].value_counts().sort_index().items()},
                desenvolvimento=cfg["dev_years"], holdout=cfg["holdout_years"],
                features_proibidas_no_dataset=[orig.get(h, h.lower()) for h in hits if not excluir_proibidas],
                features_ausentes_na_base=missing, base_origem_linhas=int(len(df)),
                aliases_aplicados_yaml_para_fisico=aliases_aplicados,
                descartadas_data_tempo_invalida=n_data_invalida,
                derivadas_criadas=[nome_final(x) for x in derivadas_criadas],
                grupos_avaliacao_incluidos=[nome_final(g) for g in grupos_cols])
    meta["sha256"] = _sha256(path)
    if split:
        meta["split"] = {"tipo": split.get("tipo", "aleatorio"), "seed": split.get("seed", 42),
                         "fracoes": split.get("fracoes"), "contagem": out["split"].value_counts().to_dict()}
    path.with_suffix(".meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    if derivadas_criadas:
        rep.add("A1", "Features derivadas" + _t, OK,
                f"criadas no dataset: {', '.join(nome_final(x) for x in derivadas_criadas)}")
    if n_data_invalida:
        rep.add("A1", "Data da coluna de tempo" + _t, WARN,
                f"{n_data_invalida:,} linhas com {nome_final(time_col)} inválida/ausente descartadas (o C2 faria o mesmo)")
    if aliases_aplicados:
        rep.add("A1", "Nomes do YAML x base" + _t, WARN,
                "colunas gravadas com o nome pedido no YAML, mas vindas de outro nome físico: "
                + ", ".join(f"{k}<-{v_}" for k, v_ in aliases_aplicados.items()) + " (confirmar equivalência)")
    hard = [h for h in hits if h != "HOSPITAL" and not excluir_proibidas]
    if hard:
        rep.add("A1", "Dataset analítico" + _t, FAIL, f"{len(out):,} linhas gravadas, MAS com features proibidas: {', '.join(hard)}")
    elif missing:
        rep.add("A1", "Dataset analítico" + _t, WARN, f"{len(out):,} linhas v{versao}; features ausentes na base: {', '.join(missing)}")
    else:
        rep.add("A1", "Dataset analítico" + _t, OK, f"{len(out):,} linhas, {out.shape[1]} colunas -> {path} (v{versao})")
    return meta


def validar_contrato_c2(path, supervised_config, rep: Report) -> bool:
    """Confere o ARQUIVO gravado contra o que o C2 consome (células 6–16 do C2_pipeline_supervisionado).

    O C2 faz: read_parquet -> TARGET e DATE_COLUMN presentes -> to_datetime(DATE_COLUMN) e dropna ->
    treino[FEATURES] -> criar_alvo_binario/filtrar_rotulos_validos -> check_leakage(X).
    """
    st, p = "A1-C2", Path(path)
    if not p.exists():
        rep.add(st, "Arquivo do dataset", FAIL, f"não encontrado: {p}")
        return False
    y = load_supervised_yaml(supervised_config)
    f = y.get("features", {}) or {}
    target = (y.get("target") or {}).get("coluna")
    data_col = y.get("coluna_tempo")
    feats = list(f.get("final") or ((f.get("numericas") or []) + (f.get("categoricas") or [])))
    positivos = [float(x) for x in ((y.get("target") or {}).get("positivos") or [])]
    if p.suffix == ".csv":
        names = list(pd.read_csv(p, nrows=0).columns)
    else:
        import pyarrow.parquet as pq

        names = pq.ParquetFile(p).schema_arrow.names
    wanted = [c for c in dict.fromkeys([target, data_col, *feats]) if c in names]
    d = pd.read_csv(p, usecols=wanted) if p.suffix == ".csv" else pd.read_parquet(p, columns=wanted)
    ok = True
    faltam = [c for c in (target, data_col, *feats) if c not in names]
    if faltam:
        ok = False
        rep.add(st, "Colunas exigidas pelo C2", FAIL, f"ausentes no dataset: {', '.join(map(str, faltam))}")
    else:
        rep.add(st, "Colunas exigidas pelo C2", OK, f"alvo '{target}', tempo '{data_col}' e {len(feats)} features presentes")
    if data_col in d.columns:
        dt = pd.to_datetime(d[data_col], errors="coerce")
        n_bad = int(dt.isna().sum())
        if n_bad:
            rep.add(st, "Coluna de tempo", WARN, f"{n_bad:,} datas inválidas (o C2 descarta essas linhas)")
        elif not dt.is_monotonic_increasing:
            rep.add(st, "Coluna de tempo", WARN, "dataset não está ordenado por tempo (o TemporalSplit pode reordenar)")
        else:
            rep.add(st, "Coluna de tempo", OK, f"datetime válido, ordenado: {dt.min().date()} -> {dt.max().date()}")
    if target in d.columns:
        vals = set(pd.Series(d[target]).dropna().astype(float).unique())
        if positivos and not (set(positivos) & vals):
            ok = False
            rep.add(st, "Alvo", FAIL, f"nenhum valor positivo {positivos} no dataset (valores: {sorted(vals)})")
        elif vals - {1.0, 2.0}:
            rep.add(st, "Alvo", WARN, f"valores fora de {{1,2}}: {sorted(vals - {1.0, 2.0})} (o C2 os descarta)")
        else:
            rep.add(st, "Alvo", OK, f"apenas cura/óbito; positivos {positivos} presentes")
    prib = {str(x).lower() for x in (f.get("proibidas") or [])}
    vazam = [c for c in feats if str(c).lower() in prib]
    if vazam:
        ok = False
        rep.add(st, "check_leakage (C2)", FAIL, f"features em `proibidas`: {', '.join(vazam)}")
    else:
        rep.add(st, "check_leakage (C2)", OK, "nenhuma feature está em `proibidas`")
    rep.add(st, "Tamanho", OK if len(d) else FAIL, f"{len(d):,} linhas")
    return ok and len(d) > 0


# =============================================================================
# Experimentos de split: aleatório 70-15-15 e cenários de período (A3b)
# =============================================================================
def _sha256(path) -> str:
    import hashlib

    h = hashlib.sha256()
    with open(path, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def verificar_dataset_congelado(path, rep: Report) -> bool:
    """Compara o SHA-256 do arquivo com o gravado no .meta.json (população analítica congelada)."""
    p = Path(path)
    meta_p = p.with_suffix(".meta.json")
    if not p.exists() or not meta_p.exists():
        rep.add("A4", "Dataset congelado", FAIL, f"arquivo ou metadados ausentes: {p.name}")
        return False
    meta = json.loads(meta_p.read_text(encoding="utf-8"))
    ok = meta.get("sha256") == _sha256(p)
    rep.add("A4", "Dataset congelado", OK if ok else FAIL,
            f"{p.name} v{meta.get('versao')} " + ("inalterado desde a exportação" if ok else "FOI ALTERADO após a exportação"))
    return ok


def cfg_para_anos(cfg: dict, anos) -> dict:
    """Cópia de cfg com o período analítico = `anos` (sem holdout temporal): usada nos cenários."""
    c2 = json.loads(json.dumps(cfg))
    c2["dev_years"] = [int(a) for a in anos]
    c2["holdout_years"] = []
    return c2


def split_aleatorio(n: int, estratos=None, seed: int = 42, fracoes: dict | None = None) -> np.ndarray:
    """Rótulos 'treino'/'validacao'/'holdout' sorteados (opcionalmente estratificados), reprodutíveis pela seed."""
    fr = fracoes or {"treino": 0.70, "validacao": 0.15, "holdout": 0.15}
    if abs(sum(fr.values()) - 1) > 1e-9:
        raise ValueError(f"frações devem somar 1: {fr}")
    rng = np.random.default_rng(seed)
    rot = np.empty(n, dtype=object)
    if estratos is None:
        grupos = [np.arange(n)]
    else:
        est = np.asarray(estratos).astype(str)
        grupos = [np.flatnonzero(est == k) for k in sorted(set(est))]
    for idx in grupos:
        idx = rng.permutation(idx)
        m = len(idx)
        n_tr, n_va = int(round(m * fr["treino"])), int(round(m * fr["validacao"]))
        rot[idx[:n_tr]] = "treino"
        rot[idx[n_tr:n_tr + n_va]] = "validacao"
        rot[idx[n_tr + n_va:]] = "holdout"
    return rot


def split_por_ordem(valores_tempo, fracoes: dict | None = None) -> np.ndarray:
    """Divisão temporal por posição (como o TemporalSplit por fração do C2): passado -> treino, futuro -> holdout."""
    fr = fracoes or {"treino": 0.70, "validacao": 0.15, "holdout": 0.15}
    v_ = np.asarray(valores_tempo)
    ordem = np.argsort(v_, kind="stable")
    n = len(v_)
    n_tr, n_va = int(round(n * fr["treino"])), int(round(n * fr["validacao"]))
    rot = np.empty(n, dtype=object)
    rot[ordem[:n_tr]] = "treino"
    rot[ordem[n_tr:n_tr + n_va]] = "validacao"
    rot[ordem[n_tr + n_va:]] = "holdout"
    return rot


def _ler(path, cols):
    p = Path(path)
    if p.suffix == ".csv":
        return pd.read_csv(p, usecols=[c for c in cols if c in pd.read_csv(p, nrows=0).columns])
    import pyarrow.parquet as pq

    nomes = pq.ParquetFile(p).schema_arrow.names
    return pd.read_parquet(p, columns=[c for c in cols if c in nomes])


def _relatorio_split(path, meta: dict, cfg: dict, rep: Report, nome: str) -> pd.DataFrame:
    st, tag = "A3b", f" [{nome}]"
    fr = cfg["experimentos_split"]["fracoes"]
    d = _ler(path, ["split", meta["alvo"], "ano_internacao", "nu_notific"])
    d["_y"] = (pd.to_numeric(d[meta["alvo"]], errors="coerce") == float(cfg["target_positive"])).astype(int)
    t = d.groupby("split").agg(n=("_y", "size"), n_obitos=("_y", "sum"))
    t["pct_linhas"] = (100 * t["n"] / t["n"].sum()).round(2)
    t["prevalencia_obito_pct"] = (100 * t["n_obitos"] / t["n"]).round(2)
    t = t.reindex(["treino", "validacao", "holdout"]).reset_index()
    rep.save(f"a3_split_aleatorio_{nome}", t)
    por_ano = pd.crosstab(d["ano_internacao"], d["split"]).reindex(columns=["treino", "validacao", "holdout"], fill_value=0)
    rep.save(f"a3_split_aleatorio_{nome}_por_ano", por_ano.reset_index())

    dev = max(abs(float(t.loc[t["split"] == k, "pct_linhas"].iloc[0]) - 100 * fr[k]) for k in fr)
    rep.add(st, "Proporções 70/15/15" + tag, OK if dev <= 0.5 else WARN,
            f"desvio máximo {dev:.2f} p.p. | " + ", ".join(f"{r.split}={r.n:,}" for r in t.itertuples()))
    amp = float(t["prevalencia_obito_pct"].max() - t["prevalencia_obito_pct"].min())
    rep.add(st, "Estratificação do alvo" + tag, OK if amp <= 0.5 else WARN,
            f"prevalência de óbito por split: " + ", ".join(f"{r.split}={r.prevalencia_obito_pct}%" for r in t.itertuples())
            + f" (amplitude {amp:.2f} p.p.)")
    faltam = [(int(a), s) for a in por_ano.index for s in por_ano.columns if por_ano.loc[a, s] == 0]
    rep.add(st, "Anos em cada split" + tag, OK if not faltam else WARN,
            "todos os anos aparecem nos 3 splits (split aleatório mistura os períodos)" if not faltam
            else f"anos ausentes em algum split: {faltam[:6]}")
    if "nu_notific" in d.columns:
        g = d.dropna(subset=["nu_notific"]).groupby("nu_notific")["split"].nunique()
        n_dup = int((g > 1).sum())
        rep.add(st, "NU_NOTIFIC entre splits" + tag, OK if n_dup == 0 else WARN,
                "nenhum NU_NOTIFIC repetido em splits diferentes" if n_dup == 0
                else f"{n_dup:,} NU_NOTIFIC aparecem em mais de um split (pode ser vazamento entre treino e validação)")
    return t


def a3_split_aleatorio_cenario(df, cfg, rep: Report, nome: str, anos, supervised_config=None,
                               versao: str = "0.1", excluir_proibidas: bool = False) -> dict:
    """Coorte do cenário (anos informados) + dataset com coluna `split` aleatória 70/15/15 + relatório."""
    cfg_s = cfg_para_anos(cfg, anos)
    a1_waterfall(df, cfg_s, rep, sufixo=f"_{nome}")
    base = _analytical_path(cfg)
    caminho = base.with_name(f"dataset_supervisionado_{nome}{base.suffix}")
    e = cfg["experimentos_split"]
    meta = a1_export_dataset(df, cfg_s, rep, supervised_config, path=caminho, versao=versao,
                             excluir_proibidas=excluir_proibidas, rotulo=nome,
                             split={"tipo": "aleatorio", "seed": e["seed"], "fracoes": e["fracoes"],
                                    "estratificar_por_alvo": e["estratificar_por_alvo"]})
    meta["anos_cenario"] = [int(a) for a in anos]
    _relatorio_split(caminho, meta, cfg, rep, nome)
    return meta


def a3_benchmark_split(path, supervised_config, cfg: dict, rep: Report, nome: str,
                       max_rows: int = 200_000, seed: int = 42) -> pd.DataFrame:
    """Regressão logística treino -> VALIDAÇÃO em split aleatório e em split temporal por ordem (o holdout NÃO é aberto).

    Mostra o quanto o split aleatório é otimista frente ao temporal (autocorrelação no tempo).
    """
    from sklearn.compose import ColumnTransformer
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler

    y = load_supervised_yaml(supervised_config)
    f = y.get("features", {}) or {}
    numericas = list(f.get("numericas") or [])
    categoricas = list(f.get("categoricas") or [])
    if f.get("final"):
        numericas = [x for x in f["final"] if x in numericas]
        categoricas = [x for x in f["final"] if x not in numericas]
    alvo, tempo = y["target"]["coluna"], y["coluna_tempo"]
    pos = float(y["target"]["positivos"][0])
    d = _ler(path, [alvo, tempo, "split", *numericas, *categoricas])
    numericas = [c for c in numericas if c in d.columns]
    categoricas = [c for c in categoricas if c in d.columns]
    d[tempo] = pd.to_datetime(d[tempo], errors="coerce")
    d = d.dropna(subset=[tempo]).reset_index(drop=True)
    d["part_aleatoria"] = d["split"].to_numpy()
    d["part_temporal"] = split_por_ordem(d[tempo].to_numpy(), cfg["experimentos_split"]["fracoes"])
    if len(d) > max_rows:
        d = d.sample(max_rows, random_state=seed).reset_index(drop=True)
    yb = (pd.to_numeric(d[alvo], errors="coerce") == pos).astype(int).to_numpy()
    X = d[numericas + categoricas].copy()
    for c in numericas:
        X[c] = pd.to_numeric(X[c], errors="coerce")
    for c in categoricas:
        X[c] = X[c].astype("string").fillna("__NA__").astype(object)

    linhas = []
    for particao, col in (("aleatoria", "part_aleatoria"), ("temporal_por_ordem", "part_temporal")):
        tr = (d[col] == "treino").to_numpy()
        va = (d[col] == "validacao").to_numpy()
        if len(np.unique(yb[tr])) < 2 or len(np.unique(yb[va])) < 2:
            continue
        prep = ColumnTransformer([
            ("num", Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler())]), numericas),
            ("cat", OneHotEncoder(handle_unknown="ignore", min_frequency=30), categoricas),
        ])
        pipe = Pipeline([("prep", prep), ("clf", LogisticRegression(max_iter=300, class_weight="balanced"))])
        pipe.fit(X[tr], yb[tr])
        p = pipe.predict_proba(X[va])[:, 1]
        prior = float(yb[tr].mean())
        base = dict(cenario=nome, particao=particao, n_treino=int(tr.sum()), n_validacao=int(va.sum()),
                    prevalencia_validacao=round(float(yb[va].mean()), 4))
        linhas.append(dict(base, modelo="baseline_prior", roc_auc=0.5, pr_auc=round(float(yb[va].mean()), 4),
                           brier=round(float(np.mean((prior - yb[va]) ** 2)), 4)))
        linhas.append(dict(base, modelo="logistica", roc_auc=round(roc_auc_score(yb[va], p), 4),
                           pr_auc=round(average_precision_score(yb[va], p), 4),
                           brier=round(brier_score_loss(yb[va], p), 4)))
    res = pd.DataFrame(linhas)
    rep.save(f"a3_benchmark_split_{nome}", res)
    tag = f" [{nome}]"
    lg = res[res["modelo"] == "logistica"].set_index("particao") if len(res) else res
    if len(res) and {"aleatoria", "temporal_por_ordem"} <= set(lg.index):
        delta = float(lg.loc["aleatoria", "pr_auc"] - lg.loc["temporal_por_ordem", "pr_auc"])
        rep.add("A3b", "Split aleatório x temporal" + tag, WARN if delta > 0.02 else OK,
                f"PR-AUC (validação): aleatório {lg.loc['aleatoria', 'pr_auc']:.3f} vs temporal {lg.loc['temporal_por_ordem', 'pr_auc']:.3f} "
                f"(Δ {delta:+.3f})" + (" — o aleatório está otimista; decidir pelo temporal" if delta > 0.02 else ""))
    else:
        rep.add("A3b", "Split aleatório x temporal" + tag, WARN, "benchmark não executado (alvo com uma só classe em algum split)")
    return res


_COR_SPLIT = {"treino": "#2F6DB5", "validacao": "#E8912D", "holdout": "#6BA368"}
_ORDEM_SPLIT = ["treino", "validacao", "holdout"]


def _rotulos_barras(ax, barras, textos, dy=0.0):
    for b, t in zip(barras, textos):
        ax.annotate(t, (b.get_x() + b.get_width() / 2, b.get_height() + dy), ha="center", va="bottom", fontsize=9)


def grafico_split_cenario(rep: Report, cfg: dict, nome: str, anos=None, fig_dir="outputs/figures/pessoa_a",
                          mostrar: bool = False):
    """3 painéis do split aleatório de um cenário (a partir das tabelas já gravadas em rep.out):
    (a) % de linhas por split x meta 70/15/15; (b) prevalência de óbito por split; (c) composição dos splits dentro de cada ano.
    """
    import matplotlib.pyplot as plt

    t = pd.read_csv(Path(rep.out) / f"a3_split_aleatorio_{nome}.csv").set_index("split").reindex(_ORDEM_SPLIT)
    pa = pd.read_csv(Path(rep.out) / f"a3_split_aleatorio_{nome}_por_ano.csv").set_index("ano_internacao")[_ORDEM_SPLIT]
    fr = cfg["experimentos_split"]["fracoes"]
    cores = [_COR_SPLIT[s] for s in _ORDEM_SPLIT]
    fig, axs = plt.subplots(1, 3, figsize=(17, 4.8), gridspec_kw={"width_ratios": [1, 1, 1.5]})

    ax = axs[0]  # (a) proporção de linhas
    barras = ax.bar(_ORDEM_SPLIT, t["pct_linhas"], color=cores)
    for i, s in enumerate(_ORDEM_SPLIT):
        ax.hlines(100 * fr[s], i - 0.42, i + 0.42, colors="black", linestyles="--", linewidth=1.4,
                  label="meta 70/15/15" if i == 0 else None)
    _rotulos_barras(ax, barras, [f"{p:.1f}%\nn={int(n):,}" for p, n in zip(t["pct_linhas"], t["n"])], dy=1)
    ax.set_ylim(0, 100 * max(fr.values()) * 1.25)
    ax.set_ylabel("% das linhas da coorte")
    ax.set_title("(a) Proporção de linhas por split")
    ax.legend(loc="upper right", fontsize=9)

    ax = axs[1]  # (b) prevalência do alvo
    prev = t["prevalencia_obito_pct"]
    geral = 100 * t["n_obitos"].sum() / t["n"].sum()
    barras = ax.bar(_ORDEM_SPLIT, prev, color=cores)
    ax.axhline(geral, color="black", linestyle="--", linewidth=1.4, label=f"geral {geral:.2f}%")
    _rotulos_barras(ax, barras, [f"{p:.2f}%" for p in prev], dy=0.3)
    ax.set_ylim(0, max(prev.max(), geral) * 1.3)
    ax.set_ylabel("% de óbitos (alvo = 1)")
    ax.set_title(f"(b) Prevalência de óbito por split (amplitude {prev.max() - prev.min():.2f} p.p.)")
    ax.legend(loc="upper right", fontsize=9)

    ax = axs[2]  # (c) composição por ano
    comp = pa.div(pa.sum(axis=1), axis=0) * 100
    base = np.zeros(len(comp))
    for s in _ORDEM_SPLIT:
        ax.bar(comp.index.astype(str), comp[s], bottom=base, color=_COR_SPLIT[s], label=s)
        for x, (v_, b_) in enumerate(zip(comp[s], base)):
            if v_ >= 6:
                ax.text(x, b_ + v_ / 2, f"{v_:.0f}%", ha="center", va="center", fontsize=8, color="white")
        base = base + comp[s].to_numpy()
    ax.axhline(70, color="black", linestyle=":", linewidth=1)
    ax.axhline(85, color="black", linestyle=":", linewidth=1)
    ax.set_ylim(0, 100)
    ax.set_xticks(range(len(comp)), [f"{a}\nn={int(n):,}" for a, n in zip(comp.index, pa.sum(axis=1))], fontsize=8)
    ax.set_ylabel("% do ano em cada split")
    ax.set_title("(c) Composição dos splits dentro de cada ano")
    ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.17), fontsize=9)

    anos_txt = f" — anos {', '.join(map(str, anos))}" if anos else ""
    fig.suptitle(f"Split aleatório estratificado 70/15/15 — {nome}{anos_txt}", fontsize=13, y=1.02)
    fig.tight_layout()
    destino = Path(fig_dir)
    destino.mkdir(parents=True, exist_ok=True)
    caminho = destino / f"split_{nome}.png"
    fig.savefig(caminho, dpi=140, bbox_inches="tight")
    if mostrar:
        plt.show()
    else:
        plt.close(fig)
    return caminho


def grafico_comparacao_cenarios(rep: Report, cfg: dict, nomes, fig_dir="outputs/figures/pessoa_a", mostrar: bool = False):
    """Compara os cenários: N por ano empilhado por split (um painel por cenário, mesmo eixo) + prevalência por split."""
    import matplotlib.pyplot as plt

    nomes = list(nomes)
    por_ano = {n: pd.read_csv(Path(rep.out) / f"a3_split_aleatorio_{n}_por_ano.csv").set_index("ano_internacao")[_ORDEM_SPLIT]
               for n in nomes}
    resumo = {n: pd.read_csv(Path(rep.out) / f"a3_split_aleatorio_{n}.csv").set_index("split").reindex(_ORDEM_SPLIT) for n in nomes}
    anos = sorted(set().union(*[set(p.index) for p in por_ano.values()]))
    topo = max(p.sum(axis=1).max() for p in por_ano.values()) * 1.12
    fig, axs = plt.subplots(1, len(nomes) + 1, figsize=(6 * len(nomes) + 5.5, 4.8),
                            gridspec_kw={"width_ratios": [1.3] * len(nomes) + [1]})
    for ax, n in zip(axs, nomes):
        p = por_ano[n].reindex(anos, fill_value=0)
        base = np.zeros(len(p))
        for s in _ORDEM_SPLIT:
            ax.bar(p.index.astype(str), p[s], bottom=base, color=_COR_SPLIT[s], label=s)
            base = base + p[s].to_numpy()
        for x, tot in enumerate(base):
            if tot == 0:
                ax.axvspan(x - 0.5, x + 0.5, color="#DDDDDD", alpha=0.6)
                ax.text(x, topo * 0.5, "fora do\ncenário", ha="center", va="center", fontsize=9, color="#555555")
            else:
                ax.text(x, tot + topo * 0.01, f"{int(tot):,}", ha="center", va="bottom", fontsize=8)
        ax.set_ylim(0, topo)
        ax.set_ylabel("registros na coorte")
        ax.set_title(f"{n}  (N={int(base.sum()):,})")
    axs[0].legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.1), fontsize=9)

    ax = axs[-1]
    larg = 0.8 / len(nomes)
    cores_cen = ["#444444", "#B5B5B5", "#8A6FBF", "#C96F6F"]
    for i, n in enumerate(nomes):
        x = np.arange(3) + (i - (len(nomes) - 1) / 2) * larg
        barras = ax.bar(x, resumo[n]["prevalencia_obito_pct"], larg, label=n, color=cores_cen[i % len(cores_cen)])
        _rotulos_barras(ax, barras, [f"{p:.1f}%" for p in resumo[n]["prevalencia_obito_pct"]], dy=0.2)
    ax.set_xticks(range(3), _ORDEM_SPLIT)
    ymax = max(r["prevalencia_obito_pct"].max() for r in resumo.values())
    ax.set_ylim(0, ymax * 1.3)
    ax.set_ylabel("% de óbitos")
    ax.set_title("Prevalência de óbito por split")
    ax.legend(fontsize=8, loc="upper right")
    fig.suptitle("Comparação dos cenários — split aleatório 70/15/15", fontsize=13, y=1.02)
    fig.tight_layout()
    destino = Path(fig_dir)
    destino.mkdir(parents=True, exist_ok=True)
    caminho = destino / "split_comparacao_cenarios.png"
    fig.savefig(caminho, dpi=140, bbox_inches="tight")
    if mostrar:
        plt.show()
    else:
        plt.close(fig)
    return caminho


def comparar_cenarios(metas: dict, benchs: dict, rep: Report) -> pd.DataFrame:
    """Tabela única: N, prevalência e desempenho (validação) por cenário."""
    linhas = []
    for nome, m in metas.items():
        d = _ler(m["arquivo"], [m["alvo"]])
        y = (pd.to_numeric(d[m["alvo"]], errors="coerce") == 2).astype(int)
        r = dict(cenario=nome, anos=",".join(map(str, m.get("anos_cenario", []))), n_linhas=len(d),
                 n_obitos=int(y.sum()), prevalencia_obito_pct=round(100 * float(y.mean()), 2))
        b = benchs.get(nome)
        if b is not None and len(b):
            for part in ("aleatoria", "temporal_por_ordem"):
                x = b[(b["modelo"] == "logistica") & (b["particao"] == part)]
                if len(x):
                    r[f"pr_auc_{part}"], r[f"roc_auc_{part}"] = float(x["pr_auc"].iloc[0]), float(x["roc_auc"].iloc[0])
        linhas.append(r)
    t = pd.DataFrame(linhas)
    rep.save("comparacao_cenarios", t)
    return t


# =============================================================================
# A2 — Qualidade, datas e elegibilidade
# =============================================================================
def a2_missing(df, cfg, rep: Report) -> None:
    ano = year_labels(df, cfg)
    coded = set(cfg["expected_codes"])
    rows = []
    for col in df.columns:
        s = df[col]
        isna = s.isna()
        if s.dtype == object or pd.api.types.is_string_dtype(s):
            isna = isna | (s.astype("string").str.strip() == "").fillna(False)
        g = isna.groupby(ano).agg(["mean", "size"])
        ign = None
        if col in coded:
            ign = (code_str(s) == "9").fillna(False).groupby(ano).mean()
        for y, r in g.iterrows():
            rows.append(dict(coluna=col, ano=y, n=int(r["size"]), pct_vazio=round(100 * r["mean"], 2),
                             pct_ignorado=None if ign is None else round(100 * ign.loc[y], 2)))
    long = pd.DataFrame(rows)
    rep.save("a2_vazios_ignorados_por_ano", long)
    piv = long[long["ano"] != "sem_data"].pivot(index="coluna", columns="ano", values="pct_vazio")
    inexistente = piv[(piv >= 99.9).any(axis=1) & (piv < 99.9).any(axis=1)]
    rep.save("a2_campos_inexistentes_por_ano", inexistente.reset_index())
    if len(inexistente):
        rep.add("A2", "Campo inexistente por ano", WARN,
                f"{len(inexistente)} campos 100% vazios em algum ano (ex.: {', '.join(inexistente.index[:5])})")
    else:
        rep.add("A2", "Campo inexistente por ano", OK, "nenhuma ruptura total de preenchimento")


def a2_dates(df, cfg, rep: Report) -> None:
    c = cfg["cols"]
    today = pd.Timestamp.today().normalize()
    rows = []
    for a, b, desc, action in cfg["date_rules"]:
        if c[a] not in df.columns or c[b] not in df.columns:
            continue
        da, db = parse_date(df[c[a]]), parse_date(df[c[b]])
        both = da.notna() & db.notna()
        bad = (da > db).fillna(False)
        rows.append(dict(regra=f"{c[a]} <= {c[b]}", descricao=desc, n_comparaveis=int(both.sum()),
                         n_violacoes=int(bad.sum()),
                         pct=round(100 * bad.sum() / max(both.sum(), 1), 3), acao_sugerida=action))
    for key in ("dt_nasc", "dt_sin_pri", "dt_notific", "dt_interna", "dt_evoluca", "dt_encerra"):
        if c[key] in df.columns:
            d = parse_date(df[c[key]])
            raw_filled = df[c[key]].notna()
            unparsable = int((raw_filled & d.isna()).sum())
            future = int((d > today).sum())
            rows.append(dict(regra=f"{c[key]} válida", descricao="Data futura, não interpretável ou fora de 1900–2100",
                             n_comparaveis=int(raw_filled.sum()), n_violacoes=unparsable + future,
                             pct=round(100 * (unparsable + future) / max(raw_filled.sum(), 1), 3),
                             acao_sugerida="transformar em ausente"))
    if {c["dt_sin_pri"], c["dt_interna"]} <= set(df.columns):
        gap = (parse_date(df[c["dt_interna"]]) - parse_date(df[c["dt_sin_pri"]])).dt.days
        big = int((gap > cfg["max_symptom_to_admission_days"]).sum())
        rows.append(dict(regra="sintomas->internação", descricao=f"> {cfg['max_symptom_to_admission_days']} dias",
                         n_comparaveis=int(gap.notna().sum()), n_violacoes=big,
                         pct=round(100 * big / max(gap.notna().sum(), 1), 3), acao_sugerida="manter com flag"))
    if {c["nu_idade"], c["tp_idade"]} <= set(df.columns):
        age = age_years(df, cfg)
        bad = int(((age < 0) | (age > cfg["max_age_years"])).sum())
        rows.append(dict(regra="idade em anos", descricao=f"< 0 ou > {cfg['max_age_years']}",
                         n_comparaveis=int(age.notna().sum()), n_violacoes=bad,
                         pct=round(100 * bad / max(age.notna().sum(), 1), 3), acao_sugerida="transformar em ausente"))
    res = pd.DataFrame(rows)
    rep.save("a2_coerencia_datas", res)
    crit = res[(res["n_violacoes"] > 0) & ((res["pct"] > 1.0) | (res["acao_sugerida"] == "excluir"))]
    if len(crit):
        rep.add("A2", "Coerência de datas", WARN,
                f"{len(crit)} regra(s) com violações relevantes: "
                + "; ".join(f"{r.regra} ({r.n_violacoes})" for r in crit.itertuples()))
    else:
        rep.add("A2", "Coerência de datas", OK, "violações ≤ 1% e nenhuma regra de exclusão violada")


def a2_duplicates(df, cfg, rep: Report) -> None:
    c = cfg["cols"]
    exact = int(pd.util.hash_pandas_object(df, index=False).duplicated().sum())  # hash: evita cópia da base
    rows = [dict(tipo="linhas exatamente duplicadas", n_linhas=exact, n_grupos=exact)]
    nn = c["nu_notific"]
    if nn in df.columns:
        d = df[df[nn].notna()].duplicated(subset=[nn], keep=False)
        grp = df.loc[d.index[d], nn].nunique()
        rows.append(dict(tipo=f"{nn} repetido (não implica mesma pessoa)", n_linhas=int(d.sum()), n_grupos=int(grp)))
        key = [x for x in (nn, c["dt_notific"], c["dt_nasc"]) if x in df.columns]
        if len(key) > 1:
            d2 = df.duplicated(subset=key, keep=False)
            rows.append(dict(tipo=f"mesma chave {key}", n_linhas=int(d2.sum()), n_grupos=int(df[d2][key].drop_duplicates().shape[0])))
    res = pd.DataFrame(rows)
    rep.save("a2_duplicidades", res)
    rep.add("A2", "Duplicidades", WARN if exact else OK,
            f"{exact:,} linhas exatas duplicadas; demais tipos em a2_duplicidades.csv")


def a2_maturity(df, cfg, rep: Report) -> None:
    c = cfg["cols"]
    dt = parse_date(df[c["dt_interna"]])
    hosp = (code_str(df[c["hospital"]]) == "1").fillna(False).to_numpy(bool)
    m = hosp & dt.notna().to_numpy(bool)
    sub = df.loc[m]
    mes = dt[m].dt.to_period("M").astype(str)
    closed = code_str(sub[c["evolucao"]]).isin(cfg["closed_codes"])
    enc = parse_date(sub[c["dt_encerra"]]) if c["dt_encerra"] in sub.columns else pd.Series(pd.NaT, index=sub.index)
    days = (enc - dt[m]).dt.days
    res = pd.DataFrame({"mes": mes, "fechado": closed, "tem_encerra": enc.notna(), "dias": days})
    out = res.groupby("mes").agg(n=("fechado", "size"), pct_evolucao_fechada=("fechado", lambda x: round(100 * x.mean(), 2)),
                                 pct_com_dt_encerra=("tem_encerra", lambda x: round(100 * x.mean(), 2)),
                                 mediana_dias_ate_encerra=("dias", "median")).reset_index()
    rep.save("a2_maturidade_evolucao_por_mes", out)
    out["ano"] = out["mes"].str[:4].astype(int)
    imaturo = out[out["ano"].isin(cfg["holdout_years"]) & (out["pct_evolucao_fechada"] < cfg["maturity_min_closed_pct"])]
    if len(imaturo):
        rep.add("A2", "Maturidade de EVOLUCAO (holdout)", WARN,
                f"{len(imaturo)} mês(es) abaixo de {cfg['maturity_min_closed_pct']}% fechados: "
                f"{', '.join(imaturo['mes'].head(6))}")
    else:
        rep.add("A2", "Maturidade de EVOLUCAO (holdout)", OK, "todos os meses do holdout com evolução madura")


def classify_variable(col: str, pct_vazio: float, cfg: dict) -> tuple[str, str, str]:
    if col in cfg["forbidden_vars"]:
        return "excluir", "Pós-admissão, desfecho ou critério de inclusão (risco de vazamento)", "Não"
    if col in cfg["conditional_vars"]:
        return "incluir com condição", "Depende de quando foi registrada/completa na admissão", "Verificar"
    if col in cfg["allowed_vars"]:
        if pct_vazio > 95:
            return "auditoria", "Permitida, mas quase toda vazia", "Verificar"
        return "incluir", "Disponível na admissão (proposta inicial)", "Sim"
    return "auditoria", "Não classificada: consultar dicionário", "Verificar"


def a2_eligibility(df, cfg, rep: Report) -> None:
    sample = df.sample(min(len(df), 100_000), random_state=0) if len(df) > 100_000 else df
    rows = []
    for col in df.columns:
        s = df[col]
        pv = float(100 * (s.isna() | (s.astype("string").str.strip() == "").fillna(False)).mean()) \
            if s.dtype == object or pd.api.types.is_string_dtype(s) else float(100 * s.isna().mean())
        classe, why, na_adm = classify_variable(col, pv, cfg)
        rows.append(dict(coluna=col, classe=classe, justificativa=why, existe_na_admissao_sugerido=na_adm,
                         pct_vazio=round(pv, 2), n_distintos_amostra=int(sample[col].nunique(dropna=True)),
                         quando_observada="", quando_chegou_na_base="", decisao_final="", responsavel="", data=""))
    carregadas = set(df.columns)
    for c_ in df.attrs.get("schema_cols", []):
        if canon(c_) not in carregadas:
            rows.append(dict(coluna=str(c_).upper(), classe="auditoria",
                             justificativa="Existe no Parquet, mas não foi carregada (fora das listas classificadas)",
                             existe_na_admissao_sugerido="Verificar", pct_vazio=None, n_distintos_amostra=None,
                             quando_observada="", quando_chegou_na_base="", decisao_final="", responsavel="", data=""))
    mat = pd.DataFrame(rows).sort_values(["classe", "coluna"])
    rep.save("a2_matriz_elegibilidade", mat)
    cont = mat["classe"].value_counts().to_dict()
    rep.add("A2", "Matriz de elegibilidade", WARN if cont.get("auditoria") else OK,
            f"{cont} — preencher colunas em branco e fechar 'auditoria'")


# =============================================================================
# A3 — Desenho experimental e pilotos
# =============================================================================
def load_feature_list(path: str | Path) -> list[str]:
    """Lê lista de features de .txt (1 por linha), .json ou .yaml/.yml."""
    p = Path(path)
    txt = p.read_text(encoding="utf-8")
    if p.suffix in (".yaml", ".yml"):
        import yaml

        data = yaml.safe_load(txt)
    elif p.suffix == ".json":
        data = json.loads(txt)
    else:
        return [canon(ln.split("#")[0]) for ln in txt.splitlines() if ln.split("#")[0].strip()]

    def find(obj):
        if isinstance(obj, list) and all(isinstance(x, str) for x in obj):
            return obj
        if isinstance(obj, dict) and ("numericas" in obj or "categoricas" in obj):
            return supervised_features({"features": obj})
        if isinstance(obj, dict):
            for k in ("features", "feature_cols", "variaveis", "variáveis", "colunas", "columns"):
                if k in obj:
                    r = find(obj[k])
                    if r:
                        return r
            for v in obj.values():
                r = find(v)
                if r:
                    return r
        return None

    res = find(data)
    if not res:
        raise ValueError(f"Nenhuma lista de features encontrada em {p}")
    return [canon(x) for x in res]


def load_supervised_yaml(path: str | Path) -> dict:
    import yaml

    return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}


def supervised_features(y: dict) -> list[str]:
    """Features efetivas do configs/supervised.yaml: `final` se preenchida, senão numéricas + categóricas."""
    f = y.get("features", {}) or {}
    lst = f.get("final") or ((f.get("numericas") or []) + (f.get("categoricas") or []))
    return [canon(x) for x in lst]


def a3_config_audit(y: dict, cfg: dict, rep: Report, schema_cols=None) -> None:
    """Confere o supervised.yaml contra as decisões do plano (A1–A3)."""
    st = "A3-cfg"
    tg = y.get("target", {}) or {}
    pos = [float(x) for x in (tg.get("positivos") or [])]
    if pos != [float(cfg["target_positive"])]:
        rep.add(st, "Alvo: positivos", WARN, f"positivos={pos}; plano prevê óbito SRAG = [{cfg['target_positive']}]")
    else:
        rep.add(st, "Alvo: positivos", OK, "óbito SRAG (evolucao=2) como positivo")
    if not any(k for k in tg if "outras" in k or "ausente" in k or "nulo" in k):
        rep.add(st, "Alvo: evolucao=3 e ausente", WARN,
                "o YAML só tem `descartar_ignorado` (evolucao==9). O C2 descarta 3/9/nulos em "
                "`filtrar_rotulos_validos`; confirmar em src/models/pipeline.py que `criar_alvo_binario` "
                "trata 3 e ausente como inválidos (nunca como cura)")
    ct = canon(y.get("coluna_tempo", ""))
    if ct != "DT_INTERNA":
        rep.add(st, "Coluna temporal", WARN,
                f"split usa '{y.get('coluna_tempo')}', mas o ponto de previsão do plano é DT_INTERNA")
    else:
        rep.add(st, "Coluna temporal", OK, "split por DT_INTERNA")
    tp = y.get("temporal", {}) or {}
    rep.add(st, "C2 x split por datas", WARN,
            "o C2 enviado cria `TemporalSplit(df, coluna_tempo, frac_treino, frac_validacao)` e não lê "
            "`temporal.modo`/`temporal.datas`: para holdout = 2025 o C precisa adaptar o split")
    if tp.get("modo") != "datas":
        rep.add(st, "Split temporal", WARN,
                f"modo='{tp.get('modo')}' (fração). Plano: desenvolvimento {cfg['dev_years']} / holdout "
                f"{cfg['holdout_years']} -> usar modo 'datas' (G2)")
    else:
        d = tp.get("datas", {}) or {}
        try:
            h0 = pd.Timestamp(d["holdout"]["start"])
            v1 = pd.Timestamp(d["validacao"]["end"])
            t0 = pd.Timestamp(d["treino"]["start"])
            ok = v1 < h0 and h0.year == min(cfg["holdout_years"]) and t0.year == min(cfg["dev_years"])
            rep.add(st, "Split temporal (datas)", OK if ok else FAIL,
                    f"treino>={t0.date()}, validação<={v1.date()}, holdout>={h0.date()}"
                    + ("" if ok else " — inconsistente com o plano"))
        except Exception:
            rep.add(st, "Split temporal (datas)", FAIL, "datas incompletas ou inválidas")
    if schema_cols:
        fisico = {str(c).lower() for c in schema_cols}
        por_canon = {canon(c): str(c).lower() for c in schema_cols}
        f = y.get("features", {}) or {}
        pedidas = [str(x).lower() for x in ((f.get("final") or []) + (f.get("numericas") or []) + (f.get("categoricas") or []))]
        if f.get("final"):
            pedidas = [str(x).lower() for x in f["final"]]
        deriv_pedidas = [n for n in pedidas if n in DERIVADAS]
        if deriv_pedidas:
            rep.add(st, "Features derivadas do YAML", OK,
                    f"{', '.join(deriv_pedidas)} não existem no Parquet: a Pessoa A as cria no dataset analítico")
        for rotulo, nomes, status in (("Features do YAML x Parquet", pedidas, FAIL),
                                      ("`proibidas` do YAML x Parquet", [str(x).lower() for x in (f.get("proibidas") or [])], WARN)):
            ausentes = [n for n in nomes if n not in fisico and n not in DERIVADAS]
            if ausentes:
                dicas = [f"{n}->{por_canon[canon(n)]}" for n in ausentes if canon(n) in por_canon]
                rep.add(st, rotulo, status,
                        f"não existem no Parquet: {', '.join(ausentes)}"
                        + (f" (nome físico provável: {', '.join(dicas)})" if dicas else "")
                        + (" — o C2 não conseguirá carregá-las" if status == FAIL else " — test_leakage não protege as colunas reais"))
            else:
                rep.add(st, rotulo, OK, "todos os nomes existem no Parquet")
    feats = supervised_features(y)
    forb = {canon(v) for v in cfg["forbidden_vars"]}
    yml_forb = {canon(v) for v in (y.get("features", {}) or {}).get("proibidas", []) or []}
    hit = sorted(set(feats) & (forb | yml_forb))
    soft = [h for h in hit if h == "HOSPITAL"]
    hard = [h for h in hit if h not in soft]
    if hard:
        rep.add(st, "Features x proibidas", FAIL, f"em X: {', '.join(hard)}")
    if soft:
        rep.add(st, "Feature constante", WARN, "internado/HOSPITAL é critério de inclusão (constante na coorte)")
    if not hit:
        rep.add(st, "Features x proibidas", OK, f"{len(feats)} features sem conflito")
    faltam = sorted(forb - yml_forb - {"HOSPITAL"})
    if faltam:
        rep.add(st, "Lista `proibidas` do YAML", WARN,
                f"{len(faltam)} do plano não protegidas pelo test_leakage: {', '.join(faltam[:12])}")
    if "NU_IDADE_N" in feats and not any(f in feats for f in ("TP_IDADE", "IDADE_ANOS")):
        rep.add(st, "Idade", WARN, "nu_idade_n sem tp_idade: unidade mistura dias/meses/anos; converter para anos")
    cond = sorted(set(feats) & {canon(v) for v in cfg["conditional_vars"]})
    if cond:
        rep.add(st, "Features condicionais", WARN, f"confirmar condição de uso: {', '.join(cond)}")
    pend = [k for k, v in (y.get("gates") or {}).items() if (v or {}).get("status") != "aprovado"]
    if pend:
        rep.add(st, "Gates", WARN, f"{len(pend)} pendentes: {', '.join(pend[:4])}... (A aprova G1/G2 com as regras A1–A3)")


def a3_forbidden(features: list[str], label: str, cfg, rep: Report, must_exclude_target=True) -> None:
    forb = {v.upper() for v in cfg["forbidden_vars"]}
    hit = sorted(set(features) & forb)
    hard = [h for h in hit if h != "HOSPITAL"]
    if "HOSPITAL" in hit:
        rep.add("A3", f"Feature constante ({label})", WARN, "HOSPITAL/internado é critério de inclusão (constante na coorte)")
    if hard:
        rep.add("A3", f"Variáveis proibidas ({label})", FAIL, f"presentes: {', '.join(hard)}")
    elif not hit:
        rep.add("A3", f"Variáveis proibidas ({label})", OK, f"{len(features)} variáveis, nenhuma proibida")
    cond = sorted(set(features) & {v.upper() for v in cfg["conditional_vars"]})
    if cond:
        rep.add("A3", f"Variáveis condicionais ({label})", WARN, f"confirmar condição de uso: {', '.join(cond)}")
    if label == "clustering" and must_exclude_target and cfg["cols"]["evolucao"] in features:
        rep.add("A3", "Desfecho no clustering", FAIL, "EVOLUCAO não pode formar clusters")


def a3_temporal_split(cohort: pd.DataFrame, cfg, rep: Report) -> None:
    dev, hold = set(cfg["dev_years"]), set(cfg["holdout_years"])
    problems = []
    if dev & hold:
        problems.append(f"anos sobrepostos: {sorted(dev & hold)}")
    if hold and dev and min(hold) <= max(dev):
        problems.append("holdout não é posterior ao desenvolvimento")
    present = set(cohort["_ano"].unique())
    if hold - present:
        problems.append(f"holdout sem registros: {sorted(hold - present)}")
    if dev - present:
        problems.append(f"desenvolvimento sem registros: {sorted(dev - present)}")
    split = np.where(cohort["_ano"].isin(dev), "desenvolvimento", np.where(cohort["_ano"].isin(hold), "holdout", "fora"))
    tab = (cohort.assign(split=split).groupby(["split", "_ano"])["_alvo"]
           .agg(n="size", n_obitos="sum", prevalencia_obito=lambda x: round(100 * x.mean(), 2)).reset_index())
    rep.save("a3_split_temporal", tab)
    if problems:
        rep.add("A3", "Split temporal", FAIL, "; ".join(problems))
        return
    prev = tab.groupby("split")["n_obitos"].sum() / tab.groupby("split")["n"].sum() * 100
    diff = abs(prev.get("holdout", np.nan) - prev.get("desenvolvimento", np.nan))
    if diff > 10:
        rep.add("A3", "Split temporal", WARN, f"prevalência difere {diff:.1f} p.p. entre dev e holdout (drift)")
    else:
        rep.add("A3", "Split temporal", OK, f"dev {sorted(dev)} < holdout {sorted(hold)}; Δ prevalência {diff:.1f} p.p.")


def a3_leak_scan(cohort: pd.DataFrame, cfg, rep: Report) -> None:
    """AUC univariada contra o alvo: valores ~1 sugerem vazamento (indicativo, não prova)."""
    from sklearn.metrics import roc_auc_score

    skip = set(cfg["cols"].values()) | {"_ano", "_alvo"}
    data = cohort.sample(min(len(cohort), cfg["leak_sample"]), random_state=0)
    y = data["_alvo"].to_numpy()
    if len(np.unique(y)) < 2:
        rep.add("A3", "Varredura de vazamento", WARN, "alvo com uma única classe; varredura não executada")
        return
    rows = []
    for col in data.columns:
        if col in skip:
            continue
        s = data[col]
        try:
            if pd.api.types.is_numeric_dtype(s):
                x = s.fillna(s.median()).to_numpy(float)
            else:
                if s.nunique() > cfg["leak_max_categories"]:
                    continue
                x = data.groupby(s.astype("string").fillna("<NA>"))["_alvo"].transform("mean").to_numpy(float)
            auc = roc_auc_score(y, x)
        except Exception:
            continue
        rows.append(dict(coluna=col, auc_univariada=round(auc, 4), forca=round(abs(auc - 0.5) * 2, 4)))
    res = pd.DataFrame(rows).sort_values("forca", ascending=False)
    rep.save("a3_varredura_vazamento", res)
    thr = cfg["leak_auc_threshold"]
    sus = res[(res["auc_univariada"] >= thr) | (res["auc_univariada"] <= 1 - thr)]
    if len(sus):
        rep.add("A3", "Varredura de vazamento", WARN,
                f"AUC univariada ≥ {thr}: {', '.join(sus['coluna'].head(8))} — investigar")
    else:
        rep.add("A3", "Varredura de vazamento", OK, f"nenhuma variável com AUC univariada ≥ {thr}")


def a3_suspicious_metrics(results: pd.DataFrame, cfg, rep: Report) -> None:
    res = results.copy()
    res.columns = [c.lower() for c in res.columns]
    thr = cfg["suspicious_metric_threshold"]
    cols = [c for c in ("roc_auc", "pr_auc") if c in res.columns]
    if not cols:
        rep.add("A3", "Métricas suspeitas", WARN, "colunas roc_auc/pr_auc não encontradas")
        return
    flag = res[(res[cols] >= thr).any(axis=1)]
    if len(flag):
        rep.add("A3", "Métricas suspeitas", WARN, f"{len(flag)} linha(s) com métrica ≥ {thr}: possível vazamento")
    else:
        rep.add("A3", "Métricas suspeitas", OK, f"nenhuma métrica ≥ {thr}")


def a3_audit_logs(logs_dir: str | Path, cfg, rep: Report) -> None:
    d = Path(logs_dir)
    files = [p for p in d.rglob("*") if p.is_file() and p.suffix in (".json", ".jsonl", ".log", ".txt")] if d.exists() else []
    if not files:
        rep.add("A3", "Auditoria de logs", WARN, f"nenhum log encontrado em {d}")
        return
    rows = []
    for p in files:
        txt = p.read_text(encoding="utf-8", errors="ignore")
        row = {"arquivo": str(p)}
        for k, rx in cfg["log_required_keys"].items():
            row[k] = bool(re.search(rx, txt, flags=re.I))
        rows.append(row)
    res = pd.DataFrame(rows)
    rep.save("a3_auditoria_logs", res)
    keys = list(cfg["log_required_keys"])
    incompletos = res[~res[keys].all(axis=1)]
    if len(incompletos):
        faltas = {k for k in keys if not res[k].all()}
        rep.add("A3", "Auditoria de logs", WARN, f"{len(incompletos)}/{len(res)} logs incompletos (faltam: {', '.join(sorted(faltas))})")
    else:
        rep.add("A3", "Auditoria de logs", OK, f"{len(res)} logs com todos os campos mínimos")


# =============================================================================
# A4 — Candidatos e decisão
# =============================================================================
def a4_decision_table(results: pd.DataFrame, cfg, rep: Report) -> None:
    """Espera colunas: modelo, [fold], roc_auc, pr_auc, brier (nomes case-insensitive)."""
    res = results.copy()
    res.columns = [c.lower() for c in res.columns]
    alias = {"model": "modelo", "candidate": "modelo", "candidato": "modelo"}
    res = res.rename(columns=alias)
    if "modelo" not in res.columns:
        rep.add("A4", "Tabela de decisão", FAIL, "coluna 'modelo' não encontrada")
        return
    metrics = [m for m in ("pr_auc", "roc_auc", "brier") if m in res.columns]
    agg = res.groupby("modelo")[metrics].agg(["mean", "std"])
    agg.columns = [f"{m}_{s}" for m, s in agg.columns]
    agg = agg.reset_index()
    lower = agg["modelo"].str.lower()
    base = agg[lower.str.contains("baseline|dummy|prevalen")]
    logi = agg[lower.str.contains("log")]
    notes = []
    for _, r in agg.iterrows():
        n = []
        if "pr_auc_mean" in agg.columns and len(logi) and "log" not in r["modelo"].lower() \
                and not re.search("baseline|dummy|prevalen", r["modelo"].lower()):
            gain = r["pr_auc_mean"] - logi["pr_auc_mean"].iloc[0]
            if gain < cfg["decision_min_pr_auc_gain"]:
                n.append(f"ganho de PR-AUC sobre a logística ({gain:+.3f}) não justifica complexidade")
            if "brier_mean" in agg.columns and r["brier_mean"] > logi["brier_mean"].iloc[0]:
                n.append("Brier pior que a logística")
        if "pr_auc_mean" in agg.columns and len(base) and r["pr_auc_mean"] <= base["pr_auc_mean"].iloc[0] \
                and not re.search("baseline|dummy|prevalen", r["modelo"].lower()):
            n.append("não supera o baseline em PR-AUC")
        if "pr_auc_std" in agg.columns and r["pr_auc_mean"] > 0 and r["pr_auc_std"] / r["pr_auc_mean"] > cfg["decision_max_cv_ratio"]:
            n.append("alta variação entre folds")
        notes.append("; ".join(n) if n else "sem alerta automático")
    agg["alertas_automaticos"] = notes
    agg["decisao"] = ""
    agg["justificativa_descarte_ou_manutencao"] = ""
    agg["pendencia_para_18_10"] = ""
    rep.save("a4_tabela_decisao", agg.round(4))
    n_alert = sum(n != "sem alerta automático" for n in notes)
    rep.add("A4", "Tabela de decisão", WARN if n_alert else OK,
            f"{len(agg)} candidatos; {n_alert} com alerta — preencher decisão/justificativa")


# =============================================================================
# Config, carga da base e registros (decisões / atas)
# =============================================================================
def load_config(path: str | Path | None = "configs/decisoes.yaml") -> dict:
    """DEFAULT_CONFIG sobreposto pelo YAML de decisões (se existir)."""
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    if path and Path(path).exists():
        import yaml

        for k, v in (yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}).items():
            cfg[k] = {**cfg[k], **v} if isinstance(cfg.get(k), dict) and isinstance(v, dict) else v
    return cfg


def find_base(root: str | Path = ".") -> Path | None:
    """Procura a base ORIGINAL (Parquet/CSV). Ignora data/analytical (saída da Pessoa A) e metadados."""
    r = Path(root)
    for pat in ("data/raw/**/*.parquet", "data/**/*.parquet", "data/raw/**/*.csv", "data/**/*.csv"):
        hits = [h for h in sorted(r.glob(pat))
                if "analytical" not in h.parts and "dataset_supervisionado" not in h.name]
        if hits:
            return hits[0]
    return None


def colunas_necessarias(schema_cols, cfg: dict, supervised_config=None, modo: str = "classificadas") -> list[str]:
    """Colunas físicas do Parquet que as verificações realmente usam (a base tem ~194; carregar todas estoura a memória).

    modo "minimas": essenciais (coorte/alvo/datas) + códigos esperados + o que o supervised.yaml pede
    (features, alvo, tempo, grupos). modo "classificadas": soma as listas proibidas/condicionais/permitidas (A2).
    """
    need = {canon(x) for x in cfg["cols"].values()} | {canon(x) for x in cfg["expected_codes"]}
    if modo != "minimas":
        for k in ("forbidden_vars", "conditional_vars", "allowed_vars"):
            need |= {canon(x) for x in cfg[k]}
    if supervised_config and Path(supervised_config).exists():
        y = load_supervised_yaml(supervised_config)
        f = y.get("features", {}) or {}
        need |= {canon(x) for x in supervised_features(y)}
        need |= {canon(x) for x in (f.get("proibidas") or [])}
        need |= {canon(x) for x in ((y.get("avaliacao") or {}).get("grupos") or [])}
        need |= {canon((y.get("target") or {}).get("coluna", cfg["cols"]["evolucao"])), canon(y.get("coluna_tempo", ""))}
    return [c for c in schema_cols if canon(c) in need]


def carregar_base(path=None, demo: bool = False, sample: int = 0, colunas="classificadas",
                  cfg: dict | None = None, supervised_config=None, compactar: bool = True) -> pd.DataFrame:
    """Lê a base. path=None -> usa `src.utils.storage.get_parquet()` do projeto (ou procura em data/).

    colunas: "minimas" (só o essencial + o que o supervised.yaml pede; A1/A3/A3b), "classificadas" (soma as listas de
    variáveis; A2), "todas" (pesado) ou lista de nomes. O schema completo fica em df.attrs["schema_cols"].
    compactar=True lê o Parquet via pyarrow com texto em `category` (e libera a tabela Arrow durante a conversão):
    reduz muito o pico de memória (a base tem milhões de linhas).
    """
    if demo:
        print("[demo] usando dados sintéticos")
        df = make_demo()[0]
        df.attrs["schema_cols"] = list(df.columns)
        return df
    p = Path(path) if path else None
    if p is None:
        try:
            from src.utils import storage  # pipeline do projeto

            p = Path(storage.get_parquet(force=False))
        except Exception as e:  # noqa: BLE001
            print(f"[storage] indisponível ({type(e).__name__}); procurando em data/ ...")
            p = find_base()
    if p is None or not p.exists():
        raise FileNotFoundError(
            f"Base não encontrada (procurei em '{Path.cwd() / 'data'}' por *.parquet e *.csv). "
            "Informe DATA_PATH com o caminho do arquivo ou coloque-o em data/raw/.")
    cfg = cfg or load_config()
    modo_leitura = "padrão"
    if p.suffix == ".parquet":
        import pyarrow.parquet as pq

        schema_cols = pq.ParquetFile(p).schema_arrow.names
        if colunas == "todas":
            cols = None
        elif isinstance(colunas, (list, tuple)):
            cols = [c for c in schema_cols if c.lower() in {str(x).lower() for x in colunas}]
        else:
            cols = colunas_necessarias(schema_cols, cfg, supervised_config, modo=str(colunas))
        df = None
        if compactar:
            try:
                tabela = pq.read_table(p, columns=cols)
                df = tabela.to_pandas(self_destruct=True, strings_to_categorical=True, split_blocks=True)
                del tabela
                modo_leitura = "compacto (texto em category)"
            except Exception as e:  # noqa: BLE001
                print(f"[leitura compacta falhou: {type(e).__name__}: {str(e)[:80]}] usando leitura padrão")
                df = None
        if df is None:
            df = pd.read_parquet(p, columns=cols)
    else:
        df = pd.read_csv(p, low_memory=False)
        schema_cols = list(df.columns)
    df.attrs["schema_cols"] = list(schema_cols)
    print(f"[base] {p} -> {len(df):,} linhas x {df.shape[1]} colunas carregadas (de {len(schema_cols)} no arquivo) | leitura {modo_leitura}")
    if sample and len(df) > sample:
        df = df.sample(sample, random_state=0)
        print(f"[amostra] {sample:,} linhas")
    return df


def uso_memoria_gb(df: pd.DataFrame) -> float:
    return float(df.memory_usage(index=False, deep=True).sum() / 1e9)


DECISION_COLS = ["id", "etapa", "tema", "decisao", "responsavel", "data", "status", "impacto", "evidencia"]


def log_decision(out, id: str, tema: str, decisao: str, etapa: str = "", responsavel: str = "Pessoa A",
                 status: str = "proposta", impacto: str = "", evidencia: str = "") -> pd.DataFrame:
    """Insere/atualiza (por id) uma linha na tabela de decisões. status: proposta | aprovada | revisar."""
    path = Path(out) / "tabela_decisoes.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    row = dict(id=id, etapa=etapa, tema=tema, decisao=decisao, responsavel=responsavel,
               data=pd.Timestamp.today().date().isoformat(), status=status, impacto=impacto, evidencia=evidencia)
    t = pd.read_csv(path, dtype=str).fillna("") if path.exists() else pd.DataFrame(columns=DECISION_COLS)
    t = pd.concat([t[t["id"] != id], pd.DataFrame([row])], ignore_index=True)[DECISION_COLS]
    t.to_csv(path, index=False, encoding="utf-8-sig")
    return t


def write_ata(out, nome: str, data: str, decisoes=(), pendencias=(), riscos=(), shortlist=(),
              descartes=(), rep: Report | None = None) -> Path:
    """Gera a ata (Gates 2/3, 17/10...) em Markdown a partir de listas e dos alertas do relatório."""
    def sec(titulo, itens):
        return [f"## {titulo}", ""] + ([f"- {i}" for i in itens] if itens else ["- (nenhum registrado)"]) + [""]

    lines = [f"# {nome}", "", f"**Data:** {data}", ""]
    lines += sec("Decisões", decisoes) + sec("Candidatos na shortlist", shortlist) + sec("Descartes e justificativas", descartes)
    lines += sec("Riscos", riscos) + sec("Pendências", pendencias)
    if rep is not None:
        alerts = [f for f in rep.findings if f[2] != OK]
        lines += ["## Alertas das verificações automáticas", ""]
        lines += [f"- [{f[2]}] {f[0]} / {f[1]}: {f[3]}" for f in alerts] or ["- nenhum"]
    slug = re.sub(r"[^a-z0-9]+", "_", nome.lower()).strip("_")
    path = Path(out) / (slug if slug.startswith("ata_") else f"ata_{slug}") 
    path = path.with_suffix(".md")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


# =============================================================================
# Execução
# =============================================================================
def run(df: pd.DataFrame, args, cfg: dict) -> Report:
    rep = Report(args.out)
    df = prepare(df)
    if args.sample and len(df) > args.sample:
        df = df.sample(args.sample, random_state=0)
        print(f"[amostra] usando {args.sample:,} linhas")
    stage = args.stage
    do = lambda s: stage in (s, "all")  # noqa: E731

    a1_columns(df, cfg, rep)
    if rep.has_failure:
        rep.write_md()
        return rep

    cohort = None
    if do("a1") or do("a3"):
        if do("a1"):
            a1_code_tables(df, cfg, rep)
            a1_waterfall(df, cfg, rep)
            a1_target(df, cfg, rep)
        cohort = a1_cohort(df, cfg)
    if do("a2"):
        a2_missing(df, cfg, rep)
        a2_dates(df, cfg, rep)
        a2_duplicates(df, cfg, rep)
        a2_maturity(df, cfg, rep)
        a2_eligibility(df, cfg, rep)
    if do("a3"):
        if args.supervised_config:
            y = load_supervised_yaml(args.supervised_config)
            a3_config_audit(y, cfg, rep, df.attrs.get("schema_cols"))
            if not args.features_supervised:
                a3_forbidden(supervised_features(y), "supervisionado", cfg, rep)
        if args.features_supervised:
            a3_forbidden(load_feature_list(args.features_supervised), "supervisionado", cfg, rep)
        if args.features_clustering:
            a3_forbidden(load_feature_list(args.features_clustering), "clustering", cfg, rep)
        if cohort is not None and len(cohort):
            a3_temporal_split(cohort, cfg, rep)
            a3_leak_scan(cohort, cfg, rep)
        if args.logs_dir:
            a3_audit_logs(args.logs_dir, cfg, rep)
        if args.results:
            a3_suspicious_metrics(pd.read_csv(args.results), cfg, rep)
    if do("a4") and args.results:
        a4_decision_table(pd.read_csv(args.results), cfg, rep)
    elif stage == "a4":
        rep.add("A4", "Tabela de decisão", FAIL, "informe --results com a tabela de experimentos")
    path = rep.write_md()
    print(f"\nRelatório: {path}")
    return rep


def make_demo(n: int = 30_000, seed: int = 0, inicio: str = "2022-01-01", anos: int = 4) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Dados sintéticos com defeitos plantados, para testar o script."""
    rng = np.random.default_rng(seed)
    interna = pd.Timestamp(inicio) + pd.to_timedelta(rng.integers(0, 365 * anos - 30, n), unit="D")
    sint = interna - pd.to_timedelta(rng.integers(0, 10, n), unit="D")
    df = pd.DataFrame({
        "NU_NOTIFIC": rng.integers(10**8, 10**9, n).astype(str),
        "DT_NOTIFIC": sint + pd.to_timedelta(rng.integers(0, 5, n), unit="D"),
        "DT_SIN_PRI": sint,
        "DT_INTERNA": interna,
        "DT_NASC": sint - pd.to_timedelta(rng.integers(365, 365 * 90, n), unit="D"),
        "NU_IDADE_N": rng.integers(1, 90, n),
        "TP_IDADE": 3,
        "HOSPITAL": rng.choice([1, 2, 9], n, p=[0.9, 0.08, 0.02]),
        "CS_SEXO": rng.choice(["M", "F", "I"], n, p=[0.49, 0.5, 0.01]),
        "FEBRE": rng.choice([1, 2, 9], n),
        "DISPNEIA": rng.choice([1, 2, 9], n),
        "SATURACAO": rng.choice([1, 2, 9, np.nan], n),
    })
    risk = (df["NU_IDADE_N"] / 90 + (df["DISPNEIA"] == 1) * 0.3 + rng.normal(0, 0.4, n))
    obito = risk > 0.9
    evo = np.where(obito, 2, 1)
    evo = np.where(rng.random(n) < 0.03, 3, evo)
    evo = np.where(rng.random(n) < 0.04, 9, evo)
    df["EVOLUCAO"] = evo
    df["DT_EVOLUCA"] = interna + pd.to_timedelta(rng.integers(2, 30, n), unit="D")
    df["DT_ENCERRA"] = df["DT_EVOLUCA"] + pd.to_timedelta(rng.integers(0, 40, n), unit="D")
    df["UTI"] = np.where(obito, rng.choice([1, 2], n, p=[0.8, 0.2]), rng.choice([1, 2], n, p=[0.3, 0.7]))
    df["VAZ_DEMO"] = (obito).astype(int)  # vazamento plantado
    # defeitos plantados
    df.loc[:30, "DT_INTERNA"] = pd.NaT
    df.loc[31:60, "DT_EVOLUCA"] = df.loc[31:60, "DT_INTERNA"] - pd.Timedelta(days=5)
    df.loc[61:90, "EVOLUCAO"] = 7
    df = pd.concat([df, df.iloc[200:230]], ignore_index=True)  # duplicatas exatas
    # 2025 imaturo: evolução ainda aberta nos meses finais
    late = df["DT_INTERNA"] >= pd.Timestamp("2025-09-01")
    df.loc[late & (rng.random(len(df)) < 0.5), "EVOLUCAO"] = np.nan
    res = pd.DataFrame({
        "modelo": ["baseline"] * 3 + ["logistica"] * 3 + ["boosting"] * 3 + ["boosting_leak"] * 3,
        "fold": [1, 2, 3] * 4,
        "pr_auc": [0.15, 0.16, 0.15, 0.40, 0.42, 0.38, 0.405, 0.41, 0.39, 0.99, 0.99, 0.98],
        "roc_auc": [0.5, 0.5, 0.5, 0.80, 0.81, 0.79, 0.805, 0.81, 0.80, 0.99, 0.99, 0.99],
        "brier": [0.15, 0.15, 0.15, 0.10, 0.10, 0.11, 0.11, 0.10, 0.11, 0.01, 0.01, 0.01],
    })
    return df, res
