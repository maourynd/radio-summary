import time
from io import BytesIO

import boto3
import requests
from botocore.exceptions import ClientError, NoCredentialsError

from context import S3_FULL_TEXT_PATH, S3_SUMMARY_TEXT_PATH, S3_HTML_PATH
from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, REGION_NAME, BUCKET_NAME
from main.helpers import filename_helper


def upload_full_text_transcript(text):
    """
    Uploads the provided text to an S3 bucket as a .txt file with a Unix timestamp as part of the filename.
    """
    # Initialize the S3 client
    s3 = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=REGION_NAME
    )

    # Generate a unique filename using the Unix timestamp
    unix_timestamp = int(time.time())
    s3_key = f"{S3_FULL_TEXT_PATH}{unix_timestamp}.txt"

    # Prepare the text as a file-like object
    text_bytes = BytesIO(text.encode("utf-8"))

    try:
        # Upload to S3
        s3.upload_fileobj(text_bytes, BUCKET_NAME, s3_key)
        print(f"Successfully uploaded text to S3: {s3_key}")
    except Exception as e:
        print(f"Failed to upload text to S3: {e}")

def upload_mp3_to_s3(url):
    """
    Downloads an MP3 file from the given URL and uploads it to the specified S3 bucket.

    :param url: URL of the MP3 file to download.
    """
    try:
        # Step 1: Download the MP3 file from the URL
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise an exception for HTTP errors
        print(f"Downloaded MP3 file from {url}, beginning upload to s3...")

        # prep s3 client
        s3 = boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=REGION_NAME
        )
        s3_key = "audio-files/" + filename_helper.extract_filename_from_url(url)

        # upload to s3
        s3.upload_fileobj(response.raw, BUCKET_NAME, s3_key)
        print(f"Uploaded MP3 file to s3://{BUCKET_NAME}/{s3_key}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"Failed to upload chunked MP3 file to s3: {e}")
        return False

def file_exists_in_s3(s3_key):
    """
    Checks if a file exists in the specified S3 bucket.

    :param bucket_name: Name of the S3 bucket.
    :param s3_key: Key (path) of the file in the bucket.
    :return: True if the file exists, False otherwise.
    """
    s3 = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=REGION_NAME
    )

    try:
        s3.head_object(Bucket=BUCKET_NAME, Key=s3_key)
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == "404":
            return False
        else:
            raise


def delete_directory_files():
    """
    Deletes all files in the given directory (prefix) within the S3 bucket.
    :param directory_prefix: The prefix (folder path) in the S3 bucket where files should be deleted.
                             For example: 'audio-files/'
    """
    s3 = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=REGION_NAME
    )

    directory_prefix = "audio-files/"

    try:
        paginator = s3.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=BUCKET_NAME, Prefix=directory_prefix)

        keys_to_delete = []
        for page in pages:
            if "Contents" in page:
                for obj in page["Contents"]:
                    keys_to_delete.append({"Key": obj["Key"]})

        if not keys_to_delete:
            print(f"No files found in directory: {directory_prefix}")
            return

        # batch delete in s3
        for i in range(0, len(keys_to_delete), 1000):
            chunk = keys_to_delete[i:i+1000]
            s3.delete_objects(
                Bucket=BUCKET_NAME,
                Delete={"Objects": chunk}
            )

        print(f"All files deleted in directory: {directory_prefix}")

    except ClientError as e:
        print(f"Failed to delete files in {directory_prefix}: {e}")

def upload_html_to_s3(content: str) -> bool:
    # Generate HTML document

    s3 = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=REGION_NAME
    )

    unix_timestamp = int(time.time())
    key = S3_HTML_PATH + str(unix_timestamp)

    try:
        # Upload the HTML content
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=key,
            Body=content,
            ContentType='text/html'
        )
        print(f"HTML uploaded successfully to s3://{BUCKET_NAME}/{key}")
        return True
    except NoCredentialsError:
        print("AWS credentials not found or invalid")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False


def upload_summarized_text(text, summary_id):

    s3 = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=REGION_NAME
    )
    s3_key = f"{S3_SUMMARY_TEXT_PATH}{summary_id}.txt"

    # Prepare the text as a file-like object
    text_bytes = BytesIO(text.encode("utf-8"))

    try:
        # Upload to S3
        s3.upload_fileobj(text_bytes, BUCKET_NAME, s3_key)
        print(f"Successfully uploaded summarized text to S3: {s3_key}")
    except Exception as e:
        print(f"Failed to upload text to S3: {e}")