from flask import Flask, render_template, request
import pyodbc

app = Flask(__name__)

# Database connection details
server = 'tcp:sqlsrv-eastus2-dev-001.database.windows.net,1433'
database = 'CustomMetadata'
username = 'Login'
password = 'Thechanger@123'
connection_string = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'
def get_event_logs(search_query=None, level_filter=None, limit=20, offset=0):
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()

        # Base query
        query = """
            SELECT RecordID, EventID, LogName, Source, Message, TimeCreatedUTC, Level 
            FROM WindowsEventlogs 
            WHERE 1=1
        """

        # Add filters based on user input
        if search_query:
            query += " AND (Message LIKE ? OR Source LIKE ?)"
        if level_filter:
            query += " AND Level = ?"

        query += " ORDER BY TimeCreatedUTC DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"

        # Execute query with parameters
        params = []
        if search_query:
            params.extend([f"%{search_query}%", f"%{search_query}%"])
        if level_filter:
            params.append(level_filter)
        params.extend([offset, limit])

        cursor.execute(query, params)
        logs = cursor.fetchall()
        conn.close()
        return logs
    except Exception as e:
        print(f"Error fetching logs: {e}")
        return []

@app.route('/')
def index():
    # Get search, filter, and pagination parameters from the request
    search_query = request.args.get('search', default=None)
    level_filter = request.args.get('level', default=None)
    limit = int(request.args.get('limit', default=20))
    page = int(request.args.get('page', default=1))

    # Calculate offset for pagination
    offset = (page - 1) * limit

    # Fetch logs with filters and pagination applied
    logs = get_event_logs(search_query, level_filter, limit, offset)
    return render_template(
        'index.html', 
        logs=logs, 
        search_query=search_query, 
        level_filter=level_filter,
        limit=limit,
        page=page
    )

@app.route('/event/<int:record_id>')
def event_details(record_id):
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()

        # Fetch the clicked event
        cursor.execute("SELECT * FROM WindowsEventlogs WHERE RecordID = ?", (record_id,))
        event = cursor.fetchone()

        if event:
            # Fetch all occurrences of similar events (same EventID and Source)
            cursor.execute("""
                SELECT * 
                FROM WindowsEventlogs 
                WHERE EventID = ? AND Source = ? 
                ORDER BY TimeCreatedUTC DESC
            """, (event.EventID, event.Source))
            timeline_events = cursor.fetchall()

            # Calculate total occurrences and time range
            total_occurrences = len(timeline_events)
            first_occurrence = min(e.TimeCreatedUTC for e in timeline_events) if timeline_events else None
            last_occurrence = max(e.TimeCreatedUTC for e in timeline_events) if timeline_events else None

        conn.close()
        return render_template(
            'event_details.html', 
            event=event,
            timeline_events=timeline_events,
            total_occurrences=total_occurrences,
            first_occurrence=first_occurrence,
            last_occurrence=last_occurrence
        )
    except Exception as e:
        print(f"Error: {e}")
        return render_template('event_details.html', event=None)

if __name__ == '__main__':
    app.run(debug=True)