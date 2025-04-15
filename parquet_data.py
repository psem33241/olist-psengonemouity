import pandas as pd  
import zipfile  
import io  
import requests  
import os

def download_and_save_csv(url, parquet_file):
    try:
        df = pd.read_csv(url).drop(columns="Unnamed: 0")
        df.to_parquet(parquet_file)
        print(f"Successfully saved {parquet_file}")
    except Exception as e:
        print(f"Error processing {url}: {e}")

def download_and_extract_zip(url, csv_filename):
    try:
        response = requests.get(url)
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            z.extractall()
        download_and_save_csv(csv_filename, csv_filename.replace('.csv', '.parquet'))
    except Exception as e:
        print(f"Error processing {url}: {e}")

# URLs and corresponding filenames  
datasets = {
    "orders_customers": "https://raw.githubusercontent.com/WildCodeSchool/wilddata/main/orders_customers_dataset.csv",
    "geolocation": "https://github.com/WildCodeSchool/wilddata/raw/main/geolocation_dataset.zip",
    "geolocation_csv": "geolocation_dataset.csv",
    "order_items": "https://raw.githubusercontent.com/WildCodeSchool/wilddata/main/order_items_dataset.csv",
    "order_payments": "https://raw.githubusercontent.com/WildCodeSchool/wilddata/main/order_payments_dataset.csv",
    "order_reviews": "https://raw.githubusercontent.com/WildCodeSchool/wilddata/main/order_reviews_dataset.csv",
    "orders": "https://raw.githubusercontent.com/WildCodeSchool/wilddata/main/orders_dataset.csv",
    "products": "https://raw.githubusercontent.com/WildCodeSchool/wilddata/main/products_dataset.csv",
    "sellers": "https://raw.githubusercontent.com/WildCodeSchool/wilddata/main/sellers_dataset.csv",
}

# Download and save datasets  
for name, url in datasets.items():
    if "zip" in url:
        download_and_extract_zip(url, datasets["geolocation_csv"])
    else:
        download_and_save_csv(url, f"{name}_df.parquet")