"""Round-trip check: synth(text) -> decode -> text. Run with pytest or directly."""

from morse import decode, synth
from morse.table import MORSE
from morse.weather import _cardinal, coordinates, report

# Distinct L/R freqs (binaural beat) — the real CLI default; exercises decoding
# a single channel rather than the cancelling stereo mean.
PARAMS = dict(sr=48000, unit=0.06, attack=0.008, release=0.008, vol=0.5, left_freq=600, right_freq=615)


def _roundtrip(message: str) -> str:
    audio = synth(message, **PARAMS)
    return decode(audio, PARAMS["sr"])


def test_roundtrip():
    for msg in ["SOS", "HELLO WORLD", "THE QUICK BROWN FOX", "ABC 123", "OVER OVER", "LAT 58.36, LON 26.69"]:
        assert _roundtrip(msg) == msg, f"{msg!r} -> {_roundtrip(msg)!r}"


def test_silence_decodes_empty():
    import numpy as np

    assert decode(np.zeros((1000, 2), dtype=np.float32), 48000) == ""


def test_cardinal():
    assert [_cardinal(d) for d in (0, 45, 90, 135, 180, 225, 270, 315)] == \
        ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    assert _cardinal(359) == "N"  # wraps


def test_report_is_morse_safe():
    reading = {
        "time": "2026-06-25 00:55:00",
        "temp": -2.6, "humidity": 99.0, "pressure": 1012.4,
        "wind": 1.7, "direction": 301.0, "precip": 0.3,
    }
    msg = report(reading)
    assert msg == "WX TARTU 0055Z TEMP MINUS 3 HUM 99 PRES 1012 WIND 2 MS NW RAIN", msg
    # Every non-space char must be encodable.
    assert all(c in MORSE for c in msg if c != " ")


def test_coordinates():
    msg = coordinates(58.366449, 26.690668)
    assert msg == "LAT 58.3664 N LON 26.6907 E", msg
    assert coordinates(-33.8, -70.6) == "LAT 33.8000 S LON 70.6000 W"
    assert all(c in MORSE for c in msg if c != " ")


if __name__ == "__main__":
    test_roundtrip()
    test_silence_decodes_empty()
    test_cardinal()
    test_report_is_morse_safe()
    test_coordinates()
    print("ok")
