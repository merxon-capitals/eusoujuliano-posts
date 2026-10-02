# Ferramentas de produção

Scripts usados para gerar os posts e Reels do @eusoujuliano no padrão AMG Carbon.

- `render.py`: carrosséis 1080×1350 (`POSTS=posts.json python3 render.py`).
- `reelc.py` + `reel_conexao.html`: Reels de conexão com vídeos e transições (`python3 reelc.py reels_video.json`).
- `reelm.py` + `reel_media.html`: Reels com fotos e cartões de dados.
- `reel.py` + `reel_template.html`: Reels só gráficos.
- `audio.py`: trilha sintetizada.
- `grab.py`: decodifica downloads do conector do Google Drive.

Dependências: Playwright (Chromium), ffmpeg, Pillow, pillow-heif, numpy e as fontes `@fontsource/barlow` e `@fontsource/barlow-condensed` (`npm install`).
Fotos e vídeos brutos não ficam aqui (`/home/claude/midia/jpg` e `/home/claude/midia/video`).
