import boto3
import os

S3_BUCKET = os.getenv("S3_BUCKET_NAME", "researchmind-shubhrato-docs")
s3_client = boto3.client("s3", region_name="ap-south-1")

def upload_file_to_s3(file_bytes: bytes, key: str):
    s3_client.put_object(Bucket=S3_BUCKET, Key=key, Body=file_bytes)
    return key

def generate_presigned_url(key: str, expiration: int = 3600):
    return s3_client.generate_presigned_url(
        'get_object',
        Params={'Bucket': S3_BUCKET, 'Key': key},
        ExpiresIn=expiration
    )

def delete_file_from_s3(key: str):
    s3_client.delete_object(Bucket=S3_BUCKET, Key=key)