import feedparser
import requests
import json
import os

def get_latest_article():
    # URL of the RSS feed
    feed_url = "https://www.reddit.com/r/nosleep.rss"
    title_file = "latest_title.json"
    
    try:
        response = requests.get(feed_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'})
        feed = feedparser.parse(response.content)
        if not feed.entries:
            return None
            
        # Load previous title if exists
        previous_title = None
        if os.path.exists(title_file):
            with open(title_file, 'r') as f:
                try:
                    previous_title = json.load(f).get('title')
                except json.JSONDecodeError:
                    pass
        
        # Find the first article that doesn't match the previous title
        for entry in feed.entries:
            if entry.title != previous_title:
                # Save the new title
                with open(title_file, 'w') as f:
                    json.dump({'title': entry.title}, f)
                
                # Extract relevant information
                article_info = {
                    'title': entry.title,
                    'link': entry.link,
                    'published': entry.published,
                    'summary': entry.summary
                }
                
                return article_info
        
        # If all articles match the previous title, return None
        return None
            
    except Exception as e:
        return None
