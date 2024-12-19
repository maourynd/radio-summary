import os
import json
import time

import boto3

from context import S3_GLUED_AUDIO_PATH, S3_GLUED_ARCHIVED_AUDIO_PATH, S3_TRANSCRIPTION_PATH
from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, REGION_NAME, BUCKET_NAME
from main.models.transcription import Transcription

def transcribe(db):
    """
    1. List all audio.mp3 files in S3 under S3_GLUED_AUDIO_PATH.
    2. Start a transcription job for each audio file found.
    3. Poll for the job completion.
    4. Once done, download the transcription JSON from S3, process it,
       archive the original audio to S3_GLUED_ARCHIVED_AUDIO_PATH,
       update the database record with the archived URL,
       and store the new transcription record in the database.
    """

    # Initialize S3 and Transcribe clients
    s3 = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=REGION_NAME
    )
    transcribe_client = boto3.client(
        'transcribe',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=REGION_NAME
    )

    # List all files in the audio directory
    response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=S3_GLUED_AUDIO_PATH)
    if 'Contents' not in response:
        print("No audio files to transcribe, exiting.")
        return

    # Filter files to only include .mp3 at the specified directory level
    mp3_files = [
        obj['Key'] for obj in response['Contents']
        if obj['Key'].endswith('.mp3') and obj['Key'].count('/') == S3_GLUED_AUDIO_PATH.count('/')
    ]

    if not mp3_files:
        print("No .mp3 files to glue.")
        return
    else:
        print("Found .mp3 files:", mp3_files)

    for item in mp3_files:
        key = item
        if key.endswith('-glued.mp3'):
            # Extract file_id from filename (e.g. "1734140358-glued.mp3" -> 1734140358)
            filename = os.path.basename(key)
            file_id_str = filename.split('-')[0]
            try:
                file_id = int(file_id_str)
            except ValueError:
                print(f"Skipping {filename}, could not parse file_id.")
                continue

            # Create transcription job name
            job_name = f"{file_id}-transcription-job"

            # Check if job is already completed in DB
            existing = Transcription.get_by_file_id(db, file_id)
            if existing:
                print(f"Transcription for {file_id} already processed. Retrieving existing job info...")
                # Since it's completed in the DB, presumably you have all data already. You can skip.
                continue

            # Check if transcription job already exists on AWS Transcribe
            try:
                existing_job = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
                job_status = existing_job['TranscriptionJob']['TranscriptionJobStatus']
                print(f"Found existing transcription job '{job_name}' with status: {job_status}")
            except transcribe_client.exceptions.BadRequestException:
                # Job doesn't exist, we will start a new job
                existing_job = None
                job_status = None

            output_key = f"{S3_TRANSCRIPTION_PATH}{file_id}-transcription.json"
            transcription_uri = f"s3://{BUCKET_NAME}/{output_key}"

            if not existing_job:
                # Start a new transcription job if not started
                audio_file_uri = f"s3://{BUCKET_NAME}/{key}"

                print(f"Starting a new transcription job for {filename}...")
                transcribe_client.start_transcription_job(
                    TranscriptionJobName=job_name,
                    Media={'MediaFileUri': audio_file_uri},
                    MediaFormat='mp3',
                    LanguageCode='en-US',
                    OutputBucketName=BUCKET_NAME,
                    OutputKey=output_key
                )
                job_status = 'IN_PROGRESS'

            # Poll until job is done if it's not completed yet
            while job_status not in ['COMPLETED', 'FAILED']:
                print("Job still in progress. Waiting 10 seconds...")
                time.sleep(10)
                status = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
                job_status = status['TranscriptionJob']['TranscriptionJobStatus']

            if job_status == 'FAILED':
                print(f"Transcription job {job_name} failed.")
                continue

            # Once completed, download and process the transcription JSON as before
            output_key = f"{S3_TRANSCRIPTION_PATH}{file_id}-transcription.json"
            obj = s3.get_object(Bucket=BUCKET_NAME, Key=output_key)
            transcription_data = json.loads(obj['Body'].read())
            transcripts = transcription_data.get("results", {}).get("transcripts", [])
            transcription_text = transcripts[0]["transcript"] if transcripts else ""

            # Move the original audio file to the archive location
            archive_key = f"{S3_GLUED_ARCHIVED_AUDIO_PATH}{filename}"
            s3.copy_object(
                Bucket=BUCKET_NAME,
                CopySource={'Bucket': BUCKET_NAME, 'Key': key},
                Key=archive_key
            )
            s3.delete_object(Bucket=BUCKET_NAME, Key=key)

            # Update the audio_url to point to the archived location
            archived_audio_url = f"s3://{BUCKET_NAME}/{archive_key}"

            # Save record in DB with updated audio_url (archived location)
            t = Transcription(
                file_id=file_id,
                data=transcription_data,
                transcription=transcription_text,
                summarized=False,
                audio_url=archived_audio_url,        # Updated to archived location
                transcribe_url=transcription_uri,
                summary_id = None
            )
            t.save(db)
            print(f"Saved transcription record for {file_id}, archived audio at {archived_audio_url}.")
        else:
            # Not a glued file, skip or handle differently if needed.
            pass
