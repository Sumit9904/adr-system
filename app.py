from flask import Flask, render_template, request, redirect, session, flash, send_file, url_for
import psycopg2
from functools import wraps
import os
from io import BytesIO
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash
from openpyxl import Workbook

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=os.environ.get('FLASK_ENV') == 'production',
)

DATABASE_URL = os.environ.get('DATABASE_URL')


def get_db_connection():
    if not DATABASE_URL:
        raise RuntimeError('DATABASE_URL is not set')
    return psycopg2.connect(DATABASE_URL)


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(80) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL DEFAULT 'viewer'
        )
        '''
    )

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS adr (
            id SERIAL PRIMARY KEY,
            name VARCHAR(120) NOT NULL,
            age INTEGER NOT NULL,
            drug VARCHAR(120) NOT NULL,
            reaction TEXT NOT NULL,
            severity VARCHAR(50) NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        '''
    )

    cursor.execute('SELECT COUNT(*) FROM users WHERE role = %s', ('admin',))
    has_admin = cursor.fetchone()[0] > 0

    if not has_admin:
        admin_user = os.environ.get('ADMIN_USERNAME', 'admin')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'admin1234')
        cursor.execute(
            'INSERT INTO users (username, password, role) VALUES (%s, %s, %s)',
            (admin_user, generate_password_hash(admin_password), 'admin'),
        )

    conn.commit()
    conn.close()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)

    return login_required(decorated_function)


def fetch_summary_metrics(cursor):
    cursor.execute('SELECT COUNT(*) FROM adr')
    total_reports = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM adr WHERE severity ILIKE 'Severe%'")
    severe_cases = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(DISTINCT drug) FROM adr')
    unique_drugs = cursor.fetchone()[0]

    return {
        'total_reports': total_reports,
        'total_users': total_users,
        'severe_cases': severe_cases,
        'unique_drugs': unique_drugs,
    }


@app.before_request
def startup():
    if not getattr(app, '_db_initialized', False):
        init_db()
        app._db_initialized = True


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, username, password, role FROM users WHERE username = %s',
            (username,),
        )
        user = cursor.fetchone()

        if user:
            stored_password = user[2]
            valid = check_password_hash(stored_password, password)

            if not valid and stored_password == password:
                valid = True
                cursor.execute(
                    'UPDATE users SET password = %s WHERE id = %s',
                    (generate_password_hash(password), user[0]),
                )
                conn.commit()

            if valid:
                session.clear()
                session['user_id'] = user[0]
                session['username'] = user[1]
                session['role'] = user[3]
                flash('Login successful.', 'success')
                conn.close()
                return redirect(url_for('home'))

        conn.close()
        flash('Invalid username or password.', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/')
@login_required
def home():
    search_query = request.args.get('search', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    if search_query:
        cursor.execute(
            '''
            SELECT id, name, age, drug, reaction, severity, created_at
            FROM adr
            WHERE name ILIKE %s OR drug ILIKE %s OR severity ILIKE %s
            ORDER BY id DESC
            ''',
            (f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'),
        )
    else:
        cursor.execute(
            'SELECT id, name, age, drug, reaction, severity, created_at FROM adr ORDER BY id DESC'
        )

    adr_list = cursor.fetchall()
    metrics = fetch_summary_metrics(cursor)

    conn.close()
    return render_template('index.html', adr_list=adr_list, metrics=metrics, search_query=search_query)


@app.route('/add', methods=['POST'])
@login_required
def add():
    name = request.form['name'].strip()
    age = request.form['age']
    drug = request.form['drug'].strip()
    reaction = request.form['reaction'].strip()
    severity = request.form['severity'].strip()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        '''
        INSERT INTO adr (name, age, drug, reaction, severity)
        VALUES (%s, %s, %s, %s, %s)
        ''',
        (name, age, drug, reaction, severity),
    )
    conn.commit()
    conn.close()

    flash('ADR report added.', 'success')
    return redirect(url_for('home'))


@app.route('/delete/<int:adr_id>')
@login_required
def delete(adr_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM adr WHERE id = %s', (adr_id,))
    conn.commit()
    conn.close()
    flash('ADR record deleted.', 'warning')
    return redirect(url_for('home'))


@app.route('/admin')
@admin_required
def admin_panel():
    conn = get_db_connection()
    cursor = conn.cursor()

    metrics = fetch_summary_metrics(cursor)

    cursor.execute(
        'SELECT COALESCE(severity, %s) AS severity, COUNT(*) FROM adr GROUP BY severity ORDER BY COUNT(*) DESC',
        ('Unknown',),
    )
    severity_data = cursor.fetchall()

    cursor.execute(
        'SELECT drug, COUNT(*) AS total FROM adr GROUP BY drug ORDER BY total DESC LIMIT 5'
    )
    top_drugs = cursor.fetchall()

    conn.close()

    return render_template(
        'admin.html',
        metrics=metrics,
        severity_labels=[row[0] for row in severity_data],
        severity_values=[row[1] for row in severity_data],
        drug_labels=[row[0] for row in top_drugs],
        drug_values=[row[1] for row in top_drugs],
    )


@app.route('/dashboard')
@admin_required
def dashboard_redirect():
    return redirect(url_for('admin_panel'))


@app.route('/users', methods=['GET', 'POST'])
@admin_required
def manage_users():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        role = request.form.get('role', 'viewer')

        try:
            cursor.execute(
                'INSERT INTO users (username, password, role) VALUES (%s, %s, %s)',
                (username, generate_password_hash(password), role),
            )
            conn.commit()
            flash('User created successfully.', 'success')
        except psycopg2.Error:
            conn.rollback()
            flash('Unable to create user. Username may already exist.', 'danger')

    cursor.execute('SELECT id, username, role FROM users ORDER BY id ASC')
    users = cursor.fetchall()
    conn.close()

    return render_template('users.html', users=users)


@app.route('/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    if user_id == session.get('user_id'):
        flash('You cannot delete your own account while logged in.', 'warning')
        return redirect(url_for('manage_users'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE id = %s', (user_id,))
    conn.commit()
    conn.close()

    flash('User deleted.', 'info')
    return redirect(url_for('manage_users'))


@app.route('/export')
@login_required
def export_adr():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, name, age, drug, reaction, severity, created_at FROM adr ORDER BY id DESC'
    )
    rows = cursor.fetchall()
    conn.close()

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = 'ADR Reports'

    headers = ['ID', 'Patient Name', 'Age', 'Drug', 'Reaction', 'Severity', 'Reported At']
    sheet.append(headers)

    for row in rows:
        clean_row = list(row)
        clean_row[-1] = clean_row[-1].strftime('%Y-%m-%d %H:%M:%S') if clean_row[-1] else ''
        sheet.append(clean_row)

    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)

    filename = f"adr_reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )


if __name__ == '__main__':
    app.run(debug=True, port=5001)
