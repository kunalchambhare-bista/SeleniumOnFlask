# flask_api_celery.py
from celery_task import process_pending_tasks
from flask import Flask, request, jsonify, g
import jwt
import sqlite3
from datetime import datetime

DATABASE = 'my_database.db'

app = Flask(__name__)

SECRET_KEY = 'tkunal'
app.config['SECRET_KEY'] = SECRET_KEY

AUTH_TOKEN = jwt.encode({'sub': 'user123'}, SECRET_KEY, algorithm='HS256')
print(f"Authentication Token: {AUTH_TOKEN}")

if_running = False


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = sqlite3.connect(DATABASE)
        g.sqlite_db.row_factory = sqlite3.Row
    return g.sqlite_db


def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''
                            CREATE TABLE IF NOT EXISTS packaging_order (
                                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                                order_name TEXT,
                                weight TEXT,
                                length TEXT,
                                width TEXT,
                                height TEXT,
                                status TEXT,
                                create_date TEXT,
                                picking TEXT,
                                error TEXT
                            )
                        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS status_boolean_table (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                status BOOLEAN DEFAULT 0
            )
        ''')
        db.commit()



def check_access(received_token):
    try:
        decoded_token = jwt.decode(received_token, SECRET_KEY, algorithms=['HS256'])
        if decoded_token:
            return jsonify(message='Access granted to protected resource', status=200)
    except jwt.ExpiredSignatureError:
        return jsonify(message='Token has expired', status=401), 401
    except jwt.InvalidTokenError:
        return jsonify(message='Unauthorized', status=401), 401


@app.route('/')
def home():
    return 'Welcome to the API!'


@app.route('/api/resource', methods=['GET'])
def protected_resource():
    received_token = request.headers.get('Authorization').split(' ')[1]
    status = check_access(received_token)
    if status.status == '200 OK':
        print("OK")


@app.route('/api/post/data', methods=['POST'])
def post_resource():
    init_db()
    global if_running
    received_token = request.headers.get('Authorization').split(' ')[1]
    status = check_access(received_token)
    if status.status == '200 OK':
        data = request.json
        print(data)
        order_name = data.get('order_name')
        weight = data.get('weight')
        length = data.get('length')
        width = data.get('width')
        height = data.get('height')
        picking = data.get('picking')

        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            'INSERT INTO packaging_order (order_name, weight, length, width, height, status, create_date, picking) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (order_name, weight, length, width, height, 'pending', datetime.now(), picking))
        new_row_id = cursor.lastrowid
        db.commit()

        cursor.execute('SELECT * FROM status_boolean_table WHERE ID = ?', (1,))
        existing_row = cursor.fetchone()

        if not existing_row:
            # If there is no row with ID 1, add a new row with status False
            cursor.execute('INSERT INTO status_boolean_table (ID, status) VALUES (?, ?)', (1, False))
            db.commit()

        cursor.execute('SELECT * FROM status_boolean_table WHERE ID = ?', (1,))
        existing_row = cursor.fetchone()

        if not existing_row[1]:
            cursor.execute('UPDATE status_boolean_table SET status = ? WHERE ID = ?', (True, 1))
            db.commit()
            process_pending_tasks.delay()
        result = {'message': f'Order: {order_name} Added to Queue',
                  "Ref": f'{new_row_id}'}

        return jsonify(result), 200


if __name__ == '__main__':
    app.run(debug=True)

