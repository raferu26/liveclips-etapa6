"""Gera previa TikTok de um arquivo gravado (nao precisa live em andamento)."""
from pathlib import Path

import config
from comum import session_output, read_json
from iniciar_tiktok import choose_session
from layout_tiktok import configure_profile, render_tiktok, video_dimensions


def main():
    print('LIVECLIPS - PREVIA DO LAYOUT TIKTOK (SEM LIVE AO VIVO)')
    folder = choose_session()
    sources = sorted(folder.glob('segmento_*.ts'))
    if not sources:
        raise RuntimeError('Nao ha arquivos .ts na sessao selecionada.')
    out = session_output(folder)
    configure_profile(folder)
    print('SEGMENTOS PARA PREVIA:')
    for i, s in enumerate(sources[:10], 1):
        print(f'  {i}. {s.name}')
    n = input('Numero do segmento [Enter = 1]: ').strip() or '1'
    if not n.isdigit() or not 1 <= int(n) <= min(10, len(sources)):
        raise ValueError('Numero invalido.')
    source = sources[int(n)-1]
    transcription = out / 'transcricoes' / (source.stem + '.json')
    duration = 12.0
    if transcription.exists():
        trans = read_json(transcription)
        duration = min(12.0, max(3.0, float(trans.get('duration', 12.0))))
    print('Gerando demonstracao de ate', duration, 'segundos... pode demorar no PC antigo.')
    job = {'id': source.stem, 'source': str(source),
           'transcription': str(transcription) if transcription.exists() else '',
           'start': 0.0, 'end': duration}
    result = render_tiktok(job, out, preview=True)
    print('PREVIA GERADA:', result)
    print('Abra o arquivo na pasta indicada. Nenhum video antigo foi apagado.')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Cancelado.')
    except Exception as e:
        print('ERRO:', e)
    input('Pressione Enter para sair...')
