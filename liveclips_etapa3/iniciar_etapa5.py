"""Etapa 5: analise e edicao TikTok continua em uma saida independente."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import config
from iniciar_tiktok import choose_session
from layout_tiktok import configure_profile
from comum import session_output


def main():
    print('LIVECLIPS - ETAPA 5 - LIVE PARA TIKTOK')
    print('Inicie a captura da etapa 2 e aguarde o primeiro segmento completo.')
    for executable in ('ffmpeg', 'ffprobe'):
        if not shutil.which(executable):
            raise RuntimeError(executable + ' nao encontrado no PATH. Reabra o terminal apos instalar.')
    folder = choose_session()
    if not list(folder.glob('segmento_*.ts')):
        raise RuntimeError('Aguarde o primeiro segmento da captura e tente novamente.')
    config.OUTPUT = config.ROOT / 'agentes_etapa5'
    out = session_output(folder)
    profile = out / 'perfil_tiktok.json'
    previous = config.ROOT / 'agentes' / folder.name / 'perfil_tiktok.json'
    if not profile.exists() and previous.is_file():
        shutil.copy2(previous, profile)
        print('Perfil anterior copiado para a etapa 5. Confira se e a mesma live.')
    configure_profile(folder)
    print('Saida independente:', out)
    print('A etapa 5 analisara os segmentos desta sessao, inclusive os ja gravados.')
    print('Depois, os novos segmentos serao processados automaticamente.')
    if input('Iniciar analise e editor TikTok? [S/N]: ').strip().lower() not in ('s', 'sim'):
        return
    env = os.environ.copy()
    env['LIVECLIPS_OUTPUT'] = str(config.OUTPUT)
    flags = subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
    children = []
    try:
        for script in ('agente_analise.py', 'agente_edicao_tiktok.py'):
            children.append(subprocess.Popen(
                [sys.executable, str(Path(__file__).with_name(script)), str(folder)],
                env=env, creationflags=flags))
    except OSError:
        for child in children:
            child.terminate()
            child.wait()
        raise
    print('Agentes iniciados. Mantenha a captura aberta para receber segmentos novos.')
    print('MP4 e SRT:', out / 'cortes_tiktok')
    print('Para parar: Ctrl+C em cada janela. Para retomar: execute este iniciador novamente.')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Cancelado.')
    except Exception as exc:
        print('ERRO:', exc)
        input('Pressione Enter para sair...')
