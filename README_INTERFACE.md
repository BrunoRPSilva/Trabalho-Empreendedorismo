# PONTE — execução local no Windows

O PONTE é um protótipo desktop. A câmera é local; ao clicar em **Gravar e traduzir**, um vídeo de três segundos é enviado à API Gemini para uma interpretação experimental. A opção **Simular tradução** funciona sem chave e apresenta frases de exemplo. A voz usa os recursos instalados no Windows.

## Instalação

1. Instale Python 3.10 ou superior e permita seu uso no terminal.
2. Abra a pasta do projeto e dê dois cliques em `Iniciar_PONTE.bat`. Na primeira execução, o programa cria `.venv` e instala as dependências; é necessária internet.
3. Para tradução com IA, crie na pasta do projeto um arquivo chamado `.env` com este conteúdo, substituindo o valor pela sua chave da API Gemini:

   ```text
   GEMINI_API_TOKEN=sua_chave_aqui
   GEMINI_MODEL=gemini-3.5-flash-lite
   ```

   Gere a chave no [Google AI Studio](https://aistudio.google.com/apikey). A disponibilidade do modelo, cotas e custos dependem da conta. Se necessário, ajuste `GEMINI_MODEL` para um modelo disponível para sua conta que aceite vídeo. Guarde a chave em segredo e não compartilhe o arquivo `.env`.
4. Reinicie o aplicativo, clique em **Iniciar** para abrir a câmera e em **Gravar e traduzir** para fazer um sinal durante três segundos. Depois aguarde a resposta. Clique em **Reproduzir** para ouvi-la.

Também é possível iniciar pelo PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe interface.py
```

Se a câmera não abrir, feche outros programas que a utilizem e selecione outro dispositivo em **Configurações**. Para testar apenas a interface e a voz, use **Simular tradução**. O arquivo `main.py` é um protótipo independente; a aplicação principal é `interface.py` e os dois não devem usar a câmera simultaneamente.

O reconhecimento por um modelo geral de IA pode estar incorreto. Não use os resultados como tradução confiável de Libras sem validação com pessoas surdas. O vídeo é enviado ao Google para processamento; obtenha o consentimento das pessoas filmadas.

## Consultas com imagens

Clique em **Imagens e sinais** e escolha uma das abas:

- **Frase → Libras:** digite uma palavra ou frase em português, aguarde o avatar carregar e clique em **Traduzir em Libras**. O serviço público VLibras recebe o texto, produz uma tradução automática e reproduz os sinais em um avatar animado. A glosa exibida é uma representação textual da tradução, não uma frase em português. Não é necessário usar a chave do Gemini nesta opção. A primeira abertura do avatar pode demorar e precisa de internet. Se o VLibras perguntar sobre coleta de dados anônimos, escolha a opção desejada no próprio widget.
- **Imagens → português:** adicione até oito arquivos PNG, JPEG ou WEBP (máximo de 14 MB no total), arraste-os para definir a ordem e clique em **Analisar imagens com IA**. Redimensione ou maximize a janela e arraste as divisórias para ajustar os espaços da lista, prévia e resultado; em telas menores, a aba também oferece rolagem. As imagens são enviadas ao Gemini. Se uma figura tiver vários sinais e legendas, a análise poderá relatar cada um; não se presume que formem uma frase. A resposta é experimental e imagens estáticas nem sempre mostram movimentos ou expressões necessárias para identificar um sinal.

O VLibras é uma ferramenta de Libras do Brasil. Seu acervo é consultado online; o PONTE não baixa todos os sinais para o computador. A ferramenta não cobre necessariamente todos os sinais nem substitui intérprete ou a validação por pessoas surdas. Para ajustar variações regionais, abra as configurações do avatar e escolha a região desejada; quando não houver sinal regional, o VLibras consulta o dicionário nacional.

Vídeos curtos são enviados diretamente à API, com amostragem de cinco quadros por segundo para capturar mais detalhes dos movimentos. O tempo de resposta depende da rede e do serviço, e a amostragem maior pode aumentar o consumo de tokens.
