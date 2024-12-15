import boto3
import io
import time

from botocore.exceptions import ClientError, BotoCoreError

from pydub import AudioSegment

from config import AWS_ACCESS_KEY_ID, REGION_NAME, BUCKET_NAME, AWS_SECRET_ACCESS_KEY
from context import S3_AUDIO_PATH, S3_GLUED_AUDIO_PATH


def glue():
    """
    Downloads all MP3 files from a specific S3 folder into memory, sorts them by the integer
    prefix in the filename, concatenates them into one MP3, and uploads the glued MP3 to S3.
    """

    aws_access_key_id = AWS_ACCESS_KEY_ID
    aws_secret_access_key = AWS_SECRET_ACCESS_KEY
    region_name = REGION_NAME
    bucket = BUCKET_NAME
    audio_path = S3_AUDIO_PATH
    glued_path = S3_GLUED_AUDIO_PATH

    # Initialize S3 client
    s3 = boto3.client(
        "s3",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name
    )

    # List all objects in the given prefix
    response = s3.list_objects_v2(Bucket=bucket, Prefix=audio_path)
    if 'Contents' not in response:
        print(f"No objects found under prefix {audio_path}")
        return False

    # Filter for MP3 files
    mp3_keys = [obj['Key'] for obj in response['Contents'] if obj['Key'].endswith('.mp3')]

    if not mp3_keys:
        print("No MP3 files to download and glue.")
        return False

    # Parse the filenames to extract the numeric prefix for sorting
    # Assuming filenames like "1734125390-1311.mp3"
    def extract_sort_key(key):
        filename = key.split('/')[-1]  # get the file name from the key
        base_name = filename.rsplit('.', 1)[0]  # remove extension
        numeric_part = base_name.split('-')[0]   # "1734125390"
        return int(numeric_part) if numeric_part.isdigit() else float('inf')

    mp3_keys.sort(key=extract_sort_key)

    print("Gluing...")
    # Download each MP3 into memory and concatenate using pydub
    combined_audio = None
    for mp3_key in mp3_keys:
        # Download MP3 into memory
        mp3_obj = io.BytesIO()
        s3.download_fileobj(BUCKET_NAME, mp3_key, mp3_obj)
        mp3_obj.seek(0)

        # Create an AudioSegment
        segment = AudioSegment.from_file(mp3_obj, format="mp3")

        if combined_audio is None:
            combined_audio = segment
        else:
            combined_audio += segment

    if combined_audio is None:
        print("No audio segments found to combine.")
        return False

    # Generate a new filename using the current epoch timestamp
    glued_filename = f"{int(time.time())}-glued.mp3"

    # Export the combined audio to memory
    glued_buffer = io.BytesIO()
    combined_audio.export(glued_buffer, format="mp3")
    glued_buffer.seek(0)

    # Upload the glued MP3 to S3
    final_s3_key = f"{glued_path}{glued_filename}"

    try:
        s3.upload_fileobj(glued_buffer, bucket, final_s3_key)
        print(f"Glued MP3 uploaded to s3://{bucket}/{final_s3_key}")
        return True
    except (BotoCoreError, ClientError) as e:
        print(f"Failed to upload glued file: {e}")
        return False




