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
MODEL_MAX_DURATION = 12

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
    _model = MusicGen.get_pretrained("facebook/musicgen-stereo-melody-large", device=device.type)

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
# Internal helper: melody generation conditioned on an existing audio segment.
# -----------------------------------------------------------------------------

def _generate_melody_with_audio(
    audio_path: str,
    descriptions: Union[str, List[str]] = "",
    output_dir: str = "output",
) -> List[str]:
    """Generate music conditioned on an *audio* melody as well as *descriptions*.

    The input audio supplies the melodic/chromatic guide while *descriptions* give
    high-level style hints (genre, mood, instruments, …).

    Parameters
    ----------
    audio_path: str
        Path to an audio file (any ffmpeg-decodable format) to be used as the
        melodic guide.
    descriptions: Union[str, List[str]]
        Either a single prompt string or a list of prompts.  If a single string
        is supplied it will be wrapped in a list.
    output_dir: str, optional
        Directory where each generated WAV will be saved.  Filenames are
        sequential (0.wav, 1.wav, …).

    Returns
    -------
    List[str]
        List of file paths corresponding to each generated sample.
    """
    # Make sure descriptions is a list.
    if isinstance(descriptions, str):
        if descriptions != "":
            descriptions = [desc.strip() for desc in descriptions.split(",")]
        else:
            descriptions = [""]

    # Load reference melody.
    melody_wav, sr = torchaudio.load(audio_path)

    # The model expects shape [B, C, T]. Replicate melody for each prompt.
    melody_batch = melody_wav[None].expand(len(descriptions), -1, -1)

    # Ensure model is in memory (idempotent).
    load_model_resources()

    wav_batch = _model.generate_with_chroma(descriptions, melody_batch, sr)

    # Persist each generated sample.
    os.makedirs(output_dir, exist_ok=True)
    saved_paths: List[str] = []
    for idx, wav in enumerate(wav_batch):
        out_path = os.path.join(output_dir, f"{idx}.wav")
        audio_write(out_path, wav.cpu(), _model.sample_rate, strategy="loudness", add_suffix=False)
        saved_paths.append(os.path.abspath(out_path))

    return saved_paths

# -----------------------------------------------------------------------------
# Utility helper to create a melody long enough for an external podcast track.
# -----------------------------------------------------------------------------

def generate_full_melody(
    total_duration_sec: int,
    prompt: str,
    output_path: str,
) -> str:
    """Generate background music of *total_duration_sec* seconds.

    It stitches together as many `MODEL_MAX_DURATION`-second segments as needed.
    The first segment is created solely from *prompt*; every subsequent segment
    is conditioned on **all** segments generated so far via
    `_generate_melody_with_audio` to preserve musical coherence across the
    entire track.

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

    # Load the MusicGen model once for the full-length generation.
    load_model_resources()

    # Determine total target length in milliseconds.
    podcast_duration_ms = total_duration_sec * 1000

    segment_ms = MODEL_MAX_DURATION * 1000
    segments_needed = ceil(podcast_duration_ms / segment_ms)

    # Temporary storage for segment WAVs.
    tmp_dir = os.path.join(os.path.dirname(output_path), "tmp_segments")
    os.makedirs(tmp_dir, exist_ok=True)

    segment_paths: List[str] = []

    # 1) First segment from prompt only.
    first_path = os.path.join(tmp_dir, "segment_0.wav")
    segment_paths.append(_generate_melody(prompt, output_path=first_path))

    # Keep track of everything that has been generated so far so that the model
    # can take the **entire** melody as context for the next segment (not just
    # the immediate predecessor).
    cumulative_melody = AudioSegment.from_wav(first_path)

    # 2) Subsequent segments conditioned on the cumulative audio so far.
    for idx in range(1, segments_needed):
        # Persist the current cumulative melody so the model can use it as a
        # chroma guide.  (Over-write the same file each iteration to save disk
        # space.)
        cumulative_path = os.path.join(tmp_dir, "cumulative_prev.wav")
        cumulative_melody.export(cumulative_path, format="wav")

        seg_dir = os.path.join(tmp_dir, f"segment_{idx}")
        os.makedirs(seg_dir, exist_ok=True)

        conditioned_path = _generate_melody_with_audio(
            audio_path=cumulative_path,
            descriptions=prompt,
            output_dir=seg_dir,
        )[0]
        segment_paths.append(conditioned_path)

        # Update the cumulative melody with the newly generated segment so that
        # the next iteration has the full context.
        cumulative_melody += AudioSegment.from_wav(conditioned_path)

    # Concatenate and trim to exact duration.
    full_melody = AudioSegment.empty()
    for p in segment_paths:
        full_melody += AudioSegment.from_wav(p)

    full_melody = full_melody[:podcast_duration_ms]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    full_melody.export(output_path, format="wav")

    # Cleanup temp files.
    for p in segment_paths:
        if os.path.exists(p):
            os.remove(p)
    # Remove the cumulative tmp file if present.
    cumulative_tmp = os.path.join(tmp_dir, "cumulative_prev.wav")
    if os.path.exists(cumulative_tmp):
        os.remove(cumulative_tmp)

    # Recursively remove the entire temporary directory tree (including any
    # empty sub-directories that were created for intermediate segments).
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir, ignore_errors=True)

    # Release model resources now that we're done.
    unload_model_resources()

    return os.path.abspath(output_path)
