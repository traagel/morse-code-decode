"""Command-line interface: encode text, decode audio, broadcast weather."""

import argparse
import sys

import numpy as np

from .decode import decode
from .loader import read_audio
from .output import write_mp3, write_wav
from .playback import play_loop
from .synth import synth
from .weather import weather_report

_ENCODE = "encode"
_DECODE = "decode"
_WEATHER = "weather"
_COMMANDS = {_ENCODE, _DECODE, _WEATHER}


def _add_tone_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("outfile", nargs="?", default="-", help="'-' to play live")
    p.add_argument("loops", nargs="?", type=int, default=5, help="repeats when writing a file")
    p.add_argument("--unit", type=float, default=0.10, help="dot length in seconds")
    p.add_argument("--attack", type=float, default=0.008)
    p.add_argument("--release", type=float, default=0.008)
    p.add_argument("--vol", type=float, default=0.20)
    p.add_argument("--left", type=float, default=600.0, help="left channel Hz")
    p.add_argument("--right", type=float, default=615.0, help="right channel Hz")
    p.add_argument("--sr", type=int, default=48000)
    p.add_argument("--bitrate", default="128k")


def _render(message: str, args: argparse.Namespace) -> None:
    one = synth(
        message, args.sr, args.unit, args.attack, args.release, args.vol, args.left, args.right
    )
    if args.outfile == "-":
        play_loop(one, args.sr)
    elif args.outfile.lower().endswith(".mp3"):
        write_mp3(args.outfile, np.tile(one, (args.loops, 1)), args.sr, args.bitrate)
    else:
        write_wav(args.outfile, np.tile(one, (args.loops, 1)), args.sr)


def _encode(args: argparse.Namespace) -> None:
    _render(args.message, args)


def _decode(args: argparse.Namespace) -> None:
    audio, sr = read_audio(args.infile)
    print(decode(audio, sr, threshold=args.threshold, window=args.window))


def _weather(args: argparse.Namespace) -> None:
    message = weather_report()
    print(message, file=sys.stderr)  # show the text being broadcast
    _render(message, args)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command")

    enc = sub.add_parser(_ENCODE, help="text -> audio (play, WAV, or MP3)")
    enc.add_argument("message", nargs="?", default="IT IS OVER OVER")
    _add_tone_args(enc)
    enc.set_defaults(func=_encode)

    dec = sub.add_parser(_DECODE, help="audio (WAV/MP3) -> text")
    dec.add_argument("infile")
    dec.add_argument("--threshold", type=float, default=0.5, help="fraction of peak = tone on")
    dec.add_argument("--window", type=float, default=0.005, help="RMS smoothing seconds")
    dec.set_defaults(func=_decode)

    wx = sub.add_parser(_WEATHER, help="broadcast Tartu weather as Morse")
    _add_tone_args(wx)
    wx.set_defaults(func=_weather)

    return parser


def main(argv: list[str] | None = None) -> None:
    argv = list(sys.argv[1:] if argv is None else argv)
    # Default to `encode` so bare `morse` and `morse "SOS" out.wav` still work.
    if not argv or argv[0] not in _COMMANDS | {"-h", "--help"}:
        argv.insert(0, _ENCODE)

    args = _build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
