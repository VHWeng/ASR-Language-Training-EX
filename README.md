# ASR Application with Pronunciation Training

An advanced speech recognition application with pronunciation training capabilities, built using Python and PyQt5. This application provides comprehensive language learning tools including vocabulary management, pronunciation practice, flashcard mode with progress tracking, and interactive speech recognition.

## 🚀 Key Features

### 🎯 Core Functionality
- **Speech Recognition**: Multiple engine support (Google Speech Recognition, Whisper) with extensible architecture for additional engines
- **Pronunciation Training**: Interactive pronunciation practice with detailed feedback
- **Flashcard Mode**: Spaced repetition learning with progress tracking and statistics
- **Vocabulary Management**: Load and navigate through vocabulary sets from CSV/ZIP files
- **Image Support**: Display images associated with vocabulary entries; includes default logo fallback when images are missing
- **Grammar Display**: Show grammatical information alongside vocabulary entries
- **Mnemonics Support**: Add memory aids to vocabulary with configurable column mapping and selective display in both main and flashcard windows

### 📚 Vocabulary System
- Load vocabulary from CSV, TXT, or ZIP files
- Support for custom column mappings and delimiters
- Navigation between vocabulary entries (Previous/Next buttons)
- Image loading from ZIP archives with "images" subdirectory support

### 🔊 Audio Features
- Audio recording and playback
- Text-to-Speech (TTS) with normal and slow modes
- ASR conversion with accuracy scoring
- Pronunciation feedback and assessment
- **Multiple TTS Engines**: Support for gTTS (Google) and Microsoft Edge TTS (edge-tts) with configurable voice selection
- **Polytonic Greek Normalization**: Automatic conversion of polytonic Greek to monotonic for edge-tts (configurable, enabled by default)

### 🎴 Flashcard Mode
- Interactive flashcard learning with spaced repetition
- Difficulty rating system (Again/Hard/Good/Easy)
- Progress tracking and statistics
- Session-based learning with streak counting
- Due item review system
- **Image Support**: Display contextual images for vocabulary items
  - Images shown automatically when available in vocabulary files
  - Supported formats: PNG, JPG, JPEG, GIF
  - Images displayed on the front of flashcards for visual context
  - Images loaded from ZIP archives with "images" subdirectory support
  - **Default Logo Fallback**: Shows application logo when vocabulary images are unavailable
- **Backside TTS Controls**: Play and Slow Play buttons for pronunciation review
  - TTS buttons located under pronunciation on card back
  - Replay word pronunciation after revealing definition
  - Normal and slow speed options for learning

### ⚙️ Configuration
- Customizable column mappings for vocabulary files
- Multiple delimiter support (comma, pipe, tab, semicolon)
- Language selection for speech recognition
- **TTS Engine Selection**: Choose between gTTS and Edge TTS, with voice selection for Edge TTS
- **Preset Management**: Save and load configuration presets as JSON files in the `Data/` directory, and restore defaults with one click
- Intuitive user interface with clear status feedback

## Installation

### Prerequisites
- Python 3.10 or higher (recommended)
- Git (for version control)
- FFmpeg (for audio processing)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/VHWeng/ASR-Language-Training
cd ASR_Language_Training
```

2. Create virtual environment:
```bash
python -m venv venv
# Or for better compatibility:
python -m venv .venv
```

3. Activate virtual environment:
```bash
# Windows (Command Prompt)
venv\Scripts\activate

# Windows (PowerShell)
venv\Scripts\Activate.ps1

# Linux/Mac
source venv/bin/activate
```

4. Install dependencies:
```bash
# Install core requirements
pip install -r requirements.txt

# Optional: Install additional audio libraries for better compatibility
pip install pyaudio
```

### System Requirements

#### Required Dependencies
See [requirements.txt](requirements.txt) for detailed Python package dependencies.

#### System Dependencies
- **FFmpeg**: Required for MP3 support and audio processing
  - Windows: Download from https://ffmpeg.org/download.html
  - Ubuntu/Debian: `sudo apt install ffmpeg`
  - macOS: `brew install ffmpeg`

#### Recommended Hardware
- Microphone for recording
- Speakers or headphones for audio playback
- Modern CPU for Whisper processing (optional but recommended)

## Usage

### Starting the Application
```bash
python main.py
```

### Getting Started

1. **Initial Setup**
   - Launch the application: `python main.py`
   - Configure your preferred settings via the gear icon (⚙)

2. **Loading Vocabulary**
   - Click "📁 Load Vocabulary" to import your learning materials
   - Supported formats: CSV, TXT, or ZIP archives
   - Create your own vocabulary files following the format described below
   - ZIP files should contain:
     - Vocabulary file in the root directory
     - Images folder named "images/" with corresponding image files
   - Ensure your vocabulary file includes a column for mnemonics (default: column 8) if you want to use this feature

3. **Interactive Learning**
   - Navigate through vocabulary items using Previous/Next buttons
   - View definitions, pronunciations, images, grammatical information, and mnemonics
   - Built-in tools enhance entries with IPA pronunciations
   - Use the "Show Mnemonics" checkbox to toggle the mnemonics display

4. **Pronunciation Practice**
   - Listen to correct pronunciation via TTS (normal or slow speed)
   - Record your attempt using the "Hold to Record" feature
   - Receive detailed feedback on accuracy and improvement areas

5. **Flashcard Mode**
   - Click the flashcard icon (🎴) to start flashcard mode
   - Practice vocabulary with spaced repetition
   - Rate your knowledge level for each card
   - Track your progress over time
   - Use the "Show Mnemonics" checkbox on the back of cards to display memory aids

### Advanced Features

#### Customization Options
- Map vocabulary columns to match your file structure
- Choose from multiple delimiter types (comma, pipe, tab, semicolon)
- Select preferred speech recognition engine and language
- **Grammar Column**: Specify the column containing grammar information in your vocabulary files.
- **Mnemonics Column**: Specify the column containing memory aids for vocabulary entries (default: column 8)
- **Image Support**: Include images in vocabulary files for visual learning context

#### Image Integration
- Display contextual images for vocabulary items
- Support for common image formats (PNG, JPG, GIF)
- Automatic loading from ZIP archive structures
- **Flashcard Image Display**: Images automatically shown on flashcard fronts when available
- **Default Logo Fallback**: When images are missing or fail to load, displays `Data/Logo.png` as a fallback

## Modular Architecture (Version 3.0)

The application has been modularized into a clean, extensible architecture:

```
ASR_Language_Training/
├── main.py                         # Application entry point
├── config.py                       # Configuration dialog and default settings
├── requirements.txt                # Python dependencies
├── README.md                       # Primary documentation
├── HELP.md                         # User guide and help
├── PROJECT_STRUCTURE.md            # Project structure documentation
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
│                                     - gTTSEngine: Google TTS
│                                     - EdgeTTSEngine: Microsoft Edge TTS (needs edge-tts package)
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
    ┌─────────────────────┐
    │                       │
    ↓                       ↓
recorder.py            asr_engines.py
(audio input)          (speech recognition)
    ↓                       ↓
    └─────────────────────┘
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

## Latest Updates (2026)

### New Feature: Mnemonics Support (Version 3.1.0)
- Added configurable mnemonics column (default: column 8) for vocabulary files
- **Main Window**: "Show Mnemonics" checkbox and text box below grammar section
- **Flashcard Mode**: Mnemonics display on back of cards with toggle checkbox
- Fully integrated with existing column mapping configuration
- Sample vocabulary file with mnemonics: `Data/sample_with_mnemonics.csv`

### New ASR Engine: Qwen3-ASR
- Added support for Qwen3-ASR engine
- Enhanced multi-engine ASR processing capabilities
- Improved accuracy and language support
- Configurable engine selection in settings

### Technical Improvements
- Enhanced modular architecture for better maintainability
- Improved error handling and logging
- Optimized performance for larger vocabulary sets
- Better integration with flashcard learning system

### Feature Enhancements
- More accurate pronunciation feedback
- Improved vocabulary loading and management
- Enhanced user interface responsiveness
- Better progress tracking and statistics
- **Flashcard Image Improvements**: Default logo fallback when vocabulary images unavailable
- **Flashcard Backside TTS**: Added Play and Slow Play buttons under pronunciation for audio review

For complete version history and detailed changes, consult the git commit log.

## Testing

The application can be tested by running it directly:

```bash
python main.py
```

Verify functionality by:
- Creating and loading your own vocabulary files
- Testing speech recognition with different engines
- Practicing pronunciation training features
- Verifying image loading from ZIP archives
- Testing flashcard mode with vocabulary

## Local Git

To save your changes to the local git repository, use the following commands:

```bash
# Stage all changes
git add .

# Commit the changes with a message
git commit -m "Your commit message here"

# Check the status of the repository
git status
```

## Troubleshooting

### Common Issues and Solutions

#### Media Handling
**Image Loading Failures**
- ✅ Validate ZIP structure (images/ subdirectory)
- ✅ Confirm supported formats (.png, .jpg, .jpeg, .gif)
- ✅ Verify column 6 contains correct relative filenames
- ✅ Check file permissions and path encoding
- ✅ Ensure images are properly referenced in vocabulary files for flashcard display

**Audio Recording Issues**
- ✅ Grant microphone permissions to Python/application
- ✅ Test audio drivers and system sound settings
- ✅ Adjust energy threshold in application settings
- ✅ Ensure no other applications are using the microphone

#### Performance Optimization
**Slow Processing**
- ✅ Use Google Speech Recognition for fastest processing
- ✅ Close other resource-intensive applications
- ✅ Consider using smaller Whisper models (tiny, base) for older hardware

#### File Compatibility
**Vocabulary Loading Errors**
- ✅ Verify CSV encoding (UTF-8 recommended)
- ✅ Check delimiter consistency throughout file
- ✅ Ensure required columns are present
- ✅ Validate ZIP file integrity

### Debug Information
The application provides detailed status messages in the status text area at the bottom of the window.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes following the modular structure
4. Run tests to ensure functionality
5. Submit a pull request

## License

[Specify your license here]

## Acknowledgments

- PyQt5 for the GUI framework
- OpenAI Whisper for speech recognition
- Google Speech Recognition API
- gTTS for text-to-speech
- Community contributors

## Version History

### Recent Enhancements

#### 🔄 Latest Improvements (2026)
- **Modular Architecture**: Reorganized codebase into core/, ui/, and utils/ packages
- **Flashcard Mode**: Added spaced repetition learning with progress tracking
- **Extensible Engine Support**: Prepared architecture for additional ASR/TTS engines
- **Session Storage**: Persistent storage of learning sessions and progress
- **Enhanced Documentation**: Updated all documentation for new structure

#### 🛠 Technical Upgrades
- **Modular Design**: Separated concerns into distinct modules
- **Engine Managers**: ASREngineManager and TTSEngineManager for easy extension
- **Component Library**: Reusable UI components in ui/components.py
- **Storage Utilities**: Centralized data handling in utils/storage.py

#### 📈 Feature Evolution
- **Flashcard System**: Interactive learning with difficulty ratings
- **Progress Tracking**: JSON-based persistent storage of learning data
- **Report Generation**: Text and HTML report export capabilities
- **Enhanced Vocabulary**: Support for grammar column and flexible mapping

For complete version history and detailed changes, consult the git commit log.
