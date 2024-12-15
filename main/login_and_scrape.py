import os
import pickle

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from main.helpers import filename_helper
from main.helpers.s3 import s3_helper

# Configuration
COOKIES_FILE = "../cookies.pkl"
LOGIN_URL = "https://www.broadcastify.com/login/"
TARGET_URL = "https://www.broadcastify.com/calls/tg/6957/1311"

def login(driver, email, password):

    driver.get(LOGIN_URL)

    # Wait for log in form
    email_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "signinSrEmail"))
    )
    email_field.send_keys(email)

    password_field = driver.find_element(By.ID, "signinSrPassword")
    password_field.send_keys(password)
    password_field.send_keys(Keys.RETURN)

    # Wait for login success
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "myAccount"))
    )
    print("Login successful.")

    # Save cookies to a file
    with open(COOKIES_FILE, "wb") as f:
        pickle.dump(driver.get_cookies(), f)


def upload_chunked_audio_s3(mp3_urls, db):

    for url in mp3_urls:

        curr_filename = os.path.basename(url)
        curr_filename_timestamp = filename_helper.extract_timestamp_from_filename(curr_filename)

        last_uploaded_filename = db.get_last_uploaded_filename()
        if not last_uploaded_filename:
            # No previously uploaded file - maybe just proceed or set a baseline.
            last_uploaded_timestamp = 0
        else:
            last_uploaded_timestamp = filename_helper.extract_timestamp_from_filename(last_uploaded_filename)

        # If the current file's timestamp is older or equal to the last uploaded timestamp, skip it
        if curr_filename_timestamp <= last_uploaded_timestamp:
            print(f"Already uploaded {curr_filename}")
            continue
        else:
            # upload new audio to s3
            if s3_helper.upload_mp3_to_s3(url):
                # increment db counter
                db.increment_counter()
                # save new latest filename
                db.set_last_uploaded_filename(curr_filename)


def extract_id_from_filename(filename):
    name, _ = os.path.splitext(filename)
    parts = name.split('-')
    return int(parts[0])  # Adjust logic if needed

def load_cookies(driver):
    """Loads cookies from a file into the current session."""
    if os.path.exists(COOKIES_FILE):
        with open(COOKIES_FILE, "rb") as f:
            cookies = pickle.load(f)
            for cookie in cookies:
                driver.add_cookie(cookie)

def sort_audio(mp3_urls):
    # Sort by the numeric portion of the filename before the first '-'
    sorted_urls = sorted(mp3_urls, key=lambda url: int(os.path.basename(url).split('-')[0]))
    return sorted_urls  # No need to reverse, as this is in ascending order

def run_broadcastify_job(driver, db, email, password):
    try:
        # Step 1: Load cookies and navigate to the target URL
        driver.get(TARGET_URL)
        load_cookies(driver)
        driver.refresh()  # Refresh to apply cookies

        # Step 2: Check if logged in
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "callsTable"))
            )
        except:
            login(driver, email, password)
            driver.get(TARGET_URL)

        # Step 3: Wait for the table to load
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "callsTable")))
        print("Target page loaded." + driver.current_url)

        # Step 4: Find MP3 links
        calls_table = driver.find_element(By.ID, "callsTable")
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#callsTable a[href$='.mp3']")))
        mp3_links = calls_table.find_elements(By.CSS_SELECTOR, "a[href$='.mp3']")
        mp3_urls = [link.get_attribute("href") for link in mp3_links]
        sorted_urls = sort_audio(mp3_urls)

        # Step 5: Upload Audio to S3
        upload_chunked_audio_s3(sorted_urls, db)
        driver.quit()

    finally:
        driver.quit()
