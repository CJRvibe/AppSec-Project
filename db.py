import os
import mysql.connector
from flask import g, current_app

def get_db():
    if "db" not in g:
        g.db = mysql.connector.connect(
            host=os.getenv("SQL_HOST"),
            user=os.getenv("SQL_USER"),
            password=os.getenv("SQL_PASSWORD"),
            database="social_sage_db"
        )
    return g.db


def close_db(e=None):
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

def get_activities_by_group_id(group_id):
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    statement = "SELECT * FROM interest_activity WHERE group_id = %s"
    cursor.execute(statement, (group_id,))
    return cursor.fetchall()

def get_activity_by_id(activity_id):
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    statement = "SELECT * FROM interest_activity WHERE activity_id = %s"
    cursor.execute(statement, (activity_id,))
    return cursor.fetchone()
