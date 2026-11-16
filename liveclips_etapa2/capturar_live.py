#!/usr/bin/env python3
"""Etapa 2 do LiveClips: gravacao continua de live em segmentos TS.

Somente captura: nao analisa conteudo, nao usa APIs e nao publica nada.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
import shutil
import subprocess
import sys

LIVE_PADRAO = "https://www.youtube.com/live/3McEJfR_oig"
PASTA_BASE = Path(r"C:\LiveClips") if sys.platform == "win32" else Path.home() / "LiveClips"
SEGUNDOS_POR_SEGMENTO = 60


def main() -> int:
    print("=" * 58)
    print(" LIVECLIPS | ETAPA 2 - CAPTURA CONTINUA EM SEGMENTOS")
    print("=" * 58)
    print("Gratuito: nenhuma API ou assinatura e utilizada.\n")

    faltando = [cmd for cmd in ("streamlink", "ffmpeg") if not shutil.which(cmd)]
    if faltando:
        print("ERRO: programa(s) nao encontrado(s):", ", ".join(faltando))
        print("Feche e abra o terminal depois de instalar os programas.")
        return 1

    print("Link da live usado no teste anterior:")
    print(LIVE_PADRAO)
    try:
        entrada = input("Cole outro link, ou pressione Enter para usar este: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nOperacao cancelada.")
        return 0
    url = entrada or LIVE_PADRAO
    if not url.lower().startswith(("https://", "http://")):
        print("ERRO: cole um link que comece com https:// ou http://")
        return 1

    pasta = PASTA_BASE / "segmentos" / dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    try:
        pasta.mkdir(parents=True, exist_ok=False)
    except OSError as erro:
        print(f"Nao foi possivel criar a pasta de saida: {erro}")
        return 1

    print("\nPasta de saida:", pasta)
    print("Um novo arquivo .ts sera finalizado aproximadamente a cada 60 segundos.")
    print("O tempo exato depende dos quadros-chave da transmissao.")
    print("Deixe rodando por 2 a 3 minutos para testar.")
    print("Pressione Ctrl+C para encerrar. Nao feche o PC durante a captura.\n")

    # Nao usa PowerShell para encadear dados binarios. A conexao entre
    # os processos e um pipe binario direto, evitando corromper o stream.
    cmd_streamlink = ["streamlink", "--stdout", url, "best"]
    cmd_ffmpeg = [
        "ffmpeg", "-hide_banner", "-loglevel", "warning", "-fflags", "+genpts",
        "-i", "pipe:0", "-map", "0:v:0?", "-map", "0:a:0?", "-c", "copy",
        "-f", "segment", "-segment_time", str(SEGUNDOS_POR_SEGMENTO),
        "-segment_format", "mpegts", "-reset_timestamps", "1",
        str(pasta / "segmento_%05d.ts"),
    ]

    produtor = None
    editor = None
    try:
        produtor = subprocess.Popen(cmd_streamlink, stdout=subprocess.PIPE)
        assert produtor.stdout is not None
        editor = subprocess.Popen(cmd_ffmpeg, stdin=produtor.stdout)
        # O pai nao precisa manter uma copia do pipe aberta.
        produtor.stdout.close()
        codigo_ffmpeg = editor.wait()
        codigo_streamlink = produtor.wait(timeout=10)
        if codigo_ffmpeg != 0 or codigo_streamlink != 0:
            print("\nATENCAO: uma ferramenta encerrou com erro.")
            print("streamlink:", codigo_streamlink, "| ffmpeg:", codigo_ffmpeg)
    except KeyboardInterrupt:
        print("\nEncerrando captura...")
    except (OSError, subprocess.TimeoutExpired) as erro:
        print("\nERRO:", erro)
    finally:
        if produtor is not None and produtor.poll() is None:
            produtor.terminate()
            try:
                produtor.wait(timeout=6)
            except subprocess.TimeoutExpired:
                produtor.kill()
                produtor.wait()
        if editor is not None and editor.poll() is None:
            try:
                editor.wait(timeout=8)  # espera o fim do pipe e finaliza o .ts
            except subprocess.TimeoutExpired:
                editor.terminate()
                try:
                    editor.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    editor.kill()
                    editor.wait()

    arquivos = sorted(pasta.glob("segmento_*.ts"))
    print("\nArquivos gerados:", len(arquivos))
    if arquivos:
        for arq in arquivos[:5]:
            print(" -", arq.name, f"({arq.stat().st_size / 1024 / 1024:.1f} MB)")
        if len(arquivos) > 5:
            print(f" - ... e mais {len(arquivos) - 5} arquivo(s)")
        print("\nPasta:", pasta)
        print("Para abrir, copie o caminho acima no Explorador de Arquivos.")
        return 0

    print("Nenhum segmento apareceu. Confira se a live ainda esta ativa")
    print("e copie qualquer mensagem de erro exibida acima.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
