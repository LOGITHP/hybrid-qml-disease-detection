"""Unit tests for dataset loading and deterministic profiling analysis."""

import pytest
import pandas as pd
from app.tools.dataset_loader import DatasetLoader
from app.tools.dataset_analysis import analyze_dataset, rank_target_candidates


@pytest.fixture
def sample_biomedical_df():
    return pd.DataFrame({
        "PATIENT_ID": [f"P_{i:03d}" for i in range(20)],
        "AGE": [45, 52, 63, 71, 39, 48, 55, 62, 67, 50, 43, 59, 61, 70, 38, 49, 56, 64, 68, 51],
        "SMOKING": [1, 2, 2, 1, 1, 2, 1, 2, 2, 1, 1, 2, 1, 2, 1, 2, 2, 1, 2, 1],
        "GENDER": ["M", "F", "F", "M", "M", "F", "M", "F", "M", "F", "M", "F", "M", "F", "M", "F", "M", "F", "M", "F"],
        "LUNG_CANCER": ["NO", "YES", "YES", "NO", "NO", "YES", "NO", "YES", "YES", "NO", "NO", "YES", "NO", "YES", "NO", "YES", "YES", "NO", "YES", "NO"]
    })


def test_analyze_dataset_schema(sample_biomedical_df):
    analysis = analyze_dataset(sample_biomedical_df, target_hint="LUNG_CANCER")
    assert analysis.row_count == 20
    assert analysis.column_count == 5
    assert "AGE" in analysis.numerical_features
    assert "GENDER" in analysis.categorical_features
    assert "PATIENT_ID" in analysis.identifier_columns
    assert analysis.detected_target == "LUNG_CANCER"
    assert analysis.detected_task == "binary_classification"


def test_target_candidate_ranking(sample_biomedical_df):
    candidates = rank_target_candidates(sample_biomedical_df)
    assert len(candidates) > 0
    top_candidate = candidates[0]
    assert top_candidate.column_name == "LUNG_CANCER"
    assert top_candidate.confidence >= 0.80
    assert top_candidate.task_type == "binary_classification"
