#!/usr/bin/env python3
"""
Example usage of the waveform video generator.

This demonstrates different ways to use the functional API.
"""

from waveform import (
    generate_waveform_video,
    load_audio,
    prepare_waveform_data,
    get_default_output_path
)
import os

def example_basic_usage():
    """Example 1: Basic usage with default settings"""
    print("=== Example 1: Basic Usage ===")
    
    audio_file = "sample_audio.mp3"  # Replace with your audio file
    
    if not os.path.exists(audio_file):
        print(f"Please provide a valid audio file. '{audio_file}' not found.")
        return
    
    # Generate video with all defaults
    output_path = generate_waveform_video(audio_file)
    print(f"Video generated: {output_path}")

def example_custom_settings():
    """Example 2: Custom video settings"""
    print("\n=== Example 2: Custom Settings ===")
    
    audio_file = "sample_audio.mp3"  # Replace with your audio file
    
    if not os.path.exists(audio_file):
        print(f"Please provide a valid audio file. '{audio_file}' not found.")
        return
    
    # Generate video with custom settings
    output_path = generate_waveform_video(
        audio_path=audio_file,
        output_path="custom_waveform.mp4",
        width=1280,          # HD width
        height=720,          # HD height  
        fps=24               # Cinematic frame rate
    )
    print(f"Custom video generated: {output_path}")

def example_step_by_step():
    """Example 3: Using individual functions step by step"""
    print("\n=== Example 3: Step by Step Processing ===")
    
    audio_file = "sample_audio.mp3"  # Replace with your audio file
    
    if not os.path.exists(audio_file):
        print(f"Please provide a valid audio file. '{audio_file}' not found.")
        return
    
    # Step 1: Load audio
    print("Step 1: Loading audio...")
    audio_data, sample_rate, duration = load_audio(audio_file)
    print(f"Loaded {duration:.2f} seconds of audio at {sample_rate} Hz")
    
    # Step 2: Prepare waveform data
    print("Step 2: Preparing waveform...")
    width, height = 1920, 1080
    bar_heights, num_bars = prepare_waveform_data(audio_data, width, height)
    print(f"Created {num_bars} bars for visualization")
    
    # Step 3: Get default output path
    default_output = get_default_output_path(audio_file)
    print(f"Default output would be: {default_output}")
    
    # Step 4: Generate the full video (you could also create individual frames here)
    print("Step 3: Generating video...")
    final_output = generate_waveform_video(
        audio_path=audio_file,
        output_path="step_by_step_output.mp4",
        width=width,
        height=height
    )
    print(f"Final video: {final_output}")

def example_multiple_files():
    """Example 4: Process multiple audio files"""
    print("\n=== Example 4: Multiple Files ===")
    
    # List of audio files to process
    audio_files = [
        "song1.mp3",
        "song2.wav", 
        "podcast.mp3"
    ]
    
    # Process each file
    for audio_file in audio_files:
        if os.path.exists(audio_file):
            print(f"Processing: {audio_file}")
            output_path = generate_waveform_video(
                audio_path=audio_file,
                width=1280,
                height=720,
                fps=30
            )
            print(f"✅ Generated: {output_path}")
        else:
            print(f"⚠️ Skipping {audio_file} (file not found)")

def main():
    """Run all examples"""
    print("🎵 Waveform Video Generator Examples 🎵\n")
    
    # You can uncomment the examples you want to try:
    
    # example_basic_usage()
    # example_custom_settings() 
    # example_step_by_step()
    # example_multiple_files()
    
    print("\n📝 To run these examples:")
    print("1. Replace 'sample_audio.mp3' with your actual audio file")
    print("2. Uncomment the example functions you want to try")
    print("3. Run: uv run python example_usage.py")
    print("\n🚀 Or use the command line: uv run python waveform.py your_audio.mp3")

if __name__ == "__main__":
    main() 