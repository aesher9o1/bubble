from openai import OpenAI
client = OpenAI()

def generate_podcast(title: str, summary: str) -> str:
    prompt = f"""You are a master horror storyteller. Create a spine-chilling horror story transcript based on the following title and summary:

Title: {title}
Summary: {summary}

Your transcript must:
1. Start with an IMMEDIATELY gripping hook (first 3-5 seconds) that makes viewers stop scrolling
2. Keep the story under 90 seconds total
3. Include dramatic pauses and tension-building moments
4. End with a shocking twist or revelation
5. Use short, impactful sentences
6. Add some spaces (blank: " ") or punctuations (e.g. "," ".") to explicitly introduce some pauses.
7. The transcript should be Text to speech friendly - provide ONLY the story text without any timestamps, formatting, or technical instructions

Remember: This is for Instagram reels, so every second counts. Make it impossible to scroll past."""

    response = client.chat.completions.create(
        model="gpt-4.1-2025-04-14",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.8,
        max_tokens=1000
    )
    
    #added fake silences 
    return f"           {response.choices[0].message.content}       "
