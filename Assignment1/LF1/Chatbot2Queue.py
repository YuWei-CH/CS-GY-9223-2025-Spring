import json
import boto3
import time
from boto3.dynamodb.conditions import Key
#LF1
# Initialize AWS clients
sqs = boto3.client("sqs")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("ChatHistory")

SQS_QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/515966538082/DiningSuggestionsQueue"

def lambda_handler(event, context):
    print("Received Lex Event:", json.dumps(event, indent=2))

    intent = event["sessionState"]["intent"]
    intent_name = intent["name"]
    invocation_source = event["invocationSource"]

    if intent_name == "GreetingIntent":
        if invocation_source == "DialogCodeHook":
            return handle_greeting(intent)
        elif invocation_source == "FulfillmentCodeHook":
            new_session_id, response = fulfill_greeting(intent)
            print("new_session_id", new_session_id)
            return response

    elif intent_name == "DiningSuggestionsIntent":
        # Extract the session_id from Lex sessionAttributes
        session_id = event["sessionState"].get("sessionAttributes", {}).get("session_id", "unknown")
        return process_dining_suggestions(intent, session_id)

    elif intent_name == "ThankYouIntent":
        return respond("You're welcome! Let me know if you need anything else.", intent_name)

    return respond("I'm not sure how to help with that.", intent_name)


# Greeting Intent
def delegate(intent, intent_name):
    return {
        "sessionState": {
            "dialogAction": {"type": "Delegate"},
            "intent": {
                "name": intent_name,
                "slots": intent.get("slots"),
                "state": "InProgress"
            }
        }
    }

def handle_greeting(intent):
    slots = intent.get("slots", {})
    
    # If the sessionID slot isn't provided yet, explicitly ask user for it
    session_slot = slots.get("sessionID")
    session_id_input = session_slot["value"]["interpretedValue"] if session_slot and session_slot.get("value") else None

    if not session_id_input:
        # Explicitly ask for the slot clearly
        return elicit_slot(
            "GreetingIntent", 
            slots, 
            "sessionID",
            "Have you been with us before? If yes, please provide your sessionID; otherwise, type 'no'."
        )

    # Once slot is filled, delegate clearly to fulfillment
    return delegate(intent, "GreetingIntent")

def fulfill_greeting(intent):
    slots = intent.get("slots", {})
    session_id_input = slots["sessionID"]["value"]["interpretedValue"].strip()

    if session_id_input.lower() == "no":
        new_session_id = f"sess-{int(time.time())}"
        table.put_item(Item={"session_id": new_session_id, "timestamp": int(time.time())})
        print(f"✨ New session created: {new_session_id}")
        return new_session_id, respond(
            f"Nice to meet you! Your new session ID is {new_session_id}. How can I help?", 
            "GreetingIntent", 
            session_attributes={"session_id": new_session_id}
        )

    # Use query instead of get_item
    response = table.query(
        KeyConditionExpression=Key("session_id").eq(session_id_input),
        ScanIndexForward=False
    )
    items = response.get("Items", [])

    if items:
        print(f"Existing session found: {session_id_input}")
        latest_record = items[0]
        last_result = ""
        if "RestaurantName" in latest_record:
            last_result = (
                "🎉 **Your Last Recommendation!**\n\n"
                f"🍴 **Name:** {latest_record.get('RestaurantName', 'Unknown')}\n"
                f"📍 **Address:** {latest_record.get('RestaurantAddress', 'Unknown')}\n"
                f"⭐ **Rating:** {latest_record.get('RestaurantRating', 'N/A')}\n"
                f"💬 **Reviews:** {latest_record.get('RestaurantReviews', 'N/A')}\n\n"
                "Hope you had a delicious experience! 😋\n"
            )
        return session_id_input, respond(
            f"Hey there! Session **{session_id_input}** is active.\n\n{last_result}What would you like to do next?",
            "GreetingIntent",
            session_attributes={"session_id": session_id_input}
        )
    else:
        new_session_id = f"sess-{int(time.time())}"
        table.put_item(Item={"session_id": new_session_id, "timestamp": int(time.time())})
        print(f"SessionID {session_id_input} not found. Created new session: {new_session_id}")
        return new_session_id, respond(
            f"Session {session_id_input} not found. Created a new session: {new_session_id}. How can I assist?", 
            "GreetingIntent",
            session_attributes={"session_id": new_session_id}
        )

def process_dining_suggestions(intent, session_id):
    slots = intent.get("slots", {})
    required_slots = ["location", "cuisine", "date", "time", "numPeople", "email"]

    for slot_name in required_slots:
        if not slots.get(slot_name, {}).get("value", {}).get("interpretedValue"):
            return elicit_slot("DiningSuggestionsIntent", slots, slot_name,
                               f"Could you please specify {slot_name}?")

    slot_values = {slot: slots[slot]["value"]["interpretedValue"] for slot in required_slots}
    try:
        sqs.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=json.dumps(slot_values),
            MessageAttributes={
                'session_id': {
                    'DataType': 'String',
                    'StringValue': session_id
                }
            }
        )
        print(f"Successfully sent message of session:{session_id} to SQS.")
    except Exception as e:
        print(f"ERROR sending to SQS: {e}")
        return respond("Couldn't process your request right now. Try again later.", "DiningSuggestionsIntent")

    return respond(f"Got it! I'll find some {slot_values['cuisine']} restaurants in {slot_values['location']} "
                   f"for {slot_values['numPeople']} people, for {slot_values['date']} at {slot_values['time']}. You'll receive an email at {slot_values['email']} soon!",
                   "DiningSuggestionsIntent")

def respond(message, intent_name, slots=None, dialog_action_type="Close", slot_to_elicit=None, session_attributes=None):
    response = {
        "sessionState": {
            "dialogAction": {"type": dialog_action_type},
            "intent": {"name": intent_name, "state": "Fulfilled" if dialog_action_type == "Close" else "InProgress"},
            "sessionAttributes": session_attributes if session_attributes else {}
        },
        "messages": [{"contentType": "PlainText", "content": message}]
    }

    if slots:
        response["sessionState"]["intent"]["slots"] = slots

    if slot_to_elicit:
        response["sessionState"]["dialogAction"]["slotToElicit"] = slot_to_elicit

    return response


def elicit_slot(intent_name, slots, slot_to_elicit, message):
    return respond(message, intent_name, slots, "ElicitSlot", slot_to_elicit)
