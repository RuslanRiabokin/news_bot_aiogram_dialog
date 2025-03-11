import os
from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

# Встановлюємо шлях до файлу database.db у кореневій папці проєкту
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'database.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    users = conn.execute('SELECT DISTINCT user_id FROM News').fetchall()
    conn.close()
    return render_template('index.html', users=users)

@app.route('/user/<int:user_id>')
def user_detail(user_id):
    conn = get_db_connection()
    news = conn.execute('SELECT * FROM News WHERE user_id = ?', (user_id,)).fetchall()
    conn.close()
    return render_template('user_detail.html', news=news, user_id=user_id)

if __name__ == '__main__':
    app.run(debug=True)
