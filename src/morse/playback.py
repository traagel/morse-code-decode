"""Loop audio through the speakers until the user presses 'q'."""

import select
import sys
import termios
import tty

import numpy as np

try:
    import sounddevice as sd
except ImportError:
    sd = None


def play_loop(audio: np.ndarray, sr: int) -> None:
    if sd is None:
        raise SystemExit("Install playback dependency: pip install sounddevice")

    print("Playing. Press q to quit.")

    old_settings = termios.tcgetattr(sys.stdin)

    try:
        tty.setcbreak(sys.stdin.fileno())

        while True:
            sd.play(audio, sr)

            while sd.get_stream().active:
                if select.select([sys.stdin], [], [], 0.05)[0]:
                    key = sys.stdin.read(1)
                    if key.lower() == "q":
                        sd.stop()
                        return

            sd.wait()

    except KeyboardInterrupt:
        pass
    finally:
        sd.stop()
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
