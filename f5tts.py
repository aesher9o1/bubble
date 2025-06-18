import torch
import soundfile as sf
import os
import re
import numpy as np
from cached_path import cached_path
from f5_tts.infer.utils_infer import (
    infer_process,
    load_model,
    load_vocoder,
    preprocess_ref_audio_text,
)
from f5_tts.model import DiT

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Global variables to store loaded models
_model = None
_vocoder = None

def load_model_resources():
    """
    Load the F5-TTS model and vocoder into memory.
    Call this function to pre-load resources for multiple generations.
    """
    global _model, _vocoder
    
    if _model is not None:
        print("Model already loaded")
        return
    
    print("Loading F5-TTS model...")
    ckpt_path = str(cached_path("hf://SWivid/F5-TTS/F5TTS_v1_Base/model_1250000.safetensors"))
    F5TTS_model_cfg = dict(dim=1024, depth=22, heads=16, ff_mult=2, text_dim=512, conv_layers=4)
    _model = load_model(DiT, F5TTS_model_cfg, ckpt_path)
    _vocoder = load_vocoder()
    print("Model loaded successfully")

def unload_model_resources():
    """
    Unload the F5-TTS model and vocoder from memory and clear GPU cache.
    Call this function when done with generation to free resources.
    """
    global _model, _vocoder
    
    if _model is None:
        print("No model to unload")
        return
    
    print("Cleaning up GPU memory...")
    del _model
    del _vocoder
    _model = None
    _vocoder = None
    torch.cuda.empty_cache()
    print("GPU memory cleared")

def generate_audio(text: str, ref_audio_path: str = os.path.join(SCRIPT_DIR, "data", "audio4.mp3"), output_path: str = os.path.join(SCRIPT_DIR, "output", "generated_speech.wav")) -> str:
    """
    Generate audio from text using F5-TTS model.
    
    The model will be loaded at the beginning and unloaded after generation to free GPU memory.
    
    Args:
        text (str): Text to convert to speech
        ref_audio_path (str): Path to reference audio file (defaults to data/audio3.mp3 relative to script)
        output_path (str): Path to save the generated audio (defaults to output/generated_speech.wav relative to script)
        
    Returns:
        str: Path to the generated audio file
    
    Raises:
        FileNotFoundError: If reference audio file not found
    """
    if not os.path.exists(ref_audio_path):
        raise FileNotFoundError(f"Audio file not found at {ref_audio_path}")
    
    # Load model resources
    load_model_resources()
    
    try:
        # Load and preprocess audio
        ref_audio, ref_text = preprocess_ref_audio_text(ref_audio_path, "")
        
        # Generate speech using F5-TTS
        with torch.no_grad():
            final_wave, final_sample_rate, _ = infer_process(
                ref_audio,
                ref_text,
                text,
                _model,
                _vocoder,
                cross_fade_duration=0.15,
                nfe_step=32,
                speed=0.8,
            )
        
        # Save the generated audio
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        sf.write(output_path, final_wave, final_sample_rate)
        print(f"Generated speech saved to {output_path}")
        return output_path
        
    finally:
        # Unload model resources
        unload_model_resources()

def parse_tagged_text(text: str):
    """
    Parse emotion-tagged text and extract segments with their emotions.
    
    Args:
        text (str): Text with emotion tags like <scared>text</scared> and <silence>2</silence>
        
    Returns:
        list: List of tuples (emotion, content) where emotion is the tag name or 'silence'
    """
    segments = []
    # Pattern to match both emotion tags and silence tags
    pattern = r'<(\w+)>(.*?)</\1>'
    
    last_end = 0
    for match in re.finditer(pattern, text, re.DOTALL):
        start, end = match.span()
        
        # Add any text before this tag as neutral
        if start > last_end:
            before_text = text[last_end:start].strip()
            if before_text:
                segments.append(('neutral', before_text))
        
        emotion = match.group(1)
        content = match.group(2).strip()
        segments.append((emotion, content))
        
        last_end = end
    
    # Add any remaining text as neutral
    if last_end < len(text):
        remaining_text = text[last_end:].strip()
        if remaining_text:
            segments.append(('neutral', remaining_text))
    
    return segments

def generate_silence(duration_seconds: float, sample_rate: int = 24000) -> np.ndarray:
    """
    Generate silence audio array.
    
    Args:
        duration_seconds (float): Duration of silence in seconds
        sample_rate (int): Sample rate for the silence
        
    Returns:
        np.ndarray: Silent audio array
    """
    samples = int(duration_seconds * sample_rate)
    return np.zeros(samples, dtype=np.float32)

def get_emotion_audio_path(emotion: str) -> str:
    """
    Get the path to the reference audio file for the given emotion.
    
    Args:
        emotion (str): Emotion name (angry, neutral, scared, surprised)
        
    Returns:
        str: Path to the emotion reference audio file
    """
    emotion_path = os.path.join(SCRIPT_DIR, "data", "emotions", f"{emotion}.mp3")
    
    # Default to neutral if emotion file doesn't exist
    if not os.path.exists(emotion_path):
        emotion_path = os.path.join(SCRIPT_DIR, "data", "emotions", "neutral.mp3")
    
    return emotion_path

def generate_emotion_audio(text: str, output_path: str = os.path.join(SCRIPT_DIR, "output", "emotional_speech.wav")) -> str:
    """
    Generate audio from emotion-tagged text using appropriate reference audio for each emotion.
    
    Args:
        text (str): Emotion-tagged text to convert to speech
        output_path (str): Path to save the generated audio
        
    Returns:
        str: Path to the generated audio file
    """
    # Parse the tagged text
    segments = parse_tagged_text(text)
    
    if not segments:
        raise ValueError("No text segments found to generate audio")
    
    # Load model resources
    load_model_resources()
    
    try:
        all_audio_segments = []
        sample_rate = 24000  # Default sample rate
        
        for emotion, content in segments:
            print(f"Processing {emotion}: {content[:50]}...")
            
            if emotion == 'silence':
                # Generate silence for the specified duration
                try:
                    duration = float(content)
                    silence_audio = generate_silence(duration, sample_rate)
                    all_audio_segments.append(silence_audio)
                    print(f"Added {duration} seconds of silence")
                except ValueError:
                    print(f"Invalid silence duration: {content}, skipping...")
                    continue
            else:
                # Generate speech for this emotion
                ref_audio_path = get_emotion_audio_path(emotion)
                print(f"Using reference audio: {ref_audio_path}")
                
                # Load and preprocess audio
                ref_audio, ref_text = preprocess_ref_audio_text(ref_audio_path, "")
                
                # Generate speech using F5-TTS
                with torch.no_grad():
                    final_wave, final_sample_rate, _ = infer_process(
                        ref_audio,
                        ref_text,
                        content,
                        _model,
                        _vocoder,
                        cross_fade_duration=0.15,
                        nfe_step=32,
                        speed=0.9,
                    )
                
                all_audio_segments.append(final_wave)
                sample_rate = final_sample_rate
        
        # Concatenate all audio segments
        if all_audio_segments:
            final_audio = np.concatenate(all_audio_segments)
            
            # Save the combined audio
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            sf.write(output_path, final_audio, sample_rate)
            print(f"Generated emotional speech saved to {output_path}")
            return output_path
        else:
            raise ValueError("No audio segments were generated")
            
    finally:
        # Unload model resources
        unload_model_resources()
