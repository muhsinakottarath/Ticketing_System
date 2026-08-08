-- Sample tickets
INSERT INTO tickets (title, status, created_by, created_at)
VALUES 
    ('Printer not working', 'open', 'alice', CURRENT_TIMESTAMP()),
    ('Password reset request', 'in_progress', 'bob', CURRENT_TIMESTAMP()),
    ('Software installation needed', 'resolved', 'carol', CURRENT_TIMESTAMP()),
    ('Email not syncing', 'open', 'david', CURRENT_TIMESTAMP());

-- Sample messages
INSERT INTO messages (ticket_id, message_text, author, created_at)
VALUES 
    (1, 'Tried restarting it, still no luck', 'alice', CURRENT_TIMESTAMP()),
    (1, 'Can you check if it has paper and toner?', 'support', CURRENT_TIMESTAMP()),
    (2, 'I will send you a password reset link', 'support', CURRENT_TIMESTAMP()),
    (3, 'Software installed successfully', 'support', CURRENT_TIMESTAMP()),
    (3, 'Thanks for the quick help!', 'carol', CURRENT_TIMESTAMP());