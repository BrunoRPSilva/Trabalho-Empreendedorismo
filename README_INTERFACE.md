# PONTE — Interface gráfica com câmera real (PySide6)

Interface desktop do PONTE com captura de webcam via OpenCV, inclusive câmeras virtuais de celulares reconhecidas pelo Windows 11. **A tradução com Gemini e a reprodução de voz ainda não estão integradas**: o botão de simular tradução insere frases de exemplo.

## Arquivos

- `interface.py`: janela desktop com transmissão de webcam, texto, histórico, botões e configurações.
- `requirements-interface.txt`: bibliotecas PySide6 e OpenCV.
- `assets/ponte_icon.png`: ícone do programa.
- `assets/camera_exemplo.jpg`: imagem do template antigo (a interface atual não usa essa foto).
- `teste_camera.py`: teste independente da webcam existente no repositório.

A interface não altera `main.py`, `ai_service.py` ou `voice_service.py`.

## Iniciar com dois cliques no Windows

1. Instale **Python 3.10 ou superior** no computador. No dia da apresentacao, confirme antes que a camera do celular esta conectada ao Windows e feche o aplicativo Camera para liberar o dispositivo.
2. Na pasta raiz do projeto, clique duas vezes em **`Iniciar_PONTE.bat`**.
3. O script cria `.venv` se necessario, verifica as bibliotecas, instala as que faltarem usando `requirements.txt` e abre `interface.py`.
4. A **primeira execucao precisa de internet** para baixar pacotes. Depois, se o ambiente e as bibliotecas ja estiverem instalados, pode iniciar sem internet. A traducao pelo Gemini ainda nao esta conectada a interface.
5. Clique em **Iniciar** na janela para ativar a webcam. Se nao abrir, pause outros programas que estejam usando a camera e ajuste o indice em **Configuracoes**.

O iniciador **nao instala o Python nem configura a chave da API**. Ele abre somente o front-end atual; nao execute `main.py` ao mesmo tempo porque ambos podem tentar abrir a mesma camera. Se o arquivo nao iniciar por duplo clique, rode `cmd /c Iniciar_PONTE.bat` no terminal para ver o erro.

## Instalação no Windows (PowerShell, VS Code)

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-interface.txt
.\.venv\Scripts\python.exe interface.py
```

Se você já tem `.venv`, basta atualizar os pacotes com o comando `pip install -r` acima e iniciar a interface.

## Como usar

1. Conecte seu celular como webcam no Windows 11 e confirme o funcionamento no aplicativo **Câmera** (ou com `teste_camera.py`). Feche os programas de teste antes de iniciar o PONTE.
2. Execute `interface.py` e clique **Iniciar**. O vídeo do celular aparece **dentro** do painel esquerdo.
3. **Pausar** interrompe a captura e libera o dispositivo.
4. **Configurações** permite trocar o índice da câmera (0 a 9) se o Windows usar outro número. Pause antes de trocar.
5. **Simular tradução** atualiza a interface com uma frase fictícia. **Não é** reconhecimento de Libras.
6. **Limpar** apaga o histórico, texto e tempo ilustrativo, mas não desliga a webcam.
7. Ao fechar o programa, a câmera é liberada automaticamente.

## Problemas comuns

- **A câmera não abre:** confirme que ela ainda aparece no aplicativo Câmera do Windows, feche outros programas que a estejam usando e escolha outro índice em Configurações.
- **A imagem parou:** confira se o celular segue vinculado, reative a câmera conectada e clique Iniciar novamente.
- **`ModuleNotFoundError: No module named 'cv2'`:** instale o `requirements-interface.txt` no mesmo ambiente do Python usado para abrir a janela.
- **Imagem espelhada:** depende da câmera virtual do Windows/celular; o código mostra os quadros como são recebidos, sem espelhar artificialmente.

## Próximos passos

Integrar o reconhecimento de Libras de `main.py` e o serviço de IA com um worker em segundo plano (`QThread`/signals), sem bloquear os eventos do PySide6. As traduções e a síntese de voz continuam desconectadas nesta etapa.
