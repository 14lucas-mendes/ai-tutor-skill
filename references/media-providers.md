# Media Providers: Local, NotebookLM, and Gemini

Media is made either locally by the tutor (a video lesson or an audio review, below) or by an external provider (NotebookLM or Gemini). For an external provider, always create a local learning pack first (*Learning pack*). External generation is optional and cannot block study.

## Local video lessons

When the learner chooses tutor-made media (made locally instead of by NotebookLM), a video lesson is rendered on the learner's machine with `scripts/video_lesson.py`; nothing leaves the computer, so no upload consent is needed.

1. **Script.** Write a scene script (`schema_version: 1`) from the lesson's written theory and registered sources only, using the theory's own examples:
   - top level: `title`, `lesson_id`, `source_ids`, an optional `pronunciation` map, and `scenes`;
   - each scene has a `type`, a `title` and `steps`, and each step has a `say` (the narration, in correct spelling);
   - `title` takes a `subtitle`;
   - `list` takes `items`, and each step takes `show`;
   - `flow` takes 1 to 3 `boxes` with `label` and `detail`, and an optional `note`; each step takes `active` and `note`;
   - `code` takes `file`, `language`, `code` and an optional `command`; each step takes `visible`, `highlight`, `output` and `error`;
   - `compare` takes `left`, `right` and `footer`; each step's `show` is `left`, `right` or `footer`;
   - `ide` shows code being typed in an editor and run in a terminal (see *The `ide` scene* below);
   - the last scene is `questions`: retrieval questions without answers;
   - in on-screen text (titles, items, boxes, compare lines, notes and footers), wrap inline code in backticks, as in `` `print(__name__)` ``. It is drawn in the monospaced font, because proportional fonts merge `__` into one stroke. Unbalanced backticks fail validation.
2. **Verify before rendering.**
   - Run every code sample and output in the script.
   - Run `python scripts/video_lesson.py validate <script.json>`.
3. **Speech.** Run `speak --voice piper --model <voice.onnx>` (any OS) or `--voice sapi` (Windows). The `pronunciation` map turns terms into their spoken form for the voice only; the subtitles keep the script text. A cloud voice is also available (see *Cloud voice* below).
4. **Render.**
   - `render --audio <dir> --out <lesson.mp4> --frames <dir>` draws dark-theme frames (code highlighted line by line, unhighlighted lines dimmed) and joins them with the speech.
   - The video is 1920×1080 at 30 frames per second.
   - A `WARNING: <step> has more than its narration can show` line means an `ide` step had to show its code line by line, or its terminal at once. Split that step and render again.
   - The subtitle file (`.srt`) is written next to the video and added as a separate track. It also serves as the transcript.
   - Subtitles are not burned into the image: on-screen text identical to the narration hurts learning (redundancy principle).
5. **Check before delivering.**
   - Inspect key frames for clipped or overlapping text.
   - Run `check <script.json> <lesson.mp4>` to transcribe the speech locally and list words that differ from the script. Recognizer noise (accents, digits) is expected; fix real mispronunciations in the `pronunciation` map.
   - Voice naturalness is judged by the learner.
6. **Register** the item in `media-index.json` with `type: "video"`, `provider: "local"`, the `.srt` as `transcript`, and `evidence_eligible: false`. Keep the MP4 out of version control; the script and subtitles are enough to render it again.

### The `ide` scene

Use it when the lesson shows code running: the code is typed in an editor, letter by letter, in time with the narration, and then it runs in a terminal below. Use `code` to show a file without typing.

**Scene fields:**
- `title`, drawn small so the editor has room;
- `files`: 1 to 4 files, each with `name`, `language` and `code`. Each file is a tab.

**Step fields** (all optional except `say`):
- `file`: the active tab. Without it, the tab stays the same; the first step starts on the first file.
- `type`: how many lines of the active file are visible at the end of the step. The missing lines are typed during the narration.
- `show`: like `type`, but the lines appear at once. A step uses `type` or `show`, never both. Lines never disappear: the count never goes down within a file.
- `highlight`: lines highlighted at the end of the step; the others are dimmed.
- `terminal`: lines added to the terminal, in order. Each line has exactly one key:
  - `cmd`: a command, typed after `$`;
  - `out`: program output, shown at once;
  - `err`: error output, shown at once in red;
  - `in`: what the user types after the last `out` (the prompt of an `input()`), on the same line.
- `clear_terminal`: `true` clears the terminal before this step's lines. The terminal starts empty in each scene.

Each terminal text is one line: write one `out` per line of output.

**Room on screen:** the editor shows 11 lines and the terminal 4. A longer file scrolls to keep the highlighted lines in view, or the last line when nothing is highlighted; the terminal keeps its last lines.

**Pacing:** everything that moves in a step ends by 75% of its narration. Typing runs at one speed for the whole step, between about 8 and 60 characters per second. Each `out` and `err` appears 0.3 s after the line before it. Afterwards the cursor blinks.

**Writing rule: one idea per step.** The narration talks about what appears in that step, not what comes next. When the narration announces the output ("it prints 212.0"), type the code in one step and run it in the next, so the output never appears after the narration has said it.

```json
{"type": "ide", "title": "Who imports",
 "files": [{"name": "conv.py", "language": "python", "code": "def f(c):\n    return c * 9 / 5 + 32"},
           {"name": "use.py", "language": "python", "code": "import conv\nprint(conv.f(100))"}],
 "steps": [{"file": "conv.py", "show": 2, "say": "The module we already wrote."},
           {"file": "use.py", "type": 2, "highlight": [1], "say": "A second file imports it."},
           {"terminal": [{"cmd": "python use.py"}, {"out": "212.0"}], "say": "Running it prints 212.0."}]}
```

Optional dependencies, imported only when used:
- `piper-tts` and a voice model, for speech;
- `pillow` and `pygments`, for frames;
- `ffmpeg` on `PATH`, for assembly;
- `faster-whisper`, for the speech check.

Without them, the workflow stops at a validated script, which is still a usable storyboard.

## Local audio reviews

An audio review is for screen-free review, made with `scripts/audio_review.py` and the same studio. By default it is retrieval first, not a replayed lesson; a narrated summary is the exception the learner may choose (below).

**Its own script, written for the ear.** Never reuse the video narration: a video narration points at the screen ("this line", "this block"), which the listener does not have. Describe code in words; do not read code symbol by symbol.

**Script format** (`schema_version: 1`, `kind: "audio"`):
- top level: `title`, `lesson_id`, `source_ids`, an optional `style` (`recall`, the default, or `summary`), an optional `pronunciation` map, optional `labels`, and `segments`;
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
2. Run `render --out <review.mp3> --voice piper --model <voice.onnx>`. It writes the MP3 and a `.txt` transcript with times, tones and pauses. The cloud voice options below work here too.
3. Run `check <script.json> <review.mp3>` to compare the speech with the script.

**Registering:** register the item in `media-index.json` with `type: "audio"`, `provider: "local"`, the `.txt` as `transcript`, and `evidence_eligible: false`. Keep the MP3 out of version control.

**What it is not:** an audio review does not record retrieval attempts. Recall that must count still happens in cards or in a session.

**Narrated summary (`"style": "summary"`).** When the learner asks for a retelling instead of recall, because retrieval already happens in cards, set `style` to `summary` (the default is `recall`):
- the script has only `say` segments, plus an optional closing `questions` segment;
- `recall` segments are rejected, and no tone or pause is played;
- it is still written for the ear, from the written theory or a registered source, with the same commands, check and registration;
- aim for 4 to 6 minutes per part of a lesson.

Offer the recall style first; use the summary only when the learner chooses it. Neither style is evidence.

### Cloud voice (OpenRouter)

When the learner chooses a cloud voice, `speak` (video) and `render` (audio review) take `--voice openrouter`. Any OpenRouter speech model that returns WAV works, for example `google/gemini-2.5-pro-tts` with the voice `Charon`.

- **Consent, every time.** The lesson text leaves the computer: it goes to OpenRouter and to the model's provider. Before each render, show the learner what will be sent and ask. Pass `--external-ok` only after the learner says yes; without it, the command refuses. Consent for one lesson part does not cover the next.
- **Options:**
  - `--cloud-model` and `--cloud-voice`;
  - `--instructions`, an optional speaking style, such as "Brazilian Portuguese, calm teacher";
  - `--fallback-model`, the Piper `.onnx` file;
  - `--cache`, by default `~/.cache/ai-tutor/tts`.
- **Defaults** may come from environment variables, so a launcher can set them once: `AI_TUTOR_PIPER_MODEL` (for `--model` and `--fallback-model`), `AI_TUTOR_CLOUD_MODEL`, `AI_TUTOR_CLOUD_VOICE` and `AI_TUTOR_CLOUD_INSTRUCTIONS`.
- **Key:** the `OPENROUTER_API_KEY` environment variable. The learner stores it in the studio's `.env`, never in the study. The tutor never opens or prints that file.
- **One voice per lesson:** if any request fails (network, credit, model), every text is spoken again with Piper from `--fallback-model`, with a `WARNING`. Without a fallback, the command stops with the error.
- **Cache:** each generated line is cached by model, voice, instructions and text, so rendering again sends nothing and costs nothing.
- **Pronunciation:** the cloud voice reads the original text. `pronunciation` stays for local voices. An optional `pronunciation_cloud` map fixes terms the cloud voice gets wrong.
- **Registering:** in `media-index.json`, use `provider: "openrouter"` and name the model and voice in the output note.

### Studio environment

Install the optional dependencies in one virtual environment of their own (the "studio"), outside the study and outside any synced folder (Google Drive, Dropbox, OneDrive), so the study stays free of binaries. The versions are pinned in `requirements-video.txt` at the skill root.

On Windows, keep the studio out of `AppData`. The Claude desktop app virtualizes `AppData\Local`: what it writes there lands in a private copy that the learner's own terminals do not see. A folder such as `C:\Users\<user>\ai-tutor-studio` avoids this.

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
