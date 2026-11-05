import os
import sqlite3
import numpy as np
import pandas as pd



def run_part_a():
    print("\n=== STARTING PART A: DATA FOUNDATION ===")
    os.makedirs('data/clean', exist_ok=True)

    # Load raw data safely
    customers_raw = pd.read_csv('data/raw/customers.csv', keep_default_na=False)
    orders_raw = pd.read_csv('data/raw/orders.csv', keep_default_na=False)
    products_raw = pd.read_csv('data/raw/products.csv', keep_default_na=False)

    # 1. Clean Customers
    customers = customers_raw.copy()
    customers['city'] = customers['city'].astype(str).str.strip().str.title()
    gender_map = {'m': 'male', 'male': 'male', 'M': 'male', 'f': 'female', 'female': 'female', 'F': 'female'}
    customers['gender'] = customers['gender'].map(lambda x: gender_map.get(str(x).strip(), 'unknown')).fillna('unknown')
    customers['age'] = pd.to_numeric(customers['age'], errors='coerce')
    customers.loc[(customers['age'] < 10) | (customers['age'] > 100), 'age'] = np.nan
    customers['age'] = customers.groupby('city')['age'].transform(lambda x: x.fillna(x.median()))
    customers['signup_date'] = pd.to_datetime(customers['signup_date'])

    # 2. Clean Orders
    orders = orders_raw.copy()
    orders['order_ts'] = pd.to_datetime(orders['order_ts'])
    orders = orders.drop_duplicates()
    orders = orders.sort_values('order_ts').groupby('order_id').last().reset_index()

    # Link product pricing and categories using the raw products schema.
    product_details = products_raw[['product_id', 'price_inr', 'category']].rename(
        columns={'category': 'product_category'}
    )
    orders = orders.merge(product_details, on='product_id', how='left')
    orders['order_amount'] = pd.to_numeric(orders['order_amount'], errors='coerce')
    missing_amt = orders['order_amount'].isna()
    orders.loc[missing_amt, 'order_amount'] = np.round(
        orders.loc[missing_amt, 'price_inr'] * orders.loc[missing_amt, 'quantity'] * (1 - orders.loc[missing_amt, 'discount_pct'] / 100.0), 2
    )

    # Handle Delivery Window Imputation
    orders['delivery_minutes'] = pd.to_numeric(orders['delivery_minutes'], errors='coerce')
    orders.loc[orders['delivery_minutes'] < 0, 'delivery_minutes'] = np.nan
    category_medians = orders[orders['status'] == 'completed'].groupby('product_category')['delivery_minutes'].median()
    orders['delivery_minutes'] = orders.apply(
        lambda row: category_medians.get(row['product_category'], np.nan) if row['status'] == 'completed' and pd.isna(row['delivery_minutes']) else row['delivery_minutes'], axis=1
    )

    # Drop temp columns before exporting
    orders.drop(columns=['price_inr'], errors='ignore', inplace=True)

    # 3. Export Checkpoints & Populate DB
    customers.to_csv('data/clean/customers.csv', index=False)
    orders.to_csv('data/clean/orders.csv', index=False)

    db_conn = sqlite3.connect('data/instamart.db')
    customers.to_sql('customers', db_conn, if_exists='replace', index=False)
    orders.to_sql('orders', db_conn, if_exists='replace', index=False)
    products_raw.to_sql('products', db_conn, if_exists='replace', index=False)
    db_conn.close()

    print("Part A completed successfully. SQLite database populated.")
