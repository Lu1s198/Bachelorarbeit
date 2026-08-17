import os
import pandas as pd

base_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_composite/2/codegen/openai_v2_few_shot/output.parquet"

customers = pd.read_csv(f"{base_path}/customers_raw.csv")
products = pd.read_csv(f"{base_path}/products_raw.csv")
orders = pd.read_csv(f"{base_path}/orders_raw.csv")

text_columns = customers.select_dtypes(include=["object", "string"]).columns
for column in text_columns:
    customers[column] = customers[column].astype("string").str.strip()

country_aliases = {
    "de": "DE", "ger": "DE", "deu": "DE", "germany": "DE", "deutschland": "DE",
    "deutshcland": "DE", "allemagne": "DE", "alemania": "DE",
    "at": "AT", "aut": "AT", "austria": "AT", "osterreich": "AT", "österreich": "AT",
    "ch": "CH", "che": "CH", "switzerland": "CH", "schweiz": "CH", "suisse": "CH",
    "fr": "FR", "fra": "FR", "fre": "FR", "france": "FR", "frankreich": "FR",
    "es": "ES", "esp": "ES", "spain": "ES", "spanien": "ES", "espana": "ES", "españa": "ES",
    "it": "IT", "ita": "IT", "italy": "IT", "italien": "IT", "italia": "IT",
    "nl": "NL", "nld": "NL", "netherlands": "NL", "holland": "NL", "niederlande": "NL",
    "be": "BE", "bel": "BE", "belgium": "BE", "belgien": "BE", "belgique": "BE",
    "lu": "LU", "lux": "LU", "luxembourg": "LU", "luxemburg": "LU",
    "gb": "GB", "uk": "GB", "gbr": "GB", "united kingdom": "GB", "great britain": "GB",
    "england": "GB", "vereinigtes konigreich": "GB", "vereinigtes königreich": "GB",
    "ie": "IE", "irl": "IE", "ireland": "IE", "irland": "IE",
    "pt": "PT", "prt": "PT", "portugal": "PT",
    "pl": "PL", "pol": "PL", "poland": "PL", "polen": "PL",
    "se": "SE", "swe": "SE", "sweden": "SE", "schweden": "SE",
    "no": "NO", "nor": "NO", "norway": "NO", "norwegen": "NO",
    "dk": "DK", "dnk": "DK", "denmark": "DK", "dänemark": "DK", "daenemark": "DK",
    "fi": "FI", "fin": "FI", "finland": "FI", "finnland": "FI",
    "cz": "CZ", "cze": "CZ", "czech republic": "CZ", "tschechien": "CZ",
    "sk": "SK", "svk": "SK", "slovakia": "SK", "slowakei": "SK",
    "hu": "HU", "hun": "HU", "hungary": "HU", "ungarn": "HU",
    "ro": "RO", "rou": "RO", "romania": "RO", "rumanien": "RO",
    "bg": "BG", "bgr": "BG", "bulgaria": "BG", "bulgarien": "BG",
    "gr": "GR", "greece": "GR", "greece": "GR", "griechenland": "GR",
    "hr": "HR", "hrv": "HR", "croatia": "HR", "kroatien": "HR",
    "si": "SI", "svn": "SI", "slovenia": "SI", "slowenien": "SI",
    "us": "US", "usa": "US", "united states": "US", "united states of america": "US",
    "amerika": "US", "vereinigte staaten": "US",
    "ca": "CA", "can": "CA", "canada": "CA", "kanada": "CA",
    "mx": "MX", "mex": "MX", "mexico": "MX", "mexiko": "MX",
    "br": "BR", "bra": "BR", "brazil": "BR", "brasil": "BR", "brasilien": "BR",
    "ar": "AR", "arg": "AR", "argentina": "AR", "argentinien": "AR",
    "cn": "CN", "chn": "CN", "china": "CN", "chinese": "CN",
    "jp": "JP", "jpn": "JP", "japan": "JP",
    "kr": "KR", "kor": "KR", "south korea": "KR", "südkorea": "KR", "sudkorea": "KR",
    "in": "IN", "ind": "IN", "india": "IN", "indien": "IN",
    "au": "AU", "aus": "AU", "australia": "AU", "australien": "AU",
    "nz": "NZ", "nzl": "NZ", "new zealand": "NZ", "neuseeland": "NZ",
}

country_key = (
    customers["country"]
    .astype("string")
    .str.strip()
    .str.lower()
    .str.replace(r"\.", "", regex=True)
    .str.replace(r"\s+", " ", regex=True)
)
customers["country_code"] = country_key.map(country_aliases).fillna("UNKNOWN")
customers = customers.drop_duplicates(subset="customer_id", keep="first")

def parse_number(series):
    values = series.astype("string").str.strip()
    values = values.str.replace(r"[^\d,.\-]", "", regex=True)
    comma_decimal = values.str.contains(",", na=False)
    values = values.where(~comma_decimal, values.str.replace(".", "", regex=False).str.replace(",", ".", regex=False))
    return pd.to_numeric(values, errors="coerce")

products["price_eur"] = parse_number(products["price_eur"])
products["in_stock"] = (
    products["in_stock"]
    .astype("string")
    .str.strip()
    .str.lower()
    .isin(["true", "1", "yes", "ja", "y", "j"])
)

orders["quantity"] = parse_number(orders["quantity"])
orders["unit_price_eur"] = parse_number(orders["unit_price_eur"])

merged = (
    orders
    .merge(customers[["customer_id", "country_code"]], on="customer_id", how="left")
    .merge(products[["product_id", "category"]], on="product_id", how="left")
)

merged["country_code"] = merged["country_code"].fillna("UNKNOWN")
merged["total_revenue_eur"] = merged["quantity"] * merged["unit_price_eur"]

result = (
    merged.groupby(["country_code", "category"], dropna=False, as_index=False)
    .agg(
        total_revenue_eur=("total_revenue_eur", "sum"),
        order_count=("order_id", "nunique"),
    )
)

result["total_revenue_eur"] = result["total_revenue_eur"].round(2)
result = result.sort_values("total_revenue_eur", ascending=False, kind="stable")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result.to_parquet(output_path, index=False)