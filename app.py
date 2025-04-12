
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
    selected_category = request.args.get('category', 'All')

    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()

    if selected_category == 'All':
        c.execute('SELECT * FROM expenses ORDER BY date DESC')
        data = c.fetchall()
    else:
        c.execute('SELECT * FROM expenses WHERE category = ? ORDER BY date DESC', (selected_category,))
        data = c.fetchall()

    c.execute('SELECT DISTINCT category FROM expenses')
    categories = [row[0] for row in c.fetchall()]

    c.execute('SELECT SUM(amount) FROM expenses')
    total_expenses = c.fetchone()[0] or 0

    c.execute("SELECT SUM(amount) FROM expenses WHERE strftime('%m', date) = strftime('%m', 'now')")
    month_expenses = c.fetchone()[0] or 0

    c.execute('SELECT category, SUM(amount) as total FROM expenses GROUP BY category ORDER BY total DESC LIMIT 1')
    top_category = c.fetchone()
    top_category_name = top_category[0] if top_category else 'N/A'

    c.execute('SELECT category, SUM(amount) FROM expenses GROUP BY category')
    chart_data = c.fetchall()
    categories_for_chart = [row[0] for row in chart_data]
    amounts_for_chart = [row[1] for row in chart_data]

    conn.close()

    return render_template(
        'index.html',
        expenses=data,
        categories=categories,
        selected_category=selected_category,
        total_expenses=total_expenses,
        month_expenses=month_expenses,
        top_category=top_category_name,
        chart_labels=categories_for_chart,
        chart_values=amounts_for_chart
    )

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
