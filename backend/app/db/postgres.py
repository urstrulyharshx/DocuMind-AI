import psycopg

from app.core.config import Config


def get_connection():
    return psycopg.connect(Config.DATABASE_URL)


def check_connection():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            return cur.fetchone()[0] == 1
