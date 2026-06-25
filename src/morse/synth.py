"""Synthesize Morse code audio from text."""

import numpy as np

from .table import MORSE


def build_envelope(
    message: str,
    sr: int,
    unit: float,
    attack: float,
    release: float,
) -> np.ndarray:
    """Build a 0..1 amplitude envelope for ``message`` at ``unit`` seconds/dot.

    Standard Morse timing: dash = 3u, intra-character gap = 1u, letter gap = 3u,
    word gap = 7u, plus a 14u tail. ``attack``/``release`` are per-mark fade
    ramps (seconds) that suppress clicks.
    """
    dot = unit
    dash = 3 * unit
    gap = unit
    letter_gap = 3 * unit
    word_gap = 7 * unit
    message_gap = 14 * unit

    words = message.upper().split()
    # Positive value = tone for that many seconds, negative = silence.
    symbols: list[float] = []

    for word_index, word in enumerate(words):
        for letter_index, char in enumerate(word):
            code = MORSE.get(char)
            if not code:
                continue

            for i, mark in enumerate(code):
                symbols.append(dash if mark == "-" else dot)
                if i < len(code) - 1:
                    symbols.append(-gap)

            if letter_index < len(word) - 1:
                symbols.append(-letter_gap)

        if word_index < len(words) - 1:
            symbols.append(-word_gap)

    symbols.append(-message_gap)

    total_duration = sum(abs(x) for x in symbols)
    env = np.zeros(int(total_duration * sr), dtype=np.float32)

    pos = 0
    for item in symbols:
        n = int(abs(item) * sr)

        if item > 0:
            env[pos : pos + n] = 1.0

            a = min(int(attack * sr), n // 2)
            r = min(int(release * sr), n // 2)

            if a > 0:
                env[pos : pos + a] *= np.linspace(0, 1, a, endpoint=False)
            if r > 0:
                env[pos + n - r : pos + n] *= np.linspace(1, 0, r, endpoint=False)

        pos += n

    return env


def synth(
    message: str,
    sr: int,
    unit: float,
    attack: float,
    release: float,
    vol: float,
    left_freq: float,
    right_freq: float,
) -> np.ndarray:
    """Render ``message`` to stereo float32 audio shaped (samples, 2).

    Distinct left/right frequencies produce a binaural beat of
    ``abs(left_freq - right_freq)`` Hz.
    """
    env = build_envelope(message, sr, unit, attack, release)
    t = np.arange(len(env), dtype=np.float32) / sr

    left = np.sin(2 * np.pi * left_freq * t) * env * vol
    right = np.sin(2 * np.pi * right_freq * t) * env * vol

    return np.column_stack((left, right)).astype(np.float32)
