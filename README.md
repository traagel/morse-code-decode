# morse

Synthesize text into Morse code audio (WAV/MP3 or live playback) and decode
Morse audio back into text.

## Install

```bash
uv sync
```

MP3 read/write needs [`ffmpeg`](https://ffmpeg.org/) on `PATH`. WAV and live
playback work without it.

## Usage

### Encode — text → audio

```bash
uv run morse "SOS OVER" out.wav      # write WAV
uv run morse "SOS OVER" out.mp3      # write MP3 (needs ffmpeg)
uv run morse "SOS OVER"              # play live, press q to quit
uv run morse "HELLO" out.wav 3       # 3 repeats in the file
```

Positional args: `message` `outfile` `loops`. `outfile` of `-` (the default)
plays live instead of writing.

| Flag | Default | Meaning |
|------|---------|---------|
| `--unit` | `0.10` | dot length in seconds (lower = faster) |
| `--attack` / `--release` | `0.008` | per-mark fade in/out (seconds), kills clicks |
| `--vol` | `0.20` | amplitude 0..1 |
| `--left` / `--right` | `600` / `615` | left/right tone Hz; the difference is a binaural beat |
| `--sr` | `48000` | sample rate |
| `--bitrate` | `128k` | MP3 bitrate |

### Decode — audio → text

```bash
uv run morse decode out.wav      # -> SOS OVER
uv run morse decode out.mp3
```

| Flag | Default | Meaning |
|------|---------|---------|
| `--threshold` | `0.5` | fraction of peak amplitude counted as "tone on" |
| `--window` | `0.005` | RMS smoothing window in seconds |

The decoder is self-calibrating: it estimates the dot length from the signal,
so it handles any speed without being told the WPM. Tuned for synthesized /
clean tones — noisy microphone recordings are not handled yet.

### As a library

```python
from morse import synth, write_wav, read_audio, decode

audio = synth("SOS", 48000, 0.1, 0.008, 0.008, 0.2, 600, 615)
write_wav("out.wav", audio, 48000)

audio, sr = read_audio("out.wav")
print(decode(audio, sr))   # -> SOS
```

## How it works

### Encode pipeline

```mermaid
flowchart LR
    A["text"] --> B["build_envelope<br/>0..1 on/off shape<br/>+ attack/release ramps"]
    B --> C["synth<br/>sine x envelope<br/>L/R freqs -> stereo"]
    C --> D{"outfile?"}
    D -->|"-"| E["play_loop<br/>(sounddevice)"]
    D -->|".wav"| F["write_wav"]
    D -->|".mp3"| G["write_mp3<br/>(ffmpeg)"]
```

### Decode pipeline

```mermaid
flowchart LR
    A["WAV / MP3"] --> B["read_audio<br/>-> float samples"]
    B --> C["pick one channel<br/>(avoids beat cancel)"]
    C --> D["sliding-RMS envelope"]
    D --> E["threshold -> on/off runs"]
    E --> F["estimate unit<br/>= shortest mark"]
    F --> G["classify dot/dash<br/>+ gap lengths"]
    G --> H["DEMORSE lookup<br/>-> text"]
```

### Morse timing

Everything is multiples of one `unit` (the dot length):

```mermaid
flowchart LR
    dot["dot = 1u (on)"]
    dash["dash = 3u (on)"]
    g1["intra-char gap = 1u (off)"]
    g3["letter gap = 3u (off)"]
    g7["word gap = 7u (off)"]
```

## Module layout

```
src/morse/
  table.py      MORSE + DEMORSE lookup maps
  synth.py      build_envelope, synth  (text -> audio)
  output.py     to_pcm16, write_wav, write_mp3
  loader.py     read_audio  (WAV native, MP3 via ffmpeg)
  decode.py     decode  (audio -> text)
  playback.py   play_loop  (live, press q)
  cli.py        encode / decode subcommands
tests/
  test_roundtrip.py   synth -> decode -> text
```

## Test

```bash
uv run python tests/test_roundtrip.py    # or: uv run pytest
```
