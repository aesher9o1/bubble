import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.figure import Figure
import librosa
import os
import argparse
from pathlib import Path
from typing import Tuple, List, Optional, Callable, Any

# Handle numpy typing compatibility
try:
    import numpy.typing as npt
    NDArrayFloat32 = npt.NDArray[np.float32]
    NDArrayUInt8 = npt.NDArray[np.uint8]
except ImportError:
    # Fallback for older numpy versions
    NDArrayFloat32 = Any
    NDArrayUInt8 = Any

# Handle MoviePy import compatibility (v1.x vs v2.x)
try:
    # MoviePy v2.0+ style imports
    from moviepy import VideoClip, AudioFileClip
    from moviepy.video.io.bindings import mplfig_to_npimage
    MOVIEPY_V2 = True
except ImportError:
    try:
        # MoviePy v1.x style imports
        import moviepy.editor as mp
        from moviepy.video.io.bindings import mplfig_to_npimage
        VideoClip = mp.VideoClip
        AudioFileClip = mp.AudioFileClip
        MOVIEPY_V2 = False
    except ImportError as e:
        raise ImportError(
            "MoviePy is not installed. Please install it with: pip install moviepy"
        ) from e

def load_audio(audio_path: str) -> Tuple[NDArrayFloat32, int, float]:
    """Load audio file and return audio data, sample rate, and duration."""
    print(f"Loading audio file: {audio_path}")
    audio_data, sample_rate = librosa.load(audio_path, sr=None)
    duration = len(audio_data) / sample_rate
    print(f"Audio loaded - Duration: {duration:.2f} seconds, Sample rate: {sample_rate} Hz")
    return audio_data, sample_rate, duration

def prepare_waveform_data(audio_data: NDArrayFloat32, width: int, height: int) -> Tuple[List[float], int]:
    """Prepare waveform data for visualization."""
    print("Preparing waveform data...")
    
    # Calculate number of bars based on video width
    num_bars = width // 4  # 4 pixels per bar (2px bar + 2px space)
    
    # Resample audio to match number of bars
    samples_per_bar = len(audio_data) // num_bars
    
    # Calculate RMS (Root Mean Square) for each bar segment
    bar_heights: List[float] = []
    for i in range(num_bars):
        start_idx = i * samples_per_bar
        end_idx = min((i + 1) * samples_per_bar, len(audio_data))
        
        if start_idx < len(audio_data):
            segment = audio_data[start_idx:end_idx]
            # Calculate RMS and normalize
            rms = np.sqrt(np.mean(segment**2))
            # Scale to video height (leave some margin)
            bar_height = min(float(rms * height * 0.8), float(height * 0.9))
            bar_heights.append(bar_height)
        else:
            bar_heights.append(0.0)
    
    # Smooth the waveform for better visualization
    bar_heights = smooth_waveform(bar_heights)
    
    print(f"Waveform prepared - {num_bars} bars")
    return bar_heights, num_bars

def smooth_waveform(heights: List[float], window_size: int = 5) -> List[float]:
    """Apply smoothing to the waveform data."""
    if len(heights) < window_size:
        return heights
    
    smoothed: List[float] = []
    for i in range(len(heights)):
        start = max(0, i - window_size // 2)
        end = min(len(heights), i + window_size // 2 + 1)
        smoothed.append(float(np.mean(heights[start:end])))
    
    return smoothed

def create_frame(t: float, bar_heights: List[float], num_bars: int, duration: float, width: int, height: int) -> NDArrayUInt8:
    """Create a single frame of the waveform visualization."""
    fig, ax = plt.subplots(figsize=(width/100, height/100), dpi=100)
    fig.patch.set_facecolor('black')
    ax.set_facecolor('black')
    
    # Remove axes
    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    ax.axis('off')
    
    # Calculate current position in the audio
    progress = t / duration
    current_bar = int(progress * num_bars)
    
    # Draw bars
    bar_width = 2
    spacing = 4
    
    for i, bar_height in enumerate(bar_heights):
        x = i * spacing + spacing // 2
        y = (height - bar_height) / 2
        
        # Determine bar color based on current position
        if i <= current_bar:
            color = 'white'  # Played portion
            alpha = 1.0
        else:
            color = 'gray'   # Unplayed portion
            alpha = 0.3
        
        # Draw the bar
        rect = Rectangle((x, y), bar_width, bar_height, 
                       facecolor=color, alpha=alpha, edgecolor='none')
        ax.add_patch(rect)
    
    # Add a progress indicator line
    if current_bar < num_bars:
        progress_x = current_bar * spacing + spacing // 2 + bar_width
        ax.axvline(x=progress_x, color='red', linewidth=3, alpha=0.8)
    
    plt.tight_layout(pad=0)
    return mplfig_to_npimage(fig)

def get_default_output_path(audio_path: str) -> str:
    """Generate default output path based on input audio file."""
    audio_stem = Path(audio_path).stem
    return f"{audio_stem}_waveform.mp4"

def generate_waveform_video(audio_path: str, output_path: Optional[str] = None, width: int = 1920, height: int = 1080, fps: int = 30) -> str:
    """Generate the complete video with waveform and audio."""
    # Set default output path if not provided
    if output_path is None:
        output_path = get_default_output_path(audio_path)
    
    print(f"Starting video generation...")
    print(f"Input: {audio_path}")
    print(f"Output: {output_path}")
    print(f"Resolution: {width}x{height} @ {fps}fps")
    print(f"Using MoviePy {'v2.x' if MOVIEPY_V2 else 'v1.x'}")
    
    # Load audio data
    audio_data, sample_rate, duration = load_audio(audio_path)
    
    # Prepare waveform data
    bar_heights, num_bars = prepare_waveform_data(audio_data, width, height)
    
    # Create video clip with waveform animation
    def make_frame(t: float) -> NDArrayUInt8:
        plt.close('all')  # Close any existing figures
        return create_frame(t, bar_heights, num_bars, duration, width, height)
    
    print("Creating video frames...")
    # Create video clip
    video_clip = VideoClip(make_frame, duration=duration)
    
    # Set fps using the appropriate method for the MoviePy version
    if MOVIEPY_V2:
        video_clip = video_clip.with_fps(fps)
    else:
        video_clip = video_clip.set_fps(fps)
    
    # Load audio clip
    print("Loading audio for video...")
    audio_clip = AudioFileClip(audio_path)
    
    # Combine video and audio
    print("Combining video and audio...")
    if MOVIEPY_V2:
        final_clip = video_clip.with_audio(audio_clip)
    else:
        final_clip = video_clip.set_audio(audio_clip)
    
    # Write the final video
    print("Rendering final video...")
    final_clip.write_videofile(
        output_path,
        fps=fps,
        codec='libx264',
        audio_codec='aac',
        temp_audiofile='temp-audio.m4a',
        remove_temp=True
    )
    
    print(f"✅ Video successfully generated: {output_path}")
    
    # Clean up
    video_clip.close()
    audio_clip.close()
    final_clip.close()
    plt.close('all')
    
    return output_path

def main() -> None:
    """Main function to handle command line arguments and generate video."""
    parser = argparse.ArgumentParser(description='Generate a video with waveform visualization from audio file')
    parser.add_argument('audio_path', help='Path to the input audio file')
    parser.add_argument('-o', '--output', help='Output video file path')
    parser.add_argument('-w', '--width', type=int, default=1920, help='Video width (default: 1920)')
    parser.add_argument('--height', type=int, default=1080, help='Video height (default: 1080)')
    parser.add_argument('-f', '--fps', type=int, default=30, help='Frames per second (default: 30)')
    
    args = parser.parse_args()
    
    # Check if audio file exists
    if not os.path.exists(args.audio_path):
        print(f"❌ Error: Audio file '{args.audio_path}' not found.")
        return
    
    try:
        # Generate video
        output_path = generate_waveform_video(
            audio_path=args.audio_path,
            output_path=args.output,
            width=args.width,
            height=args.height,
            fps=args.fps
        )
        
        print(f"🎉 Done! Your waveform video is ready: {output_path}")
        
    except Exception as e:
        print(f"❌ Error generating video: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
