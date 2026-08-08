INSERT INTO tickets (title, status, created_by)
VALUES ('Printer not working', 'open', 'alice');

INSERT INTO ticket_messages (ticket_id, description, author)
VALUES (1, 'Tried restarting it, still no luck', 'alice');