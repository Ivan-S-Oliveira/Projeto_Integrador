<!-- PROJECT_COMPLETE_REFERENCE part 3/3 -->
## `src/protocolo/verificacoes.py`

- Git: `tracked` · status `clean`
- Size: `89.8 KB` · modified `2026-10-16 14:54 UTC`
- SHA-256: `2bf4f22f18037a036d9db390362ee569764e67732feb4adf65d5e3fc51f957fd`

```python
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
            "sem_2020_2021": {"anos": [2019, 2022, 2023, 2024, 2025],
                              "descricao": "Remove 2020 e 2021 (anos de pandemia)"},
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
```

## `src/utils/__init__.py`

- Git: `tracked` · status `clean`
- Size: `0 B` · modified `2026-10-16 14:54 UTC`
- SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

```python

```

## `src/utils/config.py`

- Git: `tracked` · status `clean`
- Size: `8.0 KB` · modified `2026-10-16 14:54 UTC`
- SHA-256: `83593c64261804f7b18aab33d121ef6e4d90c7a65aa612fb5649bf4889fed358`

```python
"""
Configurações centralizadas do Projeto Integrador.

Fonte única da verdade para diretórios, identificação da versão dos dados,
seed de reprodutibilidade e acesso tipado ao ``configs/supervised.yaml``.

Segredos e URLs sensíveis (``GITHUB_TOKEN``, ``SRAG_PARQUET_URL``) são lidos
em tempo de execução via ``os.getenv``, nunca no import. O YAML aceita
interpolação ``${VAR}``, resolvida no momento da leitura.

Uso típico::

    from src.utils import config as C

    C.SEED
    C.OUTPUTS_DIR
    C.cfg("target", "coluna")
    C.exigir_gate("G7_calibracao")
"""

from __future__ import annotations

import hashlib
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


ROOT_DIR: Path = Path(__file__).resolve().parents[2]

SEED         = 42
RANDOM_STATE = SEED

DATA_DIR       = ROOT_DIR / "data"
RAW_DIR        = DATA_DIR / "raw"
PROCESSED_DIR  = DATA_DIR / "processed"
ANALYTICAL_DIR = DATA_DIR / "analytical"
TREINO_DIR     = DATA_DIR / "treino"

CONFIGS_DIR  = ROOT_DIR / "configs"
MODELS_DIR   = ROOT_DIR / "models"
OUTPUTS_DIR  = ROOT_DIR / "outputs"
RUNS_DIR     = OUTPUTS_DIR / "runs"
LOGS_DIR     = ROOT_DIR / "logs"
REPORTS_DIR  = ROOT_DIR / "reports"
FIGURES_DIR  = REPORTS_DIR / "figures"

TABLES_DIR      = OUTPUTS_DIR / "tables"
PREDICTIONS_DIR = OUTPUTS_DIR / "predictions"

SUPERVISED_YAML = CONFIGS_DIR / "supervised.yaml"

GITHUB_REPO  = "Ivan-S-Oliveira/Projeto_Integrador"
DATA_VERSION = "dados-v2"
PARQUET_NAME = "srag.parquet"

GITHUB_RELEASE_URL = (
    f"https://github.com/{GITHUB_REPO}/releases/download/{DATA_VERSION}/"
)

HTTP_TIMEOUT    = 180
HTTP_TENTATIVAS = 3
HTTP_BACKOFF    = 5

CSV_SEP      = ","
CSV_ENCODING = "utf-8-sig"
COLS         = None

PARQUET_COMPRESSION = "zstd"
CSV_CHUNKSIZE       = 500_000


class GatePendenteError(RuntimeError):
    """Levantado quando se tenta usar um valor que depende de gate não aprovado."""


def github_token() -> str | None:
    """Token do GitHub (opcional) para releases/downloads autenticados."""
    return os.getenv("GITHUB_TOKEN")


def srag_parquet_url() -> str:
    """URL do Parquet oficial processado.

    Construída a partir de ``GITHUB_REPO`` / ``DATA_VERSION`` /
    ``PARQUET_NAME``. Pode ser sobrescrita via ``SRAG_PARQUET_URL``.
    """
    url_padrao = (
        f"https://github.com/{GITHUB_REPO}/releases/download/"
        f"{DATA_VERSION}/{PARQUET_NAME}"
    )
    return os.getenv("SRAG_PARQUET_URL", url_padrao).strip() or url_padrao


_ENV_PATTERN = re.compile(r"\$\{(\w+)\}")


def _interpolar_env(texto: str) -> str:
    """Substitui ``${VAR}`` pelo valor de ``os.getenv``; ausente vira ``""``."""
    return _ENV_PATTERN.sub(lambda m: os.getenv(m.group(1), ""), texto)


def _get_nested(mapping: Any, *chaves: str, default: Any = None) -> Any:
    """Acesso a caminho de chaves num dict; devolve ``default`` se faltar."""
    atual = mapping
    for k in chaves:
        if not isinstance(atual, dict) or k not in atual:
            return default
        atual = atual[k]
    return atual


@lru_cache(maxsize=1)
def carregar_supervised() -> dict[str, Any]:
    """Lê ``configs/supervised.yaml`` e devolve o dict parseado (cacheado).

    Resolve ``${VAR}`` antes do parse. Levanta ``FileNotFoundError`` se o
    YAML não existir e ``ValueError`` se a raiz não for mapping.
    """
    if not SUPERVISED_YAML.exists():
        raise FileNotFoundError(
            f"Configuração não encontrada: {SUPERVISED_YAML}\n"
            f"Crie o arquivo em {CONFIGS_DIR}/supervised.yaml "
            f"ou ajuste CONFIGS_DIR / SUPERVISED_YAML em config.py."
        )

    texto = _interpolar_env(SUPERVISED_YAML.read_text(encoding="utf-8"))
    dados = yaml.safe_load(texto) or {}

    if not isinstance(dados, dict):
        raise ValueError(
            f"{SUPERVISED_YAML} deve conter um mapeamento (dict) na raiz, "
            f"mas veio {type(dados).__name__}."
        )
    return dados


def supervised_yaml_sha256() -> str | None:
    """SHA-256 do ``supervised.yaml``, ou ``None`` se o arquivo não existir."""
    if not SUPERVISED_YAML.exists():
        return None
    h = hashlib.sha256()
    with open(SUPERVISED_YAML, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def cfg(*chaves: str, default: Any = None) -> Any:
    """Acessa ``configs/supervised.yaml`` por caminho de chaves.

    Exemplo::

        cfg("target", "coluna")       # → "evolucao"
        cfg("temporal", "fracao")     # → {"treino": 0.7, "validacao": 0.15}

    Devolve ``default`` se qualquer chave do caminho não existir.
    """
    return _get_nested(carregar_supervised(), *chaves, default=default)


def exigir_valor(valor: Any, *, caminho: str, gate: str) -> Any:
    """Devolve ``valor`` se preenchido; levanta ``GatePendenteError`` se ``None`` ou ``"TBD"``.

    Usado para valores do YAML que só podem ser preenchidos após gate aprovado.
    """
    if valor is None or valor == "TBD":
        raise GatePendenteError(
            f"Valor não definido em '{caminho}'. "
            f"Aprove o gate '{gate}' em configs/supervised.yaml antes de usar."
        )
    return valor


def gate_aprovado(nome_gate: str) -> bool:
    """True se ``gates.<nome_gate>.status == 'aprovado'``."""
    return _get_nested(carregar_supervised(), "gates", nome_gate, default={}).get("status") == "aprovado"


def exigir_gate(nome_gate: str) -> None:
    """Levanta ``GatePendenteError`` se o gate ainda não estiver aprovado.

    Use no início de etapas que dependem de decisão metodológica congelada
    (ex.: holdout antes de G9).
    """
    if not gate_aprovado(nome_gate):
        raise GatePendenteError(
            f"Gate '{nome_gate}' está pendente. "
            f"Aprove-o em configs/supervised.yaml (status: aprovado) "
            f"antes de rodar esta etapa."
        )


def features_finais() -> list[str]:
    """Lista final de features.

    Usa ``features.final`` se preenchida; caso contrário, concatena
    ``features.numericas`` + ``features.categoricas``.
    """
    f = cfg("features") or {}
    return list(f["final"]) if f.get("final") else (
        list(f.get("numericas", [])) + list(f.get("categoricas", []))
    )


def limiar_ativo() -> float:
    """Limiar de decisão vigente.

    Usa ``limiar.otimo`` se o gate ``G8_limiar`` estiver aprovado e o valor
    preenchido; caso contrário, cai em ``limiar.default`` (0.5).
    """
    lim = cfg("limiar") or {}
    if gate_aprovado("G8_limiar") and lim.get("otimo") is not None:
        return float(lim["otimo"])
    return float(lim.get("default", 0.5))


def resumo() -> str:
    """Resumo legível das configurações ativas — usado em bootstrap de notebooks."""
    yaml_ok = "ok" if SUPERVISED_YAML.exists() else "AUSENTE"
    linhas = [
        ("ROOT_DIR",          ROOT_DIR),
        ("DATA_DIR",          DATA_DIR),
        ("RAW_DIR",           RAW_DIR),
        ("PROCESSED_DIR",     PROCESSED_DIR),
        ("ANALYTICAL_DIR",    ANALYTICAL_DIR),
        ("TREINO_DIR",        TREINO_DIR),
        ("OUTPUTS_DIR",       OUTPUTS_DIR),
        ("RUNS_DIR",          RUNS_DIR),
        ("LOGS_DIR",          LOGS_DIR),
        ("CONFIGS_DIR",       CONFIGS_DIR),
        ("SUPERVISED_YAML",   f"{SUPERVISED_YAML} ({yaml_ok})"),
        ("PARQUET_NAME",      PARQUET_NAME),
        ("DATA_VERSION",      DATA_VERSION),
        ("GITHUB_REPO",       GITHUB_REPO),
        ("HTTP_TIMEOUT",      HTTP_TIMEOUT),
        ("HTTP_TENTATIVAS",   HTTP_TENTATIVAS),
        ("SEED",              SEED),
        ("GITHUB_TOKEN?",     bool(github_token())),
        ("SRAG_PARQUET_URL",  srag_parquet_url()),
        ("SUPERVISED_SHA256", supervised_yaml_sha256()),
    ]
    return "\n".join(f"{nome:18s}= {valor}" for nome, valor in linhas)


if __name__ == "__main__":
    print(resumo())
```

## `src/utils/env.py`

- Git: `tracked` · status `clean`
- Size: `3.7 KB` · modified `2026-10-16 14:54 UTC`
- SHA-256: `7dce7d27c80c42f4efe7f89128fafb3763fe78c8070593ad5c3d508284ce866b`

```python
"""
Variáveis de ambiente e segredos do projeto.

Fluxo: ``.env`` → ``os.environ`` → ``config.py`` → restante do projeto.

O arquivo ``.env`` nunca é versionado (ver ``.gitignore``); use
``.env.example`` como template. Diretórios são aliases de
``src.utils.config``, fonte única da verdade.
"""

from __future__ import annotations

import os
from pathlib import Path

from src.utils import config as C


# Aliases públicos — conveniência para notebooks e testes.
ROOT      = C.ROOT_DIR
DATA      = C.DATA_DIR
RAW       = C.RAW_DIR
PROCESSED = C.PROCESSED_DIR
TREINO    = C.TREINO_DIR
FIGURES   = C.FIGURES_DIR

# Diretórios criados por ``garantir_diretorios``. A ordem não importa —
# ``mkdir(parents=True)`` cria a árvore conforme necessário.
_DIRS_PADRAO = (
    C.DATA_DIR, C.RAW_DIR, C.PROCESSED_DIR, C.ANALYTICAL_DIR,
    C.TREINO_DIR, C.CONFIGS_DIR, C.MODELS_DIR, C.OUTPUTS_DIR,
    C.RUNS_DIR, C.LOGS_DIR, C.REPORTS_DIR, C.FIGURES_DIR,
    C.TABLES_DIR, C.PREDICTIONS_DIR,
)


def garantir_diretorios() -> None:
    """Cria todos os diretórios padrão do projeto, se ainda não existirem.

    Percorre as constantes de ``config.py`` — nenhum caminho é redefinido aqui.
    """
    for p in _DIRS_PADRAO:
        p.mkdir(parents=True, exist_ok=True)


def carregar_dotenv(caminho: Path | None = None) -> bool:
    """Carrega ``.env`` da raiz do projeto (ou de ``caminho``).

    Retorna ``True`` se o arquivo foi encontrado e carregado, ``False`` caso
    contrário (arquivo ausente ou ``python-dotenv`` indisponível). Não
    sobrescreve variáveis já definidas no ambiente.
    """
    # Lazy: python-dotenv não é dependência obrigatória — permite importar
    # este módulo em ambientes que não o têm instalado.
    try:
        from dotenv import load_dotenv
    except ImportError:
        return False

    caminho = Path(caminho) if caminho else ROOT / ".env"
    if not caminho.exists():
        return False

    load_dotenv(dotenv_path=caminho, override=False)
    return True


def detectar_ambiente() -> str:
    """``"ci"`` se estiver em pipeline, senão ``"local"``."""
    return "ci" if os.getenv("CI") or os.getenv("GITHUB_ACTIONS") else "local"


ENV = detectar_ambiente()


def get_env(nome: str, default: str | None = None) -> str | None:
    """Lê uma variável de ambiente, com default opcional."""
    return os.getenv(nome, default)


def get_secret(nome: str, obrigatorio: bool = True) -> str | None:
    """Lê um segredo/variável sensível do ambiente.

    Se ``obrigatorio=True`` (default) e a variável não existir, levanta
    ``RuntimeError`` com instruções de configuração. Se ``False``, devolve
    ``None``.
    """
    valor = os.getenv(nome)
    if valor:
        return valor
    if not obrigatorio:
        return None

    raise RuntimeError(
        f"Variável de ambiente '{nome}' não definida.\n"
        f"Defina-a de uma destas formas:\n"
        f"  1) Crie/edite o arquivo {ROOT / '.env'} (não versionado):\n"
        f"         {nome}=seu_valor_aqui\n"
        f"  2) Exporte no shell antes de rodar o projeto:\n"
        f"         Linux/macOS:  export {nome}=seu_valor_aqui\n"
        f"         PowerShell:   $env:{nome} = \"seu_valor_aqui\"\n"
    )


def resumo() -> str:
    """Resumo legível do estado do ambiente."""
    linhas = [
        ("ROOT_DIR",         ROOT),
        ("ENV",              ENV),
        (".env encontrado?", (ROOT / ".env").exists()),
        ("GITHUB_TOKEN?",    bool(os.getenv("GITHUB_TOKEN"))),
    ]
    return "\n".join(f"{nome:18s}= {valor}" for nome, valor in linhas)


if __name__ == "__main__":
    carregar_dotenv()
    garantir_diretorios()
    print(resumo())
```

## `src/utils/hashing.py`

- Git: `tracked` · status `clean`
- Size: `891 B` · modified `2026-10-16 14:54 UTC`
- SHA-256: `aa96962d96190d264f1a459148e77cafb11afeb5598f0bc557f8422f797e044f`

```python
"""Hashing de arquivos para verificação de integridade.

Centraliza ``sha256_file``, usado tanto pela resolução de coorte
(``src/data/cohort_source.py``) quanto pela persistência do artefato
supervisionado (``src/data/supervised_artifact.py``).
"""

from __future__ import annotations

import hashlib
from pathlib import Path

__all__ = ["sha256_file"]

_DEFAULT_CHUNK_SIZE = 1024 * 1024


def sha256_file(path: Path, chunk_size: int = _DEFAULT_CHUNK_SIZE) -> str:
    """Calcula SHA-256 de um arquivo sem carregá-lo integralmente em memória.

    Lê em blocos de ``chunk_size`` bytes (default 1 MiB), permitindo
    hashear arquivos grandes com memória constante.
    """
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()
```

## `src/utils/io_eficiente.py`

- Git: `tracked` · status `clean`
- Size: `2.2 KB` · modified `2026-10-18 14:26 UTC`
- SHA-256: `88c0d654f32f8de1c7142692301599589b61a3aa4097a06cfd4b1bf74aae6859`

```python
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
```

## `src/utils/performance.py`

- Git: `tracked` · status `clean`
- Size: `3.0 KB` · modified `2026-10-18 14:26 UTC`
- SHA-256: `da66506466e2a3fe0c39751c34dda8812cb3125d1b831a35e00a1b9f13fa743d`

```python
"""Medição simples de tempo e memória para os notebooks SRAG."""
from __future__ import annotations
import gc, os, threading, time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
import pandas as pd
try:
    import psutil
except ImportError:
    psutil = None
try:
    import pyarrow as pa
except ImportError:
    pa = None
_MB = 1_048_576

def rss_mb() -> float:
    return 0.0 if psutil is None else psutil.Process(os.getpid()).memory_info().rss / _MB

def arrow_mb() -> float:
    return 0.0 if pa is None else pa.total_allocated_bytes() / _MB

def memoria_df_mb(obj) -> float:
    uso = obj.memory_usage(index=True, deep=True)
    return float(uso.sum() if hasattr(uso, "sum") else uso) / _MB

def liberar(namespace: dict, nomes, fechar_figuras: bool=True) -> list[str]:
    removidos=[]
    for nome in nomes:
        if nome in namespace:
            del namespace[nome]; removidos.append(nome)
    if fechar_figuras:
        try:
            import matplotlib.pyplot as plt
            plt.close("all")
        except Exception:
            pass
    antes=rss_mb(); gc.collect(); depois=rss_mb()
    print(f"[liberar] {removidos} | RSS {antes:,.0f} -> {depois:,.0f} MB")
    return removidos

class _Pico:
    def __init__(self, intervalo=0.2):
        self.intervalo=intervalo; self.pico=rss_mb(); self.stop=threading.Event()
        self.thread=threading.Thread(target=self._run,daemon=True)
    def _run(self):
        while not self.stop.is_set():
            self.pico=max(self.pico,rss_mb()); time.sleep(self.intervalo)
    def __enter__(self): self.thread.start(); return self
    def __exit__(self,*_):
        self.stop.set(); self.thread.join(timeout=2); self.pico=max(self.pico,rss_mb())

@dataclass
class Monitor:
    notebook: str
    pasta_saida: Path|None=None
    registros: list[dict]=field(default_factory=list)
    @contextmanager
    def etapa(self,nome: str,**extras):
        inicio=time.perf_counter(); rss0=rss_mb(); arr0=arrow_mb(); status="ok"
        try:
            with _Pico() as pico: yield
        except BaseException:
            status="erro"; raise
        finally:
            reg={"notebook":self.notebook,"etapa":nome,"status":status,
                 "duracao_s":round(time.perf_counter()-inicio,3),
                 "rss_inicio_mb":round(rss0,1),"rss_fim_mb":round(rss_mb(),1),
                 "rss_pico_mb":round(pico.pico,1),"arrow_inicio_mb":round(arr0,1),
                 "arrow_fim_mb":round(arrow_mb(),1)}
            reg.update(extras); self.registros.append(reg)
            print(f"[{self.notebook}] {nome}: {reg['duracao_s']}s | pico {reg['rss_pico_mb']} MB | {status}")
    def resumo(self): return pd.DataFrame(self.registros)
    def salvar(self):
        pasta=self.pasta_saida or Path("outputs/performance"); pasta.mkdir(parents=True,exist_ok=True)
        caminho=pasta/f"{self.notebook}.csv"; self.resumo().to_csv(caminho,index=False,encoding="utf-8-sig")
        return caminho
```

## `src/utils/reproducibility.py`

- Git: `tracked` · status `clean`
- Size: `13.1 KB` · modified `2026-10-16 14:54 UTC`
- SHA-256: `15c5a5196d30fb740693656dc5700fc2ef5b7ff4c1cb9c9e55dd3bf876094064`

```python
"""
Registro de execuções para reprodutibilidade (critério C1).

Cada execução grava em ``outputs/runs/<RUN_ID>/``:

- ``metadata.json`` — tudo estruturado
- ``summary.txt``   — versão legível

Uso::

    from src.utils.reproducibility import Run

    with Run(modelo="logistic", parametros={"C": 1.0}) as r:
        ... treino ...
        r.metrica(auc=0.82, accuracy=0.78)
        r.anotar("split aleatorio estratificado")
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Any, Literal

from src.utils import config as C
from src.utils.storage import read_sha256

RUNS_DIR: Path = C.RUNS_DIR

Status = Literal["success", "error"]
_VERSOES_PACOTES = ("numpy", "pandas", "pyarrow", "scikit-learn", "scipy", "matplotlib", "seaborn")
_DATASET_TAMANHOS = ("n_rows", "train_rows", "valid_rows", "test_rows")


# ---------------------------------------------------------------------------
# Helpers de metadados
# ---------------------------------------------------------------------------

def _agora() -> dict[str, str]:
    utc = datetime.now(timezone.utc)
    return {
        "utc":   utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "local": utc.astimezone().strftime("%Y-%m-%dT%H:%M:%S%z"),
    }


def _coletar_gates() -> dict[str, str]:
    """Estado atual de cada gate em ``supervised.yaml`` como ``{nome: status}``."""
    gates = C.cfg("gates") or {}
    return {nome: (info or {}).get("status", "desconhecido") for nome, info in gates.items()}


def _versoes() -> dict[str, str | None]:
    """Versões das bibliotecas fundamentais e do Python."""
    resultado: dict[str, str | None] = {"python": platform.python_version()}
    for pacote in _VERSOES_PACOTES:
        try:
            resultado[pacote] = metadata.version(pacote)
        except metadata.PackageNotFoundError:
            resultado[pacote] = None
    return resultado


def _run_git(args: list[str]) -> str | None:
    """Corre ``git args`` em ``C.ROOT_DIR``; devolve stdout ou ``None``."""
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=C.ROOT_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError:
        return None
    return proc.stdout.strip() if proc.returncode == 0 else None


def _git_info() -> dict[str, str | bool | None]:
    """Commit, branch e estado da árvore de trabalho."""
    status = _run_git(["status", "--porcelain"])
    return {
        "commit": _run_git(["rev-parse", "HEAD"]),
        "branch": _run_git(["branch", "--show-current"]),
        "dirty":  bool(status) if status is not None else None,
    }


def _env_info() -> dict[str, str | bool]:
    """Informações não sensíveis do ambiente."""
    return {
        "python_executable": sys.executable,
        "python_version":    platform.python_version(),
        "platform":          platform.platform(),
        "cwd":               str(Path.cwd()),
        "ci":                bool(os.getenv("CI") or os.getenv("GITHUB_ACTIONS")),
    }


def _resolver_dataset_sha256(
    dataset_sha256: str | None,
    dataset_path: Path | None,
) -> str | None:
    """SHA-256 do dataset por prioridade: explícito > sidecar > ``None``.

    O sidecar é ``<dataset_path>.sha256`` (ver ``src.utils.storage``).
    """
    if dataset_sha256:
        return dataset_sha256
    if dataset_path is None:
        return None
    try:
        return read_sha256(Path(dataset_path))
    except OSError:
        return None


# ---------------------------------------------------------------------------
# summary.txt
# ---------------------------------------------------------------------------

def _bloco(titulo: str, itens: dict[str, Any], largura: int = 20) -> list[str]:
    """``titulo`` seguido de ``k: v`` alinhados — devolve linhas já vazias acima."""
    linhas = ["", f"{titulo}:"]
    for k, v in itens.items():
        if isinstance(v, float):
            linhas.append(f"  {k:{largura}s} {v:.4f}")
        else:
            linhas.append(f"  {k:{largura}s} {v}")
    return linhas


def _resumo(meta: dict[str, Any]) -> str:
    """``summary.txt`` curto e legível a partir do metadata."""
    linhas = [
        f"RUN_ID:   {meta['run_id']}",
        f"MODELO:   {meta['modelo']}",
        f"SEED:     {meta['seed']}",
        f"STATUS:   {meta.get('status', 'desconhecido')}",
    ]

    if meta.get("data_version"):
        linhas.append(f"DADOS:    {meta['data_version']}")
    if meta.get("dataset_sha256"):
        linhas.append(f"SHA-256:  {meta['dataset_sha256']}")

    ds = meta.get("dataset") or {}
    for k in _DATASET_TAMANHOS:
        if k in ds:
            linhas.append(f"{k.upper():10s} {ds[k]:,}")

    if meta.get("duracao_s") is not None:
        linhas.append(f"DURACAO:  {meta['duracao_s']:.1f}s")

    if meta.get("erro"):
        err = meta["erro"]
        linhas += ["", "ERRO:",
                   f"  tipo:     {err.get('tipo')}",
                   f"  mensagem: {err.get('mensagem')}"]

    if meta.get("metricas"):
        linhas += _bloco("MÉTRICAS", meta["metricas"])

    if meta.get("parametros"):
        linhas += _bloco("PARÂMETROS", meta["parametros"])

    if meta.get("gates"):
        linhas += _bloco("GATES", meta["gates"], largura=34)

    if meta.get("notas"):
        linhas += ["", f"NOTAS: {meta['notas']}"]

    linhas += ["", f"TIMESTAMP_UTC: {meta['timestamp']['utc']}"]
    return "\n".join(linhas) + "\n"


# ---------------------------------------------------------------------------
# API pública: gerar, registar, listar, carregar
# ---------------------------------------------------------------------------

def gerar_run_id(
    modelo: str | None = None,
    base_dir: Path | None = None,
) -> str:
    """Identificador único ``YYYY-MM-DD_HHMMSS_micros[_modelo]``.

    Com ``base_dir``, acrescenta sufixo ``_NN`` em caso de colisão no
    sistema de arquivos.
    """
    candidato = datetime.now().strftime("%Y-%m-%d_%H%M%S_%f")
    if modelo:
        candidato = f"{candidato}_{modelo}"
    if base_dir is None:
        return candidato

    base = Path(base_dir)
    run_id, contador = candidato, 1
    while (base / run_id).exists():
        run_id = f"{candidato}_{contador:02d}"
        contador += 1
    return run_id


def registrar_execucao(
    modelo: str,
    *,
    seed: int | None = None,
    parametros: dict[str, Any] | None = None,
    dataset: dict[str, Any] | None = None,
    features: dict[str, Any] | None = None,
    metricas: dict[str, Any] | None = None,
    duracao_s: float | None = None,
    notas: str | None = None,
    run_id: str | None = None,
    output_dir: Path | None = None,
    status: Status = "success",
    erro: dict[str, Any] | None = None,
    dataset_sha256: str | None = None,
) -> Path:
    """Grava ``metadata.json`` + ``summary.txt`` em ``outputs/runs/<RUN_ID>/``.

    ``status='error'`` deve vir acompanhado de ``erro`` (dict com ``tipo``,
    ``mensagem`` e opcionalmente ``traceback``). ``dataset_sha256=None``
    deixa a chave ausente do metadata.
    """
    base = Path(output_dir) if output_dir is not None else RUNS_DIR
    if run_id is None:
        run_id = gerar_run_id(modelo=modelo, base_dir=base)

    pasta = base / run_id
    pasta.mkdir(parents=True, exist_ok=False)

    meta: dict[str, Any] = {
        "run_id":         pasta.name,
        "timestamp":      _agora(),
        "modelo":         modelo,
        "seed":           seed if seed is not None else C.SEED,
        "status":         status,
        "erro":           erro,
        "duracao_s":      duracao_s,
        "parametros":     parametros or {},
        "dataset":        dataset or {},
        "dataset_sha256": dataset_sha256,
        "data_version":   C.DATA_VERSION,
        "features":       features or {},
        "metricas":       metricas or {},
        "gates":          _coletar_gates(),
        "notas":          notas,
        "versoes":        _versoes(),
        "git":            _git_info(),
        "env":            _env_info(),
        "supervised_yaml_sha256": C.supervised_yaml_sha256(),
    }

    (pasta / "metadata.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    (pasta / "summary.txt").write_text(_resumo(meta), encoding="utf-8")

    print(f"[reproducibility] run registrado em: {pasta}")
    return pasta


def listar_runs(output_dir: Path | None = None) -> list[dict[str, Any]]:
    """Metadados das execuções registadas, ordenados por ``run_id`` decrescente.

    Cada item inclui ``"pasta"`` com o caminho absoluto.
    """
    raiz = Path(output_dir) if output_dir is not None else RUNS_DIR
    if not raiz.exists():
        return []

    runs: list[dict[str, Any]] = []
    for pasta in raiz.iterdir():
        if not pasta.is_dir():
            continue
        meta_path = pasta / "metadata.json"
        if not meta_path.exists():
            continue
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        meta["pasta"] = str(pasta)
        runs.append(meta)

    return sorted(runs, key=lambda m: str(m.get("run_id", "")), reverse=True)


def carregar_run(
    run: str | Path,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Carrega o ``metadata.json`` de uma execução."""
    caminho = Path(run)
    if not caminho.is_absolute():
        caminho = (Path(output_dir) if output_dir else RUNS_DIR) / caminho

    meta_path = caminho / "metadata.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"metadata.json não encontrado em {caminho}")
    return json.loads(meta_path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------

class Run:
    """Context manager de registo de execução.

    O metadata é gravado sempre ao sair do bloco, inclusive em caso de
    excepção (com ``status="error"`` e ``erro`` estruturado). A excepção
    não é suprimida — ``__exit__`` devolve ``False``.
    """

    def __init__(
        self,
        modelo: str,
        *,
        seed: int | None = None,
        parametros: dict[str, Any] | None = None,
        dataset: dict[str, Any] | None = None,
        features: dict[str, Any] | None = None,
        notas: str | None = None,
        output_dir: Path | None = None,
        dataset_path: Path | None = None,
        dataset_sha256: str | None = None,
    ) -> None:
        self.modelo         = modelo
        self.seed           = seed
        self.parametros     = dict(parametros or {})
        self.dataset        = dict(dataset or {})
        self.features       = dict(features or {})
        self.notas          = notas
        self.output_dir     = output_dir
        self.dataset_path   = dataset_path
        self.dataset_sha256 = dataset_sha256
        self._metricas: dict[str, Any] = {}
        self._inicio: float | None = None
        self.pasta: Path | None = None

    def metrica(self, **kwargs: Any) -> "Run":
        self._metricas.update(kwargs)
        return self

    def anotar(self, texto: str) -> "Run":
        self.notas = f"{self.notas}\n{texto}" if self.notas else texto
        return self

    def add_dataset(self, **kwargs: Any) -> "Run":
        self.dataset.update(kwargs)
        return self

    def __enter__(self) -> "Run":
        self._inicio = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        duracao = time.perf_counter() - self._inicio if self._inicio else None

        if exc_type is None:
            status: Status = "success"
            erro: dict[str, Any] | None = None
        else:
            status = "error"
            erro = {
                "tipo":      exc_type.__name__,
                "modulo":    getattr(exc_type, "__module__", None),
                "mensagem":  str(exc) if exc is not None else None,
                "traceback": (
                    "".join(traceback.format_exception(exc_type, exc, tb))
                    if tb is not None else None
                ),
            }

        self.pasta = registrar_execucao(
            modelo=self.modelo,
            seed=self.seed,
            parametros=self.parametros,
            dataset=self.dataset,
            features=self.features,
            metricas=self._metricas,
            duracao_s=duracao,
            notas=self.notas,
            output_dir=self.output_dir,
            status=status,
            erro=erro,
            dataset_sha256=_resolver_dataset_sha256(self.dataset_sha256, self.dataset_path),
        )
        return False
```

## `src/utils/storage.py`

- Git: `tracked` · status `clean`
- Size: `8.8 KB` · modified `2026-10-16 14:54 UTC`
- SHA-256: `05b2bbcc41102e5028f55a7cc665d49df4b25eca58f050f77a004b74e20dc724`

```python
"""
Contrato oficial de acesso ao Parquet de SRAG.

Fluxo: ``GitHub Release → data/processed/<DATA_VERSION>/srag.parquet``.

Tenta o download público via release; se falhar e houver ``GITHUB_TOKEN``,
usa o asset privado via API do GitHub. Grava um sidecar ``<arquivo>.sha256``
para reprodutibilidade. ``force=True`` rebaixa e descarta o sidecar antigo.
"""

from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Iterable

import pandas as pd
import requests

from src.utils import config as C
from src.utils.env import PROCESSED, get_secret


PARQUET_MAGIC: bytes = b"PAR1"
_CHUNK: int = 8 * 1024 * 1024


def _token() -> str | None:
    """``GITHUB_TOKEN`` se definido; caso contrário, ``None``."""
    return get_secret("GITHUB_TOKEN", obrigatorio=False)


def sha256_path(parquet_path: Path) -> Path:
    """Caminho do sidecar ``.sha256`` associado a um Parquet."""
    return parquet_path.with_suffix(parquet_path.suffix + ".sha256")


def read_sha256(parquet_path: Path) -> str | None:
    """Lê o SHA-256 do sidecar, ou ``None`` se ele não existir."""
    sidecar = sha256_path(parquet_path)
    if not sidecar.exists():
        return None
    linha = sidecar.read_text(encoding="utf-8").strip()
    return linha.split()[0] if linha else None


def _abrir_stream(
    url: str,
    *,
    headers: dict[str, str] | None,
    tentativas: int,
    backoff: float,
    timeout: float,
) -> requests.Response:
    """Abre um stream HTTP com retry linear.

    4xx permanente (exceto 429) falha sem retentar. 5xx, 429 e erros de
    conexão são retentados até ``tentativas`` vezes, com espera
    ``backoff * tentativa`` entre elas.
    """
    last_exc: Exception | None = None

    for tentativa in range(1, tentativas + 1):
        try:
            r = requests.get(
                url,
                headers=headers or {},
                stream=True,
                timeout=timeout,
                allow_redirects=True,
            )
        except requests.RequestException as exc:
            last_exc = exc
            if tentativa < tentativas:
                time.sleep(backoff * tentativa)
            continue

        if r.ok:
            return r

        # 4xx permanente (excepto 429): falha sem retentar.
        if 400 <= r.status_code < 500 and r.status_code != 429:
            r.close()
            r.raise_for_status()

        status = r.status_code
        r.close()
        last_exc = requests.HTTPError(f"HTTP {status} em {url}")
        if tentativa < tentativas:
            time.sleep(backoff * tentativa)

    if last_exc is None:
        raise RuntimeError(f"Nenhuma tentativa executada para {url}")
    raise last_exc


def _baixar_para_part(
    r: requests.Response,
    tmp: Path,
) -> tuple[str, bytes]:
    """Streama ``r`` para ``tmp``; devolve ``(sha256_hex, primeiros_16_bytes)``.

    Imprime progresso quando o servidor declara ``content-length``.
    """
    h = hashlib.sha256()
    first = b""
    total = int(r.headers.get("content-length", 0))
    done = 0

    with open(tmp, "wb") as f:
        for chunk in r.iter_content(_CHUNK):
            if not chunk:
                continue
            if not first:
                first = chunk[:16]
            f.write(chunk)
            h.update(chunk)
            done += len(chunk)
            if total:
                print(
                    f"\rBaixando: {done / 1e6:.0f}/{total / 1e6:.0f} MB",
                    end="",
                    flush=True,
                )

    if total:
        print()
    return h.hexdigest(), first


def download_file(
    url: str,
    dest: Path,
    *,
    headers: dict[str, str] | None = None,
    expected_magic: bytes | None = None,
    expected_sha256: str | None = None,
) -> str:
    """Baixa ``url`` para ``dest`` com verificação de magic bytes e SHA-256.

    Retorna o SHA-256 hex e grava o sidecar ``<dest>.sha256``. O download
    passa por ``<dest>.part``, removido em qualquer falha. Levanta
    ``RuntimeError`` se o content-type indicar HTML/JSON, se o magic não
    bater ou se o SHA-256 divergir.
    """
    tmp = dest.with_suffix(dest.suffix + ".part")
    tmp.unlink(missing_ok=True)

    r = _abrir_stream(
        url,
        headers=headers,
        tentativas=C.HTTP_TENTATIVAS,
        backoff=C.HTTP_BACKOFF,
        timeout=C.HTTP_TIMEOUT,
    )
    try:
        ctype = r.headers.get("content-type", "").lower()
        if "text/html" in ctype or "application/json" in ctype:
            preview = next(r.iter_content(256), b"")
            raise RuntimeError(
                f"Download retornou {ctype!r} em vez de binário. "
                f"URL: {url}\nPrimeiros bytes: {preview[:80]!r}"
            )
        digest, first_bytes = _baixar_para_part(r, tmp)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
    finally:
        r.close()

    if expected_magic and not first_bytes.startswith(expected_magic):
        tmp.unlink(missing_ok=True)
        raise RuntimeError(
            f"Arquivo baixado não é válido. Esperado começar com "
            f"{expected_magic!r}, recebido {first_bytes!r}. URL: {url}"
        )

    if expected_sha256 and digest.lower() != expected_sha256.lower():
        tmp.unlink(missing_ok=True)
        raise RuntimeError(
            f"SHA-256 divergente para {url}.\n"
            f"  esperado: {expected_sha256}\n"
            f"  obtido:   {digest}"
        )

    tmp.replace(dest)
    sha256_path(dest).write_text(f"{digest}  {dest.name}\n", encoding="utf-8")
    return digest


def _private_asset_url(token: str) -> str:
    """URL do asset Parquet via API do GitHub (repositório privado)."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    url = (
        f"https://api.github.com/repos/{C.GITHUB_REPO}/releases/tags/"
        f"{C.DATA_VERSION}"
    )
    r = requests.get(url, headers=headers, timeout=C.HTTP_TIMEOUT)
    r.raise_for_status()

    assets = r.json().get("assets", [])
    asset = next((a for a in assets if a["name"] == C.PARQUET_NAME), None)
    if asset is None:
        nomes = [a["name"] for a in assets]
        raise RuntimeError(
            f"Asset {C.PARQUET_NAME!r} não encontrado na release "
            f"{C.DATA_VERSION!r}. Disponíveis: {nomes}"
        )
    return asset["url"]


def get_parquet(
    force: bool = False,
    *,
    expected_sha256: str | None = None,
) -> Path:
    """Devolve o caminho local do Parquet de SRAG, baixando se necessário.

    Ordem: release pública; se falhar e ``GITHUB_TOKEN`` estiver definido,
    asset privado via API. ``force=True`` rebaixa mesmo que o arquivo
    exista e descarta o sidecar antigo. ``expected_sha256`` valida o hash
    do arquivo baixado.

    Efeito colateral: Parquet gravado em
    ``data/processed/<DATA_VERSION>/<PARQUET_NAME>``, sidecar ``.sha256``
    ao lado, e SHA-256 impresso no stdout.
    """
    folder = PROCESSED / C.DATA_VERSION
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / C.PARQUET_NAME

    if path.exists() and not force:
        return path

    if force and path.exists():
        path.unlink()
        sha256_path(path).unlink(missing_ok=True)

    public_url = (
        f"https://github.com/{C.GITHUB_REPO}/releases/download/"
        f"{C.DATA_VERSION}/{C.PARQUET_NAME}"
    )

    try:
        digest = download_file(
            public_url,
            path,
            expected_magic=PARQUET_MAGIC,
            expected_sha256=expected_sha256,
        )
    except (requests.HTTPError, RuntimeError):
        token = _token()
        if not token:
            raise RuntimeError(
                "Download falhou. Repositório privado ou asset inválido? "
                "Cadastre o segredo GITHUB_TOKEN."
            )
        digest = download_file(
            _private_asset_url(token),
            path,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/octet-stream",
            },
            expected_magic=PARQUET_MAGIC,
            expected_sha256=expected_sha256,
        )

    print(f"[storage] SHA-256: {digest}")
    return path


def read_srag(
    columns: Iterable[str] | None = None,
    filters: list[tuple] | None = None,
) -> pd.DataFrame:
    """Lê o Parquet de SRAG como DataFrame.

    ``columns`` restringe o subconjunto carregado (pushdown do Parquet);
    ``filters`` segue o formato de ``pd.read_parquet(filters=...)``.
    """
    return pd.read_parquet(
        get_parquet(),
        columns=list(columns) if columns is not None else None,
        filters=filters,
    )
```

## `tests/conftest.py`

- Git: `tracked` · status `clean`
- Size: `639 B` · modified `2026-10-16 14:54 UTC`
- SHA-256: `d09e0a36c305a02829b974b59774ccf94a97163357a9f419d17ec98e22a5d549`

```python
"""Fixtures partilhadas entre testes."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.utils import config as C


@pytest.fixture(scope="session")
def parquet_disponivel() -> Path | None:
    """Parquet processado, ou ``None`` se ainda não foi gerado.

    Fixture de sessão — o path é calculado uma vez por execução. Testes
    que dependem dela devem fazer ``pytest.skip()`` quando o retorno é
    ``None`` (o Parquet não vem versionado no Git).
    """
    caminho = C.PROCESSED_DIR / C.DATA_VERSION / C.PARQUET_NAME
    return caminho if caminho.is_file() else None
```

## `tests/test_calibration.py`

- Git: `tracked` · status `clean`
- Size: `3.5 KB` · modified `2026-10-16 14:54 UTC`
- SHA-256: `993b7617cdacd34f6659bdf2b40134f6a21a79b3af9fc7c9d12c44a642bfeca5`

```python
"""Testes de calibração e escolha de limiar."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

from src.models.calibration import calibrar, escolher_limiar


@pytest.fixture
def dados_limiar() -> tuple[np.ndarray, np.ndarray]:
    """10 amostras balanceadas — y_true binário, y_prob em [0, 1]."""
    y = np.array([0, 0, 1, 1, 1, 0, 1, 0, 1, 1])
    p = np.array([0.1, 0.2, 0.8, 0.9, 0.6, 0.3, 0.7, 0.4, 0.85, 0.75])
    return y, p


@pytest.fixture
def modelo_ajustado() -> tuple[LogisticRegression, pd.DataFrame, pd.Series]:
    """``LogisticRegression`` ajustado em ``X`` 1D sintético com sinal.

    Fixture separada (não por teste) para que múltiplos testes de calibração
    reutilizem o mesmo modelo — o objecto é imutável após ``fit``.
    """
    pytest.importorskip("sklearn.frozen")
    rng = np.random.RandomState(0)
    X = pd.DataFrame({"a": rng.randn(200)})
    y = pd.Series((X["a"] + rng.randn(200) * 0.1 > 0).astype(int))
    return LogisticRegression().fit(X, y), X, y


# ---------------------------------------------------------------------------
# escolher_limiar
# ---------------------------------------------------------------------------

def test_escolher_limiar_retorna_dict(dados_limiar):
    y, p = dados_limiar
    r = escolher_limiar(y, p, metrica="f1")
    assert {"limiar", "valor", "metrica", "auc", "brier", "tabela"} <= set(r)
    assert r["metrica"] == "f1"
    assert 0 < r["limiar"] < 1


def test_escolher_limiar_metrica_invalida(dados_limiar):
    y, p = dados_limiar
    # Metrica não existe no Literal — passagem intencional de valor inválido.
    with pytest.raises(ValueError, match="metrica inválida"):
        escolher_limiar(y, p, metrica="nao_existe")  # type: ignore[arg-type]


def test_escolher_limiar_min_precision_respeitado():
    y = np.array([0, 0, 1, 1])
    p = np.array([0.1, 0.2, 0.8, 0.9])
    r = escolher_limiar(y, p, metrica="recall", min_precision=0.9)
    linha = r["tabela"][r["tabela"]["limiar"] == r["limiar"]]
    assert linha["precision"].iloc[0] >= 0.9


def test_escolher_limiar_min_precision_impossivel():
    y = np.array([1, 0, 0, 0])
    p = np.array([0.1, 0.9, 0.8, 0.85])
    with pytest.raises(ValueError, match="precision"):
        escolher_limiar(y, p, min_precision=0.5)


# ---------------------------------------------------------------------------
# calibrar
# ---------------------------------------------------------------------------

def test_calibrar_metodo_invalido(modelo_ajustado):
    modelo, X, y = modelo_ajustado
    with pytest.raises(ValueError, match="method inválido"):
        calibrar(modelo, X, y, method="nao_existe")  # type: ignore[arg-type]


def test_calibrar_sigmoid_preserva_shape(modelo_ajustado):
    modelo, X, y = modelo_ajustado
    cal = calibrar(modelo, X, y, method="sigmoid")
    proba = cal.predict_proba(X)
    assert proba.shape == (len(X), 2)
    assert np.allclose(proba.sum(axis=1), 1.0)
    assert np.all((proba >= 0) & (proba <= 1))


def test_calibrar_isotonic_preserva_shape():
    pytest.importorskip("sklearn.frozen")
    rng = np.random.RandomState(1)
    X = pd.DataFrame({"a": rng.randn(500)})
    y = pd.Series((X["a"] > 0).astype(int))
    modelo = LogisticRegression().fit(X, y)

    cal = calibrar(modelo, X, y, method="isotonic")
    assert cal.predict_proba(X).shape == (len(X), 2)
```

## `tests/test_cohort_source.py`

- Git: `tracked` · status `clean`
- Size: `6.1 KB` · modified `2026-10-18 16:01 UTC`
- SHA-256: `ebf7038acc9f8e0ad20dac6fb32ab9267f9863874423af60850c4433970b0dbc`

```python
"""Testes do resolvedor de coorte (provisória, final, auto, explicit_path).

Cobrem:
- descoberta automática por ``kind`` e fallback dentro da família provisória;
- ``auto`` preferindo a final e caindo em provisional quando só ela existe;
- validação de ``explicit_path`` (nome canônico + coerência com ``kind``);
- regressão da #30: ``coorte.parquet`` não é mais engolido como provisório.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.data.cohort_source import (
    cohort_candidates,
    load_cohort,
    resolve_cohort_path,
)


# ---------------------------------------------------------------------------
# Fixtures e helpers
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _sem_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    """Limpa ``SRAG_COHORT_KIND`` do ambiente antes de cada teste.

    Sem isto, um ``SRAG_COHORT_KIND`` definido no shell do runner
    tornaria os testes dependentes do estado local.
    """
    monkeypatch.delenv("SRAG_COHORT_KIND", raising=False)


def _write(path: Path, value: int) -> None:
    """Grava um Parquet 1×1 com uma única coluna ``value``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"value": [value]}).to_parquet(path, index=False)


# ---------------------------------------------------------------------------
# Descoberta automática por kind
# ---------------------------------------------------------------------------

def test_padrao_permanece_provisorio(tmp_path: Path) -> None:
    """Sem ``kind``, o padrão é ``provisional``, mesmo com a final presente.

    Quando ``coorte_provisoria.parquet`` não existe, o resolver cai no
    próximo candidato provisório (``coorte_provisoria_b.parquet``).
    """
    paths = cohort_candidates(tmp_path)
    _write(paths["provisional"][1], 1)   # coorte_provisoria_b.parquet
    _write(paths["final"][0], 2)         # coorte_final.parquet (não é o default)

    kind, path = resolve_cohort_path(tmp_path)

    assert kind == "provisional"
    assert path.name == "coorte_provisoria_b.parquet"


def test_final_exige_escolha_explicita(tmp_path: Path) -> None:
    """Só existe a coorte final; sem ``kind`` a busca falha em vez de devolvê-la."""
    path = cohort_candidates(tmp_path)["final"][0]
    _write(path, 2)

    with pytest.raises(FileNotFoundError, match="provisional"):
        resolve_cohort_path(tmp_path)

    frame, source = load_cohort(tmp_path, kind="final")

    assert frame["value"].tolist() == [2]
    assert source.kind == "final"
    assert source.rows == 1
    assert len(source.sha256) == 64


def test_auto_prefere_final(tmp_path: Path) -> None:
    paths = cohort_candidates(tmp_path)
    _write(paths["provisional"][0], 1)
    _write(paths["final"][0], 2)

    kind, path = resolve_cohort_path(tmp_path, kind="auto")

    assert kind == "final"
    assert path.name == "coorte_final.parquet"


def test_auto_cai_em_provisional_quando_so_ela_existe(tmp_path: Path) -> None:
    """``auto`` só prefere a final quando ela existe; senão usa a provisória."""
    paths = cohort_candidates(tmp_path)
    _write(paths["provisional"][0], 1)

    kind, path = resolve_cohort_path(tmp_path, kind="auto")

    assert kind == "provisional"
    assert path.name == "coorte_provisoria.parquet"


def test_tipo_invalido_falha(tmp_path: Path) -> None:
    # Valor viola intencionalmente o Literal CohortKind.
    with pytest.raises(ValueError, match="provisional, final ou auto"):
        resolve_cohort_path(tmp_path, kind="desconhecida")  # type: ignore[arg-type]


def test_nenhum_candidato_falha(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Nenhuma coorte"):
        resolve_cohort_path(tmp_path, kind="provisional")


# ---------------------------------------------------------------------------
# Regressão da #30: nomes ambíguos não são mais aceitos
# ---------------------------------------------------------------------------

def test_coorte_parquet_nao_e_mais_candidato(tmp_path: Path) -> None:
    """``coorte.parquet`` não deve ser engolido como provisório (regressão #30)."""
    _write(tmp_path / "data" / "analytical" / "coorte.parquet", 2)

    with pytest.raises(FileNotFoundError):
        resolve_cohort_path(tmp_path, kind="provisional")


# ---------------------------------------------------------------------------
# explicit_path: nome canônico + coerência com `kind`
# ---------------------------------------------------------------------------

def test_explicit_path_sem_kind_usa_nome(tmp_path: Path) -> None:
    path = cohort_candidates(tmp_path)["final"][0]
    _write(path, 2)

    kind, resolved = resolve_cohort_path(tmp_path, explicit_path=path)

    assert kind == "final"
    assert resolved.name == "coorte_final.parquet"


def test_explicit_path_com_kind_consistente_ok(tmp_path: Path) -> None:
    path = cohort_candidates(tmp_path)["final"][0]
    _write(path, 2)

    kind, resolved = resolve_cohort_path(tmp_path, kind="final", explicit_path=path)

    assert kind == "final"
    assert resolved.name == "coorte_final.parquet"


def test_explicit_path_com_kind_conflitante_falha(tmp_path: Path) -> None:
    """Coorte final passada como ``provisional`` → falha em vez de mascarar o tipo."""
    path = cohort_candidates(tmp_path)["final"][0]
    _write(path, 2)

    with pytest.raises(ValueError, match="classificada como"):
        resolve_cohort_path(tmp_path, kind="provisional", explicit_path=path)


def test_explicit_path_com_nome_desconhecido_falha(tmp_path: Path) -> None:
    path = tmp_path / "coorte_definitiva.parquet"
    _write(path, 2)

    with pytest.raises(ValueError, match="Nome de coorte não reconhecido"):
        resolve_cohort_path(tmp_path, explicit_path=path)


def test_explicit_path_inexistente_falha(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Coorte explícita"):
        resolve_cohort_path(tmp_path, explicit_path=tmp_path / "nao_existe.parquet")
```

## `tests/test_config.py`

- Git: `tracked` · status `clean`
- Size: `7.4 KB` · modified `2026-10-16 14:54 UTC`
- SHA-256: `e9d6278318474900c708013ab29c1eaa30ed96c935b7a320868c01924ef7c5ca`

```python
"""Integridade do ambiente e da configuração do projeto."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.utils import config as C
from src.utils import env


def _url_parquet_esperada() -> str:
    """URL canônica do Parquet na release pública."""
    return (
        f"https://github.com/{C.GITHUB_REPO}/releases/download/"
        f"{C.DATA_VERSION}/{C.PARQUET_NAME}"
    )


# ---------------------------------------------------------------------------
# Raiz e diretórios
# ---------------------------------------------------------------------------

def test_root_dir_existe() -> None:
    assert C.ROOT_DIR.exists()
    assert C.ROOT_DIR.is_dir()


def test_root_dir_calculado_a_partir_do_arquivo() -> None:
    """``ROOT_DIR`` deriva de ``config.py`` (dois níveis acima: ``src/utils/``)."""
    assert C.ROOT_DIR == Path(C.__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "chave",
    ["DATA_DIR", "RAW_DIR", "PROCESSED_DIR", "REPORTS_DIR", "MODELS_DIR"],
)
def test_diretorios_derivam_da_raiz(chave: str) -> None:
    """Diretórios públicos derivam de ``ROOT_DIR``.

    O clone pode estar em ``C:/Users`` ou ``OneDrive`` — o que não pode
    é o caminho estar literalmente gravado em ``config.py``.
    """
    valor = getattr(C, chave)
    assert isinstance(valor, Path)
    assert valor.is_absolute()
    assert C.ROOT_DIR in valor.parents, f"{chave}={valor} não deriva de {C.ROOT_DIR}"


# ---------------------------------------------------------------------------
# Sem caminhos pessoais hardcoded
# ---------------------------------------------------------------------------

def _encontrar_caminhos_hardcoded(fonte: str, nomes_de_caminho: set[str]) -> list[dict]:
    """Inspeciona atribuições de ``nomes_de_caminho`` à procura de caminhos pessoais.

    Só atribuições são olhadas — comentários, docstrings e mensagens podem
    mencionar ``C:/Users`` ou ``/home`` sem serem configuração real.
    """
    proibidos = ("c:/users/", "/home/", "/users/")
    problemas: list[dict] = []

    for no in ast.walk(ast.parse(fonte)):
        if isinstance(no, ast.Assign) and len(no.targets) == 1:
            alvo, valor = no.targets[0], no.value
        elif isinstance(no, ast.AnnAssign):
            alvo, valor = no.target, no.value
        else:
            continue

        if valor is None or not isinstance(alvo, ast.Name) or alvo.id not in nomes_de_caminho:
            continue

        for item in ast.walk(valor):
            if not isinstance(item, ast.Constant) or not isinstance(item.value, str):
                continue
            texto = item.value.replace("\\", "/").lower()
            if termos := [t for t in proibidos if t in texto]:
                problemas.append({"constante": alvo.id, "valor": item.value, "termos": termos})

    return problemas


def test_config_nao_contem_caminho_pessoal_hardcoded() -> None:
    """Nenhuma constante de caminho em ``config.py`` tem caminho pessoal literal."""
    nomes_de_caminho = {
        "ROOT_DIR", "DATA_DIR", "RAW_DIR", "PROCESSED_DIR",
        "TREINO_DIR", "CONFIGS_DIR", "MODELS_DIR", "OUTPUTS_DIR",
        "RUNS_DIR", "LOGS_DIR", "REPORTS_DIR", "FIGURES_DIR",
        "TABLES_DIR", "PREDICTIONS_DIR", "SUPERVISED_YAML",
    }
    fonte = Path(C.__file__).read_text(encoding="utf-8")

    problemas = _encontrar_caminhos_hardcoded(fonte, nomes_de_caminho)
    assert not problemas, f"Caminhos pessoais hardcoded em constantes: {problemas}"


# ---------------------------------------------------------------------------
# Seed, versão e HTTP
# ---------------------------------------------------------------------------

def test_seed_definido() -> None:
    assert isinstance(C.SEED, int)
    assert C.SEED == 42


def test_random_state_igual_ao_seed() -> None:
    assert C.RANDOM_STATE == C.SEED


def test_repo_definido() -> None:
    assert C.GITHUB_REPO and "/" in C.GITHUB_REPO


def test_data_version_e_parquet_definidos() -> None:
    assert C.DATA_VERSION
    assert C.PARQUET_NAME.endswith(".parquet")


def test_parametros_http_razoaveis() -> None:
    assert C.HTTP_TIMEOUT > 0
    assert C.HTTP_TENTATIVAS >= 1
    assert C.HTTP_BACKOFF >= 0


# ---------------------------------------------------------------------------
# URL do Parquet — prioridade da variável de ambiente
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "valor_env, esperado_override",
    [
        (None, False),
        ("https://example.org/dados/srag_teste.parquet", True),
        ("   ", False),
    ],
    ids=["sem_env", "env_customizada", "env_vazia"],
)
def test_srag_parquet_url(valor_env, esperado_override, monkeypatch: pytest.MonkeyPatch) -> None:
    """``SRAG_PARQUET_URL`` sobrepõe a URL padrão; vazia cai no padrão."""
    if valor_env is None:
        monkeypatch.delenv("SRAG_PARQUET_URL", raising=False)
    else:
        monkeypatch.setenv("SRAG_PARQUET_URL", valor_env)

    url = C.srag_parquet_url()
    if esperado_override:
        assert valor_env is not None
        assert url == valor_env.strip()
    else:
        assert url == _url_parquet_esperada()


# ---------------------------------------------------------------------------
# env.py
# ---------------------------------------------------------------------------

def test_env_aponta_para_mesma_raiz() -> None:
    assert env.ROOT == C.ROOT_DIR


def test_env_diretorios_padrao_existem() -> None:
    env.garantir_diretorios()
    for caminho in (env.RAW, env.PROCESSED, env.TREINO, env.FIGURES):
        assert caminho.is_dir(), f"{caminho} não é diretório após garantir_diretorios()"


def test_env_resumo_nao_quebra() -> None:
    texto = env.resumo()
    assert "ROOT_DIR" in texto
    assert "ENV" in texto


def test_get_secret_obrigatorio_levanta_erro(monkeypatch: pytest.MonkeyPatch) -> None:
    nome = "VAR_QUE_NAO_EXISTE_XYZ"
    monkeypatch.delenv(nome, raising=False)
    with pytest.raises(RuntimeError, match=nome):
        env.get_secret(nome)


def test_get_secret_opcional_retorna_none(monkeypatch: pytest.MonkeyPatch) -> None:
    nome = "VAR_OPCIONAL_XYZ"
    monkeypatch.delenv(nome, raising=False)
    assert env.get_secret(nome, obrigatorio=False) is None


# ---------------------------------------------------------------------------
# Schema do Parquet (slow)
# ---------------------------------------------------------------------------

@pytest.mark.slow
def test_features_finais_existem_no_schema(parquet_disponivel) -> None:
    """Colunas do ``supervised.yaml`` existem no Parquet (ou são derivadas).

    Features derivadas (produzidas por ``montar_features``) não existem no
    Parquet bruto — excluídas da checagem. As colunas de entrada exigidas
    pela derivação são verificadas explicitamente.
    """
    if parquet_disponivel is None:
        pytest.skip("Parquet não disponível.")

    import pyarrow.parquet as pq
    from src.models import pipeline

    colunas = set(pq.read_schema(parquet_disponivel).names)
    derivadas = set(C.cfg("features", "engenharia", "derivadas") or [])
    entradas = set(C.cfg("features", "engenharia", "entradas") or [])
    base = set(pipeline.FEATURES) - derivadas

    faltando = (base | entradas) - colunas
    assert not faltando, f"Colunas ausentes no Parquet: {sorted(faltando)}"
```

## `tests/test_errors.py`

- Git: `tracked` · status `clean`
- Size: `5.5 KB` · modified `2026-10-16 14:54 UTC`
- SHA-256: `7c4362c964cc4035939c32264b33a4e27cff1abf1cb40979616c1e8b55479164`

```python
"""Testes de análise de erros em ``src.evaluation.errors``."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.evaluation.errors import (
    extrair_falsos_negativos,
    extrair_falsos_positivos,
    matriz_confusao,
    metricas_por_grupo,
    top_erros,
)


@pytest.fixture
def y_true_y_pred() -> tuple[np.ndarray, np.ndarray]:
    """8 amostras com falsos positivos e negativos plantados.

    Labels (não probabilidades) — para ``top_erros``, cada teste constrói
    os seus próprios dados.
    """
    y_true = np.array([0, 0, 1, 1, 0, 1, 0, 1])
    y_pred = np.array([0, 1, 1, 0, 0, 1, 1, 1])
    return y_true, y_pred


def _df_com_indice(n: int) -> pd.DataFrame:
    """DataFrame ``{"x": range(n)}`` — índice rastreável nos testes de extração."""
    return pd.DataFrame({"x": range(n)})


# ---------------------------------------------------------------------------
# matriz_confusao
# ---------------------------------------------------------------------------

def test_matriz_confusao_shape_e_valores(y_true_y_pred) -> None:
    y_true, y_pred = y_true_y_pred
    m = matriz_confusao(y_true, y_pred)
    assert {"pred_0", "pred_1"}.issubset(m.columns)
    assert {"real_0", "real_1"}.issubset(m.index)
    assert m.loc["real_0", "pred_1"] == 2
    assert m.loc["real_1", "pred_0"] == 1


def test_matriz_confusao_tem_totais(y_true_y_pred) -> None:
    y_true, y_pred = y_true_y_pred
    m = matriz_confusao(y_true, y_pred)
    assert "total" in m.columns
    assert "total" in m.index
    assert m.loc["total", "total"] == len(y_true)


# ---------------------------------------------------------------------------
# extrair_falsos_*
# ---------------------------------------------------------------------------

def test_extrair_fp(y_true_y_pred) -> None:
    y_true, y_pred = y_true_y_pred
    fp = extrair_falsos_positivos(_df_com_indice(len(y_true)), y_true, y_pred)
    assert len(fp) == 2
    assert set(fp["x"]) == {1, 6}


def test_extrair_fn(y_true_y_pred) -> None:
    y_true, y_pred = y_true_y_pred
    fn = extrair_falsos_negativos(_df_com_indice(len(y_true)), y_true, y_pred)
    assert len(fn) == 1
    assert fn["x"].iloc[0] == 3


# ---------------------------------------------------------------------------
# metricas_por_grupo
# ---------------------------------------------------------------------------

def test_metricas_por_grupo_coluna_renomeada() -> None:
    """A coluna de prevalência chama-se ``taxa_positivos``, não ``positivos``."""
    n = 300
    df = pd.DataFrame({"grupo": ["A"] * n + ["B"] * n})
    y = pd.Series(np.tile([0, 1], n))
    p = pd.Series(np.tile([0.1, 0.9], n))

    r = metricas_por_grupo(df, y, p, "grupo", min_n=10)
    assert "taxa_positivos" in r.columns
    assert "positivos" not in r.columns


def test_metricas_por_grupo_ignora_abaixo_de_min_n() -> None:
    """Grupo com menos de ``min_n`` é excluído do resultado."""
    df = pd.DataFrame({"grupo": ["A"] * 5 + ["B"] * 300})
    y = pd.Series([0, 1] * 152 + [0])
    p = pd.Series([0.1, 0.9] * 152 + [0.5])

    r = metricas_por_grupo(df, y, p, "grupo", min_n=30)
    assert set(r["grupo"]) == {"B"}
    assert r.loc[r["grupo"] == "B", "n"].iloc[0] == 300


def test_metricas_por_grupo_coluna_ausente() -> None:
    df = pd.DataFrame({"outra": [1, 2]})
    with pytest.raises(KeyError):
        metricas_por_grupo(df, np.array([0, 1]), np.array([0.1, 0.9]), "grupo")


def test_metricas_por_grupo_tamanho_incompativel() -> None:
    """``df`` (5 linhas) com ``y`` (6 linhas) deve falhar antes de agregar."""
    df = pd.DataFrame({"grupo": ["A"] * 5})
    y = np.array([0, 1, 0, 1, 0, 1])
    p = np.array([0.1, 0.9, 0.2, 0.8, 0.3, 0.7])
    with pytest.raises(ValueError):
        metricas_por_grupo(df, y, p, "grupo")


# ---------------------------------------------------------------------------
# top_erros
# ---------------------------------------------------------------------------

def test_top_erros_erro_absoluto() -> None:
    """Adiciona ``y_true``, ``y_prob``, ``y_pred``, ``erro_abs`` ao DataFrame."""
    df = pd.DataFrame({"x": range(6)})
    y_true = np.array([0, 0, 1, 1, 0, 1])
    y_prob = np.array([0.1, 0.9, 0.1, 0.9, 0.5, 0.5])

    t = top_erros(df, y_true, y_prob, n=3, criterio="erro_absoluto")
    assert len(t) == 3
    for c in ("y_true", "y_prob", "y_pred", "erro_abs"):
        assert c in t.columns


def test_top_erros_fp_ordena_por_prob_decrescente() -> None:
    df = pd.DataFrame({"x": range(5)})
    y_true = np.array([0, 0, 1, 1, 0])
    y_prob = np.array([0.1, 0.9, 0.1, 0.9, 0.6])

    t = top_erros(df, y_true, y_prob, n=5, criterio="fp")
    assert (t["y_true"] == 0).all()
    assert (t["y_pred"] == 1).all()
    assert t["y_prob"].is_monotonic_decreasing


def test_top_erros_fn_ordena_por_prob_crescente() -> None:
    df = pd.DataFrame({"x": range(5)})
    y_true = np.array([0, 0, 1, 1, 1])
    y_prob = np.array([0.1, 0.9, 0.1, 0.4, 0.9])

    t = top_erros(df, y_true, y_prob, n=5, criterio="fn")
    assert (t["y_true"] == 1).all()
    assert (t["y_pred"] == 0).all()
    assert t["y_prob"].is_monotonic_increasing


def test_top_erros_criterio_invalido() -> None:
    df = pd.DataFrame({"x": [1, 2]})
    # Valor viola intencionalmente o Literal CriterioTop.
    with pytest.raises(ValueError, match="criterio inválido"):
        top_erros(df, np.array([0, 1]), np.array([0.1, 0.9]), criterio="xxx")  # type: ignore[arg-type]
```

## `tests/test_features.py`

- Git: `tracked` · status `clean`
- Size: `11.3 KB` · modified `2026-10-16 14:54 UTC`
- SHA-256: `db4f5e070d3e0bc1ea7298a41d48a9628bc341d91ea8da80359c8444981dcfe0`

```python
"""
Testes de engenharia de atributos (``src/features/engineering.py``).

Cobre funções puras e o orquestrador ``montar_features``: contrato de
cada derivada, casos inválidos, não-mutação da entrada e invariantes de
ponto-no-tempo. Não testa parsing do YAML.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.features.engineering import (
    ano_mes_internacao,
    faixa_etaria,
    idade_em_anos,
    intervalo_sintomas_internacao,
    montar_features,
    sazonalidade,
    sexo_categoria,
)


# Conjunto mínimo de entradas exigido por ``montar_features``, alinhado
# com ``features.engenharia.entradas`` do supervised.yaml.
ENTRADAS_OBRIGATORIAS: tuple[str, ...] = (
    "nu_idade_n",
    "tp_idade",
    "cs_sexo",
    "dt_sin_pri",
    "dt_interna",
)

# Derivadas que ``montar_features`` deve produzir. Deliberadamente
# hardcoded (não importado de engineering) para travar mudanças
# silenciosas no contrato.
COLUNAS_DERIVADAS_ESPERADAS: frozenset[str] = frozenset({
    "idade_anos",
    "dias_sintomas_ate_internacao",
    "flag_intervalo_invalido",
    "flag_internacao_antes_sintomas",
    "sin_semana",
    "cos_semana",
    "faixa_etaria",
    "sexo_categoria",
    "ano_internacao",
    "mes_internacao",
})


@pytest.fixture
def df_base() -> pd.DataFrame:
    """DataFrame mínimo com as colunas exigidas por ``montar_features``.

    Linhas:

    - 0: adulto (30a), 4 dias até internação, M
    - 1: bebé (6 meses), 5 dias, F
    - 2: adulto (40a), 5 dias, sexo ignorado
    - 3: recém-nascido (1 dia), 5 dias, M
    """
    return pd.DataFrame({
        "nu_idade_n": [30, 6, 40, 1],
        "tp_idade":   [3, 2, 3, 1],
        "cs_sexo":    ["M", "F", "I", "M"],
        "dt_sin_pri": ["2024-01-01", "2024-03-15", "2024-06-20", "2024-09-05"],
        "dt_interna": ["2024-01-05", "2024-03-20", "2024-06-25", "2024-09-10"],
    })


class TestIdadeEmAnos:
    def test_anos_direto(self, df_base: pd.DataFrame) -> None:
        assert idade_em_anos(df_base).iloc[0] == pytest.approx(30.0)

    def test_meses_convertidos(self, df_base: pd.DataFrame) -> None:
        assert idade_em_anos(df_base).iloc[1] == pytest.approx(0.5)

    def test_dias_convertidos(self, df_base: pd.DataFrame) -> None:
        assert idade_em_anos(df_base).iloc[3] == pytest.approx(1 / 365.25)

    def test_retorna_float64(self, df_base: pd.DataFrame) -> None:
        assert idade_em_anos(df_base).dtype == np.float64

    def test_tipo_invalido_vira_nan(self) -> None:
        df = pd.DataFrame({"nu_idade_n": [10], "tp_idade": [9]})
        assert pd.isna(idade_em_anos(df)).all()

    def test_idade_negativa_vira_nan(self) -> None:
        df = pd.DataFrame({"nu_idade_n": [-1], "tp_idade": [3]})
        assert pd.isna(idade_em_anos(df)).all()

    def test_idade_acima_de_120_vira_nan(self) -> None:
        df = pd.DataFrame({"nu_idade_n": [200], "tp_idade": [3]})
        assert pd.isna(idade_em_anos(df)).all()

    def test_nao_muta_entrada(self, df_base: pd.DataFrame) -> None:
        antes = df_base.copy(deep=True)
        idade_em_anos(df_base)
        pd.testing.assert_frame_equal(df_base, antes)


class TestIntervaloSintomasInternacao:
    def test_intervalo_positivo(self, df_base: pd.DataFrame) -> None:
        out = intervalo_sintomas_internacao(df_base)
        assert out["dias_sintomas_ate_internacao"].iloc[0] == pytest.approx(4.0)

    def test_tipos_das_colunas(self, df_base: pd.DataFrame) -> None:
        out = intervalo_sintomas_internacao(df_base)
        assert out["dias_sintomas_ate_internacao"].dtype == np.float64
        assert out["flag_intervalo_invalido"].dtype == np.int8
        assert out["flag_internacao_antes_sintomas"].dtype == np.int8

    def test_negativo_seta_ambas_flags(self) -> None:
        df = pd.DataFrame({"dt_sin_pri": ["2024-01-10"], "dt_interna": ["2024-01-05"]})
        out = intervalo_sintomas_internacao(df)
        assert out["flag_internacao_antes_sintomas"].iloc[0] == 1
        assert out["flag_intervalo_invalido"].iloc[0] == 1

    def test_acima_do_limite_seta_flag_umbrella_sem_marcar_sinal(self) -> None:
        df = pd.DataFrame({"dt_sin_pri": ["2024-01-01"], "dt_interna": ["2024-06-01"]})
        out = intervalo_sintomas_internacao(df)
        assert out["flag_intervalo_invalido"].iloc[0] == 1
        assert out["flag_internacao_antes_sintomas"].iloc[0] == 0

    def test_data_ausente_seta_flag_umbrella(self) -> None:
        df = pd.DataFrame({"dt_sin_pri": [None], "dt_interna": ["2024-01-05"]})
        out = intervalo_sintomas_internacao(df)
        assert pd.isna(out["dias_sintomas_ate_internacao"].iloc[0])
        assert out["flag_intervalo_invalido"].iloc[0] == 1

    def test_politica_sinalizar_mantem_valor_bruto(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Default: valor inválido fica visível, comunicado por flags."""
        df = pd.DataFrame({"dt_sin_pri": ["2024-01-10"], "dt_interna": ["2024-01-05"]})
        monkeypatch.setattr(
            "src.features.engineering._intervalo_politica",
            lambda: "sinalizar",
        )
        out = intervalo_sintomas_internacao(df)
        assert out["dias_sintomas_ate_internacao"].iloc[0] == pytest.approx(-5.0)

    def test_politica_descartar_substitui_por_nan(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        df = pd.DataFrame({"dt_sin_pri": ["2024-01-10"], "dt_interna": ["2024-01-05"]})
        monkeypatch.setattr(
            "src.features.engineering._intervalo_politica",
            lambda: "descartar",
        )
        out = intervalo_sintomas_internacao(df)
        assert pd.isna(out["dias_sintomas_ate_internacao"].iloc[0])
        assert out["flag_intervalo_invalido"].iloc[0] == 1


class TestSazonalidade:
    def test_gera_sin_e_cos_no_intervalo(self, df_base: pd.DataFrame) -> None:
        out = sazonalidade(df_base)
        assert set(out.columns) == {"sin_semana", "cos_semana"}
        for col in out.columns:
            assert out[col].between(-1.0, 1.0, inclusive="both").all()

    def test_mesma_semana_em_anos_diferentes_proxima(self) -> None:
        df = pd.DataFrame({"dt_sin_pri": ["2023-03-15", "2024-03-13"]})  # mesma semana ISO
        out = sazonalidade(df)
        assert abs(out["sin_semana"].iloc[0] - out["sin_semana"].iloc[1]) < 0.1
        assert abs(out["cos_semana"].iloc[0] - out["cos_semana"].iloc[1]) < 0.1

    def test_data_nula_vira_nan(self) -> None:
        out = sazonalidade(pd.DataFrame({"dt_sin_pri": [None]}))
        assert pd.isna(out["sin_semana"].iloc[0])
        assert pd.isna(out["cos_semana"].iloc[0])

    def test_coluna_ausente_levanta_keyerror(self) -> None:
        df = pd.DataFrame({"outra_data": ["2024-01-01"]})
        with pytest.raises(KeyError, match="Coluna temporal ausente"):
            sazonalidade(df, coluna_data="dt_sin_pri")


class TestFaixaEtaria:
    def test_fronteiras_semiabertas(self) -> None:
        out = faixa_etaria(pd.Series([0.0, 0.99, 1.0, 4.99, 5.0, 80.0, 120.0]))
        assert list(out) == ["<1", "<1", "1-4", "1-4", "5-11", "80+", "80+"]

    def test_idade_nula_vira_desconhecida(self) -> None:
        out = faixa_etaria(pd.Series([np.nan, 30.0]))
        assert out.iloc[0] == "desconhecida"
        assert out.iloc[1] == "18-39"

    def test_retorna_categoria(self) -> None:
        assert isinstance(faixa_etaria(pd.Series([30.0])).dtype, pd.CategoricalDtype)


class TestSexoCategoria:
    @pytest.mark.parametrize(
        "entrada, esperado",
        [
            ("M",     "masculino"),
            ("f",     "feminino"),
            (" I ",   "ignorado"),
            ("X",     "ausente"),
            (None,    "ausente"),
        ],
    )
    def test_mapeamento(self, entrada: str | None, esperado: str) -> None:
        df = pd.DataFrame({"cs_sexo": [entrada]})
        assert sexo_categoria(df).iloc[0] == esperado

    def test_retorna_categoria(self) -> None:
        df = pd.DataFrame({"cs_sexo": ["M"]})
        assert isinstance(sexo_categoria(df).dtype, pd.CategoricalDtype)


class TestAnoMesInternacao:
    def test_extrai_ano_e_mes(self, df_base: pd.DataFrame) -> None:
        out = ano_mes_internacao(df_base)
        assert out["ano_internacao"].tolist() == [2024.0] * 4
        assert out["mes_internacao"].tolist() == [1.0, 3.0, 6.0, 9.0]

    def test_data_nula_vira_nan(self) -> None:
        out = ano_mes_internacao(pd.DataFrame({"dt_interna": [None]}))
        assert pd.isna(out["ano_internacao"].iloc[0])
        assert pd.isna(out["mes_internacao"].iloc[0])


class TestMontarFeatures:
    def test_gera_todas_as_derivadas_do_yaml(self, df_base: pd.DataFrame) -> None:
        """Trava o contrato entre ``features.engenharia.derivadas`` e a função."""
        faltando = COLUNAS_DERIVADAS_ESPERADAS - set(montar_features(df_base).columns)
        assert not faltando, f"Derivadas ausentes: {sorted(faltando)}"

    def test_nao_muta_entrada(self, df_base: pd.DataFrame) -> None:
        antes = df_base.copy(deep=True)
        montar_features(df_base)
        pd.testing.assert_frame_equal(df_base, antes)

    def test_preserva_colunas_originais(self, df_base: pd.DataFrame) -> None:
        out = montar_features(df_base)
        assert set(df_base.columns).issubset(out.columns)

    def test_nao_gera_colunas_proibidas(self, df_base: pd.DataFrame) -> None:
        proibidas = {"evolucao", "alvo_obito_srag", "dt_evoluca", "uti", "cluster"}
        assert proibidas.isdisjoint(montar_features(df_base).columns)


class TestPontoNoTempo:
    """Invariantes contra vazamento temporal — o ponto de previsão é a admissão."""

    def test_so_precisa_das_entradas_declaradas(self, df_base: pd.DataFrame) -> None:
        """Um df com só as entradas declaradas deve bastar para as derivadas."""
        out = montar_features(df_base[list(ENTRADAS_OBRIGATORIAS)].copy())
        assert COLUNAS_DERIVADAS_ESPERADAS.issubset(out.columns)

    def test_colunas_pos_admissao_nao_influenciam(self, df_base: pd.DataFrame) -> None:
        """Injetar colunas pós-alta não pode alterar a saída."""
        baseline = montar_features(df_base)

        df_contaminado = df_base.copy()
        df_contaminado["evolucao"]  = [1.0, 2.0, 1.0, 2.0]
        df_contaminado["dt_evoluca"] = pd.to_datetime(
            ["2024-02-01", "2024-04-01", "2024-07-01", "2024-10-01"]
        )
        df_contaminado["uti"]        = [0, 1, 0, 1]
        df_contaminado["suport_ven"] = [0, 1, 0, 0]

        contaminado = montar_features(df_contaminado)

        pd.testing.assert_frame_equal(
            baseline[list(COLUNAS_DERIVADAS_ESPERADAS)].reset_index(drop=True),
            contaminado[list(COLUNAS_DERIVADAS_ESPERADAS)].reset_index(drop=True),
        )

    def test_ordem_das_linhas_nao_altera_derivadas(self, df_base: pd.DataFrame) -> None:
        """Derivadas são pointwise — sem dependência de ordem."""
        normal    = montar_features(df_base)
        invertido = montar_features(df_base.iloc[::-1].reset_index(drop=True))

        pd.testing.assert_frame_equal(
            normal[list(COLUNAS_DERIVADAS_ESPERADAS)].reset_index(drop=True),
            invertido[list(COLUNAS_DERIVADAS_ESPERADAS)].iloc[::-1].reset_index(drop=True),
        )
```

## `tests/test_leakage.py`

- Git: `tracked` · status `clean`
- Size: `3.9 KB` · modified `2026-10-16 14:54 UTC`
- SHA-256: `122506d41aa18213123b6ed3ddddcd38f68b16d69a8448e540708ef0d89a55f8`

```python
"""
Testes anti-vazamento de dados.

Cobrem:

- consistência entre ``features.proibidas`` e ``pipeline.FEATURES``;
- proibição do alvo nas features;
- contrato de ``check_leakage`` (coluna proibida, alvo, lista vazia);
- duplicidade de identificadores no Parquet (slow).
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.evaluation.leakage import LeakageError, check_leakage
from src.utils import config as C


# ---------------------------------------------------------------------------
# Contrato de configuração (features.proibidas ↔ FEATURES)
# ---------------------------------------------------------------------------

@pytest.fixture
def proibidas() -> set[str]:
    """Conjunto ``features.proibidas`` do ``supervised.yaml``."""
    return set(C.cfg("features", "proibidas") or [])


@pytest.fixture
def features_finais() -> set[str]:
    """``pipeline.FEATURES`` — features efetivamente usadas pelo modelo."""
    from src.models import pipeline
    return set(pipeline.FEATURES)


def test_proibidas_nao_vazia(proibidas: set[str]) -> None:
    assert proibidas


def test_alvo_esta_entre_proibidas(proibidas: set[str]) -> None:
    assert C.cfg("target", "coluna") in proibidas


def test_features_finais_sem_proibidas(
    features_finais: set[str],
    proibidas: set[str],
) -> None:
    vazamento = features_finais & proibidas
    assert not vazamento, f"FEATURES contém colunas proibidas: {sorted(vazamento)}"


def test_features_finais_nao_inclui_alvo(features_finais: set[str]) -> None:
    assert C.cfg("target", "coluna") not in features_finais


# ---------------------------------------------------------------------------
# Contrato de check_leakage
# ---------------------------------------------------------------------------

def test_check_leakage_passa_com_X_limpo() -> None:
    X = pd.DataFrame({"feat_a": [1, 2, 3], "feat_b": [4, 5, 6]})
    check_leakage(X)


def test_check_leakage_levanta_para_proibida(proibidas: set[str]) -> None:
    coluna = sorted(proibidas)[0]
    X = pd.DataFrame({coluna: [1, 2, 3], "feat_ok": [4, 5, 6]})

    with pytest.raises(LeakageError) as exc:
        check_leakage(X)

    assert coluna in str(exc.value)


def test_check_leakage_levanta_para_alvo() -> None:
    alvo = C.cfg("target", "coluna")
    X = pd.DataFrame({alvo: [0, 1, 0], "feat_ok": [1, 2, 3]})

    with pytest.raises(LeakageError):
        check_leakage(X)


def test_check_leakage_lista_vazia_ainda_verifica_alvo() -> None:
    """``forbidden_columns=[]`` ainda soma ``DEFAULT_LEAKAGE_COLUMNS`` + alvo."""
    alvo = C.cfg("target", "coluna")
    X = pd.DataFrame({alvo: [0, 1, 0], "feat_ok": [1, 2, 3]})

    with pytest.raises(LeakageError):
        check_leakage(X, forbidden_columns=[])


# ---------------------------------------------------------------------------
# Identificadores no Parquet (slow)
# ---------------------------------------------------------------------------

@pytest.mark.slow
def test_dataset_sem_identificadores_duplicados(parquet_disponivel) -> None:
    """Taxa de ``nu_notific`` (ou equivalente) duplicado deve ser < 5%."""
    if parquet_disponivel is None:
        pytest.skip("Parquet não disponível.")

    import pyarrow.parquet as pq

    colunas = set(pq.read_schema(parquet_disponivel).names)
    candidatas = ("nu_notific", "numero_notificacao", "id_notificacao", "id")
    coluna_id = next((c for c in candidatas if c in colunas), None)

    if coluna_id is None:
        pytest.skip("Sem coluna identificadora adequada.")

    df = pd.read_parquet(parquet_disponivel, columns=[coluna_id])
    ids = df[coluna_id].dropna().astype("string").str.strip()
    ids = ids[ids.ne("")]

    if ids.empty:
        pytest.skip(f"Coluna {coluna_id} sem identificadores válidos.")

    taxa = int(ids.duplicated().sum()) / len(ids)
    assert taxa < 0.05, f"Taxa alta de duplicados em {coluna_id}: {taxa:.1%}"
```

## `tests/test_metrics.py`

- Git: `tracked` · status `clean`
- Size: `5.5 KB` · modified `2026-10-16 14:54 UTC`
- SHA-256: `1251e53dbcb79353e211e590d332539869bb13d1671fa69eaf4ca35e892eb370`

```python
"""Testes das métricas em ``src.evaluation.metrics``."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.evaluation.metrics import (
    accuracy,
    auc,
    average_precision,
    brier,
    f1,
    ic_bootstrap,
    metricas_completas,
    metricas_por_limiar,
    precision,
    recall,
)


@pytest.fixture
def y_true() -> np.ndarray:
    """10 rótulos binários — 6 positivos (1), 4 negativos (0)."""
    return np.array([0, 0, 1, 1, 1, 0, 1, 0, 1, 1])


@pytest.fixture
def y_prob() -> np.ndarray:
    """10 probabilidades em ``[0, 1]`` correlacionadas com ``y_true``."""
    return np.array([0.1, 0.2, 0.8, 0.9, 0.6, 0.3, 0.7, 0.4, 0.85, 0.75])


# Chaves contratuais de ``metricas_completas`` — a lista serve como
# armadilha contra remoções silenciosas no módulo fonte.
_CHAVES_METRICAS_COMPLETAS = (
    "auc", "ap", "brier", "f1", "precision", "recall",
    "accuracy", "limiar", "n",
)


# ---------------------------------------------------------------------------
# AUC
# ---------------------------------------------------------------------------

def test_auc_perfeito() -> None:
    """Classificador com separação perfeita → AUC = 1.0."""
    y = np.array([0, 0, 1, 1])
    p = np.array([0.1, 0.2, 0.8, 0.9])
    assert auc(y, p) == pytest.approx(1.0)


def test_auc_constante_e_meio() -> None:
    """Probabilidades constantes → AUC = 0.5 por construção."""
    y = np.array([0, 0, 1, 1])
    p = np.array([0.5, 0.5, 0.5, 0.5])
    assert auc(y, p) == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# Métricas de probabilidade (aceitam y_prob)
# ---------------------------------------------------------------------------

def test_metricas_individuais_retornam_float(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> None:
    for fn in (auc, average_precision, brier):
        assert isinstance(fn(y_true, y_prob), float)


def test_average_precision_em_intervalo(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> None:
    assert 0.0 <= average_precision(y_true, y_prob) <= 1.0


def test_brier_em_intervalo(y_true: np.ndarray, y_prob: np.ndarray) -> None:
    assert 0.0 <= brier(y_true, y_prob) <= 1.0


# ---------------------------------------------------------------------------
# Métricas de classificação (aceitam y_pred duro)
# ---------------------------------------------------------------------------

def test_f1_precision_recall(y_true: np.ndarray) -> None:
    y_pred = np.array([0, 0, 1, 1, 1, 0, 0, 0, 1, 1])
    for fn in (f1, precision, recall):
        v = fn(y_true, y_pred)
        assert isinstance(v, float)
        assert 0.0 <= v <= 1.0


def test_accuracy_perfeita() -> None:
    y = np.array([0, 1, 0, 1])
    assert accuracy(y, y) == pytest.approx(1.0)


def test_zero_division_nao_quebra() -> None:
    """``y_true`` e ``y_pred`` sem positivos → métricas devolvem 0.0, não ``ZeroDivisionError``."""
    y_true = np.zeros(3, dtype=int)
    y_pred = np.zeros(3, dtype=int)
    assert f1(y_true, y_pred) == 0.0
    assert precision(y_true, y_pred) == 0.0
    assert recall(y_true, y_pred) == 0.0


# ---------------------------------------------------------------------------
# metricas_completas
# ---------------------------------------------------------------------------

def test_metricas_completas_chaves(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> None:
    d = metricas_completas(y_true, y_prob, limiar=0.5)
    for k in _CHAVES_METRICAS_COMPLETAS:
        assert k in d
    assert d["limiar"] == 0.5
    assert d["n"] == float(len(y_true))


def test_metricas_completas_aceita_series(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> None:
    """``metricas_completas`` deve aceitar ``pd.Series`` como entrada."""
    d = metricas_completas(pd.Series(y_true), pd.Series(y_prob))
    assert "auc" in d


# ---------------------------------------------------------------------------
# metricas_por_limiar
# ---------------------------------------------------------------------------

def test_metricas_por_limiar(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> None:
    t = metricas_por_limiar(y_true, y_prob, n_limiares=11)
    assert {"limiar", "f1", "precision", "recall", "accuracy"}.issubset(t.columns)
    assert len(t) == 11
    assert (t["limiar"] > 0).all()
    assert (t["limiar"] < 1).all()


# ---------------------------------------------------------------------------
# ic_bootstrap
# ---------------------------------------------------------------------------

def test_ic_bootstrap_retorna_tres_floats(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> None:
    est, inf, sup = ic_bootstrap(y_true, y_prob, n_boot=50, seed=42)
    assert isinstance(est, float)
    assert isinstance(inf, float)
    assert isinstance(sup, float)
    assert inf <= sup


def test_ic_bootstrap_deterministico(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> None:
    """Mesma seed → mesmo resultado."""
    a = ic_bootstrap(y_true, y_prob, n_boot=50, seed=42)
    b = ic_bootstrap(y_true, y_prob, n_boot=50, seed=42)
    assert a == b


def test_ic_bootstrap_metrica_customizada(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> None:
    est, inf, sup = ic_bootstrap(
        y_true,
        y_prob,
        metrica=average_precision,
        n_boot=30,
        seed=1,
    )
    assert inf <= est <= sup
```

## `tests/test_model_pipelines.py`

- Git: `tracked` · status `clean`
- Size: `6.2 KB` · modified `2026-10-16 14:54 UTC`
- SHA-256: `5dd0bbc04fc6c0033ae84664fc9de929d70e6c05a8ca0c4f89ccdd5b8c581af6`

```python
"""
Testes rápidos dos construtores de pipeline de modelos supervisionados.

Cobrem baseline, logística e boosting. Não dependem do Parquet nem fazem
I/O pesado. As features vêm de ``src.models.pipeline`` (que lê o
``supervised.yaml``) — sem hard-code.
"""

from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd
import pytest
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from src.models import pipeline as P
from src.models.baseline import build_baseline_pipeline
from src.models.boosting import build_boosting_pipeline
from src.models.logistic import build_logistic_pipeline
from src.utils import config as C


def _df_features(
    n: int = 200,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.Series]:
    """DataFrame sintético com exactamente as features exigidas pelo YAML.

    Numéricas com distribuição normal; categóricas com 3 níveis como
    strings. O alvo é balanceado 50/50 e depois embaralhado — garante as
    duas classes para ``DummyClassifier(strategy="prior")`` e para
    ``LogisticRegression(class_weight="balanced")``.
    """
    rng = np.random.default_rng(seed)
    dados: dict[str, np.ndarray] = {}

    for coluna in P.FEATURES_NUMERICAS:
        dados[coluna] = rng.normal(loc=50.0, scale=15.0, size=n)
    for coluna in P.FEATURES_CATEGORICAS:
        dados[coluna] = rng.choice(["0", "1", "2"], size=n)

    X = pd.DataFrame(dados)
    y = pd.Series(
        np.concatenate([np.zeros(n // 2, dtype=int), np.ones(n - n // 2, dtype=int)]),
        name="alvo",
    ).sample(frac=1, random_state=seed).reset_index(drop=True)

    return X, y


def _colunas_do_pre(pipe: Pipeline) -> set[str]:
    """Colunas declaradas no ``ColumnTransformer`` do pipeline.

    ``ColumnTransformer.transformers`` é uma lista de
    ``(nome, transformer, colunas)`` — extraímos a terceira posição.
    """
    colunas: set[str] = set()
    for _, _, cols in pipe.named_steps["pre"].transformers:
        if isinstance(cols, list):
            colunas.update(cols)
    return colunas


# `max_iter` reduzido para manter os testes rápidos — smoke de fit, não tuning.
_CONSTRUTORES: list[tuple[str, Callable[[], Pipeline], type]] = [
    ("baseline", lambda: build_baseline_pipeline(), DummyClassifier),
    ("logistic", lambda: build_logistic_pipeline(max_iter=500), LogisticRegression),
    ("boosting", lambda: build_boosting_pipeline(max_iter=30), HistGradientBoostingClassifier),
]

_IDS = [nome for nome, _, _ in _CONSTRUTORES]


# ---------------------------------------------------------------------------
# Contrato do pipeline (estrutura)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(("nome", "ctor", "clf_esperado"), _CONSTRUTORES, ids=_IDS)
def test_pipeline_retorna_pipeline(
    nome: str,
    ctor: Callable[[], Pipeline],
    clf_esperado: type,
) -> None:
    """Cada construtor devolve ``Pipeline(pre, clf)`` com o classificador correto."""
    pipe = ctor()
    assert isinstance(pipe, Pipeline), nome
    assert list(pipe.named_steps.keys()) == ["pre", "clf"], nome
    assert isinstance(pipe.named_steps["clf"], clf_esperado), nome


@pytest.mark.parametrize(("nome", "ctor", "clf_esperado"), _CONSTRUTORES, ids=_IDS)
def test_pipeline_nao_inclui_proibidas(
    nome: str,
    ctor: Callable[[], Pipeline],
    clf_esperado: type,
) -> None:
    proibidas = set(C.cfg("features", "proibidas") or [])
    assert proibidas, (
        "`features.proibidas` está vazio no supervised.yaml — "
        "ao menos o alvo e as colunas posteriores ao desfecho precisam "
        "estar listadas."
    )

    colisoes = _colunas_do_pre(ctor()) & proibidas
    assert not colisoes, (
        f"{nome}: colunas proibidas no pré-processador: {sorted(colisoes)}"
    )


# ---------------------------------------------------------------------------
# Comportamento (fit + predict_proba)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(("nome", "ctor", "clf_esperado"), _CONSTRUTORES, ids=_IDS)
def test_pipeline_fit_predict_proba(
    nome: str,
    ctor: Callable[[], Pipeline],
    clf_esperado: type,
) -> None:
    X, y = _df_features(n=200)
    pipe = ctor().fit(X, y)
    proba = pipe.predict_proba(X)

    assert proba.shape == (len(X), 2), f"{nome}: shape {proba.shape}"
    assert np.isfinite(proba).all(), f"{nome}: probabilidades com NaN/Inf"
    assert ((proba >= 0) & (proba <= 1)).all(), f"{nome}: fora de [0, 1]"
    assert np.allclose(proba.sum(axis=1), 1.0), f"{nome}: linhas não somam 1"


# ---------------------------------------------------------------------------
# Contrato de features
# ---------------------------------------------------------------------------

def test_pipelines_usam_features_do_yaml() -> None:
    """Pré-processador expõe ``FEATURES_NUMERICAS + FEATURES_CATEGORICAS`` do YAML.

    Canário contra features fora do YAML ou filtros silenciosos.
    """
    esperadas = set(P.FEATURES_NUMERICAS) | set(P.FEATURES_CATEGORICAS)
    assert esperadas, "Nenhuma feature declarada em supervised.yaml."

    for nome, ctor, _ in _CONSTRUTORES:
        colunas = _colunas_do_pre(ctor())
        faltando = esperadas - colunas
        extras = colunas - esperadas
        assert colunas == esperadas, (
            f"{nome}: pré-processador divergente do YAML. "
            f"Faltando: {sorted(faltando)}; Extras: {sorted(extras)}"
        )


# ---------------------------------------------------------------------------
# Validação de parâmetros
# ---------------------------------------------------------------------------

def test_logistic_pipeline_solver_invalido() -> None:
    """``l1_ratio=1.0`` (L1 puro) exige ``liblinear`` ou ``saga``.

    Com ``lbfgs`` o construtor deve levantar ``ValueError``.
    """
    with pytest.raises(ValueError, match="combinação inválida"):
        build_logistic_pipeline(l1_ratio=1.0, solver="lbfgs")
```

## `tests/test_pipeline.py`

- Git: `tracked` · status `clean`
- Size: `2.7 KB` · modified `2026-10-16 14:54 UTC`
- SHA-256: `0b547fc2d43446a0239bbb73659cfcb3cbbb362a90b86f8bf7e73dd7b35cbc00`

```python
"""
Testes do pipeline de ingestão: ``read_srag``, ``get_parquet`` e
``build_pipeline``.

Testes que tocam no Parquet são marcados com ``@pytest.mark.slow``.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.models.pipeline import build_pipeline
from src.utils import env
from src.utils.storage import get_parquet, read_srag


# ---------------------------------------------------------------------------
# Ingestão do Parquet (slow)
# ---------------------------------------------------------------------------

@pytest.mark.slow
def test_read_srag_retorna_dataframe(parquet_disponivel: Path | None) -> None:
    if parquet_disponivel is None:
        pytest.skip("Parquet não disponível.")

    df = read_srag(columns=["sg_uf", "dt_notific"])

    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert {"sg_uf", "dt_notific"}.issubset(set(df.columns))


@pytest.mark.slow
def test_get_parquet_reaproveita_arquivo(parquet_disponivel: Path | None) -> None:
    """``force=False`` reutiliza o arquivo existente (mesmo mtime e tamanho)."""
    if parquet_disponivel is None:
        pytest.skip("Parquet não disponível.")

    caminho_1 = get_parquet(force=False)
    estado_1 = caminho_1.stat()
    caminho_2 = get_parquet(force=False)
    estado_2 = caminho_2.stat()

    assert caminho_1.resolve() == caminho_2.resolve()
    assert estado_1.st_mtime_ns == estado_2.st_mtime_ns
    assert estado_1.st_size == estado_2.st_size


# ---------------------------------------------------------------------------
# build_pipeline
# ---------------------------------------------------------------------------

def test_build_pipeline_falha_feature_ausente() -> None:
    X = pd.DataFrame({"nu_idade_n": [30.0, 40.0, 50.0]})
    with pytest.raises(KeyError, match="ausentes"):
        build_pipeline(X=X)


def test_build_pipeline_strict_false_avisa_mas_continua(
    caplog: pytest.LogCaptureFixture,
) -> None:
    X = pd.DataFrame({"nu_idade_n": [30.0, 40.0, 50.0]})
    with caplog.at_level("WARNING"):
        pipe = build_pipeline(X=X, strict=False)

    assert pipe is not None
    assert "ausentes" in caplog.text.lower()


# ---------------------------------------------------------------------------
# Diretórios padrão
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("nome_dir", ["RAW", "PROCESSED"])
def test_diretorio_padrao_foi_criado(nome_dir: str) -> None:
    """``env.garantir_diretorios`` cria os diretórios esperados."""
    env.garantir_diretorios()
    caminho = getattr(env, nome_dir)
    assert caminho.is_dir(), f"{caminho} não é diretório"
```

## `tests/test_regras_pessoa_a.py`

- Git: `tracked` · status `clean`
- Size: `22.9 KB` · modified `2026-10-16 14:54 UTC`
- SHA-256: `9b4f7be9ae95ffc9d1af19fd25f5182f4f3c57e8da0ad73e1cdf5aae7d3f74d7`

```python
"""
Testes das regras da Pessoa A (``src.protocolo.verificacoes``).

Cobre A1–A4, casos limite de datas, leitura compacta (colunas
``category``) e o contrato de exportação consumido pelo C2.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.protocolo import verificacoes as v


# ---------------------------------------------------------------------------
# Fixtures e helpers
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def cfg() -> dict:
    return v.load_config(None)


@pytest.fixture(scope="module")
def demo() -> pd.DataFrame:
    return v.prepare(v.make_demo(n=3000)[0])


def _escrever_yaml(
    tmp_path: Path,
    numericas: list[str],
    categoricas: list[str],
    *,
    proibidas: list[str] | None = None,
    grupos: list[str] | None = None,
) -> Path:
    """Escreve ``supervised.yaml`` mínimo para testes de exportação.

    Devolve o ``Path``. Cobre os campos consumidos por ``a1_export_dataset``
    e ``validar_contrato_c2``: alvo, coluna de tempo, features e (opcional)
    grupos de avaliação.
    """
    def lst(items: list[str]) -> str:
        return "[" + ", ".join(items) + "]"

    features = (
        f"{{numericas: {lst(numericas)}, categoricas: {lst(categoricas)}"
        + (f", proibidas: {lst(proibidas)}" if proibidas else "")
        + "}"
    )
    linhas = [
        "target: {coluna: evolucao, positivos: [2.0]}",
        "coluna_tempo: dt_notific",
        f"features: {features}",
    ]
    if grupos:
        linhas.append(f"avaliacao: {{grupos: {lst(grupos)}}}")

    caminho = tmp_path / "supervised.yaml"
    caminho.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return caminho


def _base_texto(n: int = 15_000) -> pd.DataFrame:
    """``make_demo`` com datas como texto ISO e códigos como strings."""
    base = v.make_demo(n=n, inicio="2019-01-01", anos=7)[0]
    base.columns = [c.lower() for c in base.columns]
    for c in ("dt_nasc", "dt_evoluca", "dt_encerra", "dt_sin_pri", "dt_interna", "dt_notific"):
        base[c] = base[c].dt.strftime("%Y-%m-%d")
    for c in ("evolucao", "hospital", "tp_idade"):
        base[c] = base[c].astype("Int64").astype(str).replace("<NA>", None)
    return base


def _como_categoria(df: pd.DataFrame) -> pd.DataFrame:
    """Converte todas as colunas string (excepto ``nu_notific``) em ``category``."""
    d = df.copy()
    for c in d.columns:
        if (d[c].dtype == object or pd.api.types.is_string_dtype(d[c])) and c != "nu_notific":
            d[c] = d[c].astype("category")
    return d


# ---------------------------------------------------------------------------
# A1 — alvo, aliases, datas, waterfall, coorte
# ---------------------------------------------------------------------------

def test_alvo_desconhecido_nao_vira_cura(cfg):
    t = v.make_target(pd.Series(["1", "2", "3", "9", None, "", "x", 1.0, 2.0]), cfg)
    assert list(t.astype("object")) == [0, 1, pd.NA, pd.NA, pd.NA, pd.NA, pd.NA, 0, 1]


def test_aliases_para_nomes_canonicos():
    df = v.prepare(pd.DataFrame({"internado": [1], "dt_encerramento": ["2024-01-01"], "evolucao": [2]}))
    assert {"HOSPITAL", "DT_ENCERRA", "EVOLUCAO"} <= set(df.columns)


def test_parse_date_iso_e_br():
    s = v.parse_date(pd.Series(["2024-03-05", "05/03/2024", "lixo", None]))
    assert s.iloc[0] == s.iloc[1] == pd.Timestamp("2024-03-05")
    assert s.iloc[2:].isna().all()


def test_waterfall_monotonico(cfg, demo, tmp_path):
    rep = v.Report(tmp_path)
    wf = v.a1_waterfall(demo, cfg, rep)
    assert wf["n_restante"].iloc[0] == len(demo)
    assert wf["n_restante"].is_monotonic_decreasing
    assert (wf["n_excluido"].iloc[1:].sum() + wf["n_restante"].iloc[-1]) == len(demo)


def test_coorte_so_tem_cura_ou_obito(cfg, demo):
    c = v.a1_cohort(demo, cfg)
    assert set(c["_alvo"].unique()) <= {0, 1}
    assert set(c["_ano"].unique()) <= set(cfg["dev_years"] + cfg["holdout_years"])


# ---------------------------------------------------------------------------
# A2 — datas absurdas, maturidade, formatos mistos
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("unidade", ["s", "ms", "us", "texto"])
def test_datas_absurdas_nao_estouram(cfg, tmp_path, unidade):
    datas = ["2024-03-05", "0001-01-01", "9999-12-31", "1850-05-05", "2024-01-01"]
    col = (pd.Series(datas) if unidade == "texto"
           else pd.Series(np.array(datas, dtype=f"datetime64[{unidade}]")))
    outra = pd.Series(["2024-03-01"] * 5) if unidade == "texto" else pd.Series(
        np.array(["2024-03-01"] * 5, dtype=f"datetime64[{unidade}]"))
    d = v.parse_date(col)
    assert d.isna().tolist() == [False, True, True, True, False]
    df = pd.DataFrame({"DT_NASC": col, "DT_SIN_PRI": outra, "DT_NOTIFIC": outra, "DT_INTERNA": col,
                       "DT_EVOLUCA": col, "DT_ENCERRA": outra, "HOSPITAL": 1, "EVOLUCAO": 1,
                       "TP_IDADE": 3, "NU_IDADE_N": 40, "NU_NOTIFIC": "1"})
    rep = v.Report(tmp_path)
    v.a2_dates(df, cfg, rep)      # não pode levantar OverflowError
    v.a2_maturity(df, cfg, rep)


def test_parse_date_formatos_mistos_e_ano_absurdo():
    s = v.parse_date(pd.Series(["2022-03-05", "05/03/2022", "05/03/2022 00:00:00", "2022/03/05", "2224-01-01", "lixo"]))
    assert s.iloc[:4].eq(pd.Timestamp("2022-03-05")).all()
    assert s.iloc[4:].isna().all()


def test_parse_date_categorica_igual_a_texto():
    s = pd.Series(["2022-03-05", "05/03/2022", None, "9999-12-31", "lixo", "2022-03-05"] * 50)
    a = v.parse_date(s)
    b = v.parse_date(s.astype("category"))
    assert a.isna().tolist() == b.isna().tolist()
    assert a.dropna().tolist() == b.dropna().tolist()


# ---------------------------------------------------------------------------
# A3 — auditoria de config e deteção de vazamento
# ---------------------------------------------------------------------------

def test_variavel_proibida_gera_falha(cfg, tmp_path):
    rep = v.Report(tmp_path)
    v.a3_forbidden(["NU_IDADE_N", "DT_EVOLUCA"], "supervisionado", cfg, rep)
    assert rep.has_failure


def test_evolucao_no_clustering_gera_falha(cfg, tmp_path):
    rep = v.Report(tmp_path)
    v.a3_forbidden(["EVOLUCAO", "FEBRE"], "clustering", cfg, rep)
    assert rep.has_failure


def test_auditoria_supervised_aponta_fracao_e_dt_notific(cfg, tmp_path):
    y = {"target": {"positivos": [2.0], "descartar_ignorado": True}, "coluna_tempo": "dt_notific",
         "temporal": {"modo": "fracao"}, "features": {"numericas": ["nu_idade_n"], "categoricas": ["febre"]}}
    rep = v.Report(tmp_path)
    v.a3_config_audit(y, cfg, rep)
    checks = {f[1]: f[2] for f in rep.findings}
    assert checks["Coluna temporal"] == v.WARN
    assert checks["Split temporal"] == v.WARN
    assert checks["Alvo: evolucao=3 e ausente"] == v.WARN
    assert checks["Idade"] == v.WARN


def test_auditoria_yaml_contra_schema_fisico(cfg, tmp_path):
    schema = ["nu_notific", "hospital", "evolucao", "dt_evoluca", "dt_encerra", "cs_gestant", "nu_idade_n", "febre"]
    y = {"target": {"positivos": [2.0]}, "coluna_tempo": "dt_notific", "temporal": {"modo": "fracao"},
         "features": {"numericas": ["nu_idade_n"], "categoricas": ["tp_gestante", "internado", "febre"],
                      "proibidas": ["evolucao", "dt_evolucao", "dt_encerramento"]}}
    rep = v.Report(tmp_path)
    v.a3_config_audit(y, cfg, rep, schema)
    achados = {f[1]: f for f in rep.findings}
    f1 = achados["Features do YAML x Parquet"]
    assert f1[2] == v.FAIL and "tp_gestante" in f1[3] and "internado->hospital" in f1[3]
    f2 = achados["`proibidas` do YAML x Parquet"]
    assert f2[2] == v.WARN and "dt_evolucao->dt_evoluca" in f2[3] and "dt_encerramento->dt_encerra" in f2[3]


def test_auditoria_nao_acusa_derivadas_como_ausentes(cfg, tmp_path):
    y = {"target": {"positivos": [2.0]}, "coluna_tempo": "dt_notific", "temporal": {"modo": "fracao"},
         "features": {"numericas": ["nu_idade_n", "idade_anos", "sin_semana"], "categoricas": ["faixa_etaria", "febre"],
                      "proibidas": ["evolucao"]}}
    rep = v.Report(tmp_path)
    v.a3_config_audit(y, cfg, rep, ["nu_idade_n", "febre", "evolucao", "dt_notific"])
    achados = {f[1]: f[2] for f in rep.findings}
    assert achados["Features do YAML x Parquet"] == v.OK
    assert achados["Features derivadas do YAML"] == v.OK


# ---------------------------------------------------------------------------
# A1 — exportação do dataset analítico
# ---------------------------------------------------------------------------

def test_exporta_dataset_para_o_c2(cfg, tmp_path):
    base = v.make_demo(n=3000)[0]
    base.columns = [c.lower() for c in base.columns]
    base = base.rename(columns={"hospital": "internado"})
    df = v.prepare(base)

    y = _escrever_yaml(tmp_path, ["nu_idade_n"], ["febre", "internado"])
    out = tmp_path / "dataset_supervisionado.csv"
    meta = v.a1_export_dataset(df, cfg, v.Report(tmp_path), y, path=out)

    d = pd.read_csv(out)
    assert {"evolucao", "dt_notific", "nu_idade_n", "febre", "internado"} <= set(d.columns)
    assert set(d["evolucao"].unique()) <= {1, 2}
    assert d["dt_notific"].is_monotonic_increasing
    assert "dt_evoluca" not in d.columns and meta["n_linhas"] == len(d)


def test_export_cria_derivadas_pedidas_pelo_yaml(cfg, tmp_path):
    base = v.make_demo(n=3000)[0]
    base.columns = [c.lower() for c in base.columns]

    y = _escrever_yaml(
        tmp_path,
        ["nu_idade_n", "idade_anos", "intervalo_sint_interna_dias",
         "flag_intervalo_invalido", "sin_semana", "cos_semana"],
        ["febre", "faixa_etaria"],
        proibidas=["evolucao", "dt_evoluca"],
        grupos=["cs_sexo", "faixa_etaria"],
    )
    out = tmp_path / "d.csv"
    meta = v.a1_export_dataset(v.prepare(base), cfg, v.Report(tmp_path), y, path=out)

    d = pd.read_csv(out)
    for col in ("idade_anos", "intervalo_sint_interna_dias", "flag_intervalo_invalido",
                "sin_semana", "cos_semana", "faixa_etaria", "cs_sexo"):
        assert col in d.columns, col
    assert meta["features_ausentes_na_base"] == []

    rep = v.Report(tmp_path, "c")
    assert v.validar_contrato_c2(out, y, rep) is True


def test_find_base_ignora_dataset_analitico(tmp_path):
    (tmp_path / "data" / "analytical").mkdir(parents=True)
    (tmp_path / "data" / "raw").mkdir(parents=True)
    (tmp_path / "data" / "analytical" / "dataset_supervisionado.parquet").write_bytes(b"x")
    (tmp_path / "data" / "raw" / "srag.csv").write_text("a\n1\n")
    base_encontrada = v.find_base(tmp_path)
    assert base_encontrada is not None
    assert base_encontrada.name == "srag.csv"


def test_contrato_c2_dataset_valido(cfg, tmp_path):
    base = v.make_demo(n=3000)[0]
    base.columns = [c.lower() for c in base.columns]

    y = _escrever_yaml(tmp_path, ["nu_idade_n"], ["febre", "dispneia"],
                       proibidas=["evolucao", "dt_evoluca"])
    out = tmp_path / "dataset_supervisionado.csv"
    meta = v.a1_export_dataset(v.prepare(base), cfg, v.Report(tmp_path), y, path=out)

    rep = v.Report(tmp_path, "contrato")
    assert v.validar_contrato_c2(out, y, rep) is True
    assert meta["descartadas_data_tempo_invalida"] >= 0
    assert not rep.has_failure


def test_contrato_c2_feature_inexistente_e_proibida_falham(cfg, tmp_path):
    base = v.make_demo(n=2000)[0]
    base.columns = [c.lower() for c in base.columns]

    # Feature inexistente na base (tp_gestante)
    y = _escrever_yaml(tmp_path, ["nu_idade_n"], ["febre", "tp_gestante"],
                       proibidas=["evolucao", "dt_evoluca"])
    out = tmp_path / "d.csv"
    v.a1_export_dataset(v.prepare(base), cfg, v.Report(tmp_path), y, path=out)

    rep = v.Report(tmp_path, "c1")
    assert v.validar_contrato_c2(out, y, rep) is False
    assert any(f[1] == "Colunas exigidas pelo C2" and f[2] == v.FAIL for f in rep.findings)

    # Feature proibida no X (evolucao)
    y2 = _escrever_yaml(tmp_path, ["nu_idade_n"], ["febre", "evolucao"],
                        proibidas=["evolucao", "dt_evoluca"])
    rep2 = v.Report(tmp_path, "c2")
    v.validar_contrato_c2(out, y2, rep2)
    assert any(f[1].startswith("check_leakage") and f[2] == v.FAIL for f in rep2.findings)


# ---------------------------------------------------------------------------
# Features derivadas
# ---------------------------------------------------------------------------

def test_features_derivadas_valores(cfg):
    df = pd.DataFrame({
        "NU_IDADE_N": [40, 24, 365, 150, 30, 5],
        "TP_IDADE": [3, 2, 1, 3, 3, 3],                       # anos, meses, dias, anos(absurdo), anos, anos
        "DT_SIN_PRI": ["2024-01-01", "2024-01-10", "2024-01-10", "2024-01-01", None, "2024-01-01"],
        "DT_INTERNA": ["2024-01-03", "2024-01-05", "2024-01-20", "2024-03-01", "2024-01-03", "2024-01-08"],
    })
    criadas = v.add_derived(df, cfg)
    assert set(criadas) == {d.upper() for d in v.DERIVADAS}
    assert df["IDADE_ANOS"].iloc[:3].tolist() == [40.0, 2.0, 1.0] and pd.isna(df["IDADE_ANOS"].iloc[3])
    assert df["FAIXA_ETARIA"].iloc[:3].tolist() == ["40-49", "1-4", "1-4"] and pd.isna(df["FAIXA_ETARIA"].iloc[3])
    # intervalo: 2 dias ok | -5 (negativo) | 10 ok | 60 (>30) | ausente | 7 ok
    assert df["FLAG_INTERVALO_INVALIDO"].tolist() == [0, 1, 0, 1, 1, 0]
    assert df["INTERVALO_SINT_INTERNA_DIAS"].iloc[np.array([0, 2, 5])].tolist() == [2.0, 10.0, 7.0]
    assert df["INTERVALO_SINT_INTERNA_DIAS"].iloc[np.array([1, 3, 4])].isna().all()
    assert df["SIN_SEMANA"].between(-1, 1).all() and df["COS_SEMANA"].between(-1, 1).all()


def test_derivadas_nao_dependem_do_desfecho(cfg):
    import inspect
    fonte = inspect.getsource(v.add_derived)
    for proibido in ("EVOLUCAO", "dt_evoluca", "dt_encerra", "CLASSI_FIN"):
        assert proibido not in fonte


# ---------------------------------------------------------------------------
# A3b — split aleatório e cenários
# ---------------------------------------------------------------------------

def test_split_aleatorio_proporcoes_estratos_e_reprodutibilidade():
    n = 10_000
    y = np.array(["1"] * 8_700 + ["2"] * 1_300)
    a = v.split_aleatorio(n, y, seed=42)
    b = v.split_aleatorio(n, y, seed=42)
    c = v.split_aleatorio(n, y, seed=7)
    assert (a == b).all() and not (a == c).all()

    s = pd.Series(a)
    assert s.value_counts().to_dict() == {"treino": 7000, "validacao": 1500, "holdout": 1500}
    for classe, total in (("1", 8700), ("2", 1300)):
        sub = pd.Series(a[y == classe]).value_counts()
        assert abs(sub["treino"] - 0.70 * total) <= 1 and abs(sub["validacao"] - 0.15 * total) <= 1


def test_split_por_ordem_e_cronologico():
    t = pd.to_datetime(pd.Series(pd.date_range("2022-01-01", periods=1000))).sample(frac=1, random_state=1).to_numpy()
    rot = v.split_por_ordem(t)
    d = pd.DataFrame({"t": t, "r": rot})
    assert d[d.r == "treino"].t.max() <= d[d.r == "validacao"].t.min()
    assert d[d.r == "validacao"].t.max() <= d[d.r == "holdout"].t.min()


def test_cenario_sem_2020_2021_exclui_os_anos(cfg, tmp_path):
    base = v.make_demo(n=20_000, inicio="2019-01-01", anos=7)[0]
    base.columns = [c.lower() for c in base.columns]
    df = v.prepare(base)

    y = _escrever_yaml(tmp_path, ["nu_idade_n", "idade_anos"], ["febre", "dispneia", "faixa_etaria"])
    c2 = json.loads(json.dumps(cfg)); c2["dataset_analitico"]["path"] = str(tmp_path / "dataset.csv")
    rep = v.Report(tmp_path)
    cenarios = c2["experimentos_split"]["cenarios"]

    m_todos = v.a3_split_aleatorio_cenario(df, c2, rep, "todos_2019_2025", cenarios["todos_2019_2025"]["anos"], y)
    m_sem = v.a3_split_aleatorio_cenario(df, c2, rep, "sem_2020_2021", cenarios["sem_2020_2021"]["anos"], y)
    d_todos = pd.read_csv(m_todos["arquivo"]); d_sem = pd.read_csv(m_sem["arquivo"])

    assert {2019, 2020, 2021, 2022, 2023, 2024, 2025} <= set(d_todos["ano_internacao"].unique())
    assert set(d_sem["ano_internacao"].unique()) == {2019, 2022, 2023, 2024, 2025}
    assert len(d_sem) < len(d_todos)
    assert set(d_todos["split"].unique()) == {"treino", "validacao", "holdout"}
    assert abs(d_todos["split"].value_counts(normalize=True)["treino"] - 0.70) < 0.005

    prev = d_todos.groupby("split")["evolucao"].apply(lambda s: (s == 2).mean())
    assert prev.max() - prev.min() < 0.005

    assert m_todos["arquivo"] != m_sem["arquivo"]
    assert not [f for f in rep.findings if f[0] == "A3b" and f[2] == v.FAIL]

    assert v.verificar_dataset_congelado(m_todos["arquivo"], rep) is True
    with open(m_todos["arquivo"], "a", encoding="utf-8") as fh:
        fh.write("\n")
    assert v.verificar_dataset_congelado(m_todos["arquivo"], rep) is False


def test_benchmark_aleatorio_x_temporal_e_comparacao(cfg, tmp_path):
    base = v.make_demo(n=15_000, inicio="2019-01-01", anos=7)[0]
    base.columns = [c.lower() for c in base.columns]
    df = v.prepare(base)

    y = _escrever_yaml(tmp_path, ["nu_idade_n", "idade_anos", "sin_semana", "cos_semana"],
                       ["febre", "dispneia", "faixa_etaria"])
    c2 = json.loads(json.dumps(cfg)); c2["dataset_analitico"]["path"] = str(tmp_path / "dataset.csv")
    rep = v.Report(tmp_path)
    metas, benchs = {}, {}

    for nome, spec in c2["experimentos_split"]["cenarios"].items():
        metas[nome] = v.a3_split_aleatorio_cenario(df, c2, rep, nome, spec["anos"], y)
        benchs[nome] = v.a3_benchmark_split(metas[nome]["arquivo"], y, c2, rep, nome, max_rows=8_000)
        assert {"aleatoria", "temporal_por_ordem"} == set(benchs[nome]["particao"])
        lg = benchs[nome][benchs[nome]["modelo"] == "logistica"]
        assert (lg["roc_auc"] > 0.6).all()      # sinal sintético (idade/dispneia) é aprendido

    t = v.comparar_cenarios(metas, benchs, rep)
    assert list(t["cenario"]) == ["todos_2019_2025", "sem_2020_2021"]
    assert t.loc[0, "n_linhas"] > t.loc[1, "n_linhas"]
    assert "pr_auc_aleatoria" in t.columns and "pr_auc_temporal_por_ordem" in t.columns


def test_graficos_do_split_sao_gerados(cfg, tmp_path):
    base = v.make_demo(n=12_000, inicio="2019-01-01", anos=7)[0]
    base.columns = [c.lower() for c in base.columns]
    df = v.prepare(base)

    y = _escrever_yaml(tmp_path, ["nu_idade_n"], ["febre", "dispneia"])
    c2 = json.loads(json.dumps(cfg)); c2["dataset_analitico"]["path"] = str(tmp_path / "dataset.csv")
    rep = v.Report(tmp_path)
    nomes = list(c2["experimentos_split"]["cenarios"])

    for nome in nomes:
        v.a3_split_aleatorio_cenario(df, c2, rep, nome, c2["experimentos_split"]["cenarios"][nome]["anos"], y)

    figs = tmp_path / "figs"
    pngs = [v.grafico_split_cenario(rep, c2, n, c2["experimentos_split"]["cenarios"][n]["anos"], figs) for n in nomes]
    pngs.append(v.grafico_comparacao_cenarios(rep, c2, nomes, figs))

    for p in pngs:
        assert p.exists() and p.stat().st_size > 10_000 and p.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert {p.name for p in pngs} == {"split_todos_2019_2025.png", "split_sem_2020_2021.png", "split_comparacao_cenarios.png"}


# ---------------------------------------------------------------------------
# A4 — tabela de decisão e registo
# ---------------------------------------------------------------------------

def test_decision_table_alerta_complexidade_sem_ganho(cfg, tmp_path):
    res = pd.DataFrame({"modelo": ["baseline"] * 2 + ["logistica"] * 2 + ["boosting"] * 2,
                        "pr_auc": [.15, .15, .40, .40, .401, .401], "roc_auc": [.5] * 2 + [.8] * 2 + [.8] * 2,
                        "brier": [.15] * 2 + [.10] * 2 + [.11] * 2})
    rep = v.Report(tmp_path)
    v.a4_decision_table(res, cfg, rep)
    t = pd.read_csv(tmp_path / "a4_tabela_decisao.csv")
    assert "não justifica" in t.loc[t["modelo"] == "boosting", "alertas_automaticos"].iloc[0]


def test_log_decision_upsert(tmp_path):
    v.log_decision(tmp_path, "D-01", "tema", "a")
    t = v.log_decision(tmp_path, "D-01", "tema", "b")
    assert len(t) == 1 and t.loc[0, "decisao"] == "b"


# ---------------------------------------------------------------------------
# Leitura compacta — colunas ``category``
# ---------------------------------------------------------------------------

def test_resultados_iguais_com_colunas_category(cfg, tmp_path):
    """O resultado do A1/A2 não muda quando o texto é lido como ``category``."""
    base = _base_texto()
    d_txt, d_cat = v.prepare(base.copy()), v.prepare(_como_categoria(base))
    r1, r2 = v.Report(tmp_path / "txt"), v.Report(tmp_path / "cat")

    wf1, wf2 = v.a1_waterfall(d_txt, cfg, r1), v.a1_waterfall(d_cat, cfg, r2)
    assert wf1[["n_excluido", "n_restante"]].equals(wf2[["n_excluido", "n_restante"]])

    c1, c2 = v.a1_cohort(d_txt, cfg), v.a1_cohort(d_cat, cfg)
    assert len(c1) == len(c2) and c1["_alvo"].sum() == c2["_alvo"].sum()

    for fn in (v.a2_missing, v.a2_dates, v.a2_duplicates, v.a2_maturity, v.a2_eligibility):
        fn(d_txt, cfg, r1)
        fn(d_cat, cfg, r2)

    d1 = pd.read_csv(tmp_path / "txt" / "a2_coerencia_datas.csv")
    d2 = pd.read_csv(tmp_path / "cat" / "a2_coerencia_datas.csv")
    assert d1[["regra", "n_violacoes"]].equals(d2[["regra", "n_violacoes"]])
    assert [f[2] for f in r1.findings] == [f[2] for f in r2.findings]


def test_export_e_vazamento_com_category(cfg, tmp_path):
    y = _escrever_yaml(tmp_path, ["nu_idade_n", "idade_anos"], ["febre", "faixa_etaria", "cs_sexo"])
    df = v.prepare(_como_categoria(_base_texto()))
    c2 = json.loads(json.dumps(cfg)); c2["dataset_analitico"]["path"] = str(tmp_path / "d.csv")
    rep = v.Report(tmp_path)

    meta = v.a3_split_aleatorio_cenario(df, c2, rep, "todos_2019_2025", [2019, 2020, 2021, 2022, 2023, 2024, 2025], y)
    assert meta["n_linhas"] > 0 and v.validar_contrato_c2(meta["arquivo"], y, rep) is True

    v.a3_leak_scan(v.a1_cohort(df, c2), c2, rep)
    assert not [f for f in rep.findings if f[2] == v.FAIL]


# ---------------------------------------------------------------------------
# Colunas necessárias do Parquet
# ---------------------------------------------------------------------------

def test_colunas_minimas_sao_menos_que_as_classificadas(cfg):
    schema = ["nu_notific", "hospital", "evolucao", "dt_interna", "dt_notific", "dt_sin_pri", "nu_idade_n", "tp_idade",
              "uti", "antiviral", "vacina_cov", "cs_raca", "coluna_x", "febre"]
    minimas = v.colunas_necessarias(schema, cfg, None, modo="minimas")
    classif = v.colunas_necessarias(schema, cfg, None, modo="classificadas")
    assert set(minimas) < set(classif)
    assert {"hospital", "evolucao", "dt_interna", "nu_idade_n", "tp_idade", "dt_sin_pri"} <= set(minimas)
    assert not ({"antiviral", "vacina_cov", "coluna_x"} & set(minimas))
    assert {"antiviral", "vacina_cov"} <= set(classif)
```

## `tests/test_reproducibility.py`

- Git: `tracked` · status `clean`
- Size: `5.1 KB` · modified `2026-10-16 14:54 UTC`
- SHA-256: `27ce4e8b0f95c728593a299998f26b53c8c39feb88b531a56c125f251acc6194`

```python
"""Testes do registro de execuções (``src.utils.reproducibility``)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from src.utils import config as C
from src.utils import reproducibility as R


# Campos que ``registrar_execucao`` deve sempre gravar no metadata.
# Serve como armadilha contra remoções silenciosas na estrutura do dict.
_CAMPOS_METADATA: tuple[str, ...] = (
    "run_id", "timestamp", "modelo", "seed", "status",
    "parametros", "dataset", "metricas", "features",
    "duracao_s", "erro", "data_version", "gates", "versoes",
    "git", "env", "notas", "dataset_sha256", "supervised_yaml_sha256",
)


def _ler_meta(pasta: Path) -> dict[str, Any]:
    """Lê ``metadata.json`` de uma execução."""
    return json.loads((pasta / "metadata.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# registrar_execucao — estrutura e conteúdo
# ---------------------------------------------------------------------------

def test_registrar_execucao_cria_pasta(tmp_path: Path) -> None:
    pasta = R.registrar_execucao(
        modelo="teste",
        seed=42,
        parametros={"C": 1.0},
        dataset={"nome": "srag", "n_rows": 100},
        metricas={"auc": 0.5},
        duracao_s=1.23,
        output_dir=tmp_path,
    )
    assert pasta.exists()
    assert (pasta / "metadata.json").exists()
    assert (pasta / "summary.txt").exists()


def test_metadata_tem_campos_obrigatorios(tmp_path: Path) -> None:
    pasta = R.registrar_execucao(
        modelo="teste",
        seed=7,
        parametros={"x": 1},
        metricas={"auc": 0.9},
        output_dir=tmp_path,
    )
    meta = _ler_meta(pasta)

    for chave in _CAMPOS_METADATA:
        assert chave in meta

    assert meta["seed"] == 7
    assert meta["modelo"] == "teste"
    assert meta["metricas"]["auc"] == 0.9


def test_metadata_grava_data_version(tmp_path: Path) -> None:
    pasta = R.registrar_execucao(modelo="dv", output_dir=tmp_path)
    assert _ler_meta(pasta)["data_version"] == C.DATA_VERSION


def test_metadata_grava_gates(tmp_path: Path) -> None:
    meta = _ler_meta(R.registrar_execucao(modelo="gates", output_dir=tmp_path))
    assert isinstance(meta["gates"], dict)
    assert "G9_holdout" in meta["gates"]


def test_seed_padrao_vem_do_config(tmp_path: Path) -> None:
    """Sem ``seed`` explícito, usa ``config.SEED``."""
    pasta = R.registrar_execucao(modelo="seed_default", output_dir=tmp_path)
    assert _ler_meta(pasta)["seed"] == C.SEED


# ---------------------------------------------------------------------------
# Run como context manager
# ---------------------------------------------------------------------------

def test_run_context_manager_sucesso(tmp_path: Path) -> None:
    r: R.Run | None = None
    with R.Run(modelo="ctx", seed=1, output_dir=tmp_path) as r:
        r.metrica(auc=0.77)
        r.anotar("nota de teste")

    assert r is not None
    assert r.pasta is not None
    meta = _ler_meta(r.pasta)
    assert meta["metricas"]["auc"] == 0.77
    assert "nota de teste" in meta["notas"]
    assert meta["duracao_s"] is not None
    assert meta["status"] == "success"
    assert meta["erro"] is None


def test_run_registra_excecao(tmp_path: Path) -> None:
    """Mesmo em exceção, o metadata é gravado — com status e erro."""
    r: R.Run | None = None
    with pytest.raises(RuntimeError, match="boom"):
        with R.Run(modelo="erro", output_dir=tmp_path) as r:
            raise RuntimeError("boom")

    assert r is not None
    assert r.pasta is not None
    meta = _ler_meta(r.pasta)
    assert meta["status"] == "error"
    assert meta["erro"]["tipo"] == "RuntimeError"
    assert "boom" in meta["erro"]["mensagem"]
    assert "Traceback" in meta["erro"]["traceback"]


def test_run_nao_suprime_excecao(tmp_path: Path) -> None:
    """O ``__exit__`` devolve ``False`` — a exceção propaga."""
    with pytest.raises(ValueError):
        with R.Run(modelo="propaga", output_dir=tmp_path):
            raise ValueError("propaga")


# ---------------------------------------------------------------------------
# gerar_run_id
# ---------------------------------------------------------------------------

def test_run_id_unico(tmp_path: Path) -> None:
    """Sufixo ``_NN`` evita colisão quando o ID base já existe."""
    a = R.gerar_run_id(modelo="dup", base_dir=tmp_path)
    (tmp_path / a).mkdir()
    b = R.gerar_run_id(modelo="dup", base_dir=tmp_path)
    assert a != b


# ---------------------------------------------------------------------------
# listar_runs / carregar_run
# ---------------------------------------------------------------------------

def test_listar_e_carregar(tmp_path: Path) -> None:
    R.registrar_execucao(modelo="a", output_dir=tmp_path)
    R.registrar_execucao(modelo="b", output_dir=tmp_path)

    runs = R.listar_runs(output_dir=tmp_path)
    assert len(runs) == 2

    meta = R.carregar_run(runs[0]["run_id"], output_dir=tmp_path)
    assert meta["modelo"] in {"a", "b"}
```

## `tests/test_smoke.py`

- Git: `tracked` · status `clean`
- Size: `3.2 KB` · modified `2026-10-16 14:54 UTC`
- SHA-256: `f3161fc26862baaf40b068430fdf0f334f7c016964efec5340d393f3fbe782bc`

```python
"""
Smoke tests do Parquet de SRAG.

Verificam que o dataset existe, abre, tem o schema esperado e produz uma
saída mínima. Todos os testes são marcados ``slow`` via ``pytestmark``.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
import pytest

from src.utils import storage


pytestmark = pytest.mark.slow


# Colunas mínimas esperadas no SRAG; ajustar conforme o dicionário de dados.
COLUNAS_ESPERADAS: frozenset[str] = frozenset({"sg_uf", "dt_notific"})


@pytest.fixture
def parquet(parquet_disponivel: Path | None) -> Path:
    """``parquet_disponivel`` obrigatório — faz skip se ausente."""
    if parquet_disponivel is None:
        pytest.skip(
            "Nenhum Parquet encontrado. Rode 00_acesso_dados_parquet.ipynb "
            "ou 01_extracao.ipynb primeiro."
        )
    return parquet_disponivel


@pytest.fixture(scope="module")
def schema_colunas(parquet: Path) -> set[str]:
    """Nome das colunas do Parquet — lido uma vez por módulo."""
    return set(pq.read_schema(parquet).names)


# ---------------------------------------------------------------------------
# Estrutura do arquivo
# ---------------------------------------------------------------------------

def test_parquet_existe_e_nao_vazio(parquet: Path) -> None:
    assert parquet.is_file()
    assert parquet.stat().st_size > 0


def test_parquet_tem_magic_bytes(parquet: Path) -> None:
    with open(parquet, "rb") as f:
        magic = f.read(4)
    assert magic == b"PAR1", f"Arquivo não é Parquet válido (magic={magic!r})"


def test_parquet_abre(schema_colunas: set[str]) -> None:
    assert schema_colunas


def test_parquet_tem_colunas_esperadas(schema_colunas: set[str]) -> None:
    faltando = COLUNAS_ESPERADAS - schema_colunas
    assert not faltando, f"Colunas ausentes: {sorted(faltando)}"


# ---------------------------------------------------------------------------
# Leitura via pandas
# ---------------------------------------------------------------------------

def test_parquet_tem_registros(parquet: Path) -> None:
    df = pd.read_parquet(parquet, columns=["sg_uf"])
    assert len(df) > 0


def test_produz_saida_pequena(parquet: Path) -> None:
    """O smoke final — produzir uma saída minúscula funciona ponta-a-ponta."""
    df = pd.read_parquet(parquet, columns=["sg_uf"]).head(10)
    assert len(df) == 10


# ---------------------------------------------------------------------------
# Leitura via storage.read_srag
# ---------------------------------------------------------------------------

def test_storage_read_srag(parquet: Path) -> None:
    """``storage.read_srag`` devolve DataFrame não vazio com as colunas pedidas."""
    df = storage.read_srag(columns=["sg_uf"])
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert "sg_uf" in df.columns


def test_storage_read_srag_com_filtro(parquet: Path) -> None:
    """O filtro ``sg_uf == "SP"`` é aplicado no lado do Parquet."""
    df = storage.read_srag(
        columns=["sg_uf"],
        filters=[("sg_uf", "==", "SP")],
    )
    if df.empty:
        pytest.skip("Nenhum registro de SP no dataset.")
    assert (df["sg_uf"] == "SP").all()
```

## `tests/test_split.py`

- Git: `tracked` · status `clean`
- Size: `9.4 KB` · modified `2026-10-16 14:54 UTC`
- SHA-256: `64427eee86a2c645dc367875cc93b984d65d716716fba3d1f498931894ab98e3`

```python
"""
Testes para ``src.data.split.criar_particoes_agrupadas``.

Invariantes:

1. nenhum grupo em mais de uma partição;
2. proporções de linhas próximas de 70/15/15 (com tolerância);
3. mesma seed → mesma partição.

Cobrem também políticas de estratos pequenos, grupos com alvo
heterogéneo (raise/warn) e validações de parâmetros/colunas.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import pytest

from src.data.split import (
    PARTICOES_CANONICAS,
    SplitWarning,
    criar_particoes_agrupadas,
)


# ---------------------------------------------------------------------------
# Fixtures sintéticas
# ---------------------------------------------------------------------------

def _df_estratificado(
    n_grupos_classe0: int = 30,
    n_grupos_classe1: int = 20,
    linhas_por_grupo: int = 3,
    seed: int = 0,
) -> pd.DataFrame:
    """DataFrame com grupos homogéneos (alvo constante por grupo)."""
    rng = np.random.default_rng(seed)
    linhas = []
    gid = 0
    for classe, n_grupos in [(0, n_grupos_classe0), (1, n_grupos_classe1)]:
        for _ in range(n_grupos):
            grupo = f"g{gid:04d}"
            gid += 1
            n = int(rng.integers(1, linhas_por_grupo + 1))
            for i in range(n):
                linhas.append({
                    "nu_notific": grupo,
                    "alvo": classe,
                    "valor": float(rng.normal()),
                    "idx_linha": i,
                })
    return pd.DataFrame(linhas)


def _df_grande(
    n_grupos_classe0: int = 700,
    n_grupos_classe1: int = 300,
) -> pd.DataFrame:
    """Base grande o suficiente para checar proporções com folga."""
    return _df_estratificado(
        n_grupos_classe0=n_grupos_classe0,
        n_grupos_classe1=n_grupos_classe1,
        linhas_por_grupo=2,
        seed=1,
    )


def _df_com_estrato_pequeno() -> pd.DataFrame:
    """1 grupo na classe 1 (estrato pequeno) + 20 grupos na classe 0."""
    return _df_estratificado(n_grupos_classe0=20, n_grupos_classe1=1)


def _df_com_grupo_heterogeneo() -> pd.DataFrame:
    """``g0000`` (classe 0) recebe uma linha com alvo=1."""
    df = _df_estratificado(n_grupos_classe0=20, n_grupos_classe1=10)
    idx = df.index[df["nu_notific"] == "g0000"][0]
    df.loc[idx, "alvo"] = 1
    return df


def _split(df: pd.DataFrame, **kwargs: Any) -> pd.DataFrame:
    """``criar_particoes_agrupadas`` com os defaults dos testes."""
    params: dict[str, Any] = {
        "target_column": "alvo",
        "group_column": "nu_notific",
        "partition_column": "particao",
    }
    params.update(kwargs)
    return criar_particoes_agrupadas(df, **params)


def _assert_proporcoes(contagem: pd.Series, tol: float = 0.05) -> None:
    """Asserts de 70/15/15 sobre ``value_counts(normalize=True)``."""
    assert abs(contagem["treino"] - 0.70) < tol, contagem
    assert abs(contagem["validacao"] - 0.15) < tol, contagem
    assert abs(contagem["teste"] - 0.15) < tol, contagem


# ---------------------------------------------------------------------------
# Invariantes de partição
# ---------------------------------------------------------------------------

def test_grupos_nao_cruzam_particoes() -> None:
    """Nenhum ``nu_notific`` aparece em mais de uma partição."""
    out = _split(_df_estratificado(), seed=42)
    grupos_por_particao = out.groupby("nu_notific", observed=True)["particao"].nunique()
    assert (grupos_por_particao == 1).all(), (
        f"Grupos em mais de uma partição:\n{grupos_por_particao[grupos_por_particao > 1]}"
    )


def test_nenhuma_linha_perdida() -> None:
    df = _df_estratificado()
    out = _split(df, seed=42)
    assert len(out) == len(df)
    assert set(out["particao"].unique()) == set(PARTICOES_CANONICAS)


# ---------------------------------------------------------------------------
# Proporções 70/15/15
# ---------------------------------------------------------------------------

def test_proporcoes_linhas_proximas_de_70_15_15() -> None:
    """Grupos são atómicos; a proporção real de linhas oscila em torno do alvo."""
    out = _split(_df_grande(), seed=42)
    _assert_proporcoes(out["particao"].value_counts(normalize=True))


def test_proporcoes_grupos_proximas_de_70_15_15() -> None:
    out = _split(_df_grande(), seed=42)
    por_grupo = out.groupby("nu_notific", observed=True)["particao"].first()
    _assert_proporcoes(por_grupo.value_counts(normalize=True))


def test_estratificacao_preserva_proporcao_aproximada() -> None:
    df = _df_estratificado(n_grupos_classe0=70, n_grupos_classe1=30)
    out = _split(df, seed=42)

    prevalencia_global = df["alvo"].mean()
    for particao in PARTICOES_CANONICAS:
        sub = out[out["particao"] == particao]
        assert abs(sub["alvo"].mean() - prevalencia_global) < 0.10


# ---------------------------------------------------------------------------
# Reprodutibilidade por seed
# ---------------------------------------------------------------------------

def test_reprodutibilidade_mesma_seed() -> None:
    """Mesma seed → mesmas partições."""
    df = _df_estratificado()
    a = _split(df, seed=7)
    b = _split(df, seed=7)
    pd.testing.assert_series_equal(a["particao"], b["particao"])


def test_seeds_diferentes_produzem_splits_diferentes() -> None:
    df = _df_estratificado()
    a = _split(df, seed=1)
    b = _split(df, seed=2)
    assert not a["particao"].equals(b["particao"])


# ---------------------------------------------------------------------------
# Estratos pequenos — 4 políticas
# ---------------------------------------------------------------------------

def test_estrato_pequeno_raise_e_default() -> None:
    with pytest.raises(ValueError, match="Estrato"):
        _split(_df_com_estrato_pequeno())


def test_estrato_pequeno_warn_teste_manda_para_teste() -> None:
    df = _df_com_estrato_pequeno()
    with pytest.warns(SplitWarning, match="Destinando ao teste"):
        out = _split(df, politica_estratos_pequenos="warn_teste")

    linhas_classe1 = out[out["alvo"] == 1]
    assert (linhas_classe1["particao"] == "teste").all()
    assert len(out) == len(df)


def test_estrato_pequeno_warn_treino_manda_para_treino() -> None:
    with pytest.warns(SplitWarning, match="Destinando ao treino"):
        out = _split(_df_com_estrato_pequeno(), politica_estratos_pequenos="warn_treino")

    linhas_classe1 = out[out["alvo"] == 1]
    assert (linhas_classe1["particao"] == "treino").all()


def test_estrato_pequeno_drop_remove_linhas() -> None:
    df = _df_com_estrato_pequeno()
    with pytest.warns(SplitWarning, match="Descartando"):
        out = _split(df, politica_estratos_pequenos="drop")

    assert (out["alvo"] == 1).sum() == 0
    assert len(out) < len(df)
    assert set(out["particao"].unique()).issubset(set(PARTICOES_CANONICAS))


# ---------------------------------------------------------------------------
# Grupos com alvo heterogéneo
# ---------------------------------------------------------------------------

def test_grupo_heterogeneo_raise() -> None:
    with pytest.raises(ValueError, match="mais de um valor distinto"):
        _split(_df_com_grupo_heterogeneo())


def test_grupo_heterogeneo_warn() -> None:
    with pytest.warns(SplitWarning, match="mais de um valor distinto"):
        _split(_df_com_grupo_heterogeneo(), on_grupo_alvo_heterogeneo="warn")


# ---------------------------------------------------------------------------
# Validação de parâmetros e colunas
# ---------------------------------------------------------------------------

def test_coluna_alvo_ausente() -> None:
    with pytest.raises(KeyError, match="alvo"):
        criar_particoes_agrupadas(
            _df_estratificado(),
            target_column="nao_existe",
            group_column="nu_notific",
        )


def test_coluna_grupo_ausente() -> None:
    with pytest.raises(KeyError, match="grupo"):
        criar_particoes_agrupadas(
            _df_estratificado(),
            target_column="alvo",
            group_column="nao_existe",
        )


def test_partition_column_ja_existente() -> None:
    df = _df_estratificado()
    df["particao"] = "treino"
    with pytest.raises(ValueError, match="já contém"):
        _split(df)


@pytest.mark.parametrize(
    "kwargs, match",
    [
        ({"frac_treino": 0.0}, "frac_treino"),
        ({"frac_validacao": 1.5}, "frac_validacao"),
        ({"frac_treino": 0.7, "frac_validacao": 0.4}, "< 1"),
    ],
    ids=["frac_treino_zero", "frac_validacao_acima", "soma_maior_que_1"],
)
def test_frac_invalida(kwargs: dict, match: str) -> None:
    with pytest.raises(ValueError, match=match):
        _split(_df_estratificado(), **kwargs)


def test_min_grupos_abaixo_de_3() -> None:
    with pytest.raises(ValueError, match="min_grupos_por_estrato"):
        _split(_df_estratificado(), min_grupos_por_estrato=2)


def test_politica_invalida() -> None:
    # Valor viola intencionalmente o Literal PoliticaEstratosPequenos.
    with pytest.raises(ValueError, match="politica_estratos_pequenos"):
        _split(_df_estratificado(), politica_estratos_pequenos="qualquer_coisa")  # type: ignore[arg-type]


def test_df_vazio() -> None:
    with pytest.raises(ValueError, match="vazio"):
        _split(pd.DataFrame({"alvo": [], "nu_notific": []}))
```

## `tests/test_supervised_artifact.py`

- Git: `tracked` · status `clean`
- Size: `6.3 KB` · modified `2026-10-18 16:24 UTC`
- SHA-256: `dd247e633bde059ab55d43a9dc86cdfec54f5b363452f9295f71944d2f81d544`

```python
"""Testes do artefato supervisionado (``src.data.supervised_artifact``).

Cobrem persistência, leitura, validação do tipo de coorte, exigência das
três partições na gravação e a trava do gate ``G9_holdout`` sobre a
partição de teste na leitura (#16).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from src.data.supervised_artifact import (
    GatePendenteError,
    holdout_partition,
    load_supervised_artifact,
    persist_supervised_artifact,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _frame() -> pd.DataFrame:
    """6 registos — 2 por partição, alvo alternado (0/1)."""
    return pd.DataFrame({
        "idade_anos":      [10.0, 20.0, 30.0, 40.0, 50.0, 60.0],
        "alvo_obito_srag": [0, 1, 0, 1, 0, 1],
        "particao":        ["treino", "treino", "validacao", "validacao", "teste", "teste"],
    })


def _persistir(tmp_path: Path, frame: pd.DataFrame, **kwargs: Any) -> None:
    """Grava ``frame`` com kwargs obrigatórios mínimos; ``**kwargs`` sobrepõe."""
    params: dict[str, Any] = {
        "source":           {},
        "feature_columns":  ["idade_anos"],
        "target_column":    "alvo_obito_srag",
        "partition_column": "particao",
        "cohort_kind":      "provisional",
        "seed":             42,
    }
    params.update(kwargs)
    persist_supervised_artifact(frame, root=tmp_path, **params)


@pytest.fixture
def g9_aprovado(monkeypatch: pytest.MonkeyPatch) -> None:
    """``exigir_gate`` aceita qualquer gate (G9 aprovado)."""
    monkeypatch.setattr("src.utils.config.gate_aprovado", lambda _nome: True)


@pytest.fixture
def g9_pendente(monkeypatch: pytest.MonkeyPatch) -> None:
    """``exigir_gate`` rejeita qualquer gate (G9 pendente)."""
    monkeypatch.setattr("src.utils.config.gate_aprovado", lambda _nome: False)


# ---------------------------------------------------------------------------
# Persistência
# ---------------------------------------------------------------------------

def test_persistencia_exige_tres_particoes(tmp_path: Path) -> None:
    """Gravar sem ``teste`` viola o contrato de partições."""
    with pytest.raises(ValueError, match="Particoes esperadas"):
        _persistir(tmp_path, _frame().query("particao != 'teste'"))


# ---------------------------------------------------------------------------
# Round-trip
# ---------------------------------------------------------------------------

def test_default_nao_carrega_teste(tmp_path: Path) -> None:
    """Por omissão, o loader devolve apenas treino+validação."""
    _persistir(tmp_path, _frame(), source={"kind": "provisional", "sha256": "abc"})

    loaded, manifest = load_supervised_artifact(tmp_path, expected_kind="provisional")

    assert set(loaded["particao"]) == {"treino", "validacao"}
    assert manifest["test_opened"] is False
    assert manifest["seed"] == 42


def test_roundtrip_completo_apos_g9(tmp_path: Path, g9_aprovado: None) -> None:
    """Com G9 aprovado e ``partitions`` explícito, o teste entra no round-trip."""
    frame = _frame()
    _persistir(tmp_path, frame)

    loaded, _ = load_supervised_artifact(
        tmp_path, partitions=("treino", "validacao", "teste"),
    )

    assert loaded["particao"].tolist() == frame["particao"].tolist()


# ---------------------------------------------------------------------------
# Tipo de coorte
# ---------------------------------------------------------------------------

def test_tipo_de_coorte_incorreto_falha(tmp_path: Path) -> None:
    """``expected_kind`` divergente falha antes de tocar nos dados."""
    _persistir(tmp_path, _frame())

    with pytest.raises(RuntimeError, match="SRAG_COHORT_KIND"):
        load_supervised_artifact(tmp_path, expected_kind="final")


# ---------------------------------------------------------------------------
# Trava do gate G9 (#16)
# ---------------------------------------------------------------------------

def test_default_funciona_com_g9_pendente(tmp_path: Path, g9_pendente: None) -> None:
    """Sem ``teste`` na seleção, o loader não consulta o gate."""
    _persistir(tmp_path, _frame())

    loaded, _ = load_supervised_artifact(tmp_path)

    assert set(loaded["particao"]) == {"treino", "validacao"}


def test_load_com_teste_sem_g9_falha(tmp_path: Path, g9_pendente: None) -> None:
    """Pedir ``teste`` sem G9 aprovado levanta antes de materializar o bloco."""
    _persistir(tmp_path, _frame())

    with pytest.raises(GatePendenteError, match="G9_holdout"):
        load_supervised_artifact(
            tmp_path, partitions=("treino", "validacao", "teste"),
        )


def test_holdout_partition_sem_g9_falha(tmp_path: Path, g9_pendente: None) -> None:
    """``holdout_partition`` revalida o gate (defesa em profundidade)."""
    _persistir(tmp_path, _frame())
    loaded, manifest = load_supervised_artifact(tmp_path)

    with pytest.raises(GatePendenteError, match="G9_holdout"):
        holdout_partition(loaded, manifest)


def test_holdout_partition_apos_g9(tmp_path: Path, g9_aprovado: None) -> None:
    """Com G9 aprovado, ``holdout_partition`` devolve o bloco de teste."""
    _persistir(tmp_path, _frame())
    loaded, manifest = load_supervised_artifact(
        tmp_path, partitions=("treino", "validacao", "teste"),
    )

    teste = holdout_partition(loaded, manifest)

    assert set(teste["particao"]) == {"teste"}
    assert len(teste) == 2


# ---------------------------------------------------------------------------
# Validação de ``partitions``
# ---------------------------------------------------------------------------

def test_partitions_vazias_falham(tmp_path: Path) -> None:
    _persistir(tmp_path, _frame())

    with pytest.raises(ValueError, match="partitions.*vazio"):
        load_supervised_artifact(tmp_path, partitions=())


def test_partitions_desconhecidas_falham(tmp_path: Path) -> None:
    _persistir(tmp_path, _frame())

    with pytest.raises(ValueError, match="Particoes desconhecidas"):
        load_supervised_artifact(tmp_path, partitions=("treino", "foo"))
```

## `tests/test_target.py`

- Git: `tracked` · status `clean`
- Size: `3.7 KB` · modified `2026-10-16 14:54 UTC`
- SHA-256: `d85c2169acc6f5354bd755e57e581a19a479be160515fcbac3260b4fcfb21aa7`

```python
"""Contrato do alvo binário: ``evolucao`` → {0, 1, NaN}."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.models.pipeline import criar_alvo_binario, filtrar_rotulos_validos
from src.utils import config as C


def _df(valores: list[float | None]) -> pd.DataFrame:
    """DataFrame ``{"evolucao": valores, "feat": range(n)}``.

    A coluna ``feat`` serve como índice rastreável nas asserts.
    """
    return pd.DataFrame({"evolucao": valores, "feat": range(len(valores))})


# ---------------------------------------------------------------------------
# Mapeamento evolucao → {0, 1, NaN}
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ([2.0],       [1.0]),
        ([1.0],       [0.0]),
        ([3.0],       [float("nan")]),
        ([9.0],       [float("nan")]),
        ([np.nan],    [float("nan")]),
    ],
    ids=["positivo", "negativo", "codigo_3", "codigo_9", "nan_entrada"],
)
def test_mapeamento_puro(entrada, esperado) -> None:
    """``2.0``→1, ``1.0``→0, qualquer outro→NaN."""
    y = criar_alvo_binario(_df(entrada))
    for obtido, esperado_valor in zip(y, esperado):
        if pd.isna(esperado_valor):
            assert pd.isna(obtido)
        else:
            assert obtido == esperado_valor


def test_mistura_completa() -> None:
    y = criar_alvo_binario(_df([1.0, 2.0, 3.0, 9.0, np.nan]))
    assert y.iloc[0] == 0.0
    assert y.iloc[1] == 1.0
    assert y.iloc[2:].isna().all()


# ---------------------------------------------------------------------------
# filtrar_rotulos_validos
# ---------------------------------------------------------------------------

def test_filtrar_remove_nan() -> None:
    df = _df([1.0, 2.0, 3.0, 9.0, np.nan])
    X_ok, y_ok = filtrar_rotulos_validos(df[["feat"]], criar_alvo_binario(df))

    assert len(y_ok) == 2
    assert y_ok.dtype == np.int8
    assert y_ok.tolist() == [0, 1]
    assert list(X_ok["feat"]) == [0, 1]


def test_filtrar_exige_indice_alinhado() -> None:
    X = pd.DataFrame({"feat": [1, 2]}, index=[0, 1])
    y = pd.Series([0, 1], index=[1, 2])
    with pytest.raises(ValueError, match="mesmo índice"):
        filtrar_rotulos_validos(X, y)


# ---------------------------------------------------------------------------
# Validação de argumentos
# ---------------------------------------------------------------------------

def test_positivos_e_negativos_nao_se_sobrepoem() -> None:
    with pytest.raises(ValueError, match="sobrepor"):
        criar_alvo_binario(_df([1.0, 2.0]), positivos=[1.0, 2.0], negativos=[1.0])


def test_positivos_vazio_levanta() -> None:
    with pytest.raises(ValueError, match="positivos"):
        criar_alvo_binario(_df([1.0, 2.0]), positivos=[], negativos=[1.0])


def test_negativos_vazio_levanta() -> None:
    with pytest.raises(ValueError, match="negativos"):
        criar_alvo_binario(_df([1.0, 2.0]), positivos=[2.0], negativos=[])


# ---------------------------------------------------------------------------
# Default vem do YAML
# ---------------------------------------------------------------------------

def test_default_vem_do_yaml() -> None:
    """Sem argumentos, usa ``target.positivos`` e ``target.negativos`` do YAML."""
    pos = C.cfg("target", "positivos")
    neg = C.cfg("target", "negativos")
    assert pos, "target.positivos precisa estar definido no YAML"
    assert neg, "target.negativos precisa estar definido no YAML"

    y = criar_alvo_binario(_df([float(pos[0]), float(neg[0])]))
    assert y.tolist() == [1.0, 0.0]
```

## `tests/test_temporal.py`

- Git: `tracked` · status `clean`
- Size: `5.9 KB` · modified `2026-10-16 14:54 UTC`
- SHA-256: `8f3be3964a5456ddc4a6588aafc2c382e7525bc613eb9bb1d2ca25cd41a93fd0`

```python
"""
Testes do split temporal em três blocos e da trava do holdout.

Cobrem garantia de não sobreposição temporal, validação de frações e
coluna temporal, tratamento de ``NaT`` e liberação do holdout apenas com
``G9_holdout`` aprovado.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.evaluation.temporal import TemporalSplit, split_temporal_3way
from src.utils import config as C


@pytest.fixture
def df_temporal() -> pd.DataFrame:
    """100 dias consecutivos a partir de 2020-01-01, coluna ``x`` = range(100)."""
    return pd.DataFrame({
        "data": pd.date_range("2020-01-01", periods=100, freq="D"),
        "x":    range(100),
    })


@pytest.fixture
def df_temporal_com_nat(df_temporal: pd.DataFrame) -> pd.DataFrame:
    """``df_temporal`` com ``NaT`` na linha 5 da coluna ``data``."""
    df = df_temporal.copy()
    df.loc[5, "data"] = pd.NaT
    return df


# ---------------------------------------------------------------------------
# split_temporal_3way — ordem e proporções
# ---------------------------------------------------------------------------

def test_split_temporal_ordem_correta(df_temporal: pd.DataFrame) -> None:
    """Sem sobreposição temporal entre blocos; proporções 70/15/15."""
    treino, validacao, holdout = split_temporal_3way(df_temporal, "data")

    assert treino["data"].max() <= validacao["data"].min()
    assert validacao["data"].max() <= holdout["data"].min()
    assert len(treino) == 70
    assert len(validacao) == 15
    assert len(holdout) == 15


def test_split_temporal_preserva_ordem(df_temporal: pd.DataFrame) -> None:
    treino, validacao, holdout = split_temporal_3way(df_temporal, "data")

    assert treino["data"].is_monotonic_increasing
    assert validacao["data"].is_monotonic_increasing
    assert holdout["data"].is_monotonic_increasing


# ---------------------------------------------------------------------------
# split_temporal_3way — validações de parâmetros
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "kwargs",
    [
        {"frac_treino": 0},
        {"frac_treino": 1},
        {"frac_validacao": 0},
        {"frac_validacao": 1},
        {"frac_treino": 0.8, "frac_validacao": 0.3},
    ],
    ids=[
        "frac_treino_zero",
        "frac_treino_um",
        "frac_validacao_zero",
        "frac_validacao_um",
        "soma_maior_que_1",
    ],
)
def test_fracoes_invalidas(df_temporal: pd.DataFrame, kwargs: dict) -> None:
    with pytest.raises(ValueError):
        split_temporal_3way(df_temporal, "data", **kwargs)


def test_coluna_tempo_ausente(df_temporal: pd.DataFrame) -> None:
    with pytest.raises(KeyError):
        split_temporal_3way(df_temporal, "coluna_inexistente")


def test_coluna_tempo_nao_datetime(df_temporal: pd.DataFrame) -> None:
    df = df_temporal.copy()
    df["data"] = df["data"].astype(str)
    with pytest.raises(TypeError):
        split_temporal_3way(df, "data")


# ---------------------------------------------------------------------------
# split_temporal_3way — tratamento de NaT
# ---------------------------------------------------------------------------

def test_on_nat_raise(df_temporal_com_nat: pd.DataFrame) -> None:
    with pytest.raises(ValueError):
        split_temporal_3way(df_temporal_com_nat, "data", on_nat="raise")


def test_on_nat_drop(df_temporal_com_nat: pd.DataFrame) -> None:
    treino, validacao, holdout = split_temporal_3way(
        df_temporal_com_nat, "data", on_nat="drop",
    )
    assert len(treino) + len(validacao) + len(holdout) == 99


def test_on_nat_invalido(df_temporal: pd.DataFrame) -> None:
    # Valor viola intencionalmente o Literal OnNat.
    with pytest.raises(ValueError):
        split_temporal_3way(df_temporal, "data", on_nat="ignorar")  # type: ignore[arg-type]


def test_dataset_pequeno() -> None:
    df = pd.DataFrame({"data": pd.date_range("2020-01-01", periods=2)})
    with pytest.raises(ValueError):
        split_temporal_3way(df, "data")


# ---------------------------------------------------------------------------
# TemporalSplit — trava do holdout
# ---------------------------------------------------------------------------

def test_holdout_bloqueado_por_padrao(df_temporal: pd.DataFrame) -> None:
    split = TemporalSplit(df_temporal, "data")
    assert not split.holdout_liberado
    with pytest.raises(RuntimeError):
        split.holdout()


def test_holdout_liberado_apos_gate(
    df_temporal: pd.DataFrame,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Com ``G9_holdout`` aprovado, ``concluir_selecao()`` libera o holdout."""
    monkeypatch.setattr(C, "cfg", lambda *a, **kw: {"status": "aprovado"})

    split = TemporalSplit(df_temporal, "data")
    split.concluir_selecao()

    assert split.holdout_liberado
    assert len(split.holdout()) == 15


def test_holdout_bloqueado_sem_gate(
    df_temporal: pd.DataFrame,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Com ``G9_holdout`` pendente, ``concluir_selecao()`` levanta ``RuntimeError``."""
    monkeypatch.setattr(C, "cfg", lambda *a, **kw: {"status": "pendente"})

    split = TemporalSplit(df_temporal, "data")
    with pytest.raises(RuntimeError):
        split.concluir_selecao()


def test_treino_validacao_nao_expoe_holdout(df_temporal: pd.DataFrame) -> None:
    split = TemporalSplit(df_temporal, "data")
    treino, validacao = split.treino_validacao()

    assert treino is split.treino
    assert validacao is split.validacao


def test_resumo_marca_holdout_bloqueado(df_temporal: pd.DataFrame) -> None:
    resumo = TemporalSplit(df_temporal, "data").resumo()

    assert "treino" in resumo
    assert "validacao" in resumo
    assert "holdout" in resumo
    assert "bloqueado" in resumo
```

## `tools/clean_project.py`

- Git: `tracked` · status `clean`
- Size: `3.7 KB` · modified `2026-10-16 14:54 UTC`
- SHA-256: `06775202d5495fc9c9bbe917b343da103153ec1a1c491c20b34c8e3cdd7260d6`

```python
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DIRECTORIES_TO_CLEAN = [
    "outputs",
    "reports",
    "models",
    "logs",
    ".pytest_cache",
    ".ipynb_checkpoints",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".nox",
]

FILE_PATTERNS = [
    "*.png", "*.jpg", "*.jpeg", "*.gif", "*.svg",
    "*.log", "*.tmp",
    "*.joblib", "*.pkl", "*.pickle",
    "*.h5", "*.hdf5",
    "*.pt", "*.pth", "*.onnx",
    "*.npy", "*.npz",
]

PROTECTED_FOLDERS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "notebooks",
    "src",
    "tests",
    "tools",
    "configs",
    "docs",
    "data/raw",
    "data/analytical",
    "data/external",
}


def remove_file(path: Path, dry_run: bool) -> None:
    if dry_run:
        print(f"[DRY RUN] FILE  {path}")
        return
    path.unlink(missing_ok=True)
    print(f"[REMOVED] FILE  {path}")


def remove_directory(path: Path, dry_run: bool) -> None:
    if dry_run:
        print(f"[DRY RUN] DIR   {path}")
        return
    shutil.rmtree(path, ignore_errors=True)
    print(f"[REMOVED] DIR   {path}")


def clean_directory_contents(path: Path, dry_run: bool) -> None:
    """Remove conteúdo mas preserva o diretório e os .gitkeep."""
    if not path.exists():
        return
    for child in path.iterdir():
        if child.name == ".gitkeep":
            continue
        if child.is_dir():
            remove_directory(child, dry_run)
        else:
            remove_file(child, dry_run)


def clean_directories(dry_run: bool) -> None:
    for directory in DIRECTORIES_TO_CLEAN:
        path = PROJECT_ROOT / directory
        if path.exists():
            clean_directory_contents(path, dry_run)


def clean_pycache(dry_run: bool) -> None:
    for cache_dir in PROJECT_ROOT.rglob("__pycache__"):
        remove_directory(cache_dir, dry_run)


def clean_generated_files(dry_run: bool) -> None:
    for pattern in FILE_PATTERNS:
        for file_path in PROJECT_ROOT.rglob(pattern):
            if any(protected in str(file_path) for protected in PROTECTED_FOLDERS):
                continue
            remove_file(file_path, dry_run)


def clean_processed_data(dry_run: bool) -> None:
    processed_folder = PROJECT_ROOT / "data" / "processed"
    if processed_folder.exists():
        clean_directory_contents(processed_folder, dry_run)


def clean_reference(dry_run: bool) -> None:
    for name in ("PROJECT_COMPLETE_REFERENCE.md", "PROJECT_COMPLETE_REFERENCE.json"):
        path = PROJECT_ROOT / "docs" / name
        if path.exists():
            remove_file(path, dry_run)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Limpa artefactos gerados sem tocar em código, configs ou dados originais."
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Mostra o que seria removido sem apagar.")
    parser.add_argument("--clean-processed", action="store_true",
                        help="Remove data/processed (obriga a re-download do Parquet).")
    parser.add_argument("--clean-reference", action="store_true",
                        help="Remove docs/PROJECT_COMPLETE_REFERENCE.{md,json}.")
    args = parser.parse_args()

    clean_directories(args.dry_run)
    clean_pycache(args.dry_run)
    clean_generated_files(args.dry_run)

    if args.clean_processed:
        clean_processed_data(args.dry_run)

    if args.clean_reference:
        clean_reference(args.dry_run)

    print("\nLimpeza concluída.")


if __name__ == "__main__":
    main()
```

## `tools/comparar_saidas.py`

- Git: `tracked` · status `clean`
- Size: `1.2 KB` · modified `2026-10-18 14:26 UTC`
- SHA-256: `0d6c1af4da97aad39c1f19408e40692ad94625d5863d69251260db35c5bd4dd0`

```python
from pathlib import Path
import sys, numpy as np, pandas as pd

def comparar(a,b,rtol=1e-6):
    rows=[]
    for pa in sorted(Path(a).glob("*.csv")):
        pb=Path(b)/pa.name
        if not pb.exists(): rows.append((pa.name,"ausente_depois",None)); continue
        x=pd.read_csv(pa,encoding="utf-8-sig"); y=pd.read_csv(pb,encoding="utf-8-sig")
        if x.shape!=y.shape or list(x.columns)!=list(y.columns): rows.append((pa.name,"estrutura_diferente",f"{x.shape} x {y.shape}")); continue
        dif=0
        for c in x.columns:
            if pd.api.types.is_numeric_dtype(x[c]) and pd.api.types.is_numeric_dtype(y[c]):
                iguais=np.isclose(x[c],y[c],rtol=rtol,equal_nan=True)
            else: iguais=x[c].astype("string").fillna("<NA>").eq(y[c].astype("string").fillna("<NA>")).to_numpy()
            dif+=int((~iguais).sum())
        rows.append((pa.name,"igual" if dif==0 else "diferente",f"{dif} células diferentes"))
    return pd.DataFrame(rows,columns=["arquivo","status","detalhe"])
if __name__=="__main__":
    r=comparar(sys.argv[1],sys.argv[2]); print(r.to_string(index=False)); raise SystemExit(0 if (r.status=="igual").all() else 1)
```

## `tools/update_project_reference.py`

- Git: `tracked` · status `clean`
- Size: `106.9 KB` · modified `2026-10-18 15:51 UTC`
- SHA-256: `e5f2dfbc4339ad587b51626d3d1bfa5715e000624e0658e91fd314aca5c29acf`

```python
#!/usr/bin/env python3
r"""Generate a complete, AI-oriented diagnostic snapshot of the SRAG repository.

Run from anywhere inside the repository, preferably with the project venv
(so installed package versions are the real ones):

    .\.venv\Scripts\python.exe tools\update_project_reference.py
    .\.venv\Scripts\python.exe tools\update_project_reference.py --split-mb 4
    .\.venv\Scripts\python.exe tools\update_project_reference.py --run-tests --pytest-args "-m 'not slow'"

Creates (default):

    docs/PROJECT_COMPLETE_REFERENCE.md     full human/AI-readable snapshot
    docs/PROJECT_COMPLETE_REFERENCE.json   machine-readable summary
    docs/project_reference_parts/          the same Markdown split into parts
                                           (default 1 MB each; --no-split to disable)

What the snapshot contains
--------------------------
1.  Git state: branch, commit, remote, status, recent log, diff stat and the
    optional uncommitted diff, disabled by default for speed.
2.  Full path inventory of the working folder, including ignored and local
    folders (data/, outputs/, models/, reports/), with size, modification time
    and Git state. File contents of data are never copied.
3.  Full, untruncated source of every relevant text file: .py, .ipynb, .md, .yaml, .yml,
    .toml, .json, .csv (capped), .txt, .ini, .cfg, .ps1, .sh, .sql, etc.
4.  Notebooks: every cell source, execution counts and, by default, the TEXT
    outputs (streams, text/plain results, errors and tracebacks). Images and
    HTML are replaced by placeholders. Execution order problems are reported.
5.  Optional small text artifacts produced by the project (manifests, waterfalls,
    summary tables under outputs/, reports/, data/ manifests), capped by size
    and number of CSV rows. Prediction folders are never included.
6.  Text extracted from .docx and .pptx documents (plans, reports).
7.  Python environment: interpreter, platform and every installed package
    version (scikit-learn, pandas, numpy, ...).
8.  Parsed configuration: full YAML summary, gates table, duplicate YAML keys,
    pyproject.toml validity and dependency lists.
9.  Static API catalog: every module, function, class, method, signature,
    docstring, consumers and tests.
10. Static diagnostics ("attention report"), including:
    - internal imports of modules or names that do not exist;
    - calls to project functions with keyword arguments they do not accept
      or with too many positional arguments;
    - gate names used in code/docs that are absent from the YAML;
    - YAML keys never referenced by code (possible dead configuration);
    - feature contract problems (forbidden features, derived features);
    - third-party imports missing from requirements.txt/pyproject.toml and
      unpinned dependencies;
    - duplicated symbols and notebook-local functions duplicating src/;
    - notebooks executed out of order, never executed, or with saved errors;
    - documents pointing to paths that do not exist;
    - mojibake/encoding problems; TODO/FIXME markers;
    - untracked relevant files.
11. Optional: pytest results (--run-tests). This is the only option that
    imports and executes project code.

Safety
------
Secrets and credentials are redacted. Absolute local paths are replaced by
<REPO> and <HOME>. .env files and binary data (Parquet, models, images) are
never copied. Notebook outputs can be disabled with --no-notebook-outputs.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.metadata as importlib_metadata
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None

try:
    import tomllib  # Python 3.11+
except Exception:  # pragma: no cover
    tomllib = None

SCHEMA_VERSION = 6

OUTPUT_DIR = Path("docs")
OUTPUT_MD_NAME = "PROJECT_COMPLETE_REFERENCE.md"
OUTPUT_JSON_NAME = "PROJECT_COMPLETE_REFERENCE.json"
PARTS_DIR_NAME = "project_reference_parts"

DEFAULT_MAX_INLINE_BYTES = 4_000_000
DEFAULT_MAX_OUTPUT_CHARS = 6_000
DEFAULT_MAX_ARTIFACT_BYTES = 300_000
DEFAULT_MAX_CSV_ROWS = 60
DEFAULT_MAX_DIFF_CHARS = 400_000
DEFAULT_GIT_LOG = 10
DEFAULT_SPLIT_MB = 1.0
MAX_INVENTORY_ENTRIES = 30_000
MAX_DOCSTRING_CHARS = 4_000
MAX_SOURCE_LINES_PER_LARGE_NOTEBOOK_CELL = 200

# Never walked (tooling, caches, virtual environments).
EXCLUDED_DIRS_ANYWHERE = {
    ".git", ".venv", "venv", "env", ".env", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", ".tox", ".nox", ".ipynb_checkpoints",
    "node_modules", ".idea", ".vscode", "site-packages", ".eggs",
    "build", "dist",
}
# Walked for the path inventory and small text artifacts, never as source.
ARTIFACT_DIRS_AT_ROOT = {
    "data", "outputs", "models", "logs", "artifacts", "mlruns", "reports",
}
# Never copied, even when small and textual.
ARTIFACT_EXCLUDED_DIR_NAMES = {"predictions", "predicoes", "raw", "cache", "tmp"}
EXCLUDED_FILES = {
    ".env", "pip_inspect-venv.json", OUTPUT_MD_NAME, OUTPUT_JSON_NAME,
}
# Files whose existence and keys are reported, but whose values are redacted.
KEYS_ONLY_FILES = {"paths.local.json"}

TEXT_SUFFIXES = {
    ".py", ".pyi", ".md", ".rst", ".txt", ".yaml", ".yml", ".toml", ".ini",
    ".cfg", ".json", ".json5", ".sql", ".ps1", ".psm1", ".sh", ".bat",
    ".cmd", ".csv", ".tsv", ".html", ".css", ".js", ".r", ".R",
}
ARTIFACT_TEXT_SUFFIXES = {".json", ".yaml", ".yml", ".md", ".txt", ".csv", ".tsv", ".log"}
OFFICE_SUFFIXES = {".docx", ".pptx"}
SPECIAL_NAMES = {
    "README", "LICENSE", "Makefile", "Dockerfile", "requirements.txt",
    "pyproject.toml", "pytest.ini", "setup.cfg", "tox.ini", ".env.example",
    ".gitignore", ".gitattributes", ".pre-commit-config.yaml", "environment.yml",
}
LANG = {
    ".py": "python", ".pyi": "python", ".md": "markdown", ".rst": "rst",
    ".yaml": "yaml", ".yml": "yaml", ".toml": "toml", ".json": "json",
    ".json5": "json5", ".ini": "ini", ".cfg": "ini", ".sql": "sql",
    ".ps1": "powershell", ".psm1": "powershell", ".sh": "bash", ".bat": "bat",
    ".cmd": "bat", ".csv": "csv", ".tsv": "tsv", ".html": "html", ".css": "css",
    ".js": "javascript", ".log": "text", ".r": "r",
}
LIKELY_BINARY_SUFFIXES = {
    ".parquet", ".feather", ".arrow", ".pkl", ".pickle", ".joblib", ".onnx",
    ".pt", ".pth", ".h5", ".hdf5", ".npy", ".npz", ".pdf", ".doc", ".ppt",
    ".xls", ".xlsx", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".zip",
    ".7z", ".gz", ".tar", ".bz2", ".xz", ".dbf", ".db", ".sqlite", ".exe", ".dll",
}
IMPORTANT_UNTRACKED_PREFIXES = (
    "src/", "tests/", "configs/", "docs/", "notebooks/", "tools/", "scripts/",
)

# Import name -> distribution name, for the dependency check.
IMPORT_TO_DIST = {
    "sklearn": "scikit-learn", "yaml": "pyyaml", "dotenv": "python-dotenv",
    "PIL": "pillow", "cv2": "opencv-python", "bs4": "beautifulsoup4",
    "docx": "python-docx", "pptx": "python-pptx", "dateutil": "python-dateutil",
    "IPython": "ipython", "jwt": "pyjwt", "skimage": "scikit-image",
    "google": "google-api-python-client", "snowflake": "snowflake-connector-python",
}
KEY_PACKAGES = (
    "scikit-learn", "pandas", "numpy", "scipy", "pyarrow", "pyyaml", "joblib",
    "matplotlib", "seaborn", "python-dotenv", "requests", "pytest",
    "ipykernel", "jupyter", "nbformat", "statsmodels", "shap",
)

ENV_RE = re.compile(
    r"(?:os\.getenv|os\.environ\.get|os\.environ\[|get_env|get_secret|getenv)"
    r"\(?\s*['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]"
)
SECRET_RE = re.compile(
    r"(?im)^(\s*[A-Za-z_][A-Za-z0-9_.-]*?"
    r"(?:token|secret|password|passwd|pwd|api[_-]?key|private[_-]?key|credential)"
    r"[A-Za-z0-9_.-]*\s*[:=]\s*)([^\n#]+)"
)
PRIVATE_KEY_RE = re.compile(
    r"-----BEGIN [^-]+ PRIVATE KEY-----.*?-----END [^-]+ PRIVATE KEY-----",
    re.DOTALL,
)
URL_CREDENTIAL_RE = re.compile(r"(?i)(https?://[^\s/:]+:)([^@\s]+)(@)")
GITHUB_TOKEN_RE = re.compile(r"\b(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b")
WINDOWS_USER_RE = re.compile(r"(?i)\b[A-Z]:[\\/]+Users[\\/]+[^\\/\s\"'<>|]+")
POSIX_HOME_RE = re.compile(r"(?<![A-Za-z0-9_])/(?:home|Users)/[^/\s\"'<>|]+")
ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
BACKTICK_RUN_RE = re.compile(r"`+")
HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
FILE_LITERAL_RE = re.compile(
    r"['\"]([^'\"\n]+\.(?:parquet|csv|json|yaml|yml|joblib|pkl|png|jpg|md|html|txt))['\"]",
    re.IGNORECASE,
)
GATE_RE = re.compile(r"\bG\d+_[A-Za-z0-9_]+\b")
TODO_RE = re.compile(r"(?i)\b(TODO|FIXME|XXX|HACK|PENDENTE)\b[:\s-]*(.{0,140})")
MOJIBAKE_RE = re.compile(r"(?:├|┤|Ã[\u0080-\u00BF¡-¿]|Â[\u00A0-\u00BF ]|â€|\uFFFD)")

CONTEXT = """# Project Complete Reference

> **Generated file. Do not edit manually.**
> Generated by `tools/update_project_reference.py` (schema v{schema}).
> Static snapshot of the repository and of the local working folder.

## 1. Purpose

This reference lets a person or an AI continue the SRAG project without prior
conversation context and without access to the machine. It prioritizes the full,
untruncated source of Python files, notebooks, tests, configuration and project
documentation, plus fast structural diagnostics that prevent duplicated functions,
conflicting pipelines and patchwork implementations.

## 2. Methodological guardrails

- Academic retrospective prediction project, not a clinically validated tool.
- Prediction time is hospital admission; later information cannot be a feature.
- Do not make causal claims from predictive associations.
- Never use the final test partition for model, hyperparameter, calibration or
  threshold selection.
- Partition, target, features, seed, calibration, threshold and gates come from
  `configs/supervised.yaml` and executable tests.
- Original data, Parquets, trained models, secrets and local paths are never
  copied into this reference (only their paths, sizes and dates).

## 3. How to use this reference (any AI)

1. Read Sections 6 (executive map) and 7 (attention report).
2. Check Section 8 (configuration and gates) and Section 9 (environment).
3. Search Section 12 (API catalog) before proposing any new function.
4. Check Sections 13 to 15 for imports, tests and notebook orchestration.
5. Read the exact implementation in Section 17 (full source).
6. Use Section 18 (artifacts) and notebook outputs as evidence of what was
   actually executed; use Section 10 (inventory) to know what exists locally.
7. If code, configuration, tests, notebooks and plans disagree, report the
   conflict explicitly; never choose silently.

## 4. Evidence precedence

1. Current executable code and tests.
2. Active configuration and explicit decision records.
3. Notebook sources and saved outputs (outputs may be stale: check execution
   counts and artifact dates).
4. Generated artifacts (manifests, tables).
5. Older plans and roadmaps (historical intent only).

## 5. Status vocabulary

- **Implemented:** executable code exists in the current snapshot.
- **Configured:** an active value, rule or gate exists in configuration.
- **Tested / Consumed:** a static reference was found in tests / other code.
- **Working tree:** relevant but not tracked in the current commit.
- **Local only:** exists in the folder but is ignored by Git.
- **Attention:** mismatch, duplication risk, stale reference or broken contract.
"""


@dataclass
class GitEntry:
    path: str
    tracked: bool
    status: str = ""
    exists: bool = True


@dataclass
class CallSite:
    name: str
    location: str
    keywords: list[str]
    n_positional: int
    has_star_args: bool
    has_star_kwargs: bool


@dataclass
class Symbol:
    module: str
    path: str
    qualname: str
    name: str
    kind: str
    signature: str
    lineno: int
    end_lineno: int | None
    docstring: str
    decorators: list[str] = field(default_factory=list)
    calls: list[str] = field(default_factory=list)
    env_vars: list[str] = field(default_factory=list)
    file_literals: list[str] = field(default_factory=list)
    is_private: bool = False
    params: list[str] = field(default_factory=list)
    n_positional_params: int = 0
    has_varargs: bool = False
    has_varkw: bool = False
    defaults: dict[str, str] = field(default_factory=dict)


@dataclass
class PythonFileAnalysis:
    path: str
    module: str
    docstring: str
    parse_error: str | None
    imports: list[str]
    internal_imports: list[str]
    external_imports: list[str]
    import_from: list[dict[str, Any]]
    calls: list[str]
    call_sites: list[CallSite]
    symbols: list[Symbol]
    top_level_names: list[str]
    constants: dict[str, str]
    env_vars: list[str]
    file_literals: list[str]
    has_star_import: bool = False
    lines: int = 0


@dataclass
class NotebookAnalysis:
    path: str
    cells: int
    code_cells: int
    markdown_cells: int
    kernel: dict[str, Any]
    language_version: str
    headings: list[str]
    imports: list[str]
    internal_imports: list[str]
    import_from: list[dict[str, Any]]
    functions: list[Symbol]
    classes: list[Symbol]
    assignments: list[str]
    file_literals: list[str]
    env_vars: list[str]
    parse_errors: list[str]
    call_sites: list[CallSite]
    code_lines: int
    executed_cells: int
    execution_counts: list[int | None]
    out_of_order: bool
    error_outputs: list[str]
    outputs_included: bool


@dataclass
class Attention:
    severity: str
    category: str
    message: str
    evidence: list[str] = field(default_factory=list)
    recommendation: str = ""


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

def run_command(
    args: list[str],
    *,
    cwd: Path,
    check: bool = True,
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    if check and result.returncode:
        raise RuntimeError(
            result.stderr.strip() or result.stdout.strip()
            or f"Command failed: {' '.join(args)}"
        )
    return result


def git(root: Path, *args: str, check: bool = True) -> str:
    return run_command(["git", "-c", "core.quotepath=false", *args], cwd=root, check=check).stdout


def root_dir() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if result.returncode:
        raise RuntimeError("Run inside the Git repository.")
    return Path(result.stdout.strip()).resolve()


def module_name(path: Path) -> str:
    parts = list(path.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def human_bytes(value: int) -> str:
    size = float(value)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{value} B"


class Redactor:
    """Removes secrets and replaces absolute local paths."""

    def __init__(self, root: Path) -> None:
        variants = {str(root), root.as_posix(), str(root).replace("\\", "\\\\")}
        self.root_variants = sorted((v for v in variants if v), key=len, reverse=True)
        home = Path.home()
        self.home_variants = sorted(
            {str(home), home.as_posix(), str(home).replace("\\", "\\\\")}, key=len, reverse=True
        )

    def __call__(self, text: str) -> tuple[str, list[str]]:
        warnings: list[str] = []
        if PRIVATE_KEY_RE.search(text):
            text = PRIVATE_KEY_RE.sub("[REDACTED_PRIVATE_KEY]", text)
            warnings.append("private key redacted")
        if GITHUB_TOKEN_RE.search(text):
            text = GITHUB_TOKEN_RE.sub("[REDACTED_TOKEN]", text)
            warnings.append("token redacted")
        if SECRET_RE.search(text):
            text = SECRET_RE.sub(r"\1[REDACTED]", text)
            warnings.append("possible secret assignment redacted")
        if URL_CREDENTIAL_RE.search(text):
            text = URL_CREDENTIAL_RE.sub(r"\1[REDACTED]\3", text)
            warnings.append("credentials in URL redacted")
        for value in self.root_variants:
            text = text.replace(value, "<REPO>")
        for value in self.home_variants:
            text = text.replace(value, "<HOME>")
        text = WINDOWS_USER_RE.sub("<HOME>", text)
        text = POSIX_HOME_RE.sub("<HOME>", text)
        return text, warnings


def fence_for(text: str) -> str:
    longest = max((len(m.group(0)) for m in BACKTICK_RUN_RE.finditer(text)), default=0)
    return "`" * max(3, longest + 1)


def code_block(text: str, lexer: str = "text") -> str:
    fence = fence_for(text)
    return f"{fence}{lexer}\n{text}\n{fence}"


def truncate(text: str, limit: int, label: str = "characters") -> str:
    if limit <= 0 or len(text) <= limit:
        return text
    head = text[: int(limit * 0.7)]
    tail = text[-int(limit * 0.3):]
    return f"{head}\n... [{len(text) - len(head) - len(tail)} {label} omitted] ...\n{tail}"


def safe_unparse(node: ast.AST | None, default: str = "") -> str:
    if node is None:
        return default
    try:
        return ast.unparse(node)
    except Exception:
        return default or "..."


def literal_preview(node: ast.AST, max_chars: int = 300) -> str:
    try:
        text = repr(ast.literal_eval(node))
    except Exception:
        text = safe_unparse(node, "<dynamic>")
    return text if len(text) <= max_chars else text[: max_chars - 3] + "..."


def dotted_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = dotted_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    if isinstance(node, ast.Call):
        return dotted_name(node.func)
    return None


def env_names(text: str) -> list[str]:
    return sorted(set(ENV_RE.findall(text)))


def file_literals(text: str) -> list[str]:
    return sorted({m.group(1) for m in FILE_LITERAL_RE.finditer(text)})


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = text.encode("utf-8")
    if path.exists() and path.read_bytes() == data:
        return
    with tempfile.NamedTemporaryFile("wb", delete=False, dir=path.parent) as handle:
        handle.write(data)
        temporary = Path(handle.name)
    temporary.replace(path)


# ---------------------------------------------------------------------------
# Git and filesystem inventory
# ---------------------------------------------------------------------------

def parse_porcelain_status(root: Path) -> dict[str, str]:
    raw = git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    items = raw.split("\0")
    status: dict[str, str] = {}
    i = 0
    while i < len(items):
        item = items[i]
        if not item:
            i += 1
            continue
        code, path_text = item[:2], item[3:]
        if code[0] in {"R", "C"} and i + 1 < len(items):
            status[path_text] = code
            i += 2
        else:
            status[path_text] = code
            i += 1
    return status


def collect_git_entries(root: Path) -> tuple[list[GitEntry], set[str], set[str]]:
    status_map = parse_porcelain_status(root)
    tracked = {line.strip() for line in git(root, "ls-files").splitlines() if line.strip()}
    untracked = {
        line.strip()
        for line in git(root, "ls-files", "--others", "--exclude-standard").splitlines()
        if line.strip()
    }
    entries = [
        GitEntry(
            path=Path(value).as_posix(),
            tracked=value in tracked,
            status=status_map.get(value, ""),
            exists=(root / value).is_file(),
        )
        for value in sorted(tracked | untracked, key=str.lower)
    ]
    return entries, tracked, untracked


def walk_inventory(
    root: Path,
    tracked: set[str],
    untracked: set[str],
) -> tuple[list[dict[str, Any]], bool]:
    """All files in the working folder, except tooling/caches/venvs."""
    rows: list[dict[str, Any]] = []
    truncated = False
    for current, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDED_DIRS_ANYWHERE)
        for name in sorted(files):
            absolute = Path(current) / name
            rel = absolute.relative_to(root).as_posix()
            try:
                stat = absolute.stat()
            except OSError:
                continue
            if rel in tracked:
                state = "tracked"
            elif rel in untracked:
                state = "untracked"
            else:
                state = "ignored"
            rows.append(
                {
                    "path": rel,
                    "git": state,
                    "bytes": stat.st_size,
                    "modified_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc)
                    .strftime("%Y-%m-%d %H:%M"),
                }
            )
            if len(rows) >= MAX_INVENTORY_ENTRIES:
                return rows, True
    return rows, truncated


def is_artifact_path(path: Path) -> bool:
    return bool(path.parts) and path.parts[0] in ARTIFACT_DIRS_AT_ROOT


def include_source(path: Path, *, tracked: bool) -> bool:
    parts = path.parts
    if any(part in EXCLUDED_DIRS_ANYWHERE for part in parts):
        return False
    if is_artifact_path(path):
        return False
    if path.name in EXCLUDED_FILES or path.parent.name == PARTS_DIR_NAME:
        return False
    if path.name.startswith(".env") and path.name != ".env.example":
        return False
    if not tracked and not path.as_posix().startswith(IMPORTANT_UNTRACKED_PREFIXES):
        if len(parts) != 1:  # untracked root files (pyproject, README) are allowed
            return False
    suffix = path.suffix.lower()
    return (
        suffix in TEXT_SUFFIXES
        or suffix == ".ipynb"
        or suffix in OFFICE_SUFFIXES
        or path.name in SPECIAL_NAMES
        or path.name in KEYS_ONLY_FILES
    )


def include_artifact(path: Path, size: int, max_bytes: int) -> bool:
    if not is_artifact_path(path):
        return False
    if any(part.lower() in ARTIFACT_EXCLUDED_DIR_NAMES for part in path.parts):
        return False
    if path.name.startswith(".env"):
        return False
    if path.suffix.lower() not in ARTIFACT_TEXT_SUFFIXES:
        return False
    # Raw/large CSVs are only previewed (head), so allow them up to 50x.
    limit = max_bytes * 50 if path.suffix.lower() in {".csv", ".tsv"} else max_bytes
    return size <= limit


# ---------------------------------------------------------------------------
# Python AST analysis
# ---------------------------------------------------------------------------

def imported_names(tree: ast.AST) -> tuple[list[str], list[dict[str, Any]], bool]:
    imports: set[str] = set()
    froms: list[dict[str, Any]] = []
    star = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            prefix = "." * node.level + (node.module or "")
            names = [alias.name for alias in node.names]
            if "*" in names:
                star = True
            froms.append(
                {"module": prefix, "names": names, "lineno": getattr(node, "lineno", 0)}
            )
            for name in names:
                imports.add(f"{prefix}.{name}".strip("."))
    return sorted(imports), froms, star


def call_names(tree: ast.AST) -> list[str]:
    return sorted(
        {
            name
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            for name in [dotted_name(node.func)]
            if name
        }
    )


def call_sites(tree: ast.AST, label: str) -> list[CallSite]:
    sites: list[CallSite] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = dotted_name(node.func)
        if not name:
            continue
        sites.append(
            CallSite(
                name=name,
                location=f"{label}:{getattr(node, 'lineno', 0)}",
                keywords=[kw.arg for kw in node.keywords if kw.arg],
                n_positional=sum(not isinstance(a, ast.Starred) for a in node.args),
                has_star_args=any(isinstance(a, ast.Starred) for a in node.args),
                has_star_kwargs=any(kw.arg is None for kw in node.keywords),
            )
        )
    return sites


def top_level_names(tree: ast.Module) -> list[str]:
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                for sub in ast.walk(target):
                    if isinstance(sub, ast.Name):
                        names.add(sub.id)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                names.add((alias.asname or alias.name).split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.add(alias.asname or alias.name)
        elif isinstance(node, (ast.If, ast.Try)):
            # Conditional definitions (try/except ImportError, if TYPE_CHECKING)
            for sub in ast.walk(node):
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    names.add(sub.name)
                elif isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Store):
                    names.add(sub.id)
                elif isinstance(sub, ast.alias):
                    names.add((sub.asname or sub.name).split(".")[0])
    return sorted(names)


def assigned_constants(tree: ast.Module) -> dict[str, str]:
    constants: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id.isupper():
                constants[target.id] = literal_preview(node.value)
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id.isupper() and node.value:
                constants[node.target.id] = literal_preview(node.value)
    return constants


def function_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
    returns = f" -> {safe_unparse(node.returns)}" if node.returns else ""
    return f"{prefix} {node.name}({safe_unparse(node.args, '...')}){returns}"


def extract_symbol(
    node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef,
    *,
    path: Path,
    module: str,
    text: str,
    parent: str = "",
) -> Symbol:
    qualname = f"{parent}.{node.name}" if parent else node.name
    params: list[str] = []
    n_pos = 0
    has_varargs = has_varkw = False
    defaults: dict[str, str] = {}
    if isinstance(node, ast.ClassDef):
        signature, kind = f"class {node.name}({', '.join(safe_unparse(b) for b in node.bases)})", "class"
        # A class call uses __init__ (or dataclass fields): handled loosely.
        init = next(
            (
                child for child in node.body
                if isinstance(child, ast.FunctionDef) and child.name == "__init__"
            ),
            None,
        )
        if init is not None:
            args = init.args
            positional = [a.arg for a in args.posonlyargs + args.args][1:]
            params = positional + [a.arg for a in args.kwonlyargs]
            n_pos = len(positional)
            has_varargs = args.vararg is not None
            has_varkw = args.kwarg is not None
        else:
            has_varargs = has_varkw = True  # unknown (dataclass, inheritance)
    else:
        signature = function_signature(node)
        kind = "method" if parent else "function"
        args = node.args
        positional = [a.arg for a in args.posonlyargs + args.args]
        if parent and positional and positional[0] in {"self", "cls"}:
            positional = positional[1:]
        params = positional + [a.arg for a in args.kwonlyargs]
        n_pos = len(positional)
        has_varargs = args.vararg is not None
        has_varkw = args.kwarg is not None
        pos_defaults = args.defaults
        for arg, default in zip((args.posonlyargs + args.args)[-len(pos_defaults):] if pos_defaults else [], pos_defaults):
            defaults[arg.arg] = literal_preview(default, 120)
        for arg, default in zip(args.kwonlyargs, args.kw_defaults):
            if default is not None:
                defaults[arg.arg] = literal_preview(default, 120)
    doc = (ast.get_docstring(node) or "").strip()
    if len(doc) > MAX_DOCSTRING_CHARS:
        doc = doc[: MAX_DOCSTRING_CHARS - 3] + "..."
    segment = ast.get_source_segment(text, node) or ""
    return Symbol(
        module=module,
        path=path.as_posix(),
        qualname=qualname,
        name=node.name,
        kind=kind,
        signature=signature,
        lineno=node.lineno,
        end_lineno=getattr(node, "end_lineno", None),
        docstring=doc,
        decorators=[safe_unparse(d) for d in node.decorator_list],
        calls=call_names(node),
        env_vars=env_names(segment),
        file_literals=file_literals(segment),
        is_private=node.name.startswith("_"),
        params=params,
        n_positional_params=n_pos,
        has_varargs=has_varargs,
        has_varkw=has_varkw,
        defaults=defaults,
    )


def analyze_python(path: Path, text: str, internal_roots: set[str]) -> PythonFileAnalysis:
    module = module_name(path)
    lines = len(text.splitlines())
    try:
        tree = ast.parse(text, filename=path.as_posix())
    except SyntaxError as exc:
        return PythonFileAnalysis(
            path=path.as_posix(), module=module, docstring="", parse_error=str(exc),
            imports=[], internal_imports=[], external_imports=[], import_from=[],
            calls=[], call_sites=[], symbols=[], top_level_names=[], constants={},
            env_vars=env_names(text), file_literals=file_literals(text), lines=lines,
        )
    imports, froms, star = imported_names(tree)
    internal = sorted(v for v in imports if v.split(".")[0] in internal_roots or v.startswith("."))
    external = sorted(set(imports) - set(internal))
    symbols: list[Symbol] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            symbols.append(extract_symbol(node, path=path, module=module, text=text))
            if isinstance(node, ast.ClassDef):
                for child in node.body:
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        symbols.append(
                            extract_symbol(child, path=path, module=module, text=text, parent=node.name)
                        )
    return PythonFileAnalysis(
        path=path.as_posix(),
        module=module,
        docstring=(ast.get_docstring(tree) or "").strip(),
        parse_error=None,
        imports=imports,
        internal_imports=internal,
        external_imports=external,
        import_from=froms,
        calls=call_names(tree),
        call_sites=call_sites(tree, path.as_posix()),
        symbols=symbols,
        top_level_names=top_level_names(tree),
        constants=assigned_constants(tree),
        env_vars=env_names(text),
        file_literals=file_literals(text),
        has_star_import=star,
        lines=lines,
    )


# ---------------------------------------------------------------------------
# Notebooks
# ---------------------------------------------------------------------------

def strip_magics(source: str) -> str:
    """Comment out IPython magics/shell lines so the cell can be parsed."""
    lines = []
    for line in source.splitlines():
        stripped = line.lstrip()
        if stripped.startswith(("%", "!", "?")) or stripped.endswith("?"):
            lines.append("# " + line)
        else:
            lines.append(line)
    return "\n".join(lines)


def render_output(output: dict[str, Any], max_chars: int, redactor: Redactor) -> tuple[str, str]:
    """Return (kind, text) for one notebook output."""
    kind = output.get("output_type", "unknown")
    if kind == "stream":
        text = "".join(output.get("text", []))
        label = f"stream:{output.get('name', 'stdout')}"
    elif kind in {"execute_result", "display_data"}:
        data = output.get("data", {})
        omitted = [mime for mime in data if mime != "text/plain"]
        text = "".join(data.get("text/plain", []))
        if omitted:
            text += ("\n" if text else "") + f"[non-text output omitted: {', '.join(sorted(omitted))}]"
        label = kind
    elif kind == "error":
        trace = "\n".join(output.get("traceback", []))
        text = f"{output.get('ename', '')}: {output.get('evalue', '')}\n{trace}"
        label = "error"
    else:
        text, label = json.dumps(output)[:500], kind
    text = ANSI_RE.sub("", text)
    text, _ = redactor(text)
    return label, truncate(text.rstrip(), max_chars)


def analyze_notebook(
    path: Path,
    data: bytes,
    internal_roots: set[str],
) -> tuple[NotebookAnalysis, dict[str, Any]]:
    nb = json.loads(data.decode("utf-8-sig"))
    headings: list[str] = []
    imports: set[str] = set()
    internal_imports: set[str] = set()
    froms: list[dict[str, Any]] = []
    functions: list[Symbol] = []
    classes: list[Symbol] = []
    assignments: set[str] = set()
    literals: set[str] = set()
    envs: set[str] = set()
    parse_errors: list[str] = []
    sites: list[CallSite] = []
    errors: list[str] = []
    counts: list[int | None] = []
    code_lines = code_cells = markdown_cells = executed = 0
    for number, cell in enumerate(nb.get("cells", []), 1):
        kind = cell.get("cell_type", "unknown")
        source = "".join(cell.get("source", []))
        if kind == "markdown":
            markdown_cells += 1
            headings.extend(title.strip() for _, title in HEADING_RE.findall(source))
            continue
        if kind != "code":
            continue
        code_cells += 1
        code_lines += len(source.splitlines())
        count = cell.get("execution_count")
        counts.append(count)
        if count is not None:
            executed += 1
        for output in cell.get("outputs", []):
            if output.get("output_type") == "error":
                errors.append(f"cell {number}: {output.get('ename', '')}: {str(output.get('evalue', ''))[:200]}")
        label = f"{path.as_posix()}#cell-{number}"
        try:
            tree = ast.parse(strip_magics(source), filename=label)
        except SyntaxError as exc:
            parse_errors.append(f"Cell {number}: {exc}")
            continue
        cell_imports, cell_froms, _ = imported_names(tree)
        imports.update(cell_imports)
        internal_imports.update(v for v in cell_imports if v.split(".")[0] in internal_roots)
        for item in cell_froms:
            froms.append({**item, "cell": number})
        sites.extend(call_sites(tree, label))
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(extract_symbol(node, path=Path(label), module=f"notebook:{path.as_posix()}", text=source))
            elif isinstance(node, ast.ClassDef):
                classes.append(extract_symbol(node, path=Path(label), module=f"notebook:{path.as_posix()}", text=source))
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    if isinstance(target, ast.Name) and (
                        target.id.isupper() or target.id.lower().endswith(("_dir", "_path", "_file"))
                    ):
                        assignments.add(target.id)
        literals.update(file_literals(source))
        envs.update(env_names(source))
    numeric = [c for c in counts if c is not None]
    out_of_order = any(b < a for a, b in zip(numeric, numeric[1:]))
    meta = nb.get("metadata", {})
    analysis = NotebookAnalysis(
        path=path.as_posix(),
        cells=len(nb.get("cells", [])),
        code_cells=code_cells,
        markdown_cells=markdown_cells,
        kernel=meta.get("kernelspec", {}),
        language_version=str(meta.get("language_info", {}).get("version", "")),
        headings=headings,
        imports=sorted(imports),
        internal_imports=sorted(internal_imports),
        import_from=froms,
        functions=functions,
        classes=classes,
        assignments=sorted(assignments),
        file_literals=sorted(literals),
        env_vars=sorted(envs),
        parse_errors=parse_errors,
        call_sites=sites,
        code_lines=code_lines,
        executed_cells=executed,
        execution_counts=counts,
        out_of_order=out_of_order,
        error_outputs=errors,
        outputs_included=False,
    )
    return analysis, nb


def notebook_source_markdown(
    nb: dict[str, Any],
    analysis: NotebookAnalysis,
    *,
    include_outputs: bool,
    max_output_chars: int,
    reduced: bool,
    redactor: Redactor,
) -> str:
    parts: list[str] = [
        f"- Cells: `{analysis.cells}` (`{analysis.code_cells}` code, `{analysis.markdown_cells}` markdown)",
        f"- Code cells executed: `{analysis.executed_cells}` of `{analysis.code_cells}`"
        + (" — **executed out of order**" if analysis.out_of_order else ""),
        f"- Kernel: `{analysis.kernel.get('display_name', '')}`; Python `{analysis.language_version}`",
        f"- Outputs: `{'text outputs included' if include_outputs else 'omitted'}`"
        + ("; **reduced view** (notebook above size limit)" if reduced else ""),
        "",
    ]
    for number, cell in enumerate(nb.get("cells", []), 1):
        kind = cell.get("cell_type", "unknown")
        source, _ = redactor("".join(cell.get("source", [])).rstrip())
        if kind == "code":
            count = cell.get("execution_count")
            if reduced:
                lines = source.splitlines()
                if len(lines) > MAX_SOURCE_LINES_PER_LARGE_NOTEBOOK_CELL:
                    source = "\n".join(lines[:MAX_SOURCE_LINES_PER_LARGE_NOTEBOOK_CELL]) + (
                        f"\n# ... {len(lines) - MAX_SOURCE_LINES_PER_LARGE_NOTEBOOK_CELL} lines omitted ..."
                    )
            parts.append(f"### Cell {number} [code] · In [{count if count is not None else ' '}]")
            parts.append("")
            parts.append(code_block(source, "python"))
            if include_outputs:
                for out_index, output in enumerate(cell.get("outputs", []), 1):
                    label, text = render_output(output, max_output_chars, redactor)
                    if not text:
                        continue
                    parts.append("")
                    parts.append(f"**Output {out_index} ({label})**")
                    parts.append("")
                    parts.append(code_block(text, "text"))
        else:
            parts.append(f"### Cell {number} [{kind}]")
            parts.append("")
            parts.append(code_block(source, "markdown"))
        parts.append("")
    return "\n".join(parts).rstrip()


# ---------------------------------------------------------------------------
# Office documents and artifacts
# ---------------------------------------------------------------------------

def office_text(data: bytes, suffix: str) -> str:
    """Plain text of .docx/.pptx using only the standard library."""
    import io
    from xml.etree import ElementTree as ET

    texts: list[str] = []
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        if suffix == ".docx":
            names = ["word/document.xml"]
        else:
            names = sorted(
                (n for n in archive.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)),
                key=lambda n: int(re.findall(r"\d+", n)[-1]),
            )
        for index, name in enumerate(names, 1):
            if name not in archive.namelist():
                continue
            root = ET.fromstring(archive.read(name))
            if suffix == ".pptx":
                texts.append(f"--- slide {index} ---")
            for paragraph in root.iter():
                tag = paragraph.tag.rsplit("}", 1)[-1]
                if tag == "p":
                    line = "".join(
                        (node.text or "")
                        for node in paragraph.iter()
                        if node.tag.rsplit("}", 1)[-1] in {"t", "tab"}
                    ).strip()
                    if line:
                        texts.append(line)
                elif tag == "tr" and suffix == ".docx":
                    pass
    return "\n".join(texts)


def csv_preview(text: str, max_rows: int) -> tuple[str, int]:
    lines = text.splitlines()
    total = max(0, len(lines) - 1)
    if len(lines) <= max_rows + 1:
        return text, total
    return "\n".join(lines[: max_rows + 1]) + f"\n... [{total - max_rows} more rows omitted]", total


def keys_only_json(text: str) -> str:
    try:
        data = json.loads(text)
    except Exception:
        return "[could not parse; values hidden]"

    def mask(value: Any) -> Any:
        if isinstance(value, dict):
            return {k: mask(v) for k, v in value.items()}
        if isinstance(value, list):
            return [mask(v) for v in value[:5]]
        return f"<{type(value).__name__}>"

    return json.dumps(mask(data), ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Configuration, environment and dependency files
# ---------------------------------------------------------------------------

def flatten_mapping(value: Any, prefix: str = "") -> dict[str, Any]:
    result: dict[str, Any] = {}
    if isinstance(value, dict) and value:
        for key, child in value.items():
            new_prefix = f"{prefix}.{key}" if prefix else str(key)
            result.update(flatten_mapping(child, new_prefix))
    else:
        result[prefix] = value
    return result


def nested_get(mapping: Any, *keys: str, default: Any = None) -> Any:
    current = mapping
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def load_yaml_strict(text: str) -> tuple[Any | None, str | None, list[str]]:
    """Parse YAML; also report duplicated keys (safe_load silently keeps the last)."""
    if yaml is None:
        return None, "PyYAML not available", []
    duplicates: list[str] = []

    class DupLoader(yaml.SafeLoader):  # type: ignore[misc]
        pass

    def construct_mapping(loader: Any, node: Any, deep: bool = False) -> Any:
        seen: set[Any] = set()
        for key_node, _ in node.value:
            key = loader.construct_object(key_node, deep=deep)
            if key in seen:
                duplicates.append(f"{key!r} (line {key_node.start_mark.line + 1})")
            seen.add(key)
        return yaml.SafeLoader.construct_mapping(loader, node, deep=deep)

    DupLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping)
    try:
        return yaml.load(text, Loader=DupLoader), None, duplicates  # noqa: S506
    except Exception as exc:
        return None, repr(exc), duplicates


def parse_requirements(text: str) -> dict[str, str]:
    deps: dict[str, str] = {}
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or line.startswith(("-", "git+", "http")):
            continue
        match = re.match(r"([A-Za-z0-9_.\-\[\]]+)\s*(.*)", line)
        if match:
            name = re.sub(r"\[.*\]", "", match.group(1)).lower().replace("_", "-")
            deps[name] = match.group(2).strip()
    return deps


def parse_pyproject(text: str) -> tuple[dict[str, Any] | None, str | None]:
    if tomllib is None:
        return None, "tomllib unavailable (Python < 3.11)"
    try:
        return tomllib.loads(text), None
    except Exception as exc:
        return None, repr(exc)


def pyproject_dependencies(data: dict[str, Any]) -> dict[str, str]:
    deps: dict[str, str] = {}
    values = list(nested_get(data, "project", "dependencies", default=[]) or [])
    for group in (nested_get(data, "project", "optional-dependencies", default={}) or {}).values():
        values.extend(group or [])
    for item in values:
        match = re.match(r"([A-Za-z0-9_.\-\[\]]+)\s*(.*)", str(item))
        if match:
            name = re.sub(r"\[.*\]", "", match.group(1)).lower().replace("_", "-")
            deps[name] = match.group(2).strip()
    return deps


def installed_packages() -> dict[str, str]:
    packages: dict[str, str] = {}
    for dist in importlib_metadata.distributions():
        try:
            name = (dist.metadata["Name"] or "").lower().replace("_", "-")
        except Exception:
            continue
        if name:
            packages[name] = dist.version
    return dict(sorted(packages.items()))


def top_level_import_map() -> dict[str, str]:
    """Import name -> distribution, from installed metadata when available."""
    mapping = {k: v for k, v in IMPORT_TO_DIST.items()}
    try:
        for top, dists in importlib_metadata.packages_distributions().items():
            if dists:
                mapping.setdefault(top, dists[0].lower().replace("_", "-"))
    except Exception:
        pass
    return mapping


def run_tests(root: Path, extra: str, timeout: int) -> dict[str, Any]:
    args = [sys.executable, "-m", "pytest", "-q", "-rfEs", "--no-header", "-p", "no:cacheprovider"]
    if extra:
        import shlex
        args += shlex.split(extra, posix=(os.name != "nt"))
    try:
        result = run_command(args, cwd=root, check=False, timeout=timeout)
        output = (result.stdout + "\n" + result.stderr).strip()
        return {"command": " ".join(args[1:]), "returncode": result.returncode, "output": output}
    except subprocess.TimeoutExpired:
        return {"command": " ".join(args[1:]), "returncode": None, "output": f"Timeout after {timeout}s"}
    except Exception as exc:
        return {"command": " ".join(args[1:]), "returncode": None, "output": repr(exc)}


# ---------------------------------------------------------------------------
# Static diagnostics
# ---------------------------------------------------------------------------

def index_consumers(
    symbols: list[Symbol],
    python_files: list[PythonFileAnalysis],
    notebooks: list[NotebookAnalysis],
) -> dict[str, list[str]]:
    consumers: dict[str, set[str]] = defaultdict(set)
    by_name: defaultdict[str, list[Symbol]] = defaultdict(list)
    for symbol in symbols:
        by_name[symbol.name].append(symbol)
    sources: list[tuple[str, set[str]]] = [
        (a.path, set(a.calls) | set(a.imports)) for a in python_files
    ] + [
        (n.path, set(n.imports) | {s.name for s in n.call_sites}) for n in notebooks
    ]
    for path, haystack in sources:
        tails = {item.rsplit(".", 1)[-1] for item in haystack}
        for name in tails & set(by_name):
            for match in by_name[name]:
                if path != match.path:
                    consumers[f"{match.module}.{match.qualname}"].add(path)
    return {key: sorted(values) for key, values in sorted(consumers.items())}


def index_tests(symbols: list[Symbol], python_files: list[PythonFileAnalysis]) -> dict[str, list[str]]:
    tests: dict[str, set[str]] = defaultdict(set)
    test_files = [
        f for f in python_files
        if f.path.startswith("tests/") or Path(f.path).name.startswith("test_")
    ]
    for test in test_files:
        tails = {v.rsplit(".", 1)[-1] for v in set(test.calls) | set(test.imports)}
        for symbol in symbols:
            if symbol.name in tails and symbol.path != test.path:
                tests[f"{symbol.module}.{symbol.qualname}"].add(test.path)
    return {key: sorted(values) for key, values in sorted(tests.items())}


def resolve_relative(module: str, current: str, is_package: bool) -> str:
    if not module.startswith("."):
        return module
    level = len(module) - len(module.lstrip("."))
    base = current.split(".")
    if not is_package:
        base = base[:-1]
    base = base[: len(base) - (level - 1)] if level > 1 else base
    rest = module.lstrip(".")
    return ".".join([*base, rest] if rest else base)


def import_integrity_attention(
    python_files: list[PythonFileAnalysis],
    notebooks: list[NotebookAnalysis],
    internal_roots: set[str],
) -> list[Attention]:
    modules = {f.module: f for f in python_files}
    packages = {m.rsplit(".", 1)[0] for m in modules if "." in m}
    missing_modules: defaultdict[str, set[str]] = defaultdict(set)
    missing_names: defaultdict[str, set[str]] = defaultdict(set)

    def check(module: str, names: list[str], where: str) -> None:
        if module.split(".")[0] not in internal_roots:
            return
        if module not in modules and module not in packages:
            missing_modules[module].add(where)
            return
        target = modules.get(module)
        if target is None or target.has_star_import or target.parse_error:
            return
        defined = set(target.top_level_names)
        for name in names:
            if name == "*" or name in defined:
                continue
            if f"{module}.{name}" in modules or f"{module}.{name}" in packages:
                continue
            missing_names[f"{module}.{name}"].add(where)

    for f in python_files:
        is_pkg = f.path.endswith("__init__.py")
        for item in f.import_from:
            module = resolve_relative(item["module"], f.module, is_pkg)
            check(module, item["names"], f"{f.path}:{item['lineno']}")
        for value in f.imports:
            if "." not in value and value in internal_roots:
                continue
    for nb in notebooks:
        for item in nb.import_from:
            check(item["module"], item["names"], f"{nb.path}#cell-{item.get('cell')}")
    attention = [
        Attention(
            "high", "internal-import-missing-module",
            f"Import of internal module `{name}`, which does not exist in the snapshot.",
            sorted(paths),
            "Check branch completeness, renamed modules or stale imports before recreating code.",
        )
        for name, paths in sorted(missing_modules.items())
    ]
    attention += [
        Attention(
            "high", "internal-import-missing-name",
            f"`{name.rsplit('.', 1)[1]}` is imported from `{name.rsplit('.', 1)[0]}`, "
            "but that module does not define or re-export it.",
            sorted(paths),
            "Export the name in the module (or its __init__) or fix the import.",
        )
        for name, paths in sorted(missing_names.items())
    ]
    return attention


def call_signature_attention(
    symbols: list[Symbol],
    python_files: list[PythonFileAnalysis],
    notebooks: list[NotebookAnalysis],
) -> list[Attention]:
    """Calls to project functions with keywords they do not accept."""
    candidates: defaultdict[str, list[Symbol]] = defaultdict(list)
    for symbol in symbols:
        if symbol.kind in {"function", "class"} and symbol.path.startswith("src/"):
            candidates[symbol.name].append(symbol)
    unique = {name: items[0] for name, items in candidates.items() if len(items) == 1}
    local_defs: dict[str, set[str]] = defaultdict(set)
    for f in python_files:
        local_defs[f.path].update(s.name for s in f.symbols if s.kind in {"function", "class"})
    for nb in notebooks:
        local_defs[nb.path].update(s.name for s in nb.functions + nb.classes)

    problems: list[Attention] = []
    sources = [(f.path, f.call_sites) for f in python_files] + [(n.path, n.call_sites) for n in notebooks]
    for path, sites in sources:
        for site in sites:
            tail = site.name.rsplit(".", 1)[-1]
            target = unique.get(tail)
            if target is None or path == target.path or tail in local_defs[path]:
                continue
            if "." in site.name and site.name.split(".")[0] in {"self", "cls"}:
                continue
            issues: list[str] = []
            if not target.has_varkw:
                bad = [k for k in site.keywords if k not in target.params]
                if bad:
                    issues.append(f"unknown keyword(s) {bad}")
            if not target.has_varargs and not site.has_star_args and site.n_positional > target.n_positional_params:
                issues.append(
                    f"{site.n_positional} positional args, accepts {target.n_positional_params}"
                )
            if issues:
                problems.append(
                    Attention(
                        "high", "call-signature-mismatch",
                        f"Call to `{target.module}.{target.name}` does not match its signature: "
                        + "; ".join(issues) + ".",
                        [site.location, f"definition: {target.path}:{target.lineno} `{target.signature}`"],
                        "Fix the call or the function signature; this raises TypeError when executed.",
                    )
                )
    return problems


def gate_attention(
    gate_names: set[str],
    files_text: dict[str, str],
    notebook_sources: dict[str, str],
) -> list[Attention]:
    if not gate_names:
        return []
    found: defaultdict[str, set[str]] = defaultdict(set)
    for path, text in {**files_text, **notebook_sources}.items():
        if path.endswith(("supervised.yaml", OUTPUT_MD_NAME)):
            continue
        for match in GATE_RE.findall(text):
            found[match].add(path)
    stale = {name: paths for name, paths in found.items() if name not in gate_names}
    return [
        Attention(
            "medium", "gate-name-not-in-yaml",
            f"`{name}` is referenced but does not exist in `gates` of the active YAML.",
            sorted(paths),
            "Update the reference (code, docstring, notebook or document) to an existing gate.",
        )
        for name, paths in sorted(stale.items())
    ]


def config_contract_attention(config: Any, python_files: list[PythonFileAnalysis]) -> list[Attention]:
    if not isinstance(config, dict):
        return []
    attention: list[Attention] = []

    def as_list(*keys: str) -> list[str]:
        value = nested_get(config, *keys, default=[])
        return [str(v) for v in value] if isinstance(value, list) else []

    final = as_list("features", "final")
    active = set(final) or set(as_list("features", "numericas")) | set(as_list("features", "categoricas"))
    prohibited = set(as_list("features", "proibidas"))
    if active & prohibited:
        attention.append(Attention(
            "high", "feature-leakage-contract",
            "Configured model features overlap `features.proibidas`.",
            sorted(active & prohibited), "Remove the overlap or revise configuration and tests."))
    target = nested_get(config, "target", "coluna")
    if target and target not in prohibited:
        attention.append(Attention(
            "high", "feature-leakage-contract", "`target.coluna` is not in `features.proibidas`.",
            [str(target)], "Add the raw target to the forbidden list."))
    derived = set(as_list("features", "engenharia", "derivadas"))
    model_features = set(as_list("features", "numericas")) | set(as_list("features", "categoricas"))
    unused_derived = sorted(derived - model_features - set(final))
    if unused_derived:
        attention.append(Attention(
            "low", "derived-not-used-as-feature",
            "Derived columns produced by feature engineering but absent from the model feature lists.",
            unused_derived, "Confirm whether they are intentionally descriptive-only or missing from the model."))
    source_text = "\n".join(
        " ".join(f.calls + list(f.constants) + list(f.constants.values()) + f.file_literals + f.top_level_names)
        for f in python_files if f.path.startswith(("src/features/", "src/data/"))
    )
    absent = sorted(v for v in derived if v not in source_text)
    if absent:
        attention.append(Attention(
            "medium", "derived-feature-contract",
            "Configured derived features not found as static names in src/features or src/data.",
            absent, "Confirm whether names are dynamic, stale or missing from the implementation."))
    fractions = nested_get(config, "temporal", "fracao", default={})
    if isinstance(fractions, dict):
        numeric = [v for v in fractions.values() if isinstance(v, (int, float))]
        if numeric and abs(sum(numeric) - 1.0) > 1e-9:
            attention.append(Attention(
                "high", "split-contract", "Split fractions do not sum to 1.", [repr(fractions)],
                "Correct the split contract."))
    models = nested_get(config, "models", default={}) or {}
    closed = set(as_list("selecao_modelos", "familias_encerradas"))
    for name in sorted(closed):
        if nested_get(models, name, "ativa") is True:
            attention.append(Attention(
                "low", "config-consistency",
                f"`models.{name}.ativa` is true, but the family is in `selecao_modelos.familias_encerradas`.",
                [f"models.{name}.ativa"], "Set `ativa: false` or remove the family from the closed list."))
    finalists = as_list("selecao_modelos", "finalistas")
    for name in finalists:
        if name not in models:
            attention.append(Attention(
                "medium", "config-consistency",
                f"Finalist `{name}` has no section in `models` (factory names must match).",
                [f"selecao_modelos.finalistas: {finalists}", f"models: {sorted(models)}"],
                "Use the same names or declare an explicit alias in code."))
    gates = nested_get(config, "gates", default={}) or {}
    numbers = sorted(int(m.group(1)) for k in gates for m in [re.match(r"G(\d+)_", str(k))] if m)
    if numbers:
        gaps = [f"G{n}" for n in range(numbers[0], numbers[-1] + 1) if n not in numbers]
        if gaps:
            attention.append(Attention(
                "low", "gate-numbering", "Gate numbering has gaps.", gaps,
                "Document why the gate does not exist or renumber."))
    return attention


def unused_config_keys_attention(config: Any, code_text: str) -> list[Attention]:
    if not isinstance(config, dict):
        return []
    unused: list[str] = []
    for key in flatten_mapping(config):
        parts = key.split(".")
        if parts[0] in {"gates", "selecao_modelos"}:
            continue
        leaf = next((p for p in reversed(parts) if not p.isdigit()), parts[-1])
        if not re.search(rf"['\"]{re.escape(leaf)}['\"]", code_text):
            unused.append(key)
    if not unused:
        return []
    return [Attention(
        "low", "config-key-not-referenced",
        f"{len(unused)} YAML keys whose name never appears as a string literal in code or notebooks "
        "(possible dead configuration, or keys read dynamically).",
        unused[:80], "Remove dead keys or make the code read them; keep documentation keys commented.")]


def dependency_attention(
    python_files: list[PythonFileAnalysis],
    notebooks: list[NotebookAnalysis],
    requirements: dict[str, str] | None,
    pyproject_deps: dict[str, str] | None,
    import_map: dict[str, str],
    internal_roots: set[str],
) -> list[Attention]:
    stdlib = set(getattr(sys, "stdlib_module_names", ()))
    used: defaultdict[str, set[str]] = defaultdict(set)
    for f in python_files:
        for value in f.external_imports:
            used[value.split(".")[0]].add(f.path)
    for nb in notebooks:
        for value in nb.imports:
            used[value.split(".")[0]].add(nb.path)
    third_party = {
        top: paths for top, paths in used.items()
        if top and top not in stdlib and top not in internal_roots and not top.startswith("_")
        and top not in {"__future__"}
    }
    attention: list[Attention] = []
    for label, deps in (("requirements.txt", requirements), ("pyproject.toml", pyproject_deps)):
        if deps is None:
            continue
        missing = []
        for top, paths in sorted(third_party.items()):
            dist = import_map.get(top, top).lower().replace("_", "-")
            if dist not in deps and top.lower() not in deps:
                missing.append(f"{top} (distribution `{dist}`) used in {sorted(paths)[0]}")
        if missing:
            attention.append(Attention(
                "medium", "dependency-not-declared",
                f"Third-party imports not declared in `{label}`.", missing,
                "Declare them (with a minimum version) in a single source of dependencies."))
        unpinned = sorted(name for name, spec in deps.items() if not spec)
        if unpinned:
            attention.append(Attention(
                "low", "dependency-unpinned", f"Dependencies without version constraint in `{label}`.",
                unpinned, "Add minimum versions for reproducibility (at least scikit-learn, pandas, numpy)."))
    return attention


def duplicate_symbol_attention(symbols: list[Symbol]) -> list[Attention]:
    grouped: defaultdict[str, set[str]] = defaultdict(set)
    for symbol in symbols:
        if symbol.kind in {"function", "class"} and not symbol.path.startswith("tests/") and symbol.name != "main":
            grouped[symbol.name].add(symbol.path)
    return [
        Attention(
            "medium", "duplicate-symbol-name", f"`{name}` is defined in multiple files.",
            sorted(paths), "Confirm distinct responsibilities or consolidate competing implementations.")
        for name, paths in sorted(grouped.items()) if len(paths) > 1
    ]


def notebook_attention(notebooks: list[NotebookAnalysis], python_files: list[PythonFileAnalysis]) -> list[Attention]:
    canonical: defaultdict[str, list[str]] = defaultdict(list)
    for f in python_files:
        if f.path.startswith("src/"):
            for s in f.symbols:
                if s.kind in {"function", "class"}:
                    canonical[s.name].append(s.path)
    attention: list[Attention] = []
    for nb in notebooks:
        for s in nb.functions + nb.classes:
            if s.name in canonical:
                attention.append(Attention(
                    "medium", "notebook-duplicates-src",
                    f"Notebook defines `{s.name}`, already present in src.",
                    [s.path, *sorted(set(canonical[s.name]))],
                    "Use the src implementation, or extend it if behaviour differs."))
        local = [s.name for s in nb.functions + nb.classes if s.name not in canonical]
        if local:
            attention.append(Attention(
                "low", "notebook-local-functions",
                f"`{nb.path}` defines {len(local)} local functions/classes.",
                local, "Keep single-use orchestration in the notebook; move reusable logic to src with tests."))
        if nb.out_of_order:
            attention.append(Attention(
                "medium", "notebook-execution-order",
                f"`{nb.path}` was saved with cells executed out of order.",
                [str(nb.execution_counts)], "Restart the kernel and run all cells before trusting saved outputs."))
        if nb.code_cells and nb.executed_cells < nb.code_cells:
            attention.append(Attention(
                "low", "notebook-not-fully-executed",
                f"`{nb.path}`: {nb.code_cells - nb.executed_cells} of {nb.code_cells} code cells have no saved execution.",
                [], "Outputs may be partial; re-run before using results."))
        if nb.error_outputs:
            attention.append(Attention(
                "high", "notebook-saved-errors", f"`{nb.path}` was saved with error outputs.",
                nb.error_outputs[:20], "Fix the error and re-run, or clear the stale output."))
        if nb.parse_errors:
            attention.append(Attention(
                "medium", "notebook-parse-error", f"`{nb.path}` has code cells that could not be parsed.",
                nb.parse_errors[:20], "Check syntax (magics are already tolerated)."))
    return attention


def stale_document_attention(files_text: dict[str, str], existing_paths: set[str]) -> list[Attention]:
    path_re = re.compile(
        r"(?<![A-Za-z0-9_./-])((?:src|tests|notebooks|configs|tools|docs|data|outputs)/"
        r"[A-Za-z0-9_./-]+\.(?:py|ipynb|yaml|yml|md|csv|json|parquet|toml))"
    )
    existing_dirs = {str(Path(p).parent.as_posix()) for p in existing_paths}
    attention: list[Attention] = []
    for path, text in files_text.items():
        if not path.lower().endswith((".md", ".rst", ".txt", ".py", ".yaml", ".yml")):
            continue
        refs = sorted({m.group(1) for m in path_re.finditer(text)})
        missing = [
            r for r in refs
            if r not in existing_paths and "{" not in r and "*" not in r and r not in existing_dirs
        ]
        if missing:
            attention.append(Attention(
                "low" if path.endswith(".py") else "medium", "reference-to-missing-path",
                f"`{path}` references paths absent from the working folder.", missing[:40],
                "Confirm whether the reference is historical, generated at runtime, or stale."))
    return attention


def text_quality_attention(files_text: dict[str, str], notebook_sources: dict[str, str]) -> tuple[list[Attention], list[str]]:
    mojibake: list[str] = []
    todos: list[str] = []
    for path, text in {**files_text, **notebook_sources}.items():
        if path.endswith(OUTPUT_MD_NAME):
            continue
        for number, line in enumerate(text.splitlines(), 1):
            if MOJIBAKE_RE.search(line):
                mojibake.append(f"{path}:{number}: {line.strip()[:100]}")
            match = TODO_RE.search(line)
            if match and not path.endswith(".csv"):
                todos.append(f"{path}:{number}: {match.group(1)} {match.group(2).strip()}")
    attention = []
    if mojibake:
        attention.append(Attention(
            "low", "encoding-mojibake", "Text with likely encoding corruption (file saved with the wrong encoding).",
            mojibake[:40], "Fix the characters and save the file as UTF-8."))
    return attention, todos


def working_tree_attention(entries: list[GitEntry]) -> list[Attention]:
    relevant = [e.path for e in entries if not e.tracked and e.exists and e.path.startswith(IMPORTANT_UNTRACKED_PREFIXES)]
    modified = [f"{e.path} ({e.status.strip()})" for e in entries if e.tracked and e.status.strip()]
    attention = []
    if relevant:
        attention.append(Attention(
            "high", "untracked-relevant-files", "Relevant files exist only in the working tree (not committed).",
            relevant, "Commit intentional files or remove them before treating the snapshot as the project state."))
    if modified:
        attention.append(Attention(
            "medium", "uncommitted-changes", "Tracked files with uncommitted changes.", modified[:60],
            "Review Section 16 (diff) and commit or discard."))
    return attention


def symbol_quality_attention(
    symbols: list[Symbol],
    consumers: dict[str, list[str]],
    tests: dict[str, list[str]],
) -> list[Attention]:
    public = [
        s for s in symbols
        if s.path.startswith("src/") and not s.is_private and s.kind in {"function", "class"}
    ]
    orphan = [f"{s.module}.{s.name}" for s in public if not consumers.get(f"{s.module}.{s.qualname}") and not tests.get(f"{s.module}.{s.qualname}")]
    untested = [f"{s.module}.{s.name}" for s in public if not tests.get(f"{s.module}.{s.qualname}")]
    nodoc = [f"{s.module}.{s.name}" for s in public if not s.docstring]
    out = []
    if orphan:
        out.append(Attention("low", "public-symbol-unused",
                             "Public src symbols with no detected consumer and no test (possibly dead code).",
                             orphan, "Remove, test, or document why they exist."))
    if untested:
        out.append(Attention("low", "public-symbol-untested",
                             f"{len(untested)} public src symbols without a detected test.", untested,
                             "Prioritise tests for functions used by notebooks C2–C6."))
    if nodoc:
        out.append(Attention("low", "missing-docstring", "Public src symbols without docstring.", nodoc,
                             "Add a short docstring with purpose, parameters and returned value."))
    return out


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def render_attention(attention: list[Attention]) -> str:
    if not attention:
        return "- No static inconsistencies detected."
    counts = Counter(a.severity for a in attention)
    lines = [
        f"Totals: **{counts.get('high', 0)} high**, {counts.get('medium', 0)} medium, {counts.get('low', 0)} low.",
        "",
        "| # | Severity | Category | Message |",
        "|---|---|---|---|",
    ]
    ordered = sorted(attention, key=lambda a: (SEVERITY_ORDER.get(a.severity, 9), a.category, a.message))
    for i, a in enumerate(ordered, 1):
        lines.append(f"| A{i} | {a.severity.upper()} | {a.category} | {a.message.replace('|', '/')} |")
    lines.append("")
    for i, a in enumerate(ordered, 1):
        lines += [f"### A{i}. {a.severity.upper()} — {a.category}", "", a.message, ""]
        if a.evidence:
            lines += ["**Evidence**", "", *(f"- `{v}`" for v in a.evidence), ""]
        if a.recommendation:
            lines += [f"**Recommended action:** {a.recommendation}", ""]
    return "\n".join(lines).rstrip()


def render_symbol(symbol: Symbol, consumers: dict[str, list[str]], tests: dict[str, list[str]]) -> str:
    key = f"{symbol.module}.{symbol.qualname}"
    lines = [
        f"#### `{symbol.qualname}`",
        "",
        code_block(symbol.signature, "python"),
        "",
        f"- Location: `{symbol.path}:{symbol.lineno}-{symbol.end_lineno}`",
        f"- Visibility: `{'private' if symbol.is_private else 'public'}`",
        "- Tested by: " + (", ".join(f"`{p}`" for p in tests.get(key, [])) or "not found statically"),
        "- Consumed by: " + (", ".join(f"`{p}`" for p in consumers.get(key, [])) or "not found statically"),
    ]
    if symbol.defaults:
        lines.append("- Defaults: " + ", ".join(f"`{k}={v}`" for k, v in symbol.defaults.items()))
    if symbol.decorators:
        lines.append("- Decorators: " + ", ".join(f"`{d}`" for d in symbol.decorators))
    if symbol.calls:
        lines.append("- Calls: " + ", ".join(f"`{c}`" for c in symbol.calls[:40]))
    if symbol.env_vars:
        lines.append("- Environment variables: " + ", ".join(f"`{e}`" for e in symbol.env_vars))
    if symbol.file_literals:
        lines.append("- File literals: " + ", ".join(f"`{e}`" for e in symbol.file_literals))
    lines += ["", symbol.docstring or "_Missing docstring._", ""]
    return "\n".join(lines)


def render_python_api(python_files: list[PythonFileAnalysis], consumers: dict, tests: dict) -> str:
    parts: list[str] = []
    for f in sorted(python_files, key=lambda x: x.path.lower()):
        parts += [f"### `{f.path}`", ""]
        if f.parse_error:
            parts += [f"- **Parse error:** `{f.parse_error}`", ""]
            continue
        parts += [
            f"- Module: `{f.module}` · {f.lines} lines",
            "- Internal imports: " + (", ".join(f"`{v}`" for v in f.internal_imports) or "none"),
            "- External imports: " + (", ".join(f"`{v}`" for v in f.external_imports) or "none"),
        ]
        if f.constants:
            parts.append("- Module constants: " + ", ".join(f"`{k} = {v}`" for k, v in f.constants.items()))
        if f.env_vars:
            parts.append("- Environment variables: " + ", ".join(f"`{e}`" for e in f.env_vars))
        parts.append("")
        if f.docstring:
            parts += [f.docstring, ""]
        for symbol in f.symbols:
            parts.append(render_symbol(symbol, consumers, tests))
    return "\n".join(parts).rstrip()


def render_table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return "- None."
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    out += ["| " + " | ".join(str(c).replace("|", "/").replace("\n", " ") for c in row) + " |" for row in rows]
    return "\n".join(out)


def render_tree(inventory: list[dict[str, Any]]) -> str:
    """Directory tree with file counts and sizes."""
    dirs: defaultdict[str, list[int]] = defaultdict(lambda: [0, 0])
    for row in inventory:
        parent = str(Path(row["path"]).parent.as_posix())
        while True:
            dirs[parent][0] += 1
            dirs[parent][1] += row["bytes"]
            if parent in {".", ""}:
                break
            parent = str(Path(parent).parent.as_posix())
    lines = []
    for d in sorted(dirs):
        depth = 0 if d == "." else d.count("/") + 1
        name = "./" if d == "." else Path(d).name + "/"
        lines.append(f"{'  ' * depth}{name}  ({dirs[d][0]} files, {human_bytes(dirs[d][1])})")
    return code_block("\n".join(lines), "text")


def split_document(document: str, max_bytes: int) -> list[str]:
    """Split on level-2 headings, keeping parts under max_bytes when possible."""
    chunks: list[str] = []
    current: list[str] = []
    in_fence = None
    for line in document.splitlines(keepends=True):
        fence = re.match(r"^(`{3,})", line)
        if fence:
            if in_fence is None:
                in_fence = fence.group(1)
            elif line.strip() == in_fence:
                in_fence = None
        if in_fence is None and line.startswith("## ") and current:
            chunks.append("".join(current))
            current = []
        current.append(line)
    if current:
        chunks.append("".join(current))
    parts: list[str] = []
    buffer = ""
    for chunk in chunks:
        if buffer and len((buffer + chunk).encode("utf-8")) > max_bytes:
            parts.append(buffer)
            buffer = ""
        if len(chunk.encode("utf-8")) > max_bytes:
            lines = chunk.splitlines(keepends=True)
            piece = ""
            for line in lines:
                if piece and len((piece + line).encode("utf-8")) > max_bytes:
                    parts.append(piece + "\n\n_(section continues in the next part)_\n")
                    piece = ""
                piece += line
            buffer = piece
        else:
            buffer += chunk
    if buffer:
        parts.append(buffer)
    return parts


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def build_reference(root: Path, args: argparse.Namespace) -> tuple[str, dict[str, Any]]:
    print("[reference] 1/7 Coletando estado Git básico...", flush=True)
    redactor = Redactor(root)
    entries, tracked, untracked = collect_git_entries(root)
    print("[reference] 2/7 Inventariando arquivos locais...", flush=True)
    inventory, inventory_truncated = walk_inventory(root, tracked, untracked)
    inv_by_path = {row["path"]: row for row in inventory}
    existing_paths = set(inv_by_path)

    internal_roots = {
        Path(e.path).parts[0] for e in entries
        if e.exists and Path(e.path).suffix.lower() in {".py", ".pyi"} and len(Path(e.path).parts) > 1
    } | {"src", "tests", "tools"}

    selected: list[tuple[Path, bool, str]] = []
    seen: set[str] = set()
    for e in entries:
        if e.exists and include_source(Path(e.path), tracked=e.tracked):
            selected.append((Path(e.path), e.tracked, e.status))
            seen.add(e.path)
    ignored_sources: list[str] = []
    for row in inventory:
        rel_path = Path(row["path"])
        if (
            row["git"] == "ignored"
            and row["path"] not in seen
            and row["path"].startswith(IMPORTANT_UNTRACKED_PREFIXES)
            and include_source(rel_path, tracked=True)
        ):
            selected.append((rel_path, False, "!! ignored by .gitignore"))
            ignored_sources.append(row["path"])

    python_files: list[PythonFileAnalysis] = []
    notebooks: list[NotebookAnalysis] = []
    files_text: dict[str, str] = {}
    notebook_text: dict[str, str] = {}
    file_records: list[dict[str, Any]] = []
    source_sections: list[str] = []
    skipped: list[str] = []
    yaml_docs: dict[str, dict[str, Any]] = {}
    config: Any = None
    config_error: str | None = None
    yaml_duplicates: dict[str, list[str]] = {}
    pyproject_data: dict[str, Any] | None = None
    pyproject_error: str | None = None
    requirements: dict[str, str] | None = None

    print(
        f"[reference] 3/7 Lendo {len(selected)} arquivos de código, notebooks e documentação em integridade...",
        flush=True,
    )
    for indice_arquivo, (rel, is_tracked, status) in enumerate(selected, 1):
        if indice_arquivo == 1 or indice_arquivo % 10 == 0 or indice_arquivo == len(selected):
            print(
                f"[reference] Arquivo {indice_arquivo}/{len(selected)}: {rel.as_posix()}",
                flush=True,
            )
        absolute = root / rel
        data = absolute.read_bytes()
        digest = sha256_bytes(data)
        suffix = rel.suffix.lower()
        header = [
            f"## `{rel.as_posix()}`",
            "",
            f"- Git: `{'tracked' if is_tracked else 'untracked (working tree)'}` · status `{status.strip() or 'clean'}`",
            f"- Size: `{human_bytes(len(data))}` · modified `{inv_by_path.get(rel.as_posix(), {}).get('modified_utc', '?')} UTC`",
            f"- SHA-256: `{digest}`",
        ]
        record = {
            "path": rel.as_posix(), "tracked": is_tracked, "status": status, "sha256": digest,
            "bytes": len(data), "type": suffix.lstrip(".") or rel.name,
        }
        if suffix in LIKELY_BINARY_SUFFIXES:
            skipped.append(f"{rel.as_posix()} (binary)")
            continue
        if suffix == ".ipynb":
            try:
                analysis, nb = analyze_notebook(rel, data, internal_roots)
            except Exception as exc:
                skipped.append(f"{rel.as_posix()} (notebook parse error: {exc!r})")
                continue
            reduced = len(data) > args.max_inline_bytes
            analysis.outputs_included = args.notebook_outputs
            notebooks.append(analysis)
            notebook_text[rel.as_posix()] = "\n".join(
                "".join(c.get("source", [])) for c in nb.get("cells", [])
            )
            body = notebook_source_markdown(
                nb, analysis, include_outputs=args.notebook_outputs,
                max_output_chars=args.max_output_chars, reduced=reduced, redactor=redactor,
            )
            source_sections.append("\n".join(header) + "\n\n" + body + "\n")
            file_records.append(record)
            continue
        if suffix in OFFICE_SUFFIXES:
            try:
                text = office_text(data, suffix)
            except Exception as exc:
                skipped.append(f"{rel.as_posix()} (office parse error: {exc!r})")
                continue
            text, warnings = redactor(text)
            files_text[rel.as_posix()] = text
            header.append("- Content: plain text extracted (formatting, tables layout and images not preserved)")
            source_sections.append("\n".join(header) + "\n\n" + code_block(text.rstrip(), "text") + "\n")
            file_records.append(record)
            continue
        if b"\x00" in data[:8192]:
            skipped.append(f"{rel.as_posix()} (binary content)")
            continue
        decoded = data.decode("utf-8-sig", errors="replace")
        text, warnings = redactor(decoded)
        if rel.as_posix() == "tools/update_project_reference.py":
            text, warnings = decoded, []  # the generator's own regexes look like secrets
            for value in redactor.root_variants:
                text = text.replace(value, "<REPO>")
        files_text[rel.as_posix()] = text
        if warnings:
            header.append("- Security: " + "; ".join(warnings))
        if suffix in {".py", ".pyi"}:
            python_files.append(analyze_python(rel, text, internal_roots))
        elif suffix in {".yaml", ".yml"}:
            parsed, error, dups = load_yaml_strict(decoded)
            yaml_docs[rel.as_posix()] = {"error": error, "duplicates": dups}
            if dups:
                yaml_duplicates[rel.as_posix()] = dups
            if rel.as_posix() == args.config:
                config, config_error = parsed, error
        elif rel.name == "pyproject.toml":
            pyproject_data, pyproject_error = parse_pyproject(decoded)
        elif rel.name == "requirements.txt" and len(rel.parts) == 1:
            requirements = parse_requirements(decoded)
        # Source and documentation are included in full. Limits apply only to
        # notebook outputs and generated artifacts, never to code or project docs.
        body = code_block(text.rstrip(), LANG.get(suffix, "text"))
        source_sections.append("\n".join(header) + "\n\n" + body + "\n")
        file_records.append(record)

    # Small text artifacts (outputs/, data/ manifests, reports/)
    artifact_sections: list[str] = []
    artifact_records: list[dict[str, Any]] = []
    if args.artifacts:
        for row in inventory:
            rel = Path(row["path"])
            if not include_artifact(rel, row["bytes"], args.max_artifact_bytes):
                continue
            try:
                raw = (root / rel).read_bytes()
            except OSError:
                continue
            if b"\x00" in raw[:8192]:
                continue
            text, _ = redactor(raw.decode("utf-8-sig", errors="replace"))
            suffix = rel.suffix.lower()
            note = ""
            if suffix in {".csv", ".tsv"}:
                text, total = csv_preview(text, args.max_csv_rows)
                note = f" · {total} rows" + (f" (first {args.max_csv_rows} shown)" if total > args.max_csv_rows else "")
            else:
                text = truncate(text, args.max_artifact_bytes)
            artifact_sections.append(
                f"### `{rel.as_posix()}`\n\n- Git: `{row['git']}` · `{human_bytes(row['bytes'])}` · "
                f"modified `{row['modified_utc']} UTC`{note}\n\n"
                + code_block(text.rstrip(), LANG.get(suffix, "text")) + "\n"
            )
            artifact_records.append(row)
            if suffix in {".yaml", ".yml"}:
                files_text[rel.as_posix()] = text

    # Indexes and diagnostics
    symbols = [s for f in python_files for s in f.symbols]
    print("[reference] 4/7 Construindo catálogo de APIs, consumidores e testes...", flush=True)
    consumers = index_consumers(symbols, python_files, notebooks)
    tests = index_tests(symbols, python_files)
    import_map = top_level_import_map()
    packages = installed_packages()
    pyproject_deps = pyproject_dependencies(pyproject_data) if pyproject_data else None
    gates = nested_get(config, "gates", default={}) if isinstance(config, dict) else {}
    gate_names = set(gates) if isinstance(gates, dict) else set()
    code_text = "\n".join(
        [t for p, t in files_text.items() if p.endswith(".py")] + list(notebook_text.values())
    )

    attention: list[Attention] = []
    attention += working_tree_attention(entries)
    if ignored_sources:
        attention.append(Attention(
            "high", "source-ignored-by-git",
            "Source/config/test/notebook files are ignored by .gitignore and therefore missing from GitHub.",
            ignored_sources,
            "Fix .gitignore (anchor root folders, e.g. `/data/` instead of `data/`) and commit the files."))
    attention += import_integrity_attention(python_files, notebooks, internal_roots)
    attention += call_signature_attention(symbols, python_files, notebooks)
    attention += config_contract_attention(config, python_files)
    attention += gate_attention(gate_names, files_text, notebook_text)
    attention += unused_config_keys_attention(config, code_text)
    attention += dependency_attention(python_files, notebooks, requirements, pyproject_deps, import_map, internal_roots)
    attention += duplicate_symbol_attention(symbols)
    attention += notebook_attention(notebooks, python_files)
    attention += stale_document_attention(files_text, existing_paths)
    quality, todos = text_quality_attention(files_text, notebook_text)
    attention += quality
    attention += symbol_quality_attention(symbols, consumers, tests)
    for f in python_files:
        if f.parse_error:
            attention.append(Attention("high", "python-parse-error", f"`{f.path}` could not be parsed.",
                                       [f.parse_error], "Fix syntax or check interpreter compatibility."))
    if config_error:
        attention.append(Attention("high", "yaml-error", f"`{args.config}` could not be analysed.",
                                   [config_error], "Fix the YAML (or install PyYAML) and regenerate."))
    for path, dups in yaml_duplicates.items():
        attention.append(Attention("high", "yaml-duplicate-keys",
                                   f"`{path}` has duplicated keys; yaml.safe_load silently keeps the last value.",
                                   dups, "Remove the duplicates."))
    if pyproject_error:
        attention.append(Attention("high", "pyproject-invalid", "`pyproject.toml` is not valid TOML.",
                                   [pyproject_error], "Fix it; `pip install -e .` fails with an invalid pyproject."))
    if inventory_truncated:
        attention.append(Attention("low", "inventory-truncated",
                                   f"Path inventory stopped at {MAX_INVENTORY_ENTRIES} files.", [],
                                   "Exclude large generated folders or raise MAX_INVENTORY_ENTRIES."))

    if args.run_tests:
        print("[reference] 5/7 Executando pytest...", flush=True)
    else:
        print("[reference] 5/7 Pytest não solicitado; seguindo sem executar código...", flush=True)
    tests_result = run_tests(root, args.pytest_args, args.test_timeout) if args.run_tests else None
    if tests_result and tests_result["returncode"] not in (0, None):
        attention.append(Attention("high", "tests-failing", "pytest returned a non-zero exit code.",
                                   [tests_result["output"].splitlines()[-1] if tests_result["output"] else ""],
                                   "See Section 11."))

    print("[reference] 6/7 Coletando contexto Git rápido e montando documentos...", flush=True)

    # Git details
    branch = git(root, "branch", "--show-current").strip() or "detached"
    commit = git(root, "rev-parse", "HEAD", check=False).strip() or "no commits"
    remote, _ = redactor(git(root, "remote", "get-url", "origin", check=False).strip())
    status_text = git(root, "status", "--short", "--branch").rstrip() or "clean"
    log_text = git(root, "log", f"-{args.git_log}", "--date=iso", "--pretty=format:%h %ad %an%n    %s", check=False).rstrip()
    branches = git(root, "branch", "-a", "-vv", check=False).rstrip()
    ahead_behind = git(root, "rev-list", "--left-right", "--count", "HEAD...@{upstream}", check=False).strip()
    diff_stat = git(root, "diff", "HEAD", "--stat", check=False).rstrip()
    diff_text = ""
    if args.include_diff:
        raw_diff = git(root, "diff", "HEAD", "--", ".", ":(exclude)docs/" + OUTPUT_MD_NAME,
                       ":(exclude)docs/" + OUTPUT_JSON_NAME, check=False)
        diff_text = truncate(redactor(raw_diff)[0], args.max_diff_chars)
    gitignore_check = git(root, "check-ignore", "-v", "--no-index", *[
        p for p in ("data/", "outputs/", "models/", ".env", "configs/paths.local.json") if (root / p).exists()
    ], check=False).strip() if any((root / p).exists() for p in ("data", "outputs", "models", ".env")) else ""

    generated = datetime.now(timezone.utc).isoformat(timespec="seconds")
    counts = Counter(a.severity for a in attention)
    public = [s for s in symbols if s.path.startswith("src/") and not s.is_private and s.kind in {"function", "class"}]

    # ---- Section 6
    sec6 = [
        "## 6. Executive continuation map", "",
        f"- Generated (UTC): `{generated}` · branch `{branch}` · commit `{commit[:12]}`",
        f"- Git status: `{'clean' if status_text.count(chr(10)) == 0 else 'has changes'}`; upstream ahead/behind: `{ahead_behind or 'n/a'}`",
        f"- Files in working folder (inventory): `{len(inventory)}` "
        f"(tracked `{sum(r['git'] == 'tracked' for r in inventory)}`, untracked `{sum(r['git'] == 'untracked' for r in inventory)}`, "
        f"ignored/local `{sum(r['git'] == 'ignored' for r in inventory)}`)",
        f"- Source files with full content: `{len(file_records)}`; artifacts included: `{len(artifact_records)}`",
        f"- Python modules: `{len(python_files)}` · notebooks: `{len(notebooks)}` · public src symbols: `{len(public)}`",
        f"- Public src symbols with tests: `{sum(bool(tests.get(f'{s.module}.{s.qualname}')) for s in public)}` · with consumers: "
        f"`{sum(bool(consumers.get(f'{s.module}.{s.qualname}')) for s in public)}`",
        f"- Attention items: **{counts.get('high', 0)} high**, {counts.get('medium', 0)} medium, {counts.get('low', 0)} low",
        f"- Tests executed: `{'yes, exit ' + str(tests_result['returncode']) if tests_result else 'no (use --run-tests)'}`",
        "",
        "### Canonical responsibility map", "",
        render_table(["Responsibility", "Inspect first"], [
            ["Data access and Parquet", "`src/utils/storage.py`, `src/utils/config.py`"],
            ["Cohort and supervised artifact", "`src/data/`, cohort notebooks, `tests/test_cohort_source.py`"],
            ["Feature engineering", "`src/features/`, `tests/test_features.py`, YAML `features`"],
            ["Split and leakage", "`src/data/split.py`, `src/evaluation/leakage.py`, split tests"],
            ["Models and pipelines", "`src/models/`, `tests/test_model_pipelines.py`"],
            ["Metrics, calibration, errors", "`src/evaluation/`, `src/models/calibration.py`"],
            ["Experiment logging", "`src/utils/reproducibility.py`"],
            ["Decisions and gates", f"`{args.config}`, `docs/decisoes.md`"],
        ]),
    ]

    # ---- Section 8: configuration
    sec8 = ["## 8. Configuration", ""]
    if isinstance(config, dict):
        if gate_names:
            sec8 += ["### Gates", "", render_table(
                ["Gate", "Status", "Approved by", "Date", "Description"],
                [[f"`{k}`", str(nested_get(gates, k, "status")), str(nested_get(gates, k, "aprovado_por")),
                  str(nested_get(gates, k, "data")), str(nested_get(gates, k, "descricao") or "").strip()[:160]]
                 for k in gates]), ""]
        sec8 += ["### Flattened active configuration", "", f"Source: `{args.config}`", ""]
        sec8 += [f"- `{k}`: `{repr(v)[:400]}`" for k, v in flatten_mapping(config).items()]
    else:
        sec8.append(f"- Configuration unavailable: `{config_error}`")
    sec8 += ["", "### YAML files", "", render_table(
        ["File", "Parse", "Duplicated keys"],
        [[f"`{p}`", "ok" if not d["error"] else d["error"][:80], ", ".join(d["duplicates"]) or "none"]
         for p, d in sorted(yaml_docs.items())])]
    sec8 += ["", "### pyproject.toml", ""]
    if pyproject_data is not None:
        sec8 += [
            f"- Valid TOML: yes · name `{nested_get(pyproject_data, 'project', 'name')}` · "
            f"requires-python `{nested_get(pyproject_data, 'project', 'requires-python')}`",
            "- Dependencies: " + (", ".join(f"`{k}{v}`" for k, v in (pyproject_deps or {}).items()) or "none"),
        ]
    else:
        sec8.append(f"- {pyproject_error or 'not found'}")
    sec8 += ["", "### requirements.txt", "",
             "- " + (", ".join(f"`{k}{v}`" for k, v in requirements.items()) if requirements else "not found")]

    # ---- Section 9: environment
    key_rows = []
    declared = {**(requirements or {}), **(pyproject_deps or {})}
    for name in KEY_PACKAGES:
        if name in packages or name in declared:
            key_rows.append([f"`{name}`", packages.get(name, "**not installed**"),
                             (requirements or {}).get(name, "—") if requirements is not None else "n/a",
                             (pyproject_deps or {}).get(name, "—") if pyproject_deps is not None else "n/a"])
    sec9 = [
        "## 9. Python environment", "",
        f"- Interpreter: `{sys.version.split()[0]}` · implementation `{platform.python_implementation()}`",
        f"- Executable inside repo venv: `{'yes' if str(root).lower() in sys.executable.lower() else 'no (results reflect another interpreter)'}`",
        f"- Platform: `{platform.platform()}`",
        f"- PyYAML available: `{yaml is not None}` · tomllib available: `{tomllib is not None}`",
        "", "### Key packages: installed vs declared", "",
        render_table(["Package", "Installed", "requirements.txt", "pyproject.toml"], key_rows),
        "", "### All installed distributions", "",
        code_block("\n".join(f"{k}=={v}" for k, v in packages.items()), "text"),
    ]

    # ---- Section 10: inventory
    sec10 = [
        "## 10. Path inventory of the working folder", "",
        "Contents of data/models are never copied. `ignored` = exists locally but is ignored by Git.", "",
        "### Directory tree", "", render_tree(inventory), "",
        "### All files", "",
        render_table(["Path", "Git", "Size", "Modified (UTC)"],
                     [[f"`{r['path']}`", r["git"], human_bytes(r["bytes"]), r["modified_utc"]] for r in inventory]),
        "", "### Skipped files", "", *(f"- `{s}`" for s in skipped), *([] if skipped else ["- None."]),
        "", "### .gitignore check for local folders", "", code_block(gitignore_check or "n/a", "text"),
    ]

    # ---- Section 11: tests
    test_rows = []
    for f in python_files:
        if f.path.startswith("tests/") or Path(f.path).name.startswith("test_"):
            names = [s.qualname for s in f.symbols if s.name.startswith("test_")]
            test_rows.append([f"`{f.path}`", str(len(names)), ", ".join(f"`{v}`" for v in f.internal_imports) or "none"])
    sec11 = ["## 11. Tests", "", render_table(["Test file", "Tests", "Internal imports"], test_rows), ""]
    if tests_result:
        sec11 += [f"### pytest result (exit `{tests_result['returncode']}`)", "",
                  f"Command: `{tests_result['command']}`", "",
                  code_block(truncate(redactor(tests_result["output"])[0], 60_000), "text")]
    else:
        sec11.append("pytest was not executed. Use `--run-tests` (optionally `--pytest-args \"-m 'not slow'\"`).")

    # ---- Section 13/14/15
    dep_rows = [[f"`{f.module}`", ", ".join(f"`{v}`" for v in f.internal_imports) or "none"]
                for f in sorted(python_files, key=lambda x: x.module)]
    sec13 = ["## 13. Internal dependency map", "", render_table(["Module", "Internal imports"], dep_rows)]
    nb_rows = [[f"`{n.path}`", f"{n.code_cells}/{n.markdown_cells}", f"{n.executed_cells}/{n.code_cells}",
                "yes" if n.out_of_order else "no", str(len(n.error_outputs)),
                ", ".join(f"`{v}`" for v in n.internal_imports) or "none",
                ", ".join(f"`{s.name}`" for s in n.functions + n.classes) or "none"]
               for n in sorted(notebooks, key=lambda x: x.path)]
    sec14 = ["## 14. Notebook orchestration inventory", "",
             render_table(["Notebook", "Code/MD cells", "Executed", "Out of order", "Errors",
                           "Internal imports", "Local functions"], nb_rows), ""]
    for n in sorted(notebooks, key=lambda x: x.path):
        sec14 += [f"### `{n.path}` headings", "", *(f"- {h}" for h in n.headings), ""]
        if n.file_literals:
            sec14 += ["Referenced files: " + ", ".join(f"`{v}`" for v in n.file_literals), ""]
    env_index: defaultdict[str, set[str]] = defaultdict(set)
    for f in python_files:
        for e in f.env_vars:
            env_index[e].add(f.path)
    for n in notebooks:
        for e in n.env_vars:
            env_index[e].add(n.path)
    lit_index: defaultdict[str, set[str]] = defaultdict(set)
    for f in python_files:
        for lit in f.file_literals:
            lit_index[lit].add(f.path)
    for n in notebooks:
        for lit in n.file_literals:
            lit_index[lit].add(n.path)
    sec15 = ["## 15. Environment variables, file literals and TODOs", "",
             "### Environment variables (names only)", "",
             *([f"- `{k}`: " + ", ".join(f"`{p}`" for p in sorted(v)) for k, v in sorted(env_index.items())] or ["- None."]),
             "", "### File names referenced in code", "",
             *([f"- `{k}` ← " + ", ".join(f"`{p}`" for p in sorted(v)) for k, v in sorted(lit_index.items())] or ["- None."]),
             "", "### TODO / FIXME / PENDENTE markers", "", *([f"- `{t}`" for t in todos] or ["- None."])]

    sec16 = ["## 16. Git history and uncommitted changes", "",
             "### Status", "", code_block(status_text, "text"), "",
             "### Branches", "", code_block(redactor(branches)[0] or "n/a", "text"), "",
             f"### Last {args.git_log} commits", "", code_block(redactor(log_text)[0] or "no commits", "text"), "",
             "### Diff stat (working tree vs HEAD)", "", code_block(diff_stat or "no changes", "text")]
    if args.include_diff:
        sec16 += ["", "### Full diff (working tree vs HEAD)", "", code_block(diff_text or "no changes", "diff")]

    document_parts = [
        CONTEXT.format(schema=SCHEMA_VERSION).rstrip(), "",
        *sec6, "",
        "## 7. Static attention report", "", render_attention(attention), "",
        *sec8, "", *sec9, "", *sec10, "", *sec11, "",
        "## 12. Python API and reuse catalog", "",
        "Generated with Python AST; project modules are not imported.", "",
        render_python_api(python_files, consumers, tests), "",
        *sec13, "", *sec14, "", *sec15, "", *sec16, "",
        "## 17. Full source by file", "",
        "Every relevant file of the repository, including untracked files in source folders. "
        "Notebooks include cell sources and, unless disabled, text outputs.", "",
        "\n".join(source_sections).rstrip(), "",
        "## 18. Local artifacts (small text files from data/, outputs/, reports/, models/)", "",
        ("\n".join(artifact_sections).rstrip() if artifact_sections else "- None included (use defaults or check --no-artifacts)."),
        "",
        "## 19. Snapshot provenance", "",
        f"- Generated UTC: `{generated}`",
        f"- Branch / commit: `{branch}` / `{commit}`",
        f"- Origin: `{remote or 'not configured'}`",
        f"- Generator options: `{ {k: (str(v) if isinstance(v, Path) else v) for k, v in vars(args).items()} }`",
    ]
    document = "\n".join(document_parts).rstrip() + "\n"

    machine = {
        "schema_version": SCHEMA_VERSION,
        "generated_utc": generated,
        "repository": {"branch": branch, "commit": commit, "origin": remote or None,
                       "status": status_text, "ahead_behind": ahead_behind},
        "environment": {"python": sys.version.split()[0], "platform": platform.platform(), "packages": packages},
        "inventory": inventory,
        "files": file_records,
        "artifacts": artifact_records,
        "python_files": [asdict(f) for f in python_files],
        "notebooks": [asdict(n) for n in notebooks],
        "consumers": consumers,
        "tests_by_symbol": tests,
        "attention": [asdict(a) for a in attention],
        "environment_variables": {k: sorted(v) for k, v in sorted(env_index.items())},
        "config": config if isinstance(config, (dict, list)) else None,
        "config_error": config_error,
        "yaml_files": yaml_docs,
        "pyproject": {"valid": pyproject_data is not None, "error": pyproject_error, "dependencies": pyproject_deps},
        "requirements": requirements,
        "tests_result": tests_result,
        "todos": todos,
        "skipped": skipped,
    }
    return document, machine


def parse_args() -> argparse.Namespace:
    # argparse rejects values that start with "-" (e.g. --pytest-args "-m 'not slow'").
    argv = sys.argv[1:]
    for index, value in enumerate(argv[:-1]):
        if value == "--pytest-args" and argv[index + 1].startswith("-"):
            argv[index : index + 2] = [f"--pytest-args={argv[index + 1]}"]
            break
    parser = argparse.ArgumentParser(
        description="Generate a complete diagnostic snapshot of the repository for review by a person or an AI.")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR, help="Destination folder (default: docs).")
    parser.add_argument("--config", default="configs/supervised.yaml", help="Main YAML configuration (relative path).")
    parser.add_argument("--split-mb", type=float, default=DEFAULT_SPLIT_MB,
                        help=f"Size of each part in docs/{PARTS_DIR_NAME}/ (default: {DEFAULT_SPLIT_MB} MB).")
    parser.add_argument("--no-split", dest="split", action="store_false",
                        help=f"Do not write docs/{PARTS_DIR_NAME}/.")
    parser.add_argument("--no-notebook-outputs", dest="notebook_outputs", action="store_false",
                        help="Omit notebook outputs (sources only).")
    parser.add_argument("--max-output-chars", type=int, default=DEFAULT_MAX_OUTPUT_CHARS,
                        help="Maximum characters per notebook output.")
    parser.add_argument("--artifacts", dest="artifacts", action="store_true",
                        help="Also include small generated text artifacts. Disabled by default for speed.")
    parser.add_argument("--max-artifact-bytes", type=int, default=DEFAULT_MAX_ARTIFACT_BYTES)
    parser.add_argument("--max-csv-rows", type=int, default=DEFAULT_MAX_CSV_ROWS)
    parser.add_argument("--max-inline-bytes", type=int, default=DEFAULT_MAX_INLINE_BYTES,
                        help="Legacy compatibility option. Source and documentation are always included in full.")
    parser.add_argument("--git-log", type=int, default=DEFAULT_GIT_LOG, help="Number of recent commits to list.")
    parser.add_argument("--include-diff", dest="include_diff", action="store_true",
                        help="Include the full uncommitted diff. Disabled by default for speed.")
    parser.add_argument("--max-diff-chars", type=int, default=DEFAULT_MAX_DIFF_CHARS)
    parser.add_argument("--run-tests", action="store_true", help="Run pytest and include the result (executes project code).")
    parser.add_argument("--pytest-args", default="", help="Extra pytest arguments, e.g. \"-m 'not slow'\".")
    parser.add_argument("--test-timeout", type=int, default=1800)
    parser.add_argument("--fail-on-high", action="store_true", help="Exit with code 2 if HIGH attention items exist.")
    return parser.parse_args(argv)


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # Windows consoles
        except Exception:
            pass
    args = parse_args()
    root = root_dir()
    document, machine = build_reference(root, args)
    print("[reference] 7/7 Gravando Markdown, JSON e partes...", flush=True)
    out_dir = root / args.output_dir
    output_md = out_dir / OUTPUT_MD_NAME
    output_json = out_dir / OUTPUT_JSON_NAME
    atomic_write(output_md, document)
    atomic_write(output_json, json.dumps(machine, ensure_ascii=False, indent=2, default=str) + "\n")

    parts_dir = out_dir / PARTS_DIR_NAME
    if parts_dir.exists():
        for old in parts_dir.glob("part_*.md"):
            old.unlink()
    written_parts: list[Path] = []
    if args.split and args.split_mb > 0:
        parts = split_document(document, int(args.split_mb * 1024 * 1024))
        for index, part in enumerate(parts, 1):
            target = parts_dir / f"part_{index:02d}_of_{len(parts):02d}.md"
            header = f"<!-- PROJECT_COMPLETE_REFERENCE part {index}/{len(parts)} -->\n"
            atomic_write(target, header + part)
            written_parts.append(target)

    high = sum(a.get("severity") == "high" for a in machine["attention"])
    print(f"update_project_reference.py schema v{SCHEMA_VERSION}")
    print(f"Updated: {output_md} ({human_bytes(output_md.stat().st_size)})")
    print(f"Updated: {output_json} ({human_bytes(output_json.stat().st_size)})")
    if written_parts:
        print(f"Parts:   {len(written_parts)} file(s) in {parts_dir}")
        for part in written_parts:
            print(f"         {part.name} ({human_bytes(part.stat().st_size)})")
    else:
        print("Parts:   not written (--no-split)")
    print(f"Inventory: {len(machine['inventory'])} files, full source: {len(machine['files'])}, "
          f"artifacts: {len(machine['artifacts'])}")
    print(f"Python modules: {len(machine['python_files'])}, notebooks: {len(machine['notebooks'])}")
    print(f"Attention items: {len(machine['attention'])} ({high} high)")
    if machine.get("tests_result"):
        print(f"pytest exit code: {machine['tests_result']['returncode']}")
    if args.fail_on_high and high:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

## 18. Local artifacts (small text files from data/, outputs/, reports/, models/)

- None included (use defaults or check --no-artifacts).

## 19. Snapshot provenance

- Generated UTC: `2026-10-18T16:40:28+00:00`
- Branch / commit: `main` / `9fa6e694d08430d3fcb9d94c00fbec8a775080e1`
- Origin: `https://github.com/Ivan-S-Oliveira/Projeto_Integrador.git`
- Generator options: `{'output_dir': 'docs', 'config': 'configs/supervised.yaml', 'split_mb': 1.0, 'split': True, 'notebook_outputs': True, 'max_output_chars': 6000, 'artifacts': False, 'max_artifact_bytes': 300000, 'max_csv_rows': 60, 'max_inline_bytes': 4000000, 'git_log': 10, 'include_diff': False, 'max_diff_chars': 400000, 'run_tests': False, 'pytest_args': '', 'test_timeout': 1800, 'fail_on_high': False}`
