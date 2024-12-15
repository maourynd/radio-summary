import os
import time

import schedule
from dotenv import load_dotenv

from sqlalchemy.orm import declarative_base
from main.gluer import glue
from main.login_and_scrape import run_broadcastify_job
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
    #wipe_database(db)
    #db.close()


    # iterate scrape-age
    execute(db)
    schedule.every(5).minutes.do(execute, db)
    #schedule.every(6).hours.do(summarize)

    #summarize
    #transcribe(db)
    #summarize(db)
    #db.close()

    while True:
        schedule.run_pending()
        time.sleep(1)



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