# LiveClips — etapa 6 (v0.6)

Checkpoint da etapa 6, com prévia das legendas executada no Windows e aprovada pelo usuário. Os scripts foram copiados da pasta AGENTE CLIPADOR V4 usada no teste.

## Primeiro teste: sem precisar abrir uma live
1. Extraia este ZIP em uma pasta nova, por exemplo AGENTE CLIPADOR V4.
2. Abra liveclips_etapa3 e dê dois cliques em TESTAR_LEGENDAS_ETAPA6.bat. Abra o arquivo .bat, não o .py.
3. Escolha a sessão 2026-11-15_20-39-33 já gravada.
4. Se o perfil da etapa 5 for encontrado, pressione Enter para reutilizar o enquadramento aprovado.
5. Escolha o segmento desejado (Enter = primeiro). O programa extrai e transcreve até 12 segundos, gera os tempos das palavras e renderiza uma prévia. Aguarde, pois o processamento usa CPU.
6. Abra C:\LiveClips\agentes_etapa6\2026-11-15_20-39-33\cortes_tiktok e procure o MP4 com PREVIA no nome.
7. Confira tamanho, posição, leitura e sincronização da palavra amarela. Se não reconhecer fala nos primeiros 12 segundos, selecione outro segmento.

O iniciador usa a .venv existente em OneDrive\Desktop\liveclips_etapa3 quando disponível. Se ela não existir, execute INSTALAR_ETAPA3.bat nesta pasta nova. FFmpeg e ffprobe precisam estar no PATH.

## Fluxo automático
Depois de aprovar a prévia, execute INICIAR_ETAPA6.bat. Selecione a sessão e confirme os agentes. A etapa 6 transcreve os segmentos com tempos por palavra e gera os cortes na saída própria agentes_etapa6. Na primeira execução também processa segmentos antigos da sessão, o que pode demorar. Para novos segmentos ao vivo, mantenha a captura da etapa 2 aberta.

Pare as janelas dos agentes anteriores antes de testar para poupar CPU. Para encerrar, Ctrl+C em cada agente; aguarde o editor concluir o vídeo antes de pará-lo. Não substitua a pasta da etapa 5.

## Legendas
- ASS em 720x1280, Arial 46, texto branco com contorno escuro e palavra ativa amarela.
- Grupos curtos de até quatro palavras, limitados também pelo comprimento e por pausas. Textos muito longos quebram automaticamente conforme o renderizador.
- Legendas na área inferior da gameplay, com margem lateral e inferior para reduzir conflito com a interface do aplicativo. Confira essa posição no seu celular; não existe garantia de margem universal para todas as interfaces.
- O transcritor fornece tempos estimados por palavra. Podem ocorrer erros de reconhecimento e sincronização.
- Transcrições antigas sem palavras alinhadas mostram frases sem destaque, com divisão aproximada quando necessário. A prévia e os novos trabalhos da etapa 6 solicitam alinhamento por palavra.
- SRT e ASS ficam ao lado do MP4 para edição posterior.
- Se o filtro de legendas do FFmpeg falhar, a tarefa fica em erros. Esta versão não entrega silenciosamente um MP4 sem as legendas solicitadas.

O alinhamento por palavra pode aumentar o tempo de transcrição. O modelo tiny e as regras de seleção de trechos foram mantidos. Não foram adicionadas APIs pagas ou novas bibliotecas.

## Validação
14 testes automatizados passaram: fluxo e retomada da etapa 5, tempos relativos no corte, pausas sem destaque, compatibilidade com transcrição antiga, proteção contra comandos ASS no texto, frases curtas, falha explícita de renderização, saída isolada e prévia de 12 segundos com alinhamento por palavra. A sintaxe dos 16 scripts Python da pasta de agentes foi verificada. A biblioteca instalada oferece word_timestamps.

O usuário gerou a prévia segmento_00000_PREVIA.mp4 da sessão 2026-11-15_20-39-33 e aprovou o resultado. Foram encontrados MP4, ASS e SRT correspondentes na saída da etapa 6. Essa validação visual cobre a prévia; a execução contínua completa da etapa 6 ainda precisa de avaliação. Os 14 testes automatizados da preparação passaram com simulação de renderização/transcrição. Nenhum vídeo existente foi alterado.

O backup funcional v0.5 permanece em https://github.com/raferu26/liveclips-etapa5. Esta versão v0.6 foi autorizada para backup após a aprovação da prévia. O perfil aprovado está em configuracoes/perfil_tiktok.json; para restaurá-lo na mesma sessão, copie para C:\LiveClips\agentes_etapa6\2026-11-15_20-39-33\perfil_tiktok.json. Para outra live, configure novamente. Vídeos, segmentos, transcrições, filas, .venv e credenciais ficam fora deste backup.

