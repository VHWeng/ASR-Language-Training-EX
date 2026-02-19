"""
Text processing utilities for ASR Application
Includes text normalization, IPA conversion, and AI response cleaning
"""

import re


def normalize_text(text):
    """
    Normalize text for comparison
    Removes punctuation, converts to lowercase, normalizes whitespace
    """
    text = text.lower().strip()
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
    return text


def clean_ai_response(response):
    """
    Clean AI response by removing markdown, extra formatting, noise, and blank lines
    """
    if not response:
        return ""

    # Remove common markdown artifacts
    cleaned = response.strip()
    cleaned = cleaned.replace("```", "")  # Remove code blocks
    cleaned = cleaned.replace("**", "")   # Remove bold markers
    cleaned = cleaned.replace("*", "")  # Remove italic markers

    # Remove blank lines and normalize whitespace
    lines = [line.strip() for line in cleaned.split('\n') if line.strip()]
    cleaned = '\n'.join(lines)

    # Remove common prefixes/suffixes for single-line responses
    if '\n' not in cleaned:
        for line in lines:
            if line and not line.lower().startswith(('note:', 'tip:', 'hint:')):
                cleaned = line
                break

    return cleaned.strip()


def clean_display_text(text):
    """
    Clean text for display by removing blank lines and normalizing whitespace
    """
    if not text:
        return ""

    # Split into lines, strip each line, and filter out empty lines
    lines = [line.strip() for line in text.split('\n') if line.strip()]

    # Join with single newlines
    cleaned = '\n'.join(lines)

    return cleaned.strip()


def text_to_ipa(text):
    """
    Convert English text to IPA pronunciation
    This is a simplified implementation
    """
    return text_to_ipa_modern(text)


def text_to_ipa_modern(text):
    """
    Convert English text to modern, accurate IPA pronunciation
    Uses a mapping-based approach
    """
    # Enhanced English to IPA mapping with better accuracy
    ipa_map = {
        # Vowels - short
        'a': 'æ', 'e': 'ɛ', 'i': 'ɪ', 'o': 'ɒ', 'u': 'ʌ',
        # Vowels - long
        'aa': 'ɑː', 'ee': 'iː', 'ii': 'aɪ', 'oo': 'uː', 'uu': 'uː',
        # Consonants
        'b': 'b', 'c': 'k', 'd': 'd', 'f': 'f', 'g': 'ɡ',
        'h': 'h', 'j': 'dʒ', 'k': 'k', 'l': 'l', 'm': 'm',
        'n': 'n', 'p': 'p', 'q': 'k', 'r': 'ɹ', 's': 's',
        't': 't', 'v': 'v', 'w': 'w', 'x': 'ks', 'y': 'j', 'z': 'z',
        # Common digraphs and trigraphs
        'th': 'θ', 'ch': 'tʃ', 'sh': 'ʃ', 'ph': 'f', 'wh': 'ʍ',
        'ck': 'k', 'qu': 'kw', 'ng': 'ŋ', 'gh': 'ɡ', 'sc': 'sk',
        'sch': 'sk', 'scr': 'skɹ', 'shr': 'ʃɹ', 'thr': 'θɹ',
        # Vowel combinations - diphthongs
        'ai': 'eɪ', 'ay': 'eɪ', 'au': 'ɔː', 'aw': 'ɔː',
        'ea': 'iː', 'ee': 'iː', 'ei': 'aɪ', 'ey': 'aɪ',
        'ie': 'aɪ', 'oa': 'əʊ', 'oo': 'uː', 'ou': 'aʊ', 'ow': 'aʊ',
        'ue': 'uː', 'ui': 'aɪ', 'ew': 'juː', 'oi': 'ɔɪ', 'oy': 'ɔɪ',
        'ar': 'ɑː', 'er': 'ɜː', 'ir': 'ɜː', 'or': 'ɔː', 'ur': 'ɜː',
        # Silent letters and special cases
        'kn': 'n', 'gn': 'n', 'wr': 'ɹ', 'mb': 'm',
        # Common words and phrases
        'the': 'ðə', 'and': 'ənd', 'of': 'əv', 'to': 'tu', 'in': 'ɪn',
        'is': 'ɪz', 'it': 'ɪt', 'you': 'juː', 'he': 'hiː', 'she': 'ʃiː',
        'we': 'wiː', 'they': 'ðeɪ', 'are': 'ɑː', 'was': 'wɒz', 'were': 'wɜː',
        'have': 'hæv', 'has': 'hæz', 'had': 'hæd', 'do': 'duː', 'does': 'dʌz',
        'did': 'dɪd', 'will': 'wɪl', 'would': 'wʊd', 'can': 'kæn', 'could': 'kʊd',
        'shall': 'ʃæl', 'should': 'ʃʊd', 'may': 'meɪ', 'might': 'maɪt',
        'must': 'mʌst', 'ought': 'ɔːt', 'need': 'niːd'
    }

    # Preprocessing
    text = text.lower().strip()
    words = text.split()
    ipa_words = []

    for word in words:
        # Remove punctuation for processing but keep it for output
        clean_word = ''.join(c for c in word if c.isalnum())
        punctuation = ''.join(c for c in word if not c.isalnum())

        if not clean_word:
            if punctuation:
                ipa_words.append(punctuation)
            continue

        # Convert the clean word
        ipa_word = ""
        i = 0

        while i < len(clean_word):
            matched = False

            # Check for longest possible matches first
            # Check trigraphs
            if i <= len(clean_word) - 3:
                trigraph = clean_word[i:i+3]
                if trigraph in ipa_map:
                    ipa_word += ipa_map[trigraph]
                    i += 3
                    matched = True
                    continue

            # Check digraphs
            if i <= len(clean_word) - 2:
                digraph = clean_word[i:i+2]
                if digraph in ipa_map:
                    ipa_word += ipa_map[digraph]
                    i += 2
                    matched = True
                    continue

            # Check single characters
            char = clean_word[i]
            if char in ipa_map:
                ipa_word += ipa_map[char]
            elif char.isalpha():
                # Unknown letters - use closest approximation
                ipa_word += char

            i += 1

        # Add back punctuation
        if punctuation:
            ipa_word += punctuation

        ipa_words.append(ipa_word)

    return ' '.join(ipa_words)


def split_into_sentences(text):
    """
    Split text into sentences
    """
    # Simple sentence splitting
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if s.strip()]


def count_syllables(word):
    """
    Estimate syllable count for a word
    Simple heuristic based on vowel groups
    """
    word = word.lower()
    vowels = 'aeiouy'
    count = 0
    prev_was_vowel = False

    for char in word:
        if char in vowels:
            if not prev_was_vowel:
                count += 1
            prev_was_vowel = True
        else:
            prev_was_vowel = False

    # Silent 'e' at the end
    if word.endswith('e') and count > 1:
        count -= 1

    return max(1, count)


def calculate_similarity(text1, text2):
    """
    Calculate similarity between two texts using SequenceMatcher
    Returns a value between 0 and 1
    """
    from difflib import SequenceMatcher
    return SequenceMatcher(None, normalize_text(text1), normalize_text(text2)).ratio()


def highlight_differences(reference, recognized):
    """
    Highlight differences between reference and recognized text
    Returns HTML formatted string
    """
    from difflib import SequenceMatcher

    ref_words = normalize_text(reference).split()
    rec_words = normalize_text(recognized).split()

    matcher = SequenceMatcher(None, ref_words, rec_words)

    result = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            result.append(' '.join(ref_words[i1:i2]))
        elif tag == 'replace':
            result.append(f'<span style="color: orange;">{" ".join(rec_words[j1:j2])}</span>')
        elif tag == 'delete':
            result.append(f'<span style="color: red;">[{" ".join(ref_words[i1:i2])}]</span>')
        elif tag == 'insert':
            result.append(f'<span style="color: blue;">{" ".join(rec_words[j1:j2])}</span>')

    return ' '.join(result)


def format_timestamp(seconds):
    """
    Format seconds to MM:SS format
    """
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def truncate_text(text, max_length=50, suffix="..."):
    """
    Truncate text to max_length characters
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


class TextProcessor:
    """
    Class for processing text with various transformations
    """

    def __init__(self):
        self.history = []

    def process(self, text, operations):
        """
        Process text with a list of operations
        operations: list of function names to apply
        """
        result = text
        for operation in operations:
            if operation == 'normalize':
                result = normalize_text(result)
            elif operation == 'clean_ai':
                result = clean_ai_response(result)
            elif operation == 'clean_display':
                result = clean_display_text(result)
            elif operation == 'to_ipa':
                result = text_to_ipa(result)
            elif operation == 'sentences':
                result = split_into_sentences(result)
            self.history.append((operation, result))
        return result
