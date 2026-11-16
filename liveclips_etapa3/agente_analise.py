"""Processo 1: espera trechos TS concluidos, faz STT com Whisper e enfileira cortes."""
from __future__ import annotations
import json
import sys
import time
import traceback
from pathlib import Path

import config
from comum import choose_clip, duration_seconds, ready_segments, save_json_atomic, session_output, read_json
from trava_sessao import trava


def recuperar_transcricoes(out):
    """Recupera a interrupcao entre salvar transcricao e enfileirar o corte."""
    for path in (out / 'transcricoes').glob('*.json'):
        if any((out / 'fila' / state / path.name).exists()
               for state in ('pendentes', 'processando', 'concluidos', 'erros')):
            continue
        result = read_json(path)
        if not Path(result['source']).is_file():
            continue
        clip = choose_clip(result['segments'], result['duration'])
        if clip:
            save_json_atomic(out / 'fila' / 'pendentes' / path.name,
                dict(clip, source=result['source'], transcription=str(path), id=path.stem))


def run(folder: Path) -> None:
    from faster_whisper import WhisperModel
    out = session_output(folder)
    recuperar_transcricoes(out)
    print('\n[AGENTE 1] ANALISE DE FALA + SUGESTAO DE CORTES', flush=True)
    print('Pasta de entrada:', folder, flush=True)
    print('Saida:', out, flush=True)
    print('Modelo:', config.WHISPER_MODEL, '| CPU int8 | sem APIs pagas', flush=True)
    print('Primeiro uso: o modelo de voz sera baixado gratuitamente.', flush=True)
    try:
        model = WhisperModel(config.WHISPER_MODEL, device='cpu', compute_type='int8',
                             cpu_threads=config.CPU_THREADS, num_workers=1)
    except Exception as exc:
        raise RuntimeError('Falha ao iniciar Faster-Whisper. Confira acesso a internet, Python 3.11, '
                           'Microsoft Visual C++ Redistributable e instrucoes do LEIA-ME.') from exc
    processed = {p.stem for p in (out / 'transcricoes').glob('*.json')}
    print('Esperando arquivos .ts completos... Ctrl+C para parar.', flush=True)
    while True:
        for src in ready_segments(folder, processed):
            print(f'\n[AGENTE 1] Transcrevendo {src.name}...', flush=True)
            try:
                duration = duration_seconds(src)
                started = time.monotonic()
                iterable, info = model.transcribe(str(src), language=config.LANGUAGE,
                    beam_size=1, best_of=1, vad_filter=False, condition_on_previous_text=False,
                    word_timestamps=True)
                segments = [{'start': round(float(s.start), 3),
                             'end': round(float(s.end), 3), 'text': s.text.strip(),
                             'words': [{'start': round(float(w.start), 3),
                                        'end': round(float(w.end), 3), 'word': w.word.strip()}
                                       for w in (s.words or [])]}
                            for s in iterable if s.text.strip()]
                result = {'source': str(src.resolve()), 'duration': round(duration, 2),
                          'language': info.language, 'segments': segments,
                          'elapsed_seconds': round(time.monotonic()-started, 1)}
                save_json_atomic(out / 'transcricoes' / (src.stem + '.json'), result)
                processed.add(src.stem)
                print(f'[AGENTE 1] Transcricao salva: {len(segments)} frases, '
                      f'{result["elapsed_seconds"]}s de processamento', flush=True)
                clip = choose_clip(segments, duration)
                if clip:
                    job = {'source': result['source'], 'transcription': str(out / 'transcricoes' / (src.stem + '.json')),
                           'start': clip['start'], 'end': clip['end'], 'score': clip['score'],
                           'transcript': clip['transcript'], 'id': src.stem}
                    save_json_atomic(out / 'fila' / 'pendentes' / (src.stem + '.json'), job)
                    print(f'[AGENTE 1] Corte sugerido: {clip["start"]:.1f}s–{clip["end"]:.1f}s '
                          f'(pontuacao {clip["score"]})', flush=True)
                else:
                    print('[AGENTE 1] Pouca fala detectada; sem corte neste trecho.', flush=True)
            except Exception as e:
                print(f'[ERRO analise] {src.name}: {e}', flush=True)
                traceback.print_exc()
                # Esperar, em vez de tentar em loop apertado. O arquivo pode estar incompleto.
                time.sleep(15)
        time.sleep(config.POLL_SECONDS)


if __name__ == '__main__':
    try:
        folder = Path(sys.argv[1])
        with trava(session_output(folder) / 'analise.lock'):
            run(folder)
    except KeyboardInterrupt:
        print('\n[AGENTE 1] Parado pelo usuario.')
    except Exception:
        traceback.print_exc()
        input('Pressione Enter para fechar (erro acima)...')
