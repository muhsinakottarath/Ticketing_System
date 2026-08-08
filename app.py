import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, jsonify, request, render_template
from datetime import datetime

app = Flask(__name__)

# Database connection
def get_db_connection():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")
    conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
    return conn

# Initialize database tables
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Read and execute schema
    with open('schema.sql', 'r') as f:
        cur.execute(f.read())
    
    # Check if tables are empty, if so, seed data
    cur.execute("SELECT COUNT(*) as count FROM tickets")
    if cur.fetchone()['count'] == 0:
        with open('seed_data.sql', 'r') as f:
            cur.execute(f.read())
    
    conn.commit()
    cur.close()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/tickets', methods=['GET'])
def get_tickets():
    """Get all tickets with optional filtering"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get query parameters
    status = request.args.get('status', 'all')
    priority = request.args.get('priority', 'all')
    sort_order = request.args.get('sort', 'newest')
    
    # Build query
    query = "SELECT * FROM tickets WHERE 1=1"
    params = []
    
    if status != 'all':
        query += " AND status = %s"
        params.append(status)
    
    if priority != 'all':
        query += " AND priority = %s"
        params.append(priority)
    
    # Sort order
    if sort_order == 'newest':
        query += " ORDER BY created_at DESC"
    else:
        query += " ORDER BY created_at ASC"
    
    cur.execute(query, params)
    tickets = cur.fetchall()
    
    # Convert datetime to ISO format
    for ticket in tickets:
        ticket['created_at'] = ticket['created_at'].isoformat()
    
    cur.close()
    conn.close()
    
    return jsonify(tickets)

@app.route('/api/tickets', methods=['POST'])
def create_ticket():
    """Create a new ticket"""
    data = request.get_json()
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        """INSERT INTO tickets (title, status, priority, category, created_by, created_at)
           VALUES (%s, %s, %s, %s, %s, %s)
           RETURNING ticket_id, title, status, priority, category, created_by, created_at""",
        (data['title'], 'open', data.get('priority', 'medium'), 
         data.get('category'), data['created_by'], datetime.now())
    )
    
    new_ticket = cur.fetchone()
    new_ticket['created_at'] = new_ticket['created_at'].isoformat()
    
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify(new_ticket), 201

@app.route('/api/tickets/<int:ticket_id>', methods=['GET'])
def get_ticket_detail(ticket_id):
    """Get ticket details with messages"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get ticket
    cur.execute("SELECT * FROM tickets WHERE ticket_id = %s", (ticket_id,))
    ticket = cur.fetchone()
    
    if not ticket:
        cur.close()
        conn.close()
        return jsonify({'error': 'Ticket not found'}), 404
    
    ticket['created_at'] = ticket['created_at'].isoformat()
    
    # Get messages
    cur.execute(
        """SELECT * FROM ticket_messages 
           WHERE ticket_id = %s 
           ORDER BY created_at ASC""",
        (ticket_id,)
    )
    messages = cur.fetchall()
    
    for message in messages:
        message['created_at'] = message['created_at'].isoformat()
    
    ticket['messages'] = messages
    
    cur.close()
    conn.close()
    
    return jsonify(ticket)

@app.route('/api/tickets/<int:ticket_id>/messages', methods=['POST'])
def add_message(ticket_id):
    """Add a message to a ticket"""
    data = request.get_json()
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        """INSERT INTO ticket_messages (ticket_id, description, author, created_at)
           VALUES (%s, %s, %s, %s)
           RETURNING message_id, ticket_id, description, author, created_at""",
        (ticket_id, data['description'], data['author'], datetime.now())
    )
    
    new_message = cur.fetchone()
    new_message['created_at'] = new_message['created_at'].isoformat()
    
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify(new_message), 201

@app.route('/api/tickets/<int:ticket_id>/status', methods=['PATCH'])
def update_ticket_status(ticket_id):
    """Update ticket status"""
    data = request.get_json()
    new_status = data.get('status')
    
    if new_status not in ['open', 'in_progress', 'resolved']:
        return jsonify({'error': 'Invalid status'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        """UPDATE tickets SET status = %s 
           WHERE ticket_id = %s 
           RETURNING ticket_id, title, status, priority, category, created_by, created_at""",
        (new_status, ticket_id)
    )
    
    updated_ticket = cur.fetchone()
    
    if not updated_ticket:
        cur.close()
        conn.close()
        return jsonify({'error': 'Ticket not found'}), 404
    
    updated_ticket['created_at'] = updated_ticket['created_at'].isoformat()
    
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify(updated_ticket)

if __name__ == '__main__':
    # Initialize database on startup
    try:
        init_db()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")
    
    # Run the app
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)