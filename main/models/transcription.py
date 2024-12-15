import json
import sqlite3
from typing import Optional, List, Dict, Any


class Transcription:
    def __init__(
        self,
        file_id: int,
        data: Dict[str, Any],
        transcription: str,
        summarized: bool,
        audio_url: str,
        transcribe_url: str,
        summary_id: Optional[int] = None,
    ):
        if not isinstance(data, dict):
            raise ValueError("data must be a dictionary")
        self.file_id = file_id
        self.data = data
        self.transcription = transcription
        self.summarized = summarized
        self.audio_url = audio_url
        self.transcribe_url = transcribe_url
        self.summary_id = summary_id

    @classmethod
    def create_table(cls, db):
        create_table_sql = """
            CREATE TABLE IF NOT EXISTS transcription (
                file_id INTEGER PRIMARY KEY,
                data TEXT NOT NULL,
                transcription TEXT NOT NULL,
                summarized INTEGER NOT NULL,
                audio_url TEXT NOT NULL,
                transcribe_url TEXT NOT NULL,
                summary_id INTEGER,
                FOREIGN KEY (summary_id) REFERENCES summary (id) ON DELETE CASCADE  
            );
        """
        db.conn.execute(create_table_sql)

        # Create an index on the summarized field for faster lookups
        db.conn.execute("CREATE INDEX IF NOT EXISTS idx_transcription_summarized ON transcription (summarized);")

        db.conn.commit()

    @classmethod
    def get_by_file_id(cls, db, file_id: int) -> Optional['Transcription']:
        """
        Retrieves a transcription by its file_id.
        """
        try:
            cursor = db.conn.execute("SELECT * FROM transcription WHERE file_id = ?", (file_id,))
            row = cursor.fetchone()
            if row:
                return cls(
                    file_id=row["file_id"],
                    data=json.loads(row["data"]),
                    transcription=row["transcription"],
                    summarized=bool(row["summarized"]),
                    audio_url=row["audio_url"],
                    transcribe_url=row["transcribe_url"],
                    summary_id=row["summary_id"] if row["summary_id"] is not None else None
                )
        except Exception as e:
            print(f"Error retrieving transcription: {e}")
        return None

    @classmethod
    def get_all_by_summarized(cls, db, summarized: bool) -> List['Transcription']:
        """
        Retrieves all transcriptions based on the summarized flag.
        """
        val = 1 if summarized else 0
        cursor = db.conn.execute(
            "SELECT * FROM transcription WHERE summarized = ?",
            (val,)
        )
        rows = cursor.fetchall()
        return [
            cls(
                file_id=row["file_id"],
                data=json.loads(row["data"]) if row["data"] else {},
                transcription=row["transcription"],
                summarized=bool(row["summarized"]),
                audio_url=row["audio_url"],
                transcribe_url=row["transcribe_url"],
                summary_id=row["summary_id"] if row["summary_id"] is not None else None
            )
            for row in rows
        ]

    @classmethod
    def update_summarized(cls, db, file_id: int, summarized: bool) -> bool:
        val = 1 if summarized else 0
        db.conn.execute(
            "UPDATE transcription SET summarized = ? WHERE file_id = ?",
            (val, file_id)
        )
        db.conn.commit()
        return db.conn.total_changes > 0

    def save(self, db):
        """
        Saves the transcription to the database.
        If the transcription exists (based on file_id), it updates the record.
        Otherwise, it inserts a new record.
        """
        try:
            # Check if the transcription already exists
            cursor = db.conn.execute("SELECT 1 FROM transcription WHERE file_id = ?", (self.file_id,))
            exists = cursor.fetchone() is not None

            if exists:
                # Update existing record
                update_sql = """
                    UPDATE transcription
                    SET data = ?, transcription = ?, summarized = ?, audio_url = ?, transcribe_url = ?, summary_id = ?
                    WHERE file_id = ?
                """
                db.conn.execute(
                    update_sql,
                    (
                        json.dumps(self.data),
                        self.transcription,
                        1 if self.summarized else 0,
                        self.audio_url,
                        self.transcribe_url,
                        self.summary_id,
                        self.file_id
                    )
                )
            else:
                # Insert new record
                insert_sql = """
                    INSERT INTO transcription (file_id, data, transcription, summarized, audio_url, transcribe_url, summary_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """
                db.conn.execute(
                    insert_sql,
                    (
                        self.file_id,
                        json.dumps(self.data),
                        self.transcription,
                        1 if self.summarized else 0,
                        self.audio_url,
                        self.transcribe_url,
                        self.summary_id
                    )
                )
            db.conn.commit()

        except sqlite3.IntegrityError as ie:
            print(f"Integrity Error saving transcription: {ie}")
        except Exception as e:
            print(f"Error saving transcription: {e}")
