import re
import pandas as pd
from pathlib import Path
import sys

def parse_data_model(file_path):
    """Parses the AIMS Data Model.txt file."""
    with open(file_path, 'r') as f:
        content = f.read()

    tables = {}
    # Regex to find Table blocks
    # Table TableName { ... }
    table_blocks = re.findall(r'Table\s+(\w+)\s+\{([^}]+)\}', content, re.MULTILINE | re.DOTALL)

    for table_name, block in table_blocks:
        columns = {}
        # Parse lines inside the block
        lines = block.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith('//') or line.startswith('--'):
                continue
            
            # Extract column name and type
            # Example: ID integer [primary key]
            # Example: CODE string
            parts = line.split()
            if len(parts) >= 2:
                col_name = parts[0]
                col_type = parts[1]
                columns[col_name] = col_type
        
        tables[table_name] = columns
    
    return tables

def get_parquet_schema(file_path):
    """Reads the schema of a parquet file."""
    try:
        # Read only the schema (metadata)
        pf = pd.read_parquet(file_path)
        return pf.columns.tolist(), pf.dtypes.to_dict()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return [], {}

def reconcile(data_model_path, data_dir):
    """Reconciles parquet files with the data model."""
    print(f"Parsing Data Model from: {data_model_path}")
    expected_tables = parse_data_model(data_model_path)
    print(f"Found {len(expected_tables)} tables in Data Model.")

    print(f"\nChecking Parquet files in: {data_dir}")
    data_dir_path = Path(data_dir)
    parquet_files = list(data_dir_path.glob("*.parquet"))
    
    print(f"Found {len(parquet_files)} parquet files.")

    results = {
        "matched": [],
        "missing_files": [],
        "schema_mismatch": [],
        "extra_files": []
    }

    # Map parquet filenames to expected table names
    # aims_routes.parquet -> Routes
    # aims_ua_meetings.parquet -> UA_Meetings? Or just fuzzy match?
    # The data model has "Table Routes", file is "aims_routes.parquet"
    # Let's normalize both to lowercase for matching.
    
    expected_tables_lower = {k.lower(): k for k in expected_tables.keys()}
    
    # Check for missing files
    for table_name in expected_tables:
        expected_filename = f"aims_{table_name.lower()}.parquet"
        if not (data_dir_path / expected_filename).exists():
            # Try to find if there is a file that matches closely?
            # For now, strict match on aims_{tablename}.parquet
            results["missing_files"].append(table_name)

    for file_path in parquet_files:
        file_name = file_path.name
        # Remove 'aims_' prefix and .parquet extension
        table_name_guess = file_name.replace("aims_", "").replace(".parquet", "")
        
        # Handle special cases if any, or just try to match with expected_tables_lower
        # The data model has CamelCase, files are snake_case or just lowercase?
        # File list shows: aims_assetattributes.parquet (lowercase)
        # Data Model: Table AssetAttributes (CamelCase)
        
        matched_table_key = expected_tables_lower.get(table_name_guess.lower())
        
        if not matched_table_key:
            # Try removing underscores from file name if table name has no underscores
            # e.g. aims_ua_meetings -> ua_meetings -> uameetings -> UAMeetings?
            # Data Model might have UA_Meetings or UAMeetings
            
            # Let's try to match by removing underscores from both sides
            found = False
            for k, v in expected_tables_lower.items():
                if k.replace("_", "") == table_name_guess.replace("_", ""):
                    matched_table_key = v
                    found = True
                    break
            
            if not found:
                results["extra_files"].append(file_name)
                continue

        # We have a match
        expected_columns = expected_tables[matched_table_key]
        actual_columns, actual_dtypes = get_parquet_schema(file_path)
        
        # Compare columns
        # Data model columns are likely Case Sensitive or UpperCase?
        # File content: aims_routes.parquet
        # Let's check case sensitivity. Usually parquet columns might be preserved.
        
        # Normalize to set for comparison
        expected_cols_set = set(expected_columns.keys())
        actual_cols_set = set(actual_columns)
        
        # Check for case-insensitive match if direct match fails
        if not expected_cols_set.issubset(actual_cols_set):
            # Try case insensitive
            expected_cols_lower = {c.lower(): c for c in expected_cols_set}
            actual_cols_lower = {c.lower(): c for c in actual_cols_set}
            
            missing_cols = [expected_cols_lower[c] for c in expected_cols_lower if c not in actual_cols_lower]
            extra_cols = [actual_cols_lower[c] for c in actual_cols_lower if c not in expected_cols_lower]
        else:
            missing_cols = list(expected_cols_set - actual_cols_set)
            extra_cols = list(actual_cols_set - expected_cols_set)

        if missing_cols:
            results["schema_mismatch"].append({
                "table": matched_table_key,
                "file": file_name,
                "missing_columns": missing_cols,
                "extra_columns_count": len(extra_cols)
            })
        else:
            results["matched"].append(matched_table_key)

    # Report
    print("\n=== RECONCILIATION REPORT ===")
    
    print(f"\n✅ Fully Matched Tables: {len(results['matched'])}")
    
    if results["missing_files"]:
        print(f"\n❌ Missing Files ({len(results['missing_files'])}):")
        for t in results["missing_files"]:
            print(f"  - Expected table '{t}' (looked for aims_{t.lower()}.parquet)")

    if results["extra_files"]:
        print(f"\n⚠️ Extra Files (Not in Data Model) ({len(results['extra_files'])}):")
        for f in results["extra_files"]:
            print(f"  - {f}")

    if results["schema_mismatch"]:
        print(f"\n⚠️ Schema Mismatches ({len(results['schema_mismatch'])}):")
        for m in results["schema_mismatch"]:
            print(f"  - Table: {m['table']} (File: {m['file']})")
            print(f"    Missing Columns: {m['missing_columns']}")
            if m['extra_columns_count'] > 0:
                print(f"    (Plus {m['extra_columns_count']} extra columns in file)")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python reconcile.py <data_model_file> <data_dir>")
        sys.exit(1)
    
    reconcile(sys.argv[1], sys.argv[2])
