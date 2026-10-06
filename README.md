# Projeto Integrador — Machine Learning

Projeto desenvolvido como parte do **Projeto Integrador I** da Pós-Graduação em Inteligência Artificial.

## 📌 Sobre o projeto

Este projeto tem como objetivo aplicar técnicas de **Machine Learning** sobre dados reais do **Síndrome Respiratória Aguda Grave (SRAG)**, utilizando a base de dados disponibilizada pelo Ministério da Saúde.

O projeto contempla as etapas de um fluxo de Machine Learning, desde a **obtenção e preparação dos dados**, passando pela **Análise Exploratória de Dados (EDA)** e engenharia de atributos, até o **treinamento e avaliação de modelos de Machine Learning**.

> **Status:** 🚧 Projeto em desenvolvimento.

## 🎯 Objetivo

Investigar a aplicação de técnicas de Machine Learning sobre os dados de SRAG, buscando identificar padrões nos registros e avaliar a capacidade de modelos preditivos em relação ao problema definido pelo projeto.

O objetivo específico do modelo será definido e documentado ao longo do desenvolvimento do projeto.

## 📊 Dados

Os dados utilizados são provenientes da base pública **SRAG 2019–2026**, disponibilizada pelo Ministério da Saúde por meio da API de Dados Abertos.

**Fonte:** [Portal de Dados Abertos do Ministério da Saúde](https://apidadosabertos.saude.gov.br/)

A coleta dos dados é realizada programaticamente em Python e os dados utilizados no projeto são organizados em diferentes etapas de processamento.

### Fluxo dos dados

```text
API do Ministério da Saúde
          ↓
     Extração
          ↓
      data/raw
          ↓
      Limpeza
          ↓
   data/processed
          ↓
 Feature Engineering
          ↓
    data/treino
          ↓
   Machine Learning
          ↓
    Avaliação
```

## 🧠 Tecnologias e bibliotecas

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

## 📁 Estrutura do projeto

```text
Projeto_Integrador/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── treino/
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
│   ├── features/
│   ├── models/
│   └── utils/
│
├── models/
│
├── reports/
│   └── figuras/
│
├── requirements.txt
├── README.md
└── .gitignore
```

## 🔬 Etapas do projeto

### 1. Extração dos dados

Obtenção dos dados da base SRAG por meio da API do Ministério da Saúde.

### 2. Limpeza e preparação

Tratamento de valores ausentes, duplicidades, tipos de dados e variáveis inconsistentes.

### 3. Análise Exploratória de Dados

Investigação das principais características da base por meio de estatísticas descritivas e visualizações.

### 4. Engenharia de atributos

Seleção, transformação e criação de variáveis relevantes para o modelo.

### 5. Treinamento

Aplicação e comparação de diferentes algoritmos de Machine Learning.

### 6. Avaliação

Avaliação dos modelos utilizando métricas adequadas ao problema, como:

* Accuracy
* Precision
* Recall
* F1-Score
* Matriz de Confusão

As métricas utilizadas poderão ser ajustadas de acordo com o problema e a distribuição das classes.

## 📓 Notebooks

Os notebooks são utilizados para **exploração, experimentação e documentação do processo de desenvolvimento**.

O código reutilizável e definitivo do projeto é organizado na pasta `src/`.

## ⚙️ Instalação

Clone o repositório:

```bash
git clone https://github.com/SEU-USUARIO/Projeto_Integrador.git
```

Entre na pasta:

```bash
cd Projeto_Integrador
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

## ▶️ Execução

O projeto pode ser executado seguindo a sequência dos notebooks disponíveis na pasta `notebooks/`.

Os scripts Python responsáveis pelas etapas reutilizáveis do projeto encontram-se na pasta `src/`.

## 📈 Resultados

Os resultados, gráficos e demais análises produzidos durante o desenvolvimento serão documentados nesta seção conforme o projeto avançar.

## ⚠️ Observações

Os dados utilizados são provenientes de uma fonte pública e podem apresentar alterações, atualizações, valores ausentes ou inconsistências próprias de bases de dados reais.

Os resultados obtidos pelo modelo devem ser interpretados considerando as limitações dos dados, das variáveis utilizadas e da metodologia empregada.

Este projeto possui finalidade **acadêmica e educacional**.

## 👥 Autores

* [Ivan Schincariol Oliveira](https://www.linkedin.com/in/ivan-s-oliveira-3608a92aa/)
* [Eduardo Hudson de Almeida Leite](https://www.linkedin.com/in/eduardo-hudson-de-almeida-leite-71ab5a7b/)
* [Pedro Henrique Silva dos Santos](https://www.linkedin.com/in/pedro-h-s-santos/)
* [Mateus da Silva Oliveira](https://www.linkedin.com/in/mateusso)