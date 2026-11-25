# 🎓 AI Tutor

Transforme seu agente de IA em um tutor que acompanha seus estudos ao longo do tempo.

O AI Tutor ajuda você a criar um plano de estudos, fazer lições, praticar, revisar o que esqueceu e acompanhar seu progresso.

Em vez de apenas explicar um assunto, ele tenta descobrir se você realmente consegue entender e aplicar o que aprendeu.

O AI Tutor segue o padrão de Agent Skills e pode ser usado em diferentes ambientes, incluindo:

- OpenAI Codex
- Claude Code
- Cursor
- OpenCode

> **Sobre a autoria:** o projeto foi concebido por mim (Lucas Mendes): os requisitos, as regras de aprendizagem e o funcionamento da skill são decisões minhas. A implementação (texto da skill, scripts e testes) foi gerada com ajuda de IA a partir dessas especificações, e eu conduzi e revisei o resultado. Sou iniciante em programação, então encare o código como um projeto educacional em evolução.

---

## 🚀 Comece aqui

Você não precisa entender como a skill funciona por dentro para começar.

O caminho é simples:

**1. Instale a skill → 2. Escolha o que quer aprender → 3. Comece a estudar**

---

## 1. O que você precisa

Antes de começar, tenha:

- um ambiente compatível: Codex, Claude Code, Cursor ou OpenCode;
- Python 3.11 ou superior;
- Git, caso queira instalar pelo terminal.

O Python é usado internamente pelo AI Tutor para salvar e validar seu progresso.

Você pode verificar sua versão executando:

```bash
python --version
```

ou:

```bash
python3 --version
```

---

## 2. Instale o AI Tutor

Escolha abaixo o ambiente que você utiliza.

### 🤖 Codex

**macOS ou Linux**

Abra o terminal e execute:

```bash
mkdir -p ~/.codex/skills

git clone https://github.com/14lucas-mendes/ai-tutor-skill \
  ~/.codex/skills/ai-tutor
```

Depois reinicie o Codex.

Para usar:

```text
$ai-tutor
```

Por exemplo:

```text
$ai-tutor

Quero aprender Python do zero.
```

**Windows PowerShell**

```powershell
New-Item -ItemType Directory -Force "$HOME\.codex\skills"

git clone https://github.com/14lucas-mendes/ai-tutor-skill `
  "$HOME\.codex\skills\ai-tutor"
```

Depois reinicie o Codex.

---

### 🟠 Claude Code

O Claude Code procura skills pessoais dentro de:

```text
~/.claude/skills/
```

**macOS ou Linux**

```bash
mkdir -p ~/.claude/skills

git clone https://github.com/14lucas-mendes/ai-tutor-skill \
  ~/.claude/skills/ai-tutor
```

Depois abra ou reinicie o Claude Code.

Para usar diretamente:

```text
/ai-tutor
```

Por exemplo:

```text
/ai-tutor

Quero aprender estatística para uma prova daqui a dois meses.
```

O Claude também pode ativar a skill automaticamente quando perceber que seu pedido corresponde ao AI Tutor.

**Windows PowerShell**

```powershell
New-Item -ItemType Directory -Force "$HOME\.claude\skills"

git clone https://github.com/14lucas-mendes/ai-tutor-skill `
  "$HOME\.claude\skills\ai-tutor"
```

Depois abra novamente o Claude Code.

---

### 🟣 Cursor

O Cursor suporta Agent Skills diretamente. Você pode instalar o AI Tutor de duas maneiras.

**Opção 1: usando o GitHub pelo próprio Cursor**

1. Abra **Customize**.
2. Vá até **Rules**.
3. Clique em **Add Rule**.
4. Escolha **Remote Rule (GitHub)**.
5. Informe o repositório: `https://github.com/14lucas-mendes/ai-tutor-skill`

Depois verifique a área **Customize → Skills** para confirmar que a skill foi reconhecida.

**Opção 2: instalação pelo terminal**

macOS ou Linux:

```bash
mkdir -p ~/.cursor/skills

git clone https://github.com/14lucas-mendes/ai-tutor-skill \
  ~/.cursor/skills/ai-tutor
```

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force "$HOME\.cursor\skills"

git clone https://github.com/14lucas-mendes/ai-tutor-skill `
  "$HOME\.cursor\skills\ai-tutor"
```

Depois reinicie o Cursor.

Para usar, abra o Agent e digite:

```text
/ai-tutor
```

Você também pode simplesmente conversar normalmente. Por exemplo:

```text
Quero começar um programa de estudos de Machine Learning.
Use o AI Tutor.
```

O Cursor pode carregar a skill automaticamente quando ela for relevante.

---

### 🟦 OpenCode

O OpenCode também suporta Agent Skills baseadas em `SKILL.md`.

A pasta global recomendada é:

```text
~/.config/opencode/skills/
```

**macOS ou Linux**

```bash
mkdir -p ~/.config/opencode/skills

git clone https://github.com/14lucas-mendes/ai-tutor-skill \
  ~/.config/opencode/skills/ai-tutor
```

Depois abra novamente o OpenCode.

**Windows PowerShell**

```powershell
New-Item -ItemType Directory -Force "$HOME\.config\opencode\skills"

git clone https://github.com/14lucas-mendes/ai-tutor-skill `
  "$HOME\.config\opencode\skills\ai-tutor"
```

O OpenCode identifica as skills disponíveis e pode carregar o AI Tutor quando seu pedido corresponde à descrição da skill.

Por exemplo:

```text
Use a skill ai-tutor.

Quero aprender SQL para trabalhar com análise de dados.
```

Você também pode simplesmente pedir:

```text
Quero começar um programa de estudos usando o AI Tutor.
```

---

### 💡 Dica: Cursor + OpenCode

Cursor e OpenCode também reconhecem a pasta padrão:

```text
~/.agents/skills/
```

Portanto, se você utiliza Cursor e OpenCode na mesma máquina, pode instalar o AI Tutor uma única vez:

```bash
mkdir -p ~/.agents/skills

git clone https://github.com/14lucas-mendes/ai-tutor-skill \
  ~/.agents/skills/ai-tutor
```

Assim, os dois ambientes podem descobrir a mesma instalação.

---

## 3. Comece seu primeiro estudo

Depois que a skill estiver instalada, você não precisa criar arquivos, editar JSON ou configurar um currículo manualmente.

Basta conversar com o AI Tutor. Por exemplo:

```text
Quero aprender Python do zero para conseguir criar pequenas automações.
Tenho aproximadamente 3 horas por semana para estudar.
```

O tutor fará algumas perguntas para entender coisas como:

- o que você quer aprender;
- qual é seu objetivo;
- quanto tempo você tem disponível;
- seu nível atual;
- se prefere teoria primeiro ou prática primeiro;
- onde deseja salvar seu programa de estudos.

Depois disso, ele cria seu plano inicial.

---

## 🗺️ Seu caminho com o AI Tutor

Depois da configuração inicial, normalmente você seguirá este ciclo:

```text
Configurar estudo
       ↓
Criar seu plano
       ↓
Aula (teoria do tema)
       ↓
Praticar no projeto
       ↓
Receber feedback
       ↓
Revisar pontos fracos
       ↓
Acompanhar progresso
       ↓
Próxima lição
```

Você não precisa decorar comandos. Pode simplesmente conversar com o tutor. Por exemplo:

- `Continue meus estudos.`
- `O que devo estudar hoje?`
- `Quero revisar o que estou esquecendo.`

---

## 💬 Comandos úteis

O AI Tutor reconhece algumas intenções específicas:

| Comando | Para que serve |
| --- | --- |
| `/setup` | Criar um novo programa de estudos |
| `/curriculum` | Ver ou ajustar seu plano |
| `/licao` | Fazer a próxima lição |
| `/review` | Revisar pontos fracos |
| `/feynman` | Testar se você realmente consegue explicar algo |
| `/flashcards` | Criar ou revisar flashcards |
| `/progress` | Ver seu progresso |
| `/sources` | Procurar boas fontes de estudo |
| `/media` | Criar materiais visuais ou multimídia |
| `/diagnostic` | Medir de onde você parte em um tema, sem gerar nota |
| `/profile` | Ver ou corrigir o que o tutor observou sobre como você aprende |

> Esses atalhos representam intenções do AI Tutor. Dependendo do ambiente, você pode digitá-los diretamente ou simplesmente pedir a mesma coisa em linguagem natural.

Por exemplo, "Quero ver meu progresso." tem a mesma intenção de `/progress`, e "Quero revisar os assuntos em que estou tendo mais dificuldade." tem a mesma intenção de `/review`.

---

## 🧠 O que torna o AI Tutor diferente?

Muitos assistentes de IA conseguem explicar assuntos.

O AI Tutor tenta fazer algo diferente: **acompanhar se você está realmente aprendendo.**

Por isso, durante uma sessão ele pode pedir que você:

- explique algo com suas próprias palavras;
- resolva um problema;
- aplique um conceito;
- tente novamente sem ajuda;
- use o que aprendeu em uma situação diferente.

Receber uma explicação do tutor não significa automaticamente que você aprendeu aquele assunto.

Seu progresso aumenta quando você consegue demonstrar conhecimento por conta própria.

### Como o tutor se adapta a você

- **Diagnóstico** (`/diagnostic`): uma sondagem curta antes de um tema novo. Ela posiciona o ponto de partida e nunca vira nota.
- **Perfil de aprendizagem** (`/profile`): o tutor registra fatos observados nas sessões, como quanta ajuda você precisou ou qual estratégia funcionou. Você pode consultar e contestar. O perfil não altera seu domínio.
- **Recuperar antes de reexplicar**: na revisão, você tenta lembrar primeiro e só depois recebe a explicação.
- **Revisão de código pragmática**: a revisão pergunta se o código fica fácil de mudar, só cobra a eliminação de duplicação na terceira repetição, pede que você corrija pequenos defeitos do projeto quando estão no escopo (os outros viram pendência) e prefere fatias de ponta a ponta a polir uma camada só. Princípio de design ainda não ensinado é ensinado antes de ser cobrado.
- **Visuais sob pedido**: durante a aula, peça "mostra visualmente", "desenha o fluxo" ou "mapeia o projeto" e o tutor monta um diagrama, uma tabela de rastreio ou um mapa interativo, seguido de perguntas curtas para conferir se você entendeu. Nada é salvo nem enviado ao NotebookLM, a menos que você peça. Ao salvar, o diagrama vai para a teoria da lição e o mapa interativo fica em `media/visuals/`, sempre em formato leve.
- **Videoaula local** (opcional): o tutor escreve um roteiro em cenas a partir da teoria da lição, confere o código rodando e gera o vídeo no seu computador, com tema escuro, voz local (Piper) e legenda numa faixa separada. Antes de entregar, ele confere os quadros e transcreve a fala de volta. Nada é enviado para fora. As dependências (Piper, Pillow, Pygments, `ffmpeg` e `faster-whisper`) só são exigidas para quem usa o vídeo. Elas ficam num ambiente virtual próprio, o "estúdio", montado a partir do `requirements-video.txt`, com as versões fixas. Detalhes em `references/media-providers.md`.
- **Áudio de revisão local** (opcional): para revisar sem tela. Cada bloco tem uma pergunta, um sinal curto, uns segundos de pausa para você responder e a resposta. O roteiro é próprio, escrito para o ouvido: o tutor não reaproveita a narração do vídeo, que aponta para a tela. Ele usa o mesmo estúdio e gera um MP3 com transcrição.
- **Revisão espaçada**: os intervalos seguem uma escada fixa (1, 3, 7, 16, 35 e 60 dias), ou uma política adaptativa, se você escolher.
- **Aulas de programação adaptativas**: o tutor ajusta exemplos, tamanho dos passos e apoio conforme você avança, mas a tentativa principal continua sendo sua.

### Superfície, profundidade e transferência

O tutor escolhe a estratégia de cada tópico pela fase em que você está, lida do seu domínio:

- **Superfície (0 e 20):** aula do zero, vocabulário e recuperação antes de reler.
- **Profundidade (40 e 60):** você organiza as ideias, explica com suas palavras, confere o próprio trabalho e responde perguntas de causa e efeito.
- **Transferência (80):** antes de aplicar em outro contexto, você compara semelhanças e diferenças com o que já resolveu.

A estratégia também muda com o tipo de matéria: um conceito, um código para implementar ou um sistema que já existe. Para entender um repositório, você primeiro prevê o papel de cada parte; depois vêm a explicação em camadas, uma microtarefa e perguntas de cenário. No começo da sessão, o tutor diz em uma linha a fase e a estratégia escolhida. Quizzes e perguntas ajudam a decidir o próximo passo, mas quem conclui um tópico é a matriz de domínio.

### Teoria primeiro ou prática primeiro

No `/setup`, você escolhe a abordagem de ensino do estudo:

| Abordagem | Como funciona |
| --- | --- |
| `theory_first` (padrão) | Todo tema novo começa por uma aula completa do zero, no formato "ver primeiro": a ideia toda numa frase, depois passos curtos que mostram o código rodando antes de explicar, com cada nome técnico só depois de você ver a coisa acontecer. Vêm ainda uma analogia em destaque, um glossário no fim para consulta, os erros comuns e checagens curtas de entendimento. A prática no projeto vem depois. |
| `practice_first` | Teoria enxuta, com todo termo novo definido, e prática logo em seguida. A teoria aprofunda quando você pedir ou quando aparecerem erros conceituais. |

Nas duas abordagens, um tema que ainda não foi ensinado neste estudo começa do zero, mesmo que o diagnóstico indique que você provavelmente já o conhece. A teoria fica escrita no arquivo da lição (`lessons/`), para você reler sem o chat. Ela é material do tutor e não conta como evidência de domínio; o progresso continua vindo da sua prática.

Se faltar tempo em `theory_first`, a lição é dividida: a teoria numa sessão e a prática na seguinte, que começa com uma recuperação rápida do que foi visto.

Para usar a outra abordagem só na lição atual, peça ao tutor (por exemplo, "nesta lição quero ir direto para a prática"). Isso fica registrado na sessão, vale também para as próximas sessões da mesma lição e não muda a configuração. Para mudar de vez, peça a mudança e confirme.

---

## 📈 Como o progresso funciona?

O AI Tutor mantém um histórico do seu programa de estudos: tentativas, evidências, revisões e o domínio de cada tópico.

### Matriz de domínio

Cada tópico tem um nível de domínio. O nível só sobe com evidência do que você fez, não com o que o tutor explicou.

| Nível | O que você precisa demonstrar |
| --- | --- |
| 0 | Nada ainda: sem evidência válida. |
| 20 | Reconhece os termos ou tenta com muita ajuda. |
| 40 | Aplica parcialmente: com pistas, ou sozinho mas faltando uma parte importante. |
| 60 | Uma explicação com suas palavras (Feynman) e uma aplicação padrão, as duas sozinho. |
| 80 | O que pede o 60, mais uma aplicação padrão feita sozinho num contexto novo (transferência). |
| 100 | O desempenho do 80 repetido em pelo menos duas sessões e dois contextos, percebendo limites ou corrigindo o próprio erro. |

### O que conta como evidência

- **Não contam:** explicações e respostas do tutor, a teoria da lição, código copiado, cards, diagramas e outras mídias geradas, nem o diagnóstico.
- **Aplicação padrão:** cumpre o objetivo da lição de ponta a ponta. Um acerto mais estreito (prever uma saída, rastrear um laço, um `assert` isolado) fica registrado como evidência de apoio (`supporting`). Ele ajuda o tutor a decidir o próximo passo, mas não vale para o 60. Quando isso acontece, o tutor diz qual é o critério e por quê.
- **Transferência para o 80:** uma aplicação de ponta a ponta, feita sozinho, num contexto em que o tópico ainda não foi aplicado. Se sair parcial, você recebe a devolutiva e faz uma variação nova no mesmo contexto.
- **Validade:** evidências com mais de 45 dias continuam no histórico, mas precisam ser reconfirmadas antes de o nível subir.

### Ajuda e autonomia

Quando você trava, o tutor sobe uma escada de ajuda, um degrau por vez:

1. reformula a tarefa;
2. relembra um pré-requisito;
3. faz uma pergunta que aponta a direção;
4. dá uma pista parcial;
5. mostra um esqueleto ou pseudocódigo;
6. explica uma solução.

Os degraus 3 e 4 limitam aquela tentativa a 40; os degraus 5 e 6, a 20.

Alguns tipos de ajuda não tiram o crédito de trabalho autônomo, desde que não entreguem a decisão, o plano ou o código:

- os degraus 1 e 2;
- explicar o contexto (o domínio, os campos, os termos do lugar);
- a **conferência antes da devolutiva**: quando sua solução sai incompleta ou incorreta, o tutor pede uma vez que você a confira contra as regras e os exemplos da tarefa, sem dizer o que falta. Se você achar o erro e corrigir sozinho, a correção conta como trabalho autônomo.

### Continuar de onde parou

O histórico permite continuar seus estudos em sessões futuras. Por exemplo:

```text
Continue de onde paramos.
```

O tutor tenta recuperar sua última sessão e indicar o próximo passo.

---

## 📁 Onde meus estudos ficam salvos?

Durante a primeira configuração, o AI Tutor pergunta onde você quer guardar seu programa de estudos.

Por exemplo, no Windows:

```text
C:\Estudos\python
```

No macOS ou Linux:

```text
~/estudos/python
```

Essa pasta passa a ser seu diretório de estudos. Ela pode conter:

- currículo;
- sessões;
- lições;
- projetos;
- flashcards;
- histórico de progresso;
- visuais de explicação que você pediu para salvar (`media/visuals/`).

Você normalmente não precisa editar esses arquivos manualmente.

Se for estudar em mais de um computador ou na nuvem, veja [Estudo em mais de um computador ou na nuvem](#estudo-em-mais-de-um-computador-ou-na-nuvem).

---

## 🧭 Posso ter mais de um programa de estudos?

Sim. Você pode ter, por exemplo:

```text
~/estudos/python
~/estudos/ingles
~/estudos/estatistica
```

Cada diretório representa um programa de estudos independente.

Assim você pode usar o mesmo AI Tutor para aprender assuntos diferentes sem misturar o progresso.

---

## 🛠️ Está tendo problemas?

### A skill não aparece

Primeiro confirme se existe um arquivo `ai-tutor/SKILL.md` dentro da pasta correta do seu ambiente.

Os caminhos mais comuns são:

| Ambiente | Pasta |
| --- | --- |
| Codex | `~/.codex/skills/ai-tutor/` |
| Claude Code | `~/.claude/skills/ai-tutor/` |
| Cursor | `~/.cursor/skills/ai-tutor/` |
| OpenCode | `~/.config/opencode/skills/ai-tutor/` |
| Cursor + OpenCode | `~/.agents/skills/ai-tutor/` |

Depois reinicie seu agente.

### Python não está disponível

```bash
python --version
```

ou:

```bash
python3 --version
```

O AI Tutor espera Python 3.11 ou superior.

### Git não está disponível

```bash
git --version
```

Se o comando não funcionar, instale o Git antes de usar os comandos de instalação pelo terminal.

### Quero atualizar o AI Tutor

Entre na pasta onde instalou a skill. Por exemplo:

```bash
cd ~/.claude/skills/ai-tutor
```

Depois execute:

```bash
git pull
```

Use o caminho correspondente ao seu ambiente.

> **Mudança de comportamento:** estudos criados antes da abordagem de ensino não têm o campo `teaching_policy` e passam a usar `theory_first`, ou seja, temas novos começam por uma aula completa. Temas que o estudo já trabalhou (com evidência, domínio acima de 0 ou lição concluída) não recomeçam do zero: o tutor escreve um resumo da teoria no arquivo da lição e segue a prática. Para manter o ritmo anterior também nos temas novos, peça ao tutor para mudar o estudo para `practice_first`.

### Estudo em mais de um computador ou na nuvem

Guarde o programa de estudos num repositório Git **privado** (por exemplo, no GitHub), porque a pasta guarda dados pessoais, como o seu perfil de aprendizagem. Rode `git pull` antes de cada sessão e faça commit e push no fim. O AI Tutor não faz pull, commit nem push por você.

Não estude em dois lugares sem fazer push num e pull no outro. Cada gravação muda a revisão dos arquivos de estado, então duas sessões em paralelo sempre dão conflito em `.ai-tutor/*.json`: o Git não junta esses arquivos sozinho. Se o `git pull` der conflito, resolva o conflito e rode o `validate_study` antes de continuar.

Inclua no `.gitignore` do estudo os arquivos temporários da skill:

```text
*.lock
.*.tmp
```

Um `.lock` que sobrou de uma sessão interrompida e foi para o repositório trava as gravações na outra máquina.

Não sincronize a pasta do estudo pelo Google Drive, Dropbox ou OneDrive. Eles copiam arquivo por arquivo e não entendem Git. A pasta `.git` pode corromper, e edições em dois lugares viram cópias como `state (1).json`, sem que o Git mostre o conflito. A proteção da skill contra gravações simultâneas só vale dentro de uma mesma máquina.

O Drive continua útil para material solto, como PDFs, mídia e exports do NotebookLM.

### Quero começar um estudo novo

Peça:

```text
Quero criar um novo programa de estudos.
```

ou use a intenção `/setup`. Depois escolha uma nova pasta. Cada pasta representa um programa separado.

---

## 🎯 Exemplos de uso

**Aprender programação**

```text
Quero aprender JavaScript para conseguir criar aplicações web.
Sou iniciante e tenho quatro horas por semana.
```

**Estudar para uma prova**

```text
Quero estudar estatística para uma prova daqui a dois meses.
Tenho dificuldade principalmente com probabilidade.
```

**Aprender um assunto profissional**

```text
Quero aprender fundamentos de Machine Learning.
Já sei Python, mas nunca trabalhei com modelos de ML.
Meu objetivo é conseguir construir pequenos projetos.
```

**Melhorar em algo que você já conhece**

```text
Já trabalho com SQL, mas sinto dificuldade com consultas complexas,
CTEs e window functions.
Quero montar um programa de estudos focado nesses pontos.
```

---

## 🔬 Para quem quer entender como funciona por dentro

Você não precisa conhecer esta parte para usar o AI Tutor.

Internamente, a skill separa duas áreas:

```text
AI Tutor
│
├── Skill
│   ├── instruções
│   ├── workflows
│   ├── scripts
│   └── regras de aprendizagem
│
└── Seu programa de estudos
    ├── currículo
    ├── sessões
    ├── lições
    ├── projetos
    └── progresso
```

A instalação contém as regras e ferramentas do tutor.

Seu programa de estudos contém seus próprios dados e progresso.

Isso significa que você pode atualizar a skill sem precisar apagar seu histórico de estudos.

Para detalhes técnicos, consulte:

- [`SKILL.md`](SKILL.md)
- [`references/architecture.md`](references/architecture.md)
- [`references/state-contract.md`](references/state-contract.md)
- [`references/learning-contract.md`](references/learning-contract.md)
- [`references/delegation-contract.md`](references/delegation-contract.md)
- [`references/diagnostic-contract.md`](references/diagnostic-contract.md)
- [`references/learner-profile-contract.md`](references/learner-profile-contract.md)
- [`references/learning-strategies.md`](references/learning-strategies.md): estratégias por fase e por tipo de matéria
- [`references/programming.md`](references/programming.md): aulas de programação, revisão de código e roteiro para entender sistemas
- [`references/output-contract.md`](references/output-contract.md): formato das respostas e dos visuais de explicação
- [`references/workflows/`](references/workflows/)

---

## 👩‍💻 Desenvolvimento

A estrutura principal do projeto é:

```text
ai-tutor-skill/
├── SKILL.md
├── agents/
├── references/
├── assets/
├── locales/
├── scripts/
├── tests/
└── docs/
```

- `SKILL.md`: ponto de entrada usado pelos agentes.
- `references/`: workflows e contratos técnicos.
- `scripts/`: inicialização, migração e validação do estado.
- `locales/`: textos traduzidos.
- `docs/superpowers/`: specs e planos de design das mudanças.
- `docs/decisions/`: decisões de rumo do projeto. Por exemplo, [por que o AI Tutor continua como skill e quando pode virar CLI ou MCP](docs/decisions/2026-11-23-skill-cli-ou-mcp.md).

Para validar localmente, rode os mesmos comandos do CI na raiz do repositório:

```bash
python -m unittest discover -s tests -p 'test_*.py'
python scripts/validate_skill.py .
```

Para conferir um programa de estudos:

```bash
python -m scripts.validate_study <pasta-do-estudo>
```

Se você pretende modificar a skill, criar novos workflows ou alterar a forma como o progresso é calculado, consulte primeiro a documentação técnica em `references/` e `docs/`.

---

## 🌐 Compatibilidade

O AI Tutor foi estruturado como uma Agent Skill baseada em `SKILL.md`.

Isso permite que o mesmo projeto seja utilizado por diferentes agentes que suportam esse padrão.

A forma como cada ambiente descobre ou ativa skills pode variar, mas a lógica principal do AI Tutor permanece a mesma.

| Ambiente | Skill | Ativação |
| --- | --- | --- |
| Codex | ✅ | `$ai-tutor` |
| Claude Code | ✅ | `/ai-tutor` ou automática |
| Cursor | ✅ | `/ai-tutor` ou automática |
| OpenCode | ✅ | descoberta automática / skill `ai-tutor` |

---

## ⚠️ Limitações

O AI Tutor ajuda a organizar e acompanhar seu aprendizado, mas não substitui professores, instituições de ensino ou especialistas.

O progresso registrado representa evidências observadas durante as sessões e não deve ser interpretado como certificação profissional.

Integrações externas e envio de materiais dependem das permissões disponíveis no ambiente e devem ser autorizados antes do uso.

O comportamento também pode variar ligeiramente entre Codex, Claude Code, Cursor e OpenCode, porque cada agente possui suas próprias ferramentas, permissões e mecanismos de execução.

---

## 🌱 Status do projeto

O AI Tutor é um projeto educacional em evolução.

O objetivo é tornar o estudo com agentes de IA mais **estruturado, contínuo, verificável e útil na prática**.

Feedback, testes e contribuições são bem-vindos.

## 📄 Licença

Distribuído sob a licença [MIT](LICENSE).
