# Audio Waveform Video Generator

This Python script generates a video visualization of an audio file with animated black vertical bar waveform using functional programming.

## Features

- **Animated Waveform**: Creates a dynamic vertical bar waveform that progresses with the audio
- **Visual Progress**: Shows a red progress line and highlights played portions in white
- **Customizable**: Adjustable video dimensions, frame rate, and output path
- **Multiple Audio Formats**: Supports various audio formats (MP3, WAV, FLAC, etc.)
- **High Quality Output**: Generates MP4 videos with H.264 codec
- **Functional Design**: Clean, functional programming approach without classes

## Installation

### Using UV (Recommended)

1. Install UV if you haven't already:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Install dependencies:
```bash
uv sync
```

### Using pip (Alternative)

```bash
pip install numpy matplotlib librosa moviepy
```

**FFmpeg Required**: You also need FFmpeg for video encoding:
- **Ubuntu/Debian**: `sudo apt install ffmpeg`
- **macOS**: `brew install ffmpeg`
- **Windows**: Download from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)

## Usage

### Command Line Interface

Basic usage:
```bash
# With UV
uv run python waveform.py path/to/your/audio.mp3

# Or direct Python
python waveform.py path/to/your/audio.mp3
```

With custom options:
```bash
uv run python waveform.py path/to/your/audio.mp3 -o output_video.mp4 -w 1280 --height 720 -f 24
```

### Command Line Arguments

- `audio_path`: Path to the input audio file (required)
- `-o, --output`: Output video file path (optional, defaults to `{audio_name}_waveform.mp4`)
- `-w, --width`: Video width in pixels (default: 1920)
- `--height`: Video height in pixels (default: 1080)
- `-f, --fps`: Frames per second (default: 30)

### Python API

You can also import and use the functions directly:

```python
from waveform import generate_waveform_video

# Generate video with default settings
output_path = generate_waveform_video("path/to/audio.mp3")

# Generate video with custom settings
output_path = generate_waveform_video(
    audio_path="path/to/audio.mp3",
    output_path="custom_output.mp4",
    width=1280,
    height=720,
    fps=24
)

print(f"Video saved to: {output_path}")
```

### Individual Functions

You can also use individual functions for more control:

```python
from waveform import load_audio, prepare_waveform_data, create_frame

# Load audio
audio_data, sample_rate, duration = load_audio("audio.mp3")

# Prepare waveform data
bar_heights, num_bars = prepare_waveform_data(audio_data, 1920, 1080)

# Create a single frame at time t=5.0 seconds
frame = create_frame(5.0, bar_heights, num_bars, duration, 1920, 1080)
```

## How It Works

The script uses a functional approach with these main functions:

1. **`load_audio()`**: Loads the audio file and returns audio data, sample rate, and duration
2. **`prepare_waveform_data()`**: Analyzes the audio using RMS calculations and creates bar height data
3. **`create_frame()`**: Generates individual video frames with the current waveform state
4. **`generate_waveform_video()`**: Orchestrates the entire process to create the final video

## Visual Elements

- **Black Background**: Clean black background for the waveform
- **White Bars**: Played portions of the audio are shown in bright white
- **Gray Bars**: Unplayed portions are shown in semi-transparent gray
- **Red Progress Line**: A red vertical line indicates the current playback position

## Supported Audio Formats

The script supports various audio formats through librosa:
- MP3
- WAV
- FLAC
- M4A
- OGG
- And many more

## Development

If you want to contribute or modify the code:

```bash
# Install development dependencies
uv sync --dev

# Run with development environment
uv run python waveform.py your_audio.mp3
```

## Requirements

- Python 3.8+
- NumPy
- Matplotlib
- librosa
- MoviePy
- FFmpeg (for video encoding)

## Example Output

The generated video will have:
- Audio track from the original file
- Animated waveform visualization
- Progress indication with smooth transitions
- Professional-quality MP4 output

## Troubleshooting

**FFmpeg not found**: Make sure FFmpeg is installed and accessible from your PATH.

**Memory issues with long audio**: For very long audio files, consider reducing the video resolution or frame rate.

**Audio loading errors**: Ensure your audio file is not corrupted and is in a supported format.

**UV not found**: Install UV using the installation command above, or fall back to pip.

## Why Functional Programming?

This implementation uses functional programming principles:
- **Pure functions**: Each function has clear inputs and outputs
- **No side effects**: Functions don't modify global state
- **Composable**: Functions can be easily combined and reused
- **Testable**: Individual functions can be tested independently
- **Readable**: Code flow is easier to follow and understand

## License

This script is provided as-is for educational and personal use.
