# Learning Strategies Contract

Este contrato descreve políticas operacionais que aumentam a chance de aprender.
Ele não cria níveis de domínio e não substitui `references/learning-contract.md`.

Toda estratégia precisa declarar quando usar, quando evitar, como executar e como avaliar o resultado. Uma estratégia, uma mídia ou uma tentativa de recuperação nunca é evidência por si só.

## `retrieval_first`

- **Quando usar:** antes de reensinar ou revisar um tópico devido, com baixa retenção ou com weak point ativo.
- **Quando evitar:** quando não há alvo de revisão relevante ou quando a atividade já está em modo de performance para uma capacidade demonstrada.
- **Como executar:** fazer uma pergunta curta, esperar a tentativa autônoma e só depois oferecer explicação, pista ou material.
- **Como avaliar:** registrar o resultado da recuperação separadamente; registrar evidência somente se a resposta cumprir o Learning Contract.
- **Limite:** a recuperação não altera mastery automaticamente.

## `adaptive_spacing`

- **Quando usar:** somente quando o estudo optou explicitamente pelo modo adaptativo.
- **Quando evitar:** em estudos legados ou configurados com a escada fixa.
- **Como executar:** calcular o próximo intervalo a partir de resultado objetivo, dificuldade, confiança e horizonte temporal.
- **Como avaliar:** verificar `due_at`, `interval_days`, `spaced_repetition_step` e `last_result` sem confundir confiança com correção.
- **Limite:** o agendamento altera prática e retenção, não mastery.

## `conditional_interleaving`

- **Quando usar:** com pelo menos dois tópicos relacionados, competência mínima demonstrada e uma tarefa que exija discriminar estratégias.
- **Quando evitar:** durante aquisição bloqueada, com pré-requisito ativo, um único tópico ou evidência insuficiente.
- **Como executar:** misturar problemas sem revelar previamente qual tópico ou estratégia cada item testa.
- **Como avaliar:** observar seleção de estratégia e aplicação; registrar cada evidência no tópico correto.
- **Limite:** a mistura não cria evidência nem domínio sem a tentativa autônoma normal.

## `representational_complementarity`

- **Quando usar:** quando uma segunda representação esclarece relações, estruturas, processos ou diferenças.
- **Quando evitar:** quando texto, áudio, imagem ou vídeo apenas repetem a mesma informação ou aumentam a carga sem função.
- **Como executar:** declarar o papel primário, a representação complementar e a justificativa pedagógica.
- **Como avaliar:** verificar distinção entre as representações, grounding e acessibilidade.
- **Limite:** artefatos continuam com `evidence_eligible: false`; a aprendizagem é verificada por recuperação, explicação ou aplicação autônoma.

## `phase_aware_strategy`

A eficácia de uma estratégia depende da fase em que o aluno está em cada tópico: superfície, profundidade ou transferência (modelo de Hattie & Donoghue, 2016, também usado por Júlio Santos em *Neurociência da Aprendizagem*). Use o modelo como estrutura de decisão, não como tabela de tamanhos de efeito.

- **Quando usar:** ao planejar a lição e ao abrir cada sessão, para escolher a estratégia principal de cada tópico trabalhado.
- **Quando evitar:** para criar ou alterar níveis de domínio; a fase é lida do domínio, nunca o contrário.
- **Como executar:** leia a fase do `mastery` atual do tópico, cruze com o tipo de matéria e declare ao aluno, em uma linha, a fase e a estratégia escolhida. A fase muda só quando o domínio muda, nunca pelo calendário.
- **Como avaliar:** a estratégia escolhida combina com a fase, e a evidência registrada segue o Learning Contract.
- **Limite:** quizzes, perguntas de cenário e checagens de entendimento informam a próxima decisão, mas não concluem tópico nem lição; quem conclui é a matriz de domínio.

### Fase pelo domínio

| `mastery` do tópico | Fase | Objetivo do tutor |
| --- | --- | --- |
| 0 (ainda não ensinado) | Superfície — aquisição | Construir o modelo mental e o vocabulário. |
| 20 | Superfície — consolidação | Fixar por recuperação e prática curta com feedback. |
| 40 | Profundidade — aquisição | Relacionar ideias: porquê, quando usar e quando não usar. |
| 60 | Profundidade — consolidação | Explicar, autoavaliar e variar os problemas. |
| 80 | Transferência | Usar em contexto novo, comparando semelhanças e diferenças. |
| 100 | Manutenção | Espaçar revisões e detectar limites. |

### Estratégia por fase e tipo de matéria

Tipos de matéria: **conceito** (ideia ou arquitetura, como autenticação por token ou grafo de agentes), **procedimento** (código a implementar) e **sistema existente** (um repositório ou programa que já existe, inclusive o do aluno).

| Fase | Conceito | Procedimento | Sistema existente |
| --- | --- | --- | --- |
| Superfície — aquisição | Teoria do zero com analogia e vocabulário; visual só se pedido. | Teoria e exemplo lido linha a linha, diferente da tarefa. | O aluno prevê o papel de cada parte; depois, explicação em camadas (mapa só se pedido). |
| Superfície — consolidação | Recuperação antes de reler a teoria; cards espaçados. | Prática curta com feedback; recuperação antes de reler. | O aluno redesenha o fluxo principal de memória. |
| Profundidade — aquisição | O aluno organiza as ideias (mapa conceitual, tabela comparativa). | Exemplos que retiram apoio aos poucos; aplicação padrão. | Rastrear um caso de ponta a ponta; microtarefa controlada, como um log. |
| Profundidade — consolidação | Explicação Feynman; perguntas de causa e efeito. | Conferência antes da devolutiva; variações; intercalação só quando `scripts/practice_strategy.py` liberar. | Perguntas de cenário ("o que acontece se esta parte falhar?"); explicar uma mudança antes de fazê-la. |
| Transferência | Comparar o conceito em dois contextos antes de aplicar. | Listar semelhanças e diferenças com o problema já resolvido; depois, tarefa no contexto novo. | Aplicar o que aprendeu num segundo sistema ou módulo. |
| Manutenção | Revisão espaçada. | Revisão espaçada; casos-limite novos. | Revisão espaçada; detectar onde o sistema mudou. |

Em todas as fases valem as regras normais: o aluno tenta o núcleo cognitivo antes de ver a solução, conteúdo do tutor nunca é evidência e um tópico ainda não ensinado começa do zero.

