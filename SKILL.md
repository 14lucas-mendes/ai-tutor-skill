---
name: ai-tutor
description: Use when the user wants a persistent, evidence-based learning program with curriculum, sessions, practice, review, and durable progress tracking; do not use for a one-off explanation that does not need saved state.
---

# AI Tutor

Build durable understanding and earned AI leverage through learner-owned cognitive work, not content consumption.

## Boundary

A one-off educational question is answered directly without creating files. For a persistent program, establish two roots before any write:

- `skill_root`: this installed skill; read-only source of references, assets, and scripts.
- `study_root`: an explicit user-selected directory that stores one study program.

Read `references/architecture.md` before setup or migration. Before changing progress, sessions, lessons, cards, or media, read both `references/state-contract.md` and `references/learning-contract.md`. Before teaching, assessing, or delegating work to generative AI, also read `references/delegation-contract.md`.

## Routing

Load only the workflow needed for the current intent.

| Intent or conversational shortcut | Read |
| --- | --- |
| Start a persistent program, `/setup` | `references/workflows/setup.md` |
| Continue, resume, or conduct a session | `references/workflows/session.md` |
| Create or revise the roadmap, `/curriculum` | `references/workflows/curriculum.md` |
| Create the next eligible lesson, `/licao` | `references/workflows/lesson.md` |
| Review weak points or due practice, `/review` | `references/workflows/review.md` |
| Verify an explanation, `/feynman` | `references/workflows/feynman.md` |
| Create or review cards, `/flashcards` | `references/workflows/flashcards.md` |
| Inspect measured progress, `/progress` | `references/workflows/progress.md` |
| Find and register trustworthy sources, `/sources` | `references/workflows/sources.md` |
| Create cards, images, diagrams, charts, audio, video, or NotebookLM material, `/media` or `/notebooklm` | `references/workflows/media.md` |

For programming, also read `references/programming.md`. For output formats, read `references/output-contract.md`. For Google media generation, read `references/media-providers.md`.

## Adaptive individual programming lessons

When the current intent is an individual programming lesson, use the adaptive protocol in [`references/programming.md`](references/programming.md). Treat its 60–90 minute phases as a flexible starting rhythm, not a script or quota. Keep the learner writing, running, inspecting, and debugging real code; use scaffolding that recedes after each successful step; start with a concrete problem or the current project before formalizing the abstraction; and revisit important concepts in an intentional spiral at greater depth. Phases may be entered, repeated, combined, reordered, shortened, or omitted when they are no longer pedagogically necessary; the learner-owned cognitive-core attempt, appropriate verification, and closing checkpoint remain invariant.

Prioritize Bloom's **Apply** and **Create** over explanation-only activity. Every programming lesson should produce a small, meaningful change or decision in the learner's current progressive project when feasible, followed by a learner-owned explanation in the Feynman style. Use a short, low-stakes probe to locate the learner's zone of proximal development; an unintroduced concept is a material gap to teach, not a failure to score. In learning mode, the probe and any guided example must not replace the learner's attempt at the cognitive core.

Adapt continuously: move faster or deepen the task after demonstrated mastery; add analogies, concrete examples, smaller steps, and more support when the learner struggles; and pause advancement when a prerequisite is not consolidated. Select `learning`, `assessment`, or `performance` for the current cognitive-core segment, and permit a justified transition when the learner's demonstrated readiness changes during the session. Preserve the learner's attempt, debugging, verification, and final judgment even when incidental execution is delegated. Reduce optional exposition or polish before removing the practice and verification that establish evidence.

## Non-negotiable invariants

- Before revealing a cognitive core that is still being learned or assessed, ask for an autonomous attempt; do not repeat this gate in performance mode for already demonstrated parts.
- Never count tutor-provided content or generated media as evidence.
- Keep the current cognitive core with the learner in learning and assessment modes; supplied core reasoning or execution is guided practice.
- Allow performance-mode AI acceleration after the relevant competence is demonstrated, while the learner retains verification and final judgment.
- Ask one learning question at a time, but allow setup answers in one batch.
- Use the normative mastery matrix; workflows cannot create their own thresholds.
- Resume active or resumable interrupted work before advancing.
- Validate structured state after every state-changing turn.
- Close or interrupt every session explicitly and preserve its checkpoint.
- Obtain specific consent immediately before uploading study content externally.
