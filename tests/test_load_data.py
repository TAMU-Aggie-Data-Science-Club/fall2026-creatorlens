
import pandas as pd
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.load_data import load_data


def main():
    with TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "channels.csv"

        data = {
            "channel_id": ["UC123"],
            "channel_name": ["Test Channel"],
            "description": ["Test description"],
            "published_at": ["2020-01-01T12:00:00Z"],
            "subscriber_count": [1000],
            "view_count": [50000],
            "video_count": [100],
            "collection_date": ["2026-10-22"]
        }

        # TEST 1: Valid data
        pd.DataFrame(data).to_csv(path, index=False)

        channels = load_data(path, "channels")

        assert len(channels) == 1
        assert channels["channel_name"].iloc[0] == "Test Channel"

        print("PASS: Valid channel CSV loaded successfully!")
        print(channels.to_string())

        # TEST 2: Invalid numeric data
        invalid_data = data.copy()
        # Replace a numeric column with invalid data
        invalid_data["view_count"] = ["hello"]

        pd.DataFrame(invalid_data).to_csv(path, index=False)

        try:
            load_data(path, "channels")
            raise AssertionError(
                "FAIL: Loader accepted invalid numeric data"
            )
        except ValueError as e:
            print("\nPASS: Invalid numeric data rejected!")
            print(f"Error: {e}")

        # TEST 3: Missing required column
        invalid_data = data.copy()
        # Remove a required column from the data
        del invalid_data["channel_id"]

        pd.DataFrame(invalid_data).to_csv(path, index=False)

        try:
            load_data(path, "channels")
            raise AssertionError(
                "FAIL: Loader accepted missing column"
            )
        except ValueError as e:
            print("\nPASS: Missing required column rejected!")
            print(f"Error: {e}")

        # TEST 4: Invalid collection date
        invalid_data = data.copy()
        # Replace the collection date with an invalid date
        invalid_data["collection_date"] = ["not-a-date"]

        pd.DataFrame(invalid_data).to_csv(path, index=False)

        try:
            load_data(path, "channels")
            raise AssertionError(
                "FAIL: Loader accepted invalid date"
            )
        except ValueError as e:
            print("\nPASS: Invalid date rejected!")
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
