# agent_state.py -- durable SQLite-backed state for edge agents (survives reboots)
import sqlite3, json
from datetime import datetime, UTC

class EdgeAgentState:
    def __init__(self, db_path: str = "agent_state.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS memory (key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS task_log (id INTEGER PRIMARY KEY AUTOINCREMENT, task TEXT, result TEXT, started_at TEXT, completed_at TEXT);
            CREATE TABLE IF NOT EXISTS sensor_history (sensor_id TEXT, value REAL, recorded_at TEXT);
            CREATE INDEX IF NOT EXISTS idx_sensor ON sensor_history(sensor_id, recorded_at DESC);
        """)
        self.conn.commit()

    def remember(self, key: str, value: object) -> None:
        self.conn.execute("INSERT OR REPLACE INTO memory VALUES (?, ?, ?)",
                          (key, json.dumps(value), datetime.now(UTC).isoformat()))
        self.conn.commit()

    def recall(self, key: str, default=None) -> object:
        row = self.conn.execute("SELECT value FROM memory WHERE key = ?", (key,)).fetchone()
        return json.loads(row[0]) if row else default

    def record_sensor(self, sensor_id: str, value: float) -> None:
        self.conn.execute("INSERT INTO sensor_history VALUES (?, ?, ?)",
                          (sensor_id, value, datetime.now(UTC).isoformat()))
        self.conn.commit()

    def get_sensor_trend(self, sensor_id: str, last_n: int = 10) -> list[float]:
        rows = self.conn.execute(
            "SELECT value FROM sensor_history WHERE sensor_id = ? ORDER BY recorded_at DESC LIMIT ?",
            (sensor_id, last_n)).fetchall()
        return [r[0] for r in reversed(rows)]
