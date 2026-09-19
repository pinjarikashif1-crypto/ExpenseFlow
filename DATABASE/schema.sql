CREATE DATABASE IF NOT EXISTS expense_tracker;

USE expense_tracker;

CREATE TABLE IF NOT EXISTS transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    type ENUM('income', 'expense') NOT NULL,
    category VARCHAR(50) NOT NULL,
    transaction_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO transactions
(title, amount, type, category, transaction_date)
VALUES
('Monthly Salary', 25000, 'income', 'Salary', '2026-09-01'),
('Food', 500, 'expense', 'Food', '2026-09-05'),
('Travel', 1000, 'expense', 'Travel', '2026-09-07'),
('Shopping', 1500, 'expense', 'Shopping', '2026-09-10');