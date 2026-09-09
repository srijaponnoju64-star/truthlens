import sqlite3
import os

DB_PATH = os.path.join(os.getcwd(), "detections.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS detections (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            module      TEXT,
            input_text  TEXT,
            image_path  TEXT,
            audio_path  TEXT,
            verdict     TEXT,
            confidence  TEXT,
            source      TEXT,
            spread_by   TEXT,
            explanation TEXT,
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def save_detection(module, input_text, image_path, audio_path,
                   verdict, confidence, source, spread_by, explanation):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO detections
            (module, input_text, image_path, audio_path,
             verdict, confidence, source, spread_by, explanation)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (module, input_text, image_path, audio_path,
          verdict, confidence, source, spread_by, explanation))
    conn.commit()
    conn.close()


def get_all_detections():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM detections ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows
