"""
Main Window module for ASR Application
Contains the main ASRApp class with PyQt5 GUI logic
"""

import sys
import os
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path

import pygame
import sounddevice as sd
import soundfile as sf
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QLabel,
    QFileDialog,
    QMessageBox,
    QToolButton,
    QGroupBox,
    QProgressBar,
    QTabWidget,
    QLineEdit,
    QCheckBox,
    QSpinBox,
    QGridLayout,
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon, QFont, QPixmap

# Import modular components
from config import ConfigDialog, DEFAULT_CONFIG
from core.recorder import RecordThread
from core.asr_engines import ASRThread
from core.tts_engines import TTSThread
from utils.text_processing import (
    normalize_text,
    clean_ai_response,
    clean_display_text,
    text_to_ipa_modern,
)
from utils.storage import (
    save_text_to_file,
    generate_pronunciation_report,
    SessionStorage,
)
from ui.flashcards import FlashcardDialog, FlashcardProgress
from ui.components import (
    PronunciationFeedbackWidget,
    AudioLevelIndicator,
    ImageViewer,
    StatusLog,
    RecordingButton,
    VocabularyNavigator,
)


class ASRApp(QMainWindow):
    """Main ASR Application Window"""

    def __init__(self):
        super().__init__()
        self.audio_file = None
        self.recorded_file = None
        self.config = DEFAULT_CONFIG.copy()
        self.pronunciation_data = None

        # Vocabulary file handling attributes
        self.vocabulary_data = []
        self.current_vocab_index = -1
        self.vocab_file_path = None
        self.image_directory = None

        # TTS engine

        self.tts_thread = None

        # Session storage
        self.session_storage = SessionStorage()

        # Flashcard progress
        self.flashcard_progress = FlashcardProgress()

        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
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

        self.flashcard_btn = QToolButton()
        self.flashcard_btn.setText("🎴")
        self.flashcard_btn.setToolTip("Flashcard Mode")
        self.flashcard_btn.clicked.connect(self.show_flashcard_mode)

        self.stats_btn = QToolButton()
        self.stats_btn.setText("📊")
        self.stats_btn.setToolTip("View Statistics")
        self.stats_btn.clicked.connect(self.show_statistics)

        self.help_btn = QToolButton()
        self.help_btn.setText("?")
        self.help_btn.setToolTip("Help")
        self.help_btn.clicked.connect(self.show_help)

        self.about_btn = QToolButton()
        self.about_btn.setText("ℹ")
        self.about_btn.setToolTip("About")
        self.about_btn.clicked.connect(self.show_about)

        toolbar.addWidget(self.config_btn)
        toolbar.addWidget(self.flashcard_btn)
        toolbar.addWidget(self.stats_btn)
        toolbar.addWidget(self.help_btn)
        toolbar.addWidget(self.about_btn)
        main_layout.addLayout(toolbar)

        # Pronunciation Training Mode
        pron_group = QGroupBox("Pronunciation Training Mode")
        pron_layout = QVBoxLayout()

        # First row: Training mode and checkboxes
        mode_layout = QHBoxLayout()
        self.training_mode_cb = QCheckBox("Enable Pronunciation Training")
        self.training_mode_cb.setChecked(True)
        self.training_mode_cb.toggled.connect(self.toggle_training_mode)

        self.show_pronunciation_cb = QCheckBox("Show Pronunciation")
        self.show_pronunciation_cb.setChecked(True)
        self.show_pronunciation_cb.toggled.connect(self.toggle_pronunciation_display)

        self.show_definition_cb = QCheckBox("Show Definition/Translation")
        self.show_definition_cb.setChecked(True)

        self.show_grammar_cb = QCheckBox("Show Grammar")
        self.show_grammar_cb.setChecked(False)
        self.show_grammar_cb.toggled.connect(self.toggle_grammar_display)

        mode_layout.addWidget(self.training_mode_cb)
        mode_layout.addWidget(self.show_pronunciation_cb)
        mode_layout.addWidget(self.show_definition_cb)
        mode_layout.addWidget(self.show_grammar_cb)
        mode_layout.addStretch()
        pron_layout.addLayout(mode_layout)

        # Vocabulary file loading section
        vocab_layout = QHBoxLayout()
        vocab_layout.addWidget(QLabel("Vocabulary File:"))

        self.vocab_file_label = QLabel("No file loaded")
        self.vocab_file_label.setMinimumWidth(150)
        vocab_layout.addWidget(self.vocab_file_label)

        self.load_vocab_btn = QPushButton("📁 Load Vocabulary")
        self.load_vocab_btn.clicked.connect(self.load_vocabulary_file)
        vocab_layout.addWidget(self.load_vocab_btn)

        self.enable_image_cb = QCheckBox("Enable Image")
        self.enable_image_cb.setChecked(False)
        vocab_layout.addWidget(self.enable_image_cb)

        vocab_layout.addStretch()
        pron_layout.addLayout(vocab_layout)

        # Navigation buttons
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
        pron_layout.addLayout(nav_layout)

        # Reference text row
        ref_layout = QHBoxLayout()
        ref_layout.addWidget(QLabel("Reference Text:"))
        self.reference_text = QLineEdit()
        self.reference_text.setPlaceholderText("Enter the text you want to practice...")
        ref_font = QFont()
        ref_font.setPointSize(14)
        self.reference_text.setFont(ref_font)
        self.reference_text.setEnabled(True)
        self.reference_text.textChanged.connect(self.update_combined_pronunciation)

        # Font size controls for reference text
        self.ref_font_minus_btn = QPushButton("-")
        self.ref_font_minus_btn.setFixedWidth(25)
        self.ref_font_minus_btn.clicked.connect(
            lambda: self.change_font_size(self.reference_text, -1)
        )

        self.ref_font_plus_btn = QPushButton("+")
        self.ref_font_plus_btn.setFixedWidth(25)
        self.ref_font_plus_btn.clicked.connect(
            lambda: self.change_font_size(self.reference_text, 1)
        )

        ref_layout.addWidget(self.ref_font_minus_btn)
        ref_layout.addWidget(self.ref_font_plus_btn)
        ref_layout.addWidget(self.reference_text)

        # TTS buttons
        self.tts_btn = QPushButton("🔊 Play TTS")
        self.tts_btn.clicked.connect(self.play_tts)
        ref_layout.addWidget(self.tts_btn)

        self.slow_tts_btn = QPushButton("🐢 Slow TTS")
        self.slow_tts_btn.clicked.connect(self.play_slow_tts)
        ref_layout.addWidget(self.slow_tts_btn)

        pron_layout.addLayout(ref_layout)

        # Pronunciation text box
        self.pronunciation_text = QTextEdit()
        self.pronunciation_text.setMaximumHeight(80)
        self.pronunciation_text.setPlaceholderText(
            "Enter text above to see English and IPA pronunciation..."
        )
        self.pronunciation_text.setReadOnly(True)
        self.pronunciation_text.setFont(QFont("Arial", 14))
        pron_layout.addWidget(self.pronunciation_text)

        # Definition text box
        self.definition_text = QTextEdit()
        self.definition_text.setMaximumHeight(90)
        self.definition_text.setPlaceholderText(
            "Definition/translation will appear here..."
        )
        self.definition_text.setReadOnly(True)
        self.definition_text.setFont(QFont("Arial", 12))
        pron_layout.addWidget(self.definition_text)

        # Grammar text box
        self.grammar_text = QTextEdit()
        self.grammar_text.setMaximumHeight(90)
        self.grammar_text.setPlaceholderText(
            "Grammar related to the reference text will appear here..."
        )
        self.grammar_text.setReadOnly(True)
        self.grammar_text.setFont(QFont("Arial", 12))
        self.grammar_text.hide()
        pron_layout.addWidget(self.grammar_text)

        # Image viewer
        self.image_viewer = QLabel()
        self.image_viewer.setMaximumHeight(300)
        self.image_viewer.setMaximumWidth(800)
        self.image_viewer.setAlignment(Qt.AlignCenter)
        self.image_viewer.setText("No image loaded")
        self.image_viewer.setStyleSheet(
            "border: 1px solid gray; background-color: #f0f0f0;"
        )
        self.image_viewer.hide()
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

        self.record_btn = RecordingButton()
        self.record_btn.recording_started.connect(self.start_recording)
        self.record_btn.recording_stopped.connect(self.stop_recording)

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

        self.auto_check_cb = QCheckBox("Auto Check After Record")
        self.auto_check_cb.setChecked(False)

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
        self.accuracy_bar.setValue(0)
        score_layout.addWidget(self.accuracy_bar)
        score_layout.addStretch()
        feedback_layout.addLayout(score_layout)

        # Feedback text
        self.feedback_text = QTextEdit()
        self.feedback_text.setReadOnly(True)
        self.feedback_text.setFont(font)
        self.feedback_text.setMinimumHeight(200)
        feedback_layout.addWidget(self.feedback_text)

        feedback_tab.setLayout(feedback_layout)

        self.tabs.addTab(asr_tab, "ASR Output")
        self.tabs.addTab(feedback_tab, "Pronunciation Feedback")
        main_layout.addWidget(self.tabs)

        # Status text box
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(60)
        self.status_text.setPlaceholderText(
            "Status and debug information will appear here..."
        )
        self.status_text.setReadOnly(True)
        font = QFont("Consolas", 9)
        self.status_text.setFont(font)
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

        # Show pronunciation and definition by default
        self.pronunciation_text.show()
        self.definition_text.show()

    # ============== Toggle Methods ==============

    def toggle_training_mode(self, enabled):
        """Toggle pronunciation training mode"""
        self.reference_text.setEnabled(enabled)
        self.tts_btn.setEnabled(enabled)
        self.slow_tts_btn.setEnabled(enabled)

        if enabled:
            self.show_pronunciation_cb.setChecked(True)
            self.show_definition_cb.setChecked(True)
            self.pronunciation_text.show()
            self.definition_text.show()
            self.grammar_text.show()
            self.tabs.setCurrentIndex(1)
        else:
            self.pronunciation_text.hide()
            self.definition_text.hide()
            self.grammar_text.hide()

    def toggle_pronunciation_display(self, enabled):
        """Toggle pronunciation text box visibility"""
        if enabled:
            self.pronunciation_text.show()
            if self.show_definition_cb.isChecked():
                self.definition_text.show()
            if self.show_grammar_cb.isChecked():
                self.grammar_text.show()
            self.update_combined_pronunciation()
        else:
            self.pronunciation_text.hide()
            self.definition_text.hide()
            self.grammar_text.hide()

    def toggle_grammar_display(self, enabled):
        """Toggle grammar text box visibility"""
        if enabled:
            self.grammar_text.show()
        else:
            self.grammar_text.hide()

    # ============== Vocabulary Methods ==============

    def load_vocabulary_file(self):
        """Load vocabulary from text, CSV, or ZIP file"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select Vocabulary File",
            "",
            "Vocabulary Files (*.txt *.csv *.zip);;All Files (*)",
        )

        if not filename:
            return

        try:
            from utils.storage import load_vocabulary_from_zip, load_csv

            self.status_text.append(
                f"[{self.get_current_time()}] Loading vocabulary: {os.path.basename(filename)}"
            )

            file_extension = Path(filename).suffix.lower()

            if file_extension == ".zip":
                self.vocabulary_data, _ = load_vocabulary_from_zip(
                    filename, self.config.get("vocab_columns")
                )
            elif file_extension in [".txt", ".csv"]:
                delimiter = self.config["vocab_delimiter"]
                column_mapping = self.config.get("vocab_columns")
                self.vocabulary_data = load_csv(
                    filename,
                    delimiter=delimiter,
                    has_header=True,
                    column_mapping=column_mapping,
                )
            else:
                QMessageBox.warning(
                    self,
                    "Unsupported Format",
                    f"Unsupported file format: {file_extension}",
                )
                return

            self.vocab_file_label.setText(os.path.basename(filename))
            self.vocab_file_path = filename

            if self.vocabulary_data:
                self.current_vocab_index = 0
                self.prev_vocab_btn.setEnabled(False)
                self.next_vocab_btn.setEnabled(len(self.vocabulary_data) > 1)
                self.display_current_vocabulary()
                self.status_text.append(
                    f"[{self.get_current_time()}] Loaded {len(self.vocabulary_data)} vocabulary entries"
                )
            else:
                QMessageBox.warning(
                    self, "Empty File", "No vocabulary entries found in file"
                )

        except Exception as e:
            QMessageBox.critical(
                self, "Load Error", f"Failed to load vocabulary: {str(e)}"
            )
            self.status_text.append(
                f"[{self.get_current_time()}] Error loading vocabulary: {str(e)}"
            )

    def display_current_vocabulary(self):
        """Display the current vocabulary entry"""
        if not self.vocabulary_data or self.current_vocab_index < 0:
            return

        entry = self.vocabulary_data[self.current_vocab_index]

        # Update reference text
        self.reference_text.setText(entry.get("reference", ""))

        # Update definition
        definition = entry.get("definition", "")
        self.definition_text.setPlainText(
            clean_display_text(definition) if definition else "No definition available"
        )

        # Update grammar
        grammar = entry.get("grammar", "")
        self.grammar_text.setPlainText(
            clean_display_text(grammar) if grammar else "No grammar available"
        )

        # Update pronunciation
        english_pron = entry.get("english_pronunciation", "")
        ipa_pron = entry.get("ipa_pronunciation", "")
        if english_pron or ipa_pron:
            combined_pron = (
                f"English: {english_pron or 'N/A'}\nIPA:     {ipa_pron or 'N/A'}"
            )
            self.pronunciation_text.setPlainText(combined_pron)
        else:
            # Auto-generate IPA
            self.update_combined_pronunciation()

        # Handle image
        if self.enable_image_cb.isChecked() and entry.get("image_filename", ""):
            self.load_vocabulary_image(entry.get("image_filename", ""))
        else:
            self.image_viewer.hide()

        # Update navigation
        self.prev_vocab_btn.setEnabled(self.current_vocab_index > 0)
        self.next_vocab_btn.setEnabled(
            self.current_vocab_index < len(self.vocabulary_data) - 1
        )

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

    def load_vocabulary_image(self, image_filename):
        """Load and display vocabulary image"""
        try:
            # Implementation depends on whether image is in ZIP or filesystem
            if self.vocab_file_path and self.vocab_file_path.endswith(".zip"):
                import zipfile

                with zipfile.ZipFile(self.vocab_file_path, "r") as zip_file:
                    # Try to find image
                    base = Path(image_filename).stem
                    for name in zip_file.namelist():
                        if Path(name).stem == base:
                            image_data = zip_file.read(name)
                            pixmap = QPixmap()
                            pixmap.loadFromData(image_data)
                            if not pixmap.isNull():
                                self.image_viewer.setPixmap(
                                    pixmap.scaled(
                                        self.image_viewer.maximumWidth() - 20,
                                        self.image_viewer.maximumHeight() - 20,
                                        Qt.KeepAspectRatio,
                                    )
                                )
                                self.image_viewer.show()
                            return
            else:
                # Load from filesystem
                image_path = Path(self.vocab_file_path).parent / image_filename
                if image_path.exists():
                    pixmap = QPixmap(str(image_path))
                    self.image_viewer.setPixmap(
                        pixmap.scaled(
                            self.image_viewer.maximumWidth() - 20,
                            self.image_viewer.maximumHeight() - 20,
                            Qt.KeepAspectRatio,
                        )
                    )
                    self.image_viewer.show()

        except Exception as e:
            self.status_text.append(
                f"[{self.get_current_time()}] Image load error: {str(e)}"
            )

    # ============== Audio Methods ==============

    def browse_file(self):
        """Browse for audio file"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select Audio File", "", "Audio Files (*.wav *.mp3);;All Files (*)"
        )
        if filename:
            self.audio_file = filename
            self.file_label.setText(os.path.basename(filename))
            self.playback_btn.setEnabled(True)
            self.convert_btn.setEnabled(True)

    def start_recording(self):
        """Start audio recording"""
        self.output_text.setText("Recording...")
        self.record_thread = RecordThread(sample_rate=self.config["sample_rate"])
        self.record_thread.finished.connect(self.on_record_finished)
        self.record_thread.error.connect(self.on_error)
        self.record_thread.start()

    def stop_recording(self):
        """Stop audio recording"""
        if hasattr(self, "record_thread") and self.record_thread:
            self.record_thread.stop_recording()

    def on_record_finished(self, filename):
        """Handle recording completion"""
        self.recorded_file = filename
        self.audio_file = filename
        self.file_label.setText("Recorded audio")
        self.output_text.setText("Recording complete!")
        self.status_text.append(f"[{self.get_current_time()}] Recording completed")
        self.playback_btn.setEnabled(True)
        self.convert_btn.setEnabled(True)

        # Auto-check functionality
        if self.auto_check_cb.isChecked():
            self.convert_audio()

    def playback_audio(self):
        """Play back recorded audio"""
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
        """Convert audio to text using ASR"""
        if not self.audio_file:
            QMessageBox.warning(self, "No Audio", "Please load or record audio first.")
            return

        reference = None
        if self.training_mode_cb.isChecked():
            reference = self.reference_text.text().strip()
            if not reference:
                QMessageBox.warning(
                    self, "No Reference", "Please enter reference text."
                )
                return

        self.convert_btn.setEnabled(False)
        self.output_text.setText(f"Processing with {self.config['engine']}...")

        self.asr_thread = ASRThread(
            self.audio_file,
            self.config,
            self.punctuation_cb.isChecked(),
            self.word_time_cb.isChecked(),
            reference,
        )
        self.asr_thread.finished.connect(self.on_asr_finished)
        self.asr_thread.error.connect(self.on_error)
        self.asr_thread.start()

    def on_asr_finished(self, text, metadata):
        """Handle ASR completion"""
        result = text
        if "word_times" in metadata:
            result += "\n\n--- Word Timestamps ---\n" + metadata["word_times"]

        self.output_text.setText(result)

        # Handle pronunciation feedback
        if metadata and "pronunciation" in metadata:
            self.pronunciation_data = metadata["pronunciation"]
            self.display_pronunciation_feedback(metadata["pronunciation"])
            self.save_report_btn.setEnabled(True)

            # Save to session storage
            self.session_storage.add_session(
                {
                    "reference": metadata["pronunciation"].get("reference", ""),
                    "recognized": metadata["pronunciation"].get("recognized", ""),
                    "accuracy": metadata["pronunciation"].get("accuracy", 0),
                }
            )

        self.convert_btn.setEnabled(True)

    def display_pronunciation_feedback(self, pron_data):
        """Display detailed pronunciation feedback"""
        accuracy = pron_data["accuracy"]
        threshold = self.config["pronunciation_threshold"]

        # Update accuracy display
        self.accuracy_label.setText(f"{accuracy:.1f}%")
        self.accuracy_bar.setValue(int(accuracy))

        # Color coding
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
        feedback += f"Reference: {pron_data['reference']}\n\n"
        feedback += f"Recognized: {pron_data['recognized']}\n\n"
        feedback += "=== WORD-BY-WORD ANALYSIS ===\n\n"

        word_analysis = pron_data.get("word_analysis", [])
        correct_count = 0

        for i, word_info in enumerate(word_analysis, 1):
            status = word_info["status"]
            ref = word_info["reference"]
            rec = word_info["recognized"]
            sim = word_info["similarity"]

            if status == "correct":
                correct_count += 1
                feedback += f"{i}. ✓ '{ref}' → '{rec}' ({sim:.1f}%)\n"
            elif status == "incorrect":
                feedback += f"{i}. ✗ '{ref}' → '{rec}' ({sim:.1f}%) - Mispronounced\n"
            elif status == "missing":
                feedback += f"{i}. ✗ '{ref}' → [MISSING]\n"
            elif status == "extra":
                feedback += f"{i}. ⚠ [EXTRA] → '{rec}'\n"

        total = len(word_analysis)
        feedback += f"\n=== SUMMARY ===\n"
        feedback += f"Correct: {correct_count}/{total}\n"
        feedback += (
            f"Accuracy: {(correct_count / total * 100) if total > 0 else 0:.1f}%\n"
        )

        self.feedback_text.setText(feedback)
        self.tabs.setCurrentIndex(1)

    # ============== TTS Methods ==============

    def play_tts(self):
        """Play text-to-speech for reference text"""
        text = self.reference_text.text().strip()
        if not text:
            QMessageBox.warning(self, "No Text", "Please enter text.")
            return

        engine_name = self.config.get("tts_engine", "gTTS")
        voice = self.config.get("tts_voice") if engine_name == "edge-tts" else None
        lang_code = self.config["language"].split("-")[0].lower()

        # Normalize polytonic Greek for edge-tts if enabled
        if (
            self.config.get("normalize_tts", True)
            and engine_name == "edge-tts"
            and (
                lang_code.startswith("el")
                or (voice and "multilingual" in voice.lower())
            )
        ):
            from utils.text_processing import normalize_polytonic_greek

            text = normalize_polytonic_greek(text)

        try:
            self.tts_thread = TTSThread(text, engine_name, lang_code, voice=voice)
            self.tts_thread.start()
            self.status_text.append(
                f"[{self.get_current_time()}] Playing TTS: {text[:50]}..."
            )
        except Exception as e:
            QMessageBox.critical(self, "TTS Error", str(e))

    def play_slow_tts(self):
        """Play slow TTS for reference text"""
        text = self.reference_text.text().strip()
        if not text:
            QMessageBox.warning(self, "No Text", "Please enter text.")
            return

        engine_name = self.config.get("tts_engine", "gTTS")
        voice = self.config.get("tts_voice") if engine_name == "edge-tts" else None
        lang_code = self.config["language"].split("-")[0].lower()

        # Normalize polytonic Greek for edge-tts if enabled
        if (
            self.config.get("normalize_tts", True)
            and engine_name == "edge-tts"
            and (
                lang_code.startswith("el")
                or (voice and "multilingual" in voice.lower())
            )
        ):
            from utils.text_processing import normalize_polytonic_greek

            text = normalize_polytonic_greek(text)

        try:
            self.tts_thread = TTSThread(
                text, engine_name, lang_code, slow=True, voice=voice
            )
            self.tts_thread.start()
            self.status_text.append(
                f"[{self.get_current_time()}] Playing slow TTS: {text[:50]}..."
            )
        except Exception as e:
            QMessageBox.critical(self, "TTS Error", str(e))

    # ============== Flashcard Methods ==============

    def show_flashcard_mode(self):
        """Open flashcard mode dialog"""
        if not self.vocabulary_data:
            QMessageBox.warning(
                self, "No Vocabulary", "Please load a vocabulary file first."
            )
            return

        dialog = FlashcardDialog(
            self.vocabulary_data,
            self.config,
            self,
            vocab_file_path=self.vocab_file_path,
        )
        dialog.session_completed.connect(self.on_flashcard_session_completed)
        dialog.exec_()

    def on_flashcard_session_completed(self, stats):
        """Handle flashcard session completion"""
        self.status_text.append(
            f"[{self.get_current_time()}] Flashcard session completed!"
        )
        self.status_text.append(
            f"[{self.get_current_time()}] Accuracy: {stats['accuracy']:.1f}%"
        )

    def show_statistics(self):
        """Show learning statistics"""
        from ui.flashcards import FlashcardStatsDialog

        dialog = FlashcardStatsDialog(self.flashcard_progress, self)
        dialog.exec_()

    # ============== Utility Methods ==============

    def update_combined_pronunciation(self):
        """Update combined pronunciation display"""
        try:
            english_text = self.reference_text.text().strip()
            if not english_text:
                self.pronunciation_text.setPlainText(
                    "Enter text to see pronunciation..."
                )
                return

            ipa_text = text_to_ipa_modern(english_text)
            display_text = f"English: {english_text}\nIPA:     {ipa_text}"
            self.pronunciation_text.setPlainText(display_text)

        except Exception as e:
            self.status_text.append(
                f"[{self.get_current_time()}] Pronunciation error: {str(e)}"
            )

    def change_font_size(self, text_widget, delta):
        """Change font size for text widgets"""
        try:
            if isinstance(text_widget, QLineEdit):
                current_font = text_widget.font()
                current_size = current_font.pointSize()
                new_size = max(6, min(72, current_size + delta))
                current_font.setPointSize(new_size)
                text_widget.setFont(current_font)
            else:  # QTextEdit
                current_font = text_widget.currentFont()
                current_size = current_font.pointSize()
                new_size = max(6, min(72, current_size + delta))
                current_font.setPointSize(new_size)
                text_widget.selectAll()
                text_widget.setCurrentFont(current_font)
        except Exception as e:
            self.status_text.append(f"[{self.get_current_time()}] Font error: {str(e)}")

    def get_current_time(self):
        """Get current timestamp"""
        return datetime.now().strftime("%H:%M:%S")

    # ============== File Operations ==============

    def save_text(self):
        """Save ASR output text"""
        text = self.output_text.toPlainText()
        if not text:
            QMessageBox.warning(self, "No Text", "No text to save.")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Text", "", "Text Files (*.txt);;All Files (*)"
        )
        if filename:
            if save_text_to_file(text, filename):
                QMessageBox.information(self, "Success", "Text saved!")
            else:
                QMessageBox.critical(self, "Error", "Failed to save text")

    def save_report(self):
        """Save pronunciation training report"""
        if not self.pronunciation_data:
            QMessageBox.warning(self, "No Report", "No pronunciation report to save.")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Report",
            "",
            "Text Files (*.txt);;HTML Files (*.html);;All Files (*)",
        )
        if filename:
            report = generate_pronunciation_report(
                self.pronunciation_data,
                self.config,
                {"timestamp": datetime.now().isoformat()},
            )
            if save_text_to_file(report, filename):
                QMessageBox.information(self, "Success", "Report saved!")
            else:
                QMessageBox.critical(self, "Error", "Failed to save report")

    # ============== Dialog Methods ==============

    def show_config(self):
        """Show configuration dialog"""
        dialog = ConfigDialog(self, self.config)
        if dialog.exec_() == dialog.Accepted:
            self.config = dialog.get_config()
            QMessageBox.information(self, "Configuration", "Settings updated!")

    def show_help(self):
        """Show help dialog"""
        help_text = """ASR Application Help

1. Load Vocabulary: Click "Load Vocabulary" to import files
2. Navigate: Use Previous/Next buttons to browse vocabulary
3. Practice: Listen with TTS, then record your pronunciation
4. Check: Click "ASR Convert" to get feedback
5. Flashcards: Use the Flashcard Mode for spaced repetition learning

Supported formats: CSV, TXT, ZIP
Languages: Greek, English, Spanish, French, German, etc."""

        QMessageBox.information(self, "Help", help_text)

    def show_about(self):
        """Show about dialog"""
        about_text = """ASR Application v2.0
Pronunciation Training Edition

Features:
• Google Speech Recognition
• OpenAI Whisper
• Pronunciation accuracy scoring
• Flashcard mode with progress tracking
• Text-to-Speech
• Vocabulary management

Built with PyQt5 and Python"""

        QMessageBox.about(self, "About", about_text)

    def on_error(self, error_msg):
        """Handle errors"""
        QMessageBox.critical(self, "Error", error_msg)
        self.record_btn.setEnabled(True)
        self.convert_btn.setEnabled(True)
        self.output_text.setText(f"Error: {error_msg}")

    def closeEvent(self, event):
        """Handle application close"""
        # Save any pending data
        if hasattr(self, "flashcard_progress"):
            self.flashcard_progress.save()
        event.accept()
