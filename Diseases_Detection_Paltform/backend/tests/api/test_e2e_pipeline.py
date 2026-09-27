"""End-to-End Pipeline test validating full flow: Auth -> Dataset -> Features -> SVM -> VQC -> Predict -> Benchmark."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_full_platform_pipeline_e2e(client: AsyncClient):
    """Execute complete end-to-end workflow on biomedical dataset."""
    # 1. Register & Login
    email = "lead_investigator@qml.org"
    pwd = "StrongPassword123!"
    await client.post("/api/v1/auth/register", json={"email": email, "password": pwd, "full_name": "Lead Investigator"})
    login_res = await client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
    token = login_res.json()["access_token"]
    auth_header = {"Authorization": f"Bearer {token}"}

    # 2. Create Dataset
    ds_res = await client.post("/api/v1/datasets", json={"name": "Lung Cancer Pilot Study"}, headers=auth_header)
    assert ds_res.status_code == 201
    dataset_id = ds_res.json()["data"]["id"]

    # 3. Upload CSV Version
    csv_content = (
        "AGE,SMOKING,YELLOW_FINGERS,ANXIETY,PEER_PRESSURE,CHRONIC_DISEASE,FATIGUE,ALLERGY,WHEEZING,LUNG_CANCER\n"
        "65,1,1,2,1,1,2,1,2,1\n"
        "45,2,2,1,2,2,1,2,1,0\n"
        "55,1,2,2,1,2,2,1,2,1\n"
        "70,2,1,1,2,1,1,2,1,0\n"
        "60,1,1,2,1,2,2,1,2,1\n"
        "50,2,2,1,2,1,1,2,1,0\n"
        "68,1,1,2,1,2,2,1,2,1\n"
        "52,2,2,1,2,1,1,2,1,0\n"
        "75,1,2,2,1,2,2,1,2,1\n"
        "48,2,1,1,2,1,1,2,1,0\n"
        "62,1,1,2,1,2,2,1,2,1\n"
        "58,2,2,1,2,1,1,2,1,0\n"
    )
    files = {"file": ("cancer_cohort.csv", csv_content.encode("utf-8"), "text/csv")}
    ver_res = await client.post(
        f"/api/v1/datasets/{dataset_id}/versions",
        data={"version_tag": "v1.0"},
        files=files,
        headers=auth_header,
    )
    assert ver_res.status_code == 201
    version_id = ver_res.json()["data"]["id"]

    # 4. Canonical Feature Selection (Single Source of Truth)
    fs_res = await client.post(
        "/api/v1/features/select",
        json={"dataset_version_id": version_id, "ranking_method": "mutual_info", "k_features": 4},
        headers=auth_header,
    )
    assert fs_res.status_code == 201
    fs_data = fs_res.json()["data"]
    fs_id = fs_data["id"]
    selected_features = fs_data["selected_features"]
    assert len(selected_features) == 4

    # 5. Register Linear SVM Model Archetype
    m_svm_res = await client.post(
        "/api/v1/models",
        json={"name": "Linear SVM Classifier", "model_type": "svm_linear"},
        headers=auth_header,
    )
    assert m_svm_res.status_code == 201
    svm_id = m_svm_res.json()["data"]["id"]

    # 6. Train Linear SVM Model
    train_svm = await client.post(
        "/api/v1/training",
        json={"model_id": svm_id, "dataset_version_id": version_id, "feature_selection_run_id": fs_id},
        headers=auth_header,
    )
    assert train_svm.status_code == 201
    svm_run_id = train_svm.json()["data"]["id"]
    svm_version_id = train_svm.json()["data"]["model_version_id"]
    assert "metrics" in train_svm.json()["data"]

    # 7. Register VQC Model Archetype
    m_vqc_res = await client.post(
        "/api/v1/models",
        json={"name": "Variational Quantum Classifier", "model_type": "vqc"},
        headers=auth_header,
    )
    assert m_vqc_res.status_code == 201
    vqc_id = m_vqc_res.json()["data"]["id"]

    # 8. Train VQC Model on Quantum Simulator
    train_vqc = await client.post(
        "/api/v1/training",
        json={"model_id": vqc_id, "dataset_version_id": version_id, "feature_selection_run_id": fs_id},
        headers=auth_header,
    )
    assert train_vqc.status_code == 201
    vqc_run_id = train_vqc.json()["data"]["id"]
    vqc_version_id = train_vqc.json()["data"]["model_version_id"]

    # 9. Perform Inference Prediction with Risk Stratification
    pred_res = await client.post(
        "/api/v1/predictions",
        json={
            "model_version_id": svm_version_id,
            "features": {selected_features[0]: 65.0, selected_features[1]: 1.0, selected_features[2]: 2.0, selected_features[3]: 1.0},
            "decision_threshold": 0.5,
        },
        headers=auth_header,
    )
    assert pred_res.status_code == 200
    pred_data = pred_res.json()
    assert len(pred_data["results"]) == 1
    assert "risk_stratification" in pred_data["results"][0]

    # 10. Create Experiment & Generate Comparative Benchmark Report (CML vs QML)
    exp_res = await client.post(
        "/api/v1/experiments",
        json={"name": "Lung Cancer CML vs QML Benchmark", "description": "Comparing Linear SVM and VQC."},
        headers=auth_header,
    )
    assert exp_res.status_code == 201
    exp_id = exp_res.json()["data"]["id"]

    comp_res = await client.post(
        f"/api/v1/experiments/{exp_id}/compare",
        json={"training_run_ids": [svm_run_id, vqc_run_id]},
        headers=auth_header,
    )
    assert comp_res.status_code == 200
    report_data = comp_res.json()["data"]
    assert "markdown_report" in report_data
    assert "Variational Quantum Classifier" in report_data["markdown_report"]
