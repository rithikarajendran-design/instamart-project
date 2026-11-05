import os
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
import joblib

def run_part_b():
    print("\n=== STARTING PART B: CUSTOMER SEGMENTS AND LAPSE PREDICTION ===")
    os.makedirs('outputs', exist_ok=True)

    orders = pd.read_csv('data/clean/orders.csv')
    orders['order_ts'] = pd.to_datetime(orders['order_ts'])
    completed_orders = orders[orders['status'] == 'completed'].copy()

    # 1. RFM Table Build
    snapshot = pd.to_datetime('2025-10-01 00:00:00')
    rfm = completed_orders.groupby('customer_id').agg(
        recency=('order_ts', lambda x: (snapshot - x.max()).days),
        frequency=('order_id', 'nunique'),
        monetary=('order_amount', 'sum')
    ).reset_index()

    # 2. K-Means Clustering (Standardized Configuration)
    scaler = StandardScaler()
    scaled_rfm = scaler.fit_transform(rfm[['recency', 'frequency', 'monetary']])

    kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
    rfm['cluster_label'] = kmeans.fit_predict(scaled_rfm)

    # Profile premium cohort (highest mean monetary metric value)
    premium_cluster = rfm.groupby('cluster_label')['monetary'].mean().idxmax()
    rfm['is_premium'] = (rfm['cluster_label'] == premium_cluster).astype(int)

    # 3. Lapse Prediction Dataset Building
    cutoff_date = pd.to_datetime('2025-09-01')
    historical = completed_orders[completed_orders['order_ts'] < cutoff_date]
    label_window = completed_orders[(completed_orders['order_ts'] >= cutoff_date) & (completed_orders['order_ts'] <= pd.to_datetime('2025-09-30'))]

    active_cohort = historical['customer_id'].unique()
    active_later = label_window['customer_id'].unique()

    ml_data = pd.DataFrame({'customer_id': active_cohort})
    ml_data['lapsed'] = ml_data['customer_id'].apply(lambda x: 0 if x in active_later else 1)

    features = historical.groupby('customer_id').agg(
        recency=('order_ts', lambda x: (cutoff_date - x.max()).days),
        frequency=('order_id', 'nunique'),
        avg_amount=('order_amount', 'mean')
    ).reset_index()

    ml_data = ml_data.merge(features, on='customer_id', how='left')
    ml_data = ml_data.merge(rfm[['customer_id', 'is_premium']], on='customer_id', how='left').fillna(0)

    # 4. Train Model & Save Artifacts
    X = ml_data[['recency', 'frequency', 'avg_amount', 'is_premium']]
    y = ml_data['lapsed']

    if len(X) > 10:  # Prevent breaking on tiny test sets
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
        model = LogisticRegression(max_iter=1000, random_state=42)
        model.fit(X_train, y_train)

        # Save retention probabilities output
        ml_data['lapse_probability'] = model.predict_proba(X)[:, 1]
        ml_data.sort_values(by='lapse_probability', ascending=False).to_csv('outputs/retention_list.csv', index=False)
        joblib.dump(model, 'outputs/lapse_model.joblib')

    print("Part B completed successfully. Model and retention_list saved.")
