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
