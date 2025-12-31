import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="rppg_db",
        user="postgres",
        password="root",
        cursor_factory=RealDictCursor
    )
