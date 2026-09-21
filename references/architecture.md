# Architecture and Roots

## Root contract

`skill_root` is the directory containing the installed `SKILL.md`. Treat it as read-only. Resolve packaged files from it, never from the current shell directory.

`study_root` is the absolute directory explicitly selected by the user. One `study_root` contains one learning program. Do not guess it when more than one plausible directory exists.

Initialize with `python <skill_root>/scripts/init_study.py --study-root <study_root> --config-json <json>`.

## Study layout

```text
<study_root>/
├── .ai-tutor/
│   ├── study-config.json
│   ├── state.json
│   ├── media-index.json
│   ├── cards.json
│   ├── sources.json
│   └── migrations/
├── curriculum.md
├── session-log.md
├── flashcards.md
├── lessons/
├── media/
└── projects/
```

Structured files are canonical. Markdown is a readable projection and carries stable IDs from structured state.

## Safe update protocol

1. Read and validate all canonical JSON.
2. Prepare the complete next revision in memory.
3. Check IDs, references, transitions, and learning invariants.
4. Write a temporary file beside each destination.
5. Replace canonical files atomically.
6. For concurrent writers, acquire the sibling `.lock` through the `scripts/state_io.py` helpers with an expected `revision` (CAS); abort on `RevisionConflict`.
7. Update Markdown projections explicitly.
8. Run `python -m scripts.validate_study <study_root>` (or `python <skill_root>/scripts/validate_study.py <study_root>`).

Markdown projections are deliberately explicit: run `python -m scripts.projections <study_root>` after a canonical update when the readable `flashcards.md` or `session-log.md` should change. Initialization never overwrites an existing projection.

Do not leave a partially updated state. If validation fails, report the exact invariant and retain the last valid revision.

## Portability

Scripts require Python 3.11+ and the standard library. Describe operations independently of shell; command examples may be adapted to PowerShell or POSIX shells.
