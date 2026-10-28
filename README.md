
# Instamart Copilot - Part A: Data Foundation

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


