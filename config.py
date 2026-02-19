"""
Configuration module for ASR Application
Contains ConfigDialog class and default settings
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QLineEdit, QPushButton, QGroupBox, QSpinBox, QGridLayout
)


# Default application settings
DEFAULT_CONFIG = {
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
        'grammar': 7
    },
    # TTS settings
    'tts_engine': 'gTTS',
    'tts_speed': 'normal',
    'tts_voice': 'default',
    # ASR engine settings
    'asr_engines': ['Google Speech Recognition', 'Whisper'],
    'asr_engine_settings': {
        'Google Speech Recognition': {
            'timeout': 10,
            'phrase_threshold': 0.3,
            'pause_threshold': 0.8
        },
        'Whisper': {
            'device': 'auto',  # 'cpu', 'cuda', 'auto'
            'fp16': False,
            'verbose': False
        }
    },
    # TTS engine settings
    'tts_engines': ['gTTS', 'pyttsx3', 'espeak'],
    'tts_engine_settings': {
        'gTTS': {
            'slow': False,
            'lang_check': True
        },
        'pyttsx3': {
            'rate': 150,
            'volume': 1.0
        },
        'espeak': {
            'speed': 150,
            'pitch': 50
        }
    },
    # Flashcard settings
    'flashcard': {
        'auto_advance': False,
        'auto_advance_delay': 3.0,
        'show_first': 'word',  # 'word', 'definition'
        'shuffle_cards': False,
        'repeat_incorrect': True
    }
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
        self.engine_combo.addItems(DEFAULT_CONFIG['asr_engines'])
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

        # TTS Engine selection
        tts_group = QGroupBox("TTS Engine (Planned Feature)")
        tts_layout = QVBoxLayout()

        self.tts_engine_label = QLabel("Select TTS Engine:")
        self.tts_engine_combo = QComboBox()
        self.tts_engine_combo.addItems(DEFAULT_CONFIG['tts_engines'])
        self.tts_engine_combo.setEnabled(False)  # Placeholder for future implementation
        self.tts_engine_combo.setToolTip("TTS engine selection - coming in a future update")

        tts_layout.addWidget(self.tts_engine_label)
        tts_layout.addWidget(self.tts_engine_combo)
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

    def on_engine_changed(self):
        self.update_model_options()

    def update_model_options(self):
        self.model_combo.clear()
        if self.engine_combo.currentText() == "Google Speech Recognition":
            self.model_combo.addItems([
                "Default",
                "Command and Search",
                "Dictation",
                "latest_short",
                "latest_long",
                "chirp_3",
                "telephony"
            ])
        else:  # Whisper
            self.model_combo.addItems([
                'tiny.en', 'tiny', 'base.en', 'base', 'small.en',
                'small', 'medium.en', 'medium', 'large-v1',
                'large-v2', 'large-v3', 'large'
            ])
            self.model_combo.setCurrentText("base")

    def get_config(self):
        """Get the current configuration as a dictionary"""
        config = {
            'engine': self.engine_combo.currentText(),
            'language': self.languages[self.lang_combo.currentText()],
            'language_name': self.lang_combo.currentText(),
            'model': self.model_combo.currentText(),
            'sample_rate': int(self.rate_entry.text()),
            'energy_threshold': int(self.energy_entry.text()),
            'pronunciation_threshold': self.pron_spin.value(),
            'vocab_delimiter': self.delim_combo.currentText(),
            'vocab_columns': {
                'reference': self.ref_col_spin.value(),
                'definition': self.def_col_spin.value(),
                'english_pronunciation': self.eng_pron_col_spin.value(),
                'ipa_pronunciation': self.ipa_col_spin.value(),
                'image_description': self.img_desc_col_spin.value(),
                'image_filename': self.img_file_col_spin.value(),
                'grammar': self.grammar_col_spin.value()
            },
            'tts_engine': self.tts_engine_combo.currentText(),
            # Include default settings for new features
            'asr_engines': DEFAULT_CONFIG['asr_engines'],
            'tts_engines': DEFAULT_CONFIG['tts_engines'],
            'flashcard': DEFAULT_CONFIG['flashcard']
        }
        return config
