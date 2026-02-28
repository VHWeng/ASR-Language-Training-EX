"""
Flashcard Mode module for ASR Application
Provides spaced repetition learning with progress tracking
"""

import json
import os
import random
from datetime import datetime, timedelta
from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QProgressBar,
    QCheckBox,
    QSpinBox,
    QGroupBox,
    QMessageBox,
    QDialog,
    QDialogButtonBox,
    QComboBox,
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPixmap

# Import TTS engines
from core.tts_engines import TTSThread

# Import recording functionality
from core.recorder import RecordThread
import sounddevice as sd
import soundfile as sf


class FlashcardSession:
    """Represents a single flashcard learning session"""

    def __init__(self, vocab_data):
        self.vocab_data = vocab_data
        self.current_index = 0
        self.correct_count = 0
        self.incorrect_count = 0
        self.start_time = datetime.now()
        self.session_log = []

    def record_attempt(self, vocab_item, was_correct, accuracy_score):
        """Record an attempt on a flashcard"""
        self.session_log.append(
            {
                "timestamp": datetime.now().isoformat(),
                "vocab_item": vocab_item,
                "correct": was_correct,
                "accuracy": accuracy_score,
            }
        )
        if was_correct:
            self.correct_count += 1
        else:
            self.incorrect_count += 1

    def get_statistics(self):
        """Get session statistics"""
        total = self.correct_count + self.incorrect_count
        if total == 0:
            return {"accuracy": 0, "total": 0}
        return {
            "accuracy": (self.correct_count / total) * 100,
            "total": total,
            "correct": self.correct_count,
            "incorrect": self.incorrect_count,
            "duration_seconds": (datetime.now() - self.start_time).total_seconds(),
        }


class FlashcardProgress:
    """
    Manages user progress for flashcard learning
    Implements spaced repetition algorithm
    """

    def __init__(self, storage_path="Data/flashcard_progress.json"):
        self.storage_path = storage_path
        self.items = {}  # {item_id: progress_data}
        self.load()

    def load(self):
        """Load progress from storage"""
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.items = data.get("items", {})
        except FileNotFoundError:
            self.items = {}

    def save(self):
        """Save progress to storage"""
        data = {"last_saved": datetime.now().isoformat(), "items": self.items}
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def update_item(self, item_id, was_correct, accuracy_score):
        """Update progress for an item"""
        if item_id not in self.items:
            self.items[item_id] = {
                "created": datetime.now().isoformat(),
                "attempts": 0,
                "correct_count": 0,
                "total_accuracy": 0,
                "last_reviewed": None,
                "next_review": datetime.now().isoformat(),
                "difficulty_level": 1,  # 1-5
                "streak": 0,
            }

        item = self.items[item_id]
        item["attempts"] += 1
        item["last_reviewed"] = datetime.now().isoformat()
        item["total_accuracy"] += accuracy_score

        if was_correct:
            item["correct_count"] += 1
            item["streak"] += 1
            item["difficulty_level"] = min(5, item["difficulty_level"] + 1)
        else:
            item["streak"] = 0
            item["difficulty_level"] = max(1, item["difficulty_level"] - 1)

        # Calculate next review (spaced repetition)
        days_until_review = self._calculate_review_interval(item)
        item["next_review"] = (
            datetime.now() + timedelta(days=days_until_review)
        ).isoformat()

    def _calculate_review_interval(self, item):
        """Calculate days until next review based on performance"""
        streak = item["streak"]
        difficulty = item["difficulty_level"]

        # Base intervals in days
        intervals = [1, 3, 7, 14, 30]

        # Adjust based on streak and difficulty
        base_index = min(streak, len(intervals) - 1)
        interval = intervals[base_index]

        # Reduce interval for difficult items
        if difficulty <= 2:
            interval = max(1, interval // 2)

        return interval

    def get_due_items(self, vocab_list):
        """Get items that are due for review"""
        now = datetime.now().isoformat()
        due = []
        for item in vocab_list:
            item_id = item.get("reference", str(item))
            if item_id in self.items:
                if self.items[item_id]["next_review"] <= now:
                    due.append(item)
            else:
                due.append(item)  # New items are always due
        return due

    def get_statistics(self):
        """Get overall learning statistics"""
        if not self.items:
            return {
                "total_items": 0,
                "mastered": 0,
                "learning": 0,
                "average_accuracy": 0,
            }

        total = len(self.items)
        mastered = sum(
            1 for item in self.items.values() if item["difficulty_level"] >= 4
        )
        avg_accuracy = (
            sum(
                item["total_accuracy"] / item["attempts"]
                for item in self.items.values()
                if item["attempts"] > 0
            )
            / total
        )

        return {
            "total_items": total,
            "mastered": mastered,
            "learning": total - mastered,
            "average_accuracy": avg_accuracy,
        }


class FlashcardDialog(QDialog):
    """
    Flashcard Mode dialog
    Interactive learning mode with pronunciation practice
    """

    session_completed = pyqtSignal(dict)

    def __init__(self, vocab_data, config, parent=None, vocab_file_path=None):
        super().__init__(parent)
        self.vocab_data = vocab_data
        self.config = config
        self.vocab_file_path = vocab_file_path
        self.progress = FlashcardProgress(storage_path="Data/flashcard_progress.json")
        self.session = None
        self.current_card = None
        self.showing_front = True  # True = word, False = definition

        # Cache for default logo image
        self.default_logo_pixmap = None

        # Initialize TTS engine
        from core.tts_engines import gTTSEngine, TTSThread

        self.tts_engine = gTTSEngine()
        self.tts_thread = None

        # Initialize recording attributes
        self.record_thread = None
        self.recorded_file = None
        self.audio_file = None

        # Initialize ASR attributes for pronunciation feedback
        from core.asr_engines import ASRThread

        self.asr_thread = None
        self.pronunciation_data = None
        self.has_pronunciation_feedback = False

        # Back card TTS buttons
        self.back_play_tts_btn = None
        self.back_play_slow_tts_btn = None

        self.setWindowTitle("Flashcard Mode")
        self.setMinimumSize(600, 500)
        self.init_ui()
        self.start_session()

    def init_ui(self):
        layout = QVBoxLayout()

        # Session stats bar
        stats_bar_layout = QHBoxLayout()

        self.progress_label = QLabel("Card: 0/0")
        self.accuracy_label = QLabel("Accuracy: 0%")
        self.streak_label = QLabel("Streak: 0")

        stats_bar_layout.addWidget(self.progress_label)
        stats_bar_layout.addWidget(self.accuracy_label)
        stats_bar_layout.addWidget(self.streak_label)
        stats_bar_layout.addStretch()

        layout.addLayout(stats_bar_layout)

        # Front Card Layout
        self.front_card_group = QWidget()
        front_card_layout = QVBoxLayout()
        front_card_layout.setContentsMargins(10, 10, 10, 10)

        # Top right controls for front card
        front_top_layout = QHBoxLayout()

        self.enable_image_cb = QCheckBox("Enable Image")
        self.enable_image_cb.setChecked(True)
        # self.enable_image_cb.toggled.connect(self.toggle_image_display) # Removed old connection
        front_top_layout.addWidget(self.enable_image_cb)

        front_top_layout.addStretch()
        self.front_config_btn = QPushButton("⚙️")
        self.front_config_btn.setFixedSize(30, 30)
        self.front_config_btn.setToolTip("Configuration")
        self.front_config_btn.clicked.connect(self.show_settings)
        front_top_layout.addWidget(self.front_config_btn)

        self.front_stats_btn = QPushButton("📊")
        self.front_stats_btn.setFixedSize(30, 30)
        self.front_stats_btn.setToolTip("Statistics")
        self.front_stats_btn.clicked.connect(self.show_statistics)
        front_top_layout.addWidget(self.front_stats_btn)

        self.front_help_btn = QPushButton("?")
        self.front_help_btn.setFixedSize(30, 30)
        self.front_help_btn.setToolTip("Help")
        self.front_help_btn.clicked.connect(self.show_help)
        front_top_layout.addWidget(self.front_help_btn)

        front_card_layout.addLayout(front_top_layout)

        # Top Center: Word/Phrase
        self.front_word_label = QLabel("Word/Phrase")
        self.front_word_label.setAlignment(Qt.AlignCenter)
        self.front_word_label.setFont(QFont("Arial", 24, QFont.Bold))
        front_card_layout.addWidget(self.front_word_label)

        # Under Word/Phrase: TTS buttons
        tts_layout = QHBoxLayout()

        self.play_tts_btn = QPushButton("🔊 Play")
        self.play_tts_btn.clicked.connect(self.play_tts)
        tts_layout.addWidget(self.play_tts_btn)

        self.play_slow_tts_btn = QPushButton("🐛 Slow")
        self.play_slow_tts_btn.clicked.connect(self.play_slow_tts)
        tts_layout.addWidget(self.play_slow_tts_btn)

        front_card_layout.addLayout(tts_layout)

        # Under TTS: Pronunciation toggle and display
        pron_layout = QHBoxLayout()

        self.show_pronunciation_cb = QCheckBox("Show Pronunciation")
        self.show_pronunciation_cb.stateChanged.connect(self.toggle_pronunciation)
        pron_layout.addWidget(self.show_pronunciation_cb)

        self.pronunciation_label = QLabel()
        self.pronunciation_label.setAlignment(Qt.AlignCenter)
        self.pronunciation_label.setFont(QFont("Arial", 14))
        self.pronunciation_label.hide()
        pron_layout.addWidget(self.pronunciation_label)

        front_card_layout.addLayout(pron_layout)

        # Center: Image display
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setScaledContents(False)  # Important for manual scaling
        self.image_label.setMinimumSize(200, 200)
        self.image_label.setText("Image disabled")
        self.image_label.setStyleSheet(
            "border: 1px solid gray; background-color: #f0f0f0;"
        )
        front_card_layout.addWidget(self.image_label)

        # Under Image: Recording controls
        record_layout = QHBoxLayout()

        self.record_btn = QPushButton("🎤 Record")
        self.record_btn.setStyleSheet("background-color: #ff4444;")
        self.record_btn.setCheckable(True)
        self.record_btn.clicked.connect(self.toggle_recording)
        record_layout.addWidget(self.record_btn)

        self.playback_btn = QPushButton("▶ Playback")
        self.playback_btn.clicked.connect(self.play_user_recording)
        self.playback_btn.setEnabled(False)
        record_layout.addWidget(self.playback_btn)

        front_card_layout.addLayout(record_layout)

        # Bottom Center: Navigation
        nav_layout = QHBoxLayout()

        self.prev_btn = QPushButton("◀ Previous")
        self.prev_btn.setStyleSheet(
            "background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;"
        )
        self.prev_btn.clicked.connect(self.previous_card)
        nav_layout.addWidget(self.prev_btn)

        self.flip_btn = QPushButton("Show ▶")
        self.flip_btn.setStyleSheet(
            "background-color: #2196F3; color: white; font-weight: bold; padding: 10px;"
        )
        self.flip_btn.setShortcut("Space")
        self.flip_btn.clicked.connect(self.flip_card)
        nav_layout.addWidget(self.flip_btn)

        nav_layout.addStretch()
        front_card_layout.addLayout(nav_layout)

        self.front_card_group.setLayout(front_card_layout)
        layout.addWidget(self.front_card_group)

        # Spacer
        layout.addSpacing(10)

        # Back Card Layout (hidden initially)
        self.back_card_group = QWidget()
        back_card_layout = QVBoxLayout()
        back_card_layout.setContentsMargins(10, 10, 10, 10)

        # Top right controls for back card
        back_top_layout = QHBoxLayout()
        back_top_layout.addStretch()
        self.back_config_btn = QPushButton("⚙️")
        self.back_config_btn.setFixedSize(30, 30)
        self.back_config_btn.setToolTip("Configuration")
        self.back_config_btn.clicked.connect(self.show_settings)
        back_top_layout.addWidget(self.back_config_btn)

        self.back_stats_btn = QPushButton("📊")
        self.back_stats_btn.setFixedSize(30, 30)
        self.back_stats_btn.setToolTip("Statistics")
        self.back_stats_btn.clicked.connect(self.show_statistics)
        back_top_layout.addWidget(self.back_stats_btn)

        self.back_help_btn = QPushButton("?")
        self.back_help_btn.setFixedSize(30, 30)
        self.back_help_btn.setToolTip("Help")
        self.back_help_btn.clicked.connect(self.show_help)
        back_top_layout.addWidget(self.back_help_btn)

        back_card_layout.addLayout(back_top_layout)

        # Top Center: Word/Phrase (same as front)
        self.back_word_label = QLabel("Word/Phrase")
        self.back_word_label.setAlignment(Qt.AlignCenter)
        self.back_word_label.setFont(QFont("Arial", 24, QFont.Bold))
        back_card_layout.addWidget(self.back_word_label)

        # Under Word/Phrase: Pronunciation (always visible)
        self.back_pronunciation_label = QLabel()
        self.back_pronunciation_label.setAlignment(Qt.AlignCenter)
        self.back_pronunciation_label.setFont(QFont("Arial", 14))
        back_card_layout.addWidget(self.back_pronunciation_label)

        # Under Pronunciation: TTS buttons (on back card)
        back_tts_layout = QHBoxLayout()

        self.back_play_tts_btn = QPushButton("🔊 Play")
        self.back_play_tts_btn.clicked.connect(self.play_tts)
        back_tts_layout.addWidget(self.back_play_tts_btn)

        self.back_play_slow_tts_btn = QPushButton("🐛 Slow")
        self.back_play_slow_tts_btn.clicked.connect(self.play_slow_tts)
        back_tts_layout.addWidget(self.back_play_slow_tts_btn)

        back_card_layout.addLayout(back_tts_layout)

        # Under Pronunciation: Definition/Translation
        self.definition_text = QTextEdit()
        self.definition_text.setReadOnly(True)
        self.definition_text.setAlignment(Qt.AlignCenter)
        self.definition_text.setFont(QFont("Arial", 16))
        self.definition_text.setMinimumSize(300, 100)
        back_card_layout.addWidget(self.definition_text)

        # Under Definition: Pronunciation Feedback
        feedback_layout = QHBoxLayout()

        self.feedback_label = QLabel("Pronunciation: ")
        feedback_layout.addWidget(self.feedback_label)

        self.feedback_progress = QProgressBar()
        self.feedback_progress.setMinimum(0)
        self.feedback_progress.setMaximum(100)
        self.feedback_progress.setValue(0)
        feedback_layout.addWidget(self.feedback_progress)

        back_card_layout.addLayout(feedback_layout)

        # Detailed pronunciation feedback text box
        self.pronunciation_feedback_text = QTextEdit()
        self.pronunciation_feedback_text.setReadOnly(True)
        self.pronunciation_feedback_text.setMinimumHeight(150)
        self.pronunciation_feedback_text.setMaximumHeight(200)
        self.pronunciation_feedback_text.setFont(QFont("Consolas", 10))
        back_card_layout.addWidget(self.pronunciation_feedback_text)
        self.pronunciation_feedback_text.hide()  # Initially hidden until feedback is available

        # Bottom: Rating buttons
        rating_layout = QHBoxLayout()

        self.unknown_btn = QPushButton("Unknown")
        self.unknown_btn.setStyleSheet(
            "background-color: #f44336; color: white; font-weight: bold; padding: 10px;"
        )
        self.unknown_btn.clicked.connect(lambda: self.rate_difficulty(1))
        rating_layout.addWidget(self.unknown_btn)

        self.partial_btn = QPushButton("Partially Known")
        self.partial_btn.setStyleSheet(
            "background-color: #FFC107; color: black; font-weight: bold; padding: 10px;"
        )
        self.partial_btn.clicked.connect(lambda: self.rate_difficulty(2))
        rating_layout.addWidget(self.partial_btn)

        self.know_btn = QPushButton("Know")
        self.know_btn.setStyleSheet(
            "background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;"
        )
        self.know_btn.clicked.connect(lambda: self.rate_difficulty(3))
        rating_layout.addWidget(self.know_btn)

        back_card_layout.addLayout(rating_layout)

        self.back_card_group.setLayout(back_card_layout)
        self.back_card_group.hide()
        layout.addWidget(self.back_card_group)

        # Close button
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.close)
        layout.addWidget(button_box)

        self.setLayout(layout)

        # Settings dialog (created on demand)
        self.settings_dialog = None

        # Session settings (defaults)
        self.shuffle_cards = True

    def start_session(self):
        """Initialize a new flashcard session"""
        vocab = self.vocab_data.copy()
        if self.shuffle_cards:
            random.shuffle(vocab)

        self.session = FlashcardSession(vocab)
        self.current_card = 0
        self.show_card()
        self.update_stats()

    def reset_session(self):
        """Reset the current session with new settings"""
        self.start_session()

    def show_card(self):
        """Display the current card"""
        if not self.vocab_data or self.current_card >= len(self.vocab_data):
            self.front_word_label.setText("Session Complete!")
            self.front_card_group.hide()
            self.back_card_group.hide()
            self.finish_session()
            return

        item = self.vocab_data[self.current_card]
        self.showing_front = True
        self.front_card_group.show()
        self.back_card_group.hide()

        # Show front card with word/phrase
        front = item.get("reference", "N/A")
        self.front_word_label.setText(front)
        self.pronunciation_label.setText(item.get("ipa_pronunciation", ""))

        # Disconnect any previous connections to avoid multiple calls
        try:
            self.enable_image_cb.toggled.disconnect()
        except TypeError:
            pass  # No connection to disconnect

        # Connect the checkbox to the image display logic, passing the current item
        self.enable_image_cb.toggled.connect(
            lambda state: self.toggle_image_display(state, item)
        )
        # Handle image display initially based on checkbox state and current item
        self.toggle_image_display(self.enable_image_cb.isChecked(), item)

        # Reset pronunciation checkbox
        self.show_pronunciation_cb.setChecked(False)
        self.pronunciation_label.hide()

        self.flip_btn.setText("Show ▶")
        self.flip_btn.setEnabled(True)
        self.playback_btn.setEnabled(False)
        self.record_btn.setEnabled(True)
        self.record_btn.setChecked(False)

        # Enable/disable back card TTS buttons
        if self.back_play_tts_btn:
            self.back_play_tts_btn.setEnabled(True)
        if self.back_play_slow_tts_btn:
            self.back_play_slow_tts_btn.setEnabled(True)

        # Store item for flip
        self.current_item = item

    def flip_card(self):
        """Flip the card to show the back side"""
        if self.showing_front and self.current_item:
            item = self.current_item
            self.showing_front = False

            # Show back card
            self.front_card_group.hide()
            self.back_card_group.show()

            # Update back card content
            self.back_word_label.setText(item.get("reference", "N/A"))
            self.back_pronunciation_label.setText(item.get("ipa_pronunciation", ""))
            self.definition_text.setText(item.get("definition", "No definition"))

            # Only reset feedback if no pronunciation feedback exists yet
            # Otherwise, preserve the existing pronunciation feedback
            if not self.pronunciation_data:
                self.feedback_progress.setValue(0)
                self.feedback_label.setText("Pronunciation: ")
                self.pronunciation_feedback_text.hide()
            else:
                # If we have pronunciation feedback, make sure it's visible
                self.pronunciation_feedback_text.show()

                # Also make sure the progress bar shows the correct score
                if self.pronunciation_data and "accuracy" in self.pronunciation_data:
                    accuracy = self.pronunciation_data["accuracy"]
                    self.feedback_progress.setValue(int(accuracy))
        else:
            # Go back to front
            self.show_card()

    def rate_difficulty(self, rating):
        """Rate the difficulty of the current card"""
        if self.current_card < len(self.vocab_data):
            item = self.vocab_data[self.current_card]
            item_id = item.get("reference", str(item))

            was_correct = rating >= 3
            accuracy = 100 if was_correct else 50

            self.progress.update_item(item_id, was_correct, accuracy)
            self.session.record_attempt(item, was_correct, accuracy)

        self.next_card()

    def next_card(self):
        """Move to the next card"""
        self.current_card += 1
        self.show_card()
        self.update_stats()

    def previous_card(self):
        """Go back to the previous card"""
        if self.current_card > 0:
            self.current_card -= 1
            self.show_card()
            self.update_stats()

    def update_stats(self):
        """Update the statistics display"""
        if self.session:
            stats = self.session.get_statistics()
            total = len(self.vocab_data)
            self.progress_label.setText(f"Card: {self.current_card + 1}/{total}")
            self.accuracy_label.setText(f"Accuracy: {stats['accuracy']:.1f}%")
            self.streak_label.setText(f"Streak: {stats.get('correct', 0)}")

    def play_tts(self):
        """Play TTS for the current card"""
        if not self.current_item:
            return

        # Get the text to speak (the reference word/phrase)
        text = self.current_item.get("reference", "").strip()
        if not text:
            return

        # Get language from config
        lang_code = self.config["language"].split("-")[0].lower()

        # Create and start TTS thread
        self.tts_thread = TTSThread(text, "gTTS", lang_code)
        self.tts_thread.start()

    def play_slow_tts(self):
        """Play TTS slowly for the current card"""
        if not self.current_item:
            return

        # Get the text to speak (the reference word/phrase)
        text = self.current_item.get("reference", "").strip()
        if not text:
            return

        # Get language from config
        lang_code = self.config["language"].split("-")[0].lower()

        # Create and start TTS thread with slow speed
        self.tts_thread = TTSThread(text, "gTTS", lang_code, slow=True)
        self.tts_thread.start()

    def toggle_recording(self):
        """Toggle recording mode"""
        if self.record_btn.isChecked():
            # Start recording
            self.record_thread = RecordThread(
                sample_rate=self.config.get("sample_rate", 16000)
            )
            self.record_thread.finished.connect(self.on_record_finished)
            self.record_thread.error.connect(self.on_record_error)
            self.record_thread.start()
        else:
            # Stop recording
            if self.record_thread:
                self.record_thread.stop_recording()

    def on_record_finished(self, filename):
        """Handle recording completion"""
        self.recorded_file = filename
        self.audio_file = filename
        # Update UI elements
        if hasattr(self, "playback_btn"):
            self.playback_btn.setEnabled(True)

        # Automatically convert the recorded audio for pronunciation feedback
        self.convert_audio_for_feedback()

    def on_record_error(self, error_msg):
        """Handle recording errors"""
        print(f"Recording error: {error_msg}")

    def play_user_recording(self):
        """Play back user recording"""
        if not self.audio_file:
            from PyQt5.QtWidgets import QMessageBox

            QMessageBox.warning(self, "No Audio", "Please record audio first.")
            return

        try:
            data, samplerate = sf.read(self.audio_file)
            sd.play(data, samplerate)

            # After playing, automatically convert the audio for pronunciation feedback
            self.convert_audio_for_feedback()
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox

            QMessageBox.critical(self, "Playback Error", str(e))

    def convert_audio_for_feedback(self):
        """Convert recorded audio to text and get pronunciation feedback"""
        if not self.audio_file:
            from PyQt5.QtWidgets import QMessageBox

            QMessageBox.warning(self, "No Audio", "Please record audio first.")
            return

        # Get the reference text for comparison (the word/phrase on the flashcard)
        if not self.current_item:
            return

        reference_text = self.current_item.get("reference", "").strip()
        if not reference_text:
            from PyQt5.QtWidgets import QMessageBox

            QMessageBox.warning(
                self, "No Reference", "No reference text available for comparison."
            )
            return

        # Start ASR conversion with reference text for pronunciation feedback
        from core.asr_engines import ASRThread

        self.asr_thread = ASRThread(
            self.audio_file,
            self.config,
            show_punctuation=True,
            show_word_time=False,
            reference_text=reference_text,
        )
        self.asr_thread.finished.connect(self.on_asr_finished_for_feedback)
        self.asr_thread.error.connect(self.on_asr_error)
        self.asr_thread.start()

    def on_asr_finished_for_feedback(self, text, metadata):
        """Handle ASR completion and display pronunciation feedback"""
        # Update the text display if needed
        # Handle pronunciation feedback
        if metadata and "pronunciation" in metadata:
            self.pronunciation_data = metadata["pronunciation"]
            self.display_pronunciation_feedback(metadata["pronunciation"])

    def on_asr_error(self, error_msg):
        """Handle ASR errors"""
        print(f"ASR Error: {error_msg}")
        from PyQt5.QtWidgets import QMessageBox

        QMessageBox.critical(self, "ASR Error", f"Error processing audio: {error_msg}")

    def display_pronunciation_feedback(self, pron_data):
        """Display detailed pronunciation feedback similar to main window"""
        accuracy = pron_data["accuracy"]

        # Make sure accuracy is a valid number between 0 and 100
        accuracy = max(0, min(100, float(accuracy)))

        # Update accuracy display on the progress bar
        self.feedback_progress.setValue(int(accuracy))

        # Color coding based on accuracy score
        # Green >= 80%, Yellow 60% to 79%, Red < 60%
        if accuracy >= 80:
            color = "green"
            status = "Excellent!"
        elif accuracy >= 60:
            color = "yellow"
            status = "Good"
        else:
            color = "red"
            status = "Needs Improvement"

        # Update progress bar color (using stylesheet)
        self.feedback_progress.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
                color: black;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                width: 1px;
            }}
        """)

        # Generate detailed feedback text
        feedback = f"=== PRONUNCIATION FEEDBACK ===\n\n"
        feedback += f"Overall Accuracy: {accuracy:.1f}% - {status}\n"
        feedback += f"Threshold: 80%\n\n"
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

        # Display the feedback text
        self.pronunciation_feedback_text.setPlainText(feedback)
        self.pronunciation_feedback_text.show()

        # Make sure the back card group is visible if we're currently showing the front
        if self.showing_front:
            # Store the fact that we have feedback for when the card is flipped
            self.has_pronunciation_feedback = True
        else:
            # We're already on the back card, so make sure it's visible
            self.pronunciation_feedback_text.show()

    def toggle_pronunciation(self, state):
        """Toggle pronunciation visibility"""
        if state == Qt.Checked:
            self.pronunciation_label.show()
        else:
            self.pronunciation_label.hide()

    def toggle_image_display(self, enabled, item=None):
        if enabled:
            if item and item.get("image_filename"):
                self.load_vocabulary_image(item.get("image_filename"))
            else:
                # Use default logo instead of text
                default_pixmap = self.load_default_logo()
                if default_pixmap and not default_pixmap.isNull():
                    self.image_label.setPixmap(
                        default_pixmap.scaled(
                            self.image_label.width() - 2,
                            self.image_label.height() - 2,
                            Qt.KeepAspectRatio,
                            Qt.SmoothTransformation,
                        )
                    )
                else:
                    self.image_label.setText("No Image")
                    self.image_label.setPixmap(QPixmap())  # Clear pixmap
        else:
            self.image_label.setText("Image disabled")
            self.image_label.setPixmap(QPixmap())  # Clear pixmap

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
                                self.image_label.setPixmap(
                                    pixmap.scaled(
                                        self.image_label.width() - 2,
                                        self.image_label.height() - 2,
                                        Qt.KeepAspectRatio,
                                        Qt.SmoothTransformation,
                                    )
                                )
                            return
            else:
                # Load from filesystem
                if self.vocab_file_path:
                    image_path = Path(self.vocab_file_path).parent / image_filename
                    if image_path.exists():
                        pixmap = QPixmap(str(image_path))
                        if not pixmap.isNull():
                            self.image_label.setPixmap(
                                pixmap.scaled(
                                    self.image_label.width() - 2,
                                    self.image_label.height() - 2,
                                    Qt.KeepAspectRatio,
                                    Qt.SmoothTransformation,
                                )
                            )
                            return
                    else:
                        # Image file not found - use default logo
                        default_pixmap = self.load_default_logo()
                        if default_pixmap and not default_pixmap.isNull():
                            self.image_label.setPixmap(
                                default_pixmap.scaled(
                                    self.image_label.width() - 2,
                                    self.image_label.height() - 2,
                                    Qt.KeepAspectRatio,
                                    Qt.SmoothTransformation,
                                )
                            )
                        return

        except Exception as e:
            print(f"Image load error: {e}")
            # Fallback to default logo
            default_pixmap = self.load_default_logo()
            if default_pixmap and not default_pixmap.isNull():
                self.image_label.setPixmap(
                    default_pixmap.scaled(
                        self.image_label.width() - 2,
                        self.image_label.height() - 2,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation,
                    )
                )
            else:
                self.image_label.setText("Image load error")

    def load_default_logo(self):
        """Load and cache the default logo image"""
        # Return cached version if already loaded
        if self.default_logo_pixmap is not None:
            return self.default_logo_pixmap

        try:
            logo_path = Path("Data") / "Logo.png"
            if logo_path.exists():
                pixmap = QPixmap(str(logo_path))
                if not pixmap.isNull():
                    # Cache the original pixmap (unscaled)
                    self.default_logo_pixmap = pixmap
                    return pixmap
        except Exception as e:
            print(f"Default logo load error: {e}")

        return None

    def show_settings(self):
        """Show settings dialog"""
        if self.settings_dialog is None:
            self.settings_dialog = FlashcardSettingsDialog(self.config, self)
            self.settings_dialog.settings_changed.connect(self.apply_settings)
            self.settings_dialog.settings_changed.connect(self.reset_session)
        self.settings_dialog.show()

    def apply_settings(self):
        """Apply settings from settings dialog"""
        if self.settings_dialog:
            self.shuffle_cards = self.settings_dialog.shuffle_cb.isChecked()

    def show_statistics(self):
        """Show statistics dialog"""
        stats_dialog = FlashcardStatsDialog(self.progress, self)
        stats_dialog.exec_()

    def show_help(self):
        """Show help information"""
        help_text = """
        <h2>Flashcard Mode Help</h2>
        <p><b>Front Card:</b></p>
        <ul>
            <li>View the word/phrase</li>
            <li>Click 🔊 to hear pronunciation</li>
            <li>Click 🐛 for slow pronunciation</li>
            <li>Check "Show Pronunciation" to see IPA</li>
            <li>Record your pronunciation with 🎤</li>
            <li>Click "Show" to see the answer</li>
        </ul>
        <p><b>Back Card:</b></p>
        <ul>
            <li>View the definition/translation</li>
            <li>See pronunciation feedback</li>
            <li>Rate your knowledge:</li>
            <li>🟢 Know - You knew it well</li>
            <li>🟡 Partially Known - Somewhat familiar</li>
            <li>🔴 Unknown - Didn't know it</li>
        </ul>
        <p><b>Navigation:</b></p>
        <ul>
            <li>Click "Previous" to go back</li>
            <li>Use Space key to flip card</li>
        </ul>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("Flashcard Help")
        msg.setTextFormat(Qt.RichText)
        msg.setText(help_text)
        msg.exec_()

    def practice_pronunciation(self):
        """Open pronunciation practice for current card"""
        # TODO: Implement pronunciation practice
        # This will integrate with the recording and ASR functionality
        pass

    def finish_session(self):
        """Complete the session and save progress"""
        self.progress.save()
        if self.session:
            self.session_completed.emit(self.session.get_statistics())

    def closeEvent(self, event):
        """Handle dialog close"""
        self.finish_session()
        event.accept()


class FlashcardStatsDialog(QDialog):
    """Dialog showing flashcard learning statistics"""

    def __init__(self, progress, parent=None):
        super().__init__(parent)
        self.progress = progress
        self.setWindowTitle("Flashcard Statistics")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        stats = self.progress.get_statistics()

        # Overall stats
        stats_group = QGroupBox("Overall Progress")
        stats_layout = QVBoxLayout()

        stats_layout.addWidget(QLabel(f"Total Items: {stats['total_items']}"))
        stats_layout.addWidget(QLabel(f"Mastered: {stats['mastered']}"))
        stats_layout.addWidget(QLabel(f"Learning: {stats['learning']}"))
        stats_layout.addWidget(
            QLabel(f"Average Accuracy: {stats['average_accuracy']:.1f}%")
        )

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # Due items
        due_count = len(self.progress.get_due_items([]))
        layout.addWidget(QLabel(f"Items Due for Review: {due_count}"))

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

        self.setLayout(layout)


class FlashcardSettingsDialog(QDialog):
    """Settings dialog for flashcard mode"""

    settings_changed = pyqtSignal()

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Flashcard Settings")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Show first option
        show_first_layout = QHBoxLayout()
        show_first_layout.addWidget(QLabel("Show First:"))
        self.show_first_combo = QComboBox()
        self.show_first_combo.addItems(["Word/Phrase", "Definition/Translation"])
        show_first_layout.addWidget(self.show_first_combo)
        layout.addLayout(show_first_layout)

        # Shuffle option
        self.shuffle_cb = QCheckBox("Shuffle Cards")
        self.shuffle_cb.setChecked(True)
        layout.addWidget(self.shuffle_cb)

        # Repeat incorrect
        self.repeat_incorrect_cb = QCheckBox("Repeat Incorrect Cards")
        self.repeat_incorrect_cb.setChecked(True)
        layout.addWidget(self.repeat_incorrect_cb)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save_and_close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def save_and_close(self):
        self.settings_changed.emit()
        self.accept()
