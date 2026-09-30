"""Quantum API tests enforce the simulator-only deployment contract."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_quantum_api_runs_simulators_and_rejects_hardware(client: AsyncClient):
    email = "quantum-simulators@research.org"
    password = "StrongPassword123!"
    await client.post("/api/v1/auth/register", json={"email": email, "password": password})
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    devices = await client.get("/api/v1/quantum/devices", headers=headers)
    assert devices.status_code == 200
    assert {device["device_id"] for device in devices.json()} == {"simulator", "noisy_simulator"}

    simulator = await client.post(
        "/api/v1/quantum/jobs",
        headers=headers,
        json={
            "device_id": "simulator",
            "circuit_data": {
                "n_qubits": 2,
                "n_layers": 1,
                "features": [0.3, 0.8],
                "weights": [[0.2, 0.4]],
                "encoding_method": "angle_ry",
                "variational_gate": "RY",
                "entanglement_strategy": "linear_cnot",
            },
        },
    )
    assert simulator.status_code == 201
    result = simulator.json()["data"]
    assert result["status"] == "completed"
    assert result["device_id"] == "simulator"
    assert len(result["expectations"]) == 2

    hardware = await client.post(
        "/api/v1/quantum/jobs",
        headers=headers,
        json={"device_id": "ibm_hardware", "circuit_data": {}},
    )
    assert hardware.status_code == 503
    assert hardware.json()["error"]["code"] == "QUANTUM_HARDWARE_UNAVAILABLE"

    credentials = await client.post(
        "/api/v1/quantum/credentials",
        headers=headers,
        json={"provider_name": "IBM Quantum", "api_key": "placeholder-secret"},
    )
    assert credentials.status_code == 503
    assert credentials.json()["error"]["code"] == "QUANTUM_HARDWARE_UNAVAILABLE"
