# Relatorio do lote (2026-11-05 21:19 UTC)

- commit: `af7811bce1` · ramo `enxugamento`
- arvore Git: limpa
- etapas: caminhos, comentarios
- modo: normal

Resumo: caminhos: ok · comentarios: ok

## caminhos · tira caminhos pessoais das saidas salvas (#189)

Resultado: **ok**

```text
==============================================================================
RELATORIO (copia em <HOME>\AppData\Local\Temp\caminhos_b9k6a7kd)
==============================================================================
notebooks/11_validacao_final.ipynb                                        17 troca(s)
data/analytical/coorte_final.manifest.json                                 3 troca(s)
data/analytical/manifesto_particao.json                                    2 troca(s)
data/analytical/manifesto_supervisionado.json                              2 troca(s)
outputs/tables/04_eda_resumo_fonte.csv                                     1 troca(s)
outputs/tables/05_cinco_familias_definitiva_manifesto.json                 9 troca(s)
outputs/tables/05_pilotos_definitiva_manifesto.json                       10 troca(s)
outputs/tables/07_baseline_logistica_final_manifesto.json                  3 troca(s)
outputs/tables/09_ajuste_fino_final_manifesto.json                         5 troca(s)
outputs/tables/10_calibracao_limiar_final_manifesto.json                   8 troca(s)
outputs/tables/11_ensaio_validacao_final_final_20261105T205921Z_manifesto.json    11 troca(s)
outputs/tables/11_validacao_final_final_20261105T211527Z_manifesto.json    11 troca(s)
outputs/runs/20261105T200852965099Z_07_baseline_logistica/metadata.json     1 troca(s)
outputs/runs/20261105T201129470875Z_09_ajuste_fino/metadata.json           1 troca(s)
outputs/runs/20261105T201249483681Z_10_calibracao_limiar/metadata.json     1 troca(s)
outputs/runs/20261105T205923835407Z_11_ensaio_validacao_final/metadata.json     1 troca(s)
outputs/runs/20261105T211647390785Z_11_validacao_final/metadata.json       1 troca(s)
------------------------------------------------------------------------------
arquivos que mudam: 17 | trocas: 87
AINDA APARECE nome pessoal ou da empresa (2):
notebooks/03_eda_primeira_passagem.ipynb:10495: "  \"arquivo_completo\": \"C:\\\\Users\\\\ivanI\\\\OneDrive\\\\Documentos\\\\Projetos\\\\Projeto_Int
notebooks/03_eda_primeira_passagem.ipynb:10496: "  \"arquivo_revisao\": \"C:\\\\Users\\\\ivanI\\\\OneDrive\\\\Documentos\\\\Projetos\\\\Projeto_Inte
Relatorio pronto. Nada foi gravado. Para gravar: rode de novo com --aplicar.
```

## comentarios · remove comentarios do codigo, notebooks e YAML (#189)

Resultado: **ok**

```text
==============================================================================
RELATORIO (copia em <HOME>\AppData\Local\Temp\limpeza_8j3d5cy1)
==============================================================================
configs/decisoes.yaml                                        comentarios=   3 docstrings=  0
configs/final_cohort_v1.yaml                                 comentarios=   1 docstrings=  0
configs/supervised.yaml                                      comentarios=  10 docstrings=  0
notebooks/01_extracao.ipynb                                  comentarios=   7 docstrings=  0
notebooks/02_coorte_definitiva.ipynb                         comentarios=   9 docstrings=  0
notebooks/03_eda_primeira_passagem.ipynb                     comentarios= 131 docstrings=  1
notebooks/04_eda_temporal_agrupamento.ipynb                  comentarios= 139 docstrings= 10
notebooks/05_supervisionado_pilotos.ipynb                    comentarios=  20 docstrings=  0
notebooks/07_baseline_logistica.ipynb                        comentarios=   8 docstrings=  0
notebooks/08_ablacoes_variaveis.ipynb                        comentarios=   3 docstrings=  0
notebooks/09_ajuste_fino.ipynb                               comentarios=   1 docstrings=  0
notebooks/10_calibracao_limiar.ipynb                         comentarios=   2 docstrings=  0
notebooks/11_validacao_final.ipynb                           comentarios=  14 docstrings=  0
src/avaliacao.py                                             comentarios=   7 docstrings= 13
src/config.py                                                comentarios=   9 docstrings= 12
src/dados.py                                                 comentarios=  25 docstrings= 23
src/features.py                                              comentarios=   6 docstrings= 10
src/modelos.py                                               comentarios=   8 docstrings= 11
src/registro.py                                              comentarios=   2 docstrings=  0
tests/conftest.py                                            comentarios=   0 docstrings=  1
tests/test_artefato.py                                       comentarios=   1 docstrings=  1
tests/test_calibracao.py                                     comentarios=   1 docstrings=  1
tests/test_coorte.py                                         comentarios=   0 docstrings=  1
tests/test_dados.py                                          comentarios=   0 docstrings=  1
tests/test_features.py                                       comentarios=   0 docstrings=  1
tests/test_modelos.py                                        comentarios=   0 docstrings=  4
tests/test_particao.py                                       comentarios=   1 docstrings=  0
tests/test_protocolo.py                                      comentarios=   2 docstrings=  2
tests/test_temporal.py                                       comentarios=   0 docstrings=  2
tools/clean_project.py                                       comentarios=  24 docstrings=  5
tools/maturidade_desfecho.py                                 comentarios=   2 docstrings=  1
tools/medir_notebook.py                                      comentarios=   0 docstrings=  1
tools/perfil_celulas.py                                      comentarios=   1 docstrings=  2
tools/perfilar_cadeia_notebooks_v2.py                        comentarios=   0 docstrings=  1
tools/read_outputs.py                                        comentarios=   0 docstrings=  1
tools/update_project_reference.py                            comentarios= 121 docstrings= 29
------------------------------------------------------------------------------
arquivos que mudam: 36 | comentarios: 558 | docstrings: 134 | celulas vazias: 0
Relatorio pronto. Nada foi gravado. Para gravar: rode de novo com --aplicar.
```
