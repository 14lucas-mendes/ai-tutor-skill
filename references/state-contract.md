# State Contract v2 (diagnostic extension)

Every productive JSON document has `schema_version: 2`. IDs are non-empty, globally unique strings with semantic prefixes such as `study_`, `topic_`, `session_`, `evidence_`, `lesson_`, `card_`, `weak_`, `project_`, and `media_`.

## Canonical files

`study-config.json` stores every setup answer: study ID, topic, goal, deadline, weekly hours, preferred times, initial level, language, accessibility needs, source policy, and revocable external consents.

`state.json` contains `revision`, `updated_at`, `topics`, `evidences`, `sessions`, `lessons`, `weak_points`, `projects`, `next_focus`, and `diagnostics`. Older valid V2 states may omit `diagnostics` until the idempotent upgrade migration runs.

`cards.json` is the canonical card registry. It contains `study_id` and `cards`; each card has a stable `card_id`, optional topic/lesson links, source IDs, front/back, difficulty, spaced-repetition step, due date, objective correctness, confidence, and status. The generated `flashcards.md` file is only a readable projection.

`sources.json` is the canonical source registry. Every source records `source_id`, title, author or institution, direct URL or bibliographic identifier, publication date when available, access date, source type, linked lesson/topic IDs, and an authority reason. Learning packs may copy source snapshots, but the study registry remains the source of truth.

Topics contain `topic_id`, `name`, `mastery`, `retention`, `status`, `last_practice`, and `evidence_ids`. Status is `not_started` for 0, `in_progress` for 20–60, and `mastered` for 80–100.

Topics may contain a `diagnostic` projection with the latest estimate, confidence, and `diagnostic_id`. This projection is advisory and never changes mastery or evidence requirements.

`diagnostics` is an append-only list of diagnostic runs. Each run records its objective, scope, status, timestamps, observations, summary, and recommended entry topic. See `references/diagnostic-contract.md` for the observation shape and allowed values.

Weak points contain `weak_point_id`, optional `topic_id`, `category`, `cause`, `supporting_evidence_ids`, `entered_at`, `exit_condition`, and `status`. Categories are `conceptual`, `procedural`, `application`, `precision`, or `execution`; a v1 migration may temporarily use `category: "unclassified"` only with `migration_pending_classification: true`.

Evidences contain `evidence_id`, `topic_id`, `session_id`, `kind`, `autonomous`, `transfer`, `context`, `recorded_at`, `reference`, `result`, and `error`. `reference.type` cannot be `media`.

`media-index.json` contains artifact metadata: IDs, type, provider, source IDs, pedagogical objective, local path or URL, status, dates, verification, accessibility, and `evidence_eligible: false`.

Canonical JSON updates must use the sibling lock/CAS helper (`scripts/state_io.py`) when more than one process may write. A successful update increments `revision`; a stale expected revision is rejected without changing the file.

## Sessions

Allowed transitions:

```text
in_progress → completed
in_progress → interrupted
interrupted → resumed
resumed → completed
resumed → interrupted
```

Resume the most recent `in_progress` session; otherwise resume the most recent `interrupted` session with `resumable: true`. Completed sessions require `ended_at` and cannot resume.

## Lessons

Lesson status is `planned`, `in_progress`, `blocked`, `completed`, or `archived`. Sessions and lessons have a many-to-many relationship. Advancing depends on lesson status and evidence, never only on session status.

## Validation

Run `python -m scripts.validate_study <study_root>` (or the direct script entrypoint) after changes. Run `python -m scripts.projections <study_root>` only when you intentionally want to rewrite the Markdown projections from canonical JSON. Never invent dates, evidence, IDs tied to nonexistent entities, or missing setup answers.
