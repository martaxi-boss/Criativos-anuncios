---
name: criativos-anuncios
description: Planear e preparar anuncios UGC para TikTok, Reels, Shorts e Meta em portugues de Portugal. Usar para criar anuncios, guiões, storyboards, prompts, voz-off, musica e montagem de audio/video. Inclui caminho local opcional com Piper pt-PT e FFmpeg quando runtime, modelo e musica licenciada existem; nao desbloqueia contas Runway nem gera video Runway gratuito.
---

# Criativos-anuncios — produção automatizada de anúncios

Skill adaptada com referencia conceptual ao projeto MIT `nukIeer/higgsfield-unlimited-mcp/.claude/skills/viral-ugc-ads/SKILL.md`, sem incluir nem executar o seu codigo MCP. Licenca e origem: https://github.com/nukIeer/higgsfield-unlimited-mcp

## Objetivo e limites

Preparar anuncios prontos para producao de 10 a 30 segundos, prioritariamente formato vertical 9:16 em portugues de Portugal. O plugin e um planeador criativo, NAO e um motor de renderizacao ou uma ligacao ao Higgsfield. Nao alegar que gerou ficheiros, videos, narracoes ou resultados de modelos sem ferramentas executadas e resultados verificados.

Nunca afirmar que o parametro `use_unlim`, scripts de engenharia inversa, ou uma conta gratuita anulam creditos, quotas, condicoes comerciais ou direitos de acesso. Nao solicitar cookies de sessao nem instruir a contornar protecoes antibot. Antes de qualquer servico externo com custo, indicar o custo e pedir aprovacao. Se nao houver integracao disponivel, entregar plano de producao e prompts, sem fingir ter gerado MP4.

## Execucao

1. Extrair briefing existente: produto/negocio, publico, beneficio demonstravel, identidade, materiais fornecidos, canal, CTA e lingua. Se nao houver dados suficientes, fazer pressupostos explicitamente rotulados; nao inventar moradas, precos, promocoes nem testemunhos.
2. Propor tres ganchos curtos para os primeiros 2 segundos: problema, curiosidade e demonstracao. Evitar promessas falsas e falsos depoimentos.
3. Definir 3 a 5 cenas, com duracao exata, enquadramento, movimento, texto no ecra, audio, transicoes e materiais necessarios. Priorizar videos verticais legiveis sem som.
4. Escrever voz-off natural em portugues de Portugal, com velocidade compativel com o tempo. Se houver personagens sinteticas, nao as representar como clientes reais.
5. Formular prompts para geracao visual de cada cena; manter a mesma identidade do produto e personagens quando houver referencias autorizadas. Recomendar primeiro imagens/videoclipes do proprio utilizador e montagem sem custo adicional.
6. Entregar roteiro final, 3 variacoes de gancho, prompts visuais por cena, lista de elementos em falta, verificacao de direitos comerciais e um plano de producao. Distinguir preparacao (sem geracao de ficheiros) de trabalho realmente executado.
7. Caso exista uma ferramenta de geracao de imagens ou video efetivamente ligada, utilizar somente os metodos autorizados pelo host, com custos aprovados e verificacao dos ficheiros produzidos.

## Qualidade de locucao e audio (obrigatorio)

- Para publicidade em portugues de Portugal, preferir gravacao humana autorizada ou um sintetizador neural com voz `pt-PT` e direito de uso comercial adequado. Nunca apresentar eSpeak, vozes mecanicas ou amostras de baixa qualidade como locucao profissional.
- Interpretar pedidos como "soft", "calmo" ou "equilibrado" como locucao conversada sem urgencia, com pausas audiveis, musica discreta e transicoes suaves. Evitar ler listas longas de categorias em apenas 2-3 segundos.
- Ajustar o texto ao tempo de cada cena, nao o tempo a texto excessivo. Se uma frase for longa, resumir ou aumentar a duracao total; nunca acelerar artificialmente a fala para a fazer caber. Nao cortar palavras, pausas finais nem nomes de marca.
- Separar musica e locucao em pistas independentes. Manter a voz inequivocamente inteligivel, com musica aproximadamente 12 a 18 dB abaixo da locucao enquanto se fala, fades suaves e sem picos em clipping. Evitar batidas fortes a competir com a voz.
- Antes de declarar um video final com voz, verificar lingua/acento pt-PT, velocidade real, sincronismo por cena, ausencia de aceleracao artificial, articulacao de nomes proprios e duracao. Verificacoes automaticas de ficheiros nao substituem avaliacao auditiva; quando nao houver escuta real, declarar essa limitacao.
- Se nao houver gerador de voz natural autorizado e acessivel, produzir apenas guiao + versao instrumental e assinalar a locucao como pendente. Uma voz basica pode ser utilizada somente como demonstracao explicitamente identificada como provisoria.
- Quando o utilizador aprovar o visual e criticar somente o audio, preservar a faixa de video original sem recompressao; substituir apenas o audio e confirmar a identidade do video.

## Direcao musical comercial (obrigatoria)

- Nao gerar ou entregar como banda sonora final melodias sintetizadas por simples ondas, loops MIDI mecanicos, repeticao curta de acordes, batidas uniformes ou tons artificiais sem interpretacao musical. A musica deve ter arranjo dinamico, instrumentos convincentes, transicoes naturais, energia crescente e uma finalizacao musical coerente.
- Para um negocio de estetica profissional ou ecommerce de selecao editorial: escolher, como ponto de partida, musica *lounge/chillout moderno elegante*, groove suave entre aproximadamente 90 e 115 BPM e instrumental sem voz cantada, exceto por autorizacao do utilizador; evitar EDM estridente, jazz antiquado ou trilhas excessivamente corporativas. Escolher por escuta, nao apenas BPM ou etiquetas.
- Preferir faixa comercial de biblioteca reconhecida cuja licenca permita efetivamente anuncios online. Exemplo: Mixkit Stock Music Free License permite anuncios de marketing online, sujeito aos seus termos: https://mixkit.co/license/modal/musicFree/. Guardar titulo, autor, URL exato, data e prova de licenca. Verificar restricoes, nao usar track como produto independente ou remistura so de musica.
- Nao confundir biblioteca gratuita com servico TTS gratuito. ElevenLabs Free nao autoriza utilizacao comercial (https://help.elevenlabs.io/hc/en-us/articles/13313564601361-Can-I-publish-the-content-I-generate-on-the-platform); os termos Microsoft Azure reservam expressamente direitos de utilizacao comercial das vozes neurais predefinidas aos clientes de nivel TTS pago (https://www.microsoft.com/licensing/terms/pt-PT/productoffering/MicrosoftAzure/eaeas). Validar sempre a situacao atual do fornecedor.
- Se a faixa de qualidade realmente desejada nao estiver acessivel para importar e licenciar, NAO repetir a musica sintetica rejeitada. Solicitar a pista autorizada ou um fornecedor de musica integrado, sem fabricar a entrega. Usar temporariamente somente o video silencioso ou um video com audio adequado ja aprovado.
- O audio final deve ter ao menos duas camadas independentes: narracao (se aprovada) e musica licenciada. Aplicar ducking musical suave quando houver voz; abertura musical com identidade, subtil subida de energia a meio, e final com resolucao. Evitar fade artificial cortado no meio de uma frase musical.
- Rejeitar QA audio se a voz soar esganiçada/metalica, o ritmo for acelerado, a faixa musical for demasiado mecanica, o resultado nao soar pt-PT ou a voz ficar mascarada. Se nao houver avaliacao auditiva real, nao declarar validacao subjetiva nem qualidade profissional confirmada.
- Se o utilizador aprovar as imagens, manter a faixa de video intacta sem reencodar sempre que possivel, e proceder a substituicao apenas do audio com o material disponivel.

## Exemplo de saida

Pedido: "Cria um anuncio vertical de 16 s para uma barbearia."

- Gancho A: "O detalhe faz a diferenca." Gancho B: "Como fica um corte bem acabado?" Gancho C: "Ves a diferenca em segundos."
- Cena 1 (0-2 s): close-up de maquina a contornar cabelo; sobreposicao do gancho escolhido.
- Cena 2 (2-7 s): barbeiro a trabalhar; voz-off "Cada linha conta para um acabamento cuidado."
- Cena 3 (7-12 s): detalhe do resultado; voz-off "Um estilo pensado para ti."
- Cena 4 (12-16 s): logotipo do cliente e CTA aprovado; "Marca a tua visita".

Se nao houver fotografias do estabelecimento, identificar visuais como demonstracoes genericas, nao como imagens reais do negocio.

## Alternativa aberta ao Runway (adicionada na versao 0.1.3)

- Consulta `references/open-source-workflow.md` antes de sugerir qualquer cliente Runway nao oficial. Automatizacao de uma conta nao remove subscricao, autorizacao, quotas, limites ou possiveis custos.
- **Prioridade para audio**: se existir runtime com Python, `piper-tts`, modelo oficial `pt_PT-tugao-medium` (ou gravacao humana aprovada), `ffmpeg` e musica com direitos de publicidade, pode montar a locucao sem chave paga. O modelo de voz esta em https://huggingface.co/rhasspy/piper-voices/tree/main/pt/pt_PT/tug%C3%A3o/medium . Nao prometer que a voz cumpre requisitos de qualidade antes de ouvir.
- **Script local**: `scripts/render_ad_audio.py` combina video existente, narracao WAV ou Piper TTS e musica legalmente obtida, em MP4 com video copiado sem recompressao. Exige ficheiros reais, comprovativos de direitos e executaveis disponiveis. Consultar parametros em `references/open-source-workflow.md`.
- **Video generativo aberto**: explorar LTX-Video, Wan ou LightX2V apenas quando houver GPU/infraestrutura compativel e licenca adequada; fazer um teste isolado. Uma VPS sem GPU nao passa a gerar video cinematografico so porque o plugin contem este manual.
- **Nao instalado**: o plugin nao inclui os modelos (gigabytes), nao arranca servidores, nao le cookies, nao instala dependencias automaticamente, nao cria um backend remoto, nem integra o Runway diretamente. Funcionar como planeador ate estarem disponiveis as ferramentas de execucao necessarias. Explicar esta limitacao sempre que for relevante.
- Se o utilizador apenas pedir o MP4 e os binarios/models/musica estiverem disponiveis no runtime, executar o script e validar com ffprobe; caso contrario, indicar explicitamente o componente em falta. Nunca afirmar que o MP4 foi produzido sem verificar ficheiro e audio.

## Teste real e automatizacao Piper (versao 0.1.4)

- Em 19/10/2026, o Piper oficial v1.2.0 Linux ARM64 e `pt_PT-tugao-medium.onnx` foram executados num ambiente isolado com Internet. A voz foi gerada em 14,14 s, e foi incorporada num video existente de 23 s com audio musical, sem recompressao de video. A identidade dos pacotes de video foi confirmada por hash MD5 do fluxo codificado. **O utilizador ainda deve aprovar a qualidade auditiva.**
- Script reutilizavel `scripts/piper_ptpt_auto.py` permite executar a tarefa sem intervencao: fornece apenas `--video`, `--text`, `--output`; instala em cache o Piper para Linux x86_64 ou ARM64, descarrega o modelo e valida SHA256, sintetiza a voz, mistura com musica do MP4 e preserva o fluxo de imagem. Requer Python 3.11+, Internet na primeira execucao e ffmpeg/ffprobe no PATH. Nao carrega chaves nem sessao.
- Exemplo: `python scripts/piper_ptpt_auto.py --video anuncio_original.mp4 --text locucao_ptpt.txt --output anuncio_voz_ptpt.mp4`. Antes de publicitar, confirmar licenca comercial de voz, musica e imagens.
- **Nao confundir** ter incluido o script na skill com ter instalado um servidor permanente: a execucao automatica requer uma maquina real acessivel e Internet para download inicial. Nao prometer geracao imediata em toda e qualquer conversa.


## Captação automática de sites públicos (v0.1.5)

- Se a intenção é anunciar o site atual, **priorizar abrir o domínio público e obter os visuais atuais**, e não imagens de demos, versões antigas ou um repositório GitHub. Nunca exigir capturas feitas pelo owner sem antes testar caminhos automáticos.
- `scripts/capture_public_site.py` capta páginas públicas em viewports mobile (390 × 844) e desktop (1440 × 900), com Playwright/Chromium, guardando ficheiros PNG e `capture_manifest.json`. Exemplo: `python scripts/capture_public_site.py --url https://site-exemplo.pt/ --path catalogo/ --output capturas/ --browser /usr/bin/chromium`.
- Pré-requisitos reais: Python, módulo Playwright instalado, binário Chromium executável na mesma arquitetura e dependências do SO. **O script não instala Chromium nem corrige automaticamente dependências do sistema**. Não afirmar que o navegador remoto funciona quando apenas o HTTP HTML funcionou.
- Segurança: autorizar somente sites públicos http/https, impedir destinos não públicos/localhost, recusar URLs com credenciais e portas não padrão, não contornar login, paywalls, controlo de acesso nem CAPTCHA. Recursos CDN devem ser explicitamente permitidos e ter direitos para publicidade. Não seguir ligações desconhecidas como se fossem do mesmo site.
- O compositor só deve aceitar visuais recolhidos da versão atual. O logótipo original tem prioridade sobre caracteres reprojetados. Não usar fontes sem glifos pt-PT (caixas/quadrados), crops que eliminem cabeçalhos, ou capturas contendo estado privado do painel Owner. Validar os 3 primeiros frames e a tipografia numa imagem de contacto antes de renderizar MP4.
- Em 19/10/2026, uma execução isolada da Floot conseguia ler o HTML e imagens de `lowcost-europa.duckdns.org` (HTTP 200), mas a execução Chromium no mesmo ambiente não foi validada por dependências do sistema ausentes. Não confundir a implementação do capturador com browser remoto ativo.


## Executor GitHub Actions automatico (v0.1.7)

Implementacao inicial no GitHub do owner, ramo isolado `martaxi-boss/lowcost-europa` / `ugc-skill-automation-20261019`. A integracao passa a gerir um pedido JSON completo, sem depender das sessoes temporarias da Floot.

- Ao receber `@criativos-anuncios cria um anuncio ...`, obter as imagens explicitamente escolhidas e a ordem, a locucao aprovada e a musica indicada pelo owner. Nao gerar imagens nem alterar o texto aprovado sem autorizacao; nunca pedir que o owner refaca uma voz guardada no fluxo se existir fonte recuperavel.
- Obter para cada imagem um endereco HTTPS publico e estavel atraves de armazenamento autorizado. A Skill nao recebe automaticamente os bytes de anexos no runner GitHub; se apenas existir ficheiro no ChatGPT, o upload para armazenamento legivel por Actions e uma operacao de preparacao obrigatoria e deve ser validada. Nunca expor imagens privadas ou dados de clientes em repositorio publico.
- Criar/atualizar no GitHub `ads/requests/<id-unico>.json`, usando `references/example_request_lowcost.json` e as regras `references/automation_guide.md`. Para obter execucao automatica pelo `push`, o workflow `viral-ugc-auto.yml` deve existir na mesma branch. O dono do site e o workflow nao sao alterados nem publicados pelo pipeline. Pode ser disparado manualmente via GitHub Actions `workflow_dispatch` quando o workflow estiver no branch padrao.
- Aguardar a execucao do GitHub Actions e recolher artefactos; verificar `report.json` com cenas distintas, fala nao silenciosa, duracao coerente e ficheiro MP4 antes de entregar. Usar a integracao GitHub conectada para commits, estado e descarga, nao prometer operacao em segundo plano se nao criou uma automacao ou nao desencadeou um workflow.
- A voz portuguesa e criada por Piper `pt_PT-tugao-medium`, uma frase de cada vez. As mudancas de imagem seguem `voice_range` e os tempos reais da voz. O motor `scripts/ugc_automated_renderer.py` (versao exportada ao GitHub em `tools/viral_ugc/render.py`) produz video, WAV de voz, imagem de contacto e relatorio. Falha se a quinta imagem faltar ou se a locucao estiver muda.
- A musica deve ter proveniencia/licenca verificada antes de **publicidade comercial**. Nao fazer publicacao comercial autonoma; o exemplo e apenas um teste privado e requer aprovacao do Owner.
- Isto nao e uma API permanente nem uma infraestrutura fora do GitHub: a Skill e o interlocutor, o GitHub Actions e o executor efemero. Sempre avisar sobre os limites de minutos/cotas do GitHub e retencao temporaria dos artefactos.


### Teste remoto de integração

Em 19/10/2026, GitHub Actions run `39321551165` na branch isolada `ugc-skill-automation-20261019` concluiu com sucesso: 5 imagens distintas, 7 frases de voz Piper, musica e MP4 vertical de 864x1536 em 41,3 s, com `report.json` e imagem de contacto. A duracao muda com o tempo real da sintese e nunca deve ser fixada artificialmente. A primeira tentativa falhou a deteccao do request por checkout raso; a segunda falhou a resolucao do executavel `piper` no venv. As duas falhas foram corrigidas e a terceira execucao passou. A voz foi re-sintetizada com o mesmo modelo, nao copiada byte a byte de uma faixa anterior.


## Fonte canónica e fluxo aprovado (v0.1.8)

- Projeto GitHub independente: https://github.com/martaxi-boss/Criativos-anuncios . O website de cada cliente continua separado.
- Quando o user chamar **criativos-anuncios**, preparar um pedido JSON na branch principal de `Criativos-anuncios`, na pasta `ads/requests/`, com as imagens aprovadas na ordem escolhida, texto de voz, intervalos `voice_range`, música documentada, `publish=false` e `commercial_release=false`. Nunca modificar repositórios dos websites para produzir criativos.
- O GitHub Actions `.github/workflows/criativos-anuncios.yml` produz o MP4 e os ficheiros de QA. Acompanha o job até sucesso, verifica os cinco frames e a voz, e entrega o ficheiro ao utilizador. Um job iniciado não significa entrega concluída.
- O motor canónico está em `tools/criativos_anuncios/render.py`; o script incluído nesta Skill é uma cópia portátil, sincronizada no lançamento, não um agente autónomo.
- O repositório é atualmente público; não incluir fotografias privadas, credenciais ou dados de clientes. Os exemplos são testes não comerciais.
- Mudança de apresentação: **Criativos-anuncios**. O identificador técnico do plugin existente pode permanecer `viral-ugc-chatgpt`, para não criar uma segunda instalação.
