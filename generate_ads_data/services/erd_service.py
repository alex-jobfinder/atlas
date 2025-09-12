"""
Service for printing all database schemas.
"""

import sqlite3
import os
from typing import List, Dict, Optional
from rich   import print

def print_all_schemas() -> None:
    """
    Print all schemas in the database.
    """
    if not os.path.exists("ads.db"):
        print("[bold red]❌ Database not found: ads.db[/bold red]")
        return

    conn = sqlite3.connect("ads.db")
    cursor = conn.cursor()

    try:
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        print("[bold green]🗄️ Database Schemas:[/bold green]")
        print("=" * 50)

        for table in tables:
            table_name = table[0]
            print(f"\n[bold blue]📋 Table: {table_name}[/bold blue]")
            print("-" * 30)

            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()

            for col in columns:
                col_id, col_name, col_type, not_null, default_val, pk = col
                pk_marker = " 🔑" if pk else ""
                not_null_marker = " NOT NULL" if not_null else ""
                default_marker = f" DEFAULT {default_val}" if default_val else ""

                print(f"  {col_name}: {col_type}{not_null_marker}{default_marker}{pk_marker}")

            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  [bold yellow]📊 Rows: {count}[/bold yellow]")

        print("\n" + "=" * 50)

    finally:
        conn.close()
