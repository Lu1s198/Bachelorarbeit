import os
import re
import pandas as pd

input_dir = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_composite/2/codegen/google_v1_zero_shot/output.parquet"

customers = pd.read_csv(os.path.join(input_dir, "customers_raw.csv"))
products = pd.read_csv(os.path.join(input_dir, "products_raw.csv"))
orders = pd.read_csv(os.path.join(input_dir, "orders_raw.csv"))

for col in customers.columns:
    if customers[col].dtype == "object" or isinstance(customers[col].dtype, pd.StringDtype):
        customers[col] = customers[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

def map_country_code(val):
    if pd.isna(val) or val is None:
        return "UNKNOWN"
    val_str = str(val).strip()
    if not val_str:
        return "UNKNOWN"
    
    clean = re.sub(r"[^A-Z]", "", val_str.upper())
    
    if clean in ["DEUTSCHLAND", "GERMANY", "GER", "DEUTSHCLAND", "DEUTSCLAND", "DEUTSCHLND", "DE", "DEU", "ALLEMAGNE"]:
        return "DE"
    if clean in ["OESTERREICH", "OSTERREICH", "AUSTRIA", "AUT", "AT"]:
        return "AT"
    if clean in ["SCHWEIZ", "SWITZERLAND", "SUISSE", "SVIZZERA", "CH", "CHE"]:
        return "CH"
    if clean in ["FRANKREICH", "FRANCE", "FR", "FRA"]:
        return "FR"
    if clean in ["ITALIEN", "ITALY", "IT", "ITA"]:
        return "IT"
    if clean in ["SPANIEN", "SPAIN", "ES", "ESP"]:
        return "ES"
    if clean in ["UK", "GB", "GBR", "GREATBRITAIN", "UNITEDKINGDOM"]:
        return "GB"
    if clean in ["USA", "US", "UNITEDSTATES", "UNITEDSTATESOFAMERICA"]:
        return "US"
    if clean in ["NIEDERLANDE", "NETHERLANDS", "HOLLAND", "NL", "NLD"]:
        return "NL"
        
    if "DEUTSH" in clean or "DEUTSC" in clean or "GERMAN" in clean:
        return "DE"
    if "OEST" in clean or "AUSTR" in clean:
        return "AT"
    if "SCHWEIZ" in clean or "SWITZ" in clean:
        return "CH"
    if "FRANK" in clean or "FRANC" in clean:
        return "FR"
    if "ITALI" in clean or "ITALY" in clean:
        return "IT"
    if "SPAN" in clean or "SPAI" in clean:
        return "ES"

    if len(clean) == 2:
        return clean

    return "UNKNOWN"

customers["country_code"] = customers["country"].apply(map_country_code)

customers = customers.drop_duplicates(subset=["customer_id"], keep="first")

def clean_price(val):
    if pd.isna(val) or val is None:
        return None
    s = str(val).replace("EUR", "").replace("eur", "").replace("€", "").strip()
    s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None

def clean_bool(val):
    if pd.isna(val) or val is None:
        return False
    if isinstance(val, bool):
        return val
    s = str(val).strip().lower()
    return s in ["true", "1", "t", "ja", "yes", "y", "wahr"]

products["price_eur"] = products["price_eur"].apply(clean_price)
products["in_stock"] = products["in_stock"].apply(clean_bool)

merged = orders.merge(customers, on="customer_id", how="left")
merged = merged.merge(products, on="product_id", how="left")

merged["country_code"] = merged["country_code"].fillna("UNKNOWN")
merged["line_revenue"] = merged["quantity"] * merged["unit_price_eur"]

result = (
    merged.groupby(["country_code", "category"], as_index=False)
    .agg(
        total_revenue_eur=("line_revenue", "sum"),
        order_count=("order_id", "count")
    )
)

result["total_revenue_eur"] = result["total_revenue_eur"].round(2)
result = result.sort_values(by="total_revenue_eur", ascending=False)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result.to_parquet(output_path, index=False)