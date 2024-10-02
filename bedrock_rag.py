import boto3

from constants import region, model_id, document_uri, source_type

bedrock_rag_client = boto3.client(service_name='bedrock-agent-runtime', region_name=region)

def retrieve_and_generate(input_text, source_type, model_id, document_s3_uri=None, data=None):
    model_arn = f'arn:aws:bedrock:{region}::foundation-model/{model_id}'

    if source_type == source_type:
        return bedrock_rag_client.retrieve_and_generate(
            input={'text': input_text},
            retrieveAndGenerateConfiguration={
                'type': 'EXTERNAL_SOURCES',
                'externalSourcesConfiguration': {
                    'modelArn': model_arn,
                    'sources': [
                        {
                            "sourceType": source_type,
                            "s3Location": {
                                "uri": document_s3_uri
                            }
                        }
                    ]
                }
            }
        )

    else:
        return bedrock_rag_client.retrieve_and_generate(
            input={'text': input_text},
            retrieveAndGenerateConfiguration={
                'type': 'EXTERNAL_SOURCES',
                'externalSourcesConfiguration': {
                    'modelArn': model_arn,
                    'sources': [
                        {
                            "sourceType": source_type,
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

def get_kb_response(input_text):
    response = retrieve_and_generate(
        input_text=input_text,
        source_type=source_type,
        model_id=model_id,
        document_s3_uri=document_uri
    )

    return response['output']['text']
