"""
Custom UI components and widgets for ASR Application
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QProgressBar, QFrame, QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor


class PronunciationFeedbackWidget(QWidget):
    """Widget displaying pronunciation feedback with visual indicators"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Accuracy display
        accuracy_layout = QHBoxLayout()
        self.accuracy_label = QLabel("Accuracy: N/A")
        self.accuracy_label.setFont(QFont("Arial", 16, QFont.Bold))
        accuracy_layout.addWidget(self.accuracy_label)

        self.accuracy_bar = QProgressBar()
        self.accuracy_bar.setMaximum(100)
        self.accuracy_bar.setValue(0)
        accuracy_layout.addWidget(self.accuracy_bar)

        layout.addLayout(accuracy_layout)

        # Status indicator
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        # Word analysis area
        self.word_analysis = QTextEdit()
        self.word_analysis.setReadOnly(True)
        self.word_analysis.setMaximumHeight(200)
        layout.addWidget(self.word_analysis)

        self.setLayout(layout)

    def update_feedback(self, accuracy, threshold=80, word_analysis=None):
        """Update the feedback display"""
        self.accuracy_label.setText(f"Accuracy: {accuracy:.1f}%")
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
        self.status_label.setText(status)

        # Update word analysis
        if word_analysis:
            self.display_word_analysis(word_analysis)

    def display_word_analysis(self, word_analysis):
        """Display word-by-word analysis"""
        text = "Word Analysis:\n"
        for i, word in enumerate(word_analysis, 1):
            status_icon = {
                'correct': '✓',
                'incorrect': '✗',
                'missing': '✗',
                'extra': '⚠'
            }.get(word['status'], '?')

            text += f"{i}. {status_icon} '{word['reference']}' → '{word['recognized']}' ({word['similarity']:.1f}%)\n"

        self.word_analysis.setText(text)


class AudioLevelIndicator(QWidget):
    """Visual audio level meter for recording feedback"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.level = 0
        self.setMinimumHeight(30)
        self.setMaximumHeight(50)

    def set_level(self, level):
        """Set the audio level (0-100)"""
        self.level = min(100, max(0, level))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        width = self.width()
        height = self.height()

        # Draw background
        painter.fillRect(0, 0, width, height, QColor(200, 200, 200))

        # Draw level bar
        bar_width = int(width * (self.level / 100))

        # Color based on level
        if self.level < 30:
            color = QColor(100, 200, 100)  # Green
        elif self.level < 70:
            color = QColor(255, 200, 0)  # Yellow
        else:
            color = QColor(255, 100, 100)  # Red

        painter.fillRect(0, 0, bar_width, height, color)


class ImageViewer(QWidget):
    """Image display widget with scaling"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pixmap = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setText("No image loaded")
        self.label.setStyleSheet("border: 1px solid gray; background-color: #f0f0f0;")
        self.label.setMinimumHeight(200)

        layout.addWidget(self.label)
        self.setLayout(layout)

    def set_image(self, pixmap):
        """Set the displayed image"""
        if pixmap and not pixmap.isNull():
            self.pixmap = pixmap
            # Scale to fit while maintaining aspect ratio
            scaled = pixmap.scaled(
                self.label.width() - 20,
                self.label.height() - 20,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.label.setPixmap(scaled)
            self.label.setText("")
        else:
            self.label.setPixmap(QPixmap())
            self.label.setText("Invalid image")

    def resizeEvent(self, event):
        """Handle resize to rescale image"""
        super().resizeEvent(event)
        if self.pixmap:
            self.set_image(self.pixmap)


class StatusLog(QWidget):
    """Status message log widget"""

    message_logged = pyqtSignal(str)

    def __init__(self, parent=None, max_lines=100):
        super().__init__(parent)
        self.max_lines = max_lines
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setMaximumHeight(100)
        font = QFont("Consolas", 9)
        self.text_edit.setFont(font)

        layout.addWidget(self.text_edit)
        self.setLayout(layout)

        self.message_logged.connect(self._append_message)

    def _append_message(self, message):
        """Internal method to append message"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.text_edit.append(f"[{timestamp}] {message}")

        # Limit lines
        text = self.text_edit.toPlainText()
        lines = text.split('\n')
        if len(lines) > self.max_lines:
            self.text_edit.setPlainText('\n'.join(lines[-self.max_lines:]))

    def log(self, message):
        """Log a status message"""
        self.message_logged.emit(message)

    def clear(self):
        """Clear the log"""
        self.text_edit.clear()


class RecordingButton(QPushButton):
    """Custom button for recording with hold functionality"""

    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("🎤 Hold to Record", parent)
        self.is_recording = False
        self.setStyleSheet("QPushButton { font-weight: bold; padding: 10px; }")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_recording = True
            self.setText("⏹️ Stop Recording")
            self.recording_started.emit()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_recording:
            self.is_recording = False
            self.setText("🎤 Hold to Record")
            self.recording_stopped.emit()
        super().mouseReleaseEvent(event)

    def stop_recording(self):
        """Force stop recording"""
        if self.is_recording:
            self.is_recording = False
            self.setText("🎤 Hold to Record")
            self.recording_stopped.emit()


class ExpandableGroup(QWidget):
    """Expandable group widget for organizing UI sections"""

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.title = title
        self.is_expanded = True
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header_layout = QHBoxLayout()
        self.toggle_btn = QPushButton("▼")
        self.toggle_btn.setFixedWidth(30)
        self.toggle_btn.clicked.connect(self.toggle)

        header_layout.addWidget(self.toggle_btn)
        header_layout.addWidget(QLabel(self.title))
        header_layout.addStretch()

        header_widget = QWidget()
        header_widget.setLayout(header_layout)
        layout.addWidget(header_widget)

        # Content container
        self.content = QWidget()
        self.content_layout = QVBoxLayout()
        self.content.setLayout(self.content_layout)
        layout.addWidget(self.content)

        self.setLayout(layout)

    def toggle(self):
        """Toggle expansion"""
        self.is_expanded = not self.is_expanded
        self.content.setVisible(self.is_expanded)
        self.toggle_btn.setText("▼" if self.is_expanded else "▶")

    def add_widget(self, widget):
        """Add a widget to the content area"""
        self.content_layout.addWidget(widget)

    def add_layout(self, layout):
        """Add a layout to the content area"""
        self.content_layout.addLayout(layout)


class VocabularyNavigator(QWidget):
    """Navigation widget for vocabulary items"""

    previous_clicked = pyqtSignal()
    next_clicked = pyqtSignal()
    item_changed = pyqtSignal(int)  # Emit current index

    def __init__(self, total_items=0, parent=None):
        super().__init__(parent)
        self.total_items = total_items
        self.current_index = 0
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()

        self.prev_btn = QPushButton("◀ Previous")
        self.prev_btn.clicked.connect(self.previous)

        self.counter_label = QLabel("0 / 0")
        self.counter_label.setAlignment(Qt.AlignCenter)

        self.next_btn = QPushButton("Next ▶")
        self.next_btn.clicked.connect(self.next)

        layout.addWidget(self.prev_btn)
        layout.addWidget(self.counter_label)
        layout.addWidget(self.next_btn)

        self.setLayout(layout)
        self.update_state()

    def set_total(self, total):
        """Set total number of items"""
        self.total_items = total
        self.current_index = 0
        self.update_state()

    def set_current(self, index):
        """Set current index"""
        self.current_index = index
        self.update_state()

    def previous(self):
        """Go to previous item"""
        if self.current_index > 0:
            self.current_index -= 1
            self.update_state()
            self.previous_clicked.emit()
            self.item_changed.emit(self.current_index)

    def next(self):
        """Go to next item"""
        if self.current_index < self.total_items - 1:
            self.current_index += 1
            self.update_state()
            self.next_clicked.emit()
            self.item_changed.emit(self.current_index)

    def update_state(self):
        """Update button states and counter"""
        self.prev_btn.setEnabled(self.current_index > 0)
        self.next_btn.setEnabled(self.current_index < self.total_items - 1)
        self.counter_label.setText(f"{self.current_index + 1} / {self.total_items}")
