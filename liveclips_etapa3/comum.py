"""Funcoes compartilhadas; usa apenas a biblioteca padrao do Python."""
from __future__ import annotations
import json
import re
import subprocess
import time
from pathlib import Path
import config


def session_output(folder: Path) -> Path:
    d = config.OUTPUT / folder.name
    for p in ('transcricoes', 'fila/pendentes', 'fila/processando',
              'fila/concluidos', 'fila/erros', 'cortes'):
        (d / p).mkdir(parents=True, exist_ok=True)
    return d


def save_json_atomic(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp.replace(path)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def duration_seconds(path: Path) -> float:
    cp = subprocess.run([
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1', str(path),
    ], capture_output=True, text=True, timeout=35)
    if cp.returncode:
        raise RuntimeError(f'ffprobe falhou em {path.name}: {cp.stderr[-500:]}')
    return float(cp.stdout.strip())


def srt_time(t: float) -> str:
    millis = max(0, int(round(t * 1000)))
    hours, millis = divmod(millis, 3600000)
    minutes, millis = divmod(millis, 60000)
    seconds, millis = divmod(millis, 1000)
    return f'{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}'


def make_srt(segments: list[dict], start: float, end: float) -> str:
    lines = []
    idx = 0
    for seg in segments:
        a = max(start, float(seg['start']))
        b = min(end, float(seg['end']))
        if b <= a + .12:
            continue
        text = re.sub(r'\s+', ' ', str(seg['text'])).strip()
        if not text:
            continue
        idx += 1
        lines.extend([str(idx), f'{srt_time(a-start)} --> {srt_time(b-start)}', text, ''])
    return '\n'.join(lines) + ('\n' if lines else '')


def pretty(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()


def score_text(text: str, seconds: float) -> float:
    low = text.casefold()
    words = len(low.split())
    keywords = sum(1 for keyword in config.KEYWORDS if keyword in low)
    excitement = text.count('!') * 1.8 + text.count('?') * .5
    words_per_sec = words / max(seconds, 1.0)
    return round(keywords * 4.0 + excitement + min(words, 30) * .04 + min(words_per_sec, 3.0), 2)


def choose_clip(segments: list[dict], length: float) -> dict | None:
    if length < 12 or len(' '.join(s['text'] for s in segments).split()) < config.MIN_WORDS:
        return None
    best = None
    # Cada ponto de inicio de fala vira um candidato com ate CUT_SECONDS.
    for seg in segments:
        start = max(0.0, float(seg['start']) - 2.0)
        end = min(length, start + config.CUT_SECONDS)
        if end - start < 10:
            continue
        included = [s for s in segments if float(s['start']) < end and float(s['end']) > start]
        text = pretty(' '.join(s['text'] for s in included))
        if len(text.split()) < config.MIN_WORDS:
            continue
        score = score_text(text, end - start)
        if best is None or score > best['score']:
            best = {'start': round(start, 2), 'end': round(end, 2), 'score': score,
                    'transcript': text}
    return best


def ready_segments(folder: Path, done: set[str]) -> list[Path]:
    files = sorted(folder.glob('segmento_*.ts'))
    if not files:
        return []
    now = time.time()
    newest = files[-1]
    ready = []
    for p in files:
        if p.stem in done:
            continue
        st = p.stat()
        if st.st_size < 128_000:
            continue
        # O segmento mais novo pode estar aberto; aguarde 25s de inatividade.
        # Os anteriores estao fechados pelo FFmpeg e basta evitar corrida de escrita.
        wait = 25 if p == newest else 3
        if now - st.st_mtime >= wait:
            ready.append(p)
    return ready
