from jinja2 import Environment, FileSystemLoader
import pandas as pd
import os

def profile_csv(csv_path: str, sample_rows: int = 5000):
    """Profile a CSV file to understand its structure and data types."""
    print(f"Reading CSV file: {csv_path}")
    
    # Read CSV with sample
    df = pd.read_csv(csv_path, nrows=sample_rows)
    
    print(f"Loaded {len(df)} rows, {len(df.columns)} columns")
    
    profile = {
        "file_path": csv_path,
        "total_rows": int(len(df)),
        "total_columns": int(len(df.columns)),
        "columns": []
    }
    
    for col in df.columns:
        col_info = {
            "name": str(col),
            "dtype": str(df[col].dtype),
            "null_count": int(df[col].isnull().sum()),
            "null_percentage": float((df[col].isnull().sum() / len(df)) * 100),
            "unique_count": int(df[col].nunique()),
            "sample_values": [convert_to_json_serializable(val) for val in df[col].dropna().head(5).tolist()]
        }
        
        # Add numeric stats if numeric
        if pd.api.types.is_numeric_dtype(df[col]):
            col_info.update({
                "min": convert_to_json_serializable(df[col].min()),
                "max": convert_to_json_serializable(df[col].max()),
                "mean": convert_to_json_serializable(df[col].mean()),
                "std": convert_to_json_serializable(df[col].std())
            })
        
        profile["columns"].append(col_info)
    
    return profile


def convert_to_json_serializable(obj):
    """Convert pandas/numpy types to JSON serializable types."""
    if pd.isna(obj):
        return None
    elif hasattr(obj, 'item'):  # numpy types
        return obj.item()
    elif isinstance(obj, (pd.Timestamp, pd.Timedelta)):
        return str(obj)
    else:
        return obj

def make_env(sql_dialect: str):
    """Create Jinja2 environment with custom functions."""
    # Look for templates in current directory or templates folder
    template_dirs = ['.', 'templates', 'src/templates']
    
    for template_dir in template_dirs:
        if os.path.exists(template_dir):
            env = Environment(loader=FileSystemLoader(template_dir))
            break
    else:
        # Default to current directory
        env = Environment(loader=FileSystemLoader('.'))
    
    def regex_fn(column, pattern):
        """Generate SQL regex expression based on dialect."""
        if sql_dialect == 'postgres':
            return f"{column} ~ '{pattern}'"
        if sql_dialect == 'bigquery':
            return f"REGEXP_CONTAINS(CAST({column} AS STRING), r'{pattern}')"
        if sql_dialect == 'spark':
            return f"{column} RLIKE '{pattern}'"
        return f"REGEXP_CONTAINS({column}, '{pattern}')"
    
    # Add custom functions to Jinja2 environment
    env.globals.update(regex_fn=regex_fn)
    
    return env