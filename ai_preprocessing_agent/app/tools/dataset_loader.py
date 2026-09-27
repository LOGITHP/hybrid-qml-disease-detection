"""Dataset loader with support for CSV and extensible formats."""

from pathlib import Path
from typing import Tuple, Dict, Any, Union
import pandas as pd


class DatasetLoader:
    """Deterministic biomedical dataset loading utility."""

    @staticmethod
    def load_dataset(file_path: Union[str, Path]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Loads a dataset from disk and computes raw ingestion metadata.

        Args:
            file_path: Absolute or relative path to the dataset file.

        Returns:
            Tuple of (DataFrame, metadata_dict)

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If file format is unsupported or file is empty.
        """
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Dataset file not found at: {path}")

        suffix = path.suffix.lower()
        if suffix == ".csv":
            df = pd.read_csv(path)
        elif suffix in [".xlsx", ".xls"]:
            df = pd.read_excel(path)
        elif suffix == ".parquet":
            df = pd.read_parquet(path)
        elif suffix == ".json":
            df = pd.read_json(path)
        else:
            raise ValueError(f"Unsupported dataset format '{suffix}'. Supported: .csv, .xlsx, .parquet, .json")

        if df.empty:
            raise ValueError(f"Loaded dataset from {path} is empty (0 rows).")

        try:
            rel_source = path.relative_to(Path.cwd()).as_posix()
        except ValueError:
            rel_source = path.as_posix()

        metadata = {
            "source_path": rel_source,
            "file_name": path.name,
            "format": suffix.lstrip("."),
            "file_size_bytes": path.stat().st_size,
            "initial_rows": int(len(df)),
            "initial_columns": int(len(df.columns)),
            "columns": list(df.columns),
        }
        return df, metadata


def load_dataset(file_path: Union[str, Path]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Helper function to load dataset via DatasetLoader."""
    return DatasetLoader.load_dataset(file_path)
