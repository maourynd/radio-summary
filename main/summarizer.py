import logging

from main.generate_document import render_html
from main.gpt import get_gpt_response
from main.helpers.s3 import s3_helper
from main.models.summary import Summary
from main.models.transcription import Transcription
from main.send_email import send_email_via_mailchimp


def upload_transcription_text(text):
    try:
        s3_helper.upload_full_text_transcript(text)
    except Exception as e:
        logging.error(f"Failed to upload transcription text to S3: {e}")
        raise

def upload_summarized_text(text, summary_id):
    try:
        s3_helper.upload_summarized_text(text, summary_id)
    except Exception as e:
        logging.error(f"Failed to upload transcription text to S3: {e}")
        raise

def summarize(db):

    # 1. Query all transcriptions with summarized = false
    transcriptions = Transcription.get_all_by_summarized(db, False)

    # 2. Sort transcriptions by their file_id
    transcriptions.sort(key=lambda t: t.file_id)

    # 3. Concatenate their transcription text into one large string
    transcribed_text = " ".join([t.transcription for t in transcriptions])
    print(f"Transcribed text: {transcribed_text}")
    if not transcribed_text.strip():
        print("Error: No valid transcription text to summarize.")
        return {
            "status": "error",
            "message": "No valid transcription text to summarize."
        }

    # 4. Upload full transcription text to s3
    upload_transcription_text(transcribed_text)

    # 5. GPT the summary
    gpt_result = call_gpt_and_check(transcribed_text)
    if gpt_result["status"] == "success":
        print("Successfully GPT'd daily summary!")
    else:
        print("GPT Error:", gpt_result["message"])
        return {
            "status": "error",
            "message": "Could not summarize GPT result."
        }
    summarized_text = gpt_result["response"]

    # 6. Create and save a Summary object
    transcription_ids = [t.file_id for t in transcriptions]
    summary = Summary(
        text={"summary": summarized_text},
        transcription_file_ids=transcription_ids
    )
    summary.save(db)

    # 7. Upload summary to s3
    upload_summarized_text(summarized_text, summary.id)

    # 8. Update each transcription to mark them as summarized
    for t in transcriptions:
        try:
            #t.summarized = True
            t.summary_id = summary.id
            t.save(db)
        except Exception as e:
            logging.error(f"Failed to save transcription {t.file_id}: {e}")

    # 9. Generate HTML File for Summary
    html_file = render_html(summarized_text)

    # 10. Upload HTML file to s3
    s3_helper.upload_html_to_s3(html_file)

    # 11. Send to Mailchimp
    send_email_via_mailchimp(html_file)

    return summary


def call_gpt_and_check(transcribed_text: str) -> dict:
    """
    Calls the `get_gpt_response` function and checks if there was an error.

    Args:
        summary (str): The input text to use.

    Returns:
        dict: A dictionary containing the status and the response or error message.
        :param transcribed_text:
    """
    try:

        # Call the `get_gpt_response` function
        response = get_gpt_response(transcribed_text)

        # Check for error in the response
        if response.startswith("Error:"):
            return {"status": "error", "message": response}

        # Return success if no error
        return {"status": "success", "response": response}

    except Exception as e:
        # Handle unexpected exceptions
        return {"status": "error", "message": f"Unexpected error: {str(e)}"}