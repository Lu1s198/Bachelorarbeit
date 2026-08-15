import os
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai/dedup_easy/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai/dedup_medium/output.parquet"

df = pd.read_parquet(input_path)

df["email"] = df["email"].astype("string")
df["registered_at"] = df["registered_at"].astype("string")

df = df.sort_values(
    by=["email", "registered_at"],
    ascending=[True, False],
    na_position="last",
    kind="stable",
)

result = df.drop_duplicates(subset=["email"], keep="first")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result.to_parquet(output_path, index=False)