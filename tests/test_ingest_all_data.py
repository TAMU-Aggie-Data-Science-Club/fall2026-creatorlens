import sys
import unittest
from unittest.mock import patch

from scripts import ingest_all_data


class IngestAllDataTest(unittest.TestCase):
    @patch("scripts.ingest_all_data.subprocess.run")
    def test_runs_trending_importer(self, run):
        ingest_all_data.main()
        run.assert_called_once_with(
            [sys.executable, str(ingest_all_data.PROJECT_ROOT / "scripts" / "ingest_trending_dataset.py")],
            cwd=ingest_all_data.PROJECT_ROOT,
            check=True,
        )


if __name__ == "__main__":
    unittest.main()
