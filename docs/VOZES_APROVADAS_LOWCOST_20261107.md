# Vozes aprovadas — Low Cost Europa (07/11/2026)

Registo de preferências editoriais do proprietário para futuros anúncios em português de Portugal.

## Referências aprovadas

- **Voz masculina ORIGINAL**: Piper, modelo `pt_PT-tugao-medium`. É a voz masculina do criativo anterior, não a amostra «Rui HD» que foi produzida depois. Ficheiro preservado na biblioteca do ChatGPT em `/Lowcost Europa/Vozes aprovadas/Voz_masculina_original_Piper_ptPT.wav`. Proveniência técnica: `voice_ptpt.wav` do ensaio público de criativos #42335182728.
- **Voz feminina RAQUEL**: `pt-PT-RaquelNeural`, sintetizada pelo percurso `edge-tts`, aprovada como voz de referência na amostra de hoje. Ficheiro preservado na biblioteca do ChatGPT em `/Lowcost Europa/Vozes aprovadas/Voz_feminina_Raquel_ptPT.mp3`. Workflow do exemplo completo #42345113788.

## Regras práticas

1. Respeitar estas duas referências. **Não substituir a masculina por Rui** só por o nome «Rui» aparecer em testes.
2. Para anúncios novos, voltar a sintetizar o texto no mesmo modelo escolhido, preservando ritmo e prosódia aproximados; não reutilizar frases antigas como se fossem nova narração.
3. Medir a duração do áudio real, sincronizar os planos e aprovar o resultado. O exemplo explicativo Raquel tem ~65 s, mas isso não altera o objetivo publicitário de 20 s quando pedido.
4. A biblioteca do ChatGPT conserva as **amostras**. Este repositório público conserva apenas as **referências e o código**; não colocar ficheiros de voz privados no Git nem alegar que os bytes estão instalados na VPS.
5. O workflow `Criativos-anuncios` é um projeto independente. Não misturar dependências na VPS Ferrari, não alterar a ponte SSH nem criar motor/Skill duplicada.
6. `edge-tts` depende de um serviço externo; um teste bem-sucedido no GitHub Actions não é prova de disponibilidade permanente/offline do modelo Raquel na VPS Ferrari. Validar termos e direitos de utilização comercial antes de publicar.

## Provas técnicas

- Piper pt-PT no projeto independente: https://github.com/martaxi-boss/Criativos-anuncios/actions/runs/42335182728
- Raquel neural pt-PT: https://github.com/martaxi-boss/Criativos-anuncios/actions/runs/42345113788
- Ferrari/Ruflo, certificação separada: https://github.com/martaxi-boss/VPS/actions/runs/42326357951

*Este registo não é uma declaração de que as duas vozes foram instaladas na VPS nem um certificado de áudio profissional.*
