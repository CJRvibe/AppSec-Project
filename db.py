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
    """Insert a new user without status_id"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO users (first_name, last_name, email, password, user_role, is_suspended) 
            VALUES (%s, %s, %s, %s, %s, %s)""",
        (first_name, last_name, email, password, user_role, 0)
    )
    conn.commit()
    return True


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
    """Get user by ID including suspension status"""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """SELECT user_id, first_name, last_name, email, user_role, 
                    is_suspended, mfa_enabled, email_notif, profile_pic
            FROM users WHERE user_id = %s""", 
        (user_id,)
    )
    user = cursor.fetchone()
    return user


def add_group_proposal(name, topic, description, max_size, is_public, activity_occurence, reason, owner, picture):
    connection = get_db()
    cursor = connection.cursor()
    values = (name, topic, description, max_size, is_public, activity_occurence, reason, owner, picture)
    statement = """
    INSERT INTO interest_group (name, topic, description, max_size, is_public,
        activity_occurence_id, proposal, status_id, owner, picture)
    VALUES (%s, %s, %s, %s, %s, %s, %s, 1, %s, %s)
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


def add_activity_proposal(name, description, start_datetime, end_datetime, max_size, funds, location, tags, remarks, group_id, picture):
    connection = get_db()
    cursor = connection.cursor()
    main_values = (name, description, start_datetime, end_datetime, max_size, funds, location, remarks, group_id, picture)

    main_statement = """
    INSERT INTO interest_activity (
        name, description, start_datetime, end_datetime, max_size, funds,
        location_code, remarks, status_id, group_id, picture
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1, %s, %s)
    """
    cursor.execute(main_statement, main_values)
    activity_id = cursor.lastrowid

    add_activity_tags(connection.cursor(), activity_id, tags)

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
        s.title status, u.email, ig.proposal, ig.owner, u.email owner_email
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
    elif type == "suspended": status_id = 6

    statement = """
    SELECT ig.group_id, ig.name, ig.topic, ig.max_size, ig.is_public, ig.owner, ac.title occurence
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
           ia.max_size, ia.funds, al.name location, ia.remarks, s.title status, ia.group_id
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
    statement = "SELECT * FROM user_interest_group WHERE user_id = %s AND group_id = %s AND status_id = 2"
    cursor.execute(statement, (user_id, group_id))
    if cursor.fetchone():
        return True 
    else:
        return False

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


def admin_join_group(user_id, group_id):
    connection = get_db()
    cursor = connection.cursor()
    
    status_id = 2

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


def admin_get_flagged_activities():
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    statement = """
    SELECT fa.flag_id, fa.activity_id, ia.name activity_name, fa.reason, fa.user_id, u.email, fa.status_id, ig.name group_name
    FROM flagged_activities fa
    INNER JOIN interest_activity ia ON fa.activity_id = ia.activity_id
    INNER JOIN interest_group ig ON ia.group_id = ig.group_id
    INNER JOIN users u ON fa.user_id = u.user_id
    """

    cursor.execute(statement)
    return cursor.fetchall()


def admin_get_flagged_groups():
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    statement = """
    SELECT fg.flag_id, fg.group_id, ig.name group_name, fg.reason, fg.user_id, u.email, fg.status_id
    FROM flagged_groups fg
    INNER JOIN interest_group ig ON fg.group_id = ig.group_id
    INNER JOIN users u ON fg.user_id = u.user_id
    """

    cursor.execute(statement)
    return cursor.fetchall()


def admin_get_flagged_group(id):
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    statement = """
    SELECT fg.flag_id, fg.group_id, fg.status_id, fg.user_id
    FROM flagged_groups fg
    INNER JOIN users u ON u.user_id = fg.user_id
    WHERE flag_id = %s
    """

    cursor.execute(statement, (id, ))
    return cursor.fetchone()


def admin_get_flagged_activity(id):
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    statement = """
    SELECT fa.flag_id, fa.activity_id, fa.status_id, fa.user_id
    FROM flagged_activities fa
    INNER JOIN users u ON u.user_id = fa.user_id
    WHERE flag_id = %s
    """

    cursor.execute(statement, (id, ))
    return cursor.fetchone()


def admin_update_group_flag_request(id, approved=False):
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    status = 2 if approved else 3
    statement = """
    UPDATE flagged_groups
    SET status_id = %s
    WHERE flag_id = %s
    """

    cursor.execute(statement, (status, id))
    connection.commit()


def admin_update_activity_flag_request(id, approved=False):
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    status = 2 if approved else 3
    statement = """
    UPDATE flagged_activities
    SET status_id = %s
    WHERE flag_id = %s
    """

    cursor.execute(statement, (status, id))
    connection.commit()

def admin_suspend_group(id):
    connection = get_db()
    cursor = connection.cursor()
    statement_1 = """
    UPDATE interest_group
    SET status_id = 6
    WHERE group_id = %s
    """
    
    statement_2 = """
    UPDATE interest_activity
    SET status_id = 6
    WHERE group_id = %s;
    """

    cursor.execute(statement_1, (id, ))
    cursor.execute(statement_2, (id, ))
    connection.commit()

def get_user_profile_pic(user_id):
    """Get user profile picture filename"""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT profile_pic FROM users WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    if result and result['profile_pic']:
        return result['profile_pic']
    else:
        return None
 
def update_user_profile_pic(user_id, profile_pic):
    """Update user profile picture filename"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET profile_pic = %s WHERE user_id = %s",
        (profile_pic, user_id)
    )
    conn.commit()
    if cursor.rowcount > 0:
        return True
    else:
        return False

def get_user_by_email(email):
    """Get user by email including suspension status"""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """SELECT user_id, first_name, last_name, email, user_role, 
                    is_suspended, mfa_enabled 
            FROM users WHERE email = %s""", 
        (email,)
    )
    user = cursor.fetchone()
    return user


def update_user_role(user_id, role):
    """Update user role and return success status"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET user_role = %s WHERE user_id = %s", (role, user_id))
    conn.commit()
    return cursor.rowcount > 0
        


def update_user_info(user_id, first_name, last_name, email):
    """Update user basic information"""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT first_name, last_name, email FROM users WHERE user_id = %s",
        (user_id,)
    )
    current_user = cursor.fetchone()
    
    if not current_user:
        return False
    
    # Check if any data has actually changed
    data_changed = (
        current_user['first_name'] != first_name or
        current_user['last_name'] != last_name or
        current_user['email'] != email
    )
    
    if not data_changed:
        return True
    
    cursor.execute(
        "UPDATE users SET first_name = %s, last_name = %s, email = %s WHERE user_id = %s",
        (first_name, last_name, email, user_id)
    )
    conn.commit()
    
    if cursor.rowcount > 0:
        return True
    else:
        return False



def get_all_users():
    """Get all users including suspension status"""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """SELECT user_id, first_name, last_name, email, user_role, 
                    is_suspended, mfa_enabled 
            FROM users"""
    )
    users = cursor.fetchall()
    return users

def get_users_by_role(role):
    """Get users by role including suspension status"""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """SELECT user_id, first_name, last_name, email, user_role, 
                    is_suspended, mfa_enabled 
            FROM users WHERE user_role = %s""", 
        (role,)
    )
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


def count_flag_group_request(user_id):
    connection = get_db()
    cursor = connection.cursor()
    statement = f"""
    SELECT COUNT(*)
    FROM flagged_groups
    WHERE user_id = %s AND status_id = 1
    """

    cursor.execute(statement, (user_id, ))
    return cursor.fetchone()[0]


def count_flag_activity_request(user_id):
    connection = get_db()
    cursor = connection.cursor()
    statement = f"""
    SELECT COUNT(*)
    FROM flagged_activities
    WHERE user_id = %s AND status_id = 1
    """

    cursor.execute(statement, (user_id, ))
    return cursor.fetchone()[0]


def add_flag_group(group_id, user_id, reason):
    connection = get_db()
    cursor = connection.cursor()

    statement = """
    INSERT INTO flagged_groups (group_id, user_id, status_id, reason)
    VALUES (%s, %s, 1, %s)
    """

    cursor.execute(statement, (group_id, user_id, reason))
    connection.commit()


def add_flag_activity(activity_id, user_id, reason):
    connection = get_db()
    cursor = connection.cursor()

    statement = """
    INSERT INTO flagged_activities (activity_id, user_id, status_id, reason)
    VALUES (%s, %s, 1, %s)
    """

    cursor.execute(statement, (activity_id, user_id, reason))
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

def update_user_suspension_status(user_id, is_suspended):
    """Update user suspension status (0 = active, 1 = suspended)"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET is_suspended = %s WHERE user_id = %s",
        (is_suspended, user_id)
    )
    conn.commit()
        
    cursor.execute("SELECT is_suspended FROM users WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
        
def get_user_suspension_status(user_id):
    """Get user suspension status directly"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT is_suspended FROM users WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    suspension_status = result[0] if result else False
    return suspension_status

def is_mfa_properly_setup(user_id):
    """Check if MFA is properly configured with a secret"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT mfa_secret FROM users WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    return result and result[0] is not None and result[0] != ''

def disable_user_mfa(user_id):
    """Disable MFA and clear the secret for security"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET mfa_enabled = 0, mfa_secret = NULL WHERE user_id = %s", (user_id,))
    conn.commit()
    return True

def reject_user(user_id, group_id):
    connection = get_db()
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM user_interest_group WHERE user_id = %s AND group_id = %s AND status_id = 1",
        (user_id, group_id)
    )
    connection.commit()

def get_activity_status(activity_id):
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    
    query = "SELECT status_id FROM interest_activity WHERE activity_id = %s"
    cursor.execute(query, (activity_id,))
    result = cursor.fetchone()
    
    return result['status_id'] if result else None

def get_group_status(activity_id):
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    
    query = """
        SELECT ig.status_id
        FROM interest_activity ia
        INNER JOIN interest_group ig ON ia.group_id = ig.group_id
        WHERE ia.activity_id = %s
    """
    cursor.execute(query, (activity_id,))
    result = cursor.fetchone()
    
    return result['status_id'] if result else None

def is_root_admin(user_id):
    """Check if user is the root admin (admin@gmail.com)"""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT email FROM users WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    return result and result['email'] == 'admin@gmail.com'

def is_root_admin_by_email(email):
    """Check if email is the root admin"""
    return email == 'admin@gmail.com'

def can_suspend_user(admin_user_id, target_user_id):
    """Check if admin can suspend the target user"""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    # Get admin info
    cursor.execute("SELECT email, user_role FROM users WHERE user_id = %s", (admin_user_id,))
    admin = cursor.fetchone()
    
    # Get target user info
    cursor.execute("SELECT email, user_role FROM users WHERE user_id = %s", (target_user_id,))
    target = cursor.fetchone()
    
    if not admin or not target:
        return False
    
    # Root admin can suspend anyone except themselves
    if admin['email'] == 'admin@gmail.com':
        return target['email'] != 'admin@gmail.com'
    
    # Regular admins can only suspend non-admin users (roles 1 and 2)
    if admin['user_role'] == 3:
        return target['user_role'] in [1, 2]
    
    return False

def verify_user_password(user_id, password):
    """Verify if the provided password matches the user's current password"""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT password FROM users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    if user and check_password_hash(user['password'], password):
        return True
    return False

def update_user_password_by_id(user_id, new_hashed_password):
    """Update user password by user ID"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET password = %s WHERE user_id = %s",
        (new_hashed_password, user_id)
    )
    conn.commit()
    return cursor.rowcount > 0


def check_email_exists_for_other_user(email, user_id):
    """Check if email exists for a different user"""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT user_id FROM users WHERE email = %s AND user_id != %s", (email, user_id))
    result = cursor.fetchone()
    return result is not None

def enable_user_email_notif(user_id):
    """Enable email notifications for user"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET email_notif = 1 WHERE user_id = %s", (user_id,))
    conn.commit()

def disable_user_email_notif(user_id):
    """Disable email notifications for user"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET email_notif = 0 WHERE user_id = %s", (user_id,))
    conn.commit()

def is_user_email_notif_enabled(user_id):
    """Check if user has email notifications enabled"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT email_notif FROM users WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    is_enabled = bool(result[0]) if result else True  # Default to enabled
    return is_enabled

def get_user_notification_status(user_id):
    """Get user's email notification preference (returns 1 for enabled, 0 for disabled)"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT email_notif FROM users WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    notification_status = result[0] if result else 1  # Default to enabled (1) if not found
    return notification_status

def update_user_notification_status(user_id, enabled):
    """Update user's email notification preference (enabled=True sets to 1, enabled=False sets to 0)"""
    conn = get_db()
    cursor = conn.cursor()
    new_value = 1 if enabled else 0
    
    cursor.execute(
        "UPDATE users SET email_notif = %s WHERE user_id = %s",
        (new_value, user_id)
    )
    conn.commit()
    
    return True  # Always return True if no exception occurred