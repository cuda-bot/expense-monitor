
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id_, username, password):
        self.id = id_
        self.username = username
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    if user:
        return User(user[0], user[1], user[2])
    return None

def init_db():
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT,
                    amount REAL,
                    date TEXT,
                    user_id INTEGER)""")
    conn.commit()
    conn.close()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        conn = sqlite3.connect('expenses.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
        except sqlite3.IntegrityError:
            flash('Username already exists')
            return redirect('/register')
        conn.close()
        flash('Registered successfully. Please log in.')
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('expenses.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()
        if user and check_password_hash(user[2], password):
            login_user(User(user[0], user[1], user[2]))
            return redirect('/')
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

@app.route('/')
@login_required
def index():
    selected_category = request.args.get('category', 'All')
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()

    if selected_category == 'All':
        c.execute('SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC', (current_user.id,))
    else:
        c.execute('SELECT * FROM expenses WHERE user_id = ? AND category = ? ORDER BY date DESC',
                  (current_user.id, selected_category))
    data = c.fetchall()

    c.execute('SELECT DISTINCT category FROM expenses WHERE user_id = ?', (current_user.id,))
    categories = [row[0] for row in c.fetchall()]

    c.execute('SELECT SUM(amount) FROM expenses WHERE user_id = ?', (current_user.id,))
    total_expenses = c.fetchone()[0] or 0

    c.execute("SELECT SUM(amount) FROM expenses WHERE user_id = ? AND strftime('%m', date) = strftime('%m', 'now')",
              (current_user.id,))
    month_expenses = c.fetchone()[0] or 0

    c.execute('SELECT category, SUM(amount) FROM expenses WHERE user_id = ? GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1',
              (current_user.id,))
    top_category = c.fetchone()
    top_category_name = top_category[0] if top_category else 'N/A'

    c.execute('SELECT category, SUM(amount) FROM expenses WHERE user_id = ? GROUP BY category', (current_user.id,))
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


from flask import Response
from flask_login import current_user

@app.route('/export/csv')
@login_required
def export_csv():
    import csv
    from io import StringIO
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute("SELECT category, amount, date FROM expenses WHERE user_id = ?", (current_user.id,))
    rows = c.fetchall()
    conn.close()

    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Category', 'Amount', 'Date'])
    cw.writerows(rows)

    output = si.getvalue()
    return Response(
        output,
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment;filename=expenses.csv"}
    )

@app.route('/export/pdf')
@login_required
def export_pdf():
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from io import BytesIO

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.drawString(100, 750, f"Expenses for {current_user.username}")

    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute("SELECT category, amount, date FROM expenses WHERE user_id = ?", (current_user.id,))
    rows = c.fetchall()
    conn.close()

    y = 720
    for row in rows:
        pdf.drawString(100, y, f"{row[0]} - ₹{row[1]} on {row[2]}")
        y -= 20

    pdf.save()
    buffer.seek(0)

    return Response(
        buffer,
        mimetype='application/pdf',
        headers={"Content-Disposition": "attachment;filename=expenses.pdf"}
    )
