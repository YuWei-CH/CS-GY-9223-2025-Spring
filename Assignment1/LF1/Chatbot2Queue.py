import json
import boto3
import time
import re
from datetime import datetime
from boto3.dynamodb.conditions import Key

# LF1
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

    # Ensure session attributes exist and extract session_id
    session_attributes = event["sessionState"].get("sessionAttributes", {})
    session_id = session_attributes.get("session_id", None)

    if intent_name == "GreetingIntent":
        if invocation_source == "DialogCodeHook":
            return handle_greeting(intent, session_attributes)
        elif invocation_source == "FulfillmentCodeHook":
            session_id, response = fulfill_greeting(intent, session_attributes)
            return response

    elif intent_name == "DiningSuggestionsIntent":
        if invocation_source == "DialogCodeHook":
            session_id = session_attributes.get("session_id", f"sess-{int(time.time())}")  # Ensure session_id exists
            session_attributes["session_id"] = session_id  # Persist it
            return handle_dining_suggestions(intent, session_id, session_attributes)
        elif invocation_source == "FulfillmentCodeHook":
            return fulfill_dining_suggestions(intent["slots"], session_attributes)

    elif intent_name == "ThankYouIntent":
        return respond("You're welcome! Let me know if you need anything else.", intent_name, session_attributes=session_attributes)

    return respond("I'm not sure how to help with that.", intent_name, session_attributes=session_attributes)

def handle_greeting(intent, session_attributes):
    slots = intent.get("slots", {})
    session_slot = slots.get("sessionID")
    session_id_input = session_slot["value"]["interpretedValue"] if session_slot and session_slot.get("value") else None

    if not session_id_input:
        return elicit_slot(
            "GreetingIntent", slots, "sessionID",
            "Have you been with us before? If yes, please provide your session ID; otherwise, type 'no'.",
            session_attributes
        )

    if session_id_input.lower() == "no":
        session_id = f"sess-{int(time.time())}"
        table.put_item(Item={"session_id": session_id, "timestamp": int(time.time())})
        session_attributes["session_id"] = session_id  # Persist session_id
        return respond(
            f"Nice to meet you! Your new session ID is {session_id}. How can I help?",
            "GreetingIntent", session_attributes=session_attributes
        )

    if not is_valid_session_id(session_id_input):
        return elicit_slot(
            "GreetingIntent", slots, "sessionID",
            "Invalid session ID format. Please enter a valid session ID (sess-XXXXXXXXXX) or type 'no' if you're new.",
            session_attributes
        )

    session_attributes["session_id"] = session_id_input  # Persist session_id
    return delegate(intent, "GreetingIntent", session_attributes)

def fulfill_greeting(intent, session_attributes):
    slots = intent.get("slots", {})
    session_id_input = slots["sessionID"]["value"]["interpretedValue"].strip()

    response = table.query(
        KeyConditionExpression=Key("session_id").eq(session_id_input),
        ScanIndexForward=False
    )
    items = response.get("Items", [])

    if items:
        latest_record = items[0]
        last_result = ""
        if "RestaurantName" in latest_record:
            last_result += "🍴 **Your Last Recommendation:**\n\n"
            last_result += f"🍽️ **Name:** {latest_record.get('RestaurantName', 'Unknown')}\n"
            last_result += f"📍 **Address:** {latest_record.get('RestaurantAddress', 'Unknown')}\n"
            last_result += f"⭐ **Rating:** {latest_record.get('RestaurantRating', 'N/A')}\n"
            last_result += f"💬 **Reviews:** {latest_record.get('RestaurantReviews', 'N/A')}\n\n"
            last_result += "Hope you enjoyed it! 😋\n"

        session_attributes["session_id"] = session_id_input  # Ensure session_id is stored

        return session_id_input, respond(
            f"Hey! Session **{session_id_input}** is active.\n\n{last_result}How can I help?",
            "GreetingIntent", session_attributes=session_attributes
        )

    # If session_id is not found, create a new one
    new_session_id = f"sess-{int(time.time())}"
    table.put_item(Item={"session_id": new_session_id, "timestamp": int(time.time())})
    session_attributes["session_id"] = new_session_id  # Ensure session_id is stored

    return new_session_id, respond(
        f"Session {session_id_input} not found. Created a new session: {new_session_id}. How can I assist?",
        "GreetingIntent", session_attributes=session_attributes
    )

def handle_dining_suggestions(intent, session_id, session_attributes):
    slots = intent.get("slots", {})

    # Ensure session ID is stored
    session_attributes["session_id"] = session_id

    # Track prompted slots using session attributes
    prompted_slots = json.loads(session_attributes.get("prompted_slots", "{}"))  # Convert from string to dict

    required_slots = ["location", "cuisine", "date", "time", "numPeople", "email"]

    for slot_name in required_slots:
        slot_data = slots.get(slot_name, None)

        if not slot_data or "value" not in slot_data or "interpretedValue" not in slot_data["value"]:
            # First-time prompt vs. reprompt
            message = (
                generate_reprompt(slot_name) if slot_name in prompted_slots else generate_prompt(slot_name)
            )

            # Mark this slot as prompted
            prompted_slots[slot_name] = True
            session_attributes["prompted_slots"] = json.dumps(prompted_slots)  # Store updated tracking info

            return elicit_slot(
                "DiningSuggestionsIntent", slots, slot_name, message, session_attributes
            )

        # Validate slot input
        slot_value = slot_data["value"]["interpretedValue"].strip()
        if not is_valid_slot(slot_name, slot_value):
            message = generate_reprompt(slot_name)  # Use reprompt message
            return elicit_slot("DiningSuggestionsIntent", slots, slot_name, message, session_attributes)

    # If all slots are filled, delegate to Lex
    return delegate(intent, "DiningSuggestionsIntent", session_attributes)

def fulfill_dining_suggestions(slots, session_attributes):
    session_id = session_attributes.get("session_id", f"sess-{int(time.time())}")
    session_attributes["session_id"] = session_id  # Ensure session_id is stored

    slot_values = {slot: slots[slot]["value"]["interpretedValue"] for slot in slots}

    try:
        sqs.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=json.dumps(slot_values),
            MessageAttributes={'session_id': {'DataType': 'String', 'StringValue': session_id}}
        )
    except Exception:
        return respond("Couldn't process your request right now. Try again later.", "DiningSuggestionsIntent")

    return respond(
        f"I'll find some {slot_values['cuisine']} restaurants in {slot_values['location']} for {slot_values['numPeople']} "
        f"people on {slot_values['date']} at {slot_values['time']}. You'll receive an email at {slot_values['email']} soon!",
        "DiningSuggestionsIntent", session_attributes=session_attributes
    )

# Utility Functions
def is_valid_session_id(session_id):
    return re.match(r"^sess-\d{10}$", session_id) is not None

def generate_prompt(slot_name):
    """ First-time slot prompts """
    prompts = {
        "location": "Where do you want to eat?",
        "cuisine": "What type of cuisine are you in the mood for? We support Chinese, Italian, Japanese, Indian, and Mexican.",
        "date": "When would you like to dine? You can say a date like 'tomorrow' or 'March 5th'.",
        "time": "What time do you plan to eat? You can say '7 PM', 'noon', or 'in the evening'.",
        "numPeople": "How many people will be dining?",
        "email": "Please enter your email so we can send you the restaurant suggestions."
    }
    return prompts.get(slot_name, f"Could you please provide a valid {slot_name}?")

def generate_reprompt(slot_name):
    """ Reprompt messages when user input is invalid """
    reprompt_messages = {
        "location": "Hmm, that doesn’t seem like a valid location. Please provide a city or area.",
        "cuisine": "I didn’t catch that. We support Chinese, Italian, Japanese, Indian, and Mexican. Which one would you like?",
        "date": "That doesn't look like a valid date. You can say something like 'tomorrow' or 'March 5th'.",
        "time": "That doesn't seem like a valid time. You can say things like '7 PM', 'noon', or 'tonight'.",
        "numPeople": "I need a number for how many people will be dining. Can you enter it again?",
        "email": "That email doesn’t seem correct. Please enter a valid email address."
    }
    return reprompt_messages.get(slot_name, f"Could you please provide a valid {slot_name}?")

def is_valid_slot(slot_name, slot_value):
    if slot_name == "cuisine":
        return slot_value.lower() in ["chinese", "italian", "japanese", "indian", "mexican"]
    elif slot_name == "email":
        return re.match(r"[^@]+@[^@]+\.[^@]+", slot_value) is not None
    elif slot_name == "date":
        try:
            datetime.strptime(slot_value, "%Y-%m-%d")
            return True
        except ValueError:
            return False
    elif slot_name == "time":
        return bool(slot_value.strip())  # Any non-empty value is valid
    elif slot_name == "numPeople":
        return slot_value.isdigit() and int(slot_value) > 0
    return True

#?should we keep the session attributes
def delegate(intent, intent_name, session_attributes = None):
    return {
        "sessionState": {
            "dialogAction": {"type": "Delegate"},
            "intent": {"name": intent_name, "slots": intent.get("slots"), "state": "InProgress"},
            "sessionAttributes": session_attributes if session_attributes else {} # Ensure session attributes persist
        }
    }

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

def elicit_slot(intent_name, slots, slot_to_elicit, message, session_attributes=None):
    """Ensure slot elicitation maintains session tracking, including session_id."""
    if session_attributes is None:
        session_attributes = {}

    if "session_id" not in session_attributes:
        session_attributes["session_id"] = f"sess-{int(time.time())}"  # Ensure session_id is tracked

    return {
        "sessionState": {
            "dialogAction": {"type": "ElicitSlot", "slotToElicit": slot_to_elicit},
            "intent": {"name": intent_name, "slots": slots, "state": "InProgress"},
            "sessionAttributes": session_attributes,  # Persist session_id and other data
        },
        "messages": [{"contentType": "PlainText", "content": message}],
    }