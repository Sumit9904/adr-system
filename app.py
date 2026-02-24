from flask import Flask, render_template, request, redirect, session, url_for
import os
import psycopg2
from urllib.parse import urlparse
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "dev_fallback_key")

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise Exception("DATABASE_URL is not set!")

def get_connection():
    url = urlparse(DATABASE_URL)
    return psycopg2.connect(
        host=url.hostname,
        database=url.path[1:],
        user=url.username,
        password=url.password,
        port=url.port
    )

# -------- DATABASE INIT --------
def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS adr (
            id SERIAL PRIMARY KEY,
            name TEXT,
            age INTEGER,
            drug TEXT,
            reaction TEXT,
            severity TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    cursor.execute("SELECT * FROM users WHERE username = %s", ("admin",))
    if not cursor.fetchone():
        hashed_password = generate_password_hash("1234")
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            ("admin", hashed_password)
        )

    conn.commit()
    conn.close()

init_db()

# -------- LOGIN --------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[0], password):
            session['user'] = username
            return redirect(url_for('home'))
        else:
            return "Invalid Credentials"

    return render_template("login.html")

# -------- LOGOUT --------
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# -------- HOME --------
@app.route('/')
def home():
    if 'user' not in session:
        return redirect(url_for('login'))

    search_query = request.args.get('search')

    conn = get_connection()
    cursor = conn.cursor()

    if search_query:
        cursor.execute("""
            SELECT * FROM adr
            WHERE name ILIKE %s OR drug ILIKE %s OR severity ILIKE %s
        """, (
            f"%{search_query}%",
            f"%{search_query}%",
            f"%{search_query}%"
        ))
    else:
        cursor.execute("SELECT * FROM adr")

    data = cursor.fetchall()
    conn.close()

    return render_template("index.html", adr_list=data)

# -------- ADD --------
@app.route('/add', methods=['POST'])
def add():
    if 'user' not in session:
        return redirect(url_for('login'))

    name = request.form['name']
    age = request.form['age']
    drug = request.form['drug']
    reaction = request.form['reaction']
    severity = request.form['severity']

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO adr (name, age, drug, reaction, severity) VALUES (%s, %s, %s, %s, %s)",
        (name, age, drug, reaction, severity)
    )
    conn.commit()
    conn.close()

    return redirect(url_for('home'))

# -------- DELETE --------
@app.route('/delete/<int:id>')
def delete(id):
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM adr WHERE id = %s", (id,))
    conn.commit()
    conn.close()

    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run()