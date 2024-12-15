# db/database.py
import sqlite3
from pathlib import Path

from main.models.summary import Summary
from main.models.transcription import Transcription


class Database:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = Path("~/Radio Summary/radio_summary.db").expanduser()
        self.db_path = db_path
        # Ensure the parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.create_tables()
    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.conn.row_factory = sqlite3.Row
        return self.conn

    def create_tables(self):

        # create non-object tables

        create_counter_table = """
        CREATE TABLE IF NOT EXISTS counter (
            id INTEGER PRIMARY KEY, 
            value INTEGER
        );
        """

        insert_counter = """
        INSERT OR IGNORE INTO counter (id, value) VALUES (1, 0);
        """

        create_last_uploaded_table = """
        CREATE TABLE IF NOT EXISTS last_uploaded (
            id INTEGER PRIMARY KEY,
            filename TEXT
        );
        """

        insert_last_uploaded = """
        INSERT OR IGNORE INTO last_uploaded (id, filename) VALUES (1, '0-0.mp3');
        """

        create_last_transcribed_table = """
        CREATE TABLE IF NOT EXISTS last_transcribed (
            id INTEGER PRIMARY KEY,
            filename TEXT
        );
        """

        insert_last_transcribed = """
        INSERT OR IGNORE INTO last_transcribed (id, filename) VALUES (1, '0-0.mp3');
        """

        # create object tables

        Transcription.create_table(self)
        Summary.create_table(self)

        self.conn.execute(create_last_uploaded_table)
        self.conn.execute(create_last_transcribed_table)
        self.conn.execute(create_counter_table)

        self.conn.execute(insert_last_uploaded)
        self.conn.execute(insert_last_transcribed)
        self.conn.execute(insert_counter)

        self.conn.commit()

    def get_counter(self):
        """Retrieve the counter value from the database."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM counter WHERE id = 1;")
        result = cursor.fetchone()
        return result["value"] if result else 0

    def increment_counter(self):
        """Increment the counter value in the database."""
        cursor = self.conn.cursor()
        cursor.execute("UPDATE counter SET value = value + 1 WHERE id = 1;")
        self.conn.commit()
        cursor.execute("SELECT value FROM counter WHERE id = 1;")
        result = cursor.fetchone()
        if result:
            counter_value = result[0]
            print("Audio Upload Counter: " + str(counter_value))
            return counter_value
        else:
            raise RuntimeError("Failed to fetch the counter value.")

    def set_last_uploaded_filename(self, filename):
        """
        Set the last uploaded filename in the database.
        If the record does not exist, it will be created.
        """
        cursor = self.conn.cursor()
        try:
            # Check if the record exists
            cursor.execute("SELECT COUNT(*) FROM last_uploaded WHERE id = 1;")
            result = cursor.fetchone()

            if result and result[0] == 0:
                # Record doesn't exist, create it
                cursor.execute("INSERT INTO last_uploaded (id, filename) VALUES (1, ?);", (filename,))
            else:
                # Update the existing record
                cursor.execute("UPDATE last_uploaded SET filename = ? WHERE id = 1;", (filename,))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise RuntimeError(f"Failed to set the last uploaded filename: {e}")
        finally:
            cursor.close()

    def get_last_uploaded_filename(self):
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT filename FROM last_uploaded WHERE id = 1;")
            result = cursor.fetchone()
            if result:
                last_filename = result[0]
                return last_filename
            else:
                return None
        except Exception as e:
            raise RuntimeError(f"Failed to fetch the last uploaded filename: {e}")
        finally:
            cursor.close()


    def set_last_transcribed_filename(self, filename):
        """
        Set the last uploaded filename in the database.
        If the record does not exist, it will be created.
        """
        cursor = self.conn.cursor()
        try:
            # Check if the record exists
            cursor.execute("SELECT COUNT(*) FROM last_transcribed WHERE id = 1;")
            result = cursor.fetchone()

            if result and result[0] == 0:
                # Record doesn't exist, create it
                cursor.execute("INSERT INTO last_transcribed (id, filename) VALUES (1, ?);", (filename,))
            else:
                # Update the existing record
                cursor.execute("UPDATE last_transcribed SET filename = ? WHERE id = 1;", (filename,))
                print(f"Updated last transcribed filename to: {filename}")
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise RuntimeError(f"Failed to set the last transcribed filename: {e}")
        finally:
            cursor.close()

    def get_last_transcribed_filename(self):
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT filename FROM last_transcribed WHERE id = 1;")
            result = cursor.fetchone()
            if result:
                last_filename = result[0]
                return last_filename
            else:
                return None
        except Exception as e:
            raise RuntimeError(f"Failed to fetch the last transcribed filename: {e}")
        finally:
            cursor.close()

    def reset_counter(self):
        """Reset the counter value to 0 in the database."""
        cursor = self.conn.cursor()
        try:
            cursor.execute("UPDATE counter SET value = 0 WHERE id = 1;")
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise RuntimeError(f"Failed to reset the counter: {e}")
        finally:
            cursor.close()

    def close(self):
        if self.conn:
            self.conn.close()
