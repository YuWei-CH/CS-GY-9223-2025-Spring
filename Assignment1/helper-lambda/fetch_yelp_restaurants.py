import requests
import boto3
import os
import time
from datetime import datetime
from decimal import Decimal

# 🚀 Get Yelp API Key from environment variables
YELP_API_KEY = os.environ['YELP_API_KEY']

# 🚀 List of cuisines to fetch (ensure 1,000+ per category)
CUISINES = ["Chinese", "Italian", "Japanese", "Mexican", "Indian"]

# 🚀 Manhattan location for Yelp API search
LOCATION = "Manhattan, NY"

# 🚀 Yelp API Headers
HEADERS = {"Authorization": f"Bearer {YELP_API_KEY}"}

# 🚀 AWS DynamoDB setup
dynamodb = boto3.resource("dynamodb", region_name="us-east-1")  # Change region if needed
table = dynamodb.Table("yelp-restaurants")


def get_restaurants(cuisine, limit=50):
    """Fetch restaurants from Yelp API for a specific cuisine in Manhattan."""
    url = "https://api.yelp.com/v3/businesses/search"
    restaurants = []
    params = {
        "term": f"{cuisine} restaurants",
        "location": LOCATION,
        "limit": limit,
        "sort_by": "rating"
    }
    
    for offset in range(0, 50, limit):  # Yelp allows pagination
        params["offset"] = offset
        response = requests.get(url, headers=HEADERS, params=params)

        if response.status_code == 200:
            data = response.json()
            for business in data.get("businesses", []):
                restaurants.append({
                    "BusinessID": business["id"],
                    "Name": business["name"],
                    "Address": " ".join(business["location"]["display_address"]),
                    "Coordinates": business["coordinates"],
                    "NumberOfReviews": business["review_count"],
                    "Rating": business["rating"],
                    "ZipCode": business["location"]["zip_code"],
                    "Cuisine": cuisine,
                    "InsertedAtTimestamp": str(datetime.utcnow())  # Store timestamp
                })
        else:
            print(f"❌ Error fetching data: {response.status_code}, {response.text}")
        time.sleep(1)  # Prevent API rate limiting

    return restaurants


def convert_floats_to_decimal(item):
    """ Recursively converts float values to Decimal for DynamoDB compatibility """
    if isinstance(item, float):
        return Decimal(str(item))  # Convert float to string, then Decimal
    elif isinstance(item, dict):
        return {k: convert_floats_to_decimal(v) for k, v in item.items()}
    elif isinstance(item, list):
        return [convert_floats_to_decimal(v) for v in item]
    return item

def check_duplicate(business_id):
    """Check if a restaurant already exists in DynamoDB"""
    response = table.get_item(Key={"BusinessID": business_id})
    return "Item" in response

def store_in_dynamodb(restaurants):
    """Store restaurant data in DynamoDB, ensuring float values are converted to Decimal."""
    with table.batch_writer() as batch:
        for restaurant in restaurants:
            business_id = restaurant["BusinessID"]
            if check_duplicate(business_id):
                print(f"❌ Duplicate found: {restaurant['Name']} ({business_id}) - Skipping...")
                continue
            cleaned_item = convert_floats_to_decimal(restaurant)  # Convert before storing
            batch.put_item(Item=cleaned_item)  # Insert into DynamoDB
            print(f"✅ Stored: {restaurant['Name']} ({business_id})")


def lambda_handler(event, context):
    """AWS Lambda entry point"""
    for cuisine in CUISINES:
        print(f"🔹 Fetching {cuisine} restaurants...")
        data = get_restaurants(cuisine)
        print(f"✅ Storing {len(data)} {cuisine} restaurants in DynamoDB...")
        store_in_dynamodb(data)
    
    return {"status": "success", "message": "Data collection complete!"}
