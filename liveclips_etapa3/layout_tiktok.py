"""Selecao manual de webcam e render 9:16. Python padrao + ffmpeg/ffprobe."""
from __future__ import annotations
import json
import math
import subprocess
import tempfile
from pathlib import Path

import config
from comum import make_srt, read_json, session_output
from legendas_dinamicas import make_ass

TIKTOK_W = 720   # 9:16 leve para computadores antigos
TIKTOK_H = 1280
TOP_H = 576       # 45% da tela dedicada a reacao do streamer
BOTTOM_H = TIKTOK_H - TOP_H


def video_dimensions(source: Path) -> tuple[int, int]:
    p = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height', '-of', 'json', str(source)],
        capture_output=True, text=True, timeout=35)
    if p.returncode:
        raise RuntimeError('ffprobe nao conseguiu ler o video: ' + p.stderr[-500:])
    info = json.loads(p.stdout)
    s = info['streams'][0]
    return int(s['width']), int(s['height'])


def default_camera(corner: str) -> list[float]:
    """Coord. normalizadas (0..1) da webcam, com 23% largura e 32% altura."""
    w, h, margin = 0.23, 0.32, 0.015
    x = margin if corner in ('1', '3') else 1 - w - margin
    y = margin if corner in ('1', '2') else 1 - h - margin
    return [x, y, w, h]


def _clamp_rect(rect: list[float]) -> list[float]:
    x, y, w, h = (float(v) for v in rect)
    x = max(0, min(0.98, x)); y = max(0, min(0.98, y))
    w = max(0.02, min(1.0 - x, w)); h = max(0.02, min(1.0 - y, h))
    return [round(x, 5), round(y, 5), round(w, 5), round(h, 5)]


def select_camera_on_image(source: Path) -> list[float] | None:
    """Escolha manual em miniatura usando Tkinter (incluso no Python Windows)."""
    import tkinter as tk
    from tkinter import messagebox

    with tempfile.TemporaryDirectory(prefix='liveclips_preview_') as temp:
        png = Path(temp) / 'frame.png'
        cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
               '-ss', '2', '-i', str(source), '-frames:v', '1',
               '-vf', 'scale=960:-2', str(png)]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=75)
        if proc.returncode or not png.exists():
            raise RuntimeError('Nao consegui obter imagem de exemplo. ' + proc.stderr[-400:])
        result = {'rect': None}
        root = tk.Tk()
        root.title('LiveClips - selecione a webcam com o mouse')
        root.resizable(False, False)
        tk.Label(root, text='Clique e arraste um retangulo ao redor da WEBCAM. Depois clique Confirmar.',
                 font=('Arial', 11), pady=8).pack()
        img = tk.PhotoImage(file=str(png))
        iw, ih = img.width(), img.height()
        canvas = tk.Canvas(root, width=iw, height=ih, cursor='crosshair', bd=0, highlightthickness=0)
        canvas.pack()
        canvas.create_image(0, 0, anchor='nw', image=img)
        state = {'x': 0, 'y': 0, 'rectangle': None, 'coords': None}
        def down(e):
            state['x'] = max(0, min(iw, e.x))
            state['y'] = max(0, min(ih, e.y))
            if state['rectangle']:
                canvas.delete(state['rectangle'])
            state['rectangle'] = canvas.create_rectangle(e.x, e.y, e.x, e.y, outline='#00ffff', width=3)
        def move(e):
            if state['rectangle']:
                canvas.coords(state['rectangle'], state['x'], state['y'],
                              max(0, min(iw, e.x)), max(0, min(ih, e.y)))
        def up(e):
            x1, x2 = sorted((state['x'], max(0, min(iw, e.x))))
            y1, y2 = sorted((state['y'], max(0, min(ih, e.y))))
            state['coords'] = (x1, y1, x2, y2)
        canvas.bind('<ButtonPress-1>', down)
        canvas.bind('<B1-Motion>', move)
        canvas.bind('<ButtonRelease-1>', up)
        def confirm():
            coords = state['coords']
            if not coords or coords[2] - coords[0] < 35 or coords[3] - coords[1] < 30:
                messagebox.showwarning('Webcam', 'Desenhe um retangulo com tamanho suficiente.')
                return
            x1, y1, x2, y2 = coords
            result['rect'] = _clamp_rect([x1 / iw, y1 / ih, (x2-x1) / iw, (y2-y1) / ih])
            root.destroy()
        tk.Button(root, text='Confirmar area da webcam', font=('Arial', 11, 'bold'),
                  command=confirm, pady=7).pack(pady=8)
        root.mainloop()
        return result['rect']


def configure_profile(folder: Path, *, force: bool = False) -> dict:
    output = session_output(folder)
    path = output / 'perfil_tiktok.json'
    if path.exists() and not force:
        p = read_json(path)
        print('Perfil TikTok encontrado:', path, flush=True)
        ans = input('Usar a configuracao anterior? [Enter = S / N = configurar de novo]: ').strip().lower()
        if ans not in ('n', 'nao'):
            return p
    print('\nESCOLHA A POSICAO DA WEBCAM NA LIVE:')
    print(' 1 - Superior esquerdo')
    print(' 2 - Superior direito')
    print(' 3 - Inferior esquerdo')
    print(' 4 - Inferior direito')
    print(' 5 - Marcar a webcam com o MOUSE (recomendado se nao estiver num canto)')
    selection = input('Digite 1, 2, 3, 4 ou 5: ').strip()
    if selection not in ('1', '2', '3', '4', '5'):
        raise ValueError('Opcao invalida. Execute novamente e escolha 1, 2, 3, 4 ou 5.')
    if selection == '5':
        sources = sorted(folder.glob('segmento_*.ts'))
        if not sources:
            print('Nenhum segmento disponivel para mostrar a imagem. Aguarde o primeiro segmento.')
            raise RuntimeError('Nao ha arquivos .ts para marcar a webcam.')
        try:
            rect = select_camera_on_image(sources[0])
        except Exception as e:
            print('Nao foi possivel abrir a janela de selecao:', e)
            raise RuntimeError('Tente escolher um dos cantos (1-4) ou iniciar a captura.') from e
        if rect is None:
            raise RuntimeError('Janela fechada sem confirmar a webcam. Tente novamente.')
    else:
        rect = default_camera(selection)
        print('Atencao: o recorte rapido presume a webcam com cerca de 23% de largura.', flush=True)
        print('Se a webcam aparecer cortada, execute novamente e escolha opcao 5.', flush=True)
    profile = {'schema_version': 1, 'camera_rect': _clamp_rect(rect),
               'resolution': [TIKTOK_W, TIKTOK_H], 'top_height': TOP_H}
    path.write_text(json.dumps(profile, indent=2), encoding='utf-8')
    print('Perfil salvo em:', path)
    return profile


def camera_pixels(source: Path, profile: dict) -> tuple[int, int, int, int]:
    vw, vh = video_dimensions(source)
    x, y, w, h = _clamp_rect(profile['camera_rect'])
    # crop width/height/x/y pares para maior compatibilidade com codificadores.
    cw = max(4, int(vw * w) // 2 * 2)
    ch = max(4, int(vh * h) // 2 * 2)
    cx = min(max(0, int(vw * x) // 2 * 2), max(0, vw - cw))
    cy = min(max(0, int(vh * y) // 2 * 2), max(0, vh - ch))
    return cw, ch, cx, cy


def render_tiktok(job: dict, output: Path, *, preview: bool = False) -> Path:
    profile_path = output / 'perfil_tiktok.json'
    if not profile_path.exists():
        raise RuntimeError('Perfil TikTok nao configurado. Execute INICIAR_TIKTOK.bat primeiro.')
    profile = read_json(profile_path)
    source = Path(job['source'])
    if not source.is_file():
        raise FileNotFoundError(f'Arquivo original nao existe: {source}')
    start, end = float(job['start']), float(job['end'])
    if not 0 <= start < end:
        raise ValueError('Tempos invalidos para o corte.')
    target_dir = output / 'cortes_tiktok'
    target_dir.mkdir(parents=True, exist_ok=True)
    clip_id = str(job['id'])
    suffix = '_PREVIA' if preview else '_tiktok'
    outfile = target_dir / f'{clip_id}{suffix}.mp4'
    subfile = target_dir / f'{clip_id}{suffix}.srt'
    trans_path = Path(job['transcription']) if job.get('transcription') else None
    trans = read_json(trans_path) if trans_path and trans_path.exists() else {'segments': []}
    captions = make_srt(trans['segments'], start, end)
    subfile.write_text(captions, encoding='utf-8-sig')
    ass = make_ass(trans['segments'], start, end)
    (target_dir / f'{clip_id}{suffix}.ass').write_text(ass, encoding='utf-8-sig')
    cw, ch, cx, cy = camera_pixels(source, profile)
    # Tamanho final TikTok 9:16. Reacao no topo (45%), gameplay embaixo (55%).
    # Escala para preencher paineis sem faixas pretas. O jogo fica com crop central.
    core = (f'[0:v]fps=30,split=2[cam0][game0];'
        f'[cam0]crop={cw}:{ch}:{cx}:{cy},'
        f'scale={TIKTOK_W}:{TOP_H}:force_original_aspect_ratio=increase,'
        f'crop={TIKTOK_W}:{TOP_H},setsar=1[cam];'
        f'[game0]scale={TIKTOK_W}:{BOTTOM_H}:force_original_aspect_ratio=increase,'
        f'crop={TIKTOK_W}:{BOTTOM_H},setsar=1[game];'
        f'[cam][game]vstack=inputs=2,format=yuv420p[base]')
    with tempfile.TemporaryDirectory(prefix='liveclips_tiktok_') as tmp:
        tmpdir = Path(tmp)
        (tmpdir / 'legendas.ass').write_text(ass, encoding='utf-8-sig')
        def makecmd(embed_subtitles: bool):
            if embed_subtitles and captions.strip():
                # A legenda fica na zona da gameplay, sem tapar o rosto do streamer.
                filters = core + ';[base]ass=legendas.ass[vout]'
                vlabel = '[vout]'
            else:
                filters = core
                vlabel = '[base]'
            return ['ffmpeg', '-hide_banner', '-y', '-loglevel', 'error',
                '-ss', f'{start:.3f}', '-i', str(source), '-t', f'{end-start:.3f}',
                '-filter_complex', filters, '-map', vlabel, '-map', '0:a:0?',
                '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '26',
                '-threads', '3', '-c:a', 'aac', '-b:a', '112k',
                '-movflags', '+faststart', str(outfile)]
        p = subprocess.run(makecmd(embed_subtitles=True), cwd=tmpdir, capture_output=True, text=True)
        if p.returncode:
            outfile.unlink(missing_ok=True)
            raise RuntimeError('FFmpeg falhou: ' + p.stderr[-1800:])
    if not outfile.exists() or outfile.stat().st_size == 0:
        raise RuntimeError('FFmpeg terminou sem gerar video.')
    print('[TIKTOK] PRONTO:', outfile, flush=True)
    return outfile
