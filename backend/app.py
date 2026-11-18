import os
import time

import psycopg2
from flask import Flask, jsonify, request

app = Flask(__name__)


def query(sql, params=(), fetch=False):
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),
        dbname=os.getenv("DB_NAME", "app"),
        user=os.getenv("DB_USER", "app"),
        password=os.getenv("DB_PASSWORD", "app"),
    )
    try:
        with conn, conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall() if fetch else None
    finally:
        conn.close()


def init_db():
    for _ in range(30):
        try:
            query("CREATE TABLE IF NOT EXISTS messages (id SERIAL PRIMARY KEY, text TEXT NOT NULL)")
            return
        except psycopg2.OperationalError:
            print("DB pas encore prête, nouvelle tentative...")
            time.sleep(2)
    raise RuntimeError("Impossible de joindre la base de données")


@app.get("/api/messages")
def list_messages():
    rows = query("SELECT id, text FROM messages ORDER BY id", fetch=True)
    return jsonify([{"id": r[0], "text": r[1]} for r in rows])


@app.post("/api/messages")
def add_message():
    text = str((request.get_json(silent=True) or {}).get("text", "")).strip()
    if not text:
        return jsonify({"error": "Le message ne peut pas être vide"}), 400
    query("INSERT INTO messages (text) VALUES (%s)", (text,))
    return jsonify({"ok": True}), 201


@app.get("/api/health")
def health():
    query("SELECT 1")
    return jsonify({"status": "ok"})

@app.delete("/api/messages/<int:message_id>")
def delete_message(message_id):
    query("DELETE FROM messages WHERE id = %s", (message_id,))
    return jsonify({"ok": True})

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
