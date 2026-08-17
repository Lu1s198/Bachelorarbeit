import os
import pandas as pd

input_dir = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_composite/2/codegen/openai_v2_few_shot_r2/output.parquet"

customers = pd.read_csv(os.path.join(input_dir, "customers_raw.csv"))
products = pd.read_csv(os.path.join(input_dir, "products_raw.csv"))
orders = pd.read_csv(os.path.join(input_dir, "orders_raw.csv"))

for column in customers.select_dtypes(include=["object", "string"]).columns:
    customers[column] = customers[column].astype("string").str.strip()

country_mapping = {
    "de": "DE", "deu": "DE", "ger": "DE", "germany": "DE", "deutschland": "DE",
    "deutshcland": "DE", "deutschlnd": "DE", "germania": "DE",
    "at": "AT", "aut": "AT", "austria": "AT", "oesterreich": "AT", "osterreich": "AT",
    "ch": "CH", "che": "CH", "switzerland": "CH", "schweiz": "CH", "suisse": "CH",
    "fr": "FR", "fra": "FR", "fre": "FR", "france": "FR", "frankreich": "FR",
    "es": "ES", "esp": "ES", "spain": "ES", "spanien": "ES", "espana": "ES",
    "it": "IT", "ita": "IT", "italy": "IT", "italien": "IT", "italia": "IT",
    "gb": "GB", "uk": "GB", "gbr": "GB", "unitedkingdom": "GB",
    "greatbritain": "GB", "england": "GB", "vereinigteskoenigreich": "GB",
    "us": "US", "usa": "US", "unitedstates": "US", "unitedstatesofamerica": "US",
    "america": "US", "vereinigtestaaten": "US",
    "ca": "CA", "can": "CA", "canada": "CA",
    "nl": "NL", "nld": "NL", "netherlands": "NL", "thenetherlands": "NL",
    "niederlande": "NL", "holland": "NL",
    "be": "BE", "bel": "BE", "belgium": "BE", "belgien": "BE", "belgique": "BE",
    "pl": "PL", "pol": "PL", "poland": "PL", "polen": "PL", "polska": "PL",
    "pt": "PT", "prt": "PT", "portugal": "PT",
    "se": "SE", "swe": "SE", "sweden": "SE", "schweden": "SE",
    "no": "NO", "nor": "NO", "norway": "NO", "norwegen": "NO",
    "dk": "DK", "dnk": "DK", "denmark": "DK", "daenemark": "DK", "danemark": "DK",
    "fi": "FI", "fin": "FI", "finland": "FI", "finnland": "FI",
    "ie": "IE", "irl": "IE", "ireland": "IE", "irland": "IE",
    "cz": "CZ", "cze": "CZ", "czechrepublic": "CZ", "czechia": "CZ", "tschechien": "CZ",
    "hu": "HU", "hun": "HU", "hungary": "HU", "ungarn": "HU",
    "ro": "RO", "rou": "RO", "romania": "RO", "rumaenien": "RO", "rumanien": "RO",
    "gr": "GR", "greece": "GR", "griechenland": "GR",
    "tr": "TR", "tur": "TR", "turkey": "TR", "tuerkei": "TR", "turkiye": "TR",
    "br": "BR", "bra": "BR", "brazil": "BR", "brasil": "BR", "brasilien": "BR",
    "mx": "MX", "mex": "MX", "mexico": "MX", "mexiko": "MX",
    "ar": "AR", "arg": "AR", "argentina": "AR", "argentinien": "AR",
    "au": "AU", "aus": "AU", "australia": "AU", "australien": "AU",
    "nz": "NZ", "nzl": "NZ", "newzealand": "NZ", "neuseeland": "NZ",
    "jp": "JP", "jpn": "JP", "japan": "JP",
    "cn": "CN", "chn": "CN", "china": "CN",
    "in": "IN", "ind": "IN", "india": "IN", "indien": "IN",
    "kr": "KR", "kor": "KR", "southkorea": "KR", "korea": "KR", "suedkorea": "KR",
    "za": "ZA", "zaf": "ZA", "southafrica": "ZA", "suedafrika": "ZA",
}

country_key = (
    customers["country"]
    .astype("string")
    .str.lower()
    .str.replace("ä", "ae", regex=False)
    .str.replace("ö", "oe", regex=False)
    .str.replace("ü", "ue", regex=False)
    .str.replace("ß", "ss", regex=False)
    .str.replace(r"[^a-z0-9]", "", regex=True)
)

customers["country_code"] = country_key.map(country_mapping).fillna("UNKNOWN")
customers = customers.drop_duplicates(subset=["customer_id"], keep="first")

def parse_number(value):
    if pd.isna(value):
        return float("nan")
    text = str(value).strip()
    text = "".join(char for char in text if char.isdigit() or char in ",.-")
    if not text:
        return float("nan")
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return float("nan")

products["price_eur"] = products["price_eur"].apply(parse_number)
products["in_stock"] = (
    products["in_stock"]
    .astype("string")
    .str.strip()
    .str.lower()
    .isin(["true", "1", "yes", "ja", "y", "j", "wahr"])
)

orders["quantity"] = orders["quantity"].apply(parse_number)
orders["unit_price_eur"] = orders["unit_price_eur"].apply(parse_number)

result = orders.merge(
    customers[["customer_id", "country_code"]],
    on="customer_id",
    how="left"
).merge(
    products[["product_id", "category", "price_eur", "in_stock"]],
    on="product_id",
    how="left"
)

result["country_code"] = result["country_code"].fillna("UNKNOWN")
result["category"] = result["category"].fillna("UNKNOWN")
result["revenue_eur"] = result["quantity"] * result["unit_price_eur"]

output = (
    result.groupby(["country_code", "category"], as_index=False)
    .agg(
        total_revenue_eur=("revenue_eur", "sum"),
        order_count=("revenue_eur", "size")
    )
)

output["total_revenue_eur"] = output["total_revenue_eur"].round(2)
output = output.sort_values("total_revenue_eur", ascending=False, kind="stable")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
output.to_parquet(output_path, index=False)