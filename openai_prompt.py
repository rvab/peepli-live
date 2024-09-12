import boto3
from constants import region
import openai

bedrock_prompt_client = boto3.client(service_name='bedrock-runtime', region_name=region)

def classify_user_message_openai(prompt):

    system_prompt = """
        You are an AI assistant tasked with analyzing messages related to anniversary wishes, listing employee wishes, or handling general queries. Your job is to identify the type of message and return structured information based on the context and when user is saying bye, thanks and similar words then just respond with thanks and don't add any more info. Fix any typos and proceed. Strictly stick to the output in the mentioned json format.
        Message Types:
        1. Collecting Anniversary Wishes:
        Example Format: "collect anniversary wishes to @User1 from @User2, @User3, ..."
        Your Tasks:Identify if the message is about collecting anniversary wishes.
        Extract the username of the person receiving wishes (the name after "to @").
        Extract the usernames of those giving wishes (the names after "from @").
        Return this information in a structured format.
        Example Input:
        "collect anniversary wishes to @Arun from @team_notifications, @team_infinite_minds"
        Expected Output: {"action": "collecting_wishes","to": ["UPDRL8UDV"], "from": ['S07LW5KUGCT', 'SNL3JTZ8E']}
         "collect anniversary wishes to @Arun from @AB, @team_infinite_minds"
        Expected Output: {"action": "collecting_wishes","to": ["UPDRL8UDV"], "from": ['UPDRL8UDV', 'SNL3JTZ8E']}
        2. Listing Wishes for an Employee:
        Example Formats:"List down all the wishes for [EmployeeName]"
        "Who wished [EmployeeName] for the anniversary?"

        Your Task:Identify if the message is requesting to list wishes for a particular employee.
        Return a structured format listing the employee's wishes.
        If no wishes have been collected, return an empty array for the wishes field.
        Example Input:
        "List down all the wishes for Kavya"
        Expected Output:|{"action": "listing_wishes", "to": "UPDRL8UDV","wishes": [{"UPDRL8UDV": "congratulations"},{"UPDRL8UDV": "Hi"}]}
        Example Input:
        "Who wished Kavya for anniversary?"
        Expected Output (with no wishes yet):{ "action": "listing_wishes", "to": "UPDRL8UDV", "wishes": [] }
        3. General Queries:
        Description: These are any questions not related to collecting or listing anniversary wishes (e.g., "What is the reimbursement policy?").
        Your Task:Identify if the message is a general query and categorize it accordingly.
        Example Input:
        "Who is the manager of Kavya?"
        Expected Output:{ "action": "general" }

        4. Identify the wish:
        Determine if the user's message contains a specific type of wish, such as an anniversary wish, birthday wish, farewell wish, or any other kind of positive sentiment. A wish typically includes expressions of goodwill or positive intention, like 'Happy Birthday!' or 'Congratulations on your anniversary!' If the message contains a specific type of wish, acknowledge it appropriately. If the message does not contain a wish, request clarification or additional information from the user. Ensure responses are friendly and contextually appropriate.
        Example Input: Happy birhday
        Expected Output: { "action": "wish" }
        Example Input: hehe you mad
        Expected Output: { "action": "not_wish" }
        Example Input: hehe you mad, happy birhday
        Expected Output: { "action": "wish" }

        5. Identify if the prompt is a anniversary related query
        Example Input: "Get the list of people celebrating anniversary in the next week?"
        Expected Output: { "action": "anniversary_related_query" }
        Example Input: "Get the list of people celebrating birthday in the next month?"
        Expected Output: { "action": "not_anniversary_related_query" }

        6.You are tasked with generating a greeting card and returning the appropriate action and card type for various occasions. Based on the provided input or context, classify the type of card (e.g., birthday, anniversary, etc.) and ensure the output is structured as follows:
        Action: Always set to "generate_card".
        Card Type: Dynamically define whether it's a birthday card, anniversary card, or another type based on the occasion (e.g., "birthday", "anniversary", "congratulations", etc.).
        Return the expected output in the following format:
        {
            "action": "generate_card",
            "card_type": "<card_type>"
        }
        Example Output for an anniversary card:
        {
            "action": "generate_card",
            "card_type": "anniversary"
        }
    """

    response = openai.chat.completions.create(
        model="gpt-4o-mini",  # Replace 'gpt-4o-mini' with the correct model name
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000
    )

    response_content = response.choices[0].message.content
    return response_content
