# Bank Accounting System

**Student Name:** Priya Choudhury  
**Roll No:** 07  
**Seat Number:** 510513055  
**Degree:** Bachelor of Science (Computer Science) — Semester V (2026–2027)  
**College:** RP Institute of Hospitality & Management (Affiliated to Mumbai University)  
**Project Guide:** Prof. Mrs. Sahaya Jeicy  

---

## 📌 Project Overview

The **Bank Accounting System** is a computerized financial management application engineered with **Python (Flask)**, **SQLite / PostgreSQL**, and a modern, responsive **HTML5/CSS3/JavaScript** frontend.

It replaces error-prone manual register bookkeeping with automated double-entry ledger calculations, real-time dashboards, transaction validation, party directories (Customers & Suppliers), invoice tracking, and comprehensive financial reports (Profit & Loss, Income Statement, Balance Summaries).

---

## 🚀 Key Modules & Features (Black Book Specification)

| Module | Report Reference | Description |
| :--- | :--- | :--- |
| **Authentication** | Figure 6.1 | Secure role-based login (Admin, Accountant, Manager), session management |
| **Dashboard** | Figure 6.2 | KPI metric cards (Total Income ₹50k, Expenses ₹20k, Balance ₹30k, Pending Payments 3), Monthly bar chart, Account balance progress meters, Recent transactions |
| **Account Management** | Figure 6.3 | Chart of accounts (Cash, Bank, Asset, Income, Expense, Liability), Quick-Add, and Edit/Delete operations |
| **Transaction Processing** | Figure 6.4 | Add/Edit transactions with interactive real-time validation checklist (Mandatory fields, valid amount, account selected) |
| **General Ledger** | Figure 6.5 | Account-wise transaction history, Debit/Credit columns, running balance, opening/closing summary |
| **Invoices & Payments** | Chapter 3.8 | Generate invoices with due dates, payment status tracking, and inline partial/full payment recording |
| **Customers & Suppliers** | Chapter 5.2 | Contact directories linked to transactions and invoices |
| **Financial Reports** | Figure 6.6 | Income Statement, Balance Summary, Transaction History, Profit/Loss, Export PDF, Print, and CSV export |
| **Settings & Reminders** | Chapter 3.10 | Business profile, currency formatting (₹ INR), date formats, and pending payment alerts |

---

## 💾 100% Portable Pen-Drive Guide (Plug & Play)

This application is designed to be **completely portable**:

### Option 1: Double-Click Launcher (Windows)
1. Insert your pen drive into any computer.
2. Open the folder and double-click **`run.bat`** (or right-click `run.ps1` → *Run with PowerShell*).
3. The script automatically verifies Python, sets up dependencies, opens your browser at `http://127.0.0.1:5000`, and launches the system!

### Option 2: Run via Visual Studio Code
1. Open this folder in **Visual Studio Code**.
2. Press **`F5`** (or go to *Run and Debug* → click **Python: Accounting System (Flask)**).
3. Open `http://127.0.0.1:5000` in your web browser.

### Option 3: Command Line (Linux / macOS / Windows)
```bash
# Windows
.\.venv\Scripts\activate
python app.py

# Linux / macOS
./run.sh
```

---

## 🔑 Default Login Credentials

| Role | Username | Password | Access Level |
| :--- | :--- | :--- | :--- |
| **Accountant** | `accountant01` | `password123` | Day-to-day transaction entry & ledgers |
| **Administrator** | `admin` | `admin123` | Full administrative control & settings |

---

## 🧪 Automated Test Suite (Table 6.2 Test Cases)

The application includes an automated test suite verifying all 15 test cases defined in the project report:

```bash
python -m pytest tests/test_accounting.py -v
```

### Test Case Verification Summary:
* ✅ **TC-01:** Login with valid credentials — *Dashboard opens* (**PASS**)
* ✅ **TC-02:** Login with invalid credentials — *Error message shown and access denied* (**PASS**)
* ✅ **TC-03:** Create a new account — *Account saved and appears in list* (**PASS**)
* ✅ **TC-04:** Update account details — *Updated details saved and reflected* (**PASS**)
* ✅ **TC-05:** Record an income transaction — *Balance increases and ledger updated* (**PASS**)
* ✅ **TC-06:** Record an expense transaction — *Balance decreases and ledger updated* (**PASS**)
* ✅ **TC-07:** Submit blank or invalid amount — *Entry rejected with readable message* (**PASS**)
* ✅ **TC-08:** Add customer and supplier — *Records saved and linked to transactions* (**PASS**)
* ✅ **TC-09:** Search and filter transactions — *Only matching transactions displayed* (**PASS**)
* ✅ **TC-10:** Edit an existing transaction — *Balances and ledger recalculated* (**PASS**)
* ✅ **TC-11:** Delete a transaction — *Transaction removed and balance adjusted* (**PASS**)
* ✅ **TC-12:** Check dashboard totals — *Totals match recorded transactions* (**PASS**)
* ✅ **TC-13:** View account ledger — *Account-wise history shown correctly* (**PASS**)
* ✅ **TC-14:** Generate financial report — *Income, expense, and profit/loss correct* (**PASS**)
* ✅ **TC-15:** Reload / reopen application — *Data persists reliably in SQLite* (**PASS**)

---

## ☁️ Deploying to Render (When Ready)

The repository includes `Procfile` and `render.yaml` configured for zero-downtime cloud hosting:

1. Connect your repository on [Render](https://render.com/).
2. Select **New Web Service** → connect repository `Accounting-System`.
3. Set:
   * **Environment:** `Python`
   * **Build Command:** `pip install -r requirements.txt`
   * **Start Command:** `gunicorn app:app`
4. Optional Database: If using Render PostgreSQL, provide the `DATABASE_URL` environment variable. The app automatically handles SQLite-to-PostgreSQL compatibility!

---

## 📁 Repository Structure

```
Accounting System/
├── .vscode/
│   ├── launch.json          # One-click F5 run & debug configurations
│   ├── tasks.json           # VS Code automated task runners
│   └── settings.json        # Python interpreter path
├── static/
│   └── style.css            # Responsive UI & print stylesheets
├── templates/
│   ├── base.html            # Navigation sidebar and header
│   ├── login.html           # Login screen (Figure 6.1)
│   ├── dashboard.html       # Metric cards & charts (Figure 6.2)
│   ├── accounts.html        # Account management & edit modal (Figure 6.3)
│   ├── transactions.html    # Add transaction & validation card (Figure 6.4)
│   ├── ledger.html          # Double-entry ledger audit trail (Figure 6.5)
│   ├── reports.html         # Profit/Loss & breakdown (Figure 6.6)
│   ├── contacts.html        # Customer and Supplier directory
│   ├── invoices.html        # Billing, due dates & payments
│   └── settings.html        # System preferences and academic metadata
├── tests/
│   └── test_accounting.py   # Automated pytest suite (TC-01 to TC-15)
├── app.py                   # Flask backend and database models
├── requirements.txt         # Pinned production dependencies
├── Procfile                 # Render cloud web server configuration
├── render.yaml              # Render blueprint specification
├── run.bat                  # Windows 1-click pen-drive launcher
├── run.ps1                  # PowerShell launcher
├── run.sh                   # Linux/macOS launcher
└── README.md                # Project documentation
```
