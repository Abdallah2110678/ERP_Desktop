"""Import the old Access (.mdb / .accdb) database into pharmacy.db (add-only).

Usage:
    python import_access.py path\\to\\DB.mdb --inspect    # list tables, columns, row counts
    python import_access.py path\\to\\DB.mdb              # dry run: does everything, then rolls back
    python import_access.py path\\to\\DB.mdb --commit     # backs up pharmacy.db, then writes

Requires:  pip install pyodbc   (and the 64-bit "Microsoft Access Driver (*.mdb, *.accdb)")

Mapping (Access -> pharmacy.db)
    suppliers (is_supplier=True)  -> suppliers        suppliers (is_supplier=False) -> customers
    items                         -> products         (skips a name+unit that already exists)
    sales   (is_sale=True)        -> sales + sale_items
    sales   (is_sale=False)       -> sale_returns + sale_return_items
    Orders  (is_order=True)       -> purchases + purchase_items
    Orders  (is_order=False)      -> purchase_returns + purchase_return_items
    dof3at  (is_credit=1)         -> payments           (customer paid us)
    dof3at  (is_credit=0)         -> supplier_payments  (we paid supplier)
    users, expenses, cartoon_sizes, new, ~TMP* are not imported.

Rows are inserted directly (not through create_sale etc.), so stock, batches and
total_debt are computed here once at the end instead of per row.
"""
import argparse
import shutil
import sqlite3
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

import pyodbc

from database import DB_PATH, init_db

DRIVER = "Microsoft Access Driver (*.mdb, *.accdb)"
CASH_NAME = "كاش"                 # Access uses this name for walk-in / cash parties
DEFAULT_TYPE = "بيطري"
NOTE = "مستورد من Access - فاتورة رقم {}"
MARKER = "مستورد من Access%"


def open_access(path: Path):
    return pyodbc.connect(f"DRIVER={{{DRIVER}}};DBQ={path};ReadOnly=1;")


def inspect(path: Path):
    conn = open_access(path)
    cur = conn.cursor()
    tables = [t.table_name for t in cur.tables(tableType="TABLE")]
    for t in tables:
        count = cur.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
        cols = [f"{c.column_name} ({c.type_name})" for c in cur.columns(table=t)]
        print(f"\n== {t}  [{count} rows]")
        print("   " + ", ".join(cols))
    conn.close()


def _num(v):
    try:
        return float(v) if v is not None else 0.0
    except (TypeError, ValueError):
        return 0.0


def _txt(v):
    return "" if v is None else " ".join(str(v).split())


def _day(v):
    return v.strftime("%Y-%m-%d") if isinstance(v, datetime) else date.today().isoformat()


def _pay_type(is_agel, total, paid):
    if not is_agel or paid >= total:
        return "cash"
    return "partial" if paid > 0 else "credit"


class Importer:
    def __init__(self, acc, lite, skip_debt=False):
        self.acc, self.lite, self.skip_debt = acc, lite, skip_debt
        self.stats = defaultdict(int)
        self.customers = {r[0]: r[1] for r in lite.execute("SELECT name, id FROM customers")}
        self.suppliers = {r[0]: r[1] for r in lite.execute("SELECT name, id FROM suppliers")}
        self.products = {(r[0], r[1]): r[2] for r in lite.execute("SELECT name, unit, id FROM products")}
        self.code_pid = {}          # Access item code -> products.id
        self.new_pids = set()       # products created by this import (only these get computed stock)
        self.stock = defaultdict(float)
        self.cust_debt = defaultdict(float)
        self.supp_debt = defaultdict(float)
        self.cost = {}              # products.id -> purchase_price, for the opening batch

    def rows(self, sql):
        return self.acc.cursor().execute(sql).fetchall()

    # ---- parties -------------------------------------------------------
    def customer(self, name, phone="", address=""):
        name = _txt(name)
        if not name or name == CASH_NAME:
            return None
        if name not in self.customers:
            cur = self.lite.execute(
                "INSERT INTO customers (name, phone, address) VALUES (?, ?, ?)", (name, phone, address))
            self.customers[name] = cur.lastrowid
            self.stats["customers"] += 1
        return self.customers[name]

    def supplier(self, name, phone="", address=""):
        name = _txt(name)
        if not name or name == CASH_NAME:
            return None
        if name not in self.suppliers:
            cur = self.lite.execute(
                "INSERT INTO suppliers (name, phone, address) VALUES (?, ?, ?)", (name, phone, address))
            self.suppliers[name] = cur.lastrowid
            self.stats["suppliers"] += 1
        return self.suppliers[name]

    def import_parties(self):
        for name, phone, is_supplier, address in self.rows(
                "SELECT name, phone, is_supplier, address FROM suppliers"):
            (self.supplier if is_supplier else self.customer)(name, _txt(phone), _txt(address))

    # ---- products ------------------------------------------------------
    def _new_product(self, name, unit, typ, cost, price):
        cur = self.lite.execute(
            "INSERT INTO products (name, unit, quantity, purchase_price, selling_price, product_type)"
            " VALUES (?, ?, 0, ?, ?, ?)", (name, unit, cost, price, typ or DEFAULT_TYPE))
        pid = cur.lastrowid
        self.products[(name, unit)] = pid
        self.new_pids.add(pid)
        self.cost[pid] = cost
        self.stats["products"] += 1
        return pid

    def import_items(self):
        for code, name, typ, unit, cost, price in self.rows(
                "SELECT code, item_name, [type], unit, cost, price FROM items"):
            name, unit = _txt(name), _txt(unit) or "-"
            if not name:
                continue
            pid = self.products.get((name, unit))
            if pid is None:
                pid = self._new_product(name, unit, _txt(typ), _num(cost), _num(price))
            else:
                self.stats["products skipped (already exist)"] += 1
            self.code_pid[code] = pid

    def product_for(self, code, name, unit, price=0.0):
        """products.id for a transaction line; creates a product when the code isn't in items."""
        key = code if code is not None else ("name", name)
        if key not in self.code_pid:
            name, unit = name or f"صنف {code}", unit or "-"
            pid = self.products.get((name, unit)) or self._new_product(name, unit, "", 0.0, price)
            self.code_pid[key] = pid
            self.stats["products created from transactions"] += 1
        return self.code_pid[key]

    # ---- invoices ------------------------------------------------------
    def _group(self, rows, key_idx):
        groups = {}
        for r in rows:
            groups.setdefault(tuple(r[i] for i in key_idx), []).append(r)
        return groups

    def import_sales(self):
        # pk, code, item_name, client, bill_num, count1, price, total_price, sale_date, is_sale, unit, type, is_agel, paid
        rows = self.rows("SELECT pk, code, item_name, client, bill_num, count1, price, total_price,"
                         " sale_date, is_sale, unit, [type], is_agel, paid FROM sales ORDER BY sale_date, pk")
        groups = self._group(rows, (4, 3, 8, 9, 12, 11))   # bill, client, date, is_sale, is_agel, type
        for (bill, client, sdate, is_sale, is_agel, typ), lines in groups.items():
            cname, cid = _txt(client), self.customer(client)
            cname = cname if cid else "عميل نقدي"
            total = sum(_num(l[7]) for l in lines)
            typ, day, note = _txt(typ) or DEFAULT_TYPE, _day(sdate), NOTE.format(bill)
            items = [(self.product_for(l[1], _txt(l[2]), _txt(l[10]), _num(l[6])), _txt(l[2]),
                      _num(l[5]), _txt(l[10]), _num(l[6]), _num(l[7])) for l in lines]
            if is_sale:
                paid = max(_num(l[13]) for l in lines) if is_agel else total
                remaining = max(0.0, total - paid)
                cur = self.lite.execute(
                    "INSERT INTO sales (customer_id, customer_name, date, total_amount, paid_amount, remaining,"
                    " payment_type, invoice_type, notes) VALUES (?,?,?,?,?,?,?,?,?)",
                    (cid, cname, day, total, paid, remaining, _pay_type(is_agel, total, paid), typ, note))
                self.lite.executemany(
                    "INSERT INTO sale_items (sale_id, product_id, product_name, quantity, unit_name, unit_price,"
                    " total) VALUES (?,?,?,?,?,?,?)", [(cur.lastrowid, *i) for i in items])
                if cid:
                    self.cust_debt[cid] += remaining
                for i in items:
                    self.stock[i[0]] -= i[2]
                self.stats["sales"] += 1
            else:
                cur = self.lite.execute(
                    "INSERT INTO sale_returns (customer_id, customer_name, date, total_amount, invoice_type, notes)"
                    " VALUES (?,?,?,?,?,?)", (cid, cname, day, total, typ, note))
                self.lite.executemany(
                    "INSERT INTO sale_return_items (return_id, product_id, product_name, quantity, unit_name,"
                    " unit_price, total) VALUES (?,?,?,?,?,?,?)", [(cur.lastrowid, *i) for i in items])
                if cid:
                    self.cust_debt[cid] -= total
                for i in items:
                    self.stock[i[0]] += i[2]
                self.stats["sale returns"] += 1

    def import_orders(self):
        # pk, code, item_name, count1, cost, total_cost, order_date, supplier, bill_num, unit, type, is_agel, paid, is_order
        rows = self.rows("SELECT pk, code, item_name, count1, cost, total_cost, order_date, supplier,"
                         " bill_num, unit, [type], is_agel, paid, is_order FROM Orders ORDER BY order_date, pk")
        groups = self._group(rows, (8, 7, 6, 13, 11))       # bill, supplier, date, is_order, is_agel
        for (bill, supplier, odate, is_order, is_agel), lines in groups.items():
            sname, sid = _txt(supplier), self.supplier(supplier)
            total = sum(_num(l[5]) for l in lines)
            typ = next((_txt(l[10]) for l in lines if _txt(l[10])), DEFAULT_TYPE)
            day, note = _day(odate), NOTE.format(bill)
            items = [(self.product_for(l[1], _txt(l[2]), _txt(l[9]), 0.0), _txt(l[2]),
                      _num(l[3]), _txt(l[9]), _num(l[4]), _num(l[5])) for l in lines]
            if is_order:
                paid = max(_num(l[12]) for l in lines) if is_agel else total
                remaining = max(0.0, total - paid)
                cur = self.lite.execute(
                    "INSERT INTO purchases (supplier_id, supplier, date, total_amount, paid_amount, payment_type,"
                    " invoice_type, notes) VALUES (?,?,?,?,?,?,?,?)",
                    (sid, sname, day, total, paid, _pay_type(is_agel, total, paid), typ, note))
                self.lite.executemany(
                    "INSERT INTO purchase_items (purchase_id, product_id, product_name, quantity, unit_name,"
                    " unit_price, total) VALUES (?,?,?,?,?,?,?)", [(cur.lastrowid, *i) for i in items])
                if sid:
                    self.supp_debt[sid] += remaining
                for i in items:
                    self.stock[i[0]] += i[2]
                self.stats["purchases"] += 1
            else:
                cur = self.lite.execute(
                    "INSERT INTO purchase_returns (supplier_id, supplier_name, date, total_amount, invoice_type,"
                    " notes) VALUES (?,?,?,?,?,?)", (sid, sname, day, total, typ, note))
                self.lite.executemany(
                    "INSERT INTO purchase_return_items (return_id, product_id, product_name, quantity, unit_name,"
                    " unit_price, total) VALUES (?,?,?,?,?,?,?)", [(cur.lastrowid, *i) for i in items])
                if sid:
                    self.supp_debt[sid] -= total
                for i in items:
                    self.stock[i[0]] -= i[2]
                self.stats["purchase returns"] += 1

    def import_payments(self):
        for amount, person, pdate, is_credit, ezn in self.rows(
                "SELECT dof3a, person_name, dof3a_date, is_credit, ezn_number FROM dof3at ORDER BY dof3a_date, ID"):
            amount, day, notes = _num(amount), _day(pdate), _txt(ezn)
            if is_credit:       # customer paid us
                cid = self.customer(person)
                if cid is None:
                    self.stats["payments skipped (cash/blank name)"] += 1
                    continue
                self.lite.execute("INSERT INTO payments (customer_id, amount, date, notes) VALUES (?,?,?,?)",
                                  (cid, amount, day, notes))
                self.cust_debt[cid] -= amount
                self.stats["customer payments"] += 1
            else:               # we paid a supplier
                sid = self.supplier(person)
                if sid is None:
                    self.stats["payments skipped (cash/blank name)"] += 1
                    continue
                self.lite.execute("INSERT INTO supplier_payments (supplier_id, amount, date, notes) VALUES (?,?,?,?)",
                                  (sid, amount, day, notes))
                self.supp_debt[sid] -= amount
                self.stats["supplier payments"] += 1

    # ---- derived values ------------------------------------------------
    def apply_debts(self):
        for table, deltas in (("customers", self.cust_debt), ("suppliers", self.supp_debt)):
            for pid, delta in deltas.items():
                self.lite.execute(
                    f"UPDATE {table} SET total_debt = MAX(0, total_debt + ?) WHERE id=?", (delta, pid))
            n, total = self.lite.execute(
                f"SELECT COUNT(*), COALESCE(SUM(total_debt), 0) FROM {table} WHERE total_debt > 0").fetchone()
            self.stats[f"{table} with debt"] = n
            self.stats[f"{table} total debt"] = f"{total:,.0f}"

    def apply_stock(self):
        """Opening stock for NEW products = purchases - purchase returns - sales + sale returns (never below 0)."""
        for pid in self.new_pids:
            qty = self.stock.get(pid, 0.0)
            if qty < 0:
                self.stats["new products whose computed stock was negative (set to 0)"] += 1
                qty = 0.0
            if qty > 0:
                self.lite.execute("UPDATE products SET quantity=? WHERE id=?", (qty, pid))
                self.lite.execute(
                    "INSERT INTO product_batches (product_id, quantity, purchase_price, expiry_date)"
                    " VALUES (?, ?, ?, NULL)", (pid, qty, self.cost.get(pid, 0.0)))
                self.stats["products with stock"] += 1

    def run(self):
        self.import_parties()
        self.import_items()
        self.import_sales()
        self.import_orders()
        self.import_payments()
        if not self.skip_debt:
            self.apply_debts()
        self.apply_stock()


class AlreadyImported(Exception):
    """Invoices from Access are already in pharmacy.db."""


def run_import(mdb: Path, commit: bool = True, skip_debt: bool = False, force: bool = False):
    """Import `mdb` into pharmacy.db. Returns (stats, backup_path or None).

    With commit=False everything is done and then rolled back (dry run).
    """
    init_db()
    acc, lite = open_access(mdb), sqlite3.connect(DB_PATH)
    try:
        if not force and lite.execute(
                "SELECT 1 FROM sales WHERE notes LIKE ? LIMIT 1", (MARKER,)).fetchone():
            raise AlreadyImported()
        backup = None
        if commit:      # copy BEFORE any write; a mid-transaction copy of the file can be inconsistent
            backup = DB_PATH.with_name(f"pharmacy.backup-{datetime.now():%Y%m%d-%H%M%S}.db")
            shutil.copy2(DB_PATH, backup)
        imp = Importer(acc, lite, skip_debt=skip_debt)
        imp.run()
        if commit:
            lite.commit()
        else:
            lite.rollback()
        return dict(imp.stats), backup
    except BaseException:
        lite.rollback()
        raise
    finally:
        acc.close()
        lite.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mdb", type=Path)
    ap.add_argument("--inspect", action="store_true")
    ap.add_argument("--commit", action="store_true")
    ap.add_argument("--force", action="store_true", help="import again even if invoices were already imported")
    ap.add_argument("--no-debt", action="store_true",
                    help="import invoices and payments but leave customers'/suppliers' total_debt untouched")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    if args.inspect:
        inspect(args.mdb)
        return
    try:
        stats, backup = run_import(args.mdb, args.commit, args.no_debt, args.force)
    except AlreadyImported:
        sys.exit("Invoices from Access are already in pharmacy.db. Use --force to import again (creates duplicates).")
    for k, v in sorted(stats.items()):
        print(f"  {k}: {v}")
    print(f"COMMITTED. Previous data is in {backup.name}" if args.commit
          else "DRY RUN - nothing written. Re-run with --commit.")


if __name__ == "__main__":
    main()
