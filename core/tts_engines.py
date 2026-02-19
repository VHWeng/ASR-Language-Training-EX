"""
TTS (Text-to-Speech) Engines module
Supports gTTS and placeholders for future TTS engines
"""

import io
import threading
import time
import pygame
from gtts import gTTS
from PyQt5.QtCore import QThread, pyqtSignal


class TTSBase:
    """Base class for TTS engines"""

    def speak(self, text, language, slow=False):
        """Speak the given text"""
        raise NotImplementedError

    def speak_words_sequentially(self, words, language, pause_between=0.5):
        """Speak words one at a time with pauses"""
        raise NotImplementedError


class gTTSEngine(TTSBase):
    """Google Text-to-Speech engine implementation"""

    def __init__(self):
        pygame.mixer.init()

    def speak(self, text, language, slow=False):
        """Speak text using gTTS"""
        try:
            tts = gTTS(text=text, lang=language, slow=slow)
            mp3_fp = io.BytesIO()
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)

            pygame.mixer.music.load(mp3_fp)
            pygame.mixer.music.play()

            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)

            return True
        except Exception as e:
            print(f"gTTS Error: {e}")
            return False

    def speak_words_sequentially(self, words, language, pause_between=0.5):
        """Speak words one at a time with pauses"""
        try:
            for i, word in enumerate(words):
                if not word.strip():
                    continue

                tts = gTTS(text=word, lang=language, slow=True)
                mp3_fp = io.BytesIO()
                tts.write_to_fp(mp3_fp)
                mp3_fp.seek(0)

                pygame.mixer.music.load(mp3_fp)
                pygame.mixer.music.play()

                # Wait for playback to finish
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)

                # Add pause between words
                if i < len(words) - 1:
                    time.sleep(pause_between)

            return True
        except Exception as e:
            print(f"gTTS Sequential Error: {e}")
            return False


class Pyttsx3Engine(TTSBase):
    """
    pyttsx3 TTS engine (Offline)
    PLACEHOLDER for future implementation
    """

    def __init__(self):
        # TODO: Import and initialize pyttsx3
        # import pyttsx3
        # self.engine = pyttsx3.init()
        pass

    def speak(self, text, language, slow=False):
        """Speak text using pyttsx3"""
        # TODO: Implement pyttsx3 TTS
        # self.engine.say(text)
        # self.engine.runAndWait()
        raise NotImplementedError("pyttsx3 engine not yet implemented")

    def speak_words_sequentially(self, words, language, pause_between=0.5):
        """Speak words one at a time"""
        # TODO: Implement sequential word playback
        raise NotImplementedError("pyttsx3 sequential playback not yet implemented")


class EspeakEngine(TTSBase):
    """
    eSpeak/eSpeak-ng TTS engine
    PLACEHOLDER for future implementation
    """

    def __init__(self):
        # TODO: Initialize espeak integration
        pass

    def speak(self, text, language, slow=False):
        """Speak text using espeak"""
        # TODO: Implement espeak TTS using subprocess or wrapper
        raise NotImplementedError("eSpeak engine not yet implemented")

    def speak_words_sequentially(self, words, language, pause_between=0.5):
        """Speak words one at a time"""
        raise NotImplementedError("eSpeak sequential playback not yet implemented")


class TTSThread(QThread):
    """Thread for TTS playback"""
    finished = pyqtSignal()
    error = pyqtSignal(str)
    word_started = pyqtSignal(int, str)  # Emits word index and word
    word_finished = pyqtSignal(int)

    def __init__(self, text, engine_name='gTTS', language='en', slow=False, word_by_word=False):
        super().__init__()
        self.text = text
        self.engine_name = engine_name
        self.language = language
        self.slow = slow
        self.word_by_word = word_by_word
        self._is_running = True

    def run(self):
        try:
            if self.engine_name == 'gTTS':
                engine = gTTSEngine()
            elif self.engine_name == 'pyttsx3':
                engine = Pyttsx3Engine()
            elif self.engine_name == 'espeak':
                engine = EspeakEngine()
            else:
                raise ValueError(f"Unknown TTS engine: {self.engine_name}")

            if self.word_by_word:
                import re
                words = re.findall(r'\S+', self.text)
                engine.speak_words_sequentially(words, self.language)
            else:
                engine.speak(self.text, self.language, self.slow)

            if self._is_running:
                self.finished.emit()
        except Exception as e:
            if self._is_running:
                self.error.emit(str(e))

    def stop(self):
        """Stop TTS playback"""
        self._is_running = False
        pygame.mixer.music.stop()


class TTSEngineManager:
    """Manager for TTS engines"""

    def __init__(self):
        self.engines = {
            'gTTS': gTTSEngine(),
            # 'pyttsx3': Pyttsx3Engine(),  # Uncomment when implemented
            # 'espeak': EspeakEngine(),    # Uncomment when implemented
        }
        self.available_engines = ['gTTS']
        self.planned_engines = ['pyttsx3', 'espeak', 'Azure TTS', 'AWS Polly', 'IBM Watson TTS']

    def get_available_engines(self):
        """Get list of available TTS engines"""
        return self.available_engines

    def get_planned_engines(self):
        """Get list of planned future engines"""
        return self.planned_engines

    def get_engine(self, name):
        """Get TTS engine by name"""
        if name in self.engines:
            return self.engines[name]
        raise ValueError(f"TTS engine {name} not available")

    def register_engine(self, name, engine):
        """Register a new TTS engine"""
        self.engines[name] = engine
        if name not in self.available_engines:
            self.available_engines.append(name)
