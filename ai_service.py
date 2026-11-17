"""Envio de vídeos curtos ao Gemini para interpretação experimental."""
import os
import time
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import errors, types


class AIService:
    def __init__(self):
        load_dotenv(Path(__file__).resolve().parent / '.env')
        token = os.getenv('GEMINI_API_TOKEN') or os.getenv('GEMINI_API_KEY')
        if not token:
            raise ValueError('Configure GEMINI_API_TOKEN no arquivo .env antes de traduzir.')
        self.client = genai.Client(api_key=token, http_options=types.HttpOptions(timeout=120000))
        self.model = os.getenv('GEMINI_MODEL', 'gemini-3.5-flash-lite')

    def translate_sign_images(self, paths):
        if not 1 <= len(paths) <= 8:
            raise ValueError('Selecione de 1 a 8 imagens na ordem desejada.')
        parts = [types.Part(text=(
            'Analise as imagens de Libras na ordem numerada. Uma imagem pode conter vários '
            'quadros ou sinais diferentes. Identifique cada sinal quando possível e '
            'apresente uma possível tradução em português apenas quando houver contexto suficiente. '
            'Transcreva legendas visíveis separadamente e não as trate como reconhecimento '
            'confirmado. Diga quando uma imagem, movimento ou sinal for incerto. '
            'Não invente palavras nem presuma que figuras independentes formem uma frase. '
            'Responda em português de forma clara e breve.'))]
        total = 0
        for number, path in enumerate(paths, 1):
            image = Path(path)
            mime = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
                    '.webp': 'image/webp'}.get(image.suffix.lower())
            if not mime:
                raise ValueError(f'Formato não suportado: {image.name}. Use PNG, JPEG ou WEBP.')
            total += image.stat().st_size
            if total > 14 * 1024 * 1024:
                raise ValueError('As imagens juntas devem ter no máximo 14 MB.')
            parts.extend([types.Part(text=f'Imagem {number}: {image.name}'),
                          types.Part.from_bytes(data=image.read_bytes(), mime_type=mime)])
        try:
            response = self.client.models.generate_content(model=self.model, contents=parts)
        except errors.APIError as exc:
            if exc.code in (503, 504):
                raise RuntimeError('O Gemini está temporariamente indisponível ou demorou. Tente novamente.') from exc
            raise
        if not response.text:
            raise RuntimeError('O Gemini não retornou uma resposta em texto.')
        return response.text.strip()

    def translate_sign_language_video(self, video_path, progress=None):
        def report(message):
            if progress:
                progress(message)

        stage = 'envio do vídeo'
        try:
            path = Path(video_path)
            if path.stat().st_size > 14 * 1024 * 1024:
                raise ValueError('O vídeo é muito grande para enviar. Tente uma câmera de menor resolução.')
            video = types.Part(
                inline_data=types.Blob(data=path.read_bytes(), mime_type='video/mp4'),
                video_metadata=types.VideoMetadata(fps=5),
            )
            prompt = ('Este vídeo pode conter um sinal de Libras. Tente interpretar em português. '
                      'Observe a posição e o movimento das mãos ao longo do vídeo. '
                      'Se não conseguir identificar com segurança, diga que não foi possível identificar. '
                      'Responda de forma curta.')
            stage = 'análise do vídeo'
            report('Enviando vídeo e aguardando análise do Gemini…')
            for attempt in range(2):
                try:
                    response = self.client.models.generate_content(model=self.model, contents=[prompt, video])
                    break
                except errors.APIError as exc:
                    if exc.code not in (503, 504) or attempt:
                        raise
                    report('O Gemini está indisponível ou demorou; tentando mais uma vez…')
                    time.sleep(5)
            if not response.text:
                raise RuntimeError('O Gemini não retornou uma resposta em texto.')
            return response.text.strip()
        except errors.APIError as exc:
            if exc.code == 503:
                raise RuntimeError(f'O Gemini está temporariamente indisponível durante {stage}. Tente novamente em alguns minutos.') from exc
            if exc.code == 504:
                raise RuntimeError(f'O Gemini excedeu o prazo durante {stage}. Tente novamente em alguns minutos.') from exc
            raise
