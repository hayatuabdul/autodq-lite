import pandas as pd
from src.utils.postprocessing import generate_sql_check_query


def create_dq_summary_dataframe(checks_data: list = None, profile_data: dict = None, table_name: str = "your_table"):
    """
    Create a summary DataFrame from DQ checks and profile data.
    
    Args:
        checks_data: Direct checks data (list of check dictionaries)
        profile_data: Direct profile data (profile dictionary)
        table_name: Name of the table for SQL queries (default: "your_table")
    
    Returns:
        pandas.DataFrame: Summary with columns [column_name, column_type, check_type, sql_rule, description]
    """
    
    # Load checks data
    if checks_data is not None:
        checks = checks_data

    print(f"checks type: {type(checks)}")
    print(f"profile data type: {type(profile_data)}")
    
    # Load profile data for column types (if available)
    column_types = {}
    if profile_data is not None:
        for col in profile_data.get('columns', []):
            column_types[col['name']] = col['dtype']
    
    # Build summary data
    summary_data = []
    
    for check in checks:
        # Extract information from each check
        column_name = check.get('column', 'unknown')
        check_type = check.get('check_type', 'unknown')
        description = check.get('description', 'No description')
        
        # Get column type from profile if available
        column_type = column_types.get(column_name, 'unknown')
        
        # Generate proper SQL query instead of using generic sql_condition
        sql_rule = generate_sql_check_query(column_name, check_type, table_name)
        
        # If LLM provided a specific SQL condition and it's not just "TRUE", use that instead
        llm_sql = check.get('sql_condition', 'TRUE')
        if llm_sql and llm_sql.strip() != 'TRUE' and 'SELECT' in llm_sql.upper():
            sql_rule = llm_sql
        
        summary_data.append({
            'column_name': column_name,
            'column_type': column_type,
            'check_type': check_type,
            'sql_rule': sql_rule,
            'description': description
        })
    
    # Create DataFrame
    df = pd.DataFrame(summary_data)
    
    # Sort by column name for better organization
    df = df.sort_values('column_name').reset_index(drop=True)
    
    return df


def create_dq_summary_from_files(checks_file: str = 'checks.json', 
                                profile_file: str = 'profile.json'):
    """
    Convenience function to create summary DataFrame from default file locations.
    
    Args:
        checks_file: Path to checks JSON file
        profile_file: Path to profile JSON file
    
    Returns:
        pandas.DataFrame: DQ summary DataFrame
    """
    import os
    
    # Check if profile file exists
    profile_path = profile_file if os.path.exists(profile_file) else None
    
    return create_dq_summary_dataframe(
        checks_json_path=checks_file,
        profile_json_path=profile_path
    )


def save_dq_summary(df: pd.DataFrame, output_path: str = 'dq_summary.csv'):
    """
    Save the DQ summary DataFrame to CSV.
    
    Args:
        df: DQ summary DataFrame
        output_path: Output CSV file path
    """
    df.to_csv(output_path, index=False)
    print(f"DQ summary saved to: {output_path}")