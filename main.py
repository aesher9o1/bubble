from dotenv import load_dotenv
load_dotenv()

from rss_reader import get_latest_article
from podcast_llm import generate_podcast
from audio_clipper import get_random_audio_segment
from f5tts import generate_emotion_audio
from video_clipper import process_video_with_audio
from slack import SlackMessenger
from pydub import AudioSegment
import random
import string 
import os
import re

def strip_xml_tags(text):
    """
    Strip XML-like tags from text, keeping only the content inside the tags.
    For silence tags like <silence>2</silence>, removes the entire tag.
    """
    # Remove silence tags completely (including their content)
    text = re.sub(r'<silence>\d*</silence>', '', text)
    
    # Remove all other XML tags but keep their content
    text = re.sub(r'<[^>]+>(.*?)</[^>]+>', r'\1', text)
    
    # Clean up extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

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

    # Generate a random name with 8 characters
    file_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    
    output_podcast_path = f"output/{file_name}_podcast.wav"
    audio = generate_emotion_audio(podcast, output_path=output_podcast_path)

    output_melody_path = f"output/{file_name}_melody.wav"
    # Calculate podcast length in seconds (rounded up)
    podcast_audio_seg = AudioSegment.from_wav(audio)
    import math
    total_duration_sec = math.ceil(len(podcast_audio_seg) / 1000)

    # Generate background melody matching the podcast duration
    melody = get_random_audio_segment(total_duration_sec, output_melody_path)
    
    # Merge the podcast audio with background melody
    output_merged_path = f"output/{file_name}_merged.wav"
    merged_audio = merge_audio_with_melody(audio, melody, output_merged_path)
    
    # Process video with the merged audio
    video_results = process_video_with_audio(total_duration_sec, merged_audio, file_name)
    
    slack_messenger = SlackMessenger()
    
    # Strip XML tags from podcast text for Slack message
    clean_podcast_text = strip_xml_tags(podcast)
    
    # Prepare file uploads for video segment, melody, and video with audio
    file_uploads = [
        {
            'file': video_results['video_segment'],
            'filename': f"{file_name}_video_segment.mp4",
            'title': f"{latest_article['title']} - Video Segment (No Audio)"
        },
        {
            'file': melody,
            'filename': f"{file_name}_melody.wav", 
            'title': f"{latest_article['title']} - Background Melody"
        },
        {
            'file': video_results['video_with_audio'],
            'filename': f"{file_name}_video_with_audio.mp4",
            'title': f"{latest_article['title']} - Video with Podcast and Music"
        }
    ]
    
    # Send all files in a single API call with cleaned text
    response = slack_messenger.send_audio_file(
        channel="C08TN9BHWBG", 
        file_uploads=file_uploads, 
        initial_comment=clean_podcast_text
    )
    
    # Clean up all audio and video files
    cleanup_files = [audio, melody, merged_audio, video_results['video_segment'], video_results['video_with_audio']]
    for file_path in cleanup_files:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Successfully deleted file: {file_path}")

    