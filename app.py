"""
Lakebase-Powered AI Support App
--------------------------------
Flask app backed by a Lakebase (Databricks-managed Postgres) instance.

Environment variables expected (wired up as Databricks App secrets/resources,
exactly like DATABASE_URL was wired for the watchlist app in the workshop):

    DATABASE_URL   -- full Postgres connection string for your Lakebase instance

Never hard-code credentials here. In Databricks Apps, add DATABASE_URL as a
secret resource on the app (Edit -> Add resource -> Secret), matching the name
used below.
"""

import os
import psycopg2
import psycopg2.extras
from flask import Flask, request, jsonify, render_template
from datetime import datetime

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")
MASSIVE_API_KEY = os.environ.get("MASSIVE_API_KEY")

VALID_STATUSES = {"open", "in_progress", "resolved"}
VALID_PRIORITIES = {"low", "medium", "high"}


def get_conn():
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not set. Add it as a secret resource on the Databricks App."
        )
    return psycopg2.connect(DATABASE_URL)


def ensure_schema():
    """Create tables if they don't exist yet, and seed sample data once."""
    base_dir = os.getcwd()
    schema_path = os.path.join(base_dir, "schema.sql")
    seed_path = os.path.join(base_dir, "seed_data.sql")

    with get_conn() as conn:
        with conn.cursor() as cur:
            with open(schema_path) as f:
                cur.execute(f.read())
            with open(seed_path) as f:
                cur.execute(f.read())
        conn.commit()


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


# ---------------------------------------------------------------------------
# Tickets API
# ---------------------------------------------------------------------------

@app.route("/api/tickets", methods=["GET"])
def list_tickets():
    """List tickets, optionally filtered by status (bonus: filtering)."""
    status_filter = request.args.get("status")

    query = """
        SELECT t.ticket_id, t.title, t.status, t.priority, t.category,
               t.created_by, t.created_at,
               COUNT(m.message_id) AS message_count
        FROM tickets t
        LEFT JOIN ticket_messages m ON m.ticket_id = t.ticket_id
    """
    params = []
    if status_filter:
        if status_filter not in VALID_STATUSES:
            return jsonify({"error": f"Invalid status filter '{status_filter}'"}), 400
        query += " WHERE t.status = %s"
        params.append(status_filter)

    query += " GROUP BY t.ticket_id ORDER BY t.created_at DESC"

    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

    return jsonify([dict(r) for r in rows])


@app.route("/api/tickets", methods=["POST"])
def create_ticket():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    created_by = (data.get("created_by") or "").strip()
    priority = data.get("priority", "medium")
    category = data.get("category") or None

    # Input validation (bonus: validation + helpful error messages)
    errors = []
    if not title:
        errors.append("title is required")
    if not created_by:
        errors.append("created_by is required")
    if priority not in VALID_PRIORITIES:
        errors.append(f"priority must be one of {sorted(VALID_PRIORITIES)}")
    if errors:
        return jsonify({"error": "; ".join(errors)}), 400

    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO tickets (title, status, priority, category, created_by)
                VALUES (%s, 'open', %s, %s, %s)
                RETURNING ticket_id, title, status, priority, category, created_by, created_at
                """,
                (title, priority, category, created_by),
            )
            new_ticket = cur.fetchone()
        conn.commit()

    return jsonify(dict(new_ticket)), 201


@app.route("/api/tickets/<int:ticket_id>/status", methods=["PATCH"])
def update_status(ticket_id):
    data = request.get_json(silent=True) or {}
    new_status = data.get("status")

    if new_status not in VALID_STATUSES:
        return jsonify({"error": f"status must be one of {sorted(VALID_STATUSES)}"}), 400

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE tickets SET status = %s WHERE ticket_id = %s",
                (new_status, ticket_id),
            )
            if cur.rowcount == 0:
                return jsonify({"error": "ticket not found"}), 404
        conn.commit()

    return jsonify({"ticket_id": ticket_id, "status": new_status})


@app.route("/api/tickets/<int:ticket_id>", methods=["DELETE"])
def delete_ticket(ticket_id):
    """Bonus: delete functionality (confirmation is handled client-side)."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM tickets WHERE ticket_id = %s", (ticket_id,))
            if cur.rowcount == 0:
                return jsonify({"error": "ticket not found"}), 404
        conn.commit()

    return jsonify({"deleted": ticket_id})


# ---------------------------------------------------------------------------
# Messages API
# ---------------------------------------------------------------------------

@app.route("/api/tickets/<int:ticket_id>/messages", methods=["GET"])
def list_messages(ticket_id):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT message_id, ticket_id, message_text, author, created_at
                FROM ticket_messages
                WHERE ticket_id = %s
                ORDER BY created_at ASC
                """,
                (ticket_id,),
            )
            rows = cur.fetchall()

    return jsonify([dict(r) for r in rows])


@app.route("/api/tickets/<int:ticket_id>/messages", methods=["POST"])
def add_message(ticket_id):
    data = request.get_json(silent=True) or {}
    message_text = (data.get("message_text") or "").strip()
    author = (data.get("author") or "").strip()

    errors = []
    if not message_text:
        errors.append("message_text is required")
    if not author:
        errors.append("author is required")
    if errors:
        return jsonify({"error": "; ".join(errors)}), 400

    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT 1 FROM tickets WHERE ticket_id = %s", (ticket_id,))
            if cur.fetchone() is None:
                return jsonify({"error": "ticket not found"}), 404

            cur.execute(
                """
                INSERT INTO ticket_messages (ticket_id, message_text, author)
                VALUES (%s, %s, %s)
                RETURNING message_id, ticket_id, message_text, author, created_at
                """,
                (ticket_id, message_text, author),
            )
            new_message = cur.fetchone()
        conn.commit()

    return jsonify(dict(new_message)), 201


# ---------------------------------------------------------------------------
# Stats (bonus: display ticket statistics)
# ---------------------------------------------------------------------------

@app.route("/api/stats", methods=["GET"])
def stats():
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT status, COUNT(*) AS count
                FROM tickets
                GROUP BY status
                """
            )
            by_status = {r["status"]: r["count"] for r in cur.fetchall()}

            cur.execute("SELECT COUNT(*) AS total FROM tickets")
            total = cur.fetchone()["total"]

    return jsonify({"total": total, "by_status": by_status})


if __name__ == "__main__":
    if DATABASE_URL:
        ensure_schema()
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
else:
    # Databricks Apps typically imports the module rather than running __main__,
    # so make sure the schema/seed step still runs on startup.
    if DATABASE_URL:
        ensure_schema()
