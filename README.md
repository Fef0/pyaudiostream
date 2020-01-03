# pyaudiostream
A python script for searching and pretty-printing info about audio streams on a Linux machine.
## Warning: pyaudiostream works with python3 only (Tested with python 3.8.0 on Arch Linux)

# Usage
pyaudiostream is totally automated, so just call it with ```python pyaudiostream.py``` (or ```python3 pyaudiostream.py``` if you're using an older system) and a list of audio streams will be printed (if any).

# Example
```python pyaudiostream.py```

```
--- Starting audiostream version 1.0 ---
Searching...

Found 3 active streams
0:
   device_name: PCH
   device_path: /proc/asound/card0
   process_name: pulseaudio (PID 959)
   access: MMAP_INTERLEAVED
   rate: 44100 Hz (44100/1)
   bit_depth: 16
   format: S16_LE
   subformat: STD
   channels: 2
   period_size: 44100
   buffer_size: 88200
   stream_name: pcm0p
   substream_name: sub0
   audio_path: /dev/snd/pcmC0D0p

1:
   device_name: USB20
   device_path: /proc/asound/card1
   process_name: strawberry (PID 53994)
   access: RW_INTERLEAVED
   rate: 96000 Hz (96000/1)
   bit_depth: 32
   format: S32_LE
   subformat: STD
   channels: 2
   period_size: 960
   buffer_size: 19200
   stream_name: pcm0p
   substream_name: sub0
   audio_path: /dev/snd/pcmC1D0p

2:
   device_name: Device
   device_path: /proc/asound/card2
   process_name: pulseaudio (PID 959)
   access: MMAP_INTERLEAVED
   rate: 48000 Hz (48000/1)
   bit_depth: 16
   format: S16_LE
   subformat: STD
   channels: 2
   period_size: 44100
   buffer_size: 88200
   stream_name: pcm0p
   substream_name: sub0
   audio_path: /dev/snd/pcmC2D0p
```
