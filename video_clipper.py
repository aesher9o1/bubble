import os
import random
import subprocess
import ffmpeg

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Use conda ffmpeg which has NVENC support
FFMPEG_BINARY = "/opt/conda/bin/ffmpeg"

# YouTube Shorts specifications
SHORTS_MAX_DURATION = 59  # seconds (under 60)
SHORTS_WIDTH = 1080
SHORTS_HEIGHT = 1920  # 9:16 aspect ratio


def detect_gpu_codec():
    """
    Detect available GPU codecs on the system.
    
    Returns:
        dict: Available GPU codecs and settings
    """
    gpu_config = {
        'video_codec': 'libx264',  # fallback to CPU
        'audio_codec': 'aac',
        'gpu_params': {},
        'gpu_available': False
    }
    
    try:
        # Check for available encoders using conda ffmpeg
        result = subprocess.run([FFMPEG_BINARY, '-encoders'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            print(f"⚠ Error running ffmpeg -encoders: {result.stderr}")
            return gpu_config
            
        encoders_output = result.stdout
        print("🔍 Checking available GPU encoders...")
        
        # Check for NVIDIA GPU presence
        nvidia_available = False
        try:
            nvidia_check = subprocess.run(['nvidia-smi'], 
                                        capture_output=True, text=True, timeout=5)
            if nvidia_check.returncode == 0:
                nvidia_available = True
                print("✓ Tesla T4 GPU detected")
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        # Check for NVENC and configure GPU acceleration
        if 'h264_nvenc' in encoders_output and nvidia_available:
            gpu_config.update({
                'video_codec': 'h264_nvenc',
                'gpu_params': {
                    'preset': 'fast',
                    'rc': 'vbr',
                    'cq': '23',
                    'qmin': '20',
                    'qmax': '26',
                    'b:v': '8M',
                    'maxrate': '12M',
                    'bufsize': '16M',
                    'gpu': '0'
                },
                'gpu_available': True
            })
            print("🚀 NVIDIA GPU encoding (h264_nvenc) enabled!")
            print("  Using Tesla T4 with NVENC acceleration")
            return gpu_config
            
        # Check for VAAPI as fallback
        elif 'h264_vaapi' in encoders_output and nvidia_available:
            gpu_config.update({
                'video_codec': 'h264_vaapi',
                'gpu_params': {
                    'preset': 'fast',
                    'b:v': '8M',
                    'maxrate': '12M',
                    'bufsize': '16M'
                },
                'gpu_available': True
            })
            print("🚀 VAAPI GPU encoding enabled!")
            print("  Using Tesla T4 with VAAPI acceleration")
            return gpu_config
            
        print("⚠ No compatible GPU encoders found, using optimized CPU encoding")
        gpu_config['gpu_params'] = {
            'preset': 'fast',
            'crf': '23'
        }
            
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"⚠ Error checking GPU encoders: {e}")
    
    return gpu_config


# Global GPU configuration
GPU_CONFIG = detect_gpu_codec()


def get_video_info(video_path):
    """
    Get video information using ffprobe.
    
    Args:
        video_path: Path to the video file
        
    Returns:
        dict: Video information including duration, fps, resolution
    """
    try:
        probe = ffmpeg.probe(video_path, cmd=FFMPEG_BINARY.replace('ffmpeg', 'ffprobe'))
        video_stream = next(s for s in probe['streams'] if s['codec_type'] == 'video')
        
        duration = float(probe['format']['duration'])
        fps = eval(video_stream['r_frame_rate'])  # Convert fraction to float
        width = int(video_stream['width'])
        height = int(video_stream['height'])
        
        return {
            'duration': duration,
            'fps': fps,
            'width': width,
            'height': height,
            'codec': video_stream['codec_name']
        }
    except Exception as e:
        raise ValueError(f"Could not get video info for {video_path}: {e}")


def get_random_video_from_directory(video_directory=None):
    """
    Pick a random video file from the specified directory.
    """
    if video_directory is None:
        video_directory = os.path.join(SCRIPT_DIR, "data", "video")
        
    if not os.path.exists(video_directory):
        raise ValueError(f"Video directory {video_directory} does not exist")
    
    video_files = [f for f in os.listdir(video_directory) 
                   if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm'))]
    
    if not video_files:
        raise ValueError(f"No video files found in {video_directory}")
    
    selected_video = random.choice(video_files)
    return os.path.join(video_directory, selected_video)


def extract_random_segment(video_path, target_duration_seconds, output_path):
    """
    Extract a random segment from a video file using GPU acceleration.
    
    Args:
        video_path: Path to the source video file
        target_duration_seconds: Duration of the segment to extract
        output_path: Path where the extracted segment will be saved
    
    Returns:
        Path to the extracted video segment
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Get video information
    video_info = get_video_info(video_path)
    video_duration = video_info['duration']
    
    # Ensure we don't try to extract more than the video length
    segment_duration = min(target_duration_seconds, video_duration)
    
    # Choose a random start time, ensuring we don't go beyond the video
    max_start_time = max(0, video_duration - segment_duration)
    start_time = random.uniform(0, max_start_time)
    
    print(f"🎬 Extracting {segment_duration:.1f}s segment starting at {start_time:.1f}s")
    print(f"🚀 Using codec: {GPU_CONFIG['video_codec']}")
    
    # Build ffmpeg command with GPU acceleration
    input_stream = ffmpeg.input(video_path, ss=start_time, t=segment_duration)
    
    # Configure encoding parameters based on GPU availability
    if GPU_CONFIG['gpu_available']:
        output_params = {
            'vcodec': GPU_CONFIG['video_codec'],
            'acodec': GPU_CONFIG['audio_codec'],
            **GPU_CONFIG['gpu_params']
        }
    else:
        output_params = {
            'vcodec': GPU_CONFIG['video_codec'],
            'acodec': GPU_CONFIG['audio_codec'],
            **GPU_CONFIG['gpu_params']
        }
    
    # Execute ffmpeg command
    try:
        (
            ffmpeg
            .output(input_stream, output_path, **output_params)
            .global_args('-y')  # Overwrite output file
            .run(cmd=FFMPEG_BINARY, quiet=True, overwrite_output=True)
        )
        
        print(f"✅ Video segment extracted: {output_path}")
        return output_path
        
    except ffmpeg.Error as e:
        raise RuntimeError(f"FFmpeg error during video extraction: {e}")


def add_audio_to_video(video_path, audio_path, output_path):
    """
    Add audio track to a video file using GPU acceleration, replacing the original audio.
    Video will be trimmed to match audio duration.
    
    Args:
        video_path: Path to the video file
        audio_path: Path to the audio file to add
        output_path: Path where the final video will be saved
    
    Returns:
        Path to the final video with audio
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Get video and audio information
    video_info = get_video_info(video_path)
    
    # Get audio duration using ffprobe
    try:
        audio_probe = ffmpeg.probe(audio_path, cmd=FFMPEG_BINARY.replace('ffmpeg', 'ffprobe'))
        audio_duration = float(audio_probe['format']['duration'])
    except Exception as e:
        raise ValueError(f"Could not get audio info for {audio_path}: {e}")
    
    # Calculate final duration (trim video to audio duration if needed)
    final_duration = min(audio_duration, video_info['duration'])
    
    print(f"🎵 Adding audio to video (duration: {final_duration:.1f}s)")
    print(f"🚀 Using codec: {GPU_CONFIG['video_codec']}")
    
    # Build ffmpeg command
    video_input = ffmpeg.input(video_path)
    audio_input = ffmpeg.input(audio_path)
    
    # Configure encoding parameters
    if GPU_CONFIG['gpu_available']:
        output_params = {
            'vcodec': GPU_CONFIG['video_codec'],
            'acodec': GPU_CONFIG['audio_codec'],
            't': final_duration,
            **GPU_CONFIG['gpu_params']
        }
    else:
        output_params = {
            'vcodec': GPU_CONFIG['video_codec'],
            'acodec': GPU_CONFIG['audio_codec'],
            't': final_duration,
            **GPU_CONFIG['gpu_params']
        }
    
    try:
        (
            ffmpeg
            .output(
                video_input['v'], audio_input['a'], 
                output_path, 
                **output_params
            )
            .global_args('-y')  # Overwrite output file
            .run(cmd=FFMPEG_BINARY, quiet=True, overwrite_output=True)
        )
        
        print(f"✅ Video with audio created: {output_path}")
        return output_path
        
    except ffmpeg.Error as e:
        raise RuntimeError(f"FFmpeg error during audio addition: {e}")


def convert_to_shorts_format(input_video_path, output_path):
    """
    Convert a regular video to YouTube Shorts format (9:16 aspect ratio).
    Uses smart cropping to focus on the center of the video.
    
    Args:
        input_video_path: Path to the input video
        output_path: Path where the shorts video will be saved
    
    Returns:
        Path to the converted shorts video
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Get video information
    video_info = get_video_info(input_video_path)
    input_width = video_info['width']
    input_height = video_info['height']
    
    print(f"📱 Converting to Shorts format (9:16)")
    print(f"   Original: {input_width}x{input_height}")
    print(f"   Target: {SHORTS_WIDTH}x{SHORTS_HEIGHT}")
    print(f"🚀 Using codec: {GPU_CONFIG['video_codec']}")
    
    # Calculate scaling and cropping parameters
    # We want to crop to 9:16 while maintaining quality
    target_aspect = SHORTS_WIDTH / SHORTS_HEIGHT  # 9:16 = 0.5625
    current_aspect = input_width / input_height
    
    # Build the filter chain based on current aspect ratio
    if current_aspect > target_aspect:
        # Video is wider than 9:16, crop width (vertical crop)
        crop_width = int(input_height * target_aspect)
        crop_height = input_height
        crop_x = (input_width - crop_width) // 2
        crop_y = 0
        
        # Crop then scale
        video_filter = f"crop={crop_width}:{crop_height}:{crop_x}:{crop_y},scale={SHORTS_WIDTH}:{SHORTS_HEIGHT}"
    else:
        # Video is taller than 9:16 or equal, crop height (horizontal crop)
        crop_width = input_width
        crop_height = int(input_width / target_aspect)
        crop_x = 0
        crop_y = (input_height - crop_height) // 2
        
        # Crop then scale
        video_filter = f"crop={crop_width}:{crop_height}:{crop_x}:{crop_y},scale={SHORTS_WIDTH}:{SHORTS_HEIGHT}"
    
    # Build ffmpeg command
    input_stream = ffmpeg.input(input_video_path)
    
    # Configure encoding parameters
    if GPU_CONFIG['gpu_available']:
        output_params = {
            'vcodec': GPU_CONFIG['video_codec'],
            'acodec': GPU_CONFIG['audio_codec'],
            'vf': video_filter,
            **GPU_CONFIG['gpu_params']
        }
    else:
        output_params = {
            'vcodec': GPU_CONFIG['video_codec'],
            'acodec': GPU_CONFIG['audio_codec'],
            'vf': video_filter,
            **GPU_CONFIG['gpu_params']
        }
    
    try:
        (
            ffmpeg
            .output(input_stream, output_path, **output_params)
            .global_args('-y')  # Overwrite output file
            .run(cmd=FFMPEG_BINARY, quiet=True, overwrite_output=True)
        )
        
        print(f"✅ Shorts video created: {output_path}")
        return output_path
        
    except ffmpeg.Error as e:
        raise RuntimeError(f"FFmpeg error during shorts conversion: {e}")


def extract_shorts_segment(video_path, target_duration_seconds, output_path):
    """
    Extract a random segment optimized for YouTube Shorts (under 60 seconds).
    
    Args:
        video_path: Path to the source video file
        target_duration_seconds: Requested duration (will be capped at 59 seconds)
        output_path: Path where the extracted segment will be saved
    
    Returns:
        Path to the extracted video segment
    """
    # Ensure shorts duration limit
    segment_duration = min(target_duration_seconds, SHORTS_MAX_DURATION)
    
    print(f"📱 Extracting Shorts segment (max {SHORTS_MAX_DURATION}s, requested {segment_duration:.1f}s)")
    
    # Use existing extract_random_segment but with shorts duration limit
    return extract_random_segment(video_path, segment_duration, output_path)


def create_shorts_version(merged_audio_path, file_name, video_directory=None):
    """
    Create a complete YouTube Shorts video with audio.
    
    Args:
        merged_audio_path: Path to the audio file to add to video
        file_name: Base name for output files
        video_directory: Directory containing source videos
    
    Returns:
        dict: Contains paths to generated shorts files
    """
    if video_directory is None:
        video_directory = os.path.join(SCRIPT_DIR, "data", "video")
        
    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)
    
    # Get audio duration to determine video length
    try:
        audio_probe = ffmpeg.probe(merged_audio_path, cmd=FFMPEG_BINARY.replace('ffmpeg', 'ffprobe'))
        audio_duration = float(audio_probe['format']['duration'])
    except Exception as e:
        raise ValueError(f"Could not get audio info for {merged_audio_path}: {e}")
    
    # Limit to shorts duration
    shorts_duration = min(audio_duration, SHORTS_MAX_DURATION)
    
    # Pick a random video
    source_video_path = get_random_video_from_directory(video_directory)
    
    # Define output paths
    shorts_segment_path = f"output/{file_name}_shorts_segment.mp4"
    shorts_converted_path = f"output/{file_name}_shorts_converted.mp4"
    shorts_final_path = f"output/{file_name}_shorts.mp4"
    
    print(f"📱 Creating YouTube Shorts version")
    print(f"📁 Source: {os.path.basename(source_video_path)}")
    print(f"⏱️  Duration: {shorts_duration:.1f}s")
    
    # Step 1: Extract segment from source video
    extract_shorts_segment(source_video_path, shorts_duration, shorts_segment_path)
    
    # Step 2: Convert to shorts format (9:16 aspect ratio)
    convert_to_shorts_format(shorts_segment_path, shorts_converted_path)
    
    # Step 3: Add audio to the shorts video
    add_audio_to_video(shorts_converted_path, merged_audio_path, shorts_final_path)
    
    return {
        'shorts_segment': shorts_segment_path,
        'shorts_converted': shorts_converted_path,
        'shorts_final': shorts_final_path,
        'source_video': source_video_path,
        'duration': shorts_duration,
        'gpu_used': GPU_CONFIG['gpu_available'],
        'codec_used': GPU_CONFIG['video_codec']
    }


def process_video_with_audio(target_duration_seconds, merged_audio_path, file_name, video_directory=None):
    """
    Complete video processing pipeline with GPU acceleration:
    1. Pick a random video from directory
    2. Extract a random segment using GPU
    3. Add the merged audio to the segment using GPU
    4. Create YouTube Shorts version
    
    Args:
        target_duration_seconds: Duration of the video segment to extract
        merged_audio_path: Path to the audio file to add to video
        file_name: Base name for output files
        video_directory: Directory containing source videos
    
    Returns:
        dict: Contains paths to generated files and performance info
    """
    if video_directory is None:
        video_directory = os.path.join(SCRIPT_DIR, "data", "video")
        
    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)
    
    # Pick a random video
    source_video_path = get_random_video_from_directory(video_directory)
    
    # Define output paths
    video_segment_path = f"output/{file_name}_video_segment.mp4"
    video_with_audio_path = f"output/{file_name}_video_with_audio.mp4"
    
    print(f"🎯 Processing video with GPU acceleration")
    print(f"📁 Source: {os.path.basename(source_video_path)}")
    
    # Extract random segment
    extract_random_segment(source_video_path, target_duration_seconds, video_segment_path)
    
    # Add audio to the video segment
    add_audio_to_video(video_segment_path, merged_audio_path, video_with_audio_path)
    
    # Create YouTube Shorts version
    shorts_results = create_shorts_version(merged_audio_path, file_name, video_directory)
    
    return {
        'video_segment': video_segment_path,
        'video_with_audio': video_with_audio_path,
        'source_video': source_video_path,
        'gpu_used': GPU_CONFIG['gpu_available'],
        'codec_used': GPU_CONFIG['video_codec'],
        # Add shorts results
        'shorts': shorts_results
    }


def get_gpu_info():
    """
    Get information about the current GPU configuration.
    
    Returns:
        dict: GPU configuration details
    """
    return {
        'video_codec': GPU_CONFIG['video_codec'],
        'audio_codec': GPU_CONFIG['audio_codec'],
        'gpu_acceleration': GPU_CONFIG['gpu_available'],
        'gpu_params': GPU_CONFIG['gpu_params']
    } 