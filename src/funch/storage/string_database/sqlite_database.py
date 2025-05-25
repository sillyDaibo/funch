import sqlite3
from typing import Iterable
from .interface import StringDatabaseInterface


class SQLiteStringDatabase(StringDatabaseInterface):
    def __init__(self, db_path: str = ":memory:"):
        self.conn = sqlite3.connect(db_path)
        self._initialize_db()

    def _initialize_db(self) -> None:
        """Create the storage table if it doesn't exist."""
        cursor = self.conn.cursor()
        cursor.execute("""
CREATE TABLE IF NOT EXISTS storage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL
);""")
        self.conn.commit()

    def indexes(self) -> Iterable[int]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM storage")
        for row in cursor.fetchall():
            yield row[0]

    def query(self, index: int) -> str:
        cursor = self.conn.cursor()
        cursor.execute("SELECT content FROM storage WHERE id = ?", (index,))
        result = cursor.fetchone()
        return result[0] if result else ""

    def add(self, content: str) -> int:
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO storage (content) VALUES (?)", (content,))
        self.conn.commit()
        if (row_id := cursor.lastrowid) is None:
            raise RuntimeError("Failed to insert row")
        return row_id

    def update(self, index: int, content: str) -> None:
        cursor = self.conn.cursor()
        cursor.execute("UPDATE storage SET content = ? WHERE id = ?", (content, index))
        self.conn.commit()

    def delete(self, index: int) -> None:
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM storage WHERE id = ?", (index,))
        self.conn.commit()

    def __len__(self) -> int:
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM storage")
        return cursor.fetchone()[0]

    def __del__(self) -> None:
        self.conn.close()
