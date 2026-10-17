# Lesson Workflow

Select the next `planned` or resumable `in_progress` lesson whose prerequisites are satisfied. Do not infer eligibility from the last session alone.

Create `lessons/<sequence>-<slug>.md` with a header (lesson ID, observable objective, prerequisites, verified sources) and three sections whose headings use the study language:

1. **Theory:** the material defined by the teaching approach in `SKILL.md` — complete in `theory_first` (problem and why, how it works, vocabulary, examples, common errors and limits, understanding checks, project bridge), lean in `practice_first` (the concrete problem, the essential mental model, and every new term). Write it before practice so the learner can reread it without the chat. It is tutor-provided content and never evidence.
2. **Practice plan:** scaffold options, independent-task variants, expected errors, evidence criteria, and state update instructions. Worked examples in the theory must differ materially from these independent tasks.
3. **Progress:** checkpoint, demonstrated evidence with IDs, and what remains.

A topic counts as taught once its lesson file contains written theory; until then it is new and starts from zero knowledge, whatever the diagnostic estimated. When a later session continues the lesson, keep the theory, deepen it when needed, and update the progress section.

For programming, read `references/programming.md` and treat the lesson as an adaptive set of teaching options, not a sequence that must be consumed. Add the project anchor and a possible concrete example to the header and plan. Select, combine, revisit, or omit the practice-plan components according to observed learner performance; the theory of a new topic is never omitted.

Transfer is required only when the targeted mastery level requires it under the learning contract. A solution supplied by the tutor remains study material. Complete the lesson only when its own criteria and evidence are present.
