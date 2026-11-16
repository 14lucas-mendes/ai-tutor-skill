# Educational Output Contract

Every artifact records `artifact_id`, `lesson_id`, pedagogical objective, topic/source IDs, audience level, format, path or URL, accessibility data, and a retrieval or transfer prompt. Every artifact has `evidence_eligible: false`.

When an artifact has `representation.role: "complementary"`, it must reference one primary artifact for the same objective, provide a non-empty `rationale` and `distinct_contribution`, and add information rather than repeat the primary representation.

## Format selection

| Learning need | Preferred output | Local canonical form | Fallback |
| --- | --- | --- | --- |
| Recall atomic facts | Cards | JSON + Markdown | Markdown |
| Check discrimination and misconceptions | Quiz | JSON with separate answer key | Markdown |
| Understand relationships | Concept map | Mermaid `.mmd` | Hierarchical Markdown |
| Compare quantitative values | Chart | CSV + chart specification | Markdown table |
| See a concrete system or object | Didactic image | Image + prompt + alt text | Mermaid or ASCII sketch |
| Combine overview and visual hierarchy | Infographic | Brief + image/PDF | Structured Markdown |
| Teach a sequence to an audience | Slides | Outline + PPTX/PDF when available | Markdown outline |
| Review while away from screen | Audio | File/URL + transcript | Script |
| Explain a visual process | Video | File/URL + transcript | Storyboard |

Do not use a decorative image where a chart is needed. Do not create a chart without identifiable data. Separate objective correctness from visual polish.

## Explanation visuals

An explanation visual helps the learner understand something now, during a lesson or session. It differs from a media artifact, which is made for later review through `references/workflows/media.md`.

- **Only on request.** Create one only when the learner asks for a visual ("show it visually", "draw the flow", "map the project"). Do not create one unprompted, and do not turn the request into a media artifact or an external upload.
- **Format by need:**

  | What the learner wants to understand | Visual | Form |
  | --- | --- | --- |
  | The path data or calls take | Flowchart or sequence diagram | Mermaid |
  | What changes on each loop iteration | Trace table or variable boxes | Table or ASCII |
  | The states something moves through | State diagram | Mermaid |
  | The structure of a project or repository | Node map; selecting a node shows its role in plain words | Interactive HTML |
  | A comparison between options | Side-by-side table | Markdown |

- **One visual per request, never decorative,** always with a short text explanation of what it shows. When the interface cannot render Mermaid, use a table or ASCII; never claim a visual rendered without seeing it.
- **Active validation:** after the visual, ask one to three scenario questions ("what happens if this input is empty?") or ask the learner to complete or redraw part of it. These are understanding checks: not evidence, and no help-ladder caps.
- **Project map:** before showing a map of the learner's own project, ask the learner what each main part does; then show the map and compare. The map describes what exists; in learning mode it never proposes the design decisions the learner must make.
- **Evidence and cognitive core:** a tutor visual is tutor-provided content and never evidence, and it must not show the solution of the independent task. A visual the learner builds, such as a trace table or a diagram, may be evidence under `references/learning-contract.md`.
- **Accessibility:** follow the study's accessibility needs (for example, a dark theme by default when the learner declared light sensitivity); never carry meaning by color alone; give each visual a one-sentence text description.

### Where explanation visuals live

- Inline visuals (Mermaid, tables, ASCII) stay in the conversation and are not saved unless the learner asks.
- An interactive visual is a single HTML file in the study: `<study_root>/media/visuals/<lesson-id>/<slug>.html`.
- When the learner asks to save an inline visual, write its Mermaid or table source into the lesson file's theory section. An interactive visual stays in its file and is linked from the lesson file.
- Saved explanation visuals are lesson material, not media artifacts: they are not registered in `media-index.json` and are never evidence.
- **Keep them small:** prefer text sources (Mermaid, Markdown) to images. An HTML visual is one self-contained file with inline CSS, inline SVG, and plain JavaScript; no bundled libraries, no embedded raster images or base64 data, and about 100 KB at most. Export screenshots or images only when the learner asks.

## Cards and quizzes

Cards in the study registry contain stable `card_id`, front, back, topic/lesson IDs, source IDs, difficulty, spaced-repetition step, due date, objective correctness, confidence, timestamps, and status. Keep one retrievable fact or decision per card. The Markdown deck is generated from `.ai-tutor/cards.json` and must not become a competing source of truth.

Quiz answers and explanations remain hidden until the learner attempts the question. Each distractor targets a documented misconception.

## Accessibility and verification

Images, diagrams, charts, infographics, and slides require alt text. Audio and video require a transcript or equivalent notes. Color cannot be the only carrier of meaning.

Before status becomes `ready`, compare claims and labels with source material. After consumption, ask for a new autonomous explanation or application; that response, not the artifact, may become evidence.
