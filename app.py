from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
import psycopg2
import os
import csv
from functools import wraps

app = Flask(__name__)
app.secret_key = "supersecretkey"

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL)

# ---------------- LOGIN REQUIRED DECORATOR ---------------- #
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


# ---------------- LOGIN ---------------- #
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "1234":
            session["user"] = username
            return redirect(url_for("home"))
        else:
            flash("Invalid Credentials!", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------- HOME WITH PAGINATION + SEARCH ---------------- #
@app.route("/", methods=["GET", "POST"])
@login_required
def home():
    page = request.args.get("page", 1, type=int)
    per_page = 5
    offset = (page - 1) * per_page

    search = request.form.get("search", "")

    conn = get_connection()
    cur = conn.cursor()

    if search:
        cur.execute("""
            SELECT * FROM adr
            WHERE name ILIKE %s OR drug ILIKE %s
            ORDER BY id DESC
            LIMIT %s OFFSET %s
        """, (f"%{search}%", f"%{search}%", per_page, offset))
    else:
        cur.execute("""
            SELECT * FROM adr
            ORDER BY id DESC
            LIMIT %s OFFSET %s
        """, (per_page, offset))

    data = cur.fetchall()

    cur.execute("SELECT COUNT(*) FROM adr")
    total = cur.fetchone()[0]
    total_pages = (total // per_page) + (1 if total % per_page > 0 else 0)

    cur.close()
    conn.close()

    return render_template("index.html", adr=data, page=page, total_pages=total_pages)


# ---------------- ADD ---------------- #
@app.route("/add", methods=["POST"])
@login_required
def add():
    name = request.form["name"]
    age = request.form["age"]
    drug = request.form["drug"]
    reaction = request.form["reaction"]
    severity = request.form["severity"]

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO adr (name, age, drug, reaction, severity)
        VALUES (%s, %s, %s, %s, %s)
    """, (name, age, drug, reaction, severity))

    conn.commit()
    cur.close()
    conn.close()

    flash("ADR Added Successfully!", "success")
    return redirect(url_for("home"))


# ---------------- DELETE ---------------- #
@app.route("/delete/<int:id>")
@login_required
def delete(id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM adr WHERE id=%s", (id,))
    conn.commit()
    cur.close()
    conn.close()

    flash("Record Deleted!", "warning")
    return redirect(url_for("home"))


# ---------------- EXPORT CSV ---------------- #
@app.route("/export")
@login_required
def export():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM adr ORDER BY id DESC")
    data = cur.fetchall()
    cur.close()
    conn.close()

    def generate():
        data_stream = []
        writer = csv.writer(data_stream)
        yield "ID,Name,Age,Drug,Reaction,Severity\n"
        for row in data:
            yield f"{row[0]},{row[1]},{row[2]},{row[3]},{row[4]},{row[5]}\n"

    return Response(generate(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment;filename=adr_data.csv"})


# ---------------- DASHBOARD ---------------- #
@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM adr")
    total = cur.fetchone()[0]

    cur.execute("SELECT severity, COUNT(*) FROM adr GROUP BY severity")
    severity_data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("dashboard.html", total=total, severity=severity_data)


if __name__ == "__main__":
    app.run(debug=True)