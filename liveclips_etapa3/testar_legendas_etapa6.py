"""Previa de 12s com palavras alinhadas, usando uma gravacao existente."""
import shutil
import subprocess
import tempfile
from pathlib import Path

import config
from comum import save_json_atomic, session_output, duration_seconds
from iniciar_tiktok import choose_session
from layout_tiktok import configure_profile, render_tiktok


def main():
    from faster_whisper import WhisperModel
    print('ETAPA 6 - COMPARAR LEGENDAS EM ATE 12 SEGUNDOS')
    for name in ('ffmpeg', 'ffprobe'):
        if not shutil.which(name):
            raise RuntimeError(name + ' nao encontrado no PATH.')
    folder = choose_session()
    config.OUTPUT = config.ROOT / 'agentes_etapa6'
    out = session_output(folder)
    profile = out / 'perfil_tiktok.json'
    previous = config.ROOT / 'agentes_etapa5' / folder.name / profile.name
    if not profile.exists() and previous.is_file():
        shutil.copy2(previous, profile)
    configure_profile(folder)
    sources = sorted(folder.glob('segmento_*.ts'))[:10]
    if not sources:
        raise RuntimeError('Nenhum segmento nesta sessao.')
    for i, path in enumerate(sources, 1):
        print(i, path.name)
    answer = input('Segmento para previa [Enter = 1]: ').strip() or '1'
    if not answer.isdigit() or not 1 <= int(answer) <= len(sources):
        raise ValueError('Numero invalido.')
    source = sources[int(answer)-1]
    duration = min(12.0, duration_seconds(source))
    with tempfile.TemporaryDirectory(prefix='liveclips_legendas_') as temp:
        audio = Path(temp) / 'audio.wav'
        cp = subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
            '-i', str(source), '-t', str(duration), '-vn', '-ac', '1', '-ar', '16000', str(audio)],
            capture_output=True, text=True)
        if cp.returncode:
            raise RuntimeError('Falha ao extrair audio: ' + cp.stderr[-800:])
        print('Transcrevendo a previa com tempos por palavra. Aguarde...')
        model = WhisperModel(config.WHISPER_MODEL, device='cpu', compute_type='int8',
                             cpu_threads=config.CPU_THREADS, num_workers=1)
        iterable, _ = model.transcribe(str(audio), language=config.LANGUAGE, beam_size=1,
            best_of=1, vad_filter=False, condition_on_previous_text=False, word_timestamps=True)
        segments = [{'start': float(s.start), 'end': float(s.end), 'text': s.text.strip(),
                     'words': [{'start': float(w.start), 'end': float(w.end), 'word': w.word.strip()}
                               for w in (s.words or [])]} for s in iterable if s.text.strip()]
    if not segments:
        raise RuntimeError('Nao houve fala reconhecida nesses 12s. Teste outro segmento.')
    trans = out / 'previas' / (source.stem + '_transcricao.json')
    save_json_atomic(trans, {'segments': segments})
    result = render_tiktok({'id': source.stem, 'source': str(source), 'start': 0,
                            'end': duration, 'transcription': str(trans)}, out, preview=True)
    print('PREVIA DA ETAPA 6:', result)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Cancelado.')
    except Exception as exc:
        print('ERRO:', exc)
    input('Pressione Enter para sair...')
