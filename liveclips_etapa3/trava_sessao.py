"""Uma instancia de cada agente por pasta de saida; liberada pelo SO ao sair."""
from contextlib import contextmanager


@contextmanager
def trava(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as handle:
        handle.seek(0, 2)
        if handle.tell() == 0:
            handle.write(b'0')
            handle.flush()
        handle.seek(0)
        try:
            import msvcrt
        except ImportError:
            import fcntl
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise RuntimeError('Este agente ja esta aberto nesta sessao.') from exc
        else:
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise RuntimeError('Este agente ja esta aberto nesta sessao.') from exc
        # Fechar o arquivo libera a trava mesmo apos falha ou Ctrl+C.
        yield
