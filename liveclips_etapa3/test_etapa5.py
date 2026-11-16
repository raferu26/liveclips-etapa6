"""Verifica entrega, retomada, falhas e exclusao mutua sem tocar em lives."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import config
import agente_edicao_tiktok as editor
import iniciar_etapa5 as launcher
from agente_analise import recuperar_transcricoes
from comum import session_output, save_json_atomic
from trava_sessao import trava


class FluxoTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.patcher = patch.object(config, 'OUTPUT', self.root / 'saida')
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.out = session_output(Path('sessao_teste'))

    def tarefa(self, state='pendentes'):
        path = self.out / 'fila' / state / 'segmento_00000.json'
        save_json_atomic(path, {'id': 'segmento_00000'})
        return path

    def render(self, job, out):
        target = out / 'cortes_tiktok'
        target.mkdir(exist_ok=True)
        (target / (job['id'] + '_tiktok.mp4')).write_bytes(b'render simulado')

    def test_entrega_e_nao_repete(self):
        self.tarefa()
        with patch.object(editor, 'render_tiktok', side_effect=self.render) as render:
            editor.processar(self.out)
            self.tarefa()
            editor.processar(self.out)
            self.assertEqual(render.call_count, 1)
        self.assertTrue((self.out / 'fila/concluidos/segmento_00000.json').exists())

    def test_retoma_interrompido(self):
        self.tarefa('processando')
        editor.recuperar(self.out)
        with patch.object(editor, 'render_tiktok', side_effect=self.render):
            editor.processar(self.out)
        self.assertTrue((self.out / 'fila/concluidos/segmento_00000.json').exists())

    def test_falha_preserva_tarefa(self):
        self.tarefa()
        with patch.object(editor, 'render_tiktok', side_effect=RuntimeError('falha simulada')):
            editor.processar(self.out)
        self.assertTrue((self.out / 'fila/erros/segmento_00000.json').exists())

    def test_recupera_transcricao_sem_retranscrever(self):
        source = self.root / 'segmento_00000.ts'
        source.write_bytes(b'teste')
        save_json_atomic(self.out / 'transcricoes/segmento_00000.json', {
            'source': str(source), 'duration': 60,
            'segments': [{'start': 2, 'end': 20, 'text': 'mano olha isso caramba nossa que jogada incrivel agora!'}]})
        recuperar_transcricoes(self.out)
        self.assertTrue((self.out / 'fila/pendentes/segmento_00000.json').exists())

    def test_trava_impede_segunda_instancia_e_libera(self):
        path = self.out / 'teste.lock'
        with trava(path):
            with self.assertRaises(RuntimeError):
                with trava(path):
                    pass
        with trava(path):
            pass

    def test_iniciador_separa_saida_e_transmite_aos_dois_agentes(self):
        session = self.root / 'segmentos' / 'sessao'
        session.mkdir(parents=True)
        (session / 'segmento_00000.ts').write_bytes(b'teste')
        old = self.root / 'agentes' / 'sessao' / 'perfil_tiktok.json'
        save_json_atomic(old, {'camera_rect': [0, 0, .2, .3]})
        original = old.read_bytes()
        with patch.object(config, 'ROOT', self.root), \
             patch.object(launcher, 'choose_session', return_value=session), \
             patch.object(launcher, 'configure_profile'), \
             patch.object(launcher.shutil, 'which', return_value='ferramenta'), \
             patch('builtins.input', return_value='s'), \
             patch.object(launcher.subprocess, 'Popen') as launch:
            launcher.main()
            self.assertEqual(launch.call_count, 2)
            for call in launch.call_args_list:
                self.assertEqual(call.kwargs['env']['LIVECLIPS_OUTPUT'],
                                 str(self.root / 'agentes_etapa5'))
        self.assertEqual(old.read_bytes(), original)
        self.assertEqual((self.root / 'agentes_etapa5/sessao/perfil_tiktok.json').read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
