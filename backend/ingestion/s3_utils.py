import boto3
import os
from fastapi import HTTPException

S3_BUCKET = os.getenv("S3_BUCKET_NAME", "researchmind-shubhrato-docs")
s3_client = boto3.client("s3", region_name="ap-south-1")

def upload_file_to_s3(file_bytes: bytes, key: str):
    try:
        s3_client.put_object(Bucket=S3_BUCKET, Key=key, Body=file_bytes)
        return key
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")

def generate_presigned_url(key: str, expiration: int = 3600):
    try:
        return s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET, 'Key': key},
            ExpiresIn=expiration
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate download link: {str(e)}")

def delete_file_from_s3(key: str):
    try:
        s3_client.delete_object(Bucket=S3_BUCKET, Key=key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")