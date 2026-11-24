# Media Providers: Local, NotebookLM, and Gemini

Always create a local learning pack first. External generation is optional and cannot block study.

## Local video lessons

When the study chooses tutor-made media, a video lesson is rendered on the learner's machine with `scripts/video_lesson.py`; nothing leaves the computer, so no upload consent is needed.

1. **Script.** Write a scene script (`schema_version: 1`) from the lesson's written theory and registered sources only, using the theory's own examples:
   - top level: `title`, `lesson_id`, `source_ids`, an optional `pronunciation` map, and `scenes`;
   - each scene has a `type`, a `title` and `steps`, and each step has a `say` (the narration, in correct spelling);
   - `title` takes a `subtitle`;
   - `list` takes `items`, and each step takes `show`;
   - `flow` takes 1 to 3 `boxes` with `label` and `detail`, and an optional `note`; each step takes `active` and `note`;
   - `code` takes `file`, `language`, `code` and an optional `command`; each step takes `visible`, `highlight`, `output` and `error`;
   - `compare` takes `left`, `right` and `footer`; each step's `show` is `left`, `right` or `footer`;
   - the last scene is `questions`: retrieval questions without answers;
   - in on-screen text (titles, items, boxes, compare lines, notes and footers), wrap inline code in backticks, as in `` `print(__name__)` ``. It is drawn in the monospaced font, because proportional fonts merge `__` into one stroke. Unbalanced backticks fail validation.
2. **Verify before rendering.**
   - Run every code sample and output in the script.
   - Run `python scripts/video_lesson.py validate <script.json>`.
3. **Speech.** Run `speak --voice piper --model <voice.onnx>` (any OS) or `--voice sapi` (Windows). The `pronunciation` map turns terms into their spoken form for the voice only; the subtitles keep the script text.
4. **Render.**
   - `render --audio <dir> --out <lesson.mp4> --frames <dir>` draws dark-theme frames (code highlighted line by line, unhighlighted lines dimmed) and joins them with the speech.
   - The subtitle file (`.srt`) is written next to the video and added as a separate track. It also serves as the transcript.
   - Subtitles are not burned into the image: on-screen text identical to the narration hurts learning (redundancy principle).
5. **Check before delivering.**
   - Inspect key frames for clipped or overlapping text.
   - Run `check <script.json> <lesson.mp4>` to transcribe the speech locally and list words that differ from the script. Recognizer noise (accents, digits) is expected; fix real mispronunciations in the `pronunciation` map.
   - Voice naturalness is judged by the learner.
6. **Register** the item in `media-index.json` with `type: "video"`, `provider: "local"`, the `.srt` as `transcript`, and `evidence_eligible: false`. Keep the MP4 out of version control; the script and subtitles are enough to render it again.

Optional dependencies, imported only when used:
- `piper-tts` and a voice model, for speech;
- `pillow` and `pygments`, for frames;
- `ffmpeg` on `PATH`, for assembly;
- `faster-whisper`, for the speech check.

Without them, the workflow stops at a validated script, which is still a usable storyboard.

## Local audio reviews

An audio review is for screen-free review, made with `scripts/audio_review.py` and the same studio. It is retrieval first, not a replayed lesson.

**Its own script, written for the ear.** Never reuse the video narration: a video narration points at the screen ("this line", "this block"), which the listener does not have. Describe code in words; do not read code symbol by symbol.

**Script format** (`schema_version: 1`, `kind: "audio"`):
- top level: `title`, `lesson_id`, `source_ids`, an optional `pronunciation` map, optional `labels`, and `segments`;
- `labels` localizes the transcript markers: `question`, `answer`, `pause`, `final` and `think`;
- each segment is one of three types:
  - `say`, with `text`;
  - `recall`, with `question`, `pause_seconds` (1 to 30) and `answer`;
  - `questions`, the last segment, with an optional `intro`, `items` (asked without answers) and an optional `outro`;
- at least one `recall` is required.

**Shape:**
- a short opening that tells the learner to answer during the pause;
- 5 to 8 recall blocks: question, a short tone, a pause of about 6 seconds, then a short answer;
- one or two application questions without answers.

Aim for 4 to 6 minutes per part of a lesson. Each answer must come from the written theory or a registered source.

**Commands:**
1. Run `validate`. It fails on a structural error, and it prints a warning when a line points at a screen.
2. Run `render --out <review.mp3> --voice piper --model <voice.onnx>`. It writes the MP3 and a `.txt` transcript with times, tones and pauses.
3. Run `check <script.json> <review.mp3>` to compare the speech with the script.

**Registering:** register the item in `media-index.json` with `type: "audio"`, `provider: "local"`, the `.txt` as `transcript`, and `evidence_eligible: false`. Keep the MP3 out of version control.

**What it is not:** an audio review does not record retrieval attempts. Recall that must count still happens in cards or in a session.

### Studio environment

Install the optional dependencies in one virtual environment of their own (the "studio"), outside the study and outside any synced folder (Google Drive, Dropbox, OneDrive), so the study stays free of binaries. The versions are pinned in `requirements-video.txt` at the skill root.

```text
python -m venv <studio>/.venv
<studio>/.venv/Scripts/python -m pip install -r <skill_root>/requirements-video.txt   (bin/python on Linux and macOS)
<studio>/.venv/Scripts/python -m piper.download_voices --download-dir <studio>/voices <voice>
```

Then run `<studio>/.venv/Scripts/python -I <skill_root>/scripts/video_lesson.py ...`, passing `--model <studio>/voices/<voice>.onnx` to `speak`. A small launcher script in the studio folder may fill in the interpreter and the voice. The speech check downloads its recognition model (`small`, about 460 MB) to the user's cache on first use.

Before rendering in a new session, confirm the studio is ready:
- `validate` passes on the script;
- `ffmpeg -version` runs.

## Capability order

1. Produce local sources, prompts, manifests, and fallbacks.
2. Determine whether an authenticated browser and the requested feature are available.
3. List the exact files and request consent immediately before upload.
4. If consented, use the existing authenticated session; never request, store, or type credentials.
5. Record generated URLs/downloads without publishing or changing sharing settings.
6. Verify the artifact against sources and preserve a transcript or accessible alternative.

## Provider split

NotebookLM is the grounded provider for Studio artifacts: cards, quizzes, mind maps, study guides, audio overviews, video overviews, infographics, and slide decks when available to the account.

Notebooks in Gemini may be used to chat with the synchronized notebook and use broader Gemini tools. Gemini chat can include web/tool context; it is not equivalent to NotebookLM's source-only grounding. Studio artifacts such as audio, video, infographics, and slide decks must be requested in NotebookLM.

Feature availability, quotas, language support, and account rules may change. Detect them at use time and fall back instead of claiming generation succeeded.

## Privacy gate

Do not upload credentials, personal identifiers, restricted coursework, proprietary material, or copyrighted content without clear rights and specific consent. Generating an artifact does not authorize public sharing. Sharing is a separate external action.

## Learning pack

`scripts/create_learning_pack.py` creates:

```text
media/<lesson-id>/notebooklm/
├── source-pack.md
├── prompts.md
├── manifest.json
└── exports/
```

The manifest begins with consent false. The manual fallback supplies the same source pack and prompts when browser automation is unavailable.

Official capability references:

- https://support.google.com/notebooklm/answer/16164461
- https://support.google.com/notebooklm/answer/16215270
- https://support.google.com/notebooklm/answer/17003757
- https://support.google.com/notebooklm/answer/16212820
- https://support.google.com/notebooklm/answer/16454555
