# AutoDQ-Lite

AutoDQ-Lite is a **minimal, LLM-assisted data quality tool**. It:

* Profiles a CSV table (row count, null %, cardinality, sample values).
* Asks a local or cloud LLM to **propose practical DQ checks** (uniqueness, nulls, regex, ranges, set membership, foreign keys).
* Renders executable SQL for **Postgres**, **BigQuery**, or **Spark SQL**.
* Returns the DQ checks both as runnable SQL scripts **and as a structured DataFrame (CSV)** so you can inspect, filter, or visualize them.

This makes it ideal for quick demos, portfolio projects, or lightweight validation on Kaggle datasets.

---

## Quickstart (Windows)

```powershell
# 1. Setup
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# 2. Run with local Ollama (recommended for quick demo)
# Install Ollama from https://ollama.com and pull a small instruct model first:
#   ollama pull phi3:mini
python -m src.main --in examples\crocodile_dataset.csv --dialect bigquery --provider ollama --model llama3.2
```

Outputs:

* `profile.json` — schema profile (inferred stats).
* `checks.json` — LLM-proposed checks (with metadata).
* `checks_<dialect>.sql` — ready-to-run SQL assertions.
* `checks.csv` — DataFrame view of all checks and rules.

---

## Running with OpenAI GPT models

1. Set your API key (PowerShell):

```powershell
$env:OPENAI_API_KEY="sk-xxxxx"
```

2. Run:

```powershell
python -m src.main --in examples\crocodile_dataset.csv --dialect postgres --provider openai --model gpt-5
```

(Replace `gpt-5` with any available OpenAI model.)

---

## Improvements & Next Steps

* **Deterministic runs:** seed sampling so profiles are reproducible.
* **Caching:** avoid re-calling LLMs for the same table + prompt.
* **Validation:** enforce JSON schema for LLM output.
* **Baseline heuristics:** add regex/range checks without LLM dependency.
* **Evaluation:** run generated SQL on sample data, report failure counts.
* **RAG augmentation (V2):** inject domain-specific regexes (IBAN, phone numbers, etc.) into the prompt.

---

## Why AutoDQ-Lite?

* 🔑 **Lean:** \~250 LOC + 2 templates.
* ⚡ **Fast:** runs locally with Ollama, or cloud with OpenAI.
* 📦 **Practical:** outputs JSON, SQL, and CSV for real analysis.
* 🎯 **Portfolio-ready:** shows off data/AI engineering skills without bloated frameworks.
