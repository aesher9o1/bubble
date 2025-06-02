import torch
import soundfile as sf
import os
import json
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
