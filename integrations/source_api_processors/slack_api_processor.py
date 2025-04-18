import logging

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from integrations.processor import Processor

logger = logging.getLogger(__name__)


class SlackApiProcessor(Processor):
    client = None

    def __init__(self, bot_auth_token):
        self.__bot_auth_token = bot_auth_token
        self.client = WebClient(token=self.__bot_auth_token)

    def fetch_channel_info(self, channel_id):
        try:
            response = self.client.conversations_info(channel=channel_id)
            if response:
                if 'ok' in response and response['ok']:
                    channel_info = response['channel']
                    return channel_info
        except Exception as e:
            logger.error(f"Exception occurred while fetching channel info for channel_id: {channel_id} with error: {e}")
        return None

    def fetch_conversation_history(self, team_id: str, channel_id: str, latest_timestamp: str, oldest_timestamp: str,
                                   next_cursor=None):
        if not channel_id or not latest_timestamp or oldest_timestamp is None or not team_id:
            logger.error(f"Invalid arguments provided for fetch_conversation_history")
            return None

        if oldest_timestamp is not None and oldest_timestamp != '':
            return self.client.conversations_history(channel=channel_id, cursor=next_cursor,
                                                     latest=latest_timestamp,
                                                     oldest=oldest_timestamp, limit=100,
                                                     timeout=300)
        else:
            return self.client.conversations_history(channel=channel_id, cursor=next_cursor,
                                                     latest=latest_timestamp, limit=100,
                                                     timeout=300)

    def send_bot_message(self, channel_id: str, text_message=None, reply_to=None, blocks=None):
        try:
            method_params = {'channel': channel_id}
            if blocks:
                method_params['blocks'] = blocks
            if text_message:
                method_params['text'] = text_message
            if reply_to:
                method_params['thread_ts'] = reply_to
            message_response = self.client.chat_postMessage(**method_params)
            return message_response.get('ts')
        except SlackApiError as e:
            logger.error(f"Error posting slack message: {e}")

    def create_channel(self, channel_name: str):
        try:
            result = self.client.conversations_create(
                name=channel_name
            )
            if result and 'ok' in result and result['ok'] and 'channel' in result and 'id' in result['channel']:
                return result['channel']['id']
            return None
        except SlackApiError as e:
            logger.error(f"Error posting slack message: {e}")
            return None

    def invite_user_to_channel(self, channel_id, emails):
        try:
            result = self.client.conversations_inviteShared(
                channel=channel_id,
                emails=emails,
                external_limited=True
            )
            if result and 'ok' in result and result['ok']:
                return True
            return False
        except SlackApiError as e:
            logger.error(f"Error posting slack message: {e}")

    def test_connection(self):
        try:
            self.client.auth_test()
            return True
        except SlackApiError as e:
            logger.error('Auth test failed:', e.response['error'])
            raise e

    def files_upload(self, channel_id, file_path, title='Report', initial_comment='Report', thread_ts=None):
        try:
            result = self.client.files_upload_v2(
                channels=channel_id,
                file=file_path,
                title=title,
                initial_comment=initial_comment,
                thread_ts=thread_ts
            )
            if result and 'ok' in result and result['ok']:
                return True
            return False
        except SlackApiError as e:
            logger.error(f"Error posting slack message: {e}")
            return False
