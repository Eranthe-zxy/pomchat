import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import json

@dataclass
class Message:
    content: str
    author: str
    timestamp: datetime
    repository: str
    commit_url: Optional[str] = None
    message_id: Optional[str] = None

class DatabaseManager:
    def __init__(self, db_path: str = "messages.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    author TEXT DEFAULT 'Anonymous',
                    timestamp TEXT NOT NULL,
                    github_url TEXT,
                    repository TEXT DEFAULT 'local'
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON messages(timestamp DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_repository ON messages(repository)")

    def add_message(self, message: Message) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO messages (content, author, timestamp, github_url, repository)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    message.content,
                    message.author,
                    message.timestamp.isoformat(),
                    message.commit_url,
                    message.repository
                )
            )
            return cursor.lastrowid

    def get_messages(self, limit: int = 100) -> List[Message]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM messages
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limit,)
            )
            
            messages = []
            for row in cursor:
                messages.append(Message(
                    content=row['content'],
                    author=row['author'],
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    repository=row['repository'],
                    commit_url=row['github_url'],
                    message_id=str(row['id'])
                ))
            
            return messages

    def add_messages_batch(self, messages: List[Message]) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany(
                """
                INSERT INTO messages (content, author, timestamp, github_url, repository)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        msg.content,
                        msg.author,
                        msg.timestamp.isoformat(),
                        msg.commit_url,
                        msg.repository
                    )
                    for msg in messages
                ]
            )
