import mysql.connector

DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",
    "password": "",       # XAMPP default is empty
    "database": "rag_db",
}


def get_db():
    return mysql.connector.connect(**DB_CONFIG)


def init_db():
    """Create database and table if they don't exist."""
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
        )
        cur = conn.cursor()
        cur.execute("CREATE DATABASE IF NOT EXISTS rag_db")
        conn.database = "rag_db"
        cur.execute("""
            CREATE TABLE IF NOT EXISTS datasets (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                filename    VARCHAR(255) NOT NULL,
                filepath    VARCHAR(500) NOT NULL,
                filetype    VARCHAR(50),
                uploaded_at TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
                chunk_count INT          DEFAULT 0,
                status      VARCHAR(50)  DEFAULT 'active'
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Database initialized.")
    except Exception as e:
        print(f"❌ DB init error: {e}")


def insert_dataset(filename, filepath, filetype, chunk_count):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO datasets (filename, filepath, filetype, chunk_count) VALUES (%s,%s,%s,%s)",
            (filename, filepath, filetype, chunk_count),
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ insert_dataset error: {e}")


def get_all_datasets():
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM datasets WHERE status='active' ORDER BY uploaded_at DESC")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        print(f"❌ get_all_datasets error: {e}")
        return []


def delete_dataset(dataset_id):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE datasets SET status='deleted' WHERE id=%s", (dataset_id,))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ delete_dataset error: {e}")