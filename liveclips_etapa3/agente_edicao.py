"""Processo 2: consome a fila e renderiza cortes em 9:16 via FFmpeg + SRT."""
from __future__ import annotations
import json
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path

import config
from comum import make_srt, read_json, session_output


def render(job: dict, output: Path) -> None:
    trans = read_json(Path(job['transcription']))
    start = float(job['start'])
    end = float(job['end'])
    clip_id = str(job['id'])
    outfile = output / 'cortes' / (clip_id + '_vertical.mp4')
    subfile = output / 'cortes' / (clip_id + '.srt')
    titlefile = output / 'cortes' / (clip_id + '_descricao.txt')
    captions = make_srt(trans['segments'], start, end)
    # SRT sempre fica separado do video para editar facilmente.
    subfile.write_text(captions, encoding='utf-8-sig')
    # Colocamos uma copia na pasta temporaria para evitar escaping de caminho C:\ no filtro ffmpeg.
    with tempfile.TemporaryDirectory(prefix='liveclips_') as temp:
        tempdir = Path(temp)
        (tempdir / 'legendas.srt').write_text(captions, encoding='utf-8-sig')
        vfbase = (f'scale={config.OUTPUT_WIDTH}:{config.OUTPUT_HEIGHT}:'
                  'force_original_aspect_ratio=decrease,'
                  f'pad={config.OUTPUT_WIDTH}:{config.OUTPUT_HEIGHT}:'
                  '(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30')
        def cmd(with_subs: bool):
            video_filter = vfbase
            if with_subs and captions.strip():
                video_filter += ',subtitles=legendas.srt:force_style=\'FontName=Arial,FontSize=18,Outline=2,MarginV=45\''
            return [
                'ffmpeg', '-hide_banner', '-y', '-loglevel', 'error',
                '-ss', f'{start:.2f}', '-i', job['source'], '-t', f'{end-start:.2f}',
                '-map', '0:v:0', '-map', '0:a:0?',
                '-vf', video_filter, '-c:v', 'libx264', '-preset', config.ENCODE_PRESET,
                '-crf', '27', '-threads', config.FFMPEG_THREADS,
                '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart',
                str(outfile),
            ]
        p = subprocess.run(cmd(with_subs=True), cwd=tempdir, capture_output=True, text=True)
        if p.returncode:
            print('[AGENTE 2] Nao foi possivel embutir as legendas. '
                  'Tentando MP4 sem legendas embutidas...', flush=True)
            p = subprocess.run(cmd(with_subs=False), cwd=tempdir, capture_output=True, text=True)
        if p.returncode:
            outfile.unlink(missing_ok=True)
            raise RuntimeError('FFmpeg: ' + p.stderr[-1200:])
    titlefile.write_text(
        'Corte sugerido automaticamente (modo demonstracao)\n\n'
        f'Ponto: {start:.1f} a {end:.1f} segundos do arquivo original\n'
        f'Pontuacao por palavras e exclamacoes: {job["score"]}\n\n'
        'Transcricao do trecho:\n' + job['transcript'] + '\n\n'
        'IMPORTANTE: Revise audio, contexto, enquadramento e direitos antes de publicar.\n',
        encoding='utf-8-sig',
    )
    print('[AGENTE 2] PRONTO:', outfile, flush=True)


def run(folder: Path) -> None:
    out = session_output(folder)
    pending = out / 'fila' / 'pendentes'
    processing = out / 'fila' / 'processando'
    done = out / 'fila' / 'concluidos'
    errors = out / 'fila' / 'erros'
    print('\n[AGENTE 2] EDITOR CONTINUO', flush=True)
    print('Procurando na fila:', pending, flush=True)
    print('Cortes finais em:', out / 'cortes', flush=True)
    print('Esperando tarefas ... Ctrl+C para parar.', flush=True)
    while True:
        for path in sorted(pending.glob('*.json')):
            # Se um trabalho foi concluido antes de uma reinicializacao, nao o repita.
            final_file = out / 'cortes' / (path.stem + '_vertical.mp4')
            if (done / path.name).exists() and final_file.exists() and final_file.stat().st_size > 0:
                try:
                    path.unlink()
                    print(f'[AGENTE 2] Ignorando tarefa duplicada: {path.stem}', flush=True)
                except FileNotFoundError:
                    pass
                continue
            work = processing / path.name
            try:
                path.replace(work)
            except FileNotFoundError:
                continue
            try:
                job = read_json(work)
                print(f'\n[AGENTE 2] Editando {job["id"]}...', flush=True)
                render(job, out)
                work.replace(done / work.name)
            except Exception as exc:
                print('[ERRO editor]', exc, flush=True)
                traceback.print_exc()
                work.replace(errors / work.name)
        time.sleep(config.POLL_SECONDS)


if __name__ == '__main__':
    try:
        run(Path(sys.argv[1]))
    except KeyboardInterrupt:
        print('\n[AGENTE 2] Parado pelo usuario.')
    except Exception:
        traceback.print_exc()
        input('Pressione Enter para fechar (erro acima)...')
