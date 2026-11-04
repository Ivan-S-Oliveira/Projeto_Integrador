<!-- PROJECT_STATUS_TEXT.md · formato 1 · fonte do conteúdo do Painel de Pendências SRAG -->
# Status do projeto SRAG · conteúdo textual

Este arquivo é a **fonte única de todo o texto** do Painel de Pendências (`.srag-status-local/painel.html`). O painel lê este arquivo do GitHub, converte para HTML e grava a página local `painel_gerado.html` sempre que algo muda (o modelo `painel.html` nunca é regravado). A situação compartilhada de cada item (concluída, a confirmar, precisa revisão…), os comentários e o resultado da última verificação continuam em `PROJECT_STATUS.md`, mantido só pelo painel.

**Pode editar à mão** no VS Code ou pelo botão ✎ do painel. Ao salvar aqui, o painel mostra a mudança em ~2 s como prévia local. Para a equipe receber: commit e push normais, ou o botão “Publicar edições locais” do painel.

Regras do formato:

- `## #N · Título` abre um item. O número é fixo e nunca é reutilizado; para tirar um item, use `- removido: motivo`.
- Logo abaixo do título, uma linha por campo: `prioridade` (P1–P4), `situação` (aberta, parcial, resolvida), `estratégia` (desenvolver, explorar, documentar, despriorizar, resolvida), `marco`, `data ideal` (DD/MM), `responsável`, `pessoas` (A, B, C, Equipe), `fonte`, `depende de` (#12, #30), `tags`, `pilar`, `carga` (número), `novo` (sim/não), `professores` (sim/não) e, opcionais, `arquivos` (caminhos que a auditoria deve ligar ao item) e `removido`. Use `—` para vazio. “Trava” é calculado sozinho a partir de “depende de”.
- Seções com `###`: `① Para entender`, `② Problema`, `③ O que fazer` e `④ Pronto quando`. Qualquer outro `### Título` vira uma seção extra no card.
- `④ Pronto quando`: um critério por linha, `- verbo: argumentos | descrição detalhada`. Verbos: `existe`, `nao-existe`, `nao-vazio`, `define`, `nao-define`, `contem`, `nao-contem`, `yaml`, `json`, `teste`, `notebook-executado`, `notebook-saida`, `manual`. A gramática completa está no topo de `.srag-status-local/deep_git_project_audit.py`.
- Texto em Markdown simples: parágrafos, `**negrito**`, `*itálico*`, `` `código` ``, listas com `-` ou `1.`, tabelas `| a | b |`, blocos de código com três crases, links `[texto](url)` e caixas `> [!decisão] Título` (também `atenção`, `exemplo`, `ok` e `pilar`). HTML também é aceito: um bloco que começa com `<` passa sem alteração (é assim que ficam os gráficos de barras e os quadros de números).
- Dentro das seções, não comece linhas com dois ou três `#` seguidos de espaço (subtítulo: use `####`). `#30` no meio do texto vira link para o item no painel.
- `## Painel · textos gerais` guarda os textos do topo, entrega, cronograma, pessoas, caminho crítico, aviso, ajuda e rodapé.

## Painel · textos gerais

### Título

Projeto SRAG · Pendências

### Subtítulo

Retrato de 03/11, ao meio-dia, sobre o commit `5c9e205`. O artefato foi regerado com as **30 variáveis** (saturação e desconforto dentro; perda de olfato, perda de paladar e fadiga fora) e o C_11, o C_12 e o C_14 foram reexecutados nele (#132 e #140 concluídos). Com hiperparâmetros padrão, o `val_ref` (119.243 fichas, 8,4% de óbitos) dá PR-AUC de **0,320 na logística e 0,353 no boosting**, isto é, 3,8× e 4,2× o acaso (critério do professor: pelo menos 1,25×). O C_15 e o C_16 já foram corrigidos pelo script de 03/11, e os rastros da coorte provisória e do desenho 70/5+5+5/15 foram removidos. G6 a G9 continuam pendentes. **Trabalho, teste e apresentação: 05/11 (em negociação com os professores).**

**Regra de ordem:** uma máquina oficial (#158) → G6 e ajuste fino de referência (#1) → G7 e G8 (#79) → exploração em equipe, 04/11 (#155) → execução limpa (#126) e clone limpo (#163) → **05/11: G9, teste aberto uma vez (#2), resultados, relatório, pacote e apresentação** (#55, #133, #157, #147, #134).

### Entrega

05/11/2026 (trabalho, teste e apresentação; em negociação com os professores)

### Cronograma

- **03/11 ter** — 12h: **máquina oficial (#158: A e C)** · 12h30: B corrige o B_04, o B_05 e o 01_extracao (#159, #137) · 13h45: C congela o G6 (#1) · 14h: B: C_15, G7 e G8 na máquina oficial (#79) · A: ensaio do C_16 (#148) e registros no decisoes.md (#73) · noite: cada pessoa prepara a sua frente do #155
- **04/11 qua** — 8h: A: maturidade do desfecho (#160) e ajustes de avaliação (#161) · B prepara a sua frente do #155 e adianta o relatório (#133) · **9h às 15h: exploração em equipe (#155: A logística L2, B logística L1 e elastic-net, C boosting)** · 15h às 16h: confirmação e escolha · 16h às 17h: congelar e rodar o C_15 final (**corte duro às 17h**) · 17h: importância das variáveis (#91) · 18h: nomes da entrega (#146) · 19h às 22h: execução limpa e README (#126), caminhos locais (#156) · 22h: clone limpo (#163) e hipóteses do teste registradas (#161) · em paralelo: relatório sem os números do teste (#133), referências (#112), dicionário (#70)
- **05/11 qui** — 7h45: RAM e checklist (#161, #2) · 8h: G9 e abertura única do teste (#2) · 9h30: conferência das saídas · 10h: figuras e tabelas por grupo (#55) · 10h às 14h: números do teste no relatório (#133) · 14h: resultados no pacote (#157) · 14h30: slides e ensaio (#134) · 16h: congelar e empacotar (#147) · **apresentação**

### Legenda das estratégias

<div class="legend"><span class="tag e-desenvolver">▶ Desenvolver</span>necessário <span class="tag e-explorar">🔍 Explorar</span>opcional com prazo <span class="tag e-documentar">✎ Decidir/documentar</span>contrato e decisão <span class="tag e-despriorizar">⏸ Despriorizado</span>não entra antes da entrega</div>

### Como ler

Cada card é uma pendência. Dentro dele: **① Para entender** (o tema em linguagem simples, com números do projeto), **② Problema** (o que está errado, com detalhes técnicos), **③ O que fazer** (passos), **④ Pronto quando** (critérios conferidos pelo verificador, com ✓, ✗, "indisponível nesta máquina" ou "confirmação manual"), **Ligações** (de quem depende e o que trava) e **Evidências** (commits que citam a pendência, commits que só mexeram nos arquivos dela e histórico). Os números dos itens são fixos e mantêm seus números históricos; o item #108 foi removido por impossibilidade material de recuperar a gravação. Cada card mostra a data ideal mesmo quando fechado. A **barra de progresso** conta só os cards P1, P2 e P3 (os despriorizados e os removidos ficam de fora).

### Pessoas

- **A (≈ 15,5 h)** — ensaio do C_16 (#148), registros no decisoes.md (#73), maturidade do desfecho (#160), ajustes de avaliação (#161), frente da logística L2 no #155, clone limpo (#163), checklist do G9 (#2), equidade e corte por região na versão mínima (#55), dicionário (#70), resultados e pacote (#157, #147), relatório (#133, dona)
- **B (≈ 12,8 h)** — correção dos notebooks B (#159, #137), restos da limpeza (#152, #153), C_15 com G7 e G8 (#79), frente da logística L1 e elastic-net no #155, nomes da entrega (#146), README (#126), referências (#112), relatório (#133), apresentação (#134, dona)
- **C (≈ 11,5 h)** — máquina oficial (#158), ajuste fino de referência (#1), frente do boosting no #155, ajustes de avaliação (#161), importância das variáveis (#91), execução limpa (#126), execução do teste (#2), relatório (#133)
- **Equipe** — máquina oficial (#158), exploração e escolha final (#155), aprovação do G9 (#2)

### Caminho crítico

#158 → #1 → #79 → #155 → #126 → #163 → #2 → #133 → #157 → #147 → #134

### Aviso da revisão

> [!decisão] Ajuste de 03/11 · versão 4.2: scripts da tarde e critérios do “Pronto quando” alinhados ao código (verificado sobre o commit `cba5d46`)
> **O que foi aplicado no repositório** (todos os scripts começaram por um relatório numa cópia): #79 (`limiar.metrica: precision`), #126 (parte mecânica: `cloudpickle` e README), #152 (conferência: os restos locais da coorte provisória já não existiam) e #154 (esquema legado e fluxo A removidos; as invariantes do #135 agora estão em `tests/test_invariantes_protocolo.py`).
>
> **O que mudou no verificador:** o “④ Pronto quando” é o verificador (está no texto, não no código dele). Os critérios que apontavam para `tests/test_regras_pessoa_a.py`, `src/protocolo/verificacoes.py`, `dataset_analitico` e para testes legados do artefato foram trocados nos cards #16, #87, #102, #123, #135 e #144; o #154 e o #79 ganharam critérios novos. Sem essa troca, esses cards já concluídos voltariam a “reconfirmar”.

> [!decisão] Revisão de 03/11 · versão 4.1: leitura completa do repositório e dos notebooks (commit `5c9e205`) e decisões da equipe sobre o corte por região e o UMAP
> **O que mudou na situação:** #132 e #140 estão concluídos; os scripts de 03/11 foram aplicados (variáveis e ANOVA; C_15 e C_16; rastros); o `requirements.txt` foi restaurado (por isso o #17, o #19 e o #124 estavam em "precisa revisão"). Medido hoje no C_14 (30 variáveis, hiperparâmetros padrão, treino inteiro): cada ajuste leva de 8 a 16 s, e o `val_ref` dá PR-AUC de 0,320 (logística) e 0,353 (boosting).
>
> **Correções do meu próprio plano:**
> - **#155 reescrito.** A versão anterior pedia `max_features`, `interaction_cst`, splines, interações e variáveis derivadas. O construtor do boosting aceita só 10 hiperparâmetros, e a fábrica **ignora em silêncio** (só um `RuntimeWarning`) as chaves que não conhece: o teste seria feito com outro modelo. Variáveis derivadas exigiriam código novo em `src/` e regerar o artefato. Agora: só hiperparâmetros que o construtor aceita, mais a logística com L1 e elastic-net.
> - **Corte por região: só a versão mínima (decisão da equipe em 03/11).** O professor sugeriu, em 24/10, um modelo único com ponto de corte por região. A equipe decidiu fazer a versão mínima: modelo único, corte global e **métricas e calibração por região no teste** (tabelas por região, UF, faixa etária e raça/cor, e figura de sensibilidade e precisão por região). O corte regional vira limitação e trabalho futuro. O #162, que o implementaria (cerca de 1 h 45 min), foi **removido e absorvido pelo #55** (que passa a 1 h 15 min). Ganho líquido: cerca de 1 h 15 min, e nenhuma alteração no C_15 nem no C_16 antes do teste.
> - **UMAP avaliado e deixado de fora.** Custaria de 3 a 4 h (teste de instalação, código no B_04, texto e slide) e o agrupamento já mostra que os grupos refletem idade e preenchimento. Resposta pronta no #134.
> - **Armadilha do `class_weight`.** A fábrica descarta valores `null` do YAML, então `class_weight: null` **não** treina sem peso: vale o padrão `balanced`. Para treinar sem peso, escreva `class_weight: {}`. Isso muda como o #1, o #79 e o #155 congelam o peso de classe.
>
> **Cards novos (5):**
>
> | Card | O quê | Por quê |
> |---|---|---|
> | #158 | Uma máquina oficial para a cadeia que termina no teste | O C_16 só abre o teste se achar, no mesmo computador, o manifesto do C_15 com o mesmo `dataset_sha256` |
> | #159 | B_04, B_05, 01_extracao e B_02 | O B_04 vai falhar na execução limpa: exige três variáveis que saíram do modelo |
> | #160 | Maturidade do desfecho por ano | A orientação do TCC pede medir desfechos pendentes e a estabilidade de 2025 |
> | #161 | Ajustes de avaliação antes do teste | Raça/cor e zona, hipóteses registradas, referência só idade e sexo, memória |
> | #163 | Clone limpo | O `requirements.txt` sumiu e só o pytest percebeu |
>
> **Scripts previstos** (todos começam por relatório, como combinado): `corrigir_notebooks_b.py` (#159), `explorar_hiperparametros.py` (#155), `executar_cadeia.py` (#126), `tabelas_relatorio.py` (#55 e #133), `montar_resultados.py` (#157), `dicionario_variaveis.py` (#70) e, por último, `checklist_g9.py` (#2). Cada card traz também os passos manuais (plano B).
>
> **Fora do escopo, de propósito:** SHAP, UMAP, corte de decisão por região (só a versão mínima), validação cruzada, sensibilidade com data do PCR, curvas de decisão e anos anteriores a 2019 ("primeiro trabalho, não TCC", orientação de 24/10).

> [!decisão] Revisão de 03/11 · versão 3.4: variáveis e ANOVA
> **Variáveis (#140):** saturação e desconforto respiratório entram no modelo principal (estão na definição de caso de SRAG hospitalizado e no campo 34 da ficha; maior ganho das ablações); perda de olfato, perda de paladar e fadiga saem (campos da era COVID, marcador de período, custo nulo). O modelo passa a ter 30 variáveis. A sensibilidade "sem saturação e desconforto" foi desativada, e o C_14 passa a medir "P − gravidade" e "P + 3 sintomas".
> **Ordem nova:** o #140 vem **antes** do #132, porque o artefato precisa ser regerado com a lista nova (mesmas fichas e blocos, hash novo).
> **ANOVA (#137, reaberto):** o professor pediu ANOVA e qui-quadrado no perfil dos grupos; o B_04 tinha só o qui-quadrado e o Kruskal-Wallis. Entra a ANOVA com η², e o Kruskal-Wallis fica como conferência.
> **Cards ajustados:** #132, #1, #155 (saturação deixa de ser proibida; nova variável derivada `sinal_gravidade`), #133, #134, #73, #70 e o #9 (concluído: critérios atualizados para a decisão nova).
> **Ferramenta:** `aplicar_decisoes_03_11.py` aplica as duas mudanças com conferência de cada troca (`--variaveis`, `--anova`, `--simular`). Salve fora do repositório.

> [!decisão] Revisão de 03/11 · versão 3.3: conferência dos removidos e varredura dos notebooks
> **Removidos conferidos um a um contra o repositório.** Nenhum precisa voltar, mas cinco motivos estavam errados ou incompletos e foram corrigidos: #35, #38, #74 e #137 citavam o "B_06/B_07" como inexistente, e eles só **mudaram de nome** para B_04/B_05 (o #35, o #38 e o #137 já estão resolvidos no código: o B_04 tem qui-quadrado, V de Cramér e Kruskal-Wallis); o #109 era sugestão de professor e ganhou resposta pronta no #134. Três textos do `decisoes.md` ainda dependiam de cards removidos e foram para o #73 (§7 sazonalidade, §29.7 ANOVA, §29.24 notebook A_15).
>
> **Necessidades que não estavam mapeadas (varredura dos 15 notebooks):**
> - **#156 (novo, P1):** 165 caminhos locais com o nome do usuário e da empresa nas saídas salvas dos notebooks.
> - **#157 (novo, P1):** `outputs/` e `reports/figures/` são ignorados pelo Git: sem uma pasta `resultados/`, nenhuma tabela ou figura citada no relatório chega à banca.
> - **#126:** o A_03 republica a coorte e regera o artefato por padrão (os três interruptores estão `True`): roda primeiro, e nunca depois do teste (#2). O medidor para a sequência se um notebook passar de 6 GB; o comando agora usa 12 GB.
> - **#146:** os títulos dos notebooks C ainda dizem C2 a C6 e há mensagens "Execute o Notebook 03" e "O B_07 exige…"; os **prefixos dos arquivos de saída não podem ser renomeados**, porque o C_16 encontra o manifesto do C_15 por eles.
> - **#70:** o dicionário completo já existe em `configs/dicionario_variaveis_v1.csv`; o card passa a filtrá-lo em vez de escrever do zero.
> - **#147:** `tools/read_outputs.py` e `tools/perfil_celulas.py` usam bibliotecas fora das dependências e saem do pacote; a conferência final inclui a busca por caminhos locais.

> [!decisão] Revisão de 03/11 · versão 3.2: cada pendência aberta conferida contra o código (commit `863dd45`)
> **20 cards ficam** (14 P1, 5 P2, 1 P3). **21 cards pós-entrega foram removidos**: o projeto termina em 05/11, então "depois da entrega" não tem janela. Cada um tem o motivo no campo "removido" (filtro "Removidos" do painel) e pode ser reaberto se o trabalho continuar como TCC. O que eles tinham de útil virou frase de limitação ou de trabalho futuro no #133; os códigos do #49 foram para o #70.
>
> | Motivo da remoção | Cards |
> |---|---|
> | já resolvido no código | #38 (modo de teste sintético), #137 (B_04 já usa só o `train_ref`) |
> | cita notebooks que não existem mais (A_08, B_06, B_07, notebooks A da coorte provisória) | #25, #35, #74, #129 |
> | variável fora do modelo | #48 (`tp_pov_ct`), #84 (vacina) |
> | gatilho vencido ou já coberto por outro card | #111, #138, #145, #49 |
> | trabalho futuro, agora frase no relatório | #13, #53, #109 |
> | sem efeito na entrega (cosmético ou ferramenta interna) | #24, #32, #42, #94, #96, #128 |
>
> **Restos do desenho de três blocos de validação, corrigidos nos textos dos cards:** #132, #140 e #133 não falam mais em "seis blocos"; o #153 deixou de pedir para apagar o script de troca (ele já não está no repositório), passou a renomear todas as tabelas `*_val_tune.csv` do B_05 e a marcar como histórico as §29.4, §29.16, §29.17, §29.19, §29.21 e §29.22; o #79 ganhou a correção do texto do C_15 que ainda cita 21,9% de óbitos (prevalência da coorte provisória). Nos C_15 e C_16, `val_cal` e `val_meas` são as **duas metades internas do `val_ref`** e continuam com esses nomes.

> [!decisão] Ajuste de 03/11 · versão 3.1: um dia de exploração antes do teste
> Em 04/11 a equipe se reúne para explorar hiperparâmetros e variáveis derivadas (#155), com orçamento fixo e regra de escolha registrada **antes** de rodar. O **teste passa para 05/11 de manhã** (#2), junto com tudo o que depende dele e da apresentação: resultados por grupo (#55), números do teste no relatório (#133), congelamento (#147) e apresentação (#134). A execução limpa (#126) e os nomes da entrega (#146) ficam em 04/11 à noite, depois da exploração.

> [!decisão] Replanejamento de 03/11 · versão 3 (entrega em 05/11, plano B em 04/11)
> Revisão completa das 69 pendências abertas contra o código do commit `9f3322b` (pacote de referência de 03/11, 04:25 UTC). Três mudanças de fundo desde a versão 2: a **coorte provisória foi aposentada** (§29.32), a validação passou para o **desenho 70/15/15** (§29.33, `val_ref`) e o artefato foi regerado. Resultado: **19 cards de trabalho** (14 P1, 5 P2), 1 P3 e 21 despriorizados. Cards unificados levam o número do card principal; os absorvidos ficam como "removido" com o destino no motivo.

| Card principal | Absorveu | Por quê |
|---|---|---|
| #140 (variáveis) | #54, #50 | ablação e decisão dos três sintomas são o mesmo passo |
| #1 (G6 e ajuste) | #78 | o G6 libera a busca que o #1 executa |
| #79 (G7 e G8) | #80, #5, #58 | o C_15 decide peso de classe, calibração e limiar numa só execução |
| #148 (C_16) | #26, #27 | registro do teste aberto e escolha do manifesto ficam no próprio C_16 |
| #2 (teste) | #81, #119 | checklist, abertura e conferência acontecem na mesma noite |
| #133 (relatório) | #56, #71, #45, #46, #47, #69 | eram só parágrafos do relatório |
| #91 (importância) | #57 | a leitura ajustada pela idade faz parte da tabela de importância |
| #55 (subgrupos) | #110 | o corte por região sai das mesmas saídas do C_16 |
| #147 (congelar) | #149, #130 | a reconferência e a referência são passos do congelamento |
| #152 (novo: provisória) | #151, #150, #41, #43 | um único card de limpeza com lista fechada de arquivos |

**Removidos por obsolescência** (a coorte provisória ou o notebook citado não existem mais): #40, #98, #89, #88, #90, #93, #39. **Novos:** #152 (rastros da coorte provisória), #153 (rastros do desenho 70/5+5+5/15), #154 (código legado, P3) e #155 (exploração de hiperparâmetros em equipe, 04/11).

> [!atenção] Se os professores mantiverem o trabalho em 04/11
> O #155 é cortado inteiro (o modelo do #1 e do #79 já está congelado e pronto) e o teste (#2) volta para 04/11, 20h. Depois, cortar nesta ordem: #146, #70, #112; #91 e #55 viram só as tabelas mínimas. **Nada do caminho crítico é cortado.**

> [!ok] Confirmar no painel depois de executar
> O #132 pode ser marcado como concluído assim que o C_11, o C_12 e o C_14 forem salvos com as saídas do artefato 70/15/15. Nenhum card foi marcado como concluído nesta revisão: o estado compartilhado só muda pelo painel ou por `[done:#N]` num commit.

### Ajuda · Como usar (30 segundos)

- **Abrir:** dois cliques em `.srag-status-local\ABRIR_PAINEL.cmd`. Abre uma janela do terminal que fica aberta rodando o servidor; não feche enquanto usa. Se já estiver aberto, só abre a aba. O painel só abre a partir da pasta do repositório.
- **Marcar como feito:** a caixa aparece no **topo** do card e de novo no **fim**; as duas são a mesma marcação. O painel confere o **④ Pronto quando**: se o verificador não confirmar todos os critérios, pede um comentário de pelo menos 15 caracteres explicando por que concluir assim mesmo. Vale também para confirmar uma pendência que estava em revisão.
- **Outras marcações:** reabrir, comentar ou confirmar/rejeitar uma sugestão. Cerca de 12 s depois do último clique sai um commit curto só com os arquivos do painel, agrupado por tipo e com cada pendência citada uma vez, ex.: `(#status) concluída: #10; conteúdo: #1, #31, #46 +12 · Mateus`. “▶ Estou fazendo” é só seu e não gera commit.
- **Editar o conteúdo:** botão ✎ no card (ou ➕ Nova pendência). A alteração vai para o `PROJECT_STATUS_TEXT.md` no mesmo tipo de commit curto, campo a campo. Também dá para editar o `PROJECT_STATUS_TEXT.md` direto no VS Code: o painel mostra a prévia em ~2 s.
- **Atualizar:** automático a cada hora e ao voltar para a aba. **⟳ Buscar** força agora e **nunca gera commit**; depois da busca, uma verificação rápida (sem testes) atualiza os ✓/✗ dos cards. **🔄 Atualizar, auditar e validar** confere todos os critérios e roda o pytest rápido numa cópia limpa do commit publicado; só gera commit se alguma pendência mudar.
- **REVISÕES:** seção no topo, sempre aberta até você recolher. Reúne o que pede atenção: detectadas como concluídas, concluídas que o verificador ainda vê como pendentes, revisões, testes falhando (aviso para todos), configuração crítica alterada, critérios inválidos e referência para IAs desatualizada.
- **Meu dia:** escolha a pessoa e veja as atrasadas, as prontas para começar, as revisões e o que destravou desde a última visita.
- **Commits do dia a dia:** continue no VS Code. Escreva `tarefa 30`, `#30` ou `[done:#30]` na mensagem: o painel reconhece sozinho.

> [!ok] Por que o VS Code não reclama
> O painel **nunca** grava o `PROJECT_STATUS.md` na sua pasta de trabalho. Ele lê o arquivo direto do GitHub e publica o commit “por fora”. Assim o arquivo nunca aparece como modificado e o *pull* não dá erro. Os arquivos de cada máquina (fila, caches, relatórios, `painel_gerado.html`) ficam fora do Git pelo `.gitignore` da pasta `.srag-status-local`. O `PROJECT_STATUS_TEXT.md` é diferente: é seu para editar, e o painel só mexe nele na pasta quando você clica em “Publicar edições locais”.

> [!atenção] Quando sai commit
> Só quando há decisão: concluir, reabrir, comentar, confirmar/rejeitar sugestão, escolher num conflito, editar conteúdo pelo painel, ou quando a verificação muda uma pendência (teste que falha e importa os arquivos dela). Buscar, ler commits, “Estou fazendo”, prévia de edições locais e a verificação rápida nunca geram commit.

> [!atenção] Três pessoas ao mesmo tempo, ou alguém sem conexão
> Cada clique vira uma alteração pequena (item + campo) guardada na fila local. Na publicação, o painel busca a versão mais nova do GitHub e reaplica as suas alterações por cima. Campos diferentes do mesmo card somam (uma pessoa muda o título, outra o responsável, outra comenta) e comentários sempre somam. Só o **mesmo campo** mudado por outra pessoa vira conflito: esse campo fica fora do seu commit, o resto sai, e abre um popup com a sua versão, a publicada e a original (“Manter a minha”, “Manter a publicada” ou “Editar e juntar”). Sem internet, a fila fica guardada e sai sozinha quando a conexão voltar; o selo mostra desde quando e a causa provável. Push rejeitado por concorrência é refeito automaticamente; nunca usa `--force`. O painel também se recusa a publicar um estado que perca itens, comentários ou histórico.

### Ajuda · Instalação e atualização (uma vez por pessoa)

- **Daqui para a frente, pelo Git:** o código do painel (`server.py`, `project_status_text.py`, `deep_git_project_audit.py`, `painel.html`, os `.cmd` e o `LEIA-ME.md`) é versionado. Para atualizar: feche o painel, faça *pull* e abra o `ABRIR_PAINEL.cmd`. Se esquecer de fechar, a versão nova encerra a antiga ao abrir (a antiga publica a fila antes de sair).
- **O que fica só na sua máquina:** fila (`outbox.json`), caches, relatórios, `config.json`, `backups/`, `logs/` e a página `painel_gerado.html`, que é montada a partir do `painel.html` com o texto deste arquivo. Ela é criada na primeira abertura; ninguém precisa mexer nela.
- **Conferir a versão:** o rodapé do painel mostra **Painel v6.0.0**.
- **Requisitos:** os mesmos de sempre, isto é, Python 3 (o `.venv` do projeto) e a credencial do GitHub que o VS Code já usa.

### Ajuda · Como interpretar os estados

- **ABERTA:** sem evidência suficiente.
- **EM ANDAMENTO:** commit com `[progress:#ID]` ou que só cita a tarefa, ou marcação no painel. O “▶ Estou fazendo” aparece só para você.
- **RESOLVIDA — PENDENTE DE VALIDAÇÃO (a confirmar):** commit que cita a tarefa explicitamente com linguagem de conclusão (“tarefa 30 concluída”, “corrige #30”), mais novo que a última decisão humana. Commit que só mexe nos arquivos da tarefa **nunca** muda a situação: aparece como informação no card. Um humano confirma com um clique (e comenta, se o ④ não estiver todo ✓).
- **PRECISA REVISÃO:** um teste que falha importa arquivos de uma pendência já iniciada (o teste entra sozinho no ④ dela), ou alguém reabriu para revisão.
- **CONCLUÍDA:** confirmação humana no painel ou `[done:#ID]` no commit. Automação nunca conclui sozinha.
- **⚠ Reconfirmar / concluída ainda pendente:** item concluído cujo ④ o verificador ainda não confirma. A conclusão não é apagada; aparece em REVISÕES.
- **⚠ #N aguardando revisão (aviso rosa):** a pendência da qual este card depende parece concluída, mas aguarda revisão. Pode começar, mas revise o #N antes.
- **Resultado de cada critério do ④:** ✓ atendido · ✗ não atendido · indisponível nesta máquina (arquivo de `outputs/` ou `data/` que só existe na máquina de quem gerou) · confirmação manual (só uma pessoa confirma) · inválido (critério mal escrito: aparece em REVISÕES).
- **Situação editorial** (aberta, parcial, resolvida no `PROJECT_STATUS_TEXT.md`) é o que o texto do card descreve; a **situação compartilhada** acima é a que vale para o andamento.

### Ajuda · Marcadores reconhecidos nos commits

- `[done:#30]`, `[feito:#30]` → concluída. `[progress:#30]` → em andamento. `[reopen:#30]` → reaberta.
- `tarefa 30`, `tarefas 30, 31 e 32`, `item 30`, `pendência 30`, `task 30`, `#30` → com palavra de conclusão (corrige, implementa, resolve, conclui, finaliza, fecha, feito, pronto, fix, done…) vira “a confirmar”; sem ela, “em andamento”.
- Só vale commit **mais novo** que a última decisão humana sobre a pendência. “Merge pull request #N”, commits do próprio painel e commits que só mexem no `PROJECT_STATUS_TEXT.md` são ignorados.

### Ajuda · Editar o conteúdo (PROJECT_STATUS_TEXT.md)

- **Pelo painel:** ✎ Editar no card abre o editor com todos os campos e as seções em Markdown, com pré-visualização. Salvar enfileira só os campos que você mudou; o commit sai ~12 s depois, junto com outras marcações.
- **Pelo VS Code:** edite `PROJECT_STATUS_TEXT.md` na raiz do repositório e salve. O painel detecta em ~2 s, mostra a prévia com o selo “prévia local” e lista os itens alterados no topo. Depois faça commit e push normais, ou clique em **Publicar edições locais**.
- **④ Pronto quando:** um critério por linha, `- verbo: argumentos | descrição detalhada`. Exemplos: ``- define: `src/data/split.py` :: `criar_group_id` | A função existe…`` · ``- yaml: `configs/supervised.yaml` :: `gates.G6_finalistas_tuning.status` = `aprovado` | O G6 está aprovado…`` · ``- teste: `tests/test_split.py` | Os testes de partição passam…`` · `- manual: | O relatório foi revisado por duas pessoas.` Critério sem descrição é inválido.
- **Item novo:** ➕ Nova pendência no painel (o número é definido na publicação, sem colisão) ou um novo `## #N · Título` no arquivo usando o próximo número livre.
- **Remover:** nunca apague a seção; use `- removido: motivo`. O número fica reservado e o card some da lista (filtro “Removidos” mostra).
- **Erros de formato** (número repetido, dependência inexistente, valor desconhecido, critério inválido) aparecem num aviso no topo ou em REVISÕES; o painel continua funcionando com o resto.

### Ajuda · Se algo parecer errado

- Clique em **⟳ Buscar atualizações**. Nada é perdido: há fila local, backups em `.srag-status-local/backups` e todo o histórico no Git.
- **“Sem conexão”:** passe o mouse no selo vermelho para ver a causa provável e o erro do Git. Credencial: faça um *pull* pelo VS Code (ele pede o login) e busque de novo. Rede: troque de rede ou ligue/desligue a VPN. A fila fica guardada até a conexão voltar.
- Sugestão automática errada? Use **✗ Não é isso** no card: ela volta ao estado anterior e aquele commit não será usado de novo para o item.
- Marcou errado? Desmarque “feito”: a reabertura fica no histórico do card.
- Painel sem texto ou desatualizado? Rode `.\.venv\Scripts\python.exe .srag-status-local\server.py gerar` para recriar o `painel_gerado.html` a partir do `PROJECT_STATUS_TEXT.md`, e `... server.py validar` para listar problemas de formato.
- Verificador no terminal: `.\.venv\Scripts\python.exe .srag-status-local\deep_git_project_audit.py` (`--item 142` para uma pendência, `--self-test` para testar a instalação).
- Diagnóstico: `DIAGNOSTICO.cmd` e o arquivo `.srag-status-local/logs/painel.log`.

### Rodapé

Painel local de acompanhamento do projeto. O conteúdo vem de PROJECT_STATUS_TEXT.md e o estado compartilhado de PROJECT_STATUS.md, ambos publicados pelo painel direto no GitHub. Planejamento alinhado à Base de Conhecimento v10 (27/10/2026), ao replanejamento de 31/10 · versão 2 e à revisão completa de 03/11 · versão 3 (commit 9f3322b: coorte provisória aposentada e desenho 70/15/15). Painel v6.

### Ajuda · Como ler a carga estimada

- O campo **carga** de cada card é o esforço estimado em **horas** de trabalho focado (aceita meia hora: `1,5`). Quando há mais de uma pessoa, o campo **responsável** traz as horas de cada uma entre parênteses (por exemplo, `Pessoa A (1,5 h) + Pessoa B (2 h)`), e o quadro "Carga aberta por pessoa" soma essas horas.
- O quadro conta só cards **abertos e não despriorizados**. Tempo de máquina (ajuste fino, execução dos notebooks) não entra nas horas.
- Estimativas não são prazos rígidos. Se uma tarefa passar do dobro do previsto, comente no card para redistribuir.

### Ajuda · Datas e dependências

- Nenhum card tem data anterior à de um card do qual ele depende.
- Quando dois cards ligados caem no mesmo dia, o prazo indica o turno (manhã, tarde, noite) e o que vem antes termina primeiro.
- Cards absorvidos por outro (esforço 0) têm a mesma data do card que os contém.
- Se um card atrasar, os que dependem dele atrasam junto: avise no card e use o filtro "Só prontos para começar".
- Um card concluído só volta para ABERTA se uma decisão pendente ou um resultado ainda por vir puder mudar a conclusão (revisão de volatilidade de 01/11); se só os números mudarem, ele fica concluído e a reconferência entra no #149.

## #120 · Registrar o protocolo fechado: treino não pandêmico e duas janelas de teste

- prioridade: P1
- situação: resolvida
- estratégia: resolvida
- marco: M0
- data ideal: Concluído
- responsável: Pessoa B (dona; revisão cruzada sem edição concorrente)
- pessoas: B
- fonte: Plano_Implementacao_Integrado_SRAG_v2.html (seção 4); reunião de 18/10
- depende de: —
- tags: Decisão
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 5
- novo: sim
- professores: não

### ① Para entender

> [!ok] Decisão fechada em 18/10
> A coorte definitiva inicial será a seleção de features da coorte provisória. O treino principal usará exclusivamente 2019, 2023, 2024 e 2025. Haverá duas janelas de teste: (A) 2019, 2023, 2024 e 2025; (B) 2019 a 2025, incluindo 2020–2022. O ano de 2026 não participa do desenvolvimento nem dos testes principais e fica apenas como exploração opcional, depois de todo o restante concluído.

O objetivo agora não é decidir se 2020–2022 entram no treino. Isso já foi decidido: não entram. O objetivo é medir o mesmo modelo congelado em duas janelas de teste.

| Comparação | O que responde | Leitura correta |
|---|---|---|
| Teste A: 2019, 2023–2025 | Desempenho no domínio temporal usado para desenvolver o modelo | Resultado principal |
| Teste B: 2019–2025 | Quanto o desempenho global muda quando 2020–2022 são acrescentados à avaliação | Robustez temporal; também reportar separadamente apenas 2020–2022 |
| Diferença A × B | Sensibilidade do resultado à composição temporal | Não interpretar como efeito causal da pandemia |

### ② Problema

Sem protocolo escrito, o Teste B pode diluir ou inflar o resultado apenas por mudar a prevalência e o volume. O relatório precisa mostrar métricas globais, por período e por ano, mantendo as pessoas/grupos fora do treino.

### ③ O que fazer

> [!ok] Situação verificada em 24/10
> Concluída: protocolo registrado em `docs/decisoes.md` §28 (commit `941c9ae`, 21/10) e nos blocos de `configs/supervised.yaml`. O que falta do critério de aceite da §28.4 (testes automáticos de anos proibidos e de grupos cruzando blocos **no artefato real**) foi movido para o #131, onde o artefato é gerado.

**Como manter o protocolo vivo até a entrega (sem retrabalho):**

1. Toda execução de modelagem lê anos e blocos de `temporal.blocos` do YAML; nenhum notebook declara anos à mão. Quem revisar um notebook procura por `2019`, `2023` ou `2020` escritos no código: se aparecerem fora do YAML, é defeito.
2. Teste A (`test_ref`) é o resultado principal. Teste B (`test_ref` + `test_pandemic`) nunca aparece sozinho: sempre ao lado do resultado isolado de 2020–2022 e das métricas por ano (#119).
3. A leitura A × B é **robustez temporal**, não efeito da pandemia. A frase pronta para o relatório está no #71.
4. Nenhum resultado de teste volta para decisões: se algo parecer errado depois do G9, vira limitação documentada, não ajuste (§22 das decisões).

**Pronto quando:** o #131 publicar o manifesto da partição com os seis blocos e os testes do §28.4 passarem.

### ④ Pronto quando

- contem: `docs/decisoes.md` :: `## 28. Decisão temporal` | O docs/decisoes.md tem a seção 28, que registra o protocolo fechado: treino de referência, Teste A (test_ref) e Teste B (test_ref + test_pandemic), com 2026 só como exploração.
- yaml: `configs/supervised.yaml` :: `gates.G2_janela_temporal.status` = `aprovado` | O gate G2 (janela temporal) está aprovado no supervised.yaml, ou seja, o desenho dos blocos é o oficial.
- yaml: `configs/supervised.yaml` :: `avaliacao.janelas.teste_b.blocos` contem `test_pandemic` | O YAML declara o Teste B como a união de test_ref com test_pandemic, para que ninguém o calcule à mão.
- yaml: `configs/supervised.yaml` :: `avaliacao.comparacao_temporal.interpretacao_causal_permitida` = `false` | O YAML proíbe ler a diferença Teste A × Teste B como efeito causal da pandemia (é robustez temporal).

## #10 · Regra definitiva para números de notificação repetidos

- prioridade: P2
- situação: parcial
- estratégia: documentar
- marco: M1
- data ideal: 01/11
- responsável: Pessoa A (regra, função e testes) · revisão: Pessoa C
- pessoas: A
- fonte: docs/decisoes.md §6; Plano v2 (A1, passo 5); B_07_supervisionado_pilotos (seção 7)
- depende de: #73
- tags: Diverge do decidido, Decisão, Dados/Coorte, Partição
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 0
- novo: não
- professores: não

### ① Para entender

> [!decisão] Decisão de 18/10
> Proposta: manter a quarentena atual (4 linhas, 2 grupos) como regra definitiva e registrar.

Cada ficha tem um `nu_notific`. Ele deveria ser único, mas 58 linhas repetem 29 números. Na coorte, 2 grupos aparecem em anos diferentes e foram colocados em **quarentena** (4 linhas fora da modelagem).

<div class="kpi">
<div><b>58</b>linhas com número repetido na base bruta</div>
<div><b>4</b>linhas em quarentena no B_07</div>
<div><b>9–10</b>números em partições diferentes no A_09</div>
</div>

Três documentos mandam fazer três coisas diferentes. A quarentena é uma solução provisória.

### ② Problema

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que esta pendência está aberta
> A auditoria automática do painel (27/10, 14:40) marcou este item como resolvido com base em commits de 18 e 19/10 (`a913228`, `f8e574f`), todos anteriores às revisões de 24 e 26/10 e sem relação com a entrega descrita aqui. Isso acontece por um defeito do painel: a cada auditoria, um commit antigo ainda não rejeitado reabre a sugestão (detalhes no #94).
> `criar_group_id` não existe em `src/`; o artefato atual ainda chama a coluna de `grupo_split`; `docs/decisoes.md` §6 não registra a regra. A função entra pelo #142 e o registro pelo #73.

Cada documento manda tratar os números de notificação repetidos de um jeito. As decisões dizem para não escolher arbitrariamente a primeira ocorrência e manter registros diferentes. O plano diz para manter a primeira ocorrência com flag. O B_07 coloca em quarentena os grupos cujo identificador aparece em mais de um estrato (2 grupos, 4 linhas).

### ③ O que fazer

> [!decisão] Enxugado em 27/10 (eficiência primeiro)
> A função `criar_group_id` entra no `src` pelo #142 (Pessoa B) e o registro da regra está no #73. Nada mais a fazer aqui.

### ④ Pronto quando

- define: `src/data/split.py` :: `criar_group_id` | A função criar_group_id existe em src/data/split.py (entra pelo #142): agrupa as fichas pelo nu_notific sem espaços e usa "sem_notific:" + id_registro quando o número está vazio.
- contem: `docs/decisoes.md` :: `criar_group_id` | O docs/decisoes.md registra a regra definitiva de números de notificação repetidos citando a função criar_group_id (registro feito no pacote do #73).

## #131 · Ensinar os seis blocos ao módulo de leitura do artefato

- prioridade: P1
- situação: parcial
- estratégia: desenvolver
- marco: M2
- data ideal: 27/10
- responsável: Pessoa C (dona; revisão cruzada sem edição concorrente)
- pessoas: C
- fonte: Revisão de 24/10: referência do projeto (commit baee782), configs/supervised.yaml, src/data/split.py, src/data/supervised_artifact.py
- depende de: —
- tags: Dados/Coorte, Partição, Código, Gate, Vazamento
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 2
- novo: sim
- professores: não
- arquivos: src/data/supervised_artifact.py, src/data/split.py, src/features/engineering.py, tests/test_split.py, tests/test_supervised_artifact.py

### ① Para entender

A coorte definitiva (3.884.728 notificações, publicada em 23/10) é a **população**. Para treinar e avaliar modelos, ela precisa virar o **artefato supervisionado**: uma tabela com as 31 features, o alvo, colunas de auditoria (ano, região, UF, faixa etária, sexo, grupo) e a coluna `particao`, que diz a qual bloco cada ficha pertence.

> [!ok] Situação em 24/10 (revisão profunda)
> O B_07 já faz quase tudo isso, mas dentro do notebook: na execução de 24/10 05:33 UTC ele criou o grupo, a região, os seis blocos e salvou um artefato `cohort_kind: final`. O problema é que essa lógica não está no código central (src), o artefato existe só na máquina da Pessoa B (a pasta `data/` não vai para o Git) e o módulo que lê o artefato ainda só conhece "treino", "validacao" e "teste".

| Bloco | Fichas (24/10) | Papel |
|---|---|---|
| train_ref | 556.462 | aprender |
| val_tune | 39.748 | escolher variáveis e ajustes |
| val_cal | 39.746 | calibrar e escolher o corte |
| val_meas | 39.749 | só medir |
| test_ref (Teste A) | 119.245 | resultado principal, aberto uma vez |
| test_pandemic | 2.915.829 | 2020–2022, Teste B |
| exploracao | 173.945 | 2026, opcional |
| fora (grupo cruza períodos) | 4 | excluídas |

### ② Problema

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que esta pendência está aberta
> Estava "em andamento" desde 26/10 porque a lógica de partição existia no B_07. Com o escopo de 27/10 (só a leitura por bloco), nada foi implementado: `ALLOWED_PARTITIONS` continua `{treino, validacao, teste}` e `cohort_source._DEFAULT_KIND` continua `provisional`. Volta para aberta.

Sem esse artefato, nada do supervisionado roda na coorte definitiva: os notebooks C ainda leem o artefato **provisório**, com a divisão antiga (que incluía 2020–2022 em treino). É o primeiro passo do caminho crítico, e dele dependem tuning, calibração, limiar e testes.

### ③ O que fazer

> [!decisão] Replanejamento de 27/10: exploração completa antes do treino
> Tudo o que pode mudar variáveis, representação, alvo ou leitura do modelo roda **antes do ajuste fino (G6)**: primeiro a exploração sem modelo, depois o diagnóstico com o piloto padrão no `val_tune`, depois o ponto de decisão (#140, 30/10, manhã). Só então ajuste, calibração, limiar e teste.

**Dono:** Pessoa C · **Prazo:** 27/10 (terça), em paralelo com o #142 (testes com dados inventados; usa os nomes de coluna combinados no #142) · **Esforço estimado:** ≈ 2 h · **Começa quando:** #142 (artefato com `bloco_mestre` e `id_registro`)

> [!decisão] Escopo de 27/10
> A geração do artefato vai para o `src` pela Pessoa B (#142, função `gerar_artefato_supervisionado`). Aqui fica só a leitura por bloco com proteção do teste, que os notebooks C precisam.

#### Passo a passo
1. Em `src/data/supervised_artifact.py`: `ALLOWED_PARTITIONS` passa a aceitar os seis blocos + `exploracao`, lidos da coluna `bloco_mestre` (ou de `particao`, se o B_07 passar a gravar o bloco real nela; combine no card do #142).
2. Leitura padrão (sem `partitions=`) = `train_ref`, `val_tune`, `val_cal`, `val_meas`.
3. `test_ref` e `test_pandemic` exigem `G9_holdout` aprovado (mesmo `exigir_gate` de hoje); `exploracao` exige `exploracao_2026.ativa`.
4. Testes rápidos em `tests/test_supervised_artifact.py`: leitura padrão não traz teste; pedir `test_ref` com G9 pendente levanta erro; com G9 aprovado (monkeypatch) devolve.
5. Trocar o padrão de `SRAG_COHORT_KIND` em `src/data/cohort_source.py` de `provisional` para `final` (≈ 15 min, com o teste).

#### Pronto quando
Testes rápidos passando e o C_11 lendo `train_ref` sem tocar no teste.

### ④ Pronto quando

- contem: `src/data/supervised_artifact.py` :: `train_ref` | O módulo de leitura do artefato (src/data/supervised_artifact.py) conhece os blocos da partição-mestre: o nome train_ref aparece no código, fora de comentários.
- contem: `src/data/supervised_artifact.py` :: `test_pandemic` | O módulo de leitura conhece o bloco test_pandemic (Teste B), para poder protegê-lo com o G9.
- nao-contem: `src/data/cohort_source.py` :: `_DEFAULT_KIND: str = "provisional"` | O padrão de SRAG_COHORT_KIND em src/data/cohort_source.py deixou de ser provisional (passa a ser final), para nenhum notebook carregar a coorte provisória por engano.
- teste: `tests/test_supervised_artifact.py` | Todos os testes de tests/test_supervised_artifact.py passam no pytest rápido, incluindo os novos: leitura padrão sem teste, test_ref com G9 pendente levantando erro e test_ref liberado com G9 aprovado (monkeypatch).
- teste: `tests/test_cohort_source.py` | Os testes de tests/test_cohort_source.py passam, já ajustados ao novo padrão final da coorte.
- json: `data/analytical/manifesto_supervisionado.json` :: `cohort_kind` = `final` | O manifesto do artefato supervisionado v3 registra cohort_kind = final (herdado do #30).

## #135 · Testes das invariantes do protocolo no artefato v3 (§28.4)

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M2
- data ideal: 28/10
- responsável: Pessoa A (dona; revisão cruzada sem edição concorrente)
- pessoas: A
- fonte: Revisão de 24/10 (rebalanceamento): docs/decisoes.md §28.4; configs/supervised.yaml (temporal.invariantes)
- depende de: #142
- tags: Partição, Vazamento, Testes, Gate
- pilar: Valor científico-acadêmico
- carga: 2
- novo: sim
- professores: não
- arquivos: tests/test_invariantes_protocolo.py

### ① Para entender

A §28.4 das decisões só considera o protocolo implementado quando testes automáticos provarem, **no artefato real**, que nenhum grupo cruza blocos e que os anos proibidos não entram no desenvolvimento. É a auditoria final do desenho, antes de qualquer tuning.

### ② Problema

A função de partição foi testada só com dados sintéticos. Ninguém conferiu ainda o artefato gerado sobre a coorte definitiva.

### ③ O que fazer

> [!decisão] Enxugado em 27/10 (eficiência primeiro)
> Cinco garantias em vez de oito; as contagens de protocolo vêm do manifesto do #142.

**Dono:** Pessoa A · **Prazo:** 28/10 (quarta) · **Esforço estimado:** ≈ 2 h · **Começa quando:** #142

1. Em `tests/test_regras_pessoa_a.py`, uma classe marcada `@pytest.mark.slow`; se o artefato não existir, `pytest.skip`.
2. Leia só `bloco_mestre`, `group_id`, `ano_internacao`, `alvo_obito_srag`.
3. Testes: (a) cada `group_id` em um único bloco; (b) 2020–2022 só em `test_pandemic`; (c) 2026 só em `exploracao`; (d) prevalência de cada bloco de 2019/2023–2025 a no máximo 0,5 ponto percentual de 8,44%; (e) SHA-256 do arquivo igual ao do manifesto (`src/utils/hashing.py`).
4. `.\.venv\Scripts\python.exe -m pytest -m slow tests/test_regras_pessoa_a.py -q` e cole a saída aqui.

**Se falhar:** não corrija o artefato; cole a falha no #142.

### ④ Pronto quando

- contem: `tests/test_invariantes_protocolo.py` :: `bloco_mestre` | tests/test_invariantes_protocolo.py tem os testes das invariantes do protocolo que leem a coluna bloco_mestre do artefato real (classe marcada como slow).
- contem: `tests/test_invariantes_protocolo.py` :: `test_pandemic` | Há teste conferindo que 2020–2022 só aparecem no bloco test_pandemic.
- contem: `tests/test_invariantes_protocolo.py` :: `sha256` | Há teste conferindo que o SHA-256 do arquivo do artefato é igual ao registrado no manifesto (src/utils/hashing.py).
- teste: `tests/test_invariantes_protocolo.py` | Os testes rápidos de tests/test_invariantes_protocolo.py passam (os de artefato real são slow e não entram aqui).
- manual: | A saída de `.\.venv\Scripts\python.exe -m pytest -m slow tests/test_invariantes_protocolo.py -q`, rodada com o artefato real, foi colada como comentário neste card, sem falhas e sem skips das cinco garantias (grupo em um único bloco, 2020–2022 só em test_pandemic, 2026 só em exploracao, prevalência por bloco a no máximo 0,5 p.p. da média, SHA-256 igual ao manifesto).

## #132 · Regerar o artefato com as 30 variáveis e reexecutar C_11, C_12 e C_14 (o C_13 roda no #1)

- prioridade: P1
- situação: resolvida
- estratégia: desenvolver
- marco: M2
- data ideal: 03/11
- responsável: Pessoa C (1 h)
- pessoas: C
- fonte: Revisão de 03/11 (commit 9f3322b): manifesto_supervisionado.json de 03/11 04:20 UTC; 02_fluxo_e_estado §11.4
- depende de: #140
- tags: Notebook, Partição, Modelagem
- pilar: Eficiência + Valor científico-acadêmico
- carga: 1
- novo: não
- professores: não
- arquivos: notebooks/C/C_11_pipeline_supervisionado.ipynb, notebooks/C/C_12_baseline_logistica.ipynb, notebooks/C/C_14_ablacoes_variaveis.ipynb

### ① Para entender

O artefato supervisionado foi regerado em 03/11 às 04:20 UTC no desenho 70/15/15. As fichas da validação são as mesmas de antes (`val_ref` = 119.243 = 39.748 + 39.746 + 39.749) e treino e teste não mudaram, mas o `dataset_sha256` mudou (`4a8a775b…` → `53d48a3f…`), porque a coluna de partição mudou de rótulo.

Tudo o que foi calculado em 02/11 continua numericamente válido, mas aponta para o hash antigo. O C_16 só aceita um manifesto do C_15 com o hash atual, então a cadeia precisa rodar de novo, em ordem.

### ② Problema

- **C_11:** lê `split_partitions` com `expected_kind="final"`, mas está salvo **sem execução** (0 de 6 células).
- **C_12:** executado em 02/11 sobre o hash antigo (manifesto `C3_baseline_logistica_final_20261102T042124Z` diverge, §11.4 do pacote).
- **Lista de variáveis nova (#140):** o artefato precisa ser regerado para trocar `feature_columns` (30 variáveis, com saturação e desconforto) e guardar os três sintomas como auditoria. As fichas e os blocos não mudam.
- **C_14:** a saída salva ainda é da validação de 39.748 fichas; depois do #140 ele mede "P + 3 sintomas" e "P − gravidade" no `val_ref` inteiro.
- O C_13 não entra aqui: ele roda uma vez só, já com o G6 aprovado (#1).

### ③ O que fazer

**Dono:** Pessoa C · **Prazo:** 03/11, 9h45 às 10h45 · **Esforço:** ≈ 1 h (a maior parte é máquina) · **Começa quando:** #140

1. `git pull`. Regere o artefato e confira num comando (esperado: `119243 30 True False`, isto é, val_ref, número de variáveis, saturação dentro e fadiga fora):
```powershell
.\.venv\Scripts\python.exe -c "from pathlib import Path;import json;from src.data.supervised_artifact import gerar_artefato_supervisionado as g;g(Path('.'),cohort_kind='final',exportar_particao=True,overwrite=True);m=json.load(open('data/analytical/manifesto_supervisionado.json',encoding='utf-8'));print(m['partition_counts']['val_ref'],len(m['feature_columns']),'saturacao' in m['feature_columns'],'fadiga' in m['feature_columns'])"
```
2. Execute e salve os três, nesta ordem, num comando:
```powershell
foreach ($n in 'C_11_pipeline_supervisionado','C_12_baseline_logistica','C_14_ablacoes_variaveis') { .\.venv\Scripts\python.exe tools\medir_notebook.py "notebooks\C\$n.ipynb" --salvar-no-lugar --limite-mb 12288; if ($LASTEXITCODE) { break } }
```
3. No C_14, confira e cole no card: Δ PR-AUC de "P − gravidade" (esperado: negativo, perto de −0,02) e de "P + 3 sintomas" (esperado: perto de zero). Se "P + 3 sintomas" ganhar ≥ 0,005, avise a equipe antes do #1.
4. Commit: `chore: artefato com 30 variáveis; reexecuta C_11, C_12 e C_14 [done:#132]`. Avise a Pessoa C do #1 (é você mesma) e a Pessoa A.

### ④ Pronto quando

- json: `data/analytical/manifesto_supervisionado.json` :: `feature_columns` contem `saturacao` | O artefato regerado tem a saturação entre as variáveis do modelo.
- notebook-executado: `notebooks/C/C_11_pipeline_supervisionado.ipynb` | O C_11 foi executado no artefato novo e salvo com as saídas, sem erro gravado.
- notebook-executado: `notebooks/C/C_12_baseline_logistica.ipynb` | O C_12 foi reexecutado no artefato novo e salvo, sem erro gravado.
- notebook-executado: `notebooks/C/C_14_ablacoes_variaveis.ipynb` | O C_14 foi reexecutado e salvo, sem erro gravado.
- notebook-saida: `notebooks/C/C_14_ablacoes_variaveis.ipynb` :: `P_menos_gravidade` | A saída salva do C_14 mostra a linha sem saturação e desconforto.
- contem: `notebooks/C/C_14_ablacoes_variaveis.ipynb` :: `ablacoes_val_ref.csv` | O C_14 grava a tabela com o nome novo.

## #139 · Fase E: EDA descritiva na coorte definitiva (B_06 parte A apontando para coorte_final)

- prioridade: P1
- situação: resolvida
- estratégia: resolvida
- marco: M3
- data ideal: Concluído
- responsável: Pessoa A (executa com roteiro) · Pessoa B (revisa ao voltar)
- pessoas: B
- fonte: Replanejamento de 26/10; B_06 de 24/10; commit fd7dcaa (contrato temporal, dicionário e EDA)
- depende de: —
- tags: Dados/Coorte, Notebook, Metodologia
- pilar: Valor científico-acadêmico
- carga: 3
- novo: sim
- professores: não

### ① Para entender

A análise exploratória (EDA) do B_06 foi feita na coorte **provisória**. A definitiva tem 30.408 fichas a menos e regras novas (intervalos negativos e acima de 60 dias saíram). Os percentuais devem mudar pouco, mas "devem" não é "mudaram": é preciso **ver** a base nova antes de modelar.

| O que esta EDA responde | Por que importa antes do ajuste |
|---|---|
| Volume e mortalidade por ano mudaram com as regras novas? | Confirma a prevalência por bloco (≈ 8,44%) e por ano |
| O preenchimento por ano continua igual (inclusive os três sintomas de 2019)? | Alimenta a decisão do #50 |
| O intervalo sintomas → internação mudou de forma (agora entre 0 e 60)? | Variável numérica do modelo; muda a escala |
| As rupturas temporais (preenchimento, idade, vacinação) se mantêm? | Base da discussão de drift e do Teste B |

Só a **parte A** (tempo e descrição) é refeita aqui. Tabelas de óbito × cura vêm do #137 (só treino); o clustering vem do #136.

### ② Problema

Sem esta passagem, o ajuste e a validação partem de números descritivos de outra base, e o relatório misturaria as duas coortes.

### ③ O que fazer

> [!ok] Concluída pela Pessoa B em 27/10
> B_06 executado na coorte definitiva (3.884.728 linhas; `eda_02_resumo_fonte` = final), após a compatibilização das colunas derivadas. B_05 também reexecutado (as saídas tinham sido apagadas no commit `1cf3787`).

**Principais números na definitiva:** mortalidade 2019 12,0% · 2020 27,9% · 2021 28,1% · 2022 18,1% · 2023 9,4% · 2024 8,2% · 2025 7,2% · 2026 5,5%. Três sintomas em branco em 2019: perda de olfato e de paladar 99,7%, fadiga 99,5% (contra 19% a 32% em 2023–2025). Comorbidades em branco: 61% a 69% em 2023–2025 (gerou o #141). Clustering sem indicadores de ausência: silhueta 0,210 (núcleo), ARI 0,127 com a solução original, grupos fortemente ligados ao período.

O comparativo com a provisória foi dispensado: a definitiva é subconjunto da provisória (30.408 linhas a menos), e as diferenças não mudam nenhuma decisão.

### ④ Pronto quando

- notebook-executado: `notebooks/B/B_06_eda_temporal_clustering.ipynb` | O B_06 está salvo com todas as células de código executadas e nenhuma saída de erro.
- notebook-saida: `notebooks/B/B_06_eda_temporal_clustering.ipynb` :: `Tipo de coorte: final` | As saídas salvas do B_06 mostram que ele rodou sobre a coorte definitiva (linha "Tipo de coorte: final" impressa no início).
- notebook-saida: `notebooks/B/B_06_eda_temporal_clustering.ipynb` :: `coorte_final.parquet` | As saídas do B_06 mostram o caminho data/analytical/coorte_final.parquet como fonte lida.

## #140 · Aplicar a decisão de variáveis: entram saturação e desconforto respiratório, saem perda de olfato, perda de paladar e fadiga

- prioridade: P1
- situação: resolvida
- estratégia: desenvolver
- marco: M3
- data ideal: 03/11
- responsável: Pessoa A (0,5 h) + Pessoa C (0,25 h)
- pessoas: A, C
- fonte: Alinhamento da equipe em 03/11; ablação do C_14 de 02/11; ficha do SIVEP-Gripe (definição de caso e campo 34); orientação de 24/10
- depende de: —
- tags: Decisão, Metodologia, Gate
- pilar: Valor científico-acadêmico
- carga: 0.75
- novo: não
- professores: não

### ① Para entender

A lista de variáveis do modelo foi decidida pela equipe em 03/11, antes do ajuste fino:

| Variável | Antes | Agora | Motivo |
|---|---|---|---|
| `saturacao`, `desc_resp` | só sensibilidade | **modelo principal** | fazem parte da definição de caso de SRAG hospitalizado e estão no campo 34 da ficha ("Sinais e Sintomas"), junto com febre e tosse; maior ganho das ablações (+0,0195 de PR-AUC) |
| `perd_olft`, `perd_pala`, `fadiga` | modelo principal | **fora** | campos da era COVID: 99,5% a 99,7% em branco em 2019; marcam o período; retirá-los não custou desempenho |

O modelo passa de 31 para 30 variáveis. A sensibilidade "sem saturação e desconforto" deixa de existir (o C_14 mostra a linha "P − gravidade"), e os três sintomas ficam guardados no artefato só para a linha "P + 3 sintomas". Este card absorveu as ablações (#54) e a decisão dos três sintomas (#50).

### ② Problema

> [!decisão] Alinhamento de 03/11 · versão 3.4
> O professor pediu para estudar os três sintomas e tirar se ficassem "muito determinísticos" (orientação de 24/10). A ablação de 02/11 é o estudo: o critério de desempenho registrado na §29.19 (ROC-AUC de 2019 subir ≥ 0,01) **não** foi atingido, então a retirada é registrada como decisão de **validade** (marcador de período), com a mudança de critério declarada na §29.34.

Resultado de 02/11 (diferença contra a lista anterior P, 31 variáveis; validação de 39.748 fichas):

| Linha | Família | Δ PR-AUC | Δ ROC-AUC |
|---|---|---|---|
| Sem os 3 sintomas | logística / boosting | −0,0002 / −0,0004 | −0,0003 / −0,0004 |
| Comorbidades recodificadas (`fator_risc`) | logística / boosting | 0,0000 / 0,0000 | 0,0000 / 0,0000 |
| + gravidade (saturação, desconforto) | logística | +0,0195 | +0,0088 |
| + contexto (escolaridade, vacina) | logística | +0,0033 | +0,0018 |
| + região | logística | +0,0033 | +0,0012 |

O que muda no código (o script `aplicar_decisoes_03_11.py --variaveis` faz tudo, com conferência de cada troca):
- `configs/supervised.yaml`: listas `categoricas` e `final`; `sensibilidade_gravidade_admissao: []`; nova chave `sensibilidade_marcador_periodo`; `sensibilidades.sem_saturacao_desc_resp.ativa: false`; texto do G1.
- `configs/feature_contract_v1.json`: as mesmas listas.
- `src/data/supervised_artifact.py`: uma linha para guardar `sensibilidade_marcador_periodo` como coluna de auditoria (senão o C_14 não acha os três sintomas).
- C_14: "P − 3 sintomas" vira "P + 3 sintomas" e "P + gravidade" vira "P − gravidade"; a tabela passa a se chamar `ablacoes_val_ref.csv`.
- `docs/decisoes.md`: entrada 29.34 e um aviso nas §13 e §29.19.

O efeito **exatamente nulo** da recodificação continua suspeito e é conferido no passo 1.

### ③ O que fazer

**Dono:** Pessoa A (script e registro) + Pessoa C (conferência do `fator_risc`) · **Prazo:** 03/11, 9h às 9h45 · **Começa quando:** já (é o primeiro card do dia: o #132 regera o artefato com a lista nova)

1. **Conferir a recodificação (C, 10 min).** O Δ exatamente zero pode ser real (nenhum branco com `fator_risc = 2`) ou efeito colateral de `copy(deep=False)` com `.loc`. Conte os casos que a regra mudaria:
```powershell
.\.venv\Scripts\python.exe -c "from pathlib import Path;import pandas as pd;from src.data.supervised_artifact import load_supervised_artifact as L;df,_=L(Path('.'),expected_kind='final',partitions=('train_ref',));f=df['fator_risc'].astype('string').str.strip().isin(['2','2.0']);print(pd.__version__,{c:int(((df[c].isna())|(df[c].astype('string').str.strip()=='')).__and__(f).sum()) for c in ['cardiopati','diabetes','obesidade','asma','renal','puerpera']})"
```
   Todas 0: a regra não tem o que mudar nesta coorte (é esse o motivo a registrar). Alguma > 0: a recodificação também não entra agora (o ganho medido foi nulo e não há tempo para medir de novo); registre a contagem como limitação.
2. **Aplicar (A, 10 min).** Salve o `aplicar_decisoes_03_11.py` **fora** do repositório (por exemplo, em Documentos). Na raiz do projeto, simule e confira a lista de arquivos (são 5):
```powershell
.\.venv\Scripts\python.exe C:\caminho\aplicar_decisoes_03_11.py --variaveis --simular
```
   Se aparecer `PARADO`, nada foi gravado: me mande a linha. Se estiver certo, aplique e rode a suíte rápida num comando:
```powershell
.\.venv\Scripts\python.exe C:\caminho\aplicar_decisoes_03_11.py --variaveis; .\.venv\Scripts\python.exe -m pytest -m "not slow" -q
```
3. **Completar a §29.34 (A, 5 min).** No fim do `docs/decisoes.md`, troque a frase que começa com "PREENCHER" pelo resultado do passo 1 (contagens e "não adotada").
4. Commit: `feat: saturação e desconforto no modelo principal; sem os três sintomas da era COVID [done:#140]`. Avise a Pessoa C: o #132 começa já (regera o artefato).

### ④ Pronto quando

- yaml: `configs/supervised.yaml` :: `features.final` contem `saturacao` | A saturação está no modelo principal.
- yaml: `configs/supervised.yaml` :: `features.final` contem `desc_resp` | O desconforto respiratório está no modelo principal.
- yaml: `configs/supervised.yaml` :: `features.final` nao-contem `perd_olft` | A perda de olfato saiu do modelo principal (o mesmo vale para perd_pala e fadiga, retiradas juntas).
- yaml: `configs/supervised.yaml` :: `sensibilidades.sem_saturacao_desc_resp.ativa` = `false` | A sensibilidade sem saturação e desconforto foi desativada.
- contem: `src/data/supervised_artifact.py` :: `sensibilidade_marcador_periodo` | O artefato guarda os três sintomas como colunas de auditoria, para a linha "P + 3 sintomas" do C_14.
- contem: `docs/decisoes.md` :: `Ponto de decisão: lista de variáveis congelada` | O decisoes.md tem a entrada 29.34 com as duas decisões, os números da ablação e a definição de caso.
- nao-contem: `docs/decisoes.md` :: `PREENCHER com o resultado` | A conferência do fator_risc foi registrada na §29.34.
- teste: `tests/test_supervised_artifact.py` | Os testes do artefato passam com a lista nova.

## #72 · Quem é responsável pelos próximos passos (passagem de bastão de 24/10)

- prioridade: P1
- situação: resolvida
- estratégia: documentar
- marco: M0
- data ideal: 27/10
- responsável: Pessoa B (registra e comunica) + Equipe
- pessoas: B, Equipe
- fonte: Plano_Unificado_SRAG_3_Pessoas_v2.docx; Projeto
- depende de: —
- tags: Documentação
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1
- novo: não
- professores: não

### ① Para entender

O plano dava o caminho supervisionado à Pessoa C, mas a Pessoa B executou o B_07 e o B_10, e a Pessoa C os notebooks C_11 a C_16. A Pessoa A faz protocolo e auditoria. Falta registrar quem conduz ajuste fino, gates e relatório.

### ② Problema

A Pessoa B executou os B_07 e B_10, enquanto o plano atribui o caminho supervisionado à Pessoa C. A responsabilidade pelos próximos passos não está clara.

### ③ O que fazer

**Dono:** Pessoa B (registra) + Equipe · **Prazo:** 27/10 (atualizado) · **Esforço estimado:** ≈ 1 h

#### Objetivo
Deixar claro quem faz o quê de 27/10 a 03/11, para ninguém ficar parado esperando outra pessoa.

#### Princípios da distribuição
- **Um dono por arquivo e por notebook.** Quem não é dono comenta no card, não edita.
- **Carga estimada por pessoa.** Cada card traz as horas previstas; o total por pessoa está no quadro abaixo.
- **Toda tarefa entra na frente de quem recebe** (protocolo e verificação; análise e interpretação; código central e integração).

| Pessoa | Frente | Esforço estimado de 27/10 a 03/11 | Por dia útil (27–30/10) | Por dia de fim de semana e feriado (31/10–02/11) |
|---|---|---|---|---|
| A | Protocolo, decisões e configuração, garantias do artefato, perfil estatístico, métricas por grupo, completude, relatório | ≈ 38 h | ver tabela por dia | ver tabela por dia |
| B | Artefato no `src`, maior parte da exploração antes do treino, não supervisionado (K-Means e HCA), interpretação, seções do relatório e apresentação | ≈ 34 h | ver tabela por dia | ver tabela por dia |
| C | Leitura por bloco, cadeia C, ablações, região, ajuste, calibração, limiar, teste e bootstrap | ≈ 31 h | ver tabela por dia | ver tabela por dia |


> [!decisão] Enxugamento de 27/10 (noite)
> Cerca de 10 a 20 horas a menos por pessoa: sete cards de decisões e configuração viraram um só (#73); #10, #13, #22, #26, #40 e #11 foram absorvidos por outros cards; #84, #19 e #138 saíram para depois da entrega; ablações, ajuste, clustering, importância e reprodução ficaram menores.

> [!decisão] Replanejamento de 27/10 (revisão da tarde)
> 1. A geração do artefato de modelagem sai do notebook e vai para o `src` numa única função (#142, Pessoa B). O B_07 só chama a função e roda os pilotos.
> 2. A exploração antes do treino continua majoritariamente com a Pessoa B; a Pessoa A fica com 2019 mês a mês (#50) e completude (#52), e a Pessoa C com região no `val_tune` (#110). A Pessoa B ganha mais seções do relatório.
> 3. Ponto de decisão em 30/10 de manhã; ajuste em 30/10 à tarde; teste em 01/11 de manhã.

#### Carga estimada por dia (horas)
| Pessoa | 27/10 | 28/10 | 29/10 | 30/10 | 31/10 | 01/11 | 02/11 | Total |
|---|---|---|---|---|---|---|---|---|
| A | 5 | 6 | 4 | 5 | 6 | 5 | 7 | ≈ 38 |
| B | 5 | 6 | 5,5 | 2 | 4 | 8 | 4 | ≈ 34,5 |
| C | 3 | 5 | 5 | 6 | 6 | 3,5 | 2 | ≈ 30,5 |

#### O que muda de mãos (quadro oficial)
| Assunto | Dono | Itens |
|---|---|---|
| Artefato de modelagem gerado pelo `src` e previsões do piloto | Pessoa B | #142 |
| Exploração antes do treino: desfecho no treino, não supervisionado (K-Means e HCA), subgrupos, completude | Pessoa B | #51, #136, #55, #52 |
| Exploração antes do treino: fator de risco, 2019 mês a mês, perfil estatístico, métricas por grupo | Pessoa A | #141, #50 (dados), #137, #23 |
| Exploração antes do treino: região no `val_tune`, ablações | Pessoa C | #110, #54 |
| Leitura por bloco, cadeia C, ajuste, calibração, limiar, teste, bootstrap | Pessoa C | #131, #132, #1, #5, #78, #79, #80, #2, #119, #127 |
| Invariantes, checklist do G9, decisões e configuração (pacote único), dicionário e variáveis finais, âncora e excluídos, falsos negativos | Pessoa A | #135, #81, #73, #70, #56, #55 (parte) |
| Limpeza mínima do repositório | Pessoas A, B e C (cada uma os próprios arquivos) | #143 |
| Relatório e reprodução independente | Pessoa A (seções de EDA, não supervisionado e interpretação: Pessoa B; conferência: Pessoa C) | #133, #126 |
| Interpretação, literatura, apresentação | Pessoa B | #91, #57, #112, #134 |
| Ponto de decisão | Equipe (conduz: Pessoa A) | #140 |

#### Como decidir rápido
Pergunta binária no card do item, com prazo. Sem resposta em 24 h, vale o padrão escrito no próprio card. O G9 é aprovado por mensagem.

#### Pronto quando
O quadro estiver publicado e as três pessoas tiverem comentado "ok" no card.

### ④ Pronto quando

- manual: | O quadro de responsáveis e de carga por dia está publicado neste card e as três pessoas (A, B e C) comentaram "ok" concordando com a divisão.

## #82 · Decidir o que fazer com intervalos impossíveis entre sintomas e internação

- prioridade: P2
- situação: resolvida
- estratégia: resolvida
- marco: M1
- data ideal: Concluído
- responsável: Pessoa A (dona; revisão cruzada sem edição concorrente)
- pessoas: A
- fonte: configs/supervised.yaml (features.engenharia.intervalo_politica); docs/decisoes.md
- depende de: #73
- tags: Decisão, Features, Dados/Coorte
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 0
- novo: não
- professores: não

### ① Para entender

A variável `dias_sintomas_ate_internacao` mede quantos dias se passaram entre os primeiros sintomas e a internação. Às vezes o número é **negativo** (internou antes dos sintomas) ou passa de **60 dias**.

<div class="kpi">
<div><b>24.340</b>internações antes dos sintomas (0,56%)</div>
<div><b>40.824</b>intervalos fora da janela (0,94%)</div>
</div>

Duas opções: **sinalizar** (manter o número e criar uma bandeira) ou **descartar** (virar vazio). Hoje vale "sinalizar", mas a bandeira não entra no modelo (item 12).

### ② Problema

Falta decidir como tratar intervalos entre sintomas e internação negativos ou acima de 60 dias: manter o valor bruto e sinalizar (`sinalizar`) ou transformar em ausente (`descartar`). A implementação do item 12 e a lista final de features do G1 dependem dessa escolha.

### ③ O que fazer

> [!decisão] Enxugado em 27/10 (eficiência primeiro)
> Feito dentro do **#73** (Pessoa A). Marque como concluído junto com ele.

### ④ Pronto quando

- contem: `configs/final_cohort_v1.yaml` :: `intervalo_sintomas_negativo` | O contrato da coorte definitiva tem a regra que exclui intervalos sintomas → internação negativos.
- contem: `configs/final_cohort_v1.yaml` :: `intervalo_sintomas_maior_limite` | O contrato da coorte definitiva tem a regra que exclui intervalos acima do limite de 60 dias.

## #83 · Definir o que a sensibilidade "com e sem indicadores de ausência" vai comparar

- prioridade: P3
- situação: aberta
- estratégia: documentar
- marco: M1
- data ideal: 01/11
- responsável: Pessoa A · revisão: Pessoa C
- pessoas: A
- fonte: configs/supervised.yaml (sensibilidades.com_sem_indicadores_ausencia); docs/decisoes.md
- depende de: #73
- tags: Decisão, Metodologia, Features
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 0
- novo: não
- professores: não

### ① Para entender

No modelo, um campo em branco vira a categoria `AUSENTE`. Na prática, isso já é um "indicador de ausência". Por isso a comparação "com e sem indicadores" prevista no YAML não compara nada hoje.

> [!exemplo] Exemplo
> Duas fichas iguais: uma com diabetes "não", outra em branco. O modelo vê `diabetes_nao` e `diabetes_AUSENTE` como coisas diferentes, e aprende com essa diferença.

Isso importa porque, no clustering, a ausência foi o que mais separou os grupos (item 52).

### ② Problema

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que esta pendência está aberta
> A auditoria automática do painel (27/10, 14:40) marcou este item como resolvido com base em commits de 09 e 10/10, todos anteriores às revisões de 24 e 26/10 e sem relação com a entrega descrita aqui. Isso acontece por um defeito do painel: a cada auditoria, um commit antigo ainda não rejeitado reabre a sugestão (detalhes no #94).
> A sensibilidade continua ligada no YAML (ver #11). Fecha junto com o #73.

Falta definir o que a sensibilidade de ausência vai comparar, já que a categoria `AUSENTE` já leva a informação de ausência ao modelo principal. Sem essa definição, o item 11 não pode ser implementado.

### ③ O que fazer

> [!decisão] Enxugado em 27/10 (eficiência primeiro)
> Feito dentro do **#73** (Pessoa A). Marque como concluído junto com ele.

### ④ Pronto quando

- yaml: `configs/supervised.yaml` :: `sensibilidades.com_sem_indicadores_ausencia.ativa` = `false` | A sensibilidade "com e sem indicadores de ausência" foi desligada no supervised.yaml, porque a categoria AUSENTE já leva a informação de ausência ao modelo principal (substituída pela análise de completude do #52).
- contem: `docs/decisoes.md` :: `indicadores de ausência` | O docs/decisoes.md registra a decisão sobre os indicadores de ausência (desligados) e o motivo.

## #84 · Definir quais doses de vacina contam como anteriores à internação

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 05/11
- responsável: Pessoa A (regra e derivação) · revisão: Pessoa C
- pessoas: A
- fonte: docs/decisoes.md §17; configs/dicionario_variaveis_v1.csv
- depende de: —
- tags: Decisão, Features, Dados/Coorte
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: —
- novo: não
- professores: não
- removido: removido na revisão de 03/11 (v3.2): vacina não está em features.final e ficou proibida na exploração do #155; limitação no #133

### ① Para entender

A vacina contra COVID só existe a partir de 2021, mas a base tem fichas de 2019 e 2020 marcadas como vacinadas. Também há doses sem data ou com data depois da internação.

<div class="bars">
<div class="br"><span class="y">2019</span><div class="t"><div class="b " style="width:2.0%"></div></div><span class="v">55 fichas</span></div>
<div class="br"><span class="y">2020</span><div class="t"><div class="b red" style="width:97.1%"></div></div><span class="v">24.284 fichas</span></div>
</div>

Sem uma regra, o campo `vacina_cov` marca mais o **ano** do que o paciente: o preenchimento dele muda 98 p.p. entre os anos.

### ② Problema

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que esta pendência está aberta
> A auditoria automática do painel (27/10, 14:40) marcou este item como resolvido com base em commits de 10 e 11/10, todos anteriores às revisões de 24 e 26/10 e sem relação com a entrega descrita aqui. Isso acontece por um defeito do painel: a cada auditoria, um commit antigo ainda não rejeitado reabre a sugestão (detalhes no #94).
> Não existe `derivar_vacina_cov_antes_admissao`. Continua pós-entrega (enxugamento de 27/10).

Falta a regra que define quais doses de vacina contam como anteriores à admissão, considerando os registros de vacina contra COVID-19 em 2019 e 2020 e as datas de dose ausentes ou posteriores à internação. A derivação do item 45 e a decisão do G1 sobre `vacina_cov` dependem dessa regra.

### ③ O que fazer

> [!decisão] Enxugado em 27/10 (eficiência primeiro)
> **Pós-entrega.** A ablação de contexto usa `vacina` como está; a qualidade da vacinação contra COVID-19 vira uma frase de limitação no relatório (#45).

### ④ Pronto quando

- define: `src/features/engineering.py` :: `derivar_vacina_cov_antes_admissao` | (Pós-entrega) Existe em src/features/engineering.py a função derivar_vacina_cov_antes_admissao, que só conta doses com data anterior à internação e trata 2019–2020 como sem vacina.
- manual: | A regra de quais doses contam como anteriores à internação está registrada no docs/decisoes.md §17, com data e motivo.

## #97 · Fechar o "assunto da entrega do professor"

- prioridade: P1
- situação: parcial
- estratégia: documentar
- marco: M0
- data ideal: 27/10
- responsável: Pessoa A
- pessoas: A
- fonte: Reunião de 16/10
- depende de: —
- tags: —
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1
- novo: não
- professores: não

### ① Para entender

Na reunião de 16/10, foi sugerido fazer o trabalho de um dos professores juntos e entregar separado, porque ele tem 13 alunos. A transcrição não deixa claro o que precisa ser entregue nem se ficou decidido.

### ② Problema

> [!atenção] Reaberto em 01/11 (revisão de volatilidade)
> Fechado sem nenhuma resposta registrada. O padrão do card cita a entrega em 03/11 e a tag `entrega-2026-11-03`; o plano usa 04/11 e `entrega-2026-11-04`. Se você já tem as respostas, cole-as e conclua.
> O comentário de 01/11 deste card tem o motivo completo, o que pode mudar, o que continua válido, de que depende e como concluir de novo.

Não há registro do que é a entrega, do prazo nem da forma (individual ou em grupo).

### ③ O que fazer

> [!ok] Respondido na orientação de 24/10
> Entrega com o modelo de um projeto de semestre anterior no GitHub (notebooks, código e resultados, sem formato rígido) e **apresentação em PowerPoint ou Canva** para explicar o trabalho a colegas que não o conhecem.

**O que ainda falta confirmar (Pessoa A, por mensagem ao professor ou na próxima aula, até 27/10):**
1. Data e hora exatas. Na transcrição aparece "até o dia 7"; o planejamento continua com **03/11**. Se for outra data, só o cronograma muda.
2. Canal de envio (AVA, e-mail ou link do GitHub).
3. Se há relatório escrito separado da apresentação e, se houver, com que modelo e tamanho.
4. Duração da apresentação e se é ao vivo.

**Padrão enquanto não houver resposta:** relatório em PDF no roteiro TRIPOD, apresentação de 15 minutos, repositório com a marcação `entrega-2026-11-03`.

**Pronto quando:** as quatro respostas estiverem neste card e o #133 e o #134 ajustados.

### ④ Pronto quando

- manual: | As quatro respostas do professor (data e hora da entrega, canal de envio, se há relatório escrito separado e duração da apresentação) estão registradas como comentário neste card.
- manual: | O #133 (relatório) e o #134 (apresentação) foram ajustados ao formato informado, ou foi registrado neste card que o padrão (PDF TRIPOD, 15 minutos, tag entrega-2026-11-03) continua valendo.
- manual: | Reconfirmado: as quatro respostas (data e hora, canal, relatório separado e duração) estão registradas em comentário, ou foi registrado que vale o padrão atualizado (PDF TRIPOD, 15 minutos, tag entrega-2026-11-04, data 04/11), e o #133 e o #134 foram avisados.

## #102 · Desenho temporal: os YAMLs tiraram 2019 do desenvolvimento sem registro — decidir e alinhar tudo

- prioridade: P1
- situação: aberta
- estratégia: documentar
- marco: M2
- data ideal: 28/10
- responsável: Equipe (decide) · Pessoa A (registra) · Pessoa C (código e testes)
- pessoas: A, C, Equipe
- fonte: configs/decisoes.yaml v0.4
- depende de: —
- tags: Decisão, Documentação
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1
- novo: sim
- professores: não

### ① Para entender

> [!ok] Decisão fechada em 18/10
> A coorte definitiva inicial será a seleção de features da coorte provisória. O treino principal usará exclusivamente 2019, 2023, 2024 e 2025. Haverá duas janelas de teste: (A) 2019, 2023, 2024 e 2025; (B) 2019 a 2025, incluindo 2020–2022. O ano de 2026 não participa do desenvolvimento nem dos testes principais e fica apenas como exploração opcional, depois de todo o restante concluído.

O YAML canônico não pode continuar anunciando 2019–2026 ou um único holdout 70/15/15. Ele deve declarar explicitamente os blocos e anos da decisão atual.

### ② Problema

> [!decisão] Decisão de 01/11 (equipe, informada pela Pessoa B): Opção A
> 2019 permanece no desenvolvimento (train_ref, val_tune, val_cal, val_meas e test_ref) e fica fora do `test_pandemic` (só 2020 a 2022). É o padrão deste card e o que o `docs/decisoes.md` §29.25 (29/10) já registra, com os YAMLs alinhados. O card só fecha com a suíte rápida sem as 4 falhas (#144, agora da Pessoa B) e o registro da confirmação de 01/11 no pacote do #73 (Pessoa A).

> [!atenção] Revisão de 28/10 (commit `032a5b65`): divergência grave, bloqueia o #142 e o treino
`configs/supervised.yaml` e `configs/decisoes.yaml` (versão 0.5) passaram a dizer que o desenvolvimento usa só 2023–2025 e que 2019 vai para `test_pandemic` junto com 2020–2022 (`periodo.desenvolvimento`, `temporal.blocos.*.anos`, `dev_years`, `pandemic_test_years` e a descrição do G2). Todo o resto do projeto continua com 2019 no desenvolvimento: `docs/decisoes.md` §5 e §28, a Base de Conhecimento v10, este painel, o teste `tests/test_split.py` (`TEMPORAL_CFG`), as saídas salvas do B_07 e o artefato atual (`manifesto_supervisionado.json`: teste = 3.035.074 linhas = `test_ref` + 2020–2022). A mudança não está registrada como decisão e o G2 continua com a data de aprovação de 18/10.

| Onde | 2019 está em | Situação |
|---|---|---|
| `configs/supervised.yaml` (`periodo`, `temporal.blocos`, descrição do G2) | `test_pandemic` (Teste B) | Mudou depois de 24/10 |
| `configs/decisoes.yaml` v0.5 (`dev_years`, `pandemic_test_years`, `experimentos_split.blocos`) | `test_pandemic` | Mudou depois de 24/10 |
| `docs/decisoes.md` §5.1, §28 (decisão de 18/10) | desenvolvimento | Sem alteração |
| Base de Conhecimento v10, este painel (#50, #140, #142) | desenvolvimento | Sem alteração |
| `tests/test_split.py` (`TEMPORAL_CFG`) | desenvolvimento | Passa porque usa a própria configuração |
| Artefato atual (`manifesto_supervisionado.json`, 24/10) e saídas do B_07 | desenvolvimento | Gerados antes da mudança |

**Consequências se a mudança ficar como está:** o Teste A deixa de ter 2019; o `test_pandemic` passa a misturar um ano pré-pandemia (12% de óbitos) com 2020–2022 (≈ 26%), e o nome do bloco fica enganoso; o treino perde ~43 mil fichas de 2019; a partição muda e todos os números de 24/10 deixam de valer; a pergunta do #50 (três sintomas vazios em 2019) muda de natureza. A mudança pode até ser boa (resolve o "marcador de ano" sem tirar variáveis), mas precisa ser uma decisão registrada.

**Teste quebrado na mesma região do código:** em `src/protocolo/verificacoes.py` (`DEFAULT_CONFIG.experimentos_split.cenarios`), o cenário `sem_2020_2021` foi renomeado para `sem_2019_2022`, com `anos: [2019, 2022, 2023, 2024, 2025]` e descrição "Remove 2019, 2020, 2021 e 2022" — a lista contradiz a descrição (mantém 2019 e 2022). Três testes de `tests/test_regras_pessoa_a.py` falham de forma determinística (`test_cenario_sem_2020_2021_exclui_os_anos` com `KeyError: 'sem_2020_2021'`; `test_benchmark_aleatorio_x_temporal_e_comparacao` e `test_graficos_do_split_sao_gerados` com nomes diferentes), porque o fixture usa `load_config(None)`, que lê só o `DEFAULT_CONFIG`. A auditoria de 27/10 registrou "testes ok" no commit `35b90f8`; confirme rodando a suíte na sua máquina.

Dois arquivos de configuração e a documentação contam histórias diferentes; a banca e outra IA não saberão qual vale.

### ③ O que fazer

**Dono:** Equipe decide (quem alterou os YAMLs explica o motivo no card) · Pessoa A registra · Pessoa C ajusta código e testes · **Prazo:** 28/10 (quarta), antes do #142 · **Esforço estimado:** A ≈ 30 min · C ≈ 30 min

#### 1. Decidir (15 min, por mensagem)
Opção A — **voltar ao desenho de 18/10** (2019 no desenvolvimento): desfazer as mudanças de `periodo`, `temporal.blocos`, descrição do G2 no `supervised.yaml` e `dev_years`/`pandemic_test_years`/`experimentos_split.blocos` no `decisoes.yaml`. Nada mais muda.
Opção B — **manter 2019 fora do desenvolvimento**: registrar a decisão nova (data, motivo, impacto) no `decisoes.md` §5 e §28; atualizar a descrição e a data de aprovação do G2; renomear ou documentar `test_pandemic` (passa a ter 2019, que não é pandemia); atualizar `TEMPORAL_CFG` em `tests/test_split.py`; refazer #50 e #140 com a nova leitura; avisar que todos os números de 24/10 mudam.

Padrão se não houver resposta até 28/10 às 14h: **Opção A** (é o que está aprovado e documentado).

#### 2. Corrigir o cenário quebrado (Pessoa C, 15 min)
Em `src/protocolo/verificacoes.py`, no `DEFAULT_CONFIG`, voltar a chave para `"sem_2020_2021"` com `"anos": [2019, 2022, 2023, 2024, 2025]` e `"descricao": "Remove 2020 e 2021 (anos de pandemia)"` — ou, se o A_09 sair no #143, remover o cenário e os três testes juntos. Rodar `.\.venv\Scripts\python.exe -m pytest tests/test_regras_pessoa_a.py -q`.

#### 3. Registrar (Pessoa A, no pacote do #73)
Uma entrada no `decisoes.md` com a opção escolhida.

#### Pronto quando
Os dois YAMLs, `decisoes.md`, `tests/test_split.py` e este painel dizem o mesmo sobre 2019, e a suíte rápida passa.

### ④ Pronto quando

- yaml: `configs/supervised.yaml` :: `temporal.blocos.train_ref.anos` contem `2019` | Opção A (padrão sem resposta até 28/10, 14h): o train_ref do supervised.yaml volta a ter 2019, como na decisão de 18/10. Se a equipe escolher a Opção B, troque este critério por `nao-contem 2019` e registre a decisão.
- yaml: `configs/supervised.yaml` :: `temporal.blocos.test_pandemic.anos` nao-contem `2019` | Opção A: test_pandemic volta a ter só 2020–2022 (nome do bloco coerente com o conteúdo).
- yaml: `configs/decisoes.yaml` :: `dev_years` contem `2019` | O configs/decisoes.yaml diz o mesmo que o supervised.yaml sobre 2019 (dev_years com 2019 na Opção A).
- contem: `docs/decisoes.md` :: `2019` | O docs/decisoes.md (§5 e §28) registra a decisão sobre 2019, com data e motivo, coerente com os dois YAMLs.
- nao-existe: `src/protocolo/verificacoes.py` | O fluxo A (onde ficavam o DEFAULT_CONFIG e o cenário contraditório sem_2019_2022) foi removido no #154: o desenho temporal agora só existe nos YAMLs conferidos acima.
- teste: `tests/test_split.py` | Os testes de partição passam com o TEMPORAL_CFG coerente com a decisão sobre 2019.

## #30 · Salvar a coorte definitiva com o nome errado a carregaria como provisória

- prioridade: P3
- situação: aberta
- estratégia: desenvolver
- marco: M0
- data ideal: 31/10
- responsável: Pessoa C (0,25 h)
- pessoas: C
- fonte: src/data/cohort_source.py
- depende de: —
- tags: Código, Dados/Coorte
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 0.25
- novo: não
- professores: não

### ① Para entender

> [!ok] Decisão fechada em 18/10
> A coorte definitiva inicial será a seleção de features da coorte provisória. O treino principal usará exclusivamente 2019, 2023, 2024 e 2025. Haverá duas janelas de teste: (A) 2019, 2023, 2024 e 2025; (B) 2019 a 2025, incluindo 2020–2022. O ano de 2026 não participa do desenvolvimento nem dos testes principais e fica apenas como exploração opcional, depois de todo o restante concluído.

> [!decisão] Decisão de 18/10
> Ao declarar a provisória como definitiva (item 44), salvar uma cópia como `coorte_final.parquet` para que `cohort_source` a reconheça.

`cohort_source` reconhece como definitiva só `coorte_final.parquet`. Se alguém salvar a coorte definitiva como `coorte.parquet`, ela será tratada como provisória sem aviso.

### ② Problema

> [!atenção] Replanejamento de 31/10 · versão 2 (entrega em 04/11)
> Sábado, 10 minutos da Pessoa C (junto com o #143). O `manifesto_supervisionado.json` grava `cohort_kind: final` e a origem (`source.sha256` = `87f28d39…`, 3.884.728 linhas). Falta só **confirmar e concluir** com um comentário.

`cohort_source` trata `coorte.parquet` como coorte provisória. No B_06, esse mesmo nome era usado como coorte "oficial". Se a coorte definitiva for salva com esse nome, será carregada como provisória.

### ③ O que fazer

**Pessoa C, 31/10, 10 min:** confira (a) `src/data/cohort_source.py` reconhece só `coorte_final.parquet` como definitiva; (b) o manifesto do artefato tem `cohort_kind: final` e o SHA-256 da origem; (c) `.\.venv\Scripts\python.exe -m pytest tests/test_cohort_source.py -q` passa. Marque como concluído com um comentário curto.

### ④ Pronto quando

- contem: `src/data/cohort_source.py` :: `coorte_final.parquet` | O cohort_source reconhece a coorte definitiva pelo nome canônico coorte_final.parquet.
- teste: `tests/test_cohort_source.py::test_explicit_path_com_nome_ambiguo_e_rejeitado` | O teste confirma que coorte.parquet não é mais candidato, então a definitiva nunca é carregada como provisória por causa do nome.

## #59 · Documentar 2026 como período parcial e exclusivamente exploratório

- prioridade: P3
- situação: aberta
- estratégia: documentar
- marco: M1
- data ideal: 01/11
- responsável: Pessoa A (dona; revisão cruzada sem edição concorrente)
- pessoas: A
- fonte: Projeto (relatório)
- depende de: #73
- tags: Metodologia, Documentação, Dados/Coorte
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 0
- novo: não
- professores: não

### ① Para entender

> [!ok] Decisão fechada em 18/10
> A coorte definitiva inicial será a seleção de features da coorte provisória. O treino principal usará exclusivamente 2019, 2023, 2024 e 2025. Haverá duas janelas de teste: (A) 2019, 2023, 2024 e 2025; (B) 2019 a 2025, incluindo 2020–2022. O ano de 2026 não participa do desenvolvimento nem dos testes principais e fica apenas como exploração opcional, depois de todo o restante concluído.

2026 só vai até setembro, e cerca de 12% dos desfechos ainda estão em aberto. Na reunião de 16/10, o time combinou deixar 2026 fora do treino, mas isso ainda não foi aplicado (item 85).

<div class="kpi">
<div><b>5,6%</b>mortalidade 2026 (parcial)</div>
<div><b>7,3%</b>mortalidade 2025</div>
</div>

### ② Problema

Agosto de 2026 pode estar subnotificado por atraso de notificação. 2026 está incompleto, com cerca de 12% dos desfechos ainda pendentes.

### ③ O que fazer

> [!decisão] Enxugado em 27/10 (eficiência primeiro)
> Feito dentro do **#73** (Pessoa A). Marque como concluído junto com ele.

### ④ Pronto quando

- yaml: `configs/supervised.yaml` :: `periodo.exploracao_opcional` contem `2026` | O supervised.yaml declara 2026 só como exploração opcional, fora do desenvolvimento e dos testes.
- contem: `docs/decisoes.md` :: `parcial` | O docs/decisoes.md registra que 2026 é período parcial (até setembro, com desfechos em aberto) e exclusivamente exploratório (feito no pacote do #73).

## #73 · decisoes.md coerente com o desenho final: registros 29.34 a 29.38 e histórico marcado

- prioridade: P1
- situação: parcial
- estratégia: documentar
- marco: M6
- data ideal: 05/11
- responsável: Pessoa A (1 h)
- pessoas: A
- fonte: docs/decisoes.md no commit 9f3322b; revisão de 03/11
- depende de: #153
- tags: Documentação, Decisão
- pilar: Documentação + Valor científico-acadêmico
- carga: 1
- novo: não
- professores: não
- arquivos: docs/decisoes.md

### ① Para entender

O `decisoes.md` é o registro que a banca pode ler para entender cada escolha. Ele já vai até a §29.33 (70/15/15), mas as seções normativas e as entradas novas precisam fechar com o que o código faz no dia da entrega.

### ② Problema

> [!decisão] Estado em 03/11
> O script `limpar_rastros.py` já tirou o "Responsável pelo registro", reescreveu a §21 e a §23, ajustou a §7 e a §29.24 e marcou como histórico as §29.4, 29.12, 29.16, 29.17, 29.19, 29.21 e 29.22. A §29.34 (variáveis) existe e a conferência do `fator_risc` está registrada. A §29.7 já descreve a ANOVA.

Falta:
- as entradas **29.35** (G6), **29.36** (G7 e G8), **29.37** (exploração) e **29.38** (hipóteses e abertura do teste): cada card do caminho crítico escreve a sua, e este card confere o conjunto;
- um acréscimo à §29.34 com a reexecução no `val_ref` (os números de hoje) e a frase do G1;
- a §29.9 ("Pendente: a Pessoa C escreve uma linha no card…"), que ainda tem linhas "aguardando a Pessoa C" para G6, G7 e G8: desatualizada;
- as onze menções restantes a "Pessoa A/B/C" (por exemplo, "Decidiu: Pessoa A"): decidir se ficam em entradas históricas ou viram "a equipe".

### ③ O que fazer

**Dono:** Pessoa A · **Prazo:** o acréscimo à §29.34 e a §29.9 em 03/11, 16h30; as entradas novas conforme cada card; conferência final em 05/11, 10h (depois do #2) · **Começa quando:** já

1. **§29.34 (A, 10 min).** Acrescente ao fim da entrada:
   - "Reexecução no `val_ref` (03/11, C_14, 30 variáveis, hiperparâmetros padrão): `P + 3 sintomas` Δ PR-AUC +0,0001 (logística) e −0,0005 (boosting); `P − gravidade` −0,0170 (logística); recodificação por `fator_risc` 0,0000 nas duas famílias, coerente com zero casos."
   - "Esta decisão reabre o G1 (aprovado em 22/10) apenas para a lista de variáveis, por falha material (marcador de período), como previsto na §29.19. Com a lista de 30 variáveis, o G1 volta a aprovado."
2. **§29.9 (A, 5 min).** Troque o conteúdo por "Resolvido: ver §29.34 a §29.38" (as linhas "aguardando a Pessoa C" não valem mais).
2b. **§29.8, corte por região (A, 5 min).** Acrescente à entrada "29.8 24/10 · Geografia como separação da análise (#110)" um item: "- **Atualização de 03/11: versão mínima do corte por região.** O professor sugeriu, em 24/10, um modelo único com ponto de corte por região. Foi implementada só a versão mínima: modelo único, corte global e métricas e calibração por região no teste. O corte regional não foi implementado, por falta de tempo antes do teste, e fica como trabalho futuro. A tabela por região mostra a diferença de sensibilidade entre regiões que ele tentaria corrigir."
3. **Menções a pessoas (A, 5 min).** Liste com `git grep -n "Pessoa [ABC]" docs/decisoes.md` e troque por "a equipe" onde a pessoa não for necessária.
4. **Entradas 29.35 a 29.38:** cada card escreve a sua (#1: 29.35; #79: 29.36; #155: 29.37; #161 e #2: 29.38).
5. **05/11, 10h:** confira que as entradas 29.34 a 29.38 existem, em ordem, e que cada número citado bate com a saída salva do notebook correspondente.
6. Commit: `docs: decisoes.md coerente com o desenho final [done:#73]`.

### ④ Pronto quando

- contem: `docs/decisoes.md` :: `29.34` | A entrada do ponto de decisão (#140) existe.
- contem: `docs/decisoes.md` :: `29.35` | A entrada do G6 (#1) existe.
- contem: `docs/decisoes.md` :: `29.36` | A entrada do G7 e do G8 (#79) existe.
- contem: `docs/decisoes.md` :: `29.37` | A entrada da exploração de hiperparâmetros (#155) existe.
- contem: `docs/decisoes.md` :: `29.38` | A entrada das hipóteses e da abertura do teste (#161 e #2) existe.
- contem: `docs/decisoes.md` :: `Reexecução no` | A §29.34 traz a reexecução das ablações no val_ref e a frase do G1.
- nao-contem: `docs/decisoes.md` :: `aguardando a Pessoa C` | A §29.9 não tem mais linhas de espera desatualizadas.
- nao-contem: `docs/decisoes.md` :: `P + sazonalidade` | A §7 não promete mais uma ablação de sazonalidade que não foi feita.
- nao-contem: `docs/decisoes.md` :: `A_15_fator_risco` | O decisoes.md não cita mais o notebook auxiliar retirado do pacote.
- contem: `docs/decisoes.md` :: `versão mínima do corte por região` | A §29.8 registra que o corte por região foi feito só na versão mínima e que o corte regional fica como trabalho futuro.

## #6 · Corrigir a chamada de criar_alvo_binario no B_07 (vai quebrar na coorte definitiva)

- prioridade: P1
- situação: resolvida
- estratégia: resolvida
- marco: M1
- data ideal: Concluído
- responsável: Pessoa B (dona; revisão cruzada sem edição concorrente)
- pessoas: B
- fonte: B_07_supervisionado_pilotos (seção 4); src/models/pipeline.py (criar_alvo_binario)
- depende de: —
- tags: Código, Notebook, Dados/Coorte
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 5
- novo: não
- professores: não

### ① Para entender

Se a coorte não trouxer a coluna do alvo pronta, o B_07 cria o alvo chamando `criar_alvo_binario` com dois argumentos que a função **não aceita**. Hoje não dá erro porque a coorte provisória já traz o alvo. Na definitiva, pode trazer só a `evolucao` bruta, e aí a célula para com `TypeError`.

> [!exemplo] Exemplo
> É uma porta que nunca foi aberta: está trancada, mas ninguém percebeu porque sempre entraram pela outra. O relatório automático marcou isso como alerta alto (A1).

### ② Problema

Quando a coorte não traz `alvo_obito_srag`, o B_07 chama `criar_alvo_binario` com os parâmetros `ignorados=` e `descartar_nao_rotulados=`. A função só aceita `alvo`, `positivos` e `negativos`. Hoje o erro não aparece porque a coorte provisória já traz o alvo pronto. Com uma coorte definitiva sem essa coluna, a célula falha com `TypeError`.

### ③ O que fazer

> [!ok] Concluída (confirmada no painel)
> A chamada foi corrigida no commit `a913228` (18/10).

**Leitura atual:** o B_07 passa a ser histórico da fase provisória (ver #72). A coorte definitiva já traz `alvo_obito_srag` pronto (`int8`, valores 0 e 1, validado na publicação), então o caminho oficial não chama mais `criar_alvo_binario` a partir do B_07. Nada a fazer.

### ④ Pronto quando

- nao-contem: `notebooks/B/B_07_supervisionado_pilotos.ipynb` :: `descartar_nao_rotulados=` | O B_07 não chama mais criar_alvo_binario com o parâmetro descartar_nao_rotulados=, que a função não aceita.
- nao-contem: `notebooks/B/B_07_supervisionado_pilotos.ipynb` :: `ignorados=` | O B_07 não chama mais criar_alvo_binario com o parâmetro ignorados=.

## #86 · Levar a partição por hash do notebook para src/data/split.py

- prioridade: P1
- situação: resolvida
- estratégia: resolvida
- marco: M1
- data ideal: Concluído
- responsável: Pessoa C (dona; revisão cruzada sem edição concorrente)
- pessoas: C
- fonte: notebooks/B/B_07 (seção 8); src/data/split.py; tests/test_split.py
- depende de: —
- tags: Código, Partição, Testes
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 5
- novo: não
- professores: não

### ① Para entender

A função que faz a partição oficial (`atribuir_particao_estratificada_por_hash`) está escrita **dentro do B_07**. O `src/data/split.py` ainda tem a função antiga, lenta e estratificada só pelo alvo.

<div class="kpi">
<div><b>8,7 s</b>partição por hash na coorte real</div>
<div><b>> 10 min</b>função antiga</div>
<div><b>0,02 p.p.</b>desvio máximo por estrato</div>
</div>

Se alguém usar o `split.py` em outro notebook, vai gerar uma partição diferente da oficial.

### ② Problema

A partição oficial do projeto existe só no notebook B_07, junto com a conferência do manifesto, que também a recalcula. O `src/data/split.py` mantém `criar_particoes_agrupadas` (laços em Python, estratificada só por `target_column`). Não há teste automatizado para o método por hash.

### ③ O que fazer

> [!ok] Concluída
> `atribuir_particao_estratificada_por_hash` e `criar_particao_mestra` estão em `src/data/split.py`, com testes em `tests/test_split.py`.

**O que não está neste item, e sim no #131:** chamar `criar_particao_mestra` sobre a coorte definitiva e gravar o resultado. A função existe; o artefato particionado ainda não.

### ④ Pronto quando

- define: `src/data/split.py` :: `atribuir_particao_estratificada_por_hash` | A partição oficial por hash vive em src/data/split.py, e não só no notebook.
- define: `src/data/split.py` :: `criar_particao_mestra` | A função criar_particao_mestra existe em src/data/split.py.
- teste: `tests/test_split.py` | Os testes de partição (inclusive os de hash: grupos não cruzam partições, determinismo com linhas embaralhadas) passam.

## #87 · Os notebooks A e o B_07 gravam no mesmo arquivo e um apaga o outro

- prioridade: P3
- situação: parcial
- estratégia: desenvolver
- marco: M3
- data ideal: 31/10
- responsável: Pessoa B (dentro do #144)
- pessoas: B
- fonte: src/protocolo/verificacoes.py (a1_export_dataset, _analytical_path); notebooks A_03, A_04, A_14; configs/decisoes.yaml (dataset_analitico.path)
- depende de: #144
- tags: Diverge do decidido, Código, Dados/Coorte, Notebook
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 0
- novo: não
- professores: não

### ① Para entender

O A_03 e o A_04 exportam a população analítica para `data/analytical/dataset_supervisionado.parquet`. O B_07 grava o artefato oficial **no mesmo caminho**. Quem rodar por último vence.

<div class="flow"><span class="">A_03 grava v0.1</span><i>→</i><span class="">A_04 grava v1.0</span><i>→</i><span class="bad">B_07 sobrescreve</span><i>→</i><span class="">A_14 confere o hash → FALHA</span></div>

Se os notebooks A rodarem depois do B_07, o hash deixa de bater com o manifesto e o B_10 e todos os C param com "Hash do dataset supervisionado difere do manifesto".

> [!exemplo] Exemplo
> Duas pessoas salvando documentos diferentes com o mesmo nome na mesma pasta.

### ② Problema

> [!decisão] Replanejamento de 01/11
> O #144, em que este card está contido, passou para a Pessoa B. A parte do #73 continua com a Pessoa A.

> [!atenção] Replanejamento de 31/10 · versão 2 (entrega em 04/11)
> Replanejamento v2: este card é **resolvido dentro do card indicado em "responsável"**; sem esforço próprio. Marque como concluído junto com ele.

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que esta pendência está aberta
> A auditoria automática (27/10, 14:40) marcou "precisa revisão" por achados que não tratam deste item: a linha decorativa `=====` no cabeçalho de `src/protocolo/verificacoes.py` (lida como conflito de merge) e o `OneHotEncoder` denso do B_06, que roda numa amostra de 80 mil fichas e será substituído pelo #136 (detalhes no #94).
> O problema real continua: `configs/decisoes.yaml` `dataset_analitico.path` e o `DEFAULT_CONFIG` de `src/protocolo/verificacoes.py` ainda apontam para `data/analytical/dataset_supervisionado.parquet`, o mesmo arquivo do artefato oficial. Rodar A_03 ou A_04 apaga o artefato. Fecha no #73.

`a1_export_dataset` grava em `_analytical_path(cfg)`, que resolve para `C.ANALYTICAL_DIR / "dataset_supervisionado.parquet"` (nome definido em `configs/decisoes.yaml`, `dataset_analitico.path`). É o mesmo arquivo de `src/data/supervised_artifact.py` (`DATASET_NAME`). O A_14 registrou **FALHA**: "dataset analítico foi alterado depois da exportação". A ordem atual de execução evita o problema por acaso, não por desenho.

### ③ O que fazer

**Resolvido pelo #73** (Pessoa A) **e pelo #144** (Pessoa B). O A_03 e o A_04 gravam em `data/analytical/dataset_provisorio_pessoa_a.parquet`, e o artefato oficial continua só com `gerar_artefato_supervisionado`. Confirme com a suíte verde (`tests/test_regras_pessoa_a.py`) e marque como concluído.

### ④ Pronto quando

- yaml: `configs/decisoes.yaml` :: `dataset_analitico` nao-existe | A chave dataset_analitico, que apontava a exportação da Pessoa A para outro arquivo, saiu do configs/decisoes.yaml (#154): nada mais aponta para o fluxo A.
- nao-existe: `src/protocolo/verificacoes.py` | O fluxo A, que gravava esse arquivo, foi removido (#154): rodar os notebooks não apaga mais o artefato oficial.

## #123 · Ler o artefato por partição, para o teste nunca chegar à memória por engano

- prioridade: P1
- situação: resolvida
- estratégia: resolvida
- marco: M1
- data ideal: Concluído
- responsável: Pessoa C (dona; revisão cruzada sem edição concorrente)
- pessoas: C
- fonte: src/data/supervised_artifact.py (load_supervised_artifact)
- depende de: —
- tags: Vazamento, Memória/Desempenho, Código
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 5
- novo: sim
- professores: não

### ① Para entender

Hoje os notebooks C carregam treino, validação e teste e filtram depois. Com um parâmetro `partitions=["treino","validacao"]`, o filtro vai para a leitura do Parquet: menos memória e uma trava natural contra abrir o teste.

<div class="flow"><span>pedido: treino + validação</span><i>→</i><span>filtro no Parquet</span><i>→</i><span>teste nem é lido</span></div>

### ② Problema

Também resolve dois problemas antigos: a leitura parcial pulava a validação (item 18) e nada impedia ler o teste antes do G9 (item 16).

### ③ O que fazer

> [!ok] Concluída para o vocabulário antigo
> `load_supervised_artifact(partitions=...)` filtra no Parquet e exige G9 para `teste`.

**Continuação obrigatória no #131:** o mesmo mecanismo precisa valer para os seis blocos. Leitura padrão: `train_ref`, `val_tune`, `val_cal`, `val_meas`. `test_ref` e `test_pandemic` exigem G9. `exploracao` (2026) exige `exploracao_2026.ativa: true`.

### ④ Pronto quando

- contem: `src/data/supervised_artifact.py` :: `partitions` | load_supervised_artifact aceita o parâmetro partitions= e filtra na leitura do Parquet.
- teste: `tests/test_supervised_artifact.py::test_default_nao_carrega_teste` | O teste confirma que a leitura padrão não traz o teste para a memória.
- teste: `tests/test_supervised_artifact.py::test_load_bloco_de_teste_sem_g9_falha` | O teste confirma que pedir test_ref ou test_pandemic com o G9 pendente levanta erro.

## #16 · Nada no código impede abrir o teste antes do G9

- prioridade: P2
- situação: resolvida
- estratégia: resolvida
- marco: M1
- data ideal: Concluído
- responsável: Pessoa C (dona; revisão cruzada sem edição concorrente)
- pessoas: C
- fonte: src/data/supervised_artifact.py (holdout_partition); notebooks C_16
- depende de: #123
- tags: Código, Vazamento, Gate
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 3
- novo: não
- professores: não

### ① Para entender

> [!decisão] Decisão de 18/10
> Resolvido junto com o item 123 (trava no carregamento do artefato).

`holdout_partition` devolve o teste sem conferir o G9, e o C_16 nem usa essa função: filtra a coluna `particao` direto. A proteção do teste depende só da disciplina de quem roda.

> [!exemplo] Exemplo
> É um cofre com aviso "não abrir", mas sem fechadura.

### ② Problema

`holdout_partition` devolve as linhas de teste sem conferir o gate G9. Além disso, o C_16 não usa essa função: filtra o teste diretamente pela coluna `particao`. A proteção do teste depende, portanto, apenas da disciplina de quem executa.

### ③ O que fazer

> [!ok] Concluída: `holdout_partition` e `load_supervised_artifact` chamam `exigir_gate("G9_holdout")`.

**Continuação no #131:** criar o teste equivalente para `test_ref` e `test_pandemic` (com G9 pendente → `GatePendenteError`; com G9 aprovado via `monkeypatch` → devolve os dois blocos). O C_16 do #132 deve usar só essa função para abrir os testes.

### ④ Pronto quando

- contem: `src/data/supervised_artifact.py` :: `exigir_gate("G9_holdout")` | holdout_partition e load_supervised_artifact chamam exigir_gate("G9_holdout") antes de devolver o teste.
- teste: `tests/test_supervised_artifact.py::test_holdout_partition_sem_g9_falha` | O teste confirma que holdout_partition falha com o G9 pendente.
- teste: `tests/test_supervised_artifact.py::test_holdout_partition_blocos_apos_g9` | O teste confirma que holdout_partition devolve o teste (test_ref e test_pandemic) depois de o G9 ser aprovado.

## #18 · Carregar só algumas colunas do artefato pula a validação

- prioridade: P2
- situação: resolvida
- estratégia: resolvida
- marco: M1
- data ideal: Concluído
- responsável: Pessoa C (dona; revisão cruzada sem edição concorrente)
- pessoas: C
- fonte: src/data/supervised_artifact.py (load_supervised_artifact)
- depende de: #123
- tags: Código
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 3
- novo: não
- professores: não

### ① Para entender

> [!decisão] Decisão de 18/10
> Resolvido junto com o item 123.

`load_supervised_artifact(columns=[...])` lê só as colunas pedidas, mas aí não confere se a tabela está íntegra. Um arquivo com partições incompletas passaria despercebido.

### ② Problema

Quando chamada com `columns=`, a função pula a validação da tabela carregada. Um artefato corrompido ou com partições incompletas pode passar despercebido se o notebook ler só algumas colunas.

### ③ O que fazer

> [!ok] Concluída: a leitura parcial lê alvo e partição por dentro e valida.

**No #131:** manter essa garantia quando os blocos passarem a ser seis. A validação deve conferir os blocos pedidos, e não “três partições presentes”.

### ④ Pronto quando

- define: `src/data/supervised_artifact.py` :: `_validate_partial_load` | Existe a validação da leitura parcial (_validate_partial_load), usada quando o notebook pede só algumas colunas.
- teste: `tests/test_supervised_artifact.py::test_load_com_columns_valida_particoes` | O teste confirma que a leitura com columns= ainda valida as partições.
- teste: `tests/test_supervised_artifact.py::test_load_com_columns_valida_alvo_binario` | O teste confirma que a leitura com columns= ainda valida o alvo binário.

## #61 · pyproject aceita scikit-learn 1.4, mas o código precisa de 1.8+

- prioridade: P2
- situação: resolvida
- estratégia: resolvida
- marco: M1
- data ideal: Concluído
- responsável: Pessoa C (dona; revisão cruzada sem edição concorrente)
- pessoas: C
- fonte: pyproject.toml; src/models/calibration.py; src/models/logistic.py
- depende de: —
- tags: Ambiente, Testes
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 3
- novo: não
- professores: não

### ① Para entender

A calibração usa `FrozenEstimator` (existe a partir da 1.6) e a logística usa a API de `l1_ratio` da 1.8. Numa máquina com versão antiga, `penalty: l1` vira L2 sem aviso.

<div class="kpi">
<div><b>1.9.1</b>versão instalada na máquina da Pessoa B</div>
<div><b>>=1.4</b>versão mínima declarada</div>
</div>

### ② Problema

O `pyproject` exige `scikit-learn>=1.4`. Mas `calibrar` usa `FrozenEstimator`, que só existe a partir da 1.6, e o `logistic.py` assume a API de `l1_ratio` da 1.8. Numa versão anterior, `penalty: l1` no YAML vira L2 sem aviso.

### ③ O que fazer

> [!ok] Concluída: `pyproject.toml` exige `scikit-learn>=1.8` e `logistic.py` confere a versão instalada.
Nada a fazer.

### ④ Pronto quando

- contem: `pyproject.toml` :: `scikit-learn>=1.8` | O pyproject.toml exige scikit-learn 1.8 ou mais novo.
- teste: `tests/test_model_pipelines.py::test_logistic_falha_com_sklearn_antiga` | O teste confirma que a logística falha com versão antiga do scikit-learn, em vez de trocar L1 por L2 em silêncio.

## #63 · Dependências sem versão e espalhadas em dois arquivos

- prioridade: P2
- situação: resolvida
- estratégia: resolvida
- marco: M1
- data ideal: Concluído
- responsável: Pessoa C (dona; revisão cruzada sem edição concorrente)
- pessoas: C
- fonte: requirements.txt; pyproject.toml
- depende de: —
- tags: Ambiente
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 3
- novo: não
- professores: não

### ① Para entender

O `requirements.txt` não fixa versões. O `pyproject.toml` não lista `python-dotenv`, `joblib`, `matplotlib`, `seaborn`, `scipy` e `ipython`, que o código usa (alertas A9, A10, A25).

> [!exemplo] Exemplo
> Uma pessoa instala hoje e recebe pandas 3.1; outra instalou semana passada e tem pandas 3.0. Um resultado muda e ninguém sabe por quê.

### ② Problema

O `requirements.txt` não fixa nenhuma versão. O `pyproject` não lista `python-dotenv`, `joblib`, `matplotlib` e `seaborn`, que o código usa. As duas fontes de dependências divergem.

### ③ O que fazer

> [!ok] Concluída: `requirements.txt` com versões fixadas (scikit-learn 1.9.1, pandas 3.0.6, pyarrow 26.0.0…) e `pyproject.toml` com as dependências que faltavam.

**Para o pacote de entrega (#126):** o `requirements.txt` fixado é o que a banca deve usar. Registrar no README a versão do Python das execuções finais (o manifesto da auditoria da coorte registra 3.14.7).

### ④ Pronto quando

- contem: `requirements.txt` :: `scikit-learn==` | O requirements.txt fixa versões (exemplo: scikit-learn==…).
- teste: `tests/test_config.py::test_requirements_tem_versao_fixada` | O teste confirma que todas as dependências do requirements.txt têm versão fixada.
- teste: `tests/test_config.py::test_requirements_cobre_dependencias_de_runtime_do_pyproject` | O teste confirma que o requirements.txt cobre as dependências de execução listadas no pyproject.toml.

## #125 · B_07: célula 19 com parêntese não fechado e duas células de teste sem execução

- prioridade: P2
- situação: resolvida
- estratégia: resolvida
- marco: M1
- data ideal: Concluído
- responsável: Pessoa B (dona; revisão cruzada sem edição concorrente)
- pessoas: B
- fonte: notebooks/B/B_07_supervisionado_pilotos.ipynb (célula 19 e células 10.1/10.2)
- depende de: —
- tags: Notebook, Código
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 3
- novo: sim
- professores: não

### ① Para entender

A referência de 18/10 detectou erro de sintaxe estático na célula 19 e duas células novas (testes do pré-processador e do boosting) sem saída salva. Outra IA leria isso como notebook quebrado.

### ② Problema

Provável resto das colagens com caracteres corrompidos. O B_07 é o gerador do artefato oficial; precisa ficar íntegro.

### ③ O que fazer

> [!ok] Concluída (commit `a913228`). B_07 é histórico da fase provisória (#72); nada a fazer.

### ④ Pronto quando

- notebook-executado: `notebooks/B/B_07_supervisionado_pilotos.ipynb` | O B_07 está salvo com todas as células de código executadas e sem saída de erro (a célula 19 não tem mais parêntese aberto, e as células de teste 10.1 e 10.2 têm saída).

## #101 · Remover o notebook duplicado A3b (cópia antiga do A_09)

- prioridade: P3
- situação: resolvida
- estratégia: resolvida
- marco: M1
- data ideal: Concluído
- responsável: Pessoa A (dona; revisão cruzada sem edição concorrente)
- pessoas: A
- fonte: notebooks/A/A3b_split_aleatorio_cenarios.ipynb
- depende de: —
- tags: Notebook, Git
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 2
- novo: sim
- professores: não

### ① Para entender

Arquivo duplicado, sem execução. Confunde a ordem da cadeia e a referência do projeto.

### ② Problema

0 de 7 células executadas.

### ③ O que fazer

> [!ok] Concluída: o notebook duplicado não existe mais no repositório. Nada a fazer.

### ④ Pronto quando

- nao-existe: `notebooks/A/A3b_split_aleatorio_cenarios.ipynb` | O notebook duplicado A3b (cópia antiga do A_09) não existe mais no repositório.

## #14 · A variável SRAG_PARQUET_URL não tem efeito

- prioridade: P2
- situação: resolvida
- estratégia: resolvida
- marco: M1
- data ideal: Concluído
- responsável: Pessoa C (dona; revisão cruzada sem edição concorrente)
- pessoas: C
- fonte: src/utils/storage.py (get_parquet); src/utils/config.py (srag_parquet_url); notebooks/01_extracao
- depende de: —
- tags: Código, Ambiente
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 3
- novo: não
- professores: não

### ① Para entender

> [!decisão] Decisão de 18/10
> Lote de higiene de 22/10: correções pequenas, teto de 1 dia; o que não couber vai para pós-entrega.

O notebook 01 explica que dá para apontar outro arquivo de dados pela variável de ambiente `SRAG_PARQUET_URL`, mas o `storage.get_parquet` monta a URL sozinho e ignora essa variável.

### ② Problema

`get_parquet` monta a URL pública por conta própria, a partir de `GITHUB_REPO`, `DATA_VERSION` e `PARQUET_NAME`, e ignora `C.srag_parquet_url()`. Com isso, a variável de ambiente `SRAG_PARQUET_URL`, descrita no `01_extracao` como forma de apontar para outro arquivo, não tem efeito.

### ③ O que fazer

> [!ok] Concluída (19/10). Nada a fazer.

### ④ Pronto quando

- contem: `src/utils/storage.py` :: `C.srag_parquet_url()` | get_parquet usa C.srag_parquet_url(), então a variável de ambiente SRAG_PARQUET_URL tem efeito.
- teste: `tests/test_config.py::test_srag_parquet_url` | O teste confirma que a URL do Parquet respeita a configuração.

## #19 · O YAML aceita chaves duplicadas em silêncio e fica em cache

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 05/11
- responsável: Pessoa B (após 30/10) · alternativa: Pessoa C
- pessoas: B, C
- fonte: src/utils/config.py (carregar_supervised)
- depende de: —
- tags: Código, Ambiente
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: —
- novo: não
- professores: não

### ① Para entender

> [!decisão] Decisão de 18/10
> Lote de higiene de 22/10: correções pequenas, teto de 1 dia; o que não couber vai para pós-entrega.

Se o YAML tiver a mesma chave duas vezes, a leitura padrão fica com a última, sem avisar. A leitura rigorosa só existe no B_10. Além disso, o YAML lido fica guardado na memória: mudar o arquivo só vale depois de reiniciar o kernel.

> [!exemplo] Exemplo
> Você aprova o G6 no YAML, roda o C_13 sem reiniciar, e ele continua achando que o G6 está pendente.

### ② Problema

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que esta pendência está aberta
> A auditoria automática do painel (27/10, 14:40) marcou este item como resolvido com base em commits de 09 e 10/10, todos anteriores às revisões de 24 e 26/10 e sem relação com a entrega descrita aqui. Isso acontece por um defeito do painel: a cada auditoria, um commit antigo ainda não rejeitado reabre a sugestão (detalhes no #94).
> `src/utils/config.py` continua com `@lru_cache(maxsize=1)` e sem detecção de chave duplicada; não existe `recarregar_supervised`. Continua pós-entrega.

`carregar_supervised` usa `yaml.safe_load`, que aceita chaves duplicadas sem aviso (a última vence). A leitura rigorosa, que barra duplicadas, existe apenas no B_10. Além disso, o resultado fica em cache (`lru_cache`), e alterações no YAML só valem depois de reiniciar o kernel.

### ③ O que fazer

> [!decisão] Enxugado em 27/10 (eficiência primeiro)
> **Pós-entrega.** Os gates G6 a G9 serão editados por uma pessoa só (Pessoa C), com conferência visual no checklist do G9; o risco de chave duplicada fica baixo.

### ④ Pronto quando

- nao-contem: `src/utils/config.py` :: `@lru_cache(maxsize=1)` | (Pós-entrega) carregar_supervised deixou de guardar o YAML em cache permanente (ou ganhou recarregar_supervised), então mudar o YAML vale sem reiniciar o kernel.
- contem: `src/utils/config.py` :: `duplicada` | (Pós-entrega) A leitura do YAML detecta chave duplicada e avisa, em vez de ficar com a última em silêncio.
- teste: `tests/test_config.py` | O teste `tests/test_config.py` precisa passar no pytest rápido. Ele importa `src/utils/config.py`, que pertence(m) a esta pendência, e falhou na verificação de 2026-11-03 (2 testes falharam; ex.: FileNotFoundError: [Errno 2] No such file or directory: 'C:\\Users\\olivem85\\AppData\\Local\\Temp\\1\\srag_verificador_9mdibj0g\\repo\\). Acrescentado automaticamente pelo verificador.

## #36 · Faixas etárias e grafia do sexo diferentes entre EDA e modelo

- prioridade: P2
- situação: resolvida
- estratégia: resolvida
- marco: M3
- data ideal: Concluído
- responsável: Pessoa B (prepara) · execução: quem rodar o #51
- pessoas: B, A
- fonte: B_06_eda_temporal_clustering
- depende de: #131
- tags: Notebook, Features
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 3
- novo: não
- professores: não

### ① Para entender

O B_06 usa faixas como 1–4, 5–9, 10–19, 20–39; o YAML usa 1–4, 5–11, 12–17, 18–39. Tabelas da EDA e resultados por subgrupo do modelo ficam incomparáveis.

| Fonte | Faixas |
|---|---|
| B_06 (EDA) | <1 · 1–4 · 5–9 · 10–19 · 20–39 · 40–59 · 60–79 · 80+ |
| supervised.yaml | <1 · 1–4 · 5–11 · 12–17 · 18–39 · 40–59 · 60–79 · 80+ |

### ② Problema

As faixas etárias e a grafia do sexo (maiúscula ou minúscula) do B_06 são diferentes das de `features.engenharia.faixas_etarias` no YAML e de `sexo_categoria` no `engineering.py`. Tabelas da EDA e resultados por subgrupo do modelo ficam incomparáveis.

### ③ O que fazer

> [!ok] Resolvida (revisão de 24/10)
> O B_06 passou a derivar faixa etária e sexo com `montar_features`, com as faixas do YAML. As tabelas de desfecho do relatório saem do #137 (só treino), já com as faixas oficiais.

### ④ Pronto quando

- contem: `notebooks/B/B_06_eda_temporal_clustering.ipynb` :: `montar_features` | O B_06 deriva faixa etária e sexo com montar_features do src, usando as faixas oficiais do YAML.
- yaml: `configs/supervised.yaml` :: `features.engenharia.faixas_etarias.2.nome` = `5-11` | As faixas oficiais do YAML (1–4, 5–11, 12–17…) são a referência única para EDA e modelo.

## #99 · B_06: terminar a execução do início ao fim depois das correções de memória

- prioridade: P2
- situação: resolvida
- estratégia: resolvida
- marco: M1
- data ideal: Concluído
- responsável: Pessoa B (dona; revisão cruzada sem edição concorrente)
- pessoas: B
- fonte: notebooks/B/B_06_eda_temporal_clustering.ipynb
- depende de: —
- tags: Notebook, Memória/Desempenho
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 3
- novo: sim
- professores: não

### ① Para entender

> [!ok] Situação atual
> Em 17/10: leitura enxuta (44 colunas, 1.456 → 321 MB, −78%), base de desfecho sem cópia integral, contadores clínicos coluna a coluna, heatmap com matriz float64 e série mensal em datetime64. O MemoryError da célula 70 foi resolvido.

Falta rodar até o fim (clustering) e salvar com saídas.

### ② Problema

O notebook ainda mistura `dtype_backend="pyarrow"` com código que espera tipos NumPy; cada novo gráfico pode repetir os erros de `pd.NA` e `to_period`.

### ③ O que fazer

> [!ok] Concluída (21/10, commit `5bdcd8d`): B_06 executado de ponta a ponta com memória validada.

**Atenção para quem usar os números:** as tabelas de desfecho dessa execução usaram a coorte inteira. Para o relatório, valem as do #51, só com `train_ref`. Os números do clustering continuam válidos, porque o clustering não usa o desfecho.

### ④ Pronto quando

- notebook-executado: `notebooks/B/B_06_eda_temporal_clustering.ipynb` | O B_06 está salvo executado do início ao fim (inclusive o clustering), sem saída de erro.
- notebook-saida: `notebooks/B/B_06_eda_temporal_clustering.ipynb` :: `Memória após compactação` | As saídas registram a leitura enxuta com compactação de memória (correções de 17/10).

## #121 · montar_features faz cópia completa da coorte e devolve tipos pesados

- prioridade: P2
- situação: resolvida
- estratégia: resolvida
- marco: M1
- data ideal: Concluído
- responsável: Pessoa C (dona; revisão cruzada sem edição concorrente)
- pessoas: C
- fonte: src/features/engineering.py (montar_features)
- depende de: —
- tags: Memória/Desempenho, Código, Features
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 3
- novo: sim
- professores: não

### ① Para entender

Para acrescentar 11 colunas, a função copia a coorte inteira (125 colunas no B_07). Na coorte definitiva inicial, essa cópia pode dobrar desnecessariamente o pico de memória antes mesmo de criar treino e validações.

| Saída | Hoje | Proposto |
|---|---|---|
| idade_anos, dias_sintomas | float64 | float32 |
| flags | int64/bool | int8 |
| faixa_etaria, sexo_categoria | texto | category |
| ano / mês | int64 | int16 / int8 |

### ② Problema

`out = df.copy()` na primeira linha. Com o pandas 3 (Copy-on-Write), uma cópia rasa já garante que a entrada não é alterada.

### ③ O que fazer

> [!ok] Concluída: `montar_features` usa cópia rasa e tipos compactos. Nada a fazer.

**Uso no #131:** chamar `montar_features` uma única vez sobre a coorte definitiva, lendo só as colunas de entrada (`nu_idade_n`, `tp_idade`, `cs_sexo`, `dt_sin_pri`, `dt_interna` + features + alvo + `sg_uf` + `nu_notific` + `id_registro`). O resto das 199 colunas não precisa ir para a memória.

### ④ Pronto quando

- contem: `src/features/engineering.py` :: `df.copy(deep=False)` | montar_features faz cópia rasa (df.copy(deep=False)), sem duplicar a coorte inteira na memória.
- teste: `tests/test_features.py::test_montar_features_usa_tipos_compactos` | O teste confirma que as colunas derivadas saem com tipos compactos (float32, int8, category).

## #124 · C_11 deve rodar com o pré-processamento esparso, sem materializar a validação inteira

- prioridade: P2
- situação: resolvida
- estratégia: resolvida
- marco: M1
- data ideal: Concluído
- responsável: Pessoa C (dona; revisão cruzada sem edição concorrente)
- pessoas: C
- fonte: notebooks/C/C_11_pipeline_supervisionado.ipynb
- depende de: #123
- tags: Notebook, Memória/Desempenho
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 3
- novo: sim
- professores: não

### ① Para entender

O C_11 só prova que o pipeline funciona. Com o one-hot esparso já no `src`, ele deve passar sem o MemoryError de 2,53 GiB.

### ② Problema

O notebook ainda faz `fit_transform` do treino e `transform` da validação completa, guardando as duas matrizes.

### ③ O que fazer

> [!ok] Concluída para o artefato provisório.

**No #132:** o C_11 passa a ler `train_ref` e uma amostra de `val_tune`, e nunca a validação inteira. Registrar tempo e pico de memória com `Monitor`, como já faz.

### ④ Pronto quando

- nao-contem: `notebooks/C/C_11_pipeline_supervisionado.ipynb` :: `sparse_output=False` | O C_11 não força mais o one-hot denso (causa do MemoryError de 2,53 GiB); usa o pré-processador esparso do src. A nova execução do C_11 nos seis blocos é conferida no #132.
- contem: `src/models/pipeline.py` :: `saida: SaidaPreprocessador = "esparsa"` | O pré-processador do src usa saída esparsa por padrão.
- teste: `tests/test_config.py` | O teste `tests/test_config.py` precisa passar no pytest rápido. Ele importa `src/models/pipeline.py`, que pertence(m) a esta pendência, e falhou na verificação de 2026-11-03 (2 testes falharam; ex.: FileNotFoundError: [Errno 2] No such file or directory: 'C:\\Users\\olivem85\\AppData\\Local\\Temp\\1\\srag_verificador_9mdibj0g\\repo\\). Acrescentado automaticamente pelo verificador.

## #20 · Nome do finalista diferente no YAML e no código

- prioridade: P3
- situação: resolvida
- estratégia: resolvida
- marco: M1
- data ideal: Concluído
- responsável: Pessoa C (dona; revisão cruzada sem edição concorrente)
- pessoas: C
- fonte: src/models/factory.py; notebooks C_15 e C_16
- depende de: —
- tags: Código, Modelagem
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 2
- novo: não
- professores: não

### ① Para entender

> [!decisão] Decisão de 18/10
> Lote de higiene de 22/10: correções pequenas, teto de 1 dia; o que não couber vai para pós-entrega.

O YAML chama o finalista de `hist_gradient_boosting`; a fábrica de modelos só aceita `boosting`. O C_15 e o C_16 traduzem o nome com uma cópia do mesmo mapeamento. O relatório automático também marcou (A8).

### ② Problema

O YAML chama o finalista de `hist_gradient_boosting`, mas a fábrica só aceita `boosting`. O C_15 e o C_16 contornam isso com o mesmo mapeamento copiado em cada notebook.

### ③ O que fazer

> [!ok] Concluída (`_FINALISTA_ALIASES` em `factory.py`, 20/10). Nada a fazer.

### ④ Pronto quando

- define: `src/models/factory.py` :: `_FINALISTA_ALIASES` | A fábrica tem o mapeamento único de nomes do finalista (hist_gradient_boosting → boosting), sem cópias nos notebooks.
- teste: `tests/test_model_pipelines.py::test_build_finalista_aceita_nomes_do_yaml` | O teste confirma que a fábrica aceita os nomes do finalista como estão no YAML.

## #21 · A fábrica passa qualquer chave nova do YAML ao modelo

- prioridade: P3
- situação: resolvida
- estratégia: resolvida
- marco: M1
- data ideal: Concluído
- responsável: Pessoa C (dona; revisão cruzada sem edição concorrente)
- pessoas: C
- fonte: src/models/factory.py (_kwargs_do_yaml)
- depende de: —
- tags: Código
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 2
- novo: não
- professores: não

### ① Para entender

> [!decisão] Decisão de 18/10
> Lote de higiene de 22/10: correções pequenas, teto de 1 dia; o que não couber vai para pós-entrega.

Uma chave administrativa no YAML, como `ativa: true`, ou um erro de digitação vira argumento do modelo e gera `TypeError`.

### ② Problema

A fábrica repassa ao construtor qualquer chave nova de `models.<nome>` que não comece com `busca_`. Uma chave administrativa (como `ativa`) ou um erro de digitação gera `TypeError` no construtor.

### ③ O que fazer

> [!ok] Concluída: a fábrica filtra as chaves com `inspect.signature`. Nada a fazer.

### ④ Pronto quando

- contem: `src/models/factory.py` :: `signature` | A fábrica filtra as chaves do YAML pela assinatura do construtor (inspect.signature).
- teste: `tests/test_model_pipelines.py::test_kwargs_do_yaml_descarta_chave_administrativa` | O teste confirma que uma chave administrativa (como ativa) não chega ao construtor do modelo.
- teste: `tests/test_model_pipelines.py::test_kwargs_do_yaml_descarta_typo` | O teste confirma que um erro de digitação no YAML não gera TypeError no modelo.

## #29 · Itens desatualizados ou sem uso no YAML

- prioridade: P3
- situação: aberta
- estratégia: desenvolver
- marco: M3
- data ideal: 01/11
- responsável: Pessoa A · revisão: Pessoa C
- pessoas: A
- fonte: configs/supervised.yaml
- depende de: #73
- tags: Código, Documentação
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 0
- novo: não
- professores: não

### ① Para entender

> [!decisão] Decisão de 18/10
> Lote de higiene de 22/10: correções pequenas, teto de 1 dia; o que não couber vai para pós-entrega.

Árvore e Random Forest seguem `ativa: true` apesar de encerradas; não existe G3; 30 chaves nunca são lidas pelo código; `youden_j` é citado mas não é métrica candidata. Isso confunde quem lê o YAML como fonte única.

### ② Problema

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que esta pendência está aberta
> A auditoria automática do painel (27/10, 14:40) marcou este item como resolvido com base em commits de 09 e 11/10, todos anteriores às revisões de 24 e 26/10 e sem relação com a entrega descrita aqui. Isso acontece por um defeito do painel: a cada auditoria, um commit antigo ainda não rejeitado reabre a sugestão (detalhes no #94).
> No `supervised.yaml` atual: `decision_tree.ativa: true`, `random_forest.ativa: true`, `boosting.early_stopping: false`, `limiar.metricas_candidatas` sem `recall_minimo`/`youden_j` e sem `limiar.min_recall`. Nada mudou. É feito dentro do #73.

O YAML tem itens desatualizados ou sem uso: `decision_tree` e `random_forest` continuam com `ativa: true`, embora estejam em `familias_encerradas`; não existe gate G3 e não há explicação; `coluna_estratificacao_temporal` e `descartar_outros` não são lidas por nenhum código; `metricas_candidatas` não inclui `youden_j`, que as decisões citam como opção.

### ③ O que fazer

> [!decisão] Enxugado em 27/10 (eficiência primeiro)
> Feito dentro do **#73** (Pessoa A). Marque como concluído junto com ele.

### ④ Pronto quando

- yaml: `configs/supervised.yaml` :: `models.decision_tree.ativa` = `false` | Família encerrada desligada no YAML.
- yaml: `configs/supervised.yaml` :: `models.random_forest.ativa` = `false` | Família encerrada desligada no YAML.
- yaml: `configs/supervised.yaml` :: `limiar.metricas_candidatas` contem `youden_j` | youden_j, citado nas decisões, passou a ser métrica candidata do limiar.
- yaml: `configs/supervised.yaml` :: `limiar.metricas_candidatas` contem `recall_minimo` | recall_minimo, a regra principal do #80, é métrica candidata do limiar.

## #38 · Sobras no B_07: modo de teste sintético e imports sem uso

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 05/11
- responsável: Pessoa B (dona; revisão cruzada sem edição concorrente)
- pessoas: B
- fonte: B_07_supervisionado_pilotos
- depende de: —
- tags: Notebook
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: —
- novo: não
- professores: não
- removido: removido na revisão de 03/11 (v3.3): resolvido; o modo SRAG_NOTEBOOK_SMOKE saiu do B_05 (antigo B_07); sobrou só um import sem uso de GroupShuffleSplit, sem efeito

### ① Para entender

> [!decisão] Decisão de 18/10
> Lote de higiene de 22/10: correções pequenas, teto de 1 dia; o que não couber vai para pós-entrega.

O modo `SRAG_NOTEBOOK_SMOKE` e imports como `GroupShuffleSplit` poluem o notebook e confundem quem lê.

### ② Problema

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Se sobrar tempo, trate durante a limpeza do B_07 no #146 (imports sem uso e o modo de teste sintético). Fora disso, pós-entrega.

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que esta pendência está aberta
> A auditoria automática do painel (27/10, 14:40) marcou este item como resolvido com base em commits de 18 e 19/10, todos anteriores às revisões de 24 e 26/10 e sem relação com a entrega descrita aqui. Isso acontece por um defeito do painel: a cada auditoria, um commit antigo ainda não rejeitado reabre a sugestão (detalhes no #94).
> O B_07 ainda tem `SRAG_NOTEBOOK_SMOKE` (3 ocorrências) e importa `GroupShuffleSplit` sem usar. Continua pós-entrega.

O B_07 ainda tem o modo `SRAG_NOTEBOOK_SMOKE`, que usa dados sintéticos, e imports sem uso, como `GroupShuffleSplit`, `ColumnTransformer` e funções avulsas de `sklearn.metrics`.

### ③ O que fazer

> [!atenção] Sugestão automática incorreta: o modo `SRAG_NOTEBOOK_SMOKE` continua no B_07.
> Como o B_07 passou a ser histórico da fase provisória (#72), **não vale a pena mexer agora**. Use **✗ Não é isso** e deixe para depois da entrega.

**Como fazer, quando for a hora (instruções anteriores mantidas):**

Remover o modo de teste com dados sintéticos (os testes de `tests/` já cumprem esse papel) e os imports sem uso. Rodar o notebook do início ao fim para confirmar.

### ④ Pronto quando

- nao-contem: `notebooks/B/B_07_supervisionado_pilotos.ipynb` :: `SRAG_NOTEBOOK_SMOKE` | (Pós-entrega) O modo de teste sintético SRAG_NOTEBOOK_SMOKE foi removido do B_07.
- nao-contem: `notebooks/B/B_07_supervisionado_pilotos.ipynb` :: `GroupShuffleSplit` | (Pós-entrega) O import sem uso de GroupShuffleSplit foi removido do B_07.

## #40 · A construção da coorte provisória não gera os arquivos de rastreio esperados

- prioridade: P3
- situação: parcial
- estratégia: desenvolver
- marco: M4
- data ideal: 01/11
- responsável: Pessoa A (dentro do #70)
- pessoas: A
- fonte: B/___provisorio_construcao_coorte_b; construção da coorte definitiva
- depende de: #70
- tags: Notebook, Dados/Coorte
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 0
- novo: não
- professores: não
- removido: obsoleto em 03/11: a construção da coorte provisória foi aposentada (§29.32)

### ① Para entender

O notebook `___provisorio_construcao_coorte_b` não foi reexecutado (0 de 14 células com saída), fixa a data final em 28/09/2026 e não gera `manifesto_coorte.json` nem `variaveis_finais.csv`, que o YAML espera.

### ② Problema

> [!atenção] Replanejamento de 31/10 · versão 2 (entrega em 04/11)
> Replanejamento v2: este card é **resolvido dentro do card indicado em "responsável"**; sem esforço próprio. Marque como concluído junto com ele.

A coorte provisória fixa a data final em 28/09/2026. A remoção de duplicatas exatas só considera as colunas carregadas do dicionário. O notebook não gera `manifesto_coorte.json` nem `variaveis_finais.csv`, que o YAML espera em `artefatos_coorte`.

### ③ O que fazer

**Resolvido dentro do #70** (Pessoa A, 31/10). Marque como concluído junto com ele. O notebook da coorte provisória não roda de novo e sai do pacote (#143); a frase de Métodos que explica a trajetória está no #133 (coorte provisória, #98).

### ④ Pronto quando

- existe: `outputs/final/variaveis_finais.csv` | A tabela de variáveis finais existe (gerada no #70, a partir do supervised.yaml cruzado com o dicionário).

## #66 · Teste lento roda junto com os rápidos

- prioridade: P3
- situação: resolvida
- estratégia: resolvida
- marco: M1
- data ideal: Concluído
- responsável: Pessoa C (dona; revisão cruzada sem edição concorrente)
- pessoas: C
- fonte: tests/test_temporal.py; tests/test_leakage.py (test_dataset_sem_identificadores_duplicados)
- depende de: —
- tags: Testes
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 2
- novo: não
- professores: não

### ① Para entender

> [!decisão] Decisão de 18/10
> Lote de higiene de 22/10: correções pequenas, teto de 1 dia; o que não couber vai para pós-entrega.

`test_dataset_sem_identificadores_duplicados` lê o Parquet inteiro e não tem a marcação `@pytest.mark.slow`.

### ② Problema

O teste de identificadores duplicados lê o Parquet inteiro, mas não tem a marcação `@pytest.mark.slow`. Ele roda junto com os testes rápidos.

### ③ O que fazer

> [!ok] Concluída. Nada a fazer.

### ④ Pronto quando

- contem: `tests/test_leakage.py` :: `@pytest.mark.slow` | O teste que lê o Parquet inteiro está marcado como slow.
- contem: `pyproject.toml` :: `not slow` | O pytest padrão do projeto exclui os testes slow (addopts com -m 'not slow ...').

## #122 · read_srag sem opção de leitura compacta

- prioridade: P3
- situação: resolvida
- estratégia: resolvida
- marco: M1
- data ideal: Concluído
- responsável: Pessoa C (dona; revisão cruzada sem edição concorrente)
- pessoas: C
- fonte: src/utils/storage.py (read_srag); src/utils/io_eficiente.py
- depende de: —
- tags: Memória/Desempenho, Código
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 2
- novo: sim
- professores: não

### ① Para entender

Notebooks que leem a base bruta recebem texto como objeto Python (pesado). `io_eficiente.ler_parquet_enxuto` já existe e transforma códigos em `category`.

### ② Problema

Falta um parâmetro `compactar=True` em `read_srag` que delegue para `ler_parquet_enxuto`, mantendo o comportamento antigo como padrão.

### ③ O que fazer

> [!ok] Concluída. Use `read_srag(..., compactar=True)` no #131 se a leitura da coorte pesar.

### ④ Pronto quando

- contem: `src/utils/storage.py` :: `compactar: bool = False` | read_srag tem o parâmetro compactar, que delega para io_eficiente.ler_parquet_enxuto, mantendo o comportamento antigo como padrão.

## #34 · O C_13 manda colar os hiperparâmetros em config.yaml (o certo é supervised.yaml)

- prioridade: P4
- situação: resolvida
- estratégia: resolvida
- marco: M1
- data ideal: Concluído
- responsável: Pessoa C (dona; revisão cruzada sem edição concorrente)
- pessoas: C
- fonte: notebooks C_13
- depende de: —
- tags: Notebook, Documentação
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1
- novo: não
- professores: não

### ① Para entender

> [!decisão] Decisão de 18/10
> Lote de higiene de 22/10: correções pequenas, teto de 1 dia; o que não couber vai para pós-entrega.

Erro de texto pequeno, mas pode fazer alguém editar um arquivo que não existe na hora de aprovar o G6.

### ② Problema

O texto da proposta de hiperparâmetros manda colar o resultado em `config.yaml`. O arquivo correto é `configs/supervised.yaml`.

### ③ O que fazer

> [!ok] Concluída. Nada a fazer.

### ④ Pronto quando

- nao-contem: `notebooks/C/C_13_boosting.ipynb` :: `config.yaml` | O C_13 não manda mais colar hiperparâmetros num arquivo config.yaml, que não existe.
- contem: `notebooks/C/C_13_boosting.ipynb` :: `supervised.yaml` | O C_13 indica configs/supervised.yaml como destino dos hiperparâmetros.

## #76 · Nenhum notebook confere a versão do scikit-learn no início

- prioridade: P4
- situação: resolvida
- estratégia: resolvida
- marco: M1
- data ideal: Concluído
- responsável: Pessoa C (dona; revisão cruzada sem edição concorrente)
- pessoas: C
- fonte: C_02_smoke_test; B_05 / 01_extracao
- depende de: —
- tags: Ambiente, Notebook
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1
- novo: não
- professores: não

### ① Para entender

Um ambiente desatualizado só falharia no C_15 (calibração). O smoke test (C_02) poderia barrar isso logo no começo.

### ② Problema

Nem o B_05 nem o C_02 conferem a versão do scikit-learn. Um ambiente desatualizado só falha mais adiante, no C_15.

### ③ O que fazer

> [!ok] Concluída: o C_02 confere a versão. Nada a fazer.

### ④ Pronto quando

- teste: `tests/test_model_pipelines.py::test_scikit_learn_instalado_e_maior_ou_igual_1_8` | O teste rápido confere a versão do scikit-learn (≥ 1.8) logo no começo do uso do projeto; continua valendo mesmo se o C_02 sair no #143.
- contem: `src/models/logistic.py` :: `SKLEARN_L1_RATIO_MIN` | build_logistic_pipeline confere a versão mínima do scikit-learn e falha com RuntimeError em versões antigas.

## #98 · Notebooks B sem execução salva: a coorte provisória não é reprodutível pelo repositório

- prioridade: P3
- situação: aberta
- estratégia: documentar
- marco: M6
- data ideal: 01/11
- responsável: Pessoa A (dentro do #133, seções 2 a 4)
- pessoas: A
- fonte: notebooks B_05 (1 de 42 células sem saída); B/___provisorio_construcao_coorte_b (0 de 14)
- depende de: —
- tags: Notebook, Dados/Coorte
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 0
- novo: não
- professores: não
- removido: obsoleto em 03/11: a coorte provisória foi aposentada (§29.32); a reprodutibilidade da definitiva está no #126

### ① Para entender

O notebook que constrói a coorte provisória B não tem nenhuma célula executada salva, e o B_05 tem uma célula sem saída. Quem clonar o repositório não consegue ver como a coorte de 3,9 milhões de linhas foi feita, só o arquivo pronto (que não vai para o Git).

<div class="kpi">
<div><b>0 / 14</b>células executadas no construtor da coorte</div>
<div><b>41 / 42</b>células executadas no B_05</div>
</div>

### ② Problema

> [!atenção] Replanejamento de 31/10 · versão 2 (entrega em 04/11)
> Replanejamento v2: uma frase ou parágrafo dentro do **#133** (domingo, Pessoa A); sem esforço próprio.

Alertas A40 e A41 do relatório. A coorte `coorte_provisoria_b.parquet` (SHA-256 `da94652d…`) é usada pelo B_06 e pelo B_07, mas o processo que a gera não está registrado com saídas.

### ③ O que fazer

**Pessoa A, dentro do #133 (01/11):** parágrafo de Métodos: a seleção de variáveis foi feita na coorte provisória e congelada antes da definitiva, e a definitiva é subconjunto exato da provisória (30.408 linhas a menos, nenhuma nova, alvo idêntico). Não executar o construtor provisório de novo.

### ④ Pronto quando

- manual: | O parágrafo de Métodos do relatório (#133) explica que a seleção de variáveis foi feita na coorte provisória e congelada antes da definitiva, e que a definitiva é subconjunto exato da provisória (30.408 linhas a menos, nenhuma nova, alvo idêntico).

## #118 · Criar a partição-mestre: treino 2019/2023–2025 e duas janelas de teste

- prioridade: P1
- situação: resolvida
- estratégia: resolvida
- marco: M2
- data ideal: Concluído
- responsável: Pessoa C (dona; revisão cruzada sem edição concorrente)
- pessoas: C
- fonte: Plano integrado v2, seção 3; src/data/split.py; notebooks/E/E_01
- depende de: #86
- tags: Partição, Vazamento, Notebook
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 5
- novo: sim
- professores: não

### ① Para entender

> [!ok] Decisão fechada em 18/10
> A coorte definitiva inicial será a seleção de features da coorte provisória. O treino principal usará exclusivamente 2019, 2023, 2024 e 2025. Haverá duas janelas de teste: (A) 2019, 2023, 2024 e 2025; (B) 2019 a 2025, incluindo 2020–2022. O ano de 2026 não participa do desenvolvimento nem dos testes principais e fica apenas como exploração opcional, depois de todo o restante concluído.

A partição deve produzir conjuntos fisicamente disjuntos por `group_id`. Nos anos 2019, 2023, 2024 e 2025, uma parte vai para treino/validações e outra parte, nunca vista, vai para o Teste A. Os registros de 2020–2022 ficam fora do treino e compõem a parcela adicional do Teste B.

| Bloco | Anos permitidos | Uso |
|---|---|---|
| train_ref | 2019, 2023, 2024, 2025 | Ajuste dos modelos |
| val_tune | 2019, 2023, 2024, 2025 | Features, geografia e tuning curto |
| val_cal | 2019, 2023, 2024, 2025 | Calibração e limiar |
| val_meas | 2019, 2023, 2024, 2025 | Comparação intermediária antes do teste |
| test_ref | 2019, 2023, 2024, 2025 | Teste A principal |
| test_pandemic | 2020, 2021, 2022 | Parcela adicional do Teste B |

**Teste B** é a união lógica de `test_ref` com `test_pandemic`, sem duplicar o arquivo nem misturar treino.

### ② Problema

A v4 previa três cenários de treino. Essa complexidade foi descartada pela decisão atual. Agora há um único treino e duas janelas de avaliação. O ponto crítico passa a ser garantir completa disjunção por grupo.

### ③ O que fazer

> [!ok] Função concluída; **artefato ainda não existe**
> `criar_particao_mestra` está pronta e testada com dados sintéticos. A coorte definitiva publicada **não tem** `group_id`, `regiao_residencia` nem `particao`, e não existe `partitions_master.parquet`. A materialização está no **#131** (novo), para não reabrir este item.

### ④ Pronto quando

- define: `src/data/split.py` :: `criar_particao_mestra` | A função que cria os seis blocos (train_ref, val_tune, val_cal, val_meas, test_ref, test_pandemic) existe em src/data/split.py.
- contem: `src/data/split.py` :: `test_pandemic` | O split.py conhece o bloco test_pandemic.
- teste: `tests/test_split.py` | Os testes de partição passam, inclusive os de grupos que não cruzam blocos.

## #127 · Funções de avaliação: bootstrap por grupo, intercepto e inclinação de calibração, ECE por quantis

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M2
- data ideal: 31/10
- responsável: Pessoa A (1,25 h)
- pessoas: A
- fonte: src/evaluation/metrics.py (bootstrap_grupo); tests/test_metrics.py
- depende de: #23
- tags: Metodologia, Código
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1.25
- novo: sim
- professores: não
- arquivos: src/evaluation/metrics.py, tests/test_metrics.py

### ① Para entender

Quando dois modelos são avaliados nas mesmas pessoas, a pergunta certa é "a diferença entre eles é real?", não "cada um tem qual nota?". O bootstrap pareado sorteia pessoas com reposição, recalcula as duas métricas e guarda a diferença; o intervalo dessas diferenças diz se o ganho é consistente.

> [!exemplo] Exemplo
> Duas balanças pesando os mesmos 80 mil pacotes: comparar pacote a pacote é muito mais preciso que comparar a média de cada balança.

### ② Problema

> [!atenção] Replanejamento de 31/10 · versão 2 (entrega em 04/11)
> Passa a ter **código completo e testado** (reduz o card de 1 h 30 para 1 h). Serve a três usos: IC de uma métrica, IC da diferença entre dois modelos (#54, #119) e IC por janela (C_16). Motivo da reescrita: o `ic_bootstrap` atual reordena o vetor inteiro a cada réplica (inviável em `test_pandemic`, 2.915.829 linhas). Medido num protótipo com 3 milhões de linhas: ≈ 0,45 s por réplica. Absorve o #22.

Não existe função para isso no `src`. Reamostrar linhas (e não grupos) subestimaria a incerteza quando a mesma notificação tem mais de uma linha.

### ③ O que fazer

> [!decisão] Replanejamento de 31/10 · versão 2
> Uma função só, com o **sorteio por `group_id`** (a mesma ficha repetida entra junta ou não entra) e as probabilidades **ordenadas uma vez**. Os blocos abaixo foram executados e passaram nos testes.

**Dono:** Pessoa A · **Prazo:** 31/10 (sábado), 17h30 às 18h45 · **Esforço estimado:** ≈ 1 h 15 · **Começa quando:** #23 (já concluído)

#### Passo a passo
1. `git pull`; abra `src/evaluation/metrics.py`.
2. Na lista `__all__` (início do arquivo), acrescente a linha `    "bootstrap_grupo",` logo depois de `    "ic_bootstrap",`.
3. **Padrões vindos do YAML (absorve o #22).** Em `ic_bootstrap`, troque a linha `    n_boot: int = 200,` por `    n_boot: int | None = None,` e, logo **antes** da linha `    y = _to_int_labels(y_true)` (a primeira do corpo da função, depois do docstring), insira exatamente:

```python
    if n_boot is None:
        from src.utils import config as C  # noqa: N812

        n_boot = int(C.cfg("avaliacao", "bootstrap", "repeticoes") or 200)
```
4. **Função nova.** Cole ao **final** do arquivo (depois do `return (...)` de `ic_bootstrap`, com duas linhas em branco antes). Nada a apagar; `np`, `pd`, `_to_np`, `_to_int_labels` e `ArrayLike` já existem no arquivo:

```python
def _niveis(prob: np.ndarray) -> tuple[np.ndarray, int]:
    """Códigos inteiros dos valores distintos de ``prob`` (ordem crescente)."""
    niveis, codigos = np.unique(prob, return_inverse=True)
    return codigos.astype(np.int64), int(niveis.size)


def _auc_ponderada(cod: np.ndarray, k: int, y: np.ndarray, w: np.ndarray) -> float:
    """AUC com pesos, tratando empates como metade (igual ao ``roc_auc_score``)."""
    pos = np.bincount(cod, weights=w * y, minlength=k)
    neg = np.bincount(cod, weights=w * (1.0 - y), minlength=k)
    total_pos, total_neg = pos.sum(), neg.sum()
    if total_pos <= 0 or total_neg <= 0:
        return float("nan")
    neg_abaixo = np.cumsum(neg) - neg
    return float((pos * (neg_abaixo + 0.5 * neg)).sum() / (total_pos * total_neg))


def _ap_ponderada(cod: np.ndarray, k: int, y: np.ndarray, w: np.ndarray) -> float:
    """Average precision com pesos (igual ao ``average_precision_score``)."""
    pos = np.bincount(cod, weights=w * y, minlength=k)[::-1]
    neg = np.bincount(cod, weights=w * (1.0 - y), minlength=k)[::-1]
    tp, fp = np.cumsum(pos), np.cumsum(neg)
    if tp[-1] <= 0:
        return float("nan")
    precisao = np.divide(tp, tp + fp, out=np.zeros_like(tp), where=(tp + fp) > 0)
    return float((pos / tp[-1] * precisao).sum())


def _brier_ponderado(y: np.ndarray, p: np.ndarray, w: np.ndarray) -> float:
    return float((w * (y - p) ** 2).sum() / w.sum())


def bootstrap_grupo(
    y_true: ArrayLike,
    prob_a: ArrayLike,
    grupos: ArrayLike,
    *,
    metrica: str = "auc",
    prob_b: ArrayLike | None = None,
    n: int | None = None,
    alpha: float = 0.05,
    seed: int | None = None,
) -> dict[str, float]:
    """Bootstrap por grupo (``group_id``) de AUC, AP ou Brier.

    Cada réplica sorteia grupos com reposição; todas as linhas do grupo entram juntas,
    com peso igual ao número de vezes sorteado. As probabilidades são ordenadas uma vez.
    Com ``prob_b``, o sorteio é o mesmo para os dois modelos e o resultado é a
    diferença A − B (IC percentil e p bilateral).
    """
    from src.utils import config as C  # noqa: N812

    if metrica not in {"auc", "ap", "brier"}:
        raise ValueError(f"metrica inválida: {metrica!r}. Use 'auc', 'ap' ou 'brier'.")
    n = int(n if n is not None else (C.cfg("avaliacao", "bootstrap", "repeticoes") or 1000))
    seed = int(seed if seed is not None else (C.cfg("avaliacao", "bootstrap", "seed") or 42))

    y = _to_int_labels(y_true).astype(np.float64)
    pa = _to_np(prob_a).astype(np.float64)
    pb = None if prob_b is None else _to_np(prob_b).astype(np.float64)
    cod_grupo = pd.factorize(np.asarray(grupos))[0]
    if (cod_grupo < 0).any():
        raise ValueError("grupos não pode ter valores ausentes.")
    n_grupos = int(cod_grupo.max()) + 1

    def calcular(p: np.ndarray, pre, w: np.ndarray) -> float:
        if metrica == "brier":
            return _brier_ponderado(y, p, w)
        cod, k = pre
        return (_auc_ponderada if metrica == "auc" else _ap_ponderada)(cod, k, y, w)

    pre_a = _niveis(pa) if metrica != "brier" else None
    pre_b = _niveis(pb) if (pb is not None and metrica != "brier") else None
    um = np.ones(len(y))

    est_a = calcular(pa, pre_a, um)
    est_b = calcular(pb, pre_b, um) if pb is not None else None

    rng = np.random.default_rng(seed)
    valores = np.full(n, np.nan)
    for i in range(n):
        sorteio = np.bincount(rng.integers(0, n_grupos, n_grupos), minlength=n_grupos)
        w = sorteio[cod_grupo].astype(np.float64)
        va = calcular(pa, pre_a, w)
        valores[i] = va if pb is None else va - calcular(pb, pre_b, w)

    validos = valores[~np.isnan(valores)]
    if validos.size == 0:
        raise ValueError("Nenhuma réplica com as duas classes: confira y_true e grupos.")
    inferior, superior = np.quantile(validos, [alpha / 2, 1 - alpha / 2])
    if pb is None:
        return {"estimativa": est_a, "ic_inferior": float(inferior), "ic_superior": float(superior),
                "n_validas": int(validos.size)}
    p_bilateral = min(1.0, 2 * min(float((validos <= 0).mean()), float((validos >= 0).mean())))
    return {"estimativa_diferenca": est_a - est_b, "ic_inferior": float(inferior),
            "ic_superior": float(superior), "p_bilateral": p_bilateral, "n_validas": int(validos.size)}
```
5. **Testes.** Acrescente ao **final** de `tests/test_metrics.py` (duas linhas em branco antes; `np` e `pytest` já estão importados lá):

```python
def test_bootstrap_grupo_igual_ao_sklearn_com_pesos_um():
    from sklearn.metrics import average_precision_score, roc_auc_score

    from src.evaluation.metrics import _ap_ponderada, _auc_ponderada, _niveis

    rng = np.random.default_rng(0)
    p = np.round(rng.beta(1, 10, 20_000), 2)
    y = (rng.random(20_000) < np.clip(p * 1.2, 0, 1)).astype(float)
    cod, k = _niveis(p)
    um = np.ones(len(y))
    assert abs(_auc_ponderada(cod, k, y, um) - roc_auc_score(y, p)) < 1e-9
    assert abs(_ap_ponderada(cod, k, y, um) - average_precision_score(y, p)) < 1e-9
    pesos = rng.integers(0, 3, len(y)).astype(float)
    repetido = np.repeat(np.arange(len(y)), pesos.astype(int))
    assert abs(_auc_ponderada(cod, k, y, pesos) - roc_auc_score(y[repetido], p[repetido])) < 1e-9
    assert abs(_ap_ponderada(cod, k, y, pesos) - average_precision_score(y[repetido], p[repetido])) < 1e-9


def test_bootstrap_grupo_diferenca_nula_e_semente():
    from src.evaluation.metrics import bootstrap_grupo

    rng = np.random.default_rng(1)
    p = rng.beta(1, 10, 4_000)
    y = (rng.random(4_000) < p).astype(int)
    grupos = np.arange(4_000)
    r = bootstrap_grupo(y, p, grupos, metrica="ap", prob_b=p, n=50, seed=7)
    assert r["estimativa_diferenca"] == 0 and r["ic_inferior"] <= 0 <= r["ic_superior"]
    r1 = bootstrap_grupo(y, p, grupos, metrica="auc", n=50, seed=7)
    r2 = bootstrap_grupo(y, p, grupos, metrica="auc", n=50, seed=7)
    assert r1 == r2 and r1["ic_inferior"] < r1["estimativa"] < r1["ic_superior"]


def test_bootstrap_grupo_ic_mais_largo_com_fichas_repetidas():
    from src.evaluation.metrics import bootstrap_grupo

    rng = np.random.default_rng(2)
    base = rng.beta(1, 10, 1_000)
    p = np.repeat(base, 3)
    y = np.repeat((rng.random(1_000) < base).astype(int), 3)
    grupos = np.repeat(np.arange(1_000), 3)
    por_linha = bootstrap_grupo(y, p, np.arange(3_000), metrica="auc", n=300, seed=3)
    por_grupo = bootstrap_grupo(y, p, grupos, metrica="auc", n=300, seed=3)
    assert (por_grupo["ic_superior"] - por_grupo["ic_inferior"]) > (por_linha["ic_superior"] - por_linha["ic_inferior"])


def test_bootstrap_grupo_brier_e_metrica_invalida():
    from src.evaluation.metrics import bootstrap_grupo

    p = np.array([0.1, 0.2, 0.8, 0.9] * 50)
    y = np.array([0, 0, 1, 1] * 50)
    r = bootstrap_grupo(y, p, np.arange(200), metrica="brier", n=30, seed=1)
    assert abs(r["estimativa"] - np.mean((y - p) ** 2)) < 1e-12
    with pytest.raises(ValueError):
        bootstrap_grupo(y, p, np.arange(200), metrica="f1")
```
6. Execute: `.\.venv\Scripts\python.exe -m pytest tests/test_metrics.py tests/test_errors.py -q`. Esperado: tudo passando (os testes antigos de `ic_bootstrap` continuam valendo).
7. **Duas medidas de calibração** (usadas pelo C_15 do #148, pelo #79 e pelo C_16). Cole ao **final** de `src/evaluation/calibration.py`, depois da última linha de `brier_decomposicao` (`    }`), com duas linhas em branco antes. Nada a apagar (`np`, `_to_np`, `_to_int_labels` e `ArrayLike` já estão no arquivo):

```python
def calibracao_intercepto_inclinacao(
    y_true: ArrayLike,
    y_prob: ArrayLike,
    eps: float = 1e-6,
) -> tuple[float, float]:
    """Regressão logística de y em logit(p): intercepto ideal 0 e inclinação ideal 1."""
    from sklearn.linear_model import LogisticRegression

    p = np.clip(_to_np(y_prob), eps, 1 - eps)
    z = np.log(p / (1 - p)).reshape(-1, 1)
    modelo = LogisticRegression(C=1e6, solver="lbfgs", max_iter=200).fit(z, _to_int_labels(y_true))
    return float(modelo.intercept_[0]), float(modelo.coef_[0, 0])


def ece_quantis(y_true: ArrayLike, y_prob: ArrayLike, n_bins: int = 10) -> float:
    """ECE com faixas de tamanho igual (quantis da probabilidade prevista)."""
    y, p = _to_int_labels(y_true), _to_np(y_prob)
    partes = np.array_split(np.argsort(p, kind="stable"), n_bins)
    return float(sum(len(i) * abs(y[i].mean() - p[i].mean()) for i in partes if len(i)) / len(y))
```
   Teste: acrescente ao **final** de `tests/test_calibration.py` (duas linhas em branco antes do `def`):

```python
def test_calibracao_intercepto_inclinacao_e_ece_quantis():
    from src.evaluation.calibration import calibracao_intercepto_inclinacao, ece_quantis

    rng = np.random.default_rng(0)
    p = rng.beta(1, 10, 100_000)
    y = (rng.random(100_000) < p).astype(int)

    intercepto, inclinacao = calibracao_intercepto_inclinacao(y, p)
    assert abs(intercepto) < 0.1 and 0.9 < inclinacao < 1.1
    assert ece_quantis(y, p) < 0.01

    inflada = np.clip(p * 2.5, 0, 1)
    assert calibracao_intercepto_inclinacao(y, inflada)[1] < 0.5
    assert ece_quantis(y, inflada) > 0.05
```
   Execute `.\.venv\Scripts\python.exe -m pytest tests/test_calibration.py -q`.
8. **Como usar nos outros cards** (não rode nada agora): IC de uma métrica, `bootstrap_grupo(y, prob, grupos, metrica="ap")`; diferença A − B entre dois modelos, `bootstrap_grupo(y, prob_a, grupos, metrica="auc", prob_b=prob_b)`. Use `n=300` quando houver mais de 1 milhão de linhas (≈ 2 min); caso contrário, o padrão do YAML (1.000 réplicas).
9. Commit: `feat: bootstrap por grupo, calibracao e padroes do YAML [done:#127] [done:#22]`. Avise no grupo (o #54 e o #148 usam as funções).

### ④ Pronto quando

- define: `src/evaluation/metrics.py` :: `bootstrap_grupo` | A função bootstrap_grupo existe em src/evaluation/metrics.py: sorteia grupos com reposição, ordena as probabilidades uma vez e devolve o IC de uma métrica ou, com prob_b, o IC da diferença pareada.
- contem: `tests/test_metrics.py` :: `bootstrap_grupo` | Há testes de bootstrap_grupo (igualdade com o scikit-learn, diferença nula, mesma semente, fichas repetidas).
- teste: `tests/test_metrics.py` | Os testes de métricas passam.
- nao-contem: `src/evaluation/metrics.py` :: `n_boot: int = 200` | O padrão fixo de 200 repetições do bootstrap deixou de existir (#22).
- define: `src/evaluation/calibration.py` :: `calibracao_intercepto_inclinacao` | A função de intercepto e inclinação de calibração existe em src/evaluation/calibration.py.
- define: `src/evaluation/calibration.py` :: `ece_quantis` | A função ece_quantis (ECE por faixas de tamanho igual) existe em src/evaluation/calibration.py.
- teste: `tests/test_calibration.py` | Os testes de calibração passam.

## #15 · Pré-processador e manifesto podem usar listas de variáveis diferentes

- prioridade: P2
- situação: aberta
- estratégia: desenvolver
- marco: M2
- data ideal: 31/10
- responsável: Pessoa C (dentro do #132)
- pessoas: C
- fonte: src/models/pipeline.py (FEATURES, build_preprocessor); notebooks C_11 a C_16
- depende de: #132
- tags: Código, Features
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 0
- novo: não
- professores: não
- removido: absorvido pelo #132 em 03/11 (o C_11 lê feature_columns do manifesto e confere que o artefato tem todas as colunas)

### ① Para entender

Do C_11 ao C_16, a tabela X é montada com as variáveis do **manifesto**, mas o pré-processador usa as listas do **YAML**. Hoje elas coincidem. Quando `features.final` for preenchida, podem divergir, e o pipeline falha ou treina com colunas erradas.

### ② Problema

> [!atenção] Replanejamento de 31/10 · versão 2 (entrega em 04/11)
> Replanejamento v2: este card é **resolvido dentro do card indicado em "responsável"**; sem esforço próprio. Marque como concluído junto com ele.

Do C_11 ao C_16, o X é montado com as features registradas no manifesto do artefato, mas o pré-processador é montado com as listas do YAML. Se as listas divergirem (por exemplo, quando `features.final` for preenchida ou o artefato for gerado com outra lista), o pipeline falha por coluna ausente ou treina com colunas diferentes das registradas.

### ③ O que fazer

**Resolvido dentro do #132 (passos de leitura).** Os notebooks C montam o pré-processador com as listas do manifesto (`numeric_columns`, `categorical_columns`) e, no início, conferem `set(manifest["feature_columns"]) == set(C.features_finais())`; se divergir, param com mensagem clara. Blocos extras das ablações são declarados explicitamente.

### ④ Pronto quando

- contem: `notebooks/C/C_11_pipeline_supervisionado.ipynb` :: `numeric_columns` | O C_11 monta o pré-processador com as listas numéricas registradas no manifesto do artefato (numeric_columns), e não com as do YAML.
- contem: `notebooks/C/C_11_pipeline_supervisionado.ipynb` :: `categorical_columns` | O C_11 monta o pré-processador com as listas categóricas do manifesto (categorical_columns).
- manual: | No início da cadeia C, set(manifest["feature_columns"]) é conferido contra features.final do YAML e o notebook para com mensagem clara se divergirem; blocos extras das ablações são declarados explicitamente.

## #64 · Testes que faltam

- prioridade: P2
- situação: resolvida
- estratégia: resolvida
- marco: M2
- data ideal: Concluído
- responsável: Pessoa C (dona; revisão cruzada sem edição concorrente)
- pessoas: C
- fonte: tests/
- depende de: #14, #16, #18, #20, #21, #86
- tags: Testes
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 3
- novo: não
- professores: não

### ① Para entender

Faltam testes para a fábrica e o mapeamento de nomes, a proteção do G9, a leitura parcial do artefato, `SRAG_PARQUET_URL`, `sha256_file` e a nova partição por hash. 55 funções públicas não têm teste (A43).

### ② Problema

Faltam testes para: fábrica e mapeamento de nomes (itens 20 e 21); G9 em `holdout_partition` (item 16); `audit_columns` e `columns=` no artefato (itens 7 e 18); `escolher_limiar(metrica="youden_j")`; sobrescrita de `SRAG_PARQUET_URL` (item 14); `hashing.sha256_file`.

### ③ O que fazer

> [!ok] Concluída. Os testes novos de seis blocos ficam no #131.

### ④ Pronto quando

- teste: `tests/test_model_pipelines.py` | Os testes da fábrica e dos pipelines passam (mapeamento de nomes, chaves do YAML, versão do scikit-learn).
- teste: `tests/test_supervised_artifact.py` | Os testes do artefato passam (G9, leitura parcial, partições).
- teste: `tests/test_config.py::test_srag_parquet_url` | O teste de SRAG_PARQUET_URL passa.

## #22 · Funções de avaliação com padrões diferentes do YAML

- prioridade: P3
- situação: aberta
- estratégia: desenvolver
- marco: M2
- data ideal: 31/10
- responsável: Pessoa A (dentro do #127)
- pessoas: A
- fonte: src/evaluation/metrics.py (ic_bootstrap); src/evaluation/errors.py (metricas_por_grupo)
- depende de: #127
- tags: Código, Metodologia
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 0
- novo: não
- professores: não

### ① Para entender

O intervalo de confiança por bootstrap usa 200 repetições por padrão (o YAML pede 1.000), e a análise por subgrupo ignora grupos com menos de 30 casos (o YAML pede 100). O C_16 passa os valores certos; qualquer outro uso recebe os antigos.

### ② Problema

> [!atenção] Replanejamento de 31/10 · versão 2 (entrega em 04/11)
> Replanejamento v2: este card é **resolvido dentro do card indicado em "responsável"**; sem esforço próprio. Marque como concluído junto com ele.

Os padrões das funções não seguem o YAML: `ic_bootstrap` usa 200 repetições (o YAML pede 1.000) e `metricas_por_grupo` usa mínimo de 30 casos por grupo (o YAML pede 100). O C_16 já passa os valores corretos, mas qualquer outro uso das funções recebe os padrões antigos.

### ③ O que fazer

**Resolvido dentro do #127 (passo 12, Pessoa A):** os padrões do bootstrap e do mínimo por grupo passam a vir do YAML (`avaliacao.bootstrap.repeticoes` = 1.000; `avaliacao.min_n_grupo` = 100).

### ④ Pronto quando

- nao-contem: `src/evaluation/metrics.py` :: `n_boot: int = 200` | O padrão fixo de 200 repetições do bootstrap saiu; o número vem do YAML (avaliacao.bootstrap.repeticoes = 1000).
- nao-contem: `src/evaluation/errors.py` :: `min_n: int = 30` | O mínimo de casos por grupo deixou de ser 30 fixo e vem do YAML (avaliacao.min_n_grupo = 100).

## #23 · A análise por subgrupo não calcula PR-AUC nem Brier

- prioridade: P3
- situação: aberta
- estratégia: desenvolver
- marco: M2
- data ideal: 27/10
- responsável: Pessoa A
- pessoas: A
- fonte: src/evaluation/errors.py (metricas_por_grupo)
- depende de: —
- tags: Código, Metodologia
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 2
- novo: não
- professores: não

### ① Para entender

A métrica principal do projeto (PR-AUC) e a de calibração (Brier) somem justamente na análise de equidade por ano, sexo, faixa etária e UF.

### ② Problema

A análise por subgrupo não calcula AP (PR-AUC) nem Brier. A métrica principal do projeto (`pr_auc`) e a métrica de calibração somem justamente na análise de equidade.

### ③ O que fazer

> [!decisão] Enxugado em 27/10 (eficiência primeiro)
> Passa para a Pessoa A (função curta com teste, na frente dela).

**Dono:** Pessoa A · **Prazo:** 27/10 (terça) · **Esforço estimado:** ≈ 1 h 30

1. Em `src/evaluation/errors.py::metricas_por_grupo`, acrescente por grupo: `n`, `prevalencia`, `pr_auc`, `pr_auc_sobre_prev`, `roc_auc`, `brier`, `o_e` (óbitos ÷ soma das probabilidades) e `suprimido` (grupo com menos de 100 fichas: métricas vazias).
2. Grupo com uma classe só devolve vazio, sem erro.
3. Teste em `tests/test_errors.py`: grupo só de curas → PR-AUC vazia.
4. `.\.venv\Scripts\python.exe -m pytest tests/test_errors.py -q`.

### ④ Pronto quando

- contem: `src/evaluation/errors.py` :: `pr_auc` | metricas_por_grupo calcula PR-AUC por grupo.
- contem: `src/evaluation/errors.py` :: `brier` | metricas_por_grupo calcula o Brier por grupo.
- contem: `src/evaluation/errors.py` :: `o_e` | metricas_por_grupo calcula a razão observado/esperado (o_e) por grupo.
- teste: `tests/test_errors.py` | Os testes de tests/test_errors.py passam, incluindo o caso de grupo com uma classe só (PR-AUC vazia, sem erro).

## #27 · O manifesto "mais recente" é escolhido pela data do arquivo

- prioridade: P3
- situação: aberta
- estratégia: desenvolver
- marco: M2
- data ideal: 01/11
- responsável: Pessoa C (dentro do #132); Pessoa A (C_16, #148)
- pessoas: C
- fonte: notebooks C_16; B_10_consolidacao_shortlist_transicao_coorte
- depende de: #132, #148
- tags: Código, Notebook
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 0
- novo: não
- professores: não
- removido: absorvido pelo #148 em 03/11 (o C_16 confere limiar e método do manifesto do C_15 contra o YAML)

### ① Para entender

O C_16 e o B_10 pegam o manifesto com a data de modificação mais nova. Copiar a pasta ou sincronizar pelo OneDrive muda essas datas e pode fazer o notebook ler o manifesto errado.

### ② Problema

> [!atenção] Replanejamento de 31/10 · versão 2 (entrega em 04/11)
> Replanejamento v2: este card é **resolvido dentro do card indicado em "responsável"**; sem esforço próprio. Marque como concluído junto com ele.

O C_16 e o B_10 escolhem o manifesto mais recente pela data de modificação do arquivo. Copiar ou sincronizar a pasta (OneDrive, git) altera essa data e pode fazer o notebook ler o manifesto errado.

### ③ O que fazer

**Resolvido dentro do #132 e do #148.** Nenhum notebook escolhe arquivo pela data: as saídas têm nome fixo em `outputs/final/` e o C_16 recalcula `identificador_execucao` e compara com `selecao_modelos.run_id_finalista`.

### ④ Pronto quando

- nao-contem: `notebooks/C/C_16_validacao_final.ipynb` :: `st_mtime` | O C_16 não escolhe mais o manifesto pela data de modificação do arquivo.
- contem: `notebooks/C/C_16_validacao_final.ipynb` :: `run_id_finalista` | O C_16 localiza o manifesto pelo run_id_finalista gravado no YAML pelo C_15.

## #58 · A mesma validação escolhe hiperparâmetros e mede o resultado

- prioridade: P3
- situação: parcial
- estratégia: documentar
- marco: M2
- data ideal: 01/11
- responsável: Pessoa B (dentro do #148, C_15)
- pessoas: B
- fonte: notebooks C_13 e C_15
- depende de: #148
- tags: Metodologia, Calibração
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 0
- novo: não
- professores: não
- removido: absorvido pelo #79 em 03/11; com o 70/15/15 vira limitação declarada (§29.33) no relatório

### ① Para entender

> [!decisão] Decisão de 18/10
> Resolvido pelo desenho do experimento: três validações disjuntas (`val_tune`, `val_cal`, `val_meas`), item 118.

O C_13 vai escolher os hiperparâmetros olhando a validação inteira. Depois, o C_15 mede o resultado em metade dessa mesma validação. Essa metade já influenciou a escolha, então a nota fica um pouco otimista.

| Etapa | Dados usados |
|---|---|
| C_13 busca | validação inteira (587.272) |
| C_15 calibra | val_cal (293.636) |
| C_15 mede | val_meas (293.636) ← já vista pelo C_13 |

### ② Problema

> [!atenção] Replanejamento de 31/10 · versão 2 (entrega em 04/11)
> Replanejamento v2: este card é **resolvido dentro do card indicado em "responsável"**; sem esforço próprio. Marque como concluído junto com ele.

A busca do C_13 usa a validação inteira. O C_15 divide a validação em duas metades e usa uma delas para medir o desempenho final antes do teste. Essa metade já influenciou a escolha dos hiperparâmetros, então a estimativa fica um pouco otimista.

### ③ O que fazer

**Resolvido por desenho; conferido no #148 (passo 1).** Com `val_tune` (escolhe), `val_cal` (calibra e escolhe o corte) e `val_meas` (só mede), nenhuma fatia escolhe e mede ao mesmo tempo. Falta confirmar que o `HONEST_CALIB_SPLIT` saiu do C_15 e escrever a frase de Métodos no #133 (Pessoa A).

### ④ Pronto quando

- nao-contem: `notebooks/C/C_15_calibracao_limiar.ipynb` :: `HONEST_CALIB_SPLIT` | A divisão da validação ao meio saiu do C_15: val_tune escolhe, val_cal calibra e escolhe o corte, val_meas só mede.
- manual: | O relatório (Métodos, #133) tem a frase explicando os três papéis da validação (val_tune, val_cal, val_meas).

## #119 · Conferir as saídas do teste e a comparação logística × boosting

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M5
- data ideal: 03/11
- responsável: Pessoa C (0,5 h) + Pessoa B (0,25 h)
- pessoas: C, B
- fonte: Plano integrado v2, seções 3 e 4; notebooks/E/E_02
- depende de: #2, #127
- tags: Modelagem, Notebook
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 0.75
- novo: sim
- professores: não
- removido: absorvido pelo #2 em 03/11 (conferência das saídas logo depois da abertura)

### ① Para entender

> [!ok] Decisão fechada em 18/10
> A coorte definitiva inicial será a seleção de features da coorte provisória. O treino principal usará exclusivamente 2019, 2023, 2024 e 2025. Haverá duas janelas de teste: (A) 2019, 2023, 2024 e 2025; (B) 2019 a 2025, incluindo 2020–2022. O ano de 2026 não participa do desenvolvimento nem dos testes principais e fica apenas como exploração opcional, depois de todo o restante concluído.

O E_02 deixa de treinar três cenários. Ele treina uma única vez com 2019, 2023, 2024 e 2025, congela o pipeline e produz dois relatórios de teste a partir das mesmas probabilidades e regras.

| Saída | População | Status |
|---|---|---|
| Relatório principal | `test_ref`: 2019, 2023–2025 | Resultado central do projeto |
| Relatório ampliado | `test_ref` + `test_pandemic`: 2019–2025 | Robustez temporal agregada |
| Relatório de domínio | `test_pandemic`: 2020–2022 | Explica a diferença entre principal e ampliado |

### ② Problema

> [!decisão] Replanejamento de 01/11
> Passou de 02/11 para **03/11, das 10h às 11h**, porque depende do teste (#2), agora em 03/11 às 8h.

> [!atenção] Replanejamento de 31/10 · versão 2 (entrega em 04/11)
> Vira **só a conferência** das saídas do C_16 (as tabelas agora saem em **um** arquivo, `teste_metricas.csv`) e a comparação pareada em `val_meas`, logo depois do #2. Nada é recalculado com o teste.

As duas janelas têm prevalências e composição temporal diferentes. Comparar apenas PR-AUC agregada seria insuficiente. É necessário reportar prevalência, PR-AUC/prevalência, ROC-AUC, Brier e calibração em cada janela e por ano.

### ③ O que fazer

> [!decisão] Replanejamento de 31/10 · versão 2
> O C_16 (#148, #2) gera tudo numa execução. Aqui se **confere**, sem abrir o teste de novo, e se acrescenta a comparação em `val_meas`.

**Dono:** Pessoa C (conferência e comparação) + Pessoa B (leitura das tabelas) · **Prazo:** 03/11 (terça), 10h às 11h · **Esforço estimado:** C ≈ 30 min · B ≈ 15 min · **Começa quando:** #2 e #127

#### O que precisa existir (nomes fixos em `outputs/final/`)
| Arquivo | Conteúdo |
|---|---|
| `teste_metricas.csv` | uma linha por janela: `teste_a`, `teste_b`, `pandemico`, `ano_2019` … `ano_2025`; colunas de n, óbitos, prevalência, PR-AUC e IC, PR-AUC ÷ prevalência, ROC-AUC e IC, Brier e IC, Brier do nulo, intercepto, inclinação, ECE e as métricas nos cortes `congelado` e `sens_70` |
| `teste_por_regiao.csv` | `regiao, n_obitos, sens_global, prec_global, sens_regional, prec_regional, usa_global` |
| `predicoes_teste.parquet` | `id_registro, group_id, particao, ano_internacao, regiao_residencia, sg_uf, faixa_etaria, sexo_categoria, y, prob_calibrada, classe` |
| `figuras/calibracao_teste_a.png` | curva de calibração do Teste A |
| `manifesto_teste.json` | SHA-256 do artefato, commit, hash do YAML, `run_id_finalista`, horário |

#### Passo a passo
1. **Pessoa C:** confira as linhas e os números: `teste_a` com n = 119.245 e prevalência ≈ 8,44%; `teste_b` com n = 3.035.074; `pandemico` com prevalência ≈ 26,4%; sete linhas de ano; nenhuma `prob_calibrada` vazia em `predicoes_teste.parquet`.
2. **Pessoa C: comparação pareada em `val_meas`** (as previsões das duas famílias estão em `outputs/final/predicoes_val_meas.parquet`, do C_15): `bootstrap_grupo(y, prob_boosting, grupos, metrica="ap", prob_b=prob_logistica)` e o mesmo para `auc` e `brier`; grave `outputs/final/comparacao_modelos_val_meas.csv`. É a evidência de que o finalista foi escolhido por diferença real (no `val_meas`, 39.749 linhas, 1.000 réplicas levam segundos).
3. **Leitura obrigatória** (vai para o relatório): a PR-AUC do Teste B pode ficar **maior** só porque 2020–2022 têm 26% de óbitos. Compare sempre PR-AUC ÷ prevalência e ROC-AUC. Escreva "robustez à mudança de período", nunca "efeito da pandemia".
4. **Pessoa B:** leia `teste_metricas.csv` e anote qualquer coluna que precise de rótulo ou unidade no relatório.
5. Comente no card o resumo: PR-AUC, PR-AUC ÷ prevalência, ROC-AUC, Brier e inclinação do Teste A e do Teste B (uma linha cada).

### ④ Pronto quando

- existe: `outputs/final/teste_metricas.csv` | As métricas de todas as janelas (Teste A, Teste B, 2020–2022 e cada ano) estão em outputs/final/teste_metricas.csv.
- existe: `outputs/final/teste_por_regiao.csv` | A sensibilidade e a precisão por região (corte global e regional) estão em outputs/final/teste_por_regiao.csv.
- existe: `outputs/final/predicoes_teste.parquet` | As previsões do teste foram exportadas com identificador, grupo, bloco, ano, região, UF, faixa, sexo, y, probabilidade calibrada e classe.
- existe: `outputs/final/comparacao_modelos_val_meas.csv` | A comparação pareada logística × boosting em val_meas está em outputs/final/comparacao_modelos_val_meas.csv.
- json: `data/analytical/manifesto_supervisionado.json` :: `test_opened` = `true` | O manifesto registra que o teste foi aberto (test_opened: true).

## #95 · 24/10: validar com os professores somente três pontos científicos, sem bloquear a implementação

- prioridade: P1
- situação: resolvida
- estratégia: resolvida
- marco: M0
- data ideal: Concluído
- responsável: Pessoa B (prepara e registra) + Equipe
- pessoas: B, Equipe
- fonte: Pauta_Orientacao_SRAG_v2.html; reunião de 16/10; orientação de 17/10
- depende de: —
- tags: Decisão
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 3
- novo: não
- professores: sim

### ① Para entender

> [!decisão] Reunião não bloqueante
> Período, coorte e desenho dos dois testes já estão decididos pela equipe. Em 24/10, os professores recebem o desenho como contexto, não como pergunta aberta.

| Pergunta essencial | Decisão padrão se não houver resposta |
|---|---|
| UMAP deve permanecer como exploração de representação, sem substituir o modelo principal? | Sim. |
| Região como feature, com métricas por UF, é suficiente para a discussão dos “vários Brasis”? | Sim; UF preditora é opcional. |
| A discussão acadêmica deve enfatizar robustez temporal entre as duas janelas de teste? | Sim; sem interpretação causal. |

### ② Problema

Na versão anterior, muitas decisões internas ficaram projetadas para os professores. Como a última conversa provável será em 24/10, isso criaria um bloqueio artificial. Os professores agregam mais valor validando a pergunta científica, a interpretação e o escopo.

### ③ O que fazer

> [!ok] Reunião realizada em 24/10. Respostas registradas abaixo.

| Pergunta | O que o professor disse | Decisão que vira regra |
|---|---|---|
| Três sintomas vazios em 2019 | Estudar; se ficar "muito determinístico", tirar; não tirar "só por tirar". | #50 com critério objetivo (D-17). |
| Queda da PR-AUC (0,44 → 0,30) | Natural: a PR-AUC depende do desbalanceamento. O modelo precisa ser pelo menos 25% melhor que o chute; 3,3× a 3,6× "está bom". ROC-AUC abaixo de 0,5 é desastre. | Critério mínimo de aceitação; sempre reportar PR-AUC ÷ prevalência. |
| Tirar a pandemia do treino | Faz sentido: o modelo usa o passado para prever o futuro, e a pandemia não tem padrão aplicável. Sugeriu, se der pouco trabalho, comparar 2019 com 2023–2025 para ver "se o mundo voltou". | Desenho mantido; comparação opcional no #138. |
| Peso de classe | Treinar com proporção diferente da real não impede o modelo de identificar perfis. | #5: decisão por evidência; calibração obrigatória. |
| Limiar | 80% de sensibilidade "já está bom"; 70% "já está muito bom". | #80: corte principal em 0,80; também reportar 0,70. |
| Não supervisionado "sem resultado" | "Resultado ruim não é ausência de resultado." Fazer ANOVA (numéricas) e qui-quadrado (qualitativas) entre os grupos. | Novos #136 e #137. |
| Geografia | Prática de mercado: modelo único e ponto de corte diferente por região; região como separação da análise, não como variável. | #110 reformulado. |
| Validação fixa sem validação cruzada | Aceita, por custo computacional. | Mantido. |
| Três blocos de validação + IC por bootstrap | "Atende." | Mantido. |
| Escopo | "É o primeiro trabalho, não TCC." | Cortar extras sem hipótese. |

Uma segunda conversa, com outro professor, não foi transcrita. Dela veio a cobrança de testar o não supervisionado depois de passar tudo o que fosse possível por one-hot (#136).

**Nada mais a fazer neste card.** As consequências estão nos itens citados.

### ④ Pronto quando

- manual: | As respostas da orientação de 24/10 estão registradas neste card, e cada uma aponta para o card onde virou regra (#50, #80, #110, #136, #137, #138, #5).

## #51 · As tabelas de óbito do B_06 usaram também os casos do teste

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M3
- data ideal: 31/10
- responsável: Pessoa B (0,5 h)
- pessoas: B
- fonte: B_06_eda_temporal_clustering
- depende de: #142
- tags: Metodologia, Vazamento, Notebook
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 0.5
- novo: não
- professores: não
- arquivos: notebooks/B/B_06_eda_temporal_clustering.ipynb

### ① Para entender

> [!decisão] Decisão de 18/10
> Com a partição-mestre, o B_06 pode refazer as tabelas de óbito só com `train_ref`.

As tabelas "mortalidade por variável" do B_06 foram feitas com a coorte inteira, antes de a partição existir. Isso inclui os 15% que viraram teste.

> [!atenção] Atenção
> É descritivo e não escolheu variáveis, então o risco é pequeno. Mas o princípio "não olhar o teste" foi violado e precisa ser declarado ou refeito só no treino.

### ② Problema

> [!atenção] Replanejamento de 31/10 · versão 2 (entrega em 04/11)
> **Executado e conferido em 31/10, 23h.** O B_06 rodou do início ao fim (120 de 120 células, sem erro) com a coorte definitiva e as tabelas de óbito só com o `train_ref`. A comparação com a versão anterior está feita para as 26 variáveis (ver "Comparação com a versão anterior"). Falta apenas colar o comentário final no card.

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que esta pendência está aberta
> A auditoria automática (27/10, 14:40) marcou "precisa revisão" por achados que não tratam deste item: a linha decorativa `=====` no cabeçalho de `src/protocolo/verificacoes.py` (lida como conflito de merge) e o `OneHotEncoder` denso do B_06, que roda numa amostra de 80 mil fichas e será substituído pelo #136 (detalhes no #94).
> Confirmado na saída do B_06 executado em 27/10: "Origem da análise do desfecho: coorte_sem_particao · Registros utilizados: 3.884.728". As tabelas `eda_02_obito_*` ainda usam a coorte inteira, inclusive casos de teste. Depende do `partitions_master.parquet` do #142.

As tabelas de desfecho do B_06 (letalidade por variável) usaram a coorte inteira, incluindo os casos que depois foram para o teste. Isso viola o princípio de não olhar o teste antes da avaliação final.

### ③ O que fazer

> [!decisão] Replanejamento de 31/10 · versão 2 (concluído em 31/10, 23h)
> Mudança pequena no B_06 e uma execução completa. A mortalidade base cai de 21,8% (coorte inteira) para 8,44% (`train_ref`).

**Dono:** Pessoa B · **Prazo:** 31/10 (sábado), 17h às 18h30 · **Esforço estimado:** ≈ 30 min (tudo feito; falta só colar o comentário final) · **Começa quando:** #142 (já concluído)

#### Estado em 31/10, 23h (execução completa do B_06, conferida)
- **Execução:** 120 de 120 células de código executadas, nenhuma saída de erro e nenhum aviso de depreciação.
- **Célula 2:** leu `coorte_final.parquet` (3.884.728 linhas); `Fichas sem bloco na partição-mestra: 4`; `Fichas em train_ref: 556462`. O `raise` de divergência com o manifesto não disparou.
- **Célula 71:** `Origem da análise do desfecho: particao_treino`; `Registros utilizados: 556462`; `Óbitos por SRAG: 46961` (8,44%).
- **Tabelas de óbito:** faixa etária, número de comorbidades e sexo somam, cada uma, 556.462 fichas, 46.961 óbitos e 509.501 curas. Os sintomas e as comorbidades têm as 13 linhas esperadas cada. A tabela "faixa × ano" mostra 30 linhas porque a célula imprime `.head(30)`; é exibição, não perda de dados.
- **Não aparece mais** `B06`, `B_06`, `Pessoa A/B/C`, `(#NN)`, "coorte provisória" nem `coorte_sem_particao`.

#### O que mudou no B_06 (aplicado e executado)
1. **Célula 2, leitura:** `resolve_cohort_path(..., kind="final")`; `id_registro` entrou em `COLUNAS_ESTRUTURA` e em `COLUNAS_OBRIGATORIAS_COORTE`.
2. **Célula 2, partição-mestra:** o notebook lê `data/analytical/partitions_master.parquet` (colunas `id_registro` e `particao`), confere que `id_registro` é único, alinha por `id_registro` (`reindex`, não pela posição das linhas) e confere as contagens por bloco com `manifesto_particao.json`; divergiu, levanta `ValueError`. As 4 fichas que a partição deixou de fora ficam sem bloco.
3. **Célula 71:** filtra `particao == "train_ref"`. Sem a coluna `particao` ou sem nenhuma ficha em `train_ref`, levanta erro; o caminho silencioso que usava a coorte inteira foi removido.
4. **Nomes:** os nove `COLUNAS_*_B06` viraram `COLUNAS_*`.
5. **Texto da célula 1:** a descrição temporal e o agrupamento usam todas as fichas (descrevem a base; não escolhem variáveis nem hiperparâmetros); as tabelas de associação com o desfecho usam só o `train_ref`.
6. **Série mensal:** `np.datetime64("NaT", "ns")` (acabou o aviso de depreciação). **Célula 3:** o comentário agora diz que cria as colunas que a coorte definitiva não traz prontas.

#### Comparação com a versão anterior (26 variáveis)
**Antes:** coorte provisória inteira, 3.915.136 fichas e 21,87% de óbitos (compilado de 31/10 às 18h56, de antes da correção). **Agora:** `train_ref` da coorte definitiva, 556.462 fichas e 8,44%. As tabelas antigas foram sobrescritas na pasta `outputs/`, mas a cópia no compilado de resultados permitiu comparar sem recalcular nada na coorte inteira (portanto, sem nova consulta ao desfecho dos blocos de teste). **Os números "antes" incluem as fichas de teste: use-os só nesta comparação, nunca no relatório.** ★ = trocou de sentido.

| Variável | Razão de chances bruta antes (coorte inteira) | Agora (`train_ref`) | IC 95% agora | Sentido |
|---|---|---|---|---|
| Saturação < 95% (`saturacao`) | 2,62 | 2,70 | 2,63 a 2,77 | risco |
| Dispneia (`dispneia`) | 2,16 | 2,46 | 2,39 a 2,53 | risco |
| Doença hepática (`hepatica`) | 1,80 | 1,98 | 1,83 a 2,15 | risco |
| Doença cardiovascular (`cardiopati`) | 1,63 | 1,87 | 1,82 a 1,91 | risco |
| Doença renal (`renal`) | 1,87 | 1,79 | 1,72 a 1,87 | risco |
| Fadiga (`fadiga`) | 1,32 | 1,66 | 1,62 a 1,70 | risco |
| Diabetes (`diabetes`) | 1,59 | 1,66 | 1,61 a 1,70 | risco |
| Desconforto respiratório (`desc_resp`) | 1,67 | 1,60 | 1,56 a 1,64 | risco |
| Imunodepressão (`imunodepre`) | 1,34 | 1,54 | 1,48 a 1,61 | risco |
| Pneumopatia (`pneumopati`) | 1,20 | 1,46 | 1,41 a 1,50 | risco |
| Obesidade (`obesidade`) | 1,32 | 1,26 | 1,20 a 1,32 | risco |
| Doença neurológica (`neurologic`) | 1,33 | 1,24 | 1,20 a 1,29 | risco |
| Perda do olfato (`perd_olft`) | 1,09 | 1,21 | 1,11 a 1,31 | risco |
| Outras morbidades (`out_morbi`) | 1,25 | 1,20 | 1,17 a 1,23 | risco |
| Perda do paladar (`perd_pala`) | 1,08 | 1,18 | 1,08 a 1,28 | risco |
| Dor abdominal ★ (`dor_abd`) | 0,96 | 1,10 | 1,06 a 1,15 | menor → risco |
| Diarreia (`diarreia`) | 1,00 | 1,06 | 1,02 a 1,09 | risco |
| Doença hematológica ★ (`hematologi`) | 1,01 | 0,90 | 0,84 a 0,98 | risco → menor |
| Outros sintomas (`outro_sin`) | 0,90 | 0,83 | 0,81 a 0,85 | menor |
| Dor de garganta (`garganta`) | 0,92 | 0,79 | 0,76 a 0,81 | menor |
| Vômito (`vomito`) | 0,72 | 0,63 | 0,61 a 0,65 | menor |
| Síndrome de Down (`sind_down`) | 0,58 | 0,52 | 0,47 a 0,57 | menor |
| Febre (`febre`) | 0,76 | 0,49 | 0,48 a 0,50 | menor |
| Puérpera (`puerpera`) | 0,34 | 0,37 | 0,29 a 0,45 | menor |
| Tosse (`tosse`) | 0,61 | 0,32 | 0,32 a 0,33 | menor |
| Asma (`asma`) | 0,30 | 0,22 | 0,21 a 0,23 | menor |

**Leitura:**
- **Sentido:** 24 das 26 variáveis mantêm o sentido; em 23 delas o intervalo de confiança fica longe de 1 nas duas versões. A correlação de postos entre as duas listas é 0,97, ou seja, a ordem de importância praticamente não mudou.
- **Duas trocaram de sentido, ambas perto de 1 e ambas entre as 31 variáveis do modelo:** dor abdominal (0,96, IC 0,95 a 0,97, para 1,10, IC 1,06 a 1,15) e doença hematológica (1,01, IC 0,99 a 1,04, para 0,90, IC 0,84 a 0,98). Em nenhuma das duas há associação forte em nenhuma das versões; o modelo é multivariado e a razão bruta perto de 1 não pede ação. O #140 só registra.
- **Mudanças de magnitude:** a mediana das variações é de 10,5%; cinco variáveis variaram mais de 20%: tosse (−47%), febre (−35%), asma (−27%), fadiga (+26%) e pneumopatia (+21%). A explicação provável, **não testada**, é a mudança de composição: o `train_ref` só tem 2019 e 2023 a 2025 e deixa de fora 2020 a 2022, quando 26% das internações terminavam em óbito. Não afirme isso no relatório sem testar (por exemplo, comparando as razões por ano).
- **Leitura para o #140 e o #91:** das 26 variáveis, 17 têm razão de chances bruta acima de 1 (associadas a maior risco) e 9 abaixo; em nenhuma o IC inclui 1. As abaixo de 1 são **brutas** e podem refletir confundimento pela idade; o #91 mostra a versão ajustada, e a redação escreve "associado a maior risco previsto", nunca "protege".

#### Para concluir o card
1. Abra o #51 no painel, cole o comentário abaixo e marque como concluído (o critério manual exige comentário):

```text
B_06 executado do início ao fim (120/120 células, sem erro) na coorte definitiva. Tabelas de óbito só com o train_ref: 556.462 fichas, 509.501 curas e 46.961 óbitos (8,44%); as tabelas de faixa etária, número de comorbidades e sexo somam esses totais. Comparação com a versão anterior (coorte inteira, 21,87% de óbitos) feita para as 26 variáveis: 24 mantêm o sentido e em 23 o IC fica longe de 1 nas duas versões. Duas trocaram de sentido, ambas perto de 1: dor abdominal (0,96 para 1,10) e doença hematológica (1,01 para 0,90). Maiores mudanças de magnitude: tosse, febre e asma. Nada exige ação no #140; as duas que trocaram de sentido só serão registradas.
```
2. O #136 (agrupamento) altera o B_06 de novo; a execução que fica salva no notebook é a do #126, em 04/11. Este card não espera por ela.
3. Commit (quando for a hora): `fix: tabelas de obito do B_06 so com train_ref [done:#51]`.

### ④ Pronto quando

- notebook-saida: `notebooks/B/B_06_eda_temporal_clustering.ipynb` :: `particao_treino` | As saídas salvas do B_06 mostram origem_analise_desfecho = particao_treino, ou seja, as tabelas de óbito × cura vieram só do train_ref.
- notebook-saida: `notebooks/B/B_06_eda_temporal_clustering.ipynb` :: `Fichas em train_ref: 556462` | As saídas do B_06 mostram as 556.462 fichas do train_ref, o mesmo número do manifesto da partição.
- contem: `notebooks/B/B_06_eda_temporal_clustering.ipynb` :: `partitions_master.parquet` | O B_06 junta a partição-mestra (partitions_master.parquet) por id_registro antes das tabelas de desfecho.
- nao-contem: `notebooks/B/B_06_eda_temporal_clustering.ipynb` :: `coorte_sem_particao` | O caminho silencioso que usava a coorte inteira (coorte_sem_particao) foi removido do B_06.
- nao-contem: `notebooks/B/B_06_eda_temporal_clustering.ipynb` :: `COLUNAS_ESTRUTURA_B06` | Os nomes de variáveis do B_06 não carregam mais o sufixo do número do notebook.
- manual: | O comentário final foi registrado neste card: totais do train_ref (556.462 fichas, 46.961 óbitos), a comparação das 26 variáveis com a versão anterior (24 mantêm o sentido) e as duas variáveis que trocaram de sentido (dor abdominal e doença hematológica), ambas perto de 1.

## #91 · Importância das variáveis do finalista (permutação no val_ref) e razões de chances ajustadas

- prioridade: P2
- situação: aberta
- estratégia: desenvolver
- marco: M7
- data ideal: 04/11
- responsável: Pessoa C (1,5 h)
- pessoas: C
- fonte: §29.20; revisão de 03/11 (absorve #57)
- depende de: #155
- tags: Modelagem, Interpretação
- pilar: Valor científico-acadêmico
- carga: 1.5
- novo: não
- professores: sim
- arquivos: notebooks/C/C_15_calibracao_limiar.ipynb

### ① Para entender

A banca vai perguntar "o que pesa mais no risco?". A resposta defensável tem duas partes: a importância por permutação do finalista (quanto o desempenho cai quando a variável é embaralhada) e as razões de chances da logística, que já vêm ajustadas pelas outras variáveis, inclusive a idade. Este card absorveu o #57: associações que parecem "protetoras" no bruto e somem com o ajuste pela idade.

### ② Problema

Nada disso existe ainda no código. Calcular no teste está fora de questão (o teste é aberto só para medir); o lugar certo é o `val_ref`, com o modelo congelado.

> [!decisão] Revisão de 03/11 · versão 4.0
> Roda na máquina oficial (#158), depois do C_15 final do #155 (passo 6). A importância por permutação usa `resultados[melhor_nome]["escolha"]["pipeline"]` e `X_val_meas`/`y_val_meas`, que existem no C_15.

### ③ O que fazer

**Dono:** Pessoa C · **Prazo:** 04/11, 17h às 18h30 · **Começa quando:** #155 (C_15 rodado com o modelo final)

1. No fim do C_15 (o modelo final já está treinado e calibrado ali), acrescente uma célula:
```python
from sklearn.inspection import permutation_importance
amostra = X_val_meas.sample(n=min(30_000, len(X_val_meas)), random_state=C.SEED)
y_am = y_val_meas.loc[amostra.index]
imp = permutation_importance(resultados[melhor_nome]["escolha"]["pipeline"], amostra, y_am, scoring="average_precision", n_repeats=5, random_state=C.SEED, n_jobs=-1)
tabela_imp = pd.DataFrame({"variavel": amostra.columns, "queda_pr_auc": imp.importances_mean, "dp": imp.importances_std}).sort_values("queda_pr_auc", ascending=False)
tabela_imp.to_csv(TABLES_DIR / "importancia_permutacao_val_meas.csv", index=False, encoding="utf-8-sig"); display(tabela_imp.head(15))
```
   (confira a chave do pipeline calibrado em `resultados[...]` antes de rodar.)
2. Razões de chances: treine a logística congelada em `train_ref` e grave os coeficientes exponenciados com nome da coluna one-hot em `outputs/tables/razoes_chances_logistica.csv` (`np.exp(coef_)` e `get_feature_names_out()` do pré-processador).
3. Para o relatório (#133): as 10 primeiras de cada tabela e a frase do #57 sobre asma, puerpério, tosse e febre.
4. Commit: `feat: importância das variáveis e razões de chances [done:#91]`.

### ④ Pronto quando

- contem: `notebooks/C/C_15_calibracao_limiar.ipynb` :: `permutation_importance` | O C_15 calcula a importância por permutação do finalista no val_ref.
- manual: | As tabelas importancia_permutacao_val_meas.csv e razoes_chances_logistica.csv foram geradas e as 10 primeiras linhas de cada uma estão no relatório.

## #55 · Equidade e desempenho por ano, região, faixa etária e raça/cor, e perfil dos óbitos sem alerta, a partir das saídas do C_16

- prioridade: P2
- situação: aberta
- estratégia: desenvolver
- marco: M7
- data ideal: 05/11
- responsável: Pessoa A (1,25 h)
- pessoas: A
- fonte: §22 e §29.8; orientação do TCC (equidade); revisão de 03/11 (v4.1: recebe a versão mínima do corte por região)
- depende de: #2
- tags: Resultados, Equidade
- pilar: Valor científico-acadêmico
- carga: 1.25
- novo: não
- professores: sim

### ① Para entender

Um modelo pode ir bem na média e mal num grupo. O protocolo pede métricas por ano, região, UF e faixa etária, e uma olhada nos óbitos que ficaram sem alerta (falsos negativos).

**Corte por região, versão mínima (decisão da equipe em 03/11).** O professor sugeriu, em 24/10, um modelo único com um ponto de corte diferente por região. Foi decidido fazer só a versão mínima: **modelo único, corte global e métricas e calibração por região no teste**. O corte regional em si não é implementado e fica como trabalho futuro, por falta de tempo antes do teste. A tabela por região mostra exatamente a diferença de sensibilidade que um corte regional tentaria corrigir.

### ② Problema

> [!decisão] Revisão de 03/11 · versão 4.0
> O C_16 novo **já grava** as tabelas por grupo (Teste A e Teste B), por ano, e a distribuição dos falsos negativos por região e faixa etária. Este card não calcula nada novo: lê as tabelas, faz a figura e escreve a leitura. Nenhum código do C_15 nem do C_16 muda por causa do corte por região.

Depois do #2, o teste não pode ser carregado de novo (`G9_holdout: executado`). Tudo sai dos arquivos que o C_16 gravou em `outputs/tables/` (prefixo `C6_validacao_final_<carimbo>`):

| Arquivo | O que tem |
|---|---|
| `*_por_grupo_teste_a_regiao_residencia.csv` | n, óbitos, PR-AUC, Brier, razão observado/esperado, sensibilidade e precisão no corte global, por região (Teste A) |
| `*_por_grupo_teste_a_faixa_etaria.csv`, `..._sexo_categoria.csv`, `..._sg_uf.csv`, `..._cs_raca.csv`, `..._cs_zona.csv` | o mesmo, por faixa etária, sexo, UF, raça/cor e zona (Teste A) |
| `*_por_grupo_teste_b_*.csv` | por região, UF, sexo, faixa etária e ano (Teste B; raça/cor e zona **não** saem no Teste B, porque as variáveis do modelo só ficam guardadas na janela principal) |
| `*_fn_por_regiao_residencia.csv`, `*_fn_por_faixa_etaria.csv` | óbitos sem alerta por grupo (Teste A) |
| `*_metricas_por_ano.csv` | por ano de 2019 a 2025 (Teste B) |

Grupos com menos de 100 fichas aparecem com as métricas vazias e `suprimido=True`.

### ③ O que fazer

**Dono:** Pessoa A · **Prazo:** 05/11, 10h às 11h15 · **Começa quando:** #2 · **Script previsto:** `tabelas_relatorio.py` (lê os CSV do C_16 e gera as tabelas em Markdown e as figuras; começa por relatório).

1. **Tabelas do relatório:** por região, faixa etária, raça/cor e ano: n, óbitos, PR-AUC ÷ prevalência, sensibilidade e precisão. Marque os grupos suprimidos.
2. **Falsos negativos do Teste A:** distribuição por faixa etária e região (contagem e % dos óbitos sem alerta).
3. **Leitura para o relatório (uma frase por tabela):** a diferença máxima de sensibilidade entre regiões; a faixa etária com mais óbitos sem alerta; se algum grupo de raça/cor tem sensibilidade ou calibração (razão observado/esperado) bem diferente; **o que o modelo não permite concluir** (heterogeneidade pode refletir acesso, capacidade e registro, e `cs_raca` tem muito branco e "ignorado"). Nunca uma causa.
4. **Corte por região (versão mínima):** uma figura com a sensibilidade e a precisão de cada região **no corte global** (barras, com a sensibilidade média como linha) e a razão observado/esperado por região. Escreva a frase de limitação, com os números: "O professor sugeriu um corte de decisão diferente por região. Implementamos a versão mínima (modelo único, corte global e métricas e calibração por região). Com o mesmo corte, a sensibilidade varia de X a Y entre as regiões, o que um corte regional tentaria corrigir; deixamos como trabalho futuro." Sem causa: "pode refletir acesso, capacidade e registro".
5. Commit: `feat: equidade e desempenho por grupo no Teste A [done:#55]`.

### ④ Pronto quando

- manual: | As tabelas por região, faixa etária, raça/cor e ano, a distribuição dos falsos negativos e a leitura (com o que não se pode concluir) estão no relatório, geradas a partir dos CSV do C_16.
- manual: | O relatório tem a figura de sensibilidade e precisão por região no corte global e a frase de limitação do corte regional (versão mínima, trabalho futuro).

## #57 · Associações "protetoras" que são efeito da idade

- prioridade: P3
- situação: aberta
- estratégia: explorar
- marco: M6
- data ideal: 02/11
- responsável: Pessoa B (dentro do #91)
- pessoas: B
- fonte: B_06_eda_temporal_clustering
- depende de: #91
- tags: Metodologia
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 0
- novo: não
- professores: não
- removido: absorvido pelo #91 em 03/11 (leitura ajustada pela idade junto da tabela de importância)

### ① Para entender

> [!decisão] Decisão de 18/10
> Resolvido pela análise ajustada do item 91 (razões de chances da logística).

Nas contas simples, quem tem asma morre menos. Asma não protege: é comum em crianças, e crianças morrem menos. Isso é **confundimento**.

<div class="bars">
<div class="br"><span class="y">Com asma</span><div class="t"><div class="b gn" style="width:35.6%"></div></div><span class="v">11,4%</span></div>
<div class="br"><span class="y">Sem asma</span><div class="t"><div class="b " style="width:93.4%"></div></div><span class="v">29,9%</span></div>
<div class="br"><span class="y">Com tosse</span><div class="t"><div class="b gn" style="width:59.1%"></div></div><span class="v">18,9%</span></div>
<div class="br"><span class="y">Sem tosse</span><div class="t"><div class="b " style="width:86.6%"></div></div><span class="v">27,7%</span></div>
</div>

Uma análise ajustada pela idade (item 91) resolve e é uma das perguntas aos professores.

### ② Problema

> [!atenção] Replanejamento de 31/10 · versão 2 (entrega em 04/11)
> Replanejamento v2: este card é **resolvido dentro do card indicado em "responsável"**; sem esforço próprio. Marque como concluído junto com ele.

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que esta pendência está aberta
> A auditoria automática (27/10, 14:40) marcou "precisa revisão" por achados que não tratam deste item: a linha decorativa `=====` no cabeçalho de `src/protocolo/verificacoes.py` (lida como conflito de merge) e o `OneHotEncoder` denso do B_06, que roda numa amostra de 80 mil fichas e será substituído pelo #136 (detalhes no #94).
> Feito dentro do #91, que depende do G6.

Associações que parecem "protetoras" (asma, tosse, febre) podem ser efeito da idade: são mais comuns em crianças, que morrem menos.

### ③ O que fazer

**Resolvido dentro do #91 (passo 5).** A tabela "bruto × ajustado" mostra quais associações "protetoras" (asma 0,30; puerpério 0,34; tosse 0,61) somem ou mudam de sinal depois do ajuste. A Pessoa B escreve o parágrafo da Discussão em 02/11.

### ④ Pronto quando

- manual: | O parágrafo da Discussão mostra quais associações "protetoras" (asma, puerpério, tosse) somem ou mudam de sinal depois do ajuste, usando a tabela "bruto × ajustado" do #91.

## #89 · Revisar a conclusão do A_09 de que o sorteio é "otimista"

- prioridade: P3
- situação: aberta
- estratégia: documentar
- marco: M6
- data ideal: 01/11
- responsável: Pessoa A (dentro do #133, seções 2 a 4)
- pessoas: A
- fonte: notebooks A_09 (seção 3, benchmark); outputs/tables/pessoa_a/a3_benchmark_split.csv
- depende de: —
- tags: Metodologia, Partição
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 0
- novo: não
- professores: não
- removido: obsoleto em 03/11: o notebook A_09 não existe mais

### ① Para entender

> [!decisão] Decisão de 18/10
> O E_02 substitui esta discussão: a comparação passa a usar PR-AUC ÷ prevalência, ROC-AUC e Brier calibrado, com IC pareado.

O A_09 comparou sorteio × temporal e concluiu "o aleatório está otimista; decidir pelo temporal", porque a PR-AUC caiu de 0,452 para 0,364. Mas a PR-AUC depende da **proporção de óbitos**, e ela era bem menor na validação temporal.

<div class="bars">
<div class="br"><span class="y">Sorteio: PR-AUC</span><div class="t"><div class="b " style="width:90.4%"></div></div><span class="v">0,452</span></div>
<div class="br"><span class="y">Temporal: PR-AUC</span><div class="t"><div class="b or" style="width:72.8%"></div></div><span class="v">0,364</span></div>
</div>

<div class="bars">
<div class="br"><span class="y">Sorteio: × chute</span><div class="t"><div class="b " style="width:65.3%"></div></div><span class="v">2,0×</span></div>
<div class="br"><span class="y">Temporal: × chute</span><div class="t"><div class="b gn" style="width:88.0%"></div></div><span class="v">2,6×</span></div>
</div>

<div class="bars">
<div class="br"><span class="y">Sorteio: ROC-AUC</span><div class="t"><div class="b " style="width:77.4%"></div></div><span class="v">0,774</span></div>
<div class="br"><span class="y">Temporal: ROC-AUC</span><div class="t"><div class="b gn" style="width:82.1%"></div></div><span class="v">0,821</span></div>
</div>

> [!exemplo] Exemplo
> Um aluno tira 6 numa prova fácil e 5 numa prova muito mais difícil. A nota caiu, mas o desempenho relativo melhorou.

### ② Problema

> [!atenção] Replanejamento de 31/10 · versão 2 (entrega em 04/11)
> Replanejamento v2: uma frase ou parágrafo dentro do **#133** (domingo, Pessoa A); sem esforço próprio.

No benchmark do A_09 (logística, cerca de 140 mil de treino e 30 mil de validação), a prevalência na validação foi 23,1% no sorteio e 13,8% no temporal. A PR-AUC de um classificador aleatório é igual à prevalência, então a comparação direta favorece o cenário com mais óbitos. Relativa ao chute, a PR-AUC temporal é maior (2,6× contra 2,0×), e a ROC-AUC também (0,821 contra 0,774). O mesmo padrão aparece sem 2020–21. A conclusão registrada no notebook pode levar a uma decisão de período e divisão (item 85) com base numa leitura incompleta.

### ③ O que fazer

**Pessoa A, dentro do #133 (01/11):** parágrafo de Métodos: "A PR-AUC depende da prevalência; por isso todas as comparações entre períodos usam também PR-AUC ÷ prevalência e ROC-AUC." Use a própria coorte: a PR-AUC da logística caiu de 0,44 (22% de óbitos) para 0,30 (8,4%), mas, contra o acaso, subiu de 2,0× para 3,6×. Cite a regra do professor (modelo pelo menos 25% melhor que o acaso). Não rodar o A_09.

### ④ Pronto quando

- manual: | O parágrafo de Métodos explica que a PR-AUC depende da prevalência, por isso todas as comparações entre períodos usam também PR-AUC ÷ prevalência e ROC-AUC, com o exemplo da coorte (0,44 com 22% de óbitos × 0,30 com 8,4%, de 2,0× para 3,6× contra o acaso).

## #110 · Geografia como separação da análise: ponto de corte por região e equidade (sem região como variável)

- prioridade: P3
- situação: aberta
- estratégia: desenvolver
- marco: M5
- data ideal: 03/11
- responsável: Pessoa A (dentro do #55)
- pessoas: A
- fonte: artefato supervisionado (sg_uf); E_03; orientação de 17/10
- depende de: #80, #2
- tags: Features, Geografia
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 0
- novo: sim
- professores: não
- removido: absorvido pelo #55 em 03/11 (descrição por região a partir das saídas do C_16)

### ① Para entender

O Brasil tem realidades muito diferentes entre regiões ("vários Brasis"). Colocar a UF como variável faria o modelo aprender acesso a UTI, capacidade hospitalar e qualidade do registro, e não algo do paciente.

> [!ok] Orientação de 24/10
> O professor descreveu a prática de mercado: **um modelo único** para todo o país e um **ponto de corte diferente por região**. A geografia entra como separação da análise, não como variável.

| O que fazemos | Para quê |
|---|---|
| Modelo principal sem geografia | Variáveis com significado clínico |
| Ablação "P + região" (#54) | Só para medir quanto a região acrescentaria |
| Ponto de corte por região | Utilidade local: cada região com sensibilidade de 80% |
| Métricas e calibração por região e UF | Equidade: o modelo erra mais ou superestima o risco em algum lugar? |

### ② Problema

> [!decisão] Replanejamento de 01/11
> Acompanha o #55: passou de 02/11 para 03/11, depois do teste (#2).

> [!atenção] Replanejamento de 31/10 · versão 2 (entrega em 04/11)
> **Absorvido pelo #55** (figura e texto de regiões) e pelo #80 (cálculo dos cortes por região). Sem esforço próprio.

Geografia nunca foi testada como variável.

### ③ O que fazer

**Resolvido dentro do #80 e do #55.** O cálculo dos cortes por região está no #80 (Pessoa C, domingo); a medição no teste está no C_16 (#148); a figura e as três frases estão no #55 (Pessoa A, segunda-feira). Marque como concluído junto com o #55.

### ④ Pronto quando

- existe: `outputs/final/limiares_por_regiao.csv` | Os cortes com sensibilidade ≥ 0,80 por região, escolhidos em val_cal, estão em outputs/final/limiares_por_regiao.csv.
- existe: `outputs/final/teste_por_regiao.csv` | A sensibilidade e a precisão por região no teste (corte global e regional) estão em outputs/final/teste_por_regiao.csv.
- existe: `outputs/final/figuras/regiao_corte_global_regional.png` | A figura por região (corte global × regional) existe.

## #138 · Opcional: "o mundo voltou?" Comparar 2019 com 2023–2025

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 05/11
- responsável: Pessoa C ou Pessoa B, se sobrar tempo
- pessoas: C, B
- fonte: Orientação de 24/10 (sugestão do professor)
- depende de: #132
- tags: Metodologia, Temporal
- pilar: Valor científico-acadêmico
- carga: —
- novo: sim
- professores: sim
- removido: removido na revisão de 03/11 (v3.2): o desempenho por ano do Teste B (#2 e #55) já mostra 2019 contra 2023–2025

### ① Para entender

O professor sugeriu verificar se, depois da pandemia, o padrão de risco "voltou" ao de antes. Uma forma barata: treinar só com o pós-pandemia e ver como o modelo se sai no pré-pandemia.

### ② Problema

Não bloqueia nada; é exploração para a Discussão.

### ③ O que fazer

> [!decisão] Enxugado em 27/10 (eficiência primeiro)
> **Pós-entrega.** A comparação 2019 × 2023–2025 sai do plano; o desempenho por ano (já no #119) mostra a diferença de 2019.

### ④ Pronto quando

- manual: | (Pós-entrega, opcional) A comparação 2019 × 2023–2025 foi feita e comentada, ou foi registrado que ficou fora; o desempenho por ano do #119 já mostra a diferença de 2019.

## #111 · Recorte só de São Paulo como entrega mínima

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Plano B
- data ideal: 01/11
- responsável: Equipe
- pessoas: Equipe
- fonte: orientação de 17/10
- depende de: #79
- tags: Dados/Coorte
- pilar: —
- carga: —
- novo: sim
- professores: não
- removido: removido na revisão de 03/11 (v3.2): o gatilho (01/11, medido em val_meas como bloco) passou e não foi acionado; o modelo é avaliado na coorte inteira

### ① Para entender

Plano de segurança do professor: se o modelo nacional ficar ruim, entregar SP funcionando. Como a partição e o código serão parametrizados, isso vira um filtro.

### ② Problema

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: gatilho ajustado para o novo calendário (conferido na hora do #79, em 01/11).

Fazer agora gastaria tempo num resultado que talvez nem seja necessário.

### ③ O que fazer

Continua despriorizado. **Gatilho revisado:** acionar só se, em 01/11 (#79), o finalista calibrado tiver PR-AUC ÷ prevalência abaixo de 1,5 em `val_meas` **e** calibração ruim (inclinação fora de 0,8–1,2 ou O/E fora de 0,9–1,1). Nesse caso, a Pessoa A reúne a equipe na mesma noite: o recorte de SP vira **análise de sensibilidade** no relatório (um filtro `sg_uf == "SP"` sobre as previsões já salvas), e não substituto do resultado nacional. Ninguém precisa fazer nada se o gatilho não disparar.

### ④ Pronto quando

- manual: | Em 28/10 alguém conferiu o gatilho (PR-AUC ÷ prevalência abaixo de 1,5 em val_meas e O/E fora de 0,9–1,1) e registrou neste card que ele não disparou, ou que o recorte de SP virou sensibilidade.

## #1 · G6 e ajuste fino no val_ref: aprovar a grade, rodar o C_13 e congelar finalista e hiperparâmetros

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M4
- data ideal: 03/11
- responsável: Pessoa C (2 h) + Pessoa A (0,25 h)
- pessoas: C, A
- fonte: §29.17 (plano do G6); revisão de 03/11 (absorve #78)
- depende de: #132
- tags: Modelagem, Gate, Tuning
- pilar: Performance + Valor científico-acadêmico
- carga: 2.25
- novo: não
- professores: não
- arquivos: notebooks/C/C_13_boosting.ipynb, configs/supervised.yaml

### ① Para entender

O ajuste fino escolhe, para cada família finalista (logística e boosting), a melhor configuração de hiperparâmetros, e depois escolhe o finalista entre as duas. Tudo é medido no `val_ref`; o teste continua fechado. Este card produz o **modelo de referência** (grade curta do YAML). Em 04/11 a equipe tenta superá-lo no #155; se ninguém superar pela regra, ele é o modelo final. Este card absorveu a aprovação do G6 (#78): o G6 **libera** a busca, e o resultado da busca fica registrado no YAML e no decisoes.md.

### ② Problema

> [!decisão] Revisão de 03/11 · versão 3
> As nove "divergências a resolver" da §29.17 foram fechadas abaixo com o que **já está no YAML e no C_13**, para não gastar tempo de decisão: a grade é a do YAML, a escolha é por PR-AUC no `val_ref` e o peso de classe entra na própria busca.

Situação no código: o C_13 só busca com `gates.G6_finalistas_tuning.status = aprovado` (hoje `pendente`); a grade vem de `models.*.busca_*` (logística: C ∈ {0,001; 0,01; 0,1; 1; 10} × peso ∈ {balanced; None}; boosting: learning_rate ∈ {0,03; 0,05; 0,1} × max_iter ∈ {500; 1000} × peso ∈ {balanced; None}); `tuning.metrica_principal: pr_auc`; o resultado sai como proposta de YAML em `outputs/tables/`. `selecao_modelos.finalista_escolhido` está `null` e o C_16 exige esse campo.

### ③ O que fazer

**Dono:** Pessoa C (A aprova o G6 com ela) · **Prazo:** 03/11, 10h45 às 13h45 (inclui máquina) · **Começa quando:** #132 (artefato com as 30 variáveis)

1. **Aprovar o G6 (A e C, 5 min).** Em `configs/supervised.yaml`, no bloco `G6_finalistas_tuning`: `status: aprovado`, `aprovado_por: Pessoa A e Pessoa C`, `data: "2026-11-03"`.
2. **Rodar a busca (C):**
```powershell
.\.venv\Scripts\python.exe tools\medir_notebook.py notebooks\C\C_13_boosting.ipynb --salvar-no-lugar --limite-s 5400
```
3. **Escolher (regras da §29.17, decididas antes dos números):**
   - dentro de cada família: maior PR-AUC no `val_ref`; diferença < 0,002 → a configuração mais simples (menos iterações, C maior);
   - entre famílias: o boosting só é o finalista se superar a logística em ≥ 0,005 de PR-AUC; senão, a logística;
   - peso de classe: `balanced` só fica se ganhar ≥ 0,005 de PR-AUC; senão `None` (o Brier calibrado é conferido no #79).
4. **Congelar no YAML** a partir da proposta que o C_13 gravou (`outputs/tables/C4_boosting_final_*_proposta_yaml.yaml`): os hiperparâmetros de `models.logistic` e `models.boosting` (incluindo `class_weight`), `selecao_modelos.finalista_escolhido` e `selecao_modelos.status: finalista_congelado`.
5. **Registrar (A, 10 min):** `#### 29.35 03/11 · G6: hiperparâmetros e finalista` no decisoes.md (tabela das duas melhores configurações por família, com PR-AUC, ROC-AUC e Brier, e a regra aplicada).
6. Rode `.\.venv\Scripts\python.exe -m pytest -m "not slow" -q` e faça o commit: `feat: G6 aprovado, hiperparâmetros e finalista congelados [done:#1]`. Avise a Pessoa B: o #79 começa às 14h.

> [!atenção] Congelar o `class_weight` (acrescentado em 03/11, v4.0)
> A fábrica descarta `null` do YAML, então `class_weight: null` **não** treina sem peso (vale `balanced`). Para "sem peso", escreva `class_weight: {}`. Rode o C_13 e o C_15 na **máquina oficial** (#158). Depois de editar o YAML, confira (deve imprimir `{}` para a família sem peso):

```powershell
.\.venv\Scripts\python.exe -c "from src.models.factory import build_finalista as b;print(b('logistic').steps[-1][1].class_weight, b('boosting').steps[-1][1].class_weight)"
```

### ④ Pronto quando

- yaml: `configs/supervised.yaml` :: `gates.G6_finalistas_tuning.status` = `aprovado` | O G6 está aprovado no supervised.yaml.
- yaml: `configs/supervised.yaml` :: `selecao_modelos.finalista_escolhido` != `null` | O finalista escolhido está congelado no YAML (o C_15 e o C_16 dependem dele).
- yaml: `configs/supervised.yaml` :: `models.boosting.learning_rate` != `null` | Os hiperparâmetros do boosting saíram do estado "a definir".
- yaml: `configs/supervised.yaml` :: `models.logistic.C` != `null` | O C da logística saiu do estado "a definir".
- notebook-saida: `notebooks/C/C_13_boosting.ipynb` :: `aprovado=True` | A saída salva do C_13 mostra que a busca rodou com o G6 aprovado.
- contem: `docs/decisoes.md` :: `G6: hiperparâmetros e finalista` | O decisoes.md registra a escolha (entrada 29.35) com a regra aplicada e os números.

## #3 · Garantir que a busca de hiperparâmetros termine a tempo

- prioridade: P1
- situação: resolvida
- estratégia: resolvida
- marco: M4
- data ideal: Concluído
- responsável: Pessoa C (dona; revisão cruzada sem edição concorrente)
- pessoas: C
- fonte: notebooks C_13; configs/supervised.yaml (models.boosting, tuning.max_configuracoes_por_modelo)
- depende de: —
- tags: Modelagem, Memória/Desempenho
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 5
- novo: não
- professores: não

### ① Para entender

Cada configuração testada treina um modelo inteiro sobre 2,74 milhões de linhas. Com até 30 configurações e boosting de até 1.000 árvores sem parada antecipada, a busca pode levar horas.

<div class="kpi">
<div><b>2,74 mi</b>linhas de treino</div>
<div><b>até 30</b>configurações por modelo</div>
<div><b>36</b>combinações na grade do boosting</div>
</div>

> [!exemplo] Exemplo
> Na rodada de 16/10, o boosting com valores padrão levou ~10 s numa amostra de 300 mil linhas. Multiplicando por 9× mais linhas, mais árvores e 30 configurações, a conta passa fácil de uma hora.

### ② Problema

A grade do boosting inclui `max_iter` de até 1.000, com `early_stopping: false`, até 30 configurações e o treino inteiro da coorte. Cada configuração treina um HistGradientBoosting completo sobre a base toda, o que cria risco real de a busca não terminar até 17/10.

### ③ O que fazer

> [!ok] Concluída (confirmada no painel): limites de tempo definidos.

**Regra para a busca de 27/10 (#1), alinhada com isto:** subamostra estratificada por ano × alvo de até 600 mil linhas de `train_ref` **por grupo** (nunca por linha), early stopping ligado e 12 configurações. Medir primeiro uma configuração: se passar de 6 minutos, cortar para 8 configurações. Registrar no `Run` o tamanho da subamostra e o tempo total.

### ④ Pronto quando

- yaml: `configs/supervised.yaml` :: `tuning.max_configuracoes_por_modelo` existe | O YAML limita o número de configurações por modelo na busca.
- contem: `src/models/boosting.py` :: `early_stopping: bool = True` | O boosting do src usa early stopping por padrão, o que limita o tempo de cada configuração.

## #5 · Decidir se o peso das classes fica, já que ele infla as probabilidades

- prioridade: P1
- situação: parcial
- estratégia: desenvolver
- marco: M3
- data ideal: 01/11
- responsável: Pessoa C (1 h)
- pessoas: C
- fonte: src/models/logistic.py; src/models/boosting.py; configs/supervised.yaml (class_weight); B_10
- depende de: #1, #148
- tags: Modelagem, Calibração
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1
- novo: não
- professores: não
- removido: absorvido pelo #79 em 03/11 (peso de classe decidido na tabela de comparação do C_15)

### ① Para entender

> [!decisão] Decisão de 18/10
> Testar `class_weight=None` como uma das 12 configurações da busca; decidir pela calibração em `val_cal`.

Como só 1 em 5 morre, os modelos usam `class_weight="balanced"`: dão peso extra aos óbitos. Isso ajuda a encontrá-los, mas infla as porcentagens.

<div class="bars">
<div class="br"><span class="y">Previsto (boosting)</span><div class="t"><div class="b red" style="width:84.8%"></div></div><span class="v">42,4%</span></div>
<div class="br"><span class="y">Previsto (logística)</span><div class="t"><div class="b red" style="width:86.0%"></div></div><span class="v">43,0%</span></div>
<div class="br"><span class="y">Real</span><div class="t"><div class="b gn" style="width:43.8%"></div></div><span class="v">21,9%</span></div>
</div>

> [!exemplo] Exemplo
> Uma balança que soma 20 kg em todo mundo ainda diz quem é mais pesado, mas o número não serve como peso. A calibração do C_15 "ajustou a balança": Brier caiu de 0,196 para 0,141.

Falta decidir se mantemos o peso + calibração ou se testamos treinar sem peso no ajuste fino.

### ② Problema

> [!atenção] Replanejamento de 31/10 · versão 2 (entrega em 04/11)
> Domingo, 12h30 às 13h30, **depois do #1 e do C_15 pronto (#148)**. A regra de decisão não mudou (0,005 de PR-AUC e Brier calibrado que não piora). A comparação usa sempre `sigmoid`, para não criar ciclo com a escolha do método no #79.

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que voltou para "em andamento"
> Marcada como concluída em 27/10 (14:39). O que foi feito está certo e é útil: o commit `35b90f8` acrescentou `busca_class_weight: [balanced, null]` na logística e no boosting, e o C_13 passou a variar o peso de classe na busca (`_candidatos_boosting` e `_candidatos_logistica`).
> O que falta para concluir, conforme o "O que fazer": (1) rodar a comparação (o C_13 tem 0 de 9 células executadas); (2) comparar com e sem peso no modelo vencedor, olhando PR-AUC e **Brier depois da calibração**; (3) gravar a escolha no YAML (`class_weight` continua `balanced` fixo nas famílias). Além disso, a busca roda sobre o artefato antigo e o vocabulário antigo (`treino/validacao`), que dependem do #131 e do #132.

Os dois finalistas usam `class_weight="balanced"`. A média das probabilidades previstas ficou em 42,4% (boosting) e 43,0% (logística), contra prevalência real de 21,9%. Isso não afeta a ordenação (ROC-AUC, PR-AUC), mas afeta Brier, calibração e qualquer limiar.

**Atualização 17/10:** o C_15 mostrou que a calibração corrige o problema (boosting: Brier 0,1959 → 0,1409; ECE 0,0018). Ainda não foi testado treinar sem peso.

### ③ O que fazer

> [!decisão] Replanejamento de 31/10
> A escolha entre `balanced` e `None` precisa vir **antes** de escolher o método de calibração (#79), porque o peso muda a escala das probabilidades. Para não criar um ciclo, a comparação usa sempre `sigmoid`.

**Dono:** Pessoa C · **Prazo:** 01/11 (domingo), 12h30 às 13h30 · **Esforço estimado:** ≈ 1 h (mais ≈ 10 min de máquina) · **Começa quando:** #1 (finalista no YAML) e #148 (C_15 pronto)

#### O que é
Com `class_weight="balanced"`, cada óbito vale ≈ 11 casos no treino (prevalência de 8,4%). O professor confirmou que isso **não impede** o modelo de identificar perfis. O efeito colateral é inflar as probabilidades: no piloto definitivo, a logística previa em média ≈ 34% de risco quando morriam 8,4%, e o Brier (0,165) ficou pior que o de um modelo que dá 8,4% para todos (0,077). A calibração corrige a escala, e a decisão é se treinar sem peso entrega o mesmo ou melhor.

#### Passo a passo
1. `git pull`; confira `selecao_modelos.finalista_escolhido` e os hiperparâmetros preenchidos (#1).
2. Execute o C_15 (célula de peso de classe, `COMPARACAO_CW_METODO = "sigmoid"`) só para o finalista: treina `balanced` e `None` com os mesmos hiperparâmetros, calibra em `val_cal` e mede em `val_meas`: PR-AUC, ROC-AUC, **Brier depois da calibração** e ECE. Saída: `outputs/final/peso_classe_val_meas.csv`.
3. **Regra:** mantenha `balanced` só se a PR-AUC subir pelo menos 0,005 **e** o Brier calibrado não piorar (diferença ≤ 0,0005 conta como "não piorou"). Senão, `None`.
4. Grave a escolha em `class_weight` das duas famílias no YAML (logística e boosting, para a tabela comparativa ficar coerente) e uma linha no card para o `decisoes.md`.
5. Se a escolha foi `None` (diferente do que o #1 usou), **refaça** o ajuste do vencedor com `class_weight=None` (uma única configuração: os hiperparâmetros já escolhidos) e atualize `run_id_finalista` no YAML.
6. Comente a decisão e o `run_id_finalista` no #79.

#### Pronto quando
O YAML refletir a escolha e houver a tabela com as duas versões.

### ④ Pronto quando

- existe: `outputs/final/peso_classe_val_meas.csv` | A tabela com as duas versões do vencedor (com e sem peso), calibradas em val_cal e medidas em val_meas (PR-AUC, ROC-AUC, Brier calibrado, ECE), está em outputs/final/peso_classe_val_meas.csv.
- yaml: `configs/supervised.yaml` :: `models.logistic.busca_class_weight` existe | A busca da logística varia o peso de classe (balanced e None).
- manual: | A escolha (balanced só se a PR-AUC subir pelo menos 0,005 e o Brier calibrado não piorar; senão None) foi gravada no class_weight das duas famílias do YAML e comentada neste card para o docs/decisoes.md.

## #78 · Aprovar o G6 para liberar o ajuste fino (busca de hiperparâmetros)

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M3
- data ideal: 01/11
- responsável: Pessoa A (0,25 h) + Pessoa C (0,25 h)
- pessoas: A, C
- fonte: configs/supervised.yaml (gates.G6_finalistas_tuning); notebooks C_13
- depende de: #132, #140, #54
- tags: Gate, Modelagem
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 0.5
- novo: não
- professores: não
- removido: absorvido pelo #1 em 03/11 (o G6 libera a busca que o #1 executa)

### ① Para entender

O **G6** libera o *fine tuning*: testar combinações de "botões" dos dois finalistas (logística e boosting). Sem ele, o C_13 só treina com os valores padrão.

Antes de abrir, três coisas precisam estar certas: o boosting do `src` tem de ser o mesmo do piloto (item 4), o peso das classes precisa entrar na busca (item 5) e a busca tem de caber no tempo (item 3).

<div class="kpi">
<div><b>0,4675</b>PR-AUC do boosting com valores padrão (C_13)</div>
<div><b>0,4406</b>PR-AUC da logística C=1</div>
<div><b>0</b>configurações testadas até agora</div>
</div>

> [!exemplo] Exemplo
> Ajustar o forno antes de saber se é o mesmo forno do teste: se o boosting do `src` é diferente do piloto, o ajuste fino otimiza outro modelo.

### ② Problema

> [!atenção] Replanejamento de 31/10 · versão 2 (entrega em 04/11)
> Domingo, 9h15. O G6 passa a vir **logo depois do ponto de decisão (#140)** e a **grade de busca é colada no YAML aqui**, antes de aprovar (na versão anterior ela era colada no #1, depois do G6, o que formava um ciclo). O que sai do ajuste (finalista e hiperparâmetros) é critério do #1, não do G6.

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que esta pendência está aberta
> A auditoria automática do painel (27/10, 14:40) marcou este item como resolvido com base em commits de 09 e 11/10, todos anteriores às revisões de 24 e 26/10 e sem relação com a entrega descrita aqui. Isso acontece por um defeito do painel: a cada auditoria, um commit antigo ainda não rejeitado reabre a sugestão (detalhes no #94).
> `gates.G6_finalistas_tuning.status: pendente`; nenhum pré-requisito do checklist (#131, #135, #132, #140, #1, #5) está concluído.

O gate `G6_finalistas_tuning` está `pendente`. Sem ele, o C_13 não faz a busca de hiperparâmetros. Antes de aprovar, o boosting precisa reproduzir o piloto, o uso de `class_weight` precisa estar incluído na busca e o tempo da busca precisa caber no prazo; caso contrário, o ajuste fino é feito sobre um modelo diferente da lista curta.

**Atualização 17/10:** o C_13 rodou e registrou "G6 pendente: busca não executada". O boosting do `src` continua com one-hot denso e sem categóricas nativas (item 4).

### ③ O que fazer

> [!decisão] Replanejamento de 31/10 · versão 2
> O G6 autoriza a **busca**, com a grade e o orçamento já escritos no YAML. Quem fecha a escolha do finalista é o #1.

**Dono:** Pessoa A (cola a grade e registra) + Pessoa C (confere e aprova) · **Prazo:** 01/11 (domingo), 9h15 às 9h30 · **Esforço estimado:** A ≈ 15 min · C ≈ 15 min · **Começa quando:** #140, #132 e #54

#### Checklist (a Pessoa C confere; ≈ 5 min)
1. **#144 concluído:** suíte rápida verde e G1, G2, G4 e G5 `aprovado` no YAML.
2. **#132 concluído:** C_11 a C_13 rodaram em `train_ref` → `val_tune` (sem busca). Anote no card o tempo de **um** ajuste do boosting com os valores padrão: se passar de 6 minutos, a busca usa 250 mil linhas, e não 400 mil (#1, passo 2).
3. **#140 concluído** e `features.final` no YAML é a lista definitiva (31 variáveis, ou 28 se os três sintomas saíram).
4. **#54 salvo** (`outputs/final/ablacoes_val_tune.csv`) e `bootstrap_grupo` (#127) no `src`.

#### Ação (Pessoa A, ≈ 10 min)
5. Em `configs/supervised.yaml`, apague **tudo da linha `models:` até a linha em branco imediatamente anterior a `calibracao:`** (são os blocos `models:` e `tuning:`) e cole no lugar o bloco abaixo. Antes dele ficam as linhas finais de `missingness:` (`    pipeline_principal: false` · `    sensibilidade: false # desativada em 28/10: ...` · linha em branco); depois dele vem a linha em branco e `calibracao:` · `  ativa: true` · `  metodo: null` · `  metodos_candidatos:`. O que mudou em relação ao arquivo de 30/10: `busca_C` só com 0,01, 0,1 e 1,0; `busca_*` do boosting com 2 × 1 × 1 × 2 × 2 × 1 × 1 = **8 configurações**; `busca_class_weight` só com `balanced`; `max_configuracoes_por_modelo: 8`. Todo o resto (`decision_tree`, `random_forest`, `early_stopping: true`) permanece igual.

```yaml
models:
  baseline:
    strategy: prior
  logistic:
    C: null
    busca_C:
    - 0.01
    - 0.1
    - 1.0
    penalty: l2
    solver: lbfgs
    max_iter: 1000
    class_weight: balanced
    busca_class_weight:
    - balanced
  decision_tree:
    ativa: false
    max_depth:
    - 3
    - 5
    - 8
    - null
    min_samples_leaf:
    - 20
    - 50
    - 100
    class_weight: balanced
  random_forest:
    ativa: false
    n_estimators: 300
    max_depth:
    - 6
    - 10
    - null
    min_samples_leaf:
    - 10
    - 20
    - 50
    max_features:
    - sqrt
    - log2
    class_weight: balanced
    n_jobs: -1
  boosting:
    learning_rate: null
    busca_learning_rate:
    - 0.05
    - 0.1
    max_iter: null
    busca_max_iter:
    - 500
    max_depth: null
    busca_max_depth:
    - null
    busca_max_leaf_nodes:
    - 31
    - 63
    busca_min_samples_leaf:
    - 50
    - 200
    busca_l2_regularization:
    - 0.0
    max_leaf_nodes: 31
    min_samples_leaf: 20
    l2_regularization: 0.0
    early_stopping: true
    class_weight: balanced
    busca_class_weight:
    - balanced

tuning:
  metrica_principal: pr_auc
  concentrar_nos_dois_melhores: true
  usar_apenas_treino_validacao: true
  teste_proibido_durante_tuning: true
  max_configuracoes_por_modelo: 8
```
6. Confira com um comando: `.\.venv\Scripts\python.exe -c "import yaml; y=yaml.safe_load(open('configs/supervised.yaml',encoding='utf-8')); print(y['tuning']['max_configuracoes_por_modelo'], y['models']['logistic']['busca_C'], y['models']['boosting']['busca_max_leaf_nodes'], y['calibracao']['ativa'])"` (esperado: `8 [0.01, 0.1, 1.0] [31, 63] True`).
7. Em `gates.G6_finalistas_tuning`: `status: aprovado`, `aprovado_por: time_do_projeto`, `data: '2026-11-01'`.
8. Registre em `docs/decisoes.md` (§29.29): grade, orçamento (8 configurações de boosting, 3 de logística, 400 mil linhas) e critério de escolha (PR-AUC em `val_tune`; o boosting só vence com 0,005 de diferença). Commit: `feat: grade de busca e G6 aprovado [done:#78]`. Avise a Pessoa C: o #1 pode começar.

### ④ Pronto quando

- yaml: `configs/supervised.yaml` :: `gates.G6_finalistas_tuning.status` = `aprovado` | O gate G6 está aprovado no supervised.yaml, com data.
- yaml: `configs/supervised.yaml` :: `tuning.max_configuracoes_por_modelo` = `8` | O orçamento da busca (8 configurações por modelo) está no YAML.
- yaml: `configs/supervised.yaml` :: `features.final` existe | A lista final de variáveis está no YAML.
- manual: | O checklist do G6 neste card está conferido (#144, #132, #140, #54, #127) e a aprovação foi registrada no docs/decisoes.md.

## #9 · Saturação, desconforto respiratório e vacina: cada documento diz uma coisa

- prioridade: P2
- situação: parcial
- estratégia: documentar
- marco: M1
- data ideal: 01/11
- responsável: Pessoa A (dona; revisão cruzada sem edição concorrente)
- pessoas: A
- fonte: docs/decisoes.md §13 e §17; Plano_Unificado_SRAG_3_Pessoas_v2.docx; configs/supervised.yaml (features)
- depende de: #73
- tags: Diverge do decidido, Decisão, Features, Vazamento, Documentação
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 0
- novo: não
- professores: não

### ① Para entender

> [!decisão] Decisão de 18/10
> Uma rodada de sensibilidade com saturação e desconforto no cenário vencedor; fora do modelo principal.

Essas variáveis são das mais ligadas ao óbito, mas há dúvida se são conhecidas **na chegada** ao hospital ou anotadas depois. Se forem posteriores, usá-las é "colar na prova" (vazamento).

<div class="bars">
<div class="br"><span class="y">Saturação < 95%</span><div class="t"><div class="b red" style="width:89.0%"></div></div><span class="v">26,7% de óbito</span></div>
<div class="br"><span class="y">Saturação normal</span><div class="t"><div class="b " style="width:40.7%"></div></div><span class="v">12,2%</span></div>
<div class="br"><span class="y">Com desconforto</span><div class="t"><div class="b red" style="width:81.0%"></div></div><span class="v">24,3%</span></div>
<div class="br"><span class="y">Sem desconforto</span><div class="t"><div class="b " style="width:53.7%"></div></div><span class="v">16,1%</span></div>
</div>

| Documento | Saturação | Desconforto | Vacina |
|---|---|---|---|
| decisoes.md | Modelo A (principal) | Modelo B | candidata clínica |
| Plano v2 | sensibilidade | sensibilidade | no modelo |
| supervised.yaml | sensibilidade | sensibilidade | contexto incremental |

É uma das perguntas Top da orientação.

### ② Problema

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que esta pendência está aberta
> A auditoria automática do painel (27/10, 14:40) marcou este item como resolvido com base em commits de 09 e 11/10, todos anteriores às revisões de 24 e 26/10 e sem relação com a entrega descrita aqui. Isso acontece por um defeito do painel: a cada auditoria, um commit antigo ainda não rejeitado reabre a sugestão (detalhes no #94).
> `docs/decisoes.md` continua com as seções "Modelo A: núcleo clínico de admissão" e "Modelo B" (§11) e §13 sobre saturação; "Última atualização: 21/10". Nada mudou. É feito dentro do #73.

Os três documentos tratam `saturacao`, `desc_resp` e `vacina` de formas diferentes. As decisões colocam saturação no Modelo A, desconforto no Modelo B e vacinação entre as candidatas clínicas. O plano v2 coloca as duas variáveis de gravidade em sensibilidade e a vacinação no modelo. O YAML coloca saturação e desconforto em `sensibilidade_gravidade_admissao` e a vacinação em `contexto_incremental`.

### ③ O que fazer

> [!decisão] Atualizado em 03/11
> A decisão mudou: saturação e desconforto respiratório entraram no modelo principal (#140, §29.34). Os critérios do ④ foram atualizados para o estado novo; o card continua concluído.

> [!decisão] Enxugado em 27/10 (eficiência primeiro)
> Feito dentro do **#73** (Pessoa A). Marque como concluído junto com ele.

### ④ Pronto quando

- yaml: `configs/supervised.yaml` :: `features.final` contem `saturacao` | Atualizado em 03/11 (#140): saturação e desconforto respiratório estão no modelo principal, e os documentos dizem o mesmo (§13 e §29.34).
- yaml: `configs/supervised.yaml` :: `sensibilidades.sem_saturacao_desc_resp.ativa` = `false` | A sensibilidade sem as duas variáveis foi desativada.
- nao-contem: `docs/decisoes.md` :: `Modelo A: núcleo clínico de admissão` | O docs/decisoes.md deixou de colocar saturação no "Modelo A" e passou a dizer o mesmo que o YAML.

## #13 · A sazonalidade é criada, mas não entra no modelo

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 05/11
- responsável: Pessoa C (ablação) + Pessoa A (texto)
- pessoas: C, A
- fonte: src/features/engineering.py (sazonalidade); configs/supervised.yaml (features); docs/decisoes.md §7
- depende de: —
- tags: Diverge do decidido, Código, Features, Documentação
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: —
- novo: não
- professores: não
- removido: removido na revisão de 03/11 (v3.3): a sazonalidade fica fora do modelo; a frase de limitação está no #133 e o parágrafo da §7 que promete uma ablação de sazonalidade (não feita) é corrigido no #73

### ① Para entender

> [!decisão] Decisão de 18/10
> Não incluir a sazonalidade agora (mais dimensões, ganho incerto); documentar como limitação.

`sin_semana` e `cos_semana` transformam a semana do ano num círculo, para o modelo entender que a semana 52 é vizinha da semana 1. Elas são criadas, mas não estão na lista de features. Além disso, `decisoes.md` cita nomes que não existem no código.

> [!exemplo] Exemplo
> Sem o círculo, a semana 52 e a semana 1 parecem estar a 51 semanas de distância, quando estão a uma.

### ② Problema

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Pós-entrega. A justificativa para o relatório (a sazonalidade é criada, mas não entra no modelo principal) é uma frase do #133; o nome inexistente `semana_sen` no `decisoes.md` é corrigido no #73.

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que esta pendência está aberta
> A auditoria automática do painel (27/10, 14:40) marcou este item como resolvido com base em commits de 09 e 11/10, todos anteriores às revisões de 24 e 26/10 e sem relação com a entrega descrita aqui. Isso acontece por um defeito do painel: a cada auditoria, um commit antigo ainda não rejeitado reabre a sugestão (detalhes no #94).
> Inconsistência do próprio painel corrigida agora: este card dizia "feito dentro do #54", mas o #54 enxugado de 27/10 tirou a linha de sazonalidade. A ablação de sazonalidade passa a ser pós-entrega.

`sin_semana` e `cos_semana` são criadas por `montar_features`, mas não aparecem em `features.numericas`; portanto, a sazonalidade não entra no modelo. As decisões citam nomes que não existem no código: `semana_sen`, `semana_cos` e `flag_intervalo_negativo_inesperado`.

### ③ O que fazer

> [!decisão] Pós-entrega (correção de 28/10)
> A ablação de sazonalidade saiu do #54 no enxugamento de 27/10. A sazonalidade continua fora do modelo principal (G1). A correção dos nomes antigos na §7 do `decisoes.md` continua no #73.

### ④ Pronto quando

- manual: | (Pós-entrega) A ablação de sazonalidade foi feita ou registrada como trabalho futuro, e os nomes antigos (semana_sen, semana_cos, flag_intervalo_negativo_inesperado) foram corrigidos na §7 do docs/decisoes.md.
- nao-contem: `docs/decisoes.md` :: `semana_sen` | O docs/decisoes.md não cita mais o nome inexistente semana_sen (o código usa sin_semana).

## #54 · Ablações em val_tune: três sintomas de 2019, comorbidades recodificadas, gravidade, contexto e região

- prioridade: P1
- situação: aberta
- estratégia: explorar
- marco: M2
- data ideal: 31/10
- responsável: Pessoa A (1,5 h)
- pessoas: A
- fonte: configs/supervised.yaml (sensibilidades); Projeto
- depende de: #127, #141, #142
- tags: Metodologia, Modelagem
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1.5
- novo: não
- professores: não
- arquivos: notebooks/C/C_14_ablacoes_variaveis.ipynb, configs/supervised.yaml
- removido: absorvido pelo #140 em 03/11 (as ablações rodam no C_14 reexecutado pelo #132 e são decididas no #140)

### ① Para entender

> [!decisão] Decisão de 18/10
> Uma rodada de sensibilidade com saturação e desconforto no cenário vencedor; fora do modelo principal.

São versões alternativas do modelo para medir o efeito de decisões polêmicas:

- **Gravidade na admissão:** com saturação e desconforto respiratório.
- **Contexto incremental:** com UF, vacinação e escolaridade.
- **Qualquer óbito:** alvo inclui óbito por outras causas (evolução 3).

> [!ok] Situação atual
> As colunas já estão no artefato desde 16/10 (item 7). Agora só depende da decisão do item 9.

### ② Problema

> [!atenção] Replanejamento de 31/10 · versão 2 (entrega em 04/11)
> Passa da Pessoa C para a **Pessoa A** e deixa de depender do #132: as ablações vivem num **notebook próprio** (`C_14_ablacoes_variaveis`, o número que faltava na série C), assim a Pessoa C trabalha em paralelo na cadeia de modelagem sem conflito de edição. É a última peça de exploração antes do ponto de decisão (#140). Decisão de projeto: as linhas de **comorbidades recodificadas** rodam **nas duas famílias** (o critério do #140 usa o boosting). Código completo e testado em dados inventados.

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que esta pendência está aberta
> A auditoria automática do painel (27/10, 14:40) marcou este item como resolvido com base em commits de 09 e 11/10, todos anteriores às revisões de 24 e 26/10 e sem relação com a entrega descrita aqui. Isso acontece por um defeito do painel: a cada auditoria, um commit antigo ainda não rejeitado reabre a sugestão (detalhes no #94).
> Não existe `outputs/final/ablacoes_val_tune.csv`; depende do #131/#142, que não começaram.
> Ao rodar, desligar no YAML `target.sensibilidade_qualquer_obito.ativa` e `sensibilidades.alvo_qualquer_obito` (cortados em 27/10) ou registrar que não serão rodados.

Faltam as sensibilidades de gravidade na admissão (com `saturacao` e `desc_resp`), de contexto incremental e de alvo "qualquer óbito". Dependem do item 7, porque as colunas não estão no artefato.

### ③ O que fazer

> [!decisão] Replanejamento de 31/10 · versão 2
> A tabela responde **três perguntas objetivas** do #140 e nada além: (1) os três sintomas de 2019 saem? (2) recodificar comorbidades muda o resultado? (3) gravidade, contexto ou região acrescentam algo que mereça mudar o plano? Qualquer outra leitura vai para o relatório.

**Dono:** Pessoa A · **Prazo:** 31/10 (sábado), 18h30 às 20h · **Esforço estimado:** ≈ 1 h 30 (≈ 15 min de máquina) · **Começa quando:** #127 (bootstrap por grupo)

| Linha | Conjunto | Famílias |
|---|---|---|
| P | as 31 variáveis do G1 (`features.final`) | logística e boosting |
| P_menos_3_sintomas | sem `perd_olft`, `perd_pala`, `fadiga` | logística e boosting |
| P_comorbidades_recodificadas | P, com o branco da comorbidade virando "2" quando `fator_risc` = 2 (regra do #141, aplicada **na memória**) | logística e boosting |
| P_mais_gravidade | P + `saturacao`, `desc_resp` | logística |
| P_mais_contexto | P + `cs_escol_n`, `vacina` | logística |
| P_mais_regiao | P + `regiao_residencia` | logística |

#### Passo a passo
1. `git pull`. Crie `notebooks/C/C_14_ablacoes_variaveis.ipynb` (kernel `.venv`). Célula 1 (Markdown): título "Ablações de variáveis em val_tune" (sem código de notebook; o número entra na limpeza do #146), três linhas (o que faz, lê `train_ref` e `val_tune`, grava duas tabelas). Célula 2 (código): copie **a segunda célula do C_12** (localiza a raiz do projeto e importa `from src.utils import config as C`).
2. Célula 3 (código), leitura. Todas as 46 colunas (≈ 600 mil linhas, cabem na memória):

```python
from src.data.supervised_artifact import load_supervised_artifact

df, manifest = load_supervised_artifact(ROOT_DIR, expected_kind="final", partitions=("train_ref", "val_tune"))
print(df.shape, df[manifest["partition_column"]].value_counts().to_dict())
```
   Esperado: `train_ref` = 556.462 e `val_tune` = 39.748.
3. Célula 4 (código): **cole inteiro** o bloco abaixo (testado com dados inventados; só mudam as colunas reais). Ele define as funções e a lista de linhas da tabela:

```python
import time

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.pipeline import Pipeline

from src.evaluation.metrics import auc, average_precision, bootstrap_grupo, brier
from src.features.engineering import recodificar_comorbidades_por_fator_risco
from src.models.factory import build_finalista
from src.models.pipeline import build_preprocessor
from src.utils import config as C  # noqa: N812

TRES_SINTOMAS = ["perd_olft", "perd_pala", "fadiga"]
COMORBIDADES = ["cardiopati", "hematologi", "sind_down", "hepatica", "asma", "diabetes", "neurologic",
                "pneumopati", "imunodepre", "renal", "obesidade", "out_morbi", "puerpera"]


def pipeline_ablacao(familia, numericas, categoricas):
    """Pipeline com hiperparâmetros padrão para um conjunto de colunas escolhido."""
    if familia == "logistic":
        return build_finalista("logistic", preprocessor=build_preprocessor(numericas, categoricas))
    mascara = [False] * len(numericas) + [True] * len(categoricas)
    classificador = HistGradientBoostingClassifier(
        learning_rate=0.08, max_iter=150, max_leaf_nodes=31, min_samples_leaf=100, l2_regularization=0.10,
        early_stopping=True, validation_fraction=0.1, n_iter_no_change=20, class_weight="balanced",
        categorical_features=mascara, random_state=C.SEED,
    )
    return Pipeline([("pre", build_preprocessor(numericas, categoricas, saida="ordinal")), ("clf", classificador)])


def executar_ablacoes(df, manifest):
    """Treina em train_ref e mede em val_tune cada linha da tabela de ablações."""
    col_part, alvo = manifest["partition_column"], manifest["target_column"]
    num, cat = list(manifest["numeric_columns"]), list(manifest["categorical_columns"])
    treino, valid = df[col_part] == "train_ref", df[col_part] == "val_tune"
    y_tr, y_va = df.loc[treino, alvo].to_numpy(), df.loc[valid, alvo].to_numpy()
    prevalencia = float(y_va.mean())

    base = df[COMORBIDADES + ["fator_risc"]].astype("object")  # astype: evita erro de categoria nova ("2")
    recod = recodificar_comorbidades_por_fator_risco(base)
    df_recod = df.drop(columns=COMORBIDADES).join(recod[COMORBIDADES])

    sem3 = lambda cols: [c for c in cols if c not in TRES_SINTOMAS]  # noqa: E731
    linhas = {
        "P": (df, num, cat, ["logistic", "boosting"]),
        "P_menos_3_sintomas": (df, sem3(num), sem3(cat), ["logistic", "boosting"]),
        "P_comorbidades_recodificadas": (df_recod, num, cat, ["logistic", "boosting"]),
        "P_mais_gravidade": (df, num, cat + ["saturacao", "desc_resp"], ["logistic"]),
        "P_mais_contexto": (df, num, cat + ["cs_escol_n", "vacina"], ["logistic"]),
        "P_mais_regiao": (df, num, cat + ["regiao_residencia"], ["logistic"]),
    }
    resultados, probabilidades = [], {}
    for linha, (quadro, n_cols, c_cols, familias) in linhas.items():
        for familia in familias:
            t0 = time.perf_counter()
            pipe = pipeline_ablacao(familia, n_cols, c_cols)
            pipe.fit(quadro.loc[treino, n_cols + c_cols], y_tr)
            prob = pipe.predict_proba(quadro.loc[valid, n_cols + c_cols])[:, 1].astype("float32")
            probabilidades[(linha, familia)] = prob
            pr = average_precision(y_va, prob)
            resultados.append({"linha": linha, "familia": familia, "n_colunas": len(n_cols + c_cols),
                               "pr_auc": pr, "pr_auc_sobre_prevalencia": pr / prevalencia,
                               "roc_auc": auc(y_va, prob), "brier": brier(y_va, prob),
                               "duracao_s": round(time.perf_counter() - t0, 1)})
            del pipe
    tabela = pd.DataFrame(resultados)
    ref = tabela[tabela["linha"] == "P"].set_index("familia")
    tabela["dif_pr_auc_vs_P"] = tabela.apply(lambda r: r["pr_auc"] - ref.loc[r["familia"], "pr_auc"], axis=1)
    tabela["dif_roc_auc_vs_P"] = tabela.apply(lambda r: r["roc_auc"] - ref.loc[r["familia"], "roc_auc"], axis=1)

    anos = df.loc[valid, "ano_internacao"].to_numpy()
    grupos = df.loc[valid, "group_id"].to_numpy()
    por_ano = []
    for ano in sorted(set(anos)):
        m = anos == ano
        linha_ano = {"ano": int(ano), "n": int(m.sum()), "obitos": int(y_va[m].sum())}
        for familia in ("logistic", "boosting"):
            p_p, p_3 = probabilidades[("P", familia)][m], probabilidades[("P_menos_3_sintomas", familia)][m]
            linha_ano[f"roc_auc_P_{familia}"] = auc(y_va[m], p_p)
            linha_ano[f"roc_auc_menos3_{familia}"] = auc(y_va[m], p_3)
            ic = bootstrap_grupo(y_va[m], p_3, grupos[m], metrica="auc", prob_b=p_p, n=300)
            linha_ano[f"dif_menos3_menos_P_{familia}"] = ic["estimativa_diferenca"]
            linha_ano[f"ic_inf_{familia}"], linha_ano[f"ic_sup_{familia}"] = ic["ic_inferior"], ic["ic_superior"]
        por_ano.append(linha_ano)
    return tabela, pd.DataFrame(por_ano)
```
4. Célula 5 (código): `tabela, por_ano = executar_ablacoes(df, manifest)` (≈ 15 min de máquina). Depois `tabela.round(4)` e `por_ano.round(4)` na tela.
5. Célula 6 (código): grave `tabela.to_csv(ROOT_DIR / "outputs/final/ablacoes_val_tune.csv", index=False)` e `por_ano.to_csv(ROOT_DIR / "outputs/final/ablacoes_roc_por_ano.csv", index=False)`.
6. **Critério único do #50 (sem "tirar só por tirar").** Retire os três sintomas **somente se** a ROC-AUC de **2019** subir **pelo menos 0,01** sem eles **e** o IC 95% da diferença (`ic_inf_*`, `ic_sup_*` em `por_ano`, linha 2019) **não incluir zero**, **na logística e no boosting**. Caso contrário, mantenha e documente. Escreva a conclusão numa célula Markdown final ("Decisão proposta: manter/retirar, porque …").
7. **Critério para as comorbidades (#140):** recodificar só vale se a PR-AUC do **boosting** subir pelo menos 0,005 em relação à linha P. Escreva a proposta na mesma célula Markdown.
8. Em `configs/supervised.yaml`, deixe `sensibilidades.alvo_qualquer_obito.ativa: false` (cortado em 27/10: a coorte definitiva não tem evolução 3).
9. Execute o notebook com `.\.venv\Scripts\python.exe tools/medir_notebook.py notebooks/C/C_14_ablacoes_variaveis.ipynb` (meta: ≤ 6 GB, ≤ 20 min) e abra a cópia executada para conferir se não há erro. Na limpeza final (#146) ele já estará no padrão: sem referência a pendências nem a pessoas.
10. Comente **antes das 8h de domingo** no #140 as três linhas de resumo (o que encontrou, tamanho do efeito, se sugere mudança). Commit: `feat: ablacoes em val_tune [done:#54]`.

### ④ Pronto quando

- existe: `notebooks/C/C_14_ablacoes_variaveis.ipynb` | O notebook das ablações existe.
- notebook-executado: `notebooks/C/C_14_ablacoes_variaveis.ipynb` | O C_14 está salvo executado do início ao fim, sem saída de erro.
- existe: `outputs/final/ablacoes_val_tune.csv` | A tabela de ablações (P, P − 3 sintomas, P com comorbidades recodificadas, P + gravidade, P + contexto, P + região) com PR-AUC, PR-AUC ÷ prevalência, ROC-AUC, Brier e diferença para P está em outputs/final/ablacoes_val_tune.csv.
- existe: `outputs/final/ablacoes_roc_por_ano.csv` | A ROC-AUC por ano (P × P − 3 sintomas) com o IC pareado está em outputs/final/ablacoes_roc_por_ano.csv.
- yaml: `configs/supervised.yaml` :: `sensibilidades.alvo_qualquer_obito.ativa` = `false` | A sensibilidade "qualquer óbito", cortada em 27/10, está desligada no YAML.
- manual: | O resumo das ablações (três linhas) e a proposta para os três sintomas e para as comorbidades foram comentados no #140.

## #52 · Fichas de óbito têm as doenças prévias mais preenchidas

- prioridade: P3
- situação: aberta
- estratégia: explorar
- marco: M3
- data ideal: 31/10
- responsável: Pessoa B (0,5 h)
- pessoas: B
- fonte: Projeto (análise de desempenho)
- depende de: #141, #142, #23
- tags: Metodologia, Vazamento
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 0.5
- novo: não
- professores: não

### ① Para entender

> [!decisão] Decisão de 18/10
> Testado junto com o UMAP com e sem indicadores de ausência (item 109).

Nos óbitos, as comorbidades estão bem mais preenchidas (13 a 21 p.p. a menos de campos em branco). Talvez porque a ficha é revisada depois da morte. Se for isso, o modelo aprende "ficha completa = risco alto", que é uma pista do futuro.

> [!exemplo] Exemplo
> Dois pacientes iguais. Um tem alta e ninguém volta à ficha; o outro morre e a vigilância completa o histórico. Nos dados, o segundo "tem mais doenças".

No clustering, os grupos separavam fichas preenchidas de fichas em branco: silhouette 0,364 com esses indicadores e 0,233 sem eles.

### ② Problema

> [!atenção] Replanejamento de 31/10 · versão 2 (entrega em 04/11)
> Sábado à noite, antes do ponto de decisão (é exploração: vira insumo do #140). Meia hora.

As comorbidades estão mais preenchidas nos óbitos (diferença de 13 a 21 pontos percentuais). Pode ser viés de documentação: fichas de óbito são revisadas com mais cuidado. Nesse caso, o modelo aprende o preenchimento, não a condição clínica.

### ③ O que fazer

> [!decisão] Replanejamento de 31/10
> Uma tabela, um parágrafo. Não refazer com as previsões do teste.

**Dono:** Pessoa B · **Prazo:** 31/10 (sábado), 21h às 21h30 · **Esforço estimado:** ≈ 30 min · **Começa quando:** #142, #23 e #141 (já concluídos)

1. Leia `outputs/final/predicoes_val_tune_piloto.parquet` (#142) e junte, por `id_registro`, os 11 sintomas e as 12 comorbidades do artefato (`load_supervised_artifact(..., partitions=("val_tune",), columns=[...])`).
2. **Completude** = % desses 23 campos com resposta 1 ou 2 (sim ou não). Divida em terços com `pd.qcut(completude, 3, duplicates="drop")`.
3. `metricas_por_grupo(df, y, prob, "terco")` (de `src/evaluation/errors.py`). Salve `outputs/final/completude_val_tune.csv`.
4. Escreva o parágrafo de limitação para o relatório: se o desempenho sobe com a completude da ficha, o modelo pode estar lendo o preenchimento (viés de documentação) e não só a condição clínica. Cite que a hipótese de preenchimento por pulo da ficha (`fator_risc`, #141) explica parte da diferença.
5. Comente o resultado no #140 (três linhas) **antes das 8h de domingo**.

### ④ Pronto quando

- existe: `outputs/final/completude_val_tune.csv` | As métricas por terço de completude da ficha (23 campos) no val_tune estão em outputs/final/completude_val_tune.csv.
- manual: | O resultado foi comentado no #140 e o parágrafo de limitação está no relatório.

## #109 · UMAP em sintomas e comorbidades: clustering no espaço latente e uma ablação supervisionada

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 05/11
- responsável: Pessoa B (dona; revisão cruzada sem edição concorrente)
- pessoas: B
- fonte: B_06 (clustering); E_03; orientação de 17/10
- depende de: —
- tags: Não supervisionado, Features
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: —
- novo: sim
- professores: não
- removido: removido na revisão de 03/11 (v3.3): sugestão de um professor, não obrigatória; o agrupamento usa PCA; UMAP vira trabalho futuro no #133 e tem resposta pronta no #134

### ① Para entender

> [!decisão] UMAP não entra no caminho crítico do modelo final
> O uso principal será exploratório no espaço clínico e no clustering. A ablação supervisionada é opcional e só começa depois de o experimento temporal, a importância das variáveis e G0 × G1 estarem concluídos.

O professor apontou que o problema é o número de dimensões (31 variáveis viram 126 colunas) e sugeriu compactar com UMAP. Vamos usar em duas frentes, com prazo fixo de 1,5 dia.

| Uso | Pergunta | Entrega |
|---|---|---|
| Clustering (B_06/E_03) | Os grupos deixam de ser "ficha preenchida × em branco"? | silhouette e ARI: PCA × UMAP |
| Supervisionado (E_03) | 10 componentes UMAP no lugar de sintomas e comorbidades ajudam a logística? | R0 originais × R1 UMAP × R2 ambos, 3 seeds |

> [!atenção] Atenção
> UMAP ajustado só em amostra do treino (150 mil) e aplicado à validação com `transform`. Instalar `umap-learn` em 19/10: ele depende do `numba`, que pode não suportar Python 3.14. Plano B: ambiente 3.12 só para o UMAP, ou `TruncatedSVD`.

> [!exemplo] Exemplo
> Em vez de comparar pacientes por 126 perguntas sim/não, o UMAP resume cada um em 10 coordenadas que mantêm perto quem é parecido.

### ② Problema

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que esta pendência está aberta
> A auditoria automática (27/10, 14:40) marcou "precisa revisão" por achados que não tratam deste item: a linha decorativa `=====` no cabeçalho de `src/protocolo/verificacoes.py` (lida como conflito de merge) e o `OneHotEncoder` denso do B_06, que roda numa amostra de 80 mil fichas e será substituído pelo #136 (detalhes no #94).
> Continua pós-entrega.

Nenhuma redução além do PCA foi testada; `umap-learn` não está nas dependências.

### ③ O que fazer

Continua **pós-entrega**. A parte de não supervisionado pedida pelos professores é atendida pelo #136 (one-hot e normalização) e pelo #137 (testes estatísticos). UMAP só se um professor pedir explicitamente: nesse caso, uma figura 2D numa amostra de 50 mil do `train_ref`, colorida pelos grupos do #136 (Pessoa B, 01/11, ≈ 2 h).

### ④ Pronto quando

- manual: | (Pós-entrega) UMAP só se um professor pedir: figura 2D numa amostra de 50 mil do train_ref colorida pelos grupos do #136; caso contrário, registrar que ficou como trabalho futuro.

## #2 · G9 e abertura única do teste: checklist, execução do C_16 e conferência das saídas

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M6
- data ideal: 05/11
- responsável: Pessoa A (0,5 h) + Pessoa C (1 h) + Equipe
- pessoas: A, C, Equipe
- fonte: §22 do decisoes.md; revisão de 03/11 (absorve #81 e #119); ajuste 3.1 (teste em 05/11)
- depende de: #79, #148, #155, #126, #161, #163
- tags: Gate, Teste, Entrega
- pilar: Valor científico-acadêmico
- carga: 1.5
- novo: não
- professores: não
- arquivos: notebooks/C/C_16_validacao_final.ipynb, configs/supervised.yaml

### ① Para entender

O teste é aberto **uma única vez**, depois de tudo congelado. Um resultado ruim no teste vira limitação documentada, nunca ajuste. Este card juntou o checklist do G9 (#81), a execução (#2) e a conferência das saídas (#119): acontecem na mesma noite e com as mesmas pessoas.

### ② Problema

Hoje o `G9_holdout` está `pendente`, com `executado_em: null` e `n_acessos: 0`. O C_16 exige G7, G8 e G9 aprovados e, ao terminar, grava `status: executado` (estado terminal: o teste não pode mais ser carregado). Se faltar qualquer congelamento, a abertura fica inválida para a banca.

O C_16 novo **se protege** antes de abrir o teste: confere o limiar do YAML contra o manifesto do C_15, as variáveis e o hash dos modelos. Se algo estiver fora do lugar, ele para sem abrir nada. Também grava as previsões **antes** de qualquer análise, para que uma falha posterior não obrigue a reabrir o teste.

### ③ O que fazer

**Dono:** Pessoa A (checklist) + Pessoa C (executa, na máquina oficial do #158) + Equipe (aprova) · **Prazo:** 05/11, 7h45 às 10h · **Começa quando:** #155 (modelo final congelado), #79 (C_15 final rodado), #126 (cadeia executada), #161 (hipóteses registradas) e #163 (clone limpo) · **Script previsto:** `checklist_g9.py` (só lê; começa por relatório; é o último script a ser entregue). Sem ele, use a tabela.

1. **Checklist (A, 15 min; um "ok" por linha no grupo):**

| Item | Onde conferir |
|---|---|
| Máquina oficial: a mesma que rodou o C_15 final (o `dataset_sha256` do artefato aparece no manifesto `C5_*`) | #158 |
| G6, G7 e G8 aprovados; `features.final` com 30 variáveis | `configs/supervised.yaml` |
| `finalista_escolhido`, `calibracao.metodo` e `limiar.otimo` preenchidos; `class_weight` conferido pelo comando do #155 | `configs/supervised.yaml` |
| C_15 executado **depois** do último ajuste do YAML dos modelos (o C_16 confere por hash) | `outputs/tables/C5_*_manifesto.json` |
| Ensaio do C_16 feito com dados reais | comentário do #148 |
| Hipóteses do teste registradas em commit anterior (§29.38) | `docs/decisoes.md` e `git log` |
| `avaliacao.grupos` com `cs_raca` e `cs_zona` | `configs/supervised.yaml` |
| Memória livre de pelo menos 14 GB | comando do #161 |
| `test_opened: false`, `partition_counts` do 70/15/15 e árvore limpa no `origin/main` | manifesto e `git status` |

2. **Aprovar (Equipe):** no bloco `G9_holdout`: `status: aprovado`, `aprovado_por: Equipe`, `data: "2026-11-05"`. Commit e push: `chore: G9 aprovado`.
3. **Executar uma vez (C):**
```powershell
.\.venv\Scripts\python.exe tools\medir_notebook.py notebooks\C\C_16_validacao_final.ipynb --salvar-no-lugar --limite-s 5400 --limite-mb 12288
```
4. **Se o notebook parar** (todas as travas abaixo disparam **antes** de abrir o teste, e nada foi visto):

| Mensagem | O que significa | O que fazer |
|---|---|---|
| "Nenhum manifesto C5 compatível" | o C_15 não rodou nesta máquina com este artefato | rodar o C_15 aqui e tentar de novo |
| "O limiar do manifesto do C5 … não é o do YAML" | o YAML mudou depois do C_15 | copiar o limiar do C_15 (todas as casas) ou rodar o C_15 de novo |
| "Os modelos do YAML mudaram depois do C5" | `models` ou `features` mudaram depois do C_15 | rodar o C_15 de novo |
| "O C5 foi rodado com outras variáveis" | idem | rodar o C_15 de novo |
| "Teste já aberto para este dataset_sha256" | já existe um manifesto C6 | **não reabrir**; ver o item 5 |
| erro de memória antes de existir `C6_*_predicoes_teste` | nada foi visto | liberar memória e rodar de novo |
| erro **depois** de gravar `C6_*_predicoes_teste` | o resultado já existe | **não reabrir**; ver o item 5 |

5. **Se falhar depois da gravação das previsões:** não rode o C_16 de novo. As análises seguintes (por ano, por grupo, falsos negativos) podem ser refeitas a partir do arquivo de previsões, sem ler o teste. O G9 e o `test_opened` precisam ser marcados: edite à mão `G9_holdout` (`status: executado`, `executado_em`, `n_acessos: 1`) e `test_opened: true` no manifesto do artefato, e registre tudo no `decisoes.md`.
6. **Conferir (A e C, 30 min):** a tabela de janelas tem Teste A, Teste B e 2020–2022 com n = 119.245, 3.035.074 e 2.915.829; prevalências perto de 8,4%, 26% e 26,4%; o finalista, o limiar e o método impressos são os do YAML; o YAML ficou com `G9_holdout.status: executado` e `n_acessos: 1`.
7. **Depois da abertura, não rode o A_03** (nem `gerar_artefato_supervisionado`): ele regrava o manifesto do artefato e apaga o registro `test_opened`. Rode o comando do #156 (caminhos locais) no C_16 salvo.
8. Complete a entrada `#### 29.38` do `decisoes.md` (criada em 04/11 com as hipóteses, #161) acrescentando o bloco `**G9: teste aberto uma vez (05/11)**` com data e hora UTC, commit, as três linhas da tabela de janelas e a comparação com as hipóteses. Commit: `feat: teste aberto uma vez no C_16 [done:#2]`.

### ④ Pronto quando

- yaml: `configs/supervised.yaml` :: `gates.G9_holdout.status` = `executado` | O C_16 marcou o G9 como executado: o teste foi aberto uma vez.
- yaml: `configs/supervised.yaml` :: `gates.G9_holdout.n_acessos` = `1` | O teste foi aberto exatamente uma vez.
- notebook-executado: `notebooks/C/C_16_validacao_final.ipynb` | O C_16 está salvo com todas as células executadas e sem erro.
- notebook-saida: `notebooks/C/C_16_validacao_final.ipynb` :: `test_pandemic` | As saídas salvas mostram a leitura do bloco 2020–2022.
- contem: `docs/decisoes.md` :: `G9: teste aberto uma vez` | O decisoes.md registra a abertura com data, commit e a tabela das três janelas.

## #77 · Aprovar o G1 com a seleção de features da coorte provisória congelada

- prioridade: P1
- situação: resolvida
- estratégia: resolvida
- marco: M6
- data ideal: Concluído
- responsável: Pessoa A (dona; revisão cruzada sem edição concorrente)
- pessoas: A
- fonte: configs/supervised.yaml (gates.G1_definicao_alvo_features; features.final)
- depende de: —
- tags: Gate, Decisão, Features
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 2
- novo: não
- professores: não

### ① Para entender

> [!ok] Decisão fechada em 18/10
> A coorte definitiva inicial será a seleção de features da coorte provisória. O treino principal usará exclusivamente 2019, 2023, 2024 e 2025. Haverá duas janelas de teste: (A) 2019, 2023, 2024 e 2025; (B) 2019 a 2025, incluindo 2020–2022. O ano de 2026 não participa do desenvolvimento nem dos testes principais e fica apenas como exploração opcional, depois de todo o restante concluído.

O **G1** é o portão que diz: "estas são as variáveis que o modelo vai usar, e este é o alvo". Hoje a lista final (`features.final`) está vazia, e o piloto usa as 31 variáveis provisórias.

Ele é o portão com mais dependências do projeto: sem ele o teste final (C_16) não roda e vários documentos não podem ser alinhados.

<div class="flow"><span class="">Coorte definitiva</span><i>→</i><span class="">Decisões de entrada (saturação, vacina, intervalo, duplicados)</span><i>→</i><span class="hl">Aprovar G1</span><i>→</i><span class="">features.final preenchida</span><i>→</i><span class="">C_16 pode rodar</span></div>

> [!exemplo] Exemplo
> É como fechar a lista de ingredientes antes de começar a receita definitiva. Enquanto ela muda, todo bolo assado é só teste.

### ② Problema

O gate `G1_definicao_alvo_features` está `pendente`. É ele que confirma o schema da coorte definitiva, o alvo e a lista final de features, incluindo onde ficam `saturacao`, `desc_resp`, `vacina` e `vacina_cov`. Enquanto não for aprovado, `features.final` continua `null`, o C_16 não roda e vários documentos não podem ser alinhados.

**Atualização 17/10:** três recortes de período convivem no projeto (item 85), e a orientação com os professores (item 95) vai responder dúvidas que entram aqui: saturação, pandemia e vacina.

### ③ O que fazer

> [!ok] Concluída: G1 aprovado em 22/10 (`configs/supervised.yaml`, commit `da41e2e`), com 31 features em `features.final`, contexto e gravidade separados e lista de proibidas.

**Únicas consequências a acompanhar:** documentos alinhados ao G1 (#9, #70) e lista conferida contra o schema do artefato v3 (#131). Reabrir só por falha material (`reabrir_somente_por` no YAML).

### ④ Pronto quando

- yaml: `configs/supervised.yaml` :: `gates.G1_definicao_alvo_features.status` = `aprovado` | O G1 está aprovado no supervised.yaml.
- yaml: `configs/supervised.yaml` :: `features.final` existe | A lista final de features (31 variáveis) está preenchida no YAML.
- teste: `tests/test_leakage.py::test_features_finais_sem_proibidas` | O teste confirma que nenhuma feature final está na lista de proibidas.

## #79 · C_15: peso de classe, calibração (G7) e limiar (G8) nas metades do val_ref

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M5
- data ideal: 03/11
- responsável: Pessoa B (1,25 h)
- pessoas: B
- fonte: §29.12, §29.21, §29.22 e §29.33; revisão de 03/11 (absorve #80, #5 e #58)
- depende de: #1, #158
- tags: Modelagem, Gate, Calibração
- pilar: Valor científico-acadêmico
- carga: 1.25
- novo: não
- professores: não
- arquivos: notebooks/C/C_15_calibracao_limiar.ipynb, configs/supervised.yaml

### ① Para entender

O C_15 transforma o finalista em probabilidades confiáveis (calibração) e escolhe o corte que vira alerta (limiar). Com o 70/15/15, ele divide o `val_ref` em duas metades estratificadas e disjuntas: `val_cal` ajusta o calibrador e `val_meas` mede o Brier, escolhe o método e escolhe o limiar. É o desenho registrado na §29.33, com a limitação declarada (a seleção do G6 também usou o `val_ref`).

Este card absorveu o G8 (#80), o peso de classe (#5) e o aviso de "a mesma validação escolhe e mede" (#58), que agora é a limitação documentada.

### ② Problema

> [!decisão] Estado em 03/11 (commit `d7d774c`)
> O script `corrigir_c15_c16.py` já aplicou no C_15: o finalista vem de `selecao_modelos.finalista_escolhido` (o notebook **para** de propósito se o campo estiver vazio), o `min_recall` entra na escolha do limiar, o manifesto grava o hash da configuração dos modelos (o C_16 recusa abrir o teste se o YAML dos modelos mudar depois) e o texto de 21,9% de óbitos (coorte provisória) foi corrigido. Não há mais edição de código neste card.

Falta o que depende de números: o YAML (G7 e G8 estão `pendente`, `finalista_escolhido` é `null` e `limiar.metrica` está vazio: com `min_recall: 0,8` o C_15 cairia em "F1 máximo com sensibilidade ≥ 0,8", e não na regra decidida) e a execução.

O C_15 treina **os dois** finalistas e compara o peso de classe nos dois, então leva alguns minutos (cada ajuste leva de 8 a 16 s).

> [!atenção] `class_weight: null` não funciona no YAML
> A fábrica descarta valores `null`: o modelo usa o padrão `balanced`. A comparação de peso de classe do C_15 passa `None` direto ao construtor, então ela mostra o efeito real, mas **o YAML precisa de `class_weight: {}`** para o C_15 e o C_16 treinarem sem peso.

### ③ O que fazer

> [!ok] Passo 2 já aplicado por script em 03/11 (commit `b3772de`)
> `limiar.metrica` passou de `null` para `precision` (`min_recall: 0.8` já estava). Os demais passos continuam abertos.

**Dono:** Pessoa B · **Prazo:** 03/11, 14h às 15h15, na **máquina oficial** (#158) · **Começa quando:** #1 (finalista e hiperparâmetros no YAML)

1. **Confira o YAML do #1:** `selecao_modelos.finalista_escolhido` preenchido e, se o peso de classe do finalista for "sem peso", `class_weight: {}` (e não `null`). Confirme com o comando:
```powershell
.\.venv\Scripts\python.exe -c "from src.models.factory import build_finalista as b;print(b('logistic').steps[-1][1].class_weight, b('boosting').steps[-1][1].class_weight)"
```
2. **YAML (G8 decidido antes dos números, §29.22):** em `limiar`: `metrica: precision` e `min_recall: 0.8` (já está); `min_precision: null`.
3. **Execute:**
```powershell
.\.venv\Scripts\python.exe tools\medir_notebook.py notebooks\C\C_15_calibracao_limiar.ipynb --salvar-no-lugar --limite-mb 12288
```
4. **Decida (regras registradas antes dos números):**
   - **Peso de classe:** na tabela de comparação, `balanced` só fica se a PR-AUC subir ≥ 0,005 **e** o Brier calibrado não piorar; senão, `class_weight: {}` no finalista. Se mudar, ajuste o YAML e **rode o C_15 de novo** (o calibrador depende do modelo).
   - **G7:** menor Brier em `val_meas`; diferença < 0,0005 → `sigmoid`. Grave `calibracao.metodo`.
   - **G8:** `limiar.otimo` = o corte do finalista na tabela do C_15, **com todas as casas decimais** (o C_16 compara com tolerância de 1e-6). Anote também a sensibilidade e a precisão nesse corte.
5. **YAML:** `G7_calibracao` e `G8_limiar` com `status: aprovado`, `aprovado_por: Pessoa B e Pessoa C`, `data: "2026-11-03"`.
6. **Registre** `#### 29.36 03/11 · G7 e G8: peso de classe, calibração e limiar` no `decisoes.md`: método, Brier antes e depois, modelo nulo (≈ 0,077), corte, sensibilidade e precisão em `val_meas` e a frase da limitação (a seleção do G6 e a escolha do limiar usam o mesmo `val_ref`; o teste dá a medida honesta).
7. Commit: `feat: G7 e G8 aprovados no val_ref [done:#79]`. Avise a equipe: esta é a execução de **referência**. A **final** (modelo do #155) roda em 04/11 às 16h.

### ④ Pronto quando

- yaml: `configs/supervised.yaml` :: `gates.G7_calibracao.status` = `aprovado` | O G7 está aprovado.
- yaml: `configs/supervised.yaml` :: `gates.G8_limiar.status` = `aprovado` | O G8 está aprovado.
- yaml: `configs/supervised.yaml` :: `calibracao.metodo` != `null` | O método de calibração está congelado.
- yaml: `configs/supervised.yaml` :: `limiar.otimo` != `null` | O limiar está congelado.
- yaml: `configs/supervised.yaml` :: `limiar.min_recall` = `0.8` | A regra do G8 (sensibilidade mínima de 0,80) está no YAML.
- contem: `notebooks/C/C_15_calibracao_limiar.ipynb` :: `min_recall=LIMIAR_MIN_RECALL` | O C_15 aplica a sensibilidade mínima na escolha do limiar.
- contem: `notebooks/C/C_15_calibracao_limiar.ipynb` :: `finalista_escolhido` | O C_15 usa o finalista do YAML, e não o de maior AUC.
- notebook-executado: `notebooks/C/C_15_calibracao_limiar.ipynb` | O C_15 foi reexecutado com o finalista congelado e salvo sem erro.
- contem: `docs/decisoes.md` :: `G7 e G8: peso de classe, calibração e limiar` | O decisoes.md registra as três decisões (entrada 29.36) com números e a limitação.
- yaml: `configs/supervised.yaml` :: `limiar.metrica` = `precision` | A métrica do limiar está definida como precisão, com a sensibilidade mínima de 0,80 (G8 decidido antes dos números).

## #80 · Aprovar o G8: escolher o limiar (proposta do C_15: 0,255 pelo F1)

- prioridade: P1
- situação: parcial
- estratégia: desenvolver
- marco: M4
- data ideal: 01/11
- responsável: Pessoa C (2 h)
- pessoas: C
- fonte: configs/supervised.yaml (gates.G8_limiar; limiar.metrica, limiar.otimo); notebooks C_15
- depende de: #79
- tags: Gate, Calibração
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 2
- novo: não
- professores: não
- removido: absorvido pelo #79 em 03/11 (o C_15 decide calibração e limiar na mesma execução)

### ① Para entender

O **limiar** transforma a probabilidade em alerta: acima dele, "alto risco". O C_15 escolheu 25,5% por F1 (equilíbrio entre pegar óbitos e evitar alarme falso).

| Corte | Óbitos que o alerta pega | Alertas que eram óbito |
|---|---|---|
| 1% | 99,6% | 25,5% |
| 5% | 98,5% | 28,8% |
| 10% | 95,8% | 31,2% |
| 15% | 91,6% | 33,6% |
| **25,5% (F1)** | — | F1 = 0,516 |

> [!atenção] Atenção
> Em saúde, deixar passar um óbito costuma ser pior que um alarme falso. Esse critério é uma das perguntas aos professores (item 95).

### ② Problema

> [!atenção] Replanejamento de 31/10 · versão 2 (entrega em 04/11)
> Domingo, 16h às 18h, **depois do #79**. Absorve os cortes por região do #110. Achado do código: `escolher_limiar` só aceita `f1`, `precision`, `recall`, `accuracy` e `youden_j`; o YAML lista `recall_minimo` e, com `limiar.metrica = recall_minimo`, o C_15 levanta `ValueError`. Esta tarefa implementa `recall_minimo` (código completo e testado). A tabela de cortes ganha a coluna `regra`, que o C_16 lê.

O gate `G8_limiar` está **pendente**, e `limiar.metrica` e `limiar.otimo` estão `null`. O C_15 propôs `limiar.metrica: f1` e `limiar.otimo: 0.255`, calculados sobre probabilidades calibradas de um modelo ainda sem ajuste fino. Não está decidido se o projeto usa um limiar único ou faixas de risco.

### ③ O que fazer

> [!decisão] Replanejamento de 31/10
> **Regra única** para o corte global e para os regionais: o de **maior precisão entre os que têm sensibilidade ≥ 0,80**. O professor disse que 80% de sensibilidade "já está bom" e 70% "já está muito bom". Os cortes de referência (70%, F1 máximo e Youden) só aparecem em tabela.

**Dono:** Pessoa C · **Prazo:** 01/11 (domingo), 16h às 18h · **Esforço estimado:** ≈ 2 h (global ≈ 1 h + regional ≈ 1 h) · **Começa quando:** #79

#### Passo a passo
1. **`recall_minimo` em `src/models/calibration.py` (blocos completos, testados).**
   **(a)** Substitua a linha `Metrica          = Literal["f1", "precision", "recall", "accuracy", "youden_j"]` por esta (uma linha só):

```python
Metrica          = Literal["f1", "precision", "recall", "accuracy", "youden_j", "recall_minimo"]
```

   **(b)** Substitua a função `escolher_limiar` **inteira**: da linha `def escolher_limiar(` até o **fim do arquivo** (é a última função; apague tudo dali para baixo). Antes dela ficam as quatro linhas finais de `calibrar` (`        method=method,` · `    )` · `    modelo.fit(X_cal, y_cal)` · `    return modelo`) e duas linhas em branco; depois dela não fica nada. Cole:

```python
def escolher_limiar(
    y_true: pd.Series | np.ndarray,
    y_prob: pd.Series | np.ndarray,
    *,
    metrica: Metrica = "f1",
    n_limiares: int = 101,
    min_precision: float | None = None,
    min_recall: float | None = None,
) -> dict[str, Any]:
    """Devolve o limiar ótimo segundo ``metrica`` e um resumo associado.

    Restrições opcionais de ``min_precision`` / ``min_recall`` filtram
    candidatos antes de maximizar ``metrica``; se nada sobrar, levanta
    ``ValueError``.

    ``metrica="recall_minimo"`` escolhe o corte de maior precisão entre os
    que têm ``recall >= min_recall`` (exige ``min_recall``).

    Retorna dict com ``limiar``, ``valor`` (da métrica escolhida),
    ``metrica``, ``auc``, ``brier`` e ``tabela`` (grade completa de
    ``metricas_por_limiar``).
    """
    if metrica not in _METRICAS_VALIDAS:
        raise ValueError(
            f"metrica inválida: {metrica!r}. Use {sorted(_METRICAS_VALIDAS)}."
        )

    y_true_arr = np.asarray(y_true).ravel().astype(int)
    y_prob_arr = np.asarray(y_prob).ravel()

    metrica_otimizada = metrica
    if metrica == "recall_minimo":
        if min_recall is None:
            raise ValueError("metrica='recall_minimo' exige min_recall.")
        metrica_otimizada = "precision"  # maior precisão entre os cortes com recall >= min_recall

    tabela = metricas_por_limiar(y_true_arr, y_prob_arr, n_limiares=n_limiares)

    candidatos = tabela
    filtros: list[str] = []
    if min_precision is not None:
        filtros.append(f"precision ≥ {min_precision}")
        candidatos = candidatos[candidatos["precision"] >= min_precision]
    if min_recall is not None:
        filtros.append(f"recall ≥ {min_recall}")
        candidatos = candidatos[candidatos["recall"] >= min_recall]
    if candidatos.empty:
        restricao = " e ".join(filtros) if filtros else "sem restrição"
        raise ValueError(f"Nenhum limiar atende à(s) restrição(ões): {restricao}.")

    if metrica_otimizada not in candidatos.columns:
        raise ValueError(
            f"A métrica {metrica_otimizada!r} não foi produzida por metricas_por_limiar. "
            f"Colunas disponíveis: {sorted(candidatos.columns)}"
        )

    idx_melhor   = candidatos[metrica_otimizada].idxmax()
    linha_melhor = tabela.loc[[idx_melhor]].iloc[0]

    return {
        "limiar":  float(linha_melhor["limiar"]),
        "valor":   float(linha_melhor[metrica_otimizada]),
        "metrica": metrica,
        "auc":     float(roc_auc_score(y_true_arr, y_prob_arr)),
        "brier":   float(brier_score_loss(y_true_arr, y_prob_arr)),
        "tabela":  tabela,
    }
```

   **(c)** Teste: acrescente ao **final** de `tests/test_calibration.py` (o arquivo termina sem quebra de linha: deixe duas linhas em branco antes do `def`):

```python
def test_escolher_limiar_recall_minimo():
    rng = np.random.default_rng(0)
    p = rng.beta(1, 8, 2000)
    y = (rng.random(2000) < p).astype(int)
    r = escolher_limiar(y, p, metrica="recall_minimo", min_recall=0.80, n_limiares=197)
    t = r["tabela"]
    elegiveis = t[t["recall"] >= 0.80]
    assert float(t.loc[t["limiar"] == r["limiar"], "recall"].iloc[0]) >= 0.80
    assert r["valor"] == float(elegiveis["precision"].max())
    with pytest.raises(ValueError):
        escolher_limiar(y, p, metrica="recall_minimo")
```
2. **Global:** em `val_cal`, com as probabilidades calibradas do #79, `escolher_limiar(y, p, metrica="recall_minimo", min_recall=0.80, n_limiares=197)`. A grade de cortes do `src` é `np.linspace(0.01, 0.99, n_limiares)`: com 197 pontos o passo é 0,005. Registre sensibilidade, precisão, especificidade, F1 e % de fichas com alerta.
3. **Referências (só tabela):** corte com sensibilidade ≥ 0,70, F1 máximo e Youden.
4. **Tabela de cortes** de 0,05 a 0,60 (passo 0,05) para o apêndice: chame `metricas_por_limiar(y, p, n_limiares=99)` (passo 0,01) e filtre os múltiplos de 0,05 com `np.isclose`. Junte o corte principal e as referências e grave em `outputs/final/limiares_val_cal.csv` **com a coluna `regra`** (valores fixos: `principal_sens_ge_0.80`, `ref_sens_ge_0.70`, `ref_f1_max`, `ref_youden`, `grade`); o C_16 lê a linha `ref_sens_ge_0.70`.
5. **Medir sem alterar:** aplique os cortes a `val_meas` e anote sensibilidade e precisão (esperado: sensibilidade perto de 0,80; se ficar abaixo de 0,75, comente no card).
6. **Faixas de risco** (baixo, médio, alto) pelos tercis da probabilidade calibrada em `val_cal`, só como descrição, em `outputs/final/faixas_risco_val_cal.csv`.
7. **Por região (absorve o #110):** repita o passo 2 em cada `regiao_residencia` (Norte, Nordeste, Centro-Oeste, Sudeste, Sul). Região com menos de 100 óbitos em `val_cal` usa o **corte global** e é marcada (`usa_global = True`; os óbitos são ≈ 3.350 em `val_cal`, e as regiões pequenas ficam perto do limite). Grave `outputs/final/limiares_por_regiao.csv` (n, óbitos, corte, sensibilidade, precisão, `usa_global`) e, no YAML, `limiar.por_regiao` (mapa região → corte).
8. YAML (à mão): `limiar.metrica: recall_minimo`, `limiar.min_recall: 0.80`, `limiar.otimo`, `limiar.por_regiao`, `gates.G8_limiar.status: aprovado`, `aprovado_por: time_do_projeto`, `data: '2026-11-01'`. Registre no `decisoes.md` (§29.31).
9. Commit: `feat: limiar global e por regiao, G8 aprovado [done:#80]`.

#### Pronto quando
O YAML tiver os cortes e existirem `limiares_val_cal.csv` e `limiares_por_regiao.csv`.

### ④ Pronto quando

- yaml: `configs/supervised.yaml` :: `limiar.otimo` != `null` | O corte global escolhido está no YAML.
- yaml: `configs/supervised.yaml` :: `limiar.metrica` = `recall_minimo` | A regra do corte é a de maior precisão com sensibilidade ≥ 0,80 (recall_minimo).
- yaml: `configs/supervised.yaml` :: `limiar.por_regiao` existe | O YAML tem limiar.por_regiao com o corte de cada região.
- yaml: `configs/supervised.yaml` :: `gates.G8_limiar.status` = `aprovado` | O G8 está aprovado, com data.
- contem: `src/models/calibration.py` :: `recall_minimo` | O escolher_limiar aceita a regra recall_minimo.
- existe: `outputs/final/limiares_val_cal.csv` | A tabela de cortes (0,05 a 0,60 e os de referência) está em outputs/final/limiares_val_cal.csv.
- existe: `outputs/final/limiares_por_regiao.csv` | Os cortes por região, escolhidos em val_cal, estão em outputs/final/limiares_por_regiao.csv.

## #81 · Aprovar o G9 e liberar as duas janelas de teste uma única vez

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M5
- data ideal: 02/11
- responsável: Pessoa A (1 h) + Pessoa C (0,5 h) + Equipe (0 h)
- pessoas: A, C, Equipe
- fonte: configs/supervised.yaml (gates.G9_holdout); notebooks C_16
- depende de: #77, #79, #80, #135, #144, #148, #127
- tags: Gate, Vazamento
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1.5
- novo: não
- professores: não
- removido: absorvido pelo #2 em 03/11 (checklist do G9 na mesma noite da abertura)

### ① Para entender

> [!ok] Decisão fechada em 18/10
> A coorte definitiva inicial será a seleção de features da coorte provisória. O treino principal usará exclusivamente 2019, 2023, 2024 e 2025. Haverá duas janelas de teste: (A) 2019, 2023, 2024 e 2025; (B) 2019 a 2025, incluindo 2020–2022. O ano de 2026 não participa do desenvolvimento nem dos testes principais e fica apenas como exploração opcional, depois de todo o restante concluído.

O **teste** é a prova final: 587 mil internações que nenhum modelo viu. O **G9** autoriza abrir essa prova **uma única vez**, no C_16. Depois disso, nenhuma decisão de modelagem pode mudar.

<div class="flow"><span class="">G1 variáveis</span><i>→</i><span class="">G6 ajuste fino</span><i>→</i><span class="">G7 calibração</span><i>→</i><span class="">G8 limiar</span><i>→</i><span class="bad">G9 abrir o teste</span><i>→</i><span class="">Resultado final</span></div>

> [!exemplo] Exemplo
> É como abrir o envelope da nota final: se depois você muda a resposta, a nota deixa de valer.

### ② Problema

> [!decisão] Replanejamento de 01/11: G9 movido para segunda, 02/11, à noite
> Antes: domingo, 01/11, 20h. Agora: **segunda, 02/11, das 20h às 21h30** (data no YAML: `2026-11-02`; tag `congelado-2026-11-02`). O #2 passa para terça, 03/11, às 8h. Os pré-requisitos não mudaram (#77, #79, #80, #135, #144, #148 e #127).

> [!atenção] Replanejamento de 31/10 · versão 2 (entrega em 04/11)
> Segunda-feira (02/11, feriado), 20h às 21h (a Pessoa A confere, a Pessoa C revisa o C_16 em ensaio). Tag de congelamento: `congelado-2026-11-02`. O C_16 é revisado em ensaio (`SRAG_DRY_RUN=1`) **antes** de abrir o teste, porque depois ele não roda de novo.

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que esta pendência está aberta
> A auditoria automática do painel (27/10, 14:40) marcou este item como resolvido com base em commits de 09 e 11/10, todos anteriores às revisões de 24 e 26/10 e sem relação com a entrega descrita aqui. Isso acontece por um defeito do painel: a cada auditoria, um commit antigo ainda não rejeitado reabre a sugestão (detalhes no #94).
> `gates.G9_holdout.status: pendente`, `n_acessos: 0`. Nenhum pré-requisito concluído.

O gate `G9_holdout` está `pendente`. Ele libera o teste uma única vez e é irreversível: depois de `executado`, nenhuma decisão de modelagem pode mudar. Só pode ser aprovado com modelo, features, calibração e limiar congelados e com a proteção do teste funcionando.

### ③ O que fazer

> [!decisão] Replanejamento de 31/10
> O G9 libera o teste **uma única vez**. Depois dele, **nada** do modelo muda. É o envelope da nota final.

**Dono:** Pessoa A (conduz) + Pessoa C (modelagem e revisão do C_16) + Equipe (aprova) · **Prazo:** 02/11 (segunda, feriado), 20h às 21h30 · **Esforço estimado:** A ≈ 1 h · C ≈ 30 min · **Começa quando:** #77, #79, #80, #135, #144, #148 e #127

#### Estado do congelamento: um comando só
`.\.venv\Scripts\python.exe -c "import yaml,json; y=yaml.safe_load(open('configs/supervised.yaml',encoding='utf-8')); g=y['gates']; s=y['selecao_modelos']; print({k:g[k]['status'] for k in ('G1_definicao_alvo_features','G2_janela_temporal','G6_finalistas_tuning','G7_calibracao','G8_limiar','G9_holdout')}); print(s['finalista_escolhido'], s.get('run_id_finalista'), y['calibracao']['metodo'], y['limiar']['otimo'], y['limiar'].get('por_regiao')); print(json.load(open('data/analytical/manifesto_supervisionado.json'))['test_opened'])"`

Esperado: G1, G2, G6, G7 e G8 `aprovado`; G9 `pendente`; finalista, `run_id_finalista`, método, corte global e cortes por região preenchidos; `test_opened` = `False`.

#### Checklist (a Pessoa A confere item por item no repositório e marca aqui)
1. Coorte e artefato com SHA-256 no manifesto (#131); invariantes passando (#135).
2. G1, G2, G6, G7 e G8 aprovados no YAML, com data (o resultado do comando acima).
3. `finalista_escolhido`, `run_id_finalista`, `calibracao.metodo`, `limiar.otimo` e `limiar.por_regiao` preenchidos.
4. Medição em `val_meas` registrada (`outputs/final/calibracao_val_meas.csv`): é a última foto antes do teste.
5. `.\.venv\Scripts\python.exe -m pytest -m "not slow" -q` com 0 falhas (inclui o teste da proteção do teste).
6. **C_16 em ensaio:** `$env:SRAG_DRY_RUN="1"` e executado até o passo 11 (#148) **sem abrir o teste**; a Pessoa C revisou o diff. O manifesto continua com `test_opened: false`.
7. Leitura do teste em **lotes de 250 mil linhas** conferida no código do C_16 (#145) e memória livre da máquina de execução ≥ 8 GB.
8. `git status` limpo; commit de congelamento com a tag **`congelado-2026-11-02`** (`git tag congelado-2026-11-02`; `git push --tags`) e o SHA anotado aqui.

#### Aprovação
Cada pessoa comenta "aprovo o G9" (pode ser pelo celular). Com as três aprovações (ou duas e nenhuma objeção em 2 horas), a Pessoa C muda `G9_holdout.status: aprovado` (com `aprovado_por`, `data: '2026-11-02'`) e roda o #2 na manhã de 03/11.

### ④ Pronto quando

- yaml: `configs/supervised.yaml` :: `gates.G9_holdout.status` != `pendente` | O G9 foi aprovado (ou já executado) no supervised.yaml.
- yaml: `configs/supervised.yaml` :: `gates.G8_limiar.status` = `aprovado` | Pré-requisito: o G8 está aprovado.
- yaml: `configs/supervised.yaml` :: `gates.G7_calibracao.status` = `aprovado` | Pré-requisito: o G7 está aprovado.
- yaml: `configs/supervised.yaml` :: `gates.G6_finalistas_tuning.status` = `aprovado` | Pré-requisito: o G6 está aprovado.
- yaml: `configs/supervised.yaml` :: `gates.G1_definicao_alvo_features.status` = `aprovado` | Pré-requisito: o G1 está aprovado.
- yaml: `configs/supervised.yaml` :: `gates.G2_janela_temporal.status` = `aprovado` | Pré-requisito: o G2 está aprovado.
- manual: | O checklist do G9 está todo marcado neste card, o commit de congelamento tem a tag congelado-2026-11-02 com o SHA anotado, e as três pessoas comentaram "aprovo o G9" (ou duas, sem objeção em 2 horas).

## #37 · O B_10 vai falhar de propósito quando a lista final de variáveis existir

- prioridade: P4
- situação: resolvida
- estratégia: resolvida
- marco: Pós-entrega
- data ideal: Concluído
- responsável: Pessoa B (dona; revisão cruzada sem edição concorrente)
- pessoas: B
- fonte: B_10_consolidacao_shortlist_transicao_coorte
- depende de: —
- tags: Notebook
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 3
- novo: não
- professores: não

### ① Para entender

O B_10 tem a verificação `features_finais_ainda_nao_congeladas`, que exige `features.final` vazia. Ela foi feita para a fase provisória e precisa ser invertida na coorte definitiva.

### ② Problema

O B_10 tem uma verificação, `features_finais_ainda_nao_congeladas`, que exige `features.final` vazia. Quando a lista final for preenchida, a verificação falha de propósito e interrompe o notebook.

### ③ O que fazer

> [!ok] Resolvida (revisão de 24/10)
> A verificação que falhava de propósito foi removida do B_10 (commit 109e046). O B_10 é histórico; basta uma célula no topo "histórico; não executar" quando alguém mexer nele.

### ④ Pronto quando

- nao-contem: `notebooks/B/B_10_consolidacao_shortlist_transicao_coorte.ipynb` :: `features_finais_ainda_nao_congeladas` | A verificação que falhava de propósito foi removida do B_10 (se o B_10 sair no #143, o critério continua atendido).

## #126 · Execução limpa da cadeia final, README novo e pacote de reprodução

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M7
- data ideal: 04/11
- responsável: Pessoa C (1 h) + Pessoa B (1,5 h)
- pessoas: C, B
- fonte: README.md e 02_fluxo_e_estado §11.5 no commit 9f3322b; revisão de 03/11
- depende de: #155, #152, #153, #158, #159
- tags: Entrega, Reprodutibilidade, Documentação
- pilar: Eficiência + Documentação
- carga: 2.5
- novo: não
- professores: não
- arquivos: README.md, requirements.txt, pyproject.toml

### ① Para entender

A banca precisa conseguir entender a estrutura e, em tese, reproduzir os resultados. Isso exige três coisas: todos os notebooks salvos com saídas do mesmo artefato, um README que descreva o projeto como ele é hoje e as dependências declaradas.

### ② Problema

- **README desatualizado (linhas 69, 76, 180, 200 e 270):** descreve notebooks que não existem (`02_eda/_provisorio_construcao_coorte_b`, `C1_smoke_test` a `C6_validacao_final`), fala em "shortlist provisória" e traz uma seção "Pontos de atenção conhecidos" (linha 408), escrita por uma auditoria automática, cujo primeiro item (`csv_to_parquet`) já não se aplica.
- **O A_03 republica e regera por padrão:** `GERAR_CANDIDATA`, `PUBLICAR` e `GERAR_ARTEFATO` estão `True`. Rodá-lo copia a coorte por cima (com `.bak`) e regrava o artefato. É determinístico, mas qualquer notebook C rodado **antes** dele fica com o hash antigo; por isso ele roda primeiro, e nunca depois do teste (#2).
- **Notebooks desatualizados:** B_04 (27/10) e B_05 (30/10) foram salvos antes de mudanças em `src/`; B_02, A_03, 00 e 01 estão sem execução salva.
- **Dependência faltando:** o C_11 importa `cloudpickle`, que não está no `requirements.txt` (restaurado em 03/11, com 17 linhas) nem no `pyproject.toml`.
- **Tempo de máquina (pelos carimbos das últimas execuções):** B_04 ≈ 5 min e B_05 ≈ 6 min; C_14 ≈ 1,5 min; C_11, C_12 e C_15 de poucos minutos cada (estimativa). B_02 e A_03 não têm carimbo: meça. Estimativa para a cadeia inteira: 30 a 45 min.
- **Não executar aqui:** o C_16 (roda uma vez, em 05/11), o 00 e o 01 (baixam dados; ficam sem saídas e o README explica).
- **C_13:** a execução limpa roda a busca da grade do YAML (a de referência do #1). O modelo final vem do #155 e do YAML; o README diz isso numa linha.

### ③ O que fazer

> [!ok] Parte mecânica aplicada por script em 03/11 (commit `b3772de`)
> `cloudpickle` está no `requirements.txt` e no `pyproject.toml`, ambos com `>=` (como as demais linhas desses arquivos, e não com `==` como o passo 1 descreve). O README já usa os nomes atuais dos notebooks, não tem mais “Pontos de atenção conhecidos” e descreve o `test_pandemic`. Falta a execução limpa e o resto do README.

**Dono:** Pessoa C (execução) + Pessoa B (README) · **Prazo:** 04/11, 19h às 22h · **Começa quando:** #155 (modelo final congelado), #152, #153, #158 e #159 · **Script previsto:** `executar_cadeia.py` (começa por relatório; roda a cadeia na ordem, para no primeiro erro, anota tempo e memória e já limpa os caminhos locais do #156). O que segue é o plano B.

1. **Dependência (C, 2 min):** acrescente `cloudpickle` ao `requirements.txt` (versão: `python -c "import cloudpickle; print(cloudpickle.__version__)"`, fixada com `==`) e ao `pyproject.toml` (`>=`). `pytest tests/test_config.py -q` deve passar.
2. **Execução (C, na máquina oficial do #158):** com os nomes finais do #146 (ou os atuais, se ele for cortado), cada notebook com `tools\medir_notebook.py <arquivo> --salvar-no-lugar --limite-mb 12288`, **nesta ordem**: A_03 (primeiro), B_02, B_04, B_05, C_11, C_12, C_14, C_13, C_15. **Não rode o C_16, o 00 nem o 01.**
3. **Confira o C_15 desta cadeia:** o limiar impresso precisa ser o `limiar.otimo` do YAML (todas as casas). O A_03 regrava o artefato, e o hash pode ter mudado; o C_15 que você acabou de rodar já usa o hash novo, que é o que o C_16 vai procurar. Se o limiar diferir, copie o novo para o YAML e **registre** (o C_16 não deixa passar nada diferente).
4. **Caminhos locais (C, 2 min):** logo depois da execução, o comando do #156.
5. **README (B, 1 h 30), seções curtas:** objetivo e pergunta; dados (SIVEP-Gripe, `dados-v2`, coorte definitiva de 3.884.728 notificações); desenho (70/15/15 por grupo, Teste A, Teste B, 2020–2022 isolado, 2026 fora); estrutura de pastas real; ordem de execução dos notebooks, com o que cada um lê e grava (§10 do pacote de referência); como instalar (`python -m venv .venv`, `pip install -r requirements.txt`) e a versão do Python testada (3.14.7); como rodar os testes (`pytest -q`); onde estão as decisões (`docs/decisoes.md`) e os resultados (`resultados/`); uma linha dizendo que os arquivos de saída começam por `C3_`, `C4_`, `C5_` e `C6_` (sem citar o nome antigo dos notebooks); que o C_16 já foi executado uma vez (reabrir exige `SRAG_ALLOW_TEST_REOPEN=1` e registro); e três linhas de limitações. **Apague** a seção "Pontos de atenção conhecidos". Nenhum nome de pessoa nem número de card.
6. Commit: `docs: README da entrega e execução limpa da cadeia [done:#126]`, e **faça o push** (o #163 clona do GitHub).

### ④ Pronto quando

- nao-contem: `README.md` :: `_provisorio_construcao_coorte_b` | O README não cita mais o notebook da coorte provisória.
- nao-contem: `README.md` :: `C6_validacao_final` | O README não usa mais os nomes antigos dos notebooks C.
- nao-contem: `README.md` :: `Pontos de atenção conhecidos` | A seção escrita por auditoria automática saiu do README.
- contem: `README.md` :: `test_pandemic` | O README descreve o Teste B e a janela 2020–2022.
- contem: `requirements.txt` :: `cloudpickle` | A dependência do notebook do pipeline está declarada.
- contem: `pyproject.toml` :: `cloudpickle` | O pyproject.toml também declara o cloudpickle.
- manual: | Todos os notebooks da lista, exceto 00, 01 e o de validação final, foram reexecutados em 04/11 e salvos com saídas; a tabela outputs/final/performance_notebooks.csv tem uma linha de 04/11 para cada um.

## #28 · O YAML diz que o finalista é escolhido no fim do C_16, mas o C_16 exige antes

- prioridade: P3
- situação: resolvida
- estratégia: resolvida
- marco: M4
- data ideal: Concluído
- responsável: Pessoa C (antes: Pessoa A)
- pessoas: C
- fonte: configs/supervised.yaml (selecao_modelos.finalista_escolhido); notebooks C_15 e C_16
- depende de: #132
- tags: Código, Documentação, Gate
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 2
- novo: não
- professores: não

### ① Para entender

O comentário do YAML e o código contam histórias diferentes. O certo é escolher o finalista no C_15 (proposta atual: `hist_gradient_boosting`, AUC 0,7875) e o C_16 apenas usá-lo.

### ② Problema

O comentário do YAML diz que `finalista_escolhido` é preenchido no fim do C_16, mas o C_16 exige esse campo preenchido antes de rodar.

### ③ O que fazer

> [!ok] Resolvida (revisão de 24/10)
> O YAML não cita mais o C_16 para preencher o finalista; a descrição do G6 manda preencher `finalista_escolhido` ao fim do ajuste, e o C_15 faz isso (#132, passo 4).

### ④ Pronto quando

- yaml: `configs/supervised.yaml` :: `gates.G6_finalistas_tuning.descricao` contem `finalista_escolhido` | A descrição do G6 manda preencher finalista_escolhido ao fim do ajuste (e não no C_16).
- nao-contem: `configs/supervised.yaml` :: `fim do C_16` | O YAML não diz mais que o finalista é escolhido no fim do C_16.

## #26 · O manifesto nunca registra que o teste foi aberto

- prioridade: P2
- situação: aberta
- estratégia: desenvolver
- marco: M5
- data ideal: 02/11
- responsável: Pessoa A (dentro do #148, C_16)
- pessoas: A
- fonte: src/data/supervised_artifact.py (manifesto); notebooks C_16
- depende de: #148
- tags: Código, Vazamento
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 0
- novo: não
- professores: não
- removido: absorvido pelo #148 em 03/11 (o C_16 grava test_opened no manifesto)

### ① Para entender

O campo `test_opened` do manifesto fica sempre `false`, mesmo depois do C_16. O registro só existe no YAML.

### ② Problema

> [!atenção] Replanejamento de 31/10 · versão 2 (entrega em 04/11)
> Replanejamento v2: este card é **resolvido dentro do card indicado em "responsável"**; sem esforço próprio. Marque como concluído junto com ele.

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que esta pendência está aberta
> A auditoria automática do painel (27/10, 14:40) marcou este item como resolvido com base em commits de 12 e 18/10, todos anteriores às revisões de 24 e 26/10 e sem relação com a entrega descrita aqui. Isso acontece por um defeito do painel: a cada auditoria, um commit antigo ainda não rejeitado reabre a sugestão (detalhes no #94).
> Nenhum código grava `test_opened: true`; `supervised_artifact.py` só escreve `False` (linha do `_build_manifest`). Passa a ser feito dentro do #2 (três linhas no C_16).

O manifesto tem o campo `test_opened`, mas ele nunca muda para `True`, nem depois de o C_16 consultar o teste. O registro de abertura fica só no YAML.

### ③ O que fazer

**Resolvido dentro do #148 e do #2.** Logo depois de carregar o primeiro bloco de teste, o C_16 regrava `data/analytical/manifesto_supervisionado.json` com `test_opened: true`, a data e o commit. Sem função nova.

### ④ Pronto quando

- json: `data/analytical/manifesto_supervisionado.json` :: `test_opened` = `true` | O manifesto do artefato registra test_opened: true depois que o C_16 carrega os testes (três linhas dentro do C_16, no #2).
- contem: `notebooks/C/C_16_validacao_final.ipynb` :: `test_opened` | O C_16 regrava o manifesto com test_opened, data e commit.

## #12 · Intervalos impossíveis entram no modelo como se fossem válidos

- prioridade: P2
- situação: resolvida
- estratégia: resolvida
- marco: M8
- data ideal: Concluído
- responsável: Pessoa A (dona; revisão cruzada sem edição concorrente)
- pessoas: A
- fonte: src/features/engineering.py (intervalo_sintomas_internacao); configs/supervised.yaml (features.engenharia.intervalo_politica)
- depende de: #82
- tags: Diverge do decidido, Código, Features
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 3
- novo: não
- professores: não

### ① Para entender

Com a política "sinalizar", o intervalo de −10 dias ou 200 dias entra no modelo como número normal, e a bandeira que avisa que ele é estranho (`flag_intervalo_invalido`) é criada mas não usada.

> [!exemplo] Exemplo
> Um paciente com intervalo de −30 dias (erro de digitação) é tratado pelo modelo como alguém que "chegou muito cedo".

### ② Problema

Com a política `sinalizar`, `dias_sintomas_ate_internacao` entra no modelo com valores negativos e acima de 60 dias. A flag que identifica esses casos (`flag_intervalo_invalido`) é criada, mas não está nas features. O modelo, então, trata intervalos impossíveis como valores válidos.

### ③ O que fazer

> [!ok] Situação em 24/10: resolvido pela coorte definitiva
> Os intervalos impossíveis foram excluídos pelo contrato (`D_COORTE_006/007`; ver #82). Na coorte de modelagem, `flag_intervalo_invalido` é sempre 0. Por isso não entra como feature e não precisa entrar.

**Ação:** no #131, um teste que confirme `dias_sintomas_ate_internacao` entre 0 e 60 em todas as linhas do artefato. No relatório (Pessoa A), uma frase em Métodos.

### ④ Pronto quando

- contem: `configs/final_cohort_v1.yaml` :: `intervalo_sintomas_negativo` | Os intervalos negativos são excluídos pelo contrato da coorte definitiva.
- contem: `configs/final_cohort_v1.yaml` :: `intervalo_sintomas_maior_limite` | Os intervalos acima de 60 dias são excluídos pelo contrato, então flag_intervalo_invalido é sempre 0 na coorte de modelagem.

## #45 · Vacina contra COVID marcada como "sim" antes de existir a vacina

- prioridade: P3
- situação: aberta
- estratégia: documentar
- marco: M6
- data ideal: 01/11
- responsável: Pessoa A (dentro do #133, seções 2 a 4)
- pessoas: A
- fonte: B_06 (achado); configs/supervised.yaml (contexto_incremental); src/features/engineering.py
- depende de: —
- tags: Dados/Coorte, Features
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 0
- novo: não
- professores: não
- removido: absorvido pelo #133 em 03/11 (qualidade dos dados no relatório)

### ① Para entender

Há 55 fichas de 2019 e 24.284 de 2020 com vacina contra COVID = sim. O YAML usa o campo bruto, sem olhar a data da dose.

<div class="bars">
<div class="br"><span class="y">2019</span><div class="t"><div class="b " style="width:2.0%"></div></div><span class="v">55</span></div>
<div class="br"><span class="y">2020</span><div class="t"><div class="b red" style="width:97.1%"></div></div><span class="v">24.284</span></div>
</div>

### ② Problema

> [!atenção] Replanejamento de 31/10 · versão 2 (entrega em 04/11)
> Replanejamento v2: uma frase ou parágrafo dentro do **#133** (domingo, Pessoa A); sem esforço próprio.

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que esta pendência está aberta
> A auditoria automática (27/10, 14:40) marcou "precisa revisão" por achados que não tratam deste item: a linha decorativa `=====` no cabeçalho de `src/protocolo/verificacoes.py` (lida como conflito de merge) e o `OneHotEncoder` denso do B_06, que roda numa amostra de 80 mil fichas e será substituído pelo #136 (detalhes no #94).
> A frase de limitação no relatório ainda não existe (o relatório não começou, #133).

Há registros com vacina contra COVID-19 marcada como "sim" em 2019 (55) e em 2020 (24.284), antes de a vacina existir. O YAML usa `vacina_cov` bruta, sem considerar a data da dose, o que contraria a seção 17 das decisões.

### ③ O que fazer

**Pessoa A, dentro do #133 (01/11):** escreva em Dados e Métodos: "55 fichas de 2019 e 24.284 de 2020 marcam vacina contra COVID-19 como 'sim' antes de a vacina existir; por isso a vacinação não integra o modelo principal e aparece apenas como contexto incremental". A regra de dose anterior à internação (#84) fica como trabalho futuro.

### ④ Pronto quando

- manual: | A frase de limitação com as contagens (55 "sim" em 2019 e 24.284 em 2020, antes de a vacina existir) e a regra adotada está no relatório (#133).

## #46 · 58 linhas repetem 29 números de notificação na base bruta

- prioridade: P3
- situação: aberta
- estratégia: documentar
- marco: M6
- data ideal: 01/11
- responsável: Pessoa A (dentro do #133, seções 2 a 4)
- pessoas: A
- fonte: Construção da coorte
- depende de: #135
- tags: Dados/Coorte
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 0
- novo: não
- professores: não
- removido: absorvido pelo #133 em 03/11 (qualidade dos dados no relatório, §29.10)

### ① Para entender

Pode ser reenvio da mesma ficha ou erro de digitação. A regra definitiva fica com o item 10.

### ② Problema

> [!atenção] Replanejamento de 31/10 · versão 2 (entrega em 04/11)
> Replanejamento v2: uma frase ou parágrafo dentro do **#133** (domingo, Pessoa A); sem esforço próprio.

Na base bruta, 58 linhas repetem 29 números de notificação.

### ③ O que fazer

**Pessoa A, dentro do #133 (01/11):** uma frase com a contagem de números de notificação repetidos **na coorte definitiva** (`manifesto_particao.json`: `rows_before_quarantine`, linhas fora e grupos; no `train_ref` são 556.461 grupos em 556.462 linhas) e a regra de grupo (§29.10): a mesma ficha fica sempre no mesmo bloco. A contagem 58 linhas / 29 números é da base bruta.

### ④ Pronto quando

- manual: | O relatório traz a contagem de números de notificação repetidos na coorte definitiva (do #135) e a regra de grupo (#10).

## #47 · Idades, datas e anos impossíveis

- prioridade: P3
- situação: aberta
- estratégia: documentar
- marco: M6
- data ideal: 01/11
- responsável: Pessoa A (dentro do #133, seções 2 a 4)
- pessoas: A
- fonte: Construção da coorte
- depende de: #135
- tags: Dados/Coorte
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 0
- novo: não
- professores: não
- removido: absorvido pelo #133 em 03/11 (qualidade dos dados no relatório)

### ① Para entender

| Problema | Quantidade | Tratamento atual |
|---|---|---|
| Idade implausível (fora de 0–120) | 24 na coorte (38 na base) | idade vira vazio, registro mantido |
| Internação depois do fechamento da base | 17 | a decidir |
| Datas com ano fora da faixa | 260 (138 de vacina COVID) | viram vazio |
| Nascimento depois dos sintomas | 1 | excluir |

### ② Problema

> [!atenção] Replanejamento de 31/10 · versão 2 (entrega em 04/11)
> Replanejamento v2: uma frase ou parágrafo dentro do **#133** (domingo, Pessoa A); sem esforço próprio.

Há 24 idades implausíveis (mantidas com a idade vazia), 17 internações com data posterior ao fechamento da base e 260 datas com ano fora da faixa válida.

### ③ O que fazer

**Pessoa A, dentro do #133 (01/11):** use a contagem de `idade_anos` vazia por bloco (#135) numa frase de Métodos ("idades implausíveis foram tratadas como ausentes e imputadas pela mediana do treino, n = …") e as contagens de datas fora do período (do manifesto de auditoria da coorte) numa tabela do apêndice.

### ④ Pronto quando

- manual: | A frase de Métodos sobre idades implausíveis (tratadas como ausentes e imputadas pela mediana do treino, com n) e a tabela de datas fora do período no apêndice estão no relatório.

## #56 · Mostrar por que a data de internação é a âncora, e quem ficou de fora

- prioridade: P2
- situação: aberta
- estratégia: documentar
- marco: M4
- data ideal: 01/11
- responsável: Pessoa A (0,5 h)
- pessoas: A
- fonte: B_06_eda_temporal_clustering; construção da coorte
- depende de: —
- tags: Metodologia, Dados/Coorte, Documentação
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 0.5
- novo: não
- professores: não
- removido: absorvido pelo #133 em 03/11 (seção Dados e coorte, com a §29.23)

### ① Para entender

Falta a tabela da diferença entre `dt_notific` e `dt_interna`, que sustenta a escolha da âncora, e a comparação entre os casos excluídos por falta de desfecho e os incluídos.

<div class="kpi">
<div><b>97.786</b>excluídos por evolução não encerrada (waterfall A_03)</div>
<div><b>36.923</b>excluídos por óbito por outra causa ou ignorado</div>
</div>

### ② Problema

> [!atenção] Replanejamento de 31/10 · versão 2 (entrega em 04/11)
> Domingo, 13h às 13h30. O notebook `A6_ancora_e_selecao` já existe e gera as duas tabelas; falta **rodar e conferir**. No #146 ele é incorporado ao notebook 04.

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que esta pendência está aberta
> A auditoria automática (27/10, 14:40) marcou "precisa revisão" por achados que não tratam deste item: a linha decorativa `=====` no cabeçalho de `src/protocolo/verificacoes.py` (lida como conflito de merge) e o `OneHotEncoder` denso do B_06, que roda numa amostra de 80 mil fichas e será substituído pelo #136 (detalhes no #94).
> Não existem `outputs/final/ancora_notificacao.csv` nem `excluidos_vs_incluidos.csv`.

Não foram produzidas a tabela da diferença entre `dt_notific` e `dt_interna`, que sustenta a escolha da internação como âncora, e a comparação entre casos excluídos por falta de desfecho e casos incluídos.

### ③ O que fazer

**Dono:** Pessoa A · **Prazo:** 01/11 (domingo), 13h às 13h30 · **Esforço estimado:** ≈ 30 min · **Começa quando:** imediatamente

1. Execute `notebooks/A/A6_ancora_e_selecao.ipynb` com `.\.venv\Scripts\python.exe tools/medir_notebook.py notebooks/A/A6_ancora_e_selecao.ipynb` (lê só `dt_notific`, `dt_interna`, `dt_sin_pri`, `evolucao`, `sg_uf`, `nu_idade_n`, `tp_idade`, `hospital` e `nosocomial`).
2. Confira as duas tabelas em `outputs/final/`: **âncora** (`ancora_notificacao_internacao.csv`: mediana e intervalo interquartil de `dt_notific − dt_interna`, por ano e desfecho) e **quem ficou de fora** (`excluidos_vs_incluidos.csv`: hospitalizados com desfecho fora do alvo, evolução 3, 9 ou vazio, × incluídos, em % por ano e região). Valores de referência: 97.786 excluídos por evolução não encerrada e 36.923 por óbito por outra causa ou ignorado (waterfall).
3. Escreva uma frase de leitura para cada tabela no relatório (#133, seção 2): a notificação costuma vir **depois** da internação, por isso a âncora é a internação; os excluídos têm perfil diferente (ou parecido) dos incluídos.
4. O conteúdo do notebook vira seção final do notebook 04 no #146; não apague o A6 antes.

### ④ Pronto quando

- existe: `outputs/final/ancora_notificacao_internacao.csv` | A mediana e o intervalo interquartil de (dt_notific − dt_interna) por ano estão em outputs/final/ancora_notificacao_internacao.csv.
- existe: `outputs/final/excluidos_vs_incluidos.csv` | A comparação excluídos (desfecho fora do alvo) × incluídos está em outputs/final/excluidos_vs_incluidos.csv.
- manual: | Uma frase de leitura de cada tabela está no relatório.

## #69 · Plano v2 e orientação de TCC descrevem outro período e outra divisão

- prioridade: P3
- situação: aberta
- estratégia: documentar
- marco: M6
- data ideal: 01/11
- responsável: Pessoa A (dentro do #133, seções 2 a 4)
- pessoas: A
- fonte: Plano_Unificado_SRAG_3_Pessoas_v2.docx
- depende de: —
- tags: Documentação, Partição
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 0
- novo: não
- professores: não
- removido: absorvido pelo #133 em 03/11 (o relatório descreve só o desenho final)

### ① Para entender

> [!ok] Decisão fechada em 18/10
> A coorte definitiva inicial será a seleção de features da coorte provisória. O treino principal usará exclusivamente 2019, 2023, 2024 e 2025. Haverá duas janelas de teste: (A) 2019, 2023, 2024 e 2025; (B) 2019 a 2025, incluindo 2020–2022. O ano de 2026 não participa do desenvolvimento nem dos testes principais e fica apenas como exploração opcional, depois de todo o restante concluído.

Os dois documentos falam em 2022–2025 com divisão temporal. O projeto executou 2019–2026 com sorteio estratificado. Quem ler os planos vai entender outro estudo.

### ② Problema

> [!atenção] Replanejamento de 31/10 · versão 2 (entrega em 04/11)
> Replanejamento v2: uma frase ou parágrafo dentro do **#133** (domingo, Pessoa A); sem esforço próprio.

O plano v2 ainda descreve treino 2022–2023, validação 2024, teste 2025, 2026 fora e âncora temporal com 2026 excluído. Isso contradiz a decisão vigente: período 2019–2026 com divisão aleatória 70/15/15 estratificada e coorte provisória.

### ③ O que fazer

**Pessoa A, dentro do #133 (01/11):** parágrafo de trajetória em Métodos: "o desenho inicial previa desenvolvimento em 2022–2024 e avaliação em 2025; foi substituído por treino em 2019 e 2023–2025 com duas janelas de teste porque …" (use o `decisoes.md` §28 e §29.25). Mostrar a evolução conta a favor.

### ④ Pronto quando

- manual: | O Plano Unificado v2 e a Orientação de 03/10 têm o aviso "HISTÓRICO" no topo (se estiverem no repositório ou na pasta da equipe) e o relatório tem o parágrafo de trajetória do desenho.

## #70 · Dicionário de variáveis do modelo final

- prioridade: P2
- situação: parcial
- estratégia: documentar
- marco: M7
- data ideal: 04/11
- responsável: Pessoa A (0,5 h)
- pessoas: A
- fonte: Revisão de 03/11 (escopo reduzido às 31 variáveis do modelo)
- depende de: #140
- tags: Documentação, Dados/Coorte
- pilar: Documentação
- carga: 0.5
- novo: não
- professores: não

### ① Para entender

O relatório e o README precisam de uma tabela que diga, para cada variável do modelo, o que ela é no SIVEP-Gripe, como foi tratada e por que entrou.

### ② Problema

> [!decisão] Revisão de 03/11 · versão 3 · escopo reduzido
> Em vez de atualizar o dicionário inteiro da base (199 colunas), o card entrega só as 30 variáveis de `features.final` (lista do #140) (mais o alvo e as colunas de auditoria), que é o que a banca precisa.

### ③ O que fazer

**Dono:** Pessoa A · **Prazo:** 04/11 · **Começa quando:** #140

1. **Fonte:** o dicionário completo já existe em `configs/dicionario_variaveis_v1.csv` (68 KB, usado pelo B_04). Filtre as linhas das variáveis do modelo; não escreva descrições do zero. Gere a lista a partir do YAML (`features.final`, `target.coluna`, `audit_columns` do manifesto do artefato).
2. Confirme no dicionário oficial do SIVEP-Gripe os dois códigos que ficaram em aberto (do #49): `ave_suino` = 3 (outro animal) e `cs_raca` = 5 (indígena).
3. Crie `docs/dicionario_variaveis.md` com uma linha por variável: nome, descrição no SIVEP-Gripe, tipo (numérica/categórica), códigos, tratamento (branco, 9 = ignorado, recodificação) e motivo de entrar.
4. Cite o arquivo no README (#126) e no relatório (#133). Se existir `configs/dicionario_variaveis_v1.csv` citado no README e não existir no repositório, tire a citação. Commit: `docs: dicionário das variáveis do modelo [done:#70]`.

**Script previsto:** `dicionario_variaveis.py` (lê `configs/dicionario_variaveis_v1.csv`, filtra as 30 variáveis do `features.final` mais o alvo e as colunas de auditoria, e gera o `docs/dicionario_variaveis.md`; começa por relatório). Precisa do CSV, que o pacote de referência lista mas não copia.

### ④ Pronto quando

- existe: `docs/dicionario_variaveis.md` | O dicionário das variáveis do modelo existe.
- contem: `docs/dicionario_variaveis.md` :: `dias_sintomas_ate_internacao` | O dicionário cobre as variáveis numéricas do modelo.

## #71 · Cuidados de redação no relatório

- prioridade: P2
- situação: aberta
- estratégia: documentar
- marco: M6
- data ideal: 03/11
- responsável: Pessoa A (0,5 h)
- pessoas: A
- fonte: Projeto (relatório)
- depende de: #55, #91
- tags: Documentação, Metodologia
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 0.5
- novo: não
- professores: não
- removido: absorvido pelo #133 em 03/11 (frases de redação no esqueleto do relatório)

### ① Para entender

- A unidade é a **notificação**, não a pessoa.
- As associações são **preditivas**, não causais.
- 2026 é ano **parcial**.
- O modelo foi avaliado com **sorteio**; a validação em anos futuros é complementar.
- A lista de variáveis importantes (item 91) é de associação, não de causa.

### ② Problema

> [!atenção] Replanejamento de 31/10 · versão 2 (entrega em 04/11)
> Terça-feira, à noite, 30 minutos: a verificação de redação é feita no relatório e a mesma lista vale para os slides (#134).

Pontos de redação: a unidade de análise é a notificação, não a pessoa; as associações são preditivas, não causais; 2026 é ano parcial; o modelo, avaliado com divisão aleatória, não foi validado em anos futuros.

### ③ O que fazer

**Dono:** Pessoa A · **Prazo:** 03/11 (terça), à noite · **Esforço estimado:** ≈ 30 min · **Começa quando:** #55 e #91

Percorra o relatório com a lista (use a busca do editor para cada termo entre aspas):
- "notificações", não "pacientes" ou "pessoas" (a unidade é a notificação);
- "associado a maior risco previsto", nunca "causa", "causado por" ou "protege";
- Teste A × B: "robustez à mudança de período", nunca "efeito da pandemia";
- "demonstração acadêmica retrospectiva; não validado para uso clínico";
- 2026: "parcial" e "exploratório";
- geografia: "heterogeneidade entre regiões, que pode refletir acesso, capacidade e registro";
- ausência: "ausência de registro", não "ausência da condição";
- todo número tem origem num arquivo de `outputs/final/` ou manifesto (planilha do #133).

A Pessoa B confere a mesma lista nos slides em 04/11.

### ④ Pronto quando

- manual: | A lista de verificação de redação deste card foi aplicada no relatório e nos slides (Pessoa A) e conferida pela Pessoa B: notificações, associação preditiva, robustez temporal, 2026 parcial, heterogeneidade regional, ausência de registro e número com origem.

## #133 · Relatório final: seções, rastreabilidade de cada número e limitações

- prioridade: P1
- situação: aberta
- estratégia: documentar
- marco: M7
- data ideal: 05/11
- responsável: Pessoa A (5 h) + Pessoa B (2 h) + Pessoa C (1,5 h)
- pessoas: A, B, C
- fonte: Orientação do TCC; decisoes.md; revisão de 03/11 (absorve #56, #71, #45, #46, #47 e #69)
- depende de: #2
- tags: Relatório, Entrega
- pilar: Valor científico-acadêmico + Documentação
- carga: 8.5
- novo: não
- professores: sim

### ① Para entender

O relatório é a peça que a banca lê. Ele precisa contar uma história curta e defensável: a pergunta, a coorte, o desenho que protege o teste, o modelo escolhido, a calibração, o limiar, o desempenho nas duas janelas e o que **não** se pode concluir. Cada número tem de vir de um arquivo do repositório.

### ② Problema

> [!decisão] Revisão de 03/11 · versão 3
> Seis cards pequenos eram só parágrafos deste relatório e foram absorvidos: âncora e quem ficou de fora (#56, §29.23), cuidados de redação (#71, §29.20), vacina marcada antes de existir (#45), 58 linhas com 29 números repetidos (#46, §29.10), idades e datas impossíveis (#47) e a diferença entre o plano v2 e a orientação e o desenho final (#69).

O texto descreve **só o desenho final** (70/15/15 e coorte definitiva); versões intermediárias não entram no relatório.

> [!decisão] Revisão de 03/11 · versão 3.2
> Os cards pós-entrega foram removidos (o projeto termina em 05/11). O que eles tinham de útil para a banca virou uma frase de **Limitações** ou de **Trabalhos futuros** neste card (lista no ③).

> [!decisão] Revisão de 03/11 · versão 4.0
> O relatório ganhou três seções que a leitura do repositório mostrou que faltavam: maturidade do desfecho (#160), equidade (#55, #161) e a comparação com as hipóteses registradas antes do teste (#161). Veja os acréscimos no ③.

### ③ O que fazer

**Dono:** Pessoa A (organiza, Métodos, Resultados, Discussão, Limitações) + Pessoa B (Introdução, revisão, agrupamento) + Pessoa C (modelos, calibração, limiar, importância) · **Prazo:** tudo o que não depende do teste em 04/11; números do teste em 05/11, 10h às 14h, com conferência às 14h · **Começa quando:** já (as seções de resultados do teste esperam o #2)

**Esqueleto (≈ 12 a 15 páginas):**

| Seção | Fonte | Quem |
|---|---|---|
| Introdução e pergunta | revisão (#112) | B |
| Dados e coorte (âncora em `dt_interna`, exclusões em cascata, quem ficou de fora; #45, #46, #47 como qualidade dos dados) | `final_cohort_v1.yaml`, `outputs/coorte_candidata/manifesto_coorte.json`, §29.10 e §29.23 | A |
| Desenho: 70/15/15 por grupo, Teste A, Teste B e 2020–2022, 2026 fora, teste aberto uma vez | `manifesto_particao.json`, §21, §22, §29.33 e §29.37 | A |
| Variáveis do modelo (30; entram saturação e desconforto, saem os três sintomas da era COVID) | §29.34, C_14 | A |
| Exploração e agrupamento (clusters refletem idade e preenchimento; perfil por qui-quadrado e ANOVA) | B_04, §29.7, #137 | B |
| Modelos e ajuste (G6 e exploração de 04/11), peso de classe, calibração (G7), limiar (G8) | C_13, C_15, §29.35 a §29.37 | C |
| Resultados: tabela das três janelas, por ano, por região e faixa etária, falsos negativos | `C6_*_janelas.csv`, #55 | A |
| Importância das variáveis | #91 | C |
| Discussão e limitações (texto pronto abaixo) | — | A |
| Reprodutibilidade (ordem dos notebooks, hashes, testes) | README (#126) | A |

**Frases que precisam estar no texto (cuidados de redação, #71):**
- "A diferença entre o Teste A e o Teste B mede a robustez a uma mudança de período, não o efeito causal da pandemia."
- "Associações de variáveis com o desfecho não são efeitos causais; as que parecem protetoras são, em geral, efeito da idade."
- **Limitação do desenho:** "A seleção de variáveis e de hiperparâmetros e a calibração e a escolha do limiar usaram a mesma validação (`val_ref`), em metades disjuntas para calibrar e medir. Por isso as métricas de validação são otimistas; as estimativas de referência são as do teste, aberto uma única vez."

**Rastreabilidade:** cada tabela e cada número no texto tem, em nota ou legenda, o arquivo de origem (`outputs/tables/...`). Em 05/11 às 14h, A e C conferem cada número contra o arquivo (lista no comentário do card).

**Limitações e trabalhos futuros (uma frase cada; vieram dos cards removidos em 03/11):**
- A sazonalidade (semana do ano em seno e cosseno) é calculada, mas não entra no modelo principal.
- A checagem automática de vazamento compara nomes de colunas com a lista proibida; a proteção principal é o contrato de variáveis congelado e a revisão da temporalidade de cada variável.
- 2026 é ano parcial, com desfechos pendentes: fica fora do desenvolvimento e do teste. Aplicar o modelo congelado a 2026 é trabalho futuro.
- O agrupamento usa PCA; UMAP é trabalho futuro.
- Saturação e desconforto respiratório fazem parte da definição de caso, mas a ficha não registra a hora da medição.
- Perda de olfato, perda de paladar e fadiga saíram do modelo por serem campos da era COVID (marcador de período); a linha "P + 3 sintomas" do C_14 mostra que não faziam falta.
- Vacinação não entra no modelo, porque não há regra confiável para saber quais doses são anteriores à internação.

**Texto que só pode ser escrito depois da reexecução:** o parágrafo de desempenho por padrão de preenchimento do B_05 (célula 52) ainda cita a validação de 39.748 fichas, e os números do agrupamento do B_04 mudam com a lista nova de variáveis; reescreva os dois com a execução limpa (#126).

**Acréscimos de 03/11 (v4.0, da leitura completa do repositório):**
- **Dados e coorte, proveniência:** a base é o SIVEP-Gripe do OpenDataSUS, consolidado no `srag.parquet` da release `dados-v2` (4.666.910 linhas × 198 colunas; o SHA-256 está em `data/manifest_dados-v2.yaml`). O script que gerou o Parquet a partir dos arquivos INFLUD **não está no repositório**: diga isso numa frase.
- **Maturidade do desfecho (#160):** a tabela por ano e a frase sobre 2025.
- **Equidade (#55, #161):** raça/cor, zona, região e faixa etária, com o que **não** se pode concluir (a orientação diz "incluir com cautela").
- **Referência simples (#161):** o modelo contra "só idade e sexo", em PR-AUC ÷ prevalência.
- **Corte por região (versão mínima, decisão de 03/11):** uma frase de limitação (o professor sugeriu um corte por região; fizemos modelo único, corte global e métricas e calibração por região; o corte regional fica como trabalho futuro) e a figura do #55.
- **Hipóteses registradas (#161):** compare o resultado do teste com a §29.38 e diga onde acertamos e onde não.
- **Pré-escrita:** em 04/11, deixe cerca de 80% do relatório escrito com os números do `val_ref` e o marcador `[TESTE]` onde entram os números do teste. Em 05/11, só se preenchem os marcadores (o script `tabelas_relatorio.py` gera as tabelas a partir dos CSV do C_16).

### ④ Pronto quando

- manual: | O relatório tem todas as seções do esqueleto, as três frases de redação e a limitação do desenho, e descreve só o desenho final (70/15/15 e coorte definitiva).
- manual: | Cada número do relatório foi conferido contra o arquivo citado na legenda; a lista da conferência foi colada como comentário neste card.

## #134 · Apresentação e defesa: roteiro, slides e perguntas difíceis

- prioridade: P1
- situação: aberta
- estratégia: documentar
- marco: M8
- data ideal: 05/11
- responsável: Pessoa B (2,5 h) + Pessoa A (0,25 h) + Pessoa C (0,25 h)
- pessoas: B, A, C
- fonte: Revisão de 03/11
- depende de: #133
- tags: Apresentação, Entrega
- pilar: Valor científico-acadêmico
- carga: 3
- novo: não
- professores: sim

### ① Para entender

A apresentação de 05/11 é uma entrega em si. Ela precisa mostrar em poucos minutos a pergunta, o desenho que protege o teste, o resultado principal (Teste A) e a leitura honesta do Teste B.

### ② Problema

A banca deve perguntar justamente sobre os pontos que mudaram nesta reta final. Ter as respostas prontas vale mais do que um slide a mais.

### ③ O que fazer

**Dono:** Pessoa B · **Prazo:** 05/11 (rascunho dos slides sem os números do teste em 04/11 à noite; números às 14h; ensaio às 15h) · **Começa quando:** #133

**Roteiro (≈ 10 slides):** pergunta e relevância · dados e coorte (funil de exclusões) · desenho (70/15/15 por grupo, Teste A, Teste B, 2020–2022) · exploração em um slide (agrupamento = idade e preenchimento) · modelos e escolha (G6) · calibração e limiar (G7, G8) · resultados nas três janelas · importância das variáveis · limitações · conclusão.

**Perguntas difíceis (resposta de uma frase cada, no fim do roteiro):**
- Vocês testaram muitos hiperparâmetros na validação: isso não infla o resultado? (sim, na validação; por isso a regra de ganho mínimo, o orçamento fixo e a pré-seleção num recorte do treino no #155; o teste, aberto uma vez depois, é a medida honesta)
- Por que 70/15/15, e não validação cruzada? (base grande; divisão por grupo evita a mesma pessoa em dois blocos; referências do #112)
- A mesma validação escolhe e mede? (sim, em metades disjuntas para calibrar e medir; a medida honesta é o teste, aberto uma vez)
- Por que 2020–2022 só no teste? (robustez a mudança de período, sem interpretação causal)
- Saturação e desconforto respiratório não vazam informação do futuro? (fazem parte da definição de caso de SRAG hospitalizado e estão no campo 34 da ficha, "Sinais e Sintomas", junto com febre e tosse; limitação: a ficha não registra a hora da medição)
- Por que tirar perda de olfato, perda de paladar e fadiga? (são campos da era COVID: 99,7% em branco em 2019; marcavam o período, e tirá-los não custou desempenho; o professor pediu para estudar antes de tirar, e a ablação é esse estudo)
- Se alguém citar números de versões intermediárias (por exemplo, 21,9% de óbitos): eram de uma coorte preliminar, substituída pela definitiva com as regras de exclusão aprovadas (8,4% de óbitos); só a definitiva é usada.
- Por que PCA e não UMAP no agrupamento? (um professor sugeriu UMAP; os grupos encontrados refletem idade e padrão de preenchimento, e o perfil por qui-quadrado e ANOVA já mostra isso; UMAP fica como trabalho futuro)
- O modelo é justo entre regiões? (tabela do #55)

A e C revisam o roteiro (15 min cada) e cada pessoa ensaia a sua parte uma vez.

**Acréscimos de 03/11 (v4.0):**
- **Um slide "como ler os números"**, porque a apresentação é para colegas que não conhecem o projeto: PR-AUC e "vezes o acaso" (a prevalência é 8,4%; 3,8× a 4,2× no `val_ref`), Brier e o modelo nulo (≈ 0,077) e o que é calibrar.
- O modelo é melhor do que só usar idade e sexo? (linha de referência do #161)
- Por que não há um corte diferente por região? (o professor sugeriu; fizemos a versão mínima: modelo único, corte global e métricas e calibração por região; o corte regional ficou como trabalho futuro por falta de tempo antes do teste; a tabela por região mostra a diferença de sensibilidade que ele tentaria corrigir)
- O desfecho de 2025 já está fechado? (tabela do #160)
- O modelo trata raça/cor de forma diferente? (tabelas do #55; cautela: muito "ignorado" e branco)
- Por que não SHAP, UMAP ou validação cruzada? ("primeiro trabalho, não TCC"; base grande e validação fixa aceita pelo professor)

### ④ Pronto quando

- manual: | Os slides estão prontos, com as perguntas difíceis respondidas, e a equipe fez um ensaio completo antes da apresentação.

## #60 · Documentar que os clusters refletem idade e preenchimento, não perfis clínicos

- prioridade: P3
- situação: resolvida
- estratégia: resolvida
- marco: M6
- data ideal: Concluído
- responsável: Pessoa B (dona; revisão cruzada sem edição concorrente)
- pessoas: B
- fonte: B_06_eda_temporal_clustering (clustering)
- depende de: —
- tags: Metodologia, Documentação
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 2
- novo: não
- professores: não

### ① Para entender

Sem os indicadores de ausência, os 2 grupos viraram basicamente bebês × idosos (mortalidade 2,6% × 26,7%). O DBSCAN achou um único grupo. A conclusão foi encerrar o clustering como exploratório; falta escrever isso no relatório como resultado, não como falha.

### ② Problema

Os clusters refletem principalmente fases da vida (bebês e idosos), não perfis clínicos.

### ③ O que fazer

> [!ok] Resolvida (revisão de 24/10)
> A conclusão do B_06 já documenta que os grupos refletem fase da vida, período e registro, e não perfis clínicos. A nova rodada com one-hot (#136) e os testes estatísticos (#137) substituem esta discussão no relatório (#133, seção 10).

### ④ Pronto quando

- notebook-saida: `notebooks/B/B_06_eda_temporal_clustering.ipynb` :: `silhouette` | O B_06 salvo registra as métricas do clustering (silhouette), base da conclusão de que os grupos refletem fase da vida, período e registro.
- manual: | A conclusão do B_06 documenta que os grupos refletem idade, período e preenchimento, e não perfis clínicos; no relatório, a seção 10 usa o #136 e o #137.

## #136 · Não supervisionado com one-hot dos quatro estados e normalização: nova representação e nova rodada de agrupamento

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M3
- data ideal: 31/10
- responsável: Pessoa B (2,5 h)
- pessoas: B
- fonte: Orientação de 24/10 (cobrança de one-hot); base de conhecimento v9 §6.3 e §8; B_06 de 24/10
- depende de: #141, #142
- tags: Não supervisionado, Features, Código, Metodologia
- pilar: Valor científico-acadêmico + Performance
- carga: 2.5
- novo: sim
- professores: sim
- arquivos: src/features/normalization.py, tests/test_features.py, notebooks/B/B_06_eda_temporal_clustering.ipynb

### ① Para entender

O agrupamento atual (B_06) separou os pacientes em dois grupos que, no fim, eram só "crianças pequenas" e "adultos e idosos". A causa provável não é a doença, e sim **como os dados foram representados** para o algoritmo.

#### Como o algoritmo "enxerga" os pacientes
Algoritmos como K-Means medem **distância** entre fichas: quanto mais diferentes os valores, mais longe ficam. Por isso a forma de transformar cada campo em números decide o resultado.

| Conceito | O que é | Por que importa aqui |
|---|---|---|
| **One-hot** | Cada resposta possível vira uma coluna 0/1. "Febre = sim" vira `febre_sim=1, febre_nao=0, febre_ignorado=0, febre_AUSENTE=0`. | Mantém os quatro estados do SIVEP separados (sim, não, ignorado, em branco). Sem isso, "em branco" e "não" se misturam. |
| **Normalização (padronização)** | Ajustar números para a mesma escala (média 0, desvio 1). | Idade vai de 0 a 100; um sintoma vai de 0 a 1. Sem padronizar, a idade domina a distância. |
| **Peso por variável** | Dividir as colunas de cada variável por √(número de categorias). | Uma variável com quatro colunas não pode valer quatro vezes mais que a idade, que tem uma só. |

#### O que estava errado no B_06
Sintomas e comorbidades foram tratados como "binários": o campo em branco foi preenchido com o valor mais comum (geralmente "não") e a ausência foi para colunas separadas. Resultado: com essas colunas, os grupos separavam "ficha preenchida × vazia" (silhueta 0,364); sem elas, sobrou só a idade (silhueta 0,233; concordância ARI 0,09 com a solução anterior).

> [!ok] Cobrança dos professores (24/10)
> Testar o não supervisionado depois de passar tudo o que for possível por one-hot. É exatamente o que este item faz.

### ② Problema

> [!atenção] Replanejamento de 31/10 · versão 2 (entrega em 04/11)
> Passa a ser **pré-requisito do ponto de decisão (#140)**: toda exploração que pode mudar decisões acontece antes do ajuste fino. Escopo reduzido de ≈ 3 h para ≈ 2 h 30: HCA em 10 mil fichas, sem comparação com a representação antiga, e o perfil dos grupos feito **no próprio notebook** (o arquivo `src/evaluation/cluster_profile.py` do #137 não está no Git; não dependa dele). Agora com **código completo e testado**.

A representação usada no clustering misturou "em branco" com "não" e deu peso desigual às variáveis. Os professores cobraram testes com one-hot. Sem refazer, a parte de Não Supervisionado fica vulnerável na banca.

### ③ O que fazer

> [!decisão] Replanejamento de 31/10 · versão 2
> A representação one-hot vem **antes** de qualquer agrupamento. O resultado **não vira variável do modelo supervisionado**: se algo novo aparecer, o #140 decide; senão, vira parágrafo do relatório.

**Dono:** Pessoa B · **Prazo:** 31/10 (sábado), 18h às 21h · **Esforço estimado:** ≈ 2 h 30 (inclui a execução, em máquina, do notebook) · **Começa quando:** #141 e #142 (já concluídos)

#### Etapa 1 · representação (≈ 45 min)
1. O arquivo `src/features/normalization.py` está **vazio** no repositório. Cole nele, **inteiro** (o arquivo passa a ter exatamente este conteúdo; código testado):

```python
from __future__ import annotations

import numpy as np
from scipy import sparse
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.models.pipeline import _normalizador_categorico


class OneHotPonderado(BaseEstimator, TransformerMixin):
    """One-hot esparso em que cada variável pesa 1/sqrt(k) (k = categorias da variável)."""

    def fit(self, X, y=None):
        self.encoder_ = OneHotEncoder(handle_unknown="ignore", dtype=np.float32, sparse_output=True).fit(X)
        pesos = [np.full(len(cats), 1.0 / np.sqrt(len(cats)), dtype=np.float32) for cats in self.encoder_.categories_]
        self.pesos_ = np.concatenate(pesos)
        return self

    def transform(self, X):
        return sparse.csr_matrix(self.encoder_.transform(X).multiply(self.pesos_).astype(np.float32))

    def get_feature_names_out(self, input_features=None):
        return self.encoder_.get_feature_names_out(input_features)


def construir_preprocessador_clustering(numericas, categoricas, valor_ausente="AUSENTE"):
    """Numéricas: mediana + padronização. Categóricas: vazio vira 'AUSENTE' e depois one-hot ponderado."""
    pipe_num = Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())])
    pipe_cat = Pipeline([
        ("normalizar_ausentes", _normalizador_categorico()),
        ("imputer", SimpleImputer(strategy="constant", fill_value=valor_ausente)),
        ("onehot", OneHotPonderado()),
    ])
    return ColumnTransformer([("num", pipe_num, list(numericas)), ("cat", pipe_cat, list(categoricas))],
                             remainder="drop", sparse_threshold=1.0, verbose_feature_names_out=False)
```
2. Teste: acrescente ao **final** de `tests/test_features.py` (já importa `numpy as np`; duas linhas em branco antes):

```python
def test_preprocessador_clustering_ausente_explicito_e_esparso():
    import pandas as pd
    from scipy import sparse

    from src.features.normalization import construir_preprocessador_clustering

    df = pd.DataFrame({
        "idade": [10.0, 20.0, None, 40.0, 50.0, 60.0, 70.0, 80.0],
        "febre": ["1", "2", None, "9", "1", "2", None, "1"],
        "tosse": ["1", "1", "2", "2", None, "1", "2", "9"],
    })
    pre = construir_preprocessador_clustering(["idade"], ["febre", "tosse"])
    matriz = pre.fit_transform(df)
    nomes = list(pre.get_feature_names_out())
    assert sparse.issparse(matriz)
    assert any(n.startswith("febre_AUSENTE") for n in nomes) and any(n.startswith("tosse_AUSENTE") for n in nomes)
    # febre tem 4 categorias (1, 2, 9, AUSENTE): peso 1/2 em cada coluna dela
    colunas_febre = [i for i, n in enumerate(nomes) if n.startswith("febre_")]
    assert len(colunas_febre) == 4 and np.isclose(matriz[:, colunas_febre].max(), 0.5)
```
   Execute `.\.venv\Scripts\python.exe -m pytest tests/test_features.py -q`.

#### Etapa 2 · agrupamento (≈ 1 h 45, no B_06 ou numa seção nova no fim dele)
3. Leia o `train_ref` com `load_supervised_artifact(ROOT_DIR, expected_kind="final", partitions=("train_ref",))` (colunas: as 31 de `manifest["feature_columns"]` e `id_registro`); **amostra de 80 mil fichas** com `df.sample(80_000, random_state=42)` (ano e desfecho já estão balanceados pela partição-mestra). Nunca converta a matriz esparsa inteira para densa.
4. `X = construir_preprocessador_clustering(manifest["numeric_columns"], manifest["categorical_columns"]).fit_transform(amostra)`; depois `TruncatedSVD(n_components=40, random_state=42)` (se a variância acumulada `explained_variance_ratio_.sum()` passar de 0,90 com menos componentes, use o menor número que alcance 0,90 e registre).
5. **K-Means:** `MiniBatchKMeans(n_clusters=k, n_init=3, batch_size=4096, random_state=42)` para k de 2 a 6; silhueta em **10 mil** fichas da amostra (`silhouette_score(Xs[idx], rotulos[idx])`, `idx` fixo com semente 42); ARI entre três sementes (42, 43, 44) com `adjusted_rand_score`. Escolha o k pelo critério: maior silhueta; empate (diferença < 0,01) fica o menor k.
6. **HCA (Ward):** em **10 mil** fichas da amostra (o custo é quadrático): `Z = scipy.cluster.hierarchy.linkage(Xs[idx], method="ward")`. Dendrograma truncado: `dendrogram(Z, truncate_mode="lastp", p=30)`. Corte pelo **maior salto** (função testada):

```python
import numpy as np
from scipy.cluster.hierarchy import fcluster


def corte_maior_salto(Z, k_min=3, k_max=6):
    """k (entre k_min e k_max) cujo corte tem o maior salto de distância entre fusões."""
    n = Z.shape[0] + 1
    saltos = {k: float(Z[n - k, 2] - Z[n - k - 1, 2]) for k in range(k_min, k_max + 1)}
    k = max(saltos, key=saltos.get)
    return k, fcluster(Z, k, criterion="maxclust"), saltos
```
   `k_hca, rotulos_hca, saltos = corte_maior_salto(Z, 3, 6)`. Registre o k, os saltos e a silhueta. Para dar rótulo ao restante da amostra, ajuste um `KNeighborsClassifier(n_neighbors=15)` nas 10 mil e preveja as 70 mil; é só para o perfil.
7. **Perfil dos grupos** (substitui o `perfil_estatistico` do #137; define a função no notebook, sem arquivo novo):

```python
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, kruskal


def perfil_grupos(df: pd.DataFrame, rotulo: str, categoricas: list[str], numericas: list[str]) -> pd.DataFrame:
    """Uma linha por variável: tamanho do efeito do rótulo do grupo (V de Cramér ou η² por postos)."""
    linhas = []
    for col in categoricas:
        tabela = pd.crosstab(df[col].astype("string").fillna("AUSENTE"), df[rotulo])
        chi2 = chi2_contingency(tabela, correction=False)[0]
        menor = min(tabela.shape) - 1
        v = float(np.sqrt(chi2 / (tabela.values.sum() * menor))) if menor > 0 else float("nan")
        linhas.append({"variavel": col, "tipo": "categorica", "medida": "V_de_Cramer", "efeito": v})
    for col in numericas:
        partes = [g[col].dropna().to_numpy() for _, g in df.groupby(rotulo)]
        partes = [p for p in partes if p.size]
        n = sum(p.size for p in partes)
        h = float(kruskal(*partes)[0]) if len(partes) > 1 else float("nan")
        eta2 = max(0.0, (h - len(partes) + 1) / (n - len(partes))) if n > len(partes) else float("nan")
        linhas.append({"variavel": col, "tipo": "numerica", "medida": "eta2_Kruskal", "efeito": eta2})
    return pd.DataFrame(linhas).sort_values("efeito", ascending=False, ignore_index=True)
```
   Rode `perfil_grupos(amostra.assign(grupo_kmeans=rotulos_kmeans), "grupo_kmeans", manifest["categorical_columns"], manifest["numeric_columns"])` e o mesmo para o HCA. Grave `outputs/final/perfil_clusters_kmeans.csv` e `outputs/final/perfil_clusters_hca.csv`.
8. Grave também `outputs/tables/ns_onehot_metricas.csv` (k, silhueta, ARI entre sementes, saltos do HCA), `outputs/tables/ns_onehot_rotulos.parquet` (`id_registro`, rótulo K-Means, rótulo HCA da amostra) e a figura do dendrograma.
9. Escreva **duas frases** no notebook (vão para o relatório): (a) quais variáveis têm maior efeito (esperado: idade e preenchimento, ver #60); (b) os grupos descrevem **perfis de preenchimento e de idade, não perfis clínicos**.
10. Execute com `.\.venv\Scripts\python.exe tools/medir_notebook.py notebooks/B/B_06_eda_temporal_clustering.ipynb` (junto com a mudança do #51; uma só execução). Meta: ≤ 6 GB e ≤ 20 min; se passar de 6 GB, reduza a amostra para 50 mil e registre.
11. Commit: `feat: agrupamento com one-hot dos quatro estados [done:#136]`. Comente no #140 três linhas (k escolhido, V de Cramér/η² dos três maiores efeitos, se sugere variável derivada).

#### Pronto quando
Função e teste no `src`, rótulos das duas técnicas, perfil em CSV e o dendrograma com o corte justificado.

### ④ Pronto quando

- define: `src/features/normalization.py` :: `construir_preprocessador_clustering` | O pré-processador de clustering (one-hot esparso com AUSENTE explícito e peso 1/√k por variável) existe em src/features/normalization.py.
- teste: `tests/test_features.py` | Os testes de features passam (inclui o do pré-processador de clustering).
- existe: `outputs/tables/ns_onehot_metricas.csv` | As métricas do agrupamento (k, silhueta, ARI entre sementes, saltos do HCA) estão em outputs/tables/ns_onehot_metricas.csv.
- existe: `outputs/tables/ns_onehot_rotulos.parquet` | Os rótulos do K-Means e do HCA (com id_registro) estão em outputs/tables/ns_onehot_rotulos.parquet.
- existe: `outputs/final/perfil_clusters_kmeans.csv` | O perfil estatístico dos grupos do K-Means está em outputs/final/perfil_clusters_kmeans.csv.
- existe: `outputs/final/perfil_clusters_hca.csv` | O perfil estatístico dos grupos do HCA está em outputs/final/perfil_clusters_hca.csv.
- manual: | As duas frases do relatório (variáveis de maior efeito; grupos descrevem preenchimento e idade, não perfis clínicos) e o corte do dendrograma estão escritos no notebook e comentados no #140.

## #137 · ANOVA no perfil dos grupos do agrupamento (pedido do professor), com Kruskal-Wallis como conferência

- prioridade: P2
- situação: parcial
- estratégia: desenvolver
- marco: M3
- data ideal: 03/11
- responsável: Pessoa B (0,25 h)
- pessoas: B
- fonte: Orientação de 24/10 (ANOVA para numéricas, qui-quadrado para qualitativas); B_04 no commit 863dd45; alinhamento de 03/11
- depende de: —
- tags: Não supervisionado, Estatística, Notebook
- pilar: Valor científico-acadêmico
- carga: 0.25
- novo: não
- professores: sim
- arquivos: notebooks/B/B_04_eda_temporal_clustering.ipynb

### ① Para entender

Na orientação de 24/10, o professor pediu para descrever em que os grupos do agrupamento diferem: **ANOVA** para as variáveis numéricas (idade, dias até a internação) e **qui-quadrado** para as qualitativas.

| Teste | Para | Tamanho do efeito |
|---|---|---|
| Qui-quadrado | qualitativas | V de Cramér (0,1 pequeno; 0,3 médio; 0,5 grande) |
| ANOVA de um fator | numéricas | η² (0,01 pequeno; 0,06 médio; 0,14 grande) |
| Kruskal-Wallis | numéricas, conferência | η² por postos (não supõe normalidade) |

Com 80 mil fichas, quase todo p-valor sai abaixo de 0,05: a leitura é pelo tamanho do efeito.

### ② Problema

> [!decisão] Estado em 03/11
> A ANOVA **já está no código** do B_04 (a função `ns_perfil_grupos` usa `f_oneway` e grava η² da ANOVA, com Kruskal-Wallis como conferência) e a §29.7 do decisoes.md já descreve isso. Falta o texto do notebook e a execução.

- O Markdown `agrupamento-01` do B_04 ainda diz "η² por postos nas numéricas": corrigido no **#159** (passo 2).
- A saída salva da célula é a antiga: o B_04 roda na execução limpa (**#126**).
- A tabela das 10 variáveis de maior efeito vai para o relatório (**#133**), depois do #126.

### ③ O que fazer

**Dono:** Pessoa B · **Prazo:** o texto em 03/11 (#159); a tabela depois do #126

1. Texto do Markdown: faça o passo 2 do #159.
2. Execução: faz parte do #126 (o B_04 leva cerca de 5 minutos).
3. Depois do #126, leve para o relatório (#133) a tabela das 10 variáveis de maior efeito, com V de Cramér ou η², e a leitura "os grupos descrevem idade e preenchimento, não perfis clínicos".

### ④ Pronto quando

- contem: `notebooks/B/B_04_eda_temporal_clustering.ipynb` :: `f_oneway` | O B_04 calcula a ANOVA de um fator no perfil dos grupos.
- contem: `notebooks/B/B_04_eda_temporal_clustering.ipynb` :: `eta2_ANOVA` | O perfil registra o η² da ANOVA como tamanho do efeito das numéricas.
- contem: `docs/decisoes.md` :: `ANOVA (η²)` | A §29.7 descreve o que o código faz (qui-quadrado e ANOVA, com Kruskal-Wallis como conferência).
- manual: | Depois da execução limpa (#126), a tabela das variáveis de maior efeito está no relatório.

## #112 · Revisão bibliográfica dirigida: SIVEP-Gripe, teste temporal e separação treino/validação/teste

- prioridade: P2
- situação: aberta
- estratégia: documentar
- marco: M7
- data ideal: 04/11
- responsável: Pessoa B (1 h)
- pessoas: B
- fonte: Revisão de 03/11 (referências levantadas em 03/11)
- depende de: —
- tags: Relatório, Literatura
- pilar: Valor científico-acadêmico
- carga: 1
- novo: não
- professores: sim

### ① Para entender

A introdução e a defesa do desenho ficam mais fortes com poucos trabalhos do mesmo tema (previsão de óbito por SRAG/COVID com dados do SIVEP-Gripe) e duas ou três referências metodológicas para a separação treino/validação/teste e a calibração.

### ② Problema

Cada referência precisa ser conferida no texto completo antes de citar um número ou uma afirmação; até aqui só foram lidos resumos.

### ③ O que fazer

**Dono:** Pessoa B · **Prazo:** 04/11 · **Começa quando:** já

1. Do tema (conferir o método de cada um no texto completo): Chen et al., 2025, *BMC Medical Research Methodology* (efeito da temporalidade em modelos de mortalidade com dados brasileiros: sustenta o Teste B); Lages dos Santos et al., 2025, *PeerJ Computer Science* (12 modelos de mortalidade pediátrica no SIVEP-Gripe); Passarelli-Araujo et al., 2022, *Smart Health* (logística, SVM, random forest e XGBoost no SIVEP-Gripe); Bottino et al., 2021, *J Pers Med* (revisão sistemática); Portal de Dados Abertos do SUS (fonte dos dados).
2. Método (citar só para o princípio): Hastie, Tibshirani e Friedman, 2009, cap. 7; Cawley e Talbot, 2010, *JMLR*; Niculescu-Mizil e Caruana, 2005, ICML (calibração); Collins et al., 2015, TRIPOD.
3. Um parágrafo de introdução e uma tabela curta (trabalho, dados, modelos, métrica, se tem teste temporal) para o relatório. Commit ou envio ao A: `docs: revisão bibliográfica [done:#112]`.

### ④ Pronto quando

- manual: | A revisão (parágrafo e tabela) está no relatório, com as referências conferidas no texto completo.

## #96 · Atualizar os guias e a base de conhecimento do agente

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 05/11
- responsável: Pessoa B (dona; revisão cruzada sem edição concorrente)
- pessoas: B
- fonte: Guia_Mestre_SRAG_PessoaB_Consolidado.html; Guia_Rapido_SRAG_15min.html; SRAG_Base_Conhecimento_Completa.docx; README
- depende de: —
- tags: Documentação
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: —
- novo: não
- professores: não
- removido: removido na revisão de 03/11 (v3.2): guias e base de conhecimento são internos; o README da entrega está no #126

### ① Para entender

Os guias usam os nomes antigos dos notebooks ("Notebook 03" em vez de `B_07`). A base de conhecimento do agente diz que as correções de `pipeline.py` e `boosting.py` foram aplicadas, mas elas não estão no repositório (itens 4 e 17).

> [!atenção] Atenção
> Um agente treinado com a base atual vai afirmar que o pré-processamento é esparso. Isso é falso no commit `8e52d8a`.

### ② Problema

Documentos afetados: Guia Mestre (commit `cab78e8`, nomes 01–04), Guia Rápido, base de conhecimento (Parte 2 marca os itens 8 e 9 como "aplicado") e README (cita `dicionario_variaveis_v1_revisao.csv`).

### ③ O que fazer

Base de conhecimento atualizada para a **v9** em 24/10 (documento único para IAs, sem anexos históricos). Antes de 03/11, só o README (Pessoa A, 02/11, junto com o #126). Guias e base: atualizar depois da entrega com os resultados finais.

### ④ Pronto quando

- manual: | (Pós-entrega) Guias e base de conhecimento atualizados com os resultados finais; antes de 03/11, só o README (no #126).

## #130 · Regerar a referência do projeto ao fim de cada marco

- prioridade: P3
- situação: aberta
- estratégia: desenvolver
- marco: M6
- data ideal: 04/11
- responsável: Pessoa A (dentro do #147)
- pessoas: A
- fonte: tools/update_project_reference.py (v6)
- depende de: #147
- tags: Documentação, Ambiente
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 0
- novo: sim
- professores: não
- removido: absorvido pelo #147 em 03/11 (referência regerada no congelamento)

### ① Para entender

> [!atenção] Inclui checkpoint Git
> Antes de cada marco: `git status`, commit do estado verde e geração da referência v6. Isso impede que outra IA leia alterações locais sem saber o que foi testado.

A referência é o "manual vivo" que impede outra IA (ou outro integrante) de criar funções repetidas. Ela só vale até o momento em que foi gerada.

### ② Problema

> [!atenção] Replanejamento de 31/10 · versão 2 (entrega em 04/11)
> Uma regeração só, **dentro do #147** (04/11). Sem esforço próprio.

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que esta pendência está aberta
> A auditoria automática do painel (27/10, 14:40) marcou este item como resolvido com base em commits de 10 e 11/10, todos anteriores às revisões de 24 e 26/10 e sem relação com a entrega descrita aqui. Isso acontece por um defeito do painel: a cada auditoria, um commit antigo ainda não rejeitado reabre a sugestão (detalhes no #94).
> É rotina contínua. A referência foi regerada em 27/10 (19:22) e 28/10 (02:45), mas o card só fecha em 02/11, depois do último marco.

Alterações feitas depois da geração não aparecem; buffers não salvos nunca aparecem.

### ③ O que fazer

**Pessoa A, dentro do #147 (04/11):** `git pull`; `.\.venv\Scripts\python.exe tools/update_project_reference.py --run-tests --pytest-args="-m 'not slow'"`; confira: nenhum erro de leitura, testes passando, nenhum código ignorado pelo Git. Ela não vai para o pacote.

### ④ Pronto quando

- existe: `docs/PROJECT_COMPLETE_REFERENCE.txt` | A referência do projeto existe em docs/.
- manual: | A referência foi regerada nos marcos de 28/10, 30/10 e 02/11, com testes rodando e sem código ignorado pelo Git; cada geração foi avisada neste card com data e commit. O painel avisa em REVISÕES quando a referência está desatualizada.

## #53 · Exploração opcional: validar o modelo congelado em 2026

- prioridade: P4
- situação: parcial
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 05/11
- responsável: Pessoa B (dona; revisão cruzada sem edição concorrente)
- pessoas: B
- fonte: src/evaluation/temporal.py; Projeto
- depende de: #2
- tags: Metodologia, Partição
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: —
- novo: não
- professores: não
- removido: removido na revisão de 03/11 (v3.2): 2026 está fora do protocolo (exploracao_2026.ativa: false); trabalho futuro no #133

### ① Para entender

> [!atenção] Só depois de todo o projeto concluído
> 2026 não entra em treino, validações, Teste A ou Teste B. Se tudo estiver fechado e revisado, o modelo congelado pode ser aplicado a 2026 como exploração de transportabilidade para um período parcial.

O resultado deve ser apresentado separadamente, com alerta de maturidade do desfecho e cobertura incompleta.

### ② Problema

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: **cortado do escopo da entrega** (2026 é ano parcial e exploratório; nada na banca depende disso). Só se alguém sobrar, depois de 05/11.

2026 é parcial e tem desfechos ainda pendentes. Misturá-lo aos testes principais criaria uma comparação injusta e potencialmente enviesada.

### ③ O que fazer

Fora da entrega de 04/11. Se, **depois de 05/11**, houver interesse: carregar `exploracao` com `temporal.exploracao_2026.ativa: true`, aplicar o modelo congelado sem recalibrar nem mudar o corte e reportar com o rótulo "exploratório, ano parcial". O relatório já declara 2026 como parcial e exploratório.

### ④ Pronto quando

- existe: `outputs/final/exploracao_2026_metricas.csv` | (Opcional) As métricas do modelo congelado em 2026, com o rótulo "exploratório, ano parcial", estão em outputs/final/exploracao_2026_metricas.csv.
- manual: | Só foi feito depois de 01/11 e com o relatório completo; o modelo não foi recalibrado nem o corte mudou.

## #11 · A sensibilidade de indicadores de ausência não existe no código

- prioridade: P4
- situação: aberta
- estratégia: documentar
- marco: M1
- data ideal: 01/11
- responsável: Pessoa A (dona; revisão cruzada sem edição concorrente)
- pessoas: A
- fonte: configs/supervised.yaml (features.sensibilidade_indicadores_ausencia, missingness.indicadores_ausencia, sensibilidades.com_sem_indicadores_ausencia); src/models/pipeline.py
- depende de: #73
- tags: Diverge do decidido, Código, Metodologia, Features
- pilar: —
- carga: 0
- novo: não
- professores: não

### ① Para entender

> [!decisão] Decisão de 18/10
> Prioridade anterior: P2. Rebaixada para P4 em 18/10.

O YAML liga uma análise "com e sem indicadores de ausência", mas nenhum código cria essas colunas. E, como o branco já vira `AUSENTE`, o modelo principal já recebe essa informação. Depende do item 83 dizer o que comparar.

### ② Problema

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que esta pendência está aberta
> A auditoria automática do painel (27/10, 14:40) marcou este item como resolvido com base em commits de 09 e 11/10, todos anteriores às revisões de 24 e 26/10 e sem relação com a entrega descrita aqui. Isso acontece por um defeito do painel: a cada auditoria, um commit antigo ainda não rejeitado reabre a sugestão (detalhes no #94).
> Continuam ligadas sem nenhum código que as use: `features.sensibilidade_indicadores_ausencia.ativa: true`, `sensibilidades.com_sem_indicadores_ausencia.ativa: true` e `missingness.indicadores_ausencia.sensibilidade: true`. Fecha junto com o #73.

O YAML ativa uma sensibilidade com indicadores de ausência (prefixo `missingindicator_`), mas nenhum código cria essas colunas. Além disso, o pré-processador já imputa as categóricas vazias como a categoria `AUSENTE`, o que dá ao modelo principal a mesma informação. Na prática, a comparação "com e sem indicadores" não existe.

### ③ O que fazer

> [!decisão] Enxugado em 27/10 (eficiência primeiro)
> Feito dentro do **#73** (Pessoa A). Marque como concluído junto com ele.

### ④ Pronto quando

- yaml: `configs/supervised.yaml` :: `features.sensibilidade_indicadores_ausencia.ativa` = `false` | A sensibilidade de indicadores de ausência, sem código que a implemente, foi desligada no YAML.
- yaml: `configs/supervised.yaml` :: `sensibilidades.com_sem_indicadores_ausencia.ativa` = `false` | A comparação "com e sem indicadores" foi desligada no YAML.
- yaml: `configs/supervised.yaml` :: `missingness.indicadores_ausencia.sensibilidade` = `false` | O bloco missingness também deixou de prometer a sensibilidade.

## #24 · Curvas de calibração calculadas de dois jeitos

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 05/11
- responsável: C
- pessoas: C
- fonte: src/evaluation/calibration.py; B_07_supervisionado_pilotos
- depende de: —
- tags: Código, Calibração
- pilar: —
- carga: —
- novo: não
- professores: não
- removido: removido na revisão de 03/11 (v3.2): não afeta a entrega; o C_15 usa uma só função de curva de calibração (curva_confiabilidade)

### ① Para entender

> [!decisão] Decisão de 18/10
> Prioridade anterior: P3. Rebaixada para P4 em 18/10.

O `src` divide as probabilidades em faixas de largura igual (0–10%, 10–20%…); o B_07 usou faixas com o mesmo número de casos. Com probabilidades concentradas, as curvas ficam diferentes.

### ② Problema

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que esta pendência está aberta
> A auditoria automática do painel (27/10, 14:40) marcou este item como resolvido com base em commits de 18 e 19/10, todos anteriores às revisões de 24 e 26/10 e sem relação com a entrega descrita aqui. Isso acontece por um defeito do painel: a cada auditoria, um commit antigo ainda não rejeitado reabre a sugestão (detalhes no #94).
> `src/evaluation/calibration.py` não mudou (curva por faixas iguais). Continua pós-entrega.

A curva de confiabilidade de `src/evaluation` usa faixas de largura igual. O B_07 usou faixas por quantis. Com probabilidades concentradas em poucos valores, as duas estratégias dão curvas visivelmente diferentes.

### ③ O que fazer

**Pós-entrega para a função**, mas com um cuidado já na avaliação final: no C_16 (#119), gerar as curvas de calibração com `sklearn.calibration.calibration_curve(..., strategy="quantile", n_bins=10)` diretamente, para que as figuras do relatório sejam coerentes com o ECE por quantis do #79. Depois da entrega, acrescentar o parâmetro `strategy` à função de `src/evaluation`.

**Como fazer, quando for a hora (instruções anteriores mantidas):**

Acrescentar o parâmetro `strategy` (`"uniform"` ou `"quantile"`), repassado a `calibration_curve`, e padronizar `"quantile"` no projeto, como no B_07.

### ④ Pronto quando

- contem: `src/evaluation/calibration.py` :: `strategy` | (Pós-entrega) A curva de confiabilidade do src aceita o parâmetro strategy (uniform ou quantile), com quantile como padrão do projeto.
- contem: `notebooks/C/C_16_validacao_final.ipynb` :: `strategy="quantile"` | As curvas de calibração do relatório usam faixas por quantis (strategy="quantile", 10 faixas), coerentes com o ECE do #79.

## #25 · A checagem de vazamento só olha o nome das colunas

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 05/11
- responsável: C
- pessoas: C
- fonte: src/evaluation/leakage.py (check_leakage)
- depende de: —
- tags: Código, Vazamento
- pilar: —
- carga: —
- novo: não
- professores: não
- removido: removido na revisão de 03/11 (v3.2): a frase de limitação está no #133; o notebook A_08 citado não existe mais

### ① Para entender

> [!decisão] Decisão de 18/10
> Prioridade anterior: P3. Rebaixada para P4 em 18/10.

`check_leakage` compara nomes com a lista de proibidas. Uma coluna derivada de uma proibida, com outro nome, passa. O A_08 complementa com uma varredura de AUC univariada (nenhuma variável acima de 0,9).

### ② Problema

`check_leakage` só compara nomes de colunas com a lista de proibidas. Colunas derivadas de variáveis proibidas, com outro nome, não são detectadas.

### ③ O que fazer

Pós-entrega. **Para o relatório (Pessoa A, limitações):** “a verificação automática de vazamento compara nomes de colunas com a lista proibida; a proteção principal é o contrato de features congelado (G1) e a revisão humana da temporalidade de cada variável”.

**Como fazer, quando for a hora (instruções anteriores mantidas):**

Documentar a limitação na docstring e no relatório. Se houver tempo, acrescentar uma checagem de prefixos (por exemplo, colunas que começam com `dt_evoluca`, `uti`, `evolucao`).

### ④ Pronto quando

- manual: | (Pós-entrega) A limitação da checagem de vazamento por nome de coluna está documentada na docstring de check_leakage e nas limitações do relatório.

## #31 · configs/paths.local.json aponta para uma pasta que ninguém usa

- prioridade: P3
- situação: aberta
- estratégia: desenvolver
- marco: M6
- data ideal: 27/10
- responsável: Pessoa A (dona; revisão cruzada sem edição concorrente)
- pessoas: A
- fonte: configs/paths.local.json
- depende de: —
- tags: Ambiente, Git
- pilar: —
- carga: 1
- novo: não
- professores: não

### ① Para entender

> [!decisão] Decisão de 18/10
> Prioridade anterior: P3. Rebaixada para P4 em 18/10.

O arquivo aponta para `data/raw/`, mas os dados ficam em `data/processed/dados-v2/`. Nenhum código o lê, e ele está no `.gitignore` (alerta A6).

### ② Problema

O arquivo aponta para `data/raw/`, mas o `storage` lê o Parquet de `data/processed/dados-v2/`. Ninguém usa o arquivo, e ele pode confundir quem chega ao projeto.

### ③ O que fazer

**Pessoa A, 2 minutos.** Apague `configs/paths.local.json` (nenhum código o lê). É o único alerta alto da referência do projeto (A1) e some na próxima geração (#130).

### ④ Pronto quando

- nao-existe: `configs/paths.local.json` | O arquivo configs/paths.local.json, que ninguém lê e aponta para data/raw/, foi apagado (é local e ignorado pelo Git: confira na sua máquina).

## #32 · Textos antigos no código (dt_notific, nomes de gates)

- prioridade: P4
- situação: parcial
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 05/11
- responsável: C
- pessoas: C
- fonte: src/utils/config.py; src/utils/reproducibility.py; src/evaluation/temporal.py; src/data/supervised_artifact.py
- depende de: —
- tags: Código, Documentação
- pilar: —
- carga: —
- novo: não
- professores: não
- removido: removido na revisão de 03/11 (v3.2): docstrings sem efeito nos resultados; o dt_notific restante está no código legado do #154

### ① Para entender

> [!decisão] Decisão de 18/10
> Prioridade anterior: P3. Rebaixada para P4 em 18/10.

Algumas docstrings ainda falam em "split temporal por `dt_notific`" e em `TemporalSplit`. A referência a `G7_limiar` no `config.py` já foi corrigida.

### ② Problema

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que esta pendência está aberta
> A auditoria automática do painel (27/10, 14:40) marcou este item como resolvido com base em commits de 09 e 10/10, todos anteriores às revisões de 24 e 26/10 e sem relação com a entrega descrita aqui. Isso acontece por um defeito do painel: a cada auditoria, um commit antigo ainda não rejeitado reabre a sugestão (detalhes no #94).
> `src/evaluation/temporal.py` ainda tem o exemplo `TemporalSplit(df, coluna_tempo="dt_notific")` na docstring. Continua pós-entrega.

Há textos desatualizados: o `config.py` cita `C.exigir_gate("G7_limiar")` e "holdout antes de G7" (os gates atuais são G8_limiar e G9_holdout); o `reproducibility.py` dá como exemplo "split temporal por dt_notific"; o `temporal.py` usa `dt_notific` como coluna de tempo; a docstring de `holdout_partition` cita `TemporalSplit`.

### ③ O que fazer

Pós-entrega. Não afeta resultados. Se alguém tocar nesses arquivos por outro motivo, corrige junto.

**Como fazer, quando for a hora (instruções anteriores mantidas):**

Atualizar os exemplos e docstrings para `G8_limiar`, `G9_holdout`, `dt_interna` e divisão aleatória estratificada. Indicar no topo do `temporal.py` que ele serve apenas à sensibilidade temporal.

### ④ Pronto quando

- nao-contem: `src/evaluation/temporal.py` :: `coluna_tempo="dt_notific"` | (Pós-entrega) O exemplo da docstring de temporal.py não usa mais dt_notific como coluna de tempo.

## #33 · normalization.py está vazio

- prioridade: P4
- situação: resolvida
- estratégia: resolvida
- marco: Pós-entrega
- data ideal: Concluído
- responsável: C
- pessoas: C
- fonte: src/features/normalization.py; src/features/__init__.py
- depende de: #136
- tags: Código
- pilar: —
- carga: —
- novo: não
- professores: não

### ① Para entender

O arquivo `src/features/normalization.py` tem 0 bytes. As exportações de `sexo_categoria` e `ano_mes_internacao` no `__init__` já existem.

### ② Problema

Na revisão anterior, `normalization.py` estava vazio, e `sexo_categoria` e `ano_mes_internacao` não eram exportadas no `__init__` (os testes as importam direto de `engineering`). Não recebi a versão atual desses arquivos.

### ③ O que fazer

> [!ok] Mudou de papel (24/10)
> `src/features/normalization.py` deixa de ser candidato a remoção: passa a receber a função `construir_preprocessador_clustering` do #136. Não apagar.

### ④ Pronto quando

- existe: `src/features/normalization.py` | O arquivo src/features/normalization.py continua no repositório (não foi apagado), porque passou a ter um papel: receberá construir_preprocessador_clustering no #136. Que ele tenha conteúdo é conferido no #136.

## #35 · Notebooks B recalculam com código próprio o que já existe em src/

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 05/11
- responsável: B
- pessoas: B
- fonte: B_06_eda_temporal_clustering; B_07_supervisionado_pilotos
- depende de: —
- tags: Notebook, Código
- pilar: —
- carga: —
- novo: não
- professores: não
- removido: removido na revisão de 03/11 (v3.3): resolvido; os antigos B_06 e B_07 viraram B_04 e B_05, e ambos já usam o src (montar_features, build_preprocessor e os construtores de pipeline)

### ① Para entender

> [!decisão] Decisão de 18/10
> Não refatorar notebooks B agora. Regra para código novo: usar sempre o `src` (a referência v6 mostra o que já existe). Prioridade anterior: P2. Rebaixada para P4 em 18/10.

O B_06 e o B_07 têm funções próprias para idade, sexo, pipelines e métricas (30 e 7 funções locais, segundo o relatório automático). Se o código central mudar, os notebooks vão continuar calculando do jeito antigo, sem aviso.

> [!exemplo] Exemplo
> Duas receitas do mesmo bolo, em cadernos diferentes. Alguém corrige o açúcar num caderno e o outro continua errado.

### ② Problema

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que esta pendência está aberta
> A auditoria automática (27/10, 14:40) marcou "precisa revisão" por achados que não tratam deste item: a linha decorativa `=====` no cabeçalho de `src/protocolo/verificacoes.py` (lida como conflito de merge) e o `OneHotEncoder` denso do B_06, que roda numa amostra de 80 mil fichas e será substituído pelo #136 (detalhes no #94).
> O B_07 ainda tem pipelines e métricas próprios. Continua pós-entrega.

Os B_06 e B_07 calculam idade, sexo, pipelines e métricas com código próprio, duplicando o que existe em `src/` (`montar_features`, `build_*`, `src/evaluation`). Quando o código central mudar, os notebooks vão produzir números diferentes sem aviso.

### ③ O que fazer

Pós-entrega. Com o B_07 histórico e o B_06 usando o artefato v3 para faixa e sexo (#36), o risco de números divergentes na entrega fica controlado.

**Como fazer, quando for a hora (instruções anteriores mantidas):**

No B_06, trocar as derivações próprias por `montar_features`. No B_07, trocar os pipelines escritos à mão por `build_baseline_pipeline` e `build_logistic_pipeline`, e as métricas por `metricas_completas`. Remover as funções duplicadas e conferir que os números batem com os anteriores (ou explicar a diferença).

### ④ Pronto quando

- manual: | (Pós-entrega) Os B_06 e B_07 usam as funções do src (montar_features, build_*_pipeline, metricas_completas) no lugar das funções locais duplicadas, e os números batem com os anteriores (ou a diferença foi explicada).

## #39 · Matriz de transição do B_10 com status escritos à mão

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 05/11
- responsável: B
- pessoas: B
- fonte: B_10_consolidacao_shortlist_transicao_coorte
- depende de: —
- tags: Notebook
- pilar: —
- carga: —
- novo: não
- professores: não
- removido: obsoleto em 03/11: o notebook B_10 não existe mais

### ① Para entender

> [!decisão] Decisão de 18/10
> Prioridade anterior: P3. Rebaixada para P4 em 18/10.

Em 4 dos 6 itens, o "pronto para seguir" foi digitado, não verificado. O texto de abertura também cita `cohort_source`, mas o código usa `load_supervised_artifact`.

### ② Problema

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Obsoleto para a entrega: o B_10 sai do pacote no #143.

Na matriz de transição do B_10, o status "pronto para seguir" está escrito à mão em 4 dos 6 itens, em vez de vir de verificações. O texto de abertura cita `cohort_source`, mas o código usa `load_supervised_artifact`.

### ③ O que fazer

Pós-entrega. O B_10 é histórico (#37).

**Como fazer, quando for a hora (instruções anteriores mantidas):**

Calcular cada status a partir de uma verificação real (por exemplo, existência do artefato, gate aprovado, lista preenchida). Corrigir o texto de abertura.

### ④ Pronto quando

- manual: | (Pós-entrega) Os status da matriz de transição do B_10 vêm de verificações reais, ou o B_10 foi removido no #143.

## #41 · "provisoria", "provisorio" e "provisional" misturados

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 05/11
- responsável: B + C
- pessoas: B, C
- fonte: Projeto (nomes de arquivos e de status)
- depende de: —
- tags: Documentação, Código
- pilar: —
- carga: —
- novo: não
- professores: não
- removido: absorvido pelo #152 em 03/11 (a coorte provisória foi aposentada; os nomes restantes são histórico ou código do #154)

### ① Para entender

> [!decisão] Decisão de 18/10
> Prioridade anterior: P3. Rebaixada para P4 em 18/10.

Nomes de arquivos e status usam três grafias. Isso atrapalha buscas e filtros automáticos (ex.: `cohort_kind="provisional"` contra `coorte_provisoria_b.parquet`).

### ② Problema

Os nomes de arquivos e valores de status misturam "provisoria", "provisorio" e "provisional" (por exemplo, `coorte_provisoria_b.parquet`, `supervisionado_..._split_provisorio.csv` e `cohort_kind="provisional"`).

### ③ O que fazer

Pós-entrega. Para os **novos** artefatos desta semana: `final` nos valores internos e português nos nomes de arquivos (ex.: `cohort_kind="final"`).

**Como fazer, quando for a hora (instruções anteriores mantidas):**

Escolher um padrão (por exemplo, `provisional` e `final` para valores internos, e português nos nomes de arquivos) e aplicar nos próximos artefatos. Não renomear arquivos já citados em manifestos sem atualizar os manifestos.

### ④ Pronto quando

- manual: | (Pós-entrega) Um padrão único foi escolhido (provisional/final nos valores internos, português nos nomes de arquivos) e aplicado aos artefatos novos, sem renomear arquivos já citados em manifestos.

## #42 · Cada notebook encontra a pasta do projeto de um jeito

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 05/11
- responsável: B + C
- pessoas: B, C
- fonte: Notebooks (célula de localização da raiz)
- depende de: —
- tags: Notebook, Ambiente
- pilar: —
- carga: —
- novo: não
- professores: não
- removido: removido na revisão de 03/11 (v3.2): cosmético, sem efeito na entrega

### ① Para entender

Uns procuram `src` e `configs`, outros `src` e `pyproject.toml`, os da Pessoa A procuram `src/protocolo`. Uma função comum em `src/utils/env.py` resolveria.

### ② Problema

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Pós-entrega. O padrão mínimo (a mesma segunda célula, que acha a raiz do projeto, em todos os notebooks) já entra no #146; a função comum em `src/utils/paths.py` fica para depois.

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que esta pendência está aberta
> A auditoria automática (27/10, 14:40) marcou "precisa revisão" por achados que não tratam deste item: a linha decorativa `=====` no cabeçalho de `src/protocolo/verificacoes.py` (lida como conflito de merge) e o `OneHotEncoder` denso do B_06, que roda numa amostra de 80 mil fichas e será substituído pelo #136 (detalhes no #94).
> Não existe `src/utils/paths.py`; cada notebook acha a raiz do seu jeito. Continua pós-entrega.

Cada notebook encontra a raiz do projeto de um jeito: procurando `src` e `configs`, `src` e `pyproject`, ou pelo nome da pasta atual.

### ③ O que fazer

Pós-entrega.

**Como fazer, quando for a hora (instruções anteriores mantidas):**

Criar `src/utils/paths.py` com uma função `encontrar_raiz()` e usá-la em todos os notebooks. Como a função precisa existir antes do import, manter no notebook apenas um bloco mínimo que adicione a raiz ao `sys.path`.

### ④ Pronto quando

- define: `src/utils/paths.py` :: `encontrar_raiz` | (Pós-entrega) Existe src/utils/paths.py com a função encontrar_raiz(), usada por todos os notebooks.

## #43 · Arquivos e listas que ninguém usa (preprocessor.joblib, lista de coortes no B_06)

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 05/11
- responsável: B + C
- pessoas: B, C
- fonte: notebooks C_11; B_06_eda_temporal_clustering
- depende de: —
- tags: Notebook
- pilar: —
- carga: —
- novo: não
- professores: não
- removido: absorvido pelo #152 em 03/11

### ① Para entender

O C_11 salva `preprocessor.joblib`, que nenhum passo seguinte lê. O B_06 tem uma lista própria de coortes candidatas, que conflita com `cohort_source`.

### ② Problema

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Pós-entrega. O C_11 do #132 remove a variável `pipeline_path` (`preprocessor.joblib`, que só aparecia numa mensagem impressa; item 3 do #132). A lista própria de coortes do B_06 fica para depois.

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que esta pendência está aberta
> A auditoria automática (27/10, 14:40) marcou "precisa revisão" por achados que não tratam deste item: a linha decorativa `=====` no cabeçalho de `src/protocolo/verificacoes.py` (lida como conflito de merge) e o `OneHotEncoder` denso do B_06, que roda numa amostra de 80 mil fichas e será substituído pelo #136 (detalhes no #94).
> Metade resolvida: o B_06 passou a usar `resolve_cohort_path` (sem lista própria de coortes). Falta só o C_11, que ainda grava `preprocessor.joblib` e `preprocessor_ajustado.joblib` sem ninguém usar. Continua pós-entrega (ou some no #132).

O C_11 salva `preprocessor.joblib`, que nenhum passo seguinte usa. O B_06 tem uma lista própria de coortes candidatas, que conflita com `cohort_source`.

### ③ O que fazer

Pós-entrega. O C_11 do #132 pode simplesmente não salvar o `preprocessor.joblib`, se for mais simples do que manter.

**Como fazer, quando for a hora (instruções anteriores mantidas):**

Remover o salvamento do `preprocessor.joblib` (ou passar a usá-lo). No B_06, trocar a lista própria por `load_cohort`.

### ④ Pronto quando

- nao-contem: `notebooks/C/C_11_pipeline_supervisionado.ipynb` :: `preprocessor.joblib` | (Pós-entrega, ou dentro do #132) O C_11 não salva mais o preprocessor.joblib que ninguém lê.

## #48 · 41 fichas com povo tradicional preenchido sem a pessoa ser de povo tradicional

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 05/11
- responsável: A
- pessoas: A
- fonte: Construção da coorte
- depende de: —
- tags: Dados/Coorte
- pilar: —
- carga: —
- novo: não
- professores: não
- removido: removido na revisão de 03/11 (v3.2): tp_pov_ct não é variável do modelo

### ① Para entender

> [!decisão] Decisão de 18/10
> Prioridade anterior: P2. Rebaixada para P4 em 18/10.

É um campo condicional: só deveria estar preenchido se a pessoa respondeu "sim" na pergunta anterior. É pouco, mas precisa de regra e registro.

### ② Problema

41 fichas têm o tipo de povo tradicional preenchido sem que a pessoa tenha declarado pertencer a um povo tradicional.

### ③ O que fazer

Pós-entrega. `tp_pov_ct` não está em nenhum conjunto de features do G1.

**Como fazer, quando for a hora (instruções anteriores mantidas):**

Investigar e decidir se o campo é tratado como ausente nesses casos. Registrar a regra.

### ④ Pronto quando

- manual: | (Pós-entrega) A regra para as 41 fichas com povo tradicional preenchido sem pertencimento declarado foi decidida e registrada.

## #49 · Códigos a confirmar no dicionário

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 05/11
- responsável: A
- pessoas: A
- fonte: configs/dicionario_variaveis_v1.csv
- depende de: —
- tags: Dados/Coorte, Documentação
- pilar: —
- carga: —
- novo: não
- professores: não
- removido: absorvido pelo #70 em 03/11 (v3.2): os dois códigos são confirmados no dicionário das variáveis do modelo

### ① Para entender

> [!decisão] Decisão de 18/10
> Prioridade anterior: P2. Rebaixada para P4 em 18/10.

`ave_suino = 3` (outro animal), `cs_raca = 5` (indígena) e o código do Brasil em `co_pais` ainda não foram confirmados na ficha oficial.

### ② Problema

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que esta pendência está aberta
> A auditoria automática do painel (27/10, 14:40) marcou este item como resolvido com base em commits de 10 e 11/10, todos anteriores às revisões de 24 e 26/10 e sem relação com a entrega descrita aqui. Isso acontece por um defeito do painel: a cada auditoria, um commit antigo ainda não rejeitado reabre a sugestão (detalhes no #94).
> Nenhuma confirmação registrada. Continua pós-entrega.

Faltam confirmar códigos: `ave_suino` = 3 (outro animal), `cs_raca` = 5 (indígena) e o código do Brasil em `co_pais`.

### ③ O que fazer

Pós-entrega. `ave_suino`, `cs_raca` e `co_pais`: só `ave_suino` e `cs_raca` estão no modelo principal; seus códigos já seguem o dicionário da ficha, e a confirmação formal entra no apêndice se houver tempo.

**Como fazer, quando for a hora (instruções anteriores mantidas):**

Conferir no dicionário oficial do SIVEP-Gripe e registrar a confirmação no dicionário de variáveis.

### ④ Pronto quando

- manual: | (Pós-entrega) Os códigos ave_suino = 3, cs_raca = 5 e o código do Brasil em co_pais foram conferidos no dicionário oficial do SIVEP-Gripe e registrados no dicionário de variáveis.

## #50 · Três sintomas vazios em 2019: estudar o "marcador de ano" e decidir se ficam no modelo

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M3
- data ideal: 01/11
- responsável: Pessoa A (dados) + Pessoa C (ablação)
- pessoas: A, C
- fonte: configs/dicionario_variaveis_v1.csv
- depende de: #54, #140
- tags: Features, Vazamento, Metodologia, Dados/Coorte
- pilar: —
- carga: 2
- novo: não
- professores: não
- removido: absorvido pelo #140 em 03/11: os três sintomas saíram do modelo por decisão de validade (§29.34)

### ① Para entender

Perda de olfato, perda de paladar e fadiga só passaram a existir na ficha com a COVID-19. Em 2019 esses campos vêm quase sempre em branco, e o modelo transforma o branco na categoria `AUSENTE`. Como 2019 está no treino e tinha mortalidade maior, o modelo pode aprender um **atalho**: "três campos em branco ⇒ é 2019 ⇒ risco mais alto". Isso se chama **marcador de ano**: a variável revela o ano da ficha, e não a condição do paciente.

| % de fichas em branco | 2019 | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| Perda de olfato | **99,7%** | 32% | 28% | 23% |
| Perda de paladar | **99,7%** | ≈32% | ≈28% | ≈23% |
| Fadiga | **99,4%** | 28% | 24% | 19% |
| Dispneia (comparação) | 1% | 13% | — | — |

| Logística por ano (piloto definitivo, validação) | 2019 | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| ROC-AUC | **0,78** | 0,86 | 0,85 | 0,85 |
| PR-AUC ÷ % de óbitos | **2,5×** | 3,7× | 3,7× | 3,6× |
| % de óbitos | 12,0% | 9,4% | 8,2% | 7,2% |
| Fichas na validação | 6.509 | 35.697 | 34.012 | 43.025 |

> [!exemplo] Como ler
> ROC-AUC 0,78 em 2019 quer dizer que, sorteando um óbito e uma cura de 2019, o modelo dá risco maior ao óbito em 78 de cada 100 pares; nos outros anos, em 85 a 86. O pior desempenho em 2019 é um **sinal** compatível com o atalho, mas não prova: 2019 tem poucas fichas e era um ano pré-pandemia, com perfil diferente.

> [!ok] Orientação de 24/10
> O professor pediu para **estudar** as três variáveis e retirar só se o efeito for "muito determinístico", sem tirar "só por tirar".

### ② Problema

> [!atenção] Reaberto em 01/11 (revisão de volatilidade)
> O critério exige a tabela de ablações do #54 e a decisão do #140, ambos abertos; a data ideal passou de 27/10 para 01/11, junto com o #140. A equipe já tinha avisado que este card deve ser reaberto se 2019 mudar de lado.
> O comentário de 01/11 deste card tem o motivo completo, o que pode mudar, o que continua válido, de que depende e como concluir de novo.

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que esta pendência está aberta
> A auditoria automática do painel (27/10, 14:40) marcou este item como resolvido com base em commits de 10 e 11/10, todos anteriores às revisões de 24 e 26/10 e sem relação com a entrega descrita aqui. Isso acontece por um defeito do painel: a cada auditoria, um commit antigo ainda não rejeitado reabre a sugestão (detalhes no #94).
> Não existem `outputs/final/volume_mensal_2019.csv` nem a ablação P × P − 3.
> **Divergência grave encontrada (28/10):** `configs/supervised.yaml` e `configs/decisoes.yaml` (versão 0.5) passaram a dizer que o desenvolvimento usa só 2023–2025 e que 2019 vai para `test_pandemic` junto com 2020–2022 (`periodo.desenvolvimento`, `temporal.blocos.*.anos`, `dev_years`, `pandemic_test_years` e a descrição do G2). Todo o resto do projeto continua com 2019 no desenvolvimento: `docs/decisoes.md` §5 e §28, a Base de Conhecimento v10, este painel, o teste `tests/test_split.py` (`TEMPORAL_CFG`), as saídas salvas do B_07 e o artefato atual (`manifesto_supervisionado.json`: teste = 3.035.074 linhas = `test_ref` + 2020–2022). A mudança não está registrada como decisão e o G2 continua com a data de aprovação de 18/10.
> Se a retirada de 2019 do treino for intencional, ela muda a natureza deste item: com 2019 fora do treino, o modelo não aprende o "marcador de ano" com 2019, mas passa a ser testado em 2019 com campos quase 100% vazios. A decisão precisa passar pelo #140.

Falta confirmar em que ano campos como perda de olfato, perda de paladar, fadiga e `vacina_cov` entraram na ficha. Antes disso, o vazio significa "campo inexistente", não "não informado".

### ③ O que fazer

**Dono:** Pessoa A (dados) + Pessoa C (ablação) · **Prazo:** 27/10 (terça); decisão no #140 (30/10, manhã) · **Esforço estimado:** A ≈ 1 h · C ≈ 1 h (dentro do #54) · **Começa quando:** #131 e #135

#### Objetivo
Decidir, com um critério combinado antes de olhar os números, se os três sintomas ficam ou saem do modelo principal.

> [!ok] Já confirmado na coorte definitiva (B_06, 27/10)
> Em branco em 2019: perda de olfato 99,7%, perda de paladar 99,7%, fadiga 99,5%. Em 2020 ainda ≈ 55%; em 2023–2025, 19% a 32%. Os passos 2 e 3 abaixo já estão cobertos por `eda_02_sintomas_por_ano.csv`.

#### Parte da Pessoa A (dados)
1. **2019 está completo?** Leia da fonte `data/processed/dados-v2/srag.parquet` só `dt_interna` e `hospital` (`read_srag(columns=[...])`), filtre internações de 2019 e conte por mês. Se algum mês estiver muito abaixo dos outros (ou zerado), anote: isso explica parte da diferença de 2019. Salve `outputs/final/volume_mensal_2019.csv`.
2. **Ano de entrada dos campos:** use `configs/dicionario_variaveis_v1.csv` (colunas `preenchimento_min_ano`, `preenchimento_max_ano`, `anos_observados`) e a tabela de sintomas por ano do B_06 (`outputs/tables/eda_02_sintomas_por_ano.csv`). Monte `outputs/final/campos_por_ano.csv` com % de branco por ano para as 31 principais e as 6 de contexto e gravidade. Destaque toda variável com mais de 90% de branco em algum ano de desenvolvimento.
3. **Conferir no artefato:** lendo só `particao`, `ano_internacao`, `perd_olft`, `perd_pala` e `fadiga` do artefato, confirme a % de `AUSENTE` em 2019 × 2023–2025 só no `train_ref`.

#### Parte da Pessoa C (modelo, dentro das ablações do #54)
4. Duas linhas na tabela de ablações, com o mesmo pipeline e os mesmos hiperparâmetros padrão: **P** (31 features) e **P − 3** (sem `perd_olft`, `perd_pala`, `fadiga`). Medir em `val_tune` e, por ano, em `val_meas`: ROC-AUC e PR-AUC ÷ prevalência.
5. Importância por permutação das três variáveis separada por ano (2019 × 2023–2025) em `val_meas` (amostra de até 100 mil).

#### Critério de decisão (combinado antes de ver o resultado)
**Retirar** os três sintomas (falha material que justifica reabrir o G1) se **qualquer** uma ocorrer:
- (a) a ROC-AUC de 2019 sobe pelo menos 0,01 sem eles;
- (b) a PR-AUC geral não cai mais que 0,005 sem eles (perder as três não custa nada);
- (c) a importância por permutação das três vem quase toda de 2019.

**Manter** e documentar se nenhuma ocorrer.

6. A Pessoa C escreve o resultado no card; a Pessoa A registra a decisão no `decisoes.md` (#73) com a tabela, e atualiza `features.final` no YAML se a decisão for retirar (com revisão da Pessoa C).

#### Pronto quando
Os três CSVs existirem, a decisão estiver registrada com a tabela e, se for o caso, o YAML atualizado antes do G6.

#### Para o relatório
Seja qual for a decisão, é um achado forte de Engenharia de Dados: mostra que a equipe percebeu que a mudança da ficha ao longo do tempo pode criar atalhos no modelo, e testou isso.

### ④ Pronto quando

- existe: `outputs/final/volume_mensal_2019.csv` | O volume mensal de internações de 2019 está em outputs/final/volume_mensal_2019.csv (mostra se algum mês está faltando).
- existe: `outputs/final/campos_por_ano.csv` | A % de branco por ano das 31 principais e das 6 de contexto e gravidade está em outputs/final/campos_por_ano.csv.
- existe: `outputs/final/ablacoes_val_tune.csv` | As linhas P e P − 3 sintomas (sem perd_olft, perd_pala, fadiga) estão na tabela de ablações do #54.
- manual: | A decisão (manter ou retirar os três sintomas, pelo critério combinado antes de ver os números) está registrada no docs/decisoes.md com a tabela e, se for retirar, o features.final do YAML foi atualizado antes do G6. Se a decisão do #102 tirar 2019 do treino, a leitura deste item muda e precisa passar pelo #140.
- manual: | Reconfirmado depois do #54 e do #140: `ablacoes_val_tune.csv` tem as linhas P e P − 3 sintomas, e a decisão de manter ou retirar `perd_olft`, `perd_pala` e `fadiga` está no `decisoes.md` com a tabela.

## #68 · Texto com codificação corrompida

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 05/11
- responsável: C
- pessoas: C
- fonte: tests/test_metrics.py
- depende de: —
- tags: Documentação
- pilar: —
- carga: —
- novo: não
- professores: não

### ① Para entender

O relatório automático ainda acusa caracteres corrompidos (A27), como "m├ętricas", sinal de arquivo salvo com a codificação errada.

### ② Problema

A docstring do arquivo tem caracteres corrompidos ("m├ętricas"), sinal de que foi salvo com a codificação errada.

### ③ O que fazer

Pós-entrega.

**Como fazer, quando for a hora (instruções anteriores mantidas):**

Corrigir o texto e salvar o arquivo em UTF-8.

### ④ Pronto quando

- nao-contem: `tests/test_metrics.py` :: `├` | (Pós-entrega) tests/test_metrics.py não tem mais caracteres corrompidos (como "m├ętricas"); o arquivo está em UTF-8.

## #74 · Faltam os números do clustering sem saturação e desconforto

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 05/11
- responsável: B
- pessoas: B
- fonte: B_06_eda_temporal_clustering
- depende de: —
- tags: Notebook, Documentação
- pilar: —
- carga: —
- novo: não
- professores: não
- removido: removido na revisão de 03/11 (v3.4): sem objeto; saturação e desconforto entraram no modelo principal (§29.34)

### ① Para entender

> [!decisão] Decisão de 18/10
> Prioridade anterior: P3. Rebaixada para P4 em 18/10.

A análise foi planejada, mas o resultado não foi registrado no B_06. Ela mostra se os grupos mudam quando tiramos as duas variáveis de gravidade.

### ② Problema

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que esta pendência está aberta
> A auditoria automática (27/10, 14:40) marcou "precisa revisão" por achados que não tratam deste item: a linha decorativa `=====` no cabeçalho de `src/protocolo/verificacoes.py` (lida como conflito de merge) e o `OneHotEncoder` denso do B_06, que roda numa amostra de 80 mil fichas e será substituído pelo #136 (detalhes no #94).
> Continua pós-entrega.

Faltam os números da sensibilidade do clustering sem saturação e sem desconforto respiratório.

### ③ O que fazer

Pós-entrega. O relatório usa o clustering principal; a sensibilidade sem saturação e desconforto vira uma frase em Trabalhos futuros, se for citada.

**Como fazer, quando for a hora (instruções anteriores mantidas):**

Recuperar os resultados da execução do B_06 (ou rodar de novo a célula) e exportá-los numa tabela para o relatório.

### ④ Pronto quando

- manual: | (Pós-entrega) Os números do clustering sem saturação e desconforto foram exportados numa tabela, ou ficaram como trabalho futuro no relatório.

## #88 · A exportação da Pessoa A não tem duas variáveis que o modelo exige

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 05/11
- responsável: A
- pessoas: A
- fonte: notebooks A_03 e A_04 (exportação); src/protocolo/verificacoes.py; src/features (montar_features)
- depende de: #87
- tags: Código, Features, Dados/Coorte
- pilar: —
- carga: —
- novo: não
- professores: não
- removido: obsoleto em 03/11: a exportação do fluxo provisório da Pessoa A foi aposentada (§29.32)

### ① Para entender

> [!decisão] Decisão de 18/10
> O E_01 monta as features pelo `src`; o export da Pessoa A deixa de alimentar o pipeline. Prioridade anterior: P2. Rebaixada para P4 em 18/10.

O A_03 e o A_04 conferem o arquivo exportado contra o que os notebooks C precisam, e a conferência falha: faltam `dias_sintomas_ate_internacao` e `sexo_categoria`, criadas por `montar_features` no `src`.

Ou seja, a população analítica da Pessoa A não serve de entrada direta para o pipeline supervisionado.

### ② Problema

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que esta pendência está aberta
> A auditoria automática (27/10, 14:40) marcou "precisa revisão" por achados que não tratam deste item: a linha decorativa `=====` no cabeçalho de `src/protocolo/verificacoes.py` (lida como conflito de merge) e o `OneHotEncoder` denso do B_06, que roda numa amostra de 80 mil fichas e será substituído pelo #136 (detalhes no #94).
> Continua pós-entrega (a exportação da Pessoa A não alimenta mais a cadeia oficial).

No A_03 e no A_04, a verificação "C2 exige todas as features" retorna FALHA: "faltam no dataset (o C não vai rodar): \['dias_sintomas_ate_internacao', 'sexo_categoria']". As demais verificações (coluna de tempo, alvo, `check_leakage`, tamanho) estão OK. `a1_export_dataset` cria só as derivadas listadas em `_DERIVADAS_CANON`.

### ③ O que fazer

Pós-entrega. A exportação da Pessoa A não alimenta mais a cadeia oficial (#87). Basta a nota de “histórico” no topo do A_03 e do A_04.

**Como fazer, quando for a hora (instruções anteriores mantidas):**

1. Em `a1_export_dataset`, aplicar `montar_features` do `src/features` antes de selecionar as colunas, em vez de derivar à parte.
2. Ou, se a exportação da Pessoa A não for mais usada pelo pipeline, documentar que ela é só para auditoria e remover a verificação "C2 exige".
3. Rodar A_03 e A_04 e conferir que a verificação passa.

### ④ Pronto quando

- manual: | (Pós-entrega) A exportação da Pessoa A aplica montar_features antes de selecionar as colunas, ou está documentada como só para auditoria (sem a verificação "C2 exige").

## #90 · O A_09 sorteia linhas, e não grupos: a mesma ficha cai em duas partições

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 05/11
- responsável: A
- pessoas: A
- fonte: notebooks A_09; src/protocolo/verificacoes.py (split_aleatorio)
- depende de: —
- tags: Partição, Código
- pilar: —
- carga: —
- novo: não
- professores: não
- removido: obsoleto em 03/11: o notebook A_09 não existe mais; a partição oficial é por grupo (src/data/split.py)

### ① Para entender

> [!decisão] Decisão de 18/10
> O E_01 usa partição por grupo; o A_09 fica como análise histórica. Prioridade anterior: P3. Rebaixada para P4 em 18/10.

No B_07, todas as linhas de um mesmo `nu_notific` vão juntas para a mesma partição. No A_09, o sorteio é por linha, e o próprio notebook avisou que 10 números (9 no cenário sem pandemia) aparecem em mais de uma partição.

> [!exemplo] Exemplo
> É como o mesmo aluno fazer o simulado e a prova com as mesmas questões: um pouco de cola.

### ② Problema

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que esta pendência está aberta
> A auditoria automática (27/10, 14:40) marcou "precisa revisão" por achados que não tratam deste item: a linha decorativa `=====` no cabeçalho de `src/protocolo/verificacoes.py` (lida como conflito de merge) e o `OneHotEncoder` denso do B_06, que roda numa amostra de 80 mil fichas e será substituído pelo #136 (detalhes no #94).
> `split_aleatorio` continua sorteando linhas. O A_09 sai no #143. Continua pós-entrega.

`split_aleatorio` (usado por `a1_export_dataset(split=...)`) estratifica pelo alvo, mas sorteia índices de linha. O A_09 reportou "10 NU_NOTIFIC em mais de uma partição (todos_2019_2025)" e 9 em "sem_2020_2021". O efeito numérico é desprezível, mas o método diverge do oficial.

### ③ O que fazer

Pós-entrega. Superado pela partição-mestre por grupo (#131). O A_09 é histórico (#89).

**Como fazer, quando for a hora (instruções anteriores mantidas):**

1. Usar a função oficial de partição por hash (item 86) também nos cenários do A_09.
2. Se mantiver a função própria, sortear por grupo (`nu_notific`) e não por linha.
3. Rodar o A_09 de novo e confirmar 0 identificadores em mais de uma partição.

### ④ Pronto quando

- manual: | (Pós-entrega) O A_09 sorteia por grupo (nu_notific), com 0 identificadores em mais de uma partição, ou foi removido no #143.

## #93 · O A_14 não tem a tabela de candidatos para comparar

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 05/11
- responsável: A + C
- pessoas: A, C
- fonte: notebooks A_14 (seção 1); outputs/tables/resultados_cv.csv; C_13 e C_15 (comparação)
- depende de: #1, #87
- tags: Notebook, Modelagem
- pilar: —
- carga: —
- novo: não
- professores: não
- removido: obsoleto em 03/11: o notebook A_14 não existe mais

### ① Para entender

> [!decisão] Decisão de 18/10
> Prioridade anterior: P2. Rebaixada para P4 em 18/10.

O A_14 deveria comparar os candidatos por validade, estabilidade e calibração (decisão D-11). Ele procura `outputs/tables/resultados_cv.csv`, que ninguém gera, e por isso a tabela de decisão ficou vazia.

### ② Problema

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Obsoleto para a entrega: o A_14 sai do pacote no #143.

Saída do A_14: "outputs/tables/resultados_cv.csv não encontrado — preencha RESULTS". Os resultados existem em outros arquivos: comparação das cinco famílias do B_07, comparação do C_13 e tabelas do C_15. Nenhum deles tem o formato esperado (`modelo, fold, pr_auc, roc_auc, brier`).

### ③ O que fazer

Pós-entrega. O A_14 é histórico; a tabela de candidatos oficial é a do tuning (#1) e das ablações (#54).

**Como fazer, quando for a hora (instruções anteriores mantidas):**

1. Combinar o formato: uma linha por modelo e partição de avaliação, com PR-AUC, ROC-AUC, Brier bruto e calibrado, ECE.
2. Gerar o CSV no fim do C_15 (após o ajuste fino), juntando C_13 e C_15.
3. Apontar `RESULTS` do A_14 para esse arquivo e rodar.

### ④ Pronto quando

- manual: | (Pós-entrega) O A_14 lê uma tabela de candidatos gerada no fim do C_15, ou foi removido no #143.

## #94 · Alertas falsos no relatório automático do projeto

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 05/11
- responsável: C
- pessoas: C
- fonte: tools/update_project_reference.py (relatório estático)
- depende de: —
- tags: Código, Documentação
- pilar: —
- carga: —
- novo: não
- professores: não
- removido: removido na revisão de 03/11 (v3.2): defeito da ferramenta do painel, não do projeto entregue

### ① Para entender

O relatório de atenção marca 7 alertas "altos", mas 4 deles são engano da ferramenta: ela confunde `subprocess.run` com a função `verificacoes.run` da Pessoa A (A2 a A5). Os alertas A12 a A16 tratam nomes de variáveis como `G6_STATUS` como se fossem gates. O A17 aponta erro de sintaxe no B_07 que não se confirma.

> [!exemplo] Exemplo
> Um alarme de incêndio que dispara com vapor do chuveiro: as pessoas param de prestar atenção nos alarmes de verdade.

### ② Problema

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que esta pendência está aberta
> A auditoria automática do painel (27/10, 14:40) marcou este item como resolvido com base em commits de 10 e 11/10, todos anteriores às revisões de 24 e 26/10 e sem relação com a entrega descrita aqui. Isso acontece por um defeito do painel: a cada auditoria, um commit antigo ainda não rejeitado reabre a sugestão (detalhes no #94).
> **Este item ganhou prioridade prática na revisão de 28/10**: dois defeitos do painel e do auditor geram trabalho falso para o time a cada auditoria (ver ③).

Falsos positivos identificados: A2–A5 (call-signature-mismatch por homonímia com `subprocess.run`), A12–A16 (gate-name-not-in-yaml para variáveis `G6_STATUS`, `G6_APROVADO`, `G7_STATUS`, `G8_STATUS` e o fragmento `G6_fi`), A17 (todas as células de código do B_07 passam em `ast.parse`). O alerta A1 (`criar_alvo_binario`) é verdadeiro (item 6).

### ③ O que fazer

**Dono:** Pessoa C (ou quem cuida do painel) · **Esforço estimado:** ≈ 20 min · **Recomendado agora**, embora o card siga marcado como pós-entrega

#### Defeito 1: a auditoria profunda reabre sugestões antigas a cada execução
Em `.srag-status-local/server.py`, `apply_deep` percorre todos os commits antigos que mexeram nos arquivos da tarefa com palavras como "resolvendo" e marca a tarefa como "a confirmar" com o primeiro commit ainda não rejeitado. Como `save_seen` não grava nada (por desenho) e "✗ Não é isso" só rejeita os commits já anexados, **cada auditoria puxa o próximo commit antigo**. Foi o que aconteceu em 26/10 e de novo em 27/10 (24 itens "a confirmar" com commits de 09 a 21/10).

Correção: ignorar commits anteriores à última decisão humana sobre o item. No `apply_deep`, logo depois de `for c in deep["source_hits"].get(iid, []):` e do `s12 = c["sha"][:12]`, acrescentar:
```python
            decidido = item.get("updated_at") if item.get("origin") == "human" else None
            if decidido and _instante(c["when"]) <= _instante(decidido):
                continue
```
e, perto de `def now()`, a função:
```python
def _instante(texto: str) -> dt.datetime:
    """Converte '2026-10-19T10:27:11-03:00' ou '...Z' em datetime com fuso."""
    return dt.datetime.fromisoformat(str(texto).replace("Z", "+00:00"))
```

#### Defeito 2: falsos "conflito de merge" e "one-hot denso"
- Em `deep_git_project_audit.py` (as duas cópias: `tools/` e `.srag-status-local/` — elas estão diferentes entre si), trocar `MERGE_CONFLICT = re.compile(r"^(<{7}|={7}|>{7})", re.M)` por `MERGE_CONFLICT = re.compile(r"^(<{7} |={7}$|>{7} )", re.M)`. A linha decorativa `=====...` de `src/protocolo/verificacoes.py` deixa de ser lida como conflito.
- O alerta "OneHotEncoder denso" também é disparado pelo próprio `PROJECT_STATUS_TEXT.md` (o auditor lê o texto do painel). Excluir `PROJECT_STATUS_TEXT.md` e `PROJECT_STATUS.md` da varredura de código.

#### Antigos falsos positivos (mantidos)
1. Na checagem de assinatura, resolver o import real antes de comparar.
2. Na checagem de gates, aceitar só nomes completos `G\d+_[a-z_]+`.
3. Rever o parser de células.

### ④ Pronto quando

- contem: `.srag-status-local/deep_git_project_audit.py` :: `={7}$` | O auditor só aceita marcadores reais de conflito de merge: a linha decorativa ===== deixou de ser alarme (verificador v6).
- nao-existe: `tools/deep_git_project_audit.py` | A cópia antiga e diferente do auditor em tools/ foi apagada; a fonte única é .srag-status-local/deep_git_project_audit.py.
- manual: | Os falsos positivos antigos do relatório estático do update_project_reference (A2–A5 por homonímia com subprocess.run, A12–A16 com nomes como G6_STATUS, A17) foram corrigidos ou aceitos como limitação conhecida.

## #128 · 29 avisos de depreciação de timedelta sem unidade no NumPy

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 05/11
- responsável: A
- pessoas: A
- fonte: src/protocolo/verificacoes.py:242
- depende de: —
- tags: Código, Ambiente
- pilar: —
- carga: —
- novo: sim
- professores: não
- removido: removido na revisão de 03/11 (v3.2): avisos de depreciação sem efeito nos resultados

### ① Para entender

Aviso, não erro: uma versão futura do NumPy vai exigir unidade explícita. Não afeta resultados hoje.

### ② Problema

`np.full(len(s), np.datetime64("NaT"), ...)` e operações com inteiro sem unidade.

### ③ O que fazer

Pós-entrega.

**Como fazer, quando for a hora (instruções anteriores mantidas):**

Despriorizado: corrigir só após a entrega, com teste da Pessoa A.

### ④ Pronto quando

- manual: | (Pós-entrega) Os avisos de timedelta sem unidade em src/protocolo/verificacoes.py foram corrigidos, com teste da Pessoa A.

## #129 · Refatoração completa de performance de B_05, construtor e notebooks A

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 05/11
- responsável: B
- pessoas: B
- fonte: Plano_Performance_SRAG.html (fases F3, F4, F7)
- depende de: —
- tags: Memória/Desempenho, Notebook
- pilar: —
- carga: —
- novo: sim
- professores: não
- removido: removido na revisão de 03/11 (v3.2): os notebooks A e o construtor da coorte provisória citados não existem mais

### ① Para entender

O plano de performance propõe reescrever B_05, o construtor da coorte (duas passadas) e o cache de datas da Pessoa A. São ganhos reais, mas esses notebooks não estão no caminho do experimento final.

### ② Problema

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Pós-entrega. O que importava para a entrega (medir tempo e memória e corrigir os picos dos notebooks) foi para o #145. A refatoração completa continua fora do escopo.

Custo alto, risco de mudar resultados já validados e nenhum impacto direto na entrega.

### ③ O que fazer

Pós-entrega. O construtor definitivo já roda com leitura projetada; não há exceção a acionar.

**Como fazer, quando for a hora (instruções anteriores mantidas):**

Despriorizado. Exceção: se o construtor da coorte não couber na memória (item 98), aplicar só a leitura em duas passadas.

### ④ Pronto quando

- manual: | (Pós-entrega) A refatoração de performance do B_05, do construtor e dos notebooks A foi feita, ou ficou registrada como trabalho futuro.

## #4 · O boosting do código central não é o mesmo do piloto

- prioridade: P1
- situação: resolvida
- estratégia: resolvida
- marco: M1
- data ideal: Concluído
- responsável: C
- pessoas: C
- fonte: src/models/boosting.py; src/models/pipeline.py (build_preprocessor)
- depende de: #92
- tags: Código, Modelagem, Memória/Desempenho
- pilar: —
- carga: —
- novo: não
- professores: não

### ① Para entender

> [!decisão] Decisão de 18/10
> Resolvido em 17/10: `boosting.py` usa pré-processamento ordinal com `categorical_features` e os parâmetros do piloto (0,08 / 150 / 100 / 0,10, early stopping). Testes de pipeline passaram.

No piloto (B_07), o boosting recebeu as categorias como **códigos** (ordinal) e tratou-as de forma nativa. O `src/models/boosting.py` ainda usa **one-hot denso** e não informa quais colunas são categóricas. Os valores padrão também são outros.

| Parâmetro | Piloto (B_07) | src (C_13) |
|---|---|---|
| Codificação | ordinal + categóricas nativas | one-hot denso |
| learning_rate | 0,08 | 0,05 |
| max_iter | 150 | 500 |
| min_samples_leaf | 100 | 20 |
| l2_regularization | 0,10 | 0,0 |
| early_stopping | sim | não |

Resultado: o ajuste fino otimizaria um modelo diferente do que entrou na lista curta.

### ② Problema

`build_boosting_pipeline` usa `build_preprocessor()` com `OneHotEncoder(sparse_output=False)` e não passa `categorical_features` ao `HistGradientBoostingClassifier`. O piloto da lista curta usou codificação ordinal com categóricas nativas. Os padrões também divergem: 0,05 / 500 / 20 / 0,0 no construtor contra 0,08 / 150 / 100 / 0,10 no piloto.

**Atualização 17/10:** a correção foi proposta em 16/10 (parâmetro `saida="ordinal"` em `build_preprocessor`), mas o `boosting.py` e o `pipeline.py` do repositório (commit `8e52d8a`) **ainda estão na versão antiga**. O C_13 rodou com one-hot denso e obteve PR-AUC 0,4675.

**Depois do pull de 17/10:** o retrato analisado é anterior ao pull. Antes de editar, abra o arquivo e confira se alguém já aplicou a mudança (procure `sparse_output=True` e `saida=`).

### ③ O que fazer

> [!ok] Concluída: `boosting.py` usa saída ordinal com categóricas nativas e `early_stopping` (commit `d790b90`). Pode **✓ Confirmar** no painel.

### ④ Pronto quando

- contem: `src/models/boosting.py` :: `early_stopping: bool = True` | O boosting do src usa early stopping por padrão, como o piloto.
- contem: `src/models/boosting.py` :: `saida="ordinal"` | O boosting do src usa pré-processamento ordinal com categóricas nativas (categorical_features), como o piloto, e não one-hot denso.
- teste: `tests/test_model_pipelines.py` | Os testes de pipelines passam.

## #7 · Artefato supervisionado com colunas de auditoria (sg_uf, vacina, saturação…)

- prioridade: P1
- situação: resolvida
- estratégia: resolvida
- marco: —
- data ideal: Concluído
- responsável: B
- pessoas: B
- fonte: B_07_supervisionado_pilotos (seção 9, persist_supervised_artifact); notebooks C_16; configs/supervised.yaml (avaliacao.grupos, features.contexto_incremental)
- depende de: —
- tags: Notebook, Dados/Coorte
- pilar: —
- carga: —
- novo: não
- professores: não

### ① Para entender

> [!ok] Situação atual
> Resolvido em 16/10. O B_07 grava 43 colunas, das quais 10 são de auditoria, e o manifesto traz `audit_columns`, `numeric_columns` e `categorical_columns`. A conferência do manifesto passou 8 de 8 verificações.

Isso destravou as sensibilidades de gravidade e de contexto (item 54) e a análise por UF no C_16.

### ② Problema

O B_07 salva o artefato supervisionado sem `audit_columns`, `numeric_columns` e `categorical_columns`, e só com as features do piloto. Por isso: o C_16 pula o grupo `sg_uf` na análise por subgrupo, e as sensibilidades de contexto incremental (`sg_uf`, `vacina`, `vacina_cov`, `cs_escol_n`) e de gravidade (`saturacao`, `desc_resp`) não têm as colunas de que precisam.

### ③ O que fazer

> [!ok] Concluída na fase provisória; **refeita no #131 para a definitiva**
> O artefato v3 já nasce com `numeric_columns`, `categorical_columns`, colunas de contexto, de gravidade e de auditoria (`sg_uf`, `regiao_residencia`, `faixa_etaria`, `ano_internacao`, `group_id`). Conferir no manifesto quando o #131 terminar e então **✓ Confirmar**.

### ④ Pronto quando

- contem: `notebooks/B/B_07_supervisionado_pilotos.ipynb` :: `audit_columns` | O B_07 grava o artefato com audit_columns, numeric_columns e categorical_columns no manifesto.
- json: `data/analytical/manifesto_supervisionado.json` :: `audit_columns` existe | O manifesto do artefato tem a lista audit_columns (arquivo local de quem gerou o artefato).

## #8 · Partição estratificada por ano × desfecho

- prioridade: P1
- situação: resolvida
- estratégia: resolvida
- marco: —
- data ideal: Concluído
- responsável: B
- pessoas: B
- fonte: B_07_supervisionado_pilotos (seções 7 e 8); src/data/split.py; configs/supervised.yaml (temporal); docs/decisoes.md §21
- depende de: #10
- tags: Diverge do decidido, Partição, Código
- pilar: —
- carga: —
- novo: não
- professores: não

### ① Para entender

> [!ok] Situação atual
> Resolvido em 16/10 com `atribuir_particao_estratificada_por_hash` (método `hash_grupo_estratificado_v1`). Desvio máximo por estrato: 0,02 p.p. Tempo: 8,7 s.

| Partição | Linhas | Prevalência |
|---|---|---|
| Treino | 2.740.584 | 0,21868 |
| Validação | 587.272 | 0,21869 |
| Teste | 587.276 | 0,21869 |

A função ainda vive só no notebook. Levá-la para `src/data/split.py` é o item 86.

### ② Problema

A divisão em treino, validação e teste não estratifica pelo ano. O B_07 cria `estrato_split` (ano + alvo), mas o usa apenas para auditar conflitos; na chamada de `criar_particoes_agrupadas`, passa `target_column=ALVO_MODELO`. O YAML, o gate G2, a seção 21 das decisões e o próprio cabeçalho do B_07 afirmam que a divisão é estratificada por alvo e ano.

### ③ O que fazer

> [!ok] Resolvida pela partição-mestre
> `criar_particao_mestra` estratifica por ano × alvo × região, com fallback registrado no manifesto. Confirmar quando o manifesto do #131 mostrar a estratificação usada.

### ④ Pronto quando

- define: `src/data/split.py` :: `atribuir_particao_estratificada_por_hash` | A partição estratificada por ano × desfecho (hash por grupo) está em src/data/split.py.
- teste: `tests/test_split.py::test_estratificacao_preserva_proporcao_aproximada` | O teste confirma que a estratificação preserva as proporções.

## #44 · Coorte definitiva inicial: congelar a seleção de features da coorte provisória

- prioridade: P1
- situação: resolvida
- estratégia: resolvida
- marco: —
- data ideal: Concluído
- responsável: A (validação técnica: C)
- pessoas: A, C
- fonte: Projeto (coorte definitiva)
- depende de: —
- tags: Dados/Coorte, Gate
- pilar: —
- carga: —
- novo: não
- professores: não

### ① Para entender

> [!ok] Decisão fechada em 18/10
> A coorte definitiva inicial será a seleção de features da coorte provisória. O treino principal usará exclusivamente 2019, 2023, 2024 e 2025. Haverá duas janelas de teste: (A) 2019, 2023, 2024 e 2025; (B) 2019 a 2025, incluindo 2020–2022. O ano de 2026 não participa do desenvolvimento nem dos testes principais e fica apenas como exploração opcional, depois de todo o restante concluído.

Esta decisão encerra a espera por uma nova seleção de features. A população e a seleção já auditadas na coorte provisória formam a base inicial da coorte definitiva da entrega. A execução física, o manifesto e o nome canônico continuam nos itens #30 e #77.

### ② Problema

O risco anterior era manter todo o pipeline bloqueado aguardando uma nova coorte sem prazo. Esse risco foi eliminado pela decisão de promover a seleção de features já validada na provisória.

### ③ O que fazer

> [!ok] Concluída e materializada
> Coorte definitiva publicada em 23/10: `data/analytical/coorte_final.parquet`, 3.884.728 notificações, 199 colunas, alvo 0/1, SHA-256 `87f28d39…`, com paridade legada revisada e comparação com a provisória. A definitiva é subconjunto exato da provisória: 30.408 linhas a menos, nenhuma nova e 0 divergências de alvo.

Não reabrir. O próximo passo é o #131.

### ④ Pronto quando

- json: `data/analytical/coorte_final.manifest.json` :: `publication_performed` = `true` | O manifesto da coorte definitiva registra que a publicação foi feita (arquivo local de quem publicou).
- json: `data/analytical/coorte_final.manifest.json` :: `legacy_parity_reviewed` = `true` | O manifesto registra a paridade com a implementação legada revisada.
- yaml: `configs/supervised.yaml` :: `features.final` existe | A seleção de features da coorte provisória ficou congelada em features.final.

## #85 · Períodos de treino e teste definidos

- prioridade: P1
- situação: resolvida
- estratégia: resolvida
- marco: —
- data ideal: Concluído
- responsável: Equipe (conduz: A)
- pessoas: A, Equipe
- fonte: B_07 + configs/supervised.yaml (periodo, temporal, G2); A_03/A_04/A_08 (D-05, D-10); A_09 (D-13, D-14); reunião de 16/10
- depende de: —
- tags: Diverge do decidido, Decisão, Partição, Gate
- pilar: —
- carga: —
- novo: não
- professores: não

### ① Para entender

> [!ok] Decisão fechada em 18/10
> A coorte definitiva inicial será a seleção de features da coorte provisória. O treino principal usará exclusivamente 2019, 2023, 2024 e 2025. Haverá duas janelas de teste: (A) 2019, 2023, 2024 e 2025; (B) 2019 a 2025, incluindo 2020–2022. O ano de 2026 não participa do desenvolvimento nem dos testes principais e fica apenas como exploração opcional, depois de todo o restante concluído.

| Conjunto | Anos | Função |
|---|---|---|
| Treino principal | 2019, 2023, 2024 e 2025 | Desenvolvimento do modelo sem anos pandêmicos |
| Teste A — referência | 2019, 2023, 2024 e 2025 | Avaliação dentro do mesmo domínio temporal do treino, em registros/grupos separados |
| Teste B — ampliado | 2019–2025 | Avaliação de robustez ao incluir 2020, 2021 e 2022 |
| Exploração opcional | 2026 | Somente depois de todo o restante concluído |

### ② Problema

A divergência anterior entre 2019–2026, recorte não pandêmico e cenários com pandemia foi encerrada. Resta implementar o mapa de partição e os dois relatórios de teste sem misturar grupos.

### ③ O que fazer

> [!ok] Concluída: decisão de 18/10, G2 aprovado. Implementação no #131 e no #132.

### ④ Pronto quando

- yaml: `configs/supervised.yaml` :: `gates.G2_janela_temporal.status` = `aprovado` | O G2 (períodos de treino e teste) está aprovado no YAML.
- yaml: `configs/supervised.yaml` :: `periodo.exploracao_opcional` contem `2026` | 2026 está declarado só como exploração. (O lugar de 2019 é decidido no #102.)

## #92 · Repositório local sincronizado com o GitHub

- prioridade: P1
- situação: resolvida
- estratégia: resolvida
- marco: —
- data ideal: Concluído
- responsável: B
- pessoas: B
- fonte: Git (branch main); docs/project_reference_parts/; tools/compilar_resultados.py; docs/RESULTADOS_COMPILADOS.md
- depende de: —
- tags: Git, Ambiente
- pilar: —
- carga: —
- novo: não
- professores: não

### ① Para entender

> [!ok] Situação atual
> Resolvido em 17/10: `git pull` feito com sucesso; a cópia local está no commit mais recente.

Os arquivos não commitados são `.md` de contexto para IA (referência do projeto e resultados compilados). Cada pessoa gera os seus na hora de usar, então ficar fora do Git é intencional e não afeta o projeto.

### ② Problema

Em 17/10 de manhã, a cópia local estava 4 commits atrás de `origin/main`, com arquivos de referência modificados e dois arquivos não rastreados (alerta A7). O pull resolveu o atraso; os `.md` de contexto ficam fora do Git por decisão do time.

### ③ O que fazer

> [!ok] Concluída. Rotina daqui em diante: `git pull` antes de começar o dia e antes de cada commit.

### ④ Pronto quando

- manual: | Rotina: git pull antes de começar o dia e antes de cada commit. O painel mostra no selo quando a sua pasta está atrás do GitHub.

## #113 · O 01_extracao lia o Parquet inteiro (processo de ~13 GB)

- prioridade: P1
- situação: resolvida
- estratégia: resolvida
- marco: M1
- data ideal: Concluído
- responsável: B
- pessoas: B
- fonte: notebooks/01_extracao.ipynb
- depende de: —
- tags: Memória/Desempenho, Notebook
- pilar: —
- carga: —
- novo: sim
- professores: não

### ① Para entender

> [!ok] Situação atual
> Resolvido em 17/10. As seções 4 e 5 agora usam só os metadados do Parquet (linhas, colunas, row groups) e uma amostra de 5 linhas. Nenhum DataFrame grande é criado.

| Antes | Depois |
|---|---|
| 198 colunas × 4.666.910 linhas na RAM | metadados + 5 linhas |
| ~13 GB de processo | alguns MB |

### ② Problema

`df = pd.read_parquet(parquet_path)` carregava a base inteira só para contar linhas e mostrar `head()`. O kernel continuava vivo depois de fechar a aba.

### ③ O que fazer

> [!ok] Concluída. Nada a fazer.

### ④ Pronto quando

- nao-contem: `notebooks/01_extracao.ipynb` :: `pd.read_parquet(parquet_path)` | O 01_extracao não carrega mais o Parquet inteiro: as seções 4 e 5 usam só os metadados (linhas, colunas, row groups) e uma amostra de 5 linhas.

## #17 · One-hot denso no código central: risco de faltar memória

- prioridade: P2
- situação: resolvida
- estratégia: resolvida
- marco: M1
- data ideal: Concluído
- responsável: C
- pessoas: C
- fonte: src/models/pipeline.py (build_preprocessor)
- depende de: #92
- tags: Código, Memória/Desempenho
- pilar: —
- carga: —
- novo: não
- professores: não

### ① Para entender

> [!decisão] Decisão de 18/10
> Resolvido em 17/10: `build_preprocessor(saida="esparsa")` gera matriz CSR em float32. Teste com amostra real confirmou saída esparsa.

O `build_preprocessor` do `src` cria a tabela de categorias em formato **denso**: guarda todos os zeros. Com a coorte inteira, são 2,7 milhões de linhas × 126 colunas em float64.

<div class="kpi">
<div><b>2,53 GiB</b>só para a matriz de treino (erro do C2 em 16/10)</div>
<div><b>~0,1 GiB</b>a mesma matriz em formato esparso float32</div>
</div>

> [!atenção] Atenção
> Em 16/10 foi proposta a versão esparsa, mas ela **não está no repositório**: o `pipeline.py` do commit `8e52d8a` ainda tem `sparse_output=False`. O C_11 rodou depois de reiniciar o kernel, mas pode falhar de novo em outra máquina.

### ② Problema

O `OneHotEncoder` de `src/models/pipeline.py` usa `sparse_output=False`. No C2 (hoje C_11), isso causou `MemoryError: Unable to allocate 2.53 GiB for an array with shape (2740584, 124) and data type float64`. A correção (saída esparsa em float32 + saída ordinal para o boosting) foi escrita em 16/10, mas o arquivo do repositório não mudou. Notebooks C_11 a C_16 dependem dessa função.

**Depois do pull de 17/10:** o retrato analisado é anterior ao pull. Antes de editar, abra o arquivo e confira se alguém já aplicou a mudança (procure `sparse_output=True` e `saida=`).

### ③ O que fazer

> [!ok] Concluída: `build_preprocessor(saida="esparsa"|"ordinal")` em `pipeline.py`. Pode **✓ Confirmar**.

### ④ Pronto quando

- contem: `src/models/pipeline.py` :: `saida: SaidaPreprocessador = "esparsa"` | build_preprocessor gera matriz esparsa por padrão (CSR em float32), sem guardar os zeros do one-hot.
- teste: `tests/test_pipeline.py` | Os testes do pipeline passam.
- teste: `tests/test_config.py` | O teste `tests/test_config.py` precisa passar no pytest rápido. Ele importa `src/models/pipeline.py`, que pertence(m) a esta pendência, e falhou na verificação de 2026-11-03 (2 testes falharam; ex.: FileNotFoundError: [Errno 2] No such file or directory: 'C:\\Users\\olivem85\\AppData\\Local\\Temp\\1\\srag_verificador_9mdibj0g\\repo\\). Acrescentado automaticamente pelo verificador.

## #62 · pyproject.toml inválido

- prioridade: P2
- situação: resolvida
- estratégia: resolvida
- marco: —
- data ideal: Concluído
- responsável: C
- pessoas: C
- fonte: pyproject.toml
- depende de: —
- tags: Ambiente
- pilar: —
- carga: —
- novo: não
- professores: não

### ① Para entender

> [!ok] Situação atual
> O relatório de 17/10 diz "Valid TOML: yes", e o `pip install -e .` funciona.

### ② Problema

Na versão exportada, `license =` está vazio, `authors = [ , ]` não tem valores e a URL do repositório é um modelo (`SEU_USUARIO/SEU_REPO`). Se o arquivo real estiver assim, `pip install -e .` falha por TOML inválido.

### ③ O que fazer

> [!ok] Concluída: `pyproject.toml` válido (licença e autores preenchidos). Pode **✓ Confirmar**.

### ④ Pronto quando

- nao-contem: `pyproject.toml` :: `SEU_USUARIO` | O pyproject.toml não tem mais o endereço de modelo SEU_USUARIO/SEU_REPO.
- contem: `pyproject.toml` :: `authors` | O pyproject.toml tem autores preenchidos e é TOML válido (pip install -e . funciona).

## #114 · Precedência errada entre penalty do YAML e l1_ratio explícito na logística

- prioridade: P2
- situação: resolvida
- estratégia: resolvida
- marco: M1
- data ideal: Concluído
- responsável: C
- pessoas: C
- fonte: src/models/logistic.py; tests/test_model_pipelines.py
- depende de: —
- tags: Código, Testes
- pilar: —
- carga: —
- novo: sim
- professores: não

### ① Para entender

> [!ok] Situação atual
> Resolvido em 17/10. Um `l1_ratio` passado explicitamente agora vence o `penalty: l2` do YAML. O teste `test_logistic_pipeline_solver_invalido` voltou a passar.

### ② Problema

O YAML forçava `l1_ratio=0` mesmo quando o código pedia L1. Uma combinação inválida (L1 com `lbfgs`) passava sem erro.

### ③ O que fazer

> [!ok] Concluída. Nada a fazer.

### ④ Pronto quando

- teste: `tests/test_model_pipelines.py::test_logistic_pipeline_solver_invalido` | O teste confirma que um l1_ratio explícito vence o penalty do YAML e que L1 com lbfgs gera erro, em vez de passar em silêncio.

## #65 · test_temporal.py era cópia de test_leakage.py

- prioridade: P3
- situação: resolvida
- estratégia: resolvida
- marco: —
- data ideal: Concluído
- responsável: C
- pessoas: C
- fonte: tests/test_temporal.py; tests/test_leakage.py
- depende de: —
- tags: Testes
- pilar: —
- carga: —
- novo: não
- professores: não

### ① Para entender

> [!ok] Situação atual
> O arquivo atual tem os testes temporais próprios (ordem, frações inválidas, bloqueio do holdout).

### ② Problema

O `test_temporal.py` é uma cópia do `test_leakage.py` sem os testes temporais, e sua docstring diz que os testes temporais estão nele. Os testes de divisão temporal e do G9 estão, na verdade, no `test_leakage.py`. Os testes de vazamento rodam duas vezes.

### ③ O que fazer

> [!ok] Concluída. Nada a fazer.

### ④ Pronto quando

- contem: `tests/test_temporal.py` :: `def test_split_temporal_ordem_correta` | tests/test_temporal.py tem os testes temporais próprios (ordem, frações inválidas, bloqueio do holdout), e não é mais cópia do test_leakage.py.
- teste: `tests/test_temporal.py` | Os testes temporais passam.

## #67 · Rodar a suíte de testes depois das correções

- prioridade: P3
- situação: resolvida
- estratégia: resolvida
- marco: M1
- data ideal: Concluído
- responsável: C
- pessoas: C
- fonte: tests/; PROJECT_COMPLETE_REFERENCE.md e .json
- depende de: —
- tags: Testes, Git
- pilar: —
- carga: —
- novo: não
- professores: não

### ① Para entender

> [!decisão] Decisão de 18/10
> Resolvido em 17/10: `pytest -q -m "not slow"` 100% verde depois das correções (itens 4, 17, 114 e 115).

A referência do projeto foi regenerada em 17/10, mas com "Tests executed: no". Nenhuma execução recente do `pytest` foi registrada.

```
pytest -q
python tools/update_project_reference.py --run-tests
```

### ② Problema

Depois das correções, é preciso rodar a suíte de testes e regenerar o retrato do projeto, que fica desatualizado.

### ③ O que fazer

> [!ok] Concluída como rotina: ver #130 para os momentos de rodar a suíte e regenerar a referência.

### ④ Pronto quando

- teste: `tests/test_split.py` | A suíte rápida de partição passa.
- teste: `tests/test_model_pipelines.py` | A suíte rápida de modelos passa.
- teste: `tests/test_supervised_artifact.py` | A suíte rápida do artefato passa. (Rodar a suíte inteira virou rotina do #130; o painel mostra em REVISÕES qualquer teste falhando.)

## #75 · A descrição do G2 não batia com o que foi executado

- prioridade: P3
- situação: resolvida
- estratégia: resolvida
- marco: —
- data ideal: Concluído
- responsável: A + C
- pessoas: A, C
- fonte: configs/supervised.yaml (gates.G2_janela_temporal)
- depende de: #8
- tags: Gate, Partição, Documentação
- pilar: —
- carga: —
- novo: não
- professores: não

### ① Para entender

> [!ok] Situação atual
> Com a partição estratificada por ano × desfecho (item 8), o G2 passou a descrever o que foi feito. Atenção: o período do G2 (2019–2026) ainda pode mudar com o item 85.

### ② Problema

O G2 está aprovado com a descrição "split aleatório estratificado 70/15/15 por alvo e ano", o que não corresponde ao que foi executado (item 8).

### ③ O que fazer

> [!ok] Concluída: a descrição do G2 no YAML agora diz exatamente o desenho vigente. Pode **✓ Confirmar**.

### ④ Pronto quando

- yaml: `configs/supervised.yaml` :: `gates.G2_janela_temporal.descricao` contem `Particao mestra` | A descrição do G2 no YAML descreve o desenho executado (partição-mestre determinística por grupo), e não mais o sorteio 70/15/15. O conteúdo dos anos é conferido no #102.

## #115 · Mensagem de erro de SRAG_COHORT_KIND fora do contrato do teste

- prioridade: P3
- situação: resolvida
- estratégia: resolvida
- marco: M1
- data ideal: Concluído
- responsável: C
- pessoas: C
- fonte: src/data/cohort_source.py; tests/test_cohort_source.py
- depende de: —
- tags: Código, Testes
- pilar: —
- carga: —
- novo: sim
- professores: não

### ① Para entender

> [!ok] Situação atual
> Resolvido em 17/10. A mensagem de `_resolve_kind` passou a dizer "provisional, final ou auto". A suíte rápida (`pytest -m "not slow"`) ficou 100% verde.

### ② Problema

O comportamento já estava certo; só o texto do erro não batia com o teste.

### ③ O que fazer

> [!ok] Concluída. Nada a fazer.

### ④ Pronto quando

- contem: `src/data/cohort_source.py` :: `deve ser final` | A mensagem de erro de SRAG_COHORT_KIND lista as três opções válidas, como o teste espera.
- teste: `tests/test_cohort_source.py::test_kind_desconhecido_e_rejeitado` | O teste confirma a mensagem para um tipo inválido.

## #116 · Referência do projeto lenta e incompleta para outra IA (schema v6)

- prioridade: P3
- situação: resolvida
- estratégia: resolvida
- marco: M1
- data ideal: Concluído
- responsável: B
- pessoas: B
- fonte: tools/update_project_reference.py
- depende de: —
- tags: Ambiente, Documentação
- pilar: —
- carga: —
- novo: sim
- professores: não

### ① Para entender

> [!ok] Situação atual
> Resolvido em 18/10. O gerador v6 inclui na íntegra todos os .py, notebooks (todas as células), Markdown, YAML e TOML, com catálogo de funções e consumidores, e mostra o progresso em 7 etapas. Histórico Git completo, GitHub CLI, hashes de binários e bundle saíram do padrão.

| Modo | Comando |
|---|---|
| Rápido (dia a dia) | `python tools/update_project_reference.py` |
| Com testes (fim de marco) | `... --run-tests --pytest-args="-m 'not slow'"` |

### ② Problema

A v5 tentava capturar tudo (histórico, fsck, GitHub, hashes) e passou de 15 minutos sem responder. A v4 reduzia notebooks grandes e cortava células acima de 200 linhas.

### ③ O que fazer

> [!ok] Concluída (schema v9, 24/10). Regerar nos marcos (#130).

### ④ Pronto quando

- existe: `tools/update_project_reference.py` | O gerador da referência do projeto existe em tools/.
- contem: `tools/update_project_reference.py` :: `## 6. Full content of every file` | O gerador usa o título "## 6. Full content of every file" (schema v16) para a seção de conteúdo completo, que não colide com os títulos dentro dos notebooks.

## #108 · Item removido (número reservado)

- prioridade: P4
- situação: resolvida
- estratégia: despriorizar
- marco: —
- data ideal: —
- responsável: —
- pessoas: —
- fonte: —
- depende de: —
- tags: —
- pilar: —
- carga: —
- novo: não
- professores: não
- removido: impossibilidade material de recuperar a gravação

## #142 · Gerar o artefato supervisionado pelo src (uma função, um comando); o B_07 só chama

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M2
- data ideal: 28/10
- responsável: Pessoa B (dona; revisão cruzada sem edição concorrente)
- pessoas: B
- fonte: Replanejamento de 27/10; referência de 27/10 (artefato sem id_registro nem regiao_residencia; previsões só com indice_original)
- depende de: #102
- tags: Dados/Coorte, Partição, Código
- pilar: Eficiência + Performance
- carga: 5
- novo: sim
- professores: não
- arquivos: src/data/supervised_artifact.py, src/data/split.py, src/features/engineering.py, tests/test_supervised_artifact.py, notebooks/B/B_07_supervisionado_pilotos.ipynb

### ① Para entender

**A coorte definitiva já é gerada pelo `src`** (`src/data/final_cohort*.py` e `cohort_*.py`, com contrato, auditoria e manifesto). O que ainda está só em notebook é o passo seguinte: transformar a coorte em **artefato de modelagem** (features, `group_id`, região, os seis blocos e o manifesto). Hoje esse passo vive dentro do B_07, misturado com os pilotos.

Lógica que define os dados de treino e teste em notebook é frágil: depende da ordem das células, não tem teste e não pode ser chamada por outros notebooks. O padrão do projeto é "lógica definitiva no `src` com teste; notebook só orquestra". Quase tudo já existe no `src` (`montar_features`, `criar_particao_mestra`, `persist_supervised_artifact`): falta **uma função que encadeie** essas peças, mais o que hoje só está no B_07 (região e grupo).

O artefato atual também não tem `id_registro` nem `regiao_residencia`, e as previsões do piloto só têm `indice_original`. Sem identificador estável, nenhuma análise da Fase E consegue juntar previsões e variáveis.

### ② Problema

A geração do artefato está num notebook, sem teste e sem identificador. Isso trava a Fase E e soa como improviso para a banca.

### ③ O que fazer

> [!atenção] Revisão de 28/10: antes de gerar o artefato, resolva o #102
> Os YAMLs agora mandam 2019 para `test_pandemic`. Gerar o artefato antes da decisão produz uma partição que pode ter de ser refeita. O artefato atual (24/10) tem 2019 no desenvolvimento, `grupo_split` em vez de `group_id`, e não tem `id_registro` nem `regiao_residencia`. As saídas salvas do B_07 versionado são da coorte provisória ("Tipo efetivo: provisional").

> [!decisão] Replanejamento de 27/10: exploração completa antes do treino
> Tudo o que pode mudar variáveis, representação, alvo ou leitura do modelo roda **antes do ajuste fino (G6)**: primeiro a exploração sem modelo, depois o diagnóstico com o piloto padrão no `val_tune`, depois o ponto de decisão (#140, 30/10, manhã). Só então ajuste, calibração, limiar e teste.

**Dono:** Pessoa B · **Prazo:** 27/10 (terça), dia inteiro: artefato até o fim da tarde; previsões do piloto até a noite · **Esforço estimado:** ≈ 5 h (inclui a execução) · **Revisão:** Pessoa C (15 min, só o commit)

> [!decisão] Nível mínimo de boas práticas (27/10)
> Uma função, um teste com dados inventados, um manifesto com hash. **Sem** CLI própria, sem novos gates e sem refatorar o B_07 inteiro: o B_07 continua rodando os pilotos, só que chamando a função.

#### Passo a passo
1. **Região** em `src/features/engineering.py`: `regiao_residencia(sg_uf) -> pd.Series` (categoria). Norte AC AP AM PA RO RR TO; Nordeste AL BA CE MA PB PE PI RN SE; Centro-Oeste DF GO MT MS; Sudeste ES MG RJ SP; Sul PR RS SC; vazio ou inválido → `AUSENTE`. Copie o mapeamento que já está no B_07.
2. **Grupo** em `src/data/split.py`: `criar_group_id(df)` → `nu_notific` sem espaços; vazio → `"sem_notific:" + id_registro`. Copie a lógica do B_07 (inclusive a remoção dos grupos que cruzam períodos, devolvendo a contagem).
3. **A função** em `src/data/supervised_artifact.py`: `gerar_artefato_supervisionado(root, *, cohort_kind="final", exportar_particao=True) -> dict`. Ela faz, nesta ordem, só chamando o que existe:
   - lê da `coorte_final.parquet` só as colunas necessárias (entradas de features, as 31 + contexto + gravidade, alvo, `sg_uf`, `nu_notific`, `id_registro`, `fator_risc`);
   - `montar_features`; `regiao_residencia`; `criar_group_id`;
   - `criar_particao_mestra(seed=42, ...)` lendo `temporal.blocos` do YAML;
   - `persist_supervised_artifact(..., cohort_kind="final")` com `id_registro`, `group_id`, `regiao_residencia`, `sg_uf`, `faixa_etaria`, `sexo_categoria`, `ano_internacao`, `bloco_mestre`, `fator_risc` em `audit_columns`;
   - grava `data/analytical/partitions_master.parquet` (`id_registro`, `group_id`, `bloco_mestre`, `ano_internacao`, `alvo_obito_srag`) e `manifesto_particao.json`;
   - `del` + `gc.collect()` e devolve um resumo (linhas por bloco, prevalência, linhas excluídas).
4. **Um teste** em `tests/test_supervised_artifact.py` com 40 linhas inventadas e uma pasta temporária: os arquivos são criados; nenhum `group_id` em dois blocos; `id_registro` presente. Marque como rápido.
5. **B_07:** substitua as células de grupo, região, partição e persistência por uma célula que chama `gerar_artefato_supervisionado(ROOT_DIR)` e mostra o resumo. Os pilotos continuam como estão, lendo o artefato.
6. **Previsões do piloto com identificador:** no B_07, salve `outputs/final/predicoes_val_tune_piloto.parquet` com `id_registro`, `bloco_mestre`, `ano_internacao`, `regiao_residencia`, `sg_uf`, `faixa_etaria`, `sexo_categoria`, `y`, `prob_logistica`, `prob_boosting` para `val_tune` (e `val_cal`/`val_meas`, se custar pouco).
7. Rode o B_07 com `$env:SRAG_COHORT_KIND="final"` e confira os números de 24/10 (train_ref 556.462; val_tune 39.748; val_cal 39.746; val_meas 39.749; test_ref 119.245; test_pandemic 2.915.829; 4 fora).
8. `.\.venv\Scripts\python.exe -m pytest -m "not slow" -q` e commit: `feat: gera artefato supervisionado pelo src com id_registro e regiao [done:#142]`.
9. Avise no #131, #135, #51, #52, #55 e #110.

#### Pronto quando
Função e teste no `src`, B_07 chamando a função com saídas da definitiva, `partitions_master.parquet` e previsões do piloto com `id_registro`.

#### Se apertar
Prioridade: passos 3, 5, 6 e 7. Os passos 1 e 2 podem começar como funções privadas dentro de `supervised_artifact.py` e ser movidas depois.

### ④ Pronto quando

- define: `src/data/supervised_artifact.py` :: `gerar_artefato_supervisionado` | A função gerar_artefato_supervisionado existe em src/data/supervised_artifact.py e encadeia leitura enxuta da coorte_final, montar_features, região, grupo, criar_particao_mestra e persistência.
- define: `src/features/engineering.py` :: `regiao_residencia` | A função regiao_residencia (UF → Norte, Nordeste, Centro-Oeste, Sudeste, Sul; vazio ou inválido → AUSENTE) existe em src/features/engineering.py.
- define: `src/data/split.py` :: `criar_group_id` | A função criar_group_id existe em src/data/split.py.
- contem: `tests/test_supervised_artifact.py` :: `gerar_artefato_supervisionado` | Há teste rápido com linhas inventadas e pasta temporária: arquivos criados, nenhum group_id em dois blocos e id_registro presente.
- teste: `tests/test_supervised_artifact.py` | Os testes do artefato passam.
- contem: `notebooks/B/B_07_supervisionado_pilotos.ipynb` :: `gerar_artefato_supervisionado(` | O B_07 chama gerar_artefato_supervisionado em vez de montar grupo, região, partição e persistência dentro do notebook.
- existe: `data/analytical/partitions_master.parquet` | A partição-mestre (id_registro, group_id, bloco_mestre, ano_internacao, alvo) foi gravada em data/analytical/partitions_master.parquet.
- existe: `outputs/final/predicoes_val_tune_piloto.parquet` | As previsões do piloto no val_tune com id_registro estão em outputs/final/predicoes_val_tune_piloto.parquet.

## #143 · Limpeza mínima do repositório: remover o que não leva a lugar nenhum

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M6
- data ideal: 31/10
- responsável: Pessoa B (0,5 h) + Pessoa C (0,25 h) + Pessoa A (0,25 h)
- pessoas: B, C, A
- fonte: Referência de 27/10: relatório de atenção (A18, A74, A136) e inventário de notebooks
- depende de: #142
- tags: Código, Git, Documentação
- pilar: Eficiência + Percepção acadêmica
- carga: 1
- novo: sim
- professores: não

### ① Para entender

Vários arquivos foram criados para uma fase que já passou (coorte provisória, divisão antiga, cópias de segurança, testes de ambiente). Eles não alimentam nada do caminho atual e, na banca, obrigariam a explicar "fizemos para usar depois". O Git guarda tudo no histórico: remover não perde trabalho.

**Fica:** tudo o que gera ou documenta a coorte definitiva, o artefato, os modelos e a avaliação; `src/protocolo/verificacoes.py` (usado pela paridade da coorte, pelo B_05 e pelo B_06); `src/evaluation/temporal.py` (já documentado como ferramenta de sensibilidade); os notebooks A_03 e A_04 (auditoria do protocolo da Pessoa A, que passam a rodar com o caminho corrigido no #73).

### ② Problema

> [!atenção] Replanejamento de 31/10 · versão 2 (entrega em 04/11)
> Sábado, 17h às 18h, **em paralelo** ao #144 (não espera a suíte). O passo 7 da Pessoa C mostra as 4 falhas conhecidas até o #144 entrar: ignore-as, o que importa é não aparecer falha nova. Os notebooks A6 e A_15 **não** são apagados aqui.

Arquivos sem papel no projeto final confundem a banca e as IAs que trabalham no repositório.

### ③ O que fazer

> [!decisão] Replanejamento de 31/10
> Três commits pequenos, um por pessoa, hoje à tarde, **em paralelo** ao #144. Só remoções e uma linha no README. Quem remove confere antes com busca no repositório que nada o chama.

**Dono:** Pessoas B, C e A · **Prazo:** 31/10 (sábado), 17h às 18h · **Esforço estimado:** B ≈ 30 min · C ≈ 15 min · A ≈ 15 min · **Começa quando:** imediatamente

#### Pessoa B (30 min)
1. `git pull`. Apague, se existirem, `notebooks/B/B_07_supervisionado_pilotos.antes_generalizacao_coorte.ipynb` (cópia de segurança), `notebooks/B/___provisorio_construcao_coorte_b.ipynb` (a coorte definitiva é gerada pelo construtor do `src`) e `notebooks/B/B_10_consolidacao_shortlist_transicao_coorte.ipynb` (ponte da fase provisória).
2. Apague `data/split.py` (cópia antiga de `src/data/split.py` dentro da pasta de dados) e a pasta `.scripts/` (`read_outputs.py` é igual a `tools/read_outputs.py`; os outros dois foram usos únicos).
3. Para a banca: o relatório precisa de **uma frase** dizendo que a seleção de variáveis foi feita numa coorte provisória, congelada antes da definitiva (#98); o notebook que a construiu sai do pacote porque a definitiva a substitui.
4. Commit: `chore: remove notebooks e scripts da fase provisoria`.

#### Pessoa C (15 min)
5. Apague `notebooks/C/C_02_smoke_test.ipynb` (os testes automáticos cobrem o ambiente; `build_logistic_pipeline` já exige scikit-learn ≥ 1.8).
6. Em `src/data/split.py`, remova `criar_particoes_agrupadas` (divisão 70/15/15 antiga, substituída por `criar_particao_mestra`) e os testes dela em `tests/test_split.py`. Antes, procure usos: `Get-ChildItem -Recurse -Include *.py,*.ipynb | Select-String "criar_particoes_agrupadas"`. Só pode restar a definição e os testes.
7. `.\.venv\Scripts\python.exe -m pytest -m "not slow" -q` (as 4 falhas de `test_regras_pessoa_a.py` são do #144: ignore-as; qualquer outra falha é sua). Commit: `chore: remove divisao antiga e smoke test`.
8. Apague localmente `outputs/backup_C2_provisorio/` e `outputs/backup_supervisionado_provisorio/` (se não forem rastreados, nada vai para o Git).

#### Pessoa A (15 min)
9. Apague `notebooks/A/teste` (se existir), `notebooks/A/A_08_desenho_experimental.ipynb`, `notebooks/A/A_09_split_aleatorio_cenarios.ipynb` e `notebooks/A/A_14_decisao_candidatos.ipynb` (substituídos pelo desenho de 18/10, pelas ablações e pelo ajuste fino). A lição do A_09 vai para o relatório pelo #89; **não** apague A_03, A_04, A6 e A_15.
10. Commit: `chore: remove notebooks A substituidos`.

#### Pronto quando
Os três commits estiverem no `main` e a suíte rápida passar. Avise no #146 que a limpeza estrutural terminou.

### ④ Pronto quando

- nao-existe: `notebooks/B/B_07_supervisionado_pilotos.antes_generalizacao_coorte.ipynb` | Pessoa B: a cópia de segurança do B_07 foi apagada.
- nao-existe: `notebooks/B/___provisorio_construcao_coorte_b.ipynb` | Pessoa B: o construtor da coorte provisória foi apagado (substituído pelo construtor do src).
- nao-existe: `notebooks/B/B_10_consolidacao_shortlist_transicao_coorte.ipynb` | Pessoa B: o B_10 (ponte da fase provisória) foi apagado.
- nao-existe: `data/split.py` | Pessoa B: a cópia antiga de split.py dentro de data/ foi apagada.
- nao-existe: `notebooks/C/C_02_smoke_test.ipynb` | Pessoa C: o C_02 foi apagado (substituído pelos testes automáticos).
- nao-define: `src/data/split.py` :: `criar_particoes_agrupadas` | Pessoa C: a divisão 70/15/15 antiga (criar_particoes_agrupadas) saiu de src/data/split.py, junto com os testes dela.
- nao-existe: `notebooks/A/A_09_split_aleatorio_cenarios.ipynb` | Pessoa A: o A_09 foi apagado (a lição vai para o relatório pelo #89).
- nao-existe: `notebooks/A/A_08_desenho_experimental.ipynb` | Pessoa A: o A_08 foi apagado.
- nao-existe: `notebooks/A/A_14_decisao_candidatos.ipynb` | Pessoa A: o A_14 foi apagado.
- teste: `tests/test_split.py` | A suíte de partição passa depois das remoções.

## #141 · "Fatores de risco" no SIVEP: as comorbidades em branco são "não"? (verificar antes do treino)

- prioridade: P1
- situação: aberta
- estratégia: explorar
- marco: M3
- data ideal: 27/10
- responsável: Pessoa A (verificação) · Pessoa C (implementa a recodificação, se aprovada)
- pessoas: A, C
- fonte: B_06 na coorte definitiva (27/10): eda_02_preenchimento_por_variavel_ano, eda_02_ausencia_por_desfecho; coluna fator_risc presente em coorte_final.parquet e ausente do dicionário
- depende de: —
- tags: Dados/Coorte, Features, Vazamento, Metodologia
- pilar: Valor científico-acadêmico + Performance
- carga: 3
- novo: sim
- professores: não

### ① Para entender

A rodada do B_06 na coorte definitiva (27/10) mostrou que as **12 comorbidades estão em branco em 61% a 69% das fichas** de 2023–2025 (asma 69%, cardiopatia 66%), muito mais do que os sintomas (dispneia 13%). E o branco é **muito mais comum nas curas** do que nos óbitos (cardiopatia: 59,8% × 38,8%; diferença de 13 a 21 pontos percentuais em todas as comorbidades).

Na ficha do SIVEP há uma pergunta-mãe: **"Possui fatores de risco/comorbidades?"** (`fator_risc`). Em geral, a lista de comorbidades só é preenchida quando a resposta é "sim". Se for isso, **o branco numa comorbidade, quando `fator_risc` = não, significa "não tem"**, e não "não informado".

| Se a hipótese se confirmar | Consequência |
|---|---|
| O branco das comorbidades é, na maior parte, "não tem" (pulo da ficha) | Hoje o modelo recebe `AUSENTE` onde deveria receber "não": a categoria AUSENTE passa a carregar "não tem comorbidade", que está ligada a menos óbitos |
| Parte do "viés de documentação" (fichas de óbito mais completas) é, na verdade, a regra de preenchimento da ficha | Muda a leitura do #52 e o texto de limitações |
| A recodificação muda a representação de 12 variáveis do modelo | Precisa ser decidida **antes do ajuste fino** |

`fator_risc` existe na `coorte_final.parquet`, mas **não está no dicionário de variáveis**, nem nas features. Ela é informação da admissão (não é vazamento).

### ② Problema

Se o branco das comorbidades for "não tem", o modelo e o clustering estão tratando a principal informação clínica de forma enviesada, e o "viés de documentação" pode ser em parte um artefato da forma de codificar. Isso precisa ser verificado antes de treinar.

### ③ O que fazer

> [!decisão] Replanejamento de 27/10: exploração completa antes do treino
> Tudo o que pode mudar variáveis, representação, alvo ou leitura do modelo roda **antes do ajuste fino (G6)**: primeiro a exploração sem modelo, depois o diagnóstico com o piloto padrão no `val_tune`, depois o ponto de decisão (#140, 30/10, manhã). Só então ajuste, calibração, limiar e teste.

**Dono:** Pessoa A (verificação) · Pessoa C (implementação, se aprovada) · **Prazo:** A: 27/10 (terça), manhã e tarde · C: 27/10, noite · **Esforço estimado:** A ≈ 2 h · C ≈ 1 h · **Revisão:** Pessoa B (leitura das tabelas)

#### Parte da Pessoa A (27/10, manhã e tarde): verificar
1. Num notebook novo e curto, `notebooks/A/A_15_fator_risco.ipynb`, leia da `coorte_final.parquet` só `fator_risc`, as 12 comorbidades, `puerpera`, `ano_internacao` (ou `dt_interna`) e `alvo_obito_srag` (`pd.read_parquet(columns=[...])`).
2. Veja os valores de `fator_risc` (`value_counts(dropna=False)`): podem aparecer `1`/`2`/`9`, `S`/`N` ou texto, dependendo do ano. Anote o mapeamento.
3. **Tabela 1:** `fator_risc` × "comorbidade em branco" para cada comorbidade (proporção de branco dentro de cada valor de `fator_risc`), por ano. Hipótese confirmada se, com `fator_risc` = não, o branco for quase 100%, e com `fator_risc` = sim, bem menor.
4. **Tabela 2:** mortalidade por `fator_risc` (sim, não, ignorado, branco), por ano.
5. **Tabela 3:** refaça a "ausência por desfecho" só entre fichas com `fator_risc` = sim. Se a diferença de 13 a 21 pontos percentuais cair muito, boa parte do "viés de documentação" era a regra da ficha.
6. Salve `outputs/tables/eda_02_fator_risc_*.csv` até as 18h e comente aqui as três tabelas em poucas linhas, com a proposta abaixo.

#### Proposta de regra (se a hipótese se confirmar)
- Comorbidade em branco **e** `fator_risc` = não → "2" (não).
- Comorbidade em branco **e** `fator_risc` = sim, ignorado ou branco → continua `AUSENTE`.
- Incluir `fator_risc` como variável do modelo? **Não por padrão**: ele é redundante com as comorbidades recodificadas. Decidir no #140 com a ablação.

#### Parte da Pessoa C (27/10, noite): implementar, se a Pessoa A confirmar
7. Função `recodificar_comorbidades_por_fator_risco(df)` em `src/features/engineering.py`, chamada por `montar_features` (assim vale para supervisionado e não supervisionado), com teste de 4 linhas (os quatro casos acima).
8. Incluir no #54 a linha "P com comorbidades recodificadas" × "P atual", com o mesmo piloto.

#### Pronto quando
As três tabelas existirem, a decisão estiver no #140 e, se aprovada, a função e a ablação estiverem prontas antes do G6.

### ④ Pronto quando

- existe: `notebooks/A/A_15_fator_risco.ipynb` | O notebook curto da verificação (A_15_fator_risco) existe.
- existe: `outputs/tables/eda_02_fator_risc_comorbidades.csv` | As tabelas fator_risc × comorbidade em branco (e as de mortalidade e ausência por desfecho) estão em outputs/tables/eda_02_fator_risc_*.csv.
- manual: | As três tabelas foram comentadas neste card e a decisão (recodificar ou não) está no #140.
- define: `src/features/engineering.py` :: `recodificar_comorbidades_por_fator_risco` | Se a regra for aprovada: a função recodificar_comorbidades_por_fator_risco existe em src/features/engineering.py e é chamada por montar_features, com teste dos quatro casos.

## #144 · Restaurar a suíte rápida e os gates G1, G2, G4 e G5 (regressões de 29/10)

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M1
- data ideal: 31/10
- responsável: Pessoa B (1,25 h)
- pessoas: B
- fonte: Diagnóstico de 31/10 (pytest rápido e auditoria do commit 1e02321)
- depende de: —
- tags: Código, Testes, Gate
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1.25
- novo: sim
- professores: não
- arquivos: configs/supervised.yaml, tests/test_invariantes_protocolo.py, tests/test_config.py, tools/medir_notebook.py

### ① Para entender

A suíte rápida do projeto (`pytest -m "not slow"`) tinha 383 testes verdes em 30/10 às 11h. No commit `1e02321` (30/10, 17h) ela passa a ter **4 falhas**, e **quatro gates do YAML** estão com o valor errado. Os dois problemas vieram de edições do #73 (gates: 29/10, 21h21; função: 30/10, depois das 11h). São correções de poucos minutos, mas bloqueiam três frentes: a Pessoa C não consegue rodar a suíte para validar o #132, os notebooks A_03 e A_04 quebrariam ao exportar o dataset, e o checklist do G9 exige G1 e G2 aprovados.

| O que quebrou | Onde | Efeito |
|---|---|---|
| `_analytical_path` definida **duas vezes**; a segunda (edição do #73 de 30/10) tem o corpo `nome = ...` seguido de `...` e devolve `None` | `src/protocolo/verificacoes.py`, linhas 503 e 514 | `AttributeError: 'NoneType' object has no attribute 'with_name'` em `a3_split_aleatorio_cenario` (linha 814): 4 testes de `tests/test_regras_pessoa_a.py` falham |
| `status: responsavel` em vez de `aprovado` em G1, G2, G4 e G5 | `configs/supervised.yaml`, commit `de8113c` (29/10, 21h21, mensagem "73") | `gate_aprovado()` devolve falso; os cards #77, #85 e #120 voltam a ✗ no verificador |

> [!exemplo] Por que a segunda definição vence
> Em Python, quando duas funções têm o mesmo nome no mesmo arquivo, a **última** substitui a primeira. A versão boa (linha 503) existe, mas nunca é chamada.

### ② Problema

> [!decisão] Replanejamento de 01/11: a Pessoa B assume este card
> Era da Pessoa A (1 h 15). É o primeiro da fila de hoje: dele dependem #73, #70, #145, #148, #149 e #87, e ele é pré-requisito do G9 (#81). O conteúdo não mudou: as 4 falhas e os 4 gates continuam como no diagnóstico de 30/10. A data ideal continua 31/10 (atrasado).

> [!atenção] Replanejamento de 31/10 · versão 2 (entrega em 04/11)
> Primeira tarefa desta tarde. Acrescenta a **ferramenta de medição de tempo e memória** (passo 11), que B e C usam ainda hoje, e fecha o #87. Nada mais mudou: as 4 falhas e os 4 gates continuam como no diagnóstico de 30/10.

Evidência do diagnóstico de 30/10, 22h12 (`diagnostico_planejamento_srag_2026-10-30.txt`):

- `FAILED tests/test_regras_pessoa_a.py::test_cenario_sem_2020_2021_exclui_os_anos`
- `FAILED tests/test_regras_pessoa_a.py::test_benchmark_aleatorio_x_temporal_e_comparacao`
- `FAILED tests/test_regras_pessoa_a.py::test_graficos_do_split_sao_gerados`
- `FAILED tests/test_regras_pessoa_a.py::test_export_e_vazamento_com_category`

Os quatro têm o mesmo erro (`verificacoes.py:814`, `base = _analytical_path(cfg)` devolve `None`). O `git status` está limpo, ou seja, o defeito está no commit e vale para todos.

Há ainda um efeito colateral: o caminho correto (`Path(C.ANALYTICAL_DIR) / nome`) faz esses testes gravarem `dataset_supervisionado_<cenário>.meta.json` na pasta real `data/analytical/` (já existem dois arquivos assim). Teste não deve escrever na pasta de dados do projeto.

### ③ O que fazer

> [!decisão] Replanejamento de 31/10
> Primeira tarefa do sábado, antes de qualquer outra: sem a suíte verde ninguém consegue validar mudanças no `src`.

**Dono:** Pessoa B (assumiu em 01/11; era da Pessoa A) · **Prazo:** atrasado desde 31/10 (sábado, 16h às 17h15); fazer primeiro, em 01/11 · **Esforço estimado:** ≈ 1 h 15 · **Começa quando:** imediatamente

#### Passo a passo
1. `git pull` e reproduza as falhas com um comando só: `.\.venv\Scripts\python.exe -m pytest tests/test_regras_pessoa_a.py -q -x`. Deve falhar em `test_cenario_sem_2020_2021_exclui_os_anos` com o `AttributeError` descrito acima.
2. Em `src/protocolo/verificacoes.py`, localize as duas definições com `Select-String -Path src\protocolo\verificacoes.py -Pattern "^def _analytical_path"` (devem aparecer 2). **Apague a segunda inteira** (da linha `def _analytical_path(cfg: dict) -> Path:` com o docstring "Caminho do dataset PROVISÓRIO do fluxo A" até a linha `...`) e **substitua a primeira** pelo bloco abaixo, que junta o docstring novo ao corpo que funciona:

```python
def _analytical_path(cfg: dict) -> Path:
    """Caminho do dataset provisório do fluxo A (notebooks de coorte e de qualidade).

    Não é o artefato oficial supervisionado, gerado só por
    ``src/data/supervised_artifact.py`` (``DATASET_NAME``). Se ``dataset_analitico.path``
    apontar para o mesmo arquivo do artefato, os notebooks A o sobrescrevem e o hash
    do manifesto deixa de bater.
    """
    nome = Path(cfg["dataset_analitico"]["path"]).name
    try:
        from src.utils import config as C  # noqa: N812

        return Path(C.ANALYTICAL_DIR) / nome
    except Exception as e:  # noqa: BLE001 - fallback intencional: nem toda base tem src.utils
        print(f"[_analytical_path] fallback ({type(e).__name__}: {e}) -> {cfg['dataset_analitico']['path']}")
        return Path(cfg["dataset_analitico"]["path"])
```

   Confira: `Select-String` agora devolve **1** ocorrência e a linha `...` sumiu da função.
3. Impeça que os testes escrevam em `data/analytical/`. No topo de `tests/test_regras_pessoa_a.py`, logo depois dos imports, acrescente:

```python
@pytest.fixture(autouse=True)
def _analytical_dir_temporario(tmp_path, monkeypatch):
    """Os testes gravam datasets de demonstração: nunca na pasta de dados do projeto."""
    from src.utils import config as C  # noqa: N812

    monkeypatch.setattr(C, "ANALYTICAL_DIR", tmp_path)
```

   Apague os arquivos que testes anteriores deixaram em `data/analytical/`: `dataset_supervisionado_todos_2019_2025.*` e `dataset_supervisionado_sem_2020_2021.*` (são só locais; a pasta é ignorada pelo Git).
4. Teste que impede a repetição do defeito, no mesmo arquivo de testes:

```python
def test_analytical_path_devolve_caminho(cfg):
    assert isinstance(v._analytical_path(cfg), Path)


def test_src_sem_funcoes_duplicadas():
    import ast

    for arquivo in Path(v.__file__).resolve().parents[1].rglob("*.py"):
        arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
        nomes = [n.name for n in arvore.body if isinstance(n, ast.FunctionDef)]
        repetidos = sorted({n for n in nomes if nomes.count(n) > 1})
        assert not repetidos, f"{arquivo.name}: funções definidas mais de uma vez: {repetidos}"
```
5. Gates. Em `configs/supervised.yaml`, nos blocos `G1_definicao_alvo_features`, `G2_janela_temporal`, `G4_baseline` e `G5_pilotos` (linhas 503, 512, 520 e 525 no commit `1e02321`), troque `status: responsavel` por `status: aprovado`. Não mexa em `aprovado_por`, nas datas nem em G6 a G9 (continuam `pendente`).
6. Teste do YAML (acrescente em `tests/test_config.py`):

```python
def test_gates_historicos_aprovados():
    from pathlib import Path

    import yaml

    caminho = Path(__file__).resolve().parents[1] / "configs" / "supervised.yaml"
    gates = yaml.safe_load(caminho.read_text(encoding="utf-8"))["gates"]
    for nome in ("G1_definicao_alvo_features", "G2_janela_temporal", "G4_baseline", "G5_pilotos"):
        assert gates[nome]["status"] == "aprovado", nome
    for nome in ("G6_finalistas_tuning", "G7_calibracao", "G8_limiar", "G9_holdout"):
        assert gates[nome]["status"] in {"pendente", "aprovado", "executado"}, nome
```
7. Valide tudo com **um** comando: `.\.venv\Scripts\python.exe -m pytest -m "not slow" -q; .\.venv\Scripts\python.exe -c "import yaml; g=yaml.safe_load(open('configs/supervised.yaml',encoding='utf-8'))['gates']; print({k: v['status'] for k, v in g.items()})"`. Esperado: 0 falhas (os 383 de antes mais 3 testes novos) e G1, G2, G4, G5 `aprovado`; G6 a G9 `pendente`.
8. Registre em `docs/decisoes.md` uma entrada curta (§29.27, 31/10): "correção de duas regressões de 29/10: função duplicada em `verificacoes.py` e `status` dos gates G1, G2, G4 e G5 trocado por engano; sem mudança de método".
9. Commit: `fix: restaura _analytical_path e o status dos gates G1, G2, G4 e G5 [done:#144] [done:#87]`. Depois, no painel, **🔄 Atualizar, auditar e validar**: #77, #85 e #120 devem voltar a ✓ no critério do YAML.
10. Avise B e C, no grupo, que a suíte está verde e que `tools/medir_notebook.py` (passo 11) já está no `main`: os dois o usam ainda hoje.
11. **Ferramenta de medição** (usada por todos até 04/11). Crie `tools/medir_notebook.py` com o código abaixo (testado: soma o consumo do processo e dos filhos, acrescenta uma linha a `outputs/final/performance_notebooks.csv` e devolve código de saída 2 se passar do limite de memória). Commit: `feat: mede tempo e pico de memoria dos notebooks`.

```python
r"""Executa um notebook em processo isolado e mede tempo e pico de memória.

Uso (na raiz do repositório):
    .\.venv\Scripts\python.exe tools/medir_notebook.py notebooks/<nome>.ipynb
    .\.venv\Scripts\python.exe tools/medir_notebook.py notebooks/<nome>.ipynb --salvar-no-lugar

Sem --salvar-no-lugar, a cópia executada vai para outputs/notebooks/<nome>_executado.ipynb
e o notebook original não muda. Com --salvar-no-lugar, o próprio arquivo é regravado
com as saídas (use só na execução final de cada notebook).
A linha de resultado é acrescentada a outputs/final/performance_notebooks.csv.
"""
from __future__ import annotations

import argparse
import csv
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import psutil

RAIZ = Path(__file__).resolve().parents[1]
TABELA = RAIZ / "outputs" / "final" / "performance_notebooks.csv"
CAMPOS = ["quando", "notebook", "duracao_s", "pico_rss_mb", "codigo_saida", "python", "limite_mb", "limite_s"]


def _rss_arvore_mb(proc: psutil.Process) -> float:
    """Soma o RSS do processo e de todos os filhos (o kernel do Jupyter é um filho)."""
    total = 0
    try:
        for p in [proc, *proc.children(recursive=True)]:
            try:
                total += p.memory_info().rss
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
    return total / 1_048_576


def medir_comando(comando: list[str], intervalo: float = 0.25) -> dict:
    """Roda `comando` e devolve duração, pico de RSS (MB, árvore de processos) e código de saída."""
    t0 = time.perf_counter()
    filho = subprocess.Popen(comando, cwd=RAIZ)
    proc, pico = psutil.Process(filho.pid), 0.0
    while filho.poll() is None:
        pico = max(pico, _rss_arvore_mb(proc))
        time.sleep(intervalo)
    return {"duracao_s": round(time.perf_counter() - t0, 1), "pico_rss_mb": round(pico), "codigo_saida": filho.returncode}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("notebook", type=Path)
    ap.add_argument("--salvar-no-lugar", action="store_true")
    ap.add_argument("--limite-mb", type=int, default=6144, help="pico aceitável de memória (padrão 6 GB)")
    ap.add_argument("--limite-s", type=int, default=1200, help="duração aceitável (padrão 20 min)")
    args = ap.parse_args()

    nb = (RAIZ / args.notebook).resolve() if not args.notebook.is_absolute() else args.notebook
    if not nb.is_file():
        print(f"Notebook não encontrado: {nb}")
        return 1
    cmd = [sys.executable, "-m", "jupyter", "nbconvert", "--to", "notebook", "--execute",
           "--ExecutePreprocessor.timeout=-1", str(nb)]
    if args.salvar_no_lugar:
        cmd.append("--inplace")
    else:
        saida = RAIZ / "outputs" / "notebooks"
        saida.mkdir(parents=True, exist_ok=True)
        cmd += ["--output", f"{nb.stem}_executado", "--output-dir", str(saida)]

    r = medir_comando(cmd)
    linha = {"quando": datetime.now().isoformat(timespec="seconds"), "notebook": nb.name, **r,
             "python": sys.version.split()[0], "limite_mb": args.limite_mb, "limite_s": args.limite_s}
    TABELA.parent.mkdir(parents=True, exist_ok=True)
    novo = not TABELA.exists()
    with TABELA.open("a", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        if novo:
            w.writeheader()
        w.writerow(linha)

    ok_mem, ok_t = r["pico_rss_mb"] <= args.limite_mb, r["duracao_s"] <= args.limite_s
    print(f"{nb.name}: {r['duracao_s']:.0f} s · pico {r['pico_rss_mb']:,} MB · saída {r['codigo_saida']} "
          f"· memória {'OK' if ok_mem else 'ACIMA DO LIMITE'} · tempo {'OK' if ok_t else 'ACIMA DO LIMITE'}")
    return 0 if r["codigo_saida"] == 0 and ok_mem else 2


if __name__ == "__main__":
    sys.exit(main())
```

### ④ Pronto quando

- nao-existe: `src/protocolo/verificacoes.py` | O arquivo que tinha a função _analytical_path foi removido junto com o fluxo A (#154): a duplicação deixou de existir.
- contem: `tests/test_invariantes_protocolo.py` :: `test_src_sem_funcoes_duplicadas` | Há teste que impede funções de topo repetidas em qualquer arquivo de src/ (veio do antigo test_regras_pessoa_a.py).
- teste: `tests/test_invariantes_protocolo.py` | Os testes rápidos de tests/test_invariantes_protocolo.py passam (as quatro falhas de 30/10 eram do antigo test_regras_pessoa_a.py, removido no #154).
- teste: `tests/test_config.py::test_gates_historicos_aprovados` | O teste que confere G1, G2, G4 e G5 aprovados passa.
- yaml: `configs/supervised.yaml` :: `gates.G1_definicao_alvo_features.status` = `aprovado` | O G1 voltou a aprovado.
- yaml: `configs/supervised.yaml` :: `gates.G2_janela_temporal.status` = `aprovado` | O G2 voltou a aprovado.
- yaml: `configs/supervised.yaml` :: `gates.G4_baseline.status` = `aprovado` | O G4 voltou a aprovado.
- yaml: `configs/supervised.yaml` :: `gates.G5_pilotos.status` = `aprovado` | O G5 voltou a aprovado.
- manual: | O pytest rápido completo (-m "not slow") terminou com 0 falhas e a entrada de 31/10 está no docs/decisoes.md.
- existe: `tools/medir_notebook.py` | A ferramenta de medição de tempo e memória dos notebooks existe em tools/medir_notebook.py.

## #145 · Medir e reduzir tempo e pico de memória dos notebooks da entrega

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 05/11
- responsável: Pessoa B (0,75 h) + Pessoa C (0,75 h) + Pessoa A (0,25 h)
- pessoas: B, C, A
- fonte: Diagnóstico de 31/10: inventário dos notebooks e manifesto do artefato
- depende de: #144
- tags: Performance, Notebook, Memória
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1.75
- novo: sim
- professores: não
- arquivos: tools/medir_notebook.py, outputs/final/performance_notebooks.csv
- removido: removido na revisão de 03/11 (v3.2): picos já reduzidos em 01/11; o medidor do #126 registra tempo e memória da execução limpa

### ① Para entender

O projeto precisa rodar em **um computador comum** (16 GB de memória, sem GPU). Nenhum notebook pode ter um pico que obrigue a máquina a usar disco ou feche o kernel.

Números do repositório que mostram onde mora o risco:

| Fato | Valor |
|---|---|
| Coorte definitiva (`coorte_final.parquet`) | 3.884.728 linhas × 43 colunas |
| Artefato supervisionado | 3.710.779 linhas × 46 colunas |
| `train_ref` (treino) | 556.462 linhas |
| `val_tune`, `val_cal`, `val_meas` | ≈ 39.700 linhas cada |
| `test_ref` (Teste A) | 119.245 linhas |
| **`test_pandemic` (2020–2022, entra no Teste B)** | **2.915.829 linhas** (26,4% de óbitos) |
| B_06 | 148 células, 120 de código |

O Teste B é o maior pico em potencial: sem cuidado, o C_16 carregaria quase 3 milhões de linhas com 46 colunas, passaria um pré-processador com one-hot por cima e ainda repetiria um bootstrap de 1.000 réplicas sobre esse vetor.

> [!decisão] Meta (valem para todo notebook da entrega)
> **Pico de memória ≤ 6 GB** (soma do kernel e de qualquer processo filho) e **tempo ≤ 20 min**, exceto o C_13 (ajuste fino, ≤ 40 min) e o C_16 (teste, ≤ 30 min). Medir com a ferramenta deste card; guardar tudo numa tabela única.

### ② Problema

> [!decisão] Revisão de 03/11 · versão 3
> Despriorizado em 03/11: o pico de memória já foi reduzido (B_04 e B_05 em 01/11); o medidor do #126 registra tempo e memória da execução limpa.

> [!atenção] Replanejamento de 31/10 · versão 2 (entrega em 04/11)
> A ferramenta de medição passa a ser criada **no #144** (sábado à tarde), porque B e C a usam desde hoje. Este card vira o **consolidador**: tabela única, correção do que passar da meta e parágrafo para o relatório. Meta (vale para todo notebook da entrega): **pico de memória ≤ 6 GB** e **tempo ≤ 20 min**, exceto o C_13 (ajuste fino, ≤ 40 min) e o C_16 (teste, ≤ 30 min). O diagnóstico de RAM livre na máquina do projeto mostrou 13,4 GB livres; 6 GB deixa folga para o sistema.

Estado atual, medido no diagnóstico de 30/10 e na leitura dos notebooks:

- Só o C_11 usa `src.utils.performance.Monitor`; nenhum notebook chama `liberar(...)`.
- `B_06` lê colunas do Parquet em 54 pontos diferentes (`columns=`) em vez de ler uma vez e reaproveitar; `B_05` tem 42 células de código na coorte inteira.
- O C_13 pode rodar a busca com `MAX_TREINO_BUSCA = None` (treino inteiro, 556 mil linhas) e `max_iter` até 1.000.
- O C_16 reconstrói `treino`, `validacao` e `teste` como DataFrames completos (`df.loc[df[PARTICAO] == "teste"]`) e usa `ic_bootstrap`, que reordena o vetor inteiro a cada réplica.
- Não há tabela de tempo e memória para nenhum notebook: sem número não dá para dizer que a execução é sustentável.

### ③ O que fazer

> [!decisão] Replanejamento de 31/10
> Em vez de uma refatoração geral (#129, fica para depois da entrega), **medir uma vez, corrigir só o que passar da meta e registrar os números**. Cada pessoa mede os próprios notebooks no momento em que já precisaria executá-los.

**Dono:** Pessoa B e Pessoa C (medição e correções dos próprios notebooks) · Pessoa A (tabela e relatório) · **Prazo:** medições de 31/10 a 03/11; tabela final em 03/11 · **Esforço estimado:** B ≈ 45 min · C ≈ 45 min · A ≈ 15 min · **Começa quando:** #144

#### 1. Ferramenta
Já criada no #144 (`tools/medir_notebook.py`): mede o pico somando o processo e os filhos, grava em `outputs/final/performance_notebooks.csv` e devolve código de saída 2 se passar do limite. Confirme que ela existe no `main` antes de começar.

#### 2. Medir (cada pessoa, no momento em que executa o notebook)
Uso: `.\.venv\Scripts\python.exe tools/medir_notebook.py notebooks/C/C_12_baseline_logistica.ipynb`. Sem `--salvar-no-lugar` a cópia executada vai para `outputs/notebooks/` e o original não muda. Na execução **final** de cada notebook (#126), acrescente `--salvar-no-lugar`.

| Pessoa | Notebooks | Quando medir |
|---|---|---|
| A | C_14 (ablações), A_03, A_04 | C_14 no #54 (31/10); A_03 e A_04 em 03/11 |
| B | B_05, B_06, B_07 | B_06 no #51 e no #136 (31/10); B_05 e B_07 em 03/11 |
| C | 00, 01, C_11, C_12, C_13, C_15 | C_11 a C_13 no #132 (31/10) e C_13 com busca no #1 (01/11); C_15 no #5 e no #79 (01/11); 00 e 01 em 03/11 |
| C | C_16 | **não roda de novo** (o teste abre uma vez): use o log do `Monitor` e a medição do #2 |

#### 3. Corrigir o que passar da meta, nesta ordem (pare quando passar a ficar dentro)
1. **Ler menos:** `pd.read_parquet(caminho, columns=[...])` ou `load_supervised_artifact(..., partitions=(...), columns=[...])` só com o que a célula usa. Ler **uma vez** por notebook e reaproveitar (B_06: um `df` base na célula 2, derivados por filtro).
2. **Tipos menores:** inteiros pequenos para indicadores (`int8`), `float32` para contínuas, `category` para textos com poucos valores (`pd.read_parquet` já devolve `category` quando o arquivo foi gravado assim). Nunca `toarray()` ou `get_dummies` na coorte; usar `OneHotEncoder(sparse_output=True, dtype=np.float32)` (o `build_preprocessor` já faz).
3. **Processar em lotes:** previsão em blocos de 250 mil linhas (`for i in range(0, len(X), 250_000): pipe.predict_proba(X.iloc[i:i+250_000])`), guardando só `y` e a probabilidade em `float32`. É obrigatório no C_16 para `test_pandemic`.
4. **Amostrar com semente e dizer que amostrou:** agrupamento (80 mil fichas do `train_ref`), importância por permutação (50 mil, `n_repeats=3`), gráficos de dispersão (`matriz_para_plot`, de `src/utils/io_eficiente.py`). Registrar a amostra no texto do notebook.
5. **Liberar memória entre seções:** `liberar(globals(), ["df_grande", "X_proc"])` (de `src.utils.performance`) e `plt.close("all")` depois de cada figura. Em notebooks longos (B_06), uma chamada de `liberar` por seção.
6. **Bootstrap:** use `bootstrap_grupo` do #127 (pesos por grupo, ordenação feita uma vez), nunca `ic_bootstrap` em vetor de milhões.

#### 4. Registro (03/11, Pessoa A consolida, 15 min)
- `outputs/final/performance_notebooks.csv` com uma linha por notebook (a última execução de cada).
- Um parágrafo para o relatório (seção "Reprodutibilidade e desempenho", #133) e a coluna de tempos no README (#126).
- Se algum notebook continuar acima da meta: registre o motivo e o número no card (por exemplo, "C_13: 36 min, 4,1 GB, busca em 400 mil linhas"). Meta ultrapassada **com explicação** é aceitável; sem número, não.

### ④ Pronto quando

- existe: `tools/medir_notebook.py` | A ferramenta de medição de tempo e memória existe em tools/medir_notebook.py.
- existe: `outputs/final/performance_notebooks.csv` | A tabela de tempo e pico de memória dos notebooks da entrega existe em outputs/final/performance_notebooks.csv.
- manual: | Todos os notebooks da entrega (00, 01, A_03, A_04, B_05, B_06, B_07, C_11, C_12, C_13, C_14, C_15) têm uma linha na tabela com pico ≤ 6 GB e tempo ≤ 20 min (C_13 ≤ 40 min), ou o motivo registrado neste card; o C_16 usou leitura em lotes de 250 mil linhas.
- manual: | O parágrafo de desempenho está no relatório (#133) e os tempos estão no README (#126).

## #146 · Nomes da entrega: notebooks numerados na ordem de execução e sem marcas internas

- prioridade: P2
- situação: aberta
- estratégia: desenvolver
- marco: M7
- data ideal: 04/11
- responsável: Pessoa B (1 h) + Pessoa A (0,25 h)
- pessoas: B, A
- fonte: Regra do pacote (31/10); revisão de 03/11 (escopo reduzido)
- depende de: #155, #152
- tags: Notebook, Limpeza, Entrega
- pilar: Documentação
- carga: 1.25
- novo: não
- professores: não

### ① Para entender

A banca lê os notebooks na ordem dos nomes. Hoje os nomes misturam letras de pessoa e de fase (A_03, B_02, C_11…) e a ordem do nome não é a ordem de execução (as ablações, C_14, vêm antes do ajuste fino, C_13).

### ② Problema

> [!decisão] Revisão de 03/11 · versão 3 · escopo reduzido
> A ferramenta de varredura (`tools/auditar_marcas.py`) e a renomeação de testes e variáveis com nome de pessoa saem do escopo: ficam para depois de 05/11. Fica só o que a banca vê primeiro: o nome e a ordem dos notebooks e o texto visível (Markdown) sem nomes de pessoa nem números de card.

### ③ O que fazer

**Dono:** Pessoa B · **Prazo:** 04/11, 18h às 19h (depois da exploração e antes da execução limpa) · **Começa quando:** #155 e #152

1. Renomeie num comando:
```powershell
$m = [ordered]@{'A/A_03_coorte_protocolo'='02_coorte_definitiva';'B/B_02_eda_primeira_passagem'='03_eda_primeira_passagem';'B/B_04_eda_temporal_clustering'='04_eda_temporal_agrupamento';'B/B_05_supervisionado_pilotos'='05_supervisionado_pilotos';'C/C_11_pipeline_supervisionado'='06_pipeline_supervisionado';'C/C_12_baseline_logistica'='07_baseline_logistica';'C/C_14_ablacoes_variaveis'='08_ablacoes_variaveis';'C/C_13_boosting'='09_ajuste_fino';'C/C_15_calibracao_limiar'='10_calibracao_limiar';'C/C_16_validacao_final'='11_validacao_final'}; foreach ($k in $m.Keys) { git mv "notebooks/$k.ipynb" "notebooks/$($m[$k]).ipynb" }
```
2. Atualize as referências aos nomes antigos: `git grep -n -E "A_03|B_02|B_04|B_05|C_1[1-6]" -- README.md docs src tests configs notebooks` e troque pelo nome novo (as entradas históricas do decisoes.md ficam, com uma nota de mapeamento no fim da §25).
2b. **Títulos e mensagens:** os títulos ainda dizem `# C2 — Pipeline Supervisionado` … `# C6 — Validação Final`, há mensagens "Execute o Notebook 03" (C_11 e `src/data/supervised_artifact.py`), "O B_07 exige…" (B_05) e "Notebook 01" (B_02). Troque pelo número e nome novos (`# 06 · Pipeline supervisionado` etc.; "Execute o notebook 02_coorte_definitiva").
   **Não renomeie** os prefixos dos arquivos de saída (`C3_baseline_logistica_*`, `C4_boosting_*`, `C5_calibracao_limiar_*`, `C6_validacao_final_*`) nem os nomes de execução em `Run(modelo=...)`: o C_16 localiza o manifesto do C_15 e a guarda contra reabertura pelo prefixo. No README, uma linha explica o mapeamento.
3. No Markdown dos notebooks, apague "Pessoa A/B/C" e "(#NN)" que aparecerem no `git grep -n -E "Pessoa [ABC]|\(#[0-9]{2,3}\)" -- notebooks`.
4. Rode `pytest -m "not slow" -q` (há testes que citam caminhos de notebook) e o `server.py validar` (os ④ do painel citam caminhos antigos: atualize os dos cards abertos). Commit: `chore: notebooks numerados na ordem de execução [done:#146]`.

### ④ Pronto quando

- existe: `notebooks/11_validacao_final.ipynb` | Os notebooks foram renomeados na ordem de execução.
- nao-existe: `notebooks/C/C_16_validacao_final.ipynb` | Os nomes antigos saíram do pacote.
- manual: | O git grep por nomes antigos, Pessoa A/B/C e (#NN) nos notebooks ficou vazio (ou só com entradas históricas do decisoes.md).

## #147 · Congelar e conferir o pacote entregue

- prioridade: P1
- situação: aberta
- estratégia: documentar
- marco: M8
- data ideal: 05/11
- responsável: Pessoa A (0,75 h)
- pessoas: A
- fonte: Revisão de 03/11 (absorve #149 e #130)
- depende de: #2, #126, #133, #156, #157, #163
- tags: Entrega, Reprodutibilidade
- pilar: Eficiência + Documentação
- carga: 0.75
- novo: não
- professores: não
- arquivos: .gitattributes

### ① Para entender

Última hora de trabalho: nada de código novo. Só conferir, congelar e empacotar. Este card absorveu a reconferência dos cards concluídos (#149: as contagens do artefato 70/15/15 já foram conferidas em 03/11) e a regeneração da referência (#130).

### ② Problema

Se a entrega for o link do GitHub, o que estiver no `main` naquela hora é o que a banca vê, inclusive a pasta do painel e os arquivos de status. O `.gitattributes` com `export-ignore` só vale para `git archive`.

> [!decisão] Revisão de 03/11 · versão 4.0
> O clone limpo (instalar, pytest e notebooks 00 e 01 numa pasta nova) é feito na véspera, no #163. Aqui, repita só o `git grep` de caminhos locais e confira que `resultados/` está versionada. **Script previsto:** `montar_pacote.py` (relatório primeiro: confere o que entra e o que sai do `git archive`).

### ③ O que fazer

**Dono:** Pessoa A · **Prazo:** 05/11, 16h às 16h45, antes da apresentação · **Começa quando:** #2, #126 e #133

1. `git pull`; `git status` limpo. Um comando para o resumo:
```powershell
.\.venv\Scripts\python.exe -m pytest -m "not slow" -q; .\.venv\Scripts\python.exe .srag-status-local\server.py validar; git grep -n -E "Pessoa [ABC]|\(#[0-9]{2,3}\)" -- notebooks src tests configs README.md; git grep -n -I -i -E "olivem85|OneDrive - " -- notebooks docs README.md resultados
```
2. Regerar a referência (fecha o antigo #130): `.\.venv\Scripts\python.exe tools\update_project_reference.py --run-tests --pytest-args="-m 'not slow'"`.
3. Pacote: crie o `.gitattributes` com `export-ignore` para `.srag-status-local/**`, `PROJECT_STATUS.md`, `PROJECT_STATUS_TEXT.md`, `docs/PROJECT_COMPLETE_REFERENCE.txt`, `docs/project_reference_md/**`, `tools/update_project_reference.py`, `tools/clean_project.py`, `tools/read_outputs.py` e `tools/perfil_celulas.py` (ferramentas internas; usam `python-docx` e `jupyter_client`, fora das dependências) e `.gitattributes`. Gere o zip: `git archive -o entrega_srag.zip HEAD`. Se a entrega for o link, crie o branch `entrega` a partir do `main` e apague nele esses mesmos arquivos.
4. Tag: `git tag entrega-2026-11-05; git push --tags`. Commit final: `chore: pacote da entrega [done:#147]`.

### ④ Pronto quando

- existe: `.gitattributes` | O .gitattributes com as exclusões do pacote existe.
- manual: | O pytest rápido passou, o painel validou sem problemas de formato, a varredura de nomes de pessoa ficou vazia e a tag entrega-2026-11-05 foi publicada.

## #148 · C_16 nos blocos: Teste A, Teste B e 2020–2022 em separado, predição em lotes e registro da abertura

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M5
- data ideal: 03/11
- responsável: Pessoa A (0,75 h)
- pessoas: A
- fonte: Leitura do C_16 no commit 9f3322b; §22 do decisoes.md; revisão de 03/11 (absorve #26 e #27)
- depende de: #158
- tags: Notebook, Teste, Vazamento
- pilar: Valor científico-acadêmico
- carga: 0.75
- novo: não
- professores: não
- arquivos: notebooks/C/C_16_validacao_final.ipynb

### ① Para entender

O C_16 é o único notebook que abre o teste, e ele roda **uma vez**. Por isso precisa estar correto antes do G9: as saídas salvas na primeira execução são as definitivas. O protocolo (§22) pede três leituras do mesmo modelo congelado: **Teste A** (`test_ref`, resultado principal), **Teste B** (`test_ref` + `test_pandemic`) e **2020–2022 isolado**, com métricas por ano.

### ② Problema

> [!decisão] Estado em 03/11 (commit `d7d774c`)
> O script `corrigir_c15_c16.py` aplicou o C_16 novo. Ele agora: lê só `train_ref` e `val_ref` antes do teste; abre `test_ref` e `test_pandemic` **separados**, prevendo em lotes de 250 mil; monta Teste A, 2020–2022 e Teste B; calcula o IC por grupo (`group_id`) no Teste A; confere, **antes de abrir o teste**, o limiar, as variáveis e o hash dos modelos contra o C_15; grava as previsões antes de qualquer análise; registra `test_opened` no manifesto do artefato; e tem modo ensaio (`SRAG_C16_ENSAIO=1`).
> O relatório do script passou nos 8 passos do ensaio sintético, na máquina de quem o rodou e com as versões reais das bibliotecas. **Ainda não foi rodado com os dados reais.**

O ensaio usa duas metades de `val_meas` no lugar dos blocos de teste, **não** lê o teste, **não** marca o G9, **não** altera o artefato e grava com o prefixo `C6ENSAIO_` (que não aciona a guarda de reabertura). Como o YAML ainda não tem finalista, método nem limiar, o ensaio usa padrões (`logistic`, `sigmoid`, 0,5) e avisa.

### ③ O que fazer

**Dono:** Pessoa A · **Prazo:** 03/11, 14h às 15h30, na **máquina oficial** (#158) · **Começa quando:** já (o artefato com 30 variáveis existe)

1. **Revise o diff (15 min):** `git show d7d774c --stat` e leia as células `split-calibrate`, `open-test` e `mark-g9` do C_16. Pontos de atenção: a trava do limiar e do hash antes de abrir o teste, as previsões gravadas antes de qualquer análise e o `mark-g9` só no fim.
2. **Ensaio com dados reais (sem abrir o teste e sem alterar o notebook):**
```powershell
$env:SRAG_C16_ENSAIO="1"; .\.venv\Scripts\python.exe tools\medir_notebook.py notebooks\C\C_16_validacao_final.ipynb --limite-mb 12288; Remove-Item Env:SRAG_C16_ENSAIO
```
3. **Confira:** o ensaio terminou; `outputs/tables/C6ENSAIO_*_janelas.csv` tem três linhas (`teste_a`, `teste_b`, `pandemico_isolado`); `git status` não mostra o notebook nem o `supervised.yaml` alterados; `test_opened` continua `false` no manifesto do artefato; o G9 continua `pendente`. Os arquivos `C6ENSAIO_*` **não** vão para `resultados/` (#157).
4. Comente o resultado neste card (tempo, pico de memória e qualquer aviso). Se algo falhar, não corrija à mão: cole a mensagem no grupo antes do #2.

### ④ Pronto quando

- nao-contem: `notebooks/C/C_16_validacao_final.ipynb` :: `partitions=("treino", "validacao", "teste")` | O C_16 não pede mais os rótulos do esquema antigo.
- contem: `notebooks/C/C_16_validacao_final.ipynb` :: `test_pandemic` | O C_16 lê o bloco test_pandemic separadamente (2020–2022 e Teste B).
- contem: `notebooks/C/C_16_validacao_final.ipynb` :: `prever_em_lotes` | A predição do teste é feita em lotes.
- contem: `notebooks/C/C_16_validacao_final.ipynb` :: `_janelas.csv` | O C_16 grava uma tabela com Teste A, Teste B e 2020–2022.
- contem: `notebooks/C/C_16_validacao_final.ipynb` :: `test_opened` | O C_16 registra a abertura do teste no manifesto (#26).
- manual: | A Pessoa A revisou o diff do C_16 e o ensaio com dados reais rodou até o fim sem abrir o teste, e o resultado está comentado neste card.

## #149 · Reconferência final dos resultados dos cards concluídos (antes da execução limpa)

- prioridade: P1
- situação: aberta
- estratégia: documentar
- marco: M6
- data ideal: 03/11
- responsável: Pessoa B (1,25 h) + Pessoa A (0,25 h) + Pessoa C (0,25 h)
- pessoas: B, A, C
- fonte: Revisão de volatilidade de 01/11: cards concluídos cujo resultado ainda pode ser recalculado
- depende de: #140, #144, #73, #102, #146
- tags: Reprodutibilidade, Entrega, Checklist
- pilar: Documentação + Valor científico-acadêmico
- carga: 1.75
- novo: sim
- professores: não
- removido: absorvido pelo #147 em 03/11 (as contagens do artefato 70/15/15 foram conferidas em 03/11)

### ① Para entender

Vários cards concluídos descrevem resultados que ainda podem ser recalculados por motivos previstos no plano: o ponto de decisão (#140) pode retirar variáveis, o ajuste fino (#1) e o peso de classe (#5) mudam o modelo, o #144 e o #73 devolvem gates e decisões ao YAML, e a execução limpa (#126) salva os notebooks de novo.

Na revisão de volatilidade de 01/11 só **dois** cards voltaram para ABERTA (#50 e #97). Os outros ficaram concluídos porque, se os números mudarem, a **conclusão** não deve mudar. Este card é a rede de segurança: uma passada única, depois da renomeação do #146 e antes da execução do #126, que reconfere os valores citados e deixa registrado, para cada um, o que mudou ou que "nada mudou".

> [!exemplo] Exemplo
> Se o #140 retirar a `fadiga`, o ROC-AUC do piloto no #52 muda na terceira casa decimal e a frase "o desempenho não sobe com o preenchimento" continua verdadeira. Mas o número que vai para o relatório tem de ser o novo.

### ② Problema

> [!decisão] Critério da revisão de 01/11
> Um card concluído só volta para ABERTA se uma decisão pendente ou um resultado ainda por vir puder **mudar a conclusão** (ou se foi fechado sem o registro que o critério exige). Se só os números ou o texto puderem mudar, ele fica concluído e a reconferência entra aqui.

Cards concluídos que este card reconfere, e por que não foram reabertos:

| Card concluído | O que pode mudar | Muda a conclusão? | Item |
|---|---|---|---|
| #142, #118, #10, #75 | `dataset_sha256`, colunas e contagens por bloco; quarentena de 4 linhas e 2 grupos | Só se o #140 mudar variáveis (hash e colunas) ou o #102 virar a Opção B (contagens) | R1 |
| #77, #85, #120, #44 | `status` dos gates e das decisões no YAML; lista `features.final` | Não, a menos que o #140 retire variáveis (#77 e #44) | R2 |
| #9, #10, #11, #29, #59, #82, #83, #12, #33 | registro no `decisoes.md` (pacote do #73) e textos | Não | R2 e R5 |
| #51, #136, #60, #99, #139 | tabelas de óbito do train_ref, agrupamento e notebook 06 salvo | Não; o #51 só mudaria se o #102 virasse a Opção B | R3 |
| #52, #125 | desempenho do piloto por padrão de preenchimento e notebook 07 salvo | Não deve mudar com o #1 e o #5 | R4 |
| #8, #9, #28, #82, #60 | textos com números de outra base | Não | R5 |
| #52, #136 | frases do relatório (piloto; k=2 principal e k=3 segundo nível) | Não | R6 |
| #141 | chave do código x YAML e teste da recodificação | Só se o #140 aprovar a recodificação (então reabra o #141) | #140 |
| #72 | divisão de 24/10, substituída pelo plano da versão 2 | Não; vale a divisão de cada card | n/d |

Reabertos nesta revisão: **#50** (a tabela de ablações e a decisão dos três sintomas dependem do #54 e do #140) e **#97** (fechado sem as respostas do professor). O #5 saiu de "resolvida" porque depende do #1 e do #148.

### ③ O que fazer

> [!decisão] Revisão de volatilidade de 01/11
> Uma hora de trabalho antes da execução limpa. Se o #140 mudar variáveis, o bloco condicional (comentário do #140) deve ser feito logo, sem esperar este card.

**Dono:** Pessoa B (reconferência, textos e relatório) + Pessoa A (manifestos, gates e decisões) + Pessoa C (finalista) · **Prazo:** 03/11 (terça), 21h às 22h30, depois da renomeação do #146 · **Esforço estimado:** B ≈ 1 h 15 · A ≈ 15 min · C ≈ 15 min · **Começa quando:** #140, #144, #73, #102 e #146

**Regra para decidir se um card reabre** (sugestão; combine antes de olhar os números):
- Padrões de preenchimento (#52): reabre se o `sim_e_nao` passar a ter ROC-AUC maior que os outros dois em alguma faixa etária, com intervalos que não se sobrepõem.
- Agrupamento (#136): reabre se o K-Means deixar de escolher k=2 ou o V de Cramér das 13 comorbidades cair abaixo de 0,5 (hoje, de 0,86 a 0,99).
- Tabelas de óbito (#51): reabre se mais de 3 das 26 razões de chances trocarem de sentido em relação à tabela registrada no card.
- Artefato (#142): reabre se o hash ou as contagens mudarem sem decisão registrada.

1. **R1 (A, 10 min). Manifestos.** Em `data/analytical/manifesto_supervisionado.json` e `manifesto_particao.json`: anote o `dataset_sha256`; `rows` = 3.710.779; train_ref 556.462, val_tune 39.748, val_cal 39.746, val_meas 39.749, test_ref 119.245, test_pandemic 2.915.829, exploracao 173.945; `rows_quarantined` = 4 e `groups_quarantined` = 2.
2. **R2 (A, 5 min). Gates, decisões e variáveis.** No `configs/supervised.yaml`: G1, G2, G4 e G5 com `status: aprovado`. No `configs/decisoes.yaml`: `alvo`, `coorte_estrita`, `evolucao_desconhecida`, `periodos` e `ponto_de_previsao` com `status: aprovada`. `features.final` com a lista do #140 (31 variáveis se nada mudou) e igual a `feature_columns` do manifesto. Painel: **Atualizar, auditar e validar** e ✓ nos critérios de #77, #85, #120, #75, #29 e #59.
3. **R3 (B, 15 min). Notebook 06.** Nas saídas da última execução: `Fichas em train_ref: 556462` e `Óbitos por SRAG: 46961` (8,44%); `k escolhido no K-Means: 2`; corte principal do hierárquico em k=2 e nível de descrição em k=3; ARI entre os dois métodos em k=2 de 0,998; 126 de 126 células executadas e sem erro.
4. **R4 (B, 15 min). Notebook 07, seção 23.** ROC-AUC do boosting de 0,872 (`comorbidades_sem_nao`), 0,868 (`sintomas_em_branco`) e 0,766 (`sim_e_nao`); 74,9% contra 39,1% de fichas com alguma comorbidade respondida (óbitos contra as demais); as cinco tabelas em `outputs/final/`. Se a seção 23 ainda não estiver no notebook, aplique-a antes (o #52 se apoia nela).
5. **R5 (B 10 min, C 10 min). Textos.** B atualiza os textos de #8 (partição-mestre), #9 (mortalidade de 11,3% e 4,5% no train_ref), #82 (coorte final) e #60 (números do agrupamento de 01/11). C atualiza o #28 (finalista e AUC vigentes, depois do #1 e do G6).
6. **R6 (B, 15 min). Relatório (#133).** (a) Parágrafo do #52 dizendo "piloto (hiperparâmetros padrão, treinado só no train_ref)"; (b) agrupamento: K-Means e corte principal do hierárquico em k=2, com k=3 como segundo nível; (c) tabelas de óbito só do train_ref (556.462 fichas, 8,44%), sem a comparação com a coorte inteira, que inclui blocos de teste; (d) resultados do piloto identificados como tal.
7. **R7 (B, 10 min). Tabela de reconferência.** Comente neste card: card, valor registrado, valor reconferido, "a conclusão mudou?". Para cada "sim": reabra o card com um comentário (o que mudou, valor antigo, valor novo e o que refazer) e avise o #133.

**O #102 foi decidido em 01/11 pela Opção A** (2019 no desenvolvimento; §29.25 do `decisoes.md`). Se a equipe voltasse atrás (Opção B), todos os cards da tabela voltariam para ABERTA e os números de 24/10 em diante seriam refeitos: comente aqui e reabra em bloco.

### ④ Pronto quando

- manual: | A tabela de reconferência (card, valor registrado, valor reconferido, a conclusão mudou?) está comentada neste card, com R1 a R5 e, se o #140 mudou variáveis, o bloco condicional.
- manual: | Cada card da tabela do ② continua com número e texto atualizados, ou foi reaberto com um comentário que diz o que mudou.
- manual: | O #133 usa os números reconferidos: parágrafo do #52 com "piloto", k=2 principal e k=3 segundo nível no agrupamento, e tabelas de óbito só do train_ref.

## #150 · Condensar a documentação do pacote e fechar as sobras que o #146 não cobre

- prioridade: P2
- situação: aberta
- estratégia: documentar
- marco: M6
- data ideal: 03/11
- responsável: Pessoa A (2,5 h) + Pessoa C (0,5 h)
- pessoas: A, C
- fonte: Levantamento de 01/11 (git grep de referências e contagem de palavras por arquivo); revisão de 01/11 sobre o nível esperado de uma entrega de pós-graduação
- depende de: #146
- tags: Documentação, Limpeza, Entrega
- pilar: Documentação + Valor científico-acadêmico
- carga: 3
- novo: sim
- professores: não
- arquivos: docs/decisoes.md, src/protocolo/verificacoes.py, requirements.txt, pyproject.toml, notebooks/C/outputs/performance/C_11_pipeline_supervisionado.csv
- removido: absorvido pelos #152, #126 e #154 em 03/11 (governança de publicação e cópias já removidas no commit 7d4373c; cloudpickle no #126; condensação do decisoes.md despriorizada)

### ① Para entender

Complementa o #146 e o #147. O #146 tira as marcas de processo (números de card e "Pessoa X") e renomeia os arquivos; este card cuida do que ele não cobre: documentação mais longa do que a banca precisa, código de governança de produção que a coorte já publicada não usa mais, um arquivo de saída versionado e dependências e caminhos que atrapalham quem reproduzir o trabalho. **Nada que seja método sai:** decisões, critérios e planos registrados antes dos resultados ficam; muda a forma, não o conteúdo.
> [!decisão] Decisão de 01/11 (Pessoa B)
> O pacote não deve exigir mais do que uma turma de pós-graduação dedicada entregaria: técnicas, estruturas de segurança e documentação acima desse nível saem, **desde que a limpeza não custe horas de adaptação**. O painel (.srag-status-local, PROJECT_STATUS.md, PROJECT_STATUS_TEXT.md) e as ferramentas de tools/ ficam **fora desta rodada**: o painel e os arquivos de status já saem do pacote da banca pelo .gitattributes do #147 (ver "Adiado" no ③).

### ② Problema

- docs/decisoes.md tem 11.348 palavras (o README tem 1.990). A §29 ocupa as linhas 972 a 1617, cerca de 40% do arquivo, e repete em cada entrada o mesmo molde de campos (Decisão, Motivo, Impacto, Implementado em, Fecha).
- src/protocolo/verificacoes.py tem 5,2 palavras por linha, contra 1,6 a 3,3 nos outros arquivos de src/: docstrings longas.
- docs/decisoes.md ainda tem "Responsável pelo registro: Pessoa X" (linhas 888 e 964) e uma nota de gestão na linha 969.
- notebooks/C/outputs/performance/C_11_pipeline_supervisionado.csv está versionado no Git (parece saída de medição) e carrega o código do notebook no nome.
- tools/read_outputs.py está no Git e não consta no .gitattributes do #147.
- **Cadeia de publicação da coorte:** src/data/cohort_publication.py (901 linhas, com testes de 500 linhas), src/data/cohort_transition.py e src/data/cohort_parity.py (382 linhas) são governança de produção (gates com hash, promoção atômica, desfazer em caso de erro) para uma coorte que já está publicada com manifesto. A coorte definitiva é construída por final_cohort.py e final_cohort_cli.py, que **ficam**.
- src/protocolo/metricas_por_grupo.py (49 linhas) é uma cópia antiga da função que vive em src/evaluation/errors.py e ainda traz no cabeçalho um aviso deixado por assistente ("não vi a versão atual de metricas_por_grupo").
- configs/feature_contract_v1.json repete a lista de variáveis que já está em features.final do supervised.yaml.
- O notebook do pipeline (C_11) usa cloudpickle, que não está declarado no requirements.txt nem no pyproject.toml: quem instalar do zero no #126 pode falhar.
- src/utils/storage.py tem um caminho de download com GITHUB_TOKEN para release privada, além do download público com tentativas repetidas.
- Os notebooks 00 e 01 imprimem ROOT_DIR e o caminho do Parquet; depois da execução final (#126), essas saídas ficam salvas com o caminho da máquina de quem rodou.

### ③ O que fazer

Cada pessoa trabalha só nos próprios arquivos. A Pessoa A pode começar na segunda (02/11, dia de folga dela): o script de limpeza primeiro e a condensação do decisoes.md depois que o #140, o #78, o #79 e o #80 registrarem as entradas deles.

#### Rodar o script de limpeza (Pessoa A, 30 min)
- Salve o limpar_projeto_v2.py **fora** do repositório (por exemplo em Documentos), para ele não entrar no pacote. Ele não toca em .srag-status-local, tools/, PROJECT_STATUS.md, PROJECT_STATUS_TEXT.md nem em PROJECT_COMPLETE_REFERENCE.txt, e **não renomeia nada** (a renomeação é do #146).
- git pull; git status limpo (ou commit do que estiver pendente). Na pasta do repositório, veja o plano sem alterar nada:
```powershell
.\.venv\Scripts\python.exe C:\caminho\limpar_projeto_v2.py --simular
```
- Se o plano estiver certo, rode sem o --simular (o script arquiva tudo em uma pasta fora do repositório, valida com compileall e com a coleta do pytest, e grava o RELATORIO_LIMPEZA.txt):
```powershell
.\.venv\Scripts\python.exe C:\caminho\limpar_projeto_v2.py
```
- O que ele move **só se nenhum arquivo mantido usar** (se algum usar, o item fica e o motivo aparece no plano):

| Item | Motivo |
|---|---|
| src/data/cohort_publication.py, cohort_transition.py, cohort_parity.py e os testes deles | governança de publicação da coorte já publicada |
| src/protocolo/metricas_por_grupo.py e o teste dele | cópia antiga da função de src/evaluation/errors.py |
| configs/feature_contract_v1.json (só se ninguém o citar) | lista de variáveis duplicada |
| .scripts/read_outputs.py (só se idêntico ao de tools/) | cópia |
| notebooks/C/outputs/performance/C_11_pipeline_supervisionado.csv | saída de medição versionada |

- **Se o final_cohort_cli.py usar algum desses módulos, não mexa no CLI:** é o que reconstrói a coorte para quem reproduzir o trabalho. Registre o motivo neste card e siga; não vale horas de adaptação.
- Fique com os manifestos da coorte (coorte_final.manifest.json e o da paridade): são a evidência do que o relatório cita; só o código de publicação sai.
- O script lista as referências de texto pendentes (README, docs) aos itens movidos: corrija à mão. Commit: chore: remove governanca de publicacao da coorte e duplicatas.
- Para desfazer qualquer item, mova-o de volta da pasta de arquivo para o mesmo caminho relativo.

#### Condensar a §29 do docs/decisoes.md (Pessoa A)
- **Não renumere nem mude títulos.** Outros textos citam §28, §29.1, §29.4, §29.10, §29.24 e §29.25, e a §29.28 a §29.31 ficam reservadas para #140, #78, #79 e #80.
- Cada entrada com no máximo Decisão, Motivo e Impacto. "Implementado em" só quando aponta uma chave de configuração.
- Funda a §29.6.1 na §29.6, deixando o estado final e uma frase sobre a correção. A §29.25 (reversão sobre 2019) vira uma frase dentro da entrada que ela corrige, se couber sem perder a decisão de 29/10.
- Planos registrados antes dos resultados (§29.17, §29.19, §29.21, §29.22): mantenha **todas** as decisões e todos os critérios; corte só a narrativa. Meta sugerida: metade das linhas da §29.
- **Mantenha estes textos**, que critérios do painel conferem: "final_cohort_v1", "criar_group_id", "indicadores de ausência", "parcial", "ponto de decisão", "## 28. Decisão temporal", a menção a 2019 nas §5 e §28, e uma linha "Última atualização" diferente de 21/10/2026.
- Apague "Responsável pelo registro: Pessoa X" (linhas 888 e 964) e reescreva a nota da linha 969 sem citar card ou pessoa.
- Depois, no painel, **Atualizar, auditar e validar**: os critérios de #73, #9, #10, #13, #59, #83, #102, #120 e #140 sobre o decisoes.md precisam continuar ✓.

#### Docstrings do verificacoes.py (Pessoa A, com o arquivo à mão)

Reduza as docstrings com mais de 6 linhas ao essencial: o que a função faz, os parâmetros e a regra de negócio. Mantenha as que explicam uma decisão (por exemplo, por que o arquivo provisório não é o artefato oficial).

#### Arquivo versionado que não deveria estar (Pessoa C, 5 min)

`git rm notebooks/C/outputs/performance/C_11_pipeline_supervisionado.csv` (se o script já o moveu, só confirme). A pasta notebooks/C deixa de existir no #146; sem este passo o arquivo ficaria órfão no pacote. Se ele reaparecer depois da execução do #126, acrescente `notebooks/**/outputs/` ao .gitignore.

#### Dependência que falta (Pessoa C, 10 min)
- Descubra a versão instalada:
```powershell
.\.venv\Scripts\python.exe -c "import cloudpickle; print(cloudpickle.__version__)"
```
- Acrescente `cloudpickle==X.Y.Z` ao requirements.txt e `cloudpickle>=X.Y.Z` às dependências do pyproject.toml, com X.Y.Z igual à versão impressa (o teste de configuração exige versão fixada no requirements e cobertura das dependências do pyproject). Confira com `.\.venv\Scripts\python.exe -m pytest tests/test_config.py -q`.

#### Fallback de token no storage.py (Pessoa C, decisão de 15 min)
- Abra a release dos dados numa janela anônima do navegador. **Pública:** em get_parquet, tire o ramo que usa GITHUB_TOKEN (as funções _token e _private_asset_url e o except que as chama), mantenha o download com tentativas repetidas e a verificação PAR1 e do SHA-256, e apague do notebook 00 a frase "Para repositório privado". **Privada:** mantenha o código e escreva no README (#126) que a banca precisa do token.
- Qualquer que seja a escolha, comente-a neste card. Se mexer no código: `.\.venv\Scripts\python.exe -m pytest -m "not slow" -q`.

#### Caminho pessoal (Pessoa A agora; Pessoa C nos notebooks 00 e 01)
- Procure caminho pessoal, o nome da empresa e `C:\Users` em todo arquivo versionado (a busca não altera nada):
```powershell
.\.venv\Scripts\python.exe C:\caminho\limpar_projeto_v2.py --auditar-caminhos
```
- Em código ou configuração: troque por caminho relativo. **Pessoa C:** nos notebooks 00 e 01, imprima só o nome (ROOT_DIR.name e parquet_path.name) em vez do caminho completo, antes do #126.
- **Repita a busca depois da execução final do #126 e antes da tag do #147**: as saídas salvas de cada notebook trazem o caminho da máquina de quem rodou.

#### Já coberto por outros cards (não repetir aqui)
- Marcas de processo, "Pessoa A/B/C", nomes de arquivo com pessoa e a renomeação (inclusive tests/test_regras_pessoa_a.py): #146.
- Notebooks com erro salvo ou sem execução (C_11 a C_16, A6, A_15): #132, #148, #146 e #126.
- Nomes antigos de notebooks e arquivo inexistente citado no README: #126.
- Decisões em "proposta" no decisoes.yaml: #73.
- Os avisos G6_STATUS, G7_STATUS e G8_STATUS do auditor são falsos alertas (#94): nome de variável de notebook, não gate. Nada a fazer.
- Células de verificação repetidas no B_06 (uma checagem por seção basta): Pessoa B, dentro da limpeza do #146, só se sobrar tempo.

#### Adiado (fora desta rodada por decisão de 01/11; sem critério neste card)
- **Painel e status:** .srag-status-local/ (inclusive backups/, que o Git já ignora), PROJECT_STATUS.md, PROJECT_STATUS_TEXT.md e docs/PROJECT_COMPLETE_REFERENCE.txt continuam como estão e saem do pacote da banca pelo .gitattributes do #147.
- **tools/:** clean_project.py (limpa DNS, pasta temporária e cache do pip, fora do escopo; já está no .gitattributes), update_project_reference.py e read_outputs.py (saem do pacote; ficam enquanto a equipe os usa) e perfil_celulas.py (**não** está no .gitattributes: acrescente a linha tools/perfil_celulas.py export-ignore ou apague depois da entrega).

#### Fechamento

Rode o pytest rápido e a validação do painel num comando só:
```powershell
.\.venv\Scripts\python.exe -m pytest -m "not slow" -q; .\.venv\Scripts\python.exe .srag-status-local\server.py validar
```
Acrescente tools/read_outputs.py export-ignore ao .gitattributes do #147.

### ④ Pronto quando

- nao-existe: notebooks/C/outputs/performance/C_11_pipeline_supervisionado.csv | O arquivo de saída com o código do notebook no nome não está mais no repositório.
- nao-contem: docs/decisoes.md :: Responsável pelo registro | O decisoes.md não tem mais as linhas "Responsável pelo registro: Pessoa X".
- contem: docs/decisoes.md :: final_cohort_v1 | O contrato da coorte continua registrado depois da condensação.
- contem: docs/decisoes.md :: criar_group_id | A regra de grupo continua registrada depois da condensação.
- contem: docs/decisoes.md :: ## 28. Decisão temporal | O protocolo temporal (§28) continua registrado.
- contem: requirements.txt :: cloudpickle | O requirements.txt declara o cloudpickle, que o notebook do pipeline usa.
- contem: pyproject.toml :: cloudpickle | O pyproject.toml também declara o cloudpickle.
- teste: tests/test_config.py | Os testes de configuração passam com o cloudpickle declarado nos dois arquivos.
- manual: | A §29 do decisoes.md foi condensada sem mudar números nem títulos, com todas as decisões e todos os critérios de método preservados, e os critérios do painel sobre o decisoes.md seguem ✓.
- manual: | As docstrings longas do verificacoes.py foram reduzidas ao essencial e o pytest rápido passa.
- manual: | O .gitattributes do #147 exclui o tools/read_outputs.py do pacote da banca.
- manual: | O limpar_projeto_v2.py rodou primeiro com --simular e depois sem ele, o plano e o RELATORIO_LIMPEZA.txt foram comentados neste card, os itens que ficaram têm o motivo registrado (sem mexer no final_cohort_cli.py) e o pytest rápido passa.
- manual: | A escolha sobre o fallback GITHUB_TOKEN do storage.py (release pública ou privada) foi comentada neste card e aplicada.
- manual: | A busca --auditar-caminhos não encontra olivem85, Pfizer nem `C:\Users` em arquivo versionado, os notebooks 00 e 01 imprimem só nomes de arquivo, e a busca foi repetida depois do #126.

## #151 · Atualizar para a coorte definitiva o que os scripts não alcançam

- prioridade: P1
- situação: aberta
- estratégia: documentar
- marco: M6
- data ideal: 03/11
- responsável: Pessoa B (0,5 h) + Pessoa A (1 h) + Pessoa C (0,5 h)
- pessoas: A, B, C
- fonte: Auditoria de 02/11 (82 arquivos varridos, 651 ocorrências, 9 pontos para decisão), leitura do contrato da coorte e execução do consolidar_coorte_definitiva.py
- depende de: #150
- tags: Coorte, Documentação, Entrega
- pilar: Documentação + Valor científico-acadêmico
- carga: 2
- novo: sim
- professores: não
- arquivos: configs/final_cohort_v1.yaml, tests/test_cohort_contract.py, configs/supervised.yaml, configs/feature_contract_v1.json, docs/decisoes.md, configs/decisoes.yaml, README.md
- removido: absorvido pelos #152, #73, #126 e #154 em 03/11 (rastros da coorte provisória com lista fechada)

### ① Para entender

O pacote passa a ter **uma única coorte, a definitiva** (`coorte_final.parquet`). O resolvedor e o padrão dos notebooks C já foram trocados. O `consolidar_coorte_definitiva.py` fecha o que é automático: contrato com `status: approved`, sensibilidade "qualquer óbito" desativada, nova entrada no decisoes.md e parquets provisórios fora do repositório. Este card cobre o que continua manual.
> [!decisão] Decisão de 02/11 (Pessoa B)
> O que conta a história do projeto (como a seleção de variáveis foi construída, a comparação provisória × definitiva, o dataset provisório do fluxo A) permanece como registro rotulado. Só se atualiza o que ainda **usa** ou **cita como atual** a coorte provisória.

### ② Problema

- decisoes.md: os números da coorte provisória em §29.12 ("Números da coorte provisória"), §29.21 (referência numérica) e §29.22 (21,9% de óbitos) estão rotulados como histórico, mas só podem ser trocados pelos da definitiva depois dos resultados do G6, G7 e G8 (#78, #79 e #80).
- README.md cita `_provisorio_construcao_coorte_b.ipynb` nas linhas 69 e 180 (nome antigo; fica com o #126).
- configs/decisoes.yaml está na versão 0.5, e o decisoes.md §29.13 registra a versão 0.7: a regra "sintomas depois da internação" ainda é "manter com flag"; CS_ZONA, OUTRO_SIN e OUT_MORBI ainda estão em conditional_vars e fora de allowed_vars; ponto_de_previsao, coorte_estrita, alvo, evolucao_desconhecida e periodos ainda constam como "proposta", embora a coorte definitiva já os implemente.
- supervised.yaml e feature_contract_v1.json: o contexto incremental ainda lista `vacina_cov`, e o decisoes.md (§17 e §29.2) diz `vacina_cov_previa`. Depende de a coluna existir na coorte (#45 e #84).
- `dataset_provisorio_pessoa_a.parquet` (fluxo A, §29.26) não é a coorte provisória. Renomeá-lo mexe em decisoes.yaml, verificacoes.py e no teste dele.
- C_12 a C_16 nunca foram executados com a coorte definitiva: o padrão mudou para `final`, mas ninguém conferiu o esquema dos blocos que eles leem.
- Sobras na raiz do repositório: scripts auxiliares, hits_coorte_v2.txt e a pasta `_backup_limpeza/`.

### ③ O que fazer

#### Rodar o consolidar_coorte_definitiva.py (Pessoa B, 20 min)
- Salve o script na raiz do repositório e veja o plano sem alterar nada:
```powershell
.\.venv\Scripts\python.exe .\consolidar_coorte_definitiva.py --simular
```
- Se o plano estiver certo, aplique, valide o painel e confira tudo numa linha só (a suíte rápida roda antes e depois, então pode levar alguns minutos):
```powershell
.\.venv\Scripts\python.exe .\consolidar_coorte_definitiva.py; .\.venv\Scripts\python.exe .srag-status-local\server.py validar; .\.venv\Scripts\python.exe .\verificar_antes_do_commit.py
```
- O verificador vai listar os arquivos do contrato, do supervised.yaml, do feature_contract e do decisoes.md como "outras alterações": é esperado.
- Se a saída disser **DESFEITO**, cole-a neste card. Um teste ou arquivo ainda depende do valor antigo, e o script não deixa o repositório pior.
- Commit sem os scripts auxiliares e sem concluir nenhum card:
```powershell
git add -A -- . ':!verificar_antes_do_commit.py' ':!corrigir_criterios_coorte.py' ':!auditar_coorte_provisoria.py' ':!consolidar_coorte_definitiva.py' ':!hits_coorte_v2.txt'; git commit -m "chore: contrato da coorte aprovado, sensibilidade de qualquer óbito desativada e decisoes.md atualizado [progress:#151]"
```

#### Decisões da Pessoa A (1 h)
- decisoes.yaml (#73): decida se as cinco decisões em "proposta" passam a "aprovada" (e com qual data e responsável), se a regra "sintomas depois da internação" passa a excluir (como o decisoes.md §29.13 registra) e se CS_ZONA, OUTRO_SIN e OUT_MORBI passam a allowed_vars. Rode o pytest rápido depois: a regra de datas é lida pelos testes do fluxo A.
- Depois do G6, G7 e G8, troque os números da coorte provisória das §29.12, §29.21 e §29.22 pelos da definitiva, ou deixe só a marca "histórico".

#### Pessoa C (30 min)
- Abra C_12, C_13, C_15 e C_16 e procure `treino`, `validacao` e `teste` (esquema legado). Se aparecerem, troque pelos blocos `train_ref`, `val_tune`, `val_cal` e `test_ref`, como o C_14 já faz. Não execute o C_16: ele abre o teste.
- Confirme se a coluna `vacina_cov_previa` já existe na coorte (#45). Se existir, troque `vacina_cov` por ela no contexto incremental do supervised.yaml e do feature_contract_v1.json e rode o pytest rápido.

#### Fechamento (Pessoa B)
- README: as linhas 69 e 180 ficam com o #126.
- Mova para fora do repositório os scripts auxiliares e o hits_coorte_v2.txt. Depois, remova os backups e acrescente `_backup_limpeza/ export-ignore` ao .gitattributes do #147:
```powershell
git rm -r _backup_limpeza; git commit -m "chore: remove backups da limpeza antes da entrega"
```

### ④ Pronto quando

- contem: configs/final_cohort_v1.yaml :: status: approved | O contrato da coorte consta como aprovado.
- nao-contem: configs/final_cohort_v1.yaml :: status: candidate | O contrato não consta mais como candidato.
- contem: tests/test_cohort_contract.py :: contract.status == "approved" | O teste do contrato espera o status aprovado.
- contem: tests/test_cohort_contract.py :: test_contract_rejects_unknown_status | O teste rejeita o status que o código não aceita.
- contem: src/data/cohort_source.py :: _RETIRED_KINDS | O resolvedor só aceita a coorte definitiva.
- teste: tests/test_cohort_contract.py | Os testes do contrato passam.
- teste: tests/test_cohort_source.py | Os testes do resolvedor passam.
- contem: docs/decisoes.md :: Coorte provisória aposentada | O decisoes.md registra a aposentadoria da coorte provisória.
- nao-existe: hits_coorte_v2.txt | O levantamento com caminho da máquina não está no repositório.
- nao-existe: _backup_limpeza/LEIA-ME.txt | A pasta de backups da limpeza foi removida antes da entrega.
- manual: | O consolidar_coorte_definitiva.py rodou primeiro com --simular e depois sem ele, terminou em "CONCLUÍDO", e qualquer pacote "DESFEITO" está comentado neste card com o teste que falhou.
- manual: | A Pessoa A decidiu e registrou o que fazer com o decisoes.yaml (versão 0.5 contra 0.7 e as cinco decisões em "proposta"), e a validação do painel segue ✓.
- manual: | Os números da coorte provisória das §29.12, §29.21 e §29.22 foram trocados pelos da definitiva depois do G6, G7 e G8, ou ficaram marcados como histórico.
- manual: | C_12 a C_16 não leem mais o esquema legado (treino, validacao, teste), e o pytest rápido passa.

## #152 · Remover os rastros da coorte provisória do pacote entregue

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M6
- data ideal: 03/11
- responsável: Pessoa B (0,25 h)
- pessoas: B
- fonte: Varredura do commit 9f3322b por provis*, dataset_provisorio, pessoa_a; §29.32; revisão de 03/11 (absorve #151, #150, #41 e #43)
- depende de: —
- tags: Limpeza, Entrega, Dados/Coorte
- pilar: Documentação + Valor científico-acadêmico
- carga: 0.25
- novo: sim
- professores: não
- arquivos: .scripts/gerar_amostra_csv_revisao_features.py, .scripts/gerar_amostra_estratificada_coorte.py, notebooks/A/A6_ancora_e_selecao.ipynb, notebooks/A/A_15_fator_risco.ipynb, notebooks/acesso_verificacao_srag.ipynb, configs/supervised.yaml, README.md

### ① Para entender

A coorte provisória (803.608 fichas, 21,9% de óbitos) foi aposentada em 02/11 (§29.32): o resolvedor só aceita a definitiva. Mas ainda há arquivos que a citam, quebram se alguém os rodar ou mostram números de outra base. A banca pode abrir qualquer um deles.

### ② Problema

> [!decisão] Estado em 03/11 (commit `7533dcc`)
> O script `limpar_rastros.py` já removeu do Git os notebooks `A6_ancora_e_selecao` e `A_15_fator_risco` (o `acesso_verificacao_srag` já não existia) e retirou o `aplicar_decisoes_03_11.py` da raiz. Falta conferir o que ele não alcança: arquivos locais ignorados pelo Git e o que ainda cita a coorte provisória.

O que **fica de propósito** (história ou proteção): `tests/test_cohort_source.py` (prova que a provisória é rejeitada), `final_metadata.origem` no YAML (origem da seleção de variáveis) e as entradas históricas do decisoes.md. O que fica para outros cards: `selecao_modelos.status: shortlist_provisoria` (vira `finalista_congelado` no #1), o README (#126) e o código legado (#154).

### ③ O que fazer

**Dono:** Pessoa B · **Prazo:** 03/11, 13h15 às 13h30

1. Uma linha confere os arquivos locais e lista o que ainda cita a provisória (a pasta `.scripts` e os dois `.meta.json` são ignorados pelo Git; o Windows pode ter barrado a exclusão: feche janelas abertas nela):
```powershell
"scripts: " + (Test-Path .scripts); "meta1: " + (Test-Path data\analytical\dataset_provisorio_pessoa_a.meta.json); "meta2: " + (Test-Path data\analytical\dataset_supervisionado.meta.json); git grep -n -i -E "provis|pessoa_a" -- src tests configs notebooks docs README.md ':!tests/test_cohort_source.py'
```
2. Se algum `Test-Path` der `True`, apague: `Remove-Item -Recurse -Force .scripts; Remove-Item -Force data\analytical\dataset_provisorio_pessoa_a.meta.json, data\analytical\dataset_supervisionado.meta.json -ErrorAction SilentlyContinue`. Se `.scripts` ainda recusar, deixe vazia (não entra no Git).
3. Para cada linha do `git grep`: está na lista de "fica de propósito" ou nos cards #1, #126 e #154? Então deixe. Senão, corrija e anote.
4. Commit só se houver mudança de arquivo versionado: `chore: remove restos da coorte provisória [done:#152]`.

### ④ Pronto quando

- nao-existe: `notebooks/A/A6_ancora_e_selecao.ipynb` | O notebook do fluxo provisório A6 saiu do pacote.
- nao-existe: `notebooks/A/A_15_fator_risco.ipynb` | O notebook A_15 saiu do pacote.
- nao-existe: `notebooks/acesso_verificacao_srag.ipynb` | A duplicata do notebook de acesso saiu do pacote.
- teste: `tests/test_cohort_source.py` | Os testes que provam que a coorte provisória é rejeitada continuam passando.
- manual: | A lista do git grep foi colada como comentário, com a decisão de cada linha (fica, #1, #126, #154 ou corrigida), e os arquivos locais .scripts e .meta.json foram apagados ou conferidos.

## #153 · Remover os rastros do desenho 70/5+5+5/15 (val_tune, val_cal e val_meas)

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M6
- data ideal: 03/11
- responsável: Pessoa B (0,25 h)
- pessoas: B
- fonte: Varredura do commit 9f3322b por val_tune, val_cal, val_meas, 70/5, 5+5+5 e seis blocos; RELATORIO_SIMULACAO de 03/11; §29.33
- depende de: —
- tags: Limpeza, Documentação, Partição
- pilar: Documentação + Valor científico-acadêmico
- carga: 0.25
- novo: sim
- professores: não
- arquivos: docs/decisoes.md, data/manifest_dados-v2.yaml, notebooks/B/B_05_supervisionado_pilotos.ipynb, notebooks/B/B_02_eda_primeira_passagem.ipynb, tools/trocar_validacao_70_15_15.py

### ① Para entender

O script de troca unificou a validação em `val_ref` no código, nos testes e no YAML (§29.33). Ficaram de fora, de propósito, os textos que descrevem papéis diferentes para cada bloco antigo (o script não podia reescrever o sentido), as saídas salvas dos notebooks e alguns nomes de arquivo.

### ② Problema

> [!decisão] Estado em 03/11 (commit `7533dcc`)
> O script `limpar_rastros.py` já reescreveu a §21 e a §23 do decisoes.md no desenho 70/15/15, acrescentou o aviso de histórico nas §29.4, 29.12, 29.16, 29.17, 29.19, 29.21 e 29.22, trocou `val_tune`, `val_cal` e `val_meas` por `val_ref` no `manifest_dados-v2.yaml` e renomeou as tabelas e variáveis do B_05 e do B_02. O C_15 já tem o texto novo (script `corrigir_c15_c16.py`).

O que sobra: as **saídas salvas** do B_05 (e a frase da célula `preenchimento-05`, com os números de 39.748 fichas) só mudam quando o notebook for reexecutado (#126) e reescrito (#133). Nos C_15 e C_16, `val_cal` e `val_meas` são as **duas metades internas do `val_ref`** e continuam com esses nomes.

### ③ O que fazer

**Dono:** Pessoa B · **Prazo:** 03/11, 13h30 às 13h45

1. Confira o que sobra (uma linha; só podem aparecer saídas salvas do B_05, o C_15, o C_16 e entradas históricas do decisoes.md):
```powershell
git grep -n -E "val_tune|val_cal|val_meas|70/5|5\+5\+5|seis blocos" -- . ':!docs/decisoes.md' ':!PROJECT_STATUS*' ':!.srag-status-local' ':!notebooks/C/C_15_calibracao_limiar.ipynb' ':!notebooks/C/C_16_validacao_final.ipynb'
```
2. Se aparecer outra coisa, corrija (é texto) e anote aqui.
3. Commit só se houver mudança: `docs: remove restos do desenho 70/5+5+5/15 [done:#153]`.

### ④ Pronto quando

- nao-contem: `docs/decisoes.md` :: `A divisão 70/15/15 foi supersedida` | A §21 não diz mais que o 70/15/15 foi substituído.
- nao-contem: `docs/decisoes.md` :: `Sim; Somente confirmação` | A linha do val_ref na tabela da §21 está corrigida.
- nao-contem: `docs/decisoes.md` :: `as três validações são disjuntas` | O parágrafo das três validações saiu da §21.
- nao-contem: `data/manifest_dados-v2.yaml` :: `val_tune` | O manifesto dos dados lista só train_ref e val_ref no desenvolvimento.
- nao-contem: `notebooks/B/B_05_supervisionado_pilotos.ipynb` :: `predicoes_val_tune_piloto` | O B_05 usa o nome novo das previsões do piloto.
- contem: `docs/decisoes.md` :: `escrita para o desenho anterior, com três blocos de validação` | As entradas históricas da §29 têm o aviso de que o desenho vigente é o da §29.33.

## #154 · Remover o código legado da coorte provisória: fluxo A e esquema treino/validacao/teste

- prioridade: P3
- situação: aberta
- estratégia: despriorizar
- marco: M6
- data ideal: 04/11
- responsável: Pessoa C (1,5 h) + Pessoa A (0,5 h)
- pessoas: C, A
- fonte: Revisão de 03/11; §29.26 e §29.32 ("mantido de propósito")
- depende de: #152, #153
- tags: Limpeza, Código
- pilar: Eficiência
- carga: 2
- novo: sim
- professores: não
- arquivos: src/data/supervised_artifact.py, src/protocolo/verificacoes.py, configs/decisoes.yaml, tests/test_supervised_artifact.py, tests/test_regras_pessoa_a.py, tests/test_invariantes_protocolo.py

### ① Para entender

Dois pedaços de código só existem por causa da coorte provisória: o esquema legado do artefato (`treino`, `validacao`, `teste`) em `src/data/supervised_artifact.py` e o "fluxo A" (`src/protocolo/verificacoes.py`, com `dataset_provisorio_pessoa_a.parquet` em `configs/decisoes.yaml`).

### ② Problema

Removê-los mexe em dezenas de testes (`tests/test_supervised_artifact.py`, `tests/test_regras_pessoa_a.py`) e em funções usadas pelos testes de invariantes do protocolo. > [!decisão] Revisão de 03/11 · versão 3.2
> O projeto termina em 05/11, então "depois da entrega" não existe. Este card só é feito se #152 e #153 estiverem prontos **antes** da execução limpa (#126, 04/11, 19h) e com o pytest verde; senão, fica como está e o README cita o módulo como legado. Fazer isso na véspera da entrega troca risco por estética: fica para depois de 05/11, ou para a manhã de 04/11 só se tudo do caminho crítico estiver pronto.

### ③ O que fazer

> [!ok] Aplicado por script em 03/11 (commit `cba5d46`)
> Passos 1 e 2 prontos: o esquema legado saiu de `supervised_artifact.py` e dos testes; o fluxo A (`verificacoes.py`, `test_regras_pessoa_a.py` e a chave `dataset_analitico`) foi removido; as invariantes do #135 estão em `tests/test_invariantes_protocolo.py`. Falta só o passo 3: o `pytest -m "not slow"` verde (o verificador mostra o resultado em REVISÕES).

1. Depois do #2 (o C_16 já não usa o esquema legado): remover `_PARTICOES_LEGADAS` e os ramos `legado` de `supervised_artifact.py` e os testes `_frame_legado`.
2. Mover os testes de invariantes do protocolo (#135) de `tests/test_regras_pessoa_a.py` para `tests/test_invariantes_protocolo.py`; apagar o fluxo A (`verificacoes.py`, `dataset_analitico` do `decisoes.yaml`) e os testes que só ele usa.
3. `pytest -m "not slow"` verde antes do commit.

### ④ Pronto quando

- nao-contem: `src/data/supervised_artifact.py` :: `_PARTICOES_LEGADAS` | O esquema legado do artefato saiu do código.
- nao-existe: `src/protocolo/verificacoes.py` | O fluxo A da coorte provisória saiu do código.
- existe: `tests/test_invariantes_protocolo.py` | As cinco invariantes da partição-mestra (#135) passaram para tests/test_invariantes_protocolo.py.
- nao-existe: `tests/test_regras_pessoa_a.py` | O arquivo de testes do fluxo A foi removido.
- yaml: `configs/decisoes.yaml` :: `dataset_analitico` nao-existe | A chave dataset_analitico saiu do configs/decisoes.yaml.
- teste: `tests/test_supervised_artifact.py` | Os testes do artefato, agora só com os blocos da partição-mestra, passam.

## #155 · Equipe: explorar hiperparâmetros para melhorar o modelo antes do teste (04/11)

- prioridade: P1
- situação: aberta
- estratégia: explorar
- marco: M5
- data ideal: 04/11
- responsável: Pessoa A (2 h) + Pessoa B (2 h) + Pessoa C (2 h) + Equipe
- pessoas: A, B, C, Equipe
- fonte: Decisão da equipe em 03/11: um dia de exploração antes de abrir o teste; §29.17 (plano do G6); revisão de 03/11 (v4.0: reescrito para o que o src aceita)
- depende de: #1, #79, #158
- tags: Modelagem, Tuning, Equipe
- pilar: Performance + Valor científico-acadêmico
- carga: 6
- novo: sim
- professores: não
- arquivos: configs/supervised.yaml, notebooks/C/C_13_boosting.ipynb, notebooks/C/C_15_calibracao_limiar.ipynb

### ① Para entender

O #1 entrega um modelo de referência com uma grade curta. Antes de abrir o teste, que é definitivo, a equipe passa um dia tentando superá-lo: outros hiperparâmetros, outra regularização, outro peso de classe. **Só o que o `src` já aceita**, sem código novo e sem regerar o artefato.

O risco é escolher "o que deu mais sorte" na validação. Por isso o card tem quatro travas: **orçamento fixo** de configurações por frente, **pré-seleção num recorte interno do treino** (o `val_ref` só confirma as poucas finalistas), **regra de troca registrada antes de rodar** e **intervalo de confiança do ganho**. Se nada passar, fica o modelo do #1, e isso também é um resultado.

### ② Problema

**Ponto de partida (medido hoje no C_14: 30 variáveis, hiperparâmetros padrão, treino em `train_ref`, medida em `val_ref`):**

| Família | PR-AUC | ROC-AUC | Brier (sem calibrar) | Tempo de ajuste |
|---|---|---|---|---|
| Logística (`class_weight=balanced`) | 0,3202 (3,8× o acaso) | 0,8555 | 0,1609 | 8 s |
| Boosting (padrão do `src`) | 0,3527 (4,2× o acaso) | 0,8662 | 0,1592 | 12 a 16 s |

Com ajustes de 8 a 16 s, o limite é **estatístico**, não de tempo: 40 configurações por frente cabem em menos de uma hora, e mais configurações só aumentariam o risco de escolher ruído.

> [!atenção] O que o `src` aceita (corrige a versão anterior deste card)
> - **Boosting** (`build_boosting_pipeline`): `learning_rate`, `max_iter`, `max_depth`, `max_leaf_nodes`, `min_samples_leaf`, `l2_regularization`, `early_stopping`, `validation_fraction`, `n_iter_no_change`, `class_weight`.
> - **Logística** (`build_logistic_pipeline`): `C`, `penalty` (l2, l1, elasticnet), `l1_ratio`, `solver`, `max_iter`, `class_weight`. L1 exige `liblinear` ou `saga`; elastic-net exige `saga`.
> - Qualquer outra chave é **ignorada pela fábrica** com um `RuntimeWarning`: o teste rodaria com outro modelo sem ninguém perceber. Por isso ficam de fora `max_features`, `interaction_cst`, splines, interações e variáveis derivadas (as derivadas exigiriam código em `src/` e regerar o artefato, e o C_15 e o C_16 leem as colunas do manifesto).

> [!atenção] Armadilha do `class_weight`
> A fábrica descarta valores `null` do YAML. `class_weight: null` **não** treina sem peso: vale o padrão `balanced`. Para treinar sem peso, escreva `class_weight: {}`. Depois de editar o YAML, confira com o comando abaixo (deve imprimir `{}` para a família sem peso):

```powershell
.\.venv\Scripts\python.exe -c "from src.models.factory import build_finalista as b;print(b('logistic').steps[-1][1].class_weight, b('boosting').steps[-1][1].class_weight)"
```

**Por que não testar direto no `val_ref`:** cada configuração medida nele gasta um pouco da sua honestidade, e ele ainda serve para calibrar e escolher o limiar. A solução é um **recorte interno do treino** (`train_ref` dividido por grupo: 85% ajusta, 15% compara) e levar ao `val_ref` só as 3 melhores de cada frente.

### ③ O que fazer

**Dono:** Equipe (A: logística L2 · B: logística L1 e elastic-net · C: boosting) · **Prazo:** 04/11, 9h às 17h (**corte duro às 17h**) · **Começa quando:** #1, #79 e #158 · **Script previsto:** `explorar_hiperparametros.py` (começa por relatório e ensaio sintético; faz o recorte, o sorteio, a confirmação e a regra). **Plano B sem o script:** o C_13 com a grade do YAML (só varia taxa, iterações, profundidade e peso), no `val_ref`; é menos defensável, mas cabe no tempo.

##### 0. Regras combinadas antes de rodar (9h, 15 min, todos)
- **Registre** no `docs/decisoes.md` a entrada `#### 29.37 04/11 · Exploração de hiperparâmetros antes do teste` com as regras abaixo, **antes** de rodar qualquer coisa.
- **Métrica de escolha:** PR-AUC no recorte interno; desempate por Brier bruto e depois pela configuração mais simples.
- **Orçamento:** no máximo **40 configurações por frente**, sorteadas com semente fixa (`random_state=42`). Nada de "só mais uma".
- **Confirmação:** as **3 melhores de cada frente** vão ao `val_ref`.
- **Regra de troca:** a configuração nova só substitui a do #1 se **(a)** ganhar **≥ 0,005 de PR-AUC** no `val_ref`, **(b)** não piorar a ROC-AUC em mais de 0,002 e **(c)** o intervalo de 95% da diferença de PR-AUC (bootstrap por grupo, 300 réplicas) tiver o limite inferior acima de zero. Empate dentro de 0,002: a mais simples. Troca de família (logística ↔ boosting) segue a §29.17 (o boosting só vence com ≥ 0,005).
- **Proibido:** carregar `test_ref` ou `test_pandemic`; mexer em variáveis, partição ou código de `src/`.

##### 1. Recorte interno do treino (10 min; os três usam o mesmo)
```python
import hashlib
h = treino["group_id"].astype(str).map(lambda g: int(hashlib.sha256(("interno42" + g).encode()).hexdigest()[:8], 16) / 0xFFFFFFFF)
ajuste, comparacao = treino[h < 0.85], treino[h >= 0.85]
```
Grave os `id_registro` de cada parte em `resultados/exploracao/recorte_interno_ids.csv` para os três usarem exatamente as mesmas fichas.

##### 2. Frente C · boosting (`HistGradientBoostingClassifier`)
Sorteie 40 combinações (`ParameterSampler`, `random_state=42`) de:

| Hiperparâmetro | Valores |
|---|---|
| `learning_rate` | 0,03 · 0,05 · 0,08 · 0,1 |
| `max_iter` (com `early_stopping=True`, que já é o padrão) | 300 · 600 · 1000 |
| `max_leaf_nodes` | 15 · 31 · 63 |
| `min_samples_leaf` | 20 · 50 · 100 · 200 |
| `l2_regularization` | 0 · 0,1 · 1 · 10 |
| `max_depth` | None · 6 · 10 |
| `class_weight` | `balanced` · None (no código; no YAML, `{}`) |

##### 3. Frente A · logística com L2 (`solver="lbfgs"`)
`C` ∈ {0,001 · 0,003 · 0,01 · 0,03 · 0,1 · 0,3 · 1 · 3 · 10 · 30} × `class_weight` ∈ {`balanced`, None}: 20 configurações.

##### 4. Frente B · logística com L1 e elastic-net (`solver="saga"`)
`C` ∈ {0,01 · 0,03 · 0,1 · 0,3 · 1 · 3} × {L1 · elastic-net com `l1_ratio` 0,3 · elastic-net com `l1_ratio` 0,6} × `class_weight` ∈ {`balanced`, None}: 36 configurações. O `saga` é bem mais lento que o `lbfgs`: **meça uma configuração antes**; se passar de 3 minutos, use uma subamostra de 300 mil linhas do recorte de ajuste. O L1 zera variáveis fracas e facilita a leitura (a §29.17 já pedia uma rodada com L1).

##### 5. Confirmação e escolha (15h às 16h, todos)
- Cada frente traz as suas 3 melhores. Na máquina oficial, rode as 9 no `val_ref` e grave `resultados/exploracao/confirmacao.csv`: frente, configuração, PR-AUC e ROC-AUC no recorte e no `val_ref`, Brier, segundos de ajuste.
- Para cada candidata a trocar o modelo do #1: `bootstrap_grupo(y, prob_nova, grupos, metrica="ap", prob_b=prob_do_1, n=300, seed=42)`.
- Aplique a regra do passo 0, em voz alta, linha a linha. Se nada passar, **fica o modelo do #1** (registre assim mesmo).

##### 6. Congelar e recalibrar (16h às 17h, máquina oficial)
- Atualize no YAML os hiperparâmetros, o `class_weight` (com `{}` para "sem peso"), `selecao_modelos.finalista_escolhido` e `selecao_modelos.status: finalista_congelado`. Rode o comando do `class_weight` da caixa acima.
- Rode o C_15 final (**não** rode o C_13 de novo): o calibrador e o limiar dependem do modelo.
```powershell
.\.venv\Scripts\python.exe tools\medir_notebook.py notebooks\C\C_15_calibracao_limiar.ipynb --salvar-no-lugar --limite-mb 12288
```
- Atualize `calibracao.metodo` e `limiar.otimo` com a saída do C_15 (todas as casas decimais) e complete a §29.37 (tabela do passo 5, regra aplicada, decisão final e a frase: "as métricas de validação são otimistas porque a validação foi usada para escolher; a medida de referência é a do teste").
- `pytest -q` e commit: `feat: exploração de 04/11 e modelo final congelado antes do teste [done:#155]`.
- **17h:** o que não estiver concluído **não entra**. O modelo do #1 permanece.

##### Não testar agora
Mudar a coorte ou a partição; variáveis derivadas, splines e interações; `vacina` e `vacina_cov`; reamostragem (SMOTE e subamostragem estragam a calibração); variáveis do momento depois da internação; qualquer coisa que exija código novo em `src/` ou regerar o artefato.

### ④ Pronto quando

- contem: `docs/decisoes.md` :: `Exploração de hiperparâmetros antes do teste` | O decisoes.md tem a entrada 29.37 com as regras (registradas antes de rodar), a tabela de confirmação e a decisão final.
- existe: `resultados/exploracao/confirmacao.csv` | As 9 configurações confirmadas no val_ref (3 por frente), com as métricas no recorte e no val_ref, estão em resultados/exploracao/confirmacao.csv.
- yaml: `configs/supervised.yaml` :: `selecao_modelos.finalista_escolhido` != `null` | O finalista final está congelado no YAML depois da exploração.
- notebook-executado: `notebooks/C/C_15_calibracao_limiar.ipynb` | O C_15 foi executado de novo com o modelo final, para que calibração e limiar correspondam a ele.
- manual: | Ninguém carregou test_ref nem test_pandemic durante a exploração (o G9 só foi aprovado em 05/11, no #2); cada pessoa confirmou por comentário neste card.

## #156 · Tirar caminhos locais (pasta do usuário e da empresa) das saídas salvas dos notebooks

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M7
- data ideal: 04/11
- responsável: Pessoa C (0,25 h)
- pessoas: C
- fonte: Revisão dos notebooks de 03/11 (v3.3): 165 caminhos absolutos nas saídas de B_02, B_04, B_05, C_12, C_13 e C_15
- depende de: —
- tags: Notebook, Entrega, Privacidade
- pilar: Documentação
- carga: 0.25
- novo: sim
- professores: não

### ① Para entender

Os notebooks imprimem caminhos como `C:\Users\<usuário>\OneDrive - <empresa>\Documents\GitHub\Projeto_Integrador\outputs\…` (em "Run registrado em", "fonte", "Gravado:" etc.). O pacote de referência mascara isso como `<REPO>` e `<HOME>`, mas **os arquivos .ipynb reais guardam o caminho completo**, com o nome do usuário e da empresa. A banca veria isso em qualquer notebook aberto no GitHub.

### ② Problema

Contagem nas saídas salvas do commit `863dd45`: B_02 37, B_04 58, B_05 18, C_12 16, C_13 16, C_15 17, `acesso_verificacao_srag` 3. A reexecução do #126 e a do C_16 (#2) gravam tudo de novo, então a limpeza é feita **depois** de cada execução, e não antes. O comando abaixo troca a raiz do repositório por `.` e a pasta do usuário por `~`, sem mexer em código nem em números, e preserva as quebras de linha do arquivo.

### ③ O que fazer

**Dono:** Pessoa C · **Quando:** em 04/11, logo depois da execução limpa (#126); em 05/11, logo depois do C_16 (#2) · **Esforço:** 2 min por vez

1. Na raiz do repositório, um comando (limpa e já confere; a conferência no fim deve sair vazia):
```powershell
.\.venv\Scripts\python.exe -c "import pathlib,functools;R=str(pathlib.Path.cwd());H=str(pathlib.Path.home());S=[(v.replace('\\',e),k) for v,k in ((R,'.'),(H,'~')) for e in ('\\\\\\\\','\\\\','\\')];m=[p for p in pathlib.Path('notebooks').rglob('*.ipynb') if (lambda t0:(lambda t:t!=t0 and p.write_bytes(t.encode('utf-8'))>0)(functools.reduce(lambda a,s:a.replace(*s),S,t0)))(p.read_bytes().decode('utf-8'))];print(len(m),'notebook(s) sem caminhos locais')"; git grep -n -I -i -E "olivem85|OneDrive - |C:.{1,4}Users" -- notebooks
```
2. Se o `git grep` listar alguma linha, ela é um formato que o comando não cobriu: troque à mão no notebook (abra, apague a saída da célula e rode a célula de novo) ou me mande a linha.
3. Commit junto com o da execução: `chore: remove caminhos locais das saídas dos notebooks [done:#156]` (o `[done]` só no de 05/11).

### ④ Pronto quando

- nao-contem: `notebooks/B/B_04_eda_temporal_clustering.ipynb` :: `OneDrive - ` | O B_04 não mostra mais a pasta local nas saídas.
- nao-contem: `notebooks/C/C_15_calibracao_limiar.ipynb` :: `OneDrive - ` | O C_15 não mostra mais a pasta local nas saídas.
- manual: | O git grep por olivem85 e "OneDrive - " em notebooks ficou vazio depois da execução limpa e depois do C_16.

## #157 · Pôr os resultados finais no pacote: tabelas e figuras citadas no relatório (outputs/ é ignorado pelo Git)

- prioridade: P1
- situação: aberta
- estratégia: documentar
- marco: M8
- data ideal: 05/11
- responsável: Pessoa A (0,5 h)
- pessoas: A
- fonte: Revisão do repositório de 03/11 (v3.3): .gitignore ignora outputs/*, reports/figures/* e data/analytical/*
- depende de: #2, #55, #91, #155, #160
- tags: Entrega, Reprodutibilidade, Relatório
- pilar: Documentação + Valor científico-acadêmico
- carga: 0.5
- novo: sim
- professores: não

### ① Para entender

O relatório cita cada número com o arquivo de origem (`outputs/tables/...`). Mas o `.gitignore` ignora `outputs/*`, `outputs/tables/*`, `outputs/predictions/*`, `reports/figures/*` e `data/analytical/*`: **nenhuma tabela, figura ou manifesto de resultado entra no repositório**, nem no zip do `git archive`. A banca só veria os números dentro das saídas salvas dos notebooks.

### ② Problema

Os dados (coorte, artefato e previsões linha a linha) **não** devem ir: são grandes e são dados de pacientes, ainda que públicos e anonimizados. Vão só as tabelas agregadas, as figuras e os manifestos (hashes, contagens), que permitem conferir o que o relatório diz.

### ③ O que fazer

**Dono:** Pessoa A · **Prazo:** 05/11, 14h às 14h30 (depois do #2, #55 e #91; antes do #147) · **Script previsto:** `montar_resultados.py` (copia só o que o relatório cita, **bloqueia `.parquet` e `C6ENSAIO_*`**, tira caminhos locais dos JSON e gera o índice; começa por relatório). O que segue é o plano B.

1. Crie a pasta `resultados/` (a `resultados/exploracao/` já existe desde o #155) e copie para ela, **sem renomear**, só o que o relatório cita: a tabela de janelas e as tabelas por ano, por grupo e de calibração do C_16 (`C6_*_janelas.csv`, `*_metricas_por_ano.csv`, `*_por_grupo_*.csv`, `*_fn_por_*.csv`, `*_ic_bootstrap.csv`, `*_matriz_confusao.csv`), as tabelas do C_15 (`C5_*_escolhas.csv` e a comparação de peso de classe), a busca do C_13, `ablacoes_val_ref.csv`, `outputs/final/maturidade_desfecho_por_ano.csv` (#160), as tabelas do #55 e do #91, os manifestos `C5_*_manifesto.json` e `C6_*_manifesto.json`, `data/analytical/manifesto_particao.json`, `manifesto_supervisionado.json` e `coorte_final.manifest.json`, e as figuras que entram no relatório (`reports/figures/...`).
2. **Nada de `.parquet`** (previsões linha a linha e dados ficam de fora) **e nada com o prefixo `C6ENSAIO_`** (são do ensaio). Rode nos JSON o comando de caminhos locais do #156 adaptado (troque `notebooks` por `resultados` e `*.ipynb` por `*.json`) e confira com `git grep -n -i olivem85 -- resultados`.
3. Escreva `resultados/LEIA-ME.md`: uma linha por arquivo dizendo qual notebook o gerou e em que seção do relatório aparece.
4. `git add resultados` (a pasta não é ignorada). No relatório (#133), troque as legendas `outputs/tables/...` por `resultados/...`. Commit: `docs: resultados finais no pacote [done:#157]`.

### ④ Pronto quando

- existe: `resultados/LEIA-ME.md` | A pasta de resultados do pacote tem o índice dos arquivos.
- manual: | Todas as tabelas e figuras citadas no relatório estão em resultados/, nenhum .parquet entrou e as legendas do relatório apontam para resultados/.

## #158 · Uma máquina oficial para a cadeia que termina no teste (artefato, manifestos e C_15 final no mesmo computador)

- prioridade: P1
- situação: aberta
- estratégia: documentar
- marco: M4
- data ideal: 03/11
- responsável: Pessoa C (0,25 h) + Pessoa A (0,25 h)
- pessoas: C, A
- fonte: Leitura do C_15 e do C_16 (commit 5c9e205): o C_16 procura o manifesto do C_15 em outputs/tables e compara o dataset_sha256
- depende de: —
- tags: Entrega, Reprodutibilidade, Gate
- pilar: Eficiência + Valor científico-acadêmico
- carga: 0.5
- novo: sim
- professores: não

### ① Para entender

`data/` e `outputs/` ficam **fora do Git**. O artefato supervisionado e o manifesto de cada notebook existem só no computador de quem os gerou.

O C_16 recusa abrir o teste se não achar, **no mesmo computador**, o manifesto do C_15 com o `dataset_sha256` do artefato. Esse hash é do arquivo Parquet inteiro: o mesmo conteúdo gravado por outra versão do pyarrow ou de outro sistema pode ter hash diferente.

### ② Problema

Hoje há mais de um computador com artefatos que podem ser diferentes. O #132 (commit `1550fcc`) foi executado num; o pacote de referência de 03/11, gerado em outro, ainda mostra o manifesto antigo (31 variáveis, hash `53d48a3f…`).

Se o C_15 final rodar num computador e o C_16 noutro, o C_16 para com "Nenhum manifesto C5 compatível". Isso acontece **antes** de abrir o teste, então não causa dano, mas custa o tempo de refazer o C_15 às 8h do dia da abertura.

### ③ O que fazer

**Dono:** Equipe decide; A e C executam · **Prazo:** 03/11, 12h às 12h30, antes do #79 · **Esforço:** ≈ 30 min

1. **Escolha uma máquina oficial** para: o C_13 do #1, o C_15 do #79 e o final do #155, a execução limpa (#126), o ensaio e o C_16 (#2). Padrão: a máquina que executou o #132 (artefato com 30 variáveis).
2. **Nela, confira o artefato** (esperado: `30 True False`, o hash e as contagens 556462 / 119243 / 119245 / 2915829):
```powershell
.\.venv\Scripts\python.exe -c "import json;m=json.load(open('data/analytical/manifesto_supervisionado.json',encoding='utf-8'));print(len(m['feature_columns']),'saturacao' in m['feature_columns'],'fadiga' in m['feature_columns'],m['dataset_sha256'][:12],m['partition_counts'])"
```
3. **As outras máquinas não regeram o artefato** (não rodam o A_03 nem `gerar_artefato_supervisionado`). Para explorar o #155 elas copiam da máquina oficial, para a pasta `data/analytical/`, quatro arquivos: `dataset_supervisionado.parquet`, `manifesto_supervisionado.json`, `partitions_master.parquet` e `manifesto_particao.json`. Rodam o comando do passo 2 e conferem que o hash é o mesmo.
4. **O que cada máquina produz na exploração viaja por Git**, em `resultados/exploracao/` (pasta versionada), e não em `outputs/` (ignorado). O YAML também viaja por Git.
5. **O C_15 e o C_16 rodam só na máquina oficial.** Se a Pessoa B precisar executar o #79, ela o faz nessa máquina (compartilhando a tela) ou recebe o artefato por cópia e devolve o manifesto `C5_*` gerado.
6. Comente neste card qual é a máquina oficial e o hash (12 caracteres).

### ④ Pronto quando

- manual: | A máquina oficial foi escolhida e comentada neste card, o comando do passo 2 mostrou 30 variáveis (saturação dentro, fadiga fora) e o hash, e as outras máquinas copiaram o artefato com o mesmo hash ou não rodam o C_15 nem o C_16.

## #159 · Corrigir o B_04, o B_05, o 01_extracao e o B_02 antes da execução limpa (três variáveis saíram do modelo)

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M6
- data ideal: 03/11
- responsável: Pessoa B (0,75 h)
- pessoas: B
- fonte: Leitura dos notebooks no commit 5c9e205: a célula caracterizacao-01 do B_04 exige perd_olft, perd_pala e fadiga entre as variáveis do modelo
- depende de: —
- tags: Notebook, Entrega
- pilar: Documentação + Valor científico-acadêmico
- carga: 0.75
- novo: sim
- professores: não
- arquivos: notebooks/B/B_04_eda_temporal_clustering.ipynb, notebooks/B/B_05_supervisionado_pilotos.ipynb, notebooks/01_extracao.ipynb, notebooks/B/B_02_eda_primeira_passagem.ipynb

### ① Para entender

Em 03/11 três sintomas saíram do modelo e o artefato foi regerado com 30 variáveis (#140 e #132). Os notebooks da cadeia C (C_11 a C_15) leem a lista de variáveis do manifesto e continuam funcionando. O B_04 e o B_05 têm listas próprias de sintomas, escritas antes dessa mudança, e o B_04 está salvo desde 27/10: ninguém o executou depois.

### ② Problema

- **B_04, célula `caracterizacao-01`:** `ns_faltantes = set(NS_COMORBIDADES + NS_SINTOMAS_SECUNDARIOS + ["idade_anos"]) - set(NS_NUMERICAS + NS_CATEGORICAS)` levanta `KeyError`. `NS_NUMERICAS` e `NS_CATEGORICAS` vêm do manifesto (agora 30 variáveis) e a lista de sintomas secundários inclui `perd_olft`, `perd_pala` e `fadiga`. As três continuam no artefato como colunas de auditoria (`sensibilidade_marcador_periodo`), então a leitura que vem logo depois funciona: só a conferência falha, e a execução limpa pararia nela.
- **B_04, textos:** a célula `agrupamento-01` diz "só com as 31 variáveis do modelo" e "η² por postos nas numéricas" (a função agora calcula a ANOVA, com Kruskal-Wallis como conferência: #137); a "Conclusão geral" (célula `18bcf6e8`) repete "31 variáveis".
- **B_05, célula `preenchimento-01`:** diz "os 24 campos de sintomas e comorbidades do modelo". Três deles deixaram de ser variáveis do modelo (continuam no artefato, então a análise segue válida).
- **01_extracao, célula 9 (`772d90ab`):** a primeira linha é o comentário "# SUBSTITUA AS CÉLULAS DAS SEÇÕES 4 E 5 DO 01_extracao.ipynb POR ESTA CÉLULA.", e a célula 10 ("Teste isolado do pré-processador esparso") não faz parte da extração.
- **B_02, célula `87c910a5`:** `display(df.head())` mostra cinco notificações individuais (número, datas, sexo e idade) no GitHub.

### ③ O que fazer

**Dono:** Pessoa B · **Prazo:** 03/11, 12h30 às 13h15, antes da execução limpa · **Script previsto:** `corrigir_notebooks_b.py` (começa por relatório; faz os passos 1 a 5). Os passos manuais abaixo são o plano B.

1. **B_04, `caracterizacao-01`:** troque a linha do `ns_faltantes` por:
```python
ns_faltantes = set(NS_COMORBIDADES + NS_SINTOMAS_SECUNDARIOS + ["idade_anos"]) - set(NS_NUMERICAS + NS_CATEGORICAS + list(ns_manifesto.get("audit_columns") or []))
```
2. **B_04, textos:** em `agrupamento-01`, "só com as 31 variáveis do modelo" → "só com as 30 variáveis do modelo" e "η² por postos nas numéricas" → "η² da ANOVA nas numéricas (com Kruskal-Wallis como conferência)". Em `18bcf6e8`, "usa as 31 variáveis do modelo" → "usa as 30 variáveis do modelo". Os números do agrupamento (silhueta, V de Cramér etc.) **não** se mexem agora: são reescritos no #133, depois da execução limpa.
3. **B_05, `preenchimento-01`:** troque "os 24 campos de sintomas e comorbidades do modelo" por "os 24 campos de sintomas e comorbidades da ficha (três deles, perda de olfato, perda de paladar e fadiga, deixaram de ser variáveis do modelo e ficam no artefato)".
4. **01_extracao:** apague a linha "# SUBSTITUA AS CÉLULAS…" da célula 9 e apague a célula 10.
5. **B_02, `87c910a5`:** troque `display(df.head())` por `display(df.head(0))`.
6. **Não execute os notebooks agora** (a execução é a do #126). Confira que os quatro continuam sendo JSON válido e rode a suíte rápida:
```powershell
.\.venv\Scripts\python.exe -c "import json;[json.load(open(p,encoding='utf-8')) for p in ('notebooks/B/B_04_eda_temporal_clustering.ipynb','notebooks/B/B_05_supervisionado_pilotos.ipynb','notebooks/01_extracao.ipynb','notebooks/B/B_02_eda_primeira_passagem.ipynb')];print('json ok')"; .\.venv\Scripts\python.exe -m pytest -q
```
7. Commit: `fix: B_04 e B_05 aceitam as 30 variáveis; textos e sobras dos notebooks [progress:#159] [progress:#137]`.

### ④ Pronto quando

- nao-contem: `notebooks/B/B_04_eda_temporal_clustering.ipynb` :: `31 vari` | O B_04 não cita mais 31 variáveis do modelo.
- contem: `notebooks/B/B_04_eda_temporal_clustering.ipynb` :: `audit_columns` | A conferência do B_04 aceita as colunas de auditoria, onde ficam as três variáveis que saíram do modelo.
- nao-contem: `notebooks/B/B_04_eda_temporal_clustering.ipynb` :: `por postos nas num` | O texto do B_04 descreve a ANOVA, e não só o Kruskal-Wallis.
- nao-contem: `notebooks/01_extracao.ipynb` :: `SUBSTITUA AS C` | O 01_extracao não tem mais a instrução de edição.
- nao-contem: `notebooks/B/B_02_eda_primeira_passagem.ipynb` :: `display(df.head())` | O B_02 não mostra mais notificações individuais.

## #160 · Maturidade do desfecho por ano: quantas internações ficaram de fora por falta de desfecho e se 2025 está maduro

- prioridade: P2
- situação: aberta
- estratégia: documentar
- marco: M6
- data ideal: 04/11
- responsável: Pessoa A (0,5 h)
- pessoas: A
- fonte: Orientação do TCC (etapa 5: medir desfechos pendentes, atrasos e estabilidade de 2025); contrato da coorte (D_COORTE_003: 530.370 linhas)
- depende de: —
- tags: Dados/Coorte, Metodologia, Relatório
- pilar: Valor científico-acadêmico
- carga: 0.5
- novo: sim
- professores: sim

### ① Para entender

A regra D_COORTE_003 exclui 530.370 internações (11% da base) porque a evolução não é cura nem óbito por SRAG: óbito por outra causa, ignorado ou em branco. Se essa exclusão se concentra nos anos mais recentes, a mortalidade observada neles fica artificialmente baixa, porque os casos mais demorados ainda não foram encerrados.

A orientação do TCC pede "medir desfechos pendentes, atrasos e estabilidade de 2025". O `decisoes.md` só trata disso para 2026 (§29.15: cerca de 12% de desfechos em aberto). Falta o mesmo número para 2019–2025.

### ② Problema

A mortalidade observada cai ano a ano nos anos de desenvolvimento (12,0% em 2019, 9,4% em 2023, 8,2% em 2024 e 7,2% em 2025, registrada no #139). Parte da queda pode ser maturidade, parte pode ser mudança de perfil e de preenchimento. A banca vai perguntar.

Esta análise é **descritiva**: usa só `dt_interna`, `hospital` e `evolucao` da base inteira, como já faz a auditoria da coorte (`regras_por_ano.csv`), e **não altera** a coorte, a partição nem o período (decisões fechadas em 18/10 e 22/10).

### ③ O que fazer

**Dono:** Pessoa A · **Prazo:** 04/11, 8h às 8h30 · **Script previsto:** `maturidade_desfecho.py` (só lê; começa por relatório). O comando abaixo é o plano B (não foi testado com os dados reais).

1. Gere a tabela (uma linha; grava `outputs/final/maturidade_desfecho_por_ano.csv` e mostra na tela):
```powershell
.\.venv\Scripts\python.exe -c "import os,pandas as pd;from src.utils import storage;d=storage.read_srag(columns=['dt_interna','hospital','evolucao']);d=d[pd.to_numeric(d['hospital'],errors='coerce').eq(1)].copy();d['ano']=pd.to_datetime(d['dt_interna'],errors='coerce').dt.year;e=pd.to_numeric(d['evolucao'],errors='coerce');d['desfecho']=e.map({1:'cura',2:'obito',3:'obito_outra_causa',9:'ignorado'}).fillna('vazio');t=pd.crosstab(d['ano'],d['desfecho']);t['n']=t.sum(axis=1);fora=[c for c in ('obito_outra_causa','ignorado','vazio') if c in t.columns];t['pct_sem_desfecho_util']=(t[fora].sum(axis=1)/t['n']*100).round(1);os.makedirs('outputs/final',exist_ok=True);t.to_csv('outputs/final/maturidade_desfecho_por_ano.csv');print(t.to_string())"
```
2. Leia a coluna `pct_sem_desfecho_util` por ano. Se 2025 tiver um percentual bem maior que 2023 e 2024 (por exemplo, o dobro), escreva a limitação: "a queda da mortalidade observada ao longo dos anos pode refletir, em parte, desfechos ainda não encerrados". Se for parecido, escreva que a exclusão por desfecho é estável entre os anos.
3. Dois parágrafos para o relatório (#133, seção Dados e coorte): a tabela e a leitura. **Não** mude o período, a coorte nem a partição por causa deste resultado: é uma limitação a declarar, não uma decisão a reabrir.

### ④ Pronto quando

- existe: `outputs/final/maturidade_desfecho_por_ano.csv` | A tabela de desfecho por ano da base de hospitalizados (cura, óbito, óbito por outra causa, ignorado e vazio) está em outputs/final/maturidade_desfecho_por_ano.csv.
- manual: | O relatório (#133) tem a tabela e a leitura da maturidade do desfecho, incluindo a frase sobre 2025.

## #161 · Ajustes de avaliação antes da abertura do teste: raça/cor e zona, hipóteses registradas, referência só idade e sexo, memória

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M5
- data ideal: 04/11
- responsável: Pessoa A (0,5 h) + Pessoa C (0,25 h)
- pessoas: A, C
- fonte: Orientação do TCC (raça/cor, escolaridade e zona: incluir com cautela, avaliar equidade); C_14 e C_16 no commit 5c9e205
- depende de: —
- tags: Teste, Equidade, Metodologia
- pilar: Valor científico-acadêmico
- carga: 0.75
- novo: sim
- professores: sim
- arquivos: configs/supervised.yaml, notebooks/C/C_14_ablacoes_variaveis.ipynb, docs/decisoes.md

### ① Para entender

O teste é aberto uma vez. O que o C_16 vai calcular precisa estar pronto **antes**, e o que esperamos ver precisa estar escrito **antes** de ver. Este card junta quatro ajustes pequenos que não cabiam em nenhum outro.

### ② Problema

- **Raça/cor e zona:** `cs_raca` e `cs_zona` são variáveis do modelo, e a orientação pede avaliar a equidade. O C_16 calcula métricas por grupo a partir de `avaliacao.grupos`, que hoje lista só `sg_uf`, `sexo_categoria`, `faixa_etaria` e `ano_internacao` (a região entra por fora). Como as variáveis do modelo só ficam guardadas na janela principal, a tabela sai para o **Teste A**; no Teste B o notebook avisa que pulou o grupo.
- **Hipóteses:** a prevalência é 8,4% no desenvolvimento e cerca de **26% em 2020–2022**. Um modelo calibrado a 8,4% deve subestimar o risco nesse período, e isso não é defeito do modelo. Escrever a expectativa antes impede que pareça desculpa depois.
- **Referência simples:** "o modelo é melhor do que só usar idade e sexo?" é a pergunta clássica. A linha custa uma linha de código no C_14, que roda de novo no #126.
- **Memória do `test_pandemic`:** o C_11 mostrou pico de 1,4 GB com o treino de 556 mil linhas; o `test_pandemic` tem 2,9 milhões (estimativa por extrapolação: 5 a 8 GB, **não medida**: o teste não pode ser carregado antes do G9).

### ③ O que fazer

**Dono:** Pessoa A (itens 1 e 2) + Pessoa C (itens 3 e 4) · **Prazo:** itens 1 e 3 em 04/11 de manhã; item 2 até 04/11 às 22h; item 4 em 05/11 às 7h45

1. **Raça/cor e zona (A, 5 min).** Em `configs/supervised.yaml`, na lista `avaliacao.grupos`, acrescente duas linhas depois de `- ano_internacao`: `- cs_raca` e `- cs_zona` (mesmo recuo). Códigos de `cs_raca`: 1 branca, 2 preta, 3 amarela, 4 parda, 5 indígena, 9 ignorado (confirmar no dicionário, #70); o branco vira o grupo "AUSENTE". Rode `pytest -q` depois.
2. **Hipóteses registradas (A, 15 min).** Crie no `docs/decisoes.md` a entrada `#### 29.38 04/11 · Hipóteses registradas antes da abertura do teste` e faça o commit **antes** do #2 (o horário do commit é a prova). Conteúdo sugerido (ajuste os números como a equipe achar justo):
   - Teste A (`test_ref`, prevalência ≈ 8,4%): PR-AUC entre 0,30 e 0,36 (3,6× a 4,3× o acaso) e ROC-AUC entre 0,85 e 0,87, perto do `val_ref`.
   - `test_pandemic` (prevalência ≈ 26%): PR-AUC absoluta **maior**, mas PR-AUC ÷ prevalência igual ou menor; Brier pior; razão observado/esperado **acima de 1** (hipótese: entre 1,5 e 3), porque o calibrador foi ajustado a 8,4%.
   - Teste B (prevalência ≈ 26%): fica entre os dois, mais perto do `test_pandemic` por volume.
   - Se algum resultado contrariar uma hipótese, a contradição entra no relatório como achado, **nunca** como motivo para ajustar o modelo, a calibração ou o corte.
3. **Referência só idade e sexo (C, 10 min).** No C_14, dentro de `executar_ablacoes`, no dicionário `linhas`, acrescente depois da linha `"P": ...`:
```python
        "so_idade_sexo": (df, [c for c in num if c == "idade_anos"], [c for c in cat if c == "sexo_categoria"], ["logistic"]),
```
A linha entra na tabela com a diferença para `P` já calculada. **Não rode agora**: o C_14 roda de novo no #126. Guarde para o relatório: PR-AUC ÷ prevalência de "só idade e sexo" contra a de `P` (3,8×).
4. **RAM (C, 5 min, 05/11 às 7h45).** Na máquina oficial, feche o navegador e o Teams e veja a memória livre (precisa de pelo menos 14 GB: o limite do medidor é 12 GB, mais folga):
```powershell
"{0:N1} GB livres" -f ((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB)
```
Se faltar, o #2 roda noutra máquina com mais memória (e com o artefato e o manifesto do C_15 copiados, #158).

### ④ Pronto quando

- yaml: `configs/supervised.yaml` :: `avaliacao.grupos` contem `cs_raca` | A avaliação por grupo inclui raça/cor.
- yaml: `configs/supervised.yaml` :: `avaliacao.grupos` contem `cs_zona` | A avaliação por grupo inclui a zona.
- contem: `docs/decisoes.md` :: `Hipóteses registradas antes da abertura do teste` | O decisoes.md tem as hipóteses do teste, escritas antes da abertura.
- contem: `notebooks/C/C_14_ablacoes_variaveis.ipynb` :: `so_idade_sexo` | O C_14 tem a linha de referência só com idade e sexo.
- manual: | A Pessoa C confirmou, em 05/11 às 7h45, que há pelo menos 14 GB de memória livre na máquina oficial (ou que o #2 roda noutra máquina).

## #162 · Ponto de corte por região (pedido do professor de 24/10): modelo único, corte regional escolhido na validação e medido no teste

- prioridade: P2
- situação: aberta
- estratégia: desenvolver
- marco: M5
- data ideal: 04/11
- responsável: Pessoa B (0,5 h) + Pessoa A (0,5 h)
- pessoas: B, A
- fonte: Orientação de 24/10 (D-14 da base v10: modelo único com corte por região e métricas por região, pendente desde o #110); revisão de 03/11
- depende de: #79
- tags: Equidade, Gate, Calibração
- pilar: Valor científico-acadêmico
- carga: 1
- novo: sim
- professores: sim
- arquivos: notebooks/C/C_15_calibracao_limiar.ipynb, notebooks/C/C_16_validacao_final.ipynb, configs/supervised.yaml
- removido: absorvido pelo #55 em 03/11 (v4.1): decisão da equipe de fazer só a versão mínima (modelo único, corte global e métricas e calibração por região no teste); o corte regional vira limitação e trabalho futuro (frase no #133, resposta pronta no #134, registro no #73)

### ① Para entender

O professor descreveu a prática de mercado: **um modelo único** para o país e **um ponto de corte diferente por região**. A geografia entra como separação da análise, não como variável do modelo.

| O que fazemos | Para quê |
|---|---|
| Modelo único, sem geografia | Variáveis com significado clínico |
| Corte da região escolhido na validação, com a mesma regra do corte global | Utilidade local: cada região com sensibilidade perto de 80% |
| Métricas e calibração por região no teste | Equidade: o modelo erra mais ou superestima o risco em algum lugar? |

Este item era o #110. Eu o absorvi no #55 em 03/11 e escrevi "sem cortes por região", o que contrariava o pedido. Volta como card próprio.

### ② Problema

Hoje o C_15 escolhe um único limiar (`limiar.otimo`) e o C_16 usa só ele. **O mínimo já existe:** o C_16 calcula sensibilidade e precisão por região no corte global (tabela `*_por_grupo_teste_a_regiao_residencia.csv`). Falta o corte regional.

Cuidados: (i) o corte regional é escolhido em `val_meas` (cerca de 5 mil óbitos no total); região com menos de 100 óbitos usa o corte global e é marcada; (ii) a grade de cortes do C_15 tem 101 pontos (passo de 0,01 numa escala onde o corte fica perto de 0,1): passa para 197 pontos (passo de 0,005), no corte global também; (iii) o calibrador é **um só**, ajustado em `val_cal`.

### ③ O que fazer

**Dono:** Pessoa B (C_15) + Pessoa A (C_16) · **Prazo:** 04/11, 8h às 9h, antes do #155 · **Script previsto:** `corte_regional.py` (começa por relatório e ensaio sintético; altera o C_15 e o C_16; o YAML continua sendo editado à mão, como o `limiar.otimo`).

1. **C_15:** depois de escolher o corte global do finalista, para cada região (`regiao_residencia` de `val_meas`) com pelo menos 100 óbitos, chame `escolher_limiar` com a mesma regra do global (`metrica`, `min_precision` e `min_recall` do YAML) e `n_limiares=197`. Região com menos de 100 óbitos ou sem corte viável: usa o global (`usa_global=True`). Grave `{prefixo}_limiares_por_regiao.csv` (região, n, óbitos, corte, sensibilidade, precisão, `usa_global`) e inclua `limiares_por_regiao` no manifesto `C5_*`.
2. **YAML (à mão, depois da execução final do C_15):** `limiar.por_regiao` com o mapa região → corte, ao lado de `limiar.otimo`.
3. **C_16:** antes de abrir o teste, trava: `limiar.por_regiao` do YAML precisa ser igual ao `limiares_por_regiao` do manifesto `C5_*`. No Teste A, uma tabela por região com sensibilidade e precisão no corte global e no regional (`{prefixo}_por_regiao_cortes.csv`).
4. **Relatório (#55):** uma figura (corte global × regional por região) e três frases: a diferença de sensibilidade entre regiões com o corte global, o que o corte regional corrige e o que não corrige. Escreva "heterogeneidade entre regiões, que pode refletir acesso, capacidade e registro", nunca uma causa.

**Plano B (se o script não passar no relatório ou faltar tempo):** versão mínima. Nada a fazer: o C_16 já entrega a tabela por região no corte global, e o relatório diz que o corte regional não foi implementado por falta de tempo (limitação).

### ④ Pronto quando

- yaml: `configs/supervised.yaml` :: `limiar.por_regiao` existe | O YAML tem o corte de cada região, escolhido na validação.
- contem: `notebooks/C/C_15_calibracao_limiar.ipynb` :: `limiares_por_regiao` | O C_15 calcula e grava os cortes por região.
- contem: `notebooks/C/C_16_validacao_final.ipynb` :: `por_regiao_cortes` | O C_16 mede o corte global e o regional por região no Teste A.
- manual: | O relatório tem a figura e as três frases sobre o corte por região, ou registra que ficou só a versão mínima (tabela por região no corte global).

## #163 · Teste de clone limpo: instalar e rodar como a banca (pasta nova, ambiente novo, sem dados nem artefatos locais)

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M7
- data ideal: 04/11
- responsável: Pessoa A (0,75 h)
- pessoas: A
- fonte: Incidente de 03/11 (requirements.txt apagado sem querer, percebido só pelo pytest); base v10 (qualquer pessoa precisa rodar o projeto do início ao fim)
- depende de: #126
- tags: Entrega, Reprodutibilidade
- pilar: Eficiência + Documentação
- carga: 0.75
- novo: sim
- professores: não

### ① Para entender

Tudo o que funciona na sua pasta pode depender de algo que só existe nela: um arquivo apagado, um pacote instalado à mão, um dado em cache. O único teste honesto é clonar do GitHub numa pasta nova, com um ambiente novo, e rodar. O quase-incidente do `requirements.txt` (apagado por engano em `1848dd3`) mostra o risco.

### ② Problema

A banca recebe o que está no GitHub (ou o zip do `git archive`), sem `data/`, sem `outputs/` e sem artefato. O que ela consegue rodar é: instalar, os testes, os notebooks 00 e 01 (baixam a base) e a leitura dos notebooks já executados. O C_16 **não** roda de novo (o teste já foi aberto).

A base de dados vem da release `dados-v2` do GitHub. Se a release for **privada**, o download exige `GITHUB_TOKEN` e a banca não consegue reproduzir sem ele: isso precisa estar escrito no README.

### ③ O que fazer

**Dono:** Pessoa A · **Prazo:** 04/11, 22h às 22h45, **depois** do commit e do push do #126 · **Esforço:** ≈ 45 min, quase tudo de espera

1. Clone o que está no GitHub (não a sua pasta), crie o ambiente e instale só pelo `requirements.txt`, e rode a suíte:
```powershell
cd $env:TEMP; Remove-Item -Recurse -Force clone_teste -ErrorAction SilentlyContinue; git clone https://github.com/Ivan-S-Oliveira/Projeto_Integrador.git clone_teste; cd clone_teste; python -m venv .venv; .\.venv\Scripts\python.exe -m pip install -r requirements.txt; .\.venv\Scripts\python.exe -m pytest -q
```
2. Notebooks 00 e 01 (baixam a base, cerca de 300 MB). Sem `--salvar-no-lugar`, a cópia executada vai para `outputs/notebooks/` e o original não muda:
```powershell
.\.venv\Scripts\python.exe tools\medir_notebook.py notebooks\00_acesso_dados_parquet.ipynb --limite-mb 12288; .\.venv\Scripts\python.exe tools\medir_notebook.py notebooks\01_extracao.ipynb --limite-mb 12288
```
Se pedir token, a release é privada: escreva no README que a banca precisa do token (ou de outra forma de obter a base).
3. Procure caminhos locais no clone (deve sair vazio):
```powershell
git grep -n -I -i -E "olivem85|OneDrive - |C:.{1,4}Users"
```
4. No navegador, abra no GitHub os notebooks de agrupamento e de validação final. Se algum não renderizar (arquivo grande demais), diga no README que ele deve ser baixado.
5. Confira se o README diz a versão do Python testada (a das execuções finais, 3.14.7; o `pyproject.toml` pede 3.11 ou mais).
6. Apague a pasta: `Remove-Item -Recurse -Force $env:TEMP\clone_teste`. Comente o resultado neste card (o que passou e o que falhou).

### ④ Pronto quando

- manual: | O clone limpo instalou pelo requirements.txt, o pytest rápido passou, os notebooks 00 e 01 rodaram (ou o README diz que a release é privada), o git grep por caminhos locais saiu vazio e o resultado está comentado neste card.

## #164 · Caminhos relativos no código: tirar a pasta do usuário e da empresa de resumos, registros e manifestos (causa raiz do #156)

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M7
- data ideal: 04/11
- responsável: a definir (0,5 h)
- pessoas: Equipe
- fonte: Revisão do src/ de 04/11 (snapshot 741fbbe): caminhos absolutos gerados por config.resumo, reproducibility._env_info e supervised_artifact
- depende de: —
- tags: Código, Entrega, Privacidade
- pilar: Documentação
- carga: 0.5
- novo: sim
- professores: não
- arquivos: src/utils/config.py, src/utils/reproducibility.py, src/data/supervised_artifact.py, src/data/final_cohort_cli.py, tests/test_config.py

### ① Para entender

O #156 limpou os caminhos absolutos das saídas salvas dos notebooks, mas eles **voltam a cada execução**, porque nascem no código, e não nos notebooks. São quatro fontes:

| Onde | O que grava hoje |
|---|---|
| `src/utils/config.py::resumo()` | `ROOT_DIR`, `DATA_DIR`, `OUTPUTS_DIR`… absolutos, impressos no começo de quase todo notebook |
| `src/utils/reproducibility.py::_env_info()` | `cwd` e `python_executable` absolutos em todo `outputs/runs/<RUN_ID>/metadata.json` |
| `src/data/supervised_artifact.py` | `dataset_path`, `partition_path` e `source.path` absolutos nos manifestos `manifesto_supervisionado.json` e `manifesto_particao.json` |
| `src/data/final_cohort_cli.py` | caminhos da fonte e da coorte nos manifestos da coorte (`coorte_final.manifest.json`, `manifesto_coorte.json`) |

Na máquina oficial, esses caminhos contêm o nome do usuário e a pasta sincronizada da empresa (`C:\Users\<usuário>\OneDrive - <empresa>\…`). O pacote de referência mascara como `<HOME>` e `<REPO>`, mas os arquivos reais, não.

### ② Problema

- A execução limpa (#126) vai regravar todas as saídas e manifestos **com os caminhos pessoais de novo**, desfazendo o #156.
- Os manifestos vão para o pacote entregue (`data/analytical/*.json` e as tabelas citadas no #157).
- O `metadata.json` de cada execução grava também o executável do Python, com o mesmo caminho.

### ③ O que fazer

**Tempo:** ≈ 30 min · **Antes de:** execução limpa (#126). Todo script começa por um relatório numa cópia, como combinado.

1. **Em `src/utils/config.py`**, acrescente a função (depois de `ROOT_DIR`):
```python
def caminho_relativo(caminho) -> str:
    """Caminho relativo à raiz do projeto, sem pastas pessoais.

    Fora do projeto, devolve só o nome do arquivo.
    """
    p = Path(caminho).resolve()
    try:
        return p.relative_to(ROOT_DIR).as_posix()
    except ValueError:
        return p.name
```
2. **`resumo()`**: troque cada valor `Path` por `caminho_relativo(...)`. Exemplo: `("ROOT_DIR", "."), ("DATA_DIR", caminho_relativo(DATA_DIR))`.
3. **`reproducibility._env_info()`**: `"cwd": caminho_relativo(Path.cwd())` e `"python_executable": Path(sys.executable).name`.
4. **`supervised_artifact.py`**: nos campos `dataset_path` e `partition_path`, use `C.caminho_relativo(...)`. Em `source.to_dict()` (vem de `cohort_source.CohortSource`), faça o mesmo com `path`. **Atenção:** `load_supervised_artifact` sobrescreve `manifest["dataset_path"]` com o caminho absoluto só em memória; isso pode ficar, porque não é gravado.
5. **`final_cohort_cli.py`**: procure os `str(path)` que entram em manifestos e aplique `caminho_relativo`.
6. **Teste** em `tests/test_config.py`:
```python
def test_caminho_relativo_nao_expoe_pasta_pessoal():
    from src.utils import config as C
    assert C.caminho_relativo(C.ROOT_DIR / "data" / "x.parquet") == "data/x.parquet"
    assert "Users" not in C.caminho_relativo("C:/Users/fulano/arquivo.txt")
```
7. Rode `python -m pytest -q` e, depois da execução limpa, confira:
```powershell
git grep -n -i "OneDrive\|C:\\Users" -- notebooks data/analytical outputs/tables configs
```
8. Commit: `fix: caminhos relativos em resumos, registros e manifestos [done:#164]`.

> [!atenção] Não altere o hash dos artefatos por isso
> Os caminhos estão no manifesto, e não no Parquet: o `dataset_sha256` não muda. Mas, se o artefato for regerado, os manifestos novos já saem limpos.

### ④ Pronto quando

- define: `src/utils/config.py` :: `caminho_relativo` | A função caminho_relativo existe em config.py e devolve caminhos relativos à raiz do projeto.
- contem: `src/utils/reproducibility.py` :: `caminho_relativo` | O registro de cada execução grava o diretório de trabalho como caminho relativo.
- contem: `src/data/supervised_artifact.py` :: `caminho_relativo` | Os manifestos do artefato e da partição gravam caminhos relativos.
- teste: `tests/test_config.py::test_caminho_relativo_nao_expoe_pasta_pessoal` | O teste garante que nenhuma pasta pessoal aparece no caminho devolvido.
- nao-contem: `data/analytical/manifesto_supervisionado.json` :: `OneDrive` | O manifesto do artefato não tem a pasta sincronizada da empresa.
- manual: | Depois da execução limpa, o git grep por OneDrive e C:\Users não encontrou nada em notebooks, manifestos e tabelas.

---

## #165 · C_16: O/E, calibração e Brier relativo por janela, e parada se a árvore Git estiver suja

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M5
- data ideal: 04/11
- responsável: a definir (0,75 h)
- pessoas: Equipe
- fonte: Revisão de 04/11: a hipótese registrada da §29.38 (O/E entre 1,5 e 3 em 2020–2022) não é calculada pelo C_16; metadata.json de 03/11 com dirty = true
- depende de: #148
- tags: Notebook, Teste, Calibração, Reprodutibilidade
- pilar: Valor científico-acadêmico
- carga: 0.75
- novo: sim
- professores: não
- arquivos: notebooks/C/C_16_validacao_final.ipynb, src/evaluation/calibration.py

### ① Para entender

A §29.38 registrou, antes da abertura do teste, que no período pandêmico o modelo deve **ordenar bem** o risco, mas **subestimar o nível**: **O/E** (óbitos observados ÷ soma das probabilidades previstas) entre 1,5 e 3, porque foi calibrado com 8,4% de óbitos e a pandemia teve 26%. É o resultado mais relevante do teste do ponto de vista de saúde pública: um modelo calibrado num período e aplicado em outro.

Hoje, porém, a tabela `janelas_df` do C_16 (célula 12) calcula `metricas_completas` mais PR-AUC ÷ prevalência, sem O/E e sem medida de calibração. A hipótese registrada **não seria conferida**.

Ao mesmo tempo, os cinco registros de execução de 03/11 (B_05 e C_11 a C_15) têm `"git": {"dirty": true}`: rodaram com mudanças não commitadas. Para o C_16, que abre o teste uma única vez, isso precisa ser impossível.

### ② Problema

- Sem O/E, inclinação de calibração e Brier relativo por janela, a §29.38 fica sem resposta.
- O `ece` do projeto usa 10 faixas de largura fixa: com prevalência de 8%, quase todas as previsões caem nas duas primeiras faixas. O `ece_quantis` (faixas com o mesmo número de fichas) já existe em `src/evaluation/calibration.py` e é mais informativo, mas nenhum notebook o usa.
- O intercepto de `calibracao_intercepto_inclinacao` é estimado junto com a inclinação; ele **não** é a calibração geral (*calibration-in-the-large*). Para a calibração geral, use O/E e a diferença entre média prevista e observada.

### ③ O que fazer

**Tempo:** ≈ 45 min · **Antes do G9.** Testar no **modo ensaio** (`SRAG_C16_ENSAIO=1`).

1. **Imports** (célula de imports do C_16):
```python
from src.evaluation.calibration import calibracao_intercepto_inclinacao, ece_quantis
```
2. **Na célula 12, dentro do laço que monta `janelas_df`**, depois de `m = metricas_completas(...)`, acrescente:
```python
y_j, p_j = y_por_janela[nome], p_por_janela[nome]   # use os nomes reais do notebook
prev = float(np.mean(y_j))
brier_nulo = prev * (1 - prev)
_, inclinacao = calibracao_intercepto_inclinacao(y_j, p_j)
m.update({
    "o_e": float(np.sum(y_j) / np.sum(p_j)),
    "media_prevista": float(np.mean(p_j)),
    "media_observada": prev,
    "inclinacao_calibracao": inclinacao,
    "ece_quantis": ece_quantis(y_j, p_j, n_bins=10),
    "brier_nulo": brier_nulo,
    "brier_relativo": 1 - m["brier"] / brier_nulo,
})
```
   **Leitura:** O/E = 1 é calibração perfeita no total; inclinação < 1 indica previsões "espalhadas demais", > 1 "comprimidas demais"; Brier relativo > 0 indica melhor que dizer a prevalência para todos.
3. **Por ano** (célula 16): acrescente `o_e` e `media_prevista` à tabela de calibração por ano, para mostrar a "travessia" 2019 → 2020–2022 → 2023–2025.
4. **Parada com árvore suja** (célula que confere gates, antes de qualquer leitura do teste):
```python
from src.utils.reproducibility import _git_info
_g = _git_info()
if _g.get("dirty") and os.getenv("SRAG_ALLOW_DIRTY") != "1" and not MODO_ENSAIO:
    raise RuntimeError(
        "Árvore Git com mudanças não commitadas: commit antes de abrir o teste "
        "(ou SRAG_ALLOW_DIRTY=1 com justificativa no decisoes.md)."
    )
print("commit:", _g.get("commit"), "| dirty:", _g.get("dirty"))
```
5. **Rode o ensaio** e confira que as colunas novas saem preenchidas e plausíveis (no ensaio, O/E perto de 1).
6. Registre na §29.38, **antes do G9**, uma linha: "O/E, inclinação de calibração, ECE por quantis e Brier relativo são reportados por janela; leitura conforme a hipótese acima".
7. Commit: `feat: calibracao por janela e trava de arvore suja no C_16 [done:#165]`.

### ④ Pronto quando

- contem: `notebooks/C/C_16_validacao_final.ipynb` :: `o_e` | O C_16 calcula a razão entre óbitos observados e esperados por janela.
- contem: `notebooks/C/C_16_validacao_final.ipynb` :: `calibracao_intercepto_inclinacao` | O C_16 calcula a inclinação de calibração por janela.
- contem: `notebooks/C/C_16_validacao_final.ipynb` :: `ece_quantis` | O C_16 usa o ECE por quantis, adequado a prevalência baixa.
- contem: `notebooks/C/C_16_validacao_final.ipynb` :: `brier_relativo` | O C_16 reporta o Brier relativo ao modelo nulo.
- contem: `notebooks/C/C_16_validacao_final.ipynb` :: `SRAG_ALLOW_DIRTY` | O C_16 se recusa a abrir o teste com mudanças não commitadas.
- contem: `docs/decisoes.md` :: `Brier relativo` | A §29.38 registra, antes da abertura, as medidas de calibração por janela.
- manual: | O ensaio do C_16 rodou com as colunas novas preenchidas.

---

## #166 · C_15 final: corrigir o rótulo do veredito do peso de classe e conferir que o manifesto grava a regra do limiar

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M5
- data ideal: 04/11
- responsável: Pessoa B (0,25 h)
- pessoas: B
- fonte: Revisão de 04/11: célula 8 do C_15 rotula como balanced a linha de Brier 0,063181 (variante sem peso); manifesto C5_..._20261103T202752Z e metadata.json registram limiar_metrica = f1
- depende de: #79
- tags: Notebook, Calibração, Gate
- pilar: Valor científico-acadêmico + Documentação
- carga: 0.25
- novo: sim
- professores: não
- arquivos: notebooks/C/C_15_calibracao_limiar.ipynb

### ① Para entender

O C_15 decide G7 (calibração) e G8 (limiar) e compara o peso de classe. Duas coisas no estado de 03/11 não batem com o que ele realmente fez:

1. A tabela **"Veredito (menor Brier pós-calibração)"** (célula 8) mostra `hist_gradient_boosting · balanced · 0,063181 · 0,360909`. Mas 0,063181 e 0,3609 são os números da variante **sem peso** (`class_weight` = `NaN` na tabela de comparação logo acima, que tem `balanced` com 0,063349 e 0,3554). A recomendação impressa no fim (`nan` = sem peso) está certa; o rótulo não.
2. O manifesto `outputs/tables/C5_calibracao_limiar_final_20261103T202752Z_manifesto.json` e o `metadata.json` da mesma execução gravam `"limiar_metrica": "f1"`. A saída do notebook salvo mostra `precision (min_recall=0.8)` e o limiar 0,1178 é o da regra de precisão. É o rótulo de uma execução intermediária ou de um valor lido antes do YAML ser atualizado.

### ② Problema

O C_16 confere o manifesto do C_15 antes de abrir o teste. A banca e o relatório citam o veredito. Rótulos trocados viram pergunta difícil ("vocês escolheram com ou sem peso?").

### ③ O que fazer

**Tempo:** ≈ 15 min · **Junto da execução final do C_15** (04/11, 16h–17h).

1. **Célula 8:** encontre o trecho que monta o veredito (provavelmente um `groupby("finalista")` com `idxmin()` sobre o Brier). O rótulo vem da coluna `class_weight`, que tem `NaN` para "sem peso" e algum preenchimento (`fillna`) está trocando. Substitua por:
```python
comparacao["peso"] = comparacao["class_weight"].map(lambda v: "sem peso" if pd.isna(v) or v in ({}, "{}", None) else str(v))
veredito = comparacao.loc[comparacao.groupby("finalista")["brier"].idxmin(), ["finalista", "peso", "brier", "pr_auc"]]
```
2. **Texto da célula 7:** tire "ainda não se mediu sem peso" e "item #5". Escreva: "o G6 escolheu sem peso (§29.35); esta tabela confirma depois da calibração".
3. Rode o C_15 final e confira **no manifesto novo**: `"limiar_metrica": "precision"` e `"min_recall": 0.8`.
4. Se ainda sair `f1`, procure onde o manifesto lê a métrica: deve ser `LIMIAR_METRICA` (lido de `C.cfg("limiar")`), e não um valor fixo.
5. Commit junto com o #79.

### ④ Pronto quando

- notebook-saida: `notebooks/C/C_15_calibracao_limiar.ipynb` :: `sem peso` | A tabela de veredito mostra o peso de classe com o rótulo correto.
- nao-contem: `notebooks/C/C_15_calibracao_limiar.ipynb` :: `item #5` | O texto do C_15 não cita mais a pendência antiga do peso de classe.
- manual: | O manifesto da execução final do C_15 registra limiar_metrica = precision e min_recall = 0.8.

---

## #167 · Colar os textos corrigidos no B_04 (células 155 e 156), no B_05 (célula 52), no C_14 (célula 7) e no B_02 (células 28, 45 e 46)

- prioridade: P1
- situação: aberta
- estratégia: documentar
- marco: M6
- data ideal: 04/11
- responsável: Pessoa B (0,75 h)
- pessoas: B
- fonte: Conferência número a número de 04/11 contra as saídas salvas (snapshot 741fbbe); documento "Pendências lotes 2 e 3", partes C1 a C5
- depende de: #159
- tags: Notebook, Entrega
- pilar: Documentação + Valor científico-acadêmico
- carga: 0.75
- novo: sim
- professores: não
- arquivos: notebooks/B/B_04_eda_temporal_clustering.ipynb, notebooks/B/B_05_supervisionado_pilotos.ipynb, notebooks/C/C_14_ablacoes_variaveis.ipynb, notebooks/B/B_02_eda_primeira_passagem.ipynb

### ① Para entender

As saídas do B_04 e do B_05 já foram regeradas com as 30 variáveis e o `val_ref`, mas os textos de leitura ainda descrevem a execução anterior (31 variáveis, `val_tune` de 39.748 fichas, peso de classe no boosting). O #159 corrige o **código**; este card corrige o **texto**, que é o que a banca lê.

**Mudança de leitura importante (B_04):** com as 30 variáveis, o corte em três grupos do hierárquico **deixou de ter salto quase igual** ao de dois (42,1 contra 77,7). Os três grupos passam a ser só um nível de descrição.

### ② Problema

| Notebook · célula | Texto atual | Saída atual |
|---|---|---|
| B_04 · 155 | silhueta 0,392; salto 63,1; 46,9/30,3/22,7%; óbito 4,0%; cortes 35,0–95,9; 2019 com 4,6% | 0,395; 77,7; 47,2/30,3/22,5%; 4,1%; 38,0–80,2; 2,4% |
| B_04 · 156 | itens 6 e 7 das implicações (indicadores de ausência; saturação em sensibilidade) | ambos superados (§29.6 e §29.34) |
| B_05 · 52 | `val_tune` (39.748; 3.355 óbitos); ROC-AUC 0,872/0,868/0,766; O/E ≈ 0,25 por peso | `val_ref` (119.243; 10.064); 0,881/0,871/0,780; boosting sem peso, O/E 0,97–1,02 |
| C_14 · 7 | "manter/retirar, porque …" (modelo não preenchido) | decisão da §29.34 |
| B_02 · 28 / 45 | "25 variáveis"; "3.847,05 MB" | 100 variáveis; 1.021,28 MB |

### ③ O que fazer

**Tempo:** ≈ 45 min · **Antes da execução limpa** (#126).

1. Abra o documento `Pendencias_Lotes_2e3_src_e_notebooks_B_04-11-2026.md`, partes **C1 a C5**: os textos estão prontos para colar.
2. **B_04 · 155:** substitua a célula inteira pelo texto de C1. Antes, abra `outputs/final/perfil_clusters_hca.csv` e `perfil_clusters_kmeans.csv` e preencha os três valores marcados com ⟨conferir⟩ (η² da idade, V dos sintomas secundários e η² do intervalo).
3. **B_04 · 156:** aplique as cinco trocas de C2 (seção de saturação, seção dos quatro estados, implicações 6 e 7, encerramento).
4. **B_05 · 52:** substitua pelo texto de C3. Na mesma passada: troque `"O B_07 exige"` por `"Este notebook exige"` e explicite, no §11 e no §20, que são **duas logísticas diferentes** (§11 sem peso, treino inteiro; §20 com `balanced`, amostra de 300 mil).
5. **C_14 · 7:** texto de C4; confira −0,0002 e −0,0004 na saída da execução limpa.
6. **B_02:** as três trocas de C5.
7. **Não reexecute** só por causa do texto: o #126 reexecuta tudo. Commit: `docs: textos dos notebooks com os numeros atuais [done:#167]`.

### ④ Pronto quando

- nao-contem: `notebooks/B/B_04_eda_temporal_clustering.ipynb` :: `0,392` | O B_04 não cita mais a silhueta da execução com 31 variáveis.
- contem: `notebooks/B/B_04_eda_temporal_clustering.ipynb` :: `0,395` | O B_04 cita a silhueta atual da rodada de quatro estados.
- nao-contem: `notebooks/B/B_04_eda_temporal_clustering.ipynb` :: `manter saturação e desconforto respiratório como sensibilidade` | A implicação superada sobre saturação foi atualizada.
- nao-contem: `notebooks/B/B_05_supervisionado_pilotos.ipynb` :: `val_tune` | O B_05 não cita mais o bloco de validação antigo.
- contem: `notebooks/B/B_05_supervisionado_pilotos.ipynb` :: `0,881` | O texto do B_05 traz o ROC-AUC atual do padrão sem respostas "não".
- nao-contem: `notebooks/C/C_14_ablacoes_variaveis.ipynb` :: `manter/retirar, porque` | A decisão do C_14 está preenchida.
- nao-contem: `notebooks/B/B_02_eda_primeira_passagem.ipynb` :: `3.847,05` | O B_02 cita a memória da leitura compactada.

---

## #168 · decisoes.md coerente com o desenho final: §1.1, §1.2, §29.9, cabeçalho e entradas 29.36 e 29.37

- prioridade: P1
- situação: aberta
- estratégia: documentar
- marco: M7
- data ideal: 04/11
- responsável: a definir (0,5 h)
- pessoas: Equipe
- fonte: Revisão de 04/11: §1.1 e §1.2 contradizem §29.34 e §29.35; §29.36 e §29.37 citadas e inexistentes; §29.9 com título de tarefa interna
- depende de: #79, #155
- tags: Documentação, Metodologia
- pilar: Documentação + Valor científico-acadêmico
- carga: 0.5
- novo: sim
- professores: não
- arquivos: docs/decisoes.md

### ① Para entender

O `decisoes.md` é a fonte do "porquê" do projeto e vai no pacote. A parte de cima (§1, "status das decisões") é o que a banca lê primeiro, e hoje ela descreve o desenho de 27/10. Este card complementa o #73 com a lista exata do que está errado.

### ② Problema

| Trecho | O que diz hoje | O que é verdade em 04/11 |
|---|---|---|
| Cabeçalho | "Última atualização: 02/11/2026" | 04/11 |
| §1.1 | "seleção de features construída e auditada na coorte provisória B" | coorte provisória aposentada (§29.32) |
| §1.1 | "`saturacao` e `desc_resp`: sensibilidade…, fora do modelo principal" | no modelo (§29.34) |
| §1.1 | "G1 aprovado em 22/10: 31 features principais; saturacao e desc_resp só em sensibilidade" | 30 variáveis (§29.34) |
| §1.1 | "Internações anteriores aos sintomas: auditoria com nosocomial antes de qualquer exclusão" | excluídas pela D_COORTE_006; `nosocomial` não está no dicionário |
| §1.1 | "em 27/10 vacina_cov foi trocada por vacina_cov_previa" | o YAML e o código ainda usam `vacina_cov`; `vacina_cov_previa` não existe |
| §1.2 | pendentes: #50, #5 ("class_weight: balanced está vigente"), G6 | decididos em 03/11 (§29.34 e §29.35) |
| §29.9 | título "Pendente (a Pessoa C escreve uma linha no card; a Pessoa A transcreve)" | tarefa interna, não decisão |
| §29.36, §29.37 | citadas 4 vezes | não existem |
| §29.23 | promete `tools/ancora_e_excluidos.py` e três tabelas | script inexistente (ver #179) |

### ③ O que fazer

**Tempo:** ≈ 30 min · **Depois do C_15 final e do #155.**

1. **Cabeçalho:** "Última atualização: 04/11/2026".
2. **§1.1:** em cada item superado, acrescente na linha seguinte `> Substituído em 03/11 (§29.34).` (mesmo padrão já usado). Para `vacina_cov_previa`, escreva: "Não implementada: o contexto incremental usa `vacina_cov`, fora do modelo principal."
3. **§1.2:** mova #50, #5 e G6 para "Decididas em 03/11 (§29.34 e §29.35)". Deixe como pendentes só: G9 e a abertura do teste.
4. **§29.9:** troque o título por "27–28/10 · Registro pendente" e tire os rótulos de pessoas.
5. **§29.36** (`#### 29.36 04/11 · G7 e G8: peso de classe, calibração e limiar`): método (sigmoid), Brier antes e depois em `val_meas`, Brier do modelo nulo (≈ 0,077), ECE, limiar com todas as casas, sensibilidade e precisão nesse corte, regra de empate e a frase da limitação (§29.33).
6. **§29.37** (`#### 29.37 04/11 · Exploração de hiperparâmetros`): orçamento, frentes (L2, L1/elastic-net, boosting), as 3 melhores de cada frente no `val_ref`, regra de troca e resultado (trocou ou manteve o G6).
7. **Numeração:** padronize as entradas 29.32 a 29.38 com `###` (hoje usam `####`) **ou** registre que a mudança é intencional.
8. Commit: `docs: decisoes.md coerente com o desenho final [done:#168]`.

### ④ Pronto quando

- contem: `docs/decisoes.md` :: `29.36` | A entrada do G7 e do G8 existe.
- contem: `docs/decisoes.md` :: `29.37` | A entrada da exploração de hiperparâmetros existe.
- nao-contem: `docs/decisoes.md` :: `Última atualização: 02/11/2026` | O cabeçalho mostra a data da última atualização real.
- nao-contem: `docs/decisoes.md` :: `a Pessoa C escreve uma linha no card` | O título da §29.9 não descreve uma tarefa interna.
- manual: | A §1.1 e a §1.2 não contradizem as §29.34 e §29.35.

---

## #169 · README final: status, gates, estratificação real, ordem de execução, tempo, memória e resultados

- prioridade: P1
- situação: aberta
- estratégia: documentar
- marco: M7
- data ideal: 04/11
- responsável: Pessoa B (0,5 h)
- pessoas: B
- fonte: Revisão do README de 04/11 (snapshot 741fbbe)
- depende de: #126
- tags: Documentação, Entrega
- pilar: Documentação
- carga: 0.5
- novo: sim
- professores: não
- arquivos: README.md

### ① Para entender

O README é a porta de entrada da banca e de quem clonar o repositório. Hoje ele descreve um projeto "em desenvolvimento", com gates pendentes que já foram aprovados. Este card detalha o que o #126 (README novo) precisa conter.

### ② Problema

- Tabela de gates: G1 e G6 "Pendente" (aprovados); G7, G8 e G9 serão aprovados em 04–05/11.
- "A lista final de atributos ainda depende da confirmação do gate G1": falso.
- Descreve a estratificação "por ano, alvo e região". O manifesto registra **"ano × alvo (fallback)"**: algum estrato com região tinha menos de 5 grupos.
- Faltam: ordem de execução da cadeia, tempo (≈ 31 min), memória (pico ≈ 4,1 GB no A_03; o C_16 pede ≈ 14 GB livres), como obter os dados, resultados principais.
- `configs/dicionario_variaveis_v1.csv` aparece na árvore: confirmar que vai no pacote.

### ③ O que fazer

**Tempo:** ≈ 30 min · **Depois do C_16** (para os números do teste).

1. **Status:** "Concluído em 05/11/2026. Teste aberto uma única vez em <data>."
2. **Gates:** tabela com G1, G2, G4–G9 e data de aprovação (copie do `supervised.yaml`).
3. **Partição:** "hash por grupo; estratificação por ano × alvo (a estratificação com região caiu porque algum estrato tinha menos de 5 grupos, como previsto no código e registrado em `manifesto_particao.json`)".
4. **Ordem de execução** (bloco de código):
```text
00_acesso_dados_parquet → 01_extracao → A/A_03 → B/B_02 → B/B_04 → B/B_05
→ C/C_11 → C/C_12 → C/C_13 → C/C_14 → C/C_15 → C/C_16 (uma vez, com G9)
```
5. **Recursos:** ≈ 31 min na máquina de referência (32 GB de RAM); pico ≈ 4,1 GB; C_16 com ≈ 14 GB livres.
6. **Resultados:** três linhas (Teste A, 2020–2022, Teste B) com PR-AUC, PR-AUC ÷ prevalência, ROC-AUC, Brier e O/E, com o link para `resultados/`.
7. **Versões:** cite o `requirements-lock.txt` (#170).
8. Commit junto com o #126.

### ④ Pronto quando

- nao-contem: `README.md` :: `ainda depende da confirmação do gate` | O README não diz mais que a lista de variáveis está pendente.
- contem: `README.md` :: `ano × alvo` | O README descreve a estratificação real da partição.
- contem: `README.md` :: `C_16` | O README traz a ordem de execução até o C_16.
- contem: `README.md` :: `requirements-lock.txt` | O README indica o arquivo com as versões exatas.

---

## #170 · Versões exatas: requirements-lock.txt da máquina oficial e pyproject coerente com o Python usado

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M7
- data ideal: 04/11
- responsável: a definir (0,25 h)
- pessoas: Equipe
- fonte: Revisão de 04/11: requirements.txt e pyproject.toml só com >=; execuções de 03/11 com Python 3.14.7, scikit-learn 1.9.1, pandas 3.0.6
- depende de: —
- tags: Reprodutibilidade, Entrega
- pilar: Documentação
- carga: 0.25
- novo: sim
- professores: não
- arquivos: requirements-lock.txt, pyproject.toml, README.md

### ① Para entender

Um clone feito daqui a um ano instalaria versões mais novas de scikit-learn e pandas. O scikit-learn muda padrões entre versões (por exemplo, o `l1_ratio` da logística a partir da 1.8), então os números podem mudar. Hoje `requirements.txt` só tem `>=` e o `pyproject.toml` declara Python 3.11/3.12, mas as execuções usaram **3.14.7**.

### ② Problema

- Sem versões exatas, ninguém reproduz o resultado com segurança.
- Teste que tenta conferir isso já existe e falha numa cópia sem o arquivo: `tests/test_config.py::test_requirements_tem_versao_fixada`.

### ③ O que fazer

**Tempo:** ≈ 15 min · **Na máquina oficial**, com o `.venv` do projeto.

1. Gere o arquivo:
```powershell
.\.venv\Scripts\python.exe -m pip freeze --exclude-editable | Out-File -Encoding utf8 requirements-lock.txt
```
2. Abra e remova pacotes de ferramentas pessoais, se houver (o `requirements.txt` continua com `>=` para instalação flexível).
3. No `pyproject.toml`, ajuste `requires-python` e os classificadores para incluir a versão usada (3.14) ou declare no README: "testado com Python 3.14.7".
4. Rode `python -m pytest -q tests/test_config.py`.
5. Commit: `build: versoes exatas da maquina oficial [done:#170]`.

### ④ Pronto quando

- existe: `requirements-lock.txt` | O arquivo com as versões exatas da máquina oficial existe.
- contem: `requirements-lock.txt` :: `scikit-learn==` | O arquivo fixa a versão do scikit-learn.
- contem: `requirements-lock.txt` :: `pandas==` | O arquivo fixa a versão do pandas.
- teste: `tests/test_config.py` | Os testes de configuração passam.

---

## #171 · supervised.yaml sem rótulos internos e com comentários atualizados

- prioridade: P1
- situação: aberta
- estratégia: documentar
- marco: M7
- data ideal: 04/11
- responsável: a definir (0,25 h)
- pessoas: Equipe
- fonte: Revisão do YAML de 04/11 (itens Y2 a Y8 do relatório do lote 1)
- depende de: #79
- tags: Configuração, Entrega
- pilar: Documentação
- carga: 0.25
- novo: sim
- professores: não
- arquivos: configs/supervised.yaml

### ① Para entender

O `supervised.yaml` é o contrato do estudo e vai no pacote. Ele ainda tem marcas de trabalho interno e comentários de etapas já concluídas.

### ② Problema

| Chave | Hoje | Correção |
|---|---|---|
| `gates.G6_finalistas_tuning.aprovado_por` | "Pessoa A e Pessoa C" | nomes reais ou "equipe" |
| `gates.G1_definicao_alvo_features` | data 22/10, lista mudou em 03/11 | acrescentar `revisado_em: "2026-11-03"` e `nota: "§29.34"` |
| `features.engenharia.recodificar_comorbidades_fator_risco` (comentário) | "decisão pendente no #140" | "não adotada (§29.34)" |
| `selecao_modelos.finalista_escolhido` | comentário "# <- era logistic, agora boosting" | tirar o comentário |
| `selecao_modelos.observacoes` | "probabilidades brutas ainda não calibradas" | "calibradas com sigmoid (G7)" |
| `selecao_modelos.nomes_execucao.logistic` | `logistica_C1_v2` | `logistica_C10` ou remover |
| `limiar.metrica` (comentário) | "# #79: …" | comentário sem card |

### ③ O que fazer

**Tempo:** ≈ 15 min · **Depois do G7 e do G8** (para não conflitar com o #79).

1. Edite cada linha da tabela. Não mude nenhum valor usado pelo código além dos comentários, de `aprovado_por` e de `observacoes`.
2. **Atenção:** o C_16 compara o hash da **seção de modelos** do YAML com o manifesto do C_15. Mudanças fora de `models` e `selecao_modelos.finalista_escolhido` não afetam essa trava; se mexer em `selecao_modelos`, rode o C_15 de novo antes do C_16.
3. Confira com:
```powershell
git grep -n "Pessoa [ABC]\|#[0-9][0-9]" -- configs/supervised.yaml
```
4. Commit: `docs: supervised.yaml sem rotulos internos [done:#171]`.

### ④ Pronto quando

- nao-contem: `configs/supervised.yaml` :: `Pessoa A` | O YAML não tem rótulos internos de pessoas.
- nao-contem: `configs/supervised.yaml` :: `era logistic, agora boosting` | O comentário informal do finalista foi removido.
- nao-contem: `configs/supervised.yaml` :: `decisão pendente no #140` | O comentário da recodificação está atualizado.

---

## #172 · Rótulos internos e nomes antigos em notebooks, mensagens do src e manifestos

- prioridade: P1
- situação: aberta
- estratégia: documentar
- marco: M7
- data ideal: 04/11
- responsável: a definir (0,5 h)
- pessoas: Equipe
- fonte: Varredura de 04/11: 15 citações de cards no B_05; "Notebook 03" no src; títulos C2…C6 nos notebooks C; campo "pendencia": "#142" em manifestos
- depende de: —
- tags: Notebook, Entrega, Código
- pilar: Documentação
- carga: 0.5
- novo: sim
- professores: não
- arquivos: notebooks/B/B_05_supervisionado_pilotos.ipynb, src/data/supervised_artifact.py, notebooks/C/C_11_pipeline_supervisionado.ipynb, notebooks/C/C_12_baseline_logistica.ipynb, notebooks/C/C_13_boosting.ipynb, notebooks/C/C_15_calibracao_limiar.ipynb, notebooks/C/C_16_validacao_final.ipynb, notebooks/A/A_03_coorte_protocolo.ipynb

### ① Para entender

A Base de Conhecimento proíbe rótulos internos (Pessoa A/B/C, #N, G1–G9 sem explicação, nomes antigos de notebook) em material da banca. O #146 renomeou os arquivos; ficaram as citações dentro deles.

### ② Problema

- **B_05:** `#142`, `#51`, `#52`, `#55`, `#110`, `#140` e "Fase E" nos textos; mensagem `"O B_07 exige o artefato…"`; campo `"pendencia": "#142"` gravado nos manifestos e no `Run`.
- **`src/data/supervised_artifact.py`:** mensagens de erro "Execute o Notebook 03 adaptado" e "Reconstrua no Notebook 03"; comentário "ver #73".
- **`src/features/engineering.py`:** docstring "Regra (decisão do #140, 30/10)".
- **C_11 a C_16:** títulos "C2…C6"; mistura "artefacto/artefato" e "Registar/Registrar".
- **A_03 · 1:** "Substitui o antigo A_03 (mover para `notebooks/A/historico/`)".
- **Testes:** comentários com cards (aceitável, mas pode limpar).

### ③ O que fazer

**Tempo:** ≈ 30 min · **Antes da execução limpa.** Script com relatório numa cópia primeiro.

1. Liste:
```powershell
git grep -n -E "#[0-9]{2,3}\b|Pessoa [ABC]|Notebook 03|\bB_0[67]\b|Fase E|\bC[2-6]\b" -- notebooks src configs README.md
```
2. Troque nos textos e mensagens: "Notebook 03" → "B_05"; "O B_07 exige" → "Este notebook exige"; títulos "C2" → "C_11", "C3" → "C_12", "C4" → "C_13", "C5" → "C_15", "C6" → "C_16".
3. No B_05, tire o campo `"pendencia"` do dicionário do manifesto e dos parâmetros do `Run`.
4. Padronize "artefato" e "Registrar".
5. **Não mude** o prefixo dos arquivos de saída (`C3_…`, `C5_…`): o C_16 procura o manifesto do C_15 pelo nome. Mude só o texto.
6. Commit: `docs: sem rotulos internos nos notebooks e mensagens [done:#172]`.

### ④ Pronto quando

- nao-contem: `src/data/supervised_artifact.py` :: `Notebook 03` | As mensagens de erro citam o notebook pelo nome atual.
- nao-contem: `notebooks/B/B_05_supervisionado_pilotos.ipynb` :: `O B_07 exige` | O B_05 não cita o nome antigo de si mesmo.
- nao-contem: `notebooks/B/B_05_supervisionado_pilotos.ipynb` :: `#142` | O B_05 não cita o card interno.
- nao-contem: `notebooks/A/A_03_coorte_protocolo.ipynb` :: `mover para` | O A_03 não tem instrução de arrumação interna.

---

## #173 · Exploração do #155 com a logística L1 e elastic-net: chamada certa da fábrica (senão vira L2 sem aviso)

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M5
- data ideal: 04/11
- responsável: Pessoa B (0,25 h)
- pessoas: B
- fonte: Revisão de src/models/factory.py e logistic.py de 04/11: o YAML passa penalty l2, que força l1_ratio = 0
- depende de: —
- tags: Modelagem, Código
- pilar: Valor científico-acadêmico
- carga: 0.25
- novo: sim
- professores: não
- arquivos: src/models/factory.py, src/models/logistic.py

### ① Para entender

Na exploração em equipe de 04/11 (#155), a sua frente é a logística com **L1** (zera coeficientes, seleciona variáveis) e **elastic-net** (mistura L1 e L2). A fábrica `build_finalista("logistic", ...)` lê `models.logistic` do YAML, que tem `penalty: l2` e `solver: lbfgs`, e soma os seus parâmetros por cima.

Dentro de `build_logistic_pipeline`, quando `penalty == "l2"`, o código **força `l1_ratio = 0`**. Então:

| Chamada | O que treina de verdade |
|---|---|
| `build_finalista("logistic", l1_ratio=0.5, solver="saga")` | **L2** com saga, sem aviso |
| `build_finalista("logistic", l1_ratio=1.0)` | **L2** com lbfgs |
| `build_finalista("logistic", penalty="l1", solver="saga", C=c, class_weight={})` | **L1** ✓ |
| `build_finalista("logistic", penalty="elasticnet", l1_ratio=0.5, solver="saga", C=c, class_weight={})` | **elastic-net** ✓ |

### ② Problema

Sem `penalty` explícito, a frente inteira mediria L2 com outro nome, e a conclusão ("L1 não ajudou") seria falsa.

### ③ O que fazer

**Tempo:** ≈ 15 min · **Antes das 9h de 04/11.**

1. Use sempre `penalty` explícito, como na tabela.
2. Depois de construir cada modelo, imprima:
```python
clf = pipe.named_steps["clf"]
print(clf.l1_ratio, clf.solver, clf.C, clf.class_weight)
```
3. `saga` com 556 mil × 122 colunas pode não convergir em `max_iter=1000` (`ConvergenceWarning`). Faça a pré-seleção numa amostra do treino (por exemplo, 150 mil, estratificada por ano e alvo) e, se aparecer o aviso no treino inteiro, registre e suba `max_iter` para 3000 só para as 3 finalistas.
4. Grade sugerida (orçamento fixo): L1 com `C ∈ {0,01; 0,1; 1; 10}`; elastic-net com `C ∈ {0,1; 1; 10}` × `l1_ratio ∈ {0,25; 0,5; 0,75}` = 13 configurações.
5. Para as razões de chances do #91, guarde quantos coeficientes a L1 zerou e quais.
6. Registre o resultado na §29.37 (#168).

### ④ Pronto quando

- manual: | Cada modelo da frente L1/elastic-net teve l1_ratio, solver e class_weight impressos e conferidos antes de ser avaliado.
- contem: `docs/decisoes.md` :: `elastic-net` | O resultado da frente está registrado na entrada da exploração.

---

## #174 · Tabelas de equidade: mínimo de óbitos por grupo, coluna de óbitos e especificidade em metricas_por_grupo

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M5
- data ideal: 04/11
- responsável: a definir (0,25 h)
- pessoas: Equipe
- fonte: Revisão de src/evaluation/errors.py de 04/11: supressão só por total de fichas (min_n = 100)
- depende de: —
- tags: Código, Equidade, Teste
- pilar: Valor científico-acadêmico
- carga: 0.25
- novo: sim
- professores: não
- arquivos: src/evaluation/errors.py, tests/test_errors.py, notebooks/C/C_16_validacao_final.ipynb

### ① Para entender

`metricas_por_grupo` calcula as métricas por UF, região, faixa etária, raça/cor e ano no teste, e alimenta as tabelas de equidade (#55). Ela suprime grupos com menos de 100 fichas, mas **não olha o número de óbitos**. Uma UF com 150 fichas e 2 óbitos recebe PR-AUC, ROC-AUC e O/E, todos sem sentido estatístico. O B_05 já usou uma regra melhor: suprimir com menos de 30 por classe.

### ② Problema

Tabelas de equidade com números instáveis podem sugerir diferenças entre grupos que são só acaso, e são as tabelas mais sensíveis do relatório.

### ③ O que fazer

**Tempo:** ≈ 15 min · **Antes do C_16.**

1. Em `src/evaluation/errors.py::metricas_por_grupo`, acrescente o parâmetro `min_eventos: int = 20` e troque a condição:
```python
n_eventos = int(y_g.sum())
suprimir = (n < min_n) or (n_eventos < min_eventos) or ((n - n_eventos) < min_eventos)
```
2. Acrescente às duas versões da linha (suprimida e calculada): `"n_obitos": float(n_eventos)` e, na calculada, `"especificidade": especificidade(y_g, y_pred)` (importe de `src.evaluation.metrics`).
3. Atualize a docstring.
4. Teste em `tests/test_errors.py`:
```python
def test_metricas_por_grupo_suprime_poucos_eventos():
    import numpy as np, pandas as pd
    from src.evaluation.errors import metricas_por_grupo
    df = pd.DataFrame({"g": ["a"] * 200})
    y = np.r_[np.ones(3), np.zeros(197)]
    p = np.linspace(0, 1, 200)
    t = metricas_por_grupo(df, y, p, "g", min_n=100, min_eventos=20)
    assert bool(t.loc[0, "suprimido"]) and t.loc[0, "n_obitos"] == 3
```
5. No C_16, confira que as chamadas passam o limiar do YAML (`limiar_ativo()`), e não 0,5.
6. Commit: `feat: minimo de eventos nas metricas por grupo [done:#174]`.

### ④ Pronto quando

- contem: `src/evaluation/errors.py` :: `min_eventos` | A função suprime grupos com poucos óbitos ou poucas curas.
- contem: `src/evaluation/errors.py` :: `n_obitos` | A tabela por grupo mostra o número de óbitos.
- teste: `tests/test_errors.py::test_metricas_por_grupo_suprime_poucos_eventos` | O teste garante a supressão por poucos eventos.

---

## #175 · Execução limpa com árvore Git limpa e suíte completa de testes

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M7
- data ideal: 04/11
- responsável: a definir (0,25 h)
- pessoas: Equipe
- fonte: metadata.json de 03/11 (B_05, C_11 a C_15) com dirty = true; suíte completa não registrada
- depende de: #164, #167, #172
- tags: Reprodutibilidade, Entrega, Teste
- pilar: Documentação + Valor científico-acadêmico
- carga: 0.25
- novo: sim
- professores: não
- arquivos: outputs/runs

### ① Para entender

Cada execução grava o commit em `outputs/runs/<RUN_ID>/metadata.json`. Se a árvore estiver "suja" (com mudanças não commitadas), o commit não reproduz o que rodou. Todas as execuções de 03/11 estão assim. Este card é a lista de conferência do #126, para que a cadeia final seja reproduzível.

### ② Problema

- `"dirty": true` em todas as execuções salvas de 03/11.
- A suíte rápida exclui testes `slow` e `net`; a completa não tem registro de execução.

### ③ O que fazer

**Tempo:** ≈ 15 min de conferência (fora o tempo da cadeia).

1. Antes de começar: `git status --short` deve sair vazio (faça commit ou `git stash`).
2. Rode a suíte completa e guarde o resultado:
```powershell
.\.venv\Scripts\python.exe -m pytest -m "" -q 2>&1 | Out-File -Encoding utf8 outputs\final\pytest_completo.txt
```
3. Rode a cadeia (#126).
4. No fim, confira que nenhuma execução nova ficou suja:
```powershell
Get-ChildItem outputs\runs -Recurse -Filter metadata.json | ForEach-Object { $j = Get-Content $_ -Raw | ConvertFrom-Json; "$($j.run_id) dirty=$($j.git.dirty)" }
```
5. Registre no #126 o commit da execução limpa.

### ④ Pronto quando

- existe: `outputs/final/pytest_completo.txt` | O resultado da suíte completa de testes foi guardado.
- manual: | Todas as execuções da cadeia final registram dirty = false.

---

## #176 · Curva de decisão (benefício líquido): utilidade do alerta por limiar no Teste A e em 2020–2022

- prioridade: P3
- situação: aberta
- estratégia: explorar
- marco: M8
- data ideal: 05/11
- responsável: a definir (0,5 h)
- pessoas: Equipe
- fonte: Parecer crítico de 04/11 (recomendação 4.3); Vickers e Elkin (2006), análise de curva de decisão
- depende de: #2
- tags: Avaliação, Teste, Saúde pública
- pilar: Valor científico-acadêmico
- carga: 0.5
- novo: sim
- professores: sim
- arquivos: notebooks/C/C_17_curva_decisao.ipynb, outputs/final/curva_decisao.csv

### ① Para entender

PR-AUC e ROC-AUC dizem se o modelo **ordena** bem o risco. Não dizem se **usá-lo para alertar** é melhor do que alternativas simples. A **curva de decisão** responde a isso. Para cada limiar *t* (por exemplo, de 2% a 40%), calcula o **benefício líquido** de três estratégias:

- **modelo**: alertar quem tem risco ≥ *t*;
- **alertar todos**;
- **não alertar ninguém** (benefício 0).

A fórmula:

$$BL(t) = \frac{VP}{n} - \frac{FP}{n} \cdot \frac{t}{1-t}$$

O fator *t* ÷ (1 − *t*) diz quanto vale um alarme falso em relação a um acerto. Escolher *t* = 10% é dizer "aceito 9 alarmes falsos para encontrar 1 óbito". O modelo é **útil** nas faixas de *t* em que sua curva fica acima das outras duas.

**Em linguagem comum:** é a pergunta "se a equipe só consegue atender um certo número de alertas, o modelo ajuda mais do que alertar todo mundo?". É o padrão em modelos de risco clínico e o que uma banca de saúde pública costuma esperar.

### ② Problema

O projeto não tem nenhuma medida de utilidade. O limiar 0,1178 é justificado pela regra de recall ≥ 80%, mas não se mostra se, nesse ponto, usar o modelo é melhor do que alertar todos.

### ③ O que fazer

**Tempo:** ≈ 30 min · **Depois do C_16**, usando só as previsões gravadas do teste (sem reajuste; não é uma escolha, é uma descrição).

1. Crie `notebooks/C/C_17_curva_decisao.ipynb` (ou uma seção no fim do C_16 antes do fechamento, se a equipe preferir um notebook só).
2. Leia o Parquet de previsões do C_16 (colunas: bloco, `y`, probabilidade calibrada).
3. Função:
```python
import numpy as np, pandas as pd
def curva_decisao(y, p, limiares=np.arange(0.02, 0.41, 0.01)):
    y = np.asarray(y).astype(int); p = np.asarray(p); n = len(y); prev = y.mean()
    linhas = []
    for t in limiares:
        alerta = p >= t
        vp = int((alerta & (y == 1)).sum()); fp = int((alerta & (y == 0)).sum())
        peso = t / (1 - t)
        linhas.append({"limiar": round(float(t), 2),
                       "bl_modelo": vp / n - fp / n * peso,
                       "bl_todos": prev - (1 - prev) * peso,
                       "bl_nenhum": 0.0,
                       "alertas_por_100": 100 * alerta.mean()})
    return pd.DataFrame(linhas)
```
4. Rode para o **Teste A** e para **2020–2022**; grave `outputs/final/curva_decisao.csv` (com a coluna `janela`).
5. Figura: três linhas por janela (modelo, todos, nenhum), eixo x de 2% a 40%; marque o limiar 0,1178.
6. **Leitura para o relatório:** "o modelo tem benefício líquido maior que alertar todos entre *t* = ⟨a⟩ e ⟨b⟩; no limiar escolhido, o benefício equivale a encontrar ⟨x⟩ óbitos a mais por 100 internações sem aumentar os alarmes falsos, em relação a alertar todos". Em 2020–2022, discuta que a prevalência maior desloca a curva de "alertar todos".
7. **Opcional:** intervalo por bootstrap de grupos no Teste A (100 réplicas bastam).

### ④ Pronto quando

- existe: `notebooks/C/C_17_curva_decisao.ipynb` | O notebook da curva de decisão existe.
- contem: `notebooks/C/C_17_curva_decisao.ipynb` :: `bl_modelo` | O notebook calcula o benefício líquido do modelo.
- notebook-executado: `notebooks/C/C_17_curva_decisao.ipynb` | O notebook rodou sem erro sobre as previsões gravadas do teste.
- manual: | O relatório traz a figura da curva de decisão e a faixa de limiares em que o modelo é útil.

---

## #177 · Comparador "só idade e sexo" no Teste A, com bootstrap pareado (quanto as variáveis clínicas acrescentam fora da validação)

- prioridade: P3
- situação: aberta
- estratégia: explorar
- marco: M5
- data ideal: 04/11
- responsável: a definir (0,5 h)
- pessoas: Equipe
- fonte: Parecer crítico de 04/11 (recomendação 4.2); #161 item 3 (referência só idade e sexo no C_14, só na validação); src/evaluation/metrics.py::bootstrap_grupo já faz comparação pareada
- depende de: #148
- tags: Avaliação, Teste, Notebook
- pilar: Valor científico-acadêmico
- carga: 0.5
- novo: sim
- professores: sim
- arquivos: notebooks/C/C_16_validacao_final.ipynb, docs/decisoes.md

### ① Para entender

Só idade e sexo já dão ROC-AUC 0,80 na validação. A pergunta natural da banca: "quanto as 28 variáveis clínicas acrescentam **no teste**?". O #161 põe a linha "só idade e sexo" no C_14, mas só na validação.

`bootstrap_grupo(y, prob_a, grupos, metrica="ap", prob_b=prob_b)` já faz o **bootstrap pareado**: sorteia os mesmos grupos para os dois modelos e devolve a diferença A − B, com intervalo de 95% e p bilateral.

### ② Problema

Sem o comparador no teste, o ganho clínico só é mostrado na mesma validação que escolheu o modelo.

### ③ O que fazer

**Tempo:** ≈ 30 min · **Antes do G9**, testado no modo ensaio. Exige registro **antes** da abertura.

1. **Registre na §29.38, antes do G9:** "Comparação descritiva, sem escolha: logística com idade e sexo (C=1, sem peso), treinada no `train_ref`, calibrada em `val_cal` com sigmoid, avaliada no Teste A; diferença de PR-AUC e ROC-AUC pelo bootstrap pareado por grupo (1.000 réplicas)."
2. No C_16, depois de treinar e calibrar o finalista:
```python
from src.models.logistic import build_logistic_pipeline
from src.models.pipeline import build_preprocessor
from src.models.calibration import calibrar
pre_ref = build_preprocessor(numericas=["idade_anos"], categoricas=["sexo_categoria"])
ref = build_logistic_pipeline(C=1.0, penalty="l2", class_weight={}, preprocessor=pre_ref)
ref.fit(X_treino[["idade_anos", "sexo_categoria"]], y_treino)
ref_cal = calibrar(ref, X_val_cal[["idade_anos", "sexo_categoria"]], y_val_cal, method="sigmoid")
```
3. Depois de prever o Teste A com os dois (mesmas fichas):
```python
from src.evaluation.metrics import bootstrap_grupo
dif_ap = bootstrap_grupo(y_a, p_final_a, grupos_a, metrica="ap", prob_b=p_ref_a, n=1000)
dif_auc = bootstrap_grupo(y_a, p_final_a, grupos_a, metrica="auc", prob_b=p_ref_a, n=1000)
```
4. Grave `C6_..._comparador_idade_sexo.csv` com as duas diferenças e intervalos.
5. **Leitura:** "no Teste A, as variáveis clínicas acrescentam ⟨x⟩ de PR-AUC (IC 95% ⟨a⟩ a ⟨b⟩) ao modelo só com idade e sexo".

### ④ Pronto quando

- contem: `notebooks/C/C_16_validacao_final.ipynb` :: `prob_b=` | O C_16 compara o finalista com a referência por bootstrap pareado.
- contem: `docs/decisoes.md` :: `idade e sexo` | A comparação foi registrada antes da abertura do teste.

---

## #178 · Mapa TRIPOD+AI no relatório (padrão de relato de modelos preditivos em saúde)

- prioridade: P3
- situação: aberta
- estratégia: documentar
- marco: M7
- data ideal: 05/11
- responsável: a definir (0,33 h)
- pessoas: Equipe
- fonte: Parecer crítico de 04/11 (recomendação 4.6); Collins et al., BMJ 2024 (TRIPOD+AI)
- depende de: #133
- tags: Relatório, Metodologia
- pilar: Valor científico-acadêmico + Documentação
- carga: 0.33
- novo: sim
- professores: sim
- arquivos: docs/tripod_ai_mapa.md

### ① Para entender

O **TRIPOD+AI** (2024) é a lista de itens que um artigo sobre modelo de predição em saúde deve relatar: fonte dos dados, participantes, desfecho, preditores, tamanho da amostra, dados ausentes, análise, desempenho, calibração, equidade, limitações, disponibilidade do código. Mapear o relatório nessa lista mostra rigor e evita esquecer itens que a banca de saúde pública conhece.

### ② Problema

O relatório (#133) não tem uma checagem formal de completude.

### ③ O que fazer

**Tempo:** ≈ 20 min.

1. Crie `docs/tripod_ai_mapa.md` com uma tabela: item · onde está no relatório · onde está no repositório.
2. Itens principais e onde o projeto já responde:

| Item | Onde |
|---|---|
| Fonte de dados e período | Introdução, `data/manifest_dados-v2.yaml` |
| Elegibilidade (7 regras) | Métodos, `configs/final_cohort_v1.yaml`, waterfall |
| Desfecho e momento | Métodos, §9 e §3 do `decisoes.md` |
| Preditores e disponibilidade na admissão | Métodos, `feature_contract_v1.json`, §29.34 |
| Dados ausentes (categoria AUSENTE) | Métodos, §20 |
| Divisão dos dados (grupo, hash, 70/15/15, pandemia no teste) | Métodos, §29.33, manifesto da partição |
| Modelos, hiperparâmetros, regra de escolha | Métodos, §29.35, §29.37 |
| Calibração e limiar | Métodos, §29.36 |
| Desempenho com IC (Teste A) e calibração por janela | Resultados, C_16 |
| Equidade (região, raça/cor, faixa etária) | Resultados, #55 |
| Limitações | Discussão |
| Código e reprodutibilidade | README, `requirements-lock.txt` |

3. Itens não atendidos (por exemplo, validação externa prospectiva): diga explicitamente "não se aplica a este estudo acadêmico" ou "limitação".
4. Cite no relatório: "O relato segue o TRIPOD+AI (Collins et al., 2024); o mapa está em `docs/tripod_ai_mapa.md`."

### ④ Pronto quando

- existe: `docs/tripod_ai_mapa.md` | O mapa TRIPOD+AI existe no repositório.
- contem: `docs/tripod_ai_mapa.md` :: `Calibração` | O mapa cobre a calibração.
- manual: | O relatório cita o TRIPOD+AI e o mapa.

---

## #179 · Evidências prometidas na §29.23: atraso notificação–internação e incluídos × excluídos por desfecho

- prioridade: P3
- situação: aberta
- estratégia: explorar
- marco: M6
- data ideal: 04/11
- responsável: a definir (0,6 h)
- pessoas: Equipe
- fonte: §29.23 do decisoes.md (tools/ancora_e_excluidos.py prometido e inexistente); parecer crítico de 04/11 (recomendação 4.4)
- depende de: —
- tags: Exploração, Viés de seleção, Vazamento
- pilar: Valor científico-acadêmico
- carga: 0.6
- novo: sim
- professores: sim
- arquivos: tools/ancora_e_excluidos.py, outputs/final/atraso_notificacao.csv, outputs/final/excluidos_por_desfecho.csv, docs/decisoes.md

### ① Para entender

Duas perguntas que uma banca de saúde pública quase certamente faz:

1. **"Quando a ficha foi preenchida?"** A notificação pode ser feita dias depois da internação. Se o atraso for grande, campos como saturação podem ter sido preenchidos já com o paciente evoluindo. O atraso `dt_notific − dt_interna` mede isso.
2. **"Quem ficou de fora pode enviesar o resultado?"** A regra D_COORTE_003 excluiu **530.370** internações: 340.351 com evolução vazia, 103.570 com código 9 (ignorado) e 86.449 com código 3 (óbito por outra causa). Se essas pessoas forem mais velhas, ou concentradas em certos anos e regiões, a mortalidade estimada pode estar enviesada.

A §29.23 prometeu essas tabelas e o script `tools/ancora_e_excluidos.py`, que não existe.

### ② Problema

Sem esses números, a resposta às duas perguntas fica no campo da opinião.

### ③ O que fazer

**Tempo:** ≈ 35 min · Usa só a base bruta e a coorte; **não toca no teste**. Começa por um relatório numa cópia, como combinado.

1. Crie `tools/ancora_e_excluidos.py`, que lê do Parquet bruto só `dt_notific, dt_interna, dt_sin_pri, evolucao, hospital, nu_idade_n, tp_idade, sg_uf` (com `storage.read_srag(columns=..., compactar=True)`).
2. **Tabela 1 — atraso** (só fichas da coorte): `dias = dt_notific − dt_interna`, por ano de internação: mediana, intervalo interquartil, % com atraso > 7 dias, % com notificação antes da internação. Grave `outputs/final/atraso_notificacao.csv`.
3. **Tabela 2 — excluídos por desfecho** (internados com `hospital = 1`, data válida e 2019–2026): três grupos (incluídos, desfecho ausente ou 9, óbito por outra causa) × ano × faixa etária × região, com contagem e idade mediana. Grave `outputs/final/excluidos_por_desfecho.csv`.
4. Use `idade_em_anos`, `regiao_residencia` e `parse_srag_date` do `src` (as datas do episódio estão em `AAAA-MM-DD`).
5. Escreva na §29.23 as frases de leitura com os números. Exemplo: "a mediana do atraso é ⟨x⟩ dias; ⟨y⟩% das fichas foram notificadas mais de 7 dias após a internação"; "a ausência de desfecho concentra-se em ⟨anos⟩ e ⟨faixas⟩".
6. Se o atraso for grande, cite-o na limitação da saturação. Se a ausência de desfecho for desigual, cite-a como possível viés de seleção.
7. A tabela 3 da §29.23 (`nosocomial`) não é possível: a coluna não está no dicionário. Registre isso como limitação.

### ④ Pronto quando

- existe: `tools/ancora_e_excluidos.py` | O script prometido na §29.23 existe.
- existe: `outputs/final/atraso_notificacao.csv` | A tabela do atraso entre notificação e internação foi gerada.
- existe: `outputs/final/excluidos_por_desfecho.csv` | A tabela dos excluídos por desfecho foi gerada.
- manual: | A §29.23 tem as frases de leitura com os números.

---

## #180 · Validação "quase prospectiva" em 2026, com o modelo congelado e sem reajuste

- prioridade: P3
- situação: aberta
- estratégia: explorar
- marco: Pós-entrega
- data ideal: 05/11
- responsável: a definir (0,5 h)
- pessoas: Equipe
- fonte: Parecer crítico de 04/11 (recomendação 4.9); temporal.exploracao_2026 no YAML (permitir_reajuste: false)
- depende de: #2, #160
- tags: Avaliação, Exploração, Teste
- pilar: Valor científico-acadêmico
- carga: 0.5
- novo: sim
- professores: não
- arquivos: configs/supervised.yaml, docs/decisoes.md

### ① Para entender

2026 é o dado mais "futuro" disponível: 173.945 fichas até 28/09/2026, nunca usadas em nada. O YAML já prevê `exploracao_2026` com `somente_apos_fluxo_principal: true` e `permitir_reajuste: false`. Avaliar o modelo congelado nesse bloco simula um uso prospectivo.

### ② Problema

2026 é parcial e o desfecho dos meses finais pode não estar maduro (fichas abertas). A mortalidade observada (5,5%) pode estar subestimada. Por isso a leitura exige o #160 e uma ressalva explícita.

### ③ O que fazer

**Tempo:** ≈ 30 min · **Só depois do C_16.**

1. Registre na §29.38 (ou §29.39), **antes de rodar**: "avaliação descritiva de 2026 com o modelo congelado; meses de ⟨x⟩ a ⟨y⟩ excluídos por imaturidade do desfecho (#160)".
2. No YAML: `temporal.exploracao_2026.ativa: true` (o carregador exige isso para ler o bloco `exploracao`).
3. Carregue com `load_supervised_artifact(root, partitions=("exploracao",))`. **Atenção:** o artefato atual **não grava** o bloco `exploracao` (ele é filtrado em `gerar_artefato_supervisionado`). Será preciso reconstruir só 2026 a partir da coorte com `montar_features`, sem regerar o artefato, ou gravar à parte.
4. Calcule as mesmas métricas do Teste A, mais O/E por mês.
5. Leitura: comparação descritiva com o Teste A; nada é reajustado.

### ④ Pronto quando

- contem: `docs/decisoes.md` :: `2026 com o modelo congelado` | A avaliação de 2026 foi registrada antes de rodar.
- manual: | As métricas de 2026 foram calculadas com o modelo congelado e a ressalva de maturidade.

---

## #181 · Equidade: "ignorado" e "AUSENTE" como grupos explícitos em raça/cor e zona, com nota de leitura

- prioridade: P3
- situação: aberta
- estratégia: desenvolver
- marco: M5
- data ideal: 05/11
- responsável: a definir (0,17 h)
- pessoas: Equipe
- fonte: Parecer crítico de 04/11 (recomendação 4.8); src/evaluation/errors.py descarta grupo nulo (dropna)
- depende de: #55, #174
- tags: Equidade, Relatório
- pilar: Valor científico-acadêmico
- carga: 0.17
- novo: sim
- professores: sim
- arquivos: notebooks/C/C_16_validacao_final.ipynb

### ① Para entender

Em raça/cor, "ignorado" (código 9) é frequente. Se o grupo "ignorado" sumir das tabelas, ou se misturar a outro, as métricas por raça/cor podem sugerir equidade onde só há falta de registro. `metricas_por_grupo` descarta valores nulos (`dropna`); o C_16 já converte para "AUSENTE".

### ② Problema

Uma tabela de equidade sem os grupos "ignorado" e "AUSENTE" esconde parte da população, justamente a de registro mais pobre.

### ③ O que fazer

**Tempo:** ≈ 10 min.

1. Confirme no C_16 que `cs_raca` e `cs_zona` passam por `fillna("AUSENTE")` antes de `metricas_por_grupo`.
2. Mapeie os códigos para nomes legíveis (1 branca, 2 preta, 3 amarela, 4 parda, 5 indígena, 9 ignorado; zona 1 urbana, 2 rural, 3 periurbana, 9 ignorado).
3. Nota no relatório: "diferenças entre grupos podem refletir acesso, capacidade dos hospitais e qualidade do registro; 'ignorado' e 'ausente' são mostrados à parte".

### ④ Pronto quando

- contem: `notebooks/C/C_16_validacao_final.ipynb` :: `ignorado` | As tabelas por raça/cor e zona mostram o grupo ignorado com nome legível.
- manual: | O relatório traz a nota de leitura sobre registro e acesso.

---

## #182 · Estratificação por região: descobrir qual estrato derrubou a região e registrar

- prioridade: P3
- situação: aberta
- estratégia: documentar
- marco: M7
- data ideal: 05/11
- responsável: a definir (0,25 h)
- pessoas: Equipe
- fonte: manifesto_particao.json ("estratificacao": "ano × alvo (fallback)"); src/data/split.py::criar_particao_mestra
- depende de: —
- tags: Partição, Documentação
- pilar: Documentação
- carga: 0.25
- novo: sim
- professores: não
- arquivos: tools/diagnostico_estratos.py, docs/decisoes.md

### ① Para entender

`criar_particao_mestra` tenta estratificar por ano × alvo × região. Se **um** estrato tiver menos de 5 grupos, toda a partição cai para ano × alvo, e o manifesto registra "fallback" sem dizer qual estrato foi. O mais provável: algum estrato de região `AUSENTE` em 2019, com óbito.

### ② Problema

A banca pode perguntar por que a região, prevista no desenho, não entrou. Hoje a resposta é "algum estrato era pequeno", sem saber qual.

### ③ O que fazer

**Tempo:** ≈ 15 min · **Não muda a partição** (mudar obrigaria regerar tudo).

1. Script `tools/diagnostico_estratos.py`: lê `partitions_master.parquet` (só `group_id`, `ano_internacao`, `alvo_obito_srag`, `regiao_residencia`) dos anos compartilhados e conta grupos por estrato:
```python
cont = (df.drop_duplicates("group_id")
          .groupby(["ano_internacao", "alvo_obito_srag", "regiao_residencia"], observed=True)
          .size().reset_index(name="grupos"))
print(cont[cont.grupos < 5])
```
2. Registre no `decisoes.md` (§21 ou §29.4): "estrato(s) ⟨…⟩ com ⟨n⟩ grupos; a estratificação caiu para ano × alvo; as prevalências dos blocos conferem (8,439%, 8,440%, 8,441%)".
3. Trabalho futuro: juntar `AUSENTE` à região mais frequente ou estratificar só nas regiões presentes.

### ④ Pronto quando

- existe: `tools/diagnostico_estratos.py` | O diagnóstico dos estratos existe.
- contem: `docs/decisoes.md` :: `ano × alvo (fallback)` | O decisoes.md explica a queda da estratificação por região.

---

## #183 · Robustez do src: fábrica com erro em chave desconhecida, datas com formato fixo e lista de proibidas completa

- prioridade: P3
- situação: aberta
- estratégia: desenvolver
- marco: Pós-entrega
- data ideal: 05/11
- responsável: a definir (0,5 h)
- pessoas: Equipe
- fonte: Revisão do src/ de 04/11 (itens B7, B9 e S6 dos relatórios)
- depende de: —
- tags: Código, Vazamento, Qualidade
- pilar: Eficiência + Valor científico-acadêmico
- carga: 0.5
- novo: sim
- professores: não
- arquivos: src/models/factory.py, src/data/cohort_audit.py, src/features/engineering.py, src/evaluation/leakage.py, configs/supervised.yaml, tests/test_model_pipelines.py, tests/test_leakage.py

### ① Para entender

Três pontos do `src/` funcionam hoje, mas protegem pouco contra erros futuros:

1. **Fábrica:** chave desconhecida em `models.<nome>` vira só um `RuntimeWarning` (o modelo treina sem o parâmetro). Valores `null` são descartados (por isso `class_weight: {}` em vez de `null`).
2. **Datas:** `parse_srag_date` aceita só `AAAA-MM-DD`; `montar_features` usa `pd.to_datetime` sem formato. As datas do episódio são 100% ISO (B_02), mas **todas as datas de vacina COVID estão em DD/MM/AAAA** e virariam vazio sem aviso.
3. **Proibidas:** faltam `classi_fin` (classificação final, definida depois dos exames), `criterio` e os campos de resultado laboratorial e de imagem. `DEFAULT_LEAKAGE_COLUMNS` cita `classificacao_final`, que não existe na base.

### ② Problema

Nenhum afeta o modelo atual, mas qualquer extensão (contexto com vacinação, novas variáveis) pode cair nessas armadilhas em silêncio.

### ③ O que fazer

**Tempo:** ≈ 30 min · **Depois da entrega** (mudar o `src` antes do C_16 exige rodar tudo de novo).

1. **Fábrica:** troque `warnings.warn(...)` por `raise ValueError(...)` quando houver chave ignorada; aceite `null` em `class_weight` tratando como "sem peso" (`{}`) explicitamente. Teste em `tests/test_model_pipelines.py`.
2. **Datas:** em `montar_features`, passe `format="%Y-%m-%d"` aos `pd.to_datetime`; no docstring de `parse_srag_date`: "datas de vacina COVID estão em DD/MM/AAAA; use converter_data_mista (B_02)".
3. **Proibidas:** acrescente ao YAML `classi_fin`, `criterio` e as colunas de exame (confira os nomes no dicionário: `pcr_resul`, `res_an`, `raiox_res`, `tomo_res` e similares); corrija `classificacao_final` para `classi_fin` em `DEFAULT_LEAKAGE_COLUMNS`.
4. Rode `python -m pytest -q`.

### ④ Pronto quando

- contem: `src/evaluation/leakage.py` :: `classi_fin` | A lista padrão de vazamento usa o nome real da classificação final.
- yaml: `configs/supervised.yaml` :: `features.proibidas` contem `classi_fin` | A classificação final está entre as proibidas.
- contem: `src/features/engineering.py` :: `format="%Y-%m-%d"` | As datas do episódio são convertidas com formato fixo.

---

## #184 · Limpeza técnica do src: teste fora do pacote, função duplicada, docstrings e nome da chave da recodificação

- prioridade: P3
- situação: aberta
- estratégia: desenvolver
- marco: Pós-entrega
- data ideal: 05/11
- responsável: a definir (0,33 h)
- pessoas: Equipe
- fonte: Revisão do src/ de 04/11 (itens S1, S3, S7, Y1 e B10)
- depende de: —
- tags: Código, Qualidade
- pilar: Eficiência
- carga: 0.33
- novo: sim
- professores: não
- arquivos: src/evaluation/calibration.py, tests/test_calibration.py, src/data/final_cohort_cli.py, src/utils/hashing.py, src/data/split.py, src/utils/config.py, src/features/engineering.py, src/models/pipeline.py

### ① Para entender

Itens pequenos que não afetam resultado, mas que um avaliador de código percebe.

### ② Problema

| Onde | Problema |
|---|---|
| `src/evaluation/calibration.py` | `test_calibracao_intercepto_inclinacao_e_ece_quantis` está dentro do pacote (não é coletada pelo `pytest`) |
| `final_cohort_cli.py` e `utils/hashing.py` | duas funções `sha256_file` |
| `src/data/split.py` | docstring "cinco blocos compartilhados" (são três) |
| `src/utils/config.py` | exemplo de `cfg` com `temporal.fracao` (chave antiga); `gate_aprovado` quebra se um gate não for dicionário |
| `src/features/engineering.py` | lê `recodificar_comorbidades_fator_risc`, o YAML tem `…_risco` (a chave nunca seria encontrada) |
| `src/models/pipeline.py` | `FEATURES` é lida do YAML na importação (mudou o YAML, reinicie o kernel); `FunctionTransformer(lambda …)` impede `pickle` comum |
| `.gitignore` | acentos corrompidos ("relatÃ³rios") |

### ③ O que fazer

**Tempo:** ≈ 20 min · **Depois da entrega.**

1. Mova o teste para `tests/test_calibration.py` (ele passa, conferido em 04/11).
2. `final_cohort_cli.py`: `from src.utils.hashing import sha256_file` e apague a cópia local.
3. Corrija as docstrings.
4. `gate_aprovado`: `g = _get_nested(...); return isinstance(g, dict) and g.get("status") == "aprovado"`.
5. Alinhe o nome da chave da recodificação (no código ou no YAML) e acrescente um teste que lê a chave.
6. Em `pipeline.py`, troque o `lambda` por uma função nomeada no módulo (`def _para_float32_fn(v): return v.astype(np.float32)`).
7. Regrave o `.gitignore` em UTF-8.

### ④ Pronto quando

- nao-define: `src/evaluation/calibration.py` :: `test_calibracao_intercepto_inclinacao_e_ece_quantis` | O teste saiu do pacote.
- nao-define: `src/data/final_cohort_cli.py` :: `sha256_file` | A função de hash existe num lugar só.
- nao-contem: `src/data/split.py` :: `cinco blocos compartilhados` | A docstring descreve os três blocos compartilhados.

---

## #185 · Piloto do boosting: L2 lida com "or 0.10" usa 0,10 em vez do 0,0 do YAML

- prioridade: P3
- situação: aberta
- estratégia: documentar
- marco: M6
- data ideal: 04/11
- responsável: Pessoa B (0,1 h)
- pessoas: B
- fonte: Revisão do B_05 de 04/11: float(cfg.get("l2_regularization") or 0.10) com YAML 0.0
- depende de: —
- tags: Notebook, Modelagem
- pilar: Documentação
- carga: 0.1
- novo: sim
- professores: não
- arquivos: notebooks/B/B_05_supervisionado_pilotos.ipynb

### ① Para entender

Na comparação das cinco famílias, o B_05 lê os parâmetros do boosting com `valor_do_yaml or padrão`. Em Python, `0.0 or 0.10` dá `0.10`, porque zero conta como "falso". O piloto usou regularização L2 de 0,10; o finalista, montado pela fábrica, usa 0,0.

### ② Problema

Diferença pequena (PR-AUC 0,354 no piloto com 300 mil fichas; 0,360 no finalista), mas é o tipo de detalhe que vira pergunta.

### ③ O que fazer

**Tempo:** ≈ 5 min.

**Opção A (sem reexecutar)**, no texto do §20 do B_05: "no piloto, a regularização L2 do boosting ficou em 0,10 (valor padrão), e não no 0,0 do YAML; o finalista usa 0,0".

**Opção B (se a execução limpa rodar o B_05)**, troque no código:
```python
def _ou(v, padrao): return padrao if v is None else v
l2 = float(_ou(boost_cfg.get("l2_regularization"), 0.10))
```
Faça o mesmo nos outros parâmetros lidos com `or`.

### ④ Pronto quando

- nao-contem: `notebooks/B/B_05_supervisionado_pilotos.ipynb` :: `get("l2_regularization") or` | O parâmetro não é mais lido com "or", que troca zero pelo padrão.

---

## #186 · Limitações e trabalhos futuros no relatório: agrupamento por hospital, nosocomial, recalibração periódica e corte por região

- prioridade: P3
- situação: aberta
- estratégia: documentar
- marco: M7
- data ideal: 05/11
- responsável: a definir (0,25 h)
- pessoas: Equipe
- fonte: Parecer crítico de 04/11 (fragilidades 3, 8 e 9); decisão da equipe de 03/11 sobre o corte por região
- depende de: #133
- tags: Relatório, Limitações
- pilar: Valor científico-acadêmico
- carga: 0.25
- novo: sim
- professores: sim
- arquivos: docs/decisoes.md

### ① Para entender

Algumas limitações não estão escritas em nenhum lugar, e outras estão espalhadas. Dizer antes da banca perguntar é a melhor defesa.

### ② Problema

Faltam no relatório:

1. **Agrupamento por hospital:** fichas de um mesmo hospital e município são correlacionadas (prática de registro, qualidade do cuidado). O bootstrap por grupo trata notificações repetidas, não hospitais. Os intervalos podem estar estreitos demais; a avaliação por UF e região mitiga em parte.
2. **Nosocomial:** a coluna não está no dicionário; não dá para separar SRAG adquirida no hospital dos intervalos negativos excluídos (D_COORTE_006).
3. **Hora da medição** da saturação e do desconforto (já citada, mas reforce com o atraso de notificação do #179).
4. **Trabalhos futuros:** recalibração periódica (por ano ou onda) e monitoramento do O/E; corte de decisão por região (sugestão do professor); modelo específico para crianças; validação prospectiva e análise de impacto (alertas que a equipe consegue atender).

### ③ O que fazer

**Tempo:** ≈ 15 min.

1. Escreva as quatro limitações e a lista de trabalhos futuros na seção de discussão do relatório (#133), com uma frase cada.
2. Registre um resumo no `decisoes.md` (§26 "Princípios inegociáveis" ou uma nova §29.40 "Limitações registradas").

### ④ Pronto quando

- contem: `docs/decisoes.md` :: `nosocomial` | A limitação sobre a origem hospitalar da infecção está registrada.
- manual: | O relatório traz as limitações e os trabalhos futuros.

---

## #187 · Resumo visual da curva de decisão e do comparador para os slides

- prioridade: P3
- situação: aberta
- estratégia: documentar
- marco: M8
- data ideal: 05/11
- responsável: Pessoa B (0,25 h)
- pessoas: B
- fonte: Recomendações de 04/11 (curva de decisão e comparador idade + sexo); #134 (apresentação)
- depende de: #176, #177, #134
- tags: Apresentação
- pilar: Valor científico-acadêmico + Documentação
- carga: 0.25
- novo: sim
- professores: sim
- arquivos: —

### ① Para entender

Se os cards #176 e #177 forem feitos, eles rendem os dois slides mais fortes para uma banca de saúde: "quanto a clínica acrescenta à idade" e "em que faixa de limiar o modelo é útil".

### ② Problema

Os resultados existiriam só em CSV e figura técnica, sem a frase que a banca entende em 10 segundos.

### ③ O que fazer

**Tempo:** ≈ 15 min · **Depois do teste.**

1. **Slide "O que a clínica acrescenta":** duas barras (só idade e sexo × modelo final) com PR-AUC no Teste A e o intervalo da diferença. Frase: "as informações clínicas da chegada acrescentam ⟨x⟩ de PR-AUC à idade e ao sexo".
2. **Slide "Quando o alerta vale a pena":** a curva de decisão com o limiar 0,118 marcado. Frase: "entre ⟨a⟩% e ⟨b⟩% de risco, usar o modelo é melhor que alertar todos ou ninguém".
3. Sem rótulos internos.

### ④ Pronto quando

- manual: | Os dois slides estão na apresentação, com as frases e os números do teste.
