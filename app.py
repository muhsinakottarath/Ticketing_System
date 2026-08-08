from flask import Flask, render_template, request, jsonify
from databricks import sql
import os
from datetime import datetime

app = Flask(__name__)

# Databricks SQL connection configuration
def get_db_connection():
    """Create a connection to Databricks SQL warehouse"""
    return sql.connect(
        server_hostname=os.getenv('DATABRICKS_SERVER_HOSTNAME'),
        http_path=os.getenv('DATABRICKS_HTTP_PATH'),
        access_token=os.getenv('DATABRICKS_TOKEN')
    )

def execute_query(query, params=None, fetch=True):
    """Execute a SQL query and return results"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params or [])
        if fetch:
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return results
        conn.commit()
        return None
    finally:
        cursor.close()
        conn.close()

# Routes
@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/tickets', methods=['GET'])
def get_tickets():
    """Get all tickets with optional status filter"""
    try:
        status_filter = request.args.get('status')
        
        if status_filter and status_filter != 'all':
            query = """
                SELECT 
                    t.ticket_id as id,
                    t.title,
                    t.status,
                    t.priority,
                    t.category,
                    t.created_by,
                    t.created_at,
                    COUNT(m.message_id) as message_count
                FROM tickets t
                LEFT JOIN messages m ON t.ticket_id = m.ticket_id
                WHERE t.status = ?
                GROUP BY t.ticket_id, t.title, t.status, t.priority, t.category, t.created_by, t.created_at
                ORDER BY t.created_at DESC
            """
            tickets = execute_query(query, [status_filter])
        else:
            query = """
                SELECT 
                    t.ticket_id as id,
                    t.title,
                    t.status,
                    t.priority,
                    t.category,
                    t.created_by,
                    t.created_at,
                    COUNT(m.message_id) as message_count
                FROM tickets t
                LEFT JOIN messages m ON t.ticket_id = m.ticket_id
                GROUP BY t.ticket_id, t.title, t.status, t.priority, t.category, t.created_by, t.created_at
                ORDER BY t.created_at DESC
            """
            tickets = execute_query(query)
        
        return jsonify(tickets)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tickets', methods=['POST'])
def create_ticket():
    """Create a new ticket"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('title') or not data.get('created_by') or not data.get('priority'):
            return jsonify({'error': 'Missing required fields'}), 400
        
        query = """
            INSERT INTO tickets (title, status, priority, category, created_by, created_at)
            VALUES (?, 'open', ?, ?, ?, CURRENT_TIMESTAMP())
        """
        
        execute_query(
            query,
            [
                data['title'],
                data['priority'],
                data.get('category'),
                data['created_by']
            ],
            fetch=False
        )
        
        return jsonify({'message': 'Ticket created successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tickets/<int:ticket_id>/status', methods=['PATCH'])
def update_ticket_status(ticket_id):
    """Update ticket status"""
    try:
        data = request.get_json()
        status = data.get('status')
        
        if not status or status not in ['open', 'in_progress', 'resolved']:
            return jsonify({'error': 'Invalid status'}), 400
        
        query = "UPDATE tickets SET status = ? WHERE ticket_id = ?"
        execute_query(query, [status, ticket_id], fetch=False)
        
        return jsonify({'message': 'Status updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tickets/<int:ticket_id>/messages', methods=['GET'])
def get_ticket_messages(ticket_id):
    """Get all messages for a ticket"""
    try:
        query = """
            SELECT 
                message_id as id,
                message_text,
                author,
                created_at
            FROM messages
            WHERE ticket_id = ?
            ORDER BY created_at ASC
        """
        
        messages = execute_query(query, [ticket_id])
        return jsonify(messages)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tickets/<int:ticket_id>/messages', methods=['POST'])
def add_ticket_message(ticket_id):
    """Add a message to a ticket"""
    try:
        data = request.get_json()
        
        if not data.get('message_text') or not data.get('author'):
            return jsonify({'error': 'Missing required fields'}), 400
        
        query = """
            INSERT INTO messages (ticket_id, message_text, author, created_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP())
        """
        
        execute_query(
            query,
            [ticket_id, data['message_text'], data['author']],
            fetch=False
        )
        
        return jsonify({'message': 'Message added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tickets/<int:ticket_id>', methods=['DELETE'])
def delete_ticket(ticket_id):
    """Delete a ticket and its messages"""
    try:
        # Delete messages first (foreign key constraint)
        execute_query("DELETE FROM messages WHERE ticket_id = ?", [ticket_id], fetch=False)
        
        # Delete ticket
        execute_query("DELETE FROM tickets WHERE ticket_id = ?", [ticket_id], fetch=False)
        
        return jsonify({'message': 'Ticket deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)