"""
Audio recorder module
Handles audio input and recording
"""

import tempfile
import queue
import numpy as np
import sounddevice as sd
import soundfile as sf
from PyQt5.QtCore import QThread, pyqtSignal


class RecordThread(QThread):
    """Thread for recording audio from microphone"""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, sample_rate=16000):
        super().__init__()
        self.sample_rate = sample_rate
        self.filename = None
        self.is_recording = True
        self.audio_queue = queue.Queue()
        self.recording_thread = None

    def run(self):
        try:
            # Initialize recording buffer
            recording_buffer = []

            # Callback function to capture audio chunks
            def audio_callback(indata, frames, time, status):
                if self.is_recording:
                    recording_buffer.append(indata.copy())

            # Start the stream
            stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype='float32',
                callback=audio_callback
            )

            stream.start()

            # Keep recording until flag is changed
            while self.is_recording:
                sd.sleep(100)  # Sleep for 100ms to avoid busy waiting

            # Stop the stream
            stream.stop()
            stream.close()

            # Combine all recorded chunks
            if recording_buffer:
                full_recording = np.concatenate(recording_buffer, axis=0)

                self.filename = tempfile.mktemp(suffix='.wav')
                sf.write(self.filename, full_recording, self.sample_rate)
                self.finished.emit(self.filename)
            else:
                self.error.emit("No audio recorded")

        except Exception as e:
            self.error.emit(str(e))

    def stop_recording(self):
        """Stop the recording"""
        self.is_recording = False
