# Runway, alternativas abertas e audio comercial (outubro de 2026)

## O que existe no GitHub

- [igolaizola/runway-automation](https://github.com/igolaizola/runway-automation): automatiza Runway por sessao/cookie, requer subscricao Runway ativa; o proprio autor alerta para risco de bloqueio. O modo Explore nao esta aberto a qualquer conta.
- [useapi/runway-api](https://github.com/useapi/runway-api): exemplos de cliente de um intermediario pago (useapi.net); requer conta Runway e credenciais.
- [Alpha-Park/runwayml-local-api](https://github.com/Alpha-Park/runwayml-local-api): browser automation de Runway com login e password; README diz apenas para testes.
- [sz-spec/opensway](https://github.com/sz-spec/opensway): projeto experimental que pretende simular a API Runway com modelos locais; nao certificado. Auditado no GitHub: o `model_loader.py` carrega `sdxl-turbo` para `flux_schnell` e SDXL Base para `flux_dev`, e so regista parte dos modelos anunciados; a implementacao de voz Kokoro carrega um pipeline em ingles. Nao instalar nem apresentar como equivalente pronto ou voz portuguesa validada.
- Alternativas abertas de video: [ModelTC/LightX2V](https://github.com/ModelTC/LightX2V), [LTX-Video](https://github.com/Lightricks/LTX-Video), [Wan2.2](https://github.com/Wan-Video/Wan2.2), [ComfyUI](https://github.com/comfyanonymous/ComfyUI). Podem evitar creditos por video mas exigem GPU/tempo de processamento, licencas dos pesos e integracao testada.

## Voz autentica pt-PT sem chave de API

- [Piper](https://github.com/rhasspy/piper) (TTS local) + [voz `pt_PT-tugao-medium`](https://huggingface.co/rhasspy/piper-voices/tree/main/pt/pt_PT/tug%C3%A3o/medium) do repositorio de vozes `rhasspy/piper-voices` (MIT; modelo tem dataset declarado CC0 no MODEL_CARD). Validar as licencas de cada componente. Apenas uma voz de qualidade medium; naturalidade tem de ser testada e aprovada, nao prometida.
- Modelos ONNX (`.onnx`, `.onnx.json`) NAO estao incluidos no plugin (cerca de 63 MB). Nao descarregar modelos automaticamente nem guardar chaves; instalar em ambiente isolado quando autorizado.
- Preparacao num ambiente Linux local com rede e direitos de instalacao:
  `python3 -m venv .venv && . .venv/bin/activate && pip install piper-tts`
- Instalar ffmpeg/ffprobe por via adequada ao sistema. Descarregar de Hugging Face os ficheiros `.onnx` e `.onnx.json` e colocar juntos num diretorio privado. Alternativamente, fornecer um ficheiro WAV com narracao profissional ja gravada.
- Nunca pedir credenciais do Runway, cookies do browser, clonagem vocal sem consentimento ou licencas da musica nao demonstraveis.

## Montagem, sem tocar nas imagens

O script `scripts/render_ad_audio.py` preserva os pacotes da faixa de video por `-c:v copy`, mistura uma voz WAV (humana, neural ou Piper) com uma faixa de musica legalmente usada, faz fade e normaliza o audio. Precisa de ficheiros locais. Nao gera banda sonora do nada.

Exemplo usando WAV aprovado:

```
python skills/viral-ugc-ads/scripts/render_ad_audio.py \
  --video anuncio_original.mp4 \
  --voice-wav locucao_aprovada.wav \
  --music musica_licenciada.mp3 \
  --license-note 'Mixkit; autor; titulo; URL; data de consulta' \
  --output anuncio_com_voz.mp4
```

Exemplo com Piper instalado e ficheiros de voz presentes:

```
python skills/viral-ugc-ads/scripts/render_ad_audio.py \
  --video anuncio_original.mp4 \
  --text-file narracao_ptpt.txt \
  --piper-model modelos/pt_PT-tugao-medium.onnx \
  --music musica_licenciada.mp3 \
  --license-note 'Faixa original/CC0/com licenca para anuncios, com prova' \
  --output anuncio_com_voz.mp4
```

Se a narracao exceder o tempo, o script falha com mensagem; nunca aumenta a velocidade artificialmente. A mistura aproxima-se de um rascunho profissional mas a qualidade so pode ser aprovada depois de ouvir o MP4.

## Limites do plugin

O plugin ChatGPT e um conjunto de skills e scripts, NAO um servidor de inferencia de video. Ativar o plugin nao fornece GPU, modelos, musica, autenticacao Runway nem acesso remoto a execucao do Piper. Requer runtime acessivel pelo agente para executar o script; caso contrario, apenas descreve instrucoes para integracao. Nao afirmar capacidade de gerar MP4 sem runtime e ficheiros confirmados.

### Implementacao real aprovada para testar a voz

Usar `scripts/piper_ptpt_auto.py` como caminho unico de geracao TTS/MUX em ambientes Linux x86_64 ou ARM64. Descarrega Piper v1.2.0 dos releases oficiais GitHub e modelo oficial rhasspy/piper-voices; valida SHA256 do modelo; mistura o audio no MP4 original usando FFmpeg e valida a identidade do video. Gera MP4 de teste automaticamente em ambiente com Internet, sem credito API. Nao depende nem imita endpoints privados do Runway. Audio teste e passivel de rejeicao do utilizador; nao declarar prontidao comercial por um teste tecnico.
