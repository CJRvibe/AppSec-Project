import os
import mysql.connector
from flask import g, current_app
from werkzeug.security import generate_password_hash, check_password_hash


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

def get_db():
    if "db" not in g:
        connection = mysql.connector.connect(
            host=os.getenv("SQL_HOST"),
            user=os.getenv("SQL_USER"),
            password=os.getenv("SQL_PASSWORD"),
            database="social_sage_db"
        )
        g.db = connection
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def get_user_by_id(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT u.first_name, u.last_name, u.email, r.user_role
        FROM users u
        LEFT JOIN user_role r ON u.user_role = r.role_id
        WHERE u.user_id = %s
    """, (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user