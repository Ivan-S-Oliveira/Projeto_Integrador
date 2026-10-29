# Painel de Pendências SRAG — v6.2

## Instalação (uma única vez, por quem publica a atualização)

1. Feche o painel (⏻ Encerrar ou `ENCERRAR_PAINEL.cmd`).
2. Copie os arquivos desta versão para `.srag-status-local\`, substituindo os antigos (inclusive o `.gitignore` desta pasta).
3. Apague a cópia antiga `tools\deep_git_project_audit.py`: o verificador agora existe só em `.srag-status-local\`.
4. No `.gitignore` da **raiz** do repositório, apague a linha `/.srag-status-local/`.
5. Commit e push pelo VS Code. As outras pessoas recebem tudo no próximo *pull* e só precisam reabrir o painel.

O `.gitignore` desta pasta versiona apenas o código (`server.py`, `project_status_text.py`, `deep_git_project_audit.py`,
`painel.html`, os `.cmd` e este arquivo). Tudo o que é de cada máquina continua fora do Git: fila, caches, relatórios,
backups, logs, `config.json` e o `painel_gerado.html`. Por isso **não é preciso voltar a linha no `.gitignore` da raiz**:
nenhum arquivo desta pasta vai aparecer como modificado no VS Code.

| Arquivo | Conteúdo | Quem edita |
|---|---|---|
| `PROJECT_STATUS_TEXT.md` (raiz) | Todo o texto: itens, seções, “④ Pronto quando”, cronograma, ajuda | Pessoas (VS Code ou editor do painel) e o painel |
| `PROJECT_STATUS.md` (raiz) | Situação compartilhada, comentários, histórico, resultado da última verificação | Só o painel |

## Uso diário

| Ação | Como |
|---|---|
| Abrir | `ABRIR_PAINEL.cmd`. A janela do terminal fica aberta enquanto você usa. O painel só abre a partir da pasta `.srag-status-local` do repositório |
| Conferir uma pendência | Botão **🔎 Conferir esta pendência**, na seção ④ do card. Confere só aquela pendência no que está salvo na sua pasta (antes ou depois do commit), roda só os testes dela (os do “④ Pronto quando” e todo teste que importa arquivos dela) e lista os arquivos que ainda precisam de commit. Não gera commit e não muda a situação |
| Concluir | Caixa “Marcar como feito” ou “✓ Confirmar conclusão”. O painel confere o “④ Pronto quando”; se o verificador não confirmar, pede um comentário de pelo menos 15 caracteres |
| Editar texto | ✎ no card, ➕ Nova pendência, ✎ Textos do painel, ou direto no `PROJECT_STATUS_TEXT.md` |
| Buscar | ⟳ Buscar atualizações. Nunca gera commit sozinho; depois da busca, uma verificação rápida (sem testes) atualiza os ✓/✗ dos cards |
| Verificar | 🔄 Atualizar, auditar e validar: confere todos os critérios e roda o pytest rápido numa cópia limpa do commit publicado. Só gera commit se alguma pendência mudar |
| Revisar | Seção **REVISÕES** (sempre aberta até você recolher): detectadas como concluídas, concluídas que o verificador ainda vê como pendentes, revisões, testes falhando, configuração crítica alterada, critérios inválidos e referência para IAs desatualizada |
| Meu dia | Escolha a pessoa: atrasadas, prontas para começar, revisões e o que destravou desde a última visita |
| Encerrar | ⏻ Encerrar no painel ou `ENCERRAR_PAINEL.cmd` |

Commits saem ~12 s depois do último clique, agrupados por tipo e com cada pendência citada uma vez:
`(#status) concluída: #10; conteúdo: #1, #31, #46 +12 · Mateus`.

## Rotina de uma pendência

1. Faça as alterações e salve.
2. No card, clique em **🔎 Conferir esta pendência**. Corrija o que der ✗ e confira de novo.
3. Com “✓ Pronta para commit”, faça commit e push pelo VS Code dos arquivos listados (cite `tarefa N` na mensagem;
   evite `[done:#N]`, que conclui sem passar pelo verificador).
4. Marque como feita. O painel confere de novo, agora no commit publicado; se tudo estiver no Git, conclui sem pedir comentário.

## Configuração crítica mudou

Na seção REVISÕES, cada mudança em chave crítica das configurações (anos dos blocos, features, alvo, gates,
calibração, limiar…) aparece com quem mudou, o que entrou e saiu e as **pendências abertas mais afetadas**:
alta (um critério do ④ confere essa chave), média (a pendência cita a chave, ex.: `train_ref`, `G6`) e baixa
(a pendência usa o arquivo). Mudanças só de formatação (quebra de linha, espaços) não aparecem.

Clique em **✓ Estou ciente** (ou **Ciente de todas**). A ciência fica só no navegador desta máquina e **não gera
commit**: cada pessoa precisa confirmar no próprio painel para o aviso sair. “Ver já confirmadas” mostra o histórico
e permite desfazer.

## Sem conexão e conflitos

Cada clique vira uma alteração pequena (item + campo) guardada na fila local. Sem conexão, a fila fica guardada
(o painel mostra desde quando e a causa provável: credencial, rede/VPN ou endereço do repositório) e sai sozinha
quando a conexão voltar. Na publicação, cada alteração é reaplicada sobre a versão **mais nova** do GitHub:

- campos diferentes do mesmo card somam (ex.: uma pessoa muda o título, outra o responsável, outra comenta);
- comentários sempre somam;
- só o **mesmo campo** mudado por outra pessoa vira conflito. Esse campo fica de fora do seu commit (o resto sai
  normalmente) e abre um popup com a sua versão, a publicada e a original: “Manter a minha”, “Manter a publicada”
  ou “Editar e juntar”. Não precisa de `git pull` nem de mexer em arquivo.

**Proteção contra regressão:** o painel se recusa a publicar um estado que perca itens, comentários, sugestões
rejeitadas ou histórico, ou que mude a situação de uma pendência sem nenhuma alteração que explique. Se o
`PROJECT_STATUS.md` do GitHub estiver ilegível, nada é publicado (a fila fica guardada) até ele ser restaurado.

## “④ Pronto quando”

Cada pendência tem critérios conferidos pelo verificador, um por linha: `- verbo: argumentos | descrição detalhada`.
Verbos: `existe`, `nao-existe`, `nao-vazio`, `define`, `nao-define`, `contem`, `nao-contem`, `yaml`, `json`, `teste`,
`notebook-executado`, `notebook-saida`, `manual`. A gramática completa está no topo do `deep_git_project_audit.py`.

- Arquivos versionados são lidos do commit publicado (igual para todos). Arquivos de pastas ignoradas pelo Git
  (`outputs/`, `data/`) só existem em cada máquina: se faltarem, o critério fica “indisponível nesta máquina”.
- Commit que só mexe nos arquivos de uma pendência **nunca** muda a situação: aparece como informação no card.
  Só a menção explícita muda (`[done:#30]`, `tarefa 30`, `#30`), e só se o commit for mais novo que a última
  decisão humana sobre a pendência.
- Teste que falha e importa arquivos de uma pendência já iniciada a coloca em “precisa revisão” e entra no
  “④ Pronto quando” dela. Quem concluir assim mesmo registra o motivo, e a mesma falha não reabre a pendência.
- Uma pendência que parece concluída mas aguarda revisão não trava quem depende dela; esses cards mostram um
  aviso rosa “⚠ #N aguardando revisão”.

## Arquivos desta pasta

| Arquivo | Versionado | Função |
|---|---|---|
| `ABRIR_PAINEL.cmd`, `ENCERRAR_PAINEL.cmd`, `DIAGNOSTICO.cmd` | sim | Abrir, encerrar, diagnosticar |
| `server.py` | sim | Serviço local (127.0.0.1): fila, reconciliação, publicação, verificação, geração do painel |
| `project_status_text.py` | sim | Formato do `PROJECT_STATUS_TEXT.md` e conversão para HTML |
| `deep_git_project_audit.py` | sim | Verificador do “④ Pronto quando” (também roda sozinho no terminal) |
| `painel.html` | sim | Modelo da interface. Nunca é regravado |
| `painel_gerado.html` | não | Interface com o conteúdo embutido, gerada a cada mudança |
| `outbox.json`, `estado_remoto.json`, `conflitos.json`, `conteudo_remoto.md`, `deep_git_audit_report.json`, `verificacao_rapida.json`, `config.json`, `backups/`, `logs/` | não | Locais de cada máquina |

## Se algo der errado

1. ⟳ Buscar atualizações. Nada se perde: há fila local, backups e histórico do Git.
2. “Sem conexão”: passe o mouse no selo vermelho para ver a causa provável e o erro do Git. Credencial: faça um
   *pull* pelo VS Code (ele pede o login) e busque de novo. Rede: troque de rede ou ligue/desligue a VPN.
3. O painel não abre: `DIAGNOSTICO.cmd` (mostra a pasta, o remoto, o erro de busca e valida o `PROJECT_STATUS_TEXT.md`).
4. Verificador no terminal: `.\.venv\Scripts\python.exe .srag-status-local\deep_git_project_audit.py` (`--item 142` para uma pendência, `--self-test` para testar a instalação).
