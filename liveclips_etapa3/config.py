"""LiveClips etapa 3 - configuracoes simples, sem API e sem pagamentos."""
from pathlib import Path
import os

ROOT = Path(os.environ.get('LIVECLIPS_ROOT', r'C:\LiveClips' if os.name == 'nt' else '/tmp/LiveClips'))
SESSIONS = ROOT / 'segmentos'
OUTPUT = Path(os.environ.get('LIVECLIPS_OUTPUT', str(ROOT / 'agentes')))

# Transcritor IA: tiny e o mais leve; base tem mais qualidade e demanda mais CPU.
WHISPER_MODEL = os.environ.get('LIVECLIPS_MODEL', 'tiny')
LANGUAGE = None  # None = autodeteccao, ou use 'pt' / 'en'
CPU_THREADS = 3

# Modo teste: gera no maximo 1 corte por segmento com fala detectada.
# A classificacao e por REGRAS simples, NAO um modelo semantico de highlights.
CLIPS_PER_SEGMENT = 1
MIN_WORDS = 8
CUT_SECONDS = 32

# Qualidade reduzida para PC antigo. Mantem quadro completo, com faixas laterais/superiores.
OUTPUT_WIDTH = 480
OUTPUT_HEIGHT = 854
ENCODE_PRESET = 'ultrafast'
FFMPEG_THREADS = '3'
POLL_SECONDS = 4

KEYWORDS = {
    'caramba', 'nossa', 'meu deus', 'impossivel', 'incrivel', 'vitoria',
    'ganhei', 'matei', 'quase', 'mano', 'olha isso', 'nao acredito',
    'absurdo', 'clutch', 'win', 'victory', 'eliminated', 'knocked',
    'no way', 'oh my god', 'omg', 'wow', 'insane', 'crazy', 'look at',
}
