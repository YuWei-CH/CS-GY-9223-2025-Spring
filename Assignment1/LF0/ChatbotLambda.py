import json
import boto3
import time
from datetime import datetime
# LF0
# Initialize AWS Lex and choose table from DB
lex_client = boto3.client("lexv2-runtime")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("ChatHistory")


def create_response(status_code, body):
    """Generate standardized HTTP responses"""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
        "body": json.dumps(body)
    }

def lambda_handler(event, context):
    """Handles API requests, sends messages to AWS Lex, and formats responses for frontend."""
    
    print("Received API Event:", json.dumps(event, indent=2))  # Debugging log

    # Handle CORS Preflight Requests
    if event.get("httpMethod") == "OPTIONS":
        return create_response(200, {"message": "CORS preflight request success"})

    try:
        # Step 1: Parse API Request Body
        if "body" not in event or not event["body"]:
            return create_response(400, {"error": "Missing 'body' field in request."})

        body = json.loads(event["body"]) if isinstance(event["body"], str) else event["body"]

        print(" Parsed Request Body:", json.dumps(body))  # Debugging log

        # Step 2: Extract User SessionID and Message
        session_id = body.get("session_id", f"sess-{int(time.time())}")
        messages = body.get("messages", [])
        
        if not messages or not isinstance(messages, list):
            return create_response(400, {"error": "Invalid request format. 'messages' field is missing or invalid."})

        user_message = messages[0].get("unstructured", {}).get("text", "")

        if not user_message:
            return create_response(400, {"error": "Invalid request format. 'text' field is missing."})

        # Step 3: Call AWS Lex Chatbot
        lex_response = lex_client.recognize_text(
            botId="ZLE5EMM5CT",  # Lex bot id
            botAliasId="TSTALIASID",  # Bot Alias ID
            localeId="en_US",  # language
            sessionId=session_id,  # User session
            text=user_message
        )

        # Step 4: Extract Lex Response
        bot_message = lex_response.get("messages", [{}])[0].get("content", "Sorry, I didn't understand that.")

        # Step 5: Store Conversation in DynamoDB
        last_category = None
        last_location = None
        words = user_message.lower().split()

        if "restaurant" in words and "in" in words:
            index = words.index("in")
            last_category = words[index-1] if index > 0 else None
            last_location = words[index+1] if index + 1 < len(words) else None
        
        if last_category and last_location:
            table.put_item(Item={
                "session_id": session_id,
                "timestamp": int(time.time()),  # Store most recent search time
                "last_category": last_category,
                "last_location": last_location
            })
            print(f"Stored last search: {last_category} in {last_location}")
                
        # Step 6: Format API Response
        bot_response = {
            "session_id": session_id,
            "messages": [
                {
                    "type": "unstructured",
                    "unstructured": {
                        "text": bot_message
                    }
                }
            ]
        }
        return create_response(200, bot_response)

    except Exception as e:
        print("Error:", str(e))
        return create_response(500, {"error": str(e)})
        