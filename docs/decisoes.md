# Decisões metodológicas

Resumo das decisões que valem para a entrega. O registro completo, com o
histórico de cada mudança, está em `docs/historico/decisoes_completo.md`.

## 1. Pergunta e ponto de previsão

Estimar o risco de óbito por SRAG no momento da internação hospitalar. A
referência temporal é `dt_interna`. Só entram no modelo informações
plausivelmente disponíveis até a admissão.

Os gates do projeto vão de G1 a G9, sem G3: essa etapa foi absorvida pelo
G2 em 18/10 (ver `docs/historico/decisoes_completo.md`).

## 2. Dados

- Fonte: SRAG 2019–2026 (Ministério da Saúde), versão `dados-v2`
  (`srag.parquet`), baixada da release do GitHub do projeto.
- `dados-v2` substitui `dados-v1` porque corrige `dt_notific` e preserva as
  datas individuais das fontes.

## 3. Coorte

Contrato `configs/final_cohort_v1.yaml`, com sete regras de exclusão
aplicadas em ordem:

| Regra | Critério | Linhas que atendem |
|---|---|---|
| D_COORTE_001 | hospital diferente de 1 | 232.253 |
| D_COORTE_002 | data de internação inválida | 304.245 |
| D_COORTE_003 | evolução diferente de cura ou óbito por SRAG | 530.370 |
| D_COORTE_004 | internação antes de 2019 | 48 |
| D_COORTE_005 | internação depois de 2026 | 76 |
| D_COORTE_006 | intervalo sintomas → internação negativo | 24.361 |
| D_COORTE_007 | intervalo acima de 60 dias | 11.708 |

As regras se sobrepõem: saem 782.182 linhas e a coorte final fica com
3.884.728 de 4.666.910 (`data/analytical/coorte_final.parquet`).

## 4. Desfecho

- `evolucao = 1` (cura) → classe 0; `evolucao = 2` (óbito por SRAG) → classe 1.
- Óbito por outras causas (3), ignorado (9) e ausentes ficam fora. Desfecho
  desconhecido nunca vira cura.
- `evolucao`, datas de evolução, encerramento e digitação não são preditoras.

## 5. Uso dos anos e partição

Partição-mestre determinística por `group_id` (hash, seed 42), estratificada
por ano × desfecho × região, com no mínimo 5 grupos por estrato — com fallback
automático para ano × desfecho quando algum estrato tem menos de 5 grupos
(registrado como `"ano × alvo (fallback)"` no manifesto da partição; as
prevalências dos blocos de desenvolvimento continuam dentro de ±0,5 p.p. de
8,44% mesmo assim):

| Bloco | Anos | Fração | Uso |
|---|---|---|---|
| `train_ref` | 2019, 2023–2025 | 70% | treino |
| `val_ref` | 2019, 2023–2025 | 15% | escolha de variáveis e hiperparâmetros; calibração e limiar em duas metades (`val_cal` e `val_meas`) |
| `test_ref` | 2019, 2023–2025 | 15% | Teste A (resultado principal) |
| `test_pandemic` | 2020–2022 | 100% | parte do Teste B |

- `group_id` é o `nu_notific`; sem número, usa o `id_registro`. Nenhum grupo
  aparece em dois blocos. Grupos em mais de um estrato vão para quarentena
  (2 grupos, 4 linhas).
- 2026 é parcial (dados até setembro) e fica no bloco `exploracao`, fora de
  treino, validação e testes.
- Teste B = `test_ref` + `test_pandemic`, sempre com o resultado de 2020–2022
  em separado. A diferença A × B mede robustez temporal, não efeito causal
  da pandemia.
- Limitação: variáveis, hiperparâmetros, calibração e limiar usam o mesmo
  `val_ref`. A medida honesta é a do teste, aberto uma única vez.

## 6. Variáveis

Modelo principal com 30 variáveis (features.final). Entraram saturacao
  e desc_resp (fazem parte da definição de caso de SRAG e da ficha de
  admissão; ganho de 0,0176 de PR-AUC na ablação, regressão logística —
  outputs/tables/ablacoes_val_ref.csv, linha P_menos_gravidade). Saíram perd_olft,
  `perd_pala` e `fadiga`, que funcionam como marcador de período (em branco
  em mais de 99% das fichas de 2019).
- Escolaridade, UF e vacinação (`vacina_cov_previa`, só doses pelo menos 1
  dia antes da internação) ficam como contexto, fora do modelo principal.
- Datas brutas não entram; delas saem idade, intervalos e flags.
- Vazio, ignorado, "não se aplica" e "não" são categorias diferentes. A
  ausência vira a categoria `AUSENTE`; não há indicadores de ausência.
- Tratamentos, textos livres, IMC e município ficam fora (EDA ou extensões).

## 7. Modelos

- Baseline, regressão logística e Hist Gradient Boosting. Árvore e random
  forest foram descartadas nos pilotos.
- Métrica principal: PR-AUC na validação.
- Busca curta, sem validação cruzada. Regras definidas antes dos números:
  diferença menor que 0,002 → configuração mais simples; o boosting só vence
  a logística com ganho de pelo menos 0,005.
- Finalista: Hist Gradient Boosting, `learning_rate` 0,05, `max_iter` 500,
  `max_leaf_nodes` 63, `min_samples_leaf` 100, `l2_regularization` 0,1,
  `early_stopping`, sem peso de classe. PR-AUC 0,3616, ROC-AUC 0,8668 e
  Brier 0,0631 em `val_ref`.

## 8. Calibração e limiar

- Calibração `sigmoid`, ajustada em `val_cal` (empate prático com o modelo
  sem calibração; `isotonic` foi pior).
- Limiar 0,1178: maior precisão entre os cortes com recall de pelo menos
  0,80, escolhido em `val_cal` e aplicado sem reajuste em `val_meas`
  (recall 0,809; precisão 0,249).

## 9. Abertura do teste

- `test_ref` e `test_pandemic` ficam bloqueados no código até o gate G9.
- O teste é aberto uma única vez, com tudo congelado. Depois disso o G9
  fica `executado`, o manifesto registra `test_opened` e nada mais muda.
- Hipóteses registradas antes (docs/historico/decisoes_completo.md, §29.38):
  (1) Teste A com PR-AUC entre 0,30 e 0,36; (2) Teste A com ROC-AUC entre
  0,85 e 0,87; (3) Teste B fica entre o Teste A e 2020–2022, mais perto de
  2020–2022 por volume; (4) em 2020–2022, PR-AUC ÷ prevalência igual ou
  menor que no Teste A; (5) em 2020–2022, Brier pior que no Teste A; (6) em
  2020–2022, razão observado/esperado acima de 1 (entre 1,5 e 3), porque a
  calibração foi feita com prevalência de 8,4% e a pandemia tem cerca de
  26%. Resultado contrário entra no relatório como achado, nunca como
  motivo para reajuste.

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

## 10. Princípios

1. Nenhuma informação posterior à admissão no modelo.
2. Transformações ajustadas só no treino.
3. Teste isolado até a avaliação final.
4. Exclusões da coorte registradas no waterfall.
5. O alvo não participa da formação dos clusters.
