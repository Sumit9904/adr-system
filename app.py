from flask import Flask, render_template, request, redirect, session, flash
import psycopg2
from functools import wraps
import os

app = Flask(__name__)

# Secret key
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "dev_fallback_key")

# PostgreSQL connection (Render)
DATABASE_URL = os.environ.get("DATABASE_URL")

# ---------- DATABASE CONNECTION ----------
def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn


# ---------- ADMIN ACCESS CONTROL ----------
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'admin':
            return "Access Denied"
        return f(*args, **kwargs)
    return decorated_function


# ---------- LOGIN ----------
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, username, password, role FROM users WHERE username=%s",
            (username,)
        )

        user = cursor.fetchone()

        conn.close()

        if user and user[2] == password:
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['role'] = user[3]

            flash("Login Successful", "success")

            return redirect('/')

        else:
            flash("Invalid Credentials", "danger")

    return render_template("login.html")


# ---------- LOGOUT ----------
@app.route('/logout')
def logout():

    session.clear()

    return redirect('/login')


# ---------- HOME ----------
@app.route('/')
def home():

    if 'user_id' not in session:
        return redirect('/login')

    search_query = request.args.get('search')

    conn = get_db_connection()
    cursor = conn.cursor()

    if search_query:
        cursor.execute("""
            SELECT * FROM adr
            WHERE name ILIKE %s
            OR drug ILIKE %s
            OR severity ILIKE %s
        """, (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"))

    else:
        cursor.execute("SELECT * FROM adr ORDER BY id DESC")

    data = cursor.fetchall()

    conn.close()

    return render_template("index.html", adr_list=data)


# ---------- ADD ADR ----------
@app.route('/add', methods=['POST'])
def add():

    if 'user_id' not in session:
        return redirect('/login')

    name = request.form['name']
    age = request.form['age']
    drug = request.form['drug']
    reaction = request.form['reaction']
    severity = request.form['severity']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO adr (name, age, drug, reaction, severity)
        VALUES (%s,%s,%s,%s,%s)
    """, (name, age, drug, reaction, severity))

    conn.commit()
    conn.close()

    flash("ADR Report Added", "success")

    return redirect('/')


# ---------- DELETE ADR ----------
@app.route('/delete/<int:id>')
def delete(id):

    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM adr WHERE id=%s", (id,))

    conn.commit()
    conn.close()

    flash("Record Deleted", "warning")

    return redirect('/')


# ---------- ADMIN DASHBOARD ----------
@app.route('/admin')
@admin_required
def admin_panel():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM adr")
    total_reports = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "admin.html",
        users=total_users,
        reports=total_reports
    )


# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True, port=5001)