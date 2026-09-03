# Session Workflow

Read and validate canonical state before the first learning question.

## Resume

Resume the latest `in_progress` session. If none exists, resume the latest `interrupted` session whose `resumable` field is true by adding the `resumed` transition. Recover its checkpoint, lesson IDs, weak points, and next action. Open a new session only when no resumable work exists.

## Conduct

1. Confirm one prerequisite with one question when the objective depends on it.
2. Set one observable session objective, identify its cognitive core, and select `learning`, `assessment`, or `performance` under `references/delegation-contract.md`.
3. Follow exactly one mode branch:
   - `learning`: teach from concrete to abstract without performing the undemonstrated cognitive core; request an observable attempt, then apply the help ladder. Guided work is not independent evidence.
   - `assessment`: present the task and collect the learner's response before teaching or revealing the cognitive core. Judge it under the normative contracts, then offer assisted review when useful.
   - `performance`: verify that existing evidence covers the delegated capability and that the learner can evaluate the result. Permit immediate generative acceleration for demonstrated parts, retain verification and final judgment with the learner, and route any new cognitive core to `learning` or `assessment`.
4. Record evidence, retention, weak points, cards, and next focus under the normative contracts.

## Close

On completion or interruption, append the valid transition, record timestamps, checkpoint, topics, evidence IDs, difficulty, next step, and files changed. Update lesson state independently. Validate canonical state after the atomic update.
