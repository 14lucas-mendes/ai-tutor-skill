# Cena de IDE e vídeo em Full HD: desenho

- **Data:** 2026-11-25
- **Situação:** rascunho, à espera da aprovação do aluno
- **Onde vai morar:** `docs/superpowers/specs/2026-11-25-cena-ide-design.md` no repositório da skill (`14lucas-mendes/ai-tutor-skill`), numa branch própria
- **Código afetado:** `scripts/video_lesson.py`, `tests/test_video_lesson.py`, `references/media-providers.md` (seção *Local video lessons*)

## 1. Intenção e porquê

O aluno quer que a videoaula **mostre o código acontecendo**: o código é digitado num editor parecido com uma IDE, depois roda num terminal, e a entrada e a saída aparecem ali. Slides de texto continuam onde a explicação é só conceito.

O pedido continua a regra 11 do estudo (teoria "ver primeiro"), que nasceu de uma queixa do aluno sobre a parte 3 da `lesson_19`: "faltou ver acontecendo". Hoje a cena `code` mostra o arquivo pronto, com linhas destacadas, e o terminal aparece inteiro de uma vez. É uma foto, não uma demonstração.

O aluno também pediu **resolução melhor**. O vídeo atual tem 1280×720, a 24 quadros por segundo, com taxa de vídeo de cerca de 42 kbit/s. O código em fonte pequena fica sujeito a borrão e a manchas da compressão.

A fala e a sincronia atuais estão boas, nas palavras do aluno: "as entradas e saídas das falas são exatas". Nada nelas deve piorar.

## 2. Objetivos

1. Um tipo de cena novo, `ide`: uma janela de editor (abas de arquivo, números de linha e cores de sintaxe) com um terminal embaixo.
2. O código é **digitado letra por letra**, com cursor, no ritmo da fala do passo.
3. No terminal:
   - o comando é digitado;
   - a saída do programa aparece de uma vez, como num terminal real;
   - a entrada do usuário (o que se responde a um `input()`) é digitada depois do texto da pergunta.
4. O vídeo sai em **1920×1080, a 30 quadros por segundo**, com compressão de mais qualidade.
5. Os tipos de cena atuais (`title`, `list`, `flow`, `code`, `compare`, `questions`) continuam funcionando, agora também em Full HD e com o mesmo visual.

## 3. Fora do escopo

- **Rodar o código durante a renderização.** As saídas continuam escritas no roteiro, e o tutor as confere rodando antes de renderizar, como manda hoje a *Local video lessons*.
- **Editar ou apagar código já digitado** (corrigir uma linha, mostrar um erro sendo consertado). Nesta versão, a digitação só acrescenta. Fica para uma versão seguinte, se fizer falta.
- Painel lateral de arquivos, minimapa, menus, barra de status e outros enfeites de IDE de verdade.
- Trocar a voz. Isso é o projeto 2 (seção 10).
- Qualquer mudança no áudio de revisão (`audio_review.py`).
- Copiar a marca ou o visual exato de um produto, como o logotipo ou o tema do VS Code. O visual é genérico, apenas inspirado em editores escuros.

## 4. Seria um fracasso, mesmo funcionando

- A digitação perde a sincronia com a fala: o código continua aparecendo depois que a narração já passou para outra coisa, ou termina muito antes dela.
- O texto fica ilegível numa tela de celular, ou cortado ou sobreposto.
- A tela mostra uma saída diferente da que o programa dá de verdade.
- A renderização fica tão lenta que inviabiliza o uso. Meta: uma parte de cerca de 6 minutos renderiza em até 10 minutos nesta máquina.
- Um roteiro antigo, válido hoje, para de validar ou de renderizar.

## 5. Restrições

- Tudo roda no computador do aluno, sem nada enviado para fora.
- As dependências são as de hoje (`pillow`, `pygments`, `ffmpeg`), sem nenhuma dependência nova obrigatória.
- Tema escuro.
- A legenda continua numa faixa separada, sem ser gravada na imagem (princípio da redundância).
- O `speak`, o dicionário de pronúncia e o `check` continuam funcionando como hoje.
- A mudança entra por branch e PR na skill, com o CI verde (Windows, Linux e macOS, `validate_skill` e `compileall`). Os testes que não precisam de `pillow` continuam rodando sem ele.

## 6. Caminhos considerados

| Caminho | O que é | Prós | Contras |
|---|---|---|---|
| **A. Ampliar o desenhista atual** | Tipo de cena novo no `video_lesson.py`, com quadros de digitação desenhados pelo `pillow` | Tudo local; mesma ferramenta, mesmos testes e mesmo formato de roteiro; a sincronia com a fala já existe | Mais quadros por passo, então a renderização fica mais lenta; é preciso escrever a animação |
| B. Gravar um terminal real (VHS, asciinema) | Gravação de uma sessão de terminal de verdade, encaixada no vídeo | A saída é real | Exige programas novos; é difícil sincronizar com a fala; não tem cara de IDE; funciona mal no Windows |
| C. Página web fotografada quadro a quadro | Cena montada em HTML e capturada com um navegador automático | Visual mais rico | O Playwright está quebrado nesta máquina; a dependência é pesada e o processo é mais lento |

Também foram pesquisadas, e descartadas, as APIs pagas de vídeo. Os geradores de vídeo por IA não desenham código exato. As APIs de montagem (Shotstack, Creatomate, Remotion) fazem o mesmo trabalho do `ffmpeg`, só que pagando.

**Escolha do aluno (2026-11-25): caminho A.**

## 7. Como fica (decidido)

### 7.1 Formato do roteiro: a cena `ide`

Exemplo:

```json
{
  "type": "ide",
  "title": "Quem importa",
  "files": [
    {"name": "conversoes.py", "language": "python", "code": "ZERO_ABSOLUTO = -273.15\n\ndef celsius_para_fahrenheit(c):\n    return c * 9 / 5 + 32"},
    {"name": "usar.py", "language": "python", "code": "import conversoes\n\nprint(conversoes.celsius_para_fahrenheit(100))"}
  ],
  "steps": [
    {"file": "conversoes.py", "show": 4,
     "say": "Este é o módulo que já escrevemos."},
    {"file": "usar.py", "type": 3, "highlight": [1],
     "say": "Agora um segundo arquivo importa o módulo e chama a função."},
    {"terminal": [{"cmd": "python usar.py"}, {"out": "212.0"}],
     "say": "Rodando o usar.py, aparece 212 ponto zero."}
  ]
}
```

**Campos da cena:**
- `title`: o título, desenhado pequeno para o editor ter espaço.
- `files`: de 1 a 4 arquivos, cada um com `name`, `language` e `code`. Cada arquivo vira uma aba.

**Campos de cada passo**, todos opcionais, menos o `say`:
- `say`: a narração, como hoje.
- `file`: a aba ativa. Sem esse campo, fica a mesma do passo anterior; no primeiro passo, é o primeiro arquivo.
- `type`: o número de linhas que o arquivo ativo deve ter visíveis no fim do passo. As linhas que faltam são digitadas durante a fala.
- `show`: igual ao `type`, mas as linhas aparecem de uma vez. Serve para trecho longo ou já conhecido. Um passo usa `type` ou `show`, nunca os dois.
- `highlight`: as linhas destacadas no fim do passo, com as demais esmaecidas, como na cena `code`.
- `terminal`: as linhas acrescentadas ao terminal neste passo, em ordem. Cada linha é de um destes tipos:
  - `{"cmd": "..."}`: um comando, digitado depois do `$`;
  - `{"out": "..."}`: a saída do programa, que aparece de uma vez;
  - `{"err": "..."}`: a saída de erro, que aparece de uma vez, em vermelho;
  - `{"in": "..."}`: a entrada do usuário, digitada **na mesma linha** do último `out` (é o texto da pergunta do `input()`).
- `clear_terminal`: se for `true`, o terminal é limpo antes das linhas deste passo.

**Regras de validação** (no `validate`, com mensagens no estilo das de hoje):
- o arquivo citado em `file` existe na cena;
- o `type` ou `show` fica entre 1 e o número de linhas do arquivo e nunca diminui no mesmo arquivo dentro da cena, porque a digitação só acrescenta;
- `highlight` só cita linhas visíveis;
- cada linha do terminal tem exatamente uma chave conhecida, e o texto não é vazio;
- um `in` só aparece logo depois de um `out`;
- o terminal começa vazio em cada cena e guarda o histórico até o fim dela.

### 7.2 Ritmo: como a digitação acompanha a fala

A duração de cada passo vem do áudio daquele passo, como hoje (a fala mais a pausa de 0,6 s). Os tempos abaixo contam a partir do início da fala do passo.

**Um prazo só para tudo o que se move no passo.** O código e o terminal, juntos, terminam até **75% da duração da fala**. A janela de animação começa 0,3 s depois do início do passo e vai até esse prazo.

1. **Código.** É digitado primeiro.
2. **Destaque.** O `highlight` aparece quando a digitação do código termina.
3. **Terminal.** Começa depois do código, ou no início da janela, se não houver código.
   - Cada `cmd` e cada `in` é digitado.
   - Cada `out` e cada `err` aparece de uma vez, 0,3 s depois da linha anterior.
4. **Parado.** Do prazo até o fim do passo, a tela fica parada e o cursor pisca no ponto onde parou.

**Velocidade.** Todo o texto digitado do passo (código, `cmd` e `in`) usa a mesma velocidade, escolhida assim:
- **velocidade alvo:** a que faz a animação terminar exatamente no prazo, descontadas as esperas de 0,3 s antes de cada `out` e de cada `err`;
- **piso de cerca de 8 caracteres por segundo:** se a velocidade alvo ficar abaixo disso, digita-se no piso e a animação termina antes do prazo. Isso evita uma digitação lenta demais, que pareceria artificial;
- **teto de cerca de 60 caracteres por segundo:** se a velocidade alvo passar disso, o código passa a aparecer **linha por linha**, com o tempo dividido igualmente entre as linhas, e o terminal mantém o teto. Se nem assim couber, as linhas do terminal aparecem de uma vez. O passo nunca passa do prazo e nunca dá erro por isso.

O `validate` avisa, sem falhar, quando um passo cai no modo linha por linha. Esse é o sinal de que o passo tem conteúdo demais para a fala.

**Regra para quem escreve o roteiro: uma ideia por passo.** A fala comenta o que aparece naquele passo, e não o que vem depois. Quando a fala anuncia a saída, por exemplo "aparece 212.0", a digitação do código e a execução ficam em **passos separados**: um passo digita, e o seguinte roda. Assim a saída nunca aparece depois de a fala já tê-la anunciado.

### 7.3 Tela em Full HD

```
┌────────────────────────────────────────────────────────────┐
│ Quem importa                                               │  título pequeno
│ ┌ conversoes.py ┐┌ usar.py ┐                               │  abas (a ativa acesa)
│ │ 1  import conversoes                                     │
│ │ 2                                                        │  editor: cerca de 60% da altura
│ │ 3  print(conversoes.celsius_para_fahrenheit(100))▌       │
│ ├ TERMINAL ────────────────────────────────────────────────┤
│ │ $ python usar.py                                         │  terminal: cerca de 35%
│ │ 212.0                                                    │
│ └──────────────────────────────────────────────────────────┘
│                                       rodapé da lição      │
└────────────────────────────────────────────────────────────┘
```

- O código fica num tamanho equivalente ou maior que o de hoje: 22 px em 720p equivalem a uns 33 px em 1080p.
- Se o arquivo tiver mais linhas do que cabem no editor, a tela rola para manter o cursor visível.
- Se o terminal encher, ele mostra as últimas linhas, como um terminal de verdade.
- As cenas de hoje são redesenhadas em escala (cada medida vezes 1,5), com o mesmo visual.

### 7.4 Qualidade do arquivo

- 1920×1080, 30 quadros por segundo.
- Vídeo em H.264 com CRF 18, um nível de compressão com mais qualidade que o 23 de hoje.
- O áudio continua igual: AAC a 128 kbit/s.

### 7.5 Desempenho

- Só é desenhado um quadro novo quando a tela muda (uma letra a mais, uma linha de saída, o cursor piscando). Um quadro que se repete entra na lista do `ffmpeg` com uma duração maior, como já se faz hoje com as imagens paradas.
- No máximo um quadro novo por quadro de vídeo, ou seja, 30 por segundo.

### 7.6 Compatibilidade

- A cena `code` continua existindo e serve para mostrar um arquivo sem digitação.
- Um roteiro de hoje continua validando e renderizando sem mudança nenhuma, agora em Full HD.
- O `schema_version` continua 1, porque a cena `ide` só acrescenta.

### 7.7 Como conferir

- **Testes automáticos:**
  - a validação da cena `ide`, com um caso certo e um caso errado para cada regra da 7.1;
  - o cálculo do ritmo, uma função pura que não precisa do `pillow`. Os casos: código e terminal juntos nunca passam de 75% da fala; um código curto é esticado até o prazo, mas não fica abaixo do piso; um passo longo cai no modo linha por linha; um passo que nem assim cabe mostra o terminal de uma vez; os tempos de cada passo somam a duração dele;
  - a renderização de um roteiro com uma cena `ide`, que só roda quando o `pillow`, o `pygments` e o `ffmpeg` estão instalados, como o teste de hoje; ela confere a resolução de 1920×1080 e a duração.
- **Documentação:** atualizar a *Local video lessons*, em `references/media-providers.md`, com o formato da cena `ide` e a nova resolução.
- **Piloto com o aluno:** reescrever o roteiro da parte 3 da `lesson_19`, trocando por cenas `ide` as cenas em que um código roda (como "Quem importa" e "Usar o pacote de fora"). Renderizar, conferir os quadros-chave e o `check`, e o aluno assiste e aprova.

## 8. Deixado para quem construir

- Cores exatas, tamanhos de fonte, margens e a velocidade do pisca do cursor, desde que o texto seja legível e o visual combine com as cenas de hoje.
- Se os quadros vão para o `ffmpeg` como arquivos PNG, como hoje, ou direto pela entrada padrão do programa. Vale o que cumprir a meta de tempo da seção 4.
- Os números exatos de velocidade e de teto, dentro das faixas da seção 7.2, ajustados no piloto.
- Como organizar o código da escala em Full HD (um fator de escala, ou outra forma), desde que as cenas de hoje continuem iguais.

## 9. Decisões tomadas pelo tutor (o aluno pode mudar)

- Full HD a 30 quadros por segundo, com CRF 18.
- Um prazo só: código e terminal terminam juntos até 75% da fala, digitados na mesma velocidade.
- Código curto é esticado até o prazo, mas nunca abaixo de cerca de 8 caracteres por segundo. Acima do teto de cerca de 60, o código aparece linha por linha.
- Quando a fala anuncia a saída, o código é digitado num passo e roda no passo seguinte.
- Abas para vários arquivos, sem painel lateral de arquivos.
- Digitação que só acrescenta código, sem edição nesta versão.
- A cena `code` antiga continua existindo.
- A meta de no máximo 10 minutos de renderização para cerca de 6 minutos de vídeo.

## 10. Próximo projeto, registrado aqui, mas fora deste desenho

**Projeto 2: teste de vozes.** O mesmo trecho, gravado com quatro vozes:
- a Piper, a voz de hoje;
- a Kokoro, local e grátis;
- uma do Google ou da Azure;
- uma da ElevenLabs.

O aluno escolhe ouvindo. Ele aceitou incluir vozes pagas no teste em 2026-11-25. As vozes pagas exigem que o aluno crie a conta e guarde a chave da API, e exigem o consentimento dele antes de o trecho ser enviado. O projeto tem desenho próprio e entra depois deste.
