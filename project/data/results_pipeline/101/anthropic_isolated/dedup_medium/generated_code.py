import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/_reference/dedup_easy/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/anthropic_isolated/dedup_medium/output.parquet"

df = pd.read_parquet(input_path)

df["registered_at"] = pd.to_datetime(df["registered_at"])
df = df.sort_values("registered_at", ascending=False)
df = df.drop_duplicates(subset="email", keep="first")
df["registered_at"] = df["registered_at"].dt.strftime("%Y-%m-%d")

df.to_parquet(output_path, index=False)