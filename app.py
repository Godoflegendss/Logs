from flask import Flask, render_template, request
import pyodbc

app = Flask(__name__)

# Database connection details
server = 'tcp:sqlsrv-eastus2-dev-001.database.windows.net,1433'
database = 'CustomMetadata'
username = 'Login'
password = 'Thechanger@123'
connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

def get_event_logs():
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        query = "SELECT RecordID, EventID, LogName, Source, Message, TimeCreatedUTC, Level FROM WindowsEventLogs ORDER BY TimeCreatedUTC DESC"
        cursor.execute(query)
        logs = cursor.fetchall()
        conn.close()
        return logs
    except Exception as e:
        print(f"Error fetching logs: {e}")
        return []

@app.route('/')
def index():
    logs = get_event_logs()
    return render_template('index.html', logs=logs)

@app.route('/event/<int:record_id>')
def event_details(record_id):
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        query = f"SELECT * FROM WindowsEventLogs WHERE RecordID = {record_id}"
        cursor.execute(query)
        event = cursor.fetchone()
        conn.close()
        return render_template('event_details.html', event=event)
    except Exception as e:
        print(f"Error fetching event details: {e}")
        return render_template('event_details.html', event=None)

if __name__ == '__main__':
    app.run(debug=True)