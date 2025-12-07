import re
import os
from pathlib import Path
import pyarrow.parquet as pq
import pyarrow as pa
import pandas as pd

# Configuration
DATA_MODEL_FILE = Path("docs/AIMS Data Model.txt")
PARQUET_DIR = Path("data/Samples_LH_Bronze_Aims_26_parquet")

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
    import pandas as pd # Import here for timestamp
    print("Parsing Data Model...")
    tables = parse_data_model(DATA_MODEL_FILE)
    print(f"Found {len(tables)} tables in model.")
    
    print("\nReconciling with Parquet files...")
    reconcile(tables, PARQUET_DIR)
