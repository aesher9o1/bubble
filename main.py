from dotenv import load_dotenv
load_dotenv()

from rss_reader import get_latest_article
from podcast_llm import generate_podcast
from melody_generator import generate_full_melody
from f5tts import generate_audio
from slack import SlackMessenger
from pydub import AudioSegment

def merge_audio_with_melody(podcast_path, melody_path, output_path):
    """
    Merge podcast audio with background melody.
    If melody is shorter than podcast, repeat the melody to match podcast length.
    """
    # Load audio files
    podcast = AudioSegment.from_wav(podcast_path)
    melody = AudioSegment.from_wav(melody_path)
    
    # Get durations
    podcast_duration = len(podcast)
    melody_duration = len(melody)
    
    # If melody is shorter than podcast, repeat it to cover the entire podcast duration
    if melody_duration < podcast_duration:
        repeat_count = (podcast_duration // melody_duration) + 1
        extended_melody = melody * repeat_count
        extended_melody = extended_melody[:podcast_duration]
    else:
        extended_melody = melody[:podcast_duration]
    
    # Reduce melody volume to make it background music but keep it audible
    background_melody = extended_melody - 20  # Reduce by 20dB for audible but not overpowering background
    # Overlay the melody on the podcast
    merged_audio = podcast.overlay(background_melody)
    
    merged_audio.export(output_path, format="wav")
    return output_path

if __name__ == "__main__":
    latest_article = get_latest_article()
    
    podcast = generate_podcast(latest_article["title"], latest_article["summary"])
    music_prompt = "Dark, suspenseful track with low strings, slow tempo, spooky podcast intro"

    print(f"Music prompt: {music_prompt}")

    file_name = latest_article["title"].replace(" ", "_")
    
    output_podcast_path = f"output/{file_name}_podcast.wav"
    audio = generate_audio(podcast, output_path=output_podcast_path)

    output_melody_path = f"output/{file_name}_melody.wav"
    # Calculate podcast length in seconds (rounded up)
    podcast_audio_seg = AudioSegment.from_wav(audio)
    import math
    total_duration_sec = math.ceil(len(podcast_audio_seg) / 1000)

    # Generate background melody matching the podcast duration
    melody = generate_full_melody(total_duration_sec, music_prompt, output_melody_path)
    
    # Merge the podcast audio with background melody
    output_merged_path = f"output/{file_name}_merged.wav"
    merged_audio = merge_audio_with_melody(audio, melody, output_merged_path)
    
    slack_messenger = SlackMessenger()
    slack_messenger.send_audio_file(channel="C08TN9BHWBG", file_path=merged_audio, initial_comment=podcast)
    
    # # Clean up all audio files
    # for file_path in [audio, melody, merged_audio]:
    #     if os.path.exists(file_path):
    #         os.remove(file_path)
    #         print(f"Successfully deleted audio file: {file_path}")

    