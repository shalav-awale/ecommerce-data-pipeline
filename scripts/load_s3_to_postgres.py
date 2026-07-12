import boto3
import pandas as pd
from sqlalchemy import create_engine
import os
import sys
from io import StringIO
from datetime import datetime


def get_db_engine():
    """
    Creates and returns a SQLAlchemy engine for PostgreSQL.
    Reads credentials from environment variables.
    Returns engine object if successful, exits if failed.
    SQLAlchemy is used instead of psycopg2 directly because:
    - Works with pandas df.to_sql() natively
    - Database-agnostic — same code works with
      PostgreSQL, Redshift, RDS by changing connection string only
    - Reads credentials from environment variables with
      local defaults for development
    """
    host     = os.environ.get("POSTGRES_HOST", "localhost")
    port     = os.environ.get("POSTGRES_PORT", "5433")
    database = os.environ.get("POSTGRES_DB", "practice_ecommerce")
    user     = os.environ.get("POSTGRES_USER", "shalavawale")
    password = os.environ.get("POSTGRES_PASSWORD", "")

    # Build connection string
    # Format: dialect://user:password@host:port/database
    connection_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"

    try:
        engine = create_engine(connection_string)

        # Test the connection immediately
        # connect() opens a real connection to verify it works
        with engine.connect() as conn:
            print("✅ PostgreSQL connection established")

        return engine

    except Exception as e:
        print(f"❌ Failed to connect to PostgreSQL: {e}")
        sys.exit(1)



def read_file_from_s3(s3_client, bucket, key):
    """
    Reads a file from S3 into a pandas DataFrame.
    Returns DataFrame if successful, exits if failed.
    """
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        df = pd.read_csv(StringIO(response["Body"].read().decode("utf-8"))) # StringIO is a memory-based file-like object that mimics a file object
        print(f"  Read {len(df):,} rows from {key}")
        return df
    except Exception as e:
        print(f"❌ Failed to read file from S3: {e}")
        sys.exit(1)



def clean_dataframe(df, filename):
    """
    Cleans a DataFrame before loading to PostgreSQL:
    - Normalizes column names to snake_case
    - Strips whitespace from string values
    - Adds metadata columns for lineage tracking
    Returns cleaned DataFrame.
    """
    try:
        # Clean column names
        # handles spaces, hyphens, dots, special characters
        df.columns = (
            df.columns
            .str.strip()
            .str.lower()
            .str.replace(r'[^a-z0-9_]', '_', regex=True)
        )

        # Strip whitespace from all string columns
        # dtype == "str" is pandas term for string columns
        for col in df.select_dtypes(include=["str"]).columns:
            df[col] = df[col].str.strip()

        # Add metadata columns for lineage tracking
        # tells you exactly when and from where data was loaded
        df["source_file"] = filename
        df["loaded_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"  Cleaned {len(df):,} rows from {filename}")
        return df

    except Exception as e:
        print(f"❌ Failed to clean {filename}: {e}")
        sys.exit(1)



def load_to_postgres(df, table_name, engine):
    """
    Loads a DataFrame into a PostgreSQL table in the ecommerce schema.
    Uses if_exists='replace' for idempotency — safe to run multiple times.
    Uses chunksize for memory-efficient loading of large files.
    Returns True if successful, exits if failed.
    """
    try:
        df.to_sql(
            table_name,
            engine,
            schema="ecommerce",
            if_exists="replace",
            index=False,
            chunksize=10000
        )
        print(f"  ✅ Loaded {len(df):,} rows into ecommerce.{table_name}")
        return True

    except Exception as e:
        print(f"  ❌ Failed to load {table_name}: {e}")
        sys.exit(1)


def get_table_name(filename):
    """
    Derives PostgreSQL table name from CSV filename.
    Examples:
    olist_orders_dataset.csv → raw_orders
    product_category_name_translation.csv → raw_product_category_name_translation
    """
    name = filename.replace(".csv", "")
    name = name.replace("olist_", "")
    name = name.replace("_dataset", "")
    return f"raw_{name}"


def process_file(filename, s3_client, bucket, s3_key, engine):
    """
    Processes a single file from S3:
    - Derives table name from filename
    - Reads file from S3
    - Cleans the dataframe
    - Loads to PostgreSQL
    - Returns True if successful, False if failed
    """
    try:
        table_name = get_table_name(filename)
        df = read_file_from_s3(s3_client, bucket, s3_key)
        df = clean_dataframe(df, filename)
        load_to_postgres(df, table_name, engine)
        return True
    except Exception as e:
        print(f"❌ Failed to process {filename}: {e}")
        return False




def main():
    """
    Orchestrates loading all Olist CSV files from S3 into PostgreSQL.
    Processes each file independently — continues on failure and
    reports all results at the end.
    """
    S3_BUCKET = "shalav-ecommerce-pipeline"
    S3_PREFIX = "raw/olist"

    print("=" * 55)
    print("S3 → PostgreSQL Loading Pipeline")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)

    # Create S3 client and database engine once
    # reuse them for all 9 files
    s3_client = boto3.client("s3", region_name="us-east-1")
    engine = get_db_engine()

    # List all CSV files in S3 under the raw/olist prefix
    # This finds files regardless of what date folder they're in
    response = s3_client.list_objects_v2(
        Bucket=S3_BUCKET,
        Prefix=S3_PREFIX
    )

    # Extract just the CSV file keys from the response
    # response["Contents"] is a list of all objects found
    # each object has a "Key" which is the full S3 path
    all_keys = [
        obj["Key"]
        for obj in response.get("Contents", [])
        if obj["Key"].endswith(".csv")
    ]

    if not all_keys:
        print("❌ No CSV files found in S3")
        sys.exit(1)

    print(f"Found {len(all_keys)} files in S3\n")

    # Process each file and track results
    results = {}

    for s3_key in all_keys:
        # Extract just the filename from the full S3 path
        # "raw/olist/2026-05-12/olist_orders_dataset.csv"
        # → "olist_orders_dataset.csv"
        filename = s3_key.split("/")[-1]
        # .split("/") splits by slash into a list
        # [-1] gets the last element = just the filename

        print(f"\nProcessing: {filename}")
        success = process_file(filename, s3_client, S3_BUCKET, s3_key, engine)
        results[filename] = success

    # Print summary report
    print(f"\n{'=' * 55}")
    print("LOADING SUMMARY")
    print(f"{'=' * 55}")

    passed = [f for f, ok in results.items() if ok]
    failed = [f for f, ok in results.items() if not ok]

    for f in passed:
        print(f"  ✅ {f}")
    for f in failed:
        print(f"  ❌ {f}")

    print(f"\nResult: {len(passed)}/{len(results)} files loaded")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()



# # scripts/load_s3_to_postgres.py
# #
# # Loads Olist CSV files from S3 into PostgreSQL raw schema.
# # Idempotent — tables are replaced on every run.
# #
# # PIPELINE FLOW:
# # main()
# #   └── process_file()         ← one file at a time
# #         ├── read_file_from_s3()   ← get data from S3
# #         ├── clean_dataframe()     ← normalize columns + metadata
# #         └── load_to_postgres()    ← write to database
# #
# # get_db_engine()    ← called once in main()
# # get_table_name()   ← called inside process_file()

# import boto3
# import pandas as pd
# from sqlalchemy import create_engine
# from io import StringIO
# import os
# import sys
# from datetime import datetime


# def get_table_name(filename):
#     """
#     Derives PostgreSQL table name from CSV filename.
#     Examples:
#     olist_orders_dataset.csv -> raw_orders
#     product_category_name_translation.csv ->
#         raw_product_category_name_translation
#     """
#     name = filename.replace(".csv", "")
#     name = name.replace("olist_", "")
#     name = name.replace("_dataset", "")
#     return f"raw_{name}"


# def get_db_engine():
#     """
#     Creates and returns a SQLAlchemy engine for PostgreSQL.
#     """
#     host     = os.environ.get("POSTGRES_HOST", "localhost")
#     port     = os.environ.get("POSTGRES_PORT", "5433")
#     database = os.environ.get("POSTGRES_DB", "practice_ecommerce")
#     user     = os.environ.get("POSTGRES_USER", "shalavawale")
#     password = os.environ.get("POSTGRES_PASSWORD", "")

#     connection_string = (
#         f"postgresql://{user}:{password}@{host}:{port}/{database}"
#     )

#     try:
#         engine = create_engine(connection_string)
#         with engine.connect() as conn:
#             print("✅ PostgreSQL connection established")
#         return engine
#     except Exception as e:
#         print(f"❌ Failed to connect to PostgreSQL: {e}")
#         sys.exit(1)


# def read_file_from_s3(s3_client, bucket, key):
#     """
#     Reads a CSV file from S3 into a pandas DataFrame.
#     """
#     try:
#         response = s3_client.get_object(Bucket=bucket, Key=key)
#         df = pd.read_csv(
#             StringIO(response["Body"].read().decode("utf-8"))
#         )
#         print(f"  Read {len(df):,} rows from s3://{bucket}/{key}")
#         return df
#     except Exception as e:
#         print(f"❌ Failed to read {key} from S3: {e}")
#         sys.exit(1)


# def clean_dataframe(df, filename):
#     """
#     Cleans a DataFrame before loading to PostgreSQL.
#     """
#     try:
#         df.columns = (
#             df.columns
#             .str.strip()
#             .str.lower()
#             .str.replace(r'[^a-z0-9_]', '_', regex=True)
#         )

#         df = df.apply(
#             lambda col: col.str.strip() if col.dtype == "object" else col
#         )

#         df["source_file"] = filename
#         df["loaded_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#         print(f"  Cleaned {len(df):,} rows from {filename}")
#         return df
#     except Exception as e:
#         print(f"❌ Failed to clean {filename}: {e}")
#         sys.exit(1)


# def load_to_postgres(df, table_name, engine):
#     """
#     Loads a DataFrame into a PostgreSQL table in the ecommerce schema.
#     """
#     try:
#         df.to_sql(
#             table_name,
#             engine,
#             schema="ecommerce",
#             if_exists="replace",
#             index=False,
#             chunksize=10000
#         )
#         print(f"  ✅ Loaded {len(df):,} rows into ecommerce.{table_name}")
#         return True
#     except Exception as e:
#         print(f"  ❌ Failed to load {table_name}: {e}")
#         sys.exit(1)


# def process_file(filename, s3_client, bucket, s3_key, engine):
#     """
#     Processes one file end to end. Returns True/False.
#     """
#     try:
#         table_name = get_table_name(filename)
#         df = read_file_from_s3(s3_client, bucket, s3_key)
#         df = clean_dataframe(df, filename)
#         load_to_postgres(df, table_name, engine)
#         return True
#     except Exception as e:
#         print(f"❌ Failed to process {filename}: {e}")
#         return False


# def main():
#     """
#     Orchestrates loading all Olist CSV files from S3 into PostgreSQL.
#     """
#     S3_BUCKET = "shalav-ecommerce-pipeline"
#     S3_PREFIX = "raw/olist"

#     print("=" * 55)
#     print("S3 -> PostgreSQL Loading Pipeline")
#     print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
#     print("=" * 55)

#     s3_client = boto3.client("s3", region_name="us-east-1")
#     engine = get_db_engine()

#     response = s3_client.list_objects_v2(
#         Bucket=S3_BUCKET,
#         Prefix=S3_PREFIX
#     )

#     all_keys = [
#         obj["Key"]
#         for obj in response.get("Contents", [])
#         if obj["Key"].endswith(".csv")
#     ]

#     if not all_keys:
#         print("❌ No CSV files found in S3")
#         sys.exit(1)

#     print(f"Found {len(all_keys)} files in S3\n")

#     results = {}

#     for s3_key in all_keys:
#         filename = s3_key.split("/")[-1]

#         print(f"\nProcessing: {filename}")
#         success = process_file(filename, s3_client, S3_BUCKET, s3_key, engine)
#         results[filename] = success

#     print(f"\n{'=' * 55}")
#     print("LOADING SUMMARY")
#     print(f"{'=' * 55}")

#     passed = [f for f, ok in results.items() if ok]
#     failed = [f for f, ok in results.items() if not ok]

#     for f in passed:
#         print(f"  ✅ {f}")
#     for f in failed:
#         print(f"  ❌ {f}")

#     print(f"\nResult: {len(passed)}/{len(results)} files loaded")
#     print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

#     if failed:
#         sys.exit(1)


# if __name__ == "__main__":
#     main()