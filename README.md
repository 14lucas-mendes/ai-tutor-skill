# AI Tutor

[![Validate](https://github.com/14lucas-mendes/ai-tutor-skill/actions/workflows/validate.yml/badge.svg)](https://github.com/14lucas-mendes/ai-tutor-skill/actions/workflows/validate.yml)

Uma skill do Codex para transformar o estudo com IA em um processo contínuo, prático e acompanhado.

O AI Tutor não mede aprendizagem pela quantidade de explicações lidas. Ele acompanha o que o aluno consegue fazer, explicar, corrigir e transferir para novos problemas.

## Em uma frase

O tutor explica quando necessário, mas prioriza a tentativa do aluno, a prática, o debugging, a revisão e o progresso comprovado.

## O que mudou recentemente

A skill passou a trabalhar com uma camada adaptativa mais completa:

- aulas de programação flexíveis, com suporte que diminui conforme o aluno evolui;
- diagnóstico inicial para descobrir por onde começar;
- Learner Profile para registrar preferências e observações factuais;
- recuperação antes de reexplicar um conteúdo;
- espaçamento fixo por padrão e adaptativo somente quando escolhido;
- interleaving apenas quando o aluno estiver pronto;
- uso de diferentes representações somente quando elas têm uma função pedagógica clara.

Essas camadas ajudam o tutor a escolher o próximo passo. Elas não substituem as evidências de domínio.

## Como funciona uma aula adaptativa

Uma aula individual de programação costuma seguir este fluxo:

| Etapa | O que acontece |
| --- | --- |
| 1. Objetivo | O tutor apresenta um problema concreto e define o resultado esperado. |
| 2. Sondagem | O aluno responde uma pergunta curta ou faz uma pequena tentativa. |
| 3. Explicação mínima | O tutor explica somente o necessário para desbloquear a próxima ação. |
| 4. Prática guiada | O aluno resolve com apoio; o suporte diminui depois de cada avanço. |
| 5. Prática independente | O aluno aplica a ideia em uma tarefa nova ligada ao projeto. |
| 6. Verificação e Feynman | O código é executado ou inspecionado, e o aluno explica suas decisões. |
| 7. Próximo passo | A sessão registra o que foi demonstrado, o que falta e a menor próxima entrega. |

Esse fluxo não é um checklist rígido. As etapas podem ser encurtadas, combinadas, repetidas, reordenadas ou omitidas quando não forem necessárias. O tutor pode mudar entre aprendizagem, avaliação e performance na mesma sessão.

Três coisas continuam obrigatórias:

1. o aluno tenta o núcleo da habilidade;
2. o resultado é verificado de forma adequada;
3. a sessão termina com um checkpoint.

Completar uma etapa não cria evidência por si só.

## Atalhos principais

| Necessidade | Atalho | Resultado |
| --- | --- | --- |
| Iniciar um programa | `/setup` | Configura o estudo e cria seu estado inicial. |
| Descobrir por onde começar | `/diagnostic` | Faz sondagens curtas e cria uma estimativa, sem alterar domínio. |
| Consultar o perfil de aprendizagem | `/profile` | Mostra preferências, observações e hipóteses com sua confiança. |
| Continuar uma sessão | “continue de onde paramos” | Retoma a sessão ativa ou interrompida que ainda pode continuar. |
| Planejar o currículo | `/curriculum` | Organiza capacidades, pré-requisitos, projetos e transferências. |
| Criar a próxima lição | `/licao` | Seleciona uma lição elegível para o estado atual. |
| Revisar pontos fracos | `/review` | Faz uma tentativa de recuperação antes de reexplicar. |
| Testar uma explicação | `/feynman` | Pede uma explicação autônoma com exemplo e limites. |
| Criar ou revisar cards | `/flashcards` | Organiza recuperação espaçada sem confundir confiança com acerto. |
| Ver progresso | `/progress` | Mostra domínio, retenção, evidências e próximo foco. |
| Pesquisar fontes | `/sources` | Registra fontes verificáveis e sua finalidade. |
| Criar material de estudo | `/media` ou `/notebooklm` | Prepara material local ou uma integração autorizada com fallback. |

## Como o domínio é medido

O tutor registra comportamentos demonstrados, não apenas participação:

| Nível | Exemplo simples |
| --- | --- |
| 20 | Reconhece o conceito ou tenta com ajuda intensa. |
| 40 | Aplica parte do procedimento com uma pista ou pergunta direcional. |
| 60 | Explica com suas próprias palavras e realiza uma aplicação padrão de forma autônoma. |
| 80 | Faz também uma aplicação transferida para outro contexto. |
| 100 | Repete o desempenho em sessões e contextos diferentes, detectando limites ou corrigindo a si mesmo. |

Uma explicação fornecida pelo tutor, um card gerado, uma imagem, um vídeo ou uma tentativa feita com o núcleo resolvido pelo tutor não são evidências autônomas.

O tutor pode ensinar um pré-requisito sem penalizar o aluno. O que não pode fazer é entregar os critérios, a análise, a conclusão ou a implementação essencial da habilidade avaliada e contar isso como autonomia.

O domínio continua separado de outras informações:

- diagnóstico não altera `mastery`;
- Learner Profile não altera `mastery`;
- recuperação organiza a prática, mas não aumenta domínio sozinha;
- cards e mídia não são evidência;
- confiança do aluno não transforma uma resposta errada em correta.

## Camadas adaptativas

### Diagnóstico

O `/diagnostic` responde “por onde começar?”. Ele usa pequenas sondagens para identificar capacidades prováveis, lacunas e pré-requisitos.

Uma estimativa diagnóstica é uma hipótese de ponto de partida. Ela não significa que o tópico foi dominado e não substitui uma tentativa avaliada pelo Learning Contract.

### Learner Profile

O `/profile` separa três tipos de informação:

- preferências declaradas pelo aluno;
- observações factuais das sessões;
- hipóteses do tutor sustentadas por observações.

O perfil pode ser corrigido pelo aluno e mantém o histórico. Ele não cria rótulos como “aluno visual” ou “aluno auditivo”, não diagnostica personalidade e não altera domínio, retenção ou evidências.

### Recuperação e espaçamento

Antes de reexplicar um conteúdo em revisão, o tutor faz uma pergunta curta para o aluno tentar recuperar a ideia sozinho. Depois disso, decide se deve explicar, dar uma pista ou propor outra aplicação.

A escada de revisão fixa — 1, 3, 7, 16, 35 e 60 dias — é o padrão. O modo adaptativo só é usado quando o estudo escolhe explicitamente `spacing_policy.mode` como `adaptive`.

### Interleaving

Misturar tópicos pode ajudar o aluno a escolher estratégias, mas não é aplicado automaticamente. Só entra quando há pelo menos dois tópicos relacionados, pré-requisitos suficientes e uma decisão pedagógica clara.

### Representações complementares

Imagem, gráfico, áudio, vídeo ou mapa são usados apenas quando acrescentam uma representação útil. O material precisa ter fonte, objetivo e acessibilidade. Nenhum artefato multimídia é evidência de domínio por si só.

## Uso de IA durante o estudo

O tutor protege a parte do raciocínio que o aluno ainda precisa aprender:

- em `learning`, o aluno tenta o núcleo antes de receber a solução;
- em `assessment`, a resposta é coletada antes de revelar o núcleo;
- em `performance`, a IA pode acelerar partes já demonstradas, mas o aluno verifica o resultado e mantém o julgamento final.

Usar IA não apaga um domínio já demonstrado. O critério é saber o que permanece com o aluno quando a assistência é retirada.

## Estrutura de um estudo

Cada programa possui duas raízes com responsabilidades diferentes:

- `skill_root`: instalação da skill, referências, scripts e templates; deve ser tratada como somente leitura;
- `study_root`: pasta escolhida para um programa de estudo específico.

Dentro do `study_root`:

```text
meu-ai-tutor/
├── .ai-tutor/
│   ├── study-config.json
│   ├── state.json
│   ├── media-index.json
│   ├── cards.json
│   ├── sources.json
│   └── learner-profile.json
├── curriculum.md
├── session-log.md
├── flashcards.md
├── lessons/
├── media/
└── projects/
```

Os arquivos JSON são o estado canônico. Os arquivos Markdown são projeções legíveis. Diagnósticos ficam separados das evidências, e o Learner Profile fica separado do domínio.

Depois de qualquer mudança de estado, valide o estudo com o script da skill. A atualização deve ser atômica e preservar a revisão esperada do estado.

## Quick start

### Pré-requisitos

- Python 3.11 ou superior;
- Git;
- um ambiente de chat ou agente que carregue a skill `ai-tutor`.

### Inicializar um estudo

No PowerShell, ajuste os dois caminhos para o seu ambiente:

```powershell
$skillRoot = 'C:\caminho\para\ai-tutor-skill'
$studyRoot = 'C:\Estudos\meu-ai-tutor'

$config = @'
{
  "topic": "Fundamentos de Python",
  "goal": "Construir automações pequenas com testes",
  "deadline": null,
  "weekly_hours": 3,
  "preferred_times": ["flexível"],
  "initial_level": "básico",
  "language": "pt-BR",
  "accessibility": [],
  "source_policy": {
    "prefer_primary": true,
    "prefer_pt_br": true
  },
  "spacing_policy": {
    "mode": "fixed",
    "target_horizon_days": null
  }
}
'@

python "$skillRoot\scripts\init_study.py" `
  --study-root "$studyRoot" `
  --config-json $config

python "$skillRoot\scripts\validate_study.py" "$studyRoot"
```

Depois, carregue a skill no seu ambiente de chat e peça `/diagnostic` se quiser descobrir o ponto de entrada antes de montar a ordem inicial. Se preferir começar diretamente, peça `/curriculum` ou `/licao`.

Use `/profile` depois que existirem observações de sessões. Um perfil vazio não é um problema: ausência de dados significa `unknown`, não baixa capacidade.

O script de projeções é opcional:

```powershell
python "$skillRoot\scripts\projections.py" "$studyRoot"
```

Use-o somente quando o seu programa permitir projeções automáticas. Alguns estudos mantêm `session-log.md` manualmente para preservar uma narrativa mais fiel.

## Limites e segurança

- A skill organiza aprendizagem; não certifica competência profissional.
- O tutor não substitui prática real, revisão humana ou documentação oficial.
- Operações em arquivos dependem das permissões e da autorização disponíveis.
- Upload externo exige consentimento específico no momento do envio e identificação dos arquivos.
- Credenciais, cookies e tokens não são manipulados pela skill.
- Conteúdo externo precisa ser revisado antes de entrar no material de estudo.
- Mídia, diagnóstico, perfil e respostas do tutor não são convertidos automaticamente em evidência.

## Para quem mantém o projeto

O entrypoint [SKILL.md](SKILL.md) roteia a intenção para contratos e workflows em [`references/`](references/). Os scripts cuidam de inicialização, migração, validação, projeções, recuperação, espaçamento e perfil.

Para validar o pacote antes de publicar:

```powershell
python -m unittest discover -s tests -p 'test_*.py' -v
python scripts/validate_skill.py .
python -m compileall -q scripts tests
```

As mudanças devem ser pequenas, testáveis e justificadas por uma necessidade real de aprendizagem, confiabilidade ou manutenção.

## Status

Projeto educacional em evolução. A arquitetura v2 e a camada adaptativa estão implementadas; o desenvolvimento continua orientado por evidências de uso, testes determinísticos, cenários comportamentais e revisão humana.
