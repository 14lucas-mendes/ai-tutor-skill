# Setup Workflow

Read `references/architecture.md`, `references/state-contract.md`, and `references/learning-contract.md`.

Collect only persisted fields: topic, concrete goal, initial level, weekly hours, preferred times, deadline, language, accessibility needs, source preferences, teaching approach, and explicit study root. Accept one complete answer or ask one missing field at a time.

Ask for the teaching approach with one line per option, and persist it as `teaching_policy.approach`:

- `theory_first` (default): each new topic starts with a complete lesson from zero — why, how it works, vocabulary, and examples — and practice in the project comes after.
- `practice_first`: lean theory with every term defined, then practice soon; the theory deepens on demand or when conceptual errors appear.

When the learner does not choose, use `theory_first`.

Summarize the proposed configuration and obtain confirmation before writing. Run `scripts/init_study.py` using the absolute study root and structured JSON. Never overwrite an existing `.ai-tutor/`; use migration when v1 state exists.

After initialization, offer `/diagnostic` as an optional next step. If accepted, run the diagnostic workflow before finalizing the starting order; if declined, create the initial curriculum with observable outcomes as before. In both cases, do not mark evidence or mastery from setup or diagnosis. Validate the study and show created paths.
