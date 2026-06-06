# scripts/ingest_olist_to_s3.py
#
# Reads Olist CSV files from local data/raw/olist/
# validates basic quality checks, and uploads to S3.

import boto3
import pandas as pd
import os
import sys
from datetime import datetime

S3_BUCKET = os.environ.get("S3_BUCKET_NAME", "shalav-ecommerce-pipeline")
S3_PREFIX = "raw/olist"
LOCAL_DATA_PATH = "data/raw/olist"

SOURCE_FILES = {
    "olist_orders_dataset.csv": {
        "key_columns": ["order_id", "customer_id", "order_status"],
        "description": "Orders - core transaction table"
    },
    "olist_order_items_dataset.csv": {
        "key_columns": ["order_id", "product_id", "seller_id", "price"],
        "description": "Order items - line item detail"
    },
    "olist_customers_dataset.csv": {
        "key_columns": ["customer_id", "customer_state"],
        "description": "Customers - dimension table"
    },
    "olist_products_dataset.csv": {
        "key_columns": ["product_id", "product_category_name"],
        "description": "Products - dimension table"
    },
    "olist_sellers_dataset.csv": {
        "key_columns": ["seller_id", "seller_state"],
        "description": "Sellers - dimension table"
    },
    "olist_order_payments_dataset.csv": {
        "key_columns": ["order_id", "payment_value"],
        "description": "Payments - payment transactions"
    },
    "olist_order_reviews_dataset.csv": {
        "key_columns": ["review_id", "order_id", "review_score"],
        "description": "Reviews - customer reviews"
    },
    "olist_geolocation_dataset.csv": {
        "key_columns": ["geolocation_zip_code_prefix", "geolocation_state"],
        "description": "Geolocation - location reference"
    },
    "product_category_name_translation.csv": {
        "key_columns": ["product_category_name",
                        "product_category_name_english"],
        "description": "Category translation - lookup table"
    }
}


def validate_dataframe(df, filename, key_columns):
    """
    Validates a DataFrame by checking:
    - Number of rows
    - Missing columns
    - Null rate for each column
    Returns True if all checks pass, False otherwise
    """
    passed = True

    if len(df) == 0:
        print(f"  ERROR: {filename} has zero rows")
        return False

    print(f"  Row count:    {len(df):,}")
    print(f"  Column count: {len(df.columns)}")

    missing_columns = [c for c in key_columns if c not in df.columns]
    if missing_columns:
        print(f"  ERROR: Missing expected columns: {missing_columns}")
        passed = False

    for col in key_columns:
        if col in df.columns:
            null_count = df[col].isna().sum()
            null_rate = null_count / len(df)
            if null_rate > 0.5:
                print(f"  WARNING: {col} is {null_rate:.1%} null")
                passed = False
            else:
                print(f"  {col}: {null_rate:.1%} null rate ✓")

    return passed


def upload_to_s3(local_path, filename, s3_client):
    date_prefix = datetime.now().strftime("%Y-%m-%d")
    s3_key = f"{S3_PREFIX}/{date_prefix}/{filename}"

    s3_client.upload_file(
        Filename=local_path,
        Bucket=S3_BUCKET,
        Key=s3_key
    )

    return s3_key


def process_file(filename, config, s3_client):
    local_path = os.path.join(LOCAL_DATA_PATH, filename)

    print(f"\n{'='*55}")
    print(f"Processing: {filename}")
    print(f"Purpose:    {config['description']}")
    print(f"{'='*55}")

    if not os.path.exists(local_path):
        print(f"  ERROR: File not found at {local_path}")
        return False

    df = pd.read_csv(local_path, low_memory=False)

    print("\nValidation:")
    validation_passed = validate_dataframe(
        df, filename, config["key_columns"]
    )

    if not validation_passed:
        print(f"  SKIPPING upload — validation failed")
        return False

    print("\nUploading to S3...")
    s3_key = upload_to_s3(local_path, filename, s3_client)
    print(f"  Uploaded: s3://{S3_BUCKET}/{s3_key}")

    return True


def main():
    print("=" * 55)
    print("Olist → S3 Ingestion Pipeline")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target:  s3://{S3_BUCKET}/{S3_PREFIX}/")
    print("=" * 55)

    s3_client = boto3.client("s3", region_name="us-east-1")

    results = {}

    for filename, config in SOURCE_FILES.items():
        success = process_file(filename, config, s3_client)
        results[filename] = success

    print(f"\n{'='*55}")
    print("INGESTION SUMMARY")
    print(f"{'='*55}")

    passed = [f for f, ok in results.items() if ok]
    failed = [f for f, ok in results.items() if not ok]

    for filename in passed:
        print(f"  ✅ {filename}")
    for filename in failed:
        print(f"  ❌ {filename}")

    print(f"\nResult: {len(passed)}/9 files uploaded")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
    