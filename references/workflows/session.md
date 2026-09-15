# Session Workflow

Read and validate canonical state before the first learning question.

## Resume

Resume the latest `in_progress` session. If none exists, resume the latest `interrupted` session whose `resumable` field is true by adding the `resumed` transition. Recover its checkpoint, lesson IDs, weak points, and next action. Open a new session only when no resumable work exists.

## Conduct

1. Set one observable session objective, identify its cognitive core, and anchor it to the current project or concrete problem.
2. Use one low-stakes prerequisite question or probe only when the objective depends on locating prior ability. Do this after the learner knows what they are trying to accomplish.
3. Select the mode for the current cognitive-core segment under `references/delegation-contract.md`. A session may transition between `learning`, `assessment`, and `performance` when different behaviors have different demonstrated readiness:
   - `learning`: teach from concrete to abstract without performing the undemonstrated cognitive core; request an observable attempt, then apply the help ladder. Guided work is not independent evidence.
   - `assessment`: present the task and collect the learner's response before teaching or revealing the cognitive core. Judge it under the normative contracts, then offer assisted review when useful.
   - `performance`: verify that existing evidence covers the delegated capability and that the learner can evaluate the result. Permit immediate generative acceleration for demonstrated parts, retain verification and final judgment with the learner, and route any new cognitive core to `learning` or `assessment`.
4. Record evidence, retention, weak points, cards, and next focus under the normative contracts. Do not record completion of a phase as evidence; record only observable learner behavior.

For an individual programming session, apply the adaptive lesson protocol in `references/programming.md`: activation and a clear objective, a low-stakes probe, minimal concrete exposition, guided practice with receding scaffolding, independent project work, verification plus Feynman explanation, and a small next step. The phase order is a reliable default, not a rigid timetable: enter, repeat, combine, reorder, shorten, or omit a phase when the learner's performance makes that useful. Never omit the learner-owned cognitive-core attempt, appropriate verification, or closing checkpoint merely to fit the clock.

## Close

On completion or interruption, append the valid transition, record timestamps, checkpoint, topics, evidence IDs, difficulty, next step, and files changed. For programming, preserve the current project slice, the last learner-owned behavior demonstrated, the support level most recently used, any unresolved blocker, and the next smallest delivery when available; a phase label is optional and never evidence. Update lesson state independently. Validate canonical state after the atomic update.
