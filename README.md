# Criativos-anuncios

Motor reutilizável de produção de anúncios verticais em português de Portugal, associado à Skill privada **criativos-anuncios**.

**Fluxo:** pedido JSON com fotografias autorizadas, texto e música → voz Piper pt-PT → FFmpeg → sincronização automática das cenas com a locução → verificações de áudio e imagens → MP4 e relatório privado via GitHub Actions.

## Automação só com URL — sem fotografias manuais

Uma única ordem com o endereço do site público pode iniciar a pré-visualização privada. Exemplo: criar um ficheiro novo em `ads/requests/` com o seguinte conteúdo:

```json
{"id":"meu-site-001","source_url":"https://example.com/","publish":false,"commercial_release":false}
```

A GitHub Action existente recolhe as páginas reais com Chromium/Playwright, grava capturas de secções distintas e produz MP4, WAV, relatório e pré-visualização com a voz **Piper pt_PT-tugão-medium**. Esse é o mesmo modelo de voz usado na demonstração aprovada do proprietário. Não é uma voz humana gravada; cada locução nova deve ser ouvida antes de ser aceite para publicidade. Nenhuma fotografia precisa de ser fornecida manualmente se a página pública for acessível.

O resultado é **preview_only**. Capturas da página não são automaticamente um filme profissional aprovado. A locução pode alterar a duração do vídeo; não acelerar artificialmente para cumprir 20 segundos. Sem música licenciada, a prévia automática entrega apenas voz.

O modo automático não faz login nem contorna bloqueios de redes sociais. Reels protegidos ou vídeos sem media original publicamente acessível e autorizado **não estão suportados só com um URL**; o sistema comunica esta limitação em vez de inventar cenas. Os projetos continuam independentes: este workflow executa apenas no próprio repositório GitHub, sem instalações na VPS Ferrari e sem alterar o website.

## Uso

1. Abrir a Skill **criativos-anuncios** no ChatGPT e dar uma ordem com os visuais na sequência pretendida.
2. A Skill coloca o pedido em `ads/requests/<id>.json`, seguindo `ads/requests/lowcost-europa-cinco-fotos.json`.
3. O workflow `.github/workflows/criativos-anuncios.yml` executa após a criação de um pedido, ou pela opção **Run workflow** no GitHub Actions.
4. O resultado de teste fica no artefacto `criativos-anuncios-mp4-voz-qa` (MP4, WAV da locução, pré-visualização das cenas e relatório JSON).

Pode executar localmente: `python tools/criativos_anuncios/render.py --request ads/requests/lowcost-europa-cinco-fotos.json --output-dir ad-output`, após instalar Piper, Pillow e FFmpeg. Consultar `docs/GUIA.md`.

## Edição fotográfica (montagens entre ambientes)

Para substituir uma pessoa num cenário sem recortes artificiais, o plugin **Criativos-anuncios** passou a incluir um fluxo de edição generativa de imagens no ChatGPT (skill especializada da versão 0.1.9), com referências separadas para pessoa e ambiente e verificações de anatomia, perspetiva, luz e texto manuscrito. **Não é uma API de edição instalada no GitHub Actions:** a imagem é editada no ChatGPT e, após aprovação, pode ser fornecida ao motor de vídeo atual. Detalhes em [docs/EDICAO_FOTOGRAFICA.md](docs/EDICAO_FOTOGRAFICA.md). Não carregar fotografias privadas neste repositório público.

## Estado da entrega

O motor teve execução de produção automática validada anteriormente em `martaxi-boss/lowcost-europa`, [GitHub Actions #39321551165](https://github.com/martaxi-boss/lowcost-europa/actions/runs/39321551165). A consolidação neste repositório preserva os scripts e a lógica testada. Novos vídeos produzidos a partir deste repositório precisam da verificação da respetiva execução.

O repositório **não publica anúncios**, não altera o website Lowcost Europa, não contém credenciais e não deve receber fotografias, gravações ou dados privados de clientes enquanto for público. O pedido de demonstração utiliza URLs públicos e materiais somente para teste; a licença para utilização comercial de imagens, vozes e música tem de ser validada antes de publicar.

[Skill Criativos-anuncios](https://chatgpt.com/plugins/Plugin_fc6a923e96c88191ba7039b6744d6eea)
