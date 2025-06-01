from openai import OpenAI
client = OpenAI()


def get_prompt_for_podcast_music(summary: str) -> str:
    prompt = f"""Given the story summary:
{summary}
Given the horror story:  {summary}

write comma seperated sounds happening in the background
"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ],
    )

    return response.choices[0].message.content


def generate_podcast(title: str, summary: str) -> str:
    prompt = f"""You are a master horror storyteller specializing in creating viral Instagram reel content. Create a spine-chilling horror story transcript based on the following title and summary:

Title: {title}
Summary: {summary}

Your transcript must:
1. Start with an IMMEDIATELY gripping hook (first 3-5 seconds) that makes viewers stop scrolling
2. Keep the story under 60 seconds total
3. Include dramatic pauses and tension-building moments
4. End with a shocking twist or revelation
5. Use short, impactful sentences
6. Add suspense through strategic pauses and timing
7. The transcript should be Text to speech friendly - provide ONLY the story text without any timestamps, formatting, or technical instructions
8. Use natural pauses in the text (like ellipses or commas) to indicate where the TTS should pause

Remember: This is for Instagram reels, so every second counts. Make it impossible to scroll past."""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a master horror storyteller who creates viral Instagram reel content. Your stories are short, impactful, and impossible to scroll past. Provide only the pure story text without any timestamps or formatting instructions."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.8,
        max_tokens=1000
    )
    
    return response.choices[0].message.content
