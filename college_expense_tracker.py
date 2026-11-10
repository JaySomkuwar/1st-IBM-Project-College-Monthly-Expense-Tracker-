"""
College Monthly Expense Tracker
-------------------------------
A simple offline desktop app for tracking monthly money received from parents
and expenses such as rent, food, and personal spending.

Requirements: Python 3 (Tkinter is included with most Python installations)
Run: python college_expense_tracker.py
"""

import csv
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date
from pathlib import Path

DB_PATH = Path(__file__).with_name("college_expenses.db")
CATEGORIES = ("Rent", "Food", "Personal", "Travel", "Education", "Other")


class ExpenseTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("College Monthly Expense Tracker")
        self.root.geometry("950x650")
        self.root.minsize(800, 560)
        self.conn = sqlite3.connect(DB_PATH)
        self.create_tables()

        today = date.today()
        self.month_var = tk.StringVar(value=today.strftime("%Y-%m"))
        self.allowance_var = tk.StringVar()
        self.amount_var = tk.StringVar()
        self.category_var = tk.StringVar(value="Food")
        self.description_var = tk.StringVar()
        self.date_var = tk.StringVar(value=today.isoformat())

        self.build_ui()
        self.load_month()

    def create_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS monthly_budget (
                month TEXT PRIMARY KEY,
                allowance REAL NOT NULL DEFAULT 0
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                spent_on TEXT NOT NULL,
                month TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                amount REAL NOT NULL
            )
        """)
        self.conn.commit()

    def build_ui(self):
        outer = ttk.Frame(self.root, padding=16)
        outer.pack(fill="both", expand=True)

        ttk.Label(
            outer, text="My College Expense Tracker",
            font=("Segoe UI", 20, "bold")
        ).pack(anchor="w")
        ttk.Label(
            outer, text="Track your monthly allowance, expenses and remaining balance.",
            font=("Segoe UI", 10)
        ).pack(anchor="w", pady=(2, 14))

        month_bar = ttk.Frame(outer)
        month_bar.pack(fill="x", pady=(0, 12))
        ttk.Label(month_bar, text="Month (YYYY-MM):").pack(side="left")
        month_entry = ttk.Entry(month_bar, textvariable=self.month_var, width=12)
        month_entry.pack(side="left", padx=8)
        ttk.Button(month_bar, text="Load Month", command=self.load_month).pack(side="left")
        ttk.Button(month_bar, text="This Month", command=self.go_to_this_month).pack(side="left", padx=6)

        budget_frame = ttk.LabelFrame(outer, text="Monthly money from parents", padding=10)
        budget_frame.pack(fill="x", pady=(0, 12))
        ttk.Label(budget_frame, text="Monthly allowance (₹):").pack(side="left")
        ttk.Entry(budget_frame, textvariable=self.allowance_var, width=16).pack(side="left", padx=8)
        ttk.Button(budget_frame, text="Save Allowance", command=self.save_allowance).pack(side="left")

        summary = ttk.Frame(outer)
        summary.pack(fill="x", pady=(0, 12))
        self.allowance_label = self.make_summary_card(summary, "Allowance", "₹0.00", 0)
        self.spent_label = self.make_summary_card(summary, "Total spent", "₹0.00", 1)
        self.remaining_label = self.make_summary_card(summary, "Money remaining", "₹0.00", 2)

        entry_frame = ttk.LabelFrame(outer, text="Add a new expense", padding=10)
        entry_frame.pack(fill="x", pady=(0, 12))

        row1 = ttk.Frame(entry_frame)
        row1.pack(fill="x")
        ttk.Label(row1, text="Date (YYYY-MM-DD)").pack(side="left")
        ttk.Entry(row1, textvariable=self.date_var, width=14).pack(side="left", padx=(6, 16))
        ttk.Label(row1, text="Category").pack(side="left")
        ttk.Combobox(
            row1, textvariable=self.category_var, values=CATEGORIES,
            state="readonly", width=14
        ).pack(side="left", padx=(6, 16))
        ttk.Label(row1, text="Amount (₹)").pack(side="left")
        ttk.Entry(row1, textvariable=self.amount_var, width=14).pack(side="left", padx=6)

        row2 = ttk.Frame(entry_frame)
        row2.pack(fill="x", pady=(10, 0))
        ttk.Label(row2, text="Description").pack(side="left")
        ttk.Entry(row2, textvariable=self.description_var).pack(
            side="left", fill="x", expand=True, padx=6
        )
        ttk.Button(row2, text="Add Expense", command=self.add_expense).pack(side="left", padx=(6, 0))

        table_frame = ttk.LabelFrame(outer, text="Expenses for selected month", padding=8)
        table_frame.pack(fill="both", expand=True)
        columns = ("date", "category", "description", "amount")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)
        self.tree.heading("date", text="Date")
        self.tree.heading("category", text="Category")
        self.tree.heading("description", text="Description")
        self.tree.heading("amount", text="Amount (₹)")
        self.tree.column("date", width=110, anchor="center")
        self.tree.column("category", width=130, anchor="center")
        self.tree.column("description", width=430)
        self.tree.column("amount", width=130, anchor="e")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        bottom = ttk.Frame(outer)
        bottom.pack(fill="x", pady=(10, 0))
        ttk.Button(bottom, text="Delete Selected Expense", command=self.delete_expense).pack(side="left")
        ttk.Button(bottom, text="Export Month to CSV", command=self.export_csv).pack(side="left", padx=8)
        ttk.Label(
            bottom, text="Your data is saved on this computer.",
            foreground="#555"
        ).pack(side="right")

    def make_summary_card(self, parent, title, value, column):
        card = ttk.LabelFrame(parent, text=title, padding=12)
        card.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 6, 6))
        parent.columnconfigure(column, weight=1)
        label = ttk.Label(card, text=value, font=("Segoe UI", 16, "bold"))
        label.pack(anchor="center")
        return label

    def valid_month(self):
        month = self.month_var.get().strip()
        try:
            parsed = date.fromisoformat(month + "-01")
            if parsed.strftime("%Y-%m") != month:
                raise ValueError
            return month
        except ValueError:
            messagebox.showerror("Invalid month", "Enter the month in YYYY-MM format, for example 2026-11.")
            return None

    def go_to_this_month(self):
        self.month_var.set(date.today().strftime("%Y-%m"))
        self.date_var.set(date.today().isoformat())
        self.load_month()

    def load_month(self):
        month = self.valid_month()
        if not month:
            return
        self.date_var.set(month + "-01")
        row = self.conn.execute(
            "SELECT allowance FROM monthly_budget WHERE month=?", (month,)
        ).fetchone()
        allowance = row[0] if row else 0.0
        self.allowance_var.set(f"{allowance:.2f}")

        expenses = self.conn.execute(
            """SELECT id, spent_on, category, description, amount
               FROM expenses WHERE month=? ORDER BY spent_on DESC, id DESC""",
            (month,)
        ).fetchall()
        for item in self.tree.get_children():
            self.tree.delete(item)
        total = 0.0
        for expense_id, spent_on, category, description, amount in expenses:
            total += amount
            self.tree.insert(
                "", "end", iid=str(expense_id),
                values=(spent_on, category, description or "", f"{amount:,.2f}")
            )

        remaining = allowance - total
        self.allowance_label.config(text=f"₹{allowance:,.2f}")
        self.spent_label.config(text=f"₹{total:,.2f}")
        self.remaining_label.config(text=f"₹{remaining:,.2f}")
        self.remaining_label.config(foreground=("green" if remaining >= 0 else "red"))

    def save_allowance(self):
        month = self.valid_month()
        if not month:
            return
        try:
            allowance = float(self.allowance_var.get().replace(",", "").strip())
            if allowance < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid amount", "Enter a valid non-negative allowance.")
            return
        self.conn.execute(
            """INSERT INTO monthly_budget(month, allowance) VALUES(?, ?)
               ON CONFLICT(month) DO UPDATE SET allowance=excluded.allowance""",
            (month, allowance)
        )
        self.conn.commit()
        self.load_month()
        messagebox.showinfo("Saved", f"Allowance for {month} has been saved.")

    def add_expense(self):
        try:
            spent_on = date.fromisoformat(self.date_var.get().strip()).isoformat()
            amount = float(self.amount_var.get().replace(",", "").strip())
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Check your entry",
                "Enter a valid date (YYYY-MM-DD) and an amount greater than zero."
            )
            return

        month = spent_on[:7]
        category = self.category_var.get()
        description = self.description_var.get().strip()
        self.conn.execute(
            """INSERT INTO expenses(spent_on, month, category, description, amount)
               VALUES(?, ?, ?, ?, ?)""",
            (spent_on, month, category, description, amount)
        )
        self.conn.commit()
        self.month_var.set(month)
        self.amount_var.set("")
        self.description_var.set("")
        self.load_month()

    def delete_expense(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Nothing selected", "Select an expense from the table first.")
            return
        if not messagebox.askyesno("Confirm delete", "Delete the selected expense?"):
            return
        self.conn.executemany(
            "DELETE FROM expenses WHERE id=?",
            [(int(item),) for item in selected]
        )
        self.conn.commit()
        self.load_month()

    def export_csv(self):
        month = self.valid_month()
        if not month:
            return
        rows = self.conn.execute(
            """SELECT spent_on, category, description, amount
               FROM expenses WHERE month=? ORDER BY spent_on""",
            (month,)
        ).fetchall()
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=f"expenses_{month}.csv",
            filetypes=[("CSV files", "*.csv")]
        )
        if not filename:
            return
        with open(filename, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(["Date", "Category", "Description", "Amount (INR)"])
            writer.writerows(rows)
        messagebox.showinfo("Export complete", f"Your expenses were exported to:\n{filename}")

    def close(self):
        self.conn.close()
        self.root.destroy()


if __name__ == "__main__":
    window = tk.Tk()
    app = ExpenseTracker(window)
    window.protocol("WM_DELETE_WINDOW", app.close)
    window.mainloop()
