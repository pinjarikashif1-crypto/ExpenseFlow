from flask import Flask, jsonify, request, render_template, redirect, url_for, session
from database import get_connection
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(
    __name__,
    template_folder="../FRONTEND",
    static_folder="../FRONTEND",
    static_url_path="/static"
)

app.secret_key = "expenseflow-secret-key-change-this"


# =========================
# LOGIN REQUIRED
# =========================

def login_required():
    return "user_id" in session


# =========================
# HOME / LOGIN
# =========================

@app.route("/")
def home():

    if not login_required():
        return redirect(url_for("login"))

    return render_template("index.html")


# =========================
# REGISTER PAGE
# =========================

@app.route("/register")
def register_page():
    return render_template("register.html")


# =========================
# REGISTER API
# =========================

@app.route("/api/register", methods=["POST"])
def register():

    data = request.get_json()

    full_name = data.get("full_name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not full_name or not email or not password:
        return jsonify({
            "error": "All fields are required"
        }), 400

    if len(password) < 6:
        return jsonify({
            "error": "Password must be at least 6 characters"
        }), 400

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT id FROM users WHERE email = %s",
        (email,)
    )

    existing_user = cursor.fetchone()

    if existing_user:

        cursor.close()
        conn.close()

        return jsonify({
            "error": "Email already registered"
        }), 409

    hashed_password = generate_password_hash(password)

    cursor.execute("""
        INSERT INTO users
        (full_name, email, password)
        VALUES (%s, %s, %s)
    """, (
        full_name,
        email,
        hashed_password
    ))

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({
        "message": "Registration successful"
    }), 201


# =========================
# LOGIN PAGE
# =========================

@app.route("/login")
def login():
    return render_template("login.html")


# =========================
# LOGIN API
# =========================

@app.route("/api/login", methods=["POST"])
def login_api():

    data = request.get_json()

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:

        return jsonify({
            "error": "Email and password are required"
        }), 400

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            id,
            full_name,
            email,
            password
        FROM users
        WHERE email = %s
    """, (email,))

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if not user:

        return jsonify({
            "error": "Invalid email or password"
        }), 401

    if not check_password_hash(
        user["password"],
        password
    ):

        return jsonify({
            "error": "Invalid email or password"
        }), 401

    session["user_id"] = user["id"]
    session["full_name"] = user["full_name"]
    session["email"] = user["email"]

    return jsonify({
        "message": "Login successful"
    })


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# =========================
# CURRENT USER
# =========================

@app.route("/api/current-user")
def current_user():

    if not login_required():

        return jsonify({
            "error": "Unauthorized"
        }), 401

    return jsonify({
        "id": session["user_id"],
        "full_name": session["full_name"],
        "email": session["email"]
    })


# =========================
# DASHBOARD SUMMARY
# =========================

@app.route("/api/summary")
def summary():

    if not login_required():

        return jsonify({
            "error": "Unauthorized"
        }), 401

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT

            COALESCE(
                SUM(
                    CASE
                        WHEN type = 'income'
                        THEN amount
                        ELSE 0
                    END
                ),
                0
            ) AS income,

            COALESCE(
                SUM(
                    CASE
                        WHEN type = 'expense'
                        THEN amount
                        ELSE 0
                    END
                ),
                0
            ) AS expense

        FROM transactions

        WHERE user_id = %s
    """, (session["user_id"],))

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
# GET TRANSACTIONS
# =========================

@app.route("/api/transactions", methods=["GET"])
def get_transactions():

    if not login_required():

        return jsonify({
            "error": "Unauthorized"
        }), 401

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

        WHERE user_id = %s

        ORDER BY
            transaction_date DESC,
            id DESC
    """, (session["user_id"],))

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

    if not login_required():

        return jsonify({
            "error": "Unauthorized"
        }), 401

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

    try:
        amount = float(amount)

        if amount <= 0:
            raise ValueError

    except (ValueError, TypeError):

        return jsonify({
            "error": "Amount must be greater than 0"
        }), 400

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO transactions
        (
            user_id,
            title,
            amount,
            type,
            category,
            transaction_date
        )
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        session["user_id"],
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

    if not login_required():

        return jsonify({
            "error": "Unauthorized"
        }), 401

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

    try:
        amount = float(amount)

        if amount <= 0:
            raise ValueError

    except (ValueError, TypeError):

        return jsonify({
            "error": "Amount must be greater than 0"
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
        AND user_id = %s
    """, (
        title,
        amount,
        transaction_type,
        category,
        transaction_date,
        transaction_id,
        session["user_id"]
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

    if not login_required():

        return jsonify({
            "error": "Unauthorized"
        }), 401

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM transactions

        WHERE id = %s
        AND user_id = %s
    """, (
        transaction_id,
        session["user_id"]
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
        "message": "Transaction deleted successfully"
    })


# =========================
# MONTHLY ANALYSIS
# =========================

@app.route("/api/monthly-analysis", methods=["GET"])
def monthly_analysis():

    if not login_required():

        return jsonify({
            "error": "Unauthorized"
        }), 401

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT

            DATE_FORMAT(
                transaction_date,
                '%Y-%m'
            ) AS month,

            COALESCE(
                SUM(
                    CASE
                        WHEN type = 'income'
                        THEN amount
                        ELSE 0
                    END
                ),
                0
            ) AS income,

            COALESCE(
                SUM(
                    CASE
                        WHEN type = 'expense'
                        THEN amount
                        ELSE 0
                    END
                ),
                0
            ) AS expense

        FROM transactions

        WHERE user_id = %s

        GROUP BY
            DATE_FORMAT(
                transaction_date,
                '%Y-%m'
            )

        ORDER BY month ASC
    """, (session["user_id"],))

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

    if not login_required():

        return jsonify({
            "error": "Unauthorized"
        }), 401

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            category,
            COALESCE(
                SUM(amount),
                0
            ) AS total

        FROM transactions

        WHERE type = 'expense'
        AND user_id = %s

        GROUP BY category

        ORDER BY total DESC
    """, (session["user_id"],))

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