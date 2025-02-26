import json
import urllib3
import boto3
import random
import os
from base64 import b64encode
from decimal import Decimal
from boto3.dynamodb.conditions import Key
#LF2
# AWS Service Clients
sqs = boto3.client("sqs")
dynamodb = boto3.resource("dynamodb", region_name=os.environ["AWS_REGION_"])
ses = boto3.client("ses", region_name=os.environ["AWS_REGION_"])

# OpenSearch Configuration
OPENSEARCH_HOST = os.environ["OPENSEARCH_HOST"]
INDEX_NAME = os.environ["OPENSEARCH_INDEX"]
OPENSEARCH_USER = os.environ["OPENSEARCH_USER"]
OPENSEARCH_PASS = os.environ["OPENSEARCH_PASS"]

# Encode OpenSearch credentials for Basic Auth
auth_headers = {
    "Authorization": "Basic " + b64encode(f"{OPENSEARCH_USER}:{OPENSEARCH_PASS}".encode()).decode(),
    "Content-Type": "application/json"
}

http = urllib3.PoolManager()

# SQS Queue URL
SQS_QUEUE_URL = os.environ["SQS_QUEUE_URL"]

# DynamoDB Table Reference
TABLE_NAME = os.environ["RES_TABLE"]
table = dynamodb.Table(TABLE_NAME)
USER_TABLE = os.environ["USER_TABLE"]
user_table = dynamodb.Table(USER_TABLE)

# SES Source Email (verified in AWS SES)
SES_SOURCE_EMAIL = os.environ["SES_SOURCE_EMAIL"]

def convert_decimals(obj):
    """Recursively converts Decimal values to float or int."""
    if isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj) if obj % 1 else int(obj)  # Convert to float or int
    return obj

def query_opensearch(cuisine, num_results=3):
    """Fetch a random restaurant for the given cuisine from OpenSearch."""
    query = {
        "query": {"match": {"Cuisine": cuisine}},
        "size": 10
    }
    url = f"{OPENSEARCH_HOST}/{INDEX_NAME}/_search"
    response = http.request("GET", url, body=json.dumps(query), headers=auth_headers)

    if response.status != 200:
        print(f"OpenSearch Query Failed: {response.data.decode()}")
        return []

    results = json.loads(response.data)
    hits = results.get("hits", {}).get("hits", [])

    # Log OpenSearch response
    print(f"OpenSearch Response: {json.dumps(results, indent=2)}")
    if not hits:
        print("No restaurants found in OpenSearch for cuisine:", cuisine)
        return []
    
    selected_restaurants = random.choices(hits, k=min(len(hits), num_results))

    return [restaurant["_source"].get("BusinessID") for restaurant in selected_restaurants]

def get_restaurant_details(business_ids):
    """Fetch full restaurant details from DynamoDB."""
    print(f"Fetching details from DynamoDB for BusinessID: {business_ids}")
    result = []
    for business_id in business_ids:
        response = table.get_item(Key={"BusinessID": business_id})
        restaurant = response.get("Item")
        if restaurant:
            result.append(convert_decimals(restaurant)) # Convert Decimal to float or int
    return result if len(result) == len(business_ids) else None


def send_email(to_email, subject, body):
    """Send an email using Amazon SES."""
    try:
        response = ses.send_email(
            Source=SES_SOURCE_EMAIL,
            Destination={"ToAddresses": [to_email]},
            Message={
                "Subject": {"Data": subject},
                "Body": {"Text": {"Data": body}}
            }
        )
        print(f"Email Sent! Message ID: {response['MessageId']}")
    except Exception as e:
        print(f"ERROR: Failed to send email to {to_email}. Error: {e}")


def lambda_handler(event, context):
    """Main Lambda function triggered by SQS messages."""
    print("Received SQS Event:", json.dumps(event, indent=2))

    if "Records" not in event:
        print("No records found in SQS event.")
        return {"statusCode": 200, "body": "No task in SQS"}
    
    for record in event["Records"]:
        body = json.loads(record["body"])
        session_id = record.get("messageAttributes", {}).get("session_id", {}).get("stringValue", "unknown")
        print(f"Session ID from SQS: {session_id}")
        user_email = body.get("email") or body.get("Email")  # Handle different casing
        cuisine = body.get("cuisine") or body.get("Cuisine")
        num_people = body.get("numPeople", "some")
        dining_time = body.get("time", "a convenient time")

        if not user_email or not cuisine:
            print(f"Missing data in SQS message: {body}")
            continue

        print(f"Looking for a {cuisine} restaurant recommendation for {user_email}...")

        # Fetch a random restaurant BusinessID
        business_ids = query_opensearch(cuisine)
        if not business_ids:
            print("No suitable restaurant found, sending email notification.")
            send_email(user_email, "Restaurant Suggestion", f"Sorry, no {cuisine} restaurants found.")
            continue

        # Fetch full restaurant details
        restaurants = get_restaurant_details(business_ids)
        if not restaurants:
            print("Failed to fetch restaurant details, sending email notification.")
            send_email(user_email, "Restaurant Suggestion", f"Sorry, we couldn't fetch details for {cuisine}.")
            continue

        rest_names = [restaurant.get('Name', 'Unknown') for restaurant in restaurants]
        rest_addresses = [restaurant.get('Address', 'Unknown') for restaurant in restaurants]
        rest_ratings = [restaurant.get('Rating', 'N/A') for restaurant in restaurants]
        rest_reviews = [restaurant.get('NumberOfReviews', 'N/A') for restaurant in restaurants]

        response_history = user_table.query(
            KeyConditionExpression=Key("session_id").eq(session_id),
            ScanIndexForward=False,  # newest first
            Limit=1
        )
        if response_history.get("Items"):
            latest_record = response_history["Items"][0]
            timestamp = latest_record["timestamp"]
            update_response = user_table.update_item(
                Key={"session_id": session_id, "timestamp": timestamp},
                UpdateExpression="""
                    SET RestaurantName = :rn,
                        RestaurantAddress = :ra,
                        RestaurantRating = :rr,
                        RestaurantReviews = :rv
                """,
                ExpressionAttributeValues={
                    ":rn": rest_names[0],
                    ":ra": rest_addresses[0],
                    # If rest_rating is a float, convert it to Decimal.
                    ":rr": Decimal(str(rest_ratings[0])) if isinstance(rest_ratings[0], float) else rest_ratings[0],
                    # Similarly for rest_reviews:
                    ":rv": Decimal(str(rest_reviews[0])) if isinstance(rest_reviews[0], float) else rest_reviews[0]
                },
                ReturnValues="ALL_NEW"
            )
            print("Restaurant details added to ChatHistory:", json.dumps(convert_decimals(update_response), indent=2))
        else:
            print(f"No ChatHistory record found for session {session_id} to update.")

        # Use the same variables in your email body:
        email_body = f"Hello! Here are my {cuisine} restaurant suggestions for {num_people} people, for {dining_time}:\n\n"

        for i, (name, address, rating, reviews) in enumerate(zip(rest_names, rest_addresses, rest_ratings, rest_reviews), 1):
            email_body += f"{i}. 🍽️ **{name}**\n"
            email_body += f"   📍 Address: {address}\n"
            email_body += f"   ⭐ Rating: {rating}\n"
            email_body += f"   💬 Reviews: {reviews}\n\n"

        email_body += "Enjoy your meal! 🍕🍣🌮"
        print("📧 Sending email with the following content:\n", email_body)

        # Send email
        send_email(user_email, f"Your {cuisine} Restaurant Suggestion", email_body)

    return {"statusCode": 200, "body": "SQS messages processed successfully"}