"""Model comparison must use measured runs tied to uploaded dataset versions."""

from pathlib import Path

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_untrained_templates_cannot_be_compared(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "templates@research.org", "password": "StrongPassword123!"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "templates@research.org", "password": "StrongPassword123!"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    seeded = await client.post("/api/v1/models/seed-defaults", headers=headers)
    assert seeded.status_code == 200
    templates = seeded.json()["data"]
    assert len(templates) >= 2

    response = await client.post(
        "/api/v1/models/compare",
        json={"model_ids": [model["id"] for model in templates[:2]]},
        headers=headers,
    )
    assert response.status_code == 422
    assert "has not been trained" in response.json()["error"]["message"]


@pytest.mark.asyncio
async def test_compare_requires_at_least_two_models(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "one-model@research.org", "password": "StrongPassword123!"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "one-model@research.org", "password": "StrongPassword123!"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = await client.post(
        "/api/v1/models/compare",
        json={"model_ids": ["single-model-id"]},
        headers=headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_pretrained_checkpoint_is_evaluated_on_upload_with_separate_metrics(client: AsyncClient):
    email = "checkpoint-evaluation@research.org"
    password = "StrongPassword123!"
    await client.post("/api/v1/auth/register", json={"email": email, "password": password})
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    defaults = await client.get("/api/v1/models/defaults", headers=headers)
    assert defaults.status_code == 200
    checkpoint = next(
        model for model in defaults.json()
        if model["configuration"].get("pretrained")
        and model["model_type"] == "svm_linear"
        and model["configuration"].get("feature_count") == 4
    )
    features = checkpoint["configuration"]["selected_features"]

    repository_root = Path(__file__).resolve().parents[4]
    dataset_path = repository_root / "Experimental_ML" / "Lung_Cancer" / "data" / "raw" / "V1_dataset.csv"
    assert dataset_path.is_file(), "The checked-in Experimental_ML source cohort is required for this checkpoint integration test."
    dataset = await client.post("/api/v1/datasets", json={"name": "Checkpoint evaluation cohort"}, headers=headers)
    dataset_id = dataset.json()["data"]["id"]
    uploaded = await client.post(
        f"/api/v1/datasets/{dataset_id}/versions",
        data={"version_tag": "upload-v1"},
        files={"file": (dataset_path.name, dataset_path.read_bytes(), "text/csv")},
        headers=headers,
    )
    version_id = uploaded.json()["data"]["id"]

    selection = await client.post(
        "/api/v1/features/select",
        json={
            "dataset_version_id": version_id,
            "target_column": "LUNG_CANCER",
            "ranking_method": "manual",
            "selected_features": features,
        },
        headers=headers,
    )
    assert selection.status_code == 201

    preprocessing = await client.post(
        "/api/v1/preprocessing/execute",
        json={
            "dataset_version_id": version_id,
            "target_column": "LUNG_CANCER",
            "mode": "user_defined",
            "generation_method": "user_defined",
            "steps": [
                {"step_id": "split", "tool_name": "stratified_split", "parameters": {"train_ratio": 0.7, "val_ratio": 0.15, "test_ratio": 0.15, "random_state": 42}, "fit_on_train_only": False},
                {"step_id": "scale", "tool_name": "min_max_scaler", "parameters": {"columns": features}},
            ],
        },
        headers=headers,
    )
    assert preprocessing.status_code == 200

    run = await client.post(
        "/api/v1/training",
        json={
            "model_id": checkpoint["id"],
            "dataset_version_id": version_id,
            "feature_selection_run_id": selection.json()["data"]["id"],
            "preprocessing_run_id": preprocessing.json()["data"]["preprocessing_run_id"],
        },
        headers=headers,
    )
    assert run.status_code == 201
    evaluated_model_id = run.json()["data"]["model_id"]
    evaluated = await client.get(f"/api/v1/models/{evaluated_model_id}", headers=headers)
    assert evaluated.status_code == 200
    evaluated_config = evaluated.json()["configuration"]
    assert evaluated_config["pretrained_used"] is True
    assert evaluated_config["pretrained_source_model_id"] == checkpoint["configuration"]["model_id"]
    assert evaluated_config["pretrained_source_metrics"]["accuracy"] == checkpoint["configuration"]["metrics"]["accuracy"]
    assert isinstance(evaluated_config["metrics"]["accuracy"], float)
    assert evaluated_config["dataset_version_id"] == version_id

    source = await client.get(f"/api/v1/models/{checkpoint['id']}", headers=headers)
    assert source.json()["configuration"]["metrics"]["accuracy"] == checkpoint["configuration"]["metrics"]["accuracy"]

    vqc_checkpoint = next(
        model for model in defaults.json()
        if model["configuration"].get("pretrained")
        and model["model_type"] == "vqc"
        and model["configuration"].get("n_qubits") == 4
        and not model["configuration"].get("noise_channels")
    )
    vqc_run = await client.post(
        "/api/v1/training",
        json={
            "model_id": vqc_checkpoint["id"],
            "dataset_version_id": version_id,
            "feature_selection_run_id": selection.json()["data"]["id"],
            "preprocessing_run_id": preprocessing.json()["data"]["preprocessing_run_id"],
        },
        headers=headers,
    )
    assert vqc_run.status_code == 201
    vqc_evaluated = await client.get(
        f"/api/v1/models/{vqc_run.json()['data']['model_id']}",
        headers=headers,
    )
    assert vqc_evaluated.status_code == 200
    vqc_config = vqc_evaluated.json()["configuration"]
    assert vqc_config["pretrained_used"] is True
    assert vqc_config["quantum_config"]["backend_type"] == "default.qubit"
    assert vqc_config["quantum_config"]["n_layers"] == 2
    assert vqc_config["pretrained_source_metrics"]["accuracy"] == vqc_checkpoint["configuration"]["metrics"]["accuracy"]
