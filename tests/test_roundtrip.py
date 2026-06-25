"""Round-trip check: synth(text) -> decode -> text. Run with pytest or directly."""

from morse import decode, synth

# Distinct L/R freqs (binaural beat) — the real CLI default; exercises decoding
# a single channel rather than the cancelling stereo mean.
PARAMS = dict(sr=48000, unit=0.06, attack=0.008, release=0.008, vol=0.5, left_freq=600, right_freq=615)


def _roundtrip(message: str) -> str:
    audio = synth(message, **PARAMS)
    return decode(audio, PARAMS["sr"])


def test_roundtrip():
    for msg in ["SOS", "HELLO WORLD", "THE QUICK BROWN FOX", "ABC 123", "OVER OVER"]:
        assert _roundtrip(msg) == msg, f"{msg!r} -> {_roundtrip(msg)!r}"


def test_silence_decodes_empty():
    import numpy as np

    assert decode(np.zeros((1000, 2), dtype=np.float32), 48000) == ""


if __name__ == "__main__":
    test_roundtrip()
    test_silence_decodes_empty()
    print("ok")
