import boto3
from constants import region, model_id, document_uri, source_type
import json

bedrock_client = boto3.client(service_name='bedrock-runtime', region_name=region)
# bedrock_client = boto3.client(service_name='bedrock-agent-runtime', region_name=region)

def retrieveAndGenerate(input_text, sourceType, model_id, document_s3_uri=None, data=None):
    model_arn = f'arn:aws:bedrock:{region}::foundation-model/{model_id}'

    if sourceType == source_type:
        return bedrock_client.retrieve_and_generate(
            input={'text': input_text},
            retrieveAndGenerateConfiguration={
                'type': 'EXTERNAL_SOURCES',
                'externalSourcesConfiguration': {
                    'modelArn': model_arn,
                    'sources': [
                        {
                            "sourceType": sourceType,
                            "s3Location": {
                                "uri": document_s3_uri
                            }
                        }
                    ]
                }
            }
        )

    else:
        return bedrock_client.retrieve_and_generate(
            input={'text': input_text},
            retrieveAndGenerateConfiguration={
                'type': 'EXTERNAL_SOURCES',
                'externalSourcesConfiguration': {
                    'modelArn': model_arn,
                    'sources': [
                        {
                            "sourceType": sourceType,
                            "byteContent": {
                                "identifier": "testFile.txt",
                                "contentType": "text/plain",
                                "data": data
                            }
                        }
                    ]
                }
            }
        )

def getBedrockResponse(input_text):
    response = retrieveAndGenerate(
        input_text=input_text,
        sourceType=source_type,
        model_id=model_id,
        document_s3_uri=document_uri
    )

    return response['output']['text']


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

    response = bedrock_client.invoke_model(
        body=request,
        modelId=model_id,
        accept='application/json',
        contentType='application/json'
    )

    response_body = response.get('body').read()
    print('invoke_bedrock_model response' ,response_body)
    response_body = json.loads(response_body)
    return response_body