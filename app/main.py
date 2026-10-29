import os

import psycopg
from flask import Flask, jsonify, request
from psycopg.rows import dict_row

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL", "")


def get_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured")

    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


@app.get("/health")
def health():
    return jsonify({"status": "alive"}), 200


@app.get("/ready")
def ready():
    try:
        with get_connection() as conn:
            conn.execute("SELECT 1")

        return jsonify({"status": "ready"}), 200

    except Exception:
        app.logger.exception("Readiness check failed")
        return jsonify({"status": "not_ready"}), 503


@app.get("/operations")
def list_operations():
    try:
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, title, status, created_at
                FROM operations
                ORDER BY id DESC
                """
            ).fetchall()

        return jsonify({"operations": rows}), 200

    except Exception:
        app.logger.exception("Failed to list operations")
        return jsonify({"error": "Unable to retrieve operations"}), 503


@app.post("/operations")
def create_operation():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "A JSON object is required"}), 400

    title = data.get("title")

    if not isinstance(title, str) or not title.strip():
        return jsonify({"error": "title must be a non-empty string"}), 400

    if len(title.strip()) > 200:
        return jsonify({"error": "title must not exceed 200 characters"}), 400

    try:
        with get_connection() as conn:
            operation = conn.execute(
                """
                INSERT INTO operations (title, status)
                VALUES (%s, %s)
                RETURNING id, title, status, created_at
                """,
                (title.strip(), "pending"),
            ).fetchone()

        return jsonify(operation), 201

    except Exception:
        app.logger.exception("Failed to create operation")
        return jsonify({"error": "Unable to create operation"}), 503
