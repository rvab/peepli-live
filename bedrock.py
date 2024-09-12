import boto3
from constants import region, model_id, document_uri, source_type

bedrock_client = boto3.client(service_name='bedrock-agent-runtime', region_name=region)

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
