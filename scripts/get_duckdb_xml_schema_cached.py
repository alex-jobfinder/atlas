# Filename: scripts/get_schema_cached.py
"""Script to extract database schema from DuckDB and output as XML with 24-hour caching.

This script connects to a DuckDB database, extracts the schema information,
and outputs it in a machine-readable XML format that can be used in Cursor.
Includes 24-hour caching to avoid regenerating the schema unnecessarily.
"""

import duckdb
import xml.etree.ElementTree as ET
from pathlib import Path
import time
import os

def is_schema_cache_valid(cache_file: str, max_age_hours: int = 24) -> bool:
    """Check if the cached schema file is still valid.

    Args:
        cache_file: Path to the cached schema file
        max_age_hours: Maximum age in hours before cache expires

    Returns:
        bool: True if cache is valid, False otherwise
    """
    if not os.path.exists(cache_file):
        return False

    file_age_hours = (time.time() - os.path.getmtime(cache_file)) / 3600
    return file_age_hours < max_age_hours

def get_schema_as_xml(db_path: str) -> ET.Element:
    """Extract schema from DuckDB database and return as XML Element.

    Args:
        db_path: Path to the DuckDB database file

    Returns:
        ET.Element: XML Element containing the database schema
    """
    # Connect to the DuckDB database
    conn = duckdb.connect(db_path)

    # Get all tables
    tables = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'").fetchall()

    # Create XML root
    root = ET.Element("database")
    root.set("name", Path(db_path).stem)

    # For each table, get its schema
    for (table_name,) in tables:
        table_elem = ET.SubElement(root, "table")
        table_elem.set("name", table_name)

        # Get column information
        columns = conn.execute(f"""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'main' AND table_name = '{table_name}'
            ORDER BY ordinal_position
        """).fetchall()

        for col_name, data_type, is_nullable in columns:
            column_elem = ET.SubElement(table_elem, "column")
            column_elem.set("name", col_name)
            column_elem.set("type", data_type)
            column_elem.set("nullable", is_nullable)

    conn.close()
    return root

def save_schema_to_file(root: ET.Element, output_path: str) -> None:
    """Save the XML schema to a file with pretty printing.

    Args:
        root: XML Element containing the schema
        output_path: Path where to save the XML file
    """
    ET.indent(root)
    tree = ET.ElementTree(root)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)

def get_cached_schema(db_path: str, output_path: str, max_age_hours: int = 24) -> bool:
    """Get schema with caching. Returns True if schema was regenerated, False if cached.

    Args:
        db_path: Path to the DuckDB database file
        output_path: Path where to save the XML file
        max_age_hours: Maximum age in hours before cache expires

    Returns:
        bool: True if schema was regenerated, False if cached version was used
    """
    # Check if cache is valid
    if is_schema_cache_valid(output_path, max_age_hours):
        print(f"Using cached schema from {output_path}")
        return False

    # Generate new schema
    print(f"Generating fresh schema from {db_path}")
    root = get_schema_as_xml(db_path)
    save_schema_to_file(root, output_path)
    print(f"Schema saved to {output_path}")
    return True

if __name__ == "__main__":
    db_path = "dbt_ads_project/dbt.duckdb"
    output_path = "dbt_ads_project/xml_schema/dbt_db_schema.xml"

    get_cached_schema(db_path, output_path)
