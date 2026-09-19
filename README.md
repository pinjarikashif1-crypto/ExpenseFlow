# ExpenseFlow – Personal Expense Tracker

ExpenseFlow is a simple Personal Expense Tracker and Budget Management System developed as a college project.

## Features

- Dashboard with Total Income, Total Expense and Current Balance
- Expense Overview chart
- Monthly Income vs Expense analysis
- Category-wise Expense analysis
- Add Transaction
- Edit Transaction
- Delete Transaction
- Recent Transactions table
- Search transactions
- Filter by Type
- Filter by Category
- MySQL database integration
- Flask REST API
- Responsive and clean user interface

## Technology Used

- HTML
- CSS
- JavaScript
- Python Flask
- MySQL
- Chart.js
- Git & GitHub

## Project Structure

```text
PERSONAL EXPENSE TRACKER
├── BACKEND
│   ├── App.py
│   └── database.py
├── DATABASE
│   └── schema.sql
├── FRONTEND
│   ├── index.html
│   ├── style.css
│   └── script.js
├── .gitignore
├── README.md
└── requirements.txt
```

## Database Setup

1. Open MySQL Workbench.
2. Open `DATABASE/schema.sql`.
3. Execute the complete SQL script.
4. This creates the `expense_tracker` database and `transactions` table.

## Python Setup

Open the project folder in VS Code terminal.

Install the required packages:

```bash
pip install -r requirements.txt
```

## MySQL Connection

Open:

```text
BACKEND/database.py
```

Enter your own MySQL password in the `password` field.

Do not upload your real MySQL password to GitHub.

## Run the Project

From the main project folder:

```bash
python .\BACKEND\App.py
```

Then open:

```text
http://127.0.0.1:5000
```

## Main API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/summary` | Dashboard totals |
| GET | `/api/transactions` | Get all transactions |
| POST | `/api/transactions` | Add transaction |
| PUT | `/api/transactions/<id>` | Edit transaction |
| DELETE | `/api/transactions/<id>` | Delete transaction |
| GET | `/api/monthly-analysis` | Monthly analysis |
| GET | `/api/category-analysis` | Category analysis |

## Project Objective

The objective of ExpenseFlow is to provide a simple web-based system for recording, managing and analysing personal income and expenses.

## Author

College Project – Personal Expense Tracker
