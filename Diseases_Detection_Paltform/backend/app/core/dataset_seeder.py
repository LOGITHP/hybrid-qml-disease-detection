"""Default dataset seeder.

Runs at application startup to ensure the bundled Lung Cancer dataset is
available in every fresh deployment. Safe to call on every start — it
checks for existence before inserting.
"""
from __future__ import annotations

import io
import pathlib
import uuid
from datetime import datetime, timezone

import pandas as pd

from app.database.models.dataset import Dataset, DatasetVersion
from app.core.logging import logger
from app.services.artifact_service import artifact_storage

# Path to the dataset bundled inside the project
_DATA_DIR = pathlib.Path(__file__).parent.parent / "data" / "default_datasets"

# Sentinel user_id that marks system-owned (shared) datasets
SYSTEM_USER_ID = "system"


_DEFAULTS = [
    {
        "name": "Lung Cancer Survey (V1)",
        "description": (
            "Benchmark lung cancer classification dataset (3000 rows, 16 columns). "
            "Bundled with the platform. Source: Experimental_ML/Lung_Cancer/data/raw/V1_dataset.csv."
        ),
        "filename": "lung_cancer_v1.csv",
        "version_tag": "v1.0",
    },
]


async def seed_default_datasets() -> None:
    """Idempotently seed all bundled default datasets into MongoDB."""

    for spec in _DEFAULTS:
        csv_path = _DATA_DIR / spec["filename"]
        if not csv_path.exists():
            logger.warning(f"[Seeder] Default dataset file not found: {csv_path}")
            continue

        # Check if already seeded (match by name + system ownership)
        existing = await Dataset.find_one(
            {"name": spec["name"], "user_id": SYSTEM_USER_ID}
        )
        if existing:
            logger.info(f"[Seeder] Default dataset already seeded: '{spec['name']}' — skipping.")
            continue

        logger.info(f"[Seeder] Seeding default dataset: '{spec['name']}'")

        # Read and parse CSV
        file_bytes = csv_path.read_bytes()
        df = pd.read_csv(io.BytesIO(file_bytes))

        # Create Dataset document
        dataset = Dataset(
            user_id=SYSTEM_USER_ID,
            name=spec["name"],
            description=spec["description"],
        )
        await dataset.insert()

        # Create DatasetVersion document
        version = DatasetVersion(
            dataset_id=str(dataset.id),
            user_id=SYSTEM_USER_ID,
            version_tag=spec["version_tag"],
            row_count=len(df),
            column_count=len(df.columns),
            status="uploaded",
            dataset_metadata={
                "filename": spec["filename"],
                "format": "csv",
                "file_size_bytes": len(file_bytes),
                "columns": [str(c) for c in df.columns],
                "dtypes": {str(c): str(t) for c, t in df.dtypes.items()},
                "is_default": True,
                "processing_status": {
                    "uploaded": True,
                    "preprocessed": False,
                    "feature_selection": False,
                },
            },
        )
        await version.insert()

        # Save the CSV bytes into artifact storage so analysis/load works
        rel_path = f"datasets/{dataset.id}/versions/{version.id}/original.csv"
        artifact_storage.save(rel_path, file_bytes)

        logger.info(
            f"[Seeder] Seeded '{spec['name']}' → dataset_id={dataset.id}, version_id={version.id}"
        )
