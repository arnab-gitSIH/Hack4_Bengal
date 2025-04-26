from flask import Flask
import pymysql
pymysql.install_as_MySQLdb()
from flask_mysqldb import MySQL

app = Flask(__name__)

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''  # Replace with your actual password
app.config['MYSQL_DB'] = 'flat_maintenance'
app.config['MYSQL_PORT'] = 3306  # This is the default MySQL port

# Initialize MySQL
mysql = MySQL(app)

def create_users_table():
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100),
                email VARCHAR(100) UNIQUE,
                password VARCHAR(200),
                role ENUM('secretary', 'owner'),
                is_verified BOOLEAN DEFAULT FALSE
            );
        """)
        # Flats table with enforced NOT NULL on owner_email
        cur.execute("""
            CREATE TABLE IF NOT EXISTS flats (
                id INT AUTO_INCREMENT PRIMARY KEY,
                flat_number VARCHAR(10) UNIQUE NOT NULL,
                owner_name VARCHAR(100) NOT NULL,
                owner_email VARCHAR(100) NOT NULL,
                default_amount DECIMAL(10, 2) NOT NULL
            );
        """)

        # Payments table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                flat_number INT NOT NULL,
                month VARCHAR(20),
                year INT,
                amount_due DECIMAL(10, 2),
                amount_paid DECIMAL(10, 2),
                maintenance_value_pending DECIMAL(10, 2),
                status ENUM('Paid', 'Pending') DEFAULT 'Pending',
                FOREIGN KEY (flat_number) REFERENCES flats(number)
            );
        """)
        mysql.connection.commit()
        cur.close()
        print("✅ Users table created successfully.")
    except Exception as e:
        print(f"❌ Error creating users table: {e}")

if __name__ == '__main__':
    with app.app_context():
        create_users_table()
