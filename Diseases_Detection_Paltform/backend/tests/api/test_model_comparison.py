"""API tests verifying multi-model comparative evaluation across all metrics."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_compare_two_or_more_models(client: AsyncClient):
    """Ensure comparing 2+ models returns side-by-side benchmarking across all clinical metrics."""
    # 1. Register and login user
    await client.post(
        "/api/v1/auth/register",
        json={"email": "evaluator@research.org", "password": "StrongPassword123!"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "evaluator@research.org", "password": "StrongPassword123!"},
    )
    token = login_resp.json()["access_token"]
    auth_header = {"Authorization": f"Bearer {token}"}

    # 2. Seed default models into registry
    seed_resp = await client.post("/api/v1/models/seed-defaults", headers=auth_header)
    assert seed_resp.status_code == 200
    seeded_models = seed_resp.json()["data"]
    assert len(seeded_models) >= 3

    # Select Linear SVM, RBF SVM, and 4-Qubit VQC
    model_ids = [m["id"] for m in seeded_models[:3]]

    # 3. Request Multi-Model Comparison
    comp_resp = await client.post(
        "/api/v1/models/compare",
        json={"model_ids": model_ids},
        headers=auth_header,
    )
    assert comp_resp.status_code == 200
    data = comp_resp.json()

    # Verify all models evaluated
    assert len(data["models_compared"]) == 3
    model_names = [m["model_name"] for m in data["models_compared"]]
    assert any("SVM" in name for name in model_names)
    assert any("VQC" in name or "Quantum" in name for name in model_names)

    # Verify comparison matrix covers all 8 metrics
    matrix = data["comparison_matrix"]
    metric_keys = [row["metric_key"] for row in matrix]
    assert "accuracy" in metric_keys
    assert "sensitivity" in metric_keys
    assert "specificity" in metric_keys
    assert "precision" in metric_keys
    assert "f1_score" in metric_keys
    assert "roc_auc" in metric_keys
    assert "training_duration_sec" in metric_keys

    # Verify each row has values for all 3 models and designates a best performer
    for row in matrix:
        assert len(row["values"]) == 3
        assert row["best_model"] in model_names

    # Verify category winners
    winners = data["category_winners"]
    assert "Overall Accuracy" in winners
    assert "Sensitivity (Recall / True Positive Rate)" in winners

    # Verify CML vs QML insights
    cml_qml = data["cml_vs_qml_insights"]
    assert cml_qml["classical_models_count"] >= 1
    assert cml_qml["quantum_models_count"] >= 1

    # Verify markdown table and summary
    assert "| Overall Accuracy |" in data["markdown_table"]
    assert "Confusion Matrix Breakdown" in data["markdown_table"]
    assert len(data["executive_summary"]) > 20


@pytest.mark.asyncio
async def test_compare_models_requires_minimum_two(client: AsyncClient):
    """Ensure comparison fails if user selects fewer than 2 models."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": "evaluator2@research.org", "password": "StrongPassword123!"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "evaluator2@research.org", "password": "StrongPassword123!"},
    )
    token = login_resp.json()["access_token"]
    auth_header = {"Authorization": f"Bearer {token}"}

    # Only 1 model selected
    bad_resp = await client.post(
        "/api/v1/models/compare",
        json={"model_ids": ["single-model-id"]},
        headers=auth_header,
    )
    assert bad_resp.status_code == 422
