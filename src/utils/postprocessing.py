from src.utils.profile import make_env
import re
import json


def parse_json_list(txt: str):
    """Extract and parse JSON array from text response."""
    print("Parsing JSON from LLM response...")
    
    # Try to find JSON array in the response - be more flexible with whitespace
    patterns = [
        r"\[.*?\]",  # Standard array
        r"```json\s*(\[.*?\])\s*```",  # Markdown code block
        r"```\s*(\[.*?\])\s*```",  # Code block without json
    ]
    
    json_text = None
    for pattern in patterns:
        m = re.search(pattern, txt, flags=re.S | re.M)
        if m:
            json_text = m.group(1) if m.groups() else m.group(0)
            break
    
    if not json_text:
        print("Response text:", txt[:500] + "..." if len(txt) > 500 else txt)
        raise ValueError("LLM did not return a JSON array of checks")
    
    try:
        raw_checks = json.loads(json_text)
        
        # Normalize the check format - handle different field names
        normalized_checks = []
        for check in raw_checks:
            normalized_check = normalize_check_format(check)
            normalized_checks.append(normalized_check)
            
        return normalized_checks
        
    except json.JSONDecodeError as e:
        print("JSON parsing error:", e)
        print("Extracted text:", json_text[:500] + "..." if len(json_text) > 500 else json_text)
        
        # Try to fix common JSON issues
        try:
            fixed_json = fix_common_json_issues(json_text)
            raw_checks = json.loads(fixed_json)
            return [normalize_check_format(check) for check in raw_checks]
        except:
            pass
            
        raise ValueError(f"Invalid JSON in LLM response: {e}")


def normalize_check_format(check) -> dict:
    """Normalize different check formats to a standard format."""
    # Handle case where check might be a string or other type
    if isinstance(check, str):
        print(f"Warning: Found string instead of dict: {check[:100]}...")
        return {
            "column": "unknown",
            "check_type": "unknown", 
            "description": check[:100] if len(check) > 100 else check,
            "sql_condition": "TRUE"
        }
    
    if not isinstance(check, dict):
        print(f"Warning: Found {type(check)} instead of dict: {check}")
        return {
            "column": "unknown",
            "check_type": "unknown", 
            "description": "Invalid check format",
            "sql_condition": "TRUE"
        }
    
    normalized = {
        "column": "unknown",
        "check_type": "unknown", 
        "description": "No description",
        "sql_condition": "TRUE"
    }
    
    # Map different field names to our standard format
    field_mappings = {
        "column": ["column", "column_name", "field", "field_name"],
        "check_type": ["check_type", "type", "rule_type", "validation_type"],
        "description": ["description", "title", "message", "rule_description"],
        "sql_condition": ["sql_condition", "condition", "rule", "sql_rule", "validation_rule"]
    }
    
    for standard_field, possible_fields in field_mappings.items():
        for field in possible_fields:
            if field in check:
                normalized[standard_field] = str(check[field])
                break
    
    return normalized


def fix_common_json_issues(json_text: str) -> str:
    """Try to fix common JSON formatting issues."""
    # Remove trailing commas
    json_text = re.sub(r',\s*}', '}', json_text)
    json_text = re.sub(r',\s*]', ']', json_text)
    
    # Fix unescaped quotes in strings
    json_text = re.sub(r'(?<!\\)"(?![\s,}\]])', r'\"', json_text)
    
    # Try to complete truncated JSON
    if not json_text.strip().endswith(']'):
        # Count opening and closing brackets
        open_brackets = json_text.count('[')
        close_brackets = json_text.count(']')
        open_braces = json_text.count('{')
        close_braces = json_text.count('}')
        
        # Add missing closing braces/brackets
        json_text += '}' * (open_braces - close_braces)
        json_text += ']' * (open_brackets - close_brackets)
    
    return json_text


def generate_sql_check_query(column_name: str, check_type: str, table_name: str = "your_table"):
    """Generate actual SQL query for a data quality check."""
    
    # Clean column name for SQL (handle spaces and special chars)
    clean_column = f"`{column_name}`" if " " in column_name or "/" in column_name else column_name
    
    if check_type.lower() in ['null', 'null_check', 'not_null']:
        return f"SELECT COUNT(*) as failed_records FROM {table_name} WHERE {clean_column} IS NULL"
    
    elif check_type.lower() in ['uniqueness', 'unique', 'duplicate']:
        return f"SELECT {clean_column}, COUNT(*) as duplicate_count FROM {table_name} GROUP BY {clean_column} HAVING COUNT(*) > 1"
    
    elif check_type.lower() in ['length', 'string_length', 'text_length']:
        return f"SELECT COUNT(*) as failed_records FROM {table_name} WHERE LENGTH({clean_column}) = 0 OR {clean_column} = ''"
    
    elif check_type.lower() in ['range', 'numeric_range', 'value_range']:
        if 'length' in column_name.lower():
            return f"SELECT COUNT(*) as failed_records FROM {table_name} WHERE {clean_column} < 0 OR {clean_column} > 100"
        elif 'weight' in column_name.lower():
            return f"SELECT COUNT(*) as failed_records FROM {table_name} WHERE {clean_column} < 0 OR {clean_column} > 10000"
        elif 'age' in column_name.lower():
            return f"SELECT COUNT(*) as failed_records FROM {table_name} WHERE {clean_column} < 0 OR {clean_column} > 200"
        else:
            return f"SELECT COUNT(*) as failed_records FROM {table_name} WHERE {clean_column} IS NULL OR {clean_column} < 0"
    
    elif check_type.lower() in ['format', 'pattern', 'regex']:
        if 'email' in column_name.lower():
            return f"SELECT COUNT(*) as failed_records FROM {table_name} WHERE {clean_column} NOT REGEXP '^[^@]+@[^@]+\\.[^@]+"


def render_sql(checks, sql_dialect: str):
    """Render SQL checks using Jinja2 template."""
    env = make_env(sql_dialect)
    
    try:
        tmpl = env.get_template('src/templates/checks.sql.j2')
        return tmpl.render(checks=checks, dialect=sql_dialect)
    except:
        # Fallback SQL generation if template doesn't exist
        print("Template 'checks.sql.j2' not found, using fallback SQL generation")
        
        sql_parts = [f"-- Data Quality Checks for {sql_dialect}", ""]
        
        for i, check in enumerate(checks, 1):
            sql_parts.append(f"-- Check {i}: {check.get('description', 'No description')}")
            sql_parts.append(f"SELECT '{check.get('check_type', 'unknown')}' as check_type,")
            sql_parts.append(f"       '{check.get('column', 'unknown')}' as column_name,")
            sql_parts.append(f"       COUNT(*) as failed_records")
            sql_parts.append(f"FROM your_table")
            sql_parts.append(f"WHERE NOT ({check.get('sql_condition', 'TRUE')});")
            sql_parts.append("")
        
        return "\n".join(sql_parts)
