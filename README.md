# Accounting System

A runnable Flask + SQLite implementation of the Accounting System project report.

## Features
- Login / logout
- Dashboard with income, expenses, balance, recent transactions
- Account management with automatic balance calculation
- Transaction management with validation, search and filtering
- Customer and supplier management
- Invoice and payment tracking
- Ledger view
- Financial reports and CSV export
- Settings / business profile
- Persistent SQLite database
- Responsive desktop/mobile UI

## Run
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

Default demo login:
- Username: admin
- Password: admin123

The application creates `accounting.db` automatically.

## Database
SQLite is used for a zero-configuration local demo. The report leaves the database technology open; the application layer is structured so the database URL can be changed later.

## Scope note
Online banking synchronization, payroll, statutory tax filing, payment gateways, multi-user collaboration and cloud backup are intentionally outside this implementation's current scope, matching the report.
