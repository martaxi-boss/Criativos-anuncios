# Criativos-anuncios — Motor automático (pré-visualizações privadas)

Este motor transforma **imagens selecionadas pelo proprietário** e **texto aprovado** em vídeo vertical MP4 com **voz Piper pt-PT**, música discreta, sincronização por frases e testes automáticos.

## Uma ordem = uma execução

A Skill `@criativos-anuncios` deve:
1. Recolher as imagens **na ordem indicada**, texto aprovado e URL de música previamente autorizada. Não inventar imagens, texto ou vozes; não utilizar capturas antigas.
2. Criar um único JSON em `ads/requests/<nome-unico>.json`, seguindo o exemplo `ads/requests/lowcost-europa-cinco-fotos.json`. As imagens devem ter URLs HTTPS publicamente acessíveis (a Skill pode previamente carregar os anexos num serviço de assets autorizado). A execução não aceita base64 embutido, pastas internas nem URLs privadas.
3. Guardar este JSON através da integração GitHub numa nova revisão. O workflow `Criativos-anuncios - gerar video automaticamente` arranca pelo push quando o manifesto é criado/atualizado em `main`. Alternativamente, o proprietário pode acionar **Run workflow** manualmente e introduzir o caminho do JSON.
4. Acompanhar GitHub Actions, confirmar estado `success`, obter o artefacto `criativos-anuncios-mp4-voz-qa` e mostrar o MP4 ao proprietário para revisão. Um workflow iniciado não significa que o vídeo já está pronto.

O workflow só gera ficheiros no runner e nos *Actions artifacts*. **Não publica anúncios nem altera o site.** O GitHub expira artefactos ao fim de sete dias neste exemplo; descarregar/arquivar uma entrega aprovada se necessária retenção.

## Sincronização real

A voz é sintetizada frase a frase. As cenas têm `voice_range: [a,b]` (índices de início inclusivo e fim exclusivo das frases, começando no zero). As faixas devem ser consecutivas, sem lacunas e cobrir todas as frases. Cada imagem entra **no início audível da primeira frase atribuída**; o tempo é medido no WAV, não adivinhado.

O render falha se faltarem imagens, duas imagens forem duplicadas, as faixas não cobrirem a locução, uma frase de voz estiver quase muda, o MP4 não tiver áudio ou se uma fotografia não aparecer no ponto médio da sua cena. Entrega também `voice_ptpt.wav`, `report.json`, `preview_scenes.jpg`.

## Montagem local (para teste)

```bash
python3 -m venv .venv
.venv/bin/pip install piper-tts pillow
.venv/bin/python tools/criativos_anuncios/render.py \
  --request ads/requests/lowcost-europa-cinco-fotos.json \
  --output-dir ad-output
```

Exige Internet inicial para o modelo oficial Piper `pt_PT-tugao-medium` e o descarregamento autorizado das imagens e da música. O modelo é verificado por SHA256. Necessita de `ffmpeg` e `ffprobe` instalados. O upload dos ficheiros é responsabilidade da Skill/integração; o workflow não navega contas privadas.

## Segurança, propriedade e custos

- Só HTTPS com endereços de Internet públicos. Bloqueados endereços internos/localhost, credenciais embutidas e portas especiais.
- Não colocar chaves, cookies, vídeos privados, dados de clientes ou anexos confidenciais num repositório público.
- Documentar direitos dos materiais, fotos, voz, modelo e música. O exemplo Lowcost Europa é **teste privado**, com direitos comerciais por validar; `publish` e `commercial_release` devem ser `false`.
- GitHub Actions pode consumir minutos/cotas do plano. Nenhum sistema é ilimitado; a Skill não cria capacidade paga sem autorização.
- O projeto `lowcost-europa` é apenas a primeira integração de teste. Para clientes futuros, colocar este motor num repositório independente e privado (ou configurar workflow reutilizável) antes de guardar materiais não públicos, sem misturar dados de clientes.
