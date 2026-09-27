"""Integration tests for PreprocessingAgent orchestrating the LangGraph workflow."""

import pytest
import pandas as pd
from pathlib import Path
from app.agent.preprocessing_agent import PreprocessingAgent


@pytest.fixture
def dummy_csv(tmp_path):
    df = pd.DataFrame({
        "AGE": [60, 55, 70, 62, 45, 58, 66, 74, 50, 63] * 3,
        "SMOKING": [2, 1, 2, 2, 1, 2, 1, 2, 1, 2] * 3,
        "COUGHING": [2, 1, 1, 2, 1, 2, 1, 2, 1, 2] * 3,
        "GENDER": ["M", "F", "M", "F", "M", "F", "M", "F", "M", "F"] * 3,
        "DIAGNOSIS": ["YES", "NO", "YES", "YES", "NO", "YES", "NO", "YES", "NO", "YES"] * 3
    })
    csv_path = tmp_path / "test_biomed.csv"
    df.to_csv(csv_path, index=False)
    return csv_path


def test_agent_auto_mode(dummy_csv, tmp_path):
    out_dir = tmp_path / "output"
    agent = PreprocessingAgent()
    result = agent.run(
        dataset_path=dummy_csv,
        target_column="DIAGNOSIS",
        feature_count=3,
        mode="auto",
        output_dir=str(out_dir)
    )

    assert result.status.lower() == "success"
    assert result.target_column == "DIAGNOSIS"
    assert result.feature_selection.selected_feature_count == 3
    assert result.validation.passed is True
    assert (out_dir / "X_train.csv").is_file()
    assert (out_dir / "fitted_pipeline.joblib").is_file()
    assert (out_dir / "preprocessing_summary.md").is_file()
