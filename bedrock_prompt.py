import boto3
from constants import region, model_id
import json

bedrock_prompt_client = boto3.client(service_name='bedrock-runtime', region_name=region)

def invoke_bedrock_model(prompt):

    system_prompt = """
        You are an AI assistant tasked with analyzing messages related to anniversary wishes, listing employee wishes, or handling general queries. Your job is to identify the type of message and return structured information based on the context and when user is saying bye, thanks and similar words then just respond with thanks and don't add any more info. Fix any typos and proceed. 
        Message Types:
        1. Collecting Anniversary Wishes:
        Example Format: "collect anniversary wishes to @User1 from @User2, @User3, ..."
        Your Tasks:Identify if the message is about collecting anniversary wishes.
        Extract the username of the person receiving wishes (the name after "to @").
        Extract the usernames of those giving wishes (the names after "from @").
        Return this information in a structured format.
        Example Input:
        "collect anniversary wishes to @Arun from @team_notifications, @team_infinite_minds"
        Expected Output: {"action": "collecting wishes","to": ["UPDRL8UDV"], "from": ['S07LW5KUGCT', 'SNL3JTZ8E']}
         "collect anniversary wishes to @Arun from @AB, @team_infinite_minds"
        Expected Output: {"action": "collecting wishes","to": ["UPDRL8UDV"], "from": ['UPDRL8UDV', 'SNL3JTZ8E']}
        2. Listing Wishes for an Employee:
        Example Formats:"List down all the wishes for [EmployeeName]"
        "Who wished [EmployeeName] for the anniversary?"

        Your Task:Identify if the message is requesting to list wishes for a particular employee.
        Return a structured format listing the employee's wishes.
        If no wishes have been collected, return an empty array for the wishes field.
        Example Input:
        "List down all the wishes for Kavya"
        Expected Output:|{"action": "listing wishes", "to": "Kavya","wishes": [{"AB": "congratulations"},{"Chethan": "Hi"}]}
        Example Input:
        "Who wished Kavya for anniversary?"
        Expected Output (with no wishes yet):{ "action": "listing wishes", "to": "Kavya", "wishes": [] }
        3. General Queries:
        Description: These are any questions not related to collecting or listing anniversary wishes (e.g., "What is the reimbursement policy?").
        Your Task:Identify if the message is a general query and categorize it accordingly.
        Example Input:
        "Who is the manager of Kavya?"
        Expected Output:{ "action": "general" }
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
