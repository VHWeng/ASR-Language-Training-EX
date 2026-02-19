"""
ASR Application with PyQt5 GUI
Main entry point for the modularized application

Supports:
- Google Speech Recognition and Whisper ASR engines
- Text-to-Speech (TTS) with gTTS and planned engines
- Pronunciation Training with feedback
- Flashcard Mode with progress tracking
- Vocabulary management from CSV/TXT/ZIP files

Default language: Greek
"""

import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import ASRApp


def main():
    """Main entry point for the ASR Application"""
    app = QApplication(sys.argv)
    app.setApplicationName("ASR Application")
    app.setApplicationVersion("2.0")

    window = ASRApp()
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
