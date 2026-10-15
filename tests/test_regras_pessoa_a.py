"""Testes das regras da Pessoa A (alvo, datas, aliases, waterfall, auditoria de config)."""
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.protocolo import verificacoes as v  # noqa: E402


@pytest.fixture(scope="module")
def cfg():
    return v.load_config(None)


@pytest.fixture(scope="module")
def demo():
    return v.prepare(v.make_demo(n=3000)[0])


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


def test_log_decision_upsert(tmp_path):
    v.log_decision(tmp_path, "D-01", "tema", "a")
    t = v.log_decision(tmp_path, "D-01", "tema", "b")
    assert len(t) == 1 and t.loc[0, "decisao"] == "b"


def test_decision_table_alerta_complexidade_sem_ganho(cfg, tmp_path):
    res = pd.DataFrame({"modelo": ["baseline"] * 2 + ["logistica"] * 2 + ["boosting"] * 2,
                        "pr_auc": [.15, .15, .40, .40, .401, .401], "roc_auc": [.5] * 2 + [.8] * 2 + [.8] * 2,
                        "brier": [.15] * 2 + [.10] * 2 + [.11] * 2})
    rep = v.Report(tmp_path)
    v.a4_decision_table(res, cfg, rep)
    t = pd.read_csv(tmp_path / "a4_tabela_decisao.csv")
    assert "não justifica" in t.loc[t["modelo"] == "boosting", "alertas_automaticos"].iloc[0]


def test_exporta_dataset_para_o_c2(cfg, tmp_path):
    base = v.make_demo(n=3000)[0]
    base.columns = [c.lower() for c in base.columns]
    base = base.rename(columns={"hospital": "internado"})
    df = v.prepare(base)
    y = tmp_path / "supervised.yaml"
    y.write_text("target: {coluna: evolucao, positivos: [2.0]}\ncoluna_tempo: dt_notific\n"
                 "features: {numericas: [nu_idade_n], categoricas: [febre, internado]}\n", encoding="utf-8")
    out = tmp_path / "dataset_supervisionado.csv"
    meta = v.a1_export_dataset(df, cfg, v.Report(tmp_path), y, path=out)
    d = pd.read_csv(out)
    assert {"evolucao", "dt_notific", "nu_idade_n", "febre", "internado"} <= set(d.columns)
    assert set(d["evolucao"].unique()) <= {1, 2}
    assert d["dt_notific"].is_monotonic_increasing
    assert "dt_evoluca" not in d.columns and meta["n_linhas"] == len(d)


def test_find_base_ignora_dataset_analitico(tmp_path):
    (tmp_path / "data" / "analytical").mkdir(parents=True)
    (tmp_path / "data" / "raw").mkdir(parents=True)
    (tmp_path / "data" / "analytical" / "dataset_supervisionado.parquet").write_bytes(b"x")
    (tmp_path / "data" / "raw" / "srag.csv").write_text("a\n1\n")
    assert v.find_base(tmp_path).name == "srag.csv"


@pytest.mark.parametrize("unidade", ["s", "ms", "us", "texto"])
def test_datas_absurdas_nao_estouram(cfg, tmp_path, unidade):
    import numpy as np
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


def test_colunas_necessarias_ignora_o_resto(cfg):
    schema = ["nu_notific", "hospital", "evolucao", "dt_interna", "coluna_irrelevante_1", "febre", "xyz"]
    cols = v.colunas_necessarias(schema, cfg, None)
    assert "hospital" in cols and "dt_interna" in cols and "febre" in cols
    assert "coluna_irrelevante_1" not in cols and "xyz" not in cols


def _yaml_c2(tmp_path, features):
    y = tmp_path / "supervised.yaml"
    y.write_text("target: {coluna: evolucao, positivos: [2.0]}\ncoluna_tempo: dt_notific\n"
                 f"features: {{numericas: [nu_idade_n], categoricas: {features}, proibidas: [evolucao, dt_evoluca]}}\n",
                 encoding="utf-8")
    return y


def test_contrato_c2_dataset_valido(cfg, tmp_path):
    base = v.make_demo(n=3000)[0]
    base.columns = [c.lower() for c in base.columns]
    y = _yaml_c2(tmp_path, "[febre, dispneia]")
    out = tmp_path / "dataset_supervisionado.csv"
    meta = v.a1_export_dataset(v.prepare(base), cfg, v.Report(tmp_path), y, path=out)
    rep = v.Report(tmp_path, "contrato")
    assert v.validar_contrato_c2(out, y, rep) is True
    assert meta["descartadas_data_tempo_invalida"] >= 0
    assert not rep.has_failure


def test_contrato_c2_feature_inexistente_e_proibida_falham(cfg, tmp_path):
    base = v.make_demo(n=2000)[0]
    base.columns = [c.lower() for c in base.columns]
    y = _yaml_c2(tmp_path, "[febre, tp_gestante]")           # tp_gestante não existe na base
    out = tmp_path / "d.csv"
    v.a1_export_dataset(v.prepare(base), cfg, v.Report(tmp_path), y, path=out)
    rep = v.Report(tmp_path, "c1")
    assert v.validar_contrato_c2(out, y, rep) is False
    assert any(f[1] == "Colunas exigidas pelo C2" and f[2] == v.FAIL for f in rep.findings)
    y2 = _yaml_c2(tmp_path, "[febre, evolucao]")             # feature proibida no X
    rep2 = v.Report(tmp_path, "c2")
    v.validar_contrato_c2(out, y2, rep2)
    assert any(f[1].startswith("check_leakage") and f[2] == v.FAIL for f in rep2.findings)


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
    assert df["INTERVALO_SINT_INTERNA_DIAS"].iloc[[0, 2, 5]].tolist() == [2.0, 10.0, 7.0]
    assert df["INTERVALO_SINT_INTERNA_DIAS"].iloc[[1, 3, 4]].isna().all()
    assert df["SIN_SEMANA"].between(-1, 1).all() and df["COS_SEMANA"].between(-1, 1).all()


def test_derivadas_nao_dependem_do_desfecho(cfg):
    import inspect
    fonte = inspect.getsource(v.add_derived)
    for proibido in ("EVOLUCAO", "dt_evoluca", "dt_encerra", "CLASSI_FIN"):
        assert proibido not in fonte


def test_export_cria_derivadas_pedidas_pelo_yaml(cfg, tmp_path):
    base = v.make_demo(n=3000)[0]
    base.columns = [c.lower() for c in base.columns]
    y = tmp_path / "supervised.yaml"
    y.write_text("target: {coluna: evolucao, positivos: [2.0]}\ncoluna_tempo: dt_notific\n"
                 "features:\n  numericas: [nu_idade_n, idade_anos, intervalo_sint_interna_dias, flag_intervalo_invalido, sin_semana, cos_semana]\n"
                 "  categoricas: [febre, faixa_etaria]\n  proibidas: [evolucao, dt_evoluca]\n"
                 "avaliacao: {grupos: [cs_sexo, faixa_etaria]}\n", encoding="utf-8")
    out = tmp_path / "d.csv"
    meta = v.a1_export_dataset(v.prepare(base), cfg, v.Report(tmp_path), y, path=out)
    d = pd.read_csv(out)
    for col in ("idade_anos", "intervalo_sint_interna_dias", "flag_intervalo_invalido", "sin_semana", "cos_semana",
                "faixa_etaria", "cs_sexo"):
        assert col in d.columns, col
    assert meta["features_ausentes_na_base"] == []
    rep = v.Report(tmp_path, "c")
    assert v.validar_contrato_c2(out, y, rep) is True


def test_auditoria_nao_acusa_derivadas_como_ausentes(cfg, tmp_path):
    y = {"target": {"positivos": [2.0]}, "coluna_tempo": "dt_notific", "temporal": {"modo": "fracao"},
         "features": {"numericas": ["nu_idade_n", "idade_anos", "sin_semana"], "categoricas": ["faixa_etaria", "febre"],
                      "proibidas": ["evolucao"]}}
    rep = v.Report(tmp_path)
    v.a3_config_audit(y, cfg, rep, ["nu_idade_n", "febre", "evolucao", "dt_notific"])
    achados = {f[1]: f[2] for f in rep.findings}
    assert achados["Features do YAML x Parquet"] == v.OK
    assert achados["Features derivadas do YAML"] == v.OK


# ----------------------------------------------------------------------------- split aleatório e cenários
def test_split_aleatorio_proporcoes_estratos_e_reprodutibilidade():
    import numpy as np
    n = 10_000
    y = np.array(["1"] * 8_700 + ["2"] * 1_300)
    a = v.split_aleatorio(n, y, seed=42)
    b = v.split_aleatorio(n, y, seed=42)
    c = v.split_aleatorio(n, y, seed=7)
    assert (a == b).all() and not (a == c).all()                 # reprodutível pela seed; muda com outra seed
    s = pd.Series(a)
    assert s.value_counts().to_dict() == {"treino": 7000, "validacao": 1500, "holdout": 1500}
    for classe, total in (("1", 8700), ("2", 1300)):             # estratificado: cada classe ~70/15/15
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
    y = tmp_path / "supervised.yaml"
    y.write_text("target: {coluna: evolucao, positivos: [2.0]}\ncoluna_tempo: dt_notific\n"
                 "features: {numericas: [nu_idade_n, idade_anos], categoricas: [febre, dispneia, faixa_etaria]}\n",
                 encoding="utf-8")
    df = v.prepare(base)
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
    # prevalência de óbito parecida nos 3 splits (estratificado)
    prev = d_todos.groupby("split")["evolucao"].apply(lambda s: (s == 2).mean())
    assert prev.max() - prev.min() < 0.005
    # arquivos separados por cenário; nada de FALHA nas checagens do split
    assert m_todos["arquivo"] != m_sem["arquivo"]
    assert not [f for f in rep.findings if f[0] == "A3b" and f[2] == v.FAIL]
    # congelamento: hash confere e detecta alteração
    assert v.verificar_dataset_congelado(m_todos["arquivo"], rep) is True
    with open(m_todos["arquivo"], "a", encoding="utf-8") as fh:
        fh.write("\n")
    assert v.verificar_dataset_congelado(m_todos["arquivo"], rep) is False


def test_benchmark_aleatorio_x_temporal_e_comparacao(cfg, tmp_path):
    base = v.make_demo(n=15_000, inicio="2019-01-01", anos=7)[0]
    base.columns = [c.lower() for c in base.columns]
    y = tmp_path / "supervised.yaml"
    y.write_text("target: {coluna: evolucao, positivos: [2.0]}\ncoluna_tempo: dt_notific\n"
                 "features: {numericas: [nu_idade_n, idade_anos, sin_semana, cos_semana], categoricas: [febre, dispneia, faixa_etaria]}\n",
                 encoding="utf-8")
    df = v.prepare(base)
    c2 = json.loads(json.dumps(cfg)); c2["dataset_analitico"]["path"] = str(tmp_path / "dataset.csv")
    rep = v.Report(tmp_path)
    metas, benchs = {}, {}
    for nome, spec in c2["experimentos_split"]["cenarios"].items():
        metas[nome] = v.a3_split_aleatorio_cenario(df, c2, rep, nome, spec["anos"], y)
        benchs[nome] = v.a3_benchmark_split(metas[nome]["arquivo"], y, c2, rep, nome, max_rows=8_000)
        assert {"aleatoria", "temporal_por_ordem"} == set(benchs[nome]["particao"])
        lg = benchs[nome][benchs[nome]["modelo"] == "logistica"]
        assert (lg["roc_auc"] > 0.6).all()                      # o sinal sintético (idade/dispneia) é aprendido
    t = v.comparar_cenarios(metas, benchs, rep)
    assert list(t["cenario"]) == ["todos_2019_2025", "sem_2020_2021"]
    assert t.loc[0, "n_linhas"] > t.loc[1, "n_linhas"]
    assert "pr_auc_aleatoria" in t.columns and "pr_auc_temporal_por_ordem" in t.columns


def test_graficos_do_split_sao_gerados(cfg, tmp_path):
    base = v.make_demo(n=12_000, inicio="2019-01-01", anos=7)[0]
    base.columns = [c.lower() for c in base.columns]
    y = tmp_path / "supervised.yaml"
    y.write_text("target: {coluna: evolucao, positivos: [2.0]}\ncoluna_tempo: dt_notific\n"
                 "features: {numericas: [nu_idade_n], categoricas: [febre, dispneia]}\n", encoding="utf-8")
    df = v.prepare(base)
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


# ----------------------------------------------------------------------------- memória: colunas category
def _base_texto(n=15_000):
    import numpy as np
    base = v.make_demo(n=n, inicio="2019-01-01", anos=7)[0]
    base.columns = [c.lower() for c in base.columns]
    for c in ("dt_nasc", "dt_evoluca", "dt_encerra", "dt_sin_pri", "dt_interna", "dt_notific"):
        base[c] = base[c].dt.strftime("%Y-%m-%d")
    for c in ("evolucao", "hospital", "tp_idade"):
        base[c] = base[c].astype("Int64").astype(str).replace("<NA>", np.nan)
    return base


def _como_categoria(df):
    d = df.copy()
    for c in d.columns:
        if (d[c].dtype == object or pd.api.types.is_string_dtype(d[c])) and c != "nu_notific":
            d[c] = d[c].astype("category")
    return d


def test_parse_date_categorica_igual_a_texto():
    s = pd.Series(["2022-03-05", "05/03/2022", None, "9999-12-31", "lixo", "2022-03-05"] * 50)
    a = v.parse_date(s)
    b = v.parse_date(s.astype("category"))
    assert a.isna().tolist() == b.isna().tolist()
    assert a.dropna().tolist() == b.dropna().tolist()


def test_resultados_iguais_com_colunas_category(cfg, tmp_path):
    """O resultado do A1/A2 não pode mudar quando o texto é lido como `category` (leitura compacta)."""
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
    y = tmp_path / "supervised.yaml"
    y.write_text("target: {coluna: evolucao, positivos: [2.0]}\ncoluna_tempo: dt_notific\n"
                 "features: {numericas: [nu_idade_n, idade_anos], categoricas: [febre, faixa_etaria, cs_sexo]}\n", encoding="utf-8")
    df = v.prepare(_como_categoria(_base_texto()))
    c2 = json.loads(json.dumps(cfg)); c2["dataset_analitico"]["path"] = str(tmp_path / "d.csv")
    rep = v.Report(tmp_path)
    meta = v.a3_split_aleatorio_cenario(df, c2, rep, "todos_2019_2025", [2019, 2020, 2021, 2022, 2023, 2024, 2025], y)
    assert meta["n_linhas"] > 0 and v.validar_contrato_c2(meta["arquivo"], y, rep) is True
    v.a3_leak_scan(v.a1_cohort(df, c2), c2, rep)
    assert not [f for f in rep.findings if f[2] == v.FAIL]


def test_colunas_minimas_sao_menos_que_as_classificadas(cfg):
    schema = ["nu_notific", "hospital", "evolucao", "dt_interna", "dt_notific", "dt_sin_pri", "nu_idade_n", "tp_idade",
              "uti", "antiviral", "vacina_cov", "cs_raca", "coluna_x", "febre"]
    minimas = v.colunas_necessarias(schema, cfg, None, modo="minimas")
    classif = v.colunas_necessarias(schema, cfg, None, modo="classificadas")
    assert set(minimas) < set(classif)
    assert {"hospital", "evolucao", "dt_interna", "nu_idade_n", "tp_idade", "dt_sin_pri"} <= set(minimas)
    assert not ({"antiviral", "vacina_cov", "coluna_x"} & set(minimas))
    assert {"antiviral", "vacina_cov"} <= set(classif)
