import logging
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
import re
import json

from slack_sdk.errors import SlackApiError
from bedrock import getBedrockResponse, invoke_bedrock_model
from constants import slack_bot_token, slack_app_token
import openai

load_dotenv()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


app = App(token=slack_bot_token)

@app.middleware  # Register a middleware to log all incoming events
def log_request(logger, body, next):
    logger.debug(f"Received event: {body}")
    return next()

@app.error
def custom_error_handler(error, body, logger):
    logger.exception(f"Error: {error}")
    logger.info(f"Request body: {body}")

# Event listener for mentions
@app.event("app_mention")
def handle_mention(event, say):
    logger.debug(f"Received message: {event}")
    say(f"You mentioned me, <@{event['user']}>!")

def get_user_ids_from_mentions(text):
    pattern = r'<@([A-Z0-9]+)>'
    return re.findall(pattern, text)


def get_parent_message(channel_id, thread_ts):
    try:
        result = app.client.conversations_replies(
            channel=channel_id,
            ts=thread_ts
        )

        if result["messages"] and len(result["messages"]) > 0:
            return result["messages"][0]
        else:
            return None
    except SlackApiError as e:
        print(f"Error: {e}")
        return None

def send_slack_message(channel_id, message):
    response = app.client.chat_postMessage(
        channel=channel_id,
        text=message
    )
    print(f"Message sent: {response['ts']}")


@app.event("message")
def handle_message(body, message, say):
    print(f"Received message 1234: {body}")
    event = body["event"]
    if event["channel_type"] == "im":
        user = event["user"]
        text = event["text"]


        # print(f"Received message: {text}")
        # if "thread_ts" in message:
        #     thread_ts = body["thread_ts"]
        #     channel_id = message["channel"]

        #     parent_message = get_parent_message(channel_id, thread_ts)
        #     say(f"This is a reply in a thread. Thread timestamp: {thread_ts}")

        #     if parent_message:

        #         print(f"Parent message text: {parent_message['text']}")
        #     else:
        #         print("Couldn't retrieve parent message")

        # user_ids = get_user_ids_from_mentions(text)

        # print(f"Extracted user IDs: {user_ids}")


        # for user_id in user_ids:
        #     send_slack_message(user_id, f"Hello <@{user_id}>! You were mentioned in a message.")

        response = invoke_bedrock_model(prompt=text)
        json_response = json.loads(response['content'][0]['text'])
        to = json_response['to']
        from_users = json_response['from']

        for user_id in from_users:
            send_slack_message(user_id, f"Hello <@{user_id}>! Wish for <@{to}>, work anniversary")

        # response = getBedrockResponse(input_text=text)
        # say(response)

def main():
    handler = SocketModeHandler(app, slack_app_token)
    logger.info("Starting the bot...")
    handler.start()

if __name__ == "__main__":
    main()
