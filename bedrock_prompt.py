import boto3
from constants import region, model_id
import json

bedrock_prompt_client = boto3.client(service_name='bedrock-runtime', region_name=region)

def invoke_bedrock_model(prompt):

    system_prompt = """
        **Instructions:**

            You are an AI assistant helping to parse a message about collecting anniversary wishes. Given a message in the format "collect anniversary wishes to @User1 from @User2, @User3, ...", your task is to: 
        
            * Identify the user who is receiving the wishes (the user after "to @"). 
            * Identify the users who are giving the wishes (the users after "from @"). 
            * Return this information in a structured format. 

        **Example:**    
            Input: The message text 
            Output: A JSON object with two fields: "to": The username of the person receiving wishes "from": An array of usernames of people giving wishes Example: 
            Input: "collect anniversary wishes to @Arun from @AB, @Kavya" 
            Output: { to: Arun from: [AB, Kavya] }
    """

    request_body = {
        "system": system_prompt,
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 512,
        "temperature": 0.5,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}],
            }
        ],
    }

    request = json.dumps(request_body)

    response = bedrock_prompt_client.invoke_model(
        body=request,
        modelId=model_id,
        accept='application/json',
        contentType='application/json'
    )

    response_body = response.get('body').read()
    print('invoke_bedrock_model response' ,response_body)
    response_body = json.loads(response_body)
    return response_body
