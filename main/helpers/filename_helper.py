import time


def generate_timestamped_id(feed_id: int) -> int:
    """
    Generates a unique ID based on the current epoch timestamp and the given feed_id.

    :param feed_id: An integer representing the feed ID.
    :return: An integer representing the sum of the current epoch timestamp and feed_id.
    """
    # Get the current epoch time in seconds as an integer
    timestamp = int(time.time())

    # Return the combined integer
    return timestamp + feed_id


#
#  Extracts the filename from the chunked audio url
#
def extract_filename_from_url(url):
    """
    Extracts the filename from an MP3 URL.

    Args:
        url (str): The URL of the MP3 file.

    Returns:
        str: The extracted filename from the URL.
    """
    try:
        # Split the URL by '/' and get the last part
        filename = url.split('/')[-1]
        return filename
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def extract_timestamp_from_filename(filename):
    """
    Extracts the numeric timestamp from a filename in the format 'timestamp-id.mp3'
    and returns it as an integer.

    Args:
        filename (str): The filename to extract the timestamp from.

    Returns:
        int: The extracted timestamp as an integer, or None if it cannot be parsed.
    """
    try:
        # Extract the part before the first hyphen
        timestamp_str = filename.split('-')[0]

        # Convert the extracted timestamp string into an integer
        timestamp_int = int(timestamp_str)

        return timestamp_int
    except Exception as e:
        print(f"An error occurred: {e}")
        return None