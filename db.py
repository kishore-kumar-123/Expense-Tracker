import os
import mysql.connector

# MySQL Database Configuration (reads from environment variable MYSQL_PASSWORD if set)
DB_CONFIG = {
    'host': os.environ.get('MYSQL_HOST', 'localhost'),
    'port': int(os.environ.get('MYSQL_PORT', 3306)),
    'user': os.environ.get('MYSQL_USER', 'root'),
    'password': os.environ.get('MYSQL_PASSWORD', ''),
    'database': os.environ.get('MYSQL_DATABASE', 'expense_db')
}

def get_connection():
    """Connect to MySQL database expense_db."""
    return mysql.connector.connect(**DB_CONFIG)

def init_db():
    """Create database and expenses table if they do not exist."""
    # Step 1: Connect to MySQL server to ensure expense_db database exists
    conn_server = mysql.connector.connect(
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password']
    )
    cursor = conn_server.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS expense_db")
    conn_server.commit()
    cursor.close()
    conn_server.close()

    # Step 2: Ensure expenses table exists inside expense_db
    conn = get_connection()
    cursor = conn.cursor()
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS expenses (
        expense_id INT AUTO_INCREMENT PRIMARY KEY,
        expense_date DATE NOT NULL,
        category VARCHAR(100) NOT NULL,
        amount DOUBLE NOT NULL,
        description TEXT
    );
    """
    cursor.execute(create_table_sql)
    conn.commit()
    cursor.close()
    conn.close()

def add_expense(expense_date, category, amount, description):
    """Insert a new expense into MySQL."""
    conn = get_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO expenses (expense_date, category, amount, description) VALUES (%s, %s, %s, %s)"
    cursor.execute(sql, (expense_date, category, float(amount), description))
    conn.commit()
    cursor.close()
    conn.close()

def get_all_expenses():
    """Fetch all expenses ordered by date descending."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    sql = "SELECT expense_id, expense_date, category, amount, description FROM expenses ORDER BY expense_date DESC, expense_id DESC"
    cursor.execute(sql)
    expenses = cursor.fetchall()
    cursor.close()
    conn.close()
    return expenses

def get_category_summary():
    """Fetch total expenses grouped by category."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    sql = "SELECT category, SUM(amount) AS total FROM expenses GROUP BY category ORDER BY total DESC"
    cursor.execute(sql)
    summary = cursor.fetchall()
    cursor.close()
    conn.close()
    return summary

def get_monthly_summary(month_number):
    """Calculate total expenses for a specific month (1-12)."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    sql = "SELECT SUM(amount) AS total FROM expenses WHERE MONTH(expense_date) = %s"
    cursor.execute(sql, (int(month_number),))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if row and row['total'] is not None:
        return row['total']
    return 0.0

def delete_expense(expense_id):
    """Delete an expense record by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    sql = "DELETE FROM expenses WHERE expense_id = %s"
    cursor.execute(sql, (int(expense_id),))
    conn.commit()
    cursor.close()
    conn.close()
