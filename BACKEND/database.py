import mysql.connector


def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="pinjari@2006",
        database="expense_tracker"
    )