import os
import pandas as pd

# Define input file paths
products_path = (
    "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/"
    "products_raw.csv"
)
orders_path = (
    "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/"
    "orders_raw.csv"
)
customers_path = (
    "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/"
    "2/_reference/dedup_hard/output.parquet"
)
output_path = (
    "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/"
    "transform/google_v3_chain_of_thought_r2/output.parquet"
)

# Step 1: Read and convert 'products' dataset
# - Read products CSV
products = pd.read_csv(products_path)

# - Convert price_eur to float: remove currency symbols/text, swap comma to dot, convert to float
price_clean = (
    products["price_eur"]
    .astype(str)
    .str.replace("€", "", regex=False)
    .str.replace("EUR", "", regex=False)
    .str.strip()
    .str.replace(",", ".", regex=False)
)
products["price_eur"] = pd.to_numeric(price_clean, errors="coerce")

# - Convert in_stock to boolean: map standard true/false representations
in_stock_clean = products["in_stock"].astype(str).str.strip().str.lower()
true_values = {"ja", "true", "1", "yes", "t"}
false_values = {"nein", "false", "0", "no", "f"}
products["in_stock"] = in_stock_clean.map(
    lambda val: (
        True if val in true_values else (False if val in false_values else None)
    )
).astype("boolean")

# Step 2: Read and transform 'orders' dataset
# - Read orders CSV
orders = pd.read_csv(orders_path)

# - Calculate total_eur = quantity * unit_price_eur
orders["total_eur"] = orders["quantity"] * orders["unit_price_eur"]

# - Parse ordered_at and extract order_year and order_month
ordered_at_dt = pd.to_datetime(orders["ordered_at"], errors="coerce")
orders["order_year"] = ordered_at_dt.dt.year.astype("Int64")
orders["order_month"] = ordered_at_dt.dt.month.astype("Int64")

# Step 3: Read 'customers' dataset, join, aggregate and format final result
# - Read customers Parquet file
customers = pd.read_parquet(customers_path)

# - Rename 'country' column to 'country_code'
customers = customers.rename(columns={"country": "country_code"})

# - Merge orders with customers and products (inner join to drop unmatched records)
merged = orders.merge(customers, on="customer_id", how="inner").merge(
    products, on="product_id", how="inner"
)

# - Filter out invalid / missing country_code and category
merged = merged.dropna(subset=["country_code", "category"])
merged = merged[
    (merged["country_code"].astype(str).str.strip() != "")
    & (merged["category"].astype(str).str.strip() != "")
]

# - Compute revenue per row (quantity * unit_price_eur)
merged["revenue"] = merged["quantity"] * merged["unit_price_eur"]

# - Aggregate per country_code and category
aggregated = (
    merged.groupby(["country_code", "category"], as_index=False)
    .agg(total_revenue_eur=("revenue", "sum"), order_count=("order_id", "count"))
    .sort_values(by="total_revenue_eur", ascending=False)
    .reset_index(drop=True)
)

# Step 4: Write result to Parquet file
os.makedirs(os.path.dirname(output_path), exist_ok=True)
aggregated.to_parquet(output_path, index=False)