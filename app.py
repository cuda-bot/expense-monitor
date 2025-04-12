
from flask import Flask, render_template, request, redirect
import sqlite3
import os

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT,
                    amount REAL,
                    date TEXT
                )""")
    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('SELECT * FROM expenses ORDER BY date DESC')
    data = c.fetchall()
    conn.close()
    return render_template('index.html', expenses=data)

@app.route('/add', methods=['GET', 'POST'])
def add_expense():
    if request.method == 'POST':
        category = request.form['category']
        amount = request.form['amount']
        date = request.form['date']

        conn = sqlite3.connect('expenses.db')
        c = conn.cursor()
        c.execute('INSERT INTO expenses (category, amount, date) VALUES (?, ?, ?)',
                  (category, amount, date))
        conn.commit()
        conn.close()
        return redirect('/')
    return render_template('add_expense.html')



if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)