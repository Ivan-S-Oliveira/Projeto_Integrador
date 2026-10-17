<!-- PROJECT_COMPLETE_REFERENCE part 3/3 -->
## `src/protocolo/verificacoes.py`

- Git: `tracked` · status `clean`
- Size: `89.8 KB` · modified `2026-10-16 01:28 UTC`
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
- Size: `0 B` · modified `2026-10-06 02:28 UTC`
- SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

```python

```

## `src/utils/config.py`

- Git: `tracked` · status `clean`
- Size: `8.0 KB` · modified `2026-10-16 01:28 UTC`
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
- Size: `3.7 KB` · modified `2026-10-16 01:28 UTC`
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
- Size: `891 B` · modified `2026-10-16 01:28 UTC`
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

## `src/utils/reproducibility.py`

- Git: `tracked` · status `clean`
- Size: `13.1 KB` · modified `2026-10-16 01:28 UTC`
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
- Size: `8.8 KB` · modified `2026-10-16 01:28 UTC`
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
- Size: `639 B` · modified `2026-10-16 01:28 UTC`
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
- Size: `3.5 KB` · modified `2026-10-16 01:28 UTC`
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
- Size: `2.1 KB` · modified `2026-10-16 01:28 UTC`
- SHA-256: `81aae255c95584ea1c6178160a6e4b8a19fd4d8833ff17fa29bc4ec9b22c67e4`

```python
"""Testes do resolvedor de coorte (provisória, final, auto)."""

from pathlib import Path

import pandas as pd
import pytest

from src.data.cohort_source import cohort_candidates, load_cohort, resolve_cohort_path


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


def test_padrao_permanece_provisorio(tmp_path: Path) -> None:
    paths = cohort_candidates(tmp_path)
    _write(paths["provisional"][1], 1)   # coorte_provisoria_b.parquet
    _write(paths["final"][0], 2)         # coorte_final.parquet (existe, mas não é o default)

    kind, path = resolve_cohort_path(tmp_path)

    assert kind == "provisional"
    assert path.name == "coorte_provisoria_b.parquet"


def test_final_exige_escolha_explicita(tmp_path: Path) -> None:
    path = cohort_candidates(tmp_path)["final"][0]
    _write(path, 2)

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


def test_tipo_invalido_falha(tmp_path: Path) -> None:
    # Valor viola intencionalmente o Literal CohortKind.
    with pytest.raises(ValueError, match="provisional, final ou auto"):
        resolve_cohort_path(tmp_path, kind="desconhecida")  # type: ignore[arg-type]
```

## `tests/test_config.py`

- Git: `tracked` · status `clean`
- Size: `7.4 KB` · modified `2026-10-16 01:28 UTC`
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
- Size: `5.5 KB` · modified `2026-10-16 01:28 UTC`
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
- Size: `11.3 KB` · modified `2026-10-16 01:28 UTC`
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
- Size: `3.9 KB` · modified `2026-10-16 01:28 UTC`
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
- Size: `5.5 KB` · modified `2026-10-16 01:28 UTC`
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
- Size: `6.2 KB` · modified `2026-10-16 01:28 UTC`
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
- Size: `2.7 KB` · modified `2026-10-16 01:28 UTC`
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
- Size: `22.9 KB` · modified `2026-10-16 01:28 UTC`
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
- Size: `5.1 KB` · modified `2026-10-16 01:28 UTC`
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
- Size: `3.2 KB` · modified `2026-10-16 01:28 UTC`
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
- Size: `9.4 KB` · modified `2026-10-16 01:28 UTC`
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
- Size: `3.0 KB` · modified `2026-10-16 01:28 UTC`
- SHA-256: `a96b43cbaabb4dfc300bb4984a27705cea7d68b5c33607eedd157aeb1b2b7d44`

```python
"""Testes do artefacto supervisionado (``src.data.supervised_artifact``).

Cobrem o contrato de persistência/leitura: preservação da partição,
validação do tipo de coorte e exigência das três partições.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from src.data.supervised_artifact import (
    load_supervised_artifact,
    persist_supervised_artifact,
)


def _frame() -> pd.DataFrame:
    """6 registos — 2 por partição, alvo alternado (0/1).

    Colunas mínimas para os testes: uma feature numérica, o alvo binário
    e a coluna de partição.
    """
    return pd.DataFrame({
        "idade_anos":      [10.0, 20.0, 30.0, 40.0, 50.0, 60.0],
        "alvo_obito_srag": [0, 1, 0, 1, 0, 1],
        "particao":        ["treino", "treino", "validacao", "validacao", "teste", "teste"],
    })


def _persistir(tmp_path: Path, frame: pd.DataFrame, **kwargs: Any) -> None:
    """Grava ``frame`` como artefacto supervisionado em ``tmp_path``.

    Preenche os kwargs obrigatórios com valores mínimos e deixa
    ``**kwargs`` sobrepor (ex.: ``source`` com conteúdo).
    """
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


# ---------------------------------------------------------------------------
# Contrato de round-trip
# ---------------------------------------------------------------------------

def test_roundtrip_preserva_particao(tmp_path: Path) -> None:
    """Gravar e ler preserva a partição, e o manifesto regista o estado inicial."""
    frame = _frame()
    _persistir(tmp_path, frame, source={"kind": "provisional", "sha256": "abc"})

    loaded, manifest = load_supervised_artifact(tmp_path, expected_kind="provisional")

    assert loaded["particao"].tolist() == frame["particao"].tolist()
    assert manifest["test_opened"] is False
    assert manifest["seed"] == 42


# ---------------------------------------------------------------------------
# Validações
# ---------------------------------------------------------------------------

def test_tipo_de_coorte_incorreto_falha(tmp_path: Path) -> None:
    """Ler com ``expected_kind`` diferente do gravado deve falhar."""
    _persistir(tmp_path, _frame())

    with pytest.raises(RuntimeError, match="SRAG_COHORT_KIND"):
        load_supervised_artifact(tmp_path, expected_kind="final")


def test_particoes_incompletas_falham(tmp_path: Path) -> None:
    """Dataset sem o bloco ``teste`` viola o contrato de partições."""
    frame = _frame().query("particao != 'teste'")

    with pytest.raises(ValueError, match="Particoes esperadas"):
        _persistir(tmp_path, frame)
```

## `tests/test_target.py`

- Git: `tracked` · status `clean`
- Size: `3.7 KB` · modified `2026-10-16 01:28 UTC`
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
- Size: `5.9 KB` · modified `2026-10-16 01:28 UTC`
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
- Size: `3.7 KB` · modified `2026-10-16 01:28 UTC`
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

## `tools/update_project_reference.py`

- Git: `tracked` · status `clean`
- Size: `103.7 KB` · modified `2026-10-15 12:51 UTC`
- SHA-256: `b7e910e208d84ce466c8718e858de196eea7ea6bf306cc87247d1af23f6b7b0d`

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
    full diff of uncommitted changes (capped).
2.  Full path inventory of the working folder, including ignored and local
    folders (data/, outputs/, models/, reports/), with size, modification time
    and Git state. File contents of data are never copied.
3.  Full source of every relevant text file: .py, .ipynb, .md, .yaml, .yml,
    .toml, .json, .csv (capped), .txt, .ini, .cfg, .ps1, .sh, .sql, etc.
4.  Notebooks: every cell source, execution counts and, by default, the TEXT
    outputs (streams, text/plain results, errors and tracebacks). Images and
    HTML are replaced by placeholders. Execution order problems are reported.
5.  Small text artifacts produced by the project (manifests, waterfalls,
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

SCHEMA_VERSION = 4

OUTPUT_DIR = Path("docs")
OUTPUT_MD_NAME = "PROJECT_COMPLETE_REFERENCE.md"
OUTPUT_JSON_NAME = "PROJECT_COMPLETE_REFERENCE.json"
PARTS_DIR_NAME = "project_reference_parts"

DEFAULT_MAX_INLINE_BYTES = 4_000_000
DEFAULT_MAX_OUTPUT_CHARS = 6_000
DEFAULT_MAX_ARTIFACT_BYTES = 300_000
DEFAULT_MAX_CSV_ROWS = 60
DEFAULT_MAX_DIFF_CHARS = 400_000
DEFAULT_GIT_LOG = 40
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

This reference lets a person or an AI diagnose the SRAG project without prior
conversation context and without access to the machine. It contains the full
source of code, notebooks (with text outputs), configuration and documentation,
plus the Git state, the local path inventory, installed package versions,
parsed configuration and static consistency checks.

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
    redactor = Redactor(root)
    entries, tracked, untracked = collect_git_entries(root)
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

    for rel, is_tracked, status in selected:
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
            source_sections.append("\n".join(header) + "\n\n" + code_block(truncate(text, args.max_inline_bytes), "text") + "\n")
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
        if suffix in {".csv", ".tsv"} and len(data) > args.max_artifact_bytes:
            preview, total = csv_preview(text, args.max_csv_rows)
            header.append(f"- Content: first {args.max_csv_rows} of {total} rows")
            body = code_block(preview, "csv")
        elif len(data) > args.max_inline_bytes:
            body = code_block(truncate(text, args.max_inline_bytes), LANG.get(suffix, "text"))
        else:
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

    tests_result = run_tests(root, args.pytest_args, args.test_timeout) if args.run_tests else None
    if tests_result and tests_result["returncode"] not in (0, None):
        attention.append(Attention("high", "tests-failing", "pytest returned a non-zero exit code.",
                                   [tests_result["output"].splitlines()[-1] if tests_result["output"] else ""],
                                   "See Section 11."))

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
    parser.add_argument("--no-artifacts", dest="artifacts", action="store_false",
                        help="Do not include small text artifacts from data/, outputs/, reports/, models/.")
    parser.add_argument("--max-artifact-bytes", type=int, default=DEFAULT_MAX_ARTIFACT_BYTES)
    parser.add_argument("--max-csv-rows", type=int, default=DEFAULT_MAX_CSV_ROWS)
    parser.add_argument("--max-inline-bytes", type=int, default=DEFAULT_MAX_INLINE_BYTES,
                        help="Files above this size are truncated (notebooks use a reduced view).")
    parser.add_argument("--git-log", type=int, default=DEFAULT_GIT_LOG, help="Number of recent commits to list.")
    parser.add_argument("--no-diff", dest="include_diff", action="store_false", help="Omit the full uncommitted diff.")
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

## `configs/paths.local.json`

- Git: `untracked (working tree)` · status `!! ignored by .gitignore`
- Size: `45 B` · modified `2026-10-08 01:30 UTC`
- SHA-256: `6a840ee1f558f2fa14ca762c3df41bf82300c680614792cd298d857ea68da198`

```json
{
"parquet_srag": "data/raw/srag.parquet"
}
```

## 18. Local artifacts (small text files from data/, outputs/, reports/, models/)

### `data/manifest_dados-v2.yaml`

- Git: `tracked` · `1.9 KB` · modified `2026-10-10 16:31 UTC`

```yaml
manifest_version: "1.0"

dataset:
  id: "srag-dados-v2"
  versao: "dados-v2"
  arquivo: "srag.parquet"
  formato: "parquet"
  caminho_relativo: "data/processed/dados-v2/srag.parquet"

integridade:
  sha256: "96ED6B9D5CEEBAAEA00659F77511112174B04BB980CB243B560C00DD2A8F316C
  tamanho_bytes: 303573013
  quantidade_linhas: 4666910
  quantidade_colunas: 198

cobertura_temporal:
  periodo_nominal_fontes: "2019-2026"
  periodo_observado_dt_notific:
    inicio: "2018-12-30"
    fim: "2026-09-28"
  observacao:
    - "Foram observados três registros com dt_notific em 2018."
    - "A elegibilidade temporal da coorte será definida por dt_interna, não por dt_notific."
    - "O recorte analítico principal considera internações entre 2019 e 2026."
    - "O ano de 2026 está incompleto na versão atual dos dados e deverá ser identificado como tal nas análises temporais."
    - "Os anos associados à pandemia serão mantidos inicialmente; qualquer exclusão posterior será tratada como análise de sensibilidade."

geracao:
  data_geracao: "2026-10-09"
  motivo_nova_versao: >
    Correção da geração de dt_notific. Na versão dados-v1,
    a coluna não preservava as datas individuais de notificação
    e apresentava valores concentrados em âncoras anuais do
    calendário epidemiológico. A versão dados-v2 preserva os
    valores individuais provenientes das fontes oficiais.

fontes:
  - nome: "Dados Abertos do SUS - SRAG 2019 a 2026"
    url: "https://dadosabertos.saude.gov.br/dataset/srag-2019-a-2026"

uso_no_projeto:
  interface_leitura: "src.utils.storage.read_srag"
  versao_configurada: "dados-v2"
  observacao: >
    Os notebooks devem acessar o dataset pela interface de storage
    do repositório, evitando caminhos locais absolutos.

validacao:
  schema_verificado: true
  dimensoes_verificadas: true
  notebook_validacao: "01_eda_primeira_passagem.ipynb"
  hash_confirmado_manualmente: true
```

### `data/analytical/dataset_supervisionado.meta.json`

- Git: `ignored` · `1.6 KB` · modified `2026-10-17 00:27 UTC`

```json
{
  "versao": "1.0",
  "criado_em": "2026-10-16T21:27:25",
  "arquivo": "<REPO>\\data\\analytical\\dataset_supervisionado.parquet",
  "n_linhas": 1236075,
  "colunas": [
    "nu_notific",
    "dt_interna",
    "evolucao",
    "idade_anos",
    "cs_gestant",
    "cs_raca",
    "cs_zona",
    "ave_suino",
    "febre",
    "tosse",
    "garganta",
    "dispneia",
    "diarreia",
    "vomito",
    "dor_abd",
    "fadiga",
    "perd_olft",
    "perd_pala",
    "outro_sin",
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
    "sg_uf",
    "faixa_etaria",
    "ano_internacao"
  ],
  "alvo": "evolucao",
  "coluna_tempo": "dt_interna",
  "anos": {
    "2022": 475980,
    "2023": 240704,
    "2024": 229478,
    "2025": 289913
  },
  "desenvolvimento": [
    2022,
    2023,
    2024
  ],
  "holdout": [
    2025
  ],
  "features_proibidas_no_dataset": [],
  "features_ausentes_na_base": [
    "DIAS_SINTOMAS_ATE_INTERNACAO",
    "SEXO_CATEGORIA"
  ],
  "base_origem_linhas": 4666910,
  "aliases_aplicados_yaml_para_fisico": {},
  "descartadas_data_tempo_invalida": 0,
  "derivadas_criadas": [
    "idade_anos",
    "faixa_etaria"
  ],
  "grupos_avaliacao_incluidos": [
    "sg_uf",
    "faixa_etaria"
  ],
  "sha256": "add8eeb8a6a250383d2203a05135844da9e823acc3a9557b785b7a01b159d27c"
}
```

### `data/analytical/dataset_supervisionado_sem_2020_2021.meta.json`

- Git: `ignored` · `1.9 KB` · modified `2026-10-17 00:51 UTC`

```json
{
  "versao": "0.1",
  "criado_em": "2026-10-16T21:51:46",
  "arquivo": "<REPO>\\data\\analytical\\dataset_supervisionado_sem_2020_2021.parquet",
  "n_linhas": 1279588,
  "colunas": [
    "nu_notific",
    "dt_interna",
    "evolucao",
    "idade_anos",
    "cs_gestant",
    "cs_raca",
    "cs_zona",
    "ave_suino",
    "febre",
    "tosse",
    "garganta",
    "dispneia",
    "diarreia",
    "vomito",
    "dor_abd",
    "fadiga",
    "perd_olft",
    "perd_pala",
    "outro_sin",
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
    "sg_uf",
    "faixa_etaria",
    "ano_internacao",
    "split"
  ],
  "alvo": "evolucao",
  "coluna_tempo": "dt_interna",
  "anos": {
    "2019": 43513,
    "2022": 475980,
    "2023": 240704,
    "2024": 229478,
    "2025": 289913
  },
  "desenvolvimento": [
    2019,
    2022,
    2023,
    2024,
    2025
  ],
  "holdout": [],
  "features_proibidas_no_dataset": [],
  "features_ausentes_na_base": [
    "DIAS_SINTOMAS_ATE_INTERNACAO",
    "SEXO_CATEGORIA"
  ],
  "base_origem_linhas": 4666910,
  "aliases_aplicados_yaml_para_fisico": {},
  "descartadas_data_tempo_invalida": 0,
  "derivadas_criadas": [
    "idade_anos",
    "faixa_etaria"
  ],
  "grupos_avaliacao_incluidos": [
    "sg_uf",
    "faixa_etaria"
  ],
  "sha256": "e7c5c4a56d29bc72aab0b0c9a7b6dd67dae4830e758c97998a4bac1aca5444b9",
  "split": {
    "tipo": "aleatorio",
    "seed": 42,
    "fracoes": {
      "treino": 0.7,
      "validacao": 0.15,
      "holdout": 0.15
    },
    "contagem": {
      "treino": 895712,
      "holdout": 191938,
      "validacao": 191938
    }
  }
}
```

### `data/analytical/dataset_supervisionado_todos_2019_2025.meta.json`

- Git: `ignored` · `1.9 KB` · modified `2026-10-17 00:50 UTC`

```json
{
  "versao": "0.1",
  "criado_em": "2026-10-16T21:50:56",
  "arquivo": "<REPO>\\data\\analytical\\dataset_supervisionado_todos_2019_2025.parquet",
  "n_linhas": 3739615,
  "colunas": [
    "nu_notific",
    "dt_interna",
    "evolucao",
    "idade_anos",
    "cs_gestant",
    "cs_raca",
    "cs_zona",
    "ave_suino",
    "febre",
    "tosse",
    "garganta",
    "dispneia",
    "diarreia",
    "vomito",
    "dor_abd",
    "fadiga",
    "perd_olft",
    "perd_pala",
    "outro_sin",
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
    "sg_uf",
    "faixa_etaria",
    "ano_internacao",
    "split"
  ],
  "alvo": "evolucao",
  "coluna_tempo": "dt_interna",
  "anos": {
    "2019": 43513,
    "2020": 979812,
    "2021": 1480215,
    "2022": 475980,
    "2023": 240704,
    "2024": 229478,
    "2025": 289913
  },
  "desenvolvimento": [
    2019,
    2020,
    2021,
    2022,
    2023,
    2024,
    2025
  ],
  "holdout": [],
  "features_proibidas_no_dataset": [],
  "features_ausentes_na_base": [
    "DIAS_SINTOMAS_ATE_INTERNACAO",
    "SEXO_CATEGORIA"
  ],
  "base_origem_linhas": 4666910,
  "aliases_aplicados_yaml_para_fisico": {},
  "descartadas_data_tempo_invalida": 0,
  "derivadas_criadas": [
    "idade_anos",
    "faixa_etaria"
  ],
  "grupos_avaliacao_incluidos": [
    "sg_uf",
    "faixa_etaria"
  ],
  "sha256": "7348b0e2f7403116d544fc27117dfe5f838fbd707f112c6b35df50ea3d2b94e4",
  "split": {
    "tipo": "aleatorio",
    "seed": 42,
    "fracoes": {
      "treino": 0.7,
      "validacao": 0.15,
      "holdout": 0.15
    },
    "contagem": {
      "treino": 2617730,
      "holdout": 560943,
      "validacao": 560942
    }
  }
}
```

### `data/analytical/manifesto_supervisionado.json`

- Git: `ignored` · `2.3 KB` · modified `2026-10-17 00:43 UTC`

```json
{
  "schema_version": 2,
  "generated_utc": "2026-10-17T00:43:25.222942+00:00",
  "cohort_kind": "provisional",
  "source": {
    "kind": "provisional",
    "path": "<REPO>\\data\\analytical\\coorte_provisoria_b.parquet",
    "sha256": "da94652dbabd832f512f8346f19ef3fb12adc3e418c27c9229d693b4fe43c7f9",
    "size_bytes": 209678288,
    "rows": 3915136,
    "columns": 125
  },
  "dataset_path": "<REPO>\\data\\analytical\\dataset_supervisionado.parquet",
  "dataset_sha256": "408e5d40ef3dc82a57af5b5c9706a224641c7f0808819d333f48d4638d4e022b",
  "rows": 3915132,
  "columns": 43,
  "feature_columns": [
    "idade_anos",
    "dias_sintomas_ate_internacao",
    "sexo_categoria",
    "cs_gestant",
    "cs_raca",
    "cs_zona",
    "ave_suino",
    "febre",
    "tosse",
    "garganta",
    "dispneia",
    "diarreia",
    "vomito",
    "dor_abd",
    "fadiga",
    "perd_olft",
    "perd_pala",
    "outro_sin",
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
    "out_morbi"
  ],
  "numeric_columns": [
    "idade_anos",
    "dias_sintomas_ate_internacao"
  ],
  "categorical_columns": [
    "sexo_categoria",
    "cs_gestant",
    "cs_raca",
    "cs_zona",
    "ave_suino",
    "febre",
    "tosse",
    "garganta",
    "dispneia",
    "diarreia",
    "vomito",
    "dor_abd",
    "fadiga",
    "perd_olft",
    "perd_pala",
    "outro_sin",
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
    "out_morbi"
  ],
  "audit_columns": [
    "nu_notific",
    "grupo_split",
    "ano_internacao",
    "sg_uf",
    "faixa_etaria",
    "cs_escol_n",
    "vacina",
    "vacina_cov",
    "saturacao",
    "desc_resp"
  ],
  "target_column": "alvo_obito_srag",
  "partition_column": "particao",
  "partition_counts": {
    "treino": 2740584,
    "teste": 587276,
    "validacao": 587272
  },
  "seed": 42,
  "test_opened": false
}
```

### `outputs/C2/split_info.json`

- Git: `ignored` · `280 B` · modified `2026-10-17 00:58 UTC`

```json
{
  "origem": "artefato_supervisionado",
  "cohort_kind": "provisional",
  "partition_column": "particao",
  "n_total": 3915132,
  "n_treino_split": 2740584,
  "n_val_split": 587272,
  "n_teste_split": 587276,
  "n_treino_rotulado": 2740584,
  "n_val_rotulado": 587272
}
```

### `outputs/runs/2026-10-16_214409_272745_03_supervisionado_pilotos/metadata.json`

- Git: `ignored` · `2.7 KB` · modified `2026-10-17 00:44 UTC`

```json
{
  "run_id": "2026-10-16_214409_272745_03_supervisionado_pilotos",
  "timestamp": {
    "utc": "2026-10-17T00:44:09Z",
    "local": "2026-10-16T21:44:09-0300"
  },
  "modelo": "03_supervisionado_pilotos",
  "seed": 42,
  "status": "success",
  "erro": null,
  "duracao_s": 9.900000804918818e-06,
  "parametros": {
    "status_coorte": "provisoria",
    "versao_execucao": "piloto_v1",
    "split": "aleatorio_estratificado_por_alvo_ano_com_grupo",
    "teste_aberto": false
  },
  "dataset": {
    "n_rows": 3915132,
    "train_rows": 2740584,
    "valid_rows": 587272,
    "test_rows": 587276
  },
  "dataset_sha256": null,
  "data_version": "dados-v2",
  "features": {
    "n_features": 31,
    "usadas": [
      "idade_anos",
      "dias_sintomas_ate_internacao",
      "sexo_categoria",
      "cs_gestant",
      "cs_raca",
      "cs_zona",
      "ave_suino",
      "febre",
      "tosse",
      "garganta",
      "dispneia",
      "diarreia",
      "vomito",
      "dor_abd",
      "fadiga",
      "perd_olft",
      "perd_pala",
      "outro_sin",
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
      "out_morbi"
    ],
    "features_final_congelada": false
  },
  "metricas": {
    "dummy_pr_auc": 0.21868742252312387,
    "logistica_pr_auc": 0.4405563015380145,
    "logistica_roc_auc": 0.7751607183667255,
    "logistica_brier": 0.1980742897570493
  },
  "gates": {
    "G1_definicao_alvo_features": "pendente",
    "G2_janela_temporal": "aprovado",
    "G4_baseline": "aprovado",
    "G5_pilotos": "aprovado",
    "G6_finalistas_tuning": "pendente",
    "G7_calibracao": "pendente",
    "G8_limiar": "pendente",
    "G9_holdout": "pendente"
  },
  "notas": "Piloto provisorio. Holdout nao consultado. Sem tuning, calibracao ou selecao de limiar.",
  "versoes": {
    "python": "3.14.7",
    "numpy": "2.5.3",
    "pandas": "3.0.6",
    "pyarrow": "25.0.1",
    "scikit-learn": "1.9.1",
    "scipy": "1.18.1",
    "matplotlib": "3.11.2",
    "seaborn": "0.13.2"
  },
  "git": {
    "commit": "17693b360302d14eccc6fb6719ec606ba002d501",
    "branch": "main",
    "dirty": true
  },
  "env": {
    "python_executable": "<HOME>\\OneDrive - Pfizer\\Documents\\GitHub\\Projeto_Integrador\\.venv\\Scripts\\python.exe",
    "python_version": "3.14.7",
    "platform": "Windows-11-10.0.22631-SP0",
    "cwd": "<HOME>\\OneDrive - Pfizer\\Documents\\GitHub\\Projeto_Integrador\\notebooks\\B",
    "ci": false
  },
  "supervised_yaml_sha256": "6a86868c0d348086a4334960c2461a9ba66b8200020aeeabaec4bfadddbaa7c6"
}
```

### `outputs/runs/2026-10-16_214409_272745_03_supervisionado_pilotos/summary.txt`

- Git: `ignored` · `1.1 KB` · modified `2026-10-17 00:44 UTC`

```text
RUN_ID:   2026-10-16_214409_272745_03_supervisionado_pilotos
MODELO:   03_supervisionado_pilotos
SEED:     42
STATUS:   success
DADOS:    dados-v2
N_ROWS     3,915,132
TRAIN_ROWS 2,740,584
VALID_ROWS 587,272
TEST_ROWS  587,276
DURACAO:  0.0s

MÉTRICAS:
  dummy_pr_auc         0.2187
  logistica_pr_auc     0.4406
  logistica_roc_auc    0.7752
  logistica_brier      0.1981

PARÂMETROS:
  status_coorte        provisoria
  versao_execucao      piloto_v1
  split                aleatorio_estratificado_por_alvo_ano_com_grupo
  teste_aberto         False

GATES:
  G1_definicao_alvo_features         pendente
  G2_janela_temporal                 aprovado
  G4_baseline                        aprovado
  G5_pilotos                         aprovado
  G6_finalistas_tuning               pendente
  G7_calibracao                      pendente
  G8_limiar                          pendente
  G9_holdout                         pendente

NOTAS: Piloto provisorio. Holdout nao consultado. Sem tuning, calibracao ou selecao de limiar.

TIMESTAMP_UTC: 2026-10-17T00:44:09Z
```

### `outputs/runs/2026-10-16_215802_867822_C2_pipeline/metadata.json`

- Git: `ignored` · `2.5 KB` · modified `2026-10-17 00:58 UTC`

```json
{
  "run_id": "2026-10-16_215802_867822_C2_pipeline",
  "timestamp": {
    "utc": "2026-10-17T00:58:02Z",
    "local": "2026-10-16T21:58:02-0300"
  },
  "modelo": "C2_pipeline",
  "seed": 42,
  "status": "success",
  "erro": null,
  "duracao_s": 3.389999983482994e-05,
  "parametros": {
    "target": "alvo_obito_srag",
    "partition_column": "particao",
    "origem_particao": "artefato_supervisionado",
    "cohort_kind": "provisional"
  },
  "dataset": {
    "n_rows": 3915132,
    "train_rows": 2740584,
    "valid_rows": 587272,
    "test_rows": 587276
  },
  "dataset_sha256": null,
  "data_version": "dados-v2",
  "features": {
    "n_features": 31,
    "numericas": [
      "idade_anos",
      "dias_sintomas_ate_internacao"
    ],
    "categoricas": [
      "sexo_categoria",
      "cs_gestant",
      "cs_raca",
      "cs_zona",
      "ave_suino",
      "febre",
      "tosse",
      "garganta",
      "dispneia",
      "diarreia",
      "vomito",
      "dor_abd",
      "fadiga",
      "perd_olft",
      "perd_pala",
      "outro_sin",
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
      "out_morbi"
    ]
  },
  "metricas": {
    "n_features_processadas": 126
  },
  "gates": {
    "G1_definicao_alvo_features": "pendente",
    "G2_janela_temporal": "aprovado",
    "G4_baseline": "aprovado",
    "G5_pilotos": "aprovado",
    "G6_finalistas_tuning": "pendente",
    "G7_calibracao": "pendente",
    "G8_limiar": "pendente",
    "G9_holdout": "pendente"
  },
  "notas": "Arquitetura do pipeline supervisionado",
  "versoes": {
    "python": "3.14.7",
    "numpy": "2.5.3",
    "pandas": "3.0.6",
    "pyarrow": "25.0.1",
    "scikit-learn": "1.9.1",
    "scipy": "1.18.1",
    "matplotlib": "3.11.2",
    "seaborn": "0.13.2"
  },
  "git": {
    "commit": "17693b360302d14eccc6fb6719ec606ba002d501",
    "branch": "main",
    "dirty": true
  },
  "env": {
    "python_executable": "<HOME>\\OneDrive - Pfizer\\Documents\\GitHub\\Projeto_Integrador\\.venv\\Scripts\\python.exe",
    "python_version": "3.14.7",
    "platform": "Windows-11-10.0.22631-SP0",
    "cwd": "<HOME>\\OneDrive - Pfizer\\Documents\\GitHub\\Projeto_Integrador\\notebooks\\C",
    "ci": false
  },
  "supervised_yaml_sha256": "6a86868c0d348086a4334960c2461a9ba66b8200020aeeabaec4bfadddbaa7c6"
}
```

### `outputs/runs/2026-10-16_215802_867822_C2_pipeline/summary.txt`

- Git: `ignored` · `915 B` · modified `2026-10-17 00:58 UTC`

```text
RUN_ID:   2026-10-16_215802_867822_C2_pipeline
MODELO:   C2_pipeline
SEED:     42
STATUS:   success
DADOS:    dados-v2
N_ROWS     3,915,132
TRAIN_ROWS 2,740,584
VALID_ROWS 587,272
TEST_ROWS  587,276
DURACAO:  0.0s

MÉTRICAS:
  n_features_processadas 126

PARÂMETROS:
  target               alvo_obito_srag
  partition_column     particao
  origem_particao      artefato_supervisionado
  cohort_kind          provisional

GATES:
  G1_definicao_alvo_features         pendente
  G2_janela_temporal                 aprovado
  G4_baseline                        aprovado
  G5_pilotos                         aprovado
  G6_finalistas_tuning               pendente
  G7_calibracao                      pendente
  G8_limiar                          pendente
  G9_holdout                         pendente

NOTAS: Arquitetura do pipeline supervisionado

TIMESTAMP_UTC: 2026-10-17T00:58:02Z
```

### `outputs/runs/2026-10-16_220044_988905_C3_baseline_logistica/metadata.json`

- Git: `ignored` · `2.8 KB` · modified `2026-10-17 01:00 UTC`

```json
{
  "run_id": "2026-10-16_220044_988905_C3_baseline_logistica",
  "timestamp": {
    "utc": "2026-10-17T01:00:44Z",
    "local": "2026-10-16T22:00:44-0300"
  },
  "modelo": "C3_baseline_logistica",
  "seed": 42,
  "status": "success",
  "erro": null,
  "duracao_s": 6.099999154685065e-06,
  "parametros": {
    "cohort_kind": "provisional",
    "logistic_C": 1.0,
    "logistic_solver": "lbfgs",
    "limiar_diagnostico": 0.5,
    "tuning_realizado": false,
    "calibracao_aplicada": false,
    "teste_aberto": false
  },
  "dataset": {
    "n_treino": 2740584,
    "n_validacao": 587272,
    "n_teste_fechado": 587276
  },
  "dataset_sha256": "408e5d40ef3dc82a57af5b5c9706a224641c7f0808819d333f48d4638d4e022b",
  "data_version": "dados-v2",
  "features": {
    "n_features": 31,
    "usadas": [
      "idade_anos",
      "dias_sintomas_ate_internacao",
      "sexo_categoria",
      "cs_gestant",
      "cs_raca",
      "cs_zona",
      "ave_suino",
      "febre",
      "tosse",
      "garganta",
      "dispneia",
      "diarreia",
      "vomito",
      "dor_abd",
      "fadiga",
      "perd_olft",
      "perd_pala",
      "outro_sin",
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
      "out_morbi"
    ]
  },
  "metricas": {
    "dummy_ap": 0.21868742252312387,
    "dummy_auc": 0.5,
    "logistica_ap": 0.44061592989801807,
    "logistica_auc": 0.7752355926034296,
    "logistica_brier": 0.19806308229531083
  },
  "gates": {
    "G1_definicao_alvo_features": "pendente",
    "G2_janela_temporal": "aprovado",
    "G4_baseline": "aprovado",
    "G5_pilotos": "aprovado",
    "G6_finalistas_tuning": "pendente",
    "G7_calibracao": "pendente",
    "G8_limiar": "pendente",
    "G9_holdout": "pendente"
  },
  "notas": "C3 — baseline e logística na partição persistida. Teste não consultado.",
  "versoes": {
    "python": "3.14.7",
    "numpy": "2.5.3",
    "pandas": "3.0.6",
    "pyarrow": "25.0.1",
    "scikit-learn": "1.9.1",
    "scipy": "1.18.1",
    "matplotlib": "3.11.2",
    "seaborn": "0.13.2"
  },
  "git": {
    "commit": "17693b360302d14eccc6fb6719ec606ba002d501",
    "branch": "main",
    "dirty": true
  },
  "env": {
    "python_executable": "<HOME>\\OneDrive - Pfizer\\Documents\\GitHub\\Projeto_Integrador\\.venv\\Scripts\\python.exe",
    "python_version": "3.14.7",
    "platform": "Windows-11-10.0.22631-SP0",
    "cwd": "<HOME>\\OneDrive - Pfizer\\Documents\\GitHub\\Projeto_Integrador\\notebooks\\C",
    "ci": false
  },
  "supervised_yaml_sha256": "6a86868c0d348086a4334960c2461a9ba66b8200020aeeabaec4bfadddbaa7c6"
}
```

### `outputs/runs/2026-10-16_220044_988905_C3_baseline_logistica/summary.txt`

- Git: `ignored` · `1.1 KB` · modified `2026-10-17 01:00 UTC`

```text
RUN_ID:   2026-10-16_220044_988905_C3_baseline_logistica
MODELO:   C3_baseline_logistica
SEED:     42
STATUS:   success
DADOS:    dados-v2
SHA-256:  408e5d40ef3dc82a57af5b5c9706a224641c7f0808819d333f48d4638d4e022b
DURACAO:  0.0s

MÉTRICAS:
  dummy_ap             0.2187
  dummy_auc            0.5000
  logistica_ap         0.4406
  logistica_auc        0.7752
  logistica_brier      0.1981

PARÂMETROS:
  cohort_kind          provisional
  logistic_C           1.0000
  logistic_solver      lbfgs
  limiar_diagnostico   0.5000
  tuning_realizado     False
  calibracao_aplicada  False
  teste_aberto         False

GATES:
  G1_definicao_alvo_features         pendente
  G2_janela_temporal                 aprovado
  G4_baseline                        aprovado
  G5_pilotos                         aprovado
  G6_finalistas_tuning               pendente
  G7_calibracao                      pendente
  G8_limiar                          pendente
  G9_holdout                         pendente

NOTAS: C3 — baseline e logística na partição persistida. Teste não consultado.

TIMESTAMP_UTC: 2026-10-17T01:00:44Z
```

### `outputs/runs/2026-10-16_220744_784223_C4_boosting/metadata.json`

- Git: `ignored` · `2.9 KB` · modified `2026-10-17 01:07 UTC`

```json
{
  "run_id": "2026-10-16_220744_784223_C4_boosting",
  "timestamp": {
    "utc": "2026-10-17T01:07:44Z",
    "local": "2026-10-16T22:07:44-0300"
  },
  "modelo": "C4_boosting",
  "seed": 42,
  "status": "success",
  "erro": null,
  "duracao_s": 6.50000038149301e-06,
  "parametros": {
    "cohort_kind": "provisional",
    "g6_status": "pendente",
    "buscas_executadas": false,
    "metrica_principal": "pr_auc",
    "max_configs": 30,
    "limiar_diagnostico": 0.5,
    "calibracao_aplicada": false,
    "teste_aberto": false
  },
  "dataset": {
    "n_treino": 2740584,
    "n_validacao": 587272,
    "n_teste_fechado": 587276
  },
  "dataset_sha256": "408e5d40ef3dc82a57af5b5c9706a224641c7f0808819d333f48d4638d4e022b",
  "data_version": "dados-v2",
  "features": {
    "n_features": 31,
    "usadas": [
      "idade_anos",
      "dias_sintomas_ate_internacao",
      "sexo_categoria",
      "cs_gestant",
      "cs_raca",
      "cs_zona",
      "ave_suino",
      "febre",
      "tosse",
      "garganta",
      "dispneia",
      "diarreia",
      "vomito",
      "dor_abd",
      "fadiga",
      "perd_olft",
      "perd_pala",
      "outro_sin",
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
      "out_morbi"
    ]
  },
  "metricas": {
    "logistica_ap": 0.44061592989801807,
    "logistica_auc": 0.7752355926034296,
    "boosting_ap": 0.46752119135143005,
    "boosting_auc": 0.7874327329924564,
    "boosting_brier": 0.1959726068522269,
    "delta_ap": 0.02690526145341199
  },
  "gates": {
    "G1_definicao_alvo_features": "pendente",
    "G2_janela_temporal": "aprovado",
    "G4_baseline": "aprovado",
    "G5_pilotos": "aprovado",
    "G6_finalistas_tuning": "pendente",
    "G7_calibracao": "pendente",
    "G8_limiar": "pendente",
    "G9_holdout": "pendente"
  },
  "notas": "C4 — boosting na partição do C3. Buscas condicionadas ao G6. Teste não consultado.",
  "versoes": {
    "python": "3.14.7",
    "numpy": "2.5.3",
    "pandas": "3.0.6",
    "pyarrow": "25.0.1",
    "scikit-learn": "1.9.1",
    "scipy": "1.18.1",
    "matplotlib": "3.11.2",
    "seaborn": "0.13.2"
  },
  "git": {
    "commit": "17693b360302d14eccc6fb6719ec606ba002d501",
    "branch": "main",
    "dirty": true
  },
  "env": {
    "python_executable": "<HOME>\\OneDrive - Pfizer\\Documents\\GitHub\\Projeto_Integrador\\.venv\\Scripts\\python.exe",
    "python_version": "3.14.7",
    "platform": "Windows-11-10.0.22631-SP0",
    "cwd": "<HOME>\\OneDrive - Pfizer\\Documents\\GitHub\\Projeto_Integrador\\notebooks\\C",
    "ci": false
  },
  "supervised_yaml_sha256": "6a86868c0d348086a4334960c2461a9ba66b8200020aeeabaec4bfadddbaa7c6"
}
```

### `outputs/runs/2026-10-16_220744_784223_C4_boosting/summary.txt`

- Git: `ignored` · `1.2 KB` · modified `2026-10-17 01:07 UTC`

```text
RUN_ID:   2026-10-16_220744_784223_C4_boosting
MODELO:   C4_boosting
SEED:     42
STATUS:   success
DADOS:    dados-v2
SHA-256:  408e5d40ef3dc82a57af5b5c9706a224641c7f0808819d333f48d4638d4e022b
DURACAO:  0.0s

MÉTRICAS:
  logistica_ap         0.4406
  logistica_auc        0.7752
  boosting_ap          0.4675
  boosting_auc         0.7874
  boosting_brier       0.1960
  delta_ap             0.0269

PARÂMETROS:
  cohort_kind          provisional
  g6_status            pendente
  buscas_executadas    False
  metrica_principal    pr_auc
  max_configs          30
  limiar_diagnostico   0.5000
  calibracao_aplicada  False
  teste_aberto         False

GATES:
  G1_definicao_alvo_features         pendente
  G2_janela_temporal                 aprovado
  G4_baseline                        aprovado
  G5_pilotos                         aprovado
  G6_finalistas_tuning               pendente
  G7_calibracao                      pendente
  G8_limiar                          pendente
  G9_holdout                         pendente

NOTAS: C4 — boosting na partição do C3. Buscas condicionadas ao G6. Teste não consultado.

TIMESTAMP_UTC: 2026-10-17T01:07:44Z
```

### `outputs/runs/2026-10-16_231055_901408_C5_calibracao_limiar/metadata.json`

- Git: `ignored` · `3.2 KB` · modified `2026-10-17 02:10 UTC`

```json
{
  "run_id": "2026-10-16_231055_901408_C5_calibracao_limiar",
  "timestamp": {
    "utc": "2026-10-17T02:10:55Z",
    "local": "2026-10-16T23:10:55-0300"
  },
  "modelo": "C5_calibracao_limiar",
  "seed": 42,
  "status": "success",
  "erro": null,
  "duracao_s": 1.2999997125007212e-05,
  "parametros": {
    "cohort_kind": "provisional",
    "finalistas": [
      "hist_gradient_boosting",
      "logistic"
    ],
    "calibracao_ativa": true,
    "metodos_candidatos": [
      "sigmoid",
      "isotonic"
    ],
    "honest_calib_split": true,
    "limiar_metrica": "f1",
    "min_precision": null,
    "teste_aberto": false,
    "yaml_atualizado": false
  },
  "dataset": {
    "n_treino": 2740584,
    "n_val_cal": 293636,
    "n_val_meas": 293636,
    "n_teste_fechado": 587276
  },
  "dataset_sha256": "408e5d40ef3dc82a57af5b5c9706a224641c7f0808819d333f48d4638d4e022b",
  "data_version": "dados-v2",
  "features": {
    "n_features": 31,
    "usadas": [
      "idade_anos",
      "dias_sintomas_ate_internacao",
      "sexo_categoria",
      "cs_gestant",
      "cs_raca",
      "cs_zona",
      "ave_suino",
      "febre",
      "tosse",
      "garganta",
      "dispneia",
      "diarreia",
      "vomito",
      "dor_abd",
      "fadiga",
      "perd_olft",
      "perd_pala",
      "outro_sin",
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
      "out_morbi"
    ]
  },
  "metricas": {
    "hist_gradient_boosting_brier_base": 0.19588851055358997,
    "hist_gradient_boosting_brier_calibrado": 0.14094344151171814,
    "hist_gradient_boosting_limiar": 0.255,
    "hist_gradient_boosting_auc": 0.7874607762382129,
    "logistic_brier_base": 0.1981048319609869,
    "logistic_brier_calibrado": 0.1438547651248468,
    "logistic_limiar": 0.255,
    "logistic_auc": 0.7750213489731965
  },
  "gates": {
    "G1_definicao_alvo_features": "pendente",
    "G2_janela_temporal": "aprovado",
    "G4_baseline": "aprovado",
    "G5_pilotos": "aprovado",
    "G6_finalistas_tuning": "pendente",
    "G7_calibracao": "pendente",
    "G8_limiar": "pendente",
    "G9_holdout": "pendente"
  },
  "notas": "C5 — calibração e limiar escolhidos na validação. Teste não consultado.",
  "versoes": {
    "python": "3.14.7",
    "numpy": "2.5.3",
    "pandas": "3.0.6",
    "pyarrow": "25.0.1",
    "scikit-learn": "1.9.1",
    "scipy": "1.18.1",
    "matplotlib": "3.11.2",
    "seaborn": "0.13.2"
  },
  "git": {
    "commit": "17693b360302d14eccc6fb6719ec606ba002d501",
    "branch": "main",
    "dirty": true
  },
  "env": {
    "python_executable": "<HOME>\\OneDrive - Pfizer\\Documents\\GitHub\\Projeto_Integrador\\.venv\\Scripts\\python.exe",
    "python_version": "3.14.7",
    "platform": "Windows-11-10.0.22631-SP0",
    "cwd": "<HOME>\\OneDrive - Pfizer\\Documents\\GitHub\\Projeto_Integrador\\notebooks\\C",
    "ci": false
  },
  "supervised_yaml_sha256": "6a86868c0d348086a4334960c2461a9ba66b8200020aeeabaec4bfadddbaa7c6"
}
```

### `outputs/runs/2026-10-16_231055_901408_C5_calibracao_limiar/summary.txt`

- Git: `ignored` · `1.4 KB` · modified `2026-10-17 02:10 UTC`

```text
RUN_ID:   2026-10-16_231055_901408_C5_calibracao_limiar
MODELO:   C5_calibracao_limiar
SEED:     42
STATUS:   success
DADOS:    dados-v2
SHA-256:  408e5d40ef3dc82a57af5b5c9706a224641c7f0808819d333f48d4638d4e022b
DURACAO:  0.0s

MÉTRICAS:
  hist_gradient_boosting_brier_base 0.1959
  hist_gradient_boosting_brier_calibrado 0.1409
  hist_gradient_boosting_limiar 0.2550
  hist_gradient_boosting_auc 0.7875
  logistic_brier_base  0.1981
  logistic_brier_calibrado 0.1439
  logistic_limiar      0.2550
  logistic_auc         0.7750

PARÂMETROS:
  cohort_kind          provisional
  finalistas           ['hist_gradient_boosting', 'logistic']
  calibracao_ativa     True
  metodos_candidatos   ['sigmoid', 'isotonic']
  honest_calib_split   True
  limiar_metrica       f1
  min_precision        None
  teste_aberto         False
  yaml_atualizado      False

GATES:
  G1_definicao_alvo_features         pendente
  G2_janela_temporal                 aprovado
  G4_baseline                        aprovado
  G5_pilotos                         aprovado
  G6_finalistas_tuning               pendente
  G7_calibracao                      pendente
  G8_limiar                          pendente
  G9_holdout                         pendente

NOTAS: C5 — calibração e limiar escolhidos na validação. Teste não consultado.

TIMESTAMP_UTC: 2026-10-17T02:10:55Z
```

### `outputs/tables/03_cinco_familias_provisoria_20261017T004540Z_amostras.csv`

- Git: `ignored` · `212 B` · modified `2026-10-17 00:45 UTC` · 2 rows

```csv
particao,linhas_originais,linhas_piloto,prevalencia_original,prevalencia_piloto
treino,2740584,300000,0.21868441178960396,0.21868333333333334
validacao,587272,120000,0.21868742252312387,0.21868333333333334
```

### `outputs/tables/03_cinco_familias_provisoria_20261017T004540Z_manifesto.json`

- Git: `ignored` · `2.7 KB` · modified `2026-10-17 00:45 UTC`

```json
{
  "status_coorte": "provisoria",
  "versao_execucao": "piloto_v2_cinco_familias",
  "carater": "comparacao_provisoria_de_integracao",
  "seed": 42,
  "n_treino_piloto": 300000,
  "n_validacao_piloto": 120000,
  "features": [
    "idade_anos",
    "dias_sintomas_ate_internacao",
    "sexo_categoria",
    "cs_gestant",
    "cs_raca",
    "cs_zona",
    "ave_suino",
    "febre",
    "tosse",
    "garganta",
    "dispneia",
    "diarreia",
    "vomito",
    "dor_abd",
    "fadiga",
    "perd_olft",
    "perd_pala",
    "outro_sin",
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
    "out_morbi"
  ],
  "modelos": [
    "dummy_prior_v2",
    "logistica_C1_v2",
    "arvore_rasa_v2",
    "random_forest_contida_v2",
    "hist_gradient_boosting_v2"
  ],
  "shortlist_provisoria": [
    "hist_gradient_boosting_v2",
    "logistica_C1_v2"
  ],
  "teste_aberto": false,
  "limiar_selecionado": false,
  "calibracao_aplicada": false,
  "tuning_realizado": false,
  "observacoes": [
    "Resultados dependem da coorte provisória.",
    "Amostras comparáveis foram usadas para controlar custo.",
    "A shortlist não congela finalistas.",
    "O teste permaneceu fechado.",
    "Calibração e limiar pertencem à próxima etapa."
  ],
  "artefatos": {
    "metricas": "<REPO>\\outputs\\tables\\03_cinco_familias_provisoria_20261017T004540Z_metricas.csv",
    "metricas_por_ano": "<REPO>\\outputs\\tables\\03_cinco_familias_provisoria_20261017T004540Z_metricas_por_ano.csv",
    "variacao_temporal": "<REPO>\\outputs\\tables\\03_cinco_familias_provisoria_20261017T004540Z_variacao_temporal.csv",
    "amostras": "<REPO>\\outputs\\tables\\03_cinco_familias_provisoria_20261017T004540Z_amostras.csv",
    "predicoes_validacao": "<REPO>\\outputs\\predictions\\03_cinco_familias_provisoria_20261017T004540Z_predicoes_validacao.parquet",
    "figura_curvas": "<REPO>\\reports\\figures\\supervisionado_03\\03_pilotos_curvas_pr_roc_calibracao.png",
    "figura_temporal": "<REPO>\\reports\\figures\\supervisionado_03\\03_pilotos_metricas_por_ano.png"
  }
}
```

### `outputs/tables/03_cinco_familias_provisoria_20261017T004540Z_metricas.csv`

- Git: `ignored` · `1.3 KB` · modified `2026-10-17 00:45 UTC` · 5 rows

```csv
roc_auc,pr_auc,brier,f1,precision,recall,accuracy,limiar_diagnostico,n_validacao,modelo,status_coorte,versao_execucao,n_treino,duracao_fit_s,duracao_pred_s
0.7833709454003838,0.4596864874551059,0.19632903073476674,0.5089796841341061,0.37006974611031307,0.8148388080176816,0.6561916666666666,0.5,120000,hist_gradient_boosting_v2,provisoria,piloto_v2_cinco_familias,300000,11.14434540000002,1.424537799999598
0.7733341014992019,0.4391946203259919,0.1981954562591791,0.5039143952353007,0.3747469682619273,0.7689581586769301,0.6689083333333333,0.5,120000,logistica_C1_v2,provisoria,piloto_v2_cinco_familias,300000,6.388927399999375,1.5536587000005966
0.7651780559732301,0.42991604084878565,0.20114864848557457,0.4926865930508181,0.3536510465946251,0.8118664735919519,0.634375,0.5,120000,random_forest_contida_v2,provisoria,piloto_v2_cinco_familias,300000,43.91674210000019,1.5719465000001946
0.756532095491909,0.39921961347201546,0.20657001421031662,0.4893024932682883,0.3473455220180111,0.827490282752839,0.6222583333333334,0.5,120000,arvore_rasa_v2,provisoria,piloto_v2_cinco_familias,300000,8.28684869999961,0.9775219000002835
0.5,0.21868333333333334,0.1708609330555555,0.0,0.0,0.0,0.7813166666666667,0.5,120000,dummy_prior_v2,provisoria,piloto_v2_cinco_familias,300000,3.7708654000016395,0.972776900000099
```

### `outputs/tables/03_cinco_familias_provisoria_20261017T004540Z_metricas_por_ano.csv`

- Git: `ignored` · `5.2 KB` · modified `2026-10-17 00:45 UTC` · 40 rows

```csv
modelo,ano_internacao,n,positivos,prevalencia,pr_auc,roc_auc,brier,probabilidade_media
arvore_rasa_v2,2019,1334,160,0.1199400299850075,0.31103495861403446,0.7979610306643952,0.12758840563851523,0.2524652640157311
arvore_rasa_v2,2020,30032,8402,0.2797682472029835,0.4515074952948283,0.7229043995094844,0.24028885773394879,0.5192341393917813
arvore_rasa_v2,2021,45369,12790,0.28191055566576295,0.43680795724582233,0.7073288419193751,0.23198605432882535,0.496558940079144
arvore_rasa_v2,2022,14589,2649,0.18157515936664612,0.34695670569584025,0.7638635956933275,0.21330302316912159,0.42760456259584456
arvore_rasa_v2,2023,7377,706,0.0957028602412905,0.27259243341254386,0.8255586418403109,0.14122061701371155,0.276987178933185
arvore_rasa_v2,2024,7034,586,0.08330963889678704,0.2367325111039219,0.8125265976591943,0.1363503264424084,0.26423552083668517
arvore_rasa_v2,2025,8886,651,0.07326130992572587,0.23094441280974853,0.8281001532367653,0.1318170838269198,0.25912931698669744
arvore_rasa_v2,2026,5379,298,0.055400632087748654,0.20227650155666232,0.8450349307658879,0.11020475887700545,0.21961792312835515
dummy_prior_v2,2019,1334,160,0.1199400299850075,0.1199400299850075,0.5,0.11530465914834248,0.21868333333333334
dummy_prior_v2,2020,30032,8402,0.2797682472029835,0.2797682472029835,0.5,0.20522934176241633,0.21868333333333337
dummy_prior_v2,2021,45369,12790,0.28191055566576295,0.28191055566576295,0.5,0.2064346759138582,0.2186833333333334
dummy_prior_v2,2022,14589,2649,0.18157515936664612,0.18157515936664612,0.5,0.14998263744276508,0.21868333333333334
dummy_prior_v2,2023,7377,706,0.0957028602412905,0.0957028602412905,0.5,0.10166801954486918,0.21868333333333334
dummy_prior_v2,2024,7034,586,0.08330963889678704,0.08330963889678704,0.5,0.09469518010907338,0.21868333333333334
dummy_prior_v2,2025,8886,651,0.07326130992572587,0.07326130992572587,0.5,0.08904165528565533,0.21868333333333334
dummy_prior_v2,2026,5379,298,0.055400632087748654,0.055400632087748654,0.5,0.07899264257808143,0.21868333333333334
hist_gradient_boosting_v2,2019,1334,160,0.1199400299850075,0.3465693516022601,0.8124547487223169,0.13110543670886737,0.2676039147206479
hist_gradient_boosting_v2,2020,30032,8402,0.2797682472029835,0.5164997626409047,0.7580653638705004,0.23151814174484173,0.5182468041996628
hist_gradient_boosting_v2,2021,45369,12790,0.28191055566576295,0.4879800499510862,0.7341272640191554,0.21919395126055652,0.4800796932090034
hist_gradient_boosting_v2,2022,14589,2649,0.18157515936664612,0.4206282927794213,0.7952690500444846,0.20082233313259307,0.4149230955055803
hist_gradient_boosting_v2,2023,7377,706,0.0957028602412905,0.32230062687583133,0.845449289406645,0.1332954113035727,0.2668442780746959
hist_gradient_boosting_v2,2024,7034,586,0.08330963889678704,0.27949801665658786,0.8336151009070198,0.12889735485599105,0.2545488992692805
hist_gradient_boosting_v2,2025,8886,651,0.07326130992572587,0.2618358631105581,0.8440987057415754,0.1240428892875915,0.24776638305867885
hist_gradient_boosting_v2,2026,5379,298,0.055400632087748654,0.21691908816802885,0.8560976608472939,0.10503800938030636,0.21063424460470664
logistica_C1_v2,2019,1334,160,0.1199400299850075,0.34252782043905955,0.8065960391822828,0.13126929489523306,0.2832903109703609
logistica_C1_v2,2020,30032,8402,0.2797682472029835,0.5002695045987536,0.7494558568326257,0.23079501402819952,0.5160348408274956
logistica_C1_v2,2021,45369,12790,0.28191055566576295,0.47676831757282606,0.725251437289345,0.2182677563384315,0.47489488020294707
logistica_C1_v2,2022,14589,2649,0.18157515936664612,0.3982419945105877,0.7856544898899936,0.20725567925101124,0.4302675831396566
logistica_C1_v2,2023,7377,706,0.0957028602412905,0.2946275487920166,0.8291804024268078,0.1410592491885203,0.2932824134819757
logistica_C1_v2,2024,7034,586,0.08330963889678704,0.25917395137361576,0.8256064266296294,0.13508743915985752,0.2802211824752972
logistica_C1_v2,2025,8886,651,0.07326130992572587,0.2462244144676162,0.8324111147485024,0.13024540290776948,0.272552470357743
logistica_C1_v2,2026,5379,298,0.055400632087748654,0.22327198776182794,0.8452558485422068,0.11204739355874034,0.2393976573825986
random_forest_contida_v2,2019,1334,160,0.1199400299850075,0.32572426198480253,0.8007905664395228,0.14916144376578358,0.3496393534401367
random_forest_contida_v2,2020,30032,8402,0.2797682472029835,0.4760313531234205,0.7293101047094549,0.2348786290505166,0.5181114482469674
random_forest_contida_v2,2021,45369,12790,0.28191055566576295,0.45705715051531104,0.7106745290169867,0.2253093920542841,0.49057310298612267
random_forest_contida_v2,2022,14589,2649,0.18157515936664612,0.3883585268711113,0.7770167529480799,0.1992066532945187,0.4348338092351371
random_forest_contida_v2,2023,7377,706,0.0957028602412905,0.3102233058174007,0.8332522953564603,0.14005422778055934,0.32473932034286557
random_forest_contida_v2,2024,7034,586,0.08330963889678704,0.26557302373811287,0.821075429373555,0.1358453544198026,0.31438593293411254
random_forest_contida_v2,2025,8886,651,0.07326130992572587,0.25951051724284785,0.8375352663736234,0.13068176776563886,0.3063814328044761
random_forest_contida_v2,2026,5379,298,0.055400632087748654,0.22759773633077704,0.8514527737894432,0.11279779548692852,0.2751319441993206
```

### `outputs/tables/03_cinco_familias_provisoria_20261017T004540Z_variacao_temporal.csv`

- Git: `ignored` · `911 B` · modified `2026-10-17 00:45 UTC` · 4 rows

```csv
modelo,pr_auc_min,pr_auc_max,pr_auc_media,roc_auc_min,roc_auc_max,brier_min,brier_max,amplitude_pr_auc,amplitude_roc_auc
arvore_rasa_v2,0.20227650155666232,0.4515074952948283,0.31110662196667527,0.7073288419193751,0.8450349307658879,0.11020475887700545,0.24028885773394879,0.24923099373816598,0.1377060888465128
hist_gradient_boosting_v2,0.21691908816802885,0.5164997626409047,0.3565288814730848,0.7341272640191554,0.8560976608472939,0.10503800938030636,0.23151814174484173,0.29958067447287584,0.12197039682813848
logistica_C1_v2,0.22327198776182794,0.5002695045987536,0.3426381924395379,0.725251437289345,0.8452558485422068,0.11204739355874034,0.23079501402819952,0.2769975168369257,0.12000441125286176
random_forest_contida_v2,0.22759773633077704,0.4760313531234205,0.338759484452973,0.7106745290169867,0.8514527737894432,0.11279779548692852,0.2348786290505166,0.24843361679264345,0.14077824477245648
```

### `outputs/tables/03_pilotos_provisoria_20261017T004408Z_contrato.csv`

- Git: `ignored` · `213 B` · modified `2026-10-17 00:44 UTC` · 8 rows

```csv
item,resultado
coorte_nao_vazia,True
dt_interna_disponivel,True
dt_interna_sem_nulos,True
ano_disponivel,True
alvo_disponivel,True
alvo_binario,True
features_sem_proibidas,True
features_presentes,True
```

### `outputs/tables/03_pilotos_provisoria_20261017T004408Z_manifesto.json`

- Git: `ignored` · `2.0 KB` · modified `2026-10-17 00:44 UTC`

```json
{
  "status_coorte": "provisoria",
  "versao_execucao": "piloto_v1",
  "fonte": "<REPO>\\data\\analytical\\coorte_provisoria_b.parquet",
  "seed": 42,
  "features": [
    "idade_anos",
    "dias_sintomas_ate_internacao",
    "sexo_categoria",
    "cs_gestant",
    "cs_raca",
    "cs_zona",
    "ave_suino",
    "febre",
    "tosse",
    "garganta",
    "dispneia",
    "diarreia",
    "vomito",
    "dor_abd",
    "fadiga",
    "perd_olft",
    "perd_pala",
    "outro_sin",
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
    "out_morbi"
  ],
  "features_final_congelada": false,
  "n_base_modelagem": 3915132,
  "n_treino": 2740584,
  "n_validacao": 587272,
  "n_teste_criado_mas_nao_aberto": 587276,
  "teste_aberto": false,
  "quarentena_conflitos_split": {
    "politica": "quarentena_provisoria",
    "grupos_conflitantes": 2,
    "linhas_excluidas": 4,
    "waterfall": "<REPO>\\outputs\\tables\\supervisionado_waterfall_conflitos_split_provisorio.csv"
  },
  "artefatos": {
    "contrato": "<REPO>\\outputs\\tables\\03_pilotos_provisoria_20261017T004408Z_contrato.csv",
    "particoes": "<REPO>\\outputs\\tables\\03_pilotos_provisoria_20261017T004408Z_particoes.csv",
    "metricas_validacao": "<REPO>\\outputs\\tables\\03_pilotos_provisoria_20261017T004408Z_metricas_validacao.csv",
    "predicoes_validacao": "<REPO>\\outputs\\predictions\\03_pilotos_provisoria_20261017T004408Z_predicoes_validacao.parquet"
  }
}
```

### `outputs/tables/03_pilotos_provisoria_20261017T004408Z_metricas_validacao.csv`

- Git: `ignored` · `574 B` · modified `2026-10-17 00:44 UTC` · 2 rows

```csv
roc_auc,pr_auc,brier,f1,precision,recall,accuracy,limiar_apenas_diagnostico,n_validacao,modelo,status_coorte,versao_execucao,n_treino_usado,duracao_fit_s,duracao_pred_s
0.7751607183667255,0.4405563015380145,0.1980742897570493,0.5056971968518372,0.37570939963981415,0.7732132150838207,0.6694359683417564,0.5,587272,logistica_piloto_C1,provisoria,piloto_v1,1000000,18.607920899999954,4.496747799999866
0.5,0.21868742252312387,0.17086323376238108,0.0,0.0,0.0,0.7813125774768761,0.5,587272,dummy_prior,provisoria,piloto_v1,2740584,0.27957860000060464,0.011728299999958836
```

### `outputs/tables/03_pilotos_provisoria_20261017T004408Z_particoes.csv`

- Git: `ignored` · `313 B` · modified `2026-10-17 00:44 UTC` · 3 rows

```csv
particao,n,positivos,prevalencia,ano_minimo,ano_maximo,grupos,percentual
treino,2740584,599323,0.21868441178960396,2019,2026,2740574,69.99978544784697
validacao,587272,128429,0.21868742252312387,2019,2026,587270,15.000056192230558
teste,587276,128431,0.2186893385733454,2019,2026,587275,15.000158359922475
```

### `outputs/tables/04_handoff_provisional_20261017T005359Z_calibracao_bruta.csv`

- Git: `ignored` · `236 B` · modified `2026-10-17 00:53 UTC` · 2 rows

```csv
modelo,n,prevalencia,probabilidade_media,diferenca_media
hist_gradient_boosting_v2,120000,0.21868333333333334,0.4237390097158091,0.20505567638247574
logistica_C1_v2,120000,0.21868333333333334,0.429519905144712,0.21083657181137866
```

### `outputs/tables/04_handoff_provisional_20261017T005359Z_manifesto.json`

- Git: `ignored` · `2.9 KB` · modified `2026-10-17 00:53 UTC`

```json
{
  "tipo_coorte": "provisional",
  "fonte_coorte": {
    "kind": "provisional",
    "path": "<REPO>\\data\\analytical\\coorte_provisoria_b.parquet",
    "sha256": "da94652dbabd832f512f8346f19ef3fb12adc3e418c27c9229d693b4fe43c7f9",
    "size_bytes": 209678288,
    "rows": 3915136,
    "columns": 125
  },
  "dataset_supervisionado": {
    "path": "<REPO>\\data\\analytical\\dataset_supervisionado.parquet",
    "sha256": "408e5d40ef3dc82a57af5b5c9706a224641c7f0808819d333f48d4638d4e022b",
    "rows": 3915132,
    "columns": 43,
    "partition_column": "particao",
    "partition_counts": {
      "treino": 2740584,
      "teste": 587276,
      "validacao": 587272
    },
    "seed": 42,
    "test_opened": false
  },
  "status_execucao": "provisoria",
  "shortlist_yaml": [
    "hist_gradient_boosting",
    "logistic"
  ],
  "shortlist_execucao": [
    "hist_gradient_boosting_v2",
    "logistica_C1_v2"
  ],
  "teste_consultado": false,
  "tuning_realizado": false,
  "calibracao_escolhida": false,
  "limiar_escolhido": false,
  "gate_g1": "pendente",
  "gate_g6": "pendente",
  "features_final_congelada": false,
  "artefatos_origem_notebook03": {
    "metricas": "<REPO>\\outputs\\tables\\03_cinco_familias_provisoria_20261017T004540Z_metricas.csv",
    "metricas_por_ano": "<REPO>\\outputs\\tables\\03_cinco_familias_provisoria_20261017T004540Z_metricas_por_ano.csv",
    "variacao_temporal": "<REPO>\\outputs\\tables\\03_cinco_familias_provisoria_20261017T004540Z_variacao_temporal.csv",
    "manifesto": "<REPO>\\outputs\\tables\\03_cinco_familias_provisoria_20261017T004540Z_manifesto.json",
    "predicoes_validacao": "<REPO>\\outputs\\predictions\\03_cinco_familias_provisoria_20261017T004540Z_predicoes_validacao.parquet"
  },
  "artefatos_handoff": {
    "shortlist": "<REPO>\\outputs\\tables\\04_handoff_provisional_20261017T005359Z_shortlist.csv",
    "temporal": "<REPO>\\outputs\\tables\\04_handoff_provisional_20261017T005359Z_temporal.csv",
    "calibracao_bruta": "<REPO>\\outputs\\tables\\04_handoff_provisional_20261017T005359Z_calibracao_bruta.csv",
    "transicao": "<REPO>\\outputs\\tables\\04_handoff_provisional_20261017T005359Z_transicao.csv"
  }
}
```

### `outputs/tables/04_handoff_provisional_20261017T005359Z_shortlist.csv`

- Git: `ignored` · `650 B` · modified `2026-10-17 00:53 UTC` · 2 rows

```csv
roc_auc,pr_auc,brier,f1,precision,recall,accuracy,limiar_diagnostico,n_validacao,modelo,status_coorte,versao_execucao,n_treino,duracao_fit_s,duracao_pred_s
0.7833709454003838,0.4596864874551059,0.1963290307347667,0.5089796841341061,0.370069746110313,0.8148388080176816,0.6561916666666666,0.5,120000,hist_gradient_boosting_v2,provisoria,piloto_v2_cinco_familias,300000,11.14434540000002,1.424537799999598
0.7733341014992019,0.4391946203259919,0.1981954562591791,0.5039143952353007,0.3747469682619273,0.7689581586769301,0.6689083333333333,0.5,120000,logistica_C1_v2,provisoria,piloto_v2_cinco_familias,300000,6.388927399999375,1.5536587000005966
```

### `outputs/tables/04_handoff_provisional_20261017T005359Z_temporal.csv`

- Git: `ignored` · `2.1 KB` · modified `2026-10-17 00:53 UTC` · 16 rows

```csv
modelo,ano_internacao,n,positivos,prevalencia,pr_auc,roc_auc,brier,probabilidade_media
hist_gradient_boosting_v2,2019,1334,160,0.1199400299850075,0.3465693516022601,0.8124547487223169,0.1311054367088673,0.2676039147206479
hist_gradient_boosting_v2,2020,30032,8402,0.2797682472029835,0.5164997626409047,0.7580653638705004,0.2315181417448417,0.5182468041996628
hist_gradient_boosting_v2,2021,45369,12790,0.2819105556657629,0.4879800499510862,0.7341272640191554,0.2191939512605565,0.4800796932090034
hist_gradient_boosting_v2,2022,14589,2649,0.1815751593666461,0.4206282927794213,0.7952690500444846,0.200822333132593,0.4149230955055803
hist_gradient_boosting_v2,2023,7377,706,0.0957028602412905,0.3223006268758313,0.845449289406645,0.1332954113035727,0.2668442780746959
hist_gradient_boosting_v2,2024,7034,586,0.083309638896787,0.2794980166565878,0.8336151009070198,0.128897354855991,0.2545488992692805
hist_gradient_boosting_v2,2025,8886,651,0.0732613099257258,0.2618358631105581,0.8440987057415754,0.1240428892875915,0.2477663830586788
hist_gradient_boosting_v2,2026,5379,298,0.0554006320877486,0.2169190881680288,0.8560976608472939,0.1050380093803063,0.2106342446047066
logistica_C1_v2,2019,1334,160,0.1199400299850075,0.3425278204390595,0.8065960391822828,0.131269294895233,0.2832903109703609
logistica_C1_v2,2020,30032,8402,0.2797682472029835,0.5002695045987536,0.7494558568326257,0.2307950140281995,0.5160348408274956
logistica_C1_v2,2021,45369,12790,0.2819105556657629,0.476768317572826,0.725251437289345,0.2182677563384315,0.474894880202947
logistica_C1_v2,2022,14589,2649,0.1815751593666461,0.3982419945105877,0.7856544898899936,0.2072556792510112,0.4302675831396566
logistica_C1_v2,2023,7377,706,0.0957028602412905,0.2946275487920166,0.8291804024268078,0.1410592491885203,0.2932824134819757
logistica_C1_v2,2024,7034,586,0.083309638896787,0.2591739513736157,0.8256064266296294,0.1350874391598575,0.2802211824752972
logistica_C1_v2,2025,8886,651,0.0732613099257258,0.2462244144676162,0.8324111147485024,0.1302454029077694,0.272552470357743
logistica_C1_v2,2026,5379,298,0.0554006320877486,0.2232719877618279,0.8452558485422068,0.1120473935587403,0.2393976573825986
```

### `outputs/tables/04_handoff_provisional_20261017T005359Z_transicao.csv`

- Git: `ignored` · `742 B` · modified `2026-10-17 00:53 UTC` · 6 rows

```csv
componente,estado_atual,condicao_para_final,troca_de_codigo,pronto_agora,pronto_para_final
Loader da coorte,provisional,SRAG_COHORT_KIND=final e coorte_final.parquet disponivel,nenhuma,True,False
Schema de features,piloto,features.final preenchida apos validacao do schema,nenhuma; somente YAML,True,False
Definicao de alvo e features,pendente,G1_definicao_alvo_features aprovado,nenhuma; somente gate,True,False
Particao fixa,"teste, treino, validacao","treino, validacao e teste persistidos no dataset supervisionado",nenhuma,True,False
Pilotos comparaveis,concluidos,rerodar Notebook 03 com a fonte final,nenhuma,True,False
Tuning dos finalistas,pendente,confirmar o tuning apos G1 e repeticao dos pilotos,Notebook 05,True,False
```

### `outputs/tables/C3_baseline_logistica_provisional_20261017T010044Z_comparacao.csv`

- Git: `ignored` · `290 B` · modified `2026-10-17 01:00 UTC` · 2 rows

```csv
modelo,auc,ap,brier,f1,precision,recall,accuracy
logistica_C1,0.7752355926034296,0.44061592989801807,0.19806308229531083,0.5058891510814808,0.3758036700301045,0.7737115449002951,0.6694768352654307
dummy_prior,0.5,0.21868742252312387,0.17086323376238108,0.0,0.0,0.0,0.7813125774768761
```

### `outputs/tables/C3_baseline_logistica_provisional_20261017T010044Z_manifesto.json`

- Git: `ignored` · `1.6 KB` · modified `2026-10-17 01:00 UTC`

```json
{
  "cohort_kind": "provisional",
  "dataset_path": "<REPO>\\data\\analytical\\dataset_supervisionado.parquet",
  "dataset_sha256": "408e5d40ef3dc82a57af5b5c9706a224641c7f0808819d333f48d4638d4e022b",
  "feature_columns": [
    "idade_anos",
    "dias_sintomas_ate_internacao",
    "sexo_categoria",
    "cs_gestant",
    "cs_raca",
    "cs_zona",
    "ave_suino",
    "febre",
    "tosse",
    "garganta",
    "dispneia",
    "diarreia",
    "vomito",
    "dor_abd",
    "fadiga",
    "perd_olft",
    "perd_pala",
    "outro_sin",
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
    "out_morbi"
  ],
  "target_column": "alvo_obito_srag",
  "partition_column": "particao",
  "n_treino": 2740584,
  "n_validacao": 587272,
  "n_teste_fechado": 587276,
  "limiar_usado": 0.5,
  "limiar_e_diagnostico": true,
  "tuning_realizado": false,
  "calibracao_aplicada": false,
  "teste_aberto": false,
  "modelos": [
    "dummy_prior",
    "logistica_C1"
  ],
  "artefatos": {
    "comparacao": "<REPO>\\outputs\\tables\\C3_baseline_logistica_provisional_20261017T010044Z_comparacao.csv",
    "predicoes_validacao": "<REPO>\\outputs\\predictions\\C3_baseline_logistica_provisional_20261017T010044Z_predicoes_validacao.parquet"
  }
}
```

### `outputs/tables/C4_boosting_provisional_20261017T010744Z_comparacao.csv`

- Git: `ignored` · `398 B` · modified `2026-10-17 01:07 UTC` · 2 rows

```csv
modelo,ap,pr_auc,auc,brier,f1,precision,recall,accuracy
boosting_base,0.46752119135143005,0.46752119135143005,0.7874327329924564,0.1959726068522269,0.5111828239611778,0.3718000913374565,0.8177436560278442,0.6579881213475187
logistica_C1,0.44061592989801807,0.44061592989801807,0.7752355926034296,0.19806308229531083,0.5058891510814808,0.3758036700301045,0.7737115449002951,0.6694768352654307
```

### `outputs/tables/C4_boosting_provisional_20261017T010744Z_manifesto.json`

- Git: `ignored` · `1.8 KB` · modified `2026-10-17 01:07 UTC`

```json
{
  "cohort_kind": "provisional",
  "dataset_path": "<REPO>\\data\\analytical\\dataset_supervisionado.parquet",
  "dataset_sha256": "408e5d40ef3dc82a57af5b5c9706a224641c7f0808819d333f48d4638d4e022b",
  "feature_columns": [
    "idade_anos",
    "dias_sintomas_ate_internacao",
    "sexo_categoria",
    "cs_gestant",
    "cs_raca",
    "cs_zona",
    "ave_suino",
    "febre",
    "tosse",
    "garganta",
    "dispneia",
    "diarreia",
    "vomito",
    "dor_abd",
    "fadiga",
    "perd_olft",
    "perd_pala",
    "outro_sin",
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
    "out_morbi"
  ],
  "target_column": "alvo_obito_srag",
  "partition_column": "particao",
  "n_treino": 2740584,
  "n_validacao": 587272,
  "n_teste_fechado": 587276,
  "g6_status": "pendente",
  "buscas_executadas": false,
  "metrica_principal": "pr_auc",
  "max_configs": 30,
  "melhor_config_logistica": null,
  "melhor_config_boosting": null,
  "limiar_usado": 0.5,
  "limiar_e_diagnostico": true,
  "calibracao_aplicada": false,
  "teste_aberto": false,
  "features_final_congelada_no_yaml": false,
  "artefatos": {
    "comparacao": "<REPO>\\outputs\\tables\\C4_boosting_provisional_20261017T010744Z_comparacao.csv",
    "predicoes_validacao": "<REPO>\\outputs\\predictions\\C4_boosting_provisional_20261017T010744Z_predicoes_validacao.parquet",
    "busca_logistica": null,
    "busca_boosting": null
  }
}
```

### `outputs/tables/C5_calibracao_limiar_provisional_20261017T021055Z_escolhas.csv`

- Git: `ignored` · `327 B` · modified `2026-10-17 02:10 UTC` · 2 rows

```csv
finalista,metodo_calibracao,brier_base,brier_calibrado,ganho_brier,limiar,metrica,valor_metrica
hist_gradient_boosting,sigmoid,0.19588851055358997,0.14094344151171814,0.054945069041871825,0.255,f1,0.5159037889148097
logistic,isotonic,0.1981048319609869,0.1438547651248468,0.054250066836140115,0.255,f1,0.5059127591117675
```

### `outputs/tables/C5_calibracao_limiar_provisional_20261017T021055Z_hist_gradient_boosting_curva.csv`

- Git: `ignored` · `648 B` · modified `2026-10-17 02:10 UTC` · 10 rows

```csv
bin_centro,freq_positiva,n,gap
0.027825986748290676,0.028480915009822777,97223.0,0.0006549282615321006
0.15081382175876953,0.15179852985951026,45982.0,0.0009847081007407221
0.2502368982378113,0.24860763423958393,51531.0,0.0016292639982273815
0.3485098196979096,0.3484912607389225,47258.0,1.8558958987113794e-05
0.44543437466864416,0.4412066985067408,33082.0,0.004227676161903338
0.5411781595827138,0.5466728897186292,14998.0,0.005494730135915393
0.6342307817883099,0.6602663363270362,3229.0,0.026035554538726302
0.7290706600293554,0.7706422018348624,327.0,0.04157154180550704
0.8173973776475069,1.0,6.0,0.18260262235249314
0.95,,0.0,
```

### `outputs/tables/C5_calibracao_limiar_provisional_20261017T021055Z_hist_gradient_boosting_limiar.csv`

- Git: `ignored` · `15.0 KB` · modified `2026-10-17 02:10 UTC` · 101 rows (first 60 shown)

```csv
limiar,tp,fp,tn,fn,f1,precision,recall,sensibilidade,especificidade,accuracy,youden_j
0.01,63974,186669,42753,240,0.40636860543040176,0.25523952394441496,0.9962624972747376,0.9962624972747376,0.18635091665141093,0.36346701358144096,0.1826134139261486
0.019799999999999998,63741,171677,57745,473,0.42546189993058153,0.2707566965992405,0.9926340050456287,0.9926340050456287,0.25169774476728474,0.41372992412374504,0.2443317498129134
0.0296,63574,165224,64198,640,0.4339344463707971,0.27786082046171734,0.990033326065967,0.990033326065967,0.2798249513996042,0.4351373809750848,0.2698582774655711
0.0394,63414,160720,68702,800,0.43984352241042074,0.2829289621387206,0.9875416575824586,0.9875416575824586,0.2994568960256645,0.4499312073451484,0.286998553608123
0.0492,63225,156674,72748,989,0.44506939140412444,0.28751836070195863,0.9845983741863145,0.9845983741863145,0.3170925194619522,0.46306651772943375,0.30169089364826673
0.059000000000000004,62967,152439,76983,1247,0.45037550962019884,0.292317762736414,0.9805805587566574,0.9805805587566574,0.3355519522975129,0.4766104973504611,0.3161325110541702
0.0688,62673,148038,81384,1541,0.4559279803582795,0.2974358244230249,0.976002117918211,0.976002117918211,0.3547349425948688,0.4905972019779591,0.33073706051307994
0.07859999999999999,62311,143841,85581,1903,0.46093813571233067,0.30225755753036593,0.9703647179742735,0.9703647179742735,0.37302874179459683,0.5036575896688417,0.34339345976887037
0.08839999999999999,61944,139818,89604,2270,0.4657863867416609,0.3070151961221637,0.9646494533902265,0.9646494533902265,0.3905641132934069,0.516108379081584,0.35521356668363335
0.0982,61518,135696,93726,2696,0.4706305368973484,0.3119352581459734,0.9580153860528856,0.9580153860528856,0.40853100400135994,0.5286953915732403,0.3665463900542456
0.108,61038,131692,97730,3176,0.47510741640201753,0.31670212213978105,0.9505403806023609,0.9505403806023609,0.4259835586822537,0.5406966448255663,0.3765239392846147
0.11779999999999999,60552,127885,101537,3662,0.47933315126399656,0.3213381660714191,0.9429719375837045,0.9429719375837045,0.4425774337247518,0.5520065659524036,0.3855493713084561
0.1276,59999,124044,105378,4215,0.4833619998630452,0.3260053357095896,0.934360108387579,0.934360108387579,0.4593195072835212,0.5632041030391369,0.3936796156711002
0.1374,59415,120232,109190,4799,0.4872857898556965,0.33073193540665863,0.9252655184227738,0.9252655184227738,0.475935176225471,0.574197305507499,0.4012006946482449
0.1472,58813,116475,112947,5401,0.4911274227355095,0.33552211218109623,0.915890615753574,0.915890615753574,0.4923111122734524,0.5849419008568432,0.4082017280270265
0.157,58109,112615,116807,6105,0.4946751909014293,0.34036807947330194,0.9049272744261376,0.9049272744261376,0.5091360026501381,0.5956899017831601,0.41406327707627577
0.1668,57334,108922,120500,6880,0.4975398099535731,0.34485371956500815,0.8928582552091444,0.8928582552091444,0.5252329767851383,0.6056273753899386,0.41809123199428266
0.1766,56600,105093,124329,7614,0.5010911569805274,0.3500460749692318,0.8814277260410502,0.8814277260410502,0.5419227449852237,0.6161676361209116,0.4233504710262741
0.1864,55760,101398,128024,8454,0.5037674141264478,0.35480217360872496,0.8683464665026318,0.8683464665026318,0.5580284366800046,0.6258905583784005,0.42637490318263627
0.1962,54828,97492,131930,9386,0.5064146969990856,0.359952731092437,0.8538324975861962,0.8538324975861962,0.5750538309316456,0.6360187442956585,0.4288863285178417
0.20600000000000002,53860,93566,135856,10354,0.5089775089775089,0.36533582950090215,0.8387579032609711,0.8387579032609711,0.5921664007810934,0.6460924409813511,0.4309243040420645
0.2158,52796,89649,139773,11418,0.5109479867801547,0.37064130015093544,0.8221883078456411,0.8221883078456411,0.609239741611528,0.6558085520848942,0.43142804945716917
0.2256,51684,85734,143688,12530,0.5126567211553722,0.3761079334584989,0.8048712118852587,0.8048712118852587,0.6263043648821822,0.6653543843397949,0.431175576767441
0.2354,50586,81890,147532,13628,0.5143728710153033,0.3818502974123615,0.7877721369171832,0.7877721369171832,0.6430595147806226,0.674706098707243,0.4308316516978059
0.2452,49347,78066,151356,14867,0.5150318065825797,0.38729956911775093,0.768477279098016,0.768477279098016,0.6597274890812563,0.6835095151820622,0.4282047681792722
0.255,48099,74152,155270,16115,0.5159037889148097,0.3934446343997186,0.7490422649266515,0.7490422649266515,0.6767877535720201,0.6925887833916822,0.42583001849867164
0.2648,46744,70343,159079,17470,0.5156507686113149,0.3992245082716271,0.7279409474569408,0.7279409474569408,0.6933903461742988,0.7009460692830579,0.42133129363123967
0.2746,45421,66638,162784,18793,0.5153483517044585,0.40533112021345896,0.7073379636839319,0.7073379636839319,0.709539625667983,0.7090581536323884,0.41687758935191477
0.2844,43983,62946,166476,20231,0.5139912237135027,0.4113290127093679,0.6849440931884013,0.6849440931884013,0.7256322410230928,0.716734324129194,0.4105763342114941
0.2942,42542,59320,170102,21672,0.5123196608781522,0.41764347843160354,0.662503503908805,0.662503503908805,0.7414371769054406,0.7241755098148729,0.4039406808142456
0.304,41016,55811,173611,23198,0.5093858085829075,0.4236008551333822,0.6387392157473448,0.6387392157473448,0.7567321355406195,0.7309287689520358,0.3954713512879642
0.3138,39505,52478,176944,24709,0.5058355794285422,0.42948153463139926,0.6152085215062136,0.6152085215062136,0.7712599489150996,0.7371337301965699,0.38646847042131327
0.3236,37930,49278,180144,26284,0.5009840049662533,0.4349371617282818,0.590681159871679,0.590681159871679,0.7852080445641656,0.7426677927774523,0.3758892044358446
0.3334,36333,45980,183442,27881,0.4959222532366049,0.44140050781772017,0.5658111938206621,0.5658111938206621,0.7995833006424842,0.7484606792082714,0.3653944944631462
0.3432,34730,42807,186615,29484,0.4900141797941461,0.44791518887756815,0.5408477902015136,0.5408477902015136,0.8134137092345111,0.7538074350556472,0.3542614994360247
0.353,33061,39690,189732,31153,0.4827656700616946,0.4544404887905321,0.514856573332918,0.514856573332918,0.8270000261526793,0.758738710512335,0.3418565994855973
0.3628,31465,36675,192747,32749,0.47546730737265214,0.4617698855297916,0.4900021802099231,0.4900021802099231,0.8401417475220336,0.7635712242368102,0.33014392773195667
0.3726,29797,33837,195585,34417,0.466131656341906,0.4682559637929409,0.46402653626934937,0.46402653626934937,0.8525119648507989,0.7675557492950456,0.31653850112014825
0.3824,28105,31047,198375,36109,0.4556360747693854,0.47513186367324856,0.4376771420562494,0.4376771420562494,0.8646729607448284,0.7712950728112357,0.30235010280107777
0.3922,26434,28437,200985,37780,0.4439517991350716,0.48174810008930036,0.41165477933160993,0.41165477933160993,0.8760493762585977,0.7744929095887425,0.28770415559020757
0.402,24864,26004,203418,39350,0.4321092786013451,0.4887945270110875,0.38720528233718504,0.38720528233718504,0.8866542877317781,0.7774319225163128,0.2738595700689632
0.4118,23299,23587,205835,40915,0.4194239423942394,0.49692872072686944,0.36283364998286977,0.36283364998286977,0.8971894587267132,0.7803334740971816,0.260023108709583
0.4216,21771,21327,208095,42443,0.40575145370508425,0.5051510510928582,0.3390382159653658,0.3390382159653658,0.907040301278866,0.7828263564413083,0.2460785172442319
0.4314,20177,19130,210292,44037,0.38981462698389696,0.5133182384816953,0.3142149686984147,0.3142149686984147,0.9166165406979279,0.7848799193559373,0.23083150939634267
0.4412,18645,17148,212274,45569,0.3728738988270821,0.5209119101500294,0.290357242968823,0.290357242968823,0.925255642440568,0.7864124289937201,0.21561288540939105
0.451,17150,15319,214103,47064,0.3547676427086458,0.5281961255351258,0.2670757155760426,0.2670757155760426,0.9332278508599873,0.7875498917026522,0.20030356643602998
0.4608,15758,13576,215846,48456,0.33689656646855093,0.537192336537806,0.24539819976952065,0.24539819976952065,0.9408252042088379,0.7887452492201229,0.18622340397835857
0.4706,14415,11968,217454,49799,0.31822245769727475,0.5463745593753554,0.22448375743607313,0.22448375743607313,0.9478341222724935,0.7896477271179283,0.1723178797085667
0.4804,13035,10545,218877,51179,0.2969451215345012,0.5527989821882952,0.2029931167658143,0.2029931167658143,0.9540366660564374,0.7897941669277609,0.15702978282225177
0.49019999999999997,11733,9196,220226,52481,0.2756069201226172,0.5606096803478428,0.18271716448126576,0.18271716448126576,0.9599166601284969,0.7899542290454848,0.1426338246097627
0.5,10589,7971,221451,53625,0.25585328726411677,0.5705280172413794,0.16490173482418163,0.16490173482418163,0.9652561654941548,0.7902300807802858,0.1301579003183364
0.5097999999999999,9448,6878,222544,54766,0.2346163397069779,0.5787088080362611,0.1471330239511633,0.1471330239511633,0.970020311914289,0.790066613085589,0.11715333586545218
0.5196,8418,5918,223504,55796,0.21433481858688733,0.5871930803571429,0.13109290808857882,0.13109290808857882,0.9742047406090087,0.7898282226974894,0.10529764869758762
0.5294,7398,5046,224376,56816,0.19301312322262518,0.59450337512054,0.1152085215062136,0.1152085215062136,0.9780055966733792,0.7893241973055075,0.09321411817959269
0.5392,6478,4263,225159,57736,0.17285037689280236,0.6031095801135835,0.10088142772604106,0.10088142772604106,0.98141852132751,0.788857633260227,0.08229994905355098
0.549,5634,3589,225833,58580,0.153437640426488,0.6108641439878565,0.08773787647553492,0.08773787647553492,0.9843563389735945,0.7882786851748423,0.07209421544912953
0.5588,4882,2980,226442,59332,0.13546811698762418,0.6209615873823454,0.07602703460304606,0.07602703460304606,0.9870108359268074,0.7877916876677247,0.06303787052985355
0.5686,4203,2435,226987,60011,0.1186416756054875,0.6331726423621573,0.06545301647615785,0.06545301647615785,0.9893863709670389,0.7873353403533626,0.05483938744319672
0.5784,3533,1966,227456,60681,0.10135842669229556,0.6424804509910893,0.05501915470146697,0.05501915470146697,0.9914306387356051,0.7866508193818197,0.04644979343707201
0.5882,2955,1593,227829,61259,0.08594863442017393,0.649736147757256,0.046018002304793346,0.046018002304793346,0.9930564636346993,0.7859526761023853,0.0390744659394926
... [41 more rows omitted]
```

### `outputs/tables/C5_calibracao_limiar_provisional_20261017T021055Z_logistic_curva.csv`

- Git: `ignored` · `627 B` · modified `2026-10-17 02:10 UTC` · 10 rows

```csv
bin_centro,freq_positiva,n,gap
0.027438238397586693,0.028146896693633103,92337.0,0.0007086582960464105
0.15322176658723152,0.15335909210446463,49433.0,0.00013732551723311115
0.25488216507363265,0.25634227291801776,52426.0,0.0014601078443851057
0.35484213135240433,0.35244871557937535,54110.0,0.002393415773028984
0.4446337720929318,0.44450808196512664,31428.0,0.00012569012780516697
0.534979850800845,0.5362044486512069,12678.0,0.001224597850361886
0.6365978683019593,0.6183017312448474,1213.0,0.01829613705711186
0.7254462025848847,0.5454545454545454,11.0,0.17999165713033927
0.8500000000000001,,0.0,
0.95,,0.0,
```

### `outputs/tables/C5_calibracao_limiar_provisional_20261017T021055Z_logistic_limiar.csv`

- Git: `ignored` · `14.1 KB` · modified `2026-10-17 02:10 UTC` · 101 rows (first 60 shown)

```csv
limiar,tp,fp,tn,fn,f1,precision,recall,sensibilidade,especificidade,accuracy,youden_j
0.01,64066,205400,24022,148,0.3839966434907696,0.23775170151336347,0.9976952066527548,0.9976952066527548,0.10470661052558168,0.299990464384476,0.10240181717833652
0.019799999999999998,63664,174711,54711,550,0.4207952040556663,0.26707498689040376,0.9914348895879403,0.9914348895879403,0.2384732065800141,0.40313517416120637,0.2299080961679545
0.0296,63389,163466,65956,825,0.4355599531382593,0.27942518348724954,0.9871523343819105,0.9871523343819105,0.28748768644680983,0.440494353553379,0.2746400208287203
0.0394,63379,163139,66283,835,0.43599603758788164,0.2797967490442261,0.9869966051016912,0.9869966051016912,0.2889130074709487,0.4415739214537727,0.2759096125726399
0.0492,63119,157439,71983,1095,0.44329498686668634,0.2861786922260811,0.9829476438159903,0.9829476438159903,0.3137580528458474,0.46010026018608075,0.29670569666183777
0.059000000000000004,63025,155868,73554,1189,0.4452380195473796,0.2879260643328019,0.9814837885819292,0.9814837885819292,0.3206056960535607,0.4651302973749813,0.30208948463549
0.0688,62712,151249,78173,1502,0.4508816392558641,0.2931001444188427,0.9766094621110661,0.9766094621110661,0.34073890036700927,0.47979471182007655,0.3173483624780755
0.07859999999999999,62270,145731,83691,1944,0.45750601546571645,0.2993735607040351,0.9697262279253746,0.9697262279253746,0.3647906478018673,0.4970814205342669,0.33451687572724187
0.08839999999999999,61691,140303,89119,2523,0.4634796850583003,0.30541006168500057,0.960709502600679,0.960709502600679,0.3884501050465954,0.5135950632756201,0.3491596076472745
0.0982,61615,139684,89738,2599,0.4641204008843258,0.3060869651612775,0.9595259600710125,0.9595259600710125,0.3911481897987115,0.5154442915718781,0.3506741498697241
0.108,61599,139560,89862,2615,0.4642446669404951,0.30622045247789065,0.9592767932226617,0.9592767932226617,0.39168867850511285,0.515812093884946,0.3509654717277746
0.11779999999999999,60708,132335,97087,3506,0.4719638338315381,0.3144791574934082,0.9454013143551251,0.9454013143551251,0.4231808632127695,0.5373830184309826,0.3685821775678946
0.1276,59729,125604,103818,4485,0.47869940331881367,0.32227935661754786,0.9301554178216588,0.9301554178216588,0.45251981065460156,0.55697189717882,0.38267522847626045
0.1374,59729,125604,103818,4485,0.47869940331881367,0.32227935661754786,0.9301554178216588,0.9301554178216588,0.45251981065460156,0.55697189717882,0.38267522847626045
0.1472,59447,123781,105641,4767,0.4804923982185724,0.3244427707555614,0.9257638521194755,0.9257638521194755,0.4604658663946788,0.562219891293983,0.38622971851415433
0.157,58016,115340,114082,6198,0.488411836511344,0.3346639285631879,0.9034789921200984,0.9034789921200984,0.49725832744898046,0.5860929858736668,0.4007373195690789
0.1668,57215,111336,118086,6999,0.4916117113827251,0.3394521539474699,0.8910050767745351,0.8910050767745351,0.5147108821298743,0.5970010489177077,0.4057159589044095
0.1766,56628,108518,120904,7586,0.49379141960237183,0.34289658847322974,0.8818637680256642,0.8818637680256642,0.5269939238608329,0.6045988911441377,0.40885769188649723
0.1864,55866,105138,124284,8348,0.49610599508032216,0.3469851680703585,0.8699971968729561,0.8699971968729561,0.5417265998901587,0.6135146916590609,0.4117237967631149
0.1962,54236,98535,130887,9978,0.4999055234232781,0.35501502248463385,0.8446133241972156,0.8446133241972156,0.5705076235060282,0.6304506259450476,0.4151209477032438
0.20600000000000002,53538,95911,133511,10676,0.5011443254096404,0.35823591994593473,0.8337434204379107,0.8337434204379107,0.5819450619382622,0.6370097671947581,0.41568848237617306
0.2158,51838,89702,139720,12376,0.5038832780893688,0.3662427582308888,0.8072694428006354,0.8072694428006354,0.6090087262773405,0.6523655137653421,0.41627816907797577
0.2256,51634,89048,140374,12580,0.5040020302982977,0.36702634310004123,0.8040925654841623,0.8040925654841623,0.6118593683256183,0.653898023403125,0.41595193380978057
0.2354,50840,86346,143076,13374,0.5048659384309832,0.3705917513448894,0.7917276606347525,0.7917276606347525,0.6236367915892983,0.6603958642673242,0.41536445222405094
0.2452,50430,85005,144417,13784,0.5051866024873654,0.3723557426071547,0.7853427601457627,0.7853427601457627,0.629481915422235,0.6635664564290482,0.4148246755679976
0.255,47958,77418,152004,16256,0.5059127591117675,0.3825133996937213,0.7468464820755598,0.7468464820755598,0.6625519784501922,0.6809859826451797,0.40939846052575213
0.2648,46894,74307,155115,17320,0.5058274681120729,0.386910999084166,0.7302768866602298,0.7302768866602298,0.6761121426890185,0.6879571987086052,0.40638902934924825
0.2746,46260,72574,156848,17954,0.5054411957519339,0.3892825285692647,0.7204036502943283,0.7204036502943283,0.6836659082389658,0.6916999278017681,0.40406955853329407
0.2844,44609,68407,161015,19605,0.5034023585171811,0.3947140227932328,0.6946927461301274,0.6946927461301274,0.7018289440419838,0.7002683594654606,0.39652169017211136
0.2942,40595,58846,170576,23619,0.49610461030827047,0.40823201697488964,0.6321830130501137,0.6321830130501137,0.7435032385734586,0.7191590949338637,0.37568625162357216
0.304,39481,56367,173055,24733,0.49332133798153216,0.4119126116350889,0.6148347712336873,0.6148347712336873,0.7543086539215943,0.723807707501805,0.36914342515528165
0.3138,39481,56367,173055,24733,0.49332133798153216,0.4119126116350889,0.6148347712336873,0.6148347712336873,0.7543086539215943,0.723807707501805,0.36914342515528165
0.3236,37905,52790,176632,26309,0.48938409001413735,0.4179392469265119,0.5902918366711309,0.5902918366711309,0.7699000095893157,0.7306222670244793,0.36019184626044654
0.3334,36392,49535,179887,27822,0.48477098194363966,0.42352229217824433,0.5667299965739558,0.5667299965739558,0.78408783813235,0.7365547821111853,0.3508178347063058
0.3432,34833,46476,182946,29381,0.47872844842396045,0.4284027598420839,0.5424518017877722,0.5424518017877722,0.797421345816879,0.7416631475704614,0.33987314760465104
0.353,31259,39571,189851,32955,0.4629454103847635,0.4413242976140054,0.4867941570374062,0.4867941570374062,0.827518720959629,0.7530071244670272,0.3143128779970352
0.3628,30504,38260,191162,33710,0.45878265577764743,0.4436042115060206,0.47503659638085155,0.47503659638085155,0.8332330813958557,0.7549006252639322,0.30826967777670733
0.3726,29322,36241,193181,34892,0.45188284518828453,0.4472339581776307,0.45662939545893416,0.45662939545893416,0.8420334579944382,0.7577510931902083,0.2986628534533724
0.3824,26567,31670,197752,37647,0.43392050697830153,0.4561876470285214,0.4137259787585262,0.4137259787585262,0.8619574408731507,0.7639356209729052,0.27568341963167686
0.3922,25931,30727,198695,38283,0.4290654576742339,0.45767587984044616,0.4038215965365808,0.4038215965365808,0.8660677703097349,0.7649811331035704,0.2698893668463156
0.402,21524,23806,205616,42690,0.39297451252464766,0.47482903154643724,0.33519170274394994,0.33519170274394994,0.8962348859307303,0.7735427536133171,0.23142658867468024
0.4118,19485,20865,208557,44729,0.3726904097012356,0.4828996282527881,0.3034385025072414,0.3034385025072414,0.9090540575881999,0.7766145840428286,0.21249256009544126
0.4216,19485,20865,208557,44729,0.3726904097012356,0.4828996282527881,0.3034385025072414,0.3034385025072414,0.9090540575881999,0.7766145840428286,0.21249256009544126
0.4314,15340,15278,214144,48874,0.3235194870929644,0.5010124763211183,0.23888871585635532,0.23888871585635532,0.9334065608354909,0.7815254260376793,0.1722952766918462
0.4412,14214,13822,215600,50000,0.3081626016260163,0.5069910115565701,0.22135359890366588,0.22135359890366588,0.9397529443558159,0.78264926643872,0.16110654325948182
0.451,14142,13741,215681,50072,0.3071109808137073,0.5071907613958326,0.22023234808608716,0.22023234808608716,0.9401060055269329,0.7826799166314757,0.16033835361302007
0.4608,12880,12229,217193,51334,0.2883915676813363,0.5129634792305547,0.20057931292241568,0.20057931292241568,0.9466964807211166,0.7835313108746884,0.14727579364353227
0.4706,11719,10918,218504,52495,0.26986448054714396,0.5176922737111808,0.1824991434889588,0.1824991434889588,0.9524108411573432,0.784042147420616,0.134909984646302
0.4804,8609,7517,221905,55605,0.2143141647996017,0.53385836537269,0.1340673373407668,0.1340673373407668,0.9672350515643661,0.7850331703197155,0.10130238890513299
0.49019999999999997,7561,6351,223071,56653,0.19355912244323273,0.5434876365727429,0.11774690877378764,0.11774690877378764,0.9723173889164944,0.785435028402512,0.09006429769028212
0.5,7561,6351,223071,56653,0.19355912244323273,0.5434876365727429,0.11774690877378764,0.11774690877378764,0.9723173889164944,0.785435028402512,0.09006429769028212
0.5097999999999999,6988,5731,223691,57226,0.18166456527108002,0.5494142621275258,0.10882362101722366,0.10882362101722366,0.975019832448501,0.7855950905202359,0.08384345346572464
0.5196,5048,3903,225519,59166,0.1379894758422743,0.5639593341526087,0.0786121406546859,0.0786121406546859,0.9829876820880299,0.7852136658992767,0.06159982274271569
0.5294,3616,2649,226773,60598,0.10261212559769577,0.5771747805267359,0.056311707727286886,0.056311707727286886,0.9884535920705076,0.7846074731981092,0.04476529979779453
0.5392,3615,2649,226773,60599,0.10258520389341355,0.5771072796934866,0.05629613479926496,0.05629613479926496,0.9884535920705076,0.7846040676211363,0.04474972686977252
0.549,3614,2649,226773,60600,0.1025582814251458,0.5770397573048061,0.05628056187124303,0.05628056187124303,0.9884535920705076,0.7846006620441636,0.04473415394175073
0.5588,2266,1583,227839,61948,0.06658536943713912,0.5887243439854508,0.03528825489768586,0.03528825489768586,0.9931000514336027,0.7836402893378196,0.028388306331288637
0.5686,1699,1140,228282,62515,0.05067633066380326,0.5984501585065164,0.026458404709253435,0.026458404709253435,0.9950309909250202,0.7832179977931861,0.021489395634273656
0.5784,756,468,228954,63458,0.023105840643051438,0.6176470588235294,0.011773133584576573,0.011773133584576573,0.9979600910113241,0.7822950864335436,0.009733224595900758
0.5882,756,468,228954,63458,0.023105840643051438,0.6176470588235294,0.011773133584576573,0.011773133584576573,0.9979600910113241,0.7822950864335436,0.009733224595900758
... [41 more rows omitted]
```

### `outputs/tables/C5_calibracao_limiar_provisional_20261017T021055Z_manifesto.json`

- Git: `ignored` · `3.2 KB` · modified `2026-10-17 02:10 UTC`

```json
{
  "cohort_kind": "provisional",
  "dataset_sha256": "408e5d40ef3dc82a57af5b5c9706a224641c7f0808819d333f48d4638d4e022b",
  "feature_columns": [
    "idade_anos",
    "dias_sintomas_ate_internacao",
    "sexo_categoria",
    "cs_gestant",
    "cs_raca",
    "cs_zona",
    "ave_suino",
    "febre",
    "tosse",
    "garganta",
    "dispneia",
    "diarreia",
    "vomito",
    "dor_abd",
    "fadiga",
    "perd_olft",
    "perd_pala",
    "outro_sin",
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
    "out_morbi"
  ],
  "target_column": "alvo_obito_srag",
  "partition_column": "particao",
  "n_treino": 2740584,
  "n_validacao": 587272,
  "n_val_cal": 293636,
  "n_val_meas": 293636,
  "n_teste_fechado": 587276,
  "honest_calib_split": true,
  "calib_split_frac": 0.5,
  "calib_split_seed": 42,
  "calib_split_hash": "c1a8f0dfddbf2b40",
  "finalistas": [
    "hist_gradient_boosting",
    "logistic"
  ],
  "calibracao_ativa": true,
  "metodos_candidatos": [
    "sigmoid",
    "isotonic"
  ],
  "escolhas": {
    "hist_gradient_boosting": {
      "metodo": "sigmoid",
      "brier_base": 0.19588851055358997,
      "brier_calibrado": 0.14094344151171814,
      "limiar": 0.255,
      "limiar_metrica": "f1"
    },
    "logistic": {
      "metodo": "isotonic",
      "brier_base": 0.1981048319609869,
      "brier_calibrado": 0.1438547651248468,
      "limiar": 0.255,
      "limiar_metrica": "f1"
    }
  },
  "diagnosticos": {
    "hist_gradient_boosting": {
      "curva": "<REPO>\\outputs\\tables\\C5_calibracao_limiar_provisional_20261017T021055Z_hist_gradient_boosting_curva.csv",
      "ece": 0.0017532450432245082,
      "mce": 0.18260262235249314,
      "brier_decomp": {
        "brier": 0.14094344151171817,
        "reliability": 1.437547312466074e-05,
        "resolution": 0.0291172104868383,
        "uncertainty": 0.17086227571878104,
        "n": 293636.0
      }
    },
    "logistic": {
      "curva": "<REPO>\\outputs\\tables\\C5_calibracao_limiar_provisional_20261017T021055Z_logistic_curva.csv",
      "ece": 0.0010963502365718537,
      "mce": 0.17999165713033927,
      "brier_decomp": {
        "brier": 0.1438547651248468,
        "reliability": 4.260251277333118e-06,
        "resolution": 0.02615998136454755,
        "uncertainty": 0.17086227571878104,
        "n": 293636.0
      }
    }
  },
  "g7_status": "pendente",
  "g8_status": "pendente",
  "teste_aberto": false,
  "yaml_atualizado": false,
  "artefatos": {
    "tabela": "<REPO>\\outputs\\tables\\C5_calibracao_limiar_provisional_20261017T021055Z_escolhas.csv",
    "predicoes_val_meas": "<REPO>\\outputs\\predictions\\C5_calibracao_limiar_provisional_20261017T021055Z_predicoes_val_meas.parquet"
  }
}
```

### `outputs/tables/dicionario_variaveis_revisao.csv`

- Git: `ignored` · `24.8 KB` · modified `2026-10-17 00:33 UTC` · 119 rows (first 60 shown)

```csv
coluna,nome_amigavel,grupo,uso_inicial_sugerido,aplicabilidade,transformacao_sugerida,risco_temporal,percentual_ausente,percentual_preenchido_aplicavel,valores_distintos_sem_ausente,amplitude_preenchimento_ano,ponto_de_decisao,decisao_final_usuario,justificativa_decisao_final
nu_notific,Numero da notificacao,estrutura_coorte,estrutura_coorte,Populacao geral,Identificador tecnico; nao usar como preditor,baixo,0.0,100.0,4666881,0.0,,,
dt_notific,Data da notificacao,estrutura_coorte,estrutura_coorte,Populacao geral,Auditoria temporal; nao usar data bruta,baixo,0.0,100.0,2829,0.0,,,
dt_sin_pri,Data dos primeiros sintomas,estrutura_coorte,estrutura_coorte,Populacao geral,Derivar intervalo entre sintomas e internacao,baixo,0.0,100.0,2828,0.0,,derivar_atributo,"Fonte para o intervalo entre sintomas e internação e para atributos
sazonais. A data bruta não será fornecida diretamente aos modelos."
sem_pri,Semana epidemiologica dos primeiros sintomas,estrutura_coorte,auditoria_temporal,Populacao geral,Auditar contra a semana derivada de dt_sin_pri; não utilizar diretamente como preditora,baixo,0.0,100.0,53,0.0,,,
hospital,Houve internacao?,estrutura_coorte,estrutura_coorte,Populacao geral,Filtro de elegibilidade,baixo,2.554795,97.445205,3,0.004207,,,
dt_interna,Data da internacao por SRAG,estrutura_coorte,estrutura_coorte,Populacao geral,"Ancora temporal; derivar ano, mes, semana e intervalos",confirmar_momento_medicao,6.519196,93.480804,2953,0.0,,estrutura_coorte,"Âncora temporal da coorte. Intervalos negativos não serão excluídos
automaticamente. A decisão dependerá da avaliação de nosocomial,
magnitude, quantidade e distribuição dos casos."
cs_sexo,Sexo,demografia_contexto_social,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,0.0,100.0,3,0.0,,,
nu_idade_n,Idade informada,demografia_contexto_social,modelo_a_nucleo,Populacao geral,Combinar com tp_idade para criar idade_anos,baixo,0.0,100.0,139,0.0,Alta cardinalidade; evitar uso bruto no primeiro piloto,,
tp_idade,"Unidade da idade: dias, meses ou anos",demografia_contexto_social,modelo_a_nucleo,Populacao geral,Combinar com nu_idade_n,baixo,0.0,100.0,3,0.0,,,
cs_gestant,Situacao gestacional,demografia_contexto_social,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,0.0,100.0,8,0.0,,,
cs_raca,Raca ou cor,demografia_contexto_social,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,0.967257,99.032743,6,3.699653,,,
cs_etinia,Etnia indigena,demografia_contexto_social,exploracao_subgrupo,Registros com raca ou cor indigena,"Categorica; preservar sim, nao, ignorado e vazio",baixo,99.763119,70.879015,310,0.816109,Reavaliar o uso detalhado depois da EDA no denominador indígena. | Confirmar se cs_raca = 5 em todos os anos | Avaliar apenas no denominador aplicavel ou em sensibilidade,,
cs_escol_n,Escolaridade,demografia_contexto_social,modelo_b_ampliado,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,34.043168,65.956832,7,29.625463,Preenchimento varia pelo menos 20 pontos percentuais entre 2019 e 2026,,
cs_zona,Zona de residencia,demografia_contexto_social,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,9.943239,90.056761,4,7.92861,,,
ave_suino,"Contato direto com aves, suinos ou outro animal?",exposicao_animal,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,16.876049,83.123951,4,13.492583,,,
out_anim,Especificacao do outro animal,exposicao_animal,exploracao_texto,Registros com contato com outro animal,Categorizar respostas frequentes; nao usar texto bruto,baixo,99.886949,74.921897,575,0.324085,Confirmar se ave_suino = 3 significa outro animal | Avaliar apenas no denominador aplicavel ou em sensibilidade,decidir_depois_da_eda,"Preservar para EDA e possível categorização simples. Não utilizar texto
bruto e não implementar NLP antes do Fine Tuning."
febre,Febre,sintomas,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,14.844276,85.155724,3,18.039239,,,
tosse,Tosse,sintomas,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,11.048017,88.951983,3,12.214481,,,
garganta,Dor de garganta,sintomas,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,27.194075,72.805925,3,28.304763,Preenchimento varia pelo menos 20 pontos percentuais entre 2019 e 2026,,
dispneia,Dispneia,sintomas,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,12.240733,87.759267,3,15.037821,,,
desc_resp,Desconforto respiratorio,sintomas,modelo_b_ampliado,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",confirmar_momento_medicao,17.18364,82.81636,3,20.342508,Preenchimento varia pelo menos 20 pontos percentuais entre 2019 e 2026,modelo_b_ampliado,"Indicador clínico relevante, mas mais dependente da avaliação e do
momento de registro. Entrará no modelo ampliado e será removido se a
auditoria indicar informação posterior à admissão."
saturacao,Saturacao de oxigenio abaixo de 95%?,sintomas,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",confirmar_momento_medicao,16.380239,83.619761,3,18.308578,,modelo_a_nucleo,"Medida clínica objetiva e plausivelmente disponível na avaliação inicial.
Será executada análise adicional sem a variável para verificar robustez
e possível incerteza temporal."
diarreia,Diarreia,sintomas,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,28.277104,71.722896,3,29.808114,Preenchimento varia pelo menos 20 pontos percentuais entre 2019 e 2026,,
vomito,Vomito,sintomas,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,28.683754,71.316246,3,29.275268,Preenchimento varia pelo menos 20 pontos percentuais entre 2019 e 2026,,
dor_abd,Dor abdominal,sintomas,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,37.990598,62.009402,3,81.518308,Preenchimento varia pelo menos 20 pontos percentuais entre 2019 e 2026,,
fadiga,Fadiga,sintomas,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,35.363613,64.636387,3,82.867461,Preenchimento varia pelo menos 20 pontos percentuais entre 2019 e 2026,,
perd_olft,Perda do olfato,sintomas,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,37.834949,62.165051,3,81.09531,Preenchimento varia pelo menos 20 pontos percentuais entre 2019 e 2026,,
perd_pala,Perda do paladar,sintomas,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,37.91213,62.08787,3,80.911408,Preenchimento varia pelo menos 20 pontos percentuais entre 2019 e 2026,,
puerpera,Puerpera ou parturiente,comorbidades_fatores_risco,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,65.655669,34.344331,3,12.660443,,,
cardiopati,Doenca cardiovascular cronica,comorbidades_fatores_risco,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,56.624255,43.375745,3,21.05926,Preenchimento varia pelo menos 20 pontos percentuais entre 2019 e 2026,,
hematologi,Doenca hematologica cronica,comorbidades_fatores_risco,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,65.453073,34.546927,3,12.513576,,,
sind_down,Sindrome de Down,comorbidades_fatores_risco,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,65.570731,34.429269,3,12.425315,,,
hepatica,Doenca hepatica cronica,comorbidades_fatores_risco,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,65.586159,34.413841,3,12.57102,,,
asma,Asma,comorbidades_fatores_risco,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,64.482773,35.517227,3,11.712076,,,
diabetes,Diabetes mellitus,comorbidades_fatores_risco,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,59.456278,40.543722,3,18.748456,,,
neurologic,Doenca neurologica cronica,comorbidades_fatores_risco,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,64.455946,35.544054,3,12.984829,,,
pneumopati,Outra pneumopatia cronica,comorbidades_fatores_risco,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,64.448168,35.551832,3,12.840579,,,
imunodepre,Imunodeficiencia ou imunodepressao,comorbidades_fatores_risco,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,65.006803,34.993197,3,12.634167,,,
renal,Doenca renal cronica,comorbidades_fatores_risco,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,64.898766,35.101234,3,13.248539,,,
obesidade,Obesidade,comorbidades_fatores_risco,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,64.353887,35.646113,3,13.679778,,,
tabag,Tabagismo,comorbidades_fatores_risco,indisponivel_se_100pct_vazio,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,100.0,0.0,0,0.0,Coluna 100% vazia na versao atual; manter documentada e fora dos modelos,,
outro_sin,Apresentou outros sintomas?,sintomas,exploracao_texto,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,28.534962,71.465038,3,23.033708,Preenchimento varia pelo menos 20 pontos percentuais entre 2019 e 2026,,
outro_des,Descricao dos outros sintomas,sintomas,exploracao_texto,Registros com outro sintoma informado,Categorizar respostas frequentes; nao usar texto bruto,baixo,70.493389,98.3981,251506,9.60582,Decidir se os textos frequentes serao categorizados,decidir_depois_da_eda,"Preservar em EDA. Não utilizar texto bruto no primeiro modelo.
Categorizar somente se os termos frequentes acrescentarem informação
não representada pelas variáveis estruturadas."
obes_imc,IMC registrado,comorbidades_fatores_risco,reavaliar_apos_eda,Registros com obesidade informada,Converter para numero e validar faixa plausivel,baixo,98.836404,22.794108,1011,2.171606,Reavaliar somente depois da auditoria de valores e faixas plausíveis. | Decidir se IMC entra no Modelo C ou somente na EDA | Avaliar apenas no denominador aplicavel ou em sensibilidade,,
out_morbi,Outro fator de risco?,comorbidades_fatores_risco,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,58.916714,41.083286,3,17.486237,,,
morb_desc,Descricao de outro fator de risco,comorbidades_fatores_risco,exploracao_texto,Registros com outro fator de risco informado,Categorizar respostas frequentes; nao usar texto bruto,baixo,77.219938,98.836507,232631,12.355135,Decidir se os textos frequentes serao categorizados,decidir_depois_da_eda,"Preservar em EDA. Não utilizar texto bruto no primeiro modelo.
Categorizar somente se houver ganho claro e suficiente antes do
congelamento das features."
out_antiv,Outro antiviral utilizado,tratamentos,excluir_modelagem,Populacao geral,Exploracao de texto,alto_tratamento,99.628705,0.371295,3273,0.564117,Avaliar apenas no denominador aplicavel ou em sensibilidade,excluir_modelagem,"Campo textual de tratamento com baixa cobertura, alta cardinalidade e
risco temporal. Preservado somente para auditoria ou exploração."
... [59 more rows omitted]
```

### `outputs/tables/eda_01_auditoria_datas_pos_corte.csv`

- Git: `ignored` · `347 B` · modified `2026-10-17 00:33 UTC` · 5 rows

```csv
coluna,data_corte_observada,quantidade_posterior_corte,menor_data_posterior_corte,maior_data_posterior_corte
dt_interna,2026-09-28,17,2026-09-29,2026-12-29
dose_1_cov,2026-09-28,3,2026-11-17,2026-12-23
dose_2_cov,2026-09-28,1,2026-10-30,2026-10-30
dose_ref,2026-09-28,1,2026-12-19,2026-12-19
dt_antivir,2026-09-28,3,2026-09-30,2026-12-03
```

### `outputs/tables/eda_01_auditoria_faixa_datas.csv`

- Git: `ignored` · `408 B` · modified `2026-10-17 00:33 UTC` · 19 rows

```csv
coluna,datas_antes_1900,datas_depois_2026,datas_fora_faixa
dt_notific,0,0,0
dt_sin_pri,0,0,0
dt_interna,21,76,97
dt_ut_dose,0,0,0
dt_vac_mae,0,0,0
dt_doseuni,0,0,0
dt_1_dose,0,0,0
dt_2_dose,0,0,0
dose_1_cov,13,52,65
dose_2_cov,25,43,68
dose_ref,0,4,4
dose_2ref,0,1,1
dose_adic,0,0,0
dos_re_bi,0,0,0
dt_antivir,6,19,25
dt_trt_cov,0,0,0
dt_evoluca,0,0,0
dt_encerra,0,0,0
dt_digita,0,0,0
```

### `outputs/tables/eda_01_auditoria_vazamento.csv`

- Git: `ignored` · `1.3 KB` · modified `2026-10-17 00:33 UTC` · 10 rows

```csv
coluna,uso_nesta_eda,candidata_feature_principal,risco_temporal,justificativa,existe_no_dataframe
evolucao,rotulo,False,desfecho,Fonte utilizada para construir o alvo. Não pode ser utilizada como preditora.,True
dt_evoluca,auditoria,False,posterior_admissao,"Data de alta ou óbito, posterior ao ponto de previsão.",True
dt_encerra,auditoria,False,posterior_admissao,"Data de encerramento do caso, posterior ao ponto de previsão.",True
dt_digita,auditoria,False,administrativo,Data administrativa de inclusão do registro.,True
antiviral,eda_sensibilidade,False,tratamento,A disponibilidade até a admissão precisa ser confirmada.,True
tp_antivir,eda_sensibilidade,False,tratamento,Tipo de tratamento condicionado ao uso de antiviral.,True
dt_antivir,auditoria_temporal,False,tratamento,Somente tratamentos iniciados até a admissão poderão ser avaliados em sensibilidade.,True
trat_cov,eda_sensibilidade,False,tratamento,Pode representar decisão assistencial posterior ao ponto de previsão.,True
tipo_trat,eda_sensibilidade,False,tratamento,Tipo de tratamento condicionado ao registro de tratamento para COVID-19.,True
dt_trt_cov,auditoria_temporal,False,tratamento,Somente tratamentos iniciados até a admissão poderão ser avaliados em sensibilidade.,True
```

### `outputs/tables/eda_01_ausencias.csv`

- Git: `ignored` · `5.2 KB` · modified `2026-10-17 00:33 UTC` · 88 rows (first 60 shown)

```csv
coluna,quantidade_ausente,quantidade_preenchida,percentual_ausente,percentual_preenchido
tabag,4666910,0,100.0,0.0
out_trat,4664116,2794,99.94013169313314,0.05986830686685623
dt_trt_cov,4663077,3833,99.9178685682818,0.08213143171820327
tipo_trat,4662126,4784,99.89749105939477,0.10250894060523986
out_anim,4661634,5276,99.88694875195793,0.11305124804206637
dt_vac_mae,4661265,5645,99.87904202138031,0.12095797861968625
dt_2_dose,4656015,10895,99.76654788714589,0.23345211285411546
cs_etinia,4655855,11055,99.7631194944835,0.23688050551649806
tp_pov_ct,4654353,12557,99.7309354583654,0.2690645416346148
out_antiv,4649582,17328,99.62870507466396,0.37129492533603603
dt_doseuni,4649309,17601,99.62285537968377,0.37714462031622636
dt_1_dose,4648284,18626,99.60089223919039,0.3991077608096149
dose_adic,4645758,21152,99.54676649003302,0.4532335099669803
obes_imc,4612606,54304,98.83640353038734,1.163596469612656
pac_cocbo,4583721,83189,98.21747151755659,1.7825284824434153
pac_dscbo,4583721,83189,98.21747151755659,1.7825284824434153
m_amamenta,4573155,93755,97.9910690371145,2.0089309628855068
mae_vac,4562552,104358,97.76387374086923,2.236126259130774
dos_re_bi,4555994,110916,97.62335249661982,2.376647503380181
dose_2ref,4471761,195149,95.81845375205435,4.181546247945643
dt_antivir,4319198,347712,92.54941706611012,7.4505829338898755
tp_antivir,4300025,366885,92.13858848788598,7.861411512114011
dt_ut_dose,4276869,390041,91.64241435982267,8.357585640177334
dose_ref,4193370,473540,89.85324336659588,10.146756633404115
trat_cov,3673788,993122,78.7199238896829,21.280076110317108
dose_2_cov,3642101,1024809,78.04095215035215,21.95904784964784
morb_desc,3603785,1063125,77.21993781752808,22.780062182471912
dose_1_cov,3455748,1211162,74.04788178902099,25.952118210979
outro_des,3289863,1377047,70.49338855902514,29.50661144097486
puerpera,3064091,1602819,65.6556693829536,34.344330617046396
hepatica,3060847,1606063,65.58615872172379,34.4138412782762
sind_down,3060127,1606783,65.57073095474307,34.42926904525693
hematologi,3054636,1612274,65.45307280406092,34.54692719593907
imunodepre,3033809,1633101,65.0068032166894,34.99319678331059
renal,3028767,1638143,64.89876599291608,35.10123400708392
asma,3009353,1657557,64.48277339824423,35.517226601755766
neurologic,3008101,1658809,64.45594622566108,35.544053774338906
pneumopati,3007738,1659172,64.44816805980831,35.55183194019169
obesidade,3003338,1663572,64.35388726159279,35.64611273840721
diabetes,2774771,1892139,59.456278351200254,40.54372164879974
out_morbi,2749590,1917320,58.91671362850366,41.08328637149634
cardiopati,2642603,2024307,56.62425459243911,43.37574540756089
dor_abd,1772987,2893923,37.990597633123414,62.009402366876586
perd_pala,1769325,2897585,37.91213029606313,62.087869703936875
perd_olft,1765723,2901187,37.834948606251245,62.16505139374875
estrang,1753176,2913734,37.566098339158025,62.433901660841975
fadiga,1650388,3016522,35.363613183026885,64.63638681697311
cs_escol_n,1588764,3078146,34.043167749110225,65.95683225088978
vacina_cov,1531225,3135685,32.81025346535502,67.18974653464498
vomito,1338645,3328265,28.68375434709476,71.31624565290524
outro_sin,1331701,3335209,28.53496210554735,71.46503789445265
diarreia,1319667,3347243,28.277104122427904,71.7228958775721
garganta,1269123,3397787,27.194074880381237,72.80592511961876
vacina,1194387,3472523,25.592672667782324,74.40732733221768
pov_ct,1066268,3600642,22.84740867083359,77.15259132916641
co_rg_inte,1010405,3656505,21.650406800216846,78.34959319978316
desc_resp,801945,3864965,17.18363971021511,82.81636028978488
ave_suino,787590,3879320,16.87604860603697,83.12395139396303
antiviral,776808,3890102,16.645017795500664,83.35498220449934
saturacao,764451,3902459,16.380238744694026,83.61976125530597
... [28 more rows omitted]
```

### `outputs/tables/eda_01_cardinalidade.csv`

- Git: `ignored` · `1.5 KB` · modified `2026-10-17 00:33 UTC` · 88 rows (first 60 shown)

```csv
coluna,valores_distintos_sem_na,valores_distintos_com_na
nu_notific,4666881,4666881
outro_des,251506,251507
morb_desc,232631,232632
co_mun_res,5604,5605
co_mun_not,3661,3662
out_antiv,3273,3274
dt_ut_dose,3072,3073
co_mu_inte,3028,3029
dt_interna,2953,2954
dt_antivir,2856,2857
dt_notific,2829,2829
dt_sin_pri,2828,2828
dt_evoluca,2827,2828
dt_encerra,2820,2821
dt_digita,2764,2765
dose_1_cov,2060,2061
dose_2_cov,1960,1961
dt_1_dose,1820,1821
dt_vac_mae,1767,1768
dt_2_dose,1732,1733
pac_dscbo,1628,1629
pac_cocbo,1628,1629
dt_doseuni,1561,1562
dt_trt_cov,1378,1379
dose_ref,1205,1206
obes_imc,1011,1012
dos_re_bi,773,774
dose_adic,773,774
dose_2ref,757,758
out_anim,575,576
out_trat,555,556
co_rg_resi,320,321
co_rg_inte,312,313
co_regiona,312,313
cs_etinia,310,311
nu_idade_n,139,139
co_pais,57,58
sem_pri,53,53
tp_pov_ct,46,47
sg_uf_not,27,28
sg_uf,27,28
sg_uf_inte,27,28
cs_gestant,8,8
cs_escol_n,7,8
cs_raca,6,7
cs_zona,4,5
evolucao,4,5
ave_suino,4,5
febre,3,4
desc_resp,3,4
hospital,3,4
vomito,3,4
dispneia,3,4
garganta,3,4
tosse,3,4
diarreia,3,4
vacina_cov,3,4
perd_olft,3,4
saturacao,3,4
outro_sin,3,4
... [28 more rows omitted]
```

### `outputs/tables/eda_01_duplicidades_nu_notific.csv`

- Git: `ignored` · `4.0 KB` · modified `2026-10-17 00:33 UTC` · 58 rows

```csv
nu_notific,dt_notific,dt_sin_pri,hospital,dt_interna,evolucao,dt_evoluca,dt_encerra
31735935004234,2024-01-03,2024-01-01,1,2024-01-03,,,
31735935004234,2025-01-03,2025-01-01,1,2025-01-03,1,2025-01-10,2025-07-25
31736177754051,2025-01-06,2025-01-02,1,2025-01-02,1,2025-01-05,2025-01-06
31736177754051,2025-01-06,2024-01-02,1,2025-01-02,1,2025-01-05,2025-01-06
31736344210476,2025-01-08,2025-01-03,1,2025-01-03,1,2025-02-07,2025-02-08
31736344210476,2025-01-08,2024-12-25,1,2025-01-05,,,
31736722248953,2025-01-12,2025-01-09,2,,3,2025-01-12,2025-01-12
31736722248953,2025-01-12,2024-01-09,2,,2,2025-01-12,2025-01-12
31736866916969,2025-01-14,2024-01-13,1,2024-01-14,1,2025-01-23,2025-01-24
31736866916969,2025-01-14,2025-01-13,1,2025-01-14,1,2025-01-23,2025-01-24
31737727549117,2025-01-20,2025-01-11,1,2025-01-12,1,,2025-09-25
31737727549117,2025-01-20,2024-01-11,1,2025-01-12,,,
31738324913116,2025-01-30,2025-01-27,1,2025-01-30,1,2025-02-03,2025-02-04
31738324913116,2025-01-30,2024-01-27,1,2025-01-30,1,2025-02-03,2025-02-04
31738932515531,2024-02-07,2024-02-06,1,2024-02-06,,,
31738932515531,2025-02-07,2025-02-06,1,2025-02-06,1,2025-02-08,2025-08-18
31739904591826,2025-02-06,2025-02-05,1,2025-02-06,3,2025-02-06,2025-02-08
31739904591826,2025-02-06,2024-02-05,1,2025-02-06,3,2025-02-06,2025-02-08
31741286280540,2025-02-24,2024-02-02,1,2024-12-02,3,2025-02-27,2025-02-27
31741286280540,2025-02-24,2025-02-10,1,2025-02-14,3,2025-02-27,2025-02-27
31741716994694,2025-03-02,2025-03-01,1,2025-03-02,1,2025-03-10,2025-03-10
31741716994694,2025-03-02,2024-03-01,1,2025-03-02,1,2025-03-10,2025-03-02
31743770891762,2024-04-04,2024-04-04,2,,,,
31743770891762,2025-04-04,2025-04-03,2,,2,2025-04-03,2025-05-04
31743975908104,2025-04-06,2025-04-01,1,2025-04-01,1,2025-04-30,2025-04-11
31743975908104,2025-04-06,2024-04-05,1,2025-04-01,1,2025-04-30,2025-04-11
31744118738694,2025-04-02,2025-03-26,1,2025-03-27,2,2025-04-05,2025-04-09
31744118738694,2025-04-02,2024-03-26,1,2025-03-27,2,2025-04-05,2025-04-09
31744265580768,2025-04-10,2025-04-10,1,2025-04-10,1,2025-04-10,2025-04-10
31744265580768,2025-04-10,2024-04-10,1,2025-04-10,1,2025-04-10,2025-04-10
31744397861067,2025-04-11,2025-04-07,1,2025-04-08,1,2025-06-03,2025-06-03
31744397861067,2025-04-11,2024-04-07,1,2025-04-08,1,2025-06-03,2025-06-03
31744638947734,2025-04-07,2025-04-02,1,2025-04-02,1,2025-04-30,2025-07-07
31744638947734,2025-04-07,2024-05-02,1,2025-04-02,,,
31744827529781,2025-04-14,2025-03-31,1,2025-04-13,1,2025-04-22,2025-04-16
31744827529781,2025-04-14,2024-03-31,1,2025-04-13,,,
31745324608735,2025-04-20,2024-08-15,1,2024-08-15,2,2025-04-20,2025-04-24
31745324608735,2025-04-20,2025-04-16,1,2025-04-16,2,2025-04-20,2025-04-24
31745519106567,2025-04-24,2025-04-15,1,2025-04-20,1,2025-04-30,2025-05-02
31745519106567,2025-04-24,2024-04-15,1,2025-04-20,1,2025-04-30,2025-05-02
31746458224089,2025-05-05,2025-05-02,1,2025-04-14,1,2025-05-26,2025-06-10
31746458224089,2025-05-05,2024-05-02,1,2025-04-14,1,2025-05-26,2025-06-10
31746459301774,2025-05-05,2025-04-29,1,2025-04-30,2,2025-05-04,2025-05-05
31746459301774,2025-05-05,2024-04-29,1,2025-04-30,2,2025-05-04,2025-05-05
31746816257499,2025-04-28,2025-04-26,1,2025-04-28,1,2025-05-06,2025-05-06
31746816257499,2025-04-28,2022-04-26,1,2025-04-28,1,2025-05-06,
31747221217548,2025-04-24,2025-04-23,1,2025-04-23,1,2025-05-13,2025-10-16
31747221217548,2025-04-24,2024-04-23,1,2025-04-23,,,
31748044066509,2025-05-23,2025-05-20,1,2025-05-20,1,,2025-09-26
31748044066509,2025-05-23,2023-05-20,1,2025-05-20,1,,2025-06-06
31748270369373,2025-05-26,2025-05-23,1,2025-05-23,1,2025-05-30,2025-12-02
31748270369373,2025-05-26,2024-05-23,1,2025-05-23,,,
31749232662324,2025-05-23,2025-05-20,1,2025-05-21,1,2025-05-22,2025-07-29
31749232662324,2025-05-23,2023-05-20,1,2025-05-23,,,
31750088488779,2025-05-06,2024-12-28,1,2025-01-02,1,,2025-05-06
31750088488779,2025-05-06,2025-05-06,1,2025-05-06,1,,2025-05-06
31750216000318,2024-06-17,2024-06-16,1,2024-06-17,,,
31750216000318,2025-06-17,2025-06-16,1,2025-06-17,1,,2025-08-01
```

### `outputs/tables/eda_01_frequencias_categoricas.csv`

- Git: `ignored` · `10.2 KB` · modified `2026-10-17 00:33 UTC` · 275 rows (first 60 shown)

```csv
coluna,valor,quantidade,percentual
sg_uf_not,SP,1306611,27.997347281177483
sg_uf_not,MG,521998,11.185088206114967
sg_uf_not,RJ,385820,8.267140356252852
sg_uf_not,PR,380639,8.156124716354075
sg_uf_not,RS,256895,5.504605831267369
sg_uf_not,CE,197156,4.224551148404405
sg_uf_not,SC,187571,4.019169000473546
sg_uf_not,PE,176695,3.7861240092480895
sg_uf_not,BA,176306,3.7777887295876713
sg_uf_not,GO,137685,2.9502390232509303
sg_uf_not,DF,121098,2.594821841432554
sg_uf_not,PA,103062,2.208356278565475
sg_uf_not,MS,95598,2.048421760865326
sg_uf_not,AM,78321,1.6782196356904249
sg_uf_not,PB,72324,1.5497191932134966
sg_uf_not,MT,70767,1.516356647117686
sg_uf_not,MA,54497,1.167731968261655
sg_uf_not,SE,49040,1.0508023510202682
sg_uf_not,ES,45763,0.9805845838038445
sg_uf_not,AL,43497,0.9320299727228509
sg_uf_not,RN,42488,0.9104096714957006
sg_uf_not,PI,41981,0.8995459522467757
sg_uf_not,RO,31827,0.6819715829103197
sg_uf_not,TO,29217,0.6260459276052034
sg_uf_not,AC,20991,0.4497836898504578
sg_uf_not,AP,17444,0.37378051001626345
sg_uf_not,RR,10998,0.2356591406305243
sg_uf_not,,10621,0.22758099041978527
sg_uf,SP,1301367,27.88498171166789
sg_uf,MG,524022,11.228457373294107
sg_uf,RJ,386412,8.279825409103667
sg_uf,PR,379585,8.13354017969063
sg_uf,RS,257423,5.515919527053232
sg_uf,CE,196933,4.219772826131209
sg_uf,SC,187448,4.01653342361434
sg_uf,BA,177563,3.8047230394415146
sg_uf,PE,175844,3.767889245775042
sg_uf,GO,151110,3.237902595078971
sg_uf,DF,105934,2.2698959268552423
sg_uf,PA,105265,2.2555609600356554
sg_uf,MS,96096,2.0590926330269923
sg_uf,AM,80338,1.7214388106905854
sg_uf,MT,78606,1.6843264601202939
sg_uf,PB,72426,1.5519047935357657
sg_uf,MA,56431,1.2091726645682046
sg_uf,SE,48395,1.0369816431000383
sg_uf,ES,45952,0.9846343726362841
sg_uf,AL,43932,0.9413509152737035
sg_uf,RN,42662,0.9141380485160416
sg_uf,PI,40410,0.8658834217930065
sg_uf,RO,34657,0.742611278126212
sg_uf,TO,29024,0.6219104289562044
sg_uf,AC,20399,0.4370986369996422
sg_uf,AP,16631,0.35635998980053185
sg_uf,RR,11161,0.23915181565532656
sg_uf,,884,0.01894186945966389
sg_uf_inte,SP,1155790,24.76563722034494
sg_uf_inte,,514107,11.016004165497083
sg_uf_inte,MG,483408,10.358202750856563
sg_uf_inte,PR,364385,7.807842876764283
... [215 more rows omitted]
```

### `outputs/tables/eda_01_preenchimento_por_ano_internacao.csv`

- Git: `ignored` · `12.2 KB` · modified `2026-10-17 00:33 UTC` · 8 rows

```csv
ano_internacao,nu_notific,dt_notific,dt_sin_pri,sem_pri,hospital,dt_interna,cs_sexo,nu_idade_n,tp_idade,cs_gestant,cs_raca,cs_etinia,cs_escol_n,cs_zona,ave_suino,out_anim,febre,tosse,garganta,dispneia,desc_resp,saturacao,diarreia,vomito,dor_abd,fadiga,perd_olft,perd_pala,puerpera,cardiopati,hematologi,sind_down,hepatica,asma,diabetes,neurologic,pneumopati,imunodepre,renal,obesidade,tabag,outro_sin,outro_des,obes_imc,out_morbi,morb_desc,out_antiv,out_trat,sg_uf_not,co_regiona,co_mun_not,co_pais,sg_uf,co_rg_resi,co_mun_res,sg_uf_inte,co_rg_inte,co_mu_inte,vacina,dt_ut_dose,mae_vac,dt_vac_mae,m_amamenta,dt_doseuni,dt_1_dose,dt_2_dose,vacina_cov,dose_1_cov,dose_2_cov,dose_ref,dose_2ref,dose_adic,dos_re_bi,pac_cocbo,pac_dscbo,pov_ct,tp_pov_ct,estrang,antiviral,tp_antivir,dt_antivir,trat_cov,tipo_trat,dt_trt_cov,evolucao,dt_evoluca,dt_encerra,dt_digita
2019,100.0,100.0,100.0,100.0,99.99579345882847,100.0,100.0,100.0,100.0,100.0,96.30034703964665,0.5447470817120622,92.33568198548743,97.57072247344621,96.64318014512567,0.0,99.65506362393522,99.58986223577662,97.6464402145336,99.22389315385425,99.12714270690924,98.30055736670522,97.16689452098012,97.24471553265329,0.29866442317804187,0.5300241876117362,0.2944578820065201,0.2944578820065201,37.68009254390577,38.59922178988327,37.75581028499316,37.87149016721001,37.62961404984752,38.199600378588705,38.21222000210327,38.16174150804501,38.226942896203596,37.957724261226204,37.56441266168893,37.57072247344621,0.0,92.04543064465244,21.827742139026185,1.4996319276474919,37.95562099064045,17.644336943947838,0.2650120938058681,0.0,99.91586917656956,89.98632874119255,99.91586917656956,99.99369018824271,99.92848880008412,91.20201913976234,99.92848880008412,95.65674624040382,86.21306131033758,95.65674624040382,81.19465769271217,16.479125039436322,12.714270690924387,2.288358397307814,11.39762330423809,0.49637185823956254,0.6141550110421705,0.42906719949521505,1.3145441161005362,0.10516352928804291,0.07571774108739089,0.025239247029130295,0.01051635292880429,0.004206541171521716,0.006309811757282574,0.016826164686086865,0.016826164686086865,1.7162687979808602,0.0,0.47113261121043226,98.87054369544643,61.236723104427384,61.23461983384162,0.20191397623304236,0.0,0.0,94.35902828898938,84.61247239457356,96.52960353349458,65.51898201703649
2020,100.0,100.0,100.0,100.0,99.99897805132969,100.0,100.0,100.0,100.0,100.0,96.503727790036,0.15998141911508534,71.42269190570201,90.21521309952387,84.03205202647777,0.03762629195215422,87.96581117175705,89.92869585414005,76.58697015445361,90.19458831726861,85.20924399024503,85.74623156427825,75.83463012425968,74.97591452792939,45.69178957147834,46.89099988386947,46.10623620949948,46.01342468935083,42.12621066078272,53.63892695389618,42.4288003716177,42.24791545697364,42.325490651492274,43.19498316107305,50.18241783764952,43.56390663105331,43.600232261061436,42.880130066194404,43.23836952734874,43.32746487051446,0.0,75.52860294971549,31.433561723377075,2.384020438973406,49.54128440366973,27.14286377888747,0.7004993612820811,0.0011148530948786436,99.83537335965626,86.30523748693531,99.83537335965626,100.0,99.99098827081639,86.6736964347927,99.99098827081639,94.18195331552666,81.69132504935548,94.18195331552666,80.78169782835907,9.017767971199628,0.7577284868191847,0.05054000696783184,0.5667169898966439,0.010126582278481013,0.010405295552200673,0.007896876088723725,12.811798861920797,2.2180002322610615,2.091743119266055,1.2298687725002904,0.4846823829984903,0.03465335036581117,0.1093485077226803,1.7885959818836374,1.7885959818836374,22.790477296481246,0.035954012309836254,6.14209731738474,88.41723377075833,15.679015213099524,15.354778771338983,1.0600394843804437,0.025920334455928465,0.0008361398211589827,94.35577749390315,88.82954360701429,94.67629775868076,100.0
2021,100.0,100.0,100.0,100.0,99.99975865726556,100.0,100.0,100.0,100.0,100.0,100.0,0.08724539849908954,65.94334237966349,89.64211285910291,83.15059665957521,0.08983983289429068,83.28393852035182,87.56101446004993,70.11036603245819,88.37391712531843,81.35192959549751,84.93514517368833,69.10776797792197,68.05527231304083,66.79166209121065,71.09148458362948,67.586826065498,67.55315875404399,34.64601657783243,45.28796411716225,34.62393371763142,34.512554045688596,34.50989927560978,35.355503881394526,42.054031811385826,35.422778168618926,35.45807454353039,34.95867609029597,35.20834514907138,37.03971415366533,0.0,70.50423737505989,31.20199542172833,1.3273247037216256,42.71760365972123,24.29832616746531,0.34023291987300547,0.0009653709377492618,99.85501335228678,88.51419758971011,99.85501335228678,100.0,99.98527809319933,88.84670754208113,99.98527809319933,91.8934785573014,81.69698937005926,91.8934785573014,74.38454585934305,4.389481318262284,0.9677240294100257,0.0328226118834749,0.7723570858830188,0.005671554259276913,0.005068197423183624,0.004042490801825034,74.6216047602441,20.435997716897734,13.687994526346783,1.9845009695944356,0.4784619710219779,0.02914213518330584,0.08706439144826154,2.3897154207146882,2.3897154207146882,93.25205714513267,0.26330492327111116,72.61604663707,84.11916538855577,2.359788921644461,2.0313817957588842,1.12284707196961,0.007421289083947449,0.0031374555476851008,92.92467572586844,87.28950388380795,93.48097072874644,100.0
2022,100.0,100.0,100.0,100.0,99.9996269596277,100.0,100.0,100.0,100.0,100.0,100.0,0.18148414112117284,63.26634149980882,90.70140916000634,85.02019081015042,0.0880375278614528,81.61582437259273,87.37538120063044,69.34167700299365,84.1860725377004,78.78463446706519,79.99197963199566,67.35878090406334,67.9694479935091,66.52522219217175,68.9885942906171,65.5775131263581,65.5260335549815,34.99976684976732,44.38844693967005,35.281412330849506,35.1314501011872,35.09992818972834,36.481856248892534,41.105132102921836,36.92596081210889,36.757160043645726,35.961464929542,36.101168548966214,35.57853898738191,0.0,69.01172279369935,28.90055676275565,0.4291829483245824,43.41984761300792,25.71945498801608,0.2284872280302536,0.11377731354975892,99.9287492888918,89.54106708198495,99.9287492888918,100.0,99.97649845654546,90.07582045566882,99.97649845654546,94.74423419474573,85.05618920607682,94.74423419474573,61.57889337573559,3.490165723185392,2.8360394303673515,0.10967386945452172,2.4995570145579005,0.021076781034627474,0.019957659917744598,0.01660029656709597,99.83996568028574,56.99422720023875,53.25878743226986,28.327939791283914,5.006574836561687,0.09139489121210143,0.1620860417618697,1.4552304923200314,1.4552304923200314,99.99925391925541,0.23874583826834658,91.33725647458196,82.69596277057084,3.7145495071204078,3.382730095964636,17.762876887351133,0.18819886782247008,0.156117395805161,93.68162869426544,87.73424603877754,93.56206925494511,100.0
2023,100.0,100.0,100.0,100.0,99.99924718919266,100.0,100.0,100.0,100.0,100.0,100.0,0.3560795118774725,64.89492643156385,92.68456097955742,85.66384739019314,0.32408505256501463,86.55291695367579,91.70063725434842,72.62215296362795,87.5741048138487,84.65470450293783,82.6985256200338,72.1840170737491,73.0034516375517,71.38076794230457,73.37910423042034,70.47927700050062,70.41942854131614,29.46576781056269,35.05350602813254,29.952836402919402,29.822600133247512,29.75447075518216,31.698981070572252,33.01941122666757,31.21680574846333,31.117434721892867,30.672899940151545,30.28219113113588,29.73113362015425,0.0,71.76959472430187,28.403928166792763,0.24052305294894813,34.97935416360837,19.180866560520343,0.2969838635003444,0.23600618810483642,99.98155613521988,87.07085078913393,99.98155613521988,100.0,99.97515724335739,88.16920175706042,99.97515724335739,96.41850258402309,84.12359647835105,96.41850258402309,55.814522473284626,3.7023235505568914,6.2727960522601265,0.22546683680190913,5.860255729831257,0.11593286433220036,0.11932051296528413,0.08280918880871453,99.98306175683457,49.45289474575697,45.10353030628107,30.313432779640987,17.575121108438633,1.7947009647270498,7.433253911793157,0.7377545912049114,0.7377545912049114,100.0,0.333118782253238,92.30250949482631,83.23189207704266,5.9618851888237705,5.493260461247182,77.1006244565647,0.39296724143771805,0.3278491066017744,95.5911635067433,89.56754783171668,95.10447131979026,100.0
2024,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,0.4475720989710578,62.71021877355773,92.04118926300583,85.81306957891123,0.23483721242308586,89.91541913508863,93.94988297607819,75.98819104303244,89.49784304980523,88.46337526197176,85.49811143519085,76.30512260870594,77.01713324939712,75.43129136785768,77.06725816700676,74.61113720413472,74.47654982693089,29.915892756357376,34.836423054304625,30.427403726610013,30.316102728453192,30.19611867370257,31.907470191461396,32.91549412512285,31.433848922708957,31.474106730552915,31.02732400036311,30.58567216725146,30.219799737140196,0.0,73.64060828758284,27.05877245260827,0.2158923616729882,33.98508882372211,17.327828801698722,0.1898431918916039,0.25101927243879435,99.99960531560937,87.37641445018491,99.99960531560937,100.0,99.9707933550936,88.38483306823699,99.9707933550936,96.22405443487115,84.26985361155953,96.22405443487115,77.27446747208595,13.423216125225462,5.60570240007578,0.2679907012357568,5.311662529058638,0.5778179478779794,0.5643986785966602,0.44717741458043075,99.98658073071867,45.579337482781895,41.42765237777611,20.577660074121727,12.152727071797036,1.935926936025607,9.961834019426366,0.6950392118942088,0.6950392118942088,100.0,0.4294166170022142,93.88515473601534,82.61336322409785,8.373624031543176,7.7733090733994565,77.1568515236791,0.36271495498624523,0.3252199378766769,95.08341654595903,89.08381912403746,94.6350550782067,100.0
2025,100.0,100.0,100.0,100.0,99.99968315928217,100.0,100.0,100.0,100.0,100.0,100.0,0.605165771063571,64.93397039440333,93.82604177228025,88.40141184223867,0.2341452904795701,92.22979823583088,95.77271114265436,81.5896532495184,92.53459900638751,91.92784903173477,88.74201561391058,81.57824698367637,82.12162881476223,80.88246476731217,82.4137559566055,80.27761583696645,80.15499847916455,31.220216972523573,34.73809946263815,31.600425833924767,31.597574267464264,31.424579235526718,33.09844874784548,33.50844063672311,32.28195021798641,32.418191726655174,32.063013281962895,31.714488492345126,31.3764194464159,0.0,76.18340008111122,25.655860285917065,0.24586839703944036,33.84080654973132,16.41741863530366,0.18756970495792355,0.18345077562607726,99.99683159282165,86.87107117509886,99.99683159282165,100.0,99.96799908749874,87.94832961573557,99.96799908749874,95.5940129777958,82.85511507654871,95.5940129777958,94.069375443577,26.965996654162023,5.222168711345432,0.29687975261076754,5.088778769137179,1.822467808983068,1.9023116698773193,1.2223714894048463,99.99239582277197,44.33298692081517,40.27900993612491,21.961814356686606,12.877040454222852,1.8227846497009024,10.833417824191423,0.7379220318361553,0.7379220318361553,99.99968315928217,0.5224703437088107,95.30156899523472,87.51045574368852,12.115038527831288,11.14487224982257,81.5399092568184,0.2766019466693704,0.2544230964209672,96.23308070566765,88.19324749062152,95.95489455540911,100.0
2026,100.0,100.0,100.0,100.0,99.99952480065387,100.0,100.0,100.0,100.0,100.0,100.0,0.9033539569849551,65.15505754664082,94.02484342181545,89.78368925764359,0.23142208156321578,92.99461123941494,95.99359431281422,82.39148822931219,92.69381005331738,92.59781978539998,89.14882293121966,82.43330577177126,82.9408186734335,81.81697221984624,83.3974852450603,81.38976800767922,81.20586586072858,29.603493665592715,32.579667170377974,29.91522443665118,29.919501230766304,29.77456543019797,31.482907079519855,31.43396154686891,30.57907792318878,30.759653674716542,30.245963181554664,29.98983073399291,29.647687204782407,0.0,77.5601364772522,26.514222716429543,0.21241410771818775,32.0550470922552,14.78772845208565,0.13638221233807582,0.11262224503179084,99.99952480065387,87.37062697801727,99.99952480065387,100.0,99.95628166015644,88.2492705690037,99.95628166015644,95.99929670496773,83.72537279388703,95.99929670496773,95.7084747051388,21.487088833765764,4.062954409374733,0.25138045410049514,3.973616932303101,4.041570438799076,4.445014683659795,2.2182305477147666,99.9833680228856,36.97573632138682,33.74105437230918,21.72183731075186,12.478734829260874,1.4550603978368926,10.561305467643676,0.8605860158336422,0.8605860158336422,100.0,0.7826533230690275,95.86861688478317,89.2034708560241,12.875526283275834,12.130413708550737,83.00972257862173,0.1705965652591262,0.15396458814472672,87.90997823586994,79.48231783233066,87.85437991237323,100.0
```

### `outputs/tables/eda_01_preenchimento_por_ano_notificacao.csv`

- Git: `ignored` · `12.9 KB` · modified `2026-10-17 00:33 UTC` · 9 rows

```csv
ano_notificacao,nu_notific,dt_notific,dt_sin_pri,sem_pri,hospital,dt_interna,cs_sexo,nu_idade_n,tp_idade,cs_gestant,cs_raca,cs_etinia,cs_escol_n,cs_zona,ave_suino,out_anim,febre,tosse,garganta,dispneia,desc_resp,saturacao,diarreia,vomito,dor_abd,fadiga,perd_olft,perd_pala,puerpera,cardiopati,hematologi,sind_down,hepatica,asma,diabetes,neurologic,pneumopati,imunodepre,renal,obesidade,tabag,outro_sin,outro_des,obes_imc,out_morbi,morb_desc,out_antiv,out_trat,sg_uf_not,co_regiona,co_mun_not,co_pais,sg_uf,co_rg_resi,co_mun_res,sg_uf_inte,co_rg_inte,co_mu_inte,vacina,dt_ut_dose,mae_vac,dt_vac_mae,m_amamenta,dt_doseuni,dt_1_dose,dt_2_dose,vacina_cov,dose_1_cov,dose_2_cov,dose_ref,dose_2ref,dose_adic,dos_re_bi,pac_cocbo,pac_dscbo,pov_ct,tp_pov_ct,estrang,antiviral,tp_antivir,dt_antivir,trat_cov,tipo_trat,dt_trt_cov,evolucao,dt_evoluca,dt_encerra,dt_digita
2018,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,33.33333333333333,0.0,66.66666666666666,100.0,33.33333333333333,0.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,66.66666666666666,33.33333333333333,0.0,0.0,0.0,0.0,0.0,100.0,66.66666666666666,100.0,66.66666666666666,100.0,66.66666666666666,100.0,100.0,66.66666666666666,100.0,100.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,100.0,66.66666666666666,66.66666666666666,0.0,0.0,0.0,100.0,100.0,100.0,66.66666666666666
2019,100.0,100.0,100.0,100.0,99.44072048361228,97.31874820084715,100.0,100.0,100.0,100.0,96.25570588477197,0.5901221367767406,92.26467080643171,97.46062425463667,96.44076160710614,0.0,99.57642801332402,99.50446189908294,97.50174774848871,99.13435045441462,99.0150923222437,98.16177982481392,97.01854669572727,97.09668133404614,0.2570218365752354,0.48320105276144265,0.25290948719003165,0.25085331249742976,37.4470535016655,38.35999506518073,37.52107579059917,37.63827774807748,37.397705309043054,37.967265698893776,37.983715096434594,37.91380515688613,37.983715096434594,37.724637085166755,37.31545832133898,37.3401324176502,0.0,91.90689640991899,21.916766048443474,1.4968951762141711,37.73286178393717,17.56590039889789,0.2755274088086524,0.0,99.91364066291072,89.90006990993955,99.91364066291072,99.99383147592219,99.92597771106632,91.12760620142288,99.92597771106632,94.2200929390961,84.84599251552412,94.2200929390961,80.96804704527698,16.437060492659455,12.637249660731175,2.2535674630916644,11.32129785746597,0.49142575153185014,0.6147962330879632,0.42974051075379366,1.2624912612575565,0.09664021055228852,0.07196611424106593,0.0246740963112226,0.008224698770407534,0.0020561746926018834,0.00616852407780565,0.016449397540815067,0.016449397540815067,1.6552206275445163,0.0,0.43796520952420115,98.60385738372332,60.76201834107826,60.75996216638566,0.19328042110457705,0.0,0.0,94.18925031870707,84.08109552987622,96.41814368548752,65.41925401982152
2020,100.0,100.0,100.0,100.0,97.62462493047013,92.57077247566346,100.0,100.0,100.0,100.0,96.22924005929733,0.16321563527442426,70.38589399079203,89.47324438734073,82.38846713968734,0.03638620562384498,87.15941249335168,89.1636134461828,75.65588747087145,89.04044004676237,83.85714671214072,84.30483631865611,74.57161336261639,73.65551664494811,44.04228111912826,45.22570328529136,44.52365843276429,44.42555495492202,40.46955614922523,51.825360140739754,40.76465001780139,40.58863827672145,40.669854376833996,41.51935911531032,48.47043011454691,41.87573501441085,41.91394923514977,41.21390649441541,41.558269722759746,41.63287014912251,0.0,74.39577571821408,31.333310700765242,2.2831038303880526,47.7880581865916,26.240112396815075,0.6676607586959115,0.0010445800657563151,99.50965670746622,86.08401731565556,99.50965670746622,100.0,99.99033763439175,86.75637868464737,99.99033763439175,88.37861152676693,76.75583028011285,88.37861152676693,79.22016875190963,8.992093399385613,0.7400849765883493,0.04866002139648168,0.5538885798672861,0.010358752318750126,0.010271703979937099,0.007747302154359337,12.441296776512965,2.1529665638625786,2.0264853275672516,1.1856854229722307,0.47232428639948054,0.03656030230147103,0.10619897335189205,1.9161950822911473,1.9161950822911473,22.373773380095702,0.0348193355252105,5.833283280538516,86.34638100883801,14.819022151190778,14.513047240262992,1.01393905049413,0.01627803935803591,0.0007834350493172365,93.64120589804725,87.27240123713099,94.05564303913606,100.0
2021,100.0,100.0,100.0,100.0,97.37247551264886,93.65924881967445,100.0,100.0,100.0,100.0,100.0,0.0911563667112959,64.92667183426116,88.79870340356564,81.27539990134592,0.08670283982806004,82.16294834754422,86.47542808822493,68.93991966739482,87.07716158128392,79.97491367768303,83.38654076527376,67.72816573884856,66.65869917553378,65.36819110703968,69.64098372207738,66.20753999013459,66.16734550066944,33.59069832992742,44.2212670002114,33.579310830808254,33.4677471636953,33.46915650764569,34.28753435275879,40.999506729617366,34.3697272919456,34.40039461630611,33.9005285039814,34.15776196180678,35.951744063138605,0.0,69.13209780847016,30.772856035515467,1.265703614967233,41.53697413853851,23.698287647100276,0.3354802339510958,0.0009583538862659432,99.7614262560778,88.15057430765978,99.7614262560778,100.0,99.985568317948,88.5567472341625,99.985568317948,87.46179973222465,77.66071453738284,87.46179973222465,72.47043901064055,4.271552392361356,0.9292086533718553,0.03196392079486999,0.7408075540835741,0.005524628285533084,0.005130011979423578,0.004115284335141992,73.15521104925658,20.068775984779087,13.424339370023256,1.929617363117469,0.4672820801916708,0.029652596716228597,0.08726657740821649,2.418659713903178,2.418659713903178,92.85879782961032,0.2788246071453738,71.69479247410331,81.77904305545769,2.246043266859277,1.9292227468113592,1.0788809809033895,0.007328588542033683,0.002987809174829117,91.9290254386583,85.79899936579523,92.46553449369318,100.0
2022,100.0,100.0,100.0,100.0,96.70646144551846,92.8628556129174,100.0,100.0,100.0,100.0,100.0,0.1766050637082601,62.066811291739896,89.61239565026362,82.86364510105449,0.08478416080843584,80.18453427065026,86.0090688159051,67.90078536906854,82.38840756810193,76.91262082601055,77.92848610500879,65.49318980667839,66.070545913884,64.6154849516696,67.1063200241652,63.69676103910369,63.64269826449912,33.58293744507909,42.93047698813709,33.840379228910365,33.69295090070299,33.663774165202106,35.000411906854126,39.695291904657296,35.47393316124781,35.2690095013181,34.50183298550088,34.64617201230229,34.14862285808436,0.0,67.07285259226714,28.337818541300525,0.40641476274165206,41.89350148286468,24.914357699912127,0.22037016695957823,0.10263345782073813,99.91281304920913,89.4242915202109,99.91281304920913,100.0,99.97734512302284,89.96388949912127,99.97734512302284,89.16358880711776,79.88573017355009,89.16358880711776,59.630038993848856,3.372830623901582,2.681685248242531,0.10434973637961337,2.3605695298769773,0.02008045913884007,0.019565575571177503,0.01596139059753954,99.83026005052724,56.67924126757469,52.8512535698594,27.512631810193323,4.705177669156415,0.07757579086115993,0.1515473967486819,1.5228539652899824,1.5228539652899824,100.0,0.24886039103690685,90.75063159050967,79.99591525702988,3.612766366432337,3.2717418167838312,16.454820683216166,0.17145622803163446,0.14073484182776802,91.92233496265378,85.64281497144113,91.87101823374341,100.0
2023,100.0,100.0,100.0,100.0,97.21502340153947,94.23277762735466,100.0,100.0,100.0,100.0,100.0,0.36253925164303075,64.09701001817972,91.9323588259495,84.40940562551206,0.31225495194860453,85.74703832507569,90.81450016351188,71.88685680930294,86.66692453487023,83.67483288382218,81.57766111195114,71.23386419019421,72.03454496225162,70.4089203644381,72.3875899754908,69.50028658534441,69.43347527805811,28.86142983230362,34.5045238287802,29.35337203700643,29.212365014786396,29.152234838228726,31.02470963454215,32.43372494136429,30.5918426910188,30.48459296090132,30.080208732589504,29.68672529651913,29.133597999880443,0.0,70.3864155030364,27.978114022286842,0.2380592370148708,34.35331929123752,19.025047207463174,0.29256319822211596,0.22575189093581544,99.94268293111755,87.35261953070331,99.94268293111755,100.0,99.97573694630128,88.43355615490377,99.97573694630128,91.80858208824016,80.14719585910551,91.80858208824016,54.84153412827067,3.6004261858127946,6.000007032769188,0.2162576525319727,5.597732635213778,0.11111775317089981,0.11393086084611247,0.07982193028415904,99.98206643857051,49.91437603513572,45.54104851555824,30.461736461040218,17.568912347081227,1.777884050734397,7.195929433193967,0.8154495873522679,0.8154495873522679,100.0,0.35199009786098323,91.85394344950296,81.14936546840002,5.872713910465816,5.345256221363443,74.88422303724202,0.42020795898489005,0.318584444217833,94.98774539968986,88.15330030276071,94.46169426442509,100.0
2024,100.0,100.0,100.0,100.0,97.84074869934716,94.31995501249446,100.0,100.0,100.0,100.0,100.0,0.4495026422711242,62.2011850185648,91.64677359888871,84.81113068348981,0.23275820333011815,89.38287421001866,93.43100488233608,75.42557509896879,88.75237878883804,87.85039419929316,84.63497927520957,75.60135409412369,76.31787694725513,74.68894193706963,76.29515974661011,73.85846066758776,73.72178505059233,29.311892268331107,34.17039390136266,29.823215489406707,29.713353617434894,29.591574525452575,31.274881851935987,32.32918340974009,30.82612403591552,30.861130869696375,30.412745466801233,29.969946260786017,29.627326185484083,0.0,72.56097333894435,26.708724522287064,0.21413754706370872,33.44009176259408,17.243100115820482,0.191047933293361,0.24914438084455848,99.99776552124803,87.76995296422227,99.99776552124803,100.0,99.97132418934973,88.7162547156812,99.97132418934973,92.05642803674972,80.71197941300244,92.05642803674972,76.36591824042247,13.129424733445305,5.457341938559282,0.2584547089777632,5.163135569550013,0.5552679698643299,0.5422335104778433,0.4327440516313557,99.98510347498687,46.23211020449205,42.062945266442966,20.499852896815497,12.054268040622823,1.928355162949363,9.806010003016546,0.7723848219306642,0.7723848219306642,100.0,0.43833024851127855,93.60194250686172,81.12870970024467,8.117861305903865,7.524234784130732,75.59725754974508,0.3593786659417024,0.3202752877822426,94.41789966445577,87.87832518369278,93.96094875967809,100.0
2025,100.0,100.0,100.0,100.0,97.96090971578852,94.57547592719882,100.0,100.0,100.0,100.0,100.0,0.6057798631242342,64.59131526254446,93.33552493948179,87.77591823316698,0.23699231941663432,91.83736290009264,95.40121335285855,81.06243088969248,91.89593855533307,91.33379157825529,88.02695675562595,80.86160007172529,81.40312602731538,80.15450823346583,81.68883177430442,79.54215355189623,79.41065718298915,30.596515346223963,34.12569857445982,30.975762828367355,30.975463972983476,30.8054152595559,32.46555691700786,32.90427662054332,31.674785571262063,31.789247183288005,31.45034517796838,31.09321299423209,30.755805265831864,0.0,75.22010699022744,25.486387137264277,0.2354980424972356,33.21658049669765,16.27835390454559,0.18439377185379993,0.17931323032784435,99.99671259077732,87.32434774812468,99.99671259077732,100.0,99.96772361854099,88.33926063178028,99.96772361854099,91.51669107318968,79.39870296763397,91.51669107318968,93.76318699381369,26.75054541107558,5.076357550581274,0.28600460237291175,4.937688652461074,1.840949164699202,1.885777472281163,1.2151459908550253,99.992528615403,44.611936284032154,40.5370431248319,22.161620991602163,12.955082035802876,1.8463285616090372,10.927049400794955,0.8666806132512478,0.8666806132512478,100.0,0.525387764860584,95.04587430142554,86.04883296972595,11.776097546397299,10.798541585726667,79.98864349541257,0.27345267624996267,0.2495442455395834,95.45171991273422,86.43674725800186,95.26732614088043,100.0
2026,100.0,100.0,100.0,100.0,97.635766025115,93.91021233748664,100.0,100.0,100.0,100.0,100.0,0.8791579246195268,64.71791095753694,93.35397417529043,88.68183975550362,0.2306569731595126,92.532924065063,95.43299193144165,81.83665050589283,92.08003796968634,91.91325523524793,88.36113784859144,81.7155555949841,82.20437094964137,81.09366890965788,82.65193419179127,80.67804278686852,80.47887936196733,28.833895929347996,31.78364375917638,29.139959989886577,29.14395212980665,29.000235092684186,30.66495743935274,30.66407029714828,29.799550218902336,29.962784384522916,29.48461473631916,29.21137493734558,28.882245179491044,0.0,76.31108528541583,26.12057149700811,0.21646269788815797,31.24647915437605,14.514533607164559,0.14504775042915505,0.11355420217083698,99.98846715134202,87.79425397994171,99.98846715134202,100.0,99.95786074528816,88.61219909245352,99.95786074528816,91.47057127522255,79.88138908726374,91.47057127522255,95.51860115417202,21.43291208864325,3.947339238743274,0.2435205351241777,3.85285859396832,4.019197757304507,4.397563907506554,2.2072098046956437,99.98181358480858,37.60418376263623,34.2982483377173,21.976730259977025,12.568587181682286,1.4819710525498684,10.603123627701901,0.9306121724781874,0.9306121724781874,100.0,0.8095172615694433,95.5363439982612,87.3391500290539,12.552175050899784,11.804757743642517,81.06971607013746,0.17432344317632395,0.15524988578044116,86.7904525755956,77.36412308210944,86.69064907759389,100.0
```

### `outputs/tables/eda_01_resumo_datas.csv`

- Git: `ignored` · `1.8 KB` · modified `2026-10-17 00:33 UTC` · 19 rows

```csv
coluna,data_minima_convertida,data_maxima_convertida,quantidade_total,quantidade_original_preenchida,quantidade_ausente_original,quantidade_convertida,quantidade_formato_iso,quantidade_formato_br,quantidade_formato_nao_reconhecido,quantidade_data_calendario_invalida,datas_antes_1900,datas_depois_2026,datas_fora_faixa
dt_notific,2018-12-30,2026-09-28,4666910,4666910,0,4666910,4666910,0,0,0,0,0,0
dt_sin_pri,2018-12-30,2026-09-26,4666910,4666910,0,4666910,4666910,0,0,0,0,0,0
dt_interna,1917-09-01,2026-12-29,4666910,4362665,304245,4362568,4362665,0,0,0,21,76,97
dt_ut_dose,2009-03-02,2026-09-23,4666910,390041,4276869,390041,390041,0,0,0,0,0,0
dt_vac_mae,1955-11-16,2026-09-21,4666910,5645,4661265,5645,5645,0,0,0,0,0,0
dt_doseuni,2013-04-25,2026-09-18,4666910,17601,4649309,17601,17601,0,0,0,0,0,0
dt_1_dose,2012-08-06,2026-09-22,4666910,18626,4648284,18626,18626,0,0,0,0,0,0
dt_2_dose,2012-09-14,2026-09-22,4666910,10895,4656015,10895,10895,0,0,0,0,0,0
dose_1_cov,1900-01-01,2026-12-23,4666910,1211162,3455748,1211097,0,1211162,0,0,13,52,65
dose_2_cov,1900-04-20,2026-10-30,4666910,1024809,3642101,1024741,0,1024809,0,0,25,43,68
dose_ref,1982-02-09,2026-12-19,4666910,473540,4193370,473536,0,473540,0,0,0,4,4
dose_2ref,2020-04-12,2025-11-28,4666910,195149,4471761,195148,0,195149,0,0,0,1,1
dose_adic,2021-01-19,2026-05-24,4666910,21152,4645758,21152,0,21152,0,0,0,0,0
dos_re_bi,2021-03-27,2026-02-04,4666910,110916,4555994,110916,0,110916,0,0,0,0,0
dt_antivir,2018-12-30,2026-12-03,4666910,347712,4319198,347687,347712,0,0,0,6,19,25
dt_trt_cov,2020-03-15,2026-09-27,4666910,3833,4663077,3833,3833,0,0,0,0,0,0
dt_evoluca,2019-01-01,2026-09-27,4666910,4014740,652170,4014740,4014740,0,0,0,0,0,0
dt_encerra,2019-01-05,2026-09-27,4666910,4338057,328853,4338057,4338057,0,0,0,0,0,0
dt_digita,2019-01-18,2026-09-28,4666910,4650091,16819,4650091,4650091,0,0,0,0,0,0
```

### `outputs/tables/eda_01_status_periodos.csv`

- Git: `ignored` · `1.4 KB` · modified `2026-10-17 00:33 UTC` · 18 rows

```csv
ano_internacao,quantidade_registros_int,percentual,status_periodo,dentro_periodo_coorte,observacao
1917.0,4,8.570981655956511e-05,fora_periodo,False,Ano fora do período definido para a coorte
1918.0,1,2.1427454139891278e-05,fora_periodo,False,Ano fora do período definido para a coorte
1941.0,4,8.570981655956511e-05,fora_periodo,False,Ano fora do período definido para a coorte
2009.0,1,2.1427454139891278e-05,fora_periodo,False,Ano fora do período definido para a coorte
2011.0,1,2.1427454139891278e-05,fora_periodo,False,Ano fora do período definido para a coorte
2012.0,2,4.2854908279782555e-05,fora_periodo,False,Ano fora do período definido para a coorte
2016.0,1,2.1427454139891278e-05,fora_periodo,False,Ano fora do período definido para a coorte
2017.0,2,4.2854908279782555e-05,fora_periodo,False,Ano fora do período definido para a coorte
2018.0,11,0.00023570199553880403,fora_periodo,False,Ano fora do período definido para a coorte
2019.0,47545,1.0187683070811309,completo,True,
2020.0,1076375,23.063975949825473,completo,True,
2021.0,1657394,35.513733926730964,completo,True,
2022.0,536135,11.488008125290609,completo,True,
2023.0,265671,5.692653168799056,completo,True,
2024.0,253367,5.429009773061833,completo,True,
2025.0,315616,6.762847365815926,completo,True,
2026.0,210438,4.509150594290441,incompleto,True,Ano incompleto na versão atual dos dados
,304342,6.521274247842792,sem_data_valida,False,Registro sem dt_interna válida
```

### `outputs/tables/eda_01_tipos_memoria.csv`

- Git: `ignored` · `2.9 KB` · modified `2026-10-17 00:33 UTC` · 88 rows (first 60 shown)

```csv
coluna,tipo_pandas,memoria_mb
nu_notific,str,92.27620506286621
dt_notific,str,80.11294555664062
dt_sin_pri,str,80.11294555664062
dt_digita,str,79.95838165283203
dt_interna,str,77.7677812576294
dt_encerra,str,77.53310108184814
dt_evoluca,str,74.44970989227295
co_mun_res,str,62.86055564880371
co_mun_not,str,62.805665016174316
co_mu_inte,str,59.92469501495361
outro_des,str,55.45233154296875
co_rg_resi,str,51.882933616638184
co_regiona,str,51.770304679870605
co_rg_inte,str,50.11062526702881
morb_desc,str,48.541239738464355
dose_1_cov,str,47.712706565856934
dose_2_cov,str,45.935505867004395
sg_uf,str,45.061079025268555
sg_uf_not,str,45.04333209991455
sem_pri,str,44.50724792480469
sg_uf_inte,str,44.083008766174316
nu_idade_n,str,43.637024879455566
dose_ref,str,40.678194999694824
hospital,str,40.49917125701904
evolucao,str,40.28829383850098
cs_zona,str,40.17033290863037
cs_raca,str,40.1631965637207
tosse,str,40.12116241455078
dispneia,str,40.06807804107666
co_pais,str,40.06374645233154
cs_sexo,str,40.056535720825195
cs_gestant,str,40.056535720825195
tp_idade,str,40.056535720825195
febre,str,39.95220184326172
saturacao,str,39.883840560913086
dt_ut_dose,str,39.88188648223877
antiviral,str,39.872056007385254
ave_suino,str,39.86177349090576
desc_resp,str,39.84808349609375
dt_antivir,str,39.47820568084717
vacina,str,39.47382164001465
garganta,str,39.40254783630371
pov_ct,str,39.39747428894043
diarreia,str,39.35434532165527
outro_sin,str,39.34286880493164
vomito,str,39.336246490478516
vacina_cov,str,39.152587890625
cs_escol_n,str,39.0977144241333
fadiga,str,39.03894519805908
estrang,str,38.940918922424316
perd_olft,str,38.92895317077637
perd_pala,str,38.92551803588867
dor_abd,str,38.92202568054199
pac_dscbo,str,38.161781311035156
cardiopati,str,38.092695236206055
dose_2ref,str,38.0232515335083
out_morbi,str,37.9906644821167
diabetes,str,37.96665000915527
obesidade,str,37.748671531677246
pneumopati,str,37.74447536468506
... [28 more rows omitted]
```

### `outputs/tables/eda_01_volume_por_ano_internacao.csv`

- Git: `ignored` · `647 B` · modified `2026-10-17 00:33 UTC` · 18 rows

```csv
ano_internacao,quantidade_registros_int,percentual
1917.0,4,8.570981655956511e-05
1918.0,1,2.1427454139891278e-05
1941.0,4,8.570981655956511e-05
2009.0,1,2.1427454139891278e-05
2011.0,1,2.1427454139891278e-05
2012.0,2,4.2854908279782555e-05
2016.0,1,2.1427454139891278e-05
2017.0,2,4.2854908279782555e-05
2018.0,11,0.00023570199553880403
2019.0,47545,1.0187683070811309
2020.0,1076375,23.063975949825473
2021.0,1657394,35.513733926730964
2022.0,536135,11.488008125290609
2023.0,265671,5.692653168799056
2024.0,253367,5.429009773061833
2025.0,315616,6.762847365815926
2026.0,210438,4.509150594290441
,304342,6.521274247842792
```

### `outputs/tables/eda_01_volume_por_ano_notificacao.csv`

- Git: `ignored` · `333 B` · modified `2026-10-17 00:33 UTC` · 9 rows

```csv
ano_notificacao,quantidade_registros,percentual
2018,3,6.428236241967383e-05
2019,48634,1.0421028046394725
2020,1148787,24.61558075900328
2021,1773875,38.00962521239964
2022,582656,12.484834719332492
2023,284383,6.093603690664701
2024,268519,5.753678558189466
2025,334610,7.169840429749021
2026,225443,4.830669543659509
```

### `outputs/tables/eda_02_alvo_por_ano.csv`

- Git: `ignored` · `608 B` · modified `2026-10-17 00:34 UTC` · 8 rows

```csv
ano_internacao,quantidade_cura,quantidade_obito_srag,quantidade_total,percentual_cura,percentual_obito_srag
2019,38292,5221,43513,88.0012869717096,11.998713028290396
2020,705699,274113,979812,72.02391887423302,27.97608112576698
2021,1062924,417291,1480215,71.80875751157771,28.19124248842229
2022,389547,86433,475980,81.84104374133368,18.158956258666333
2023,217667,23037,240704,90.42932398298325,9.570676017016751
2024,210358,19120,229478,91.66804661013256,8.331953389867438
2025,268686,21227,289913,92.67814827206783,7.321851727932173
2026,165778,9743,175521,94.44909725901745,5.55090274098256
```

### `outputs/tables/eda_02_auditoria_idade.csv`

- Git: `ignored` · `331 B` · modified `2026-10-17 00:34 UTC` · 3 rows

```csv
tipo_idade,quantidade_registros,quantidade_valor_informado,quantidade_idade_convertida,quantidade_idade_ausente,quantidade_nao_convertida,quantidade_tipo_invalido,percentual_convertido
1,26669,26669,26668,0,1,0,99.9962503280963
2,355242,355242,355227,0,15,0,99.995777526306
3,3533225,3533225,3533217,0,8,0,99.99977357796348
```

### `outputs/tables/eda_02_ausencia_por_desfecho.csv`

- Git: `ignored` · `4.2 KB` · modified `2026-10-17 00:39 UTC` · 32 rows

```csv
coluna,nome_amigavel,quantidade_cura,ausente_cura,percentual_ausente_cura,quantidade_obito,ausente_obito,percentual_ausente_obito,diferenca_pp_obito_menos_cura,diferenca_absoluta_pp
cardiopati,Doenca cardiovascular cronica,3058951,1824837,59.65564665795562,856185,331032,38.663606580353544,-20.992040077602077,20.992040077602077
diabetes,Diabetes mellitus,3058951,1898839,62.07484199648834,856185,366939,42.85744319276792,-19.21739880372042,19.21739880372042
out_morbi,Outro fator de risco?,3058951,1874080,61.26544688031943,856185,364372,42.557624812394515,-18.707822067924916,18.707822067924916
renal,Doenca renal cronica,3058951,2032866,66.45631133025668,856185,440595,51.460256837015365,-14.996054493241317,14.996054493241317
obesidade,Obesidade,3058951,2015083,65.87496824891932,856185,435685,50.88678264627388,-14.988185602645437,14.988185602645437
neurologic,Doenca neurologica cronica,3058951,2018213,65.9772909078962,856185,438174,51.177490846020426,-14.799800061875779,14.799800061875779
pneumopati,Outra pneumopatia cronica,3058951,2016957,65.93623108052401,856185,438583,51.225260895717625,-14.710970184806385,14.710970184806385
imunodepre,Imunodeficiencia ou imunodepressao,3058951,2031395,66.40822294963208,856185,446538,52.15438252246886,-14.253840427163219,14.253840427163219
hepatica,Doenca hepatica cronica,3058951,2047407,66.93167036673682,856185,453221,52.934938126689914,-13.99673224004691,13.99673224004691
hematologi,Doenca hematologica cronica,3058951,2042358,66.76661378361406,856185,452872,52.89417590824414,-13.872437875369926,13.872437875369926
puerpera,Puerpera ou parturiente,3058951,2047771,66.94356987084788,856185,454781,53.117141739226916,-13.826428131620965,13.826428131620965
sind_down,Sindrome de Down,3058951,2045025,66.85380053488925,856185,454593,53.09518386797246,-13.758616666916787,13.758616666916787
asma,Asma,3058951,2004879,65.5413898424656,856185,451326,52.713607456332454,-12.827782386133151,12.827782386133151
vacina_cov,Recebeu vacina contra COVID-19?,3058951,904011,29.55297420586338,856185,357156,41.71481630722332,12.161842101359944,12.161842101359944
dor_abd,Dor abdominal,3058951,1061739,34.709251635609725,856185,349829,40.85904331423699,6.149791678627267,6.149791678627267
perd_olft,Perda do olfato,3058951,1057820,34.58113582074378,856185,348117,40.65908652919637,6.07795070845259,6.07795070845259
perd_pala,Perda do paladar,3058951,1060020,34.65305590053584,856185,348634,40.71947067514614,6.066414774610301,6.066414774610301
fadiga,Fadiga,3058951,985594,32.21999960117047,856185,322940,37.718483738911566,5.4984841377410945,5.4984841377410945
tosse,Tosse,3058951,263141,8.60232805298287,856185,118414,13.830422163434305,5.228094110451435,5.228094110451435
febre,Febre,3058951,379907,12.419518978891784,856185,144159,16.83736575623259,4.417846777340806,4.417846777340806
vomito,Vomito,3058951,782772,25.589556681359067,856185,256373,29.943645357019804,4.354088675660737,4.354088675660737
garganta,Dor de garganta,3058951,750713,24.54151766406196,856185,243313,28.41827408795996,3.8767564238980015,3.8767564238980015
diarreia,Diarreia,3058951,774678,25.32495616961501,856185,249086,29.092544251534424,3.7675880819194134,3.7675880819194134
outro_sin,Apresentou outros sintomas?,3058951,778040,25.43486312791542,856185,249920,29.189953105929213,3.7550899780137925,3.7550899780137925
saturacao,Saturacao de oxigenio abaixo de 95%?,3058951,461890,15.09962075234288,856185,104118,12.16068957059514,-2.938931181747739,2.938931181747739
dispneia,Dispneia,3058951,339613,11.102270026554855,856185,79534,9.289347512511899,-1.8129225140429561,1.8129225140429561
cs_escol_n,Escolaridade,3058951,1001269,32.73243016968889,856185,266269,31.09947032475458,-1.6329598449343088,1.6329598449343088
vacina,Recebeu vacina contra influenza?,3058951,720472,23.552910785429386,856185,192208,22.449353819560024,-1.1035569658693625,1.1035569658693625
desc_resp,Desconforto respiratorio,3058951,473204,15.469486108146224,856185,129163,15.08587513212682,-0.38361097601940486,0.38361097601940486
sg_uf,UF de residencia,3058951,562,0.018372311292335183,856185,195,0.02277545156712626,0.004403140274791079,0.004403140274791079
nu_idade_n,Idade informada,3058951,0,0.0,856185,0,0.0,0.0,0.0
tp_idade,"Unidade da idade: dias, meses ou anos",3058951,0,0.0,856185,0,0.0,0.0,0.0
```

### `outputs/tables/eda_02_cluster_ano_sensibilidade.csv`

- Git: `ignored` · `1.6 KB` · modified `2026-10-17 00:40 UTC` · 32 rows

```csv
matriz,cluster_rotulo,ano_internacao,quantidade,percentual_dentro_cluster
nucleo,Cluster 1,2019,6704,16.857775095554214
nucleo,Cluster 1,2020,1685,4.237075035204184
nucleo,Cluster 1,2021,1761,4.428183464091732
nucleo,Cluster 1,2022,3722,9.35928384630859
nucleo,Cluster 1,2023,6079,15.286159726413196
nucleo,Cluster 1,2024,6349,15.965097565882116
nucleo,Cluster 1,2025,6422,16.148662240997787
nucleo,Cluster 1,2026,7046,17.71776302554818
nucleo,Cluster 2,2019,3296,8.192483595148142
nucleo,Cluster 2,2020,8315,20.66762775899781
nucleo,Cluster 2,2021,8239,20.47872340425532
nucleo,Cluster 2,2022,6278,15.604493935175977
nucleo,Cluster 2,2023,3921,9.745973354543647
nucleo,Cluster 2,2024,3651,9.074865778484789
nucleo,Cluster 2,2025,3578,8.893418174587394
nucleo,Cluster 2,2026,2954,7.3424139988069195
ampliada,Cluster 1,2019,6452,16.627580341726155
ampliada,Cluster 1,2020,1368,3.5255006056232765
ampliada,Cluster 1,2021,1782,4.592428420482952
ampliada,Cluster 1,2022,3623,9.336906940185036
ampliada,Cluster 1,2023,5994,15.447259232533566
ampliada,Cluster 1,2024,6263,16.14050460015978
ampliada,Cluster 1,2025,6329,16.31059454165915
ampliada,Cluster 1,2026,6992,18.01922531763008
ampliada,Cluster 2,2019,3548,8.612277593028619
ampliada,Cluster 2,2020,8632,20.952982013253393
ampliada,Cluster 2,2021,8218,19.948054469985678
ampliada,Cluster 2,2022,6377,15.47928247202466
ampliada,Cluster 2,2023,4006,9.724009029783721
ampliada,Cluster 2,2024,3737,9.071048862781272
ampliada,Cluster 2,2025,3671,8.910843022550186
ampliada,Cluster 2,2026,3008,7.30150253659247
```

### `outputs/tables/eda_02_cluster_desfecho_sensibilidade.csv`

- Git: `ignored` · `365 B` · modified `2026-10-17 00:40 UTC` · 4 rows

```csv
matriz,cluster_rotulo,quantidade_registros,quantidade_obitos,proporcao_obito,percentual_obito
nucleo,Cluster 1,39768,1039,0.02612653389660028,2.612653389660028
nucleo,Cluster 2,40232,10762,0.267498508649831,26.7498508649831
ampliada,Cluster 1,38803,964,0.024843439940210807,2.4843439940210805
ampliada,Cluster 2,41197,10837,0.26305313493701,26.305313493701
```

### `outputs/tables/eda_02_comorbidades_por_ano.csv`

- Git: `ignored` · `14.8 KB` · modified `2026-10-17 00:37 UTC` · 104 rows (first 60 shown)

```csv
ano_internacao,grupo_clinico,coluna,nome_amigavel,quantidade_total,quantidade_sim,quantidade_nao,quantidade_ignorado,quantidade_ausente,quantidade_inesperado,quantidade_respostas_validas,percentual_sim_validos,percentual_nao_validos,percentual_sem_resposta_valida
2019,comorbidades,asma,Asma,43513,2504,14109,259,26641,0,16613,15.072533558056945,84.92746644194305,61.820605336336264
2020,comorbidades,asma,Asma,979812,38401,380622,11662,549127,0,419023,9.164413409287796,90.8355865907122,57.23434699717905
2021,comorbidades,asma,Asma,1480215,46306,480519,10731,942659,0,526825,8.789636027143738,91.21036397285626,64.40888654688676
2022,comorbidades,asma,Asma,475980,23147,151272,2484,299077,0,174419,13.270916585922404,86.72908341407759,63.3558132694651
2023,comorbidades,asma,Asma,240704,16950,57824,748,165182,0,74774,22.66830716559232,77.33169283440769,68.93528981653816
2024,comorbidades,asma,Asma,229478,15656,56016,515,157291,0,71672,21.84395579863824,78.15604420136177,68.76737639337975
2025,comorbidades,asma,Asma,289913,21168,73108,480,195157,0,94276,22.453222453222455,77.54677754677755,67.48127886641855
2026,comorbidades,asma,Asma,175521,13998,40239,213,121071,0,54237,25.808949610044802,74.1910503899552,69.09942400054693
2019,comorbidades,cardiopati,Doenca cardiovascular cronica,43513,4699,12134,191,26489,0,16833,27.915404265431,72.084595734569,61.31500930756326
2020,comorbidades,cardiopati,Doenca cardiovascular cronica,979812,324584,199994,6493,448741,0,524578,61.87525973258505,38.12474026741495,46.46136197556266
2021,comorbidades,cardiopati,Doenca cardiovascular cronica,1480215,421658,252532,6646,799379,0,674190,62.54290333585488,37.457096664145126,54.453238212016494
2022,comorbidades,cardiopati,Doenca cardiovascular cronica,475980,123882,88039,1718,262341,0,211921,58.45668904922117,41.543310950778825,55.4769107945712
2023,comorbidades,cardiopati,Doenca cardiovascular cronica,240704,39973,42468,633,157630,0,82441,48.48679661818755,51.513203381812446,65.75004985376229
2024,comorbidades,cardiopati,Doenca cardiovascular cronica,229478,36489,41603,390,150996,0,78092,46.72565691748194,53.27434308251806,65.9697225877862
2025,comorbidades,cardiopati,Doenca cardiovascular cronica,289913,42965,55616,441,190891,0,98581,43.58344914334405,56.416550856655945,65.99635062932673
2026,comorbidades,cardiopati,Doenca cardiovascular cronica,175521,22336,33575,208,119402,0,55911,39.9492049864964,60.0507950135036,68.1456919684824
2019,comorbidades,diabetes,Diabetes mellitus,43513,3257,13412,191,26653,0,16669,19.539264502969584,80.46073549703041,61.691908165375864
2020,comorbidades,diabetes,Diabetes mellitus,979812,227313,262733,8005,481761,0,490046,46.38605355415614,53.613946445843865,49.98571154466367
2021,comorbidades,diabetes,Diabetes mellitus,1480215,289134,337285,7860,845936,0,626419,46.15664595103278,53.84335404896723,57.68053965133444
2022,comorbidades,diabetes,Diabetes mellitus,475980,77827,118313,2014,277826,0,196140,39.67931069644132,60.32068930355868,58.79238623471574
2023,comorbidades,diabetes,Diabetes mellitus,240704,24216,53370,637,162481,0,77586,31.211816564844174,68.78818343515583,67.76704998670566
2024,comorbidades,diabetes,Diabetes mellitus,229478,21613,52032,408,155425,0,73645,29.347545658225272,70.65245434177473,67.90759898552366
2025,comorbidades,diabetes,Diabetes mellitus,289913,26275,68840,455,194343,0,95115,27.624454607580297,72.37554539241971,67.19188170244178
2026,comorbidades,diabetes,Diabetes mellitus,175521,13487,40483,198,121353,0,53970,24.989809153233278,75.01019084676672,69.25154255046405
2019,comorbidades,hematologi,Doenca hematologica cronica,43513,441,16002,246,26824,0,16443,2.681992337164751,97.31800766283524,62.21129317675178
2020,comorbidades,hematologi,Doenca hematologica cronica,979812,9316,401644,12385,556467,0,410960,2.2668872883005644,97.73311271169943,58.057259964156394
2021,comorbidades,hematologi,Doenca hematologica cronica,1480215,9016,506018,11745,953436,0,515034,1.7505640404322822,98.24943595956772,65.20546001763257
2022,comorbidades,hematologi,Doenca hematologica cronica,475980,4832,163535,2825,304788,0,168367,2.869921065291892,97.13007893470811,64.62729526450691
2023,comorbidades,hematologi,Doenca hematologica cronica,240704,2340,68077,874,169413,0,70417,3.3230611926097393,96.67693880739026,70.74539683594789
2024,comorbidades,hematologi,Doenca hematologica cronica,229478,2444,65639,586,160809,0,68083,3.589736057459278,96.41026394254072,70.33136074046314
2025,comorbidades,hematologi,Doenca hematologica cronica,289913,2595,87107,576,199635,0,89702,2.8929120866870304,97.10708791331297,69.05899356013701
2026,comorbidades,hematologi,Doenca hematologica cronica,175521,1459,49938,266,123858,0,51397,2.8386870829036717,97.16131291709632,70.71746400715584
2019,comorbidades,hepatica,Doenca hepatica cronica,43513,335,16071,236,26871,0,16406,2.0419358771181275,97.95806412288186,62.296325236136326
2020,comorbidades,hepatica,Doenca hepatica cronica,979812,10167,399852,12280,557513,0,410019,2.4796411873596105,97.5203588126404,58.15329879609558
2021,comorbidades,hepatica,Doenca hepatica cronica,1480215,10305,503010,11758,955142,0,513315,2.007539230297186,97.99246076970282,65.32159179578643
2022,comorbidades,hepatica,Doenca hepatica cronica,475980,4128,163434,2804,305614,0,167562,2.463565724925699,97.5364342750743,64.7964200176478
2023,comorbidades,hepatica,Doenca hepatica cronica,240704,1552,68386,866,169900,0,69938,2.219108353112757,97.78089164688724,70.94439643711779
2024,comorbidades,hepatica,Doenca hepatica cronica,229478,1308,66259,565,161346,0,67567,1.935856261192594,98.0641437388074,70.55621889680056
2025,comorbidades,hepatica,Doenca hepatica cronica,289913,1429,87741,591,200152,0,89170,1.6025569137602331,98.39744308623976,69.24249688699713
2026,comorbidades,hepatica,Doenca hepatica cronica,175521,774,50376,281,124090,0,51150,1.5131964809384164,98.48680351906158,70.85818790913908
2019,comorbidades,imunodepre,Imunodeficiencia ou imunodepressao,43513,1684,14839,253,26737,0,16523,10.19185377957998,89.80814622042001,62.02744007537977
2020,comorbidades,imunodepre,Imunodeficiencia ou imunodepressao,979812,32709,382862,11964,552277,0,415571,7.870857206109185,92.12914279389082,57.586659481614845
2021,comorbidades,imunodepre,Imunodeficiencia ou imunodepressao,1480215,30940,489082,11680,948513,0,520022,5.949748279880467,94.05025172011953,64.86848194350145
2022,comorbidades,imunodepre,Imunodeficiencia ou imunodepressao,475980,16502,155125,2784,301569,0,171627,9.615037261037017,90.38496273896298,63.94239253750158
2023,comorbidades,imunodepre,Imunodeficiencia ou imunodepressao,240704,7041,65094,857,167712,0,72135,9.76086504470784,90.23913495529216,70.03165713905875
2024,comorbidades,imunodepre,Imunodeficiencia ou imunodepressao,229478,6330,63087,606,159455,0,69417,9.11880375124249,90.88119624875752,69.75004139830398
2025,comorbidades,imunodepre,Imunodeficiencia ou imunodepressao,289913,6855,84080,622,198356,0,90935,7.5383515698026065,92.4616484301974,68.63369355634276
2026,comorbidades,imunodepre,Imunodeficiencia ou imunodepressao,175521,3915,47966,326,123314,0,51881,7.546115148127446,92.45388485187256,70.4417135271563
2019,comorbidades,neurologic,Doenca neurologica cronica,43513,2051,14585,211,26666,0,16636,12.328684779995191,87.67131522000481,61.767747569691814
2020,comorbidades,neurologic,Doenca neurologica cronica,979812,49276,373606,11476,545454,0,422882,11.652423134586007,88.34757686541398,56.840495931872645
2021,comorbidades,neurologic,Doenca neurologica cronica,1480215,48912,478226,11203,941874,0,527138,9.278784682568892,90.72121531743112,64.38774097006178
2022,comorbidades,neurologic,Doenca neurologica cronica,475980,29637,146898,2555,296890,0,176535,16.78817231710426,83.21182768289574,62.91125677549477
2023,comorbidades,neurologic,Doenca neurologica cronica,240704,12286,61158,781,166479,0,73444,16.728391699798486,83.27160830020152,69.48783568199947
2024,comorbidades,neurologic,Doenca neurologica cronica,229478,11012,59366,523,158577,0,70378,15.646935121771008,84.35306487822899,69.33126487070655
2025,comorbidades,neurologic,Doenca neurologica cronica,289913,12458,79193,547,197715,0,91651,13.592868599360619,86.40713140063939,68.38672291342576
2026,comorbidades,neurologic,Doenca neurologica cronica,175521,7613,44927,249,122732,0,52540,14.489912447658925,85.51008755234108,70.06625987773543
2019,comorbidades,obesidade,Obesidade,43513,667,15574,372,26900,0,16241,4.106889969829444,95.89311003017056,62.67552225771609
2020,comorbidades,obesidade,Obesidade,979812,49907,365428,16830,547647,0,415335,12.016083402554564,87.98391659744543,57.610745734896085
2021,comorbidades,obesidade,Obesidade,1480215,124189,425917,13021,917088,0,550106,22.575467273580003,77.42453272642,62.83607448917894
2022,comorbidades,obesidade,Obesidade,475980,16485,152772,3394,303329,0,169257,9.739626721494531,90.26037327850547,64.44031261817723
... [44 more rows omitted]
```

### `outputs/tables/eda_02_comparacao_original_sensibilidade.csv`

- Git: `ignored` · `825 B` · modified `2026-10-17 00:40 UTC` · 2 rows

```csv
matriz,k_original,silhouette_original,ari_estabilidade_original,menor_cluster_percentual_original,maior_cluster_percentual_original,k_sem_indicadores_ausencia,indicadores_ausencia_excluidos,features_sensibilidade,componentes_pca_90,silhouette_sem_indicadores_ausencia,menor_cluster_percentual_sem_ausencia,maior_cluster_percentual_sem_ausencia,ari_original_vs_sem_ausencia,queda_silhouette,queda_silhouette_percentual,rotulo_matriz
ampliada,2,0.2935044765472412,0.9999797474460079,33.29125,66.70875000000001,2,28,69,30,0.16932816803455353,48.503750000000004,51.496249999999996,0.08798891737376612,0.12417630851268768,42.30814806420876,Ampliada
nucleo,2,0.36442187428474426,0.9999493687268458,33.28875,66.71125,2,26,31,15,0.23322749137878418,49.71,50.29,0.09417414798684123,0.13119438290596008,36.00068825820543,Núcleo
```

### `outputs/tables/eda_02_contadores_clinicos_por_ano.csv`

- Git: `ignored` · `1.2 KB` · modified `2026-10-17 00:37 UTC` · 8 rows

```csv
ano_internacao,quantidade_registros,sintomas_confirmados_media,sintomas_confirmados_mediana,sintomas_avaliados_media,comorbidades_confirmadas_media,comorbidades_confirmadas_mediana,comorbidades_avaliadas_media,quantidade_multimorbidade,percentual_multimorbidade
2019,43513,4.794015581550341,5.0,8.634132328269713,0.6506561257555213,0.0,4.938753935605451,6820,15.67347689196332
2020,979812,4.030769167962833,4.0,9.062353798483791,1.137412074969484,1.0,5.771504125281177,328202,33.49642584495801
2021,1480215,4.32198633306648,4.0,9.667717865310108,0.9781815479508045,1.0,4.845769026796783,418132,28.24805855906068
2022,475980,3.7105970839110887,4.0,9.457418378923483,0.9927139795789739,1.0,4.889522669019707,135639,28.49678557922602
2023,240704,3.994835981122042,4.0,9.974711679074714,0.7327422892847647,0.0,3.9753473145440044,47028,19.53768944429673
2024,229478,4.123950879822902,4.0,10.38484734920123,0.6940970376245218,0.0,3.9917203392046297,42437,18.492840272270108
2025,289913,4.193044120132591,4.0,10.934221645804087,0.6607568477439784,0.0,4.120194679093383,50429,17.394528703438617
2026,175521,4.279755698748298,4.0,11.056016089242883,0.6074714706502355,0.0,3.894890070134058,27357,15.586169176337874
```

### `outputs/tables/eda_02_dbscan_varredura_minima.csv`

- Git: `ignored` · `502 B` · modified `2026-10-17 00:40 UTC` · 3 rows

```csv
metodo,eps,min_samples,quantidade_registros,quantidade_clusters_sem_ruido,quantidade_ruido,percentual_ruido,silhouette_sem_ruido,calinski_harabasz_sem_ruido,davies_bouldin_sem_ruido,menor_cluster_percentual_sem_ruido,ari_dbscan_vs_kmeans,tempo_segundos
DBSCAN,1.401609,10,8000,1,220,2.75,,,,,0.0006927723173552484,1.9340924999996787
DBSCAN,1.479287,10,8000,1,100,1.25,,,,,2.9349417913744897e-05,1.8540164000005461
DBSCAN,1.656968,10,8000,1,54,0.675,,,,,-8.569456750579377e-06,2.1974824000008084
```

### `outputs/tables/eda_02_decisao_clustering.csv`

- Git: `ignored` · `706 B` · modified `2026-10-17 00:40 UTC` · 1 rows

```csv
status,matriz_principal_documentada,quantidade_clusters_documentada,usar_cluster_como_preditor_supervisionado,aplicar_clusters_na_coorte_completa,justificativa,encaminhamento,ari_nucleo_vs_ampliada_sem_ausencia
encerrar_como_exploratorio,nucleo,2,False,False,"A solução original foi dominada por indicadores de ausência. Sem esses indicadores, a concordância com a solução original foi baixa, o silhouette diminuiu e a composição dos grupos passou a acompanhar fortemente o período de internação.",Preservar o clustering como achado exploratório de qualidade e drift temporal. Prosseguir para a modelagem supervisionada com divisão temporal e avaliação por período.,0.9186733075232211
```

### `outputs/tables/eda_02_decisao_clustering.json`

- Git: `ignored` · `766 B` · modified `2026-10-17 00:40 UTC`

```json
{
  "status": "encerrar_como_exploratorio",
  "matriz_principal_documentada": "nucleo",
  "quantidade_clusters_documentada": 2,
  "usar_cluster_como_preditor_supervisionado": false,
  "aplicar_clusters_na_coorte_completa": false,
  "justificativa": "A solução original foi dominada por indicadores de ausência. Sem esses indicadores, a concordância com a solução original foi baixa, o silhouette diminuiu e a composição dos grupos passou a acompanhar fortemente o período de internação.",
  "encaminhamento": "Preservar o clustering como achado exploratório de qualidade e drift temporal. Prosseguir para a modelagem supervisionada com divisão temporal e avaliação por período.",
  "ari_nucleo_vs_ampliada_sem_ausencia": 0.9186733075232211
}
```

### `outputs/tables/eda_02_diagnostico_final_clustering.csv`

- Git: `ignored` · `534 B` · modified `2026-10-17 00:40 UTC` · 2 rows

```csv
matriz,silhouette_sem_indicadores_ausencia,ari_original_vs_sem_indicadores_ausencia,menor_cluster_percentual,nmi_cluster_ano,interpretacao
nucleo,0.23322749137878418,0.09417414798684123,49.71,0.06736268232984413,A partição mudou substancialmente após retirar os indicadores de ausência e permaneceu associada ao período.
ampliada,0.16932816803455353,0.08798891737376612,48.503750000000004,0.06904843374127206,A partição mudou substancialmente após retirar os indicadores de ausência e permaneceu associada ao período.
```

### `outputs/tables/eda_02_escolaridade_por_ano.csv`

- Git: `ignored` · `2.5 KB` · modified `2026-10-17 00:37 UTC` · 64 rows (first 60 shown)

```csv
ano_internacao,categoria_escolaridade,quantidade,percentual_ano,flag_ausente
2019,0,1804,4.145887435938685,False
2019,1,3999,9.190356904833038,False
2019,2,2207,5.0720474341001545,False
2019,3,3334,7.6620779996782575,False
2019,4,1489,3.42196584928642,False
2019,5,19192,44.1063590191437,False
2019,9,8264,18.992025371727987,False
2019,ausente,3224,7.409279985291752,True
2020,0,30829,3.146419925455087,False
2020,1,101136,10.321980134964667,False
2020,2,63870,6.518597445224186,False
2020,3,99791,10.18470890334064,False
2020,4,47085,4.805513710793499,False
2020,5,29043,2.9641400595216227,False
2020,9,334942,34.18431290900703,False
2020,ausente,273116,27.874326911693263,True
2021,0,42055,2.841141320686522,False
2021,1,136505,9.221971132571957,False
2021,2,95064,6.422310272494198,False
2021,3,160007,10.809713453788808,False
2021,4,67527,4.561972416169273,False
2021,5,40755,2.7533162412217145,False
2021,9,447177,30.21027350756478,False
2021,ausente,491125,33.17930165550275,True
2022,0,26567,5.581537039371402,False
2022,1,42951,9.02369847472583,False
2022,2,22096,4.642211857641077,False
2022,3,25812,5.422916929282743,False
2022,4,11178,2.3484180007563342,False
2022,5,42247,8.875793100550442,False
2022,9,134761,28.312324047228877,False
2022,ausente,170368,35.7931005504433,True
2023,0,17407,7.231703669236905,False
2023,1,19815,8.232102499335284,False
2023,2,7949,3.3023963041744215,False
2023,3,9170,3.8096583355490563,False
2023,4,3984,1.6551449082690775,False
2023,5,42260,17.55683328901888,False
2023,9,55948,23.243485775059824,False
2023,ausente,84171,34.968675219356555,True
2024,0,17084,7.444722369900382,False
2024,1,17266,7.524032804887614,False
2024,2,7909,3.446517748978115,False
2024,3,9419,4.104532896399655,False
2024,4,3620,1.5774932673284585,False
2024,5,36713,15.998483514759585,False
2024,9,51658,22.51109038774959,False
2024,ausente,85809,37.393127009996604,True
2025,0,26708,9.212418898083218,False
2025,1,24893,8.586369014152522,False
2025,2,10763,3.7124930582623064,False
2025,3,12764,4.402700120380942,False
2025,4,4270,1.4728556497983878,False
2025,5,49580,17.101682228806574,False
2025,9,60019,20.702417621838276,False
2025,ausente,100916,34.80906340867777,True
2026,0,18721,10.665960198494767,False
2026,1,16456,9.375516319984504,False
2026,2,7134,4.064470918009811,False
2026,3,7760,4.4211233983398,False
... [4 more rows omitted]
```

### `outputs/tables/eda_02_faixa_etaria_por_ano.csv`

- Git: `ignored` · `3.1 KB` · modified `2026-10-17 00:34 UTC` · 70 rows (first 60 shown)

```csv
ano_internacao,faixa_etaria,quantidade,percentual_ano
2019,1 a 4 anos,8211,18.870222692069035
2019,10 a 19 anos,1736,3.9896122997724817
2019,20 a 39 anos,4718,10.842736653413922
2019,40 a 59 anos,5323,12.233125732539701
2019,5 a 9 anos,2299,5.283478500677958
2019,60 a 79 anos,5611,12.894996897478913
2019,80 anos ou mais,2486,5.713235125135017
2019,Menor de 1 ano,13129,30.172592098912972
2020,1 a 4 anos,24466,2.4970096304188965
2020,10 a 19 anos,17292,1.7648283548272525
2020,20 a 39 anos,124732,12.7301972215078
2020,40 a 59 anos,273535,27.917090217306995
2020,5 a 9 anos,14382,1.4678326046221113
2020,60 a 79 anos,352938,36.02099178209697
2020,80 anos ou mais,153028,15.618098165770578
2020,Idade ausente ou inválida,4,0.00040824158103799506
2020,Menor de 1 ano,19435,1.9835437818683583
2021,1 a 4 anos,47421,3.203656225615873
2021,10 a 19 anos,19030,1.2856240478579126
2021,20 a 39 anos,213066,14.394260293268207
2021,40 a 59 anos,501489,33.879470212097566
2021,5 a 9 anos,17681,1.1944886384748161
2021,60 a 79 anos,474259,32.039872586077024
2021,80 anos ou mais,164098,11.086092223089214
2021,Idade ausente ou inválida,8,0.0005404620274757383
2021,Menor de 1 ano,43163,2.9159953114919115
2022,1 a 4 anos,57955,12.175931761838733
2022,10 a 19 anos,13032,2.7379301651329886
2022,20 a 39 anos,35546,7.4679608386907015
2022,40 a 59 anos,61612,12.944241354678768
2022,5 a 9 anos,22482,4.723307702004286
2022,60 a 79 anos,132755,27.890877767973443
2022,80 anos ou mais,98551,20.70486154880457
2022,Idade ausente ou inválida,4,0.0008403714441783268
2022,Menor de 1 ano,54043,11.35404848943233
2023,1 a 4 anos,46857,19.46664783302313
2023,10 a 19 anos,8903,3.6987337144376498
2023,20 a 39 anos,11807,4.905194762031375
2023,40 a 59 anos,19820,8.234179739431003
2023,5 a 9 anos,22260,9.247872906141984
2023,60 a 79 anos,41453,17.221566737569795
2023,80 anos ou mais,29699,12.338390720553043
2023,Idade ausente ou inválida,3,0.001246344057431534
2023,Menor de 1 ano,59902,24.88616724275459
2024,1 a 4 anos,44872,19.553944168939942
2024,10 a 19 anos,10067,4.3869129066838655
2024,20 a 39 anos,11831,5.155614045790882
2024,40 a 59 anos,18301,7.9750564324248945
2024,5 a 9 anos,21810,9.50417904984356
2024,60 a 79 anos,37044,16.142723921247352
2024,80 anos ou mais,25677,11.18930790751183
2024,Idade ausente ou inválida,4,0.0017430864832358658
2024,Menor de 1 ano,59872,26.090518481074437
2025,1 a 4 anos,58583,20.20709661174214
2025,10 a 19 anos,11765,4.058113985919913
2025,20 a 39 anos,13752,4.743492013121178
2025,40 a 59 anos,22988,7.929275334324435
2025,5 a 9 anos,24691,8.516692938916158
2025,60 a 79 anos,46556,16.058610686654273
2025,80 anos ou mais,30507,10.522812016018598
... [10 more rows omitted]
```

### `outputs/tables/eda_02_hca_dbscan_resumo_minimo.csv`

- Git: `ignored` · `627 B` · modified `2026-10-17 00:40 UTC` · 2 rows

```csv
metodo,matriz,quantidade_registros,quantidade_clusters,percentual_ruido,silhouette,calinski_harabasz,davies_bouldin,menor_cluster_percentual,ari_vs_kmeans,tempo_segundos,parametros,decisao
HCA_Ward,nucleo_sem_indicadores_ausencia,5000,2,0.0,0.2103562355041504,1400.8716617335656,1.7601060730978162,46.160000000000004,0.7842444162553112,0.5938283000014053,linkage=ward; k=2,nao aprofundar: comparacao minima registrada; K-Means permanece como referencia
DBSCAN,nucleo_sem_indicadores_ausencia,8000,0,100.0,,,,,,,eps=nan; min_samples=10,descartar: a varredura curta nao produziu ao menos dois clusters avaliaveis sem ruido
```

### `outputs/tables/eda_02_idade_por_ano.csv`

- Git: `ignored` · `951 B` · modified `2026-10-17 00:34 UTC` · 8 rows

```csv
ano_internacao,quantidade_registros,quantidade_idade_valida,quantidade_idade_ausente,percentual_idade_ausente,idade_media,idade_mediana,idade_q1,idade_q3,idade_iqr,idade_minima,idade_maxima
2019,43513,43513,0,0.0,24.590190265151314,5.0,0.6666666666666666,50.0,49.333333333333336,0.0,108.0
2020,979812,979808,4,0.00040824158103799506,56.897618532015855,60.0,43.0,74.0,31.0,0.0,120.0
2021,1480215,1480207,8,0.0005404620274757383,53.57439593341799,56.0,41.0,70.0,29.0,0.0,119.0
2022,475980,475976,4,0.0008403714441783268,47.423172459247304,58.0,5.0,77.0,72.0,0.0,118.0
2023,240704,240701,3,0.001246344057431534,30.035234843706462,7.0,1.0,66.0,65.0,0.0,117.0
2024,229478,229474,4,0.0017430864832358658,28.289975096127495,6.0,0.9166666666666666,63.0,62.083333333333336,0.0,114.0
2025,289913,289912,1,0.00034493106552655454,27.4152186671472,5.0,0.75,62.0,61.25,0.0,114.0
2026,175521,175521,0,0.0,23.672497067603732,3.0,0.75,53.0,52.25,0.0,115.0
```

### `outputs/tables/eda_02_obito_comorbidades.csv`

- Git: `ignored` · `3.8 KB` · modified `2026-10-17 00:39 UTC` · 13 rows

```csv
grupo_indicador,coluna,nome_amigavel,quantidade_sim,obito_sim,cura_sim,percentual_obito_sim,ic95_obito_sim_inferior,ic95_obito_sim_superior,quantidade_nao,obito_nao,cura_nao,percentual_obito_nao,ic95_obito_nao_inferior,ic95_obito_nao_superior,odds_ratio_bruta,ic95_or_inferior,ic95_or_superior,quantidade_ignorado,quantidade_ausente,quantidade_inesperado
comorbidades,renal,Doenca renal cronica,125182,51917,73265,41.47321499896151,41.2005588472639,41.746394457337765,1289010,353901,935109,27.45525635953173,27.378280190293392,27.532366902353246,1.872377795378616,1.8502458652196698,1.8947744591828404,27483,2473461,0
comorbidades,hepatica,Doenca hepatica cronica,29998,12365,17633,41.21941462764184,40.66355469091473,41.777523110157446,1355129,379894,975235,28.033788665138154,27.958226433065793,28.10947543451595,1.8001751319653052,1.7587276613304137,1.8425993842019206,29381,2500628,0
comorbidades,cardiopati,Doenca cardiovascular cronica,1016586,345365,671221,33.97302343333471,33.88101718317478,34.06515080799932,725961,174180,551781,23.99302441866712,23.894928460744936,24.09139560954837,1.62997612592386,1.6189749242326557,1.641052082595416,16720,2155869,0
comorbidades,diabetes,Diabetes mellitus,683122,240882,442240,35.26192978706585,35.148712441915045,35.37531288700555,946468,241584,704884,25.524793231255572,25.43705475998722,25.612730378268544,1.5892631441369018,1.5785224831538285,1.6000768872582307,19768,2265778,0
comorbidades,imunodepre,Imunodeficiencia ou imunodepressao,105976,36125,69851,34.087906695855665,33.8031057426785,34.37386118257916,1302135,362987,939148,27.876295468595806,27.799345590166553,27.953375881953008,1.3380680297360732,1.3204334697942015,1.355938101509065,29092,2477933,0
comorbidades,neurologic,Doenca neurologica cronica,173245,58699,114546,33.88207451874513,33.659558580962994,34.105305224331666,1257959,349335,908624,27.769982964468635,27.6917870337004,27.848314663468194,1.3328856078122973,1.3187173966146282,1.347206041320112,27545,2456387,0
comorbidades,obesidade,Obesidade,210819,70572,140247,33.4751611572012,33.27402351949005,33.676901001841095,1216471,336522,879949,27.663791409741783,27.584368664214367,27.743355224566464,1.3157788042059022,1.3028435656823645,1.328842469810072,37078,2450768,0
comorbidades,out_morbi,Outro fator de risco?,930468,291415,639053,31.319185614121064,31.22502614690555,31.41349932905479,724021,193059,530962,26.66483430729219,26.56309962011751,26.766816613258236,1.2541469106266776,1.2456397671636512,1.262712153944741,22195,2238452,0
comorbidades,pneumopati,Outra pneumopatia cronica,180160,57360,122800,31.838365896980463,31.623643259068736,32.0538630207042,1251179,350048,901131,27.977451667587133,27.898864310635158,28.056174254514676,1.2024612929770748,1.1897192454430583,1.215339809493989,28257,2455540,0
comorbidades,hematologi,Doenca hematologica cronica,32443,9228,23215,28.44373208396264,27.955393399448457,28.937174964250843,1357960,383281,974679,28.224763616012254,28.149123345222794,28.30052708400525,1.0108418547567384,0.9864685146717442,1.0358174033238718,29503,2495230,0
comorbidades,sind_down,Sindrome de Down,17905,3354,14551,18.732197710136834,18.167428827018078,19.310380523485115,1371001,388705,982296,28.35191221596483,28.276529304836938,28.427416439921465,0.5824953543455293,0.5609303923117962,0.6048893810794292,26612,2499618,0
comorbidades,puerpera,Puerpera ou parturiente,12999,1549,11450,11.916301253942612,11.370576906380899,12.484527907778842,1372975,391306,981669,28.50059178062237,28.425143672707904,28.576160194966686,0.3393864511980115,0.32180613790246815,0.3579271794116293,26610,2502552,0
comorbidades,asma,Asma,178130,20249,157881,11.367540560264976,11.220968923614333,11.515778415988475,1253709,374422,879287,29.865144144295048,29.785093678226275,29.945317999416037,0.30119170392217276,0.29667138629419587,0.30578089665035074,27092,2456205,0
```

### `outputs/tables/eda_02_obito_faixa_etaria.csv`

- Git: `ignored` · `925 B` · modified `2026-10-17 00:39 UTC` · 9 rows

```csv
faixa_etaria,quantidade_total,quantidade_obito_srag,quantidade_cura,percentual_obito_srag,ic95_inferior,ic95_superior
Menor de 1 ano,381952,6722,375230,1.7599070040214475,1.7186898574688039,1.8020944843699709
1 a 4 anos,330768,3621,327147,1.0947250036279204,1.0598278233794314,1.1307581185387119
5 a 9 anos,140432,1608,138824,1.1450381679389312,1.0907144950789642,1.202034581918472
10 a 19 anos,89775,3890,85885,4.333054859370649,4.201814484358208,4.46820323066315
20 a 39 anos,423572,48252,375320,11.391687835834286,11.296358968057598,11.487716990203355
40 a 59 anos,914523,193140,721383,21.11920640596245,21.035676023017103,21.202979415748857
60 a 79 anos,1114229,383573,730656,34.42497009142645,34.33680395589146,34.51324362073731
80 anos ou mais,519861,215377,304484,41.429728331227,41.29588641809588,41.56369690168545
Idade ausente ou inválida,24,2,22,8.333333333333332,2.315881529704331,25.84880219321068
```

### `outputs/tables/eda_02_obito_numero_comorbidades.csv`

- Git: `ignored` · `576 B` · modified `2026-10-17 00:39 UTC` · 4 rows

```csv
grupo_numero_comorbidades,quantidade_total,quantidade_obito_srag,quantidade_cura,percentual_obito_srag,ic95_inferior,ic95_superior
Nenhuma comorbidade confirmada,1751582,219109,1532473,12.509205963523259,12.460295749070244,12.558280622490543
Uma comorbidade confirmada,1107510,265687,841823,23.989580229523888,23.910142151445317,24.069198744094926
Duas comorbidades confirmadas,691829,228494,463335,33.02752558797044,32.91679582110583,33.13844383695857
Três ou mais comorbidades confirmadas,364215,142895,221320,39.23369438381176,39.075235384707156,39.39238048989145
```

### `outputs/tables/eda_02_obito_sintomas.csv`

- Git: `ignored` · `3.7 KB` · modified `2026-10-17 00:39 UTC` · 13 rows

```csv
grupo_indicador,coluna,nome_amigavel,quantidade_sim,obito_sim,cura_sim,percentual_obito_sim,ic95_obito_sim_inferior,ic95_obito_sim_superior,quantidade_nao,obito_nao,cura_nao,percentual_obito_nao,ic95_obito_nao_inferior,ic95_obito_nao_superior,odds_ratio_bruta,ic95_or_inferior,ic95_or_superior,quantidade_ignorado,quantidade_ausente,quantidade_inesperado
sintomas,saturacao,Saturacao de oxigenio abaixo de 95%?,2311260,618091,1693169,26.742599274854406,26.68557540452633,26.799700455566146,997117,122100,875017,12.245303209151984,12.181106556729752,12.309790765358352,2.616091550840492,2.5987301802775664,2.6335689077378626,40751,566008,0
sintomas,dispneia,Dispneia,2682695,663856,2018839,24.745861903794506,24.694258959301,24.79753717301567,783396,103596,679800,13.223963359526984,13.14913038338162,13.299157003680856,2.15779594309479,2.1425281296972924,2.1731725560560875,29898,419147,0
sintomas,desc_resp,Desconforto respiratorio,2300240,558432,1741808,24.2771189093312,24.22175374635577,24.332569987883655,975538,157151,818387,16.10916232888929,16.036346738063497,16.18224482832275,1.6695967437915027,1.65930637671044,1.6799509276915383,36991,602367,0
sintomas,fadiga,Fadiga,733292,172047,561245,23.462276964701648,23.36542491058367,23.559407060953433,1805281,340584,1464697,18.865982636498142,18.808977723628345,18.923120049284712,1.3183118912620826,1.3096880146702052,1.3269925533224372,68029,1308534,0
sintomas,perd_olft,Perda do olfato,191692,40851,150841,21.310748492373182,21.128007166515566,21.494639645764085,2216502,440257,1776245,19.862693559491486,19.81022269617673,19.91526888562289,1.092647025536152,1.0802411781379349,1.1051953457939327,101005,1405937,0
sintomas,perd_pala,Perda do paladar,194924,41196,153728,21.13439083950668,20.95372055679628,21.316198836030495,2209221,439090,1770131,19.875331621417686,19.82276184410635,19.928006161875704,1.0803237750515509,1.0681157471330678,1.0926713346135457,102337,1408654,0
sintomas,diarreia,Diarreia,421101,87025,334076,20.66606348595705,20.544035039760857,20.78862712005931,2406519,496955,1909564,20.650366774581876,20.599270221042307,20.701557027965464,1.0009581243967502,0.9928970695100992,1.0090846247438434,63752,1023764,0
sintomas,dor_abd,Dor abdominal,205578,39830,165748,19.37464125538725,19.204365153596036,19.54606187513443,2221677,443816,1777861,19.976621264027127,19.924098461698858,20.029247891865275,0.9626243828167531,0.9516927988623076,0.9736815320039038,76313,1411568,0
sintomas,garganta,Dor de garganta,569484,112121,457363,19.688173855630712,19.585102376764503,19.791654269063862,2265572,475699,1789873,20.996860836910063,20.943875531622535,21.0499444963226,0.9223928185049454,0.9157094761770133,0.9291249394748314,86054,994026,0
sintomas,outro_sin,Apresentou outros sintomas?,1201597,237211,964386,19.741310938692425,19.670236782777796,19.812578565689936,1604620,344431,1260189,21.464957435405267,21.40149872870601,21.52855276750935,0.8999479232313568,0.89468664579503,0.9052401400366705,80959,1027960,0
sintomas,febre,Febre,2209872,424633,1785239,19.215275816879892,19.163383305548958,19.267275355264598,1141670,271719,869951,23.800134890117107,23.72210629882234,23.878339793944008,0.7615390190878549,0.7573965060159404,0.7657041892679217,39528,524066,0
sintomas,vomito,Vomito,383652,61999,321653,16.160218114332782,16.04408329044029,16.277030598328764,2426912,514150,1912762,21.185358183568255,21.133994425310053,21.236813160696173,0.7170809306724982,0.7105627745484236,0.7236588793452112,65427,1039145,0
sintomas,tosse,Tosse,2790984,527269,2263715,18.89186752772499,18.845986424063263,18.93783426458662,711130,196769,514361,27.669905643131354,27.56604955915098,27.774002976038247,0.6088661684983051,0.6052252388657167,0.6125290013294685,31467,381555,0
```

### `outputs/tables/eda_02_perfis_binarios_clusters_sensibilidade.csv`

- Git: `ignored` · `11.9 KB` · modified `2026-10-17 00:40 UTC` · 104 rows (first 60 shown)

```csv
cluster_rotulo,quantidade_registros,quantidade_respostas_validas,quantidade_sim,quantidade_sem_resposta_valida,percentual_preenchido_valido,percentual_sem_resposta_valida,percentual_sim_entre_validos,variavel,grupo_clinico,matriz
Cluster 1,39768,36908,29142,2860,92.8082880708107,7.191711929189299,78.9584913839818,febre,sintoma,nucleo
Cluster 2,40232,34269,20549,5963,85.17846490355936,14.821535096440645,59.9638156934839,febre,sintoma,nucleo
Cluster 1,39768,37951,33681,1817,95.43099979883324,4.569000201166768,88.74864957445126,tosse,sintoma,nucleo
Cluster 2,40232,36123,28111,4109,89.78673692583018,10.213263074169815,77.82022534119535,tosse,sintoma,nucleo
Cluster 1,39768,30668,4557,9100,77.11728022530679,22.88271977469322,14.859136559280032,garganta,sintoma,nucleo
Cluster 2,40232,30154,5995,10078,74.95028832769934,25.049711672300656,19.881276115938185,garganta,sintoma,nucleo
Cluster 1,39768,35823,25837,3945,90.0799637899819,9.920036210018104,72.12405437847194,dispneia,sintoma,nucleo
Cluster 2,40232,36214,29157,4018,90.01292503479817,9.98707496520183,80.51306124703153,dispneia,sintoma,nucleo
Cluster 1,39768,35796,27887,3972,90.012070006035,9.987929993964997,77.90535255335791,desc_resp,sintoma,nucleo
Cluster 2,40232,34138,24040,6094,84.85285344999006,15.147146550009943,70.42005975745504,desc_resp,sintoma,nucleo
Cluster 1,39768,34322,20703,5446,86.30557231945282,13.694427680547175,60.319911427073016,saturacao,sintoma,nucleo
Cluster 2,40232,34696,25284,5536,86.23980910717836,13.760190892821633,72.87295365459995,saturacao,sintoma,nucleo
Cluster 1,39768,31696,3696,8072,79.70227318446993,20.297726815530073,11.66077738515901,diarreia,sintoma,nucleo
Cluster 2,40232,29881,3830,10351,74.27172400079539,25.728275999204612,12.8175094541682,diarreia,sintoma,nucleo
Cluster 1,39768,32032,6029,7736,80.54717360692014,19.452826393079864,18.821803196803195,vomito,sintoma,nucleo
Cluster 2,40232,29658,3155,10574,73.71743885464306,26.28256114535693,10.637939173241621,vomito,sintoma,nucleo
Cluster 1,39768,24025,1773,15743,60.41289478978072,39.58710521021927,7.379812695109261,dor_abd,sintoma,nucleo
Cluster 2,40232,23950,2056,16282,59.5297275800358,40.47027241996421,8.584551148225469,dor_abd,sintoma,nucleo
Cluster 1,39768,24558,4326,15210,61.75316837658419,38.24683162341581,17.615440996823846,fadiga,sintoma,nucleo
Cluster 2,40232,25134,8003,15098,62.47265858023464,37.52734141976536,31.841330468687833,fadiga,sintoma,nucleo
Cluster 1,39768,23322,438,16446,58.64514182257091,41.35485817742909,1.8780550553125805,perd_olft,sintoma,nucleo
Cluster 2,40232,23745,1539,16487,59.02018293895407,40.97981706104593,6.4813644977890075,perd_olft,sintoma,nucleo
Cluster 1,39768,23261,451,16507,58.491752162542745,41.508247837457255,1.9388676325179484,perd_pala,sintoma,nucleo
Cluster 2,40232,23709,1594,16523,58.93070192881289,41.06929807118711,6.723185288287148,perd_pala,sintoma,nucleo
Cluster 1,39768,30496,11406,9272,76.68477167571918,23.315228324280827,37.40162644281217,outro_sin,sintoma,nucleo
Cluster 2,40232,29307,11224,10925,72.84499900576655,27.155000994233447,38.29801753847204,outro_sin,sintoma,nucleo
Cluster 1,39768,7071,193,32697,17.78062764031382,82.21937235968618,2.7294583510111723,puerpera,comorbidade,nucleo
Cluster 2,40232,19471,99,20761,48.396798568303836,51.603201431696164,0.5084484618150069,puerpera,comorbidade,nucleo
Cluster 1,39768,7316,939,32452,18.3967008650171,81.6032991349829,12.834882449425915,cardiopati,comorbidade,nucleo
Cluster 2,40232,24100,14886,16132,59.90256512229072,40.09743487770929,61.76763485477178,cardiopati,comorbidade,nucleo
Cluster 1,39768,7135,293,32633,17.941561054113862,82.05843894588614,4.106517168885775,hematologi,comorbidade,nucleo
Cluster 2,40232,19547,430,20685,48.585702923046334,51.414297076953666,2.199826060265002,hematologi,comorbidade,nucleo
Cluster 1,39768,7144,440,32624,17.964192315429493,82.0358076845705,6.159014557670773,sind_down,comorbidade,nucleo
Cluster 2,40232,19561,120,20671,48.62050109365679,51.379498906343215,0.6134655692449261,sind_down,comorbidade,nucleo
Cluster 1,39768,7056,101,32712,17.742908871454436,82.25709112854557,1.43140589569161,hepatica,comorbidade,nucleo
Cluster 2,40232,19542,454,20690,48.573275004971165,51.42672499502883,2.323201309998977,hepatica,comorbidade,nucleo
Cluster 1,39768,7905,3070,31863,19.877791188895593,80.1222088111044,38.83617963314358,asma,comorbidade,nucleo
Cluster 2,40232,19786,1632,20446,49.17975740703917,50.82024259296083,8.248256342868695,asma,comorbidade,nucleo
Cluster 1,39768,7102,231,32666,17.858579762623215,82.14142023737678,3.252604900028161,diabetes,comorbidade,nucleo
Cluster 2,40232,22728,10072,17504,56.4923444024657,43.5076555975343,44.31538190777895,diabetes,comorbidade,nucleo
Cluster 1,39768,7376,1299,32392,18.547575940454635,81.45242405954536,17.611171366594363,neurologic,comorbidade,nucleo
Cluster 2,40232,20109,2481,20123,49.98260091469477,50.01739908530523,12.337759212293003,neurologic,comorbidade,nucleo
Cluster 1,39768,7192,628,32576,18.08489237577952,81.91510762422047,8.731924360400445,pneumopati,comorbidade,nucleo
Cluster 2,40232,20319,3532,19913,50.50457347385166,49.49542652614834,17.38274521383926,pneumopati,comorbidade,nucleo
Cluster 1,39768,7235,593,32533,18.193019513176424,81.80698048682358,8.19626814098134,imunodepre,comorbidade,nucleo
Cluster 2,40232,19814,1710,20418,49.24935374826009,50.75064625173991,8.630261431311194,imunodepre,comorbidade,nucleo
Cluster 1,39768,7085,231,32683,17.815831824582578,82.18416817541741,3.2604093154551874,renal,comorbidade,nucleo
Cluster 2,40232,19940,1995,20292,49.562537283754224,50.437462716245776,10.005015045135405,renal,comorbidade,nucleo
Cluster 1,39768,7081,302,32687,17.805773486220076,82.19422651377992,4.264934331309137,obesidade,comorbidade,nucleo
Cluster 2,40232,19749,2352,20483,49.087790813282965,50.912209186717035,11.909463770317483,obesidade,comorbidade,nucleo
Cluster 1,39768,7977,4209,31791,20.05884127942064,79.94115872057937,52.764197066566375,out_morbi,comorbidade,nucleo
Cluster 2,40232,22347,11961,17885,55.5453370451382,44.4546629548618,53.52396294804672,out_morbi,comorbidade,nucleo
Cluster 1,38803,36029,28467,2774,92.85106821637503,7.1489317836249775,79.01135196647145,febre,sintoma,ampliada
Cluster 2,41197,35148,21224,6049,85.31689200669952,14.683107993300485,60.38465915557073,febre,sintoma,ampliada
Cluster 1,38803,37047,32947,1756,95.47457670798649,4.525423292013504,88.93297702917916,tosse,sintoma,ampliada
Cluster 2,41197,37027,28845,4170,89.87790373085419,10.12209626914581,77.9026116077457,tosse,sintoma,ampliada
Cluster 1,38803,29876,4339,8927,76.99404685204753,23.00595314795248,14.52336323470344,garganta,sintoma,ampliada
Cluster 2,41197,30946,6213,10251,75.11712017865378,24.882879821346215,20.07690816260583,garganta,sintoma,ampliada
Cluster 1,38803,34957,25231,3846,90.08839522717315,9.911604772826843,72.17724633120692,dispneia,sintoma,ampliada
Cluster 2,41197,37080,29763,4117,90.00655387528218,9.99344612471782,80.26699029126215,dispneia,sintoma,ampliada
... [44 more rows omitted]
```

### `outputs/tables/eda_02_perfis_numericos_clusters_sensibilidade.csv`

- Git: `ignored` · `2.7 KB` · modified `2026-10-17 00:40 UTC` · 24 rows

```csv
cluster_rotulo,quantidade_registros,quantidade_preenchida,media,desvio_padrao,mediana,p25,p75,variavel,matriz,percentual_preenchido
Cluster 1,39768,39768,6.022081400321729,9.549172989351487,1.0,0.5,7.0,idade_anos,nucleo,100.0
Cluster 2,40232,40232,66.76455102074634,15.732651991662259,68.0,55.0,79.0,idade_anos,nucleo,100.0
Cluster 1,39768,39768,3.6171042043854356,6.647296654516078,3.0,1.0,5.0,dias_sintomas_ate_internacao,nucleo,100.0
Cluster 2,40232,40232,5.435871942732153,16.820979588570726,3.0,1.0,7.0,dias_sintomas_ate_internacao,nucleo,100.0
Cluster 1,39768,39768,4.272933011466506,1.568733410310557,4.0,3.0,5.0,n_sintomas_confirmados,nucleo,100.0
Cluster 2,40232,40232,4.089704712666534,1.8005303012481249,4.0,3.0,5.0,n_sintomas_confirmados,nucleo,100.0
Cluster 1,39768,39768,10.079913498290082,3.7710925482249964,13.0,8.0,13.0,n_sintomas_avaliados,nucleo,100.0
Cluster 2,40232,40232,9.71808510638298,4.154358443085973,12.0,6.0,13.0,n_sintomas_avaliados,nucleo,100.0
Cluster 1,39768,39768,0.31505230335948503,0.609884747980405,0.0,0.0,1.0,n_comorbidades_confirmadas,nucleo,100.0
Cluster 2,40232,40232,1.2856432690395705,1.1417558241865937,1.0,0.0,2.0,n_comorbidades_confirmadas,nucleo,100.0
Cluster 1,39768,39768,2.3806829611748137,4.892131997601032,0.0,0.0,1.0,n_comorbidades_avaliadas,nucleo,100.0
Cluster 2,40232,40232,6.636831378007556,6.085915870548763,3.0,0.0,13.0,n_comorbidades_avaliadas,nucleo,100.0
Cluster 1,38803,38803,5.3561915262907815,8.661931790309335,1.0,0.4166666666666667,6.0,idade_anos,ampliada,100.0
Cluster 2,41197,41197,65.96891157123092,16.378472831534076,67.0,54.0,79.0,idade_anos,ampliada,100.0
Cluster 1,38803,38803,3.60554596294101,6.710221531293958,3.0,1.0,5.0,dias_sintomas_ate_internacao,ampliada,100.0
Cluster 2,41197,41197,5.404155642401146,16.63122370472312,3.0,1.0,7.0,dias_sintomas_ate_internacao,ampliada,100.0
Cluster 1,38803,38803,4.278612478416617,1.5647207829835041,4.0,3.0,5.0,n_sintomas_confirmados,ampliada,100.0
Cluster 2,41197,41197,4.088647231594534,1.7984027252336405,4.0,3.0,5.0,n_sintomas_confirmados,ampliada,100.0
Cluster 1,38803,38803,10.094064891889802,3.7735999077423994,13.0,8.0,13.0,n_sintomas_avaliados,ampliada,100.0
Cluster 2,41197,41197,9.713231545986359,4.1428168305503945,12.0,6.0,13.0,n_sintomas_avaliados,ampliada,100.0
Cluster 1,38803,38803,0.30902249826044376,0.6031443309426237,0.0,0.0,0.0,n_comorbidades_confirmadas,ampliada,100.0
Cluster 2,41197,41197,1.2685875185086293,1.140263552310428,1.0,0.0,2.0,n_comorbidades_confirmadas,ampliada,100.0
Cluster 1,38803,38803,2.34311780017009,4.86277792885031,0.0,0.0,1.0,n_comorbidades_avaliadas,ampliada,100.0
Cluster 2,41197,41197,6.572517416316722,6.092517054557381,3.0,0.0,13.0,n_comorbidades_avaliadas,ampliada,100.0
```

### `outputs/tables/eda_02_perfis_sexo_clusters_sensibilidade.csv`

- Git: `ignored` · `696 B` · modified `2026-10-17 00:40 UTC` · 12 rows

```csv
matriz,cluster_rotulo,sexo_categoria,quantidade,percentual_cluster
nucleo,Cluster 1,Feminino,18070,45.43854355260511
nucleo,Cluster 1,Ignorado,8,0.020116676725005028
nucleo,Cluster 1,Masculino,21690,54.541339770669886
nucleo,Cluster 2,Feminino,20243,50.31566911910916
nucleo,Cluster 2,Ignorado,6,0.014913501690196859
nucleo,Cluster 2,Masculino,19983,49.66941737920064
ampliada,Cluster 1,Feminino,17634,45.44493982424039
ampliada,Cluster 1,Ignorado,8,0.020616962605984075
ampliada,Cluster 1,Masculino,21161,54.53444321315363
ampliada,Cluster 2,Feminino,20679,50.19540257785761
ampliada,Cluster 2,Ignorado,6,0.014564167293734982
ampliada,Cluster 2,Masculino,20512,49.79003325484865
```

### `outputs/tables/eda_02_preenchimento_por_variavel_ano.csv`

- Git: `ignored` · `88.1 KB` · modified `2026-10-17 00:34 UTC` · 704 rows (first 60 shown)

```csv
ano_internacao,coluna,nome_amigavel,grupo,uso_inicial_sugerido,quantidade_registros_ano,quantidade_preenchida,quantidade_ausente,percentual_preenchido,percentual_ausente
2019,asma,Asma,comorbidades_fatores_risco,modelo_a_nucleo,43513,16872,26641,38.774619079355595,61.225380920644405
2020,asma,Asma,comorbidades_fatores_risco,modelo_a_nucleo,979812,430685,549127,43.95588133233723,56.04411866766277
2021,asma,Asma,comorbidades_fatores_risco,modelo_a_nucleo,1480215,537556,942659,36.316075705218495,63.683924294781505
2022,asma,Asma,comorbidades_fatores_risco,modelo_a_nucleo,475980,176903,299077,37.16605739736964,62.83394260263036
2023,asma,Asma,comorbidades_fatores_risco,modelo_a_nucleo,240704,75522,165182,31.375465301781443,68.62453469821855
2024,asma,Asma,comorbidades_fatores_risco,modelo_a_nucleo,229478,72187,157291,31.457045991336862,68.54295400866314
2025,asma,Asma,comorbidades_fatores_risco,modelo_a_nucleo,289913,94756,195157,32.6842880450342,67.31571195496579
2026,asma,Asma,comorbidades_fatores_risco,modelo_a_nucleo,175521,54450,121071,31.021928999948724,68.97807100005127
2019,cardiopati,Doenca cardiovascular cronica,comorbidades_fatores_risco,modelo_a_nucleo,43513,17024,26489,39.1239399719624,60.8760600280376
2020,cardiopati,Doenca cardiovascular cronica,comorbidades_fatores_risco,modelo_a_nucleo,979812,531071,448741,54.20131617085726,45.79868382914274
2021,cardiopati,Doenca cardiovascular cronica,comorbidades_fatores_risco,modelo_a_nucleo,1480215,680836,799379,45.99575061730897,54.00424938269103
2022,cardiopati,Doenca cardiovascular cronica,comorbidades_fatores_risco,modelo_a_nucleo,475980,213639,262341,44.88402874070339,55.11597125929661
2023,cardiopati,Doenca cardiovascular cronica,comorbidades_fatores_risco,modelo_a_nucleo,240704,83074,157630,34.51292874235576,65.48707125764423
2024,cardiopati,Doenca cardiovascular cronica,comorbidades_fatores_risco,modelo_a_nucleo,229478,78482,150996,34.200228344329304,65.7997716556707
2025,cardiopati,Doenca cardiovascular cronica,comorbidades_fatores_risco,modelo_a_nucleo,289913,99022,190891,34.15576397057048,65.84423602942951
2026,cardiopati,Doenca cardiovascular cronica,comorbidades_fatores_risco,modelo_a_nucleo,175521,56119,119402,31.972812370029796,68.0271876299702
2019,diabetes,Diabetes mellitus,comorbidades_fatores_risco,modelo_a_nucleo,43513,16860,26653,38.747041114149795,61.252958885850205
2020,diabetes,Diabetes mellitus,comorbidades_fatores_risco,modelo_a_nucleo,979812,498051,481761,50.831281919388616,49.168718080611384
2021,diabetes,Diabetes mellitus,comorbidades_fatores_risco,modelo_a_nucleo,1480215,634279,845936,42.850464290660476,57.149535709339524
2022,diabetes,Diabetes mellitus,comorbidades_fatores_risco,modelo_a_nucleo,475980,198154,277826,41.630740787428046,58.369259212571954
2023,diabetes,Diabetes mellitus,comorbidades_fatores_risco,modelo_a_nucleo,240704,78223,162481,32.49759040148897,67.50240959851104
2024,diabetes,Diabetes mellitus,comorbidades_fatores_risco,modelo_a_nucleo,229478,74053,155425,32.270195835766394,67.7298041642336
2025,diabetes,Diabetes mellitus,comorbidades_fatores_risco,modelo_a_nucleo,289913,95570,194343,32.96506193237281,67.0349380676272
2026,diabetes,Diabetes mellitus,comorbidades_fatores_risco,modelo_a_nucleo,175521,54168,121353,30.861264464081223,69.13873553591878
2019,hematologi,Doenca hematologica cronica,comorbidades_fatores_risco,modelo_a_nucleo,43513,16689,26824,38.35405510996714,61.64594489003286
2020,hematologi,Doenca hematologica cronica,comorbidades_fatores_risco,modelo_a_nucleo,979812,423345,556467,43.2067580311325,56.7932419688675
2021,hematologi,Doenca hematologica cronica,comorbidades_fatores_risco,modelo_a_nucleo,1480215,526779,953436,35.58800579645525,64.41199420354475
2022,hematologi,Doenca hematologica cronica,comorbidades_fatores_risco,modelo_a_nucleo,475980,171192,304788,35.96621706794403,64.03378293205597
2023,hematologi,Doenca hematologica cronica,comorbidades_fatores_risco,modelo_a_nucleo,240704,71291,169413,29.617704732783835,70.38229526721616
2024,hematologi,Doenca hematologica cronica,comorbidades_fatores_risco,modelo_a_nucleo,229478,68669,160809,29.924001429330914,70.07599857066909
2025,hematologi,Doenca hematologica cronica,comorbidades_fatores_risco,modelo_a_nucleo,289913,90278,199635,31.139686733606286,68.86031326639372
2026,hematologi,Doenca hematologica cronica,comorbidades_fatores_risco,modelo_a_nucleo,175521,51663,123858,29.43408481036457,70.56591518963543
2019,hepatica,Doenca hepatica cronica,comorbidades_fatores_risco,modelo_a_nucleo,43513,16642,26871,38.24604141291108,61.75395858708892
2020,hepatica,Doenca hepatica cronica,comorbidades_fatores_risco,modelo_a_nucleo,979812,422299,557513,43.10000285769107,56.89999714230893
2021,hepatica,Doenca hepatica cronica,comorbidades_fatores_risco,modelo_a_nucleo,1480215,525073,955142,35.47275226909604,64.52724773090395
2022,hepatica,Doenca hepatica cronica,comorbidades_fatores_risco,modelo_a_nucleo,475980,170366,305614,35.79268036472121,64.2073196352788
2023,hepatica,Doenca hepatica cronica,comorbidades_fatores_risco,modelo_a_nucleo,240704,70804,169900,29.415381547460782,70.58461845253922
2024,hepatica,Doenca hepatica cronica,comorbidades_fatores_risco,modelo_a_nucleo,229478,68132,161346,29.6899920689565,70.3100079310435
2025,hepatica,Doenca hepatica cronica,comorbidades_fatores_risco,modelo_a_nucleo,289913,89761,200152,30.961357372729058,69.03864262727095
2026,hepatica,Doenca hepatica cronica,comorbidades_fatores_risco,modelo_a_nucleo,175521,51431,124090,29.30190689433173,70.69809310566828
2019,imunodepre,Imunodeficiencia ou imunodepressao,comorbidades_fatores_risco,modelo_a_nucleo,43513,16776,26737,38.55399535770919,61.44600464229081
2020,imunodepre,Imunodeficiencia ou imunodepressao,comorbidades_fatores_risco,modelo_a_nucleo,979812,427535,552277,43.634391087269805,56.365608912730195
2021,imunodepre,Imunodeficiencia ou imunodepressao,comorbidades_fatores_risco,modelo_a_nucleo,1480215,531702,948513,35.92059261661313,64.07940738338687
2022,imunodepre,Imunodeficiencia ou imunodepressao,comorbidades_fatores_risco,modelo_a_nucleo,475980,174411,301569,36.64250598764654,63.35749401235346
2023,imunodepre,Imunodeficiencia ou imunodepressao,comorbidades_fatores_risco,modelo_a_nucleo,240704,72992,167712,30.32438181334751,69.67561818665249
2024,imunodepre,Imunodeficiencia ou imunodepressao,comorbidades_fatores_risco,modelo_a_nucleo,229478,70023,159455,30.514036203906258,69.48596379609374
2025,imunodepre,Imunodeficiencia ou imunodepressao,comorbidades_fatores_risco,modelo_a_nucleo,289913,91557,198356,31.580853566414753,68.41914643358524
2026,imunodepre,Imunodeficiencia ou imunodepressao,comorbidades_fatores_risco,modelo_a_nucleo,175521,52207,123314,29.744019234165712,70.2559807658343
2019,morb_desc,Descricao de outro fator de risco,comorbidades_fatores_risco,exploracao_texto,43513,7726,35787,17.755613265001262,82.24438673499874
2020,morb_desc,Descricao de outro fator de risco,comorbidades_fatores_risco,exploracao_texto,979812,269076,710736,27.46200291484489,72.53799708515511
2021,morb_desc,Descricao de outro fator de risco,comorbidades_fatores_risco,exploracao_texto,1480215,364531,1115684,24.626895417219796,75.3731045827802
2022,morb_desc,Descricao de outro fator de risco,comorbidades_fatores_risco,exploracao_texto,475980,123215,352765,25.886591873608133,74.11340812639187
2023,morb_desc,Descricao de outro fator de risco,comorbidades_fatores_risco,exploracao_texto,240704,45139,195565,18.752908136134007,81.24709186386599
2024,morb_desc,Descricao de outro fator de risco,comorbidades_fatores_risco,exploracao_texto,229478,38647,190831,16.841265829404126,83.15873417059588
2025,morb_desc,Descricao de outro fator de risco,comorbidades_fatores_risco,exploracao_texto,289913,46401,243512,16.005146371497656,83.99485362850234
2026,morb_desc,Descricao de outro fator de risco,comorbidades_fatores_risco,exploracao_texto,175521,25148,150373,14.327630312042434,85.67236968795757
2019,neurologic,Doenca neurologica cronica,comorbidades_fatores_risco,modelo_a_nucleo,43513,16847,26666,38.717164985176844,61.282835014823156
2020,neurologic,Doenca neurologica cronica,comorbidades_fatores_risco,modelo_a_nucleo,979812,434358,545454,44.33074916412536,55.66925083587464
2021,neurologic,Doenca neurologica cronica,comorbidades_fatores_risco,modelo_a_nucleo,1480215,538341,941874,36.36910854166456,63.63089145833544
2022,neurologic,Doenca neurologica cronica,comorbidades_fatores_risco,modelo_a_nucleo,475980,179090,296890,37.62553048447414,62.37446951552586
... [644 more rows omitted]
```

### `outputs/tables/eda_02_resumo_analise_desfecho.csv`

- Git: `ignored` · `367 B` · modified `2026-10-17 00:39 UTC` · 10 rows

```csv
metrica,valor
origem_analise,coorte_sem_particao
quantidade_registros,3915136
quantidade_curas,3058951
quantidade_obitos_srag,856185
percentual_obito_srag,21.86858898388204
ic95_obito_inferior,21.8276718791117
ic95_obito_superior,21.90956129263557
quantidade_sintomas_analisados,13
quantidade_comorbidades_analisadas,13
quantidade_variaveis_ausencia,32
```

### `outputs/tables/eda_02_resumo_fonte.csv`

- Git: `ignored` · `237 B` · modified `2026-10-17 00:34 UTC` · 4 rows

```csv
metrica,valor
nome_coorte,coorte_desenvolvimento
caminho_coorte,<REPO>\data\analytical\coorte_provisoria_b.parquet
quantidade_linhas,3915136
quantidade_colunas,125
```

### `outputs/tables/eda_02_resumo_preenchimento_variaveis.csv`

- Git: `ignored` · `11.1 KB` · modified `2026-10-17 00:34 UTC` · 88 rows (first 60 shown)

```csv
coluna,nome_amigavel,grupo,uso_inicial_sugerido,quantidade_registros,quantidade_preenchida,quantidade_ausente,percentual_preenchido,percentual_ausente
tabag,Tabagismo,comorbidades_fatores_risco,indisponivel_se_100pct_vazio,3915136,0,3915136,0.0,100.0
out_trat,Outro tratamento para COVID-19,tratamentos,excluir_modelagem,3915136,2471,3912665,0.06311402720109852,99.9368859727989
dt_trt_cov,Data de inicio do tratamento para COVID-19,tratamentos,exploracao_eda,3915136,3344,3911792,0.08541210318109001,99.91458789681892
tipo_trat,Tipo de tratamento para COVID-19,tratamentos,exploracao_eda,3915136,4075,3911061,0.10408322980351128,99.8959167701965
out_anim,Especificacao do outro animal,exposicao_animal,exploracao_texto,3915136,4612,3910524,0.11779922843037892,99.88220077156961
dt_vac_mae,Data da vacinacao materna,vacinacao_influenza,modelo_c_sensibilidade,3915136,5194,3909942,0.13266461241703992,99.86733538758295
dt_2_dose,Data da segunda dose infantil,vacinacao_influenza,modelo_c_sensibilidade,3915136,8592,3906544,0.21945597802988198,99.78054402197012
cs_etinia,Etnia indigena,demografia_contexto_social,exploracao_subgrupo,3915136,8988,3906148,0.22957056919606367,99.77042943080393
tp_pov_ct,Povo ou comunidade tradicional,demografia_contexto_social,exploracao_subgrupo,3915136,9502,3905634,0.24269910419459248,99.75730089580541
dt_doseuni,Data da dose unica infantil,vacinacao_influenza,modelo_c_sensibilidade,3915136,14066,3901070,0.35927232157452516,99.64072767842548
out_antiv,Outro antiviral utilizado,tratamentos,excluir_modelagem,3915136,14561,3900575,0.3719155605322523,99.62808443946774
dt_1_dose,Data da primeira dose infantil,vacinacao_influenza,modelo_c_sensibilidade,3915136,14830,3900306,0.3787863307941282,99.62121366920587
dose_adic,Data da dose adicional,vacinacao_covid,modelo_c_sensibilidade,3915136,17594,3897542,0.44938413378232583,99.55061586621767
obes_imc,IMC registrado,comorbidades_fatores_risco,reavaliar_apos_eda,3915136,50513,3864623,1.290197837316507,98.70980216268349
pac_cocbo,Codigo da ocupacao,demografia_contexto_social,reavaliar_apos_modelo_principal,3915136,64480,3850656,1.6469415110994867,98.35305848890052
pac_dscbo,Descricao da ocupacao,demografia_contexto_social,apoio_interpretacao,3915136,64480,3850656,1.6469415110994867,98.35305848890052
m_amamenta,Mae amamenta a crianca?,vacinacao_influenza,modelo_c_sensibilidade,3915136,84061,3831075,2.147077393990911,97.85292260600909
dos_re_bi,Data do reforco bivalente,vacinacao_covid,modelo_c_sensibilidade,3915136,91356,3823780,2.33340553176186,97.66659446823815
mae_vac,Mae vacinada contra influenza?,vacinacao_influenza,modelo_c_sensibilidade,3915136,93116,3822020,2.3783592702782226,97.62164072972178
dose_2ref,Data da segunda dose de reforco,vacinacao_covid,modelo_c_sensibilidade,3915136,161245,3753891,4.11850316310851,95.88149683689149
dt_antivir,Data de inicio do antiviral,tratamentos,exploracao_eda,3915136,315448,3599688,8.057140288357798,91.9428597116422
tp_antivir,Tipo de antiviral utilizado,tratamentos,exploracao_eda,3915136,331007,3584129,8.454546661980581,91.54545333801941
dt_ut_dose,Data da ultima dose contra influenza,vacinacao_influenza,modelo_c_sensibilidade,3915136,336934,3578202,8.60593348481381,91.39406651518618
dose_ref,Data da dose de reforco,vacinacao_covid,modelo_c_sensibilidade,3915136,393149,3521987,10.04177121816458,89.95822878183542
dose_2_cov,Data da segunda dose contra COVID-19,vacinacao_covid,modelo_c_sensibilidade,3915136,847592,3067544,21.649107463955275,78.35089253604473
trat_cov,Recebeu tratamento antiviral para COVID-19?,tratamentos,exploracao_eda,3915136,865502,3049634,22.10656283715304,77.89343716284696
morb_desc,Descricao de outro fator de risco,comorbidades_fatores_risco,exploracao_texto,3915136,919883,2995253,23.49555673161801,76.50444326838199
dose_1_cov,Data da primeira dose contra COVID-19,vacinacao_covid,modelo_c_sensibilidade,3915136,1006619,2908517,25.710958699774416,74.28904130022559
outro_des,Descricao dos outros sintomas,sintomas,exploracao_texto,3915136,1183041,2732095,30.217111231895906,69.7828887681041
puerpera,Puerpera ou parturiente,comorbidades_fatores_risco,modelo_a_nucleo,3915136,1412584,2502552,36.08007486840815,63.91992513159185
hepatica,Doenca hepatica cronica,comorbidades_fatores_risco,modelo_a_nucleo,3915136,1414508,2500628,36.12921747801354,63.87078252198646
sind_down,Sindrome de Down,comorbidades_fatores_risco,modelo_a_nucleo,3915136,1415518,2499618,36.15501479386668,63.84498520613332
hematologi,Doenca hematologica cronica,comorbidades_fatores_risco,modelo_a_nucleo,3915136,1419906,2495230,36.267092637394974,63.732907362605026
imunodepre,Imunodeficiencia ou imunodepressao,comorbidades_fatores_risco,modelo_a_nucleo,3915136,1437203,2477933,36.70889082780266,63.29110917219734
renal,Doenca renal cronica,comorbidades_fatores_risco,modelo_a_nucleo,3915136,1441675,2473461,36.82311419066924,63.17688580933076
neurologic,Doenca neurologica cronica,comorbidades_fatores_risco,modelo_a_nucleo,3915136,1458749,2456387,37.25921653807173,62.74078346192827
asma,Asma,comorbidades_fatores_risco,modelo_a_nucleo,3915136,1458931,2456205,37.26386516330467,62.73613483669533
pneumopati,Outra pneumopatia cronica,comorbidades_fatores_risco,modelo_a_nucleo,3915136,1459596,2455540,37.28085052473273,62.71914947526727
obesidade,Obesidade,comorbidades_fatores_risco,modelo_a_nucleo,3915136,1464368,2450768,37.4027364566646,62.5972635433354
diabetes,Diabetes mellitus,comorbidades_fatores_risco,modelo_a_nucleo,3915136,1649358,2265778,42.12773196129074,57.87226803870926
out_morbi,Outro fator de risco?,comorbidades_fatores_risco,modelo_a_nucleo,3915136,1676684,2238452,42.82568983555105,57.17431016444895
cardiopati,Doenca cardiovascular cronica,comorbidades_fatores_risco,modelo_a_nucleo,3915136,1759267,2155869,44.935016305946974,55.064983694053026
estrang,Paciente estrangeiro?,demografia_contexto_social,modelo_b_ampliado,3915136,2459733,1455403,62.82624664890313,37.17375335109687
dor_abd,Dor abdominal,sintomas,modelo_a_nucleo,3915136,2503568,1411568,63.94587569882629,36.05412430117371
perd_pala,Perda do paladar,sintomas,modelo_a_nucleo,3915136,2506482,1408654,64.02030478634714,35.97969521365286
perd_olft,Perda do olfato,sintomas,modelo_a_nucleo,3915136,2509199,1405937,64.08970212018178,35.910297879818216
fadiga,Fadiga,sintomas,modelo_a_nucleo,3915136,2606602,1308534,66.57755950240298,33.42244049759702
cs_escol_n,Escolaridade,demografia_contexto_social,modelo_b_ampliado,3915136,2647598,1267538,67.62467510707162,32.375324892928376
vacina_cov,Recebeu vacina contra COVID-19?,vacinacao_covid,modelo_a_nucleo,3915136,2653969,1261167,67.78740253212149,32.21259746787851
vomito,Vomito,sintomas,modelo_a_nucleo,3915136,2875991,1039145,73.45826556216693,26.54173443783307
outro_sin,Apresentou outros sintomas?,sintomas,exploracao_texto,3915136,2887176,1027960,73.7439516788178,26.256048321182206
diarreia,Diarreia,sintomas,modelo_a_nucleo,3915136,2891372,1023764,73.85112547814431,26.14887452185569
garganta,Dor de garganta,sintomas,modelo_a_nucleo,3915136,2921110,994026,74.61069040768955,25.389309592310454
vacina,Recebeu vacina contra influenza?,vacinacao_influenza,modelo_a_nucleo,3915136,3002456,912680,76.68842155163958,23.31157844836042
pov_ct,Pertence a povo ou comunidade tradicional?,demografia_contexto_social,modelo_b_ampliado,3915136,3018493,896643,77.09803695197306,22.901963048026943
co_rg_inte,Regional de saude de internacao,geografia_internacao,exploracao_eda,3915136,3263378,651758,83.3528643704842,16.6471356295158
desc_resp,Desconforto respiratorio,sintomas,modelo_b_ampliado,3915136,3312769,602367,84.61440419949652,15.38559580050348
saturacao,Saturacao de oxigenio abaixo de 95%?,sintomas,modelo_a_nucleo,3915136,3349128,566008,85.54308202831268,14.456917971687318
ave_suino,"Contato direto com aves, suinos ou outro animal?",exposicao_animal,modelo_a_nucleo,3915136,3352831,562305,85.63766367247524,14.362336327524758
antiviral,Usou antiviral contra influenza?,tratamentos,exploracao_eda,3915136,3379034,536102,86.30693799653447,13.693062003465528
... [28 more rows omitted]
```

### `outputs/tables/eda_02_resumo_rupturas_temporais.csv`

- Git: `ignored` · `771 B` · modified `2026-10-17 00:37 UTC` · 9 rows

```csv
tipo_indicador,grupo_indicador,quantidade_indicadores,quantidade_destaques,maior_amplitude,amplitude_mediana,percentual_indicadores_destacados
qualidade_dados,preenchimento,88,22,98.62178747183194,11.185375960892992,25.0
clinico,sintomas,13,9,28.726919171929584,12.003363973507568,69.23076923076923
clinico,comorbidades,13,5,34.62749907042388,7.509387634535367,38.46153846153847
territorio,uf_residencia,10,3,8.528311660459739,2.794892732490122,30.0
contexto,vacinacao,2,2,45.48807599371179,29.001747326609213,100.0
demografia,idade,1,1,55.0,55.0,100.0
composicao,volume,1,1,38.41844681872332,38.41844681872332,100.0
qualidade_dados,escolaridade,1,1,29.98384702470485,29.98384702470485,100.0
desfecho,desfecho,1,1,20.869390760490116,20.869390760490116,100.0
```

### `outputs/tables/eda_02_resumo_temporal.csv`

- Git: `ignored` · `836 B` · modified `2026-10-17 00:34 UTC` · 8 rows

```csv
ano_internacao,quantidade_registros,percentual_coorte,quantidade_cura,quantidade_obito_srag,percentual_cura,percentual_obito_srag,periodo_completo
2019,43513,1.1114045591264263,38292,5221,88.0012869717096,11.998713028290396,True
2020,979812,25.026257069997058,705699,274113,72.02391887423302,27.97608112576698,True
2021,1480215,37.807498896590054,1062924,417291,71.80875751157771,28.19124248842229,True
2022,475980,12.157432078987805,389547,86433,81.84104374133368,18.158956258666333,True
2023,240704,6.148036747637885,217667,23037,90.42932398298325,9.570676017016751,True
2024,229478,5.861303413214764,210358,19120,91.66804661013256,8.331953389867438,True
2025,289913,7.404927951417268,268686,21227,92.67814827206783,7.321851727932173,True
2026,175521,4.483139283028738,165778,9743,94.44909725901745,5.55090274098256,False
```

### `outputs/tables/eda_02_resumo_uf_residencia.csv`

- Git: `ignored` · `981 B` · modified `2026-10-17 00:37 UTC` · 28 rows

```csv
uf_residencia_categoria,quantidade,percentual_coorte,ordem_frequencia
SP,1158797,29.597873483833,1
MG,472256,12.062314054990681,2
PR,336568,8.596585150554157,3
RJ,300618,7.678353957563671,4
RS,235248,6.008680158237159,5
SC,166751,4.259136847353451,6
BA,142962,3.6515206623729037,7
GO,142693,3.644649892111027,8
CE,129855,3.3167430199104198,9
PE,101230,2.5856062215974105,10
DF,100575,2.568876279138196,11
MS,89937,2.2971615800830416,12
PA,84009,2.145749215352928,13
AM,63253,1.6156016036224539,14
PB,59052,1.5083000948115213,15
MT,50033,1.2779377268120444,16
MA,39880,1.0186108477457743,17
RN,34468,0.8803781018079576,18
ES,33443,0.854197657501553,19
AL,33202,0.8480420603524373,20
PI,32473,0.8294220175237846,21
SE,28293,0.722656888547422,22
RO,20888,0.5335191421192009,23
AC,17061,0.43577030274299544,24
TO,16084,0.4108158694870369,25
AP,15117,0.38611685519992156,26
RR,9633,0.24604509268643543,27
Ausente ou inesperada,757,0.01933521594141302,28
```

### `outputs/tables/eda_02_rupturas_temporais.csv`

- Git: `ignored` · `21.6 KB` · modified `2026-10-17 00:37 UTC` · 130 rows (first 60 shown)

```csv
tipo_indicador,grupo_indicador,indicador,unidade,periodo_avaliado,ano_minimo,valor_minimo,ano_maximo,valor_maximo,amplitude,limite_destaque,flag_destaque,ordem_destaque,quantidade_anos
demografia,idade,Idade mediana,anos,2019-2025,2019,5.0,2020,60.0,55.0,5.0,True,11.0,7
composicao,volume,Participação no volume do período,pontos_percentuais,2019-2025,2019,1.1635689770203617,2021,39.58201579574368,38.41844681872332,5.0,True,7.683689363744664,7
qualidade_dados,preenchimento,Recebeu vacina contra COVID-19?,pontos_percentuais,2019-2025,2019,1.3720037689885782,2025,99.99379124082051,98.62178747183194,20.0,True,4.931089373591597,7
qualidade_dados,preenchimento,Pertence a povo ou comunidade tradicional?,pontos_percentuais,2019-2025,2019,1.7787787557741366,2023,100.0,98.22122124422586,20.0,True,4.911061062211293,7
qualidade_dados,preenchimento,Paciente estrangeiro?,pontos_percentuais,2019-2025,2019,0.48950888240296003,2025,95.36240182399548,94.87289294159253,20.0,True,4.743644647079626,7
contexto,vacinacao,Recebeu vacina contra COVID-19?,pontos_percentuais,2019-2025,2019,16.272189349112427,2022,61.76026534282422,45.48807599371179,10.0,True,4.5488075993711785,7
desfecho,desfecho,Óbito por SRAG,pontos_percentuais,2019-2025,2025,7.321851727932173,2021,28.19124248842229,20.869390760490116,5.0,True,4.173878152098023,7
qualidade_dados,preenchimento,Fadiga,pontos_percentuais,2019-2025,2019,0.5538574678831614,2025,82.60202198590612,82.04816451802296,20.0,True,4.102408225901148,7
qualidade_dados,preenchimento,Recebeu tratamento antiviral para COVID-19?,pontos_percentuais,2019-2025,2019,0.2091329028106543,2025,82.23191095259612,82.02277804978547,20.0,True,4.101138902489273,7
qualidade_dados,preenchimento,Dor abdominal,pontos_percentuais,2019-2025,2019,0.30105945349665614,2025,81.07708174521322,80.77602229171656,20.0,True,4.038801114585828,7
qualidade_dados,preenchimento,Perda do olfato,pontos_percentuais,2019-2025,2019,0.2964631259623561,2025,80.48069593291781,80.18423280695545,20.0,True,4.009211640347773,7
qualidade_dados,preenchimento,Perda do paladar,pontos_percentuais,2019-2025,2019,0.2964631259623561,2025,80.35997005998351,80.06350693402115,20.0,True,4.003175346701058,7
clinico,comorbidades,Doenca cardiovascular cronica,pontos_percentuais,2019-2025,2019,27.915404265431,2021,62.54290333585488,34.62749907042388,10.0,True,3.462749907042388,7
qualidade_dados,preenchimento,Data de inicio do antiviral,pontos_percentuais,2019-2025,2021,2.0252463324584604,2019,62.15154091880587,60.12629458634741,20.0,True,3.0063147293173706,7
qualidade_dados,preenchimento,Tipo de antiviral utilizado,pontos_percentuais,2019-2025,2021,2.3266890282830537,2019,62.15383908257303,59.82715005428997,20.0,True,2.9913575027144987,7
clinico,sintomas,Fadiga,pontos_percentuais,2019-2025,2024,21.273080828070416,2019,50.0,28.726919171929584,10.0,True,2.8726919171929586,7
qualidade_dados,preenchimento,Data da primeira dose contra COVID-19,pontos_percentuais,2019-2025,2019,0.11490818835750236,2022,56.78389848312955,56.668990294772044,20.0,True,2.8334495147386023,7
clinico,sintomas,Febre,pontos_percentuais,2019-2025,2022,61.38461498738701,2019,88.72229163774354,27.337676650356528,10.0,True,2.7337676650356526,7
clinico,comorbidades,Diabetes mellitus,pontos_percentuais,2019-2025,2019,19.539264502969584,2020,46.38605355415614,26.84678905118656,10.0,True,2.684678905118656,7
qualidade_dados,preenchimento,Data da segunda dose contra COVID-19,pontos_percentuais,2019-2025,2019,0.0827338956174017,2022,53.10307155762847,53.020337662011066,20.0,True,2.6510168831005534,7
clinico,sintomas,Desconforto respiratorio,pontos_percentuais,2019-2025,2022,63.90864654416326,2019,85.05905099117147,21.150404447008214,10.0,True,2.1150404447008215,7
clinico,sintomas,Apresentou outros sintomas?,pontos_percentuais,2019-2025,2019,25.14156579562575,2021,46.095983867734105,20.954418072108357,10.0,True,2.0954418072108356,7
qualidade_dados,preenchimento,Recebeu vacina contra influenza?,pontos_percentuais,2019-2025,2023,56.22216498271736,2025,94.20515809915389,37.98299311643653,20.0,True,1.8991496558218266,7
clinico,comorbidades,Obesidade,pontos_percentuais,2019-2025,2019,4.106889969829444,2021,22.575467273580003,18.468577303750557,10.0,True,1.8468577303750557,7
qualidade_dados,preenchimento,Data de inclusao do registro no sistema,pontos_percentuais,2019-2025,2019,64.15324155999357,2020,100.0,35.846758440006425,20.0,True,1.7923379220003213,7
clinico,sintomas,Tosse,pontos_percentuais,2019-2025,2020,76.0662108853592,2019,93.37900071740992,17.312789832050726,10.0,True,1.7312789832050726,7
territorio,uf_residencia,UF PR,pontos_percentuais,2019-2025,2020,6.5361518332088195,2019,15.064463493668558,8.528311660459739,5.0,True,1.7056623320919477,7
territorio,uf_residencia,UF SP,pontos_percentuais,2019-2025,2025,24.39007564338267,2020,32.0495156213641,7.659439977981432,5.0,True,1.5318879955962863,7
qualidade_dados,escolaridade,Preenchimento da escolaridade,pontos_percentuais,2019-2025,2024,62.6068729900034,2019,92.59072001470825,29.98384702470485,20.0,True,1.4991923512352425,7
qualidade_dados,preenchimento,Escolaridade,pontos_percentuais,2019-2025,2024,62.6068729900034,2019,92.59072001470825,29.98384702470485,20.0,True,1.4991923512352425,7
clinico,sintomas,Saturacao de oxigenio abaixo de 95%?,pontos_percentuais,2019-2025,2025,62.097120924306026,2021,76.99078255707443,14.8936616327684,10.0,True,1.48936616327684,7
qualidade_dados,preenchimento,Data da dose de reforco,pontos_percentuais,2019-2025,2019,0.027577965205800567,2023,29.40582624302047,29.37824827781467,20.0,True,1.4689124138907335,7
qualidade_dados,preenchimento,Diarreia,pontos_percentuais,2019-2025,2022,68.48859195764528,2019,97.6030151908625,29.11442323321721,20.0,True,1.4557211616608605,7
qualidade_dados,preenchimento,Vomito,pontos_percentuais,2019-2025,2022,69.08630614731712,2019,97.6857490864799,28.599442939162785,20.0,True,1.4299721469581392,7
clinico,comorbidades,Asma,pontos_percentuais,2019-2025,2021,8.789636027143738,2023,22.66830716559232,13.878671138448583,10.0,True,1.3878671138448584,7
qualidade_dados,preenchimento,Dor de garganta,pontos_percentuais,2019-2025,2022,70.38425984285054,2019,98.03736814285386,27.653108300003325,20.0,True,1.3826554150001662,7
clinico,comorbidades,Outro fator de risco?,pontos_percentuais,2019-2025,2019,47.286821705426355,2022,59.968219573853375,12.68139786842702,10.0,True,1.268139786842702,7
contexto,vacinacao,Recebeu vacina contra influenza?,pontos_percentuais,2019-2025,2021,19.93422802020895,2020,32.449646679715585,12.515418659506636,10.0,True,1.2515418659506636,7
clinico,sintomas,Perda do olfato,pontos_percentuais,2019-2025,2019,0.7936507936507936,2021,12.797014767158363,12.003363973507568,10.0,True,1.2003363973507568,7
qualidade_dados,preenchimento,Data da ultima dose contra influenza,pontos_percentuais,2019-2025,2022,3.615067859994117,2025,27.031557743185026,23.41648988319091,20.0,True,1.1708244941595454,7
clinico,sintomas,Perda do paladar,pontos_percentuais,2019-2025,2019,1.574803149606299,2021,13.049298893290151,11.474495743683853,10.0,True,1.1474495743683852,7
qualidade_dados,preenchimento,Apresentou outros sintomas?,pontos_percentuais,2019-2025,2022,70.30106306987689,2019,92.6114034886126,22.310340418735706,20.0,True,1.1155170209367853,7
clinico,sintomas,Dispneia,pontos_percentuais,2019-2025,2022,72.57666416413274,2019,83.65496396186933,11.078299797736591,10.0,True,1.107829979773659,7
territorio,uf_residencia,UF MG,pontos_percentuais,2019-2025,2019,8.443453680509274,2022,13.733980419345352,5.290526738836078,5.0,True,1.0581053477672158,7
qualidade_dados,preenchimento,Doenca cardiovascular cronica,pontos_percentuais,2019-2025,2025,34.15576397057048,2020,54.20131617085726,20.045552200286778,20.0,True,1.002277610014339,7
qualidade_dados,preenchimento,Desconforto respiratorio,pontos_percentuais,2019-2025,2022,79.49241564771629,2019,99.28067474088203,19.78825909316575,20.0,False,0.9894129546582875,7
clinico,sintomas,Dor de garganta,pontos_percentuais,2019-2025,2025,13.37345688380503,2021,23.249005879339368,9.875548995534338,10.0,False,0.9875548995534338,7
qualidade_dados,preenchimento,Diabetes mellitus,pontos_percentuais,2019-2025,2024,32.270195835766394,2020,50.831281919388616,18.56108608362222,20.0,False,0.9280543041811111,7
clinico,comorbidades,Outra pneumopatia cronica,pontos_percentuais,2019-2025,2021,9.063950734249172,2019,18.11307166006482,9.049120925815647,10.0,False,0.9049120925815647,7
qualidade_dados,preenchimento,Saturacao de oxigenio abaixo de 95%?,pontos_percentuais,2019-2025,2022,80.70612210597083,2019,98.51998253395537,17.813860427984537,20.0,False,0.8906930213992268,7
qualidade_dados,preenchimento,Febre,pontos_percentuais,2019-2025,2022,82.36984747258288,2019,99.724220347942,17.354372875359118,20.0,False,0.8677186437679559,7
clinico,sintomas,Diarreia,pontos_percentuais,2019-2025,2019,9.454563139848746,2021,18.105316101164206,8.65075296131546,10.0,False,0.865075296131546,7
qualidade_dados,preenchimento,Data da segunda dose de reforco,pontos_percentuais,2019-2025,2019,0.011490818835750236,2023,17.06826641850572,17.05677559966997,20.0,False,0.8528387799834984,7
qualidade_dados,preenchimento,Outro fator de risco?,pontos_percentuais,2019-2025,2025,33.337932414207025,2020,50.27178683257605,16.933854418369023,20.0,False,0.8466927209184512,7
territorio,uf_residencia,UF RJ,pontos_percentuais,2019-2025,2019,5.076643761634454,2020,9.302396786322275,4.225753024687821,5.0,False,0.8451506049375641,7
qualidade_dados,preenchimento,Usou antiviral contra influenza?,pontos_percentuais,2019-2025,2024,83.16875691787448,2019,99.17725737136028,16.00850045348581,20.0,False,0.8004250226742904,7
clinico,comorbidades,Doenca neurologica cronica,pontos_percentuais,2019-2025,2021,9.278784682568892,2022,16.78817231710426,7.509387634535367,10.0,False,0.7509387634535367,7
qualidade_dados,preenchimento,Dispneia,pontos_percentuais,2019-2025,2022,84.4730871045002,2019,99.34042699882794,14.867339894327742,20.0,False,0.7433669947163871,7
qualidade_dados,preenchimento,Obesidade,pontos_percentuais,2019-2025,2023,29.39170101036958,2020,44.106930717321276,14.715229706951696,20.0,False,0.7357614853475848,7
clinico,sintomas,Dor abdominal,pontos_percentuais,2019-2025,2019,2.2900763358778624,2021,9.448363736797415,7.158287400919552,10.0,False,0.7158287400919552,7
... [70 more rows omitted]
```

### `outputs/tables/eda_02_sexo_por_ano.csv`

- Git: `ignored` · `1014 B` · modified `2026-10-17 00:34 UTC` · 24 rows

```csv
ano_internacao,sexo_categoria,quantidade,percentual_ano
2019,Feminino,21171,48.65442511433365
2019,Ignorado,12,0.027577965205800567
2019,Masculino,22330,51.31799692046055
2020,Feminino,446843,45.60497319894021
2020,Ignorado,221,0.022555347352349226
2020,Masculino,532748,54.37247145370745
2021,Feminino,670315,45.28497549342494
2021,Ignorado,175,0.011822606851031776
2021,Masculino,809725,54.70320189972403
2022,Feminino,235553,49.488003697634355
2022,Ignorado,52,0.01092482877431825
2022,Masculino,240375,50.50107147359133
2023,Feminino,116318,48.32408269077373
2023,Ignorado,14,0.005816272268013826
2023,Masculino,124372,51.67010103695826
2024,Feminino,111138,48.43078639346691
2024,Ignorado,35,0.015252006728313824
2024,Masculino,118305,51.55396159980478
2025,Feminino,140063,48.3120798308458
2025,Ignorado,33,0.0113827251623763
2025,Masculino,149817,51.67653744399182
2026,Feminino,83546,47.5988628141362
2026,Ignorado,11,0.006267056363626005
2026,Masculino,91964,52.39487012950017
```

### `outputs/tables/eda_02_sintomas_por_ano.csv`

- Git: `ignored` · `13.8 KB` · modified `2026-10-17 00:37 UTC` · 104 rows (first 60 shown)

```csv
ano_internacao,grupo_clinico,coluna,nome_amigavel,quantidade_total,quantidade_sim,quantidade_nao,quantidade_ignorado,quantidade_ausente,quantidade_inesperado,quantidade_respostas_validas,percentual_sim_validos,percentual_nao_validos,percentual_sem_resposta_valida
2019,sintomas,desc_resp,Desconforto respiratorio,43513,36515,6414,271,313,0,42929,85.05905099117147,14.94094900882853,1.3421276400156275
2020,sintomas,desc_resp,Desconforto respiratorio,979812,560899,264215,13473,141225,0,825114,67.97836420179515,32.021635798204855,15.78853902585394
2021,sintomas,desc_resp,Desconforto respiratorio,1480215,832352,367371,15770,264722,0,1199723,69.37868157899781,30.62131842100218,18.949409376340597
2022,sintomas,desc_resp,Desconforto respiratorio,475980,239003,134973,4392,97612,0,373976,63.90864654416326,36.09135345583674,21.430312197991512
2023,sintomas,desc_resp,Desconforto respiratorio,240704,149928,53657,1115,36004,0,203585,73.64393250976251,26.356067490237496,15.421015022600374
2024,sintomas,desc_resp,Desconforto respiratorio,229478,152371,49920,666,26521,0,202291,75.32267871531604,24.677321284683945,11.847323054933371
2025,sintomas,desc_resp,Desconforto respiratorio,289913,202424,63374,697,23418,0,265798,76.15708169361696,23.842918306383044,8.318012645172862
2026,sintomas,desc_resp,Desconforto respiratorio,175521,126748,35614,607,12552,0,162362,78.06506448553233,21.93493551446767,7.497108608086782
2019,sintomas,diarreia,Diarreia,43513,3888,37235,1347,1043,0,41123,9.454563139848746,90.54543686015126,5.492611403488612
2020,sintomas,diarreia,Diarreia,979812,121536,604896,23746,229634,0,726432,16.730540504823576,83.26945949517642,25.8600629508518
2021,sintomas,diarreia,Diarreia,1480215,183587,830408,25609,440611,0,1013995,18.105316101164206,81.8946838988358,31.496775806217343
2022,sintomas,diarreia,Diarreia,475980,36619,283078,6295,149988,0,319697,11.454283274475518,88.54571672552449,32.83394260263036
2023,sintomas,diarreia,Diarreia,240704,18748,154161,1979,65816,0,172909,10.842697603941957,89.15730239605804,28.165298457856952
2024,sintomas,diarreia,Diarreia,229478,19455,154134,1596,54293,0,173589,11.207507388140954,88.79249261185905,24.354840115392324
2025,sintomas,diarreia,Diarreia,289913,23038,212264,1824,52787,0,235302,9.79082200746275,90.20917799253725,18.83703041947067
2026,sintomas,diarreia,Diarreia,175521,14230,130343,1356,29592,0,144573,9.842778388772453,90.15722161122754,17.632078212863416
2019,sintomas,dispneia,Dispneia,43513,35980,7030,216,287,0,43010,83.65496396186933,16.345036038130665,1.1559763748764738
2020,sintomas,dispneia,Dispneia,979812,680930,195967,10373,92542,0,876897,77.65222141254903,22.34777858745098,10.503545578131316
2021,sintomas,dispneia,Dispneia,1480215,1052319,252173,11597,164126,0,1304492,80.66887340052679,19.331126599473205,11.871451106764894
2022,sintomas,dispneia,Dispneia,475980,289046,109217,3812,73905,0,398263,72.57666416413274,27.423335835867253,16.327786881801757
2023,sintomas,dispneia,Dispneia,240704,157205,52397,1313,29789,0,209602,75.00166983139474,24.99833016860526,12.921264291411857
2024,sintomas,dispneia,Dispneia,229478,151730,52362,921,24465,0,204092,74.3439233286949,25.6560766713051,11.06249836585642
2025,sintomas,dispneia,Dispneia,289913,196590,70639,1063,21621,0,267229,73.56611744982767,26.43388255017232,7.824416290404362
2026,sintomas,dispneia,Dispneia,175521,118895,43611,603,12412,0,162506,73.16345242637195,26.83654757362805,7.41506714296295
2019,sintomas,dor_abd,Dor abdominal,43513,3,128,0,43382,0,131,2.2900763358778624,97.70992366412213,99.69894054650335
2020,sintomas,dor_abd,Dor abdominal,979812,33816,395535,20002,530459,0,429351,7.876073422444573,92.12392657755542,56.18026723493895
2021,sintomas,dor_abd,Dor abdominal,1480215,92023,881934,32085,474173,0,973957,9.448363736797415,90.55163626320258,34.20165313822654
2022,sintomas,dor_abd,Dor abdominal,475980,27852,285864,8339,153925,0,313716,8.87809356233026,91.12190643766974,34.09050800453801
2023,sintomas,dor_abd,Dor abdominal,240704,13607,154986,4379,67732,0,168593,8.070916348840106,91.9290836511599,29.958372108481786
2024,sintomas,dor_abd,Dor abdominal,229478,13416,156312,3433,56317,0,169728,7.904411764705882,92.09558823529412,26.037354343335746
2025,sintomas,dor_abd,Dor abdominal,289913,15891,214408,4754,54860,0,230299,6.900160226488174,93.09983977351183,20.562720540300024
2026,sintomas,dor_abd,Dor abdominal,175521,8970,132510,3321,30720,0,141480,6.340118744698897,93.6598812553011,19.39426051583571
2019,sintomas,fadiga,Fadiga,43513,120,120,1,43272,0,240,50.0,50.0,99.44844069588399
2020,sintomas,fadiga,Fadiga,979812,110891,330823,19316,518782,0,441714,25.10470575983555,74.89529424016445,54.918494568345764
2021,sintomas,fadiga,Fadiga,1480215,378505,662761,28740,410209,0,1041266,36.35046184164277,63.64953815835723,29.65440831230598
2022,sintomas,fadiga,Fadiga,475980,85051,241474,7177,142278,0,326525,26.047316438251283,73.95268356174873,31.39942854741796
2023,sintomas,fadiga,Fadiga,240704,38447,135984,3374,62899,0,174431,22.04138025924291,77.95861974075709,27.53298657272002
2024,sintomas,fadiga,Fadiga,229478,37086,137247,2594,52551,0,174333,21.273080828070416,78.7269191719296,24.030626029510454
2025,sintomas,fadiga,Fadiga,289913,51777,183932,3765,50439,0,235709,21.96649258195487,78.03350741804513,18.696643475801363
2026,sintomas,fadiga,Fadiga,175521,31415,112940,3062,28104,0,144355,21.76232205327145,78.23767794672855,17.75627987534255
2019,sintomas,febre,Febre,43513,38344,4874,175,120,0,43218,88.72229163774354,11.277708362256467,0.6779583113092639
2020,sintomas,febre,Febre,979812,565476,286663,14129,113544,0,852139,66.35959626305097,33.64040373694902,13.030356843965984
2021,sintomas,febre,Febre,1480215,787029,437554,16986,238646,0,1224583,64.26914304706173,35.73085695293827,17.269923625959745
2022,sintomas,febre,Febre,475980,237742,149557,4765,83916,0,387299,61.38461498738701,38.615385012613,18.63124501029455
2023,sintomas,febre,Febre,240704,139532,68262,1346,31564,0,207794,67.14919583818589,32.850804161814104,13.67239431002393
2024,sintomas,febre,Febre,229478,143886,62074,752,22766,0,205960,69.86113808506506,30.13886191493494,10.248476978185273
2025,sintomas,febre,Febre,289913,181501,85642,850,21920,0,267143,67.94151446977837,32.058485530221645,7.854080362039646
2026,sintomas,febre,Febre,175521,116362,47044,525,11590,0,163406,71.21035947272438,28.789640527275623,6.902307985939005
2019,sintomas,garganta,Dor de garganta,43513,7515,32189,2955,854,0,39704,18.92756397340318,81.07243602659682,8.75370578907453
2020,sintomas,garganta,Dor de garganta,979812,158804,573086,25461,222461,0,731890,21.69779611690281,78.30220388309719,25.30301731352545
2021,sintomas,garganta,Dor de garganta,1480215,238250,786525,28030,427410,0,1024775,23.249005879339368,76.75099412066064,30.768503224193783
2022,sintomas,garganta,Dor de garganta,475980,64636,261589,8790,140965,0,326225,19.813319028278027,80.18668097172197,31.46245640573133
2023,sintomas,garganta,Dor de garganta,240704,25913,144903,4943,64945,0,170816,15.170124578493818,84.82987542150619,29.034831161925016
2024,sintomas,garganta,Dor de garganta,229478,23923,145960,4519,55076,0,169883,14.082044701353286,85.91795529864672,25.969809742110357
2025,sintomas,garganta,Dor de garganta,289913,30842,199779,6574,52718,0,230621,13.37345688380503,86.62654311619497,20.451652737200472
2026,sintomas,garganta,Dor de garganta,175521,19601,121541,4782,29597,0,141142,13.887432514772357,86.11256748522764,19.586830065918036
2019,sintomas,outro_sin,Apresentou outros sintomas?,43513,9679,28819,1800,3215,0,38498,25.14156579562575,74.85843420437426,11.525291292257487
2020,sintomas,outro_sin,Apresentou outros sintomas?,979812,316919,402383,28311,232199,0,719302,44.05924076396284,55.94075923603717,26.58775356905202
2021,sintomas,outro_sin,Apresentou outros sintomas?,1480215,473639,553867,31743,420966,0,1027506,46.095983867734105,53.904016132265895,30.58400299956425
2022,sintomas,outro_sin,Apresentou outros sintomas?,475980,141819,184576,8224,141361,0,326395,43.45011412552275,56.54988587447725,31.426740619353755
... [44 more rows omitted]
```

### `outputs/tables/eda_02_uf_residencia_por_ano.csv`

- Git: `ignored` · `7.4 KB` · modified `2026-10-17 00:37 UTC` · 224 rows (first 60 shown)

```csv
ano_internacao,uf_residencia_categoria,quantidade,percentual_ano
2019,SP,10795,24.80867786638476
2019,PR,6555,15.064463493668558
2019,MG,3674,8.443453680509274
2019,RS,3427,7.875807230023211
2019,RJ,2209,5.076643761634454
2019,SC,2176,5.000804357318502
2019,AM,1921,4.414772596695241
2019,MS,1656,3.8057591984004784
2019,PE,1608,3.6954473375772756
2019,DF,1500,3.4472456507250704
2019,BA,1345,3.091030266816813
2019,GO,1294,2.973823914692161
2019,PA,996,2.288971112081447
2019,CE,963,2.2131317077654953
2019,ES,657,1.5098935950175811
2019,PI,414,0.9514397996001196
2019,AC,314,0.7216234228851148
2019,MT,307,0.7055362765150645
2019,RN,293,0.6733619837749638
2019,PB,278,0.6388895272677131
2019,SE,252,0.5791372693218119
2019,TO,233,0.5354721577459609
2019,MA,227,0.5216831751430607
2019,RO,156,0.35851354767540733
2019,AL,155,0.3562153839082573
2019,AP,47,0.10801369705605221
2019,Ausente ou inesperada,33,0.07583940431595156
2019,RR,28,0.06434858548020132
2020,SP,314025,32.0495156213641
2020,MG,98025,10.004470245312366
2020,RJ,91146,9.302396786322275
2020,PR,64042,6.5361518332088195
2020,RS,52287,5.336431886933412
2020,PE,40759,4.15987965038191
2020,CE,35257,3.5983433556641478
2020,BA,34485,3.5195527305238143
2020,GO,31476,3.212453001187983
2020,SC,29282,2.9885324939886426
2020,PA,27557,2.8124783121660073
2020,DF,23281,2.3760680620363903
2020,AM,20696,2.1122419402905863
2020,MS,16455,1.6794038039950523
2020,PB,14964,1.5272317546631395
2020,MT,13840,1.4125158703914629
2020,PI,11728,1.1969643156034013
2020,MA,11194,1.1424640645348292
2020,AL,9566,0.9763097410523651
2020,RN,9267,0.9457936828697749
2020,ES,8051,0.8216882422342244
2020,RO,5906,0.6027686944025997
2020,SE,5445,0.5557188521879707
2020,TO,4287,0.4375329144774712
2020,AC,2467,0.2517829951051835
2020,AP,2423,0.2472923377137655
2020,RR,1813,0.18503549660547125
2020,Ausente ou inesperada,88,0.00898131478283589
2021,SP,448900,30.326675516732365
2021,MG,191958,12.968251233773472
2021,PR,119005,8.03971044746878
2021,RJ,110165,7.44249990710809
... [164 more rows omitted]
```

### `outputs/tables/eda_02_vacinacao_por_ano.csv`

- Git: `ignored` · `2.6 KB` · modified `2026-10-17 00:37 UTC` · 16 rows

```csv
ano_internacao,grupo_clinico,coluna,nome_amigavel,quantidade_total,quantidade_sim,quantidade_nao,quantidade_ignorado,quantidade_ausente,quantidade_inesperado,quantidade_respostas_validas,percentual_sim_validos,percentual_nao_validos,percentual_sem_resposta_valida
2019,vacinacao,vacina,Recebeu vacina contra influenza?,43513,9073,19227,7241,7972,0,28300,32.06007067137809,67.9399293286219,34.96196538965366
2020,vacinacao,vacina,Recebeu vacina contra influenza?,979812,133125,277126,386783,182778,0,410251,32.449646679715585,67.5503533202844,58.12962078439538
2021,vacinacao,vacina,Recebeu vacina contra influenza?,1480215,124445,499833,493503,362434,0,624278,19.93422802020895,80.06577197979105,57.825180801437625
2022,vacinacao,vacina,Recebeu vacina contra influenza?,475980,41385,107033,149120,178442,0,148418,27.88408414073765,72.11591585926236,68.81843774948527
2023,vacinacao,vacina,Recebeu vacina contra influenza?,240704,16719,54881,63729,105375,0,71600,23.350558659217878,76.64944134078212,70.25392182930071
2024,vacinacao,vacina,Recebeu vacina contra influenza?,229478,34502,118213,24881,51882,0,152715,22.59241069966932,77.40758930033068,33.45113692815869
2025,vacinacao,vacina,Recebeu vacina contra influenza?,289913,77684,189362,6067,16800,0,267046,29.090119305288226,70.90988069471177,7.887538675395723
2026,vacinacao,vacina,Recebeu vacina contra influenza?,175521,36806,130225,1493,6997,0,167031,22.03543054882028,77.96456945117973,4.837028047925889
2019,vacinacao,vacina_cov,Recebeu vacina contra COVID-19?,43513,55,283,259,42916,0,338,16.272189349112427,83.72781065088756,99.22322064670328
2020,vacinacao,vacina_cov,Recebeu vacina contra COVID-19?,979812,24284,65967,36376,853185,0,90251,26.907181083866107,73.0928189161339,90.78894726743498
2021,vacinacao,vacina_cov,Recebeu vacina contra COVID-19?,1480215,343199,528311,243981,364724,0,871510,39.37981205034939,60.62018794965061,41.12274230432742
2022,vacinacao,vacina_cov,Recebeu vacina contra COVID-19?,475980,286756,177549,11427,248,0,464305,61.76026534282422,38.23973465717578,2.452834152695491
2023,vacinacao,vacina_cov,Recebeu vacina contra COVID-19?,240704,121641,115227,3802,34,0,236868,51.35391863822889,48.64608136177112,1.5936586014357883
2024,vacinacao,vacina_cov,Recebeu vacina contra COVID-19?,229478,109937,114985,4536,20,0,224922,48.87783320439974,51.12216679560026,1.985375504405651
2025,vacinacao,vacina_cov,Recebeu vacina contra COVID-19?,289913,175324,111918,2653,18,0,287242,61.037034973994054,38.962965026005946,0.9213108760214271
2026,vacinacao,vacina_cov,Recebeu vacina contra COVID-19?,175521,65900,107505,2094,22,0,173405,38.00351777630403,61.99648222369597,1.2055537514029662
```

### `outputs/tables/eda_02_variacao_comorbidades.csv`

- Git: `ignored` · `2.0 KB` · modified `2026-10-17 00:37 UTC` · 13 rows

```csv
grupo_clinico,coluna,nome_amigavel,percentual_sim_minimo,percentual_sim_maximo,percentual_sim_medio,percentual_sem_resposta_valida_maximo,quantidade_anos_observados,amplitude_percentual_sim,flag_variacao_10_pp
comorbidades,cardiopati,Doenca cardiovascular cronica,27.915404265431,62.54290333585488,48.691920506075256,68.1456919684824,8,34.62749907042388,True
comorbidades,diabetes,Diabetes mellitus,19.539264502969584,46.38605355415614,33.11686258606036,69.25154255046405,8,26.84678905118656,True
comorbidades,obesidade,Obesidade,4.106889969829444,22.575467273580003,9.581222489434838,71.07650890720552,8,18.468577303750557,True
comorbidades,asma,Asma,8.789636027143738,25.808949610044802,17.383991825988588,69.09942400054693,8,17.019313582901063,True
comorbidades,out_morbi,Outro fator de risco?,46.379868358849414,59.968219573853375,52.95513627159808,68.66585764666337,8,13.58835121500396,True
comorbidades,pneumopati,Outra pneumopatia cronica,9.063950734249172,18.11307166006482,15.490135863076581,69.94718580682652,8,9.049120925815647,False
comorbidades,neurologic,Doenca neurologica cronica,9.278784682568892,16.78817231710426,13.813271597855422,70.06625987773543,8,7.509387634535367,False
comorbidades,renal,Doenca renal cronica,5.950635386119258,10.730760315252667,8.180654361040396,70.6285857532717,8,4.780124929133409,False
comorbidades,imunodepre,Imunodeficiencia ou imunodepressao,5.949748279880467,10.19185377957998,8.448954005060878,70.4417135271563,8,4.2421054996995124,False
comorbidades,sind_down,Sindrome de Down,0.7262040243400194,3.7271958439047967,2.195611885124995,70.81062217495348,8,3.0009918195647773,False
comorbidades,hematologi,Doenca hematologica cronica,1.7505640404322822,3.589736057459278,2.776720143856151,70.74539683594789,8,1.8391720170269958,False
comorbidades,hepatica,Doenca hepatica cronica,1.5131964809384164,2.4796411873596105,2.032925003588078,70.94439643711779,8,0.9664447064211941,False
comorbidades,puerpera,Puerpera ou parturiente,0.7066460796357448,1.5632603406326033,0.9626067797983271,71.16167575113002,8,0.8566142609968586,False
```

### `outputs/tables/eda_02_variacao_preenchimento.csv`

- Git: `ignored` · `12.6 KB` · modified `2026-10-17 00:34 UTC` · 88 rows (first 60 shown)

```csv
coluna,nome_amigavel,grupo,uso_inicial_sugerido,preenchimento_minimo,preenchimento_maximo,preenchimento_medio,quantidade_anos_observados,amplitude_pontos_percentuais,flag_variacao_20_pp
vacina_cov,Recebeu vacina contra COVID-19?,vacinacao_covid,modelo_a_nucleo,1.3720037689885782,99.99379124082051,73.69524810117095,8,98.62178747183194,True
pov_ct,Pertence a povo ou comunidade tradicional?,demografia_contexto_social,modelo_b_ampliado,1.7787787557741366,100.0,77.24939208684502,8,98.22122124422586,True
estrang,Paciente estrangeiro?,demografia_contexto_social,modelo_b_ampliado,0.48950888240296003,96.14234194198986,68.7212896734563,8,95.6528330595869,True
trat_cov,Recebeu tratamento antiviral para COVID-19?,tratamentos,exploracao_eda,0.2091329028106543,84.40357564052164,42.821559686499626,8,84.19444273771099,True
fadiga,Fadiga,sintomas,modelo_a_nucleo,0.5538574678831614,83.98824072333225,63.4451417800059,8,83.43438325544909,True
dor_abd,Dor abdominal,sintomas,modelo_a_nucleo,0.30105945349665614,82.49782077358265,61.58550311325197,8,82.19676132008598,True
perd_olft,Perda do olfato,sintomas,modelo_a_nucleo,0.2964631259623561,82.12179739176509,61.28934723589909,8,81.82533426580272,True
perd_pala,Perda do paladar,sintomas,modelo_a_nucleo,0.2964631259623561,81.92808837688938,61.20698715442671,8,81.63162525092702,True
dt_antivir,Data de inicio do antiviral,tratamentos,exploracao_eda,2.0252463324584604,62.15154091880587,15.129731478932602,8,60.12629458634741,True
tp_antivir,Tipo de antiviral utilizado,tratamentos,exploracao_eda,2.3266890282830537,62.15383908257303,15.59245270829318,8,59.82715005428997,True
dose_1_cov,Data da primeira dose contra COVID-19,vacinacao_covid,modelo_c_sensibilidade,0.11490818835750236,56.78389848312955,31.503610601659787,8,56.668990294772044,True
dose_2_cov,Data da segunda dose contra COVID-19,vacinacao_covid,modelo_c_sensibilidade,0.0827338956174017,53.10307155762847,28.16627182870427,8,53.020337662011066,True
vacina,Recebeu vacina contra influenza?,vacinacao_influenza,modelo_a_nucleo,56.22216498271736,96.01358242033716,78.11027858451898,8,39.7914174376198,True
dt_digita,Data de inclusao do registro no sistema,desfecho_auditoria,auditoria,64.15324155999357,100.0,95.5191551949992,8,35.846758440006425,True
cs_escol_n,Escolaridade,demografia_contexto_social,modelo_b_ampliado,62.6068729900034,92.59072001470825,69.38346659273792,8,29.98384702470485,True
dose_ref,Data da dose de reforco,vacinacao_covid,modelo_c_sensibilidade,0.027577965205800567,29.40582624302047,15.387413718079475,8,29.37824827781467,True
diarreia,Diarreia,sintomas,modelo_a_nucleo,68.48859195764528,97.6030151908625,78.35231354619049,8,29.11442323321721,True
vomito,Vomito,sintomas,modelo_a_nucleo,69.08630614731712,97.6857490864799,78.52156672280701,8,28.599442939162785,True
garganta,Dor de garganta,sintomas,modelo_a_nucleo,70.38425984285054,98.03736814285386,78.85175449401551,8,27.653108300003325,True
dt_ut_dose,Data da ultima dose contra influenza,vacinacao_influenza,modelo_c_sensibilidade,3.615067859994117,27.031557743185026,12.421953651158011,8,23.41648988319091,True
outro_sin,Apresentou outros sintomas?,sintomas,exploracao_texto,70.30106306987689,92.6114034886126,76.6190544545802,8,22.310340418735706,True
cardiopati,Doenca cardiovascular cronica,comorbidades_fatores_risco,modelo_a_nucleo,31.972812370029796,54.20131617085726,39.88084611601467,8,22.228503800827465,True
diabetes,Diabetes mellitus,comorbidades_fatores_risco,modelo_a_nucleo,30.861264464081223,50.831281919388616,37.831705093167045,8,19.970017455307392,False
desc_resp,Desconforto respiratorio,sintomas,modelo_b_ampliado,79.49241564771629,99.28067474088203,88.09147763635902,8,19.78825909316575,False
out_morbi,Outro fator de risco?,comorbidades_fatores_risco,modelo_a_nucleo,31.59678898821224,50.27178683257605,38.67093063173505,8,18.67499784436381,False
saturacao,Saturacao de oxigenio abaixo de 95%?,sintomas,modelo_a_nucleo,80.70612210597083,98.51998253395537,87.20295551110405,8,17.813860427984537,False
febre,Febre,sintomas,modelo_a_nucleo,82.36984747258288,99.724220347942,89.64815865568102,8,17.354372875359118,False
dose_2ref,Data da segunda dose de reforco,vacinacao_covid,modelo_c_sensibilidade,0.011490818835750236,17.06826641850572,7.393951409341573,8,17.05677559966997,False
antiviral,Usou antiviral contra influenza?,tratamentos,exploracao_eda,83.16875691787448,99.17725737136028,87.79467548154338,8,16.00850045348581,False
obesidade,Obesidade,comorbidades_fatores_risco,modelo_a_nucleo,29.189669612183156,44.106930717321276,34.477271994400375,8,14.91726110513812,False
dispneia,Dispneia,sintomas,modelo_a_nucleo,84.4730871045002,99.34042699882794,90.71430629302054,8,14.867339894327742,False
renal,Doenca renal cronica,comorbidades_fatores_risco,modelo_a_nucleo,29.509289486728086,44.01293309328728,34.484323304899206,8,14.503643606559194,False
neurologic,Doenca neurologica cronica,comorbidades_fatores_risco,modelo_a_nucleo,30.075603489041196,44.33074916412536,35.08167299397847,8,14.255145675084162,False
pneumopati,Outra pneumopatia cronica,comorbidades_fatores_risco,modelo_a_nucleo,30.224873376974838,44.36840944997612,35.11054682651589,8,14.143536073001282,False
imunodepre,Imunodeficiencia ou imunodepressao,comorbidades_fatores_risco,modelo_a_nucleo,29.744019234165712,43.634391087269805,34.61434698338411,8,13.890371853104092,False
hepatica,Doenca hepatica cronica,comorbidades_fatores_risco,modelo_a_nucleo,29.30190689433173,43.10000285769107,33.99751434848719,8,13.798095963359337,False
hematologi,Doenca hematologica cronica,comorbidades_fatores_risco,modelo_a_nucleo,29.43408481036457,43.2067580311325,34.15381421394807,8,13.772673220767931,False
puerpera,Puerpera ou parturiente,comorbidades_fatores_risco,modelo_a_nucleo,29.14949481520872,42.91476324029508,33.87844337445482,8,13.765268425086362,False
sind_down,Sindrome de Down,comorbidades_fatores_risco,modelo_a_nucleo,29.455164909042225,43.02723379587105,34.09069125051857,8,13.572068886828824,False
morb_desc,Descricao de outro fator de risco,comorbidades_fatores_risco,exploracao_texto,14.327630312042434,27.46200291484489,20.20725676496904,8,13.134372602802458,False
asma,Asma,comorbidades_fatores_risco,modelo_a_nucleo,31.021928999948724,43.95588133233723,35.34392023154777,8,12.933952332388504,False
ave_suino,"Contato direto com aves, suinos ou outro animal?",exposicao_animal,modelo_a_nucleo,84.30113193015879,97.09971732585664,88.01868326298013,8,12.798585395697856,False
mae_vac,Mae vacinada contra influenza?,vacinacao_influenza,modelo_c_sensibilidade,0.7310586112437897,12.761703398984212,4.923902874079337,8,12.030644787740423,False
tosse,Tosse,sintomas,modelo_a_nucleo,87.88562544644734,99.65987176246179,93.04977621340292,8,11.774246316014455,False
m_amamenta,Mae amamenta a crianca?,vacinacao_influenza,modelo_c_sensibilidade,0.5424510008042359,11.456346379242985,4.555187515347466,8,10.913895378438749,False
dos_re_bi,Data do reforco bivalente,vacinacao_covid,modelo_c_sensibilidade,0.006894491301450142,10.596627264041283,4.744728731219468,8,10.589732772739833,False
outro_des,Descricao dos outros sintomas,sintomas,exploracao_texto,21.745225564773747,31.817838524125037,28.016747509063443,8,10.07261295935129,False
cs_zona,Zona de residencia,demografia_contexto_social,modelo_a_nucleo,90.26607621190165,97.66046928504124,92.88527194536411,8,7.394393073139597,False
dt_1_dose,Data da primeira dose infantil,vacinacao_influenza,modelo_c_sensibilidade,0.004256138466371439,4.155058369084042,0.921300198896669,8,4.15080223061767,False
co_mu_inte,Municipio de internacao,geografia_internacao,exploracao_eda,92.45785240657607,96.59498803509705,95.3173196342878,8,4.13713562852098,False
sg_uf_inte,UF de internacao,geografia_internacao,derivar_atributo,92.45785240657607,96.59498803509705,95.3173196342878,8,4.13713562852098,False
co_rg_inte,Regional de saude de internacao,geografia_internacao,exploracao_eda,82.4095504513423,86.39487049847172,84.00134941445134,8,3.98532004712942,False
dt_evoluca,Data da alta ou do obito,desfecho_auditoria,auditoria,92.4367430423092,96.30830656357354,94.65558083818499,8,3.871563521264335,False
dt_doseuni,Data da dose unica infantil,vacinacao_influenza,modelo_c_sensibilidade,0.004256138466371439,3.85196073404322,0.8601828967129729,8,3.8477045955768485,False
co_rg_resi,Regional de saude de residencia,geografia_residencia,exploracao_eda,87.49321298371524,91.12219336749938,88.85143013154557,8,3.628980383784139,False
co_regiona,Regional de saude da notificacao,geografia_notificacao,exploracao_eda,86.37349825637347,89.97540964769149,87.99494897634035,8,3.6019113913180263,False
cs_raca,Raca ou cor,demografia_contexto_social,modelo_a_nucleo,96.54815802174063,100.0,99.14130769571072,8,3.451841978259367,False
dt_vac_mae,Data da vacinacao materna,vacinacao_influenza,modelo_c_sensibilidade,0.03391399222410258,2.387792154068899,0.4621145951128455,8,2.3538781618447966,False
pac_cocbo,Codigo da ocupacao,demografia_contexto_social,reavaliar_apos_modelo_principal,0.01608714637005033,2.319730579679303,1.0227116064525472,8,2.3036434333092526,False
pac_dscbo,Descricao da ocupacao,demografia_contexto_social,apoio_interpretacao,0.01608714637005033,2.319730579679303,1.0227116064525472,8,2.3036434333092526,False
... [28 more rows omitted]
```

### `outputs/tables/eda_02_variacao_sintomas.csv`

- Git: `ignored` · `1.9 KB` · modified `2026-10-17 00:37 UTC` · 13 rows

```csv
grupo_clinico,coluna,nome_amigavel,percentual_sim_minimo,percentual_sim_maximo,percentual_sim_medio,percentual_sem_resposta_valida_maximo,quantidade_anos_observados,amplitude_percentual_sim,flag_variacao_10_pp
sintomas,fadiga,Fadiga,21.273080828070416,50.0,28.068219970283657,99.44844069588399,8,28.726919171929584,True
sintomas,febre,Febre,61.38461498738701,88.72229163774354,69.61223172512462,18.63124501029455,8,27.337676650356528,True
sintomas,desc_resp,Desconforto respiratorio,63.90864654416326,85.05905099117147,73.68918759004444,21.430312197991512,8,21.150404447008214,True
sintomas,outro_sin,Apresentou outros sintomas?,25.14156579562575,46.095983867734105,38.57198951252496,31.426740619353755,8,20.954418072108357,True
sintomas,tosse,Tosse,76.0662108853592,93.37900071740992,83.2678499659398,12.946497637167573,8,17.312789832050726,True
sintomas,saturacao,Saturacao de oxigenio abaixo de 95%?,61.01212055103913,76.99078255707443,66.69674051217274,20.202949703769065,8,15.978662006035293,True
sintomas,perd_olft,Perda do olfato,0.7936507936507936,12.797014767158363,4.201351397889889,99.71043136533909,8,12.003363973507568,True
sintomas,perd_pala,Perda do paladar,1.574803149606299,13.049298893290151,4.377449342323514,99.70813320157194,8,11.474495743683853,True
sintomas,dispneia,Dispneia,72.57666416413274,83.65496396186933,76.32848574692089,16.327786881801757,8,11.078299797736591,True
sintomas,garganta,Dor de garganta,13.37345688380503,23.249005879339368,17.525092959543485,31.46245640573133,8,9.875548995534338,False
sintomas,diarreia,Diarreia,9.454563139848746,18.105316101164206,12.17856355107877,32.83394260263036,8,8.65075296131546,False
sintomas,dor_abd,Dor abdominal,2.2900763358778624,9.448363736797415,7.213526767772896,99.69894054650335,8,7.158287400919552,False
sintomas,vomito,Vomito,12.228737980517804,16.03842412451362,14.638187728743688,32.642825535479645,8,3.809686143995817,False
```

### `outputs/tables/eda_02_volume_por_ano.csv`

- Git: `ignored` · `368 B` · modified `2026-10-17 00:34 UTC` · 8 rows

```csv
ano_internacao,quantidade_registros,percentual_coorte,periodo_completo
2019,43513,1.1114045591264263,True
2020,979812,25.026257069997058,True
2021,1480215,37.807498896590054,True
2022,475980,12.157432078987805,True
2023,240704,6.148036747637885,True
2024,229478,5.861303413214764,True
2025,289913,7.404927951417268,True
2026,175521,4.483139283028738,False
```

### `outputs/tables/supervisionado_registros_conflitantes_split_provisorio.csv`

- Git: `ignored` · `376 B` · modified `2026-10-17 00:42 UTC` · 4 rows

```csv
indice_original,grupo_split,estrato_split,nu_notific,ano_internacao,alvo_obito_srag,evolucao,dt_interna
653105,31736866916969,2024__y0,31736866916969,2024,0,1,2024-01-14
263526,31736866916969,2025__y0,31736866916969,2025,0,1,2025-01-14
483104,31745324608735,2024__y1,31745324608735,2024,1,2,2024-08-15
196104,31745324608735,2025__y1,31745324608735,2025,1,2,2025-04-16
```

### `outputs/tables/supervisionado_resumo_conflitos_split_provisorio.csv`

- Git: `ignored` · `154 B` · modified `2026-10-17 00:42 UTC` · 2 rows

```csv
grupo_split,quantidade_linhas,quantidade_estratos,estratos_observados
31736866916969,2,2,2024__y0 | 2025__y0
31745324608735,2,2,2024__y1 | 2025__y1
```

### `outputs/tables/supervisionado_waterfall_conflitos_split_provisorio.csv`

- Git: `ignored` · `181 B` · modified `2026-10-17 00:42 UTC` · 1 rows

```csv
etapa,politica,grupos_conflitantes,linhas_excluidas,linhas_restantes,status
quarentena_conflitos_split,quarentena_provisoria,2,4,3915132,provisoria_pendente_validacao_pessoa_a
```

### `outputs/tables/pessoa_a/a1_alvo_por_ano.csv`

- Git: `ignored` · `830 B` · modified `2026-10-17 00:23 UTC` · 32 rows

```csv
ano,1,2,3,9,<vazio>,total
1917,1,0,0,0,3,4
1918,0,0,0,0,1,1
1941,1,0,0,1,2,4
2009,1,0,0,0,0,1
2011,1,0,0,0,0,1
2012,2,0,0,0,0,2
2016,0,1,0,0,0,1
2017,2,0,0,0,0,2
2018,10,0,0,0,1,11
2019,38292,5221,8,1340,2682,47543
2020,705699,274113,15414,20385,60753,1076364
2021,1062924,417291,21305,38603,117266,1657389
2022,389547,86433,13727,12552,33874,536133
2023,217667,23037,7724,5528,11713,265669
2024,210358,19120,7220,4212,12457,253367
2025,268686,21227,8252,5561,11889,315615
2026,165784,9743,5014,4454,25442,210437
2027,6,0,0,1,0,7
2028,4,0,0,0,0,4
2029,3,0,0,3,3,9
2031,2,0,0,0,0,2
2032,1,0,0,0,0,1
2033,0,0,0,0,3,3
2034,0,0,0,1,0,1
2050,0,0,0,0,1,1
2052,1,0,0,0,0,1
2055,0,0,0,0,1,1
2056,0,0,0,0,1,1
2092,1,0,0,0,0,1
2098,1,0,0,1,0,2
2099,1,0,0,0,0,1
sem_data,38927,16729,1383,2610,12429,72078
```

### `outputs/tables/pessoa_a/a1_amostra_exclusoes_01.csv`

- Git: `ignored` · `3.5 KB` · modified `2026-10-17 00:22 UTC` · 50 rows

```csv
HOSPITAL,DT_INTERNA,EVOLUCAO,TP_IDADE,NU_IDADE_N,DT_NASC,DT_SIN_PRI,DT_NOTIFIC,DT_EVOLUCA,DT_ENCERRA,NU_NOTIFIC
,,,3,75,1950-11-02,2026-03-22,2026-03-23,,,31775652598724
2,,1,3,4,2022-03-03,2026-03-23,2026-03-29,2026-03-31,2026-06-11,31781205405890
,,1,2,8,2025-08-09,2026-04-18,2026-04-28,2026-04-19,2026-06-02,31780414044334
2,,1,3,50,1975-04-08,2026-03-07,2026-03-07,,2026-03-20,31776951547485
,,1,3,83,1942-12-21,2026-08-10,2026-08-13,,2026-08-13,31786648314248
,,9,3,8,2017-09-29,2026-03-25,2026-03-26,,2026-03-30,31776114768213
2,,,3,7,2019-02-21,2026-04-18,2026-04-22,,2026-04-26,31777485114556
,,1,2,4,2026-03-22,2026-07-12,2026-07-13,2026-07-21,2026-07-21,31784037049124
,,1,3,4,2021-09-27,2026-06-01,2026-06-15,,2026-07-23,31781782758352
,,,3,75,1950-09-14,2026-06-07,2026-06-08,,,31780925222220
,,,3,65,1960-07-08,2026-04-01,2026-04-14,,,31784125722808
,,,3,9,2016-07-22,2026-01-13,2026-01-18,,,31768751302378
2,,,2,7,2025-06-18,2026-01-04,2026-01-07,,,31767972796009
,,,3,5,2020-10-10,2026-08-18,2026-08-20,,,31787317509231
,,1,3,1,2025-01-15,2026-05-06,2026-05-06,,2026-05-08,31780258970676
9,,1,3,4,2021-09-06,2026-05-03,2026-05-03,2026-05-05,2026-07-03,31783105365899
2,,2,3,1,2025-03-11,2026-05-28,2026-06-09,2026-06-09,2026-06-16,31782311120470
,,1,2,6,2025-11-02,2026-05-20,2026-05-21,2026-06-08,2026-06-23,31782218952764
,,,2,7,2026-01-06,2026-08-02,2026-08-07,,,31786119085137
,,,3,73,1952-08-22,2026-04-04,2026-04-13,,,31776078195609
,,1,3,57,1968-08-22,2026-04-29,2026-04-30,,2026-05-12,31778069604877
,,1,3,1,2025-04-14,2026-04-24,2026-04-27,,2026-05-05,31777322020581
9,,1,3,40,1985-05-02,2026-01-30,2026-02-03,,2026-08-03,31772451218119
2,,1,2,2,2026-04-13,2026-06-19,2026-06-22,2026-06-26,2026-06-26,31782249136338
2,,1,3,6,2020-03-01,2026-05-03,2026-05-07,,2026-05-13,31778676513948
,,,3,9,2017-02-18,2026-06-23,2026-06-24,,,31782997221458
,,,2,2,2026-05-23,2026-07-06,2026-07-06,,,31783376982074
,,,3,80,1945-10-02,2026-02-28,2026-03-06,,2026-03-18,31772828882255
,,1,2,8,2025-11-28,2026-07-21,2026-07-24,,2026-07-24,31785406932822
,,1,2,6,2026-02-17,2026-08-07,2026-08-11,2026-08-12,2026-08-31,31787766202549
2,,2,3,12,2014-02-11,2026-03-19,2026-03-27,2026-03-27,2026-03-27,31774964608477
,,1,3,1,2024-10-01,2026-02-09,2026-02-09,,2026-02-13,31779580487653
2,,2,3,88,1937-10-25,2026-01-27,2026-01-31,2026-01-31,2026-02-12,31774289284081
2,,,3,2,2023-10-15,2026-04-22,2026-04-24,,2026-04-28,31777486180757
,,,3,66,1960-04-14,2026-08-08,2026-08-12,,,31786571794321
,,,3,1,2024-10-13,2026-06-11,2026-06-17,,,31781707959452
,,1,3,57,1969-05-11,2026-08-14,2026-08-17,2026-08-19,2026-08-19,31786973020085
9,,,3,46,1979-11-27,2026-09-01,2026-09-02,,,31788371070901
,,1,3,1,2024-12-23,2026-04-11,2026-04-16,,2026-06-08,31776357800729
,,,3,1,2025-01-04,2026-04-05,2026-04-16,,,31776343591581
2,,1,3,41,1984-05-03,2026-02-22,2026-03-02,2026-02-24,2026-03-02,31772423427061
,,1,2,11,2025-08-30,2026-07-23,2026-07-24,,2026-08-03,31784914226565
,,1,2,4,2025-09-06,2026-01-12,2026-01-12,2026-01-26,2026-02-06,31769008935928
,,,3,35,1991-08-07,2026-08-15,2026-08-18,,,31787060140830
,,,3,2,2024-05-29,2026-08-21,2026-08-28,,,31789074988249
2,,1,3,90,1935-08-24,2026-01-07,2026-01-09,2026-01-09,2026-01-14,31768403627553
,,1,3,67,1959-01-29,2026-06-15,2026-06-16,2026-06-19,2026-06-25,31781696854761
2,,1,3,42,1983-12-15,2026-01-14,2026-02-08,,2026-02-08,31770572532065
2,,2,3,64,1961-07-01,2026-02-21,2026-02-21,2026-02-21,2026-02-21,31773350909558
,,,3,58,1968-06-08,2026-07-16,2026-07-21,,2026-08-10,31784646474693
```

### `outputs/tables/pessoa_a/a1_amostra_exclusoes_02.csv`

- Git: `ignored` · `3.6 KB` · modified `2026-10-17 00:22 UTC` · 50 rows

```csv
HOSPITAL,DT_INTERNA,EVOLUCAO,TP_IDADE,NU_IDADE_N,DT_NASC,DT_SIN_PRI,DT_NOTIFIC,DT_EVOLUCA,DT_ENCERRA,NU_NOTIFIC
1,,1,2,8,2025-08-10,2026-04-01,2026-04-15,,2026-04-21,31777549715837
1,,1,3,77,1949-05-26,2026-07-12,2026-07-12,2026-07-15,2026-07-17,31788874096772
1,,1,3,7,2018-08-31,2026-01-10,2026-01-12,2026-01-28,2026-02-09,31770647469632
1,,,3,3,2023-04-20,2026-09-04,2026-09-09,,,31788975169679
1,,1,2,3,2025-11-10,2026-02-06,2026-02-07,2026-02-20,2026-06-10,31773940312126
1,,1,3,1,2024-09-24,2026-07-04,2026-08-26,2026-08-11,2026-08-26,31787751835649
1,,1,3,43,1982-11-27,2026-02-21,2026-02-27,2026-03-02,2026-03-05,31772219564355
1,,1,2,1,2025-12-04,2026-01-08,2026-01-12,2026-01-21,2026-01-26,31769453667829
1,,1,2,11,2025-03-16,2026-02-20,2026-02-23,2026-02-24,2026-04-13,31771838270995
1,,1,3,31,1994-11-08,2026-09-06,2026-09-09,2026-09-16,2026-09-17,31789563351861
1,,1,3,62,1963-11-04,2026-02-11,2026-02-13,2026-02-20,2026-03-04,31771008239682
1,,,1,7,2026-05-12,2026-05-19,2026-05-21,,,31779467820819
1,,,3,3,2022-12-09,2026-09-03,2026-09-05,,,31788620734654
1,,,3,4,2021-11-21,2026-07-30,2026-07-31,,,31786458971825
1,,,3,2,2024-03-30,2026-08-01,2026-08-04,,,31785867861406
1,,1,3,2,2023-09-24,2026-07-10,2026-07-20,2026-07-14,2026-07-22,31784748275602
1,,1,3,2,2024-05-11,2026-09-03,2026-09-10,2026-09-15,2026-09-18,31789065947469
1,,,3,2,2024-06-17,2026-09-01,2026-09-02,,,31788382629475
1,,,3,2,2024-06-05,2026-08-14,2026-08-19,,,31787172228431
1,,,3,2,2024-06-25,2026-06-26,2026-07-10,,,31783704794838
1,,,3,1,2024-08-25,2026-06-20,2026-06-22,,,31782152025297
1,,,3,1,2024-12-14,2026-05-03,2026-05-07,,,31778183597383
1,,1,3,1,2025-06-09,2026-08-21,2026-08-24,2026-09-03,2026-09-22,31787583741919
1,,,3,1,2025-07-27,2026-07-28,2026-07-29,,,31785360853298
1,,,2,10,2025-08-16,2026-06-01,2026-06-04,,,31780575267248
1,,1,2,8,2025-08-22,2026-04-25,2026-04-29,2026-05-01,2026-05-25,31777465516478
1,,1,2,7,2025-08-18,2026-03-23,2026-03-28,,2026-04-01,31774888210371
1,,1,3,73,1952-05-15,2026-04-25,2026-04-27,2026-04-30,2026-05-04,31778092086325
1,,1,3,2,2023-11-03,2026-07-07,2026-07-09,2026-07-13,2026-07-14,31783942348556
1,,,3,2,2023-10-10,2026-04-13,2026-04-13,,,31776091074476
1,,1,3,2,2023-11-06,2026-08-25,2026-08-25,,2026-09-11,31787918509080
1,,1,3,75,1950-11-05,2026-06-04,2026-06-11,,2026-06-16,31781178224317
1,,1,3,1,2024-12-27,2026-03-12,2026-03-15,2026-03-16,2026-03-16,31773662225812
1,,2,3,46,1980-03-30,2026-05-04,2026-05-07,2026-05-14,2026-05-15,31778770573608
1,,1,3,2,2024-03-22,2026-04-22,2026-04-29,2026-05-02,2026-05-07,31781007905994
1,,1,3,37,1989-08-03,2026-08-24,2026-08-25,2026-09-04,2026-09-25,31789485848987
1,,,3,50,1975-05-26,2026-01-17,2026-01-18,,2026-01-22,31769099934860
1,,1,3,74,1952-02-15,2026-07-20,2026-08-03,2026-08-03,2026-08-18,31786461727931
1,,1,3,81,1944-05-31,2026-03-27,2026-04-09,2026-04-15,2026-04-20,31775740797449
1,,1,3,2,2024-01-08,2026-09-01,2026-09-03,2026-09-05,2026-09-08,31789128973635
1,,1,3,1,2024-10-17,2026-08-18,2026-08-24,,2026-09-10,31789062515336
1,,1,3,2,2024-01-29,2026-03-17,2026-03-18,2026-03-26,2026-04-03,31775250713894
1,,1,3,27,1998-11-17,2026-05-01,2026-05-09,,2026-05-18,31778336961281
1,,1,3,57,1968-08-22,2026-01-19,2026-02-04,,2026-02-04,31770645711921
1,,,3,2,2024-05-21,2026-08-04,2026-08-06,,2026-08-07,31786039467922
1,,1,3,78,1947-11-07,2026-06-19,2026-06-26,,2026-07-08,31782494985225
1,,1,3,1,2024-02-22,2026-01-06,2026-01-08,2026-01-13,2026-01-14,31768314692248
1,,1,2,8,2025-12-25,2026-08-30,2026-09-02,2026-09-09,2026-09-11,31788527556568
1,,1,3,1,2024-07-23,2026-01-30,2026-02-05,2026-02-13,2026-02-24,31770378778543
1,,,2,7,2026-01-11,2026-09-07,2026-09-11,,,31789140997184
```

### `outputs/tables/pessoa_a/a1_amostra_exclusoes_03.csv`

- Git: `ignored` · `4.1 KB` · modified `2026-10-17 00:22 UTC` · 50 rows

```csv
HOSPITAL,DT_INTERNA,EVOLUCAO,TP_IDADE,NU_IDADE_N,DT_NASC,DT_SIN_PRI,DT_NOTIFIC,DT_EVOLUCA,DT_ENCERRA,NU_NOTIFIC
1,2026-06-11,1,2,1,2026-05-02,2026-06-02,2026-06-11,2026-06-19,2026-06-19,31781201987679
1,2026-06-15,,3,37,1989-04-04,2026-06-15,2026-06-17,,,31782407823707
1,2026-03-10,1,3,4,2021-10-06,2026-03-09,2026-03-14,,,31773493207022
1,2026-03-18,1,1,11,2026-03-07,2026-03-18,2026-03-23,2026-04-14,2026-04-15,31774542694487
1,2026-08-18,,3,75,1950-09-09,2026-08-08,2026-08-18,,,31787085791388
1,2026-03-10,1,3,78,1947-11-10,2026-03-10,2026-03-10,2026-03-16,2026-03-16,31773441569320
1,2026-05-27,,3,1,2025-03-11,2026-05-19,2026-05-26,,,31780065930274
1,2026-05-08,,2,0,2025-05-13,2026-05-05,2026-05-08,,,31779901434401
1,2026-06-15,,3,66,1960-06-13,2026-06-14,2026-06-16,,,31781629359036
1,2026-05-23,,3,15,2011-04-14,2026-05-23,2026-05-24,,,31780947295202
1,2026-07-07,1,3,4,2021-07-14,2026-07-03,2026-07-09,2026-07-11,2026-07-17,31783622594901
1,2026-04-04,,3,32,1993-09-15,2026-04-04,2026-04-04,,,31779149516127
1,2026-05-13,1,2,6,2025-11-17,2026-05-12,2026-05-13,2026-05-15,2026-05-21,31779376399165
1,2026-05-15,,3,74,1952-04-18,2026-05-15,2026-05-16,,,31779137099882
1,2026-03-19,1,3,11,2014-09-18,2026-03-19,2026-03-20,2026-03-28,2026-04-06,31775493343412
1,2026-05-19,,3,75,1950-12-19,2026-05-16,2026-05-22,,,31779804314537
1,2026-09-08,,2,5,2026-03-21,2026-09-08,2026-09-09,,,31788967146868
1,2026-06-02,1,2,1,2026-04-22,2026-05-27,2026-06-03,2026-06-16,2026-06-19,31780508092246
1,2026-04-14,1,2,5,2025-11-23,2026-04-14,2026-05-04,2026-04-14,2026-05-04,31777902324367
1,2026-04-22,1,3,31,1995-01-25,2026-04-19,2026-04-23,2026-05-04,2026-05-11,31777581635868
1,2026-03-28,,3,1,2024-10-25,2026-03-08,2026-03-28,,,31774869565386
1,2026-04-11,1,3,5,2020-06-26,2026-04-05,2026-04-11,2026-04-13,2026-04-17,31776433120192
1,2026-05-26,1,3,12,2013-08-27,2026-05-26,2026-05-28,2026-05-29,2026-06-03,31780063755400
1,2026-03-26,,3,78,1947-12-30,2026-03-26,2026-03-31,,,31775052422525
1,2026-06-02,1,2,4,2026-02-04,2026-06-02,2026-06-03,2026-06-09,2026-07-29,31785339117793
1,2026-08-25,2,3,65,1961-06-06,2026-08-25,2026-08-25,2026-08-27,2026-09-01,31790273405307
1,2026-05-18,1,3,58,1967-11-07,2026-05-16,2026-05-18,2026-05-25,2026-05-25,31779716421577
1,2026-06-20,1,3,25,2001-02-10,2026-06-18,2026-06-20,2026-07-01,2026-07-07,31783419856968
1,2026-05-26,1,3,2,2023-10-10,2026-05-21,2026-05-26,2026-05-30,2026-05-30,31781122407541
1,2026-05-09,1,3,64,1962-02-11,2026-05-08,2026-05-12,2026-05-20,2026-05-20,31778874675119
1,2026-04-13,1,3,80,1946-03-11,2026-04-01,2026-04-16,2026-05-07,2026-05-08,31776340279767
1,2026-03-24,1,3,25,2000-04-11,2026-03-24,2026-03-25,2026-04-03,2026-04-13,31774465391980
1,2026-05-05,1,3,1,2024-12-13,2026-05-05,2026-05-05,2026-05-10,2026-05-11,31778065923802
1,2026-07-27,1,2,3,2026-04-14,2026-07-15,2026-07-27,2026-08-07,2026-08-10,31785175448633
1,2026-01-18,1,3,81,1945-01-17,2026-01-18,2026-01-19,2026-01-24,2026-03-25,31768838162860
1,2026-05-17,1,3,11,2014-07-17,2026-05-10,2026-05-18,2026-05-25,2026-05-29,31779116223319
1,2026-08-09,,3,3,2023-06-18,2026-08-07,2026-08-10,,,31786456692694
1,2026-04-11,,3,15,2010-07-19,2026-04-11,2026-04-11,,,31777560339040
1,2026-06-24,1,3,90,1935-11-19,2026-06-24,2026-06-24,2026-07-10,2026-07-11,31782483816212
1,2026-03-29,1,3,12,2013-06-20,2026-03-26,2026-03-30,2026-04-02,2026-04-02,31776451468405
1,2026-08-13,1,3,3,2023-01-23,2026-08-05,2026-08-13,2026-08-17,2026-09-02,31787326594739
1,2026-06-03,1,3,35,1991-04-24,2026-06-01,2026-06-03,,2026-06-16,31781011168335
1,2026-06-09,1,2,1,2026-05-26,2026-06-09,2026-06-10,2026-06-23,2026-07-24,31781096428357
1,2026-09-19,,3,67,1959-04-27,2026-09-19,2026-09-23,,,31790263201573
1,2026-05-06,,3,1,2024-09-30,2026-05-05,2026-05-06,,,31778163531908
1,2026-03-09,,3,85,1940-10-17,2026-03-08,2026-03-10,,,31773322485191
1,2026-03-12,1,3,1,2024-11-10,2026-03-07,2026-03-12,2026-03-20,2026-03-23,31773400244831
1,2026-07-12,1,3,8,2018-03-13,2026-07-10,2026-07-12,,2026-08-05,31783901810343
1,2026-05-23,1,2,3,2026-02-03,2026-05-22,2026-05-25,2026-05-31,2026-06-19,31779735858953
1,2026-05-06,1,3,2,2023-08-06,2026-05-04,2026-05-06,2026-05-09,2026-05-25,31779714355076
```

### `outputs/tables/pessoa_a/a1_amostra_exclusoes_04.csv`

- Git: `ignored` · `3.8 KB` · modified `2026-10-17 00:22 UTC` · 50 rows

```csv
HOSPITAL,DT_INTERNA,EVOLUCAO,TP_IDADE,NU_IDADE_N,DT_NASC,DT_SIN_PRI,DT_NOTIFIC,DT_EVOLUCA,DT_ENCERRA,NU_NOTIFIC
1,2025-12-24,9,2,4,2025-12-26,2026-04-09,2026-04-16,,2026-05-25,31776358797785
1,2025-10-03,9,3,4,2021-09-04,2026-03-01,2026-03-04,,2026-06-03,31780500876680
1,2025-12-16,9,2,6,2025-10-07,2026-04-08,2026-04-13,,2026-06-03,31780511592426
1,2025-12-17,,3,48,1977-06-27,2026-01-10,2026-01-12,,2026-04-02,31768219829649
1,2025-10-31,,3,67,1959-02-05,2026-03-16,2026-03-18,,,31773833215234
1,2025-11-01,,3,1,2025-03-26,2026-06-10,2026-06-11,,,31781197871583
1,2025-03-22,,3,75,1951-03-07,2026-03-24,2026-03-25,,,31774544007083
1,2025-01-14,,1,8,2026-01-14,2026-01-22,2026-02-26,,,31772103567239
1,2025-07-29,,2,6,2025-07-29,2026-01-19,2026-01-21,,,31769002628458
1,2025-09-11,,2,9,2025-09-11,2026-06-29,2026-06-29,,,31782995283941
1,2024-11-27,9,3,1,2024-11-11,2026-04-11,2026-04-19,,2026-05-26,31776623873074
1,2025-06-25,,3,1,2025-04-04,2026-05-30,2026-06-30,,2026-07-02,31782913329965
1,2025-12-27,,2,7,2025-12-26,2026-08-24,2026-08-31,,,31788210956301
1,2025-12-27,9,2,3,2025-12-26,2026-03-29,2026-03-30,,2026-05-25,31779819988812
1,2024-11-27,9,3,1,2024-11-11,2026-03-26,2026-03-31,,2026-05-26,31782076559440
1,2025-09-06,9,3,1,2024-11-07,2026-02-12,2026-02-18,,2026-05-25,31771513748972
1,2025-09-18,,3,12,2014-01-27,2026-06-29,2026-07-07,,2026-07-22,31783709799403
1,2024-03-08,,3,3,2022-11-17,2026-03-01,2026-03-12,,,31773333151517
1,2025-07-29,,2,9,2025-07-29,2026-04-18,2026-04-19,,,31776624396581
1,2025-08-08,,2,2,2025-06-13,2025-08-08,2025-08-11,,,31754941893170
1,2025-11-22,,3,63,1962-10-23,2025-11-20,2025-11-22,,,31774014430620
1,2025-08-19,,2,11,2024-09-29,2025-08-19,2025-08-22,,,31756133743688
1,2025-05-29,,2,3,2025-02-02,2025-05-27,2025-05-29,,2025-12-23,31748523312830
1,2025-07-06,,1,20,2025-06-10,2025-06-30,2025-07-06,,,31751895447999
1,2025-05-23,9,3,46,1978-12-12,2025-05-20,2025-05-24,,2025-05-25,31748089238562
1,2025-11-17,,2,8,2025-03-13,2025-11-10,2025-11-19,,,31764859064552
1,2025-05-31,9,3,1,2023-11-18,2025-05-28,2025-05-31,,2025-06-06,31749241564718
1,2025-01-24,9,3,54,1970-08-22,2025-01-16,2025-02-06,,2025-02-06,31738852792527
1,2025-03-29,,3,1,2023-06-23,2025-03-26,2025-03-31,,,31743606324329
1,2025-09-20,,3,75,1950-03-01,2025-09-20,2025-09-27,,2025-10-01,31759177531632
1,2025-08-26,,2,3,2025-05-07,2025-08-26,2025-08-27,,2025-09-01,31756299279917
1,2025-06-25,9,2,7,2024-11-04,2025-06-21,2025-06-25,,2025-07-14,31751467374225
1,2025-07-29,,3,2,2022-08-25,2025-07-28,2025-07-29,,,31754404310472
1,2025-06-19,,3,1,2023-11-14,2025-06-19,2025-06-21,,2025-06-21,31750504750935
1,2025-06-22,,3,3,2021-07-30,2025-06-22,2025-06-23,,,31750795034604
1,2025-07-03,9,1,1,2025-06-28,2025-06-29,2025-07-03,,2025-07-07,31751634307198
1,2025-07-23,,3,13,2011-12-11,2025-07-20,2025-08-08,,,31755001458106
1,2025-05-09,9,2,8,2024-09-07,2025-05-09,2025-06-16,,2025-06-16,31747153986065
1,2025-02-02,,3,1,2023-07-21,2025-01-31,2025-02-04,,,31738672439669
1,2025-04-01,,3,8,2016-12-01,2025-03-31,2025-04-01,,,31743515421873
1,2025-09-15,,2,1,2025-08-19,2025-09-12,2025-09-15,,,31760622681774
1,2025-06-05,9,3,6,2018-09-30,2025-06-01,2025-06-05,,2025-06-18,31749648905665
1,2025-10-23,,3,91,1934-06-23,2025-10-20,2025-10-29,,,31761741761758
1,2025-05-21,9,1,9,2025-05-02,2025-05-11,2025-05-21,,2025-07-10,31747839435766
1,2025-08-21,9,3,5,2019-08-29,2025-08-20,2025-08-26,,2025-09-08,31756211835539
1,2025-06-01,9,3,4,2020-10-29,2025-05-31,2025-06-02,,2025-06-04,31748863954462
1,2025-05-20,,3,75,1949-06-24,2025-05-19,2025-05-20,,,31747801163619
1,2025-07-23,9,3,71,1953-12-10,2025-07-23,2025-07-26,,2025-07-26,31753555880402
1,2025-10-22,9,3,1,2024-01-15,2025-10-22,2025-10-27,,,31761594784556
1,2025-06-19,9,3,1,2023-10-08,2025-06-19,2025-06-21,,2025-06-21,31750509631746
```

### `outputs/tables/pessoa_a/a1_amostra_exclusoes_05.csv`

- Git: `ignored` · `4.5 KB` · modified `2026-10-17 00:22 UTC` · 50 rows

```csv
HOSPITAL,DT_INTERNA,EVOLUCAO,TP_IDADE,NU_IDADE_N,DT_NASC,DT_SIN_PRI,DT_NOTIFIC,DT_EVOLUCA,DT_ENCERRA,NU_NOTIFIC
1,2025-09-24,3,2,8,2025-08-12,2026-04-11,2026-05-04,2026-04-16,2026-05-04,31777916441450
1,2025-12-03,3,2,1,2025-12-03,2026-01-09,2026-01-30,2026-03-11,2026-03-12,31769792468795
1,2025-12-18,3,3,77,1948-02-08,2026-01-05,2026-01-06,2026-01-06,2026-01-06,31768488161625
1,2025-10-31,3,2,4,2025-10-31,2026-02-04,2026-05-01,2026-04-07,2026-05-01,31777634956473
1,2025-12-30,3,3,50,1975-11-28,2026-01-09,2026-01-13,2026-01-21,2026-02-10,31770727069269
1,2025-12-11,3,3,62,1963-10-16,2026-01-30,2026-02-03,2026-02-13,2026-02-19,31770125136508
1,2025-02-10,3,3,52,1973-02-02,2025-02-09,2025-02-11,2025-02-18,2025-03-11,31739820410851
1,2025-06-27,3,3,81,1944-05-26,2025-06-27,2025-06-30,2025-07-03,2025-07-04,31751305140132
1,2025-08-16,3,2,4,2025-04-18,2025-08-09,2025-08-16,2025-10-11,2025-10-08,31755535974964
1,2025-05-15,3,3,57,1967-10-16,2025-05-08,2025-05-15,2025-05-29,2025-06-13,31747425704642
1,2025-04-10,3,3,68,1956-12-10,2025-04-10,2025-04-24,2025-04-10,2025-05-16,31747403476732
1,2025-03-05,3,3,71,1953-04-23,2025-02-15,2025-03-28,2025-03-05,2025-04-03,31743690196040
1,2025-03-08,3,3,9,2015-06-09,2025-03-07,2025-03-08,2025-03-08,2025-03-14,31741617511408
1,2025-04-17,3,3,54,1971-02-10,2025-04-17,2025-04-17,2025-04-17,2025-04-23,31745430231436
1,2025-07-24,3,3,98,1927-03-01,2025-07-22,2025-07-24,2025-07-31,2025-08-04,31753706945283
1,2025-01-13,3,3,94,1930-09-16,2025-01-03,2025-01-09,2025-02-07,2025-02-23,31737987292722
1,2025-08-06,3,3,37,1987-11-13,2025-08-06,2025-08-08,2025-08-11,2025-08-08,31754680600341
1,2025-04-06,3,3,15,2009-08-26,2025-04-01,2025-04-10,2025-04-10,2025-04-10,31745600659334
1,2025-12-23,3,2,1,2025-11-24,2025-12-20,2025-12-23,2025-12-26,2026-01-20,31766517607662
1,2025-09-02,3,3,36,1988-10-29,2025-09-02,2025-09-12,2025-09-08,2025-09-12,31757676072748
1,2025-07-01,3,3,66,1958-07-01,2025-06-30,2025-07-01,2025-09-04,2025-09-16,31751474441385
1,2025-01-09,3,3,92,1932-09-05,2025-01-09,2025-02-03,2025-01-22,2025-02-03,31738613590398
1,2025-01-20,3,2,5,2024-08-17,2025-01-17,2025-01-20,2025-01-27,2025-02-19,31737476808694
1,2025-07-05,3,3,54,1971-01-20,2025-07-05,2025-07-05,2025-07-07,2025-07-08,31751959045074
1,2025-06-05,3,3,86,1938-09-22,2025-06-04,2025-06-05,2025-06-12,2025-07-09,31752086047118
1,2025-06-20,3,3,57,1967-11-05,2025-06-15,2025-06-27,2025-07-02,2025-07-02,31751046185463
1,2025-05-20,3,3,73,1952-02-02,2025-05-20,2025-05-21,2025-05-22,2025-05-30,31747854379616
1,2025-06-25,3,3,77,1948-05-01,2025-06-25,2025-06-25,2025-07-27,2025-08-22,31750947402157
1,2025-07-18,3,3,78,1946-09-15,2025-07-16,2025-07-18,2025-08-13,2025-08-18,31752816212607
1,2025-01-30,3,3,63,1961-09-30,2025-01-10,2025-01-30,2025-03-08,2025-03-08,31738669486415
1,2025-05-07,3,3,56,1968-10-28,2025-05-07,2025-06-02,2025-06-09,2025-06-12,31748863298033
1,2025-05-30,3,3,73,1951-12-15,2025-05-28,2025-06-02,2025-07-15,2025-07-18,31749474500518
1,2025-04-22,3,2,8,2024-08-28,2025-04-10,2025-04-23,2025-04-23,2025-04-23,31745420160005
1,2025-11-16,3,3,1,2024-01-05,2025-11-13,2025-11-17,2025-11-25,2025-12-11,31764096943902
1,2025-04-11,3,3,65,1960-03-09,2025-04-09,2025-04-14,2025-05-05,2025-05-06,31744640890627
1,2025-06-24,3,3,76,1948-11-18,2025-06-18,2025-06-26,2025-06-28,2025-07-02,31751387763386
1,2025-10-20,3,3,60,1964-12-06,2025-10-17,2025-10-20,2025-10-23,2025-10-31,31761157628603
1,2025-03-14,3,3,43,1981-12-04,2025-03-10,2025-03-17,2025-04-05,2025-06-09,31742315828370
1,2025-04-08,3,3,38,1986-06-19,2025-04-05,2025-04-08,2025-04-08,2025-04-14,31745865241129
1,2025-06-11,3,3,68,1957-05-30,2025-06-10,2025-06-11,2025-06-24,2025-07-01,31749629091064
1,2025-12-03,3,3,54,1971-07-24,2025-11-28,2025-12-03,2025-12-07,2025-12-29,31765400192345
1,2025-09-19,3,3,85,1939-12-14,2025-09-19,2025-09-19,2025-10-08,2025-10-18,31761743862779
1,2025-05-07,3,3,1,2023-10-17,2025-05-05,2025-05-07,2025-05-28,2025-05-30,31747073511832
1,2025-12-23,3,3,57,1968-05-20,2025-12-10,2025-12-24,2026-01-27,2026-01-27,31766574194275
1,2025-08-21,3,3,73,1952-05-02,2025-08-18,2025-08-21,2025-09-17,2025-10-03,31755809317953
1,2025-05-13,3,3,93,1932-02-23,2025-05-09,2025-05-15,2025-06-21,2025-06-24,31747331606130
1,2025-01-22,3,3,87,1937-11-10,2025-01-22,2025-01-22,2025-02-01,2025-02-01,31739541405562
1,2025-08-15,3,3,51,1974-03-22,2025-08-15,2025-08-16,2025-08-19,2025-08-19,31755863690526
1,2025-07-04,3,3,32,1992-12-08,2025-06-27,2025-07-07,2025-07-07,2025-08-20,31755726935268
1,2025-11-22,3,3,65,1960-01-04,2025-11-22,2025-11-25,2026-01-07,2026-01-08,31764096261188
```

### `outputs/tables/pessoa_a/a1_amostra_exclusoes_sem_2020_2021_01.csv`

- Git: `ignored` · `3.5 KB` · modified `2026-10-17 00:51 UTC` · 50 rows

```csv
HOSPITAL,DT_INTERNA,EVOLUCAO,TP_IDADE,NU_IDADE_N,DT_NASC,DT_SIN_PRI,DT_NOTIFIC,DT_EVOLUCA,DT_ENCERRA,NU_NOTIFIC
,,,3,75,1950-11-02,2026-03-22,2026-03-23,,,31775652598724
2,,1,3,4,2022-03-03,2026-03-23,2026-03-29,2026-03-31,2026-06-11,31781205405890
,,1,2,8,2025-08-09,2026-04-18,2026-04-28,2026-04-19,2026-06-02,31780414044334
2,,1,3,50,1975-04-08,2026-03-07,2026-03-07,,2026-03-20,31776951547485
,,1,3,83,1942-12-21,2026-08-10,2026-08-13,,2026-08-13,31786648314248
,,9,3,8,2017-09-29,2026-03-25,2026-03-26,,2026-03-30,31776114768213
2,,,3,7,2019-02-21,2026-04-18,2026-04-22,,2026-04-26,31777485114556
,,1,2,4,2026-03-22,2026-07-12,2026-07-13,2026-07-21,2026-07-21,31784037049124
,,1,3,4,2021-09-27,2026-06-01,2026-06-15,,2026-07-23,31781782758352
,,,3,75,1950-09-14,2026-06-07,2026-06-08,,,31780925222220
,,,3,65,1960-07-08,2026-04-01,2026-04-14,,,31784125722808
,,,3,9,2016-07-22,2026-01-13,2026-01-18,,,31768751302378
2,,,2,7,2025-06-18,2026-01-04,2026-01-07,,,31767972796009
,,,3,5,2020-10-10,2026-08-18,2026-08-20,,,31787317509231
,,1,3,1,2025-01-15,2026-05-06,2026-05-06,,2026-05-08,31780258970676
9,,1,3,4,2021-09-06,2026-05-03,2026-05-03,2026-05-05,2026-07-03,31783105365899
2,,2,3,1,2025-03-11,2026-05-28,2026-06-09,2026-06-09,2026-06-16,31782311120470
,,1,2,6,2025-11-02,2026-05-20,2026-05-21,2026-06-08,2026-06-23,31782218952764
,,,2,7,2026-01-06,2026-08-02,2026-08-07,,,31786119085137
,,,3,73,1952-08-22,2026-04-04,2026-04-13,,,31776078195609
,,1,3,57,1968-08-22,2026-04-29,2026-04-30,,2026-05-12,31778069604877
,,1,3,1,2025-04-14,2026-04-24,2026-04-27,,2026-05-05,31777322020581
9,,1,3,40,1985-05-02,2026-01-30,2026-02-03,,2026-08-03,31772451218119
2,,1,2,2,2026-04-13,2026-06-19,2026-06-22,2026-06-26,2026-06-26,31782249136338
2,,1,3,6,2020-03-01,2026-05-03,2026-05-07,,2026-05-13,31778676513948
,,,3,9,2017-02-18,2026-06-23,2026-06-24,,,31782997221458
,,,2,2,2026-05-23,2026-07-06,2026-07-06,,,31783376982074
,,,3,80,1945-10-02,2026-02-28,2026-03-06,,2026-03-18,31772828882255
,,1,2,8,2025-11-28,2026-07-21,2026-07-24,,2026-07-24,31785406932822
,,1,2,6,2026-02-17,2026-08-07,2026-08-11,2026-08-12,2026-08-31,31787766202549
2,,2,3,12,2014-02-11,2026-03-19,2026-03-27,2026-03-27,2026-03-27,31774964608477
,,1,3,1,2024-10-01,2026-02-09,2026-02-09,,2026-02-13,31779580487653
2,,2,3,88,1937-10-25,2026-01-27,2026-01-31,2026-01-31,2026-02-12,31774289284081
2,,,3,2,2023-10-15,2026-04-22,2026-04-24,,2026-04-28,31777486180757
,,,3,66,1960-04-14,2026-08-08,2026-08-12,,,31786571794321
,,,3,1,2024-10-13,2026-06-11,2026-06-17,,,31781707959452
,,1,3,57,1969-05-11,2026-08-14,2026-08-17,2026-08-19,2026-08-19,31786973020085
9,,,3,46,1979-11-27,2026-09-01,2026-09-02,,,31788371070901
,,1,3,1,2024-12-23,2026-04-11,2026-04-16,,2026-06-08,31776357800729
,,,3,1,2025-01-04,2026-04-05,2026-04-16,,,31776343591581
2,,1,3,41,1984-05-03,2026-02-22,2026-03-02,2026-02-24,2026-03-02,31772423427061
,,1,2,11,2025-08-30,2026-07-23,2026-07-24,,2026-08-03,31784914226565
,,1,2,4,2025-09-06,2026-01-12,2026-01-12,2026-01-26,2026-02-06,31769008935928
,,,3,35,1991-08-07,2026-08-15,2026-08-18,,,31787060140830
,,,3,2,2024-05-29,2026-08-21,2026-08-28,,,31789074988249
2,,1,3,90,1935-08-24,2026-01-07,2026-01-09,2026-01-09,2026-01-14,31768403627553
,,1,3,67,1959-01-29,2026-06-15,2026-06-16,2026-06-19,2026-06-25,31781696854761
2,,1,3,42,1983-12-15,2026-01-14,2026-02-08,,2026-02-08,31770572532065
2,,2,3,64,1961-07-01,2026-02-21,2026-02-21,2026-02-21,2026-02-21,31773350909558
,,,3,58,1968-06-08,2026-07-16,2026-07-21,,2026-08-10,31784646474693
```

### `outputs/tables/pessoa_a/a1_amostra_exclusoes_sem_2020_2021_02.csv`

- Git: `ignored` · `3.6 KB` · modified `2026-10-17 00:51 UTC` · 50 rows

```csv
HOSPITAL,DT_INTERNA,EVOLUCAO,TP_IDADE,NU_IDADE_N,DT_NASC,DT_SIN_PRI,DT_NOTIFIC,DT_EVOLUCA,DT_ENCERRA,NU_NOTIFIC
1,,1,2,8,2025-08-10,2026-04-01,2026-04-15,,2026-04-21,31777549715837
1,,1,3,77,1949-05-26,2026-07-12,2026-07-12,2026-07-15,2026-07-17,31788874096772
1,,1,3,7,2018-08-31,2026-01-10,2026-01-12,2026-01-28,2026-02-09,31770647469632
1,,,3,3,2023-04-20,2026-09-04,2026-09-09,,,31788975169679
1,,1,2,3,2025-11-10,2026-02-06,2026-02-07,2026-02-20,2026-06-10,31773940312126
1,,1,3,1,2024-09-24,2026-07-04,2026-08-26,2026-08-11,2026-08-26,31787751835649
1,,1,3,43,1982-11-27,2026-02-21,2026-02-27,2026-03-02,2026-03-05,31772219564355
1,,1,2,1,2025-12-04,2026-01-08,2026-01-12,2026-01-21,2026-01-26,31769453667829
1,,1,2,11,2025-03-16,2026-02-20,2026-02-23,2026-02-24,2026-04-13,31771838270995
1,,1,3,31,1994-11-08,2026-09-06,2026-09-09,2026-09-16,2026-09-17,31789563351861
1,,1,3,62,1963-11-04,2026-02-11,2026-02-13,2026-02-20,2026-03-04,31771008239682
1,,,1,7,2026-05-12,2026-05-19,2026-05-21,,,31779467820819
1,,,3,3,2022-12-09,2026-09-03,2026-09-05,,,31788620734654
1,,,3,4,2021-11-21,2026-07-30,2026-07-31,,,31786458971825
1,,,3,2,2024-03-30,2026-08-01,2026-08-04,,,31785867861406
1,,1,3,2,2023-09-24,2026-07-10,2026-07-20,2026-07-14,2026-07-22,31784748275602
1,,1,3,2,2024-05-11,2026-09-03,2026-09-10,2026-09-15,2026-09-18,31789065947469
1,,,3,2,2024-06-17,2026-09-01,2026-09-02,,,31788382629475
1,,,3,2,2024-06-05,2026-08-14,2026-08-19,,,31787172228431
1,,,3,2,2024-06-25,2026-06-26,2026-07-10,,,31783704794838
1,,,3,1,2024-08-25,2026-06-20,2026-06-22,,,31782152025297
1,,,3,1,2024-12-14,2026-05-03,2026-05-07,,,31778183597383
1,,1,3,1,2025-06-09,2026-08-21,2026-08-24,2026-09-03,2026-09-22,31787583741919
1,,,3,1,2025-07-27,2026-07-28,2026-07-29,,,31785360853298
1,,,2,10,2025-08-16,2026-06-01,2026-06-04,,,31780575267248
1,,1,2,8,2025-08-22,2026-04-25,2026-04-29,2026-05-01,2026-05-25,31777465516478
1,,1,2,7,2025-08-18,2026-03-23,2026-03-28,,2026-04-01,31774888210371
1,,1,3,73,1952-05-15,2026-04-25,2026-04-27,2026-04-30,2026-05-04,31778092086325
1,,1,3,2,2023-11-03,2026-07-07,2026-07-09,2026-07-13,2026-07-14,31783942348556
1,,,3,2,2023-10-10,2026-04-13,2026-04-13,,,31776091074476
1,,1,3,2,2023-11-06,2026-08-25,2026-08-25,,2026-09-11,31787918509080
1,,1,3,75,1950-11-05,2026-06-04,2026-06-11,,2026-06-16,31781178224317
1,,1,3,1,2024-12-27,2026-03-12,2026-03-15,2026-03-16,2026-03-16,31773662225812
1,,2,3,46,1980-03-30,2026-05-04,2026-05-07,2026-05-14,2026-05-15,31778770573608
1,,1,3,2,2024-03-22,2026-04-22,2026-04-29,2026-05-02,2026-05-07,31781007905994
1,,1,3,37,1989-08-03,2026-08-24,2026-08-25,2026-09-04,2026-09-25,31789485848987
1,,,3,50,1975-05-26,2026-01-17,2026-01-18,,2026-01-22,31769099934860
1,,1,3,74,1952-02-15,2026-07-20,2026-08-03,2026-08-03,2026-08-18,31786461727931
1,,1,3,81,1944-05-31,2026-03-27,2026-04-09,2026-04-15,2026-04-20,31775740797449
1,,1,3,2,2024-01-08,2026-09-01,2026-09-03,2026-09-05,2026-09-08,31789128973635
1,,1,3,1,2024-10-17,2026-08-18,2026-08-24,,2026-09-10,31789062515336
1,,1,3,2,2024-01-29,2026-03-17,2026-03-18,2026-03-26,2026-04-03,31775250713894
1,,1,3,27,1998-11-17,2026-05-01,2026-05-09,,2026-05-18,31778336961281
1,,1,3,57,1968-08-22,2026-01-19,2026-02-04,,2026-02-04,31770645711921
1,,,3,2,2024-05-21,2026-08-04,2026-08-06,,2026-08-07,31786039467922
1,,1,3,78,1947-11-07,2026-06-19,2026-06-26,,2026-07-08,31782494985225
1,,1,3,1,2024-02-22,2026-01-06,2026-01-08,2026-01-13,2026-01-14,31768314692248
1,,1,2,8,2025-12-25,2026-08-30,2026-09-02,2026-09-09,2026-09-11,31788527556568
1,,1,3,1,2024-07-23,2026-01-30,2026-02-05,2026-02-13,2026-02-24,31770378778543
1,,,2,7,2026-01-11,2026-09-07,2026-09-11,,,31789140997184
```

### `outputs/tables/pessoa_a/a1_amostra_exclusoes_sem_2020_2021_03.csv`

- Git: `ignored` · `4.1 KB` · modified `2026-10-17 00:51 UTC` · 50 rows

```csv
HOSPITAL,DT_INTERNA,EVOLUCAO,TP_IDADE,NU_IDADE_N,DT_NASC,DT_SIN_PRI,DT_NOTIFIC,DT_EVOLUCA,DT_ENCERRA,NU_NOTIFIC
1,2026-06-11,1,2,1,2026-05-02,2026-06-02,2026-06-11,2026-06-19,2026-06-19,31781201987679
1,2026-06-15,,3,37,1989-04-04,2026-06-15,2026-06-17,,,31782407823707
1,2026-03-10,1,3,4,2021-10-06,2026-03-09,2026-03-14,,,31773493207022
1,2026-03-18,1,1,11,2026-03-07,2026-03-18,2026-03-23,2026-04-14,2026-04-15,31774542694487
1,2026-08-18,,3,75,1950-09-09,2026-08-08,2026-08-18,,,31787085791388
1,2026-03-10,1,3,78,1947-11-10,2026-03-10,2026-03-10,2026-03-16,2026-03-16,31773441569320
1,2026-05-27,,3,1,2025-03-11,2026-05-19,2026-05-26,,,31780065930274
1,2026-05-08,,2,0,2025-05-13,2026-05-05,2026-05-08,,,31779901434401
1,2026-06-15,,3,66,1960-06-13,2026-06-14,2026-06-16,,,31781629359036
1,2026-05-23,,3,15,2011-04-14,2026-05-23,2026-05-24,,,31780947295202
1,2026-07-07,1,3,4,2021-07-14,2026-07-03,2026-07-09,2026-07-11,2026-07-17,31783622594901
1,2026-04-04,,3,32,1993-09-15,2026-04-04,2026-04-04,,,31779149516127
1,2026-05-13,1,2,6,2025-11-17,2026-05-12,2026-05-13,2026-05-15,2026-05-21,31779376399165
1,2026-05-15,,3,74,1952-04-18,2026-05-15,2026-05-16,,,31779137099882
1,2026-03-19,1,3,11,2014-09-18,2026-03-19,2026-03-20,2026-03-28,2026-04-06,31775493343412
1,2026-05-19,,3,75,1950-12-19,2026-05-16,2026-05-22,,,31779804314537
1,2026-09-08,,2,5,2026-03-21,2026-09-08,2026-09-09,,,31788967146868
1,2026-06-02,1,2,1,2026-04-22,2026-05-27,2026-06-03,2026-06-16,2026-06-19,31780508092246
1,2026-04-14,1,2,5,2025-11-23,2026-04-14,2026-05-04,2026-04-14,2026-05-04,31777902324367
1,2026-04-22,1,3,31,1995-01-25,2026-04-19,2026-04-23,2026-05-04,2026-05-11,31777581635868
1,2026-03-28,,3,1,2024-10-25,2026-03-08,2026-03-28,,,31774869565386
1,2026-04-11,1,3,5,2020-06-26,2026-04-05,2026-04-11,2026-04-13,2026-04-17,31776433120192
1,2026-05-26,1,3,12,2013-08-27,2026-05-26,2026-05-28,2026-05-29,2026-06-03,31780063755400
1,2026-03-26,,3,78,1947-12-30,2026-03-26,2026-03-31,,,31775052422525
1,2026-06-02,1,2,4,2026-02-04,2026-06-02,2026-06-03,2026-06-09,2026-07-29,31785339117793
1,2026-08-25,2,3,65,1961-06-06,2026-08-25,2026-08-25,2026-08-27,2026-09-01,31790273405307
1,2026-05-18,1,3,58,1967-11-07,2026-05-16,2026-05-18,2026-05-25,2026-05-25,31779716421577
1,2026-06-20,1,3,25,2001-02-10,2026-06-18,2026-06-20,2026-07-01,2026-07-07,31783419856968
1,2026-05-26,1,3,2,2023-10-10,2026-05-21,2026-05-26,2026-05-30,2026-05-30,31781122407541
1,2026-05-09,1,3,64,1962-02-11,2026-05-08,2026-05-12,2026-05-20,2026-05-20,31778874675119
1,2026-04-13,1,3,80,1946-03-11,2026-04-01,2026-04-16,2026-05-07,2026-05-08,31776340279767
1,2026-03-24,1,3,25,2000-04-11,2026-03-24,2026-03-25,2026-04-03,2026-04-13,31774465391980
1,2026-05-05,1,3,1,2024-12-13,2026-05-05,2026-05-05,2026-05-10,2026-05-11,31778065923802
1,2026-07-27,1,2,3,2026-04-14,2026-07-15,2026-07-27,2026-08-07,2026-08-10,31785175448633
1,2026-01-18,1,3,81,1945-01-17,2026-01-18,2026-01-19,2026-01-24,2026-03-25,31768838162860
1,2026-05-17,1,3,11,2014-07-17,2026-05-10,2026-05-18,2026-05-25,2026-05-29,31779116223319
1,2026-08-09,,3,3,2023-06-18,2026-08-07,2026-08-10,,,31786456692694
1,2026-04-11,,3,15,2010-07-19,2026-04-11,2026-04-11,,,31777560339040
1,2026-06-24,1,3,90,1935-11-19,2026-06-24,2026-06-24,2026-07-10,2026-07-11,31782483816212
1,2026-03-29,1,3,12,2013-06-20,2026-03-26,2026-03-30,2026-04-02,2026-04-02,31776451468405
1,2026-08-13,1,3,3,2023-01-23,2026-08-05,2026-08-13,2026-08-17,2026-09-02,31787326594739
1,2026-06-03,1,3,35,1991-04-24,2026-06-01,2026-06-03,,2026-06-16,31781011168335
1,2026-06-09,1,2,1,2026-05-26,2026-06-09,2026-06-10,2026-06-23,2026-07-24,31781096428357
1,2026-09-19,,3,67,1959-04-27,2026-09-19,2026-09-23,,,31790263201573
1,2026-05-06,,3,1,2024-09-30,2026-05-05,2026-05-06,,,31778163531908
1,2026-03-09,,3,85,1940-10-17,2026-03-08,2026-03-10,,,31773322485191
1,2026-03-12,1,3,1,2024-11-10,2026-03-07,2026-03-12,2026-03-20,2026-03-23,31773400244831
1,2026-07-12,1,3,8,2018-03-13,2026-07-10,2026-07-12,,2026-08-05,31783901810343
1,2026-05-23,1,2,3,2026-02-03,2026-05-22,2026-05-25,2026-05-31,2026-06-19,31779735858953
1,2026-05-06,1,3,2,2023-08-06,2026-05-04,2026-05-06,2026-05-09,2026-05-25,31779714355076
```

### `outputs/tables/pessoa_a/a1_amostra_exclusoes_sem_2020_2021_04.csv`

- Git: `ignored` · `3.8 KB` · modified `2026-10-17 00:51 UTC` · 50 rows

```csv
HOSPITAL,DT_INTERNA,EVOLUCAO,TP_IDADE,NU_IDADE_N,DT_NASC,DT_SIN_PRI,DT_NOTIFIC,DT_EVOLUCA,DT_ENCERRA,NU_NOTIFIC
1,2025-12-24,9,2,4,2025-12-26,2026-04-09,2026-04-16,,2026-05-25,31776358797785
1,2025-10-03,9,3,4,2021-09-04,2026-03-01,2026-03-04,,2026-06-03,31780500876680
1,2025-12-16,9,2,6,2025-10-07,2026-04-08,2026-04-13,,2026-06-03,31780511592426
1,2025-12-17,,3,48,1977-06-27,2026-01-10,2026-01-12,,2026-04-02,31768219829649
1,2025-10-31,,3,67,1959-02-05,2026-03-16,2026-03-18,,,31773833215234
1,2025-11-01,,3,1,2025-03-26,2026-06-10,2026-06-11,,,31781197871583
1,2025-03-22,,3,75,1951-03-07,2026-03-24,2026-03-25,,,31774544007083
1,2025-01-14,,1,8,2026-01-14,2026-01-22,2026-02-26,,,31772103567239
1,2025-07-29,,2,6,2025-07-29,2026-01-19,2026-01-21,,,31769002628458
1,2025-09-11,,2,9,2025-09-11,2026-06-29,2026-06-29,,,31782995283941
1,2024-11-27,9,3,1,2024-11-11,2026-04-11,2026-04-19,,2026-05-26,31776623873074
1,2025-06-25,,3,1,2025-04-04,2026-05-30,2026-06-30,,2026-07-02,31782913329965
1,2025-12-27,,2,7,2025-12-26,2026-08-24,2026-08-31,,,31788210956301
1,2025-12-27,9,2,3,2025-12-26,2026-03-29,2026-03-30,,2026-05-25,31779819988812
1,2024-11-27,9,3,1,2024-11-11,2026-03-26,2026-03-31,,2026-05-26,31782076559440
1,2025-09-06,9,3,1,2024-11-07,2026-02-12,2026-02-18,,2026-05-25,31771513748972
1,2025-09-18,,3,12,2014-01-27,2026-06-29,2026-07-07,,2026-07-22,31783709799403
1,2024-03-08,,3,3,2022-11-17,2026-03-01,2026-03-12,,,31773333151517
1,2025-07-29,,2,9,2025-07-29,2026-04-18,2026-04-19,,,31776624396581
1,2025-08-08,,2,2,2025-06-13,2025-08-08,2025-08-11,,,31754941893170
1,2025-11-22,,3,63,1962-10-23,2025-11-20,2025-11-22,,,31774014430620
1,2025-08-19,,2,11,2024-09-29,2025-08-19,2025-08-22,,,31756133743688
1,2025-05-29,,2,3,2025-02-02,2025-05-27,2025-05-29,,2025-12-23,31748523312830
1,2025-07-06,,1,20,2025-06-10,2025-06-30,2025-07-06,,,31751895447999
1,2025-05-23,9,3,46,1978-12-12,2025-05-20,2025-05-24,,2025-05-25,31748089238562
1,2025-11-17,,2,8,2025-03-13,2025-11-10,2025-11-19,,,31764859064552
1,2025-05-31,9,3,1,2023-11-18,2025-05-28,2025-05-31,,2025-06-06,31749241564718
1,2025-01-24,9,3,54,1970-08-22,2025-01-16,2025-02-06,,2025-02-06,31738852792527
1,2025-03-29,,3,1,2023-06-23,2025-03-26,2025-03-31,,,31743606324329
1,2025-09-20,,3,75,1950-03-01,2025-09-20,2025-09-27,,2025-10-01,31759177531632
1,2025-08-26,,2,3,2025-05-07,2025-08-26,2025-08-27,,2025-09-01,31756299279917
1,2025-06-25,9,2,7,2024-11-04,2025-06-21,2025-06-25,,2025-07-14,31751467374225
1,2025-07-29,,3,2,2022-08-25,2025-07-28,2025-07-29,,,31754404310472
1,2025-06-19,,3,1,2023-11-14,2025-06-19,2025-06-21,,2025-06-21,31750504750935
1,2025-06-22,,3,3,2021-07-30,2025-06-22,2025-06-23,,,31750795034604
1,2025-07-03,9,1,1,2025-06-28,2025-06-29,2025-07-03,,2025-07-07,31751634307198
1,2025-07-23,,3,13,2011-12-11,2025-07-20,2025-08-08,,,31755001458106
1,2025-05-09,9,2,8,2024-09-07,2025-05-09,2025-06-16,,2025-06-16,31747153986065
1,2025-02-02,,3,1,2023-07-21,2025-01-31,2025-02-04,,,31738672439669
1,2025-04-01,,3,8,2016-12-01,2025-03-31,2025-04-01,,,31743515421873
1,2025-09-15,,2,1,2025-08-19,2025-09-12,2025-09-15,,,31760622681774
1,2025-06-05,9,3,6,2018-09-30,2025-06-01,2025-06-05,,2025-06-18,31749648905665
1,2025-10-23,,3,91,1934-06-23,2025-10-20,2025-10-29,,,31761741761758
1,2025-05-21,9,1,9,2025-05-02,2025-05-11,2025-05-21,,2025-07-10,31747839435766
1,2025-08-21,9,3,5,2019-08-29,2025-08-20,2025-08-26,,2025-09-08,31756211835539
1,2025-06-01,9,3,4,2020-10-29,2025-05-31,2025-06-02,,2025-06-04,31748863954462
1,2025-05-20,,3,75,1949-06-24,2025-05-19,2025-05-20,,,31747801163619
1,2025-07-23,9,3,71,1953-12-10,2025-07-23,2025-07-26,,2025-07-26,31753555880402
1,2025-10-22,9,3,1,2024-01-15,2025-10-22,2025-10-27,,,31761594784556
1,2025-06-19,9,3,1,2023-10-08,2025-06-19,2025-06-21,,2025-06-21,31750509631746
```

### `outputs/tables/pessoa_a/a1_amostra_exclusoes_sem_2020_2021_05.csv`

- Git: `ignored` · `4.5 KB` · modified `2026-10-17 00:51 UTC` · 50 rows

```csv
HOSPITAL,DT_INTERNA,EVOLUCAO,TP_IDADE,NU_IDADE_N,DT_NASC,DT_SIN_PRI,DT_NOTIFIC,DT_EVOLUCA,DT_ENCERRA,NU_NOTIFIC
1,2025-09-24,3,2,8,2025-08-12,2026-04-11,2026-05-04,2026-04-16,2026-05-04,31777916441450
1,2025-12-03,3,2,1,2025-12-03,2026-01-09,2026-01-30,2026-03-11,2026-03-12,31769792468795
1,2025-12-18,3,3,77,1948-02-08,2026-01-05,2026-01-06,2026-01-06,2026-01-06,31768488161625
1,2025-10-31,3,2,4,2025-10-31,2026-02-04,2026-05-01,2026-04-07,2026-05-01,31777634956473
1,2025-12-30,3,3,50,1975-11-28,2026-01-09,2026-01-13,2026-01-21,2026-02-10,31770727069269
1,2025-12-11,3,3,62,1963-10-16,2026-01-30,2026-02-03,2026-02-13,2026-02-19,31770125136508
1,2025-02-10,3,3,52,1973-02-02,2025-02-09,2025-02-11,2025-02-18,2025-03-11,31739820410851
1,2025-06-27,3,3,81,1944-05-26,2025-06-27,2025-06-30,2025-07-03,2025-07-04,31751305140132
1,2025-08-16,3,2,4,2025-04-18,2025-08-09,2025-08-16,2025-10-11,2025-10-08,31755535974964
1,2025-05-15,3,3,57,1967-10-16,2025-05-08,2025-05-15,2025-05-29,2025-06-13,31747425704642
1,2025-04-10,3,3,68,1956-12-10,2025-04-10,2025-04-24,2025-04-10,2025-05-16,31747403476732
1,2025-03-05,3,3,71,1953-04-23,2025-02-15,2025-03-28,2025-03-05,2025-04-03,31743690196040
1,2025-03-08,3,3,9,2015-06-09,2025-03-07,2025-03-08,2025-03-08,2025-03-14,31741617511408
1,2025-04-17,3,3,54,1971-02-10,2025-04-17,2025-04-17,2025-04-17,2025-04-23,31745430231436
1,2025-07-24,3,3,98,1927-03-01,2025-07-22,2025-07-24,2025-07-31,2025-08-04,31753706945283
1,2025-01-13,3,3,94,1930-09-16,2025-01-03,2025-01-09,2025-02-07,2025-02-23,31737987292722
1,2025-08-06,3,3,37,1987-11-13,2025-08-06,2025-08-08,2025-08-11,2025-08-08,31754680600341
1,2025-04-06,3,3,15,2009-08-26,2025-04-01,2025-04-10,2025-04-10,2025-04-10,31745600659334
1,2025-12-23,3,2,1,2025-11-24,2025-12-20,2025-12-23,2025-12-26,2026-01-20,31766517607662
1,2025-09-02,3,3,36,1988-10-29,2025-09-02,2025-09-12,2025-09-08,2025-09-12,31757676072748
1,2025-07-01,3,3,66,1958-07-01,2025-06-30,2025-07-01,2025-09-04,2025-09-16,31751474441385
1,2025-01-09,3,3,92,1932-09-05,2025-01-09,2025-02-03,2025-01-22,2025-02-03,31738613590398
1,2025-01-20,3,2,5,2024-08-17,2025-01-17,2025-01-20,2025-01-27,2025-02-19,31737476808694
1,2025-07-05,3,3,54,1971-01-20,2025-07-05,2025-07-05,2025-07-07,2025-07-08,31751959045074
1,2025-06-05,3,3,86,1938-09-22,2025-06-04,2025-06-05,2025-06-12,2025-07-09,31752086047118
1,2025-06-20,3,3,57,1967-11-05,2025-06-15,2025-06-27,2025-07-02,2025-07-02,31751046185463
1,2025-05-20,3,3,73,1952-02-02,2025-05-20,2025-05-21,2025-05-22,2025-05-30,31747854379616
1,2025-06-25,3,3,77,1948-05-01,2025-06-25,2025-06-25,2025-07-27,2025-08-22,31750947402157
1,2025-07-18,3,3,78,1946-09-15,2025-07-16,2025-07-18,2025-08-13,2025-08-18,31752816212607
1,2025-01-30,3,3,63,1961-09-30,2025-01-10,2025-01-30,2025-03-08,2025-03-08,31738669486415
1,2025-05-07,3,3,56,1968-10-28,2025-05-07,2025-06-02,2025-06-09,2025-06-12,31748863298033
1,2025-05-30,3,3,73,1951-12-15,2025-05-28,2025-06-02,2025-07-15,2025-07-18,31749474500518
1,2025-04-22,3,2,8,2024-08-28,2025-04-10,2025-04-23,2025-04-23,2025-04-23,31745420160005
1,2025-11-16,3,3,1,2024-01-05,2025-11-13,2025-11-17,2025-11-25,2025-12-11,31764096943902
1,2025-04-11,3,3,65,1960-03-09,2025-04-09,2025-04-14,2025-05-05,2025-05-06,31744640890627
1,2025-06-24,3,3,76,1948-11-18,2025-06-18,2025-06-26,2025-06-28,2025-07-02,31751387763386
1,2025-10-20,3,3,60,1964-12-06,2025-10-17,2025-10-20,2025-10-23,2025-10-31,31761157628603
1,2025-03-14,3,3,43,1981-12-04,2025-03-10,2025-03-17,2025-04-05,2025-06-09,31742315828370
1,2025-04-08,3,3,38,1986-06-19,2025-04-05,2025-04-08,2025-04-08,2025-04-14,31745865241129
1,2025-06-11,3,3,68,1957-05-30,2025-06-10,2025-06-11,2025-06-24,2025-07-01,31749629091064
1,2025-12-03,3,3,54,1971-07-24,2025-11-28,2025-12-03,2025-12-07,2025-12-29,31765400192345
1,2025-09-19,3,3,85,1939-12-14,2025-09-19,2025-09-19,2025-10-08,2025-10-18,31761743862779
1,2025-05-07,3,3,1,2023-10-17,2025-05-05,2025-05-07,2025-05-28,2025-05-30,31747073511832
1,2025-12-23,3,3,57,1968-05-20,2025-12-10,2025-12-24,2026-01-27,2026-01-27,31766574194275
1,2025-08-21,3,3,73,1952-05-02,2025-08-18,2025-08-21,2025-09-17,2025-10-03,31755809317953
1,2025-05-13,3,3,93,1932-02-23,2025-05-09,2025-05-15,2025-06-21,2025-06-24,31747331606130
1,2025-01-22,3,3,87,1937-11-10,2025-01-22,2025-01-22,2025-02-01,2025-02-01,31739541405562
1,2025-08-15,3,3,51,1974-03-22,2025-08-15,2025-08-16,2025-08-19,2025-08-19,31755863690526
1,2025-07-04,3,3,32,1992-12-08,2025-06-27,2025-07-07,2025-07-07,2025-08-20,31755726935268
1,2025-11-22,3,3,65,1960-01-04,2025-11-22,2025-11-25,2026-01-07,2026-01-08,31764096261188
```

### `outputs/tables/pessoa_a/a1_amostra_exclusoes_todos_2019_2025_01.csv`

- Git: `ignored` · `3.5 KB` · modified `2026-10-17 00:50 UTC` · 50 rows

```csv
HOSPITAL,DT_INTERNA,EVOLUCAO,TP_IDADE,NU_IDADE_N,DT_NASC,DT_SIN_PRI,DT_NOTIFIC,DT_EVOLUCA,DT_ENCERRA,NU_NOTIFIC
,,,3,75,1950-11-02,2026-03-22,2026-03-23,,,31775652598724
2,,1,3,4,2022-03-03,2026-03-23,2026-03-29,2026-03-31,2026-06-11,31781205405890
,,1,2,8,2025-08-09,2026-04-18,2026-04-28,2026-04-19,2026-06-02,31780414044334
2,,1,3,50,1975-04-08,2026-03-07,2026-03-07,,2026-03-20,31776951547485
,,1,3,83,1942-12-21,2026-08-10,2026-08-13,,2026-08-13,31786648314248
,,9,3,8,2017-09-29,2026-03-25,2026-03-26,,2026-03-30,31776114768213
2,,,3,7,2019-02-21,2026-04-18,2026-04-22,,2026-04-26,31777485114556
,,1,2,4,2026-03-22,2026-07-12,2026-07-13,2026-07-21,2026-07-21,31784037049124
,,1,3,4,2021-09-27,2026-06-01,2026-06-15,,2026-07-23,31781782758352
,,,3,75,1950-09-14,2026-06-07,2026-06-08,,,31780925222220
,,,3,65,1960-07-08,2026-04-01,2026-04-14,,,31784125722808
,,,3,9,2016-07-22,2026-01-13,2026-01-18,,,31768751302378
2,,,2,7,2025-06-18,2026-01-04,2026-01-07,,,31767972796009
,,,3,5,2020-10-10,2026-08-18,2026-08-20,,,31787317509231
,,1,3,1,2025-01-15,2026-05-06,2026-05-06,,2026-05-08,31780258970676
9,,1,3,4,2021-09-06,2026-05-03,2026-05-03,2026-05-05,2026-07-03,31783105365899
2,,2,3,1,2025-03-11,2026-05-28,2026-06-09,2026-06-09,2026-06-16,31782311120470
,,1,2,6,2025-11-02,2026-05-20,2026-05-21,2026-06-08,2026-06-23,31782218952764
,,,2,7,2026-01-06,2026-08-02,2026-08-07,,,31786119085137
,,,3,73,1952-08-22,2026-04-04,2026-04-13,,,31776078195609
,,1,3,57,1968-08-22,2026-04-29,2026-04-30,,2026-05-12,31778069604877
,,1,3,1,2025-04-14,2026-04-24,2026-04-27,,2026-05-05,31777322020581
9,,1,3,40,1985-05-02,2026-01-30,2026-02-03,,2026-08-03,31772451218119
2,,1,2,2,2026-04-13,2026-06-19,2026-06-22,2026-06-26,2026-06-26,31782249136338
2,,1,3,6,2020-03-01,2026-05-03,2026-05-07,,2026-05-13,31778676513948
,,,3,9,2017-02-18,2026-06-23,2026-06-24,,,31782997221458
,,,2,2,2026-05-23,2026-07-06,2026-07-06,,,31783376982074
,,,3,80,1945-10-02,2026-02-28,2026-03-06,,2026-03-18,31772828882255
,,1,2,8,2025-11-28,2026-07-21,2026-07-24,,2026-07-24,31785406932822
,,1,2,6,2026-02-17,2026-08-07,2026-08-11,2026-08-12,2026-08-31,31787766202549
2,,2,3,12,2014-02-11,2026-03-19,2026-03-27,2026-03-27,2026-03-27,31774964608477
,,1,3,1,2024-10-01,2026-02-09,2026-02-09,,2026-02-13,31779580487653
2,,2,3,88,1937-10-25,2026-01-27,2026-01-31,2026-01-31,2026-02-12,31774289284081
2,,,3,2,2023-10-15,2026-04-22,2026-04-24,,2026-04-28,31777486180757
,,,3,66,1960-04-14,2026-08-08,2026-08-12,,,31786571794321
,,,3,1,2024-10-13,2026-06-11,2026-06-17,,,31781707959452
,,1,3,57,1969-05-11,2026-08-14,2026-08-17,2026-08-19,2026-08-19,31786973020085
9,,,3,46,1979-11-27,2026-09-01,2026-09-02,,,31788371070901
,,1,3,1,2024-12-23,2026-04-11,2026-04-16,,2026-06-08,31776357800729
,,,3,1,2025-01-04,2026-04-05,2026-04-16,,,31776343591581
2,,1,3,41,1984-05-03,2026-02-22,2026-03-02,2026-02-24,2026-03-02,31772423427061
,,1,2,11,2025-08-30,2026-07-23,2026-07-24,,2026-08-03,31784914226565
,,1,2,4,2025-09-06,2026-01-12,2026-01-12,2026-01-26,2026-02-06,31769008935928
,,,3,35,1991-08-07,2026-08-15,2026-08-18,,,31787060140830
,,,3,2,2024-05-29,2026-08-21,2026-08-28,,,31789074988249
2,,1,3,90,1935-08-24,2026-01-07,2026-01-09,2026-01-09,2026-01-14,31768403627553
,,1,3,67,1959-01-29,2026-06-15,2026-06-16,2026-06-19,2026-06-25,31781696854761
2,,1,3,42,1983-12-15,2026-01-14,2026-02-08,,2026-02-08,31770572532065
2,,2,3,64,1961-07-01,2026-02-21,2026-02-21,2026-02-21,2026-02-21,31773350909558
,,,3,58,1968-06-08,2026-07-16,2026-07-21,,2026-08-10,31784646474693
```

### `outputs/tables/pessoa_a/a1_amostra_exclusoes_todos_2019_2025_02.csv`

- Git: `ignored` · `3.6 KB` · modified `2026-10-17 00:50 UTC` · 50 rows

```csv
HOSPITAL,DT_INTERNA,EVOLUCAO,TP_IDADE,NU_IDADE_N,DT_NASC,DT_SIN_PRI,DT_NOTIFIC,DT_EVOLUCA,DT_ENCERRA,NU_NOTIFIC
1,,1,2,8,2025-08-10,2026-04-01,2026-04-15,,2026-04-21,31777549715837
1,,1,3,77,1949-05-26,2026-07-12,2026-07-12,2026-07-15,2026-07-17,31788874096772
1,,1,3,7,2018-08-31,2026-01-10,2026-01-12,2026-01-28,2026-02-09,31770647469632
1,,,3,3,2023-04-20,2026-09-04,2026-09-09,,,31788975169679
1,,1,2,3,2025-11-10,2026-02-06,2026-02-07,2026-02-20,2026-06-10,31773940312126
1,,1,3,1,2024-09-24,2026-07-04,2026-08-26,2026-08-11,2026-08-26,31787751835649
1,,1,3,43,1982-11-27,2026-02-21,2026-02-27,2026-03-02,2026-03-05,31772219564355
1,,1,2,1,2025-12-04,2026-01-08,2026-01-12,2026-01-21,2026-01-26,31769453667829
1,,1,2,11,2025-03-16,2026-02-20,2026-02-23,2026-02-24,2026-04-13,31771838270995
1,,1,3,31,1994-11-08,2026-09-06,2026-09-09,2026-09-16,2026-09-17,31789563351861
1,,1,3,62,1963-11-04,2026-02-11,2026-02-13,2026-02-20,2026-03-04,31771008239682
1,,,1,7,2026-05-12,2026-05-19,2026-05-21,,,31779467820819
1,,,3,3,2022-12-09,2026-09-03,2026-09-05,,,31788620734654
1,,,3,4,2021-11-21,2026-07-30,2026-07-31,,,31786458971825
1,,,3,2,2024-03-30,2026-08-01,2026-08-04,,,31785867861406
1,,1,3,2,2023-09-24,2026-07-10,2026-07-20,2026-07-14,2026-07-22,31784748275602
1,,1,3,2,2024-05-11,2026-09-03,2026-09-10,2026-09-15,2026-09-18,31789065947469
1,,,3,2,2024-06-17,2026-09-01,2026-09-02,,,31788382629475
1,,,3,2,2024-06-05,2026-08-14,2026-08-19,,,31787172228431
1,,,3,2,2024-06-25,2026-06-26,2026-07-10,,,31783704794838
1,,,3,1,2024-08-25,2026-06-20,2026-06-22,,,31782152025297
1,,,3,1,2024-12-14,2026-05-03,2026-05-07,,,31778183597383
1,,1,3,1,2025-06-09,2026-08-21,2026-08-24,2026-09-03,2026-09-22,31787583741919
1,,,3,1,2025-07-27,2026-07-28,2026-07-29,,,31785360853298
1,,,2,10,2025-08-16,2026-06-01,2026-06-04,,,31780575267248
1,,1,2,8,2025-08-22,2026-04-25,2026-04-29,2026-05-01,2026-05-25,31777465516478
1,,1,2,7,2025-08-18,2026-03-23,2026-03-28,,2026-04-01,31774888210371
1,,1,3,73,1952-05-15,2026-04-25,2026-04-27,2026-04-30,2026-05-04,31778092086325
1,,1,3,2,2023-11-03,2026-07-07,2026-07-09,2026-07-13,2026-07-14,31783942348556
1,,,3,2,2023-10-10,2026-04-13,2026-04-13,,,31776091074476
1,,1,3,2,2023-11-06,2026-08-25,2026-08-25,,2026-09-11,31787918509080
1,,1,3,75,1950-11-05,2026-06-04,2026-06-11,,2026-06-16,31781178224317
1,,1,3,1,2024-12-27,2026-03-12,2026-03-15,2026-03-16,2026-03-16,31773662225812
1,,2,3,46,1980-03-30,2026-05-04,2026-05-07,2026-05-14,2026-05-15,31778770573608
1,,1,3,2,2024-03-22,2026-04-22,2026-04-29,2026-05-02,2026-05-07,31781007905994
1,,1,3,37,1989-08-03,2026-08-24,2026-08-25,2026-09-04,2026-09-25,31789485848987
1,,,3,50,1975-05-26,2026-01-17,2026-01-18,,2026-01-22,31769099934860
1,,1,3,74,1952-02-15,2026-07-20,2026-08-03,2026-08-03,2026-08-18,31786461727931
1,,1,3,81,1944-05-31,2026-03-27,2026-04-09,2026-04-15,2026-04-20,31775740797449
1,,1,3,2,2024-01-08,2026-09-01,2026-09-03,2026-09-05,2026-09-08,31789128973635
1,,1,3,1,2024-10-17,2026-08-18,2026-08-24,,2026-09-10,31789062515336
1,,1,3,2,2024-01-29,2026-03-17,2026-03-18,2026-03-26,2026-04-03,31775250713894
1,,1,3,27,1998-11-17,2026-05-01,2026-05-09,,2026-05-18,31778336961281
1,,1,3,57,1968-08-22,2026-01-19,2026-02-04,,2026-02-04,31770645711921
1,,,3,2,2024-05-21,2026-08-04,2026-08-06,,2026-08-07,31786039467922
1,,1,3,78,1947-11-07,2026-06-19,2026-06-26,,2026-07-08,31782494985225
1,,1,3,1,2024-02-22,2026-01-06,2026-01-08,2026-01-13,2026-01-14,31768314692248
1,,1,2,8,2025-12-25,2026-08-30,2026-09-02,2026-09-09,2026-09-11,31788527556568
1,,1,3,1,2024-07-23,2026-01-30,2026-02-05,2026-02-13,2026-02-24,31770378778543
1,,,2,7,2026-01-11,2026-09-07,2026-09-11,,,31789140997184
```

### `outputs/tables/pessoa_a/a1_amostra_exclusoes_todos_2019_2025_03.csv`

- Git: `ignored` · `4.1 KB` · modified `2026-10-17 00:50 UTC` · 50 rows

```csv
HOSPITAL,DT_INTERNA,EVOLUCAO,TP_IDADE,NU_IDADE_N,DT_NASC,DT_SIN_PRI,DT_NOTIFIC,DT_EVOLUCA,DT_ENCERRA,NU_NOTIFIC
1,2026-06-11,1,2,1,2026-05-02,2026-06-02,2026-06-11,2026-06-19,2026-06-19,31781201987679
1,2026-06-15,,3,37,1989-04-04,2026-06-15,2026-06-17,,,31782407823707
1,2026-03-10,1,3,4,2021-10-06,2026-03-09,2026-03-14,,,31773493207022
1,2026-03-18,1,1,11,2026-03-07,2026-03-18,2026-03-23,2026-04-14,2026-04-15,31774542694487
1,2026-08-18,,3,75,1950-09-09,2026-08-08,2026-08-18,,,31787085791388
1,2026-03-10,1,3,78,1947-11-10,2026-03-10,2026-03-10,2026-03-16,2026-03-16,31773441569320
1,2026-05-27,,3,1,2025-03-11,2026-05-19,2026-05-26,,,31780065930274
1,2026-05-08,,2,0,2025-05-13,2026-05-05,2026-05-08,,,31779901434401
1,2026-06-15,,3,66,1960-06-13,2026-06-14,2026-06-16,,,31781629359036
1,2026-05-23,,3,15,2011-04-14,2026-05-23,2026-05-24,,,31780947295202
1,2026-07-07,1,3,4,2021-07-14,2026-07-03,2026-07-09,2026-07-11,2026-07-17,31783622594901
1,2026-04-04,,3,32,1993-09-15,2026-04-04,2026-04-04,,,31779149516127
1,2026-05-13,1,2,6,2025-11-17,2026-05-12,2026-05-13,2026-05-15,2026-05-21,31779376399165
1,2026-05-15,,3,74,1952-04-18,2026-05-15,2026-05-16,,,31779137099882
1,2026-03-19,1,3,11,2014-09-18,2026-03-19,2026-03-20,2026-03-28,2026-04-06,31775493343412
1,2026-05-19,,3,75,1950-12-19,2026-05-16,2026-05-22,,,31779804314537
1,2026-09-08,,2,5,2026-03-21,2026-09-08,2026-09-09,,,31788967146868
1,2026-06-02,1,2,1,2026-04-22,2026-05-27,2026-06-03,2026-06-16,2026-06-19,31780508092246
1,2026-04-14,1,2,5,2025-11-23,2026-04-14,2026-05-04,2026-04-14,2026-05-04,31777902324367
1,2026-04-22,1,3,31,1995-01-25,2026-04-19,2026-04-23,2026-05-04,2026-05-11,31777581635868
1,2026-03-28,,3,1,2024-10-25,2026-03-08,2026-03-28,,,31774869565386
1,2026-04-11,1,3,5,2020-06-26,2026-04-05,2026-04-11,2026-04-13,2026-04-17,31776433120192
1,2026-05-26,1,3,12,2013-08-27,2026-05-26,2026-05-28,2026-05-29,2026-06-03,31780063755400
1,2026-03-26,,3,78,1947-12-30,2026-03-26,2026-03-31,,,31775052422525
1,2026-06-02,1,2,4,2026-02-04,2026-06-02,2026-06-03,2026-06-09,2026-07-29,31785339117793
1,2026-08-25,2,3,65,1961-06-06,2026-08-25,2026-08-25,2026-08-27,2026-09-01,31790273405307
1,2026-05-18,1,3,58,1967-11-07,2026-05-16,2026-05-18,2026-05-25,2026-05-25,31779716421577
1,2026-06-20,1,3,25,2001-02-10,2026-06-18,2026-06-20,2026-07-01,2026-07-07,31783419856968
1,2026-05-26,1,3,2,2023-10-10,2026-05-21,2026-05-26,2026-05-30,2026-05-30,31781122407541
1,2026-05-09,1,3,64,1962-02-11,2026-05-08,2026-05-12,2026-05-20,2026-05-20,31778874675119
1,2026-04-13,1,3,80,1946-03-11,2026-04-01,2026-04-16,2026-05-07,2026-05-08,31776340279767
1,2026-03-24,1,3,25,2000-04-11,2026-03-24,2026-03-25,2026-04-03,2026-04-13,31774465391980
1,2026-05-05,1,3,1,2024-12-13,2026-05-05,2026-05-05,2026-05-10,2026-05-11,31778065923802
1,2026-07-27,1,2,3,2026-04-14,2026-07-15,2026-07-27,2026-08-07,2026-08-10,31785175448633
1,2026-01-18,1,3,81,1945-01-17,2026-01-18,2026-01-19,2026-01-24,2026-03-25,31768838162860
1,2026-05-17,1,3,11,2014-07-17,2026-05-10,2026-05-18,2026-05-25,2026-05-29,31779116223319
1,2026-08-09,,3,3,2023-06-18,2026-08-07,2026-08-10,,,31786456692694
1,2026-04-11,,3,15,2010-07-19,2026-04-11,2026-04-11,,,31777560339040
1,2026-06-24,1,3,90,1935-11-19,2026-06-24,2026-06-24,2026-07-10,2026-07-11,31782483816212
1,2026-03-29,1,3,12,2013-06-20,2026-03-26,2026-03-30,2026-04-02,2026-04-02,31776451468405
1,2026-08-13,1,3,3,2023-01-23,2026-08-05,2026-08-13,2026-08-17,2026-09-02,31787326594739
1,2026-06-03,1,3,35,1991-04-24,2026-06-01,2026-06-03,,2026-06-16,31781011168335
1,2026-06-09,1,2,1,2026-05-26,2026-06-09,2026-06-10,2026-06-23,2026-07-24,31781096428357
1,2026-09-19,,3,67,1959-04-27,2026-09-19,2026-09-23,,,31790263201573
1,2026-05-06,,3,1,2024-09-30,2026-05-05,2026-05-06,,,31778163531908
1,2026-03-09,,3,85,1940-10-17,2026-03-08,2026-03-10,,,31773322485191
1,2026-03-12,1,3,1,2024-11-10,2026-03-07,2026-03-12,2026-03-20,2026-03-23,31773400244831
1,2026-07-12,1,3,8,2018-03-13,2026-07-10,2026-07-12,,2026-08-05,31783901810343
1,2026-05-23,1,2,3,2026-02-03,2026-05-22,2026-05-25,2026-05-31,2026-06-19,31779735858953
1,2026-05-06,1,3,2,2023-08-06,2026-05-04,2026-05-06,2026-05-09,2026-05-25,31779714355076
```

### `outputs/tables/pessoa_a/a1_amostra_exclusoes_todos_2019_2025_04.csv`

- Git: `ignored` · `3.8 KB` · modified `2026-10-17 00:50 UTC` · 50 rows

```csv
HOSPITAL,DT_INTERNA,EVOLUCAO,TP_IDADE,NU_IDADE_N,DT_NASC,DT_SIN_PRI,DT_NOTIFIC,DT_EVOLUCA,DT_ENCERRA,NU_NOTIFIC
1,2020-06-21,,2,7,2026-01-27,2026-08-08,2026-08-09,,,31787231962439
1,2025-12-24,9,2,4,2025-12-26,2026-04-09,2026-04-16,,2026-05-25,31776358797785
1,2025-10-03,9,3,4,2021-09-04,2026-03-01,2026-03-04,,2026-06-03,31780500876680
1,2025-12-16,9,2,6,2025-10-07,2026-04-08,2026-04-13,,2026-06-03,31780511592426
1,2025-12-17,,3,48,1977-06-27,2026-01-10,2026-01-12,,2026-04-02,31768219829649
1,2025-10-31,,3,67,1959-02-05,2026-03-16,2026-03-18,,,31773833215234
1,2025-11-01,,3,1,2025-03-26,2026-06-10,2026-06-11,,,31781197871583
1,2025-03-22,,3,75,1951-03-07,2026-03-24,2026-03-25,,,31774544007083
1,2025-01-14,,1,8,2026-01-14,2026-01-22,2026-02-26,,,31772103567239
1,2025-07-29,,2,6,2025-07-29,2026-01-19,2026-01-21,,,31769002628458
1,2025-09-11,,2,9,2025-09-11,2026-06-29,2026-06-29,,,31782995283941
1,2024-11-27,9,3,1,2024-11-11,2026-04-11,2026-04-19,,2026-05-26,31776623873074
1,2025-06-25,,3,1,2025-04-04,2026-05-30,2026-06-30,,2026-07-02,31782913329965
1,2025-12-27,,2,7,2025-12-26,2026-08-24,2026-08-31,,,31788210956301
1,2025-12-27,9,2,3,2025-12-26,2026-03-29,2026-03-30,,2026-05-25,31779819988812
1,2024-11-27,9,3,1,2024-11-11,2026-03-26,2026-03-31,,2026-05-26,31782076559440
1,2025-09-06,9,3,1,2024-11-07,2026-02-12,2026-02-18,,2026-05-25,31771513748972
1,2025-09-18,,3,12,2014-01-27,2026-06-29,2026-07-07,,2026-07-22,31783709799403
1,2024-03-08,,3,3,2022-11-17,2026-03-01,2026-03-12,,,31773333151517
1,2025-07-29,,2,9,2025-07-29,2026-04-18,2026-04-19,,,31776624396581
1,2025-08-08,,2,2,2025-06-13,2025-08-08,2025-08-11,,,31754941893170
1,2025-11-22,,3,63,1962-10-23,2025-11-20,2025-11-22,,,31774014430620
1,2025-08-19,,2,11,2024-09-29,2025-08-19,2025-08-22,,,31756133743688
1,2025-05-29,,2,3,2025-02-02,2025-05-27,2025-05-29,,2025-12-23,31748523312830
1,2025-07-06,,1,20,2025-06-10,2025-06-30,2025-07-06,,,31751895447999
1,2025-05-23,9,3,46,1978-12-12,2025-05-20,2025-05-24,,2025-05-25,31748089238562
1,2025-11-17,,2,8,2025-03-13,2025-11-10,2025-11-19,,,31764859064552
1,2025-05-31,9,3,1,2023-11-18,2025-05-28,2025-05-31,,2025-06-06,31749241564718
1,2025-01-24,9,3,54,1970-08-22,2025-01-16,2025-02-06,,2025-02-06,31738852792527
1,2025-03-29,,3,1,2023-06-23,2025-03-26,2025-03-31,,,31743606324329
1,2025-09-20,,3,75,1950-03-01,2025-09-20,2025-09-27,,2025-10-01,31759177531632
1,2025-08-26,,2,3,2025-05-07,2025-08-26,2025-08-27,,2025-09-01,31756299279917
1,2025-06-25,9,2,7,2024-11-04,2025-06-21,2025-06-25,,2025-07-14,31751467374225
1,2025-07-29,,3,2,2022-08-25,2025-07-28,2025-07-29,,,31754404310472
1,2025-06-19,,3,1,2023-11-14,2025-06-19,2025-06-21,,2025-06-21,31750504750935
1,2025-06-22,,3,3,2021-07-30,2025-06-22,2025-06-23,,,31750795034604
1,2025-07-03,9,1,1,2025-06-28,2025-06-29,2025-07-03,,2025-07-07,31751634307198
1,2025-07-23,,3,13,2011-12-11,2025-07-20,2025-08-08,,,31755001458106
1,2025-05-09,9,2,8,2024-09-07,2025-05-09,2025-06-16,,2025-06-16,31747153986065
1,2025-02-02,,3,1,2023-07-21,2025-01-31,2025-02-04,,,31738672439669
1,2025-04-01,,3,8,2016-12-01,2025-03-31,2025-04-01,,,31743515421873
1,2025-09-15,,2,1,2025-08-19,2025-09-12,2025-09-15,,,31760622681774
1,2025-06-05,9,3,6,2018-09-30,2025-06-01,2025-06-05,,2025-06-18,31749648905665
1,2025-10-23,,3,91,1934-06-23,2025-10-20,2025-10-29,,,31761741761758
1,2025-05-21,9,1,9,2025-05-02,2025-05-11,2025-05-21,,2025-07-10,31747839435766
1,2025-08-21,9,3,5,2019-08-29,2025-08-20,2025-08-26,,2025-09-08,31756211835539
1,2025-06-01,9,3,4,2020-10-29,2025-05-31,2025-06-02,,2025-06-04,31748863954462
1,2025-05-20,,3,75,1949-06-24,2025-05-19,2025-05-20,,,31747801163619
1,2025-07-23,9,3,71,1953-12-10,2025-07-23,2025-07-26,,2025-07-26,31753555880402
1,2025-10-22,9,3,1,2024-01-15,2025-10-22,2025-10-27,,,31761594784556
```

### `outputs/tables/pessoa_a/a1_amostra_exclusoes_todos_2019_2025_05.csv`

- Git: `ignored` · `4.5 KB` · modified `2026-10-17 00:50 UTC` · 50 rows

```csv
HOSPITAL,DT_INTERNA,EVOLUCAO,TP_IDADE,NU_IDADE_N,DT_NASC,DT_SIN_PRI,DT_NOTIFIC,DT_EVOLUCA,DT_ENCERRA,NU_NOTIFIC
1,2025-09-24,3,2,8,2025-08-12,2026-04-11,2026-05-04,2026-04-16,2026-05-04,31777916441450
1,2025-12-03,3,2,1,2025-12-03,2026-01-09,2026-01-30,2026-03-11,2026-03-12,31769792468795
1,2025-12-18,3,3,77,1948-02-08,2026-01-05,2026-01-06,2026-01-06,2026-01-06,31768488161625
1,2025-10-31,3,2,4,2025-10-31,2026-02-04,2026-05-01,2026-04-07,2026-05-01,31777634956473
1,2025-12-30,3,3,50,1975-11-28,2026-01-09,2026-01-13,2026-01-21,2026-02-10,31770727069269
1,2025-12-11,3,3,62,1963-10-16,2026-01-30,2026-02-03,2026-02-13,2026-02-19,31770125136508
1,2025-02-10,3,3,52,1973-02-02,2025-02-09,2025-02-11,2025-02-18,2025-03-11,31739820410851
1,2025-06-27,3,3,81,1944-05-26,2025-06-27,2025-06-30,2025-07-03,2025-07-04,31751305140132
1,2025-08-16,3,2,4,2025-04-18,2025-08-09,2025-08-16,2025-10-11,2025-10-08,31755535974964
1,2025-05-15,3,3,57,1967-10-16,2025-05-08,2025-05-15,2025-05-29,2025-06-13,31747425704642
1,2025-04-10,3,3,68,1956-12-10,2025-04-10,2025-04-24,2025-04-10,2025-05-16,31747403476732
1,2025-03-05,3,3,71,1953-04-23,2025-02-15,2025-03-28,2025-03-05,2025-04-03,31743690196040
1,2025-03-08,3,3,9,2015-06-09,2025-03-07,2025-03-08,2025-03-08,2025-03-14,31741617511408
1,2025-04-17,3,3,54,1971-02-10,2025-04-17,2025-04-17,2025-04-17,2025-04-23,31745430231436
1,2025-07-24,3,3,98,1927-03-01,2025-07-22,2025-07-24,2025-07-31,2025-08-04,31753706945283
1,2025-01-13,3,3,94,1930-09-16,2025-01-03,2025-01-09,2025-02-07,2025-02-23,31737987292722
1,2025-08-06,3,3,37,1987-11-13,2025-08-06,2025-08-08,2025-08-11,2025-08-08,31754680600341
1,2025-04-06,3,3,15,2009-08-26,2025-04-01,2025-04-10,2025-04-10,2025-04-10,31745600659334
1,2025-12-23,3,2,1,2025-11-24,2025-12-20,2025-12-23,2025-12-26,2026-01-20,31766517607662
1,2025-09-02,3,3,36,1988-10-29,2025-09-02,2025-09-12,2025-09-08,2025-09-12,31757676072748
1,2025-07-01,3,3,66,1958-07-01,2025-06-30,2025-07-01,2025-09-04,2025-09-16,31751474441385
1,2025-01-09,3,3,92,1932-09-05,2025-01-09,2025-02-03,2025-01-22,2025-02-03,31738613590398
1,2025-01-20,3,2,5,2024-08-17,2025-01-17,2025-01-20,2025-01-27,2025-02-19,31737476808694
1,2025-07-05,3,3,54,1971-01-20,2025-07-05,2025-07-05,2025-07-07,2025-07-08,31751959045074
1,2025-06-05,3,3,86,1938-09-22,2025-06-04,2025-06-05,2025-06-12,2025-07-09,31752086047118
1,2025-06-20,3,3,57,1967-11-05,2025-06-15,2025-06-27,2025-07-02,2025-07-02,31751046185463
1,2025-05-20,3,3,73,1952-02-02,2025-05-20,2025-05-21,2025-05-22,2025-05-30,31747854379616
1,2025-06-25,3,3,77,1948-05-01,2025-06-25,2025-06-25,2025-07-27,2025-08-22,31750947402157
1,2025-07-18,3,3,78,1946-09-15,2025-07-16,2025-07-18,2025-08-13,2025-08-18,31752816212607
1,2025-01-30,3,3,63,1961-09-30,2025-01-10,2025-01-30,2025-03-08,2025-03-08,31738669486415
1,2025-05-07,3,3,56,1968-10-28,2025-05-07,2025-06-02,2025-06-09,2025-06-12,31748863298033
1,2025-05-30,3,3,73,1951-12-15,2025-05-28,2025-06-02,2025-07-15,2025-07-18,31749474500518
1,2025-04-22,3,2,8,2024-08-28,2025-04-10,2025-04-23,2025-04-23,2025-04-23,31745420160005
1,2025-11-16,3,3,1,2024-01-05,2025-11-13,2025-11-17,2025-11-25,2025-12-11,31764096943902
1,2025-04-11,3,3,65,1960-03-09,2025-04-09,2025-04-14,2025-05-05,2025-05-06,31744640890627
1,2025-06-24,3,3,76,1948-11-18,2025-06-18,2025-06-26,2025-06-28,2025-07-02,31751387763386
1,2025-10-20,3,3,60,1964-12-06,2025-10-17,2025-10-20,2025-10-23,2025-10-31,31761157628603
1,2025-03-14,3,3,43,1981-12-04,2025-03-10,2025-03-17,2025-04-05,2025-06-09,31742315828370
1,2025-04-08,3,3,38,1986-06-19,2025-04-05,2025-04-08,2025-04-08,2025-04-14,31745865241129
1,2025-06-11,3,3,68,1957-05-30,2025-06-10,2025-06-11,2025-06-24,2025-07-01,31749629091064
1,2025-12-03,3,3,54,1971-07-24,2025-11-28,2025-12-03,2025-12-07,2025-12-29,31765400192345
1,2025-09-19,3,3,85,1939-12-14,2025-09-19,2025-09-19,2025-10-08,2025-10-18,31761743862779
1,2025-05-07,3,3,1,2023-10-17,2025-05-05,2025-05-07,2025-05-28,2025-05-30,31747073511832
1,2025-12-23,3,3,57,1968-05-20,2025-12-10,2025-12-24,2026-01-27,2026-01-27,31766574194275
1,2025-08-21,3,3,73,1952-05-02,2025-08-18,2025-08-21,2025-09-17,2025-10-03,31755809317953
1,2025-05-13,3,3,93,1932-02-23,2025-05-09,2025-05-15,2025-06-21,2025-06-24,31747331606130
1,2025-01-22,3,3,87,1937-11-10,2025-01-22,2025-01-22,2025-02-01,2025-02-01,31739541405562
1,2025-08-15,3,3,51,1974-03-22,2025-08-15,2025-08-16,2025-08-19,2025-08-19,31755863690526
1,2025-07-04,3,3,32,1992-12-08,2025-06-27,2025-07-07,2025-07-07,2025-08-20,31755726935268
1,2025-11-22,3,3,65,1960-01-04,2025-11-22,2025-11-25,2026-01-07,2026-01-08,31764096261188
```

### `outputs/tables/pessoa_a/a1_tabela_codigos.csv`

- Git: `ignored` · `3.8 KB` · modified `2026-10-17 00:22 UTC` · 32 rows

```csv
codigo,campo,esperado,1917,1918,1941,2009,2011,2012,2016,2017,2018,2019,2020,2021,2022,2023,2024,2025,2026,2027,2028,2029,2031,2032,2033,2034,2050,2052,2055,2056,2092,2098,2099,sem_data
1,HOSPITAL,True,4,1,4,1,1,2,1,2,11,47543,1076364,1657389,536133,265669,253367,315615,210437,7,4,9,2,1,3,1,1,1,1,1,1,2,1,72078
2,HOSPITAL,True,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,102956
9,HOSPITAL,True,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,10066
<vazio>,HOSPITAL,False,0,0,0,0,0,0,0,0,0,2,11,4,2,2,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,119207
1,EVOLUCAO,True,1,0,1,1,1,2,0,2,10,38294,705704,1062927,389548,217669,210358,268686,165785,6,4,3,2,1,0,0,0,1,0,0,1,1,1,141523
2,EVOLUCAO,True,0,0,0,0,0,0,1,0,0,5221,274119,417293,86433,23037,19120,21227,9743,0,0,0,0,0,0,0,0,0,0,0,0,0,0,79814
3,EVOLUCAO,True,0,0,0,0,0,0,0,0,0,8,15414,21305,13727,7724,7220,8253,5014,0,0,0,0,0,0,0,0,0,0,0,0,0,0,7784
9,EVOLUCAO,True,0,0,1,0,0,0,0,0,0,1340,20385,38603,12552,5528,4212,5561,4454,1,0,3,0,0,0,1,0,0,0,0,0,1,0,10928
<vazio>,EVOLUCAO,False,3,1,2,0,0,0,0,0,1,2682,60753,117266,33875,11713,12457,11889,25442,0,0,3,0,0,3,0,1,0,1,1,0,0,0,64258
1,TP_IDADE,True,0,0,0,0,0,0,0,0,0,1754,3866,5920,4181,3258,3638,4771,2724,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1695
2,TP_IDADE,True,1,0,1,0,1,0,0,0,2,12580,18283,43407,54697,60504,60545,81218,57591,1,0,1,0,0,0,0,0,0,1,0,0,0,0,16103
3,TP_IDADE,True,3,1,3,1,0,2,1,2,9,33211,1054226,1608067,477257,201909,189184,229627,150123,6,4,8,2,1,3,1,1,1,0,1,1,2,1,286509
1,UTI,True,0,0,0,0,1,1,0,1,8,17130,332253,508784,147058,73955,73262,85580,53968,0,0,0,0,0,0,0,0,0,0,0,0,0,0,26453
2,UTI,True,4,1,4,1,0,1,1,0,2,29183,629864,960616,325691,167145,160537,208066,141221,4,4,9,2,1,2,0,1,0,1,1,1,2,1,42265
9,UTI,True,0,0,0,0,0,0,0,1,0,327,25070,34232,8046,2778,3241,3033,1930,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2650
<vazio>,UTI,False,0,0,0,0,0,0,0,0,1,905,89188,153762,55340,21793,16327,18937,13319,3,0,0,0,0,1,1,0,1,0,0,0,0,0,232939
1,FEBRE,True,1,0,4,0,0,1,1,1,7,41899,617699,877980,266070,152246,157260,195656,137085,5,3,7,1,1,0,0,0,0,0,1,1,2,1,145310
2,FEBRE,True,3,0,0,1,1,1,0,1,4,5269,313591,483203,166184,76126,69569,94455,57941,2,1,2,1,0,2,0,1,1,1,0,0,0,0,66099
9,FEBRE,True,0,0,0,0,0,0,0,0,0,213,15552,19160,5317,1574,987,981,670,0,0,0,0,0,0,0,0,0,0,0,0,0,0,5986
<vazio>,FEBRE,False,0,1,0,0,0,0,0,0,0,164,129533,277051,98564,35725,25551,24524,14742,0,0,0,0,0,1,1,0,0,0,0,0,0,0,86912
1,TOSSE,True,2,1,3,0,0,2,0,1,7,44036,725450,1127588,366618,201006,198279,255199,172114,7,4,8,2,1,1,0,1,0,1,1,1,2,1,179090
2,TOSSE,True,2,0,1,1,1,0,1,1,4,3131,229341,308468,97958,41498,38961,46422,29378,0,0,1,0,0,1,0,0,1,0,0,0,0,0,45857
9,TOSSE,True,0,0,0,0,0,0,0,0,0,183,13179,15175,3874,1118,798,653,515,0,0,0,0,0,0,0,0,0,0,0,0,0,0,5360
<vazio>,TOSSE,False,0,0,0,0,0,0,0,0,0,195,108405,206163,67685,22049,15329,13342,8431,0,0,0,0,0,1,1,0,0,0,0,0,0,0,74000
1,DISPNEIA,True,3,1,4,0,0,1,1,2,8,39368,745718,1170804,326207,174529,168783,215847,143136,5,3,6,1,0,1,0,1,1,1,1,1,0,1,145095
2,DISPNEIA,True,0,0,0,1,1,1,0,0,3,7548,213596,280704,120980,56624,56905,75066,51206,2,1,2,1,1,1,0,0,0,0,0,0,1,0,64414
9,DISPNEIA,True,0,0,0,0,0,0,0,0,0,260,11518,13196,4164,1506,1070,1141,721,0,0,0,0,0,0,0,0,0,0,0,0,0,0,5483
<vazio>,DISPNEIA,False,1,0,0,0,0,0,0,0,0,369,105543,192690,84784,33012,26609,23562,15375,0,0,1,0,0,1,1,0,0,0,0,0,1,0,89315
1,SATURACAO,True,1,0,1,0,0,0,1,2,8,32213,605830,1068602,283505,143613,138419,173998,114940,5,3,6,1,0,1,1,1,1,1,1,0,0,0,101837
2,SATURACAO,True,2,0,3,1,1,2,0,0,3,13811,298619,321592,140591,74378,76794,104460,71428,2,1,3,1,1,1,0,0,0,0,0,1,1,1,80891
9,SATURACAO,True,0,0,0,0,0,0,0,0,0,713,18502,17516,4769,1715,1411,1626,1235,0,0,0,0,0,0,0,0,0,0,0,0,0,0,9393
<vazio>,SATURACAO,False,1,1,0,0,0,0,0,0,0,808,153424,249684,107270,45965,36743,35532,22835,0,0,0,0,0,1,0,0,0,0,0,0,1,0,112186
```

### `outputs/tables/pessoa_a/a1_waterfall.csv`

- Git: `ignored` · `555 B` · modified `2026-10-17 00:22 UTC` · 6 rows

```csv
ordem,filtro,regra,n_excluido,n_restante,pct_restante
0,Base completa,—,0,4666910,100.0
1,Hospitalização confirmada,HOSPITAL = 1,232253,4434657,95.02
2,Data de internação válida,"DT_INTERNA parseável, ≥ 2009-01-01 e ≤ hoje",72133,4362524,93.48
3,Período analítico,"ano(DT_INTERNA) em [2022, 2023, 2024, 2025]",2991740,1370784,29.37
4,Evolução encerrada,"EVOLUCAO em ['1', '2', '3'] (9/ausente fora)",97786,1272998,27.28
5,Alvo binário definido,"EVOLUCAO em {cura, óbito}; óbito por outras causas separado",36923,1236075,26.49
```

### `outputs/tables/pessoa_a/a1_waterfall_sem_2020_2021.csv`

- Git: `ignored` · `562 B` · modified `2026-10-17 00:51 UTC` · 6 rows

```csv
ordem,filtro,regra,n_excluido,n_restante,pct_restante
0,Base completa,—,0,4666910,100.0
1,Hospitalização confirmada,HOSPITAL = 1,232253,4434657,95.02
2,Data de internação válida,"DT_INTERNA parseável, ≥ 2009-01-01 e ≤ hoje",72133,4362524,93.48
3,Período analítico,"ano(DT_INTERNA) em [2019, 2022, 2023, 2024, 2025]",2944197,1418327,30.39
4,Evolução encerrada,"EVOLUCAO em ['1', '2', '3'] (9/ausente fora)",101808,1316519,28.21
5,Alvo binário definido,"EVOLUCAO em {cura, óbito}; óbito por outras causas separado",36931,1279588,27.42
```

### `outputs/tables/pessoa_a/a1_waterfall_todos_2019_2025.csv`

- Git: `ignored` · `573 B` · modified `2026-10-17 00:50 UTC` · 6 rows

```csv
ordem,filtro,regra,n_excluido,n_restante,pct_restante
0,Base completa,—,0,4666910,100.0
1,Hospitalização confirmada,HOSPITAL = 1,232253,4434657,95.02
2,Data de internação válida,"DT_INTERNA parseável, ≥ 2009-01-01 e ≤ hoje",72133,4362524,93.48
3,Período analítico,"ano(DT_INTERNA) em [2019, 2020, 2021, 2022, 2023, 2024, 2025]",210444,4152080,88.97
4,Evolução encerrada,"EVOLUCAO em ['1', '2', '3'] (9/ausente fora)",338815,3813265,81.71
5,Alvo binário definido,"EVOLUCAO em {cura, óbito}; óbito por outras causas separado",73650,3739615,80.13
```

### `outputs/tables/pessoa_a/a2_campos_inexistentes_por_ano.csv`

- Git: `ignored` · `15.3 KB` · modified `2026-10-17 00:25 UTC` · 87 rows (first 60 shown)

```csv
coluna,1917,1918,1941,2009,2011,2012,2016,2017,2018,2019,2020,2021,2022,2023,2024,2025,2026,2027,2028,2029,2031,2032,2033,2034,2050,2052,2055,2056,2092,2098,2099
ANTIVIRAL,0.0,0.0,25.0,0.0,0.0,0.0,0.0,0.0,0.0,1.13,11.58,15.88,17.3,16.77,17.39,12.49,10.8,28.57,0.0,11.11,0.0,0.0,0.0,100.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0
ASMA,100.0,100.0,50.0,0.0,100.0,50.0,0.0,0.0,90.91,61.8,56.81,64.64,63.52,68.3,68.09,66.9,68.52,85.71,75.0,77.78,50.0,100.0,66.67,100.0,0.0,100.0,100.0,100.0,100.0,100.0,0.0
AVE_SUINO,50.0,100.0,25.0,0.0,0.0,0.0,0.0,0.0,27.27,3.36,15.97,16.85,14.98,14.34,14.19,11.6,10.22,28.57,0.0,22.22,0.0,0.0,66.67,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0
CARDIOPATI,100.0,100.0,50.0,0.0,100.0,50.0,0.0,0.0,90.91,61.4,46.36,54.71,55.61,64.95,65.16,65.26,67.42,85.71,75.0,77.78,50.0,100.0,33.33,0.0,0.0,100.0,100.0,100.0,100.0,100.0,0.0
CLASSI_FIN,25.0,100.0,0.0,0.0,0.0,0.0,0.0,0.0,9.09,1.94,2.31,3.25,3.48,2.47,2.9,2.0,6.62,0.0,0.0,33.33,0.0,0.0,33.33,0.0,100.0,0.0,0.0,0.0,0.0,0.0,0.0
CLASSI_OUT,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,99.76,99.82,99.84,99.6,99.03,98.9,99.33,99.53,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0
CO_REGIONA,25.0,0.0,0.0,0.0,0.0,100.0,0.0,0.0,9.09,10.01,13.69,11.49,10.46,12.93,12.62,13.13,12.63,14.29,0.0,0.0,0.0,0.0,33.33,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0
CO_RG_INTE,25.0,0.0,0.0,0.0,0.0,100.0,0.0,0.0,9.09,13.79,18.31,18.3,14.94,15.88,15.73,17.14,16.27,42.86,25.0,11.11,0.0,0.0,66.67,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0
CO_RG_RESI,25.0,0.0,0.0,0.0,0.0,100.0,0.0,0.0,9.09,8.8,13.33,11.15,9.92,11.83,11.62,12.05,11.75,14.29,0.0,0.0,0.0,0.0,33.33,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0
CRITERIO,50.0,100.0,0.0,0.0,0.0,0.0,0.0,0.0,9.09,3.84,3.96,5.27,5.33,4.75,5.02,4.08,9.34,28.57,0.0,44.44,0.0,0.0,33.33,0.0,100.0,0.0,0.0,0.0,0.0,0.0,0.0
CS_ESCOL_N,25.0,100.0,25.0,0.0,0.0,50.0,0.0,50.0,27.27,7.66,28.58,34.06,36.73,35.11,37.29,35.07,34.84,42.86,50.0,44.44,0.0,0.0,66.67,100.0,0.0,0.0,0.0,0.0,0.0,50.0,100.0
CS_ETINIA,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,99.46,99.84,99.91,99.82,99.64,99.55,99.39,99.1,85.71,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0
CS_ZONA,0.0,100.0,0.0,0.0,100.0,0.0,0.0,0.0,0.0,2.43,9.78,10.36,9.3,7.32,7.96,6.17,5.98,0.0,0.0,22.22,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0
DESC_RESP,25.0,100.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.87,14.79,18.65,21.22,15.35,11.54,8.07,7.4,0.0,25.0,0.0,0.0,0.0,33.33,100.0,0.0,0.0,0.0,0.0,0.0,50.0,0.0
DIABETES,100.0,0.0,50.0,0.0,100.0,50.0,0.0,0.0,90.91,61.79,49.82,57.95,58.89,66.98,67.08,66.49,68.57,85.71,75.0,77.78,50.0,100.0,66.67,100.0,0.0,100.0,100.0,100.0,100.0,100.0,0.0
DIARREIA,25.0,100.0,25.0,0.0,0.0,0.0,0.0,0.0,0.0,2.83,24.17,30.89,32.64,27.82,23.69,18.42,17.57,0.0,25.0,11.11,0.0,0.0,33.33,100.0,0.0,0.0,0.0,0.0,0.0,50.0,0.0
DISPNEIA,25.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.78,9.81,11.63,15.81,12.43,10.5,7.47,7.31,0.0,0.0,11.11,0.0,0.0,33.33,100.0,0.0,0.0,0.0,0.0,0.0,50.0,0.0
DOR_ABD,50.0,100.0,50.0,0.0,0.0,0.0,0.0,0.0,81.82,99.7,54.31,33.21,33.47,28.62,24.57,19.12,18.18,0.0,25.0,22.22,0.0,0.0,33.33,100.0,0.0,100.0,0.0,0.0,0.0,50.0,0.0
DOSE_1_COV,50.0,0.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,99.89,97.78,79.56,43.01,50.55,54.42,55.67,63.02,42.86,50.0,88.89,100.0,100.0,100.0,0.0,100.0,100.0,100.0,0.0,0.0,0.0,0.0
DOSE_2REF,100.0,100.0,75.0,100.0,100.0,100.0,100.0,100.0,100.0,99.99,99.52,99.52,94.99,82.42,87.85,87.12,87.52,85.71,50.0,100.0,100.0,100.0,100.0,0.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0
DOSE_2_COV,75.0,0.0,75.0,100.0,100.0,100.0,100.0,100.0,100.0,99.92,97.91,86.31,46.74,54.9,58.57,59.72,66.26,71.43,50.0,88.89,100.0,100.0,100.0,0.0,100.0,100.0,100.0,0.0,0.0,0.0,0.0
DOSE_ADIC,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,99.97,99.97,99.91,98.21,98.06,98.18,98.54,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0
DOSE_REF,100.0,0.0,75.0,100.0,100.0,100.0,100.0,100.0,100.0,99.97,98.77,98.02,71.67,69.69,79.42,78.04,78.28,100.0,50.0,88.89,100.0,100.0,100.0,0.0,100.0,100.0,100.0,100.0,0.0,50.0,0.0
DOS_RE_BI,75.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,99.99,99.89,99.91,99.84,92.57,90.04,89.17,89.44,85.71,50.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0
DT_1_DOSE,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,99.39,99.99,99.99,99.98,99.88,99.44,98.1,95.55,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0
DT_2_DOSE,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,99.57,99.99,100.0,99.98,99.92,99.55,98.78,97.78,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0
DT_ANTIVIR,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,45.45,38.77,84.65,97.97,96.62,94.51,92.23,88.86,87.87,100.0,100.0,88.89,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0
DT_COLETA,0.0,0.0,0.0,0.0,0.0,0.0,100.0,0.0,9.09,12.71,5.91,8.19,5.69,5.31,5.17,5.97,5.5,28.57,25.0,11.11,0.0,0.0,33.33,0.0,100.0,0.0,0.0,0.0,100.0,50.0,0.0
DT_DOSEUNI,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,99.5,99.99,99.99,99.98,99.88,99.42,98.18,95.96,71.43,100.0,88.89,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0
DT_ENCERRA,75.0,100.0,25.0,0.0,0.0,0.0,0.0,0.0,9.09,3.47,5.32,6.52,6.44,4.9,5.36,4.05,12.15,0.0,25.0,44.44,0.0,0.0,100.0,100.0,100.0,0.0,0.0,100.0,100.0,50.0,0.0
DT_ENTUTI,100.0,100.0,100.0,100.0,0.0,50.0,100.0,50.0,27.27,64.31,69.69,70.12,73.3,72.71,71.62,73.29,74.83,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0
DT_EVOLUCA,100.0,100.0,100.0,0.0,0.0,0.0,0.0,50.0,9.09,15.39,11.17,12.71,12.27,10.43,10.92,11.81,20.52,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0
DT_PCR,50.0,100.0,25.0,0.0,0.0,0.0,100.0,50.0,36.36,20.05,17.8,31.98,39.23,32.98,29.92,27.66,28.31,28.57,50.0,55.56,0.0,0.0,66.67,0.0,100.0,100.0,100.0,0.0,100.0,50.0,100.0
DT_RES,100.0,100.0,75.0,100.0,100.0,100.0,0.0,50.0,100.0,100.0,90.35,92.6,97.99,98.34,98.65,98.56,98.31,100.0,100.0,100.0,100.0,100.0,66.67,100.0,100.0,100.0,100.0,100.0,100.0,100.0,0.0
DT_RES_AN,75.0,100.0,75.0,100.0,100.0,100.0,100.0,50.0,100.0,78.58,92.83,77.81,55.67,55.5,59.91,58.06,57.99,57.14,75.0,88.89,100.0,100.0,100.0,100.0,100.0,0.0,0.0,100.0,100.0,100.0,100.0
DT_SAIDUTI,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,45.45,79.74,82.66,81.57,84.04,82.76,82.55,83.54,86.34,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0
DT_TRT_COV,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,99.84,99.67,99.67,99.75,99.85,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0
DT_UT_DOSE,100.0,100.0,100.0,100.0,100.0,100.0,0.0,100.0,90.91,83.52,90.98,95.61,96.51,96.3,86.58,73.03,78.51,71.43,50.0,88.89,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0
DT_VAC_MAE,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,97.71,99.95,99.97,99.89,99.77,99.73,99.7,99.75,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0
ESTRANG,50.0,100.0,25.0,100.0,0.0,50.0,100.0,100.0,90.91,99.53,93.86,27.38,8.66,7.7,6.11,4.7,4.13,0.0,0.0,22.22,0.0,0.0,100.0,0.0,100.0,100.0,0.0,0.0,0.0,0.0,0.0
EVOLUCAO,75.0,100.0,50.0,0.0,0.0,0.0,0.0,0.0,9.09,5.64,5.64,7.08,6.32,4.41,4.92,3.77,12.09,0.0,0.0,33.33,0.0,0.0,100.0,0.0,100.0,0.0,100.0,100.0,0.0,0.0,0.0
FADIGA,50.0,100.0,50.0,0.0,0.0,0.0,0.0,0.0,81.82,99.47,53.11,28.91,31.01,26.62,22.93,17.59,16.6,14.29,25.0,22.22,0.0,0.0,33.33,100.0,0.0,100.0,0.0,0.0,0.0,50.0,0.0
FEBRE,0.0,100.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.34,12.03,16.72,18.38,13.45,10.08,7.77,7.01,0.0,0.0,0.0,0.0,0.0,33.33,100.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0
GARGANTA,25.0,100.0,25.0,0.0,0.0,0.0,0.0,0.0,0.0,2.35,23.41,29.89,30.66,27.38,24.01,18.41,17.61,0.0,25.0,11.11,50.0,0.0,33.33,100.0,0.0,0.0,0.0,0.0,0.0,50.0,0.0
HEMATOLOGI,100.0,100.0,50.0,0.0,100.0,50.0,0.0,0.0,90.91,62.24,57.57,65.38,64.72,70.05,69.57,68.4,70.08,85.71,75.0,77.78,50.0,100.0,66.67,100.0,0.0,100.0,100.0,100.0,100.0,100.0,0.0
HEPATICA,100.0,100.0,50.0,0.0,100.0,50.0,0.0,0.0,90.91,62.37,57.67,65.49,64.9,70.25,69.8,68.58,70.23,85.71,75.0,77.78,50.0,100.0,66.67,100.0,0.0,100.0,100.0,100.0,100.0,100.0,0.0
IMUNODEPRE,100.0,100.0,50.0,0.0,100.0,50.0,0.0,0.0,90.91,62.04,57.12,65.04,64.04,69.33,68.97,67.94,69.75,85.71,75.0,77.78,50.0,100.0,66.67,100.0,0.0,100.0,100.0,100.0,100.0,100.0,0.0
MAE_VAC,75.0,100.0,100.0,100.0,0.0,100.0,100.0,100.0,100.0,87.29,99.24,99.03,97.16,93.73,94.39,94.78,95.94,100.0,100.0,88.89,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0
MORB_DESC,100.0,0.0,25.0,0.0,100.0,100.0,0.0,100.0,72.73,82.36,72.86,75.7,74.28,80.82,82.67,83.58,85.21,100.0,100.0,88.89,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0
M_AMAMENTA,75.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,88.6,99.43,99.23,97.5,94.14,94.69,94.91,96.03,100.0,100.0,88.89,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0
NEUROLOGIC,100.0,100.0,50.0,0.0,100.0,50.0,0.0,0.0,90.91,61.84,56.44,64.58,63.07,68.78,68.57,67.72,69.42,85.71,75.0,77.78,50.0,100.0,66.67,100.0,0.0,100.0,100.0,100.0,100.0,100.0,0.0
OBESIDADE,100.0,100.0,50.0,0.0,100.0,50.0,0.0,0.0,90.91,62.43,56.67,62.96,64.42,70.27,69.78,68.62,70.35,85.71,75.0,77.78,50.0,100.0,66.67,100.0,0.0,100.0,100.0,100.0,100.0,100.0,0.0
OBES_IMC,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,98.5,97.62,98.67,99.57,99.76,99.78,99.75,99.79,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0
OUTRO_DES,50.0,100.0,50.0,100.0,100.0,100.0,100.0,100.0,90.91,78.17,68.57,68.8,71.1,71.6,72.94,74.34,73.49,85.71,100.0,100.0,100.0,100.0,33.33,0.0,0.0,100.0,100.0,100.0,100.0,0.0,100.0
OUTRO_SIN,0.0,100.0,0.0,100.0,100.0,50.0,0.0,0.0,18.18,7.95,24.47,29.5,30.99,28.23,26.36,23.82,22.44,28.57,50.0,55.56,0.0,0.0,33.33,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0
OUT_ANIM,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,99.96,99.91,99.91,99.68,99.77,99.77,99.77,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0
OUT_ANTIV,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,99.73,99.3,99.66,99.77,99.7,99.81,99.81,99.86,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0
OUT_MORBI,100.0,0.0,25.0,0.0,100.0,50.0,0.0,0.0,63.64,62.04,50.46,57.28,56.58,65.02,66.01,66.16,67.94,100.0,75.0,77.78,50.0,100.0,100.0,100.0,0.0,100.0,100.0,100.0,100.0,100.0,100.0
OUT_TRAT,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,99.89,99.76,99.75,99.82,99.89,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0
PAC_COCBO,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,99.98,98.21,97.61,98.54,99.26,99.3,99.26,99.14,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0
... [27 more rows omitted]
```

### `outputs/tables/pessoa_a/a2_coerencia_datas.csv`

- Git: `ignored` · `1.3 KB` · modified `2026-10-17 00:25 UTC` · 13 rows

```csv
regra,descricao,n_comparaveis,n_violacoes,pct,acao_sugerida
DT_NASC <= DT_SIN_PRI,Nascimento posterior ao início dos sintomas,4662951,1,0.0,excluir
DT_SIN_PRI <= DT_NOTIFIC,Início dos sintomas posterior à notificação,4666910,0,0.0,manter com flag
DT_SIN_PRI <= DT_INTERNA,Início dos sintomas posterior à internação,4362603,24340,0.558,manter com flag
DT_INTERNA <= DT_EVOLUCA,Evolução anterior à internação,3822766,0,0.0,excluir
DT_EVOLUCA <= DT_ENCERRA,Encerramento anterior à evolução,3985787,107196,2.689,manter com flag
DT_NASC válida,"Data futura, não interpretável ou fora de 1900–2100",4662964,13,0.0,transformar em ausente
DT_SIN_PRI válida,"Data futura, não interpretável ou fora de 1900–2100",4666910,0,0.0,transformar em ausente
DT_NOTIFIC válida,"Data futura, não interpretável ou fora de 1900–2100",4666910,0,0.0,transformar em ausente
DT_INTERNA válida,"Data futura, não interpretável ou fora de 1900–2100",4362665,108,0.002,transformar em ausente
DT_EVOLUCA válida,"Data futura, não interpretável ou fora de 1900–2100",4014740,0,0.0,transformar em ausente
DT_ENCERRA válida,"Data futura, não interpretável ou fora de 1900–2100",4338057,0,0.0,transformar em ausente
sintomas->internação,> 30 dias,4362603,40824,0.936,manter com flag
idade em anos,< 0 ou > 120,4666910,38,0.001,transformar em ausente
```

### `outputs/tables/pessoa_a/a2_duplicidades.csv`

- Git: `ignored` · `177 B` · modified `2026-10-17 00:26 UTC` · 3 rows

```csv
tipo,n_linhas,n_grupos
linhas exatamente duplicadas,0,0
NU_NOTIFIC repetido (não implica mesma pessoa),58,29
"mesma chave ['NU_NOTIFIC', 'DT_NOTIFIC', 'DT_NASC']",50,25
```

### `outputs/tables/pessoa_a/a2_matriz_elegibilidade.csv`

- Git: `ignored` · `21.0 KB` · modified `2026-10-17 00:27 UTC` · 198 rows (first 60 shown)

```csv
coluna,classe,justificativa,existe_na_admissao_sugerido,pct_vazio,n_distintos_amostra,quando_observada,quando_chegou_na_base,decisao_final,responsavel,data
AMOSTRA,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
ANO_ARQUIVO,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
AN_ADENO,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
AN_OUTRO,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
AN_PARA1,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
AN_PARA2,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
AN_PARA3,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
AN_SARS2,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
AN_VSR,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
ARQUIVO_ORIGEM,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
COD_IDADE,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
CO_DETEC,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
CO_PS_VGM,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
CS_ETINIA,auditoria,"Permitida, mas quase toda vazia",Verificar,99.76,87.0,,,,,
DATA_SNAPSHOT,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
DS_AN_OUT,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
DS_PCR_OUT,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
DT_CO_SOR,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
DT_NASC,auditoria,Não classificada: consultar dicionário,Verificar,0.08,31268.0,,,,,
DT_RAIOX,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
DT_RT_VGM,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
DT_TOMO,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
DT_VGM,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
FAB_ADIC,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
FAB_COVRF,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
FAB_COVRF2,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
FAB_COV_1,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
FAB_COV_2,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
FAB_RE_BI,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
FATOR_RISC,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
FLUASU_OUT,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
FLUBLI_OUT,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
FNT_IN_COV,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
HISTO_VGM,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
ID_MN_INTE,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
ID_MUNICIP,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
ID_PAIS,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
ID_REGIONA,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
ID_REGISTRO,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
ID_RG_INTE,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
ID_RG_RESI,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
LOTE_1_COV,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
LOTE_2_COV,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
LOTE_ADIC,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
LOTE_REF,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
LOTE_REF2,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
LOT_RE_BI,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
LO_PS_VGM,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
NM_UN_INTE,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
NOSOCOMIAL,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
NU_NOTIFIC,auditoria,Não classificada: consultar dicionário,Verificar,0.0,100000.0,,,,,
OUT_AMOST,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
OUT_ANIM,auditoria,"Permitida, mas quase toda vazia",Verificar,99.89,35.0,,,,,
OUT_SOR,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
PAIS_VGM,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
PCR_ADENO,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
PCR_BOCA,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
PCR_FLUASU,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
PCR_FLUBLI,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
PCR_METAP,auditoria,"Existe no Parquet, mas não foi carregada (fora das listas classificadas)",Verificar,,,,,,,
... [138 more rows omitted]
```

### `outputs/tables/pessoa_a/a2_maturidade_evolucao_por_mes.csv`

- Git: `ignored` · `4.2 KB` · modified `2026-10-17 00:26 UTC` · 140 rows (first 60 shown)

```csv
mes,n,pct_evolucao_fechada,pct_com_dt_encerra,mediana_dias_ate_encerra
1917-09,2,50.0,50.0,39695.0
1917-10,2,0.0,0.0,
1918-01,1,0.0,0.0,
1941-01,1,0.0,100.0,29397.0
1941-04,1,0.0,0.0,
1941-08,1,100.0,100.0,29223.0
1941-11,1,0.0,100.0,30231.0
2009-09,1,100.0,100.0,4053.0
2011-07,1,100.0,100.0,4025.0
2012-02,1,100.0,100.0,3866.0
2012-03,1,100.0,100.0,3295.0
2016-06,1,100.0,100.0,1625.0
2017-01,1,100.0,100.0,1476.0
2017-12,1,100.0,100.0,983.0
2018-09,2,50.0,50.0,1719.0
2018-12,9,100.0,100.0,28.0
2019-01,1175,91.4,98.04,29.0
2019-02,1837,92.49,98.48,22.0
2019-03,4102,92.37,97.49,19.0
2019-04,6000,92.67,96.8,21.0
2019-05,8172,92.03,96.11,18.0
2019-06,7599,92.08,96.0,19.0
2019-07,5366,92.3,96.55,17.0
2019-08,3894,91.29,96.12,17.0
2019-09,2970,90.51,96.5,15.0
2019-10,2618,88.58,97.1,18.0
2019-11,1967,87.65,95.73,20.0
2019-12,1843,89.09,95.55,21.0
2020-01,1755,94.42,97.32,22.0
2020-02,2491,94.94,97.55,22.0
2020-03,28459,95.43,96.95,24.0
2020-04,84846,93.83,95.89,23.0
2020-05,135936,93.12,94.89,22.0
2020-06,134214,93.16,95.09,18.0
2020-07,148007,93.21,94.94,16.0
2020-08,127273,92.45,94.9,15.0
2020-09,99912,92.07,94.51,14.0
2020-10,85820,90.81,93.7,15.0
2020-11,99653,91.15,94.0,16.0
2020-12,127998,90.97,93.38,18.0
2021-01,141017,93.08,95.11,17.0
2021-02,145606,92.86,94.63,16.0
2021-03,292192,92.1,93.86,17.0
2021-04,224626,90.33,93.07,16.0
2021-05,229563,89.4,92.49,16.0
2021-06,200069,90.03,93.12,14.0
2021-07,127986,90.08,93.55,13.0
2021-08,90523,89.76,94.16,14.0
2021-09,63285,89.42,93.64,14.0
2021-10,49032,88.55,92.92,15.0
2021-11,40664,87.81,92.38,14.0
2021-12,52826,86.0,91.12,17.0
2022-01,125385,92.51,94.8,17.0
2022-02,67713,93.27,95.4,14.0
2022-03,35116,92.75,94.75,13.0
2022-04,29606,91.59,93.91,16.0
2022-05,41428,91.9,94.46,14.0
2022-06,57046,92.16,94.32,14.0
2022-07,46178,91.05,93.35,13.0
2022-08,27288,89.23,91.98,12.0
... [80 more rows omitted]
```

### `outputs/tables/pessoa_a/a2_vazios_ignorados_por_ano.csv`

- Git: `ignored` · `87.7 KB` · modified `2026-10-17 00:25 UTC` · 3520 rows (first 60 shown)

```csv
coluna,ano,n,pct_vazio,pct_ignorado
NU_NOTIFIC,1917,4,0.0,
NU_NOTIFIC,1918,1,0.0,
NU_NOTIFIC,1941,4,0.0,
NU_NOTIFIC,2009,1,0.0,
NU_NOTIFIC,2011,1,0.0,
NU_NOTIFIC,2012,2,0.0,
NU_NOTIFIC,2016,1,0.0,
NU_NOTIFIC,2017,2,0.0,
NU_NOTIFIC,2018,11,0.0,
NU_NOTIFIC,2019,47545,0.0,
NU_NOTIFIC,2020,1076375,0.0,
NU_NOTIFIC,2021,1657394,0.0,
NU_NOTIFIC,2022,536135,0.0,
NU_NOTIFIC,2023,265671,0.0,
NU_NOTIFIC,2024,253367,0.0,
NU_NOTIFIC,2025,315616,0.0,
NU_NOTIFIC,2026,210438,0.0,
NU_NOTIFIC,2027,7,0.0,
NU_NOTIFIC,2028,4,0.0,
NU_NOTIFIC,2029,9,0.0,
NU_NOTIFIC,2031,2,0.0,
NU_NOTIFIC,2032,1,0.0,
NU_NOTIFIC,2033,3,0.0,
NU_NOTIFIC,2034,1,0.0,
NU_NOTIFIC,2050,1,0.0,
NU_NOTIFIC,2052,1,0.0,
NU_NOTIFIC,2055,1,0.0,
NU_NOTIFIC,2056,1,0.0,
NU_NOTIFIC,2092,1,0.0,
NU_NOTIFIC,2098,2,0.0,
NU_NOTIFIC,2099,1,0.0,
NU_NOTIFIC,sem_data,304307,0.0,
DT_NOTIFIC,1917,4,0.0,
DT_NOTIFIC,1918,1,0.0,
DT_NOTIFIC,1941,4,0.0,
DT_NOTIFIC,2009,1,0.0,
DT_NOTIFIC,2011,1,0.0,
DT_NOTIFIC,2012,2,0.0,
DT_NOTIFIC,2016,1,0.0,
DT_NOTIFIC,2017,2,0.0,
DT_NOTIFIC,2018,11,0.0,
DT_NOTIFIC,2019,47545,0.0,
DT_NOTIFIC,2020,1076375,0.0,
DT_NOTIFIC,2021,1657394,0.0,
DT_NOTIFIC,2022,536135,0.0,
DT_NOTIFIC,2023,265671,0.0,
DT_NOTIFIC,2024,253367,0.0,
DT_NOTIFIC,2025,315616,0.0,
DT_NOTIFIC,2026,210438,0.0,
DT_NOTIFIC,2027,7,0.0,
DT_NOTIFIC,2028,4,0.0,
DT_NOTIFIC,2029,9,0.0,
DT_NOTIFIC,2031,2,0.0,
DT_NOTIFIC,2032,1,0.0,
DT_NOTIFIC,2033,3,0.0,
DT_NOTIFIC,2034,1,0.0,
DT_NOTIFIC,2050,1,0.0,
DT_NOTIFIC,2052,1,0.0,
DT_NOTIFIC,2055,1,0.0,
DT_NOTIFIC,2056,1,0.0,
... [3460 more rows omitted]
```

### `outputs/tables/pessoa_a/a3_benchmark_split_sem_2020_2021.csv`

- Git: `ignored` · `416 B` · modified `2026-10-17 00:52 UTC` · 4 rows

```csv
cenario,particao,n_treino,n_validacao,prevalencia_validacao,modelo,roc_auc,pr_auc,brier
sem_2020_2021,aleatoria,139939,30227,0.1194,baseline_prior,0.5,0.1194,0.1051
sem_2020_2021,aleatoria,139939,30227,0.1194,logistica,0.8371,0.367,0.1739
sem_2020_2021,temporal_por_ordem,139890,29922,0.0766,baseline_prior,0.5,0.0766,0.0747
sem_2020_2021,temporal_por_ordem,139890,29922,0.0766,logistica,0.8418,0.2763,0.139
```

### `outputs/tables/pessoa_a/a3_benchmark_split_todos_2019_2025.csv`

- Git: `ignored` · `425 B` · modified `2026-10-17 00:52 UTC` · 4 rows

```csv
cenario,particao,n_treino,n_validacao,prevalencia_validacao,modelo,roc_auc,pr_auc,brier
todos_2019_2025,aleatoria,139616,30329,0.2309,baseline_prior,0.5,0.2309,0.1776
todos_2019_2025,aleatoria,139616,30329,0.2309,logistica,0.774,0.4517,0.1984
todos_2019_2025,temporal_por_ordem,139803,30142,0.1377,baseline_prior,0.5,0.1377,0.1383
todos_2019_2025,temporal_por_ordem,139803,30142,0.1377,logistica,0.8206,0.3642,0.1678
```

### `outputs/tables/pessoa_a/a3_split_aleatorio_sem_2020_2021.csv`

- Git: `ignored` · `155 B` · modified `2026-10-17 00:51 UTC` · 3 rows

```csv
split,n,n_obitos,pct_linhas,prevalencia_obito_pct
treino,895712,108527,70.0,12.12
validacao,191938,23256,15.0,12.12
holdout,191938,23255,15.0,12.12
```

### `outputs/tables/pessoa_a/a3_split_aleatorio_sem_2020_2021_por_ano.csv`

- Git: `ignored` · `166 B` · modified `2026-10-17 00:51 UTC` · 5 rows

```csv
ano_internacao,treino,validacao,holdout
2019,30412,6546,6555
2022,333642,71094,71244
2023,168213,36176,36315
2024,160377,34741,34360
2025,203068,43381,43464
```

### `outputs/tables/pessoa_a/a3_split_aleatorio_todos_2019_2025.csv`

- Git: `ignored` · `158 B` · modified `2026-10-17 00:51 UTC` · 3 rows

```csv
split,n,n_obitos,pct_linhas,prevalencia_obito_pct
treino,2617730,592509,70.0,22.63
validacao,560942,126966,15.0,22.63
holdout,560943,126967,15.0,22.63
```

### `outputs/tables/pessoa_a/a3_split_aleatorio_todos_2019_2025_por_ano.csv`

- Git: `ignored` · `221 B` · modified `2026-10-17 00:51 UTC` · 7 rows

```csv
ano_internacao,treino,validacao,holdout
2019,30393,6694,6426
2020,686366,146395,147051
2021,1036718,221925,221572
2022,332754,71549,71677
2023,168742,36006,35956
2024,160515,34358,34605
2025,202242,44015,43656
```

### `outputs/tables/pessoa_a/a3_split_temporal.csv`

- Git: `ignored` · `197 B` · modified `2026-10-17 00:49 UTC` · 4 rows

```csv
split,_ano,n,n_obitos,prevalencia_obito
desenvolvimento,2022,475980,86433,18.16
desenvolvimento,2023,240704,23037,9.57
desenvolvimento,2024,229478,19120,8.33
holdout,2025,289913,21227,7.32
```

### `outputs/tables/pessoa_a/a3_varredura_vazamento.csv`

- Git: `ignored` · `889 B` · modified `2026-10-17 00:49 UTC` · 36 rows

```csv
coluna,auc_univariada,forca
SUPORT_VEN,0.7237,0.4473
CARDIOPATI,0.6623,0.3246
UTI,0.6571,0.3142
OUT_MORBI,0.6455,0.2911
DIABETES,0.6446,0.2893
ASMA,0.6277,0.2553
RENAL,0.6205,0.241
PNEUMOPATI,0.6203,0.2406
NEUROLOGIC,0.6198,0.2396
IMUNODEPRE,0.616,0.232
HEPATICA,0.6111,0.2221
OBESIDADE,0.6109,0.2219
TOSSE,0.6089,0.2179
SIND_DOWN,0.6089,0.2178
HEMATOLOGI,0.6088,0.2176
PUERPERA,0.6082,0.2164
SATURACAO,0.608,0.2159
FEBRE,0.5917,0.1834
TRAT_COV,0.5869,0.1738
CS_GESTANT,0.5786,0.1572
SG_UF,0.5769,0.1538
DISPNEIA,0.5744,0.1489
FADIGA,0.5503,0.1007
ANTIVIRAL,0.5474,0.0949
VOMITO,0.5387,0.0774
CS_RACA,0.5357,0.0714
GARGANTA,0.5277,0.0555
AVE_SUINO,0.5275,0.055
OUTRO_SIN,0.5263,0.0526
DIARREIA,0.5227,0.0455
DOR_ABD,0.5189,0.0377
PERD_PALA,0.5181,0.0361
PERD_OLFT,0.5178,0.0355
TP_ANTIVIR,0.5138,0.0277
CS_ZONA,0.5096,0.0192
TIPO_TRAT,0.5004,0.0007
```

### `outputs/tables/pessoa_a/ata_17_10_fine_tuning.md`

- Git: `ignored` · `526 B` · modified `2026-10-17 02:02 UTC`

```markdown
# Ata 17/10 — Fine Tuning

**Data:** 2026-10-17

## Decisões

- Busca encerrada ou finalizando; sem novas famílias de modelo

## Candidatos na shortlist

- (preencher) clustering: solução principal + alternativa
- (preencher) supervisionado: 1–2 modelos

## Descartes e justificativas

- (preencher) candidato — justificativa padronizada

## Riscos

- (preencher)

## Pendências

- Confirmação dos finalistas e congelamento em 18/10

## Alertas das verificações automáticas

- nenhum
```

### `outputs/tables/pessoa_a/ata_gate_2_11_10.md`

- Git: `ignored` · `2.0 KB` · modified `2026-10-17 00:49 UTC`

```markdown
# Ata Gate 2 (11/10)

**Data:** 2026-10-11

## Decisões

- (preencher) decisões do Gate 2 — desenho experimental

## Candidatos na shortlist

- (nenhum registrado)

## Descartes e justificativas

- (nenhum registrado)

## Riscos

- (nenhum registrado)

## Pendências

- (preencher)

## Alertas das verificações automáticas

- [ATENÇÃO] A3-cfg / Alvo: evolucao=3 e ausente: o YAML só tem `descartar_ignorado` (evolucao==9). O C2 descarta 3/9/nulos em `filtrar_rotulos_validos`; confirmar em src/models/pipeline.py que `criar_alvo_binario` trata 3 e ausente como inválidos (nunca como cura)
- [ATENÇÃO] A3-cfg / C2 x split por datas: o C2 enviado cria `TemporalSplit(df, coluna_tempo, frac_treino, frac_validacao)` e não lê `temporal.modo`/`temporal.datas`: para holdout = 2025 o C precisa adaptar o split
- [ATENÇÃO] A3-cfg / Split temporal: modo='aleatorio_estratificado' (fração). Plano: desenvolvimento [2022, 2023, 2024] / holdout [2025] -> usar modo 'datas' (G2)
- [FALHA] A3-cfg / Features do YAML x Parquet: não existem no Parquet: dias_sintomas_ate_internacao, sexo_categoria — o C2 não conseguirá carregá-las
- [ATENÇÃO] A3-cfg / `proibidas` do YAML x Parquet: não existem no Parquet: alvo_obito_srag, evolucao_normalizada, evolucao_covid19, utilizouvni, cluster, cluster_rotulo — test_leakage não protege as colunas reais
- [ATENÇÃO] A3-cfg / Lista `proibidas` do YAML: 17 do plano não protegidas pelo test_leakage: CLASSI_FIN, CLASSI_OUT, CRITERIO, DT_COLETA, DT_PCR, DT_RES, DT_RES_AN, PCR, PCR_RESUL, POS_PCRFLU, POS_PCROUT, RES_AN
- [ATENÇÃO] A3-cfg / Features condicionais: confirmar condição de uso: CS_ZONA, OUTRO_SIN, OUT_MORBI
- [ATENÇÃO] A3-cfg / Gates: 5 pendentes: G1_definicao_alvo_features, G6_finalistas_tuning, G7_calibracao, G8_limiar... (A aprova G1/G2 com as regras A1–A3)
- [ATENÇÃO] A3 / Variáveis condicionais (supervisionado): confirmar condição de uso: CS_ZONA, OUTRO_SIN, OUT_MORBI
- [ATENÇÃO] A3 / Auditoria de logs: nenhum log encontrado em logs
```

### `outputs/tables/pessoa_a/ata_gate_3_14_10.md`

- Git: `ignored` · `2.0 KB` · modified `2026-10-17 00:49 UTC`

```markdown
# Ata Gate 3 (14/10)

**Data:** 2026-10-14

## Decisões

- (preencher) configurações inviáveis eliminadas

## Candidatos na shortlist

- (nenhum registrado)

## Descartes e justificativas

- (nenhum registrado)

## Riscos

- (nenhum registrado)

## Pendências

- (preencher)

## Alertas das verificações automáticas

- [ATENÇÃO] A3-cfg / Alvo: evolucao=3 e ausente: o YAML só tem `descartar_ignorado` (evolucao==9). O C2 descarta 3/9/nulos em `filtrar_rotulos_validos`; confirmar em src/models/pipeline.py que `criar_alvo_binario` trata 3 e ausente como inválidos (nunca como cura)
- [ATENÇÃO] A3-cfg / C2 x split por datas: o C2 enviado cria `TemporalSplit(df, coluna_tempo, frac_treino, frac_validacao)` e não lê `temporal.modo`/`temporal.datas`: para holdout = 2025 o C precisa adaptar o split
- [ATENÇÃO] A3-cfg / Split temporal: modo='aleatorio_estratificado' (fração). Plano: desenvolvimento [2022, 2023, 2024] / holdout [2025] -> usar modo 'datas' (G2)
- [FALHA] A3-cfg / Features do YAML x Parquet: não existem no Parquet: dias_sintomas_ate_internacao, sexo_categoria — o C2 não conseguirá carregá-las
- [ATENÇÃO] A3-cfg / `proibidas` do YAML x Parquet: não existem no Parquet: alvo_obito_srag, evolucao_normalizada, evolucao_covid19, utilizouvni, cluster, cluster_rotulo — test_leakage não protege as colunas reais
- [ATENÇÃO] A3-cfg / Lista `proibidas` do YAML: 17 do plano não protegidas pelo test_leakage: CLASSI_FIN, CLASSI_OUT, CRITERIO, DT_COLETA, DT_PCR, DT_RES, DT_RES_AN, PCR, PCR_RESUL, POS_PCRFLU, POS_PCROUT, RES_AN
- [ATENÇÃO] A3-cfg / Features condicionais: confirmar condição de uso: CS_ZONA, OUTRO_SIN, OUT_MORBI
- [ATENÇÃO] A3-cfg / Gates: 5 pendentes: G1_definicao_alvo_features, G6_finalistas_tuning, G7_calibracao, G8_limiar... (A aprova G1/G2 com as regras A1–A3)
- [ATENÇÃO] A3 / Variáveis condicionais (supervisionado): confirmar condição de uso: CS_ZONA, OUTRO_SIN, OUT_MORBI
- [ATENÇÃO] A3 / Auditoria de logs: nenhum log encontrado em logs
```

### `outputs/tables/pessoa_a/comparacao_cenarios.csv`

- Git: `ignored` · `337 B` · modified `2026-10-17 00:52 UTC` · 2 rows

```csv
cenario,anos,n_linhas,n_obitos,prevalencia_obito_pct,pr_auc_aleatoria,roc_auc_aleatoria,pr_auc_temporal_por_ordem,roc_auc_temporal_por_ordem
todos_2019_2025,"2019,2020,2021,2022,2023,2024,2025",3739615,846442,22.63,0.4517,0.774,0.3642,0.8206
sem_2020_2021,"2019,2022,2023,2024,2025",1279588,155038,12.12,0.367,0.8371,0.2763,0.8418
```

### `outputs/tables/pessoa_a/relatorio_A1.md`

- Git: `ignored` · `1.1 KB` · modified `2026-10-17 00:23 UTC`

```markdown
# Relatório de verificações — relatorio_A1

| Etapa | Verificação | Status | Detalhe |
| --- | --- | --- | --- |
| A1 | Colunas essenciais | OK | 11 colunas presentes |
| A1 | Códigos inesperados | OK | todos os códigos dentro do esperado |
| A1 | Waterfall da coorte | OK | 4,666,910 -> 1,236,075 registros (26.5%) |
| A1 | Alvo: desconhecido ≠ cura | OK | 9/ausente/3 viram NA; só 1->0 e 2->1 |
| A1 | Features derivadas | OK | criadas no dataset: idade_anos, faixa_etaria |
| A1 | Dataset analítico | ATENÇÃO | 1,236,075 linhas v0.1; features ausentes na base: DIAS_SINTOMAS_ATE_INTERNACAO, SEXO_CATEGORIA |
| A1-C2 | Colunas exigidas pelo C2 | FALHA | ausentes no dataset: dias_sintomas_ate_internacao, sexo_categoria |
| A1-C2 | Coluna de tempo | OK | datetime válido, ordenado: 2022-01-01 -> 2025-12-31 |
| A1-C2 | Alvo | OK | apenas cura/óbito; positivos [2.0] presentes |
| A1-C2 | check_leakage (C2) | OK | nenhuma feature está em `proibidas` |
| A1-C2 | Tamanho | OK | 1,236,075 linhas |

**Resumo:** 9 OK · 1 atenção · 1 falha(s).
```

### `outputs/tables/pessoa_a/relatorio_A2.md`

- Git: `ignored` · `1.4 KB` · modified `2026-10-17 00:27 UTC`

```markdown
# Relatório de verificações — relatorio_A2

| Etapa | Verificação | Status | Detalhe |
| --- | --- | --- | --- |
| A2 | Campo inexistente por ano | ATENÇÃO | 87 campos 100% vazios em algum ano (ex.: ANTIVIRAL, ASMA, AVE_SUINO, CARDIOPATI, CLASSI_FIN) |
| A2 | Coerência de datas | ATENÇÃO | 2 regra(s) com violações relevantes: DT_NASC <= DT_SIN_PRI (1); DT_EVOLUCA <= DT_ENCERRA (107196) |
| A2 | Duplicidades | OK | 0 linhas exatas duplicadas; demais tipos em a2_duplicidades.csv |
| A2 | Maturidade de EVOLUCAO (holdout) | OK | todos os meses do holdout com evolução madura |
| A2 | Matriz de elegibilidade | ATENÇÃO | {'auditoria': 93, 'incluir com condição': 39, 'incluir': 34, 'excluir': 32} — preencher colunas em branco e fechar 'auditoria' |
| A1 | Features derivadas | OK | criadas no dataset: idade_anos, faixa_etaria |
| A1 | Dataset analítico | ATENÇÃO | 1,236,075 linhas v1.0; features ausentes na base: DIAS_SINTOMAS_ATE_INTERNACAO, SEXO_CATEGORIA |
| A1-C2 | Colunas exigidas pelo C2 | FALHA | ausentes no dataset: dias_sintomas_ate_internacao, sexo_categoria |
| A1-C2 | Coluna de tempo | OK | datetime válido, ordenado: 2022-01-01 -> 2025-12-31 |
| A1-C2 | Alvo | OK | apenas cura/óbito; positivos [2.0] presentes |
| A1-C2 | check_leakage (C2) | OK | nenhuma feature está em `proibidas` |
| A1-C2 | Tamanho | OK | 1,236,075 linhas |

**Resumo:** 7 OK · 4 atenção · 1 falha(s).
```

### `outputs/tables/pessoa_a/relatorio_A3.md`

- Git: `ignored` · `2.4 KB` · modified `2026-10-17 00:49 UTC`

```markdown
# Relatório de verificações — relatorio_A3

| Etapa | Verificação | Status | Detalhe |
| --- | --- | --- | --- |
| A3-cfg | Alvo: positivos | OK | óbito SRAG (evolucao=2) como positivo |
| A3-cfg | Alvo: evolucao=3 e ausente | ATENÇÃO | o YAML só tem `descartar_ignorado` (evolucao==9). O C2 descarta 3/9/nulos em `filtrar_rotulos_validos`; confirmar em src/models/pipeline.py que `criar_alvo_binario` trata 3 e ausente como inválidos (nunca como cura) |
| A3-cfg | Coluna temporal | OK | split por DT_INTERNA |
| A3-cfg | C2 x split por datas | ATENÇÃO | o C2 enviado cria `TemporalSplit(df, coluna_tempo, frac_treino, frac_validacao)` e não lê `temporal.modo`/`temporal.datas`: para holdout = 2025 o C precisa adaptar o split |
| A3-cfg | Split temporal | ATENÇÃO | modo='aleatorio_estratificado' (fração). Plano: desenvolvimento [2022, 2023, 2024] / holdout [2025] -> usar modo 'datas' (G2) |
| A3-cfg | Features derivadas do YAML | OK | idade_anos não existem no Parquet: a Pessoa A as cria no dataset analítico |
| A3-cfg | Features do YAML x Parquet | FALHA | não existem no Parquet: dias_sintomas_ate_internacao, sexo_categoria — o C2 não conseguirá carregá-las |
| A3-cfg | `proibidas` do YAML x Parquet | ATENÇÃO | não existem no Parquet: alvo_obito_srag, evolucao_normalizada, evolucao_covid19, utilizouvni, cluster, cluster_rotulo — test_leakage não protege as colunas reais |
| A3-cfg | Features x proibidas | OK | 31 features sem conflito |
| A3-cfg | Lista `proibidas` do YAML | ATENÇÃO | 17 do plano não protegidas pelo test_leakage: CLASSI_FIN, CLASSI_OUT, CRITERIO, DT_COLETA, DT_PCR, DT_RES, DT_RES_AN, PCR, PCR_RESUL, POS_PCRFLU, POS_PCROUT, RES_AN |
| A3-cfg | Features condicionais | ATENÇÃO | confirmar condição de uso: CS_ZONA, OUTRO_SIN, OUT_MORBI |
| A3-cfg | Gates | ATENÇÃO | 5 pendentes: G1_definicao_alvo_features, G6_finalistas_tuning, G7_calibracao, G8_limiar... (A aprova G1/G2 com as regras A1–A3) |
| A3 | Variáveis proibidas (supervisionado) | OK | 31 variáveis, nenhuma proibida |
| A3 | Variáveis condicionais (supervisionado) | ATENÇÃO | confirmar condição de uso: CS_ZONA, OUTRO_SIN, OUT_MORBI |
| A3 | Split temporal | OK | dev [2022, 2023, 2024] < holdout [2025]; Δ prevalência 6.3 p.p. |
| A3 | Varredura de vazamento | OK | nenhuma variável com AUC univariada ≥ 0.9 |
| A3 | Auditoria de logs | ATENÇÃO | nenhum log encontrado em logs |

**Resumo:** 7 OK · 9 atenção · 1 falha(s).
```

### `outputs/tables/pessoa_a/relatorio_A3b.md`

- Git: `ignored` · `3.1 KB` · modified `2026-10-17 00:52 UTC`

```markdown
# Relatório de verificações — relatorio_A3b

| Etapa | Verificação | Status | Detalhe |
| --- | --- | --- | --- |
| A1 | Waterfall da coorte [todos_2019_2025] | OK | 4,666,910 -> 3,739,615 registros (80.1%) |
| A1 | Features derivadas [todos_2019_2025] | OK | criadas no dataset: idade_anos, faixa_etaria |
| A1 | Dataset analítico [todos_2019_2025] | ATENÇÃO | 3,739,615 linhas v0.1; features ausentes na base: DIAS_SINTOMAS_ATE_INTERNACAO, SEXO_CATEGORIA |
| A3b | Proporções 70/15/15 [todos_2019_2025] | OK | desvio máximo 0.00 p.p. / treino=2,617,730, validacao=560,942, holdout=560,943 |
| A3b | Estratificação do alvo [todos_2019_2025] | OK | prevalência de óbito por split: treino=22.63%, validacao=22.63%, holdout=22.63% (amplitude 0.00 p.p.) |
| A3b | Anos em cada split [todos_2019_2025] | OK | todos os anos aparecem nos 3 splits (split aleatório mistura os períodos) |
| A3b | NU_NOTIFIC entre splits [todos_2019_2025] | ATENÇÃO | 10 NU_NOTIFIC aparecem em mais de um split (pode ser vazamento entre treino e validação) |
| A1-C2 | Colunas exigidas pelo C2 | FALHA | ausentes no dataset: dias_sintomas_ate_internacao, sexo_categoria |
| A1-C2 | Coluna de tempo | OK | datetime válido, ordenado: 2019-01-01 -> 2025-12-31 |
| A1-C2 | Alvo | OK | apenas cura/óbito; positivos [2.0] presentes |
| A1-C2 | check_leakage (C2) | OK | nenhuma feature está em `proibidas` |
| A1-C2 | Tamanho | OK | 3,739,615 linhas |
| A1 | Waterfall da coorte [sem_2020_2021] | OK | 4,666,910 -> 1,279,588 registros (27.4%) |
| A1 | Features derivadas [sem_2020_2021] | OK | criadas no dataset: idade_anos, faixa_etaria |
| A1 | Dataset analítico [sem_2020_2021] | ATENÇÃO | 1,279,588 linhas v0.1; features ausentes na base: DIAS_SINTOMAS_ATE_INTERNACAO, SEXO_CATEGORIA |
| A3b | Proporções 70/15/15 [sem_2020_2021] | OK | desvio máximo 0.00 p.p. / treino=895,712, validacao=191,938, holdout=191,938 |
| A3b | Estratificação do alvo [sem_2020_2021] | OK | prevalência de óbito por split: treino=12.12%, validacao=12.12%, holdout=12.12% (amplitude 0.00 p.p.) |
| A3b | Anos em cada split [sem_2020_2021] | OK | todos os anos aparecem nos 3 splits (split aleatório mistura os períodos) |
| A3b | NU_NOTIFIC entre splits [sem_2020_2021] | ATENÇÃO | 9 NU_NOTIFIC aparecem em mais de um split (pode ser vazamento entre treino e validação) |
| A1-C2 | Colunas exigidas pelo C2 | FALHA | ausentes no dataset: dias_sintomas_ate_internacao, sexo_categoria |
| A1-C2 | Coluna de tempo | OK | datetime válido, ordenado: 2019-01-01 -> 2025-12-31 |
| A1-C2 | Alvo | OK | apenas cura/óbito; positivos [2.0] presentes |
| A1-C2 | check_leakage (C2) | OK | nenhuma feature está em `proibidas` |
| A1-C2 | Tamanho | OK | 1,279,588 linhas |
| A3b | Split aleatório x temporal [todos_2019_2025] | ATENÇÃO | PR-AUC (validação): aleatório 0.452 vs temporal 0.364 (Δ +0.087) — o aleatório está otimista; decidir pelo temporal |
| A3b | Split aleatório x temporal [sem_2020_2021] | ATENÇÃO | PR-AUC (validação): aleatório 0.367 vs temporal 0.276 (Δ +0.091) — o aleatório está otimista; decidir pelo temporal |

**Resumo:** 18 OK · 6 atenção · 2 falha(s).
```

### `outputs/tables/pessoa_a/relatorio_A4.md`

- Git: `ignored` · `280 B` · modified `2026-10-17 02:02 UTC`

```markdown
# Relatório de verificações — relatorio_A4

| Etapa | Verificação | Status | Detalhe |
| --- | --- | --- | --- |
| A4 | Dataset congelado | FALHA | dataset_supervisionado.parquet v1.0 FOI ALTERADO após a exportação |

**Resumo:** 0 OK · 0 atenção · 1 falha(s).
```

### `outputs/tables/pessoa_a/tabela_decisoes.csv`

- Git: `ignored` · `3.0 KB` · modified `2026-10-17 02:02 UTC` · 14 rows

```csv
id,etapa,tema,decisao,responsavel,data,status,impacto,evidencia
D-01,A1,Ponto de previsão,DT_INTERNA (admissão); campos posteriores bloqueados,Pessoa A,2026-10-16,proposta,Define quais variáveis podem entrar,Dicionário SIVEP-Gripe (completar)
D-02,A1,Coorte estrita,"HOSPITAL=1, DT_INTERNA válida, período analítico, evolução encerrada",Pessoa A,2026-10-16,proposta,Ver waterfall (a1_waterfall.csv),
D-03,A1,Alvo principal,Óbito SRAG (EVOLUCAO=2) vs cura (EVOLUCAO=1),Pessoa A,2026-10-16,proposta,Alinhar target.positivos do supervised.yaml (G1),
D-04,A1,Evolução desconhecida e óbito outras causas,EVOLUCAO=9/ausente e 3 saem do alvo binário; nunca viram cura,Pessoa A,2026-10-16,proposta,"Exigir filtro EVOLUCAO in {1,2} no loader do C",
D-12,A1,Features derivadas (criadas no dataset analítico),"idade_anos (TP_IDADE), faixa_etaria, intervalo sintomas->internação (inválido se ausente/negativo/>30 dias) + flag, sin/cos da semana ISO da internação",Pessoa A,2026-10-16,proposta,Só informação da admissão; o C2 as encontra no dataset (supervised.yaml),
D-05,A1,Período analítico,"Desenvolvimento [2022, 2023, 2024]; holdout [2025]",Pessoa A,2026-10-16,proposta,Exclui anos fora do período; alinhar G2,
D-06,A2,Ação por tipo de inconsistência de datas,Nascimento posterior ao início dos sintomas -> excluir; Início dos sintomas posterior à notificação -> manter com flag; Início dos sintomas posterior à internação -> manter com flag; Evolução anterior à internação -> excluir; Encerramento anterior à evolução -> manter com flag,Pessoa A,2026-10-16,proposta,Ver a2_coerencia_datas.csv,
D-07,A2,Duplicidades,Linhas exatas removidas; NU_NOTIFIC repetido apenas documentado,Pessoa A,2026-10-16,proposta,Ver a2_duplicidades.csv,
D-08,A2,Maturidade de EVOLUCAO,Meses do holdout com < 90.0% de evolução fechada ficam fora ou sob sensibilidade,Pessoa A,2026-10-16,proposta,Ver a2_maturidade_evolucao_por_mes.csv,
D-09,A2,Variáveis proibidas/condicionais,Matriz de elegibilidade v1.0 (classes incluir/condição/auditoria/excluir),Pessoa A,2026-10-16,proposta,C bloqueia automaticamente (test_leakage); B usa na matriz de clustering,
D-10,A3,Split temporal,"Desenvolvimento [2022, 2023, 2024] / holdout [2025] por DT_INTERNA",Pessoa A,2026-10-16,proposta,supervised.yaml: modo 'datas' e coluna_tempo = dt_interna (G2),
D-13,A3b,Experimento split aleatório 70/15/15 (2019–2025),"Split aleatório estratificado pelo alvo, seed 42; dataset_supervisionado_todos_2019_2025",Pessoa A,2026-10-16,proposta,Comparativo; o padrão do projeto segue a validação temporal (README),a3_benchmark_split_*.csv
D-14,A3b,Cenário sem 2020 e 2021,Mesma análise removendo 2020–2021 (pandemia); dataset_supervisionado_sem_2020_2021,Pessoa A,2026-10-16,proposta,"Compara N, prevalência e desempenho com a base completa (comparacao_cenarios.csv)",
D-11,A4,Seleção de candidatos,"Shortlist por validade, estabilidade, calibração e interpretação — não só maior métrica",Pessoa A,2026-10-16,proposta,Candidatos para confirmação em 18/10,
```

## 19. Snapshot provenance

- Generated UTC: `2026-10-17T16:15:24+00:00`
- Branch / commit: `main` / `3590d686d20a1fbc6bb7b360d422e7d9d071e97f`
- Origin: `https://github.com/Ivan-S-Oliveira/Projeto_Integrador.git`
- Generator options: `{'output_dir': 'docs', 'config': 'configs/supervised.yaml', 'split_mb': 1.0, 'split': True, 'notebook_outputs': True, 'max_output_chars': 6000, 'artifacts': True, 'max_artifact_bytes': 300000, 'max_csv_rows': 60, 'max_inline_bytes': 4000000, 'git_log': 40, 'include_diff': True, 'max_diff_chars': 400000, 'run_tests': False, 'pytest_args': '', 'test_timeout': 1800, 'fail_on_high': False}`
