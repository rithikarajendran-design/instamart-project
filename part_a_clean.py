import csv
import os
import sqlite3
from collections import defaultdict
from datetime import datetime
from statistics import median


def safe_float(value):
    if value is None:
        return None
    value = str(value).strip()
    if value == "" or value.lower() in {"na", "n/a", "nan", "null", "none", "error"}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_date(value):
    if value is None:
        return None
    value = str(value).strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def normalize_city(value):
    return str(value).strip().title() if value is not None else ""


def write_csv(path, fieldnames, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            clean_row = {}
            for field in fieldnames:
                value = row.get(field)
                if value is None:
                    clean_row[field] = ""
                elif isinstance(value, float) and value.is_integer():
                    clean_row[field] = str(int(value))
                else:
                    clean_row[field] = str(value)
            writer.writerow(clean_row)


# 1. Load raw data
with open("data/raw/customers.csv", newline="", encoding="utf-8") as f:
    customers = list(csv.DictReader(f))
with open("data/raw/products.csv", newline="", encoding="utf-8") as f:
    products = list(csv.DictReader(f))
with open("data/raw/orders.csv", newline="", encoding="utf-8") as f:
    orders = list(csv.DictReader(f))

# 2. Clean customers data
for customer in customers:
    customer["city"] = normalize_city(customer.get("city"))
    age = safe_float(customer.get("age"))
    if age is not None and (age < 10 or age > 100):
        age = None
    customer["age"] = age
    signup_date = customer.get("signup_date")
    customer["signup_date"] = signup_date.strip() if signup_date and signup_date.strip() else ""
    if customer["signup_date"]:
        parsed_signup = parse_date(customer["signup_date"])
        customer["signup_date"] = parsed_signup.strftime("%Y-%m-%d") if parsed_signup else ""

city_age_map = defaultdict(list)
for customer in customers:
    if customer["age"] is not None:
        city_age_map[customer["city"]].append(customer["age"])

city_medians = {
    city: median(values) if values else None
    for city, values in city_age_map.items()
}
for customer in customers:
    if customer["age"] is None:
        customer["age"] = city_medians.get(customer["city"])

# 3. Clean orders data
# Remove exact duplicates before resolving duplicate order_ids
seen = set()
cleaned_orders = []
for order in orders:
    key = tuple((k, str(v)) for k, v in sorted(order.items()))
    if key not in seen:
        seen.add(key)
        cleaned_orders.append(order)

orders = cleaned_orders

for order in orders:
    order["order_ts"] = str(order.get("order_ts", "")).strip()
    parsed_ts = parse_date(order["order_ts"])
    order["_order_ts_dt"] = parsed_ts
    amount = safe_float(order.get("order_amount"))
    order["order_amount"] = amount
    discount = safe_float(order.get("discount_pct"))
    order["discount_pct"] = discount
    delivery = safe_float(order.get("delivery_minutes"))
    if delivery is not None and delivery < 0:
        delivery = None
    order["delivery_minutes"] = delivery
    order["status"] = str(order.get("status", "")).strip().lower()

order_id_map = defaultdict(list)
for order in orders:
    order_id_map[order["order_id"]].append(order)

final_orders = []
for order_id, group in order_id_map.items():
    winner = max(
        group,
        key=lambda row: row["_order_ts_dt"] if row["_order_ts_dt"] else datetime.min,
    )
    final_orders.append(winner)
orders = sorted(final_orders, key=lambda row: row["order_id"])

products_by_id = {
    product["product_id"]: product for product in products
}
for order in orders:
    if order["order_amount"] is None:
        product = products_by_id.get(order.get("product_id"))
        if product is not None:
            price = safe_float(product.get("price_inr"))
            quantity = safe_float(order.get("quantity"))
            discount = safe_float(order.get("discount_pct"))
            if price is not None and quantity is not None and discount is not None:
                order["order_amount"] = round(
                    price * quantity * (1 - discount / 100),
                    2,
                )

# completed orders: infer missing delivery_minutes from category median
completed_by_category = defaultdict(list)
for order in orders:
    product = products_by_id.get(order.get("product_id"))
    if order["status"] == "completed" and order["delivery_minutes"] is not None and product:
        completed_by_category[product.get("category")].append(order["delivery_minutes"])

category_medians = {
    category: median(values) if values else None
    for category, values in completed_by_category.items()
}
for order in orders:
    if order["status"] == "cancelled":
        order["delivery_minutes"] = None
        continue
    if order["status"] == "completed" and order["delivery_minutes"] is None:
        product = products_by_id.get(order.get("product_id"))
        if product:
            order["delivery_minutes"] = category_medians.get(product.get("category"))

# Clean numeric fields for CSV output
for order in orders:
    quantity = safe_float(order.get("quantity"))
    order["quantity"] = int(quantity) if quantity is not None and int(quantity) == quantity else quantity
    if order["order_amount"] is not None:
        order["order_amount"] = round(float(order["order_amount"]), 2)
    if order["delivery_minutes"] is not None:
        order["delivery_minutes"] = round(float(order["delivery_minutes"]), 2)
    order["order_ts"] = order["order_ts"][:19] if order["order_ts"] and len(order["order_ts"]) >= 19 else order["order_ts"]

# 4. Store cleaned data to CSV and SQLite database
os.makedirs("data/clean", exist_ok=True)

customers_out = []
for customer in customers:
    customers_out.append(
        {
            "customer_id": customer.get("customer_id"),
            "city": customer.get("city"),
            "signup_date": customer.get("signup_date"),
            "age": customer.get("age"),
            "gender": customer.get("gender"),
        }
    )

products_out = [
    {
        "product_id": product.get("product_id"),
        "product_name": product.get("product_name"),
        "category": product.get("category"),
        "price_inr": safe_float(product.get("price_inr")),
    }
    for product in products
]

orders_out = [
    {
        "order_id": order.get("order_id"),
        "customer_id": order.get("customer_id"),
        "product_id": order.get("product_id"),
        "quantity": order.get("quantity"),
        "order_ts": order.get("order_ts"),
        "status": order.get("status"),
        "discount_pct": order.get("discount_pct"),
        "order_amount": order.get("order_amount"),
        "delivery_minutes": order.get("delivery_minutes"),
    }
    for order in orders
]

write_csv(
    "data/clean/customers.csv",
    ["customer_id", "city", "signup_date", "age", "gender"],
    customers_out,
)
write_csv(
    "data/clean/products.csv",
    ["product_id", "product_name", "category", "price_inr"],
    products_out,
)
write_csv(
    "data/clean/orders.csv",
    ["order_id", "customer_id", "product_id", "quantity", "order_ts", "status", "discount_pct", "order_amount", "delivery_minutes"],
    orders_out,
)

conn = sqlite3.connect("data/instamart.db")
conn.execute("DROP TABLE IF EXISTS customers")
conn.execute("DROP TABLE IF EXISTS products")
conn.execute("DROP TABLE IF EXISTS orders")

conn.execute(
    "CREATE TABLE customers (customer_id TEXT, city TEXT, signup_date TEXT, age REAL, gender TEXT)"
)
conn.execute(
    "CREATE TABLE products (product_id TEXT, product_name TEXT, category TEXT, price_inr REAL)"
)
conn.execute(
    "CREATE TABLE orders (order_id TEXT, customer_id TEXT, product_id TEXT, quantity INTEGER, order_ts TEXT, status TEXT, discount_pct REAL, order_amount REAL, delivery_minutes REAL)"
)

conn.executemany(
    "INSERT INTO customers (customer_id, city, signup_date, age, gender) VALUES (?, ?, ?, ?, ?)",
    [
        (
            row["customer_id"],
            row["city"],
            row["signup_date"],
            row["age"],
            row["gender"],
        )
        for row in customers_out
    ],
)
conn.executemany(
    "INSERT INTO products (product_id, product_name, category, price_inr) VALUES (?, ?, ?, ?)",
    [
        (
            row["product_id"],
            row["product_name"],
            row["category"],
            row["price_inr"],
        )
        for row in products_out
    ],
)
conn.executemany(
    "INSERT INTO orders (order_id, customer_id, product_id, quantity, order_ts, status, discount_pct, order_amount, delivery_minutes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
    [
        (
            row["order_id"],
            row["customer_id"],
            row["product_id"],
            row["quantity"],
            row["order_ts"],
            row["status"],
            row["discount_pct"],
            row["order_amount"],
            row["delivery_minutes"],
        )
        for row in orders_out
    ],
)
conn.commit()
conn.close()

print("Part A Data Cleaning and Storing Completed Successfully!")

