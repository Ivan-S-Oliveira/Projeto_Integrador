# Projeto Integrador --- SRAG e Machine Learning

Projeto acadêmico desenvolvido no âmbito do **Projeto Integrador I da
Pós-Graduação em Inteligência Artificial**. Investiga o uso de técnicas
de aprendizado de máquina sobre dados públicos de Síndrome Respiratória
Aguda Grave (SRAG), com foco em preparação de dados, avaliação de
modelos e reprodutibilidade.

> **Status:** em desenvolvimento. A seleção final do modelo, a
> calibração, a definição do limiar e a avaliação final ainda dependem
> da conclusão dos gates metodológicos configurados no projeto.

## Objetivo

Construir um fluxo reproduzível para estudar a previsão retrospectiva de
óbito por SRAG a partir de informações disponíveis **no momento da
internação hospitalar**. O trabalho envolve:

-   acesso, organização e preparação dos dados;
-   definição e rastreabilidade da coorte analítica;
-   análise exploratória e experimentos não supervisionados;
-   engenharia e validação de atributos;
-   comparação de modelos supervisionados;
-   calibração das probabilidades e escolha de limiar;
-   avaliação de erros e análise de desempenho por grupos;
-   documentação dos experimentos e das limitações.

O projeto tem finalidade **acadêmica e exploratória**. Não é um sistema
clinicamente validado, não deve ser usado para diagnóstico ou decisão
clínica e não permite inferir causalidade a partir de associações
preditivas.

## Fonte dos dados

Os dados são provenientes da base pública **SRAG 2019--2026**,
disponibilizada pelo Ministério da Saúde por meio da API de Dados
Abertos.

-   **Fonte:** Ministério da Saúde --- Dados Abertos
-   **Endpoint:**
    <https://apidadosabertos.saude.gov.br/vigilancia-e-meio-ambiente/srag-2019-2026>

O projeto utiliza arquivos Parquet e rotinas de acesso/armazenamento. Os
dados originais, arquivos Parquet, modelos treinados e resultados
volumosos não devem ser versionados diretamente no Git.

## Arquitetura e organização

A lógica reutilizável deve ficar em `src/`; notebooks devem orquestrar
experimentos, explicar decisões e apresentar tabelas e gráficos.
Parâmetros e decisões metodológicas devem permanecer centralizados em
`configs/` e `docs/`.

``` text
Projeto_Integrador/
├── configs/
│   ├── dicionario_variaveis_v1.csv
│   └── supervised.yaml
├── docs/
│   └── decisoes.md
├── notebooks/
│   ├── 00_acesso_dados_parquet.ipynb
│   ├── 01_extracao.ipynb
│   ├── 02_eda/
│   │   ├── 01_eda_primeira_passagem.ipynb
│   │   ├── 02_eda_temporal_clustering.ipynb
│   │   ├── 03_supervisionado_pilotos.ipynb
│   │   ├── 04_consolidacao_shortlist_transicao_coorte.ipynb
│   │   └── _provisorio_construcao_coorte_b.ipynb
│   └── C/
│       ├── C1_smoke_test.ipynb
│       ├── C2_pipeline_supervisionado.ipynb
│       ├── C3_baseline_logistica.ipynb
│       ├── C4_boosting.ipynb
│       ├── C5_calibracao_limiar.ipynb
│       └── C6_validacao_final.ipynb
├── src/
│   ├── data/
│   │   ├── cohort_source.py
│   │   ├── split.py
│   │   └── supervised_artifact.py
│   ├── evaluation/
│   │   ├── calibration.py
│   │   ├── errors.py
│   │   ├── leakage.py
│   │   ├── metrics.py
│   │   └── temporal.py
│   ├── features/
│   │   ├── engineering.py
│   │   └── normalization.py
│   ├── models/
│   │   ├── baseline.py
│   │   ├── boosting.py
│   │   ├── calibration.py
│   │   ├── factory.py
│   │   ├── logistic.py
│   │   └── pipeline.py
│   └── utils/
│       ├── config.py
│       ├── env.py
│       ├── reproducibility.py
│       └── storage.py
├── tests/
├── tools/
│   └── update_project_reference.py
├── .env.example
├── .gitignore
├── pyproject.toml
├── requirements.txt
└── README.md
```

A árvore acima destaca os principais componentes identificados na
referência do projeto; `tests/` contém testes automatizados para
configuração, coorte, atributos, partições, pipeline, métricas,
calibração, leakage e reprodutibilidade. Consulte os arquivos do
repositório para a lista completa.

### Responsabilidades principais

  ---------------------------------------------------------------------------
  Componente                              Responsabilidade
  --------------------------------------- -----------------------------------
  `configs/supervised.yaml`               Configura alvo, período, atributos,
                                          partições, modelos, métricas e
                                          gates metodológicos.

  `configs/dicionario_variaveis_v1.csv`   Dicionário de variáveis.

  `docs/decisoes.md`                      Registro das decisões
                                          metodológicas.

  `src/data/`                             Resolução/carregamento da coorte,
                                          partições e artefatos
                                          supervisionados.

  `src/features/`                         Engenharia e normalização de
                                          atributos.

  `src/models/`                           Construção de pipelines, modelos e
                                          calibração.

  `src/evaluation/`                       Métricas, avaliação temporal,
                                          calibração, erros e verificações de
                                          leakage.

  `src/utils/`                            Configuração, ambiente,
                                          armazenamento e reprodutibilidade.

  `tests/`                                Verificações automatizadas dos
                                          contratos do projeto.

  `notebooks/`                            Exploração, experimentos,
                                          orquestração e comunicação dos
                                          resultados.
  ---------------------------------------------------------------------------

## Notebooks

  -----------------------------------------------------------------------------------------------
  Notebook                                                    Finalidade
  ----------------------------------------------------------- -----------------------------------
  `00_acesso_dados_parquet.ipynb`                             Verificar o acesso aos dados
                                                              Parquet.

  `01_extracao.ipynb`                                         Documentar a etapa de extração.

  `02_eda/01_eda_primeira_passagem.ipynb`                     Primeira exploração e diagnóstico
                                                              dos dados.

  `02_eda/02_eda_temporal_clustering.ipynb`                   Análises temporais e experimentos
                                                              de agrupamento.

  `02_eda/03_supervisionado_pilotos.ipynb`                    Experimentos supervisionados
                                                              preliminares.

  `02_eda/04_consolidacao_shortlist_transicao_coorte.ipynb`   Consolidar a shortlist e a
                                                              transição da coorte.

  `02_eda/_provisorio_construcao_coorte_b.ipynb`              Notebook provisório de construção
                                                              de coorte; confirmar sua
                                                              necessidade antes de tratá-lo como
                                                              fluxo oficial.

  `C/C1_smoke_test.ipynb`                                     Verificar componentes essenciais do
                                                              ambiente e do projeto.

  `C/C2_pipeline_supervisionado.ipynb`                        Orquestrar e validar o pipeline
                                                              supervisionado.

  `C/C3_baseline_logistica.ipynb`                             Executar referências e experimentos
                                                              com regressão logística.

  `C/C4_boosting.ipynb`                                       Executar a busca limitada e avaliar
                                                              boosting.

  `C/C5_calibracao_limiar.ipynb`                              Escolher calibração e limiar usando
                                                              dados permitidos.

  `C/C6_validacao_final.ipynb`                                Executar o protocolo de validação
                                                              final, condicionado à liberação do
                                                              gate correspondente.
  -----------------------------------------------------------------------------------------------

Os notebooks devem evitar implementações duplicadas de funções
reutilizáveis. Uma função deve migrar para `src/` quando representar uma
responsabilidade compartilhada ou uma regra que precise de testes;
código exclusivo de apresentação e orquestração pode permanecer no
notebook.

## Metodologia supervisionada

### Alvo e momento da previsão

A configuração ativa define:

-   coluna de origem do alvo: `evolucao`;
-   coluna de modelagem: `alvo_obito_srag`;
-   classe positiva: valor `2.0`;
-   classe negativa: valor `1.0`;
-   descarte de outros valores para o alvo principal: habilitado;
-   análise de sensibilidade para qualquer óbito: configurada
    separadamente.

O momento de previsão definido metodologicamente é a **internação
hospitalar**. Informações registradas depois desse momento não devem ser
usadas como atributos de entrada.

### Período e partições

A configuração abrange 2019--2026, incluindo 2026 como ano parcial. A
partição primária atualmente configurada é **aleatória estratificada por
alvo e ano de internação**, com seed `42` e proporções:

-   treino: 70%;
-   validação: 15%;
-   teste/holdout: 15%.

**Importante:** apesar do interesse em comportamento temporal, essa
configuração não corresponde a uma separação estritamente cronológica
entre passado e futuro. Análises temporais adicionais podem ser usadas
como análises de robustez, mas não devem substituir silenciosamente a
partição primária definida na configuração. A documentação e os
resultados devem explicitar essa escolha.

### Atributos e prevenção de leakage

A configuração inclui atributos numéricos e categóricos, além de regras
para engenharia de atributos. A lista final de atributos ainda depende
da confirmação do gate `G1_definicao_alvo_features`.

Variáveis relacionadas ao desfecho ou a informações posteriores à
internação estão listadas entre as proibidas em
`configs/supervised.yaml`. Antes de treinar, verificar:

1.  se cada atributo estava disponível no momento da internação;
2.  se o alvo não aparece entre as entradas;
3.  se transformações e imputações são ajustadas somente nos dados de
    treino;
4.  se treino, validação e teste respeitam os contratos de partição;
5.  se a coorte e a lista de atributos estão documentadas e versionadas
    por metadados.

Não use o holdout final para escolher modelo, hiperparâmetros,
calibração ou limiar.

### Modelos e seleção

A configuração prevê baseline, regressão logística, árvore de decisão,
random forest e boosting. A shortlist provisória registrada aponta
`hist_gradient_boosting` e `logistic` como finalistas candidatos; isso
não equivale a uma escolha final de modelo. A métrica principal
configurada para comparação é `PR-AUC`.

### Calibração, limiar e avaliação

A configuração prevê comparar métodos de calibração (`sigmoid` e
`isotonic`) e avaliar o Brier Score antes e depois da calibração. O
limiar deve ser escolhido apenas com dados de validação, de acordo com
os critérios registrados na configuração.

As métricas configuradas incluem:

-   PR-AUC e ROC-AUC;
-   Brier Score e log loss;
-   precisão, recall/sensibilidade, F1 e especificidade;
-   matriz de confusão;
-   avaliação por grupos e por ano;
-   análise de erros, com prioridade para falsos negativos;
-   bootstrap para estimativa de incerteza, conforme os parâmetros
    ativos.

As métricas finais devem ser publicadas somente após a execução válida
do protocolo de avaliação e acompanhadas do contexto, tamanho da amostra
e limitações.

## Gates metodológicos e status

Os gates em `configs/supervised.yaml` registram decisões que precisam
ser concluídas antes de avançar. No snapshot documentado:

  -----------------------------------------------------------------------
  Gate                    Situação registrada     Significado
  ----------------------- ----------------------- -----------------------
  G1 --- alvo e atributos Pendente                Confirmar coorte
                                                  definitiva, alvo e
                                                  lista final de
                                                  atributos.

  G2 --- janela e         Aprovado                Período e estratégia de
  partições                                       partição registrados.

  G4 --- baseline         Aprovado                Execução do modelo de
                                                  referência registrada.

  G5 --- pilotos          Aprovado                Pilotos supervisionados
                                                  registrados.

  G6 --- finalistas e     Pendente                Selecionar finalista e
  tuning                                          concluir busca
                                                  limitada.

  G7 --- calibração       Pendente                Escolher método com
                                                  dados permitidos.

  G8 --- limiar           Pendente                Definir limiar usando
                                                  validação.

  G9 --- holdout final    Pendente                Liberar e executar o
                                                  teste final uma única
                                                  vez, após congelar as
                                                  decisões.
  -----------------------------------------------------------------------

Esses estados são os registrados no snapshot de referência e podem
mudar. Consulte sempre `configs/supervised.yaml` e os testes antes de
executar ou descrever uma etapa como concluída.

## Configuração do ambiente

Recomenda-se executar o projeto em ambiente virtual, na raiz do
repositório.

### Windows PowerShell

``` powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Se a política do PowerShell impedir a ativação, use o terminal Command
Prompt:

``` bat
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Configure o interpretador do ambiente `.venv` no VS Code. Não é
necessário remover a instalação global do Python para usar esse
ambiente.

### Segredos e dados privados

O projeto inclui `.env.example` como referência de configuração. Nunca
comite tokens, arquivos `.env` com valores reais, senhas ou credenciais.
Se o acesso aos dados exigir `GITHUB_TOKEN`, configure-o como variável
de ambiente ou pelo mecanismo de segredos suportado pelo ambiente de
execução.

## Testes

Execute os testes a partir da raiz do repositório, com o ambiente
virtual ativado:

``` powershell
python -m pytest
```
Por padrão, `pytest` roda só os rápidos.
Suíte completa:  pytest -m ""
Só os lentos:    pytest -m slow
Só os de rede:   pytest -m net

Se o comando não estiver disponível, confira se as dependências de
desenvolvimento estão instaladas no ambiente selecionado. Após mudanças,
execute os testes pertinentes, revise o diff e verifique se a
documentação continua coerente com código e configuração.

## Reprodutibilidade e artefatos

Para permitir a rastreabilidade dos experimentos:

-   mantenha parâmetros e decisões em `configs/` e `docs/`;
-   registre seeds, versões, origem e identificação da coorte;
-   mantenha transformações reutilizáveis em `src/`;
-   registre resultados e metadados sem expor dados sensíveis;
-   preserve a separação entre desenvolvimento e holdout;
-   use `.gitignore` para impedir o versionamento de dados grandes,
    modelos, saídas geradas, segredos e caminhos locais.

Os artefatos e resultados devem seguir as convenções já utilizadas no
projeto. Não crie diretórios alternativos para a mesma finalidade sem
antes verificar a organização existente.

## Pontos de atenção conhecidos

A referência estática do repositório identificou itens que precisam ser
conferidos; eles não significam automaticamente que toda a
funcionalidade esteja quebrada:

1.  **Importação de `csv_to_parquet`:** `tests/test_pipeline.py`
    referencia `src.data.extracao.csv_to_parquet`, mas o módulo
    correspondente não aparece entre os arquivos rastreados no snapshot.
    Verifique histórico de renomeação e atualize o teste ou a
    implementação canônica, sem recriar o módulo às cegas.
2.  **Engenharia de atributos:** nomes derivados configurados --- como
    `sin_semana`, `cos_semana`, `ano_internacao` e
    `dias_sintomas_ate_internacao` --- não foram todos encontrados como
    nomes estáticos nos módulos de `src/data/` e `src/features/`.
    Confirme sua geração real e cubra o contrato com testes.
3.  **Documentação de decisões:** `docs/decisoes.md` cita
    `configs/dicionario_variaveis_v1_revisao.csv`, que não aparece na
    lista de arquivos rastreados do snapshot. Atualize a referência ou
    restaure o arquivo se ele for realmente necessário.
4.  **Lógica nos notebooks:** há funções auxiliares locais nos notebooks
    de EDA e modelagem. Avalie caso a caso se são exclusivas de um
    experimento ou se devem ser promovidas a módulos testados em `src/`.
5.  **Caminhos e estrutura:** mantenha este README sincronizado com os
    arquivos reais; a referência do projeto é um snapshot estático, não
    uma verificação de execução ponta a ponta.

## Limitações

Os dados públicos podem conter ausências, inconsistências, duplicidades,
diferenças de preenchimento e mudanças ao longo do tempo. A definição da
coorte, do alvo e das variáveis disponíveis influencia os resultados. O
ano de 2026 está configurado como parcial e exige interpretação
cuidadosa.

Os resultados descrevem desempenho preditivo na população e nas
condições avaliadas. Não demonstram causalidade, não garantem
generalização para outros períodos ou populações e não constituem
validação clínica.

## Autores

-   **Ivan Schincariol Oliveira** ---
    [LinkedIn](https://www.linkedin.com/in/ivan-s-oliveira-3608a92aa/)
-   **Eduardo Hudson de Almeida Leite** ---
    [LinkedIn](https://www.linkedin.com/in/eduardo-hudson-de-almeida-leite-71ab5a7b/)
-   **Pedro Henrique Silva dos Santos** ---
    [LinkedIn](https://www.linkedin.com/in/pedro-h-s-santos/)
-   **Mateus da Silva Oliveira** ---
    [LinkedIn](https://www.linkedin.com/in/mateusso)

## Contexto acadêmico

**Projeto Integrador I --- Pós-Graduação em Inteligência Artificial.**

O projeto reúne práticas de engenharia de dados, análise exploratória,
aprendizado supervisionado e não supervisionado, engenharia de
atributos, avaliação de modelos, prevenção de vazamento de informação e
reprodutibilidade.
