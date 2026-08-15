import os
import numpy as np
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_r2/dedup_easy/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_r2/dedup_medium/output.parquet"

df = pd.read_parquet(input_path)

required_columns = ["customer_id", "full_name", "email", "country", "registered_at"]
df = df.loc[:, required_columns].copy()

df["_original_order"] = np.arange(len(df))
df["_registered_at_sort"] = pd.to_datetime(df["registered_at"], format="%Y-%m-%d", errors="coerce")

result = (
    df.sort_values(
        by=["email", "_registered_at_sort", "_original_order"],
        ascending=[True, False, True],
        na_position="last",
        kind="stable",
    )
    .drop_duplicates(subset=["email"], keep="first")
    .sort_values("_original_order", kind="stable")
    .loc[:, required_columns]
    .reset_index(drop=True)
)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result.to_parquet(output_path, index=False)