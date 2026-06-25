"""Decode Morse audio back to text.

Self-calibrating: estimates the dot length from the signal itself, so it
decodes any speed without being told the WPM. Designed to round-trip the
output of :func:`morse.synth.synth`, and tolerant enough for clean recordings.
"""

import numpy as np

from .table import DEMORSE


def _envelope(mono: np.ndarray, sr: int, window: float) -> np.ndarray:
    """Sliding-window RMS amplitude — turns a tone into an on/off shape."""
    n = max(1, int(window * sr))
    sq = mono.astype(np.float64) ** 2
    csum = np.cumsum(np.insert(sq, 0, 0.0))
    return np.sqrt((csum[n:] - csum[:-n]) / n)


def _runs(mask: np.ndarray):
    """Yield (is_on, length_in_samples) for each consecutive run in a bool mask."""
    if mask.size == 0:
        return
    edges = np.flatnonzero(np.diff(mask.astype(np.int8))) + 1
    bounds = np.concatenate(([0], edges, [mask.size]))
    for start, end in zip(bounds[:-1], bounds[1:]):
        yield bool(mask[start]), int(end - start)


def decode(
    audio: np.ndarray,
    sr: int,
    *,
    threshold: float = 0.5,
    window: float = 0.005,
) -> str:
    """Decode mono or stereo audio (float, any range) into text.

    ``threshold`` is the fraction of peak amplitude counted as "tone on".
    ``window`` is the RMS smoothing window in seconds. Returns "" if silent.
    """
    # One channel only — averaging stereo with distinct L/R tones (a binaural
    # beat) would cancel to zero mid-mark and shred the on/off shape.
    mono = audio if audio.ndim == 1 else audio[:, 0]
    env = _envelope(mono, sr, window)
    if env.size == 0 or env.max() <= 0:
        return ""

    runs = [(on, length / sr) for on, length in _runs(env > threshold * env.max())]

    # One unit = the shortest mark (a dot). Marks only, since edge/RMS artifacts
    # show up as tiny silences. Fails only for a word with no dots (e.g. "TO"),
    # which is genuinely ambiguous without external timing.
    marks = [dur for on, dur in runs if on]
    if not marks:
        return ""
    unit = min(marks)

    out: list[str] = []
    code = ""

    def flush() -> None:
        nonlocal code
        if code:
            out.append(DEMORSE.get(code, "?"))
            code = ""

    for on, dur in runs:
        if on:
            code += "-" if dur > 2 * unit else "."
        elif dur > 5 * unit:  # word gap (7u)
            flush()
            out.append(" ")
        elif dur > 2 * unit:  # letter gap (3u)
            flush()
        # else intra-character gap (1u): same letter, keep accumulating
    flush()

    return "".join(out).strip()
