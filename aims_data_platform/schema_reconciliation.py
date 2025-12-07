import re
import os
from pathlib import Path
import pyarrow.parquet as pq
import pyarrow as pa
import pandas as pd

# Configuration
# These defaults can be overridden by passing arguments
DEFAULT_DATA_MODEL_FILE = Path(os.getenv("DATA_MODEL_FILE", "docs/AIMS Data Model.txt"))
DEFAULT_PARQUET_DIR = Path(os.getenv("BRONZE_PATH", "data/Samples_LH_Bronze_Aims_26_parquet"))
DEFAULT_GENERATED_MODEL_FILE = Path(os.getenv("GENERATED_MODEL_FILE", "docs/AIMS_Data_Model_Actual.txt"))

def parse_data_model(file_path):
    """
    Parses the AIMS Data Model definition file.

    Args:
        file_path (Path): Path to the data model text file.

    Returns:
        dict: A dictionary mapping table names to column definitions.
    """
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
    """
    Retrieves metadata from a Parquet file, including schema and row count.

    Args:
        file_path (Path): Path to the Parquet file.

    Returns:
        pyarrow.parquet.FileMetaData: The metadata object, or None if reading fails.
    """
    try:
        # Read metadata only
        metadata = pq.read_metadata(file_path)
        return metadata
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def format_size(size_bytes):
    """
    Formats a byte count into a human-readable string (e.g., KB, MB).

    Args:
        size_bytes (int): The size in bytes.

    Returns:
        str: Formatted string representation of the size.
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def map_arrow_type(arrow_type):
    """
    Maps PyArrow data types to the corresponding AIMS Data Model types.

    Args:
        arrow_type (pyarrow.DataType): The PyArrow data type.

    Returns:
        str: The corresponding AIMS model type string (e.g., 'varchar(255)', 'bigint').
    """
    t = str(arrow_type)
    if 'string' in t: return 'varchar(255)'
    if 'int64' in t: return 'bigint'
    if 'int32' in t: return 'int'
    if 'double' in t or 'float' in t: return 'float'
    if 'bool' in t: return 'bit'
    if 'timestamp' in t: return 'datetime'
    return 'varchar(255)' # Default fallback

def check_relationship(source_table, source_col, target_table, target_col, parquet_dir, sample_size=None):
    """
    Verifies referential integrity by checking if values in a source column exist in a target column.

    Args:
        source_table (str): Name of the source table.
        source_col (str): Name of the foreign key column in the source table.
        target_table (str): Name of the target (referenced) table.
        target_col (str): Name of the primary key column in the target table.
        parquet_dir (Path): Directory containing the Parquet files.
        sample_size (int, optional): Number of rows to sample from the source table. Defaults to None (full scan).

    Returns:
        tuple: (bool, str) indicating validity and a status message.
    """
    source_file = parquet_dir / f"aims_{source_table.lower()}.parquet"
    target_file = parquet_dir / f"aims_{target_table.lower()}.parquet"
    
    if not source_file.exists() or not target_file.exists():
        return False, "Files not found"
        
    try:
        # Read Target (Full) - We need all valid IDs
        target_df = pq.read_table(target_file, columns=[target_col]).to_pandas()
        target_vals = set(target_df[target_col].dropna().unique())
        
        # Read Source (Sampled if requested)
        if sample_size:
            # Read first row group(s) until we have enough samples
            parquet_file = pq.ParquetFile(source_file)
            dfs = []
            rows_collected = 0
            for i in range(parquet_file.num_row_groups):
                if rows_collected >= sample_size: break
                df = parquet_file.read_row_group(i, columns=[source_col]).to_pandas()
                dfs.append(df)
                rows_collected += len(df)
            source_df = pd.concat(dfs)
            if len(source_df) > sample_size:
                source_df = source_df.head(sample_size)
            sampled_msg = f" (Sampled {len(source_df)})"
        else:
            source_df = pq.read_table(source_file, columns=[source_col]).to_pandas()
            sampled_msg = ""
        
        # Use sets for O(1) lookup
        source_vals = set(source_df[source_col].dropna().unique())
        
        if len(source_vals) == 0:
            return False, "No source data"
            
        valid_refs = len(source_vals.intersection(target_vals))
        total_refs = len(source_vals)
        
        percentage = (valid_refs / total_refs) * 100
        return valid_refs > 0, f"{percentage:.2f}% ({valid_refs}/{total_refs}){sampled_msg}"
    except Exception as e:
        return False, f"Error: {e}"

def analyze_comparison(tables, parquet_dir):
    """Analyzes the comparison between model and parquet files, returning a DataFrame."""
    results = []
    modeled_files = set()

    for table_name, expected_cols in tables.items():
        parquet_filename = f"aims_{table_name.lower()}.parquet"
        parquet_path = parquet_dir / parquet_filename
        modeled_files.add(parquet_filename)

        row = {
            "Table": table_name,
            "Status": "UNKNOWN",
            "Rows": 0,
            "Size": "0 B",
            "Model_Col_Count": len(expected_cols),
            "Parquet_Col_Count": 0,
            "Missing_Cols": [],
            "Extra_Cols": [],
            "Details": ""
        }

        if not parquet_path.exists():
            row["Status"] = "MISSING FILE"
            row["Details"] = f"File {parquet_filename} not found"
            results.append(row)
            continue

        metadata = get_parquet_metadata(parquet_path)
        if not metadata:
            row["Status"] = "READ ERROR"
            row["Details"] = "Could not read Parquet metadata"
            results.append(row)
            continue

        schema = metadata.schema.to_arrow_schema()
        actual_cols = schema.names
        row["Parquet_Col_Count"] = len(actual_cols)
        row["Rows"] = metadata.num_rows
        row["Size"] = format_size(parquet_path.stat().st_size)
        
        missing_cols = []
        
        for col_name in expected_cols.keys():
            found = False
            for actual_col in actual_cols:
                if actual_col.lower() == col_name.lower():
                    found = True
                    break
            if not found:
                missing_cols.append(col_name)

        expected_cols_upper = [c.upper() for c in expected_cols.keys()]
        extra_cols = [col for col in actual_cols if col.upper() not in expected_cols_upper]

        row["Missing_Cols"] = missing_cols
        row["Extra_Cols"] = extra_cols

        kino_missing = [c for c in missing_cols if 'KINO' in c.upper()]
        real_missing = [c for c in missing_cols if 'KINO' not in c.upper()]

        if not missing_cols:
            row["Status"] = "MATCH"
            row["Details"] = "All model columns present"
            if extra_cols:
                row["Status"] = "MATCH (+EXTRA)"
                row["Details"] += f", {len(extra_cols)} extra columns"
        elif not real_missing:
            row["Status"] = "AUDIT MISSING"
            row["Details"] = f"Missing {len(kino_missing)} Audit Cols (KINO)"
        else:
            row["Status"] = "MISMATCH"
            row["Details"] = f"Missing {len(missing_cols)} columns"

        results.append(row)

    return pd.DataFrame(results), modeled_files

def analyze_extra_files(modeled_files, parquet_dir):
    """Analyzes files present in directory but not in model."""
    all_parquet_files = set(f.name for f in parquet_dir.glob("*.parquet"))
    extra_files = sorted(list(all_parquet_files - modeled_files))
    
    results = []
    for file_name in extra_files:
        file_path = parquet_dir / file_name
        metadata = get_parquet_metadata(file_path)
        if metadata:
            guessed_name = file_name.replace("aims_", "").replace(".parquet", "").title()
            results.append({
                "File Name": file_name,
                "Guessed Table": guessed_name,
                "Rows": metadata.num_rows,
                "Size": format_size(file_path.stat().st_size)
            })
            
    return pd.DataFrame(results)

def generate_model(tables, parquet_dir, output_file=DEFAULT_GENERATED_MODEL_FILE):
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
    connected_tables = set()
    
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
                    
                    # Use sampling for large tables (e.g. > 100MB or known large tables)
                    # For simplicity, we'll use sampling for AssetAttributes or if explicitly requested
                    sample_size = None
                    if table_name == 'AssetAttributes':
                         sample_size = 100000
                         print(f"(Sampling {sample_size})", end=" ")

                    is_valid, details = check_relationship(table_name, col_name, target_table, 'ID', parquet_dir, sample_size=sample_size)
                    
                    if is_valid:
                        print(f"VALID {details}")
                        relationships.append(f"Ref: {table_name}.{col_name} > {target_table}.ID // Verified: {details}")
                        connected_tables.add(table_name)
                        connected_tables.add(target_table)
                    else:
                        print(f"INVALID {details}")
                        # relationships.append(f"// Ref: {table_name}.{col_name} > {target_table}.ID // Rejected: {details}")

    if relationships:
        new_model_lines.append("")
        new_model_lines.append("// Validated Relationships")
        new_model_lines.extend(relationships)
        
    # 3. Orphaned Tables Summary
    all_tables = set(generated_tables.keys())
    orphaned_tables = sorted(list(all_tables - connected_tables))
    
    new_model_lines.append("")
    new_model_lines.append("// Orphaned Tables (No Relationships Detected)")
    if orphaned_tables:
        for t in orphaned_tables:
            new_model_lines.append(f"// - {t}")
    else:
        new_model_lines.append("// None")

    print("\nOrphaned Tables Summary:")
    if orphaned_tables:
        for t in orphaned_tables:
            print(f" - {t}")
    else:
        print(" - None")

    with open(output_file, 'w') as f:
        f.write('\n'.join(new_model_lines))
    
    print(f"\nSuccessfully generated new data model: {output_file}")


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

    df_comparison, modeled_files = analyze_comparison(tables, parquet_dir)
    
    for _, row in df_comparison.iterrows():
        status = row['Status']
        if status == "MATCH": status_icon = "✅ MATCH"
        elif status == "MATCH (+EXTRA)": status_icon = "✅ MATCH"
        elif status == "AUDIT MISSING": status_icon = "🟡 AUDIT MISSING"
        elif status == "MISSING FILE": status_icon = "🔴 MISSING"
        else: status_icon = "⚠️ MISMATCH"
        
        print(f"{row['Table']:<30} | {row['Status']:<10} | {str(row['Rows']):<10} | {row['Size']:<10} | {row['Details']}")
        report_lines.append(f"| {row['Table']} | {status_icon} | {row['Rows']} | {row['Size']} | {row['Details']} |")

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

    df_extra = analyze_extra_files(modeled_files, parquet_dir)
    
    for _, row in df_extra.iterrows():
        print(f"{row['File Name']:<40} | {str(row['Rows']):<10} | {row['Size']:<10}")
        report_lines.append(f"| {row['File Name']} | {row['Guessed Table']} | {row['Rows']} | {row['Size']} |")

    with open("RECONCILIATION_REPORT.md", "w") as f:
        f.write("\n".join(report_lines))
    print("\nReport saved to RECONCILIATION_REPORT.md")
