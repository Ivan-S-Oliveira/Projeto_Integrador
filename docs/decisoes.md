# Registro de Decisões Metodológicas

Este arquivo registra as decisões que afetam a coorte, a preparação dos
dados, os experimentos e a interpretação dos resultados do Projeto
Integrador SRAG.

Decisões específicas de cada variável ficam em
`configs/dicionario_variaveis_v1.csv`. Visões reduzidas podem ser geradas
em `outputs/tables/`, mas não constituem uma segunda fonte editável.

Este documento registra somente decisões gerais ou com impacto em várias
etapas do projeto.

Última atualização: 21/10/2026.

---

## 1. Status das decisões metodológicas

### 1.1 Decisões fechadas

- Dataset oficial: `dados-v2`.
- Ponto de previsão: admissão hospitalar, operacionalizada por `dt_interna`.
- Ano de `dt_interna`, e não de `dt_notific`, como referência de elegibilidade temporal.
- Coorte definitiva inicial: seleção de features construída e auditada na coorte provisória B, promovida e congelada para o fluxo principal.
- Alvo principal: `evolucao = 1` versus `evolucao = 2`.
- Desenvolvimento: apenas 2019, 2023, 2024 e 2025.
- Blocos de desenvolvimento: `train_ref`, `val_tune`, `val_cal` e `val_meas`.
- Teste A: `test_ref`, com 2019, 2023, 2024 e 2025 e grupos nunca usados no desenvolvimento; é o resultado principal.
- Teste B: união lógica de `test_ref` com `test_pandemic`, cobrindo 2019–2025; é a avaliação ampliada de robustez temporal.
- `test_pandemic`: somente 2020, 2021 e 2022, sem participação em qualquer decisão de desenvolvimento.
- Resultado pandêmico: 2020–2022 sempre reportado separadamente, além do Teste B agregado.
- 2026: fora do desenvolvimento e dos Testes A/B; exploração opcional posterior, sem reajuste.
- Interpretação A × B: sensibilidade à composição temporal, sem interpretação causal do efeito da pandemia.
- Testes fechados: `test_ref` e `test_pandemic` permanecem inacessíveis até G9.
- Partição-mestre: seis blocos (`train_ref`, `val_tune`, `val_cal`, `val_meas`, `test_ref`, `test_pandemic`) materializados por `criar_particao_mestra` com o método `hash_grupo_estratificado_mestre_v1`. Frações nos anos compartilhados: `0.70/0.05/0.05/0.05/0.15`; `min_grupos_por_estrato: 5`.
- 2026 é marcado como `exploracao`, rótulo separado do fluxo principal.
- Tratamentos: somente EDA e auditoria até a conclusão do modelo principal.
- Textos livres: EDA, sem NLP completo antes do Fine Tuning.
- Geografia: UF de residência preservada; comparação sem geografia × região obrigatória, e UF como preditora é condicional.
- Município de residência: extensão posterior ao modelo principal.
- `saturacao` e `desc_resp`: sensibilidade de gravidade no cenário vencedor, fora do modelo principal até o contrato final de features.
- Internações anteriores aos sintomas: auditoria com `nosocomial` antes de qualquer exclusão.
- `sem_pri`: auditoria e descrição epidemiológica, sem uso direto nas matrizes.

### 1.2 Decisões pendentes

- Regra definitiva para identificadores repetidos e destino dos grupos em quarentena.
- Aprovação do G1 com alvo e lista final de features.
- Escolha final do método de calibração no G7, após o ajuste fino.
- Escolha final do critério e valor do limiar no G8, usando somente validação.
- Aprovação conjunta do G9 depois do congelamento de features, modelo, hiperparâmetros, calibrador, limiar, commit e manifestos.

### 1.3 Desenho supersedido

Até 10/10/2026, o documento registrava coorte 2019–2026, manutenção dos
anos pandêmicos no desenvolvimento e divisão aleatória 70/15/15. Esse
desenho foi supersedido em 18/10/2026 pelo contrato das seções 5, 21, 22
e 28. O registro histórico permanece nesta subseção, mas não deve
orientar novas execuções.

## 2. Dataset oficial do projeto

- O dataset oficial é o `dados-v2`.
- O arquivo correspondente é `srag.parquet`.
- A identidade técnica do dataset — hash, tamanho, dimensões, cobertura
  temporal, data de geração e fonte — fica em
  `data/manifest_dados-v2.yaml`.
- Os notebooks acessam o dataset por
  `src.utils.storage.read_srag(columns=...)`.
- Caminhos locais absolutos não devem ser incorporados aos notebooks.
- A versão `dados-v2` substitui a `dados-v1` porque corrige a geração de
  `dt_notific` e preserva as datas individuais das fontes oficiais.
- O manifesto do dataset é separado deste registro porque descreve
  propriedades técnicas do artefato, enquanto este arquivo registra
  escolhas metodológicas.

---

## 3. Pergunta e ponto de previsão

O projeto estima o risco de óbito por SRAG no momento da admissão
hospitalar. A referência temporal é `dt_interna`.

Somente informações plausivelmente disponíveis até a admissão entram no
modelo principal.

Informações posteriores à admissão podem ser mantidas na coorte
auditável para construção do rótulo, controle de qualidade, auditoria,
EDA e análises futuras de sensibilidade. A permanência dessas
informações na coorte não autoriza seu uso como preditoras.

---

## 4. Coorte analítica

A coorte é construída em notebook específico, e não no Notebook 01 de
EDA.

Critérios da coorte auditável:

- hospitalização confirmada;
- `dt_interna` válida;
- cobertura bruta de 2019 a 2026, preservada para auditoria;
- `evolucao` elegível para o alvo principal;
- remoção somente de duplicidades exatas;
- auditoria de identificadores repetidos não idênticos;
- waterfall com contagens antes e depois de cada filtro.

A cobertura auditável não determina o uso experimental dos anos. Para o
fluxo principal:

- 2019, 2023, 2024 e 2025 alimentam desenvolvimento e Teste A, com
  grupos disjuntos;
- 2020–2022 ficam exclusivamente em `test_pandemic`;
- 2026 fica fora dos blocos principais e é apenas exploração opcional
  posterior.

A coorte definitiva inicial utiliza a seleção de features já construída
e auditada na coorte provisória B. Sua promoção gera
`coorte_final.parquet`, `coorte_waterfall.csv`, `variaveis_finais.csv` e
`manifesto_coorte.json`, acompanhados de SHA-256, commit, schema,
cobertura temporal, contagens e versão.

A coorte auditável preserva variáveis amplas para EDA, auditoria,
transformação e experimentos. Permanecer na coorte não significa
inclusão automática nos modelos.

## 5. Período da coorte e uso dos anos

A fonte `dados-v2` cobre registros de 2019 a 2026. O experimento usa os
anos de forma assimétrica e definida antes da avaliação.

### 5.1 Desenvolvimento de referência

Somente 2019, 2023, 2024 e 2025 alimentam `train_ref`, `val_tune`,
`val_cal` e `val_meas`. Esses blocos são disjuntos por `group_id`.
Nenhum registro de 2020–2022 ou 2026 participa de decisões de
desenvolvimento.

### 5.2 Teste A

`test_ref` contém registros de 2019, 2023, 2024 e 2025 pertencentes a
grupos nunca usados no desenvolvimento. É o resultado principal do
projeto.

### 5.3 Teste B

O Teste B é a união lógica de `test_ref` com `test_pandemic`. O segundo
bloco contém exclusivamente 2020–2022. O agregado 2019–2025 mede a
robustez do mesmo modelo congelado quando os anos pandêmicos são
acrescentados à avaliação.

O Teste B nunca é apresentado sozinho. Acompanham-no: resultado
exclusivo de 2020–2022, métricas por ano, região e UF, prevalência,
PR-AUC, PR-AUC/prevalência, ROC-AUC, Brier e calibração.

### 5.4 Exploração opcional de 2026

2026 é parcial e fica fora de treino, validações e Testes A/B. Só é
avaliado depois da conclusão dos testes principais, relatório e revisão,
sem recalibração, novo limiar ou qualquer reajuste.

### 5.5 Interpretação

A diferença A × B descreve sensibilidade à composição temporal e não
identifica causalmente o efeito da pandemia. Diferenças de prevalência e
volume acompanham as métricas.

### 5.6 Contagens e auditoria

O manifesto da partição-mestre registra, por bloco, linhas, grupos,
anos, prevalência, região e hash, depois dos filtros de hospitalização,
data, desfecho, duplicidades e coerência temporal.

O gerador é `src/data/split.py::criar_particao_mestra`. A função lê
`temporal.blocos` do `supervised.yaml` e falha com `RuntimeError` se um
`group_id` aparecer em mais de um bloco — condição que normalmente
indica linhas de um mesmo grupo em anos pandêmicos e não pandêmicos.

## 6. Identificadores e duplicidades

- `nu_notific` é o identificador técnico.
- `nu_notific` não é preditora.
- Duplicidades exatamente iguais podem ser removidas.
- Registros com o mesmo `nu_notific` mas conteúdo diferente não são
  eliminados automaticamente.
- Identificadores repetidos não idênticos são inspecionados e
  sinalizados.
- Não se escolhe arbitrariamente a primeira ocorrência de um
  identificador repetido.
- Um mesmo identificador ou episódio não pode aparecer em mais de uma
  partição de treino, validação ou teste.
- As decisões sobre duplicidades são refletidas no waterfall da coorte.

---

## 7. Estrutura temporal

- `dt_interna` é a âncora temporal da coorte e do ponto de previsão.
- `dt_sin_pri` deriva o intervalo entre início dos sintomas e
  internação.
- `dt_sin_pri` também é a fonte dos atributos sazonais.
- `sem_pri` é mantida apenas para descrição epidemiológica e auditoria
  de consistência.
- `sem_pri` não entra diretamente nas matrizes de modelagem.
- Datas brutas não são fornecidas diretamente aos modelos.
- Datas podem gerar ano, mês, semana, representação cíclica de
  sazonalidade, intervalos e flags de coerência.

Poderão ser derivados:

- `ano_internacao`;
- `mes_internacao`;
- `semana_sintomas`;
- `semana_sen`;
- `semana_cos`;
- `dias_sintomas_ate_internacao`;
- `flag_internacao_antes_sintomas`;
- `flag_intervalo_negativo_inesperado`.

---

## 8. Internação anterior aos primeiros sintomas

A variável `nosocomial` é carregada adicionalmente no notebook de
construção da coorte para interpretar registros em que `dt_interna` é
anterior a `dt_sin_pri`.

`nosocomial` é usada para auditoria da elegibilidade, não como
preditora, pois pode representar condição definida depois da
internação.

Serão derivados:

- `dias_sintomas_ate_internacao`;
- `flag_internacao_antes_sintomas`;
- `flag_intervalo_negativo_inesperado`.

Registros com intervalo negativo entre sintomas e internação não são
excluídos automaticamente antes da avaliação de `nosocomial`.

Antes de qualquer exclusão, são verificadas:

- quantidade absoluta de registros afetados;
- proporção da coorte;
- distribuição por ano;
- distribuição do desfecho;
- magnitude do intervalo negativo;
- presença ou ausência de indicação em `nosocomial`.

Somente registros com intervalo negativo, sem indicação de situação
nosocomial e sem outra explicação plausível podem ser excluídos da
coorte principal. Qualquer exclusão é registrada no waterfall.

---

## 9. Definição do desfecho principal

O alvo principal é construído exclusivamente com:

- `evolucao = 1`: cura, classe `0`;
- `evolucao = 2`: óbito por SRAG, classe `1`.

Ficam fora do alvo principal:

- `evolucao = 3`, óbito por outras causas;
- `evolucao = 9`;
- valores ausentes;
- códigos inválidos ou não previstos.

Óbito por outras causas não é combinado com óbito por SRAG, pois
representa desfecho diferente da pergunta principal.

Desfecho desconhecido, ausente, ignorado ou não encerrado nunca é
transformado em cura.

Uma análise alternativa com `evolucao = 3` pode ser explorada somente se
houver tempo depois da conclusão do modelo principal. A extensão não faz
parte do caminho crítico até o Fine Tuning.

---

## 10. Auditoria do desfecho

- `evolucao` é utilizada somente para construir o alvo.
- `evolucao` não é preditora.
- `dt_evoluca` é preservada para auditoria da data da alta ou do óbito.
- `dt_encerra` é preservada para auditoria do encerramento.
- `dt_digita` é preservada para auditoria administrativa e qualidade
  dos registros.
- Informações de evolução, encerramento ou digitação não entram nas
  matrizes de features.
- O padrão de ausência dessas variáveis também não é usado como
  preditor.

---

## 11. Estratégia geral de variáveis

As variáveis são organizadas em camadas.

### Modelo A: núcleo clínico de admissão

Informações clínicas, demográficas e derivadas mais diretamente
associadas ao ponto de previsão.

### Modelo B: ampliado epidemiológico, social e geográfico

Acrescenta contexto social, epidemiológico e territorial ao núcleo
clínico.

### Modelo C: sensibilidade

Pode incorporar variáveis condicionais com temporalidade e
aplicabilidade validadas. Tratamentos só são avaliados nessa camada
depois da conclusão do modelo principal e se a temporalidade estiver
comprovada.

### Modelo D: exploração

Pode incluir campos de texto, variáveis muito esparsas, códigos
territoriais de alta cardinalidade e extensões que não passem pelo
processo completo de Fine Tuning.

A seleção final não é determinada apenas pelo percentual global de
ausência. Também entram:

- disponibilidade no ponto de previsão;
- população em que o campo é aplicável;
- risco de vazamento;
- cardinalidade;
- estabilidade entre anos;
- qualidade e plausibilidade dos valores;
- contribuição incremental nos experimentos.

Ausência, categoria ignorada, "não se aplica" e resposta negativa
permanecem semanticamente distintas.

---

## 12. Variáveis clínicas

- Sintomas e comorbidades estruturados são inicialmente preservados no
  modelo clínico.
- `nu_idade_n` e `tp_idade` são combinadas para produzir `idade_anos`.
- Poderão ser derivados: `n_sintomas`, `n_comorbidades`,
  `flag_multimorbidade`, `flag_outro_sintoma` e
  `flag_outro_fator_risco`.
- Vazio não é interpretado automaticamente como resposta negativa.
- Códigos ignorados e ausências continuam distinguíveis.
- `tabag` fica documentada mas fora dos modelos enquanto estiver
  completamente vazia.
- `obes_imc` é preservada para EDA e auditoria, mas não entra
  inicialmente nos modelos.

---

## 13. Saturação e desconforto respiratório

Papéis nos experimentos iniciais:

- `saturacao` (saturação abaixo de 95%): Modelo A;
- `desc_resp` (desconforto respiratório): Modelo B.

A saturação é tratada como medida clínica objetiva potencialmente
disponível na avaliação inicial. O desconforto respiratório é avaliado
no modelo ampliado por depender de registro mais subjetivo e por ainda
existir incerteza sobre o momento exato da documentação.

Será executada comparação entre:

1. Modelo A com `saturacao`;
2. Modelo A sem `saturacao`;
3. Modelo B acrescido de `desc_resp`.

Se houver evidência de que alguma dessas informações representa o pior
estado durante a internação, em vez da condição na admissão, a variável
é removida do modelo correspondente e mantida apenas em análise de
sensibilidade ou EDA.

---

## 14. Variáveis sociais

- Escolaridade é avaliada no Modelo B, não no núcleo clínico.
- `pov_ct` pode entrar como indicador binário no Modelo B.
- `tp_pov_ct` fica inicialmente em EDA e análises de subgrupo.
- `cs_etinia` é avaliada no denominador aplicável, correspondente aos
  registros indígenas.
- A categoria detalhada de etnia fica inicialmente em EDA e subgrupo,
  por alta cardinalidade e baixo volume global.
- Ocupação é preservada para EDA.
- `pac_cocbo` não entra como código bruto nos primeiros pilotos.
- `pac_dscbo` apoia a interpretação e o eventual agrupamento das
  ocupações.
- Um agrupamento por grandes grupos da CBO pode ser avaliado como
  extensão, sem bloquear os primeiros modelos.

---

## 15. Variáveis geográficas

A primeira versão do Modelo B utiliza `sg_uf` (UF de residência). A UF
de residência foi escolhida por oferecer contexto territorial com
cardinalidade controlável e implementação mais rápida.

Na primeira versão:

- `sg_uf_not` é usada principalmente em EDA;
- `sg_uf_inte` deriva indicadores de deslocamento;
- regionais de saúde ficam em EDA;
- códigos municipais não entram diretamente nos primeiros modelos.

Pode ser derivada `uf_residencia_igual_internacao`.

`co_mun_res` (município de residência) é preservado na coorte auditável
e analisado em EDA. Depois do modelo principal, avalia-se se a
granularidade municipal acrescenta valor suficiente para justificar
maior cardinalidade, maior custo de processamento, categorias raras,
risco de sobreajuste a padrões locais e maior dificuldade de
interpretação.

A comparação futura avalia:

1. modelo sem geografia;
2. modelo com UF de residência;
3. modelo com município de residência agrupado ou codificado de forma
   controlada.

O município de residência não faz parte do caminho crítico até
17/10/2026, mas permanece como extensão prioritária.

`co_pais` pode virar um indicador de residência no Brasil, depois da
confirmação do código correspondente no dicionário.

---

## 16. Campos de texto livre

Os campos de texto livre são preservados para EDA. Nesta fase:

- `outro_des`, `morb_desc` e `out_anim` ficam em EDA;
- `pac_dscbo` apoia a interpretação das ocupações;
- os textos não entram brutos nos primeiros modelos.

Uma categorização simples pode ser criada somente se a EDA demonstrar
ganho claro e se os termos frequentes representarem informações ainda
não capturadas pelas variáveis estruturadas.

Não é implementado pipeline completo de NLP antes do Fine Tuning. A
ausência de NLP não implica descarte: os campos permanecem preservados
na coorte auditável para análise futura.

---

## 17. Vacinação

- `vacina` e `vacina_cov` permanecem entre as candidatas clínicas.
- Datas brutas de vacinação não entram diretamente nos modelos.
- Somente doses anteriores ou iguais a `dt_interna` contribuem para
  atributos preditores.
- Datas posteriores à internação são sinalizadas e desconsideradas na
  criação das features de admissão.

Poderão ser derivados:

- quantidade de doses antes da admissão;
- presença de reforço;
- data da última dose anterior à admissão;
- dias desde a última dose;
- vacinação contra influenza anterior à admissão;
- flag de dose posterior à admissão.

A mudança de preenchimento entre anos é registrada como limitação.
Campos maternos e pediátricos são avaliados somente no denominador em
que são aplicáveis e não entram nos primeiros modelos gerais.

---

## 18. IMC

- `obes_imc` é preservada para EDA e auditoria.
- `obes_imc` não entra inicialmente nos modelos.
- A coluna tem baixo preenchimento mesmo entre registros com obesidade.
- Os valores numéricos são convertidos e avaliados quanto à
  plausibilidade.
- A utilização futura depende da qualidade observada depois da
  conversão numérica e da validação de faixa.

---

## 19. Tratamentos e decisões assistenciais

As variáveis de tratamento ficam apenas em EDA e auditoria até que o
modelo principal esteja concluído. Aplica-se a:

- `antiviral`, `tp_antivir`, `dt_antivir`, `out_antiv`;
- `trat_cov`, `tipo_trat`, `dt_trt_cov`, `out_trat`.

Essas variáveis não entram no Modelo A nem no Modelo B.

Depois do modelo principal, um Modelo C de sensibilidade pode avaliar
tratamentos somente se:

- houver tempo disponível;
- a data de início estiver válida;
- o tratamento tiver sido iniciado até `dt_interna`;
- a temporalidade puder ser demonstrada;
- a cobertura for suficiente para uma análise interpretável.

Tratamentos iniciados depois da internação permanecem excluídos das
features. `out_antiv` e `out_trat` não entram nos modelos e ficam apenas
em auditoria ou exploração.

A criação do Modelo C não faz parte do caminho crítico até 17/10/2026.

---

## 20. Estratégia de dados ausentes

- Nenhuma variável é excluída apenas pelo percentual global de ausência.
- Campos condicionais são avaliados na população em que deveriam estar
  habilitados.
- Vazio não é convertido automaticamente em "não".
- Resposta ignorada permanece distinta de vazio.
- "Não se aplica" permanece distinto de resposta negativa.
- Campos inexistentes em determinados períodos são documentados
  separadamente.
- A estratégia de imputação é definida e ajustada dentro dos pipelines
  de modelagem.
- Imputação, encoding, escala e balanceamento usam somente os dados de
  treino.
- Nenhum processamento é ajustado com validação ou teste.

---

## 21. Separação dos dados

**Status:** decisão fechada em 18/10/2026.

A divisão 70/15/15 foi supersedida. A partição-mestre determinística por
`group_id` tem seis blocos:

| Bloco | Anos | Fração | Finalidade | Influencia decisões? |
|---|---|---|---|---|
| `train_ref` | 2019, 2023, 2024, 2025 | 0.70 | treino | Sim |
| `val_tune` | 2019, 2023, 2024, 2025 | 0.05 | features, geografia e tuning | Sim |
| `val_cal` | 2019, 2023, 2024, 2025 | 0.05 | calibração e limiar | Sim |
| `val_meas` | 2019, 2023, 2024, 2025 | 0.05 | confirmação pré-teste | Somente confirmação |
| `test_ref` | 2019, 2023, 2024, 2025 | 0.15 | Teste A | Não |
| `test_pandemic` | 2020, 2021, 2022 | n/a (100% dos anos pandêmicos) | parcela adicional do Teste B | Não |

Invariantes:

- nenhum `group_id` cruza blocos;
- 2020–2022 aparecem somente em `test_pandemic`;
- 2026 fica fora dos seis blocos, em `exploracao`;
- mesma entrada, seed e configuração reproduzem o mapa;
- ambos os testes ficam fechados até G9;
- Teste B é união lógica sem duplicação física;
- método `hash_grupo_estratificado_mestre_v1`, sal determinístico a
  partir da seed;
- `min_grupos_por_estrato: 5`, para garantir ≥1 grupo por bloco
  compartilhado em cada estrato;
- estratificação por ano × alvo × região, com fallback explícito para
  ano × alvo quando o estrato geográfico ficar abaixo do mínimo. O
  fallback é registrado no campo `estratificacao` do manifesto.

A materialização fica em `src/data/split.py::criar_particao_mestra`. A
função lê `temporal.blocos`, atribui 2020–2022 inteiramente a
`test_pandemic`, distribui os demais anos por hash entre os cinco blocos
compartilhados, marca o restante (2026) como `exploracao` e devolve um
manifesto com contagem, nº de grupos, anos, prevalência do alvo e hash
por bloco.

A coluna de partição é gravada no artefato. Nenhum notebook posterior
cria nova divisão. Resultados de teste não orientam features, algoritmo,
hiperparâmetros, imputação, encoding, balanceamento, calibração, limiar,
período ou coorte.

## 22. Preservação dos conjuntos de teste

`test_ref` e `test_pandemic` permanecem isolados durante EDA orientada
ao desfecho, escolha de features, comparação de algoritmos, Fine
Tuning, calibração, escolha de limiar, construção de categorias de
texto, decisões geográficas e seleção de representação, incluindo UMAP.

A abertura ocorre uma única vez, depois do fechamento de coorte,
features, modelo, hiperparâmetros, calibrador, limiar, commit, ambiente,
manifestos e hashes, com G1, G7, G8 e G9 aprovados.

Sem novo ajuste, a execução produz:

1. Teste A em `test_ref`;
2. Teste B na união de `test_ref` e `test_pandemic`;
3. relatório isolado de 2020–2022.

Para cada saída são registrados: população, prevalência, PR-AUC,
PR-AUC/prevalência, ROC-AUC, Brier, calibração, métricas por ano, região
e UF, intervalos de confiança por bootstrap de grupo, hash, commit e
timestamp.

Depois da abertura, G9 passa a `executado`, o manifesto registra
`test_opened: true` e nenhuma decisão de modelagem pode mudar em
resposta aos resultados.

## 23. Critério de escolha do limiar

**Status:** decisão pendente.

O critério definitivo para transformar probabilidades em classes é
definido somente depois que os modelos finalistas forem avaliados na
validação.

Até essa decisão:

- os modelos são comparados prioritariamente por métricas baseadas em
  probabilidade;
- nenhum limiar é escolhido usando o conjunto de teste;
- o conjunto de teste permanece intocado;
- o limiar é registrado antes da avaliação final.

Alternativas possíveis:

- maximização de F1;
- sensibilidade mínima;
- especificidade mínima;
- Youden J;
- regra orientada ao objetivo acadêmico.

Independentemente do critério escolhido, devem ser apresentados:
sensibilidade, especificidade, precisão, F1, matriz de confusão e
distribuição das probabilidades.

---

## 24. Clustering

- O clustering usa somente registros do conjunto de desenvolvimento.
- Alvo, evolução, datas de desfecho, identificadores e informações
  posteriores à admissão são excluídos da matriz de clustering.
- K-Means é a referência inicial.
- HCA e DBSCAN podem ser avaliados em amostras.
- PCA é usado para visualização.
- O desfecho só é associado aos clusters depois da formação dos grupos.
- As decisões sobre número de clusters e parametrização não usam o
  conjunto de teste.
- Textos livres e códigos geográficos de alta cardinalidade não entram
  na primeira matriz de clustering.

---

## 25. Documentação e rastreabilidade

- O manifesto do dataset fica separado deste arquivo, em
  `data/manifest_dados-v2.yaml`.
- O dicionário operacional oficial fica em
  `configs/dicionario_variaveis_v1.csv`. Esse é o único arquivo
  editável e a fonte oficial das decisões específicas de cada variável.
- Visões reduzidas para revisão podem ser geradas em
  `outputs/tables`, mas não são uma segunda fonte de decisões.
- Nenhuma decisão é atualizada manualmente em mais de um arquivo.
- Cada variável deve ter: nome amigável, grupo, uso recomendado,
  aplicabilidade, transformação sugerida, risco temporal, decisão final
  e justificativa.
- O Notebook 01 permanece como primeira passagem descritiva.
- A construção da coorte, do alvo, das features e das partições fica em
  notebook específico.
- O fluxo da coorte é registrado em `coorte_waterfall.csv`.
- Os experimentos são registrados em tabela própria.
- Configurações executáveis são mantidas em arquivos de configuração
  quando isso reduz duplicação e facilita reprodução.
- Nenhum notebook incorpora caminhos locais absolutos.
- Decisões futuras são acrescentadas sem apagar o histórico relevante.

---

## 26. Princípios inegociáveis

Independentemente das simplificações para cumprir prazo:

1. nenhuma informação posterior à admissão entra no modelo principal;
2. transformações aprendidas com os dados são ajustadas somente no
   treino;
3. o conjunto de teste permanece isolado até a avaliação final;
4. vazio, ignorado, "não se aplica" e resposta negativa não são
   tratados como equivalentes;
5. nenhuma correção de dados é realizada silenciosamente;
6. exclusões da coorte são registradas no waterfall;
7. o alvo não é utilizado, direta ou indiretamente, na formação dos
   clusters;
8. a documentação permite que outro integrante compreenda as decisões,
   reproduza a execução e explique as limitações do estudo.

---

## 27. Extensões fora do caminho crítico

Permanecem registradas, sem bloquear o fluxo principal:

- exploração de 2026, somente depois dos Testes A/B e sem reajuste;
- análise com `evolucao = 3`;
- município de residência;
- ocupações detalhadas;
- categorização de textos e NLP;
- tratamentos anteriores à admissão;
- IMC;
- novas famílias de modelos após congelamento;
- alta granularidade territorial;
- UMAP supervisionado;
- UF como feature, condicionada ao resultado com região.

Não são extensões e não podem ser cortados:

- partição-mestre disjunta por grupo;
- bloqueio técnico dos testes até G9;
- calibração e limiar congelados;
- Teste A, Teste B e resultado exclusivo de 2020–2022;
- importância das variáveis na validação;
- documentação de limitações e rastreabilidade.

Nenhuma extensão retroage para otimizar o resultado oficial de teste.

## 28. Decisão temporal — treino de referência e duas janelas de teste

**Data:** 18/10/2026
**Status:** aprovada e congelada
**Origem:** decisão metodológica aprovada pelo time
**Responsável pelo registro:** Pessoa B
**Natureza:** contrato metodológico do experimento principal

### 28.1 Decisão

Um único modelo é desenvolvido sem 2020–2022. Treino e desenvolvimento
usam exclusivamente 2019, 2023, 2024 e 2025, distribuídos em
`train_ref`, `val_tune`, `val_cal` e `val_meas`, com separação
determinística por grupo.

- **Teste A (`test_ref`)**: 2019, 2023, 2024 e 2025, em grupos nunca
  usados no desenvolvimento (detalhes em §5.2). É o resultado
  principal.
- **Teste B**: união lógica de `test_ref` com `test_pandemic`, este
  último com somente 2020–2022 (detalhes em §5.3). É a avaliação
  ampliada de robustez temporal.
- **2026**: exploração opcional posterior, fora dos blocos principais e
  sem reajuste (detalhes em §5.4).

### 28.2 Regras invariantes

- nenhum `group_id` em mais de um bloco;
- 2020–2022 apenas em `test_pandemic`;
- 2026 fora dos blocos principais;
- testes fechados até G9;
- mesmo pipeline, features, modelo, hiperparâmetros, calibrador e
  limiar nas duas janelas;
- nenhuma métrica de teste orienta desenvolvimento;
- Teste B acompanhado do resultado isolado de 2020–2022 e de métricas
  anuais;
- comparação A × B interpretada como robustez temporal, nunca como
  efeito causal da pandemia.

### 28.3 Saídas mínimas

Registrar, por janela, população, prevalência, PR-AUC,
PR-AUC/prevalência, ROC-AUC, Brier, calibração e resultados por ano,
região e UF. Registrar hashes, commit e timestamp.

### 28.4 Critério de aceite

A decisão estará implementada quando:

- [x] este registro estiver versionado;
- [x] o `supervised.yaml` declarar os seis blocos e seus anos;
- [x] nenhuma configuração ativa permitir 2020–2022 ou 2026 em
      desenvolvimento;
- [ ] testes automatizados bloquearem anos proibidos e sobreposição de
      grupos;
- [x] o manifesto implementado em `criar_particao_mestra` registrar
      anos, contagens, prevalência, grupos e hash por bloco;
- [ ] documentação, configuração e implementação estiverem sem
      conflito.

Os dois itens em aberto (testes automatizados e verificação final de
consistência) são o que resta para transformar a decisão em código
verificado e reproduzível. A implementação
(`src/data/split.py::criar_particao_mestra`) já existe; falta cobri-la
com testes e rodar o fluxo ponta a ponta no Notebook 03.

### 28.5 Relação com a implementação

Este documento registra o contrato metodológico. Os arquivos de
configuração refletem os mesmos blocos e restrições temporais; a
partição-mestre materializa o contrato com grupos disjuntos e testes
automatizados; e a execução final aplica o modelo congelado, sem
ajustes, nas duas janelas de teste. A aprovação documental não substitui
os critérios técnicos de aceite da configuração, da partição, dos
manifestos e da execução.