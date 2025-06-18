from openai import OpenAI
client = OpenAI()

def generate_podcast(title: str, summary: str) -> str:
    prompt = f"""You are a master horror storyteller. Create a spine-chilling horror story transcript based on the following title and summary:

Title: {title}
Summary: {summary}

Your transcript must:
1. Label segments with <neutral></neutral> <angry></angry> <scared></scared> <silence>SECONDS</silence> example <neutral>Final rule: "If you see your own username,</neutral> <angry>STOP</angry> <neutral>reading."</neutral>.
2. Do not change emotions if not required. Start with neutral, end with neutral and keep the emotions consistent.
3. Start with an IMMEDIATELY gripping hook (first 3-5 seconds) that makes viewers stop scrolling
4. Keep the story under 70 seconds total
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
    return f"<silence>2</silence>           {response.choices[0].message.content}       <silence>2</silence>"

def format_podcast_for_youtube(article_title, podcast_text, article_url=None):
    """
    Format podcast content for YouTube upload using GPT-3.5 to generate title, description, and tags.
    
    Args:
        article_title (str): The original article title
        podcast_text (str): The podcast transcript/content
        article_url (str): Optional URL to the original article
        
    Returns:
        tuple: (title, description, tags)
    """
    prompt = f"""You are a YouTube content optimizer. Create engaging YouTube metadata for a horror podcast video based on the following:

Article Title: {article_title}
Podcast Content: {podcast_text}
{f"Original Article URL: {article_url}" if article_url else ""}

Generate the following in this exact format:

TITLE: [Create a compelling YouTube title under 100 characters that includes emojis and hooks viewers. Make it horror/thriller themed and clickable]

DESCRIPTION: [Create a detailed YouTube description that includes:
- An engaging hook in the first line
- Brief summary of the content
- Mention that it's AI-generated
- Call to action for likes/subscribes
- Relevant hashtags
- Credit to original source if URL provided]

TAGS: [Provide 8-12 relevant tags as a comma-separated list, focusing on horror, podcast, AI, and content-specific keywords]

Make everything optimized for YouTube's algorithm and viewer engagement. Keep the horror/thriller theme prominent."""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=800
    )
    
    # Parse the response
    content = response.choices[0].message.content
    
    # Extract title, description, and tags
    lines = content.split('\n')
    title = ""
    description = ""
    tags = []
    
    current_section = None
    for line in lines:
        line = line.strip()
        if line.startswith("TITLE:"):
            title = line.replace("TITLE:", "").strip()
            current_section = "title"
        elif line.startswith("DESCRIPTION:"):
            description = line.replace("DESCRIPTION:", "").strip()
            current_section = "description"
        elif line.startswith("TAGS:"):
            tags_line = line.replace("TAGS:", "").strip()
            tags = [tag.strip() for tag in tags_line.split(',')]
            current_section = "tags"
        elif current_section == "description" and line:
            description += "\n" + line
    
    # Fallback in case parsing fails
    if not title:
        title = f"🎧 Horror Podcast: {article_title}"
    if not description:
        description = f"AI-generated horror podcast based on: {article_title}\n\n{podcast_text[:300]}..."
    if not tags:
        tags = ["horror", "podcast", "ai generated", "scary stories", "thriller", "audio content"]
    
    return title, description, tags
