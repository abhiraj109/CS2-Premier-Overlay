"""Store only local match observations, independent of the profile API."""

from contextlib import closing
import sqlite3
from pathlib import Path
from typing import Any


class MatchHistory:
    def __init__(self, path: Path):
        self.path = path

    def connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path)
        try:
            db.execute("""CREATE TABLE IF NOT EXISTS matches (
                id TEXT PRIMARY KEY, steam_id TEXT NOT NULL, finished_at REAL NOT NULL,
                map_name TEXT NOT NULL, mode TEXT NOT NULL, outcome TEXT NOT NULL,
                ct_score INTEGER NOT NULL, t_score INTEGER NOT NULL,
                kills INTEGER, deaths INTEGER, assists INTEGER
            )""")
            db.execute("""CREATE INDEX IF NOT EXISTS matches_account_time
                          ON matches (steam_id, finished_at DESC)""")
            return db
        except sqlite3.Error:
            db.close()
            raise

    def record(self, match: tuple) -> bool:
        with closing(self.connect()) as db, db:
            cursor = db.execute(
                "INSERT OR IGNORE INTO matches VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", match
            )
            db.execute("""DELETE FROM matches WHERE steam_id = ? AND id NOT IN (
                SELECT id FROM matches WHERE steam_id = ? ORDER BY finished_at DESC, id DESC LIMIT 20
            )""", (match[1], match[1]))
            return cursor.rowcount == 1

    def recent(self, steam_id: str) -> list[dict[str, Any]]:
        with closing(self.connect()) as db:
            db.row_factory = sqlite3.Row
            return [dict(row) for row in db.execute(
                "SELECT * FROM matches WHERE steam_id = ? ORDER BY finished_at DESC, id DESC LIMIT 20",
                (steam_id,),
            )]
