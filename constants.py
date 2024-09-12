import os
from dotenv import load_dotenv

load_dotenv()

slack_bot_token=os.getenv("SLACK_BOT_TOKEN")
slack_app_token=os.getenv("SLACK_APP_TOKEN")
region=os.getenv("REGION")
model_id=os.getenv("MODEL_ID")
document_uri=os.getenv("DOCUMENT_URI")
source_type=os.getenv("SOURCE_TYPE")