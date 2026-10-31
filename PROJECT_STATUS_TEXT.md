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

Retrato de 31/10 sobre o commit `1e02321` (painel v6). A coorte definitiva (3.884.728 notificações), a partição-mestre em seis blocos e o artefato supervisionado existem; a exploração e a EDA estão feitas. **O que falta está na cadeia de modelagem:** os notebooks C ainda usam o vocabulário antigo (treino, validação e teste), o ajuste fino, a calibração, o limiar e o teste não rodaram, e a suíte rápida tem 4 falhas (#144). O plano foi refeito para a nova data: **trabalho entregue em 04/11/2026** e **apresentação em 05/11/2026**. Ordem: consertar a base (#144, #143) → cadeia C (#132, #148) e ablações (#54) → ponto de decisão (#140, 31/10 à noite) → G6, ajuste fino, peso de classe, calibração, limiar e G9 (#78, #1, #5, #79, #80, #81; 31/10 e 01/11) → **testes A e B uma única vez, na manhã de 02/11 (#2)** → relatório (#133), limpeza e unificação dos notebooks (#146) e pacote final (#126, #147).

### Entrega

04/11/2026 (trabalho) · 05/11/2026 (apresentação)

### Cronograma

- **31/10 sáb** — manhã: A: suíte e gates (#144), decisões (#73) · A, B, C: limpeza do repositório (#143) · tarde: C: C_11 a C_13 (#132) e ablações (#54) · B: agrupamento (#136), óbitos só no treino (#51), completude (#52) · A: dicionário (#70), bootstrap por grupo (#127) · **19h: ponto de decisão (#140)** · 20h: G6 (#78) · B: C_15 (#148)
- **01/11 dom** — C: **ajuste fino (#1)**, peso de classe (#5), calibração e G7 (#79), limiar global e regional e G8 (#80) · A: C_16 (#148), âncora (#56), Dados e Métodos (#133) · B: literatura (#112) · **21h: checklist e aprovação do G9 (#81)**
- **02/11 seg (feriado)** — **manhã: testes A e B uma única vez (#2)** · C: conferência das saídas (#119) e importância (#91) · A: subgrupos e falsos negativos (#55), Resultados (#133) · B: interpretação (#91) e região (#110)
- **03/11 ter** — #133 (Discussão e fechamento), redação (#71) · limpeza e unificação dos notebooks: A, B e C (#146); medições de tempo e memória (#145) · à noite: renomeação dos notebooks (#146)
- **04/11 qua** — **ENTREGA do trabalho** · manhã: execução limpa e README (#126), conferência dos números (#133) · tarde: congelar e empacotar (#147) · B: monta a apresentação (#134)
- **05/11 qui** — ensaio e **entrega da apresentação** (#134)

### Legenda das estratégias

<div class="legend"><span class="tag e-desenvolver">▶ Desenvolver</span>necessário <span class="tag e-explorar">🔍 Explorar</span>opcional com prazo <span class="tag e-documentar">✎ Decidir/documentar</span>contrato e decisão <span class="tag e-despriorizar">⏸ Despriorizado</span>não entra antes da entrega</div>

### Como ler

Cada card é uma pendência. Dentro dele: **① Para entender** (o tema em linguagem simples, com números do projeto), **② Problema** (o que está errado, com detalhes técnicos), **③ O que fazer** (passos), **④ Pronto quando** (critérios conferidos pelo verificador, com ✓, ✗, "indisponível nesta máquina" ou "confirmação manual"), **Ligações** (de quem depende e o que trava) e **Evidências** (commits que citam a pendência, commits que só mexeram nos arquivos dela e histórico). Os números dos itens são fixos e mantêm seus números históricos; o item #108 foi removido por impossibilidade material de recuperar a gravação. Cada card mostra a data ideal mesmo quando fechado.

### Pessoas

- **A** — suíte e gates (#144), decisões e configuração (#73, #70), bootstrap por grupo (#127), C_16 e abertura do teste (#148), checklist do G9 (#81), subgrupos (#55), relatório (#133) e pacote final (#147) (≈ 25 h de 31/10 a 04/11)
- **B** — agrupamento (#136), EDA no treino (#51, #52), C_15 (#148), literatura (#112), interpretação (#91, #110), seções do relatório e apresentação (#133, #134) (≈ 19 h)
- **C** — cadeia de modelagem (#132, #54, #1, #5, #79, #80), teste e conferência das saídas (#2, #119), importância (#91) e conferência técnica do relatório (≈ 22 h)
- **Equipe** — ponto de decisão (#140) e aprovações dos gates (#78, #81)

### Caminho crítico

#144 → #132 → #54 → #140 → #78 → #1 → #5 → #79 → #80 → #81 → #2 → #119 → #146 → #126 → #133 → #147

### Aviso da revisão

> [!atenção] Replanejamento de 31/10 (commit `1e02321`): entrega em 04/11
> Nenhum item do caminho crítico de 30/10 foi concluído (#132, #127, #1, #78 e #140 seguem abertos). O plano foi refeito com o ajuste fino no domingo e os testes na manhã de 02/11. Achados da leitura do código: (1) a suíte rápida tem **4 falhas** por uma função repetida em `verificacoes.py` e os gates G1, G2, G4 e G5 estão com `status: responsavel` no YAML (#144); (2) os notebooks C ainda usam `treino`/`validacao`/`teste` e `provisional`, e o C_16 carregaria de uma vez as 3.035.074 linhas do teste (`test_pandemic` tem 2.915.829), o que exige leitura em lotes (#145, #148); (3) o G6 precisa ser aprovado **antes** do ajuste (o C_13 só executa a busca com o G6 aprovado), e o `escolher_limiar` não aceita `recall_minimo` (#78, #80); (4) os notebooks estão sem saídas salvas e com marcas de processo: é preciso limpar, unificar e executar de novo (#146, #126); (5) `src/evaluation/cluster_profile.py` (#137) não está no Git. **Cortado do escopo da entrega:** #136 não bloqueia mais nada, #110 e #52 viraram parágrafos, ablações só da logística (exceto P e P − 3), e 2026, SP, UMAP e refatorações ficam para depois de 05/11. Cada card alterado tem, no início do **② Problema**, uma caixa "Replanejamento de 31/10" com o que mudou.

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

Painel local de acompanhamento do projeto. O conteúdo vem de `PROJECT_STATUS_TEXT.md` e o estado compartilhado de `PROJECT_STATUS.md`, ambos publicados pelo painel direto no GitHub. Planejamento alinhado à Base de Conhecimento v10 (27/10/2026), à revisão de 28/10 e ao replanejamento de 31/10 (commit `1e02321`). Painel v6.

### Ajuda · Como ler a carga estimada

- O campo **carga** de cada card é o esforço estimado em horas de trabalho focado (arredondado por card). O "O que fazer" detalha a divisão por pessoa quando há mais de uma.
- O total por pessoa (de 31/10 a 04/11) está no quadro de Pessoas: A ≈ 25 h, B ≈ 19 h e C ≈ 22 h. Tempo de máquina (ajuste fino, execução dos notebooks) não entra nas horas.
- Estimativas não são prazos rígidos. Se uma tarefa passar do dobro do previsto, comente no card para redistribuir.

### Ajuda · Datas e dependências

- Nenhum card tem data anterior à de um card do qual ele depende.
- Quando dois cards ligados caem no mesmo dia, o prazo indica o turno (manhã, tarde, noite) e o que vem antes termina primeiro.
- Cards absorvidos por outro (esforço 0) têm a mesma data do card que os contém.
- Se um card atrasar, os que dependem dele atrasam junto: avise no card e use o filtro "Só prontos para começar".

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
- data ideal: 31/10
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
- arquivos: tests/test_regras_pessoa_a.py, src/protocolo/verificacoes.py

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

- contem: `tests/test_regras_pessoa_a.py` :: `bloco_mestre` | tests/test_regras_pessoa_a.py tem os testes das invariantes do protocolo que leem a coluna bloco_mestre do artefato real (classe marcada como slow).
- contem: `tests/test_regras_pessoa_a.py` :: `test_pandemic` | Há teste conferindo que 2020–2022 só aparecem no bloco test_pandemic.
- contem: `tests/test_regras_pessoa_a.py` :: `sha256` | Há teste conferindo que o SHA-256 do arquivo do artefato é igual ao registrado no manifesto (src/utils/hashing.py).
- teste: `tests/test_regras_pessoa_a.py` | Os testes rápidos de tests/test_regras_pessoa_a.py passam (os de artefato real são slow e não entram aqui).
- manual: | A saída de `.\.venv\Scripts\python.exe -m pytest -m slow tests/test_regras_pessoa_a.py -q`, rodada com o artefato real, foi colada como comentário neste card, sem falhas e sem skips das cinco garantias (grupo em um único bloco, 2020–2022 só em test_pandemic, 2026 só em exploracao, prevalência por bloco a no máximo 0,5 p.p. da média, SHA-256 igual ao manifesto).

## #132 · Adaptar os notebooks C_11, C_12 e C_13 aos seis blocos (train_ref e val_tune)

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M2
- data ideal: 31/10
- responsável: Pessoa C (dona; revisão cruzada sem edição concorrente)
- pessoas: C
- fonte: Revisão de 24/10: notebooks C_11–C_16 na referência (commit baee782)
- depende de: #131, #142, #144
- tags: Código, Notebook, Partição, Modelagem, Vazamento
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 3
- novo: sim
- professores: não
- arquivos: notebooks/C/C_11_pipeline_supervisionado.ipynb, notebooks/C/C_12_baseline_logistica.ipynb, notebooks/C/C_13_boosting.ipynb, src/utils/hashing.py

### ① Para entender

A cadeia C foi escrita para a divisão antiga: treino, validação (dividida ao meio dentro do C_15) e teste. Na partição-mestre, cada papel tem bloco próprio:

| Bloco | Papel | Notebook |
|---|---|---|
| `train_ref` | ajustar modelos e pré-processamento | C_11 a C_15 |
| `val_tune` | escolher features (ablações), família e hiperparâmetros | C_12, C_13 |
| `val_cal` | ajustar o calibrador e escolher o limiar | C_15 |
| `val_meas` | medir uma vez, antes do teste, sem decidir nada | C_15 (fim) |
| `test_ref` / `test_pandemic` | Testes A e B, depois do G9 | C_16 |

### ② Problema

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: o card cobre agora **só C_11, C_12 e C_13** (Pessoa C). C_15 e C_16 passaram para o #148 (Pessoa B e Pessoa A), em paralelo. Todo notebook sai deste card **já limpo** (sem marcas de processo, ver #146), para não ser editado de novo. Achados da leitura do código em 31/10: o C_11 lê `manifest["partition_counts"]["teste"]`, chave que não existe no esquema de blocos (dá `KeyError`); o C_11 e o C_12 usam `EXPECTED_KIND = "provisional"` por padrão; o C_13 só faz a busca se o G6 estiver aprovado (por isso o G6 vem **antes** do ajuste, ver #78); a célula 6 do C_13 constrói os modelos de referência duas vezes.

Os notebooks C ainda usam o vocabulário `treino`/`validacao`/`teste` (12 ocorrências de cada na referência de 24/10). O C_15 divide a validação em duas metades por conta própria, e o C_16 escolhe manifesto pela data do arquivo. Rodar a cadeia assim na coorte definitiva quebraria o protocolo das duas janelas.

### ③ O que fazer

> [!decisão] Replanejamento de 31/10
> Vocabulário novo (`train_ref`, `val_tune`) só nos três notebooks do treino. Resultados com **nomes fixos** em `outputs/final/`, sem carimbo de data (os notebooks seguintes leem pelo nome, nunca pela data do arquivo; isso fecha o #27).

**Dono:** Pessoa C · **Prazo:** 31/10 (sábado), 10h30 às 15h · **Esforço estimado:** ≈ 3 h (inclui a execução dos três notebooks) · **Revisão:** Pessoa A (10 min, só o diff) · **Começa quando:** #131, #142 e #144

#### Padrão de leitura (vale para os três notebooks)
```python
EXPECTED_KIND = "final"
df, manifest = load_supervised_artifact(ROOT_DIR, expected_kind=EXPECTED_KIND, partitions=("train_ref", "val_tune"))
PARTICAO, ALVO = manifest["partition_column"], manifest["target_column"]
FEATURES = list(manifest["feature_columns"])
assert set(FEATURES) == set(C.features_finais()), "manifesto e YAML com listas de variáveis diferentes"
treino = df.loc[df[PARTICAO] == "train_ref"]
validacao = df.loc[df[PARTICAO] == "val_tune"]
```
Não importe `split_partitions` (ela junta os três blocos de validação num só). O `assert` fecha o #15: o pré-processador usa as listas do manifesto (`numeric_columns`, `categorical_columns`) e o YAML precisa concordar.

#### C_11 (pipeline)
1. Troque a célula de leitura pelo padrão acima. Troque `N_TESTE = int(manifest["partition_counts"]["teste"])` por `N_TESTE = int(sum(manifest["partition_counts"].get(b, 0) for b in ("test_ref", "test_pandemic")))`; o teste continua fechado (apenas informado).
2. `X_train`/`y_train` de `treino`, `X_val`/`y_val` de `validacao` com `filtrar_rotulos_validos`; `check_leakage` nos dois.
3. Mantenha `Monitor` e as asserções de saída esparsa `float32`. A saída é `outputs/C2/preprocessor_ajustado.joblib` (mantenha). A variável `pipeline_path` (`preprocessor.joblib`, sem ajuste) só aparece na mensagem impressa: remova essa variável e a linha do `print` (é a sobra do #43).

#### C_12 (baseline e logística)
4. Mesmo padrão de leitura. Treine `DummyClassifier` (estratégia `prior`) e a logística (`build_finalista("logistic", C=1.0)`) em `train_ref`; meça em `val_tune`.
5. Mostre **ao lado** o Brier do modelo nulo (`brier(y_val, np.full(len(y_val), y_train.mean()))`): sem esse número, o Brier da logística não tem referência.
6. Grave `outputs/final/baseline_logistica_val_tune.csv` (modelo, PR-AUC, PR-AUC ÷ prevalência, ROC-AUC, Brier, prevalência, n) e as previsões em `outputs/final/predicoes_val_tune_c12.parquet` (`id_registro`, `y`, `prob`). Esperado: PR-AUC da logística ≈ 0,30 e ROC-AUC ≈ 0,85 (valores do piloto definitivo); se fugir muito, pare e comente no card.

#### C_13 (boosting e busca)
7. Mesmo padrão de leitura. Remova a duplicação da célula 6: fique só com `build_finalista("logistic", C=1.0)` e `build_finalista("boosting", learning_rate=0.05, max_iter=500)`.
8. A busca (`_busca_limitada`) continua protegida por `G6_finalistas_tuning == aprovado` (checagem de `C.cfg("gates", "G6_finalistas_tuning", "status")`); com G6 pendente o notebook só mostra os modelos de referência. O que a busca testa está definido no #1.
9. Grave `outputs/final/tuning_val_tune.csv` (uma linha por configuração: `familia`, hiperparâmetros, PR-AUC, ROC-AUC, Brier, duração do ajuste em segundos) e o bloco de YAML proposto em `outputs/final/proposta_yaml_ajuste.txt`. **Não** escreva no YAML: quem aplica é a Pessoa C, à mão, no #1.

#### Identificador da execução (necessário para o C_15 e o C_16)
10. Em `src/utils/hashing.py`, acrescente `identificador_execucao(**campos) -> str`: `hashlib.sha256(json.dumps(campos, sort_keys=True, default=str).encode()).hexdigest()[:12]`. Teste em `tests/test_reproducibility.py`: mesma entrada, mesma saída; uma chave diferente, saída diferente. O C_13 imprime `run_id_finalista = identificador_execucao(dataset_sha256=manifest["dataset_sha256"], finalista=..., parametros=..., seed=C.SEED)`; esse valor vai para o YAML no #1 e o C_16 o recalcula para conferir (nunca escolhe arquivo pela data).

#### Fechamento
11. Procure nos três notebooks por `"validacao"`, `"teste"`, `provisional`, `HONEST_CALIB_SPLIT`, `st_mtime` e `split_partitions`: o resultado deve ser vazio (as palavras podem aparecer só em texto Markdown que explica o desenho).
12. Execute C_11, C_12 e C_13 com `.\.venv\Scripts\python.exe tools/medir_notebook.py notebooks/C/C_12_baseline_logistica.ipynb` (e os outros dois, nesta ordem). Anote tempo e pico no #145. O C_13 roda sem busca (G6 ainda pendente): só serve de ensaio.
13. Rode `.\.venv\Scripts\python.exe -m pytest -m "not slow" -q` e commit: `feat: notebooks C_11, C_12 e C_13 nos seis blocos [done:#132] [done:#15] [done:#27]`.
14. Avise no #54 e no #148 que a cadeia C está pronta.

### ④ Pronto quando

- contem: `notebooks/C/C_11_pipeline_supervisionado.ipynb` :: `train_ref` | O C_11 lê o bloco train_ref pelo módulo de leitura e não usa mais o vocabulário antigo treino/validacao/teste.
- contem: `notebooks/C/C_12_baseline_logistica.ipynb` :: `val_tune` | O C_12 treina em train_ref e mede em val_tune.
- contem: `notebooks/C/C_13_boosting.ipynb` :: `val_tune` | O C_13 faz a busca de hiperparâmetros em train_ref e mede em val_tune.
- nao-contem: `notebooks/C/C_11_pipeline_supervisionado.ipynb` :: `partition_counts"]["teste"]` | O C_11 não lê mais a chave `teste`, que não existe no esquema de blocos.
- contem: `notebooks/C/C_11_pipeline_supervisionado.ipynb` :: `numeric_columns` | O C_11 monta o pré-processador com as listas do manifesto (#15).
- define: `src/utils/hashing.py` :: `identificador_execucao` | A função identificador_execucao existe em src/utils/hashing.py (#27).
- notebook-executado: `notebooks/C/C_12_baseline_logistica.ipynb` | O C_12 foi executado do início ao fim na coorte definitiva e salvo com as saídas, sem erro gravado.
- notebook-executado: `notebooks/C/C_13_boosting.ipynb` | O C_13 foi executado do início ao fim e salvo com as saídas, sem erro gravado.
- existe: `outputs/final/baseline_logistica_val_tune.csv` | A comparação do C_12 (com o Brier do modelo nulo) está em outputs/final/baseline_logistica_val_tune.csv.

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

## #140 · Fase E: ponto de decisão dos achados exploratórios (31/10, noite)

- prioridade: P1
- situação: aberta
- estratégia: documentar
- marco: M3
- data ideal: 31/10
- responsável: Pessoa A (conduz e registra) + Pessoa C + Pessoa B (por mensagem)
- pessoas: A, C, B
- fonte: Replanejamento de 26/10
- depende de: #141, #137, #50, #54, #127
- tags: Decisão, Metodologia, Gate
- pilar: Valor científico-acadêmico
- carga: 2
- novo: sim
- professores: não

### ① Para entender

A Fase E existe para que descobertas na base nova **possam mudar o plano**. Este card é o momento em que isso acontece: antes do ajuste fino (G6), a equipe olha todos os achados juntos e decide o que muda. Depois do G6, mudanças de variáveis ou de representação ficam muito caras; depois do G9, ficam proibidas.

### ② Problema

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: o ponto de decisão **não aconteceu em 30/10** e vai para a **noite de 31/10**, com só o que muda o plano. Deixam de ser pré-requisito: #136, #51, #52, #55 e #110 (viram texto do relatório). Duas decisões têm padrão fechado: (1) comorbidades **não** são recodificadas no modelo (flag continua `false`); (2) os três sintomas de 2019 só saem pelo critério objetivo do #54.

Sem um ponto de decisão explícito, os achados exploratórios viram só "texto de relatório" e não influenciam o modelo, que é justamente o risco que o replanejamento quer evitar.

### ③ O que fazer

> [!decisão] Replanejamento de 31/10
> 45 minutos, às 19h, com a tabela de ablações (#54) em mãos. **Padrão se não houver consenso: nada muda.** Quem não puder participar responde "de acordo" ou objeta em uma linha até as 21h.

**Dono:** Pessoa A (conduz) · **Prazo:** 31/10 (sábado), 19h às 20h · **Esforço estimado:** A ≈ 1 h · C ≈ 30 min · B ≈ 15 min (mensagem) · **Começa quando:** #54 e #127

#### Antes (até 18h45)
Pessoa C comenta no #54 as três linhas de resumo. Pessoa B comenta nos cards #136, #51 e #52 o que encontrou (opcional).

#### Roteiro de decisão (a Pessoa A preenche a tabela neste card)
| Pergunta | Opções | Regra e padrão |
|---|---|---|
| Os três sintomas de 2019 (`perd_olft`, `perd_pala`, `fadiga`) saem? | manter · retirar | Retirar **só** se a ROC-AUC de 2019 sobe ≥ 0,01 sem eles **e** o IC pareado exclui zero, ou se ≥ 80% da importância por permutação vem de 2019 (#54, passo 5). Padrão: **manter** e documentar. |
| Recodificar o branco das comorbidades quando `fator_risc` = não? | recodificar · manter | Padrão: **manter** (`recodificar_comorbidades_fator_risco: false`). A linha "P com comorbidades recodificadas" do #54 vai para o relatório como sensibilidade. Só mude se a PR-AUC do **boosting** subir ≥ 0,005 e a equipe aceitar regenerar o artefato (volta ao G1; custo ≈ 2 h). |
| Gravidade, contexto ou região entram no modelo principal? | só relatório · reabrir G1 | Padrão: **só relatório** (saturação e desconforto ficam fora por serem medidos depois da internação). |
| Algum bloco do #50/#54 mostra problema de dados que exija ação? | nada · investigar | Padrão: **nada**; registrar. |
| Os achados do não supervisionado (#136) sugerem variável derivada? | só relatório · nova ablação | Padrão: **só relatório**. |

#### Depois (até 21h)
1. A Pessoa A registra as decisões em `docs/decisoes.md` (§29.28), com data, motivo e a linha da tabela.
2. Se alguma decisão mudar variáveis: a Pessoa C atualiza `features.final` no YAML **antes** de começar o #78 e avisa; a Pessoa A atualiza `variaveis_finais.csv` (#70).
3. A Pessoa B confirma por mensagem ("de acordo" ou objeção em uma linha).

#### Pronto quando
A tabela estiver preenchida (decisão + motivo por linha), registrada no `decisoes.md`, e o YAML refletir as mudanças (se houver).

### ④ Pronto quando

- contem: `docs/decisoes.md` :: `ponto de decisão` | O docs/decisoes.md tem a entrada do ponto de decisão da Fase E (#140), com data e a decisão de cada linha da tabela (sintomas de 2019, comorbidades, gravidade/contexto/região, dados, não supervisionado).
- manual: | A tabela de decisão deste card está preenchida linha a linha (decisão + motivo), as três pessoas confirmaram por comentário ou mensagem e, se alguma decisão mudou variáveis, o supervised.yaml foi atualizado antes do #78.

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
- data ideal: 31/10
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
- carga: 0
- novo: não
- professores: não

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
- define: `src/protocolo/verificacoes.py` :: `DEFAULT_CONFIG` | O DEFAULT_CONFIG de src/protocolo/verificacoes.py continua existindo (o cenário quebrado sem_2019_2022 foi corrigido para sem_2020_2021, ou removido junto com os testes se o A_09 sair no #143).
- nao-contem: `src/protocolo/verificacoes.py` :: `sem_2019_2022` | O cenário com nome e lista contraditórios (sem_2019_2022, que mantém 2019 e 2022) não existe mais em verificacoes.py.
- teste: `tests/test_regras_pessoa_a.py` | Os testes de tests/test_regras_pessoa_a.py passam (hoje 3 falham com KeyError: 'sem_2020_2021').
- teste: `tests/test_split.py` | Os testes de partição passam com o TEMPORAL_CFG coerente com a decisão sobre 2019.

## #30 · Salvar a coorte definitiva com o nome errado a carregaria como provisória

- prioridade: P3
- situação: resolvida
- estratégia: resolvida
- marco: M0
- data ideal: 31/10
- responsável: Pessoa C (dona; revisão cruzada sem edição concorrente)
- pessoas: C
- fonte: src/data/cohort_source.py
- depende de: —
- tags: Código, Dados/Coorte
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 0
- novo: não
- professores: não

### ① Para entender

> [!ok] Decisão fechada em 18/10
> A coorte definitiva inicial será a seleção de features da coorte provisória. O treino principal usará exclusivamente 2019, 2023, 2024 e 2025. Haverá duas janelas de teste: (A) 2019, 2023, 2024 e 2025; (B) 2019 a 2025, incluindo 2020–2022. O ano de 2026 não participa do desenvolvimento nem dos testes principais e fica apenas como exploração opcional, depois de todo o restante concluído.

> [!decisão] Decisão de 18/10
> Ao declarar a provisória como definitiva (item 44), salvar uma cópia como `coorte_final.parquet` para que `cohort_source` a reconheça.

`cohort_source` reconhece como definitiva só `coorte_final.parquet`. Se alguém salvar a coorte definitiva como `coorte.parquet`, ela será tratada como provisória sem aviso.

### ② Problema

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: reaberto três vezes (28/10 e 30/10). No commit `1e02321`, o único cuidado que faltava está atendido: o `manifesto_supervisionado.json` grava `cohort_kind: final` e a origem (`source.sha256` = `87f28d39…`, 3.884.728 linhas). Falta só a Pessoa C **confirmar e concluir** com um comentário (10 min).

`cohort_source` trata `coorte.parquet` como coorte provisória. No B_06, esse mesmo nome era usado como coorte "oficial". Se a coorte definitiva for salva com esse nome, será carregada como provisória.

### ③ O que fazer

**Pessoa C, 31/10, 10 min:** confira (a) `src/data/cohort_source.py` reconhece só `coorte_final.parquet` como definitiva; (b) o manifesto do artefato tem `cohort_kind: final` e o SHA-256 da origem; (c) `.\.venv\Scripts\python.exe -m pytest tests/test_cohort_source.py -q` passa. Marque como concluído com um comentário curto.

### ④ Pronto quando

- contem: `src/data/cohort_source.py` :: `coorte_final.parquet` | O cohort_source reconhece a coorte definitiva pelo nome canônico coorte_final.parquet.
- teste: `tests/test_cohort_source.py::test_coorte_parquet_nao_e_mais_candidato` | O teste confirma que coorte.parquet não é mais candidato, então a definitiva nunca é carregada como provisória por causa do nome.

## #59 · Documentar 2026 como período parcial e exclusivamente exploratório

- prioridade: P3
- situação: aberta
- estratégia: documentar
- marco: M1
- data ideal: 31/10
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

## #73 · decisoes.md parado em 10/10

- prioridade: P2
- situação: aberta
- estratégia: documentar
- marco: M1
- data ideal: 31/10
- responsável: Pessoa A (dona; revisão cruzada sem edição concorrente)
- pessoas: A
- fonte: docs/decisoes.md
- depende de: #144
- tags: Documentação, Decisão
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1
- novo: não
- professores: não

### ① Para entender

Desde 10/10 foram decididas muitas coisas que não estão registradas: quarentena, lista curta, famílias encerradas, peso das classes, partição por hash, 2026 fora, resultados do C_15.

> [!exemplo] Exemplo
> Se a banca perguntar "por que hash?", a resposta precisa estar no registro de decisões, com data.

### ② Problema

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: sobra **uma hora** para fechar o card. A verificação de 30/10 mostra 8 de 10 critérios atendidos; faltam `status_decisoes.coorte_estrita` (continua `proposta` em `configs/decisoes.yaml`) e o resultado do `tests/test_config.py` (volta com o #144). As entradas de G6, G7, G8, G9 e do ponto de decisão entram no `decisoes.md` **dentro dos cards respectivos**, não aqui.

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que esta pendência está aberta
> A auditoria automática do painel (27/10, 14:40) marcou este item como resolvido com base em commits de 10 e 19/10, todos anteriores às revisões de 24 e 26/10 e sem relação com a entrega descrita aqui. Isso acontece por um defeito do painel: a cada auditoria, um commit antigo ainda não rejeitado reabre a sugestão (detalhes no #94).
> `docs/decisoes.md` continua com "Última atualização: 21/10" e §28 como última seção; nenhuma das 8 entradas pedidas foi escrita.
> **Divergência grave encontrada (28/10):** `configs/supervised.yaml` e `configs/decisoes.yaml` (versão 0.5) passaram a dizer que o desenvolvimento usa só 2023–2025 e que 2019 vai para `test_pandemic` junto com 2020–2022 (`periodo.desenvolvimento`, `temporal.blocos.*.anos`, `dev_years`, `pandemic_test_years` e a descrição do G2). Todo o resto do projeto continua com 2019 no desenvolvimento: `docs/decisoes.md` §5 e §28, a Base de Conhecimento v10, este painel, o teste `tests/test_split.py` (`TEMPORAL_CFG`), as saídas salvas do B_07 e o artefato atual (`manifesto_supervisionado.json`: teste = 3.035.074 linhas = `test_ref` + 2020–2022). A mudança não está registrada como decisão e o G2 continua com a data de aprovação de 18/10.
> Itens a acrescentar ao pacote do #73: (a) registrar a decisão sobre 2019 (manter no desenvolvimento ou mover para o Teste B) e alinhar `decisoes.md` §5/§28 com o YAML, ou desfazer a mudança no YAML; (b) `configs/decisoes.yaml` ainda tem `coorte_estrita`, `acoes_inconsistencias_datas`, `variaveis_condicionais` e `maturidade_evolucao` como `proposta`; (c) `decisoes.yaml` `intervalo_sintomas_internacao` (`manter_com_flag`, `exclusao_automatica: false`) e `supervised.yaml` `engenharia.intervalo_politica: sinalizar` contradizem o contrato da coorte, que exclui intervalos negativos e acima de 60 dias.

As decisões dizem "última atualização 10/10" e não registram o que foi decidido neste ciclo: quarentena dos 2 grupos, lista curta, famílias encerradas, uso de `class_weight` e aprovações de gates.

### ③ O que fazer

> [!decisão] Replanejamento de 31/10
> Fechar o que falta, sem recomeçar. As decisões novas são registradas por quem as toma, nos cards do #140, #78, #79, #80 e #81.

**Dono:** Pessoa A · **Prazo:** 31/10 (sábado), manhã (logo depois do #144) · **Esforço estimado:** ≈ 1 h · **Começa quando:** #144

1. `configs/decisoes.yaml`, bloco `status_decisoes`: troque `coorte_estrita` para `status: aprovada` e `maturidade_evolucao` para `status: aprovada`, `responsavel: time_do_projeto`, `data: '2026-10-22'`. Alinhe também as quatro que o `docs/decisoes.md` §1.1 já dá como fechadas (`ponto_de_previsao`, `alvo`, `evolucao_desconhecida`, `periodos`): `status: aprovada`. Depois, `.\.venv\Scripts\python.exe -m pytest tests/test_config.py tests/test_regras_pessoa_a.py -q`.
2. `docs/decisoes.md`: troque o nome inexistente `semana_sen` por `sin_semana` (é o que o código usa; fecha o critério do #13) e confira que a linha "Última atualização" tem a data de hoje.
3. Entradas pendentes de 24 a 30/10 (se faltar alguma, uma linha cada: data · decisão · motivo · onde está no código): contrato `final_cohort_v1`; G1 (31 variáveis); regra de grupo; orientação do professor; indicadores de ausência desligados; 2026 só exploração; quarentena de `nu_notific` repetido; lista curta de modelos. O que já está nas seções §29.1 a §29.26 **não** se repete.
4. Commit: `docs: fecha decisoes e status_decisoes [done:#73]`.

### ④ Pronto quando

- nao-contem: `docs/decisoes.md` :: `Última atualização: 21/10/2026` | O docs/decisoes.md foi atualizado depois de 21/10 (a linha de última atualização mudou).
- contem: `docs/decisoes.md` :: `final_cohort_v1` | O docs/decisoes.md tem a entrada do contrato final_cohort_v1 (7 regras; 4.666.910 → 3.884.728 notificações).
- contem: `docs/decisoes.md` :: `criar_group_id` | O docs/decisoes.md registra a regra de grupo (nu_notific, fichas repetidas no mesmo bloco, 4 linhas fora) citando criar_group_id.
- yaml: `configs/supervised.yaml` :: `models.decision_tree.ativa` = `false` | A árvore de decisão, família encerrada, está desligada no supervised.yaml.
- yaml: `configs/supervised.yaml` :: `models.random_forest.ativa` = `false` | A Random Forest, família encerrada, está desligada no supervised.yaml.
- yaml: `configs/supervised.yaml` :: `models.boosting.early_stopping` = `true` | O early stopping do boosting está ligado no YAML (com false, a fábrica anula o padrão e a busca fica lenta).
- yaml: `configs/supervised.yaml` :: `limiar.min_recall` = `0.8` | O YAML tem limiar.min_recall = 0,80, a regra de corte orientada pelo professor.
- yaml: `configs/decisoes.yaml` :: `status_decisoes.coorte_estrita` = `aprovada` | As decisões que estavam como "proposta" no decisoes.yaml (coorte_estrita e as outras três) passaram a aprovada.
- yaml: `configs/decisoes.yaml` :: `dataset_analitico.path` != `data/analytical/dataset_supervisionado.parquet` | A exportação da Pessoa A deixou de apontar para o mesmo arquivo do artefato oficial (fecha o #87).
- teste: `tests/test_config.py` | Os testes de configuração passam depois das mudanças nos YAMLs.

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
- responsável: Pessoa A · revisão: Pessoa C
- pessoas: A, C
- fonte: src/protocolo/verificacoes.py (a1_export_dataset, _analytical_path); notebooks A_03, A_04, A_14; configs/decisoes.yaml (dataset_analitico.path)
- depende de: #73, #144
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

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: o `dataset_analitico.path` já aponta para `dataset_provisorio_pessoa_a.parquet` (decisoes §29.26). O critério do teste só fica ✓ depois do #144, que repara `_analytical_path`. Marque como concluído com ele.

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que esta pendência está aberta
> A auditoria automática (27/10, 14:40) marcou "precisa revisão" por achados que não tratam deste item: a linha decorativa `=====` no cabeçalho de `src/protocolo/verificacoes.py` (lida como conflito de merge) e o `OneHotEncoder` denso do B_06, que roda numa amostra de 80 mil fichas e será substituído pelo #136 (detalhes no #94).
> O problema real continua: `configs/decisoes.yaml` `dataset_analitico.path` e o `DEFAULT_CONFIG` de `src/protocolo/verificacoes.py` ainda apontam para `data/analytical/dataset_supervisionado.parquet`, o mesmo arquivo do artefato oficial. Rodar A_03 ou A_04 apaga o artefato. Fecha no #73.

`a1_export_dataset` grava em `_analytical_path(cfg)`, que resolve para `C.ANALYTICAL_DIR / "dataset_supervisionado.parquet"` (nome definido em `configs/decisoes.yaml`, `dataset_analitico.path`). É o mesmo arquivo de `src/data/supervised_artifact.py` (`DATASET_NAME`). O A_14 registrou **FALHA**: "dataset analítico foi alterado depois da exportação". A ordem atual de execução evita o problema por acaso, não por desenho.

### ③ O que fazer

**Resolvido pelo #73 e pelo #144** (Pessoa A). O A_03 e o A_04 gravam em `data/analytical/dataset_provisorio_pessoa_a.parquet`, e o artefato oficial continua só com `gerar_artefato_supervisionado`. Confirme com a suíte verde (`tests/test_regras_pessoa_a.py`) e marque como concluído.

### ④ Pronto quando

- yaml: `configs/decisoes.yaml` :: `dataset_analitico.path` != `data/analytical/dataset_supervisionado.parquet` | O configs/decisoes.yaml aponta a exportação da Pessoa A para outro arquivo (por exemplo, populacao_analitica_pessoa_a.parquet), diferente do artefato oficial.
- nao-contem: `src/protocolo/verificacoes.py` :: `"dataset_supervisionado.parquet"` | O DEFAULT_CONFIG de src/protocolo/verificacoes.py também deixou de usar o nome do artefato oficial, então rodar A_03 ou A_04 não apaga mais o artefato.
- teste: `tests/test_regras_pessoa_a.py` | Os testes de tests/test_regras_pessoa_a.py passam (incluído pelo verificador em 28/10: esses testes importam src/protocolo/verificacoes.py, arquivo desta pendência, e 3 deles falham hoje pelo cenário renomeado do #102).

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
- teste: `tests/test_supervised_artifact.py::test_load_com_teste_sem_g9_falha` | O teste confirma que pedir o teste com o G9 pendente levanta erro.

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
- teste: `tests/test_supervised_artifact.py::test_holdout_partition_apos_g9` | O teste confirma que holdout_partition devolve o teste depois de o G9 ser aprovado.

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
- carga: 0
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
- data ideal: 31/10
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
- carga: 2
- novo: não
- professores: não

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
- data ideal: 31/10
- responsável: Pessoa A (dentro do #70)
- pessoas: A
- fonte: B/___provisorio_construcao_coorte_b; construção da coorte definitiva
- depende de: #70
- tags: Notebook, Dados/Coorte
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 0
- novo: não
- professores: não

### ① Para entender

O notebook `___provisorio_construcao_coorte_b` não foi reexecutado (0 de 14 células com saída), fixa a data final em 28/09/2026 e não gera `manifesto_coorte.json` nem `variaveis_finais.csv`, que o YAML espera.

### ② Problema

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: a construção da coorte provisória **não será reexecutada** (o notebook sai do pacote no #143). O que importa é a tabela `variaveis_finais.csv`, feita no #70; o `manifesto_coorte.json` da coorte definitiva já existe (`coorte_final.manifest.json`).

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

- prioridade: P4
- situação: aberta
- estratégia: documentar
- marco: M6
- data ideal: 01/11
- responsável: Pessoa A (dentro do #133)
- pessoas: A
- fonte: notebooks B_05 (1 de 42 células sem saída); B/___provisorio_construcao_coorte_b (0 de 14)
- depende de: —
- tags: Notebook, Dados/Coorte
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 0
- novo: não
- professores: não

### ① Para entender

O notebook que constrói a coorte provisória B não tem nenhuma célula executada salva, e o B_05 tem uma célula sem saída. Quem clonar o repositório não consegue ver como a coorte de 3,9 milhões de linhas foi feita, só o arquivo pronto (que não vai para o Git).

<div class="kpi">
<div><b>0 / 14</b>células executadas no construtor da coorte</div>
<div><b>41 / 42</b>células executadas no B_05</div>
</div>

### ② Problema

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: um parágrafo dentro do #133; o construtor da coorte provisória sai do pacote (#143).

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

## #127 · Função de comparação pareada com bootstrap por grupo

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M2
- data ideal: 31/10
- responsável: Pessoa A (dona; revisão cruzada sem edição concorrente: Pessoa C)
- pessoas: A
- fonte: src/evaluation/metrics.py (bootstrap_grupo); tests/test_metrics.py
- depende de: #23, #144
- tags: Metodologia, Código
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1
- novo: sim
- professores: não
- arquivos: src/evaluation/metrics.py, tests/test_metrics.py

### ① Para entender

Quando dois modelos são avaliados nas mesmas pessoas, a pergunta certa é "a diferença entre eles é real?", não "cada um tem qual nota?". O bootstrap pareado sorteia pessoas com reposição, recalcula as duas métricas e guarda a diferença; o intervalo dessas diferenças diz se o ganho é consistente.

> [!exemplo] Exemplo
> Duas balanças pesando os mesmos 80 mil pacotes: comparar pacote a pacote é muito mais preciso que comparar a média de cada balança.

### ② Problema

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: passa da Pessoa C para a **Pessoa A** (a Pessoa C fica com a cadeia de modelagem) e ganha um requisito de **desempenho**: o Teste B tem 2.915.829 linhas e o `ic_bootstrap` atual reordena o vetor inteiro a cada réplica. Absorve o #22 (padrões do bootstrap e do mínimo por grupo vêm do YAML).

Não existe função para isso no `src`. Reamostrar linhas (e não grupos) subestimaria a incerteza quando a mesma notificação tem mais de uma linha.

### ③ O que fazer

> [!decisão] Replanejamento de 31/10
> Uma função só, **rápida o bastante para 3 milhões de linhas**: ordenar as probabilidades **uma vez** e a cada réplica só recalcular pesos. Serve para três usos: IC de uma métrica, IC da diferença entre dois modelos e IC da diferença entre janelas.

**Dono:** Pessoa A · **Revisão:** Pessoa C (10 min) · **Prazo:** 31/10 (sábado), 13h às 14h30 · **Esforço estimado:** ≈ 1 h 30 · **Começa quando:** #23 e #144

#### Assinatura
`bootstrap_grupo(y, prob_a, grupos, metrica="auc", prob_b=None, n=None, seed=None) -> dict` em `src/evaluation/metrics.py`, com `metrica` em `{"auc", "ap", "brier"}` (ou uma função `f(y, p, w)` com pesos, para uso raro). Devolve `{"estimativa", "ic_inferior", "ic_superior", "n_validas"}` e, com `prob_b`, `{"estimativa_diferenca", "ic_inferior", "ic_superior", "p_bilateral"}` (A − B).

#### Como fazer rápido (o que muda em relação ao `ic_bootstrap`)
1. `grupos` vira códigos inteiros (`pd.factorize`). Cada réplica sorteia `G` grupos com reposição: `cont = np.bincount(rng.integers(0, G, G), minlength=G)` e o peso de cada linha é `cont[codigo_do_grupo]`. Assim a mesma ficha repetida (mesmo `group_id`) entra junta ou não entra.
2. **Ordene uma única vez**: `ordem = np.argsort(-prob, kind="stable")`; guarde `y`, `peso_base` e os **níveis distintos** de probabilidade (`np.unique(prob, return_inverse=True)`). Em cada réplica, some os pesos por nível com `np.bincount(nivel, weights=w * y)` (positivos) e `np.bincount(nivel, weights=w * (1 - y))` (negativos). Agrupar por nível trata empates corretamente (calibração isotônica gera muitos).
3. **AUC ponderada:** acumule negativos por nível em ordem crescente de probabilidade; AUC = Σ (positivos do nível × (negativos abaixo + metade dos negativos do próprio nível)) ÷ (P × N).
4. **AP ponderada:** percorra os níveis em ordem decrescente de probabilidade, com `tp` e `fp` acumulados; AP = Σ (Δrecall × precisão no nível), igual à definição do scikit-learn (`average_precision_score`).
5. **Brier:** média ponderada de `(y − p)²`.
6. `n` e `seed` vêm do YAML (`avaliacao.bootstrap.repeticoes` = 1.000 e `.seed` = 42) quando não informados. Para vetores com mais de 1 milhão de linhas, aceite `n` menor (300) e registre no resultado (`n_replicas`). Calcule os somatórios de positivos e negativos por nível **uma vez por réplica** e reaproveite para AUC e AP. Medido num protótipo com 3 milhões de linhas e probabilidades quase todas distintas: ≈ 0,6 s por réplica (AUC e AP juntas), ou seja, ≈ 3 min para 300 réplicas. Réplicas com uma classe só são descartadas e contadas em `n_validas`.
7. Com `prob_b`: use **o mesmo sorteio** de grupos para os dois modelos e devolva o IC percentil de `metrica(a) − metrica(b)`.

#### Testes (`tests/test_metrics.py`, rápidos)
8. Contra o scikit-learn: com 20 mil linhas inventadas e **pesos 1**, `auc` e `ap` ponderadas diferem de `roc_auc_score` e `average_precision_score` em menos de 1e-9, inclusive com probabilidades **repetidas** (arredonde para 2 casas).
9. A igual a B → diferença estimada 0 e o IC contém 0. Mesma `seed` → mesmo resultado.
10. Grupos repetidos: com 10 mil fichas em 5 mil grupos, o IC com `grupos` é **mais largo** que o IC tratando cada linha como grupo.
11. Desempenho: com 1 milhão de linhas e `n=50`, a chamada termina em menos de 60 s (marque `@pytest.mark.slow`).

#### Absorve o #22
12. Troque o padrão fixo de `ic_bootstrap` (`n_boot: int = 200`) por `n_boot: int | None = None` (lê o YAML) e o `min_n: int = 30` de `errors.py` por leitura de `avaliacao.min_n_grupo` (100). Os dois testes antigos continuam passando.
13. Commit: `feat: bootstrap por grupo rapido e padroes do YAML [done:#127] [done:#22]`.

### ④ Pronto quando

- define: `src/evaluation/metrics.py` :: `bootstrap_grupo` | A função bootstrap_grupo existe em src/evaluation/metrics.py: sorteia grupos com reposição, ordena as probabilidades uma vez e devolve o IC de uma métrica ou, com prob_b, o IC da diferença pareada.
- contem: `tests/test_metrics.py` :: `bootstrap_grupo` | Há testes de bootstrap_grupo (igualdade com o scikit-learn, A igual a B, mesma semente, grupos repetidos).
- teste: `tests/test_metrics.py` | Os testes de métricas passam.
- nao-contem: `src/evaluation/metrics.py` :: `n_boot: int = 200` | O padrão fixo de 200 repetições do bootstrap deixou de existir (#22).
- nao-contem: `src/evaluation/errors.py` :: `min_n: int = 30` | O mínimo de casos por grupo deixou de ser 30 fixo (#22).

## #15 · Pré-processador e manifesto podem usar listas de variáveis diferentes

- prioridade: P2
- situação: aberta
- estratégia: desenvolver
- marco: M2
- data ideal: 31/10
- responsável: Pessoa C (antes: Pessoa A)
- pessoas: C
- fonte: src/models/pipeline.py (FEATURES, build_preprocessor); notebooks C_11 a C_16
- depende de: #132
- tags: Código, Features
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 0
- novo: não
- professores: não

### ① Para entender

Do C_11 ao C_16, a tabela X é montada com as variáveis do **manifesto**, mas o pré-processador usa as listas do **YAML**. Hoje elas coincidem. Quando `features.final` for preenchida, podem divergir, e o pipeline falha ou treina com colunas erradas.

### ② Problema

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: resolvido dentro do #132 (padrão de leitura com `assert` do manifesto contra o YAML).

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

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: passa para a Pessoa A junto com o #127.

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
- responsável: Pessoa C (antes: Pessoa B)
- pessoas: C
- fonte: notebooks C_16; B_10_consolidacao_shortlist_transicao_coorte
- depende de: #132, #148
- tags: Código, Notebook
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 0
- novo: não
- professores: não

### ① Para entender

O C_16 e o B_10 pegam o manifesto com a data de modificação mais nova. Copiar a pasta ou sincronizar pelo OneDrive muda essas datas e pode fazer o notebook ler o manifesto errado.

### ② Problema

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: resolvido no #132 (nomes fixos) e no #148 (o C_16 confere `run_id_finalista`).

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
- responsável: Pessoa C (conferência no #148)
- pessoas: C
- fonte: notebooks C_13 e C_15
- depende de: #148
- tags: Metodologia, Calibração
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 0
- novo: não
- professores: não

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

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: o `HONEST_CALIB_SPLIT` sai do C_15 no #148; a frase de Métodos entra no #133.

A busca do C_13 usa a validação inteira. O C_15 divide a validação em duas metades e usa uma delas para medir o desempenho final antes do teste. Essa metade já influenciou a escolha dos hiperparâmetros, então a estimativa fica um pouco otimista.

### ③ O que fazer

**Resolvido por desenho; conferido no #148 (passo 1).** Com `val_tune` (escolhe), `val_cal` (calibra e escolhe o corte) e `val_meas` (só mede), nenhuma fatia escolhe e mede ao mesmo tempo. Falta confirmar que o `HONEST_CALIB_SPLIT` saiu do C_15 e escrever a frase de Métodos no #133 (Pessoa A).

### ④ Pronto quando

- nao-contem: `notebooks/C/C_15_calibracao_limiar.ipynb` :: `HONEST_CALIB_SPLIT` | A divisão da validação ao meio saiu do C_15: val_tune escolhe, val_cal calibra e escolhe o corte, val_meas só mede.
- manual: | O relatório (Métodos, #133) tem a frase explicando os três papéis da validação (val_tune, val_cal, val_meas).

## #119 · Executar o modelo congelado nas duas janelas de teste (E_02)

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M5
- data ideal: 02/11
- responsável: Pessoa C (conferência das saídas) + Pessoa B (revisão)
- pessoas: C, B
- fonte: Plano integrado v2, seções 3 e 4; notebooks/E/E_02
- depende de: #2, #127
- tags: Modelagem, Notebook
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1
- novo: sim
- professores: não

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

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: este card vira a **conferência das saídas do C_16** (os arquivos que o #148 manda gerar), logo depois do #2. A comparação logística × boosting com bootstrap pareado é feita em `val_meas` (antes do teste, 39.749 linhas); no teste só o finalista é avaliado.

As duas janelas têm prevalências e composição temporal diferentes. Comparar apenas PR-AUC agregada seria insuficiente. É necessário reportar prevalência, PR-AUC/prevalência, ROC-AUC, Brier e calibração em cada janela e por ano.

### ③ O que fazer

> [!decisão] Replanejamento de 31/10
> O C_16 (#148, #2) gera tudo em uma execução. Aqui se **confere** e se acrescenta, sem abrir o teste de novo, o que depende só das previsões salvas.

**Dono:** Pessoa C (conferência) · Pessoa B (revisão) · **Prazo:** 02/11 (segunda, feriado), tarde · **Esforço estimado:** C ≈ 1 h · B ≈ 15 min · **Começa quando:** #2

#### O que precisa existir (nomes fixos em `outputs/final/`)
| Arquivo | Conteúdo |
|---|---|
| `teste_a_metricas.csv` | Teste A (`test_ref`): n, óbitos, prevalência, PR-AUC, PR-AUC ÷ prevalência, ROC-AUC, Brier, Brier do nulo, intercepto e inclinação, ECE, sensibilidade, precisão, especificidade, F1 no corte congelado e no de sensibilidade 0,70, IC 95% |
| `teste_b_metricas.csv` | Teste B (`test_ref` + `test_pandemic`): as mesmas métricas |
| `pandemico_metricas.csv` | 2020–2022 isolado |
| `por_ano.csv` | cada ano, inclusive 2019 |
| `calibracao_*.csv`, `figuras/*.png` | curvas de calibração e figuras |
| `predicoes_teste.parquet` | `id_registro`, `group_id`, `particao`, `ano_internacao`, `regiao_residencia`, `sg_uf`, `faixa_etaria`, `sexo_categoria`, `y`, `prob_calibrada`, `classe` |
| `teste_por_regiao.csv` | sensibilidade e precisão por região, corte global e regional |
| `manifesto_teste.json` | SHA-256 do artefato, commit, hash do YAML, `run_id_finalista`, horário |

#### Passo a passo
1. Confira cada arquivo: número de linhas dos Testes A e B (119.245 e 3.035.074 no Teste B), prevalências (8,44% no A; 26,4% em 2020–2022), colunas e ausência de valores vazios em `prob_calibrada`.
2. **Logística × boosting com bootstrap pareado, em `val_meas`** (`outputs/final/predicoes_val_meas.parquet` do C_15 tem as duas probabilidades): `bootstrap_grupo(y, prob_boosting, grupos, metrica="ap", prob_b=prob_logistica)` e o mesmo para `auc` e `brier`; grave `outputs/final/comparacao_modelos_val_meas.csv`. É a evidência de que o finalista foi escolhido por diferença real.
3. **Leitura obrigatória** (vai para o relatório): a PR-AUC do Teste B pode ficar **maior** só porque 2020–2022 têm 26% de óbitos. Compare sempre PR-AUC ÷ prevalência e ROC-AUC. Escreva "robustez à mudança de período", nunca "efeito da pandemia".
4. Pessoa B revisa a legibilidade das tabelas (nomes de colunas, unidades, casas decimais) e anota qualquer coluna que precise de rótulo no relatório.
5. Comente no card o resumo: PR-AUC, PR-AUC ÷ prevalência, ROC-AUC, Brier e inclinação do Teste A e do Teste B (uma linha cada).

### ④ Pronto quando

- existe: `outputs/final/teste_a_metricas.csv` | As métricas do Teste A (test_ref) estão em outputs/final/teste_a_metricas.csv.
- existe: `outputs/final/teste_b_metricas.csv` | As métricas do Teste B (test_ref + test_pandemic) estão em outputs/final/teste_b_metricas.csv.
- existe: `outputs/final/pandemico_metricas.csv` | As métricas só de 2020–2022 estão em outputs/final/pandemico_metricas.csv.
- existe: `outputs/final/por_ano.csv` | As métricas por ano (inclusive 2019) estão em outputs/final/por_ano.csv.
- existe: `outputs/final/predicoes_teste.parquet` | As previsões do teste foram exportadas com id_registro, grupo, bloco, ano, região, UF, faixa, sexo, y, probabilidade calibrada e classe.
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
- responsável: Pessoa B
- pessoas: B
- fonte: B_06_eda_temporal_clustering
- depende de: #142
- tags: Metodologia, Vazamento, Notebook
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1
- novo: não
- professores: não

### ① Para entender

> [!decisão] Decisão de 18/10
> Com a partição-mestre, o B_06 pode refazer as tabelas de óbito só com `train_ref`.

As tabelas "mortalidade por variável" do B_06 foram feitas com a coorte inteira, antes de a partição existir. Isso inclui os 15% que viraram teste.

> [!atenção] Atenção
> É descritivo e não escolheu variáveis, então o risco é pequeno. Mas o princípio "não olhar o teste" foi violado e precisa ser declarado ou refeito só no treino.

### ② Problema

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: continua P1 (usar os casos de teste numa tabela é o tipo de coisa que a banca aponta na hora). Passa a ser **só a mudança de código** (0,5 h); a execução completa do B_06 acontece **uma vez**, junto com o #136, para não rodar o notebook mais pesado duas vezes.

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que esta pendência está aberta
> A auditoria automática (27/10, 14:40) marcou "precisa revisão" por achados que não tratam deste item: a linha decorativa `=====` no cabeçalho de `src/protocolo/verificacoes.py` (lida como conflito de merge) e o `OneHotEncoder` denso do B_06, que roda numa amostra de 80 mil fichas e será substituído pelo #136 (detalhes no #94).
> Confirmado na saída do B_06 executado em 27/10: "Origem da análise do desfecho: coorte_sem_particao · Registros utilizados: 3.884.728". As tabelas `eda_02_obito_*` ainda usam a coorte inteira, inclusive casos de teste. Depende do `partitions_master.parquet` do #142.

As tabelas de desfecho do B_06 (letalidade por variável) usaram a coorte inteira, incluindo os casos que depois foram para o teste. Isso viola o princípio de não olhar o teste antes da avaliação final.

### ③ O que fazer

> [!decisão] Replanejamento de 31/10
> Mudança pequena no B_06 e **uma** execução (a mesma do #136 e do #145). A mortalidade base cai de 21,8% (coorte inteira) para ≈ 8,4% (`train_ref`); anote qualquer variável que mude de direção.

**Dono:** Pessoa B · **Prazo:** 31/10 (sábado) · **Esforço estimado:** ≈ 30 min de edição + execução do B_06 · **Começa quando:** #142

1. No B_06, logo depois da leitura da coorte, leia `data/analytical/partitions_master.parquet` só com `id_registro` e `bloco_mestre` e junte por `id_registro` (inclua `id_registro` na lista de colunas lidas). Crie `coorte["particao"] = coorte["bloco_mestre"].map({"train_ref": "treino"})`; as demais ficam vazias. O notebook já filtra `particao == "treino"` quando a coluna existe.
2. Execute o B_06 com `.\.venv\Scripts\python.exe tools/medir_notebook.py notebooks/B/B_06_eda_temporal_clustering.ipynb` (cópia executada em `outputs/notebooks/`; a execução final com `--salvar-no-lugar` fica no #126). Confira na saída: `origem_analise_desfecho = particao_treino` e ≈ 556 mil fichas.
3. Compare as tabelas `eda_02_obito_*` com a versão da coorte inteira: as direções devem se manter. Escreva no card as variáveis que mudaram de direção (ou "nenhuma mudou").
4. Commit: `fix: tabelas de obito do B_06 so com train_ref [done:#51]`.

### ④ Pronto quando

- notebook-saida: `notebooks/B/B_06_eda_temporal_clustering.ipynb` :: `particao_treino` | As saídas salvas do B_06 mostram origem_analise_desfecho = particao_treino, ou seja, as tabelas de óbito × cura vieram só do train_ref.
- contem: `notebooks/B/B_06_eda_temporal_clustering.ipynb` :: `partitions_master.parquet` | O B_06 junta a partição-mestre (partitions_master.parquet) por id_registro antes das tabelas de desfecho.
- manual: | As variáveis que mudaram de direção entre a versão da coorte inteira e a do train_ref foram anotadas neste card (ou foi registrado que nenhuma mudou).

## #91 · Mostrar quais características pesam mais no risco (importância das variáveis)

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M5
- data ideal: 02/11
- responsável: Pessoa C (tabelas) + Pessoa B (interpretação)
- pessoas: C, B
- fonte: Projeto (pergunta de pesquisa); finalistas do C_13/C_15; relatório
- depende de: #5
- tags: Metodologia, Modelagem
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 2
- novo: não
- professores: não

### ① Para entender

> [!decisão] Decisão de 18/10
> Prioridade elevada: responde a segunda metade da pergunta de pesquisa e alimenta o UMAP e a redução de variáveis sugerida pelo professor.

A pergunta de pesquisa tem duas metades: **estimar** o risco (feito) e dizer **quais características ajudam** a estimá-lo (não feito). Não há nenhum gráfico ou tabela de importância de variáveis nos notebooks. Na reunião de 16/10, foi a pergunta mais elogiada.

<div class="bars">
<div class="br"><span class="y"><1 ano</span><div class="t"><div class="b " style="width:4.0%"></div></div><span class="v">1,8%</span></div>
<div class="br"><span class="y">1–4</span><div class="t"><div class="b " style="width:2.4%"></div></div><span class="v">1,1%</span></div>
<div class="br"><span class="y">20–39</span><div class="t"><div class="b " style="width:25.3%"></div></div><span class="v">11,4%</span></div>
<div class="br"><span class="y">40–59</span><div class="t"><div class="b or" style="width:46.9%"></div></div><span class="v">21,1%</span></div>
<div class="br"><span class="y">60–79</span><div class="t"><div class="b red" style="width:76.4%"></div></div><span class="v">34,4%</span></div>
<div class="br"><span class="y">80+</span><div class="t"><div class="b red" style="width:92.0%"></div></div><span class="v">41,4%</span></div>
</div>

Exemplo do que se quer mostrar de forma ajustada: a idade claramente pesa, mas quanto, comparando pessoas parecidas no resto?

| Técnica | Em uma frase |
|---|---|
| Razão de chances da logística | "Com diabetes, a chance é X vezes maior, comparando pessoas parecidas" |
| Importância por permutação | embaralha uma coluna e mede quanto o modelo piora |
| SHAP | quanto cada característica empurrou o risco de cada paciente |

### ② Problema

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: depende só do **finalista congelado** (#1 e #5), não do #78; a Pessoa C gera as tabelas na manhã de 02/11 e a Pessoa B interpreta à tarde. Absorve o #57 (associações "protetoras").

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que esta pendência está aberta
> A auditoria automática do painel (27/10, 14:40) marcou este item como resolvido com base em commits de 19 e 20/10 (`0eab341`, `00d7105`), todos anteriores às revisões de 24 e 26/10 e sem relação com a entrega descrita aqui. Isso acontece por um defeito do painel: a cada auditoria, um commit antigo ainda não rejeitado reabre a sugestão (detalhes no #94).
> Nenhum cálculo de importância nem razão de chances ajustada no repositório; depende do G6.

Nenhum notebook calcula importância de variáveis. O B_06 tem razões de chances **brutas**, que sofrem confundimento (asma e tosse aparecem como "protetoras"). Sem uma análise ajustada, o relatório não responde a segunda metade da pergunta de pesquisa.

### ③ O que fazer

> [!decisão] Replanejamento de 31/10
> Uma técnica por modelo, sem teste de estabilidade. A importância é de **associação preditiva**, não de causa.

**Dono:** Pessoa C (tabelas) · Pessoa B (interpretação) · **Prazo:** C: 02/11 (segunda, feriado), manhã · B: 02/11, tarde · **Esforço estimado:** C ≈ 1 h · B ≈ 1 h 30 · **Começa quando:** #5 (finalista e peso definidos)

#### Pessoa C
1. Carregue `val_meas` (`partitions=("train_ref", "val_meas")`) e o finalista ajustado em `train_ref` (mesmos hiperparâmetros do YAML).
2. **Logística:** razões de chance `np.exp(clf.coef_[0])` com os nomes de `pipe.named_steps["pre"].get_feature_names_out()`; salve `outputs/final/importancia_logistica.csv` (variável, categoria, razão de chance). Faça isso **no modelo logístico mesmo que o finalista seja o boosting** (é a tabela interpretável do relatório).
3. **Boosting (ou finalista):** `sklearn.inspection.permutation_importance(pipe, X_amostra, y_amostra, scoring="average_precision", n_repeats=3, random_state=42)` numa amostra de 50 mil fichas de `val_meas`, **nas colunas originais** (o pipeline completo é passado, então cada variável é embaralhada inteira). Salve `outputs/final/importancia_permutacao.csv` (variável, média, desvio).
4. Tempo esperado: ≈ 10 a 15 min; meça com `tools/medir_notebook.py` se rodar em notebook.

#### Pessoa B (fecha também o #57)
5. Tabela "bruto × ajustado" para asma, puerpério, tosse, febre, doença renal e diabetes: razão de chance **bruta** (B_06, tabelas `eda_02_obito_*`) ao lado da **ajustada** (logística). Mostre quais associações aparentemente "protetoras" (asma 0,30; puerpério 0,34; tosse 0,61) somem ou mudam de sinal depois do ajuste: é confundimento pela idade.
6. Uma figura com as 15 maiores importâncias por permutação e um parágrafo para a Discussão. Escreva "associado a maior risco previsto", nunca "causa" ou "protege".

### ④ Pronto quando

- existe: `outputs/final/importancia_logistica.csv` | As razões de chance da logística (np.exp(coef_)) estão em outputs/final/importancia_logistica.csv.
- existe: `outputs/final/importancia_permutacao.csv` | A importância por permutação do finalista em val_meas está em outputs/final/importancia_permutacao.csv.
- manual: | A tabela "bruto × ajustado" (asma, puerpério, tosse, febre, doença renal, diabetes), a figura das 15 maiores importâncias e o parágrafo da Discussão (que fecha o #57) estão no relatório (#133).

## #55 · Desempenho e erros por ano, idade, sexo e UF

- prioridade: P2
- situação: aberta
- estratégia: desenvolver
- marco: M5
- data ideal: 02/11
- responsável: Pessoa A (subgrupos e falsos negativos)
- pessoas: A
- fonte: notebooks C_16
- depende de: #2, #23
- tags: Metodologia, Notebook
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 2
- novo: não
- professores: não

### ① Para entender

Um modelo pode ir bem na média e mal num grupo. O C_16 já calcula métricas por subgrupo e analisa os falsos negativos (óbitos que o alerta não pegou), mas só roda no final.

Exemplo do B_07: a PR-AUC do boosting varia de 0,22 (2026) a 0,52 (2020) entre anos.

### ② Problema

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: passa para a **Pessoa A** e roda **uma vez**, nas previsões do teste (`predicoes_teste.parquet`); a versão em `val_tune` (decisão) foi cortada, porque o ponto de decisão não depende mais dela. Pendência de código do #137: `src/evaluation/cluster_profile.py` e `tests/test_cluster_profile.py` **não estão no Git** (o verificador não encontra o arquivo no commit `1e02321`); dê push antes de usar `perfil_estatistico`.

Faltam o desempenho e a calibração por ano, faixa etária, sexo e UF, e a análise de erros com foco em falsos negativos. O C_16 já faz essas análises, mas só roda depois da coorte definitiva.

### ③ O que fazer

> [!decisão] Replanejamento de 31/10
> Um modelo pode ir bem na média e mal num grupo. Uma tabela por dimensão, no Teste A, e o perfil dos óbitos que o alerta não pegou.

**Dono:** Pessoa A · **Prazo:** 02/11 (segunda, feriado), tarde · **Esforço estimado:** ≈ 1 h 30 · **Começa quando:** #2 e #23

1. `git status`: se `src/evaluation/cluster_profile.py` e `tests/test_cluster_profile.py` só existem na sua máquina, `git add` e commit agora (`feat: perfil estatistico dos grupos (#137)`). É o que fecha o critério do #137.
2. Leia `outputs/final/predicoes_teste.parquet` e filtre `particao == "test_ref"` (Teste A).
3. `metricas_por_grupo(df, y, prob, coluna, limiar=<corte congelado>, min_n=100)` (de `src/evaluation/errors.py`) para `ano_internacao`, `faixa_etaria`, `sexo_categoria`, `regiao_residencia` e `sg_uf`. Salve `outputs/final/subgrupos_teste_a.csv` (uma linha por dimensão e grupo).
4. Marque no relatório qualquer grupo com O/E (óbitos observados ÷ esperados) fora de 0,8 a 1,2 ou com PR-AUC ÷ prevalência abaixo de 1,5; escreva três frases (onde o modelo vai pior, se é uma diferença grande e por que pode ser: tamanho do grupo, qualidade do registro).
5. **Falsos negativos:** perfil dos óbitos **sem** alerta (`classe == "FN"`) × óbitos **com** alerta (`classe == "TP"`) no Teste A, com `perfil_estatistico` (#137). Salve `outputs/final/falsos_negativos_perfil.csv` e escreva um parágrafo: quem são (idade, comorbidades, sintomas), sem interpretação causal.
6. Commit: `resultados: subgrupos e falsos negativos [done:#55]`.

### ④ Pronto quando

- existe: `outputs/final/subgrupos_teste_a.csv` | As métricas por ano, faixa etária, sexo, região e UF no Teste A estão em outputs/final/subgrupos_teste_a.csv.
- existe: `outputs/final/falsos_negativos_perfil.csv` | O perfil dos óbitos sem alerta no Teste A está em outputs/final/falsos_negativos_perfil.csv.
- manual: | Os grupos com O/E fora de 0,8–1,2 (ou PR-AUC ÷ prevalência abaixo de 1,5) estão comentados e as três frases do relatório sobre subgrupos no teste estão escritas.

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

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: resolvido dentro do #91 (passos 5 e 6, Pessoa B).

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
- responsável: Pessoa A (dentro do #133)
- pessoas: A
- fonte: notebooks A_09 (seção 3, benchmark); outputs/tables/pessoa_a/a3_benchmark_split.csv
- depende de: —
- tags: Metodologia, Partição
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 0
- novo: não
- professores: não

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

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: um parágrafo dentro do #133; o A_09 sai do pacote (#143) e **não** é rodado.

No benchmark do A_09 (logística, cerca de 140 mil de treino e 30 mil de validação), a prevalência na validação foi 23,1% no sorteio e 13,8% no temporal. A PR-AUC de um classificador aleatório é igual à prevalência, então a comparação direta favorece o cenário com mais óbitos. Relativa ao chute, a PR-AUC temporal é maior (2,6× contra 2,0×), e a ROC-AUC também (0,821 contra 0,774). O mesmo padrão aparece sem 2020–21. A conclusão registrada no notebook pode levar a uma decisão de período e divisão (item 85) com base numa leitura incompleta.

### ③ O que fazer

**Pessoa A, dentro do #133 (01/11):** parágrafo de Métodos: "A PR-AUC depende da prevalência; por isso todas as comparações entre períodos usam também PR-AUC ÷ prevalência e ROC-AUC." Use a própria coorte: a PR-AUC da logística caiu de 0,44 (22% de óbitos) para 0,30 (8,4%), mas, contra o acaso, subiu de 2,0× para 3,6×. Cite a regra do professor (modelo pelo menos 25% melhor que o acaso). Não rodar o A_09.

### ④ Pronto quando

- manual: | O parágrafo de Métodos explica que a PR-AUC depende da prevalência, por isso todas as comparações entre períodos usam também PR-AUC ÷ prevalência e ROC-AUC, com o exemplo da coorte (0,44 com 22% de óbitos × 0,30 com 8,4%, de 2,0× para 3,6× contra o acaso).

## #110 · Geografia como separação da análise: ponto de corte por região e equidade (sem região como variável)

- prioridade: P2
- situação: aberta
- estratégia: desenvolver
- marco: M5
- data ideal: 02/11
- responsável: Pessoa C (conferência) · Pessoa B (figura e texto)
- pessoas: C, B
- fonte: artefato supervisionado (sg_uf); E_03; orientação de 17/10
- depende de: #80, #2
- tags: Features, Geografia
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1
- novo: sim
- professores: não

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

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: o **cálculo dos cortes por região foi para o #80** (Pessoa C, 01/11) e a medição por região no teste está no C_16 (#148). Aqui sobram a conferência e o texto: uma figura e três frases. A análise por região em `val_tune` (versão antiga do card) foi cortada: não muda nenhuma decisão.

Geografia nunca foi testada como variável.

### ③ O que fazer

> [!decisão] Replanejamento de 31/10
> O modelo é **único** para o país; a região entra como separação da análise (orientação de 24/10), nunca como variável.

**Dono:** Pessoa C (conferência) · Pessoa B (figura e texto) · **Prazo:** 02/11 (segunda, feriado), tarde · **Esforço estimado:** C ≈ 15 min · B ≈ 30 min · **Começa quando:** #80 e #2

1. **Pessoa C:** confira que `outputs/final/limiares_por_regiao.csv` (do #80) e `outputs/final/teste_por_regiao.csv` (do C_16) existem e que o corte regional **não** foi reescolhido com dados do teste.
2. **Pessoa B:** uma figura de barras por região (sensibilidade e precisão com o corte global e com o regional) a partir de `teste_por_regiao.csv`, salva em `outputs/final/figuras/regiao_corte_global_regional.png`.
3. **Pessoa B:** três frases para a Discussão: onde a sensibilidade fica abaixo de 0,80 com o corte global, quanto o corte regional corrige, e a ressalva "heterogeneidade entre regiões, que pode refletir acesso, capacidade hospitalar e qualidade do registro, e não diferença clínica".
4. Regiões que usaram o corte global por terem poucos óbitos em `val_cal` (`usa_global = True`) precisam aparecer na nota da figura.

### ④ Pronto quando

- existe: `outputs/final/limiares_por_regiao.csv` | Os cortes com sensibilidade ≥ 0,80 por região, escolhidos em val_cal, estão em outputs/final/limiares_por_regiao.csv.
- existe: `outputs/final/teste_por_regiao.csv` | A sensibilidade e a precisão por região no teste (corte global e regional) estão em outputs/final/teste_por_regiao.csv.
- existe: `outputs/final/figuras/regiao_corte_global_regional.png` | A figura por região (corte global × regional) existe.
- manual: | As três frases da Discussão sobre regiões estão no relatório (#133), com a ressalva sobre acesso, capacidade e registro.

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
- carga: 0
- novo: sim
- professores: sim

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

## #1 · Rodar o ajuste fino e preencher os hiperparâmetros no YAML

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M3
- data ideal: 01/11
- responsável: Pessoa C (dona; revisão cruzada sem edição concorrente)
- pessoas: C
- fonte: configs/supervised.yaml (gates G6, G7, G8; models; calibracao; limiar); notebooks C_13 e C_15
- depende de: #78, #132
- tags: Modelagem, Gate, Notebook
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 2
- novo: não
- professores: não

### ① Para entender

> [!decisão] Busca limitada, não exaustiva
> Para qualidade acadêmica importa mais uma comparação controlada e reproduzível do que uma busca grande. Executar no máximo 6 configurações de HGB no cenário vencedor; manter a logística como baseline interpretável.

> [!decisão] Decisão de 18/10
> Só no cenário vencedor do E_02 e só HGB: 12 configurações em subamostra de 500 mil, escolha em `val_tune`.

O caminho até o resultado final é uma fila: ajuste fino → calibração → limiar → teste. Hoje a fila está parada no primeiro passo, porque o G6 não foi aprovado.

<div class="flow"><span class="bad">C_13 ajuste fino</span><i>→</i><span class="">C_15 calibração e limiar</span><i>→</i><span class="">C_16 teste final</span></div>

O C_15 já rodou, mas sobre modelos sem ajuste. Por isso calibração e limiar terão de ser refeitos.

### ② Problema

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: roda no **domingo de manhã**, depois do G6 (#78, aprovado na noite de 31/10). A grade passa a estar **no YAML** (antes havia duas grades diferentes: a do card e a do arquivo), o `early_stopping` volta a `true` e a busca roda em **400 mil linhas** de `train_ref`. Escopo: 3 valores de C na logística (L2) mais uma rodada L1; 8 configurações de boosting.

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que esta pendência está aberta
> A auditoria automática do painel (27/10, 14:40) marcou este item como resolvido com base em commits de 18 e 19/10 (`a913228`, `0eab341`), todos anteriores às revisões de 24 e 26/10 e sem relação com a entrega descrita aqui. Isso acontece por um defeito do painel: a cada auditoria, um commit antigo ainda não rejeitado reabre a sugestão (detalhes no #94).
> Estado real: `models.logistic.C` e `models.boosting.learning_rate`/`max_iter` continuam `null`; `selecao_modelos.finalista_escolhido` é `null`; G6 pendente; C_13 com 0 de 9 células executadas; não existe `outputs/final/tuning_val_tune.csv`.
> Divergência a resolver antes de rodar: a grade do YAML não é a do card. YAML: `busca_C` com 5 valores (0,001 a 10) × 2 pesos de classe; boosting `busca_learning_rate` 3 × `busca_max_iter` 2 × 2 pesos = 12 configurações. Card: C em {0,01; 0,1; 1} e 8 configurações variando `max_leaf_nodes`, `min_samples_leaf` e `l2_regularization`. O `_candidatos_boosting` do C_13 só varia `learning_rate`, `max_iter`, `max_depth` e `class_weight`.
> `models.boosting.early_stopping: false` no YAML é repassado pela fábrica (`_kwargs_do_yaml`) e anula o padrão `True` de `build_boosting_pipeline`: com `max_iter` até 1.000, a busca fica bem mais lenta (#73).
> O YAML agora treina só com 2023–2025 (ver #102): confirme qual desenho vale antes do ajuste.

Os gates `G6_finalistas_tuning`, `G7_calibracao` e `G8_limiar` estão **pendentes**. Os campos que dependem deles estão nulos: `models.logistic.C`, `models.boosting.learning_rate`, `max_iter`, `max_depth`, `calibracao.metodo`, `limiar.metrica` e `limiar.otimo`. O C_13 rodou sem busca ("G6 pendente"), e o C_15 calibrou e escolheu o limiar sobre os modelos com valores padrão (C=1 na logística; 0,05 / 500 no boosting).

### ③ O que fazer

> [!decisão] Replanejamento de 31/10
> Busca **curta e reproduzível**, mais importante que uma busca grande: 3 configurações de logística, 1 rodada L1 e 8 de boosting. O peso de classe **não** entra na grade (é decidido no #5, só no vencedor).

**Dono:** Pessoa C · **Prazo:** 01/11 (domingo), 8h às 11h30 (a máquina trabalha sozinha durante a busca) · **Esforço estimado:** ≈ 2 h de trabalho + ≈ 40 min de máquina · **Começa quando:** #78 (G6 aprovado)

#### Passo a passo
1. **Grade no YAML (bloco completo, validado).** Em `configs/supervised.yaml`, apague **tudo da linha `models:` até a linha em branco imediatamente anterior a `calibracao:`** (são os blocos `models:` e `tuning:`) e cole no lugar o bloco abaixo. Antes dele ficam as linhas finais de `missingness:` (`    pipeline_principal: false` · `    sensibilidade: false # desativada em 28/10: ...` · linha em branco); depois dele vem a linha em branco e `calibracao:` · `  ativa: true` · `  metodo: null` · `  metodos_candidatos:`. O que mudou em relação ao arquivo de 30/10: `busca_C` só com 0,01, 0,1 e 1,0; `busca_*` do boosting com 2 × 1 × 1 × 2 × 2 × 1 × 1 = **8 configurações**; `busca_class_weight` só com `balanced` nas duas famílias; `max_configuracoes_por_modelo: 8`. Todo o resto (`decision_tree`, `random_forest`, `early_stopping: true`) permanece igual.

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

   Confira com um comando: `.\.venv\Scripts\python.exe -c "import yaml; y=yaml.safe_load(open('configs/supervised.yaml',encoding='utf-8')); print(y['tuning']['max_configuracoes_por_modelo'], y['models']['logistic']['busca_C'], y['models']['boosting']['busca_max_leaf_nodes'], y['calibracao']['ativa'])"` (esperado: `8 [0.01, 0.1, 1.0] [31, 63] True`).
2. **C_13:** em `_candidatos_boosting()` acrescente os eixos `busca_max_leaf_nodes`, `busca_min_samples_leaf` e `busca_l2_regularization` (mesmo padrão dos eixos que já existem). 2 × 1 × 1 × 2 × 2 × 1 × 1 = **8 configurações**. Em `MAX_TREINO_BUSCA` use `400_000` (ou `250_000`, se o tempo de um ajuste passou de 6 minutos no #78). A amostra é sorteio de linhas com semente 42 (cada linha é um grupo: 556.461 grupos em 556.462 linhas).
3. **Executar:** `.\.venv\Scripts\python.exe tools/medir_notebook.py notebooks/C/C_13_boosting.ipynb` (G6 aprovado → a busca roda). Meta: ≤ 40 min e ≤ 6 GB. Estoure o tempo: interrompa, baixe `MAX_TREINO_BUSCA` e registre no card.
4. **Rodada L1 da logística:** no melhor C, `build_finalista("logistic", C=<melhor>, penalty="l1", solver="saga", max_iter=300)`; conte `int((pipe.named_steps["clf"].coef_ == 0).sum())` coeficientes zerados entre os `pipe.named_steps["pre"].get_feature_names_out().size` totais e grave em `outputs/final/logistica_l1_val_tune.csv` (PR-AUC, número de zeros, tempo). É só a parte de regularização pedida; não entra na escolha do vencedor. Se passar de 8 minutos, use 150 mil linhas.
5. **Escolha:** maior PR-AUC em `val_tune` (desempate por Brier). O boosting só vence se superar a logística em **pelo menos 0,005** de PR-AUC; caso contrário, o finalista é a logística (interpretável). Registre as duas melhores configurações de cada família no card.
6. **YAML (à mão, com o bloco impresso pelo C_13):** `models.logistic.C`; `models.boosting.learning_rate`, `max_iter`, `max_leaf_nodes`, `min_samples_leaf`, `l2_regularization`; `selecao_modelos.finalista_escolhido` (`hist_gradient_boosting` ou `logistic`); `selecao_modelos.run_id_finalista` (o valor impresso pelo C_13 com `identificador_execucao`).
7. **Libere a memória** (`del pipe_*`, `liberar(globals(), [...])`).
8. Commit: `feat: ajuste fino e finalista no YAML [done:#1]`. Comente no #5 e no #79: finalista, hiperparâmetros e o `run_id_finalista`.

### ④ Pronto quando

- yaml: `configs/supervised.yaml` :: `models.logistic.C` != `null` | O C escolhido da logística está preenchido no supervised.yaml.
- yaml: `configs/supervised.yaml` :: `models.boosting.learning_rate` != `null` | O learning_rate escolhido do boosting está preenchido no YAML.
- yaml: `configs/supervised.yaml` :: `selecao_modelos.finalista_escolhido` != `null` | O finalista escolhido (logística ou boosting, pela PR-AUC em val_tune com margem de 0,005) está preenchido.
- yaml: `configs/supervised.yaml` :: `selecao_modelos.run_id_finalista` != `null` | O identificador da execução do finalista está no YAML.
- notebook-executado: `notebooks/C/C_13_boosting.ipynb` | O C_13 está salvo executado (busca rodada), sem saída de erro.
- existe: `outputs/final/tuning_val_tune.csv` | A tabela da busca (todas as configurações, métricas e tempo) está em outputs/final/tuning_val_tune.csv.
- existe: `outputs/final/logistica_l1_val_tune.csv` | A rodada L1 da logística (PR-AUC e número de coeficientes zerados) está em outputs/final/logistica_l1_val_tune.csv.

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
- responsável: Pessoa C (dona; revisão cruzada sem edição concorrente)
- pessoas: C
- fonte: src/models/logistic.py; src/models/boosting.py; configs/supervised.yaml (class_weight); B_10
- depende de: #1, #148
- tags: Modelagem, Calibração
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1
- novo: não
- professores: não

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

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: a comparação com e sem peso roda **no C_15** (já tem a célula), só no finalista, com calibração `sigmoid` fixa, e **antes** do #79. O C_15 adaptado vem do #148 (Pessoa B). A regra de decisão não mudou (0,005 de PR-AUC e Brier calibrado que não piora).

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que voltou para "em andamento"
> Marcada como concluída em 27/10 (14:39). O que foi feito está certo e é útil: o commit `35b90f8` acrescentou `busca_class_weight: [balanced, null]` na logística e no boosting, e o C_13 passou a variar o peso de classe na busca (`_candidatos_boosting` e `_candidatos_logistica`).
> O que falta para concluir, conforme o "O que fazer": (1) rodar a comparação (o C_13 tem 0 de 9 células executadas); (2) comparar com e sem peso no modelo vencedor, olhando PR-AUC e **Brier depois da calibração**; (3) gravar a escolha no YAML (`class_weight` continua `balanced` fixo nas famílias). Além disso, a busca roda sobre o artefato antigo e o vocabulário antigo (`treino/validacao`), que dependem do #131 e do #132.

Os dois finalistas usam `class_weight="balanced"`. A média das probabilidades previstas ficou em 42,4% (boosting) e 43,0% (logística), contra prevalência real de 21,9%. Isso não afeta a ordenação (ROC-AUC, PR-AUC), mas afeta Brier, calibração e qualquer limiar.

**Atualização 17/10:** o C_15 mostrou que a calibração corrige o problema (boosting: Brier 0,1959 → 0,1409; ECE 0,0018). Ainda não foi testado treinar sem peso.

### ③ O que fazer

> [!decisão] Replanejamento de 31/10
> A escolha entre `balanced` e `None` precisa vir **antes** de escolher o método de calibração (#79), porque o peso muda a escala das probabilidades. Para não criar um ciclo, a comparação usa sempre `sigmoid`.

**Dono:** Pessoa C · **Prazo:** 01/11 (domingo), 12h às 13h · **Esforço estimado:** ≈ 1 h (mais ≈ 10 min de máquina) · **Começa quando:** #1 (finalista no YAML) e #148 (C_15 adaptado)

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
- data ideal: 31/10
- responsável: Pessoa C (aprova) + Pessoa A (registra)
- pessoas: C, A
- fonte: configs/supervised.yaml (gates.G6_finalistas_tuning); notebooks C_13
- depende de: #132, #140, #144, #54
- tags: Gate, Modelagem
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1
- novo: não
- professores: não

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

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: **o G6 passa a ser aprovado ANTES do ajuste**, e não depois. O C_13 só executa a busca com `gates.G6_finalistas_tuning.status = aprovado`; a versão anterior deste card dependia do #1 e do #5, o que formava um ciclo (o ajuste esperava o gate e o gate esperava o ajuste). O que sai do ajuste (finalista e hiperparâmetros) é critério do #1, não do G6.

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que esta pendência está aberta
> A auditoria automática do painel (27/10, 14:40) marcou este item como resolvido com base em commits de 09 e 11/10, todos anteriores às revisões de 24 e 26/10 e sem relação com a entrega descrita aqui. Isso acontece por um defeito do painel: a cada auditoria, um commit antigo ainda não rejeitado reabre a sugestão (detalhes no #94).
> `gates.G6_finalistas_tuning.status: pendente`; nenhum pré-requisito do checklist (#131, #135, #132, #140, #1, #5) está concluído.

O gate `G6_finalistas_tuning` está `pendente`. Sem ele, o C_13 não faz a busca de hiperparâmetros. Antes de aprovar, o boosting precisa reproduzir o piloto, o uso de `class_weight` precisa estar incluído na busca e o tempo da busca precisa caber no prazo; caso contrário, o ajuste fino é feito sobre um modelo diferente da lista curta.

**Atualização 17/10:** o C_13 rodou e registrou "G6 pendente: busca não executada". O boosting do `src` continua com one-hot denso e sem categóricas nativas (item 4).

### ③ O que fazer

> [!decisão] Replanejamento de 31/10
> O G6 autoriza a **busca**, com a grade e o orçamento de tempo já escritos no YAML. Quem fecha a escolha do finalista é o #1.

**Dono:** Pessoa C (aprova) + Pessoa A (registra) · **Prazo:** 31/10 (sábado), 20h às 21h · **Esforço estimado:** ≈ 30 min (C ≈ 15 min · A ≈ 15 min) · **Começa quando:** #144, #132, #140 e #54

#### Checklist para aprovar o G6
1. **#144 concluído:** suíte rápida verde e G1, G2, G4 e G5 `aprovado` no YAML.
2. **#132 concluído:** C_11 a C_13 rodaram em `train_ref` → `val_tune` (sem busca). Anote no card o tempo de **um** ajuste do boosting com os valores padrão (célula do C_13): se passar de 6 minutos, a busca usa 250 mil linhas, e não 400 mil.
3. **#140 concluído** (decisões registradas) e `features.final` no YAML é a lista definitiva (31 variáveis, ou 28 se os três sintomas saíram; neste último caso o artefato precisa ser regenerado antes, e o G1 volta a ser aprovado).
4. **#54 salvo** (`outputs/final/ablacoes_val_tune.csv`) e `bootstrap_grupo` (#127) no `src`.
5. **A grade está no YAML** (ver #1, passo 1) e `tuning.max_configuracoes_por_modelo: 8`.
6. `models.boosting.early_stopping: true` e `models.*.class_weight: balanced` (o peso é decidido no #5, no vencedor).

**Ação:** `gates.G6_finalistas_tuning.status: aprovado`, `aprovado_por: time_do_projeto`, `data: '2026-10-31'`. A Pessoa A registra a entrada no `docs/decisoes.md` (§29.29): grade, orçamento (8 configurações de boosting, 3 de logística, 400 mil linhas) e o critério de escolha (PR-AUC em `val_tune`; boosting só vence com 0,005 de diferença).

### ④ Pronto quando

- yaml: `configs/supervised.yaml` :: `gates.G6_finalistas_tuning.status` = `aprovado` | O gate G6 está aprovado no supervised.yaml, com data.
- yaml: `configs/supervised.yaml` :: `features.final` existe | A lista final de variáveis está no YAML.
- yaml: `configs/supervised.yaml` :: `tuning.max_configuracoes_por_modelo` = `8` | O orçamento da busca (8 configurações por modelo) está no YAML.
- manual: | O checklist do G6 neste card está todo marcado (#144, #132, #140, #54, #127, grade no YAML) e a Pessoa A registrou a aprovação no docs/decisoes.md.

## #9 · Saturação, desconforto respiratório e vacina: cada documento diz uma coisa

- prioridade: P2
- situação: parcial
- estratégia: documentar
- marco: M1
- data ideal: 31/10
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

> [!decisão] Enxugado em 27/10 (eficiência primeiro)
> Feito dentro do **#73** (Pessoa A). Marque como concluído junto com ele.

### ④ Pronto quando

- yaml: `configs/supervised.yaml` :: `features.sensibilidade_gravidade_admissao` contem `saturacao` | Saturação fica só na sensibilidade de gravidade na admissão (fora do modelo principal).
- yaml: `configs/supervised.yaml` :: `features.final` nao-contem `saturacao` | Saturação não está nas 31 features do modelo principal.
- nao-contem: `docs/decisoes.md` :: `Modelo A: núcleo clínico de admissão` | O docs/decisoes.md deixou de colocar saturação no "Modelo A" e passou a dizer o mesmo que o YAML (§11, §13, §17 alinhadas no pacote do #73).

## #13 · A sazonalidade é criada, mas não entra no modelo

- prioridade: P3
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
- carga: 0
- novo: não
- professores: não

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

## #54 · Rodar as sensibilidades de gravidade, contexto e "qualquer óbito"

- prioridade: P1
- situação: aberta
- estratégia: explorar
- marco: M3
- data ideal: 31/10
- responsável: Pessoa C (execução) + Pessoa A (copia a tabela no relatório)
- pessoas: C, A
- fonte: configs/supervised.yaml (sensibilidades); Projeto
- depende de: #132, #141, #142
- tags: Metodologia, Modelagem
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1
- novo: não
- professores: não

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

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: roda **no sábado à tarde, depois do #132**, e vira insumo único do #140. Só a logística roda todas as linhas; o boosting roda apenas P e P − 3. A linha "P com comorbidades recodificadas" é feita **na memória**, aplicando `recodificar_comorbidades_por_fator_risco` às colunas lidas do artefato (`fator_risc` está em `audit_columns`), sem regenerar o artefato. O `recodificar_comorbidades_fator_risco` continua `false` no YAML.

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que esta pendência está aberta
> A auditoria automática do painel (27/10, 14:40) marcou este item como resolvido com base em commits de 09 e 11/10, todos anteriores às revisões de 24 e 26/10 e sem relação com a entrega descrita aqui. Isso acontece por um defeito do painel: a cada auditoria, um commit antigo ainda não rejeitado reabre a sugestão (detalhes no #94).
> Não existe `outputs/final/ablacoes_val_tune.csv`; depende do #131/#142, que não começaram.
> Ao rodar, desligar no YAML `target.sensibilidade_qualquer_obito.ativa` e `sensibilidades.alvo_qualquer_obito` (cortados em 27/10) ou registrar que não serão rodados.

Faltam as sensibilidades de gravidade na admissão (com `saturacao` e `desc_resp`), de contexto incremental e de alvo "qualquer óbito". Dependem do item 7, porque as colunas não estão no artefato.

### ③ O que fazer

> [!decisão] Replanejamento de 31/10
> A tabela de ablações responde **três perguntas objetivas** do #140 e nada além: (1) os três sintomas de 2019 saem? (2) recodificar comorbidades muda o resultado? (3) gravidade, contexto ou região acrescentam algo que mereça mudar o plano? Qualquer outra leitura vai para o relatório.

**Dono:** Pessoa C · **Prazo:** 31/10 (sábado), 15h às 17h · **Esforço estimado:** ≈ 1 h 30 · **Revisão:** Pessoa A (copia a tabela no relatório) · **Começa quando:** #132

| Linha | Conjunto | Modelos |
|---|---|---|
| P | as 31 variáveis do G1 (`features.final`) | logística e boosting |
| P − 3 sintomas | sem `perd_olft`, `perd_pala`, `fadiga` | logística e boosting |
| P com comorbidades recodificadas | P, com a regra do #141 aplicada na memória | logística |
| P + gravidade | P + `saturacao`, `desc_resp` | logística |
| P + contexto | P + `cs_escol_n`, `vacina` | logística |
| P + região | P + `regiao_residencia` | logística |

#### Passo a passo
1. Notebook novo e descartável **dentro do C_12** (seção "Ablações", sem criar arquivo novo). Carregue `partitions=("train_ref", "val_tune")` com `columns=None` (todas as 46 colunas: ≈ 600 mil linhas, cabe). `ano_internacao` e as colunas extras vêm do próprio artefato.
2. Função auxiliar `ajustar_e_medir(colunas, familia)`: `build_finalista(familia, preprocessor=build_preprocessor(numericas=[...], categoricas=[...]))` com os hiperparâmetros **padrão** do YAML (sem ajuste), `fit` em `train_ref`, previsões em `val_tune`. Para as linhas extras, passe as listas de numéricas e categóricas explicitamente (o `build_preprocessor` aceita `numericas=`, `categoricas=` e `saida=`; o boosting usa `saida="ordinal"`).
3. Linha de comorbidades: `X = recodificar_comorbidades_por_fator_risco(df[FEATURES + ["fator_risc"]])` e depois remova `fator_risc` antes do `fit` (a variável não entra no modelo).
4. Para cada linha: PR-AUC, PR-AUC ÷ prevalência, ROC-AUC, Brier e **diferença para P** (com IC de bootstrap pareado do #127, assim que existir; se ainda não existir, só o ponto). Só em P e P − 3, calcule também a ROC-AUC **por ano** (2019, 2023, 2024, 2025), que é a medida do critério (a) do #50.
5. **Critério do #50 (único, sem "tirar só por tirar"):** retire os três sintomas apenas se (a) a ROC-AUC de 2019 subir ≥ 0,01 sem eles **e** o IC pareado dessa diferença não incluir zero, ou (c) a importância por permutação das três vier ≥ 80% de 2019 (permutação em 50 mil fichas de `val_tune`, `n_repeats=3`). Caso contrário, mantenha e documente. A decisão sai no #140, não aqui.
6. Grave `outputs/final/ablacoes_val_tune.csv` (uma linha por linha × modelo) e, em `configs/supervised.yaml`, deixe `sensibilidades.alvo_qualquer_obito.ativa: false` (cortado em 27/10: a coorte definitiva não tem evolução 3).
7. Comente no #140 as três linhas de resumo (o que encontrou, tamanho do efeito, se sugere mudança). Meça o notebook com `tools/medir_notebook.py` se rodar fora do C_12.
8. Commit: `feat: ablacoes em val_tune [done:#54]`.

### ④ Pronto quando

- existe: `outputs/final/ablacoes_val_tune.csv` | A tabela de ablações (P, P − 3 sintomas, P com comorbidades recodificadas, P + gravidade, P + contexto, P + região) com PR-AUC, PR-AUC ÷ prevalência, ROC-AUC, Brier e diferença para P está em outputs/final/ablacoes_val_tune.csv.
- yaml: `configs/supervised.yaml` :: `sensibilidades.alvo_qualquer_obito.ativa` = `false` | A sensibilidade "qualquer óbito", cortada em 27/10, está desligada no YAML.
- manual: | O resumo das ablações foi comentado no #140 (três linhas: o que encontrou, tamanho do efeito, se sugere mudança) e a ROC-AUC por ano (P × P − 3) está na tabela.

## #52 · Fichas de óbito têm as doenças prévias mais preenchidas

- prioridade: P3
- situação: aberta
- estratégia: explorar
- marco: M3
- data ideal: 31/10
- responsável: Pessoa B
- pessoas: B
- fonte: Projeto (análise de desempenho)
- depende de: #141, #142, #23
- tags: Metodologia, Vazamento
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1
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

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: roda **uma vez**, com as previsões do piloto em `val_tune`, e vira um parágrafo de limitação no relatório. Não entra mais no #140 como condição para o ajuste.

As comorbidades estão mais preenchidas nos óbitos (diferença de 13 a 21 pontos percentuais). Pode ser viés de documentação: fichas de óbito são revisadas com mais cuidado. Nesse caso, o modelo aprende o preenchimento, não a condição clínica.

### ③ O que fazer

> [!decisão] Replanejamento de 31/10
> Uma tabela, um parágrafo. Não refazer com as previsões do teste.

**Dono:** Pessoa B · **Prazo:** 31/10 (sábado), tarde · **Esforço estimado:** ≈ 30 min · **Começa quando:** #142, #23 e #141

1. Leia `outputs/final/predicoes_val_tune_piloto.parquet` (#142) e junte, por `id_registro`, os 11 sintomas e as 12 comorbidades do artefato (`load_supervised_artifact(..., partitions=("val_tune",), columns=[...])`).
2. **Completude** = % desses 23 campos com resposta 1 ou 2 (sim ou não). Divida em terços com `pd.qcut(completude, 3, duplicates="drop")`.
3. `metricas_por_grupo(df, y, prob, "terco")` (de `src/evaluation/errors.py`). Salve `outputs/final/completude_val_tune.csv`.
4. Escreva o parágrafo de limitação para o relatório: se o desempenho sobe com a completude da ficha, o modelo pode estar lendo o preenchimento (viés de documentação) e não só a condição clínica. Cite que a hipótese de preenchimento por pulo da ficha (`fator_risc`, #141) explica parte da diferença.
5. Comente o resultado no #140 (três linhas).

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
- carga: 3
- novo: sim
- professores: não

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

## #2 · Executar o C_16 uma única vez nas duas janelas de teste autorizadas

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M5
- data ideal: 02/11
- responsável: Pessoa C (dona; revisão cruzada sem edição concorrente)
- pessoas: C
- fonte: notebooks C_16; configs/supervised.yaml (features.final, selecao_modelos.finalista_escolhido)
- depende de: #81, #148
- tags: Notebook, Gate, Dados/Coorte
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 2
- novo: não
- professores: não

### ① Para entender

> [!ok] Decisão fechada em 18/10
> A coorte definitiva inicial será a seleção de features da coorte provisória. O treino principal usará exclusivamente 2019, 2023, 2024 e 2025. Haverá duas janelas de teste: (A) 2019, 2023, 2024 e 2025; (B) 2019 a 2025, incluindo 2020–2022. O ano de 2026 não participa do desenvolvimento nem dos testes principais e fica apenas como exploração opcional, depois de todo o restante concluído.

O C_16 abre o teste e calcula o resultado oficial. Ele se recusa a rodar se a lista final de variáveis e o finalista não estiverem escolhidos, e esses dois dependem da coorte definitiva.

> [!atenção] Atenção
> Não preencha `features.final` com a lista provisória só para o C_16 rodar: isso gastaria a única abertura do teste num modelo que ainda vai mudar.

### ② Problema

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: roda na **manhã de 02/11 (feriado)**, e não em 01/11. O C_16 chega pronto e limpo do #148; o #26 (`test_opened` no manifesto) está dentro do C_16. Memória: o C_16 lê `test_pandemic` (2.915.829 linhas) em lotes de 250 mil e **não** pode ser reexecutado.

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que esta pendência está aberta
> A auditoria automática do painel (27/10, 14:40) marcou este item como resolvido com base em commits de 09 e 11/10 (`0f565b5`, `c8a9997`), todos anteriores às revisões de 24 e 26/10 e sem relação com a entrega descrita aqui. Isso acontece por um defeito do painel: a cada auditoria, um commit antigo ainda não rejeitado reabre a sugestão (detalhes no #94).
> Estado real: G9 pendente; `manifesto_supervisionado.json` com `test_opened: false`; C_16 com 0 de 11 células executadas. O C_16 ainda escolhe o manifesto pela data do arquivo (`st_mtime`) e carrega `partitions=("treino", "validacao", "teste")`, vocabulário antigo (#132).

O C_16 interrompe a execução quando `features.final` ou `selecao_modelos.finalista_escolhido` estão vazios. Os dois campos dependem da coorte definitiva e da aprovação do G1, que ainda está pendente. Portanto, o C_16 não pode rodar antes de a coorte definitiva chegar.

### ③ O que fazer

> [!decisão] Replanejamento de 31/10
> Uma execução, kernel limpo, máquina com ≥ 8 GB livres e nada mais aberto. O C_16 já foi revisado em ensaio no #81; aqui só se roda.

**Dono:** Pessoa C · **Prazo:** 02/11 (segunda, feriado), 8h às 10h30 (≈ 30 min de máquina) · **Esforço estimado:** ≈ 2 h · **Começa quando:** #81 (G9 aprovado, com tag `congelado-2026-11-01`)

1. Feche o Excel e o navegador pesado; `git pull`; `git status` limpo; confira que `git describe --tags` mostra `congelado-2026-11-01`.
2. Kernel limpo; rode o C_16 **inteiro de uma vez**: `.\.venv\Scripts\python.exe tools/medir_notebook.py notebooks/C/C_16_validacao_final.ipynb --salvar-no-lugar --limite-s 1800` (a ferramenta registra duração e pico de memória em `outputs/final/performance_notebooks.csv`).
3. Se quebrar **antes** de carregar o teste (passos 9 a 12 do #148): corrija e rode de novo. Se quebrar **depois**: corrija **só** o código de relatório (nunca modelo, calibrador, corte ou lista de variáveis), registre no card o que mudou e por quê, e rode apenas a parte de relatório a partir das previsões salvas (`predicoes_teste.parquet`).
4. Confirme as saídas do contrato do #119 e que o manifesto tem `test_opened: true`, `test_opened_utc` e `test_opened_commit`.
5. Commit só de tabelas, figuras e manifesto: `resultados: testes A e B [done:#2] [done:#26]`.
6. Comente no card: "testes abertos às HH:MM; nenhuma decisão de modelagem muda a partir daqui". Avise A e B: #55, #91, #110 e o relatório (#133) podem começar.

### ④ Pronto quando

- yaml: `configs/supervised.yaml` :: `gates.G9_holdout.n_acessos` = `1` | O G9 registra exatamente um acesso aos testes.
- json: `data/analytical/manifesto_supervisionado.json` :: `test_opened` = `true` | O manifesto foi regravado com test_opened: true, data e commit logo depois de carregar os testes (substitui o #26).
- notebook-executado: `notebooks/C/C_16_validacao_final.ipynb` | O C_16 está salvo executado de uma vez, sem saída de erro.
- manual: | O card registra "testes abertos às HH:MM; nenhuma decisão de modelagem muda a partir daqui" e o tempo e o pico de memória da execução.

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

## #79 · Aprovar o G7: escolher o método de calibração (proposta do C_15: sigmoid)

- prioridade: P1
- situação: parcial
- estratégia: desenvolver
- marco: M4
- data ideal: 01/11
- responsável: Pessoa C (dona; revisão cruzada sem edição concorrente) + Pessoa A (registra)
- pessoas: C, A
- fonte: configs/supervised.yaml (gates.G7_calibracao; calibracao.metodo); notebooks C_15
- depende de: #1, #5, #148
- tags: Gate, Calibração
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 2
- novo: não
- professores: não

### ① Para entender

**Calibrar** é ajustar as probabilidades para que "30%" signifique 30% de fato. O C_15 já testou dois métodos e propôs **sigmoid** para o boosting e **isotonic** para a logística.

<div class="bars">
<div class="br"><span class="y">Brier antes</span><div class="t"><div class="b red" style="width:89.0%"></div></div><span class="v">0,196</span></div>
<div class="br"><span class="y">Brier depois</span><div class="t"><div class="b gn" style="width:64.0%"></div></div><span class="v">0,141</span></div>
<div class="br"><span class="y">Dummy (chute)</span><div class="t"><div class="b gr" style="width:77.7%"></div></div><span class="v">0,171</span></div>
</div>

Depois de calibrado, o boosting erra menos na probabilidade do que o chute. Falta só formalizar a escolha, mas ela deve ser refeita depois do ajuste fino, porque o modelo vai mudar.

### ② Problema

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: roda no domingo à tarde, **depois do #1 e do #5**, usando o C_15 adaptado (#148). Acrescenta duas medidas que o card pedia e o `src` não tinha: **intercepto e inclinação de calibração** e **ECE por quantis** (o `ece` atual usa faixas de largura igual, e quase todas as probabilidades caem nas primeiras faixas porque a prevalência é 8%).

O gate `G7_calibracao` está **pendente** e `calibracao.metodo` está `null`. O C_15 já rodou sobre os modelos com valores padrão e propôs `calibracao.metodo: sigmoid` (boosting: Brier 0,1959 → 0,1409; ECE 0,0018). Como o ajuste fino (G6) ainda não aconteceu, essa escolha foi feita sobre um modelo que ainda vai mudar.

### ③ O que fazer

> [!decisão] Replanejamento de 31/10
> Escolha por **menor Brier em `val_meas`**, com empate (diferença < 0,0005) para `sigmoid`. A ordenação dos pacientes não pode mudar (ROC-AUC igual).

**Dono:** Pessoa C · Pessoa A (registra) · **Prazo:** 01/11 (domingo), 14h às 16h · **Esforço estimado:** C ≈ 1 h 30 · A ≈ 15 min · **Começa quando:** #1, #5 e #148

#### O que é calibração
Fazer com que "30% de risco" signifique cerca de 30 óbitos em cada 100 fichas parecidas. A calibração quase não muda a ordem dos pacientes; ela corrige o **número**.

#### Passo a passo
1. **Duas funções novas (blocos completos, testados).** Cole ao **final** de `src/evaluation/calibration.py`, depois da última linha de `brier_decomposicao` (`    }`), com duas linhas em branco antes. Nada a apagar; `np`, `_to_np`, `_to_int_labels` e `ArrayLike` já estão no arquivo:

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
2. Execute o C_15 com `tools/medir_notebook.py` (G6 aprovado e finalista no YAML). Para o finalista congelado (`FrozenEstimator`, feito pelo `calibrar`), ajuste **sigmoid** e **isotônica** só em `val_cal`; meça em `val_meas`: Brier, log loss, intercepto, inclinação, ECE por quantis (10 faixas) e a curva de calibração (figura em `outputs/final/figuras/calibracao_val_meas.png`).
3. **Regra de escolha:** menor Brier em `val_meas`; diferença menor que 0,0005 → `sigmoid`.
4. Conferir que a ordenação não mudou: PR-AUC e ROC-AUC iguais ao modelo bruto com tolerância de 0,002 (a isotônica pode criar empates).
5. **Referência de sanidade:** o Brier calibrado precisa ficar **abaixo de 0,077** (o do modelo nulo com 8,4% de prevalência) e a inclinação entre 0,9 e 1,1. Se não ficar, pare e comente no card antes de seguir para o #80.
6. YAML (à mão): `calibracao.metodo`, `gates.G7_calibracao.status: aprovado`, `aprovado_por: time_do_projeto`, `data: '2026-11-01'`. Pessoa A registra no `decisoes.md` (§29.30): método, Brier antes e depois, intercepto e inclinação.
7. Commit: `feat: calibracao escolhida e G7 aprovado [done:#79]`.

### ④ Pronto quando

- yaml: `configs/supervised.yaml` :: `calibracao.metodo` != `null` | O método de calibração (sigmoid ou isotônica, pelo menor Brier em val_meas) está no YAML.
- yaml: `configs/supervised.yaml` :: `gates.G7_calibracao.status` = `aprovado` | O G7 está aprovado, com data.
- define: `src/evaluation/calibration.py` :: `calibracao_intercepto_inclinacao` | A função de intercepto e inclinação de calibração existe em src/evaluation/calibration.py.
- define: `src/evaluation/calibration.py` :: `ece_quantis` | A função ece_quantis existe em src/evaluation/calibration.py.
- teste: `tests/test_calibration.py` | Os testes de calibração passam.
- existe: `outputs/final/calibracao_val_meas.csv` | A tabela dos dois métodos (Brier, log loss, intercepto, inclinação, ECE) em val_meas está em outputs/final/calibracao_val_meas.csv.

## #80 · Aprovar o G8: escolher o limiar (proposta do C_15: 0,255 pelo F1)

- prioridade: P1
- situação: parcial
- estratégia: desenvolver
- marco: M4
- data ideal: 01/11
- responsável: Pessoa C (dona; revisão cruzada sem edição concorrente) + Pessoa A (registra)
- pessoas: C, A
- fonte: configs/supervised.yaml (gates.G8_limiar; limiar.metrica, limiar.otimo); notebooks C_15
- depende de: #79
- tags: Gate, Calibração
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 2
- novo: não
- professores: não

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

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: o card **absorve os cortes por região do #110** (cálculo da Pessoa C). Achado do código: `escolher_limiar` só aceita `f1`, `precision`, `recall`, `accuracy` e `youden_j`; o YAML lista `recall_minimo` (adicionado no #73) e com `limiar.metrica = recall_minimo` o C_15 levanta `ValueError`. Esta tarefa implementa `recall_minimo`.

O gate `G8_limiar` está **pendente**, e `limiar.metrica` e `limiar.otimo` estão `null`. O C_15 propôs `limiar.metrica: f1` e `limiar.otimo: 0.255`, calculados sobre probabilidades calibradas de um modelo ainda sem ajuste fino. Não está decidido se o projeto usa um limiar único ou faixas de risco.

### ③ O que fazer

> [!decisão] Replanejamento de 31/10
> **Regra única** para o corte global e para os regionais: o de **maior precisão entre os que têm sensibilidade ≥ 0,80**. O professor disse que 80% de sensibilidade "já está bom" e 70% "já está muito bom". Os cortes de referência (70%, F1 máximo e Youden) só aparecem em tabela.

**Dono:** Pessoa C · Pessoa A (registra) · **Prazo:** 01/11 (domingo), 16h às 19h · **Esforço estimado:** C ≈ 2 h (global ≈ 1 h + regional ≈ 1 h) · A ≈ 15 min · **Começa quando:** #79

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
3. **Referências (só tabela):** sensibilidade ≥ 0,70, F1 máximo e Youden.
4. **Tabela de cortes** de 0,05 a 0,60 (passo 0,05) para o apêndice: chame `metricas_por_limiar(y, p, n_limiares=99)` (passo 0,01) e filtre os múltiplos de 0,05 com `np.isclose`. Junte o corte principal e as referências e grave em `outputs/final/limiares_val_cal.csv`.
5. **Medir sem alterar:** aplique os cortes a `val_meas` e anote sensibilidade e precisão (esperado: sensibilidade perto de 0,80; se ficar abaixo de 0,75, comente no card).
6. **Faixas de risco** (baixo, médio, alto) pelos tercis da probabilidade calibrada em `val_cal`, só como descrição, em `outputs/final/faixas_risco_val_cal.csv`.
7. **Por região (absorve o #110):** repita o passo 2 em cada `regiao_residencia` (Norte, Nordeste, Centro-Oeste, Sudeste, Sul). Região com menos de 100 óbitos em `val_cal` usa o **corte global** e é marcada (`usa_global = True`; os óbitos são ≈ 3.350 em `val_cal`, e as regiões pequenas ficam perto do limite). Grave `outputs/final/limiares_por_regiao.csv` (n, óbitos, corte, sensibilidade, precisão, `usa_global`) e, no YAML, `limiar.por_regiao` (mapa região → corte).
8. YAML (à mão): `limiar.metrica: recall_minimo`, `limiar.min_recall: 0.80`, `limiar.otimo`, `limiar.por_regiao`, `gates.G8_limiar.status: aprovado`, `aprovado_por: time_do_projeto`, `data: '2026-11-01'`. Pessoa A registra no `decisoes.md` (§29.31).
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
- data ideal: 01/11
- responsável: Pessoa A (conduz o checklist) + Pessoa C (modelagem) + Equipe (aprova)
- pessoas: A, C, Equipe
- fonte: configs/supervised.yaml (gates.G9_holdout); notebooks C_16
- depende de: #77, #79, #80, #135, #144, #148, #127
- tags: Gate, Vazamento
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1
- novo: não
- professores: não

### ① Para entender

> [!ok] Decisão fechada em 18/10
> A coorte definitiva inicial será a seleção de features da coorte provisória. O treino principal usará exclusivamente 2019, 2023, 2024 e 2025. Haverá duas janelas de teste: (A) 2019, 2023, 2024 e 2025; (B) 2019 a 2025, incluindo 2020–2022. O ano de 2026 não participa do desenvolvimento nem dos testes principais e fica apenas como exploração opcional, depois de todo o restante concluído.

O **teste** é a prova final: 587 mil internações que nenhum modelo viu. O **G9** autoriza abrir essa prova **uma única vez**, no C_16. Depois disso, nenhuma decisão de modelagem pode mudar.

<div class="flow"><span class="">G1 variáveis</span><i>→</i><span class="">G6 ajuste fino</span><i>→</i><span class="">G7 calibração</span><i>→</i><span class="">G8 limiar</span><i>→</i><span class="bad">G9 abrir o teste</span><i>→</i><span class="">Resultado final</span></div>

> [!exemplo] Exemplo
> É como abrir o envelope da nota final: se depois você muda a resposta, a nota deixa de valer.

### ② Problema

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: o G9 é aprovado na **noite de 01/11** (antes: 31/10) e o #2 roda na **manhã de 02/11**. A tag de congelamento passa a ser `congelado-2026-11-01`. Entram no checklist: o C_16 revisado em modo de ensaio (#148), a leitura do teste em lotes (#145) e os cortes por região (#80).

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que esta pendência está aberta
> A auditoria automática do painel (27/10, 14:40) marcou este item como resolvido com base em commits de 09 e 11/10, todos anteriores às revisões de 24 e 26/10 e sem relação com a entrega descrita aqui. Isso acontece por um defeito do painel: a cada auditoria, um commit antigo ainda não rejeitado reabre a sugestão (detalhes no #94).
> `gates.G9_holdout.status: pendente`, `n_acessos: 0`. Nenhum pré-requisito concluído.

O gate `G9_holdout` está `pendente`. Ele libera o teste uma única vez e é irreversível: depois de `executado`, nenhuma decisão de modelagem pode mudar. Só pode ser aprovado com modelo, features, calibração e limiar congelados e com a proteção do teste funcionando.

### ③ O que fazer

> [!decisão] Replanejamento de 31/10
> O G9 libera o teste **uma única vez**. Depois dele, **nada** do modelo muda. É o envelope da nota final.

**Dono:** Pessoa A (conduz) + Pessoa C (modelagem) + Equipe (aprova) · **Prazo:** 01/11 (domingo), 21h às 23h · **Esforço estimado:** A ≈ 1 h · C ≈ 30 min · **Começa quando:** #77, #79, #80, #135, #144, #148 e #127

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
8. `git status` limpo; commit de congelamento com a tag **`congelado-2026-11-01`** (`git tag congelado-2026-11-01`; `git push --tags`) e o SHA anotado aqui.

#### Aprovação
Cada pessoa comenta "aprovo o G9" (pode ser pelo celular). Com as três aprovações (ou duas e nenhuma objeção em 2 horas), a Pessoa C muda `G9_holdout.status: aprovado` (com `aprovado_por`, `data: '2026-11-01'`) e roda o #2 na manhã de 02/11.

### ④ Pronto quando

- yaml: `configs/supervised.yaml` :: `gates.G9_holdout.status` != `pendente` | O G9 foi aprovado (ou já executado) no supervised.yaml.
- yaml: `configs/supervised.yaml` :: `gates.G8_limiar.status` = `aprovado` | Pré-requisito: o G8 está aprovado.
- yaml: `configs/supervised.yaml` :: `gates.G7_calibracao.status` = `aprovado` | Pré-requisito: o G7 está aprovado.
- yaml: `configs/supervised.yaml` :: `gates.G6_finalistas_tuning.status` = `aprovado` | Pré-requisito: o G6 está aprovado.
- yaml: `configs/supervised.yaml` :: `gates.G1_definicao_alvo_features.status` = `aprovado` | Pré-requisito: o G1 está aprovado.
- yaml: `configs/supervised.yaml` :: `gates.G2_janela_temporal.status` = `aprovado` | Pré-requisito: o G2 está aprovado.
- manual: | O checklist do G9 está todo marcado neste card, o commit de congelamento tem a tag congelado-2026-11-01 com o SHA anotado, e as três pessoas comentaram "aprovo o G9" (ou duas, sem objeção em 2 horas).

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

## #126 · Execução limpa da cadeia final e pacote de reprodução

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M6
- data ideal: 04/11
- responsável: Pessoa A (README e conferência) + Pessoa B + Pessoa C (cada um executa os próprios notebooks)
- pessoas: A, B, C
- fonte: tools/executar_cadeia.py (do Plano de Performance)
- depende de: #2, #146
- tags: Memória/Desempenho, Ambiente, Testes
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1
- novo: sim
- professores: não

### ① Para entender

No dia do congelamento, a prova de reprodutibilidade é: cada notebook do caminho final roda do zero, em kernel novo, sem depender de variáveis de outro. O executor faz isso e grava uma tabela com duração e pico de memória.

| Ganho | Por quê |
|---|---|
| Memória volta ao Windows entre notebooks | cada notebook é um processo |
| Tabela de performance para o relatório | pilar Performance |
| Falha aparece no notebook certo | para na primeira erro |

### ② Problema

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: acontece **na manhã de 04/11, depois do #146** (renomeação e limpeza), e vale como a prova de reprodução do pacote. O C_16 **não** roda de novo (o teste abre uma vez): as saídas salvas em 02/11 ficam. Substitui a execução de 01/11 do plano anterior. A tag passa a ser `entrega-2026-11-04`.

Hoje a cadeia é rodada à mão, no mesmo kernel, e a memória se acumula.

### ③ O que fazer

> [!decisão] Replanejamento de 31/10
> Qualquer pessoa precisa conseguir rodar os notebooks do início ao fim. Cada pessoa executa **os próprios** notebooks em kernel limpo, já com os nomes finais, com a ferramenta do #145, e salva com as saídas.

**Dono:** Pessoa A (README e conferência) + Pessoa B + Pessoa C · **Prazo:** 04/11 (quarta), 8h às 12h · **Esforço estimado:** A ≈ 30 min · B ≈ 30 min · C ≈ 30 min (mais o tempo de máquina) · **Começa quando:** #2 e #146 (depois do `git pull` da renomeação)

#### Execução (cada pessoa, kernel limpo, nesta ordem)
1. Ambiente: `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` (versões fixas: numpy 2.5.4, pandas 3.0.6, scikit-learn 1.9.1 e outras) e confira `.\.venv\Scripts\python.exe -m pytest -m "not slow" -q`.
2. `.\.venv\Scripts\python.exe tools/medir_notebook.py notebooks/<nome>.ipynb --salvar-no-lugar` para cada notebook:
   - **A:** 03 e 04 (inclui âncora e fator de risco);
   - **B:** 05, 06, 07;
   - **C:** 01, 02, 08, 09, 10 e 11. O **12 não roda de novo**.
3. Se algum notebook passar de 20 minutos ou de 6 GB, comente no #145 e siga (a Pessoa C avalia); não refaça a limpeza.
4. Commit por pessoa: `resultados: execucao limpa dos notebooks (B)`.

#### README (Pessoa A, 30 min)
5. Seção "Como reproduzir": versão do Python, `pip install -r requirements.txt`, download da tag `dados-v2`, ordem dos notebooks (01 a 12, com a observação de que o 12 foi executado uma única vez) e **tempo e memória de cada um** (de `outputs/final/performance_notebooks.csv`).
6. Árvore e tabela de notebooks com os **nomes novos**; remova os nomes antigos (`C1_smoke_test` a `C6_validacao_final`) e a citação do arquivo inexistente `dicionario_variaveis_v1_revisao.csv`; remova a seção de avisos gerada automaticamente em outubro.
7. Tag `entrega-2026-11-04` no commit final, depois do #147.

### ④ Pronto quando

- contem: `README.md` :: `Como reproduzir` | O README tem a seção "Como reproduzir" (versão do Python, pip install -r requirements.txt, download da tag dados-v2, ordem dos notebooks e tempos).
- nao-contem: `README.md` :: `C1_smoke_test` | O README não usa mais os nomes antigos dos notebooks (C1_smoke_test … C6_validacao_final).
- nao-contem: `README.md` :: `dicionario_variaveis_v1_revisao.csv` | O README não cita mais o arquivo inexistente dicionario_variaveis_v1_revisao.csv.
- manual: | Cada pessoa rodou os próprios notebooks em kernel limpo (A: 03, 04; B: 05, 06, 07; C: 01, 02, 08 a 11), com saídas salvas, e anotou tempo e memória; o 12 manteve as saídas de 02/11.

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
- responsável: Pessoa C (dentro do #2)
- pessoas: C
- fonte: src/data/supervised_artifact.py (manifesto); notebooks C_16
- depende de: #2
- tags: Código, Vazamento
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 0
- novo: não
- professores: não

### ① Para entender

O campo `test_opened` do manifesto fica sempre `false`, mesmo depois do C_16. O registro só existe no YAML.

### ② Problema

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: o código fica no C_16 (#148, passo 14); a conferência é feita no #2.

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
- responsável: Pessoa A (dentro do #133, Dados e Métodos)
- pessoas: A
- fonte: B_06 (achado); configs/supervised.yaml (contexto_incremental); src/features/engineering.py
- depende de: —
- tags: Dados/Coorte, Features
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 0
- novo: não
- professores: não

### ① Para entender

Há 55 fichas de 2019 e 24.284 de 2020 com vacina contra COVID = sim. O YAML usa o campo bruto, sem olhar a data da dose.

<div class="bars">
<div class="br"><span class="y">2019</span><div class="t"><div class="b " style="width:2.0%"></div></div><span class="v">55</span></div>
<div class="br"><span class="y">2020</span><div class="t"><div class="b red" style="width:97.1%"></div></div><span class="v">24.284</span></div>
</div>

### ② Problema

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: vira **uma frase** dentro do #133 (Dados e Métodos), sem esforço próprio.

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
- responsável: Pessoa A (dentro do #133, Dados e Métodos)
- pessoas: A
- fonte: Construção da coorte
- depende de: #135
- tags: Dados/Coorte
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 0
- novo: não
- professores: não

### ① Para entender

Pode ser reenvio da mesma ficha ou erro de digitação. A regra definitiva fica com o item 10.

### ② Problema

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: uma frase dentro do #133, sem esforço próprio.

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
- responsável: Pessoa A (dentro do #133, Dados e Métodos)
- pessoas: A
- fonte: Construção da coorte
- depende de: #135
- tags: Dados/Coorte
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 0
- novo: não
- professores: não

### ① Para entender

| Problema | Quantidade | Tratamento atual |
|---|---|---|
| Idade implausível (fora de 0–120) | 24 na coorte (38 na base) | idade vira vazio, registro mantido |
| Internação depois do fechamento da base | 17 | a decidir |
| Datas com ano fora da faixa | 260 (138 de vacina COVID) | viram vazio |
| Nascimento depois dos sintomas | 1 | excluir |

### ② Problema

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: uma frase e uma tabela de apêndice dentro do #133, sem esforço próprio.

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
- responsável: Pessoa A
- pessoas: A
- fonte: B_06_eda_temporal_clustering; construção da coorte
- depende de: —
- tags: Metodologia, Dados/Coorte, Documentação
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1
- novo: não
- professores: não

### ① Para entender

Falta a tabela da diferença entre `dt_notific` e `dt_interna`, que sustenta a escolha da âncora, e a comparação entre os casos excluídos por falta de desfecho e os incluídos.

<div class="kpi">
<div><b>97.786</b>excluídos por evolução não encerrada (waterfall A_03)</div>
<div><b>36.923</b>excluídos por óbito por outra causa ou ignorado</div>
</div>

### ② Problema

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: já existe o notebook `A6_ancora_e_selecao` que gera as duas tabelas; falta **rodar e conferir** (≈ 45 min). Os nomes dos arquivos são os do notebook (`ancora_notificacao_internacao.csv`); o critério ④ foi ajustado.

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que esta pendência está aberta
> A auditoria automática (27/10, 14:40) marcou "precisa revisão" por achados que não tratam deste item: a linha decorativa `=====` no cabeçalho de `src/protocolo/verificacoes.py` (lida como conflito de merge) e o `OneHotEncoder` denso do B_06, que roda numa amostra de 80 mil fichas e será substituído pelo #136 (detalhes no #94).
> Não existem `outputs/final/ancora_notificacao.csv` nem `excluidos_vs_incluidos.csv`.

Não foram produzidas a tabela da diferença entre `dt_notific` e `dt_interna`, que sustenta a escolha da internação como âncora, e a comparação entre casos excluídos por falta de desfecho e casos incluídos.

### ③ O que fazer

**Dono:** Pessoa A · **Prazo:** 01/11 (domingo), manhã · **Esforço estimado:** ≈ 45 min · **Começa quando:** imediatamente

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
- responsável: Pessoa A (dentro do #133)
- pessoas: A
- fonte: Plano_Unificado_SRAG_3_Pessoas_v2.docx
- depende de: —
- tags: Documentação, Partição
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 0
- novo: não
- professores: não

### ① Para entender

> [!ok] Decisão fechada em 18/10
> A coorte definitiva inicial será a seleção de features da coorte provisória. O treino principal usará exclusivamente 2019, 2023, 2024 e 2025. Haverá duas janelas de teste: (A) 2019, 2023, 2024 e 2025; (B) 2019 a 2025, incluindo 2020–2022. O ano de 2026 não participa do desenvolvimento nem dos testes principais e fica apenas como exploração opcional, depois de todo o restante concluído.

Os dois documentos falam em 2022–2025 com divisão temporal. O projeto executou 2019–2026 com sorteio estratificado. Quem ler os planos vai entender outro estudo.

### ② Problema

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: os documentos antigos (Plano v2, Orientação de 03/10) **não estão no repositório**, então não há aviso "HISTÓRICO" a colocar neles. Fica o parágrafo de trajetória no #133.

O plano v2 ainda descreve treino 2022–2023, validação 2024, teste 2025, 2026 fora e âncora temporal com 2026 excluído. Isso contradiz a decisão vigente: período 2019–2026 com divisão aleatória 70/15/15 estratificada e coorte provisória.

### ③ O que fazer

**Pessoa A, dentro do #133 (01/11):** parágrafo de trajetória em Métodos: "o desenho inicial previa desenvolvimento em 2022–2024 e avaliação em 2025; foi substituído por treino em 2019 e 2023–2025 com duas janelas de teste porque …" (use o `decisoes.md` §28 e §29.25). Mostrar a evolução conta a favor.

### ④ Pronto quando

- manual: | O Plano Unificado v2 e a Orientação de 03/10 têm o aviso "HISTÓRICO" no topo (se estiverem no repositório ou na pasta da equipe) e o relatório tem o parágrafo de trajetória do desenho.

## #70 · Dicionário de variáveis desatualizado e com arquivo fantasma

- prioridade: P2
- situação: aberta
- estratégia: documentar
- marco: M4
- data ideal: 31/10
- responsável: Pessoa A (dona; revisão cruzada sem edição concorrente)
- pessoas: A
- fonte: configs/dicionario_variaveis_v1.csv; docs/decisoes.md §25
- depende de: #144
- tags: Documentação, Dados/Coorte
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1
- novo: não
- professores: não

### ① Para entender

O dicionário ainda põe saturação no "Modelo A" e tem 36 colunas com revisão pendente. O README e o `decisoes.md` citam `dicionario_variaveis_v1_revisao.csv`, que não existe (alertas A18 e A20).

### ② Problema

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: continua junto com o #40 (tabela de variáveis finais). A frase do README com o arquivo inexistente é corrigida **no #146** (limpeza do README) e no #126; aqui basta o CSV e o dicionário.

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que esta pendência está aberta
> A auditoria automática do painel (27/10, 14:40) marcou este item como resolvido com base em commits de 10 e 11/10, todos anteriores às revisões de 24 e 26/10 e sem relação com a entrega descrita aqui. Isso acontece por um defeito do painel: a cada auditoria, um commit antigo ainda não rejeitado reabre a sugestão (detalhes no #94).
> O dicionário (CSV) não é reproduzido no snapshot, então não foi possível confirmar os papéis; a versão de 27/10 ainda tinha saturação como `modelo_a_nucleo`. O `README.md` (linha ~425) continua citando `configs/dicionario_variaveis_v1_revisao.csv`, arquivo que não existe; `docs/decisoes.md` não o cita mais. Não existe `outputs/final/variaveis_finais.csv`. Fica em andamento.

O dicionário mantém a classificação original (saturação no "Modelo A") e tem 36 colunas com pontos de revisão sem decisão. A seção 25 das decisões diz que o dicionário é o único arquivo editável, mas a introdução das decisões cita um segundo arquivo, `dicionario_variaveis_v1_revisao.csv`.

### ③ O que fazer

> [!decisão] Replanejamento de 31/10
> Junta o #40 (tabela de variáveis finais) e o #70 (dicionário). Um script curto, um CSV.

**Dono:** Pessoa A · **Prazo:** 31/10 (sábado), tarde · **Esforço estimado:** ≈ 1 h · **Começa quando:** #144

1. No `configs/dicionario_variaveis_v1.csv`, corrija só a coluna de **papel** das variáveis usadas (as 31 principais, as 4 de contexto, as 2 de gravidade e `fator_risc`) para bater com o YAML. As demais ficam como estão. Inclua `fator_risc` (existe na coorte e não estava no dicionário).
2. Gere `outputs/final/variaveis_finais.csv` com um script de poucas linhas (`scripts/variaveis_finais.py`) que lê as listas do `supervised.yaml` e cruza com o dicionário: nome amigável, grupo, tipo, % em branco mínima e máxima **por ano de desenvolvimento** (2019, 2023, 2024, 2025; os valores do dicionário cobrem 2019–2026 e confundem). Esta tabela é a do relatório (seção 3) e fecha o #40.
3. Se a decisão do #140 mudou variáveis, gere de novo depois.
4. Commit: `docs: dicionario e tabela de variaveis finais [done:#70] [done:#40]`.

### ④ Pronto quando

- existe: `outputs/final/variaveis_finais.csv` | A tabela de variáveis finais, gerada por script a partir do supervised.yaml e do dicionário, está em outputs/final/variaveis_finais.csv.
- manual: | No configs/dicionario_variaveis_v1.csv, o papel das variáveis usadas (31 principais, 4 de contexto, 2 de gravidade e fator_risc) bate com o supervised.yaml.

## #71 · Cuidados de redação no relatório

- prioridade: P2
- situação: aberta
- estratégia: documentar
- marco: M6
- data ideal: 03/11
- responsável: Pessoa A (dona; revisão cruzada sem edição concorrente)
- pessoas: A
- fonte: Projeto (relatório)
- depende de: #55, #91
- tags: Documentação, Metodologia
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1
- novo: não
- professores: não

### ① Para entender

- A unidade é a **notificação**, não a pessoa.
- As associações são **preditivas**, não causais.
- 2026 é ano **parcial**.
- O modelo foi avaliado com **sorteio**; a validação em anos futuros é complementar.
- A lista de variáveis importantes (item 91) é de associação, não de causa.

### ② Problema

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: a verificação de redação é feita no **relatório em 03/11** e nos **slides em 04/11** (dentro do #134).

Pontos de redação: a unidade de análise é a notificação, não a pessoa; as associações são preditivas, não causais; 2026 é ano parcial; o modelo, avaliado com divisão aleatória, não foi validado em anos futuros.

### ③ O que fazer

**Dono:** Pessoa A · **Prazo:** 03/11 (terça), à noite · **Esforço estimado:** ≈ 1 h · **Começa quando:** #55 e #91

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

## #133 · Relatório final: esqueleto, seções e rastreabilidade de cada número

- prioridade: P1
- situação: aberta
- estratégia: documentar
- marco: M6
- data ideal: 04/11
- responsável: Pessoa A (dona) + Pessoa B (EDA, não supervisionado e Introdução) + Pessoa C (conferência técnica)
- pessoas: A, B, C
- fonte: Revisão de 24/10; base de conhecimento v7 (contratos assíncronos e definição de pronto)
- depende de: #97
- tags: Documentação, Metodologia
- pilar: Valor científico-acadêmico
- carga: 9
- novo: sim
- professores: não

### ① Para entender

O relatório é a entrega avaliada. Ele precisa existir em paralelo à modelagem, com lugares marcados para os números que só chegam em 30/10, e não começar em 31/10.

### ② Problema

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: o relatório é a **entrega de 04/11** e passa a ter um calendário por dia (Dados e Métodos em 01/11, Resultados em 02/11, fechamento em 03/11 e conferência final em 04/11). O esforço baixou de ≈ 17 h para ≈ 10 h (A 6 h 30 · B 2 h · C 30 min): cortaram-se a seção de literatura longa e o apêndice de sensibilidades. As frases de Métodos e Limitações dos cards #45, #46, #47, #58, #69, #89 e #98 entram aqui (lista abaixo).

Nenhum item do painel cobria a redação. Com a Pessoa C no caminho crítico e a exploração concentrada até 29/10, sem um dono e um esqueleto agora o texto vira gargalo em 31/10–02/11.

### ③ O que fazer

> [!decisão] Replanejamento de 31/10
> O texto vem **das tabelas e dos cards**, nunca de memória: cada número aponta para um arquivo de `outputs/final/` ou para um manifesto. Número sem origem sai do texto.

**Dono:** Pessoa A (dona) + Pessoa B (EDA, não supervisionado e Introdução) + Pessoa C (conferência técnica) · **Prazo:** Dados e Métodos 01/11 · Resultados 02/11 (tarde) · Discussão, Limitações e Conclusão 03/11 · conferência final 04/11 (manhã) · **Esforço estimado:** A ≈ 6 h 30 · B ≈ 2 h · C ≈ 30 min · **Começa quando:** #97 (formato); a seção Resultados espera o #119

#### Roteiro (TRIPOD adaptado) e de onde vem cada parte
| Seção | Conteúdo | Fonte | Quem · quando |
|---|---|---|---|
| 1. Introdução | Pergunta, relevância para a saúde pública, lacuna | #112 | B · 03/11 |
| 2. Dados e coorte | SIVEP-Gripe (`dados-v2`); funil 4.666.910 → 3.884.728; regras `D_COORTE_001` a `007`; âncora; qualidade (2019, viés de documentação, vacinação) | `decisoes.md` §29.1, #56, #45, #46, #47 | A · 01/11 |
| 3. Desfecho e variáveis | Alvo `evolucao` 1 × 2; 31 variáveis; o que ficou de fora e por quê (vazamento, gravidade) | #70, `variaveis_finais.csv` | A · 01/11 |
| 4. Desenho temporal e partição | Seis blocos, grupos, estratificação, invariantes; os três papéis da validação (#58) | §28, §29.4, #135 | A · 01/11 |
| 5. Representação | One-hot e escala na logística; categóricas nativas no boosting; AUSENTE explícito | §29.24, #136 | A · 01/11 |
| 6. Modelos e ajuste | Nulo, logística (L2 e rodada L1), boosting; busca; peso de classe | #1, #5, `tuning_val_tune.csv` | A · 02/11 |
| 7. Calibração e limiar | Método, regra de corte (sens. ≥ 0,80), corte global e por região | #79, #80 | A · 02/11 |
| 8. Resultados | Teste A, Teste B, 2020–2022, por ano; ablações; IC | #119, #54 | A · 02/11 |
| 9. O que pesa no risco | Bruto × ajustado; permutação | #91 | B · 02/11 |
| 10. Não supervisionado | Representação antiga × nova; perfis estatísticos; "agrupam idade e preenchimento, não perfis clínicos" | #136, #137, #60 | B · 03/11 |
| 11. Discussão | Mudança de período, sintomas de 2019, viés de documentação, equidade regional, subgrupos | #50, #52, #55, #110 | A · 03/11 |
| 12. Limitações e conclusão | O que não foi feito e por quê (lista abaixo) | #71 | A · 03/11 |
| Reprodutibilidade e desempenho | Como reproduzir; tempos e memória | #126, #145 | A · 03/11 |

#### Frases obrigatórias (vêm dos cards absorvidos; a Pessoa A as escreve em Dados e Métodos ou Limitações)
- **Âncora (#56):** a data de internação é a âncora; a notificação costuma vir depois. Citar a mediana e o intervalo interquartil (`ancora_notificacao_internacao.csv`) e os excluídos × incluídos (`excluidos_vs_incluidos.csv`).
- **Vacina (#45):** 55 fichas de 2019 e 24.284 de 2020 marcam vacina contra COVID-19 como "sim" antes de a vacina existir; vacinação fica fora do modelo principal (só contexto). A regra de dose anterior à internação fica como trabalho futuro (#84).
- **Duplicados (#46):** a base bruta tem 58 linhas repetindo 29 números de notificação; na coorte definitiva a regra de grupo mantém a mesma ficha no mesmo bloco (`manifesto_particao.json`).
- **Idades e datas impossíveis (#47):** "idades implausíveis foram tratadas como ausentes e imputadas pela mediana do treino, n = …" (contagem de `idade_anos` vazia por bloco, do #135) e as contagens de datas fora do período numa tabela do apêndice.
- **Três papéis da validação (#58):** `val_tune` escolhe hiperparâmetros, `val_cal` calibra e escolhe o corte, `val_meas` só mede; nenhuma fatia escolhe e mede ao mesmo tempo.
- **Trajetória do desenho (#69):** o desenho inicial previa desenvolvimento em 2022–2024 e avaliação em 2025; foi substituído por treino em 2019 e 2023–2025 com duas janelas de teste, para não treinar com 2020–2022 (anos de composição atípica). Mostrar a evolução conta a favor.
- **PR-AUC e prevalência (#89):** "a PR-AUC depende da prevalência; por isso todas as comparações entre períodos usam também PR-AUC ÷ prevalência e ROC-AUC". Exemplo da própria coorte: a PR-AUC da logística caiu de 0,44 (22% de óbitos) para 0,30 (8,4%) e, medida contra o acaso, subiu de 2,0× para 3,6×.
- **Coorte provisória (#98):** a seleção de variáveis foi feita numa coorte provisória, congelada antes da definitiva; a definitiva é subconjunto exato dela (30.408 linhas a menos, nenhuma nova, alvo idêntico).
- **Sazonalidade (#13):** `sin_semana` e `cos_semana` são calculadas, mas não entram no modelo principal; ablação fica como trabalho futuro.

#### Limitações obrigatórias (uma frase cada)
2026 é ano parcial e só exploratório; unidade de análise é a **notificação**; associações são **preditivas**, não causais; sem validação clínica ou externa; ausência de registro ≠ ausência da condição; heterogeneidade regional pode refletir acesso, capacidade e registro; sem município de residência; só SIVEP-Gripe; o Teste B mistura prevalências diferentes (compare PR-AUC ÷ prevalência).

#### Passo a passo
1. **Hoje (31/10, 10 min):** a Pessoa A copia o roteiro para o documento no formato do #97, com marcadores `[NÚMERO: arquivo.csv]` onde entram números. Sem esqueleto não há onde colar.
2. **01/11:** seções 2 a 5 (não dependem do teste). Planilha de rastreabilidade (`rastreabilidade_numeros.csv`: número, texto onde aparece, arquivo, coluna): número sem origem sai do texto.
3. **02/11 (tarde):** seções 6 a 8 a partir de `outputs/final/`, **colando tabelas dos arquivos** (nunca redigitando). Pessoa B: seção 9 (#91).
4. **03/11:** Pessoa B: seções 1 e 10 (#112, #136, #137); Pessoa A: 11, 12 e Reprodutibilidade; revisão de linguagem pela lista do #71.
5. **04/11 (manhã):** a Pessoa C confere todos os números técnicos contra a planilha; a Pessoa B lê o texto inteiro como leitor de fora; versão final em PDF e no formato pedido.

**Pronto quando:** documento completo no formato pedido, sem número órfão e com a conferência da Pessoa C.

### ④ Pronto quando

- manual: | O relatório está completo no formato pedido (#97), com todas as seções do roteiro deste card, as frases obrigatórias e as limitações.
- manual: | A planilha de rastreabilidade liga cada número do texto a um arquivo de outputs/final/ ou manifesto, sem número órfão, e a Pessoa C conferiu os números técnicos em 04/11.

## #134 · Apresentação e defesa: roteiro, slides e perguntas difíceis

- prioridade: P2
- situação: aberta
- estratégia: documentar
- marco: M7
- data ideal: 04/11
- responsável: Pessoa B (roteiro, slides e respostas) + Pessoa A (números) + Pessoa C (revisão técnica)
- pessoas: B, A, C
- fonte: Revisão de 24/10
- depende de: #133
- tags: Documentação
- pilar: Valor científico-acadêmico
- carga: 3
- novo: sim
- professores: não

### ① Para entender

A apresentação precisa contar a mesma história do relatório em poucos minutos, com os números finais e respostas preparadas para as perguntas previsíveis da banca.

### ② Problema

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: a apresentação é **construída em 04/11**, depois do relatório, e **entregue em 05/11**. O ensaio (30 min, as três pessoas) é na manhã de 05/11. Esforço: B ≈ 2 h 30 · A ≈ 15 min · C ≈ 15 min.

Não havia item para a apresentação. As perguntas difíceis (vazamento, por que excluir 2020–2022 do treino, por que PR-AUC, calibração, geografia) precisam de resposta curta e ensaiada.

### ③ O que fazer

> [!decisão] Replanejamento de 31/10
> 10 a 12 slides, uma ideia por slide, **os mesmos números do relatório** (copiados da planilha de rastreabilidade). Colegas que **não conhecem** o projeto (orientação de 24/10): linguagem simples.

**Dono:** Pessoa B (roteiro, slides e respostas) + Pessoa A (números) + Pessoa C (revisão técnica) · **Prazo:** 04/11 (quarta), tarde e noite · entrega em 05/11 · **Esforço estimado:** B ≈ 2 h 30 · A ≈ 15 min · C ≈ 15 min · **Começa quando:** #133 (relatório fechado)

#### Roteiro
1. O problema: SRAG, mortalidade, por que prever **na admissão**.
2. Os dados: SIVEP-Gripe e o funil 4,67 mi → 3,88 mi.
3. Desenho temporal: figura dos seis blocos e por que 2020–2022 não entram no treino.
4. Variáveis e o cuidado com vazamento (saturação fora do principal).
5. Achado de dados: os três sintomas de 2019 e a decisão tomada (#140).
6. Modelos: por que o finalista (logística × boosting; PR-AUC em `val_tune`).
7. Calibração e corte: o que é "30% de risco" e por que 80% de sensibilidade.
8. Teste A (resultado principal) com IC.
9. Teste B e 2020–2022: robustez a outro período (PR-AUC ÷ prevalência).
10. O que pesa no risco: bruto × ajustado.
11. Não supervisionado: representação antiga × nova e o que diferencia os grupos.
12. Equidade regional, limitações e conclusão.

#### Perguntas difíceis (a Pessoa B redige as respostas em 04/11, uma a duas frases; a Pessoa C revisa as técnicas)
Por que não treinar com 2020–2022? Como garantem que não há vazamento (grupos, blocos, teste aberto uma vez)? Por que PR-AUC e não acurácia? O que muda com a calibração? Por que esse corte (sensibilidade ≥ 0,80)? Por que a geografia não é variável do modelo? Para que servem os agrupamentos? O modelo serve para uso clínico? (**não**: demonstração acadêmica retrospectiva.)

#### Regras
Aplique a lista de verificação do #71 aos slides. Todo número do slide está no relatório. Ensaio cronometrado (≤ 30 min) com as três pessoas em 05/11, de manhã.

### ④ Pronto quando

- manual: | Os slides (10 a 12) seguem o roteiro deste card com os mesmos números do relatório, as respostas às perguntas difíceis estão escritas e revisadas pela Pessoa C, e o ensaio cronometrado com as três pessoas foi feito em 05/11.

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
- responsável: Pessoa B (dona; contingência: Pessoa C)
- pessoas: B
- fonte: Orientação de 24/10 (cobrança de one-hot); base de conhecimento v9 §6.3 e §8; B_06 de 24/10
- depende de: #141, #142
- tags: Não supervisionado, Features, Código, Metodologia
- pilar: Valor científico-acadêmico + Performance
- carga: 3
- novo: sim
- professores: sim
- arquivos: src/features/normalization.py, tests/test_features.py

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

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: continua obrigatório (os professores cobraram o one-hot e o dendrograma), mas **deixa de bloquear o #140 e o ajuste fino**: o não supervisionado só alimenta o relatório e a apresentação. Escopo reduzido de ≈ 5 h 30 para ≈ 3 h (sem comparação com a representação antiga além do ARI e sem sensibilidade extra).

A representação usada no clustering misturou "em branco" com "não" e deu peso desigual às variáveis. Os professores cobraram testes com one-hot. Sem refazer, a parte de Não Supervisionado fica vulnerável na banca.

### ③ O que fazer

> [!decisão] Replanejamento de 31/10
> A representação one-hot vem **antes** de qualquer agrupamento (as análises dependem dela). O resultado **não muda o modelo supervisionado**: se mostrar algo novo, vira parágrafo do relatório.

**Dono:** Pessoa B · **Prazo:** 31/10 (sábado), manhã e início da tarde · **Esforço estimado:** ≈ 3 h · **Revisão:** Pessoa C (só a função, 10 min) · **Começa quando:** #141 e #142 (já concluídos)

#### Etapa 1 · representação (≈ 1 h)
1. Em `src/features/normalization.py`, `construir_preprocessador_clustering(numericas, categoricas)`: numéricas → mediana + `StandardScaler`; categóricas e clínicas → vazio vira `AUSENTE` (reaproveite o normalizador de `src/models/pipeline.py`) → `OneHotEncoder(handle_unknown="ignore", dtype=np.float32)` (saída **esparsa**) → peso `1/√k` por variável (k = número de categorias da variável). Sem imputação pela moda e sem indicadores de vazio.
2. Teste em `tests/test_features.py` com 8 linhas inventadas: vazio vira a coluna `AUSENTE`; o número de colunas é a soma das categorias; saída esparsa `float32`.

#### Etapa 2 · agrupamento (≈ 2 h)
3. Amostra de **80 mil fichas** do `train_ref` (leia `train_ref` com `load_supervised_artifact(..., partitions=("train_ref",))`), estratificada por ano × desfecho, `random_state=42`. Nunca converta a matriz esparsa inteira para densa.
4. `TruncatedSVD` até ≈ 90% da variância (fixe `n_components=40` se a variância acumulada passar de 90% antes).
5. **K-Means:** `MiniBatchKMeans`, k de 2 a 6; silhueta (em 10 mil fichas da amostra) e ARI entre 3 sementes.
6. **HCA:** Ward em subamostra de **15 mil** (o custo cresce com o quadrado). Dendrograma truncado (`scipy.cluster.hierarchy.dendrogram`, `truncate_mode="lastp"`, `p=30`); corte no **maior salto de distância** entre fusões que deixe mais de 2 grupos (normalmente 3 a 6). Registre o k e a silhueta.
7. Na mesma amostra, rode a representação antiga do B_06 e calcule o ARI entre as soluções antiga e nova (um número).
8. Grave `outputs/tables/ns_onehot_metricas.csv`, `ns_onehot_rotulos.parquet` (`id_registro`, rótulo K-Means, rótulo HCA) e a figura do dendrograma.
9. **Perfil dos grupos (fecha a parte pendente do #137):** com `perfil_estatistico` (de `src/evaluation/cluster_profile.py`; se o arquivo ainda não estiver no Git, peça à Pessoa A o push antes), gere `outputs/final/perfil_clusters_kmeans.csv` e `outputs/final/perfil_clusters_hca.csv` (qui-quadrado e V de Cramér para as categóricas; ANOVA/Kruskal-Wallis e η² para as numéricas). Escreva duas frases: os grupos separam **idade e preenchimento**, não perfis clínicos (#60).
10. Execute com `tools/medir_notebook.py` (#145); se passar de 6 GB, reduza a amostra para 50 mil e registre.
11. Commit: `feat: agrupamento com one-hot dos quatro estados [done:#136]`.

#### Pronto quando
Função testada, rótulos das duas técnicas e o dendrograma com o corte justificado.

### ④ Pronto quando

- define: `src/features/normalization.py` :: `construir_preprocessador_clustering` | A função construir_preprocessador_clustering existe em src/features/normalization.py: numéricas com mediana e padronização, categóricas com AUSENTE explícito, one-hot esparso em float32 e peso 1/√k por variável.
- contem: `tests/test_features.py` :: `construir_preprocessador_clustering` | Há teste com linhas inventadas confirmando que vazio vira a coluna AUSENTE e que o número de colunas é a soma das categorias.
- teste: `tests/test_features.py` | Os testes de features passam.
- existe: `outputs/tables/ns_onehot_metricas.csv` | As métricas do agrupamento (K-Means k = 2 a 6, HCA e ARI antiga × nova) estão em outputs/tables/ns_onehot_metricas.csv.
- existe: `outputs/tables/ns_onehot_rotulos.parquet` | Os rótulos K-Means e HCA por id_registro estão em outputs/tables/ns_onehot_rotulos.parquet, prontos para o #137.

## #137 · Perfil estatístico dos grupos: qui-quadrado e ANOVA (e óbito × cura só no treino)

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M3
- data ideal: 31/10
- responsável: Pessoa A (dona; revisão cruzada sem edição concorrente)
- pessoas: A
- fonte: Orientação de 24/10 (recomendação de ANOVA e qui-quadrado); base de conhecimento v9 §8.3
- depende de: #136, #142
- tags: Não supervisionado, Estatística, Código
- pilar: Valor científico-acadêmico
- carga: 4
- novo: sim
- professores: sim
- arquivos: src/evaluation/cluster_profile.py, tests/test_cluster_profile.py

### ① Para entender

Depois de formar grupos, é preciso dizer **em que eles diferem**. O professor sugeriu testes estatísticos clássicos.

| Teste | Para que tipo de variável | Pergunta que responde | Tamanho do efeito (o que ler) |
|---|---|---|---|
| **Qui-quadrado** | Qualitativa (sexo, sintoma sim/não/ignorado/branco) | A distribuição da variável é a mesma em todos os grupos? | **V de Cramér**: 0 = nenhuma associação; 0,1 pequena; 0,3 média; 0,5 grande |
| **ANOVA** | Numérica (idade, dias até internar) | A média é a mesma em todos os grupos? | **eta²**: % da variação explicada pelo grupo; 0,01 pequeno; 0,06 médio; 0,14 grande |
| **Kruskal-Wallis** | Numérica com distribuição torta | Versão sem suposição de normalidade da ANOVA (compara medianas e postos) | Mesmo eta² ou épsilon² |

> [!atenção] Com milhares de linhas, quase tudo é "significativo"
> Com 80 mil fichas, até diferenças minúsculas dão p < 0,001. Por isso o que se lê é o **tamanho do efeito** (V de Cramér, eta²), não o p. Também se corrige o p para muitos testes (Benjamini-Hochberg).

A mesma função serve para comparar **óbito × cura** no treino, o que substitui as tabelas de desfecho do B_06, que usaram a coorte inteira (#51).

### ② Problema

Os grupos do agrupamento foram descritos só com médias e figuras, sem teste do que realmente difere entre eles. E as tabelas de óbito × cura do B_06 usaram a coorte inteira, incluindo casos que hoje são teste.

### ③ O que fazer

> [!decisão] Replanejamento de 27/10: exploração completa antes do treino
> Tudo o que pode mudar variáveis, representação, alvo ou leitura do modelo roda **antes do ajuste fino (G6)**: primeiro a exploração sem modelo, depois o diagnóstico com o piloto padrão no `val_tune`, depois o ponto de decisão (#140, 30/10, manhã). Só então ajuste, calibração, limiar e teste.

**Dono:** Pessoa A · **Prazo:** função e uso 1 em 28/10 (quarta, tarde); uso 2 (clusters) em 29/10 (quinta) · **Esforço estimado:** ≈ 4 h · **Revisão:** Pessoa C (função) · Pessoa B (leitura, 31/10)

#### Passo a passo
1. Crie `src/evaluation/cluster_profile.py` com `perfil_estatistico(df, coluna_grupo, numericas, categoricas, min_esperado=5) -> pd.DataFrame`. Uma linha por variável: `variavel`, `tipo`, `teste`, `estatistica`, `p`, `p_ajustado` (Benjamini-Hochberg), `efeito` (V de Cramér ou eta²), `leitura` (pequeno, médio, grande), resumo por grupo (proporções para qualitativas; média e mediana para numéricas) e `observacao`.
2. Use `scipy.stats.chi2_contingency` (sobre `pd.crosstab`), `scipy.stats.f_oneway` e `scipy.stats.kruskal`. V de Cramér = √(χ² ÷ (n × (min(linhas, colunas) − 1))). eta² = soma de quadrados entre grupos ÷ soma total.
3. Categorias com esperado menor que 5: juntar em "outras" ou sinalizar em `observacao`. Vazio é categoria própria (`AUSENTE`), nunca descartado.
4. Testes em `tests/test_cluster_profile.py`: variável independente do grupo → V ≈ 0; variável igual ao grupo → V ≈ 1; numérica com médias muito diferentes → eta² alto.
5. **Uso 1 (28/10): óbito × cura no `train_ref`** (filtre por `partitions_master.parquet` do #142). Complementa o #51 com tamanho de efeito. Salve `outputs/final/perfil_desfecho_train_ref.csv`. Comente no #140 as cinco variáveis com maior efeito e qualquer resultado estranho (efeito enorme numa variável sem sentido clínico pode ser erro de dado).
6. **Uso 2 (29/10): clusters** com os rótulos do #136 (antiga e nova representação). Salve `outputs/final/perfil_clusters_*.csv` e comente no #140.
7. Ordene cada tabela pelo efeito e escreva três frases por uso.

#### Pronto quando
Função testada no `src` e os CSVs dos dois usos gerados, com os comentários no #140.

### ④ Pronto quando

- define: `src/evaluation/cluster_profile.py` :: `perfil_estatistico` | A função perfil_estatistico existe em src/evaluation/cluster_profile.py, com qui-quadrado, ANOVA e Kruskal-Wallis, p ajustado (Benjamini-Hochberg) e tamanho do efeito (V de Cramér ou eta²).
- teste: `tests/test_cluster_profile.py` | Os testes do perfil estatístico passam (variável independente → V ≈ 0; variável igual ao grupo → V ≈ 1; médias muito diferentes → eta² alto).
- existe: `outputs/final/perfil_desfecho_train_ref.csv` | O perfil óbito × cura no train_ref está em outputs/final/perfil_desfecho_train_ref.csv.
- manual: | Os perfis dos clusters (outputs/final/perfil_clusters_*.csv) foram gerados e os comentários dos dois usos estão no #140.

## #112 · Atualizar a revisão bibliográfica com busca científica dirigida

- prioridade: P2
- situação: aberta
- estratégia: desenvolver
- marco: M6
- data ideal: 01/11
- responsável: Pessoa B (busca e matriz) · conferência de citações: Pessoa A (dentro do #133)
- pessoas: B
- fonte: orientação de 17/10
- depende de: —
- tags: Documentação, Literatura
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1
- novo: sim
- professores: não

### ① Para entender

> [!decisão] Sem dependência de ferramenta específica
> O resultado esperado é uma revisão curta e verificável; MCP e Consensus são meios opcionais. A busca precisa sustentar a transportabilidade entre períodos, a calibração, o uso de SIVEP-Gripe e a heterogeneidade regional.

O professor indicou ferramentas e um artigo. Boa parte do valor acadêmico vem de situar o trabalho na literatura de predição de óbito por SRAG/COVID com SIVEP-Gripe.

### ② Problema

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: continua obrigatório (um trabalho sem trabalhos relacionados é a primeira crítica de qualquer banca), mas **curto**: 6 a 8 referências, uma linha cada. A conferência das citações é feita pela Pessoa A ao colar no #133.

O título do artigo indicado não ficou na transcrição.

### ③ O que fazer

> [!decisão] Replanejamento de 31/10
> Uma matriz pequena e **verificável**. Nenhuma referência entra sem título, ano, periódico e DOI conferidos na fonte.

**Dono:** Pessoa B · **Prazo:** 01/11 (domingo), tarde · **Esforço estimado:** ≈ 1 h 30 · **Revisão:** Pessoa A (confere as citações ao colar no relatório)

1. Pesquise (Google Scholar, PubMed, SciELO; o professor indicou ferramentas e um artigo; use-os) por estes quatro blocos, 1 a 2 referências por bloco:
   - **Predição de óbito por SRAG/COVID-19 com SIVEP-Gripe** (`SIVEP-Gripe mortality prediction`, `SRAG óbito aprendizado de máquina`);
   - **Relato de modelos de predição** (declaração TRIPOD; ponto de partida: Collins et al., 2015, *TRIPOD*, Annals of Internal Medicine; confirme título, ano e DOI antes de citar);
   - **Calibração de modelos clínicos** (ponto de partida: Van Calster et al., 2019, "Calibration: the Achilles heel of predictive analytics", BMC Medicine; confirme na fonte);
   - **Validação temporal e mudança de período** (`temporal validation clinical prediction model`, `dataset shift COVID-19`).
2. Matriz `docs/revisao_bibliografica.csv` (uma linha por referência): população, período, modelo, métrica, validação, limitação, DOI.
3. **Parágrafo de lacuna** para a Introdução (quatro frases): o que se sabe; que a maior parte dos trabalhos não separa treino e teste por **grupo** e por **período**; que raramente reporta calibração; o que este trabalho acrescenta.
4. Envie a matriz e o parágrafo à Pessoa A (ela os usa na seção 1 e na bibliografia do #133).

### ④ Pronto quando

- manual: | Seis a oito referências verificáveis estão na matriz (população, período, modelo, métrica, validação, limitação), as citações foram conferidas pela Pessoa A e o parágrafo de lacuna da Introdução está escrito.

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
- carga: 2
- novo: não
- professores: não

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

### ① Para entender

> [!atenção] Inclui checkpoint Git
> Antes de cada marco: `git status`, commit do estado verde e geração da referência v6. Isso impede que outra IA leia alterações locais sem saber o que foi testado.

A referência é o "manual vivo" que impede outra IA (ou outro integrante) de criar funções repetidas. Ela só vale até o momento em que foi gerada.

### ② Problema

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: a referência é regerada **uma vez, ao final (#147)**, e uma vez agora, depois do #144 (para que outras ferramentas leiam o código com a suíte verde).

> [!atenção] Revisão de 28/10 (commit `032a5b65`): por que esta pendência está aberta
> A auditoria automática do painel (27/10, 14:40) marcou este item como resolvido com base em commits de 10 e 11/10, todos anteriores às revisões de 24 e 26/10 e sem relação com a entrega descrita aqui. Isso acontece por um defeito do painel: a cada auditoria, um commit antigo ainda não rejeitado reabre a sugestão (detalhes no #94).
> É rotina contínua. A referência foi regerada em 27/10 (19:22) e 28/10 (02:45), mas o card só fecha em 02/11, depois do último marco.

Alterações feitas depois da geração não aparecem; buffers não salvos nunca aparecem.

### ③ O que fazer

**Pessoa A, 31/10 (depois do #144) e 04/11 (dentro do #147), ≈ 15 min cada:** `git pull`; `.\.venv\Scripts\python.exe tools/update_project_reference.py --run-tests --pytest-args="-m 'not slow'"`; confira: nenhum erro de leitura, testes passando, nenhum código ignorado pelo Git. Avise no card com a data e o commit.

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
- carga: 0
- novo: não
- professores: não

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
- data ideal: 31/10
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
- data ideal: 27/10
- responsável: Pessoa A (dados) + Pessoa C (ablação)
- pessoas: A, C
- fonte: configs/dicionario_variaveis_v1.csv
- depende de: —
- tags: Features, Vazamento, Metodologia, Dados/Coorte
- pilar: —
- carga: 2
- novo: não
- professores: não

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

- prioridade: P2
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
- carga: 1
- novo: não
- professores: não

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

- contem: `src/data/cohort_source.py` :: `provisional, final ou auto` | A mensagem de erro de SRAG_COHORT_KIND lista as três opções válidas, como o teste espera.
- teste: `tests/test_cohort_source.py::test_tipo_invalido_falha` | O teste confirma a mensagem para um tipo inválido.

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
- data ideal: 27/10
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
- responsável: Pessoa B (notebooks B e pastas) · Pessoa C (C_02 e função antiga) · Pessoa A (notebooks A)
- pessoas: B, C, A
- fonte: Referência de 27/10: relatório de atenção (A18, A74, A136) e inventário de notebooks
- depende de: #142, #144
- tags: Código, Git, Documentação
- pilar: Eficiência + Percepção acadêmica
- carga: 1
- novo: sim
- professores: não

### ① Para entender

Vários arquivos foram criados para uma fase que já passou (coorte provisória, divisão antiga, cópias de segurança, testes de ambiente). Eles não alimentam nada do caminho atual e, na banca, obrigariam a explicar "fizemos para usar depois". O Git guarda tudo no histórico: remover não perde trabalho.

**Fica:** tudo o que gera ou documenta a coorte definitiva, o artefato, os modelos e a avaliação; `src/protocolo/verificacoes.py` (usado pela paridade da coorte, pelo B_05 e pelo B_06); `src/evaluation/temporal.py` (já documentado como ferramenta de sensibilidade); os notebooks A_03 e A_04 (auditoria do protocolo da Pessoa A, que passam a rodar com o caminho corrigido no #73).

### ② Problema

> [!atenção] Replanejamento de 31/10 (entrega em 04/11)
> Replanejamento de 31/10: sobe para P1 e passa a ser a **primeira tarefa depois do #144**, porque todo o resto do plano (notebooks, limpeza, medição) fica mais simples com menos arquivos. Deixa de depender do #132. Os notebooks A6 e A_15 **não** são apagados aqui: viram seções do notebook 04 no #146.

Arquivos sem papel no projeto final confundem a banca e as IAs que trabalham no repositório.

### ③ O que fazer

> [!decisão] Replanejamento de 31/10
> Três commits pequenos, um por pessoa, no sábado de manhã, logo depois do #144. Só remoções e uma linha no README. Quem remove confere antes com busca no repositório que nada o chama.

**Dono:** Pessoas B, C e A · **Prazo:** 31/10 (sábado), 9h às 10h30 · **Esforço estimado:** B ≈ 30 min · C ≈ 30 min · A ≈ 15 min · **Começa quando:** #144 concluído (a suíte precisa estar verde para o passo 6 da Pessoa C)

#### Pessoa B (30 min)
1. `git pull`. Apague, se existirem, `notebooks/B/B_07_supervisionado_pilotos.antes_generalizacao_coorte.ipynb` (cópia de segurança), `notebooks/B/___provisorio_construcao_coorte_b.ipynb` (a coorte definitiva é gerada pelo construtor do `src`) e `notebooks/B/B_10_consolidacao_shortlist_transicao_coorte.ipynb` (ponte da fase provisória).
2. Apague `data/split.py` (cópia antiga de `src/data/split.py` dentro da pasta de dados) e a pasta `.scripts/` (`read_outputs.py` é igual a `tools/read_outputs.py`; os outros dois foram usos únicos).
3. Para a banca: o relatório precisa de **uma frase** dizendo que a seleção de variáveis foi feita numa coorte provisória, congelada antes da definitiva (#98); o notebook que a construiu sai do pacote porque a definitiva a substitui.
4. Commit: `chore: remove notebooks e scripts da fase provisoria`.

#### Pessoa C (30 min)
5. Apague `notebooks/C/C_02_smoke_test.ipynb` (os testes automáticos cobrem o ambiente; `build_logistic_pipeline` já exige scikit-learn ≥ 1.8).
6. Em `src/data/split.py`, remova `criar_particoes_agrupadas` (divisão 70/15/15 antiga, substituída por `criar_particao_mestra`) e os testes dela em `tests/test_split.py`. Antes, procure usos: `Get-ChildItem -Recurse -Include *.py,*.ipynb | Select-String "criar_particoes_agrupadas"`. Só pode restar a definição e os testes.
7. `.\.venv\Scripts\python.exe -m pytest -m "not slow" -q`. Commit: `chore: remove divisao antiga e smoke test`.
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
- responsável: Pessoa A (dona; revisão cruzada sem edição concorrente: Pessoa C)
- pessoas: A
- fonte: Diagnóstico de 31/10 (pytest rápido e auditoria do commit 1e02321)
- depende de: —
- tags: Código, Testes, Gate
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1
- novo: sim
- professores: não
- arquivos: src/protocolo/verificacoes.py, configs/supervised.yaml, tests/test_regras_pessoa_a.py, tests/test_config.py

### ① Para entender

A suíte rápida do projeto (`pytest -m "not slow"`) tinha 383 testes verdes em 30/10 às 11h. No commit `1e02321` (30/10, 17h) ela passa a ter **4 falhas**, e **quatro gates do YAML** estão com o valor errado. Os dois problemas vieram de edições do #73 (gates: 29/10, 21h21; função: 30/10, depois das 11h). São correções de poucos minutos, mas bloqueiam três frentes: a Pessoa C não consegue rodar a suíte para validar o #132, os notebooks A_03 e A_04 quebrariam ao exportar o dataset, e o checklist do G9 exige G1 e G2 aprovados.

| O que quebrou | Onde | Efeito |
|---|---|---|
| `_analytical_path` definida **duas vezes**; a segunda (edição do #73 de 30/10) tem o corpo `nome = ...` seguido de `...` e devolve `None` | `src/protocolo/verificacoes.py`, linhas 503 e 514 | `AttributeError: 'NoneType' object has no attribute 'with_name'` em `a3_split_aleatorio_cenario` (linha 814): 4 testes de `tests/test_regras_pessoa_a.py` falham |
| `status: responsavel` em vez de `aprovado` em G1, G2, G4 e G5 | `configs/supervised.yaml`, commit `de8113c` (29/10, 21h21, mensagem "73") | `gate_aprovado()` devolve falso; os cards #77, #85 e #120 voltam a ✗ no verificador |

> [!exemplo] Por que a segunda definição vence
> Em Python, quando duas funções têm o mesmo nome no mesmo arquivo, a **última** substitui a primeira. A versão boa (linha 503) existe, mas nunca é chamada.

### ② Problema

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

**Dono:** Pessoa A · **Revisão:** Pessoa C (5 min, só o diff) · **Prazo:** 31/10 (sábado), até as 9h · **Esforço estimado:** ≈ 1 h · **Começa quando:** imediatamente

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
10. Avise no #143 e no #132 que a suíte está verde: eles começam em seguida.

### ④ Pronto quando

- define: `src/protocolo/verificacoes.py` :: `_analytical_path` | A função _analytical_path existe em src/protocolo/verificacoes.py (uma única definição, devolvendo um Path).
- contem: `tests/test_regras_pessoa_a.py` :: `test_src_sem_funcoes_duplicadas` | Há teste que impede funções de topo repetidas em qualquer arquivo de src/.
- teste: `tests/test_regras_pessoa_a.py` | Os testes de test_regras_pessoa_a.py passam (as quatro falhas de 30/10 sumiram).
- teste: `tests/test_config.py::test_gates_historicos_aprovados` | O teste que confere G1, G2, G4 e G5 aprovados passa.
- yaml: `configs/supervised.yaml` :: `gates.G1_definicao_alvo_features.status` = `aprovado` | O G1 voltou a aprovado.
- yaml: `configs/supervised.yaml` :: `gates.G2_janela_temporal.status` = `aprovado` | O G2 voltou a aprovado.
- yaml: `configs/supervised.yaml` :: `gates.G4_baseline.status` = `aprovado` | O G4 voltou a aprovado.
- yaml: `configs/supervised.yaml` :: `gates.G5_pilotos.status` = `aprovado` | O G5 voltou a aprovado.
- manual: | O pytest rápido completo (-m "not slow") terminou com 0 falhas e a entrada de 31/10 está no docs/decisoes.md.

## #145 · Medir e reduzir tempo e pico de memória dos notebooks da entrega

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M6
- data ideal: 03/11
- responsável: Pessoa A (ferramenta) + Pessoa B (B_05, B_06, B_07) + Pessoa C (cadeia C e 00, 01)
- pessoas: A, B, C
- fonte: Diagnóstico de 31/10: inventário dos notebooks e manifesto do artefato
- depende de: #144
- tags: Performance, Notebook, Memória
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 2
- novo: sim
- professores: não
- arquivos: tools/medir_notebook.py, outputs/final/performance_notebooks.csv

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

Estado atual, medido no diagnóstico de 30/10 e na leitura dos notebooks:

- Só o C_11 usa `src.utils.performance.Monitor`; nenhum notebook chama `liberar(...)`.
- `B_06` lê colunas do Parquet em 54 pontos diferentes (`columns=`) em vez de ler uma vez e reaproveitar; `B_05` tem 42 células de código na coorte inteira.
- O C_13 pode rodar a busca com `MAX_TREINO_BUSCA = None` (treino inteiro, 556 mil linhas) e `max_iter` até 1.000.
- O C_16 reconstrói `treino`, `validacao` e `teste` como DataFrames completos (`df.loc[df[PARTICAO] == "teste"]`) e usa `ic_bootstrap`, que reordena o vetor inteiro a cada réplica.
- Não há tabela de tempo e memória para nenhum notebook: sem número não dá para dizer que a execução é sustentável.

### ③ O que fazer

> [!decisão] Replanejamento de 31/10
> Em vez de uma refatoração geral (#129, fica para depois da entrega), **medir uma vez, corrigir só o que passar da meta e registrar os números**. Cada pessoa mede os próprios notebooks no momento em que já precisaria executá-los.

**Dono:** Pessoa A (ferramenta, 31/10) · Pessoa B e Pessoa C (medição e correções) · **Prazo:** ferramenta em 31/10; medições de 31/10 a 03/11; tabela final em 03/11 · **Esforço estimado:** A ≈ 30 min · B ≈ 1 h · C ≈ 1 h · **Começa quando:** #144

#### 1. Ferramenta (Pessoa A, 31/10, 30 min)
Crie `tools/medir_notebook.py` com o código abaixo (testado: mede o pico somando o processo e os filhos, grava em `outputs/final/performance_notebooks.csv` e devolve código de saída 2 se passar do limite). Commit: `feat: mede tempo e pico de memoria dos notebooks`.

```python
r"""Executa um notebook em processo isolado e mede tempo e pico de memória.

Uso (na raiz do repositório):
    .\.venv\Scripts\python.exe tools/medir_notebook.py notebooks/09_baseline_e_logistica.ipynb
    .\.venv\Scripts\python.exe tools/medir_notebook.py notebooks/06_eda_temporal_e_agrupamento.ipynb --salvar-no-lugar

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

#### 2. Medir (cada pessoa, no momento em que executa o notebook)
Uso: `.\.venv\Scripts\python.exe tools/medir_notebook.py notebooks/C/C_12_baseline_logistica.ipynb`. Sem `--salvar-no-lugar` a cópia executada vai para `outputs/notebooks/` e o original não muda. Na execução **final** de cada notebook (#126), acrescente `--salvar-no-lugar`.

| Pessoa | Notebooks | Quando medir |
|---|---|---|
| B | B_05, B_06, B_07 | B_06 no #51 e no #136 (31/10); B_05 e B_07 em 03/11 |
| C | 00, 01, C_11, C_12, C_13, C_15 | C_11 a C_13 no #132 (31/10); C_15 no #79 (01/11); 00 e 01 em 03/11 |
| C | C_16 | **não roda de novo** (o teste abre uma vez): use o log do `Monitor` e a medição do #2 |
| A | A_03, A_04 | 03/11 |

#### 3. Corrigir o que passar da meta, nesta ordem (pare quando passar a ficar dentro)
1. **Ler menos:** `pd.read_parquet(caminho, columns=[...])` ou `load_supervised_artifact(..., partitions=(...), columns=[...])` só com o que a célula usa. Ler **uma vez** por notebook e reaproveitar (B_06: um `df` base na célula 2, derivados por filtro).
2. **Tipos menores:** inteiros pequenos para indicadores (`int8`), `float32` para contínuas, `category` para textos com poucos valores (`pd.read_parquet` já devolve `category` quando o arquivo foi gravado assim). Nunca `toarray()` ou `get_dummies` na coorte; usar `OneHotEncoder(sparse_output=True, dtype=np.float32)` (o `build_preprocessor` já faz).
3. **Processar em lotes:** previsão em blocos de 250 mil linhas (`for i in range(0, len(X), 250_000): pipe.predict_proba(X.iloc[i:i+250_000])`), guardando só `y` e a probabilidade em `float32`. É obrigatório no C_16 para `test_pandemic`.
4. **Amostrar com semente e dizer que amostrou:** agrupamento (80 mil fichas do `train_ref`), importância por permutação (50 mil, `n_repeats=3`), gráficos de dispersão (`matriz_para_plot`, de `src/utils/io_eficiente.py`). Registrar a amostra no texto do notebook.
5. **Liberar memória entre seções:** `liberar(globals(), ["df_grande", "X_proc"])` (de `src.utils.performance`) e `plt.close("all")` depois de cada figura. Em notebooks longos (B_06), uma chamada de `liberar` por seção.
6. **Bootstrap:** use `bootstrap_grupo` do #127 (pesos por grupo, ordenação feita uma vez), nunca `ic_bootstrap` em vetor de milhões.

#### 4. Registro (03/11, Pessoa A consolida)
- `outputs/final/performance_notebooks.csv` com uma linha por notebook (a última execução de cada).
- Um parágrafo para o relatório (seção "Reprodutibilidade e desempenho", #133) e a coluna de tempos no README (#126).
- Se algum notebook continuar acima da meta: registre o motivo e o número no card (por exemplo, "C_13: 36 min, 4,1 GB, busca em 400 mil linhas"). Meta ultrapassada **com explicação** é aceitável; sem número, não.

### ④ Pronto quando

- existe: `tools/medir_notebook.py` | A ferramenta de medição de tempo e memória existe em tools/medir_notebook.py.
- existe: `outputs/final/performance_notebooks.csv` | A tabela de tempo e pico de memória dos notebooks da entrega existe em outputs/final/performance_notebooks.csv.
- manual: | Todos os notebooks da entrega (00, 01, A_03, A_04, B_05, B_06, B_07, C_11, C_12, C_13, C_15) têm uma linha na tabela com pico ≤ 6 GB e tempo ≤ 20 min (C_13 ≤ 40 min), ou o motivo registrado neste card; o C_16 usou leitura em lotes de 250 mil linhas.
- manual: | O parágrafo de desempenho está no relatório (#133) e os tempos estão no README (#126).

## #146 · Unificar e sanear o pacote entregue: notebooks, código, configuração e documentos

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M6
- data ideal: 03/11
- responsável: Pessoa A (src, testes, configuração, docs e ferramenta) + Pessoa B (B_05, B_06, B_07) + Pessoa C (00, 01, C_11 a C_16)
- pessoas: A, B, C
- fonte: Diagnóstico de 31/10: marcas de processo em notebooks, src, testes e docs
- depende de: #143, #148, #136, #51
- tags: Notebook, Limpeza, Entrega
- pilar: Documentação + Valor científico-acadêmico
- carga: 5
- novo: sim
- professores: não
- arquivos: tools/auditar_marcas.py

### ① Para entender

O pacote que a banca recebe precisa parecer o que é: um projeto de pós-graduação feito por três pessoas, com **um** estilo, **uma** numeração e comentários que explicam o *porquê* das decisões, não o histórico de como o trabalho foi organizado. Hoje há três tipos de sobra:

1. **Marcas de processo:** referências a pendências (`(#73)`, "ficha #81"), "Pessoa A/B/C", datas internas, "Saída até 10/10", "Gate 1 (09/10)", cabeçalhos `# ====`, "Passo 1", setas e emojis.
2. **Excesso de comentário e de texto narrativo** (células de Markdown que repetem o que o código faz).
3. **Falta de unidade:** pastas por pessoa (`A/`, `B/`, `C/`), títulos que não batem com o nome do arquivo (o arquivo `C_11_...` se chama "C2 — Pipeline Supervisionado"), cada notebook achando a pasta do projeto de um jeito, e duas variantes do mesmo bloco de leitura.

Números da varredura de 31/10 (arquivos do repositório no commit `1e02321`):

| Área | O que a varredura achou |
|---|---|
| `docs/decisoes.md` | 86 referências a pendências, 15 "Pessoa X", 92 datas |
| `tests/` | 24 referências a pendências e 184 linhas decorativas |
| `src/` | 46 linhas decorativas, 5 "Pessoa X", 3 TODO |
| Notebooks | B_05: 76 cabeçalhos decorativos; B_06: 54; B_07: 10; A_09 e A_15 com "Pessoa X"; cabeçalhos do tipo "A1 | 07", "C2", "C3" em quase todos |
| `tools/update_project_reference.py` e `.srag-status-local/` | feitos para uso interno e para outras ferramentas (instruções explícitas a assistentes de IA): **não fazem parte do pacote entregue** |

> [!atenção] O que nunca se faz
> Não apagar comentário que explica uma decisão metodológica (por que 2019 fica no treino, por que o teste só abre uma vez, por que o boosting usa categóricas nativas). Limpar é trocar história por justificativa, não deixar o código mudo.

### ② Problema

A limpeza só funciona se for **feita por uma ferramenta de busca** (não de memória) e **depois** das mudanças de código, porque cada edição de notebook pode reintroduzir marcas. Por isso a ordem é: remoções (#143) → adaptação dos notebooks (#132, #148, #136, #51) → este card → execução final (#126).

Também não se pode reexecutar o C_16 (o teste abre uma vez). Por isso o C_16 é **limpo antes** de rodar, durante a adaptação (#148): as saídas que ficam salvas são as definitivas.

### ③ O que fazer

> [!decisão] Replanejamento de 31/10
> Limpeza **automatizada onde é segura** (linhas decorativas, `(#NN)`, emojis) e **manual onde exige leitura** (frases, "Pessoa X", datas, comentários excessivos). Cada pessoa limpa os arquivos que já editou; a Pessoa A cuida do que não tem dono e da renomeação final.

**Dono:** Pessoa A (src, testes, configuração, docs, ferramenta e renomeação) · Pessoa B (B_05, B_06, B_07) · Pessoa C (00, 01, C_11 a C_16) · **Prazo:** ferramenta em 31/10; limpeza e renomeação em 03/11, até as 20h · **Esforço estimado:** A ≈ 2 h · B ≈ 2 h 30 · C ≈ 1 h · **Começa quando:** #143, #148, #136 e #51

#### 1. Ferramenta de varredura (Pessoa A, 31/10, 20 min)
Crie `tools/auditar_marcas.py` (testado em notebook e em `.py` de exemplo). Sem argumento só relata; com `--aplicar` remove apenas linhas decorativas, `(#NN)` em comentários e Markdown e emojis, preservando saídas e ordem das células. Commit: `chore: ferramenta de varredura de marcas`.

```python
r"""Procura (e, se pedido, remove) marcas de processo interno nos arquivos que serão entregues.

Procura: referências a pendências ((#73), ficha #81, card 12), "Pessoa A/B/C", linhas decorativas
(# =====, # -----), emojis e setas decorativas, TODO/FIXME e menções a IA.
Mostra também a proporção de linhas de comentário em células de código.

Uso (na raiz do repositório):
    .\.venv\Scripts\python.exe tools/auditar_marcas.py                 # só relatório
    .\.venv\Scripts\python.exe tools/auditar_marcas.py notebooks src   # só estas pastas
    .\.venv\Scripts\python.exe tools/auditar_marcas.py --aplicar       # remove o que é seguro

--aplicar só mexe em COMENTÁRIOS e em células Markdown: apaga linhas decorativas, tira "(#NN)" e emojis.
"Pessoa X", datas e frases explicativas continuam como aviso: exigem leitura e reescrita humana.
Notebooks mantêm as saídas e a ordem das células; o arquivo só é regravado se algo mudou.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
PADROES = {
    "ref_pendencia": re.compile(r"\(\s*#\d{1,3}(?:\s*[,e/]\s*#?\d{1,3})*\s*\)|\b(?:ficha|card|tarefa|pendência|item)\s*#?\d{1,3}\b|(?<![\w&/])#\d{2,3}\b"),
    "pessoa": re.compile(r"\bPessoa\s+[ABC]\b"),
    "decorativa": re.compile(r"^\s*#\s*(?:[=\-─━_*~]{4,}.*[=\-─━_*~]{4,}|[=\-─━_*~]{6,})\s*$", re.M),
    "emoji": re.compile("[\u2705\u274c\u26a0\u2714\u2716\u2b50\U0001F300-\U0001FAFF]"),
    "etapa_numerada": re.compile(r"^\s*#\s*(?:PASSO|Passo|ETAPA|Etapa|STEP|Step|PARTE|Parte)\s*\d+", re.M),
    "todo": re.compile(r"\b(?:TODO|FIXME|XXX|HACK)\b"),
    "ia": re.compile(r"\b(?:IA|Copilot|ChatGPT|Claude|GPT|LLM|assistente)\b"),
}
SEGURO = ("decorativa", "emoji")
EXTENSOES = {".ipynb", ".py", ".md", ".yaml", ".yml", ".toml"}
IGNORAR = {".venv", ".git", "outputs", "data", "__pycache__", ".srag-status-local"}
IGNORAR_ARQ = {"PROJECT_STATUS.md", "PROJECT_STATUS_TEXT.md", "auditar_marcas.py"}


def _limpar_comentarios(texto: str) -> str:
    """Remove linhas decorativas, '(#NN)' e emojis de linhas de comentário."""
    saida = []
    for linha in texto.split("\n"):
        if PADROES["decorativa"].match(linha):
            continue
        if linha.lstrip().startswith("#"):
            linha = re.sub(r"\s*\(\s*#\d{1,3}(?:\s*[,e/]\s*#?\d{1,3})*\s*\)", "", linha)
            linha = PADROES["emoji"].sub("", linha).rstrip()
        else:
            linha = re.sub(r"\s+#\s*\(\s*#\d{1,3}(?:\s*[,e/]\s*#?\d{1,3})*\s*\)\s*$", "", linha)
        saida.append(linha)
    return re.sub(r"\n{4,}", "\n\n\n", "\n".join(saida))


def _limpar_markdown(texto: str) -> str:
    texto = re.sub(r"\s*\(\s*#\d{1,3}(?:\s*[,e/]\s*#?\d{1,3})*\s*\)", "", texto)
    return PADROES["emoji"].sub("", texto)


def _celulas(caminho: Path):
    nb = json.loads(caminho.read_text(encoding="utf-8"))
    return nb, nb.get("cells", [])


def _fonte(c) -> str:
    s = c.get("source", "")
    return "".join(s) if isinstance(s, list) else s


def auditar(caminho: Path) -> tuple[Counter, dict]:
    achados, info = Counter(), {}
    if caminho.suffix == ".ipynb":
        _, cels = _celulas(caminho)
        linhas_cod = com = 0
        for c in cels:
            t = _fonte(c)
            for k, p in PADROES.items():
                achados[k] += len(p.findall(t))
            if c.get("cell_type") == "code":
                ls = [l for l in t.split("\n") if l.strip()]
                linhas_cod += len(ls)
                com += sum(1 for l in ls if l.lstrip().startswith("#"))
        info = {"linhas_codigo": linhas_cod, "comentarios": com, "pct_comentario": round(100 * com / max(linhas_cod, 1))}
    else:
        t = caminho.read_text(encoding="utf-8", errors="replace")
        for k, p in PADROES.items():
            achados[k] += len(p.findall(t))
    return achados, info


def aplicar(caminho: Path) -> bool:
    if caminho.suffix == ".ipynb":
        nb, cels = _celulas(caminho)
        mudou = False
        for c in cels:
            antes = _fonte(c)
            depois = _limpar_comentarios(antes) if c.get("cell_type") == "code" else _limpar_markdown(antes)
            if depois != antes:
                c["source"] = depois.splitlines(keepends=True)
                mudou = True
        if mudou:
            caminho.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        return mudou
    antes = caminho.read_text(encoding="utf-8")
    depois = _limpar_markdown(antes) if caminho.suffix == ".md" else _limpar_comentarios(antes)
    if depois != antes:
        caminho.write_text(depois, encoding="utf-8")
        return True
    return False


def arquivos(pastas: list[str]):
    bases = [RAIZ / p for p in pastas] if pastas else [RAIZ]
    for base in bases:
        itens = [base] if base.is_file() else sorted(base.rglob("*"))
        for p in itens:
            if p.is_file() and p.suffix in EXTENSOES and p.name not in IGNORAR_ARQ \
                    and not (set(p.relative_to(RAIZ).parts) & IGNORAR):
                yield p


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pastas", nargs="*")
    ap.add_argument("--aplicar", action="store_true", help="remove linhas decorativas, (#NN) e emojis em comentários e Markdown")
    args = ap.parse_args()

    total, linhas = Counter(), []
    for p in arquivos(args.pastas):
        if args.aplicar and aplicar(p):
            print(f"limpo: {p.relative_to(RAIZ)}")
        a, info = auditar(p)
        total.update(a)
        if sum(a.values()) or info.get("pct_comentario", 0) >= 15:
            linhas.append((sum(a.values()), p.relative_to(RAIZ).as_posix(), a, info))
    for _, nome, a, info in sorted(linhas, reverse=True):
        det = ", ".join(f"{k}={v}" for k, v in a.items() if v)
        extra = f" · comentários={info['pct_comentario']}% do código" if info else ""
        print(f"{nome}: {det}{extra}")
    print("TOTAL:", ", ".join(f"{k}={v}" for k, v in total.items()) or "nada encontrado")
    restante = sum(v for k, v in total.items() if k not in SEGURO)
    return 0 if restante == 0 and not total.get("decorativa") and not total.get("emoji") else 1


if __name__ == "__main__":
    sys.exit(main())
```

#### 2. Conjunto final de notebooks (12) e nomes
A renomeação é feita **uma vez**, no fim (passo 6), com `git mv`, para não quebrar o trabalho dos outros durante o fim de semana. Até lá, todos usam os nomes atuais.

| Novo nome (`notebooks/`) | Origem | Observação |
|---|---|---|
| `01_acesso_dados.ipynb` | `00_acesso_dados_parquet` | |
| `02_extracao.ipynb` | `01_extracao` | |
| `03_coorte_e_protocolo.ipynb` | `A/A_03_coorte_protocolo` | |
| `04_qualidade_e_elegibilidade.ipynb` | `A/A_04_qualidade_elegibilidade` | recebe, como seções finais, o conteúdo do `A6_ancora_e_selecao` (âncora e excluídos) e do `A_15_fator_risco` (comorbidades × fator de risco); depois apague os dois |
| `05_eda_primeira_passagem.ipynb` | `B/B_05_eda_primeira_passagem` | |
| `06_eda_temporal_e_agrupamento.ipynb` | `B/B_06_eda_temporal_clustering` | |
| `07_pilotos_supervisionados.ipynb` | `B/B_07_supervisionado_pilotos` | |
| `08_pipeline_supervisionado.ipynb` | `C/C_11_pipeline_supervisionado` | |
| `09_baseline_e_logistica.ipynb` | `C/C_12_baseline_logistica` | |
| `10_boosting_e_ajuste_fino.ipynb` | `C/C_13_boosting` | |
| `11_calibracao_e_limiar.ipynb` | `C/C_15_calibracao_limiar` | |
| `12_validacao_final.ipynb` | `C/C_16_validacao_final` | executado uma única vez; só renomear |

Saem do pacote (já tratados no #143): `B_10`, `A_08`, `A_09`, `A_14`, `C_02`, o construtor provisório da coorte B e as cópias de segurança.

#### 3. Padrão de cada notebook (todos os 12)
1. **Primeira célula (Markdown):** `# NN — Título` igual ao nome do arquivo, três linhas (o que faz, o que lê, o que grava) e a linha "Pré-requisito: notebooks NN e NN". Sem nome de pessoa, sem data, sem número de pendência.
2. **Segunda célula (código):** a mesma de todos para achar a raiz (função `encontrar_raiz_projeto` já usada nos notebooks C), mais `from src.utils import config as C`. Nada de caminho absoluto.
3. Uma célula Markdown curta por seção (título e uma frase). Parágrafo longo só onde houver uma decisão a justificar.
4. Comentário no código só para o **porquê**; no máximo uma linha por bloco lógico. Docstring de uma linha nas funções definidas no notebook.
5. Saídas salvas, sem erro, sem barras de progresso longas, sem `display` de DataFrame com mais de 30 linhas e com `plt.close()` depois de cada figura (o B_06 não pode passar de ≈ 15 MB).
6. Última célula: caminhos e hashes dos arquivos gravados (ajuda quem reproduz).

#### 4. Regras de limpeza
| Padrão | Ação |
|---|---|
| `(#NN)`, "ficha #NN", "card NN", "tarefa NN" | apagar a referência; se a frase perder o sentido, reescrever dizendo o motivo |
| "Pessoa A", "Pessoa B", "Pessoa C", "Revisão: B confere…" | apagar; autoria fica no Git |
| Datas internas ("até 10/10", "decidido em 28/10") | apagar; em `docs/decisoes.md` a data da decisão **fica** |
| `# ====`, `# ----`, emojis, setas, "Passo N" | apagar |
| `TODO`, `FIXME`, código comentado, `print` de depuração | apagar ou resolver |
| Mais de uma em cada seis linhas de uma célula de código em comentário | reduzir para o essencial |
| Texto que descreve a gestão do projeto ("Enxugado", "Replanejamento", "Gate pendente") | apagar |

#### 5. Execução (cada pessoa, com a ferramenta do passo 1)
1. `git pull`; `.\.venv\Scripts\python.exe tools/auditar_marcas.py notebooks src tests configs docs README.md` (só relatório) e copie as linhas dos **seus** arquivos para um bloco de notas.
2. `.\.venv\Scripts\python.exe tools/auditar_marcas.py <seus arquivos> --aplicar` e depois leia **arquivo por arquivo** o que sobrou (frases, "Pessoa X", datas, comentários em excesso) e reescreva.
3. Rode de novo a varredura; o objetivo é `TOTAL` zerado para `ref_pendencia`, `pessoa`, `decorativa`, `emoji` e `etapa_numerada` nos seus arquivos.
4. Não reexecute notebook só por causa da limpeza se o código não mudou; se mudou, execute com `tools/medir_notebook.py --salvar-no-lugar` (#145).
5. Commit por pessoa: `chore: limpa marcas e padroniza notebooks (B)`.

| Pessoa | Arquivos |
|---|---|
| A | `src/`, `tests/`, `configs/`, `docs/decisoes.md` (tirar `(#NN)`, "Pessoa X" e os trechos de gestão; **manter as datas das decisões**), `README.md`, `04_...` (com A6 e A_15 incorporados) e `03_...` |
| B | `05_...`, `06_...`, `07_...` (os três são os maiores: 76, 54 e 10 cabeçalhos decorativos) |
| C | `01_...`, `02_...`, `08_...` a `11_...`; o `12_...` já saiu limpo do #148 |

#### 6. Renomear e fechar (Pessoa A, 03/11, depois que B e C fizeram push)
1. `git pull`; confira que a varredura não acusa mais nada.
2. `git mv` de cada notebook para o nome novo do passo 2; remova as pastas `notebooks/A`, `notebooks/B` e `notebooks/C`.
3. Troque os nomes antigos nos documentos: `README.md`, `docs/decisoes.md`, docstrings que citam notebooks e o **`PROJECT_STATUS_TEXT.md`** (critérios ④ e campo `arquivos` dos cards; são ≈ 60 ocorrências). Um comando basta: `.\.venv\Scripts\python.exe -c "import pathlib,re; m={'notebooks/C/C_16_validacao_final':'notebooks/12_validacao_final','notebooks/C/C_15_calibracao_limiar':'notebooks/11_calibracao_e_limiar','notebooks/C/C_13_boosting':'notebooks/10_boosting_e_ajuste_fino','notebooks/C/C_12_baseline_logistica':'notebooks/09_baseline_e_logistica','notebooks/C/C_11_pipeline_supervisionado':'notebooks/08_pipeline_supervisionado','notebooks/B/B_07_supervisionado_pilotos':'notebooks/07_pilotos_supervisionados','notebooks/B/B_06_eda_temporal_clustering':'notebooks/06_eda_temporal_e_agrupamento','notebooks/B/B_05_eda_primeira_passagem':'notebooks/05_eda_primeira_passagem','notebooks/A/A_04_qualidade_elegibilidade':'notebooks/04_qualidade_e_elegibilidade','notebooks/A/A_03_coorte_protocolo':'notebooks/03_coorte_e_protocolo','notebooks/01_extracao':'notebooks/02_extracao','notebooks/00_acesso_dados_parquet':'notebooks/01_acesso_dados'}; arqs=['PROJECT_STATUS_TEXT.md','README.md','docs/decisoes.md']; [p.write_text(re.sub('|'.join(map(re.escape,m)),lambda x:m[x.group(0)],p.read_text(encoding='utf-8')),encoding='utf-8') for p in map(pathlib.Path,arqs)]"`.
4. `.\.venv\Scripts\python.exe -m pytest -m "not slow" -q` e `.\.venv\Scripts\python.exe .srag-status-local\server.py validar` (o painel não pode apontar problema de formato).
5. Commit: `chore: unifica a numeracao dos notebooks`. Avise B e C para `git pull` antes do #126.

### ④ Pronto quando

- nao-existe: `notebooks/C/C_16_validacao_final.ipynb` | O C_16 foi renomeado para a numeração unificada (a pasta notebooks/C deixou de existir).
- nao-existe: `notebooks/B/B_06_eda_temporal_clustering.ipynb` | O B_06 foi renomeado para a numeração unificada (a pasta notebooks/B deixou de existir).
- nao-existe: `notebooks/A/A_03_coorte_protocolo.ipynb` | O A_03 foi renomeado para a numeração unificada (a pasta notebooks/A deixou de existir).
- existe: `notebooks/12_validacao_final.ipynb` | O notebook final de validação segue a numeração unificada.
- existe: `notebooks/04_qualidade_e_elegibilidade.ipynb` | O notebook 04 reúne qualidade, elegibilidade, âncora e fator de risco.
- nao-existe: `notebooks/A/A6_ancora_e_selecao.ipynb` | O A6 foi incorporado ao notebook 04 e removido.
- existe: `tools/auditar_marcas.py` | A ferramenta de varredura de marcas existe.
- manual: | `tools/auditar_marcas.py notebooks src tests configs docs README.md` termina com ref_pendencia, pessoa, decorativa, emoji e etapa_numerada zerados (em docs/decisoes.md, as datas das decisões foram mantidas), e cada notebook segue o padrão do item 3 deste card.
- manual: | `.srag-status-local\server.py validar` não aponta problema de formato e o pytest rápido passa depois da renomeação.

## #147 · Congelar e conferir o pacote entregue em 04/11 (e zerar as pendências de verificação)

- prioridade: P1
- situação: aberta
- estratégia: documentar
- marco: M6
- data ideal: 04/11
- responsável: Pessoa A
- pessoas: A
- fonte: Auditoria do commit 1e02321 (verificação rápida de 30/10): critérios ✗ em cards concluídos
- depende de: #126, #133, #146
- tags: Entrega, Reprodutibilidade, Checklist
- pilar: Documentação + Valor científico-acadêmico
- carga: 1
- novo: sim
- professores: não
- arquivos: .gitattributes

### ① Para entender

Último passo antes de entregar: congelar o commit, montar o pacote que a banca recebe e fechar as **discrepâncias do painel** (cards concluídos cujo "④ Pronto quando" ainda aparece ✗ ou "⚠ reconfirmar"). Se essas discrepâncias ficarem, um avaliador que abra o painel vê "concluída, mas critério não atendido".

O pacote da banca **não é o repositório inteiro**. Ferramentas internas de acompanhamento (painel, auditor, gerador de referência para assistentes de IA) e os arquivos de status não fazem parte do trabalho e não devem ir para a entrega.

### ② Problema

Discrepâncias encontradas na verificação rápida de 30/10 (commit `1e02321`) e o remédio de cada uma:

| Card concluído | Critério ✗ | Remédio |
|---|---|---|
| #77, #85, #120 | `gates.G1/G2.status = aprovado` | resolvido pelo #144 |
| #99, #139, #125 | notebook B_06 e B_07 sem execução salva | resolvido pelo #126 (execução final com `--salvar-no-lugar`); o #99 pede também o texto "Memória após compactação" na saída do B_06 (confira ou troque o critério para o texto atual) |
| #60 | saída do B_06 com "silhouette" | mesma execução do #126 |
| #116 | `tools/update_project_reference.py` contém `## SECTION` | o gerador hoje escreve `## 6. Full content of every file` (schema v16): troque o critério pelo texto atual (já ajustado neste painel) |
| #137 | `src/evaluation/cluster_profile.py` não está no Git | push do arquivo e do teste (#55, passo 1) |
| #31 | `configs/paths.local.json` não pode existir | apague o arquivo na máquina onde existir (é ignorado pelo Git) |
| #135 | colar a saída do `pytest -m slow` | rode `.\.venv\Scripts\python.exe -m pytest -m slow tests/test_regras_pessoa_a.py -q` com o artefato real e cole no card |
| #50, #141 | arquivos de `outputs/` só existem na máquina de quem gerou | comentar no card que foram conferidos (o painel mostra "indisponível nesta máquina", sem erro) |

### ③ O que fazer

> [!decisão] Replanejamento de 31/10
> Última hora de trabalho: nada de código novo. Só **conferir, congelar e empacotar**.

**Dono:** Pessoa A · **Prazo:** 04/11 (quarta), 12h às 14h (a entrega vai até o fim do dia) · **Esforço estimado:** ≈ 1 h · **Começa quando:** #126, #133 e #146

1. `git pull`; `git status` limpo. Um comando para o resumo: `.\.venv\Scripts\python.exe tools/auditar_marcas.py notebooks src tests configs docs README.md; .\.venv\Scripts\python.exe -m pytest -m "not slow" -q; .\.venv\Scripts\python.exe .srag-status-local\server.py validar` (varredura sem marcas, 0 falhas e nenhum problema de formato).
2. Painel: **🔄 Atualizar, auditar e validar**. Para cada card concluído que ainda apareça ✗ ou ⚠, aplique o remédio da tabela do **② Problema**. O que for "indisponível nesta máquina" só precisa de um comentário.
3. Regerar a referência do projeto (fecha o #130): `.\.venv\Scripts\python.exe tools/update_project_reference.py --run-tests --pytest-args="-m 'not slow'"` (testes passando, nenhum código ignorado pelo Git). Ela **não** vai para o pacote.
4. **Pacote da banca:** crie `.gitattributes` com as linhas abaixo; elas excluem do `git archive` (e só dele) os arquivos internos. O repositório da equipe continua igual.

```
.srag-status-local/** export-ignore
.scripts/** export-ignore
PROJECT_STATUS.md export-ignore
PROJECT_STATUS_TEXT.md export-ignore
docs/PROJECT_COMPLETE_REFERENCE.txt export-ignore
tools/update_project_reference.py export-ignore
tools/clean_project.py export-ignore
tools/auditar_marcas.py export-ignore
.gitattributes export-ignore
```
   (Em `.gitattributes`, um padrão de pasta com barra no fim não funciona: use `pasta/**`.)
   Se a entrega for o **link do GitHub**, em vez disso crie o branch `entrega` a partir da tag e remova esses caminhos nele com `git rm -r`; entregue o link desse branch (o histórico do `main` não precisa ser reescrito).
5. Commit final: `chore: pacote de entrega`. Tag e envio: `git tag entrega-2026-11-04; git push --tags`. Pacote: `git archive --format=zip -o entrega_srag_2026-11-04.zip entrega-2026-11-04`.
6. **Confira o zip:** abra-o numa pasta nova e confirme (a) sem `.srag-status-local`, sem `PROJECT_STATUS*.md` e sem referência para assistentes; (b) notebooks `01` a `12` com saídas; (c) `README.md` com "Como reproduzir"; (d) `outputs/final/` com as tabelas citadas no relatório (os arquivos de `outputs/` são ignorados pelo Git: copie `outputs/final/` para dentro do pacote se a banca pedir os resultados; o relatório já os traz); (e) relatório em PDF e no formato do #97.
7. Anote no card: SHA do commit, nome da tag e o tamanho do zip. Avise as duas pessoas: **nenhum push depois deste ponto**.

### ④ Pronto quando

- existe: `.gitattributes` | O arquivo .gitattributes com os export-ignore do pacote da banca existe.
- manual: | O pytest rápido passa, o painel não aponta problema de formato, a varredura de marcas está zerada e os cards concluídos com ✗ ou ⚠ foram tratados (ou comentados).
- manual: | A tag entrega-2026-11-04 está no commit final, o zip da banca foi aberto numa pasta nova e conferido (sem arquivos internos, notebooks 01 a 12 com saídas, README e relatório), e o SHA foi anotado neste card.

## #148 · Adaptar o C_15 (Pessoa B) e o C_16 (Pessoa A) aos seis blocos e à estrutura de entrega

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M2
- data ideal: 01/11
- responsável: Pessoa B (C_15) + Pessoa A (C_16); revisão: Pessoa C
- pessoas: B, A
- fonte: Leitura dos notebooks C_15 e C_16 no commit 1e02321 (31/10)
- depende de: #132, #127, #144
- tags: Código, Notebook, Partição, Vazamento, Calibração
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 5
- novo: sim
- professores: não
- arquivos: notebooks/C/C_15_calibracao_limiar.ipynb, notebooks/C/C_16_validacao_final.ipynb, src/evaluation/calibration.py, src/models/calibration.py

### ① Para entender

A cadeia C foi escrita para a divisão antiga (treino, validação, teste). O C_11 a C_13 são adaptados no #132 (Pessoa C). Os dois últimos precisam de mais mudança, porque contêm a lógica que **decide** (C_15) e a que **abre o teste** (C_16). Para ganhar tempo, são adaptados em paralelo, por duas pessoas diferentes:

| Notebook | Papel | Blocos que usa | Quem |
|---|---|---|---|
| C_15 | ajusta o calibrador e escolhe o corte | `train_ref`, `val_cal`, `val_meas` | Pessoa B |
| C_16 | abre o teste uma única vez e gera o resultado | `train_ref`, `val_cal`, `val_meas`, `test_ref`, `test_pandemic` | Pessoa A |

Os dois saem **já limpos** (padrão do #146): o C_16 não pode ser reexecutado depois que o teste abrir.

### ② Problema

O que foi lido no código do commit `1e02321`:

- **C_15:** divide a validação em metades com `train_test_split` (`HONEST_CALIB_SPLIT = True`), carrega `partitions=("treino", "validacao")` e `split_partitions`, usa `SRAG_COHORT_KIND` com padrão `provisional`, escolhe o "melhor" finalista pela AUC (`max(... ["limiar"]["auc"])`) e grava arquivos com carimbo de data em `outputs/tables/`.
- **C_16:** `partitions=("treino", "validacao", "teste")`, `df.loc[df[PARTICAO] == "teste"]`, `_reproduzir_split_val_cal` (outra divisão da validação), `_localizar_manifesto_c5` por `st_mtime`, `ic_bootstrap` (reordena o vetor a cada réplica) e gravação em `outputs/tables/C6_*` com carimbo.
- **Memória:** o teste inteiro (`test_ref` + `test_pandemic`) são 3.035.074 linhas com 46 colunas. O notebook as carrega de uma vez e as passa pelo pré-processador de uma vez.
- **Limiar:** o YAML lista `recall_minimo` entre as métricas candidatas (#73), mas `escolher_limiar` só aceita `f1`, `precision`, `recall`, `accuracy` e `youden_j`: com `limiar.metrica = recall_minimo` o C_15 levanta `ValueError` (corrigido no #80).

### ③ O que fazer

> [!decisão] Replanejamento de 31/10
> Mesmo padrão de leitura do #132, nomes de arquivos **fixos** em `outputs/final/` (sem carimbo; nenhum notebook escolhe arquivo pela data) e o C_16 lendo o teste **em lotes**.

**Dono:** Pessoa B (C_15) e Pessoa A (C_16) · **Revisão:** Pessoa C (20 min cada, só o diff) · **Prazo:** C_15: 31/10 (sábado), 20h às 22h · C_16: 01/11 (domingo), manhã · **Esforço estimado:** B ≈ 2 h · A ≈ 2 h 30 · **Começa quando:** #132 (padrão de leitura) e #127 (bootstrap)

#### C_15 · Pessoa B
1. **Leitura:** `df, manifest = load_supervised_artifact(ROOT_DIR, expected_kind="final", partitions=("train_ref", "val_cal", "val_meas"))`; `treino`, `val_cal`, `val_meas` por `df[PARTICAO]`. **Apague** `HONEST_CALIB_SPLIT`, `CALIB_SPLIT_FRAC`, `CALIB_SPLIT_SEED`, `CALIB_SPLIT_HASH`, `train_test_split` e `split_partitions`. O bloco `val_tune` não é lido aqui (é do ajuste).
2. **Finalista:** `FINALISTA = C.cfg("selecao_modelos", "finalista_escolhido")` (preenchido no #1). Treine `build_finalista(FINALISTA)` em `train_ref`; se o YAML ainda tiver `finalista_escolhido = null`, pare com mensagem clara. Mantenha o **outro** finalista só para a tabela comparativa (`FINALISTAS` do YAML).
3. **Calibração:** para `sigmoid` e `isotonic`, `calibrar(pipe, X_val_cal, y_val_cal, method=m)`; probabilidades em `val_meas`. Para cada método e para o modelo bruto: Brier, log loss, **intercepto e inclinação de calibração**, **ECE por quantis** e curva (as funções novas são feitas no #79; se ainda não existirem, deixe a chamada pronta e a célula protegida por `try/except ImportError`).
4. **Peso de classe (#5):** troque a célula que usa "o método escolhido" por uma constante `COMPARACAO_CW_METODO = "sigmoid"` e rode só no finalista (`balanced` × `None`, mesmos hiperparâmetros, calibradas em `val_cal`, medidas em `val_meas`). Grave `outputs/final/peso_classe_val_meas.csv` (PR-AUC, ROC-AUC, Brier calibrado, ECE).
5. **Escolha do finalista:** use o que está no YAML, nunca `max(AUC)`.
6. **Saídas fixas:** `outputs/final/calibracao_val_meas.csv`, `outputs/final/limiares_val_cal.csv`, `outputs/final/predicoes_val_meas.parquet` (`id_registro`, `y`, `prob_bruta`, `prob_calibrada`, `regiao_residencia`, `ano_internacao`) e `outputs/final/manifesto_calibracao.json` (`dataset_sha256`, `run_id_finalista`, `calibracao`, `brier_val_meas`, commit). O notebook **imprime** a proposta de YAML (`calibracao.metodo`, `limiar.*`, `run_id_finalista`); quem aplica é a Pessoa C, à mão (#79 e #80).
7. **Limpeza:** padrão do #146 (primeira célula, sem "C5", sem "item #5", sem emojis); `liberar(globals(), ["X_train_proc"])` depois do ajuste.
8. A execução completa é do #5 e do #79 (depois do #1). Até lá, o notebook só precisa abrir e rodar as primeiras células sem erro (leitura dos blocos e checagem do manifesto).

#### C_16 · Pessoa A
9. **Portões:** `GATES_EXIGIDOS = ["G6_finalistas_tuning", "G7_calibracao", "G8_limiar", "G9_holdout"]`, todos `aprovado`.
10. **Congelamento:** leia do YAML `finalista_escolhido`, os hiperparâmetros, `class_weight`, `calibracao.metodo`, `limiar.otimo` e `limiar.por_regiao`. Recalcule `identificador_execucao(...)` (#132, passo 10) e **compare** com `selecao_modelos.run_id_finalista`; divergiu, pare. Isso substitui `_localizar_manifesto_c5` (nada de `st_mtime`).
11. **Reprodução do desenvolvimento (sem gate de teste):** `load_supervised_artifact(..., partitions=("train_ref", "val_cal", "val_meas"))`; ajuste o finalista em `train_ref`, calibre em `val_cal`, meça em `val_meas` e confira que o Brier de `val_meas` bate com `manifesto_calibracao.json` (tolerância 1e-6). Se não bater, pare antes de abrir o teste.
12. **Guarda contra reabertura:** pare se `manifesto_supervisionado.json["test_opened"]` já for `true` ou se `gates.G9_holdout.n_acessos >= 1` (exceto com `SRAG_ALLOW_TEST_REOPEN=1`, justificado no `decisoes.md`). Isso substitui a busca por `C6_*_manifesto.json`.
13. **Abrir o teste em lotes** (obrigatório pelo #145): para cada bloco em `("test_ref", "test_pandemic")`, `load_supervised_artifact(ROOT_DIR, expected_kind="final", partitions=(bloco,), columns=[*FEATURES, ALVO, "id_registro", "group_id", "ano_internacao", "regiao_residencia", "sg_uf", "faixa_etaria", "sexo_categoria"])` (o alvo precisa estar na lista: o carregador só devolve as colunas pedidas); probabilidades em lotes de 250 mil linhas (`preditor.predict_proba(X.iloc[i:i+250_000])[:, 1]`); guarde só `y`, `prob` em `float32` e as colunas de grupo, e `del` o quadro de dados do bloco (`liberar`).
14. **Logo depois do primeiro carregamento do teste**, regrave `data/analytical/manifesto_supervisionado.json` com `test_opened: true`, `test_opened_utc` e `test_opened_commit` (três linhas; substitui o #26). Só depois calcule métricas.
15. **Métricas** (contrato do #119): Teste A (`test_ref`), Teste B (`test_ref` + `test_pandemic`), `test_pandemic` isolado e cada ano (inclui 2019): `n`, óbitos, prevalência, PR-AUC, PR-AUC ÷ prevalência, ROC-AUC, Brier, Brier do modelo nulo, intercepto e inclinação, ECE por quantis, matriz de confusão e sensibilidade, precisão, especificidade e F1 no corte congelado (e no corte de sensibilidade 0,70). IC 95% com `bootstrap_grupo` (#127): 1.000 réplicas no Teste A; 300 no Teste B e no `test_pandemic` (mais de 1 milhão de linhas).
16. **Por região:** sensibilidade e precisão no corte global e no regional (`limiar.por_regiao`) em `outputs/final/teste_por_regiao.csv`.
17. **Saídas fixas** (nomes do #119): `teste_a_metricas.csv`, `teste_b_metricas.csv`, `pandemico_metricas.csv`, `por_ano.csv`, `calibracao_*.csv`, `figuras/*.png`, `predicoes_teste.parquet` (`id_registro`, `group_id`, `particao`, `ano_internacao`, `regiao_residencia`, `sg_uf`, `faixa_etaria`, `sexo_categoria`, `y`, `prob_calibrada`, `classe`) e `manifesto_teste.json` (SHA-256 do artefato, commit, hash do YAML, `run_id_finalista`, horário de abertura).
18. **Marcar o G9** como `executado` com a função existente (`_marcar_g9_executado`), **no fim**. Mantenha a ordem: gravar tudo → marcar o gate.
19. **Limpeza** padrão do #146, para o notebook sair pronto. Verificação **sem abrir o teste**: com `SRAG_DRY_RUN=1` o notebook roda até o passo 11 e para (acrescente essa saída antecipada) e mostra o que faria nos passos 12 a 18; a Pessoa C revisa o diff nessa condição.
20. Commit: `feat: C_15 e C_16 nos seis blocos [done:#148] [done:#58]`.

### ④ Pronto quando

- nao-contem: `notebooks/C/C_15_calibracao_limiar.ipynb` :: `HONEST_CALIB_SPLIT` | O C_15 não divide mais a validação ao meio por conta própria: a variável HONEST_CALIB_SPLIT sumiu do código; calibração e corte usam val_cal e a medição usa val_meas.
- contem: `notebooks/C/C_15_calibracao_limiar.ipynb` :: `val_cal` | O C_15 calibra e escolhe o corte em val_cal.
- nao-contem: `notebooks/C/C_16_validacao_final.ipynb` :: `st_mtime` | O C_16 não escolhe mais o manifesto pela data do arquivo (st_mtime).
- contem: `notebooks/C/C_16_validacao_final.ipynb` :: `run_id_finalista` | O C_16 confere o run_id_finalista gravado no YAML.
- contem: `notebooks/C/C_16_validacao_final.ipynb` :: `test_opened` | O C_16 regrava o manifesto com test_opened logo depois de carregar o teste.
- contem: `notebooks/C/C_16_validacao_final.ipynb` :: `250_000` | O C_16 prevê o teste em lotes de 250 mil linhas.
- manual: | Os dois notebooks seguem o padrão de limpeza do #146, escrevem só em outputs/final com nomes fixos e a Pessoa C revisou o diff do C_16 com SRAG_DRY_RUN=1, antes do G9.
