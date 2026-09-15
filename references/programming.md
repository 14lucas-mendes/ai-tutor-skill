# Programming Learning

Use real code when an observable objective requires implementation. Conceptual explanations do not automatically require a project or commit.

Projects live in `<study_root>/projects/<slug>/`, where the slug is lowercase with hyphens. Keep structure proportional to the task. Record the exact file, test command, and result used as evidence.

## Delivery evidence

Require a student-created Git commit only when the project is a writable Git repository and the curriculum item explicitly names a commit as a criterion. The tutor explains and reviews but does not commit for the student.

Without Git, record file paths, the executed test and a SHA-256 content hash. This fallback preserves traceability without blocking learning.

When implementation is the assessed capability, code supplied by the tutor that performs the essential part of the task makes that attempt guided practice. Explaining or retyping a near-identical supplied implementation does not turn it into an independent application. Collect a later reconstruction or a substantially different task in which the learner implements the cognitive core before receiving that code.

## Code review

Check only relevant items:

1. Acceptance criteria are satisfied.
2. The code runs with expected behavior.
3. Appropriate tests pass.
4. Relevant errors and boundaries are handled.
5. Names and structure aid maintenance.
6. Complexity and duplication are justified.
7. The change is scoped and deliverable.

Feedback uses `What worked`, `What to adjust`, and `Next step`, with at most three items each. Every adjustment identifies location, impact, and a verifiable action.

Prefer progressive useful projects, but select them from current mastery and learner motivation rather than a fixed technology ladder.

## Adaptive individual lesson protocol

Use this protocol for one-to-one programming lessons. A 60–90 minute lesson is a planning envelope; the ranges below are starting points that may be shortened, extended, or reordered when the learner's performance makes that useful. Phases may also be repeated, combined, or omitted when they are redundant for the learner. The lesson is successful when the learner owns the relevant capability, not when every minute or section is consumed. The cognitive-core attempt, appropriate verification, and closing checkpoint are invariants; phase completion is not evidence.

### 1. Activation and clear objective (5–8 minutes)

Start from a concrete operational problem or the next slice of the learner's current project. State one observable outcome in plain language: what the learner will be able to implement, diagnose, or explain by the end. Make the project's relevance explicit.

### 2. Probe (about 5 minutes)

Ask one low-stakes question at a time, using at most two short probes or a tiny mini-challenge when useful, to locate the learner's current ability and zone of proximal development. Do not grade an unintroduced concept as an incorrect answer. Use the result to choose the depth and amount of support for the rest of the lesson.

### 3. Minimal exposition and guided example (10–15 minutes)

Explain only what is needed to unblock the next action, moving from the concrete example toward the abstraction. Use runnable code, pair programming, or a visible execution when that clarifies behavior. In learning mode, do not perform the undemonstrated cognitive core: demonstrate incidental syntax or a partial example, then ask the learner to attempt the essential decision or implementation before showing it.

### 4. Guided practice with receding scaffolding (15–20 minutes)

Move through the help ladder as needed: rephrase the task, retrieve a prerequisite, ask a directional question, give a partial hint, provide an incomplete skeleton or pseudocode, and only then explain a solution. After a successful step, remove support and vary the context. Code supplied at the core level is guided practice, not independent evidence.

### 5. Independent practice and a small project change (20–25 minutes)

Ask the learner to solve a new but related problem in the current project. Prefer real code, tests, logs, or a documented design decision over another theory question. Prioritize Bloom's Apply and Create; keep the scope proportional and use fictional or anonymized data where appropriate. The tutor reviews the learner's artifact rather than silently replacing it.

### 6. Verification and Feynman check (8–10 minutes)

Run the relevant code or tests when possible, inspect the result, and ask the learner to explain the key concept and their decisions in their own words. Include a debugging check when errors or boundaries matter. Separate objective correctness from confidence, and record only demonstrated evidence under the mastery matrix.

### 7. Closing and next smallest delivery (about 5 minutes)

Summarize what was demonstrated, what remains uncertain, and the smallest useful follow-up. Preserve a checkpoint and route unresolved gaps to the next session; do not advance just because the nominal time elapsed. When the lesson closes, update the canonical state and required projections according to the session workflow.

## Adaptation rules

- **Fast demonstrated mastery:** shorten exposition and scaffolding, deepen the project variation, add a transfer case, or move to the next justified capability.
- **Difficulty or repeated errors:** slow down, return to a concrete example, use an analogy, split the task, retrieve the prerequisite, and increase support. Do not reset the whole curriculum or force the planned next topic.
- **Time pressure:** protect the learner's attempt, debugging, verification, and checkpoint; trim optional explanation, polish, or breadth first.
- **Spiral revisit:** bring previously learned concepts back in the project with a new constraint, data shape, failure mode, or integration boundary. Increasing complexity should follow demonstrated readiness.
- **Project connection:** if a lesson cannot yet produce a project change, make the connection explicit and record the smallest preparatory artifact or decision that moves the project forward.
- **Tone:** stay direct, clear, patient, and demanding about the quality of understanding without becoming rude.

Use these observable signals to choose the next move rather than to impose a quota:

| Signal | Adaptive response |
| --- | --- |
| Implements and explains without help | Omit redundant exposition and offer a transfer variation. |
| Explains but cannot implement | Return to a minimal concrete example and use short guided practice. |
| Implements but cannot diagnose | Introduce a controlled failure and ask for inspection before explaining. |
| Succeeds after a partial hint | Reduce one level of support and change the context. |
| Repeats the same causal error | Split the task, revisit the prerequisite, or use a new analogy. |
| Encounters an unintroduced concept | Teach it before evaluation; do not score the knowledge gap as learner failure. |
| Time becomes limited | Preserve attempt, debugging, verification, and checkpoint; trim optional exposition or polish. |

The protocol is a flexible teaching loop, not a compliance checklist. The tutor may repeat or combine phases when doing so increases real understanding while preserving the cognitive-core and evidence gates in `references/learning-contract.md` and `references/delegation-contract.md`.
