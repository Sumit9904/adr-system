from flask import Flask, render_template, request, redirect, session, url_for
import os
import psycopg2
from urllib.parse import urlparse
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise Exception("DATABASE_URL is not set in environment variables!")

def get_connection():
    return psycopg2.connect(DATABASE_URL)

# ------------------ INIT DATABASE ------------------ #
def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # ADR table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS adr (
            id SERIAL PRIMARY KEY,
            name TEXT,
            age INTEGER,
            drug TEXT,
            reaction TEXT,
            severity TEXT
        )
    """)

    # Users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    # Create default admin if not exists
    cur.execute("SELECT * FROM users WHERE username = %s", ("admin",))
    if not cur.fetchone():
        hashed = generate_password_hash("1234")
        cur.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            ("admin", hashed)
        )

    conn.commit()
    cur.close()
    conn.close()

init_db()

# ------------------ LOGIN ------------------ #
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT password FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and check_password_hash(user[0], password):
            session["user"] = username
            return redirect(url_for("home"))
        else:
            return "Invalid credentials"

    return render_template("login.html")

# ------------------ LOGOUT ------------------ #
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ------------------ HOME ------------------ #
@app.route("/")
def home():
    if "user" not in session:
        return redirect(url_for("login"))

    search = request.args.get("search")

    conn = get_connection()
    cur = conn.cursor()

    if search:
        cur.execute("""
            SELECT * FROM adr
            WHERE name ILIKE %s
               OR drug ILIKE %s
               OR severity ILIKE %s
        """, (f"%{search}%", f"%{search}%", f"%{search}%"))
    else:
        cur.execute("SELECT * FROM adr ORDER BY id DESC")

    data = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("index.html", adr_list=data)

# ------------------ ADD ADR ------------------ #
@app.route("/add", methods=["POST"])
def add():
    if "user" not in session:
        return redirect(url_for("login"))

    name = request.form["name"]
    age = request.form["age"]
    drug = request.form["drug"]
    reaction = request.form["reaction"]
    severity = request.form["severity"]

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO adr (name, age, drug, reaction, severity) VALUES (%s, %s, %s, %s, %s)",
        (name, age, drug, reaction, severity)
    )
    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("home"))

# ------------------ DELETE ------------------ #
@app.route("/delete/<int:id>")
def delete(id):
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM adr WHERE id = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("home"))


# ------------------ EDIT PAGE ------------------ #
@app.route("/edit/<int:id>")
def edit(id):
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM adr WHERE id = %s", (id,))
    data = cur.fetchone()
    cur.close()
    conn.close()

    return render_template("edit.html", adr=data)


# ------------------ UPDATE ------------------ #
@app.route("/update/<int:id>", methods=["POST"])
def update(id):
    if "user" not in session:
        return redirect(url_for("login"))

    name = request.form["name"]
    age = request.form["age"]
    drug = request.form["drug"]
    reaction = request.form["reaction"]
    severity = request.form["severity"]

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE adr
        SET name=%s, age=%s, drug=%s, reaction=%s, severity=%s
        WHERE id=%s
    """, (name, age, drug, reaction, severity, id))

    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("home"))

# ------------------ RUN ------------------ #
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)