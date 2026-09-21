# Diagnostic Workflow

Leia `references/architecture.md`, `references/state-contract.md`, `references/learning-contract.md` e `references/diagnostic-contract.md`.

Use este fluxo para `/diagnostic` ou quando o aluno disser que quer descobrir o que já sabe antes de começar, avançar ou revisar uma área.

1. Leia `study-config.json`, o objetivo, o currículo, o estado e o diagnóstico interrompido mais recente.
2. Confirme o objetivo ou a área a diagnosticar e derive somente as capacidades e pré-requisitos relevantes.
3. Crie uma execução diagnóstica `in_progress` com ID estável e persista o checkpoint antes da primeira pergunta.
4. Faça uma tarefa ou pergunta por vez. Colete a resposta do aluno antes de avaliar ou revelar a solução.
5. Classifique a observação conforme o Diagnostic Contract e escolha `probe_up`, `probe_down` ou `probe_across`.
6. Registre a observação e o checkpoint após cada resposta; não crie evidência nem altere `mastery`.
7. Encerre quando o ponto de entrada estiver claro, gere o resumo e projete a estimativa mais recente nos tópicos envolvidos.
8. Valide o estado e proponha a ordem inicial do currículo explicando quais tópicos foram pulados, mantidos como pré-requisitos ou priorizados.

Uma execução interrompida deve ser retomada antes de iniciar outro ramo. Um re-diagnóstico cria nova entrada append-only e nunca apaga evidências, domínio, sessões, lições, pontos fracos ou projetos.

