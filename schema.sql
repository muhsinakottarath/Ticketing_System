CREATE TABLE IF NOT EXISTS tickets(
    ticket_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title STRING NOT NULL,
    status STRING NOT NULL,
    priority STRING NOT NULL DEFAULT 'medium',
    category STRING,
    created_by STRING NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS messages(
    message_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ticket_id BIGINT NOT NULL,
    message_text STRING NOT NULL,
    author STRING NOT NULL,
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id)
);



