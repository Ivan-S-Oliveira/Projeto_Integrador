<!-- PROJECT_STATUS_TEXT.md · formato 1 · fonte do conteúdo do Painel de Pendências SRAG -->
# Status do projeto SRAG · conteúdo textual

Este arquivo é a **fonte única de todo o texto** do Painel de Pendências (`.srag-status-local/painel.html`). O painel lê este arquivo do GitHub, converte para HTML e grava o conteúdo **dentro** do `painel.html` sempre que algo muda (só a região de dados; nada é reescrito quando não há mudança). A situação compartilhada de cada item (concluída, a confirmar, precisa revisão…), os comentários e a auditoria continuam em `PROJECT_STATUS.md`, mantido só pelo painel.

**Pode editar à mão** no VS Code ou pelo botão ✎ do painel. Ao salvar aqui, o painel mostra a mudança em ~2 s como prévia local. Para a equipe receber: commit e push normais, ou o botão “Publicar edições locais” do painel.

Regras do formato:

- `## #N · Título` abre um item. O número é fixo e nunca é reutilizado; para tirar um item, use `- removido: motivo`.
- Logo abaixo do título, uma linha por campo: `prioridade` (P1–P4), `situação` (aberta, parcial, resolvida), `estratégia` (desenvolver, explorar, documentar, despriorizar, resolvida), `marco`, `data ideal` (DD/MM), `responsável`, `pessoas` (A, B, C, Equipe), `fonte`, `depende de` (#12, #30), `tags`, `pilar`, `carga` (número), `novo` (sim/não), `professores` (sim/não) e, opcionais, `arquivos` (caminhos que a auditoria deve ligar ao item) e `removido`. Use `—` para vazio. “Trava” é calculado sozinho a partir de “depende de”.
- Seções com `###`: `① Para entender`, `② Problema`, `③ O que fazer`. Qualquer outro `### Título` vira uma seção extra no card.
- Texto em Markdown simples: parágrafos, `**negrito**`, `*itálico*`, `` `código` ``, listas com `-` ou `1.`, tabelas `| a | b |`, blocos de código com três crases, links `[texto](url)` e caixas `> [!decisão] Título` (também `atenção`, `exemplo`, `ok` e `pilar`). HTML também é aceito: um bloco que começa com `<` passa sem alteração (é assim que ficam os gráficos de barras e os quadros de números).
- Dentro das seções, não comece linhas com dois ou três `#` seguidos de espaço (subtítulo: use `####`). `#30` no meio do texto vira link para o item no painel.
- `## Painel · textos gerais` guarda os textos do topo, entrega, cronograma, pessoas, caminho crítico, aviso, ajuda e rodapé.

### Subtítulo

Revisão de 24/10 (noite), depois da orientação com o professor. Coorte definitiva publicada (3.884.728 notificações) e partição em seis blocos já gerada; agora o caminho é levar o artefato para o código central (#131), conferir as invariantes (#135), adaptar a cadeia C (#132), decidir os três sintomas de 2019 (#50), ajustar, calibrar, escolher o corte e abrir os Testes A e B uma única vez. Não supervisionado refeito com one-hot e testes estatísticos (#136, #137). Entrega: **03/11/2026**.

### Cronograma

- **24–25/10** — Orientação (#95); passagem de bastão (#72); regra de grupo (#10); artefato de seis blocos no src (#131); decisões e YAMLs (#73, #83, #9, #59)
- **26/10 dom · Fase E** — Invariantes (#135); cadeia C nos seis blocos e previsões do piloto no `val_tune` (#132); **EDA descritiva na coorte definitiva (#139)**; vacina e YAMLs (#84, #102, #29, #87)
- **27/10 seg · Fase E** — Perfil óbito × cura no treino (#137); sintomas de 2019 (#50); ablações (#54); **não supervisionado com one-hot (#136)**
- **28/10 ter · Fase E** — Completude (#52), subgrupos (#55) e região (#110) no `val_tune`; perfil dos clusters (#137); **ponto de decisão dos achados (#140)**
- **29/10 qua** — Ajuste fino e peso de classe (#1, #5); G6 (#78); calibração G7 (#79); importância (#91); marca de teste aberto (#26)
- **30/10 qui** — Corte global e por região, G8 (#80, #110); checklist e aprovação do G9 (#81); congelamento. Pessoa B volta à noite
- **31/10 sex** — Testes A e B e 2020–2022, uma única vez, de manhã (#2, #119); repetição no teste para o relatório (#55, #110, #52); interpretação (#91); âncora e excluídos (#56)
- **01/11 sáb** — Relatório completo (#133); slides (#134); reprodução independente (#126)
- **02/11 dom** — Conferência de números e ensaio (feriado: contingência)
- **03/11 seg** — Entrega

### Pessoas

- **A** — protocolo, regras, verificação, Fase E (EDA definitiva, perfil estatístico, completude), relatório e conferência de números (esforço estimado até 03/11: ≈ 55 h, o maior, porque é quem menos entregou até 24/10)
- **B** — interpretação, não supervisionado (leitura), figuras, relatório e apresentação; fora de 25 a 30/10 (≈ 32 h, concentradas de 31/10 a 02/11)
- **C** — artefato, pipeline, Fase E (clustering one-hot, subgrupos e região no `val_tune`), modelos, avaliação final e reprodução (≈ 49 h, concentradas até 31/10)
- **Equipe** — ponto de decisão da Fase E (#140) e aprovações de gates

### Caminho crítico

#10 → #131 → #135 → #132 → Fase E (#139, #137, #50, #54, #136, #52, #55, #110) → #140 → #1 → #78 → #79 → #80 → #81 → #2 → #119 → #133

### Aviso da revisão

> [!atenção] Replanejamento de 26/10: exploração antes da validação
> Com a troca para a coorte definitiva, todas as análises que podem mudar decisões rodam na **Fase E (26 a 28/10)**, sobre o `train_ref` e o `val_tune`, e são decididas no **#140** (28/10 à noite). Novos: #139 (EDA descritiva na coorte definitiva) e #140 (ponto de decisão). Antecipados: #136, #137, #52, #55, #110. Ajuste fino passa para 29/10 e o teste abre em 31/10 de manhã. Depois do teste, as análises só são repetidas para o relatório.

### Ajuda · Como ler a carga estimada

- O campo **carga** de cada card é o esforço estimado em horas de trabalho focado (arredondado). O "O que fazer" detalha a divisão quando há mais de uma pessoa.
- O total por pessoa (no quadro de Pessoas e no #72) considera o que cada um já entregou até 24/10: quem entregou menos recebe mais do que falta; quem viaja recebe pouco na viagem e compensa na volta.
- Estimativas não são prazos rígidos. Se uma tarefa passar do dobro do previsto, comente no card para redistribuir.

### Rodapé

Painel local de acompanhamento do projeto. O conteúdo vem de `PROJECT_STATUS_TEXT.md` e o estado compartilhado de `PROJECT_STATUS.md`, ambos publicados pelo painel direto no GitHub. Planejamento alinhado à Base de Conhecimento v9 (24/10/2026). Painel v5.1.

## Painel · textos gerais

### Título

Projeto SRAG · Pendências

### Subtítulo

Revisão de 24/10. Coorte definitiva publicada (3.884.728 notificações) e G1 aprovado; o caminho crítico agora é materializar o artefato com os seis blocos (#131), adaptar a cadeia C (#132), ajustar, calibrar, escolher o limiar e abrir os Testes A e B uma única vez. Treino em 2019, 2023, 2024 e 2025; Teste A nesses anos; Teste B em 2019–2025; 2020–2022 também isolado; 2026 só exploração. Entrega: **03/11/2026**.

### Entrega

03/11/2026

### Cronograma

- **24/10** — Reunião com professores (#95, #97); passagem de bastão (#72); regra do `group_id` (#10); funções de avaliação (#127, #23)
- **25/10** — `group_id` (#10) e artefato supervisionado v3 com seis blocos (#131); esqueleto do relatório (#133); decisões registradas (#73)
- **26/10** — Invariantes do protocolo no artefato real (#135); cadeia C nos seis blocos (#132); pilotos na coorte definitiva
- **27/10** — Ablações em `val_tune` (#54) e tuning curto (G6, #1); EDA de desfecho só no `train_ref` (#51)
- **28/10** — Calibração (G7, #79), limiar (G8, #80), medição em `val_meas`, importância (#91)
- **29/10** — Congelamento, tag e aprovação conjunta do G9 (#81)
- **30/10** — Testes A e B e 2020–2022 isolado, uma única vez (#2, #119)
- **31/10** — Interpretação, subgrupos, figuras e Resultados no relatório (#55, #91, #133)
- **01/11** — Relatório completo, apresentação e execução limpa (#126, #134)
- **02/11** — Revisão final e ensaio (feriado: dia de contingência)
- **03/11** — Entrega

### Legenda das estratégias

<div class="legend"><span class="tag e-desenvolver">▶ Desenvolver</span>necessário <span class="tag e-explorar">🔍 Explorar</span>opcional com prazo <span class="tag e-documentar">✎ Decidir/documentar</span>contrato e decisão <span class="tag e-despriorizar">⏸ Despriorizado</span>não entra antes da entrega</div>

### Como ler

Cada card é uma pendência. Dentro dele: **① Para entender** (o tema em linguagem simples, com números do projeto), **② Problema** (o que está errado, com detalhes técnicos), **③ O que fazer** (passos), **④ Ligações** (de quem depende e o que trava) e **⑤ Evidências** (commits, auditoria e histórico). Os números dos itens são fixos e mantêm seus números históricos; o item #108 foi removido por impossibilidade material de recuperar a gravação. Cada card mostra a data ideal mesmo quando fechado.

<div class="legend"><span class="tag" style="background:var(--p1);color:#fff">P1</span>bloqueia o próximo passo ou compromete resultados <span class="tag" style="background:var(--p2);color:#fff">P2</span>afeta a validade ou a defesa <span class="tag" style="background:var(--p3);color:#fff">P3</span>consistência e organização <span class="tag" style="background:var(--p4);color:#fff">P4</span>melhoria <span class="tag" style="background:var(--ok);color:#fff">✓</span>resolvida</div>

<div class="legend"><span class="tag blk">travado</span>depende de item ainda aberto <span class="tag rdy">pronto</span>pode começar já <span class="tag trv">trava N</span>quantos itens esperam por ele <span class="tag new">novo</span>surgiu na revisão de 18/10 <span class="tag mk">M3</span>marco lógico <span class="tag due">24/10</span>data ideal visível no card fechado <span class="tag pil">pilar</span>pilar do plano</div>

### Pessoas

- **A** — protocolo, decisões, documentação, relatório e conferência de números
- **B** — EDA, clustering, interpretação, figuras e apresentação (fora de 25/10 a 30/10)
- **C** — artefato de modelagem, pipeline, modelos, avaliação e reprodução
- **Equipe** — itens conjuntos e aprovações de gates

### Caminho crítico

#10 → #131 → #135 → #132 → #78 → #1 → #79 → #80 → #81 → #2 → #119 → #133

### Aviso da revisão

> [!atenção] Revisão de 24/10: o que mudou
> A coorte definitiva existe, mas ainda não há artefato de modelagem com `group_id` e os seis blocos: esse é agora o primeiro passo (#131, #132). A Pessoa B fica fora de 25/10 a 30/10; nenhum item do caminho crítico depende dela nesse período, e as transições estão descritas em cada card e no #72. Mudanças e motivos: `MUDANCAS_PLANO_2026-10-24.md`.

### Ajuda · Como usar (30 segundos)

- **Abrir:** dois cliques em `.srag-status-local\ABRIR_PAINEL.cmd`. Abre uma janela do terminal que fica aberta rodando o servidor; não feche enquanto usa. Se já estiver aberto, só abre a aba.
- **Marcar como feito:** a caixa aparece no **topo** do card assim que ele abre e de novo no **fim**; as duas são a mesma marcação.
- **Outras marcações:** concluir, reabrir, comentar ou confirmar/rejeitar uma sugestão: em ~8 s sai um commit curto só com os arquivos do painel, ex.: `(#status) #10 concluída · Mateus`. “▶ Estou fazendo” é só seu e não gera commit.
- **Editar o conteúdo:** botão ✎ no card (ou ➕ Nova pendência). A alteração vai para o `PROJECT_STATUS_TEXT.md` no mesmo tipo de commit curto, campo a campo. Também dá para editar o `PROJECT_STATUS_TEXT.md` direto no VS Code: o painel mostra a prévia em ~2 s.
- **Atualizar:** automático a cada hora e ao voltar para a aba. **⟳ Buscar** força agora e **nunca gera commit**. **🔎 Buscar + auditar** também varre o código e só gera commit se alguma pendência mudar.
- **Commits do dia a dia:** continue no VS Code. Escreva `tarefa 30`, `#30` ou `[done:#30]` na mensagem: o painel reconhece sozinho.

> [!ok] Por que o VS Code não reclama
> O painel **nunca** grava o `PROJECT_STATUS.md` na sua pasta de trabalho. Ele lê o arquivo direto do GitHub e publica o commit “por fora”. Assim o arquivo nunca aparece como modificado e o *pull* não dá erro. Quando a única novidade remota são os arquivos do painel e sua branch não tem commits locais, o painel ainda avança sua branch sozinho. Se encontrar uma versão antiga modificada do `PROJECT_STATUS.md` na pasta (versões anteriores do painel), ele guarda backup, converte as marcações em alterações do painel e devolve o arquivo ao estado do commit. O `PROJECT_STATUS_TEXT.md` é diferente: é seu para editar, e o painel só mexe nele na pasta quando você clica em “Publicar edições locais”.

> [!atenção] Quando sai commit
> Só quando há decisão: concluir, reabrir, comentar, confirmar/rejeitar sugestão, escolher num conflito, editar conteúdo pelo painel, ou quando a auditoria muda uma pendência. Buscar, ler commits, “Estou fazendo”, prévia de edições locais e resumo da auditoria nunca geram commit: cada painel lê o mesmo histórico do Git e chega ao mesmo resultado sozinho.

> [!atenção] Três pessoas ao mesmo tempo
> Cada clique vira uma alteração pequena (item + campo). Na hora de publicar, o painel busca a versão mais nova do GitHub e reaplica as suas alterações por cima. Itens ou campos diferentes nunca conflitam; comentários sempre somam. Se duas pessoas mudarem o **mesmo** campo (situação, título, uma seção…) para valores diferentes, vale o que chegou primeiro e a outra recebe um aviso aqui em cima para decidir. Push rejeitado por concorrência é refeito automaticamente; nunca usa `--force`. Sem internet, a fila fica guardada e sai sozinha depois.

### Ajuda · Instalação e atualização (uma vez por pessoa)

- **Único passo:** extrair o zip na **raiz do repositório** (a pasta que tem `src`, `configs` e `notebooks`) e aceitar substituir os arquivos de `.srag-status-local`. Depois, dois cliques em `.srag-status-local\ABRIR_PAINEL.cmd`.
- **O que o painel faz sozinho na primeira abertura:** fecha a versão antiga do painel, se estiver aberta (ela publica antes o que tinha na fila); usa o `.venv` do projeto, ou o Python do Windows; mantém sua fila, seus conflitos e suas marcações locais; e, se o `PROJECT_STATUS_TEXT.md` ainda não estiver no GitHub, publica-o uma única vez (quem abrir primeiro publica; os outros já encontram pronto).
- **Nada aparece no VS Code:** a pasta `.srag-status-local` tem um `.gitignore` próprio com `*` e nunca vai para o Git. O `PROJECT_STATUS_TEXT.md` chega pelo *pull* normal, como qualquer arquivo do projeto.
- **Nome antigo:** se sobrou um `PENDENCIAS.md` da versão 5.0 na pasta, o painel move para `backups/`. No GitHub, o nome antigo é removido no mesmo commit que publica o novo.
- **Requisitos:** os mesmos de sempre, isto é, Python 3 e a credencial do GitHub que o VS Code já usa.

### Ajuda · Como interpretar os estados

- **ABERTA:** sem evidência suficiente.
- **EM ANDAMENTO:** commit com `[progress:#ID]` ou commit que só cita a tarefa (lido por cada painel, sem commit). O “▶ Estou fazendo” aparece só para você.
- **RESOLVIDA — PENDENTE DE VALIDAÇÃO (a confirmar):** commit cita a tarefa com linguagem de conclusão (“tarefa 30 concluída”, “corrige #30”) ou a auditoria achou commit nos arquivos da tarefa, sem problema impeditivo. Um humano confirma com um clique.
- **PRECISA REVISÃO:** há implementação relacionada, mas a auditoria achou problema grave (notebook com erro salvo, sintaxe, JSON/YAML inválido, conflito de merge, teste falhando, possível vazamento).
- **CONCLUÍDA:** confirmação humana no painel ou marcador `[done:#ID]` no commit. Automação nunca conclui sozinha.
- **⚠ Reconfirmar:** item concluído cujos arquivos voltaram a apresentar problema. A conclusão não é apagada.
- **Situação editorial** (aberta, parcial, resolvida no `PROJECT_STATUS_TEXT.md`) é o que o texto do card descreve; a **situação compartilhada** acima é a que vale para o andamento. Um item concluído no painel aparece como resolvido mesmo que o texto ainda diga “aberta”.

### Ajuda · Marcadores reconhecidos nos commits

- `[done:#30]`, `[feito:#30]` → concluída. `[progress:#30]` → em andamento. `[reopen:#30]` → reaberta.
- `tarefa 30`, `tarefas 30, 31 e 32`, `item 30`, `pendência 30`, `task 30`, `#30` → com palavra de conclusão (corrige, implementa, resolve, conclui, finaliza, fecha, feito, pronto, fix, done…) vira “a confirmar”; sem ela, “em andamento”.
- “Merge pull request #N” é ignorado. Commits do próprio painel e commits que só mexem no `PROJECT_STATUS_TEXT.md` também (editar texto não conta como progresso).

### Ajuda · Editar o conteúdo (PROJECT_STATUS_TEXT.md)

- **Pelo painel:** ✎ Editar no card abre o editor com todos os campos e as seções em Markdown, com pré-visualização. Salvar enfileira só os campos que você mudou; o commit sai em ~8 s junto com outras marcações.
- **Pelo VS Code:** edite `PROJECT_STATUS_TEXT.md` na raiz do repositório e salve. O painel detecta em ~2 s, mostra a prévia com o selo “prévia local” e lista os itens alterados no topo. Depois faça commit e push normais, ou clique em **Publicar edições locais** (o painel publica só as suas diferenças, campo a campo, e devolve o arquivo da pasta ao estado do Git).
- **Item novo:** ➕ Nova pendência no painel (o número é definido na publicação, sem colisão) ou um novo `## #N · Título` no arquivo usando o próximo número livre.
- **Remover:** nunca apague a seção; use `- removido: motivo`. O número fica reservado e o card some da lista (filtro “Removidos” mostra).
- **Erros de formato** (número repetido, dependência inexistente, valor desconhecido) aparecem num aviso no topo; o painel continua funcionando com o resto.

### Ajuda · Se algo parecer errado

- Clique em **⟳ Buscar atualizações**. Nada é perdido: há fila local, backups em `.srag-status-local/backups` e todo o histórico no Git.
- Sugestão automática errada? Use **✗ Não é isso** no card: ela volta ao estado anterior e aquele commit não será usado de novo para o item.
- Marcou errado? Desmarque “feito”: a reabertura fica no histórico do card.
- Se o GitHub recusar (credencial), faça um *push* qualquer pelo VS Code uma vez para salvar a credencial e clique em Buscar.
- Painel sem texto ou desatualizado? Rode `.\.venv\Scripts\python.exe .srag-status-local\server.py gerar` para regenerar o `painel.html` a partir do `PROJECT_STATUS_TEXT.md`, e `... server.py validar` para listar problemas de formato.
- Diagnóstico: `DIAGNOSTICO.cmd` e o arquivo `.srag-status-local/logs/painel.log`.

### Rodapé

Painel local de acompanhamento do projeto. O conteúdo vem de `PROJECT_STATUS_TEXT.md` e o estado compartilhado de `PROJECT_STATUS.md`, ambos publicados pelo painel direto no GitHub. Painel v5.1.

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

## #10 · Regra definitiva para números de notificação repetidos

- prioridade: P1
- situação: parcial
- estratégia: documentar
- marco: M1
- data ideal: 25/10
- responsável: Pessoa A (regra, função e testes) · revisão: Pessoa C
- pessoas: A
- fonte: docs/decisoes.md §6; Plano v2 (A1, passo 5); B_07_supervisionado_pilotos (seção 7)
- depende de: —
- tags: Diverge do decidido, Decisão, Dados/Coorte, Partição
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 3
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

Cada documento manda tratar os números de notificação repetidos de um jeito. As decisões dizem para não escolher arbitrariamente a primeira ocorrência e manter registros diferentes. O plano diz para manter a primeira ocorrência com flag. O B_07 coloca em quarentena os grupos cujo identificador aparece em mais de um estrato (2 grupos, 4 linhas).

### ③ O que fazer

**Dono:** Pessoa A · **Prazo:** 25/10 (sábado), até as 12h · **Esforço estimado:** ≈ 3 h · **Revisão:** Pessoa C (só o commit, 15 min)

> [!atenção] Bloqueia o caminho crítico
> O #131 só começa quando a função deste item estiver no `main`. Se às 12h de 25/10 ela não estiver pronta, a Pessoa C usa a lógica que já existe no B_07 e a Pessoa A substitui depois (o resultado precisa ser idêntico).

#### Objetivo
Transformar a regra de grupo, que hoje existe só dentro do B_07 com o rótulo "quarentena_provisoria", numa função oficial, testada e documentada, que o #131 vai chamar para montar a partição.

#### A regra (decisão D-06 da base v9, já aplicada na partição de 24/10)
1. `group_id` = `nu_notific` sem espaços no começo e no fim.
2. Quando `nu_notific` estiver vazio (nulo ou texto vazio), `group_id` = `"sem_notific:" + str(id_registro)`. Assim cada linha sem número vira um grupo próprio e nunca se junta a outra por acaso.
3. Linhas com o mesmo `nu_notific` **não são apagadas nem fundidas**. Ficam no mesmo grupo e, portanto, sempre caem no mesmo bloco (treino, validações ou teste). Isso impede que o modelo treine com uma ficha e seja testado com a "irmã".
4. Um grupo "cruza períodos" quando tem linhas em mais de uma janela: desenvolvimento (2019, 2023–2025), pandemia (2020–2022) ou exploração (2026). Esse grupo não cabe em bloco nenhum e sai do artefato de modelagem. Na partição de 24/10 foram **4 linhas**.

#### Passo a passo
1. Abra `src/protocolo/verificacoes.py` (é o módulo de regras de protocolo que você já mantém). Procure no PROJECT_COMPLETE_REFERENCE se já existe alguma função com "group" ou "grupo" no nome; se existir, estenda em vez de criar outra.
2. Crie duas funções, com docstring em português e tipos:
   - `criar_group_id(df, coluna_notificacao="nu_notific", coluna_id="id_registro") -> pd.Series` devolve uma série de texto com o mesmo índice do `df`.
   - `grupos_que_cruzam_janelas(df, coluna_grupo="group_id", coluna_ano="ano_internacao") -> pd.DataFrame` devolve uma linha por grupo problemático, com as colunas `group_id`, `anos` (lista), `n_linhas` e `janelas` (lista com "desenvolvimento", "pandemia" ou "exploracao").
3. As janelas devem vir do YAML, não de anos escritos à mão: leia `temporal.blocos` com `C.cfg("temporal", "blocos")`. train_ref define os anos de desenvolvimento, test_pandemic os anos de pandemia e 2026 é exploração.
4. Em `tests/test_regras_pessoa_a.py`, escreva três testes com um DataFrame pequeno criado no próprio teste (5 a 8 linhas):
   - (a) duas linhas com o mesmo `nu_notific` recebem o mesmo `group_id`;
   - (b) duas linhas com `nu_notific` vazio recebem `group_id` diferentes;
   - (c) um grupo com uma linha de 2021 e outra de 2023 aparece em `grupos_que_cruzam_janelas`, e um grupo só de 2023 não aparece.
5. Rode `.\.venv\Scripts\python.exe -m pytest tests/test_regras_pessoa_a.py -q` e confira que os três passam.
6. Commit com a mensagem `feat: regra oficial de grupo de notificação [progress:#10]` e avise no card do #131 com o nome das funções.
7. Em `docs/decisoes.md` §6, acrescente um parágrafo datado (24/10) com a regra acima, o motivo ("evitar vazamento entre blocos sem descartar dados arbitrariamente") e a contagem de 4 linhas. Quando o #135 confirmar a contagem no artefato real, atualize o número se mudar.

#### Como validar
- Os três testes passam.
- Aplicada à coorte definitiva pelo #131, a função produz exatamente as 4 linhas em grupos que cruzam períodos (o mesmo número da partição de 24/10). Se der outro número, comente no card antes de seguir.

#### Pronto quando
A função e os testes estiverem no `main`, o #131 estiver usando a função e a §6 do `decisoes.md` estiver atualizada.

#### Se der errado
Se não conseguir terminar até as 12h de 25/10, deixe no card até onde chegou. A Pessoa C segue com a lógica do B_07 e você termina a função até 26/10; o #135 vai conferir se as duas dão o mesmo resultado.

## #131 · Levar para o src o artefato de seis blocos que o B_07 já gera (group_id, região, partição, leitura protegida)

- prioridade: P1
- situação: parcial
- estratégia: desenvolver
- marco: M2
- data ideal: 25/10
- responsável: Pessoa C (dona; revisão cruzada sem edição concorrente)
- pessoas: C
- fonte: Revisão de 24/10: referência do projeto (commit baee782), configs/supervised.yaml, src/data/split.py, src/data/supervised_artifact.py
- depende de: #10
- tags: Dados/Coorte, Partição, Código, Gate, Vazamento
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 6
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

Sem esse artefato, nada do supervisionado roda na coorte definitiva: os notebooks C ainda leem o artefato **provisório**, com a divisão antiga (que incluía 2020–2022 em treino). É o primeiro passo do caminho crítico, e dele dependem tuning, calibração, limiar e testes.

### ③ O que fazer

**Dono:** Pessoa C · **Prazo:** 25/10 (sábado) · **Esforço estimado:** ≈ 6 h · **Começa quando:** função do #10 no main (ou, se atrasar, lógica do B_07)

#### Objetivo
Levar para o `src` o que o B_07 já faz em notebook e deixar um único comando que qualquer pessoa roda para gerar o artefato de seis blocos a partir de `data/analytical/coorte_final.parquet`.

#### Passo a passo
1. **Leitura enxuta.** Leia só as colunas necessárias: entradas de `features.engenharia.entradas`, as 31 de `features.final`, as 4 de `contexto_incremental`, as 2 de `sensibilidade_gravidade_admissao`, `alvo_obito_srag`, `sg_uf`, `nu_notific`, `id_registro`, `nosocomial`, `dt_interna`. Use `read_srag(..., compactar=True)` ou `pd.read_parquet(columns=...)` e converta textos repetidos para `category`. Registre o tamanho em memória com `Monitor`.
2. **Features:** `montar_features` uma única vez. Não copie o DataFrame inteiro depois disso.
3. **Região:** crie `regiao_residencia(sg_uf)` em `src/features/engineering.py`. Mapeamento fixo: Norte AC AP AM PA RO RR TO; Nordeste AL BA CE MA PB PE PI RN SE; Centro-Oeste DF GO MT MS; Sudeste ES MG RJ SP; Sul PR RS SC; vazio ou inválido → `AUSENTE`. Teste com as 27 UFs e com um valor inválido.
4. **Grupo:** `criar_group_id` do #10; depois `grupos_que_cruzam_janelas`, removendo essas linhas e guardando a contagem.
5. **Partição:** `criar_particao_mestra(seed=42, ...)` lendo `temporal.blocos` do YAML. A coluna de grupo passa a se chamar **`group_id`** (o B_07 usava `grupo_split`; unifique).
6. **Vocabulário em `src/data/supervised_artifact.py`:**
   - `ALLOWED_PARTITIONS` = `train_ref`, `val_tune`, `val_cal`, `val_meas`, `test_ref`, `test_pandemic`, `exploracao`;
   - leitura padrão (sem `partitions=`) = os quatro blocos de desenvolvimento;
   - `test_ref` e `test_pandemic` exigem `G9_holdout` aprovado (mesmo mecanismo de `exigir_gate` usado hoje para "teste");
   - `exploracao` exige `exploracao_2026.ativa: true`;
   - a coluna `particao` guarda o bloco real (sem a visão agregada treino/validacao/teste).
7. **Persistir:** `persist_supervised_artifact(..., cohort_kind="final")` com `numeric_columns` e `categorical_columns` do YAML e, em `audit_columns`, `group_id`, `ano_internacao`, `regiao_residencia`, `sg_uf`, `faixa_etaria`, `sexo_categoria`, `nosocomial`, contexto e gravidade. O manifesto registra caminho e SHA-256 da coorte de origem.
8. **Arquivos de partição:** salve `data/analytical/partitions_master.parquet` (`id_registro`, `group_id`, `particao`) e `data/analytical/manifesto_particao.json` (linhas, grupos, anos, prevalência, distribuição por região e hash por bloco, além do fallback de estratificação usado e da contagem de linhas excluídas).
9. **Comando único:** uma função `gerar_artefato_supervisionado(root)` e uma entrada de linha de comando (ou uma célula curta no início do C_11) para quem não tem o artefato. Ela deve rodar do zero a partir de `coorte_final.parquet` em menos de alguns minutos.
10. **Liberar memória:** depois de persistir, `del` nos DataFrames grandes e `gc.collect()`.
11. **Testes rápidos** com dados sintéticos em `tests/test_supervised_artifact.py`: leitura padrão não devolve teste; pedir `test_ref` com G9 pendente levanta `GatePendenteError`; com G9 aprovado via `monkeypatch`, devolve. Rode a suíte rápida.
12. **Avise no card do #135** e cole uma tabela bloco × (linhas, grupos, prevalência). Ela deve bater com a tabela do "Para entender", exceto por diferenças explicadas.

#### Como validar
- `.\.venv\Scripts\python.exe -m pytest -m "not slow" -q` passa.
- Os números por bloco batem com os de 24/10 (diferença zero ou explicada).
- O C_11 consegue carregar `train_ref` sem carregar o teste.

#### Pronto quando
A função de geração estiver no `src`, o artefato e os dois arquivos de partição existirem, o manifesto tiver `test_opened: false` e o #135 confirmar as invariantes.

#### Se der errado
Prioridade absoluta: passos 5 a 8 (partição e artefato com seis blocos). Região como função e o comando único podem ficar para a manhã de 26/10. Nenhum ajuste fino começa sem o #135.

## #135 · Testes das invariantes do protocolo no artefato v3 (§28.4)

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M2
- data ideal: 26/10
- responsável: Pessoa A (dona; revisão cruzada sem edição concorrente)
- pessoas: A
- fonte: Revisão de 24/10 (rebalanceamento): docs/decisoes.md §28.4; configs/supervised.yaml (temporal.invariantes)
- depende de: #131
- tags: Partição, Vazamento, Testes, Gate
- pilar: Valor científico-acadêmico
- carga: 3
- novo: sim
- professores: não
- arquivos: tests/test_regras_pessoa_a.py, src/protocolo/verificacoes.py

### ① Para entender

A §28.4 das decisões só considera o protocolo implementado quando testes automáticos provarem, **no artefato real**, que nenhum grupo cruza blocos e que os anos proibidos não entram no desenvolvimento. É a auditoria final do desenho, antes de qualquer tuning.

### ② Problema

A função de partição foi testada só com dados sintéticos. Ninguém conferiu ainda o artefato gerado sobre a coorte definitiva.

### ③ O que fazer

**Dono:** Pessoa A · **Prazo:** 26/10 (domingo) · **Esforço estimado:** ≈ 3 h · **Revisão:** Pessoa C · **Começa quando:** aviso da Pessoa C no #131 de que o artefato existe

#### Objetivo
Provar, com testes automáticos rodando **no artefato real**, que o desenho do estudo foi respeitado. É a "auditoria final" do protocolo antes de qualquer ajuste de modelo. Sem isso, a §28.4 do `decisoes.md` não pode ser marcada como cumprida.

#### O que é uma invariante
Uma regra que tem de ser verdadeira em qualquer versão do artefato. Se falhar, há erro no artefato, e não "um resultado diferente".

#### Passo a passo
1. Em `tests/test_regras_pessoa_a.py`, crie uma classe `TestInvariantesArtefato` marcada com `@pytest.mark.slow`. No começo, se `data/analytical/dataset_supervisionado.parquet` não existir, use `pytest.skip("artefato ausente")`, para não quebrar a suíte de quem não tem os dados.
2. Leia **só** quatro ou cinco colunas: `pd.read_parquet(caminho, columns=["particao", "group_id", "ano_internacao", "alvo_obito_srag", "dias_sintomas_ate_internacao"])`. Nunca carregue as features. Isso deixa o teste leve (poucos segundos).
3. Escreva um teste para cada invariante:
   - (a) cada `group_id` aparece em um único bloco: `df.groupby("group_id")["particao"].nunique().max() == 1`;
   - (b) 2020, 2021 e 2022 só aparecem em `test_pandemic`;
   - (c) 2026 só aparece em `exploracao`;
   - (d) `test_pandemic` só tem 2020–2022;
   - (e) nos anos de desenvolvimento, as frações dos blocos ficam a no máximo 0,5 ponto percentual de 70%, 5%, 5%, 5% e 15%;
   - (f) a prevalência de cada bloco de desenvolvimento fica a no máximo 0,5 ponto percentual da prevalência conjunta desses anos (≈ 8,44%);
   - (g) `dias_sintomas_ate_internacao` está entre 0 e 60 em todas as linhas (garantido pelo contrato da coorte);
   - (h) o SHA-256 do arquivo é igual ao do manifesto (use a função de hash que já existe em `src/utils/hashing.py`).
4. Rode `.\.venv\Scripts\python.exe -m pytest -m slow tests/test_regras_pessoa_a.py -q` e cole a saída no card.
5. **Contagens para o relatório:** num script curto (`tools/contagens_protocolo.py`, ou uma célula de notebook seu), gere `outputs/final/contagens_protocolo.csv` com: número de `nu_notific` com mais de uma linha (#46); `idade_anos` vazia por bloco (#47); linhas removidas por grupo que cruza períodos (#10). Leia só as colunas necessárias.
6. Marque na §28.4 do `docs/decisoes.md` os dois critérios que faltavam ("anos proibidos" e "grupos cruzando blocos"), com a data e o comando do teste.

#### Como validar
Os oito testes passam; o CSV existe e os números batem com o manifesto de partição.

#### Pronto quando
Testes passando no artefato real, CSV salvo e §28.4 atualizada.

#### Se algum teste falhar
Não corrija o artefato você mesma(o). Cole no card do #131 o nome do teste, a mensagem de erro e o número de linhas afetadas. O ajuste fino não começa até a Pessoa C corrigir.

## #132 · Adaptar a cadeia C_11–C_16 aos seis blocos (train_ref, val_tune, val_cal, val_meas)

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M2
- data ideal: 26/10
- responsável: Pessoa C (dona; revisão cruzada sem edição concorrente)
- pessoas: C
- fonte: Revisão de 24/10: notebooks C_11–C_16 na referência (commit baee782)
- depende de: #131
- tags: Código, Notebook, Partição, Modelagem, Vazamento
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 8
- novo: sim
- professores: não
- arquivos: notebooks/C/C_11_pipeline_supervisionado.ipynb, notebooks/C/C_12_baseline_logistica.ipynb, notebooks/C/C_13_boosting.ipynb, notebooks/C/C_15_calibracao_limiar.ipynb, notebooks/C/C_16_validacao_final.ipynb

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

Os notebooks C ainda usam o vocabulário `treino`/`validacao`/`teste` (12 ocorrências de cada na referência de 24/10). O C_15 divide a validação em duas metades por conta própria, e o C_16 escolhe manifesto pela data do arquivo. Rodar a cadeia assim na coorte definitiva quebraria o protocolo das duas janelas.

### ③ O que fazer

**Dono:** Pessoa C · **Prazo:** 26/10 (domingo) · **Esforço estimado:** ≈ 6 h · **Começa quando:** #131 e #135

#### Objetivo
Fazer a cadeia oficial (C_11 a C_16) usar os seis blocos, cada um com seu papel, sem gambiarras antigas. É o que garante que nenhuma escolha seja feita com dados que depois servem para medir.

#### Passo a passo por notebook
1. **C_11 (pipeline):** carregar `train_ref` e uma amostra de 10 mil de `val_tune` com `load_supervised_artifact(partitions=(...))`. Montar o pré-processador com as listas do manifesto (#15). Imprimir no topo: SHA-256 do artefato, SHA-256 do YAML e commit. Não salvar `preprocessor.joblib` (#43).
2. **C_12 (baseline e logística):** treinar em `train_ref`, medir em `val_tune`. Tabela com PR-AUC, PR-AUC ÷ prevalência, ROC-AUC, Brier e o Brier do modelo nulo (`p × (1 − p)`), para que o leitor tenha a referência ao lado.
3. **C_13 (boosting e busca):** prepara a busca do #1 só em `val_tune`; ainda não roda a busca.
4. **C_15 (calibração e limiar):** apagar `HONEST_CALIB_SPLIT` e qualquer divisão interna da validação. Calibrador ajustado em `val_cal`; limiar escolhido em `val_cal`; medição final em `val_meas` sem decidir nada com ela (#58). No fim, gravar no YAML `selecao_modelos.finalista_escolhido`, `run_id_finalista`, `calibracao.metodo` e `limiar.*` (fecha #28).
5. **C_16 (avaliação final):** abrir os testes só por `load_supervised_artifact(partitions=("test_ref", "test_pandemic"))` (#16); localizar o manifesto pelo `run_id_finalista`, e não pela data do arquivo (#27); chamar `marcar_teste_aberto` do #26 logo depois de carregar os testes. Não rodar agora.
6. **Busca de regressão:** procurar nos notebooks C pelos textos `"validacao"`, `"teste"`, `HONEST_CALIB_SPLIT`, `st_mtime` e anos escritos à mão (`2019`, `2020`…). Tudo deve vir do YAML ou do manifesto.
7. **Ensaio da cadeia:** rodar C_11 → C_15 numa amostra de 2% do artefato (por grupo), de ponta a ponta, antes de rodar com tudo. Reaproveitar o C_02 se for mais rápido.
8. Rodar de verdade C_11, C_12 e C_13 (sem busca) e salvar com saídas.

#### Como validar
- A busca do passo 6 volta vazia.
- C_11 a C_13 rodam na coorte definitiva com saídas salvas.
- As métricas do C_12 ficam próximas às do piloto de 24/10 (logística PR-AUC ≈ 0,30; ROC-AUC ≈ 0,85). Diferença grande é sinal de erro.

#### Pronto quando
A cadeia roda sem tocar o teste e com cada bloco no seu papel.

#### Se der errado
Prioridade: C_11, C_12 e C_13 (destravam as ablações e o G6). C_15 e C_16 podem ser adaptados em 27/10 de manhã.

#### Acréscimo do replanejamento de 26/10: previsões do piloto para a Fase E
9. Depois do C_12 e do C_13 (sem busca), exporte `outputs/final/predicoes_val_tune_piloto.parquet` com: `id_registro`, `group_id`, `ano_internacao`, `regiao_residencia`, `sg_uf`, `faixa_etaria`, `sexo_categoria`, `y`, `prob_logistica`, `prob_boosting` (probabilidades brutas, sem calibração). Avise no #52, #55 e #110. É o que permite as análises de subgrupo, região e completude **antes** do ajuste fino. ≈ 30 min.

## #139 · Fase E: EDA descritiva na coorte definitiva (B_06 parte A apontando para coorte_final)

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M3
- data ideal: 26/10
- responsável: Pessoa A (executa com roteiro) · Pessoa B (revisa ao voltar)
- pessoas: A, B
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

**Dono:** Pessoa A · **Prazo:** 26/10 (domingo) · **Esforço estimado:** ≈ 3 h (parte é tempo de máquina) · **Revisão:** Pessoa B ao voltar (31/10)

#### Objetivo
Rodar a parte descritiva do B_06 na coorte definitiva, sem alterar a lógica do notebook, e registrar o que mudou em relação à provisória.

#### Passo a passo
1. `git pull` (o commit `fd7dcaa` da Pessoa B atualizou contrato temporal, dicionário e EDA). Confira se a coorte definitiva existe na sua máquina; se não, gere pelo CLI (`.\.venv\Scripts\python.exe -m src.data.final_cohort_cli` seguindo o README) e confira o SHA-256 com `coorte_final.manifest.json` (começa com `87f28d39`).
2. Abra `notebooks/B/B_06_eda_temporal_clustering.ipynb`. Na célula de carregamento, confirme que a fonte é `data/analytical/coorte_final.parquet` (procure por `coorte_provisoria_b` e por `SRAG_COHORT_KIND`; com `SRAG_COHORT_KIND=final` o loader `cohort_source` usa a definitiva). Se precisar mudar algo além disso, **não edite**: comente no card e a Pessoa C ajusta.
3. Rode **só as seções da parte A** (até antes de "A ideia do clustering"): volume e óbito por ano, idade e sexo, sim/não/ignorado/ausente, sintomas e comorbidades por ano, vacinação, escolaridade e UF, rupturas temporais, série mensal. **Não rode** as seções de desfecho (óbito por característica) nem o clustering.
4. Confira na primeira saída: "Tipo efetivo: final" e dimensão com 3.884.728 linhas. Se aparecer 3.915.136, a fonte ainda é a provisória: pare e comente.
5. Salve o notebook com as saídas.
6. Monte `outputs/final/eda_definitiva_vs_provisoria.csv` com, por ano: fichas, % de óbito, % de branco em `perd_olft`, `perd_pala`, `fadiga`, `dispneia`, mediana de idade e mediana de dias até internar, nas duas coortes (os números da provisória estão em `outputs/tables/eda_02_*` de 24/10).
7. Comente no card as três maiores diferenças (em pontos percentuais) e se alguma muda uma decisão (ex.: os três sintomas deixarem de estar 99% em branco em 2019).

#### Pronto quando
B_06 parte A salvo com saídas da coorte definitiva, o CSV comparativo existir e o comentário estiver no card.

#### Se der errado
Erro de memória: feche outros programas e rode de novo; se persistir, comente no card com a célula e a mensagem. A Pessoa C decide se usa leitura projetada.

## #140 · Fase E: ponto de decisão dos achados exploratórios (28/10 à noite)

- prioridade: P1
- situação: aberta
- estratégia: documentar
- marco: M3
- data ideal: 28/10
- responsável: Pessoa A (conduz e registra) + Pessoa C + Pessoa B (por mensagem)
- pessoas: A, C, Equipe
- fonte: Replanejamento de 26/10
- depende de: #139, #137, #50, #54, #136, #52, #55, #110
- tags: Decisão, Metodologia, Gate
- pilar: Valor científico-acadêmico
- carga: 2
- novo: sim
- professores: não

### ① Para entender

A Fase E existe para que descobertas na base nova **possam mudar o plano**. Este card é o momento em que isso acontece: antes do ajuste fino (G6), a equipe olha todos os achados juntos e decide o que muda. Depois do G6, mudanças de variáveis ou de representação ficam muito caras; depois do G9, ficam proibidas.

### ② Problema

Sem um ponto de decisão explícito, os achados exploratórios viram só "texto de relatório" e não influenciam o modelo, que é justamente o risco que o replanejamento quer evitar.

### ③ O que fazer

**Dono:** Pessoa A (conduz) · **Prazo:** 28/10, até as 21h · **Esforço estimado:** A ≈ 1 h 30 · C ≈ 30 min · B ≈ 15 min (mensagem)

#### Antes (cada dono comenta no próprio card até as 18h de 28/10)
Três linhas por análise: o que encontrou, quão grande é o efeito e se sugere mudança.

#### Roteiro de decisão (a Pessoa A preenche esta tabela neste card)
| Análise | Pergunta de decisão | Opções | Padrão se não houver consenso |
|---|---|---|---|
| EDA definitiva (#139) | Algo mudou o suficiente para rever variáveis ou faixas? | manter · ajustar | manter |
| Sintomas de 2019 (#50) | Retirar `perd_olft`, `perd_pala`, `fadiga`? | manter · retirar | critério objetivo do #50 |
| Ablações (#54) | Algum bloco extra (gravidade, contexto, região, sazonalidade) muda a narrativa? | só relatório · reabrir G1 | só relatório |
| Perfil óbito × cura (#137) | Alguma variável com efeito grande que não está no modelo, ou efeito estranho que indique erro de dado? | nada · investigar | nada |
| Completude (#52) | O desempenho sobe muito com a completude da ficha (viés de documentação)? | só limitação · testar modelo sem comorbidades em branco | só limitação |
| Subgrupos (#55) | Alguma faixa etária, sexo ou ano com calibração muito ruim (O/E fora de 0,8–1,2)? | só relatório · calibrar por faixa (sensibilidade) | só relatório |
| Região (#110) | Diferença grande de desempenho ou calibração entre regiões? | corte por região (já previsto) · só relatório | corte por região |
| Não supervisionado (#136) | Os grupos novos revelam perfis além da idade? Algum achado sugere variável derivada? | só relatório · nova ablação | só relatório |

#### Depois
1. A Pessoa A registra as decisões no `docs/decisoes.md` (#73) com data e motivo.
2. Se alguma decisão mudar variáveis: a Pessoa C atualiza o YAML antes de começar o #1, e a Pessoa A atualiza `variaveis_finais.csv` (#40).
3. A Pessoa B confirma por mensagem ("de acordo" ou objeção em uma linha).

#### Pronto quando
A tabela estiver preenchida com a decisão de cada linha, registrada no `decisoes.md`, e o YAML refletir as mudanças (se houver).

## #72 · Quem é responsável pelos próximos passos (passagem de bastão de 24/10)

- prioridade: P1
- situação: aberta
- estratégia: documentar
- marco: M0
- data ideal: 24/10
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

**Dono:** Pessoa B (registra) + Equipe · **Prazo:** 24/10 à noite · **Esforço estimado:** ≈ 1 h

#### Objetivo
Deixar claro quem faz o quê de 25/10 a 03/11, para ninguém ficar parado esperando a Pessoa B, que fica fora de 25 a 30/10 (volta no fim do dia 30).

#### Princípios da distribuição
- **Um dono por arquivo e por notebook.** Quem não é dono comenta no card, não edita.
- **Carga estimada equilibrada no total do projeto.** A divisão leva em conta o que cada pessoa já entregou até 24/10. Quem entregou menos até aqui recebe mais do que falta; quem viaja recebe pouco durante a viagem e compensa depois.
- **Toda tarefa entra na frente de quem recebe** (protocolo e verificação; análise e interpretação; código central e integração).

| Pessoa | Frente | Esforço estimado até 03/11 | Quando concentra |
|---|---|---|---|
| A | Protocolo, regras, verificação, relatório e conferência de números | ≈ 55 h | Distribuído de 25/10 a 02/11 |
| B | Exploração, não supervisionado, interpretação, figuras e apresentação | ≈ 32 h | Leve de 25 a 30/10 (leitura e rascunhos no tablet); forte de 31/10 a 02/11 |
| C | Artefato, pipeline, modelos, avaliação final e reprodução | ≈ 49 h | Forte até 30/10; revisão técnica de 31/10 a 02/11 |

Somando o já entregue (commits de código até 24/10: B 81, C 81, A 12) com o estimado até 03/11, o esforço total fica o mais próximo possível entre as três pessoas dentro do que cada frente comporta. As horas de cada item estão no "O que fazer" de cada card.

> [!decisão] Replanejamento de 26/10
> As análises que podem mudar decisões foram antecipadas para a Fase E (26 a 28/10), antes do ajuste fino, e são feitas pelas Pessoas A e C. A Pessoa B fica com a interpretação, a repetição no teste para o relatório e a apresentação a partir de 31/10. O teste abre em 31/10 de manhã (um dia depois do plano anterior).

#### O que muda de mãos (quadro oficial)
| Assunto | Dono | Itens |
|---|---|---|
| Regra de grupo, invariantes, marca de teste aberto, checklist do G9, referência do projeto | Pessoa A | #10, #135, #26, #81, #130 |
| Perfil estatístico (qui-quadrado e ANOVA) e EDA de desfecho só no treino | Pessoa A | #137, #51 |
| Decisões, YAML de decisões, dicionário, `variaveis_finais.csv` | Pessoa A | #73, #102, #29, #70, #40, #9, #83, #84 |
| Tabelas de âncora e excluídos, falsos negativos, reprodução independente | Pessoa A | #56, #55 (parte), #126 (parte) |
| Artefato de seis blocos, cadeia C, ablações, ajuste, calibração, limiar, testes finais | Pessoa C | #131, #132, #54, #50 (parte), #1, #5, #78, #79, #80, #2, #119 |
| Funções de avaliação (bootstrap pareado, métricas por grupo) | Pessoa B (hoje); Pessoa C se não ficarem prontas até 25/10 | #127, #22, #23 |
| Representação one-hot do não supervisionado e nova rodada de agrupamento | Pessoa C executa na Fase E (27/10); Pessoa B interpreta (31/10) | #136 |
| Fase E antes do ajuste: EDA definitiva, completude, subgrupos e região no `val_tune`, ponto de decisão | Pessoas A e C | #139, #52, #55, #110, #140 |
| Repetição no teste para o relatório, interpretação, tabelas de âncora e excluídos, literatura, slides | Pessoa B | #55, #110, #52, #91, #57, #56, #112, #134 |

#### O que a Pessoa B deixa hoje (24/10)
1. Este card publicado e avisado no grupo.
2. Resumo da orientação no #95 (feito nesta revisão).
3. As funções do #127, #22 e #23, ou um comentário dizendo exatamente onde parou.

#### Como decidir sem a Pessoa B
Pergunta binária no card do item, com prazo. Sem resposta em 24 h, vale o padrão escrito no próprio card. O G9 é aprovado com duas pessoas.

#### Pronto quando
O quadro estiver publicado e as três pessoas tiverem comentado "ok" no card.

## #82 · Decidir o que fazer com intervalos impossíveis entre sintomas e internação

- prioridade: P2
- situação: resolvida
- estratégia: resolvida
- marco: M1
- data ideal: Concluído
- responsável: Pessoa A (dona; revisão cruzada sem edição concorrente)
- pessoas: A
- fonte: configs/supervised.yaml (features.engenharia.intervalo_politica); docs/decisoes.md
- depende de: —
- tags: Decisão, Features, Dados/Coorte
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 3
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

> [!ok] Resolvida pela coorte definitiva
> O contrato `final_cohort_v1` excluiu intervalos negativos (`D_COORTE_006`) e acima de 60 dias (`D_COORTE_007`). Na coorte de modelagem, o intervalo está sempre entre 0 e 60; o #135 testa isso.

**O que sobrou foi para outros itens:** a correção da §8 está no #73; a tabela por `nosocomial` (quantos dos intervalos negativos eram casos hospitalares) virou passo do #56, porque usa a mesma leitura da fonte.

## #83 · Definir o que a sensibilidade "com e sem indicadores de ausência" vai comparar

- prioridade: P3
- situação: aberta
- estratégia: documentar
- marco: M1
- data ideal: 25/10
- responsável: Pessoa A · revisão: Pessoa C
- pessoas: A
- fonte: configs/supervised.yaml (sensibilidades.com_sem_indicadores_ausencia); docs/decisoes.md
- depende de: —
- tags: Decisão, Metodologia, Features
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1
- novo: não
- professores: não

### ① Para entender

No modelo, um campo em branco vira a categoria `AUSENTE`. Na prática, isso já é um "indicador de ausência". Por isso a comparação "com e sem indicadores" prevista no YAML não compara nada hoje.

> [!exemplo] Exemplo
> Duas fichas iguais: uma com diabetes "não", outra em branco. O modelo vê `diabetes_nao` e `diabetes_AUSENTE` como coisas diferentes, e aprende com essa diferença.

Isso importa porque, no clustering, a ausência foi o que mais separou os grupos (item 52).

### ② Problema

Falta definir o que a sensibilidade de ausência vai comparar, já que a categoria `AUSENTE` já leva a informação de ausência ao modelo principal. Sem essa definição, o item 11 não pode ser implementado.

### ③ O que fazer

**Dono:** Pessoa A · **Prazo:** 25/10 · **Esforço estimado:** ≈ 1 h · **Revisão:** Pessoa C

#### Objetivo
Desligar uma análise que não compara nada e trocar por outra que responde a pergunta certa.

#### Por quê
O modelo já transforma campo vazio na categoria `AUSENTE`. Uma versão "com indicadores de ausência" seria praticamente igual à versão sem. A pergunta que importa é outra: **o modelo está aprendendo o hábito de preenchimento (fichas de óbito são mais completas) em vez da doença?** Ela é respondida pelo #52, que mede o desempenho por completude da ficha.

#### Passo a passo
1. Em `configs/supervised.yaml`, mude para `false` as duas chaves: `features.sensibilidade_indicadores_ausencia.ativa` e `sensibilidades.com_sem_indicadores_ausencia.ativa`. Acima de cada uma, um comentário: `# desativada em 24/10: AUSENTE já carrega a informação; ver análise de completude (#52)`.
2. Rode `.\.venv\Scripts\python.exe -m pytest tests/test_config.py -q`.
3. Peça revisão da Pessoa C no card e faça o commit.
4. A entrada no `decisoes.md` está no #73 (item 6).
5. Marque o #11 como concluído (ele dependia desta decisão).

#### Pronto quando
As duas chaves estiverem `false`, os testes passarem e o #11 estiver fechado.

## #84 · Definir quais doses de vacina contam como anteriores à internação

- prioridade: P3
- situação: aberta
- estratégia: documentar
- marco: M3
- data ideal: 26/10
- responsável: Pessoa A (regra e derivação) · revisão: Pessoa C
- pessoas: A
- fonte: docs/decisoes.md §17; configs/dicionario_variaveis_v1.csv
- depende de: —
- tags: Decisão, Features, Dados/Coorte
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 3
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

Falta a regra que define quais doses de vacina contam como anteriores à admissão, considerando os registros de vacina contra COVID-19 em 2019 e 2020 e as datas de dose ausentes ou posteriores à internação. A derivação do item 45 e a decisão do G1 sobre `vacina_cov` dependem dessa regra.

### ③ O que fazer

**Dono:** Pessoa A · **Prazo:** 26/10 · **Esforço estimado:** ≈ 3 h · **Revisão:** Pessoa C

#### Objetivo
Criar uma versão confiável da vacinação contra COVID-19 para a ablação de contexto (#54). A variável bruta tem erros impossíveis (55 "sim" em 2019 e 24.284 em 2020, antes de a vacina existir) e não diz se a dose foi antes da internação.

#### A regra
| Situação | Valor |
|---|---|
| Alguma data entre `dose_1_cov`, `dose_2_cov`, `dose_ref`, `dose_2ref`, `dose_adic` ≤ `dt_interna` | `sim` |
| `vacina_cov` = 2 | `nao` |
| `vacina_cov` = 1 e `dt_interna` antes de 17/01/2021 (início da vacinação no Brasil) | `inconsistente` |
| `vacina_cov` = 1 e nenhuma data válida | `sem_data` |
| Todo o resto (9, vazio, só datas depois da internação) | `AUSENTE` |

Para a vacina da gripe (`vacina`), mesma lógica com `dt_ut_dose`.

#### Passo a passo
1. Em `src/features/engineering.py` (confira antes no PROJECT_COMPLETE_REFERENCE se já existe algo parecido), crie `derivar_vacina_cov_antes_admissao(df) -> pd.Series` com tipo `category`. As datas chegam como texto: converta com `pd.to_datetime(..., errors="coerce")`.
2. Teste em `tests/test_features.py` com um DataFrame de 6 linhas, uma por linha da tabela acima, mais uma com dose depois da internação (deve virar `AUSENTE`).
3. Rode o teste. Peça revisão da Pessoa C.
4. Num script curto, conte quantas linhas caem em cada categoria por ano, só no `train_ref`. Salve em `outputs/final/vacina_categorias_por_ano.csv`. Esse número vai para o apêndice do relatório e para o #45.
5. Avise a Pessoa C no #54 o nome da coluna para incluir na linha "P + contexto".

#### Pronto quando
Função testada, CSV gerado e a Pessoa C avisada.

#### Se não der até 27/10
A ablação de contexto roda sem `vacina_cov`, e a qualidade da vacinação vira só limitação no relatório (#45).

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

## #102 · Alinhar todos os YAMLs ao treino 2019/2023–2025 e às duas janelas de teste

- prioridade: P2
- situação: parcial
- estratégia: documentar
- marco: M2
- data ideal: 26/10
- responsável: Pessoa A (decisoes.yaml) + Pessoa C (artefato)
- pessoas: A, C
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

Dois arquivos de configuração contam histórias diferentes; a banca e outra IA não saberão qual vale.

### ③ O que fazer

**Dono:** Pessoa A (decisoes.yaml) + Pessoa C (artefato, já no #131) · **Prazo:** 26/10 · **Esforço estimado:** ≈ 1 h

#### Objetivo
Os dois arquivos de configuração precisam contar a mesma história. O `supervised.yaml` já está certo; o `decisoes.yaml` ainda tem decisões marcadas como "proposta".

#### Passo a passo (Pessoa A)
1. Em `configs/decisoes.yaml`, atualize `status_decisoes`:
   - `coorte_estrita` → `aprovada`, data `2026-10-22`, comentário "contrato final_cohort_v1";
   - `acoes_inconsistencias_datas` → `aprovada`, "D_COORTE_006/007";
   - `variaveis_condicionais` → `aprovada`, "G1 de 22/10";
   - `maturidade_evolucao` → `aprovada`, "2026 só exploração".
   Em todas, `responsavel: time_do_projeto`.
2. Troque `dataset_analitico.path` para `data/analytical/populacao_analitica_pessoa_a.parquet` (evita sobrescrever o artefato; é o #87).
3. Rode `.\.venv\Scripts\python.exe -m pytest tests/test_config.py tests/test_regras_pessoa_a.py -q`.
4. Peça revisão da Pessoa C.

#### Pronto quando
Nenhuma decisão do `decisoes.yaml` está como "proposta" ou "a_definir", e o vocabulário de seis blocos estiver no código (feito pelo #131).

## #30 · Salvar a coorte definitiva com o nome errado a carregaria como provisória

- prioridade: P3
- situação: resolvida
- estratégia: resolvida
- marco: M0
- data ideal: Concluído
- responsável: Pessoa C (dona; revisão cruzada sem edição concorrente)
- pessoas: C
- fonte: src/data/cohort_source.py
- depende de: —
- tags: Código, Dados/Coorte
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 2
- novo: não
- professores: não

### ① Para entender

> [!ok] Decisão fechada em 18/10
> A coorte definitiva inicial será a seleção de features da coorte provisória. O treino principal usará exclusivamente 2019, 2023, 2024 e 2025. Haverá duas janelas de teste: (A) 2019, 2023, 2024 e 2025; (B) 2019 a 2025, incluindo 2020–2022. O ano de 2026 não participa do desenvolvimento nem dos testes principais e fica apenas como exploração opcional, depois de todo o restante concluído.

> [!decisão] Decisão de 18/10
> Ao declarar a provisória como definitiva (item 44), salvar uma cópia como `coorte_final.parquet` para que `cohort_source` a reconheça.

`cohort_source` reconhece como definitiva só `coorte_final.parquet`. Se alguém salvar a coorte definitiva como `coorte.parquet`, ela será tratada como provisória sem aviso.

### ② Problema

`cohort_source` trata `coorte.parquet` como coorte provisória. No B_06, esse mesmo nome era usado como coorte "oficial". Se a coorte definitiva for salva com esse nome, será carregada como provisória.

### ③ O que fazer

> [!ok] Concluída (confirmada no painel em 21/10)
> A coorte foi publicada como `data/analytical/coorte_final.parquet` (SHA-256 `87f28d39…`), com manifesto próprio (`coorte_final.manifest.json`).

**Único cuidado restante:** o artefato supervisionado v3 do #131 deve gravar no manifesto o caminho e o SHA-256 da coorte de origem, e o `cohort_kind` deve ser `final`. Assim nenhum notebook carrega a provisória por engano.

## #59 · Documentar 2026 como período parcial e exclusivamente exploratório

- prioridade: P3
- situação: aberta
- estratégia: documentar
- marco: M1
- data ideal: 25/10
- responsável: Pessoa A (dona; revisão cruzada sem edição concorrente)
- pessoas: A
- fonte: Projeto (relatório)
- depende de: —
- tags: Metodologia, Documentação, Dados/Coorte
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1
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

**Dono:** Pessoa A · **Prazo:** 25/10 · **Esforço estimado:** ≈ 30 min

1. `docs/decisoes.md` §5.4: "2026 tem desfechos ainda pendentes e possível atraso de notificação; por isso não participa de nenhuma decisão nem dos Testes A e B. As 173.945 fichas ficam no bloco `exploracao`."
2. No esqueleto do relatório (#133), na seção Dados: uma frase e uma nota na tabela de volume por ano marcando 2026 como parcial.
3. Anotar no #134: toda figura com eixo de anos que mostrar 2026 recebe a legenda "parcial".

**Pronto quando:** as três menções existirem.

## #73 · decisoes.md parado em 10/10

- prioridade: P2
- situação: aberta
- estratégia: documentar
- marco: M1
- data ideal: 25/10
- responsável: Pessoa A (dona; revisão cruzada sem edição concorrente)
- pessoas: A
- fonte: docs/decisoes.md
- depende de: #10
- tags: Documentação, Decisão
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 3
- novo: não
- professores: não

### ① Para entender

Desde 10/10 foram decididas muitas coisas que não estão registradas: quarentena, lista curta, famílias encerradas, peso das classes, partição por hash, 2026 fora, resultados do C_15.

> [!exemplo] Exemplo
> Se a banca perguntar "por que hash?", a resposta precisa estar no registro de decisões, com data.

### ② Problema

As decisões dizem "última atualização 10/10" e não registram o que foi decidido neste ciclo: quarentena dos 2 grupos, lista curta, famílias encerradas, uso de `class_weight` e aprovações de gates.

### ③ O que fazer

**Dono:** Pessoa A · **Prazo:** 25/10 (sábado), revisão final em 29/10 · **Esforço estimado:** ≈ 3 h

#### Objetivo
O `docs/decisoes.md` é a memória oficial das decisões e vai ser citado no relatório. Ele parou em 21/10 e tem trechos que contradizem o que foi decidido depois. Quem ler hoje entende outro estudo.

#### Como escrever cada entrada
Data · decisão em uma frase · motivo · impacto (o que muda no código ou nos resultados) · onde está implementado (arquivo ou item #N) · quem decidiu. Nunca apague o texto antigo: marque "substituído em DD/MM por …".

#### Entradas novas (nesta ordem)
1. **22/10 · Contrato da coorte definitiva (`final_cohort_v1`).** As 7 regras `D_COORTE_001` a `007`, com a contagem de linhas que atendem a cada regra: hospital ≠ 1 (232.253); data de internação inválida (304.245); evolução fora de óbito/cura (530.370); antes de 2019 (48); depois de 2026 (76); intervalo negativo (24.361); intervalo acima de 60 dias (11.708). As regras se sobrepõem: o total excluído é 782.182, e a coorte fica com 3.884.728 de 4.666.910.
2. **22/10 · G1 aprovado.** 31 features principais; `saturacao` e `desc_resp` só em sensibilidade (não se sabe se foram medidas na admissão); `vacina`, `vacina_cov`, `cs_escol_n` e `sg_uf` só como contexto.
3. **23/10 · Coorte publicada.** Paridade com o protocolo legado e comparação com a provisória: a definitiva tem 30.408 linhas a menos e nenhuma divergência de alvo nas linhas em comum.
4. **24/10 · Regra de grupo (#10)** e partição em seis blocos (números do #131).
5. **24/10 · Orientação.** Os pontos do #95, em uma linha cada.
6. **24/10 · Indicadores de ausência desativados no supervisionado (#83)** e troca pela análise de completude (#52).
7. **24/10 · Não supervisionado com one-hot dos quatro estados (#136)** e perfil por qui-quadrado/ANOVA (#137).
8. **24/10 · Geografia como separação da análise (#110).**
9. **27–28/10 (quando acontecer):** resultado dos sintomas de 2019 (#50), peso de classe (#5), finalista e hiperparâmetros (G6), calibração (G7) e limiar (G8). A Pessoa C escreve uma linha no card; você transcreve.

#### Correções em seções antigas
- **§7:** trocar `semana_sen`, `semana_cos` e `flag_intervalo_negativo_inesperado` pelos nomes reais (`sin_semana`, `cos_semana`, `flag_intervalo_invalido`, `flag_internacao_antes_sintomas`) e dizer que a sazonalidade é só ablação (#13).
- **§8:** "sinalizar intervalos impossíveis" foi substituído em 22/10 pelas regras `D_COORTE_006/007` (#82).
- **§13:** saturação e desconforto saem do "Modelo A" e vão para sensibilidade (#9).
- **§17:** vacinação como contexto, com a regra de doses do #84.
- Topo: "Última atualização" e a lista de pendentes da §1.2 (só o que de fato está pendente).

#### Como validar
Leia o arquivo inteiro procurando contradições com o YAML (`configs/supervised.yaml`). Não pode sobrar nenhuma.

#### Pronto quando
As entradas 1 a 8 estiverem escritas em 25/10, as correções feitas e a entrada 9 completada até 29/10 (antes do G9).

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

## #87 · Os notebooks A e o B_07 gravam no mesmo arquivo e um apaga o outro

- prioridade: P3
- situação: parcial
- estratégia: desenvolver
- marco: M3
- data ideal: 27/10
- responsável: Pessoa A · revisão: Pessoa C
- pessoas: A
- fonte: src/protocolo/verificacoes.py (a1_export_dataset, _analytical_path); notebooks A_03, A_04, A_14; configs/decisoes.yaml (dataset_analitico.path)
- depende de: —
- tags: Diverge do decidido, Código, Dados/Coorte, Notebook
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1
- novo: não
- professores: não

### ① Para entender

O A_03 e o A_04 exportam a população analítica para `data/analytical/dataset_supervisionado.parquet`. O B_07 grava o artefato oficial **no mesmo caminho**. Quem rodar por último vence.

<div class="flow"><span class="">A_03 grava v0.1</span><i>→</i><span class="">A_04 grava v1.0</span><i>→</i><span class="bad">B_07 sobrescreve</span><i>→</i><span class="">A_14 confere o hash → FALHA</span></div>

Se os notebooks A rodarem depois do B_07, o hash deixa de bater com o manifesto e o B_10 e todos os C param com "Hash do dataset supervisionado difere do manifesto".

> [!exemplo] Exemplo
> Duas pessoas salvando documentos diferentes com o mesmo nome na mesma pasta.

### ② Problema

`a1_export_dataset` grava em `_analytical_path(cfg)`, que resolve para `C.ANALYTICAL_DIR / "dataset_supervisionado.parquet"` (nome definido em `configs/decisoes.yaml`, `dataset_analitico.path`). É o mesmo arquivo de `src/data/supervised_artifact.py` (`DATASET_NAME`). O A_14 registrou **FALHA**: "dataset analítico foi alterado depois da exportação". A ordem atual de execução evita o problema por acaso, não por desenho.

### ③ O que fazer

**Dono:** Pessoa A · **Prazo:** 26/10 · **Esforço estimado:** ≈ 1 h · **Revisão:** Pessoa C

#### Objetivo
Impedir que os notebooks da frente A sobrescrevam o artefato oficial (os dois gravam hoje em `data/analytical/dataset_supervisionado.parquet`).

#### Passo a passo
1. A troca do caminho no `configs/decisoes.yaml` está no #102 (passo 2).
2. Em `src/protocolo/verificacoes.py`, a função `_analytical_path` usa só o **nome** do arquivo do YAML e o coloca na pasta padrão. Mude para usar o caminho completo do YAML, para que a troca do passo 1 tenha efeito.
3. Rode `.\.venv\Scripts\python.exe -m pytest tests/test_regras_pessoa_a.py -q`.
4. No topo de A_03, A_04, A_09 e A_14, uma célula de texto: "Histórico da fase provisória. Não executar: a cadeia oficial é C_11 a C_16."
5. No README, seção "Dados": tabela de quem é dono de cada arquivo em `data/analytical/` (coorte e artefato → Pessoa C; população da frente A → Pessoa A).

#### Pronto quando
Nenhum notebook A consegue gravar no caminho do artefato oficial.

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

## #19 · O YAML aceita chaves duplicadas em silêncio e fica em cache

- prioridade: P3
- situação: aberta
- estratégia: desenvolver
- marco: M6
- data ideal: 31/10
- responsável: Pessoa B (após 30/10) · alternativa: Pessoa C
- pessoas: B, C
- fonte: src/utils/config.py (carregar_supervised)
- depende de: —
- tags: Código, Ambiente
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1
- novo: não
- professores: não

### ① Para entender

> [!decisão] Decisão de 18/10
> Lote de higiene de 22/10: correções pequenas, teto de 1 dia; o que não couber vai para pós-entrega.

Se o YAML tiver a mesma chave duas vezes, a leitura padrão fica com a última, sem avisar. A leitura rigorosa só existe no B_10. Além disso, o YAML lido fica guardado na memória: mudar o arquivo só vale depois de reiniciar o kernel.

> [!exemplo] Exemplo
> Você aprova o G6 no YAML, roda o C_13 sem reiniciar, e ele continua achando que o G6 está pendente.

### ② Problema

`carregar_supervised` usa `yaml.safe_load`, que aceita chaves duplicadas sem aviso (a última vence). A leitura rigorosa, que barra duplicadas, existe apenas no B_10. Além disso, o resultado fica em cache (`lru_cache`), e alterações no YAML só valem depois de reiniciar o kernel.

### ③ O que fazer

**Pessoa B em 31/10 (≈ 1 h) ou Pessoa C se tiver folga antes.** Em `src/utils/config.py`: leitura do YAML que dá erro quando há chave duplicada (o código existe no B_10; mover, não reescrever) e `recarregar_supervised()` que limpa o cache. Teste com um YAML temporário duplicado. Importante porque os gates G6 a G9 serão escritos à mão nos próximos dias.

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

## #29 · Itens desatualizados ou sem uso no YAML

- prioridade: P3
- situação: aberta
- estratégia: desenvolver
- marco: M3
- data ideal: 26/10
- responsável: Pessoa A · revisão: Pessoa C
- pessoas: A
- fonte: configs/supervised.yaml
- depende de: —
- tags: Código, Documentação
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1
- novo: não
- professores: não

### ① Para entender

> [!decisão] Decisão de 18/10
> Lote de higiene de 22/10: correções pequenas, teto de 1 dia; o que não couber vai para pós-entrega.

Árvore e Random Forest seguem `ativa: true` apesar de encerradas; não existe G3; 30 chaves nunca são lidas pelo código; `youden_j` é citado mas não é métrica candidata. Isso confunde quem lê o YAML como fonte única.

### ② Problema

O YAML tem itens desatualizados ou sem uso: `decision_tree` e `random_forest` continuam com `ativa: true`, embora estejam em `familias_encerradas`; não existe gate G3 e não há explicação; `coluna_estratificacao_temporal` e `descartar_outros` não são lidas por nenhum código; `metricas_candidatas` não inclui `youden_j`, que as decisões citam como opção.

### ③ O que fazer

**Dono:** Pessoa A · **Prazo:** 26/10 · **Esforço estimado:** ≈ 1 h · **Revisão:** Pessoa C

#### Objetivo
Deixar o `configs/supervised.yaml` sem informações que confundem quem o lê (pessoa ou IA).

#### Passo a passo
1. `models.decision_tree.ativa: false` e `models.random_forest.ativa: false` (as duas famílias foram encerradas: ficaram atrás no piloto definitivo).
2. Acima de `gates:`, o comentário `# não existe G3: a etapa foi absorvida pelo G2 em 18/10`.
3. Em `limiar.metricas_candidatas`, acrescente `youden_j` e `recall_minimo`, e crie a chave `limiar.min_recall: 0.80` (vai ser usada pelo #80).
4. Em `models.boosting`, mude `early_stopping: false` para `true` (o código já usa `true`; o YAML estava contraditório).
5. Não apague `target.descartar_outros` nem `temporal.coluna_estratificacao_temporal`: acrescente `# documental` ao lado.
6. Rode `.\.venv\Scripts\python.exe -m pytest tests/test_config.py -q` e peça revisão.

#### Pronto quando
Testes passando e, na próxima referência do projeto (#130), os alertas A67 e A68 terem sumido.

## #38 · Sobras no B_07: modo de teste sintético e imports sem uso

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 03/11
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

O B_07 ainda tem o modo `SRAG_NOTEBOOK_SMOKE`, que usa dados sintéticos, e imports sem uso, como `GroupShuffleSplit`, `ColumnTransformer` e funções avulsas de `sklearn.metrics`.

### ③ O que fazer

> [!atenção] Sugestão automática incorreta: o modo `SRAG_NOTEBOOK_SMOKE` continua no B_07.
> Como o B_07 passou a ser histórico da fase provisória (#72), **não vale a pena mexer agora**. Use **✗ Não é isso** e deixe para depois da entrega.

**Como fazer, quando for a hora (instruções anteriores mantidas):**

Remover o modo de teste com dados sintéticos (os testes de `tests/` já cumprem esse papel) e os imports sem uso. Rodar o notebook do início ao fim para confirmar.

## #40 · A construção da coorte provisória não gera os arquivos de rastreio esperados

- prioridade: P3
- situação: parcial
- estratégia: desenvolver
- marco: M4
- data ideal: 28/10
- responsável: Pessoa A (tabela) + Pessoa C (conferência)
- pessoas: A
- fonte: B/___provisorio_construcao_coorte_b; construção da coorte definitiva
- depende de: #131
- tags: Notebook, Dados/Coorte
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 2
- novo: não
- professores: não

### ① Para entender

O notebook `___provisorio_construcao_coorte_b` não foi reexecutado (0 de 14 células com saída), fixa a data final em 28/09/2026 e não gera `manifesto_coorte.json` nem `variaveis_finais.csv`, que o YAML espera.

### ② Problema

A coorte provisória fixa a data final em 28/09/2026. A remoção de duplicatas exatas só considera as colunas carregadas do dicionário. O notebook não gera `manifesto_coorte.json` nem `variaveis_finais.csv`, que o YAML espera em `artefatos_coorte`.

### ③ O que fazer

**Dono:** Pessoa A · **Prazo:** 28/10 · **Esforço estimado:** ≈ 2 h · **Revisão:** Pessoa C (nomes contra o artefato)

#### Objetivo
Gerar o único artefato de rastreio que falta: a tabela das variáveis finais, que vai para a seção de Métodos.

#### Passo a passo
1. Fonte: `configs/feature_contract_v1.json` + `configs/supervised.yaml` (listas) + `configs/dicionario_variaveis_v1.csv` (nome amigável, preenchimento).
2. Colunas da tabela: `variavel`, `nome_amigavel`, `grupo` (principal, contexto_incremental, sensibilidade_gravidade, proibida), `tipo` (numérica ou categórica), `codificacao` (one-hot na logística; ordinal no boosting; one-hot dos quatro estados no não supervisionado), `justificativa_temporal` (disponível na admissão ou não), `preenchimento_min_ano` e `preenchimento_max_ano` (do dicionário), `observacao` (ex.: "campo inexistente em 2019" para os três sintomas, a partir do #50).
3. Script curto em `tools/` ou célula do seu notebook; salve em `data/analytical/variaveis_finais.csv` e uma cópia em `outputs/final/`.
4. A Pessoa C confere se os nomes batem com `numeric_columns`, `categorical_columns` e `audit_columns` do manifesto do artefato.

#### Pronto quando
O CSV tiver as 31 principais, as 4 de contexto, as 2 de gravidade e as proibidas, com a conferência da Pessoa C.

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

## #98 · Notebooks B sem execução salva: a coorte provisória não é reprodutível pelo repositório

- prioridade: P4
- situação: aberta
- estratégia: documentar
- marco: M6
- data ideal: 31/10
- responsável: Pessoa A
- pessoas: A
- fonte: notebooks B_05 (1 de 42 células sem saída); B/___provisorio_construcao_coorte_b (0 de 14)
- depende de: —
- tags: Notebook, Dados/Coorte
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1
- novo: não
- professores: não

### ① Para entender

O notebook que constrói a coorte provisória B não tem nenhuma célula executada salva, e o B_05 tem uma célula sem saída. Quem clonar o repositório não consegue ver como a coorte de 3,9 milhões de linhas foi feita, só o arquivo pronto (que não vai para o Git).

<div class="kpi">
<div><b>0 / 14</b>células executadas no construtor da coorte</div>
<div><b>41 / 42</b>células executadas no B_05</div>
</div>

### ② Problema

Alertas A40 e A41 do relatório. A coorte `coorte_provisoria_b.parquet` (SHA-256 `da94652d…`) é usada pelo B_06 e pelo B_07, mas o processo que a gera não está registrado com saídas.

### ③ O que fazer

**Pessoa A, 31/10, 15 minutos:** um parágrafo de Métodos (no #133) dizendo que a seleção de variáveis foi feita na coorte provisória e congelada antes da definitiva, e que a definitiva é subconjunto exato da provisória (30.408 linhas a menos, nenhuma nova, alvo idêntico). Não executar o construtor provisório de novo.

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

## #127 · Função de comparação pareada com bootstrap por grupo

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M2
- data ideal: 25/10
- responsável: Pessoa B até 24/10 → Pessoa C a partir de 26/10
- pessoas: B, C
- fonte: src/evaluation/comparacao.py (novo)
- depende de: #23
- tags: Metodologia, Código
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 3
- novo: sim
- professores: não

### ① Para entender

Quando dois modelos são avaliados nas mesmas pessoas, a pergunta certa é "a diferença entre eles é real?", não "cada um tem qual nota?". O bootstrap pareado sorteia pessoas com reposição, recalcula as duas métricas e guarda a diferença; o intervalo dessas diferenças diz se o ganho é consistente.

> [!exemplo] Exemplo
> Duas balanças pesando os mesmos 80 mil pacotes: comparar pacote a pacote é muito mais preciso que comparar a média de cada balança.

### ② Problema

Não existe função para isso no `src`. Reamostrar linhas (e não grupos) subestimaria a incerteza quando a mesma notificação tem mais de uma linha.

### ③ O que fazer

**Dono:** Pessoa B (24/10) → Pessoa C se não estiver no main até o fim de 25/10 · **Prazo:** 25/10 (B) ou 28/10 (C) · **Esforço estimado:** ≈ 3 h

#### Objetivo
Dar intervalo de confiança às **diferenças**: Teste A × Teste B, logística × boosting, e cada linha das ablações contra o modelo principal.

#### Passo a passo
1. Em `src/evaluation/metrics.py`, `bootstrap_pareado(y, prob_a, prob_b, grupos, metrica, n=None, seed=None) -> dict`. Quando `n` e `seed` forem `None`, ler `avaliacao.bootstrap` do YAML (1.000 e 42).
2. Sortear **grupos** (`group_id`) com reposição, nunca linhas. Por desempenho: `np.unique(grupos, return_inverse=True)` uma vez e usar a contagem de cada grupo sorteado como peso (`np.bincount`), sem `groupby` dentro do laço.
3. Em cada réplica: calcular a métrica para A e para B sobre as mesmas linhas e guardar a diferença. Réplicas com uma classe só são descartadas e contadas.
4. Devolver `{"diferenca", "ic_inf", "ic_sup", "n_grupos", "n_reps_validas"}`.
5. Métricas: `average_precision_score`, `roc_auc_score`, `brier_score_loss`.
6. Variante não pareada `ic_bootstrap_grupo(y, prob, grupos, metrica)` reaproveitando o mesmo núcleo.
7. Testes: A igual a B → diferença 0 e IC [0, 0]; modelo perfeito × aleatório → IC acima de zero; mesma semente → mesmo resultado.

#### Pronto quando
Função e testes no `main`. É usada a partir de 27/10 (ablações) e é obrigatória a partir de 29/10.

## #15 · Pré-processador e manifesto podem usar listas de variáveis diferentes

- prioridade: P2
- situação: aberta
- estratégia: desenvolver
- marco: M2
- data ideal: 26/10
- responsável: Pessoa C (antes: Pessoa A)
- pessoas: C
- fonte: src/models/pipeline.py (FEATURES, build_preprocessor); notebooks C_11 a C_16
- depende de: #131
- tags: Código, Features
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1
- novo: não
- professores: não

### ① Para entender

Do C_11 ao C_16, a tabela X é montada com as variáveis do **manifesto**, mas o pré-processador usa as listas do **YAML**. Hoje elas coincidem. Quando `features.final` for preenchida, podem divergir, e o pipeline falha ou treina com colunas erradas.

### ② Problema

Do C_11 ao C_16, o X é montado com as features registradas no manifesto do artefato, mas o pré-processador é montado com as listas do YAML. Se as listas divergirem (por exemplo, quando `features.final` for preenchida ou o artefato for gerado com outra lista), o pipeline falha por coluna ausente ou treina com colunas diferentes das registradas.

### ③ O que fazer

**Resolvido dentro do #132.** Os notebooks C montam o pré-processador com as listas do manifesto (`numeric_columns`, `categorical_columns`) e, no início, conferem `set(manifest["feature_columns"]) == set(cfg("features", "final"))`; se divergir, param com mensagem clara. Blocos extras das ablações são declarados explicitamente.

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

## #22 · Funções de avaliação com padrões diferentes do YAML

- prioridade: P3
- situação: aberta
- estratégia: desenvolver
- marco: M2
- data ideal: 25/10
- responsável: Pessoa B até 24/10 → Pessoa C
- pessoas: B, C
- fonte: src/evaluation/metrics.py (ic_bootstrap); src/evaluation/errors.py (metricas_por_grupo)
- depende de: —
- tags: Código, Metodologia
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1
- novo: não
- professores: não

### ① Para entender

O intervalo de confiança por bootstrap usa 200 repetições por padrão (o YAML pede 1.000), e a análise por subgrupo ignora grupos com menos de 30 casos (o YAML pede 100). O C_16 passa os valores certos; qualquer outro uso recebe os antigos.

### ② Problema

Os padrões das funções não seguem o YAML: `ic_bootstrap` usa 200 repetições (o YAML pede 1.000) e `metricas_por_grupo` usa mínimo de 30 casos por grupo (o YAML pede 100). O C_16 já passa os valores corretos, mas qualquer outro uso das funções recebe os padrões antigos.

### ③ O que fazer

**Mesmo arquivo do #127; quem fizer o #127 faz este junto (10 minutos).** Em `ic_bootstrap` e `metricas_por_grupo`, trocar os padrões fixos (200 réplicas e mínimo de 30 casos) por `None` e, quando `None`, ler `avaliacao.bootstrap.repeticoes` (1.000) e `avaliacao.min_n_grupo` (100) do YAML. Teste: com um YAML de teste de 7 réplicas, a função faz 7.

## #23 · A análise por subgrupo não calcula PR-AUC nem Brier

- prioridade: P3
- situação: aberta
- estratégia: desenvolver
- marco: M2
- data ideal: 25/10
- responsável: Pessoa B até 24/10 → Pessoa C
- pessoas: B, C
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

**Dono:** Pessoa B (24/10) → Pessoa C junto com o #127 · **Prazo:** 25/10 · **Esforço estimado:** ≈ 1 h 30

1. Em `src/evaluation/errors.py::metricas_por_grupo`, por grupo: `n`, `prevalencia`, `pr_auc`, `pr_auc_sobre_prev`, `roc_auc`, `brier`, `o_e` (óbitos observados ÷ soma das probabilidades: 1 = calibrado), sensibilidade e precisão no corte.
2. Grupo com uma classe só → `NaN`, sem erro. Grupo com `n` abaixo do mínimo → linha mantida com `suprimido=True` e métricas `NaN` (o grupo aparece, mas sem número instável).
3. Teste com dados sintéticos: grupo só de curas devolve `NaN` em PR-AUC.

**Pronto quando:** função e teste no `main` (é usada pelo #55 e pelo #110).

## #27 · O manifesto "mais recente" é escolhido pela data do arquivo

- prioridade: P3
- situação: aberta
- estratégia: desenvolver
- marco: M2
- data ideal: 26/10
- responsável: Pessoa C (antes: Pessoa B)
- pessoas: C
- fonte: notebooks C_16; B_10_consolidacao_shortlist_transicao_coorte
- depende de: #132
- tags: Código, Notebook
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1
- novo: não
- professores: não

### ① Para entender

O C_16 e o B_10 pegam o manifesto com a data de modificação mais nova. Copiar a pasta ou sincronizar pelo OneDrive muda essas datas e pode fazer o notebook ler o manifesto errado.

### ② Problema

O C_16 e o B_10 escolhem o manifesto mais recente pela data de modificação do arquivo. Copiar ou sincronizar a pasta (OneDrive, git) altera essa data e pode fazer o notebook ler o manifesto errado.

### ③ O que fazer

**Resolvido dentro do #132 (passo 5).** O C_16 localiza o manifesto de execução pelo `run_id_finalista` gravado no YAML pelo C_15, e não pela data do arquivo (copiar ou sincronizar a pasta muda a data).

## #58 · A mesma validação escolhe hiperparâmetros e mede o resultado

- prioridade: P3
- situação: parcial
- estratégia: documentar
- marco: M2
- data ideal: 26/10
- responsável: Pessoa C (conferência no #132)
- pessoas: C
- fonte: notebooks C_13 e C_15
- depende de: #132
- tags: Metodologia, Calibração
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1
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

A busca do C_13 usa a validação inteira. O C_15 divide a validação em duas metades e usa uma delas para medir o desempenho final antes do teste. Essa metade já influenciou a escolha dos hiperparâmetros, então a estimativa fica um pouco otimista.

### ③ O que fazer

**Resolvido por desenho, conferir no #132 (passo 4).** Com `val_tune` (escolhe), `val_cal` (calibra e escolhe o corte) e `val_meas` (só mede), nenhuma fatia escolhe e mede ao mesmo tempo. Falta só confirmar que o `HONEST_CALIB_SPLIT` saiu do C_15. No relatório (Métodos), uma frase explicando os três papéis.

## #119 · Executar o modelo congelado nas duas janelas de teste (E_02)

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M5
- data ideal: 31/10
- responsável: Pessoa C (execução) + Pessoa B (revisão ao voltar)
- pessoas: C, B
- fonte: Plano integrado v2, seções 3 e 4; notebooks/E/E_02
- depende de: #2, #81, #127, #23
- tags: Modelagem, Notebook
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 3
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

As duas janelas têm prevalências e composição temporal diferentes. Comparar apenas PR-AUC agregada seria insuficiente. É necessário reportar prevalência, PR-AUC/prevalência, ROC-AUC, Brier e calibração em cada janela e por ano.

### ③ O que fazer

**Dono:** Pessoa C (até 30/10) · revisão da Pessoa B ao voltar · **Prazo:** 30/10 (preparar) e 31/10 de manhã (executar) · **Esforço estimado:** ≈ 3 h

#### O que o C_16 precisa produzir (preparar até 29/10)
1. **Teste A** (`test_ref`): n, óbitos, prevalência, PR-AUC, PR-AUC ÷ prevalência, ROC-AUC, Brier, Brier do nulo, intercepto e inclinação de calibração, curva de calibração por quantis, matriz de confusão e sensibilidade, precisão, especificidade e F1 no corte congelado (e no de 0,70).
2. **Teste B** (`test_ref` ∪ `test_pandemic`): as mesmas métricas.
3. **2020–2022 isolado** e **cada ano** separado, incluindo 2019.
4. **IC 95%** por bootstrap de grupos (1.000 réplicas, #127) para as métricas principais; diferença A × B e logística × boosting com bootstrap pareado.
5. **Exportar previsões:** `outputs/final/predicoes_val_meas.parquet` e `predicoes_teste.parquet` com `id_registro`, `group_id`, `particao`, `ano_internacao`, `regiao_residencia`, `sg_uf`, `faixa_etaria`, `sexo_categoria`, `y`, `prob_calibrada`, `classe`. Tudo o que vem depois (#55, #110, #52) parte daqui, sem rodar modelo de novo.
6. Nomes fixos: `teste_a_metricas.csv`, `teste_b_metricas.csv`, `pandemico_metricas.csv`, `por_ano.csv`, `calibracao_*.csv`, `figuras/*.png`, e um manifesto com SHA-256 do artefato, commit, YAML e horário.

#### Leitura obrigatória
A PR-AUC do Teste B pode ficar **maior** só porque 2020–2022 têm 26% de óbitos. Comparar sempre PR-AUC ÷ prevalência e ROC-AUC. Escrever "robustez à mudança de período", nunca "efeito da pandemia".

#### Pronto quando
Os arquivos existirem e o manifesto tiver `test_opened: true`.

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

## #51 · As tabelas de óbito do B_06 usaram também os casos do teste

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M3
- data ideal: 27/10
- responsável: Pessoa A
- pessoas: A
- fonte: B_06_eda_temporal_clustering
- depende de: #131
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

As tabelas de desfecho do B_06 (letalidade por variável) usaram a coorte inteira, incluindo os casos que depois foram para o teste. Isso viola o princípio de não olhar o teste antes da avaliação final.

### ③ O que fazer

**Dono:** Pessoa A · **Prazo:** 27/10 · **Esforço estimado:** ≈ 30 min (dentro do #137) · **Começa quando:** #131 e função do #137

> [!decisão] Mudança de plano (24/10)
> Em vez de reexecutar o B_06 (notebook pesado e da frente da Pessoa B, que está fora), as tabelas de óbito × cura são refeitas com a função `perfil_estatistico` do #137, só no `train_ref`. É mais rápido, tem teste e traz tamanho de efeito.

1. Execute o **uso 1** do #137 (óbito × cura no `train_ref`).
2. Compare com a tabela antiga do B_06 (`eda_02_obito_sintomas.csv`, `eda_02_obito_comorbidades.csv`): as direções devem ser as mesmas (o `train_ref` tem 70% dos mesmos anos). Anote no card qualquer variável que mude de direção.
3. No relatório, as tabelas de desfecho passam a vir de `outputs/final/perfil_desfecho_train_ref.csv`, com a legenda "somente bloco de treino".

**Pronto quando:** o CSV existir e o relatório usar só ele.

## #91 · Mostrar quais características pesam mais no risco (importância das variáveis)

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M4
- data ideal: 29/10
- responsável: Pessoa C (tabelas) + Pessoa B (interpretação em 31/10)
- pessoas: C, B
- fonte: Projeto (pergunta de pesquisa); finalistas do C_13/C_15; relatório
- depende de: #1
- tags: Metodologia, Modelagem
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 4
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

Nenhum notebook calcula importância de variáveis. O B_06 tem razões de chances **brutas**, que sofrem confundimento (asma e tosse aparecem como "protetoras"). Sem uma análise ajustada, o relatório não responde a segunda metade da pergunta de pesquisa.

### ③ O que fazer

**Dono:** Pessoa C (tabelas, 29/10) + Pessoa B (interpretação, 31/10) · **Prazo:** 31/10 · **Esforço estimado:** C ≈ 2 h · B ≈ 2 h · **Começa quando:** G6

#### O que é
A segunda metade da pergunta de pesquisa: quais características pesam no risco.

| Técnica | Em uma frase |
|---|---|
| Razão de chances ajustada (logística) | "Com diabetes, a chance de óbito é X vezes maior, comparando pessoas parecidas no resto." |
| Importância por permutação (boosting) | Embaralha uma variável e mede quanto a PR-AUC cai: quanto maior a queda, mais o modelo depende dela. |

#### Parte da Pessoa C (29/10, depois do G6)
1. **Logística:** `np.exp(coef_)` do pipeline final com os nomes de `get_feature_names_out()`; uma tabela por variável original (categoria × referência). Nota obrigatória: "associação ajustada e regularizada, não causal".
2. **Boosting:** `permutation_importance` em `val_meas` (amostra de 100 mil), `scoring="average_precision"`, `n_repeats=5`, semente 42, permutando as **colunas originais** (pipeline inteiro como estimador).
3. **Estabilidade:** repetir a permutação em duas amostras diferentes de `val_meas` e reportar a correlação de postos.
4. Salvar `outputs/final/importancia_logistica.csv` e `importancia_permutacao.csv`. Nunca calcular no teste.

#### Parte da Pessoa B
5. Tabela "bruto × ajustado": para asma, puerpério, tosse, febre, doença renal e diabetes, a razão de chances bruta (do #137, uso 1) ao lado da ajustada. Marcar as que mudam de sinal (exemplo central de confundimento pela idade: mortalidade de 1–2% em crianças × 41% acima de 80 anos).
6. Duas figuras: 15 maiores razões ajustadas e 15 maiores importâncias.
7. Um parágrafo para a Discussão (fecha o #57).

**Pronto quando:** CSVs, figuras e parágrafo existirem.

## #55 · Desempenho e erros por ano, idade, sexo e UF

- prioridade: P2
- situação: aberta
- estratégia: desenvolver
- marco: M3
- data ideal: 28/10
- responsável: Pessoa C (Fase E, val_tune) · Pessoa B (teste, 31/10) · Pessoa A (falsos negativos, 31/10)
- pessoas: C, B, A
- fonte: notebooks C_16
- depende de: #132, #23
- tags: Metodologia, Notebook
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 6
- novo: não
- professores: não

### ① Para entender

Um modelo pode ir bem na média e mal num grupo. O C_16 já calcula métricas por subgrupo e analisa os falsos negativos (óbitos que o alerta não pegou), mas só roda no final.

Exemplo do B_07: a PR-AUC do boosting varia de 0,22 (2026) a 0,52 (2020) entre anos.

### ② Problema

Faltam o desempenho e a calibração por ano, faixa etária, sexo e UF, e a análise de erros com foco em falsos negativos. O C_16 já faz essas análises, mas só roda depois da coorte definitiva.

### ③ O que fazer

> [!decisão] Replanejamento de 26/10: exploração antes da validação
> A troca para a coorte definitiva é uma base "nova": antes de ajustar e validar modelos, todas as análises que podem mudar decisões (variáveis, representação, limiar, calibração, leitura por região) rodam na **Fase E (26 a 28/10)**, sobre o `train_ref` e o `val_tune`. Os achados são discutidos no **ponto de decisão do #140 (28/10 à noite)**. Só então começam o ajuste fino (29/10) e a validação. Depois do teste, as mesmas análises são apenas repetidas para o relatório, sem decidir nada.

**Dono:** Pessoa C (Fase E) · Pessoa B e Pessoa A (relatório) · **Prazo:** 28/10 (C) · 31/10 (B e A) · **Esforço estimado:** C ≈ 1 h · B ≈ 3 h · A ≈ 2 h · **Começa quando:** previsões do piloto em `val_tune` (#132) e `metricas_por_grupo` ampliada (#23)

#### Por que antes da validação
Um modelo pode ir bem na média e mal num grupo. Se uma faixa etária ou um ano estiver muito mal calibrado no `val_tune`, ainda dá para decidir (no #140) uma calibração por faixa como sensibilidade, ou discutir a variável. Depois do G9, não.

#### Parte da Pessoa C (28/10, sobre o `val_tune`)
1. Com `predicoes_val_tune_piloto.parquet` (logística e boosting do piloto, já com as colunas `ano_internacao`, `faixa_etaria`, `sexo_categoria`), rode `metricas_por_grupo` por ano, faixa etária e sexo.
2. Salve `outputs/final/subgrupos_val_tune.csv` e comente no #140 qualquer grupo com O/E fora de 0,8–1,2 ou ROC-AUC muito abaixo da média.

#### Parte da Pessoa B (31/10, relatório)
3. Repita com `predicoes_val_meas.parquet` e `predicoes_teste.parquet` (Testes A e B), sem decidir nada. Salve `outputs/final/por_subgrupo.csv`; calibração (O/E) por faixa etária; três frases de resultado.

#### Parte da Pessoa A (31/10, relatório)
4. **Falsos negativos no Teste A** (óbitos sem alerta no corte congelado): compare com os verdadeiros positivos em idade, dias até internar, número de sintomas e de comorbidades e completude, usando `perfil_estatistico` (#137) com `coluna_grupo` = "falso negativo × verdadeiro positivo". Salve `outputs/final/falsos_negativos_perfil.csv`.
5. Figura com PR-AUC ÷ prevalência e IC por faixa etária e por região.

#### Pronto quando
Subgrupos do `val_tune` comentados no #140 (28/10) e os arquivos do relatório prontos (31/10).

## #57 · Associações "protetoras" que são efeito da idade

- prioridade: P3
- situação: aberta
- estratégia: explorar
- marco: M6
- data ideal: 31/10
- responsável: Pessoa B (dona; revisão cruzada sem edição concorrente)
- pessoas: B
- fonte: B_06_eda_temporal_clustering
- depende de: #51, #91
- tags: Metodologia
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1
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

Associações que parecem "protetoras" (asma, tosse, febre) podem ser efeito da idade: são mais comuns em crianças, que morrem menos.

### ③ O que fazer

**Resolvido dentro do #91 (passo 5).** A tabela "bruto × ajustado" mostra quais associações "protetoras" (asma 0,30; puerpério 0,34; tosse 0,61) somem ou mudam de sinal depois do ajuste. A Pessoa B escreve o parágrafo da Discussão em 31/10.

## #89 · Revisar a conclusão do A_09 de que o sorteio é "otimista"

- prioridade: P3
- situação: aberta
- estratégia: documentar
- marco: M6
- data ideal: 31/10
- responsável: Pessoa A
- pessoas: A
- fonte: notebooks A_09 (seção 3, benchmark); outputs/tables/pessoa_a/a3_benchmark_split.csv
- depende de: —
- tags: Metodologia, Partição
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1
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

No benchmark do A_09 (logística, cerca de 140 mil de treino e 30 mil de validação), a prevalência na validação foi 23,1% no sorteio e 13,8% no temporal. A PR-AUC de um classificador aleatório é igual à prevalência, então a comparação direta favorece o cenário com mais óbitos. Relativa ao chute, a PR-AUC temporal é maior (2,6× contra 2,0×), e a ROC-AUC também (0,821 contra 0,774). O mesmo padrão aparece sem 2020–21. A conclusão registrada no notebook pode levar a uma decisão de período e divisão (item 85) com base numa leitura incompleta.

### ③ O que fazer

**Pessoa A, 31/10, 20 minutos:** um parágrafo de Métodos: "A PR-AUC depende da prevalência; por isso todas as comparações entre períodos usam também PR-AUC ÷ prevalência e ROC-AUC." Use como exemplo a própria coorte: a PR-AUC da logística caiu de 0,44 (22% de óbitos) para 0,30 (8,4%), mas, medida contra o acaso, subiu de 2,0× para 3,6×. Cite a regra do professor (modelo pelo menos 25% melhor que o acaso). Não rodar o A_09.

## #110 · Geografia como separação da análise: ponto de corte por região e equidade (sem região como variável)

- prioridade: P2
- situação: aberta
- estratégia: desenvolver
- marco: M3
- data ideal: 28/10
- responsável: Pessoa C (execução) + Pessoa B (interpretação em 31/10)
- pessoas: C, B
- fonte: artefato supervisionado (sg_uf); E_03; orientação de 17/10
- depende de: #132, #23
- tags: Features, Geografia
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 5
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

Geografia nunca foi testada como variável.

### ③ O que fazer

> [!decisão] Replanejamento de 26/10: exploração antes da validação
> A troca para a coorte definitiva é uma base "nova": antes de ajustar e validar modelos, todas as análises que podem mudar decisões (variáveis, representação, limiar, calibração, leitura por região) rodam na **Fase E (26 a 28/10)**, sobre o `train_ref` e o `val_tune`. Os achados são discutidos no **ponto de decisão do #140 (28/10 à noite)**. Só então começam o ajuste fino (29/10) e a validação. Depois do teste, as mesmas análises são apenas repetidas para o relatório, sem decidir nada.

**Dono:** Pessoa C (Fase E e cortes) · Pessoa B (relatório) · **Prazo:** 28/10 (métricas) · 30/10 (cortes) · 31/10 (B) · **Esforço estimado:** C ≈ 2 h · B ≈ 3 h · **Começa quando:** #132 e #23

#### Parte da Pessoa C · 28/10 (Fase E, sobre o `val_tune`)
1. Com `predicoes_val_tune_piloto.parquet`, rode `metricas_por_grupo` por região e por UF (n ≥ 100): PR-AUC ÷ prevalência, ROC-AUC, O/E.
2. Salve `outputs/final/regiao_val_tune.csv` e comente no #140 se alguma região tem desempenho ou calibração muito diferente.

#### Parte da Pessoa C · 30/10 (junto com o #80)
3. Em `val_cal`, para cada região, o corte de maior precisão entre os que dão sensibilidade ≥ 0,80, no modelo calibrado. Grave `outputs/final/limiares_por_regiao.csv` e `limiar.por_regiao` no YAML, sem substituir o corte global.

#### Parte da Pessoa B · 31/10 (relatório)
4. Em `val_meas` e no Teste A: corte global × corte regional por região (sensibilidade, precisão, especificidade, % de alertas).
5. `metricas_por_grupo` por região e UF no teste.
6. Figura de barras por região nos dois cortes e três frases (onde o corte regional ajuda, alguma região mal calibrada, o dilema de equidade).

#### Pronto quando
Métricas por região do `val_tune` comentadas no #140, cortes no YAML e figura e texto do relatório prontos.

## #138 · Opcional: "o mundo voltou?" Comparar 2019 com 2023–2025

- prioridade: P4
- situação: aberta
- estratégia: explorar
- marco: M6
- data ideal: 01/11
- responsável: Pessoa C ou Pessoa B, se sobrar tempo
- pessoas: C, B
- fonte: Orientação de 24/10 (sugestão do professor)
- depende de: #132
- tags: Metodologia, Temporal
- pilar: Valor científico-acadêmico
- carga: 2
- novo: sim
- professores: sim

### ① Para entender

O professor sugeriu verificar se, depois da pandemia, o padrão de risco "voltou" ao de antes. Uma forma barata: treinar só com o pós-pandemia e ver como o modelo se sai no pré-pandemia.

### ② Problema

Não bloqueia nada; é exploração para a Discussão.

### ③ O que fazer

**Dono:** Pessoa C ou Pessoa B · **Prazo:** 01/11, só se o relatório estiver encaminhado · **Esforço estimado:** ≈ 2 h

1. Treinar a logística (configuração do G6) só com `train_ref` de 2023–2025.
2. Medir em `val_meas` de 2019 e de 2023–2025: ROC-AUC, PR-AUC ÷ prevalência e O/E.
3. Comparar com o modelo completo nos mesmos recortes.
4. Leitura: se o modelo pós-pandemia for bem em 2019, o padrão de risco é parecido; se cair muito, 2019 é um "mundo" diferente (consistente com o #50).

**É o segundo item a ser cortado** (depois do 2026, #53).

## #111 · Recorte só de São Paulo como entrega mínima

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Plano B
- data ideal: 28/10
- responsável: Equipe
- pessoas: Equipe
- fonte: orientação de 17/10
- depende de: #119
- tags: Dados/Coorte
- pilar: —
- carga: —
- novo: sim
- professores: não

### ① Para entender

Plano de segurança do professor: se o modelo nacional ficar ruim, entregar SP funcionando. Como a partição e o código serão parametrizados, isso vira um filtro.

### ② Problema

Fazer agora gastaria tempo num resultado que talvez nem seja necessário.

### ③ O que fazer

Continua despriorizado. **Gatilho revisado para o novo calendário:** acionar só se, em 28/10, o finalista calibrado tiver PR-AUC/prevalência abaixo de 1,5 em `val_meas` **e** calibração ruim (O/E fora de 0,9–1,1). Nesse caso, o recorte de SP vira análise de sensibilidade no relatório, e não substituto do resultado nacional. Ninguém precisa fazer nada se o gatilho não disparar.

## #1 · Rodar o ajuste fino e preencher os hiperparâmetros no YAML

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M3
- data ideal: 29/10
- responsável: Pessoa C (dona; revisão cruzada sem edição concorrente)
- pessoas: C
- fonte: configs/supervised.yaml (gates G6, G7, G8; models; calibracao; limiar); notebooks C_13 e C_15
- depende de: #140
- tags: Modelagem, Gate, Notebook
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 4
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

Os gates `G6_finalistas_tuning`, `G7_calibracao` e `G8_limiar` estão **pendentes**. Os campos que dependem deles estão nulos: `models.logistic.C`, `models.boosting.learning_rate`, `max_iter`, `max_depth`, `calibracao.metodo`, `limiar.metrica` e `limiar.otimo`. O C_13 rodou sem busca ("G6 pendente"), e o C_15 calibrou e escolheu o limiar sobre os modelos com valores padrão (C=1 na logística; 0,05 / 500 no boosting).

### ③ O que fazer

**Dono:** Pessoa C · **Prazo:** 29/10 · **Esforço estimado:** ≈ 4 h · **Começa quando:** ponto de decisão da Fase E (#140)

#### Objetivo
Escolher a melhor configuração de cada finalista com uma busca curta e defensável, e decidir o modelo final.

#### O que é ajuste fino
Todo modelo tem "botões" que ele não aprende sozinho (hiperparâmetros). Testamos algumas combinações e ficamos com a que vai melhor num conjunto que o modelo não viu (`val_tune`). O professor aceitou fazer isso sem validação cruzada, por causa do tamanho da base.

#### Passo a passo
1. **Logística:** `C` em {0,01; 0,1; 1; 10}, penalidade L2. Para a melhor `C`, uma rodada extra de **regularização L1** (ou elastic-net com `l1_ratio=0,5`): anotar quantos coeficientes ficam diferentes de zero e se algum sinal muda. Isso é a parte de "regularização" pedida pela equipe e vira um parágrafo de Métodos.
2. **Boosting (categóricas nativas, sem one-hot):** 12 configurações aleatórias, semente 42, sobre `learning_rate` {0,05; 0,1}, `max_leaf_nodes` {31; 63}, `min_samples_leaf` {50; 200}, `l2_regularization` {0; 1}, `max_depth` {None; 8}, com `early_stopping=True` e `max_iter` até 1.000.
3. **Tempo:** rode primeiro uma configuração e meça. Se passar de 6 minutos, corte para 8 configurações. Se precisar, use subamostra do `train_ref` **por grupo** de até 600 mil fichas e retreine o vencedor no `train_ref` completo.
4. **Escolha dentro de cada família:** maior PR-AUC em `val_tune`; empate (diferença menor que 0,002) → a configuração mais simples.
5. **Peso de classe:** rodar o #5 no vencedor.
6. **Finalista:** o boosting só vence se superar a logística em pelo menos 0,005 de PR-AUC e não tiver Brier calibrado pior. No piloto ele estava 0,027 à frente.
7. **Registro:** `outputs/final/tuning_val_tune.csv` (uma linha por configuração, com tempo); hiperparâmetros no YAML; `selecao_modelos.finalista_escolhido`; liberar memória (`del` nos modelos descartados).

#### Pronto quando
CSV gravado, YAML preenchido e o #78 pronto para aprovar.

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

## #5 · Decidir se o peso das classes fica, já que ele infla as probabilidades

- prioridade: P1
- situação: parcial
- estratégia: desenvolver
- marco: M3
- data ideal: 29/10
- responsável: Pessoa C (dona; revisão cruzada sem edição concorrente)
- pessoas: C
- fonte: src/models/logistic.py; src/models/boosting.py; configs/supervised.yaml (class_weight); B_10
- depende de: #132
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

Os dois finalistas usam `class_weight="balanced"`. A média das probabilidades previstas ficou em 42,4% (boosting) e 43,0% (logística), contra prevalência real de 21,9%. Isso não afeta a ordenação (ROC-AUC, PR-AUC), mas afeta Brier, calibração e qualquer limiar.

**Atualização 17/10:** o C_15 mostrou que a calibração corrige o problema (boosting: Brier 0,1959 → 0,1409; ECE 0,0018). Ainda não foi testado treinar sem peso.

### ③ O que fazer

**Dono:** Pessoa C · **Prazo:** 29/10, dentro do ajuste fino · **Esforço estimado:** ≈ 1 h · **Começa quando:** #132

#### Objetivo
Decidir por evidência se o treino usa peso de classe.

#### O que é
Com `class_weight="balanced"`, cada óbito vale ≈ 11 casos no treino. O professor confirmou que isso **não impede** o modelo de identificar perfis. O efeito colateral é inflar as probabilidades: no piloto definitivo, a logística previa em média ≈ 34% de risco quando morriam 8,4%, e o Brier (0,165) ficou pior que o de um modelo que dá 8,4% para todos (0,077).

#### Passo a passo
1. No modelo vencedor do #1, treinar duas versões: `class_weight=None` e `class_weight="balanced"`.
2. Calibrar as duas em `val_cal` (mesmo método do #79) e medir em `val_meas`: PR-AUC, ROC-AUC e **Brier depois da calibração**.
3. Regra: manter `balanced` só se a PR-AUC subir pelo menos 0,005 **e** o Brier calibrado não piorar. Senão, `None`.
4. Gravar a escolha no YAML de todas as famílias ativas e uma linha no card para o #73.

#### Pronto quando
O YAML refletir a escolha e houver uma tabela com as duas versões.

## #78 · Aprovar o G6 para liberar o ajuste fino (busca de hiperparâmetros)

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M3
- data ideal: 29/10
- responsável: Pessoa C (aprova) + Pessoa A (registra)
- pessoas: C, A
- fonte: configs/supervised.yaml (gates.G6_finalistas_tuning); notebooks C_13
- depende de: #1, #5, #140
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

O gate `G6_finalistas_tuning` está `pendente`. Sem ele, o C_13 não faz a busca de hiperparâmetros. Antes de aprovar, o boosting precisa reproduzir o piloto, o uso de `class_weight` precisa estar incluído na busca e o tempo da busca precisa caber no prazo; caso contrário, o ajuste fino é feito sobre um modelo diferente da lista curta.

**Atualização 17/10:** o C_13 rodou e registrou "G6 pendente: busca não executada". O boosting do `src` continua com one-hot denso e sem categóricas nativas (item 4).

### ③ O que fazer

**Dono:** Pessoa C (aprova) + Pessoa A (registra) · **Prazo:** 29/10 · **Esforço estimado:** ≈ 30 min · **Começa quando:** #1, #5, #50

#### Checklist para aprovar o G6
1. #131, #135 e #132 concluídos: tudo rodou na coorte definitiva, em `train_ref` → `val_tune`.
2. Decisões do ponto de decisão da Fase E (#140), incluindo os três sintomas de 2019 (#50), tomadas e refletidas no YAML.
3. Ablações (#54) gravadas.
4. Busca (#1) dentro do tempo; peso de classe (#5) decidido.
5. Finalista e hiperparâmetros no YAML.

**Ação:** `gates.G6_finalistas_tuning.status: aprovado`, `aprovado_por: time_do_projeto`, `data: '2026-10-29'`. A Pessoa A registra a entrada no `decisoes.md`.

## #9 · Saturação, desconforto respiratório e vacina: cada documento diz uma coisa

- prioridade: P2
- situação: parcial
- estratégia: documentar
- marco: M1
- data ideal: 25/10
- responsável: Pessoa A (dona; revisão cruzada sem edição concorrente)
- pessoas: A
- fonte: docs/decisoes.md §13 e §17; Plano_Unificado_SRAG_3_Pessoas_v2.docx; configs/supervised.yaml (features)
- depende de: —
- tags: Diverge do decidido, Decisão, Features, Vazamento, Documentação
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1
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

Os três documentos tratam `saturacao`, `desc_resp` e `vacina` de formas diferentes. As decisões colocam saturação no Modelo A, desconforto no Modelo B e vacinação entre as candidatas clínicas. O plano v2 coloca as duas variáveis de gravidade em sensibilidade e a vacinação no modelo. O YAML coloca saturação e desconforto em `sensibilidade_gravidade_admissao` e a vacinação em `contexto_incremental`.

### ③ O que fazer

**Dono:** Pessoa A · **Prazo:** 25/10 · **Esforço estimado:** ≈ 1 h

#### Objetivo
Alinhar os documentos à decisão do G1: saturação e desconforto respiratório só em sensibilidade; vacinação só como contexto.

#### Passo a passo
1. `docs/decisoes.md` §13: reescreva (o texto atual põe saturação no "Modelo A"). Texto sugerido: "Saturação abaixo de 95% e desconforto respiratório são sinais fortes de gravidade, mas a ficha não registra quando foram anotados: podem ser da admissão ou do pior momento da internação. Por isso ficam fora do modelo principal e entram numa versão de sensibilidade (#54), com o ganho reportado."
2. §17: vacinação como contexto incremental, com a regra de doses do #84.
3. `configs/dicionario_variaveis_v1.csv`: coluna de uso igual ao G1 (faz junto com o #70).

#### Pronto quando
Os três documentos dizem a mesma coisa que o YAML.

## #13 · A sazonalidade é criada, mas não entra no modelo

- prioridade: P3
- situação: aberta
- estratégia: explorar
- marco: M3
- data ideal: 27/10
- responsável: Pessoa C (ablação) + Pessoa A (texto)
- pessoas: C, A
- fonte: src/features/engineering.py (sazonalidade); configs/supervised.yaml (features); docs/decisoes.md §7
- depende de: #132
- tags: Diverge do decidido, Código, Features, Documentação
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1
- novo: não
- professores: não

### ① Para entender

> [!decisão] Decisão de 18/10
> Não incluir a sazonalidade agora (mais dimensões, ganho incerto); documentar como limitação.

`sin_semana` e `cos_semana` transformam a semana do ano num círculo, para o modelo entender que a semana 52 é vizinha da semana 1. Elas são criadas, mas não estão na lista de features. Além disso, `decisoes.md` cita nomes que não existem no código.

> [!exemplo] Exemplo
> Sem o círculo, a semana 52 e a semana 1 parecem estar a 51 semanas de distância, quando estão a uma.

### ② Problema

`sin_semana` e `cos_semana` são criadas por `montar_features`, mas não aparecem em `features.numericas`; portanto, a sazonalidade não entra no modelo. As decisões citam nomes que não existem no código: `semana_sen`, `semana_cos` e `flag_intervalo_negativo_inesperado`.

### ③ O que fazer

**Resolvido dentro do #54** (linha "P + sazonalidade"). A sazonalidade não entra no modelo principal (G1 congelado). Se a ablação mostrar ganho de pelo menos 0,005 de PR-AUC, vira achado da Discussão: a sazonalidade carrega informação de onda epidêmica.

**Pessoa A:** a correção dos nomes na §7 do `decisoes.md` está no #73.

## #54 · Rodar as sensibilidades de gravidade, contexto e "qualquer óbito"

- prioridade: P1
- situação: aberta
- estratégia: explorar
- marco: M3
- data ideal: 27/10
- responsável: Pessoa C (execução) + Pessoa A (relatório)
- pessoas: C, A
- fonte: configs/supervised.yaml (sensibilidades); Projeto
- depende de: #132
- tags: Metodologia, Modelagem
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 4
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

Faltam as sensibilidades de gravidade na admissão (com `saturacao` e `desc_resp`), de contexto incremental e de alvo "qualquer óbito". Dependem do item 7, porque as colunas não estão no artefato.

### ③ O que fazer

**Dono:** Pessoa C (execução) + Pessoa A (tabela no relatório) · **Prazo:** 27/10 (Fase E), antes do ponto de decisão · **Esforço estimado:** C ≈ 3 h · A ≈ 30 min · **Começa quando:** #132

#### Objetivo
Uma única tabela que mostra quanto cada grupo de informação acrescenta ao modelo. É o resultado "de laboratório" mais rico do trabalho e custa pouco, porque reusa o mesmo pipeline.

#### O que é ablação
Treinar o mesmo modelo várias vezes, tirando ou acrescentando um bloco de variáveis, e comparar. A diferença mostra o valor daquele bloco.

#### Linhas da tabela (todas em `val_tune`, hiperparâmetros padrão, semente 42)
| Linha | Conjunto | Item |
|---|---|---|
| P | 31 features do G1 | — |
| P − 3 sintomas | sem `perd_olft`, `perd_pala`, `fadiga` | #50 |
| P + sazonalidade | + `sin_semana`, `cos_semana` | #13 |
| P + gravidade | + `saturacao`, `desc_resp` | #9 |
| P + contexto | + `cs_escol_n`, `vacina` (+ `vacina_cov_antes_admissao` se o #84 estiver pronto) | #84 |
| P + região | + `regiao_residencia` | #110 |
| Alvo "qualquer óbito" | P, com evolução 2 ou 3 como positivo | — |

#### Passo a passo
1. Montar o pré-processador de cada linha com as listas do manifesto mais o bloco extra declarado explicitamente (#15), nunca por diferença de listas.
2. Rodar primeiro com a **logística** (minutos). Rodar o **boosting** só para P e P − 3, que alimentam a decisão do #50.
3. Para cada linha: PR-AUC, PR-AUC ÷ prevalência, ROC-AUC, Brier, tempo de treino, número de colunas depois da codificação e diferença para P. Usar o bootstrap pareado do #127 para o intervalo da diferença, se estiver pronto; senão, sem intervalo e com nota.
4. Salvar `outputs/final/ablacoes_val_tune.csv` e avisar no card.

#### Regras de leitura
- Nenhuma linha substitui o modelo principal (G1 congelado), exceto pela decisão do #50.
- Diferença menor que 0,005 de PR-AUC = "sem ganho prático".
- O alvo "qualquer óbito" muda a prevalência: comparar só PR-AUC ÷ prevalência e ROC-AUC.

#### Pronto quando
O CSV existir e a Pessoa A tiver colado a tabela no relatório.

## #52 · Fichas de óbito têm as doenças prévias mais preenchidas

- prioridade: P3
- situação: aberta
- estratégia: explorar
- marco: M3
- data ideal: 28/10
- responsável: Pessoa A (Fase E, val_tune) · Pessoa B (repete no teste, 31/10)
- pessoas: A, B
- fonte: Projeto (análise de desempenho)
- depende de: #132
- tags: Metodologia, Vazamento
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 3
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

As comorbidades estão mais preenchidas nos óbitos (diferença de 13 a 21 pontos percentuais). Pode ser viés de documentação: fichas de óbito são revisadas com mais cuidado. Nesse caso, o modelo aprende o preenchimento, não a condição clínica.

### ③ O que fazer

> [!decisão] Replanejamento de 26/10: exploração antes da validação
> A troca para a coorte definitiva é uma base "nova": antes de ajustar e validar modelos, todas as análises que podem mudar decisões (variáveis, representação, limiar, calibração, leitura por região) rodam na **Fase E (26 a 28/10)**, sobre o `train_ref` e o `val_tune`. Os achados são discutidos no **ponto de decisão do #140 (28/10 à noite)**. Só então começam o ajuste fino (29/10) e a validação. Depois do teste, as mesmas análises são apenas repetidas para o relatório, sem decidir nada.

**Dono:** Pessoa A (Fase E) · Pessoa B (relatório) · **Prazo:** 28/10 (A) · 31/10 (B) · **Esforço estimado:** A ≈ 2 h · B ≈ 1 h · **Começa quando:** previsões do piloto em `val_tune` (#132)

#### Por que importa
Nas fichas de óbito, as comorbidades ficam 13 a 21 pontos percentuais **menos em branco** (cardiopatia em branco: 39% nos óbitos × 60% nas curas). Se o modelo aprendeu "ficha completa ⇒ óbito", parte do desempenho é hábito de registro (viés de documentação). Descobrir isso **antes** do ajuste permite reagir (por exemplo, testar uma versão sem as categorias `AUSENTE` das comorbidades).

#### Parte da Pessoa A (28/10, sobre o `val_tune`)
1. Leia `outputs/final/predicoes_val_tune_piloto.parquet` (exportado pela Pessoa C no #132) e junte às variáveis do artefato por `id_registro`, lendo só os 11 sintomas e 12 comorbidades.
2. Calcule a **completude** de cada ficha: % desses 23 campos com resposta 1 ou 2.
3. Divida em terços de completude (`pd.qcut(..., 3)`). Por terço: fichas, prevalência, ROC-AUC, PR-AUC ÷ prevalência e O/E (use `metricas_por_grupo` do #23 com `coluna_grupo` = terço).
4. Salve `outputs/final/completude_val_tune.csv` e comente no #140: se desempenho **e** prevalência sobem juntos com a completude, sinal de viés de documentação.

#### Parte da Pessoa B (31/10, para o relatório)
5. Repita os passos 2 a 4 em `predicoes_val_meas.parquet` e no Teste A, sem decidir nada. Salve `completude_val_meas.csv` e escreva o parágrafo de limitações.

#### Pronto quando
CSV do `val_tune` comentado no #140 (28/10) e o do relatório pronto (31/10).

## #109 · UMAP em sintomas e comorbidades: clustering no espaço latente e uma ablação supervisionada

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 03/11
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

Nenhuma redução além do PCA foi testada; `umap-learn` não está nas dependências.

### ③ O que fazer

Continua **pós-entrega**. A parte de não supervisionado pedida pelos professores é atendida pelo #136 (one-hot e normalização) e pelo #137 (testes estatísticos). UMAP só se um professor pedir explicitamente: nesse caso, uma figura 2D numa amostra de 50 mil do `train_ref`, colorida pelos grupos do #136 (Pessoa B, 01/11, ≈ 2 h).

## #2 · Executar o C_16 uma única vez nas duas janelas de teste autorizadas

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M5
- data ideal: 31/10
- responsável: Pessoa C (dona; revisão cruzada sem edição concorrente)
- pessoas: C
- fonte: notebooks C_16; configs/supervised.yaml (features.final, selecao_modelos.finalista_escolhido)
- depende de: #81, #132
- tags: Notebook, Gate, Dados/Coorte
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 3
- novo: não
- professores: não

### ① Para entender

> [!ok] Decisão fechada em 18/10
> A coorte definitiva inicial será a seleção de features da coorte provisória. O treino principal usará exclusivamente 2019, 2023, 2024 e 2025. Haverá duas janelas de teste: (A) 2019, 2023, 2024 e 2025; (B) 2019 a 2025, incluindo 2020–2022. O ano de 2026 não participa do desenvolvimento nem dos testes principais e fica apenas como exploração opcional, depois de todo o restante concluído.

O C_16 abre o teste e calcula o resultado oficial. Ele se recusa a rodar se a lista final de variáveis e o finalista não estiverem escolhidos, e esses dois dependem da coorte definitiva.

> [!atenção] Atenção
> Não preencha `features.final` com a lista provisória só para o C_16 rodar: isso gastaria a única abertura do teste num modelo que ainda vai mudar.

### ② Problema

O C_16 interrompe a execução quando `features.final` ou `selecao_modelos.finalista_escolhido` estão vazios. Os dois campos dependem da coorte definitiva e da aprovação do G1, que ainda está pendente. Portanto, o C_16 não pode rodar antes de a coorte definitiva chegar.

### ③ O que fazer

**Dono:** Pessoa C · **Prazo:** 31/10 de manhã · **Esforço estimado:** ≈ 3 h · **Começa quando:** G9

1. Kernel limpo. Rodar o C_16 inteiro de uma vez.
2. Se quebrar **antes** de carregar os testes: corrigir e rodar de novo. Se quebrar **depois**: corrigir só o código de relatório (nunca modelo, calibrador ou limiar) e registrar no card.
3. Gerar tudo o que o #119 lista e exportar as previsões.
4. Commit só de tabelas e figuras: `resultados: testes A e B [done:#2]`.
5. Avisar no card: "testes abertos às HH:MM; nenhuma decisão de modelagem muda a partir daqui".

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

## #79 · Aprovar o G7: escolher o método de calibração (proposta do C_15: sigmoid)

- prioridade: P1
- situação: parcial
- estratégia: desenvolver
- marco: M4
- data ideal: 29/10
- responsável: Pessoa C (dona; revisão cruzada sem edição concorrente)
- pessoas: C
- fonte: configs/supervised.yaml (gates.G7_calibracao; calibracao.metodo); notebooks C_15
- depende de: #1
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

O gate `G7_calibracao` está **pendente** e `calibracao.metodo` está `null`. O C_15 já rodou sobre os modelos com valores padrão e propôs `calibracao.metodo: sigmoid` (boosting: Brier 0,1959 → 0,1409; ECE 0,0018). Como o ajuste fino (G6) ainda não aconteceu, essa escolha foi feita sobre um modelo que ainda vai mudar.

### ③ O que fazer

**Dono:** Pessoa C · **Prazo:** 29/10 · **Esforço estimado:** ≈ 2 h · **Começa quando:** G6

#### O que é calibração
Fazer com que "30% de risco" signifique cerca de 30 óbitos em cada 100 fichas parecidas. A calibração quase não muda a ordem dos pacientes (ROC-AUC fica igual); ela corrige o **número**.

#### Passo a passo
1. Sobre o finalista congelado (`FrozenEstimator`), ajustar dois métodos só em `val_cal`: **sigmoid** (curva suave em S) e **isotônica** (escada flexível).
2. Medir em `val_meas`: Brier, log loss, intercepto e inclinação de calibração (regressão logística de y em logit(p)), ECE com 10 faixas por quantis e curva de calibração (figura).
3. **Regra de escolha:** menor Brier em `val_meas`; diferença menor que 0,0005 → sigmoid.
4. Conferir que a ordenação não mudou (PR-AUC e ROC-AUC iguais, com tolerância).
5. YAML: `calibracao.metodo` e `G7_calibracao: aprovado` com data. Linha no card para o #73.

#### Referência para conferir se faz sentido
No piloto antigo, o boosting calibrado foi de Brier 0,196 para 0,141. Espera-se o Brier calibrado abaixo de 0,077 (o do modelo nulo).

## #80 · Aprovar o G8: escolher o limiar (proposta do C_15: 0,255 pelo F1)

- prioridade: P1
- situação: parcial
- estratégia: desenvolver
- marco: M4
- data ideal: 30/10
- responsável: Pessoa C (dona; revisão cruzada sem edição concorrente)
- pessoas: C
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

O gate `G8_limiar` está **pendente**, e `limiar.metrica` e `limiar.otimo` estão `null`. O C_15 propôs `limiar.metrica: f1` e `limiar.otimo: 0.255`, calculados sobre probabilidades calibradas de um modelo ainda sem ajuste fino. Não está decidido se o projeto usa um limiar único ou faixas de risco.

### ③ O que fazer

**Dono:** Pessoa C · **Prazo:** 30/10 · **Esforço estimado:** ≈ 2 h · **Começa quando:** #79

#### O que é
O ponto de corte que transforma probabilidade em "alerta". Mexer nele troca óbitos perdidos por alarmes falsos. O professor disse que 80% de sensibilidade "já está bom" e 70% "já está muito bom".

#### Passo a passo
1. Em `val_cal`, com as probabilidades calibradas, calcular para cada corte possível: sensibilidade, precisão, especificidade, F1 e % de fichas com alerta.
2. **Corte principal:** o de maior precisão entre os que têm sensibilidade ≥ 0,80.
3. **Cortes de referência** (só para mostrar): sensibilidade ≥ 0,70, F1 máximo e Youden.
4. Tabela de cortes de 0,05 a 0,60 (passo 0,05) para o apêndice.
5. Medir os cortes em `val_meas` sem alterá-los.
6. Faixas de risco (baixo, médio, alto, pelos tercis da probabilidade calibrada em `val_cal`) só como descrição.
7. **Por região:** os cortes por região (#110) usam a mesma regra; este item entrega só o global.
8. YAML: `limiar.metrica: recall_minimo`, `limiar.min_recall: 0.80`, `limiar.otimo`, `G8_limiar: aprovado` com data.

#### Pronto quando
O YAML tiver o corte e houver `outputs/final/limiares_val_cal.csv`.

## #81 · Aprovar o G9 e liberar as duas janelas de teste uma única vez

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M5
- data ideal: 30/10
- responsável: Pessoa A (conduz o checklist) + Pessoa C (modelagem) + Equipe (aprova)
- pessoas: A, C, Equipe
- fonte: configs/supervised.yaml (gates.G9_holdout); notebooks C_16
- depende de: #77, #79, #80, #131
- tags: Gate, Vazamento
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 2
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

O gate `G9_holdout` está `pendente`. Ele libera o teste uma única vez e é irreversível: depois de `executado`, nenhuma decisão de modelagem pode mudar. Só pode ser aprovado com modelo, features, calibração e limiar congelados e com a proteção do teste funcionando.

### ③ O que fazer

**Dono:** Pessoa A (conduz) + Pessoa C (modelagem) + Equipe (aprova) · **Prazo:** 30/10 · **Esforço estimado:** A ≈ 1 h · C ≈ 30 min

#### O que é
O G9 libera o teste **uma única vez**. Depois dele, nada do modelo pode mudar. É o envelope da nota final.

#### Checklist (a Pessoa A confere item por item no repositório e marca aqui)
1. Coorte e artefato com SHA-256 no manifesto (#131); invariantes passando (#135).
2. G1, G6, G7 e G8 aprovados no YAML, com data.
3. `finalista_escolhido`, `run_id_finalista`, `calibracao.metodo` e `limiar.*` preenchidos.
4. Medição em `val_meas` registrada (a última foto antes do teste).
5. Proteção do teste testada (o teste rápido do #131) e `pytest -m "not slow"` passando.
6. `marcar_teste_aberto` (#26) pronto e chamado no C_16.
7. Commit com a tag `congelado-2026-10-30` e o SHA anotado aqui.

#### Aprovação
Cada pessoa comenta "aprovo o G9" (a Pessoa B volta na noite de 30/10 e pode aprovar do celular). Com duas aprovações e nenhuma objeção em 12 horas, a Pessoa C muda `G9_holdout.status: aprovado` e roda o #2 na manhã de 31/10.

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

## #126 · Execução limpa da cadeia final e pacote de reprodução

- prioridade: P2
- situação: aberta
- estratégia: desenvolver
- marco: M6
- data ideal: 01/11
- responsável: Pessoa A (reprodução independente e README) + Pessoa C (script)
- pessoas: C, A
- fonte: tools/executar_cadeia.py (do Plano de Performance)
- depende de: #2
- tags: Memória/Desempenho, Ambiente, Testes
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 5
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

Hoje a cadeia é rodada à mão, no mesmo kernel, e a memória se acumula.

### ③ O que fazer

**Dono:** Pessoa C (script, até 31/10) + Pessoa A (reprodução independente e README, 01/11) · **Prazo:** 01/11 · **Esforço estimado:** C ≈ 2 h · A ≈ 3 h

#### Por que a Pessoa A reproduz
Uma reprodução feita por outra pessoa, em outra máquina, é a melhor prova de que o trabalho é reprodutível.

#### Parte da Pessoa C
1. `tools/executar_cadeia.py`: roda em processos separados (`jupyter nbconvert --execute --inplace`) a cadeia final: construção da coorte (CLI) → artefato (#131) → C_11 → C_12 → C_13 (hiperparâmetros fixos, sem busca) → C_15. **O C_16 não roda de novo** (o teste já foi aberto).
2. O script confere os SHA-256 esperados e grava tempo e pico de memória por etapa num CSV.

#### Parte da Pessoa A
3. Na sua máquina: clonar o repositório limpo, criar o `.venv`, instalar o `requirements.txt`, baixar a tag de dados e rodar o script. Anotar cada problema no card.
4. README, seção "Como reproduzir": versão do Python, instalação, onde baixar os dados, ordem dos comandos, tempo e memória esperados.
5. Tag `entrega-2026-11-03` no commit final (com a Pessoa C).

**Se não der:** README honesto com a ordem manual e os hashes esperados.

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

## #26 · O manifesto nunca registra que o teste foi aberto

- prioridade: P2
- situação: aberta
- estratégia: desenvolver
- marco: M5
- data ideal: 29/10
- responsável: Pessoa A (função e teste) · Pessoa C (chamada no C_16)
- pessoas: A
- fonte: src/data/supervised_artifact.py (manifesto); notebooks C_16
- depende de: #131
- tags: Código, Vazamento
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 2
- novo: não
- professores: não

### ① Para entender

O campo `test_opened` do manifesto fica sempre `false`, mesmo depois do C_16. O registro só existe no YAML.

### ② Problema

O manifesto tem o campo `test_opened`, mas ele nunca muda para `True`, nem depois de o C_16 consultar o teste. O registro de abertura fica só no YAML.

### ③ O que fazer

**Dono:** Pessoa A · **Prazo:** 29/10 · **Esforço estimado:** ≈ 1 h 30 · **Revisão:** Pessoa C

1. Em `src/data/supervised_artifact.py`, crie `marcar_teste_aberto(root) -> dict`: lê o manifesto, grava `test_opened: true`, `test_opened_at` (data e hora UTC) e o commit atual (`git rev-parse HEAD`), escrevendo num arquivo temporário e trocando com `os.replace` (assim o manifesto nunca fica pela metade).
2. Se o manifesto já tiver `test_opened: true`, a função **não** sobrescreve a data original: devolve o que já estava e emite um aviso.
3. Teste em `tests/test_supervised_artifact.py` com um manifesto falso numa pasta temporária (`tmp_path`): primeira chamada grava; segunda chamada não muda a data.
4. Avise a Pessoa C para chamar a função no C_16, logo depois de carregar os testes.

**Pronto quando:** teste passando e a chamada no C_16.

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

## #45 · Vacina contra COVID marcada como "sim" antes de existir a vacina

- prioridade: P3
- situação: aberta
- estratégia: documentar
- marco: M6
- data ideal: 31/10
- responsável: Pessoa A (dona; revisão cruzada sem edição concorrente)
- pessoas: A
- fonte: B_06 (achado); configs/supervised.yaml (contexto_incremental); src/features/engineering.py
- depende de: #84
- tags: Dados/Coorte, Features
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1
- novo: não
- professores: não

### ① Para entender

Há 55 fichas de 2019 e 24.284 de 2020 com vacina contra COVID = sim. O YAML usa o campo bruto, sem olhar a data da dose.

<div class="bars">
<div class="br"><span class="y">2019</span><div class="t"><div class="b " style="width:2.0%"></div></div><span class="v">55</span></div>
<div class="br"><span class="y">2020</span><div class="t"><div class="b red" style="width:97.1%"></div></div><span class="v">24.284</span></div>
</div>

### ② Problema

Há registros com vacina contra COVID-19 marcada como "sim" em 2019 (55) e em 2020 (24.284), antes de a vacina existir. O YAML usa `vacina_cov` bruta, sem considerar a data da dose, o que contraria a seção 17 das decisões.

### ③ O que fazer

**Pessoa A, 31/10, 15 minutos:** uma frase nas limitações com as contagens (55 "sim" em 2019 e 24.284 em 2020, antes da vacina existir) e a regra adotada (#84). A vacinação está fora do modelo principal.

## #46 · 58 linhas repetem 29 números de notificação na base bruta

- prioridade: P3
- situação: aberta
- estratégia: documentar
- marco: M6
- data ideal: 31/10
- responsável: Pessoa A (dona; revisão cruzada sem edição concorrente)
- pessoas: A
- fonte: Construção da coorte
- depende de: #10, #135
- tags: Dados/Coorte
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1
- novo: não
- professores: não

### ① Para entender

Pode ser reenvio da mesma ficha ou erro de digitação. A regra definitiva fica com o item 10.

### ② Problema

Na base bruta, 58 linhas repetem 29 números de notificação.

### ③ O que fazer

**Pessoa A, 31/10, 10 minutos:** uma frase no relatório com a contagem de números de notificação repetidos **na coorte definitiva** (do #135) e a regra de grupo (#10). A contagem de 58/29 é da base bruta.

## #47 · Idades, datas e anos impossíveis

- prioridade: P3
- situação: aberta
- estratégia: documentar
- marco: M6
- data ideal: 31/10
- responsável: Pessoa A (dona; revisão cruzada sem edição concorrente)
- pessoas: A
- fonte: Construção da coorte
- depende de: #135
- tags: Dados/Coorte
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1
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

Há 24 idades implausíveis (mantidas com a idade vazia), 17 internações com data posterior ao fechamento da base e 260 datas com ano fora da faixa válida.

### ③ O que fazer

**Pessoa A, 31/10, 20 minutos:** usar a contagem de `idade_anos` vazia por bloco (#135) numa frase de Métodos ("idades implausíveis foram tratadas como ausentes e imputadas pela mediana do treino, n = …") e as contagens de datas fora do período do manifesto de auditoria numa tabela do apêndice.

## #56 · Mostrar por que a data de internação é a âncora, e quem ficou de fora

- prioridade: P2
- situação: aberta
- estratégia: documentar
- marco: M4
- data ideal: 31/10
- responsável: Pessoa B
- pessoas: B
- fonte: B_06_eda_temporal_clustering; construção da coorte
- depende de: —
- tags: Metodologia, Dados/Coorte, Documentação
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 3
- novo: não
- professores: não

### ① Para entender

Falta a tabela da diferença entre `dt_notific` e `dt_interna`, que sustenta a escolha da âncora, e a comparação entre os casos excluídos por falta de desfecho e os incluídos.

<div class="kpi">
<div><b>97.786</b>excluídos por evolução não encerrada (waterfall A_03)</div>
<div><b>36.923</b>excluídos por óbito por outra causa ou ignorado</div>
</div>

### ② Problema

Não foram produzidas a tabela da diferença entre `dt_notific` e `dt_interna`, que sustenta a escolha da internação como âncora, e a comparação entre casos excluídos por falta de desfecho e casos incluídos.

### ③ O que fazer

**Dono:** Pessoa B · **Prazo:** 31/10 · **Esforço estimado:** ≈ 3 h · **Revisão:** Pessoa A (números no relatório)

#### Por que a banca vai pedir
Duas perguntas típicas de saúde pública: "por que a data de internação, e não a de notificação?" e "quem ficou de fora da coorte?" (viés de seleção).

#### Passo a passo
1. Leia da fonte só `dt_notific`, `dt_interna`, `dt_sin_pri`, `evolucao`, `sg_uf`, `nu_idade_n`, `tp_idade`, `hospital`, `nosocomial` (`read_srag(columns=[...])`).
2. **Tabela 1 (âncora):** dias entre notificação e internação (`dt_notific − dt_interna`), mediana e intervalo interquartil, por ano e por desfecho. Normalmente a notificação vem depois: por isso a âncora é a internação.
3. **Tabela 2 (quem ficou de fora):** hospitalizados excluídos por desfecho não elegível (evolução 3, 9 ou vazio) × incluídos: % por ano, região e faixa etária.
4. **Tabela 3 (casos hospitalares):** entre as internações com intervalo negativo (excluídas pela `D_COORTE_006`), quantas são `nosocomial` = 1, 2, 9 ou vazio, e o desfecho. Responde "e os casos adquiridos no hospital?".
5. Salve em `outputs/final/ancora_notificacao_internacao.csv`, `excluidos_vs_incluidos.csv` e `intervalo_negativo_nosocomial.csv`.
6. Uma frase de leitura para cada tabela, no relatório (seção 2).

**Pronto quando:** as três tabelas e as frases existirem.

## #69 · Plano v2 e orientação de TCC descrevem outro período e outra divisão

- prioridade: P3
- situação: aberta
- estratégia: documentar
- marco: M6
- data ideal: 31/10
- responsável: Pessoa A (dona; revisão cruzada sem edição concorrente)
- pessoas: A
- fonte: Plano_Unificado_SRAG_3_Pessoas_v2.docx
- depende de: —
- tags: Documentação, Partição
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1
- novo: não
- professores: não

### ① Para entender

> [!ok] Decisão fechada em 18/10
> A coorte definitiva inicial será a seleção de features da coorte provisória. O treino principal usará exclusivamente 2019, 2023, 2024 e 2025. Haverá duas janelas de teste: (A) 2019, 2023, 2024 e 2025; (B) 2019 a 2025, incluindo 2020–2022. O ano de 2026 não participa do desenvolvimento nem dos testes principais e fica apenas como exploração opcional, depois de todo o restante concluído.

Os dois documentos falam em 2022–2025 com divisão temporal. O projeto executou 2019–2026 com sorteio estratificado. Quem ler os planos vai entender outro estudo.

### ② Problema

O plano v2 ainda descreve treino 2022–2023, validação 2024, teste 2025, 2026 fora e âncora temporal com 2026 excluído. Isso contradiz a decisão vigente: período 2019–2026 com divisão aleatória 70/15/15 estratificada e coorte provisória.

### ③ O que fazer

**Dono:** Pessoa A · **Prazo:** 31/10 · **Esforço estimado:** ≈ 30 min

1. No topo do Plano Unificado v2 e da Orientação Intermediária de 03/10 (se forem para o repositório ou para a pasta da equipe): "HISTÓRICO. Período, divisão e prazo substituídos em 18/10; ver docs/decisoes.md §28."
2. No relatório (Métodos), um parágrafo de trajetória: "o desenho inicial previa desenvolvimento em 2022–2024 e avaliação em 2025; foi substituído por treino em 2019 e 2023–2025 com duas janelas de teste porque …". Mostrar a evolução conta a favor.

## #70 · Dicionário de variáveis desatualizado e com arquivo fantasma

- prioridade: P2
- situação: aberta
- estratégia: documentar
- marco: M4
- data ideal: 28/10
- responsável: Pessoa A (dona; revisão cruzada sem edição concorrente)
- pessoas: A
- fonte: configs/dicionario_variaveis_v1.csv; docs/decisoes.md §25
- depende de: —
- tags: Documentação, Dados/Coorte
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 2
- novo: não
- professores: não

### ① Para entender

O dicionário ainda põe saturação no "Modelo A" e tem 36 colunas com revisão pendente. O README e o `decisoes.md` citam `dicionario_variaveis_v1_revisao.csv`, que não existe (alertas A18 e A20).

### ② Problema

O dicionário mantém a classificação original (saturação no "Modelo A") e tem 36 colunas com pontos de revisão sem decisão. A seção 25 das decisões diz que o dicionário é o único arquivo editável, mas a introdução das decisões cita um segundo arquivo, `dicionario_variaveis_v1_revisao.csv`.

### ③ O que fazer

**Dono:** Pessoa A · **Prazo:** 28/10 · **Esforço estimado:** ≈ 2 h

1. Em `configs/dicionario_variaveis_v1.csv`, coluna `uso_inicial_sugerido` (ou a coluna de papel no contrato): refletir o G1. Hoje `saturacao`, `fadiga`, `perd_olft`, `perd_pala` e `vacina_cov` aparecem como `modelo_a_nucleo`; corrigir para o papel atual.
2. Das 36 linhas com revisão pendente, feche **só** as das variáveis usadas (principais, contexto, gravidade). As demais recebem `pos_entrega` na coluna de status de revisão.
3. Remova a citação ao arquivo `dicionario_variaveis_v1_revisao.csv` (não existe) do README, se ainda estiver lá.
4. Faça junto com o #40: a tabela de variáveis finais sai deste dicionário.

**Pronto quando:** nenhuma variável usada tiver papel diferente do G1.

## #71 · Cuidados de redação no relatório

- prioridade: P2
- situação: aberta
- estratégia: documentar
- marco: M7
- data ideal: 01/11
- responsável: Pessoa A (dona; revisão cruzada sem edição concorrente)
- pessoas: A
- fonte: Projeto (relatório)
- depende de: #55, #91
- tags: Documentação, Metodologia
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 2
- novo: não
- professores: não

### ① Para entender

- A unidade é a **notificação**, não a pessoa.
- As associações são **preditivas**, não causais.
- 2026 é ano **parcial**.
- O modelo foi avaliado com **sorteio**; a validação em anos futuros é complementar.
- A lista de variáveis importantes (item 91) é de associação, não de causa.

### ② Problema

Pontos de redação: a unidade de análise é a notificação, não a pessoa; as associações são preditivas, não causais; 2026 é ano parcial; o modelo, avaliado com divisão aleatória, não foi validado em anos futuros.

### ③ O que fazer

**Pessoa A aplica no relatório e nos slides em 01/11; Pessoa B confere em 02/11.** Lista de verificação:
- "notificações", não "pacientes" ou "pessoas";
- "associado a maior risco previsto", nunca "causa" ou "protege";
- Teste A × B: "robustez à mudança de período", nunca "efeito da pandemia";
- "demonstração acadêmica retrospectiva; não validado para uso clínico";
- 2026: "parcial";
- geografia: "heterogeneidade entre regiões, que pode refletir acesso, capacidade e registro";
- ausência: "ausência de registro", não "ausência da condição";
- todo número com origem num arquivo de `outputs/final/` ou manifesto.

## #133 · Relatório final: esqueleto, seções e rastreabilidade de cada número

- prioridade: P1
- situação: aberta
- estratégia: documentar
- marco: M6
- data ideal: 01/11
- responsável: Pessoa A (dona) + Pessoa B (EDA e perfis) + Pessoa C (conferência técnica)
- pessoas: A, B, C
- fonte: Revisão de 24/10; base de conhecimento v7 (contratos assíncronos e definição de pronto)
- depende de: #97
- tags: Documentação, Metodologia
- pilar: Valor científico-acadêmico
- carga: 15
- novo: sim
- professores: não

### ① Para entender

O relatório é a entrega avaliada. Ele precisa existir em paralelo à modelagem, com lugares marcados para os números que só chegam em 30/10, e não começar em 31/10.

### ② Problema

Nenhum item do painel cobria a redação. Com a Pessoa B fora de 25 a 30/10 e a Pessoa C no caminho crítico, sem um dono e um esqueleto agora o texto vira gargalo em 31/10–02/11.

### ③ O que fazer

**Dono:** Pessoa A (dona) + Pessoa B (seções de EDA, não supervisionado e interpretação) + Pessoa C (conferência técnica) · **Prazo:** esqueleto 25/10 · Dados e Métodos 29/10 · Resultados 31/10 · completo 01/11 · **Esforço estimado:** A ≈ 10 h · B ≈ 4 h · C ≈ 1 h · **Começa quando:** #97 (formato)

#### Roteiro (TRIPOD) e de onde vem cada parte
| Seção | Conteúdo | Fonte |
|---|---|---|
| 1. Introdução | Pergunta, relevância para a saúde pública, lacuna | #112 |
| 2. Dados e coorte | SIVEP-Gripe; waterfall de 4.666.910 → 3.884.728; regras D_COORTE; qualidade (campos de 2019, viés de documentação, vacinação) | #73, #56, #50, #45, #47 |
| 3. Desfecho e variáveis | Alvo; 31 variáveis; o que ficou de fora e por quê (vazamento, gravidade) | #40, #9 |
| 4. Desenho temporal e partição | Seis blocos, grupos, estratificação, invariantes | #131, #135 |
| 5. Representação | One-hot e escala na logística; categóricas nativas no boosting; one-hot dos quatro estados no não supervisionado | #136, base v9 §6.3 |
| 6. Modelos e ajuste | Dummy, logística (L2 e sensibilidade L1), boosting; busca; peso de classe | #1, #5 |
| 7. Calibração e limiar | Método, corte global e por região | #79, #80, #110 |
| 8. Resultados | Teste A, Teste B, 2020–2022, por ano; ablações; IC | #119, #54 |
| 9. O que pesa no risco | Bruto × ajustado; permutação | #91 |
| 10. Não supervisionado | Representação antiga × nova; perfis estatísticos | #136, #137, #60 |
| 11. Discussão | Drift, sintomas de 2019, viés de documentação, equidade regional | #50, #52, #55, #110 |
| 12. Limitações e conclusão | | #71 |

#### Passo a passo
1. **25/10:** esqueleto no formato do #97 (ou no padrão TRIPOD), com todas as seções e marcadores `[NÚMERO: arquivo]` onde entram números.
2. **26–29/10:** escrever Dados, Coorte, Variáveis, Desenho e Métodos (não dependem do teste).
3. **Planilha de rastreabilidade:** cada número do texto → arquivo e coluna de origem. Número sem origem sai do texto.
4. **31/10:** Resultados a partir de `outputs/final/`, colando tabelas dos arquivos (nunca redigitando).
5. **Seções da Pessoa B:** EDA, não supervisionado e interpretação (rascunho no tablet durante a viagem; fechamento em 31/10).
6. **01/11:** versão completa; revisão de linguagem (#71).
7. **02/11:** a Pessoa C confere todos os números técnicos.

**Pronto quando:** documento completo no formato pedido, sem número órfão.

## #134 · Apresentação e defesa: roteiro, slides e perguntas difíceis

- prioridade: P2
- situação: aberta
- estratégia: documentar
- marco: M7
- data ideal: 02/11
- responsável: Pessoa B (roteiro, slides e respostas) + Pessoa A (números) + Pessoa C (revisão técnica)
- pessoas: B, A, C
- fonte: Revisão de 24/10
- depende de: #97, #119
- tags: Documentação
- pilar: Valor científico-acadêmico
- carga: 8
- novo: sim
- professores: não

### ① Para entender

A apresentação precisa contar a mesma história do relatório em poucos minutos, com os números finais e respostas preparadas para as perguntas previsíveis da banca.

### ② Problema

Não havia item para a apresentação. As perguntas difíceis (vazamento, por que excluir 2020–2022 do treino, por que PR-AUC, calibração, geografia) precisam de resposta curta e ensaiada.

### ③ O que fazer

**Dono:** Pessoa B (roteiro, slides e respostas) + Pessoa A (números) + Pessoa C (revisão técnica) · **Prazo:** 01/11 (slides) e 02/11 (ensaio) · **Esforço estimado:** B ≈ 6 h · A ≈ 1 h · C ≈ 1 h

#### Para quem
Colegas que **não conhecem** o projeto (orientação de 24/10). Linguagem simples, uma ideia por slide.

#### Roteiro (10 a 12 slides)
1. O problema: SRAG, mortalidade, por que prever na admissão.
2. Os dados: SIVEP-Gripe e o funil 4,67 mi → 3,88 mi.
3. Desenho temporal: figura dos seis blocos e por que a pandemia não entra no treino.
4. Variáveis e o cuidado com vazamento (saturação fora do principal).
5. Achado de dados: os três sintomas de 2019 e a decisão tomada.
6. Modelos e por que o vencedor (boosting × logística).
7. Calibração e limiar: o que é "30% de risco" e por que 80% de sensibilidade.
8. Teste A (resultado principal) com IC.
9. Teste B e 2020–2022: robustez a outro período.
10. O que pesa no risco: bruto × ajustado.
11. Não supervisionado: representação antiga × nova e o que diferencia os grupos.
12. Equidade regional, limitações e conclusão.

#### Perguntas difíceis (Pessoa B redige em 31/10; Pessoa C revisa as técnicas)
Por que não treinar com 2020–2022? Como garantem que não há vazamento? Por que PR-AUC e não acurácia? O que muda com a calibração? Por que esse corte? Por que a geografia não é variável? Os clusters servem para quê? O modelo serve para uso clínico?

#### Ensaio (02/11)
Cronometrado, com as três pessoas.

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

## #136 · Não supervisionado com one-hot dos quatro estados e normalização: nova representação e nova rodada de agrupamento

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M3
- data ideal: 27/10
- responsável: Pessoa C (executa na Fase E) · Pessoa B (interpreta ao voltar)
- pessoas: C, B
- fonte: Orientação de 24/10 (cobrança de one-hot); base de conhecimento v9 §6.3 e §8; B_06 de 24/10
- depende de: #131
- tags: Não supervisionado, Features, Código, Metodologia
- pilar: Valor científico-acadêmico + Performance
- carga: 6
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

A representação usada no clustering misturou "em branco" com "não" e deu peso desigual às variáveis. Os professores cobraram testes com one-hot. Sem refazer, a parte de Não Supervisionado fica vulnerável na banca.

### ③ O que fazer

> [!decisão] Replanejamento de 26/10: exploração antes da validação
> A troca para a coorte definitiva é uma base "nova": antes de ajustar e validar modelos, todas as análises que podem mudar decisões (variáveis, representação, limiar, calibração, leitura por região) rodam na **Fase E (26 a 28/10)**, sobre o `train_ref` e o `val_tune`. Os achados são discutidos no **ponto de decisão do #140 (28/10 à noite)**. Só então começam o ajuste fino (29/10) e a validação. Depois do teste, as mesmas análises são apenas repetidas para o relatório, sem decidir nada.

**Dono:** Pessoa C (execução) · Pessoa B (interpretação, 31/10) · **Prazo:** 27/10 (segunda) · **Esforço estimado:** C ≈ 6 h · B ≈ 1 h · **Revisão:** Pessoa B · **Começa quando:** #131 (amostra da coorte definitiva)

> [!atenção] Mudança de dono
> Para rodar **antes** do ajuste fino, a execução passa para a Pessoa C (a Pessoa B está fora até 30/10). A Pessoa B revisa a função, interpreta os grupos e escreve a seção do relatório ao voltar.

#### Passo a passo
1. **Função no `src`:** em `src/features/normalization.py` (hoje vazio), crie `construir_preprocessador_clustering(numericas, categoricas, pesar_por_variavel=True, saida="esparsa")` que devolve um `ColumnTransformer`:
   - numéricas (`idade_anos`, `dias_sintomas_ate_internacao`): mediana para faltantes e `StandardScaler`;
   - categóricas e clínicas (sexo, raça, zona, gestante, puerpério, os 11 sintomas, as 12 comorbidades): o mesmo normalizador de ausentes do pipeline supervisionado (vazio → `AUSENTE`; reaproveite o de `src/models/pipeline.py`), depois `OneHotEncoder(handle_unknown="ignore", dtype=np.float32)`;
   - peso: multiplicar o bloco one-hot de cada variável por `1/√k` (k = número de categorias);
   - **sem** `SimpleImputer(strategy="most_frequent")` e **sem** `add_indicator`.
2. **Testes** em `tests/test_features.py` com 8 linhas inventadas: número de colunas = soma das categorias; vazio vira a coluna `_AUSENTE`; nenhum vazio vira "não"; pesos aplicados.
3. **Amostra:** 80 mil fichas do `train_ref`, estratificadas por ano × desfecho, semente 42; ler só as colunas necessárias. O desfecho não entra no agrupamento.
4. **Redução:** `TruncatedSVD` (esparso) ou PCA (denso; 80 mil cabem) até ~90% da variância. Registrar dimensão, tempo e memória.
5. **Agrupamento:** `MiniBatchKMeans` k = 2 a 8; HCA (Ward) k = 2 a 4 numa subamostra de 10 a 20 mil. Para cada solução: silhueta, Calinski-Harabasz, Davies-Bouldin e ARI entre 5 sementes.
6. **Comparação com a representação antiga:** rodar também a representação do B_06 (binárias com imputação pela moda) na **mesma** amostra e calcular o ARI entre as duas soluções. Isso dá a tabela "antiga × nova" na mesma base.
7. **Só adultos:** repetir 4 e 5 com 18 anos ou mais.
8. **Saídas:** `outputs/tables/ns_onehot_metricas.csv` e `outputs/tables/ns_onehot_rotulos.parquet` (`id_registro` + rótulos de cada solução escolhida). Não salvar matrizes. `del` + `gc.collect()`.
9. Passar os rótulos para a Pessoa A rodar o perfil estatístico (#137, uso 2) em 28/10 e comentar no #140 o resumo (três linhas).

#### Como escolher k
Silhueta e Calinski-Harabasz (maior), Davies-Bouldin (menor), ARI entre sementes perto de 1, nenhum grupo abaixo de 5%. Escrever o motivo.

#### Pronto quando
Função testada no `src`, os dois arquivos de saída e o comentário no #140.

#### Pessoa B (31/10)
Revisar a função, ler o perfil estatístico (#137), escrever a seção "Não supervisionado: representação antiga × nova" do relatório e o slide correspondente.

## #137 · Perfil estatístico dos grupos: qui-quadrado e ANOVA (e óbito × cura só no treino)

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M3
- data ideal: 28/10
- responsável: Pessoa A (dona; revisão cruzada sem edição concorrente)
- pessoas: A
- fonte: Orientação de 24/10 (recomendação de ANOVA e qui-quadrado); base de conhecimento v9 §8.3
- depende de: #131
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

> [!decisão] Replanejamento de 26/10: exploração antes da validação
> A troca para a coorte definitiva é uma base "nova": antes de ajustar e validar modelos, todas as análises que podem mudar decisões (variáveis, representação, limiar, calibração, leitura por região) rodam na **Fase E (26 a 28/10)**, sobre o `train_ref` e o `val_tune`. Os achados são discutidos no **ponto de decisão do #140 (28/10 à noite)**. Só então começam o ajuste fino (29/10) e a validação. Depois do teste, as mesmas análises são apenas repetidas para o relatório, sem decidir nada.

**Dono:** Pessoa A · **Prazo:** função e uso 1 em 27/10; uso 2 em 28/10 · **Esforço estimado:** ≈ 4 h · **Revisão:** Pessoa C (função) · Pessoa B (leitura, 31/10)

#### Passo a passo
1. Crie `src/evaluation/cluster_profile.py` com `perfil_estatistico(df, coluna_grupo, numericas, categoricas, min_esperado=5) -> pd.DataFrame`. Uma linha por variável: `variavel`, `tipo`, `teste`, `estatistica`, `p`, `p_ajustado` (Benjamini-Hochberg), `efeito` (V de Cramér ou eta²), `leitura` (pequeno, médio, grande), resumo por grupo (proporções para qualitativas; média e mediana para numéricas) e `observacao`.
2. Use `scipy.stats.chi2_contingency` (sobre `pd.crosstab`), `scipy.stats.f_oneway` e `scipy.stats.kruskal`. V de Cramér = √(χ² ÷ (n × (min(linhas, colunas) − 1))). eta² = soma de quadrados entre grupos ÷ soma total.
3. Categorias com esperado menor que 5: juntar em "outras" ou sinalizar em `observacao`. Vazio é categoria própria (`AUSENTE`), nunca descartado.
4. Testes em `tests/test_cluster_profile.py`: variável independente do grupo → V ≈ 0; variável igual ao grupo → V ≈ 1; numérica com médias muito diferentes → eta² alto.
5. **Uso 1 (27/10): óbito × cura no `train_ref`** (fecha o #51). Salve `outputs/final/perfil_desfecho_train_ref.csv`. Comente no #140 as cinco variáveis com maior efeito e qualquer resultado estranho (efeito enorme numa variável sem sentido clínico pode ser erro de dado).
6. **Uso 2 (28/10): clusters** com os rótulos do #136 (antiga e nova representação). Salve `outputs/final/perfil_clusters_*.csv` e comente no #140.
7. Ordene cada tabela pelo efeito e escreva três frases por uso.

#### Pronto quando
Função testada no `src` e os CSVs dos dois usos gerados, com os comentários no #140.

## #112 · Atualizar a revisão bibliográfica com busca científica dirigida

- prioridade: P2
- situação: aberta
- estratégia: desenvolver
- marco: M6
- data ideal: 31/10
- responsável: Pessoa B (busca e matriz) · conferência de citações: Pessoa A
- pessoas: B
- fonte: orientação de 17/10
- depende de: —
- tags: Documentação, Literatura
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 4
- novo: sim
- professores: não

### ① Para entender

> [!decisão] Sem dependência de ferramenta específica
> O resultado esperado é uma revisão curta e verificável; MCP e Consensus são meios opcionais. A busca precisa sustentar a transportabilidade entre períodos, a calibração, o uso de SIVEP-Gripe e a heterogeneidade regional.

O professor indicou ferramentas e um artigo. Boa parte do valor acadêmico vem de situar o trabalho na literatura de predição de óbito por SRAG/COVID com SIVEP-Gripe.

### ② Problema

O título do artigo indicado não ficou na transcrição.

### ③ O que fazer

**Dono:** Pessoa B (busca e matriz, durante a viagem) · Pessoa A (confere as citações) · **Prazo:** 31/10 · **Esforço estimado:** B ≈ 3 h · A ≈ 30 min

1. 8 a 12 referências verificáveis, em quatro temas: (a) predição de óbito por SRAG/COVID-19 com SIVEP-Gripe; (b) TRIPOD/TRIPOD+AI (como relatar modelos preditivos); (c) calibração e avaliação de modelos clínicos; (d) validação temporal e mudança de distribuição (drift).
2. Matriz em CSV: referência, população, período, modelo, métrica, tipo de validação, limitação, onde usar no texto.
3. Cada citação com DOI ou link conferido à mão.
4. Rascunho do parágrafo de lacuna da Introdução.

**Pronto quando:** matriz e parágrafo existirem.

## #96 · Atualizar os guias e a base de conhecimento do agente

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 03/11
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

## #130 · Regerar a referência do projeto ao fim de cada marco

- prioridade: P3
- situação: aberta
- estratégia: desenvolver
- marco: Contínuo
- data ideal: 02/11
- responsável: Pessoa A (dona; revisão cruzada sem edição concorrente)
- pessoas: A
- fonte: tools/update_project_reference.py (v6)
- depende de: —
- tags: Documentação, Ambiente
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 2
- novo: sim
- professores: não

### ① Para entender

> [!atenção] Inclui checkpoint Git
> Antes de cada marco: `git status`, commit do estado verde e geração da referência v6. Isso impede que outra IA leia alterações locais sem saber o que foi testado.

A referência é o "manual vivo" que impede outra IA (ou outro integrante) de criar funções repetidas. Ela só vale até o momento em que foi gerada.

### ② Problema

Alterações feitas depois da geração não aparecem; buffers não salvos nunca aparecem.

### ③ O que fazer

**Dono:** Pessoa A · **Prazo:** nos marcos: 25/10, 27/10, 29/10 e 02/11 · **Esforço estimado:** ≈ 30 min por vez

1. `git pull`; salvar tudo.
2. `.\.venv\Scripts\python.exe tools/update_project_reference.py --run-tests --pytest-args="-m 'not slow'"`.
3. Conferir: nenhum erro de leitura, testes passando, nenhum código ignorado pelo Git.
4. Avisar no card com a data e o commit; as IAs de todos passam a usar a nova referência.

## #53 · Exploração opcional: validar o modelo congelado em 2026

- prioridade: P4
- situação: parcial
- estratégia: explorar
- marco: Plano B
- data ideal: 02/11
- responsável: Pessoa B (dona; revisão cruzada sem edição concorrente)
- pessoas: B
- fonte: src/evaluation/temporal.py; Projeto
- depende de: #1, #2, #89, #119
- tags: Metodologia, Partição
- pilar: Eficiência + Performance + Valor científico-acadêmico
- carga: 1
- novo: não
- professores: não

### ① Para entender

> [!atenção] Só depois de todo o projeto concluído
> 2026 não entra em treino, validações, Teste A ou Teste B. Se tudo estiver fechado e revisado, o modelo congelado pode ser aplicado a 2026 como exploração de transportabilidade para um período parcial.

O resultado deve ser apresentado separadamente, com alerta de maturidade do desfecho e cobertura incompleta.

### ② Problema

2026 é parcial e tem desfechos ainda pendentes. Misturá-lo aos testes principais criaria uma comparação injusta e potencialmente enviesada.

### ③ O que fazer

Só depois de 01/11 e se o relatório estiver completo. É o **primeiro** item a ser cortado. Carregar `exploracao` com `exploracao_2026.ativa: true`, sem recalibrar nem mudar o corte, e reportar métricas com o rótulo "exploratório, ano parcial".

## #11 · A sensibilidade de indicadores de ausência não existe no código

- prioridade: P4
- situação: aberta
- estratégia: documentar
- marco: M1
- data ideal: 25/10
- responsável: Pessoa A (dona; revisão cruzada sem edição concorrente)
- pessoas: A
- fonte: configs/supervised.yaml (features.sensibilidade_indicadores_ausencia, missingness.indicadores_ausencia, sensibilidades.com_sem_indicadores_ausencia); src/models/pipeline.py
- depende de: #83
- tags: Diverge do decidido, Código, Metodologia, Features
- pilar: —
- carga: 1
- novo: não
- professores: não

### ① Para entender

> [!decisão] Decisão de 18/10
> Prioridade anterior: P2. Rebaixada para P4 em 18/10.

O YAML liga uma análise "com e sem indicadores de ausência", mas nenhum código cria essas colunas. E, como o branco já vira `AUSENTE`, o modelo principal já recebe essa informação. Depende do item 83 dizer o que comparar.

### ② Problema

O YAML ativa uma sensibilidade com indicadores de ausência (prefixo `missingindicator_`), mas nenhum código cria essas colunas. Além disso, o pré-processador já imputa as categóricas vazias como a categoria `AUSENTE`, o que dá ao modelo principal a mesma informação. Na prática, a comparação "com e sem indicadores" não existe.

### ③ O que fazer

Fecha junto com o #83: quando as duas chaves estiverem `false` no YAML, marque este item como concluído. Nenhum código novo.

## #24 · Curvas de calibração calculadas de dois jeitos

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 03/11
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

A curva de confiabilidade de `src/evaluation` usa faixas de largura igual. O B_07 usou faixas por quantis. Com probabilidades concentradas em poucos valores, as duas estratégias dão curvas visivelmente diferentes.

### ③ O que fazer

**Pós-entrega para a função**, mas com um cuidado já na avaliação final: no C_16 (#119), gerar as curvas de calibração com `sklearn.calibration.calibration_curve(..., strategy="quantile", n_bins=10)` diretamente, para que as figuras do relatório sejam coerentes com o ECE por quantis do #79. Depois da entrega, acrescentar o parâmetro `strategy` à função de `src/evaluation`.

**Como fazer, quando for a hora (instruções anteriores mantidas):**

Acrescentar o parâmetro `strategy` (`"uniform"` ou `"quantile"`), repassado a `calibration_curve`, e padronizar `"quantile"` no projeto, como no B_07.

## #25 · A checagem de vazamento só olha o nome das colunas

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 03/11
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

## #31 · configs/paths.local.json aponta para uma pasta que ninguém usa

- prioridade: P3
- situação: aberta
- estratégia: desenvolver
- marco: M6
- data ideal: 31/10
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

## #32 · Textos antigos no código (dt_notific, nomes de gates)

- prioridade: P4
- situação: parcial
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 03/11
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

Há textos desatualizados: o `config.py` cita `C.exigir_gate("G7_limiar")` e "holdout antes de G7" (os gates atuais são G8_limiar e G9_holdout); o `reproducibility.py` dá como exemplo "split temporal por dt_notific"; o `temporal.py` usa `dt_notific` como coluna de tempo; a docstring de `holdout_partition` cita `TemporalSplit`.

### ③ O que fazer

Pós-entrega. Não afeta resultados. Se alguém tocar nesses arquivos por outro motivo, corrige junto.

**Como fazer, quando for a hora (instruções anteriores mantidas):**

Atualizar os exemplos e docstrings para `G8_limiar`, `G9_holdout`, `dt_interna` e divisão aleatória estratificada. Indicar no topo do `temporal.py` que ele serve apenas à sensibilidade temporal.

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

## #35 · Notebooks B recalculam com código próprio o que já existe em src/

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 03/11
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

Os B_06 e B_07 calculam idade, sexo, pipelines e métricas com código próprio, duplicando o que existe em `src/` (`montar_features`, `build_*`, `src/evaluation`). Quando o código central mudar, os notebooks vão produzir números diferentes sem aviso.

### ③ O que fazer

Pós-entrega. Com o B_07 histórico e o B_06 usando o artefato v3 para faixa e sexo (#36), o risco de números divergentes na entrega fica controlado.

**Como fazer, quando for a hora (instruções anteriores mantidas):**

No B_06, trocar as derivações próprias por `montar_features`. No B_07, trocar os pipelines escritos à mão por `build_baseline_pipeline` e `build_logistic_pipeline`, e as métricas por `metricas_completas`. Remover as funções duplicadas e conferir que os números batem com os anteriores (ou explicar a diferença).

## #39 · Matriz de transição do B_10 com status escritos à mão

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 03/11
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

Na matriz de transição do B_10, o status "pronto para seguir" está escrito à mão em 4 dos 6 itens, em vez de vir de verificações. O texto de abertura cita `cohort_source`, mas o código usa `load_supervised_artifact`.

### ③ O que fazer

Pós-entrega. O B_10 é histórico (#37).

**Como fazer, quando for a hora (instruções anteriores mantidas):**

Calcular cada status a partir de uma verificação real (por exemplo, existência do artefato, gate aprovado, lista preenchida). Corrigir o texto de abertura.

## #41 · "provisoria", "provisorio" e "provisional" misturados

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 03/11
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

## #42 · Cada notebook encontra a pasta do projeto de um jeito

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 03/11
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

Cada notebook encontra a raiz do projeto de um jeito: procurando `src` e `configs`, `src` e `pyproject`, ou pelo nome da pasta atual.

### ③ O que fazer

Pós-entrega.

**Como fazer, quando for a hora (instruções anteriores mantidas):**

Criar `src/utils/paths.py` com uma função `encontrar_raiz()` e usá-la em todos os notebooks. Como a função precisa existir antes do import, manter no notebook apenas um bloco mínimo que adicione a raiz ao `sys.path`.

## #43 · Arquivos e listas que ninguém usa (preprocessor.joblib, lista de coortes no B_06)

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 03/11
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

O C_11 salva `preprocessor.joblib`, que nenhum passo seguinte usa. O B_06 tem uma lista própria de coortes candidatas, que conflita com `cohort_source`.

### ③ O que fazer

Pós-entrega. O C_11 do #132 pode simplesmente não salvar o `preprocessor.joblib`, se for mais simples do que manter.

**Como fazer, quando for a hora (instruções anteriores mantidas):**

Remover o salvamento do `preprocessor.joblib` (ou passar a usá-lo). No B_06, trocar a lista própria por `load_cohort`.

## #48 · 41 fichas com povo tradicional preenchido sem a pessoa ser de povo tradicional

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 03/11
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

## #49 · Códigos a confirmar no dicionário

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 03/11
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

Faltam confirmar códigos: `ave_suino` = 3 (outro animal), `cs_raca` = 5 (indígena) e o código do Brasil em `co_pais`.

### ③ O que fazer

Pós-entrega. `ave_suino`, `cs_raca` e `co_pais`: só `ave_suino` e `cs_raca` estão no modelo principal; seus códigos já seguem o dicionário da ficha, e a confirmação formal entra no apêndice se houver tempo.

**Como fazer, quando for a hora (instruções anteriores mantidas):**

Conferir no dicionário oficial do SIVEP-Gripe e registrar a confirmação no dicionário de variáveis.

## #50 · Três sintomas vazios em 2019: estudar o "marcador de ano" e decidir se ficam no modelo

- prioridade: P1
- situação: aberta
- estratégia: desenvolver
- marco: M3
- data ideal: 27/10
- responsável: Pessoa A (tabela e verificação) + Pessoa C (linha na ablação)
- pessoas: A, C
- fonte: configs/dicionario_variaveis_v1.csv
- depende de: #131, #135
- tags: Features, Vazamento, Metodologia, Dados/Coorte
- pilar: —
- carga: 4
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

Falta confirmar em que ano campos como perda de olfato, perda de paladar, fadiga e `vacina_cov` entraram na ficha. Antes disso, o vazio significa "campo inexistente", não "não informado".

### ③ O que fazer

**Dono:** Pessoa A (dados e verificação) + Pessoa C (linhas na ablação) · **Prazo:** 27/10 (Fase E), decisão no #140 · **Esforço estimado:** A ≈ 3 h · C ≈ 1 h (dentro do #54) · **Começa quando:** #131 e #135

#### Objetivo
Decidir, com um critério combinado antes de olhar os números, se os três sintomas ficam ou saem do modelo principal.

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

## #68 · Texto com codificação corrompida

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 03/11
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

## #74 · Faltam os números do clustering sem saturação e desconforto

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 03/11
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

Faltam os números da sensibilidade do clustering sem saturação e sem desconforto respiratório.

### ③ O que fazer

Pós-entrega. O relatório usa o clustering principal; a sensibilidade sem saturação e desconforto vira uma frase em Trabalhos futuros, se for citada.

**Como fazer, quando for a hora (instruções anteriores mantidas):**

Recuperar os resultados da execução do B_06 (ou rodar de novo a célula) e exportá-los numa tabela para o relatório.

## #88 · A exportação da Pessoa A não tem duas variáveis que o modelo exige

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 03/11
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

No A_03 e no A_04, a verificação "C2 exige todas as features" retorna FALHA: "faltam no dataset (o C não vai rodar): \['dias_sintomas_ate_internacao', 'sexo_categoria']". As demais verificações (coluna de tempo, alvo, `check_leakage`, tamanho) estão OK. `a1_export_dataset` cria só as derivadas listadas em `_DERIVADAS_CANON`.

### ③ O que fazer

Pós-entrega. A exportação da Pessoa A não alimenta mais a cadeia oficial (#87). Basta a nota de “histórico” no topo do A_03 e do A_04.

**Como fazer, quando for a hora (instruções anteriores mantidas):**

1. Em `a1_export_dataset`, aplicar `montar_features` do `src/features` antes de selecionar as colunas, em vez de derivar à parte.
2. Ou, se a exportação da Pessoa A não for mais usada pelo pipeline, documentar que ela é só para auditoria e remover a verificação "C2 exige".
3. Rodar A_03 e A_04 e conferir que a verificação passa.

## #90 · O A_09 sorteia linhas, e não grupos: a mesma ficha cai em duas partições

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 03/11
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

`split_aleatorio` (usado por `a1_export_dataset(split=...)`) estratifica pelo alvo, mas sorteia índices de linha. O A_09 reportou "10 NU_NOTIFIC em mais de uma partição (todos_2019_2025)" e 9 em "sem_2020_2021". O efeito numérico é desprezível, mas o método diverge do oficial.

### ③ O que fazer

Pós-entrega. Superado pela partição-mestre por grupo (#131). O A_09 é histórico (#89).

**Como fazer, quando for a hora (instruções anteriores mantidas):**

1. Usar a função oficial de partição por hash (item 86) também nos cenários do A_09.
2. Se mantiver a função própria, sortear por grupo (`nu_notific`) e não por linha.
3. Rodar o A_09 de novo e confirmar 0 identificadores em mais de uma partição.

## #93 · O A_14 não tem a tabela de candidatos para comparar

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 03/11
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

Saída do A_14: "outputs/tables/resultados_cv.csv não encontrado — preencha RESULTS". Os resultados existem em outros arquivos: comparação das cinco famílias do B_07, comparação do C_13 e tabelas do C_15. Nenhum deles tem o formato esperado (`modelo, fold, pr_auc, roc_auc, brier`).

### ③ O que fazer

Pós-entrega. O A_14 é histórico; a tabela de candidatos oficial é a do tuning (#1) e das ablações (#54).

**Como fazer, quando for a hora (instruções anteriores mantidas):**

1. Combinar o formato: uma linha por modelo e partição de avaliação, com PR-AUC, ROC-AUC, Brier bruto e calibrado, ECE.
2. Gerar o CSV no fim do C_15 (após o ajuste fino), juntando C_13 e C_15.
3. Apontar `RESULTS` do A_14 para esse arquivo e rodar.

## #94 · Alertas falsos no relatório automático do projeto

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 03/11
- responsável: C
- pessoas: C
- fonte: tools/update_project_reference.py (relatório estático)
- depende de: —
- tags: Código, Documentação
- pilar: —
- carga: —
- novo: não
- professores: não

### ① Para entender

O relatório de atenção marca 7 alertas "altos", mas 4 deles são engano da ferramenta: ela confunde `subprocess.run` com a função `verificacoes.run` da Pessoa A (A2 a A5). Os alertas A12 a A16 tratam nomes de variáveis como `G6_STATUS` como se fossem gates. O A17 aponta erro de sintaxe no B_07 que não se confirma.

> [!exemplo] Exemplo
> Um alarme de incêndio que dispara com vapor do chuveiro: as pessoas param de prestar atenção nos alarmes de verdade.

### ② Problema

Falsos positivos identificados: A2–A5 (call-signature-mismatch por homonímia com `subprocess.run`), A12–A16 (gate-name-not-in-yaml para variáveis `G6_STATUS`, `G6_APROVADO`, `G7_STATUS`, `G8_STATUS` e o fragmento `G6_fi`), A17 (todas as células de código do B_07 passam em `ast.parse`). O alerta A1 (`criar_alvo_binario`) é verdadeiro (item 6).

### ③ O que fazer

Pós-entrega. Os alertas de gates (A59–A64 na referência de 24/10) continuam falsos positivos.

**Como fazer, quando for a hora (instruções anteriores mantidas):**

1. Na checagem de assinatura, resolver o import real (`import subprocess` × `from src.protocolo...`) antes de comparar.
2. Na checagem de gates, aceitar só nomes completos que casem com `G\d+_[a-z_]+` e ignorar sufixos `_STATUS`/`_APROVADO`.
3. Rever o parser de células (provavelmente quebra com crases dentro de strings).

## #128 · 29 avisos de depreciação de timedelta sem unidade no NumPy

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 03/11
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

## #129 · Refatoração completa de performance de B_05, construtor e notebooks A

- prioridade: P4
- situação: aberta
- estratégia: despriorizar
- marco: Pós-entrega
- data ideal: Após 03/11
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

Custo alto, risco de mudar resultados já validados e nenhum impacto direto na entrega.

### ③ O que fazer

Pós-entrega. O construtor definitivo já roda com leitura projetada; não há exceção a acionar.

**Como fazer, quando for a hora (instruções anteriores mantidas):**

Despriorizado. Exceção: se o construtor da coorte não couber na memória (item 98), aplicar só a leitura em duas passadas.

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
