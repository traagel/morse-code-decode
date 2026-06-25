"""Write audio to WAV (stdlib) or MP3 (via ffmpeg)."""

import subprocess
import wave

import numpy as np


def to_pcm16(audio: np.ndarray) -> np.ndarray:
    """Clamp float audio to -1..1 and convert to signed 16-bit PCM."""
    return (np.clip(audio, -1, 1) * 32767).astype(np.int16)


def write_wav(path: str, audio: np.ndarray, sr: int) -> None:
    """Write stereo float audio to a 16-bit WAV file."""
    pcm = to_pcm16(audio)

    with wave.open(path, "wb") as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(sr)
        f.writeframes(pcm.tobytes())


def write_mp3(path: str, audio: np.ndarray, sr: int, bitrate: str) -> None:
    """Encode stereo float audio to MP3 by piping PCM through ffmpeg."""
    pcm = to_pcm16(audio)

    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "s16le",
        "-ar",
        str(sr),
        "-ac",
        "2",
        "-i",
        "-",
        "-codec:a",
        "libmp3lame",
        "-b:a",
        bitrate,
        path,
    ]

    try:
        subprocess.run(cmd, input=pcm.tobytes(), check=True)
    except FileNotFoundError:
        raise SystemExit("ffmpeg not found — needed to write .mp3 output")
