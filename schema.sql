-- Lakebase (Postgres) schema for the Day 1 Support Ticket App

CREATE TABLE IF NOT EXISTS tickets (
    ticket_id   SERIAL PRIMARY KEY,
    title       TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'open',       -- open | in_progress | resolved
    priority    TEXT NOT NULL DEFAULT 'medium',      -- low | medium | high  (bonus: priority)
    category    TEXT,                                -- e.g. billing, bug, question (bonus: category)
    created_by  TEXT NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ticket_messages (
    message_id   SERIAL PRIMARY KEY,
    ticket_id    INTEGER NOT NULL REFERENCES tickets(ticket_id) ON DELETE CASCADE,
    message_text TEXT NOT NULL,
    author       TEXT NOT NULL,
    created_at   TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ticket_messages_ticket_id ON ticket_messages(ticket_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
