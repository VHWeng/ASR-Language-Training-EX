# ASR Application with Pronunciation Training

An advanced speech recognition application with pronunciation training capabilities, built using Python and PyQt5. This application provides comprehensive language learning tools including vocabulary management, pronunciation practice, flashcard mode with progress tracking, and interactive speech recognition.

## 🚀 Key Features

### 🎯 Core Functionality
- **Speech Recognition**: Multiple engine support (Google Speech Recognition, Whisper) with extensible architecture for additional engines
- **Pronunciation Training**: Interactive pronunciation practice with detailed feedback
- **Flashcard Mode**: Spaced repetition learning with progress tracking and statistics
- **Vocabulary Management**: Load and navigate through vocabulary sets from CSV/ZIP files
- **Image Support**: Display images associated with vocabulary entries
- **Grammar Display**: Show grammatical information alongside vocabulary entries

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
- **Planned**: Multiple TTS engine support (pyttsx3, espeak, cloud services)

### 🎴 Flashcard Mode
- Interactive flashcard learning with spaced repetition
- Difficulty rating system (Again/Hard/Good/Easy)
- Progress tracking and statistics
- Session-based learning with streak counting
- Due item review system

### ⚙️ Configuration
- Customizable column mappings for vocabulary files
- Multiple delimiter support (comma, pipe, tab, semicolon)
- Language selection for speech recognition
- **Planned**: ASR and TTS engine selection
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

3. **Interactive Learning**
   - Navigate through vocabulary items using Previous/Next buttons
   - View definitions, pronunciations, images, and grammatical information
   - Built-in tools enhance entries with IPA pronunciations

4. **Pronunciation Practice**
   - Listen to correct pronunciation via TTS (normal or slow speed)
   - Record your attempt using the "Hold to Record" feature
   - Receive detailed feedback on accuracy and improvement areas

5. **Flashcard Mode**
   - Click the flashcard icon (🎴) to start flashcard mode
   - Practice vocabulary with spaced repetition
   - Rate your knowledge level for each card
   - Track your progress over time

### Advanced Features

#### Customization Options
- Map vocabulary columns to match your file structure
- Choose from multiple delimiter types (comma, pipe, tab, semicolon)
- Select preferred speech recognition engine and language
- **Grammar Column**: Specify the column containing grammar information in your vocabulary files.

#### Image Integration
- Display contextual images for vocabulary items
- Support for common image formats (PNG, JPG, GIF)
- Automatic loading from ZIP archive structures

## Project Structure

```
ASR_Language_Training/
├── main.py                         # Application entry point
├── config.py                       # Configuration dialog and defaults
├── requirements.txt                # Python dependencies
├── README.md                       # Primary documentation
├── HELP.md                         # User guide and help
├── PROJECT_STRUCTURE.md            # Project structure documentation
│
├── core/                           # Core functionality
│   ├── __init__.py
│   ├── recorder.py                 # Audio recording (RecordThread)
│   ├── asr_engines.py              # ASR engines (Google, Whisper + planned)
│   └── tts_engines.py              # TTS engines (gTTS + planned)
│
├── ui/                             # User interface components
│   ├── __init__.py
│   ├── main_window.py              # Main application window (ASRApp)
│   ├── flashcards.py               # Flashcard mode and progress tracking
│   └── components.py               # Custom UI widgets
│
└── utils/                          # Utility modules
    ├── __init__.py
    ├── text_processing.py          # Text normalization, IPA conversion
    └── storage.py                  # CSV/JSON handling, report generation
```

## Vocabulary File Format

### CSV Structure
Default column mapping:
```
Column 1: Reference Text (Word/Phrase)
Column 2: Definition/Translation
Column 3: English Pronunciation
Column 4: IPA Pronunciation
Column 5: Image Description
Column 6: Image Filename
Column 7: Grammar
```

### Example CSV Format
```csv
Word|Definition|English Pron|IPA Pron|Image Desc|Image File|Grammar
hello|A greeting|heh-low|həˈloʊ|Waving hand|hello.png|Noun, common
world|The earth|wurld|wɜrld|Planet Earth|world.png|Noun, singular
αὐτός|he, she, it|af-toss|ˈav.tos|Person pointing|person.png|Pronoun, 3rd person
βλέπω|I see|vleh-po|ˈvle.po|Eye seeing|eye.png|Verb, present tense
```

### ZIP Archive Structure
```
vocabulary_package.zip
├── vocabulary.csv          # Main vocabulary file
└── images/                 # Image directory
    ├── hello.png
    ├── world.png
    ├── αὐτός.png
    └── βλέπω.png
```

## Configuration Options

### Column Mapping
Customize which columns contain what data:
- Reference Text Column
- Definition Column
- English Pronunciation Column
- IPA Pronunciation Column
- Image Description Column
- Image Filename Column
- Grammar Column

### Delimiters
Supported delimiters:
- Comma (,)
- Pipe (|)
- Tab (\t)
- Semicolon (;)

## Planned Upgrades

### Additional ASR Engines
- Vosk (offline)
- Wav2Vec 2.0 (Facebook)
- NVIDIA NeMo
- Azure Speech (cloud)
- AWS Transcribe (cloud)
- IBM Watson (cloud)

### Additional TTS Engines
- pyttsx3 (offline)
- espeak/espeak-ng
- Azure TTS (cloud)
- AWS Polly (cloud)
- IBM Watson TTS (cloud)

### Flashcard Enhancements
- Import/export progress data
- Statistics dashboard
- Learning schedule recommendations
- Card difficulty auto-adjustment

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
