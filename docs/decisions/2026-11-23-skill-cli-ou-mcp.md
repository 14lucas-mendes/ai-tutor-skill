# AI Tutor — quando evoluir a skill para CLI ou MCP

- **Data:** 23/11/2026
- **Status:** decidido — manter o AI Tutor como skill
- **Revisão:** em 4 a 6 semanas (entre 21/12/2026 e 04/01/2027)

## Resumo

Decisão atual: manter o AI Tutor como skill e seguir atualizando o repositório `14lucas-mendes/ai-tutor-skill`. A skill já é uma ferramenta: cerca de 3.100 linhas de Python com estado em JSON, validação, migração, repetição espaçada, testes e CI. O `SKILL.md` é só a camada de instruções.

Mudar de formato só se justifica quando uma das duas dores abaixo pesar. Cada dor aponta para uma saída diferente: CLI ou MCP.

## Dor 1 — o estado depende do modelo seguir os contratos

**Status em 23/11/2026:** ainda não aconteceu. Nenhum caso de estado corrompido até agora.

O protocolo de gravação segura (validar, preparar a revisão, gravar de forma atômica, rodar `validate_study`) só roda se o agente lembrar de executá-lo. Hoje quem garante a consistência é o modelo, não o código.

Sinais de que essa dor ficou real:

- `validate_study` aponta erro depois de uma sessão;
- progresso, cartões ou lições ficam fora de sincronia entre o JSON e o Markdown;
- o agente pula etapas do contrato ou grava direto no arquivo canônico.

**Saída indicada:** tirar a gravação do modelo e passar para comandos determinísticos (CLI e, depois, MCP).

## Dor 2 — usar fora do computador

**Status em 23/11/2026:** já acontece. A skill só roda onde há sistema de arquivos e Python (Codex, Claude Code, Cursor). No celular ou no chat do claude.ai não existe `study_root` persistente.

Contornos usados hoje:

- abrir um ambiente em nuvem do Claude para continuar a formação fora de casa;
- deixar o repositório no Google Drive para sincronizar as mudanças entre ambientes.

**Risco do segundo contorno:** o Drive sincroniza arquivo a arquivo e não entende Git. A pasta `.git` pode corromper, e edições em dois lugares viram cópias como `state (1).json` em vez de serem mescladas. O lock e o controle de revisão da skill só protegem dentro de uma mesma máquina.

**Ajuste imediato, sem ferramenta nova:** o estado versionado fica só no GitHub, com `git pull` no início da sessão e commit + push no fim. O Drive continua útil para material solto (PDFs, mídia, exports do NotebookLM).

## Opção CLI

A CLI é o primeiro passo se a Dor 1 aparecer, ou se você quiser revisar sem abrir um agente. É um `pyproject.toml` com entry points sobre os scripts que já existem, como `ai-tutor due`, `ai-tutor review`, `ai-tutor progress` e `ai-tutor record-evidence`.

- **O que resolve:** a gravação passa a ser um comando que valida e grava sozinho, e o agente só chama o comando. Também dá para revisar cartões e ver progresso sem gastar tokens.
- **O que não resolve:** o celular. A CLI continua precisando de terminal e Python.
- **Custo:** baixo, porque reaproveita `state_io.py`, `spaced_repetition.py`, `validate_study.py` e os testes. Também é um bom exercício de empacotamento em Python.
- **Faz sentido quando:** a Dor 1 aparecer pelo menos uma vez, ou quando você notar que abre o agente só para ver o que está vencido.

## Opção MCP

O MCP é o passo seguinte, e o único que resolve as duas dores juntas. Um servidor MCP expõe as operações do tutor como ferramentas (`cartoes_vencidos`, `registrar_evidencia`, `proxima_licao`, `progresso`) para qualquer cliente compatível, incluindo o Claude Desktop e o web.

- **O que resolve:** o estado é gravado por código (Dor 1). Com servidor remoto e armazenamento no GitHub ou no Drive, funciona fora do computador (Dor 2).
- **O que não resolve:** o ensino em si. Teoria, prática e escada de ajuda continuam nas instruções da skill.
- **Custo:** médio. Local é simples; remoto exige hospedagem, autenticação e acesso ao repositório ou ao Drive.
- **Faz sentido quando:** você quiser estudar 10 a 15 minutos pelo celular (revisar cartões, ver o que vence hoje) com frequência, e abrir um ambiente em nuvem só para isso virar atrito.
- **Escopo mínimo:** começar só com leitura de progresso e revisão de cartões. A criação de lições fica na skill.

**Caminho mais barato:** construir a CLI primeiro e fazer o MCP como uma camada fina sobre ela. Assim a lógica fica em um lugar só.

## Gatilhos de decisão

Revisar esta decisão depois de 4 a 6 semanas de uso na formação Python, anotando cada falha de estado e cada vez que quis estudar fora do computador.

| Sinal observado | Ação |
| --- | --- |
| Nenhuma falha e pouco uso fora de casa | Manter a skill; só aplicar o fluxo GitHub (pull no início, push no fim) |
| Estado inconsistente ou contrato pulado | Fazer a CLI |
| Abre o agente só para ver cartões vencidos | Fazer a CLI |
| Quer revisar pelo celular com frequência | Fazer o MCP mínimo, sobre a CLI |
| Outras pessoas vão usar (alunos do minicurso, equipes) | Reavaliar o MCP remoto e a instalação simplificada |

## O que não fazer agora

App web ou SaaS. Exigiria login, custo de API, cobrança e interface, sem usuários validados, e concorreria com os modos de estudo já embutidos no ChatGPT e no Claude.
