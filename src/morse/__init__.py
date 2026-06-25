"""Morse code audio: synthesize text to tones and decode tones back to text."""

from .decode import decode
from .loader import read_audio
from .output import write_mp3, write_wav
from .synth import build_envelope, synth
from .table import DEMORSE, MORSE
from .weather import coordinates, latest_reading, report, weather_report

__all__ = [
    "MORSE",
    "DEMORSE",
    "synth",
    "build_envelope",
    "decode",
    "read_audio",
    "write_wav",
    "write_mp3",
    "latest_reading",
    "report",
    "coordinates",
    "weather_report",
]
