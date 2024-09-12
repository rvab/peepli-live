import logging
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
import re
import json
import requests
from slack_sdk.errors import SlackApiError
from bedrock_prompt import invoke_bedrock_model
from bedrock_rag import getBedrockResponse
from constants import slack_bot_token, slack_app_token

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


def get_group_members(group_id):
    url = "https://slack.com/api/usergroups.users.list"
    headers = {
      "Authorization": f"Bearer {slack_bot_token}"
    }
    params = {
      "usergroup": group_id,
    }
    
    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    if data.get("ok"):
        return data.get("users")
    else:
        raise Exception(f"Failed to get members: {data.get('error')}")

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

def send_slack_message(channel_id, message, thread_ts=None):
    response = app.client.chat_postMessage(
        channel=channel_id,
        text=message,
        thread_ts=thread_ts
    )
    print(f"Message sent: {response['ts']}")

def get_user_id_from_collect_wish_text(text):
    pattern = r'Wish for <@([A-Z0-9]+)>'
    return re.findall(pattern, text)

# Event listener for mentions
@app.event("app_mention")
def handle_mention(event, say):
    logger.debug(f"Received message: {event}")
    print(f'TEsting johnnn - body: {event}')
    response = getBedrockResponse(input_text=event["text"])
    # say(response)
    send_slack_message(event["channel"], response, event["ts"])

@app.event("message")
def handle_message(body, message, say):
    event = body["event"]
    if event["channel_type"] == "im":
        text = event["text"]

        print(f'TEsting arunnn - body: {body} and message: {message}')

        print(f"Received message: {text}")
        if "thread_ts" in message:
            thread_ts = message["thread_ts"]
            channel_id = message["channel"]

            parent_message = get_parent_message(channel_id, thread_ts)

            if parent_message:
                print(f"Parent message text: {parent_message['text']}")
                from_user = event["user"]
                for_user = get_user_id_from_collect_wish_text(parent_message['text'])[0]
                print(f"For user: {for_user}")

                print(f"From user: {from_user}, For user: {for_user}")
                response = f"Recieved the following wish from you: {text}"
                # response = f"From user: <@{from_user}>, For user: <@{for_user}>, Wish: {text}"
                send_slack_message(event["channel"], response, event["ts"])
            else:
                print("Couldn't retrieve parent message")

        response = invoke_bedrock_model(prompt=text)
        json_response = json.loads(response['content'][0]['text'])
        to_users = json_response['to']
        from_users = json_response['from']

        users = []
        for from_user in from_users:
            if from_user.startswith('S'):
                users.extend(get_group_members(from_user))
            else:
                users.append(from_user)

        users = list(set(users))
        to_users = list(set(to_users))

        for user_id in users:
            for target_user in to_users:
                if target_user != user_id:
                    send_slack_message(user_id, f"Hello <@{user_id}>! Wish for <@{target_user}>, work anniversary")
        # response = getBedrockResponse(input_text=text)
        # say(response)

def main():
    handler = SocketModeHandler(app, slack_app_token)
    logger.info("Starting the bot...")
    handler.start()

if __name__ == "__main__":
    main()
