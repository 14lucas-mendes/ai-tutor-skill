# Media Workflow

Leia `references/learning-strategies.md` antes de combinar representações no mesmo objetivo.

Read `references/output-contract.md` and `references/media-providers.md`. This workflow is for artifacts made for later review; a visual requested to understand something during a lesson follows *Explanation visuals* in `references/output-contract.md` instead.

Choose format from the learning need: cards for recall, quizzes for discrimination, maps for relationships, charts for quantitative comparison, images for concrete visualization, infographics for overview, slides for teaching sequence, audio for screen-free review, and video for visual process.

Apply `representational_complementarity` when combining formats. Mark the primary artifact and at most one complementary artifact with a distinct contribution and rationale; do not generate redundant media.

When the learner chose tutor-made media (made locally instead of by NotebookLM), render a video lesson locally with `scripts/video_lesson.py`, following *Local video lessons* in `references/media-providers.md`. The video is offered when parts of a lesson close, not generated unasked. It never reveals the solution of an open task, and it ends with retrieval questions without answers. For screen-free review, offer with it an audio review made with `scripts/audio_review.py` (*Local audio reviews* in the same reference). The video shows the code; the audio asks for recall. When the learner prefers a retelling because retrieval already happens in cards, the audio is a narrated summary (`"style": "summary"`, same reference).

Otherwise, create the local learning pack first with `scripts/create_learning_pack.py`. Validate source IDs, prompts, accessibility fields, and `evidence_eligible: false`.

For NotebookLM/Gemini, detect an already authenticated browser and feature availability. Immediately before upload, list exact files and obtain specific consent. Without capability or consent, provide the local pack and manual steps. Never claim an external artifact exists until its URL or downloaded file is observed.

After generation, verify claims against sources and ask for a new autonomous explanation or application.
