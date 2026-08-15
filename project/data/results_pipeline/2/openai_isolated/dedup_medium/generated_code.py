import os
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/dedup_easy/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_isolated/dedup_medium/output.parquet"

df = pd.read_parquet(input_path)

df["_registered_at_sort"] = pd.to_datetime(
    df["registered_at"],
    format="%Y-%m-%d",
    errors="coerce"
)

result = (
    df.sort_values("_registered_at_sort", ascending=False, kind="stable")
      .drop_duplicates(subset=["email"], keep="first")
      .drop(columns=["_registered_at_sort"])
      .reset_index(drop=True)
)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result.to_parquet(output_path, index=False)