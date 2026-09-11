import sqlite3
import hashlib
import os
import sys
from pathlib import Path


def _app_dir() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent


DB_PATH = _app_dir() / "pharmacy.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            unit TEXT NOT NULL,
            quantity REAL DEFAULT 0,
            purchase_price REAL DEFAULT 0,
            selling_price REAL DEFAULT 0,
            product_type TEXT DEFAULT 'بيطري',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT DEFAULT '',
            address TEXT DEFAULT '',
            total_debt REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT DEFAULT '',
            address TEXT DEFAULT '',
            total_debt REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            customer_name TEXT DEFAULT 'عميل نقدي',
            date TEXT DEFAULT (date('now')),
            total_amount REAL DEFAULT 0,
            paid_amount REAL DEFAULT 0,
            remaining REAL DEFAULT 0,
            payment_type TEXT DEFAULT 'cash',
            invoice_type TEXT DEFAULT 'بيطري',
            notes TEXT DEFAULT '',
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        );

        CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit_name TEXT DEFAULT '',
            unit_price REAL NOT NULL,
            total REAL NOT NULL,
            FOREIGN KEY (sale_id) REFERENCES sales(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        );

        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier TEXT DEFAULT '',
            date TEXT DEFAULT (date('now')),
            total_amount REAL DEFAULT 0,
            invoice_type TEXT DEFAULT 'بيطري',
            notes TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS purchase_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit_name TEXT DEFAULT '',
            unit_price REAL NOT NULL,
            total REAL NOT NULL,
            FOREIGN KEY (purchase_id) REFERENCES purchases(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        );

        CREATE TABLE IF NOT EXISTS sale_returns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            customer_name TEXT DEFAULT '',
            date TEXT DEFAULT (date('now')),
            total_amount REAL DEFAULT 0,
            invoice_type TEXT DEFAULT 'بيطري',
            notes TEXT DEFAULT '',
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        );

        CREATE TABLE IF NOT EXISTS sale_return_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            return_id INTEGER NOT NULL,
            product_id INTEGER,
            product_name TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit_name TEXT DEFAULT '',
            unit_price REAL NOT NULL,
            total REAL NOT NULL,
            FOREIGN KEY (return_id) REFERENCES sale_returns(id)
        );

        CREATE TABLE IF NOT EXISTS purchase_returns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER,
            supplier_name TEXT DEFAULT '',
            date TEXT DEFAULT (date('now')),
            total_amount REAL DEFAULT 0,
            invoice_type TEXT DEFAULT 'بيطري',
            notes TEXT DEFAULT '',
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
        );

        CREATE TABLE IF NOT EXISTS purchase_return_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            return_id INTEGER NOT NULL,
            product_id INTEGER,
            product_name TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit_name TEXT DEFAULT '',
            unit_price REAL NOT NULL,
            total REAL NOT NULL,
            FOREIGN KEY (return_id) REFERENCES purchase_returns(id)
        );

        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            date TEXT DEFAULT (date('now')),
            notes TEXT DEFAULT '',
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        );

        CREATE TABLE IF NOT EXISTS supplier_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            date TEXT DEFAULT (date('now')),
            notes TEXT DEFAULT '',
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
        );

        CREATE TABLE IF NOT EXISTS product_units (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            unit_name TEXT NOT NULL,
            selling_price REAL NOT NULL DEFAULT 0,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS product_batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            quantity REAL NOT NULL DEFAULT 0,
            purchase_price REAL DEFAULT 0,
            expiry_date TEXT,
            purchase_date TEXT DEFAULT (date('now')),
            FOREIGN KEY (product_id) REFERENCES products(id)
        );
    """)
    conn.commit()

    # Migrate existing databases
    for col_sql in [
        "ALTER TABLE purchases ADD COLUMN supplier_id INTEGER REFERENCES suppliers(id)",
        "ALTER TABLE purchases ADD COLUMN paid_amount REAL DEFAULT 0",
        "ALTER TABLE purchases ADD COLUMN payment_type TEXT DEFAULT 'cash'",
        "ALTER TABLE purchases ADD COLUMN invoice_type TEXT DEFAULT 'بيطري'",
        "ALTER TABLE sales ADD COLUMN invoice_type TEXT DEFAULT 'بيطري'",
        "ALTER TABLE products ADD COLUMN product_type TEXT DEFAULT 'بيطري'",
        "ALTER TABLE sale_items ADD COLUMN unit_name TEXT DEFAULT ''",
        "ALTER TABLE purchase_items ADD COLUMN unit_name TEXT DEFAULT ''",
    ]:
        try:
            conn.execute(col_sql)
            conn.commit()
        except Exception:
            pass

    conn.close()


# ===== Products =====

def get_all_products():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM products ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def search_products(query):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM products WHERE name LIKE ? ORDER BY name",
        (f"%{query}%",)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_product(name, unit, quantity, purchase_price, selling_price, product_type='بيطري'):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO products (name, unit, quantity, purchase_price, selling_price, product_type) VALUES (?, ?, ?, ?, ?, ?)",
        (name, unit, quantity, purchase_price, selling_price, product_type)
    )
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id


def update_product(pid, name, unit, quantity, purchase_price, selling_price, product_type='بيطري'):
    conn = get_connection()
    conn.execute(
        "UPDATE products SET name=?, unit=?, quantity=?, purchase_price=?, selling_price=?, product_type=? WHERE id=?",
        (name, unit, quantity, purchase_price, selling_price, product_type, pid)
    )
    conn.commit()
    conn.close()


def delete_product(pid):
    conn = get_connection()
    conn.execute("DELETE FROM products WHERE id=?", (pid,))
    conn.commit()
    conn.close()


# ===== Product Units =====

def get_product_units(product_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM product_units WHERE product_id=? ORDER BY id",
        (product_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_product_unit(product_id, unit_name, selling_price):
    conn = get_connection()
    conn.execute(
        "INSERT INTO product_units (product_id, unit_name, selling_price) VALUES (?, ?, ?)",
        (product_id, unit_name, selling_price)
    )
    conn.commit()
    conn.close()


def delete_product_unit(unit_id):
    conn = get_connection()
    conn.execute("DELETE FROM product_units WHERE id=?", (unit_id,))
    conn.commit()
    conn.close()


# ===== Customers =====

def get_all_customers():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM customers ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_customer(name, phone='', address=''):
    conn = get_connection()
    conn.execute(
        "INSERT INTO customers (name, phone, address) VALUES (?, ?, ?)",
        (name, phone, address)
    )
    conn.commit()
    conn.close()


def update_customer(cid, name, phone='', address=''):
    conn = get_connection()
    conn.execute(
        "UPDATE customers SET name=?, phone=?, address=? WHERE id=?",
        (name, phone, address, cid)
    )
    conn.commit()
    conn.close()


def delete_customer(cid):
    conn = get_connection()
    conn.execute("DELETE FROM customers WHERE id=?", (cid,))
    conn.commit()
    conn.close()


def get_customer_history(customer_id):
    conn = get_connection()
    sales = conn.execute(
        "SELECT * FROM sales WHERE customer_id=? ORDER BY date DESC, id DESC",
        (customer_id,)
    ).fetchall()
    payments = conn.execute(
        "SELECT * FROM payments WHERE customer_id=? ORDER BY date DESC, id DESC",
        (customer_id,)
    ).fetchall()
    conn.close()
    return [dict(s) for s in sales], [dict(p) for p in payments]


def get_customer_sales_items(customer_id):
    conn = get_connection()
    rows = conn.execute("""
        SELECT si.product_name, si.quantity, si.unit_price, si.total,
               COALESCE(si.unit_name, '') as unit_name,
               s.date, s.id as sale_id,
               COALESCE(s.invoice_type, 'بيطري') as invoice_type,
               s.payment_type, s.total_amount as invoice_total
        FROM sale_items si
        JOIN sales s ON si.sale_id = s.id
        WHERE s.customer_id = ?
        ORDER BY s.date DESC, s.id DESC, si.id
    """, (customer_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_payment(customer_id, amount, notes, date=None):
    conn = get_connection()
    if date:
        conn.execute(
            "INSERT INTO payments (customer_id, amount, notes, date) VALUES (?, ?, ?, ?)",
            (customer_id, amount, notes, date)
        )
    else:
        conn.execute(
            "INSERT INTO payments (customer_id, amount, notes) VALUES (?, ?, ?)",
            (customer_id, amount, notes)
        )
    conn.execute(
        "UPDATE customers SET total_debt = MAX(0, total_debt - ?) WHERE id=?",
        (amount, customer_id)
    )
    conn.commit()
    conn.close()


def delete_payment(payment_id):
    conn = get_connection()
    p = conn.execute("SELECT customer_id, amount FROM payments WHERE id=?", (payment_id,)).fetchone()
    if p:
        conn.execute("UPDATE customers SET total_debt = total_debt + ? WHERE id=?", (p['amount'], p['customer_id']))
        conn.execute("DELETE FROM payments WHERE id=?", (payment_id,))
    conn.commit()
    conn.close()


# ===== Batch / FIFO helpers =====

def _consume_batches(cursor, product_id, qty_to_consume):
    """Deduct qty_to_consume from product_batches FIFO (earliest expiry first)."""
    batches = cursor.execute("""
        SELECT id, quantity FROM product_batches
        WHERE product_id = ? AND quantity > 0
        ORDER BY CASE WHEN expiry_date IS NULL THEN '9999-99-99' ELSE expiry_date END ASC,
                 purchase_date ASC
    """, (product_id,)).fetchall()
    remaining = qty_to_consume
    for batch in batches:
        if remaining <= 0:
            break
        take = min(batch['quantity'], remaining)
        cursor.execute(
            "UPDATE product_batches SET quantity = quantity - ? WHERE id = ?",
            (take, batch['id'])
        )
        remaining -= take


def get_expiring_batches(days=30):
    """Return products that have batches expiring within `days` days (incl. already expired)."""
    from datetime import date, timedelta
    cutoff = (date.today() + timedelta(days=days)).strftime('%Y-%m-%d')
    conn = get_connection()
    rows = conn.execute("""
        SELECT p.id AS product_id, p.name, p.unit,
               ROUND(SUM(pb.quantity), 2) AS total_qty,
               MIN(pb.expiry_date) AS expiry_date
        FROM product_batches pb
        JOIN products p ON p.id = pb.product_id
        WHERE pb.expiry_date IS NOT NULL
          AND pb.expiry_date <= ?
          AND pb.quantity > 0
        GROUP BY p.id
        ORDER BY expiry_date ASC
    """, (cutoff,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_product_batches(product_id):
    """Return active batches for a product ordered by expiry date (FIFO order)."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT id, quantity, purchase_price, expiry_date, purchase_date
        FROM product_batches
        WHERE product_id = ? AND quantity > 0
        ORDER BY CASE WHEN expiry_date IS NULL THEN '9999-99-99' ELSE expiry_date END ASC,
                 purchase_date ASC
    """, (product_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def set_product_expiry(product_id, expiry_date, current_qty):
    """Set or update the expiry date for a product.
    - No batches → creates one batch with current_qty and expiry_date.
    - Batches exist → updates the first (nearest) batch's expiry date.
    Pass expiry_date=None to clear the expiry on the first batch.
    """
    conn = get_connection()
    cur  = conn.cursor()
    batches = cur.execute(
        "SELECT id FROM product_batches WHERE product_id = ? AND quantity > 0 "
        "ORDER BY CASE WHEN expiry_date IS NULL THEN '9999-99-99' ELSE expiry_date END ASC",
        (product_id,)
    ).fetchall()
    if not batches:
        cur.execute(
            "INSERT INTO product_batches (product_id, quantity, expiry_date) VALUES (?, ?, ?)",
            (product_id, current_qty, expiry_date)
        )
    else:
        cur.execute(
            "UPDATE product_batches SET expiry_date = ? WHERE id = ?",
            (expiry_date, batches[0]['id'])
        )
    conn.commit()
    conn.close()


def get_product_nearest_expiries():
    """Return {product_id: nearest_expiry_date_str} for products with active batches that have expiry dates."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT product_id, MIN(expiry_date) AS nearest_expiry
        FROM product_batches
        WHERE expiry_date IS NOT NULL AND quantity > 0
        GROUP BY product_id
    """).fetchall()
    conn.close()
    return {r['product_id']: r['nearest_expiry'] for r in rows}


# ===== Sales =====

def create_sale(customer_id, customer_name, items, total_amount, paid_amount, payment_type, notes, invoice_type='بيطري'):
    remaining = max(0.0, total_amount - paid_amount)
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """INSERT INTO sales (customer_id, customer_name, total_amount, paid_amount, remaining, payment_type, invoice_type, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (customer_id, customer_name, total_amount, paid_amount, remaining, payment_type, invoice_type, notes)
    )
    sale_id = cursor.lastrowid

    for item in items:
        cursor.execute(
            """INSERT INTO sale_items (sale_id, product_id, product_name, quantity, unit_name, unit_price, total)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (sale_id, item['product_id'], item['product_name'],
             item['quantity'], item.get('unit_name', ''), item['unit_price'], item['total'])
        )
        cursor.execute(
            "UPDATE products SET quantity = MAX(0, quantity - ?) WHERE id=?",
            (item['quantity'], item['product_id'])
        )
        if item.get('product_id'):
            _consume_batches(cursor, item['product_id'], item['quantity'])

    if customer_id and remaining > 0:
        cursor.execute(
            "UPDATE customers SET total_debt = total_debt + ? WHERE id=?",
            (remaining, customer_id)
        )

    conn.commit()
    conn.close()
    return sale_id


def get_all_sales():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM sales ORDER BY date DESC, id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_sale_items(sale_id):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM sale_items WHERE sale_id=?", (sale_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ===== Suppliers =====

def get_all_suppliers():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM suppliers ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_supplier(name, phone, address):
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO suppliers (name, phone, address) VALUES (?, ?, ?)",
        (name, phone, address)
    )
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id


def update_supplier(sid, name, phone, address):
    conn = get_connection()
    conn.execute(
        "UPDATE suppliers SET name=?, phone=?, address=? WHERE id=?",
        (name, phone, address, sid)
    )
    conn.commit()
    conn.close()


def delete_supplier(sid):
    conn = get_connection()
    conn.execute("DELETE FROM suppliers WHERE id=?", (sid,))
    conn.commit()
    conn.close()


def get_supplier_history(supplier_id):
    conn = get_connection()
    purchases = conn.execute(
        "SELECT * FROM purchases WHERE supplier_id=? ORDER BY date DESC, id DESC",
        (supplier_id,)
    ).fetchall()
    payments = conn.execute(
        "SELECT * FROM supplier_payments WHERE supplier_id=? ORDER BY date DESC, id DESC",
        (supplier_id,)
    ).fetchall()
    conn.close()
    return [dict(p) for p in purchases], [dict(p) for p in payments]


def add_supplier_payment(supplier_id, amount, notes, date=None):
    conn = get_connection()
    if date:
        conn.execute(
            "INSERT INTO supplier_payments (supplier_id, amount, notes, date) VALUES (?, ?, ?, ?)",
            (supplier_id, amount, notes, date)
        )
    else:
        conn.execute(
            "INSERT INTO supplier_payments (supplier_id, amount, notes) VALUES (?, ?, ?)",
            (supplier_id, amount, notes)
        )
    conn.execute(
        "UPDATE suppliers SET total_debt = MAX(0, total_debt - ?) WHERE id=?",
        (amount, supplier_id)
    )
    conn.commit()
    conn.close()


def delete_supplier_payment(payment_id):
    conn = get_connection()
    p = conn.execute("SELECT supplier_id, amount FROM supplier_payments WHERE id=?", (payment_id,)).fetchone()
    if p:
        conn.execute("UPDATE suppliers SET total_debt = total_debt + ? WHERE id=?", (p['amount'], p['supplier_id']))
        conn.execute("DELETE FROM supplier_payments WHERE id=?", (payment_id,))
    conn.commit()
    conn.close()


# ===== Purchases =====

def create_sale_return(customer_id, customer_name, items, total_amount, invoice_type, notes):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sale_returns (customer_id, customer_name, total_amount, invoice_type, notes) VALUES (?, ?, ?, ?, ?)",
        (customer_id, customer_name, total_amount, invoice_type, notes)
    )
    return_id = cursor.lastrowid
    for item in items:
        cursor.execute(
            "INSERT INTO sale_return_items (return_id, product_id, product_name, quantity, unit_name, unit_price, total) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (return_id, item.get('product_id'), item['product_name'],
             item['quantity'], item.get('unit_name', ''), item['unit_price'], item['total'])
        )
        if item.get('product_id'):
            cursor.execute("UPDATE products SET quantity = quantity + ? WHERE id=?",
                           (item['quantity'], item['product_id']))
    if customer_id and total_amount > 0:
        cursor.execute("UPDATE customers SET total_debt = MAX(0, total_debt - ?) WHERE id=?",
                       (total_amount, customer_id))
    conn.commit()
    conn.close()
    return return_id


def get_all_sale_returns():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM sale_returns ORDER BY date DESC, id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_sale_return_items(return_id):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM sale_return_items WHERE return_id=?", (return_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_purchase_return(supplier_id, supplier_name, items, total_amount, invoice_type, notes):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO purchase_returns (supplier_id, supplier_name, total_amount, invoice_type, notes) VALUES (?, ?, ?, ?, ?)",
        (supplier_id, supplier_name, total_amount, invoice_type, notes)
    )
    return_id = cursor.lastrowid
    for item in items:
        cursor.execute(
            "INSERT INTO purchase_return_items (return_id, product_id, product_name, quantity, unit_name, unit_price, total) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (return_id, item.get('product_id'), item['product_name'],
             item['quantity'], item.get('unit_name', ''), item['unit_price'], item['total'])
        )
        if item.get('product_id'):
            cursor.execute("UPDATE products SET quantity = MAX(0, quantity - ?) WHERE id=?",
                           (item['quantity'], item['product_id']))
    if supplier_id and total_amount > 0:
        cursor.execute("UPDATE suppliers SET total_debt = MAX(0, total_debt - ?) WHERE id=?",
                       (total_amount, supplier_id))
    conn.commit()
    conn.close()
    return return_id


def get_all_purchase_returns():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM purchase_returns ORDER BY date DESC, id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_purchase_return_items(return_id):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM purchase_return_items WHERE return_id=?", (return_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_payments_combined():
    conn = get_connection()
    cp = conn.execute("""
        SELECT p.id, p.amount, p.date, p.notes,
               COALESCE(c.name, '') as entity_name, 'customer' as entity_type,
               p.customer_id as entity_id
        FROM payments p
        LEFT JOIN customers c ON p.customer_id = c.id
        ORDER BY p.date DESC, p.id DESC
    """).fetchall()
    sp = conn.execute("""
        SELECT sp.id, sp.amount, sp.date, sp.notes,
               COALESCE(s.name, '') as entity_name, 'supplier' as entity_type,
               sp.supplier_id as entity_id
        FROM supplier_payments sp
        LEFT JOIN suppliers s ON sp.supplier_id = s.id
        ORDER BY sp.date DESC, sp.id DESC
    """).fetchall()
    conn.close()
    all_p = [dict(r) for r in cp] + [dict(r) for r in sp]
    all_p.sort(key=lambda x: (x['date'], x['id']), reverse=True)
    return all_p


def get_customer_account(customer_id, date_from, date_to):
    conn = get_connection()
    sales = conn.execute("""
        SELECT s.id, s.date, s.total_amount, s.paid_amount, s.remaining,
               s.payment_type, s.invoice_type, s.customer_name,
               GROUP_CONCAT(si.product_name || ' ×' || si.quantity, ', ') as items_summary
        FROM sales s
        LEFT JOIN sale_items si ON si.sale_id = s.id
        WHERE s.customer_id = ? AND s.date BETWEEN ? AND ?
        GROUP BY s.id
        ORDER BY s.date DESC, s.id DESC
    """, (customer_id, date_from, date_to)).fetchall()

    returns = conn.execute("""
        SELECT sr.id, sr.date, sr.total_amount, sr.invoice_type, sr.customer_name,
               GROUP_CONCAT(sri.product_name || ' ×' || sri.quantity, ', ') as items_summary
        FROM sale_returns sr
        LEFT JOIN sale_return_items sri ON sri.return_id = sr.id
        WHERE sr.customer_id = ? AND sr.date BETWEEN ? AND ?
        GROUP BY sr.id
        ORDER BY sr.date DESC, sr.id DESC
    """, (customer_id, date_from, date_to)).fetchall()

    payments = conn.execute(
        "SELECT * FROM payments WHERE customer_id = ? AND date BETWEEN ? AND ? ORDER BY date DESC",
        (customer_id, date_from, date_to)
    ).fetchall()

    conn.close()
    return {
        'sales': [dict(r) for r in sales],
        'returns': [dict(r) for r in returns],
        'payments': [dict(r) for r in payments],
    }


def get_supplier_account(supplier_id, date_from, date_to):
    conn = get_connection()
    purchases = conn.execute("""
        SELECT p.id, p.date, p.total_amount,
               COALESCE(p.paid_amount, 0) as paid_amount,
               COALESCE(p.payment_type, 'cash') as payment_type,
               COALESCE(p.invoice_type, 'بيطري') as invoice_type, p.supplier as supplier_name,
               GROUP_CONCAT(pi.product_name || ' ×' || pi.quantity, ', ') as items_summary
        FROM purchases p
        LEFT JOIN purchase_items pi ON pi.purchase_id = p.id
        WHERE p.supplier_id = ? AND p.date BETWEEN ? AND ?
        GROUP BY p.id
        ORDER BY p.date DESC, p.id DESC
    """, (supplier_id, date_from, date_to)).fetchall()

    returns = conn.execute("""
        SELECT pr.id, pr.date, pr.total_amount, pr.invoice_type, pr.supplier_name,
               GROUP_CONCAT(pri.product_name || ' ×' || pri.quantity, ', ') as items_summary
        FROM purchase_returns pr
        LEFT JOIN purchase_return_items pri ON pri.return_id = pr.id
        WHERE pr.supplier_id = ? AND pr.date BETWEEN ? AND ?
        GROUP BY pr.id
        ORDER BY pr.date DESC, pr.id DESC
    """, (supplier_id, date_from, date_to)).fetchall()

    payments = conn.execute(
        "SELECT * FROM supplier_payments WHERE supplier_id = ? AND date BETWEEN ? AND ? ORDER BY date DESC",
        (supplier_id, date_from, date_to)
    ).fetchall()

    conn.close()
    return {
        'purchases': [dict(r) for r in purchases],
        'returns': [dict(r) for r in returns],
        'payments': [dict(r) for r in payments],
    }


def create_purchase(supplier_id, supplier_name, items, total_amount, paid_amount, payment_type, notes, invoice_type='بيطري'):
    remaining = max(0.0, total_amount - paid_amount)
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """INSERT INTO purchases (supplier_id, supplier, total_amount, paid_amount, payment_type, invoice_type, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (supplier_id, supplier_name, total_amount, paid_amount, payment_type, invoice_type, notes)
    )
    purchase_id = cursor.lastrowid

    for item in items:
        cursor.execute(
            """INSERT INTO purchase_items (purchase_id, product_id, product_name, quantity, unit_name, unit_price, total)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (purchase_id, item['product_id'], item['product_name'],
             item['quantity'], item.get('unit_name', ''), item['unit_price'], item['total'])
        )
        cursor.execute(
            "UPDATE products SET quantity = quantity + ?, purchase_price = ?, selling_price = ? WHERE id=?",
            (item['quantity'], item['unit_price'], item['selling_price'], item['product_id'])
        )
        if item.get('product_id'):
            cursor.execute(
                """INSERT INTO product_batches (product_id, quantity, purchase_price, expiry_date)
                   VALUES (?, ?, ?, ?)""",
                (item['product_id'], item['quantity'], item['unit_price'],
                 item.get('expiry_date') or None)
            )

    if supplier_id and remaining > 0:
        cursor.execute(
            "UPDATE suppliers SET total_debt = total_debt + ? WHERE id=?",
            (remaining, supplier_id)
        )

    conn.commit()
    conn.close()
    return purchase_id


def get_all_purchases():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM purchases ORDER BY date DESC, id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_purchase_items(purchase_id):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM purchase_items WHERE purchase_id=?", (purchase_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ===== Product Report =====

def get_product_report(product_id, date_from, date_to):
    """Return purchase, sale, return, and batch data for one product within a date range."""
    conn = get_connection()
    product = conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
    if not product:
        conn.close()
        return None

    purchases = conn.execute("""
        SELECT pi.quantity, COALESCE(pi.unit_name, '') AS unit_name,
               pi.unit_price, pi.total,
               p.date, COALESCE(p.supplier, '') AS supplier_name
        FROM purchase_items pi
        JOIN purchases p ON pi.purchase_id = p.id
        WHERE pi.product_id = ? AND p.date BETWEEN ? AND ?
        ORDER BY p.date DESC, p.id DESC
    """, (product_id, date_from, date_to)).fetchall()

    sales = conn.execute("""
        SELECT si.quantity, COALESCE(si.unit_name, '') AS unit_name,
               si.unit_price, si.total,
               s.date, COALESCE(s.customer_name, 'عميل نقدي') AS customer_name
        FROM sale_items si
        JOIN sales s ON si.sale_id = s.id
        WHERE si.product_id = ? AND s.date BETWEEN ? AND ?
        ORDER BY s.date DESC, s.id DESC
    """, (product_id, date_from, date_to)).fetchall()

    sale_returns = conn.execute("""
        SELECT sri.quantity, COALESCE(sri.unit_name, '') AS unit_name,
               sri.unit_price, sri.total,
               sr.date, COALESCE(sr.customer_name, '') AS customer_name
        FROM sale_return_items sri
        JOIN sale_returns sr ON sri.return_id = sr.id
        WHERE sri.product_id = ? AND sr.date BETWEEN ? AND ?
        ORDER BY sr.date DESC, sr.id DESC
    """, (product_id, date_from, date_to)).fetchall()

    purchase_returns = conn.execute("""
        SELECT pri.quantity, COALESCE(pri.unit_name, '') AS unit_name,
               pri.unit_price, pri.total,
               pr.date, COALESCE(pr.supplier_name, '') AS supplier_name
        FROM purchase_return_items pri
        JOIN purchase_returns pr ON pri.return_id = pr.id
        WHERE pri.product_id = ? AND pr.date BETWEEN ? AND ?
        ORDER BY pr.date DESC, pr.id DESC
    """, (product_id, date_from, date_to)).fetchall()

    batches = conn.execute("""
        SELECT quantity, purchase_price, expiry_date, purchase_date
        FROM product_batches
        WHERE product_id = ? AND quantity > 0
        ORDER BY CASE WHEN expiry_date IS NULL THEN '9999-99-99' ELSE expiry_date END ASC,
                 purchase_date ASC
    """, (product_id,)).fetchall()

    conn.close()
    return {
        'product':          dict(product),
        'purchases':        [dict(r) for r in purchases],
        'sales':            [dict(r) for r in sales],
        'sale_returns':     [dict(r) for r in sale_returns],
        'purchase_returns': [dict(r) for r in purchase_returns],
        'batches':          [dict(r) for r in batches],
    }


# ===== Low Stock =====

def get_low_stock_products(threshold=10):
    """Return products with quantity <= threshold, sorted by quantity ascending."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM products WHERE quantity <= ? AND quantity >= 0 ORDER BY quantity ASC",
        (threshold,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ===== Dashboard =====

def get_dashboard_stats():
    conn = get_connection()
    total_products = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    total_customers = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    today_sales = conn.execute(
        "SELECT COALESCE(SUM(total_amount), 0) FROM sales WHERE date = date('now')"
    ).fetchone()[0]
    total_debt = conn.execute(
        "SELECT COALESCE(SUM(total_debt), 0) FROM customers"
    ).fetchone()[0]
    total_supplier_debt = conn.execute(
        "SELECT COALESCE(SUM(total_debt), 0) FROM suppliers"
    ).fetchone()[0]
    low_stock = conn.execute(
        "SELECT COUNT(*) FROM products WHERE quantity <= 10 AND quantity >= 0"
    ).fetchone()[0]
    conn.close()
    return {
        'total_products': total_products,
        'total_customers': total_customers,
        'today_sales': today_sales,
        'total_debt': total_debt,
        'total_supplier_debt': total_supplier_debt,
        'low_stock': low_stock,
    }


# ===== Authentication =====

def init_auth():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY,
            username      TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            salt          TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def _hash_password(password: str, salt: str = None):
    if salt is None:
        salt = os.urandom(16).hex()
    hashed = hashlib.sha256((salt + password).encode('utf-8')).hexdigest()
    return hashed, salt


def has_any_user() -> bool:
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    return count > 0


def get_username() -> str:
    conn = get_connection()
    row = conn.execute("SELECT username FROM users LIMIT 1").fetchone()
    conn.close()
    return row['username'] if row else ''


def set_credentials(username: str, password: str):
    """Used only on first-run to create the initial user."""
    hashed, salt = _hash_password(password)
    conn = get_connection()
    conn.execute("DELETE FROM users")
    conn.execute(
        "INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)",
        (username, hashed, salt)
    )
    conn.commit()
    conn.close()


def get_all_users() -> list:
    conn = get_connection()
    rows = conn.execute("SELECT id, username FROM users ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_user(username: str, password: str) -> bool:
    """Add a new user. Returns False if the username is already taken."""
    hashed, salt = _hash_password(password)
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)",
            (username, hashed, salt)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def delete_user(user_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


def update_user_password(user_id: int, new_password: str):
    hashed, salt = _hash_password(new_password)
    conn = get_connection()
    conn.execute(
        "UPDATE users SET password_hash = ?, salt = ? WHERE id = ?",
        (hashed, salt, user_id)
    )
    conn.commit()
    conn.close()


def update_username(user_id: int, new_username: str) -> bool:
    """Returns False if the new username is already taken."""
    conn = get_connection()
    try:
        conn.execute("UPDATE users SET username = ? WHERE id = ?", (new_username, user_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def verify_credentials(username: str, password: str) -> bool:
    conn = get_connection()
    row = conn.execute(
        "SELECT password_hash, salt FROM users WHERE username = ?",
        (username,)
    ).fetchone()
    conn.close()
    if not row:
        return False
    hashed, _ = _hash_password(password, row['salt'])
    return hashed == row['password_hash']
