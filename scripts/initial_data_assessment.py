import os
import json
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd
from dotenv import load_dotenv
from googleapiclient.discovery import build
import numpy as np
import re

from load_data import *

def summarize_data(df: pd.DataFrame):
    # Summarize dataset dimensions, columns, and data types.
    print("\n ======== SUMMARY STATISTICS ========")
    print("\nDimensions: ")
    print(f"{df.shape[0]} Rows, {df.shape[1]} Columns")

    print("\nColumns: ")
    columns_list = df.columns.tolist()
    for col in columns_list:
        print(f"{col}")
    
    print("\nData types: ")
    print(df.dtypes)

    print("\nInfo: ")
    print(df.info())

    # Identify missing values and duplicate records
    print("\nMissing Values By Column: ")
    print(f"{df.isna().sum()}")
    
    print(f"\nDuplicate Records: {df.duplicated().sum()}")

    # Capture core YouTube metrics if present (views, likes, comments)
    print("\n======== CORE YOUTUBE METRICS ========")

    metrics_col = df.select_dtypes(include=[np.number]).columns.tolist()
    if metrics_col:
        print(df[metrics_col].describe().T)
    else:
        print("No Core YouTube Metrics Present")

def clean_dataset(df: pd.DataFrame):
    clean_df = df.copy(deep = True)

    # Handling Duplications
    # Justification: Repeated observations violates the independent assumption
    clean_df.drop_duplicates(subset='video_id', keep="first")

    # Standardize Missing Data Labels
    # Justification: If ignored, missing values can provide training difficulty, increased preprocessing, loss of information
    clean_df.replace(['NO DATA','N/A', 0, ''],np.nan)

    # Converting Duration Format
    # Numeric values of duration (converted from H:M:S format) are more appropiate for analysis and interpretation
    clean_df['duration'] = pd.to_timedelta(df['duration']).dt.total_seconds()

    return clean_df

def main():
    # Define file paths to separate raw and cleaned data
    INTERIM_DATA_PATH = "data/interim/videos_2026-10-23.csv" # Update file path to appropiate location/collection date
    PROCESSED_DATA_PATH = "/data/processed/videos_2026-10-23_cleaned.csv"
    
    raw_df = load_data(INTERIM_DATA_PATH, dataset_type='videos')

    print("INTERIM DATASET: ")
    summarize_data(raw_df)
    
    clean_data = clean_dataset(raw_df)

    print(f"{'-'*80}")
    print("PROCESSED DATASET: ")
    summarize_data(clean_data)
    
    os.makedirs(os.path.dirname(PROCESSED_DATA_PATH), exist_ok = True)
    clean_data.to_csv(PROCESSED_DATA_PATH, index = False)
    print(f"Verification: Cleaned dataset saved to {PROCESSED_DATA_PATH}")

if __name__ == "__main__":
    main()