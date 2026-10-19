# Edição fotográfica realista — pessoas e cenários

Este fluxo complementa o motor de anúncios; **não substitui** a montagem de vídeo existente.

## Ferramenta de edição

Para trocar uma pessoa de uma fotografia por outra, o plugin **Criativos-anuncios** (a partir de 0.1.9) utiliza a capacidade nativa de **edição generativa de imagens no ChatGPT**, quando disponível. Este método é preferível a recorte/colagem em Pillow ou FFmpeg, que continuam reservados à preparação de imagens e à produção de MP4. A ferramenta nativa **não fica instalada nem executável nos runners do GitHub Actions** por esta documentação; automatizar essa fase exigiria uma integração aprovada e possivelmente custos e credenciais adicionais.

## Entradas e operação

1. Receber fotografia original da pessoa, fotografia de fundo e, opcionalmente, uma tentativa anterior para identificar defeitos.
2. Usar a primeira como referência de identidade, vestuário, posição e objeto; usar a segunda como referência principal de arquitetura, luz e perspetiva. O resultado anterior falhado **não** é imagem-base.
3. Retirar completamente a pessoa antiga do fundo, reconstruir zonas tapadas e integrar a nova pessoa com proporções, sombras e iluminação compatíveis.
4. Preservar rigorosamente o texto visível em papel/cartazes e não redesenhar elementos do quarto sem necessidade.
5. Fazer verificação visual: sem restos da pessoa removida, bordos enevoados, pernas duplicadas, dedos deformados, cortes de móveis ou texto trocado.
6. Entregar pré-visualização para aprovação; só depois usar essa imagem na pipeline de MP4.

## Privacidade e integridade

Não colocar fotografias de clientes ou pessoas privadas no repositório público. Não apresentar fotomontagens como registo documental não alterado. Se a edição generativa não estiver disponível, declarar a limitação; não substituir por recortes desfocados em silêncio.
