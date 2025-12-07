import re
import os
from pathlib import Path
import pyarrow.parquet as pq
import pyarrow as pa
import pandas as pd
import argparse

# Configuration
DATA_MODEL_FILE = Path("docs/AIMS Data Model.txt")
PARQUET_DIR = Path("data/Samples_LH_Bronze_Aims_26_parquet")
GENERATED_MODEL_FILE = Path("docs/AIMS_Data_Model_Actual.txt")

def parse_data_model(file_path):
    """Parses the AIMS Data Model text file."""
    with open(file_path, 'r') as f:
        content = f.read()

    tables = {}
    # Regex to find Table blocks
    table_blocks = re.findall(r'Table\s+(\w+)\s+\{([^}]+)\}', content)

    for table_name, block in table_blocks:
        columns = {}
        # Parse lines inside the block
        lines = block.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith('//'):
                continue
            
            parts = line.split()
            if len(parts) >= 2:
                col_name = parts[0]
                col_type = parts[1]
                columns[col_name] = col_type
        
        tables[table_name] = columns
    
    return tables

def get_parquet_metadata(file_path):
    """Reads the metadata of a parquet file (schema + row count)."""
    try:
        # Read metadata only
        metadata = pq.read_metadata(file_path)
        return metadata
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def format_size(size_bytes):
    """Formats bytes to human readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def map_arrow_type(arrow_type):
    """Maps PyArrow types to AIMS Model types."""
    t = str(arrow_type)
    if 'string' in t: return 'varchar(255)'
    if 'int64' in t: return 'bigint'
    if 'int32' in t: return 'int'
    if 'double' in t or 'float' in t: return 'float'
    if 'bool' in t: return 'bit'
    if 'timestamp' in t: return 'datetime'
    return 'varchar(255)' # Default fallback

def check_relationship(source_table, source_col, target_table, target_col):
    """Checks if values in source_col exist in target_col."""
    source_file = PARQUET_DIR / f"aims_{source_table.lower()}.parquet"
    target_file = PARQUET_DIR / f"aims_{target_table.lower()}.parquet"
    
    if not source_file.exists() or not target_file.exists():
        return False, "Files not found"
        
    try:
        # Optimization: Read only relevant columns
        source_df = pq.read_table(source_file, columns=[source_col]).to_pandas()
        target_df = pq.read_table(target_file, columns=[target_col]).to_pandas()
        
        # Use sets for O(1) lookup
        source_vals = set(source_df[source_col].dropna().unique())
        target_vals = set(target_df[target_col].dropna().unique())
        
        if len(source_vals) == 0:
            return False, "No source data"
            
        valid_refs = len(source_vals.intersection(target_vals))
        total_refs = len(source_vals)
        
        percentage = (valid_refs / total_refs) * 100
        return valid_refs > 0, f"{percentage:.2f}% ({valid_refs}/{total_refs})"
    except Exception as e:
        return False, f"Error: {e}"

def generate_model(tables, parquet_dir):
    """Generates a new data model from Parquet files with inferred and validated relationships."""
    print("Generating new data model...")
    new_model_lines = []
    new_model_lines.append("// AIMS Data Model (Reversed from Parquet Data)")
    new_model_lines.append(f"// Generated on {pd.Timestamp.now()}")
    new_model_lines.append("")

    all_parquet_files = sorted(list(parquet_dir.glob("*.parquet")))
    generated_tables = {} # Store table name -> list of columns

    # 1. Generate Tables
    for file_path in all_parquet_files:
        file_name = file_path.name
        name_part = file_name.replace('aims_', '').replace('.parquet', '')
        
        # Try to find matching original table name
        table_name = name_part.capitalize()
        original_cols = {}
        for t_name, t_cols in tables.items():
            if t_name.lower() == name_part.lower():
                table_name = t_name
                original_cols = t_cols
                break
        
        generated_tables[table_name] = []
        
        try:
            metadata = pq.read_metadata(file_path)
            schema = metadata.schema.to_arrow_schema()
        except Exception as e:
            print(f"Skipping {file_name}: {e}")
            continue
            
        new_model_lines.append(f"Table {table_name} {{")
        
        for field in schema:
            col_name = field.name
            col_type = "varchar(255)"
            
            # Preserve original type if known
            found_orig = False
            for orig_col, orig_type in original_cols.items():
                if orig_col.lower() == col_name.lower():
                    col_type = orig_type
                    found_orig = True
                    break
            
            if not found_orig:
                col_type = map_arrow_type(field.type)
            
            generated_tables[table_name].append(col_name)
            
            suffix = ""
            if col_name.upper() == 'ID':
                suffix = " [primary key]"
            
            new_model_lines.append(f"    {col_name} {col_type}{suffix}")
            
        new_model_lines.append("}")
        new_model_lines.append("")

    # 2. Infer and Validate Relationships
    print("Inferring and validating relationships...")
    relationships = []
    
    # Build singular map
    singular_map = {}
    for t in generated_tables:
        singular = t[:-1] if t.endswith('s') and not t.endswith('ss') else t
        if t.endswith('ies'): singular = t[:-3] + 'y'
        singular_map[singular.lower()] = t
        singular_map[t.lower()] = t

    for table_name, columns in generated_tables.items():
        for col_name in columns:
            if col_name.upper() == 'ID': continue
            
            if col_name.upper().endswith('ID'):
                potential_ref = col_name[:-2]
                if potential_ref.lower() in singular_map:
                    target_table = singular_map[potential_ref.lower()]
                    
                    # Validate
                    print(f"  Checking {table_name}.{col_name} -> {target_table}.ID...", end=" ", flush=True)
                    
                    # Skip huge tables validation if needed, or just do it
                    # AssetAttributes is huge, let's skip it for speed unless critical
                    if table_name == 'AssetAttributes':
                         print("Skipped (Large Table)")
                         relationships.append(f"Ref: {table_name}.{col_name} > {target_table}.ID // Unverified (Large Table)")
                         continue

                    is_valid, details = check_relationship(table_name, col_name, target_table, 'ID')
                    
                    if is_valid:
                        print(f"VALID {details}")
                        relationships.append(f"Ref: {table_name}.{col_name} > {target_table}.ID // Verified: {details}")
                    else:
                        print(f"INVALID {details}")
                        # relationships.append(f"// Ref: {table_name}.{col_name} > {target_table}.ID // Rejected: {details}")

    if relationships:
        new_model_lines.append("")
        new_model_lines.append("// Validated Relationships")
        new_model_lines.extend(relationships)

    with open(GENERATED_MODEL_FILE, 'w') as f:
        f.write('\n'.join(new_model_lines))
    
    print(f"\nSuccessfully generated new data model: {GENERATED_MODEL_FILE}")


def reconcile(tables, parquet_dir):
    """Reconciles the data model with parquet files."""
    report_lines = []
    header = f"{'Table':<30} | {'Status':<10} | {'Rows':<10} | {'Size':<10} | {'Details'}"
    print(header)
    print("-" * 100)
    
    report_lines.append("# AIMS Data Model Reconciliation Report")
    report_lines.append(f"**Date:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    
    # 1. Model vs Files Analysis
    report_lines.append("## 1. Model vs Parquet Files")
    report_lines.append("| Table | Status | Rows | Size | Details |")
    report_lines.append("|---|---|---|---|---|")

    modeled_files = set()

    for table_name, expected_cols in tables.items():
        parquet_filename = f"aims_{table_name.lower()}.parquet"
        parquet_path = parquet_dir / parquet_filename
        modeled_files.add(parquet_filename)

        if not parquet_path.exists():
            msg = f"File {parquet_filename} not found"
            print(f"{table_name:<30} | MISSING    | {'-':<10} | {'-':<10} | {msg}")
            report_lines.append(f"| {table_name} | 🔴 MISSING | - | - | {msg} |")
            continue

        metadata = get_parquet_metadata(parquet_path)
        if not metadata:
            continue

        schema = metadata.schema.to_arrow_schema()
        actual_cols = schema.names
        num_rows = metadata.num_rows
        file_size = format_size(parquet_path.stat().st_size)
        
        missing_cols = []
        
        for col_name, col_type in expected_cols.items():
            if col_name not in actual_cols:
                # Try case-insensitive match
                found = False
                for actual_col in actual_cols:
                    if actual_col.lower() == col_name.lower():
                        found = True
                        break
                if not found:
                    missing_cols.append(col_name)

        extra_cols = [col for col in actual_cols if col not in expected_cols and col.upper() not in [c.upper() for c in expected_cols]]

        # Analyze Missing Columns (KINO vs Real)
        kino_missing = [c for c in missing_cols if 'KINO' in c.upper()]
        real_missing = [c for c in missing_cols if 'KINO' not in c.upper()]

        if not missing_cols:
            status = "MATCH"
            details = f"Found {len(actual_cols)} cols"
            if extra_cols:
                details += f", {len(extra_cols)} extra"
            print(f"{table_name:<30} | {status:<10} | {num_rows:<10} | {file_size:<10} | {details}")
            report_lines.append(f"| {table_name} | ✅ MATCH | {num_rows} | {file_size} | {details} |")
        elif not real_missing:
             # Only KINO columns missing
            status = "PARTIAL"
            details = f"Missing {len(kino_missing)} Audit Cols (KINO)"
            print(f"{table_name:<30} | {status:<10} | {num_rows:<10} | {file_size:<10} | {details}")
            report_lines.append(f"| {table_name} | 🟡 AUDIT MISSING | {num_rows} | {file_size} | {details} |")
        else:
            status = "MISMATCH"
            details = f"Missing: {', '.join(real_missing[:3])}..." if len(real_missing) > 3 else f"Missing: {', '.join(real_missing)}"
            print(f"{table_name:<30} | {status:<10} | {num_rows:<10} | {file_size:<10} | {details}")
            report_lines.append(f"| {table_name} | ⚠️ MISMATCH | {num_rows} | {file_size} | {details} |")

    # 2. Extra Files Analysis
    report_lines.append("")
    report_lines.append("## 2. Unmodeled Files (Extra Data)")
    report_lines.append("These files exist in the data directory but are not defined in the Data Model.")
    report_lines.append("")
    report_lines.append("| File Name | Guessed Table | Rows | Size |")
    report_lines.append("|---|---|---|---|")
    
    print("\n" + "="*100)
    print(f"{'Unmodeled File':<40} | {'Rows':<10} | {'Size':<10}")
    print("-" * 100)

    all_parquet_files = set(f.name for f in parquet_dir.glob("*.parquet"))
    extra_files = sorted(list(all_parquet_files - modeled_files))

    for file_name in extra_files:
        file_path = parquet_dir / file_name
        metadata = get_parquet_metadata(file_path)
        if metadata:
            num_rows = metadata.num_rows
            file_size = format_size(file_path.stat().st_size)
            guessed_name = file_name.replace("aims_", "").replace(".parquet", "").title()
            
            print(f"{file_name:<40} | {num_rows:<10} | {file_size:<10}")
            report_lines.append(f"| {file_name} | {guessed_name} | {num_rows} | {file_size} |")

    with open("RECONCILIATION_REPORT.md", "w") as f:
        f.write("\n".join(report_lines))
    print("\nReport saved to RECONCILIATION_REPORT.md")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AIMS Schema Reconciliation Tool")
    parser.add_argument("--generate", action="store_true", help="Generate a new data model from Parquet files")
    parser.add_argument("--reconcile", action="store_true", help="Reconcile existing model with Parquet files")
    
    args = parser.parse_args()
    
    # Default to reconcile if no args provided
    if not args.generate and not args.reconcile:
        args.reconcile = True

    print("Parsing Data Model...")
    tables = parse_data_model(DATA_MODEL_FILE)
    print(f"Found {len(tables)} tables in model.")
    
    if args.reconcile:
        print("\nReconciling with Parquet files...")
        reconcile(tables, PARQUET_DIR)
        
    if args.generate:
        generate_model(tables, PARQUET_DIR)
