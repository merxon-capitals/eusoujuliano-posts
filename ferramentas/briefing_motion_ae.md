# Briefing de motion design · Reels @eusoujuliano (padrão After Effects)

Prompt de direção para editor de After Effects (ou para o nosso motor em código, que reproduz cada item). Vale para todos os Reels a partir da semana 12/10/2026.

## Prompt

> Você é um motion designer sênior especializado em After Effects, editando Reels verticais 1080×1920, 30 fps, 20 s, para um advogado que ensina a viajar com milhas (marca Duplicando Milhas, visual AMG Carbon: carbono #15171A, verde #6FBF93, branco; tipografia Barlow / Barlow Condensed).
> Edite no tempo da música (120 BPM, corte a cada compasso de 2 s) e trate cada corte como um momento de design. Monte uma composição principal com câmera 3D, camadas de vídeo em espaço 3D, ajustes de cor e uma pilha de acabamento por cima de tudo.
> Use: (1) câmera 3D com dolly-in lento e parallax, alternando a direção a cada plano; (2) transições de editor, uma diferente por corte: whip pan com motion blur direcional e separação RGB, cubo 3D, zoom-through com flash, spin whip, glitch com fatias deslocadas e aberração cromática, wipe gráfico diagonal na cor da marca e light leak sobre dissolve; (3) speed ramp em todo vídeo que entra ou sai num corte rápido (acelera até 2,6× no corte e desacelera ao chegar); (4) tipografia cinética: letras girando em X a partir da linha de base, palavra em destaque com marca-texto desenhado da esquerda para a direita, números rolando como contador até o valor final, saída com desfoque de movimento para cima, etiqueta de lugar revelada por máscara; (5) camera shake curto no drop (primeiro compasso) e na chamada final, pulso de escala em cada batida; (6) acabamento de cinema: grão de filme, vinheta, color grade teal/laranja leve, streak anamórfico nas transições rápidas; (7) end card 3D: a foto do Juliano vira um cartão flutuante que gira em Y até parar, sobre a mesma foto desfocada, com linha verde desenhando embaixo e a chamada para o treinamento.
> Som: trilha com batida, o som real de cada vídeo e um efeito para cada transição (whoosh no whip, cubo e wipe; impacto no zoom; estalos digitais no glitch; blip em cada pino do mapa; swell no light leak).
> Regras: gancho legível inteiro no primeiro quadro (vira a capa); nenhum efeito pode atrapalhar a leitura da legenda; rosto do Juliano só no fim; sem "salve/compartilhe/comenta".

## Como cada item foi feito no nosso motor (reel_ae.html + reelae.py + audio3.py)

| After Effects | No código |
| --- | --- |
| Câmera 3D, dolly e parallax | `perspective` CSS por plano; scale 1,07→1,15, rotateY ±2,2°, rotateX e translateX alternando por plano (`cam` no JSON ajusta) |
| Directional Blur + RGB split (whip) | filtro SVG por plano: feGaussianBlur só no eixo do movimento → canais R e B deslocados (feOffset) e somados em screen |
| Cubo 3D | `translateZ(-540) rotateY(a) translateZ(540)` com sombreamento por ângulo |
| Zoom-through | escala até 3,2× com desfoque e brilho, flash branco no meio, plano novo chegando de 1,7× |
| Spin whip | rotação de 90° com escala e desfoque leve |
| Glitch | corte seco no meio, tremor por quadro, RGB 26 px, faixas verdes/vermelhas/brancas em screen |
| Wipe gráfico | clip-path diagonal com faixa carbono e filete verde |
| Light leak | gradientes laranja/rosa em screen, desfocados, cruzando a tela |
| Speed ramp (time remap) | `ramp_in`/`ramp_out` automáticos; o quadro do vídeo é a integral da curva de velocidade |
| Texto cinético | letra a letra (rotateX −95°→0, stagger 12 ms), marca-texto por background-size, contador numérico (pt-BR) com largura travada |
| Shake e pulso | deslocamento amortecido no drop e na CTA; escala por batida |
| Acabamento | grão 360×640 por quadro (overlay), vinheta radial, grade soft-light teal/laranja, streak anamórfico |
| End card 3D | `card: true` no último plano: cartão com perspectiva, sombra, rotação em Y/X até parar, linha verde |
| Globo | estrelas, atmosfera verde, luz de borda, rota com brilho, avião com rastro, pinos com blip, entrada e saída em zoom-through |

Transições por plano no JSON: `"tr": "whipL" | "whipR" | "whipU" | "whipD" | "cube" | "zoom" | "spin" | "glitch" | "slab" | "leak" | "dissolve"` e `"td"` (duração). Use uma diferente a cada corte e guarde `slab` para a entrada do end card.
Render: `python3 reelae.py reels_semanaN.json [ids]`; prévia: `--stills ID t1 t2 ...`.
