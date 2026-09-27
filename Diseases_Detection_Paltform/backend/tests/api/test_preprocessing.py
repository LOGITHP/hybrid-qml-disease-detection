"""Tests for AI Preprocessing Agent API endpoints."""

import io
import pytest
from httpx import AsyncClient
import pandas as pd


@pytest.mark.asyncio
async def test_preprocessing_plan_and_execution(client: AsyncClient, test_user_token: str):
    """Test AI plan generation and leak-free execution on uploaded dataset."""
    headers = {"Authorization": f"Bearer {test_user_token}"}

    # 1. Create a dataset container
    ds_res = await client.post(
        "/api/v1/datasets",
        json={"name": "Screening Cohort", "description": "Biomarker clinical trial"},
        headers=headers,
    )
    assert ds_res.status_code == 201
    dataset_id = ds_res.json()["data"]["id"]

    # 2. Upload a dataset version
    df_data = pd.DataFrame({
        "AGE": [65, 54, 71, 62, 45, 59, 67, 52, 60, 48, 70, 56],
        "SMOKING": [2, 1, 2, 2, 1, 1, 2, 1, 2, 1, 2, 1],
        "YELLOW_FINGERS": [2, 1, 2, 2, 1, 1, 2, 1, 2, 1, 2, 1],
        "WHEEZING": [2, 1, 2, 2, 1, 1, 2, 1, 2, 1, 2, 1],
        "LUNG_CANCER": [1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 0],
    })
    csv_bytes = df_data.to_csv(index=False).encode("utf-8")

    files = {"file": ("cohort.csv", csv_bytes, "text/csv")}
    data = {"version_tag": "v1.0"}
    ver_res = await client.post(
        f"/api/v1/datasets/{dataset_id}/versions",
        files=files,
        data=data,
        headers=headers,
    )
    assert ver_res.status_code == 201
    version_id = ver_res.json()["data"]["id"]

    # 3. Request AI Preprocessing Plan
    plan_res = await client.post(
        "/api/v1/preprocessing/plan",
        json={"dataset_version_id": version_id, "target_column": "LUNG_CANCER"},
        headers=headers,
    )
    assert plan_res.status_code == 200
    plan_data = plan_res.json()["data"]
    assert "steps" in plan_data
    assert len(plan_data["steps"]) >= 3
    assert "leakage_prevention_guarantee" in plan_data

    # 4. Execute the Preprocessing Plan
    exec_res = await client.post(
        "/api/v1/preprocessing/execute",
        json={"dataset_version_id": version_id, "target_column": "LUNG_CANCER"},
        headers=headers,
    )
    assert exec_res.status_code == 200
    exec_data = exec_res.json()["data"]
    assert exec_data["status"] == "completed"
    assert exec_data["train_samples"] > 0
    assert "leakage_audit" in exec_data
