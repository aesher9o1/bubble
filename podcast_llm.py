import re
import logging
from openai import OpenAI
client = OpenAI()

def generate_podcast(title: str, summary: str) -> str:
    prompt = f"""You are a master horror storyteller. Create a spine-chilling horror story transcript based on the following title and summary:

Title: {title}
Summary: {summary}

Your transcript must:
1. Label segments with <neutral></neutral> <scared></scared> <silence>SECONDS</silence> example <neutral> Final rule: "If you see your own username,</neutral> <angry>STOP</angry> <neutral>reading."</neutral>.
2. Do not change emotions if not required. Start with neutral, end with neutral and make sure the tags are opened and closed correctly.
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
    return f"<silence>1</silence>           {response.choices[0].message.content}       <silence>1</silence>"

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
- Call to action for likes/subscribes
- Relevant hashtags]

TAGS: [Provide 8-12 relevant tags as a comma-separated list, focusing on horror, podcast, and content-specific keywords]

Make everything optimized for YouTube's algorithm and viewer engagement. Keep the horror/thriller theme prominent."""

    try:
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
        print(f"DEBUG: GPT response:\n{content}")  # Debug logging
        
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
        
        print(f"DEBUG: Parsed title: '{title}'")  # Debug logging
        print(f"DEBUG: Parsed description length: {len(description)}")  # Debug logging
        print(f"DEBUG: Parsed tags count: {len(tags)}")  # Debug logging
        
    except Exception as e:
        print(f"ERROR: GPT request failed: {e}")
        title = ""
        description = ""
        tags = []
    
    # Sanitize and validate title
    if title:
        # Remove problematic characters that YouTube might reject
        title = re.sub(r'[<>:"\\|?*]', '', title)  # Remove invalid filename characters
        title = title.strip()
        
        # Ensure title is not too long (YouTube limit is 100 characters)
        if len(title) > 100:
            title = title[:97] + "..."
    
    # Fallback in case parsing fails or title is invalid
    if not title or len(title.strip()) == 0:
        title = f"🎧 Horror Podcast: {article_title[:50]}"  # Ensure we don't exceed length limits
        print(f"WARNING: Using fallback title: '{title}'")
    
    if not description:
        description = f"AI-generated horror podcast based on: {article_title}\n\n{podcast_text[:300]}..."
        print("WARNING: Using fallback description")
    
    if not tags:
        tags = ["horror", "podcast", "ai generated", "scary stories", "thriller", "audio content"]
        print("WARNING: Using fallback tags")
    
    # Final validation
    if not title or len(title.strip()) == 0:
        raise ValueError("Title is still empty after all fallbacks")
    
    print(f"FINAL: Title='{title}', Description length={len(description)}, Tags count={len(tags)}")
    
    return title, description, tags
