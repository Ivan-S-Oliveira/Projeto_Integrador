# Entrega, resultados oficiais e reprodução segura

Este é o documento canônico da entrega. Ele consolida a identidade do run oficial,
a governança do holdout, as instruções seguras de reprodução e a distinção entre
o estado científico apresentado e a manutenção técnica posterior.

## Governança do holdout

Antes da abertura oficial, o notebook 11 foi executado em modo ensaio sobre uma
coorte derivada da validação. O ensaio validou a cadeia de carregamento,
reconstrução do modelo, calibração, aplicação do limiar, inferência, bootstrap,
subgrupos e persistência sem carregar `test_ref` ou `test_pandemic` e sem alterar o G9.

Depois do congelamento do modelo, das variáveis, do calibrador e do limiar, o
holdout foi aberto uma única vez para o run oficial.

- Commit oficial: `52970fc`
- Abertura oficial em UTC: `2026-11-05T21:15:27Z`
- Dataset supervisionado: SHA-256 iniciado por `763a136e`
- Limiar congelado: `0.1178`

Após o run oficial, somente os notebooks 01–10 foram reexecutados por motivos
técnicos de segurança de execução, acessibilidade, remoção de código morto e
preservação dos outputs. O notebook 11 permaneceu congelado. Essas reexecuções
não alteraram modelo, variáveis, calibrador, limiar ou resultados oficiais reportados.

O contador legado de execuções do notebook não deve ser interpretado como
contador de aberturas do holdout. O estado canônico distingue:

- ensaios do notebook 11;
- execuções oficiais do notebook 11;
- aberturas reais do holdout.


## Resultados oficiais apresentados

Os resultados da banca pertencem ao primeiro run oficial do holdout.

- Teste A: 119245 registros
- PR-AUC: 0.3690
- ROC-AUC: 0.8686
- Brier: 0.0628

## Reprodução segura

### Cadeia de desenvolvimento

Os notebooks 01–10 podem ser executados na ordem para reproduzir a cadeia de
desenvolvimento. Essa execução não deve carregar `test_ref` ou `test_pandemic`.

### Ensaio do notebook 11

O notebook 11 deve usar o modo ensaio para testar a cadeia final sobre dados de
validação. O ensaio deve registrar `ensaio = true`, `test_opened = false`, manter
o G9 inalterado e não carregar as partições de teste.

### Run oficial

O holdout não deve ser reexecutado apenas para restaurar outputs. Para a entrega,
devem ser usados o manifesto, as previsões e as tabelas congeladas do primeiro
run oficial.

### Pós-teste

O notebook 12 deve consumir as previsões oficiais congeladas, sem reabrir o
holdout.

### Reprodução posterior solicitada pela banca

Se uma nova execução do holdout for explicitamente exigida, ela deve receber
identificador próprio, justificativa, data, commit e hashes. Essa execução será
classificada como reprodução técnica pós-holdout, não substituirá o run oficial
e não autorizará novas decisões analíticas.

## Unidade observacional e partição

- A unidade observacional é a notificação hospitalar elegível, usada como
  aproximação de episódio hospitalar; não representa necessariamente uma pessoa
  única.
- O `group_id` usa o número de notificação normalizado, com fallback pelo
  identificador do registro.
- A partição tenta estratificar por ano, desfecho e região, com fallback
  pré-definido para ano e desfecho em estratos pequenos.

## Limites que acompanham os resultados

- A sensibilidade de aproximadamente 81% é agregada e não vale para todos os
  subgrupos.
- O limiar global não é adequado para triagem pediátrica.
- O período pandêmico apresenta drift relevante de discriminação e calibração.
- Sigmoid foi mantida por parcimônia após empate prático com isotonic no boosting;
  o modelo base já apresentava boa calibração.
- O projeto é retrospectivo, acadêmico e não está validado para uso clínico.

## Documentos entregáveis

Na versão pública da entrega, a pasta `docs/` mantém somente
`docs/dicionario_variaveis.md`. Este documento, localizado na raiz, é a fonte
canônica para resultados oficiais, governança e reprodução segura.

Materiais históricos, painéis internos, Bases de Conhecimento, status de tarefas,
compilações com identificadores e documentos de trabalho não integram a entrega.
