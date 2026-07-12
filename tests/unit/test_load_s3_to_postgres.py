import pytest
import pandas as pd
from scripts.load_s3_to_postgres import get_table_name, clean_dataframe

def test_get_table_name_orders():
    """Standard olist file with olist_ prefix and _dataset suffix"""
    assert get_table_name("olist_orders_dataset.csv") == "raw_orders"

def test_get_table_name_order_items():
    """Multi-word table name"""
    assert get_table_name("olist_order_items.csv") == "raw_order_items"

def test_get_table_name_translation():
    """File without olist_ prefix — only csv and _dataset stripped"""
    result = get_table_name("product_category_name_translation.csv")
    assert result == "raw_product_category_name_translation"

def test_get_table_name_removes_csv_extension():
    """Confirms .csv is always stripped"""
    result = get_table_name("olist_customers_dataset.csv")
    assert "csv" not in result

def test_clean_dataframe_convert_column_names_to_snake_case():
    # 1. Create a fake DataFrame with test data
    df = pd.DataFrame({"Order ID": [1, 2, 3], "Order Date": ["2026-01-01", "2026-01-02", "2026-01-03"]})
    
    # 2. Call the function
    result = clean_dataframe(df, "test_file.csv")
    
    # 3. Assert the expected outcome
    assert "order_id" in result.columns
    assert "order_date" in result.columns
    assert "Order ID" not in result.columns
    assert "Order Date" not in result.columns

def test_clean_dataframe_strip_whitespace_from_string_columns():
    # 1. Create a fake DataFrame with test data
    df = pd.DataFrame({"Order ID": [1,2,3], "Order Name": [" Product A ", " Product B ", " Product C "], "Order Date": ["2026-01-01", "2026-01-02", "2026-01-03"]})

    # 2. Call the function
    result = clean_dataframe(df, "test_file.csv")

    # 3. Assert the expected outcome
    assert result.order_name.tolist() == ["Product A", "Product B", "Product C" ]

#Adds source_file and loaded_at metadata columns
def test_clean_dataframe_add_metadata_columns():
    # 1. Create a fake DataFrame with test data
    df = pd.DataFrame({"Order ID": [1,2,3], "Order Date": ["2026-01-01", "2026-01-02", "2026-01-03"]})

    # 2. Call the function
    result = clean_dataframe(df, "test_file.csv")

    # 3. Assert the expected outcome
    assert "source_file" in result.columns
    assert "loaded_at" in result.columns
    assert result.source_file.iloc[0] == "test_file.csv"