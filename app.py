from flask import Flask, render_template, request, redirect, session, flash, send_file, url_for
import psycopg2
from functools import wraps
import os
import csv
import secrets
import string
from io import StringIO, BytesIO
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-me')
app.secret_key = app.config['SECRET_KEY']
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=os.environ.get('FLASK_ENV') == 'production',
)
app.jinja_env.auto_reload = True

DATABASE_URL = os.environ.get('DATABASE_URL')
ALLOWED_ROLES = {'admin', 'user'}


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
            role VARCHAR(20) NOT NULL DEFAULT 'user'
        )
        '''
    )

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS adr (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            name VARCHAR(120) NOT NULL,
            age INTEGER NOT NULL,
            drug VARCHAR(120) NOT NULL,
            reaction TEXT NOT NULL,
            severity VARCHAR(50) NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        '''
    )

    cursor.execute('ALTER TABLE adr ADD COLUMN IF NOT EXISTS user_id INTEGER')
    cursor.execute(
        '''
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'adr_user_id_fkey'
            ) THEN
                ALTER TABLE adr
                ADD CONSTRAINT adr_user_id_fkey
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
            END IF;
        END $$;
        '''
    )

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS activity_logs (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            action VARCHAR(80) NOT NULL,
            details TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        '''
    )

    cursor.execute("UPDATE users SET role = 'user' WHERE role = 'viewer'")

    admin_user = os.environ.get('ADMIN_USERNAME', 'admin')
    admin_password = os.environ.get('ADMIN_PASSWORD', 'admin1234')
    cursor.execute(
        '''
        INSERT INTO users (username, password, role)
        VALUES (%s, %s, %s)
        ON CONFLICT (username) DO NOTHING
        ''',
        (admin_user, generate_password_hash(admin_password), 'admin'),
    )

    conn.commit()
    conn.close()


def log_activity(action, details=''):
    user_id = session.get('user_id')
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO activity_logs (user_id, action, details) VALUES (%s, %s, %s)',
            (user_id, action, details),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('login'))

        if not ensure_session_identity():
            flash('Your session has expired. Please log in again.', 'warning')
            return redirect(url_for('login'))

        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)

    return login_required(decorated_function)


def user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'user':
            flash('User access required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)

    return login_required(decorated_function)


def ensure_session_identity():
    user_id = session.get('user_id')
    if not user_id:
        return False

    username = session.get('username')
    role = session.get('role')
    if username and role:
        return True

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT username, role FROM users WHERE id = %s', (user_id,))
        user = cursor.fetchone()
        conn.close()

        if not user:
            session.clear()
            return False

        session['username'] = user[0]
        session['role'] = user[1]
        return True
    except psycopg2.Error:
        session.clear()
        return False


def dashboard_redirect_for_role():
    return redirect(url_for('admin_dashboard' if session.get('role') == 'admin' else 'user_dashboard'))


def generate_random_password(length=12):
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_unique_username(cursor, base='user'):
    while True:
        candidate = f"{base}_{secrets.randbelow(900000) + 100000}"
        cursor.execute('SELECT 1 FROM users WHERE username = %s', (candidate,))
        if not cursor.fetchone():
            return candidate


def get_dashboard_metrics(cursor, user_id=None):
    filter_sql = ''
    params = []
    if user_id:
        filter_sql = ' WHERE user_id = %s'
        params = [user_id]

    cursor.execute(f'SELECT COUNT(*) FROM adr{filter_sql}', tuple(params))
    total_reports = cursor.fetchone()[0]

    date_filter = f"{filter_sql} {'AND' if filter_sql else 'WHERE'} DATE(created_at) = CURRENT_DATE"
    cursor.execute(f'SELECT COUNT(*) FROM adr{date_filter}', tuple(params))
    todays_reports = cursor.fetchone()[0]

    severe_filter = f"{filter_sql} {'AND' if filter_sql else 'WHERE'} LOWER(severity) = 'severe'"
    cursor.execute(f'SELECT COUNT(*) FROM adr{severe_filter}', tuple(params))
    severe_cases = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]

    cursor.execute(
        f"SELECT COUNT(DISTINCT LOWER(TRIM(drug))) FROM adr{filter_sql} "
        "AND TRIM(COALESCE(drug, '')) <> ''" if filter_sql else
        "SELECT COUNT(DISTINCT LOWER(TRIM(drug))) FROM adr WHERE TRIM(COALESCE(drug, '')) <> ''",
        tuple(params),
    )
    total_drugs = cursor.fetchone()[0]

    return {
        'total_reports': total_reports,
        'todays_reports': todays_reports,
        'severe_cases': severe_cases,
        'total_users': total_users,
        'total_drugs': total_drugs,
    }


def get_chart_data(cursor, user_id=None):
    params = []
    where = ''
    if user_id:
        where = 'WHERE user_id = %s'
        params = [user_id]

    cursor.execute(
        f'''
        SELECT COALESCE(severity, 'Unknown') AS label, COUNT(*) AS count
        FROM adr
        {where}
        GROUP BY label
        ORDER BY count DESC
        ''',
        tuple(params),
    )
    severity_data = cursor.fetchall()

    cursor.execute(
        f'''
        SELECT COALESCE(drug, 'Unknown') AS label, COUNT(*) AS count
        FROM adr
        {where}
        GROUP BY label
        ORDER BY count DESC
        LIMIT 10
        ''',
        tuple(params),
    )
    drug_data = cursor.fetchall()

    return {
        'severity_labels': [row[0] for row in severity_data],
        'severity_values': [row[1] for row in severity_data],
        'drug_labels': [row[0] for row in drug_data],
        'drug_values': [row[1] for row in drug_data],
    }


def get_report_filters():
    return {
        'search': request.args.get('search', '').strip(),
        'drug': request.args.get('drug', '').strip(),
        'severity': request.args.get('severity', '').strip(),
        'date_from': request.args.get('date_from', '').strip(),
        'date_to': request.args.get('date_to', '').strip(),
    }


def fetch_reports_with_filters(cursor, filters, user_id=None):
    query = '''
        SELECT a.id, a.name, a.age, a.drug, a.reaction, a.severity, a.created_at, COALESCE(u.username, 'Unknown')
        FROM adr a
        LEFT JOIN users u ON u.id = a.user_id
        WHERE 1=1
    '''
    params = []

    if user_id:
        query += ' AND a.user_id = %s'
        params.append(user_id)

    if filters['search']:
        query += ' AND (a.name ILIKE %s OR a.drug ILIKE %s OR a.reaction ILIKE %s OR a.severity ILIKE %s)'
        params.extend([f"%{filters['search']}%"] * 4)

    if filters['drug']:
        query += ' AND a.drug ILIKE %s'
        params.append(f"%{filters['drug']}%")

    if filters['severity']:
        query += ' AND a.severity = %s'
        params.append(filters['severity'])

    if filters['date_from']:
        query += ' AND DATE(a.created_at) >= %s'
        params.append(filters['date_from'])

    if filters['date_to']:
        query += ' AND DATE(a.created_at) <= %s'
        params.append(filters['date_to'])

    query += ' ORDER BY a.created_at DESC, a.id DESC'
    cursor.execute(query, tuple(params))
    return cursor.fetchall()


def can_access_report(cursor, adr_id, user_id, role):
    if role == 'admin':
        cursor.execute('SELECT 1 FROM adr WHERE id = %s', (adr_id,))
    else:
        cursor.execute('SELECT 1 FROM adr WHERE id = %s AND user_id = %s', (adr_id, user_id))
    return cursor.fetchone() is not None


@app.before_request
def startup():
    if not getattr(app, '_db_initialized', False):
        init_db()
        app._db_initialized = True


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        return dashboard_redirect_for_role()

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if not username or not password:
            flash('Username and password are required.', 'warning')
            return render_template('login.html')

        try:
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
                    conn.close()
                    log_activity('LOGIN', f'User {user[1]} logged in')
                    flash('Login successful.', 'success')
                    return dashboard_redirect_for_role()

            conn.close()
            flash('Invalid username or password.', 'danger')
        except psycopg2.Error:
            flash('Unable to authenticate at this time.', 'danger')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    username = session.get('username', 'Unknown')
    log_activity('LOGOUT', f'User {username} logged out')
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/')
def home():
    if session.get('user_id'):
        return dashboard_redirect_for_role()
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    return dashboard_redirect_for_role()


@app.route('/admin')
@admin_required
def admin_dashboard():
    filters = get_report_filters()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        metrics = get_dashboard_metrics(cursor)
        chart_data = get_chart_data(cursor)
        adr_list = fetch_reports_with_filters(cursor, filters)

        cursor.execute('SELECT id, username, role FROM users ORDER BY id ASC')
        users = cursor.fetchall()

        cursor.execute(
            "SELECT DISTINCT severity FROM adr WHERE TRIM(COALESCE(severity, '')) <> '' ORDER BY severity ASC"
        )
        severity_options = [row[0] for row in cursor.fetchall()]

        conn.close()

        return render_template(
            'admin_dashboard.html',
            metrics=metrics,
            users=users,
            adr_list=adr_list,
            filters=filters,
            severity_options=severity_options,
            severity_labels=chart_data['severity_labels'],
            severity_values=chart_data['severity_values'],
            drug_labels=chart_data['drug_labels'],
            drug_values=chart_data['drug_values'],
        )
    except psycopg2.Error:
        flash('Unable to load admin dashboard.', 'danger')
        return render_template(
            'admin_dashboard.html',
            metrics={'total_reports': 0, 'todays_reports': 0, 'severe_cases': 0, 'total_users': 0, 'total_drugs': 0},
            users=[],
            adr_list=[],
            filters=filters,
            severity_options=['Mild', 'Moderate', 'Severe'],
            severity_labels=[],
            severity_values=[],
            drug_labels=[],
            drug_values=[],
        )


@app.route('/user')
@user_required
def user_dashboard():
    filters = get_report_filters()
    user_id = session.get('user_id')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        metrics = get_dashboard_metrics(cursor, user_id=user_id)
        chart_data = get_chart_data(cursor, user_id=user_id)
        adr_list = fetch_reports_with_filters(cursor, filters, user_id=user_id)

        cursor.execute(
            "SELECT DISTINCT severity FROM adr WHERE user_id = %s AND TRIM(COALESCE(severity, '')) <> '' ORDER BY severity ASC",
            (user_id,),
        )
        severity_options = [row[0] for row in cursor.fetchall()]

        conn.close()

        return render_template(
            'user_dashboard.html',
            metrics=metrics,
            adr_list=adr_list,
            filters=filters,
            severity_options=severity_options,
            severity_labels=chart_data['severity_labels'],
            severity_values=chart_data['severity_values'],
            drug_labels=chart_data['drug_labels'],
            drug_values=chart_data['drug_values'],
        )
    except psycopg2.Error:
        flash('Unable to load user dashboard.', 'danger')
        return render_template(
            'user_dashboard.html',
            metrics={'total_reports': 0, 'todays_reports': 0, 'severe_cases': 0, 'total_users': 0, 'total_drugs': 0},
            adr_list=[],
            filters=filters,
            severity_options=['Mild', 'Moderate', 'Severe'],
            severity_labels=[],
            severity_values=[],
            drug_labels=[],
            drug_values=[],
        )


@app.route('/add', methods=['POST'])
@login_required
def add():
    name = request.form.get('name', '').strip()
    age = request.form.get('age', '').strip()
    drug = request.form.get('drug', '').strip()
    reaction = request.form.get('reaction', '').strip()
    severity = request.form.get('severity', '').strip()

    if not all([name, age, drug, reaction, severity]):
        flash('All ADR fields are required.', 'warning')
        return dashboard_redirect_for_role()

    try:
        age_value = int(age)
        if age_value < 0:
            raise ValueError
    except ValueError:
        flash('Age must be a valid non-negative number.', 'warning')
        return dashboard_redirect_for_role()

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''
            INSERT INTO adr (user_id, name, age, drug, reaction, severity)
            VALUES (%s, %s, %s, %s, %s, %s)
            ''',
            (session.get('user_id'), name, age_value, drug, reaction, severity),
        )
        conn.commit()
        conn.close()
        log_activity('ADD_REPORT', f'Added ADR report for patient {name}')
        flash('ADR report added.', 'success')
    except psycopg2.Error:
        flash('Could not add ADR report.', 'danger')

    return dashboard_redirect_for_role()


@app.route('/reports/edit/<int:adr_id>', methods=['GET', 'POST'])
@login_required
def edit_report(adr_id):
    user_id = session.get('user_id')
    role = session.get('role')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if not can_access_report(cursor, adr_id, user_id, role):
            conn.close()
            flash('You do not have permission to edit this ADR report.', 'danger')
            return dashboard_redirect_for_role()

        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            age = request.form.get('age', '').strip()
            drug = request.form.get('drug', '').strip()
            reaction = request.form.get('reaction', '').strip()
            severity = request.form.get('severity', '').strip()

            if not all([name, age, drug, reaction, severity]):
                flash('All ADR fields are required.', 'warning')
                return redirect(url_for('edit_report', adr_id=adr_id))

            try:
                age_value = int(age)
                if age_value < 0:
                    raise ValueError
            except ValueError:
                flash('Age must be a valid non-negative number.', 'warning')
                return redirect(url_for('edit_report', adr_id=adr_id))

            if role == 'admin':
                cursor.execute(
                    'UPDATE adr SET name = %s, age = %s, drug = %s, reaction = %s, severity = %s WHERE id = %s',
                    (name, age_value, drug, reaction, severity, adr_id),
                )
            else:
                cursor.execute(
                    'UPDATE adr SET name = %s, age = %s, drug = %s, reaction = %s, severity = %s WHERE id = %s AND user_id = %s',
                    (name, age_value, drug, reaction, severity, adr_id, user_id),
                )
            conn.commit()
            conn.close()
            log_activity('EDIT_REPORT', f'Edited ADR report #{adr_id}')
            flash('ADR report updated successfully.', 'success')
            return dashboard_redirect_for_role()

        if role == 'admin':
            cursor.execute(
                'SELECT id, name, age, drug, reaction, severity, created_at FROM adr WHERE id = %s',
                (adr_id,),
            )
        else:
            cursor.execute(
                'SELECT id, name, age, drug, reaction, severity, created_at FROM adr WHERE id = %s AND user_id = %s',
                (adr_id, user_id),
            )
        adr = cursor.fetchone()
        conn.close()

        if not adr:
            flash('ADR record not found.', 'warning')
            return dashboard_redirect_for_role()

        return render_template('edit.html', adr=adr)
    except psycopg2.Error:
        flash('Unable to edit ADR report right now.', 'danger')
        return dashboard_redirect_for_role()


@app.route('/reports/delete/<int:adr_id>', methods=['POST'])
@login_required
def delete_report(adr_id):
    user_id = session.get('user_id')
    role = session.get('role')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if role == 'admin':
            cursor.execute('DELETE FROM adr WHERE id = %s', (adr_id,))
        else:
            cursor.execute('DELETE FROM adr WHERE id = %s AND user_id = %s', (adr_id, user_id))

        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        if deleted:
            log_activity('DELETE_REPORT', f'Deleted ADR report #{adr_id}')
            flash('ADR report deleted.', 'warning')
        else:
            flash('ADR record not found or not permitted.', 'warning')
    except psycopg2.Error:
        flash('Could not delete ADR report.', 'danger')

    return dashboard_redirect_for_role()


@app.route('/users/create', methods=['POST'])
@admin_required
def create_user():
    username = request.form.get('username', '').strip()

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if not username:
            username = generate_unique_username(cursor)
        password = generate_random_password()
        cursor.execute(
            'INSERT INTO users (username, password, role) VALUES (%s, %s, %s)',
            (username, generate_password_hash(password), 'user'),
        )
        conn.commit()
        conn.close()
        log_activity('CREATE_USER', f'Created user {username} with role user')
        flash(f'User created: {username} | Temporary password: {password}', 'success')
    except psycopg2.Error:
        flash('Unable to create user. Username may already exist.', 'danger')

    return redirect(url_for('admin_dashboard'))


@app.route('/users/reset-password/<int:user_id>', methods=['POST'])
@admin_required
def reset_user_password(user_id):
    new_password = generate_random_password()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE users SET password = %s WHERE id = %s',
            (generate_password_hash(new_password), user_id),
        )
        updated = cursor.rowcount
        conn.commit()
        conn.close()
        if updated:
            log_activity('RESET_PASSWORD', f'Reset password for user #{user_id}')
            flash(f'Password reset successfully. New temporary password: {new_password}', 'success')
        else:
            flash('User not found.', 'warning')
    except psycopg2.Error:
        flash('Unable to reset password.', 'danger')
    return redirect(url_for('admin_dashboard'))


@app.route('/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    if user_id == session.get('user_id'):
        flash('You cannot delete your own account while logged in.', 'warning')
        return redirect(url_for('admin_dashboard'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE id = %s', (user_id,))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        if deleted:
            log_activity('DELETE_USER', f'Deleted user id #{user_id}')
            flash('User deleted.', 'info')
        else:
            flash('User not found.', 'warning')
    except psycopg2.Error:
        flash('Unable to delete user.', 'danger')

    return redirect(url_for('admin_dashboard'))


@app.route('/users/role/<int:user_id>', methods=['POST'])
@admin_required
def update_user_role(user_id):
    if user_id == session.get('user_id'):
        flash('You cannot change your own role while logged in.', 'warning')
        return redirect(url_for('admin_dashboard'))

    new_role = request.form.get('role', '').strip().lower()
    if new_role not in ALLOWED_ROLES:
        flash('Invalid role selected.', 'warning')
        return redirect(url_for('admin_dashboard'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET role = %s WHERE id = %s', (new_role, user_id))
        updated = cursor.rowcount
        conn.commit()
        conn.close()

        if updated:
            log_activity('CHANGE_ROLE', f'Changed user #{user_id} role to {new_role}')
            flash('User role updated.', 'success')
        else:
            flash('User not found.', 'warning')
    except psycopg2.Error:
        flash('Unable to update user role.', 'danger')

    return redirect(url_for('admin_dashboard'))


@app.route('/export/csv')
@login_required
def export_adr_csv():
    filters = get_report_filters()
    role = session.get('role')
    owner_id = None if role == 'admin' else session.get('user_id')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        rows = fetch_reports_with_filters(cursor, filters, user_id=owner_id)
        conn.close()

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Patient Name', 'Age', 'Drug', 'Reaction', 'Severity', 'Reported At', 'Owner'])

        for row in rows:
            writer.writerow([
                row[0], row[1], row[2], row[3], row[4], row[5],
                row[6].strftime('%Y-%m-%d %H:%M:%S') if row[6] else '',
                row[7],
            ])

        mem = BytesIO()
        mem.write(output.getvalue().encode('utf-8'))
        mem.seek(0)

        filename = f"adr_reports_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        return send_file(mem, as_attachment=True, download_name=filename, mimetype='text/csv')
    except psycopg2.Error:
        flash('Unable to export CSV right now.', 'danger')
        return dashboard_redirect_for_role()


if __name__ == '__main__':
    app.run(debug=True, port=5001)
