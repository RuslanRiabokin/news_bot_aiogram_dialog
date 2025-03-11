import os
import pyodbc
from flask import Flask, render_template

app = Flask(__name__)

# Підключення до Azure SQL через змінні оточення
AZURE_SQL_CONNECTION_STRING = os.getenv("AZURE_SQL_CONNECTION_STRING")

def get_db_connection():
    conn = pyodbc.connect(AZURE_SQL_CONNECTION_STRING)
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT user_id FROM News')
    users = cursor.fetchall()
    conn.close()
    return render_template('index.html', users=users)

@app.route('/user/<int:user_id>')
def user_detail(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, topic_name, channel_name, last_pub_time FROM News WHERE user_id = ?', user_id)
    news = cursor.fetchall()
    conn.close()
    return render_template('user_detail.html', news=news, user_id=user_id)

if __name__ == '__main__':
    app.run(debug=True)
