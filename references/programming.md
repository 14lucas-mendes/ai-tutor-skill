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
5. The code is easy to change: names and structure make the next likely change touch one place, not many.
6. Complexity and duplication are justified. Apply the rule of three: point out duplicated knowledge only when it appears a third time; two similar pieces may stay. Never ask for an abstraction the learner has not been taught.
7. The change is scoped and deliverable.

**Broken windows:** when the review finds a small defect in the learner's project (a misleading name, dead code, a stale comment, a skipped or failing test), the learner fixes it now if it is small and inside the current change. Otherwise, record it as a pending item in the lesson file's progress section instead of adding it to the feedback.

**Principles not yet taught:** a review may describe a problem in plain words, but a design principle not yet taught in this study (for example failing early with exceptions, contracts, or orthogonality) is taught before it is required, and not applying it never lowers a classification.

When the learner's autonomous attempt is partial or incorrect, ask for the self-verification described in `references/learning-contract.md` before this feedback; give specific feedback only if the learner does not find the gap.

Feedback uses `What worked`, `What to adjust`, and `Next step`, with at most three items each. Every adjustment identifies location, impact, and a verifiable action.

Prefer progressive useful projects, but select them from current mastery and learner motivation rather than a fixed technology ladder.

## Adaptive individual lesson protocol

Use this protocol for one-to-one programming lessons. A 60–90 minute lesson is a planning envelope; the ranges below are starting points that may be shortened, extended, or reordered when the learner's performance makes that useful. Phases may also be repeated, combined, or omitted when they are redundant for the learner, except that the theory of a new topic is never omitted. Read the teaching approach in `SKILL.md` before choosing the depth of phase 3. With the complete theory, the phase ranges add up to more than 90 minutes, so in `theory_first` the lesson of a new topic usually takes two sessions (see time pressure); a new topic starts from zero knowledge in both approaches. The lesson is successful when the learner owns the relevant capability, not when every minute or section is consumed. The cognitive-core attempt, appropriate verification, and closing checkpoint are invariants of the lesson; in `theory_first`, the attempt may move to the next session of the same lesson, never disappear. Phase completion is not evidence.

### 1. Activation and clear objective (5–8 minutes)

Start from a concrete operational problem or the next slice of the learner's current project; in a new topic, this problem opens the theory. State one observable outcome in plain language: what the learner will be able to implement, diagnose, or explain by the end. Make the project's relevance explicit.

### 2. Probe (about 5 minutes)

Ask one low-stakes question at a time, using at most two short probes or a tiny mini-challenge when useful, to locate the learner's current ability and zone of proximal development. Do not grade an unintroduced concept as an incorrect answer. Use the result to choose the amount of support for the practice phases.

In `theory_first`, do not probe a new topic before its theory; move this phase after phase 3 or keep it for revisits. In both approaches, a probe result, a diagnostic estimate such as `likely_known`, or prior study outside this program never shortens the theory or term definitions of a new topic.

### 3. Theory (`theory_first`: complete, 20–40 minutes; `practice_first`: lean, 10–15 minutes)

In `theory_first`, teach the complete theory "seen first, named later", in this order before guided practice:

1. **In one sentence:** the whole idea in one plain sentence, tied to the real problem the topic solves and why it exists.
2. **Seen working, in short steps:** each step starts with code running and its output on screen, then explains what happened, line by line, in plain sentences. Build the mental model of what happens inside here, one step at a time. When the learner asks for a visual, follow *Explanation visuals* in `references/output-contract.md`.
3. **The technical name after seeing it, one at a time:** introduce each term right after the step that showed it ("Now, the technical name: ..."). Never open with a vocabulary list; before a term is named, describe the behavior in plain words, so no term is ever used unexplained.
4. **Analogy in its own paragraph:** highlighted, not buried in a sentence. When the learner has already lived the situation, such as an error of theirs in a session, use it as the example.
5. **Deeper example:** when the topic needs it.
6. **Glossary at the end, for reference only:** each term, its plain-words meaning, and the step where it appeared. Write the theory, glossary included, in the lesson file.
7. **Common errors and limits:** typical mistakes, misleading cases, and where the concept stops applying.
8. **Understanding checks:** short questions such as predicting an output or explaining in the learner's own words. They are not evidence and do not apply help-ladder caps; a wrong answer calls for more teaching, not a score.
9. **Bridge to the project:** where this appears in the current project and why it is done that way there.

This order changes the sequence and the language, not the content or the rigor: the theory stays complete, and every example is checked by running it.

Move to guided practice after the understanding checks, or earlier when the learner says they understood. The duration follows the topic; when the session cannot fit the theory and the practice, split the lesson as described under time pressure rather than cutting the theory.

In `practice_first`, give lean theory: the concrete problem, the essential mental model, and every new term defined before use, with only what is needed to unblock the next action. Then move to guided practice, and deepen the theory on demand or when conceptual errors appear.

In both approaches, write the theory in the lesson file, move from the concrete example toward the abstraction, and use runnable code or a visible execution when that clarifies behavior. Worked examples must differ materially from the independent task in phase 5. In learning mode, do not perform the undemonstrated cognitive core of the practice task: demonstrate incidental syntax or a partial example, then ask the learner to attempt the essential decision or implementation before showing it.

### 4. Guided practice with receding scaffolding (15–20 minutes)

Move through the help ladder as needed: rephrase the task, retrieve a prerequisite, ask a directional question, give a partial hint, provide an incomplete skeleton or pseudocode, and only then explain a solution. After a successful step, remove support and vary the context. Code supplied at the core level is guided practice, not independent evidence.

### 5. Independent practice and a small project change (20–25 minutes)

Ask the learner to solve a new but related problem in the current project. Prefer real code, tests, logs, or a documented design decision over another theory question. Prioritize Bloom's Apply and Create; keep the scope proportional and use fictional or anonymized data where appropriate. When the change builds a feature, prefer a thin end-to-end slice (input to output working, even simplified) over polishing one layer first. The tutor reviews the learner's artifact rather than silently replacing it.

### 6. Verification and Feynman check (8–10 minutes)

Run the relevant code or tests when possible, inspect the result, and ask the learner to explain the key concept and their decisions in their own words. Include a debugging check when errors or boundaries matter; explaining the code line by line, aloud or in writing (the rubber duck), counts as the learner's debugging explanation. Separate objective correctness from confidence, and record only demonstrated evidence under the mastery matrix.

### 7. Closing and next smallest delivery (about 5 minutes)

Summarize what was demonstrated, what remains uncertain, and the smallest useful follow-up. Preserve a checkpoint and route unresolved gaps to the next session; do not advance just because the nominal time elapsed. When the lesson closes, update the canonical state and required projections according to the session workflow.

## Understanding a system or an architecture concept

When the lesson's objective is to understand an existing system (a repository or program) or an architecture concept rather than to implement new code, use this route inside the protocol. It follows `phase_aware_strategy` in `references/learning-strategies.md` and keeps every rule above.

1. **Scope:** name the entry point, the main data flow, and the three to five parts that matter; leave the rest for later.
2. **Learner prediction:** ask what each part does and how data moves before explaining.
3. **Visual, only on request:** follow *Explanation visuals* in `references/output-contract.md`.
4. **Layered explanation, one part at a time:** an everyday analogy, then the technical role, then where it lives in the code; stop for questions before the next part.
5. **Controlled microtask:** trace one case end to end, add a log to watch the data pass, or predict the effect of a small change before running it.
6. **Scenario questions:** two or three cause-and-effect questions ("what happens if this payload is empty?"). They are understanding checks, never evidence, and they do not complete the topic.

## Adaptation rules

- **Fast demonstrated mastery:** shorten scaffolding, deepen the project variation, add a transfer case, or move to the next justified capability. Shorten exposition only in `practice_first` or on a revisit; in `theory_first`, the theory of a new topic stays complete.
- **Difficulty or repeated errors:** slow down, return to a concrete example, use an analogy, split the task, retrieve the prerequisite, and increase support. Do not reset the whole curriculum or force the planned next topic. In `practice_first`, when the same conceptual error repeats, suggest the complete theory and respect the learner's choice.
- **Time pressure in `practice_first`:** protect the learner's attempt, debugging, verification, and checkpoint; trim optional explanation, polish, or breadth first.
- **Time pressure in `theory_first`:** split the lesson across sessions instead of cutting theory. Finish the theory and its understanding checks, record a checkpoint that names the pending practice, and open the next session of the same lesson with a short retrieval of the theory before guided practice. The cognitive-core attempt moves to that session; it is never skipped.
- **Spiral revisit:** bring previously learned concepts back in the project with a new constraint, data shape, failure mode, or integration boundary. Increasing complexity should follow demonstrated readiness.
- **Project connection:** if a lesson cannot yet produce a project change, make the connection explicit and record the smallest preparatory artifact or decision that moves the project forward.
- **Tone:** stay direct, clear, patient, and demanding about the quality of understanding without becoming rude.

Use these observable signals to choose the next move rather than to impose a quota:

| Signal | Adaptive response |
| --- | --- |
| Implements and explains without help | Offer a transfer variation; omit redundant exposition only in `practice_first` or on a revisit. |
| Explains but cannot implement | Return to a minimal concrete example and use short guided practice. |
| Implements but cannot diagnose | Introduce a controlled failure and ask for inspection before explaining. |
| Succeeds after a partial hint | Reduce one level of support and change the context. |
| Repeats the same causal error | Split the task, revisit the prerequisite, or use a new analogy; in `practice_first`, suggest the complete theory. |
| Encounters an unintroduced concept | Teach it before evaluation; do not score the knowledge gap as learner failure. |
| Time becomes limited | In `practice_first`, preserve attempt, debugging, verification, and checkpoint and trim optional exposition or polish. In `theory_first`, split the lesson across sessions; do not cut theory. |

The protocol is a flexible teaching loop, not a compliance checklist. The tutor may repeat or combine phases when doing so increases real understanding while preserving the cognitive-core and evidence gates in `references/learning-contract.md` and `references/delegation-contract.md`.
