import os
import logging
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


app = App(token=os.getenv("SLACK_BOT_TOKEN"))

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

@app.event("message")
def handle_dm(body, say):
    event = body["event"]
    if event["channel_type"] == "im":
        user = event["user"]
        text = event["text"]

        # Process the DM and respond
        response = f"Hello <@{user}>! You sent me a DM: {text}"
        say(response)


def main():
    handler = SocketModeHandler(app, os.getenv("SLACK_APP_TOKEN"))
    logger.info("Starting the bot...")
    handler.start()

if __name__ == "__main__":
    main()
