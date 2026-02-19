"""
ASR (Automatic Speech Recognition) Engines module
Supports Google Speech Recognition and Whisper
"""

import re
from difflib import SequenceMatcher
from PyQt5.QtCore import QThread, pyqtSignal


class ASRThread(QThread):
    """Thread for ASR processing with multiple engine support"""
    finished = pyqtSignal(str, dict)
    error = pyqtSignal(str)

    def __init__(self, audio_file, config, show_punctuation, show_word_time, reference_text=None):
        super().__init__()
        self.audio_file = audio_file
        self.config = config
        self.show_punctuation = show_punctuation
        self.show_word_time = show_word_time
        self.reference_text = reference_text

    def run(self):
        try:
            if self.config['engine'] == "Google Speech Recognition":
                result = self.google_asr()
            elif self.config['engine'] == "Whisper":
                result = self.whisper_asr()
            else:
                # Placeholder for future ASR engines
                raise ValueError(f"Unknown ASR engine: {self.config['engine']}")

            # Add pronunciation analysis if reference text provided
            if self.reference_text:
                pronunciation_result = self.analyze_pronunciation(
                    self.reference_text, result['text']
                )
                if 'metadata' not in result:
                    result['metadata'] = {}
                result['metadata']['pronunciation'] = pronunciation_result

            self.finished.emit(result['text'], result.get('metadata', {}))
        except Exception as e:
            self.error.emit(str(e))

    def google_asr(self):
        """Google Speech Recognition implementation"""
        import speech_recognition as sr

        recognizer = sr.Recognizer()
        recognizer.energy_threshold = self.config['energy_threshold']

        with sr.AudioFile(self.audio_file) as source:
            audio = recognizer.record(source)

        text = recognizer.recognize_google(audio, language=self.config['language'])

        return {'text': text, 'metadata': {}}

    def whisper_asr(self):
        """OpenAI Whisper implementation"""
        import whisper

        model = whisper.load_model(self.config['model'])
        lang_code = self.config['language'][:2]

        result = model.transcribe(
            self.audio_file,
            language=lang_code,
            word_timestamps=self.show_word_time
        )

        text = result['text']

        metadata = {}
        if self.show_word_time and 'segments' in result:
            timestamps = []
            word_data = []
            for segment in result['segments']:
                if 'words' in segment:
                    for word in segment['words']:
                        timestamps.append(f"{word['word']} [{word['start']:.2f}s]")
                        word_data.append({
                            'word': word['word'],
                            'start': word['start'],
                            'end': word.get('end', word['start']),
                            'probability': word.get('probability', 1.0)
                        })
            metadata['word_times'] = '\n'.join(timestamps)
            metadata['word_data'] = word_data

        return {'text': text, 'metadata': metadata}

    def analyze_pronunciation(self, reference, recognized):
        """Analyze pronunciation accuracy between reference and recognized text"""
        # Normalize texts
        ref_normalized = self.normalize_text(reference)
        rec_normalized = self.normalize_text(recognized)

        # Calculate similarity
        similarity = SequenceMatcher(None, ref_normalized, rec_normalized).ratio()
        accuracy = similarity * 100

        # Word-level analysis
        ref_words = ref_normalized.split()
        rec_words = rec_normalized.split()

        word_analysis = []
        max_len = max(len(ref_words), len(rec_words))

        for i in range(max_len):
            ref_word = ref_words[i] if i < len(ref_words) else ""
            rec_word = rec_words[i] if i < len(rec_words) else ""

            if ref_word and rec_word:
                word_sim = SequenceMatcher(None, ref_word, rec_word).ratio()
                status = "correct" if word_sim > 0.8 else "incorrect"
                word_analysis.append({
                    'reference': ref_word,
                    'recognized': rec_word,
                    'similarity': word_sim * 100,
                    'status': status
                })
            elif ref_word:
                word_analysis.append({
                    'reference': ref_word,
                    'recognized': "",
                    'similarity': 0,
                    'status': "missing"
                })
            elif rec_word:
                word_analysis.append({
                    'reference': "",
                    'recognized': rec_word,
                    'similarity': 0,
                    'status': "extra"
                })

        return {
            'accuracy': accuracy,
            'word_analysis': word_analysis,
            'reference': reference,
            'recognized': recognized
        }

    def normalize_text(self, text):
        """Normalize text for comparison"""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        return text


class ASREngineManager:
    """Manager class for handling multiple ASR engines (Future expansion)"""

    def __init__(self):
        self.engines = {}
        self.available_engines = ['Google Speech Recognition', 'Whisper']

        # Placeholder for future engines
        self.planned_engines = [
            'Vosk',           # Offline ASR
            'Wav2Vec 2.0',    # Facebook's model
            'NVIDIA NeMo',    # NVIDIA's toolkit
            'Azure Speech',   # Microsoft Azure
            'AWS Transcribe', # Amazon Web Services
            'IBM Watson',     # IBM Watson Speech to Text
        ]

    def get_available_engines(self):
        """Return list of available ASR engines"""
        return self.available_engines + self.planned_engines

    def register_engine(self, name, engine_class):
        """Register a new ASR engine"""
        self.engines[name] = engine_class
        if name not in self.available_engines:
            self.available_engines.append(name)

    def create_engine(self, name, config):
        """Create an ASR engine instance"""
        if name in self.engines:
            return self.engines[name](config)
        raise ValueError(f"Engine {name} not registered")
