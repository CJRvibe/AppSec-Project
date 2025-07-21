import os
import mysql.connector
from flask import g, current_app
from werkzeug.security import generate_password_hash, check_password_hash

def get_db():
    if "db" not in g:
        g.db = mysql.connector.connect(
            host=os.getenv("SQL_HOST"),
            user=os.getenv("SQL_USER"),
            password=os.getenv("SQL_PASSWORD"),
            database="social_sage_db"
        )

    return g.db

def open_db():
    connection = mysql.connector.connect(
        host=os.getenv("SQL_HOST"),
        user=os.getenv("SQL_USER"),
        password=os.getenv("SQL_PASSWORD"),
        database="social_sage_db"
    )

    return connection

def hashed_pw(password):
    hashed_pw = generate_password_hash(password)
    return hashed_pw

def insert_user(first_name, last_name, email, password, user_role):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "INSERT INTO users (first_name, last_name, email, password, user_role) VALUES (%s, %s, %s, %s, %s)",
            (first_name, last_name, email, password, user_role)
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
    if user and check_password_hash(user['password'], password):
        return user
    else:
        return None
    
def close_db(exception=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def get_all_groups():
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    statement = "SELECT * FROM interest_group"
    cursor.execute(statement)
    return cursor.fetchall()

def get_group_by_id(group_id):
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    statement = "SELECT * FROM interest_group WHERE group_id = %s"
    cursor.execute(statement, (group_id,))
    return cursor.fetchone()

def get_activities_by_group_id(group_id, search=None):
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    
    if search:
        statement = """
            SELECT * FROM interest_activity 
            WHERE group_id = %s AND LOWER(name) LIKE %s
        """
        cursor.execute(statement, (group_id, f"%{search.lower()}%"))
    else:
        statement = "SELECT * FROM interest_activity WHERE group_id = %s"
        cursor.execute(statement, (group_id,))
    
    return cursor.fetchall()

def get_activity_by_id(activity_id):
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    statement = "SELECT * FROM interest_activity WHERE activity_id = %s"
    cursor.execute(statement, (activity_id,))
    return cursor.fetchone()

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
    return user


def add_group_proposal(name, topic, description, max_size, is_public, activity_occurence, reason):
    connection = get_db()
    cursor = connection.cursor()
    values = (name, topic, description, max_size, is_public, activity_occurence, reason)
    statement = """
    INSERT INTO interest_group (name, topic, description, max_size, is_public,
        activity_occurence_id, proposal, status_id, owner)
    VALUES (%s, %s, %s, %s, %s, %s, %s, 1, 3)
    """ # change to generate dynamic owner

    cursor.execute(statement, values)
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


def search_groups(query):
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    statement = """
        SELECT * FROM interest_group
        WHERE name LIKE %s OR topic LIKE %s OR description LIKE %s
    """
    like_query = f"%{query}%"
    cursor.execute(statement, (like_query, like_query, like_query))
    return cursor.fetchall()


def admin_get_group_by_id(id: int):
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    statement = """
    SELECT
        ig.group_id, ig.name, ig.topic, ig.description,
        ig.max_size, ig.is_public, ig.picture, ac.title occurence,
        s.title status, u.email, ig.proposal
    FROM interest_group ig
    INNER JOIN activity_occurences ac ON ig.activity_occurence_id = ac.activity_occurence_id
    INNER JOIN statuses s ON s.status_id = ig.status_id
    INNER JOIN users u ON ig.owner = u.user_id
    WHERE ig.group_id = %s;
    """

    cursor.execute(statement, (id, ))
    return cursor.fetchone()


def admin_update_group_proposal(id, approved=False):
    connection = get_db()
    cursor = connection.cursor()
    status = "approved" if approved else "rejected"

    statement = """
    UPDATE interest_group
    SET status_id = (SELECT status_id FROM statuses WHERE title = %s)
    WHERE group_id = %s;
    """

    cursor.execute(statement, (status, id))
    connection.commit()


def admin_get_groups(type="approved"):
    connection = get_db()
    cursor = connection.cursor(dictionary=True)

    if type == "pending": status_id = 1
    elif type == "approved": status_id = 2
    elif type == "rejected": status_id = 3

    statement = """
    SELECT ig.group_id, ig.name, ig.topic, ig.max_size, ig.is_public, ac.title occurence
    FROM interest_group ig
    INNER JOIN activity_occurences ac ON ig.activity_occurence_id = ac.activity_occurence_id
    INNER JOIN statuses s ON ig.status_id = s.status_id
    WHERE s.status_id = %s;
    """

    cursor.execute(statement, (status_id,))
    return cursor.fetchall()


def admin_get_group_activity(id):
    connection = get_db()
    cursor = connection.cursor(dictionary=True)

    statement = """
    SELECT ia.activity_id, ig.name group_name, ia.name, ia.description, ia.start_datetime, ia.end_datetime,
           ia.max_size, ia.funds, al.name location, ia.remarks, s.title status
    FROM interest_activity ia
    INNER JOIN interest_group ig ON ia.group_id = ig.group_id
    INNER JOIN activity_location al ON ia.location_code = al.location_code
    INNER JOIN statuses s ON ia.status_id = s.status_id
    WHERE ia.activity_id = %s;
    """

    cursor.execute(statement, (id, ))
    return cursor.fetchone()


def admin_get_group_activities(type="approved"):
    connection = get_db()
    cursor = connection.cursor(dictionary=True)

    if type == "pending": status_id = 1
    elif type == "approved": status_id = 2
    elif type == "rejected": status_id = 3

    statement = """
    SELECT ia.activity_id, ig.name group_name, ia.name, ia.start_datetime, ia.end_datetime, 
            ia.max_size, ia.funds, al.name location
    FROM interest_activity ia
    INNER JOIN interest_group ig ON ia.group_id = ig.group_id
    INNER JOIN activity_location al ON ia.location_code = al.location_code
    INNER JOIN statuses s ON ia.status_id = s.status_id
    WHERE ia.status_id = %s;
    """

    cursor.execute(statement, (status_id, ))
    return cursor.fetchall()


def admin_update_activity_proposal(id, approved=False):
    connection = get_db()
    cursor = connection.cursor()
    status = "approved" if approved else "rejected"

    statement = """
    UPDATE interest_activity
    SET status_id = (SELECT status_id FROM statuses WHERE title = %s)
    WHERE activity_id = %s;
    """

    cursor.execute(statement, (status, id))
    connection.commit()