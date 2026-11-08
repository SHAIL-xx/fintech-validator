import boto3

def get_local_client(service_name: str):
    """Returns a Boto3 client configured for LocalStack."""
    return boto3.client(
        service_name,
        endpoint_url="http://127.0.0.1:4566",
        region_name="us-east-1",
        aws_access_key_id="test",
        aws_secret_access_key="test"
    )