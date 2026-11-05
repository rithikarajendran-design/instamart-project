
### Instamart Copilot - Capstone Project

## Reproducible Setup

To set up the project and reproduce the data pipeline from scratch, follow these numbered steps:

1. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate

```
 2. Install the required libraries and generate the requirements.txt file:
   ```bash
   pip install -r requirements.txt
   pip freeze > requirements.txt
   
   ```
 3. Generate the raw data by running:
   ```bash
   python generate_data.py
   
   ```
 4. Run the data cleaning and validation scripts to clean the raw data and verify checkpoints:
   ```bash
   python validate.py
   
   ```
 5. Execute the SQL queries against the SQLite database:
   ```bash
   python run_queries.py
   
   ```
 6. Execute all capstone pipeline steps:
    ```bash
    python run_project.py
    ```

   Open `Instamart_copilot.ipynb` and run cells from top to bottom. The notebook calls the same modules used by the scripts.

   
## Repository map:

- `generate_data.py`: deterministic fictional CSV and policy generation.
- `mock_llm.py`: offline stand-in for classification, policy answers and agent tool calls.
- `part_a.py`: audit, clean, SQLite load, validation.
- `part_b.py`: Customer segments and lapse prdiction.
- `part_c.py`: token guardrails, PII redaction, retries, response validation, routing.
- `part_d.py`: chunking, TF-IDF retrieval and grounded policy evaluation,
               refund calculation, ledger and bounded tool loop.
- `sql/queries.sql`: seven SQL learning patterns.
- `outputs/`: generated artifacts; `state/`: agent checkpoint examples.


## Part A: Data Foundation

  ## Data Cleaning Documentation (Task 4)
Below are the documentation rules and changes applied during data cleaning:
 * **Order Timestamp (order_ts):** Converted to standard datetime format.
 * **Duplicates:** Exact duplicate rows were identified and removed.
 * **Status Conflicts:** Where orders appeared multiple times with different statuses (pending vs. final), only the record with the latest order_ts was retained.
 * **Order Amounts:** Unparseable entries were converted to missing values, and then imputed using product price, quantity, and discount formulas.
 * **Delivery Minutes:** Negative delivery times were set to missing, and completed orders had missing delivery times imputed using the median delivery time of their respective product categories.
## SQL Analysis Notes (Task 6.vi)
In query Q6, RANK(), DENSE_RANK(), and ROW_NUMBER() produce different results for rows with identical total_spend values because RANK() leaves gaps in ranking sequences after ties, DENSE_RANK() assigns consecutive ranks without gaps, and ROW_NUMBER() assigns unique sequential numbers arbitrarily based on physical row order.
```

```
## Part B — Segments and lapse
RFM uses completed orders and a fixed snapshot date. K-means diagnostics compare K=2..8; the notebook starts with K=4 for interpretable teaching. Lapse features use orders strictly before 2025-09-01, while the label uses September outcomes. The pipeline uses a preprocessing Pipeline fitted on training rows, GridSearchCV and a saved joblib model. The Premium retention list is illustrative only because the Premium label uses the whole RFM window and is post-hoc; it is not a leakage-free evaluation.

## Part C — Ticket triage and privacy
Empty and overlong tickets are skipped before model calls. Email, phone and order ID patterns are redacted before prompting. Retries handle simulated transient errors. JSON category values are allow-listed; malformed outputs are accepted only when exactly one allowed category is detectable using `re.findall`. Human review receives guardrail/invalid/budget cases, fraud goes to security, premium customers go to the premium desk, and the rest go to the support queue.

## Part D — Policy retrieval and refund tools
Policy documents are chunked with overlap, represented with `TfidfVectorizer`, and ranked using cosine similarity. The offline mock returns context-derived sentences. Refund rules are implemented in Python tools backed by SQLite: completed orders delivered in over 45 minutes qualify for a full refund; orders over INR 1000 escalate instead of auto-issuing. This is a teaching simulation, not a payment integration.

## GitHub suggestions
These public repositories/documentation projects are useful for learning concepts; do not copy a student's capstone solution. Adapt the patterns and cite the source in your notes:
- pandas documentation: https://github.com/pandas-dev/pandas — CSV loading, cleaning, groupby, pivot tables.
- scikit-learn: https://github.com/scikit-learn/scikit-learn — pipelines, preprocessing, clustering, model selection, metrics and TF-IDF.
- Python tutorial: https://github.com/python/cpython/tree/main/Doc/tutorial — Python fundamentals.
- Jupyter Notebook: https://github.com/jupyter/notebook — notebook workflow.
- SQLite: https://github.com/sqlite/sqlite — SQL database engine (official mirror).
- scikit-learn text feature extraction guide: https://scikit-learn.org/stable/modules/feature_extraction.html#text-feature-extraction.

## Limitations and next steps
- This is a teaching implementation and may need adjustment to match every numeric checkpoint in a strict grading rubric; compare actual outputs with the supplied brief and investigate differences rather than hardcoding expected answers.
- The offline mock model is deterministic rule-based simulation, not a real language model.
- The refund ledger is a local JSONL audit trail, not a real transaction system.
- Production work would add access controls, secure secret management, monitoring, schema contracts, data lineage, model drift checks and human approval workflows.
