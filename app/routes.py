from flask import Blueprint, render_template, request, redirect, session, flash, url_for, jsonify
from app import mysql
from .email_utils import send_otp_email, send_email
from werkzeug.security import generate_password_hash, check_password_hash
import random
import datetime

main = Blueprint('main', __name__)

@main.route('/')
def welcome():
    return render_template('welcome.html')

@main.route('/login/secretary', methods=['GET', 'POST'])
def login_secretary():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s AND role = 'secretary'", (email,))
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['user_email'] = user[2]
            session['user_role'] = user[4]
            flash('Secretary login successful!')
            return redirect(url_for('main.secretary_dashboard'))
        else:
            flash('Invalid credentials')

    return render_template('login_secretary.html')

@main.route('/login/owner', methods=['GET', 'POST'])
def login_owner():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s AND role = 'owner'", (email,))
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user[3], password):  
            # Storing necessary user info in the session
            session['user_id'] = user[0]  
            session['user_email'] = user[2]  
            session['user_role'] = user[4]  
            flash('Owner login successful!')
            return redirect(url_for('main.owner_dashboard'))
        else:
            flash('Invalid credentials')  # Error flash message if credentials are wrong

    return render_template('login_owner.html')  # Render the login form for GET requests


@main.route('/signup/owner', methods=['GET', 'POST'])
def signup_owner():
    role = 'owner'
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()

        if user:
            flash('User already exists')
            return redirect(url_for('main.signup_owner'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        otp = str(random.randint(100000, 999999))
        session['signup_data'] = {
            'name': name,
            'email': email,
            'password': hashed_password,
            'role': role,
            'otp': otp
        }
        send_otp_email(email, otp)
        return redirect('/verify-otp')

    return render_template('signup_owner.html')

@main.route('/signup/secretary', methods=['GET', 'POST'])
def signup_secretary():
    role = 'secretary'
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()

        if user:
            flash('User already exists')
            return redirect(url_for('main.signup_secretary'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        otp = str(random.randint(100000, 999999))
        session['signup_data'] = {
            'name': name,
            'email': email,
            'password': hashed_password,
            'role': role,
            'otp': otp
        }
        send_otp_email(email, otp)
        return redirect('/verify-otp')

    return render_template('signup_secretary.html')

@main.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        user_otp = request.form['otp']
        real_otp = session['signup_data']['otp']
        if user_otp == real_otp:
            data = session['signup_data']
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO users (name, email, password, role, is_verified) VALUES (%s, %s, %s, %s, %s)",
                        (data['name'], data['email'], data['password'], data['role'], True))
            mysql.connection.commit()
            cur.close()
            session.pop('signup_data', None)
            flash('Signup successful! Please login.')
            return redirect(url_for('main.owner_dashboard'))
        else:
            flash('Invalid OTP')
    return render_template('verify_otp.html')

@main.route('/secretary/dashboard')
def secretary_dashboard():
    if session.get('user_role') != 'secretary':
        flash("Unauthorized access.")
        return redirect(url_for('main.login'))
    return render_template('secretary_dashboard.html')

@main.route('/owner/dashboard')
def owner_dashboard():
    if session.get('user_role') != 'owner':
        flash("Unauthorized access.")
        return redirect(url_for('main.login'))

    email = session['user_email']
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM flats WHERE owner_email = %s", (email,))
    flat = cur.fetchone()

    if not flat:
        flash("No flat linked to this owner.")
        return redirect(url_for('main.login_owner'))

    flat_id = flat[0]
    cur.execute("SELECT month, year, amount_due, amount_paid, status FROM payments WHERE flat_id = %s", (flat_id,))
    payments = cur.fetchall()
    cur.close()

    return render_template("owner_dashboard.html", payments=[
        {
            "month": row[0], "year": row[1],
            "amount_due": float(row[2]),
            "amount_paid": float(row[3]),
            "status": row[4]
        } for row in payments
    ])

@main.route('/add-record', methods=['GET', 'POST'])
def add_record():
    if session.get('user_role') != 'secretary':
        flash("Unauthorized access.")
        return redirect(url_for('main.login'))

    if request.method == 'POST':
        flat_number = request.form['flat_number']
        owner_name = request.form['owner_name']
        owner_email = request.form.get('owner_email')
        default_amount = request.form['default_amount']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO flats (flat_number, owner_name, owner_email, default_amount) VALUES (%s, %s, %s, %s)",
                    (flat_number, owner_name, owner_email, default_amount))
        flat_id = cur.lastrowid

        now = datetime.datetime.now()
        cur.execute("""
            INSERT INTO payments (flat_id, month, year, amount_due, amount_paid, status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (flat_id, now.strftime('%B'), now.year, default_amount, 0.0, 'Pending'))

        mysql.connection.commit()
        cur.close()
        flash("Record and payment added successfully!")
        return redirect(url_for('main.secretary_dashboard'))

    return render_template('add_record.html')

@main.route('/show-flats')
def show_flats():
    if session.get('user_role') != 'secretary':
        flash("Unauthorized access.")
        return redirect(url_for('main.login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM flats")
    records = cur.fetchall()
    cur.close()
    return render_template('show_flats.html', records=records)

@main.route('/delete-flat/<int:flat_id>', methods=['POST'])
def delete_flat(flat_id):
    if session.get('user_role') != 'secretary':
        flash("Unauthorized access.")
        return redirect(url_for('main.login'))

    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM flats WHERE id = %s", (flat_id,))
    mysql.connection.commit()
    cur.close()

    flash("Flat record deleted successfully.")
    return redirect(url_for('main.show_flats'))

@main.route('/payment-status')
def payment_status():
    if session.get('user_role') != 'secretary':
        flash("Unauthorized access.")
        return redirect(url_for('main.login'))

    cur = mysql.connection.cursor()
    cur.execute("""
    SELECT 
        p.id, f.flat_number, f.owner_name, f.owner_email, 
        p.amount_due, p.amount_paid, p.status,
        p.maintenance_value_pending, p.flat_id
    FROM payments p
    JOIN flats f ON p.flat_id = f.id
""")
    rows = cur.fetchall()
    payments = []
    for row in rows:
        payments.append({
            'id': row[0],
            'flat_number': row[1],
            'owner_name': row[2],
            'owner_email': row[3],
            'amount_due': float(row[4]),
            'amount_paid': float(row[5]),
            'status': row[6],
            'maintenance_value_pending': float(row[7]) if row[7] is not None else None,
            'flat_id': row[8]
        })
    cur.close()
    return render_template('payment_status.html', payments=payments)

@main.route('/delete-payment/<int:payment_id>', methods=['POST'])
def delete_payment(payment_id):
    if session.get('user_role') != 'secretary':
        flash("Unauthorized access.")
        return redirect(url_for('main.login'))

    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM payments WHERE id = %s", (payment_id,))
    mysql.connection.commit()
    cur.close()

    flash("Payment record deleted successfully.")
    return redirect(url_for('main.payment_status'))

@main.route('/send-reminder/<int:flat_id>', methods=['POST'])
def send_reminder(flat_id):
    if session.get('user_role') != 'secretary':
        flash('Unauthorized access.')
        return redirect(url_for('main.login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT owner_email FROM flats WHERE id = %s", (flat_id,))
    row = cur.fetchone()
    cur.close()

    if row:
        recipient = row[0]
        subject = "Maintenance Payment Reminder"
        message = f"""Dear Resident,

This is a reminder to pay your pending maintenance dues. Please log in and complete your payment.

Thank you!
Secretary, Flat Maintenance Tracker"""

        send_email(recipient, subject, message)
        flash("✅ Reminder sent successfully.")
    else:
        flash("❌ Flat owner not found.")
    return redirect(url_for('main.payment_status'))

@main.route('/mark-paid/<int:payment_id>', methods=['POST'])
def mark_paid(payment_id):
    if session.get('user_role') != 'secretary':
        flash("Unauthorized access.")
        return redirect(url_for('main.login'))

    data = request.get_json()  # Handling the POST data properly
    months_paid = int(data['months_paid'])

    cur = mysql.connection.cursor()
    cur.execute("SELECT amount_due FROM payments WHERE id = %s", (payment_id,))
    row = cur.fetchone()

    if not row:
        return jsonify({'success': False, 'error': 'Payment record not found'}), 404

    monthly_amount = float(row[0])  # Default amount
    total_paid = monthly_amount * months_paid
    total_due = monthly_amount * months_paid  # Maintenance value pending

    # Update the payment details
    cur.execute("""
        UPDATE payments 
        SET amount_paid = %s, 
            maintenance_value_pending = %s, 
            status = 'Paid' 
        WHERE id = %s
    """, (total_paid, total_due, payment_id))

    mysql.connection.commit()
    cur.close()

    return jsonify({'success': True})

@main.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for('main.welcome'))

