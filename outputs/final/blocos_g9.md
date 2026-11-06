# Blocos do G9

Fonte: `outputs/tables/11_validacao_final_final_20261105T211527Z_manifesto.json` · commit atual `52970fc` · teste aberto em 05/11/2026 às 21:15 UTC.

## Bloco 1 · docs/decisoes.md (no fim da seção 9, depois das hipóteses)

```markdown
### Resultado da abertura (teste aberto uma única vez em 05/11/2026, 21:15 UTC, commit 52970fc)

O teste foi aberto com tudo congelado: Hist Gradient Boosting, 30 variáveis, calibração `sigmoid` e limiar 0,1178. Nada foi reajustado depois.

| Janela | Blocos | n | Óbitos | Prevalência | PR-AUC | PR-AUC ÷ prevalência | ROC-AUC | Brier | O/E | Sensibilidade | Precisão |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Teste A (principal) | test_ref | 119.245 | 10.065 | 8,4% | 0,369 | 4,37x | 0,869 | 0,0628 | 0,99 | 0,813 | 0,252 |
| 2020–2022 (isolado) | test_pandemic | 2.915.829 | 771.095 | 26,4% | 0,457 | 1,73x | 0,728 | 0,1835 | 1,66 | 0,792 | 0,379 |
| Teste B (A + 2020–2022) | test_ref+test_pandemic | 3.035.074 | 781.160 | 25,7% | 0,454 | 1,77x | 0,735 | 0,1788 | 1,64 | 0,792 | 0,376 |

Teste A, com intervalo de 95% por bootstrap de grupos (1000 réplicas): PR-AUC 0,369 (IC 95%: 0,359 a 0,379); ROC-AUC 0,869 (IC 95%: 0,865 a 0,872); Brier 0,0628 (IC 95%: 0,0618 a 0,0637).

Calibração por janela: Teste A: O/E 0,99, inclinação 1,01, ECE por quantis 0,002; 2020–2022: O/E 1,66, inclinação 0,82, ECE por quantis 0,105; Teste B: O/E 1,64, inclinação 0,83, ECE por quantis 0,101.

| Hipótese registrada antes do teste | Resultado | Leitura |
|---|---|---|
| Teste A: PR-AUC entre 0,30 e 0,36 | 0,369 | fora do previsto (acima da faixa) |
| Teste A: ROC-AUC entre 0,85 e 0,87 | 0,869 | dentro do previsto |
| 2020–2022: Brier pior que no Teste A | 0,1835 contra 0,0628 | dentro do previsto |
| 2020–2022: O/E acima de 1 | 1,66 | dentro do previsto |

Resultado fora do previsto entra como achado, nunca como motivo para reajuste.
```

## Bloco 2 · README.md (trocar o parágrafo da seção "Resultados")

Apague:

```markdown
Validação (`val_ref`): PR-AUC 0,362, ROC-AUC 0,867, Brier 0,063. Os
resultados do teste ficam no relatório final, depois da abertura única.
```

Cole no lugar:

```markdown
Validação (`val_ref`): PR-AUC 0,362, ROC-AUC 0,867, Brier 0,063.

Teste aberto uma única vez em 05/11/2026. No Teste A (`test_ref`, n = 119.245): PR-AUC 0,369 (4,37x a prevalência), ROC-AUC 0,869, Brier 0,0628, sensibilidade 0,813 e precisão 0,252 no limiar 0,1178. Em 2020–2022 (isolado): PR-AUC 0,457, ROC-AUC 0,728, Brier 0,1835. As tabelas estão em `resultados/`.
```

## Bloco 3 · configs/supervised.yaml (o notebook já gravou; só conferir)

```yaml
  G9_holdout:
    status: executado
    executado_em: "2026-11-05T21:15:27.499663+00:00"
    n_acessos: 1
```

## Bloco 4 · resultados/LEIA-ME.md (lista dos arquivos da abertura)

| Arquivo | Bytes | SHA-256 (12) |
|---|---|---|
| `outputs/tables/11_validacao_final_final_20261105T211527Z_analise_erros.csv` | 246 | b607be67b1cf |
| `outputs/tables/11_validacao_final_final_20261105T211527Z_calibracao_por_ano.csv` | 1.018 | 0e477c048687 |
| `outputs/tables/11_validacao_final_final_20261105T211527Z_curva_2019.csv` | 605 | 986720c0fe7e |
| `outputs/tables/11_validacao_final_final_20261105T211527Z_curva_2020.csv` | 659 | f1b4b8705e32 |
| `outputs/tables/11_validacao_final_final_20261105T211527Z_curva_2021.csv` | 652 | 6a043c864ec0 |
| `outputs/tables/11_validacao_final_final_20261105T211527Z_curva_2022.csv` | 651 | 0f53ef464bc5 |
| `outputs/tables/11_validacao_final_final_20261105T211527Z_curva_2023.csv` | 631 | b9430aa0d1ce |
| `outputs/tables/11_validacao_final_final_20261105T211527Z_curva_2024.csv` | 634 | 4be7ea408777 |
| `outputs/tables/11_validacao_final_final_20261105T211527Z_curva_2025.csv` | 617 | 65b34b2db913 |
| `outputs/tables/11_validacao_final_final_20261105T211527Z_fn_amostra.csv` | 2.668 | 7c32f1fb1cab |
| `outputs/tables/11_validacao_final_final_20261105T211527Z_fn_por_faixa_etaria.csv` | 317 | 959fd0e1f633 |
| `outputs/tables/11_validacao_final_final_20261105T211527Z_fn_por_regiao_residencia.csv` | 257 | b19801e2ccf4 |
| `outputs/tables/11_validacao_final_final_20261105T211527Z_ic_bootstrap.csv` | 382 | 3cb517ff3884 |
| `outputs/tables/11_validacao_final_final_20261105T211527Z_janelas.csv` | 1.052 | ba00f30c4a08 |
| `outputs/tables/11_validacao_final_final_20261105T211527Z_matriz_confusao.csv` | 102 | d0857ba8460e |
| `outputs/tables/11_validacao_final_final_20261105T211527Z_metricas.csv` | 365 | 6f25483939e8 |
| `outputs/tables/11_validacao_final_final_20261105T211527Z_metricas_por_ano.csv` | 927 | bde13b28f9c2 |
| `outputs/tables/11_validacao_final_final_20261105T211527Z_por_grupo_teste_a_ano_internacao.csv` | 1.042 | 58dd05f7d9d0 |
| `outputs/tables/11_validacao_final_final_20261105T211527Z_por_grupo_teste_a_cs_raca.csv` | 1.697 | c3667d18dbf3 |
| `outputs/tables/11_validacao_final_final_20261105T211527Z_por_grupo_teste_a_cs_zona.csv` | 1.255 | 61bf194dda07 |
| `outputs/tables/11_validacao_final_final_20261105T211527Z_por_grupo_teste_a_faixa_etaria.csv` | 1.981 | 3b6e09505780 |
| `outputs/tables/11_validacao_final_final_20261105T211527Z_por_grupo_teste_a_regiao_residencia.csv` | 1.360 | ef6979c79e48 |
| `outputs/tables/11_validacao_final_final_20261105T211527Z_por_grupo_teste_a_sexo_categoria.csv` | 657 | 1124e70d6669 |
| `outputs/tables/11_validacao_final_final_20261105T211527Z_por_grupo_teste_a_sg_uf.csv` | 6.267 | b2ebf7bad89c |
| `outputs/tables/11_validacao_final_final_20261105T211527Z_por_grupo_teste_b_ano_internacao.csv` | 1.742 | f4dddd5c379b |
| `outputs/tables/11_validacao_final_final_20261105T211527Z_por_grupo_teste_b_faixa_etaria.csv` | 2.036 | ec5aac48e68e |
| `outputs/tables/11_validacao_final_final_20261105T211527Z_por_grupo_teste_b_regiao_residencia.csv` | 1.512 | d976b9d68e68 |
| `outputs/tables/11_validacao_final_final_20261105T211527Z_por_grupo_teste_b_sexo_categoria.csv` | 826 | a8572155b057 |
| `outputs/tables/11_validacao_final_final_20261105T211527Z_por_grupo_teste_b_sg_uf.csv` | 6.508 | 907d9765e005 |
| `outputs/tables/11_validacao_final_final_20261105T211527Z_manifesto.json` | 6.918 | 67d46b69151f |

## Bloco 5 · comentário para o card do painel (#2)

Teste aberto uma vez em 05/11/2026 às 21:15 UTC, commit 52970fc. Teste A: PR-AUC 0,369, ROC-AUC 0,869, Brier 0,0628. 2020–2022: PR-AUC 0,457, Brier 0,1835. Hipóteses: PR-AUC fora do previsto (acima da faixa); ROC-AUC dentro do previsto; Brier de 2020–2022 dentro do previsto; O/E dentro do previsto.
