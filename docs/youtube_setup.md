# YouTube API Setup Guide

This guide explains how to set up YouTube API credentials and handle authentication in different environments.

## Table of Contents
- [OAuth Credentials Setup](#oauth-credentials-setup)
- [Authentication Methods](#authentication-methods)
- [Local Development](#local-development)
- [Remote/Headless Environments](#remoteheadless-environments)
- [Troubleshooting](#troubleshooting)

## OAuth Credentials Setup

### 1. Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to "APIs & Services" > "Library"
4. Search for "YouTube Data API v3" and enable it

### 2. Create OAuth 2.0 Credentials
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Select "Desktop application" as the application type
4. Name your client (e.g., "YouTube Podcast Uploader")

### 3. Configure Redirect URIs
For the OAuth client, add these authorized redirect URIs:

**For Local Development:**
```
http://localhost:8080/
http://localhost:8081/
http://127.0.0.1:8080/
```

**For Remote/Headless Environments:**
```
urn:ietf:wg:oauth:2.0:oob
```

### 4. Download Credentials
1. Download the JSON file containing your credentials
2. Rename it to `credentials.json`
3. Place it in your project root directory

## Authentication Methods

The YouTube uploader supports two authentication methods:

### Local Server Authentication (Default)
- **Best for:** Local development, desktop applications
- **How it works:** Opens a browser window automatically
- **Pros:** Seamless, no manual steps
- **Cons:** Doesn't work on remote servers or headless environments

### Console-Based Authentication
- **Best for:** Remote servers, Docker containers, headless environments
- **How it works:** Provides a URL to visit manually, you copy/paste the authorization code
- **Pros:** Works everywhere, including remote environments
- **Cons:** Requires manual interaction

## Local Development

For local development, use the default authentication method:

```python
from youtube_uploader import YouTubeUploader

# This will open a browser window automatically
uploader = YouTubeUploader(
    credentials_file='credentials.json',
    use_local_server=True  # Default behavior
)
```

## Remote/Headless Environments

For remote servers, containers, or environments without browser access:

```python
from youtube_uploader import YouTubeUploader

# This will provide a URL to visit manually
uploader = YouTubeUploader(
    credentials_file='credentials.json',
    use_local_server=False  # Forces console-based auth
)
```

### Console Authentication Flow
When using `use_local_server=False`, you'll see:

1. A URL to visit in your browser
2. Instructions to authorize the application
3. A prompt to enter the authorization code manually

Example output:
```
Please visit this URL to authorize this application: https://accounts.google.com/o/oauth2/auth?...
Enter the authorization code: [paste code here]
```

## Automatic Fallback

The uploader can automatically try both methods:

```python
# Try local server first, fallback to console if it fails
uploader = YouTubeUploader(
    credentials_file='credentials.json',
    use_local_server=True  # Will fallback to console on failure
)
```

## Token Refresh

Once authenticated, the uploader automatically:
- Saves tokens in `token.pickle` file
- Refreshes expired tokens automatically
- Only requires re-authentication if refresh token expires (typically after 6 months of inactivity)

## Environment-Specific Examples

### Docker Containers
```python
# In Docker containers, always use console authentication
uploader = YouTubeUploader(use_local_server=False)
```

### GitHub Actions / CI/CD
```python
# For automated environments, pre-generate tokens locally first
# Then include token.pickle in your deployment
uploader = YouTubeUploader()  # Will use existing token.pickle
```

### Cloud Functions / Lambda
```python
# Store token.pickle in cloud storage and load it before authentication
uploader = YouTubeUploader(use_local_server=False)
```

## Troubleshooting

### "redirect_uri_mismatch" Error
- **Cause:** Redirect URI not configured in Google Cloud Console
- **Solution:** Add `http://localhost:8080/` to authorized redirect URIs

### "This app isn't verified" Warning
- **Cause:** OAuth app is in testing mode
- **Solution:** This is normal for personal use. Click "Advanced" > "Go to [App Name] (unsafe)"

### "Access blocked: This app's request" Error
- **Cause:** OAuth scopes not properly configured
- **Solution:** Ensure YouTube Data API v3 is enabled and scopes are correct

### Browser Doesn't Open in Remote Environment
- **Cause:** No display server available
- **Solution:** Use `use_local_server=False` for console-based authentication

### Token Refresh Fails
- **Cause:** Refresh token expired or revoked
- **Solution:** Delete `token.pickle` and re-authenticate

## Security Best Practices

1. **Never commit credentials.json:** Add it to `.gitignore`
2. **Protect token.pickle:** Contains access tokens, treat as sensitive
3. **Use minimal scopes:** Only request YouTube upload permission
4. **Regular rotation:** Re-generate credentials periodically
5. **Environment variables:** Consider using environment variables for credentials in production

## Testing Authentication

Use the provided test script to verify your setup:

```bash
python test/youtube_example.py
```

This will test both authentication methods and help identify any configuration issues.

## Prerequisites

1. A Google account with access to YouTube
2. A YouTube channel where you want to upload videos

## Configuration Options

In `main.py`, you can modify the YouTube upload settings:

```python
youtube_response = youtube_uploader.upload_video(
    video_file=video_results['video_with_audio'],
    title=youtube_title,
    description=youtube_description,
    tags=youtube_tags,
    privacy_status="private"  # Options: "private", "public", "unlisted"
)
```

### Privacy Status Options:
- `"private"`: Only you can see the video
- `"unlisted"`: Anyone with the link can see the video
- `"public"`: Everyone can find and view the video

### Video Categories:
You can also specify a category ID (default is "22" for People & Blogs):
- Education: "27"
- News & Politics: "25" 
- Science & Technology: "28"
- Entertainment: "24"

## Troubleshooting

### Common Issues:

1. **"Credentials file not found"**
   - Make sure `credentials.json` is in your project root directory
   - Verify the file was downloaded correctly from Google Cloud Console

2. **"The OAuth client was invalid"**  
   - Check that YouTube Data API v3 is enabled in your Google Cloud project
   - Verify your OAuth consent screen is properly configured

3. **"Access blocked: This app's request is invalid"**
   - Make sure your app is in "Testing" mode and your Google account is added as a test user
   - Or publish your app (requires verification for production use)

4. **"Quota exceeded"**
   - YouTube API has daily quotas. Each upload costs ~1600 quota units
   - Default quota is 10,000 units per day (about 6 uploads)
   - You can request quota increases in Google Cloud Console

### File Structure:
```
your-project/
├── main.py
├── youtube_uploader.py
├── credentials.json          # OAuth2 credentials (download from Google Cloud)
├── token.pickle             # Generated automatically after first auth
└── ...
```

## Security Notes

- Never commit `credentials.json` or `token.pickle` to version control
- Add them to your `.gitignore` file
- Keep your credentials secure and don't share them

## Testing

You can test the YouTube upload functionality by:
1. Setting `privacy_status="private"` initially
2. Running your script
3. Checking your YouTube Studio for the uploaded video
4. Once confirmed working, change to "public" or "unlisted" as needed 