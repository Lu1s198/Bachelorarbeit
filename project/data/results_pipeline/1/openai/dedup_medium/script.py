import os
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai/dedup_easy/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai/dedup_medium/output.parquet"

df = pd.read_parquet(input_path)

required_columns = ["customer_id", "full_name", "email", "country", "registered_at"]
missing_columns = [column for column in required_columns if column not in df.columns]
if missing_columns:
    raise ValueError(f"Missing required columns: {missing_columns}")

df["_registered_at_sort"] = pd.to_datetime(df["registered_at"], format="%Y-%m-%d", errors="coerce")
df["_original_order"] = range(len(df))

df = df.sort_values(
    by=["email", "_registered_at_sort", "_original_order"],
    ascending=[True, False, True],
    na_position="last",
    kind="stable",
)

df = df.drop_duplicates(subset=["email"], keep="first")
df = df.drop(columns=["_registered_at_sort", "_original_order"])

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)