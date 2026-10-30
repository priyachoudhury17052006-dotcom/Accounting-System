"""
Bank Accounting System — Automated Test Suite
Covers all 15 Test Cases from Table 6.2 (Implementation and Testing chapter):
- TC-01: Login with valid credentials
- TC-02: Login with invalid credentials
- TC-03: Create a new account
- TC-04: Update account details
- TC-05: Record an income transaction
- TC-06: Record an expense transaction
- TC-07: Submit blank or invalid amount
- TC-08: Add customer and supplier
- TC-09: Search and filter transactions
- TC-10: Edit an existing transaction
- TC-11: Delete a transaction
- TC-12: Check dashboard totals
- TC-13: View account ledger
- TC-14: Generate financial report
- TC-15: Reload / reopen the application (Data persistence)
"""

import pytest
import os
import tempfile
from datetime import date
from app import app, db, User, Account, Transaction, Customer, Supplier, Invoice, Setting, seed_database

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    
    # Use temporary SQLite database for testing isolation
    db_fd, db_path = tempfile.mkstemp()
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    
    with app.app_context():
        db.drop_all()
        seed_database()

    with app.test_client() as test_client:
        yield test_client

    os.close(db_fd)
    try:
        os.unlink(db_path)
    except Exception:
        pass

def login_as(client, username, password):
    return client.post("/login", data={"username": username, "password": password}, follow_redirects=True)

# -------------------------------------------------------------
# TC-01: Login with valid credentials
# -------------------------------------------------------------
def test_tc01_login_valid(client):
    res = login_as(client, "accountant01", "password123")
    assert res.status_code == 200
    assert b"Dashboard" in res.data
    assert b"Accountant Staff" in res.data

# -------------------------------------------------------------
# TC-02: Login with invalid credentials
# -------------------------------------------------------------
def test_tc02_login_invalid(client):
    res = login_as(client, "accountant01", "wrong_password")
    assert res.status_code == 200
    assert b"Invalid username or password" in res.data

# -------------------------------------------------------------
# TC-03: Create a new account
# -------------------------------------------------------------
def test_tc03_create_account(client):
    login_as(client, "admin", "admin123")
    res = client.post("/accounts", data={
        "name": "Fixed Deposit",
        "type": "Asset",
        "opening_balance": "50000.00",
        "description": "Long term deposit"
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Fixed Deposit" in res.data
    assert b"50,000" in res.data

# -------------------------------------------------------------
# TC-04: Update account details
# -------------------------------------------------------------
def test_tc04_update_account(client):
    login_as(client, "admin", "admin123")
    with app.app_context():
        acc = Account.query.filter_by(code="AC-001").first()
        acc_id = acc.id

    res = client.post(f"/accounts/edit/{acc_id}", data={
        "name": "Petty Cash Drawer",
        "type": "Cash",
        "opening_balance": "15000.00",
        "description": "Updated petty cash balance"
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Petty Cash Drawer" in res.data
    assert b"updated successfully" in res.data

    with app.app_context():
        updated = db.session.get(Account, acc_id)
        assert updated.name == "Petty Cash Drawer"
        assert updated.opening_balance == 15000.0

# -------------------------------------------------------------
# TC-05: Record an income transaction
# -------------------------------------------------------------
def test_tc05_record_income(client):
    login_as(client, "admin", "admin123")
    with app.app_context():
        bank = Account.query.filter_by(code="AC-002").first()
        initial_balance = bank.current_balance()
        bank_id = bank.id

    res = client.post("/transactions", data={
        "tx_date": str(date.today()),
        "account_id": bank_id,
        "tx_type": "Income",
        "category": "Sales",
        "amount": "50000.00",
        "description": "Sales payment received",
        "payment_method": "Bank Transfer",
        "reference": "TXN-0101"
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Income transaction of 50000.00 recorded" in res.data

    with app.app_context():
        bank = db.session.get(Account, bank_id)
        assert bank.current_balance() == initial_balance + 50000.0

# -------------------------------------------------------------
# TC-06: Record an expense transaction
# -------------------------------------------------------------
def test_tc06_record_expense(client):
    login_as(client, "admin", "admin123")
    with app.app_context():
        cash = Account.query.filter_by(code="AC-001").first()
        initial_balance = cash.current_balance()
        cash_id = cash.id

    res = client.post("/transactions", data={
        "tx_date": str(date.today()),
        "account_id": cash_id,
        "tx_type": "Expense",
        "category": "Materials",
        "amount": "12000.00",
        "description": "Material purchase",
        "payment_method": "Cash",
        "reference": "TXN-0102"
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Expense transaction of 12000.00 recorded" in res.data

    with app.app_context():
        cash = db.session.get(Account, cash_id)
        assert cash.current_balance() == initial_balance - 12000.0

# -------------------------------------------------------------
# TC-07: Submit blank or invalid amount
# -------------------------------------------------------------
def test_tc07_invalid_amount(client):
    login_as(client, "admin", "admin123")
    with app.app_context():
        bank_id = Account.query.first().id

    # Blank amount
    res1 = client.post("/transactions", data={
        "tx_date": str(date.today()),
        "account_id": bank_id,
        "tx_type": "Income",
        "amount": "",
        "category": "Sales"
    }, follow_redirects=True)
    assert b"mandatory and cannot be blank" in res1.data

    # Negative / zero amount
    res2 = client.post("/transactions", data={
        "tx_date": str(date.today()),
        "account_id": bank_id,
        "tx_type": "Income",
        "amount": "-500",
        "category": "Sales"
    }, follow_redirects=True)
    assert b"must be a positive number" in res2.data

# -------------------------------------------------------------
# TC-08: Add customer and supplier
# -------------------------------------------------------------
def test_tc08_add_customer_and_supplier(client):
    login_as(client, "admin", "admin123")
    res_c = client.post("/customers", data={
        "name": "Reliance Retail",
        "phone": "9876543210",
        "email": "contact@reliance.com",
        "address": "Andheri West, Mumbai"
    }, follow_redirects=True)
    assert res_c.status_code == 200
    assert b"Reliance Retail" in res_c.data

    res_s = client.post("/suppliers", data={
        "name": "Tata Steel Distribution",
        "phone": "9811122233",
        "email": "sales@tatasteel.com",
        "address": "Kurla East, Mumbai"
    }, follow_redirects=True)
    assert res_s.status_code == 200
    assert b"Tata Steel Distribution" in res_s.data

# -------------------------------------------------------------
# TC-09: Search and filter transactions
# -------------------------------------------------------------
def test_tc09_search_and_filter(client):
    login_as(client, "admin", "admin123")
    # Search for pre-seeded 'Material purchase'
    res = client.get("/transactions?search=Material", follow_redirects=True)
    assert res.status_code == 200
    assert b"Material purchase" in res.data

# -------------------------------------------------------------
# TC-10: Edit an existing transaction
# -------------------------------------------------------------
def test_tc10_edit_transaction(client):
    login_as(client, "admin", "admin123")
    with app.app_context():
        tx = Transaction.query.first()
        tx_id = tx.id
        acc_id = tx.account_id

    # Edit transaction amount to 55000.00
    res = client.post(f"/transactions/edit/{tx_id}", data={
        "tx_date": str(date.today()),
        "account_id": acc_id,
        "tx_type": "Income",
        "amount": "55000.00",
        "category": "Sales",
        "description": "Updated sales amount",
        "payment_method": "UPI",
        "reference": "UPI-0099"
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"updated successfully" in res.data

    with app.app_context():
        updated_tx = db.session.get(Transaction, tx_id)
        assert updated_tx.amount == 55000.0
        assert updated_tx.description == "Updated sales amount"

# -------------------------------------------------------------
# TC-11: Delete a transaction
# -------------------------------------------------------------
def test_tc11_delete_transaction(client):
    login_as(client, "admin", "admin123")
    with app.app_context():
        tx = Transaction.query.first()
        tx_id = tx.id

    res = client.post(f"/transactions/delete/{tx_id}", follow_redirects=True)
    assert res.status_code == 200
    assert b"Transaction deleted and balance adjusted" in res.data

    with app.app_context():
        assert db.session.get(Transaction, tx_id) is None

# -------------------------------------------------------------
# TC-12: Check dashboard totals
# -------------------------------------------------------------
def test_tc12_check_dashboard_totals(client):
    login_as(client, "admin", "admin123")
    res = client.get("/dashboard")
    assert res.status_code == 200
    # Pre-seeded totals: Income 50,000, Expense 20,000
    assert b"50,000" in res.data
    assert b"20,000" in res.data

# -------------------------------------------------------------
# TC-13: View account ledger
# -------------------------------------------------------------
def test_tc13_view_account_ledger(client):
    login_as(client, "admin", "admin123")
    with app.app_context():
        bank = Account.query.filter_by(code="AC-002").first()
        bank_id = bank.id

    res = client.get(f"/ledger/{bank_id}")
    assert res.status_code == 200
    assert b"Ledger - Bank Account" in res.data
    assert b"Sales payment received" in res.data

# -------------------------------------------------------------
# TC-14: Generate financial report
# -------------------------------------------------------------
def test_tc14_generate_financial_report(client):
    login_as(client, "admin", "admin123")
    res = client.get("/reports")
    assert res.status_code == 200
    assert b"Profit and Loss Summary" in res.data
    assert b"50,000" in res.data  # Total Income
    assert b"20,000" in res.data  # Total Expenses
    assert b"30,000" in res.data  # Net Profit (50k - 20k = 30k)

# -------------------------------------------------------------
# TC-15: Reload / reopen the application (Persistence)
# -------------------------------------------------------------
def test_tc15_data_persistence(client):
    with app.app_context():
        users = User.query.count()
        accounts = Account.query.count()
        assert users >= 2
        assert accounts >= 5
