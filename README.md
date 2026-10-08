# Projeto Integrador — SRAG Machine Learning

Projeto desenvolvido como parte do **Projeto Integrador I** da Pós-Graduação em Inteligência Artificial.

O projeto investiga a aplicação de técnicas de **Machine Learning** sobre dados públicos de **Síndrome Respiratória Aguda Grave (SRAG)** disponibilizados pelo Ministério da Saúde.

> 🚧 **Status:** Projeto em desenvolvimento.

## 🎯 Objetivo

Desenvolver um fluxo de Machine Learning **reprodutível e temporalmente consistente** aplicado aos dados de SRAG, abrangendo:

1. Extração e armazenamento dos dados;
2. Preparação e construção da população analítica;
3. Análise exploratória e aprendizado não supervisionado;
4. Engenharia de atributos e preparação para modelagem;
5. Modelagem supervisionada;
6. Validação temporal;
7. Calibração de probabilidades e definição de limiar;
8. Análise de erros;
9. Validação final em holdout temporal.

A estrutura do projeto busca manter código, configurações, dados, modelos e resultados organizados para facilitar a reprodução dos experimentos em diferentes ambientes.

---

## 📊 Dados

Os dados utilizados são provenientes da base pública **SRAG 2019–2026**, disponibilizada pelo Ministério da Saúde por meio da API de Dados Abertos.

**Fonte:** Ministério da Saúde — Dados Abertos

Endpoint utilizado:

```text
https://apidadosabertos.saude.gov.br/vigilancia-e-meio-ambiente/srag-2019-2026
```

A extração é realizada em Python e os dados são organizados em camadas para separar a fonte original, os dados processados e a população utilizada na modelagem.

### Camadas dos dados

| Camada | Finalidade |
|---|---|
| `data/raw/` | Dados obtidos diretamente das fontes, sem as transformações analíticas finais. |
| `data/processed/` | Dados processados e armazenados para reutilização. |
| `data/analytical/` | População analítica utilizada nas análises e na modelagem supervisionada. |

A população analítica deve ser definida antes da modelagem final, documentando período, inclusões, exclusões, tratamento de ausentes, variável-alvo e variáveis permitidas.

---

## 🔄 Fluxo do projeto

```text
API de Dados Abertos
        ↓
Extração
        ↓
data/raw/
        ↓
Processamento / Limpeza
        ↓
data/processed/
        ↓
População Analítica
        ↓
Análise exploratória e não supervisionada
        ↓
Pipeline supervisionado
        ↓
Validação temporal
        ↓
Calibração e definição do threshold
        ↓
Validação final
        ↓
Resultados
```

A modelagem supervisionada utiliza o mesmo pipeline de transformação durante treinamento e inferência, evitando duplicação de lógica entre notebooks e código de produção experimental.

---

## 🧱 Estrutura do projeto

```text
Projeto_Integrador/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── analytical/
│
├── configs/
│   ├── base.yaml
│   └── supervised.yaml
│
├── logs/
├── models/
│
├── outputs/
│   ├── tables/
│   ├── figures/
│   └── predictions/
│
├── notebooks/
│   ├── 00_acesso_dados_parquet.ipynb
│   ├── 01_extracao.ipynb
│   └── C/
│       ├── C1_smoke_test.ipynb
│       ├── C2_pipeline_supervisionado.ipynb
│       ├── C3_baseline_logistica.ipynb
│       ├── C4_boosting.ipynb
│       ├── C5_calibracao_limiar.ipynb
│       └── C6_validacao_final.ipynb
│
├── src/
│   ├── data/
│   │   ├── extracao.py
│   │   └── ...
│   ├── models/
│   │   ├── pipeline.py
│   │   ├── baseline.py
│   │   ├── logistic.py
│   │   ├── boosting.py
│   │   └── calibration.py
│   ├── evaluation/
│   │   ├── temporal.py
│   │   ├── metrics.py
│   │   ├── calibration.py
│   │   └── errors.py
│   └── utils/
│       ├── config.py
│       ├── env.py
│       ├── storage.py
│       ├── logging.py
│       └── reproducibility.py
│
├── tests/
│   ├── test_smoke.py
│   ├── test_pipeline.py
│   ├── test_leakage.py
│   └── test_config.py
│
├── requirements.txt
├── README.md
└── .gitignore
```

### Principais diretórios

| Diretório | Finalidade |
|---|---|
| `data/` | Organização das diferentes camadas dos dados. |
| `configs/` | Configurações e parâmetros do projeto. |
| `logs/` | Registros das execuções. |
| `models/` | Modelos e artefatos treinados. |
| `outputs/tables/` | Métricas, comparações e tabelas dos experimentos. |
| `outputs/figures/` | Gráficos e visualizações. |
| `outputs/predictions/` | Predições produzidas pelos modelos. |
| `notebooks/` | Execução, exploração e documentação dos experimentos. |
| `src/` | Código reutilizável e definitivo do projeto. |
| `tests/` | Testes de funcionamento, configuração e prevenção de problemas. |

---

## 🧩 Organização do código

A lógica reutilizável deve permanecer em `src/`, enquanto os notebooks são utilizados para execução, experimentação, apresentação de resultados e documentação.

Exemplo:

```text
src/models/logistic.py
        ↓
Implementação da regressão logística
        ↓
notebooks/C/C3_baseline_logistica.ipynb
        ↓
Execução + resultados + documentação
```

Essa separação reduz a duplicação de código e facilita a reprodução dos experimentos.

---

## 🔬 Metodologia

### 1. Acesso e extração dos dados

O notebook `notebooks/00_acesso_dados_parquet.ipynb` valida o acesso à base Parquet, incluindo existência do arquivo, schema, colunas, quantidade de registros e funcionamento do armazenamento.

A extração pela API é implementada em `src/data/extracao.py` e documentada em `notebooks/01_extracao.ipynb`.

A rotina utiliza requisições paginadas e contempla:

- controle de paginação;
- tratamento de erros;
- novas tentativas de requisição;
- controle de tempo entre requisições;
- conversão dos resultados para `DataFrame`;
- armazenamento em CSV/Parquet.

### 2. Preparação e população analítica

A população analítica é construída a partir dos dados processados e envolve decisões sobre:

- período analisado;
- população incluída;
- exclusões;
- tratamento de dados ausentes;
- definição da variável-alvo (`target`);
- seleção das variáveis utilizadas na modelagem;
- prevenção de variáveis que possam causar vazamento de informação.

Após definida, a população analítica deve permanecer congelada para a etapa de modelagem supervisionada.

### 3. Análise exploratória

A análise exploratória busca compreender:

- estrutura e tipos das variáveis;
- valores ausentes e duplicidades;
- distribuições;
- relações entre atributos;
- comportamento temporal;
- inconsistências;
- padrões e anomalias.

### 4. Aprendizado não supervisionado

São avaliadas técnicas exploratórias de agrupamento, incluindo:

- DBSCAN;
- Hierarchical Clustering / HCA;
- análise de agrupamentos;
- avaliação de estabilidade;
- análise de ruído;
- comparação de métricas;
- análise de dendrogramas.

Essas análises têm caráter exploratório e não substituem a avaliação supervisionada.

### 5. Pipeline supervisionado

A modelagem supervisionada é construída em um pipeline reproduzível, concentrando as transformações necessárias para que o mesmo processamento seja aplicado durante treinamento e inferência.

Implementação principal:

```text
src/models/pipeline.py
```

O pipeline contempla preparação e transformação das variáveis, separação temporal, prevenção de leakage, treinamento e avaliação.

### 6. Validação temporal

A avaliação respeita a ordem temporal dos registros em vez de depender exclusivamente de uma divisão aleatória.

```text
PASSADO
   ↓
Treinamento
   ↓
Desenvolvimento
   ↓
Holdout temporal
   ↓
Futuro / período não utilizado
```

Essa estratégia busca representar um cenário no qual dados históricos são utilizados para realizar previsões sobre períodos posteriores.

A implementação encontra-se em `src/evaluation/temporal.py`.

### 7. Baseline e regressão logística

São estabelecidos modelos de referência para comparação com modelos mais complexos:

1. baseline;
2. regressão logística.

Notebook: `notebooks/C/C3_baseline_logistica.ipynb`

### 8. Boosting

Após os modelos de referência, é avaliado um modelo baseado em boosting.

Notebook: `notebooks/C/C4_boosting.ipynb`

A busca de hiperparâmetros deve ser limitada aos dados de desenvolvimento, sem utilização do holdout final para seleção do modelo.

### 9. Calibração e definição do limiar

Além da capacidade discriminativa, o projeto avalia a qualidade das probabilidades produzidas pelo modelo.

São consideradas:

- curva de calibração;
- Brier Score;
- comparação entre probabilidades previstas e observadas;
- avaliação de diferentes limiares de classificação.

Notebook: `notebooks/C/C5_calibracao_limiar.ipynb`

O threshold é definido com dados de desenvolvimento e deve ser congelado antes da utilização do holdout final.

### 10. Validação final

A validação final utiliza um holdout temporal que não participa das decisões de modelagem.

Antes da abertura do holdout devem estar definidos:

- modelo;
- hiperparâmetros;
- pipeline;
- transformações;
- calibração;
- threshold;
- métricas;
- critérios de avaliação.

Notebook: `notebooks/C/C6_validacao_final.ipynb`

```text
Dados de desenvolvimento
        ↓
Treinamento / seleção / calibração / threshold
        ↓
CONFIGURAÇÃO CONGELADA
        ↓
HOLDOUT FINAL
        ↓
MÉTRICAS FINAIS
```

O holdout não deve ser utilizado para ajustar novamente o modelo.

---

## 📏 Métricas

A escolha definitiva das métricas depende da variável-alvo e das características da tarefa supervisionada.

Entre as métricas consideradas estão:

- ROC-AUC;
- PR-AUC;
- Brier Score;
- Precision;
- Recall / Sensibilidade;
- Specificity / Especificidade;
- F1-Score;
- matriz de confusão;
- curvas de calibração.

O conjunto de métricas permite avaliar discriminação, qualidade das probabilidades e diferentes tipos de erro.

---

## ⚠️ Prevenção de Data Leakage

Informações que não estariam disponíveis no momento da previsão não devem ser utilizadas como variáveis de entrada.

Também devem ser evitadas situações em que informações futuras sejam utilizadas durante o treinamento ou a seleção do modelo.

Os testes relacionados a leakage estão em:

```text
tests/test_leakage.py
```

O holdout final permanece separado durante todas as etapas de desenvolvimento.

---

## 🧪 Testes

Os testes buscam detectar problemas antes dos experimentos principais:

```text
tests/
├── test_smoke.py
├── test_pipeline.py
├── test_leakage.py
└── test_config.py
```

São verificados aspectos como funcionamento básico, carregamento de módulos, configuração, construção do pipeline e prevenção de leakage.

---

## 📝 Notebooks da modelagem supervisionada

| Notebook | Finalidade |
|---|---|
| `C1_smoke_test.ipynb` | Verifica o ambiente e os principais componentes do projeto. |
| `C2_pipeline_supervisionado.ipynb` | Constrói e valida o pipeline supervisionado. |
| `C3_baseline_logistica.ipynb` | Estabelece modelos de referência e avalia a regressão logística. |
| `C4_boosting.ipynb` | Avalia boosting e realiza busca limitada de hiperparâmetros. |
| `C5_calibracao_limiar.ipynb` | Avalia a calibração e define o threshold com dados de desenvolvimento. |
| `C6_validacao_final.ipynb` | Realiza a avaliação final no holdout temporal. |

---

## 🔁 Reprodutibilidade

O projeto utiliza mecanismos para facilitar a reprodução dos experimentos:

- ambiente virtual Python;
- `requirements.txt`;
- configurações centralizadas;
- caminhos relativos;
- controle de seeds;
- registro de parâmetros e versões;
- logs de execução;
- organização padronizada dos dados;
- testes automatizados.

Os utilitários relacionados estão em `src/utils/`, especialmente:

```text
config.py

env.py

storage.py

logging.py

reproducibility.py
```

---

## ⚙️ Configuração do ambiente

Recomenda-se utilizar um ambiente virtual.

### Windows

Criar o ambiente:

```powershell
python -m venv .venv
```

Ativar:

```powershell
.venv\Scripts\activate
```

Atualizar o pip:

```powershell
python -m pip install --upgrade pip
```

Instalar as dependências:

```powershell
pip install -r requirements.txt
```

---

## ▶️ Execução

A execução deve seguir a ordem lógica do projeto:

```text
00_acesso_dados_parquet.ipynb
        ↓
01_extracao.ipynb
        ↓
Preparação / população analítica
        ↓
Análise exploratória e não supervisionada
        ↓
C1_smoke_test.ipynb
        ↓
C2_pipeline_supervisionado.ipynb
        ↓
C3_baseline_logistica.ipynb
        ↓
C4_boosting.ipynb
        ↓
C5_calibracao_limiar.ipynb
        ↓
C6_validacao_final.ipynb
```

As etapas de preparação, exploração e análise não supervisionada são definidas pelos notebooks correspondentes às atividades anteriores do projeto.

---

## 📦 Dependências

Principais tecnologias utilizadas:

- Python;
- Jupyter / Jupyter Notebook;
- Pandas;
- NumPy;
- PyArrow;
- Requests;
- Scikit-learn;
- Matplotlib;
- Seaborn;
- python-dotenv;
- PyYAML.

As versões efetivamente utilizadas devem ser registradas em `requirements.txt`.

---

## 📈 Resultados

Os resultados dos experimentos são organizados em:

```text
outputs/
├── tables/
├── figures/
└── predictions/
```

- `tables/`: métricas, comparações entre modelos e resultados de validação;
- `figures/`: gráficos, curvas de calibração, matrizes de confusão e demais visualizações;
- `predictions/`: previsões produzidas pelos modelos.

Os resultados finais serão documentados após a conclusão da modelagem e da validação.

---

## 🧠 Organização metodológica

O projeto é dividido em responsabilidades relacionadas à preparação dos dados, análise exploratória e não supervisionada, e modelagem supervisionada.

A etapa de modelagem supervisionada contempla:

- reprodutibilidade;
- pipeline supervisionado;
- baseline;
- regressão logística;
- boosting;
- calibração;
- definição de threshold;
- validação temporal;
- análise de erros;
- validação final;
- integração dos resultados.

---

## ⚠️ Considerações e limitações

Os dados provenientes de uma fonte pública podem apresentar:

- valores ausentes;
- inconsistências;
- alterações na estrutura;
- registros duplicados;
- diferenças de preenchimento;
- mudanças ao longo do período;
- limitações de representatividade.

Os modelos possuem **finalidade acadêmica e educacional**. Os resultados não devem ser interpretados como ferramenta de diagnóstico médico, decisão clínica ou substituição de avaliação profissional.

As conclusões devem considerar as limitações dos dados, das variáveis disponíveis, da população analítica e da metodologia utilizada.

---

## 🔒 Dados e arquivos grandes

Devido ao tamanho da base SRAG, arquivos de dados e artefatos grandes não necessariamente devem ser versionados diretamente no Git.

Quando aplicável, devem ser utilizados mecanismos de armazenamento externo ou arquivos disponibilizados separadamente.

O Git deve manter principalmente:

- código;
- notebooks;
- configurações;
- testes;
- documentação;
- arquivos de dependências.

---

## 🚧 Status do projeto

### Etapas estruturadas

- [x] Estrutura inicial do projeto
- [x] Acesso aos dados Parquet
- [x] Validação da leitura da base SRAG
- [x] Rotina de armazenamento dos dados
- [x] Estrutura de extração
- [x] Organização da arquitetura `src/`
- [x] Estrutura de configurações
- [x] Planejamento da reprodutibilidade
- [x] Estrutura da modelagem supervisionada
- [x] Definição dos notebooks da modelagem supervisionada

### Em desenvolvimento

- [ ] Consolidação da população analítica
- [ ] Finalização do pipeline supervisionado
- [ ] Baseline
- [ ] Regressão logística
- [ ] Boosting
- [ ] Calibração
- [ ] Definição do threshold
- [ ] Validação temporal final
- [ ] Análise de erros
- [ ] Resultados finais
- [ ] Documentação final

---

## 👥 Autores

- **Ivan Schincariol Oliveira** — [LinkedIn](https://www.linkedin.com/in/ivan-s-oliveira-3608a92aa/)
- **Eduardo Hudson de Almeida Leite** — [LinkedIn](https://www.linkedin.com/in/eduardo-hudson-de-almeida-leite-71ab5a7b/)
- **Pedro Henrique Silva dos Santos** — [LinkedIn](https://www.linkedin.com/in/pedro-h-s-santos/)
- **Mateus da Silva Oliveira** — [LinkedIn](https://www.linkedin.com/in/mateusso)

---

## 🎓 Contexto acadêmico

**Projeto Integrador I — Pós-Graduação em Inteligência Artificial.**

O projeto aplica, de forma prática, conceitos de Engenharia de Dados, Machine Learning, aprendizado supervisionado e não supervisionado, engenharia de atributos, validação e avaliação de modelos, reprodutibilidade e análise de dados.
