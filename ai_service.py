import os
import time
import warnings
from dotenv import load_dotenv


warnings.filterwarnings("ignore")
import google.generativeai as genai

class AIService:
    def __init__(self):
        
        load_dotenv()
        api_token = os.getenv("GEMINI_API_TOKEN")
        
        if not api_token:
            raise ValueError("Token não encontrado. Verifique se o arquivo .env contém GEMINI_API_TOKEN.")
        
        genai.configure(api_key=api_token)
        
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def translate_sign_language_video(self, video_path):
        try:
            print("Fazendo upload do vídeo para a IA...")
            video_file = genai.upload_file(path=video_path)
            
            
            while video_file.state.name == 'PROCESSING':
                time.sleep(2)
                video_file = genai.get_file(video_file.name)
                
            if video_file.state.name == 'FAILED':
                genai.delete_file(video_file.name)
                return "Erro: O Google não conseguiu processar o vídeo."
            
            print("Vídeo processado. Traduzindo sinal...")
            prompt = "Este vídeo contém uma pessoa fazendo um sinal de língua de sinais. Traduza o movimento para uma palavra ou frase curta em português. Responda apenas com a tradução."
            
            response = self.model.generate_content([prompt, video_file])
            genai.delete_file(video_file.name)
            
            return response.text.strip()
            
        except Exception as e:
            return f"Erro na IA: {e}"