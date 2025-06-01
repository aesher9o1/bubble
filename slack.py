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

    def send_audio_file(self, channel, file_path, initial_comment=None, thread_ts=None):
        """
        Send an audio file to a specific Slack channel.
        
        Args:
            channel (str): The channel ID or name to send the file to
            file_path (str): Path to the audio file
            initial_comment (str, optional): Message to send with the file
            thread_ts (str, optional): The timestamp of the parent message if replying in a thread
        
        Returns:
            dict: The response from Slack API
        
        Raises:
            SlackApiError: If there's an error sending the file
            FileNotFoundError: If the specified file doesn't exist
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found at: {file_path}")

        try:
            # Upload the file
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