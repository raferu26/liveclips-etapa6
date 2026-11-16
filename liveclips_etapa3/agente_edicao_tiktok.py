"""Editor TikTok da Etapa 4, consome fila do analisador existente."""
import sys
import time
import traceback
from pathlib import Path

import config
from comum import read_json, session_output
from layout_tiktok import render_tiktok
from trava_sessao import trava


def recuperar(out):
    """Recoloca trabalhos interrompidos na fila; chamada com trava exclusiva."""
    for item in (out / 'fila' / 'processando').glob('*.json'):
        pending = out / 'fila' / 'pendentes' / item.name
        if pending.exists():
            raise RuntimeError('Tarefa duplicada na fila: ' + item.name)
        item.replace(pending)
        print('[AGENTE 2] Retomando tarefa interrompida:', item.stem, flush=True)


def processar(out):
    pending = out / 'fila' / 'pendentes'
    processing = out / 'fila' / 'processando'
    done = out / 'fila' / 'concluidos'
    errors = out / 'fila' / 'erros'
    for item in sorted(pending.glob('*.json')):
        final = out / 'cortes_tiktok' / (item.stem + '_tiktok.mp4')
        if (done / item.name).exists() and final.exists() and final.stat().st_size > 0:
            item.unlink(missing_ok=True)
            continue
        working = processing / item.name
        try:
            item.replace(working)
        except FileNotFoundError:
            continue
        try:
            job = read_json(working)
            print('[AGENTE 2] Editando', job.get('id'), flush=True)
            render_tiktok(job, out)
            working.replace(done / working.name)
        except Exception as exc:
            print('[ERRO EDITOR TIKTOK]', exc, flush=True)
            traceback.print_exc()
            working.replace(errors / working.name)


def run(folder: Path):
    out = session_output(folder)
    print('[AGENTE 2] EDITOR TIKTOK - 720x1280, webcam em cima, jogo embaixo', flush=True)
    print('Fila:', out / 'fila' / 'pendentes', flush=True)
    print('Saida:', out / 'cortes_tiktok', flush=True)
    print('Esperando tarefas... Ctrl+C encerra.', flush=True)
    with trava(out / 'editor_tiktok.lock'):
        recuperar(out)
        while True:
            processar(out)
            time.sleep(config.POLL_SECONDS)


if __name__ == '__main__':
    try:
        run(Path(sys.argv[1]))
    except KeyboardInterrupt:
        print('[AGENTE 2] Interrompido.')
    except Exception:
        traceback.print_exc()
        input('Pressione Enter para fechar...')
