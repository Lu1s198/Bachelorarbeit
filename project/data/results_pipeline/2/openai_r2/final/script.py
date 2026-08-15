import os
import numpy as np
import pandas as pd

customers_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_r2/dedup_hard/output.parquet"
products_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_r2/products/output.parquet"
orders_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_r2/orders/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_r2/final/output.parquet"

iso_country_codes = set(
    """
    AD AE AF AG AI AL AM AO AQ AR AS AT AU AW AX AZ BA BB BD BE BF BG BH BI BJ BL BM BN BO BQ BR BS BT BV BW BY BZ
    CA CC CD CF CG CH CI CK CL CM CN CO CR CU CV CW CX CY CZ DE DJ DK DM DO DZ EC EE EG EH ER ES ET FI FJ FK FM FO
    FR GA GB GD GE GF GG GH GI GL GM GN GP GQ GR GS GT GU GW GY HK HM HN HR HT HU ID IE IL IM IN IO IQ IR IS IT JE
    JM JO JP KE KG KH KI KM KN KP KR KW KY KZ LA LB LC LI LK LR LS LT LU LV LY MA MC MD ME MF MG MH MK ML MM MN MO
    MP MQ MR MS MT MU MV MW MX MY MZ NA NC NE NF NG NI NL NO NP NR NU NZ OM PA PE PF PG PH PK PL PM PN PR PS PT PW
    PY QA RE RO RS RU RW SA SB SC SD SE SG SH SI SJ SK SL SM SN SO SR SS ST SV SX SY SZ TC TD TF TG TH TJ TK TL TM
    TN TO TR TT TV TW TZ UA UG UM US UY UZ VA VC VE VG VI VN VU WF WS XK YE YT ZA ZM ZW
    """.split()
)

customers = pd.read_parquet(customers_path)
products = pd.read_parquet(products_path)
orders = pd.read_parquet(orders_path)

customers["customer_id"] = pd.to_numeric(customers["customer_id"], errors="coerce").astype("Int64")
orders["customer_id"] = pd.to_numeric(orders["customer_id"], errors="coerce").astype("Int64")

products["product_id"] = pd.to_numeric(products["product_id"], errors="coerce").astype("Int64")
orders["product_id"] = pd.to_numeric(orders["product_id"], errors="coerce").astype("Int64")

customers = customers[["customer_id", "country"]].copy()
customers["country_code"] = customers["country"].astype("string").str.strip().str.upper()
customers = customers[
    customers["customer_id"].notna()
    & customers["country_code"].isin(iso_country_codes)
][["customer_id", "country_code"]]

products = products[["product_id", "category"]].copy()
products["category"] = products["category"].astype("string").str.strip()
products = products[
    products["product_id"].notna()
    & products["category"].notna()
    & products["category"].ne("")
]

orders = orders[["customer_id", "product_id", "quantity", "unit_price_eur"]].copy()
orders["quantity"] = pd.to_numeric(orders["quantity"], errors="coerce")
orders["unit_price_eur"] = pd.to_numeric(orders["unit_price_eur"], errors="coerce")

merged = orders.merge(customers, on="customer_id", how="inner")
merged = merged.merge(products, on="product_id", how="inner")

merged["revenue"] = merged["quantity"] * merged["unit_price_eur"]

result = (
    merged.groupby(["country_code", "category"], dropna=False, as_index=False)
    .agg(
        total_revenue_eur=("revenue", "sum"),
        order_count=("revenue", "size"),
    )
    .sort_values("total_revenue_eur", ascending=False, kind="stable")
    .reset_index(drop=True)
)

result["total_revenue_eur"] = result["total_revenue_eur"].astype("float64")
result["order_count"] = result["order_count"].astype("int64")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result.to_parquet(output_path, index=False)