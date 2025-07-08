import os
import mysql.connector
from flask import g, current_app

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