"""
Flashcard Mode module for ASR Application
Provides spaced repetition learning with progress tracking
"""

import json
import random
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QProgressBar, QCheckBox, QSpinBox, QGroupBox,
    QMessageBox, QDialog, QDialogButtonBox, QComboBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont


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
        self.session_log.append({
            'timestamp': datetime.now().isoformat(),
            'vocab_item': vocab_item,
            'correct': was_correct,
            'accuracy': accuracy_score
        })
        if was_correct:
            self.correct_count += 1
        else:
            self.incorrect_count += 1

    def get_statistics(self):
        """Get session statistics"""
        total = self.correct_count + self.incorrect_count
        if total == 0:
            return {'accuracy': 0, 'total': 0}
        return {
            'accuracy': (self.correct_count / total) * 100,
            'total': total,
            'correct': self.correct_count,
            'incorrect': self.incorrect_count,
            'duration_seconds': (datetime.now() - self.start_time).total_seconds()
        }


class FlashcardProgress:
    """
    Manages user progress for flashcard learning
    Implements spaced repetition algorithm
    """

    def __init__(self, storage_path='flashcard_progress.json'):
        self.storage_path = storage_path
        self.items = {}  # {item_id: progress_data}
        self.load()

    def load(self):
        """Load progress from storage"""
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.items = data.get('items', {})
        except FileNotFoundError:
            self.items = {}

    def save(self):
        """Save progress to storage"""
        data = {
            'last_saved': datetime.now().isoformat(),
            'items': self.items
        }
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def update_item(self, item_id, was_correct, accuracy_score):
        """Update progress for an item"""
        if item_id not in self.items:
            self.items[item_id] = {
                'created': datetime.now().isoformat(),
                'attempts': 0,
                'correct_count': 0,
                'total_accuracy': 0,
                'last_reviewed': None,
                'next_review': datetime.now().isoformat(),
                'difficulty_level': 1,  # 1-5
                'streak': 0
            }

        item = self.items[item_id]
        item['attempts'] += 1
        item['last_reviewed'] = datetime.now().isoformat()
        item['total_accuracy'] += accuracy_score

        if was_correct:
            item['correct_count'] += 1
            item['streak'] += 1
            item['difficulty_level'] = min(5, item['difficulty_level'] + 1)
        else:
            item['streak'] = 0
            item['difficulty_level'] = max(1, item['difficulty_level'] - 1)

        # Calculate next review (spaced repetition)
        days_until_review = self._calculate_review_interval(item)
        item['next_review'] = (datetime.now() + timedelta(days=days_until_review)).isoformat()

    def _calculate_review_interval(self, item):
        """Calculate days until next review based on performance"""
        streak = item['streak']
        difficulty = item['difficulty_level']

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
            item_id = item.get('reference', str(item))
            if item_id in self.items:
                if self.items[item_id]['next_review'] <= now:
                    due.append(item)
            else:
                due.append(item)  # New items are always due
        return due

    def get_statistics(self):
        """Get overall learning statistics"""
        if not self.items:
            return {
                'total_items': 0,
                'mastered': 0,
                'learning': 0,
                'average_accuracy': 0
            }

        total = len(self.items)
        mastered = sum(1 for item in self.items.values() if item['difficulty_level'] >= 4)
        avg_accuracy = sum(item['total_accuracy'] / item['attempts']
                          for item in self.items.values() if item['attempts'] > 0) / total

        return {
            'total_items': total,
            'mastered': mastered,
            'learning': total - mastered,
            'average_accuracy': avg_accuracy
        }


class FlashcardDialog(QDialog):
    """
    Flashcard Mode dialog
    Interactive learning mode with pronunciation practice
    """
    session_completed = pyqtSignal(dict)

    def __init__(self, vocab_data, config, parent=None):
        super().__init__(parent)
        self.vocab_data = vocab_data
        self.config = config
        self.progress = FlashcardProgress()
        self.session = None
        self.current_card = None
        self.showing_front = True  # True = word, False = definition

        self.setWindowTitle("Flashcard Mode")
        self.setMinimumSize(600, 500)
        self.init_ui()
        self.start_session()

    def init_ui(self):
        layout = QVBoxLayout()

        # Session stats
        stats_group = QGroupBox("Session Progress")
        stats_layout = QHBoxLayout()

        self.progress_label = QLabel("Card: 0/0")
        self.accuracy_label = QLabel("Accuracy: 0%")
        self.streak_label = QLabel("Streak: 0")

        stats_layout.addWidget(self.progress_label)
        stats_layout.addWidget(self.accuracy_label)
        stats_layout.addWidget(self.streak_label)
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # Card display
        self.card_group = QGroupBox("Flashcard")
        card_layout = QVBoxLayout()

        self.card_text = QTextEdit()
        self.card_text.setReadOnly(True)
        self.card_text.setAlignment(Qt.AlignCenter)
        self.card_text.setFont(QFont("Arial", 24))
        self.card_text.setStyleSheet("""
            QTextEdit {
                background-color: #f0f0f0;
                border: 2px solid #ccc;
                border-radius: 10px;
            }
        """)
        card_layout.addWidget(self.card_text)

        # Pronunciation display
        self.pronunciation_label = QLabel()
        self.pronunciation_label.setAlignment(Qt.AlignCenter)
        self.pronunciation_label.setFont(QFont("Arial", 14))
        card_layout.addWidget(self.pronunciation_label)

        # Flip button
        self.flip_btn = QPushButton("Flip Card (Space)")
        self.flip_btn.setShortcut("Space")
        self.flip_btn.clicked.connect(self.flip_card)
        card_layout.addWidget(self.flip_btn)

        self.card_group.setLayout(card_layout)
        layout.addWidget(self.card_group)

        # Control buttons
        control_layout = QHBoxLayout()

        self.prev_btn = QPushButton("◀ Previous")
        self.prev_btn.clicked.connect(self.previous_card)
        control_layout.addWidget(self.prev_btn)

        self.play_tts_btn = QPushButton("🔊 Play Pronunciation")
        self.play_tts_btn.clicked.connect(self.play_tts)
        control_layout.addWidget(self.play_tts_btn)

        self.record_btn = QPushButton("🎤 Practice Pronunciation")
        self.record_btn.clicked.connect(self.practice_pronunciation)
        control_layout.addWidget(self.record_btn)

        self.next_btn = QPushButton("Next ▶")
        self.next_btn.clicked.connect(self.next_card)
        control_layout.addWidget(self.next_btn)

        layout.addLayout(control_layout)

        # Difficulty rating (shown after flip)
        self.difficulty_group = QGroupBox("How well did you know this?")
        difficulty_layout = QHBoxLayout()

        self.again_btn = QPushButton("Again")
        self.again_btn.setStyleSheet("background-color: #ff6b6b;")
        self.again_btn.clicked.connect(lambda: self.rate_difficulty(1))

        self.hard_btn = QPushButton("Hard")
        self.hard_btn.setStyleSheet("background-color: #ffa500;")
        self.hard_btn.clicked.connect(lambda: self.rate_difficulty(2))

        self.good_btn = QPushButton("Good")
        self.good_btn.setStyleSheet("background-color: #4ecdc4;")
        self.good_btn.clicked.connect(lambda: self.rate_difficulty(3))

        self.easy_btn = QPushButton("Easy")
        self.easy_btn.setStyleSheet("background-color: #95e1d3;")
        self.easy_btn.clicked.connect(lambda: self.rate_difficulty(4))

        difficulty_layout.addWidget(self.again_btn)
        difficulty_layout.addWidget(self.hard_btn)
        difficulty_layout.addWidget(self.good_btn)
        difficulty_layout.addWidget(self.easy_btn)

        self.difficulty_group.setLayout(difficulty_layout)
        self.difficulty_group.hide()  # Hidden until card is flipped
        layout.addWidget(self.difficulty_group)

        # Settings
        settings_group = QGroupBox("Mode Settings")
        settings_layout = QVBoxLayout()

        self.show_first_combo = QComboBox()
        self.show_first_combo.addItems(["Show Word First", "Show Definition First"])
        self.show_first_combo.currentTextChanged.connect(self.reset_session)
        settings_layout.addWidget(self.show_first_combo)

        self.shuffle_cb = QCheckBox("Shuffle Cards")
        self.shuffle_cb.stateChanged.connect(self.reset_session)
        settings_layout.addWidget(self.shuffle_cb)

        self.repeat_incorrect_cb = QCheckBox("Repeat Incorrect Cards")
        self.repeat_incorrect_cb.setChecked(True)
        settings_layout.addWidget(self.repeat_incorrect_cb)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # Close button
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.close)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def start_session(self):
        """Initialize a new flashcard session"""
        vocab = self.vocab_data.copy()
        if self.shuffle_cb.isChecked():
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
            self.card_text.setText("Session Complete!")
            self.finish_session()
            return

        item = self.vocab_data[self.current_card]
        self.showing_front = True
        self.difficulty_group.hide()

        show_word_first = "Word" in self.show_first_combo.currentText()

        if show_word_first:
            front = item.get('reference', 'N/A')
            back = item.get('definition', 'No definition')
        else:
            front = item.get('definition', 'No definition')
            back = item.get('reference', 'N/A')

        self.card_text.setText(f"{front}")
        self.flip_btn.setText("Flip Card (Space)")

        # Store back content for flip
        self.current_back = back

    def flip_card(self):
        """Flip the card to show the other side"""
        if self.showing_front:
            self.card_text.setText(f"{self.card_text.toPlainText()}\n\n{'='*40}\n\n{self.current_back}")
            self.showing_front = False
            self.flip_btn.setText("Show Answer")
            self.difficulty_group.show()

            # Show pronunciation if available
            if self.current_card < len(self.vocab_data):
                item = self.vocab_data[self.current_card]
                ipa = item.get('ipa_pronunciation', '')
                if ipa:
                    self.pronunciation_label.setText(f"IPA: {ipa}")
        else:
            self.show_card()

    def rate_difficulty(self, rating):
        """Rate the difficulty of the current card"""
        if self.current_card < len(self.vocab_data):
            item = self.vocab_data[self.current_card]
            item_id = item.get('reference', str(item))

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
        # TODO: Implement TTS playback
        # This will integrate with the TTS engines from core.tts_engines
        pass

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
        stats_layout.addWidget(QLabel(f"Average Accuracy: {stats['average_accuracy']:.1f}%"))

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
