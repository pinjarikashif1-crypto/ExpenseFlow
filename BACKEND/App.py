from flask import Flask, jsonify, request, render_template
from database import get_connection

app = Flask(
    __name__,
    template_folder="../FRONTEND",
    static_folder="../FRONTEND",
    static_url_path="/static"
)


# =========================
# HOME
# =========================

@app.route("/")
def home():
    return render_template("index.html")


# =========================
# DASHBOARD SUMMARY
# =========================

@app.route("/api/summary")
def summary():

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            COALESCE(
                SUM(
                    CASE
                        WHEN type = 'income' THEN amount
                        ELSE 0
                    END
                ), 0
            ) AS income,

            COALESCE(
                SUM(
                    CASE
                        WHEN type = 'expense' THEN amount
                        ELSE 0
                    END
                ), 0
            ) AS expense

        FROM transactions
    """)

    data = cursor.fetchone()

    cursor.close()
    conn.close()

    income = float(data["income"])
    expense = float(data["expense"])

    return jsonify({
        "income": income,
        "expense": expense,
        "balance": income - expense
    })


# =========================
# GET ALL TRANSACTIONS
# =========================

@app.route("/api/transactions", methods=["GET"])
def get_transactions():

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            id,
            title,
            amount,
            type,
            category,
            transaction_date
        FROM transactions
        ORDER BY transaction_date DESC, id DESC
    """)

    transactions = cursor.fetchall()

    cursor.close()
    conn.close()

    for transaction in transactions:

        transaction["amount"] = float(
            transaction["amount"]
        )

        transaction["transaction_date"] = str(
            transaction["transaction_date"]
        )

    return jsonify(transactions)


# =========================
# ADD TRANSACTION
# =========================

@app.route("/api/transactions", methods=["POST"])
def add_transaction():

    data = request.get_json()

    title = data.get("title")
    amount = data.get("amount")
    transaction_type = data.get("type")
    category = data.get("category")
    transaction_date = data.get("transaction_date")

    if not title or not amount or not transaction_type or not category or not transaction_date:

        return jsonify({
            "error": "All fields are required"
        }), 400

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO transactions
        (
            title,
            amount,
            type,
            category,
            transaction_date
        )
        VALUES (%s, %s, %s, %s, %s)
    """, (
        title,
        amount,
        transaction_type,
        category,
        transaction_date
    ))

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({
        "message": "Transaction added successfully"
    }), 201


# =========================
# EDIT TRANSACTION
# =========================

@app.route("/api/transactions/<int:transaction_id>", methods=["PUT"])
def update_transaction(transaction_id):

    data = request.get_json()

    title = data.get("title")
    amount = data.get("amount")
    transaction_type = data.get("type")
    category = data.get("category")
    transaction_date = data.get("transaction_date")

    if not title or not amount or not transaction_type or not category or not transaction_date:

        return jsonify({
            "error": "All fields are required"
        }), 400

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE transactions

        SET
            title = %s,
            amount = %s,
            type = %s,
            category = %s,
            transaction_date = %s

        WHERE id = %s
    """, (
        title,
        amount,
        transaction_type,
        category,
        transaction_date,
        transaction_id
    ))

    conn.commit()

    if cursor.rowcount == 0:

        cursor.close()
        conn.close()

        return jsonify({
            "error": "Transaction not found"
        }), 404

    cursor.close()
    conn.close()

    return jsonify({
        "message": "Transaction updated successfully"
    })


# =========================
# DELETE TRANSACTION
# =========================

@app.route("/api/transactions/<int:transaction_id>", methods=["DELETE"])
def delete_transaction(transaction_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM transactions WHERE id = %s",
        (transaction_id,)
    )

    conn.commit()

    if cursor.rowcount == 0:

        cursor.close()
        conn.close()

        return jsonify({
            "error": "Transaction not found"
        }), 404

    cursor.close()
    conn.close()

    return jsonify({
        "message": "Transaction deleted successfully"
    })


# =========================
# MONTHLY ANALYSIS
# =========================

@app.route("/api/monthly-analysis", methods=["GET"])
def monthly_analysis():

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            DATE_FORMAT(transaction_date, '%Y-%m') AS month,

            COALESCE(
                SUM(
                    CASE
                        WHEN type = 'income' THEN amount
                        ELSE 0
                    END
                ), 0
            ) AS income,

            COALESCE(
                SUM(
                    CASE
                        WHEN type = 'expense' THEN amount
                        ELSE 0
                    END
                ), 0
            ) AS expense

        FROM transactions

        GROUP BY
            DATE_FORMAT(transaction_date, '%Y-%m')

        ORDER BY month ASC
    """)

    data = cursor.fetchall()

    cursor.close()
    conn.close()

    for row in data:

        row["income"] = float(row["income"])
        row["expense"] = float(row["expense"])

    return jsonify(data)


# =========================
# CATEGORY ANALYSIS
# =========================

@app.route("/api/category-analysis", methods=["GET"])
def category_analysis():

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            category,
            COALESCE(
                SUM(amount), 0
            ) AS total

        FROM transactions

        WHERE type = 'expense'

        GROUP BY category

        ORDER BY total DESC
    """)

    data = cursor.fetchall()

    cursor.close()
    conn.close()

    for row in data:

        row["total"] = float(row["total"])

    return jsonify(data)


# =========================
# RUN APPLICATION
# =========================

if __name__ == "__main__":
    app.run(debug=True)