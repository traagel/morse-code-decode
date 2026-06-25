"""Read audio files into normalized float arrays for decoding."""

import subprocess
import wave

import numpy as np


def _read_wav(path: str) -> tuple[np.ndarray, int]:
    with wave.open(path, "rb") as f:
        channels = f.getnchannels()
        width = f.getsampwidth()
        sr = f.getframerate()
        raw = f.readframes(f.getnframes())

    if width != 2:
        raise ValueError(f"unsupported WAV sample width: {width * 8}-bit (need 16-bit)")

    data = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    if channels > 1:
        data = data.reshape(-1, channels)
    return data, sr


def _read_mp3(path: str, sr: int = 48000) -> tuple[np.ndarray, int]:
    # Keep both channels: a mono downmix cancels a binaural-beat signal to zero.
    cmd = ["ffmpeg", "-v", "error", "-i", path, "-f", "s16le", "-ar", str(sr), "-ac", "2", "-"]
    try:
        raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    except FileNotFoundError:
        raise SystemExit("ffmpeg not found — needed to read .mp3 input")
    data = np.frombuffer(raw, dtype=np.int16).astype(np.float32).reshape(-1, 2) / 32768.0
    return data, sr


def read_audio(path: str) -> tuple[np.ndarray, int]:
    """Return (samples in -1..1, sample rate). Dispatches on file extension."""
    if path.lower().endswith(".mp3"):
        return _read_mp3(path)
    return _read_wav(path)
