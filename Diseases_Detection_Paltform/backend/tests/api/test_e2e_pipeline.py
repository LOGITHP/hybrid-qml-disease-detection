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

    # 4. Generate and execute an approved, schema-aware preprocessing plan.
    plan_res = await client.post(
        "/api/v1/preprocessing/plan",
        json={"dataset_version_id": version_id, "target_column": "LUNG_CANCER"},
        headers=auth_header,
    )
    assert plan_res.status_code == 200
    approved_steps = plan_res.json()["data"]["steps"]
    prep_res = await client.post(
        "/api/v1/preprocessing/execute",
        json={"dataset_version_id": version_id, "target_column": "LUNG_CANCER", "mode": "ai", "steps": approved_steps, "generation_method": "rule_based"},
        headers=auth_header,
    )
    assert prep_res.status_code == 200
    preprocessing_run_id = prep_res.json()["data"]["preprocessing_run_id"]

    # 5. Canonical feature ranking fits only on a training partition.
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
    assert fs_data["ranking_data_partition"] == "training partition only"
    assert fs_data["ranking_random_state"] == 42

    # 6. Register Linear SVM Model Archetype
    m_svm_res = await client.post(
        "/api/v1/models",
        json={"name": "Linear SVM Classifier", "model_type": "svm_linear"},
        headers=auth_header,
    )
    assert m_svm_res.status_code == 201
    svm_id = m_svm_res.json()["data"]["id"]

    # 7. Train Linear SVM using the saved preprocessing run.
    train_svm = await client.post(
        "/api/v1/training",
        json={"model_id": svm_id, "dataset_version_id": version_id, "feature_selection_run_id": fs_id, "preprocessing_run_id": preprocessing_run_id},
        headers=auth_header,
    )
    assert train_svm.status_code == 201
    svm_run_id = train_svm.json()["data"]["id"]
    assert "metrics" in train_svm.json()["data"]
    svm_model_id = train_svm.json()["data"]["model_id"]
    svm_model = await client.get(f"/api/v1/models/{svm_model_id}", headers=auth_header)
    assert svm_model.status_code == 200
    assert svm_model.json()["dataset_version_id"] == version_id
    assert svm_model.json()["configuration"]["preprocessing_run_id"] == preprocessing_run_id
    assert svm_model.json()["configuration"]["feature_selection_method"] == "mutual_info"

    # 8. Register VQC Model Archetype
    m_vqc_res = await client.post(
        "/api/v1/models",
        json={"name": "Variational Quantum Classifier", "model_type": "vqc"},
        headers=auth_header,
    )
    assert m_vqc_res.status_code == 201
    vqc_id = m_vqc_res.json()["data"]["id"]

    # 9. Train VQC Model on the PennyLane simulator.
    train_vqc = await client.post(
        "/api/v1/training",
        json={"model_id": vqc_id, "dataset_version_id": version_id, "feature_selection_run_id": fs_id, "preprocessing_run_id": preprocessing_run_id, "hyperparameters": {"layers": 1, "epochs": 1, "n_qubits": 4, "encoding_method": "angle_rx", "variational_gate": "RZ", "entanglement_strategy": "ring_cnot"}},
        headers=auth_header,
    )
    assert train_vqc.status_code == 201
    vqc_run_id = train_vqc.json()["data"]["id"]
    vqc_model_id = train_vqc.json()["data"]["model_id"]

    # 10. Exercise the noisy simulator training path.
    noisy_model = await client.post("/api/v1/models", json={"name": "Noisy VQC", "model_type": "vqc"}, headers=auth_header)
    assert noisy_model.status_code == 201
    noisy_run = await client.post(
        "/api/v1/training",
        json={"model_id": noisy_model.json()["data"]["id"], "dataset_version_id": version_id,
              "feature_selection_run_id": fs_id, "preprocessing_run_id": preprocessing_run_id,
              "hyperparameters": {"layers": 1, "epochs": 1, "n_qubits": 4}, "is_noisy_quantum": True,
              "noise_params": {"p_gate": 0.01, "p_cnot": 0.02, "p_meas": 0.01}},
        headers=auth_header,
    )
    assert noisy_run.status_code == 201
    noisy_model_id = noisy_run.json()["data"]["model_id"]
    noisy_details = await client.get(f"/api/v1/models/{noisy_model_id}", headers=auth_header)
    assert noisy_details.json()["configuration"]["quantum_config"]["backend_type"] == "default.mixed"

    # Compare saved held-out metrics for compatible trained models only.
    model_comparison = await client.post(
        "/api/v1/models/compare",
        json={"model_ids": [svm_model_id, vqc_model_id, noisy_model_id]},
        headers=auth_header,
    )
    assert model_comparison.status_code == 200
    comparison_data = model_comparison.json()
    assert len(comparison_data["models_compared"]) == 3
    assert comparison_data["category_winners"] == {}
    assert all(0 <= entry["accuracy"] <= 1 for entry in comparison_data["models_compared"])
    assert all(row["best_model"] is None for row in comparison_data["comparison_matrix"])

    # 11. Persist a real prediction record and verify its model/dataset lineage.
    pred_res = await client.post(
        "/api/v1/predictions",
        json={
            "model_id": svm_model_id,
            "features": {selected_features[0]: 65.0, selected_features[1]: 1.0, selected_features[2]: 2.0, selected_features[3]: 1.0},
            "decision_threshold": 0.5,
        },
        headers=auth_header,
    )
    if pred_res.status_code != 200:
        print(f"Prediction failed with: {pred_res.text}")
    assert pred_res.status_code == 200
    pred_data = pred_res.json()
    assert len(pred_data["results"]) == 1
    assert "risk_stratification" in pred_data["results"][0]
    prediction_id = pred_data["results"][0]["prediction_id"]
    assert prediction_id
    assert pred_data["dataset_version_id"] == version_id

    # 12. Verified feedback is attached to the saved prediction.
    feedback_res = await client.post("/api/v1/feedback", json={
        "prediction_id": prediction_id,
        "model_id": svm_model_id,
        "is_correct": False,
        "verified_label": 1 - pred_data["results"][0]["predicted_class"],
        "original_input": {selected_features[0]: 65.0},
        "notes": "E2E verified label",
    }, headers=auth_header)
    assert feedback_res.status_code == 200
    assert feedback_res.json()["data"]["prediction_id"] == prediction_id

    # 13. Create an experiment report from actual completed runs.
    exp_res = await client.post(
        "/api/v1/experiments",
        json={"name": "Lung Cancer CML vs QML Benchmark", "description": "Comparing Linear SVM and VQC."},
        headers=auth_header,
    )
    assert exp_res.status_code == 201
    exp_id = exp_res.json()["data"]["id"]

    comp_res = await client.post(
        f"/api/v1/experiments/{exp_id}/compare",
        json={"training_run_ids": [svm_run_id, vqc_run_id, noisy_run.json()["data"]["id"]]},
        headers=auth_header,
    )
    assert comp_res.status_code == 200
    report_data = comp_res.json()["data"]
    assert "markdown_report" in report_data
    assert "Variational Quantum Classifier" in report_data["markdown_report"]
    assert "does not rank models or claim an advantage" in report_data["markdown_report"]

    # 14. Manual feedback retraining creates a review candidate without replacing the parent.
    retrain_res = await client.post(f"/api/v1/feedback/model/{svm_model_id}/retrain", headers=auth_header)
    assert retrain_res.status_code == 200
    candidate_id = retrain_res.json()["data"]["model_id"]
    candidate = await client.get(f"/api/v1/models/{candidate_id}", headers=auth_header)
    assert candidate.status_code == 200
    assert candidate.json()["status"] == "candidate"
    assert candidate.json()["configuration"]["parent_model_id"] == svm_model_id
