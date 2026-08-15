import os
import numpy as np
import pandas as pd

customers_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_r3/dedup_hard/output.parquet"
products_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_r3/products/output.parquet"
orders_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_r3/orders/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_r3/final/output.parquet"

customers = pd.read_parquet(customers_path)
products = pd.read_parquet(products_path)
orders = pd.read_parquet(orders_path)

customers["customer_id"] = customers["customer_id"].astype("string")
orders["customer_id"] = orders["customer_id"].astype("string")
products["product_id"] = products["product_id"].astype("string")
orders["product_id"] = orders["product_id"].astype("string")

iso_country_codes = set("""
AD AE AF AG AI AL AM AO AQ AR AS AT AU AW AX AZ BA BB BD BE BF BG BH BI BJ BL BM BN BO
BQ BR BS BT BV BW BY BZ CA CC CD CF CG CH CI CK CL CM CN CO CR CU CV CW CX CY CZ DE DJ
DK DM DO DZ EC EE EG EH ER ES ET FI FJ FK FM FO FR GA GB GD GE GF GG GH GI GL GM GN GP
GQ GR GS GT GU GW GY HK HM HN HR HT HU ID IE IL IM IN IO IQ IR IS IT JE JM JO JP KE KG
KH KI KM KN KP KR KW KY KZ LA LB LC LI LK LR LS LT LU LV LY MA MC MD ME MF MG MH MK ML
MM MN MO MP MQ MR MS MT MU MV MW MX MY MZ NA NC NE NF NG NI NL NO NP NR NU NZ OM PA PE
PF PG PH PK PL PM PN PR PS PT PW PY QA RE RO RS RU RW SA SB SC SD SE SG SH SI SJ SK SL
SM SN SO SR SS ST SV SX SY SZ TC TD TF TG TH TJ TK TL TM TN TO TR TT TV TW TZ UA UG UM
US UY UZ VA VC VE VG VI VN VU WF WS YE YT ZA ZM ZW
""".split())

customers["country_code"] = customers["country"].astype("string").str.strip().str.upper()
products["category"] = products["category"].astype("string").str.strip()

customers = customers.loc[customers["country_code"].isin(iso_country_codes), ["customer_id", "country_code"]]
products = products.loc[
    products["category"].notna() & products["category"].ne(""),
    ["product_id", "category"],
]

merged = orders.merge(customers, on="customer_id", how="inner")
merged = merged.merge(products, on="product_id", how="inner")

merged["total_revenue_eur"] = (
    pd.to_numeric(merged["quantity"], errors="coerce")
    * pd.to_numeric(merged["unit_price_eur"], errors="coerce")
)

result = (
    merged.groupby(["country_code", "category"], dropna=True, as_index=False)
    .agg(
        total_revenue_eur=("total_revenue_eur", "sum"),
        order_count=("order_id", "size"),
    )
    .sort_values("total_revenue_eur", ascending=False, kind="stable")
    .reset_index(drop=True)
)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result.to_parquet(output_path, index=False)