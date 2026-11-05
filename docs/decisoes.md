# Decisões metodológicas

Resumo das decisões que valem para a entrega. O registro completo, com o
histórico de cada mudança, está em `docs/historico/decisoes_completo.md`.

## 1. Pergunta e ponto de previsão

Estimar o risco de óbito por SRAG no momento da internação hospitalar. A
referência temporal é `dt_interna`. Só entram no modelo informações
plausivelmente disponíveis até a admissão.

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
por ano × desfecho × região, com no mínimo 5 grupos por estrato:

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

- Modelo principal com 30 variáveis (`features.final`). Entraram `saturacao`
  e `desc_resp` (fazem parte da definição de caso de SRAG e da ficha de
  admissão; ganho de 0,0195 de PR-AUC na ablação). Saíram `perd_olft`,
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
- Hipóteses registradas antes: Teste A com PR-AUC entre 0,30 e 0,36 e
  ROC-AUC entre 0,85 e 0,87; em 2020–2022, Brier pior e razão
  observado/esperado acima de 1, porque a calibração foi feita com
  prevalência de 8,4% e a pandemia tem cerca de 26%. Resultado contrário
  entra no relatório como achado, nunca como motivo para reajuste.

## 10. Princípios

1. Nenhuma informação posterior à admissão no modelo.
2. Transformações ajustadas só no treino.
3. Teste isolado até a avaliação final.
4. Exclusões da coorte registradas no waterfall.
5. O alvo não participa da formação dos clusters.
