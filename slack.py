import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

class SlackMessenger:
    def __init__(self, token=None):
        """
        Initialize the Slack messenger with a bot token.
        If no token is provided, it will try to get it from SLACK_BOT_TOKEN environment variable.
        """
        self.token = token or os.environ.get("SLACK_BOT_TOKEN")
        if not self.token:
            raise ValueError("Slack bot token is required. Either pass it to the constructor or set SLACK_BOT_TOKEN environment variable.")
        
        self.client = WebClient(token=self.token)

    def send_message(self, channel, message, thread_ts=None):
        """
        Send a message to a specific Slack channel.
        
        Args:
            channel (str): The channel ID or name to send the message to
            message (str): The message text to send
            thread_ts (str, optional): The timestamp of the parent message if replying in a thread
        
        Returns:
            dict: The response from Slack API
        
        Raises:
            SlackApiError: If there's an error sending the message
        """
        try:
            response = self.client.chat_postMessage(
                channel=channel,
                text=message,
                thread_ts=thread_ts
            )
            return response
        except SlackApiError as e:
            print(f"Error sending message: {e.response['error']}")
            raise

    def send_audio_file(self, channel, file_path=None, file_uploads=None, initial_comment=None, thread_ts=None):
        """
        Send audio file(s) to a specific Slack channel.
        
        Args:
            channel (str): The channel ID or name to send the file to
            file_path (str, optional): Path to a single audio file (for backward compatibility)
            file_uploads (list, optional): List of file dictionaries with keys: 'file', 'filename', 'title'
            initial_comment (str, optional): Message to send with the file(s)
            thread_ts (str, optional): The timestamp of the parent message if replying in a thread
        
        Returns:
            dict: The response from Slack API
        
        Raises:
            SlackApiError: If there's an error sending the file
            FileNotFoundError: If the specified file doesn't exist
            ValueError: If neither file_path nor file_uploads is provided
        """
        if file_uploads:
            # Multiple files mode
            for file_upload in file_uploads:
                if not os.path.exists(file_upload['file']):
                    raise FileNotFoundError(f"Audio file not found at: {file_upload['file']}")
            
            try:
                response = self.client.files_upload_v2(
                    file_uploads=file_uploads,
                    channel=channel,
                    initial_comment=initial_comment,
                    thread_ts=thread_ts
                )
                return response
            except SlackApiError as e:
                print(f"Error uploading audio files: {e.response['error']}")
                raise
                
        elif file_path:
            # Single file mode (backward compatibility)
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Audio file not found at: {file_path}")

            try:
                response = self.client.files_upload_v2(
                    channel=channel,
                    file=file_path,
                    initial_comment=initial_comment,
                    thread_ts=thread_ts
                )
                return response
            except SlackApiError as e:
                print(f"Error uploading audio file: {e.response['error']}")
                raise
        else:
            raise ValueError("Either file_path or file_uploads must be provided")