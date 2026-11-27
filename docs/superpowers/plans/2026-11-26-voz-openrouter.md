# Voz pela nuvem (OpenRouter): plano de construção

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** a voz `openrouter` nos dois geradores de fala, com consentimento explícito, cache, pronúncia própria e a Piper de reserva.

**Spec:** `docs/superpowers/specs/2026-11-26-voz-openrouter-design.md`

## Global Constraints

- `cloud_voice.py` usa só a biblioteca padrão (`urllib`, `hashlib`, `json`). O CI roda sem rede e sem as dependências do estúdio: todo teste de nuvem usa um `opener` falso.
- Endpoint: `POST https://openrouter.ai/api/v1/audio/speech`, com o cabeçalho `Authorization: Bearer <OPENROUTER_API_KEY>` e o corpo `{"model", "input", "voice", "response_format": "wav", "instructions"?}`. A resposta 200 é o WAV cru; um erro é JSON.
- Mensagens em inglês, como no resto dos scripts. A chave nunca aparece em mensagem, log ou exceção.

## Review Focus

1. A resposta 200 sem cabeçalho WAV (por exemplo, um JSON de erro com status 200) não entra no cache: vira erro e aciona a reserva.
2. Uma falha no meio de um vídeo não deixa trechos da nuvem misturados com a Piper na pasta de saída.
3. A chave ausente, com `--voice openrouter`, dá uma mensagem clara, sem traceback de `KeyError`.
4. Os roteiros antigos, sem `pronunciation_cloud`, continuam validando.
5. O cache fica separado por modelo, voz e instruções: mudar a voz não reaproveita a fala antiga.

---

### Task 1: `cloud_voice.py`

**Produces:**
- `@dataclass(frozen=True) class CloudOptions: model: str; voice: str; instructions: str = ""; cache_dir: Path = DEFAULT_CACHE; external_ok: bool = False`
- `class CloudVoiceError(RuntimeError)`
- `def cache_key(text: str, options: CloudOptions) -> str`, o sha256 de um JSON ordenado com o modelo, a voz, as instruções e o texto
- `def openrouter_wav(text: str, options: CloudOptions, api_key: str, opener=urllib.request.urlopen) -> bytes`
- `def speak_cloud(paths: list[Path], texts: list[str], options: CloudOptions, api_key: str, opener=...) -> list[Path]`: ou grava todos os WAV, ou levanta `CloudVoiceError` sem deixar nada em `paths`

**Testes** (`tests/test_cloud_voice.py`, com um opener falso que registra os pedidos):
- `test_request_has_model_voice_wav_and_bearer`;
- `test_instructions_are_sent_only_when_given`;
- `test_http_error_becomes_cloud_voice_error_without_key`: o texto da exceção não contém a chave;
- `test_non_wav_body_is_rejected` (Review Focus 1);
- `test_cache_avoids_second_request` e `test_cache_key_changes_with_voice` (Review Focus 5);
- `test_partial_failure_leaves_no_outputs` (Review Focus 2).

### Task 2: fala com reserva nos dois scripts

**Produces** em `video_lesson.py`:
- `VOICES = {"piper", "sapi", "openrouter"}`;
- `def speak_script_texts(paths: list[Path], texts: list[str], script: dict, *, voice: str, model: Path | None, cloud: CloudOptions | None = None, fallback_model: Path | None = None, env: Mapping[str, str] = os.environ, opener=None) -> str`, que devolve a voz usada (`"openrouter"` ou `"piper"`). Ele aplica `pronunciation_cloud` na nuvem e `pronunciation` na Piper, exige `cloud.external_ok` e a chave no `env`, e na falha avisa em stderr e refaz tudo com a Piper, se houver `fallback_model`.
- `synthesize` e o `render_audio` do `audio_review.py` passam a usar essa função.
- Os validadores de vídeo e de áudio aceitam `pronunciation_cloud`, com a mesma regra do `pronunciation`.
- CLI: `--cloud-model`, `--cloud-voice`, `--instructions`, `--external-ok`, `--fallback-model` e `--cache`, com padrões vindos de `AI_TUTOR_PIPER_MODEL`, `AI_TUTOR_CLOUD_MODEL`, `AI_TUTOR_CLOUD_VOICE` e `AI_TUTOR_CLOUD_INSTRUCTIONS`.

**Testes:**
- `test_openrouter_needs_external_ok`;
- `test_missing_key_is_a_clear_error` (Review Focus 3);
- `test_cloud_uses_cloud_pronunciation`;
- `test_failure_falls_back_to_piper_for_all`, com a Piper trocada por uma função falsa por injeção;
- `test_old_script_without_cloud_map_validates` (Review Focus 4);
- `test_cli_defaults_come_from_env`.

### Task 3: documentação, piloto e PR

- Atualizar `references/media-providers.md` (*Local video lessons*, *Local audio reviews* e *Studio environment*) e as docstrings.
- No estúdio do aluno (fora do repositório): os atalhos passam a carregar o `.env`.
- Piloto real com o consentimento do aluno: o vídeo da parte 1 com a voz `openrouter`.
- Revisão final e PR.
