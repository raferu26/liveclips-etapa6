"""Abre os dois agentes em janelas independentes do Windows."""
import os
import subprocess
import sys
from pathlib import Path

import config


def main() -> int:
    print('=' * 64)
    print('LIVECLIPS | ETAPA 3 - DOIS AGENTES EM PARALELO')
    print('=' * 64)
    print('Sem API paga. Sua captura da etapa 2 permanece independente.\n')
    sessions = [p for p in config.SESSIONS.iterdir() if p.is_dir()] if config.SESSIONS.exists() else []
    if not sessions:
        print('Nenhuma pasta de segmentos em:', config.SESSIONS)
        print('Execute a captura da etapa 2 para produzir os arquivos .ts.')
        return 1
    def last_change(folder):
        files = list(folder.glob('segmento_*.ts'))
        return max((p.stat().st_mtime for p in files), default=folder.stat().st_mtime)
    sessions.sort(key=last_change, reverse=True)
    print('As sessoes mais recentes sao:')
    for i, p in enumerate(sessions[:8], 1):
        count = len(list(p.glob('segmento_*.ts')))
        print(f' {i}. {p.name} ({count} arquivos)')
    chosen = input('\nNumero da sessao [Enter = 1]: ').strip() or '1'
    if not chosen.isdigit() or not 1 <= int(chosen) <= min(len(sessions), 8):
        print('Numero invalido.')
        return 1
    session = sessions[int(chosen) - 1]
    print('\nSera monitorada a pasta:', session)
    print('Abriremos DUAS janelas que continuarao funcionando em paralelo.')
    print('Mantenha a captura da etapa 2 aberta, se a live ainda estiver acontecendo.')
    resp = input('Iniciar os dois agentes? (S/N): ').strip().lower()
    if resp not in ('s', 'sim'):
        return 0
    for script in ('agente_analise.py', 'agente_edicao.py'):
        kwargs = {'creationflags': subprocess.CREATE_NEW_CONSOLE} if os.name == 'nt' else {}
        subprocess.Popen([sys.executable, str(Path(__file__).with_name(script)), str(session)], **kwargs)
    print('\nAgentes abertos! As janelas sao independentes.')
    print('Para parar cada agente: Ctrl+C na respectiva janela.')
    print('Cortes finais em:', config.OUTPUT / session.name / 'cortes')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print('\nCancelado.')
