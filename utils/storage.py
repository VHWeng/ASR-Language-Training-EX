"""
Storage utilities for ASR Application
Handles CSV/JSON saving and report generation
"""

import json
import csv
import os
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path


def save_text_to_file(text, filename):
    """
    Save text to a file
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(text)
        return True
    except Exception as e:
        print(f"Error saving text: {e}")
        return False


def save_json(data, filename):
    """
    Save data as JSON file
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving JSON: {e}")
        return False


def load_json(filename):
    """
    Load data from JSON file
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return None


def save_csv(data, filename, headers=None):
    """
    Save data as CSV file
    data: list of dictionaries or list of lists
    """
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            if isinstance(data, list) and data:
                if isinstance(data[0], dict):
                    # Data is list of dictionaries
                    fieldnames = headers or list(data[0].keys())
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(data)
                else:
                    # Data is list of lists
                    writer = csv.writer(f)
                    if headers:
                        writer.writerow(headers)
                    writer.writerows(data)
        return True
    except Exception as e:
        print(f"Error saving CSV: {e}")
        return False


def load_csv(filename, delimiter=',', has_header=True, column_mapping=None):
    """
    Load data from CSV file
    Returns list of dictionaries if has_header=True, else list of lists

    Args:
        filename: Path to CSV file
        delimiter: Field delimiter (default: ',')
        has_header: Whether file has header row (default: True)
        column_mapping: Optional dict mapping expected keys to column indices (1-based)
                       e.g., {'reference': 1, 'definition': 2}
    """
    try:
        data = []
        with open(filename, 'r', newline='', encoding='utf-8') as f:
            if has_header:
                reader = csv.DictReader(f, delimiter=delimiter)
                raw_data = list(reader)

                # Apply column mapping if provided
                if column_mapping and raw_data:
                    headers = reader.fieldnames
                    data = []
                    for row in raw_data:
                        mapped_row = {}
                        for key, col_idx in column_mapping.items():
                            # Column indices are 1-based, convert to 0-based
                            if 1 <= col_idx <= len(headers):
                                csv_key = headers[col_idx - 1]
                                mapped_row[key] = row.get(csv_key, '').strip()
                            else:
                                mapped_row[key] = ''
                        # Also keep original data for reference
                        mapped_row['_original'] = dict(row)
                        data.append(mapped_row)
                else:
                    data = raw_data
            else:
                reader = csv.reader(f, delimiter=delimiter)
                raw_data = list(reader)

                # Apply column mapping for non-header CSV
                if column_mapping and raw_data:
                    data = []
                    for row in raw_data:
                        mapped_row = {}
                        for key, col_idx in column_mapping.items():
                            # Column indices are 1-based
                            if 1 <= col_idx <= len(row):
                                mapped_row[key] = row[col_idx - 1].strip()
                            else:
                                mapped_row[key] = ''
                        data.append(mapped_row)
                else:
                    data = raw_data
        return data
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return []


def generate_pronunciation_report(pronunciation_data, config, session_info=None):
    """
    Generate a detailed pronunciation training report
    """
    report = []
    report.append("=" * 60)
    report.append("PRONUNCIATION TRAINING REPORT")
    report.append("=" * 60)
    report.append("")

    # Session info
    if session_info:
        report.append("SESSION INFORMATION")
        report.append("-" * 60)
        for key, value in session_info.items():
            report.append(f"{key}: {value}")
        report.append("")

    # Configuration
    report.append("CONFIGURATION")
    report.append("-" * 60)
    report.append(f"Engine: {config.get('engine', 'N/A')}")
    report.append(f"Language: {config.get('language_name', 'N/A')}")
    report.append(f"Model: {config.get('model', 'N/A')}")
    report.append(f"Threshold: {config.get('pronunciation_threshold', 'N/A')}%")
    report.append("")

    # Pronunciation results
    if pronunciation_data:
        report.append("PRONUNCIATION RESULTS")
        report.append("-" * 60)

        accuracy = pronunciation_data.get('accuracy', 0)
        threshold = config.get('pronunciation_threshold', 80)

        report.append(f"Overall Accuracy: {accuracy:.1f}%")

        if accuracy >= threshold:
            status = "Excellent!"
        elif accuracy >= threshold - 10:
            status = "Good"
        else:
            status = "Needs Improvement"

        report.append(f"Status: {status}")
        report.append("")

        # Reference and recognized
        report.append(f"Reference: {pronunciation_data.get('reference', 'N/A')}")
        report.append(f"Recognized: {pronunciation_data.get('recognized', 'N/A')}")
        report.append("")

        # Word analysis
        word_analysis = pronunciation_data.get('word_analysis', [])
        if word_analysis:
            report.append("WORD-BY-WORD ANALYSIS")
            report.append("-" * 60)

            correct_count = 0
            for i, word in enumerate(word_analysis, 1):
                status = word['status']
                ref = word['reference']
                rec = word['recognized']
                sim = word['similarity']

                if status == "correct":
                    correct_count += 1
                    report.append(f"{i}. [✓] '{ref}' → '{rec}' ({sim:.1f}%)")
                elif status == "incorrect":
                    report.append(f"{i}. [✗] '{ref}' → '{rec}' ({sim:.1f}%) - Mispronounced")
                elif status == "missing":
                    report.append(f"{i}. [✗] '{ref}' → [MISSING]")
                elif status == "extra":
                    report.append(f"{i}. [!] [EXTRA] → '{rec}'")

            report.append("")
            report.append(f"Correct Words: {correct_count}/{len(word_analysis)}")
            report.append(f"Word Accuracy: {(correct_count/len(word_analysis)*100):.1f}%")
            report.append("")

    report.append("=" * 60)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 60)

    return '\n'.join(report)


def save_pronunciation_report(pronunciation_data, config, filename, session_info=None):
    """
    Save pronunciation report to file
    """
    report = generate_pronunciation_report(pronunciation_data, config, session_info)
    return save_text_to_file(report, filename)


def export_vocabulary_to_csv(vocabulary_data, filename):
    """
    Export vocabulary data to CSV file
    """
    if not vocabulary_data:
        return False

    # Get all unique keys from vocabulary entries
    all_keys = set()
    for entry in vocabulary_data:
        all_keys.update(entry.keys())

    # Ensure required columns come first
    field_order = [
        'reference', 'definition', 'english_pronunciation',
        'ipa_pronunciation', 'image_description', 'image_filename', 'grammar'
    ]

    fieldnames = [f for f in field_order if f in all_keys]
    fieldnames += [k for k in sorted(all_keys) if k not in fieldnames and k != 'row_number']

    return save_csv(vocabulary_data, filename, fieldnames)


def create_backup(data, backup_dir='backups'):
    """
    Create a timestamped backup of data
    """
    import os
    from datetime import datetime

    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = os.path.join(backup_dir, f'backup_{timestamp}.json')

    return save_json(data, filename)


def load_vocabulary_from_zip(zip_path, column_mapping=None):
    """
    Load vocabulary data from a ZIP file
    Returns tuple (vocabulary_data, image_paths)

    Args:
        zip_path: Path to ZIP file
        column_mapping: Optional dict mapping expected keys to column indices (1-based)
    """
    vocabulary_data = []
    image_paths = {}

    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_file:
            # Look for CSV files
            csv_files = [f for f in zip_file.namelist() if f.lower().endswith('.csv')]

            if csv_files:
                csv_filename = csv_files[0]
                with zip_file.open(csv_filename) as csv_file_obj:
                    content = csv_file_obj.read().decode('utf-8')

                    # Detect delimiter from content if not using default
                    delimiter = '|'
                    if '\t' in content[:1024]:
                        delimiter = '\t'
                    elif ',' in content[:1024] and '|' not in content[:1024]:
                        delimiter = ','

                    # Create temporary file for processing
                    temp_csv = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8')
                    temp_csv.write(content)
                    temp_csv.close()

                    try:
                        vocabulary_data = load_csv(temp_csv.name, delimiter=delimiter, has_header=True, column_mapping=column_mapping)
                    finally:
                        os.unlink(temp_csv.name)

            # Find images directory
            images_dir = None
            for name in zip_file.namelist():
                if name.lower() == 'images/' or name.lower().endswith('/images/'):
                    images_dir = name
                    break

            if images_dir:
                # Collect image paths
                for name in zip_file.namelist():
                    if name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                        basename = Path(name).stem
                        image_paths[basename] = name

    except Exception as e:
        print(f"Error loading ZIP: {e}")

    return vocabulary_data, image_paths


class SessionStorage:
    """
    Manages session data storage and retrieval
    """

    def __init__(self, storage_path='session_data.json'):
        self.storage_path = storage_path
        self.sessions = []
        self.load()

    def load(self):
        """Load sessions from storage"""
        data = load_json(self.storage_path)
        if data:
            self.sessions = data.get('sessions', [])

    def save(self):
        """Save sessions to storage"""
        data = {
            'last_saved': datetime.now().isoformat(),
            'sessions': self.sessions
        }
        save_json(data, self.storage_path)

    def add_session(self, session_data):
        """Add a new session"""
        session = {
            'timestamp': datetime.now().isoformat(),
            'data': session_data
        }
        self.sessions.append(session)
        self.save()

    def get_sessions(self, limit=None):
        """Get all sessions or limited number"""
        if limit:
            return self.sessions[-limit:]
        return self.sessions

    def get_statistics(self):
        """Get overall statistics from all sessions"""
        if not self.sessions:
            return {}

        total_sessions = len(self.sessions)
        total_attempts = sum(s['data'].get('attempts', 0) for s in self.sessions)
        total_correct = sum(s['data'].get('correct', 0) for s in self.sessions)

        return {
            'total_sessions': total_sessions,
            'total_attempts': total_attempts,
            'total_correct': total_correct,
            'average_accuracy': (total_correct / total_attempts * 100) if total_attempts > 0 else 0
        }

    def clear(self):
        """Clear all sessions"""
        self.sessions = []
        self.save()


class ReportGenerator:
    """
    Generates various reports from application data
    """

    def __init__(self, config):
        self.config = config

    def generate_html_report(self, pronunciation_data, session_info=None):
        """Generate an HTML formatted report"""
        # Simple HTML generation
        html = []
        html.append("<html><head>")
        html.append("<style>")
        html.append("body { font-family: Arial, sans-serif; margin: 40px; }")
        html.append("h1 { color: #333; }")
        html.append(".correct { color: green; }")
        html.append(".incorrect { color: red; }")
        html.append(".summary { background: #f0f0f0; padding: 20px; margin: 20px 0; }")
        html.append("</style>")
        html.append("</head><body>")
        html.append("<h1>Pronunciation Training Report</h1>")

        if pronunciation_data:
            accuracy = pronunciation_data.get('accuracy', 0)
            html.append(f"<div class='summary'>")
            html.append(f"<h2>Accuracy: {accuracy:.1f}%</h2>")
            html.append("</div>")

        html.append("</body></html>")

        return '\n'.join(html)
