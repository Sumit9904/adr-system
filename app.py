from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ---------- DATABASE INIT ----------
def init_db():
    conn = sqlite3.connect("adr.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS adr (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            age INTEGER,
            drug TEXT,
            reaction TEXT,
            severity TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------- LOGIN PAGE ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Simple hardcoded login
        if username == "admin" and password == "1234":
            session['user'] = username
            return redirect('/')
        else:
            return "Invalid Credentials"

    return render_template("login.html")

# ---------- LOGOUT ----------
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')

# ---------- HOME ----------
@app.route('/')
def home():
    if 'user' not in session:
        return redirect('/login')

    search_query = request.args.get('search')

    conn = sqlite3.connect("adr.db")
    cursor = conn.cursor()

    if search_query:
        cursor.execute("""
            SELECT * FROM adr 
            WHERE name LIKE ? OR drug LIKE ? OR severity LIKE ?
        """, (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"))
    else:
        cursor.execute("SELECT * FROM adr")

    data = cursor.fetchall()
    conn.close()

    return render_template("index.html", adr_list=data)

# ---------- ADD ----------
@app.route('/add', methods=['POST'])
def add():
    if 'user' not in session:
        return redirect('/login')

    name = request.form['name']
    age = request.form['age']
    drug = request.form['drug']
    reaction = request.form['reaction']
    severity = request.form['severity']

    conn = sqlite3.connect("adr.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO adr (name, age, drug, reaction, severity) VALUES (?, ?, ?, ?, ?)",
        (name, age, drug, reaction, severity)
    )
    conn.commit()
    conn.close()

    return redirect('/')

# ---------- DELETE ----------
@app.route('/delete/<int:id>')
def delete(id):
    if 'user' not in session:
        return redirect('/login')

    conn = sqlite3.connect("adr.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM adr WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True, port=5001)