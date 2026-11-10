# Author/Operator: JACKAL
# Service: Zero-Trust PII Masking Worker

import boto3 
import json 
import re 
import time 
import uuid 

# Configure LocalStack Clients 
LOCALSTACK_URL = 'http://localhost:4566'
REGION = 'us-east-1'

sqs = boto3.client('sqs', 
                   endpoint_url=LOCALSTACK_URL, 
                   region_name=REGION,
                   aws_access_key_id='test',
                   aws_secret_access_key='test')

s3 = boto3.client('s3', 
                  endpoint_url=LOCALSTACK_URL, 
                  region_name=REGION,
                  aws_access_key_id='test',
                  aws_secret_access_key='test')

QUEUE_URL = f"{LOCALSTACK_URL}/000000000000/fintech-raw-logs"
BUCKET_NAME = 'fintech-masked-archive'

# Define PII Regex Patterns
PII_PATTERNS = {
    "CREDIT_CARD": r'\b(?:\d[ -]*?){13,16}\b',
    "AADHAR": r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
    "PAN": r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b'
}

def mask_data(text):
    """ Scans text and masks identified PII with X's. """
    masked_text = text 
    for pii_type, pattern in PII_PATTERNS.items():
        # Masks everything except the last 4 characters for context 
        def replacer(match):
            val = match.group(0)
            # Remove spaces/dashes to process the raw string 
            clean_val = re.sub(r'[\s-]', '', val)
            return f"XXXX-XXXX-XXXX-{clean_val[-4:]}" if len(clean_val) > 4 else "XXXX"
        masked_text = re.sub(pattern, replacer, masked_text)
    return masked_text 

def process_queue():
    print("JACKAL Masking Worker started. Polling LocalStack SQS...")
    while True:
        try:
            # Poll SQS Queue (Long Polling)
            response = sqs.receive_message(
                QueueUrl=QUEUE_URL,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=5 # Long polling reduces CPU/network thrashing 
            )

            messages = response.get('Messages', [])
            if not messages:
                continue

            for message in messages:
                receipt_handle = message['ReceiptHandle']
                body = message['Body']

                print("\n[+] Received new log event.")

                # Mask the Payload 
                sanitized_body = mask_data(body)

                # Archive to S3 
                log_id = str(uuid.uuid4())
                s3_key = f"sanitized-logs/{time.strftime('%Y-%m-%d')}/log_{log_id}.json"

                s3.put_object(
                    Bucket=BUCKET_NAME,
                    Key=s3_key,
                    Body=sanitized_body,
                    ContentType='application/json'
                )

                print(f"[+] Sanitized log archived to S3: s3://{BUCKET_NAME}/{s3_key}")

                # Delete message from queue so it isn't processed again
                sqs.delete_message(
                    QueueUrl=QUEUE_URL,
                    ReceiptHandle=receipt_handle
                )
                print("[+] Message removed from SQS.")

        except Exception as e:
            print(f"[!] Error processing message: {str(e)}")
            time.sleep(5)

if __name__ == "__main__":
    process_queue()