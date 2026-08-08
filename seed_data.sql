-- Sample ticket data
INSERT INTO tickets (title, status, priority, category, created_by, created_at)
VALUES 
    ('Printer not working', 'open', 'high', 'Technical', 'alice', CURRENT_TIMESTAMP),
    ('Login issues with portal', 'in_progress', 'medium', 'Technical', 'bob', CURRENT_TIMESTAMP),
    ('Invoice discrepancy', 'resolved', 'low', 'Billing', 'charlie', CURRENT_TIMESTAMP);

-- Sample messages for tickets
INSERT INTO ticket_messages (ticket_id, message_text, author, created_at)
VALUES 
    (1, 'Tried restarting it, still no luck', 'alice', CURRENT_TIMESTAMP),
    (1, 'Have you checked the paper tray and ink levels?', 'support_team', CURRENT_TIMESTAMP),
    (2, 'Getting error "Invalid credentials" when trying to log in', 'bob', CURRENT_TIMESTAMP),
    (3, 'Invoice #12345 shows incorrect amount', 'charlie', CURRENT_TIMESTAMP),
    (3, 'Investigated and corrected. Refund processed.', 'billing_team', CURRENT_TIMESTAMP);