import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import os

def get_db_connection():
    conn = mysql.connector.connect(
        host=os.getenv("SQL_HOST", "localhost"),
        user=os.getenv("SQL_USER", "root"),
        password=os.getenv("SQL_PASSWORD", ""),
        database=os.getenv("SQL_DB", "social_sage_db")
    )
    return conn

def insert_user(first_name, last_name, email, password, user_role):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    hashed_pw = generate_password_hash(password)
    try:
        cursor.execute(
            "INSERT INTO users (first_name, last_name, email, password, user_role) VALUES (%s, %s, %s, %s, %s)",
            (first_name, last_name, email, hashed_pw, user_role)
        )
        conn.commit()
        return True
    except mysql.connector.IntegrityError:
        return False
    finally:
        cursor.close()
        conn.close()

def verify_user(email, password):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user and check_password_hash(user['password'], password):
        return user
    else:
        return None