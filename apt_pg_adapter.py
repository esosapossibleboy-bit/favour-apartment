import os
import sqlite3

class PgCursorWrapper:
    def __init__(self, cur):
        self._cur = cur

    def _adapt(self, sql: str) -> str:
        adapted = sql.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
        return adapted.replace("?", "%s")

    def execute(self, sql: str, params=()):
        self._cur.execute(self._adapt(sql), params)
        return self

    def fetchone(self):
        return self._cur.fetchone()

    def fetchall(self):
        return self._cur.fetchall()

    @property
    def rowcount(self):
        return self._cur.rowcount

class PgConnWrapper:
    def __init__(self, pg_conn):
        self._conn = pg_conn

    def cursor(self):
        return PgCursorWrapper(self._conn.cursor())

    def execute(self, sql: str, params=()):
        cur = self.cursor()
        cur.execute(sql, params)
        return cur

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

def open_apartment_db(sqlite_path: str = "apartment_tours.db"):
    db_url = os.getenv("DATABASE_URL", "").strip()
    if db_url and not sqlite_path.startswith("temp_"):
        import psycopg2
        if db_url.startswith("postgres://"):
            db_url = "postgresql://" + db_url[len("postgres://"):]
        return PgConnWrapper(psycopg2.connect(db_url))
    return sqlite3.connect(sqlite_path)
