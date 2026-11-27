# Voz pela nuvem (OpenRouter) com a Piper de reserva: desenho curto

- **Data:** 2026-11-26. Aprovado pelo aluno no chat ("Aprovo").
- **Código afetado:** `scripts/video_lesson.py`, `scripts/audio_review.py`, um módulo novo `scripts/cloud_voice.py` (só biblioteca padrão), os testes e `references/media-providers.md`.

## Intenção

O aluno ouviu amostras e escolheu o **Gemini 2.5 Pro TTS**, voz `Charon`, pelo OpenRouter (pago com os créditos dele), como voz principal das videoaulas e dos resumos em áudio. A Piper fica de reserva. Antes, ele preferiu uma voz principal só, e não uma fila com a ElevenLabs gratuita, para o curso não misturar vozes.

## O que muda

1. **Voz `openrouter`** no `speak` (vídeo) e no `render` (áudio de revisão), com `--cloud-model` (por exemplo `google/gemini-2.5-pro-tts`), `--cloud-voice` (por exemplo `Charon`) e `--instructions`, opcional, com o estilo da fala. Serve para qualquer modelo de voz do OpenRouter que entregue WAV.
2. **Chave fora do código:** a variável de ambiente `OPENROUTER_API_KEY`. Os atalhos do estúdio a carregam do `.env`.
3. **Consentimento explícito:** sem `--external-ok`, a voz `openrouter` se recusa a enviar. O tutor só passa essa opção depois do "sim" do aluno, como a skill exige para todo envio externo.
4. **Uma voz só por mídia:** se qualquer trecho falhar (rede, crédito, modelo), todo o vídeo ou áudio é refeito com a Piper (`--fallback-model`), com um aviso. Sem modelo de reserva, o erro é mostrado.
5. **Cache:** cada fala gerada na nuvem é guardada pelo hash de (modelo, voz, instruções, texto), numa pasta de cache, por padrão `~/.cache/ai-tutor/tts`. Renderizar de novo não reenvia nem paga outra vez.
6. **Pronúncia:** a nuvem lê o texto original. O mapa `pronunciation` continua só para a Piper. Um roteiro pode ter `pronunciation_cloud`, um mapa só para a nuvem.
7. **Padrões por variável de ambiente:** `AI_TUTOR_PIPER_MODEL` (o `.onnx` da Piper, usado em `--model` e `--fallback-model`), `AI_TUTOR_CLOUD_MODEL`, `AI_TUTOR_CLOUD_VOICE` e `AI_TUTOR_CLOUD_INSTRUCTIONS`. O estúdio guarda esses valores no `.env` e os atalhos não precisam mais acrescentar `--voice piper --model` à linha de comando.
8. **Testes** com o OpenRouter simulado, sem rede. **Documentação:** a voz nova, o consentimento, o cache, a reserva e o aviso para nunca deixar o estúdio em `AppData` no Windows (o app do Claude grava lá numa pasta só dele).

## Caminhos considerados

- **A. Voz `openrouter` genérica** (escolhido): um caminho para qualquer modelo de voz do OpenRouter, pago com os créditos que o aluno já tem.
- B. Integração direta com a ElevenLabs: o plano gratuito só libera pela API as vozes que já vêm na conta (o erro 402 recusou as vozes brasileiras da biblioteca) e dá uns 10 minutos por mês. Descartado pelo aluno.
- C. Uma integração para cada fornecedor (Google, Microsoft etc.): mais chaves e mais código para o mesmo resultado.

## Decisões do tutor (o aluno pode mudar)

Refazer tudo com a Piper em vez de misturar vozes; a nuvem sem o mapa da Piper; o pedido de estilo; a pasta de cache padrão; e só WAV na resposta, que o Gemini oferece.

## Fora do escopo

Escolher a voz automaticamente, contar ou consultar créditos e trocar de fornecedor sozinho.
