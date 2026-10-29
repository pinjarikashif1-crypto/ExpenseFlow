from datetime import date
from decimal import Decimal, InvalidOperation

from flask import (
    Flask, jsonify, request, render_template,
    redirect, url_for, session
)
from database import get_connection
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(
    __name__,
    template_folder="../FRONTEND",
    static_folder="../FRONTEND",
    static_url_path="/static"
)

# For a public deployment, use a strong secret stored in an environment variable.
app.secret_key = "expenseflow-secret-key-change-this"


# ==================================================
# HELPER FUNCTIONS
# ==================================================

def login_required():
    return "user_id" in session


def api_error(message, status=400):
    return jsonify({"error": message}), status


def parse_amount(value):
    try:
        amount = Decimal(str(value))

        if not amount.is_finite() or amount <= 0:
            return None

        return amount

    except (InvalidOperation, TypeError, ValueError):
        return None


def parse_transaction_date(value):
    if not isinstance(value, str):
        return None

    try:
        parsed_date = date.fromisoformat(value)

        if parsed_date.isoformat() != value:
            return None

        return parsed_date

    except ValueError:
        return None


def validate_transaction(data):
    title = str(data.get("title", "")).strip()
    amount = parse_amount(data.get("amount"))
    transaction_type = data.get("type")
    category = str(data.get("category", "")).strip()
    transaction_date = parse_transaction_date(
        data.get("transaction_date")
    )

    if not title:
        return None, "Please enter a transaction title."

    if amount is None:
        return None, "Amount must be greater than zero."

    if transaction_type not in ("income", "expense"):
        return None, "Please select a valid transaction type."

    if not category:
        return None, "Please select a category."

    if transaction_date is None:
        return None, "Please select a valid transaction date."

    # Do not allow future transaction dates.
    if transaction_date > date.today():
        return None, (
            "Future dates are not allowed. "
            "Please select today or an earlier date."
        )

    return {
        "title": title,
        "amount": amount,
        "type": transaction_type,
        "category": category,
        "transaction_date": transaction_date
    }, None


def get_user_balance(cursor, user_id):
    cursor.execute(
        """
        SELECT COALESCE(
            SUM(
                CASE
                    WHEN type = 'income' THEN amount
                    WHEN type = 'expense' THEN -amount
                    ELSE 0
                END
            ), 0
        ) AS balance
        FROM transactions
        WHERE user_id = %s
        """,
        (user_id,)
    )

    result = cursor.fetchone()
    return Decimal(str(result["balance"] or 0))


# ==================================================
# HOME PAGE
# ==================================================

@app.route("/")
def home():
    if not login_required():
        return redirect(url_for("login"))

    return render_template("index.html")


# ==================================================
# REGISTER
# ==================================================

@app.route("/register")
def register_page():
    return render_template("register.html")


@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}

    full_name = str(data.get("full_name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = data.get("password", "")

    if not full_name or not email or not password:
        return api_error("All fields are required.")

    if not isinstance(password, str) or len(password) < 6:
        return api_error("Password must be at least 6 characters.")

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT id FROM users WHERE email = %s",
            (email,)
        )

        if cursor.fetchone():
            return api_error("Email already registered.", 409)

        hashed_password = generate_password_hash(password)

        cursor.execute(
            """
            INSERT INTO users (full_name, email, password)
            VALUES (%s, %s, %s)
            """,
            (full_name, email, hashed_password)
        )

        conn.commit()

        return jsonify({
            "message": "Registration successful."
        }), 201

    except Exception:
        if conn:
            conn.rollback()

        app.logger.exception("Registration error")
        return api_error("Unable to register. Please try again.", 500)

    finally:
        if cursor:
            cursor.close()

        if conn:
            conn.close()


# ==================================================
# LOGIN
# ==================================================

@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/api/login", methods=["POST"])
def login_api():
    data = request.get_json(silent=True) or {}

    email = str(data.get("email", "")).strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return api_error("Email and password are required.")

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, full_name, email, password
            FROM users
            WHERE email = %s
            """,
            (email,)
        )

        user = cursor.fetchone()

        if (
            not user
            or not check_password_hash(user["password"], password)
        ):
            return api_error("Invalid email or password.", 401)

        session["user_id"] = user["id"]
        session["full_name"] = user["full_name"]
        session["email"] = user["email"]

        return jsonify({"message": "Login successful."})

    except Exception:
        app.logger.exception("Login error")
        return api_error("Unable to log in. Please try again.", 500)

    finally:
        if cursor:
            cursor.close()

        if conn:
            conn.close()


# ==================================================
# LOGOUT
# ==================================================

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ==================================================
# CURRENT USER
# ==================================================

@app.route("/api/current-user")
def current_user():
    if not login_required():
        return api_error("Please login first.", 401)

    return jsonify({
        "id": session["user_id"],
        "full_name": session.get("full_name", ""),
        "email": session.get("email", "")
    })


# ==================================================
# DASHBOARD SUMMARY
# ==================================================

@app.route("/api/summary")
def summary():
    if not login_required():
        return api_error("Please login first.", 401)

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                COALESCE(
                    SUM(CASE WHEN type = 'income'
                        THEN amount ELSE 0 END), 0
                ) AS income,
                COALESCE(
                    SUM(CASE WHEN type = 'expense'
                        THEN amount ELSE 0 END), 0
                ) AS expense
            FROM transactions
            WHERE user_id = %s
            """,
            (session["user_id"],)
        )

        data = cursor.fetchone()

        income = float(data["income"])
        expense = float(data["expense"])

        return jsonify({
            "income": income,
            "expense": expense,
            "balance": income - expense
        })

    except Exception:
        app.logger.exception("Summary error")
        return api_error("Unable to load dashboard summary.", 500)

    finally:
        if cursor:
            cursor.close()

        if conn:
            conn.close()


# ==================================================
# GET ALL TRANSACTIONS
# ==================================================

@app.route("/api/transactions", methods=["GET"])
def get_transactions():
    if not login_required():
        return api_error("Please login first.", 401)

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                id, title, amount, type, category, transaction_date
            FROM transactions
            WHERE user_id = %s
            ORDER BY transaction_date DESC, id DESC
            """,
            (session["user_id"],)
        )

        transactions = cursor.fetchall()

        for transaction in transactions:
            transaction["amount"] = float(transaction["amount"])
            transaction["transaction_date"] = str(
                transaction["transaction_date"]
            )

        return jsonify(transactions)

    except Exception:
        app.logger.exception("Get transactions error")
        return api_error("Unable to load transactions.", 500)

    finally:
        if cursor:
            cursor.close()

        if conn:
            conn.close()


# ==================================================
# ADD TRANSACTION
# ==================================================

@app.route("/api/transactions", methods=["POST"])
def add_transaction():
    if not login_required():
        return api_error("Please login first.", 401)

    data = request.get_json(silent=True) or {}

    transaction, error = validate_transaction(data)

    if error:
        return api_error(error, 400)

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Lock the user's row to prevent simultaneous expense requests
        # from spending the same balance. This relies on InnoDB tables.
        cursor.execute(
            "SELECT id FROM users WHERE id = %s FOR UPDATE",
            (session["user_id"],)
        )

        if not cursor.fetchone():
            conn.rollback()
            return api_error("User account not found.", 401)

        if transaction["type"] == "expense":
            balance = get_user_balance(cursor, session["user_id"])

            if transaction["amount"] > balance:
                conn.rollback()

                return api_error(
                    "Insufficient balance! Available balance: "
                    f"₹{balance:.2f}",
                    400
                )

        cursor.execute(
            """
            INSERT INTO transactions
                (user_id, title, amount, type, category, transaction_date)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                session["user_id"],
                transaction["title"],
                str(transaction["amount"]),
                transaction["type"],
                transaction["category"],
                transaction["transaction_date"].isoformat()
            )
        )

        conn.commit()

        return jsonify({
            "message": "Transaction added successfully."
        }), 201

    except Exception:
        if conn:
            conn.rollback()

        app.logger.exception("Add transaction error")
        return api_error("Unable to save transaction. Please try again.", 500)

    finally:
        if cursor:
            cursor.close()

        if conn:
            conn.close()


# ==================================================
# EDIT TRANSACTION
# ==================================================

@app.route("/api/transactions/<int:transaction_id>", methods=["PUT"])
def update_transaction(transaction_id):
    if not login_required():
        return api_error("Please login first.", 401)

    data = request.get_json(silent=True) or {}

    transaction, error = validate_transaction(data)

    if error:
        return api_error(error, 400)

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT id FROM users WHERE id = %s FOR UPDATE",
            (session["user_id"],)
        )

        if not cursor.fetchone():
            conn.rollback()
            return api_error("User account not found.", 401)

        cursor.execute(
            """
            SELECT id, amount, type
            FROM transactions
            WHERE id = %s AND user_id = %s
            FOR UPDATE
            """,
            (transaction_id, session["user_id"])
        )

        old_transaction = cursor.fetchone()

        if not old_transaction:
            conn.rollback()
            return api_error("Transaction not found.", 404)

        if transaction["type"] == "expense":
            balance = get_user_balance(cursor, session["user_id"])

            # When editing an existing expense, add its old amount back
            # before checking the replacement amount.
            if old_transaction["type"] == "expense":
                balance += Decimal(str(old_transaction["amount"]))

            if transaction["amount"] > balance:
                conn.rollback()

                return api_error(
                    "Insufficient balance! Available balance for this edit: "
                    f"₹{balance:.2f}",
                    400
                )

        cursor.execute(
            """
            UPDATE transactions
            SET title = %s,
                amount = %s,
                type = %s,
                category = %s,
                transaction_date = %s
            WHERE id = %s AND user_id = %s
            """,
            (
                transaction["title"],
                str(transaction["amount"]),
                transaction["type"],
                transaction["category"],
                transaction["transaction_date"].isoformat(),
                transaction_id,
                session["user_id"]
            )
        )

        conn.commit()

        return jsonify({
            "message": "Transaction updated successfully."
        })

    except Exception:
        if conn:
            conn.rollback()

        app.logger.exception("Update transaction error")
        return api_error("Unable to update transaction. Please try again.", 500)

    finally:
        if cursor:
            cursor.close()

        if conn:
            conn.close()


# ==================================================
# DELETE TRANSACTION
# ==================================================

@app.route("/api/transactions/<int:transaction_id>", methods=["DELETE"])
def delete_transaction(transaction_id):
    if not login_required():
        return api_error("Please login first.", 401)

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM transactions
            WHERE id = %s AND user_id = %s
            """,
            (transaction_id, session["user_id"])
        )

        if cursor.rowcount == 0:
            conn.rollback()
            return api_error("Transaction not found.", 404)

        conn.commit()

        return jsonify({
            "message": "Transaction deleted successfully."
        })

    except Exception:
        if conn:
            conn.rollback()

        app.logger.exception("Delete transaction error")
        return api_error("Unable to delete transaction.", 500)

    finally:
        if cursor:
            cursor.close()

        if conn:
            conn.close()


# ==================================================
# MONTHLY ANALYSIS
# ==================================================

@app.route("/api/monthly-analysis")
def monthly_analysis():
    if not login_required():
        return api_error("Please login first.", 401)

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                DATE_FORMAT(transaction_date, '%Y-%m') AS month,
                COALESCE(
                    SUM(CASE WHEN type = 'income'
                        THEN amount ELSE 0 END), 0
                ) AS income,
                COALESCE(
                    SUM(CASE WHEN type = 'expense'
                        THEN amount ELSE 0 END), 0
                ) AS expense
            FROM transactions
            WHERE user_id = %s
            GROUP BY DATE_FORMAT(transaction_date, '%Y-%m')
            ORDER BY month ASC
            """,
            (session["user_id"],)
        )

        rows = cursor.fetchall()

        for row in rows:
            row["income"] = float(row["income"])
            row["expense"] = float(row["expense"])

        return jsonify(rows)

    except Exception:
        app.logger.exception("Monthly analysis error")
        return api_error("Unable to load monthly analysis.", 500)

    finally:
        if cursor:
            cursor.close()

        if conn:
            conn.close()


# ==================================================
# CATEGORY ANALYSIS
# ==================================================

@app.route("/api/category-analysis")
def category_analysis():
    if not login_required():
        return api_error("Please login first.", 401)

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                category,
                COALESCE(SUM(amount), 0) AS total
            FROM transactions
            WHERE type = 'expense' AND user_id = %s
            GROUP BY category
            ORDER BY total DESC
            """,
            (session["user_id"],)
        )

        rows = cursor.fetchall()

        for row in rows:
            row["total"] = float(row["total"])

        return jsonify(rows)

    except Exception:
        app.logger.exception("Category analysis error")
        return api_error("Unable to load category analysis.", 500)

    finally:
        if cursor:
            cursor.close()

        if conn:
            conn.close()


# ==================================================
# RUN APPLICATION
# ==================================================

if __name__ == "__main__":
    app.run(debug=True)