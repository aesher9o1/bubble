import os
import random
from pydub import AudioSegment

def get_random_audio_segment(duration_sec, output_path):
    """
    Pick a random audio file from data/background directory and extract a random segment
    of the specified duration.
    
    Args:
        duration_sec (int): Duration of the segment to extract in seconds
        output_path (str): Path where the extracted segment should be saved
        
    Returns:
        str: Path to the saved audio segment
    """
    background_dir = "data/background"
    
    # Get all audio files from the background directory
    audio_files = [f for f in os.listdir(background_dir) if f.endswith(('.webm', '.mp3', '.wav', '.m4a'))]
    
    if not audio_files:
        raise ValueError("No audio files found in data/background directory")
    
    # Pick a random audio file
    random_file = random.choice(audio_files)
    file_path = os.path.join(background_dir, random_file)
    
    print(f"Selected background audio: {random_file}")
    
    # Load the audio file
    audio = AudioSegment.from_file(file_path)
    
    # Convert duration to milliseconds
    duration_ms = duration_sec * 1000
    audio_length_ms = len(audio)
    
    # If the audio is shorter than requested duration, repeat it
    if audio_length_ms < duration_ms:
        repeat_count = (duration_ms // audio_length_ms) + 1
        audio = audio * repeat_count
        audio_length_ms = len(audio)
    
    # Pick a random starting point for the segment
    if audio_length_ms > duration_ms:
        max_start = audio_length_ms - duration_ms
        start_ms = random.randint(0, max_start)
        end_ms = start_ms + duration_ms
        segment = audio[start_ms:end_ms]
    else:
        # If audio is exactly the right length or we repeated it
        segment = audio[:duration_ms]
    
    # Export the segment
    segment.export(output_path, format="wav")
    
    print(f"Extracted {duration_sec}s segment from {random_file} and saved to {output_path}")
    
    return output_path
