# Projeto Integrador — SRAG Machine Learning

Projeto desenvolvido como parte do **Projeto Integrador I** da Pós-Graduação em Inteligência Artificial.

O projeto tem como objetivo aplicar técnicas de **Machine Learning** sobre dados reais da base de **Síndrome Respiratória Aguda Grave (SRAG)**, disponibilizada pelo Ministério da Saúde.

> 🚧 **Status:** Projeto em desenvolvimento.

---

## 🎯 Objetivo

O projeto busca investigar a aplicação de técnicas de Machine Learning sobre dados de SRAG, realizando um fluxo completo de desenvolvimento de um modelo:

**extração → limpeza → análise exploratória → engenharia de atributos → treinamento → avaliação**

O problema específico de Machine Learning e a variável-alvo (`target`) serão definidos e documentados durante o desenvolvimento do projeto.

---

## 📊 Dados

Os dados utilizados são provenientes da base pública **SRAG 2019–2026**, disponibilizada pelo Ministério da Saúde por meio da API de Dados Abertos.

**Fonte:** [Portal de Dados Abertos do Ministério da Saúde](https://apidadosabertos.saude.gov.br/)

Os dados são coletados por meio de uma rotina desenvolvida em Python e passam por diferentes etapas de preparação antes de serem utilizados nos modelos.

### Fluxo dos dados

```text
API do Ministério da Saúde
          │
          ▼
     Extração
          │
          ▼
      data/raw/
          │
          ▼
       Limpeza
          │
          ▼
   data/processed/
          │
          ▼
Feature Engineering
          │
          ▼
     data/treino/
          │
          ▼
     Treinamento
          │
          ▼
      Avaliação
          │
          ▼
   Modelo final
```

---

## 🧠 Tecnologias

O projeto utiliza principalmente:

* Python
* JupyterLab
* Pandas
* NumPy
* Requests
* Matplotlib
* Seaborn
* Scikit-learn
* python-dotenv

---

## 📁 Estrutura do projeto

```text
srag-machine-learning/
│
├── data/
│   ├── raw/
│   │   └── srag_amostra.csv
│   │
│   ├── processed/
│   │   └── srag_limpo.csv
│   │
│   └── treino/
│       ├── X_train.csv
│       ├── X_test.csv
│       ├── y_train.csv
│       └── y_test.csv
│
├── notebooks/
│   ├── 01_extracao.ipynb
│   ├── 02_analise_exploratoria.ipynb
│   ├── 03_preprocessamento.ipynb
│   ├── 04_feature_engineering.ipynb
│   ├── 05_treinamento.ipynb
│   └── 06_avaliacao.ipynb
│
├── src/
│   ├── data/
│   │   ├── extracao.py
│   │   └── preprocessamento.py
│   │
│   ├── features/
│   │   └── engenharia_features.py
│   │
│   ├── models/
│   │   ├── treinamento.py
│   │   └── avaliacao.py
│   │
│   └── utils/
│       └── config.py
│
├── models/
│   └── modelo_final.pkl
│
├── reports/
│   └── figuras/
│
├── requirements.txt
├── README.md
└── .gitignore
```

### 📂 Descrição das pastas

| Pasta             | Finalidade                                |
| ----------------- | ----------------------------------------- |
| `data/raw/`       | Dados obtidos diretamente da fonte        |
| `data/processed/` | Dados após limpeza e tratamento           |
| `data/treino/`    | Dados separados para treinamento e teste  |
| `notebooks/`      | Exploração, experimentação e documentação |
| `src/data/`       | Extração e preparação dos dados           |
| `src/features/`   | Engenharia e transformação de atributos   |
| `src/models/`     | Treinamento e avaliação dos modelos       |
| `src/utils/`      | Configurações e funções auxiliares        |
| `models/`         | Modelos treinados                         |
| `reports/`        | Gráficos e resultados das análises        |

---

## 🔬 Etapas do projeto

### 1. Extração dos dados

Os dados são obtidos por meio da API de Dados Abertos do Ministério da Saúde.

O código responsável pela extração está em:

```text
src/data/extracao.py
```

O processo é explorado e documentado em:

```text
notebooks/01_extracao.ipynb
```

---

### 2. Análise Exploratória

Nesta etapa são investigados:

* estrutura dos dados;
* tipos das variáveis;
* valores ausentes;
* duplicidades;
* distribuição das variáveis;
* relações entre atributos;
* distribuição temporal dos registros;
* possíveis padrões e anomalias.

Notebook:

```text
notebooks/02_analise_exploratoria.ipynb
```

---

### 3. Pré-processamento

Nesta etapa são realizados os tratamentos necessários para preparar os dados para Machine Learning.

Exemplos:

* tratamento de valores ausentes;
* conversão de tipos;
* remoção de duplicidades;
* tratamento de variáveis categóricas;
* tratamento de datas;
* preparação das variáveis.

Código principal:

```text
src/data/preprocessamento.py
```

Notebook:

```text
notebooks/03_preprocessamento.ipynb
```

---

### 4. Engenharia de atributos

Nesta etapa são criadas e selecionadas variáveis que podem contribuir para o desempenho dos modelos.

Código:

```text
src/features/engenharia_features.py
```

Notebook:

```text
notebooks/04_feature_engineering.ipynb
```

---

### 5. Treinamento

Os dados são separados em conjuntos de treinamento e teste:

```text
X_train
X_test
y_train
y_test
```

Diferentes algoritmos de Machine Learning poderão ser avaliados e comparados.

Código:

```text
src/models/treinamento.py
```

Notebook:

```text
notebooks/05_treinamento.ipynb
```

---

### 6. Avaliação

Os modelos são avaliados utilizando métricas adequadas ao problema.

Entre as métricas que poderão ser utilizadas:

* Accuracy
* Precision
* Recall
* F1-Score
* Matriz de Confusão
* ROC-AUC

A escolha definitiva das métricas será feita de acordo com a variável-alvo e as características do problema.

Código:

```text
src/models/avaliacao.py
```

Notebook:

```text
notebooks/06_avaliacao.ipynb
```

---

## 📈 Resultados

Os resultados dos experimentos, métricas, gráficos e comparações entre modelos serão documentados nesta seção conforme o desenvolvimento do projeto.

Os gráficos gerados durante as análises poderão ser armazenados em:

```text
reports/figuras/
```

---

## ⚙️ Instalação

Clone o repositório:

```bash
git clone https://github.com/SEU-USUARIO/srag-machine-learning.git
```

Entre na pasta:

```bash
cd srag-machine-learning
```

Crie um ambiente virtual:

```bash
python -m venv .venv
```

Ative o ambiente virtual no Windows:

```bash
.venv\Scripts\activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

---

## ▶️ Execução

Os notebooks podem ser executados seguindo a ordem:

```text
01_extracao
      ↓
02_analise_exploratoria
      ↓
03_preprocessamento
      ↓
04_feature_engineering
      ↓
05_treinamento
      ↓
06_avaliacao
```

O código reutilizável e definitivo das etapas encontra-se na pasta `src/`.

---

## ⚠️ Considerações

Os dados utilizados são provenientes de uma fonte pública e podem apresentar valores ausentes, inconsistências, alterações e outras características comuns a bases de dados reais.

Os resultados dos modelos devem ser interpretados considerando as limitações dos dados, das variáveis utilizadas e da metodologia empregada.

Este projeto possui finalidade **acadêmica e educacional**.

---

## 👥 Autores

* [Ivan Schincariol Oliveira](https://www.linkedin.com/in/ivan-s-oliveira-3608a92aa/)
* [Eduardo Hudson de Almeida Leite](https://www.linkedin.com/in/eduardo-hudson-de-almeida-leite-71ab5a7b/)
* [Pedro Henrique Silva dos Santos](https://www.linkedin.com/in/pedro-h-s-santos/)
* [Mateus da Silva Oliveira](https://www.linkedin.com/in/mateusso)