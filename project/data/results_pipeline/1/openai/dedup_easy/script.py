import os
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai/cleaning_hard/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai/dedup_easy/output.parquet"

df = pd.read_parquet(input_path)
result = df.drop_duplicates(keep="first")

required_columns = ["customer_id", "full_name", "email", "country", "registered_at"]
missing_columns = [column for column in required_columns if column not in result.columns]
if missing_columns:
    raise ValueError(f"Missing required columns: {missing_columns}")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result.to_parquet(output_path, index=False)