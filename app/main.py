import logging
import os

import psycopg
from flask import Flask, jsonify, request
from psycopg.rows import dict_row

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)


def get_connection():
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is not configured")

    return psycopg.connect(database_url, row_factory=dict_row)


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
        return jsonify({"status": "not ready"}), 503


@app.get("/operations")
def list_operations():
    try:
        with get_connection() as conn:
            operations = conn.execute(
                """
                SELECT id, title, status, created_at
                FROM operations
                ORDER BY id DESC
                """
            ).fetchall()

        return jsonify({"operations": operations}), 200

    except Exception:
        app.logger.exception("Failed to retrieve operations")
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


@app.get("/version")
def version():
    return jsonify({"version": "2.0.0"}), 200
