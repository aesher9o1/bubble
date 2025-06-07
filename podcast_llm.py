from openai import OpenAI
client = OpenAI()

def generate_podcast(title: str, summary: str) -> str:
    prompt = f"""You are a master horror storyteller. Create a spine-chilling horror story transcript based on the following title and summary:

Title: {title}
Summary: {summary}

Your transcript must:
1. Label segments with <neutral></neutral> <angry></angry> <scared></scared> <surprised></surprised> <silence>SECONDS</silence> example <neutral>Final rule: "If you see your own username,</neutral> <angry>STOP</angry> <neutral>reading."</neutral>.
2. Do not change emotions if not required. Stick to neutral if confused. Make sure you close the tags.
3. Start with an IMMEDIATELY gripping hook (first 3-5 seconds) that makes viewers stop scrolling
4. Keep the story under 80 seconds total
5. Include dramatic pauses and tension-building moments
6. End with a shocking twist or revelation
7. Use short, impactful sentences
8. Add some spaces (blank: " ") or punctuations (e.g. "," ".") to explicitly introduce some pauses.
9. The transcript should be Text to speech friendly - provide ONLY the story text without any timestamps, formatting, or technical instructions. 
10. Do not use ALL CAPS.

Remember: This is for Instagram reels, so every second counts. Make it impossible to scroll past."""

    response = client.chat.completions.create(
        model="gpt-4.1-2025-04-14",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.8,
        max_tokens=1000
    )
    
    #added fake silences and 2 second silence at the end
    return f"           {response.choices[0].message.content}       <silence>2</silence>"
