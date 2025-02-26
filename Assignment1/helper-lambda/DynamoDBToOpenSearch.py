import json
import urllib3
from base64 import b64encode
# OpenSearch Configuration
OPENSEARCH_HOST = "https://search-restaurant-search-new-m5jzetu7zoaydikncu57gywtva.us-east-1.es.amazonaws.com"
INDEX_NAME = "restaurants"
OPENSEARCH_USER = "USER Place holder"
OPENSEARCH_PASS = "PASS Place holder"

# Encode OpenSearch credentials for Basic Auth
auth_headers = {
    "Authorization": "Basic " + b64encode(f"{OPENSEARCH_USER}:{OPENSEARCH_PASS}".encode()).decode(),
    "Content-Type": "application/json"
}

# Initialize HTTP Client
http = urllib3.PoolManager()

def lambda_handler(event, context):
    print("Received event:", json.dumps(event, indent=2))  # Debugging log

    for record in event["Records"]:
        if "dynamodb" not in record or "NewImage" not in record["dynamodb"]:
            print("Skipping record due to missing 'NewImage':", record)
            continue

        new_image = record["dynamodb"]["NewImage"]

        # Ensure BusinessID and Cuisine exist before indexing
        if "BusinessID" not in new_image or "Cuisine" not in new_image:
            print("Skipping record due to missing required fields:", new_image)
            continue

        document = {
            "BusinessID": new_image["BusinessID"]["S"],  # Store BusinessID
            "Cuisine": new_image["Cuisine"]["S"]
        }
        doc_id = new_image["BusinessID"]["S"]

        # OpenSearch PUT Request (Index Data)
        url = f"{OPENSEARCH_HOST}/{INDEX_NAME}/_doc/{doc_id}"
        response = http.request("PUT", url, body=json.dumps(document), headers=auth_headers)

        print(f"Indexed document {doc_id}: {response.status}, {response.data.decode()}")

    return {"statusCode": 200, "body": "Processing complete"}