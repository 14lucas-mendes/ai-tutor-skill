# Diagnostic Contract

O diagnóstico estima o ponto de partida; não comprova domínio. Ele responde “onde começar?”, enquanto o Learning Contract responde “o que foi demonstrado?”.

## Separação de conceitos

- `declared_level`: experiência declarada pelo aluno.
- `diagnostic_estimate`: hipótese baseada nas sondagens.
- `mastery`: domínio demonstrado pelas evidências normativas.

Nunca copie uma estimativa diagnóstica para `mastery`, `evidences` ou `evidence_ids`.

## Estimativas

`not_observed` significa que ainda não houve sondagem; `unknown` significa que a sondagem foi insuficiente ou inconclusiva; `weak` indica uma lacuna observada; `partial` indica aplicação incompleta; `likely_known` indica sinal suficiente para começar além daquele tópico. Nenhuma classificação significa `mastered`.

Use confiança `low`, `medium` ou `high`. A confiança descreve a qualidade do sinal, não a porcentagem de domínio.

## Registro canônico

`state.json.diagnostics` é uma lista append-only. Cada execução tem `diagnostic_id`, objetivo, escopo, status, timestamps, observações, resumo e `entry_topic_id`. Uma observação registra a pergunta ou tarefa, a resposta do aluno, o tópico, a estimativa, a confiança, a direção da sondagem, eventual lacuna de pré-requisito e uma justificativa factual.

Os status são `not_started`, `in_progress`, `interrupted` e `completed`. Uma execução concluída precisa de `completed_at`. Re-diagnósticos criam uma nova execução; não sobrescrevem o histórico.

## Regras pedagógicas

Parta do objetivo do aluno e das capacidades necessárias. Prefira produção, explicação, previsão, correção e comparação a reconhecimento ou múltipla escolha. Faça uma pergunta por vez e não revele a solução do núcleo que está sendo sondado antes da resposta autônoma.

Após cada resposta, escolha `probe_up` para aprofundar após sucesso, `probe_down` para investigar um pré-requisito após falha e `probe_across` para testar a mesma capacidade em outro contexto quando o sinal for incerto.

Pare quando houver um ponto de entrada útil, os pré-requisitos principais estiverem classificados e qualquer incerteza restante não mudar o início do currículo.

