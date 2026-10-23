from pathlib import Path
import pandas as pd
import re

# Define the required columns for each dataset type
REQUIRED_COLUMNS = {
    "channels": [
        "channel_id",
        "channel_name",
        "description",
        "published_at",
        "subscriber_count",
        "view_count",
        "video_count",
        "collection_date"
    ],
    "videos": [
        "video_id",
        "channel_id",
        "title",
        "published_at",
        "duration",
        "category_id",
        "view_count",
        "like_count",
        "comment_count",
        "collection_date"
    ]
}

#Define the Required Numeric Columns for each dataset type
REQUIRED_NUMERIC_COLUMNS = {
    "channels": ["view_count", "video_count"],
    "videos": []
}

#Define the Numeric Columns for each dataset type
NUMERIC_COLUMNS = {
    "channels": [
        "subscriber_count",
        "view_count",
        "video_count"
    ],
    "videos": [
        "view_count",
        "like_count",
        "comment_count"
    ]
}

#Define the String Columns for each dataset type

STRING_COLUMNS = {
    "channels": [
        "channel_id",
        "channel_name"
    ],
    "videos": [
        "video_id",
        "channel_id",
        "title",
        "duration"
    ]
}

#Function to load data from a CSV file and validate required columns

def load_data(file_path, dataset_type):

    path = Path(file_path)

    # Validate dataset type
    if dataset_type not in REQUIRED_COLUMNS:
        raise ValueError(
            f"Invalid dataset type: {dataset_type}"
        )

    # Check file existence
    if not path.is_file():
        raise FileNotFoundError(
            f"Dataset not found: {path}"
        )

    # Load CSV
    df = pd.read_csv(path)

    # Check for missing columns
    required = REQUIRED_COLUMNS[dataset_type]

    missing = [
        col for col in required
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    #Validate the Numeric Columns and Convert to Int64
    for col in NUMERIC_COLUMNS[dataset_type]:
        # Convert values to numeric types
        numeric_values = pd.to_numeric(
            df[col],
            errors="raise"
        )

        # Check for required numeric columns
        if col in REQUIRED_NUMERIC_COLUMNS[dataset_type]:
            if numeric_values.isna().any():
                raise ValueError(
                    f"Column '{col}' contains missing values"
                )

        # Check for negative numbers
        if (numeric_values.dropna() < 0).any():
            raise ValueError(
                f"Column '{col}' contains negative values"
            )
        
        # Check for decimal values
        if (numeric_values.dropna() % 1 != 0).any():
            raise ValueError(
                f"Column '{col}' must contain whole numbers"
            )

        # Store as nullable integers
        df[col] = numeric_values.astype("Int64")

    #Validate the String Columns
        
    for col in STRING_COLUMNS[dataset_type]:
        # Check for missing values
        if df[col].isna().any():
            raise ValueError(
                f"Column '{col}' contains missing values"
            )
        
        # Check for empty strings or whitespace
        if df[col].astype(str).str.strip().eq("").any():
            raise ValueError(
                f"Column '{col}' contains empty strings"
            )

    # Validate publication timestamps
    if df["published_at"].isna().any():
        raise ValueError(
            "Column 'published_at' contains missing values"
        )
    #Validate Format of publication timestamps
    try:
        df["published_at"] = pd.to_datetime(
            df["published_at"],
            errors="raise",
            utc=True,
            format="ISO8601"
        )
    except (ValueError, TypeError):
        raise ValueError(
            "Column 'published_at' contains invalid timestamps"
        ) from None

    # Validate collection dates
    try:
        #Validate Format
        df["collection_date"] = pd.to_datetime(
            df["collection_date"],
            format="%Y-%m-%d",
           errors="raise"
       )
        
    except (ValueError, TypeError):
      raise ValueError(
          "Column 'collection_date' contains invalid dates"
       ) from None

    if df["collection_date"].isna().any():
       raise ValueError(
           "Column 'collection_date' contains missing values"
       )
    # Validate YouTube video durations
    if dataset_type == "videos":
        duration_pattern = r"^P(?:(?:\d+W)|(?:\d+D)?(?:T(?=\d)(?:\d+H)?(?:\d+M)?(?:\d+S)?))$"
        # Validate each video duration against Youtube ISO 8601 format
        for duration in df["duration"]:
            if not re.fullmatch(duration_pattern, duration):
                raise ValueError(
                    f"Invalid video duration: {duration}"
                )
    #Return Data
    return df