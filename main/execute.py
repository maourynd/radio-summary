import os
import time
from datetime import datetime

import pytz
import schedule
from dotenv import load_dotenv

from sqlalchemy.orm import declarative_base

from main.gluer import glue
from main.login_and_scrape import run_broadcastify_job
from main.summarizer import summarize
from main.transcriber import transcribe
from main.db.database import Database
from main.helpers.s3 import s3_helper
from main.utils import setup_chrome_driver

# -- Main Fields -- #

Base = declarative_base()
feed_id = "1311"

# -- Functions -- #

# Uses selenium to log-in and scrape audio
def scrape(db):
    driver = setup_chrome_driver()
    email = get_env_variable("BROADCASTIFY_EMAIL")
    password = get_env_variable("BROADCASTIFY_PASSWORD")
    run_broadcastify_job(driver, db, email, password)

def wipe_database(db):
    """
    Drops all tables in the SQLite database and starts clean.
    """
    connection = db.connect()  # Assuming `db.connect()` returns a SQLite connection object
    cursor = connection.cursor()

    db.reset_counter()

    # Fetch all tables in the database
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    # Drop each table
    for table_name in tables:
        if table_name[0] != "sqlite_sequence":  # Skip SQLite's internal sequence table (if exists)
            cursor.execute(f"DROP TABLE IF EXISTS {table_name[0]};")

    connection.commit()
    print("Database wiped successfully.")

def get_env_variable(var_name):
    return os.getenv(var_name)

def startup():
    load_dotenv()
    db = Database()
    db.connect()
    db.create_tables()
    return db

# Executes Script
def main():

    db = startup()

    #summarize(db)

    # Wipe DB for testing if needed
    #wipe_database(db)

    # Execution Code
    execute(db)
    schedule.every(5).minutes.do(execute, db)

    # summarize and email at 7:30AM every day
    schedule_summarizer_task(7, 30, db)

    while True:
        schedule.run_pending()
        time.sleep(1)


def schedule_summarizer_task(hour, minute, db):
    def wrapper():
        est = pytz.timezone('US/Eastern')
        now = datetime.now(est)
        print(f"Executing task at {now}")
        summarize(db)

    # Schedule the function at the specific time in EST
    schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(wrapper)

# scrapes, glues, and transcribes
def execute(db):
    scrape(db)

    # glue audio
    counter_value = db.get_counter()
    if counter_value >= 25:
        if glue():
            db.reset_counter()
            s3_helper.delete_directory_files()

    # transcribe audio
    transcribe(db)


if __name__ == "__main__":
    main()