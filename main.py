import cv2
import time
import threading

from ai_service import AIService
from voice_service import VoiceService

class LiveSignTranslator:
    def __init__(self, ai_service, voice_service):
        self.ai = ai_service
        self.voice = voice_service
        
        self.is_recording = False
        self.frames_buffer = []
        self.recording_start_time = 0
        self.max_record_time = 3.0 # Segundos de gravação por sinal
        
        self.previous_frame = None 

    def process_video_async(self, frames):
        temp_video_path = "movimento_temp.mp4"
        height, width, _ = frames[0].shape
        out = cv2.VideoWriter(temp_video_path, cv2.VideoWriter_fourcc(*'mp4v'), 20.0, (width, height))
        
        for frame in frames:
            out.write(frame)
        out.release()

        print("\nAnalisando movimento com a IA...")
        traducao = self.ai.translate_sign_language_video(temp_video_path)
        print(f"Tradução: {traducao}")
        
        self.voice.speak(traducao)

    def run(self):
        cap = cv2.VideoCapture(0)
        time.sleep(1)

        while True:
            ret, frame = cap.read()
            if not ret: break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)

            if self.previous_frame is None:
                self.previous_frame = gray
                continue

            frame_diff = cv2.absdiff(self.previous_frame, gray)
            thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)[1]
            thresh = cv2.dilate(thresh, None, iterations=2)
            
            contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            movimento_detectado = False
            for contour in contours:
                if cv2.contourArea(contour) > 6000:
                    movimento_detectado = True
                    break

            if movimento_detectado and not self.is_recording:
                self.is_recording = True
                self.recording_start_time = time.time()
                self.frames_buffer = []
                print("\nMovimento detectado! Gravando...")

            if self.is_recording:
                self.frames_buffer.append(frame)
                cv2.putText(frame, "Gravando...", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                
                if time.time() - self.recording_start_time > self.max_record_time:
                    self.is_recording = False
                    
                    thread = threading.Thread(target=self.process_video_async, args=(self.frames_buffer.copy(),))
                    thread.start()
                    
                    self.frames_buffer.clear()
                    self.previous_frame = None # Reseta o comparador
            else:
                self.previous_frame = gray

            cv2.imshow('Tradutor de Libras Ao Vivo', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()


def main():
    print("Carregando configurações e conectando IA...")
    try:
        ai = AIService()
        voice = VoiceService()
        
        app = LiveSignTranslator(ai, voice)
        
        print("Tudo pronto! Abrindo a câmera...")
        app.run()
        
    except Exception as e:
        print(f"Erro crítico ao iniciar o sistema: {e}")

if __name__ == "__main__":
    main()