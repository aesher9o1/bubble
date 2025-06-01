"""
Simple MelodyFlow Generator

A simplified Python module for generating music using Hugging Face's MusicGen models.

Requirements:
    - transformers
    - soundfile
    - torch
    - torchaudio

Install dependencies with:
    uv add transformers soundfile torch torchaudio
"""

import os
import torch
import soundfile as sf
from transformers import AutoProcessor, MusicgenForConditionalGeneration

# Check for GPU availability
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Global variables to store loaded models
_processor = None
_model = None

def load_model_resources():
    """
    Load the MusicGen model and processor into memory.
    Call this function to pre-load resources for multiple generations.
    """
    global _processor, _model
    
    if _model is not None:
        print("Model already loaded")
        return
    
    print("Loading MusicGen model...")
    _processor = AutoProcessor.from_pretrained("facebook/musicgen-stereo-medium")
    _model = MusicgenForConditionalGeneration.from_pretrained("facebook/musicgen-stereo-medium")
    _model = _model.to(device)
    print("Model loaded successfully")

def unload_model_resources():
    """
    Unload the MusicGen model and processor from memory and clear GPU cache.
    Call this function when done with generation to free resources.
    """
    global _processor, _model
    
    if _model is None:
        print("No model to unload")
        return
    
    print("Cleaning up GPU memory...")
    del _processor
    del _model
    _processor = None
    _model = None
    torch.cuda.empty_cache()
    print("GPU memory cleared")

def generate_melody(
    prompt: str,
    output_path: str = "output/generated_melody.wav",
    duration_seconds: float = 30.0,
) -> str:
    """
    Generate 30-second stereo music using MusicGen model.
    
    The model will be loaded at the beginning and unloaded after generation to free GPU memory.
    
    Args:
        prompt: Text description of the desired music
        output_path: Path to save the generated audio
        duration_seconds: Duration in seconds (will be converted to tokens)
        
    Returns:
        Path to the generated stereo audio file
    """
    # Load model resources
    load_model_resources()
    
    try:
        # Convert duration to tokens (roughly 50 tokens per second for stereo-large)
        max_new_tokens = int(duration_seconds * 50)
        
        # Process the input
        inputs = _processor(
            text=prompt.split(","),
            padding=True,
            return_tensors="pt",
        )
        
        # Move inputs to the same device as the model
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        # Generate music with configuration parameters
        with torch.no_grad():  # Disable gradient computation for inference
            audio_values = _model.generate(
                **inputs, 
                max_new_tokens=max_new_tokens,
            )
        
        # Save the generated audio
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Convert to numpy and save (take first sequence if multiple generated)
        # Move back to CPU for numpy conversion
        audio_np = audio_values[0].cpu().numpy()
        
        # Handle tensor shape - MusicGen outputs [batch, channels, samples]
        # We need to squeeze and potentially transpose for soundfile
        if audio_np.ndim == 3:
            audio_np = audio_np.squeeze(0)  # Remove batch dimension
        if audio_np.ndim == 2 and audio_np.shape[0] < audio_np.shape[1]:
            audio_np = audio_np.T  # Transpose to [samples, channels] if needed
        
        # Get the correct sampling rate
        sampling_rate = _model.config.audio_encoder.sampling_rate
        
        sf.write(output_path, audio_np, sampling_rate)
        
        return output_path
        
    finally:
        # Unload model resources
        unload_model_resources()
