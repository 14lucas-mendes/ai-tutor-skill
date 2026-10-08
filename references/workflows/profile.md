# Learner Profile Workflow

Leia `references/architecture.md`, `references/learner-profile-contract.md`, `references/state-contract.md` e `references/learning-contract.md`.

Use `/profile` ou intenções como “o que você percebeu sobre como estou aprendendo?” para apresentar o perfil atual.

1. Valide `state.json` e `learner-profile.json` antes de responder.
2. Mostre em blocos separados as preferências declaradas, os padrões observados e as inferências.
3. Para cada inferência, mostre confiança, escopo e as observações que a sustentam; se não houver dados suficientes, diga `unknown`.
4. Se o aluno corrigir uma preferência, inative o registro anterior e acrescente a nova preferência. Não apague histórico.
5. Se o aluno contestar uma inferência, preserve as observações, marque a inferência como `challenged` e registre o feedback literal do aluno.
6. Valide o novo perfil após cada alteração e não modifique `mastery`, evidências, retenção, currículo ou estratégia de ensino.

Não transforme o perfil em diagnóstico de personalidade ou “learning style”. Uma inferência é uma hipótese operacional, nunca uma verdade sobre o aluno.

