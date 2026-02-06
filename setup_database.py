"""
Setup SQLite database for legal agent with proper schema and mock data
"""
import sqlite3
from datetime import datetime, timedelta
import json

def create_database():
    """Create SQLite database with legal data schema"""
    conn = sqlite3.connect('legal_cases.db')
    cursor = conn.cursor()
    
    # Create attorneys table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attorneys (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        specialty TEXT NOT NULL,
        hourly_rate REAL NOT NULL,
        years_experience INTEGER NOT NULL,
        bar_number TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT NOT NULL,
        available INTEGER NOT NULL DEFAULT 1
    )
    ''')
    
    # Create clients table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS clients (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT,
        company TEXT,
        created_date TEXT NOT NULL
    )
    ''')
    
    # Create cases table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cases (
        id TEXT PRIMARY KEY,
        case_number TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        type TEXT NOT NULL,
        status TEXT NOT NULL,
        filed_date TEXT NOT NULL,
        attorney_id TEXT NOT NULL,
        client TEXT NOT NULL,
        next_hearing TEXT,
        estimated_value REAL,
        FOREIGN KEY (attorney_id) REFERENCES attorneys(id)
    )
    ''')
    
    # Create invoices table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS invoices (
        id TEXT PRIMARY KEY,
        invoice_number TEXT UNIQUE NOT NULL,
        client_name TEXT NOT NULL,
        date TEXT NOT NULL,
        status TEXT NOT NULL,
        total REAL NOT NULL
    )
    ''')
    
    # Create invoice items table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS invoice_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id TEXT NOT NULL,
        description TEXT NOT NULL,
        amount REAL NOT NULL,
        FOREIGN KEY (invoice_id) REFERENCES invoices(id)
    )
    ''')
    
    # Create legal rates table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS legal_rates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service TEXT NOT NULL,
        rate REAL NOT NULL,
        unit TEXT NOT NULL DEFAULT 'hour'
    )
    ''')
    
    conn.commit()
    return conn

def populate_mock_data(conn):
    """Populate database with mock data"""
    cursor = conn.cursor()
    
    # Insert attorneys
    attorneys = [
        ('att-001', 'Sarah Johnson', 'Corporate Law', 500.0, 15, 'CA123456', 'sarah.johnson@lawfirm.com', '+1-555-0101', 1),
        ('att-002', 'Michael Chen', 'Intellectual Property', 450.0, 12, 'CA123457', 'michael.chen@lawfirm.com', '+1-555-0102', 1),
        ('att-003', 'Emily Rodriguez', 'Employment Law', 425.0, 10, 'CA123458', 'emily.rodriguez@lawfirm.com', '+1-555-0103', 1),
        ('att-004', 'David Kim', 'Real Estate', 400.0, 8, 'CA123459', 'david.kim@lawfirm.com', '+1-555-0104', 0),
        ('att-005', 'Jessica Williams', 'Contract Law', 475.0, 14, 'CA123460', 'jessica.williams@lawfirm.com', '+1-555-0105', 1)
    ]
    cursor.executemany('INSERT OR IGNORE INTO attorneys VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', attorneys)
    
    # Insert clients
    clients = [
        ('client-001', 'John Smith', 'john.smith@email.com', '+1-555-1001', 'Smith Corp', '2025-01-15'),
        ('client-002', 'ABC Corporation', 'legal@abccorp.com', '+1-555-1002', 'ABC Corporation', '2025-02-01'),
        ('client-003', 'TechSolutions Inc', 'info@techsolutions.com', '+1-555-1003', 'TechSolutions Inc', '2025-03-10'),
        ('client-004', 'Global Ventures LLC', 'contact@globalventures.com', '+1-555-1004', 'Global Ventures LLC', '2025-06-20')
    ]
    cursor.executemany('INSERT OR IGNORE INTO clients VALUES (?, ?, ?, ?, ?, ?)', clients)
    
    # Insert cases
    cases = [
        ('case-001', '2025-CV-10001', 'Smith v. Jones', 'Contract Dispute', 'Active', '2025-06-15', 'att-001', 'John Smith', '2026-03-01', 250000.0),
        ('case-002', '2025-CV-10002', 'ABC Corp v. XYZ Inc', 'Intellectual Property', 'Active', '2025-08-22', 'att-002', 'ABC Corporation', '2026-02-15', 500000.0),
        ('case-003', '2025-CV-10003', 'Employee Dispute Matter', 'Employment Law', 'Closed', '2025-09-10', 'att-003', 'TechSolutions Inc', None, 75000.0),
        ('case-004', '2025-RE-10004', 'Property Line Dispute', 'Real Estate', 'Active', '2025-11-05', 'att-004', 'Global Ventures LLC', '2026-04-10', 150000.0)
    ]
    cursor.executemany('INSERT OR IGNORE INTO cases VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', cases)
    
    # Insert invoices
    invoices = [
        ('inv-001', 'INV-2026-001', 'TechSolutions Consulting', '2026-01-15', 'PAID', 5700.0),
        ('inv-002', 'INV-2026-002', 'ABC Corporation', '2026-01-20', 'OUTSTANDING', 13600.0),
        ('inv-003', 'INV-2026-003', 'TechStart Industries', '2026-02-01', 'OUTSTANDING', 4300.0)
    ]
    cursor.executemany('INSERT OR IGNORE INTO invoices VALUES (?, ?, ?, ?, ?, ?)', invoices)
    
    # Insert invoice items
    invoice_items = [
        ('inv-001', 'Professional Services Invoice from TechSolutions Consulting', 5700.0),
        ('inv-002', 'Legal Consultation', 3400.0),
        ('inv-002', 'Document Review', 4800.0),
        ('inv-002', 'Court Appearance', 5400.0),
        ('inv-003', 'Contract Drafting', 2800.0),
        ('inv-003', 'Legal Review', 1500.0)
    ]
    cursor.executemany('INSERT OR IGNORE INTO invoice_items (invoice_id, description, amount) VALUES (?, ?, ?)', invoice_items)
    
    # Insert legal rates
    legal_rates = [
        ('Partner Attorney Rate', 500.0, 'hour'),
        ('Senior Attorney Rate', 400.0, 'hour'),
        ('Junior Attorney Rate', 250.0, 'hour'),
        ('Paralegal Rate', 150.0, 'hour'),
        ('Document Review', 200.0, 'hour'),
        ('Court Appearance', 600.0, 'hour'),
        ('Consultation', 350.0, 'hour')
    ]
    cursor.executemany('INSERT OR IGNORE INTO legal_rates (service, rate, unit) VALUES (?, ?, ?)', legal_rates)
    
    conn.commit()
    print("✓ Database created and populated with mock data")
    print(f"  - {len(attorneys)} attorneys")
    print(f"  - {len(clients)} clients")
    print(f"  - {len(cases)} cases")
    print(f"  - {len(invoices)} invoices")
    print(f"  - {len(legal_rates)} legal rates")

if __name__ == '__main__':
    conn = create_database()
    populate_mock_data(conn)
    conn.close()
    print("\nDatabase 'legal_cases.db' ready for use!")
