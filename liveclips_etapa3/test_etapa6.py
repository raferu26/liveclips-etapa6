import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from legendas_dinamicas import make_ass, grupos
from comum import save_json_atomic
from comum import read_json
import layout_tiktok
import iniciar_etapa6
import testar_legendas_etapa6
import config


class LegendasTest(unittest.TestCase):
    def segment(self):
        return {'start': 10, 'end': 13, 'text': 'olha essa jogada', 'words': [
            {'start': 10, 'end': 10.4, 'word': 'olha'},
            {'start': 10.6, 'end': 11, 'word': 'essa'},
            {'start': 11, 'end': 13, 'word': 'jogada'}]}

    def test_tempos_relativos_e_palavra_destacada(self):
        result = make_ass([self.segment()], 10.2, 11.5)
        lines = [line for line in result.splitlines() if line.startswith('Dialogue')]
        self.assertEqual(len(lines), 4)  # tres palavras + pausa sem destaque
        self.assertIn('0:00:00.00,0:00:00.20', lines[0])
        self.assertIn(r'{\c&H00E8FF&}olha', lines[0])
        self.assertNotIn(r'\c', lines[1])
        self.assertIn('0:00:00.80,0:00:01.30', lines[-1])

    def test_fala_fora_do_corte_nao_aparece(self):
        self.assertNotIn('Dialogue:', make_ass([self.segment()], 20, 30))

    def test_sem_tempos_nao_inventa_destaque(self):
        seg = self.segment()
        del seg['words']
        result = make_ass([seg], 10, 13)
        self.assertIn('olha essa jogada', result)
        self.assertNotIn(r'\c&H00E8FF&', result)

    def test_texto_nao_injeta_comandos_ass(self):
        seg = {'start': 0, 'end': 2, 'text': r'{\pos(0,0)} teste'}
        result = make_ass([seg], 0, 2)
        self.assertNotIn(r'{\pos', result)
        self.assertIn('｛', result)

    def test_grupos_curtos_e_pausas(self):
        words = [{'start': i, 'end': i+.9, 'text': 'mano'} for i in range(9)]
        self.assertEqual([len(g) for g in grupos(words)], [4, 4, 1])
        words[-1]['start'] = 20
        self.assertEqual(len(list(grupos(words))[-1]), 1)

    def test_falha_de_legenda_nao_entrega_mp4_sem_legenda(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            source = out / 'entrada.ts'
            source.write_bytes(b'teste')
            save_json_atomic(out / 'perfil_tiktok.json', {})
            trans = out / 'trans.json'
            save_json_atomic(trans, {'segments': [self.segment()]})
            with patch.object(layout_tiktok, 'camera_pixels', return_value=(100, 100, 0, 0)), \
                 patch.object(layout_tiktok.subprocess, 'run', return_value=SimpleNamespace(
                     returncode=1, stderr='No such filter: ass')) as run:
                with self.assertRaisesRegex(RuntimeError, 'FFmpeg falhou'):
                    layout_tiktok.render_tiktok({'source': str(source), 'id': 'teste',
                        'start': 10, 'end': 13, 'transcription': str(trans)}, out)
                self.assertEqual(run.call_count, 1)
                self.assertIn('ass=legendas.ass', ' '.join(run.call_args.args[0]))
                self.assertTrue((out / 'cortes_tiktok/teste_tiktok.ass').exists())

    def test_etapa6_isolada_e_perfil_da_etapa5_preservado(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            session = root / 'segmentos/sessao'
            session.mkdir(parents=True)
            (session / 'segmento_00000.ts').write_bytes(b'teste')
            original = root / 'agentes_etapa5/sessao/perfil_tiktok.json'
            save_json_atomic(original, {'camera_rect': [0, 0, .2, .3]})
            content = original.read_bytes()
            with patch.object(config, 'ROOT', root), patch.object(config, 'OUTPUT', root / 'out'), \
                 patch.object(iniciar_etapa6, 'choose_session', return_value=session), \
                 patch.object(iniciar_etapa6, 'configure_profile'), \
                 patch.object(iniciar_etapa6.shutil, 'which', return_value='ferramenta'), \
                 patch('builtins.input', return_value='s'), \
                 patch.object(iniciar_etapa6.subprocess, 'Popen') as launch:
                iniciar_etapa6.main()
                self.assertEqual(launch.call_count, 2)
                for call in launch.call_args_list:
                    self.assertEqual(call.kwargs['env']['LIVECLIPS_OUTPUT'], str(root / 'agentes_etapa6'))
            self.assertEqual(original.read_bytes(), content)

    def test_previa_transcreve_apenas_12s_com_tempos_por_palavra(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            session = root / 'segmentos/sessao'
            session.mkdir(parents=True)
            (session / 'segmento_00000.ts').write_bytes(b'teste')
            segment = SimpleNamespace(start=0, end=1, text='teste', words=[
                SimpleNamespace(start=0, end=1, word='teste')])
            with patch.object(config, 'ROOT', root), patch.object(config, 'OUTPUT', root / 'out'), \
                 patch.object(testar_legendas_etapa6, 'choose_session', return_value=session), \
                 patch.object(testar_legendas_etapa6, 'configure_profile'), \
                 patch.object(testar_legendas_etapa6, 'duration_seconds', return_value=60), \
                 patch.object(testar_legendas_etapa6.shutil, 'which', return_value='ferramenta'), \
                 patch.object(testar_legendas_etapa6.subprocess, 'run', return_value=SimpleNamespace(returncode=0)) as ffmpeg, \
                 patch('faster_whisper.WhisperModel') as model, \
                 patch.object(testar_legendas_etapa6, 'render_tiktok') as render, \
                 patch('builtins.input', return_value='1'):
                model.return_value.transcribe.return_value = (iter([segment]), None)
                testar_legendas_etapa6.main()
                self.assertTrue(model.return_value.transcribe.call_args.kwargs['word_timestamps'])
                command = ffmpeg.call_args.args[0]
                self.assertEqual(command[command.index('-t')+1], '12.0')
                job = render.call_args.args[0]
                self.assertEqual(job['end'], 12)
                self.assertEqual(read_json(Path(job['transcription']))['segments'][0]['words'][0]['word'], 'teste')


if __name__ == '__main__':
    unittest.main()
