"""
ASR (Automatic Speech Recognition) Engines module
Supports Google Speech Recognition and Whisper
"""

import re
from difflib import SequenceMatcher
from PyQt5.QtCore import QThread, pyqtSignal


# Model caches - load once and reuse
_whisper_model_cache = {}
_qwen_model_cache = {}


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
        self.error_occurred = False
        self.error_message = ""

    def run(self):
        try:
            if self.config['engine'] == "Google Speech Recognition":
                result = self.google_asr()
            elif self.config['engine'] == "Whisper":
                result = self.whisper_asr()
            elif self.config['engine'] == "Qwen3-ASR":
                result = self.qwen3_asr()
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
            self.error_occurred = True
            self.error_message = str(e)
            self.error.emit(str(e))

    def google_asr(self):
        """Google Speech Recognition implementation"""
        import speech_recognition as sr

        recognizer = sr.Recognizer()
        recognizer.energy_threshold = self.config.get('energy_threshold', 300)

        # Debug: Print the language being used
        lang = self.config.get('language', 'en-US')
        print(f"[DEBUG] Google ASR using language: {lang}")

        try:
            with sr.AudioFile(self.audio_file) as source:
                # Adjust for ambient noise
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.record(source)

            # Try to recognize - the free API doesn't support model selection
            # Note: model parameter only works with recognize_google_cloud (requires API key)
            try:
                text = recognizer.recognize_google(audio, language=lang)
                print(f"[DEBUG] Google ASR recognized: {text}")
            except sr.UnknownValueError as e:
                # Speech was not understood - this is common for test audio
                # Return empty text instead of failing
                print(f"[DEBUG] Google ASR UnknownValueError: {e}")
                text = ""
            except sr.RequestError as e:
                raise Exception(f"Google Speech Recognition API error: {str(e)}")
            except Exception as e:
                raise Exception(f"Recognition failed: {str(e)}")

            return {'text': text, 'metadata': {}}

        except sr.UnknownValueError:
            # Could not understand audio - return empty for connection test
            return {'text': '', 'metadata': {}}
        except sr.RequestError as e:
            raise Exception(f"Google Speech Recognition connection error: {str(e)}")

    def whisper_asr(self):
        """OpenAI Whisper implementation"""
        import whisper

        model_name = self.config['model']
        # Use cached model if available
        if model_name not in _whisper_model_cache:
            _whisper_model_cache[model_name] = whisper.load_model(model_name)
        model = _whisper_model_cache[model_name]
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

    def qwen3_asr(self):
        """Qwen3-ASR implementation using the official Qwen3-ASR package"""
        import torch
        import librosa
        from qwen_asr import Qwen3ASRModel

        # Auto-detect GPU availability
        device = "cuda" if torch.cuda.is_available() else "cpu"

        # Get the model identifier from config
        model_name_short = self.config['model']  # e.g., 'Qwen3-ASR-1.7B'

        # Map short name to model configuration
        if model_name_short == 'Qwen3-ASR-1.7B':
            model_size = '1.7B'
        elif model_name_short == 'Qwen3-ASR-0.6B':
            model_size = '0.6B'
        else:
            raise ValueError(f"Unknown Qwen3-ASR model: {model_name_short}")

        # Create cache key based on model size and device
        cache_key = f"{model_size}_{device}"

        # Use cached model if available
        if cache_key not in _qwen_model_cache:
            # Load the Qwen3-ASR model
            # The first time this is called, it will download the model.
            # This might take a while, but subsequent calls will use cached versions.
            _qwen_model_cache[cache_key] = Qwen3ASRModel.from_pretrained(
                f"Qwen/Qwen3-ASR-{model_size}",
                device_map=device,
                dtype=torch.float16 if device == "cuda" else torch.float32
            )
        model = _qwen_model_cache[cache_key]

        # Perform ASR transcription using the Qwen3-ASR model
        # According to the signature, transcribe accepts file paths directly
        # Convert language codes to full names as required by Qwen3-ASR
        language_code = self.config.get('language', 'en')

        # Extract just the language part (e.g., 'el' from 'el-GR')
        lang_part = language_code.split('-')[0].lower()

        # Map common language codes to the format expected by Qwen3-ASR
        language_mapping = {
            'en': 'English',
            'zh': 'Chinese',
            'yue': 'Cantonese',
            'ar': 'Arabic',
            'de': 'German',
            'fr': 'French',
            'es': 'Spanish',
            'pt': 'Portuguese',
            'id': 'Indonesian',
            'it': 'Italian',
            'ko': 'Korean',
            'ru': 'Russian',
            'th': 'Thai',
            'vi': 'Vietnamese',
            'ja': 'Japanese',
            'tr': 'Turkish',
            'hi': 'Hindi',
            'ms': 'Malay',
            'nl': 'Dutch',
            'sv': 'Swedish',
            'da': 'Danish',
            'fi': 'Finnish',
            'pl': 'Polish',
            'cs': 'Czech',
            'fil': 'Filipino',
            'fa': 'Persian',
            'el': 'Greek',
            'ro': 'Romanian',
            'hu': 'Hungarian',
            'mk': 'Macedonian'
        }

        # Default to English if language code not found in mapping
        mapped_language = language_mapping.get(lang_part, 'English')
        
        transcriptions = model.transcribe([self.audio_file], language=mapped_language)
        
        # Extract the text from the transcription result
        # transcriptions is a list, so we get the first element
        transcription_text = transcriptions[0].text if transcriptions else ""
        
        # Return the transcription result
        metadata = {}
        
        return {'text': transcription_text, 'metadata': metadata}

    def analyze_pronunciation(self, reference, recognized):
        """Analyze pronunciation by comparing reference and recognized text"""
        import unicodedata
        
        # Normalize texts (preserving script differences for analysis)
        ref_normalized = self.normalize_text_preserve_case(reference)
        rec_normalized = self.normalize_text_preserve_case(recognized)

        # Calculate similarity
        # First try direct comparison
        direct_similarity = SequenceMatcher(None, ref_normalized, rec_normalized).ratio()
        
        # Also try comparing without diacritics/script normalization for Greek
        ref_no_accents = self.remove_accents(ref_normalized)
        rec_no_accents = self.remove_accents(rec_normalized)
        normalized_similarity = SequenceMatcher(None, ref_no_accents, rec_no_accents).ratio()
        
        # Use the higher similarity score to account for script/diacritic differences
        similarity = max(direct_similarity, normalized_similarity)
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
                # Calculate word similarity considering script differences
                direct_word_sim = SequenceMatcher(None, ref_word, rec_word).ratio()
                
                # Also compare without accents for Greek text
                ref_word_no_acc = self.remove_accents(ref_word)
                rec_word_no_acc = self.remove_accents(rec_word)
                normalized_word_sim = SequenceMatcher(None, ref_word_no_acc, rec_word_no_acc).ratio()
                
                word_sim = max(direct_word_sim, normalized_word_sim)
                
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

    def normalize_text_preserve_case(self, text):
        """Normalize text for comparison while preserving script differences"""
        import re
        # Remove punctuation but preserve all scripts (Greek, Latin, etc.)
        text = text.strip()
        text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        return text.lower()

    def remove_accents(self, text):
        """Remove diacritics and accents from text for better Greek comparison"""
        import unicodedata
        # Normalize to decomposed form (NFD) to separate base characters from diacritics
        nfd = unicodedata.normalize('NFD', text)
        # Filter out combining characters (diacritics)
        without_accents = ''.join(char for char in nfd if not unicodedata.combining(char))
        return without_accents

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
        self.available_engines = ['Google Speech Recognition', 'Whisper', 'Qwen3-ASR']

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
