"""Inicia analisador da Etapa 3 + novo editor TikTok, com perfil de webcam."""
import os
import subprocess
import sys
from pathlib import Path

import config
from layout_tiktok import configure_profile


def choose_session():
    sessions = [p for p in config.SESSIONS.iterdir() if p.is_dir()] if config.SESSIONS.exists() else []
    if not sessions:
        raise RuntimeError('Nao ha sessoes em C:\\LiveClips\\segmentos. Grave uma live primeiro.')
    def order(p):
        fs = list(p.glob('segmento_*.ts'))
        return max((x.stat().st_mtime for x in fs), default=p.stat().st_mtime)
    sessions.sort(key=order, reverse=True)
    print('SESSOES DISPONIVEIS:')
    for i, folder in enumerate(sessions[:8], 1):
        print(f'  {i}. {folder.name} ({len(list(folder.glob("segmento_*.ts")))} arquivos)')
    num = input('Numero da sessao [Enter = 1]: ').strip() or '1'
    if not num.isdigit() or not 1 <= int(num) <= min(8, len(sessions)):
        raise ValueError('Numero de sessao invalido.')
    return sessions[int(num)-1]


def main():
    print('=' * 60)
    print('LIVECLIPS - ETAPA 4 - EDITOR TIKTOK MANUAL')
    print('=' * 60)
    print('Nenhuma API paga. Editor original permanece disponivel.')
    folder = choose_session()
    configure_profile(folder)
    print('\nATENCAO: feche as janelas antigas dos agentes, se estiverem abertas.')
    print('Novo analisador e editor TikTok vao operar em paralelo.')
    ans = input('Iniciar os DOIS agentes? [S/N]: ').strip().lower()
    if ans not in ('s', 'sim'):
        return
    for script in ('agente_analise.py', 'agente_edicao_tiktok.py'):
        kwargs = {'creationflags': subprocess.CREATE_NEW_CONSOLE} if os.name == 'nt' else {}
        subprocess.Popen([sys.executable, str(Path(__file__).with_name(script)), str(folder)], **kwargs)
    print('Agentes iniciados. Para parar, Ctrl+C em cada janela.')
    print('Cortes novos em:', config.OUTPUT / folder.name / 'cortes_tiktok')
    print('Se a sessao for antiga, o analisador nao repetira arquivos ja processados.')
    print('Use TESTAR_LAYOUT_TIKTOK.bat para gerar uma previa com arquivos antigos.')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nCancelado.')
    except Exception as e:
        print('\nERRO:', e)
        input('Pressione Enter para fechar...')
