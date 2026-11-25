# Course Workflow

The course is an optional, readable projection of a study: one lesson page per completed lesson (or part of one), written for any reader, to consult and review. It exists only when `study-config.json.course_policy` is present; `course_policy.path` names the course folder, relative to the study root. Without it, never create a course.

The course is tutor-provided material. It is never evidence, never changes mastery, and never replaces the lesson file, which stays the source of truth.

## When to write a lesson page

- When a lesson becomes `completed` and the study has `course_policy`, write its page in the same closing turn. One lesson may become more than one page when its theory has independent parts.
- A lesson that is not `completed` never becomes a page.
- `/course` may also be used to write a missing page for a lesson already completed, to fix a page, or to run the checker.

## Structure of a lesson page

Write in the study language. Keep this order; headings follow the language:

1. **Header:** title, then in the first 10 lines the source lesson ID in backticks (for example, ``origin: `lesson_15-logic` ``), suggested time, and prerequisites with links to earlier pages.
2. **Objectives:** what the reader can do at the end, as observable actions.
3. **Theory:** rewritten from the lesson's `## Theory` section for any reader, in the theory format of `SKILL.md` (seen first, named later), with every example checked by running it.
4. **Exercises:** the understanding checks and suitable practice turned into exercises, each answer inside a `<details>` block so the reader attempts first.
5. **One-page summary:** for later review.
6. **Supporting material:** links only (official documentation, sources registered in `sources.json`, and other materials the study already lists).
7. **Bridge to the project:** where this appears in the study's project, described for any reader.

Then update the course index (`README.md` in the course folder): the page link, its source lesson, and its status.

## Rules

- **Nothing personal:** no evidence, mastery, weak points, session names or IDs, learner errors, dates of the learner's sessions, or phrases such as "you got X wrong". The page speaks to any reader.
- **Fictional data only** in examples and exercises.
- **Third-party material as links:** do not copy courses, videos, or books; cite them.
- **Check before closing:** run `python -m scripts.course_check <study_root>` from the skill root and fix every error before closing the turn. The checker confirms that each page cites a completed source lesson, hides answers in balanced `<details>` blocks, contains no real study ID, and has working relative links. It does not judge the writing; the rules above still apply.
