import argparse
import json
import os
from src.utils.profile import profile_csv
from src.utils.llm import build_prompt, ask_ollama, ask_openai
from src.utils.postprocessing import parse_json_list, render_sql, generate_sql_check_query
from src.utils.create_output_df import create_dq_summary_dataframe, save_dq_summary
import traceback

# --------------------------- CLI ---------------------------

def main():
    """Main CLI function."""
    print("Starting AutoDQ-Lite...")
    
    ap = argparse.ArgumentParser(description='AutoDQ-Lite — LLM-assisted DQ checks')
    ap.add_argument('--in', dest='inp', required=True, help='Path to CSV file')
    ap.add_argument('--dialect', default='bigquery', 
                    choices=['postgres', 'bigquery', 'spark'])
    ap.add_argument('--provider', default='ollama', 
                    choices=['ollama', 'openai'])
    ap.add_argument('--model', default='llama3.2')
    ap.add_argument('--api_key', default=os.getenv('OPENAI_API_KEY', ''))
    ap.add_argument('--sample_rows', type=int, default=5000)
    ap.add_argument('--out', default=None, 
                    help='Output SQL path; default checks_<dialect>.sql')
    
    args = ap.parse_args()
    
    print(f"Processing file: {args.inp}")
    print(f"Using dialect: {args.dialect}")
    print(f"Using provider: {args.provider}, model: {args.model}")
    
    # Extract table name from file path for better SQL generation
    table_name = os.path.splitext(os.path.basename(args.inp))[0]
    
    # Profile the CSV file
    print("Profiling CSV...")
    prof = profile_csv(args.inp, sample_rows=args.sample_rows)
    with open('profile.json', 'w') as f:
        json.dump(prof, f, indent=2)
    print("Saved profile.json")
    
    # Generate prompt and get LLM response
    print("Building prompt...")
    prompt = build_prompt(prof)
    print("Sending request to LLM...")
    
    try:
        if args.provider == 'ollama':
            raw = ask_ollama(args.model, prompt)
        else:
            raw = ask_openai(args.model, args.api_key, prompt)
        
        print("Got LLM response")
        
        # Parse checks from LLM response
        checks = parse_json_list(raw)
        print(f"Parsed {len(checks)} data quality checks")
        
        with open('checks.json', 'w') as f:
            json.dump(checks, f, indent=2)
        print("Saved checks.json")
        
        # Generate SQL and write to file
        out_path = args.out or f"checks_{args.dialect}.sql"
        sql = render_sql(checks, args.dialect)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(sql)
        
        print(f"✅ Success! Wrote: profile.json, checks.json, {out_path}")

        # Create DQ summary DataFrame with proper parameters
        print("Creating DQ summary...")
        output_df = create_dq_summary_dataframe(
            checks_data=checks,           # Pass the checks list
            profile_data=prof,            # Pass the profile dict
            table_name=table_name         # Use extracted table name
        )
        
        # Display preview
        print("\nDQ Summary Preview:")
        print(output_df.head())
        
        # Save to CSV
        save_dq_summary(output_df, 'dq_summary.csv')
        print(f"✅ DQ Summary saved to: dq_summary.csv")
        
    except Exception as e:
        traceback.print_exc()
        print(f"❌ Error: {e}")
        return 1


if __name__ == '__main__':
    main()