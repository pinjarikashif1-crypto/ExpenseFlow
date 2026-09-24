let expenseChart = null;
let monthlyChart = null;
let categoryChart = null;

let allTransactions = [];
let editingTransactionId = null;


// =========================
// FORMAT MONEY
// =========================

function formatMoney(amount) {
    return "₹" + Number(amount).toLocaleString("en-IN", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}


// =========================
// LOAD DASHBOARD SUMMARY
// =========================

async function loadSummary() {

    try {

        const response = await fetch("/api/summary");
        const data = await response.json();

        document.getElementById("totalIncome").textContent =
            formatMoney(data.income);

        document.getElementById("totalExpense").textContent =
            formatMoney(data.expense);

        document.getElementById("totalBalance").textContent =
            formatMoney(data.balance);

        document.getElementById("quickIncome").textContent =
            formatMoney(data.income);

        document.getElementById("quickExpense").textContent =
            formatMoney(data.expense);

        document.getElementById("quickBalance").textContent =
            formatMoney(data.balance);

        const message = document.getElementById("balanceMessage");

        if (data.balance > 0) {
            message.textContent = "Your current balance is positive.";
        }
        else if (data.balance < 0) {
            message.textContent =
                "Your expenses are higher than your income.";
        }
        else {
            message.textContent =
                "Your income and expenses are equal.";
        }

        updateChart(data);

    }
    catch (error) {
        console.error("Summary error:", error);
    }
}


// =========================
// EXPENSE OVERVIEW CHART
// =========================

function updateChart(data) {

    const ctx = document.getElementById("expenseChart");

    if (expenseChart) {
        expenseChart.destroy();
    }

    expenseChart = new Chart(ctx, {

        type: "doughnut",

        data: {

            labels: [
                "Income",
                "Expense"
            ],

            datasets: [{

                data: [
                    data.income,
                    data.expense
                ],

                backgroundColor: [
                    "#16a34a",
                    "#dc2626"
                ],

                borderWidth: 0

            }]

        },

        options: {

            responsive: true,
            maintainAspectRatio: false,

            plugins: {

                legend: {
                    position: "bottom"
                }

            }

        }

    });
}


// =========================
// MONTHLY ANALYSIS
// =========================

async function loadMonthlyAnalysis() {

    try {

        const response =
            await fetch("/api/monthly-analysis");

        const data =
            await response.json();

        const labels =
            data.map(item => item.month);

        const incomeData =
            data.map(item => item.income);

        const expenseData =
            data.map(item => item.expense);

        const ctx =
            document.getElementById("monthlyChart");

        if (monthlyChart) {
            monthlyChart.destroy();
        }

        monthlyChart = new Chart(ctx, {

            type: "bar",

            data: {

                labels: labels,

                datasets: [

                    {
                        label: "Income",
                        data: incomeData,
                        backgroundColor: "#16a34a"
                    },

                    {
                        label: "Expense",
                        data: expenseData,
                        backgroundColor: "#dc2626"
                    }

                ]

            },

            options: {

                responsive: true,
                maintainAspectRatio: false,

                scales: {

                    y: {
                        beginAtZero: true
                    }

                },

                plugins: {

                    legend: {
                        position: "bottom"
                    }

                }

            }

        });

    }
    catch (error) {

        console.error(
            "Monthly analysis error:",
            error
        );

    }

}


// =========================
// CATEGORY ANALYSIS
// =========================

async function loadCategoryAnalysis() {

    try {

        const response =
            await fetch("/api/category-analysis");

        const data =
            await response.json();

        const labels =
            data.map(item => item.category);

        const values =
            data.map(item => item.total);

        const ctx =
            document.getElementById("categoryChart");

        if (categoryChart) {
            categoryChart.destroy();
        }

        categoryChart = new Chart(ctx, {

            type: "doughnut",

            data: {

                labels: labels,

                datasets: [{

                    label: "Expenses",

                    data: values,

                    backgroundColor: [
                        "#2563eb",
                        "#16a34a",
                        "#dc2626",
                        "#f59e0b",
                        "#7c3aed",
                        "#0891b2",
                        "#db2777",
                        "#65a30d",
                        "#64748b"
                    ],

                    borderWidth: 0

                }]

            },

            options: {

                responsive: true,
                maintainAspectRatio: false,

                plugins: {

                    legend: {
                        position: "bottom"
                    }

                }

            }

        });

    }
    catch (error) {

        console.error(
            "Category analysis error:",
            error
        );

    }

}


// =========================
// LOAD TRANSACTIONS
// =========================

async function loadTransactions() {

    const table =
        document.getElementById("transactionTable");

    try {

        const response =
            await fetch("/api/transactions");

        allTransactions =
            await response.json();

        filterTransactions();

    }
    catch (error) {

        console.error(
            "Transaction error:",
            error
        );

        table.innerHTML = `

            <tr>

                <td
                    colspan="6"
                    class="empty-row"
                >
                    Unable to load transactions.
                </td>

            </tr>

        `;

    }

}


// =========================
// DISPLAY TRANSACTIONS
// =========================

function displayTransactions(transactions) {

    const table =
        document.getElementById("transactionTable");

    table.innerHTML = "";

    if (transactions.length === 0) {

        table.innerHTML = `

            <tr>

                <td
                    colspan="6"
                    class="empty-row"
                >
                    No transactions found.
                </td>

            </tr>

        `;

        return;
    }

    transactions.forEach(transaction => {

        const row =
            document.createElement("tr");

        const amountClass =
            transaction.type === "income"
                ? "income-text"
                : "expense-text";

        const amountSign =
            transaction.type === "income"
                ? "+"
                : "-";

        const badgeClass =
            transaction.type === "income"
                ? "income-badge"
                : "expense-badge";


        let receiptButton = "";

        if (transaction.type === "expense") {

            receiptButton = `

                <button
                    class="refresh-btn"
                    onclick="downloadReceipt(${transaction.id})"
                >
                    Receipt
                </button>

            `;

        }


        row.innerHTML = `

            <td>
                <strong>
                    ${escapeHTML(transaction.title)}
                </strong>
            </td>

            <td>
                ${escapeHTML(transaction.category)}
            </td>

            <td>

                <span
                    class="type-badge ${badgeClass}"
                >
                    ${escapeHTML(transaction.type)}
                </span>

            </td>

            <td class="${amountClass}">

                ${amountSign}${formatMoney(
                    transaction.amount
                )}

            </td>

            <td>
                ${transaction.transaction_date}
            </td>

            <td>

                <button
                    class="refresh-btn"
                    onclick="editTransaction(${transaction.id})"
                >
                    Edit
                </button>

                <button
                    class="delete-btn"
                    onclick="deleteTransaction(${transaction.id})"
                >
                    Delete
                </button>

                ${receiptButton}

            </td>

        `;

        table.appendChild(row);

    });

}


// =========================
// SEARCH + FILTER
// =========================

function filterTransactions() {

    const search =
        document
            .getElementById("searchInput")
            .value
            .toLowerCase()
            .trim();

    const type =
        document.getElementById("typeFilter").value;

    const category =
        document.getElementById("categoryFilter").value;

    const filtered =
        allTransactions.filter(transaction => {

            const matchesSearch =

                transaction.title
                    .toLowerCase()
                    .includes(search)

                ||

                transaction.category
                    .toLowerCase()
                    .includes(search);

            const matchesType =
                type === "all" ||
                transaction.type === type;

            const matchesCategory =
                category === "all" ||
                transaction.category === category;

            return (
                matchesSearch &&
                matchesType &&
                matchesCategory
            );

        });

    displayTransactions(filtered);

}


// =========================
// EDIT TRANSACTION
// =========================

function editTransaction(id) {

    const transaction =
        allTransactions.find(
            item => item.id === id
        );

    if (!transaction) {

        alert("Transaction not found.");

        return;
    }

    editingTransactionId = id;

    document.getElementById("title").value =
        transaction.title;

    document.getElementById("amount").value =
        transaction.amount;

    document.getElementById("type").value =
        transaction.type;

    document.getElementById("category").value =
        transaction.category;

    document.getElementById("transaction_date").value =
        transaction.transaction_date;

    document.getElementById("formTitle").textContent =
        "Edit Transaction";

    document.getElementById("formSubtitle").textContent =
        "Update your income or expense";

    document.getElementById("submitBtn").textContent =
        "Update Transaction";

    document.getElementById("cancelEditBtn").style.display =
        "inline-block";

    document.getElementById("formMessage").textContent =
        "";

    document
        .getElementById("add-section")
        .scrollIntoView({
            behavior: "smooth"
        });

}


// =========================
// CANCEL EDIT
// =========================

function cancelEdit() {

    editingTransactionId = null;

    document
        .getElementById("transactionForm")
        .reset();

    document.getElementById("formTitle").textContent =
        "Add Transaction";

    document.getElementById("formSubtitle").textContent =
        "Record your income or expense";

    document.getElementById("submitBtn").textContent =
        "Add Transaction";

    document.getElementById("cancelEditBtn").style.display =
        "none";

    document.getElementById("formMessage").textContent =
        "";

    setToday();

}


// =========================
// ADD / UPDATE TRANSACTION
// =========================

document
    .getElementById("transactionForm")
    .addEventListener(
        "submit",
        async function(event) {

            event.preventDefault();

            const title =
                document.getElementById("title")
                    .value
                    .trim();

            const amount =
                document.getElementById("amount")
                    .value;

            const type =
                document.getElementById("type")
                    .value;

            const category =
                document.getElementById("category")
                    .value;

            const transaction_date =
                document
                    .getElementById("transaction_date")
                    .value;

            const message =
                document.getElementById(
                    "formMessage"
                );

            try {

                let response;

                if (editingTransactionId !== null) {

                    response = await fetch(

                        `/api/transactions/${editingTransactionId}`,

                        {

                            method: "PUT",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body: JSON.stringify({

                                title,
                                amount,
                                type,
                                category,
                                transaction_date

                            })

                        }

                    );

                }

                else {

                    response = await fetch(

                        "/api/transactions",

                        {

                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body: JSON.stringify({

                                title,
                                amount,
                                type,
                                category,
                                transaction_date

                            })

                        }

                    );

                }

                const data =
                    await response.json();

                if (!response.ok) {

                    message.textContent =
                        data.error ||
                        "Something went wrong.";

                    message.style.color =
                        "#dc2626";

                    return;
                }

                if (editingTransactionId !== null) {

                    message.textContent =
                        "Transaction updated successfully!";

                }
                else {

                    message.textContent =
                        "Transaction added successfully!";

                }

                message.style.color =
                    "#15803d";

                editingTransactionId = null;

                document
                    .getElementById("transactionForm")
                    .reset();

                document.getElementById("formTitle")
                    .textContent =
                    "Add Transaction";

                document.getElementById("formSubtitle")
                    .textContent =
                    "Record your income or expense";

                document.getElementById("submitBtn")
                    .textContent =
                    "Add Transaction";

                document.getElementById("cancelEditBtn")
                    .style.display =
                    "none";

                setToday();

                await loadSummary();
                await loadTransactions();
                await loadMonthlyAnalysis();
                await loadCategoryAnalysis();

            }
            catch (error) {

                console.error(error);

                message.textContent =
                    "Server error. Please try again.";

                message.style.color =
                    "#dc2626";

            }

        }
    );


// =========================
// DELETE TRANSACTION
// =========================

async function deleteTransaction(id) {

    const confirmed =
        confirm(
            "Are you sure you want to delete this transaction?"
        );

    if (!confirmed) {
        return;
    }

    try {

        const response =
            await fetch(
                `/api/transactions/${id}`,
                {
                    method: "DELETE"
                }
            );

        if (response.ok) {

            await loadSummary();
            await loadTransactions();
            await loadMonthlyAnalysis();
            await loadCategoryAnalysis();

        }
        else {

            alert(
                "Unable to delete transaction."
            );

        }

    }
    catch (error) {

        console.error(error);

        alert("Server error.");

    }

}


// =====================================================
// DOWNLOAD TRANSACTION REPORT
// =====================================================

function downloadReport() {

    if (allTransactions.length === 0) {

        alert("No transactions available for download.");

        return;
    }

    let csv = "";

    csv += "ExpenseFlow - Transaction Report\n";
    csv += "Title,Category,Type,Amount,Date\n";


    allTransactions.forEach(transaction => {

        const title =
            String(transaction.title)
                .replaceAll('"', '""');

        const category =
            String(transaction.category)
                .replaceAll('"', '""');

        const type =
            String(transaction.type);

        const amount =
            Number(transaction.amount).toFixed(2);

        const date =
            transaction.transaction_date;


        csv += `"${title}","${category}","${type}","${amount}","${date}"\n`;

    });


    const blob =
        new Blob(
            [csv],
            {
                type: "text/csv;charset=utf-8;"
            }
        );


    const url =
        URL.createObjectURL(blob);


    const link =
        document.createElement("a");

    link.href = url;

    link.download =
        "ExpenseFlow_Transaction_Report.csv";


    document.body.appendChild(link);

    link.click();

    document.body.removeChild(link);

    URL.revokeObjectURL(url);

}


// =====================================================
// DOWNLOAD EXPENSE RECEIPT
// =====================================================

function downloadReceipt(id) {

    const transaction =
        allTransactions.find(
            item => item.id === id
        );


    if (!transaction) {

        alert("Transaction not found.");

        return;
    }


    if (transaction.type !== "expense") {

        alert("Receipt is available only for expenses.");

        return;
    }


    const amount =
        formatMoney(transaction.amount);


    const receiptHTML = `

<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<title>Expense Receipt - ExpenseFlow</title>

<style>

body {

    font-family: Arial, sans-serif;

    background: #f3f4f6;

    padding: 30px;

}

.receipt {

    max-width: 500px;

    margin: auto;

    background: white;

    padding: 30px;

    border-radius: 12px;

    box-shadow: 0 5px 20px rgba(0,0,0,0.10);

}

.header {

    text-align: center;

    border-bottom: 2px solid #e5e7eb;

    padding-bottom: 15px;

    margin-bottom: 20px;

}

.header h1 {

    margin: 0;

    color: #111827;

}

.header p {

    margin: 5px 0;

    color: #6b7280;

}

.row {

    display: flex;

    justify-content: space-between;

    padding: 12px 0;

    border-bottom: 1px solid #e5e7eb;

}

.label {

    color: #6b7280;

}

.value {

    font-weight: bold;

    color: #111827;

}

.amount {

    color: #dc2626;

    font-size: 22px;

}

.footer {

    text-align: center;

    margin-top: 25px;

    color: #6b7280;

    font-size: 13px;

}

</style>

</head>

<body>

<div class="receipt">

    <div class="header">

        <h1>ExpenseFlow</h1>

        <p>Personal Expense Tracker</p>

        <p><strong>Expense Receipt</strong></p>

    </div>


    <div class="row">

        <span class="label">Transaction ID</span>

        <span class="value">
            ${transaction.id}
        </span>

    </div>


    <div class="row">

        <span class="label">Title</span>

        <span class="value">
            ${escapeHTML(transaction.title)}
        </span>

    </div>


    <div class="row">

        <span class="label">Category</span>

        <span class="value">
            ${escapeHTML(transaction.category)}
        </span>

    </div>


    <div class="row">

        <span class="label">Date</span>

        <span class="value">
            ${transaction.transaction_date}
        </span>

    </div>


    <div class="row">

        <span class="label">Type</span>

        <span class="value">
            Expense
        </span>

    </div>


    <div class="row">

        <span class="label">Amount</span>

        <span class="value amount">
            ${amount}
        </span>

    </div>


    <div class="footer">

        Generated by ExpenseFlow

        <br>

        Personal Expense Tracker

    </div>

</div>

</body>

</html>

`;


    const blob =
        new Blob(
            [receiptHTML],
            {
                type: "text/html;charset=utf-8"
            }
        );


    const url =
        URL.createObjectURL(blob);


    const link =
        document.createElement("a");


    link.href = url;


    link.download =
        `ExpenseFlow_Receipt_${transaction.id}.html`;


    document.body.appendChild(link);

    link.click();

    document.body.removeChild(link);

    URL.revokeObjectURL(url);

}


// =====================================================
// ADD DOWNLOAD REPORT BUTTON
// =====================================================

function addDownloadReportButton() {

    const panelHeader =
        document.querySelector(
            ".transactions-panel .panel-header"
        );


    if (!panelHeader) {
        return;
    }


    if (
        document.getElementById(
            "downloadReportBtn"
        )
    ) {
        return;
    }


    const button =
        document.createElement("button");


    button.id =
        "downloadReportBtn";


    button.className =
        "refresh-btn";


    button.textContent =
        "⬇ Download Report";


    button.onclick =
        downloadReport;


    panelHeader.appendChild(button);

}


// =========================
// SET TODAY'S DATE
// =========================

function setToday() {

    const today =
        new Date()
            .toISOString()
            .split("T")[0];

    document.getElementById(
        "transaction_date"
    ).value = today;

}


// =========================
// SCROLL TO ADD SECTION
// =========================

function scrollToAdd() {

    document
        .getElementById("add-section")
        .scrollIntoView({
            behavior: "smooth"
        });

}


// =========================
// ESCAPE HTML
// =========================

function escapeHTML(value) {

    return String(value)

        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");

}


// =========================
// SEARCH EVENT
// =========================

document
    .getElementById("searchInput")
    .addEventListener(
        "input",
        filterTransactions
    );


// =========================
// TYPE FILTER EVENT
// =========================

document
    .getElementById("typeFilter")
    .addEventListener(
        "change",
        filterTransactions
    );


// =========================
// CATEGORY FILTER EVENT
// =========================

document
    .getElementById("categoryFilter")
    .addEventListener(
        "change",
        filterTransactions
    );


// =========================
// PAGE LOAD
// =========================

document.addEventListener(
    "DOMContentLoaded",
    function() {

        setToday();

        addDownloadReportButton();

        loadSummary();

        loadTransactions();

        loadMonthlyAnalysis();

        loadCategoryAnalysis();

    }
);