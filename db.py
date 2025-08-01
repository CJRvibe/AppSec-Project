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
    except mysql.connector.IntegrityError as e:
        print("IntegrityError inserting user:", e)
        return False
    except Exception as e:
        print("Error inserting user:", e)
        return False
    finally:
        cursor.close()

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
    statement = "SELECT group_id, name, topic, description, max_size, is_public, picture, proposal, activity_occurence_id, status_id, owner FROM interest_group WHERE status_id = 2"
    cursor.execute(statement)
    return cursor.fetchall()

def get_group_by_id(group_id):
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    statement = "SELECT group_id, name, topic, description, max_size, is_public, picture, proposal, activity_occurence_id, status_id, owner FROM interest_group WHERE group_id = %s"
    cursor.execute(statement, (group_id,))
    return cursor.fetchone()

def get_activities_by_group_id(group_id, search=None):
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    
    if search:
        statement = """
            SELECT activity_id, name, description, start_datetime, end_datetime, max_size, funds, location_code, remarks, picture, status_id, group_id FROM interest_activity 
            WHERE group_id = %s AND LOWER(name) LIKE %s
        """
        cursor.execute(statement, (group_id, f"%{search.lower()}%"))
    else:
        statement = "SELECT activity_id, name, description, start_datetime, end_datetime, max_size, funds, location_code, remarks, picture, status_id, group_id FROM interest_activity WHERE group_id = %s"
        cursor.execute(statement, (group_id,))
    
    return cursor.fetchall()

def get_activity_by_id(activity_id):
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    statement = "SELECT activity_id, name, description, start_datetime, end_datetime, max_size, funds, location_code, remarks, picture, status_id, group_id FROM interest_activity WHERE activity_id = %s"
    cursor.execute(statement, (activity_id,))
    return cursor.fetchone()

def get_user_by_id(user_id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT u.first_name, u.last_name, u.email, r.user_role, u.profile_pic
        FROM users u
        LEFT JOIN user_role r ON u.user_role = r.role_id
        WHERE u.user_id = %s
    """, (user_id,))
    user = cursor.fetchone()
    return user


def add_group_proposal(name, topic, description, max_size, is_public, activity_occurence, reason, owner):
    connection = get_db()
    cursor = connection.cursor()
    values = (name, topic, description, max_size, is_public, activity_occurence, reason, owner)
    statement = """
    INSERT INTO interest_group (name, topic, description, max_size, is_public,
        activity_occurence_id, proposal, status_id, owner)
    VALUES (%s, %s, %s, %s, %s, %s, %s, 1, %s)
    """

    cursor.execute(statement, values)
    connection.commit()

def add_activity_tags(cursor, activity_id, tags):
    for tag in tags:
        cursor.execute("SELECT tag_id FROM tags WHERE name = %s", (tag, ))
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
        SELECT group_id, name, topic, description, max_size, is_public, picture, proposal, activity_occurence_id, status_id, owner FROM interest_group
        WHERE status_id  = 2 AND name LIKE %s OR topic LIKE %s OR description LIKE %s
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

def check_user_joined_group(user_id, group_id):
    connection = get_db()
    cursor = connection.cursor()
    statement = "SELECT * FROM user_interest_group WHERE user_id = %s AND group_id = %s"
    cursor.execute(statement, (user_id, group_id))
    return cursor.fetchone() is not None

def join_group(user_id, group_id):
    connection = get_db()
    cursor = connection.cursor()

    group = get_group_by_id(group_id)
    status_id = 2 if group["is_public"] == 1 else 1

    statement = """
        INSERT INTO user_interest_group (user_id, group_id, date_joined, status_id)
        VALUES (%s, %s, NOW(), %s)
        ON DUPLICATE KEY UPDATE status_id = VALUES(status_id)
    """
    cursor.execute(statement, (user_id, group_id, status_id))
    connection.commit()



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

def update_user_profile_pic(user_id, profile_pic):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE users SET profile_pic = %s WHERE user_id = %s",
            (profile_pic, user_id)
        )
        conn.commit()
        return True
    except Exception as e:
        print("Error saving profile picture:", e)
        return False

def get_user_profile_pic(user_id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT profile_pic FROM users WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        if result and result['profile_pic']:
            return result['profile_pic']
        else:
            return None
    finally:
        cursor.close()

def get_user_by_email(email):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT user_id, first_name, last_name, email, password, profile_pic, email_notif, mfa_secret, mfa_enabled, user_role FROM users WHERE email = %s", (email,))
    result = cursor.fetchone()
    cursor.close()  
    return result

def update_user_role(user_id, role):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET user_role = %s WHERE user_id = %s", (role, user_id))
    conn.commit()


def update_user_info(user_id, first_name, last_name, email):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET first_name = %s, last_name = %s, email = %s WHERE user_id = %s",
        (first_name, last_name, email, user_id)
    )
    conn.commit()


def get_all_users():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT user_id, first_name, last_name, email, password, profile_pic, email_notif, mfa_secret, mfa_enabled, user_role FROM users")
    users = cursor.fetchall()
    return users

def get_users_by_role(role):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT user_id, first_name, last_name, email, password, profile_pic, email_notif, mfa_secret, mfa_enabled, user_role FROM users WHERE user_role = %s", (role,))
    users = cursor.fetchall()
    return users

def get_pending_users_by_group(group_id):
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    statement = """
        SELECT u.user_id, u.first_name, u.last_name, u.email
        FROM user_interest_group ug
        INNER JOIN users u ON ug.user_id = u.user_id
        WHERE ug.group_id = %s AND ug.status_id = 1
    """
    cursor.execute(statement, (group_id,))
    return cursor.fetchall()

def get_approved_users_by_group(group_id):
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    statement = """
        SELECT u.user_id, u.first_name, u.last_name, u.email
        FROM user_interest_group ug
        INNER JOIN users u ON ug.user_id = u.user_id
        WHERE ug.group_id = %s AND ug.status_id = 2
    """
    cursor.execute(statement, (group_id,))
    return cursor.fetchall()

def approve_user(user_id, group_id):
    connection = get_db()
    cursor = connection.cursor()
    statement = """
        UPDATE user_interest_group
        SET status_id = 2
        WHERE user_id = %s AND group_id = %s
    """
    cursor.execute(statement, (user_id, group_id))
    connection.commit()

def remove_user_from_group(user_id, group_id):
    connection = get_db()
    cursor = connection.cursor()
    statement = """
        DELETE FROM user_interest_group
        WHERE user_id = %s AND group_id = %s
    """
    cursor.execute(statement, (user_id, group_id))
    connection.commit()

def remove_activity(activity_id):
    connection = get_db()
    cursor = connection.cursor()
    statement = "DELETE FROM interest_activity WHERE activity_id = %s"
    cursor.execute(statement, (activity_id,))
    connection.commit()

def update_user_password(email, hashed_password):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET password = %s WHERE email = %s",
        (hashed_password, email)
    )
    conn.commit()
    

def update_user_mfa_secret(user_id, secret):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET mfa_secret = %s WHERE user_id = %s", (secret, user_id))
    conn.commit()
   

def get_user_mfa_secret(user_id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT mfa_secret FROM users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    return user['mfa_secret'] if user else None

def enable_user_mfa(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET mfa_enabled = 1 WHERE user_id = %s", (user_id,))
    conn.commit()

def disable_user_mfa(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET mfa_enabled = 0, mfa_secret = NULL WHERE user_id = %s", (user_id,))
    conn.commit()

def is_user_mfa_enabled(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT mfa_enabled FROM users WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    return result and result[0] == 1

def get_groups_by_user(user_id):
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    
    query = """
        SELECT ig.*
        FROM interest_group ig
        JOIN user_interest_group uig ON ig.group_id = uig.group_id
        WHERE uig.user_id = %s AND uig.status_id = (
            SELECT status_id FROM statuses WHERE title = 'approved'
        )
    """
    cursor.execute(query, (user_id,))
    return cursor.fetchall()


def add_flag_group(group_id, user_id, reason):
    connection = get_db()
    cursor = connection.cursor()

    statement = """
    INSERT INTO flagged_groups (group_id, user_id, status_id, reason)
    VALUES (%s, %s, 1, %s)
    """

    cursor.execute(statement, (group_id, user_id, reason))
    connection.commit()

def get_groups_by_owner(user_id):
    connection = get_db()
    cursor = connection.cursor(dictionary=True)

    statement = "SELECT group_id, name, topic, description, max_size, is_public, picture, proposal, activity_occurence_id, status_id, owner FROM interest_group WHERE owner = %s"
    cursor.execute(statement, (user_id,))
    return cursor.fetchall()

#admin dashboard

def get_total_users():
    cursor = get_db().cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) AS total FROM users")
    return cursor.fetchone()["total"]

def get_total_groups():
    cursor = get_db().cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) AS total FROM interest_group")
    return cursor.fetchone()["total"]

def get_total_activities():
    cursor = get_db().cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) AS total FROM interest_activity")
    return cursor.fetchone()["total"]

def get_user_growth_last_7_days():
    cursor = get_db().cursor(dictionary=True)
    cursor.execute("""
        SELECT DATE(date_joined) as day, COUNT(*) as count
        FROM user_interest_group
        GROUP BY day
        ORDER BY day DESC
        LIMIT 7
    """)
    return cursor.fetchall()[::-1]  # reverse for Chart.js order

#admin dashboard end

def get_group_member_count(group_id):
    connection = get_db()
    cursor = connection.cursor()
    query = """
        SELECT COUNT(*) FROM user_interest_group
        WHERE group_id = %s AND status_id = 2
    """
    cursor.execute(query, (group_id,))
    (count,) = cursor.fetchone()
    return count

def register_user_for_activity(user_id, activity_id):
    connection = get_db()
    cursor = connection.cursor()

    query = """
        INSERT INTO user_interest_activity (user_id, activity_id, join_datetime)
        VALUES (%s, %s, NOW())
        ON DUPLICATE KEY UPDATE join_datetime = VALUES(join_datetime)
    """
    cursor.execute(query, (user_id, activity_id))
    connection.commit()

def is_user_registered_for_activity(user_id, activity_id):
    connection = get_db()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT user_id, activity_id, join_datetime FROM user_interest_activity
        WHERE user_id = %s AND activity_id = %s
    """
    cursor.execute(query, (user_id, activity_id))
    return cursor.fetchone() is not None

def get_activity_registration_count(activity_id):
    connection = get_db()
    cursor = connection.cursor()

    query = """
        SELECT COUNT(*) FROM user_interest_activity
        WHERE activity_id = %s
    """
    cursor.execute(query, (activity_id,))
    result = cursor.fetchone()
    return result[0] if result else 0

def leave_group(user_id, group_id):
    connection = get_db()
    cursor = connection.cursor()

    statement = """
        DELETE FROM user_interest_group
        WHERE user_id = %s AND group_id = %s
    """
    cursor.execute(statement, (user_id, group_id))
    connection.commit()

def get_user_group_status_id(user_id, group_id):
    connection = get_db()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT status_id
        FROM user_interest_group
        WHERE user_id = %s AND group_id = %s
    """
    cursor.execute(query, (user_id, group_id))
    result = cursor.fetchone()

    return result['status_id'] if result else None
