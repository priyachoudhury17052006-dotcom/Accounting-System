from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from datetime import date, datetime
from decimal import Decimal
import csv, io, os

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "accounting-demo-secret")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///" + os.path.join(os.path.dirname(__file__), "accounting.db")
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(120), default="Administrator")

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    type = db.Column(db.String(40), nullable=False)
    opening_balance = db.Column(db.Float, default=0)
    description = db.Column(db.String(255), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    transactions = db.relationship("Transaction", backref="account", lazy=True, cascade="all, delete-orphan")

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(40), default="")
    email = db.Column(db.String(120), default="")
    address = db.Column(db.String(255), default="")

class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(40), default="")
    email = db.Column(db.String(120), default="")
    address = db.Column(db.String(255), default="")

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tx_date = db.Column(db.Date, nullable=False, default=date.today)
    amount = db.Column(db.Float, nullable=False)
    tx_type = db.Column(db.String(30), nullable=False)  # Income, Expense, Transfer
    category = db.Column(db.String(80), default="General")
    description = db.Column(db.String(255), default="")
    payment_method = db.Column(db.String(50), default="Cash")
    reference = db.Column(db.String(80), default="")
    account_id = db.Column(db.Integer, db.ForeignKey("account.id"), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.id"))
    supplier_id = db.Column(db.Integer, db.ForeignKey("supplier.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    customer = db.relationship("Customer")
    supplier = db.relationship("Supplier")

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_no = db.Column(db.String(50), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.id"))
    invoice_date = db.Column(db.Date, default=date.today)
    due_date = db.Column(db.Date)
    amount = db.Column(db.Float, nullable=False)
    paid = db.Column(db.Float, default=0)
    status = db.Column(db.String(30), default="Pending")
    notes = db.Column(db.String(255), default="")
    customer = db.relationship("Customer")

class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    business_name = db.Column(db.String(150), default="My Business")
    owner_name = db.Column(db.String(120), default="Administrator")
    currency = db.Column(db.String(10), default="₹")
    date_format = db.Column(db.String(30), default="%d-%m-%Y")
    notifications = db.Column(db.Boolean, default=True)

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login", next=request.path))
        return fn(*args, **kwargs)
    return wrapper

def seed():
    db.create_all()
    if not User.query.first():
        db.session.add(User(username="admin", password="admin123", name="Priya Choudhury"))
    if not Setting.query.first():
        db.session.add(Setting(business_name="Accounting System", owner_name="Priya Choudhury"))
    if Account.query.count() == 0:
        accounts = [
            Account(name="Cash", type="Cash", opening_balance=10000, description="Cash account"),
            Account(name="Bank Account", type="Bank", opening_balance=25000, description="Primary bank account"),
            Account(name="Sales", type="Income", opening_balance=0, description="Sales income"),
            Account(name="Office Expenses", type="Expense", opening_balance=0, description="Office expenses"),
        ]
        db.session.add_all(accounts)
        db.session.commit()
        cash = Account.query.filter_by(name="Cash").first()
        bank = Account.query.filter_by(name="Bank Account").first()
        db.session.add_all([
            Transaction(tx_date=date.today(), amount=50000, tx_type="Income", category="Sales",
                        description="Sample sales receipt", payment_method="Bank Transfer",
                        reference="DEMO-001", account_id=bank.id),
            Transaction(tx_date=date.today(), amount=20000, tx_type="Expense", category="Materials",
                        description="Sample purchase expense", payment_method="Cash",
                        reference="DEMO-002", account_id=cash.id),
        ])
        db.session.commit()

with app.app_context():
    seed()

@app.context_processor
def inject_globals():
    setting = Setting.query.first()
    return {"setting": setting, "today": date.today()}

@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("login.html", landing=True)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = User.query.filter_by(username=request.form.get("username","").strip()).first()
        if u and u.password == request.form.get("password",""):
            session["user_id"] = u.id
            session["user_name"] = u.name
            return redirect(request.args.get("next") or url_for("dashboard"))
        flash("Invalid username or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

def totals():
    inc = db.session.query(db.func.coalesce(db.func.sum(Transaction.amount),0)).filter(Transaction.tx_type=="Income").scalar() or 0
    exp = db.session.query(db.func.coalesce(db.func.sum(Transaction.amount),0)).filter(Transaction.tx_type=="Expense").scalar() or 0
    opening = db.session.query(db.func.coalesce(db.func.sum(Account.opening_balance),0)).scalar() or 0
    return float(inc), float(exp), float(opening + inc - exp)

@app.route("/dashboard")
@login_required
def dashboard():
    inc, exp, bal = totals()
    txs = Transaction.query.order_by(Transaction.tx_date.desc(), Transaction.id.desc()).limit(8).all()
    invoices = Invoice.query.filter(Invoice.status != "Paid").order_by(Invoice.due_date.asc()).limit(5).all()
    return render_template("dashboard.html", income=inc, expenses=exp, balance=bal, transactions=txs, invoices=invoices, account_count=Account.query.count())

@app.route("/accounts", methods=["GET","POST"])
@login_required
def accounts():
    if request.method == "POST":
        name = request.form.get("name","").strip()
        typ = request.form.get("type","").strip()
        if not name or not typ:
            flash("Account name and type are required.", "danger")
        else:
            db.session.add(Account(name=name, type=typ, opening_balance=float(request.form.get("opening_balance") or 0),
                                   description=request.form.get("description","").strip()))
            db.session.commit()
            flash("Account created successfully.", "success")
        return redirect(url_for("accounts"))
    rows = Account.query.order_by(Account.name).all()
    return render_template("accounts.html", accounts=rows)

@app.route("/accounts/delete/<int:id>", methods=["POST"])
@login_required
def delete_account(id):
    a = db.get_or_404(Account,id)
    if a.transactions:
        flash("Account cannot be deleted while it has transactions.", "danger")
    else:
        db.session.delete(a); db.session.commit(); flash("Account deleted.", "success")
    return redirect(url_for("accounts"))

def tx_query():
    q = Transaction.query
    search = request.args.get("search","").strip()
    typ = request.args.get("type","")
    account_id = request.args.get("account_id","")
    if search:
        like = f"%{search}%"
        q = q.filter(db.or_(Transaction.description.ilike(like), Transaction.category.ilike(like), Transaction.reference.ilike(like)))
    if typ: q = q.filter_by(tx_type=typ)
    if account_id: q = q.filter_by(account_id=int(account_id))
    return q.order_by(Transaction.tx_date.desc(), Transaction.id.desc())

@app.route("/transactions", methods=["GET","POST"])
@login_required
def transactions():
    if request.method == "POST":
        try:
            amount = float(request.form.get("amount",""))
            if amount <= 0: raise ValueError()
            account_id = int(request.form.get("account_id",""))
            if not db.session.get(Account, account_id): raise ValueError()
            tx = Transaction(
                tx_date=datetime.strptime(request.form.get("tx_date"), "%Y-%m-%d").date(),
                amount=amount, tx_type=request.form.get("tx_type"),
                category=request.form.get("category","General"), description=request.form.get("description",""),
                payment_method=request.form.get("payment_method","Cash"), reference=request.form.get("reference",""),
                account_id=account_id,
                customer_id=int(request.form["customer_id"]) if request.form.get("customer_id") else None,
                supplier_id=int(request.form["supplier_id"]) if request.form.get("supplier_id") else None
            )
            db.session.add(tx); db.session.commit(); flash("Transaction saved and ledger updated.", "success")
        except Exception:
            flash("Please enter valid transaction details.", "danger")
        return redirect(url_for("transactions"))
    return render_template("transactions.html", transactions=tx_query().all(),
                           accounts=Account.query.order_by(Account.name).all(),
                           customers=Customer.query.order_by(Customer.name).all(),
                           suppliers=Supplier.query.order_by(Supplier.name).all(),
                           filter_search=request.args.get("search",""), filter_type=request.args.get("type",""),
                           filter_account=request.args.get("account_id",""))

@app.route("/transactions/delete/<int:id>", methods=["POST"])
@login_required
def delete_transaction(id):
    tx=db.get_or_404(Transaction,id); db.session.delete(tx); db.session.commit()
    flash("Transaction deleted.", "success"); return redirect(url_for("transactions"))

@app.route("/customers", methods=["GET","POST"])
@login_required
def customers():
    if request.method=="POST":
        name=request.form.get("name","").strip()
        if not name: flash("Customer name is required.","danger")
        else:
            db.session.add(Customer(name=name,phone=request.form.get("phone",""),email=request.form.get("email",""),address=request.form.get("address","")))
            db.session.commit(); flash("Customer added.","success")
        return redirect(url_for("customers"))
    return render_template("contacts.html", title="Customers", entity="customer", rows=Customer.query.order_by(Customer.name).all())

@app.route("/suppliers", methods=["GET","POST"])
@login_required
def suppliers():
    if request.method=="POST":
        name=request.form.get("name","").strip()
        if not name: flash("Supplier name is required.","danger")
        else:
            db.session.add(Supplier(name=name,phone=request.form.get("phone",""),email=request.form.get("email",""),address=request.form.get("address","")))
            db.session.commit(); flash("Supplier added.","success")
        return redirect(url_for("suppliers"))
    return render_template("contacts.html", title="Suppliers", entity="supplier", rows=Supplier.query.order_by(Supplier.name).all())

@app.route("/contacts/delete/<entity>/<int:id>", methods=["POST"])
@login_required
def delete_contact(entity,id):
    cls = Customer if entity=="customer" else Supplier
    obj=db.get_or_404(cls,id)
    if entity=="customer" and Transaction.query.filter_by(customer_id=id).first():
        flash("Customer is linked to transactions and cannot be deleted.","danger")
    elif entity=="supplier" and Transaction.query.filter_by(supplier_id=id).first():
        flash("Supplier is linked to transactions and cannot be deleted.","danger")
    else:
        db.session.delete(obj); db.session.commit(); flash("Record deleted.","success")
    return redirect(url_for("customers" if entity=="customer" else "suppliers"))

@app.route("/invoices", methods=["GET","POST"])
@login_required
def invoices():
    if request.method=="POST":
        try:
            amount=float(request.form.get("amount",""))
            due=datetime.strptime(request.form.get("due_date"),"%Y-%m-%d").date()
            inv=Invoice(invoice_no=request.form.get("invoice_no","").strip(), customer_id=int(request.form.get("customer_id")),
                        invoice_date=datetime.strptime(request.form.get("invoice_date"),"%Y-%m-%d").date(),
                        due_date=due, amount=amount, notes=request.form.get("notes",""))
            if not inv.invoice_no or amount<=0: raise ValueError()
            db.session.add(inv); db.session.commit(); flash("Invoice created.","success")
        except Exception:
            db.session.rollback(); flash("Enter valid invoice details; invoice number must be unique.","danger")
        return redirect(url_for("invoices"))
    return render_template("invoices.html", invoices=Invoice.query.order_by(Invoice.invoice_date.desc()).all(),
                           customers=Customer.query.order_by(Customer.name).all())

@app.route("/invoices/pay/<int:id>", methods=["POST"])
@login_required
def pay_invoice(id):
    inv=db.get_or_404(Invoice,id)
    try:
        payment=float(request.form.get("payment","0"))
        if payment<=0 or payment > inv.amount-inv.paid: raise ValueError()
        inv.paid += payment
        inv.status = "Paid" if inv.paid >= inv.amount else "Partially Paid"
        db.session.commit(); flash("Invoice payment recorded.","success")
    except Exception: flash("Invalid payment amount.","danger")
    return redirect(url_for("invoices"))

@app.route("/ledger/<int:account_id>")
@login_required
def ledger(account_id):
    account=db.get_or_404(Account,account_id)
    rows=Transaction.query.filter_by(account_id=account_id).order_by(Transaction.tx_date,Transaction.id).all()
    running=account.opening_balance
    entries=[]
    for tx in rows:
        running += tx.amount if tx.tx_type=="Income" else -tx.amount if tx.tx_type=="Expense" else 0
        entries.append((tx,running))
    return render_template("ledger.html", account=account, entries=entries, balance=running)

@app.route("/reports")
@login_required
def reports():
    inc,exp,bal=totals()
    bycat={}
    for tx in Transaction.query.filter_by(tx_type="Expense").all():
        bycat[tx.category]=bycat.get(tx.category,0)+tx.amount
    return render_template("reports.html", income=inc, expenses=exp, balance=bal, bycat=sorted(bycat.items(), key=lambda x:-x[1]),
                           accounts=Account.query.order_by(Account.name).all())

@app.route("/reports/export")
@login_required
def export_report():
    out=io.StringIO(); w=csv.writer(out)
    w.writerow(["Date","Type","Amount","Account","Category","Description","Payment Method","Reference"])
    for tx in Transaction.query.order_by(Transaction.tx_date).all():
        w.writerow([tx.tx_date.isoformat(),tx.tx_type,tx.amount,tx.account.name,tx.category,tx.description,tx.payment_method,tx.reference])
    return Response(out.getvalue(), mimetype="text/csv", headers={"Content-Disposition":"attachment; filename=accounting_transactions.csv"})

@app.route("/settings", methods=["GET","POST"])
@login_required
def settings():
    s=Setting.query.first()
    if request.method=="POST":
        s.business_name=request.form.get("business_name","Accounting System")
        s.owner_name=request.form.get("owner_name","")
        s.currency=request.form.get("currency","₹")
        s.date_format=request.form.get("date_format","%d-%m-%Y")
        s.notifications=bool(request.form.get("notifications"))
        db.session.commit(); flash("Settings saved.","success"); return redirect(url_for("settings"))
    return render_template("settings.html", settings=s)

@app.route("/api/summary")
@login_required
def api_summary():
    inc,exp,bal=totals()
    return jsonify({"income":inc,"expenses":exp,"balance":bal,"transactions":Transaction.query.count(),"accounts":Account.query.count()})

if __name__=="__main__":
    app.run(debug=True)
