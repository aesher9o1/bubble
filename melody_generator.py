"""
Simple MelodyFlow Generator

A simplified Python module for generating music using Hugging Face's MusicGen models.

Requirements:
    - transformers
    - soundfile
    - torch
    - torchaudio
    - audiocraft

Install dependencies with:
    uv add audiocraft torch torchaudio
"""

import os
import torch
import torchaudio
from typing import List, Union
from pydub import AudioSegment
import shutil

# AudioCraft implementation of MusicGen
from audiocraft.models import MusicGen
from audiocraft.data.audio import audio_write

device = torch.device("cuda")

# Global variable to store loaded model
_model = None
MODEL_MAX_DURATION = 20

def load_model_resources():
    """Load the AudioCraft MusicGen *melody* model into memory.
    """
    global _model

    if _model is not None:
        print("MusicGen already in memory – re-using it.")
        return

    print("Loading MusicGen (AudioCraft) – this can take a while …")

    # AudioCraft provides a convenient helper.  By default it puts the model on
    # GPU when available.
    _model = MusicGen.get_pretrained("facebook/musicgen-stereo-large", device=device.type)

    # Default generation parameters mirror those we had earlier.
    _model.set_generation_params(
        duration=MODEL_MAX_DURATION,
        use_sampling=True,
        top_k=250,
        top_p=0.0,
        temperature=1.0,
        cfg_coef=3.0,
    )

    print("MusicGen loaded and ready.")

def unload_model_resources():
    """Unload the global MusicGen model and free CUDA memory."""
    global _model

    if _model is None:
        print("No MusicGen instance is currently loaded – nothing to do.")
        return

    print("Releasing MusicGen and clearing GPU cache …")
    del _model
    _model = None
    torch.cuda.empty_cache()
    print("Resources released.")

# -----------------------------------------------------------------------------
# Internal helper: text-only melody generation (expects model pre-loaded).
# -----------------------------------------------------------------------------

def _generate_melody(
    prompt: str,
    output_path: str = "output/generated_melody.wav",
) -> str:
    """Generate music from *prompt* and write it to *output_path*.

    Parameters
    ----------
    prompt: str
        A single textual description (comma-separated tags, free-form text, …)
        describing the music to be produced.
    output_path: str, optional
        Destination WAV path.  Parent directories will be created when needed.

    Returns
    -------
    str
        The absolute path of the written WAV file.
    """
    # Make sure the global model is available (idempotent call).
    load_model_resources()

    # Generate the waveform from the textual prompt.
    wav_batch = _model.generate([prompt])

    # Extract the single sample and move it to CPU memory.
    wav_tensor = wav_batch[0].cpu()

    # Persist to disk.
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    audio_write(output_path, wav_tensor, _model.sample_rate, strategy="loudness", add_suffix=False)

    return os.path.abspath(output_path)

# -----------------------------------------------------------------------------
# Utility helper to create a melody long enough for an external podcast track.
# -----------------------------------------------------------------------------

def generate_full_melody(
    total_duration_sec: int,
    prompt: str,
    output_path: str,
) -> str:
    """Generate background music of *total_duration_sec* seconds by repeating a melody.

    It generates a single `MODEL_MAX_DURATION`-second segment from *prompt* and 
    repeats it as many times as needed to reach the desired total duration.

    Parameters
    ----------
    total_duration_sec: int
        Desired length of the resulting melody in **seconds**.
    prompt: str
        Textual description guiding the melody style.
    output_path: str
        Where to write the final combined WAV.

    Returns
    -------
    str
        Absolute path to the combined WAV file.
    """
    from math import ceil

    # Load the MusicGen model once for the generation.
    load_model_resources()

    # Determine total target length in milliseconds.
    target_duration_ms = total_duration_sec * 1000
    segment_ms = MODEL_MAX_DURATION * 1000
    
    # Calculate how many repetitions we need
    repetitions_needed = ceil(target_duration_ms / segment_ms)

    # Temporary storage for the base segment.
    tmp_dir = os.path.join(os.path.dirname(output_path), "tmp_segments")
    os.makedirs(tmp_dir, exist_ok=True)

    # Generate the base melody segment
    base_segment_path = os.path.join(tmp_dir, "base_segment.wav")
    _generate_melody(prompt, output_path=base_segment_path)
    
    # Load the base segment and repeat it
    base_melody = AudioSegment.from_wav(base_segment_path)
    full_melody = AudioSegment.empty()
    
    for _ in range(repetitions_needed):
        full_melody += base_melody

    # Trim to exact duration
    full_melody = full_melody[:target_duration_ms]

    # Export the final melody
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    full_melody.export(output_path, format="wav")

    # Cleanup temp files
    if os.path.exists(base_segment_path):
        os.remove(base_segment_path)
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir, ignore_errors=True)

    # Release model resources now that we're done.
    unload_model_resources()

    return os.path.abspath(output_path)
