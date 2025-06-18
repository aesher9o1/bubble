import os
import pickle
import random
import time
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
import logging

class YouTubeUploader:
    """
    YouTube video uploader following the official YouTube API guide pattern.
    Based on: https://developers.google.com/youtube/v3/guides/uploading_a_video
    """
    
    # YouTube API scopes
    SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
    
    # Maximum number of times to retry before giving up
    MAX_RETRIES = 10
    
    # Always retry when an HttpError with one of these status codes is raised
    RETRIABLE_STATUS_CODES = [500, 502, 503, 504]
    
    def __init__(self, token_file='token.pickle'):
        """
        Initialize the YouTube uploader.
        Always uses 'credentials.json' for OAuth2 client secrets.
        
        Args:
            token_file (str): Path to store the OAuth2 token pickle file
        """
        self.client_secrets_file = 'credentials.json'  # Always use this file
        self.token_file = token_file
        self.youtube = None
        self._authenticate()
    
    @classmethod
    def for_server(cls, token_file='token.pickle'):
        """
        Create a YouTubeUploader instance for server use.
        Always uses 'credentials.json' for OAuth2 client secrets.
        
        Args:
            token_file (str): Path to store the OAuth2 token pickle file
            
        Returns:
            YouTubeUploader: Configured uploader instance
        """
        return cls(token_file=token_file)
    
    def _authenticate(self):
        """
        Authenticate with YouTube following the official guide pattern.
        Uses modern google-auth libraries instead of deprecated oauth2client.
        """
        creds = None
        
        # Load existing token if available
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, 'rb') as token:
                    creds = pickle.load(token)
                logging.info(f"Loaded existing credentials from {self.token_file}")
            except Exception as e:
                logging.warning(f"Failed to load existing token: {e}")
                creds = None
        
        # If there are no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logging.info("Token refreshed successfully.")
                except Exception as e:
                    logging.warning(f"Token refresh failed: {e}. Re-authenticating...")
                    creds = None
            
            # If we still don't have valid credentials, authenticate
            if not creds or not creds.valid:
                # Perform authentication using the modern approach
                creds = self._get_authenticated_credentials()
                
                # Ensure we got valid credentials
                if not creds:
                    raise Exception("Authentication failed - no credentials returned")
            
            # Save the credentials for the next run
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
                logging.info(f"Credentials saved to {self.token_file}")
        
        # Build the YouTube service
        self.youtube = build('youtube', 'v3', credentials=creds)
        logging.info("YouTube service initialized successfully.")
    
    def _get_authenticated_credentials(self):
        """
        Get authenticated credentials following the official guide pattern.
        Modern equivalent of oauth2client.tools.run_flow().
        
        Returns:
            Credentials: The authenticated credentials
        """
        flow = InstalledAppFlow.from_client_secrets_file(
            self.client_secrets_file, self.SCOPES
        )
        
        print("\n" + "="*60)
        print("YOUTUBE AUTHENTICATION REQUIRED")
        print("="*60)
        
        # Try the modern equivalent of run_flow() - local server with manual URL
        try:
            print("Starting local authentication server...")
            print("You'll need to copy and paste a URL into your browser.")
            print("="*60)
            
            # This is the modern equivalent of oauth2client.tools.run_flow()
            # It automatically handles the redirect URI and local server
            creds = flow.run_local_server(
                port=0,  # Use any available port
                open_browser=False,  # Don't open browser automatically (server environment)
                bind_addr='127.0.0.1'  # Bind to localhost
            )
            
            print("✅ Authentication successful!")
            return creds
            
        except Exception as e:
            logging.warning(f"Local server authentication failed: {e}")
            print(f"\n⚠️ Local server authentication failed: {e}")
            
            # Fallback to console-based authentication
            fallback_creds = self._console_auth_fallback(flow)
            if not fallback_creds:
                raise Exception("Both local server and console authentication failed")
            return fallback_creds
    
    def _console_auth_fallback(self, flow):
        """
        Fallback console authentication when automatic method fails.
        
        Args:
            flow: The OAuth2 flow object
            
        Returns:
            Credentials: The authenticated credentials
        """
        print("\n" + "="*60)
        print("FALLBACK AUTHENTICATION")
        print("="*60)
        print("Automatic authentication failed. Using manual method.")
        print("Make sure your OAuth client is configured as 'Desktop application'")
        print("="*60)
        
        try:
            # Use the built-in console flow
            auth_url, _ = flow.authorization_url(prompt='consent')
            
            print("\n1. Open this URL in your browser:")
            print(f"   {auth_url}")
            print("\n2. Complete the authorization")
            print("3. Copy the authorization code")
            
            auth_code = input("\nEnter the authorization code: ").strip()
            
            if not auth_code:
                raise Exception("No authorization code provided")
            
            flow.fetch_token(code=auth_code)
            print("✅ Authentication successful!")
            return flow.credentials
            
        except Exception as e:
            print(f"\n❌ Authentication failed: {e}")
            print("\nTroubleshooting tips:")
            print("1. Make sure your OAuth client type is 'Desktop application'")
            print("2. Check that the YouTube Data API v3 is enabled")
            print("3. Verify your credentials.json file is correct")
            print("4. Make sure the file contains 'installed' not 'web' configuration")
            raise Exception(f"Console authentication failed: {e}")

    def upload_video(self, video_file, title, description="", tags=None, category_id="22", 
                    privacy_status="private"):
        """
        Upload a video to YouTube following the official guide pattern.
        
        Args:
            video_file (str): Path to the video file to upload
            title (str): Video title
            description (str): Video description  
            tags (list): List of tags for the video
            category_id (str): YouTube category ID (default: "22" for People & Blogs)
            privacy_status (str): Privacy status - "private", "public", "unlisted"
            
        Returns:
            dict: Response from YouTube API containing video ID and other details
        """
        if not os.path.exists(video_file):
            raise FileNotFoundError(f"Video file '{video_file}' not found.")
        
        if tags is None:
            tags = []
        
        # Prepare video metadata following official guide structure
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags,
                'categoryId': category_id
            },
            'status': {
                'privacyStatus': privacy_status,
                'selfDeclaredMadeForKids': False
            }
        }
        
        # Create media upload object (following official guide)
        media = MediaFileUpload(
            video_file,
            chunksize=-1,  # Upload entire file in single request
            resumable=True
        )
        
        try:
            # Call the API's videos.insert method (following official guide)
            insert_request = self.youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            # Use resumable upload with retry logic (following official guide)
            response = self._resumable_upload(insert_request)
            return response
            
        except HttpError as e:
            logging.error(f"An HTTP error occurred: {e}")
            raise
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            raise
    
    def _resumable_upload(self, insert_request):
        """
        Resumable upload with exponential backoff strategy.
        Following the official guide pattern exactly.
        
        Args:
            insert_request: The YouTube API insert request
            
        Returns:
            dict: Response from the API
        """
        response = None
        error = None
        retry = 0
        
        while response is None:
            try:
                print("Uploading file...")
                status, response = insert_request.next_chunk()
                if response is not None:
                    if 'id' in response:
                        print(f"Video id '{response['id']}' was successfully uploaded.")
                        logging.info(f"Video uploaded successfully. Video ID: {response['id']}")
                        return response
                    else:
                        raise Exception(f"Upload failed with unexpected response: {response}")
                        
            except HttpError as e:
                if e.resp.status in self.RETRIABLE_STATUS_CODES:
                    error = f"A retriable HTTP error {e.resp.status} occurred:\n{e.content}"
                else:
                    raise
                    
            except Exception as e:
                error = f"A retriable error occurred: {e}"
            
            if error is not None:
                print(error)
                retry += 1
                if retry > self.MAX_RETRIES:
                    raise Exception("No longer attempting to retry.")
                
                max_sleep = 2 ** retry
                sleep_seconds = random.random() * max_sleep
                print(f"Sleeping {sleep_seconds} seconds and then retrying...")
                time.sleep(sleep_seconds)
                error = None  # Reset error for next iteration
