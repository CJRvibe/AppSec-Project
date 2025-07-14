import os
import mysql.connector
from flask import g, current_app
from werkzeug.security import generate_password_hash, check_password_hash

def insert_user(first_name, last_name, email, password, user_role):
    conn = get_db()
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
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user and check_password_hash(user['password'], password):
        return user
    else:
        return None

def open_db():
    connection = mysql.connector.connect(
        host=os.getenv("SQL_HOST"),
        user=os.getenv("SQL_USER"),
        password=os.getenv("SQL_PASSWORD"),
        database="social_sage_db"
    )

    return connection

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


def close_db(exception=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def get_user_by_id(user_id):
    conn = get_db()
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


def add_group_proposal(name, topic, description, max_size, is_public, activity_occurence, reason):
    connection = get_db()
    cursor = connection.cursor()
    values = (name, topic, description, max_size, is_public, activity_occurence)
    statement = """
    INSERT INTO interest_group (name, topic, description, max_size, is_public,
        activity_occurence_id, status_id, owner)
    VALUES (%s, %s, %s, %s, %s, %s, 1, 1)
    """ # change to generate dynamic owner

    cursor.execute(statement, values)

    cursor.execute("INSERT INTO interest_group_proposals VALUES (%s, %s)", (cursor.lastrowid, reason))
    connection.commit()

def add_activity_tags(cursor, activity_id, tags):
    for tag in tags:
        cursor.execute("SELECT tag_id FROM tags WHERE tag_id = %s", (tag, ))
        result = cursor.fetchone()
        if result:
            tag_id = result[0]
        else:
            cursor.execute("INSERT INTO tags (name) VALUES (%s)", (tag, ))
            tag_id = cursor.lastrowid

        cursor.execute("INSERT INTO activity_tags VALUES (%s, %s)", (activity_id, tag_id))


def add_activity_proposal(name, description, start_datetime, end_datetime, max_size, funds, location, tags, remarks):
    # MUST CHANGE TO GET ACTIVITY_ID
    connection = get_db()
    cursor = connection.cursor()
    main_values = (name, description, start_datetime, end_datetime, max_size, funds, location, remarks)

    main_statement = """
    INSERT INTO interest_activity (name, description, start_datetime, end_datetime, max_size, funds,
        location_code, remarks, status_id, group_id)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1, 3)
    """
    cursor.execute(main_statement, main_values)
    add_activity_tags(connection.cursor(), cursor.lastrowid, tags)
    connection.commit()


def get_group_proposals():
    connection = get_db()
    cursor = connection.cursor()
    statement = """
    SELECT ig.group_id, ig.name, ig.topic, ig.description, ig.max_size, ig.is_public, ac.title
    FROM interest_group ig
    INNER JOIN interest_group_proposals igp ON ig.group_id = igp.group_id
    INNER JOIN activity_occurences ac ON ig.activity_occurence_id = ac.activity_occurence_id
    WHERE ig.status_id = 1;
    """

    cursor.execute(statement)
    return cursor.fetchall()