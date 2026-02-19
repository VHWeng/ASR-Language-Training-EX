"""
ASR Application with PyQt5 GUI
Supports Google Speech Recognition and Whisper
Default language: Greek
Enhanced with Pronunciation Training Feedback
"""

import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QTextEdit, QLabel, 
                             QFileDialog, QDialog, QComboBox, QCheckBox,
                             QLineEdit, QMessageBox, QToolButton, QGroupBox,
                             QProgressBar, QSpinBox, QTabWidget, QGridLayout)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon, QFont, QColor, QTextCharFormat, QTextCursor, QPixmap
import speech_recognition as sr
import sounddevice as sd
import soundfile as sf
import numpy as np
from pydub import AudioSegment
import whisper
import tempfile
from difflib import SequenceMatcher
import re
from gtts import gTTS
import pygame
import io
from datetime import datetime
import time
import threading
import csv
import zipfile
from pathlib import Path


class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuration")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        
        # Engine selection
        engine_group = QGroupBox("ASR Engine")
        engine_layout = QVBoxLayout()
        
        self.engine_label = QLabel("Select Engine:")
        self.engine_combo = QComboBox()
        self.engine_combo.addItems(["Google Speech Recognition", "Whisper"])
        self.engine_combo.currentIndexChanged.connect(self.on_engine_changed)
        
        engine_layout.addWidget(self.engine_label)
        engine_layout.addWidget(self.engine_combo)
        engine_group.setLayout(engine_layout)
        layout.addWidget(engine_group)
        
        # Language selection
        lang_group = QGroupBox("Language")
        lang_layout = QVBoxLayout()
        
        self.lang_label = QLabel("Select Language:")
        self.lang_combo = QComboBox()
        self.languages = {
            "Greek": "el-GR",
            "English (US)": "en-US",
            "English (UK)": "en-GB",
            "Spanish": "es-ES",
            "French": "fr-FR",
            "German": "de-DE",
            "Italian": "it-IT",
            "Portuguese": "pt-PT",
            "Russian": "ru-RU",
            "Chinese": "zh-CN",
            "Japanese": "ja-JP",
            "Korean": "ko-KR",
            "Arabic": "ar-SA"
        }
        self.lang_combo.addItems(self.languages.keys())
        self.lang_combo.setCurrentText("Greek")
        
        lang_layout.addWidget(self.lang_label)
        lang_layout.addWidget(self.lang_combo)
        lang_group.setLayout(lang_layout)
        layout.addWidget(lang_group)
        
        # Model selection
        model_group = QGroupBox("Model")
        model_layout = QVBoxLayout()
        
        self.model_label = QLabel("Select Model:")
        self.model_combo = QComboBox()
        self.update_model_options()
        
        model_layout.addWidget(self.model_label)
        model_layout.addWidget(self.model_combo)
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)
        
        # Additional settings
        settings_group = QGroupBox("Additional Settings")
        settings_layout = QVBoxLayout()
        
        # Sample rate
        rate_layout = QHBoxLayout()
        self.rate_label = QLabel("Sample Rate (Hz):")
        self.rate_entry = QLineEdit("16000")
        rate_layout.addWidget(self.rate_label)
        rate_layout.addWidget(self.rate_entry)
        settings_layout.addLayout(rate_layout)
        
        # Energy threshold for Google
        energy_layout = QHBoxLayout()
        self.energy_label = QLabel("Energy Threshold:")
        self.energy_entry = QLineEdit("300")
        energy_layout.addWidget(self.energy_label)
        energy_layout.addWidget(self.energy_entry)
        settings_layout.addLayout(energy_layout)
        
        # Pronunciation threshold
        pron_layout = QHBoxLayout()
        self.pron_label = QLabel("Pronunciation Accuracy Threshold (%):")
        self.pron_spin = QSpinBox()
        self.pron_spin.setRange(50, 100)
        self.pron_spin.setValue(80)
        pron_layout.addWidget(self.pron_label)
        pron_layout.addWidget(self.pron_spin)
        settings_layout.addLayout(pron_layout)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # AI features removed in this version
        
        # Vocabulary File Configuration
        vocab_config_group = QGroupBox("Vocabulary File Settings")
        vocab_config_layout = QVBoxLayout()
        
        # Delimiter selection
        delim_layout = QHBoxLayout()
        self.delim_label = QLabel("Delimiter:")
        self.delim_combo = QComboBox()
        self.delimiters = ["|", ",", ";", "\t"]
        self.delim_combo.addItems(self.delimiters)
        self.delim_combo.setCurrentText("|")
        delim_layout.addWidget(self.delim_label)
        delim_layout.addWidget(self.delim_combo)
        vocab_config_layout.addLayout(delim_layout)
        
        # Column mappings
        col_mapping_layout = QGridLayout()
        
        # Reference text column
        col_mapping_layout.addWidget(QLabel("Reference Text Column:"), 0, 0)
        self.ref_col_spin = QSpinBox()
        self.ref_col_spin.setRange(1, 20)
        self.ref_col_spin.setValue(1)
        col_mapping_layout.addWidget(self.ref_col_spin, 0, 1)
        
        # Definition column
        col_mapping_layout.addWidget(QLabel("Definition Column:"), 1, 0)
        self.def_col_spin = QSpinBox()
        self.def_col_spin.setRange(1, 20)
        self.def_col_spin.setValue(2)
        col_mapping_layout.addWidget(self.def_col_spin, 1, 1)
        
        # English pronunciation column
        col_mapping_layout.addWidget(QLabel("English Pronunciation Column:"), 2, 0)
        self.eng_pron_col_spin = QSpinBox()
        self.eng_pron_col_spin.setRange(1, 20)
        self.eng_pron_col_spin.setValue(3)
        col_mapping_layout.addWidget(self.eng_pron_col_spin, 2, 1)
        
        # IPA pronunciation column
        col_mapping_layout.addWidget(QLabel("IPA Pronunciation Column:"), 3, 0)
        self.ipa_col_spin = QSpinBox()
        self.ipa_col_spin.setRange(1, 20)
        self.ipa_col_spin.setValue(4)
        col_mapping_layout.addWidget(self.ipa_col_spin, 3, 1)
        
        # Image description column
        col_mapping_layout.addWidget(QLabel("Image Description Column:"), 4, 0)
        self.img_desc_col_spin = QSpinBox()
        self.img_desc_col_spin.setRange(1, 20)
        self.img_desc_col_spin.setValue(5)
        col_mapping_layout.addWidget(self.img_desc_col_spin, 4, 1)
        
        # Image filename column
        col_mapping_layout.addWidget(QLabel("Image Filename Column:"), 5, 0)
        self.img_file_col_spin = QSpinBox()
        self.img_file_col_spin.setRange(1, 20)
        self.img_file_col_spin.setValue(6)
        col_mapping_layout.addWidget(self.img_file_col_spin, 5, 1)
        
        # Grammar column
        col_mapping_layout.addWidget(QLabel("Grammar Column:"), 6, 0)
        self.grammar_col_spin = QSpinBox()
        self.grammar_col_spin.setRange(1, 20)
        self.grammar_col_spin.setValue(7) # Default to column 7
        col_mapping_layout.addWidget(self.grammar_col_spin, 6, 1)

        vocab_config_layout.addLayout(col_mapping_layout)
        vocab_config_group.setLayout(vocab_config_layout)
        layout.addWidget(vocab_config_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Cancel")
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def on_engine_changed(self):
        self.update_model_options()
    
    def update_model_options(self):
        self.model_combo.clear()
        # Updated model options for Google Speech Recognition
        if self.engine_combo.currentText() == "Google Speech Recognition":
            self.model_combo.addItems([
                "Default",           # Legacy compatibility
                "Command and Search", # Legacy compatibility  
                "Dictation",         # Legacy compatibility
                "latest_short",      # NEW: Short utterances (recommended over Command and Search)
                "latest_long",       # NEW: Long content (recommended over Default)
                "chirp_3",          # NEW: Latest multilingual model with advanced features
                "telephony"         # NEW: Phone call optimization
            ])
        else:  # Whisper
            self.model_combo.addItems(['tiny.en', 'tiny', 'base.en', 'base', 'small.en', 'small', 'medium.en', 'medium', 'large-v1', 'large-v2', 'large-v3', 'large'])
            self.model_combo.setCurrentText("base")
    
    def get_config(self):
        config = {
            'engine': self.engine_combo.currentText(),
            'language': self.languages[self.lang_combo.currentText()],
            'language_name': self.lang_combo.currentText(),
            'model': self.model_combo.currentText(),
            'sample_rate': int(self.rate_entry.text()),
            'energy_threshold': int(self.energy_entry.text()),
            'pronunciation_threshold': self.pron_spin.value()
        }
        
        # Add vocabulary configuration
        config['vocab_delimiter'] = self.delim_combo.currentText()
        config['vocab_columns'] = {
            'reference': self.ref_col_spin.value(),
            'definition': self.def_col_spin.value(),
            'english_pronunciation': self.eng_pron_col_spin.value(),
            'ipa_pronunciation': self.ipa_col_spin.value(),
            'image_description': self.img_desc_col_spin.value(),
            'image_filename': self.img_file_col_spin.value(),
            'grammar': self.grammar_col_spin.value() # Added grammar column
        }
        
        return config


import threading
import queue

class RecordThread(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, sample_rate=16000):
        super().__init__()
        self.sample_rate = sample_rate
        self.filename = None
        self.is_recording = True  # Flag to control recording
        self.audio_queue = queue.Queue()
        self.recording_thread = None
    
    def run(self):
        try:
            # Initialize recording buffer
            recording_buffer = []
            
            # Callback function to capture audio chunks
            def audio_callback(indata, frames, time, status):
                if self.is_recording:
                    recording_buffer.append(indata.copy())
            
            # Start the stream
            stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype='float32',
                callback=audio_callback
            )
            
            stream.start()
            
            # Keep recording until flag is changed
            while self.is_recording:
                sd.sleep(100)  # Sleep for 100ms to avoid busy waiting
            
            # Stop the stream
            stream.stop()
            stream.close()
            
            # Combine all recorded chunks
            if recording_buffer:
                import numpy as np
                full_recording = np.concatenate(recording_buffer, axis=0)
                
                self.filename = tempfile.mktemp(suffix='.wav')
                sf.write(self.filename, full_recording, self.sample_rate)
                self.finished.emit(self.filename)
            else:
                self.error.emit("No audio recorded")
                
        except Exception as e:
            self.error.emit(str(e))
    
    def stop_recording(self):
        """Stop the recording"""
        self.is_recording = False


class ASRThread(QThread):
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
            else:
                result = self.whisper_asr()
            
            # Add pronunciation analysis if reference text provided
            if self.reference_text:
                pronunciation_result = self.analyze_pronunciation(
                    self.reference_text, result['text']
                )
                # Add pronunciation data to metadata
                if 'metadata' not in result:
                    result['metadata'] = {}
                result['metadata']['pronunciation'] = pronunciation_result
                
                # Debug logging
                print(f"DEBUG: Pronunciation analysis completed. Accuracy: {pronunciation_result['accuracy']:.1f}%")
                print(f"DEBUG: Word analysis items: {len(pronunciation_result['word_analysis'])}")
            
            self.finished.emit(result['text'], result.get('metadata', {}))
        except Exception as e:
            self.error.emit(str(e))
    
    def google_asr(self):
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = self.config['energy_threshold']
        
        with sr.AudioFile(self.audio_file) as source:
            audio = recognizer.record(source)
        
        text = recognizer.recognize_google(audio, language=self.config['language'])
        
        print(f"DEBUG: Google ASR returned text: '{text}'")
        return {'text': text, 'metadata': {}}
    
    def whisper_asr(self):
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
        """Analyze pronunciation accuracy"""
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


# AI thread classes removed in this version



class ASRApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.audio_file = None
        self.recorded_file = None
        self.config = {
            'engine': 'Google Speech Recognition',
            'language': 'el-GR',
            'language_name': 'Greek',
            'model': 'chirp_3',
            'sample_rate': 16000,
            'energy_threshold': 300,
            'pronunciation_threshold': 80,
            'vocab_delimiter': '|',
            'vocab_columns': {
                'reference': 1,
                'definition': 2,
                'english_pronunciation': 3,
                'ipa_pronunciation': 4,
                'image_description': 5,
                'image_filename': 6,
                'grammar': 7 # Added grammar column default
            }
        }
        self.pronunciation_data = None
        
        # Vocabulary file handling attributes
        self.vocabulary_data = []
        self.current_vocab_index = -1
        self.vocab_file_path = None
        self.image_directory = None
        
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("ASR Application with Pronunciation Training")
        self.setGeometry(100, 100, 900, 700)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout()
        
        # Top toolbar with icons
        toolbar = QHBoxLayout()
        toolbar.addStretch()
        
        self.config_btn = QToolButton()
        self.config_btn.setText("⚙")
        self.config_btn.setToolTip("Configuration")
        self.config_btn.clicked.connect(self.show_config)
        
        self.help_btn = QToolButton()
        self.help_btn.setText("?")
        self.help_btn.setToolTip("Help")
        self.help_btn.clicked.connect(self.show_help)
        
        self.about_btn = QToolButton()
        self.about_btn.setText("ℹ")
        self.about_btn.setToolTip("About")
        self.about_btn.clicked.connect(self.show_about)
        
        toolbar.addWidget(self.config_btn)
        toolbar.addWidget(self.help_btn)
        toolbar.addWidget(self.about_btn)
        main_layout.addLayout(toolbar)
        
        # Pronunciation Training Mode
        pron_group = QGroupBox("Pronunciation Training Mode")
        pron_layout = QVBoxLayout()
        
        # First row: Training mode and AI checkboxes
        mode_layout = QHBoxLayout()
        self.training_mode_cb = QCheckBox("Enable Pronunciation Training")
        self.training_mode_cb.setChecked(True)  # Default enabled
        self.training_mode_cb.toggled.connect(self.toggle_training_mode)
        
        self.show_pronunciation_cb = QCheckBox("Show Pronunciation")
        self.show_pronunciation_cb.setChecked(True)
        self.show_pronunciation_cb.toggled.connect(self.toggle_pronunciation_display)
        
        self.show_definition_cb = QCheckBox("Show Definition/Translation")
        self.show_definition_cb.setChecked(True)
        self.show_definition_cb.toggled.connect(self.toggle_definition_display)
        
        mode_layout.addWidget(self.show_definition_cb)
        
        # Add Show Grammar checkbox
        self.show_grammar_cb = QCheckBox("Show Grammar")
        self.show_grammar_cb.setChecked(False) # Default to disabled
        self.show_grammar_cb.toggled.connect(self.toggle_grammar_display)
        mode_layout.addWidget(self.show_grammar_cb)

        mode_layout.addStretch()
        pron_layout.addLayout(mode_layout)
        
        # Add Grammar text box
        self.grammar_text = QTextEdit()
        self.grammar_text.setMaximumHeight(90) # ~5 lines height (3 lines for definition + 2)
        self.grammar_text.setPlaceholderText("Grammar related to the reference text will appear here...")
        self.grammar_text.setReadOnly(True)
        self.grammar_text.setFont(QFont("Arial", 12))
        self.grammar_text.setStyleSheet("QTextEdit { font-family: Arial; font-size: 12pt; }")
        self.grammar_text.hide() # Hidden by default
        # pron_layout.addWidget(self.grammar_text) # Removed this line
        
        # Vocabulary file loading section
        vocab_layout = QHBoxLayout()
        vocab_layout.addWidget(QLabel("Vocabulary File:"))
        
        self.vocab_file_label = QLabel("No file loaded")
        self.vocab_file_label.setMinimumWidth(150)
        vocab_layout.addWidget(self.vocab_file_label)
        
        self.load_vocab_btn = QPushButton("📁 Load Vocabulary")
        self.load_vocab_btn.clicked.connect(self.load_vocabulary_file)
        self.load_vocab_btn.setToolTip("Load vocabulary from text, CSV, or ZIP file")
        vocab_layout.addWidget(self.load_vocab_btn)
        
        # Enable Image checkbox
        self.enable_image_cb = QCheckBox("Enable Image")
        self.enable_image_cb.setChecked(False)
        self.enable_image_cb.toggled.connect(self.toggle_image_display)
        vocab_layout.addWidget(self.enable_image_cb)
        
        vocab_layout.addStretch()
        pron_layout.addLayout(vocab_layout)
        
        # Navigation buttons (centered below definition)
        nav_layout = QHBoxLayout()
        nav_layout.addStretch()
        
        self.prev_vocab_btn = QPushButton("◀ Previous")
        self.prev_vocab_btn.clicked.connect(self.previous_vocabulary)
        self.prev_vocab_btn.setEnabled(False)
        nav_layout.addWidget(self.prev_vocab_btn)
        
        self.next_vocab_btn = QPushButton("Next ▶")
        self.next_vocab_btn.clicked.connect(self.next_vocabulary)
        self.next_vocab_btn.setEnabled(False)
        nav_layout.addWidget(self.next_vocab_btn)
        
        nav_layout.addStretch()
        
        # Reference text row
        ref_layout = QHBoxLayout()
        ref_layout.addWidget(QLabel("Reference Text:"))
        self.reference_text = QLineEdit()
        self.reference_text.setPlaceholderText("Enter the text you want to practice...")
        # Set default font size to 12pt
        ref_font = QFont()
        ref_font.setPointSize(14)
        self.reference_text.setFont(ref_font)
        self.reference_text.setEnabled(True)  # Default enabled
        self.reference_text.returnPressed.connect(self.load_ai_data)  # Enter key handler
        self.reference_text.textChanged.connect(self.update_combined_pronunciation)  # Connect to combined pronunciation update
        
        # Add font size controls for reference text
        font_control_layout = QHBoxLayout()
        font_control_layout.setSpacing(2)
        
        self.ref_font_minus_btn = QPushButton("-")
        self.ref_font_minus_btn.setFixedWidth(25)
        self.ref_font_minus_btn.clicked.connect(lambda: self.change_font_size(self.reference_text, -1))
        self.ref_font_minus_btn.setToolTip("Decrease font size")
        
        self.ref_font_plus_btn = QPushButton("+")
        self.ref_font_plus_btn.setFixedWidth(25)
        self.ref_font_plus_btn.clicked.connect(lambda: self.change_font_size(self.reference_text, 1))
        self.ref_font_plus_btn.setToolTip("Increase font size")
        
        font_control_layout.addWidget(self.ref_font_minus_btn)
        font_control_layout.addWidget(self.ref_font_plus_btn)
        
        ref_layout.addLayout(font_control_layout)
        ref_layout.addWidget(self.reference_text)
        
        # Add TTS button
        self.tts_btn = QPushButton("🔊 Play TTS")
        self.tts_btn.clicked.connect(self.play_tts)
        self.tts_btn.setEnabled(True)  # Default enabled
        ref_layout.addWidget(self.tts_btn)
        
        # Add Slow TTS button
        self.slow_tts_btn = QPushButton("🐢 Slow TTS")
        self.slow_tts_btn.clicked.connect(self.play_slow_tts)
        self.slow_tts_btn.setEnabled(True)  # Default enabled
        self.slow_tts_btn.setToolTip("Play reference text one word at a time with pauses")
        ref_layout.addWidget(self.slow_tts_btn)
        
        pron_layout.addLayout(ref_layout)
        
        # Pronunciation text box (visible by default since training mode is enabled)
        # Will display both English text (top) and IPA pronunciation (bottom)
        self.pronunciation_text = QTextEdit()
        self.pronunciation_text.setMaximumHeight(80)  # Increased height for two lines
        self.pronunciation_text.setPlaceholderText("Enter text above to see English and IPA pronunciation...")
        self.pronunciation_text.setReadOnly(True)
        self.pronunciation_text.setFont(QFont("Arial", 14))  # Use Arial for better IPA symbol support, 14pt default
        self.pronunciation_text.setStyleSheet("QTextEdit { font-family: Arial; font-size: 14pt; }")
        self.pronunciation_text.show()  # Show by default
        
        # Add font size controls for all three text boxes below
        pron_font_layout = QHBoxLayout()
        self.pron_font_minus_btn = QPushButton("-")
        self.pron_font_minus_btn.setFixedWidth(25)
        self.pron_font_minus_btn.clicked.connect(self.change_all_text_boxes_font_size(-1))
        self.pron_font_minus_btn.setToolTip("Decrease font size for all text boxes")
        
        self.pron_font_plus_btn = QPushButton("+")
        self.pron_font_plus_btn.setFixedWidth(25)
        self.pron_font_plus_btn.clicked.connect(self.change_all_text_boxes_font_size(1))
        self.pron_font_plus_btn.setToolTip("Increase font size for all text boxes")
        
        pron_font_layout.addWidget(self.pron_font_minus_btn)
        pron_font_layout.addWidget(self.pron_font_plus_btn)
        pron_font_layout.addStretch()
        pron_layout.addLayout(pron_font_layout)
        pron_layout.addWidget(self.pronunciation_text)
        
        # Definition text box (visible by default since training mode is enabled)
        self.definition_text = QTextEdit()
        self.definition_text.setMaximumHeight(90)  # Increased to 3 line height
        self.definition_text.setPlaceholderText("Definition/translation from Ollama AI will appear here...")
        self.definition_text.setReadOnly(True)
        self.definition_text.setFont(QFont("Arial", 12))  # Set default font size to 12pt
        self.definition_text.setStyleSheet("QTextEdit { font-family: Arial; font-size: 12pt; }")
        self.definition_text.show()  # Show by default
        
        pron_layout.addWidget(self.definition_text)
        
        # Add Grammar text box (moved here)
        pron_layout.addWidget(self.grammar_text)
        
        # Add navigation buttons layout here
        pron_layout.addLayout(nav_layout)
        
        # Image viewer (below definition)
        self.image_viewer = QLabel()
        self.image_viewer.setMaximumHeight(300)
        self.image_viewer.setMaximumWidth(800)  # Prevent horizontal shrinking
        self.image_viewer.setAlignment(Qt.AlignCenter)
        self.image_viewer.setText("No image loaded")
        self.image_viewer.setStyleSheet("border: 1px solid gray; background-color: #f0f0f0;")
        self.image_viewer.hide()  # Hidden by default
        pron_layout.addWidget(self.image_viewer)
        
        pron_group.setLayout(pron_layout)
        main_layout.addWidget(pron_group)
        
        # File browser section
        file_group = QGroupBox("Audio File (Optional)")
        file_layout = QHBoxLayout()
        
        self.file_label = QLabel("No file selected")
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.browse_file)
        
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(self.browse_btn)
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)
        
        # Control buttons
        control_layout = QHBoxLayout()
        
        self.record_btn = QPushButton("🎤 Hold to Record")
        self.record_btn.pressed.connect(self.start_recording)
        self.record_btn.released.connect(self.stop_recording)
        self.is_recording = False
        
        # Set button style to make it clear it's a press-and-hold button
        self.record_btn.setStyleSheet("QPushButton { font-weight: bold; padding: 10px; }")
        
        self.playback_btn = QPushButton("▶ Playback")
        self.playback_btn.clicked.connect(self.playback_audio)
        self.playback_btn.setEnabled(False)
        
        self.convert_btn = QPushButton("🔄 ASR Convert")
        self.convert_btn.clicked.connect(self.convert_audio)
        self.convert_btn.setEnabled(False)
        
        control_layout.addWidget(self.record_btn)
        control_layout.addWidget(self.playback_btn)
        control_layout.addWidget(self.convert_btn)
        main_layout.addLayout(control_layout)
        
        # Options
        options_layout = QHBoxLayout()
        
        self.punctuation_cb = QCheckBox("Show Punctuation")
        self.punctuation_cb.setChecked(True)
        
        self.word_time_cb = QCheckBox("Word Timestamps")
        self.word_time_cb.setChecked(False)
        
        # Add auto-check checkbox
        self.auto_check_cb = QCheckBox("Auto Check After Record")
        self.auto_check_cb.setChecked(False)
        self.auto_check_cb.setToolTip("Automatically run ASR Convert after recording completes")
        
        options_layout.addWidget(self.punctuation_cb)
        options_layout.addWidget(self.word_time_cb)
        options_layout.addWidget(self.auto_check_cb)
        options_layout.addStretch()
        main_layout.addLayout(options_layout)
        
        # Tabs for output
        self.tabs = QTabWidget()
        
        # ASR Output tab
        asr_tab = QWidget()
        asr_layout = QVBoxLayout()
        self.output_text = QTextEdit()
        self.output_text.setMinimumHeight(150)
        font = QFont("Consolas", 10)
        self.output_text.setFont(font)
        
        # Add font size controls for output text
        output_font_layout = QHBoxLayout()
        self.output_font_minus_btn = QPushButton("-")
        self.output_font_minus_btn.setFixedWidth(25)
        self.output_font_minus_btn.clicked.connect(lambda: self.change_font_size(self.output_text, -1))
        self.output_font_minus_btn.setToolTip("Decrease font size")
        
        self.output_font_plus_btn = QPushButton("+")
        self.output_font_plus_btn.setFixedWidth(25)
        self.output_font_plus_btn.clicked.connect(lambda: self.change_font_size(self.output_text, 1))
        self.output_font_plus_btn.setToolTip("Increase font size")
        
        output_font_layout.addWidget(self.output_font_minus_btn)
        output_font_layout.addWidget(self.output_font_plus_btn)
        output_font_layout.addStretch()
        asr_layout.addLayout(output_font_layout)
        asr_layout.addWidget(self.output_text)
        asr_tab.setLayout(asr_layout)
        
        # Pronunciation Feedback tab
        feedback_tab = QWidget()
        feedback_layout = QVBoxLayout()
        
        # Accuracy score
        score_layout = QHBoxLayout()
        score_layout.addWidget(QLabel("Pronunciation Accuracy:"))
        self.accuracy_label = QLabel("N/A")
        self.accuracy_label.setFont(QFont("Arial", 14, QFont.Bold))
        score_layout.addWidget(self.accuracy_label)
        self.accuracy_bar = QProgressBar()
        self.accuracy_bar.setMaximum(100)
        score_layout.addWidget(self.accuracy_bar)
        score_layout.addStretch()
        feedback_layout.addLayout(score_layout)
        
        # Feedback text
        self.feedback_text = QTextEdit()
        self.feedback_text.setReadOnly(True)
        self.feedback_text.setFont(font)
        self.feedback_text.setMinimumHeight(200)  # Increased size for more feedback lines
        
        # Add font size controls for feedback text
        feedback_font_layout = QHBoxLayout()
        self.feedback_font_minus_btn = QPushButton("-")
        self.feedback_font_minus_btn.setFixedWidth(25)
        self.feedback_font_minus_btn.clicked.connect(lambda: self.change_font_size(self.feedback_text, -1))
        self.feedback_font_minus_btn.setToolTip("Decrease font size")
        
        self.feedback_font_plus_btn = QPushButton("+")
        self.feedback_font_plus_btn.setFixedWidth(25)
        self.feedback_font_plus_btn.clicked.connect(lambda: self.change_font_size(self.feedback_text, 1))
        self.feedback_font_plus_btn.setToolTip("Increase font size")
        
        feedback_font_layout.addWidget(self.feedback_font_minus_btn)
        feedback_font_layout.addWidget(self.feedback_font_plus_btn)
        feedback_font_layout.addStretch()
        feedback_layout.addLayout(feedback_font_layout)
        feedback_layout.addWidget(self.feedback_text)
        
        feedback_tab.setLayout(feedback_layout)
        
        self.tabs.addTab(asr_tab, "ASR Output")
        self.tabs.addTab(feedback_tab, "Pronunciation Feedback")
        
        main_layout.addWidget(self.tabs)
        
        # Status/Debug text box
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(60)  # About 3 lines
        self.status_text.setPlaceholderText("Status and debug information will appear here...")
        self.status_text.setReadOnly(True)
        font = QFont("Consolas", 9)
        self.status_text.setFont(font)
        
        # Add font size controls for status text
        status_font_layout = QHBoxLayout()
        self.status_font_minus_btn = QPushButton("-")
        self.status_font_minus_btn.setFixedWidth(25)
        self.status_font_minus_btn.clicked.connect(lambda: self.change_font_size(self.status_text, -1))
        self.status_font_minus_btn.setToolTip("Decrease font size")
        
        self.status_font_plus_btn = QPushButton("+")
        self.status_font_plus_btn.setFixedWidth(25)
        self.status_font_plus_btn.clicked.connect(lambda: self.change_font_size(self.status_text, 1))
        self.status_font_plus_btn.setToolTip("Increase font size")
        
        status_font_layout.addWidget(self.status_font_minus_btn)
        status_font_layout.addWidget(self.status_font_plus_btn)
        status_font_layout.addStretch()
        main_layout.addLayout(status_font_layout)
        main_layout.addWidget(self.status_text)
        
        # Bottom buttons
        bottom_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("💾 Save Text")
        self.save_btn.clicked.connect(self.save_text)
        
        self.save_report_btn = QPushButton("📊 Save Report")
        self.save_report_btn.clicked.connect(self.save_report)
        self.save_report_btn.setEnabled(False)
        
        self.exit_btn = QPushButton("❌ Exit")
        self.exit_btn.clicked.connect(self.close)
        
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.save_btn)
        bottom_layout.addWidget(self.save_report_btn)
        bottom_layout.addWidget(self.exit_btn)
        main_layout.addLayout(bottom_layout)
        
        central.setLayout(main_layout)
    
    def toggle_training_mode(self, enabled):
        self.reference_text.setEnabled(enabled)
        self.tts_btn.setEnabled(enabled)
        self.slow_tts_btn.setEnabled(enabled) # Ensure slow TTS button is also enabled/disabled with training mode
        
        if enabled:
            # Auto-show pronunciation, definition, and grammar when training mode is enabled
            self.show_pronunciation_cb.setChecked(True)
            self.show_definition_cb.setChecked(True)
            # Only auto-check grammar if it was explicitly checked by the user previously
            # Or if it's the default state and the user hasn't touched it yet
            if self.show_grammar_cb.isChecked() or not self.show_grammar_cb.isEnabled(): # Assuming initially disabled means user hasn't interacted
                self.show_grammar_cb.setChecked(True)

            self.pronunciation_text.show()
            self.definition_text.show()
            self.grammar_text.show() # Show grammar text box as well
            self.tabs.setCurrentIndex(1)  # Switch to feedback tab
        else:
            # Hide text boxes when training mode is disabled
            self.pronunciation_text.hide()
            self.definition_text.hide()
            self.grammar_text.hide() # Hide grammar text box as well
    
    def toggle_pronunciation_display(self, enabled):
        """Toggle pronunciation text box visibility"""
        if enabled:
            self.pronunciation_text.show()
            # Also show definition if it's enabled
            if self.show_definition_cb.isChecked():
                self.definition_text.show()
            # Also show grammar if it's enabled
            if self.show_grammar_cb.isChecked():
                self.grammar_text.show()
            # Update pronunciation display when shown
            self.update_combined_pronunciation()
        else:
            self.pronunciation_text.hide()
            self.definition_text.hide() # Hide definition if pronunciation is off
            self.grammar_text.hide() # Hide grammar if pronunciation is off
    
    def toggle_definition_display(self, enabled):
        """Toggle definition text box visibility"""
        if enabled and self.show_pronunciation_cb.isChecked():
            self.definition_text.show()
        else:
            self.definition_text.hide()
            
    def toggle_grammar_display(self, enabled):
        """Toggle grammar text box visibility"""
        if enabled:
            self.grammar_text.show()
        else:
            self.grammar_text.hide()
    
    def clean_ai_response(self, response):
        """Clean AI response by removing markdown, extra formatting, noise, and blank lines"""
        if not response:
            return ""
        
        # Remove common markdown artifacts
        cleaned = response.strip()
        cleaned = cleaned.replace("```", "")  # Remove code blocks
        cleaned = cleaned.replace("**", "")   # Remove bold markers
        cleaned = cleaned.replace("*", "")    # Remove italic markers
        
        # Remove blank lines and normalize whitespace
        lines = [line.strip() for line in cleaned.split('\n') if line.strip()]
        cleaned = '\n'.join(lines)
        
        # Remove common prefixes/suffixes for single-line responses
        if '\n' not in cleaned:
            # Take the first meaningful line for pronunciation
            for line in lines:
                if line and not line.lower().startswith(('note:', 'tip:', 'hint:')):
                    cleaned = line
                    break
        
        return cleaned.strip()
    
    def load_ai_data(self):
        """Load pronunciation and definition from AI"""
        # AI functionality removed in this version
        QMessageBox.information(self, "AI Feature Removed", "AI functionality has been removed from this version.")

    def on_ai_data_finished(self, results):
        pron_result = results['pron_result']
        def_result = results['def_result']

        # Process pronunciation response
        if pron_result.returncode == 0 and pron_result.stdout.strip():
            ai_response = pron_result.stdout.strip()
            self.status_text.append(f"[{self.get_current_time()}] 🤖 AI Raw Response:\n{ai_response}")

            # Parse the structured response
            english_pron = "N/A"
            ipa_pron = "N/A"
            
            for line in ai_response.split('\n'):
                if line.lower().startswith("english:"):
                    english_pron = self.clean_ai_response(line.split(":", 1)[1])
                elif line.lower().startswith("ipa:"):
                    ipa_pron = self.clean_ai_response(line.split(":", 1)[1])

            self.status_text.append(f"[{self.get_current_time()}] parsed English: {english_pron}")
            self.status_text.append(f"[{self.get_current_time()}] parsed IPA: {ipa_pron}")

            # Combine with current English text in proper format
            english_text = self.reference_text.text().strip()
            if english_text:
                combined_display = f"English: {english_pron}\nIPA:     {ipa_pron}"
                self.pronunciation_text.setPlainText(combined_display)
                self.status_text.append(f"[{self.get_current_time()}] ✅ AI pronunciation loaded.")
            else:
                self.pronunciation_text.setPlainText(f"IPA: {ipa_pron}")
                self.status_text.append(f"[{self.get_current_time()}] ✅ AI pronunciation loaded.")
        else:
            # Fall back to local IPA conversion if AI fails
            self.status_text.append(f"[{self.get_current_time()}] ⚠️ AI pronunciation failed, using local conversion")
            english_text = self.reference_text.text().strip()
            if english_text:
                local_ipa = self.text_to_ipa(english_text)
                combined_display = f"English: {english_text}\nIPA:     {local_ipa} (Local conversion)"
                self.pronunciation_text.setPlainText(combined_display)
                self.status_text.append(f"[{self.get_current_time()}] 📝 Local IPA: {local_ipa}")
            else:
                self.pronunciation_text.setPlainText("Failed to get pronunciation")
            
            # Log detailed error information
            if pron_result.returncode != 0:
                self.status_text.append(f"[{self.get_current_time()}] ❌ Pronunciation error code: {pron_result.returncode}")
            if not pron_result.stdout.strip():
                self.status_text.append(f"[{self.get_current_time()}] ❌ Empty pronunciation response")
            
        # Process definition response
        if def_result.returncode == 0 and def_result.stdout.strip():
            definition = def_result.stdout.strip()
            # Clean up the response
            definition = self.clean_ai_response(definition)
            self.definition_text.setPlainText(definition)
            self.status_text.append(f"[{self.get_current_time()}] ✅ AI definition loaded")
        else:
            self.definition_text.setPlainText("Failed to get definition from AI")
            self.status_text.append(f"[{self.get_current_time()}] ❌ AI definition request failed")
            
            # Log detailed error information
            if def_result.returncode != 0:
                self.status_text.append(f"[{self.get_current_time()}] ❌ Definition error code: {def_result.returncode}")
            if not def_result.stdout.strip():
                self.status_text.append(f"[{self.get_current_time()}] ❌ Empty definition response")
        
        # Update final status
        if pron_result.returncode == 0 and def_result.returncode == 0 and pron_result.stdout.strip() and def_result.stdout.strip():
            self.status_text.append(f"[{self.get_current_time()}] 🎉 AI data loading completed successfully")
        else:
            self.status_text.append(f"[{self.get_current_time()}] ⚠️ AI data loading completed with partial results")
        
    def on_ai_error(self, error_msg):
        self.status_text.append(f"[{self.get_current_time()}] ❌ AI request error: {error_msg}")
        QMessageBox.critical(self, "AI Error", error_msg)
    
    def clean_display_text(self, text):
        """Clean text for display by removing blank lines and normalizing whitespace"""
        if not text:
            return ""
        
        # Split into lines, strip each line, and filter out empty lines
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Join with single newlines
        cleaned = '\n'.join(lines)
        
        return cleaned.strip()
    
    def load_vocabulary_file(self):
        """Load vocabulary from text, CSV, or ZIP file"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select Vocabulary File", "", 
            "Vocabulary Files (*.txt *.csv *.zip);;Text Files (*.txt);;CSV Files (*.csv);;ZIP Files (*.zip);;All Files (*)"
        )
        
        if not filename:
            return
        
        try:
            self.status_text.append(f"[{self.get_current_time()}] 📁 Loading vocabulary file: {os.path.basename(filename)}")
            
            file_extension = Path(filename).suffix.lower()
            
            if file_extension == ".zip":
                self.load_zip_vocabulary(filename)
            elif file_extension in [".txt", ".csv"]:
                self.load_csv_vocabulary(filename)
            else:
                QMessageBox.warning(self, "Unsupported Format", 
                                  f"Unsupported file format: {file_extension}")
                return
            
            # Update UI
            self.vocab_file_label.setText(os.path.basename(filename))
            self.vocab_file_path = filename
            
            # Enable navigation buttons if we have data
            if self.vocabulary_data:
                self.current_vocab_index = 0
                self.prev_vocab_btn.setEnabled(False)
                self.next_vocab_btn.setEnabled(len(self.vocabulary_data) > 1)
                self.display_current_vocabulary()
                self.status_text.append(f"[{self.get_current_time()}] ✅ Loaded {len(self.vocabulary_data)} vocabulary entries")
            else:
                self.current_vocab_index = -1
                self.prev_vocab_btn.setEnabled(False)
                self.next_vocab_btn.setEnabled(False)
                self.status_text.append(f"[{self.get_current_time()}] ⚠️ No vocabulary entries found in file")
                
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load vocabulary file: {str(e)}")
            self.status_text.append(f"[{self.get_current_time()}] ❌ Vocabulary load error: {str(e)}")
    
    def load_csv_vocabulary(self, filepath):
        """Load vocabulary from CSV or text file"""
        self.vocabulary_data = []
        
        delimiter = self.config['vocab_delimiter']
        if delimiter == "\t":
            delimiter = "\t"
        
        columns = self.config['vocab_columns']
        
        try:
            with open(filepath, 'r', encoding='utf-8', newline='') as file:
                # Detect if it's a CSV or tab-delimited file
                sample = file.read(1024)
                file.seek(0)
                
                if delimiter == ",":
                    reader = csv.reader(file, delimiter=",")
                elif delimiter == "|":
                    reader = csv.reader(file, delimiter="|")
                elif delimiter == ";":
                    reader = csv.reader(file, delimiter=";")
                else:  # tab
                    reader = csv.reader(file, delimiter="\t")
                
                # Skip header row if it looks like a header
                header_skipped = False
                for row_num, row in enumerate(reader, 1):
                    if not row or all(not cell.strip() for cell in row):
                        continue
                    
                    # Check if this looks like a header row (first row with text-like content)
                    if not header_skipped and row_num == 1:
                        # Heuristic: if most cells look like column names, skip as header
                        text_cells = [cell.strip().lower() for cell in row if cell.strip()]
                        common_header_words = ['word', 'phrase', 'definition', 'pronunciation', 'image', 'desc', 'file']
                        header_score = sum(1 for cell in text_cells if any(header_word in cell for header_word in common_header_words))
                        if header_score >= 2 or len(text_cells) <= 3:  # Likely a header
                            header_skipped = True
                            continue
                    
                    # Extract data based on column configuration
                    vocab_entry = {
                        'reference': '',
                        'definition': '',
                        'english_pronunciation': '',
                        'ipa_pronunciation': '',
                        'image_description': '',
                        'image_filename': '',
                        'row_number': row_num
                    }
                    
                    # Get data from configured columns
                    if columns['reference'] <= len(row):
                        vocab_entry['reference'] = row[columns['reference'] - 1].strip()
                    
                    if columns['definition'] <= len(row):
                        vocab_entry['definition'] = row[columns['definition'] - 1].strip()
                    
                    if columns['english_pronunciation'] <= len(row):
                        vocab_entry['english_pronunciation'] = row[columns['english_pronunciation'] - 1].strip()
                    
                    if columns['ipa_pronunciation'] <= len(row):
                        vocab_entry['ipa_pronunciation'] = row[columns['ipa_pronunciation'] - 1].strip()
                    
                    if columns['image_description'] <= len(row):
                        vocab_entry['image_description'] = row[columns['image_description'] - 1].strip()
                    
                    if columns['image_filename'] <= len(row):
                        vocab_entry['image_filename'] = row[columns['image_filename'] - 1].strip()
                    
                    # Grammar column
                    if columns['grammar'] <= len(row):
                        vocab_entry['grammar'] = row[columns['grammar'] - 1].strip()

                    # Only add entries that have reference text
                    if vocab_entry['reference']:
                        self.vocabulary_data.append(vocab_entry)
                        
        except Exception as e:
            raise Exception(f"Error reading CSV file: {str(e)}")
    
    def load_zip_vocabulary(self, filepath):
        """Load vocabulary from ZIP file"""
        self.vocabulary_data = []
        
        try:
            with zipfile.ZipFile(filepath, 'r') as zip_file:
                # Look for CSV files in the ZIP
                csv_files = [f for f in zip_file.namelist() if f.lower().endswith('.csv')]
                
                if not csv_files:
                    raise Exception("No CSV files found in ZIP archive")
                
                # Use the first CSV file found
                csv_filename = csv_files[0]
                self.status_text.append(f"[{self.get_current_time()}] 📄 Found CSV file in ZIP: {csv_filename}")
                
                # Extract and load the CSV
                with zip_file.open(csv_filename) as csv_file_obj:
                    # Read the CSV content
                    content = csv_file_obj.read().decode('utf-8')
                    
                    # Create temporary file for processing
                    temp_csv = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8')
                    temp_csv.write(content)
                    temp_csv.close()
                    
                    try:
                        self.load_csv_vocabulary(temp_csv.name)
                    finally:
                        os.unlink(temp_csv.name)
                
                # Look for "images" directory specifically
                all_entries = zip_file.namelist()
                
                # Priority 1: Look for exact "images/" directory
                images_dir = "images/"  # Exact match for the directory
                if images_dir in all_entries:
                    self.image_directory = images_dir
                    self.status_text.append(f"[{self.get_current_time()}] 📁 Found primary images directory: {self.image_directory}")
                else:
                    # Priority 2: Look for variations of image directories
                    image_dirs = [f for f in all_entries if f.lower().endswith('/') and ('image' in f.lower() or 'img' in f.lower())]
                    
                    # Also look for directories containing image files
                    if not image_dirs:
                        # Check if there are image files in root or subdirectories
                        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
                        image_files = [f for f in all_entries 
                                     if not f.endswith('/') and any(f.lower().endswith(ext) for ext in image_extensions)]
                        
                        if image_files:
                            # Get the directories containing images
                            dirs_with_images = set()
                            for img_file in image_files:
                                parts = img_file.split('/')
                                if len(parts) > 1:
                                    # Add the directory path
                                    dir_path = '/'.join(parts[:-1]) + '/'
                                    dirs_with_images.add(dir_path)
                            
                            if dirs_with_images:
                                image_dirs = list(dirs_with_images)
                                self.status_text.append(f"[{self.get_current_time()}] 📁 Found alternative image directories: {image_dirs}")
                            else:
                                self.status_text.append(f"[{self.get_current_time()}] 📁 Found {len(image_files)} image files in ZIP root")
                    
                    if image_dirs:
                        self.image_directory = image_dirs[0]  # Use first found directory
                        self.status_text.append(f"[{self.get_current_time()}] 📁 Selected image directory: {self.image_directory}")
                    else:
                        self.status_text.append(f"[{self.get_current_time()}] ℹ️ No dedicated image directory found")
                    
        except Exception as e:
            raise Exception(f"Error reading ZIP file: {str(e)}")
    
    def display_current_vocabulary(self):
        """Display the current vocabulary entry"""
        if not self.vocabulary_data or self.current_vocab_index < 0:
            return
        
        entry = self.vocabulary_data[self.current_vocab_index]
        
        # Update reference text
        self.reference_text.setText(entry['reference'])
        
        # Update definition and pronunciation from file if available
        definition = entry.get('definition', '')
        english_pron = entry.get('english_pronunciation', '')
        ipa_pron = entry.get('ipa_pronunciation', '')

        # Clean definition text to remove blank lines
        cleaned_definition = self.clean_display_text(definition) if definition else "No definition available"
        self.definition_text.setPlainText(cleaned_definition)
        
        # Update grammar text
        grammar = entry.get('grammar', '')
        cleaned_grammar = self.clean_display_text(grammar) if grammar else "No grammar available"
        self.grammar_text.setPlainText(cleaned_grammar)
        if self.show_grammar_cb.isChecked():
            self.grammar_text.show()
        else:
            self.grammar_text.hide()

        if english_pron or ipa_pron:
            combined_pron = f"English: {english_pron or 'N/A'}\nIPA:     {ipa_pron or 'N/A'}"
            self.pronunciation_text.setPlainText(combined_pron)
        else:
            self.pronunciation_text.setPlainText("No pronunciation available")

        # If definition or pronunciation are missing, fetch them from AI
        if not definition or not english_pron or not ipa_pron:
            self.load_ai_data()

        # Handle image
        if self.enable_image_cb.isChecked() and entry.get('image_filename', ''):
            self.load_vocabulary_image(entry.get('image_filename', ''), entry.get('image_description', ''))
        else:
            self.image_viewer.hide()
        
        # Update navigation button states
        self.prev_vocab_btn.setEnabled(self.current_vocab_index > 0)
        self.next_vocab_btn.setEnabled(self.current_vocab_index < len(self.vocabulary_data) - 1)
        
        self.status_text.append(f"[{self.get_current_time()}] 📚 Displaying vocabulary entry {self.current_vocab_index + 1}/{len(self.vocabulary_data)}: {entry['reference']}")
    
    def previous_vocabulary(self):
        """Navigate to previous vocabulary entry"""
        if self.current_vocab_index > 0:
            self.current_vocab_index -= 1
            self.display_current_vocabulary()
    
    def next_vocabulary(self):
        """Navigate to next vocabulary entry"""
        if self.current_vocab_index < len(self.vocabulary_data) - 1:
            self.current_vocab_index += 1
            self.display_current_vocabulary()
    
    def load_vocabulary_image(self, image_filename, image_description=""):
        """Load and display vocabulary image"""
        try:
            # Handle missing file extensions
            base_filename = Path(image_filename).stem
            file_extension = Path(image_filename).suffix.lower()
            
            # If no extension provided, try common image extensions
            if not file_extension:
                possible_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
                self.status_text.append(f"[{self.get_current_time()}] ⚠️ No extension found for {image_filename}, will try common extensions")
            else:
                possible_extensions = [file_extension]
            
            # Check if we're loading from ZIP or filesystem
            if self.vocab_file_path and self.vocab_file_path.endswith('.zip'):
                # Load from ZIP file
                with zipfile.ZipFile(self.vocab_file_path, 'r') as zip_file:
                    # First, try to find the image in the "images" subdirectory
                    images_dir_path = "images/"
                    
                    # Try each possible extension
                    found_image_path = None
                    for ext in possible_extensions:
                        target_filename = f"{base_filename}{ext}"
                        image_path_in_images = f"{images_dir_path}{target_filename}"
                        
                        if image_path_in_images in zip_file.namelist():
                            found_image_path = image_path_in_images
                            self.status_text.append(f"[{self.get_current_time()}] 🖼️ Loading image from images/ directory: {found_image_path}")
                            break
                    
                    # If not found in images/ directory, search entire ZIP
                    if not found_image_path:
                        self.status_text.append(f"[{self.get_current_time()}] ⚠️ Image not found in images/ directory, searching entire ZIP...")
                        image_files = [f for f in zip_file.namelist() 
                                     if not f.endswith('/') and '.' in f.split('/')[-1]]
                        
                        # Try to find the image by base filename with any extension
                        for ext in possible_extensions:
                            target_filename_lower = f"{base_filename}{ext}".lower()
                            for img_path in image_files:
                                if Path(img_path).name.lower() == target_filename_lower:
                                    found_image_path = img_path
                                    self.status_text.append(f"[{self.get_current_time()}] 🖼️ Found image in ZIP (alternative location): {found_image_path}")
                                    break
                            if found_image_path:
                                break
                    
                    if found_image_path and found_image_path in zip_file.namelist():
                        image_data = zip_file.read(found_image_path)
                        pixmap = QPixmap()
                        pixmap.loadFromData(image_data)
                    else:
                        self.status_text.append(f"[{self.get_current_time()}] ❌ Image not found in ZIP: {image_filename}")
                        self.image_viewer.setText(f"Image not found: {image_filename}")
                        self.image_viewer.show()
                        return
            else:
                # Load from filesystem
                image_path = Path(self.vocab_file_path).parent / image_filename
                if image_path.exists():
                    pixmap = QPixmap(str(image_path))
                else:
                    self.image_viewer.setText("Image file not found")
                    self.image_viewer.show()
                    return
            
            # Scale image to fit viewer (use maximum dimensions to prevent shrinking)
            if not pixmap.isNull():
                # Use maximum width/height to prevent cumulative shrinking
                max_width = self.image_viewer.maximumWidth()
                max_height = self.image_viewer.maximumHeight()
                
                # If maximum size is not set, use reasonable defaults
                if max_width <= 0:
                    max_width = 800  # Default maximum width
                if max_height <= 0:
                    max_height = 300  # Same as maximumHeight setting
                
                scaled_pixmap = pixmap.scaled(
                    max_width - 10,  # Leave margin
                    max_height - 10,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.image_viewer.setPixmap(scaled_pixmap)
                if image_description:
                    self.image_viewer.setToolTip(image_description)
                self.image_viewer.show()
            else:
                self.image_viewer.setText("Invalid image format")
                self.image_viewer.show()
                
        except Exception as e:
            self.status_text.append(f"[{self.get_current_time()}] ❌ Image loading error: {str(e)}")
            self.image_viewer.setText("Error loading image")
            self.image_viewer.show()
    
    def toggle_image_display(self, enabled):
        """Toggle image viewer visibility"""
        if enabled and self.vocabulary_data and self.current_vocab_index >= 0:
            entry = self.vocabulary_data[self.current_vocab_index]
            if entry.get('image_filename', ''):
                self.load_vocabulary_image(entry.get('image_filename', ''), entry.get('image_description', ''))
            else:
                self.image_viewer.setText("No image available for current entry")
                self.image_viewer.show()
        else:
            self.image_viewer.hide()
    
    def browse_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select Audio File", "", 
            "Audio Files (*.wav *.mp3);;All Files (*)"
        )
        if filename:
            self.audio_file = filename
            self.file_label.setText(os.path.basename(filename))
            self.playback_btn.setEnabled(True)
            self.convert_btn.setEnabled(True)
    
    def start_recording(self):
        if self.is_recording:
            return
        
        self.is_recording = True
        self.record_btn.setText("⏹️ Stop Recording")
        self.output_text.setText("Recording... Release button to stop")
        
        self.record_thread = RecordThread(sample_rate=self.config['sample_rate'])
        self.record_thread.finished.connect(self.on_record_finished)
        self.record_thread.error.connect(self.on_error)
        self.record_thread.start()
    
    def stop_recording(self):
        if not self.is_recording:
            return
        
        self.is_recording = False
        self.record_btn.setText("🎤 Hold to Record")
        
        if hasattr(self, 'record_thread') and self.record_thread:
            self.record_thread.stop_recording()
    
    def record_audio(self):
        # This method is kept for compatibility but not used for the hold-to-record functionality
        pass
    
    def on_record_finished(self, filename):
        self.recorded_file = filename
        self.audio_file = filename
        self.file_label.setText("Recorded audio")
        self.output_text.setText("Recording complete!")
        self.status_text.append(f"[{self.get_current_time()}] Recording completed: {os.path.basename(filename)}")
        self.is_recording = False
        self.record_btn.setText("🎤 Hold to Record")
        self.playback_btn.setEnabled(True)
        self.convert_btn.setEnabled(True)
        
        # Auto-check functionality
        if self.auto_check_cb.isChecked():
            self.status_text.append(f"[{self.get_current_time()}] Auto-check enabled - starting ASR conversion...")
            self.convert_audio()
    
    def on_error(self, error_msg):
        QMessageBox.critical(self, "Error", error_msg)
        self.is_recording = False
        self.record_btn.setText("🎤 Hold to Record")
        self.record_btn.setEnabled(True)  # Re-enable the button
        self.convert_btn.setEnabled(True)
        self.output_text.setText(f"Error: {error_msg}")
    
    def playback_audio(self):
        if not self.audio_file:
            QMessageBox.warning(self, "No Audio", "Please load or record audio first.")
            return
        
        try:
            data, samplerate = sf.read(self.audio_file)
            sd.play(data, samplerate)
            self.output_text.setText("Playing audio...")
        except Exception as e:
            QMessageBox.critical(self, "Playback Error", str(e))
    
    def convert_audio(self):
        if not self.audio_file:
            QMessageBox.warning(self, "No Audio", "Please load or record audio first.")
            return
        
        # Check if reference text is needed
        reference = None
        if self.training_mode_cb.isChecked():
            reference = self.reference_text.text().strip()
            print(f"DEBUG: Training mode enabled, reference text: '{reference}'")
            if not reference:
                QMessageBox.warning(self, "No Reference", 
                                  "Please enter reference text for pronunciation training.")
                return
        else:
            print(f"DEBUG: Training mode disabled")
        
        # Convert MP3 to WAV if needed
        audio_file = self.audio_file
        if self.audio_file.lower().endswith('.mp3'):
            try:
                audio = AudioSegment.from_mp3(self.audio_file)
                audio_file = tempfile.mktemp(suffix='.wav')
                audio.export(audio_file, format='wav')
            except Exception as e:
                QMessageBox.critical(self, "Conversion Error", 
                                   f"Failed to convert MP3: {str(e)}")
                return
        
        self.convert_btn.setEnabled(False)
        self.output_text.setText(f"Processing with {self.config['engine']}...")
        
        self.asr_thread = ASRThread(
            audio_file, 
            self.config,
            self.punctuation_cb.isChecked(),
            self.word_time_cb.isChecked(),
            reference
        )
        self.asr_thread.finished.connect(self.on_asr_finished)
        self.asr_thread.error.connect(self.on_error)
        self.asr_thread.start()
    
    def on_asr_finished(self, text, metadata):
        # Debug logging
        print(f"DEBUG: ASR finished callback called")
        print(f"DEBUG: Metadata keys: {list(metadata.keys()) if metadata else 'None'}")
        
        result = text
        if 'word_times' in metadata:
            result += "\n\n--- Word Timestamps ---\n" + metadata['word_times']
        
        self.output_text.setText(result)
        
        # Handle pronunciation feedback
        print(f"DEBUG: Checking for pronunciation data...")
        print(f"DEBUG: metadata is None: {metadata is None}")
        if metadata is not None:
            print(f"DEBUG: metadata keys: {list(metadata.keys())}")
            print(f"DEBUG: 'pronunciation' in metadata: {'pronunciation' in metadata}")
        
        if metadata and 'pronunciation' in metadata:
            print(f"DEBUG: Found pronunciation data in metadata")
            self.pronunciation_data = metadata['pronunciation']
            self.display_pronunciation_feedback(metadata['pronunciation'])
            print(f"DEBUG: Enabling save report button")
            self.save_report_btn.setEnabled(True)
            print(f"DEBUG: Save report button enabled: {self.save_report_btn.isEnabled()}")
        else:
            print(f"DEBUG: No pronunciation data found in metadata")
            if self.training_mode_cb.isChecked():
                print(f"DEBUG: Training mode is enabled but no pronunciation data received")
                self.output_text.append("\n⚠ Warning: Pronunciation training enabled but no analysis performed.")
        
        self.convert_btn.setEnabled(True)
    
    def display_pronunciation_feedback(self, pron_data):
        """Display detailed pronunciation feedback"""
        print(f"DEBUG: display_pronunciation_feedback called")
        print(f"DEBUG: Pronunciation data keys: {list(pron_data.keys())}")
        print(f"DEBUG: Accuracy: {pron_data.get('accuracy', 'N/A')}")
        print(f"DEBUG: Word analysis count: {len(pron_data.get('word_analysis', []))}")
        
        accuracy = pron_data['accuracy']
        threshold = self.config['pronunciation_threshold']
        
        # Update accuracy display
        self.accuracy_label.setText(f"{accuracy:.1f}%")
        self.accuracy_bar.setValue(int(accuracy))
        
        # Color code the accuracy
        if accuracy >= threshold:
            color = "green"
            status = "Excellent!"
        elif accuracy >= threshold - 10:
            color = "orange"
            status = "Good"
        else:
            color = "red"
            status = "Needs Improvement"
        
        self.accuracy_label.setStyleSheet(f"color: {color};")
        
        # Generate detailed feedback
        feedback = f"=== PRONUNCIATION FEEDBACK ===\n\n"
        feedback += f"Overall Accuracy: {accuracy:.1f}% - {status}\n"
        feedback += f"Threshold: {threshold}%\n\n"
        
        feedback += f"Reference Text:\n{pron_data['reference']}\n\n"
        feedback += f"Your Pronunciation:\n{pron_data['recognized']}\n\n"
        
        feedback += "=== WORD-BY-WORD ANALYSIS ===\n\n"
        
        correct_count = 0
        total_count = len(pron_data['word_analysis'])
        
        for i, word_info in enumerate(pron_data['word_analysis'], 1):
            status = word_info['status']
            ref = word_info['reference']
            rec = word_info['recognized']
            sim = word_info['similarity']
            
            if status == "correct":
                feedback += f"{i}. ✓ '{ref}' → '{rec}' ({sim:.1f}%)\n"
                correct_count += 1
            elif status == "incorrect":
                feedback += f"{i}. ✗ '{ref}' → '{rec}' ({sim:.1f}%) - Mispronounced\n"
            elif status == "missing":
                feedback += f"{i}. ✗ '{ref}' → [MISSING] - Word not pronounced\n"
            elif status == "extra":
                feedback += f"{i}. ⚠ [EXTRA] → '{rec}' - Extra word added\n"
        
        feedback += f"\n=== SUMMARY ===\n"
        feedback += f"Correct Words: {correct_count}/{total_count}\n"
        feedback += f"Word Accuracy: {(correct_count/total_count*100) if total_count > 0 else 0:.1f}%\n\n"
        
        # Recommendations
        feedback += "=== RECOMMENDATIONS ===\n"
        if accuracy >= threshold:
            feedback += "• Great job! Your pronunciation is excellent.\n"
            feedback += "• Try practicing more complex sentences.\n"
        elif accuracy >= threshold - 10:
            feedback += "• Good effort! Focus on the mispronounced words.\n"
            feedback += "• Practice speaking more slowly and clearly.\n"
        else:
            feedback += "• Review the reference text carefully.\n"
            feedback += "• Practice each word individually.\n"
            feedback += "• Speak slowly and enunciate clearly.\n"
            feedback += "• Consider listening to native speakers.\n"
        
        self.feedback_text.setText(feedback)
        
        # Switch to feedback tab
        self.tabs.setCurrentIndex(1)
    
    def play_tts(self):
        """Play text-to-speech for the reference text"""
        text = self.reference_text.text().strip()
        if not text:
            QMessageBox.warning(self, "No Text", "Please enter text to convert to speech.")
            return
        
        try:
            # Get language code from config (first part before dash)
            lang_code = self.config['language'].split('-')[0].lower()
            
            # Create TTS object
            tts = gTTS(text=text, lang=lang_code, slow=False)
            
            # Create temporary file in memory
            mp3_fp = io.BytesIO()
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)
            
            # Initialize pygame mixer
            pygame.mixer.init()
            pygame.mixer.music.load(mp3_fp)
            pygame.mixer.music.play()
            
            self.output_text.append(f"🔊 Playing TTS: '{text}' in {self.config['language_name']}")
            
        except Exception as e:
            QMessageBox.critical(self, "TTS Error", f"Failed to play text-to-speech: {str(e)}")
            self.output_text.append(f"❌ TTS Error: {str(e)}")
    
    def play_slow_tts(self):
        """Play reference text one word at a time with pauses"""
        text = self.reference_text.text().strip()
        if not text:
            QMessageBox.warning(self, "No Text", "Please enter text to convert to speech.")
            return
        
        try:
            # Split text into words (handle various punctuation)
            import re
            words = re.findall(r'\S+', text)  # Split on whitespace, keep punctuation with words
            
            if not words:
                QMessageBox.warning(self, "No Words", "No words found in the text.")
                return
            
            # Disable buttons during playback
            self.slow_tts_btn.setEnabled(False)
            self.tts_btn.setEnabled(False)
            
            # Get language code
            lang_code = self.config['language'].split('-')[0].lower()
            
            # Create a separate thread for word-by-word playback
            def play_words_sequentially():
                try:
                    pygame.mixer.init()
                    
                    for i, word in enumerate(words):
                        # Skip empty words
                        if not word.strip():
                            continue
                        
                        # Update status
                        self.status_text.append(f"[{self.get_current_time()}] Playing word {i+1}/{len(words)}: '{word}'")
                        
                        # Create TTS for single word
                        tts = gTTS(text=word, lang=lang_code, slow=True)
                        
                        # Create temporary file in memory
                        mp3_fp = io.BytesIO()
                        tts.write_to_fp(mp3_fp)
                        mp3_fp.seek(0)
                        
                        # Play the word
                        pygame.mixer.music.load(mp3_fp)
                        pygame.mixer.music.play()
                        
                        # Wait for playback to finish
                        while pygame.mixer.music.get_busy():
                            time.sleep(0.1)
                        
                        # Add pause between words (500ms)
                        if i < len(words) - 1:  # Don't pause after the last word
                            time.sleep(0.5)
                    
                    # Re-enable buttons
                    self.slow_tts_btn.setEnabled(True)
                    self.tts_btn.setEnabled(True)
                    self.status_text.append(f"[{self.get_current_time()}] Slow TTS playback completed")
                    self.output_text.append(f"🐢 Slow TTS completed: {len(words)} words played")
                    
                except Exception as e:
                    # Re-enable buttons on error
                    self.slow_tts_btn.setEnabled(True)
                    self.tts_btn.setEnabled(True)
                    QMessageBox.critical(self, "Slow TTS Error", f"Failed to play slow text-to-speech: {str(e)}")
                    self.output_text.append(f"❌ Slow TTS Error: {str(e)}")
            
            # Start the playback thread
            playback_thread = threading.Thread(target=play_words_sequentially, daemon=True)
            playback_thread.start()
            
        except Exception as e:
            # Re-enable buttons on error
            self.slow_tts_btn.setEnabled(True)
            self.tts_btn.setEnabled(True)
            QMessageBox.critical(self, "Slow TTS Error", f"Failed to initialize slow text-to-speech: {str(e)}")
            self.output_text.append(f"❌ Slow TTS Initialization Error: {str(e)}")
    
    def on_error(self, error_msg):
        QMessageBox.critical(self, "Error", error_msg)
        self.record_btn.setEnabled(True)
        self.convert_btn.setEnabled(True)
        self.output_text.setText(f"Error: {error_msg}")
    
    def save_text(self):
        text = self.output_text.toPlainText()
        if not text:
            QMessageBox.warning(self, "No Text", "No text to save.")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Text", "", "Text Files (*.txt);;All Files (*)"
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(text)
                QMessageBox.information(self, "Success", "Text saved successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", str(e))
    
    def save_report(self):
        """Save pronunciation training report"""
        if not self.pronunciation_data:
            QMessageBox.warning(self, "No Report", "No pronunciation report to save.")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Pronunciation Report", "", 
            "Text Files (*.txt);;HTML Files (*.html);;All Files (*)"
        )
        if filename:
            try:
                report_text = self.feedback_text.toPlainText()
                report_text += f"\n\n=== SESSION INFO ===\n"
                report_text += f"Language: {self.config['language_name']}\n"
                report_text += f"Engine: {self.config['engine']}\n"
                report_text += f"Model: {self.config['model']}\n"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(report_text)
                QMessageBox.information(self, "Success", "Report saved successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", str(e))
    
    def show_help(self):
        help_text = """ASR Application with Pronunciation Training

🚀 GETTING STARTED
1. Load Vocabulary:
   - Click "📁 Load Vocabulary" to import CSV/TXT/ZIP files
   - Supports custom column mappings and multiple delimiters

2. Configure Settings (Optional):
   - Click ⚙ to select engine, language, and AI model
   - Customize column mappings for your file structure

3. Navigate and Practice:
   - Use Previous/Next buttons to browse vocabulary
   - Click "🔊 Play TTS" or "🐢 Slow TTS" for audio playback
   - Hold record button to practice pronunciation
   - Click "🔄 ASR Convert" for detailed feedback

📚 VOCABULARY MANAGEMENT
• Load from CSV, TXT, or ZIP archives
• Automatic AI enhancement for missing definitions/pronunciations
• Image support with ZIP archive integration
• Customizable column mapping (1-6 columns)
• Multiple delimiter support (comma, pipe, tab, semicolon)

🔊 PRONUNCIATION TRAINING
1. Select vocabulary item or enter custom text
2. Listen to model pronunciation (normal/slow speed)
3. Record your attempt (hold to record, release to stop)
4. Get comprehensive feedback including:
   • Overall accuracy score (percentage)
   • Word-by-word analysis
   • Mispronounced words identification
   • Missing/extra words detection
   • Personalized improvement recommendations
   • Color-coded results (🟢Excellent 🟡Good 🔴Needs Practice)

🤖 AI INTEGRATION
• Automatic content enhancement for incomplete vocabulary
• Smart definitions and pronunciation guides
• Fallback to local IPA when AI unavailable
• Visual status indicators:
  ⚪ Disconnected | 🟢 Connected | 🔴 Busy/Error | 🟡 Connecting

🔧 AUDIO FEATURES
• Multiple speech recognition engines (Google, Vosk, Whisper)
• Text-to-Speech with normal and slow playback
• ASR conversion with accuracy scoring
• Configurable energy threshold and sensitivity
• Support for WAV and MP3 file formats

📋 SUPPORTED LANGUAGES
Greek (default), English, Spanish, French, German, 
Italian, Portuguese, Russian, Chinese, Japanese, 
Korean, Arabic, and more

💡 TIPS FOR BEST RESULTS
• Use Whisper engine for highest accuracy
• Practice in quiet environment
• Speak clearly at moderate pace
• Focus on one challenging sound at a time
• Regular practice yields best improvement
• Check AI status indicator for optimal performance

📄 SAVE OPTIONS
• Export transcribed text
• Save detailed pronunciation reports
• Preserve practice session data

❓ NEED MORE HELP?
Refer to HELP.md for comprehensive documentation
or check the status area for detailed error messages."""
        
        QMessageBox.information(self, "Help", help_text)
    
    def show_about(self):
        about_text = """ASR Application v2.0
Pronunciation Training Edition

Automatic Speech Recognition tool supporting:
• Google Speech Recognition
• OpenAI Whisper

NEW FEATURES:
• Pronunciation accuracy scoring
• Word-by-word analysis
• Mispronunciation detection
• Training recommendations
• Detailed feedback reports
• Push-to-start/Push-to-stop recording
• Text-to-Speech (TTS) pronunciation guide

Default Language: Greek (el-GR)

Supports multiple languages and audio formats.

Built with PyQt5 and Python.
Perfect for language learners!"""
        
        QMessageBox.about(self, "About ASR App", about_text)
    
    def text_to_ipa(self, text):
        """Convert English text to IPA pronunciation
        Args:
            text: English text to convert
        Returns:
            IPA pronunciation string
        """
        return self.text_to_ipa_modern(text)
    
    def text_to_ipa_modern(self, text):
        """Convert English text to modern, accurate IPA pronunciation"""
        # Enhanced English to IPA mapping with better accuracy
        ipa_map = {
            # Vowels - short
            'a': 'æ', 'e': 'ɛ', 'i': 'ɪ', 'o': 'ɒ', 'u': 'ʌ',
            # Vowels - long
            'aa': 'ɑː', 'ee': 'iː', 'ii': 'aɪ', 'oo': 'uː', 'uu': 'uː',
            # Consonants
            'b': 'b', 'c': 'k', 'd': 'd', 'f': 'f', 'g': 'ɡ',
            'h': 'h', 'j': 'dʒ', 'k': 'k', 'l': 'l', 'm': 'm',
            'n': 'n', 'p': 'p', 'q': 'k', 'r': 'ɹ', 's': 's',
            't': 't', 'v': 'v', 'w': 'w', 'x': 'ks', 'y': 'j', 'z': 'z',
            # Common digraphs and trigraphs
            'th': 'θ', 'ch': 'tʃ', 'sh': 'ʃ', 'ph': 'f', 'wh': 'ʍ',
            'ck': 'k', 'qu': 'kw', 'ng': 'ŋ', 'gh': 'ɡ', 'sc': 'sk',
            'sch': 'sk', 'scr': 'skɹ', 'shr': 'ʃɹ', 'thr': 'θɹ',
            # Vowel combinations - diphthongs
            'ai': 'eɪ', 'ay': 'eɪ', 'au': 'ɔː', 'aw': 'ɔː',
            'ea': 'iː', 'ee': 'iː', 'ei': 'aɪ', 'ey': 'aɪ',
            'ie': 'aɪ', 'oa': 'əʊ', 'oo': 'uː', 'ou': 'aʊ', 'ow': 'aʊ',
            'ue': 'uː', 'ui': 'aɪ', 'ew': 'juː', 'oi': 'ɔɪ', 'oy': 'ɔɪ',
            'ar': 'ɑː', 'er': 'ɜː', 'ir': 'ɜː', 'or': 'ɔː', 'ur': 'ɜː',
            # Silent letters and special cases
            'kn': 'n', 'gn': 'n', 'wr': 'ɹ', 'mb': 'm',
            # Common words and phrases
            'the': 'ðə', 'and': 'ənd', 'of': 'əv', 'to': 'tu', 'in': 'ɪn',
            'is': 'ɪz', 'it': 'ɪt', 'you': 'juː', 'he': 'hiː', 'she': 'ʃiː',
            'we': 'wiː', 'they': 'ðeɪ', 'are': 'ɑː', 'was': 'wɒz', 'were': 'wɜː',
            'have': 'hæv', 'has': 'hæz', 'had': 'hæd', 'do': 'duː', 'does': 'dʌz',
            'did': 'dɪd', 'will': 'wɪl', 'would': 'wʊd', 'can': 'kæn', 'could': 'kʊd',
            'shall': 'ʃæl', 'should': 'ʃʊd', 'may': 'meɪ', 'might': 'maɪt',
            'must': 'mʌst', 'ought': 'ɔːt', 'need': 'niːd'
        }
        
        # Preprocessing
        text = text.lower().strip()
        words = text.split()
        ipa_words = []
        
        for word in words:
            # Remove punctuation for processing but keep it for output
            clean_word = ''.join(c for c in word if c.isalnum())
            punctuation = ''.join(c for c in word if not c.isalnum())
            
            if not clean_word:
                if punctuation:
                    ipa_words.append(punctuation)
                continue
            
            # Word-specific exceptions
            if clean_word in ['been', 'read']:
                # Context-sensitive pronunciation would go here
                pass
            
            # Convert the clean word
            ipa_word = ""
            i = 0
            
            while i < len(clean_word):
                # Check for longest possible matches first
                matched = False
                
                # Check trigraphs
                if i <= len(clean_word) - 3:
                    trigraph = clean_word[i:i+3]
                    if trigraph in ipa_map:
                        ipa_word += ipa_map[trigraph]
                        i += 3
                        matched = True
                        continue
                
                # Check digraphs
                if i <= len(clean_word) - 2:
                    digraph = clean_word[i:i+2]
                    if digraph in ipa_map:
                        ipa_word += ipa_map[digraph]
                        i += 2
                        matched = True
                        continue
                
                # Check single characters
                char = clean_word[i]
                if char in ipa_map:
                    ipa_word += ipa_map[char]
                elif char.isalpha():
                    # Unknown letters - use closest approximation
                    ipa_word += char
                
                i += 1
            
            # Add back punctuation
            if punctuation:
                ipa_word += punctuation
                
            ipa_words.append(ipa_word)
        
        return ' '.join(ipa_words)
    
    def update_combined_pronunciation(self):
        """Update combined pronunciation display (English + IPA) in pronunciation text box"""
        try:
            english_text = self.reference_text.text().strip()
            if not english_text:
                self.pronunciation_text.setPlainText("Enter text above to see English and IPA pronunciation...")
                return
            
            # Convert to IPA using modern algorithm
            ipa_text = self.text_to_ipa_modern(english_text)
            
            # Display both English and IPA in the pronunciation text box
            display_text = f"English: {english_text}\nIPA:     {ipa_text}"
            self.pronunciation_text.setPlainText(display_text)
            
            # Update status
            self.status_text.append(f"[{self.get_current_time()}] 🔄 Combined pronunciation updated")
            
        except Exception as e:
            self.status_text.append(f"[{self.get_current_time()}] ❌ Pronunciation conversion error: {str(e)}")
    
    def change_font_size(self, text_widget, delta):
        """Change font size for text widgets
        Args:
            text_widget: The text widget to modify (QLineEdit or QTextEdit)
            delta: Size change (+1 to increase, -1 to decrease)
        """
        try:
            # Get current font
            if isinstance(text_widget, QLineEdit):
                current_font = text_widget.font()
            else:  # QTextEdit
                current_font = text_widget.currentFont()
            
            # Get current point size
            current_size = current_font.pointSize()
            if current_size == -1:  # If pointSize returns -1, use default
                current_size = 10
            
            # Calculate new size (minimum 6pt, maximum 72pt)
            new_size = max(6, min(72, current_size + delta))
            
            # Apply new font size
            current_font.setPointSize(new_size)
            
            if isinstance(text_widget, QLineEdit):
                text_widget.setFont(current_font)
            else:  # QTextEdit
                text_widget.selectAll()
                text_widget.setCurrentFont(current_font)
                text_widget.setTextColor(text_widget.textColor())  # Reset selection
            
            # Update status
            widget_name = {
                self.reference_text: "Reference Text",
                self.pronunciation_text: "Pronunciation",
                self.definition_text: "Definition",
                self.output_text: "ASR Output",
                self.feedback_text: "Feedback",
                self.status_text: "Status"
            }.get(text_widget, "Unknown")
            
            self.status_text.append(f"[{self.get_current_time()}] {widget_name} font size changed to {new_size}pt")
            
        except Exception as e:
            self.status_text.append(f"[{self.get_current_time()}] Font size change error: {str(e)}")
    
    def change_all_text_boxes_font_size(self, delta):
        """Return a function that changes font size for all three text boxes below Pronunciation"""
        def change_size():
            try:
                # List of text boxes to modify
                text_boxes = [
                    self.pronunciation_text,
                    self.definition_text,
                    self.grammar_text # Added grammar text box
                ]
                
                # Get current font size from pronunciation text (as reference)
                current_font = self.pronunciation_text.currentFont()
                current_size = current_font.pointSize()
                if current_size == -1:
                    current_size = 14  # Default size
                
                # Calculate new size
                new_size = max(6, min(72, current_size + delta))
                
                # Apply new font size to all text boxes
                for text_box in text_boxes:
                    font = text_box.currentFont()
                    font.setPointSize(new_size)
                    text_box.selectAll()
                    text_box.setCurrentFont(font)
                    text_box.setTextColor(text_box.textColor())  # Reset selection
                
                # Update status
                self.status_text.append(f"[{self.get_current_time()}] All text boxes font size changed to {new_size}pt")
                
            except Exception as e:
                self.status_text.append(f"[{self.get_current_time()}] Font size change error: {str(e)}")
        
        return change_size
    
    def get_current_time(self):
        """Get current timestamp for status messages"""
        return datetime.now().strftime("%H:%M:%S")
    
    def show_config(self):
        dialog = ConfigDialog(self)
        # Set current values
        dialog.engine_combo.setCurrentText(self.config['engine'])
        dialog.lang_combo.setCurrentText(self.config['language_name'])
        dialog.model_combo.setCurrentText(self.config['model'])
        dialog.rate_entry.setText(str(self.config['sample_rate']))
        dialog.energy_entry.setText(str(self.config['energy_threshold']))
        dialog.pron_spin.setValue(self.config['pronunciation_threshold'])
        
        if dialog.exec_() == QDialog.Accepted:
            self.config = dialog.get_config()
            QMessageBox.information(self, "Configuration", 
                                  f"Engine: {self.config['engine']}\n"
                                  f"Language: {self.config['language_name']}\n"
                                  f"Model: {self.config['model']}\n"
                                  f"Pronunciation Threshold: {self.config['pronunciation_threshold']}%")


def main():
    app = QApplication(sys.argv)
    window = ASRApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
