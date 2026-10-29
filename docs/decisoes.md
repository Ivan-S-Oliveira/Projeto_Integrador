# Registro de Decisões Metodológicas

Este arquivo registra as decisões que afetam a coorte, a preparação dos
dados, os experimentos e a interpretação dos resultados do Projeto
Integrador SRAG.

Decisões específicas de cada variável ficam em
`configs/dicionario_variaveis_v1.csv`. Visões reduzidas podem ser geradas
em `outputs/tables/`, mas não constituem uma segunda fonte editável.

Este documento registra somente decisões gerais ou com impacto em várias
etapas do projeto.

Última atualização: 27/10/2026 (entradas de 22–24/10 redigidas em 27/10; ver §29).

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
- Coorte definitiva `final_cohort_v1`: sete regras de exclusão (D_COORTE_001 a 007), 3.884.728 de 4.666.910 linhas (§29.1). Publicada em 23/10 (§29.3).
- G1 aprovado em 22/10: 31 features principais; `saturacao` e `desc_resp` só em sensibilidade; `vacina`, `vacina_cov`, `cs_escol_n` e `sg_uf` só como contexto incremental (§29.2); em 27/10 `vacina_cov` foi trocada por `vacina_cov_previa`.
- `nu_notific` repetido: quarentena entre estratos com flag (§29.10).
- Lista curta provisória de modelos: `hist_gradient_boosting` e `logistic`; `decision_tree` e `random_forest` encerradas (§29.11).

### 1.2 Decisões pendentes

- Resultado dos sintomas de 2019 (#50).
- Peso de classe (#5): `class_weight: balanced` está vigente nos quatro modelos e depende da confirmação do #5 (§29.12).
- Escolha do finalista e dos hiperparâmetros no G6.
- Escolha final do método de calibração no G7, após o ajuste fino.
- Escolha final do critério e valor do limiar no G8, usando somente validação.
- Aprovação conjunta do G9 depois do congelamento de features, modelo, hiperparâmetros, calibrador, limiar, commit e manifestos.
- Confirmar a decisão de desativar a sensibilidade `alvo_qualquer_obito` (evolução 2 e 3), feita em 27/10 porque a coorte definitiva exclui o código 3 (§29.13).

Substituído em 27/10: a versão de 21/10 listava também "regra definitiva para identificadores repetidos" (fechada, §29.10) e "aprovação do G1" (aprovado em 22/10, §29.2).

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

Atualizado em 22/10: os critérios definitivos da coorte são as regras
D_COORTE_001 a 007 do contrato `final_cohort_v1`, descritas em §29.1.
Elas acrescentam as exclusões por período, por intervalo entre sintomas e
internação e por hospital diferente de 1. A lista acima descreve a coorte
auditável anterior e não é mais o contrato vigente.

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

Atualizado em 27/10 (#85): 2026 é período **parcial e exclusivamente
exploratório**. Os dados vão só até setembro de 2026, cerca de 12% dos
desfechos ainda estão em aberto e os meses mais recentes (agosto em
diante) podem estar subnotificados por atraso de notificação. Por isso
2026 não participa de nenhuma decisão nem dos Testes A e B. As 173.945
fichas de 2026 ficam no bloco `exploracao`. Qualquer tabela ou figura com
eixo de anos que mostre 2026 deve marcá-lo como "parcial". A mortalidade
de 2026 (5,6%, contra 7,3% em 2025, valores da ficha não verificados na
base) não é comparável à dos anos completos.

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
- Atualizado em 27/10: a regra definitiva para identificadores repetidos
  está em §29.10 (quarentena entre estratos e flag). Não se escolhe a
  primeira ocorrência, o que continua valendo.

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
- `semana_sintomas` (não consta em `engenharia.derivadas` do `supervised.yaml`; confirmar se continua prevista);
- `semana_sen` (substituído em 27/10 por `sin_semana`);
- `semana_cos` (substituído em 27/10 por `cos_semana`);
- `dias_sintomas_ate_internacao`;
- `flag_internacao_antes_sintomas`;
- `flag_intervalo_negativo_inesperado` (substituído em 27/10 por `flag_intervalo_invalido`, que cobre intervalo negativo e intervalo acima de 60 dias).

Atualizado em 27/10: `sin_semana` e `cos_semana` (sazonalidade derivada de
`dt_sin_pri`) existem somente para a ablação de sazonalidade (#13). Não
fazem parte das 31 features principais (`features.final`). Na coorte
definitiva, `flag_intervalo_invalido` e `flag_internacao_antes_sintomas`
devem ficar sem variação (sempre 0), porque as regras D_COORTE_006 e 007
excluem esses registros (§29.1); confirmar no manifesto.

Decisão de 18/10 (#13): a sazonalidade não entra no modelo principal (mais
dimensões, ganho incerto) e é documentada como limitação. `sin_semana` e
`cos_semana` transformam a semana do ano num círculo (a semana 52 fica
vizinha da semana 1) e são criadas por `montar_features`, mas não constam em
`features.final`. Serão testadas na linha "P + sazonalidade" da tabela de
ablações (#54). Se a PR-AUC subir pelo menos 0,005, vira achado da Discussão:
a sazonalidade carrega informação de onda epidêmica; o modelo principal
continua o do G1.

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
- `flag_intervalo_negativo_inesperado` (substituído em 27/10 por `flag_intervalo_invalido`).

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

**Substituído em 22/10 pelas regras D_COORTE_006 e D_COORTE_007 (#82).**
Os parágrafos acima (verificar `nosocomial` antes de excluir; sinalizar
intervalos impossíveis em vez de excluir) não valem mais para a coorte
definitiva. O contrato `final_cohort_v1` exclui todo registro com
intervalo negativo (24.361 linhas que atendem à regra) e todo registro
com intervalo acima de 60 dias (11.708 linhas), sem consultar
`nosocomial`. Motivo: internação anterior ao início dos sintomas é
incompatível com a cronologia do episódio e com o ponto de previsão na
admissão; a cauda acima de 60 dias chega a 1.836 dias e a auditoria não
encontrou falha de conversão das datas ISO. As exclusões estão no
waterfall. O texto original fica como registro histórico.

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

Atualizado em 27/10: a coorte definitiva exclui `evolucao` 3 e 9 (regra
D_COORTE_003). Por isso a sensibilidade `alvo_qualquer_obito` foi
desativada (`ativa: false`) no `supervised.yaml` e no
`feature_contract_v1.json`. Para reativá-la, a coorte teria de preservar o
código 3, o que exige novo contrato de coorte (§29.13).

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

Atualizado em 27/10 (G1 e #9): as camadas abaixo foram alinhadas ao
`supervised.yaml`. O texto original de cada camada fica como histórico.

### Camada principal: núcleo clínico de admissão (antes chamada de "Modelo A")

As 31 features de `features.final`: informações clínicas, demográficas e
derivadas mais diretamente associadas ao ponto de previsão. Não inclui
`saturacao` nem `desc_resp` (ver §13).

Texto original: informações clínicas, demográficas e derivadas mais
diretamente associadas ao ponto de previsão.

### Contexto incremental (antes chamada de "Modelo B", ampliado epidemiológico, social e geográfico)

`cs_escol_n`, `sg_uf`, `vacina` e `vacina_cov_previa`
(`features.contexto_incremental`), fora do conjunto principal e avaliadas como
sensibilidade.

Texto original: acrescenta contexto social, epidemiológico e territorial ao
núcleo clínico.

### Sensibilidade de gravidade na admissão

`saturacao` e `desc_resp` (`features.sensibilidade_gravidade_admissao`), só
em análise de sensibilidade (§13).

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
- Atualizado em 27/10: no `supervised.yaml` os contadores agregados
  aparecem como `n_sintomas_confirmados`, `n_sintomas_avaliados`,
  `n_comorbidades_confirmadas` e `n_comorbidades_avaliadas`, em
  `sensibilidade_contadores_clinicos` com `ativa: false` (podem duplicar
  o peso das variáveis individuais). Não estão nas 31 features principais.
- `tabag` fica documentada mas fora dos modelos enquanto estiver
  completamente vazia.
- `obes_imc` é preservada para EDA e auditoria, mas não entra
  inicialmente nos modelos.

---

## 13. Saturação e desconforto respiratório

Saturação abaixo de 95% (`saturacao`) e desconforto respiratório
(`desc_resp`) são sinais fortes de gravidade, mas a ficha não registra
quando foram anotados: podem ser da admissão ou do pior momento da
internação. Por isso ficam fora do modelo principal e entram numa versão
de sensibilidade (#54), com o ganho reportado.

- **Decisão:** G1, 22/10; confirma a decisão de 18/10 (uma rodada de
  sensibilidade com as duas variáveis no cenário vencedor).
- **Papel:** `sensibilidade_gravidade_admissao` no `supervised.yaml`
  (sensibilidade `sem_saturacao_desc_resp`). Nenhuma das duas está nas 31
  features principais, nem no Modelo A nem no Modelo B.
- **Condição para entrar em configuração congelada:** só se a auditoria
  confirmar disponibilidade consistente no momento da admissão
  (`regra_temporal_experimento` do dicionário).
- **Por que importa (dados da ficha, não verificados na base):** óbito em
  26,7% com saturação abaixo de 95%, contra 12,2% com saturação normal; e
  24,3% com desconforto, contra 16,1% sem. Se as variáveis forem
  posteriores à admissão, usá-las seria vazamento.

**Texto anterior (substituído em 22/10 e reescrito em 27/10), mantido como
histórico:**

> Papéis nos experimentos iniciais:
>
> - `saturacao` (saturação abaixo de 95%): Modelo A;
> - `desc_resp` (desconforto respiratório): Modelo B.
>
> **Substituído em 22/10 (G1, #9).** `saturacao` e `desc_resp` saem do
> Modelo A e do Modelo B e ficam somente na análise de sensibilidade de
> gravidade na admissão (`sensibilidade_gravidade_admissao`; sensibilidade
> `sem_saturacao_desc_resp`). Motivo: não se sabe se foram medidas na
> admissão. O texto abaixo é o desenho anterior e fica como histórico.
>
> A saturação é tratada como medida clínica objetiva potencialmente
> disponível na avaliação inicial. O desconforto respiratório é avaliado
> no modelo ampliado por depender de registro mais subjetivo e por ainda
> existir incerteza sobre o momento exato da documentação.
>
> Será executada comparação entre:
>
> 1. Modelo A com `saturacao`;
> 2. Modelo A sem `saturacao`;
> 3. Modelo B acrescido de `desc_resp`.
>
> Se houver evidência de que alguma dessas informações representa o pior
> estado durante a internação, em vez da condição na admissão, a variável
> é removida do modelo correspondente e mantida apenas em análise de
> sensibilidade ou EDA.
>
> ---

## 14. Variáveis sociais

- Escolaridade é avaliada no Modelo B, não no núcleo clínico
  (atualizado em 27/10: `cs_escol_n` é contexto incremental pelo G1).
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

A primeira versão do Modelo B utiliza `sg_uf` (UF de residência)
(atualizado em 27/10: pelo G1, `sg_uf` é contexto incremental, fora das 31
features principais). A UF
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

- `vacina` e `vacina_cov` permanecem entre as candidatas clínicas
  (substituído em 27/10: são contexto incremental, ver o parágrafo
  "Atualizado em 27/10" abaixo).
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

Atualizado em 27/10 (#84 e G1): `vacina` e `vacina_cov_previa` (que
substitui `vacina_cov` bruta) são **contexto
incremental**, fora das 31 features principais. A regra de doses é:

1. campos de dose: `DOSE_1_COV`, `DOSE_2_COV`, `DOSE_REF`, `DOSE_2REF`,
   `DOSE_ADIC` e `DOS_RE_BI`;
2. dose válida: data a partir de 17/01/2021 e pelo menos 1 dia antes de
   `dt_interna`;
3. dose sem data não conta (`declarada_sem_data`);
4. dose depois da internação, ou internação antes de 2021, não conta
   (`declarada_data_invalida`);
5. "sim" em registros de 2019–2020 é `declarada_data_invalida`.

Substituído em 27/10: o critério "doses anteriores ou iguais a
`dt_interna`" (acima) passa a ser "pelo menos 1 dia antes". A feature
derivada é `vacina_cov_previa`, que passou a constar no `supervised.yaml`
e no `feature_contract_v1.json` (§29.2). Confirmado em 27/10: os campos
`DOSE_*` são datas (`dd/mm/aaaa`).

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
- Atualizado em 27/10: indicadores de ausência (`missingindicator_`)
  desativados no supervisionado; a ausência é a categoria `AUSENTE` e é
  analisada na completude (#52) (§29.6).
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

Atualizado em 27/10 (#118): as três validações são disjuntas e cada uma tem
um papel só, de modo que nenhuma fatia escolhe e mede ao mesmo tempo.
`val_tune` escolhe features, geografia e hiperparâmetros; `val_cal` ajusta
a calibração e escolhe o limiar; `val_meas` só mede o desempenho antes do
teste e não influencia nenhuma escolha. Isso substitui o desenho anterior,
em que a busca de hiperparâmetros (C_13) usava a validação inteira e o C_15
media o resultado numa metade dela, já vista pela busca, o que deixava a
estimativa otimista.

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

Atualizado em 27/10: `limiar.min_recall: 0.80` e as métricas candidatas
`youden_j` e `recall_minimo` foram incluídas no `supervised.yaml` (uso no
#80). São parâmetros e candidatos; a escolha do critério e do valor
continua no G8, só com a validação.

Proposta do G8 (card #80, 27/10), ainda não aprovada: corte principal igual
ao de maior precisão entre os que têm sensibilidade de pelo menos 0,80,
escolhido em `val_cal` sobre probabilidades calibradas. Cortes de referência,
só para mostrar: sensibilidade de pelo menos 0,70, F1 máximo e Youden. Os
cortes são medidos em `val_meas` sem serem alterados. Detalhes e pontos em
aberto em §29.22.

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


---

## 29. Decisões do ciclo de 22 a 24/10/2026

**Redigido em:** 27/10/2026
**Responsável pelo registro:** Pessoa A
**Regra de escrita:** cada entrada traz data, decisão, motivo, impacto, onde
está implementado e quem decidiu. Texto antigo não é apagado; as seções
substituídas levam a marca "substituído em DD/MM por …".
**Campos sem dado:** o que não consta nos arquivos (decisores, datas das
§29.10 a 29.12, números do #131, pontos do #95) não foi preenchido aqui e
deve ser consultado nas fichas.

### 29.1 22/10 · Contrato da coorte definitiva (`final_cohort_v1`)

- **Decisão:** a coorte definitiva é definida por sete regras de exclusão,
  D_COORTE_001 a 007, aplicadas na ordem do contrato.
- **Linhas que atendem a cada regra:**

| Regra | Critério | Linhas |
|---|---|---|
| D_COORTE_001 | hospital ≠ 1 | 232.253 |
| D_COORTE_002 | data de internação inválida | 304.245 |
| D_COORTE_003 | evolução fora de óbito/cura | 530.370 |
| D_COORTE_004 | antes de 2019 | 48 |
| D_COORTE_005 | depois de 2026 | 76 |
| D_COORTE_006 | intervalo sintomas→internação negativo | 24.361 |
| D_COORTE_007 | intervalo acima de 60 dias | 11.708 |

- **Resultado:** as regras se sobrepõem. A soma das contagens (1.103.061) é
  maior que o total excluído (782.182). A coorte fica com 3.884.728 de
  4.666.910 linhas (4.666.910 − 782.182 = 3.884.728).
- **Motivo:** hospital igual a 1 define a população; a data de internação é
  a âncora temporal obrigatória; o alvo principal aceita só cura e óbito
  por SRAG; o período auditável é 2019–2026; internação antes dos sintomas
  é incompatível com o ponto de previsão na admissão; intervalo acima de 60
  dias foge do episódio agudo (máximo de 1.836 dias, sem falha de
  conversão das datas ISO).
- **Impacto:** códigos 3 e 9 de `evolucao` saem da coorte e a sensibilidade de "qualquer óbito" foi desativada (§29.13);
  `flag_intervalo_invalido` e `flag_internacao_antes_sintomas` ficam sem
  variação; o limite de 60 dias vale em `audit.max_symptom_to_admission_days`.
- **Implementado em:** `configs/final_cohort_v1.yaml` (regras D_COORTE_001 a
  007); item #82.
- **Substitui:** §8 (sinalizar intervalos impossíveis) e a lista de
  critérios da §4.

### 29.2 22/10 · G1 aprovado

- **Decisão:** 31 features principais (`features.final`). `saturacao` e
  `desc_resp` só em sensibilidade. `vacina`, `vacina_cov`, `cs_escol_n` e
  `sg_uf` só como contexto incremental.
- **Motivo:** não se sabe se `saturacao` e `desc_resp` foram medidas na
  admissão; manter o modelo principal só com informação disponível na
  admissão.
- **Alterado em 27/10:** `vacina_cov` bruta foi trocada por `vacina_cov_previa`
  (regra do #84, §17) na lista de contexto do `supervised.yaml` e no
  `feature_contract_v1.json`. A coluna precisa existir na coorte (item #45).
- **Impacto:** lista congelada em `feature_contract_v1.json`
  (`congelado_para_validacao_g1`, teste não consultado). Só reabre por
  falha material, vazamento ou indisponibilidade na admissão.
- **Implementado em:** `configs/supervised.yaml` (`features.final`, gate
  `G1_definicao_alvo_features`); item #9.
- **Decidiu:** time do projeto (registro do gate em 22/10/2026).

### 29.3 23/10 · Coorte publicada

- **Decisão:** publicar `coorte_final.parquet` depois da checagem de
  paridade com o protocolo legado e da comparação com a coorte provisória.
- **Resultado:** a definitiva tem 30.408 linhas a menos que a provisória e
  nenhuma divergência de alvo nas linhas em comum.
- **Impacto:** arquivo em `data/analytical/coorte_final.parquet`. O
  contrato ainda consta como `status: candidate` e precisa ser atualizado
  (§29.13).

### 29.4 24/10 · Regra de grupo (#10) e partição em seis blocos

- **Regra de grupo (#10):** `group_id` é o `nu_notific` sem espaços; quando o
  número está vazio, usa-se "sem_notific:" mais o `id_registro`. Fichas com o
  mesmo `nu_notific` ficam sempre no mesmo bloco. Grupos que aparecem em mais
  de um estrato (ano × desfecho) vão para quarentena: 2 grupos, 4 linhas.
  Função `criar_group_id` em `src/data/split.py` (entra pelo #142); o
  artefato atual ainda chama a coluna de `grupo_split`.
- **Decisão:** partição-mestre por hash de `group_id`, método
  `hash_grupo_estratificado_mestre_v1`, seed 42, em seis blocos
  (`train_ref` 0,70; `val_tune`, `val_cal` e `val_meas` 0,05 cada;
  `test_ref` 0,15; `test_pandemic` com 2020–2022).
- **Motivo (resposta se a banca perguntar "por que hash?"):** o hash é
  determinístico e reproduzível com a mesma entrada, seed e configuração;
  não permite novo sorteio; mantém grupos disjuntos, de modo que nenhum
  `group_id` aparece em mais de um bloco; a partição é gravada na coorte.
- **Impacto:** estratificação por ano × alvo × região, com mínimo de 5
  grupos por estrato; abaixo disso, a geografia é reduzida e o fallback é
  registrado no manifesto. Números: ficha #131.
- **Implementado em:** `src/data/split.py::criar_particao_mestra`; seção
  `temporal` do `supervised.yaml`; §21 e §28 deste documento.
- **Decidiu:** time do projeto (G2, aprovado em 18/10/2026).

### 29.5 24/10 · Orientação

- Pontos: ficha #95.

### 29.6 24/10 · Indicadores de ausência desativados no supervisionado

- **Decisão:** os indicadores de ausência (`missingindicator_`) estão
  desativados no supervisionado (#83), inclusive como sensibilidade. A
  pergunta sobre ausência passa a ser respondida pela análise de
  completude (#52).
- **Motivo:** `AUSENTE` já é uma categoria no pré-processador, então o
  modelo principal já recebe a informação de ausência e a comparação "com
  × sem indicadores" não tinha contraste real; nenhum código criava essas
  colunas. Vazio, ignorado e não aplicável não são "não".
- **Impacto:** `features.sensibilidade_indicadores_ausencia.ativa`,
  `missingness.indicadores_ausencia.sensibilidade` e
  `sensibilidades.com_sem_indicadores_ausencia.ativa` ficam `false`;
  `pipeline_principal` já era `false`. Nenhum código novo.
- **Implementado em:** `supervised.yaml` (alterado em 27/10); #83 e #52.
  O item de código "a sensibilidade não existe" fica concluído com as
  três chaves em `false`.
- **Substitui:** a proposta de 18/10 (comparar o conjunto completo com o
  subconjunto de comorbidades preenchidas).

### 29.7 24/10 · Não supervisionado

- **Decisão:** one-hot dos quatro estados (#136) e perfil dos grupos por
  qui-quadrado/ANOVA (#137).
- **Detalhes:** fichas #136 e #137.

### 29.8 24/10 · Geografia como separação da análise (#110)

- **Decisão (#110):** estado atual nos
  arquivos: a região de residência estratifica a partição; `sg_uf` fica
  como contexto incremental; a comparação sem geografia × região é
  obrigatória e UF como preditora é condicional (§1.1).

### 29.9 27–28/10 · Pendente (a Pessoa C escreve uma linha no card; a Pessoa A transcreve)

- Sintomas de 2019 (#50): aguardando a Pessoa C
- Peso de classe (#5): aguardando a Pessoa C
- Finalista e hiperparâmetros (G6): aguardando a Pessoa C
- Calibração (G7): aguardando a Pessoa C
- Limiar (G8): aguardando a Pessoa C
- Concluir até 29/10, antes do G9.

### 29.10 · Quarentena para `nu_notific` repetido (#10)

- **Decisão:** política `quarentena_entre_estratos_e_flag`: números
  presentes em mais de um estrato (ano × desfecho) saem da base; os demais
  repetidos ficam com `flag_nu_notific_repetido`. Dois grupos entraram em
  quarentena.
- **Dados da ficha (não verificados na base):** 58 linhas e 29 números
  repetidos; 4 linhas (2 grupos) em quarentena; 9 a 10 números em
  partições diferentes no A_09.
- **Alternativa não adotada:** `excluir_todos_repetidos` (≈ 58 linhas),
  que a ficha recomendava.
- **Limitação registrada na ficha de 18/10 (substituída em 27/10):** repetidos
  dentro do mesmo estrato poderiam cair em partições diferentes. A regra de
  grupo por `nu_notific` (§29.4, `criar_group_id`) mantém todas as fichas com
  o mesmo número no mesmo bloco, o que elimina essa limitação.
- **Implementado em:** `configs/decisoes.yaml` (`nu_notific.politica`).

### 29.11 · Lista curta e famílias encerradas

- **Decisão:** finalistas `hist_gradient_boosting` e `logistic`
  (execuções `hist_gradient_boosting_v2` e `logistica_C1_v2`);
  `decision_tree` e `random_forest` encerradas. Critério: PR-AUC.
- **Status:** `shortlist_provisoria`, teste não consultado, sujeita a
  repetição na coorte definitiva; escolha final só com blocos de
  desenvolvimento.
- **Implementado em:** `supervised.yaml` (`selecao_modelos`); G5
  aprovado em 11/10. O `finalista_escolhido` fica em aberto até o G6.

### 29.12 27/10 · Peso de classe (#5)

- **Decisão vigente:** `class_weight: balanced` na regressão logística e no
  boosting (as famílias encerradas, árvore e random forest, também trazem a
  chave, mas estão com `ativa: false`). A decisão final depende de evidência,
  regra abaixo, e é da Pessoa C no ajuste fino.
- **Por que está em discussão:** `balanced` dá a cada óbito um peso de
  aproximadamente (1 − p) / p vezes o de uma cura, cerca de 11 vezes com
  prevalência de 8,4% na coorte definitiva. Isso não muda a ordenação
  (ROC-AUC e PR-AUC), mas infla as probabilidades e prejudica Brier,
  calibração e qualquer limiar. No piloto definitivo, a logística previa em
  média cerca de 34% de risco quando morriam 8,4%, e o Brier (0,165) ficou pior
  que o de um modelo que dá 8,4% para todos (0,077).
- **Números da coorte provisória (não valem para a definitiva):** previsto
  42,4% (boosting) e 43,0% (logística) contra 21,9% reais; a calibração do
  C_15 levou o Brier do boosting de 0,1959 para 0,1409 (ECE 0,0018). Ainda
  não foi testado treinar sem peso.
- **Regra proposta (card #5):** treinar duas versões do modelo vencedor
  (`class_weight=None` e `balanced`), calibrar as duas com o mesmo método do
  G7 e manter `balanced` só se a PR-AUC subir pelo menos 0,005 e o Brier
  calibrado não piorar. Caso contrário, `None`. A escolha é gravada no YAML
  das famílias ativas.
- **Conflito a resolver antes de rodar:** o passo a passo manda calibrar em
  `val_cal` e medir em `val_meas`, e usar essa medida para decidir. Mas
  `val_meas` não pode influenciar nenhuma decisão (§21, `influencia_decisoes:
  false`), e a decisão de 18/10 dizia para decidir pela calibração em
  `val_cal`. Opções: decidir em `val_tune` (PR-AUC) e em `val_cal` com
  calibração em metades de grupos (Brier), e usar `val_meas` só para
  confirmar e relatar.
- **Observação:** como a calibração não altera a ordenação, a PR-AUC da
  regra não depende do calibrador; só o Brier depende.
- **Efeito no limiar:** com ou sem peso, o limiar padrão de 0,5 deixa de ser
  informativo; ele é escolhido no G8 (§23).

### 29.13 Alinhamento entre documento e configuração (27/10)

**Corrigido em 27/10** (arquivos em `outputs/corrigidos/`):

1. `supervised.yaml` e `feature_contract_v1.json`: `sensibilidade_qualquer_obito` e
   `sensibilidades.alvo_qualquer_obito` desativadas (a coorte exclui o código 3).
2. `supervised.yaml` e `feature_contract_v1.json`: `vacina_cov` bruta trocada por
   `vacina_cov_previa` no contexto incremental (#84).
3. `supervised.yaml`: `decision_tree` e `random_forest` com `ativa: false`,
   conforme as famílias encerradas (§29.11).
4. `decisoes.yaml` (v0.7): `max_symptom_to_admission_days` 60; regra de datas
   "sintomas depois da internação" passa a `excluir`; `anos_coorte` inclui 2026;
   `cs_zona`, `outro_sin` e `out_morbi` saem de `conditional_vars` e entram em
   `allowed_vars`; sete decisões passam a `aprovada` com a data do gate
   (coorte_estrita, alvo, periodos, variaveis_proibidas, variaveis_condicionais,
   intervalo_sintomas_internacao_82 e sensibilidade_ausencia_83).
5. `final_cohort_v1.yaml`: `status: published`.
6. `dicionario_variaveis_v1.csv` (nome oficial: v1): as seis colunas de dose COVID
   seguem a regra do #84 (data a partir de 2021-01-17 e pelo menos 1 dia antes de
   `dt_interna`) e apontam para `vacina_cov_previa`.
7. `intervalo_politica` (`decisoes.yaml` e `supervised.yaml`): mantida, com
   comentário de que a coorte definitiva exclui os intervalos inválidos.
8. `supervised.yaml` (higiene, lote de 22/10): comentário "não existe G3: a etapa
   foi absorvida pelo G2 em 18/10" acima de `gates:`; `limiar.metricas_candidatas`
   com `youden_j` e `recall_minimo`, mais `limiar.min_recall: 0.80` (para o #80);
   `models.boosting.early_stopping: true` (o código já usava `true`);
   `target.descartar_outros` e `temporal.coluna_estratificacao_temporal` mantidas
   com a marca `# documental`, porque nenhum código as lê.

**Mantido como está, por decisão de 27/10:**

1. As demais decisões do `decisoes.yaml` seguem como `proposta`.
2. As vacinas não COVID do dicionário (`dt_1_dose`, `dt_2_dose`, `dt_doseuni`,
   `dt_ut_dose`, `dt_vac_mae`) mantêm a regra "anterior ou igual a `dt_interna`";
   o #84 trata só das doses COVID.
3. `experimentos_split` (70/15/15) segue como exploratório (`canonico: false`);
   não é o desenho oficial (§21).

**Ainda aberto:**

0. **Anos do desenvolvimento.** O card #73 de 28/10 relata que os YAMLs do
   repositório passaram a colocar 2019 no `test_pandemic` (desenvolvimento só
   com 2023–2025), enquanto este documento (§5, §21, §28), a decisão de 18/10
   e as cópias de `supervised.yaml` e `decisoes.yaml` usadas aqui mantêm 2019
   no desenvolvimento. A mudança não consta como decisão e o G2 segue com data
   de 18/10. Decidir: manter 2019 no desenvolvimento (desfazer o YAML) ou
   mover 2019 para o Teste B (registrar a decisão e reescrever §5, §21 e §28).
1. G1 e G2 constam como aprovados por `time_do_projeto`, não pela Pessoa A. A
   ausência do G3 está explicada no YAML (absorvido pelo G2 em 18/10).
2. Confirmar o `status: published` do contrato da coorte e o `ativa: false` da
   sensibilidade de "qualquer óbito" contra o código que lê esses arquivos.

### 29.14 27/10 · Alinhamento de saturação, desconforto respiratório e vacina

- **Decisão:** saturação e desconforto respiratório só em sensibilidade;
  vacinação (`vacina`, `vacina_cov_previa`), escolaridade e UF só como
  contexto incremental (G1, 22/10; regra de doses do #84).
- **Motivo:** os documentos divergiam. As decisões punham saturação no
  Modelo A, desconforto no Modelo B e vacinação entre as candidatas clínicas;
  o Plano v2 punha a vacinação no modelo; o `supervised.yaml` já seguia o G1.
- **Alinhado em 27/10:** `decisoes.md` (§13 reescrita; §14, §15 e §17
  ajustadas); coluna `uso_inicial_sugerido` do dicionário (`saturacao` e
  `desc_resp` em sensibilidade de gravidade; `vacina`, `vacina_cov`,
  `sg_uf` e `cs_escol_n` em contexto incremental; `outro_sin` passa a
  `modelo_a_nucleo`, pois é uma das 31 features e constava como
  `exploracao_texto`).
- **Pendente:** Plano Unificado v2. Onde diz que a vacinação entra no
  modelo, trocar por contexto incremental; sensibilidade para saturação e
  desconforto já está correta.
- **Implementado em:** itens #54 e #70; `supervised.yaml`.

### 29.15 27/10 · 2026 como período parcial e exclusivamente exploratório (#85)

- **Decisão:** 2026 é parcial (dados até setembro; cerca de 12% dos
  desfechos em aberto; possível subnotificação de agosto em diante) e só
  entra como exploração opcional, depois dos Testes A e B, sem reajuste.
- **Motivo:** desfechos pendentes e atraso de notificação distorcem a
  mortalidade observada; a reunião de 16/10 já havia combinado deixar 2026
  fora do treino.
- **Impacto:** 2026 fica no bloco `exploracao` (173.945 fichas, número do
  card) e é marcado como "parcial" em tabelas e figuras. No
  `supervised.yaml` isso já consta em `anos_parciais: [2026]` e
  `exploracao_2026.ativa: false`.
- **Implementado em:** §5.4 deste documento. Falta registrar no esqueleto do
  relatório (#133, seção Dados) e na nota do #134.

### 29.16 27/10 · Validação que escolhe não é a validação que mede (#118)

- **Decisão:** três validações disjuntas, cada uma com um papel: `val_tune`
  (escolhe features, geografia e hiperparâmetros), `val_cal` (calibra e
  escolhe o limiar) e `val_meas` (só mede, sem influenciar escolhas).
- **Motivo:** no desenho anterior a busca do C_13 usava a validação inteira
  (587.272 linhas) e o C_15 media o resultado em metade dela (293.636), que a
  busca já tinha visto. A nota ficava um pouco otimista.
- **Impacto:** a estimativa pré-teste passa a ser honesta; `val_meas` tem
  `influencia_decisoes: false` no `supervised.yaml`.
- **Implementado em:** `supervised.yaml` (`temporal.blocos`); §21. Conferência
  no #132 (passo 4): confirmar que o `HONEST_CALIB_SPLIT` saiu do C_15.
- **Frase para o relatório (Métodos):** "Os dados de desenvolvimento foram
  divididos em blocos disjuntos por grupo: `train_ref` ajusta os modelos;
  `val_tune` escolhe variáveis, geografia e hiperparâmetros; `val_cal` ajusta
  a calibração e escolhe o limiar; `val_meas` apenas mede o desempenho antes
  do teste e não participa de nenhuma escolha. Assim, nenhuma fatia escolhe e
  mede ao mesmo tempo."

### 29.17 27/10 · Plano do ajuste fino (G6), registrado antes dos resultados

- **Decisão:** busca curta e reproduzível, não exaustiva, sem validação
  cruzada (aceito pelo professor, por causa do tamanho da base). Escolha em
  `val_tune`, por PR-AUC; logística mantida como baseline interpretável.
- **Logística:** C em {0,01; 0,1; 1; 10}, penalidade L2. Na melhor C, uma
  rodada extra com L1 (ou elastic-net, `l1_ratio` 0,5), anotando quantos
  coeficientes ficam diferentes de zero e se algum sinal muda (parágrafo de
  Métodos sobre regularização).
- **Boosting (categóricas nativas):** configurações aleatórias, semente 42,
  sobre `learning_rate` {0,05; 0,1}, `max_leaf_nodes` {31; 63},
  `min_samples_leaf` {50; 200}, `l2_regularization` {0; 1}, `max_depth`
  {None; 8}, com `early_stopping` e `max_iter` até 1.000.
- **Escolha dentro da família:** maior PR-AUC em `val_tune`; se a diferença
  for menor que 0,002, vale a configuração mais simples.
- **Finalista:** o boosting só vence se superar a logística em pelo menos
  0,005 de PR-AUC e não tiver Brier calibrado pior (no piloto estava 0,027 à
  frente). Peso de classe: rodar o #5 no vencedor.
- **Consequência:** a calibração e o limiar que o C_15 já gerou valem para
  modelos sem ajuste e precisam ser refeitos depois do G6 (G7 e G8).
- **Registro:** `outputs/final/tuning_val_tune.csv` (uma linha por
  configuração, com tempo), hiperparâmetros no YAML e
  `selecao_modelos.finalista_escolhido`.
- **Divergências a resolver antes de rodar (Pessoa A e Pessoa C):**
  1. Número de configurações do boosting: 6 (cabeçalho do card), 12 (decisão
     de 18/10 e passo 2) ou 8 (corte por tempo). O YAML permite até 30
     (`tuning.max_configuracoes_por_modelo`).
  2. Subamostra do `train_ref`: 500 mil (decisão de 18/10) ou 600 mil
     (passo 3 do card).
  3. Grades: o YAML tem `busca_C` com 0,001, `busca_learning_rate` com 0,03,
     `busca_max_iter` {300, 500, 1000} e `busca_max_depth` {None, 4, 6, 8},
     além de `max_leaf_nodes`, `min_samples_leaf` e `l2_regularization`
     fixos. O plano acima usa outras grades e varia esses três parâmetros.
  4. "Só HGB" (decisão de 18/10) contra logística também ajustada em C.
  5. L1 e elastic-net exigem solver `saga`; o YAML usa `lbfgs` e `penalty: l2`.
  6. A regra de 0,005 e 0,002 não consta no YAML nem no texto do G6.
  7. O "cenário vencedor do E_02" não aparece nos arquivos de configuração.
  8. "Brier calibrado" não pode ser medido em `val_cal` sem otimismo, porque
     `val_cal` ajusta o calibrador, nem em `val_meas`, que não pode influenciar
     decisões (§21). Definir o bloco ou o procedimento (por exemplo,
     calibrar numa metade dos grupos de `val_cal` e medir na outra).
  9. Ordem do G6: o C_13 só busca depois do G6 aprovado, mas o checklist do
     G6 (#78) exige a busca feita e o finalista no YAML. Definir se o G6
     libera a busca (checklist: coorte, #50, #54) ou aprova o resultado dela,
     e registrar o outro passo com outro nome.

### 29.18 27/10 · Sensibilidades (#54): pontos a decidir antes de rodar

- **Linha "qualquer óbito":** o card inclui o alvo com evolução 2 ou 3 como
  positivo, mas a coorte definitiva exclui o código 3 (D_COORTE_003) e a
  sensibilidade foi desativada no `supervised.yaml` (§29.13). A linha não
  pode ser calculada na coorte atual. Decidir: retirar a linha da tabela ou
  republicar a coorte preservando o código 3.
- **Nome da variável de vacina:** o card cita `vacina_cov_antes_admissao`; o
  #84, o `supervised.yaml` e o `feature_contract_v1.json` usam
  `vacina_cov_previa`. Usar um só nome.
- **Linha "contexto":** o card lista `cs_escol_n` e `vacina`; o G1 e o
  `supervised.yaml` incluem também `sg_uf` e `vacina_cov_previa` no contexto
  incremental.
- **Linha "+ região":** acrescenta `regiao_residencia` como variável, enquanto
  o #110 trata a geografia como separação da análise, sem região como
  variável (§29.8). Se a linha ficar, rotular como ablação e não como modelo.
- **Lista de sensibilidades:** as linhas do card (sintomas de 2019,
  sazonalidade, gravidade, contexto, região, qualquer óbito) não coincidem
  com as chaves de `sensibilidades` no `supervised.yaml` (temporal,
  com_sem_indicadores_ausencia, sem_saturacao_desc_resp, contexto_incremental,
  alvo_qualquer_obito). Alinhar o YAML ao que será rodado.

### 29.19 27/10 · Três sintomas vazios em 2019 (#50): critério registrado antes dos números

- **Problema:** `perd_olft`, `perd_pala` e `fadiga` só existem na ficha a partir
  da COVID-19. Em 2019 vêm quase sempre em branco (cerca de 99,7%, 99,7% e
  99,4%), e o pré-processador transforma o branco em `AUSENTE`. Como 2019 está
  no treino e tinha mortalidade maior, o modelo pode aprender um "marcador de
  ano": três campos em branco indicariam 2019 e, portanto, risco mais alto.
  Em 2019 o vazio significa "campo inexistente", não "não informado".
- **Orientação de 24/10:** estudar as três variáveis e retirar só se o efeito
  for muito determinístico, sem tirar "só por tirar".
- **Critério proposto (card #50):** retirar as três, o que reabre o G1 por
  falha material, se (a) a ROC-AUC de 2019 subir pelo menos 0,01 sem elas, ou
  (b) a PR-AUC geral cair no máximo 0,005 sem elas, ou (c) a importância por
  permutação das três vier quase toda de 2019. Se nenhuma ocorrer, manter e
  documentar.
- **Achado do dicionário (preliminar):** `dor_abd`, que está nas 31 features
  principais, tem até 99,7% de branco em algum ano, como os três sintomas.
  Também passam de 90% em algum ano `vacina_cov` (contexto) e as três
  variáveis do card. Os valores mínimo e máximo do dicionário cobrem 2019–2026,
  não só os anos de desenvolvimento, e não dizem em que ano ocorrem; a tabela
  por ano (`campos_por_ano.csv`) confirma.
- **Pontos a resolver antes de aplicar o critério:**
  1. O critério (b) retira as variáveis sempre que elas não ajudam, o que é
     "tirar só por tirar", contra a orientação de 24/10.
  2. O critério (a) mede a ROC-AUC de 2019 numa amostra pequena (6.509 fichas
     de validação; `val_meas` tem menos), em que 0,01 está dentro do ruído. Pede
     intervalo pareado (#127).
  3. A medida por ano é feita em `val_meas`, que não pode influenciar decisões
     (§21); decidir em `val_tune` e `val_cal`, e usar `val_meas` só para
     confirmar.
  4. O critério (c) não tem número: definir "quase toda" (por exemplo, mais de
     80% da importância vinda de 2019).
  5. Incluir `dor_abd` no estudo, ou justificar por que fica fora.
- **Confirmado no B_06 (27/10, coorte definitiva):** branco em 2019 de 99,7%
  em `perd_olft` e `perd_pala` e 99,5% em `fadiga`; em 2020 ainda cerca de 55%;
  em 2023–2025, de 19% a 32%. A tabela por ano já existe em
  `eda_02_sintomas_por_ano.csv`.
- **Dependência da decisão sobre 2019 (§29.13, item 0):** se 2019 sair do
  treino e for para o Teste B, o modelo não aprende o marcador de ano com 2019,
  mas passa a ser testado em 2019 com esses campos quase 100% vazios. O
  critério deixa de ser "retirar para evitar o atalho" e vira "o teste em 2019
  é confiável?". A decisão passa pelo #140 (30/10).
- **Registro:** a decisão final entra aqui, com a tabela, depois do #54.

### 29.20 27/10 · Importância das variáveis e razões de chances: cuidados de leitura (#91, #57, #71)

- **Decisão (card #91):** responder à segunda metade da pergunta de pesquisa
  (quais características pesam no risco) com razão de chances ajustada da
  logística e importância por permutação do boosting, calculadas no modelo
  final e nunca no teste.
- **Regras de leitura para o relatório:**
  1. Razões de chances são "associação ajustada e regularizada, não causal".
  2. Informar a unidade de cada variável numérica (por ano de idade ou por
     desvio-padrão, conforme o pré-processador) e a categoria de referência.
  3. A logística é regularizada (L2) e pode usar `class_weight`, então os
     coeficientes não têm erro-padrão válido. Reportar sem intervalo de
     confiança, ou com bootstrap, e dizer qual. A razão de chances muda se o
     peso de classe mudar (#5).
  4. Categorias `AUSENTE` não são efeito clínico: refletem padrão de
     preenchimento e, em `perd_olft`, `perd_pala`, `fadiga` e `dor_abd`, o ano da
     ficha (§29.19). Não interpretar essas categorias.
  5. Importância por permutação de variáveis correlacionadas (sintomas,
     comorbidades) tende a subestimar cada uma; ler por grupo quando fizer
     sentido.
  6. Razões brutas, como as do B_06, sofrem confundimento pela idade (asma e
     tosse aparecem como "protetoras"); mostrar bruto e ajustado lado a lado.
- **Ponto a resolver:** a permutação é calculada em `val_meas`. Como
  interpretação, tudo bem. Mas se ela for usada para decidir reduzir variáveis,
  alimentar o UMAP ou escolher features, passa a influenciar decisões, o que
  `val_meas` não pode (§21). Nesse caso, calcular em `val_tune` e reservar
  `val_meas` para o relatório.
- **Depende de:** G6 (finalista), #5 (peso de classe) e #50 (decisão sobre os
  três sintomas).

### 29.21 27/10 · Plano do G7 (calibração), registrado antes dos resultados

- **Decisão (card #79):** calibrar o finalista congelado (FrozenEstimator)
  com dois métodos, `sigmoid` e `isotonic`, ajustados só em `val_cal`; a
  ordenação não muda (PR-AUC e ROC-AUC iguais, com tolerância).
- **Métricas:** Brier, log loss, intercepto e inclinação de calibração, ECE
  com 10 faixas por quantis e curva de calibração.
- **Regra de escolha proposta:** menor Brier; se a diferença for menor que
  0,0005, `sigmoid`. A proposta do C_15 (sigmoid no boosting, isotônica na
  logística) foi feita sobre modelos sem ajuste fino e precisa ser refeita
  depois do G6 e do #5.
- **Ponto a resolver:** o card manda escolher o método pelo menor Brier em
  `val_meas`, mas `val_meas` não pode influenciar decisões (§21). Escolher o
  método dentro de `val_cal` (calibrar numa metade dos grupos e medir na
  outra, ou validação cruzada por grupo) e usar `val_meas` só para confirmar e
  relatar o Brier e a curva finais. É o mesmo ponto do G6 (§29.17, item 8) e
  do peso de classe (§29.12).
- **Referência numérica:** os valores do C_15 (Brier 0,196 → 0,141; modelo
  nulo 0,171) são da coorte provisória, com 21,9% de óbitos. Na coorte
  definitiva (8,4%) o modelo nulo tem Brier de cerca de 0,077, e esse é o
  parâmetro de comparação. Não citar os dois conjuntos juntos.
- **Ordem:** G6 (finalista), #5 (peso de classe), G7 (método), G8 (limiar),
  G9. Mudar o peso de classe ou o finalista invalida a calibração.
- **YAML:** `calibracao.metodo` e `G7_calibracao` (status, aprovado por, data)
  são preenchidos ao fim. `calibracao.fonte` diz só "validacao"; deve nomear
  `val_cal`.

### 29.22 27/10 · Plano do G8 (limiar), registrado antes dos resultados

- **Decisão proposta (card #80):** o corte principal é o de maior precisão
  entre os que têm sensibilidade de pelo menos 0,80, escolhido em `val_cal`
  com as probabilidades calibradas (G7). O professor disse que 80% de
  sensibilidade "já está bom" e 70% "já está muito bom". Referências, só para
  mostrar: sensibilidade de pelo menos 0,70, F1 máximo e Youden. Faixas de
  risco (baixo, médio, alto, pelos tercis em `val_cal`) só como descrição.
  Os cortes são medidos em `val_meas` sem alterá-los. Os cortes por região
  (#110) usam a mesma regra; o G8 entrega só o global.
- **YAML:** `limiar.metrica: recall_minimo`, `limiar.min_recall: 0.80`,
  `limiar.otimo` e o G8 (status, aprovado por, data).
- **Substitui:** a proposta anterior do C_15 (F1, corte 0,255), calculada
  sobre modelo sem ajuste fino e na coorte provisória (21,9% de óbitos).
- **Pontos a resolver:**
  1. Os números do card (cortes de 1% a 25,5%, F1 de 0,516) são da coorte
     provisória. Com 8,4% de óbitos na definitiva, o corte de 80% de
     sensibilidade deve ficar bem mais baixo, e a tabela de 0,05 a 0,60 com
     passo 0,05 ficaria grossa justamente onde está a decisão. Usar passo
     fino (por exemplo 0,01) de 0,01 a 0,30.
  2. A precisão do alerta depende da prevalência, que varia por ano (12,0%
     em 2019, 7,2% em 2025, números do #50). O mesmo corte terá precisão
     diferente em cada ano; reportar por ano.
  3. O corte é escolhido na amostra de `val_cal`, então a sensibilidade de 0,80
     é uma estimativa com erro. Informar a sensibilidade medida em `val_meas`
     com intervalo, e não afirmar que o alerta "pega 80%".
- **Ordem:** só depois do G7. Mudar finalista, peso de classe ou calibrador
  invalida o corte.

### 29.23 27/10 · Âncora temporal e quem ficou de fora (#56)

- **Decisão (D_COORTE_002):** a data de internação (`dt_interna`) é a âncora
  temporal obrigatória; `dt_notific` não é usada como âncora nem como
  preditora (consta nas variáveis proibidas).
- **Evidência a produzir:** (1) dias entre `dt_notific` e `dt_interna`
  (mediana e intervalo interquartil) por ano e desfecho; (2) hospitalizados
  excluídos por desfecho não elegível contra incluídos, por ano, região e faixa
  etária; (3) entre os intervalos negativos (D_COORTE_006), a distribuição por
  `nosocomial` e desfecho. Script: `tools/ancora_e_excluidos.py`. Saídas em
  `outputs/final/`. As frases de leitura só se escrevem com os números.
- **Números de referência:** a exclusão por evolução (D_COORTE_003) soma 530.370
  linhas e, segundo o dicionário, é composta por 340.351 vazias, 103.570 com
  código 9 e 86.449 com código 3. Os valores do card (97.786 e 36.923) vêm do
  waterfall do A_03, de outra etapa e coorte, e não devem ser citados como o
  total excluído. Usar o `coorte_waterfall.csv` da coorte definitiva.
- **Separar duas coisas na tabela 2:** código 3 é óbito por outra causa (o
  desfecho é conhecido, mas fora do alvo); código 9 e vazio são ausência de
  desfecho. O viés de seleção é diferente em cada caso, e a ausência de
  desfecho deve se concentrar nos anos recentes (2026 parcial, §5.4).
- **Limite conhecido:** o dicionário (88 colunas) não tem a coluna
  `nosocomial`. Se ela também não estiver no `srag.parquet`, a tabela 3 não
  pode ser feita. Nesse caso, registrar como limitação: não é possível
  distinguir infecção adquirida no hospital dos intervalos negativos, e a
  exclusão pela D_COORTE_006 não depende dessa informação (§8).

### 29.24 28/10 · "Fatores de risco" (`fator_risc`): o branco das comorbidades é "não"? (verificação antes do treino)

- **Hipótese:** a ficha tem a pergunta-mãe `fator_risc`. Se a lista de
  comorbidades só é preenchida quando a resposta é "sim", o branco numa
  comorbidade com `fator_risc` = não significa "não tem", e não "não
  informado". Hoje o pré-processador transforma esse branco em `AUSENTE`.
- **Por que importa:** as 12 comorbidades estão em branco em 61% a 69% das
  fichas de 2023–2025 (asma 69%, cardiopatia 66%), e o branco é mais comum nas
  curas do que nos óbitos (cardiopatia: 59,8% contra 38,8%; diferença de 13 a
  21 pontos percentuais). Se a hipótese se confirmar, parte do "viés de
  documentação" (#52) é a regra de preenchimento da ficha, e a categoria
  `AUSENTE` carrega "não tem comorbidade", ligada a menos óbitos.
- **Verificação (Pessoa A):** `notebooks/A/A_15_fator_risco.ipynb`, só leitura
  de `coorte_final.parquet`: (1) `fator_risc` × comorbidade em branco, por ano;
  (2) mortalidade por valor de `fator_risc`; (3) a diferença de ausência entre
  curas e óbitos só entre fichas com `fator_risc` = sim. Saídas em
  `outputs/tables/eda_02_fator_risc_*.csv`.
- **Regra proposta, se a hipótese se confirmar:** comorbidade em branco com
  `fator_risc` = não vira "2" (não); com `fator_risc` = sim, ignorado ou
  branco, continua `AUSENTE`. `fator_risc` não entra como variável do modelo
  por padrão, por ser redundante; decidir no #140 com a ablação.
- **Critério de confirmação (proposta, a combinar antes de ver os números):**
  confirmada se, em 2023–2025, o branco com `fator_risc` = não for de pelo menos
  90% em todas as comorbidades e pelo menos 30 pontos percentuais menor com
  `fator_risc` = sim. Os cortes são sugestão desta entrada; o card diz apenas
  "quase 100%" e "bem menor".
- **Pontos de atenção:**
  1. A regra `missingness.vazio_nao_e_nao` do `supervised.yaml` passaria a ter
     uma exceção documentada, só para comorbidades com `fator_risc` = não.
  2. Recodificar 12 variáveis muda a representação das features congeladas no
     G1; só se justifica como falha material e precisa de registro (G1
     reaberto) antes do G6.
  3. `fator_risc` existe em `coorte_final.parquet` e não está no dicionário
     (#70). Confirmar o mapeamento de códigos por ano (1/2/9, S/N ou texto).
  4. Se `fator_risc` também for preenchido mais vezes "não" ou ficar em branco
     de modo diferente entre curas e óbitos, a recodificação embute esse padrão.
     A tabela 2 (mortalidade por valor de `fator_risc`, por ano) mostra isso.
  5. Afeta o #54 (linha "P com comorbidades recodificadas"), o #52 e o #136
     (não supervisionado).


### 29.25 29/10 · Reversão da mudança não registrada sobre 2019

- **Decisão:** 2019 permanece no desenvolvimento (`train_ref`, `val_tune`,
  `test_ref`) e **não** entra em `test_pandemic`. Os YAMLs
  `configs/supervised.yaml` e `configs/decisoes.yaml` foram revertidos
  para o estado descrito em §5, §21 e §28.
- **Motivo:** A mudança que colocava 2019 no `test_pandemic` foi feita
  nos YAMLs sem registro no `decisoes.md` (§29.13, item 0). Como toda a
  documentação oficial, os testes (`tests/test_split.py`) e as saídas
  salvas do `B_07` pressupõem 2019 no desenvolvimento, a alteração é
  tratada como erro de configuração, não como decisão.
- **Impacto:** O card #50 mantém a leitura original: o modelo pode
  aprender o "marcador de ano" com 2019 no treino, e a decisão sobre
  retirar `perd_olft`, `perd_pala` e `fadiga` segue o critério combinado.
- **Implementado em:** `configs/supervised.yaml` (seção `periodo` e
  `temporal.blocos`), `configs/decisoes.yaml` (`dev_years`,
  `pandemic_test_years`), e esta entrada.
- **Substitui:** §29.13, item 0.