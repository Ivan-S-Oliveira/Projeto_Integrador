# Status do projeto SRAG

> Arquivo mantido automaticamente pelo **Painel de Pendências** (pasta local `.srag-status-local`).
> Não edite à mão: use o painel, ou escreva `[done:#ID]`, `[progress:#ID]`, `[reopen:#ID]` ou `tarefa ID` nas mensagens de commit.
> O texto das pendências (títulos, seções, responsáveis, datas) fica em `PROJECT_STATUS_TEXT.md` — esse sim pode ser editado à mão.

> Atualizado em 2026-10-25T00:40:12Z.

- Concluídas: **6**
- Resolvidas pendentes de validação: **5**
- Precisam revisão: **0**
- Em andamento: **5**
- Abertas: **114**

## Precisam revisão (a auditoria encontrou problema) (0)

_Nenhum item._

## Detectadas como resolvidas — confirmar no painel (5)

- 🟪 **#123** Ler o artefato por partição, para o teste nunca chegar à memória por engano — RESOLVIDA — PENDENTE DE VALIDAÇÃO · Pessoa C (dona; revisão cruzada sem edição concorrente) · Concluído
- 🟪 **#16** Nada no código impede abrir o teste antes do G9 — RESOLVIDA — PENDENTE DE VALIDAÇÃO · Pessoa C (dona; revisão cruzada sem edição concorrente) · Concluído
- 🟪 **#61** pyproject aceita scikit-learn 1.4, mas o código precisa de 1.8+ — RESOLVIDA — PENDENTE DE VALIDAÇÃO · Pessoa C (dona; revisão cruzada sem edição concorrente) · Concluído
- 🟪 **#63** Dependências sem versão e espalhadas em dois arquivos — RESOLVIDA — PENDENTE DE VALIDAÇÃO · Pessoa C (dona; revisão cruzada sem edição concorrente) · Concluído
- 🟪 **#101** Remover o notebook duplicado A3b (cópia antiga do A_09) — RESOLVIDA — PENDENTE DE VALIDAÇÃO · Pessoa A (dona; revisão cruzada sem edição concorrente) · Concluído

## Em andamento (5)

- 🟦 **#102** Alinhar todos os YAMLs ao treino 2019/2023–2025 e às duas janelas de teste — EM ANDAMENTO · Pessoa A (decisoes.yaml) + Pessoa C (artefato) · 26/10
- 🟦 **#70** Dicionário de variáveis desatualizado e com arquivo fantasma — EM ANDAMENTO · Pessoa A (dona; revisão cruzada sem edição concorrente) · 28/10
- 🟦 **#14** A variável SRAG_PARQUET_URL não tem efeito — EM ANDAMENTO · Pessoa C (dona; revisão cruzada sem edição concorrente) · Concluído
- 🟦 **#121** montar_features faz cópia completa da coorte e devolve tipos pesados — EM ANDAMENTO · Pessoa C (dona; revisão cruzada sem edição concorrente) · Concluído
- 🟦 **#30** Salvar a coorte definitiva com o nome errado a carregaria como provisória — EM ANDAMENTO · Pessoa C (dona; revisão cruzada sem edição concorrente) · Concluído

## Abertas (114)

- ⬜ **#72** Quem é responsável pelos próximos passos (passagem de bastão de 24/10) — ABERTA · Pessoa B (registra e comunica) + Equipe · 24/10
- ⬜ **#10** Regra definitiva para números de notificação repetidos — ABERTA · Pessoa A (regra, função e testes) · revisão: Pessoa C · 25/10
- ⬜ **#127** Função de comparação pareada com bootstrap por grupo — ABERTA · Pessoa B até 24/10 → Pessoa C a partir de 26/10 · 25/10
- ⬜ **#131** Levar para o src o artefato de seis blocos que o B_07 já gera (group_id, região, partição, leitura protegida) — ABERTA · Pessoa C (dona; revisão cruzada sem edição concorrente) · 25/10
- ⬜ **#132** Adaptar a cadeia C_11–C_16 aos seis blocos (train_ref, val_tune, val_cal, val_meas) — ABERTA · Pessoa C (dona; revisão cruzada sem edição concorrente) · 26/10
- ⬜ **#135** Testes das invariantes do protocolo no artefato v3 (§28.4) — ABERTA · Pessoa A (dona; revisão cruzada sem edição concorrente) · 26/10
- ⬜ **#1** Rodar o ajuste fino e preencher os hiperparâmetros no YAML — ABERTA · Pessoa C (dona; revisão cruzada sem edição concorrente) · 27/10
- ⬜ **#5** Decidir se o peso das classes fica, já que ele infla as probabilidades — ABERTA · Pessoa C (dona; revisão cruzada sem edição concorrente) · 27/10
- ⬜ **#50** Três sintomas vazios em 2019: estudar o "marcador de ano" e decidir se ficam no modelo — ABERTA · Pessoa A (tabela e verificação) + Pessoa C (linha na ablação) · 27/10
- ⬜ **#51** As tabelas de óbito do B_06 usaram também os casos do teste — ABERTA · Pessoa A · 27/10
- ⬜ **#54** Rodar as sensibilidades de gravidade, contexto e "qualquer óbito" — ABERTA · Pessoa C (execução) + Pessoa A (relatório) · 27/10
- ⬜ **#78** Aprovar o G6 para liberar o ajuste fino (busca de hiperparâmetros) — ABERTA · Pessoa C (aprova) + Pessoa A (registra) · 27/10
- ⬜ **#97** Fechar o "assunto da entrega do professor" — ABERTA · Pessoa A · 27/10
- ⬜ **#79** Aprovar o G7: escolher o método de calibração (proposta do C_15: sigmoid) — ABERTA · Pessoa C (dona; revisão cruzada sem edição concorrente) · 28/10
- ⬜ **#80** Aprovar o G8: escolher o limiar (proposta do C_15: 0,255 pelo F1) — ABERTA · Pessoa C (dona; revisão cruzada sem edição concorrente) · 28/10
- ⬜ **#91** Mostrar quais características pesam mais no risco (importância das variáveis) — ABERTA · Pessoa C (tabelas) + Pessoa B (interpretação em 31/10) · 28/10
- ⬜ **#81** Aprovar o G9 e liberar as duas janelas de teste uma única vez — ABERTA · Pessoa A (conduz o checklist) + Pessoa C (modelagem) + Equipe (aprova) · 29/10
- ⬜ **#2** Executar o C_16 uma única vez nas duas janelas de teste autorizadas — ABERTA · Pessoa C (dona; revisão cruzada sem edição concorrente) · 30/10
- ⬜ **#119** Executar o modelo congelado nas duas janelas de teste (E_02) — ABERTA · Pessoa C (execução) + Pessoa B (revisão ao voltar) · 30/10
- ⬜ **#136** Não supervisionado com one-hot dos quatro estados e normalização: nova representação e nova rodada de agrupamento — ABERTA · Pessoa B (dona) · contingência: Pessoa C · 31/10
- ⬜ **#137** Perfil estatístico dos grupos: qui-quadrado e ANOVA (e óbito × cura só no treino) — ABERTA · Pessoa A (dona; revisão cruzada sem edição concorrente) · 31/10
- ⬜ **#133** Relatório final: esqueleto, seções e rastreabilidade de cada número — ABERTA · Pessoa A (dona) + Pessoa B (EDA e perfis) + Pessoa C (conferência técnica) · 01/11
- ⬜ **#3** Garantir que a busca de hiperparâmetros termine a tempo — ABERTA · Pessoa C (dona; revisão cruzada sem edição concorrente) · Concluído
- ⬜ **#4** O boosting do código central não é o mesmo do piloto — ABERTA · C · Concluído
- ⬜ **#7** Artefato supervisionado com colunas de auditoria (sg_uf, vacina, saturação…) — ABERTA · B · Concluído
- ⬜ **#8** Partição estratificada por ano × desfecho — ABERTA · B · Concluído
- ⬜ **#44** Coorte definitiva inicial: congelar a seleção de features da coorte provisória — ABERTA · A (validação técnica: C) · Concluído
- ⬜ **#77** Aprovar o G1 com a seleção de features da coorte provisória congelada — ABERTA · Pessoa A (dona; revisão cruzada sem edição concorrente) · Concluído
- ⬜ **#85** Períodos de treino e teste definidos — ABERTA · Equipe (conduz: A) · Concluído
- ⬜ **#86** Levar a partição por hash do notebook para src/data/split.py — ABERTA · Pessoa C (dona; revisão cruzada sem edição concorrente) · Concluído
- ⬜ **#92** Repositório local sincronizado com o GitHub — ABERTA · B · Concluído
- ⬜ **#95** 24/10: validar com os professores somente três pontos científicos, sem bloquear a implementação — ABERTA · Pessoa B (prepara e registra) + Equipe · Concluído
- ⬜ **#113** O 01_extracao lia o Parquet inteiro (processo de ~13 GB) — ABERTA · B · Concluído
- ⬜ **#118** Criar a partição-mestre: treino 2019/2023–2025 e duas janelas de teste — ABERTA · Pessoa C (dona; revisão cruzada sem edição concorrente) · Concluído
- ⬜ **#9** Saturação, desconforto respiratório e vacina: cada documento diz uma coisa — ABERTA · Pessoa A (dona; revisão cruzada sem edição concorrente) · 25/10
- ⬜ **#73** decisoes.md parado em 10/10 — ABERTA · Pessoa A (dona; revisão cruzada sem edição concorrente) · 25/10
- ⬜ **#15** Pré-processador e manifesto podem usar listas de variáveis diferentes — ABERTA · Pessoa C (antes: Pessoa A) · 26/10
- ⬜ **#26** O manifesto nunca registra que o teste foi aberto — ABERTA · Pessoa A (função e teste) · Pessoa C (chamada no C_16) · 28/10
- ⬜ **#56** Mostrar por que a data de internação é a âncora, e quem ficou de fora — ABERTA · Pessoa A (antes: Pessoa B) · 28/10
- ⬜ **#55** Desempenho e erros por ano, idade, sexo e UF — ABERTA · Pessoa B (subgrupos e calibração) + Pessoa A (falsos negativos e figura) · 31/10
- ⬜ **#110** Geografia como separação da análise: ponto de corte por região e equidade (sem região como variável) — ABERTA · Pessoa C (execução) + Pessoa B (interpretação em 31/10) · 31/10
- ⬜ **#112** Atualizar a revisão bibliográfica com busca científica dirigida — ABERTA · Pessoa B (busca e matriz) · conferência de citações: Pessoa A · 31/10
- ⬜ **#71** Cuidados de redação no relatório — ABERTA · Pessoa A (dona; revisão cruzada sem edição concorrente) · 01/11
- ⬜ **#126** Execução limpa da cadeia final e pacote de reprodução — ABERTA · Pessoa A (reprodução independente e README) + Pessoa C (script) · 01/11
- ⬜ **#134** Apresentação e defesa: roteiro, slides e perguntas difíceis — ABERTA · Pessoa B (roteiro, slides e respostas) + Pessoa A (números) + Pessoa C (revisão técnica) · 02/11
- ⬜ **#12** Intervalos impossíveis entram no modelo como se fossem válidos — ABERTA · Pessoa A (dona; revisão cruzada sem edição concorrente) · Concluído
- ⬜ **#17** One-hot denso no código central: risco de faltar memória — ABERTA · C · Concluído
- ⬜ **#36** Faixas etárias e grafia do sexo diferentes entre EDA e modelo — ABERTA · Pessoa B (prepara) · execução: quem rodar o #51 · Concluído
- ⬜ **#62** pyproject.toml inválido — ABERTA · C · Concluído
- ⬜ **#64** Testes que faltam — ABERTA · Pessoa C (dona; revisão cruzada sem edição concorrente) · Concluído
- ⬜ **#82** Decidir o que fazer com intervalos impossíveis entre sintomas e internação — ABERTA · Pessoa A (dona; revisão cruzada sem edição concorrente) · Concluído
- ⬜ **#114** Precedência errada entre penalty do YAML e l1_ratio explícito na logística — ABERTA · C · Concluído
- ⬜ **#124** C_11 deve rodar com o pré-processamento esparso, sem materializar a validação inteira — ABERTA · Pessoa C (dona; revisão cruzada sem edição concorrente) · Concluído
- ⬜ **#22** Funções de avaliação com padrões diferentes do YAML — ABERTA · Pessoa B até 24/10 → Pessoa C · 25/10
- ⬜ **#23** A análise por subgrupo não calcula PR-AUC nem Brier — ABERTA · Pessoa B até 24/10 → Pessoa C · 25/10
- ⬜ **#59** Documentar 2026 como período parcial e exclusivamente exploratório — ABERTA · Pessoa A (dona; revisão cruzada sem edição concorrente) · 25/10
- ⬜ **#83** Definir o que a sensibilidade "com e sem indicadores de ausência" vai comparar — ABERTA · Pessoa A · revisão: Pessoa C · 25/10
- ⬜ **#27** O manifesto "mais recente" é escolhido pela data do arquivo — ABERTA · Pessoa C (antes: Pessoa B) · 26/10
- ⬜ **#29** Itens desatualizados ou sem uso no YAML — ABERTA · Pessoa A · revisão: Pessoa C · 26/10
- ⬜ **#58** A mesma validação escolhe hiperparâmetros e mede o resultado — ABERTA · Pessoa C (conferência no #132) · 26/10
- ⬜ **#84** Definir quais doses de vacina contam como anteriores à internação — ABERTA · Pessoa A (regra e derivação) · revisão: Pessoa C · 26/10
- ⬜ **#13** A sazonalidade é criada, mas não entra no modelo — ABERTA · Pessoa C (ablação) + Pessoa A (texto) · 27/10
- ⬜ **#87** Os notebooks A e o B_07 gravam no mesmo arquivo e um apaga o outro — ABERTA · Pessoa A · revisão: Pessoa C · 27/10
- ⬜ **#40** A construção da coorte provisória não gera os arquivos de rastreio esperados — ABERTA · Pessoa A (tabela) + Pessoa C (conferência) · 28/10
- ⬜ **#19** O YAML aceita chaves duplicadas em silêncio e fica em cache — ABERTA · Pessoa B (após 30/10) · alternativa: Pessoa C · 31/10
- ⬜ **#31** configs/paths.local.json aponta para uma pasta que ninguém usa — ABERTA · Pessoa A (dona; revisão cruzada sem edição concorrente) · 31/10
- ⬜ **#45** Vacina contra COVID marcada como "sim" antes de existir a vacina — ABERTA · Pessoa A (dona; revisão cruzada sem edição concorrente) · 31/10
- ⬜ **#46** 58 linhas repetem 29 números de notificação na base bruta — ABERTA · Pessoa A (dona; revisão cruzada sem edição concorrente) · 31/10
- ⬜ **#47** Idades, datas e anos impossíveis — ABERTA · Pessoa A (dona; revisão cruzada sem edição concorrente) · 31/10
- ⬜ **#52** Fichas de óbito têm as doenças prévias mais preenchidas — ABERTA · Pessoa B (dona; revisão cruzada sem edição concorrente) · 31/10
- ⬜ **#57** Associações "protetoras" que são efeito da idade — ABERTA · Pessoa B (dona; revisão cruzada sem edição concorrente) · 31/10
- ⬜ **#69** Plano v2 e orientação de TCC descrevem outro período e outra divisão — ABERTA · Pessoa A (dona; revisão cruzada sem edição concorrente) · 31/10
- ⬜ **#89** Revisar a conclusão do A_09 de que o sorteio é "otimista" — ABERTA · Pessoa A · 31/10
- ⬜ **#130** Regerar a referência do projeto ao fim de cada marco — ABERTA · Pessoa A (dona; revisão cruzada sem edição concorrente) · 02/11
- ⬜ **#21** A fábrica passa qualquer chave nova do YAML ao modelo — ABERTA · Pessoa C (dona; revisão cruzada sem edição concorrente) · Concluído
- ⬜ **#28** O YAML diz que o finalista é escolhido no fim do C_16, mas o C_16 exige antes — ABERTA · Pessoa C (antes: Pessoa A) · Concluído
- ⬜ **#60** Documentar que os clusters refletem idade e preenchimento, não perfis clínicos — ABERTA · Pessoa B (dona; revisão cruzada sem edição concorrente) · Concluído
- ⬜ **#65** test_temporal.py era cópia de test_leakage.py — ABERTA · C · Concluído
- ⬜ **#66** Teste lento roda junto com os rápidos — ABERTA · Pessoa C (dona; revisão cruzada sem edição concorrente) · Concluído
- ⬜ **#67** Rodar a suíte de testes depois das correções — ABERTA · C · Concluído
- ⬜ **#75** A descrição do G2 não batia com o que foi executado — ABERTA · A + C · Concluído
- ⬜ **#115** Mensagem de erro de SRAG_COHORT_KIND fora do contrato do teste — ABERTA · C · Concluído
- ⬜ **#116** Referência do projeto lenta e incompleta para outra IA (schema v6) — ABERTA · B · Concluído
- ⬜ **#122** read_srag sem opção de leitura compacta — ABERTA · Pessoa C (dona; revisão cruzada sem edição concorrente) · Concluído
- ⬜ **#11** A sensibilidade de indicadores de ausência não existe no código — ABERTA · Pessoa A (dona; revisão cruzada sem edição concorrente) · 25/10
- ⬜ **#111** Recorte só de São Paulo como entrega mínima — ABERTA · Equipe · 28/10
- ⬜ **#98** Notebooks B sem execução salva: a coorte provisória não é reprodutível pelo repositório — ABERTA · Pessoa A · 31/10
- ⬜ **#138** Opcional: "o mundo voltou?" Comparar 2019 com 2023–2025 — ABERTA · Pessoa C ou Pessoa B, se sobrar tempo · 01/11
- ⬜ **#53** Exploração opcional: validar o modelo congelado em 2026 — ABERTA · Pessoa B (dona; revisão cruzada sem edição concorrente) · 02/11
- ⬜ **#24** Curvas de calibração calculadas de dois jeitos — ABERTA · C · Após 03/11
- ⬜ **#25** A checagem de vazamento só olha o nome das colunas — ABERTA · C · Após 03/11
- ⬜ **#32** Textos antigos no código (dt_notific, nomes de gates) — ABERTA · C · Após 03/11
- ⬜ **#33** normalization.py está vazio — ABERTA · C · Concluído
- ⬜ **#34** O C_13 manda colar os hiperparâmetros em config.yaml (o certo é supervised.yaml) — ABERTA · Pessoa C (dona; revisão cruzada sem edição concorrente) · Concluído
- ⬜ **#35** Notebooks B recalculam com código próprio o que já existe em src/ — ABERTA · B · Após 03/11
- ⬜ **#37** O B_10 vai falhar de propósito quando a lista final de variáveis existir — ABERTA · Pessoa B (dona; revisão cruzada sem edição concorrente) · Concluído
- ⬜ **#38** Sobras no B_07: modo de teste sintético e imports sem uso — ABERTA · Pessoa B (dona; revisão cruzada sem edição concorrente) · Após 03/11
- ⬜ **#39** Matriz de transição do B_10 com status escritos à mão — ABERTA · B · Após 03/11
- ⬜ **#41** "provisoria", "provisorio" e "provisional" misturados — ABERTA · B + C · Após 03/11
- ⬜ **#42** Cada notebook encontra a pasta do projeto de um jeito — ABERTA · B + C · Após 03/11
- ⬜ **#43** Arquivos e listas que ninguém usa (preprocessor.joblib, lista de coortes no B_06) — ABERTA · B + C · Após 03/11
- ⬜ **#48** 41 fichas com povo tradicional preenchido sem a pessoa ser de povo tradicional — ABERTA · A · Após 03/11
- ⬜ **#49** Códigos a confirmar no dicionário — ABERTA · A · Após 03/11
- ⬜ **#68** Texto com codificação corrompida — ABERTA · C · Após 03/11
- ⬜ **#74** Faltam os números do clustering sem saturação e desconforto — ABERTA · B · Após 03/11
- ⬜ **#76** Nenhum notebook confere a versão do scikit-learn no início — ABERTA · Pessoa C (dona; revisão cruzada sem edição concorrente) · Concluído
- ⬜ **#88** A exportação da Pessoa A não tem duas variáveis que o modelo exige — ABERTA · A · Após 03/11
- ⬜ **#90** O A_09 sorteia linhas, e não grupos: a mesma ficha cai em duas partições — ABERTA · A · Após 03/11
- ⬜ **#93** O A_14 não tem a tabela de candidatos para comparar — ABERTA · A + C · Após 03/11
- ⬜ **#94** Alertas falsos no relatório automático do projeto — ABERTA · C · Após 03/11
- ⬜ **#96** Atualizar os guias e a base de conhecimento do agente — ABERTA · Pessoa B (dona; revisão cruzada sem edição concorrente) · Após 03/11
- ⬜ **#109** UMAP em sintomas e comorbidades: clustering no espaço latente e uma ablação supervisionada — ABERTA · Pessoa B (dona; revisão cruzada sem edição concorrente) · Após 03/11
- ⬜ **#128** 29 avisos de depreciação de timedelta sem unidade no NumPy — ABERTA · A · Após 03/11
- ⬜ **#129** Refatoração completa de performance de B_05, construtor e notebooks A — ABERTA · B · Após 03/11

## Concluídas (6)

- ✅ **#6** Corrigir a chamada de criar_alvo_binario no B_07 (vai quebrar na coorte definitiva) — CONCLUÍDA · Pessoa B (dona; revisão cruzada sem edição concorrente) · Concluído
- ✅ **#120** Registrar o protocolo fechado: treino não pandêmico e duas janelas de teste — CONCLUÍDA · Pessoa B (dona; revisão cruzada sem edição concorrente) · Concluído
- ✅ **#18** Carregar só algumas colunas do artefato pula a validação — CONCLUÍDA · Pessoa C (dona; revisão cruzada sem edição concorrente) · Concluído
- ✅ **#99** B_06: terminar a execução do início ao fim depois das correções de memória — CONCLUÍDA · Pessoa B (dona; revisão cruzada sem edição concorrente) · Concluído
- ✅ **#125** B_07: célula 19 com parêntese não fechado e duas células de teste sem execução — CONCLUÍDA · Pessoa B (dona; revisão cruzada sem edição concorrente) · Concluído
- ✅ **#20** Nome do finalista diferente no YAML e no código — CONCLUÍDA · Pessoa C (dona; revisão cruzada sem edição concorrente) · Concluído

<!-- PROJECT_STATUS_DATA
{"schema_version":3,"generated_at":"2026-10-25T00:40:12Z","scan":{"seen":[],"deep_seen":[]},"audit":{},"published_by":"Mateus","items":{
"1":{"id":"1","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"2":{"id":"2","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"3":{"id":"3","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"4":{"id":"4","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"5":{"id":"5","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"6":{"id":"6","status":"done","done":true,"note":"Commit a91322865c23: fix: estabiliza B_07 e preprocessamento esparso float32 [done:#6] [done:#125]","comments":[],"updated_at":"2026-10-18T17:23:01-03:00","updated_by":"mateus-so","origin":"commit","evidence":[{"type":"commit","sha":"a91322865c23","subject":"fix: estabiliza B_07 e preprocessamento esparso float32 [done:#6] [done:#125]","author":"mateus-so","when":"2026-10-18T17:23:01-03:00","marker":"done"}],"history":[{"at":"2026-10-18T17:23:01-03:00","by":"mateus-so","from":"open","to":"done","origin":"commit","ref":"a91322865c23"}],"dismissed":[],"flags":{}},
"7":{"id":"7","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"8":{"id":"8","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"9":{"id":"9","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"10":{"id":"10","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"11":{"id":"11","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"12":{"id":"12","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"13":{"id":"13","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"14":{"id":"14","status":"in_progress","done":false,"note":"Commit e94dbe2ca014 de Ivan-S-Oliveira cita a tarefa: “resolução da tarefa 14”.","comments":[],"updated_at":"2026-10-19T13:15:12-03:00","updated_by":"varredura de commits","origin":"auto","evidence":[{"type":"commit_task_reference","sha":"e94dbe2ca014","subject":"resolução da tarefa 14","author":"Ivan-S-Oliveira","when":"2026-10-19T13:15:12-03:00","completion_language":false}],"history":[{"at":"2026-10-19T13:15:12-03:00","by":"varredura de commits","from":"open","to":"in_progress","origin":"auto","ref":"e94dbe2ca014"}],"dismissed":[],"flags":{},"auto_prev":"open"},
"15":{"id":"15","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"16":{"id":"16","status":"resolved_pending_validation","done":false,"note":"Commit 9fa6e694d084 de Ivan-S-Oliveira cita a tarefa com linguagem de conclusão: “Resolvendo tarefa 16”. Confirme no painel.","comments":[],"updated_at":"2026-10-18T13:30:22-03:00","updated_by":"varredura de commits","origin":"auto","evidence":[{"type":"commit_task_reference","sha":"9fa6e694d084","subject":"Resolvendo tarefa 16","author":"Ivan-S-Oliveira","when":"2026-10-18T13:30:22-03:00","completion_language":true}],"history":[{"at":"2026-10-18T13:30:22-03:00","by":"varredura de commits","from":"open","to":"resolved_pending_validation","origin":"auto","ref":"9fa6e694d084"}],"dismissed":[],"flags":{},"auto_prev":"open"},
"17":{"id":"17","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"18":{"id":"18","status":"done","done":true,"note":"Commit f8e574fc2d4a: \"test(artifact): cobre columns= sem pular validação de alvo e partição [done:#18]\"","comments":[],"updated_at":"2026-10-19T10:10:12-03:00","updated_by":"Ivan-S-Oliveira","origin":"commit","evidence":[{"type":"commit","sha":"f8e574fc2d4a","subject":"\"test(artifact): cobre columns= sem pular validação de alvo e partição [done:#18]\"","author":"Ivan-S-Oliveira","when":"2026-10-19T10:10:12-03:00","marker":"done"}],"history":[{"at":"2026-10-19T10:10:12-03:00","by":"Ivan-S-Oliveira","from":"open","to":"done","origin":"commit","ref":"f8e574fc2d4a"}],"dismissed":[],"flags":{}},
"19":{"id":"19","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"20":{"id":"20","status":"done","done":true,"note":"Commit 00d7105cc819: refactor(factory): unifica aliases de finalista (hist_gradient_boosting → boosting) e remove duplicação em C_15/C_16 [done:#20]","comments":[],"updated_at":"2026-10-20T11:50:27-03:00","updated_by":"Ivan-S-Oliveira","origin":"commit","evidence":[{"type":"commit","sha":"00d7105cc819","subject":"refactor(factory): unifica aliases de finalista (hist_gradient_boosting → boosting) e remove duplicação em C_15/C_16 [done:#20]","author":"Ivan-S-Oliveira","when":"2026-10-20T11:50:27-03:00","marker":"done"}],"history":[{"at":"2026-10-20T11:50:27-03:00","by":"Ivan-S-Oliveira","from":"open","to":"done","origin":"commit","ref":"00d7105cc819"}],"dismissed":[],"flags":{}},
"21":{"id":"21","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"22":{"id":"22","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"23":{"id":"23","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"24":{"id":"24","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"25":{"id":"25","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"26":{"id":"26","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"27":{"id":"27","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"28":{"id":"28","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"29":{"id":"29","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"30":{"id":"30","status":"in_progress","done":false,"note":"Commit 6129458eaa1b de Ivan-S-Oliveira cita a tarefa: “Correção de tarefa 30”.","comments":[],"updated_at":"2026-10-18T13:07:59-03:00","updated_by":"varredura de commits","origin":"auto","evidence":[{"type":"commit_task_reference","sha":"6129458eaa1b","subject":"Correção de tarefa 30","author":"Ivan-S-Oliveira","when":"2026-10-18T13:07:59-03:00","completion_language":false}],"history":[{"at":"2026-10-18T13:07:59-03:00","by":"varredura de commits","from":"open","to":"in_progress","origin":"auto","ref":"6129458eaa1b"}],"dismissed":[],"flags":{},"auto_prev":"open"},
"31":{"id":"31","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"32":{"id":"32","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"33":{"id":"33","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"34":{"id":"34","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"35":{"id":"35","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"36":{"id":"36","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"37":{"id":"37","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"38":{"id":"38","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"39":{"id":"39","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"40":{"id":"40","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"41":{"id":"41","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"42":{"id":"42","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"43":{"id":"43","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"44":{"id":"44","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"45":{"id":"45","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"46":{"id":"46","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"47":{"id":"47","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"48":{"id":"48","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"49":{"id":"49","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"50":{"id":"50","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"51":{"id":"51","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"52":{"id":"52","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"53":{"id":"53","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"54":{"id":"54","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"55":{"id":"55","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"56":{"id":"56","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"57":{"id":"57","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"58":{"id":"58","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"59":{"id":"59","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"60":{"id":"60","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"61":{"id":"61","status":"resolved_pending_validation","done":false,"note":"Commit 99399b96191c de Ivan-S-Oliveira cita a tarefa com linguagem de conclusão: “resolvendo tarefa 61”. Confirme no painel.","comments":[],"updated_at":"2026-10-19T10:27:11-03:00","updated_by":"varredura de commits","origin":"auto","evidence":[{"type":"commit_task_reference","sha":"99399b96191c","subject":"resolvendo tarefa 61","author":"Ivan-S-Oliveira","when":"2026-10-19T10:27:11-03:00","completion_language":true}],"history":[{"at":"2026-10-19T10:27:11-03:00","by":"varredura de commits","from":"open","to":"resolved_pending_validation","origin":"auto","ref":"99399b96191c"}],"dismissed":[],"flags":{},"auto_prev":"open"},
"62":{"id":"62","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"63":{"id":"63","status":"resolved_pending_validation","done":false,"note":"Commit 17584cfab245 de Ivan-S-Oliveira cita a tarefa com linguagem de conclusão: “resolvendo tarefa 63”. Confirme no painel.","comments":[],"updated_at":"2026-10-19T10:36:13-03:00","updated_by":"varredura de commits","origin":"auto","evidence":[{"type":"commit_task_reference","sha":"17584cfab245","subject":"resolvendo tarefa 63","author":"Ivan-S-Oliveira","when":"2026-10-19T10:36:13-03:00","completion_language":true}],"history":[{"at":"2026-10-19T10:36:13-03:00","by":"varredura de commits","from":"open","to":"resolved_pending_validation","origin":"auto","ref":"17584cfab245"}],"dismissed":[],"flags":{},"auto_prev":"open"},
"64":{"id":"64","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"65":{"id":"65","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"66":{"id":"66","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"67":{"id":"67","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"68":{"id":"68","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"69":{"id":"69","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"70":{"id":"70","status":"in_progress","done":false,"note":"Commit fd7dcaa5cc2f: Atualiza contrato temporal, dicionário e EDA","comments":[],"updated_at":"2026-10-19T00:26:02-03:00","updated_by":"mateus-so","origin":"commit","evidence":[{"type":"commit","sha":"fd7dcaa5cc2f","subject":"Atualiza contrato temporal, dicionário e EDA","author":"mateus-so","when":"2026-10-19T00:26:02-03:00","marker":"in_progress"}],"history":[{"at":"2026-10-19T00:26:02-03:00","by":"mateus-so","from":"open","to":"in_progress","origin":"commit","ref":"fd7dcaa5cc2f"}],"dismissed":[],"flags":{}},
"71":{"id":"71","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"72":{"id":"72","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"73":{"id":"73","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"74":{"id":"74","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"75":{"id":"75","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"76":{"id":"76","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"77":{"id":"77","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"78":{"id":"78","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"79":{"id":"79","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"80":{"id":"80","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"81":{"id":"81","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"82":{"id":"82","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"83":{"id":"83","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"84":{"id":"84","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"85":{"id":"85","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"86":{"id":"86","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"87":{"id":"87","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"88":{"id":"88","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"89":{"id":"89","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"90":{"id":"90","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"91":{"id":"91","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"92":{"id":"92","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"93":{"id":"93","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"94":{"id":"94","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"95":{"id":"95","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"96":{"id":"96","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"97":{"id":"97","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"98":{"id":"98","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"99":{"id":"99","status":"done","done":true,"note":"Commit fd7dcaa5cc2f: Atualiza contrato temporal, dicionário e EDA","comments":[],"updated_at":"2026-10-19T00:26:02-03:00","updated_by":"mateus-so","origin":"commit","evidence":[{"type":"commit","sha":"fd7dcaa5cc2f","subject":"Atualiza contrato temporal, dicionário e EDA","author":"mateus-so","when":"2026-10-19T00:26:02-03:00","marker":"done"},{"type":"commit","sha":"5bdcd8dea744","subject":"perf: valida uso de memória e execução integral do Notebook B_06 [done:#99]","author":"mateus-so","when":"2026-10-21T22:36:16-03:00","marker":"done"}],"history":[{"at":"2026-10-19T00:26:02-03:00","by":"mateus-so","from":"open","to":"done","origin":"commit","ref":"fd7dcaa5cc2f"}],"dismissed":[],"flags":{}},
"101":{"id":"101","status":"resolved_pending_validation","done":false,"note":"Commit 108c723b1566 de Ivan-S-Oliveira cita a tarefa com linguagem de conclusão: “Resolvendo tarefa 101”. Confirme no painel.","comments":[],"updated_at":"2026-10-18T13:11:54-03:00","updated_by":"varredura de commits","origin":"auto","evidence":[{"type":"commit_task_reference","sha":"108c723b1566","subject":"Resolvendo tarefa 101","author":"Ivan-S-Oliveira","when":"2026-10-18T13:11:54-03:00","completion_language":true}],"history":[{"at":"2026-10-18T13:11:54-03:00","by":"varredura de commits","from":"open","to":"resolved_pending_validation","origin":"auto","ref":"108c723b1566"}],"dismissed":[],"flags":{},"auto_prev":"open"},
"102":{"id":"102","status":"in_progress","done":false,"note":"Commit fd7dcaa5cc2f: Atualiza contrato temporal, dicionário e EDA","comments":[],"updated_at":"2026-10-19T00:26:02-03:00","updated_by":"mateus-so","origin":"commit","evidence":[{"type":"commit","sha":"fd7dcaa5cc2f","subject":"Atualiza contrato temporal, dicionário e EDA","author":"mateus-so","when":"2026-10-19T00:26:02-03:00","marker":"in_progress"}],"history":[{"at":"2026-10-19T00:26:02-03:00","by":"mateus-so","from":"open","to":"in_progress","origin":"commit","ref":"fd7dcaa5cc2f"}],"dismissed":[],"flags":{}},
"109":{"id":"109","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"110":{"id":"110","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"111":{"id":"111","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"112":{"id":"112","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"113":{"id":"113","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"114":{"id":"114","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"115":{"id":"115","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"116":{"id":"116","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"118":{"id":"118","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"119":{"id":"119","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"120":{"id":"120","status":"done","done":true,"note":"Commit 941c9ae37c96: docs: valida protocolo temporal e duas janelas de teste [done:#120]","comments":[],"updated_at":"2026-10-21T22:41:37-03:00","updated_by":"mateus-so","origin":"commit","evidence":[{"type":"commit","sha":"fd7dcaa5cc2f","subject":"Atualiza contrato temporal, dicionário e EDA","author":"mateus-so","when":"2026-10-19T00:26:02-03:00","marker":"in_progress"},{"type":"commit","sha":"941c9ae37c96","subject":"docs: valida protocolo temporal e duas janelas de teste [done:#120]","author":"mateus-so","when":"2026-10-21T22:41:37-03:00","marker":"done"}],"history":[{"at":"2026-10-19T00:26:02-03:00","by":"mateus-so","from":"open","to":"in_progress","origin":"commit","ref":"fd7dcaa5cc2f"},{"at":"2026-10-21T22:41:37-03:00","by":"mateus-so","from":"in_progress","to":"done","origin":"commit","ref":"941c9ae37c96"}],"dismissed":[],"flags":{}},
"121":{"id":"121","status":"in_progress","done":false,"note":"Commit 72e839fb1013 de Ivan-S-Oliveira cita a tarefa: “tarefa 121 arrumada”.","comments":[],"updated_at":"2026-10-19T14:07:58-03:00","updated_by":"varredura de commits","origin":"auto","evidence":[{"type":"commit_task_reference","sha":"72e839fb1013","subject":"tarefa 121 arrumada","author":"Ivan-S-Oliveira","when":"2026-10-19T14:07:58-03:00","completion_language":false}],"history":[{"at":"2026-10-19T14:07:58-03:00","by":"varredura de commits","from":"open","to":"in_progress","origin":"auto","ref":"72e839fb1013"}],"dismissed":[],"flags":{},"auto_prev":"open"},
"122":{"id":"122","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"123":{"id":"123","status":"resolved_pending_validation","done":false,"note":"Commit 0eab341e9fd7 de Ivan-S-Oliveira cita a tarefa com linguagem de conclusão: “resolvendo a tarefa 123”. Confirme no painel.","comments":[],"updated_at":"2026-10-19T09:21:28-03:00","updated_by":"varredura de commits","origin":"auto","evidence":[{"type":"commit_task_reference","sha":"0eab341e9fd7","subject":"resolvendo a tarefa 123","author":"Ivan-S-Oliveira","when":"2026-10-19T09:21:28-03:00","completion_language":true}],"history":[{"at":"2026-10-19T09:21:28-03:00","by":"varredura de commits","from":"open","to":"resolved_pending_validation","origin":"auto","ref":"0eab341e9fd7"}],"dismissed":[],"flags":{},"auto_prev":"open"},
"124":{"id":"124","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"125":{"id":"125","status":"done","done":true,"note":"Commit a91322865c23: fix: estabiliza B_07 e preprocessamento esparso float32 [done:#6] [done:#125]","comments":[],"updated_at":"2026-10-18T17:23:01-03:00","updated_by":"mateus-so","origin":"commit","evidence":[{"type":"commit","sha":"a91322865c23","subject":"fix: estabiliza B_07 e preprocessamento esparso float32 [done:#6] [done:#125]","author":"mateus-so","when":"2026-10-18T17:23:01-03:00","marker":"done"}],"history":[{"at":"2026-10-18T17:23:01-03:00","by":"mateus-so","from":"open","to":"done","origin":"commit","ref":"a91322865c23"}],"dismissed":[],"flags":{}},
"126":{"id":"126","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"127":{"id":"127","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"128":{"id":"128","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"129":{"id":"129","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"130":{"id":"130","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"131":{"id":"131","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"132":{"id":"132","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"133":{"id":"133","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"134":{"id":"134","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"135":{"id":"135","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"136":{"id":"136","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"137":{"id":"137","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}},
"138":{"id":"138","status":"open","done":false,"note":"","comments":[],"updated_at":null,"updated_by":"baseline","origin":"baseline","evidence":[],"history":[],"dismissed":[],"flags":{}}
}}
PROJECT_STATUS_DATA -->
