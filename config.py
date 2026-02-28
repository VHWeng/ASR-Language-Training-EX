"""
Configuration module for ASR Application
Contains ConfigDialog class and default settings
"""

from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QLineEdit,
    QPushButton,
    QGroupBox,
    QSpinBox,
    QGridLayout,
    QTextEdit,
)


# Default application settings
DEFAULT_CONFIG = {
    "engine": "Google Speech Recognition",
    "language": "el-GR",
    "language_name": "Greek",
    "model": "latest_short",
    "sample_rate": 16000,
    "energy_threshold": 300,
    "pronunciation_threshold": 80,
    "vocab_delimiter": "|",
    "vocab_columns": {
        "reference": 1,
        "definition": 2,
        "english_pronunciation": 3,
        "ipa_pronunciation": 4,
        "image_description": 5,
        "image_filename": 6,
        "grammar": 7,
    },
    # TTS settings
    "tts_engine": "gTTS",
    "tts_speed": "normal",
    "tts_voice": "en-US-BrianMultilingualNeural",
    # ASR engine settings
    "asr_engines": ["Google Speech Recognition", "Whisper", "Qwen3-ASR"],
    "asr_engine_settings": {
        "Google Speech Recognition": {
            "timeout": 10,
            "phrase_threshold": 0.3,
            "pause_threshold": 0.8,
        },
        "Whisper": {
            "device": "auto",  # 'cpu', 'cuda', 'auto'
            "fp16": False,
            "verbose": False,
        },
        "Qwen3-ASR": {
            "device": "auto",  # Auto-detect GPU/CPU, 'cpu', 'cuda'
            "sample_rate": 16000,
            "model": "Qwen3-ASR-1.7B",  # Default model
        },
    },
    # TTS engine settings
    "tts_engines": ["gTTS", "edge-tts"],
    "tts_engine_settings": {
        "gTTS": {"slow": False, "lang_check": True},
        "pyttsx3": {"rate": 150, "volume": 1.0},
        "espeak": {"speed": 150, "pitch": 50},
    },
    # Flashcard settings
    "flashcard": {
        "auto_advance": False,
        "auto_advance_delay": 3.0,
        "show_first": "word",  # 'word', 'definition'
        "shuffle_cards": False,
        "repeat_incorrect": True,
    },
}


class ConfigDialog(QDialog):
    """Configuration dialog for ASR Application settings"""

    def __init__(self, parent=None, current_config=None):
        super().__init__(parent)
        self.current_config = current_config or DEFAULT_CONFIG.copy()
        self.setWindowTitle("Configuration")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Engine selection
        engine_group = QGroupBox("ASR Engine")
        engine_layout = QVBoxLayout()

        self.engine_label = QLabel("Select Engine:")
        self.engine_combo = QComboBox()
        self.engine_combo.addItems(DEFAULT_CONFIG["asr_engines"])
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
            "Arabic": "ar-SA",
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

        # Device selection for Qwen3-ASR
        device_layout = QHBoxLayout()
        self.device_label = QLabel("Device:")
        self.device_combo = QComboBox()
        self.device_combo.addItems(["auto", "cpu", "cuda"])
        self.device_combo.setToolTip("Select processing device (auto-detects GPU/CPU)")
        device_layout.addWidget(self.device_label)
        device_layout.addWidget(self.device_combo)
        settings_layout.addLayout(device_layout)

        # Test connection button
        test_layout = QHBoxLayout()
        self.test_btn = QPushButton("Test Connection")
        self.test_btn.clicked.connect(self.test_asr_connection)
        self.test_btn.setToolTip("Test ASR engine connection")
        self.test_status = QLabel("")
        self.test_status.setStyleSheet("color: gray;")
        test_layout.addWidget(self.test_btn)
        test_layout.addWidget(self.test_status)
        settings_layout.addLayout(test_layout)

        # Test result feedback
        self.test_feedback = QLabel("")
        self.test_feedback.setWordWrap(True)
        self.test_feedback.setStyleSheet("color: gray;")
        settings_layout.addWidget(self.test_feedback)

        # New: Status text box for detailed info
        self.status_log = QTextEdit()
        self.status_log.setReadOnly(True)
        self.status_log.setFixedHeight(100)  # Give it a fixed height
        self.status_log.setPlaceholderText(
            "Connection test status and model info will appear here..."
        )
        settings_layout.addWidget(self.status_log)

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

        # TTS Engine selection
        tts_group = QGroupBox("Text-to-Speech (TTS)")
        tts_layout = QVBoxLayout()

        self.tts_engine_label = QLabel("Select TTS Engine:")
        self.tts_engine_combo = QComboBox()
        self.tts_engine_combo.addItems(DEFAULT_CONFIG["tts_engines"])
        self.tts_engine_combo.currentIndexChanged.connect(self.on_tts_engine_changed)
        self.tts_engine_combo.setToolTip("Select TTS engine for pronunciation playback")
        # Initialize to the configured engine
        current_engine = self.current_config.get(
            "tts_engine", DEFAULT_CONFIG.get("tts_engine", "gTTS")
        )
        index = self.tts_engine_combo.findText(current_engine)
        if index >= 0:
            self.tts_engine_combo.setCurrentIndex(index)

        tts_layout.addWidget(self.tts_engine_label)
        tts_layout.addWidget(self.tts_engine_combo)

        # Voice selection (for edge-tts)
        self.voice_label = QLabel("Voice (edge-tts only):")
        self.voice_combo = QComboBox()
        self.voice_combo.setEnabled(False)
        self.voice_combo.setToolTip(
            "Select voice for edge-tts (only applicable when edge-tts engine is selected)"
        )

        tts_layout.addWidget(self.voice_label)
        tts_layout.addWidget(self.voice_combo)

        # Info label about voice selection
        self.tts_info_label = QLabel(
            "Note: gTTS uses language setting only. edge-tts offers specific voices."
        )
        self.tts_info_label.setStyleSheet("color: gray; font-size: 10px;")
        tts_layout.addWidget(self.tts_info_label)

        tts_group.setLayout(tts_layout)
        layout.addWidget(tts_group)

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
        self.grammar_col_spin.setValue(7)
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
        self.on_tts_engine_changed()

    def on_engine_changed(self):
        self.update_model_options()
        self.update_device_visibility()

    def update_device_visibility(self):
        """Show/hide device selection based on engine"""
        engine = self.engine_combo.currentText()
        if engine == "Qwen3-ASR":
            self.device_label.show()
            self.device_combo.show()
            self.device_combo.setCurrentText("auto")
        else:
            self.device_label.hide()
            self.device_combo.hide()

    def update_model_options(self):
        self.model_combo.clear()
        engine = self.engine_combo.currentText()
        if engine == "Google Speech Recognition":
            # Note: Free Google Speech API doesn't support model selection
            # These options are for reference only - the API uses its default model
            self.model_combo.addItems(
                [
                    "Default",
                ]
            )
        elif engine == "Whisper":
            self.model_combo.addItems(
                [
                    "tiny.en",
                    "tiny",
                    "base.en",
                    "base",
                    "small.en",
                    "small",
                    "medium.en",
                    "medium",
                    "large-v1",
                    "large-v2",
                    "large-v3",
                    "large",
                ]
            )
        elif engine == "Qwen3-ASR":
            self.model_combo.addItems(["Qwen3-ASR-1.7B", "Qwen3-ASR-0.6B"])
            self.model_combo.setCurrentText("Qwen3-ASR-1.7B")

    def on_tts_engine_changed(self):
        """Handle TTS engine selection change"""
        engine = self.tts_engine_combo.currentText()
        print(
            f"[DEBUG] on_tts_engine_changed: engine={engine}, voice_combo.count={self.voice_combo.count()}"
        )
        if engine == "edge-tts":
            self.voice_label.show()
            self.voice_combo.show()
            self.voice_combo.setEnabled(True)
            if self.voice_combo.count() == 0:
                print("[DEBUG] Calling load_edge_tts_voices")
                self.load_edge_tts_voices()
            else:
                print("[DEBUG] Voice combo already has items, skipping load")
        else:
            self.voice_label.hide()
            self.voice_combo.hide()
            self.voice_combo.setEnabled(False)

    def load_edge_tts_voices(self):
        """Load available edge-tts voices in background thread"""
        import threading
        import asyncio

        # Show loading state immediately (called from main thread — safe)
        self.voice_combo.clear()
        self.voice_combo.addItem("Loading voices...", None)
        self.voice_combo.setEnabled(False)
        print("[DEBUG] load_edge_tts_voices: starting background fetch thread")

        def fetch_voices():
            print("[DEBUG] fetch_voices thread started")
            voices_data = []
            try:
                import edge_tts

                print("[DEBUG] edge_tts imported successfully")
                # asyncio.run() creates a brand-new event loop — safe in a plain thread
                voices = asyncio.run(edge_tts.list_voices())
                print(f"[DEBUG] asyncio.run(list_voices()) returned {len(voices)} voices")

                if not voices:
                    print("[DEBUG] WARNING: voice list is empty!")

                # Sort and format
                voices.sort(key=lambda v: (v.get("Locale", ""), v.get("ShortName", "")))
                for voice in voices:
                    display = (
                        f"{voice.get('ShortName', 'Unknown')} "
                        f"({voice.get('Locale', 'Unknown')}) - "
                        f"{voice.get('Gender', 'Unknown')}"
                    )
                    voices_data.append((display, voice.get("ShortName")))

                print(f"[DEBUG] Prepared {len(voices_data)} voice entries for UI")

            except ImportError as e:
                print(f"[DEBUG] ImportError — edge_tts not installed? {e}")
                voices_data = [(f"edge-tts not installed: {e}", None)]
            except Exception as e:
                print(f"[DEBUG] Exception fetching voices: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                voices_data = [(f"Error loading voices: {e}", None)]

            # ---------------------------------------------------------------
            # CRITICAL FIX: QTimer.singleShot must be called from the main
            # (GUI) thread.  Calling it from a worker thread means the timer
            # is owned by that thread and fires there — but Qt widgets can
            # only be touched from the main thread, so the callback is either
            # silently dropped or causes a crash/hang.
            #
            # Fix: use a custom Qt signal emitted from the worker thread so
            # Qt's cross-thread queued connection delivers the call safely on
            # the main thread.  If signals aren't available we fall back to
            # QMetaObject.invokeMethod with a Qt.QueuedConnection.
            # ---------------------------------------------------------------
            def update_ui():
                print("[DEBUG] update_ui running on main thread — updating voice_combo")
                self.voice_combo.clear()
                for display, data in voices_data:
                    self.voice_combo.addItem(display, data)
                print(f"[DEBUG] voice_combo now has {self.voice_combo.count()} items")

                # Set default voice
                default_voice = self.current_config.get(
                    "tts_voice", DEFAULT_CONFIG["tts_voice"]
                )
                print(f"[DEBUG] Looking for default voice: '{default_voice}'")
                idx = self.voice_combo.findData(default_voice)
                if idx >= 0:
                    self.voice_combo.setCurrentIndex(idx)
                    print(f"[DEBUG] Default voice set at index {idx}")
                else:
                    print(
                        f"[DEBUG] Default voice '{default_voice}' not found — "
                        "selecting index 0"
                    )
                    if self.voice_combo.count() > 0:
                        self.voice_combo.setCurrentIndex(0)

                # Enable the combo only when we have real entries
                has_valid = len(voices_data) > 0 and voices_data[0][1] is not None
                self.voice_combo.setEnabled(has_valid)
                print(f"[DEBUG] voice_combo enabled={has_valid}")

            # Use QMetaObject.invokeMethod to guarantee execution on the
            # main/GUI thread via a queued connection — this is safe to call
            # from any thread.
            from PyQt5.QtCore import QMetaObject, Qt
            import PyQt5.QtCore as QtCore

            # Wrap update_ui in a zero-argument slot via a lambda stored on a
            # temporary QObject so invokeMethod can dispatch it.
            # Simplest cross-thread approach: use a thread-safe signal bridge.
            print("[DEBUG] Dispatching update_ui to main thread via _VoiceBridge")
            self._voice_bridge.voices_ready.emit(voices_data)

        # Create a lightweight signal bridge so the worker thread can safely
        # post the result back to the main thread.
        from PyQt5.QtCore import QObject, pyqtSignal

        class _VoiceBridge(QObject):
            # Signal carries the list of (display, shortname) tuples
            voices_ready = pyqtSignal(list)

        bridge = _VoiceBridge(self)  # parent=self keeps it alive

        def _on_voices_ready(voices_data):
            print("[DEBUG] _on_voices_ready signal received on main thread")
            self.voice_combo.clear()
            for display, data in voices_data:
                self.voice_combo.addItem(display, data)
            print(f"[DEBUG] voice_combo now has {self.voice_combo.count()} items")

            default_voice = self.current_config.get(
                "tts_voice", DEFAULT_CONFIG["tts_voice"]
            )
            print(f"[DEBUG] Looking for default voice: '{default_voice}'")
            idx = self.voice_combo.findData(default_voice)
            if idx >= 0:
                self.voice_combo.setCurrentIndex(idx)
                print(f"[DEBUG] Default voice set at index {idx}")
            else:
                print(
                    f"[DEBUG] Default voice '{default_voice}' not found — selecting index 0"
                )
                if self.voice_combo.count() > 0:
                    self.voice_combo.setCurrentIndex(0)

            has_valid = len(voices_data) > 0 and voices_data[0][1] is not None
            self.voice_combo.setEnabled(has_valid)
            print(f"[DEBUG] voice_combo enabled={has_valid}")

        # Qt automatically makes this a QueuedConnection because the signal
        # is emitted from a different thread — so _on_voices_ready always
        # runs on the main thread. No manual thread-safety needed.
        bridge.voices_ready.connect(_on_voices_ready)
        self._voice_bridge = bridge  # keep reference alive

        threading.Thread(target=fetch_voices, daemon=True).start()
        print("[DEBUG] Background thread started, returning control to event loop")

    def test_asr_connection(self):
        """Test ASR engine connection and display feedback"""
        from core.asr_engines import ASRThread
        import tempfile
        import numpy as np
        import soundfile as sf
        import os  # Import os for file cleanup

        engine = self.engine_combo.currentText()
        device = self.device_combo.currentText()
        model = self.model_combo.currentText()  # Get selected model

        self.test_btn.setEnabled(False)
        self.test_status.setText("⏳ Testing...")
        self.status_log.clear()  # Clear previous logs
        self.status_log.append(f"Attempting to test ASR engine: {engine}")
        self.status_log.append(f"Selected model: {model}")
        if engine == "Qwen3-ASR":
            self.status_log.append(f"Selected device: {device}")

        temp_audio_file = None
        try:
            self.status_log.append("Generating a temporary audio file for testing...")
            # Create temporary audio file for testing
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_audio_file = temp_file.name
                # Generate 1 second of 1000 Hz tone for testing
                sample_rate = 16000
                duration = 1.0
                t = np.linspace(0, duration, int(sample_rate * duration), False)
                frequency = 1000
                data = np.sin(2 * np.pi * frequency * t)
                data = (data * 32767).astype(np.int16)

                sf.write(temp_audio_file, data, sample_rate)
            self.status_log.append(f"Temporary audio file created: {temp_audio_file}")

            # Create test config
            test_config = {
                "engine": engine,
                "device": device,
                "sample_rate": 16000,
                "model": model,  # Use the selected model
                "language": self.languages[self.lang_combo.currentText()],
                "energy_threshold": 300,
            }
            self.status_log.append(f"Test configuration: {test_config}")

            self.status_log.append("Starting ASR thread for connection test...")
            # Create and run ASR thread
            asr_thread = ASRThread(
                temp_audio_file,
                test_config,
                show_punctuation=False,
                show_word_time=False,
            )

            asr_thread.start()
            asr_thread.wait()  # Wait for the thread to finish

            if asr_thread.error_occurred:
                raise Exception(asr_thread.error_message)

            self.test_status.setText("✅ Connected")
            self.test_status.setStyleSheet("color: green;")
            self.test_feedback.setText("✅ ASR engine connection successful!")
            self.status_log.append("✅ Connection test completed successfully!")

        except Exception as e:
            self.test_status.setText("❌ Failed")
            self.test_status.setStyleSheet("color: red;")
            self.test_feedback.setText(f"❌ Connection failed: {str(e)}")
            self.status_log.append(f"❌ Connection test failed: {str(e)}")

        finally:
            self.test_btn.setEnabled(True)
            self.test_feedback.show()
            # Clean up the temporary audio file
            if temp_audio_file and os.path.exists(temp_audio_file):
                os.remove(temp_audio_file)
                self.status_log.append(
                    f"Cleaned up temporary audio file: {temp_audio_file}"
                )

    def get_config(self):
        """Get the current configuration as a dictionary"""
        config = {
            "engine": self.engine_combo.currentText(),
            "language": self.languages[self.lang_combo.currentText()],
            "language_name": self.lang_combo.currentText(),
            "model": self.model_combo.currentText(),
            "sample_rate": int(self.rate_entry.text()),
            "energy_threshold": int(self.energy_entry.text()),
            "pronunciation_threshold": self.pron_spin.value(),
            "vocab_delimiter": self.delim_combo.currentText(),
            "vocab_columns": {
                "reference": self.ref_col_spin.value(),
                "definition": self.def_col_spin.value(),
                "english_pronunciation": self.eng_pron_col_spin.value(),
                "ipa_pronunciation": self.ipa_col_spin.value(),
                "image_description": self.img_desc_col_spin.value(),
                "image_filename": self.img_file_col_spin.value(),
                "grammar": self.grammar_col_spin.value(),
            },
            "tts_engine": self.tts_engine_combo.currentText(),
            "tts_voice": self.voice_combo.currentData()
            if self.voice_combo.currentData()
            else DEFAULT_CONFIG["tts_voice"],
            # Include default settings for new features
            "asr_engines": DEFAULT_CONFIG["asr_engines"],
            "tts_engines": DEFAULT_CONFIG["tts_engines"],
            "flashcard": DEFAULT_CONFIG["flashcard"],
        }
        return config