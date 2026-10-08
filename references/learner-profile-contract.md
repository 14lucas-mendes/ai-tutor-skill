# Learner Profile Contract

O Learner Profile descreve como o aluno está aprendendo ao longo das sessões. Ele não substitui o diagnóstico inicial, o Learning Contract ou as evidências de domínio.

## Três fontes distintas

- `declared_preferences`: o que o aluno afirma preferir. Uma preferência pode mudar; a alteração inativa o registro anterior e preserva o histórico.
- `observations`: fatos objetivos de sessões, como nível de ajuda, tentativa autônoma, confiança declarada, dificuldade percebida ou resultado de uma estratégia.
- `inferences`: hipóteses do tutor sustentadas por IDs de observações. Uma inferência pode estar `hypothesis` ou `challenged` pelo aluno.

Não registre “aluno visual”, “auditivo” ou qualquer estilo fixo. Registre comportamentos observáveis e escopo limitado, por exemplo: `worked_examples_effective` em um tópico.

## Proveniência e confiança

Uma observação isolada não cria inferência. Use `low` com pelo menos duas observações consistentes, `medium` com três ou mais e `high` com cinco ou mais em pelo menos duas sessões. Sinais contraditórios reduzem a confiança ou impedem sua elevação.

Inferências com escopo `topic` só podem referenciar observações daquele tópico. Inferências com escopo `study` exigem sinais em pelo menos dois tópicos. Ausência de dados é sempre `unknown`, nunca baixa autonomia.

## Dimensões iniciais

O resumo começa com `autonomy` e `help_dependency` em `unknown`, `low`, `medium` ou `high`, e `confidence_pattern` em `unknown`, `underconfident`, `calibrated`, `overconfident` ou `mixed`. O resumo é uma síntese, não uma evidência independente.

O resumo é recalculado a cada observação, e uma dimensão com menos de duas observações utilizáveis fica `unknown`:

- `autonomy` usa a **taxa de acerto** das observações `autonomous_attempt` (`value.result`: `correct` ou `autonomous_success` valem 1, `partial` vale 0,5 e `incorrect` vale 0), nunca a quantidade de acertos. Taxa abaixo de 0,5 é `low`; de 0,5 em diante é `medium`; é `high` só com taxa de 0,75 ou mais **e** cinco acertos em pelo menos duas sessões.
- `help_dependency` usa a média de `value.help_level` das observações `help_usage`, de 0 (sem ajuda) a 6 (degraus da escada de ajuda do Learning Contract): média de 4 ou mais é `high`, de 2 a 4 é `medium` e abaixo de 2 é `low`.

O validador rejeita `help_usage` sem `help_level` inteiro de 0 a 6 e `autonomous_attempt` com `result` fora da lista acima, para que nenhuma observação seja ignorada em silêncio. A migração renomeia a chave antiga `support_level` para `help_level` e recalcula o resumo.

## Atualização e correção

Atualize o perfil somente ao fechar ou interromper uma sessão que produziu um sinal relevante. Use escrita atômica com revisão esperada. O aluno pode consultar `/profile`, corrigir uma preferência e contestar uma inferência. A contestação muda a hipótese e registra o feedback, mas não apaga as observações factuais.

Learner Profile nunca altera diretamente `mastery`, `retention`, `evidences`, `evidence_ids`, currículo ou estratégia de ensino. Qualquer adaptação futura será uma fase posterior e deverá respeitar estes limites.
