# Project Structure Summary

## Modular Architecture (Version 3.0)

The application has been modularized into a clean, extensible architecture:

```
ASR_Language_Training/
├── main.py                         # Application entry point
├── config.py                       # Configuration dialog and default settings
├── requirements.txt                # Python dependencies
├── README.md                       # Primary documentation
├── HELP.md                         # User guide and help
├── PROJECT_STRUCTURE.md            # This file
├── asr_app.py                      # Original monolithic file (preserved for reference)
│
├── core/                           # Core functionality package
│   ├── __init__.py
│   ├── recorder.py                 # Audio recording (RecordThread class)
│   │                                 - Microphone input handling
│   │                                 - Audio buffer management
│   │                                 - Temporary file creation
│   │
│   ├── asr_engines.py              # ASR engine implementations
│   │                                 - ASRThread: Main ASR processing
│   │                                 - Google Speech Recognition support
│   │                                 - Whisper (OpenAI) support
│   │                                 - Qwen3-ASR support (new)
│   │                                 - ASREngineManager: Future engine management
│   │                                 - Planned: Vosk, Azure, AWS, IBM Watson
│   │
│   └── tts_engines.py              # TTS engine implementations
│                                     - TTSBase: Abstract base class
│                                     - gTTSEngine: Google TTS (current)
│                                     - Pyttsx3Engine: Offline TTS (planned)
│                                     - EspeakEngine: Open source (planned)
│                                     - TTSThread: Async TTS playback
│                                     - TTSEngineManager: Engine management
│
├── ui/                             # User interface package
│   ├── __init__.py
│   ├── main_window.py              # Main application window (ASRApp class)
│   │                                 - Vocabulary navigation
│   │                                 - Recording controls
│   │                                 - ASR/TTS integration
│   │                                 - Pronunciation feedback display
│   │
│   ├── flashcards.py               # Flashcard mode implementation
│   │                                 - FlashcardDialog: Interactive learning UI
│   │                                 - FlashcardSession: Session management
│   │                                 - FlashcardProgress: Persistent storage
│   │                                 - Spaced repetition algorithm
│   │                                 - Statistics tracking
│   │
│   └── components.py               # Reusable UI components
│                                     - PronunciationFeedbackWidget
│                                     - AudioLevelIndicator
│                                     - ImageViewer
│                                     - StatusLog
│                                     - RecordingButton
│                                     - VocabularyNavigator
│                                     - ExpandableGroup
│
└── utils/                          # Utility modules
    ├── __init__.py
    ├── text_processing.py          # Text processing utilities
    │                                 - normalize_text()
    │                                 - clean_ai_response()
    │                                 - clean_display_text()
    │                                 - text_to_ipa_modern()
    │                                 - split_into_sentences()
    │                                 - calculate_similarity()
    │                                 - highlight_differences()
    │                                 - TextProcessor class
    │
    └── storage.py                  # Data storage utilities
                                      - CSV/JSON import/export
                                      - save_text_to_file()
                                      - generate_pronunciation_report()
                                      - SessionStorage class
                                      - ReportGenerator class
                                      - load_vocabulary_from_zip()
```

## Module Responsibilities

### `main.py`
- Application entry point
- QApplication initialization
- Main window creation and display

### `config.py`
- ConfigurationDialog: Settings UI
- DEFAULT_CONFIG: Default application settings
- Engine selection options
- Language mappings
- Vocabulary column configuration

### `core/` Package

#### `recorder.py`
- RecordThread: QThread-based audio recording
- Real-time audio capture using sounddevice
- WAV file output

#### `asr_engines.py`
- ASRThread: Multi-engine ASR processing
- Google Speech Recognition integration
- Whisper model loading and transcription
- Qwen3-ASR integration (new)
- Pronunciation analysis (accuracy calculation)
- ASREngineManager: Plugin architecture for future engines

#### `tts_engines.py`
- TTSBase: Abstract interface for TTS engines
- gTTSEngine: Current implementation
- Placeholder classes for pyttsx3, espeak
- TTSThread: Non-blocking TTS playback
- Support for word-by-word slow playback

### `ui/` Package

#### `main_window.py`
- ASRApp: Main QMainWindow
- Vocabulary loading and navigation
- Recording and playback controls
- ASR conversion workflow
- Pronunciation feedback display
- Integration with all modules

#### `flashcards.py`
- Complete flashcard learning system
- Spaced repetition with difficulty ratings
- Session-based learning
- Persistent progress tracking
- Statistics visualization

#### `components.py`
- Custom widgets for reuse across UI
- Audio level visualization
- Image display with scaling
- Status logging with timestamps
- Recording button with hold functionality

### `utils/` Package

#### `text_processing.py`
- Text normalization for comparison
- IPA pronunciation generation
- Text cleaning utilities
- Diff/highlight functionality

#### `storage.py`
- File I/O operations
- Report generation
- Session history tracking
- ZIP file vocabulary loading
- CSV import/export

## Data Flow

```
User Input → UI (main_window.py) → Core Modules → Output
                ↓
         config.py (settings)
                ↓
    ┌───────────┴───────────┐
    ↓                       ↓
recorder.py            asr_engines.py
(audio input)          (speech recognition)
    ↓                       ↓
    └───────────┬───────────┘
                ↓
         tts_engines.py
         (speech output)
                ↓
         utils/storage.py
         (persistence)
                ↓
         ui/flashcards.py
         (learning mode)
```

## Extension Points

### Adding New ASR Engines
1. Create engine class in `core/asr_engines.py`
2. Inherit from base pattern in `ASRThread`
3. Register in `ASREngineManager`
4. Add to config options in `config.py`

### Adding New TTS Engines
1. Create engine class inheriting from `TTSBase`
2. Implement `speak()` and `speak_words_sequentially()`
3. Register in `TTSEngineManager`
4. Update configuration options

### Adding New UI Components
1. Create widget in `ui/components.py`
2. Import and use in `main_window.py` or `flashcards.py`
3. Follow existing signal/slot patterns

## Files Generated at Runtime

- `flashcard_progress.json` - Flashcard learning progress
- `session_data.json` - Practice session history
- `*.wav` - Temporary audio recordings (cleaned up automatically)
- `backup_*.json` - Automatic backups (if configured)

## Migration from Monolithic Version

The original `asr_app.py` (single 109KB file) has been refactored into:
- `main.py` (entry point)
- `config.py` (configuration)
- `ui/main_window.py` (main UI)
- `ui/flashcards.py` (new feature)
- `ui/components.py` (UI utilities)
- `core/recorder.py` (audio)
- `core/asr_engines.py` (ASR)
- `core/tts_engines.py` (TTS)
- `utils/text_processing.py` (text)
- `utils/storage.py` (persistence)

**Total modular files**: 11 Python modules (vs 1 monolithic file)
**New features added**: Flashcard mode, progress tracking, extensible engine architecture

## Benefits of Modularization

1. **Maintainability**: Each module has a single responsibility
2. **Testability**: Modules can be tested independently
3. **Extensibility**: New engines/features added without modifying existing code
4. **Readability**: Smaller files are easier to understand
5. **Collaboration**: Multiple developers can work on different modules
6. **Reusability**: Components can be reused in other projects

## Ready for Development

This modular structure enables:
- Easy addition of new ASR/TTS engines
- Implementation of planned features
- Collaborative development
- Unit testing of individual components
- Future GUI framework migration (if needed)
- Plugin architecture for community extensions
