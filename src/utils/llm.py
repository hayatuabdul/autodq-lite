import json
import requests
from src.utils.profile import make_env


def build_prompt(profile):
    """Build prompt from profile using Jinja2 template."""
    env = make_env('postgres')
    
    try:
        tmpl = env.get_template('src/prompts/dq_prompt.j2')
        return tmpl.render(profile=profile)
    except:
        # Fallback prompt if template doesn't exist
        print("Template 'dq_prompt.j2' not found, using fallback prompt")
        return f"""
    Analyze this CSV data profile and generate data quality checks:

    {json.dumps(profile, indent=2)}

    Generate a JSON array of data quality checks. Each check should have:
    - "column": column name
    - "check_type": type of check (null_check, range_check, pattern_check, etc.)
    - "description": human readable description
    - "sql_condition": the condition that should be true for good data

    Return only a valid JSON array of checks.
    """


def ask_ollama(model: str, prompt: str):
    """Send prompt to Ollama and get response."""
    print(f"Sending request to Ollama model: {model}")
    
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload, timeout=300)
        response.raise_for_status()
        result = response.json()
        return result.get("response", "")
    except requests.exceptions.ConnectionError:
        raise ConnectionError("Cannot connect to Ollama. Make sure Ollama is running with: ollama serve")
    except requests.exceptions.Timeout:
        raise TimeoutError("Request to Ollama timed out")
    except Exception as e:
        raise Exception(f"Error calling Ollama: {e}")


def ask_openai(model: str, api_key: str, prompt: str):
    """Send prompt to OpenAI and get response."""
    if not api_key:
        raise ValueError("OpenAI API key is required")
    
    print(f"Sending request to OpenAI model: {model}")
    
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4000
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=300)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        raise Exception(f"Error calling OpenAI: {e}")
