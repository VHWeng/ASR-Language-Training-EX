# ASR Application Help Guide

## 📖 Table of Contents
- [Getting Started](#getting-started)
- [Core Features](#core-features)
- [Vocabulary Management](#vocabulary-management)
- [Pronunciation Training](#pronunciation-training)
- [Flashcard Mode](#flashcard-mode)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

## 🚀 Getting Started

### Initial Setup
1. **Launch the Application**
   ```bash
   python main.py
   ```

2. **First-Time Configuration** (Optional)
    - Click the gear icon ⚙ to access settings
    - Configure your preferred speech recognition engine
    - Set your default language
    - Configure TTS engine and voice selection (gTTS or edge-tts)

3. **Load Your First Vocabulary**
   - Click "📁 Load Vocabulary"
   - Select a CSV, TXT, or ZIP file
   - Start exploring your vocabulary items

### System Requirements
- **Python**: 3.10 or higher recommended
- **FFmpeg**: Required for audio processing
- **Microphone**: For recording practice sessions
- **Speakers/Headphones**: For audio playback

## 🎯 Core Features

### Speech Recognition Engines
The application supports multiple speech recognition engines:
- **Google Speech Recognition**: Cloud-based, high accuracy
- **Whisper**: OpenAI's open-source model, excellent accuracy, requires more processing power
- **Qwen3-ASR**: New engine support (2026), enhanced accuracy and language support

**Planned Engines** (configurable in future releases):
- Vosk: Offline-capable, good for privacy
- Azure Speech, AWS Transcribe, IBM Watson: Cloud-based enterprise options

### Audio Controls
- **Record Button**: Hold to record, release to stop
- **Playback Controls**: Normal and slow-speed TTS
- **ASR Conversion**: Transcribe recorded audio with accuracy scoring

### Navigation
- **Previous/Next Buttons**: Move between vocabulary items
- **Progress Indicator**: Shows current position
- **Flashcard Mode**: Access via the 🎴 button in the toolbar

## 📚 Vocabulary Management

### Supported File Formats
1. **CSV/TXT Files**
   - Customizable column mappings
   - Multiple delimiter support (comma, pipe, tab, semicolon)
   - UTF-8 encoding recommended

2. **ZIP Archives**
   - Vocabulary file in root directory
   - Images in "images/" subdirectory
   - Automatic extraction and organization

### Column Structure
Default mapping (customizable):
```
Column 1: Reference Text (Word/Phrase)
Column 2: Definition/Translation
Column 3: English Pronunciation
Column 4: IPA Pronunciation
Column 5: Image Description
Column 6: Image Filename
Column 7: Grammar
```

### Example Vocabulary File
```csv
Word|Definition|English Pron|IPA Pron|Image Desc|Image File|Grammar
hello|A greeting|heh-low|həˈloʊ|Waving hand|hello.png|Noun, common
world|The earth|wurld|wɜrld|Planet Earth|world.png|Noun, singular
αὐτός|he, she, it|af-toss|ˈav.tos|Person pointing|person.png|Pronoun, 3rd person
βλέπω|I see|vleh-po|ˈvle.po|Eye seeing|eye.png|Verb, present tense
```

### Loading Vocabulary
1. Click "📁 Load Vocabulary"
2. Select your file (CSV, TXT, or ZIP)
3. Configure column mappings if needed (in Configuration dialog)
4. The application will automatically enhance entries with built-in IPA conversion

## 🔊 Pronunciation Training

### Grammar Display
- **Show Grammar Checkbox**: Toggle the visibility of the "Grammar" text box
- **Grammar Text Box**: Displays grammatical information related to the reference text, loaded from your vocabulary file

### Basic Workflow
1. **Select Vocabulary Item**
   - Browse using Previous/Next buttons
   - Or enter text directly in Reference Text field

2. **Listen to Model Pronunciation**
   - Click "🔊 Play TTS" for normal speed
   - Click "🐢 Slow TTS" for slower playback
   - Pay attention to stress and intonation

3. **Record Your Attempt**
   - Hold the record button to start
   - Release to stop recording
   - Speak clearly at a moderate pace

4. **Get Feedback**
   - Click "🔄 ASR Convert" to analyze your pronunciation
   - Review accuracy score and detailed feedback
   - Identify specific areas for improvement

### Feedback Components
- **Overall Accuracy Score**: Percentage match to reference
- **Word-by-Word Analysis**: Individual word accuracy
- **Mispronounced Words**: Highlighted problematic areas
- **Missing/Extra Words**: Content completeness check
- **Personalized Recommendations**: Targeted improvement suggestions
- **Color-Coded Results**:
  - 🟢 Green: Excellent (90%+ accuracy)
  - 🟡 Yellow: Good (70-89% accuracy)
  - 🔴 Red: Needs Improvement (<70% accuracy)

### Practice Tips
- **Environment**: Find a quiet space for recording
- **Technique**: Speak clearly and at moderate pace
- **Consistency**: Practice regularly for best results
- **Focus**: Work on one challenging sound/word at a time
- **Patience**: Improvement takes time and repetition

## 🎴 Flashcard Mode

### Starting Flashcard Mode
1. Load a vocabulary file first
2. Click the 🎴 (flashcard) icon in the toolbar
3. The flashcard dialog will open with your vocabulary

### Using Flashcards
1. **Card Display**: Cards show either the word or definition first (selectable)
2. **Flip Card**: Click "Flip" or press Space to reveal the other side
3. **Listen**: Click 🔊 to hear the pronunciation
   - **Front**: Play and Slow buttons for TTS
   - **Back**: Additional Play and Slow buttons under pronunciation for review
4. **Practice**: Click 🎤 to record your pronunciation
5. **View Images**: If vocabulary items include images, they will be displayed on the card:
   - Images are shown on the front of the card when displaying the word
   - Images appear automatically when available
   - Supported formats: PNG, JPG, JPEG, GIF
   - If a vocabulary image is missing or unavailable, the application logo (Data/Logo.png) is displayed as a fallback
   - Images are displayed at appropriate size for the card layout
6. **Rate Difficulty**: After flipping, rate how well you knew the card:
   - **Again**: Didn't know it - will appear again soon
   - **Hard**: Difficult - shortened review interval
   - **Good**: Knew it - normal review interval
   - **Easy**: Very easy - extended review interval

### Progress Tracking
- **Session Stats**: Shows current accuracy and streak during sessions
- **Persistent Storage**: Progress is saved automatically to `flashcard_progress.json`
- **Due Items**: Cards that need review are prioritized

### Flashcard Settings
- **Show First**: Choose whether to show word or definition first
- **Shuffle**: Randomize card order
- **Repeat Incorrect**: Automatically repeat cards rated "Again"

### Viewing Statistics
Click the 📊 (statistics) icon to view:
- Total items mastered
- Items currently learning
- Overall accuracy percentage
- Cards due for review

## 🔊 Text-to-Speech (TTS) Configuration

The application supports two TTS engines:

- **gTTS (Google Text-to-Speech)**: Default, works out of the box, uses Google's cloud service
- **Edge TTS (Microsoft Edge)**: Higher quality voices, requires `edge-tts` Python package

### Selecting a TTS Engine

1. Click the gear icon ⚙ to open Configuration
2. In the "Text-to-Speech (TTS)" section:
   - Choose your preferred engine from the dropdown: `gTTS` or `edge-tts`
3. If you select `edge-tts`:
   - A "Voice" dropdown will appear
   - Choose from available Microsoft Edge voices (e.g., `en-US-BrianMultilingualNeural`)
   - The voice list loads automatically when you select edge-tts
4. Click "OK" to save settings

### Default Settings

- **Default Engine**: gTTS (no additional installation required)
- **Default Edge TTS Voice**: `en-US-BrianMultilingualNeural` (English, male, multilingual)

### Installation

To use Edge TTS, install the package:

```bash
pip install edge-tts
```

The package is included in `requirements.txt`, so it will be installed with:

```bash
pip install -r requirements.txt
```

Note: Edge TTS voices are provided by Microsoft and require internet connectivity.

### Using TTS in the Application

- **Normal Speed**: Click `🔊 Play TTS` to hear the reference text at normal speed
- **Slow Speed**: Click `🐢 Slow TTS` for slower articulation (helpful for learning)
- **Flashcard Mode**: TTS buttons appear on the back of cards for review after revealing the answer

### Configuration Presets

The Configuration dialog now includes a **Presets** section with three buttons:

- **Save Configuration...**: Saves the current configuration to a JSON file in the `Data/` directory.
- **Load Configuration...**: Loads configuration from a previously saved JSON file.
- **Restore Defaults**: Resets all settings to their factory defaults.

Presets store all configuration options, including ASR engine, language, model, sample rate, energy threshold, pronunciation threshold, column mappings, TTS engine/voice, and polytonic Greek normalization. You can create multiple presets for different use cases (e.g., one for Greek with edge-tts, another for English with gTTS).

To use presets:
1. Open the Configuration dialog (gear icon).
2. Adjust settings as desired.
3. Click **Save Configuration...**, choose a filename, and save.
4. Later, click **Load Configuration...** and select the preset file to restore.
5. Use **Restore Defaults** to revert to the original defaults.

Presets are saved as human‑readable JSON files in the `Data/` directory and can be backed up or shared.

### Polytonic Greek Normalization

When using **edge-tts** with **Greek language (el)** or a **Multilingual** voice, the application can automatically normalize polytonic (ancient/ecclesiastical) Greek text to monotonic for better pronunciation.

- **Purpose**: Some TTS engines do not handle polytonic diacritics (breathing marks, multiple accents). Normalization ensures clearer speech.
- **Enable/Disable**: In Configuration ⚙ → TTS section, check/uncheck "Normalize polytonic Greek text for edge-tts". Enabled by default.
- **Scope**: Only applies to edge-tts engine when the language is Greek (el-GR) or the selected voice name contains "Multilingual".
- **Example**:
  - Polytonic: `ἐν ἀρχῇ ἦν`
  - Normalized: `εν αρχη ην`
- **Manual override**: Uncheck the box to play original polytonic text (if your TTS supports it).

## 🔧 Troubleshooting

### Common Issues

#### Audio Problems
**Microphone Not Working**
- Check microphone permissions in system settings
- Ensure no other applications are using the microphone
- Test microphone in system audio settings
- Adjust energy threshold in application settings

**Poor Recording Quality**
- Move closer to microphone
- Reduce background noise
- Check microphone sensitivity settings
- Ensure proper microphone placement

**TTS Not Playing**
- Check system volume
- Verify internet connection (for gTTS)
- Ensure `edge-tts` package is installed if using Edge TTS: `pip install edge-tts`
- Check pygame installation
- For Edge TTS: ensure you have selected a valid voice in configuration
- First-time voice loading may take a few seconds (requires internet)

#### File Loading Problems
**Vocabulary Not Loading**
- Verify file format and encoding (UTF-8 recommended)
- Check delimiter consistency throughout file
- Ensure required columns are present
- Validate ZIP file integrity

**Images Not Displaying**
- Confirm images are in "images/" subdirectory for ZIP files
- Check supported formats (.png, .jpg, .jpeg, .gif)
- Verify column 6 contains correct relative filenames
- Check file permissions and path encoding
- Note: If vocabulary images are missing, the application logo (Data/Logo.png) will be displayed as a fallback

#### Flashcard Issues
**Progress Not Saving**
- Check write permissions in application directory
- Verify disk space availability
- Look for `flashcard_progress.json` file

**Cards Not Showing**
- Ensure vocabulary file is loaded first
- Check that vocabulary has items with reference text

### Debug Information
The application provides detailed status messages:
- Bottom status text area shows real-time information
- Error messages include specific troubleshooting guidance
- Progress indicators for long-running operations
- Detailed logs available through console output

## ❓ FAQ

### General Questions

**Q: What languages are supported?**
A: The application supports multiple languages including Greek (default), English, Spanish, French, German, Italian, Portuguese, Russian, Chinese, Japanese, Korean, and Arabic.

**Q: Do I need internet connection?**
A: Basic functionality works offline. Internet is only required for Google Speech Recognition and gTTS. Whisper can work offline after model download.

**Q: How much RAM/CPU does it need?**
A: Minimum 4GB RAM recommended. Whisper processing benefits from more powerful CPUs or GPUs.

### Vocabulary Management

**Q: Can I create my own vocabulary files?**
A: Yes! Create CSV files with your desired content following the column structure outlined above.

**Q: Can I add images to my vocabulary?**
A: Yes! Images can be included in your vocabulary files. For CSV/TXT files, add image filenames in column 6. For ZIP files, place images in an "images/" subdirectory and reference them in column 6.

**Q: What image formats are supported?**
A: PNG, JPG/JPEG, and GIF formats are supported for vocabulary images.

**Q: Do images appear in flashcard mode?**
A: Yes, images are automatically displayed on the front of flashcards when available. Images appear when the card shows the word/definition and provide visual context for learning.

**Q: How do I organize images in ZIP files?**
A: Place your CSV file in the root, and all images in an "images/" subdirectory. The application will automatically detect and display images when showing vocabulary items in flashcard mode.

### Audio and Pronunciation

**Q: Why is my accuracy score low?**
A: Common reasons include background noise, unclear pronunciation, speaking too fast, or accent differences. Practice in a quiet environment and speak clearly.

**Q: Can I adjust sensitivity settings?**
A: Yes, you can adjust the energy threshold and other audio settings in the configuration menu.

**Q: How do I improve my pronunciation?**
A: Regular practice, listening carefully to model pronunciations, focusing on problem areas, and using the slow playback feature.

### Flashcard Mode

**Q: Is my progress saved?**
A: Yes, flashcard progress is automatically saved to `flashcard_progress.json` in the application directory.

**Q: Can I reset my progress?**
A: Delete the `flashcard_progress.json` file to reset all flashcard progress.

**Q: How does spaced repetition work?**
A: Cards rated "Easy" appear less frequently, while cards rated "Again" appear sooner. The algorithm adjusts review intervals based on your performance.

**Q: Can I export my flashcard data?**
A: Currently, progress is stored locally. Export functionality is planned for future releases.

**Q: How do I know if a vocabulary item has an image?**
A: When loading vocabulary, items with images will be indicated in the status area. In flashcard mode, images will automatically appear when the card displays the word or definition. If an image is missing, the application logo is shown instead.

**Q: Are there TTS controls on both sides of the flashcard?**
A: Yes! The front of the card has Play and Slow TTS buttons below the word. The back of the card also has Play and Slow TTS buttons directly under the pronunciation label, allowing you to replay the pronunciation after seeing the definition.

## 📞 Support

For additional help:
1. Check the detailed status messages in the application
2. Review the troubleshooting section above
3. Examine console output for error details
4. Consult the README.md for technical documentation
5. Check git commit history for recent changes and fixes

---

*Last updated: February 2026*
*Version: 3.0.0*
