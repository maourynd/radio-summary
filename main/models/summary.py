import json
from datetime import datetime
from sqlite3 import Connection
from typing import List, Optional


class Summary:
    def __init__(
            self,
            text: dict,
            transcription_file_ids: List[int],
            created_date: str = None,
            id: Optional[int] = None  # Added id as an optional parameter
    ):
        # ... existing validation ...

        self.id = id  # Correctly assign the provided id
        self.text = text
        self.transcription_file_ids = transcription_file_ids
        self.created_date = created_date or datetime.now().isoformat()

    @classmethod
    def create_table(cls, db):
        create_table_sql = """
               CREATE TABLE IF NOT EXISTS summary (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   data TEXT,
                   transcription_file_ids TEXT,
                   created_date TEXT
               );
            """
        db.conn.execute(create_table_sql)
        db.conn.commit()

    def save(self, db):

        if self.id is not None:
            # Update existing record
            update_sql = """
                UPDATE summary
                SET data = ?, transcription_file_ids = ?
                WHERE id = ?
                """
            db.conn.execute(
                update_sql,
                (json.dumps(self.text), json.dumps(self.transcription_file_ids), self.id)
            )
        else:
            # Insert new record (set created_date)
            insert_sql = """
                            INSERT INTO summary (data, transcription_file_ids, created_date)
                            VALUES (?, ?, ?)
                            """
            cursor = db.conn.execute(
                insert_sql,
                (json.dumps(self.text), json.dumps(self.transcription_file_ids), self.created_date)
            )
            self.id = cursor.lastrowid
        db.conn.commit()

    def set_text(self, text: dict):
        """
        Set the text attribute.
        """
        self.text = text

    def get_text(self) -> dict:
        """
        Return the text (summary).
        """
        return self.text

    def get_transcription_file_ids(self) -> List[int]:
        """
        Get the list of transcription file IDs.
        """
        return self.transcription_file_ids

    def set_transcription_file_ids(self, ids: List[int]):
        """
        Set the list of transcription file IDs.
        """
        if not isinstance(ids, list):
            raise ValueError("transcription_file_ids must be a list")
        self.transcription_file_ids = ids

    @classmethod
    def load(cls, db, id_val: int):
        """
        Load a Summary object by ID from the database.
        """
        select_sql = "SELECT id, data, transcription_file_ids FROM summary WHERE id = ?"
        cursor = db.conn.execute(select_sql, (id_val,))
        row = cursor.fetchone()
        if row:
            return cls(
                text=json.loads(row["data"]),
                transcription_file_ids=json.loads(row["transcription_file_ids"]),
                created_date=row["created_date"]
            )
        return None
