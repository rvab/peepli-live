import logging
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
import re
import requests
import ast
import os

from slack_sdk.errors import SlackApiError
# from bedrock_prompt import classify_user_message
from openai_prompt import classify_user_message_openai
from bedrock_rag import get_kb_response
from constants import slack_bot_token, slack_app_token
from generate_card import generate_card_for_user
from load_employee_data import load_employee_data
import numpy as np
from datetime import datetime

from sqlite_helper import add_message_to_db, get_user_messages, get_distinct_wished_user_receiver_user_combinations

load_dotenv()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


app = App(token=slack_bot_token)

employee_data = load_employee_data()

def ordinal_suffix(n):
    if 11 <= n % 100 <= 13:
        return f"{n}th"
    else:
        suffixes = {1: "st", 2: "nd", 3: "rd"}
        return f"{n}{suffixes.get(n % 10, 'th')}"

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


def get_upcoming_anniversary(doj):

    today = datetime.today()

    current_year_anniversary = doj.replace(year=today.year)

    if current_year_anniversary < today:
        next_anniversary = doj.replace(year=today.year + 1)
    else:
        next_anniversary = current_year_anniversary

    years_completed = next_anniversary.year - doj.year

    return {
        'next_anniversary_date': next_anniversary.strftime('%Y-%m-%d'),
        'years_completed': ordinal_suffix(years_completed)
    }

def get_doj_of_user(user_id):
    user = get_slack_user_details(user_id)
    user_email = user['email']
    doj_row = employee_data[employee_data['Email'] == user_email]
    if not doj_row.empty:
        doj = doj_row['FTE Start Date'].values[0]
        print(f"The Date of Joining for {user_email} is: {doj}", type(doj))
        date_time = np.datetime64(doj)
        date_str = str(date_time)[:10]
        return date_str

    print(f"No matching record found for {user_email}")


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
    pattern = r'Give your wishes for <@([A-Z0-9]+)>'
    return re.findall(pattern, text)

def get_slack_user_details(user_id):
    try:
        # Call the users.info method using the WebClient
        result = app.client.users_info(user=user_id)

        user = result["user"]
        # Extract relevant user details
        user_details = {
            "id": user.get("id"),
            "name": user.get("name"),
            "real_name": user.get("real_name"),
            "display_name": user.get("profile", {}).get("display_name"),
            "email": user.get("profile", {}).get("email"),
            "image_original": user.get("profile", {}).get("image_original"),
            "title": user.get("profile", {}).get("title"),
            "team": user.get("team_id"),
            "is_admin": user.get("is_admin", False),
            "is_owner": user.get("is_owner", False),
            "is_bot": user.get("is_bot", False)
        }

        return user_details
    except Exception as e:
        print(f"Error fetching user details: {e}")
        return None

def send_file_message(channel, response, event_ts, file_path, user_id):
    if not os.path.isfile(file_path):
        response = "Sorry, I couldn't find the sample file."
    else:
        try:
            result = app.client.files_upload_v2(
                channels=channel,
                file=file_path,
                initial_comment=f":done: Generated card for user <@{user_id}>",
                thread_ts=event_ts
            )
        except Exception as e:
            response = f"An error occurred while sending the file: {str(e)}"

    send_slack_message(channel, response, event_ts)

# Event listener for mentions
@app.event("app_mention")
def handle_mention(event, say):
    logger.debug(f"Received message: {event}")
    response = get_kb_response(input_text=event["text"])
    send_slack_message(event["channel"], response, event["ts"])

@app.event("message")
def handle_message(body, message, say):
    event = body["event"]
    if event["channel_type"] == "im":
        text = event["text"]

        # Find the action and other details from bedrock
        raw_response = classify_user_message_openai(prompt=text)
        classify_response = ast.literal_eval(raw_response)

        # Help general query from KB
        if classify_response['action'] == 'general':
            kb_response = get_kb_response(input_text=text)
            send_slack_message(event["channel"], kb_response, event["ts"])
            return

        # Storing wishes, Using only thread to identify whom we are wishing
        if "thread_ts" in message:

            # get parent message
            thread_ts = message["thread_ts"]
            channel_id = message["channel"]
            parent_message = get_parent_message(channel_id, thread_ts)

            if parent_message:
                # if classify_response['action'] == 'wish':
                    print(f"Parent message text: {parent_message['text']}")
                    from_user = event["user"]
                    for_user = get_user_id_from_collect_wish_text(parent_message['text'])[0]

                    # Store data in database
                    from_user_details = get_slack_user_details(from_user)
                    print(f'from_user asdfasdfadf - {from_user_details}')
                    from_user_values = {
                        "name": from_user_details['real_name'],
                        "email": from_user_details['name'],
                        "profile_pic": from_user_details['image_original'],
                        "slack_user_id": from_user_details['id']
                    }
                    print(f'for_user asdfasdfadf - {get_slack_user_details(for_user)}')
                    for_user_details = get_slack_user_details(for_user)
                    for_user_values = {
                        "name": for_user_details['real_name'],
                        "email": for_user_details['name'],
                        "profile_pic": for_user_details['image_original'],
                        "slack_user_id": for_user_details['id']
                    }

                    # Add messages (users will be created automatically if they don't exist)
                    add_message_to_db(
                        from_user_values,
                        for_user_values,
                        text
                    )

                    print(f"From user: {from_user}, For user: {for_user}")
                    response = f"Recieved the following wish from you: {text}. \n If you want to update your wish, please reply with new message to this thread."
                    # response = f"From user: <@{from_user}>, For user: <@{for_user}>, Wish: {text}"
                # else:
                #     response = "Please provide a appropriate wish."

                    send_slack_message(event["channel"], response, event["ts"])
                    return
            else:
                print("Couldn't retrieve parent message")

        # Asking for wishes
        if classify_response['action'] == 'collecting_wishes':
            try:
                to_users = classify_response['to']
                from_users = classify_response['from']

                from_users_unpacked = []
                for from_user in from_users:
                    if from_user.startswith('S'):
                        from_users_unpacked.extend(get_group_members(from_user))
                    else:
                        from_users_unpacked.append(from_user)

                from_users_unpacked = list(set(from_users_unpacked))
                to_users = list(set(to_users))

                # distinct in last 15 days
                distinct_sender_receiver_mapping = get_distinct_wished_user_receiver_user_combinations(days=15)
                print(f"Distinct sender receiver mapping: {distinct_sender_receiver_mapping}")
                for mapping in distinct_sender_receiver_mapping:
                    print(f'From: {mapping[0]}, To: {mapping[1]}')

                wishes_sent_for = {}
                print(f"From users: {from_users_unpacked}, To users: {to_users}")

                for target_user in to_users: # to_users is the list of users for whom we are collecting wishes
                    doj = get_doj_of_user(target_user)
                    upcoming_anniversary = get_upcoming_anniversary(datetime.strptime(doj, '%Y-%m-%d'))
                    requested_wishes_from = []
                    for receiver_user in from_users_unpacked:
                        if receiver_user != target_user and (receiver_user, target_user) not in distinct_sender_receiver_mapping:
                            send_slack_message(receiver_user, 
                                f"Hello <@{receiver_user}>! Give your wishes for <@{target_user}>'s {upcoming_anniversary['years_completed']} work anniversary which is on {upcoming_anniversary['next_anniversary_date']}.  Please reply to this thread at the earliest"
                            )
                            requested_wishes_from.append(receiver_user)
                    wishes_sent_for[target_user] = requested_wishes_from

                # for user_id in from_users_unpacked:
                #     requested_wishes_from = []
                #     for target_user in to_users:
                #         if target_user != user_id and (user_id, target_user) not in distinct_sender_receiver_mapping:
                #             doj = get_doj_of_user(target_user)
                #             upcoming_anniversary = get_upcoming_anniversary(datetime.strptime(doj, '%Y-%m-%d'))
                #             send_slack_message(user_id, 
                #                 f"Hello <@{user_id}>! Give your wishes for <@{target_user}>'s {upcoming_anniversary['years_completed']} work anniversary which is on {upcoming_anniversary['next_anniversary_date']}.  Please reply to this thread at the earliest"
                #             )
                #             requested_wishes_from.append(target_user)
                #             wishes_sent_for[target_user] = user_id

                print(f"Wishes sent for: {wishes_sent_for}")
                for target_user, requested_wishes_from in wishes_sent_for.items():
                    print(f"asdfasdfn Target user: {target_user}, requested_wishes_from: {requested_wishes_from}")
                    if len(requested_wishes_from) == 0:
                        print(f"No wishes to collect for {target_user}")
                        response = f'No wishes to collect for <@{target_user}>'
                    else:
                        print(f"Sent requests to get wishes for {target_user} from {requested_wishes_from}")
                        formatted_from_users = ', '.join([f'<@{user_id}>' for user_id in requested_wishes_from])
                        target_user = f'<@{target_user}>'
                        print(f"Sent requests to get wishes for {target_user} from {formatted_from_users}")
                        response = f'Sent requests to get wishes for {target_user} from {formatted_from_users}. Note: For users who have already wished, the message will not be sent again.'
                    send_slack_message(event["channel"], response, event["ts"])
            except Exception as e:
                print(f"Error: {e}")
                response = 'Error in collecting wishes'
                send_slack_message(event["channel"], response, event["ts"])
            return

        # Get wishes of an user
        if classify_response['action'] == 'listing_wishes':
            to_user = classify_response['to']
            user_id = event["user"]
            if '@' in user_id:
                user_id = user_id[2:-1]
            messages = get_user_messages(to_user)
            response = f'Listing wishes for user <@{to_user}>\n'
            if len(messages) == 0:
                response = f'No wishes found for user <@{to_user}>'
                send_slack_message(event["channel"], response, event["ts"])
            else:
                for message in messages:
                    response += f"{message[1].capitalize()} wished: {message[3]}\n"
                    response = f"""```{response}```"""
                send_slack_message(event["channel"], response, event["ts"])

            return

        # Generate card for an user
        if classify_response['action'] == 'generate_card':
            to_user = classify_response['to']
            user_id = event["user"]
            if '@' in user_id:
                user_id = user_id[2:-1]
            messages = get_user_messages(to_user)
            if len(messages) == 0:
                response = f'No wishes found for user <@{to_user}>'
                send_slack_message(event["channel"], response, event["ts"])
            response = f'Generating card for user <@{to_user}>'
            output_card = generate_card_for_user(to_user)
            send_file_message(event["channel"], response, event["ts"], output_card, to_user)
            return


def main():
    handler = SocketModeHandler(app, slack_app_token)
    logger.info("Starting the bot...")
    handler.start()

if __name__ == "__main__":
    main()
