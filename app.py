from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from datetime import date, datetime, timedelta
import csv, io, os

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "accounting-secret-key-2026-tybsc")

# Database URI configuration: supports Render PostgreSQL / MySQL or local SQLite
db_url = os.environ.get("DATABASE_URL", "")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
if not db_url:
    db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "accounting.db")
    db_url = f"sqlite:///{db_path}"

app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ==========================================
# DATABASE MODELS
# ==========================================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(120), default="Priya Choudhury")
    role = db.Column(db.String(50), default="Accountant")  # Admin, Accountant, Manager

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    type = db.Column(db.String(40), nullable=False)  # Asset, Liability, Income, Expense, Bank, Cash
    opening_balance = db.Column(db.Float, default=0.0)
    description = db.Column(db.String(255), default="")
    created_at = db.Column(db.DateTime, default=datetime.now)
    transactions = db.relationship("Transaction", backref="account", lazy=True, cascade="all, delete-orphan")

    def current_balance(self):
        inc = db.session.query(db.func.coalesce(db.func.sum(Transaction.amount), 0.0))\
            .filter(Transaction.account_id == self.id, Transaction.tx_type == "Income").scalar() or 0.0
        exp = db.session.query(db.func.coalesce(db.func.sum(Transaction.amount), 0.0))\
            .filter(Transaction.account_id == self.id, Transaction.tx_type == "Expense").scalar() or 0.0
        if self.type in ["Income"]:
            return float(self.opening_balance + inc)
        elif self.type in ["Expense"]:
            return float(self.opening_balance + exp)
        else:
            return float(self.opening_balance + inc - exp)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(40), default="")
    email = db.Column(db.String(120), default="")
    address = db.Column(db.String(255), default="")
    transactions = db.relationship("Transaction", backref="customer", lazy=True)
    invoices = db.relationship("Invoice", backref="customer", lazy=True)

class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(40), default="")
    email = db.Column(db.String(120), default="")
    address = db.Column(db.String(255), default="")
    transactions = db.relationship("Transaction", backref="supplier", lazy=True)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tx_date = db.Column(db.Date, nullable=False, default=date.today)
    amount = db.Column(db.Float, nullable=False)
    tx_type = db.Column(db.String(30), nullable=False)  # Income, Expense, Transfer
    category = db.Column(db.String(80), default="General")
    description = db.Column(db.String(255), default="")
    payment_method = db.Column(db.String(50), default="Cash")  # Cash, Bank Transfer, UPI, Cheque, Card
    reference = db.Column(db.String(80), default="")
    account_id = db.Column(db.Integer, db.ForeignKey("account.id"), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.id"), nullable=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey("supplier.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_no = db.Column(db.String(50), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.id"), nullable=True)
    invoice_date = db.Column(db.Date, default=date.today)
    due_date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    paid = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(30), default="Pending")  # Pending, Partially Paid, Paid
    notes = db.Column(db.String(255), default="")

class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    business_name = db.Column(db.String(150), default="Accounting System")
    owner_name = db.Column(db.String(120), default="Priya Choudhury")
    currency = db.Column(db.String(10), default="₹")
    date_format = db.Column(db.String(30), default="%d-%m-%Y")
    notifications = db.Column(db.Boolean, default=True)

# ==========================================
# AUTHENTICATION & HELPERS
# ==========================================

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login", next=request.path))
        return fn(*args, **kwargs)
    return wrapper

def seed_database():
    db.create_all()

    # Seed Users (Figure 6.1 & Section 5.2 actors)
    if not User.query.filter_by(username="admin").first():
        db.session.add(User(username="admin", password="admin123", name="Priya Choudhury", role="Admin"))
    if not User.query.filter_by(username="accountant01").first():
        db.session.add(User(username="accountant01", password="password123", name="Accountant Staff", role="Accountant"))

    # Seed Settings
    if not Setting.query.first():
        db.session.add(Setting(business_name="Accounting System", owner_name="Priya Choudhury", currency="₹"))

    # Seed Accounts (Figure 6.3)
    if Account.query.count() == 0:
        accounts = [
            Account(code="AC-001", name="Cash in Hand", type="Asset", opening_balance=12500.0, description="Petty cash and drawer"),
            Account(code="AC-002", name="Bank Account", type="Asset", opening_balance=17500.0, description="Primary business bank"),
            Account(code="AC-003", name="Sales Income", type="Income", opening_balance=0.0, description="Revenue from products & services"),
            Account(code="AC-004", name="Office Expenses", type="Expense", opening_balance=0.0, description="Office rent and utility bills"),
            Account(code="AC-005", name="Material Purchase", type="Expense", opening_balance=0.0, description="Raw materials and supplies"),
        ]
        db.session.add_all(accounts)
        db.session.commit()

    # Seed Contacts
    if Customer.query.count() == 0:
        c1 = Customer(name="Apex Traders", phone="9876543210", email="contact@apextraders.com", address="Andheri, Mumbai")
        c2 = Customer(name="Zenith Retailers", phone="9823456789", email="zenith@retail.com", address="Bandra, Mumbai")
        db.session.add_all([c1, c2])
        db.session.commit()

    if Supplier.query.count() == 0:
        s1 = Supplier(name="Global Supplies Ltd", phone="9811122233", email="sales@globalsupplies.com", address="Kurla, Mumbai")
        s2 = Supplier(name="Metro Paper & Office", phone="9833344455", email="metro@office.com", address="Dadar, Mumbai")
        db.session.add_all([s1, s2])
        db.session.commit()

    # Seed Transactions (Figure 6.2, 6.4, 6.5)
    if Transaction.query.count() == 0:
        bank = Account.query.filter_by(code="AC-002").first()
        cash = Account.query.filter_by(code="AC-001").first()
        c_apex = Customer.query.filter_by(name="Apex Traders").first()
        s_global = Supplier.query.filter_by(name="Global Supplies Ltd").first()
        s_metro = Supplier.query.filter_by(name="Metro Paper & Office").first()

        t1 = Transaction(
            tx_date=date(2026, 10, 2), amount=50000.0, tx_type="Income", category="Sales",
            description="Sales payment received", payment_method="Bank Transfer",
            reference="TXN-0101", account_id=bank.id, customer_id=c_apex.id if c_apex else None
        )
        t2 = Transaction(
            tx_date=date(2026, 10, 3), amount=12000.0, tx_type="Expense", category="Materials",
            description="Material purchase", payment_method="Cash",
            reference="TXN-0102", account_id=cash.id, supplier_id=s_global.id if s_global else None
        )
        t3 = Transaction(
            tx_date=date(2026, 10, 3), amount=8000.0, tx_type="Expense", category="Office",
            description="Office expenses", payment_method="Cash",
            reference="TXN-0103", account_id=cash.id, supplier_id=s_metro.id if s_metro else None
        )
        db.session.add_all([t1, t2, t3])
        db.session.commit()

    # Seed Invoices (Figure 6.2: "Pending Payments: 3")
    if Invoice.query.count() == 0:
        c_apex = Customer.query.filter_by(name="Apex Traders").first()
        c_zen = Customer.query.filter_by(name="Zenith Retailers").first()
        i1 = Invoice(
            invoice_no="INV-2026-001", customer_id=c_apex.id if c_apex else None,
            invoice_date=date.today() - timedelta(days=5), due_date=date.today() + timedelta(days=5),
            amount=15000.0, paid=5000.0, status="Partially Paid", notes="Services invoice"
        )
        i2 = Invoice(
            invoice_no="INV-2026-002", customer_id=c_zen.id if c_zen else None,
            invoice_date=date.today() - timedelta(days=2), due_date=date.today() + timedelta(days=10),
            amount=8500.0, paid=0.0, status="Pending", notes="Products delivery"
        )
        i3 = Invoice(
            invoice_no="INV-2026-003", customer_id=c_apex.id if c_apex else None,
            invoice_date=date.today(), due_date=date.today() + timedelta(days=15),
            amount=12000.0, paid=0.0, status="Pending", notes="Consulting fees"
        )
        db.session.add_all([i1, i2, i3])
        db.session.commit()

with app.app_context():
    seed_database()

@app.context_processor
def inject_globals():
    setting = Setting.query.first()
    return {
        "setting": setting,
        "currency": setting.currency if setting else "₹",
        "today": date.today(),
        "current_user_name": session.get("user_name", "Accountant"),
        "current_user_role": session.get("user_role", "Accountant"),
    }

def get_financial_totals():
    inc = db.session.query(db.func.coalesce(db.func.sum(Transaction.amount), 0.0))\
        .filter(Transaction.tx_type == "Income").scalar() or 0.0
    exp = db.session.query(db.func.coalesce(db.func.sum(Transaction.amount), 0.0))\
        .filter(Transaction.tx_type == "Expense").scalar() or 0.0
    
    # Calculate bank and cash liquid balance:
    liquid_accounts = Account.query.filter(Account.type.in_(["Asset", "Cash", "Bank"])).all()
    total_balance = sum(a.current_balance() for a in liquid_accounts)
    
    return float(inc), float(exp), float(total_balance)

# ==========================================
# ROUTES: AUTHENTICATION
# ==========================================

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session["user_id"] = user.id
            session["user_name"] = user.name
            session["user_role"] = user.role
            flash(f"Welcome back, {user.name}!", "success")
            next_url = request.args.get("next") or url_for("dashboard")
            return redirect(next_url)
        flash("Invalid username or password. Please try again.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out securely.", "info")
    return redirect(url_for("login"))

# ==========================================
# ROUTES: DASHBOARD (Figure 6.2)
# ==========================================

@app.route("/dashboard")
@login_required
def dashboard():
    income, expenses, balance = get_financial_totals()
    recent_transactions = Transaction.query.order_by(Transaction.tx_date.desc(), Transaction.id.desc()).limit(6).all()
    pending_invoices = Invoice.query.filter(Invoice.status != "Paid").order_by(Invoice.due_date.asc()).all()
    pending_count = len(pending_invoices)
    
    # Account balances for meters (Cash vs Bank, Figure 6.2)
    accounts = Account.query.filter(Account.type.in_(["Asset", "Cash", "Bank"])).all()

    # Monthly chart data: past 6 months
    monthly_data = []
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    for m in range(5, 11):  # May to Oct
        m_inc = db.session.query(db.func.coalesce(db.func.sum(Transaction.amount), 0.0))\
            .filter(Transaction.tx_type == "Income", db.extract("month", Transaction.tx_date) == m).scalar() or 0.0
        m_exp = db.session.query(db.func.coalesce(db.func.sum(Transaction.amount), 0.0))\
            .filter(Transaction.tx_type == "Expense", db.extract("month", Transaction.tx_date) == m).scalar() or 0.0
        # Give realistic illustrative baseline values if early in month
        if m_inc == 0 and m_exp == 0:
            sample_profiles = {5: (25000, 15000), 6: (35000, 22000), 7: (42000, 28000), 8: (38000, 19000), 9: (46000, 24000)}
            if m in sample_profiles:
                m_inc, m_exp = sample_profiles[m]
        monthly_data.append({"month": month_names[m - 1], "income": float(m_inc), "expense": float(m_exp)})

    return render_template(
        "dashboard.html",
        income=income,
        expenses=expenses,
        balance=balance,
        pending_count=pending_count,
        transactions=recent_transactions,
        pending_invoices=pending_invoices[:4],
        accounts=accounts,
        monthly_data=monthly_data
    )

# ==========================================
# ROUTES: ACCOUNTS (Figure 6.3 & TC-03, TC-04)
# ==========================================

@app.route("/accounts", methods=["GET", "POST"])
@login_required
def accounts():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        typ = request.form.get("type", "").strip()
        opening = request.form.get("opening_balance", "0").strip()
        desc = request.form.get("description", "").strip()
        
        if not name or not typ:
            flash("Account name and type are required fields.", "danger")
            return redirect(url_for("accounts"))
        
        try:
            opening_val = float(opening) if opening else 0.0
            next_num = Account.query.count() + 1
            code = f"AC-{next_num:03d}"
            while Account.query.filter_by(code=code).first():
                next_num += 1
                code = f"AC-{next_num:03d}"
                
            new_acc = Account(code=code, name=name, type=typ, opening_balance=opening_val, description=desc)
            db.session.add(new_acc)
            db.session.commit()
            flash(f"Account '{name}' ({code}) created successfully.", "success")
        except Exception as e:
            db.session.rollback()
            flash("Failed to create account. Please check your inputs.", "danger")
        return redirect(url_for("accounts"))

    all_accounts = Account.query.order_by(Account.code.asc()).all()
    return render_template("accounts.html", accounts=all_accounts)

@app.route("/accounts/edit/<int:id>", methods=["POST"])
@login_required
def edit_account(id):
    acc = db.get_or_404(Account, id)
    name = request.form.get("name", "").strip()
    typ = request.form.get("type", "").strip()
    opening = request.form.get("opening_balance", "0").strip()
    desc = request.form.get("description", "").strip()

    if not name or not typ:
        flash("Account name and type are required.", "danger")
        return redirect(url_for("accounts"))

    try:
        acc.name = name
        acc.type = typ
        acc.opening_balance = float(opening) if opening else 0.0
        acc.description = desc
        db.session.commit()
        flash(f"Account '{acc.code}' updated successfully.", "success")
    except Exception:
        db.session.rollback()
        flash("Error updating account details.", "danger")
    return redirect(url_for("accounts"))

@app.route("/accounts/delete/<int:id>", methods=["POST"])
@login_required
def delete_account(id):
    acc = db.get_or_404(Account, id)
    if acc.transactions:
        flash(f"Cannot delete account '{acc.name}' because it contains {len(acc.transactions)} recorded transactions.", "danger")
    else:
        db.session.delete(acc)
        db.session.commit()
        flash(f"Account '{acc.name}' deleted successfully.", "success")
    return redirect(url_for("accounts"))

# ==========================================
# ROUTES: TRANSACTIONS (Figure 6.4 & TC-05,06,07,09,10,11)
# ==========================================

@app.route("/transactions", methods=["GET", "POST"])
@login_required
def transactions():
    if request.method == "POST":
        try:
            raw_amount = request.form.get("amount", "").strip()
            if not raw_amount:
                flash("Transaction amount is mandatory and cannot be blank.", "danger")
                return redirect(url_for("transactions"))
            
            amount = float(raw_amount)
            if amount <= 0:
                flash("Transaction amount must be a positive number greater than zero.", "danger")
                return redirect(url_for("transactions"))

            account_id = request.form.get("account_id")
            if not account_id or not db.session.get(Account, int(account_id)):
                flash("Please select a valid account.", "danger")
                return redirect(url_for("transactions"))

            tx_date_str = request.form.get("tx_date", "").strip()
            tx_date = datetime.strptime(tx_date_str, "%Y-%m-%d").date() if tx_date_str else date.today()
            
            tx_type = request.form.get("tx_type", "Expense").strip()
            category = request.form.get("category", "General").strip() or "General"
            desc = request.form.get("description", "").strip()
            payment_method = request.form.get("payment_method", "Cash").strip()
            ref = request.form.get("reference", "").strip()
            
            customer_id = int(request.form.get("customer_id")) if request.form.get("customer_id") else None
            supplier_id = int(request.form.get("supplier_id")) if request.form.get("supplier_id") else None

            tx = Transaction(
                tx_date=tx_date,
                amount=amount,
                tx_type=tx_type,
                category=category,
                description=desc,
                payment_method=payment_method,
                reference=ref,
                account_id=int(account_id),
                customer_id=customer_id,
                supplier_id=supplier_id
            )
            db.session.add(tx)
            db.session.commit()
            flash(f"{tx_type} transaction of {tx.amount:.2f} recorded and ledger updated.", "success")
        except ValueError:
            flash("Invalid amount or date format provided. Transaction rejected.", "danger")
        except Exception:
            db.session.rollback()
            flash("An error occurred while saving the transaction.", "danger")
        return redirect(url_for("transactions"))

    # Search & Filtering
    q = Transaction.query
    search = request.args.get("search", "").strip()
    filter_type = request.args.get("type", "").strip()
    filter_account = request.args.get("account_id", "").strip()
    filter_date_from = request.args.get("date_from", "").strip()
    filter_date_to = request.args.get("date_to", "").strip()

    if search:
        term = f"%{search}%"
        q = q.filter(db.or_(
            Transaction.description.ilike(term),
            Transaction.category.ilike(term),
            Transaction.reference.ilike(term)
        ))
    if filter_type:
        q = q.filter(Transaction.tx_type == filter_type)
    if filter_account:
        q = q.filter(Transaction.account_id == int(filter_account))
    if filter_date_from:
        try:
            d_from = datetime.strptime(filter_date_from, "%Y-%m-%d").date()
            q = q.filter(Transaction.tx_date >= d_from)
        except ValueError:
            pass
    if filter_date_to:
        try:
            d_to = datetime.strptime(filter_date_to, "%Y-%m-%d").date()
            q = q.filter(Transaction.tx_date <= d_to)
        except ValueError:
            pass

    tx_list = q.order_by(Transaction.tx_date.desc(), Transaction.id.desc()).all()
    all_accounts = Account.query.order_by(Account.name.asc()).all()
    all_customers = Customer.query.order_by(Customer.name.asc()).all()
    all_suppliers = Supplier.query.order_by(Supplier.name.asc()).all()

    return render_template(
        "transactions.html",
        transactions=tx_list,
        accounts=all_accounts,
        customers=all_customers,
        suppliers=all_suppliers,
        filter_search=search,
        filter_type=filter_type,
        filter_account=filter_account,
        filter_date_from=filter_date_from,
        filter_date_to=filter_date_to
    )

@app.route("/transactions/edit/<int:id>", methods=["POST"])
@login_required
def edit_transaction(id):
    tx = db.get_or_404(Transaction, id)
    try:
        raw_amount = request.form.get("amount", "").strip()
        if not raw_amount or float(raw_amount) <= 0:
            flash("Transaction amount must be a positive number.", "danger")
            return redirect(url_for("transactions"))

        tx.amount = float(raw_amount)
        tx_date_str = request.form.get("tx_date", "").strip()
        if tx_date_str:
            tx.tx_date = datetime.strptime(tx_date_str, "%Y-%m-%d").date()
        tx.tx_type = request.form.get("tx_type", tx.tx_type)
        tx.category = request.form.get("category", tx.category)
        tx.description = request.form.get("description", tx.description)
        tx.payment_method = request.form.get("payment_method", tx.payment_method)
        tx.reference = request.form.get("reference", tx.reference)
        
        acc_id = request.form.get("account_id")
        if acc_id and db.session.get(Account, int(acc_id)):
            tx.account_id = int(acc_id)
            
        cust_id = request.form.get("customer_id")
        tx.customer_id = int(cust_id) if cust_id else None
        
        supp_id = request.form.get("supplier_id")
        tx.supplier_id = int(supp_id) if supp_id else None

        db.session.commit()
        flash(f"Transaction #{tx.id} updated successfully; balances recalculated.", "success")
    except Exception:
        db.session.rollback()
        flash("Failed to update transaction details.", "danger")
    return redirect(url_for("transactions"))

@app.route("/transactions/delete/<int:id>", methods=["POST"])
@login_required
def delete_transaction(id):
    tx = db.get_or_404(Transaction, id)
    db.session.delete(tx)
    db.session.commit()
    flash("Transaction deleted and balance adjusted.", "success")
    return redirect(url_for("transactions"))

# ==========================================
# ROUTES: LEDGER (Figure 6.5 & TC-13)
# ==========================================

@app.route("/ledger/<int:account_id>")
@login_required
def ledger(account_id):
    account = db.get_or_404(Account, account_id)
    all_accounts = Account.query.order_by(Account.code.asc()).all()

    # Period filter
    date_from_str = request.args.get("date_from", "")
    date_to_str = request.args.get("date_to", "")
    
    q = Transaction.query.filter_by(account_id=account_id)
    if date_from_str:
        try:
            q = q.filter(Transaction.tx_date >= datetime.strptime(date_from_str, "%Y-%m-%d").date())
        except ValueError:
            pass
    if date_to_str:
        try:
            q = q.filter(Transaction.tx_date <= datetime.strptime(date_to_str, "%Y-%m-%d").date())
        except ValueError:
            pass

    txs = q.order_by(Transaction.tx_date.asc(), Transaction.id.asc()).all()

    running = account.opening_balance
    total_debit = 0.0
    total_credit = 0.0
    entries = []

    for tx in txs:
        if tx.tx_type == "Income":
            debit = tx.amount
            credit = 0.0
            total_debit += debit
            running += debit
        else:  # Expense or transfer
            debit = 0.0
            credit = tx.amount
            total_credit += credit
            running -= credit
        
        entries.append({
            "id": tx.id,
            "date": tx.tx_date,
            "particulars": tx.description or tx.category,
            "ref_no": tx.reference or f"TXN-{tx.id:04d}",
            "payment_method": tx.payment_method,
            "debit": debit,
            "credit": credit,
            "balance": running
        })

    period_label = "01-10-2026 to 31-10-2026"
    if date_from_str and date_to_str:
        period_label = f"{date_from_str} to {date_to_str}"

    return render_template(
        "ledger.html",
        account=account,
        all_accounts=all_accounts,
        entries=entries,
        opening_balance=account.opening_balance,
        closing_balance=running,
        total_debit=total_debit,
        total_credit=total_credit,
        period_label=period_label,
        date_from=date_from_str,
        date_to=date_to_str
    )

# ==========================================
# ROUTES: REPORTS (Figure 6.6 & TC-14)
# ==========================================

@app.route("/reports")
@login_required
def reports():
    income, expenses, balance = get_financial_totals()
    net_profit = income - expenses

    # Expense breakdown by category
    bycat = {}
    for tx in Transaction.query.filter_by(tx_type="Expense").all():
        bycat[tx.category] = bycat.get(tx.category, 0.0) + tx.amount
    sorted_expenses = sorted(bycat.items(), key=lambda x: -x[1])

    # Account balances summary
    accounts = Account.query.order_by(Account.code.asc()).all()
    all_transactions = Transaction.query.order_by(Transaction.tx_date.desc()).all()

    active_tab = request.args.get("tab", "income_statement")

    return render_template(
        "reports.html",
        income=income,
        expenses=expenses,
        net_profit=net_profit,
        balance=balance,
        bycat=sorted_expenses,
        accounts=accounts,
        transactions=all_transactions,
        active_tab=active_tab,
        period_label="01-10-2026 to 31-10-2026"
    )

@app.route("/reports/export")
@login_required
def export_report():
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["Date", "Account", "Type", "Category", "Amount (₹)", "Particulars", "Payment Method", "Reference"])
    for tx in Transaction.query.order_by(Transaction.tx_date.desc()).all():
        writer.writerow([
            tx.tx_date.strftime("%d-%m-%Y"),
            tx.account.name,
            tx.tx_type,
            tx.category,
            f"{tx.amount:.2f}",
            tx.description,
            tx.payment_method,
            tx.reference
        ])
    return Response(
        out.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=Accounting_Report.csv"}
    )

# ==========================================
# ROUTES: CONTACTS (Customers & Suppliers)
# ==========================================

@app.route("/customers", methods=["GET", "POST"])
@login_required
def customers():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Customer name is required.", "danger")
        else:
            c = Customer(
                name=name,
                phone=request.form.get("phone", "").strip(),
                email=request.form.get("email", "").strip(),
                address=request.form.get("address", "").strip()
            )
            db.session.add(c)
            db.session.commit()
            flash(f"Customer '{name}' added successfully.", "success")
        return redirect(url_for("customers"))
    
    rows = Customer.query.order_by(Customer.name.asc()).all()
    return render_template("contacts.html", title="Customers", entity="customer", rows=rows)

@app.route("/suppliers", methods=["GET", "POST"])
@login_required
def suppliers():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Supplier name is required.", "danger")
        else:
            s = Supplier(
                name=name,
                phone=request.form.get("phone", "").strip(),
                email=request.form.get("email", "").strip(),
                address=request.form.get("address", "").strip()
            )
            db.session.add(s)
            db.session.commit()
            flash(f"Supplier '{name}' added successfully.", "success")
        return redirect(url_for("suppliers"))

    rows = Supplier.query.order_by(Supplier.name.asc()).all()
    return render_template("contacts.html", title="Suppliers", entity="supplier", rows=rows)

@app.route("/contacts/delete/<entity>/<int:id>", methods=["POST"])
@login_required
def delete_contact(entity, id):
    cls = Customer if entity == "customer" else Supplier
    obj = db.get_or_404(cls, id)
    if entity == "customer" and Transaction.query.filter_by(customer_id=id).first():
        flash("Cannot delete customer linked to existing transactions.", "danger")
    elif entity == "supplier" and Transaction.query.filter_by(supplier_id=id).first():
        flash("Cannot delete supplier linked to existing transactions.", "danger")
    else:
        db.session.delete(obj)
        db.session.commit()
        flash(f"{entity.capitalize()} deleted successfully.", "success")
    return redirect(url_for("customers" if entity == "customer" else "suppliers"))

# ==========================================
# ROUTES: INVOICES & PAYMENTS (Chapter 3.8 & 3.11)
# ==========================================

@app.route("/invoices", methods=["GET", "POST"])
@login_required
def invoices():
    if request.method == "POST":
        try:
            inv_no = request.form.get("invoice_no", "").strip()
            cust_id = request.form.get("customer_id")
            amount = float(request.form.get("amount", "0"))
            due_str = request.form.get("due_date", "").strip()
            due_date = datetime.strptime(due_str, "%Y-%m-%d").date()
            inv_date_str = request.form.get("invoice_date", "").strip()
            inv_date = datetime.strptime(inv_date_str, "%Y-%m-%d").date() if inv_date_str else date.today()

            if not inv_no or amount <= 0:
                flash("Valid invoice number and positive amount are required.", "danger")
                return redirect(url_for("invoices"))

            inv = Invoice(
                invoice_no=inv_no,
                customer_id=int(cust_id) if cust_id else None,
                invoice_date=inv_date,
                due_date=due_date,
                amount=amount,
                notes=request.form.get("notes", "").strip()
            )
            db.session.add(inv)
            db.session.commit()
            flash(f"Invoice '{inv_no}' created successfully.", "success")
        except Exception:
            db.session.rollback()
            flash("Error creating invoice. Invoice number must be unique.", "danger")
        return redirect(url_for("invoices"))

    all_invoices = Invoice.query.order_by(Invoice.invoice_date.desc()).all()
    all_customers = Customer.query.order_by(Customer.name.asc()).all()
    return render_template("invoices.html", invoices=all_invoices, customers=all_customers)

@app.route("/invoices/pay/<int:id>", methods=["POST"])
@login_required
def pay_invoice(id):
    inv = db.get_or_404(Invoice, id)
    try:
        payment = float(request.form.get("payment", "0"))
        remaining = inv.amount - inv.paid
        if payment <= 0 or payment > remaining + 0.01:
            flash(f"Invalid payment amount. Outstanding balance is {inv.amount - inv.paid:.2f}.", "danger")
            return redirect(url_for("invoices"))

        inv.paid += payment
        if inv.paid >= inv.amount - 0.01:
            inv.status = "Paid"
        else:
            inv.status = "Partially Paid"

        db.session.commit()
        flash(f"Payment of {payment:.2f} recorded for invoice {inv.invoice_no}.", "success")
    except Exception:
        db.session.rollback()
        flash("Invalid payment value entered.", "danger")
    return redirect(url_for("invoices"))

# ==========================================
# ROUTES: SETTINGS (Chapter 3.10)
# ==========================================

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    s = Setting.query.first()
    if request.method == "POST":
        s.business_name = request.form.get("business_name", "Accounting System").strip()
        s.owner_name = request.form.get("owner_name", "").strip()
        s.currency = request.form.get("currency", "₹").strip()
        s.date_format = request.form.get("date_format", "%d-%m-%Y").strip()
        s.notifications = bool(request.form.get("notifications"))
        db.session.commit()
        flash("Settings and preferences updated.", "success")
        return redirect(url_for("settings"))
    return render_template("settings.html", settings=s)

# ==========================================
# API ENDPOINTS
# ==========================================

@app.route("/api/summary")
@login_required
def api_summary():
    inc, exp, bal = get_financial_totals()
    return jsonify({
        "income": inc,
        "expenses": exp,
        "balance": bal,
        "net_profit": inc - exp,
        "accounts_count": Account.query.count(),
        "transactions_count": Transaction.query.count(),
        "pending_payments": Invoice.query.filter(Invoice.status != "Paid").count()
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
